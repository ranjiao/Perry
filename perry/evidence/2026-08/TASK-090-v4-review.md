# TASK-090 V4 review — task reads come from the store

> Reviewed: 2026-08-19
> Rung: V4
> Acceptance criteria: `perry/evidence/2026-08/TASK-090-spec.md`
> Review constraints: `work/reference/review-constraints.md`
> Result: PASS after bounded fixes

## Scope

This was a fresh-context review of the uncommitted TASK-090 changes to
`bin/perry-task`, the shared store validator, the task-list contract and shape
fixture, and the TASK-090-related tests. The claim under review was that current
Task truth and writer baselines come only from validated `tasks.jsonl`, while
`BOARD.md` remains a projection/layout and non-Task register source and the
event log remains disposable history.

The review did not modify the implementation or Perry state. Destructive and
mutation-sensitive checks ran only on disposable copies under `/tmp`.

## Review progression

### 1. Initial structural FAIL — `status_text`

The first implementation still declared `perry-task/list/1.9`, whose contract
defined `status_text` as the Board `Status` cell verbatim, but the new reader
emitted normalized store `status` for both `status` and `status_text`. Comparing
the HEAD reader and the cutover reader on the same disposable Perry project
showed that the only task-field difference was `status_text`, across every
closed task and any decorated open status.

That was a real contract contradiction at the time: typed store truth could not
also preserve raw Board text without making the projection a second source.

### 2. User authority — typed status wins

The user resolved the conflict explicitly:

- `status` is the sole typed current-status truth.
- `status_text` remains present as a legacy string alias of `status`.
- Raw, emphasized or off-enum Board text is not current Task truth.
- The public contract moves to `perry-task/list/1.10`, with the semantic change
  announced and no key removal or type change.

The implementation, contract document, contract-shape fixture and invariance
tests were updated accordingly. A Board-only status edit now changes neither
`status` nor `status_text`, and the payload advertises the change in
`semantics`.

### 3. Store-validation FAIL — `depends_on` elements

The shared validator initially checked only that `depends_on` was a list, not
that every element was a string. A disposable-copy type matrix covered `null`,
boolean, integer, float, list and object elements:

- scalar elements were accepted into the public payload;
- nested list/object elements produced a raw `TypeError` during graph lookup;
- an unrelated `ask` write could update the store, Board, journal and event log
  while the malformed dependency remained in canonical state.

The bounded fix changed shared validation to require `list[str] | null` and
added both read refusal and unrelated-write no-side-effect regressions. The
same matrix then returned structured JSON refusals for every non-string element,
with no traceback and no write.

### 4. Bounded contract FAIL — group priority and semantic announcements

Two contract issues remained after the typed-status and validation fixes:

1. `conformance.sections_read` copied a task's priority for every stored group.
   Perry therefore emitted `priority: "P0"` for the noncanonical group
   `P0 (must finish this period)`, while contract 1.10 required `null` unless
   the group was exactly `P0`, `P1` or `P2`.
2. The cutover changed the meanings of `conformance.sections_read`,
   `conformance.sections_skipped` and
   `conformance.rows_with_unrecognized_id`, but the 1.10 `semantics` entry named
   only `status_text`. A disposable 1.9/1.10 comparison demonstrated the
   changed group counts and the legacy-empty behavior for skipped tables and
   unrecognized projection rows.

The bounded fixes now derive a non-null section priority only for exact
`P0`/`P1`/`P2` groups and list all four changed fields in the 1.10 semantics
entry, with the store-group and legacy-empty meanings stated. Focused tests pin
both behaviors.

## Mutation-sensitive checks

Two central cutovers were mutated in a disposable checkout, with `__pycache__`
cleared and more than one second allowed before execution:

- Replacing the store-backed `cmd_list` with the old Board reader made the
  focused suite fail on a missing Board and on a Board-only title overriding a
  store-only title.
- Returning raw Board values from `task_projection_row` before store hydration
  made the writer-baseline regression fail: an empty store `next_action` was
  incorrectly treated as the Board literal and the write was refused as a
  no-op.

Both mutations went red, so the focused checks exercise the claimed read and
writer-baseline cutovers rather than merely their happy paths.

## Gates and results

- Focused store/task/contract/migration gate before the final bounded fixes:
  417 tests green.
- Final bounded re-review gate:
  `test_task_store_read_cutover`, `test_contract_invariance` and
  `test_task_writer` — 284 tests green.
- The stale `test_role_on_rows` 1.9 version pin was updated to 1.10; its focused
  rerun passed.
- Full parallel suite: 56 modules, 1603 tests. Its only remaining failure was
  the known repository-wide `SKILL.md` byte-budget overrun
  (`21036 > 20480`, over by 556 bytes). The same failure reproduced from HEAD,
  so it is not introduced by TASK-090.
- `bash tests/run` reached the same sole pre-existing byte-budget failure; its
  schema, syntax and sample-project stages otherwise completed.
- `python3 bin/perry-lint`: clean, 100 store records and zero drifted rows.
- `git diff --check`: clean.

## Not checked

- Windows path and filesystem behavior.
- Permission-denied and read-only filesystem cases beyond the existing suite.
- Real process-crash timing during the store/journal transaction.
- Live migration against gimegime-pmo or PolyForge; migration coverage was via
  repository fixtures and tests only.

=== VERDICT ===
task: TASK-090
rung: V4
result: PASS
criteria: perry/evidence/2026-08/TASK-090-spec.md
checked: criteria 1-8 on disposable copies; Board deletion; store-only and Board-only edits; event-log deletion; malformed JSON and wrong-typed dependency matrices; unrelated-write side effects; list and writer Board-read mutations; 1.9-to-1.10 payload comparison; typed status alias; exact-group priority; complete 1.10 semantics announcement; focused 417-test and final 284-test gates; full parallel and bash tests/run gates; perry-lint; git diff --check
not-checked: Windows paths; permission-denied/read-only filesystems; process-crash timing during writes; live migration against gimegime-pmo or PolyForge
proof: none
=== END VERDICT ===
