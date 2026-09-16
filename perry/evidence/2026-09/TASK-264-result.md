# TASK-264 — result

> Row: DESIGN-022 B — goals writes KR records, their checks and their measurements
> Branch `coding/task-264-kr-writer` · base `9156ea1c` (main's tip at dispatch)
> Written 2026-09-16 by the Coding Agent.
> **Landed:** `perry-goals measure` (deliverable 1) and `perry-goals check` (deliverable 2), both requiring `--actor` (USER-950, added mid-row by the coordinator).
> **Blocked:** deliverable 3, KR `add` / `restate` / `withdraw` at both levels — the append-only stores have no representation for a restated or withdrawn KR (§ 3 below). Nothing of it was built.

## Round 2 — Codex takeover, 2026-09-16

**Partial delivery only: check and measure are implemented; KR add/restate/
withdraw remain blocked. This result does not claim full-task V4 or closure.**

- Branch: `codex/task-264-round2`; original implementation pinned at `4ea3178a`.
- Integration baseline: `d270935d` (includes the PMO clarification of Every
  write); merged into this branch before the fixes. Implementation head is
  the commit carrying this section (`git log -1 --format=%H -- bin/perry-goals`).
- Scope: `bin/perry-goals`, writer regression tests, durations conflict
  resolution, this result. No task-state writes, schema edits, journal writes,
  live checks or live measurements were performed by this coding session.

**Authority bug fixed.** `refuse_closed_kr` now reuses
`overall_kr_model(..., "current")`, the same validated canonical store model
`krs --level overall` uses. An `OKR.md` whose last heading is v3 can no longer
reopen v3 when the store is at v4. Lagging, ahead and absent markdown all leave
v4 writable. Regression tests assert refusal code, recovery wording and
unchanged store/event bytes for the rejected stale version.

**Event failures follow the clarified spec and ARCHITECTURE §4.** A committed
record plus a failed derived event still returns exit 0 with `written: true`,
`event_written: false`, and stderr explaining the failure. It is not an atomic
record/event transaction, does not claim rollback, and must not be reported as
“nothing written.” A directory at `.perry/events.jsonl` exercises the real
append failure for both verbs and both human/JSON output; each call appends
exactly one canonical record, warns, and creates no journal. The warning now
names `event.file` (`linkage.jsonl` here), rather than falsely saying `OKR.md`
was written. No automatic retry is promised or performed.

**Independent D3 confirmation.** Fresh scratch projects show that appending a
second phase KR with the same id produces two displayed KRs, even with an
undeclared `status: withdrawn`; the parser appends all `kind: kr` records.
The overall store refuses duplicate `version/objective/id` keys. Its
`record_key` / `validate_records` contain no same-version supersession rule.
Neither store declares a withdrawal representation. Options for a separately
approved design are typed append-only supersession/tombstone semantics in both
stores and readers, or explicitly relaxing the task's append-only requirement
and defining rewrite/history behavior. A new overall OKR version can represent
new wording today, but is not a same-version KR withdrawal command. No option
was implemented, and add remains outside this round's scope.

**Validation before this commit:**

- Writer module: 45 tests passed (including projection drift and real event
  failures). The only subsequent test change makes the missing-event mutation
  fail by an explicit event-count assertion rather than an unpacking error.
- Writer + durations provenance: 68 tests passed before the event-failure test
  was added; 153 modules recorded / 153 on disk, no stale or unstamped sources.
- Durations conflict: preserved all current-main entries/sources and the
  original branch-only `test_goals_kr_writer.py` 5.17 s / source
  `2026-09-16-task264`; historical timing provenance remains `ec5d5421` and is
  not relabeled as a fresh measurement. Current-main existing timings win.
- Fresh scratch end to end: check `decrease 1702 → 400`; measurements 1702,
  1051, 400 yielded `(state, met, fraction)` of `(measured, false, 0.0)`,
  `(measured, false, 0.5)`, `(measured, true, 1.0)`.
- Six fresh-copy mutations red: computed KR accepted →
  `test_a_computed_kr`; event omitted →
  `test_the_measure_event_is_appended_with_the_record`; invalid decrease →
  `test_decrease_with_target_not_below_baseline`; missing evidence accepted →
  `test_a_missing_evidence_path`; ambiguous version accepted →
  `test_a_bare_overall_id_two_versions_carry`; markdown authority restored →
  `test_a_lagging_projection_cannot_reopen_a_past_store_version`.
- `git diff --check` passed. Final affected-tier results are quoted in the
  hand-off on this committed tree; full and slow merged-tree validation belong
  to the coordinating session, not this partial result.

Architecture compliance: NN-1 reuses the existing model without a second
parser; NN-2 chooses the store over its projection; NN-3 distinguishes a
persisted record from a missing event; NN-4 compares typed values only; NN-5
all mutations and measurements use isolated scratch roots. Existing project
lock and lane ownership remain intact. No confirmed architecture rule changes.

The original implementation receipt follows for provenance; the updated
write-policy wording above supersedes any earlier atomicity implication.

## 1. What landed, and where

| File | Change |
|---|---|
| `bin/perry-goals` | `cmd_measure`, `cmd_check`, the shared KR resolver and refusals, the per-subcommand flag refusal for the new flags, the usage block |
| `tests/test_goals_kr_writer.py` | new, 42 tests, `COVERS` declared |
| `tests/durations.json` | the new module (5.17 s) and its `2026-09-16-task264` source |
| `tests/test_a_write_refuses_where_nothing_is_installed.py` | `measure` and `check` added to `GATED` — the test derives the write commands from `COMMANDS` and reddens until each is listed |
| `tests/test_okr_store_is_the_source.py` | the one new write call site added to the list of read-and-placed `write_atomic` sites |

The last two files are outside the spec's "Files in scope". Both are registries
whose job is to redden when a write path is added without being placed; each
gains one entry and nothing else.

`schema/state-schema.json`, `ARCHITECTURE.md`, `bin/perry-state § next_kr_progress`,
`reference/next-rules.json` and this repository's `perry/` stores are not
touched. Nothing here declares a check or measures a KR of phase 004.

## 2. Each command's surface

```
perry-goals measure <KR-ID> [--okr-version V] --check S --value N --evidence <path>
                    --actor <who> [--dry-run] [--json] [--root P]
perry-goals check   <KR-ID> [--okr-version V] --id S --direction D --target N
                    [--baseline N] --label "…" --actor <who> [--dry-run] [--json] [--root P]
```

**What each writes.** One record appended to `<state root>/linkage.jsonl`,
then one event appended to `.perry/events.jsonl`, under the project lock:

```json
{"kind": "check", "kr": "P004-O1-KR1", "okr_version": "", "id": "p90", "label": "p90 next-action length", "direction": "decrease", "target": 400, "baseline": 1702, "declared_at": "2026-09-16T09:04:43Z", "actor": "pmo"}
{"kind": "measurement", "kr": "P004-O1-KR1", "okr_version": "", "check": "p90", "value": 1702, "asserted_at": "2026-09-16T09:04:44Z", "evidence": "evidence/2026-09/m.md", "computed": false, "actor": "pmo"}
{"ts": "2026-09-16T17:04:44+08:00", "event": "measure", "actor": "pmo", "file": "linkage.jsonl", "kr": "P004-O1-KR1", "okr_version": "", "check": "p90", "value": 1702, "evidence": "evidence/2026-09/m.md"}
```

The fields are exactly the ones `§ stores.declared["linkage.jsonl"].records.check`
and `.measurement` declare. No field was needed that is not declared.

- **The KR key** is `(kr, okr_version)`, the key `lib.kr_checks` files records
  under. A phase KR is a `kind: "kr"` record of `linkage.jsonl` and carries
  `okr_version: ""`. An overall KR is a `kind: "kr"` record of `okr.jsonl`,
  read through `overall_kr_model` (the reader `krs --level overall` uses), and
  carries its record's `version` label, **matched exactly** (`v4: 2026-09-15`,
  not `v4`). Without `--okr-version`, an id must name exactly one KR.
  `--okr-version ""` names the phase KR explicitly.
