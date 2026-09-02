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

class TestAClosedRowKeepsItsName(unittest.TestCase):
    """TASK-166. `TASK-029` on this repository is `done`, at `V3`, with real
    evidence, and has no title — and until this row landed, nothing reported it
    and nothing could repair it.

    **The two halves were one shape.** The `untitled` check read the rows
    AFTER they had been filtered to `open`, so the only kind of row that can be
    permanently untitled was the one kind it could not see; and `retitle` is a
    `cell_writer`, which edits a BOARD row, and closing a row REMOVES it from
    the board. The check only looked where the writer could reach, and the
    writer only reached where the check already looked. Fixing either alone is
    worse than fixing neither: a reported row nobody can repair is a permanent
    warning, and a repair path nobody is told to use is dead code.

    **Why `title` and not the other cells.** Every other cell `cell_writer`
    writes is a claim ABOUT the work — where it got to, what is next, who
    checked it, what they checked — and a claim about finished work is finished
    with it. That is why `next` refuses a terminal row on purpose. The title is
    the row's NAME: `reference/user-load.md` forbids handing a reader a bare
    id, and a name is needed for exactly as long as anybody reads the record.
    """

    #: A board that has already let a finished row go — which is what `done`
    #: does, and therefore the state every closed row on a real project is in.
    #: The record survives in `tasks.jsonl`; the projection line does not.
    def closed_row(self) -> tuple[Project, str]:
        p = Project()
        _, a = p.run("add", "--title", "temporary name", "--priority", "P0")
        code, out = p.run("done", a["id"], "--evidence", "e.md", "--rung", "V3")
        self.assertEqual(code, 0, out)
        self.assertNotIn(f"| {a['id']} ", p.board(),
                         "the fixture is wrong: closing did not remove the row")
        return p, a["id"]

    def record(self, p, tid) -> dict:
        text = (p.root / "tasks.jsonl").read_text()
        return next(json.loads(l) for l in text.splitlines()
                    if l.strip() and json.loads(l)["id"] == tid)

    def blank_the_title(self, p, tid) -> None:
        """Reproduce `TASK-029`'s state: a closed record with an empty title.

        Written by hand into the store because no tool path can produce it any
        more — which is the point. It arrived through a migration that no
        longer runs (see `perry/evidence/2026-08/TASK-166-result.md`), and the
        row it left behind still has to be repairable.
        """
        path = p.root / "tasks.jsonl"
        out = []
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["id"] == tid:
                rec["title"] = ""
            out.append(json.dumps(rec, ensure_ascii=False))
        path.write_text("\n".join(out) + "\n")

    # ── half one: the check sees it ───────────────────────────────────────

    def test_an_untitled_closed_row_is_reported_without_all(self):
        """The measurement that opened the row: `untitled` was `[]` on a
        default call and named the row only under `--all` — the flag a triage
        does not pass, on the rows a triage will never look at again."""
        p, tid = self.closed_row()
        self.blank_the_title(p, tid)
        _, default = p.run("list")
        self.assertIn(tid, default["untitled"],
                      "a closed row with no title is invisible again")
        _, everything = p.run("list", "--all")
        self.assertEqual(default["untitled"], everything["untitled"],
                         "the finding still moves with the flag")

    def test_the_finding_is_not_a_caption_for_the_listing(self):
        """`untitled` names rows that are NOT in `tasks[]` on a default call.
        That is deliberate: it is a finding about the project, not a legend for
        the rows on screen, and the human printer reads the same key."""
        p, tid = self.closed_row()
        self.blank_the_title(p, tid)
        _, payload = p.run("list")
        self.assertNotIn(tid, [t["id"] for t in payload["tasks"]])
        self.assertIn(tid, payload["untitled"])
        r = subprocess.run(["python3", str(TOOL), "list", "--root",
                            str(p.root)], capture_output=True, text=True)
        self.assertIn(tid, r.stdout,
                      "the surface a human reads still hides it")

    def test_an_open_untitled_row_is_still_reported(self):
        """The half of the check that already worked must keep working."""
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0")
        self.blank_the_title(p, a["id"])
        _, payload = p.run("list")
        self.assertEqual([a["id"]], payload["untitled"])

    def test_a_titled_project_reports_nothing(self):
        """The check must not have become an unconditional warning."""
        p, tid = self.closed_row()
        _, payload = p.run("list")
        self.assertEqual([], payload["untitled"])

    # ── half two: the writer reaches it ───────────────────────────────────

    def test_retitle_repairs_a_row_the_board_has_let_go_of(self):
        p, tid = self.closed_row()
        self.blank_the_title(p, tid)
        code, out = p.run("retitle", tid, "--title", "the name it had")
        self.assertEqual(code, 0, out)
        self.assertEqual("the name it had", self.record(p, tid)["title"])
        _, payload = p.run("list")
        self.assertEqual([], payload["untitled"],
                         "repaired and still reported")

    def test_the_repair_leaves_the_row_closed_at_its_rung(self):
        """Verification 4, from the record's side: the door reaches the row,
        and carries one field through it."""
        p, tid = self.closed_row()
        before = self.record(p, tid)
        self.assertEqual(0, p.run("retitle", tid, "--title", "clearer")[0])
        after = self.record(p, tid)
        self.assertEqual("clearer", after["title"])
        for field in [k for k in before if k != "title"]:
            self.assertEqual(before[field], after[field],
                             f"the repair also rewrote {field}")

    def test_no_other_cell_writer_reaches_a_row_off_the_board(self):
        """Verification 4, from the door's side. `off_board_repair` is passed
        by `retitle` and by nothing else; a mutation that passes it to another
        writer reddens this."""
        p, tid = self.closed_row()
        for sub, flag, value in (("next", "--next", "do more"),
                                 ("rung", "--rung", "V5"),
                                 ("evidence", "--evidence", "other.md"),
                                 ("status", "--status", "in_progress"),
                                 ("start", None, None)):
            with self.subTest(sub=sub):
                argv = (sub, tid) + ((flag, value) if flag else ())
                code, out = p.run(*argv)
                self.assertEqual(code, 1, f"{sub} reached a closed row: {out}")
                self.assertIn("not a row on the board", str(out))

    def test_next_still_refuses_a_finished_row_that_is_on_the_board(self):
        """Verification 3. The refusal this row must not weaken is not the
        board one — it is `terminal_ok`, which fires on a project that stages
        finished work in place rather than removing it."""
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
            "| TASK-900 | finished in place | User | done | — | e.md |\n\n## P1", 1))
        code, out = p.run("next", "TASK-900", "--next", "something")
        self.assertEqual(code, 1, out)
        self.assertIn("finished", str(out))
        self.assertEqual(0, p.run("retitle", "TASK-900", "--title", "named")[0],
                         "the title stopped being correctable in place")

    def test_an_open_row_missing_from_the_board_is_still_refused(self):
        """The third guard. "Not on the board" means "finished" only because
        `done` removes the row; an OPEN row that is missing from it is a stale
        projection, and repairing the record here would paper over that."""
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0")
        board = p.board()
        p_board = "\n".join(l for l in board.split("\n")
                            if not l.startswith(f"| {a['id']} "))
        (p.root / "BOARD.md").write_text(p_board)
        code, out = p.run("retitle", a["id"], "--title", "new")
        self.assertEqual(code, 1, out)
        self.assertIn("rendering failure", str(out))

    def test_the_repair_does_not_reorder_the_store(self):
        """A finished record's position is the order the work happened in.
        Rewriting a name is not a reason to move history — and the generic
        writer path appends, which would move it to the last line."""
        p, tid = self.closed_row()
        _, b = p.run("add", "--title", "later", "--priority", "P0")
        order = lambda: [json.loads(l)["id"] for l in
                         (p.root / "tasks.jsonl").read_text().splitlines()
                         if l.strip()]
        before = order()
        self.assertEqual(0, p.run("retitle", tid, "--title", "renamed")[0])
        self.assertEqual(before, order())

    def test_the_repair_is_recorded_as_a_retitle_and_carries_the_new_name(self):
        """The event log is how a later reader learns the name was repaired
        rather than never missing. `TASK-029`'s own history is why: its only
        event predates the `title` key, and that is exactly what made the
        question "never written, or written and lost?" hard to answer."""
        p, tid = self.closed_row()
        self.blank_the_title(p, tid)
        self.assertEqual(0, p.run("retitle", tid, "--title", "restored")[0])
        ev = p.events()[-1]
        self.assertEqual("retitle", ev["event"])
        self.assertEqual(tid, ev["id"])
        self.assertEqual("", ev["from"])
        self.assertEqual("restored", ev["to"])
        self.assertEqual("restored", ev["title"])
        self.assertIn(f"- [{tid}] retitled", p.journal())

    def test_a_no_op_repair_is_still_refused(self):
        p, tid = self.closed_row()
        code, out = p.run("retitle", tid, "--title", "temporary name")
        self.assertEqual(code, 1, out)
        self.assertIn("already", str(out))

    def test_an_id_nothing_knows_is_still_refused(self):
        p, _ = self.closed_row()
        code, out = p.run("retitle", "TASK-9999", "--title", "x")
        self.assertEqual(code, 1, out)
        self.assertIn("not a task", str(out))

    def test_every_event_this_tool_writes_carries_a_title(self):
        """The question TASK-166 had to answer about `TASK-029` was whether a
        write path can DROP a title. On this repository exactly one event of
        770 has no `title` key — the first line of the log, written before
        `TASK-030` added the field. This pins the answer for today's writer:
        no live path emits a task event without one, so the loss was a
        migration artefact and not a defect that can recur.
        """
        p = Project()
        _, a = p.run("add", "--title", "named", "--priority", "P0")
        p.run("start", a["id"])
        p.run("next", a["id"], "--next", "a step")
        p.run("rung", a["id"], "--rung", "V3")
        p.run("evidence", a["id"], "--evidence", "e.md")
        p.run("retitle", a["id"], "--title", "renamed")
        p.run("summary", a["id"], "--summary", "a summary")
        p.run("done", a["id"], "--evidence", "e.md", "--rung", "V3")
        p.run("retitle", a["id"], "--title", "renamed after closing")
        events = [e for e in p.events() if e.get("id", "").startswith("TASK-")]
        self.assertGreaterEqual(len(events), 9)
        for e in events:
            self.assertIn("title", e, e)
            self.assertTrue(e["title"], e)


