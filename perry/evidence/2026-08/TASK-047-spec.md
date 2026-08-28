# TASK-047 — Flip the conformance gate to enforce

> Source: `perry/decisions/ADR-004-mandatory-migration.md`; unblocked by TASK-044 (migration) landing 2026-08-19
> Dispatch mode: auto
> Executor: claude-subagent (repository-local behaviour change across a writer gate, its schema default and its tests; needs codebase familiarity)
> Estimated cycle: medium
> Subjective verification: whether `enforce` is the right default now, versus keeping `advisory` and enforcing only under an explicit opt-in
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## Deliverable

1. The conformance gate's default mode changes from `advisory` to `enforce`.
   The default is declared in `schema/state-schema.json` under the conformance
   block; the `PERRY_CONFORMANCE` environment variable keeps overriding it.
2. Under `enforce`, a writer refuses to write a state file that is not declared
   conformant, naming the file, the shape version it was checked against, and
   the exact command that declares it.
3. The two documented exemptions survive the flip and are covered by a test
   each: `perry-goals commit --migrate` is exempt, and `bin/perry-migrate` is
   exempt — the migration is how an undeclared project becomes declarable, so a
   gate that refuses it is a wall with no door.
4. The refusal message names `bin/perry-migrate` as the way forward. The reason
   this gate shipped `advisory` was that the migration did not exist yet; it
   does now, so the refusal can point somewhere real.
5. Every file this project currently reports as `undeclared` is listed in the
   dispatch RESULT notes, not silently declared. Declaring them is the user's
   act, never the agent's.

## Verification — V4

1. Fixture: an undeclared state file plus a writer call that would modify it.
   Assert the refusal, and assert its text names the file and a runnable
   declare command.
2. Same fixture with `PERRY_CONFORMANCE=advisory` — assert the write proceeds
   and says so.
3. Assert `perry-goals commit --migrate` writes an undeclared file without
   refusal.
4. Assert `bin/perry-migrate` runs to completion against an undeclared project.
5. `python3 bin/perry-lint` exits clean on this repository, and
   `python3 bin/perry-conform status` still reports the same per-file verdicts
   as before the change.
6. `python3 tests/parallel`, `bash tests/run`, `git diff --check`.

## Files in scope

- `bin/perry-conform`
- `schema/state-schema.json` — the conformance default value only
- the writers that consult the gate
- focused conformance tests

## Out of scope

- Declaring any file conformant on the user's behalf. `perry-conform declare` is
  the user's command; adoption proposes, the user declares.
- **`schema/state-schema.json § claims[]` — the claim surface is untouched by
  this task.** No path Perry claims in anyone's project changes.
- Changing the shape version, or what "conformant" means for any file class.
- Changing `bin/perry-migrate`'s behaviour beyond confirming its exemption.
- Closing TASK-047 without the V4 evidence above.

## Changes

- 2026-08-20 — **High-stakes gate overridden by the user, explicitly.** The
  dispatch pre-flight safety scan matched `state-schema.json` in this spec's
  `Deliverable` and `Files in scope`, against `.perry/hook.md`'s "The claim
  surface" rule. That match is substantive, not a substring artifact: this task
  really does edit `schema/state-schema.json`. It edits the conformance default
  only — `advisory` to `enforce` — and no entry in `claims[]`. The user was
  shown that distinction, including that the flip changes upgrade behaviour for
  every existing Perry project and not only this repository, and cleared it for
  automated dispatch. Recorded here because a gate that is overridden without a
  written trace is a gate that was never really armed.
- 2026-08-20 — Dispatched via `claude-subagent` in an isolated git worktree,
  with `PERRY_MAX_DISPATCH_SUBAGENT` raised from 2 to 3 by the user to make the
  third concurrent slot available.
- 2026-08-20 — Corrected the `Source:` path. It read
  `perry/decisions/ADR-004-conformance-marker.md`, which does not exist and
  never did; ADR-004 is `ADR-004-mandatory-migration.md`. The id was right and
  the decision was the right one — the filename was invented from the subject
  matter instead of read off the filesystem. Caught by the user, not by any
  check: `ADR-004` resolves as an id, so the dangling-id check passes, and
  nothing validates that a `> Source:` path exists. The dispatch prompt happened
  to carry the correct path, so the agent read the real file.

