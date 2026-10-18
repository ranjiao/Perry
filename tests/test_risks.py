"""`BOARD.md § Top risks` — the table, its writer, and the bullets it replaces.

TASK-040. Until this landed, `## Top risks` was a bullet list with no writer,
and it carried the two defects that shape always carries.

**A cleared risk stayed live forever.** The only way to retire one was
`~~strikethrough~~`, which is markdown decoration and not a field, so nothing
could act on it. On Perry's own board a risk cleared on 2026-08-16 was still
being reported as one of four live risks the next morning.

**The reader invented ids out of prose.** With no id column it split the first
sentence on whitespace and published `id: "Perry"` with
`title: "is half-adopted: …"` — a handle that names nothing, cannot be passed
back to any tool, and reads as though the project had a risk register.

Neither is fixable by writing the bullets more carefully, which is the whole
argument for a writer: an id has to be minted against the ones already issued,
and a status has to be a cell something can read.

The governing rule, and what most of this file is really checking: **the tool
owns the row and every computed cell; the agent owns the prose cell.** `ID`,
`Opened` and `Status` are the tool's. `Risk` is the human's sentence, and it is
never parsed for meaning, never enum-checked, and never rewritten.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

COVERS = (
    "bin/perry-task",
    "bin/perry-state",
    "bin/perry-lint",
    "viewer/parsers.py",
    "tests/printed_board.py",
    "perry/tasks.jsonl",
    "perry/asks.jsonl",
    "perry/risks.jsonl",
    "perry/intake.jsonl",
    ".perry/config.jsonl",
)

import subprocess
import sys
import unittest
import json
from kernel_work_support import ACTOR, ready, task
from pathlib import Path

from task_writer_support import PT, Project

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
import parsers as P  # noqa: E402


def board_with(risks_section: str, headers: str | None = None) -> str:
    """A minimal board whose `## Top risks` holds whatever is passed in."""
    h = headers or "| ID | Title | Owner | Status | Next action | Evidence |"
    sep = "|" + "|".join(["---"] * len(h.strip().strip("|").split("|"))) + "|"
    return (
        "# Board — T\n\n"
        f"## P0 (must finish this period)\n\n{h}\n{sep}\n\n"
        f"## P1\n\n{h}\n{sep}\n\n"
        f"## P2\n\n{h}\n{sep}\n\n"
        "## Top risks (one-line; full list in `PROJECT_STATE.md`)\n\n"
        f"{risks_section}\n"
    )


# The two real projects surveyed while designing the columns. Neither had
# migrated, both are quoted verbatim, and both must keep parsing.
AIMARK_BULLETS = (
    "- H · Apple developer agreement expired — notarized builds blocked\n"
    "- M · KR-O2.2 and KR-O2.3 carry zero tasks — commitments nobody is working on\n"
)
PERRY_BULLETS = (
    "- Perry is half-adopted: `.perry/config.md` exists and flips `is_adopted()`.\n"
    "- ~~`LOAD-03` (10 decisions queued on the user)~~ — cleared 2026-08-16 when "
    "DESIGN-003's 8 rows were decided.\n"
    "- DESIGN-003 phase G rewrites `SKILL.md § The hand-off contract`.\n"
)

# A table under `## Top risks` that is NOT a risk register — a severity legend,
# with the live risks still in bullets underneath it. The reader has had a test
# for this shape since the day the table landed; the writer had none, and
# `risk-add` bolted the four risk columns onto the legend and swallowed both
# bullets. One constant now, read by the reader test and by the writer tests,
# so the two can never be given different inputs for "the same" shape.
LEGEND_SECTION = (
    "| Severity | Meaning |\n"
    "|---|---|\n"
    "| H | drop everything |\n"
    "\n"
    "- H · Apple developer agreement expired\n"
    "- M · KR-O2.2 carries zero tasks\n"
)


def _project_state(p, bullets: str) -> None:
    """`PROJECT_STATE.md` holding these bullets under `## Top risks` — the one
    bullet register a project with no risks store is read from since TASK-262
    round 4b retired a held board's."""
    (p.root / "PROJECT_STATE.md").write_text(
        f"# Project state\n\n## Top risks\n\n{bullets}", encoding="utf-8")


def risks(text: str) -> list:
    return P.parse_top_risks(text)


def state(root: Path) -> dict:
    """The `perry-state --json` payload — what a consumer actually reads."""
    r = subprocess.run(
        ["python3", str(PERRY_HOME / "bin" / "perry-state"), "--root", str(root),
         "--json"], capture_output=True, text=True)
    return __import__("json").loads(r.stdout)


