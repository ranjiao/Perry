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

import task_actor

COVERS = (
    "bin/perry-task",
    "bin/perry-state",
    "bin/perry-lint",
    "modes/queue.md",
    "work/reference/subcommands.md",
    "schema/task-list-contract.md",
    "schema/README.md",
)

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from held_board import import_board  # noqa: E402


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
        # TASK-237 3b′: the config store makes this project installed;
        # `.perry/config.md` is deleted (ADR-019) and `BOARD.md` alone no
        # longer counts. It declares nothing the cadence register reads.
        (self.root / ".perry" / "config.jsonl").write_text(
            '{"kind": "setting", "key": "state_root", "label": "State root", '
            '"value": ".", "order": 0}\n')
        (self.root / "BOARD.md").write_text(board)

    def run(self, *argv):
        r = subprocess.run(
            task_actor.command(["python3", str(TOOL), *argv, "--root", str(self.root), "--json"], 'test_cadence'),
            capture_output=True, text=True)
        try:
            return r.returncode, json.loads(r.stdout or "{}")
        except json.JSONDecodeError:
            return r.returncode, r.stdout + r.stderr

    def seed_cadence(self, title="x", frequency="weekly", next_due="n/a", **fields):
        """Archived register input for readers, with dates declared by the test."""
        path = self.cadence_store()
        rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        row = {"id": f"CAD-{len(rows)+1:03}", "title": title, "owner": "fixture",
               "frequency": frequency, "next_due": next_due, "last_run": "",
               "last_evidence": "", "order": len(rows), **fields}
        path.write_text("".join(json.dumps(r) + "\n" for r in [*rows, row]))
        return row["id"]

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
        """What `perry-tasks board` prints from the stores (TASK-262 round 4a).

        The fixture's `BOARD.md` is the retired file a project upgraded from;
        no write reads or re-renders it, so the rows a write made are read off
        the board a reader gets. `held()` is the file itself.
        """
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-tasks"), "board",
             "--root", str(self.root)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        return r.stdout

    def held(self) -> str:
        return (self.root / "BOARD.md").read_text()

    def cadence_store(self) -> Path:
        return self.root / "cadence.jsonl"

    def import_cadence(self) -> None:
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-tasks"), "cadence-write",
             "--from-board", "--root", str(self.root)],
            capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr

    def edit_record(self, cid: str, **fields) -> None:
        """Change one stored record by hand; the store is the register."""
        store = self.cadence_store()
        recs = [json.loads(l) for l in store.read_text().split("\n") if l.strip()]
        hits = [r for r in recs if r["id"] == cid]
        assert len(hits) == 1, (cid, len(hits))
        hits[0].update(fields)
        store.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                 for r in recs))

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


class TestRetiredCadenceWrites(unittest.TestCase):
    def test_add_and_done_refuse_for_empty_imported_and_absent_sections(self):
        for board in (BOARD, BOARD_NO_SECTION):
            p = Project(board)
            p.seed_cadence("Friday review", "weekly", "2026-01-09")
            before = {str(f.relative_to(p.root)): f.read_bytes()
                      for f in p.root.rglob("*") if f.is_file()}
            for argv in (("cadence-add", "--title", "weekly review", "--frequency", "weekly"),
                         ("cadence-add", "--title", "x", "--frequency", "unknown", "--dry-run"),
                         ("cadence-done", "CAD-001", "--evidence", "proof.md"),
                         ("cadence-done", "CAD-099", "--dry-run")):
                with self.subTest(argv=argv, has_section=board == BOARD):
                    code, out = p.run(*argv)
                    self.assertEqual(code, 1, out)
                    self.assertIn("no kernel write equivalent", out["refused"])
                    self.assertEqual({str(f.relative_to(p.root)): f.read_bytes()
                                      for f in p.root.rglob("*") if f.is_file()}, before)


