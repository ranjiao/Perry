"""Contract tests for the recurrence register — `BOARD.md § Cadence`.

The defect this closes: the section had three readers (`perry-state`,
`work/reference/subcommands.md § triage`, `modes/queue.md` step 5) and no
writer, and its `Next due` column is **computed** — frequency plus the last
run — so a human redid the arithmetic after every single occurrence. Perry has
now hit that defect three times. `Stage since` and `Arrived` store a date and
compute the age; `Idle` was removed from the User Input Queue for it (TASK-039).

Every test below names a behaviour that can fail. Each was verified by reverting
the code it covers and confirming the assertion goes red — a test whose
assertion is satisfied by its own setup is worse than no test, because it
reports coverage that does not exist.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
TOOL = PERRY_HOME / "bin" / "perry-task"
STATE = PERRY_HOME / "bin" / "perry-state"

sys.path.insert(0, str(PERRY_HOME / "viewer"))
import parsers as P  # noqa: E402


def load(name: str, path: Path):
    spec = importlib.util.spec_from_loader(
        name, importlib.machinery.SourceFileLoader(name, str(path)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PT = load("perry_task_cad", TOOL)

# Six columns, no `Last run` — the shape the template shipped and every board
# written before this work has.
BOARD = """# Board — T

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## Cadence (recurring; doesn't consume P0 slots)

| ID | Recurring task | Owner | Frequency | Next due | Last evidence |
|---|---|---|---|---|---|

## Top risks

