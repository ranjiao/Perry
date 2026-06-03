"""Perry viewer — read-only local web UI for a project's PMO state.

Don't run this directly; use the launcher which sets up the venv + deps:
    bash "$PERRY_HOME/bin/perry-viewer"        # from inside your project dir
The launcher resolves the project root (where BOARD.md lives) and starts this.
Port defaults to 8080 (override with PERRY_VIEWER_PORT)."""

from __future__ import annotations

import html as _html
import re
from collections import Counter
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for

import markdown as md_lib

from parsers import PROJECT_ROOT, load_snapshot

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


# ── Helpers ───────────────────────────────────────────────────────────────


def _build_id_evidence_map(snap) -> dict:
    """Map task / user IDs to evidence file paths when available.
    Used so user-input-queue items can deep-link to the same evidence file
    as the matching BOARD task row."""
    m: dict[str, str] = {}
    for t in snap.board.all_tasks:
        ev = _extract_evidence_path(t.evidence or "")
        if ev:
            m[t.id] = ev
    return m


def _extract_evidence_path(text: str) -> str | None:
    if not text:
        return None
    m = _RE_EV_PATH.search(text)
    return m.group(1) if m else None


def _kpi(snap) -> dict:
    """Aggregate stats the Today / Pulse pages display."""
    okr_objs = snap.okr.objectives or []
    # Heuristic: count KR checkboxes in each objective body. Lines starting with
    # "- [x]" or containing the ✓ glyph in a `| ... |` table are likely "done".
    kr_done = 0
    kr_total = 0
    for o in okr_objs:
        body = o.raw_body or ""
        # Count ticked KR boxes
        kr_done += len(re.findall(r"-\s*\[[xX]\]", body))
        # Count table-style metric rows that look like KR rows
        kr_total += body.count("- [ ]") + body.count("- [x]") + body.count("- [X]")
    # If we couldn't infer, fall back to a flat assumption
    if kr_total == 0:
        kr_total = len(okr_objs) * 4
        kr_done = max(0, kr_total // 3)

    phase_day, phase_day_sub = _phase_day(snap)
    return {
        "kr_done": kr_done,
        "kr_total": kr_total,
        "phase_day": phase_day,
        "phase_day_sub": phase_day_sub,
        "user_q_sub": _user_q_sub(snap),
        "risks_sub": _risks_sub(snap),
    }


def _phase_day(snap) -> tuple[str, str]:
    """Days elapsed since the phase started (day 1 = start date), from the
    phase file's Started date. Falls back to '—' if no phase / no parseable date."""
    if not snap.phase:
        return "—", "no phase"
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", snap.phase.started or "")
    if not m:
        return "—", (snap.phase.slug or "no start date")
    from datetime import date
    start = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    elapsed = (date.today() - start).days + 1  # start date is day 1
    if elapsed < 1:
        return "—", f"starts {snap.phase.started}"
    return str(elapsed), f"since {snap.phase.started}"


def _user_q_sub(snap) -> str:
    items = snap.board.user_input_queue
    if not items:
        return "queue empty"
    idle_items = [u for u in items if u.idle and u.idle != "—"]
    p0_items = [u for u in items if u.priority == "P0"]
    parts = []
    if p0_items:
        parts.append(f"{len(p0_items)} P0")
    if idle_items:
        oldest = max(idle_items, key=lambda u: _days(u.idle))
        parts.append(f"oldest {oldest.idle}")
    return " · ".join(parts) or "—"


def _risks_sub(snap) -> str:
    if not snap.top_risks:
        return "no risks parsed"
    sev_counts = Counter(r.severity for r in snap.top_risks)
    parts = []
    if sev_counts.get("top"):
        parts.append(f"{sev_counts['top']} top")
    if sev_counts.get("watch"):
        parts.append(f"{sev_counts['watch']} watch")
    if sev_counts.get("accept"):
        parts.append(f"{sev_counts['accept']} accept")
    return " · ".join(parts) or "—"


def _days(s: str) -> int:
    m = re.match(r"(\d+)\s*d", s or "")
    return int(m.group(1)) if m else 0


_RE_MERMAID = re.compile(r"```mermaid[ \t]*\n(.*?)\n?```", re.S)


def render_md(text: str) -> tuple[str, list[tuple[int, str, str]]]:
    # Stash ```mermaid blocks before markdown runs so the engine doesn't
    # escape/mangle the diagram DSL. Re-insert as <div class="mermaid"> for
    # client-side rendering (mermaid.js reads textContent, so HTML-escaping
    # the source is correct — the browser un-escapes it back for mermaid).
    mermaid_blocks: list[str] = []

    def _stash(m: re.Match) -> str:
        mermaid_blocks.append(m.group(1))
        return f"\n\nMERMAIDBLOCK{len(mermaid_blocks) - 1}ENDMERMAID\n\n"

    text = _RE_MERMAID.sub(_stash, text)

    md = md_lib.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
        output_format="html5",
        extension_configs={"toc": {"permalink": False}},
    )
    html = md.convert(text)
    toc_tokens = getattr(md, "toc_tokens", [])
    flat: list[tuple[int, str, str]] = []

    def walk(items, level):
        for it in items:
            flat.append((level, it["name"], it["id"]))
            if it.get("children"):
                walk(it["children"], level + 1)

    walk(toc_tokens, 1)

    # Restore mermaid blocks. The bare placeholder line gets wrapped in <p>…</p>
    # by markdown — replace that form first, then any stray bare occurrence.
    for i, block in enumerate(mermaid_blocks):
        div = f'<div class="mermaid">{_html.escape(block)}</div>'
        token = f"MERMAIDBLOCK{i}ENDMERMAID"
        html = html.replace(f"<p>{token}</p>", div).replace(token, div)

    return html, flat


