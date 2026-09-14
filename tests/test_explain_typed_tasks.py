"""Typed Task lookup for ``bin/perry-explain`` (ADR-009, TASK-105)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import config_store  # noqa: E402


PERRY_HOME = Path(__file__).resolve().parent.parent
EXPLAIN = PERRY_HOME / "bin" / "perry-explain"


class TypedTaskLookup(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        config_store.write_config(self.root, {"State root": "."})

    def tearDown(self):
        self.temp.cleanup()

    def run_explain(self, task_id: str, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(EXPLAIN), task_id, "--root", str(self.root),
             *extra],
            text=True, capture_output=True,
        )

    def write_store(self, records: list[dict]) -> None:
        (self.root / "tasks.jsonl").write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )

    def write_false_markdown_definition(self, task_id: str = "TASK-091") -> None:
        (self.root / "DESIGN.md").write_text(
            "| Task | Title |\n|---|---|\n"
            f"| {task_id} | 2 |\n",
            encoding="utf-8",
        )

    def test_store_title_wins_over_a_plausible_markdown_definition(self):
        self.write_false_markdown_definition()
        self.write_store([{
            "id": "TASK-091",
            "title": "By when splits into due plus note",
            "status": "done",
        }])

        human = self.run_explain("TASK-091")
        machine = self.run_explain("TASK-091", "--json")

        self.assertEqual(human.returncode, 0, human.stderr)
        self.assertIn("By when splits into due plus note", human.stdout)
        self.assertNotIn("TASK-091  —  2", human.stdout)
        payload = json.loads(machine.stdout)
        self.assertEqual(payload["title"], "By when splits into due plus note")
        self.assertEqual(payload["status"], "done")
        self.assertEqual(payload["kind"], "Task")
        self.assertTrue(payload["defined"].startswith("tasks.jsonl:"))

    def test_open_done_and_dropped_tasks_all_resolve(self):
        self.write_store([
            {"id": "TASK-001", "title": "Open", "status": "in_progress"},
            {"id": "TASK-002", "title": "Done", "status": "done"},
            {"id": "TASK-003", "title": "Dropped", "status": "dropped"},
        ])
        for task_id, status in (("TASK-001", "in_progress"),
                                ("TASK-002", "done"),
                                ("TASK-003", "dropped")):
            with self.subTest(task_id=task_id):
                result = self.run_explain(task_id, "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["status"], status)

    def test_present_store_disables_markdown_fallback_for_a_missing_task(self):
        self.write_false_markdown_definition("TASK-999")
        self.write_store([{"id": "TASK-001", "title": "Other"}])

        human = self.run_explain("TASK-999")
        machine = self.run_explain("TASK-999", "--json")

        self.assertEqual(human.returncode, 1)
        self.assertIn("not found in canonical Task store", human.stdout)
        self.assertIn("Markdown lookup was not used", human.stdout)
        payload = json.loads(machine.stdout)
        self.assertEqual(payload["error"], "not-found-in-task-store")
        self.assertFalse(payload["found"])

    def test_no_store_keeps_the_generic_cross_project_lookup(self):
        self.write_false_markdown_definition("TASK-999")
        result = self.run_explain("TASK-999", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["title"], "2")

    def test_a_tasks_jsonl_alone_is_a_canonical_store_and_is_claimed(self):
        """**Inverted by TASK-237 3b′, and on purpose.** This test asserted a
        `tasks.jsonl` with no `.perry/` was NOT claimed, because `BOARD.md` /
        `OKR.md` / `phase/` were then what adopted a project. The user's
        criterion (Amendment (4) item 2, `schema/README.md § installed`) is
        the config store OR any canonical store under the state root — so a
        `tasks.jsonl` at the root makes the directory an installed Perry
        project, and its record answers ahead of a markdown definition
        (ADR-009), exactly as on a configured project."""
        self.write_false_markdown_definition("TASK-999")
        self.write_store([{"id": "TASK-999", "title": "unrelated store"}])
        (self.root / ".perry" / "config.jsonl").unlink()
        (self.root / ".perry").rmdir()

        result = self.run_explain("TASK-999", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["title"], "unrelated store")

    def test_a_markdown_only_project_s_definition_is_not_overridden(self):
        """The half of the old test the criterion keeps: with no config and no
        store, nothing is claimed and the markdown lookup answers."""
        self.write_false_markdown_definition("TASK-999")
        (self.root / ".perry" / "config.jsonl").unlink()
        (self.root / ".perry").rmdir()
        self.assertFalse((self.root / "tasks.jsonl").exists())

        result = self.run_explain("TASK-999", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["title"], "2")

    def test_malformed_store_states_are_named_refusals(self):
        cases = {
            "invalid-json": "{broken\n",
            "non-object": "[]\n",
            "missing-id": '{"title":"missing"}\n',
            "duplicate-id": (
                '{"id":"TASK-001","title":"first"}\n'
                '{"id":"TASK-001","title":"second"}\n'
            ),
        }
        for name, raw in cases.items():
            with self.subTest(name=name):
                (self.root / "tasks.jsonl").write_text(raw, encoding="utf-8")
                result = self.run_explain("TASK-001", "--json")
                self.assertEqual(result.returncode, 1)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["error"], "task-store-invalid")
                self.assertTrue(payload["findings"])
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