- none
"""

# No `## Cadence` at all.
BOARD_NO_SECTION = "\n".join(
    BOARD.split("\n")[:BOARD.split("\n").index("## Cadence (recurring; doesn't consume P0 slots)")]
    + ["## Top risks", "", "- none", ""])

TODAY = date.today()


class Project:
    def __init__(self, board: str = BOARD):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n")
        (self.root / "BOARD.md").write_text(board)

    def run(self, *argv):
        r = subprocess.run(
            ["python3", str(TOOL), *argv, "--root", str(self.root), "--json"],
            capture_output=True, text=True)
        try:
            return r.returncode, json.loads(r.stdout or "{}")
        except json.JSONDecodeError:
            return r.returncode, r.stdout + r.stderr

    def state(self) -> dict:
        r = subprocess.run(
            ["python3", str(STATE), "--root", str(self.root), "--section", "cadence"],
            capture_output=True, text=True)
        return json.loads(r.stdout)["cadence"]

    def dashboard(self) -> str:
        """The human surface. A payload key nothing renders reaches nobody."""
        r = subprocess.run(
            ["python3", str(STATE), "--root", str(self.root), "--dashboard"],
            capture_output=True, text=True)
        return r.stdout + r.stderr

    def board(self) -> str:
        return (self.root / "BOARD.md").read_text()

    def rows(self) -> list:
        return P.parse_board(self.board()).cadence_items

    def row(self, cid: str):
        return next(r for r in self.rows() if r.id == cid)

    def events(self) -> list[dict]:
        p = self.root / ".perry" / "events.jsonl"
        return ([json.loads(l) for l in p.read_text().split("\n") if l.strip()]
                if p.exists() else [])

    def journal(self) -> str:
        for p in (self.root / "journal").rglob("*.md"):
            return p.read_text()
        return ""

    def __del__(self):
        self.dir.cleanup()


class TestFrequencyArithmetic(unittest.TestCase):
    """The period table, against what real registers actually say."""

    def test_the_four_frequencies_the_task_named(self):
        for freq, days in (("weekly", 7), ("14d", 14)):
            self.assertEqual(P.next_due_after(date(2026, 3, 2), freq),
                             date(2026, 3, 2) + timedelta(days=days), freq)
        self.assertEqual(P.next_due_after(date(2026, 3, 2), "monthly"),
                         date(2026, 4, 2))
        self.assertEqual(P.next_due_after(date(2026, 3, 2), "quarterly"),
                         date(2026, 6, 2))

    def test_month_arithmetic_is_calendar_not_thirty_days(self):
        """A month-end close moved 30 days from 31 January lands on 2 March and
        stops being month-end. Calendar months clamp instead."""
        self.assertEqual(P.next_due_after(date(2026, 1, 31), "monthly"),
                         date(2026, 2, 28))
        self.assertEqual(P.next_due_after(date(2024, 1, 31), "monthly"),
                         date(2024, 2, 29))
        self.assertEqual(P.next_due_after(date(2026, 11, 30), "quarterly"),
                         date(2027, 2, 28))
        self.assertEqual(P.next_due_after(date(2026, 12, 15), "monthly"),
                         date(2027, 1, 15))

    def test_every_frequency_on_a_real_register_parses(self):
        """Verified against `~/proj/gimegime-pmo` — `continuous` and `hourly`
        are live there, and a vocabulary that refuses them cannot describe the
        register it is a writer for."""
        for freq in ("weekly", "monthly", "continuous", "hourly"):
            self.assertIsNotNone(P.parse_frequency(freq), freq)
        self.assertEqual(P.parse_frequency("continuous")[0], "aperiodic")
        self.assertEqual(P.parse_frequency("hourly")[0], "aperiodic")
        self.assertIsNone(P.next_due_after(TODAY, "continuous"))

    def test_an_unreadable_frequency_is_none_not_a_guess(self):
        for junk in ("twice in a blue moon", "", "0d", "sometimes"):
            self.assertIsNone(P.parse_frequency(junk), junk)


class TestNextDueIsReadTolerantly(unittest.TestCase):
    """`Next due` is prose on a real board. Reading it is the tolerant half."""

    def test_the_three_shapes_on_a_real_register(self):
        # Copied verbatim from `~/proj/gimegime-pmo/BOARD.md § Cadence`.
        self.assertEqual(
            P.parse_due("**2026-08-31**（7 月版 ✅ 8/3 补作 → `evidence/2026-08/retro-2026-07.md`；6 月版跳过）"),
            date(2026, 8, 31))
        self.assertEqual(
            P.parse_due("**2026-W32 friday-review (8/7)**（W31 版 ✅ 8/3 补作）"),
            date(2026, 8, 9))
        self.assertIsNone(P.parse_due("n/a"))
        self.assertIsNone(P.parse_due("continuous"))

    def test_an_iso_week_resolves_to_its_sunday_not_its_monday(self):
        """A week-scoped ritual is not late on Monday. Taking the Monday would
        report every weekly row as up to six days overdue inside its own week."""
        self.assertEqual(P.parse_due("2026-W32"), date(2026, 8, 9))
        self.assertEqual(P.parse_due("2026-W32").isoweekday(), 7)

    def test_a_date_inside_a_trailing_note_is_not_the_due_date(self):
        """Both cells are from a live register, and both were reported overdue.

        The old rule searched the WHOLE cell for `\\d{4}-\\d{2}-\\d{2}`, so a
        row saying `n/a` came back due `2026-08-03` — scraped out of an
        evidence *filename* — and a quarterly row came back 224 days overdue on
        the date of its LAST run. `parse_frequency`'s docstring states the rule
        this enforces: a confidently wrong value is worse than an admitted
        unreadable one, and an unreadable `Next due` is a reported finding
        (`cadence.undated`), not a silent pass."""
        self.assertIsNone(
            P.parse_due("n/a （见 evidence/2026-08/2026-08-03-retro.md）"),
            "a date inside a cited path became the due date")
        self.assertEqual(
            P.parse_due("2026-W40（上次 2026-01-05 完成）"),
            date(2026, 10, 4),
            "the note about the last run overruled the ISO week before it")

    def test_a_leading_n_a_is_never_a_date_however_the_note_is_written(self):
        """The cell says there is no date. Reading on to find one anyway is the
        failure mode, not the tolerance."""
        for cell in ("n/a", "n/a (2026-01-05 完成)", "n/a — see 2026-01-05",
                     "na 2026-01-05", "—", "continuous 2026-01-05"):
            self.assertIsNone(P.parse_due(cell), cell)

    def test_a_bare_path_yields_no_date(self):
        """An evidence path cites the LAST run. Mining it for digits is how a
        finished ritual gets reported as overdue by the width of its own
        filing convention."""
        self.assertIsNone(P.parse_due("evidence/2026-08/2026-08-03-retro.md"))
        self.assertIsNone(P.parse_due("`weekly/2026-32.md`"))


class TestColumnsResolveByName(unittest.TestCase):
    """`schema/README.md § Columns resolve by name`. Fourth location."""

    def test_a_reordered_header_is_read_correctly(self):
        board = BOARD.replace(
            "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |\n|---|---|---|---|---|---|",
            "| ID | Frequency | Next due | Recurring task | Owner | Last evidence |\n|---|---|---|---|---|---|\n"
            "| CAD-001 | weekly | 2026-01-01 | Friday review | PMO | weekly/x.md |")
        row = P.parse_board(board).cadence_items[0]
        self.assertEqual(row.frequency, "weekly")
        self.assertEqual(row.title, "Friday review")
        self.assertEqual(row.owner, "PMO")
        self.assertEqual(row.next_due, "2026-01-01")

    def test_last_run_has_no_positional_fallback(self):
        """It has never occupied a position, and a reader that invents one for
        it would read `Last evidence` as a date on every board written before
        this work."""
        row = P.parse_board(BOARD.replace(
            "|---|---|---|---|---|---|",
            "|---|---|---|---|---|---|\n"
            "| CAD-001 | Friday review | PMO | weekly | 2026-01-01 | weekly/x.md |")
        ).cadence_items[0]
        self.assertEqual(row.last_run, "")
        self.assertEqual(row.last_evidence, "weekly/x.md")

    def test_a_five_column_register_still_parses(self):
        """A live project's register has no `Last evidence` column at all."""
        board = BOARD.replace(
            "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |\n|---|---|---|---|---|---|",
            "| ID | Recurring task | Owner | Frequency | Next due |\n|---|---|---|---|---|\n"
            "| CAD-001 | Friday review | PMO | weekly | 2026-01-01 |")
        row = P.parse_board(board).cadence_items[0]
        self.assertEqual(row.frequency, "weekly")
        self.assertEqual(row.next_due, "2026-01-01")
        self.assertEqual(row.last_evidence, "")