def lint(root: Path) -> str:
    return subprocess.run(
        ["python3", str(PERRY_HOME / "bin" / "perry-lint"), "--root", str(root)],
        capture_output=True, text=True).stdout


class TestClearedRisksStopCounting(unittest.TestCase):
    """Defect 1: strikethrough is decoration, so a cleared risk never left."""

    #: Deliberately NOT `2026-08-16`. That is the day Perry's own board
    #: happens to record, and a fixture that borrows it reads as though it
    #: were checking the real thing — which is how
    #: `test_the_risk_cleared_on_2026_08_16_no_longer_counts` got its name.
    #: Every date below is one this file wrote and only this file can move.
    DATED = (
        "| ID | Risk | Opened | Status |\n"
        "|---|---|---|---|\n"
        "| RX-001 | still a problem | 2026-01-02 | open |\n"
        "| RX-002 | was a problem | 2026-01-03 | cleared 2026-02-04 — fixed |\n"
        "| RX-003 | also a problem | 2026-01-05 | open |\n"
    )

    def test_a_cleared_row_is_not_a_live_risk(self):
        board = board_with(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n"
            "| RX-001 | still a problem | 2026-08-01 | open |\n"
            "| RX-002 | was a problem | 2026-08-01 | cleared 2026-08-16 — fixed |\n")
        parsed = risks(board)
        self.assertEqual(len(parsed), 2, "both rows must survive parsing")
        live = [r for r in parsed if not r.resolved]
        self.assertEqual([r.id for r in live], ["RX-001"])

    def test_a_cleared_row_carries_the_date_its_status_cell_states(self):
        """**Where `test_the_risk_cleared_on_2026_08_16_no_longer_counts`
        went** (TASK-404).

        That test read the live `perry/BOARD.md` and asserted the count of
        cleared risks was `1` and the date was `2026-08-16`. Neither is a fact
        about the reader: clearing a second risk, or clearing the first one a
        day later, turned it red with no line of code changed — and its NAME
        had to be edited to match. `TestPerrysOwnBoard` still asks the live
        board the part that is about this repository; the count and the date
        are exact here, where the fixture owns them.

        `cleared_on` is the field the whole row exists for — a date a consumer
        can act on, parsed out of the cell rather than out of decoration —
        and until this it was the one thing about a cleared row that only the
        live-board test asserted.
        """
        parsed = risks(board_with(self.DATED))
        self.assertEqual([r.id for r in parsed], ["RX-001", "RX-002", "RX-003"],
                         "the fixture did not parse; nothing here is checking "
                         "anything")
        self.assertEqual([r.id for r in parsed if r.resolved], ["RX-002"])
        self.assertEqual([r.cleared_on for r in parsed if r.resolved],
                         ["2026-02-04"])

    def test_an_open_row_carries_no_cleared_date(self):
        """`status_cleared_date`'s own rule, and the reason a count of cleared
        rows may not be taken from `cleared_on` being non-empty: an open risk
        has no cleared date — not today's, and not its `Opened`."""
        parsed = risks(board_with(self.DATED))
        self.assertEqual([r.cleared_on for r in parsed if not r.resolved],
                         ["", ""])

    def test_a_struck_through_bullet_is_not_a_live_risk_either(self):
        """The bullet form had the verdict all along — nothing acted on it.

        This is the exact shape that was live on Perry's board: the parser set
        `severity="resolved"`, and every count read the unfiltered list anyway.
        """
        parsed = risks(board_with(PERRY_BULLETS))
        self.assertEqual(len(parsed), 3)
        self.assertEqual(sum(1 for r in parsed if r.resolved), 1)

    def test_perry_state_reports_open_risks_only(self):
        """End to end, through the payload a consumer actually reads.

        This is the defect as it was observed: `perry-state --json` said
        `count: 4` for a board with three live risks and one struck through the
        day before. Asserted against the real payload rather than against a
        filter applied in the test, because the bug was that the payload did
        not apply one.
        """
        # The bullets are `PROJECT_STATE.md`'s (TASK-262 round 4b): a held
        # board's `## Top risks` is not read, and `PROJECT_STATE.md` is the
        # one bullet register left for a project with no risks store.
        p = Project()
        _project_state(p, PERRY_BULLETS)
        payload = state(p.root)["risks"]
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["cleared"], 1)
        self.assertNotIn("LOAD-03", payload["top"]["meta"])

    def test_the_cleared_risk_is_never_the_headline_risk(self):
        """`top` is the first OPEN risk, not the first row."""
        p = Project()
        _project_state(p, "- ~~was a problem~~ — cleared 2026-08-16\n"
                          "- still a problem\n")
        self.assertEqual(state(p.root)["risks"]["top"]["meta"], "still a problem")


