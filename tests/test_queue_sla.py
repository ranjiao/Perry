"""TASK-136 — the queue breach step, which is the SLA's first consumer.

`.perry/config.md § Tracks` has carried an `SLA` per queue track since work
modes shipped. `bin/perry-state` computed `stage_counts` and `wip_breaches` off
that register and nothing else, and the only reader of a track SLA **anywhere**
was `bin/lib § classify_due` — which governs a Commitments `Due` cell, not a row
clock. `today − Arrived` was computed nowhere.

TASK-135 then made the clock trustworthy: `Arrived` is carried on a queue→queue
move and cleared on the way off, on the argument that it "is not provenance, it
is a queue's clock". **So the number this project maintains correctly still had
no consumer.** That is what these tests cover.

Three answers, and keeping them apart is most of the work:

- a row **inside** its SLA — measured, not breached;
- a row **past** it — named, with its age and the promise it breaks;
- a row with **no clock at all** — a different finding, in `sla_no_clock` and
  never in `sla_breaches`, and still visible to
  `perry-task list --json § conformance.rows_with_no_computable_age`. A breach
  check that read "no `Arrived`" as "not breached" would silently merge the
  first and the third, and undo the decision `cmd_route` was changed for.

Plus the two that are not row-shaped: a track with **no** SLA reports that it
cannot run the step rather than reporting zero, and a **declared and empty**
queue track runs the step and reports zero.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from gate import GATE_OFF   # tests/gate.py — why this fixture opts out

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "bin"))
import lib  # noqa: E402

STATE = PERRY_HOME / "bin" / "perry-state"
TASK = PERRY_HOME / "bin" / "perry-task"

CONFIG = ("# Perry configuration\n\n- State root: perry\n" + GATE_OFF
          + "\n## Tracks\n\n"
          "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
          "|---|---|---|---|---|---|---|---|\n{rows}")

HEAD = ("| ID | Title | Owner | Status | Next action | Evidence | "
        "Verification | Track | Stage | Arrived | Commitment |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|\n")

#: One queue track with a five-calendar-day promise, and nothing else declared.
OPS_5D = "| ops | queue | OKR.md | — | — | 5d | 1w | V2 |\n"

TODAY = date.today()


def ago(days: int) -> str:
    return (TODAY - timedelta(days=days)).isoformat()


def row(tid: str, arrived: str, track: str = "ops",
        commitment: str = "—", status: str = "in_progress") -> str:
    return (f"| {tid} | {tid.lower()} | User | {status} | n | — | V2 | "
            f"{track} | triaged | {arrived} | {commitment} |\n")


class Base(unittest.TestCase):
    def project(self, tracks: str, board_rows: str = "") -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".perry").mkdir()
        (root / "perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            CONFIG.format(rows=tracks), encoding="utf-8")
        (root / "perry" / "BOARD.md").write_text(
            "# Board\n\n## P1\n\n" + HEAD + board_rows, encoding="utf-8")
        return root

    def state(self, root: Path) -> dict:
        r = subprocess.run([sys.executable, str(STATE), "--json",
                            "--root", str(root)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def track(self, root: Path, name: str = "ops") -> dict:
        return {t["track"]: t for t in
                self.state(root)["project"]["config"]["tracks"]}[name]

    def import_board(self, root: Path) -> None:
        """`perry-task list` reads the STORE, so a hand-written row reaches it
        only after `perry-tasks write --from-board`. `perry-state` reads the
        markdown, which is why the other tests here need no import — and why
        the cross-payload test does."""
        r = subprocess.run([sys.executable,
                            str(PERRY_HOME / "bin" / "perry-tasks"),
                            "write", "--from-board", "--root", str(root)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def task(self, root: Path, *args: str) -> dict:
        r = subprocess.run([sys.executable, str(TASK), *args,
                            "--root", str(root), "--json"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads(r.stdout)


class TestTheThreeStatesOfARowOnOneBoard(Base):
    """V3 item 1. One fixture, three answers, asserted apart from each other.

    They are separate assertions on purpose: the failure this guards against is
    two of the three collapsing into one, which no single "the list is right"
    assertion would catch.
    """

    BOARD = (row("T-INSIDE", ago(2))
             + row("T-LATE", ago(9), commitment="ops/1")
             + row("T-NOCLOCK", "—"))

    def setUp(self):
        self.root = self.project(OPS_5D, self.BOARD)
        self.tr = self.track(self.root)
        self.breached = [b["id"] for b in self.tr["sla_breaches"]]

    def test_a_row_inside_its_sla_is_measured_and_is_not_a_breach(self):
        self.assertNotIn("T-INSIDE", self.breached)
        self.assertNotIn("T-INSIDE", self.tr["sla_no_clock"])
        self.assertEqual(self.tr["sla_check"]["measured"], 2,
                         "a row with a readable clock was not measured")

    def test_a_row_past_its_sla_is_named_with_its_age(self):
        """`modes/queue.md` asks for the row "named with its age and the
        `Commitment` it breaches" — a bare id would make triage re-read the
        board the procedure forbids re-reading."""
        breach = next(b for b in self.tr["sla_breaches"] if b["id"] == "T-LATE")
        self.assertEqual(breach["arrived"], ago(9))
        self.assertEqual(breach["age_days"], 9)
        self.assertEqual(breach["over_by_days"], 4)
        self.assertEqual(breach["sla"], "5d")
        self.assertEqual(breach["commitment"], "ops/1")

    def test_a_row_with_no_clock_is_a_third_answer_not_a_pass(self):
        """The one that must not collapse. A row with no `Arrived` has no age,
        so it is neither inside its SLA nor past it — and reporting it as "not
        breached" is the silent merge this check was written to avoid."""
        self.assertEqual(self.tr["sla_no_clock"], ["T-NOCLOCK"])
        self.assertNotIn("T-NOCLOCK", self.breached)

    def test_the_three_lists_partition_the_track(self):
        """`rows` = breached + clockless + inside. Stated as arithmetic so a
        row cannot go missing from all three at once."""
        check = self.tr["sla_check"]
        self.assertEqual(check["rows"], 3)
        self.assertEqual(check["measured"], check["rows"]
                         - len(self.tr["sla_no_clock"]))
        self.assertEqual(len(self.breached), 1)


