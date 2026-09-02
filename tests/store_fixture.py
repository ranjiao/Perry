"""Small project fixtures for store/projection contract tests."""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS = ROOT / "bin" / "perry-tasks"

BOARD = """# Board - Store fixture

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence | Depends on |
|---|---|---|---|---|---|---|
| TASK-001 | first task | Coding Agent | not_started | start it | - | - |
| TASK-002 | second task | Coding Agent | in_progress | finish it | - | TASK-001 |

## P1

| ID | Title | Owner | Status | Next action | Evidence | Depends on |
|---|---|---|---|---|---|---|
| TASK-003 | third task | Coding Agent | blocked | wait | - | TASK-002 |

## P2

| ID | Title | Owner | Status | Next action | Evidence | Depends on |
|---|---|---|---|---|---|---|

## Cadence (recurring; doesn't consume P0 slots)

| ID | Recurring task | Owner | Frequency | Next due | Last evidence |
|---|---|---|---|---|---|

## User Input Queue

| USER-id | Needed from user | Blocks | Idle | Status |
|---|---|---|---|---|

## Top risks

- (no active risks)
"""

CONFIG = """# Perry configuration

- Document language: English
- Repo layout: single
- State root: perry
"""


class StoreFixture(unittest.TestCase):
    """Build only the files needed by a store/projection comparison."""

    def project(self, *, with_store: bool = False,
                markdown_stores: bool = False) -> pathlib.Path:
        root = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        (root / ".perry").mkdir()
        (root / "perry").mkdir()
        (root / "perry" / "BOARD.md").write_text(BOARD, encoding="utf-8")
        (root / ".perry" / "events.jsonl").write_text("", encoding="utf-8")

        if markdown_stores:
            shutil.copy2(ROOT / ".perry" / "config.md",
                         root / ".perry" / "config.md")
            shutil.copy2(ROOT / ".perry" / "config.jsonl",
                         root / ".perry" / "config.jsonl")
            shutil.copy2(ROOT / "perry" / "OKR.md",
                         root / "perry" / "OKR.md")
            shutil.copy2(ROOT / "perry" / "okr.jsonl",
                         root / "perry" / "okr.jsonl")
        else:
            (root / ".perry" / "config.md").write_text(
                CONFIG, encoding="utf-8")

        if with_store:
            self.write_store(root)
        return root

    def full_project(self) -> pathlib.Path:
        """Copy the live state only for tests whose subject is that corpus."""
        root = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        shutil.copytree(ROOT / "perry", root / "perry")
        shutil.copytree(ROOT / ".perry", root / ".perry",
                        ignore=shutil.ignore_patterns("*.lock"))
        return root

    def write_store(self, root: pathlib.Path) -> pathlib.Path:
        proc = subprocess.run(
            [sys.executable, str(TASKS), "write", "--from-board",
             "--root", str(root)],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        path = root / "perry" / "tasks.jsonl"
        self.assertTrue(path.exists(), "the fixture wrote no store")
        return path
