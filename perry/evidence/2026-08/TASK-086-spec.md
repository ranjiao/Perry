# TASK-086 — Default lint emits NS-01, as DESIGN-002 decision 4 says it does

> Source: `perry/design/DESIGN-002-namespace-collision.md` § Where the check runs, row `perry-lint` default mode (locked 2026-08-16)
> Dispatch mode: auto
> Executor: claude-subagent (repository-local lint behaviour and fixtures; this project routes all automated dispatch to claude-subagent)
> Estimated cycle: small
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P2
- **Attribution**: unlinked

## Deliverable

1. On an adopted project, a plain `perry-lint` run — no flags — performs the
   same namespace check that `--claims` performs today, and emits `NS-01` at
   `warn` when a directory Perry claims holds files Perry did not write.
   DESIGN-002 says this closes P4; `bin/perry-diagnose` already emits the
   finding and default lint does not, so the decision is implemented in one of
   the two places it names.
2. `NS-01` stays `warn` and never becomes `error`, so a user can knowingly live
   with a collision. A permanently red lint with no way to accept it is the
   outcome DESIGN-002 rejects by name.
3. The finding's text matches the catalog entry already in
   `reference/diagnose.md`: what it is, why it bites, the two remedies
   (relocate the state root, or move the file), and the offending paths as
   evidence.
4. A project that is not adopted, and a project with no collision, produce
   byte-identical lint output to today's.
5. `--claims` keeps working exactly as it does now, including `--state-root`.

## Verification — V2

1. Fixture: an adopted project whose claimed directory holds a file Perry did
   not write. Assert a flagless lint run emits `NS-01`, at `warn`, with that
   path as evidence.
2. Assert the exit code is unchanged by a warn-level finding.
3. Fixture with no collision: assert output is byte-identical to today's.
4. Fixture that is not adopted: assert the check does not run.
5. Assert `--claims` output is unchanged.
6. `python3 bin/perry-lint` on this repository, `python3 tests/parallel`,
   `bash tests/run`, `git diff --check`.

## Files in scope

- `bin/perry-lint` — the default-mode pass and its `NS-01` emission
- focused lint tests and fixtures

## Out of scope

- **Editing `schema/state-schema.json`, and in particular `claims[]`.** This
  task READS the claim list that is already declared there and changes no entry
  in it; it does not add, remove or repoint any path Perry claims in anyone's
  project. Adding `tasks.jsonl` to `claims[]` is TASK-100 and stays there.
- Moving anyone's files, or running `relocate`. The finding recommends; it never acts.
- Raising `NS-01` above `warn`.
- Changing `bin/perry-diagnose`'s existing emitter or the catalog text.
- Closing TASK-086 without the V2 evidence above.

## Changes

- 2026-08-20 — `Executor` changed from `codex` to `claude-subagent`. The user
  declared that this project's codex quota is not to be spent on dispatch, and
  that every automated dispatch goes to `claude-subagent` from now on. The
  routing reason originally recorded ("self-contained, no MCP dependency") was
  a correct reading of the executor-choosing rules and is simply overridden by
  a quota constraint the rules do not model. Nothing about the task's scope,
  deliverable or verification changed.
