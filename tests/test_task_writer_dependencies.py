"""Task-writer contract tests, split for module-level parallelism."""

from __future__ import annotations

COVERS = ("bin/perry-task", "reference/i18n.md")

import json
from kernel_work_support import ACTOR, ready, task
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
        p.seed_task("TASK-001", title="temporary name", priority="P0", status="done",
                    evidence="e.md", verification="V3")
        (p.root / ".perry/events.jsonl").write_text(json.dumps({
            "event": "done", "id": "TASK-001", "title": "temporary name",
            "to": "done", "evidence": "e.md", "rung": "V3",
            "ts": "2026-09-01T00:00:00Z", "actor": "fixture"}) + "\n")
        self.assertNotIn("| TASK-001 |", p.board())
        return p, "TASK-001"

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
        p.seed_task("TASK-001", title="x", priority="P0")
        a = {"id": "TASK-001"}
        self.blank_the_title(p, a["id"])
        _, payload = p.run("list")
        self.assertEqual([a["id"]], payload["untitled"])

    def test_a_titled_project_reports_nothing(self):
        """The check must not have become an unconditional warning."""
        p, tid = self.closed_row()
        _, payload = p.run("list")
        self.assertEqual([], payload["untitled"])

    # ── half two: the writer reaches it ───────────────────────────────────

    def test_native_terminal_title_can_be_corrected_without_reopening(self):
        sb = ready(self)
        tid = task(sb)
        sb.move(tid, "done", set={"evidence": "proof.md"})
        before = sb.get(tid)["fields"]
        sb.ok("item update", data={"actor": ACTOR, "id": tid, "set": {"title": "Corrected name"}})
        after = sb.get(tid)
        self.assertEqual(after["state"], "done")
        self.assertEqual(after["fields"]["title"], "Corrected name")
        self.assertEqual({k: v for k, v in before.items() if k != "title"},
                         {k: v for k, v in after["fields"].items() if k != "title"})
        # Earlier event payloads remain historical facts, not overwritten titles.
        self.assertEqual(sb.events(items=[tid])[0]["changes"][0]["key"], "type")


class TestNativeDependencies(unittest.TestCase):
    def test_blocking_relation_is_visible_on_both_ends_and_survives_satisfaction(self):
        sb = ready(self)
        blocker, dependent = task(sb), task(sb)
        edge = {"kind": "blocks", "from": blocker, "to": dependent}
        sb.ok("rel add", data={"actor": ACTOR, **edge})
        self.assertEqual(sb.get(dependent)["blocked_by"], [blocker])
        self.assertFalse(sb.get(dependent)["startable"])
        for end in (blocker, dependent):
            self.assertIn(edge, sb.get(end)["relations"])
        sb.move(blocker, "done", set={"evidence": "proof.md"})
        self.assertEqual(sb.get(dependent)["blocked_by"], [])
        self.assertTrue(sb.get(dependent)["startable"])
        self.assertIn(edge, sb.get(dependent)["relations"])

    def test_an_edge_can_be_added_to_an_already_terminal_item(self):
        sb = ready(self)
        blocker, dependent = task(sb), task(sb)
        sb.move(blocker, "drop", set={"reason": "user removed scope"})
        sb.ok("rel add", data={"actor": ACTOR, "kind": "blocks", "from": blocker, "to": dependent})
        self.assertEqual(sb.get(dependent)["blocked_by"], [])
        self.assertTrue(sb.get(dependent)["startable"])

    def test_dependencies_are_one_hop(self):
        sb = ready(self)
        a, b, c = task(sb), task(sb), task(sb)
        for src, dst in ((c, b), (b, a)):
            sb.ok("rel add", data={"actor": ACTOR, "kind": "blocks", "from": src, "to": dst})
        self.assertEqual(sb.get(a)["blocked_by"], [b])
        sb.move(b, "done", set={"evidence": "proof.md"})
        self.assertEqual(sb.get(a)["blocked_by"], [])
        self.assertEqual(sb.get(b)["blocked_by"], [c])

    def test_self_cycle_and_unknown_ids_refuse_without_a_partial_edge(self):
        sb = ready(self)
        a, b = task(sb), task(sb)
        sb.ok("rel add", data={"actor": ACTOR, "kind": "blocks", "from": a, "to": b})
        before = sb.seq()
        for src, dst in ((b, a), (a, a), ("TASK-404", a)):
            out = sb.run("rel add", data={"actor": ACTOR, "kind": "blocks", "from": src, "to": dst})
            self.assertFalse(out.ok, out)
            self.assertEqual(sb.seq(), before)
        self.assertEqual(sb.get(a)["relations"], [{"kind": "blocks", "from": a, "to": b}])

    def test_add_and_remove_are_idempotent_and_preserve_history(self):
        sb = ready(self)
        a, b = task(sb), task(sb)
        edge = {"actor": ACTOR, "kind": "blocks", "from": a, "to": b}
        sb.ok("rel add", data=edge)
        before = sb.seq()
        out = sb.run("rel add", data=edge)
        self.assertEqual(out.env["effect"], "unchanged", out)
        self.assertEqual(sb.seq(), before)
        sb.ok("rel remove", data=edge)
        self.assertEqual(sb.get(b)["relations"], [])
        self.assertEqual(sb.get(b)["blocked_by"], [])
        self.assertEqual(sb.events()[-1]["changes"][0]["after"], False)