class TestIdsAreMintedNotInvented(unittest.TestCase):
    """Defect 2: `id: "Perry"`, `title: "is half-adopted: …"`."""

    def test_a_table_row_reports_the_id_the_tool_minted(self):
        board = board_with(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n"
            "| RX-007 | Perry is half-adopted: `.perry/config.md` exists. | 2026-08-01 | open |\n")
        r = risks(board)[0]
        self.assertEqual(r.id, "RX-007")

    def test_the_statement_is_never_split_into_an_id_and_a_remainder(self):
        """The prose cell comes back whole.

        The bullet parser chopped `Perry is half-adopted: …` into an id and a
        title at the first space. A sentence is not a record, and the fix is a
        column rather than a better guess.
        """
        statement = "Perry is half-adopted: `.perry/config.md` exists and flips `is_adopted()`."
        board = board_with(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n"
            f"| RX-001 | {statement} | 2026-08-01 | open |\n")
        r = risks(board)[0]
        self.assertEqual(r.title, statement)
        self.assertNotEqual(r.id, "Perry")


class TestBulletsKeepParsing(unittest.TestCase):
    """Every project except Perry was on bullets the day this shipped."""

    def test_an_unmigrated_board_still_reports_its_risks(self):
        parsed = risks(board_with(AIMARK_BULLETS))
        self.assertEqual(len(parsed), 2)
        self.assertTrue(all(r.source == "bullets" for r in parsed))

    def test_the_payload_says_which_form_it_read(self):
        """A consumer must be able to tell an minted id from an invented one.

        `id` is real in a table and meaningless on a bullet, and a reader that
        cannot tell which it got will trust both equally.
        """
        self.assertEqual(risks(board_with(AIMARK_BULLETS))[0].source, "bullets")
        table = board_with(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n"
            "| RX-001 | something | 2026-08-01 | open |\n")
        self.assertEqual(risks(table)[0].source, "table")

    def test_a_table_that_is_not_a_risk_table_falls_back_to_the_bullets(self):
        """A legend under the heading must not be read as rows.

        Guessing which cell holds the sentence is the same invention this task
        removed; with no `Risk` column there is nothing to read.
        """
        parsed = risks(board_with(LEGEND_SECTION))
        self.assertEqual(len(parsed), 2)
        self.assertTrue(all(r.source == "bullets" for r in parsed))

    def test_an_empty_table_means_no_risks_not_fall_back(self):
        """Migrated-and-currently-clear is not the same as never-migrated.

        Collapsing the two would make a migrated project with zero risks
        re-parse its own prose preamble as risk bullets.
        """
        board = board_with(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n"
            "\n"
            "- this line is prose, not a risk\n")
        self.assertEqual(risks(board), [])


class TestBoardStateRisksReadsBothForms(unittest.TestCase):
    """`BoardState.risks` is the raw per-line view, and it is not dead weight
    just because nothing reads it yet — migrating the board would have left it
    returning [] forever, with no reason a future consumer could find."""

    def test_the_raw_view_sees_a_migrated_table(self):
        board = P.parse_board(board_with(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n"
            "| RX-001 | still a problem | 2026-08-01 | open |\n"
            "| RX-002 | was a problem | 2026-08-01 | cleared 2026-08-16 — fixed |\n"))
        self.assertEqual([r.text for r in board.risks],
                         ["still a problem", "was a problem"])
        self.assertEqual([r.resolved for r in board.risks], [False, True])

    def test_the_raw_view_still_sees_bullets(self):
        board = P.parse_board(board_with(AIMARK_BULLETS))
        self.assertEqual(len(board.risks), 2)


class TestColumnsResolveByName(unittest.TestCase):
    """`schema/README.md § Columns resolve by name`. Three times now."""

    def test_a_reordered_header_reads_the_same(self):
        board = board_with(
            "| Status | Opened | Risk | ID |\n"
            "|---|---|---|---|\n"
            "| open | 2026-08-01 | the statement | RX-001 |\n")
        r = risks(board)[0]
        self.assertEqual(r.id, "RX-001")
        self.assertEqual(r.title, "the statement")
        self.assertEqual(r.opened, "2026-08-01")

    def test_a_localized_header_reads_the_same(self):
        board = board_with(
            "| 编号 | 风险 | 提出 | 状态 |\n"
            "|---|---|---|---|\n"
            "| RX-001 | 一个风险 | 2026-08-01 | open |\n")
        r = risks(board)[0]
        self.assertEqual(r.id, "RX-001")
        self.assertEqual(r.title, "一个风险")
        self.assertEqual(r.opened, "2026-08-01")


