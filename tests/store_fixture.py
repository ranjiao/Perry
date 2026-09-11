"""Small project fixtures for store/projection contract tests."""

from __future__ import annotations

import pathlib
import shutil
import tempfile
import unittest

import config_store
import inproc


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

#: The settings the fixture project declares. Written as a store, because
#: since ADR-019 there is nowhere else to write them — a `.perry/config.md`
#: here would be a file no tool opens, and every assertion below would be
#: measuring an unconfigured project.
CONFIG_SETTINGS = {
    "Document language": "English",
    "Repo layout": "single",
    "State root": "perry",
}


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
            shutil.copy2(ROOT / ".perry" / "config.jsonl",
                         root / ".perry" / "config.jsonl")
            shutil.copy2(ROOT / "perry" / "OKR.md",
                         root / "perry" / "OKR.md")
            shutil.copy2(ROOT / "perry" / "okr.jsonl",
                         root / "perry" / "okr.jsonl")
        else:
            config_store.write_config(root, CONFIG_SETTINGS)

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
        # **In-process** (TASK-368). All four modules that share this helper
        # were measured before converting it — `test_store_drift` 73.5%,
        # `test_store_is_canonical` 73.1%, `test_design_handoff` 82.5%,
        # `test_linkage_store_declared` 65.6% — and the boundary is 97.7% of a
        # `perry-tasks` call against a fixture. `perry-tasks`' two module
        # globals are sibling-module handles, neither root-dependent.
        proc = inproc.run("perry-tasks",
                          ["write", "--from-board", "--root", str(root)],
                          cwd=str(ROOT))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        path = root / "perry" / "tasks.jsonl"
        self.assertTrue(path.exists(), "the fixture wrote no store")
        return path
