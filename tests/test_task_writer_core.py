"""Task-writer contract tests, split for module-level parallelism."""

from __future__ import annotations

import task_actor

COVERS = (
    "bin/perry-task",
    "bin/perry_store.py",
    "schema/state-schema.json",
    "schema/task-list-contract.md",
    "work/state/BOARD_TEMPLATE.md",
    "tests/printed_board.py",
    "perry/tasks.jsonl",
    "perry/asks.jsonl",
    "perry/risks.jsonl",
    "perry/intake.jsonl",
    ".perry/config.jsonl",
)

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from kernel_work_support import ACTOR, ready, task

import config_store
from config_store import track
from task_writer_support import (
    BASIC_MODE_TRACKS, BOARD, MODE_TRACKS, PERRY_HOME, PT, Project,
    ROUND_TRIP_BOARD, ROUND_TRIP_ROW_IDS, ROUND_TRIP_ROW_PRIORITIES, TASKS,
    TOOL, ZH_BOARD, mode_cells,
)

class TestFormatIsMechanized(unittest.TestCase):
    """V3: the tool reproduces the format, it does not redefine it."""

    def test_every_hand_written_row_in_perrys_own_board_round_trips(self):
        """The real check. Perry's board was written by hand over a whole
        session; if the tool's renderer disagrees with any of it, adopting the
        tool would silently rewrite rows the moment they were touched.

        Quantified over whatever the board holds, and over nothing else.
        `assertGreater(len(rows), 5)` used to stand at the top of it
        (TASK-151) — a proxy for "the corpus is not empty" that was really a
        census: a board that closed its way below six open rows would have
        reddened a test about ROW FORMATTING. The not-empty guard is a
        property of the reader, not of this project's backlog, so it is proved
        below on a board this module wrote.
        """
        # TASK-237 3c: this repository holds no `BOARD.md`. The corpus is the
        # board its stores print, so the rows here are tool-written; the
        # hand-written shapes are `ROUND_TRIP_BOARD`'s job below.
        from printed_board import put_printed_board
        with tempfile.TemporaryDirectory() as td:
            board = PT.Board(put_printed_board(Path(td)))
        for _, raw, _ in board.rows():
            self.assertEqual(
                PT.render_row(PT.split_row(raw)), raw,
                "the tool renders this hand-written row differently:\n"
                f"  hand: {raw}\n  tool: {PT.render_row(PT.split_row(raw))}")

    def test_the_round_trip_above_is_reading_rows_at_all(self):
        """TASK-151's other half: the loop above is vacuous over an empty list.

        `Board.rows()` walking away with nothing — a heading renamed, a
        separator the table reader stopped recognising, a priority it no
        longer maps — would leave that test green while checking no row at
        all. So the reader is held to a board whose roster is written down
        HERE, in the shapes the format actually uses: full cells, blank cells,
        the `—` marker, a pipe-free link, and a row in every section the
        walker is supposed to see.
        """
        board = PT.Board(self.write_board(ROUND_TRIP_BOARD))
        rows = board.rows()
        self.assertEqual([cells["id"] for _, _, cells in rows],
                         list(ROUND_TRIP_ROW_IDS),
                         "the reader did not find the rows this fixture "
                         "wrote — the round-trip above may be looping over "
                         "nothing")
        self.assertEqual([priority for priority, _, _ in rows],
                         list(ROUND_TRIP_ROW_PRIORITIES))
        for _, raw, _ in rows:
            self.assertEqual(
                PT.render_row(PT.split_row(raw)), raw,
                "the tool renders this row differently:\n"
                f"  hand: {raw}\n  tool: {PT.render_row(PT.split_row(raw))}")

    def write_board(self, text: str) -> Path:
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        path = Path(d.name) / "BOARD.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_the_shipped_template_round_trips_too(self):
        board = PT.Board(PERRY_HOME / "work" / "state" / "BOARD_TEMPLATE.md")
        for _, raw, _ in board.rows():
            self.assertEqual(PT.render_row(PT.split_row(raw)), raw)


