"""Markdown parsers for a Perry project's state files. Read-only — never writes.

The viewer ships inside the Perry skill but renders the *project* it's pointed
at (where BOARD.md / OKR.md live), NOT the skill directory. Project root is
resolved from $PERRY_PROJECT, else by walking up from the current working dir
to the nearest ancestor containing BOARD.md or OKR.md."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


def _resolve_project_root() -> Path:
    env = os.environ.get("PERRY_PROJECT")
    if env:
        return Path(env).expanduser().resolve()
    cur = Path.cwd().resolve()
    for d in [cur, *cur.parents]:
        if (d / "BOARD.md").exists() or (d / "OKR.md").exists():
            return d
    return cur  # fall back to CWD; load_snapshot will just find nothing


PROJECT_ROOT = _resolve_project_root()


# ── Data classes ──────────────────────────────────────────────────────────

@dataclass
class Task:
    id: str
    title: str
    owner: str
    status: str          # normalized base enum: not_started/in_progress/blocked/review/done/dropped
    next_action: str
    evidence: str = ""
    priority: str = ""   # P0 / P1 / P2 / Cadence / Backbone
    status_note: str = ""  # parenthetical qualifier, e.g. "dev done" from "review (dev done)"


@dataclass
class UserInput:
    id: str
    needed_from_user: str
    blocks: str
    idle: str
    status: str
    priority: str = ""  # inferred P0 if blocks a P0 task


@dataclass
class Risk:
    """A single risk line. `text` is the raw markdown."""
    text: str
    resolved: bool = False  # ~~strikethrough~~ or contains **RESOLVED**


@dataclass
class TopRisk:
    """Structured risk from PROJECT_STATE.md or BOARD.md. Optional fields are
    populated when the parser can extract them from the line."""
    id: str
    title: str
    severity: str  # 'top' | 'watch' | 'accept' | 'resolved'
    meta: str = ""
    value: float | None = None
    threshold: float | None = None
    max1: float | None = None  # boundary into 'amber'
    max2: float | None = None  # boundary into 'rust'


@dataclass
class Tripwire:
    """Phase tripwire (from phase/<NNN>.md `## Trip-wires` table)."""
    id: str  # synthesized e.g. "#1"
    when: str  # the Day column
    condition: str
    response: str
    status: str = "armed"  # 'armed' | 'fired-resolved' (best-effort)


@dataclass
class BoardState:
    last_updated_header: str = ""
    p0: list[Task] = field(default_factory=list)
    p1: list[Task] = field(default_factory=list)
    p2: list[Task] = field(default_factory=list)
    cadence: list[Task] = field(default_factory=list)
    backbone_groups: list[tuple[str, list[Task]]] = field(default_factory=list)
    user_input_queue: list[UserInput] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)

    @property
    def all_tasks(self) -> list[Task]:
        out = list(self.p0) + list(self.p1) + list(self.p2) + list(self.cadence)
        for _, tasks in self.backbone_groups:
            out.extend(tasks)
        return out


@dataclass
class KR:
    id: str            # e.g. "KR1"
    text: str          # the key-result statement
    qualifier: str = ""  # optional parenthetical, e.g. "(Phase 1, 系统建设期)"


@dataclass
class Objective:
    title: str
    raw_body: str = ""
    intro: str = ""    # prose between the heading and the first KR bullet
    krs: list[KR] = field(default_factory=list)


@dataclass
class OKR:
    version: str = ""
    mission: str = ""  # prose between the doc title and ## Operating Principles
    objectives: list[Objective] = field(default_factory=list)
    anti_goals: list[str] = field(default_factory=list)
    operating_principles: list[str] = field(default_factory=list)
    version_log: list[tuple[str, str]] = field(default_factory=list)  # (vN, description)


@dataclass
class Phase:
    slug: str = ""
    number: str = ""
    started: str = ""
    focus: str = ""
    objectives: list[Objective] = field(default_factory=list)
    cost_ceiling_raw: str = ""
    cost_ceiling_lines: list[str] = field(default_factory=list)
    tripwires: list[Tripwire] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class ADR:
    id: str
    title: str
    type: str
    date: str
    sunset_or_notes: str
    file_path: str


@dataclass
class EvidenceFile:
    path: str
    rel: str
    name: str
    month: str
    mtime: float
    size: int


@dataclass
class JournalEntry:
    date: str  # YYYY-MM-DD
    month: str  # YYYY-MM
    path: str
    rel: str


@dataclass
class CarryForward:
    id: str
    origin: str
    description: str
    owner: str
    target: str


@dataclass
class ProjectState:
    last_updated: str = ""
    phase_lines: list[str] = field(default_factory=list)       # ## Phase bullets
    carry_forwards: list[CarryForward] = field(default_factory=list)
    cross_session: list[str] = field(default_factory=list)     # ## Recent cross-session work bullets
    external_deps: list[str] = field(default_factory=list)     # ## Key external dependencies bullets


@dataclass
class ArchMeta:
    exists: bool = False
    version: str = ""
    last_reviewed: str = ""
    status: str = ""
    section_count: int = 0
    open_questions: int = 0
    mermaid_count: int = 0


@dataclass
class DesignDoc:
    id: str                 # e.g. DESIGN-008 / INFRA-001
    title: str
    status: str             # normalized base enum: draft/in_review/locked/superseded/dropped
    status_raw: str = ""    # original status line (qualifier / dates / prose)
    date: str = ""
    locked: str = ""
    linked_okr: str = ""
    rel: str = ""           # design/<file>.md
    impl_refs: int = 0      # # of BOARD tasks referencing this design ID
    section_count: int = 0
    mermaid: bool = False


# ── BOARD.md ──────────────────────────────────────────────────────────────


def parse_board(text: str) -> BoardState:
    state = BoardState()

    m = re.search(r"Last updated:\s*([^\n]+)", text)
    if m:
        state.last_updated_header = m.group(1).strip().rstrip(",").rstrip(".")

    chunks = re.split(r"\n(?=## )", text)
    backbone_chunk = None
    for chunk in chunks:
        head_match = re.match(r"## (.+?)\n", chunk)
        if not head_match:
            continue
        head = head_match.group(1).strip()

        if head.startswith("P0"):
            state.p0 = _parse_task_table(chunk, "P0")
        elif head.startswith("P1"):
            state.p1 = _parse_task_table(chunk, "P1")
        elif head.startswith("P2"):
            state.p2 = _parse_task_table(chunk, "P2")
        elif head.startswith("Cadence"):
            state.cadence = _parse_task_table(chunk, "Cadence")
        elif head.startswith("User Input Queue"):
            state.user_input_queue = _parse_user_input(chunk)
        elif head.startswith("Top risks"):
            state.risks = _parse_risks(chunk)
        elif head.startswith("Backbone"):
            backbone_chunk = chunk

    if backbone_chunk:
        state.backbone_groups = _parse_backbone(backbone_chunk)

    # Heuristic: tag userInput priority by whether the user-id blocks a P0 task.
    p0_ids = {t.id for t in state.p0} | {t.id.split(' ')[0] for t in state.p0}
    p0_id_strs = ' '.join(p0_ids).lower()
    for u in state.user_input_queue:
        # blocks could be 'PAPER-FILL-AUDIT-rest post-fix data' or 'CADENCE-002'
        blocks_low = u.blocks.lower()
        if any(pid.lower() and pid.lower() in blocks_low for pid in p0_ids if pid):
            u.priority = "P0"
        elif u.id in p0_ids or u.id.lower() in p0_id_strs:
            u.priority = "P0"
        else:
            # default to P2 unless we can do better
            u.priority = "P2"

    return state


_STATUS_ENUM = {"not_started", "in_progress", "blocked", "review", "done", "dropped"}


def _split_status(raw: str) -> tuple[str, str]:
    """Normalize a messy status cell into (base_enum, note).
    Handles markdown bold + parenthetical qualifiers:
      '**review (dev done)**' -> ('review', 'dev done')
      '**done**'              -> ('done', '')
      'not_started (P1)'      -> ('not_started', 'P1')
      'review'                -> ('review', '')
    Falls back to (cleaned, '') if the first token isn't a known enum."""
    clean = (raw or "").replace("**", "").strip()
    if not clean:
        return "", ""
    # Leading enum word, then anything else as the note — whether glued to a
    # paren ("blocked(等 RW-BACKEND)") or space-separated ("review (dev done)").
    m = re.match(r"^(not_started|in_progress|blocked|review|done|dropped)\b(.*)$", clean)
    if m:
        note = m.group(2).strip().strip("()（）").strip()
        return m.group(1), note
    # First token isn't a known status word — keep the whole thing as base,
    # no note split (e.g. cadence "Frequency" cells never reach here).
    return clean, ""


