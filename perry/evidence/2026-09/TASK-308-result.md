# TASK-308 — result (IN PROGRESS)

- **Branch**: `coding/task-308-bound-before-the-round`
- **Branched from**: `548f206` ("Escalation override recorded before either row is dispatched"), which is `main` at dispatch time.
- **Worktree cut at**: `d49964e` — ~140 commits behind, the stale cut the brief warned of. Re-branched onto `548f206` before any work.

## What this row is about to do

Make a spec's missing `## Bound` reportable **before** a review round, from the
spec-side pass in `bin/perry-lint` that already reports `spec-scope-unscannable`
and runs under the default `perry-lint --root .`. The existing verdict-side
check at `bin/perry-lint:2458` stays — it answers a different question.

Steps, in order:

1. Measure the before-state (specs on disk / carrying a bound / `criteria-unbounded` reported).
2. Add the spec-side check with a chosen, argued severity — not 127 warnings.
3. Fixture for the main property: a spec with no bound and **no review document anywhere**.
4. Control: a spec that has a bound is silent.
5. Mutation-test the new call site; verify restores against `git show`.
6. Full suite vs. measured baseline.

_This stub exists so the round survives a watchdog. It is replaced on completion._
