# TASK-289 — round 1 result

2026-09-16 · Coding Agent (Codex takeover) · round 1 only.

## RESULT

```text
=== RESULT ===
Branch: codex/task-289-round1
Base: 00205059a087be4451a1158feb833c4b32e41a7f (main incorporated into the isolated branch)
Takeover base: c84e8775 (all prior TASK-289 implementation preserved)
Head: 6d9498fea090be479447c86d43ddbb2301dd381e (implementation; this result is the next evidence-only commit)
PR URL: n/a — no push or PR authorized
Files changed: 63 (against Base, including this result)
Tests: 284/284 final targeted checks across 8 modules; broad validation incomplete
Cycle time: 18 minutes
Notes: Existing implementation retained; sibling test branches had no additional
committed test fixes. Full and slow merged-preview gates belong to the parent.
=== END RESULT ===
```

## Behavior and scope

- All 27 `perry-task` writers are identified from `SURFACE.writes`. Missing,
  empty and whitespace-only actors exit 2 before schema/install/lock/write
  work, including dry runs. Usage renders the required flag without brackets.
- All four readers (`list`, `events`, `asks`, `signoff-offer`) still work
  without an actor. A representative write persists its supplied actor in
  the event and linkage record. Nonblank actor strings retain their exact
  identity, including surrounding whitespace; blank-only values are refused.
- Removed the parser's `"agent"` default and the linkage writer's fallback.
  No historical events were rewritten. The unchanged history reader at
  `bin/perry-task:8485` still uses `e.get("actor", "")` for a missing field;
  there is no retained `"agent"` fallback in this tool's executable code.
- All 51 writing examples found in the shipped scope carry `--actor`.
  `SKILL.md` is unchanged: net byte delta **0** against Base. Router and lane
  budgets passed `test_router_budget`.
- Existing test fixtures explicitly supply a named actor using
  `tests/task_actor.py`, or directly in subprocess/in-process argv. The
  helper leaves supplied actor arguments (including empty values), readers
  and unrelated tools intact. Missing-actor and reader contract tests use
  raw `inproc.run`; the runner itself has no actor injection.
- No edits to `bin/perry-goals`, `schema/state-schema.json`, other production
  tools, canonical task state, asks, or journal. The main merge brought in
  upstream state as history; this implementation authored no state changes.
  No push and no merge into main.

## Verification receipts

All commands below ran with `PERRY_PROJECT` and `PERRY_HOME` unset.

| Command | Outcome |
|---|---|
| `env -u PERRY_PROJECT -u PERRY_HOME python3 tests/parallel -j 1 --times test_actor_required` | 13/13, 30.23 module-seconds; code at `aeb8cf5f`; duration source records this exact ref and concurrent machine load |
| `env -u PERRY_PROJECT -u PERRY_HOME python3 tests/parallel test_durations_provenance test_router_budget test_a_write_refuses_where_nothing_is_installed` | 43/43, 19.2s |
| `env -u PERRY_PROJECT -u PERRY_HOME python3 tests/parallel test_bin_surface test_store_is_the_write_target test_task_writer_contracts test_task_writer_core` | 228/228, 29.9s; final caller/expectation fixes |
| `env -u PERRY_PROJECT -u PERRY_HOME python3 tests/parallel test_add_writes_the_edge test_add_declares_unlinked test_actor_required` | Earlier 66/66, 11.0s (actor module then had 12 tests; its added identity-preservation case is included in the final 13 above) |
| `git diff --check` | clean |

### Affected tier — exploratory, not a passing gate

`env -u PERRY_PROJECT -u PERRY_HOME bash tests/run --tier affected --base 00205059`
selected **153 of 153** modules because `bin/lib/` requires the full selection;
its selection estimate was **1012.0 of 1012.0 module-seconds**. The runner held
back the three slow-tier harness modules and attempted 150 modules.

The exploratory receipt reports 4150 tests and 30 failed assertions across four
modules: 27 usage subtests assumed every flag was bracketed, one recovery probe
called `main` directly without an actor, one concurrency probe built its own
`Popen` argv, and one document assertion expected `add --title` without the new
intervening actor. All were fixed and the four modules' 228 tests passed above.

Four unrelated configuration modules were deliberately stopped after the run
had taken 555.2s, to avoid duplicating the parent's active full suite:
`test_empty_config_store`, `test_state_root_unset`,
`test_tracks_source_documented`, and `test_empty_declared_store`. Their exit
-15 results are incomplete, not product failures or passes. The completed
module count is therefore 146, with four incomplete modules.

The tree guard also refused this exploratory run because the coding agent
edited `bin/perry-task`, `tests/durations.json`,
`tests/test_a_write_refuses_where_nothing_is_installed.py`, and
`tests/test_actor_required.py` while it was running. Those are known agent
edits, not evidence of a test writing project state. This receipt is **not** a
clean-tree or repository-wide pass. An earlier superseded exploratory run was
stopped during caller migration and supplies no validation claim.

Per the parent's explicit instruction, no second full-sized affected run was
launched solely for the caller fixes. The parent must run the immutable merged
preview with the committed result present:

```bash
env -u PERRY_PROJECT -u PERRY_HOME bash tests/run
env -u PERRY_PROJECT -u PERRY_HOME bash tests/run --tier slow
```

These two final gates are **not run by this coding agent**, and remain pending
parent verification. No repository-wide completion or V4/V5 award is claimed.