def _parse_task_table(section: str, priority: str) -> list[Task]:
    """Collect task rows from EVERY markdown table inside the section, not just
    the first. A priority section (## P0 …) may hold several tables split by
    ### sub-headings (e.g. "### Web v2.0", "### Research Workbench"); all of
    their rows belong to the same priority. The section text is already bounded
    to a single ## block by the caller, so we won't bleed into the next one."""
    tasks: list[Task] = []
    lines = section.split("\n")
    in_table = False
    for line in lines:
        if re.match(r"^\|\s*---", line):
            in_table = True
            continue
        if not in_table:
            continue
        stripped = line.strip()
        if stripped == "" or stripped.startswith("###"):
            # Blank line or ### sub-group label *inside* the table (e.g.
            # "### Web v2.0", "### Research Workbench"). Rows resume after it
            # with the same columns — stay in the table, don't stop.
            continue
        if not line.startswith("|"):
            # Genuine end of table (prose / blockquote). The chunk is bounded
            # to one ## section, so a later |--- can still start a new table.
            in_table = False
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        tid = cells[0]
        if not tid or tid.lower() == "id":
            continue
        base_status, status_note = _split_status(cells[3] if len(cells) > 3 else "")
        tasks.append(
            Task(
                id=tid,
                title=cells[1] if len(cells) > 1 else "",
                owner=cells[2] if len(cells) > 2 else "",
                status=base_status,
                next_action=cells[4] if len(cells) > 4 else "",
                evidence=cells[5] if len(cells) > 5 else "",
                priority=priority,
                status_note=status_note,
            )
        )
    return tasks


