#!/usr/bin/env python3
"""TASK-237 deliverable 1 — can the declared skeleton reproduce BOARD.md? A MEASUREMENT.

Not a renderer, not a test module, and not the deliverable:
`perry/evidence/2026-09/TASK-237-result.md § 2` is the report, and this file is
how every number in it is reproduced. It lives in `tests/` beside
`sweep_blank_cell_sites.py` and `mutate_blank_cell.py` for the reason those do:
it holds table rows on purpose, and `tests/header_rule.py § NOT_A_READER`
excludes `tests/` from the census of product readers for exactly that.

    probe <project root>              render from DECLARED sources only, to stdout.
                                      Reads schema/state-schema.json
                                      § files[id=board], work/state/BOARD_TEMPLATE.md,
                                      .perry/config.jsonl and the four board
                                      stores. Exit 3 if anything opens BOARD.md.
                                      Every choice the declarations leave open is
                                      printed to stderr as `choice:`.
    facts <BOARD.md>                  ACCOUNTING: read the board and write, as
                                      JSON, every byte of it no store holds.
    accounting <project root> <facts> facts + stores -> board text, never opening
                                      BOARD.md. `cmp`-equal to the board means the
                                      facts are the COMPLETE undeclared layout —
                                      and, because they were read out of the
                                      board, that it must never become a renderer.
    compare <rendered> <live>         hunk-by-hunk difference and matched bytes.

Columns resolve through `tables.header_index(…, alias=perry-task § norm)` — the
one header rule, the same route `perry_store.plan` takes — so a localized or
decorated header lands on the same field here as in the real renderer.

Measured 2026-09-14 on 02825582 (BOARD.md 157,242 bytes):
    probe      -> exit 0, 157,422 bytes, not identical; 2,349 live bytes on matching lines
    accounting -> cmp-equal, with BOARD.md present and with it deleted
"""
from __future__ import annotations

import builtins
import difflib
import importlib.machinery
import importlib.util
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "viewer"))
sys.path.insert(0, str(REPO / "bin"))
import lib  # noqa: E402
import perry_store  # noqa: E402
from tables import header_index, render_row, render_separator, split_row  # noqa: E402

SEP = re.compile(r"^\|\s*:?-{2,}")
REGISTERS = [(r"^P[012]\b", perry_store.FIELD_BY_COLUMN, "tasks"),
             (r"^User Input Queue\b", perry_store.ASK_FIELD_BY_COLUMN, "asks"),
             (r"^Top risks\b", perry_store.RISK_FIELD_BY_COLUMN, "risks"),
             (r"^Intake\b", perry_store.INTAKE_FIELD_BY_COLUMN, "intake")]
MAPS = {name: m for _rx, m, name in REGISTERS}


