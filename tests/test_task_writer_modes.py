"""Task-writer contract tests, split for module-level parallelism."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from task_writer_support import (
    BASIC_MODE_TRACKS, BOARD, MODE_TRACKS, PERRY_HOME, PT, Project,
    ROUND_TRIP_BOARD, ROUND_TRIP_ROW_IDS, ROUND_TRIP_ROW_PRIORITIES, TASKS,
    TOOL, ZH_BOARD, mode_cells,
)

class TestModeColumns(unittest.TestCase):
    """The container creation four review rounds kept finding missing."""

    TRACKS = ("\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| core | project | phase/ | — | — | — | — | V3 |\n"
              "| blog | pipeline | commitments | brief->draft->published | review:2 | 5d | 2026-W34 | V5 |\n"
              "| ops | queue | commitments | new->triaged->resolved | — | 5d | monthly | V2 |\n"
              "| study | inquiry | questions | open->researching->answered | open:5 | — | — | V4 |\n")

    def test_a_project_track_adds_no_columns(self):
        """DESIGN-003 goal 7: declaring nothing costs nothing."""
        p = Project(tracks=self.TRACKS)
        p.run("add", "--title", "X", "--track", "core")
        header = [l for l in p.board().split("\n") if l.startswith("| ID |")][0]
        self.assertNotIn("Stage", header)
        self.assertNotIn("Track", header)

    def test_a_pipeline_track_gets_stage_and_its_clock(self):
        p = Project(tracks=self.TRACKS)
        p.run("add", "--title", "X", "--track", "blog", "--priority", "P0")
        board = p.board()
        header = [l for l in board.split("\n") if l.startswith("| ID |")][0]
        for col in ("Track", "Stage", "Stage since"):
            self.assertIn(col, header, f"{col} was not created")
        row = [l for l in board.split("\n") if l.startswith("| TASK-001 |")][0]
        self.assertIn("brief", row, "Stage was not set to the first declared stage")

    def test_a_queue_track_gets_arrived_not_stage_since(self):
        p = Project(tracks=self.TRACKS)
        p.run("add", "--title", "X", "--track", "ops", "--priority", "P0")
        header = [l for l in p.board().split("\n") if l.startswith("| ID |")][0]
        self.assertIn("Arrived", header)
        self.assertNotIn("Stage since", header)

    def test_an_inquiry_track_gets_parent(self):
        p = Project(tracks=self.TRACKS)
        p.run("add", "--title", "Q", "--track", "study", "--priority", "P0",
              "--parent", "TASK-000")
        header = [l for l in p.board().split("\n") if l.startswith("| ID |")][0]
        self.assertIn("Parent", header)

    def test_adding_a_column_preserves_every_existing_row(self):
        """The rows that were there before must not lose data when the header
        grows — they gain an empty cell, not a shifted one."""
        p = Project(tracks=self.TRACKS)
        p.run("add", "--title", "plain one", "--track", "core", "--priority", "P0")
        p.run("add", "--title", "mode one", "--track", "blog", "--priority", "P0")
        rows = [l for l in p.board().split("\n") if l.startswith("| TASK-")]
        header = [l for l in p.board().split("\n") if l.startswith("| ID |")][0]
        width = len(PT.split_row(header))
        for r in rows:
            self.assertEqual(len(PT.split_row(r)), width,
                             f"row width diverged from the header:\n  {r}")
        self.assertIn("plain one", p.board())

    def test_an_undeclared_track_is_refused(self):
        p = Project(tracks=self.TRACKS)
        code, out = p.run("add", "--title", "X", "--track", "nope")
        self.assertEqual(code, 1)
        self.assertIn("nope", str(out))


class TestModeAwareWrites(unittest.TestCase):
    """`stage`, `intake`, `route` — the operations DESIGN-003's modes describe
    and nothing could perform.

    Each closes a specific review finding that survived because the rule lived
    in prose: the stage clock nothing wound (round 3, N1), the arrival date the
    routing procedure dropped (round 4, B2), and the `## Intake` section nothing
    created (round 4, F2).
    """

    TRACKS = ("\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| core | project | phase/ | — | — | — | — | V3 |\n"
              "| blog | pipeline | commitments | brief->draft->review->published | review:2 | 5d | 2026-W34 | V5 |\n"
              "| ops | queue | commitments | new->triaged->in_progress->resolved | — | 5d | monthly | V2 |\n"
              "| study | inquiry | questions | open->researching->answered | open:5 | — | — | V4 |\n")

    def cells(self, p: "Project", tid: str) -> dict:
        board = p.board()
        header = next(l for l in board.split("\n") if l.startswith("| ID |"))
        row = next(l for l in board.split("\n") if l.startswith(f"| {tid} |"))
        return dict(zip([PT.norm(h) for h in PT.split_row(header)], PT.split_row(row)))

    def test_a_stage_move_restamps_the_clock(self):
        """Status and Stage are orthogonal, so a draft→review move produces no
        status change and would otherwise leave no trace at all.

        The clock is aged first, deliberately. Asserting `stage since` is merely
        non-empty passes whether or not the move updates it — `add` already set
        it — so that assertion cannot fail on the bug it names. A mutation run
        proved exactly that: deleting the restamp left this test green. Aging
        the cell to a past date is what makes the check able to fail.
        """
        p = Project(tracks=self.TRACKS)
        _, a = p.run("add", "--title", "post", "--track", "blog", "--priority", "P0")
        self.assertEqual(self.cells(p, a["id"])["stage"], "brief")

        board = p.root / "BOARD.md"
        board.write_text(board.read_text().replace(
            self.cells(p, a["id"])["stage since"], "2020-01-01"))
        self.assertEqual(self.cells(p, a["id"])["stage since"], "2020-01-01")
        p.import_board()

        code, _ = p.run("stage", a["id"], "--stage", "draft")
        self.assertEqual(code, 0)
        c = self.cells(p, a["id"])
        self.assertEqual(c["stage"], "draft")
        self.assertNotEqual(
            c["stage since"], "2020-01-01",
            "the stage moved and the clock did not — dwell time now reads "
            "from whenever the row was created, which is the defect the "
            "column was added to fix")

    def test_a_stage_outside_the_tracks_vocabulary_is_refused(self):
        p = Project(tracks=self.TRACKS)
        _, a = p.run("add", "--title", "post", "--track", "blog", "--priority", "P0")
        code, out = p.run("stage", a["id"], "--stage", "shipped")
        self.assertEqual(code, 1)
        self.assertIn("vocabulary", str(out))

    def test_a_commitment_reaches_the_board(self):
        """Round-3 finding B3, and round-4's B2 (`Arrived` dropped at routing)
        one column further out.

        `mode_columns` was a hand-maintained per-mode list that omitted
        `Commitment`. `--commitment` was accepted, stored into `values`, and
        then dropped by `append_row`, which maps values onto headers and had no
        header to map it to — exit 0, success message, no cell. That silently
        emptied the scan `modes/queue.md` is built on: "given a commitment due
        this week, which board rows carry its id."

        The list of columns and the list of values were written down
        separately, so they drifted. `columns_for(values)` derives one from the
        other, which is why this cannot recur for a seventh column.
        """
        p = Project(tracks=self.TRACKS)
        code, out = p.run("add", "--title", "Q3 post", "--track", "blog",
                          "--priority", "P0", "--commitment", "blog/1")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.cells(p, "TASK-001").get("commitment"), "blog/1",
                         "--commitment was accepted and silently discarded")

        p.run("intake", "--title", "vendor spend")
        code, out = p.run("route", "1", "--track", "ops", "--commitment", "ops/1")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.cells(p, out["id"]).get("commitment"), "ops/1")

    def test_a_bad_stage_is_refused_at_creation_too(self):
        """`stage` validated the vocabulary from the day it shipped; `add` and
        `route` took `--stage` verbatim and exited 0.

        The vocabulary was enforced when a row *moved* and not when it was
        *born* — the one moment there is no prior value to fall back on, so the
        bad cell is what the row carries from then on. `subcommands.md` already
        promised this refusal, which made the doc the only place it existed.
        """
        p = Project(tracks=self.TRACKS)
        code, out = p.run("add", "--title", "post", "--track", "blog",
                          "--stage", "shipped", "--priority", "P0")
        self.assertEqual(code, 1, f"an out-of-vocabulary stage was written: {out}")
        self.assertIn("vocabulary", str(out))
        self.assertNotIn("post", p.board(), "a refusal wrote a row anyway")

        p.run("intake", "--title", "req")
        code, out = p.run("route", "1", "--track", "ops", "--stage", "bogus")
        self.assertEqual(code, 1, f"route wrote an out-of-vocabulary stage: {out}")

    def test_moving_to_the_same_stage_is_refused(self):
        p = Project(tracks=self.TRACKS)
        _, a = p.run("add", "--title", "post", "--track", "blog", "--priority", "P0")
        code, _ = p.run("stage", a["id"], "--stage", "brief")
        self.assertEqual(code, 1, "a no-op move would restamp the clock for nothing")

    def test_intake_creates_the_section_that_nothing_created(self):
        """`triage` step 0 gated itself on 'only applies when the section
        exists', so for every queue track ever made it no-opped forever."""
        p = Project(tracks=self.TRACKS)
        self.assertNotIn("## Intake", p.board())
        code, _ = p.run("intake", "--title", "reconcile vendor spend")
        self.assertEqual(code, 0)
        self.assertIn("## Intake", p.board())
        self.assertIn("| Arrived | Request | Outcome |", p.board())

    def test_intake_sits_above_the_work_it_becomes(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request")
        board = p.board()
        self.assertLess(board.index("## Intake"), board.index("## P0"))

    def test_routing_carries_the_arrival_date(self):
        """B2: the procedure that actually routed a row dropped the date its
        own SLA check measures, silently exempting it from the only clock
        governing it."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "vendor spend", "--arrived", "2026-08-14")
        code, out = p.run("route", "1", "--track", "ops", "--priority", "P0")
        self.assertEqual(code, 0, out)
        c = self.cells(p, out["id"])
        self.assertEqual(c["arrived"], "2026-08-14",
                         "the arrival date was replaced with today, or lost")
        self.assertEqual(c["track"], "ops")

    def test_routing_records_where_the_intake_row_went(self):
        """A request whose outcome is not written down is one that gets
        re-asked."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "vendor spend")
        _, out = p.run("route", "1", "--track", "ops")
        intake_row = next(l for l in p.board().split("\n")
                          if "vendor spend" in l and not l.startswith("| TASK-"))
        self.assertIn(out["id"], intake_row)

    def test_routing_into_a_project_track_is_refused(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "x")
        code, out = p.run("route", "1", "--track", "core")
        self.assertEqual(code, 1)
        self.assertIn("queue-mode", str(out))

    def test_routing_a_row_that_does_not_exist_is_refused(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "x")
        code, _ = p.run("route", "7", "--track", "ops")
        self.assertEqual(code, 1)

    def test_the_generated_board_still_lints(self):
        """Everything the tool writes must satisfy the schema it renders from —
        otherwise it is producing files Perry's own reader rejects."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "x", "--arrived", "2026-08-14")
        p.run("route", "1", "--track", "ops", "--priority", "P0")
        _, a = p.run("add", "--title", "post", "--track", "blog", "--priority", "P0")
        p.run("stage", a["id"], "--stage", "draft")
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-lint"),
             "--root", str(p.root)], capture_output=True, text=True)
        self.assertNotIn("error", r.stdout.split("\n")[-2].lower().replace("0 error", ""),
                         f"the tool wrote a board its own linter rejects:\n{r.stdout}")


class TestTheStageClockHasOneWriter(unittest.TestCase):
    """V4 review 2026-08-17, three blocking findings. 543 tests passed at the
    time and not one of them covered these.

    `Status` and `Stage` are orthogonal by design. Every defect here came from
    a path that forgot that.
    """

    TRACKS = MODE_TRACKS

    def cells(self, p: "Project", tid: str) -> dict:
        board = p.board()
        header = next(l for l in board.split("\n") if l.startswith("| ID |"))
        row = next(l for l in board.split("\n") if l.startswith(f"| {tid} |"))
        return dict(zip([PT.norm(h) for h in PT.split_row(header)], PT.split_row(row)))

    def age(self, p: "Project", tid: str, days_ago: str):
        b = p.root / "BOARD.md"
        b.write_text(b.read_text().replace(self.cells(p, tid)["stage since"], days_ago))
        p.import_board()

    def test_start_does_not_restamp_the_stage_clock(self):
        """B-1. `dispatch` calls `start` on every automated run, so an item
        that had sat in `review` for a fortnight reported zero days' dwell —
        blinding pipeline triage's first question, the one aimed at that
        mode's signature failure."""
        p = Project(tracks=self.TRACKS)
        _, a = p.run("add", "--title", "post", "--track", "blog", "--priority", "P0")
        self.age(p, a["id"], "2026-08-01")
        p.run("start", a["id"])
        c = self.cells(p, a["id"])
        self.assertEqual(c["stage since"], "2026-08-01",
                         "starting work moved the stage clock without the "
                         "stage changing")
        self.assertEqual(c["stage"], "brief", "the stage moved")

    def test_a_stage_move_still_restamps_it(self):
        """The other half — removing the restamp entirely would be the 2026-08
        defect the clock was added to fix."""
        p = Project(tracks=self.TRACKS)
        _, a = p.run("add", "--title", "post", "--track", "blog", "--priority", "P0")
        self.age(p, a["id"], "2020-01-01")
        p.run("stage", a["id"], "--stage", "draft")
        self.assertNotEqual(self.cells(p, a["id"])["stage since"], "2020-01-01")

    def test_stage_creates_the_column_it_writes_into(self):
        """B-2b. `replace_row` maps values onto headers, so a missing header
        discards the value and the call still exits 0."""
        p = Project(tracks=self.TRACKS, board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence | Track | Stage |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| TASK-900 | no clock | User | not_started | — | — | blog | brief |\n\n## P1", 1))
        code, out = p.run("stage", "TASK-900", "--stage", "draft")
        self.assertEqual(code, 0, out)
        self.assertIn("Stage since", p.board(), "the column was not created")
        self.assertTrue(self.cells(p, "TASK-900")["stage since"],
                        "the stamp was silently dropped")


class TestRoutingRespectsTheTracksMode(unittest.TestCase):
    """B-2a. `stages[1]` is the QUEUE rule — a queue row skips `new`, which
    means "sitting in intake", because it has just left. A pipeline or inquiry
    row has no such stage to skip, and routing them to `stages[1]` silently
    skipped `brief` / `open`."""

    TRACKS = MODE_TRACKS

    def routed(self, track: str):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request", "--arrived", "2026-08-10")
        _, r = p.run("route", "1", "--track", track, "--priority", "P1")
        board = p.board()
        header = next(l for l in board.split("\n") if l.startswith("| ID |") and "Track" in l)
        row = next(l for l in board.split("\n") if l.startswith(f"| {r['id']} |"))
        return dict(zip([PT.norm(h) for h in PT.split_row(header)], PT.split_row(row)))

    def test_a_pipeline_row_enters_at_the_first_stage(self):
        self.assertEqual(self.routed("blog")["stage"], "brief")

    def test_a_queue_row_still_skips_the_intake_stage(self):
        self.assertEqual(self.routed("ops")["stage"], "triaged")

    def test_a_pipeline_row_gets_the_clock_its_mode_reads(self):
        """Routing gave every row `Arrived` regardless, so a pipeline row
        arrived with no dwell clock — and `rows_with_no_computable_age` could
        not report it, because `arrived` was non-empty."""
        c = self.routed("blog")
        self.assertTrue(c.get("stage since"), "no dwell clock on a pipeline row")

    def test_a_queue_row_keeps_the_arrival_date(self):
        """Every SLA number is `today − Arrived`."""
        self.assertEqual(self.routed("ops")["arrived"], "2026-08-10")


class TestWritingToAProjectsOwnSections(unittest.TestCase):
    """V4 review M-8. On the only year-old real project available, `add`
    refused: "BOARD.md has no `## P1` section".

    That board files work under `## Open — 投资线` and `## Open — 工程线 ·
    phase #004`. The read side learned to see every section in 1.1; the write
    side stayed on P0/P1/P2, so arrivals could be recorded and never routed.

    Creating the missing priority section would have been the wrong fix —
    "no automatic rewrite of a project's existing structure" is an Anti-Goal,
    and a board filed by workstream is not malformed. The project says where
    the row goes instead.
    """

    WORKSTREAM = """# BOARD

## Open — 工程线

| ID | Title | Owner | Status |
|---|---|---|---|
| TECH-1 | pre-existing | Coding Agent | not_started |

## Backbone

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
"""

    def test_a_board_with_no_priority_section_is_refused_with_its_own_headings(self):
        """A refusal that names what the project actually has is the
        difference between a wall and a door."""
        p = Project(board=self.WORKSTREAM)
        code, out = p.run("add", "--title", "X")
        self.assertEqual(code, 1)
        self.assertIn("Open — 工程线", str(out), "the refusal listed no sections")
        self.assertIn("--group", str(out))

    def test_group_files_the_row_under_the_projects_own_heading(self):
        p = Project(board=self.WORKSTREAM)
        code, a = p.run("add", "--title", "new work", "--group", "Open — 工程线")
        self.assertEqual(code, 0, a)
        section = p.board().split("## Backbone")[0]
        self.assertIn(a["id"], section, "the row did not land in the named section")

    def test_a_narrower_section_gains_the_columns_rather_than_losing_the_data(self):
        """Writing only what fits would drop `Next action` silently — exactly
        how `--commitment` was lost."""
        p = Project(board=self.WORKSTREAM)
        _, a = p.run("add", "--title", "new work", "--group", "Open — 工程线",
                     "--next", "the actual next step")
        self.assertIn("the actual next step", p.board())
        old = next(l for l in p.board().split("\n") if l.startswith("| TECH-1 |"))
        header = next(l for l in p.board().split("\n") if l.startswith("| ID |"))
        self.assertEqual(len(PT.split_row(old)), len(PT.split_row(header)),
                         "an existing row was not widened with the new columns")
        self.assertIn("pre-existing", old, "existing data was disturbed")

    def test_a_heading_ending_in_punctuation_resolves(self):
        """`\\b` needs a word char on one side, so `## P2 (低优先 carry)` never
        matched and `--group` refused a section the same tool had just listed."""
        p = Project(board=self.WORKSTREAM.replace(
            "## Open — 工程线", "## P2 (低优先 carry)", 1))
        code, out = p.run("add", "--title", "X", "--group", "P2 (低优先 carry)")
        self.assertEqual(code, 0, out)

    def test_a_priority_board_is_unaffected(self):
        """The default path must not change for a project using P0/P1/P2."""
        p = Project()
        code, a = p.run("add", "--title", "X", "--priority", "P0")
        self.assertEqual(code, 0, a)
        self.assertIn(a["id"], p.board().split("## P1")[0])


class TestANarrowSectionIsWidenedWhicheverFlagNamedIt(unittest.TestCase):
    """Round-5 review B-3. The M-8 widening landed on `--group` alone.

    `add --group P1` widened a four-column section and succeeded; `add
    --priority P1` and `route --priority P1` on **the same section** refused
    with "BOARD.md's columns cannot be resolved". The board does not know which
    flag named it, so two answers is one of them being wrong — and the narrow
    case is if anything MORE likely under a priority heading, since a
    hand-written `## P2 (低优先 carry)` is the shape a project reaches for when
    it wants a short list.

    Measured on a copy of a real adopted project: `intake` wrote the row and
    `route 1 --track ops --priority P2` refused, so `## Intake` filled and could
    never be drained. TASK-020's deliverable 3 is *"`triage` gains a first step:
    drain intake"* — the routing half did not run at all.
    """

    NARROW = """# BOARD

## P1

| ID | Title | Owner | Status |
|---|---|---|---|
| TECH-1 | pre-existing | Coding Agent | not_started |
"""

    TRACKS = ("\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| ops | queue | commitments | new->triaged->resolved | — | 5d | monthly | V2 |\n")

    def widths(self, p: Project) -> tuple[str, list[str]]:
        header = next(l for l in p.board().split("\n") if l.startswith("| ID |"))
        return header, [l for l in p.board().split("\n")
                        if l.startswith(("| TECH-1 |", "| TASK-"))]

    def test_add_by_priority_widens_it_the_way_add_by_group_does(self):
        p = Project(board=self.NARROW)
        code, a = p.run("add", "--title", "new work", "--priority", "P1",
                        "--next", "the actual next step")
        self.assertEqual(code, 0, f"the priority path refused a section the "
                                  f"group path accepts: {a}")
        self.assertIn("the actual next step", p.board(),
                      "`Next action` was dropped silently")

    def test_the_two_flags_produce_the_same_header(self):
        """The claim in one assertion: same board, same section, same result."""
        by_group = Project(board=self.NARROW)
        by_group.run("add", "--title", "x", "--group", "P1", "--next", "n")
        by_priority = Project(board=self.NARROW)
        by_priority.run("add", "--title", "x", "--priority", "P1", "--next", "n")
        self.assertEqual(self.widths(by_group)[0], self.widths(by_priority)[0])

    def test_widening_pads_the_rows_that_were_already_there(self):
        p = Project(board=self.NARROW)
        p.run("add", "--title", "new work", "--priority", "P1")
        header, rows = self.widths(p)
        for r in rows:
            self.assertEqual(len(PT.split_row(r)), len(PT.split_row(header)),
                             f"row width diverged from the header:\n  {r}")
        old = next(r for r in rows if r.startswith("| TECH-1 |"))
        self.assertIn("pre-existing", old, "existing data was disturbed")
        self.assertIn("not_started", old, "a cell shifted into another column")

    def test_the_intake_drain_runs_on_a_narrow_pre_existing_board(self):
        """The end-to-end statement, and the one that was failing in the
        field: a section the tool itself creates and fills must be drainable
        onto the board the project already had."""
        p = Project(tracks=self.TRACKS, board=self.NARROW)
        code, _ = p.run("intake", "--title", "客户要对账", "--arrived", "2026-08-05")
        self.assertEqual(code, 0)
        code, out = p.run("route", "1", "--track", "ops", "--priority", "P1")
        self.assertEqual(code, 0, f"the drain refused on a board `intake` had "
                                  f"just filled: {out}")
        row = next(l for l in p.board().split("\n")
                   if l.startswith(f"| {out['id']} |"))
        self.assertIn("2026-08-05", row, "the SLA clock was lost at routing")
        self.assertIn("客户要对账", row)

    def test_an_unreadable_header_is_still_refused_not_widened(self):
        """The bound on the fix. A section whose IDENTITY columns cannot be
        resolved is not a narrow table, it is an unknown one — appending `ID`
        and `Title` beside `甲` and `乙` writes a row with two blank leading
        cells and exits 0, which is `check_header`'s reason for existing wearing
        a disguise. Both flags refuse it."""
        board = self.NARROW.replace("| ID | Title |", "| 甲 | 乙 |")
        for flag in ("--priority", "--group"):
            p = Project(board=board)
            code, out = p.run("add", "--title", "X", flag, "P1")
            self.assertEqual(code, 1, f"{flag} wrote against an unreadable "
                                      f"header: {out}")
            self.assertIn("i18n.columns", str(out))
            self.assertNotIn("TASK-001", p.board())


class TestEveryWriterThatFilesARowReadsGroup(unittest.TestCase):
    """TASK-053. `--group` parsed into `args.group` and `cmd_route` never read
    it, so the intake drain could not run on a board with no `## P0`/`## P1`/
    `## P2` at all — which is `~/proj/gimegime-pmo`'s actual shape.

    The flag was added for `cmd_add`, and `cmd_add` is where it stayed. What
    makes it worse than a missing feature is that `check_priority`'s own
    refusal recommends it — *"pass the whole heading to `--group` instead"* —
    so a user who read the refusal and did exactly what it said got refused a
    second time by the same tool.

    **Why this is a different fixture, not a stronger assertion.** The guard
    that was supposed to cover this is
    `TestANarrowSectionIsWidenedWhicheverFlagNamedIt`'s
    `test_the_intake_drain_runs_on_a_narrow_pre_existing_board`, and its board
    **has a `## P1`**. It grades narrow COLUMNS. A guard whose fixture carries
    the heading cannot fail on the heading being missing, however hard it
    asserts — the round-5 fix repaired one half of "the board does not care
    which flag named the section" and the guard was built out of the half that
    had been repaired. The category here is *a board that does not use
    priority headings*, so the fixture has none.
    """

    # `~/proj/gimegime-pmo`'s shape, minus the rows: work filed under the
    # project's own workstream headings, and not a `## P0`/`## P1`/`## P2`
    # anywhere in the file.
    WORKSTREAM = """# BOARD

## Open — 工程线 · phase #004 W24（流程层）

| ID | Title | Owner | Status |
|---|---|---|---|
| TECH-1 | pre-existing | Coding Agent | not_started |

## Backbone

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
"""
    HEADING = "Open — 工程线 · phase #004 W24（流程层）"

    TRACKS = ("\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| ops | queue | commitments | new->triaged->resolved | — | 5d "
              "| monthly | V2 |\n")

    def drained(self, *extra) -> tuple[Project, int, dict]:
        p = Project(tracks=self.TRACKS, board=self.WORKSTREAM)
        code, _ = p.run("intake", "--title", "客户要对账", "--arrived", "2026-08-05")
        self.assertEqual(code, 0)
        code, out = p.run("route", "1", "--track", "ops", *extra)
        return p, code, out

    def section_of(self, p: Project, heading: str) -> str:
        return p.board().split(f"## {heading}", 1)[1].split("\n## ", 1)[0]

    def test_route_files_the_row_under_the_projects_own_heading(self):
        """The statement of the defect. Before this, exit 1 on every form of
        the command — there was no landing site and no way to name one."""
        p, code, out = self.drained("--group", self.HEADING)
        self.assertEqual(code, 0, f"the drain refused a board that files work "
                                  f"under its own headings: {out}")
        self.assertIn(out["id"], self.section_of(p, self.HEADING),
                      "the row did not land in the section --group named")
        self.assertNotIn("## P1", p.board(),
                         "a priority section was created on a board that has none")

    def test_the_intake_table_survives_the_drain(self):
        """**The drain bricked the queue after one row, at exit 0.**

        `ensure_section` anchors `## Intake` before `## P0` *or at the end of
        the file*, so on a board with no priority heading — this fixture, and
        `~/proj/gimegime-pmo`'s actual shape — Intake lands **below** every
        landing site. `cmd_route` captured the intake row's line index, then
        `append_row` inserted above it, then wrote the outcome to the now-stale
        index: the separator row was overwritten, the request stayed
        undischarged, and the next `route` refused "`## Intake` has no table".

        Every existing test in this class passed throughout, because they only
        asserted `"routed → <id>" in board`. The corruption is one line above
        the row they were looking at.
        """
        p, code, out = self.drained("--group", self.HEADING)
        self.assertEqual(code, 0, out)
        intake = self.section_of(p, "Intake")
        self.assertRegex(intake, r"(?m)^\|\s*:?-{2,}",
                         f"the intake table lost its separator row:\n{intake}")
        rows = [l for l in intake.split("\n")
                if l.strip().startswith("|") and "---" not in l
                and not l.strip().startswith("| Arrived")]
        self.assertEqual(len(rows), 1, f"the request was duplicated:\n{intake}")
        self.assertIn("routed →", rows[0], "the request was not discharged")

    def test_a_second_drain_still_works(self):
        """The consequence, stated as the thing a user would hit. One drain
        used to leave the section unparseable, so every later arrival could be
        recorded and never routed — `triage` step 1 becomes a step that cannot
        run."""
        p, code, _ = self.drained("--group", self.HEADING)
        self.assertEqual(code, 0)
        code, _ = p.run("intake", "--title", "第二个请求", "--arrived", "2026-08-06")
        self.assertEqual(code, 0)
        code, out = p.run("route", "2", "--track", "ops", "--group", self.HEADING)
        self.assertEqual(code, 0,
                         f"the queue was bricked by the first drain: {out}")

    def test_the_routed_row_still_carries_its_clock(self):
        """`--group` must not buy the landing site by dropping `Arrived` —
        `today − Arrived` is the only clock a queue row has."""
        p, code, out = self.drained("--group", self.HEADING)
        row = next(l for l in p.board().split("\n")
                   if l.startswith(f"| {out['id']} |"))
        self.assertIn("2026-08-05", row, "the SLA clock was lost at routing")
        self.assertIn("客户要对账", row)

    def test_the_intake_row_is_discharged_by_a_grouped_route(self):
        p, code, out = self.drained("--group", self.HEADING)
        self.assertEqual(code, 0, out)
        self.assertIn(f"routed → {out['id']}", p.board())

    def test_route_reports_the_section_it_filed_into(self):
        """A caller that named a section has to be able to read back the one
        the row actually reached."""
        _, code, out = self.drained("--group", self.HEADING)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["group"], self.HEADING)
        self.assertEqual(out["priority"], "")

    def test_the_flag_the_refusal_recommends_is_the_flag_that_works(self):
        """The defect's sharpest edge, asserted as a loop rather than as two
        independent facts: take the refusal the tool gives, do exactly what it
        says, and it must not refuse again."""
        p, code, refusal = self.drained()
        self.assertEqual(code, 1, refusal)
        self.assertIn("--group", str(refusal))
        named = [h for h in (self.HEADING, "Backbone") if h in str(refusal)]
        self.assertIn(self.HEADING, named, f"refusal named no usable "
                                           f"section: {refusal}")
        code, out = p.run("route", "1", "--track", "ops", "--group", self.HEADING)
        self.assertEqual(code, 0, f"the tool refused the flag its own refusal "
                                  f"recommended: {out}")

    def test_add_and_route_reach_the_same_section_from_the_same_flag(self):
        """The category, stated once. Every subcommand that FILES A NEW ROW
        takes `--group` and means the same thing by it; a writer that reads
        `--priority` and ignores `--group` is a board Perry can write into and
        then not write into, depending on which verb you used.

        A new row-filing writer belongs in this list.
        """
        for verb in ("add", "route"):
            p = Project(tracks=self.TRACKS, board=self.WORKSTREAM)
            if verb == "add":
                code, out = p.run("add", "--title", "客户要对账",
                                  "--group", self.HEADING)
            else:
                p.run("intake", "--title", "客户要对账", "--arrived", "2026-08-05")
                code, out = p.run("route", "1", "--track", "ops",
                                  "--group", self.HEADING)
            self.assertEqual(code, 0, f"{verb} --group refused: {out}")
            self.assertIn(out["id"], self.section_of(p, self.HEADING),
                          f"{verb} filed the row somewhere else")

    def test_a_group_is_not_silently_upgraded_to_a_priority(self):
        """`route` defaulted `--priority P1` unconditionally. Keeping that
        default alongside `--group` would file the row under a heading that
        does not exist and refuse — the same failure, one line further on."""
        _, code, out = self.drained("--group", self.HEADING)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["priority"], "")

    def test_a_priority_board_routes_exactly_as_before(self):
        """The bound. A project that does use P0/P1/P2 must be untouched, and
        must still get `P1` when it names nothing."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request", "--arrived", "2026-08-05")
        code, out = p.run("route", "1", "--track", "ops")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["priority"], "P1")
        self.assertIn(out["id"], self.section_of(p, "P1"))

    def test_route_still_refuses_a_priority_that_is_not_one(self):
        """`check_priority` must keep running on the route path — it is the
        function whose refusal sends people to `--group` in the first place."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request", "--arrived", "2026-08-05")
        code, out = p.run("route", "1", "--track", "ops",
                          "--priority", "P2 (低优先 carry)")
        self.assertEqual(code, 1, out)
        self.assertIn("--group", str(out))