def _parse_user_input(section: str) -> list[UserInput]:
    items: list[UserInput] = []
    lines = section.split("\n")
    in_table = False
    for line in lines:
        if re.match(r"^\|\s*---", line):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        # Tolerate both the 5-col (USER-id | Needed | Blocks | Idle | Status)
        # and 4-col (USER-id | Needed | Blocks | Status — no Idle) BOARD formats.
        if len(cells) < 4:
            continue
        if cells[0].lower() in {"user-id", ""}:
            continue
        if len(cells) >= 5:
            items.append(
                UserInput(
                    id=cells[0], needed_from_user=cells[1], blocks=cells[2],
                    idle=cells[3], status=cells[4],
                )
            )
        else:  # 4 columns — no Idle column
            items.append(
                UserInput(
                    id=cells[0], needed_from_user=cells[1], blocks=cells[2],
                    idle="", status=cells[3],
                )
            )
    return items


def _parse_risks(section: str) -> list[Risk]:
    risks: list[Risk] = []
    for line in section.split("\n"):
        if not line.startswith("- "):
            continue
        text = line[2:].strip()
        if not text:
            continue
        resolved = bool(re.search(r"\*\*RESOLVED", text)) or text.startswith("~~")
        risks.append(Risk(text=text, resolved=resolved))
    return risks


def _parse_backbone(section: str) -> list[tuple[str, list[Task]]]:
    groups: list[tuple[str, list[Task]]] = []
    sub_chunks = re.split(r"\n(?=### )", section)
    for sub in sub_chunks:
        m = re.match(r"### (.+?)\n", sub)
        if not m:
            continue
        sub_title = m.group(1).strip()
        tasks = _parse_task_table(sub, "Backbone")
        if tasks:
            groups.append((sub_title, tasks))
    return groups


# ── OKR.md ────────────────────────────────────────────────────────────────


_RE_KR = re.compile(r"^-\s*(KR\d+)([^:：]*)[:：]\s*(.+)$")


def parse_okr(text: str) -> OKR:
    okr = OKR()

    # Mission: prose between the H1 title and the first ## section.
    mission_match = re.search(r"^#\s+[^\n]+\n(.*?)(?=\n## )", text, re.S)
    if mission_match:
        okr.mission = mission_match.group(1).strip()

    op_match = re.search(r"## Operating Principles\n(.+?)(?=\n## )", text, re.S)
    if op_match:
        okr.operating_principles = [
            line.lstrip("- ").strip()
            for line in op_match.group(1).split("\n")
            if line.strip().startswith("-")
        ]

    versions = re.findall(r"\n## v(\d+):\s*([^\n]+)\n(.*?)(?=\n## |\Z)", text, re.S)
    if versions:
        versions.sort(key=lambda v: int(v[0]), reverse=True)
        n, label, body = versions[0]
        okr.version = f"v{n}: {label.strip()}"
        okr.objectives = _parse_okr_objectives(body)
        ag_match = re.search(r"### Anti-Goals\n(.+?)(?=\n### |\n## |\Z)", body, re.S)
        if ag_match:
            okr.anti_goals = [
                line.lstrip("- ").strip()
                for line in ag_match.group(1).split("\n")
                if line.strip().startswith("-")
            ]

    # Version log: the ## Versioning section's bullets (vN: description).
    vlog_match = re.search(r"## Versioning\n(.+?)(?=\n## |\Z)", text, re.S)
    if vlog_match:
        for line in vlog_match.group(1).split("\n"):
            vm = re.match(r"-\s*(v\d+)[:：]\s*(.+)$", line.strip())
            if vm:
                okr.version_log.append((vm.group(1), vm.group(2).strip()))

    return okr


