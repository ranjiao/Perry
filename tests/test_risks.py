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

from test_task_writer import PT, Project

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
        board = board_with(
            "| Severity | Meaning |\n"
            "|---|---|\n"
            "| H | drop everything |\n"
            "\n"
            "- H · Apple developer agreement expired\n")
        parsed = risks(board)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].source, "bullets")

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
        code, out = p.run("risk-add", "--title", "另一个风险")
        self.assertEqual(code, 0, out)
        self.assertIn("| 编号 | 风险 | 提出 | 状态 |", p.board())


class TestMigrationLosesNothing(unittest.TestCase):
    """`risk-add` converts a bullet list in the same write."""

    def test_every_bullet_survives_verbatim(self):
        """The statement is the human's and this tool has no opinion about it.

        Checked against the two real boards' actual text — bold, emoji, inline
        links, Chinese, backticks.
        """
        p = Project(board=board_with(AIMARK_BULLETS))
        code, out = p.run("risk-add", "--title", "a new one")
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
        p.run("risk-add", "--title", "sentinel")
        after = [r for r in risks(p.board()) if r.title != "sentinel"]
        self.assertEqual([r.meta for r in before], [r.meta for r in after])
        self.assertEqual([r.resolved for r in before], [r.resolved for r in after])

    def test_migration_does_not_invent_an_opened_date(self):
        """A pre-existing risk's open date is not recorded anywhere.

        Stamping today would assert that a nine-month-old risk is new. Empty
        reads back as `age_days: null`, which is the honest answer.
        """
        p = Project(board=board_with(PERRY_BULLETS))
        p.run("risk-add", "--title", "sentinel")
        migrated = [r for r in risks(p.board()) if r.title != "sentinel"]
        self.assertTrue(all(r.opened == "" for r in migrated),
                        [r.opened for r in migrated])

    def test_a_struck_through_bullet_carries_its_stated_date_across(self):
        p = Project(board=board_with(PERRY_BULLETS))
        code, out = p.run("risk-add", "--title", "sentinel")
        self.assertEqual(code, 0, out)
        cleared = [m for m in out["migrated"] if m["status"].startswith("cleared")]
        self.assertEqual(len(cleared), 1)
        self.assertEqual(cleared[0]["status"], "cleared 2026-08-16")

    def test_a_placeholder_bullet_is_not_migrated_into_a_risk(self):
        """`BOARD_TEMPLATE.md` ships `- (no active risks)`."""
        p = Project(board=board_with("- (no active risks)\n"))
        code, out = p.run("risk-add", "--title", "the first real one")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["migrated"], [])
        self.assertEqual(len(risks(p.board())), 1)


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
        self.assertIn("risk-add", out["refused"])

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


if __name__ == "__main__":
    unittest.main()