class TestADependencyIsQueryable(unittest.TestCase):
    """TASK-063. `blocked` said a row was stopped and never said on what.

    Found by the user running `perry-task list` and seeing a pile of rows with
    no way to tell which could be advanced. Three facts made it unanswerable:
    `add --depends` wrote free text into the journal's definition block, once,
    at creation, never updatable; `status --status blocked` refused without
    `--reason` on the stated ground that "a blocked row with no named
    dependency is a row nobody can unblock" and then put that dependency into
    prose; and `subcommands.md` told triage to find "the same dependency cited
    in >= 2 rows" over data nothing could read.
    """

    def payload(self, p, *extra) -> dict:
        _, out = p.run("list", "--all", *extra)
        return out

    def task(self, p, tid, *extra) -> dict:
        return next(t for t in self.payload(p, *extra)["tasks"] if t["id"] == tid)

    def two(self, p) -> tuple[str, str]:
        _, a = p.run("add", "--title", "first", "--priority", "P0")
        _, b = p.run("add", "--title", "second", "--priority", "P0")
        return a["id"], b["id"]

    # ── the edge is on the board, not in the log ──────────────────────────

    def test_the_edge_survives_deleting_the_event_log(self):
        """The log is DERIVED AND DISPOSABLE. `mode` already cost this project
        one released contract for reading a value out of it: deleting
        `.perry/events.jsonl` blanked the field for every row on the board."""
        p = Project()
        a, b = self.two(p)
        self.assertEqual(0, p.run("depends", b, "--on", a)[0])
        (p.root / ".perry" / "events.jsonl").unlink()
        self.assertEqual([a], self.task(p, b)["depends_on"],
                         "the edge lived in the disposable half")

    def test_the_cell_is_what_the_reader_reads(self):
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        self.assertIn("Depends on", p.board())
        self.assertIn(a, p.board().split("\n")[
            next(i for i, l in enumerate(p.board().split("\n")) if l.startswith(f"| {b} "))])

    # ── the four keys ─────────────────────────────────────────────────────

    def test_blocked_by_names_the_unfinished_half_and_blocks_is_the_reverse(self):
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        self.assertEqual([a], self.task(p, b)["blocked_by"])
        self.assertEqual([b], self.task(p, a)["blocks"],
                         "closing a row does not say what it frees up")

    def test_a_satisfied_dependency_leaves_blocked_by_and_stays_in_depends_on(self):
        """Both halves matter. A dependency that vanished when it was met would
        delete the record of why the row waited; one that kept blocking would
        make `startable` never true."""
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        p.run("done", a, "--evidence", "e.md", "--rung", "V3")
        t = self.task(p, b)
        self.assertEqual([a], t["depends_on"], "the satisfied edge was erased")
        self.assertEqual([], t["blocked_by"])
        self.assertTrue(t["startable"])

    def test_a_dependency_may_point_at_a_closed_task(self):
        """It has to: `done` removes the row, so refusing ids that are no
        longer on the board would mean every satisfied dependency had to be
        deleted from the record in order to be written at all."""
        p = Project()
        a, b = self.two(p)
        p.run("done", a, "--evidence", "e.md", "--rung", "V3")
        self.assertEqual(0, p.run("depends", b, "--on", a)[0],
                         "an edge onto finished work was refused")
        self.assertEqual([], self.task(p, b)["blocked_by"])

    def test_an_id_this_payload_does_not_carry_counts_as_unsatisfied(self):
        """"I do not know" is not "it is done". Reporting such a row startable
        is the one error that sends somebody to work on something blocked."""
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", "DESIGN-006")
        t = self.task(p, b)
        self.assertEqual(["DESIGN-006"], t["blocked_by"])
        self.assertFalse(t["startable"])
        self.assertEqual([{"id": b, "unknown": ["DESIGN-006"]}],
                         self.payload(p)["conformance"]["depends_on_unknown"])

    def test_the_edge_is_one_hop_and_not_the_transitive_closure(self):
        """A waits on B, B waits on C. A's answer is B and only B — A becomes
        startable the moment B closes, and B's history is not A's business."""
        p = Project()
        _, a = p.run("add", "--title", "A", "--priority", "P0")
        _, b = p.run("add", "--title", "B", "--priority", "P0")
        _, c = p.run("add", "--title", "C", "--priority", "P0")
        p.run("depends", a["id"], "--on", b["id"])
        p.run("depends", b["id"], "--on", c["id"])
        self.assertEqual([b["id"]], self.task(p, a["id"])["blocked_by"])

    def test_blocks_is_computed_before_the_track_and_all_filters(self):
        """A row you filtered out still blocks the rows that name it. A graph
        that changed with the caller's flags would be a different graph per
        query."""
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        p.run("done", b, "--evidence", "e.md", "--rung", "V3")
        without_all = next(t for t in self.payload(p, )["tasks"] if t["id"] == a)
        _, out = p.run("list")
        live = next(t for t in out["tasks"] if t["id"] == a)
        self.assertEqual([b], live["blocks"],
                         "a closed dependant disappeared from `blocks` when "
                         "the caller asked for open work only")
        self.assertEqual([b], without_all["blocks"])

    # ── startable: the question a dashboard asks ──────────────────────────

    def test_startable_is_false_for_a_row_whose_own_status_says_it_is_waiting(self):
        """The user's actual complaint: a pile of `review` rows read as work
        that could be picked up. This holds on a board with no declared edge on
        it at all, which is every board that predates 1.6."""
        p = Project()
        a, b = self.two(p)
        p.run("status", a, "--status", "review")
        p.run("status", b, "--status", "blocked", "--reason", "waiting on Apple")
        self.assertFalse(self.task(p, a)["startable"], "a review row read as startable")
        self.assertFalse(self.task(p, b)["startable"])

    def test_startable_is_false_for_a_closed_row(self):
        p = Project()
        a, _ = self.two(p)
        p.run("done", a, "--evidence", "e.md", "--rung", "V3")
        self.assertFalse(self.task(p, a)["startable"])

    def test_startable_is_true_for_open_unblocked_work(self):
        p = Project()
        a, _ = self.two(p)
        self.assertTrue(self.task(p, a)["startable"])

    # ── cycles ────────────────────────────────────────────────────────────

    def test_a_cycle_is_refused_at_write_time(self):
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        code, out = p.run("depends", a, "--on", b)
        self.assertEqual(1, code)
        self.assertIn("cycle", out["refused"])

    def test_a_row_cannot_depend_on_itself(self):
        p = Project()
        a, _ = self.two(p)
        code, out = p.run("depends", a, "--on", a)
        self.assertEqual(1, code)
        self.assertIn("itself", out["refused"])

    def test_a_cycle_only_on_the_projection_is_not_task_truth(self):
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        p.run("depends", a, "--on", "TASK-999")
        board = p.board().replace("| TASK-999 |", f"| {b} |")
        board = board.replace("TASK-999", b)
        (p.root / "BOARD.md").write_text(board)
        d = self.payload(p)
        cycles = d["conformance"]["dependency_cycles"]
        self.assertEqual(cycles, [])
        self.assertEqual(["TASK-999"], self.task(p, a)["depends_on"])

    # ── the write paths ───────────────────────────────────────────────────

    def test_blocked_is_satisfied_by_on_as_well_as_by_reason(self):
        """The refusal was right and the answer landed in prose. `--on` makes
        the same demand and reaches the payload."""
        p = Project()
        a, b = self.two(p)
        code, _ = p.run("status", b, "--status", "blocked", "--on", a)
        self.assertEqual(0, code)
        self.assertEqual([a], self.task(p, b)["depends_on"])

    def test_blocked_with_neither_on_nor_reason_is_still_refused(self):
        p = Project()
        a, _ = self.two(p)
        code, out = p.run("status", a, "--status", "blocked")
        self.assertEqual(1, code)
        self.assertIn("unblock", out["refused"])

    def test_add_depends_writes_a_cell_and_not_only_journal_prose(self):
        p = Project()
        a, _ = self.two(p)
        _, b = p.run("add", "--title", "later", "--priority", "P0",
                     "--depends", a)
        self.assertEqual([a], self.task(p, b["id"])["depends_on"],
                         "--depends still only reached the journal")
        self.assertIn(f"- **Dependencies**: {a}", p.journal())

    def test_prose_in_the_dependency_flag_is_refused(self):
        """Free text here would rebuild, one column to the right, the very
        unreadable `- **Dependencies**: <free text>` line this replaces."""
        p = Project()
        a, _ = self.two(p)
        code, out = p.run("depends", a, "--on", "waiting for the design review")
        self.assertEqual(1, code)
        self.assertIn("not an id", out["refused"])

    def test_clear_records_that_a_row_waits_on_nothing(self):
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        self.assertEqual(0, p.run("depends", b, "--clear")[0])
        self.assertEqual([], self.task(p, b)["depends_on"])

    def test_declaring_the_same_edge_twice_is_refused_as_a_no_op(self):
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        code, _ = p.run("depends", b, "--on", a)
        self.assertEqual(1, code)

    # ── the migration worklist ────────────────────────────────────────────

    def test_a_blocked_row_with_no_declared_edge_is_named(self):
        """The honest measure of how far the backfill has got. On Perry's own
        board this is every blocked row: their dependency is prose inside
        `Next action`, where nothing can read it."""
        p = Project()
        a, b = self.two(p)
        p.run("status", a, "--status", "blocked", "--reason", "waiting on Apple")
        p.run("status", b, "--status", "blocked", "--on", a)
        c = self.payload(p)["conformance"]
        self.assertEqual([a], c["blocked_without_dependency"])

    def test_a_cell_a_project_wrote_in_its_own_language_is_read(self):
        """`reference/i18n.md`: a board may be written in the project's own
        language, and a column table that only speaks English would report
        every such row as declaring nothing — which reads as `startable`."""
        p = Project()
        a, b = self.two(p)
        board = p.board().replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n"
            "|---|---|---|---|---|---|\n"
            f"| {a} ", "| ID | Title | Owner | Status | Next action | Evidence | 依赖 |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| {a} ", 1)
        board = board.replace(f"| {a} | first | Coding Agent | not_started | — | — |",
                              f"| {a} | first | Coding Agent | not_started | — | — | {b} |")
        (p.root / "BOARD.md").write_text(board)
        p.import_board()
        self.assertEqual([b], self.task(p, a)["depends_on"],
                         "a `依赖` column was invisible to the reader")


if __name__ == "__main__":
    unittest.main()
