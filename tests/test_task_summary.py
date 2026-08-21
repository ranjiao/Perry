"""TASK-106: optional Task summaries stay explicit and typed end to end."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from tests.gate import GATE_OFF   # tests/gate.py — why this fixture opts out
from tests.test_store_is_the_write_target import Project, task_module


ROOT = Path(__file__).resolve().parent.parent
EXPLAIN = ROOT / "bin" / "perry-explain"
TASK = ROOT / "bin" / "perry-task"


class TaskSummaryContract(unittest.TestCase):
    def add(self, project: Project, summary: str | None = None) -> str:
        argv = ["add", "--title", "Compact label", "--priority", "P1"]
        if summary is not None:
            argv += ["--summary", summary]
        rc, out = project.task(*argv)
        self.assertEqual(rc, 0, out)
        return out["id"]

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
        self.assertEqual(payload["contract"], "perry-task/list/1.15")
        contract = (ROOT / "schema" / "task-list-contract.md").read_text(
            encoding="utf-8")
        self.assertIn("### 1.11", contract)
        self.assertIn("never inferred", contract)

    def test_create_list_reload_and_explain_preserve_unicode_exactly(self):
        for summary in (None, "Why it exists; what success changes.",
                        "直白说明任务为什么存在，以及完成后得到什么。"):
            with self.subTest(summary=summary):
                project = Project(self)
                task_id = self.add(project, summary)
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

    def test_dedicated_update_and_clear_touch_only_summary(self):
        project = Project(self)
        task_id = self.add(project, "old purpose")
        before = project.record(task_id)

        rc, out = project.task("summary", task_id, "--summary", "新的稳定说明")
        self.assertEqual(rc, 0, out)
        after = project.record(task_id)
        self.assertEqual(after["summary"], "新的稳定说明")
        self.assertEqual({k: v for k, v in after.items() if k != "summary"},
                         {k: v for k, v in before.items() if k != "summary"})
        event = json.loads((project.root / ".perry" / "events.jsonl")
                           .read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual((event["event"], event["field"], event["from"], event["to"]),
                         ("summary", "summary", "old purpose", "新的稳定说明"))
        timeline = self.listed(project, task_id)["timeline"][-1]
        self.assertEqual(timeline["field"], "summary")

        before_clear = project.record(task_id)
        rc, out = project.task("summary", task_id, "--clear")
        self.assertEqual(rc, 0, out)
        cleared = project.record(task_id)
        self.assertEqual(cleared["summary"], "")
        self.assertEqual({k: v for k, v in cleared.items() if k != "summary"},
                         {k: v for k, v in before_clear.items() if k != "summary"})

        terminal = Project(self)
        terminal_id = self.add(terminal, "before close")
        rc, out = terminal.task("done", terminal_id, "--evidence", "proof.md",
                                "--rung", "V3")
        self.assertEqual(rc, 0, out)
        rc, out = terminal.task("summary", terminal_id,
                                "--summary", "still editable after close")
        self.assertEqual(rc, 0, out)
        self.assertEqual(terminal.record(terminal_id)["status"], "done")
        self.assertEqual(terminal.record(terminal_id)["summary"],
                         "still editable after close")

    def test_summary_update_preserves_store_record_order(self):
        project = Project(self)
        before = [record["id"] for record in project.store()]

        rc, out = project.task("summary", "TASK-002", "--summary",
                               "metadata only")

        self.assertEqual(rc, 0, out)
        self.assertEqual([record["id"] for record in project.store()], before)

    def test_summary_is_verbatim_prose_not_an_identifier_surface(self):
        project = Project(self)

        written = subprocess.run(
            [sys.executable, str(TASK), "summary", "TASK-002", "--summary",
             "ROUND-2 purpose", "--root", str(project.root)],
            capture_output=True, text=True)

        self.assertEqual(written.returncode, 0, written.stderr)
        self.assertNotIn("reads as an id", written.stderr)
        self.assertEqual(project.record("TASK-002")["summary"],
                         "ROUND-2 purpose")

    def test_every_unrelated_task_writer_preserves_the_sentinel(self):
        cases = {
            "start": lambda tid: ("start", tid),
            "status": lambda tid: ("status", tid, "--status", "review"),
            "next": lambda tid: ("next", tid, "--next", "new current step"),
            "retitle": lambda tid: ("retitle", tid, "--title", "New label"),
            "rung": lambda tid: ("rung", tid, "--rung", "V3"),
            "evidence": lambda tid: ("evidence", tid, "--evidence", "proof.md"),
            "prioritize": lambda tid: ("prioritize", tid, "--priority", "P2"),
            "depends": lambda tid: ("depends", tid, "--on", "TASK-001"),
            "done": lambda tid: ("done", tid, "--evidence", "proof.md",
                                  "--rung", "V3"),
            "drop": lambda tid: ("drop", tid, "--reason", "no longer needed"),
        }
        for name, command in cases.items():
            with self.subTest(command=name):
                project = Project(self)
                task_id = self.add(project, "SUMMARY-SENTINEL")
                rc, out = project.task(*command(task_id))
                self.assertEqual(rc, 0, out)
                self.assertEqual(project.record(task_id)["summary"],
                                 "SUMMARY-SENTINEL")

    def test_pipeline_stage_mutation_preserves_the_sentinel(self):
        from tests.test_store_is_the_write_target import BOARD

        board = BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |",
            "| ID | Title | Owner | Status | Next action | Evidence | Track | Stage |",
        ).replace(
            "|---|---|---|---|---|---|",
            "|---|---|---|---|---|---|---|---|",
        ).replace("| — | — |", "| — | — | ops | brief |")
        project = Project(self, board=board)
        # Overwrites the config `Project` wrote, so it carries `GATE_OFF`
        # forward itself — see tests/gate.py.
        (project.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n" + GATE_OFF
            + "\n## Tracks\n\n"
            "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| ops | pipeline | OKR.md | brief,draft | — | 3d | — | V2 |\n",
            encoding="utf-8")
        rc, out = project.task("summary", "TASK-002", "--summary",
                               "SUMMARY-SENTINEL")
        self.assertEqual(rc, 0, out)

        rc, out = project.task("stage", "TASK-002", "--stage", "draft")

        self.assertEqual(rc, 0, out)
        self.assertEqual(project.record("TASK-002")["stage"], "draft")
        self.assertEqual(project.record("TASK-002")["summary"],
                         "SUMMARY-SENTINEL")

    def test_legacy_record_stays_empty_after_the_next_write(self):
        project = Project(self)
        store = project.store()
        record = next(item for item in store if item["id"] == "TASK-001")
        record.pop("summary", None)
        record["title"] = "A title is not a summary"
        record["next_action"] = "A next action is not a summary"
        record["evidence"] = "evidence/is-not-a-summary.md"
        (project.root / "tasks.jsonl").write_text(
            "".join(json.dumps(item) + "\n" for item in store), encoding="utf-8")
        (project.root / "TASK-001-spec.md").write_text(
            "This prose must not be inferred.\n", encoding="utf-8")

        self.assertEqual(self.listed(project, "TASK-001")["summary"], "")
        explained = self.explain(project, "TASK-001", "--json")
        self.assertNotIn("summary", json.loads(explained.stdout))

        rc, out = project.task("next", "TASK-001", "--next", "changed explicitly")
        self.assertEqual(rc, 0, out)
        self.assertIn("summary", project.record("TASK-001"))
        self.assertEqual(project.record("TASK-001")["summary"], "")


if __name__ == "__main__":
    unittest.main()
