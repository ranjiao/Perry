# TASK-146 — the viewer renders a KR's `current` with no provenance

> Source: `perry/evidence/2026-08/TASK-120-dispatch-2026-08-21-result.md`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: no
> Touches architecture: no — it moves a consumer onto a derivation that exists
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P2
- **Attribution**: unlinked

## The gap

TASK-120 landed on 2026-08-21 and made a KR's `current` **honest**: it is
reported as an author's assertion, with `current_provenance`,
`current_staleness` and `linked_task_completion` beside it, from one derivation
in `bin/lib`. `perry-goals/list` moved to `2.1` to carry them.

`viewer/serve.py` renders its chain view from `viewer/parsers.py` and **never
touches `bin/lib`**, so the viewer still shows the bare number. On this
repository that means it renders:

```
P002-O1-KR1   current 0.0 / target 1.0        → reads as 0% progress
```

while the payload says: **asserted, never measured, and all four of its linked
tasks are closed.** The viewer shows the one thing TASK-120 established you
cannot trust on its own.

## Deliverable

The chain view shows a KR's `current` **together with** whether it was asserted
or measured and whether it has gone stale — by reading `perry-state --json` or
the shared `bin/lib` derivation, **not by re-deriving it from
`viewer/parsers.py`.**

Which of those two, and why, is your call — but a third statement of the rule is
not on the table. `bin/lib`'s own docstring argues for importability, TASK-120
put the derivation there for exactly this reason, and TASK-148 shipped an AST
guard that fails when a rule is stated twice.

## Verification — V3

1. **The two KRs that made this a row.** `P002-O1-KR1` renders as an assertion
   contradicted by four closed tasks, not as 0% progress. `P002-O2-KR2` — `current 0`
   against `target 0` — does not render as met while 0 of its 2 linked tasks are
   closed.
2. **A stale assertion is visibly marked**, on a fixture whose linked task moved
   after the register's `updated`. And one that is not stale is not marked.
3. **Nothing is invented.** A KR whose `current` is absent renders as absent —
   not `0`, not `—%`. That default is the defect TASK-120 measured.
4. **Reverting reddens** the render, not only a helper's unit test.
5. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`, `git diff -- perry/` empty.

## Files in scope

- `viewer/serve.py`, and `viewer/parsers.py` **only** where it stops being the
  source of this number
- focused tests

## Out of scope

- The derivation itself, its keys, and `perry-goals/list`'s contract — TASK-120
  settled all three the day before.
- Any other view.
- Making the viewer write anything.
