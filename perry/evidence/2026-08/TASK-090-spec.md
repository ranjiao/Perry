# TASK-090 — `perry-task` reads the task store, not task rows in `BOARD.md`

> Source: `perry/design/DESIGN-007-the-entity-model.md § 6` step 1,
> `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md`, and
> `perry/evidence/2026-08/TASK-089-spec.md`
> Dispatch mode: auto
> Executor: codex (high confidence — repository-local code and tests, no MCP dependency)
> Estimated cycle: large
> Subjective verification: (none)
> Touches architecture: §6 step 1
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: P-O1.1, P-O3.2

### Deliverable

1. Every current Task field is loaded from validated `perry/tasks.jsonl`.
   `BOARD.md` is never consulted to decide a task's value, existence, status,
   dependencies, order, startability, or current evidence relation.
2. `perry-task list --json` preserves the published task payload shape under
   `perry-task/list/1.10` and derives task counts, dependency inverses,
   `blocked_by`, `startable`, and timelines from the store plus the disposable event log.
   Deleting the event log may remove history detail but cannot change current
   Task truth. Per the user decision on 2026-08-19, typed `status` is the only
   status truth; `status_text` remains a string key as its legacy display alias
   and no longer carries raw Board text. This semantic change is announced in
   the contract's `semantics` array.
3. Every command that names or mutates a Task resolves its baseline record,
   duplicate-id checks, dependency graph, and id-mint inputs from the store.
   A board-only edit cannot become task truth on the next unrelated write.
4. Read-only Task paths do not require a task table in `BOARD.md`.
   `perry-task events` and the task portion of `list --json` remain usable when
   `BOARD.md` is absent. If the multiplexed list cannot read its non-Task
   registers, it keeps their existing keys empty and reports the missing board
   in conformance rather than failing or fabricating data.
5. The remaining Board reads are enumerated and category-bounded:
   non-Task registers (`risks`, `asks`, `intake`, `cadence`) and projection
   layout may remain board-backed. They cannot influence `tasks[]` or any
   task-derived field. Removing those exceptions belongs to later entity-store
   work and TASK-094/TASK-095.
6. Store validation failures are structured refusals/findings with no raw
   traceback. A malformed or wrong-typed store is never replaced from the
   board as recovery.
7. Migration and contract shape invariance remain green. A consumer moving
   from 1.9 to 1.10 loses no key and sees no type change; it must acknowledge
   the announced `status_text` semantic change if it relied on raw Board text.

### Verification — V4

1. Delete `BOARD.md`: `events` and the task portion of `list --json` still
   return current records; non-Task register keys remain shaped and the missing
   projection is reported.
2. Change a Task only in the store: the next list reflects it. Change a task
   row only in the board: list and a subsequent unrelated write retain the
   store value.
3. Delete `.perry/events.jsonl`: current fields, dependencies, open/closed, and
   startability remain correct; only derived history may shrink.
4. Mutate each remaining Task read of `BOARD.md` back into the code and show a
   focused guard goes red. A grep count without a behavioral mutation is not
   sufficient.
5. Malformed store shapes and wrong-typed fields return normal JSON refusal or
   lint findings, never `TypeError` or partial writes.
6. Run focused store/task/contract/migration suites, the full parallel suite,
   `bash tests/run`, `python3 bin/perry-lint`, and `git diff --check`.
7. The 1.10 payload reports the `status_text` semantics entry, and a Board-only
   status edit changes neither `status` nor `status_text`.
8. A fresh V4 reviewer works on disposable copies and records untested
   filesystem/platform cases.

### Dependencies

- TASK-089 — done at V4. The task store is the write target and the board is a
  projection before this read cutover begins.

### Out of scope

- Creating stores for risks, asks, intake, cadence, goals, config, agents, or
  runs.
- Removing Markdown layout parsing used only to render projections
  (TASK-094/TASK-095).
- TASK-092's goals/config migration and TASK-102's typed document relations.
- Public API shape changes beyond an additive conformance signal for a missing
  projection. The authorized 1.10 `status_text` meaning change is in scope.
- Closing TASK-090. Implementation returns it to `review`; fresh V4 closes it.

## Scope decision

This is the recommended **task-only cutover**. Expanding the task into stores
for every non-Task register would combine several entities under one id and
contradict DESIGN-007's ordered plan. The exceptions above are explicit so
they cannot quietly become a second source of Task truth.