def _parse_okr_objectives(body: str) -> list[Objective]:
    objs: list[Objective] = []
    chunks = re.split(r"\n(?=### Objective \d+)", body)
    for chunk in chunks:
        m = re.match(r"### Objective (\d+)[:：]?\s*([^\n]*)\n", chunk)
        if not m:
            continue
        title = (m.group(2) or "").strip() or f"Objective {m.group(1)}"
        krs: list[KR] = []
        intro_lines: list[str] = []
        seen_kr = False
        for line in chunk.split("\n")[1:]:  # skip the heading line
            km = _RE_KR.match(line.strip())
            if km:
                seen_kr = True
                krs.append(KR(id=km.group(1), qualifier=km.group(2).strip(), text=km.group(3).strip()))
            elif not seen_kr and line.strip():
                intro_lines.append(line.strip())
        objs.append(Objective(
            title=title,
            raw_body=chunk,
            intro=" ".join(intro_lines).strip(),
            krs=krs,
        ))
    return objs


# ── phase/<slug>.md ───────────────────────────────────────────────────────


def parse_phase(slug: str, text: str) -> Phase:
    # Section labels are bilingual: a project's document language may be English
    # or 中文 (per .perry/config.md), so the phase file can use either set of
    # headers. Match both. Chinese uses a fullwidth colon （：）in some labels.
    phase = Phase(slug=slug, raw_text=text)

    m = re.match(r"#\s*(?:Phase|阶段)\s*#(\d+)\s*[—\-–]\s*([^\n（(]*)", text)
    if m:
        phase.number = m.group(1)
    started = re.search(r"(?:Started|启动)\s*\**\s*[:：]\s*\**\s*([^\n（(*]+)", text)
    if started:
        phase.started = started.group(1).strip()

    focus = re.search(r"## (?:Phase Focus|阶段焦点)[^\n]*\n(.+?)(?=\n## )", text, re.S)
    if focus:
        phase.focus = focus.group(1).strip()

    cc = re.search(r"## (?:Cost Ceiling|成本上限)[^\n]*\n(.+?)(?=\n## )", text, re.S)
    if cc:
        phase.cost_ceiling_raw = cc.group(1).strip()
        phase.cost_ceiling_lines = [
            line.lstrip("- ").strip()
            for line in phase.cost_ceiling_raw.split("\n")
            if line.strip().startswith("-")
        ]

    tw = re.search(r"## (?:Trip-wires|触发线|触发条件)[^\n]*\n(.+?)(?=\n## )", text, re.S)
    if tw:
        phase.tripwires = _parse_tripwires(tw.group(1))

    obj_chunks = re.split(r"\n(?=## (?:Objective|目标)\s*\d+)", text)
    for chunk in obj_chunks:
        m = re.match(r"## (?:Objective|目标)\s*(\d+)\s*[:：]?\s*([^\n]*)\n", chunk)
        if not m:
            continue
        title = (m.group(2) or "").strip() or f"Objective {m.group(1)}"
        phase.objectives.append(Objective(title=title, raw_body=chunk))

    return phase


def _parse_tripwires(section: str) -> list[Tripwire]:
    """Phase tripwires are a markdown table: | Day | Condition | Response |."""
    tw: list[Tripwire] = []
    lines = section.split("\n")
    in_table = False
    idx = 0
    for line in lines:
        if re.match(r"^\|\s*---", line):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            if in_table:
                break
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0].lower() in {"day", ""}:
            continue
        idx += 1
        # Heuristic: status from response wording.
        response = cells[2]
        status = "armed"
        if re.search(r"\b(resolved|fired-resolved|done|closed)\b", response, re.I):
            status = "fired-resolved"
        tw.append(
            Tripwire(
                id=f"#{idx}",
                when=cells[0].replace("**", "").strip(),
                condition=cells[1],
                response=response,
                status=status,
            )
        )
    return tw


# ── PROJECT_STATE.md (Top risks) ──────────────────────────────────────────

