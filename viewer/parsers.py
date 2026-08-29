"""Markdown parsers for a Perry project's state files. Read-only — never writes.

The viewer ships inside the Perry skill but renders the *project* it's pointed
at, NOT the skill directory.

Two roots, and they are not always the same directory. `PROJECT_ROOT` is where
`.perry/` is anchored — what $PERRY_PROJECT holds and what `bin/perry-state
--root` takes. `STATE_ROOT` is where the state files live, which
`.perry/config.md § State root` may move into a subdirectory (Perry's own
project does). `resolve_state_root` goes one way and `resolve_project_root`
goes back; every reader here takes whichever of the two it actually needs."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

# ── one normalization for a header cell ───────────────────────────────────
#
# `squash` is the single rule for turning a written header cell into the key
# a column is resolved by: whitespace and markdown decoration off, lowercased.
# It lives in `tables.py` because `bin/perry-task`, `bin/perry-goals` and
# `bin/perry-lint` already import it from there; this reader used to spell the
# same idea `.strip().lower()` at eleven sites, and the two rules were not the
# same rule.
#
# What that cost (TASK-050): on `| ID | **Risk** | Opened | Status |` the
# writer's `is_risk_header` squashed `**Risk**` to `risk` and said "risk
# table"; this reader lowered it to `**risk**` and said "not a risk table".
# So `risk-add` wrote rows, `perry-state` reported 0 risks, `perry-lint` was
# clean and `risk-migrate` said "already migrated" — four exits, all closed,
# and the user's live risks invisible in every one. The task tables survived
# only because every column there has a positional fallback, which is to say
# they were being read by position, not by name.
#
# `tests/test_risks.py::TestOneNormalizationForAHeaderCell` compares the
# reader's predicate against the writer's over a corpus of header forms.
from tables import UnrenderableCell, render_row, split_row, squash  # noqa: E402

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
    """True when `head` opens the section named `canonical`, in any language.

    **Decoration-tolerant**, via the same `squash` the header cells use. It was
    not, and neither was `bin/perry-task § heading_re`, and the two failed
    together on `## **Top risks**`: the reader saw no risks section, the section
    locator could not find it either and so `risk-add` **appended a second
    `## Top risks`** at exit 0 — while the id minter, which reads the rows by a
    third rule, could see them and minted the next id in sequence. Three
    implementations of "where is this section", three different answers in one
    call, and every risk already recorded became invisible to every tool.

    `squash` strips `*`, backticks and whitespace runs without touching internal
    spaces, so `## Top risks (one-line)` and `## P2 (低优先 carry)` still match
    by prefix — which is what the `(?!\w)` in `heading_re` was protecting and
    is preserved here.
    """
    h = squash(head)
    return any(h.startswith(squash(a)) for a in alias("headings", canonical))


@lru_cache(maxsize=1)
def _column_index() -> dict[str, tuple[str, ...]]:
    """Squashed column spelling -> every squashed spelling of the same column.

    Keyed by alias as well as by canonical name so a lookup succeeds whichever
    spelling the caller happens to hold. Squashed with the same `squash` the
    header cells are squashed with, or the two sides of the lookup would be
    normalized by different rules — which is the defect this index exists to
    prevent one level up."""
    idx: dict[str, tuple[str, ...]] = {}
    for canonical, per_lang in (_i18n().get("columns") or {}).items():
        spellings = [canonical, *[s for v in per_lang.values() for s in v]]
        lowered = tuple(dict.fromkeys(squash(s) for s in spellings))
        for s in lowered:
            idx[s] = lowered
    return idx


def _column_keys(canonical: str) -> tuple[str, ...]:
    """Squashed header keys that satisfy `canonical`, in any language."""
    key = squash(canonical)
    return _column_index().get(key, (key,))


# ── the risks register: ONE rule, every caller ────────────────────────────
#
# **TASK-040.** Four implementations of "what is a risk row" is what this row
# died of once (`bin/perry-task § is_risk_header` against this file's
# `_has_risk_header`, and this file's own two bullet scanners against
# `bin/perry-task § _RISK_BULLET`). They were unified pairwise and stayed four
# functions, which is a state that holds only while nobody edits one of them.
# The four questions live here now, in the module every reader of a Perry
# document already imports, and the callers ask rather than answer:
#
#   `viewer/parsers.py`   `_has_risk_header`, `_risk_bullets`, `_parse_risk_table`
#   `bin/perry-task`      `is_risk_header`, `risk_bullets`, `cmd_risk_clear`
#   `bin/perry_store.py`  the register's record shape and its renderer
#   `bin/perry-lint`      `looks_like_perry_record`, the drift report
#
# This file is the bottom of the import graph — it imports `tables` and the
# standard library and nothing else — so a rule placed here is reachable from
# `bin/` and from `viewer/` without either one growing a dependency on the
# other. That is why it is here and not in `bin/perry_store.py`, which imports
# this direction already.

#: The register's columns, in the order `perry-task risk-migrate` writes them.
#: `ID` and `Opened` are stamped by the tool, `Status` is a two-move state
#: machine written as prose, and `Risk` is the human's sentence — never parsed,
#: never enum-checked, never rewritten.
RISK_COLUMNS = ["ID", "Risk", "Opened", "Status"]


def is_risk_register_header(header: list[str]) -> bool:
    """Whether this table header declares the risk-statement column.

    `Risk` is the column that identifies the register: it is the cell that
    holds the sentence, so a table under `## Top risks` without one is a legend
    or a severity key, not the register. Resolved by NAME through the schema
    glossary (`schema/README.md § Columns resolve by name`), so `| 编号 | 风险 |`
    counts, and by `squash`, so `| ID | **Risk** |` counts.

    On `| ID | **Risk** | Opened | Status |` the writer's copy of this squashed
    to `risk` and said yes while the reader's lowered to `**risk**` and said
    no — `risk-add` wrote rows, `perry-state` reported 0 risks, `perry-lint`
    was clean and `risk-migrate` said "already migrated". Four exits, all
    closed, and the user's live risks invisible in every one. There is one
    predicate now because that defect is only reachable while there are two.
    """
    return bool(set(_column_keys("Risk")) & {squash(c) for c in header})


#: What counts as a risk bullet on a section that has not migrated, and what
#: counts as a placeholder standing in for none. `BOARD_TEMPLATE.md` ships
#: `- (no active risks)` and several fixtures carry `- none`; reading those as
#: risks returned `id='(no'` — a handle split out of prose at the space.
_RE_RISK_BULLET = re.compile(r"^(?:-|\d+\.)\s+(.*)$")
_RE_RISK_PLACEHOLDER = re.compile(
    r"^\(?\s*(?:no active risks?|none|n/a|na|tbd|—|-|–|无|暂无)\s*\)?[.。]?$", re.I)


def risk_bullet_text(line: str) -> str:
    """The risk a bullet line states, or `""` when it states none.

    One rule for both the reader and the writer. They disagreed twice: this
    file matched `- ` only while `bin/perry-task` matched `- ` and `1. `, so a
    numbered register read as zero risks on one side and nine on the other;
    and only the writer knew about placeholders, so the template's own
    `- (no active risks)` came back from the reader as a risk.
    """
    m = _RE_RISK_BULLET.match(line.strip())
    if not m:
        return ""
    text = m.group(1).strip()
    if not text or _RE_RISK_PLACEHOLDER.match(text):
        return ""
    return text


#: A `Status` cell that means "this risk is no longer live". Matched as a
#: PREFIX on the cleaned cell and never as an enum: `perry-task risk-clear`
#: writes `cleared <date> — <reason>`, but the column is free text on any board
#: a human has touched, and `## Top risks` is a section three real projects
#: write by hand today. Imposing an enum on a prose column is the mistake this
#: repo made once already and reverted.
_RE_CLEARED = re.compile(
    r"^(?:cleared|resolved|closed|retired|mitigated|已解除|已关闭|已缓解)\b", re.I)
_RE_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def undecorate_cell(cell: str) -> str:
    """A cell with the decoration a human adds removed, text otherwise kept."""
    return (cell or "").replace("~", "").replace("*", "").replace("`", "").strip()


def status_is_cleared(status_cell: str) -> bool:
    """Whether a `Status` cell says the risk is over.

    `cmd_risk_clear` had its own `^(?:cleared|resolved|closed)\\b` — three of
    the eight words this knows — so a risk a human retired as `mitigated` could
    be cleared twice, and the second clear overwrote the first one's date and
    reason.
    """
    return bool(_RE_CLEARED.match(undecorate_cell(status_cell)))


def status_cleared_date(status_cell: str) -> str:
    """The date a `Status` cell says the risk was cleared on, or `""`.

    **`""` is not today and it is not a zero.** A risk retired with no date
    recorded has no cleared date, and inventing one would assert a fact about
    a project's history that nothing in its files supports — the same defect
    as a `current: 0` default that reads as a drive-to-zero already met.
    """
    if not status_is_cleared(status_cell):
        return ""
    m = _RE_ISO_DATE.search(undecorate_cell(status_cell))
    return m.group(0) if m else ""


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


def resolve_project_root(state_root: Path) -> Path:
    """The inverse of `resolve_state_root`: the project root a state root sits in.

    **THE ANCHOR IS THE INVERSE, AND IT IS ALREADY STORED.** `resolve_state_root`
    above records the rule that makes an inverse computable at all: `.perry/`
    never moves, because it holds the pointer and so cannot sit behind it. The
    project root is therefore the nearest ancestor of the state root whose
    `.perry/` pointer resolves BACK to this state root — an exact answer, not a
    bounded guess, and one that needs no new field anywhere.

    The round trip is the whole point. `.perry/` alone is not enough: a project
    whose state IS its root, checked out underneath an unrelated Perry project,
    would otherwise report the outer project's root and send every `.perry/`
    read outside itself. A directory that holds the anchor is a project root by
    definition and answers for itself before any walk starts.

    TASK-159. Three readers each held a different answer to "what is a project
    root": `_resolve_project_root` below returned the directory holding
    `BOARD.md` — the STATE root — while `bin/perry-viewer` exports
    `$PERRY_PROJECT` as the project root and `bin/perry-state --root` expects
    the project root. On Perry's own layout (`.perry/config.md § State root:
    perry`) those are different directories, so **the viewer rendered an empty
    snapshot when pointed where its own launcher points it.** Both directions
    now come out of this one pair of functions, so there is one answer rather
    than three, and `walk_design`'s bounded walk up four levels — written
    because "there is no stored inverse of `resolve_state_root`" — is handed the
    exact root instead.

    A directory with no `.perry/` above it was never adopted: its state root is
    its project root, and it comes back unchanged. That is every fixture, and
    every project whose state sits at its root."""
    root = Path(state_root).expanduser().resolve()
    if (root / ".perry").is_dir():
        return root
    for d in root.parents:
        if (d / ".perry").is_dir() and Path(resolve_state_root(d)).resolve() == root:
            return d
    return root


def _resolve_project_root() -> Path:
    """The PROJECT root — where `.perry/` is anchored — never the state root.

    `STATE_ROOT` below is the state root, and on a project with `State root:
    <subdir>` the two are different directories. Everything this module reads
    state out of takes `STATE_ROOT`; everything that reads `.perry/`, or hands a
    root to a `bin/` tool, takes `PROJECT_ROOT`.

    `$PERRY_PROJECT` is taken verbatim, exactly as `bin/perry-state §
    resolve_root` takes it — a launcher's `--root` and the env var must mean the
    same directory to both readers or they are back to disagreeing, which is the
    defect this function used to be half of.

    The walk is `perry-state § resolve_root`'s walk, predicate for predicate:
    `.perry/config.md` OR `BOARD.md` OR `OKR.md`, first ancestor wins. It reads
    `.perry/config.md` as well as the state files so that standing in a project
    root whose state is a subdirectory resolves to that project root rather than
    falling through to the CWD — the second half of the same defect.
    `tests/test_project_root.py` asserts the two walks against each other rather
    than trusting this comment."""
    env = os.environ.get("PERRY_PROJECT")
    if env:
        return Path(env).expanduser().resolve()
    cur = Path.cwd().resolve()
    for d in [cur, *cur.parents]:
        if ((d / ".perry" / "config.md").exists()
                or (d / "BOARD.md").exists() or (d / "OKR.md").exists()):
            return d
    return cur  # fall back to CWD; load_snapshot will just find nothing


#: Where `.perry/` is anchored. What `bin/perry-viewer` exports as
#: `$PERRY_PROJECT` and what `bin/perry-state --root` takes.
PROJECT_ROOT = _resolve_project_root()

#: Where the state files live — `BOARD.md`, `OKR.md`, `phase/`, `evidence/`,
#: `design/`. The same directory as `PROJECT_ROOT` on every project that has
#: not moved its state, which is every project but Perry's own.
STATE_ROOT = resolve_state_root(PROJECT_ROOT)


# ── the conformance declaration (ADR-004) ─────────────────────────────────
#
# `.perry/conformance.md` records, per state file, that **the user declared**
# this file to match Perry's shape at a given shape version. It is only ever
# half the fact: the other half is whether the file still matches, and that is
# computed live by `bin/perry-conform` from `bin/perry-lint`'s schema
# validation. Storing a verdict would make the file a cache that goes wrong;
# storing a decision makes it a record that cannot.
#
# The reader lives here, beside `resolve_state_root`, for the same reason that
# one does: `bin/perry-lint`, `bin/perry-conform` and any front-end must read
# the declaration identically, and a second parser is how they stop agreeing.

CONFORMANCE_FILE = ".perry/conformance.md"

_CONFORMANCE_ROW = re.compile(r"^\s*\|(?!\s*-)(.+)\|\s*$")

#: A markdown code fence — ``` or ~~~, three or more, any indent, any info
#: string. `read_conformance` tracked none, so a row written INSIDE a fenced
#: block — an example in prose, or a row someone hid there — read as a real
#: declaration (TASK-241). It cannot be caught by any property of the row
#: itself: a fenced row is byte-for-byte identical to a genuine one, and what
#: makes it not a declaration is where it sits, not how it is written.
#:
#: Three groups, because the *first* version of this guard had none and was a
#: boolean toggle flipped by any line that looked like a fence. That is not
#: markdown's rule, and it was defeated by the ordinary way a document shows a
#: fenced block — a NESTED fence. `~~~` then ``` ``` ``` closed the toggle on
#: the inner line, and the row under it was a live declaration again, laundered
#: into a canonical row by the next legitimate `declare`, exactly as before the
#: guard existed. Measured on four nestings (TASK-241 round 2).
_FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")