class TestTheNoClockReportThatMustKeepWorking(Base):
    """The inherited decision, asserted across BOTH payloads.

    `cmd_route` had to stop writing `Arrived` onto pipeline rows precisely so
    `conformance.rows_with_no_computable_age` could still see such rows. A
    breach check that treats a missing `Arrived` as "not breached" undoes that
    deliberately-made decision, so the property is asserted where it can
    actually break: one row, two tools, two findings.
    """

    def test_the_clockless_row_is_in_both_reports_and_neither_is_the_other(self):
        # An EMPTY cell, which is what `perry-task` itself writes for a row
        # with no arrival. The em-dash spelling is asserted separately, in
        # `TestAHandWrittenDashIsNoClockToEitherReader` below — the two readers
        # once disagreed about it, and a tool-written board could not show it.
        root = self.project(OPS_5D, row("TASK-900", ""))
        self.import_board(root)
        # A tool-written row beside it, so an event log exists — without one
        # `rows_with_no_computable_age` is deliberately empty (contract 1.9).
        self.task(root, "add", "--title", "tool written",
                  "--deliverable", "d with a test", "--verification", "v",
                  "--next", "n", "--track", "ops")

        listed = self.task(root, "list", "--all")
        self.assertIn("TASK-900",
                      listed["conformance"]["rows_with_no_computable_age"],
                      "the breach check swallowed the no-clock finding")

        tr = self.track(root)
        self.assertIn("TASK-900", tr["sla_no_clock"])
        self.assertEqual([b["id"] for b in tr["sla_breaches"]], [])

    def test_every_declared_spelling_of_an_empty_cell_is_clockless_here(self):
        """`lib § is_blank_cell` is the gate, so a hand-written `—`, `n/a` or
        `无` is as clockless as an empty cell. The breach step reads a column a
        person edits by hand, and one that only understood `""` would report a
        `—` row as inside its SLA forever."""
        for cell in ("", "—", "n/a", "无"):
            with self.subTest(cell=cell):
                tr = self.track(self.project(OPS_5D, row("T-1", cell)))
                self.assertEqual(tr["sla_no_clock"], ["T-1"])
                self.assertEqual(tr["sla_breaches"], [])


