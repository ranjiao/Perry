"""TASK-090: task reads come from the store; Board is projection only.

Run: python3 tests/parallel test_task_store_read_cutover
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path



ROOT = Path(__file__).resolve().parent.parent
TASK = ROOT / "bin" / "perry-task"

BOARD = """# Board

## P0

| ID | Title | Owner | Status | Next action | Evidence | Depends on |
|---|---|---|---|---|---|---|
| TASK-001 | Store one | Coding Agent | not_started | store next | — |  |
| TASK-002 | Store two | Coding Agent | blocked | wait | — | TASK-001 |

## User Input Queue

| USER-id | Needed from user | Blocks | Asked | Status |
|---|---|---|---|---|

## Top risks

- none
"""


def record(tid: str, title: str, status: str, order: int,
           depends_on: list[str] | None = None) -> dict:
    return {
        "id": tid, "title": title, "owner": "Coding Agent",
        "status": status, "priority": "P0", "track": "main", "stage": "",
        "stage_since": "", "arrived": "", "verification": "V2",
        "evidence": "—", "next_action": "store next",
        "depends_on": list(depends_on or []), "commitment": "", "parent": "",
        "group": "P0", "role": "", "created": "2026-08-19T10:00:00",
        "order": order,
    }


class Project:
    def __init__(self, case: unittest.TestCase):
        self.root = Path(tempfile.mkdtemp()).resolve()
        case.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- State root: .\n",
            encoding="utf-8")
        (self.root / "BOARD.md").write_text(BOARD, encoding="utf-8")
        self.write_store([
            record("TASK-001", "Store one", "not_started", 0),
            record("TASK-002", "Store two", "blocked", 1, ["TASK-001"]),
        ])

    def write_store(self, records: list[dict]) -> None:
        (self.root / "tasks.jsonl").write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records),
            encoding="utf-8")

    def store(self) -> list[dict]:
        return [json.loads(line) for line in
                (self.root / "tasks.jsonl").read_text(encoding="utf-8").splitlines()]

    def run(self, *args: str) -> tuple[int, dict, str]:
        proc = subprocess.run(
            [sys.executable, str(TASK), *args, "--root", str(self.root), "--json"],
            capture_output=True, text=True)
        return proc.returncode, json.loads(proc.stdout or "{}"), proc.stderr

    def listed(self) -> dict:
        code, payload, stderr = self.run("list", "--all")
        if code:
            raise AssertionError(payload or stderr)
        return payload


class TestTaskStoreReadCutover(unittest.TestCase):
    CURRENT_FIELDS = {
        "id", "title", "owner", "priority", "status", "status_text", "track",
        "mode", "stage", "stage_since", "arrived", "parent", "commitment",
        "next_action", "evidence", "verification", "open", "group", "role",
        "depends_on", "blocked_by", "blocks", "startable", "created",
    }

    def task(self, payload: dict, tid: str) -> dict:
        return next(item for item in payload["tasks"] if item["id"] == tid)

    def test_list_and_events_work_without_board(self):
        project = Project(self)
        (project.root / ".perry" / "events.jsonl").write_text(
            json.dumps({"ts": "2026-08-19T11:00:00", "event": "start",
                        "id": "TASK-001", "from": "not_started",
                        "to": "in_progress"}) + "\n", encoding="utf-8")
        (project.root / "BOARD.md").unlink()

        payload = project.listed()
        self.assertEqual(self.task(payload, "TASK-001")["status"], "not_started")
        self.assertEqual(set(payload["risks"]), {"items", "open", "cleared", "source"})
        self.assertEqual(set(payload["asks"]), {"items", "open"})
        self.assertEqual(payload["intake"]["rows"], [])
        self.assertEqual(payload["conformance"]["missing_projection"],
                         str(project.root / "BOARD.md"))

        code, events, stderr = project.run("events")
        self.assertEqual(code, 0, stderr)
        self.assertEqual(events["events"][0]["task"], "TASK-001")

    def test_store_edit_wins_and_unrelated_write_renders_it(self):
        project = Project(self)
        records = project.store()
        records[0]["title"] = "Store-only title"
        project.write_store(records)
        board_path = project.root / "BOARD.md"
        board_path.write_text(
            board_path.read_text(encoding="utf-8").replace(
                "Store one", "Board-only title").replace(
                "Coding Agent | not_started | store next | — |  |",
                "Board Owner | review | board-only next | board.md | TASK-999 |"),
            encoding="utf-8")
        lines = board_path.read_text(encoding="utf-8").splitlines()
        first = next(i for i, line in enumerate(lines) if line.startswith("| TASK-001 |"))
        second = next(i for i, line in enumerate(lines) if line.startswith("| TASK-002 |"))
        lines[first], lines[second] = lines[second], lines[first]
        board_path.write_text("\n".join(lines), encoding="utf-8")

        listed = self.task(project.listed(), "TASK-001")
        self.assertEqual(listed["title"], "Store-only title")
        self.assertEqual(listed["status"], "not_started")
        self.assertEqual(listed["status_text"], listed["status"])
        self.assertEqual(listed["owner"], "Coding Agent")
        self.assertEqual(listed["next_action"], "store next")
        self.assertEqual(listed["evidence"], "—")
        self.assertEqual(listed["depends_on"], [])
        code, result, stderr = project.run("ask", "--needed", "unrelated")
        self.assertEqual(code, 0, result or stderr)
        self.assertEqual(project.store()[0]["title"], "Store-only title")
        self.assertEqual([item["order"] for item in project.store()], [0, 1])
        board = board_path.read_text(encoding="utf-8")
        self.assertIn("Store-only title", board)
        self.assertNotIn("Board-only title", board)
        self.assertTrue(result["projection"]["cells_the_store_and_board_disagree_on"])

    def test_status_text_is_the_typed_status_alias_not_projection_text(self):
        project = Project(self)
        board = project.root / "BOARD.md"
        board.write_text(
            board.read_text(encoding="utf-8").replace(
                "| not_started |", "| **board-only prose** |", 1),
            encoding="utf-8")

        payload = project.listed()
        task = self.task(payload, "TASK-001")
        self.assertEqual(task["status"], "not_started")
        self.assertEqual(task["status_text"], "not_started")
        change = next(item for item in payload["semantics"]
                      if item["version"] == "1.10")
        self.assertIn("status_text", change["fields"])

    def test_custom_group_does_not_publish_a_standard_priority(self):
        project = Project(self)
        records = project.store()
        records[0]["group"] = "P0 (must finish this period)"
        project.write_store(records)

        sections = project.listed()["conformance"]["sections_read"]
        custom = next(section for section in sections
                      if section["heading"] == "P0 (must finish this period)")
        self.assertIsNone(custom["priority"])

    def test_deleting_events_only_removes_history(self):
        project = Project(self)
        event_path = project.root / ".perry" / "events.jsonl"
        event_path.write_text(
            "".join(json.dumps(event) + "\n" for event in [
                {"ts": "2026-08-19T11:00:00", "event": "done", "id": "TASK-001",
                 "to": "done", "depends_on": ["TASK-999"], "title": "event title"},
                {"ts": "2026-08-19T11:01:00", "event": "depends", "id": "TASK-002",
                 "to": "TASK-999", "depends_on": ["TASK-999"]},
            ]), encoding="utf-8")
        before = project.listed()
        event_path.unlink()
        after = project.listed()

        for tid in ("TASK-001", "TASK-002"):
            current_before = {key: self.task(before, tid)[key]
                              for key in self.CURRENT_FIELDS}
            current_after = {key: self.task(after, tid)[key]
                             for key in self.CURRENT_FIELDS}
            self.assertEqual(current_before, current_after)
            self.assertTrue(self.task(before, tid)["timeline"])
            self.assertEqual(self.task(after, tid)["timeline"], [])
        self.assertEqual(self.task(after, "TASK-002")["blocked_by"], ["TASK-001"])
        self.assertFalse(self.task(after, "TASK-002")["startable"])

    def test_board_only_task_and_edges_never_become_truth(self):
        project = Project(self)
        board_path = project.root / "BOARD.md"
        board = board_path.read_text(encoding="utf-8")
        board = board.replace("| TASK-002 | Store two", "| TASK-002 | Board two")
        board = board.replace("| TASK-001 | Store one", "| TASK-999 | Board ghost")
        board_path.write_text(board, encoding="utf-8")

        payload = project.listed()
        self.assertEqual({task["id"] for task in payload["tasks"]},
                         {"TASK-001", "TASK-002"})
        self.assertEqual(self.task(payload, "TASK-002")["title"], "Store two")
        code, result, stderr = project.run("start", "TASK-999")
        self.assertEqual(code, 1, stderr)
        self.assertIn("not a task", result["refused"])

    def test_writer_baseline_does_not_read_a_literal_for_an_empty_store_field(self):
        project = Project(self)
        records = project.store()
        records[0]["next_action"] = ""
        project.write_store(records)
        board = project.root / "BOARD.md"
        board.write_text(board.read_text().replace("store next", "board literal", 1),
                         encoding="utf-8")

        code, result, stderr = project.run(
            "next", "TASK-001", "--next", "board literal")
        self.assertEqual(code, 0, result or stderr)
        record = next(r for r in project.store() if r["id"] == "TASK-001")
        self.assertEqual(record["next_action"], "board literal")

    def test_id_mint_ignores_board_and_event_ids(self):
        project = Project(self)
        board_path = project.root / "BOARD.md"
        board_path.write_text(
            board_path.read_text(encoding="utf-8").replace(
                "| TASK-001 |", "| TASK-999 |", 1), encoding="utf-8")
        (project.root / ".perry" / "events.jsonl").write_text(
            json.dumps({"ts": "2026-08-19T12:00:00", "event": "add",
                        "id": "TASK-888", "title": "history only"}) + "\n",
            encoding="utf-8")
        code, result, stderr = project.run(
            "add", "--title", "New", "--priority", "P0",
            "--deliverable", "artifact", "--verification", "test passes")
        self.assertEqual(code, 0, result or stderr)
        self.assertEqual(result["id"], "TASK-003")
        self.assertEqual({item["id"] for item in project.store()},
                         {"TASK-001", "TASK-002", "TASK-003"})

    def test_malformed_store_is_a_structured_refusal_and_is_not_recovered(self):
        project = Project(self)
        path = project.root / "tasks.jsonl"
        for bad in ('{"id": "TASK-001"\n',
                    json.dumps({**record("TASK-001", "x", "not_started", 0),
                                "depends_on": "TASK-002"}) + "\n",
                    json.dumps({**record("TASK-001", "x", "not_started", 0),
                                "depends_on": [7]}) + "\n",
                    json.dumps({**record("TASK-001", "x", "not_started", 0),
                                "depends_on": [{}]}) + "\n"):
            with self.subTest(bad=bad[:20]):
                path.write_text(bad, encoding="utf-8")
                before = path.read_bytes()
                code, result, stderr = project.run("list", "--all")
                self.assertEqual(code, 1)
                self.assertIn("tasks.jsonl", result["refused"])
                self.assertNotIn("Traceback", stderr)
                self.assertEqual(path.read_bytes(), before)

    def test_wrong_typed_dependency_element_refuses_before_unrelated_write(self):
        project = Project(self)
        records = project.store()
        records[0]["depends_on"] = [7]
        project.write_store(records)
        board = project.root / "BOARD.md"
        before_store = (project.root / "tasks.jsonl").read_bytes()
        before_board = board.read_bytes()

        code, result, stderr = project.run("ask", "--needed", "unrelated")

        self.assertEqual(code, 1)
        self.assertIn("list of strings", result["refused"])
        self.assertNotIn("Traceback", stderr)
        self.assertEqual((project.root / "tasks.jsonl").read_bytes(), before_store)
        self.assertEqual(board.read_bytes(), before_board)
        self.assertFalse((project.root / ".perry" / "events.jsonl").exists())
        self.assertFalse((project.root / "journal").exists())


if __name__ == "__main__":
    unittest.main()