@dataclass
class Declaration:
    """One row of `.perry/conformance.md`."""
    path: str            # as the schema declares it, relative to that spec's anchor
    shape_version: int
    declared: str        # ISO date the user declared it
    route: str           # "declare" (already conformant) or "migrate" (TASK-044)
    line: int


@dataclass
class ConformanceRecord:
    path: Path
    exists: bool
    declarations: dict[str, Declaration] = field(default_factory=dict)
    #: Rows present in the file that this reader could not turn into a
    #: declaration. Reported, never guessed at — a mangled row must not read as
    #: "declared" and must not read as "absent" either.
    unreadable: list[tuple[int, str]] = field(default_factory=list)


def read_conformance(project_root: Path) -> ConformanceRecord:
    """The declarations recorded for this project. Never writes, never infers.

    A project with no file has no declarations — which is every project that
    existed before ADR-004, including Perry's own."""
    path = Path(project_root) / CONFORMANCE_FILE
    rec = ConformanceRecord(path=path, exists=path.exists())
    if not rec.exists:
        return rec
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return rec
    # ── which lines are inside a code fence ───────────────────────────────
    #
    # `fence` is the OPEN fence's `(delimiter character, run length)`, not a
    # boolean. A boolean was the first version and it was wrong: any
    # fence-looking line flipped it, so a fence nested inside a longer or
    # differently-charactered one — ``` inside ~~~, ``` inside ````, a
    # ```` ```x ```` line inside ``` — turned tracking OFF and handed the row
    # below it back to the parser as a real declaration.
    #
    # **Opening is liberal, closing is strict, and each direction is chosen
    # fail-closed.** Any run of three or more backticks or tildes at any indent
    # OPENS — including the two shapes CommonMark says are not openers (a
    # backtick fence whose info string contains a backtick; a fence indented
    # four or more spaces, which is an indented code block) — because refusing
    # a row we are unsure about costs a loud `unreadable`, while parsing one
    # costs a false `conformant` on the file that gates every write. A fence
    # CLOSES only on CommonMark's terms (§ 4.5): the same delimiter character,
    # a run at least as long as the opener's, indented at most three, and
    # nothing after it but whitespace. Every line that is not that is content.
    fence: tuple[str, int] | None = None
    for i, line in enumerate(text.split("\n"), start=1):
        f = _FENCE.match(line)
        if f:
            run, rest = f.group(2), f.group(3)
            if fence is None:
                fence = (run[0], len(run))
            elif (run[0] == fence[0] and len(run) >= fence[1]
                  and len(f.group(1).expandtabs(4)) < 4 and not rest.strip()):
                fence = None
            continue
        m = _CONFORMANCE_ROW.match(line)
        if not m:
            continue
        if fence is not None:
            # Reported, not skipped. A row nobody can see the effect of is how
            # this class stayed live: `ConformanceRecord.unreadable` exists so
            # a row that is neither `declared` nor `absent` says so out loud,
            # and `perry-conform status` prints it.
            rec.unreadable.append((i, line.strip()))
            continue
        # `split_row` — the SIXTH implementation of this, found by a V4
        # reviewer after five were unified. It reads a row out of a regex
        # group rather than off a line, which is why every sweep looking for
        # `strip("|").split("|")` at the start of a line walked past it.
        cells = [c.strip("` ") for c in split_row("|" + m.group(1) + "|")]
        if len(cells) < 4:
            continue
        rel, ver, declared, route = cells[0], cells[1], cells[2], cells[3]
        # `squash`, not `.lower()`. `strip("` ")` removes backticks and spaces
        # and leaves ASTERISKS, so a bolded `| **File** |` header row was read
        # as a DECLARATION whose version cell is not a number — and
        # `perry-conform status` reported `unreadable row` against a correct
        # file while `perry-lint` still said clean.
        #
        # The fifth live copy of this rule, in the file the first pass claimed
        # to have unified, found by a reviewer running an AST sweep over all
        # 111 lowercasing sites rather than by grepping for the ones it knew.
        if squash(rel) in ("file", "path") or not rel:
            continue           # the header row
        if not re.fullmatch(r"\d+", ver or ""):
            rec.unreadable.append((i, line.strip()))
            continue
        # ── the round trip: a row is a declaration only if it is ALREADY the
        # row `bin/perry-conform:render` would write for what we just parsed.
        #
        # `strip("` ")` above removes backticks, `_CONFORMANCE_ROW` allows
        # leading whitespace, and this reader tracks no code fences — so a
        # path cell in BACKTICKS, an INDENTED row, and a row inside a ``` ```
        # ``` FENCE each parsed to the same plain key as a row a person had
        # declared on purpose. Measured (TASK-241, found by the TASK-226 V4
        # reviewer): one hand-written backticked row flipped a real file from
        # `undeclared` to `conformant`, and because `declare` rewrites the
        # whole file from the parsed declarations, the next legitimate
        # `perry-conform declare` LAUNDERED it into a plain canonical row that
        # nothing downstream could tell from a real one. This is the file that
        # gates every write under ADR-004's enforce gate.
        #
        # This is ONE PROPERTY, not a list of decorations, and that is the
        # whole reason it is written this way: `render(parse(row)) == row`
        # closes the class, including the shapes nobody has thought of yet.
        # A list of known decorations closes the three that have been found
        # and is defeated by the fourth — TASK-050 spent eight V4 rounds
        # learning that on this same file.
        #
        # It is not a new normalization rule either: the canonical form is
        # `render_row`, the same writer the record's only writer uses, so
        # "what a declaration looks like" still has exactly one definition.
        #
        # ASTERISKS survive, deliberately: `strip("` ")` never removed them,
        # so `| **path** |` round-trips to itself and still reads as a
        # declaration under the key `**path**` — inert, because no key from
        # `state_files()` carries asterisks, and unchanged by this guard. A
        # bolded `| **File** |` HEADER is squashed to `file` above and skipped
        # before we get here; that is TASK-050's rule and it still stands.
        try:
            canonical = render_row([rel, str(int(ver)), declared,
                                    route or "declare"])
        except UnrenderableCell:
            # A cell that cannot be written back at all — a `\n` smuggled in,
            # say. Refused for the same reason: unreadable, never guessed at.
            canonical = None
        if canonical != line:
            rec.unreadable.append((i, line.strip()))
            continue
        rec.declarations[rel] = Declaration(
            path=rel, shape_version=int(ver), declared=declared,
            route=route or "declare", line=i)
    return rec


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
    # **The two columns the non-`project` modes are defined by.** They were
    # absent, so `bin/perry-state` — which reads the board through this class —
    # could not see a row's track or stage at all, while `perry-task/list`
    # parses both with its own row reader. Two readers of one board, and the
    # one the standup and `triage` use dropped exactly the columns
    # `modes/pipeline.md` and `modes/queue.md` measure. That is why the mode's
    # own triage step ("stages at their WIP limit") could only be done by
    # eyeballing a board the procedure forbids eyeballing.
    track: str = ""
    stage: str = ""
    # **The queue's clock.** `modes/queue.md § The mode contract` calls
    # `Arrived` the arrival date "carried from intake and never lost", and its
    # triage step 2 is `today − Arrived` against the track's SLA. The column was
    # absent here for the same reason `track` and `stage` were: `perry-task`
    # parses it with its own row reader, `bin/perry-state` reads the board
    # through this class, and so the one payload triage reads could not see the
    # number the mode is measured by. TASK-135 made the cell trustworthy —
    # carried on a queue→queue move, cleared on the way off — and left it with
    # no reader.
    arrived: str = ""
    # The `Id` from `OKR.md § Commitments` this row discharges. Read for one
    # reason: the queue breach step names each late row "with its age and the
    # `Commitment` it breaches" (`modes/queue.md § Triage in this mode`), and a
    # breach list that cannot say what promise is being broken is half the
    # finding.
    commitment: str = ""
    # `Role` (DESIGN-006 phase E). Present so the roster can answer "what does
    # each role hold" by JOINING two files it already reads, rather than by a
    # third registry storing a fact both of them carry.
    role: str = ""


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
    # ── the table form (TASK-040) ──────────────────────────────────────────
    # `source` says how this row was read, because the two forms carry
    # genuinely different amounts of truth and a consumer is entitled to know
    # which it got. A `table` row's `id` was minted by `perry-task risk-add`;
    # a `bullets` row's `id` is the first word of a sentence and means nothing
    # — reporting them under one key without saying so is how `id: "Perry"`
    # reached a payload in the first place.
    source: str = "bullets"     # 'table' | 'bullets'
    opened: str = ""            # YYYY-MM-DD, stamped by `perry-task risk-add`
    status: str = ""            # the raw `Status` cell; "" on a bullet
    cleared_on: str = ""        # YYYY-MM-DD parsed out of a cleared status
    # ── the magnitude a human wrote (TASK-058) ────────────────────────────
    # `severity` above is a STANCE — what we decided to do about the risk —
    # and it is read out of prose words like `TOP RISK` and `ACCEPT`. It is
    # not the H/M/L a person writes at the front of a bullet, and folding the
    # two into one field is why `H · …` and `M · …` on a real board both
    # arrived as `watch`: the letter was consumed as an ID and the stance
    # heuristic, finding no stance word, defaulted.
    #
    # Two axes, because they answer different questions. `severity_text` is
    # the marker verbatim (`H`, `🔴`) so a consumer can render exactly what the
    # project wrote; `severity_rank` normalizes it to `high`/`medium`/`low` so
    # the same consumer can sort. Both are `""` when the line carries no
    # marker, which is most of them.
    severity_text: str = ""
    severity_rank: str = ""     # 'high' | 'medium' | 'low' | ''

    @property
    def resolved(self) -> bool:
        """Whether this risk is no longer live.

        One predicate, so every consumer agrees. Before TASK-040 the only test
        was `severity == "resolved"`, which the bullet parser set from a
        `~~strikethrough~~` — real, but invisible to anything that had not read
        that function. A struck-through risk on Perry's own board was counted
        as live for exactly that reason.
        """
        return self.severity == "resolved"


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
    #: `## Intake` rows. Absent from this class until 2026-08-18, so
    #: `perry-state` could not see the section at all.
    intake: list[dict] = field(default_factory=list)
    cadence: list[Task] = field(default_factory=list)
    # Task tables under project-defined headings. The writer accepts these via
    # `--group`; keeping them separate avoids inventing a P0/P1/P2 priority.
    task_groups: list[tuple[str, list[Task]]] = field(default_factory=list)
    backbone_groups: list[tuple[str, list[Task]]] = field(default_factory=list)
    user_input_queue: list[UserInput] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)

    @property
    def all_tasks(self) -> list[Task]:
        out = list(self.p0) + list(self.p1) + list(self.p2) + list(self.cadence)
        for _, tasks in self.task_groups:
            out.extend(tasks)
        return out


@dataclass
class KR:
    id: str              # e.g. "KR-O1.1" (OKR.md) or "P002-O1-KR2" (phase file)
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
    #: `"1"` for `## Objective 1 — …` in a phase document, `""` everywhere
    #: else. Recorded rather than re-derived from position because
    #: `phase_key_results_by_objective` attaches a register's KRs by the
    #: objective number their **id** carries (`P003-O2-KR1` → `O2`), and
    #: matching by position would put a KR under the wrong heading the moment
    #: a document's objectives are not `1, 2, 3 …` in order.
    number: str = ""
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
    #: The overall KR this phase KR serves — the `Linked overall KR` column of
    #: the KR table the phase document used to carry. TASK-157 moved it here
    #: rather than dropping it with the table: it is the only one of that
    #: table's four columns the register had no field for, and DESIGN-013 § 5.1
    #: puts a schema'd fact in exactly one store rather than in a document.
    #: **Additive and optional**, so `linkage: 1` is unchanged: a register
    #: written before this field existed carries `""`, which is what an empty
    #: `Linked overall KR` cell always meant.
    linked: str = ""
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
#
# **A task row is read out of `perry/tasks.jsonl`, not out of a markdown
# table** (ADR-007 decision 4, TASK-094). `BOARD.md` is a projection of that
# store — `bin/perry_store.py § render` reproduces it byte-for-byte — so
# resolving a header cell and splitting a row to recover the fifteen task
# columns is asking a rendered document for a value the store already holds,
# and it is the shape every "two readers of one board" defect in this
# repository has taken.
#
# The markdown reader below survives for exactly one caller and is named for
# it: a project with NO store has not been adopted, its markdown IS its state,
# and parsing it is the job (`bin/perry-migrate`, `tests/fixtures/
# sample-project`). That is the one place ADR-007 decision 4 keeps.
#
# What the store does not hold stays board-backed and is enumerated rather
# than assumed: `## Cadence`, `## Intake`, `## User Input Queue` and
# `## Top risks` have no store of their own yet (DESIGN-007's ordered plan;
# TASK-090 § 5 bounded them explicitly), and neither does the `### ` sub-group
# a Backbone row sits under.

#: `<state root>/tasks.jsonl`. Named here because two readers of one path is
#: the same defect one level down; `bin/perry_store.py § store_path` builds it
#: the same way and this module may not import from `bin/`.
TASK_STORE = "tasks.jsonl"