- **Timestamps.** `declared_at` / `asserted_at` are the write's own moment,
  from `lib.register_stamp()` (UTC, with `Z`), the stamp `link` gives
  `declared_at`. The event's `ts` is `lib.event_stamp()`, as every event.
- **`computed`** is `false` on every record `measure` writes.
- **`--actor` is required** (USER-950). A missing value, an empty or
  whitespace-only one, or one with a line break is refused at exit 2 before
  any root, gate or lock. The message names the flag and the usage. The given
  value, stripped, is the `actor` on the record and on the event. `commit` and
  `link` keep their defaulted actor, per the coordinator (TASK-289 round 2).
- **`--evidence`** is checked for existence only (NN-4). A relative path is
  looked for under the state root, then the project root; it must be a file
  inside the project. It is stored relative to the state root
  (`evidence/2026-09/m.md`), which is how DESIGN-022 § 5.1's example writes it.
  An `evidence/` prefix is not enforced, because the spec says existence only.
- **`--value`, `--target`, `--baseline`** must be JSON numbers. An integer stays
  an integer, and `nan` and `inf` are refused.
- **`--dry-run`** writes nothing. It prints the record as a `+linkage.jsonl`
  diff line, and `--json` carries `record`, `event`, `written: false`.
- **Re-declaring** a check with the same `(kr, okr_version, id)` appends a
  second record, and `--json` names the declaration it supersedes. The reader
  (`lib.kr_checks`) decides which declaration is current; this writer does not
  restate that rule.
