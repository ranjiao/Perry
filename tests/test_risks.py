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

import subprocess
import sys
import unittest
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
        p = Project(board=board_with(PERRY_BULLETS))
        payload = state(p.root)["risks"]
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["cleared"], 1)
        self.assertNotIn("LOAD-03", payload["top"]["meta"])

    def test_the_cleared_risk_is_never_the_headline_risk(self):
        """`top` is the first OPEN risk, not the first row."""
        p = Project(board=board_with(
            "- ~~was a problem~~ — cleared 2026-08-16\n"
            "- still a problem\n"))
        self.assertEqual(state(p.root)["risks"]["top"]["meta"], "still a problem")

    def test_cleared_rows_stay_on_the_board(self):
        """They stop counting; they do not disappear.

        A risk that was real and is now over is the record that the mitigation
        worked. Deleting it would leave the same hole the strikethrough was
        trying to fill.
        """
        p = Project(board=board_with(PERRY_BULLETS))
        self.assertEqual(p.run("risk-migrate")[0], 0)
        p.run("risk-add", "--title", "new one")
        code, out = p.run("risk-clear", "RX-001", "--reason", "adoption finished")
        self.assertEqual(code, 0, out)
        self.assertIn("RX-001", p.board())
        self.assertIn("cleared", p.board())


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

    def test_ids_are_not_reissued_after_a_risk_is_cleared(self):
        """A cleared risk still owns its number."""
        p = Project(board=board_with("- none\n"))
        p.run("risk-add", "--title", "one")
        p.run("risk-clear", "RX-001", "--reason", "done")
        code, out = p.run("risk-add", "--title", "two")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["id"], "RX-002")


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

    def test_a_new_column_joins_a_localized_table_in_its_own_language(self):
        p = Project(board=board_with(
            "- 一个风险\n",
            headers="| 编号 | 标题 | 负责人 | 状态 | 下一步 | 证据 |"))
        self.assertEqual(p.run("risk-migrate")[0], 0)
        self.assertIn("| 编号 | 风险 | 提出 | 状态 |", p.board())
        code, out = p.run("risk-add", "--title", "另一个风险")
        self.assertEqual(code, 0, out)
        self.assertEqual([r.title for r in risks(p.board())],
                         ["一个风险", "另一个风险"])


class TestMigrationLosesNothing(unittest.TestCase):
    """`risk-add` converts a bullet list in the same write."""

    def test_every_bullet_survives_verbatim(self):
        """The statement is the human's and this tool has no opinion about it.

        Checked against the two real boards' actual text — bold, emoji, inline
        links, Chinese, backticks.
        """
        p = Project(board=board_with(AIMARK_BULLETS))
        code, out = p.run("risk-migrate")
        self.assertEqual(code, 0, out)
        migrated = [m["risk"] for m in out["migrated"]]
        self.assertEqual(migrated, [
            "H · Apple developer agreement expired — notarized builds blocked",
            "M · KR-O2.2 and KR-O2.3 carry zero tasks — commitments nobody is working on",
        ])

    def test_migration_preserves_every_verdict(self):
        """The property, not a sample: the set of (statement, resolved) pairs
        is identical either side of the conversion.

        `Status` is derived from the reader's OWN two markers — `~~strike~~`
        and `**RESOLVED` — and nothing else, so a bullet the old parser called
        resolved becomes a row the new parser calls cleared. That makes the
        conversion checkable rather than a claim a reviewer has to believe.
        """
        before = risks(board_with(PERRY_BULLETS))
        p = Project(board=board_with(PERRY_BULLETS))
        code, out = p.run("risk-migrate")
        # Asserted, because without it this test passes on a tool that refuses
        # to migrate at all: an unconverted board is trivially identical to
        # itself, and the property under test is about the conversion.
        self.assertEqual(code, 0, out)
        after = risks(p.board())
        self.assertTrue(all(r.source == "table" for r in after), "did not convert")
        self.assertEqual([r.meta for r in before], [r.meta for r in after])
        self.assertEqual([r.resolved for r in before], [r.resolved for r in after])

    def test_migration_does_not_invent_an_opened_date(self):
        """A pre-existing risk's open date is not recorded anywhere.

        Stamping today would assert that a nine-month-old risk is new. Empty
        reads back as `age_days: null`, which is the honest answer.
        """
        p = Project(board=board_with(PERRY_BULLETS))
        code, out = p.run("risk-migrate")
        self.assertEqual(code, 0, out)
        migrated = risks(p.board())
        self.assertEqual(len(migrated), 3)
        self.assertTrue(all(r.opened == "" for r in migrated),
                        [r.opened for r in migrated])

    def test_a_struck_through_bullet_carries_its_stated_date_across(self):
        p = Project(board=board_with(PERRY_BULLETS))
        code, out = p.run("risk-migrate")
        self.assertEqual(code, 0, out)
        cleared = [m for m in out["migrated"] if m["status"].startswith("cleared")]
        self.assertEqual(len(cleared), 1)
        self.assertEqual(cleared[0]["status"], "cleared 2026-08-16")

    def test_a_placeholder_bullet_is_not_migrated_into_a_risk(self):
        """`BOARD_TEMPLATE.md` ships `- (no active risks)`."""
        p = Project(board=board_with("- (no active risks)\n"))
        code, out = p.run("risk-add", "--title", "the first real one")
        self.assertEqual(code, 0, out)
        self.assertEqual([r.title for r in risks(p.board())],
                         ["the first real one"])
        self.assertNotIn("no active risks", p.board())


