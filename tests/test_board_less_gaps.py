"""TASK-237 deliverable 3b, item 3 — the board-less gaps 3a named.

`TASK-237-d3a-result.md § 6` named them, and `TASK-237-spec.md § Amendment (5)
§ Deliverable 3b` item 3 made them this row's:

* R3 — `perry-diagnose § open_user_asks` and its intake count read `BOARD.md`,
  bypassing `asks.jsonl` and `intake.jsonl`;
* R5 — `perry-lint` checks that go quiet with the file absent. Three are fixed
  here (`check_verification`, `check_reviews`, `resolves_somewhere`); the
  fourth, `done-needs-evidence`, is argued in the result: its subject is a
  hand-kept `done` ROW, which a rendered board never carries, so silence with
  no file is the same answer the check gives a rendered board.

Each case is run with the file ABSENT and with a file present — either the
board the stores render to, or a FORGED one carrying rows no store holds.
Expectations come from the records this module writes, never from a board.

Run: python3 tests/parallel test_board_less_gaps
"""

from __future__ import annotations

COVERS = ("bin/perry-diagnose", "bin/perry-lint", "bin/perry-explain")

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import inproc

CONFIG = [{"kind": "setting", "key": "state_root", "label": "State root",
           "value": "perry", "order": 0}]


def task(tid, status="not_started", verification="V3", **kw):
    rec = {"id": tid, "title": f"title of {tid}", "summary": "",
           "owner": "Coding Agent", "status": status, "priority": "P1",
           "track": "main", "stage": "", "stage_since": "", "arrived": "",
           "verification": verification, "evidence": "", "next_action": "next",
           "depends_on": [], "design_refs": [], "commitment": "", "parent": "",
           "group": "P1", "role": "", "created": "2026-09-01", "order": 0}
    rec.update(kw)
    return rec


def jsonl(records) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)


ASKS = [
    {"id": "USER-001", "needed": "which threshold?", "blocks": "TASK-001",
     "asked": "2026-09-01", "status": "pending", "answered": False, "order": 0},
    {"id": "USER-002", "needed": "keep the file?", "blocks": "TASK-001",
     "asked": "2026-08-20", "status": "answered 2026-08-21: no",
     "answered": True, "order": 1},
]
INTAKE = [
    {"order": 0, "arrived": "2026-09-10", "request": "print the board",
     "outcome": "", "discharged": False},
    {"order": 1, "arrived": "2026-09-09", "request": "drop the file",
     "outcome": "", "discharged": False},
]

FORGED_BOARD = """# Board — forged

## Intake

| Arrived | Request | Outcome |
|---|---|---|
| 2026-01-01 | forged one | |
| 2026-01-02 | forged two | |
| 2026-01-03 | forged three | |
| 2026-01-04 | forged four | |
| 2026-01-05 | forged five | |

## User Input Queue

| USER-id | Needed from user | Blocks | Status |
|---|---|---|---|
| USER-001 | which threshold? | TASK-001 | answered 2026-09-02: seven |
| USER-777 | forged question | TASK-001 | pending |
"""


class Project:
    def __init__(self, tasks=(), events=(), board: str | None = None):
        self.tmp = tempfile.mkdtemp(prefix="t237gaps-")
        self.root = Path(self.tmp)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.jsonl").write_text(jsonl(CONFIG))
        (self.root / ".perry" / "events.jsonl").write_text(jsonl(events))
        self.state = self.root / "perry"
        (self.state / "evidence").mkdir(parents=True)
        (self.state / "tasks.jsonl").write_text(jsonl(tasks))
        (self.state / "asks.jsonl").write_text(jsonl(ASKS))
        (self.state / "intake.jsonl").write_text(jsonl(INTAKE))
        (self.root / "notes").mkdir()
        (self.root / "notes" / "asks.md").write_text(
            "# Asks\n\nUSER-001, USER-002 and USER-777 were discussed.\n")
        if board == "rendered":
            out = inproc.run("perry-tasks", ["board", "--root", str(self.root)])
            assert out.returncode == 0, out.stderr
            (self.state / "BOARD.md").write_text(out.stdout)
        elif board is not None:
            (self.state / "BOARD.md").write_text(board)

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


def states(testcase, forged: str = FORGED_BOARD, **kw):
    """`(label, Project)` for the file absent, rendered and forged."""
    out = []
    for label, board in (("absent", None), ("rendered", "rendered"),
                         ("forged", forged)):
        p = Project(board=board, **kw)
        testcase.addCleanup(p.close)
        out.append((label, p))
    return out


