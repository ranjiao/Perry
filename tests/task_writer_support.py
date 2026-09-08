"""Shared fixtures for the task-writer contract tests."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

import config_store
from config_store import track as _track

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


#: One track per DESIGN-003 mode. **Records, not a `## Tracks` table.** They
#: were the table until ADR-019 deleted the file it lived in; a fixture still
#: writing one declares nothing, and `perry-task add --track ops` then refuses
#: by name rather than exercising queue mode at all.
BASIC_MODE_TRACKS = [
    _track("core", "project", spine="phase/", default_rung="V3"),
    _track("blog", "pipeline", spine="commitments",
           stages="brief->draft->published", wip="review:2", sla="5d",
           cycle="2026-W34", default_rung="V5"),
    _track("ops", "queue", spine="commitments",
           stages="new->triaged->resolved", sla="5d", cycle="monthly",
           default_rung="V2"),
    _track("study", "inquiry", spine="questions",
           stages="open->researching->answered", wip="open:5",
           default_rung="V4"),
]

#: The same four with `review` and `in_progress` back in the two staged
#: vocabularies — the difference the mode tests turn on.
MODE_TRACKS = [
    _track("core", "project", spine="phase/", default_rung="V3"),
    _track("blog", "pipeline", spine="commitments",
           stages="brief->draft->review->published", wip="review:2", sla="5d",
           cycle="2026-W34", default_rung="V5"),
    _track("ops", "queue", spine="commitments",
           stages="new->triaged->in_progress->resolved", sla="5d",
           cycle="monthly", default_rung="V2"),
    _track("study", "inquiry", spine="questions",
           stages="open->researching->answered", wip="open:5",
           default_rung="V4"),
]

class Project:
    """A throwaway Perry project the tool can write into."""

    def __init__(self, tracks: list[dict] | None = None, board: str = BOARD):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / ".perry").mkdir()
        # **A string is refused rather than ignored.** `tracks` was a `##
        # Tracks` table until ADR-019, and a fixture still passing one would
        # write settings, declare no track, and then fail somewhere far away
        # with "track 'ops' is not declared" — which is the same message a
        # genuine typo produces. Fail here, at the fixture, naming the change.
        if isinstance(tracks, str):
            raise AssertionError(
                "Project(tracks=...) takes track RECORDS, not a `## Tracks` "
                "markdown table: ADR-019 deleted `.perry/config.md` and "
                "nothing reads one. Use `config_store.track(name, mode, ...)`, "
                "or one of MODE_TRACKS / BASIC_MODE_TRACKS above.")
        config_store.write_config(self.root, tracks=tracks or [])
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
    #: `--summary` joined the refusals under TASK-325, and is injected
    #: SEPARATELY from the pair above because a test that supplies its own
    #: deliverable inline still needs one. It has to satisfy the same
    #: structural rules the tool enforces — a sentence, five words or more,
    #: and not the title again — so it is deliberately generic enough never to
    #: fold onto any fixture title.
    SUMMARY_DEFAULT = ("--summary",
                       "A fixture row that exists so the writer has something "
                       "to write. It carries no meaning beyond that.")

    def run(self, *argv) -> tuple[int, dict | str]:
        if argv and argv[0] == "add" and "--deliverable" not in argv \
                and "--title" in argv:
            argv = (*argv, *self.ADD_DEFAULTS)
        if argv and argv[0] == "add" and "--summary" not in argv \
                and "--title" in argv:
            argv = (*argv, *self.SUMMARY_DEFAULT)
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