class TestLegacyDependencyReader(unittest.TestCase):
    def payload(self, rows, *flags):
        p = Project()
        for n, row in enumerate(rows, 1):
            p.seed_task(f"TASK-{n:03}", **row)
        code, result = p.run("list", "--all", *flags)
        self.assertEqual(code, 0, result)
        return result

    def test_reverse_edges_and_unknown_edges_are_both_reported(self):
        out = self.payload([{}, {"depends_on": ["TASK-001", "TASK-404"]}])
        by = {r["id"]: r for r in out["tasks"]}
        self.assertEqual(by["TASK-001"]["blocks"], ["TASK-002"])
        self.assertEqual(by["TASK-002"]["blocked_by"], ["TASK-001", "TASK-404"])
        self.assertEqual(out["conformance"]["depends_on_unknown"],
                         [{"id": "TASK-002", "unknown": ["TASK-404"]}])

    def test_closed_dependencies_stay_declared_but_stop_blocking(self):
        out = self.payload([{"status": "done"}, {"depends_on": ["TASK-001"]}])
        row = next(r for r in out["tasks"] if r["id"] == "TASK-002")
        self.assertEqual(row["depends_on"], ["TASK-001"])
        self.assertEqual(row["blocked_by"], [])
        self.assertTrue(row["startable"])

    def test_status_waits_and_unknown_dependencies_remain_distinct(self):
        out = self.payload([{"status": "blocked"}, {}, {"status": "review"},
                            {"status": "done"}, {"depends_on": ["TASK-404"]}])
        by = {r["id"]: r for r in out["tasks"]}
        self.assertEqual([by[f"TASK-{n:03}"]["startable"] for n in range(1, 6)],
                         [False, True, False, False, False])
        self.assertEqual(out["conformance"]["blocked_without_dependency"], ["TASK-001"])

    def test_one_hop_and_cycle_reports_survive_legacy_import(self):
        out = self.payload([{"depends_on": ["TASK-002"]}, {"depends_on": ["TASK-003"]}, {}])
        self.assertEqual(out["tasks"][0]["blocked_by"], ["TASK-002"])
        cycle = self.payload([{"depends_on": ["TASK-002"]}, {"depends_on": ["TASK-001"]}])
        self.assertTrue(cycle["conformance"]["dependency_cycles"])

    def test_reverse_edges_are_computed_before_track_filtering(self):
        out = self.payload([{"track": "main"}, {"track": "intake", "depends_on": ["TASK-001"]}],
                           "--track", "main")
        self.assertEqual([r["id"] for r in out["tasks"]], ["TASK-001"])
        self.assertEqual(out["tasks"][0]["blocks"], ["TASK-002"])


if __name__ == "__main__":
    unittest.main()