# Heuristic patterns for extracting structured risk values from the Top risks
# section. Each top-risk line typically looks like:
#   "**ERROR-RATE 8.21%** ACCEPT until next review; ..." (a value + a verdict)
# or:
#   "**OQ-A timeline unclear** (NEW top risk) — ..." (a qualitative top risk)

_RE_PCT = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def parse_top_risks(text: str) -> list[TopRisk]:
    risks: list[TopRisk] = []
    m = re.search(r"## Top risks[^\n]*\n(.+?)(?=\n## |\Z)", text, re.S)
    if not m:
        return risks
    section = m.group(1)

    for raw_line in section.split("\n"):
        line = raw_line.strip()
        # Accept both bullet (`- `) and numbered (`0. ` / `1. `) list forms.
        m_bullet = re.match(r"^(?:-|\d+\.)\s+(.*)$", line)
        if not m_bullet:
            continue
        body = m_bullet.group(1).strip()
        resolved = bool(re.search(r"\*\*RESOLVED", body)) or body.startswith("~~")

        # Strip leading ~~strike~~ markers for ID/title extraction
        # (keep the original body for the meta field).
        clean = re.sub(r"~~([^~]*)~~", r"\1", body).strip()

        # ID extraction: first **bold** chunk that's NOT a status word.
        STATUS_BOLDS = {"resolved", "new", "approve", "rejected"}
        id_match = None
        for bm in re.finditer(r"\*\*([^*]+?)\*\*", clean):
            heading_text = bm.group(1).strip()
            first_word_lower = heading_text.split()[0].lower() if heading_text else ""
            if first_word_lower not in STATUS_BOLDS:
                id_match = bm
                break

        if id_match:
            heading = id_match.group(1).strip()
            first = heading.split()[0] if heading else "?"
            short_id = first.rstrip(":,.")
            title = heading[len(first):].strip()
            # If title is empty (e.g. "**R-2** 33.16%"), pull text after the bold.
            if not title:
                after = clean[id_match.end():].strip()
                title = after.split(" — ")[0].split("·")[0].strip()
        else:
            # No useful bold: fall back to first space-separated token.
            first_word = re.match(r"(\S+)", clean)
            short_id = first_word.group(1).rstrip(",.:;") if first_word else "?"
            title = clean[len(short_id):].strip().split(" — ")[0].strip()

        meta = body
        # value: first percentage in line
        pct_match = _RE_PCT.search(body)
        value = float(pct_match.group(1)) if pct_match else None

        # severity heuristic
        if resolved:
            sev = "resolved"
        elif "TOP RISK" in body.upper() or "(NEW top risk" in body:
            sev = "top"
        elif "APPROVE" in body or "豁免" in body or "接受" in body:
            sev = "accept"
        else:
            sev = "watch"

        risks.append(
            TopRisk(
                id=short_id,
                title=title or short_id,
                severity=sev,
                meta=meta,
                value=value,
            )
        )
    return risks


# ── DECISIONS.md ──────────────────────────────────────────────────────────


def parse_decisions(text: str) -> list[ADR]:
    adrs: list[ADR] = []
    in_active = False
    in_table = False
    for line in text.split("\n"):
        if line.startswith("## "):
            in_active = "Active" in line or "进行中" in line
            in_table = False
            continue
        if not in_active:
            continue
        if re.match(r"^\|\s*---", line):
            in_table = True
            continue
        if not in_table or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        first = cells[0]
        if first.lower().startswith("adr") and "id" in first.lower():
            continue
        link_match = re.match(r"\[(ADR-\d+)\]\(([^)]+)\)", first)
        if link_match:
            adr_id = link_match.group(1)
            adr_path = link_match.group(2)
        else:
            adr_id = first
            adr_path = ""
        adrs.append(
            ADR(
                id=adr_id,
                title=cells[1] if len(cells) > 1 else "",
                type=cells[2] if len(cells) > 2 else "",
                date=cells[3] if len(cells) > 3 else "",
                sunset_or_notes=cells[4] if len(cells) > 4 else "",
                file_path=adr_path,
            )
        )

    # Sort newest first by ADR number (e.g. ADR-024 before ADR-001).
    def _adr_num(a: ADR) -> int:
        m = re.search(r"(\d+)", a.id)
        return int(m.group(1)) if m else 0

    adrs.sort(key=_adr_num, reverse=True)
    return adrs


# ── evidence/ + journal/ ──────────────────────────────────────────────────