- **Flags.** `perry-goals` declares no `SURFACE`, so NN-B2 is held by hand for
  the new surface. `measure` and `check` refuse, at exit 2, any flag not in
  their `KR_WRITER_FLAGS` set. Every other subcommand refuses, at exit 2, the
  eight flags only these two take.
- **Exit codes** are `bin/ARCHITECTURE.md § 5`'s: 0 written or would write,
  1 refused and nothing written, 2 bad invocation (an undeclared flag, a
  missing or empty `--actor`).

**The journal is not written, and that is the lane's rule.** The brief glosses
NN-3 as the record first and then the journal line and event in the same
write. `journal/` belongs to `work`: `perry-goals § HANDOFF` and
`assert_owned` refuse a goals write to it, and neither `link`, `commit` nor
`perry-decide` writes one. These two follow the existing goals pattern:
- the record is written first, through the tool's gated `write_atomic`;
- the event is appended after it under the same lock;
- `event_written` in the payload says whether the event landed, and a failure
  is printed rather than reported as a full success (NN-3).

If the PMO wants a journal line for a measurement, that is a `work` hand-off or
a change to the hand-off contract. It is not this row's call.

## 3. Restate and withdraw in the append-only store — blocked

**Finding: neither store can represent a restated or withdrawn KR by
appending, so deliverable 3 needs a schema (and reader) change.** Probed on a
scratch project built by `tests/test_goals_kr_writer.py § make_project`:

| Probe | What happens |
|---|---|
| `linkage.jsonl`: append a second `kind: "kr"` record for `P004-O1-KR1` with a new title | `perry-goals krs --json` exit 0 prints **both**: `[('P004-O1-KR1', 'P004-O1-KR1 title'), ('O2-KR1', …), ('P004-O1-KR1', 'RESTATED title')]`. `perry-lint`: `8 record(s), 0 malformed`. There is no later-wins rule for `kr` (`parsers.linkage_from_store` appends every `kr` record to its objective) |
| `linkage.jsonl`: append a `kr` record carrying `status: "withdrawn"` | Not a declared field. The reader ignores it and prints the KR twice, and lint reports 0 malformed |
| `okr.jsonl`: append a second `kind: "kr"` record for `O4-KR1` in v4 | `perry-goals krs --level overall --json` **exit 1**, refusing: `… O4-KR1 — … is not unique`. `md_store.record_key` is `version/objective/id` and a duplicate is malformed, so the whole overall register stops printing |

What the stores do have, and why none of it fits:

- **`linkage.jsonl`.** Only `project` records supersede (a later record for the
  same Project id wins, `link --alias`). The store's one removal is the
  `unlinked` retraction, which is a rewrite. The `kr` record has no `status`,
  `withdrawn_at`, `supersedes` or `restated_from` field, and no ordering rule.
- **`okr.jsonl`.** A KR is restated by a **new OKR version** (`revise`, a new
  `## vN` block). Inside one version a record is changed only by rewriting it
  in place, and `write_okr_and_store` rewrites the whole store. That is not an
  append (§ 4), and nothing records a withdrawal.

**What it would take** (for the PMO to specify; none of it was done):
- a declared field or record kind on both `kr` shapes for a withdrawal, and a
  supersede rule for a restatement (e.g. a later `kr` record with the same key
  wins from a declared timestamp, as `check` does);