class TestCadenceAdd(unittest.TestCase):

    def test_it_mints_stamps_and_writes_all_three(self):
        p = Project()
        code, out = p.run("cadence-add", "--title", "Month-end close",
                          "--frequency", "monthly", "--owner", "User")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["id"], "CAD-001")
        row = p.row("CAD-001")
        self.assertEqual(row.title, "Month-end close")
        self.assertEqual(row.owner, "User")
        self.assertEqual(row.frequency, "monthly")
        self.assertEqual(row.next_due, f"{P.advance(TODAY, 1, 'm'):%Y-%m-%d}")
        self.assertIn("CAD-001", p.journal())
        self.assertEqual([e["event"] for e in p.events()], ["cadence-add"])

    def test_next_due_is_computed_from_the_frequency_not_from_today(self):
        """The whole point of the pair. A tool that stamped today's date, or the
        same date for every frequency, would pass every other test here."""
        p = Project()
        for title, freq, expect in (
                ("w", "weekly", P.advance(TODAY, 1, "w")),
                ("m", "monthly", P.advance(TODAY, 1, "m")),
                ("q", "quarterly", P.advance(TODAY, 3, "m")),
                ("n", "21d", TODAY + timedelta(days=21))):
            code, out = p.run("cadence-add", "--title", title, "--frequency", freq)
            self.assertEqual(code, 0, out)
            self.assertEqual(out["next_due"], f"{expect:%Y-%m-%d}", freq)
        self.assertEqual(len({r.next_due for r in p.rows()}), 4,
                         "four frequencies produced fewer than four due dates")

    def test_a_registration_is_not_a_run(self):
        """`Last run` stays empty. Stamping today would assert an occurrence
        that did not happen, and make the first `Next due` unverifiable."""
        p = Project()
        p.run("cadence-add", "--title", "x", "--frequency", "weekly")
        self.assertNotIn(f"{TODAY:%Y-%m-%d}", p.row("CAD-001").last_run)

    def test_on_backdates_the_history_and_the_due_date_follows(self):
        p = Project()
        code, out = p.run("cadence-add", "--title", "x", "--frequency", "weekly",
                          "--on", "2026-01-01")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.row("CAD-001").last_run, "2026-01-01")
        self.assertEqual(out["next_due"], "2026-01-08")

    def test_an_aperiodic_frequency_is_recorded_with_no_due_date(self):
        p = Project()
        code, out = p.run("cadence-add", "--title", "watch logs",
                          "--frequency", "continuous")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["next_due"], "n/a")
        self.assertIsNone(P.parse_due(p.row("CAD-001").next_due))

    def test_the_section_is_created_after_the_priority_tables(self):
        p = Project(BOARD_NO_SECTION)
        self.assertNotIn("## Cadence", p.board())
        code, out = p.run("cadence-add", "--title", "x", "--frequency", "weekly")
        self.assertEqual(code, 0, out)
        lines = p.board().split("\n")
        self.assertLess(next(i for i, l in enumerate(lines) if l.startswith("## P2")),
                        next(i for i, l in enumerate(lines) if l.startswith("## Cadence")))
        self.assertEqual(p.row("CAD-001").frequency, "weekly")

    def test_it_refuses_a_frequency_it_cannot_schedule_from(self):
        p = Project()
        code, out = p.run("cadence-add", "--title", "x", "--frequency", "whenever")
        self.assertEqual(code, 1)
        self.assertIn("whenever", out["refused"])
        self.assertNotIn("## Cadence\n\n| ID", p.board().replace("(recurring; doesn't consume P0 slots)", ""))
        self.assertEqual(p.rows(), [])

    def test_it_refuses_without_a_title_or_a_frequency(self):
        p = Project()
        self.assertEqual(p.run("cadence-add", "--frequency", "weekly")[0], 1)
        self.assertEqual(p.run("cadence-add", "--title", "x")[0], 1)
        self.assertEqual(p.events(), [])

    def test_ids_are_minted_above_a_boards_existing_cadence_numbering(self):
        """A live register numbers its rows `CADENCE-NNN`. A minter blind to
        that prefix issues `CAD-001` beside `CADENCE-002` and puts two
        numbering schemes in one table."""
        p = Project(BOARD.replace(
            "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |\n"
            "|---|---|---|---|---|---|",
            "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |\n"
            "|---|---|---|---|---|---|\n"
            "| CADENCE-003 | Weekly report | PMO | weekly | 2026-01-01 | — |"))
        code, out = p.run("cadence-add", "--title", "x", "--frequency", "weekly")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["id"], "CAD-004")

    def test_an_id_is_never_reissued_after_its_row_is_removed(self):
        p = Project()
        p.run("cadence-add", "--title", "x", "--frequency", "weekly")
        board = p.board()
        (p.root / "BOARD.md").write_text(
            "\n".join(l for l in board.split("\n") if "CAD-001" not in l))
        self.assertEqual(p.rows(), [])
        code, out = p.run("cadence-add", "--title", "y", "--frequency", "weekly")
        self.assertEqual(out["id"], "CAD-002", "a retired id was reissued")