def walk_evidence(root: Path) -> list[EvidenceFile]:
    out: list[EvidenceFile] = []
    base = root / "evidence"
    if not base.is_dir():
        return out
    for md in base.rglob("*.md"):
        try:
            st = md.stat()
        except OSError:
            continue
        rel = md.relative_to(root).as_posix()
        out.append(
            EvidenceFile(
                path=md.as_posix(),
                rel=rel,
                name=md.name,
                month=md.parent.name,
                mtime=st.st_mtime,
                size=st.st_size,
            )
        )
    out.sort(key=lambda e: e.mtime, reverse=True)
    return out


def walk_journal(root: Path) -> list[JournalEntry]:
    out: list[JournalEntry] = []
    base = root / "journal"
    if not base.is_dir():
        return out
    for md in base.rglob("*.md"):
        if not re.match(r"\d{4}-\d{2}-\d{2}\.md", md.name):
            continue
        out.append(
            JournalEntry(
                date=md.stem,
                month=md.parent.name,
                path=md.as_posix(),
                rel=md.relative_to(root).as_posix(),
            )
        )
    out.sort(key=lambda j: j.date, reverse=True)
    return out


def walk_handoff(root: Path) -> list[JournalEntry]:
    """Handoff docs are flat: handoff/<YYYY-MM-DD>.md (no month subdir).
    Reuses JournalEntry; month is derived from the date prefix."""
    out: list[JournalEntry] = []
    base = root / "handoff"
    if not base.is_dir():
        return out
    for md in base.glob("*.md"):
        if not re.match(r"\d{4}-\d{2}-\d{2}\.md", md.name):
            continue
        out.append(
            JournalEntry(
                date=md.stem,
                month=md.stem[:7],
                path=md.as_posix(),
                rel=md.relative_to(root).as_posix(),
            )
        )
    out.sort(key=lambda j: j.date, reverse=True)
    return out


# ── design/<DESIGN-ID>-<slug>.md (design-skill RFC docs) ──────────────────

# Display + sort priority. Lower index = higher up the page.
_DESIGN_STATUS_ORDER = {
    "in_review": 0,   # needs decisions — surface first
    "locked": 1,      # decided; may need impl tasks
    "draft": 2,       # still being written
    "superseded": 3,  # historical
    "dropped": 4,     # historical
}


def _norm_design_status(text: str) -> str:
    """The Status line is freeform prose ('Design locked（2026…）', 'locked',
    'in_review', 'superseded by DESIGN-009'…). Normalize to the base enum by
    keyword. Order matters: superseded/dropped before locked before review."""
    t = (text or "").lower()
    if "superseded" in t:
        return "superseded"
    if "dropped" in t or "abandoned" in t:
        return "dropped"
    if "lock" in t:
        return "locked"
    if "in_review" in t or "in review" in t or "review" in t:
        return "in_review"
    if "draft" in t:
        return "draft"
    return "draft"


