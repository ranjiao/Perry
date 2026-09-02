# TASK-258 — spec

> Filed 2026-08-30 from the `TASK-249` rounds
> Dispatch mode: auto
> Executor: claude-subagent (one test module, stdlib only, no MCP)
> Estimated cycle: small
> Subjective verification: (none) — the acceptance is a reproduction and a mutation
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked — test-suite reliability, not a phase-003 KR
- **Verification rung**: V4

## Why

`tests/test_tree_guard.py:102` builds its fixture with
`shutil.copytree(PERRY_HOME, ...)` over the **live** repository. Any write
landing in the tree while that copy runs makes the copy inconsistent, and the
module reddens for a reason that has nothing to do with what it tests.

The row's own summary states why four review rounds missed it: all four ran in
private worktrees where nothing else was writing, *"which is exactly why a test
that depends on the tree being still passed four reviews"*. It surfaced the
first time the module ran in the live repository.

**The condition is not hypothetical and is live today.** On 2026-09-02 this
repository has a dispatched agent editing `bin/` and `tests/` while the PMO
writes board and journal state on every command — precisely the concurrency the
fixture cannot survive.

The project already has the stable pattern and used it elsewhere: the `TASK-235`
review ran every destructive probe against `git archive` copies of a commit
rather than against a working tree.

## Files in scope

- `tests/test_tree_guard.py` — `copy_repo` at :95-105, and any test that
  depends on its behaviour.

That is the whole surface. No tool under `bin/` changes.

## Deliverable

`copy_repo` builds its fixture from a **stable snapshot** rather than from the
live working tree, so a concurrent write cannot redden the module.

Take the snapshot from a committed state — the pattern the `TASK-235` review
used — rather than by copying a directory that another process may be writing.
Keep the existing exclusions (`.git`, `__pycache__`, `*.pyc`, `*.pyo`) and the
docstring's reason for them: a stale bytecode file beside a source whose mtime
no longer matches is its own class of false result.

If the module genuinely needs uncommitted working-tree content for some test,
say so and fence that case explicitly rather than reverting the whole change.

## Out of scope

- Every other test module. This row is one fixture helper.
- `bin/` and `viewer/` — no tool changes.
- The tree guard's own algorithm. `TASK-249` settled that; this is its fixture.
- Any project other than Perry's own.

## Verification

- **Reproduce the failure first, then fix it.** Run the module while writing to
  the repository in a loop, and show it reddening. A fix whose failure was never
  reproduced is a guess. If it will not reproduce, say so — that is a finding
  about the row, not a licence to change the code anyway.
- After the change, the same concurrent-write loop leaves the module green.
- **Mutation, and the acceptance turns on it**: revert `copy_repo` to the live
  copy and show the concurrent-write reproduction goes red again. A green
  mutation is a finding either way — the fix does not work, or the test does not
  test it (`work/reference/review.md § 2`).
- Clear `__pycache__` and wait past the second boundary before re-running:
  CPython validates bytecode on whole-second mtime plus size, so a same-size
  edit reverted inside one second runs stale bytecode and shows a result that
  never happened.
- `bash tests/run` overall: report the baseline failure count you started from
  and the runner that produced it. This project has two runners that disagree,
  so a bare number is not evidence.
