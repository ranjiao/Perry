"""This repository's board, as `perry-tasks board` prints it from the stores.

**Why this exists (TASK-237 deliverable 3c).** `perry/BOARD.md` is deleted.
Several modules copied or read that file because their subject was "a real,
large board": the projection verbs' byte gate, the risk register's shape, the
row round-trip, the drift messages. Those subjects did not go away with the
file — a project that still holds a board is exactly what `render`, `diff`,
`verify` and the `--from-board` imports serve — but the corpus has to come
from somewhere that is not a file this repository no longer carries.

It comes from the stores, through the one command a person now reads a board
with. Measured at 3c on a scratch copy of this repository: over this output
`perry-tasks render` is byte-identical to the file, `diff` and every
`*-diff` exit 0, and `verify` reports 0 mismatches.

**What a test built on this no longer proves**, and each module says so where
it matters: that a HAND-KEPT board round-trips. Every row here was written by
a tool. The hand-written shapes are the fixtures' job (`SECOND_PROJECT_BOARD`,
`ROUND_TRIP_BOARD`), and they are unchanged.
"""

from __future__ import annotations

import pathlib
from functools import lru_cache

import inproc

ROOT = pathlib.Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def printed_board() -> str:
    """The text `perry-tasks board --root <this repository>` prints."""
    proc = inproc.run("perry-tasks", ["board", "--root", str(ROOT)])
    if proc.returncode != 0 or not proc.stdout.startswith("# "):
        raise AssertionError(f"perry-tasks board printed no board for "
                             f"{ROOT}: exit {proc.returncode}, "
                             f"{proc.stderr[-400:]}")
    return proc.stdout


def put_printed_board(state_root: pathlib.Path) -> pathlib.Path:
    """Write `printed_board()` as `<state_root>/BOARD.md`; return its path."""
    path = pathlib.Path(state_root) / "BOARD.md"
    path.write_text(printed_board(), encoding="utf-8")
    return path