class TestCadenceDone(unittest.TestCase):

    def setUp(self):
        self.p = Project()
        self.p.run("cadence-add", "--title", "Friday review",
                   "--frequency", "weekly", "--on", "2026-01-02")

    def test_it_recomputes_next_due_from_the_rows_own_frequency(self):
        """The defect this whole task exists for. A `cadence-done` that recorded
        the run and left `Next due` alone would satisfy every other assertion
        about evidence and journalling in this file."""
        before = self.p.row("CAD-001").next_due
        code, out = self.p.run("cadence-done", "CAD-001",
                               "--evidence", "weekly/2026-33.md", "--on", "2026-03-06")
        self.assertEqual(code, 0, out)
        self.assertEqual(before, "2026-01-09")
        self.assertEqual(self.p.row("CAD-001").next_due, "2026-03-13")

    def test_it_records_the_run_and_the_evidence(self):
        self.p.run("cadence-done", "CAD-001", "--evidence", "weekly/2026-33.md",
                   "--on", "2026-03-06")
        row = self.p.row("CAD-001")
        self.assertEqual(row.last_run, "2026-03-06")
        self.assertEqual(row.last_evidence, "weekly/2026-33.md")

    def test_the_run_defaults_to_today(self):
        self.p.run("cadence-done", "CAD-001", "--evidence", "x.md")
        self.assertEqual(self.p.row("CAD-001").last_run, f"{TODAY:%Y-%m-%d}")
        self.assertEqual(self.p.row("CAD-001").next_due,
                         f"{P.advance(TODAY, 1, 'w'):%Y-%m-%d}")

    def test_it_refuses_without_evidence(self):
        code, out = self.p.run("cadence-done", "CAD-001")
        self.assertEqual(code, 1)
        # A REFUSAL, not a crash. Asserting only the exit code passed while the
        # guard was removed, because writing `None` into a cell raises and exits
        # 1 too — a test satisfied by a traceback, which is the failure mode
        # this file's docstring names.
        self.assertIsInstance(out, dict, f"not a refusal, a crash: {out}")
        self.assertIn("--evidence", out.get("refused", ""))
        self.assertEqual(self.p.row("CAD-001").last_run, "2026-01-02")
        self.assertEqual([e["event"] for e in self.p.events()], ["cadence-add"])

    def test_it_refuses_an_id_that_is_not_in_the_register(self):
        self.assertEqual(self.p.run("cadence-done", "CAD-099", "--evidence", "x")[0], 1)

    def test_it_writes_the_board_the_journal_and_the_event(self):
        self.p.run("cadence-done", "CAD-001", "--evidence", "weekly/2026-33.md")
        self.assertIn("weekly/2026-33.md", self.p.journal())
        ev = self.p.events()[-1]
        self.assertEqual(ev["event"], "cadence-done")
        self.assertEqual(ev["id"], "CAD-001")
        self.assertEqual(ev["previous_due"], "2026-01-09")
        self.assertEqual(ev["next_due"], self.p.row("CAD-001").next_due)

    def test_frequency_can_be_corrected_in_the_same_write(self):
        code, out = self.p.run("cadence-done", "CAD-001", "--evidence", "x.md",
                               "--frequency", "monthly", "--on", "2026-01-31")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.p.row("CAD-001").frequency, "monthly")
        self.assertEqual(self.p.row("CAD-001").next_due, "2026-02-28")

    def test_it_refuses_a_row_whose_frequency_it_cannot_read(self):
        board = self.p.board().replace("| weekly |", "| when the mood takes us |")
        (self.p.root / "BOARD.md").write_text(board)
        code, out = self.p.run("cadence-done", "CAD-001", "--evidence", "x.md")
        self.assertEqual(code, 1)
        self.assertIn("--frequency", out["refused"])

    def test_last_run_is_added_to_a_section_that_predates_it(self):
        """`ensure_section_columns`'s reason for existing: a board that already
        has the section has nowhere to put the date, and dropping it silently is
        the defect that lost `--commitment`."""
        self.assertIn("Last run", self.p.board())
        header = next(l for l in self.p.board().split("\n")
                      if l.startswith("| ID | Recurring task"))
        self.assertEqual(header.count("|"), 8, header)

    def test_a_sub_grouped_register_is_written_the_way_it_is_read(self):
        """The reader tolerates a `###` label inside `## Cadence`; the writers
        stopped at the first one, and the two then disagreed about what the
        section contained.

        On such a board `cadence-done` refused with "not a row in `## Cadence`"
        — false, and the third false "not a row" message in this file's history
        — while `cadence-add` SUCCEEDED, widening the header to seven columns
        and padding none of the sub-grouped rows. The result is a ragged table
        that `perry-lint` reports clean, produced by the tool whose entire claim
        is that it mechanizes the format rather than breaking it.
        """
        p = Project(BOARD.replace(
            "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |\n"
            "|---|---|---|---|---|---|",
            "### Weekly\n\n"
            "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |\n"
            "|---|---|---|---|---|---|\n"
            "| CAD-100 | friday review | PMO | weekly | 2026-01-01 | w/x.md |\n"
            "\n### Monthly\n\n"
            "| CAD-200 | month close | PMO | monthly | 2026-01-31 | m/x.md |"))
        code, out = p.run("cadence-done", "CAD-200", "--evidence", "runbook/y.md")
        self.assertEqual(code, 0, f"a sub-grouped row was unreachable: {out}")
        self.assertEqual(p.row("CAD-200").last_evidence, "runbook/y.md")

        # And the widening `cadence-done` just did reaches every row, including
        # the ones above the sub-group label.
        rows = [l for l in p.board().split("\n") if l.startswith("| CAD-")]
        header = next(l for l in p.board().split("\n")
                      if l.startswith("| ID | Recurring task"))
        width = header.count("|")
        for r in rows:
            self.assertEqual(r.count("|"), width,
                             f"row width diverged from the header:\n  {r}")

    def test_last_evidence_is_created_on_a_register_that_lacks_the_column(self):
        p = Project(BOARD.replace(
            "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |\n|---|---|---|---|---|---|",
            "| ID | Recurring task | Owner | Frequency | Next due |\n|---|---|---|---|---|"))
        p.run("cadence-add", "--title", "x", "--frequency", "weekly")
        code, out = p.run("cadence-done", "CAD-001", "--evidence", "runbook/x.md")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.row("CAD-001").last_evidence, "runbook/x.md")


