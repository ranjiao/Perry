"""Task-writer contract tests, split for module-level parallelism."""

from __future__ import annotations

COVERS = ("bin/perry-task", "bin/perry-lint", "modes/queue.md")

import json
import os
import re
import subprocess
import tempfile
import unittest
from kernel_work_support import ACTOR, ready, task
from pathlib import Path

from config_store import track
from task_writer_support import (
    BASIC_MODE_TRACKS, BOARD, MODE_TRACKS, PERRY_HOME, PT, Project,
    ROUND_TRIP_BOARD, ROUND_TRIP_ROW_IDS, ROUND_TRIP_ROW_PRIORITIES, TASKS,
    TOOL, ZH_BOARD, mode_cells,
)

def age_in_store(p: "Project", tid: str, when: str) -> None:
    """Set one record's `stage_since` in `tasks.jsonl`, and nothing else.

    **The board-less way to age a clock** (TASK-262 round 4a). These tests
    used to rewrite the date in the held `BOARD.md` and re-import it. No write
    re-renders that file any more, so after the first `add` it carries no row
    to edit; the store is what a write reads, so the store is what is aged.
    """
    store = p.root / "tasks.jsonl"
    records = [json.loads(l) for l in store.read_text().split("\n") if l.strip()]
    hits = [r for r in records if r["id"] == tid]
    assert len(hits) == 1, (tid, len(hits))
    assert hits[0]["stage_since"], "control: the clock was wound at creation"
    hits[0]["stage_since"] = when
    store.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                             for r in records))


def stored(p: "Project", tid: str) -> dict:
    store = p.root / "tasks.jsonl"
    return next(json.loads(l) for l in store.read_text().split("\n")
                if l.strip() and json.loads(l)["id"] == tid)


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

    TRACKS = MODE_TRACKS

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


    # -- m-8: `mode` in the frozen list contract


class TestLegacyModeReadFixtures(unittest.TestCase):
    def test_all_four_declared_modes_and_their_stored_columns_survive_without_events(self):
        p = Project(tracks=MODE_TRACKS)
        for n, (track, mode, stage) in enumerate((("core", "project", ""), ("blog", "pipeline", "draft"),
                                                ("ops", "queue", "triaged"), ("study", "inquiry", "researching")), 1):
            p.seed_task(f"TASK-{n:03}", track=track, stage=stage,
                        stage_since="2026-09-01", arrived="2026-08-01")
        code, out = p.run("list", "--all")
        self.assertEqual(code, 0, out)
        self.assertEqual([(r["track"], r["mode"], r["stage"]) for r in out["tasks"]],
                         [("core", "project", ""), ("blog", "pipeline", "draft"),
                          ("ops", "queue", "triaged"), ("study", "inquiry", "researching")])
        for row in out["tasks"]:
            self.assertEqual(row["arrived"], "2026-08-01")
            self.assertEqual(row["stage_since"], "2026-09-01")
        self.assertFalse((p.root / ".perry/events.jsonl").exists())

    def test_custom_group_is_not_invented_as_a_priority(self):
        p = Project()
        p.seed_task("TASK-001", title="a grouped record", priority="", group="Release train")
        code, out = p.run("list", "--all")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["tasks"][0]["group"], "Release train")
        self.assertEqual(out["tasks"][0]["priority"], "")
        self.assertIn("## Release train", p.board())


class TestNativeModesAreRemoved(unittest.TestCase):
    def test_intake_is_a_task_track_without_stage_or_queue_clocks(self):
        sb = ready(self)
        tid = task(sb, track="intake")
        got = sb.get(tid)
        self.assertEqual(got["state"], "not_started")
        self.assertEqual(got["fields"]["track"], "intake")
        for key in ("mode", "stage", "stage_since", "arrived", "commitment", "parent"):
            self.assertNotIn(key, got["fields"])
            before = sb.seq()
            out = sb.run("item update", data={"actor": ACTOR, "id": tid, "set": {key: "invented"}})
            self.assertFalse(out.ok, out)
            self.assertEqual(sb.seq(), before)

    def test_stage_route_and_intake_commands_cannot_recreate_the_old_method(self):
        p = Project(tracks=MODE_TRACKS)
        p.seed_task("TASK-001", track="blog", stage="draft")
        before = {str(f.relative_to(p.root)): f.read_bytes() for f in p.root.rglob("*") if f.is_file()}
        for argv in (("stage", "TASK-001", "--stage", "review"),
                     ("route", "1", "--track", "ops"), ("intake", "--title", "a request")):
            code, out = p.run(*argv)
            self.assertEqual(code, 1, out)
            self.assertIn("read-only", out["refused"])
            self.assertEqual({str(f.relative_to(p.root)): f.read_bytes()
                              for f in p.root.rglob("*") if f.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