- that rule stated once and read by `parsers.linkage_from_store`,
  `perry_md_store`'s key uniqueness, `overall_kr_model` and `perry-lint`.

That is a `state-schema.json` change, which the spec forbids here.

**`add` alone was not built either, and this is a judgement for the PMO.**
- An appended phase `kr` record is representable today.
- An overall `add` goes through `write_okr_and_store`, a whole-store rewrite.
- The larger reason: an `add` with no `restate` and no `withdraw` makes a
  mistyped KR removable only by hand-editing the store. The original scope was
  opened to remove exactly that.
- The Bound's last element is the withdraw of an overall KR.
- If the PMO wants phase-KR `add` split off, it is small on top of
  `resolve_kr_for_writer` and `append_linkage_records`.

## 4. End to end (Verification § 3)

On a scratch project (`make_project`), through the real CLI as a subprocess,
`PERRY_PROJECT` and `PERRY_HOME` unset:

```
$ perry-goals check P004-O1-KR1 --id p90 --direction decrease --baseline 1702 --target 400 --label "p90 next-action length" --actor pmo
  perry-goals: wrote linkage.jsonl — check P004-O1-KR1 · p90
  exit 0
$ perry-goals krs --json   → P004-O1-KR1: state='unmeasured' met=null fraction=null value=null
$ perry-goals measure P004-O1-KR1 --check p90 --value 1702 --evidence evidence/2026-09/m.md --actor pmo
  perry-goals: wrote linkage.jsonl — measurement P004-O1-KR1 · p90 = 1702 (evidence evidence/2026-09/m.md)
  exit 0
$ perry-goals krs --json   → P004-O1-KR1: state='measured' met=false fraction=0.0 value=1702
$ perry-goals measure P004-O1-KR1 --check p90 --value 1051 --evidence evidence/2026-09/m.md --actor pmo
  exit 0
$ perry-goals krs --json   → P004-O1-KR1: state='measured' met=false fraction=0.5 value=1051
$ perry-goals measure P004-O1-KR1 --check p90 --value 400 --evidence evidence/2026-09/m.md --actor pmo
  exit 0
$ perry-goals krs --json   → P004-O1-KR1: state='measured' met=true fraction=1.0 value=400
```

`.perry/events.jsonl` then holds one `check` and three `measure` events, each
`actor: "pmo"`.
`perry-lint` on the same copy reports `linkage store: 11 record(s), 0 malformed`.
`TestEndToEnd.test_check_then_three_measurements` asserts the same sequence
in-process.

**One observation, not a defect.** The 1051 and 400 measurements landed in the
same second, so their `asserted_at` strings are equal. 400 is current because
`lib._latest_by` breaks a tie by file position (the later line wins), the rule
TASK-416 wrote. Two measurements in one second are therefore ordered by the
append, which is the order they were written.

## 5. Refusals (Verification § 4)

Every row below is a test. It asserts the exit code, that `linkage.jsonl` and
`.perry/events.jsonl` are byte-identical before and after, that the message
carries each fragment listed, and, for exit 1, `Nothing was written`.