class TestOverdueReport(unittest.TestCase):

    def test_overdue_rows_are_reported_by_age_oldest_first(self):
        """The NEWER row is registered first, so board order and sorted order
        differ — which is the only arrangement that can fail on the sort.

        This test used to add `old` before `newer`, so the rows arrived already
        in the order the assertion wanted and `perry-state`'s sort line could be
        deleted with the whole 600-test suite still green. The claim it guards
        is not a nicety: `work/reference/subcommands.md § triage` now tells the
        agent in bold that the list "is already sorted oldest-first" and to stop
        scanning the table by eye, and that promise is the only thing standing
        between the procedure and the eyeball it replaced.
        """
        p = Project()
        p.run("cadence-add", "--title", "newer", "--frequency", "weekly",
              "--on", f"{TODAY - timedelta(days=12):%Y-%m-%d}")
        p.run("cadence-add", "--title", "old", "--frequency", "weekly",
              "--on", f"{TODAY - timedelta(days=37):%Y-%m-%d}")
        p.run("cadence-add", "--title", "future", "--frequency", "monthly")
        # Board order: CAD-001 (5 days overdue) then CAD-002 (30).
        self.assertEqual([r.id for r in p.rows()],
                         ["CAD-001", "CAD-002", "CAD-003"])
        rep = p.state()
        self.assertEqual(rep["count"], 3)
        self.assertEqual([r["id"] for r in rep["overdue"]], ["CAD-002", "CAD-001"])
        self.assertEqual([r["days_overdue"] for r in rep["overdue"]], [30, 5])

    def test_a_row_due_today_is_not_yet_overdue(self):
        p = Project()
        p.run("cadence-add", "--title", "x", "--frequency", "weekly",
              "--on", f"{TODAY - timedelta(days=7):%Y-%m-%d}")
        self.assertEqual(p.row("CAD-001").next_due, f"{TODAY:%Y-%m-%d}")
        self.assertEqual(p.state()["overdue"], [])

    def test_an_aperiodic_row_is_never_overdue_and_is_not_a_finding(self):
        p = Project()
        p.run("cadence-add", "--title", "x", "--frequency", "continuous")
        rep = p.state()
        self.assertEqual(rep["overdue"], [])
        self.assertEqual(rep["undated"], [])
        self.assertEqual(rep["unreadable_frequency"], [])
        self.assertEqual(rep["items"][0]["frequency_kind"], "aperiodic")

    def test_a_periodic_row_with_an_unreadable_due_cell_is_a_finding(self):
        """Not silently 'fine'. That would exempt exactly the rows most likely
        to have been abandoned — a clock that stops when it cannot read a date."""
        p = Project()
        p.run("cadence-add", "--title", "x", "--frequency", "weekly")
        (p.root / "BOARD.md").write_text(
            p.board().replace(f"| {P.advance(TODAY, 1, 'w'):%Y-%m-%d} |", "| soon |"))
        rep = p.state()
        self.assertEqual([r["id"] for r in rep["undated"]], ["CAD-001"])
        self.assertEqual(rep["overdue"], [])

    def test_an_unreadable_frequency_is_reported_rather_than_dropped(self):
        p = Project(BOARD.replace(
            "|---|---|---|---|---|---|",
            "|---|---|---|---|---|---|\n"
            "| CAD-009 | mystery | X | when the mood takes us | — | — |"))
        rep = p.state()
        self.assertEqual([r["id"] for r in rep["unreadable_frequency"]], ["CAD-009"])
        self.assertEqual(rep["items"][0]["frequency_kind"], "")

    def test_a_done_run_clears_the_overdue_finding(self):
        p = Project()
        p.run("cadence-add", "--title", "x", "--frequency", "weekly",
              "--on", f"{TODAY - timedelta(days=30):%Y-%m-%d}")
        self.assertEqual(len(p.state()["overdue"]), 1)
        p.run("cadence-done", "CAD-001", "--evidence", "e.md")
        self.assertEqual(p.state()["overdue"], [])

    def test_the_dashboard_line_appears_only_when_there_is_a_register(self):
        empty = Project(BOARD_NO_SECTION)
        self.assertNotIn("Cadence", empty.dashboard())
        p = Project()
        p.run("cadence-add", "--title", "x", "--frequency", "weekly",
              "--on", f"{TODAY - timedelta(days=30):%Y-%m-%d}")
        self.assertIn("1 overdue", p.dashboard())

    def test_an_unreadable_frequency_reaches_the_human_surface(self):
        """The third list, which the dashboard line dropped.

        A row unreadable on BOTH axes is in `unreadable_frequency` ONLY — the
        `undated` branch is gated on `frequency_kind == "period"` — so it was in
        the JSON and nowhere a human looks. That is the row nothing can schedule
        and nothing was saying so about, which is the failure the register
        exists to catch. Both procedures that read this payload name all three
        lists (`work/reference/subcommands.md § triage`, `modes/queue.md`
        step 5); the line they read from named two.
        """
        p = Project(BOARD.replace(
            "|---|---|---|---|---|---|",
            "|---|---|---|---|---|---|\n"
            "| CAD-009 | mystery | X | 每周五 | — | — |"))
        rep = p.state()
        self.assertEqual([r["id"] for r in rep["unreadable_frequency"]], ["CAD-009"])
        self.assertEqual(rep["undated"], [], "the setup no longer reaches the "
                                             "only-unreadable_frequency case")
        line = next(l for l in p.dashboard().split("\n") if "Cadence" in l)
        self.assertIn("unreadable Frequency", line,
                      f"the only list this row is in reaches nobody: {line}")