class TestModeColumnsOnBoardsPerryDidNotBuild(unittest.TestCase):
    """m-11: two guards could not fail on the defect they named.
    `test_arrived_survives_routing_out_of_intake` asserted a schema key and
    routed nothing; `test_add_task_sets_the_mode_columns_at_creation` grepped
    prose. The behavioural tests that existed only ever exercised **queue**
    tracks on boards **`add` had just created** — which is why B-2, the
    arrival date dropped on routing, survived a review.

    Both blind spots are the same shape as M-8: Perry's own board is the one
    board Perry never has to adapt to. These tests use a pipeline track, and a
    board written by hand with none of the mode columns present.
    """

    TRACKS = MODE_TRACKS

    #: Six standard columns, no `Stage`, no `Stage since`, no `Arrived`, no
    #: `Track` — a board that predates work modes entirely, which is every
    #: board of every project that adopts Perry.
    PREEXISTING = """# BOARD

## P0

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-900 | already here | Coding Agent | in_progress | keep going | — |

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
"""

    cells = mode_cells

    def test_add_on_a_pipeline_track_stamps_the_stage_clock(self):
        """The prose guard asserted the string `Stage since` appears in the
        triage procedure. That passes whether or not any write sets it."""
        p = Project(tracks=self.TRACKS, board=self.PREEXISTING)
        code, a = p.run("add", "--title", "post", "--track", "blog",
                        "--priority", "P0")
        self.assertEqual(code, 0, a)
        c = self.cells(p, a["id"])
        self.assertEqual(c["stage"], "brief",
                         "the row landed in no stage, so dwell time has no "
                         "start and triage's first question has no answer")
        self.assertTrue(c["stage since"],
                        "the stage clock was never wound")

    def test_the_columns_are_created_on_a_board_that_never_had_them(self):
        p = Project(tracks=self.TRACKS, board=self.PREEXISTING)
        _, a = p.run("add", "--title", "post", "--track", "blog",
                     "--priority", "P0")
        self.assertIn("stage since", self.cells(p, a["id"]))
        old = next(l for l in p.board().split("\n")
                   if l.startswith("| TASK-900 |"))
        self.assertIn("already here", old,
                      "widening the table disturbed a row that was there first")

    def test_routing_into_a_pipeline_track_carries_the_arrival_date(self):
        """The only routing test covered `ops`, a queue track. A pipeline
        track reads `Arrived` too — it is what says how long a brief sat
        before anyone picked it up."""
        p = Project(tracks=self.TRACKS, board=self.PREEXISTING)
        p.run("intake", "--title", "guest post pitch", "--arrived", "2026-08-01")
        code, out = p.run("route", "1", "--track", "blog", "--priority", "P0")
        self.assertEqual(code, 0, out)
        c = self.cells(p, out["id"])
        self.assertEqual(c["arrived"], "2026-08-01",
                         "the arrival date was replaced with today, or lost")
        self.assertEqual(c["stage"], "brief")
        self.assertTrue(c["stage since"])

    #: An `## Intake` section a human typed straight into the board: the
    #: request and nothing else. `perry-task intake` always stamps a date, so
    #: every test that had ever routed a row supplied one without meaning to.
    HAND_TYPED = PREEXISTING.replace("## P0", """## Intake

| Request | Outcome |
|---|---|
| a request someone typed in | — |

## P0""", 1)

    def test_routing_a_hand_typed_intake_row_does_not_traceback(self):
        """`values['arrived']` was read three lines after a branch that only
        sometimes sets it. On a pipeline track with no arrival date that was
        `KeyError: 'arrived'` — a traceback, not a refusal, on the one intake
        shape every adopting project already has."""
        p = Project(tracks=self.TRACKS, board=self.HAND_TYPED)
        code, out = p.run("route", "1", "--track", "blog", "--priority", "P0")
        self.assertEqual(code, 0, out)
        self.assertTrue(self.cells(p, out["id"])["stage since"],
                        "a pipeline row is measured from `Stage since`; it "
                        "has no arrival date and does not need one")

    def test_routing_one_into_a_queue_track_is_refused_not_crashed(self):
        """A queue row's only clock is `Arrived`. Filing one without a date
        creates a request that can never breach an SLA — which reads as
        compliance rather than as a gap."""
        p = Project(tracks=self.TRACKS, board=self.HAND_TYPED)
        code, out = p.run("route", "1", "--track", "ops", "--priority", "P0")
        self.assertEqual(code, 1)
        self.assertIn("--arrived", str(out), "the refusal named no way out")
        self.assertEqual(self.HAND_TYPED, p.board(),
                         "a refusal is supposed to write nothing at all")

    def test_route_accepts_the_date_the_intake_row_lacks(self):
        p = Project(tracks=self.TRACKS, board=self.HAND_TYPED)
        code, out = p.run("route", "1", "--track", "ops", "--priority", "P0",
                          "--arrived", "2026-07-04")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.cells(p, out["id"])["arrived"], "2026-07-04")

    def test_a_stage_move_restamps_the_clock_on_such_a_board(self):
        p = Project(tracks=self.TRACKS, board=self.PREEXISTING)
        _, a = p.run("add", "--title", "post", "--track", "blog",
                     "--priority", "P0")
        board = p.root / "BOARD.md"
        board.write_text(board.read_text().replace(
            self.cells(p, a["id"])["stage since"], "2020-01-01"))
        p.import_board()
        code, _ = p.run("stage", a["id"], "--stage", "draft")
        self.assertEqual(code, 0)
        self.assertNotEqual(
            self.cells(p, a["id"])["stage since"], "2020-01-01",
            "the stage moved and the clock did not, so the row reads as "
            "having sat in `draft` since 2020")