class TestAHandWrittenDashIsNoClockToEitherReader(Base):
    """TASK-163. The board column a person edits by hand, read twice.

    `perry-state § sla_no_clock` asked `lib.is_blank_cell`, so `—` was no
    clock. `perry-task § rows_with_no_computable_age` asked `not
    t["arrived"]`, and `—` is truthy, so the row had an age and the finding
    whose whole job is to say "this row has no age" said nothing. Measured:

        Arrived `—`   perry-task: not reported   perry-state: sla_no_clock
        Arrived ``    perry-task: reported       perry-state: sla_no_clock

    **Every fixture here is hand-edited, and that is the point.** `perry-task`
    writes `""` for a row with no arrival, so no board the tool produced could
    ever exhibit the disagreement — which is why it survived weeks of a suite
    that only ever asserted on tool-written rows. `import_board` is what puts a
    hand-written cell in front of `perry-task list`.

    Asserted on the SAME board, in the same test, for both tools: two
    single-tool assertions in different classes would both stay green while the
    tools disagreed, which is exactly the state this row found.
    """

    #: A hand-written em-dash, plus a tool-written row so an event log exists —
    #: without one `rows_with_no_computable_age` is empty by contract 1.9 and
    #: would pass this test for the wrong reason.
    def board(self, cell: str, tid: str = "T-DASH") -> Path:
        root = self.project(OPS_5D, row(tid, cell))
        self.import_board(root)
        self.task(root, "add", "--title", "tool written",
                  "--deliverable", "d with a test", "--verification", "v",
                  "--next", "n", "--track", "ops")
        return root

    def both(self, cell: str, tid: str = "T-DASH") -> tuple[bool, bool]:
        """(is it clockless to `perry-task`, is it clockless to `perry-state`)."""
        root = self.board(cell, tid)
        listed = self.task(root, "list", "--all")
        return (tid in listed["conformance"]["rows_with_no_computable_age"],
                tid in self.track(root)["sla_no_clock"])

    def test_a_dash_is_clockless_to_both_readers(self):
        """The row this task exists for. `not t["arrived"]` returns
        `(False, True)` here — the two tools disagreeing about one cell."""
        self.assertEqual(self.both("—"), (True, True),
                         "a hand-written `—` is a clock to one reader and not "
                         "the other")

    def test_an_empty_cell_is_clockless_to_both_readers(self):
        self.assertEqual(self.both(""), (True, True))

    def test_a_real_date_is_a_clock_to_both_readers(self):
        """Neither list, not both — the fix must not make every row clockless."""
        self.assertEqual(self.both(ago(1)), (False, False))

    def test_every_declared_spelling_of_nothing_reaches_both_readers(self):
        """`schema § i18n.blank_cell` is the vocabulary, and the point of
        reading it from the schema is that a new language is a schema edit. A
        list hardcoded in `perry-task` would pass the `—` case above and fail
        these."""
        for cell in ("—", "n/a", "无", "tbd", "-", "待定"):
            with self.subTest(cell=cell):
                self.assertTrue(lib.is_blank_cell(cell),
                                "the fixture's premise moved")
                self.assertEqual(self.both(cell), (True, True))

    def test_the_dash_row_is_still_empty_without_an_event_log(self):
        """Contract 1.9, unchanged. On a project with no event log EVERY open
        row is clockless by construction, so the array names no finding and
        stays empty — a dash does not become the exception that reopens it."""
        root = self.project(OPS_5D, row("T-DASH", "—"))
        self.import_board(root)
        listed = self.task(root, "list", "--all")
        self.assertFalse(listed["conformance"]["has_event_log"])
        self.assertEqual(listed["conformance"]["rows_with_no_computable_age"],
                         [])

    #: The standard fixture head has no `Stage since`, so a board that carries
    #: one is written here rather than assumed.
    HEAD_WITH_STAGE_SINCE = (
        "| ID | Title | Owner | Status | Next action | Evidence | "
        "Verification | Track | Stage | Stage since | Arrived | Commitment |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|\n")

    def test_a_dash_in_stage_since_is_no_clock_either(self):
        """`Stage since` is the other hand-edited date cell in the same
        predicate, and it was read with the same raw truthiness. A row whose
        date cells are BOTH dashes has no clock in either column — and if only
        `Arrived` had been fixed, this row would still read as dated."""
        root = self.project(OPS_5D)
        (root / "perry" / "BOARD.md").write_text(
            "# Board\n\n## P1\n\n" + self.HEAD_WITH_STAGE_SINCE
            + "| T-BOTH | t-both | User | in_progress | n | — | V2 | "
              "ops | triaged | — | — | — |\n", encoding="utf-8")
        self.import_board(root)
        self.task(root, "add", "--title", "tool written",
                  "--deliverable", "d with a test", "--verification", "v",
                  "--next", "n", "--track", "ops")
        listed = self.task(root, "list", "--all")
        self.assertIn("T-BOTH",
                      listed["conformance"]["rows_with_no_computable_age"],
                      "a dash in `Stage since` still read as a date")