#: The two statuses that take a row off the board. Spelled the same way in
#: `bin/perry_store.py § TERMINAL_STATUSES`; this module may not import from
#: `bin/`, and `tests/test_row_integrity.py` asserts the two agree rather than
#: leaving a second copy to drift.
_TERMINAL_STATUSES = frozenset(("done", "dropped"))


def load_task_store(state_root: Path) -> list[dict] | None:
    """Every record of `<state root>/tasks.jsonl`, or `None` when there is none.

    `None` is not "no tasks" — it is **"this project has not been adopted"**,
    and it is the only condition under which anything in this module reads a
    task out of a markdown table. An empty list is a real, adopted, empty
    board and reads zero tasks without touching `BOARD.md`.

    A malformed store returns `None` rather than raising: this reader is
    read-only and feeds a viewer and a standup, and `bin/perry-tasks` is the
    tool that reports a store it cannot parse. Falling back to the projection
    would be the recovery `bin/perry_store.py § validate_records` refuses, so
    the caller gets "unadopted" and the tool that can say why says why.
    """
    p = Path(state_root) / TASK_STORE
    if not p.exists():
        return None
    try:
        return [json.loads(line) for line
                in p.read_text(encoding="utf-8").split("\n") if line.strip()]
    except (OSError, ValueError):
        return None


def _task_from_record(rec: dict, priority: str) -> Task:
    """One store record → the `Task` the viewer and `bin/perry-state` consume.

    `status_note` is empty by construction. It exists because a hand-written
    cell could read `review (dev done)`; a stored `status` is one of the six
    enum values or the write was refused (`bin/perry-task §
    refuse_unstorable_status`), so there is no parenthetical left to split off
    and inventing one would be the reader asking prose a question again.

    `priority` comes from the SECTION, exactly as the markdown reader derived
    it, and not from the record's own `priority` field. The two disagree on a
    real board — Perry's own `## Done this period` holds rows whose stored
    priority is `P1` — and this function's job is to be the same reader, not a
    better one.
    """
    def s(field: str) -> str:
        v = rec.get(field)
        return "" if v is None else str(v)

    return Task(
        id=s("id"), title=s("title"), owner=s("owner"), status=s("status"),
        next_action=s("next_action"), evidence=s("evidence"),
        priority=priority, status_note="", verification=s("verification"),
        track=s("track"), stage=s("stage"), arrived=s("arrived"),
        commitment=s("commitment"), role=s("role"))


def _records_by_group(records: list[dict]) -> list[tuple[str, list[dict]]]:
    """`(section heading, rows)` in the order the store files them.

    Rows are ordered by `order`, the field `bin/perry_store.py § STORED`
    carries so that authored row order is *recorded* rather than re-derived —
    which is the whole reason this reader can stop looking at the lines. A
    record written before the field existed sorts last and keeps its file
    order, because `sorted` is stable and a missing `order` is not a claim
    about position.
    """
    groups: dict[str, list[dict]] = {}
    for rec in records:
        if str(rec.get("status") or "") in _TERMINAL_STATUSES:
            # **Which rows have a line is the store's own answer**, and this is
            # it: `bin/perry_store.py § plan` computes exactly this set as
            # `wanted` when it decides which records the projection owes a
            # line. A closed row keeps its `group` in the store as history —
            # 22 of Perry's own P1/P2 records are `done` or `dropped` and none
            # of them is on the board — so reading the group without this rule
            # doubles the board. Measured: 24 rows before, 47 after.
            continue
        groups.setdefault(str(rec.get("group") or ""), []).append(rec)
    out = []
    for head, rows in groups.items():
        if not head:
            # No section: no line on the board and nothing to project it into.
            # `bin/perry-tasks § plan` reports these as `rows_not_on_board`;
            # a reader that invented a section for them would be inventing
            # layout the store deliberately does not hold.
            continue
        out.append((head, sorted(
            rows, key=lambda r: r["order"]
            if isinstance(r.get("order"), int)
            and not isinstance(r.get("order"), bool) else 1 << 30)))
    return out


def _board_tasks_from_store(state: BoardState, records: list[dict]) -> None:
    """Fill `state`'s task lists from the store. Reads no markdown at all.

    The section-to-list mapping is the markdown reader's, character for
    character: `P0`/`P1`/`P2` are priority enum values and are matched by
    prefix, `Backbone` names the spine, and every other heading is a
    project-defined group that gets no invented priority.
    """
    for head, rows in _records_by_group(records):
        if head.startswith("P0"):
            state.p0 = [_task_from_record(r, "P0") for r in rows]
        elif head.startswith("P1"):
            state.p1 = [_task_from_record(r, "P1") for r in rows]
        elif head.startswith("P2"):
            state.p2 = [_task_from_record(r, "P2") for r in rows]
        elif head.startswith("Backbone"):
            tasks = [_task_from_record(r, "Backbone") for r in rows]
            state.task_groups.append((head, tasks))
            # The `### ` sub-group is LAYOUT and the store has no field for
            # it, so a store-backed spine is one group per `##` heading. Said
            # here rather than silently flattened: it is the one shape this
            # cutover cannot reproduce, and the entity store that would fix it
            # is DESIGN-007's, not this row's.
            state.backbone_groups.append((head, tasks))
        else:
            state.task_groups.append(
                (head, [_task_from_record(r, "") for r in rows]))


def parse_board(text: str, *, tasks: list[dict] | None = None) -> BoardState:
    """`BOARD.md` → the registers it carries.

    `tasks` is the task store's records. **When it is given, no task row is
    read out of `text`** — the fifteen task columns come from the store and
    this function reads only the registers the store does not hold. When it is
    `None` the project has no store and every register is parsed, which is
    adoption and is the one caller that still needs a header rule here.
    """
    state = BoardState()
    if tasks is not None:
        _board_tasks_from_store(state, tasks)

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
            if tasks is None:
                state.p0 = _parse_task_table(chunk, "P0")
        elif head.startswith("P1"):
            if tasks is None:
                state.p1 = _parse_task_table(chunk, "P1")
        elif head.startswith("P2"):
            if tasks is None:
                state.p2 = _parse_task_table(chunk, "P2")
        elif heading_is(head, "Cadence"):
            state.cadence_items = _parse_cadence(chunk)
            state.cadence = [_cadence_as_task(c) for c in state.cadence_items]
        elif heading_is(head, "User Input Queue"):
            state.user_input_queue = _parse_user_input(chunk)
        elif heading_is(head, "Top risks"):
            state.risks = _parse_risks(chunk)
        elif heading_is(head, "Intake"):
            # **`## Intake` matched nothing here**, so `perry-state` carried no
            # intake block at all — while `perry-task/list` parses it. The
            # correlation `work/reference/subcommands.md § triage` asks for
            # (board over its cap *because* intake is undrained) was therefore
            # not computable from the payload the standup reads, on the one
            # mode whose whole shape is arrival.
            state.intake = _parse_intake(chunk)
        elif head.startswith("Backbone"):
            if tasks is None:
                backbone_chunk = chunk
                rows = _parse_task_table(chunk, "Backbone",
                                         task_headers_only=True)
                if rows:
                    state.task_groups.append((head, rows))
        elif tasks is None:
            rows = _parse_task_table(chunk, "", task_headers_only=True)
            if rows:
                state.task_groups.append((head, rows))

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


def _parse_task_table(section: str, priority: str,
                      *, task_headers_only: bool = False) -> list[Task]:
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
            header = ([squash(c) for c in split_row(prev)]
                      if prev.strip().startswith("|") else [])
            # Project-defined groups may contain reference tables beside work.
            # The writer treats only tables with resolvable ID + Title columns
            # as task tables, so the state reader must apply the gate per table.
            in_table = (not task_headers_only or
                        (any(h in _column_keys("ID") for h in header) and
                         any(h in _column_keys("Title") for h in header)))
            idx = {}
            # `Track` and `Stage` were absent from this list, so the two
            # columns the non-`project` modes are DEFINED by resolved to -1 and
            # every row read them as empty — while `perry-task/list`, with its
            # own row reader, parsed both. The mode's own triage step could not
            # run off this payload as a result.
            for name in ("ID", "Title", "Owner", "Status", "Next action",
                         "Evidence", "Verification", "Track", "Stage",
                         "Arrived", "Commitment", "Role"):
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
        cells = split_row(line)
        if len(cells) < 4:
            continue

        def cell(name: str, fallback: int) -> str:
            # Fall back to the canonical position when a header cell is absent
            # or unrecognized, so a board whose headers this build does not know
            # keeps parsing exactly as it did before.
            i = idx.get(name, fallback)
            return cells[i] if 0 <= i < len(cells) else ""

        tid = cell("ID", 0)
        if not tid or squash(tid) in _column_keys("ID"):
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
                track=cell("Track", -1),
                stage=cell("Stage", -1),
                arrived=cell("Arrived", -1),
                commitment=cell("Commitment", -1),
                role=cell("Role", -1),
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
_ISO_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")

# Where the cell stops being a due date and starts being an annotation. Every
# live register writes its note about the LAST run after one of these, and that
# note routinely contains dates — a completion date, or a dated evidence
# filename. Reading past this is how `n/a （见 evidence/2026-08/2026-08-03-…）`
# came back as "14 days overdue".
_ANNOTATION = re.compile(r"->|→|[(（\[【<;；\n]")

# A leading token that says, in the register's own words, that there is no date
# here. Not an error and not a guess — the same set `parse_frequency` treats as
# deliberately aperiodic, plus the em-dash spellings of an empty cell.
_NO_DATE = _APERIODIC | {"—", "–", "-", "tbd", "无", "none", "待定", "?", "??"}


# ── the intake register: ONE rule, every caller ───────────────────────────
#
# **TASK-196, and it is TASK-040's lesson arriving a second time.** "Is this
# intake row discharged?" had FOUR implementations when the store was written,
# and they disagreed in both directions:
#
#   `viewer/parsers.py § _parse_intake`   `squash(outcome) not in _NO_DATE`
#   `bin/perry-task § check_intake_undischarged`   `not in INTAKE_UNSET`
#   `bin/perry-task § cmd_intake_sweep`            a second copy of the same
#   `bin/perry-task § cmd_list` (twice)            a third and a fourth
#
# `_NO_DATE` holds `无`, `待定`, `?` and the aperiodic spellings and `INTAKE_
# UNSET` does not, so an outcome cell reading `待定` counted as DISCHARGED for
# the writer's "already has an outcome" refusal and as WAITING for the
# reader's queue-depth count. `INTAKE_UNSET` holds `n/a` and `pending` and
# `_NO_DATE` does not, so those two went the other way. Every one of those
# cells is one a human types.
#
# The store must not be the fifth. The rule is here, in the module every
# reader of a Perry document already imports, for the reason the risks block
# above gives: this file is the bottom of the import graph.

#: The register's columns, in the order `bin/perry-task § cmd_intake` writes
#: them. There is no `ID` column and there never was — an intake row is
#: addressed by POSITION, which is what `perry-task resolve-intake <n>` takes
#: and what `perry-task/list § intake.rows[].n` publishes.
INTAKE_COLUMNS = ["Arrived", "Request", "Outcome"]

#: Every spelling either implementation treated as "no outcome recorded", so
#: unifying them cannot turn a row that any of the four called WAITING into a
#: discharged one. Squashed, because the cell is one a human decorates.
#:
#: **`_APERIODIC` rides along, deliberately.** `ongoing` and `as needed` are
#: cadence vocabulary and read oddly in an `Outcome` cell — but `_parse_intake`
#: has counted them as "still waiting" since it was written, and dropping them
#: here would silently reclassify such a row as discharged and quietly shorten
#: the queue depth an over-cap board is judged by. Narrowing this set is a
#: decision about somebody's board, not a tidy-up.
INTAKE_UNSET_OUTCOME = frozenset(
    {squash(s) for s in (_NO_DATE | {"", "n/a", "na", "pending"})})


def is_intake_register_header(header: list[str]) -> bool:
    """Whether this table header declares the request column.

    `Request` is the column that identifies the register — it holds the
    human's sentence — exactly as `Risk` identifies the risks register one
    block up. Resolved by NAME through the glossary so `| 到达 | 请求 |`
    counts, and by `squash` so `| Arrived | **Request** |` counts.
    """
    return bool(set(_column_keys("Request")) & {squash(c) for c in header})


def intake_is_discharged(outcome: str) -> bool:
    """Whether an `Outcome` cell says this request has left the queue.

    The ONE rule, called by the reader, by all three writers and by the store.
    `discharged` is what triage actually asks — a row whose `Outcome` is empty
    is still waiting, and the count of those is what makes an over-cap board
    mean *"the queue is not being drained"* rather than *"the board is long"*.

    **Not an enum on the cell.** `resolve-intake` writes
    `dropped <date> — <reason>` and `route` writes a task id, but the column is
    free text on any board a human has touched, so the question is asked the
    only way it can be: is this cell one of the spellings that means "nothing
    recorded yet".
    """
    return squash(outcome or "") not in INTAKE_UNSET_OUTCOME