# ── Routes ────────────────────────────────────────────────────────────────


@app.route("/favicon.ico")
def favicon():
    # Browsers probe /favicon.ico even when an SVG <link> is present; redirect
    # to the SVG so there's no 404 noise in the log.
    return redirect(url_for("static", filename="favicon.svg"))


@app.route("/")
def today():
    snap = load_snapshot()
    return render_template(
        "today.html",
        snap=snap,
        active="today",
        kpi=_kpi(snap),
        id_evidence_map=_build_id_evidence_map(snap),
    )


@app.route("/okr")
def okr():
    snap = load_snapshot()
    return render_template("okr.html", snap=snap, active="okr")


@app.route("/board")
def board():
    snap = load_snapshot()
    return render_template(
        "board.html",
        snap=snap,
        active="board",
        id_evidence_map=_build_id_evidence_map(snap),
    )


@app.route("/architecture")
def architecture():
    snap = load_snapshot()
    arch_path = PROJECT_ROOT / "ARCHITECTURE.md"
    body, toc = ("", [])
    if arch_path.exists():
        body, toc = render_md(arch_path.read_text())
    return render_template(
        "architecture.html",
        snap=snap,
        active="architecture",
        body=body,
        toc=toc,
        exists=arch_path.exists(),
    )


@app.route("/phase")
def phase():
    snap = load_snapshot()
    return render_template("phase.html", snap=snap, active="phase")


@app.route("/risks")
def risks():
    snap = load_snapshot()
    return render_template("risks.html", snap=snap, active="risks")


@app.route("/atlas")
def atlas():
    snap = load_snapshot()
    tab = request.args.get("tab", "tasks")
    query = (request.args.get("q") or "").strip().lower()
    priority_filter = (request.args.get("priority") or "").strip()
    status_filter = (request.args.get("status") or "").strip()
    type_filter = (request.args.get("type") or "").strip()

    tasks = snap.board.all_tasks
    if priority_filter:
        tasks = [t for t in tasks if t.priority == priority_filter]
    if status_filter:
        tasks = [t for t in tasks if t.status == status_filter]
    if query:
        tasks = [
            t for t in tasks
            if query in t.id.lower()
            or query in t.title.lower()
            or query in t.owner.lower()
            or query in t.next_action.lower()
        ]

    evidence = snap.evidence
    if query:
        evidence = [e for e in evidence if query in e.name.lower() or query in e.rel.lower()]

    adrs = snap.adrs
    # Distinct ADR type tokens (types are slash-compound, e.g. "Architecture /
    # Trading") → individual chips. Filter by case-insensitive substring so a
    # token chip matches any compound type containing it.
    adr_types = sorted({
        tok.strip() for a in snap.adrs for tok in (a.type or "").split("/") if tok.strip()
    })
    if type_filter:
        adrs = [a for a in adrs if type_filter.lower() in (a.type or "").lower()]
    if query:
        adrs = [
            a for a in adrs
            if query in a.id.lower() or query in a.title.lower() or query in a.type.lower()
        ]

    journal = snap.journal
    if query:
        journal = [j for j in journal if query in j.date]
    # Group journal entries by month, newest month first (entries already sorted
    # date-desc), so the journal tab reads as month sections instead of a flat list.
    journal_groups = []
    for j in journal:
        if not journal_groups or journal_groups[-1][0] != j.month:
            journal_groups.append((j.month, []))
        journal_groups[-1][1].append(j)

    handoff = snap.handoff
    if query:
        handoff = [h for h in handoff if query in h.date]

    counts = {
        "tasks": len(snap.board.all_tasks),
        "evidence": len(snap.evidence),
        "decisions": len(snap.adrs),
        "journal": len(snap.journal),
        "handoff": len(snap.handoff),
    }

    return render_template(
        "atlas.html",
        snap=snap,
        active="atlas",
        tab=tab,
        query=query,
        priority_filter=priority_filter,
        status_filter=status_filter,
        type_filter=type_filter,
        tasks=tasks,
        evidence=evidence,
        adrs=adrs,
        adr_types=adr_types,
        journal=journal,
        journal_groups=journal_groups,
        handoff=handoff,
        counts=counts,
    )