class TestNativeAtomicity(unittest.TestCase):
    def test_create_is_one_event_and_failed_multifield_update_changes_nothing(self):
        sb = ready(self)
        seq = sb.seq()
        tid = task(sb)
        self.assertEqual(sb.seq(), seq + 1)
        before = sb.get(tid)
        out = sb.run("item update", data={"actor": ACTOR, "id": tid,
            "set": {"summary": "would change", "priority": "invalid"}})
        self.assertFalse(out.ok, out)
        self.assertEqual(sb.get(tid), before)
        self.assertEqual(sb.seq(), seq + 1)

    def test_native_writes_preserve_legacy_journal_and_event_bytes(self):
        sb = ready(self)
        legacy = {"journal/2026-08/2026-08-01.md": "historical journal\n",
                  ".perry/events.jsonl": "historical event stream\n"}
        for rel, body in legacy.items():
            path = sb.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
        tid = task(sb)
        sb.move(tid, "start")
        sb.move(tid, "done", set={"evidence": "proof.md"})
        for rel, body in legacy.items():
            self.assertEqual((sb.root / rel).read_text(), body)
        self.assertEqual(len(sb.events(items=[tid])), 3)

    def test_concurrent_real_cli_creates_do_not_lose_or_duplicate_ids(self):
        from concurrent.futures import ThreadPoolExecutor
        sb = ready(self)
        def create(n):
            return sb.cli("item create", data={"actor": ACTOR, "type": "task",
                "fields": {"title": f"parallel {n}", "summary": "fixture",
                           "priority": "P1", "verification": "V3"}})
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(create, range(5)))
        for out in results:
            self.assertTrue(out.ok, out)
        ids = {out.result["item"]["id"] for out in results}
        self.assertEqual(len(ids), 5)
        self.assertEqual(sb.ok("query", data={"type": "task"})["total"], 5)


class TestNativeUnicode(unittest.TestCase):
    def test_unicode_and_delimiters_survive_create_update_close(self):
        sb = ready(self)
        tid = task(sb, title="中文标题 | 原文", summary="任务说明。", next_action="下一步\n下一行")
        self.assertEqual(sb.get(tid)["fields"]["title"], "中文标题 | 原文")
        sb.ok("item update", data={"actor": ACTOR, "id": tid,
                                  "set": {"next_action": "读取 | ID | 风险 |"}})
        sb.move(tid, "done", set={"evidence": "证据/说明.md"})
        got = sb.get(tid)
        self.assertEqual(got["state"], "done")
        self.assertEqual(got["fields"]["next_action"], "读取 | ID | 风险 |")
        self.assertEqual(got["fields"]["evidence"], "证据/说明.md")


class TestNativeIdsAndValidation(unittest.TestCase):
    def test_closed_ids_are_retained_and_never_reissued(self):
        sb = ready(self)
        first = task(sb)
        sb.move(first, "done", set={"evidence": "proof.md"})
        second = task(sb)
        self.assertEqual((first, second), ("TASK-001", "TASK-002"))
        self.assertEqual(sb.get(first)["state"], "done")
        self.assertEqual(sb.ok("query", data={"type": "task"})["total"], 2)

    def test_invalid_rungs_and_priorities_leave_no_event_or_item(self):
        sb = ready(self)
        before = sb.seq()
        for field, value in (("priority", "P3"), ("verification", "V0"),
                             ("verification", "invalid")):
            fields = {"title": "label", "summary": "description", "priority": "P1",
                      "verification": "V3", field: value}
            out = sb.run("item create", data={"actor": ACTOR, "type": "task", "fields": fields})
            self.assertFalse(out.ok, out)
            self.assertEqual(sb.seq(), before)
        self.assertEqual(sb.ok("query", data={"type": "task"})["total"], 0)

    def test_done_needs_evidence_and_leaves_the_item_live_on_refusal(self):
        sb = ready(self)
        tid = task(sb)
        before = sb.get(tid)
        out = sb.run("item move", data={"actor": ACTOR, "id": tid, "transition": "done"})
        self.assertFalse(out.ok, out)
        self.assertEqual(sb.get(tid), before)
        sb.move(tid, "done", set={"evidence": "proof.md"})
        self.assertEqual(sb.get(tid)["fields"]["evidence"], "proof.md")


class TestNativeLifecycle(unittest.TestCase):
    def test_start_twice_refuses_without_adding_an_event(self):
        sb = ready(self)
        tid = task(sb)
        sb.move(tid, "start")
        seq = sb.seq()
        out = sb.run("item move", data={"actor": ACTOR, "id": tid, "transition": "start"})
        self.assertEqual(out.code_name, "transition_not_allowed", out)
        self.assertEqual(sb.seq(), seq)
        self.assertEqual(sb.get(tid)["state"], "in_progress")

    def test_close_from_not_started_and_from_review_both_retain_the_item(self):
        for submit in (False, True):
            sb = ready(self)
            tid = task(sb)
            if submit:
                sb.move(tid, "submit")
            sb.move(tid, "done", set={"evidence": "proof.md"})
            self.assertEqual(sb.get(tid)["state"], "done")
            self.assertEqual(sb.get(tid)["fields"]["verification"], "V3")


