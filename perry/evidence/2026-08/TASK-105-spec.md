# TASK-105 - perry-explain resolves Tasks from the typed Task domain

> Source: `perry/decisions/ADR-009-task-summary-field.md`
> Dispatch mode: auto
> Estimated cycle: small
> Touches architecture: DESIGN-007 typed identity lookup
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: P-O3.1

## Deliverable

1. When a project has a canonical Perry Task store, a single
   `perry-explain TASK-*` lookup reads that typed store through the shared Task
   record validator. It does not use a Markdown table, heading, filename or
   journal mention as the Task definition.
2. The lookup includes open, done and dropped Tasks. It returns the canonical
   title and current typed status from the stored record.
3. If the store exists and the requested `TASK-*` id is absent, the command
   reports it as absent from the Task store and does not fall back to the
   generic Markdown harvester. A design or evidence document mentioning that
   id cannot become its definition.
4. If the project has no Perry Task store, the existing generic cross-project
   lookup behavior remains available unchanged.
5. Malformed Task-store input is reported as a named refusal rather than
   silently falling back to Markdown or emitting a traceback.
6. Human and JSON output describe the same canonical Task. No output invents a
   summary before TASK-106 adds that field.

## Verification - V3

1. Reproduce the reported bug with a fixture where a design table names
   `TASK-091` and gives it the apparent title `2`, while `tasks.jsonl` carries
   the real title. Both human and JSON output must use the store title.
2. Resolve one open, one done and one dropped Task from the store.
3. Request an id absent from a present store while Markdown defines it; assert
   that lookup fails without scanner fallback.
4. Remove the store and assert that the same Markdown-only fixture retains the
   old generic behavior.
5. Exercise malformed JSONL, a non-object record, a missing id and a duplicate
   id. Each case must fail deterministically through the shared validator.
6. Run the focused explain tests, `python3 tests/parallel`, `bash tests/run`,
   `python3 bin/perry-lint`, and `git diff --check`.

## Files in scope

- `bin/perry-explain`
- focused `perry-explain` tests
- command documentation only when behavior changed by this task requires it

## Out of scope

- Adding or writing the Task `summary` field; TASK-106 owns it.
- Changing Task-store schema, migration or the public task-list contract.
- Replacing generic lookup for non-Task namespaces or projects with no Perry
  Task store.
- Closing TASK-105 without the V3 evidence above.