| Command | Refused when | Exit | The message names | Test |
|---|---|---|---|---|
| measure | check not declared | 1 | `perry-goals check P004-O1-KR1 --id median …` | `TestMeasureRefuses.test_an_undeclared_check` |
| measure | KR in `COMPUTED_KR_METRICS` | 1 | `COMPUTED_KR_METRICS`, `never typed`, `perry-goals krs` | `test_a_computed_kr` |
| measure | evidence path missing | 1 | `does not exist under the project`, `write the evidence first` | `test_a_missing_evidence_path` |
| measure | evidence outside the project / a directory | 1 | `does not exist under the project` | `test_an_evidence_file_outside_the_project`, `test_a_directory_is_not_evidence` |
| measure | KR's phase scored | 1 | `which is scored`, `perry-goals krs` | `test_a_scored_phase` |
| measure | OKR version not current | 1 | `'v3: …' is not the current one`, the current label, `perry-goals krs --level overall` | `test_an_okr_version_that_is_not_current` |
| measure | bare overall id, two versions | 1 | `names 2 KRs`, `--okr-version "v3: …"`, `--okr-version "v4: …"` | `test_a_bare_overall_id_two_versions_carry` |
| measure | bare id, a phase KR and a version | 1 | `names 2 KRs`, `--okr-version ""`, `--okr-version "v4: …"` | `test_a_bare_id_a_phase_and_a_version_both_carry` |
| measure | id resolves to no KR | 1 | `resolves to no KR`, `perry-goals krs` | `test_an_id_that_resolves_to_no_kr` |
| measure | `--okr-version` not an exact label | 1 | `matched exactly`, the labels carrying the id | `test_a_version_label_that_is_not_exact` |
| measure | `--value` not a number (`many`, `nan`, `inf`, `""`) | 1 | `--value takes a number` | `test_a_value_that_is_not_a_number` |
| measure | a required flag missing | 1 | `--check is required`, the usage line | `test_a_missing_required_flag` |
| check | `increase`, target ≤ baseline | 1 | `--direction decrease` | `TestCheckRefuses.test_increase_with_target_not_above_baseline` |
| check | `decrease`, target ≥ baseline | 1 | `--direction increase` | `test_decrease_with_target_not_below_baseline` |
| check | `increase`/`decrease` with no baseline | 1 | `--baseline <N>` | `test_increase_or_decrease_without_a_baseline` |
| check | `done`, target ≠ 1 | 1 | `--target 1` | `test_done_with_a_target_other_than_one` |
| check | baseline on `at_least` / `at_most` / `done` | 1 | `Re-run without --baseline` | `test_a_baseline_on_a_limit_or_a_milestone` |
| check | direction outside the five | 1 | the five | `test_a_direction_outside_the_five` |
| check | id resolves to no KR | 1 | `perry-goals krs` | `test_an_id_that_resolves_to_no_kr` |
| check | bare overall id, two versions | 1 | `--okr-version "v4: …"` | `test_a_bare_overall_id_two_versions_carry` |
| check | `--id` not a slug | 1 | a slugged suggestion, `--id p90-length` | `test_an_id_that_is_not_a_slug` |
| check | `--target` not a number | 1 | `--target takes a number` | `test_a_target_that_is_not_a_number` |
| both | `--actor` missing | 2 | `requires --actor <who>`, `was not given`, the usage | `TestActorIsRequired.test_a_missing_actor_is_refused` (one subtest per verb) |
| both | `--actor ""` or `--actor "   "` | 2 | `requires --actor <who>`, `empty value` | `TestActorIsRequired.test_an_empty_actor_is_refused` (two subtests per verb) |
| both | a flag the subcommand does not take | 2 | the flags it does take | `TestTheSurface.test_a_flag_the_writer_does_not_take_is_exit_2` |
| others | `measure`/`check`-only flag on e.g. `krs` | 2 | which subcommands own it | `test_the_writers_flags_are_refused_elsewhere` |
| both | directory not an installed project | 1 | `not an installed Perry project` | `test_an_uninstalled_directory_is_refused` (and the two gate tables) |

Three messages as the CLI prints them, for the spec's `[user-verify]` item
(does each tell you what to run next?):

```
$ perry-goals measure P004-O1-KR1 --check median --value 3 --evidence evidence/2026-09/m.md --actor pmo
perry-goals: refused — no check 'median' is declared on P004-O1-KR1; declared: p90. A value is measured against a declared check: `perry-goals check P004-O1-KR1 --id median --direction <D> --target <N> [--baseline <N>] --label "…" --actor <who>` declares it. Nothing was written
exit 1
$ perry-goals check O1-KR1 --id p90 --direction decrease --baseline 1702 --target 1702 --label x --actor pmo
perry-goals: refused — O1-KR1 names 2 KRs: overall KR O1-KR1 in `--okr-version "v3: 2026-09-01"`; overall KR O1-KR1 in `--okr-version "v4: 2026-09-15"`. A number filed under the wrong one is read by no reader of the other, so it is not guessed. Re-run with `--okr-version` naming one of them. Nothing was written
exit 1
$ perry-goals measure P004-O1-KR1 --check p90 --value 3 --evidence evidence/2026-09/m.md
perry-goals: `measure` requires --actor <who>, and it was not given. Every write names who made it (USER-950). Usage: perry-goals measure <KR-ID> [--okr-version V] --check S --value N --evidence <path> --actor <who>. Nothing was written
exit 2
```

## 6. Mutations (Verification § 5)

