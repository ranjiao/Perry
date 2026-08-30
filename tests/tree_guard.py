#!/usr/bin/env python3
"""The tree the suite starts in must be the tree it ends in — byte for byte.

## Why this exists (TASK-249)

`bash tests/run` wrote Perry state into the repository it ran in. One test —
`tests/test_task_writer.py § test_every_accepted_command_runs_and_is_advertised`
— walked `PT.COMMANDS` and invoked `bin/perry-task <name>` with **no `--root`**.
`perry-task` resolves its project root from `$PERRY_PROJECT`, else the cwd, and
`tests/run` cds to the repository root, so 29 real commands ran against the live
checkout. Twenty-eight of them refused for want of arguments. `intake-sweep`
takes none: it discharged a real board row and moved four files —
`.perry/events.jsonl`, `perry/BOARD.md`, `perry/intake.jsonl` and
`perry/journal/<today>.md`.

**It survived four months of green runs because the sweep is idempotent.** The
natural check — run the suite twice and diff — reports nothing, because the
first run leaves no discharged row for the second to find. Four agents
confirmed it in twelve hours; none of them were looking for it, and the only
reason it ever surfaced was that an append-only file conflicted at a merge. A
fast-forward would have carried a stray `intake-sweep` event with actor `agent`
into `main` in silence.

## Why a guard rather than only a fixture

The spec offered two shapes: a fixture that refuses a root inside the
repository, or this. **A fixture guard could not have caught this one** — the
offending call site does not go through any fixture. It builds its own `argv`
and calls `subprocess.run` directly, which is exactly why it was the call site
that got it wrong. A guard that compares the tree at both ends does not care
how the write arrived: fixture, bare subprocess, a stray `open(..., "w")`, or a
tool three layers down that resolved a root from the cwd.

## The blind spot the project had already declared

`tests/live_state_expectations.py § _tool_reads_this_project` decides which
project a test's tool call reads from `--root`, then `cwd=`, then a state path
among the arguments, and says of a call carrying none of the three: *"With none
of them the answer is no — the tool would in fact inherit the runner's cwd and
so read this repository, but `--help` and `--version` runs are the bulk of that
population and **none of them touches state**. A stated blind spot, not a
claim."*

TASK-249's call site is exactly that shape, and `intake-sweep` is the
counterexample to the sentence. The blind spot was declared honestly and the
population turned out to have one member that wrote. That is the argument for a
guard that watches the tree instead of reading the call: a static guard can only
be as good as its statement about what the un-analysable population contains.

## What it does NOT catch, said plainly

Each of these was found by a reviewer or by looking for it. They are listed so
that the next reader inherits the list rather than rediscovering it.

- **An idempotent write on an already-written tree.** The very sweep that
  motivated this file moves nothing on a tree it has already swept. The guard
  catches the *first* occurrence — which is the one that matters, and the one
  that would have been caught in the first place — not the steady state.
- **A write to a DIFFERENT checkout.** The guard hashes `$ROOT` and only
  `$ROOT`. A tool that resolves its root from `$PERRY_PROJECT` would write into
  whatever tree that names while the guard reports `$ROOT` unmoved — and this
  machine runs several worktrees, so it is not hypothetical. **`tests/run`
  closes the ambient case** by exporting `PERRY_PROJECT="$ROOT"` for the whole
  run, which pins every un-rooted write into the tree the guard is watching
  rather than letting it escape to a neighbour. What remains uncovered is a
  test that builds its own `env=` dict naming a third directory; nothing a
  tree comparison can do reaches that, and it is named here instead.
- **`.git`.** A test that runs `git commit` in the live root gets through.
  Hashing `.git` against a live repository would be slow and noisy — index and
  ref mtimes move under any concurrent git command, including a reviewer's
  `git log` in another terminal, and a guard that is red for reasons the reader
  did not cause is a guard that gets switched off.
- **`__pycache__` and `*.pyc` / `*.pyo`, at any depth.** Running the suite
  compiles the suite. This is deliberate and unbounded on purpose: bytecode
  legitimately appears beside any Python file.
- **A file named `.DS_Store`, at any depth.** Written by the Finder, not by a
  test, and it appears in whatever directory a human opened.
- **A write that is reverted before the suite ends.** Two writes that cancel
  are one tree.

The ignore list is **two directory names and two suffixes and one filename**,
and it was cut down to that: `.pytest_cache`, `.mypy_cache`, `.ruff_cache` and
`node_modules` were carried here from habit, and this repository contains none
of them and no tool that makes one. An ignore entry that matches nothing is a
blind spot held open for no benefit, so they are gone. All three lists are
pinned by `tests/test_tree_guard.py`, and separately the four files of TASK-249
are asserted to be visible to the manifest — because pinning a list by equality
catches a list that GREW and the thing to fear is a list that grew.

Usage:

    python3 tests/tree_guard.py snapshot <root> <manifest-path>
    python3 tests/tree_guard.py verify   <root> <manifest-path>

`verify` exits 1 and names every path that moved. The manifest belongs OUTSIDE
`<root>` — a manifest written into the tree it describes is itself a change to
that tree.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

#: Directories never descended into. Each one is here for a reason, and the
#: reason is in the docstring above — do not extend this list to make a red
#: run green. A red run means the suite wrote into the checkout, and the fix
#: is the write, not the guard.
IGNORE_DIRS = frozenset({".git", "__pycache__"})

#: Files never hashed. Compiled bytecode is a build artefact of running the
#: suite at all, and `.DS_Store` is written by the Finder, not by a test.
IGNORE_SUFFIXES = (".pyc", ".pyo")
IGNORE_NAMES = frozenset({".DS_Store"})


def _skip_name(name: str) -> bool:
    return name in IGNORE_NAMES or name.endswith(IGNORE_SUFFIXES)


def manifest(root: str | os.PathLike) -> dict[str, str]:
    """Map every path under `root` to a token that changes when it does.

    Files hash their bytes AND carry their permission bits: `chmod +x` on a
    shipped script changes what the tree is without changing a byte of it, and
    this repository ships eleven executables whose bit is load-bearing.
    Symlinks record their target rather than following it — a relinked symlink
    is a change even when both targets are identical. Directories are recorded
    too, with their mode, so that creating an empty one counts.
    """
    root = Path(root).resolve()
    out: dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORE_DIRS)
        here = Path(dirpath)
        for d in dirnames:
            p = here / d
            rel = str(p.relative_to(root))
            out[rel] = (("l:" + os.readlink(p)) if p.is_symlink()
                        else "d:%04o" % (p.stat().st_mode & 0o7777))
        for name in sorted(filenames):
            if _skip_name(name):
                continue
            p = here / name
            rel = str(p.relative_to(root))
            if p.is_symlink():
                out[rel] = "l:" + os.readlink(p)
                continue
            try:
                mode = p.stat().st_mode & 0o7777
                h = hashlib.sha256(p.read_bytes()).hexdigest()
            except OSError as exc:                     # unreadable is a state
                out[rel] = f"e:{exc.errno}"            # too, and it can change
            else:
                out[rel] = "f:%04o:%s" % (mode, h)
    return out


def compare(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Report every path whose token differs, as `+ / - / M` lines.

    Sorted, so the report of a run is comparable with the report of the next.
    """
    lines = []
    for rel in sorted(set(before) | set(after)):
        was, now = before.get(rel), after.get(rel)
        if was == now:
            continue
        if was is None:
            lines.append(f"  + {rel}   (created)")
        elif now is None:
            lines.append(f"  - {rel}   (removed)")
        else:
            lines.append(f"  M {rel}   (changed)")
    return lines