class TestTheToolOwnsTheComputedCells(unittest.TestCase):

    def test_risk_add_stamps_opened_and_mints_the_id(self):
        p = Project(board=board_with("- none\n"))
        code, out = p.run("risk-add", "--title", "a risk")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["id"], "RX-001")
        self.assertRegex(out["opened"], r"^\d{4}-\d{2}-\d{2}$")

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

    def test_every_write_is_board_journal_and_event(self):
        p = Project(board=board_with("- none\n"))
        p.run("risk-add", "--title", "a risk")
        self.assertIn("RX-001", p.board())
        self.assertIn("RX-001", p.journal())
        self.assertEqual([e["event"] for e in p.events()], ["risk-add"])
        p.run("risk-clear", "RX-001", "--reason", "mitigated")
        self.assertIn("open → cleared", p.journal())
        self.assertEqual([e["event"] for e in p.events()],
                         ["risk-add", "risk-clear"])

    def test_risk_clear_refuses_without_a_reason(self):
        p = Project(board=board_with("- none\n"))
        p.run("risk-add", "--title", "a risk")
        code, out = p.run("risk-clear", "RX-001")
        self.assertEqual(code, 1)
        self.assertIn("--reason", out["refused"])

    def test_risk_clear_refuses_a_risk_that_is_already_cleared(self):
        p = Project(board=board_with("- none\n"))
        p.run("risk-add", "--title", "a risk")
        p.run("risk-clear", "RX-001", "--reason", "first")
        code, out = p.run("risk-clear", "RX-001", "--reason", "second")
        self.assertEqual(code, 1)
        self.assertIn("already cleared", out["refused"])

    def test_risk_clear_on_an_unmigrated_board_says_what_to_do(self):
        p = Project(board=board_with(AIMARK_BULLETS))
        code, out = p.run("risk-clear", "RX-001", "--reason", "x")
        self.assertEqual(code, 1)
        self.assertIn("risk-migrate", out["refused"])

    def test_risk_add_refuses_without_a_statement(self):
        p = Project(board=board_with("- none\n"))
        code, out = p.run("risk-add")
        self.assertEqual(code, 1)
        self.assertIn("--title", out["refused"])


class TestRiskRowsAreNotTaskRows(unittest.TestCase):

    def test_list_does_not_pick_up_risks_as_tasks(self):
        """`## Top risks` is in `NON_TASK_SECTIONS` — and now it has a table
        with an `ID` column, which is exactly what `task_tables()` looks for."""
        p = Project(board=board_with("- none\n"))
        p.run("risk-add", "--title", "a risk")
        code, out = p.run("list", "--all")
        self.assertEqual(code, 0, out)
        self.assertNotIn("RX-001", [t["id"] for t in out["tasks"]])

    def test_the_event_log_does_not_turn_questions_into_tasks(self):
        """Found by the test above, and it predates risks.

        `cmd_list` absorbed every event carrying an id, and `ask` has carried
        one since TASK-039 — so on a project with a single `ask` and no tasks
        at all, `list --all` returned one task: `USER-001`, untitled, with
        `open: false`. `risk-add` would have widened the same hole to `RX-*`.
        """
        p = Project(board=board_with("- none\n"))
        p.run("ask", "--needed", "a question")
        p.run("risk-add", "--title", "a risk")
        code, out = p.run("list", "--all")
        self.assertEqual(code, 0, out)
        self.assertEqual([t["id"] for t in out["tasks"]], [])

    def test_a_risk_id_never_collides_with_a_task_id(self):
        p = Project(board=board_with("- none\n"))
        p.run("risk-add", "--title", "a risk")
        code, out = p.run("add", "--title", "a task")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["id"], "TASK-001")