class TestCadenceIsNotATask(unittest.TestCase):
    """`schema/task-list-contract.md § What this contract does not cover`."""

    def test_cadence_rows_and_events_stay_out_of_the_list_payload(self):
        """The board half of this was always right — `_task_sections` skips the
        heading. The EVENT half folded every event carrying an id, so a
        registered ritual arrived as a closed task with `status: registered`."""
        p = Project()
        p.run("cadence-add", "--title", "x", "--frequency", "weekly")
        p.run("cadence-done", "CAD-001", "--evidence", "e.md")
        code, out = p.run("list", "--all")
        self.assertEqual(code, 0, out)
        self.assertEqual([t["id"] for t in out["tasks"]], [])
        self.assertEqual(out["closed"], 0)
        self.assertEqual(out["untitled"], [])

    def test_user_input_rows_stay_out_too(self):
        p = Project()
        p.run("ask", "--needed", "which staging default?")
        _, out = p.run("list", "--all")
        self.assertEqual([t["id"] for t in out["tasks"]], [])

    def test_every_subcommand_is_classified_as_task_or_section(self):
        """The partition that keeps the fix above from rotting. A command added
        to `COMMANDS` and to neither set fails here rather than silently
        leaking into — or vanishing from — the front-end contract."""
        classified = PT.TASK_EVENTS | PT.SECTION_EVENTS
        # The partition is over WRITERS. `list` and `events` are read-only —
        # they emit nothing, so classifying them as task- or section-writing
        # would be classifying a fact that does not exist. Derived from
        # `READ_ONLY_COMMANDS` rather than named here, so a third read-only
        # subcommand does not have to be remembered in two places.
        writers = set(PT.COMMANDS) - set(PT.READ_ONLY_COMMANDS)
        self.assertEqual(writers - classified, set(),
                         "subcommand writes events nothing classifies")
        self.assertEqual(classified - writers - {"route"}, set(),
                         "classified an event no subcommand emits")

    def test_done_cannot_close_a_cadence_row(self):
        p = Project()
        p.run("cadence-add", "--title", "x", "--frequency", "weekly")
        code, out = p.run("done", "CAD-001", "--evidence", "e.md")
        self.assertEqual(code, 1)
        self.assertIn("CAD-001", p.board())

    def test_the_refusal_is_true_and_says_why(self):
        """Rubric item 5 is "refuses **and says why**", and only the first half
        held.

        All five task subcommands answered `CAD-001 is not a row on the board`
        — about a row the same tool had written one command earlier and which
        `perry-state --json` lists. That is verbatim the defect class
        `bin/perry-task § _task_sections` documents ("a message that was false,
        about rows the same tool had just printed"), reintroduced for a
        different section. A refusal that misdescribes the state sends the
        reader hunting for a missing row instead of reading the rule.
        """
        p = Project()
        p.run("cadence-add", "--title", "x", "--frequency", "weekly")
        for argv in (("done", "CAD-001", "--evidence", "e.md"),
                     ("status", "CAD-001", "--status", "blocked"),
                     ("next", "CAD-001", "--next", "do the thing"),
                     ("drop", "CAD-001", "--reason", "no longer needed"),
                     ("retitle", "CAD-001", "--title", "y")):
            code, out = p.run(*argv)
            msg = str(out)
            self.assertEqual(code, 1, f"{argv[0]} did not refuse: {out}")
            self.assertNotIn(
                "is not a row on the board", msg,
                f"{argv[0]} refused with a false statement about a row the "
                f"tool wrote and `perry-state` lists")
            self.assertIn("Cadence", msg, f"{argv[0]} named no section")
            self.assertIn("cadence-done", msg,
                          f"{argv[0]} named no way forward")
        self.assertIn("CAD-001", p.board())

    def test_every_non_task_section_has_a_refusal_to_offer(self):
        """The partition that keeps the fix above from becoming a crash. A
        section added to `NON_TASK_SECTIONS` and not to `NON_TASK_REFUSAL`
        would raise `KeyError` out of `find()` — a traceback in place of a
        refusal, on the write path."""
        self.assertEqual(set(PT.Board.NON_TASK_SECTIONS),
                         set(PT.NON_TASK_REFUSAL))
        for name, text in PT.NON_TASK_REFUSAL.items():
            self.assertIn("{id}", text, f"{name}: the message names no row")
            self.assertIn("perry-task", text, f"{name}: no way forward")

    def test_the_refusal_still_says_not_on_the_board_for_an_id_that_is_not(self):
        """The specific message must not swallow the general one — an id that
        genuinely is nowhere has to keep saying so."""
        p = Project()
        code, out = p.run("done", "TASK-404", "--evidence", "e.md")
        self.assertEqual(code, 1)
        self.assertIn("is not a row on the board", str(out))