class TestTheToolOwnsTheComputedCells(unittest.TestCase):


    def test_age_is_computed_from_opened_rather_than_stored(self):
        """Same rule as `Asked`/`Idle`: a stored age is stale by morning."""
        board = board_with(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n"
            "| RX-001 | a risk | 2026-08-01 | open |\n")
        r = risks(board)[0]
        self.assertEqual(r.opened, "2026-08-01")
        self.assertEqual([f.name for f in __import__("dataclasses").fields(r)
                          if f.name == "age_days"], [],
                         "age must be derived at read time, never a stored field")


class TestPerrysOwnBoard(unittest.TestCase):
    """The migration required by TASK-040, checked in place.

    Since TASK-237 3c there is no `perry/BOARD.md`; "in place" is the board
    Perry's own stores print (`tests/printed_board.py`), so what is checked is
    that the register those stores hold reads as a dated table."""

    def setUp(self):
        from printed_board import printed_board
        self.text = printed_board()

    def test_perrys_top_risks_is_a_table(self):
        parsed = risks(self.text)
        self.assertTrue(parsed)
        self.assertTrue(all(r.source == "table" for r in parsed))

    def test_every_cleared_risk_is_dated_and_no_longer_counts(self):
        """**Whatever** this board has cleared is dated and out of the live set.

        Renamed from `test_the_risk_cleared_on_2026_08_16_no_longer_counts`,
        which pinned the count (`1`) and the day (`2026-08-16`) that Perry's
        board happened to hold and had to be edited every time a risk was
        cleared — a red that meant the board had moved, not that the reader
        had broken (TASK-404).

        Quantified over the rows rather than counting them, so it is silent
        about how many there are; the exact count and the exact date live in
        `TestClearedRisksStopCounting` above, where the fixture owns both.
        A board with nothing cleared makes this vacuous, which is why the
        behaviour is asserted there and not only here.
        """
        parsed = risks(self.text)
        live = [r.id for r in parsed if not r.resolved]
        for r in parsed:
            if not r.resolved:
                continue
            with self.subTest(risk=r.id):
                self.assertRegex(
                    r.cleared_on, r"^\d{4}-\d{2}-\d{2}$",
                    f"{r.id} reads as cleared and carries no date — its "
                    f"`Status` cell is {r.status!r}")
                self.assertNotIn(
                    r.id, live,
                    f"{r.id} is cleared and is still being reported as a live "
                    f"risk — TASK-040's defect, back")

    def test_no_risk_id_is_a_word_from_the_sentence(self):
        for r in risks(self.text):
            self.assertRegex(r.id, r"^RX-\d{3}$")


class TestConversionIsAskedForNotPerformed(unittest.TestCase):
    """B-2. `perry/OKR.md:37` — "No automatic rewrite of a project's existing
    structure. Adoption proposes; the user declares." `risk-add` used to
    convert the whole section on the way past: 9 bullets on a copy of a real
    board became 9 rows, exit 0, and the human-readable line said only
    `wrote RX-010 (risk-add)`.

    **Four refusal tests left with TASK-262 round 4a.** `risk-add` asked
    before converting a held bullet section — refused, counted the lines,
    printed `risk-migrate`, minted nothing. A write now builds from the risks
    store and never reads the held file, so there is nothing for it to convert
    and nothing to ask: the first test below asserts what happens instead. The
    conversion is still only ever asked for, by `risk-migrate`."""


    def test_risk_migrate_is_a_section_event_not_a_task_event(self):
        """`tests/test_cadence.py` asserts the two sets partition `COMMANDS`;
        this asserts which side of the partition this one is on. A risk row is
        not a task row, and `perry-task list` folds `TASK_EVENTS` only."""
        self.assertIn("risk-migrate", PT.SECTION_EVENTS)
        self.assertNotIn("risk-migrate", PT.TASK_EVENTS)