def walk_design(root: Path, board: BoardState | None = None) -> list[DesignDoc]:
    """Parse design/<ID>-<slug>.md RFC docs. Headers are bilingual & freeform
    (em-dash or colon title sep; '> Status:' value embedded in prose;
    '> **Date**:' fullwidth colons), so all field extraction is lenient."""
    out: list[DesignDoc] = []
    base = root / "design"
    if not base.is_dir():
        return out

    # Pre-index BOARD task text once for impl back-reference counting.
    task_blobs: list[str] = []
    if board is not None:
        for t in board.all_tasks:
            task_blobs.append(
                " ".join([t.id or "", t.title or "", t.next_action or "", t.evidence or ""])
            )

    for md in sorted(base.glob("*.md")):
        if md.name.upper() == "README.MD":
            continue
        text = md.read_text(errors="replace")

        # ID from filename: leading <LETTERS>-<digits> (DESIGN-008, INFRA-001).
        fm = re.match(r"([A-Za-z]+-\d+)", md.name)
        doc_id = fm.group(1).upper() if fm else md.stem

        # Header block = everything before the first '## ' section.
        head = re.split(r"\n##\s", text, maxsplit=1)[0]

        # Title: H1, strip the leading "<ID> — " / "<ID>: " prefix.
        title = doc_id
        h1 = re.search(r"^#\s+(.+)$", head, re.M)
        if h1:
            t = h1.group(1).strip()
            t = re.sub(r"^[A-Za-z]+-\d+\s*[—\-–:：]\s*", "", t).strip()
            title = t or doc_id

        def field_line(label_pat: str) -> str:
            m = re.search(
                rf">?\s*\*{{0,2}}(?:{label_pat})\*{{0,2}}\s*[:：]\s*(.+)",
                head, re.I,
            )
            return m.group(1).strip() if m else ""

        status_raw = field_line(r"Status|状态")
        status = _norm_design_status(status_raw)

        date_raw = field_line(r"Date|日期")
        dm = re.search(r"\d{4}-\d{2}-\d{2}", date_raw)
        date = dm.group(0) if dm else ""

        # Locked date: explicit "Locked:" field, else from status prose.
        locked = ""
        lm = re.search(r"Locked\*{0,2}\s*[:：]\s*\*{0,2}(\d{4}-\d{2}-\d{2})", head, re.I)
        if lm:
            locked = lm.group(1)
        elif status == "locked":
            slm = re.search(r"\d{4}-\d{2}-\d{2}", status_raw)
            if slm:
                locked = slm.group(0)

        linked_okr = field_line(r"Linked OKR|关联\s*OKR|关联目标")

        impl_refs = sum(1 for blob in task_blobs if doc_id in blob)

        out.append(
            DesignDoc(
                id=doc_id,
                title=title,
                status=status,
                status_raw=status_raw,
                date=date,
                locked=locked,
                linked_okr=linked_okr,
                rel=md.relative_to(root).as_posix(),
                impl_refs=impl_refs,
                section_count=len(re.findall(r"^##\s", text, re.M)),
                mermaid="```mermaid" in text,
            )
        )

    # Primary: status band (in_review → locked → draft → historical).
    # Secondary: newer date first within each band.
    out.sort(key=lambda d: (_DESIGN_STATUS_ORDER.get(d.status, 9), _date_desc_key(d.date), d.id))
    return out


def _date_desc_key(date: str) -> str:
    """Sort key that orders dates descending while keeping the status band
    (applied as the primary key by the caller). Empty dates sort last."""
    return "0000-00-00" if not date else "".join(str(9 - int(c)) if c.isdigit() else c for c in date)


# ── PROJECT_STATE.md (structured sections) ────────────────────────────────


def parse_project_state(text: str) -> ProjectState:
    ps = ProjectState()
    if not text:
        return ps

    m = re.search(r"Last updated:\s*([^\n(]+)", text)
    if m:
        ps.last_updated = m.group(1).strip()

    # ## Phase — bullet lines
    ph = re.search(r"## Phase\n(.+?)(?=\n## )", text, re.S)
    if ph:
        ps.phase_lines = [
            line.lstrip("- ").strip()
            for line in ph.group(1).split("\n")
            if line.strip().startswith("-")
        ]

    # ## Cross-monthly carry-forwards — markdown table
    cf = re.search(r"## Cross-monthly carry-forwards\n(.+?)(?=\n## )", text, re.S)
    if cf:
        in_table = False
        for line in cf.group(1).split("\n"):
            if re.match(r"^\|\s*---", line):
                in_table = True
                continue
            if not in_table or not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 5 or cells[0].lower() == "id":
                continue
            ps.carry_forwards.append(
                CarryForward(
                    id=cells[0], origin=cells[1], description=cells[2],
                    owner=cells[3], target=cells[4],
                )
            )

    # ## Recent cross-session work — top-level bullets (skip nested sub-bullets)
    cs = re.search(r"## Recent cross-session work\n(.+?)(?=\n## )", text, re.S)
    if cs:
        for line in cs.group(1).split("\n"):
            if re.match(r"^- ", line):  # top-level only (no leading spaces)
                ps.cross_session.append(line[2:].strip())

    # ## Key external dependencies — bullets
    ed = re.search(r"## Key external dependencies\n(.+?)(?=\n## |\Z)", text, re.S)
    if ed:
        for line in ed.group(1).split("\n"):
            if line.strip().startswith("- "):
                ps.external_deps.append(line.strip()[2:].strip())

    return ps


# ── ARCHITECTURE.md (metadata header only; body rendered by serve.py) ──────


