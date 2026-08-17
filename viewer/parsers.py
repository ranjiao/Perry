"""Markdown parsers for a Perry project's state files. Read-only — never writes.

The viewer ships inside the Perry skill but renders the *project* it's pointed
at (where BOARD.md / OKR.md live), NOT the skill directory. Project root is
resolved from $PERRY_PROJECT, else by walking up from the current working dir
to the nearest ancestor containing BOARD.md or OKR.md."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

# ── localization glossary ─────────────────────────────────────────────────
#
# A project writes its state files in the language declared by
# `.perry/config.md § Document language`, so a section heading may read
# `## Top risks` or `## 主要风险` and a column header `Owner` or `负责人`.
# Which spellings count is declared once, in `schema/state-schema.json §
# i18n`, so this reader, `bin/perry-lint` and any external frontend agree.
# See `reference/i18n.md` for the contract.

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "state-schema.json"


@lru_cache(maxsize=1)
def _i18n() -> dict:
    """The schema's i18n block, or {} when the schema isn't readable.

    Missing glossary degrades to English-only matching rather than raising —
    the parsers must keep working against a bare checkout."""
    try:
        return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8")).get("i18n", {}) or {}
    except Exception:
        return {}


@lru_cache(maxsize=256)
def alias(kind: str, canonical: str) -> tuple[str, ...]:
    """Canonical English name plus every localized spelling declared for it.

    `kind` is "headings" or "columns". Unknown names return just the
    canonical form, which is what an un-glossaried language should get."""
    entry = ((_i18n().get(kind) or {}).get(canonical)) or {}
    out = [canonical]
    for spellings in entry.values():
        for s in spellings:
            if s not in out:
                out.append(s)
    return tuple(out)


def heading_is(head: str, canonical: str) -> bool:
    """True when `head` opens the section named `canonical`, in any language."""
    return any(head.startswith(a) for a in alias("headings", canonical))


@lru_cache(maxsize=1)
def _column_index() -> dict[str, tuple[str, ...]]:
    """Lowered column spelling -> every lowered spelling of the same column.

    Keyed by alias as well as by canonical name so a lookup succeeds whichever
    spelling the caller happens to hold."""
    idx: dict[str, tuple[str, ...]] = {}
    for canonical, per_lang in (_i18n().get("columns") or {}).items():
        spellings = [canonical, *[s for v in per_lang.values() for s in v]]
        lowered = tuple(dict.fromkeys(s.strip().lower() for s in spellings))
        for s in lowered:
            idx[s] = lowered
    return idx


def _column_keys(canonical: str) -> tuple[str, ...]:
    """Lowercased header keys that satisfy `canonical`, in any language."""
    key = canonical.strip().lower()
    return _column_index().get(key, (key,))


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


def resolve_state_root(project_root: Path) -> Path:
    """Where this project's Perry state files live.

    Defaults to the project root, which is what every project written before
    this field existed assumes. A project that already uses a name Perry claims
    — `design/` is the common one — declares `State root: <relpath>` in
    `.perry/config.md` and Perry's whole tree moves under it.

    `.perry/` itself never moves: it is the anchor that says "this is a Perry
    project" and it is where the pointer lives, so it cannot be behind the
    pointer. Every reader must resolve the root the same way, which is why this
    lives here and not in a caller."""
    cfg = project_root / ".perry" / "config.md"
    if not cfg.exists():
        return project_root
    m = re.search(r"State root\s*[:：]\s*([^\n]+)", cfg.read_text(errors="replace"), re.I)
    if not m:
        return project_root
    raw = m.group(1).strip().strip("*`  ")
    if not raw or raw in {".", "./", "—", "-"}:
        return project_root
    root = (project_root / raw).resolve()
    # A state root outside the project is a misconfiguration, not a feature:
    # every path Perry writes and every path the frontend reads is relative to
    # the project, and escaping it would silently point two readers elsewhere.
    if project_root not in root.parents and root != project_root:
        return project_root
    return root


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
    verification: str = ""  # V0..V6 rung (DESIGN-003 § 5.3); "" = unrated


@dataclass
class UserInput:
    id: str
    needed_from_user: str
    blocks: str
    idle: str
    status: str
    priority: str = ""  # inferred P0 if blocks a P0 task
    asked: str = ""     # YYYY-MM-DD the question was put; idle is derived from it


@dataclass
class Cadence:
    """One row of `BOARD.md § Cadence` — a recurring ritual, not a task.

    The section had readers and no writer until TASK-021, and the only reader
    was `_parse_task_table`, which is built for a table this is not. On the
    canonical cadence header its positional fallbacks land `Frequency` in
    `status`, `Next due` in `next_action` and `Last evidence` in `evidence` —
    so every cadence row in `perry-state --json` claimed a status of `weekly`,
    a value the task enum does not contain and `tests/test_i18n.py` has to
    special-case by heading to stay green.

    This is the shape the register actually has. `next_due` is a stamped
    absolute date — an assertion, not a clock — and `last_run` is the input it
    was computed from, so a reader can check it instead of trusting it. Both
    cells are free text on a real board: `n/a`, `continuous`, `2026-W32`, and
    `**2026-08-31**（…）` are all live in one project's register today, and
    none of them is a date this dataclass may reject. Parsing them is
    `bin/perry-state`'s job and it reports what it could not read.
    """
    id: str
    title: str
    owner: str
    frequency: str
    next_due: str
    last_run: str = ""
    last_evidence: str = ""


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
class ScopeTrigger:
    """One trigger from a phase file's `## Phase Scope Reduction Rule` section.

    The skill vocabulary is "scope-reduction trigger" (see goals/SKILL.md
    § plan-phase step 6). Legacy projects that still carry a `## Trip-wires`
    table are parsed into the same shape."""
    id: str        # synthesized, e.g. "#1"
    when: str      # phase day, if the trigger names one
    condition: str
    response: str
    kind: str = ""  # 'phase-day' | 'kr-progress' | '' (legacy table rows)
    status: str = "armed"  # 'armed' | 'disarmed' | 'tripped'


@dataclass
class BoardState:
    last_updated_header: str = ""
    p0: list[Task] = field(default_factory=list)
    p1: list[Task] = field(default_factory=list)
    p2: list[Task] = field(default_factory=list)
    # Both views of `## Cadence`, produced by ONE parse. `cadence_items` is the
    # register's real shape; `cadence` is the task-shaped projection the viewer
    # template, `all_tasks` and the drift exclusion have always consumed. They
    # are derived from each other rather than parsed separately, because two
    # parsers of one table is the defect this repository has now fixed three
    # times (`schema/README.md § Columns resolve by name`).
    cadence_items: list[Cadence] = field(default_factory=list)
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
    id: str              # e.g. "KR-O1.1" (OKR.md) or "P-O1.2" (phase file)
    text: str            # the key-result statement
    qualifier: str = ""  # optional parenthetical, e.g. "(Phase 1, 系统建设期)"
    metric: str = ""     # 'Metric / Target' column, when the KR came from a table
    linked: str = ""     # phase KR → overall KR id ('Linked overall KR' column)
    stretch: bool = False


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
    status: str = ""          # 'active' | 'scored' (from the header block)
    focus: str = ""
    objectives: list[Objective] = field(default_factory=list)
    cost_ceiling_raw: str = ""
    cost_ceiling_lines: list[str] = field(default_factory=list)
    scope_triggers: list[ScopeTrigger] = field(default_factory=list)
    raw_text: str = ""

    @property
    def day(self) -> int | None:
        """Phase day = calendar days since `Started:`, 1-indexed (start = day 1).

        None when the header carries no parseable date — callers render '—'
        rather than a wrong number."""
        m = re.search(r"\d{4}-\d{2}-\d{2}", self.started or "")
        if not m:
            return None
        try:
            start = datetime.strptime(m.group(0), "%Y-%m-%d").date()
        except ValueError:
            return None
        return (datetime.now().date() - start).days + 1

    @property
    def krs(self) -> list[KR]:
        return [kr for o in self.objectives for kr in o.krs]


@dataclass
class LinkageProject:
    """One `projects:` entry in `phase/<NNN>-linkage.md` — the Project↔KR
    registry that keeps attribution from being guessed."""
    project_id: str
    serves_kr: str
    objective: str
    name: str
    aliases: list[str] = field(default_factory=list)
    status: str = "active"   # active | done | dropped | unlinked


@dataclass
class LinkageKR:
    id: str
    title: str
    metric: str = ""
    target: float | None = None
    current: float | None = None
    due: str = ""
    stretch: bool = False
    tasks: list[str] = field(default_factory=list)


@dataclass
class LinkageObjective:
    id: str
    title: str
    krs: list[LinkageKR] = field(default_factory=list)


@dataclass
class LinkageAgent:
    id: str
    tasks: list[str] = field(default_factory=list)


@dataclass
class Linkage:
    """`phase/<NNN>-linkage.md` — the O→KR→task→agent graph.

    Machine-written by `okr plan-phase` / `plan-week`, machine-read by Perry
    (attribution) and by the frontend (the chain view). YAML frontmatter, spec
    version 1 — see $PERRY_HOME/schema/README.md § The linkage contract."""
    spec: int = 0
    phase: str = ""
    updated: str = ""
    objectives: list[LinkageObjective] = field(default_factory=list)
    unlinked: list[str] = field(default_factory=list)
    agents: list[LinkageAgent] = field(default_factory=list)
    projects: list[LinkageProject] = field(default_factory=list)
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.spec > 0 and not self.error

    def kr_for_task(self, task_id: str) -> str:
        """Direct task→KR edge, when the graph declares one."""
        for obj in self.objectives:
            for kr in obj.krs:
                if task_id in kr.tasks:
                    return kr.id
        return ""


@dataclass
class OpsCounts:
    """Cheap directory / INDEX-header counts used by the standup dashboard."""
    inputs: int = 0
    inputs_oldest: str = ""
    inputs_oldest_days: int | None = None
    knowledge_index: str = ""     # raw header line from knowledge/INDEX.md
    runbook_index: str = ""
    incidents_index: str = ""


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

        # P0/P1/P2 are priority enum values, invariant across languages; the
        # prose headings below resolve through the schema glossary.
        if head.startswith("P0"):
            state.p0 = _parse_task_table(chunk, "P0")
        elif head.startswith("P1"):
            state.p1 = _parse_task_table(chunk, "P1")
        elif head.startswith("P2"):
            state.p2 = _parse_task_table(chunk, "P2")
        elif heading_is(head, "Cadence"):
            state.cadence_items = _parse_cadence(chunk)
            state.cadence = [_cadence_as_task(c) for c in state.cadence_items]
        elif heading_is(head, "User Input Queue"):
            state.user_input_queue = _parse_user_input(chunk)
        elif heading_is(head, "Top risks"):
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
    prev = ""
    # EVERY column is resolved by HEADER NAME, never by position.
    #
    # The argument was written for `Verification` alone — "a board with an extra
    # column would silently rate the wrong cell" — and then applied to that one
    # column while the other six stayed positional. `bin/perry-task` places
    # cells by resolved header name and `check_header` accepts the six required
    # columns in any order, so the writer and the only reader disagreed about
    # what a board row means. On a header of `| ID | Title | Track | Owner |
    # Status | …`, every field shifted one place: `owner` read the track,
    # `status` read the owner, and `open` counted zero — silently zeroing every
    # standup number, `verification_distribution`, and drift's `stale_done`
    # branch. `perry-lint` reports such a board clean, because column order is
    # not something the schema constrains.
    idx: dict[str, int] = {}
    for line in lines:
        if re.match(r"^\|\s*---", line):
            in_table = True
            header = ([c.strip().lower() for c in prev.strip().strip("|").split("|")]
                      if prev.strip().startswith("|") else [])
            idx = {}
            for name in ("ID", "Title", "Owner", "Status", "Next action",
                         "Evidence", "Verification"):
                keys = _column_keys(name)
                pos = next((i for i, h in enumerate(header) if h in keys), -1)
                if pos >= 0:
                    idx[name] = pos
            continue
        prev = line
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

        def cell(name: str, fallback: int) -> str:
            # Fall back to the canonical position when a header cell is absent
            # or unrecognized, so a board whose headers this build does not know
            # keeps parsing exactly as it did before.
            i = idx.get(name, fallback)
            return cells[i] if 0 <= i < len(cells) else ""

        tid = cell("ID", 0)
        if not tid or tid.strip().lower() in _column_keys("ID"):
            continue
        base_status, status_note = _split_status(cell("Status", 3))
        tasks.append(
            Task(
                id=tid,
                title=cell("Title", 1),
                owner=cell("Owner", 2),
                status=base_status,
                next_action=cell("Next action", 4),
                evidence=cell("Evidence", 5),
                priority=priority,
                status_note=status_note,
                verification=cell("Verification", -1).replace("*", "").strip(),
            )
        )
    return tasks


# ── recurrence arithmetic ─────────────────────────────────────────────────
#
# ONE implementation, here, because it has two callers that must agree:
# `bin/perry-task cadence-add/cadence-done` STAMPS `Next due` from it and
# `bin/perry-state` READS the cell back to decide what is overdue. A writer
# and a reader with separate copies of a period table is the same shape as a
# writer and a reader with separate copies of a column order, and this
# repository has now paid for that three times.
#
# The vocabulary comes off two real registers, not out of a design. `weekly`,
# `monthly`, `quarterly` and `Nd` are the four the task named; `continuous`
# and `hourly` are in a live project's `Frequency` column today and are
# recognized as APERIODIC rather than rejected — a register whose whole
# purpose is to record what repeats may not refuse the words a project uses
# for the things that repeat constantly. An aperiodic row simply has no
# computable due date, which is exactly what that project already writes in
# its `Next due` cell (`n/a`, `continuous`).

_NAMED_PERIODS: dict[str, tuple[int, str]] = {
    "daily": (1, "d"), "nightly": (1, "d"), "every day": (1, "d"),
    "weekly": (1, "w"), "every week": (1, "w"),
    "biweekly": (2, "w"), "fortnightly": (2, "w"), "every other week": (2, "w"),
    "monthly": (1, "m"), "every month": (1, "m"),
    "bimonthly": (2, "m"),
    "quarterly": (3, "m"), "every quarter": (3, "m"),
    "semiannually": (6, "m"), "semi-annually": (6, "m"), "half-yearly": (6, "m"),
    "yearly": (12, "m"), "annually": (12, "m"), "every year": (12, "m"),
}

# Recognized, and deliberately without a period. These are not errors.
_APERIODIC = {
    "continuous", "continuously", "ongoing", "hourly", "ad hoc", "adhoc",
    "ad-hoc", "on demand", "on-demand", "as needed", "as-needed", "n/a", "na",
}

_UNITS = {"d": "d", "day": "d", "days": "d",
          "w": "w", "week": "w", "weeks": "w",
          "m": "m", "month": "m", "months": "m",
          "q": "q", "quarter": "q", "quarters": "q",
          "y": "y", "year": "y", "years": "y"}

_EVERY_N = re.compile(r"^(?:every\s+)?(\d+)\s*([a-z]+)$")


def parse_frequency(cell: str) -> tuple[str, int, str] | None:
    """A `Frequency` cell → `("period", n, unit)` or `("aperiodic", 0, "")`.

    `None` means the cell says something this build does not recognize. That is
    reported by every caller and never guessed at: a frequency read wrongly
    produces a due date that is confidently wrong, which is worse than a cell
    the tool admits it cannot schedule from.
    """
    s = re.sub(r"[\s`*_]+", " ", cell or "").strip().lower()
    if not s:
        return None
    if s in _APERIODIC:
        return ("aperiodic", 0, "")
    if s in _NAMED_PERIODS:
        n, unit = _NAMED_PERIODS[s]
        return ("period", n, unit)
    m = _EVERY_N.match(s)
    if m and _UNITS.get(m.group(2)):
        n, unit = int(m.group(1)), _UNITS[m.group(2)]
        if n <= 0:
            return None
        if unit == "q":
            n, unit = n * 3, "m"
        elif unit == "y":
            n, unit = n * 12, "m"
        return ("period", n, unit)
    return None


def advance(start: date, n: int, unit: str) -> date:
    """`start` plus n days / weeks / months, clamping a short month.

    Month arithmetic is calendar-based rather than 30-day, because the rituals
    this register holds are calendar rituals: a month-end close moved 30 days
    from 31 January lands on 2 March and stops being month-end. The clamp puts
    it on 28 February instead, which is what a human running the close would do.
    """
    if unit == "d":
        return start + timedelta(days=n)
    if unit == "w":
        return start + timedelta(weeks=n)
    if unit != "m":
        raise ValueError(f"unknown unit {unit!r}")
    total = (start.year * 12 + start.month - 1) + n
    year, month = divmod(total, 12)
    month += 1
    # Last day of the target month, so 31 Jan + 1 month is 28/29 Feb.
    first_of_next = (date(year + 1, 1, 1) if month == 12
                     else date(year, month + 1, 1))
    last = (first_of_next - timedelta(days=1)).day
    return date(year, month, min(start.day, last))


def next_due_after(run: date, frequency: str) -> date | None:
    """The date a ritual with this frequency is next due, having run on `run`.

    `None` for an aperiodic or unrecognized frequency — there is nothing to
    compute and the caller says so rather than inventing a date.
    """
    parsed = parse_frequency(frequency)
    if not parsed or parsed[0] != "period":
        return None
    _, n, unit = parsed
    return advance(run, n, unit)


_ISO_WEEK = re.compile(r"(\d{4})-W(\d{1,2})\b", re.I)


def parse_due(cell: str) -> date | None:
    """A `Next due` cell → the date it is late after, or `None`.

    The cell is prose on a real board and this function is the tolerant half of
    the contract. Three live examples from one project's register:

        n/a
        **2026-08-31**（7 月版 ✅ 8/3 补作 → `evidence/2026-08/retro-2026-07.md`）
        **2026-W32 friday-review (8/7)**（W31 版 ✅ 8/3 补作…）

    A bare date wins. Failing that, an ISO week resolves to its **Sunday** —
    a week-scoped ritual is not late on Monday, and taking the Monday would
    report every weekly row as six days overdue for most of its own week.
    Anything else returns `None` and is reported as unreadable rather than
    treated as never due, which would silently exempt it from the only clock
    governing it.
    """
    raw = cell or ""
    m = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    if m:
        try:
            return datetime.strptime(m.group(0), "%Y-%m-%d").date()
        except ValueError:
            return None
    w = _ISO_WEEK.search(raw)
    if w:
        try:
            return date.fromisocalendar(int(w.group(1)), int(w.group(2)), 7)
        except ValueError:
            return None
    return None


def _parse_cadence(section: str) -> list[Cadence]:
    """`BOARD.md § Cadence` — columns resolved by NAME, never by position.

    Fourth implementation of this rule in this file, and the first one written
    knowing what the real tables look like. Two shapes are live right now:

    - `ID | Recurring task | Owner | Frequency | Next due | Last evidence` —
      the template and the schema;
    - `ID | Recurring task | Owner | Frequency | Next due` — a project that
      keeps its evidence links inline in the `Next due` cell and has been
      carrying a `table-columns` lint error for it.

    A third appears the first time `perry-task cadence-done` runs on a board:
    `Last run` joins at the end, because `ensure_section_columns` appends. Under
    a positional rule that column would be read as `Last evidence` on one board
    and as nothing on another. It is resolved by name here, and `Last run` has
    no positional fallback at all — there is no position it has ever occupied,
    and inventing one is how a reader starts making things up.

    The positional fallbacks that DO exist reproduce, exactly, what
    `_parse_task_table` did for this section before it had a parser of its own,
    so a board whose headers this build cannot resolve keeps parsing as it did.
    """
    items: list[Cadence] = []
    idx: dict[str, int] = {}
    prev = ""
    in_table = False
    for line in section.split("\n"):
        if re.match(r"^\|\s*---", line):
            in_table = True
            header = ([c.strip().lower() for c in prev.strip().strip("|").split("|")]
                      if prev.strip().startswith("|") else [])
            idx = {}
            for name in ("ID", "Recurring task", "Title", "Owner", "Frequency",
                         "Next due", "Last run", "Last evidence", "Evidence"):
                keys = _column_keys(name)
                pos = next((i for i, h in enumerate(header) if h in keys), -1)
                if pos >= 0:
                    idx[name] = pos
            continue
        prev = line
        if not in_table:
            continue
        stripped = line.strip()
        if stripped == "" or stripped.startswith("###"):
            # A `###` sub-group label or a blank line inside the section. Rows
            # resume under the same header — same rule as `_parse_task_table`.
            continue
        if not line.startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue

        def cell(name: str, fallback: int = -1) -> str:
            i = idx.get(name, fallback)
            return cells[i] if 0 <= i < len(cells) else ""

        cid = cell("ID", 0)
        if not cid or cid.strip().lower() in _column_keys("ID"):
            continue
        items.append(
            Cadence(
                id=cid,
                # `Recurring task` is this table's name for the column every
                # other table calls `Title`; both resolve, and the canonical
                # position is the same either way.
                title=cell("Recurring task", -1) or cell("Title", 1),
                owner=cell("Owner", 2),
                frequency=cell("Frequency", 3),
                next_due=cell("Next due", 4),
                last_run=cell("Last run"),
                last_evidence=cell("Last evidence", -1) or cell("Evidence", 5),
            )
        )
    return items


def _cadence_as_task(c: Cadence) -> Task:
    """The task-shaped projection of a cadence row, for the consumers that
    predate `Cadence` — `BoardState.all_tasks`, the viewer's board template and
    `perry-state`'s drift exclusion, which keys on `priority == "Cadence"`.

    It is deliberately lossy and deliberately unchanged: `status` carries the
    frequency, which is not a task status and never was. Keeping it means this
    refactor changes no payload; the honest reading is `cadence_items`.
    """
    return Task(
        id=c.id,
        title=c.title,
        owner=c.owner,
        status=_split_status(c.frequency)[0],
        next_action=c.next_due,
        evidence=c.last_evidence,
        priority="Cadence",
        status_note=_split_status(c.frequency)[1],
    )


def _parse_user_input(section: str) -> list[UserInput]:
    """Columns resolved by NAME — see `schema/README.md § Columns resolve by name`.

    This read them positionally, assuming cell 3 of a five-column row was
    `Idle`. Three real shapes are in circulation: five columns with `Idle`
    (Perry's own board), four without it (a live project dropped the column
    because a stored age is stale the moment it is written), and five with
    `Asked` instead. Under the positional rule the third of those puts a date
    into `idle` and reports every request as having waited zero days.

    Third location of this defect. The first two were `_parse_task_table` and
    the writer/reader split it caused.
    """
    items: list[UserInput] = []
    idx: dict[str, int] = {}
    prev = ""
    in_table = False
    for line in section.split("\n"):
        if re.match(r"^\|\s*---", line):
            in_table = True
            header = ([c.strip().lower() for c in prev.strip().strip("|").split("|")]
                      if prev.strip().startswith("|") else [])
            idx = {}
            for name in ("USER-id", "Needed from user", "Blocks", "Asked",
                         "Idle", "Status"):
                keys = _column_keys(name)
                pos = next((i for i, h in enumerate(header) if h in keys), -1)
                if pos >= 0:
                    idx[name] = pos
            continue
        prev = line
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0].strip().lower() in {"", *_column_keys("USER-id")}:
            continue

        def cell(name: str, fallback: int = -1) -> str:
            i = idx.get(name, fallback)
            return cells[i] if 0 <= i < len(cells) else ""

        # Positional fallback only for a header this build cannot resolve, and
        # only in the two shapes that predate `Asked`.
        status = cell("Status", 4 if len(cells) >= 5 else 3)
        items.append(
            UserInput(
                id=cell("USER-id", 0),
                needed_from_user=cell("Needed from user", 1),
                blocks=cell("Blocks", 2),
                asked=cell("Asked"),
                idle=cell("Idle", 3 if len(cells) >= 5 and "Asked" not in idx else -1),
                status=status,
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


# KR ids as written by the templates: "KR-O1.1" (OKR.md), "P-O1.2" (phase file).
# The legacy bullet form ("- KR1: text") is still accepted for hand-written files.
_RE_KR_ID = re.compile(r"^(?:KR|P)[-\w.]*\d$")
_RE_KR_BULLET = re.compile(
    r"^-\s*\**((?:KR|P-O)[\w.\-]*\d)\**([^:：]*)[:：]\s*(.+)$"
)


def _table_rows(section: str) -> list[dict[str, str]]:
    """Parse every markdown table in `section` into header-keyed row dicts.

    Header keys are lowercased and stripped. Rows shorter than the header are
    padded; longer rows are truncated. Returns [] when no table is present."""
    rows: list[dict[str, str]] = []
    header: list[str] = []
    prev_cells: list[str] = []
    for line in section.split("\n"):
        stripped = line.strip()
        if re.match(r"^\|\s*:?-{2,}", stripped):
            header = [c.strip().lower() for c in prev_cells]
            continue
        if not stripped.startswith("|"):
            prev_cells = []
            if not stripped:
                continue
            header = []
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not header:
            prev_cells = cells
            continue
        row = {}
        for i, key in enumerate(header):
            row[key] = cells[i] if i < len(cells) else ""
        rows.append(row)
    return rows


def _col(row: dict[str, str], *names: str) -> str:
    """First non-empty value among `names`, else the first column whose header
    starts with one of them (tolerates 'kr text' vs 'kr').

    Each name is expanded through the schema glossary first, so a table
    written in the project's document language resolves the same way — `_col(
    row, "owner")` also matches a `负责人` header."""
    wanted: list[str] = []
    for n in names:
        for a in _column_keys(n):
            if a not in wanted:
                wanted.append(a)
    for n in wanted:
        if row.get(n):
            return row[n]
    for key, val in row.items():
        if val and any(key.startswith(n) for n in wanted):
            return val
    return ""


def _parse_krs(section: str) -> list[KR]:
    """KRs from a template-style table first, falling back to bullet lines."""
    krs: list[KR] = []
    for row in _table_rows(section):
        kid = _col(row, "id", "kr id")
        if not _RE_KR_ID.match(kid.replace("*", "").strip()):
            continue
        kid = kid.replace("*", "").strip()
        stretch_cell = _col(row, "stretch?", "stretch").lower()
        krs.append(KR(
            id=kid,
            text=_col(row, "kr text", "kr", "key result"),
            metric=_col(row, "metric / target", "metric", "target"),
            linked=_col(row, "linked overall kr", "linked"),
            stretch=stretch_cell.startswith("y") or stretch_cell == "stretch",
        ))
    if krs:
        return krs
    for line in section.split("\n"):
        km = _RE_KR_BULLET.match(line.strip())
        if km:
            krs.append(KR(
                id=km.group(1),
                qualifier=km.group(2).strip(),
                text=km.group(3).strip(),
            ))
    return krs


def _clean_heading_title(raw: str, fallback: str) -> str:
    """'— Ship the pipeline' / ': Ship the pipeline' -> 'Ship the pipeline'."""
    return re.sub(r"^[—\-–:：]\s*", "", (raw or "").strip()).strip() or fallback


def _section(text: str, *heading_alternatives: str, level: str = "## ") -> str:
    """Body of the first heading matching any alternative, up to the next
    heading of the same level. Heading text may carry a suffix ('## Versioning
    log' matches 'Versioning')."""
    alt = "|".join(heading_alternatives)
    m = re.search(
        rf"^{re.escape(level)}(?:{alt})[^\n]*\n(.+?)(?=^{re.escape(level)}|\Z)",
        text, re.S | re.M,
    )
    return m.group(1) if m else ""


_RE_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
_RE_HRULE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")


def _strip_comments(text: str) -> str:
    """Drop HTML comments. Templates park example blocks (`## v2: …`) inside
    comments; parsing them would shadow the real current version."""
    return _RE_HTML_COMMENT.sub("", text)


def _bullets(section: str) -> list[str]:
    out: list[str] = []
    for line in section.split("\n"):
        s = line.strip()
        if not s.startswith("-") or _RE_HRULE.match(s):
            continue
        out.append(s.lstrip("-").strip())
    return out


def parse_okr(text: str) -> OKR:
    okr = OKR()
    text = _strip_comments(text)

    # Mission: the `## Mission` section (template shape). Older hand-written
    # files put the mission as prose between the H1 and the first ## — fall
    # back to that.
    mission = _section(text, "Mission", "使命")
    if not mission:
        m = re.search(r"^#\s+[^\n]+\n(.*?)(?=\n## )", text, re.S)
        mission = m.group(1) if m else ""
    okr.mission = mission.strip()

    okr.operating_principles = _bullets(
        _section(text, "Operating Principles", "运行原则")
    )

    # Anti-Goals live at the top level in the template; some files nest them
    # inside the current version block instead.
    anti = _section(text, "Anti-Goals", "反目标")

    versions = re.findall(r"\n## v(\d+):\s*([^\n]+)\n(.*?)(?=\n## |\Z)", text, re.S)
    if versions:
        versions.sort(key=lambda v: int(v[0]), reverse=True)
        n, label, body = versions[0]
        okr.version = f"v{n}: {label.strip()}"
        okr.objectives = _parse_okr_objectives(body)
        if not anti:
            anti = _section(body, "Anti-Goals", "反目标", level="### ")
    okr.anti_goals = _bullets(anti)

    # Version log: bullets under `## Versioning log` (template) / `## Versioning`.
    for line in _section(text, "Versioning").split("\n"):
        vm = re.match(r"-\s*\**(v\d+)\**[:：]\s*(.+)$", line.strip())
        if vm:
            okr.version_log.append((vm.group(1), vm.group(2).strip()))

    return okr


def _parse_okr_objectives(body: str) -> list[Objective]:
    objs: list[Objective] = []
    chunks = re.split(r"\n(?=### (?:Objective|目标) \d+)", body)
    for chunk in chunks:
        m = re.match(r"### (?:Objective|目标) (\d+)\s*([^\n]*)\n", chunk)
        if not m:
            continue
        title = _clean_heading_title(m.group(2), f"Objective {m.group(1)}")
        krs = _parse_krs(chunk)
        intro_lines = [
            line.strip()
            for line in chunk.split("\n")[1:]
            if line.strip()
            and not line.strip().startswith("|")
            and not line.strip().startswith("#")
            and not _RE_KR_BULLET.match(line.strip())
        ]
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
    text = _strip_comments(text)

    m = re.match(r"#\s*(?:Phase|阶段)\s*#(\d+)\s*[—\-–]\s*([^\n（(]*)", text)
    if m:
        phase.number = m.group(1)
    started = re.search(r"(?:Started|启动)\s*\**\s*[:：]\s*\**\s*([^\n（(*]+)", text)
    if started:
        phase.started = started.group(1).strip()
    st = re.search(r"(?:Status|状态)\s*\**\s*[:：]\s*\**\s*([^\n（(*]+)", text)
    if st:
        phase.status = st.group(1).strip().split("|")[0].strip()

    phase.focus = _section(text, "Phase Focus", "阶段焦点").strip()

    cc = _section(text, "Cost Ceiling", "成本上限")
    if cc:
        phase.cost_ceiling_raw = cc.strip()
        phase.cost_ceiling_lines = _bullets(cc)

    # Scope-reduction triggers. The template section is
    # `## Phase Scope Reduction Rule` (bullet form); legacy projects may carry
    # a `## Trip-wires` table instead — both land in the same shape.
    srr = _section(text, "Phase Scope Reduction Rule", "阶段缩圈规则", "缩圈规则")
    if srr:
        phase.scope_triggers = _parse_scope_triggers(srr)
    else:
        legacy = _section(text, "Trip-wires", "Tripwires", "触发线", "触发条件")
        if legacy:
            phase.scope_triggers = _parse_legacy_tripwire_table(legacy)

    # Status of the rule, when the mid-phase check has recorded one.
    mp = _section(text, "Mid-phase check", "期中检查")
    sm = re.search(
        r"(?:Scope-reduction rule status|缩圈规则状态)\s*\**\s*[:：]\s*\**\s*([^\n]+)",
        mp, re.I,
    )
    if sm:
        raw = sm.group(1).lower()
        # Only a single unambiguous word counts — the template ships the literal
        # placeholder "{{armed / disarmed / tripped}}", which must NOT be read
        # as a real status.
        found = {w for w in ("tripped", "disarmed", "armed") if re.search(rf"\b{w}\b", raw)}
        found |= {"tripped" if "已触发" in raw else "", "disarmed" if "已解除" in raw else ""}
        found.discard("")
        if len(found) == 1:
            status = found.pop()
            for t in phase.scope_triggers:
                t.status = status

    obj_chunks = re.split(r"\n(?=## (?:Objective|目标)\s*\d+)", text)
    for chunk in obj_chunks:
        m = re.match(r"## (?:Objective|目标)\s*(\d+)\s*([^\n]*)\n", chunk)
        if not m:
            continue
        title = _clean_heading_title(m.group(2), f"Objective {m.group(1)}")
        phase.objectives.append(
            Objective(title=title, raw_body=chunk, krs=_parse_krs(chunk))
        )

    return phase


def _parse_scope_triggers(section: str) -> list[ScopeTrigger]:
    """`## Phase Scope Reduction Rule` is a bullet list, one per trigger:

        - **Phase-day trigger** (optional): If by phase day 14 USER-003 is
          still open, O2 collapses to its Must-Have.
        - **KR-progress trigger**: If commit KRs are <50% at phase day 14, …

    Condition = text up to the first comma/`,`; response = the remainder."""
    triggers: list[ScopeTrigger] = []
    for idx, body in enumerate(_bullets(section), start=1):
        label = ""
        lm = re.match(r"\*\*([^*]+)\*\*\s*(?:\([^)]*\))?\s*[:：]?\s*(.*)$", body, re.S)
        if lm:
            label = lm.group(1).strip()
            body = lm.group(2).strip()
        if not body:
            continue
        kind = ""
        low = label.lower()
        if "day" in low or "阶段日" in label:
            kind = "phase-day"
        elif "kr" in low or "进度" in label:
            kind = "kr-progress"
        when = ""
        wm = re.search(r"(?:phase day|阶段第?)\s*\**\s*(\d+)", body, re.I)
        if wm:
            when = wm.group(1)
        # "If <condition>, <consequence>" — split at the LAST comma, so a
        # multi-clause condition ("If at day 14, commit KRs are <50%, cut …")
        # keeps its clauses together instead of splitting after the first one.
        cut = max(body.rfind(", "), body.rfind("，"))
        if cut == -1:
            condition, response = body.strip(), ""
        else:
            condition = body[:cut].strip().rstrip(",，")
            response = body[cut + 1:].strip()
        triggers.append(ScopeTrigger(
            id=f"#{idx}",
            when=when,
            condition=condition,
            response=response,
            kind=kind,
        ))
    return triggers


def _parse_legacy_tripwire_table(section: str) -> list[ScopeTrigger]:
    """Legacy `## Trip-wires` markdown table: | Day | Condition | Response |."""
    tw: list[ScopeTrigger] = []
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
            status = "tripped"
        tw.append(
            ScopeTrigger(
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
    heads = "|".join(re.escape(a) for a in alias("headings", "Top risks"))
    m = re.search(rf"## (?:{heads})[^\n]*\n(.+?)(?=\n## |\Z)", text, re.S)
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
            # If the title is empty or carries no words (e.g. "**R-2** 33.16%",
            # "**DEPLOY-FLAKE 4.2%**"), pull the prose after the bold instead —
            # a bare number is not a risk title.
            if not re.search(r"[A-Za-z一-鿿]{2,}", title):
                after = clean[id_match.end():].strip().lstrip("—-–·:： ")
                # Drop a leading severity marker — "TOP RISK", "ACCEPT until …"
                # is a label, not the title. The prose after it is the title.
                after = re.sub(
                    r"^\(?\s*(?:NEW\s+)?(?:TOP RISK|ACCEPT|APPROVE|WATCH|REJECTED)\b[^—·]*",
                    "", after, flags=re.I,
                ).strip().lstrip("—-–·:： ")
                after = after.split(" — ")[0].split("·")[0].strip()
                title = after or title
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
            in_active = heading_is(line[3:].strip(), "Active")
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


def walk_weekly(root: Path) -> list[JournalEntry]:
    """Weekly reports: weekly/<YYYY-WW>.md. `date` carries the ISO week label."""
    out: list[JournalEntry] = []
    base = root / "weekly"
    if not base.is_dir():
        return out
    for md in base.glob("*.md"):
        if not re.match(r"\d{4}-W?\d{2}\.md", md.name):
            continue
        out.append(
            JournalEntry(
                date=md.stem,
                month=md.stem[:4],
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


# ── phase/<NNN>-linkage.md (Project ↔ KR registry) ────────────────────────


_RE_FRONTMATTER = re.compile(r"\A﻿?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)


def split_frontmatter(text: str) -> tuple[str, str]:
    """(frontmatter, body). Empty frontmatter when the file has none.

    Matches the frontend's `splitFrontmatter` so both sides agree on what
    counts as a fenced block."""
    m = _RE_FRONTMATTER.match(text)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


_BLOCK_SENTINEL = "\x00blk"
_BLOCK_HEAD = re.compile(r"^(\s*(?:-\s+)?)([A-Za-z_][\w.-]*|\"[^\"]+\"|\'[^\']+\'):\s*([|>][-+]?)\s*$")


def _lift_block_scalars(raw_lines: list[str], blocks: dict) -> list[str]:
    """Replace each `key: |` block with a one-line sentinel scalar.

    Runs before comment/blank stripping so markdown headings and paragraph
    breaks inside the block survive verbatim. Chomping indicators (`|-`, `|+`)
    are honoured; anything else after the marker is ignored rather than
    rejected, since this is a reader, not a validator."""
    out: list[str] = []
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        m = _BLOCK_HEAD.match(line)
        if not m:
            out.append(line)
            i += 1
            continue
        prefix, key, marker = m.groups()
        key_indent = len(line) - len(line.lstrip(" "))
        body, j, block_indent = [], i + 1, None
        while j < len(raw_lines):
            nxt = raw_lines[j]
            if nxt.strip() == "":
                body.append("")
                j += 1
                continue
            ind = len(nxt) - len(nxt.lstrip(" "))
            if ind <= key_indent:
                break
            if block_indent is None:
                block_indent = ind
            body.append(nxt[block_indent:] if len(nxt) >= block_indent else nxt.lstrip())
            j += 1
        while body and body[-1] == "":
            body.pop()
        text = "\n".join(body)
        if marker.startswith(">"):
            text = " ".join(t for t in text.splitlines() if t).strip()
        if marker.endswith("+"):
            text += "\n"
        elif not marker.endswith("-") and text:
            text += "\n"
        token = f"{_BLOCK_SENTINEL}{len(blocks)}\x00"
        blocks[token] = text
        out.append(f"{prefix}{key}: {token}")
        i = j
    return out


def parse_yaml_subset(text: str):
    """A deliberately small YAML reader — enough for machine-written Perry
    frontmatter, and nothing more.

    Perry ships with zero dependencies, so PyYAML isn't available. That's
    acceptable here only because these files are *written by Perry* to a
    declared shape: nested maps, lists of maps, scalars, and inline flow lists.
    Anything outside that raises ValueError rather than returning a half-parsed
    structure — a linkage graph that silently loses an objective would report
    committed work as nonexistent.

    Block scalars (`key: |`) ARE supported, because `declarations[].content` is
    specified as verbatim multi-line — an authored KR table cannot live on one
    line, which is the whole reason `candidates[].resolution` could not hold it.
    They are lifted out here rather than in the parser, because the loop below
    strips blank lines and `#` comments, and markdown content is full of both:
    a heading like `## Objective 1` would otherwise be silently eaten.

    Not supported (by design): anchors, multi-document files, nested flow maps,
    tags."""
    blocks: dict[str, str] = {}
    src = _lift_block_scalars(text.split("\n"), blocks)
    lines = []
    for n, raw in enumerate(src, start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        # YAML forbids tabs for indentation, and silently treating one as
        # zero-indent would misplace a whole objective.
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise ValueError(f"line {n}: tab used for indentation (YAML requires spaces)")
        lines.append(raw.rstrip())
    pos = 0

    def indent_of(line: str) -> int:
        return len(line) - len(line.lstrip(" "))

    def scalar(tok: str):
        tok = tok.strip()
        if not tok:
            return None
        if tok[0] in "\"'" and len(tok) > 1 and tok[-1] == tok[0]:
            return tok[1:-1]
        if tok.startswith(_BLOCK_SENTINEL):
            return blocks.get(tok, "")
        if tok.startswith("[") and tok.endswith("]"):
            inner = tok[1:-1].strip()
            return [scalar(p) for p in _split_flow(inner)] if inner else []
        low = tok.lower()
        if low in {"true", "yes"}:
            return True
        if low in {"false", "no"}:
            return False
        if low in {"null", "~", ""}:
            return None
        try:
            return int(tok)
        except ValueError:
            pass
        try:
            return float(tok)
        except ValueError:
            pass
        return tok

    def parse_block(level: int):
        nonlocal pos
        if pos >= len(lines):
            return None
        if lines[pos].lstrip().startswith("- "):
            return parse_list(level)
        return parse_map(level)

    def parse_map(level: int) -> dict:
        nonlocal pos
        out: dict = {}
        while pos < len(lines):
            line = lines[pos]
            ind = indent_of(line)
            if ind < level:
                break
            if ind > level:
                raise ValueError(f"unexpected indent at: {line.strip()!r}")
            stripped = line.strip()
            if stripped.startswith("- "):
                break
            if ":" not in stripped:
                raise ValueError(f"expected 'key: value' at: {stripped!r}")
            key, _, rest = stripped.partition(":")
            key = key.strip().strip("\"'")
            rest = rest.strip()
            pos += 1
            if rest:
                out[key] = scalar(rest)
                continue
            if pos < len(lines) and indent_of(lines[pos]) > level:
                out[key] = parse_block(indent_of(lines[pos]))
            elif pos < len(lines) and lines[pos].strip().startswith("- ") \
                    and indent_of(lines[pos]) == level:
                out[key] = parse_list(level)   # list at the key's own indent
            else:
                out[key] = None
        return out

    def parse_list(level: int) -> list:
        nonlocal pos
        out: list = []
        while pos < len(lines):
            line = lines[pos]
            ind = indent_of(line)
            if ind < level or not line.strip().startswith("- "):
                break
            if ind > level:
                raise ValueError(f"unexpected indent at: {line.strip()!r}")
            item = line.strip()[2:].strip()
            pos += 1
            if not item:
                out.append(parse_block(indent_of(lines[pos])) if pos < len(lines) else None)
                continue
            if ":" in item and not item.startswith(("[", "\"", "'")):
                # "- key: value" starts a map whose remaining keys are indented
                # to just past the dash.
                child_indent = ind + 2
                key, _, rest = item.partition(":")
                entry: dict = {}
                rest = rest.strip()
                if rest:
                    entry[key.strip()] = scalar(rest)
                else:
                    if pos < len(lines) and indent_of(lines[pos]) > child_indent:
                        entry[key.strip()] = parse_block(indent_of(lines[pos]))
                    else:
                        entry[key.strip()] = None
                while pos < len(lines) and indent_of(lines[pos]) == child_indent \
                        and not lines[pos].strip().startswith("- "):
                    entry.update(parse_map(child_indent))
                out.append(entry)
            else:
                out.append(scalar(item))
        return out

    result = parse_block(0) if lines else {}
    if pos < len(lines):
        raise ValueError(f"could not parse from: {lines[pos].strip()!r}")
    return result if result is not None else {}


def _split_flow(inner: str) -> list[str]:
    """Split an inline `[a, b, "c, d"]` body on top-level commas."""
    parts, buf, quote = [], "", ""
    for ch in inner:
        if quote:
            buf += ch
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
            buf += ch
        elif ch == ",":
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    return [p.strip() for p in parts if p.strip()]


def _as_list(value) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _num(value) -> float | None:
    """Numbers only. A target of '≤ 15%' has no numeric value, and parsing the
    15 out of it would render a ceiling as two-thirds complete."""
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def parse_linkage(text: str) -> Linkage:
    """`phase/<NNN>-linkage.md` — YAML frontmatter, spec version 1.

    All-or-nothing: a file that half-parses would render a chain missing
    objectives the user committed to, which reads as "nothing is being done
    about that". On any error the returned Linkage carries `error` and no data.
    See $PERRY_HOME/reference/okr-linkage.md."""
    front, _ = split_frontmatter(text)
    if not front.strip():
        return Linkage(error="no YAML frontmatter (expected `---` fenced block at the top)")
    try:
        data = parse_yaml_subset(front)
    except ValueError as exc:
        return Linkage(error=str(exc))
    if not isinstance(data, dict):
        return Linkage(error="frontmatter is not a mapping")
    if "{{" in front:
        return Linkage(error="unfilled template placeholders")

    spec = data.get("linkage")
    if spec != 1:
        return Linkage(error=f"unsupported linkage spec version: {spec!r} (expected 1)")

    link = Linkage(
        spec=1,
        phase=str(data.get("phase") or ""),
        updated=str(data.get("updated") or ""),
        unlinked=[str(t) for t in _as_list(data.get("unlinked"))],
    )
    for obj in _as_list(data.get("objectives")):
        if not isinstance(obj, dict):
            continue
        krs = []
        for kr in _as_list(obj.get("krs")):
            if not isinstance(kr, dict) or not kr.get("id"):
                continue
            krs.append(LinkageKR(
                id=str(kr["id"]),
                title=str(kr.get("title") or ""),
                metric=str(kr.get("metric") or ""),
                target=_num(kr.get("target")),
                current=_num(kr.get("current")),
                due=str(kr.get("due") or ""),
                stretch=bool(kr.get("stretch")),
                tasks=[str(t) for t in _as_list(kr.get("tasks"))],
            ))
        link.objectives.append(LinkageObjective(
            id=str(obj.get("id") or ""), title=str(obj.get("title") or ""), krs=krs))
    for ag in _as_list(data.get("agents")):
        if isinstance(ag, dict) and ag.get("id"):
            link.agents.append(LinkageAgent(
                id=str(ag["id"]), tasks=[str(t) for t in _as_list(ag.get("tasks"))]))
    for pr in _as_list(data.get("projects")):
        if not isinstance(pr, dict) or not pr.get("id"):
            continue
        link.projects.append(LinkageProject(
            project_id=str(pr["id"]),
            serves_kr=str(pr.get("serves") or pr.get("serves_kr") or ""),
            objective=str(pr.get("objective") or ""),
            name=str(pr.get("name") or ""),
            aliases=[str(a) for a in _as_list(pr.get("aliases"))],
            status=str(pr.get("status") or "active").lower(),
        ))
    return link


def _load_ops_counts(root: Path) -> OpsCounts:
    ops = OpsCounts()

    inputs = root / "inputs"
    if inputs.is_dir():
        files = [p for p in inputs.iterdir() if p.is_file() and not p.name.startswith(".")]
        ops.inputs = len(files)
        if files:
            oldest = min(files, key=lambda p: p.stat().st_mtime)
            ops.inputs_oldest = oldest.name
            age = datetime.now() - datetime.fromtimestamp(oldest.stat().st_mtime)
            ops.inputs_oldest_days = age.days

    def index_header(path: Path) -> str:
        if not path.exists():
            return ""
        for line in path.read_text().split("\n"):
            s = line.strip().lstrip(">").strip()
            # The INDEX templates put the counts line right under the H1.
            if s and not s.startswith("#") and re.search(r"\d", s):
                return s
        return ""

    ops.knowledge_index = index_header(root / "knowledge" / "INDEX.md")
    ops.runbook_index = index_header(root / "runbook" / "INDEX.md")
    ops.incidents_index = index_header(root / "incidents" / "INDEX.md")

    return ops



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
    linkage: Linkage = field(default_factory=Linkage)
    ops: OpsCounts = field(default_factory=OpsCounts)
    weekly: list[JournalEntry] = field(default_factory=list)


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
    linkage = Linkage()
    cur_pointer = root / "phase" / "CURRENT"
    if cur_pointer.exists():
        slug = cur_pointer.read_text().strip()
        if slug and slug not in {"(none)", "none", "—"}:
            phase_file = root / "phase" / f"{slug}.md"
            if phase_file.exists():
                phase = parse_phase(slug, phase_file.read_text())
            # Linkage registry is named by phase number: phase/<NNN>-linkage.md
            number = (phase.number if phase else "") or slug.split("-")[0]
            linkage_file = root / "phase" / f"{number}-linkage.md"
            if linkage_file.exists():
                linkage = parse_linkage(linkage_file.read_text())

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
        linkage=linkage,
        ops=_load_ops_counts(root),
        weekly=walk_weekly(root),
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
        print(f"  · day: {s.phase.day if s.phase.day is not None else '—'}")
        print(f"  · objectives: {len(s.phase.objectives)} · KRs: {len(s.phase.krs)}")
        print(f"  · scope triggers: {len(s.phase.scope_triggers)}")
        print(f"  · cost-ceiling lines: {len(s.phase.cost_ceiling_lines)}")
    print(f"ADRs: {len(s.adrs)} · Evidence: {len(s.evidence)} · Journal: {len(s.journal)}")
    print(f"Design docs: {len(s.design)}")
    for d in s.design:
        print(f"  · {d.id:<10} [{d.status:<10}] refs={d.impl_refs} {d.date or '----------'} {d.title[:50]}")