class TestLintToleratesBothForms(unittest.TestCase):
    """Reading is tolerant; writing is strict. The rule that cost 61 -> 67
    lint errors on a live project the last time it was broken."""

    def test_a_board_that_never_migrated_is_not_reported_missing_a_table(self):
        p = Project(board=board_with(AIMARK_BULLETS))
        out = lint(p.root)
        self.assertNotIn("missing-table", out, out)

    def test_a_migrated_board_passes_the_column_check(self):
        p = Project(board=board_with("- none\n"))
        p.run("risk-add", "--title", "a risk")
        out = lint(p.root)
        self.assertNotIn("table-columns", out, out)

    def test_status_is_not_enum_checked(self):
        """It holds a human's reason. An enum here is the reverted mistake."""
        p = Project(board=board_with(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n"
            "| RX-001 | a risk | 2026-08-01 | 已解除 2026-08-16 — 上游修好了 |\n"))
        out = lint(p.root)
        self.assertNotIn("bad-enum", out, out)


class TestPerrysOwnBoard(unittest.TestCase):
    """The migration required by TASK-040, checked in place."""

    def setUp(self):
        self.text = (PERRY_HOME / "perry" / "BOARD.md").read_text()

    def test_perrys_top_risks_is_a_table(self):
        parsed = risks(self.text)
        self.assertTrue(parsed)
        self.assertTrue(all(r.source == "table" for r in parsed))

    def test_the_risk_cleared_on_2026_08_16_no_longer_counts(self):
        parsed = risks(self.text)
        cleared = [r for r in parsed if r.resolved]
        self.assertEqual(len(cleared), 1)
        self.assertEqual(cleared[0].cleared_on, "2026-08-16")
        self.assertNotIn(cleared[0].id, [r.id for r in parsed if not r.resolved])

    def test_no_risk_id_is_a_word_from_the_sentence(self):
        for r in risks(self.text):
            self.assertRegex(r.id, r"^RX-\d{3}$")


class TestTheWriterAsksTheReadersQuestion(unittest.TestCase):
    """B-1. Two implementations of "is this section already a table?".

    The reader asked `_has_risk_header` — a table with a `Risk` column. The
    writer asked `section_table()` — **any** table. On a severity legend they
    disagreed, and the writer took the already-a-table branch: it bolted the
    four risk columns onto the legend, appended the new row into it, and left
    the live bullets below, where the reader could no longer see them because
    the legend now had a `Risk` header. Count 2 → 1, exit 0, no warning.

    These are the writer twins of `TestBulletsKeepParsing`, on the reader's own
    fixture — the systematic gap the V4 review named: every writer test started
    from a bullet list or an empty section, so the branch that destroyed data
    was the one branch nothing exercised.
    """

    def test_risk_add_refuses_a_table_that_is_not_a_risk_table(self):
        p = Project(board=board_with(LEGEND_SECTION))
        before = p.board()
        code, out = p.run("risk-add", "--title", "a new risk")
        self.assertEqual(code, 1, out)
        self.assertIn("no `Risk` column", out["refused"])
        self.assertEqual(p.board(), before, "the board was written to anyway")

    def test_the_bullets_under_a_legend_are_still_there_afterwards(self):
        """The failure was silent loss, so this asserts on the count."""
        p = Project(board=board_with(LEGEND_SECTION))
        p.run("risk-add", "--title", "a new risk")
        parsed = risks(p.board())
        self.assertEqual(len(parsed), 2)
        self.assertIn("Apple developer agreement expired", parsed[0].meta)

    def test_no_risk_column_is_ever_added_to_a_legend(self):
        p = Project(board=board_with(LEGEND_SECTION))
        p.run("risk-add", "--title", "a new risk")
        self.assertIn("| Severity | Meaning |", p.board())
        self.assertNotIn("| Severity | Meaning | ID | Risk |", p.board())

    def test_risk_migrate_refuses_it_too(self):
        """Consent does not make an unwritable shape writable."""
        p = Project(board=board_with(LEGEND_SECTION))
        before = p.board()
        code, out = p.run("risk-migrate")
        self.assertEqual(code, 1, out)
        self.assertIn("no `Risk` column", out["refused"])
        self.assertEqual(p.board(), before)

    def test_a_second_table_in_the_section_is_refused(self):
        """`section_table` addresses the first table and `section_rows` reads
        straight through a blank line into the next one, so a row appended to a
        section holding two tables lands in whichever one the scan reached."""
        p = Project(board=board_with(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n"
            "| RX-001 | a real risk | 2026-08-01 | open |\n"
            "\n"
            "| Severity | Meaning |\n"
            "|---|---|\n"
            "| H | drop everything |\n"))
        before = p.board()
        code, out = p.run("risk-add", "--title", "another")
        self.assertEqual(code, 1, out)
        self.assertIn("more than one table", out["refused"])
        self.assertEqual(p.board(), before)