class TestOverdueReport(unittest.TestCase):
    def test_overdue_rows_are_reported_by_age_oldest_first(self):
        p = Project()
        for title, days in (("newer", -5), ("old", -30), ("future", 7)):
            p.seed_cadence(title, "weekly", str(TODAY + timedelta(days=days)))
        self.assertEqual([r.id for r in p.rows()], ["CAD-001", "CAD-002", "CAD-003"])
        report = p.state()
        self.assertEqual(report["count"], 3)
        self.assertEqual([r["id"] for r in report["overdue"]], ["CAD-002", "CAD-001"])
        self.assertEqual([r["days_overdue"] for r in report["overdue"]], [30, 5])

    def test_today_future_and_aperiodic_are_not_overdue(self):
        p = Project()
        p.seed_cadence("today", "weekly", str(TODAY))
        p.seed_cadence("future", "weekly", str(TODAY + timedelta(days=7)))
        p.seed_cadence("continuous", "continuous", "n/a")
        report = p.state()
        self.assertEqual(report["count"], 3)
        self.assertEqual(report["overdue"], [])
        self.assertEqual(report["undated"], [])
        self.assertEqual(report["unreadable_frequency"], [])
        self.assertEqual(report["items"][2]["frequency_kind"], "aperiodic")

    def test_unreadable_due_and_frequency_remain_distinct_findings(self):
        p = Project()
        p.seed_cadence("due unknown", "weekly", "soon")
        p.seed_cadence("frequency unknown", "每周五", "n/a")
        report = p.state()
        self.assertEqual([r["id"] for r in report["undated"]], ["CAD-001"])
        self.assertEqual([r["id"] for r in report["unreadable_frequency"]], ["CAD-002"])
        self.assertEqual(report["overdue"], [])
        self.assertIn("unreadable Frequency", p.dashboard())

    def test_fresh_historical_snapshot_clears_an_overdue_finding(self):
        p = Project()
        p.seed_cadence("weekly review", "weekly", str(TODAY - timedelta(days=23)))
        self.assertEqual(len(p.state()["overdue"]), 1)
        p.edit_record("CAD-001", next_due=str(TODAY + timedelta(days=7)),
                      last_run=str(TODAY), last_evidence="proof.md")
        self.assertEqual(p.state()["overdue"], [])

    def test_dashboard_reports_a_register_only_when_it_exists(self):
        self.assertNotIn("Cadence", Project(BOARD_NO_SECTION).dashboard())
        p = Project()
        p.seed_cadence("weekly review", "weekly", str(TODAY - timedelta(days=23)))
        self.assertIn("1 overdue", p.dashboard())


class TestCadenceIsNotATask(unittest.TestCase):
    """`schema/task-list-contract.md § What this contract does not cover`."""

    def test_cadence_rows_and_events_stay_out_of_the_list_payload(self):
        """The board half of this was always right — `_task_sections` skips the
        heading. The EVENT half folded every event carrying an id, so a
        registered ritual arrived as a closed task with `status: registered`."""
        p = Project()
        p.seed_cadence()
        p.edit_record("CAD-001", last_evidence="e.md")
        (p.root / ".perry/events.jsonl").write_text(json.dumps({
            "event": "cadence-done", "id": "CAD-001", "ts": "2026-08-01T00:00:00Z"}) + "\n")
        code, out = p.run("list", "--all")
        self.assertEqual(code, 0, out)
        self.assertEqual([t["id"] for t in out["tasks"]], [])
        self.assertEqual(out["closed"], 0)
        self.assertEqual(out["untitled"], [])

    def test_user_input_rows_stay_out_too(self):
        p = Project()
        (p.root / "asks.jsonl").write_text(json.dumps({"id": "USER-001",
            "needed": "which staging default?", "status": "pending", "order": 0}) + "\n")
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
        p.seed_cadence()
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
        p.seed_cadence()
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
            self.assertIn("read-only after the kernel cutover", msg)
            self.assertIn("perry-kernel", msg)
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
        self.assertIn("read-only after the kernel cutover", str(out))