class TestOneRegisterNotTwo(unittest.TestCase):
    """M-1. What happens when a project keeps risks in both files.

    **The rule: once `BOARD.md § Top risks` is a table, that table is the
    register and `PROJECT_STATE.md` is no longer merged into it.**

    Both files used to hold bullets, both ids were invented out of the prose,
    and a risk written into both collapsed because the invented ids matched —
    the first word of each sentence. Minting real ids guarantees that key can
    never match again, so the merge silently stopped deduping: on one real
    project adding a single risk took the total from 13 to 15, and one risk was
    reported open (board) and cleared (`PROJECT_STATE.md`) at the same time.
    """

    STATE = (
        "# Project state\n\n"
        "## Top risks\n\n"
        "- GAVI — ~~the vendor contract lapses~~ cleared 2026-08-10\n"
        "- LEDGER — reconciliation is manual\n")

    def snapshot(self, p: Project):
        (p.root / "PROJECT_STATE.md").write_text(self.STATE)
        return P.load_snapshot(p.root)

    # **TASK-262 round 4b: the declaration is the store, not a held table.**
    # A held `BOARD.md` is retired and its `## Top risks` is not read, so a
    # migrated table reaches the reader through `risks-write --from-board`
    # (`_imported`), and "migrated" means a `risks.jsonl` exists — which is
    # what TASK-237 3a already made the rule.

    def _imported(self, section: str) -> Project:
        p = Project(board=board_with(section))
        from held_board import import_board
        import_board(p.root, "risks-write", remove=False)
        return p

    def test_a_migrated_board_is_the_whole_register(self):
        p = self._imported(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n"
            "| RX-001 | GAVI — the vendor contract lapses | 2026-08-01 | open |\n")
        snap = self.snapshot(p)
        self.assertEqual([r.id for r in snap.top_risks], ["RX-001"])
        self.assertEqual(snap.risks_source, "table")

    def test_no_risk_is_reported_open_and_cleared_at_the_same_time(self):
        """The measured symptom, asserted as the property it violates."""
        p = self._imported(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n"
            "| RX-001 | GAVI — the vendor contract lapses | 2026-08-01 | open |\n")
        snap = self.snapshot(p)
        gavi = [r for r in snap.top_risks if "GAVI" in r.meta]
        self.assertEqual(len(gavi), 1)
        self.assertEqual([r.resolved for r in gavi], [False])


    def test_an_unmigrated_board_is_not_merged_and_project_state_is(self):
        """**Rewritten at TASK-262 round 4b.** This was
        `test_an_unmigrated_board_still_merges_both_files`: a held board's
        bullets were merged with `PROJECT_STATE.md`'s. The held board is
        retired, so with no risks store the one file read is
        `PROJECT_STATE.md` — the board's bullet reaches nothing until it is
        migrated (`perry-task risk-migrate`, the import for bullets)."""
        p = Project(board=board_with("- ONLY-ON-THE-BOARD — a third thing\n"))
        metas = " ".join(r.meta for r in self.snapshot(p).top_risks)
        self.assertNotIn("ONLY-ON-THE-BOARD", metas)
        self.assertIn("LEDGER", metas)

    def test_an_empty_migrated_table_is_still_a_migrated_board(self):
        """Migrated-and-currently-clear must not read as never-migrated, or the
        rule would switch itself off the moment the last risk is cleared. The
        empty table's import writes an empty `risks.jsonl` — the declaration —
        and `PROJECT_STATE.md`'s bullets stay out."""
        p = self._imported(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n")
        self.assertTrue((p.root / "risks.jsonl").exists(),
                        "the empty table's import wrote no store")
        self.assertEqual(self.snapshot(p).top_risks, [])


class TestOneRuleForWhatABulletIs(unittest.TestCase):
    """m-1 and m-2 — the same "three implementations of one rule" shape as B-1.

    `viewer/parsers.py` matched `- ` in one reader and `- ` or `1. ` in the
    other, so a numbered list read as 0 risks through one and 2 through the
    other. And only the writer knew what a placeholder was, so the reader
    turned `BOARD_TEMPLATE.md`'s own `- (no active risks)` into a risk with
    `id='(no'` — an id split out of prose at the first space.
    """

    NUMBERED = ("1. the vendor contract lapses\n"
                "2. reconciliation is manual\n")

    def test_a_numbered_list_reads_the_same_through_both_readers(self):
        board = board_with(self.NUMBERED)
        self.assertEqual(len(risks(board)), 2)
        self.assertEqual(len(P.parse_board(board).risks), 2)


    def test_the_placeholder_the_template_ships_is_not_a_risk(self):
        self.assertEqual(risks(board_with("- (no active risks)\n")), [])
        self.assertEqual(P.parse_board(board_with("- none\n")).risks, [])

    def test_the_placeholder_is_never_an_id_split_out_of_prose(self):
        for line in ("- (no active risks)\n", "- none\n", "- 暂无\n", "- —\n"):
            self.assertEqual(risks(board_with(line)), [], line)

    def test_the_reader_and_the_writer_agree_on_every_placeholder(self):
        """Two copies of one rule, checked to be one rule. They live in
        different files because `bin/perry-task` is a script and
        `viewer/parsers.py` is a module; nothing enforces that but this."""
        corpus = ["(no active risks)", "no active risk", "none", "N/A", "na",
                  "TBD", "—", "-", "–", "无", "暂无", "None.",
                  "a real risk", "no active risks are pending — except one",
                  "nonetheless the vendor lapsed"]
        self.assertEqual(
            [bool(P._RE_RISK_PLACEHOLDER.match(s)) for s in corpus],
            [bool(PT._RISK_PLACEHOLDER.match(s)) for s in corpus])

    def test_the_reader_and_the_writer_agree_on_every_bullet_form(self):
        corpus = ["- a risk", "1. a risk", "10. a risk", "-a risk",
                  "* a risk", "  - a risk", "a risk", "-", "- "]
        self.assertEqual(
            [bool(P._RE_RISK_BULLET.match(s.strip())) for s in corpus],
            [bool(PT._RISK_BULLET.match(s.strip())) for s in corpus])


class TestOneNormalizationForAHeaderCell(unittest.TestCase):
    """TASK-050. The same "one rule, two implementations" shape as above, one
    level down: what a *header cell* normalizes to before a column is resolved.

    `viewer/parsers.py` spelled it `.strip().lower()` at eleven sites;
    `bin/perry-task`, `bin/perry-goals` and `bin/perry-lint` spelled it
    `squash`, which also takes off markdown decoration. So on

        | ID | **Risk** | Opened | Status |

    the writer squashed `**Risk**` to `risk` and said "risk table", and the
    reader lowered it to `**risk**` and said "not a risk table". Every exit a
    user could reach was closed by that one disagreement: `risk-add` wrote the
    row, `perry-state` reported zero risks, `perry-lint` reported the board
    clean, and `risk-migrate` said it had already migrated. The board was
    fine; nothing would show it.

    The task tables survived only because every column there has a positional
    fallback — which is to say a decorated header was being read by position,
    the thing `_parse_task_table`'s own comment says must never happen.

    These are the CATEGORY tests. `test_..._on_every_written_header_cell`
    compares the two predicates over a corpus of forms rather than checking one
    behaviour on one fixture, because a fixture only ever covers the decoration
    someone happened to think of.
    """

    # Every way a person writes a header cell, crossed with every column that
    # has a reader and a writer. Decoration, case, padding, both languages,
    # plus near-misses that must resolve to nothing on BOTH sides.
    DECORATIONS = ("{}", "**{}**", "`{}`", "*{}*", "  {}  ", "**`{}`**",
                   "{} ", "__{}__")
    COLUMNS = ("ID", "Title", "Owner", "Status", "Next action", "Evidence",
               "Verification", "Risk", "Opened", "USER-id")
    NEAR_MISSES = ("Risks", "Risk level", "Severity", "risk ", "  ", "",
                   "**Meaning**", "`Note`", "IDs", "编号x")

    def _corpus(self) -> list[str]:
        cells: list[str] = []
        for col in self.COLUMNS:
            for lang_spelling in P.alias("columns", col):
                for deco in self.DECORATIONS:
                    cells.append(deco.format(lang_spelling))
                    cells.append(deco.format(lang_spelling.upper()))
                    cells.append(deco.format(lang_spelling.lower()))
        cells.extend(self.NEAR_MISSES)
        return cells

    def test_the_reader_and_the_writer_normalize_with_the_same_function(self):
        """Not "two functions that agree today" — one function, imported by
        both. The corpus tests below would keep passing if someone reinlined a
        copy that happens to agree; this is what stops the copy."""
        self.assertIs(P.squash, PT.squash)

    def test_the_reader_and_the_writer_resolve_every_written_header_cell_alike(self):
        """The reader asks "is this cell one of this column's spellings?" by
        membership in a glossary-built key set; the writer asks it by mapping
        the cell through an alias table. Two implementations, one rule — and
        nothing but this asserts they are the same rule."""
        corpus = self._corpus()
        for canonical in self.COLUMNS:
            reader = [P.squash(c) in P._column_keys(canonical) for c in corpus]
            writer = [PT.norm(c) == PT.norm(canonical) for c in corpus]
            disagreements = [c for c, r, w in zip(corpus, reader, writer)
                             if r != w]
            self.assertEqual(disagreements, [], f"column {canonical!r}")

    def test_the_reader_and_the_writer_agree_on_every_risk_header_form(self):
        """The predicate the four closed exits actually hung on: the reader's
        `_has_risk_header` against the writer's `is_risk_header`, over headers
        rather than over cells."""
        headers = [
            ["ID", "Risk", "Opened", "Status"],
            ["ID", "**Risk**", "Opened", "Status"],
            ["ID", "`Risk`", "Opened", "Status"],
            ["**ID**", "**Risk**", "**Opened**", "**Status**"],
            ["Status", "Opened", "*Risk*", "ID"],
            ["编号", "风险", "提出", "状态"],
            ["编号", "**风险**", "提出", "状态"],
            ["ID", "RISK", "Opened", "Status"],
            ["Severity", "Meaning"],
            ["**Severity**", "**Meaning**"],
            ["ID", "Risks", "Opened"],
            ["ID", "Title", "Owner", "Status"],
        ]
        reader = [P._has_risk_header(self._section(h)) for h in headers]
        writer = [PT.is_risk_header(h) for h in headers]
        self.assertEqual(reader, writer,
                         [h for h, r, w in zip(headers, reader, writer) if r != w])

    @staticmethod
    def _section(header: list[str]) -> str:
        sep = "|" + "|".join(["---"] * len(header)) + "|"
        return "| " + " | ".join(header) + " |\n" + sep + "\n"

    # ── and the four exits, on the header the finding was found on ─────────

    BOLD_HEADER = ("| ID | **Risk** | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-001 | the vendor contract lapses | 2026-08-01 | open |\n")

    def test_the_reader_sees_the_row_the_writer_wrote(self):
        self.assertEqual([r.id for r in risks(board_with(self.BOLD_HEADER))],
                         ["RX-001"])

    def test_perry_state_counts_a_risk_under_a_decorated_header(self):
        """Exit one. It reported 0 while the risk sat in the file."""
        p = Project(board=board_with(self.BOLD_HEADER))
        # Through the import (TASK-262 round 4b): the decorated header has to
        # be read by `risks-write --from-board`, and the store by `perry-state`.
        from held_board import import_board
        import_board(p.root, "risks-write", remove=False)
        self.assertEqual(state(p.root)["risks"]["count"], 1)
        self.assertEqual(state(p.root)["risks"]["source"], "table")


    # ── the task table, which was surviving on its positional fallbacks ────

    def test_a_decorated_task_header_resolves_by_name_not_by_position(self):
        """`_parse_task_table` falls back to the canonical position for any
        header cell it cannot resolve, so a decorated header parsed *correctly*
        only while the columns stayed in canonical order. Reorder them and the
        fallback reads the wrong cell — owner from the track column, and so on.
        """
        board = board_with(
            "- none\n",
            headers="| **ID** | **Title** | **Track** | **Owner** | "
                    "**Status** | **Next action** | **Evidence** |")
        rows = ("| TASK-001 | a title | web | Coding Agent | in_progress | "
                "do the thing | — |")
        board = board.replace(
            "## P1", rows + "\n\n## P1", 1)
        tasks = P.parse_board(board).all_tasks
        self.assertEqual(len(tasks), 1, board)
        self.assertEqual(tasks[0].owner, "Coding Agent")
        self.assertEqual(tasks[0].status, "in_progress")
        self.assertEqual(tasks[0].next_action, "do the thing")

    def test_a_decorated_header_row_is_never_read_as_a_row(self):
        """The other half of resolving the id column by name: `| **ID** | … |`
        under a second separator would otherwise mint a task called `**ID**`."""
        board = board_with("- none\n")
        board = board.replace(
            "## P1",
            "| **ID** | **Title** | **Owner** | **Status** | **Next action** | "
            "**Evidence** |\n\n## P1", 1)
        self.assertEqual(P.parse_board(board).all_tasks, [])


class TestNativeRiskLifecycle(unittest.TestCase):
    def test_create_clear_and_fresh_risk_retain_distinct_ids(self):
        sb = ready(self)
        tid = task(sb)
        risk = sb.create("risk", fields={"concern": "供应商中断 | 风险"})
        self.assertEqual((tid, risk), ("TASK-001", "RX-001"))
        sb.move(risk, "clear", set={"reason": "verified recovery"})
        fresh = sb.create("risk", fields={"concern": "another concern"})
        self.assertEqual(fresh, "RX-002")
        self.assertEqual(sb.get(risk)["state"], "cleared")
        self.assertEqual(sb.get(risk)["fields"]["concern"], "供应商中断 | 风险")
        self.assertEqual(sb.get(risk)["fields"]["reason"], "verified recovery")
        self.assertEqual(sb.ok("query", data={"type": "risk"})["total"], 2)
        self.assertEqual(sb.ok("query", data={"type": "task"})["total"], 1)

    def test_concern_and_clear_reason_are_required_without_partial_effects(self):
        sb = ready(self)
        before = sb.seq()
        for concern in (None, "", "   "):
            fields = {} if concern is None else {"concern": concern}
            out = sb.run("item create", data={"actor": ACTOR, "type": "risk", "fields": fields})
            self.assertFalse(out.ok, out)
            self.assertEqual(sb.seq(), before)
        rid = sb.create("risk", fields={"concern": "a real concern"})
        before = sb.seq()
        for fields in ({}, {"reason": ""}):
            out = sb.run("item move", data={"actor": ACTOR, "id": rid,
                                            "transition": "clear", "set": fields})
            self.assertFalse(out.ok, out)
            self.assertEqual(sb.seq(), before)
            self.assertEqual(sb.get(rid)["state"], "open")

    def test_a_second_clear_refuses_and_preserves_the_first_reason(self):
        sb = ready(self)
        rid = sb.create("risk", fields={"concern": "a concern"})
        sb.move(rid, "clear", set={"reason": "first verified reason"})
        before = sb.seq()
        out = sb.run("item move", data={"actor": ACTOR, "id": rid,
            "transition": "clear", "set": {"reason": "replacement"}})
        self.assertEqual(out.code_name, "transition_not_allowed", out)
        self.assertEqual(sb.seq(), before)
        self.assertEqual(sb.get(rid)["fields"]["reason"], "first verified reason")

    def test_retired_risk_commands_preserve_bullets_tables_legends_and_placeholders(self):
        for section in (AIMARK_BULLETS, LEGEND_SECTION, "- none\n",
                        "| ID | Risk | Opened | Status |\n|---|---|---|---|\n"
                        "| RX-001 | old risk | 2026-01-01 | open |\n"):
            p = Project(board=board_with(section))
            before = {str(f.relative_to(p.root)): f.read_bytes()
                      for f in p.root.rglob("*") if f.is_file()}
            for argv in (("risk-add", "--title", "new risk"), ("risk-migrate",),
                         ("risk-clear", "RX-001", "--reason", "handled"), ("risk-migrate", "--dry-run")):
                code, out = p.run(*argv)
                self.assertEqual(code, 1, out)
                self.assertIn("read-only", out["refused"])
                self.assertEqual({str(f.relative_to(p.root)): f.read_bytes()
                                  for f in p.root.rglob("*") if f.is_file()}, before)


class TestRetainedRiskConversionUnits(unittest.TestCase):
    """The dormant pure conversion helper is checked without a public write."""
    def test_conversion_preserves_bullets_verdicts_and_missing_dates(self):
        for section in (AIMARK_BULLETS, PERRY_BULLETS,
                        "1. the vendor contract lapses\n2. reconciliation is manual\n"):
            p = Project(board=board_with(section))
            held = p.held_board()
            before = risks(held)
            board = PT.Board(p.root / "BOARD.md")
            migrated = PT.ensure_risk_table(board, [], p.root)
            after = risks("\n".join(board.lines))
            self.assertEqual(len(migrated), len(before))
            self.assertEqual([r.meta for r in after], [r.meta for r in before])
            self.assertEqual([r.resolved for r in after], [r.resolved for r in before])
            self.assertTrue(all(r.source == "table" for r in after))
            self.assertTrue(all(not r.opened for r in after))
            self.assertEqual(p.held_board(), held)

    def test_cleared_date_and_placeholders_are_preserved_by_conversion(self):
        p = Project(board=board_with(PERRY_BULLETS))
        migrated = PT.ensure_risk_table(PT.Board(p.root / "BOARD.md"), [], p.root)
        self.assertEqual([r["status"] for r in migrated if r["status"].startswith("cleared")],
                         ["cleared 2026-08-16"])
        for placeholder in ("- (no active risks)\n", "- none\n", "- 暂无\n"):
            p = Project(board=board_with(placeholder))
            self.assertEqual(PT.ensure_risk_table(PT.Board(p.root / "BOARD.md"), [], p.root), [])

    def test_archived_risks_asks_and_section_events_never_become_tasks(self):
        p = Project()
        (p.root / "risks.jsonl").write_text(json.dumps({"id": "RX-001", "risk": "a risk",
            "status": "open", "order": 0}) + "\n")
        (p.root / "asks.jsonl").write_text(json.dumps({"id": "USER-001", "needed": "Which?",
            "status": "pending", "order": 0}) + "\n")
        (p.root / ".perry/events.jsonl").write_text("".join(json.dumps({
            "event": name, "id": item, "ts": "2026-08-01T00:00:00Z"}) + "\n"
            for name, item in (("risk-add", "RX-001"), ("ask", "USER-001"))))
        code, out = p.run("list", "--all")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["tasks"], [])
        self.assertEqual(out["untitled"], [])
        self.assertEqual(out["risks"]["open"], 1)
        self.assertEqual(out["asks"]["open"], 1)

    def test_foreign_legend_refuses_without_mutating_the_in_memory_board(self):
        p = Project(board=board_with(LEGEND_SECTION))
        board = PT.Board(p.root / "BOARD.md")
        before = list(board.lines)
        with self.assertRaises(PT.Refused):
            PT.ensure_risk_table(board, [], p.root)
        self.assertEqual(board.lines, before)


if __name__ == "__main__":
    unittest.main()