# ── R3: perry-diagnose ─────────────────────────────────────────────────────


class TestDiagnoseReadsTheRegisterStores(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.diagnose = inproc.load("perry-diagnose")
        cls.explain = cls.diagnose.load_sibling("perry-explain")

    def test_open_asks_are_the_stores_unanswered_asks(self):
        want = [(a["id"], f"perry/asks.jsonl:{n}")
                for n, a in enumerate(ASKS, 1) if not a["answered"]]
        for label, p in states(self):
            with self.subTest(board=label):
                # Resolved, as `perry-diagnose § main` hands it: a temp dir is
                # a symlink on macOS, and `resolve_state_root` ignores a state
                # root that resolves outside an unresolved project root.
                root = p.root.resolve()
                entries = self.explain.harvest(root)
                got = self.diagnose.open_user_asks(root, entries, self.explain)
                self.assertEqual(got, want)

    def test_the_fixture_has_something_to_get_wrong(self):
        """Anti-vacuity: the forged board answers USER-001 and opens USER-777."""
        self.assertTrue(any(not a["answered"] for a in ASKS))
        self.assertIn("| USER-777 |", FORGED_BOARD)
        self.assertIn("| USER-001 | which threshold? | TASK-001 | answered", FORGED_BOARD)

    def test_the_intake_count_is_the_stores(self):
        want = f"intake.jsonl carries {len(INTAKE)} arrived request(s)"
        for label, p in states(self):
            with self.subTest(board=label):
                self.diagnose._TEXT_CACHE.clear()
                got = json.dumps(self.diagnose.scan_work_modes(p.root, p.state),
                                 ensure_ascii=False)
                self.assertIn(want, got)
                self.assertNotIn("BOARD.md § Intake carries", got)


# ── R5: perry-lint ─────────────────────────────────────────────────────────


def rules(findings) -> list[tuple[str, str, str]]:
    return sorted((f.as_dict()["rule"], f.as_dict()["file"], f.as_dict()["message"])
                  for f in findings)


class TestLintChecksDoNotGoQuietWithNoFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lint = inproc.load("perry-lint")

    def test_closures_in_the_event_log_are_judged_with_no_file(self):
        events = [{"ts": "2026-09-10T10:00:00+08:00", "event": "done",
                   "id": "TASK-009", "title": "a closure with no rung",
                   "evidence": "perry/evidence/x.md", "actor": "agent",
                   "from": "in_progress", "to": "done"}]
        got = {}
        for label, p in states(self, forged=None, tasks=[task("TASK-001")],
                               events=events):
            if label == "forged":
                continue
            got[label] = rules(self.lint.check_verification(p.state, p.root / ".perry"))
        self.assertIn("no-verification-rung", [r for r, _, _ in got["absent"]])
        self.assertEqual(got["absent"], got["rendered"])

    def test_reviews_run_on_the_stores_rows_with_no_file(self):
        events = [{"ts": "2026-09-10T10:00:00+08:00", "event": "done",
                   "id": "TASK-008", "title": "closed at V4", "rung": "V4",
                   "evidence": "perry/evidence/x.md", "actor": "agent",
                   "from": "review", "to": "done"}]
        tasks = [task("TASK-001", status="review", verification="V4"),
                 task("TASK-008", status="done", verification="V4")]
        got = {}
        for label, p in states(self, forged=None, tasks=tasks, events=events):
            if label == "forged":
                continue
            got[label] = rules(self.lint.check_reviews(p.state, p.root))
        found = [r for r, _, _ in got["absent"]]
        self.assertIn("v4-close-without-verdict", found)
        self.assertTrue(any("TASK-001" in m for _, _, m in got["absent"]),
                        "no finding about the open store row at review")
        self.assertEqual(got["absent"], got["rendered"])

    def test_a_source_naming_an_open_task_resolves_with_no_file(self):
        tasks = [task("TASK-005"), task("TASK-006", status="done")]
        for label, p in states(self, forged=None, tasks=tasks):
            if label == "forged":
                continue
            with self.subTest(board=label):
                self.assertTrue(self.lint.resolves_somewhere("TASK-005", p.state, p.root))
                self.assertTrue(self.lint.resolves_somewhere("USER-002", p.state, p.root))
                # A closed task is not a row of either board; with no event
                # naming it, it resolves in neither state.
                self.assertFalse(self.lint.resolves_somewhere("TASK-006", p.state, p.root))
                self.assertFalse(self.lint.resolves_somewhere("TASK-404", p.state, p.root))


if __name__ == "__main__":
    unittest.main()
