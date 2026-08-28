# TASK-106 - Task summary is optional, explicit and preserved end to end

> Source: `perry/decisions/ADR-009-task-summary-field.md`
> Dispatch mode: auto
> Estimated cycle: medium
> Touches architecture: DESIGN-007 Task fields; task-list contract
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: P002-O3-KR1

## Deliverable

1. The canonical Task record gains optional prose `summary`. Missing legacy
   values normalize to an empty value; no migration or reader infers text from
   `title`, `next_action`, a specification, evidence or journal prose.
2. `perry-task add --summary` writes it at creation. A dedicated deterministic
   update command changes or explicitly clears it without changing status,
   title or next action. The event records `field: summary`.
3. Every unrelated Task mutation preserves `summary`, including start, status,
   next, retitle, rung, evidence, priority, dependency, done and drop.
4. `perry-task list --json` exposes `tasks[].summary` as a string. The
   versioned task-list contract, contract-shape fixture and semantics document
   are updated together; the change is additive and explicitly announced.
5. Store creation and `perry-migrate` produce an empty summary for legacy
   board rows and preserve a summary already present in a canonical store.
   Dry-run/apply equivalence and restore behavior remain TASK-044's guarantees,
   not weaker copies here.
6. `BOARD.md` remains a compact projection and does not gain a required Summary
   column. Rendering or any later writer must nevertheless preserve the stored
   value.
7. After TASK-105's typed lookup, `perry-explain TASK-*` prints the canonical
   title and the summary when set. An unset summary remains visibly absent and
   is not replaced with another field.

## Verification - V4

1. Create Tasks with no summary, an ASCII summary and a Chinese summary. List,
   store reload and explain output must preserve exact text and Unicode.
2. Update and clear a summary through the dedicated command. Assert that the
   event field is `summary` and no unrelated Task field changes.
3. Run every unrelated Task writer against a record with a sentinel summary;
   all must preserve it, including terminal transitions whose rows leave the
   board.
4. Load a legacy record with no `summary`; list emits an empty string and the
   next write adds or preserves the normalized field without refusal.
5. Migrate a legacy board and assert every created record has an empty summary.
   Start with an existing store carrying a sentinel summary and assert the
   migration path does not erase it.
6. Mutate the shared stored-field declaration, add path, update command,
   unrelated-writer preservation, list payload, migration default and explain
   rendering one at a time; each mutation must make a focused behavioral test
   fail.
7. Run focused Task-store/writer/list-contract/migration/explain tests,
   `python3 tests/parallel`, `bash tests/run`, `python3 bin/perry-lint`, and
   `git diff --check`.
8. A fresh-context reviewer who did not implement the change evaluates this
   specification. The implementing session cannot award V4 or close TASK-106.

## Dependencies

- TASK-105 - establishes typed Task lookup in `perry-explain` before the
  optional field is displayed there.
- TASK-044 - must land before TASK-106 changes migration code, so migration
  safety repairs are not mixed with a schema addition.

## Files in scope

- `bin/perry_store.py`, `bin/perry-task`, `bin/perry-migrate`,
  `bin/perry-explain`
- `schema/task-list-contract.md`, contract-shape fixtures and focused tests
- implementation and fresh V4 evidence

## Out of scope

- Inferring summaries for legacy Tasks.
- Making summary required or adding a required Board column.
- Rewriting titles, next actions, specifications or evidence.
- Goals/config stores, parser removal or migration of external live projects.
- Closing TASK-106 before fresh V4.