class TestJournalAppendsChronologically(unittest.TestCase):
    """A day's journal accumulates one `## Status changes` per entry.

    Appending to the first one buries an 18:33 change inside the block written
    at 09:00. Perry's own journal had seventeen such sections on the day this
    tool shipped, and the tool's first real write landed on line 12 of a
    1026-line file. An append-only record is only chronological if new lines
    land at the end of it.
    """

    MULTI = ("# 2026-08-16\n\n## Status changes\n\n- [TASK-001] a → b · early\n\n"
             "## Notes\n\nprose\n\n---\n\n## Second entry\n\n"
             "## Status changes\n\n- [TASK-002] a → b · later\n\n## Notes\n\nmore prose\n")

    def test_the_line_lands_in_the_last_section(self):
        out = PT.append_status_change(self.MULTI, "- [TASK-003] a → b · newest")
        idx_new = out.index("TASK-003")
        idx_later = out.index("TASK-002")
        self.assertGreater(idx_new, idx_later,
                           "the new line was inserted before an older one")

    def test_earlier_sections_are_untouched(self):
        out = PT.append_status_change(self.MULTI, "- [TASK-003] a → b · newest")
        head = out[:out.index("## Second entry")]
        self.assertNotIn("TASK-003", head)
        self.assertIn("TASK-001", head)

    def test_a_journal_with_no_section_gets_one(self):
        out = PT.append_status_change("# 2026-08-16\n", "- [TASK-001] a → b")
        self.assertIn("## Status changes", out)
        self.assertIn("TASK-001", out)

    def test_an_empty_journal_gets_a_heading_too(self):
        out = PT.append_status_change("", "- [TASK-001] a → b")
        self.assertTrue(out.startswith("# "))
        self.assertIn("TASK-001", out)


class TestEveryNativeStateHasAPath(unittest.TestCase):
    def test_work_states_and_reasons_are_explicit(self):
        sb = ready(self)
        tid = task(sb)
        seen = [sb.get(tid)["state"]]
        for transition, fields in (("block", {"reason": "waiting on a vendor"}),
                                   ("reset", {}), ("start", {}), ("submit", {}),
                                   ("done", {"evidence": "proof.md"})):
            sb.move(tid, transition, set=fields)
            seen.append(sb.get(tid)["state"])
        self.assertEqual(seen, ["not_started", "blocked", "not_started",
                                "in_progress", "review", "done"])
        other = task(sb)
        seq = sb.seq()
        for transition in ("block", "drop"):
            out = sb.run("item move", data={"actor": ACTOR, "id": other,
                                             "transition": transition})
            self.assertFalse(out.ok, out)
            self.assertEqual(sb.seq(), seq)
        sb.move(other, "drop", set={"reason": "user removed scope"})
        self.assertEqual(sb.get(other)["state"], "dropped")

    def test_dispatch_and_autopilot_use_native_cas_and_evidence(self):
        for name in ("dispatch", "autopilot"):
            text = (PERRY_HOME / "work/reference" / f"{name}.md").read_text()
            self.assertIn("kernel", text)
            if name == "autopilot":
                self.assertIn("dispatch.md", text)
                text = (PERRY_HOME / "work/reference/dispatch.md").read_text()
            self.assertIn("expect", text)


class TestNativeRetitle(unittest.TestCase):
    def test_update_changes_only_the_named_field_and_noop_adds_no_event(self):
        sb = ready(self)
        tid = task(sb, summary="keep this summary")
        before = sb.get(tid)["fields"]
        out = sb.ok("item update", data={"actor": ACTOR, "id": tid,
                                        "set": {"title": "Clearer name"}})
        after = sb.get(tid)["fields"]
        self.assertEqual(after["title"], "Clearer name")
        self.assertEqual({k: v for k, v in before.items() if k != "title"},
                         {k: v for k, v in after.items() if k != "title"})
        seq = sb.seq()
        same = sb.run("item update", data={"actor": ACTOR, "id": tid,
                                           "set": {"title": "Clearer name"}})
        self.assertTrue(same.ok, same)
        self.assertEqual(same.env["effect"], "unchanged")
        self.assertEqual(sb.seq(), seq)


class TestNativePriority(unittest.TestCase):
    def test_create_and_update_share_the_closed_priority_enum(self):
        sb = ready(self)
        tid = task(sb)
        for value in ("P0", "P1", "P2"):
            sb.ok("item update", data={"actor": ACTOR, "id": tid, "set": {"priority": value}})
            self.assertEqual(sb.get(tid)["fields"]["priority"], value)
        for value in ("P3", "P2 (低优先 carry)", "Release train"):
            before = sb.seq()
            out = sb.run("item update", data={"actor": ACTOR, "id": tid,
                                              "set": {"priority": value}})
            self.assertFalse(out.ok, out)
            self.assertEqual(sb.seq(), before)


