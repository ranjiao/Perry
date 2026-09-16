# TASK-289 round 2 — goals writes require an actor

Date: 2026-09-16. Coding branch: `codex/task-289-round2`.
Base before round-2 changes: `c828b13f41d094cf5120febc45ec9a46f84ef241`,
which integrates immutable TASK-264 `0fbe8d48` and TASK-289 round 1
`ff7a86ac`. Before committing, integrated current main `a93ee34c` at
`7cb843ed805f0d744c0c2a9f30a868503c3550de` (PMO evidence and criteria only).
Implementation head: the commit carrying this result; the exact SHA is in
the hand-off. Neither prior implementation branch was modified.

## Scope and behavior

`perry-goals commit` and `link`, in all existing modes, now require an
explicit actor. Missing, empty, whitespace-only, LF and CR values return
usage exit 2 before root resolution, installation gates, locks or writes.
The error names the flag, examples of an owner and a command usage example.
The write-side `agent` default is removed. Read fallbacks are untouched.

All four goals writers call the same `lib.actor_refusal` as `perry-task`.
Its optional `single_line=True` preserves the existing goals requirement;
the default remains false, so this round does not expand perry-task's
accepted-value policy. The helper only validates. Commit/link retain valid
actors verbatim, including surrounding spaces, while check/measure retain
their pre-existing `.strip()` normalization. No new identity interpretation
or rewrite is introduced.

`ACTOR_SURFACE` adapts goals' existing COMMANDS/write dispatch to the shared
validator, without claiming conversion of the legacy parser to a complete
SURFACE. `READ_COMMANDS` identifies list/krs; other declared commands follow
the existing write gate. Per-command KR flags and malformed invocation
refusals still precede actor validation. List/krs remain actor-free.

Executable examples were updated only in goals/reference/{phases,linkage,
weekly}.md and reference/okr-linkage.md. The help examples name the actor.
Historical evidence/journals were not rewritten. The router budget check
passes; no budgeted SKILL page needed a change in this round.

Fourteen existing fixture modules now opt into tests/goals_actor.py, which
adds an explicit test owner only to commit/link calls lacking one. The helper
has a bare path; the actor-contract tests use raw inproc calls and never this
adapter. Existing explicit actors and reads pass through unchanged. Each
adapted module declares the helper in COVERS. This preserves the purpose of
older writer/refusal fixtures rather than letting them pass on the new early
actor refusal. No new test module or durations entry was needed.

## Verification

All commands below run with PYTHONPATH, PERRY_PROJECT and PERRY_HOME unset.
The first is required because inherited PYTHONPATH=.: makes subprocesses
started in the global temporary directory scan that large directory during
imports; the separate TASK-264 environment receipt documents the diagnosis.

1. Main narrow run: `python3 tests/parallel test_actor_required
   test_goals_kr_writer test_goals_writer test_linkage_writer
   test_a_write_refuses_where_nothing_is_installed test_add_writes_the_edge
   test_empty_config_store test_kr_progress_provenance
   test_linkage_store_readers test_linkage_task_exists test_md_store
   test_okr_store_is_the_source test_one_line_break_rule
   test_same_action_linkage test_store_population_agrees
   test_track_register_source test_unlinked_declaration test_router_budget`:
   **18 modules, 600 tests, 18.4 seconds, exit 0**.
2. Surface/procedure follow-up: `python3 tests/parallel test_actor_required
   test_bin_argument_contract test_procedures_call_the_tool test_bin_surface`:
   **4 modules, 155 tests, 28.7 seconds, exit 0**.
3. The added contract cases cover five commit modes (create/amend/close/miss/
   migrate), four link modes (edge/alias/unlinked/project), and check/measure.
   Each rejects all five invalid actor shapes, with and without dry-run,
   while a whole-project byte snapshot stays identical. The same argv with
   an actor successfully writes and records it in the event and applicable
   linkage record. Both declared readers work without an actor.
4. The first new success test exposed an incomplete test fixture: close
   needs --discharged-by. The fixture was corrected; no product workaround
   was added. All quoted green runs include that correction.
5. Three mutations, each on a fresh scratch archive with this round's files,
   were red on named tests:
   - skip the actor refusal for commit →
     TestGoalsActorContract.test_every_mode_refuses_absent_empty_blank_and_multiline_before_writing;
   - accept empty actors in the shared helper → the same named test;
   - require actor for list (and provide its refusal usage) →
     TestGoalsActorContract.test_every_reader_stays_actor_free.
   No green mutation. Scratch logs are under the worktree-derived
   perry-scratch/Perry-task-289-round2-codex/actor-round2-2ciefn9a directory.
6. `git diff --check` passes. The final code removes only redundant fixture
   wrappers, moves unittest.main after the new test class, and adds COVERS
   after the first narrow run; actor/surface tests passed after those code
   cleanups. Parent owns full+slow validation on the final combined merge.
   No repository-wide completion claim is made here.

## Architecture and boundaries

Touches bin/ARCHITECTURE §5 argument surface. NN-B2 remains enforced before
the actor check, NN-4 validates only typed strings, and NN-5 keeps all fixture
writes outside the checkout. The shared helper avoids a second validator.
No architecture rule, schema field, store shape, task-state record, journal
ownership or derived-event failure policy changed. KR add/restate/withdraw
remain outside scope. No push or merge to main was performed.
