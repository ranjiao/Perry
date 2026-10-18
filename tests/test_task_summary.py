"""TASK-106: optional Task summaries stay explicit and typed end to end."""

from __future__ import annotations

import task_actor

COVERS = (
    "bin/perry-task",
    "bin/perry-explain",
    "schema/task-list-contract.md",
)

import json
import subprocess
import sys
import unittest
from pathlib import Path

from tests.test_store_is_the_write_target import Project, task_module

import config_store  # noqa: E402
from kernel_work_support import ACTOR, ready, task


ROOT = Path(__file__).resolve().parent.parent
EXPLAIN = ROOT / "bin" / "perry-explain"
TASK = ROOT / "bin" / "perry-task"

#: The sentinel other writers must not disturb. It is a SENTENCE rather than
#: the bare token it used to be because `add` now refuses a summary that
#: carries none (TASK-325); the token is still in it, so the assertions still
#: name exactly what they are looking for.
SENTINEL = ("SUMMARY-SENTINEL must survive every unrelated write "
            "that this row receives.")


class TaskSummaryContract(unittest.TestCase):
    def seed_summary(self, project: Project, summary: str | None = None) -> str:
        """Archived input for list/explain; no current writer is simulated."""
        store = project.root / "tasks.jsonl"
        rows = [json.loads(line) for line in store.read_text().splitlines()]
        tid = "TASK-005"
        rows.append(task_module().perry_store.record({
            "id": tid, "title": "Compact label", "priority": "P1", "track": "main",
            "group": "P1", "status": "not_started", "summary": summary or ""}, len(rows)))
        store.write_text(task_module().perry_store.store_text(rows))
        return tid

    def listed(self, project: Project, task_id: str) -> dict:
        rc, out = project.task("list", "--all")
        self.assertEqual(rc, 0, out)
        return next(task for task in out["tasks"] if task["id"] == task_id)

    def explain(self, project: Project, task_id: str, *extra: str):
        return subprocess.run(
            [sys.executable, str(EXPLAIN), task_id, "--root", str(project.root),
             *extra], capture_output=True, text=True)

    def test_shared_shape_normalizes_legacy_without_inference(self):
        store = task_module().perry_store

        self.assertIn("summary", store.STORED)
        valid, findings = store.validate_records([{
            "id": "TASK-001", "title": "Do not copy this",
            "next_action": "Or this", "evidence": "Nor this",
        }])
        self.assertEqual(findings, [])
        self.assertEqual(valid[0]["summary"], "")

        _valid, findings = store.validate_records([
            {"id": "TASK-001", "summary": ["not prose"]},
        ])
        self.assertTrue(findings)
        self.assertIn("summary", findings[0]["message"])

        project = Project(self)
        rc, payload = project.task("list", "--all")
        self.assertEqual(rc, 0, payload)
        # 2.1: TASK-237 3a's store-read minor; nothing about `summary` moved.
        # TASK-237 3b′: `installed` was added, a minor bump.
        # TASK-237 3c: `installed` narrowed (a store needs `.perry/`), a minor bump.
        self.assertEqual(payload["contract"], "perry-task/list/2.4")
        contract = (ROOT / "schema" / "task-list-contract.md").read_text(
            encoding="utf-8")
        self.assertIn("### 1.11", contract)
        self.assertIn("never inferred", contract)

    def test_create_list_reload_and_explain_preserve_unicode_exactly(self):
        for summary in (None, "Why it exists; what success changes.",
                        "直白说明任务为什么存在，以及完成后得到什么。"):
            with self.subTest(summary=summary):
                project = Project(self)
                task_id = self.seed_summary(project, summary)
                expected = summary or ""

                self.assertEqual(project.record(task_id)["summary"], expected)
                self.assertEqual(self.listed(project, task_id)["summary"], expected)
                self.assertNotIn("Summary", project.board(),
                                 "the compact Board gained a required column")

                machine = self.explain(project, task_id, "--json")
                human = self.explain(project, task_id)
                self.assertEqual(machine.returncode, 0, machine.stderr)
                self.assertEqual(human.returncode, 0, human.stderr)
                payload = json.loads(machine.stdout)
                if summary:
                    self.assertEqual(payload["summary"], summary)
                    self.assertIn(f"summary    {summary}", human.stdout)
                else:
                    self.assertNotIn("summary", payload)
                    self.assertNotIn("  summary", human.stdout)

    def test_native_update_clear_and_unicode_are_verbatim(self):
        sb = ready(self)
        tid = task(sb, summary=SENTINEL)
        before = sb.get(tid)["fields"]
        for summary in ("中文与 ROUND-2 都是原文。", None):
            sb.ok("item update", data={"actor": ACTOR, "id": tid,
                                       "set": {"summary": summary},
                                       "expect": {tid: sb.get(tid)["seq"]}})
            after = sb.get(tid)["fields"]
            self.assertEqual(after["summary"], summary)
            self.assertEqual({k: v for k, v in before.items() if k != "summary"},
                             {k: v for k, v in after.items() if k != "summary"})

    def test_native_unrelated_mutations_preserve_summary_through_close(self):
        sb = ready(self)
        tid = task(sb, summary=SENTINEL)
        for fields in ({"title": "Correct label"}, {"priority": "P0"},
                       {"next_action": "Read evidence"}, {"evidence": "proof.md"}):
            sb.ok("item update", data={"actor": ACTOR, "id": tid, "set": fields})
            self.assertEqual(sb.get(tid)["fields"]["summary"], SENTINEL)
        for transition in ("start", "submit", "done"):
            sb.move(tid, transition)
            self.assertEqual(sb.get(tid)["fields"]["summary"], SENTINEL)
        sb.ok("item update", data={"actor": ACTOR, "id": tid,
                                   "set": {"summary": "Historical correction"}})
        self.assertEqual(sb.get(tid)["state"], "done")
        self.assertEqual(sb.get(tid)["fields"]["summary"], "Historical correction")

    def test_frozen_summary_and_stage_writers_preserve_the_whole_legacy_store(self):
        project = Project(self)
        tid = self.seed_summary(project, SENTINEL)
        before = {str(p.relative_to(project.root)): p.read_bytes()
                  for p in project.root.rglob("*") if p.is_file()}
        for argv in (("summary", tid, "--summary", "replacement"),
                     ("summary", tid, "--clear"), ("stage", tid, "--stage", "draft"),
                     ("done", tid, "--evidence", "proof.md", "--rung", "V3")):
            with self.subTest(argv=argv):
                rc, out = project.task(*argv)
                self.assertEqual(rc, 1, out)
                self.assertIn("read-only", out["refused"])
                self.assertEqual({str(p.relative_to(project.root)): p.read_bytes()
                                  for p in project.root.rglob("*") if p.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