class TestTheLegacyProjectionIsUnchanged(unittest.TestCase):
    """`BoardState.cadence` has consumers that predate `Cadence` — `all_tasks`,
    the viewer's board template, and `perry-state`'s drift exclusion, which keys
    on `priority == "Cadence"`. One parse feeds both views; this pins the old
    one so the refactor changed no payload."""

    def test_the_task_projection_of_a_real_register(self):
        board = BOARD.replace(
            "|---|---|---|---|---|---|",
            "|---|---|---|---|---|---|\n"
            "| CAD-001 | Friday review | PMO Agent | weekly | 2026-08-15 | weekly/2026-32.md |")
        state = P.parse_board(board)
        t = state.cadence[0]
        self.assertEqual(t.priority, "Cadence")
        self.assertEqual((t.id, t.title, t.owner), ("CAD-001", "Friday review", "PMO Agent"))
        self.assertEqual(t.status, "weekly")
        self.assertEqual(t.next_action, "2026-08-15")
        self.assertEqual(t.evidence, "weekly/2026-32.md")
        self.assertEqual(len(state.cadence), len(state.cadence_items))

    def test_cadence_rows_are_still_excluded_from_drift(self):
        p = Project()
        p.run("cadence-add", "--title", "x", "--frequency", "weekly")
        r = subprocess.run(
            ["python3", str(STATE), "--root", str(p.root), "--section", "board"],
            capture_output=True, text=True)
        drift = json.loads(r.stdout)["board"]["drift"]
        self.assertEqual(drift["unrecorded"], 0)
        self.assertEqual(drift["orphaned"], [])