class TestATrackWithNoSlaCannotRunTheStep(Base):
    """V3 item 2. Zero and *cannot compute* are different answers.

    `modes/queue.md` is explicit — a track without an SLA "cannot run the
    breach step, and triage reports that rather than skipping it" — and
    `schema § work_modes.modes.queue.no_default` is where the refusal to invent
    one is declared.
    """

    BARE = "| bare | queue | OKR.md | — | — | — | 1w | V2 |\n"

    def track_bare(self, rows: str = "") -> dict:
        return self.track(self.project(self.BARE, rows), "bare")

    def test_it_reports_that_it_cannot_run_rather_than_zero_breaches(self):
        tr = self.track_bare(row("T-ANCIENT", ago(400), track="bare"))
        self.assertFalse(tr["sla_check"]["runnable"])
        self.assertEqual(tr["sla_check"]["reason"], "no-sla")

    def test_it_names_the_track_and_says_it_is_not_zero(self):
        """A reader that prints rather than branches still gets the sentence,
        and the sentence says which of the two answers this is."""
        note = self.track_bare()["sla_check"]["note"]
        self.assertIn("track 'bare' declares no SLA", note)
        self.assertIn("this is not zero breaches", note)

    def test_no_fallback_sla_is_invented_for_it(self):
        """A 400-day-old row on a track with no promise is not late, because
        there is no promise to be late against."""
        tr = self.track_bare(row("T-ANCIENT", ago(400), track="bare"))
        self.assertEqual(tr["sla_breaches"], [])
        self.assertEqual(tr["sla_check"]["sla"], "—")

    def test_a_cell_that_is_not_a_duration_is_its_own_reason(self):
        """`no SLA — best effort` is what `modes/queue.md` tells a project to
        write when it has none, and `5 working days` is what a person writes
        instead of `5d`. Neither is measurable and neither is blank, so the
        step still cannot run — but the note quotes the cell rather than
        claiming the column is empty."""
        for cell in ("no SLA — best effort", "5 working days"):
            with self.subTest(cell=cell):
                tr = self.track(self.project(
                    f"| bare | queue | OKR.md | — | — | {cell} | 1w | V2 |\n",
                    row("T-ANCIENT", ago(400), track="bare")), "bare")
                self.assertFalse(tr["sla_check"]["runnable"])
                self.assertEqual(tr["sla_check"]["reason"],
                                 "sla-not-a-duration")
                self.assertIn(cell, tr["sla_check"]["note"])
                self.assertEqual(tr["sla_breaches"], [])

    def test_a_non_queue_track_says_which_step_did_not_run(self):
        """The breach step is queue mode's. A pipeline row carries no `Arrived`
        by design — `cmd_route` clears it on the way off a queue — so running
        this there would report every row as clockless, which is a finding
        about the mode rather than about the rows."""
        tr = self.track(self.project(
            "| rel | pipeline | phase/ | — | — | 5d | 2w | V3 |\n"), "rel")
        self.assertFalse(tr["sla_check"]["runnable"])
        self.assertEqual(tr["sla_check"]["reason"], "not-a-queue-track")
        self.assertEqual(tr["sla_breaches"], [])


