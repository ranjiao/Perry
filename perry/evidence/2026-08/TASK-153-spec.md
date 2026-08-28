# TASK-153 — `perry-diagnose` counts test fixtures as the project's own state

> Source: found independently by two agents on 2026-08-21, reproduced by the PMO
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: no
> Touches architecture: it decides what `perry-diagnose` is FOR — see below
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## The measurement, made three times

```
tests/test_diagnose.py:1161
DecisionsAreCountedPerRecordNotPerMention
  .test_the_queue_register_reconciles_with_the_queue_on_this_repository
AssertionError: 1 != 0 : diagnose and perry-task disagree about how many
                         queue rows are waiting on the user
```

```
open_decisions_by_register : {"queue": 1, "design": 0}
sample                     : tests/fixtures/sample-project/BOARD.md:36 — USER-014
perry-task list --all      : asks.open = 0
```

`perry-diagnose` scans the **whole repository**, including test fixtures, and
counts a fixture's `USER-014` as one of Perry's *own* open decisions.
`perry-task` reads only `perry/BOARD.md`, where all four USER rows are answered,
and reports 0.

**It surfaced only once every one of Perry's own queue rows was answered** — the
fixture had always been counted; there was simply always a real row beside it.

This is the last red in the suite: **72 modules · 2078 tests · 1 red**, and it is
this one.

## The decision this row makes, which is bigger than the red

Two candidate answers, and **they are different claims about what
`perry-diagnose` is for**:

1. **`perry-diagnose` excludes `tests/fixtures/`** — it is a tool that reports on
   *a project*, and a fixture is a test's private furniture, not the project's
   state. But `perry-diagnose` runs on **any folder**, including ones that have
   never heard of Perry, and a hard-coded `tests/fixtures/` is a guess about
   somebody else's layout. `perry-explain` already faces this and answers it with
   `is_illustrative` — **read how, and say whether that is the same question.**
2. **The reconciliation check scans a fixture project** rather than the live
   repo. Honest, cheap — and it gives up the property the test was written for,
   which is that *this* repository's two tools agree.

**Pick one with the argument.** Do not do both, and do not add a flag that lets
a caller choose — this repository has a rule that a second way to answer one
question is the defect, not the feature.

## Verification — V3

1. **The two tools agree on this repository.** Whichever answer you take,
   `test_the_queue_register_reconciles_with_the_queue_on_this_repository` passes
   for a reason you can state in one sentence.
2. **A project that genuinely has an open queue row still reports it** — both in
   `perry-diagnose` and in `perry-task`. If your fix is exclusion, prove that a
   *real* `USER-*` row under the state root is still counted; if it is a fixture,
   prove the fixture actually contains one.
3. **The exclusion does not swallow more than it should.** If you take answer 1:
   name every path shape it now skips, and show a project whose real state
   happens to live under a similarly-named directory is unaffected. That is the
   failure mode of every path-based rule this project has written.
4. **Reverting reddens exactly this test** and nothing else.
5. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`, `git diff -- perry/` empty.

## Files in scope

- `bin/perry-diagnose`, or `tests/test_diagnose.py` — depending on which answer
  you take. **Not both** unless the argument requires it, and then say why.
- focused tests and fixtures

## Out of scope

- `perry-explain`'s `is_illustrative` and `in_tracking_doc` gates — read them,
  do not change them.
- The `user_load` dangling-id rules (TASK-126 and TASK-149, both landed).
- Anything under `perry/`.
