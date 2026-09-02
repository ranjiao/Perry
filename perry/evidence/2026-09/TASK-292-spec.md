# TASK-292 — spec

> Dispatch mode: auto
> Executor: claude-subagent (one fixture or one function, stdlib only, no MCP)
> Estimated cycle: small
> Subjective verification: which of the two defects to fix is a judgement — say which you chose and why
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: intake / queue
- **Dependencies**: —
- **KR linkage**: declared unlinked
- **Verification rung**: V4

## Why

`tests/test_parsers.py § test_locked_design_without_impl_rows_is_flagged`
asserts the FIXTURE's `pending_handoff` is `['DESIGN-001']` and gets `[]`. The
suite is red on this now.

`impl_refs` walks **up to four parent directories** looking for
`.perry/events.jsonl` when the caller passes no `project_root`. The fixture at
`tests/fixtures/sample-project` has a `.perry/` directory but no
`events.jsonl`, so the walk climbs out of the fixture and reads the **host
repository's** log. Perry's own PMO events that merely mention the string
`DESIGN-001` then count as implementation references for the fixture's design.

**It is getting worse while unfixed.** Measured 2026-09-02: the fixture's
`DESIGN-001` was at `impl_refs: 2` at 14:0x and `impl_refs: 6` at 15:3x, with
no change to the fixture — only PMO prose accumulating in the live log.

**A worktree observation to check, not to trust.** A dispatched agent in an
isolated worktree reported the full suite green on the same commit range.
`.perry/events.jsonl` is git-tracked, so each worktree carries its own copy at
its own branch point, and the walk stops there. That would explain the
difference, and if it does, it is further evidence rather than a contradiction
— the same fixture answers differently depending on which checkout it is run
from. Confirm or refute it; do not assume it.

## Files in scope

- `viewer/parsers.py` — the upward walk, around :3298-3311.
- `tests/fixtures/sample-project/.perry/` — if the fix is fixture-side.
- `tests/` — the guard.

Re-derive line numbers before editing.

## Deliverable

The fixture's answer does not depend on the repository it is run from. **Two
defects are available and the row should say which it fixed and why the other
was left:**

1. **Test isolation** — give the fixture its own `.perry/events.jsonl` so the
   walk stops inside it. Minimal, and it fixes the red test.
2. **The walk itself** — a caller that cannot say which project it means
   arguably deserves no log rather than someone else's. Larger, and it changes
   behaviour for every caller of `impl_refs`.

Fixing 1 alone is acceptable **if the row says so** and leaves 2 named.

### A third option was raised and is answered here, not left open

*"Is the test simply too strict?"* — asked by the user 2026-09-02. **No, and
loosening it is refused as a fix.** A looser assertion would not have avoided
the defect; it would have HIDDEN it. The fixture's `pending_handoff` is wrong
whatever shape the assertion takes, because it is computed partly from the host
repository's event log — `assertIn`, a count, or a subset check would all read
the same corrupted value and simply not complain. The strictness is what
surfaced a cross-project read, which is the test doing its job.

What the question correctly points at is one level down: `impl_refs` itself is
a poor measure. `impl_refs = sum(1 for blob in task_blobs if doc_id in blob)`
is a literal substring count over board-task text plus every event-log line, so
it is wrong in **both** directions — measured 2026-09-02: `TASK-001`–`TASK-006`
are DESIGN-001's real implementation, all six done, and count **zero** because
they never wrote the id; `TASK-282` merely says "read DESIGN-001" and counts
**one**. That is `TASK-282`'s subject and is out of scope here. **Do not close
this row by weakening the assertion.**

## Out of scope

- **Rewording the PMO rows that mention `DESIGN-001`.** The prose is correct,
  the finding it records is real, and the test is what is wrong. A fix that
  edits `perry/BOARD.md`, `perry/tasks.jsonl` or the event log to make a test
  pass is refused.
- `impl_refs`' text matching in general — that is `TASK-282`, and it is the
  wider defect this one is an instance of.
- `schema/state-schema.json` and any declaration file.
- Any project other than Perry's own.

## Verification

- **Reproduce first**: show the fixture's `DESIGN-001` picking up `impl_refs`
  from the host repository's log, and name the events it read.
- After the fix, the fixture's `pending_handoff` is `['DESIGN-001']` again and
  **does not move** when a new event mentioning that id is appended to the host
  log. Append one and show it.
- `tests/test_parsers.py` is green.
- **Mutation**: revert the fix and the reproduction returns. A green mutation
  is a finding either way.
- Clear `__pycache__` and wait past the second boundary before re-running.
- `bash tests/run`: baseline failure count and the runner that produced it.

## Bound

The finite set: **one test module (`tests/test_parsers.py`), one fixture
(`tests/fixtures/sample-project`), and one function (`impl_refs`' log walk in
`viewer/parsers.py`).** Size 3. Any other fixture that reads host state is a
NEW ROW to record, not an extension of this round.