Each mutation was applied to a fresh copy of the tree at `7ddbce6e` (the
worktree minus `.git`) under `$TMPDIR/perry-scratch/task-264/`. Each replaces
one exact substring of `bin/perry-goals`, asserted to occur once, and runs
`tests/test_goals_kr_writer.py` (42 tests) in that copy. The five the spec
names were first run at `3e5cc51e`, before USER-950, with the same reds on
39 tests. M6 was added for the actor rule.

| # | Mutation | Red |
|---|---|---|
| M1 | `measure` accepts a KR in `COMPUTED_KR_METRICS` (`if False and kr in …`) | `TestMeasureRefuses.test_a_computed_kr` |
| M2 | `measure` writes the record without the event (`event_written = True` for `measure`) | `TestMeasureWrites.test_the_measure_event_is_appended_with_the_record`, `TestActorIsRequired.test_the_given_actor_is_on_the_record_and_the_event` |
| M3 | `check` accepts `decrease` with `target >= baseline` | 2 subtests: `TestCheckRefuses.test_decrease_with_target_not_below_baseline` (target 1702 and 2000) |
| M4 | `measure` accepts a missing evidence path (`evidence = evidence_text`) | `test_a_missing_evidence_path`, `test_an_evidence_file_outside_the_project`, `test_a_directory_is_not_evidence`, `TestMeasureWrites.test_an_absolute_evidence_path_inside_the_project_is_stored_relative` |
| M5 | an overall KR resolves without `okr_version` when two versions carry the id (`if False and len(candidates) > 1`) | `TestCheckRefuses.test_a_bare_overall_id_two_versions_carry`, `TestMeasureRefuses.test_a_bare_overall_id_two_versions_carry`, `test_a_bare_id_a_phase_and_a_version_both_carry` |
| M6 | (USER-950) a missing or empty `--actor` is accepted (`if False:`) | 6 subtests: `TestActorIsRequired.test_a_missing_actor_is_refused` (×2), `test_an_empty_actor_is_refused` (×4) |

No mutation was green.

**Why M1 and M5 are real rather than incidental reds:**
- **M1.** The test declares the check first. Without the computed refusal, the
  call would write, and the test's byte comparison catches it.
- **M5.** On `measure`, the silently chosen version is v3, which the
  current-version refusal then catches at exit 1. The test also asserts the
  ambiguity message, which is what goes red. The `check` twin has no later
  refusal, so the mutation writes and the byte comparison goes red.

## 7. Tests

- **Round 1** (`ec5d5421`): `bash tests/run --tier affected --base 9156ea1c`
  selected 49 modules. Two were red, both registries asking for the new write
  path to be placed: `test_a_write_refuses_where_nothing_is_installed` and
  `test_okr_store_is_the_source`. Both were fixed in round 2.
- **Round 2** (`3e5cc51e`): the same command selected 52 of 150 modules and was
  green ("this is NOT a green suite"). `test_durations_provenance` and
  `test_parallel_runner` were held back for the slow tier.
- **Round 3** (USER-950, `--actor` required): quoted in the hand-off, with the
  final commit.
- **Final:** `bash tests/run` and `bash tests/run --tier slow` run on the commit
  that adds this file, with `PERRY_PROJECT` and `PERRY_HOME` unset. Both are
  quoted in the hand-off.

**Pre-existing, not this row.** `tests/test_empty_config_store.py` (TASK-270,
`7e099398`) is on disk at base `9156ea1c` with no `tests/durations.json` entry
(`git show 9156ea1c:tests/durations.json` has 0 occurrences).
`test_durations_provenance` run alone on this branch fails its two tests
naming only that module. Its entry is TASK-270's to add; round 3 of that row
is in flight, and adding it here would conflict with that branch.

## 8. For the PMO

1. **Deliverable 3 is blocked** on a schema and reader decision (§ 3).
   `TASK-231` "closes with" this row per the spec; its measuring half is
   delivered and its KR-record half is not.
2. **A stale sentence in the schema.**
   `schema/state-schema.json § … records.check.description` and
   `.measurement.description` still say "nothing writes one yet". This row may
   not edit the schema, so the sentence is left for a consented edit.
3. **Phase E is untouched.** No check is declared and no KR of phase 004 is
   measured. `perry-goals check` / `measure` against this repository's own
   `perry/` is the goals-lane action the user approves per Objective.