class TestTheArithmeticIsTheBoringKind(Base):
    """V3 item 3, and the boundary is the part that has to be right."""

    def breached(self, days_old: int, sla: str = "5d") -> list[str]:
        root = self.project(
            f"| ops | queue | OKR.md | — | — | {sla} | 1w | V2 |\n",
            row("T-1", ago(days_old)))
        return [b["id"] for b in self.track(root)["sla_breaches"]]

    def test_a_row_exactly_its_sla_old_is_not_breached(self):
        """**The declared side, and the mode file declares it.** Triage step 2
        is "rows whose `today − Arrived` **exceeds** the track's `SLA`" —
        exceeds, not reaches. Five calendar days of allowance are not exceeded
        by a row that has used exactly five; it is on its last day, and calling
        that a breach would report the project late one day before it is."""
        self.assertEqual(self.breached(5), [])

    def test_one_day_past_it_is_breached(self):
        """The other side of the same boundary, so the pair pins it rather than
        one assertion permitting a whole family of thresholds."""
        self.assertEqual(self.breached(6), ["T-1"])

    def test_the_first_breaching_day_is_one_day_over_not_zero(self):
        root = self.project(OPS_5D, row("T-1", ago(6)))
        breach = self.track(root)["sla_breaches"][0]
        self.assertEqual((breach["age_days"], breach["over_by_days"]), (6, 1))

    def test_the_week_token_this_project_already_parses_is_measured(self):
        """`2w` is fourteen calendar days, on the same boundary rule."""
        self.assertEqual(self.breached(14, "2w"), [])
        self.assertEqual(self.breached(15, "2w"), ["T-1"])

    def test_the_token_has_exactly_one_reader(self):
        """**No second spelling.** `lib § SLA_TOKEN_RE` is the pattern
        `classify_due` already matches `Due` cells with; `lib § parse_sla` puts
        two groups on it and reads the same pattern. `bin/perry-state` must not
        grow a private `<n><unit>` regex — a writer and a reader with separate
        copies of one format is the shape this repository has paid for three
        times (column order, the period table, the stage separators)."""
        src = STATE.read_text(encoding="utf-8")
        self.assertIn("lib.parse_sla", src)
        self.assertNotIn("dwhmy", src)
        self.assertEqual(lib.parse_sla("5d"), (5, "d"))
        self.assertEqual(lib.parse_sla(" **2w** "), (2, "w"))
        self.assertIsNone(lib.parse_sla("5 working days"))

    def test_the_anchors_the_due_check_relies_on_survived_the_groups(self):
        """`tests/test_goals_writer.py` asserts this pattern is anchored at
        both ends — "is the WHOLE cell this" rather than "does it contain
        this". Adding capture groups must not have moved either anchor."""
        self.assertEqual(lib.SLA_TOKEN_RE.pattern[0], "^")
        self.assertEqual(lib.SLA_TOKEN_RE.pattern[-1], "$")
        self.assertTrue(lib.is_sla_token("24h"))
        self.assertFalse(lib.is_sla_token("5 days"))

    def test_a_deadline_is_calendar_arithmetic_shared_with_the_cadence_writer(self):
        """`viewer/parsers.py § advance` is the one implementation, so a month
        is a calendar month here for the same reason it is one where
        `cadence-done` stamps `Next due`."""
        self.assertEqual(lib.sla_deadline(date(2026, 1, 31), "1m"),
                         date(2026, 2, 28))
        self.assertEqual(lib.sla_deadline(date(2026, 8, 20), "5d"),
                         date(2026, 8, 25))
        self.assertEqual(lib.sla_deadline(date(2026, 8, 20), "24h"),
                         date(2026, 8, 21))
        self.assertIsNone(lib.sla_deadline(date(2026, 8, 20), "soon"))

    def test_the_oldest_breach_is_first(self):
        """The order `modes/queue.md` asks for, and the order the work should
        be picked up in."""
        root = self.project(OPS_5D, row("T-B", ago(7)) + row("T-A", ago(40)))
        self.assertEqual([b["id"] for b in self.track(root)["sla_breaches"]],
                         ["T-A", "T-B"])

    def test_a_closed_row_is_not_late(self):
        """Depth and age both count live rows only — the same definition
        `wip_report` uses, so a queue that discharges does not report a rising
        breach count forever."""
        root = self.project(OPS_5D, row("T-1", ago(90), status="done"))
        tr = self.track(root)
        self.assertEqual(tr["sla_breaches"], [])
        self.assertEqual(tr["sla_check"]["rows"], 0)

    def test_a_malformed_arrived_is_clockless_rather_than_a_crash(self):
        """`2026-02-30` matches the shape and is not a day. `lib § is_iso_date`
        is the gate for exactly that reason, and a row whose cell it rejects
        has no clock — it is not silently dated."""
        root = self.project(OPS_5D, row("T-1", "2026-02-30"))
        tr = self.track(root)
        self.assertEqual(tr["sla_no_clock"], ["T-1"])
        self.assertEqual(tr["sla_breaches"], [])