class TestDecoratedHeaders(unittest.TestCase):
    """A board whose header cells are bolded or backticked.

    Perry handles it — `squash()` strips `*` and `` ` `` before a header cell
    becomes a key — and nothing tested it. Deleting that stripping left all
    588 tests green, which is how a coverage gap announces itself: the
    behaviour is right, and nothing would notice it breaking.

    Real projects write `| **ID** | **Title** |`. Losing this makes every
    column resolve to nothing, and `add` would file rows into a table whose
    columns it could not name.
    """

    BOLD = """# BOARD

## P0

| **ID** | **Title** | **Owner** | **Status** | **Next action** | **Evidence** |
|---|---|---|---|---|---|
| TASK-900 | old | Coding Agent | not_started | — | — |
"""

    def test_a_row_can_be_added_to_a_table_with_bolded_headers(self):
        p = Project(board=self.BOLD)
        code, a = p.run("add", "--title", "new work", "--priority", "P0")
        self.assertEqual(code, 0, a)
        row = next(l for l in p.board().split("\n")
                   if l.startswith(f"| {a['id']} |"))
        self.assertEqual(
            len(PT.split_row(row)), 6,
            "the columns did not resolve, so the row was written blind")
        self.assertIn("new work", row)

    def test_the_header_is_left_exactly_as_the_project_wrote_it(self):
        p = Project(board=self.BOLD)
        p.run("add", "--title", "new work", "--priority", "P0")
        self.assertIn("| **ID** | **Title** |", p.board(),
                      "the tool rewrote a header it was only supposed to read")

    def test_an_existing_row_is_still_findable(self):
        p = Project(board=self.BOLD)
        code, _ = p.run("status", "TASK-900", "--status", "in_progress")
        self.assertEqual(code, 0)
        row = next(l for l in p.board().split("\n")
                   if l.startswith("| TASK-900 |"))
        self.assertIn("in_progress", row)

    def test_squash_drops_decoration_and_nothing_else(self):
        self.assertEqual("status", PT.squash("**Status**"))
        self.assertEqual("next action", PT.squash("`Next action`"))
        self.assertEqual("下一步", PT.squash(" **下一步** "),
                         "squash has no language knowledge and must not "
                         "touch anything that is not decoration")