def _norm():
    loader = importlib.machinery.SourceFileLoader("perry_task_t237",
                                                  str(REPO / "bin" / "perry-task"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod.norm


NORM = _norm()


def fields(header: list[str], fmap: dict) -> list[str | None]:
    """The store field each column renders from, or None — by the one header rule."""
    return [fmap.get(k) for k in header_index(header, alias=NORM)]


def forbid_the_board():
    real = io.open

    def guarded(file, *a, **k):
        if Path(str(file)).name == "BOARD.md":
            print("measurement void: BOARD.md was opened", file=sys.stderr)
            raise SystemExit(3)
        return real(file, *a, **k)

    builtins.open = io.open = guarded


def jsonl(p: Path):
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").split("\n") if l.strip()]


def stores(root: Path) -> tuple[dict, dict]:
    settings = {r["key"]: r["value"] for r in jsonl(root / ".perry/config.jsonl")
                if r.get("kind") == "setting"}
    state = root / settings.get("state_root", "")
    return settings, {n: jsonl(state / f"{n}.jsonl")
                      for n in ("tasks", "asks", "risks", "intake")}


def rows_for(name: str, title: str, recs: list[dict]) -> list[dict]:
    if name == "tasks":
        recs = [r for r in recs if r.get("group") == title
                and r.get("status") not in perry_store.TERMINAL_STATUSES]
    elif name == "intake":
        recs = [r for r in recs if not r.get("discharged")]
    return sorted(recs, key=lambda r: (r.get("order") is None, r.get("order") or 0))


def cmd_probe(root: Path) -> None:
    forbid_the_board()
    schema = json.loads((REPO / "schema/state-schema.json").read_text(encoding="utf-8"))
    board = next(f for f in schema["files"] if f.get("id") == "board")
    template = (REPO / board["template"]).read_text(encoding="utf-8").split("\n")
    settings, st = stores(root)
    choices = [
        "placeholders: only `{{YYYY-MM-DD}}` on the `Last updated` line has a declared "
        "source (config `last_updated`); every other `{{…}}` is left as written",
        "sections: the template's, in the template's order (it agrees with "
        "`headings`); a section neither declares is not emitted",
        "columns: required `columns`, then EVERY `optional_columns` key in declaration "
        "order — the schema says which columns MAY appear, not which DO, nor where",
        "rows: the section's store records (tasks: non-terminal, `group` == heading), "
        "by `order`; a table with no store keeps the template's placeholder rows",
    ]
    out, title, i = [], "", 0
    while i < len(template):
        line = template[i]
        if line.startswith("## "):
            title = line[3:].strip()
        if line.startswith("|") and i + 1 < len(template) and SEP.match(template[i + 1]):
            spec = next(t for t in board["tables"] if re.search(t["under"], title))
            cols = list(spec["columns"]) + list(spec.get("optional_columns") or {})
            out += [render_row(cols), render_separator(len(cols))]
            j = i + 2
            placeholder = []
            while j < len(template) and template[j].startswith("|"):
                placeholder.append(template[j]); j += 1
            reg = next(((m, n) for rx, m, n in REGISTERS if re.match(rx, title)), None)
            if reg is None:
                out += [render_row([""] * len(cols)) for _ in placeholder]
            else:
                fmap, name = reg
                flds = fields(cols, fmap)
                for r in rows_for(name, title, st[name]):
                    out.append(render_row([
                        perry_store.cell_text(f, r, escape=False) if f else ""
                        for f in flds]))
            i = j
            continue
        if "Last updated" in line and settings.get("last_updated"):
            line = line.replace("{{YYYY-MM-DD}}", settings["last_updated"])
        out.append(line)
        i += 1
    sys.stdout.write("\n".join(out))
    for c in choices:
        print("choice:", c, file=sys.stderr)


def cmd_facts(board_path: Path) -> None:
    lines = board_path.read_text(encoding="utf-8").split("\n")
    items, title, i = [], "", 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("## "):
            title = l[3:].strip()
        if l.startswith("|") and i + 1 < len(lines) and SEP.match(lines[i + 1]):
            header = split_row(l)
            reg = next(((m, n) for rx, m, n in REGISTERS if re.match(rx, title)), None)
            j = i + 2
            rows = []
            while j < len(lines) and lines[j].startswith("|"):
                rows.append(lines[j]); j += 1
            item = {"table": title, "header": header, "header_line": l,
                    "separator_line": lines[i + 1], "store": reg and reg[1]}
            if reg is None:
                item["verbatim_rows"] = rows
            else:
                flds = fields(header, reg[0])
                unmapped, markers = {}, {}
                for r in rows:
                    cells = split_row(r)
                    rid = cells[0].strip()
                    for n, c in enumerate(cells):
                        if flds[n] is None:
                            unmapped.setdefault(rid, {})[str(n)] = c
                        elif c.strip() and lib.is_blank_cell(c.strip()):
                            markers.setdefault(rid, {})[str(n)] = c.strip()
                item.update(unmapped_cells=unmapped, blank_markers=markers,
                            row_count=len(rows))
            items.append(item)
            i = j
            continue
        items.append({"line": l})
        i += 1
    json.dump(items, sys.stdout, ensure_ascii=False, indent=1)


def cmd_accounting(root: Path, facts_path: Path) -> None:
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    forbid_the_board()
    _settings, st = stores(root)
    out = []
    for it in facts:
        if "line" in it:
            out.append(it["line"]); continue
        h = it["header"]
        out += [render_row(h), render_separator(len(h))]
        if it["store"] is None:
            out += it["verbatim_rows"]; continue
        flds = fields(h, MAPS[it["store"]])
        for k, r in enumerate(rows_for(it["store"], it["table"], st[it["store"]])):
            rid = r.get("id", str(k))
            cells = []
            for n, f in enumerate(flds):
                v = perry_store.cell_text(f, r, escape=False) if f else \
                    it["unmapped_cells"].get(rid, {}).get(str(n), "")
                if f and not v:
                    v = it["blank_markers"].get(rid, {}).get(str(n), "")
                cells.append(v)
            out.append(render_row(cells))
    sys.stdout.write("\n".join(out))


def cmd_compare(rendered: Path, live: Path) -> None:
    r, l = rendered.read_text(encoding="utf-8"), live.read_text(encoding="utf-8")
    print(f"rendered {len(r.encode())} B, live {len(l.encode())} B, identical={r == l}")
    a, b = l.split("\n"), r.split("\n")
    eq = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == "equal":
            eq += sum(len(x.encode()) + 1 for x in a[i1:i2]); continue
        print(f"@@ {tag} live {i1 + 1}-{i2} | render {j1 + 1}-{j2}")
        for x in a[i1:i2][:6]:
            print("  - " + x[:160])
        for x in b[j1:j2][:6]:
            print("  + " + x[:160])
    print(f"live bytes on exactly matching lines: {eq} of {len(l.encode())}")


if __name__ == "__main__":
    cmd, args = sys.argv[1], [Path(a).resolve() for a in sys.argv[2:]]
    {"probe": cmd_probe, "facts": cmd_facts, "accounting": cmd_accounting,
     "compare": cmd_compare}[cmd](*args)