class TestConversionIsAskedForNotPerformed(unittest.TestCase):
    """B-2. `perry/OKR.md:37` — "No automatic rewrite of a project's existing
    structure. Adoption proposes; the user declares." `risk-add` used to
    convert the whole section on the way past: 9 bullets on a copy of a real
    board became 9 rows, exit 0, and the human-readable line said only
    `wrote RX-010 (risk-add)`."""

    def test_risk_add_refuses_to_convert_a_section_it_did_not_write(self):
        p = Project(board=board_with(PERRY_BULLETS))
        before = p.board()
        code, out = p.run("risk-add", "--title", "a new risk")
        self.assertEqual(code, 1, out)
        self.assertEqual(p.board(), before)

    def test_the_refusal_counts_the_lines_it_would_rewrite(self):
        """A refusal that does not say how much is at stake is not a question."""
        p = Project(board=board_with(PERRY_BULLETS))
        _, out = p.run("risk-add", "--title", "a new risk")
        self.assertIn("3 risk(s)", out["refused"])

    def test_the_refusal_prints_the_command_that_does_it(self):
        p = Project(board=board_with(AIMARK_BULLETS))
        _, out = p.run("risk-add", "--title", "a new risk")
        self.assertIn("perry-task risk-migrate", out["refused"])
        # And the command it prints is one the tool actually has.
        self.assertIn("risk-migrate", PT.COMMANDS)

    def test_nothing_is_minted_by_a_refused_risk_add(self):
        """A refusal that has already burned RX-001 is not a refusal."""
        p = Project(board=board_with(AIMARK_BULLETS))
        p.run("risk-add", "--title", "a new risk")
        self.assertEqual(p.events(), [])
        self.assertEqual(p.journal(), "")
        p.run("risk-migrate")
        code, out = p.run("risk-add", "--title", "a new risk")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["id"], "RX-003")

    def test_an_empty_section_is_not_asked_about(self):
        """There is no consent to collect for a section holding nothing of the
        user's — the thing being protected is their own writing."""
        p = Project(board=board_with("- none\n"))
        code, out = p.run("risk-add", "--title", "the first one")
        self.assertEqual(code, 0, out)

    def test_risk_migrate_refuses_a_board_that_has_already_migrated(self):
        p = Project(board=board_with("- none\n"))
        p.run("risk-add", "--title", "a risk")
        before = p.board()
        code, out = p.run("risk-migrate")
        self.assertEqual(code, 1, out)
        self.assertIn("already a table", out["refused"])
        self.assertEqual(p.board(), before)

    def test_risk_migrate_refuses_when_there_is_nothing_to_convert(self):
        p = Project(board=board_with("- (no active risks)\n"))
        code, out = p.run("risk-migrate")
        self.assertEqual(code, 1, out)
        self.assertIn("no risk bullets", out["refused"])

    def test_dry_run_shows_every_row_and_writes_nothing(self):
        """The preview that makes the refusal actionable."""
        p = Project(board=board_with(PERRY_BULLETS))
        before = p.board()
        code, out = p.run("risk-migrate", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertEqual(len(out["migrated"]), 3)
        self.assertEqual(p.board(), before)
        self.assertEqual(p.events(), [])

    def test_the_conversion_is_its_own_event_and_its_own_journal_line(self):
        """It is a fact about the project, not a field on an unrelated risk."""
        p = Project(board=board_with(AIMARK_BULLETS))
        code, out = p.run("risk-migrate")
        self.assertEqual(code, 0, out)
        self.assertEqual([e["event"] for e in p.events()], ["risk-migrate"])
        self.assertEqual(p.events()[0]["count"], 2)
        self.assertIn("`## Top risks` migrated", p.journal())

    def test_risk_migrate_is_a_section_event_not_a_task_event(self):
        """`tests/test_cadence.py` asserts the two sets partition `COMMANDS`;
        this asserts which side of the partition this one is on. A risk row is
        not a task row, and `perry-task list` folds `TASK_EVENTS` only."""
        self.assertIn("risk-migrate", PT.SECTION_EVENTS)
        self.assertNotIn("risk-migrate", PT.TASK_EVENTS)

    def test_the_frozen_list_contract_never_sees_a_migration(self):
        p = Project(board=board_with(AIMARK_BULLETS))
        p.run("risk-migrate")
        code, out = p.run("list", "--all")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["tasks"], [])
        self.assertEqual(out["untitled"], [])

    def test_risk_add_no_longer_reports_a_migration_it_did_not_do(self):
        p = Project(board=board_with("- none\n"))
        _, out = p.run("risk-add", "--title", "a risk")
        self.assertNotIn("migrated", out)
        self.assertNotIn("migrated", p.events()[0])