class TestTheLegacyProjectionIsUnchanged(unittest.TestCase):
    """`BoardState.cadence` has consumers that predate `Cadence` — `all_tasks`
    and `perry-state`'s drift exclusion, which keys
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
        p.seed_cadence()
        (p.root / "tasks.jsonl").write_text("")
        (p.root / ".perry/events.jsonl").write_text(json.dumps({
            "event": "cadence-done", "id": "CAD-001", "ts": "2026-08-01T00:00:00Z"}) + "\n")
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
    naming `P001-O1-KR4` — a KR that exists exactly where it should. A guard written
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
            "|---|---|---|---|\n| P001-O1-KR1 | old work | 1 | — |\n")
        (d / "phase" / "002-new.md").write_text(
            "# Phase #002 — new\n\n> **Started**: 2026-08-19\n"
            "> **Status**: active\n\n## Objective 1 — b\n\n"
            "| Id | KR text | Metric / Target | Linked overall KR |\n"
            "|---|---|---|---|\n| P002-O1-KR9 | new work | 1 | — |\n")
        # The scored phase's records. They were `phase/001-linkage.md` until
        # ADR-019; one file holds every phase now, which is exactly why the
        # per-phase rule this class is about had to keep working.
        (d / "linkage.jsonl").write_text("".join(
            json.dumps(r) + "\n" for r in (
                {"kind": "objective", "phase": "001-old", "id": "O1",
                 "title": "a"},
                {"kind": "kr", "phase": "001-old", "objective": "O1",
                 "id": "P001-O1-KR1", "title": "old work", "metric": "1",
                 "target": 1, "current": 1, "stretch": False,
                 "asserted_at": "2026-08-01T00:00:00Z"})))
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

    def test_the_pre_migration_id_form_is_an_error_not_a_silence(self):
        """TASK-180. `KR_ID_RE` no longer matching the old form is not enough.

        Every KR guard in `check_cross_file` is written `if phase_krs and …`,
        so a phase file left in `P-O1.1` [[old-form]] yields an EMPTY KR set
        and buys
        silence from all of them — the compatibility branch the user ruled out,
        wearing a different hat. `kr-id-legacy-form` is what turns that silence
        into a sentence, and this is what holds it: deleting the check left
        every other module in the suite green.
        """
        d = self.project("002-new")
        f = d / "phase" / "001-old.md"
        f.write_text(f.read_text().replace("P001-O1-KR1",
                                           "P-O1.1"))  # [[old-form]]
        rules = self.rules(d)
        self.assertIn("kr-id-legacy-form", rules)
        self.assertNotIn("kr-id-legacy-form", self.rules(self.project("002-new")),
                         "a migrated project must be silent about the old form")

    def test_the_legacy_form_finding_is_an_error_and_names_the_new_shape(self):
        import json
        import subprocess
        import sys
        d = self.project("002-new")
        f = d / "phase" / "001-old.md"
        f.write_text(f.read_text().replace("P001-O1-KR1",
                                           "P-O1.1"))  # [[old-form]]
        proc = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-lint"),
             "--root", str(d), "--json"], capture_output=True, text=True)
        hits = [x for x in json.loads(proc.stdout)["findings"]
                if x["rule"] == "kr-id-legacy-form"]
        self.assertEqual(len(hits), 1, hits)
        self.assertEqual(hits[0]["severity"], "error")
        self.assertEqual(hits[0]["file"], "phase/001-old.md")
        self.assertIn("P-O1.1", hits[0]["message"])  # [[old-form]] echoed back
        self.assertIn("P001-O<n>-KR<n>", hits[0]["message"],
                      "the finding does not say what to write instead")

    def test_a_genuinely_wrong_kr_is_still_reported(self):
        """The guard has to keep working, or moving the KR set just turns it
        off. A registry naming a KR its OWN phase does not have is a real
        finding."""
        d = self.project("002-new")
        p = d / "linkage.jsonl"
        p.write_text(p.read_text().replace("P001-O1-KR1", "P001-O9-KR9"))
        self.assertIn("linkage-kr-exists", self.rules(d))

    def test_a_kr_belonging_to_another_phase_is_reported(self):
        """The *phase* half of the id, which the test above cannot reach.

        TASK-157 replaced `linkage-kr-exists`'s document scan with two direct
        questions about the id: does it name the objective it is declared
        under, and does it name the phase whose register it sits in. The test
        above supplies `P001-O9-KR9`, which fails only the FIRST — its phase
        is still `001` — so the phase half shipped with nothing holding it.
        Measured: deleting `if not kr.id.startswith(f"P{own}-")` from
        `bin/perry-lint` left the ENTIRE suite unchanged, which is the
        definition of a guard that is not one.

        Before this row the case was caught sideways: `001-old.md` did not
        mention `P002-O1-KR1`, so the document scan reported it. Asking the id
        directly must not lose that.
        """
        d = self.project("002-new")
        p = d / "linkage.jsonl"
        # Objective `O1` is kept, so the objective-agreement half is SILENT and
        # only the phase half can produce the finding.
        p.write_text(p.read_text().replace("P001-O1-KR1", "P002-O1-KR1"))
        rules = self.rules(d)
        self.assertIn("linkage-kr-exists", rules)

    def test_the_phase_half_names_the_phase_and_the_id(self):
        """A finding that does not say which two things disagree is a shrug."""
        import json
        import subprocess
        import sys
        d = self.project("002-new")
        p = d / "linkage.jsonl"
        p.write_text(p.read_text().replace("P001-O1-KR1", "P002-O1-KR1"))
        proc = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-lint"),
             "--root", str(d), "--json"], capture_output=True, text=True)
        hits = [x for x in json.loads(proc.stdout)["findings"]
                if x["rule"] == "linkage-kr-exists"
                and "P002-O1-KR1" in x["message"]]
        self.assertEqual(len(hits), 1, hits)
        self.assertEqual(hits[0]["file"], "linkage.jsonl")
        self.assertIn("001", hits[0]["message"],
                      "the finding does not name the phase whose register "
                      "this is")


if __name__ == "__main__":
    unittest.main()