HEADLINE = ("tests/tree_guard.py: THE SUITE WROTE INTO THE TREE IT RAN IN — "
            "the checkout is not what it was when the run started")

EXPLAIN = """
A test wrote into the live repository instead of a temp root. This is a
failure of the suite, not of the guard: fix the write.

The usual cause is a Perry write-side tool invoked without `--root`.
`bin/perry-task` resolves its project root from $PERRY_PROJECT, else the
current directory, and `tests/run` runs from the repository root — so an
un-rooted `perry-task` call discharges real board rows. See TASK-249 and
`tests/tree_guard.py`'s docstring.

Restore the paths above (`git checkout --` for tracked ones, delete the
created ones) before you trust any board-dependent test result: three of
this suite's failures are data-dependent on board state.
""".rstrip()


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] not in ("snapshot", "verify"):
        print(__doc__.split("Usage:")[-1].strip(), file=sys.stderr)
        return 2
    mode, root, store = argv
    if mode == "snapshot":
        Path(store).write_text(json.dumps(manifest(root)))
        return 0

    before = json.loads(Path(store).read_text())
    lines = compare(before, manifest(root))
    if not lines:
        return 0
    print(HEADLINE, file=sys.stderr)
    for line in lines:
        print(line, file=sys.stderr)
    print(EXPLAIN, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
