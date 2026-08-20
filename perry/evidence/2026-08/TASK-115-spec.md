# TASK-115 — Two guards on the read-only report have a hole beside them

> Source: found by the V4 rubric review of TASK-079, 2026-08-20, by mutation rather than by reading
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P2
- **Attribution**: unlinked

## How these were found, because it matters

TASK-079 shipped with ten new tests, all green, and a fresh-context reviewer
scored every deliverable `MET`. The two holes below were invisible to that —
they surfaced only when the reviewer **mutated the production code and watched
which tests failed**. Five of six mutations were caught. These are the two that
were not.

Nothing here is broken today. What shipped is correct. What is missing is the
guard that keeps it correct.

## Deliverable

1. **The wording guard covers the machine-readable plan.** TASK-079's deliverable
   4 required that the emitted wording *"states what was observed, not what
   should happen"* — the refuse-versus-report policy is USER-004 and unanswered.
   That is enforced today on the rendered note only. The reviewer mutated the
   `--json` plan's `read_only_override.observed` string
   (`bin/perry-migrate:377-379`) to *"read-only for its owner; you should chmod
   it"* and **all ten tests stayed green.** A policy word can enter through the
   machine surface undetected. Cover it with the same guard.
2. **The task-store path has a test behind it.** `_plan_task_store` sets
   `read_only_mode=owner_read_only(store_path)` (`:1690`). Deleting that line
   leaves all ten tests green, so a read-only `tasks.jsonl` would silently lose
   its report. That file appears in the per-file list, so it is inside TASK-079's
   deliverable 1, and it is currently the only reported file with no test behind
   it.

## Verification — V3

1. **The exact two mutations that survived are now caught.** Injecting
   `you should chmod it` into `read_only_override.observed` fails a test.
   Deleting `read_only_mode=owner_read_only(store_path)` from `_plan_task_store`
   fails a test. Demonstrate both by making the mutation and showing the red,
   not by asserting that a test exists.
2. The ten existing tests stay green and **none is weakened** to achieve it.
   Show the count before and after.
3. Re-run the reviewer's other four mutations and confirm they are still caught,
   so this change does not trade one hole for another: dropping
   `and self.writable`; reporting every file; adding a policy word to the
   rendered note; dry-run only.
4. `python3 tests/parallel`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `bin/perry-migrate` — only if the guard needs a seam; prefer changing tests
- `tests/test_migrate.py`

## Out of scope

- The read-only **policy**. Whether migration should refuse such a file is
  USER-004 and is still unanswered. Do not implement a refusal, and do not let a
  policy word into either surface while adding the guard against policy words.
- The rendered note's current wording, which is correct.
- `write_atomic`, the restore-point format, migration ordering.
- `schema/state-schema.json`, `claims`, anything under `perry/`.
- Closing without the V3 evidence above.