def parse_arch_meta(text: str) -> ArchMeta:
    meta = ArchMeta()
    if not text:
        return meta
    meta.exists = True

    # Header line: "> Owner: ... · Version: **v2.0** · Last reviewed: 2026-05-29 · Status: **draft ...**"
    vm = re.search(r"Version:\s*\*{0,2}([^*·\n]+)", text)
    if vm:
        meta.version = vm.group(1).strip()
    lm = re.search(r"Last reviewed:\s*([^*·\n]+)", text)
    if lm:
        meta.last_reviewed = lm.group(1).strip()
    sm = re.search(r"Status:\s*\*{0,2}([^*·\n]+)", text)
    if sm:
        meta.status = sm.group(1).strip()

    meta.section_count = len(re.findall(r"^## §", text, re.M))
    meta.mermaid_count = text.count("```mermaid")

    # §7 open questions: count OQ-N tokens not marked done (no ✅ on the line)
    s7 = re.search(r"## §7[^\n]*\n(.+?)(?=\n## |\Z)", text, re.S)
    if s7:
        for line in s7.group(1).split("\n"):
            if re.search(r"\bOQ-\d+\b", line) and "✅" not in line:
                meta.open_questions += 1

    return meta


# ── Top-level snapshot ────────────────────────────────────────────────────


@dataclass
class PMOSnapshot:
    board: BoardState
    okr: OKR
    phase: Phase | None
    top_risks: list[TopRisk]
    adrs: list[ADR]
    evidence: list[EvidenceFile]
    journal: list[JournalEntry]
    handoff: list[JournalEntry]
    design: list[DesignDoc]
    project_state: ProjectState
    arch_meta: ArchMeta
    project_root: Path
    project_name: str
    fetched_at: datetime


def _resolve_project_name(root: Path, board_text: str) -> str:
    # Prefer the BOARD.md H1 suffix ("# Board — <name>"), else the root dir name.
    m = re.match(r"#\s+Board\s*[—\-–]\s*(.+)", board_text)
    if m:
        return m.group(1).strip()
    return root.name or "Perry"


def load_snapshot(root: Path = PROJECT_ROOT) -> PMOSnapshot:
    def read(p: Path) -> str:
        return p.read_text() if p.exists() else ""

    board_text = read(root / "BOARD.md")
    okr_text = read(root / "OKR.md")
    decisions_text = read(root / "DECISIONS.md")
    project_state_text = read(root / "PROJECT_STATE.md")
    architecture_text = read(root / "ARCHITECTURE.md")

    phase = None
    cur_pointer = root / "phase" / "CURRENT"
    if cur_pointer.exists():
        slug = cur_pointer.read_text().strip()
        phase_file = root / "phase" / f"{slug}.md"
        if phase_file.exists():
            phase = parse_phase(slug, phase_file.read_text())

    # Merge top risks from BOARD.md (most-recent, often holds the acute "TOP"
    # entry) and PROJECT_STATE.md (cross-monthly, more structured). Dedupe by ID.
    top_risks = parse_top_risks(board_text) + parse_top_risks(project_state_text)
    seen: set[str] = set()
    deduped: list[TopRisk] = []
    for r in top_risks:
        key = (r.id or "").lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(r)

    board = parse_board(board_text) if board_text else BoardState()

    return PMOSnapshot(
        board=board,
        okr=parse_okr(okr_text) if okr_text else OKR(),
        phase=phase,
        top_risks=deduped,
        adrs=parse_decisions(decisions_text) if decisions_text else [],
        evidence=walk_evidence(root),
        journal=walk_journal(root),
        handoff=walk_handoff(root),
        design=walk_design(root, board),
        project_state=parse_project_state(project_state_text),
        arch_meta=parse_arch_meta(architecture_text),
        project_root=root,
        project_name=_resolve_project_name(root, board_text),
        fetched_at=datetime.now(),
    )


if __name__ == "__main__":
    s = load_snapshot()
    print(f"Project root: {s.project_root}")
    print(f"P0={len(s.board.p0)} P1={len(s.board.p1)} P2={len(s.board.p2)}")
    print(f"Backbone groups: {len(s.board.backbone_groups)}")
    print(f"User Input Q: {len(s.board.user_input_queue)}")
    print(f"Top risks (PROJECT_STATE): {len(s.top_risks)}")
    print(f"OKR version: {s.okr.version}, objectives: {len(s.okr.objectives)}")
    print(f"Phase: {s.phase.slug if s.phase else '(none)'} #{s.phase.number if s.phase else ''}")
    if s.phase:
        print(f"  · tripwires: {len(s.phase.tripwires)}")
        print(f"  · cost-ceiling lines: {len(s.phase.cost_ceiling_lines)}")
    print(f"ADRs: {len(s.adrs)} · Evidence: {len(s.evidence)} · Journal: {len(s.journal)}")
    print(f"Design docs: {len(s.design)}")
    for d in s.design:
        print(f"  · {d.id:<10} [{d.status:<10}] refs={d.impl_refs} {d.date or '----------'} {d.title[:50]}")