class TestNativeRungCorrection(unittest.TestCase):
    def test_selected_rung_is_stored_and_correctable_without_closing(self):
        sb = ready(self)
        tid = task(sb, verification="V4")
        sb.ok("item update", data={"actor": ACTOR, "id": tid, "set": {"verification": "V5"}})
        got = sb.get(tid)
        self.assertEqual(got["fields"]["verification"], "V5")
        self.assertEqual(got["state"], "not_started")
        before = sb.seq()
        out = sb.run("item move", data={"actor": ACTOR, "id": tid, "transition": "done",
                                        "set": {"evidence": "proof.md"}})
        self.assertFalse(out.ok, out)
        self.assertEqual(sb.seq(), before)


class TestNativeRungIsChosenAtCreate(unittest.TestCase):
    def test_create_refuses_missing_and_blank_rungs_without_mode_defaults(self):
        sb = ready(self)
        before = sb.seq()
        for value in (None, "", "—", "V0"):
            fields = {"title": "label", "summary": "description", "priority": "P1"}
            if value is not None:
                fields["verification"] = value
            out = sb.run("item create", data={"actor": ACTOR, "type": "task", "fields": fields})
            self.assertFalse(out.ok, out)
            self.assertEqual(sb.seq(), before)


class TestTheDelimiterIsACharacterPeopleWrite(unittest.TestCase):
    """`render_row` joined on `|` and escaped nothing, so a cell whose value
    contained a pipe silently became several cells and shifted every column
    after it.

    Not hypothetical: filing a task whose `Next action` quoted a markdown
    header — `` | ID | **Risk** | Opened | Status | `` — turned a 7-cell row
    into a 12-cell row on Perry's own board and pushed the word `Risk` into
    the `Verification` column, where the enum check caught it.

    Two things that make this worse than an ordinary escaping bug, and both
    are asserted below:

    - the corruption **survives** later tool writes. A row is read back with
      `dict(zip(header, cells))`, and a shifted row zips without complaint, so
      the wrong values are read as right and written out again.
    - nothing upstream refuses. The value is the user's prose; the delimiter is
      a character prose contains.
    """

    def test_a_pipe_in_a_value_round_trips(self):
        for cells in (["a", "b | c", "d"],
                      ["a", "|leading", "trailing|"],
                      ["a", "b || c", "d"]):
            with self.subTest(cells=cells):
                self.assertEqual(cells, PT.split_row(PT.render_row(cells)))

    def test_a_row_keeps_its_column_count(self):
        line = PT.render_row(["TASK-001", "quoting | ID | Title |", "Coding Agent"])
        self.assertEqual(3, len(PT.split_row(line)),
                         "a value containing the delimiter became extra cells")

    def test_an_already_escaped_pipe_is_not_double_escaped(self):
        """Reading a hand-written row that already uses markdown's `\\|` and
        writing it back must not grow a second backslash each time."""
        once = PT.render_row(PT.split_row(r"| a | b \| c | d |"))
        twice = PT.render_row(PT.split_row(once))
        self.assertEqual(once, twice, "escaping is not idempotent")

    def test_a_pipe_survives_native_fields_and_the_legacy_reader(self):
        text = "see | ID | Title | Owner | in the board"
        sb = ready(self)
        tid = task(sb, next_action=text)
        self.assertEqual(sb.get(tid)["fields"]["next_action"], text)
        p = Project()
        p.seed_task("TASK-001", next_action=text)
        board = p.board()
        header = next(l for l in board.splitlines() if l.startswith("| ID |"))
        row = next(l for l in board.splitlines() if l.startswith("| TASK-001 |"))
        self.assertEqual(len(PT.split_row(header)), len(PT.split_row(row)))
        self.assertIn(text, PT.split_row(row))


class TestNativeFieldUpdates(unittest.TestCase):
    def test_each_field_changes_alone_and_records_its_key(self):
        sb = ready(self)
        tid = task(sb)
        for name, value in (("next_action", "a next step"), ("title", "Clear name"),
                            ("verification", "V4"), ("evidence", "proof.md")):
            with self.subTest(field=name):
                before = sb.get(tid)["fields"]
                sb.ok("item update", data={"actor": ACTOR, "id": tid, "set": {name: value}})
                after = sb.get(tid)["fields"]
                self.assertEqual(after[name], value)
                self.assertEqual({k: v for k, v in before.items() if k != name},
                                 {k: v for k, v in after.items() if k != name})
                self.assertEqual([c["key"] for c in sb.events()[-1]["changes"]], ["field:" + name])
                self.assertEqual(sb.get(tid)["state"], "not_started")


if __name__ == "__main__":
    unittest.main()