class TestADeclaredAndEmptyQueueTrack(Base):
    """V3 item 5. `intake` on this repository was declared and empty when the
    spec was written, so "no rows" is a real case and not a formality.

    **Zero is the defensible answer, and it is not the same as `runnable:
    false`.** The promise exists, the row set is empty, and nothing had to be
    guessed to say so — which is precisely the distinction a track with no SLA
    cannot make.
    """

    def test_it_runs_the_step_and_reports_zero(self):
        tr = self.track(self.project(OPS_5D))
        self.assertTrue(tr["sla_check"]["runnable"])
        self.assertEqual(tr["sla_check"]["reason"], "")
        self.assertEqual(tr["sla_breaches"], [])
        self.assertEqual(tr["sla_no_clock"], [])

    def test_and_says_it_measured_nothing_rather_than_staying_silent(self):
        """`rows: 0` is what separates "this queue is empty" from "this queue
        is fine" — two very different things to tell a review period."""
        check = self.track(self.project(OPS_5D))["sla_check"]
        self.assertEqual((check["rows"], check["measured"]), (0, 0))
        self.assertEqual(check["sla"], "5d")

    def test_an_empty_track_reads_differently_from_a_track_with_no_sla(self):
        """The whole point of item 5, asserted as the comparison it is."""
        empty = self.track(self.project(OPS_5D))["sla_check"]
        bare = self.track(self.project(
            "| bare | queue | OKR.md | — | — | — | 1w | V2 |\n"), "bare")["sla_check"]
        self.assertEqual((empty["runnable"], bare["runnable"]), (True, False))
        self.assertEqual(empty["sla_breaches"] if "sla_breaches" in empty
                         else [], [])
        self.assertNotEqual(empty["note"], bare["note"])
        self.assertEqual(empty["note"], "")


class TestTheImplicitTrackKeepsTheShape(Base):
    """Every key the declared branch produces must exist on the implicit track
    too, or a reader that works on a track-declaring project raises `KeyError`
    on an ordinary one. `DEFAULT_TRACK`'s own comment records that this shipped
    broken once already.
    """

    def test_a_project_with_no_track_register_carries_the_same_keys(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".perry").mkdir()
        (root / "perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- State root: perry\n" + GATE_OFF,
            encoding="utf-8")
        (root / "perry" / "BOARD.md").write_text(
            "# Board\n\n## P1\n\n" + HEAD, encoding="utf-8")
        tr = self.track(root, "main")
        self.assertFalse(tr["declared"])
        for key in ("sla_breaches", "sla_no_clock", "sla_check"):
            self.assertIn(key, tr)
        self.assertEqual(tr["sla_check"]["reason"], "not-a-queue-track")


class TestTheModeFileRecordsThatTheStepLanded(unittest.TestCase):
    """`modes/queue.md` said a track *without* an SLA cannot run the breach
    step. A track *with* one could not run it either, and nothing said so — a
    claim that stops being true and stays written is the defect this project
    keeps finding, so the file moves in the same change as the code.
    """

    def test_the_payload_field_is_named_where_the_step_is_declared(self):
        doc = (PERRY_HOME / "modes" / "queue.md").read_text(encoding="utf-8")
        self.assertIn("sla_breaches", doc)
        self.assertIn("sla_no_clock", doc)
        self.assertIn("sla_check", doc)


if __name__ == "__main__":
    unittest.main()