def parse_due(cell: str) -> date | None:
    """A `Next due` cell → the date it is late after, or `None`.

    The cell is prose on a real board and this function is the tolerant half of
    the contract. Three live examples from one project's register:

        n/a （见 `evidence/2026-08/2026-08-03-retro.md`）
        **2026-08-31**（7 月版 ✅ 8/3 补作 → `evidence/2026-08/retro-2026-07.md`）
        **2026-W32 friday-review (8/7)**（W31 版 ✅ 8/3 补作…）

    Only the LEADING segment is read — the text before the first annotation
    opener. The old rule searched the whole cell for `\\d{4}-\\d{2}-\\d{2}` and
    so read the first two rows above as due `2026-08-03` (a path fragment) and
    `2026-01-05` (a note about the last run), reporting both overdue by 14 and
    224 days. `parse_frequency`'s docstring next door states the rule this now
    honours: **a confidently wrong value is worse than an admitted unreadable
    one.** A cell this cannot read returns `None` and lands in
    `cadence.undated`, which is a reported finding, not a silent pass.

    Within that segment the FIRST token that resolves wins, so an ISO week
    written before a bare date is not overruled by it. A week resolves to its
    **Sunday** — a week-scoped ritual is not late on Monday, and taking the
    Monday would report every weekly row as up to six days overdue inside its
    own week. A token that is a path (`evidence/2026-08/x.md`) is skipped
    rather than mined for digits: it cites the last run, never the next one.
    """
    head = _ANNOTATION.split(cell or "", 1)[0]
    for token in head.split():
        t = token.strip("*`_ 　,.，。;；:：、!！").strip()
        if not t:
            continue
        if t.lower() in _NO_DATE:
            # The cell says there is no date. Reading on would find one in the
            # citation that follows and report a ritual that is deliberately
            # aperiodic as overdue.
            return None
        if "/" in t or t.lower().endswith((".md", ".txt", ".json")):
            continue
        w = _ISO_WEEK.match(t)
        if w:
            try:
                return date.fromisocalendar(int(w.group(1)), int(w.group(2)), 7)
            except ValueError:
                return None
        d = _ISO_DATE.match(t)
        if d:
            try:
                return datetime.strptime(d.group(1), "%Y-%m-%d").date()
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
            header = ([squash(c) for c in split_row(prev)]
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
        cells = split_row(line)
        if len(cells) < 4:
            continue

        def cell(name: str, fallback: int = -1) -> str:
            i = idx.get(name, fallback)
            return cells[i] if 0 <= i < len(cells) else ""

        cid = cell("ID", 0)
        if not cid or squash(cid) in _column_keys("ID"):
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


#: The register's columns, in the order `perry-task ask` writes them. `Idle` is
#: NOT among them and never was: `cmd_ask` stamps `Asked`, a date, and the age
#: is computed at read time by `bin/perry-state § idle_days`.
USER_COLUMNS = ["USER-id", "Needed from user", "Blocks", "Asked", "Status"]


def is_user_register_header(header: list[str]) -> bool:
    """Whether this table header declares the question column.

    `Needed from user` is the column that identifies the register — it holds
    the human's sentence — exactly as `Risk` and `Request` identify the two
    registers above. Resolved by NAME through the glossary so
    `| 用户输入编号 | 需要用户提供 |` counts, and by `squash` so
    `| USER-id | **Needed from user** |` counts.

    **Not `USER-id`.** A table under this heading with an id column and no
    question column is a legend or an index, and the sentence is what a row of
    this register is for — the same reading `is_risk_register_header` gives one
    block up, taken here for the same reason rather than by analogy.
    """
    return bool(set(_column_keys("Needed from user"))
                & {squash(c) for c in header})


#: A `Status` cell that means "this question is still on the user". Matched as a
#: PREFIX on the cleaned cell and never as an enum, for the reason
#: `_RE_CLEARED` is: `perry-task ask` writes `pending` and `answer` writes
#: `answered <date>: <text>`, but the column is free text on any board a human
#: has touched.
_ASK_STILL_OPEN = ("pending", "waiting", "open", "—", "-")


def ask_is_answered(status_cell: str) -> bool:
    """Whether a `## User Input Queue` row has had its answer.

    **The rule, in the file both `bin/` and `viewer/` already import.** It was
    written in `bin/perry-state § answered`, whose own docstring records that
    it had already been written twice and that a third copy would decide the
    number the user is told to act on ("2 items waiting on you" on a board
    where both were answered the same day). The store is the fourth caller, and
    a store that re-spelled it would be that defect wearing a record file —
    exactly what `intake_is_discharged` was moved here to prevent one register
    over.

    An empty cell is NOT answered: a row with nothing in `Status` is a question
    nobody has come back to, and reading blank as closed is the direction that
    silently shortens the needs-you list.

    **A FIFTH READING EXISTS AND THIS DID NOT UNIFY IT.** `bin/perry-diagnose`
    asks the same question with its own regex at `bin/perry-diagnose:298` —
    `\\b(answered|resolved|closed|done|decided|已回答|已解决|已决定)\\b`, a
    substring search anywhere in the row rather than a prefix on the cell — and
    the two disagree in BOTH directions. Measured on eight real `Status`
    spellings, four disagree: `dropped 2026-08-20 — folded into TASK-190` and
    `withdrawn 2026-08-20` are answered here and open there, while
    `pending — will be resolved by TASK-9` and `open — the RFC decided against
    it` are open here and answered there. That is `intake_is_discharged`'s
    defect one register over, exactly: same cell, two readings, opposite signs,
    and the number it decides is "open questions waiting on you".

    It is NOT fixed here, and the reason is stated rather than left implicit:
    changing it moves `LOAD-03` counts on somebody's board, `test_diagnose` is
    the suite's one red module today, and a semantic change to a checker under
    a red test is the edit nobody can review. **A finding with no row does not
    get fixed** — so this one has a row, and this paragraph is it.

    **Byte-identical to what `answered` did, deliberately** — `.strip("*` ")`
    rather than `undecorate_cell`, even though the latter also drops `~` and
    would read `~~pending~~` as still open instead of as answered. Moving a
    rule and changing it in the same edit is how a move becomes unreviewable;
    widening it is a decision about somebody's board and belongs to a row that
    says so.
    """
    s = (status_cell or "").strip().strip("*` ").lower()
    return bool(s) and not s.startswith(_ASK_STILL_OPEN)


def _parse_user_input(section: str) -> list[UserInput]:
    """Columns resolved by NAME — see `schema/README.md § Columns resolve by name`.

    This read them positionally, assuming cell 3 of a five-column row was
    `Idle`. **Four real shapes are in circulation**, and the fourth is the one
    this file's own project writes:

      six with `Idle` AND `Asked`   Perry's own board since 2026-08-19, when
                                    `perry-task ask` first ran on it and
                                    `ensure_section_columns` appended `Asked`
                                    beside the `Idle` column already there.
      five with `Idle`              what Perry's board was when this docstring
                                    was written on 2026-08-17, two days
                                    earlier. **The parenthetical that used to
                                    say "Perry's own board" here was stale from
                                    the commit after the one that wrote it** —
                                    stale against the writer TASK-039 shipped
                                    in the same change.
      four with neither            a live project dropped `Idle` because a
                                    stored age is stale the moment it is
                                    written.
      five with `Asked` instead    what `cmd_ask` creates from scratch, and
                                    `USER_COLUMNS` above.

    Under the positional rule the last of those puts a date into `idle` and
    reports every request as having waited zero days.

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
            header = ([squash(c) for c in split_row(prev)]
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
        cells = split_row(line)
        if len(cells) < 4:
            continue
        if squash(cells[0]) in {"", *_column_keys("USER-id")}:
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


def _risk_bullets(section: str) -> list[str]:
    """Every risk bullet in `section`, placeholders and empties dropped.

    The rule is `risk_bullet_text` at the top of this file, which the writer
    calls too. It was mirrored here and in `bin/perry-task` and the copies
    disagreed in both directions — see that function.
    """
    return [t for t in (risk_bullet_text(raw) for raw in section.split("\n"))
            if t]


def _parse_intake(section: str) -> list[dict]:
    """`## Intake` rows: `{arrived, request, outcome, discharged}`.

    `discharged` is the question triage actually asks — a row whose `Outcome`
    is empty is still waiting, and the count of those is what makes an
    over-cap board mean "the queue is not being drained" rather than "the
    board is long".

    The predicate is `intake_is_discharged` above, which the three writers in
    `bin/perry-task` and `bin/perry_store.py § intake_record` also call. It was
    spelled out inline here and in four other places, and the copies disagreed
    — see that function.
    """
    out: list[dict] = []
    header: list[str] = []
    for line in section.split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            continue
        if re.match(r"^\|\s*:?-{2,}", s):
            continue
        cells = split_row(s)
        if not cells:
            continue
        if not header and squash(cells[0]) in set(_column_keys("Arrived")) | {"arrived"}:
            header = [squash(c) for c in cells]
            continue
        if not header:
            header = [squash(c) for c in cells]
            continue
        row = dict(zip(header, cells))
        outcome = (row.get("outcome") or "").strip()
        out.append({
            "arrived": (row.get("arrived") or "").strip(),
            "request": (row.get("request") or "").strip(),
            "outcome": outcome,
            "discharged": intake_is_discharged(outcome),
        })
    return out


def _parse_risks(section: str) -> list[Risk]:
    """`BoardState.risks` — the raw per-line view of `## Top risks`.

    Reads the table too. This field has no consumer in this repo today, which
    is exactly why it needed saying: migrating Perry's board to the table form
    would have left it silently returning [] forever, and the first consumer to
    arrive would have found an empty list and no reason for it.
    """
    tabular = _parse_risk_table(section)
    if tabular is not None:
        return [Risk(text=r.title, resolved=r.resolved) for r in tabular]
    risks: list[Risk] = []
    for text in _risk_bullets(section):
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


# KR ids as written by the templates: "KR-O1.1" (OKR.md), "P002-O1-KR2"
# (phase file — DESIGN-007 decision #4, migrated by TASK-180).
# The legacy bullet form ("- KR1: text") is still accepted for hand-written files.
#
# `_RE_KR_ID` needed no change and that is worth stating rather than
# leaving to be rediscovered: `^(?:KR|P)[-\w.]*\d$` already admitted
# "P002-O3-KR1" — `P`, then `002-O3-KR`, then `1`. It is `_RE_KR_BULLET`
# that hardcoded the shape, spelling the whole prefix `P-O`, and it is the
# one that moved. The **overall** OKR family `KR-O1.1` is untouched: it is
# a different family, out of TASK-180's scope by the same decision.
# `{{NNN}}` is admitted because a phase-KR id now CONTAINS the phase
# number, and a template cannot know it: `goals/state/phase_TEMPLATE.md`
# ships `P{{NNN}}-O1-KR1`, and a reader that rejected it would report the
# template as having no key results at all. That is tolerance for a
# placeholder, not for the old id form — `P-O1.1` [[old-form]] still parses
# here, and still fails `perry-lint` twice over (`schema/state-schema.json`
# `id_pattern`/`pattern`, and `kr-id-legacy-form`). Deliberately: a
# reader that silently dropped the row would hand the checker an empty
# KR set, and an empty set is what every downstream guard treats as
# "nothing to check".
_RE_KR_ID = re.compile(r"^(?:KR|P)(?:\{\{[^}]*\}\}|[-\w.])*\d$")
_RE_KR_BULLET = re.compile(
    r"^-\s*\**((?:KR|P\d+-O)[\w.\-]*\d)\**([^:：]*)[:：]\s*(.+)$"
)


def _table_rows(section: str) -> list[dict[str, str]]:
    """Parse every markdown table in `section` into header-keyed row dicts.

    Header keys are `squash`ed — the one rule every Perry tool normalizes a
    header cell by. Rows shorter than the header are padded; longer rows are
    truncated. Returns [] when no table is present."""
    rows: list[dict[str, str]] = []
    header: list[str] = []
    prev_cells: list[str] = []
    for line in section.split("\n"):
        stripped = line.strip()
        if re.match(r"^\|\s*:?-{2,}", stripped):
            header = [squash(c) for c in prev_cells]
            continue
        if not stripped.startswith("|"):
            prev_cells = []
            if not stripped:
                continue
            header = []
            continue
        cells = split_row(stripped)
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


#: `<state root>/okr.jsonl`. The second of ADR-007's three stores (TASK-092).
OKR_STORE = "okr.jsonl"


def load_okr_store(state_root: Path) -> list[dict] | None:
    """Every record of `<state root>/okr.jsonl`, or `None` when there is none.

    The same contract `load_task_store` documents, for the same reason: `None`
    means the project has not been adopted and its markdown is its state.
    """
    p = Path(state_root) / OKR_STORE
    if not p.exists():
        return None
    try:
        return [json.loads(line) for line
                in p.read_text(encoding="utf-8").split("\n") if line.strip()]
    except (OSError, ValueError):
        return None


def _heading_key(head: str) -> str:
    """A heading as a lookup key: collapsed whitespace, nothing else.

    The store files a KR under the `##` version heading and the `###`
    objective heading it was written beneath (`bin/perry_md_store.py §
    scan_okr`), because `KR-O1.1` is unique inside one objective of one
    version and nowhere else — Perry's own `OKR.md` carries that id twice and
    both are live. Matching those two headings back is therefore the whole
    join, and the ONE thing normalized is the run of spaces a `## v3:  label`
    would differ by. No decoration is stripped: a heading is prose, and
    `squash` is the rule for a table's header cell, which this is not.
    """
    return " ".join(str(head or "").split())


def _krs_from_store(records: list[dict]) -> dict[tuple[str, str], list[KR]]:
    """Store records → `{(version heading, objective heading): [KR, …]}`.

    Both authored forms come back the same way, because the store holds both:
    a KR written as a table row and a KR written as `- KR1: …` differ only in
    the record's `form` field, which is layout and is not read here.
    """
    out: dict[tuple[str, str], list[KR]] = {}
    for rec in sorted(records, key=lambda r: r.get("order")
                      if isinstance(r.get("order"), int)
                      and not isinstance(r.get("order"), bool) else 1 << 30):
        if rec.get("kind") != "kr":
            continue
        stretch = str(rec.get("stretch") or "").strip().lower()
        out.setdefault((_heading_key(rec.get("version")),
                        _heading_key(rec.get("objective"))), []).append(
            KR(id=str(rec.get("id") or ""), text=str(rec.get("text") or ""),
               qualifier=str(rec.get("qualifier") or ""),
               metric=str(rec.get("metric") or ""),
               linked=str(rec.get("linked") or ""),
               stretch=stretch.startswith("y") or stretch == "stretch"))
    return out


def parse_okr(text: str, *, krs: list[dict] | None = None) -> OKR:
    """`OKR.md` → the goals it carries.

    `krs` is the OKR store's records. **When it is given, no KR is read out of
    a table or a bullet in `text`** — every key result comes from the store,
    and the markdown is asked only for the prose the store does not hold: the
    mission, the operating principles, the anti-goals and the version log.
    `None` is a project with no store, which is adoption.
    """
    okr = OKR()
    text = _strip_comments(text)
    stored_krs = None if krs is None else _krs_from_store(krs)

    # Mission: the `## Mission` section (template shape). Older hand-written
    # files put the mission as prose between the H1 and the first ## — fall
    # back to that.
    mission = _section(text, *alias("headings", "Mission"))
    if not mission:
        m = re.search(r"^#\s+[^\n]+\n(.*?)(?=\n## )", text, re.S)
        mission = m.group(1) if m else ""
    okr.mission = mission.strip()

    okr.operating_principles = _bullets(
        _section(text, *alias("headings", "Operating Principles"))
    )

    # Anti-Goals live at the top level in the template; some files nest them
    # inside the current version block instead.
    anti = _section(text, *alias("headings", "Anti-Goals"))

    versions = re.findall(r"\n## v(\d+):\s*([^\n]+)\n(.*?)(?=\n## |\Z)", text, re.S)
    if versions:
        versions.sort(key=lambda v: int(v[0]), reverse=True)
        n, label, body = versions[0]
        okr.version = f"v{n}: {label.strip()}"
        okr.objectives = _parse_okr_objectives(body, stored_krs, okr.version)
        if not anti:
            anti = _section(body, *alias("headings", "Anti-Goals"), level="### ")
    okr.anti_goals = _bullets(anti)

    # Version log: bullets under `## Versioning log` (template) / `## Versioning`.
    for line in _section(text, "Versioning").split("\n"):
        vm = re.match(r"-\s*\**(v\d+)\**[:：]\s*(.+)$", line.strip())
        if vm:
            okr.version_log.append((vm.group(1), vm.group(2).strip()))

    return okr


def _parse_okr_objectives(body: str,
                          stored_krs: dict[tuple[str, str], list[KR]] | None = None,
                          version: str = "") -> list[Objective]:
    objs: list[Objective] = []
    chunks = re.split(r"\n(?=### (?:Objective|目标) \d+)", body)
    for chunk in chunks:
        m = re.match(r"### (?:Objective|目标) (\d+)\s*([^\n]*)\n", chunk)
        if not m:
            continue
        title = _clean_heading_title(m.group(2), f"Objective {m.group(1)}")
        if stored_krs is None:
            krs = _parse_krs(chunk)
        else:
            # The `###` heading AS AUTHORED is the join key, not the cleaned
            # title: `_clean_heading_title` drops the `— ` a heading opens
            # with, and the store filed the row under what the file says.
            krs = stored_krs.get(
                (_heading_key(version),
                 _heading_key(chunk.split("\n", 1)[0].lstrip("# "))), [])
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
        # NOT a table row: this takes the text before an inline `|` inside a
        # `Status:` field, and is named here so the next sweep does not "fix"
        # it. Routing it through `split_row` would honour an escape that must
        # stay literal in prose.
        phase.status = st.group(1).strip().split("|", 1)[0].strip()

    phase.focus = _section(text, *alias("headings", "Phase Focus")).strip()

    cc = _section(text, *alias("headings", "Cost Ceiling"))
    if cc:
        phase.cost_ceiling_raw = cc.strip()
        phase.cost_ceiling_lines = _bullets(cc)

    # Scope-reduction triggers. The template section is
    # `## Phase Scope Reduction Rule` (bullet form); legacy projects may carry
    # a `## Trip-wires` table instead — both land in the same shape.
    srr = _section(text, *alias("headings", "Phase Scope Reduction Rule"))
    if srr:
        phase.scope_triggers = _parse_scope_triggers(srr)
    else:
        legacy = _section(text, "Trip-wires", "Tripwires", "触发线", "触发条件")
        if legacy:
            phase.scope_triggers = _parse_legacy_tripwire_table(legacy)

    # Status of the rule, when the mid-phase check has recorded one.
    mp = _section(text, *alias("headings", "Mid-phase check"))
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
        # `_parse_krs` still runs, and TASK-157 did not make it dead code:
        # a phase document Perry writes carries no KR table any more, but an
        # ADOPTED project's does, and so does a Perry project that has not
        # migrated. `phase_key_results` is what chooses between the two — one
        # source at a time, never merged.
        phase.objectives.append(
            Objective(title=title, raw_body=chunk, number=m.group(1),
                      krs=_parse_krs(chunk))
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
        cells = split_row(line)
        if len(cells) < 3:
            continue
        # **The `"day"` half was dead and is gone.** A V4 reviewer flagged this
        # as a header cell resolved by a second rule — the shape is real — but
        # `if not in_table: continue` above already skips every line before the
        # separator, so the header row never reaches here and no spelling of it
        # ever could. Verified by deleting the whole branch: the parse is
        # unchanged.
        #
        # What remains is reachable and is not a header question at all: a DATA
        # row whose first cell is empty. `squash` rather than `.lower()` so the
        # two rules stay one, at no cost.
        if squash(cells[0]) == "":
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


# `_RE_CLEARED` and `_RE_ISO_DATE` used to be declared here. They are
# `status_is_cleared` / `status_cleared_date` at the top of this file now,
# because `bin/perry-task § cmd_risk_clear` had a third of the same rule
# (`cleared|resolved|closed` — three of eight words) and could therefore clear a
# risk a human had already retired as `mitigated`, overwriting the first
# clear's date and reason.


def _risk_severity(body: str, resolved: bool) -> str:
    """The severity heuristic, shared by both forms.

    Deliberately reads the PROSE rather than a `Severity` column. Both real
    projects checked while writing TASK-040 state severity inside the
    sentence — `H · Apple developer agreement expired` on one, a `🔴` on the
    other — so a stored enum column would have been a column nothing on a real
    board fills, and reading it would have made those two projects look
    severity-less.
    """
    if resolved:
        return "resolved"
    if "TOP RISK" in body.upper() or "(NEW top risk" in body:
        return "top"
    if "APPROVE" in body or "豁免" in body or "接受" in body:
        return "accept"
    return "watch"


#: The magnitude markers real boards put at the front of a risk line, and the
#: rank each one means. Measured, not invented: `H · …` / `M · …` is aimark's
#: board and `🔴 …` is gimegime-pmo's — the two projects TASK-040 checked, and
#: the reason `_risk_severity` reads prose rather than a `Severity` column.
#: The CJK forms are here because `reference/i18n.md` says a board may be
#: written in the project's own language and a marker table that only speaks
#: English would silently rank those boards as unmarked.
_SEVERITY_RANKS = {
    "H": "high", "M": "medium", "L": "low",
    "高": "high", "中": "medium", "低": "low",
    "🔴": "high", "🟡": "medium", "🟠": "medium", "🟢": "low",
}

#: A marker only counts when it stands ALONE as the first token — a separator
#: or whitespace has to follow it. `H · Apple …` and `🔴 9/1 ADR-010 …` are
#: marked lines; `Hostname resolution is flaky` and `H2 database migration`
#: are not, because the character after the `H` is a letter or a digit. That
#: boundary is the whole safety argument: without it this becomes the same
#: over-eager first-token guess that put `id: "Perry"` into a payload.
_RE_SEVERITY_MARKER = re.compile(
    r"^(?P<marker>[HML]|[高中低]|[🔴🟡🟠🟢])(?:\s*[·•・:：\-—–]\s*|\s+)(?=\S)"
)


def split_severity_marker(text: str) -> tuple[str, str, str]:
    """`("H", "high", "Apple developer agreement expired")`.

    Returns `("", "", text)` unchanged when the line carries no marker, which
    is the common case and must cost the caller nothing.

    This exists because the marker was being read as the risk's ID. On a real
    board `- H · Apple developer agreement expired — notarized builds blocked`
    arrived as `{"id": "H", "title": "· Apple developer agreement expired",
    "severity": "watch"}`: the letter became the handle, the separator stayed
    glued to the front of the title, and the one thing the human actually
    said about severity was thrown away. Three defects, one cause — nothing
    told the parser that the first token was a severity marker.
    """
    m = _RE_SEVERITY_MARKER.match(text.strip())
    if not m:
        return "", "", text
    marker = m.group("marker")
    return marker, _SEVERITY_RANKS.get(marker, ""), text.strip()[m.end():].strip()


def _has_risk_header(section: str) -> bool:
    """Whether any table in `section` declares a risk-statement column.

    The predicate is `is_risk_register_header` at the top of this file, which
    the writer and the store both call. This function only finds the headers to
    ask it about.
    """
    lines = section.split("\n")
    for i, line in enumerate(lines):
        if not re.match(r"^\|\s*:?-{2,}", line.strip()) or i == 0:
            continue
        prev = lines[i - 1].strip()
        if not prev.startswith("|"):
            continue
        if is_risk_register_header(split_row(prev)):
            return True
    return False


def _parse_risk_table(section: str) -> list[TopRisk] | None:
    """The `## Top risks` table form, or None when the section has no table.

    Returning None rather than [] is the whole contract: an EMPTY table means
    "this project migrated and currently has no risks", while no table at all
    means "this project still writes bullets" — and the caller must fall back
    only in the second case. Collapsing them would make a migrated project with
    zero risks silently re-parse its own prose preamble as risk bullets.

    Columns resolve by NAME through the schema glossary (`schema/README.md
    § Columns resolve by name`), never by position.
    """
    # Detected from the HEADER, not from the rows: a migrated project that
    # currently has no risks has a header and zero rows, and asking the rows
    # whether a table exists would answer "no" and send it back to the bullet
    # path — where it would re-read its own prose preamble as risks.
    #
    # `Risk` is the column that identifies the migrated shape. A table under
    # this heading with no risk-statement column is something else — a legend,
    # a severity key — and is left to the bullet path rather than read as rows,
    # because guessing which cell holds the sentence is exactly the invention
    # this task exists to remove.
    if not _has_risk_header(section):
        return None

    out: list[TopRisk] = []
    for row in _table_rows(section):
        statement = _col(row, "Risk")
        if not statement:
            continue
        rid = undecorate_cell(_col(row, "ID"))
        status = _col(row, "Status")
        resolved = status_is_cleared(status) or \
            bool(re.search(r"\*\*RESOLVED", statement)) or statement.strip().startswith("~~")
        # `""` when the row is cleared and names no date. Not today's date —
        # see `status_cleared_date`.
        cleared_on = status_cleared_date(status) if resolved else ""
        pct = _RE_PCT.search(statement)
        # DETECTED, not stripped. A table's `Risk` cell comes back whole —
        # `test_the_statement_is_never_split_into_an_id_and_a_remainder` is the
        # guard on that, and it is the promise that distinguishes the table
        # form from the bullet guessing it replaced. So a marker written into
        # a table cell still ranks the row, and still leaves `title` verbatim.
        sev_text, sev_rank, _ = split_severity_marker(statement)
        out.append(TopRisk(
            id=rid or "?",
            title=statement,
            severity=_risk_severity(statement, resolved),
            severity_text=sev_text,
            severity_rank=sev_rank,
            meta=statement,
            value=float(pct.group(1)) if pct else None,
            source="table",
            opened=_col(row, "Opened").strip(),
            status=status,
            cleared_on=cleared_on,
        ))
    return out


def top_risks_section(text: str) -> str | None:
    """The body of `## Top risks`, or None when the document has no such
    section. One extractor, so "does this file have a risk table?" and "what
    are its risks?" can never be answered about different spans of text."""
    # **Scanned with `heading_is`, not a fourth regex.** This was the fourth
    # implementation of "where is this section": `parse_board` used
    # `heading_is`, `bin/perry-task § ensure_section` used a regex, the id
    # minter read the rows by a third rule, and this had a regex of its own.
    # On `## **Top risks**` they gave three different answers in one call —
    # `risk-add` appended a second section at exit 0 while the minter, which
    # could see the existing rows, numbered from them. Fixing three of the four
    # left this one, and the reader still reported zero risks on a board that
    # had them.
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if not line.startswith("## ") or not heading_is(line[3:], "Top risks"):
            continue
        end = next((j for j in range(i + 1, len(lines))
                    if lines[j].startswith("## ")), len(lines))
        return "\n".join(lines[i + 1:end])
    return None


def has_risk_table(text: str) -> bool:
    """Whether this document's `## Top risks` has migrated to the table form.

    The same question `_parse_risk_table` asks, asked about a whole document
    and separately from its answer: a migrated project that currently has no
    risks parses to `[]`, and `[]` must not read as "never migrated".
    """
    section = top_risks_section(text)
    return section is not None and _has_risk_header(section)


def parse_top_risks(text: str) -> list[TopRisk]:
    risks: list[TopRisk] = []
    section = top_risks_section(text)
    if section is None:
        return risks

    # Table when present, bullets when not. Projects that have not migrated —
    # and at the time this shipped that was every project except Perry itself —
    # must keep parsing exactly as before, so the bullet path below is
    # untouched rather than reimplemented.
    tabular = _parse_risk_table(section)
    if tabular is not None:
        return tabular

    for body in _risk_bullets(section):
        resolved = bool(re.search(r"\*\*RESOLVED", body)) or body.startswith("~~")

        # Strip leading ~~strike~~ markers for ID/title extraction
        # (keep the original body for the meta field).
        clean = re.sub(r"~~([^~]*)~~", r"\1", body).strip()

        # A leading severity marker comes off BEFORE anything looks for an id.
        # It is read both bare (`- H · …`) and inside the bold chunk the id
        # scan targets (`- **🔴 9/1 ADR-010 …**`), and both forms were feeding
        # the marker to `short_id`. Taking it here means the id/title logic
        # below sees the sentence a human wrote, not the label in front of it.
        sev_text, sev_rank, clean = split_severity_marker(clean)
        if not sev_text:
            bold = re.match(r"\*\*\s*([^*]+?)\s*\*\*", clean)
            if bold:
                inner_text, inner_rank, inner_rest = split_severity_marker(bold.group(1))
                if inner_text:
                    sev_text, sev_rank = inner_text, inner_rank
                    clean = f"**{inner_rest}**" + clean[bold.end():]

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
            # No bold at all: THE WHOLE LINE IS THE STATEMENT.
            #
            # This used to take the first space-separated token as an id and
            # publish the remainder as the title, which meant every unbolded
            # bullet lost its first word. `- H · Apple developer agreement
            # expired` reported `Apple` as the id and `· Apple` was never in
            # the title at all; `- Perry is half-adopted: …` reported `Perry`.
            # `test_the_statement_is_never_split_into_an_id_and_a_remainder`
            # already states the rule for the table form — "a sentence is not
            # a record" — and the bullet form is where the sentence actually
            # lives. Now that a bullet publishes no id, the split has nothing
            # left to produce and only ever cost a word.
            #
            # The trailing-detail split stays: `statement — elaboration` is a
            # real convention on these lines and the title is the first half.
            first_word = re.match(r"(\S+)", clean)
            short_id = first_word.group(1).rstrip(",.:;") if first_word else "?"
            title = clean.split(" — ")[0].strip()

        meta = body
        # value: first percentage in line
        pct_match = _RE_PCT.search(body)
        value = float(pct_match.group(1)) if pct_match else None

        sev = _risk_severity(body, resolved)

        risks.append(
            TopRisk(
                # A BULLET HAS NO ID, and saying so is the honest answer.
                # `short_id` is the first word of somebody's sentence — this
                # class's own docstring calls it meaningless, and the reader
                # tests say the same — so publishing it under the same key a
                # table's minted `RX-001` uses invites a consumer to treat the
                # two alike. `source` already says which form this came from;
                # `""` is what that means for the handle.
                id="",
                title=title or short_id,
                severity=sev,
                severity_text=sev_text,
                severity_rank=sev_rank,
                meta=meta,
                value=value,
            )
        )
    return risks


# ── decisions/ADR-*.md ────────────────────────────────────────────────────
#
# **The ADR files are the record and there is no index.** `DECISIONS.md` was a
# rendered projection of exactly these files, and TASK-235 deleted it under
# DESIGN-013 § 5.3 — so the reader that used to parse its `## Active` table
# reads the directory instead. Nothing replaces the file (§ 4.1: the link
# surface it gave a web reader is given up, deliberately, and must not be
# re-added under another name).
#
# **This lives here rather than in `bin/perry-decide`, and that is the point.**
# `perry-decide` carried its own tolerant header parser while this module
# carried a table parser for the rendering of it — two readers of one record.
# With the table gone there is one reader, and `bin/perry-decide` imports it
# (`import parsers as P`). A second implementation is the defect this project
# has now caught six times; `split_row` reached six copies before TASK-234
# found the last one.

ADR_ID_RE = re.compile(r"\bADR-(\d+)\b")


def adr_header_fields(text: str) -> dict:
    """The `> Key: value` block at the top of an ADR, normalized.

    Tolerant by construction. Every one of these is real, from files in this
    repo and its templates:

        > **Status**: active          > Status: active
        > **Sunset criteria**: —      > Sunset: —
        > Deciders: Ran Jiao          (absent entirely)

    Keys are lowercased with punctuation stripped, so `Sunset criteria` and
    `Sunset` land on the same key and a caller does not need to know which
    generation of the template produced the file.
    """
    out: dict[str, str] = {}
    for line in text.split("\n"):
        s = line.strip()
        if not s.startswith(">"):
            if s.startswith("#") or not s:
                continue
            break
        # Two fields share one line in every ADR this repo has written:
        # `> Supersedes: —   · Superseded by: —`. Reading to end-of-line gives
        # `Supersedes` the value "· Superseded by: —", which is not a wrong
        # format on the file's part — it is a wrong assumption on the reader's.
        for part in re.split(r"\s+·\s+|\s+\|\s+", s.lstrip("> ").strip()):
            m = re.match(r"\**\s*([A-Za-z][\w ]*?)\s*\**\s*[:：]\s*(.*)$", part)
            if not m:
                continue
            key = re.sub(r"\s+", " ", m.group(1)).strip().lower()
            key = {"sunset criteria": "sunset", "superseded by": "superseded_by",
                   "status date": "status_date"}.get(key, key)
            out.setdefault(key, m.group(2).strip().strip("*` "))
    return out


def read_adr_records(state_root: Path) -> list[dict]:
    """Every `decisions/ADR-*.md`, as records, id-sorted.

    The record `perry-decide list` publishes, and the source `parse_decisions`
    below projects for the snapshot. Reading is tolerant and reports what the
    file says — an off-enum `status` is named by the caller, never corrected
    here.
    """
    out: list[dict] = []
    d = state_root / "decisions"
    if not d.is_dir():
        return out
    for p in sorted(d.glob("ADR-*.md")):
        text = p.read_text(errors="replace")
        h = adr_header_fields(text)
        title = ""
        first = next((l for l in text.split("\n") if l.startswith("# ")), "")
        if first:
            # `# ADR-001: Title`, `# ADR-001 — Title`, and a bare `# Title` are
            # all in circulation; strip the id and whichever separator follows.
            title = re.sub(r"^ADR-\d+\s*[—:–-]?\s*", "", first[2:].strip()).strip()
        m = ADR_ID_RE.search(p.name)
        out.append({
            "id": f"ADR-{int(m.group(1)):03d}" if m else p.stem,
            "title": title,
            "type": h.get("type", ""),
            "status": (h.get("status") or "active").lower(),
            "date": h.get("date", ""),
            "deciders": h.get("deciders", ""),
            "supersedes": h.get("supersedes", "").strip("—- ") or "",
            "superseded_by": h.get("superseded_by", "").strip("—- ") or "",
            "sunset": h.get("sunset", "").strip("—- ") or "",
            "path": str(p.relative_to(state_root)),
            "lines": len(text.split("\n")),
        })
    return out


def parse_decisions(state_root: Path) -> list[ADR]:
    """The snapshot's `adrs` — **active decisions, newest first**.

    Active-only and newest-first are not new: the reader this replaces parsed
    the `## Active` section of `DECISIONS.md` and sorted descending by number,
    and `bin/perry-state § expired_sunsets` says so in its own docstring —
    "Active ADRs whose date-based sunset criteria have passed". Feeding it the
    superseded ones too would start warning about the sunset of a decision that
    is no longer in force.

    It takes the **state root**, not text: there is no document to hand it any
    more. That signature change is why the one other caller,
    `bin/perry-migrate § records_in`, drops its `DECISIONS.md` branch instead
    of being ported — a before/after reading of a file neither side can have.
    """
    adrs = [
        ADR(
            id=r["id"],
            title=r["title"],
            type=r["type"],
            date=r["date"],
            sunset_or_notes=r["sunset"],
            file_path=r["path"],
        )
        for r in read_adr_records(state_root)
        if r["status"] == "active"
    ]

    # Newest first by ADR number (e.g. ADR-024 before ADR-001).
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


def walk_design(root: Path, board: BoardState | None = None,
                project_root: Path | None = None) -> list[DesignDoc]:
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

    # **And the closures that have already left the board.** `perry-task done`
    # REMOVES the row it closes, so a board-only count reports `impl_refs: 0`
    # for a design whose implementation tasks are all FINISHED — and
    # `perry-state` turns that into "pending hand-off". `DESIGN-004` is
    # `bin/perry-task` itself, 3,300 lines shipping with 11 close events
    # against its id, and Perry reported it as never handed off.
    #
    # The same trap `bin/perry-lint § check_verification` documents in its own
    # docstring, in a second reader that did not know about it. Counted here
    # rather than in the caller so every consumer of `walk_design` gets the
    # corrected number.
    # `.perry/` is anchored to the PROJECT root and this function receives the
    # STATE root, which may be a subdirectory of it (`perry/` here).
    # `load_snapshot` now hands over the exact project root — `resolve_project_root`
    # is the stored inverse this comment used to say nobody had written (TASK-159)
    # — so the first probe below lands. The bounded walk stays for the callers
    # that pass no `project_root` at all, where a guess still beats no log.
    log = None
    probe = project_root or root
    for _ in range(4):
        cand = probe / ".perry" / "events.jsonl"
        if cand.exists():
            log = cand
            break
        if probe.parent == probe:
            break
        probe = probe.parent
    if log is not None:
        for line in log.read_text(errors="replace").split("\n"):
            if line.strip():
                task_blobs.append(line)

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
            cells = split_row(line)
            if len(cells) < 5 or squash(cells[0]) == "id":
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
                linked=str(kr.get("linked") or ""),
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


#: `P003-O2-KR1` → `O2`. A phase KR id names the objective it belongs to, so
#: attaching a register's KRs to a document's headings needs no position match
#: and no second field to keep in sync.
_KR_OBJECTIVE_RE = re.compile(r"^P\d{3}-(O\d+)-KR\d+$")


def kr_objective_id(kr_id: str) -> str:
    m = _KR_OBJECTIVE_RE.match((kr_id or "").strip())
    return m.group(1) if m else ""


def phase_key_results(phase, linkage) -> list["KR"]:
    """A phase's key results, from the ONE place that declares them — TASK-157.

    The id, title, metric and target of a phase KR used to be written **twice**:
    as a row of a markdown table in `phase/<NNN>-<slug>.md`, and as a `krs[]`
    entry in `phase/<NNN>-linkage.md`. Nothing compared the two, the markdown
    copy is the one that went stale, and it had — `P003-O2-KR1` read a target
    the register did not.

    DESIGN-013 § 5.1, locked 2026-08-29: *a fact that has a schema lives in
    exactly one store; a document holds what has no schema; no field lives in
    both.* Those four fields are schema'd (`files[id=linkage].frontmatter`), so
    they live in the register and the phase document carries no KR table.

    **The document is still read, and only when there is no register.** An
    adopted project's phase file carries a table (that is what adoption reads),
    and so does a Perry project written before this row. `linkage` answering
    with objectives is the test, so the two sources are never merged and never
    both consulted: a project has a register or it has a table, and which one
    answered is observable in `perry-goals list --json § conformance`.

    Returned as `KR` — the same shape the document's table produced — so every
    consumer downstream of this function is unchanged by where the values came
    from. `linked` is carried because TASK-157 moved that column into the
    register rather than dropping it with the table.
    """
    declared = [k for o in (getattr(linkage, "objectives", None) or [])
                for k in (getattr(o, "krs", None) or [])]
    if not declared:
        return list(getattr(phase, "krs", None) or [])
    return [KR(id=k.id, text=k.title, metric=kr_metric_cell(k),
               linked=k.linked, stretch=bool(k.stretch)) for k in declared]


def kr_metric_cell(kr: "LinkageKR") -> str:
    """The register's two target fields → the one string a reader is shown.

    `metric` is *"prose; always safe to display"* in the schema and is what the
    `Metric / Target` column always held. `target` is *"NUMBER ONLY. Omit for
    prose targets"*, so it is what there is to show exactly when there is no
    prose — a register carrying only a number must not display an empty metric.
    """
    if kr.metric:
        return kr.metric
    if kr.target is None:
        return ""
    return f"{kr.target:g}"


def phase_key_results_by_objective(phase, linkage) -> list[list["KR"]]:
    """`phase_key_results`, grouped to match `phase.objectives` one for one.

    A KR is attached to the objective its **id** names (`P003-O2-KR1` → the
    document's `## Objective 2`). A registered KR whose objective the document
    has no heading for is appended to the last objective rather than dropped:
    losing it would make `kr_total` disagree with the sum of the groups, and a
    payload that cannot add up is worse than one whose grouping is approximate.
    """
    objectives = list(getattr(phase, "objectives", None) or [])
    krs = phase_key_results(phase, linkage)
    if not objectives:
        return []
    declared = [k for o in (getattr(linkage, "objectives", None) or [])
                for k in (getattr(o, "krs", None) or [])]
    if not declared:
        return [list(o.krs) for o in objectives]
    slots: dict[str, int] = {}
    for n, o in enumerate(objectives):
        slots.setdefault(o.number or str(n + 1), n)
    out: list[list[KR]] = [[] for _ in objectives]
    for kr in krs:
        oid = kr_objective_id(kr.id)
        at = slots.get(oid.lstrip("O"), len(objectives) - 1)
        out[at].append(kr)
    return out


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


# ── .perry/roles/*.md + the escalation union (DESIGN-006 § 5.2) ────────────
#
# THE UNION ONLY EVER GROWS. A role's `## Must escalate` list is ADDED to the
# project's high-stakes list from `.perry/hook.md`; it never substitutes for
# it. Get that backwards and hiring a role quietly NARROWS what the project
# refuses to do unsupervised — the opposite of what a role is for, and
# invisible, because the narrowed scan still passes everything it is asked.
#
# This is the one implementation. `bin/perry-lint` and `bin/perry-state` both
# call it rather than each carrying a copy: two extractions of one rule is how
# `squash` went wrong above, and an escalation list is a worse place to
# discover the same defect than a table header is.


#: The extraction rule, in one place: only **backticked spans** count, and only
#: those long enough to carry a meaning (`extracts` below). Prose does not
#: extract — which is exactly the `hook_TEMPLATE.md` backtick bug, and the
#: reason a `Must escalate` line that yields no fragment is a lint warning
#: rather than a silent no-op.
_BACKTICKED = re.compile(r"`([^`]+)`")


def extracts(frag: str) -> bool:
    """Is this backticked span long enough to be a scan fragment?

    **The floor is measured per script, because the matcher is.** It used to be
    a flat `len(frag) > 2`, and that number is an ASCII assumption which
    directly contradicted `_ESC_WORD` two hundred lines below: that class is
    written ASCII-only *on purpose*, so that a CJK fragment matches unguarded
    and a hook's Chinese half is not silently weaker than its English half
    (ADR-007's fifth `CLOCK_RE` round, `下周期` vs `next cycle`). A flat floor
    of 2 characters undid it from the other end — the CJK fragment never
    reached the matcher to be unguarded, because it never became a fragment.
    TASK-200 measured the size of that hole: **18 of 20** Chinese trading verbs
    a real finance role would escalate on, `下单` and `平仓` among them,
    extracted to nothing and warned about nothing.

    So the two decisions now say the same thing — ASCII and CJK are different
    measures — instead of contradicting each other:

    - **Pure ASCII: still `len > 2`.** One or two ASCII characters is a flag,
      a punctuation mark or a two-letter word: `sh`, `rm`, `go`, `-f`, `*`.
      Those are noise, and the edge guard cannot save them — `go` guarded at
      both edges still matches the English word "go" in any spec that uses it.
      A gate that cries wolf on ordinary prose gets waved through, which is
      TASK-107's whole finding, so this half of the floor is kept unchanged.
    - **Anything with a non-ASCII character: `len > 1`.** Two characters is the
      ordinary *word* in Chinese, not an abbreviation of one — `下单`, `平仓`,
      `建仓` are as whole as `deploy` is. A floor of three there is not a noise
      filter, it is a blanket refusal to arm on an entire domain vocabulary.

    A single character is never enough in either script. In ASCII it is
    punctuation; in CJK it is a morpheme that occurs inside a large share of
    the compounds around it, and there is no boundary available to guard it
    with — the same "matches everywhere" shape, arrived at from the other side.

    What this does NOT fix, and is not this function's to fix: a CJK fragment
    still matches inside a longer compound and still cannot express polarity,
    so `下单` fires on `系统永不下单` ("the system never places orders"). That
    is a property of a boundary-free script, named in TASK-200 § 11 and left
    standing here rather than papered over with a floor that hides the token
    altogether.
    """
    frag = (frag or "").strip()
    return len(frag) > (2 if frag.isascii() else 1)


def line_fragments(line: str) -> list[str]:
    """Every scan fragment ONE escalation bullet yields, in order.

    Split out of `escalation_fragments` so that "did this line contribute
    anything" is answerable — `escalate_unextractable` asks exactly that, and
    used to ask "does this line contain a backtick" instead, which is a
    different question with the same answer only in ASCII.
    """
    if "{{" in line:                         # an unfilled template placeholder
        return []
    out: list[str] = []
    for frag in _BACKTICKED.findall(line):
        frag = frag.strip().lower()
        if extracts(frag) and frag not in out:
            out.append(frag)
    return out


def escalation_fragments(lines: list[str]) -> list[str]:
    """Backticked spans from escalation bullets, lowercased, order preserved.

    Shared by `.perry/hook.md § High-stakes operations` and a role card's
    `## Must escalate`, because § 5.2 says a role's list is extracted *exactly
    like* the hook's. If the two ever extract differently, a term a role
    declares would mean something other than the same term in the hook.
    """
    out: list[str] = []
    for line in lines:
        for frag in line_fragments(line):
            if frag not in out:
                out.append(frag)
    return out


def unextractable_lines(lines: list[str]) -> list[str]:
    """The bullets that contribute NOTHING — the complement of the function above.

    **One predicate, both halves of the union, for the reason
    `escalation_fragments` gives one paragraph up.** That docstring says the
    two sides must EXTRACT the same way or "a term a role declares would mean
    something other than the same term in the hook". The same argument decides
    reporting: if only one side is asked which of its bullets died, then
    whether a rule is *known* to be unenforceable depends on which file it was
    written in — and the file every project has was the side not asked.
    TASK-202 measured a real project whose hook turned **5 bullets into 3
    fragments**, three of them silent, while the same three sentences on a role
    card would each have been warned about.

    Note the asymmetry this replaces was not in the extractor: `line_fragments`
    was already shared. It was in *who called it*. A shared extractor with one
    caller is how a check comes to cover half of what it describes.
    """
    return [line for line in lines if not line_fragments(line)]


def unextractable_says(bullet: str, where: str) -> str:
    """The sentence a reader is told, for either half. One text, three surfaces.

    `bin/perry-lint` says it about a role card and about the hook, and
    `bin/perry-state` says it in the standup. Three copies is how the fourth
    one goes stale: `perry-state` still said *"has no backticked span"* after
    TASK-201 proved that sentence false — backticks are not the test, the
    extractor is, and a line whose only span is below `extracts`' floor has a
    backtick and yields nothing. The copy nobody edited kept telling the user
    to look for the thing that was not the problem.

    `where` names the section, because that is the only part that legitimately
    differs between the two halves.
    """
    return (f"{where} line {bullet!r} yields no scan fragment, so it "
            f"contributes nothing to the pre-flight scan. The union matches "
            f"`backticked` spans the extractor keeps: a prose line — or a span "
            f"too short to carry a meaning — reads as a rule and enforces "
            f"nothing.")


#: How the two halves name themselves in that sentence.
HOOK_SECTION = "`.perry/hook.md § High-stakes operations`"
CARD_SECTION = "`Must escalate`"


def hook_escalation_lines(project_root: Path) -> list[str]:
    """The `## High-stakes operations` bullets from `.perry/hook.md`."""
    path = Path(project_root) / ".perry" / "hook.md"
    if not path.exists():
        return []
    text = _strip_comments(path.read_text(errors="replace"))
    # `"High-stakes"` is a PREFIX tolerance, not an alias the schema declares —
    # saying so is the difference between reading the table and quietly
    # extending it. It is spelled here and nowhere else: `bin/perry-state` and
    # `bin/perry-lint` both had their own copy of this read, and the linter's
    # was spelled without the tolerance, so a hook headed `## High-stakes` was
    # armed for the gate and unarmed for the linter (TASK-202).
    body = _section(text, *alias("headings", "High-stakes operations"),
                    "High-stakes")
    return [b for b in _bullets(body) if "{{" not in b]


def hook_escalation_unextractable(project_root: Path) -> list[str]:
    """The hook bullets that enforce nothing. `[]` when there is no hook at all.

    **Absence is not failure**, and this is where that inversion would land if
    it were going to: a project with no `.perry/hook.md` has no bullets, so it
    has no dead ones, and every caller here reports zero rather than N.
    `hook_escalation_lines` already returns `[]` for a missing file — the
    property is inherited rather than re-implemented, because TASK-117 and
    TASK-156 were both a second place that decided the same thing differently.
    Whether an unarmed hook deserves a word at all is a DIFFERENT check, and
    `hook-high-stakes-armed` has been making that call since long before this.

    This is the one-call form, for a caller that has a project root and wants
    the answer. `bin/perry-lint` and `bin/perry-state` already hold the bullets
    when they ask — they read the section for other reasons — so they call
    `unextractable_lines` on what they have rather than reading the file twice.
    """
    return unextractable_lines(hook_escalation_lines(project_root))


@dataclass
class RoleCard:
    """A hiring contract, never a workflow (DESIGN-006 decision #1).

    Each field has one mechanical consumer, and nothing else reads the file:

      context, may_touch   → rendered into the delegation prompt VERBATIM
      loads_knowledge      → § 5.4 subscription injection, by topic
      escalate_fragments   → UNIONED into the dispatch pre-flight scan
      accepted_by, rung    → the close-task gate; the stricter of mode-rung
                             and role-rung wins (DESIGN-003 § 5.3)
    """
    name: str = ""
    path: str = ""
    accepted_by: str = ""
    default_rung: str = ""
    executors: str = ""
    context: str = ""
    may_touch: str = ""
    loads_knowledge: list[str] = field(default_factory=list)
    loads_pack: list[str] = field(default_factory=list)
    escalate_lines: list[str] = field(default_factory=list)
    escalate_fragments: list[str] = field(default_factory=list)
    #: Escalation bullets carrying no backticked span. They read as rules and
    #: enforce nothing — the failure class `hook_TEMPLATE.md` already shipped.
    escalate_unextractable: list[str] = field(default_factory=list)


_ROLE_FIELD = {
    "accepted_by": "Accepted by",
    "default_rung": "Default rung",
    "executors": "Executors",
}


def _role_header_field(text: str, label: str) -> str:
    m = re.search(rf"^\s*[-*]?\s*\**\s*{re.escape(label)}\s*\**\s*[:：]\s*([^\n]*)$",
                  text, re.M)
    return m.group(1).strip().strip("*` ") if m else ""


def _loads_topics(section: str, label: str) -> list[str]:
    """`- knowledge: reporting, ledger-quirks` → `['reporting', 'ledger-quirks']`."""
    out: list[str] = []
    for b in _bullets(section):
        m = re.match(rf"^{re.escape(label)}\s*[:：]\s*(.*)$", b.strip(), re.I)
        if not m:
            continue
        for tok in re.split(r"[,，;；]", m.group(1)):
            tok = tok.strip().strip("*`")
            if tok and "{{" not in tok and tok not in out:
                out.append(tok)
    return out


def parse_role_card(name: str, text: str) -> RoleCard:
    text = _strip_comments(text)
    card = RoleCard(name=name)
    for attr, label in _ROLE_FIELD.items():
        setattr(card, attr, _role_header_field(text, label))
    card.context = _section(text, "Context").strip()
    card.may_touch = _section(text, "May touch").strip()
    loads = _section(text, "Loads")
    card.loads_knowledge = _loads_topics(loads, "knowledge")
    card.loads_pack = _loads_topics(loads, "pack")
    card.escalate_lines = [b for b in _bullets(_section(text, "Must escalate"))
                           if "{{" not in b]
    card.escalate_fragments = escalation_fragments(card.escalate_lines)
    # **Asked of the extractor, not of the punctuation.** This read
    # `not _BACKTICKED.search(b)` — "does the line contain a backtick" — which
    # answers the right question only when every backticked span becomes a
    # fragment. It does not: `extracts` has a floor, and a line whose only
    # span is below it looks constrained, reads as a rule, contributes nothing
    # and warned about nothing. That is `hook_TEMPLATE.md`'s failure class
    # (DESIGN-006 § 7) arriving through the hole its own fix left open.
    # `schema/roles-list-contract.md § must_escalate.unextractable` already
    # said "bullets that yielded no fragment"; the code, not the contract, was
    # the deviation.
    # Through `unextractable_lines`, which the hook half now asks too. The
    # comprehension that stood here was correct and was the ONLY caller —
    # which is exactly how the hook, the half every project has, went
    # unchecked for as long as this check has existed (TASK-202).
    card.escalate_unextractable = unextractable_lines(card.escalate_lines)
    return card


def read_role_cards(project_root: Path) -> list[RoleCard]:
    """Every card in `.perry/roles/`, by filename. Empty when none is declared.

    Goal 7 lives here: no directory, or an empty one, returns `[]`, and every
    caller downstream degrades to exactly today's behaviour.
    """
    rdir = Path(project_root) / ".perry" / "roles"
    out: list[RoleCard] = []
    for md in sorted(rdir.glob("*.md")) if rdir.is_dir() else []:
        card = parse_role_card(md.stem, md.read_text(errors="replace"))
        card.path = md.relative_to(Path(project_root)).as_posix()
        out.append(card)
    return out


def escalation_union(project_root: Path) -> dict:
    """The dispatch pre-flight's scan list: hook fragments ⊕ every role's.

    Returns the union **and its two halves separately**, on purpose. A caller
    that only ever sees a merged list cannot tell an addition from a
    substitution, and neither can a test — so the halves are part of the
    contract, not an implementation detail. `origins` says which side each
    fragment came from, which is what makes a replacement structurally visible
    instead of merely numerically smaller.

    `project` is computed the same way whether or not roles exist. That is the
    whole safety property: declaring a role can only ever ADD to what the
    project refuses to do unsupervised.

    `unextractable` is the same shape as the two halves above and carries what
    each side wrote down and did NOT arm: `{"hook": [...], "roles": {name:
    [...]}}`. It is here rather than only in the two reporters because the
    number that matters is *bullets minus fragments*, and until TASK-202 no
    single value in this payload could be compared with the hook's own list to
    produce it. A gate reporting `armed: true` over three dead sentences out of
    five is worse than one reporting `armed: false`: the second is honest.
    """
    hook_lines = hook_escalation_lines(project_root)
    project = escalation_fragments(hook_lines)
    cards = read_role_cards(project_root)
    roles = {c.name: list(c.escalate_fragments) for c in cards}

    origins: dict[str, list[str]] = {}
    union: list[str] = []
    for frag in project:
        union.append(frag)
        origins.setdefault(frag, []).append("hook")
    for name in roles:
        for frag in roles[name]:
            if frag not in union:
                union.append(frag)
            origins.setdefault(frag, []).append(f"role:{name}")
    return {
        "project": project,
        "roles": roles,
        "union": union,
        "origins": origins,
        "armed": bool(union),
        "unextractable": {
            "hook": unextractable_lines(hook_lines),
            "roles": {c.name: list(c.escalate_unextractable) for c in cards},
        },
    }


#: The escalation matcher's word class, **written out on purpose**. Never `\w`,
#: never `\b`. ADR-007's fifth `CLOCK_RE` round is the reason: `\b` does not
#: exist in Chinese, so a `\b`-guarded matcher word-bounds the English half of
#: a hook and leaves the Chinese half matching bare — the exact asymmetry that
#: let `下周期` write a live row while `next cycle` was refused. An explicit
#: ASCII class has one meaning in both. A hook's match tokens are ASCII
#: commands and paths by construction — `tests/fixtures/sample-project-zh/
#: .perry/hook.md` states that invariant in the fixture itself — and CJK prose
#: around such a token is not a word character here, so the token still matches.
_ESC_WORD = "[A-Za-z0-9_]"


@lru_cache(maxsize=512)
def escalation_pattern(frag: str) -> re.Pattern:
    """`frag` guarded at ITS OWN edges — not at both edges unconditionally.

    The fragments are not all words, so which guards a fragment gets is decided
    by its own first and last character. `~/.claude/skills` starts with `~` and
    `design/` ends with `/`; a guard demanding a word boundary there would be
    demanding a word character that is never present, and both fragments would
    stop matching anything at all — a gate that silently matches nothing being
    the failure this whole section exists to avoid.

        origin              (?<!W)origin(?!W)         both edges are letters
        ~/.claude/skills    escape(~/.claude/skills)(?!W)  leading `~`: none
        design/             (?<!W)design/             trailing `/` needs none
        --force-with-lease  --force-with-lease(?!W)   leading `-` needs none

    That is what stops `origin` matching "original" and `main` matching
    "remains", while `git push origin main`, `design/anything`,
    `push --force` inside `push --force-with-lease`, and `~/.claude/skills` all
    still match.

    **The cost is stated rather than special-cased.** A right-edge guard cannot
    match `ln -sf` from `ln -s`, `rm -rfv` from `rm -rf`, or `tokens` from
    `token`: that is the same morphology that stops `adopted` matching `adopt`,
    and no rule separates them lexically. The hook enumerates the forms it
    means — `publish` and `published`, `prod` and `production` — and that
    convention, not an exception in here, is what covers them.
    """
    if not frag:
        return re.compile(r"(?!)")          # matches nothing, and says so
    left = f"(?<!{_ESC_WORD})" if re.match(_ESC_WORD, frag[0]) else ""
    right = f"(?!{_ESC_WORD})" if re.match(_ESC_WORD, frag[-1]) else ""
    return re.compile(left + re.escape(frag) + right)


def matching_escalations(haystack: str, fragments: list[str]) -> list[str]:
    """Every scan fragment present in `haystack` at a word edge, case-folded.

    The pre-flight's matcher, factored out so the union can be tested at the
    behaviour it is for — *does this text trip the scan* — and not merely at
    the shape of a list. A "one lookup" rewrite that kept the list shape but
    dropped a source would still let a project term through here.

    **This used to be a bare substring test** (`f in hay`), and on 2026-08-20 it
    read `origin` out of "its original bytes" and `adopt` out of "on an adopted
    project", refusing two dispatches that touched no remote and ran no adoption
    — while `main` read itself out of "remains" on two more. The cost is not the
    adjudication: it is that a gate crying wolf on ordinary English gets waved
    through, and that the cheapest way to pass it was to reword the spec, which
    is the one thing a safety gate must never pay out for. TASK-107.
    """
    hay = (haystack or "").lower()
    return [f for f in fragments if f and escalation_pattern(f).search(hay)]


#: The three spec sections `work/reference/dispatch.md` pre-flight step 4 reads,
#: split by what a hit in each one MEANS. The first two say "the task touches
#: this"; the third says "the task has written down that it does not".
#:
#: **These are canonical names, resolved through `alias()` below — never
#: matched literally.** They read literally for eleven days anyway, because the
#: glossary carried no `zh` spelling for any of the three while the hook
#: heading on the other side of the same gate (`High-stakes operations` →
#: `高风险操作`) had one. Half a gate internationalised is worse than none of
#: it: a spec written in the project's own declared document language found no
#: sections, matched nothing, and scanned `pass` with a fully armed union —
#: TASK-200 measured three real specs through it, one of them containing a term
#: its role card escalates on. The fix was three glossary entries, not a second
#: table here; a second translation table is the defect this repository pays
#: for most. TASK-201.
ESCALATION_TOUCHES = ("Files in scope", "Deliverable")
ESCALATION_DISCLAIMS = "Out of scope"


def scan_spec_escalations(text: str, fragments: list[str]) -> dict:
    """The dispatch pre-flight's verdict on one spec, computed rather than read.

    Step 4 was prose telling an agent to scan three sections and decide. The
    scan is deterministic and the decision has two rules, so neither belongs to
    a model reading a paragraph — the model reads `verdict`.

    `touches` is what `Files in scope` and `Deliverable` matched; `disclaims` is
    what `Out of scope` matched. A fragment in both is **green-lit**, per step
    4's own rule that an `Out of scope` hit is a green light for the line in
    question: the spec has said in writing that it does not do that. What is
    left in `refuse` is what the task touches and never disclaimed.

    `verdict` is `unarmed` when the project declared no fragments at all. That
    is deliberately not `pass`: an empty list matches nothing and would wave
    everything through, which is the one outcome a gate must not report as
    clean. Callers refuse or escalate on it exactly as `dispatch.md` says.
    """
    body = _strip_comments(text or "")
    touches: dict[str, list[str]] = {}
    for label in ESCALATION_TOUCHES:
        hits = matching_escalations(_section(body, *alias("headings", label)),
                                    fragments)
        if hits:
            touches[label] = hits
    disclaims = matching_escalations(
        _section(body, *alias("headings", ESCALATION_DISCLAIMS)), fragments)

    green = set(disclaims)
    refuse: list[str] = []
    for hits in touches.values():
        for f in hits:
            if f not in green and f not in refuse:
                refuse.append(f)

    return {
        "armed": bool(fragments),
        "touches": touches,
        "disclaims": disclaims,
        "green_lit": [f for hits in touches.values() for f in hits
                      if f in green],
        "refuse": refuse,
        "verdict": ("unarmed" if not fragments
                    else "refuse" if refuse else "pass"),
    }


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
    #: Where `.perry/` is anchored — what a `bin/` tool's `--root` takes.
    #: `state_root` is where everything in this snapshot was read from. They
    #: are the same directory unless `.perry/config.md` moved the state, and
    #: reporting one under the other's name is what TASK-159 came from.
    project_root: Path
    state_root: Path
    project_name: str
    fetched_at: datetime
    linkage: Linkage = field(default_factory=Linkage)
    ops: OpsCounts = field(default_factory=OpsCounts)
    weekly: list[JournalEntry] = field(default_factory=list)
    #: `BOARD.md` exactly as it is on disk. Kept so `board_as_authored` can be
    #: computed on demand instead of on every snapshot; nothing else reads it.
    board_text: str = ""

    @property
    def board_as_authored(self) -> BoardState:
        """The board PARSED FROM ITS MARKDOWN, for the one question that needs it.

        `board` is store-backed on an adopted project (TASK-094): its task
        rows come out of `perry/tasks.jsonl` and nothing asks a rendered
        document what a value is. **Drift asks the opposite question** — does
        the projection still agree with the record of how it got that way —
        and it cannot ask that of the store, because the store is the thing it
        is checking against. Handing it `board` reported `drift: 0` for a row
        deleted from `BOARD.md` by hand and `unrecorded: 0` for a row typed
        into it, which is the detector saying "no drift" about the two edits
        it exists to catch.

        So the parse survives, HERE, named for its one caller, rather than
        twice inside `bin/perry-task` and `bin/perry-state`. On a project with
        no store this is the same object `board` is.

        TASK-091 is where it goes: a byte comparison against what the store
        would render (`bin/perry-tasks diff` already performs it) answers the
        same question without parsing anything.
        """
        return parse_board(self.board_text)

    @property
    def open_top_risks(self) -> list[TopRisk]:
        """Risks that are still live.

        `top_risks` deliberately keeps the cleared ones — `viewer/templates/
        risks.html` shows a resolved list, and dropping them at the snapshot
        would empty a panel that is doing its job. What was wrong is that every
        COUNT read the unfiltered list, so a risk struck through on Perry's own
        board was reported as one of four live risks the day after it was
        cleared. A count of top risks that includes the cleared ones is not a
        count of anything.
        """
        return [r for r in self.top_risks if not r.resolved]

    @property
    def risks_source(self) -> str:
        """'table' | 'bullets' | 'mixed' | 'none' — how the risks were read."""
        kinds = {r.source for r in self.top_risks}
        if not kinds:
            return "none"
        return kinds.pop() if len(kinds) == 1 else "mixed"


def _resolve_project_name(root: Path, board_text: str) -> str:
    # Prefer the BOARD.md H1 suffix ("# Board — <name>"), else the root dir name.
    m = re.match(r"#\s+Board\s*[—\-–]\s*(.+)", board_text)
    if m:
        return m.group(1).strip()
    return root.name or "Perry"


def load_snapshot(root: Path = STATE_ROOT) -> PMOSnapshot:
    """The whole project state, read from `root` — which is the STATE root.

    Every caller already passed a state root: `bin/perry-state` resolves one
    before calling, and every test hands one in. What was wrong was the
    DEFAULT, which was `PROJECT_ROOT` — so a viewer launched by
    `bin/perry-viewer` against a project whose state is a subdirectory read
    `BOARD.md` from a directory that has none and rendered an empty snapshot.
    The two names now mean two things and the default is the right one of them
    (TASK-159).

    `.perry/` is still anchored at the project root, so the inverse is taken
    once here and handed down rather than re-walked by each reader that needs
    it."""
    project_root = resolve_project_root(root)

    def read(p: Path) -> str:
        return p.read_text() if p.exists() else ""

    board_text = read(root / "BOARD.md")
    okr_text = read(root / "OKR.md")
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

    # **THE RULE: once `BOARD.md § Top risks` is a table, that table is the
    # register and `PROJECT_STATE.md` is no longer merged into it.**
    #
    # Before the table existed both files held bullets, both ids were invented
    # out of prose, and a risk written into both collapsed because the invented
    # ids happened to match — the first word of each sentence. Minting real ids
    # guarantees that key can never match again, so on a migrated board the
    # merge stopped deduping anything: measured on one real project, adding a
    # single risk took the total from 13 to 15, and one risk was reported open
    # (board, `RX-004`) and cleared (`PROJECT_STATE.md`) at the same time.
    #
    # Deduping on the statement instead does not fix it — the two files phrase
    # the same risk differently, which is why the ids were doing the work — and
    # a fuzzy key would put the invention back one level down. The migration is
    # the project declaring where its risks live, so it is read as exactly
    # that. An unmigrated board is untouched: both files, deduped by id, as
    # before.
    if has_risk_table(board_text):
        top_risks = parse_top_risks(board_text)
    else:
        top_risks = parse_top_risks(board_text) + parse_top_risks(project_state_text)
    # A BULLET HAS NO ID, AND A RISK MUST NEVER BE DROPPED FOR THAT.
    #
    # This read `if key and key not in seen`, so a risk with a falsy id was
    # silently discarded. That branch was unreachable only because the bullet
    # parser invented an id out of the first word of the sentence — the very
    # invention TASK-058 removed — and the moment it stopped, "no id" became
    # "no risks at all" for every unmigrated project. The whole two-file merge
    # above went to zero.
    #
    # So the key falls back to the statement for a row that has no handle,
    # which is also what the invented id was approximating: the first word of
    # a sentence is a very coarse hash of that sentence. Prefixed, so a
    # statement can never collide with a minted `RX-001`.
    seen: set[str] = set()
    deduped: list[TopRisk] = []
    for r in top_risks:
        key = (r.id or "").lower() or \
            "stmt:" + " ".join((r.title or r.meta or "").split()).lower()
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    # **The task rows come out of the store, and the board is not asked.**
    # `load_snapshot` is the read path every tool and the viewer share, so it
    # is where ADR-007's "Python never parses a document" has to be true. A
    # project with no `tasks.jsonl` has not been adopted and is parsed, which
    # is the one caller `parse_board`'s markdown reader still has.
    board = parse_board(board_text, tasks=load_task_store(root))

    return PMOSnapshot(
        board=board,
        okr=parse_okr(okr_text, krs=load_okr_store(root)) if okr_text else OKR(),
        phase=phase,
        top_risks=deduped,
        adrs=parse_decisions(root),
        evidence=walk_evidence(root),
        journal=walk_journal(root),
        handoff=walk_handoff(root),
        design=walk_design(root, board, project_root=project_root),
        project_state=parse_project_state(project_state_text),
        arch_meta=parse_arch_meta(architecture_text),
        project_root=project_root,
        state_root=root,
        project_name=_resolve_project_name(root, board_text),
        fetched_at=datetime.now(),
        linkage=linkage,
        ops=_load_ops_counts(root),
        weekly=walk_weekly(root),
        board_text=board_text,
    )


if __name__ == "__main__":
    s = load_snapshot()
    print(f"Project root: {s.project_root}")
    print(f"State root:   {s.state_root}")
    print(f"P0={len(s.board.p0)} P1={len(s.board.p1)} P2={len(s.board.p2)}")
    print(f"Backbone groups: {len(s.board.backbone_groups)}")
    print(f"User Input Q: {len(s.board.user_input_queue)}")
    print(f"Top risks (PROJECT_STATE): {len(s.top_risks)}")
    print(f"OKR version: {s.okr.version}, objectives: {len(s.okr.objectives)}")
    print(f"Phase: {s.phase.slug if s.phase else '(none)'} #{s.phase.number if s.phase else ''}")
    if s.phase:
        print(f"  · day: {s.phase.day if s.phase.day is not None else '—'}")
        # Through the resolver, not `s.phase.krs`: TASK-157 moved the
        # phase's KRs into `phase/<NNN>-linkage.md`, so the document's
        # own list is empty on every migrated project and this smoke
        # print would report a phase with no key results.
        print(f"  · objectives: {len(s.phase.objectives)} · KRs: "
              f"{len(phase_key_results(s.phase, getattr(s, 'linkage', None)))}")
        print(f"  · scope triggers: {len(s.phase.scope_triggers)}")
        print(f"  · cost-ceiling lines: {len(s.phase.cost_ceiling_lines)}")
    print(f"ADRs: {len(s.adrs)} · Evidence: {len(s.evidence)} · Journal: {len(s.journal)}")
    print(f"Design docs: {len(s.design)}")
    for d in s.design:
        print(f"  · {d.id:<10} [{d.status:<10}] refs={d.impl_refs} {d.date or '----------'} {d.title[:50]}")