Local raw receipts: `/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry-task-289-codex/actor-round1` (`actor-final.log`,
`final-targeted.log`, `fixed-callers.log`, `targeted2.log`, `affected2.log`,
`bounded-processes.json`, and mutation logs).

## Mutation outcomes

Each mutation used a fresh scratch copy, never this worktree. Each exited 1
with an assertion failure on the named test; the copy was then removed and its
log retained. The helper/individual assertion bodies below were unchanged by
the subsequent caller-only fixes.

| Mutation | Named red test | Observed failure |
|---|---|---|
| Exempt writer `start` from `required_flags` | `TestEveryWriterRefusesWithoutAnOwner.test_each_writer_refuses_absent_empty_and_blank` | `start` absent/empty/blank/dry-run subtests |
| Change the acceptance check to `actor is not None` | `TestEveryWriterRefusesWithoutAnOwner.test_each_writer_refuses_absent_empty_and_blank` | Empty/blank actor cases, including `add` |
| Make reader `list` require the flag | `TestNoReadDemandsIt.test_every_read_runs_without_the_flag` | `list` exits 2 |
| Remove ` --actor <actor>` from `work/SKILL.md` | `TestEveryDocumentExampleCarriesTheActor.test_no_writing_invocation_lacks_the_actor` | The writing example is named as missing the flag |

Commands on each copy were `PYTHONPATH=tests python3 -m unittest
 test_actor_required.<class>.<method>` with the two Perry variables unset.
`mutations.json` and the four named logs under the receipt directory retain
exit codes and exact test identities.

## ARCHITECTURE COMPLIANCE

Touched sections:

- `bin/ARCHITECTURE.md` §5 and project `ARCHITECTURE.md` §5: the existing
  argument surface now requires the caller's actor on writes, per USER-950;
  exit 2 remains the bad-invocation contract. No payload contract version or
  schema changes.
- `bin/ARCHITECTURE.md` §4: validation occurs before root resolution, lock and
  write dispatch. Existing write transactions and history readers remain.
- Project §3 and §6 NN-1/NN-4/NN-5, module §6 NN-B1/NN-B2: shared helper reads
  declarations only; it adds no state parser or prose interpretation. Help
  still exits before actor validation. Tests write temporary projects; the
  actor absence probes retain the raw runner boundary.

Reasons: caller attribution is a mechanical argument constraint. Fixtures and
shipped instructions must obey that contract; the document scanner examines
command syntax rather than semantic meaning. Architecture files themselves
were not edited because this round's authorized file list excludes them.

New questions: none. The already-scoped `perry-goals commit/link` work remains
round 2, after TASK-264 integration. Scope deviations: none in implementation;
full/slow validation is explicitly handed to the parent as described above.

## Files changed

- `bin/lib/__init__.py`
- `bin/perry-task`
- `goals/SKILL.md`
- `goals/reference/linkage.md`
- `reference/okr-linkage.md`
- `reference/version-compatibility.md`
- `tests/durations.json`
- `tests/held_board.py`
- `tests/task_actor.py`
- `tests/task_writer_support.py`
- `tests/test_a_write_refuses_where_nothing_is_installed.py`
- `tests/test_actor_required.py`
- `tests/test_add_declares_unlinked.py`
- `tests/test_add_writes_the_edge.py`
- `tests/test_asks_list.py`
- `tests/test_asks_store.py`
- `tests/test_bin_argument_contract.py`
- `tests/test_bin_surface.py`
- `tests/test_board_less_reads_and_writes.py`
- `tests/test_cadence.py`
- `tests/test_cadence_store.py`
- `tests/test_decoration_changes_nothing.py`
- `tests/test_design_handoff.py`
- `tests/test_duplicate_ids_are_refused.py`
- `tests/test_empty_config_store.py`
- `tests/test_id_families.py`
- `tests/test_installed_is_one_predicate.py`
- `tests/test_intake_store.py`
- `tests/test_knowledge_promotion.py`
- `tests/test_linkage_store_readers.py`
- `tests/test_md_store.py`
- `tests/test_one_heading_predicate.py`
- `tests/test_one_line_break_rule.py`
- `tests/test_perry_task_writes_are_what_it_writes.py`
- `tests/test_prioritize.py`
- `tests/test_queue_sla.py`
- `tests/test_register_store_invariant.py`
- `tests/test_register_substitution.py`
- `tests/test_retired_tolerance.py`
- `tests/test_role_on_rows.py`
- `tests/test_row_integrity.py`
- `tests/test_same_action_linkage.py`
- `tests/test_semantics_on_every_payload.py`
- `tests/test_state_root_unset.py`
- `tests/test_store_is_the_write_target.py`
- `tests/test_summary_is_asked_for.py`
- `tests/test_task_store_read_cutover.py`
- `tests/test_task_summary.py`
- `tests/test_task_writer_contracts.py`
- `tests/test_task_writer_core.py`
- `tests/test_track_move.py`
- `tests/test_track_register_source.py`
- `tests/test_v5_signoff.py`
- `tests/test_wip_and_stages.py`
- `tests/test_work_modes.py`
- `work/SKILL.md`
- `work/reference/autopilot.md`
- `work/reference/delegate.md`
- `work/reference/dispatch.md`
- `work/reference/promotion.md`
- `work/reference/review.md`
- `work/reference/subcommands.md`
- `perry/evidence/2026-09/TASK-289-result.md`