class TestOneRuleOneImplementation(unittest.TestCase):
    """Round-5 review m-6, m-7, m-8 — three values with two writers each.

    Perry has hit this shape often enough to name it: two implementations of
    one rule drift silently, and a value that is both stored and derived is
    wrong for exactly the rows nobody wrote the storing path for.
    """

    TRACKS = ("\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| core | project | phase/ | — | — | — | — | V3 |\n"
              "| blog | pipeline | commitments | brief->draft->review->published | review:2 | 5d | 2026-W34 | V5 |\n"
              "| ops | queue | commitments | new->triaged->in_progress->resolved | — | 5d | monthly | V2 |\n"
              "| study | inquiry | questions | open->researching->answered | open:5 | — | — | V4 |\n")

    # -- m-6: the stage vocabulary parser

    def test_perry_task_carries_no_second_stage_parser(self):
        """`split_stages` existed twice, differing only in a loop variable,
        with the docstring explaining the normalization on one copy.

        Three spellings of the separator are in circulation (`->`, `→`, `→`
        with spaces) and "the first stage" / "the terminal stage" are both
        load-bearing, so the two copies were one edit away from disagreeing
        about where every row in a track begins and ends. Replacing
        `perry-state`'s must change `perry-task`'s answer; if it does not,
        there is a second body here.
        """
        ps = PT.perry_state()
        original = ps.split_stages
        try:
            ps.split_stages = lambda cell: ["SENTINEL"]
            self.assertEqual(
                PT.split_stages("brief->draft"), ["SENTINEL"],
                "perry-task carries its own copy of the stage parser")
        finally:
            ps.split_stages = original
        self.assertEqual(PT.split_stages("brief→draft"), ["brief", "draft"])

    def test_stages_of_consumes_the_registers_computed_list(self):
        """`parse_tracks` already computes `stage_list`; `stages_of` ignored it
        and re-split the raw cell. Two readings of one register, and nothing
        asserted they agreed."""
        track = {"track": "blog", "mode": "pipeline",
                 "stages": "this-cell->is-stale",
                 "stage_list": ["brief", "draft"]}
        self.assertEqual(PT.stages_of(PT.load_schema(), track),
                         ["brief", "draft"],
                         "the raw cell was re-parsed instead of the computed "
                         "list the register already carries")

    # -- m-7: where a row is born

    def test_the_entry_stage_rule_has_one_implementation(self):
        self.assertEqual(PT.entry_stage("queue", ["new", "triaged", "done"]),
                         "triaged", "a queue row must skip the intake stage")
        self.assertEqual(PT.entry_stage("pipeline", ["brief", "draft"]), "brief")
        self.assertEqual(PT.entry_stage("inquiry", ["open", "answered"]), "open")
        self.assertEqual(PT.entry_stage("queue", ["only"]), "only")
        self.assertEqual(PT.entry_stage("pipeline", []), "")

    def test_add_and_route_are_born_at_the_same_stage_in_every_mode(self):
        """The expression lived in `cmd_add` and in `cmd_route`, both written
        the same round. A row's entry stage is where its dwell clock starts, so
        the two disagreeing means the same work measured two ways depending on
        which command created it."""
        for track, expected in (("ops", "triaged"), ("blog", "brief"),
                                ("study", "open")):
            p = Project(tracks=self.TRACKS)
            _, a = p.run("add", "--title", "raised", "--track", track,
                         "--priority", "P0")
            p.run("intake", "--title", "arrived", "--arrived", "2026-08-01")
            code, r = p.run("route", "1", "--track", track, "--priority", "P0")
            self.assertEqual(code, 0, r)
            header = next(l for l in p.board().split("\n")
                          if l.startswith("| ID |"))
            keys = [PT.norm(h) for h in PT.split_row(header)]

            def stage_of(tid: str) -> str:
                row = next(l for l in p.board().split("\n")
                           if l.startswith(f"| {tid} |"))
                return dict(zip(keys, PT.split_row(row)))["stage"]

            self.assertEqual(stage_of(a["id"]), expected, f"{track}: add")
            self.assertEqual(stage_of(r["id"]), expected, f"{track}: route")

    # -- m-8: `mode` in the frozen list contract

    def test_mode_is_derived_from_the_track_register(self):
        """It shipped in `perry-task/list/1.4` read back out of the event log,
        so it was blank for exactly the rows `route` creates — on the one mode
        where routing is how a row is normally born."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "vendor spend", "--arrived", "2026-08-01")
        _, r = p.run("route", "1", "--track", "ops", "--priority", "P0")
        _, a = p.run("add", "--title", "post", "--track", "blog",
                     "--priority", "P0")
        _, out = p.run("list", "--all")
        modes = {t["id"]: t["mode"] for t in out["tasks"]}
        self.assertEqual(modes[r["id"]], "queue",
                         "a routed row still ships a blank mode")
        self.assertEqual(modes[a["id"]], "pipeline")

    def test_mode_survives_the_event_log_being_deleted(self):
        """The log is declared DERIVED AND DISPOSABLE at the top of
        `bin/perry-task`. Nothing in a frozen contract may depend on it for a
        value the markdown already determines."""
        p = Project(tracks=self.TRACKS)
        _, a = p.run("add", "--title", "post", "--track", "blog",
                     "--priority", "P0")
        (p.root / ".perry" / "events.jsonl").unlink()
        _, out = p.run("list", "--all")
        self.assertEqual({t["id"]: t["mode"] for t in out["tasks"]}[a["id"]],
                         "pipeline", "deleting the derived log blanked a "
                                     "value the board determines")

    def test_a_project_with_no_track_register_still_reports_project_mode(self):
        """`parse_tracks`'s own fallback: a project that never heard of tracks
        has exactly one, named `main`, mode `project`. The payload says the
        same rather than an empty string."""
        p = Project()
        _, a = p.run("add", "--title", "X", "--priority", "P0")
        _, out = p.run("list", "--all")
        self.assertEqual(out["tasks"][0]["mode"], "project")


if __name__ == "__main__":
    unittest.main()