class TestTheWriterResolvesTheIdColumnByName(unittest.TestCase):
    """M-2. The write twin of `test_a_reordered_header_reads_the_same`.

    `find_section_row` matched `cells[0]`, so on a board that lists its columns
    in another order `perry-state` reported a risk that `risk-clear` insisted
    did not exist:

        board: | Status | Opened | Risk | ID |
        reader (parse_top_risks):    id='RX-001'
        writer (risk-clear RX-001):  "RX-001 is not a row in `## Top risks`"
    """

    REORDERED = (
        "| Status | Opened | Risk | ID |\n"
        "|---|---|---|---|\n"
        "| open | 2026-08-01 | the statement | RX-001 |\n")

    def test_risk_clear_finds_a_row_the_reader_can_see(self):
        p = Project(board=board_with(self.REORDERED))
        self.assertEqual(risks(p.board())[0].id, "RX-001")
        code, out = p.run("risk-clear", "RX-001", "--reason", "it stopped")
        self.assertEqual(code, 0, out)
        self.assertTrue(risks(p.board())[0].resolved)

    def test_the_cleared_cell_lands_in_the_status_column(self):
        """Resolving the id by name is only half of it — the write back has to
        respect the same order, or the reason lands in `Opened`."""
        p = Project(board=board_with(self.REORDERED))
        p.run("risk-clear", "RX-001", "--reason", "it stopped")
        r = risks(p.board())[0]
        self.assertIn("it stopped", r.status)
        self.assertEqual(r.opened, "2026-08-01")
        self.assertEqual(r.title, "the statement")

    def test_a_new_row_lands_in_the_right_columns_too(self):
        p = Project(board=board_with(self.REORDERED))
        code, out = p.run("risk-add", "--title", "a second statement")
        self.assertEqual(code, 0, out)
        second = risks(p.board())[1]
        self.assertEqual(second.id, "RX-002")
        self.assertEqual(second.title, "a second statement")
        self.assertEqual(second.status, "open")

    def test_a_localized_header_clears_the_same(self):
        p = Project(board=board_with(
            "| 状态 | 提出 | 风险 | 编号 |\n"
            "|---|---|---|---|\n"
            "| open | 2026-08-01 | 一个风险 | RX-001 |\n"))
        code, out = p.run("risk-clear", "RX-001", "--reason", "上游修好了")
        self.assertEqual(code, 0, out)
        self.assertTrue(risks(p.board())[0].resolved)

    def test_the_user_input_queue_still_answers_by_id(self):
        """`find_section_row`'s other caller. `USER-id` is an id column too, and
        resolving by name must not have narrowed the rule to `ID`."""
        p = Project()
        p.run("ask", "--needed", "which staging default?")
        code, out = p.run("answer", "USER-001", "--answer", "the second one")
        self.assertEqual(code, 0, out)


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

    def test_a_migrated_board_is_the_whole_register(self):
        p = Project(board=board_with(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n"
            "| RX-001 | GAVI — the vendor contract lapses | 2026-08-01 | open |\n"))
        snap = self.snapshot(p)
        self.assertEqual([r.id for r in snap.top_risks], ["RX-001"])
        self.assertEqual(snap.risks_source, "table")

    def test_no_risk_is_reported_open_and_cleared_at_the_same_time(self):
        """The measured symptom, asserted as the property it violates."""
        p = Project(board=board_with(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n"
            "| RX-001 | GAVI — the vendor contract lapses | 2026-08-01 | open |\n"))
        snap = self.snapshot(p)
        gavi = [r for r in snap.top_risks if "GAVI" in r.meta]
        self.assertEqual(len(gavi), 1)
        self.assertEqual([r.resolved for r in gavi], [False])

    def test_migrating_does_not_raise_the_count(self):
        """End to end through the writer, which is how the count moved: 2 → 4
        for a board and a state file naming the same two risks."""
        p = Project(board=board_with(
            "- GAVI — the vendor contract lapses\n"
            "- LEDGER — reconciliation is manual\n"))
        before = len(self.snapshot(p).top_risks)
        code, out = p.run("risk-migrate")
        self.assertEqual(code, 0, out)
        self.assertEqual(len(self.snapshot(p).top_risks), before)

    def test_an_unmigrated_board_still_merges_both_files(self):
        """The rule is about what migration means, not about dropping a file:
        before it, nothing changes."""
        p = Project(board=board_with("- ONLY-ON-THE-BOARD — a third thing\n"))
        metas = " ".join(r.meta for r in self.snapshot(p).top_risks)
        self.assertIn("ONLY-ON-THE-BOARD", metas)
        self.assertIn("LEDGER", metas)

    def test_an_empty_migrated_table_is_still_a_migrated_board(self):
        """Migrated-and-currently-clear must not read as never-migrated, or the
        rule would switch itself off the moment the last risk is cleared."""
        p = Project(board=board_with(
            "| ID | Risk | Opened | Status |\n"
            "|---|---|---|---|\n"))
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

    def test_the_writer_sees_the_same_bullets_the_reader_does(self):
        """And the conversion is verdict-preserving on this shape too — the
        reader's fixture, put through the writer."""
        p = Project(board=board_with(self.NUMBERED))
        code, out = p.run("risk-migrate")
        self.assertEqual(code, 0, out)
        self.assertEqual(len(out["migrated"]), 2)
        self.assertEqual([r.title for r in risks(p.board())],
                         ["the vendor contract lapses",
                          "reconciliation is manual"])

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
        self.assertEqual(state(p.root)["risks"]["count"], 1)
        self.assertEqual(state(p.root)["risks"]["source"], "table")

    def test_risk_migrate_does_not_offer_to_migrate_a_migrated_board(self):
        """Exit two. It answered "still bullets" and would have appended a
        second table under the heading."""
        p = Project(board=board_with(self.BOLD_HEADER))
        code, out = p.run("risk-migrate")
        self.assertEqual(code, 1, out)
        self.assertIn("already a table", out["refused"])

    def test_risk_add_appends_to_the_table_that_is_already_there(self):
        """Exit three. It wrote a row the reader could not count."""
        p = Project(board=board_with(self.BOLD_HEADER))
        code, out = p.run("risk-add", "--title", "a second statement")
        self.assertEqual(code, 0, out)
        self.assertEqual([r.id for r in risks(p.board())], ["RX-001", "RX-002"])

    def test_the_decorated_header_is_still_one_table_afterwards(self):
        p = Project(board=board_with(self.BOLD_HEADER))
        p.run("risk-add", "--title", "a second statement")
        self.assertEqual(
            p.board().split("\n").count("|---|---|---|---|"), 1, p.board())

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


if __name__ == "__main__":
    unittest.main()