class TestLinkageBelongsToItsOwnPhase(unittest.TestCase):
    """A scored phase's linkage registry is not dangling.

    `linkage-kr-exists` judged **every** `phase/*-linkage.md` against the
    **current** phase's KR set. So the moment a phase was scored and the next
    one opened, the old phase's registry — which correctly names the KRs it was
    written for — was reported as pointing at KRs that do not exist.

    It fired on this project's first rollover ever, on `phase/001-linkage.md`,
    naming `P-O1.4` — a KR that exists exactly where it should. A guard written
    when there had only ever been one phase.

    The file names its own phase (`<NNN>-linkage.md`), so the right KR set is
    derivable with no new state.
    """

    def project(self, current):
        import shutil
        import tempfile
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "phase").mkdir()
        (d / ".perry").mkdir()
        (d / ".perry" / "config.md").write_text("State root: .\n")
        (d / "BOARD.md").write_text("# Board\n")
        (d / "phase" / "CURRENT").write_text(current + "\n")
        (d / "phase" / "001-old.md").write_text(
            "# Phase #001 — old\n\n> **Started**: 2026-08-01\n"
            "> **Status**: scored\n\n## Objective 1 — a\n\n"
            "| Id | KR text | Metric / Target | Linked overall KR |\n"
            "|---|---|---|---|\n| P-O1.1 | old work | 1 | — |\n")
        (d / "phase" / "002-new.md").write_text(
            "# Phase #002 — new\n\n> **Started**: 2026-08-19\n"
            "> **Status**: active\n\n## Objective 1 — b\n\n"
            "| Id | KR text | Metric / Target | Linked overall KR |\n"
            "|---|---|---|---|\n| P-O1.9 | new work | 1 | — |\n")
        (d / "phase" / "001-linkage.md").write_text(
            '---\nlinkage: 1\nphase: "001-old"\nobjectives:\n  - id: O1\n'
            '    title: "a"\n    krs:\n      - id: P-O1.1\n'
            '        title: "old work"\n        metric: "1"\n        target: 1\n'
            '        current: 1\n        stretch: false\n        tasks: []\n---\n')
        return d

    def rules(self, d):
        import json
        import subprocess
        import sys
        proc = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-lint"),
             "--root", str(d), "--json"], capture_output=True, text=True)
        return [f["rule"] for f in json.loads(proc.stdout)["findings"]]

    def test_the_old_phases_registry_is_not_reported_after_a_rollover(self):
        self.assertNotIn("linkage-kr-exists",
                         self.rules(self.project("002-new")))

    def test_a_genuinely_wrong_kr_is_still_reported(self):
        """The guard has to keep working, or moving the KR set just turns it
        off. A registry naming a KR its OWN phase does not have is a real
        finding."""
        d = self.project("002-new")
        p = d / "phase" / "001-linkage.md"
        p.write_text(p.read_text().replace("P-O1.1", "P-O9.9"))
        self.assertIn("linkage-kr-exists", self.rules(d))


if __name__ == "__main__":
    unittest.main()