@app.route("/pulse")
def pulse():
    snap = load_snapshot()
    # ADR by month (parse date like "2026-05-06" → "2026-05")
    adr_month_counts: Counter = Counter()
    for a in snap.adrs:
        if a.date and len(a.date) >= 7:
            adr_month_counts[a.date[:7]] += 1
    adr_by_month = sorted(adr_month_counts.items())

    # Journal by month
    journal_month_counts: Counter = Counter(j.month for j in snap.journal if j.month)
    journal_by_month = sorted(journal_month_counts.items())

    # Evidence by month
    evidence_month_counts: Counter = Counter(e.month for e in snap.evidence if e.month)
    evidence_by_month = sorted(evidence_month_counts.items())

    return render_template(
        "pulse.html",
        snap=snap,
        active="pulse",
        kpi=_kpi(snap),
        adr_by_month=adr_by_month,
        journal_by_month=journal_by_month,
        evidence_by_month=evidence_by_month,
    )


@app.route("/file/<path:rel>")
def view_file(rel: str):
    target = (PROJECT_ROOT / rel).resolve()
    # Guard against directory traversal
    if not str(target).startswith(str(PROJECT_ROOT)):
        abort(403)
    if not target.exists() or not target.is_file():
        abort(404)
    snap = load_snapshot()
    if target.suffix == ".md":
        body, toc = render_md(target.read_text())
    else:
        body = f"<pre>{target.read_text()}</pre>"
        toc = []
    return render_template(
        "file.html",
        snap=snap,
        active="atlas",  # file viewer keeps atlas highlighted
        rel=rel,
        body=body,
        toc=toc,
        size=target.stat().st_size,
    )


# ── Filters ───────────────────────────────────────────────────────────────


@app.template_filter("first_line")
def first_line(text: str) -> str:
    if not text:
        return ""
    return text.split("\n", 1)[0].strip()


@app.template_filter("strip_md_link")
def strip_md_link(text: str) -> str:
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text or "")


_RE_EV_PATH = re.compile(r"((?:evidence|docs|design|decisions|runbook|incidents)/[A-Za-z0-9_./-]+\.md)")


@app.template_filter("evidence_path")
def evidence_path(text: str) -> str | None:
    """Extract the first project-relative .md path from a free-form cell.
    Accepts patterns like 'evidence/2026-05/foo.md', '(待) evidence/...md',
    '[link](evidence/...md)'. Returns None if no path found."""
    if not text:
        return None
    m = _RE_EV_PATH.search(text)
    return m.group(1) if m else None


@app.template_filter("strip_md")
def strip_md(text: str) -> str:
    """Strip inline markdown emphasis markers so risk/meta text renders as clean
    prose instead of showing literal **, ~~, ` to the user."""
    if not text:
        return ""
    t = re.sub(r"\*\*([^*]*)\*\*", r"\1", text)   # **bold**
    t = re.sub(r"~~([^~]*)~~", r"\1", t)           # ~~strike~~
    t = re.sub(r"`([^`]*)`", r"\1", t)             # `code`
    return t


@app.template_filter("strip_leading_bold")
def strip_leading_bold(text: str) -> str:
    """Remove the leading **bold** header from a risk meta line so it doesn't
    duplicate the ID + title already shown above, then strip any remaining
    inline markdown markers from the rest."""
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"^~~([^~]*)~~", r"\1", t)
    t = re.sub(r"^\*\*[^*]+?\*\*\s*[—:·-]?\s*", "", t)
    return strip_md(t).strip()


# ── Main ──────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PERRY_VIEWER_PORT", "8080"))
    print(f"Perry viewer · project root: {PROJECT_ROOT}")
    print(f"Open http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)
