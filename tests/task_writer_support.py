"""Shared fixtures for the task-writer contract tests."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
TOOL = PERRY_HOME / "bin" / "perry-task"
TASKS = PERRY_HOME / "bin" / "perry-tasks"


def load_tool():
    spec = importlib.util.spec_from_loader(
        "perry_task", importlib.machinery.SourceFileLoader("perry_task", str(TOOL)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PT = load_tool()

BOARD = """# Board — T

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## Cadence (recurring; doesn't consume P0 slots)

| ID | Recurring task | Owner | Frequency | Next due | Last evidence |
|---|---|---|---|---|---|

## User Input Queue

| USER-id | Needed from user | Blocks | Idle | Status |
|---|---|---|---|---|

## Top risks

- none
"""


ROUND_TRIP_BOARD = """# Board — round trip

> A fixture. Every row below is hand-written.

## Intake

| Arrived | Request | Outcome |
|---|---|---|
| 2026-08-01 | someone asked for a thing | routed |

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-001 | Every cell full | Coding Agent | open | do the next thing | evidence/2026-08/TASK-001-spec.md |
| TASK-002 | An empty cell and a blank marker | Coding Agent | blocked |  | — |

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-003 | A cell quoting a table: \\| ID \\| Risk \\| | user | open | read the escaped pipes back as one cell | — |
| TASK-004 | 中文标题也要原样回来 | Coding Agent | open | 保持字节一致 | — |

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-005 | Dependencies, comma separated | Coding Agent | open | TASK-001, TASK-002 | — |
| TASK-006 | A long next action that runs well past any column width anyone would align to | Coding Agent | open | keep going, and keep going, and do not wrap | — |
| TASK-007 | Trailing punctuation and a colon: like this | Coding Agent | open | — | — |

## Done this period (leaves the board at next triage)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-008 | Closed, and carries no priority | Coding Agent | done | — | — |

## Top risks

- none
"""


ROUND_TRIP_ROW_IDS = ("TASK-001", "TASK-002", "TASK-003", "TASK-004",
                      "TASK-005", "TASK-006", "TASK-007")


ROUND_TRIP_ROW_PRIORITIES = ("P0", "P0", "P1", "P1", "P2", "P2", "P2")


ZH_BOARD = """# BOARD

## P0
| 编号 | 标题 | 负责人 | 状态 | 下一步 | 证据 |
|---|---|---|---|---|---|

## P1
| 编号 | 标题 | 负责人 | 状态 | 下一步 | 证据 |
|---|---|---|---|---|---|

## P2
| 编号 | 标题 | 负责人 | 状态 | 下一步 | 证据 |
|---|---|---|---|---|---|
"""


BASIC_MODE_TRACKS = '\n## Tracks\n\n| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n|---|---|---|---|---|---|---|---|\n| core | project | phase/ | — | — | — | — | V3 |\n| blog | pipeline | commitments | brief->draft->published | review:2 | 5d | 2026-W34 | V5 |\n| ops | queue | commitments | new->triaged->resolved | — | 5d | monthly | V2 |\n| study | inquiry | questions | open->researching->answered | open:5 | — | — | V4 |\n'

MODE_TRACKS = '\n## Tracks\n\n| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n|---|---|---|---|---|---|---|---|\n| core | project | phase/ | — | — | — | — | V3 |\n| blog | pipeline | commitments | brief->draft->review->published | review:2 | 5d | 2026-W34 | V5 |\n| ops | queue | commitments | new->triaged->in_progress->resolved | — | 5d | monthly | V2 |\n| study | inquiry | questions | open->researching->answered | open:5 | — | — | V4 |\n'

class Project:
    """A throwaway Perry project the tool can write into."""

    def __init__(self, tracks: str = "", board: str = BOARD):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n" + tracks)
        (self.root / "BOARD.md").write_text(board)
        self.import_board()

    # `add` requires a deliverable and a verification in production — a task
    # whose only record is a title cannot be picked up by anyone who was not in
    # the conversation that created it. Supplying defaults HERE rather than
    # relaxing the tool keeps 70-odd tests about ids, columns and drift free of
    # noise they do not exercise, while the refusals stay real and are covered
    # by `TestATaskMustCarryItsDefinition`.
    ADD_DEFAULTS = ("--deliverable", "a thing that exists afterwards",
                    "--verification", "the suite is green")

    def run(self, *argv) -> tuple[int, dict | str]:
        if argv and argv[0] == "add" and "--deliverable" not in argv \
                and "--title" in argv:
            argv = (*argv, *self.ADD_DEFAULTS)
        r = subprocess.run(
            ["python3", str(TOOL), *argv, "--root", str(self.root), "--json"],
            capture_output=True, text=True)
        try:
            return r.returncode, json.loads(r.stdout or "{}")
        except json.JSONDecodeError:
            return r.returncode, r.stdout + r.stderr

    def board(self) -> str:
        return (self.root / "BOARD.md").read_text()

    def events(self) -> list[dict]:
        p = self.root / ".perry" / "events.jsonl"
        if not p.exists():
            return []
        return [json.loads(l) for l in p.read_text().split("\n") if l.strip()]

    def journal(self) -> str:
        for p in (self.root / "journal").rglob("*.md"):
            return p.read_text()
        return ""

    def import_board(self) -> None:
        r = subprocess.run(
            ["python3", str(TASKS), "write", "--from-board", "--root",
             str(self.root)], capture_output=True, text=True)
        if r.returncode:
            raise AssertionError(r.stdout + r.stderr)

    def __del__(self):
        self.dir.cleanup()


def mode_cells(self, project: Project, task_id: str) -> dict:
    board = project.board()
    header = next(line for line in board.split("\n") if line.startswith("| ID |"))
    row = next(line for line in board.split("\n")
               if line.startswith(f"| {task_id} |"))
    return dict(zip([PT.norm(cell) for cell in PT.split_row(header)],
                    PT.split_row(row)))
