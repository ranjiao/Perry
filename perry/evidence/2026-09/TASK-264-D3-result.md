# TASK-264 deliverable 3 — result: KR add, restate and withdraw at both levels

> Row: TASK-264, deliverable 3 (DESIGN-022 phase B2) · Spec: `TASK-264-D3-spec.md`
> Design: `DESIGN-022 § 5.7`, `ADR-022` · Authority: `USER-952`, `USER-965`
> Written 2026-09-18 by the Coding Agent, in an isolated worktree.
> Base `5e5407ea` (main's tip; the worktree started at `0b5bf99e` and was
> fast-forwarded first). Code head `12c941de`; this file is committed on top of it.
> Not merged, pushed, tagged or released. No record was written to this
> repository's own `perry/` stores; this file is the one `perry/` write.

## 1. What landed

| Piece | Where |
|---|---|
| **Schema.** `kr_revision` declared on `linkage.jsonl`, and on `okr.jsonl` in a new `stores.declared["okr.jsonl"]` entry that declares that one kind only. Each carries `identity_fields`. No existing entry changed | `schema/state-schema.json` |
| **The fold rule, once.** `kr_revisions` (the fold and its findings), `fold_kr_records` (the hook readers pass), `kr_status`, `kr_identity_fields`, `withdrawn_krs`; `objective_kr_summary` leaves a withdrawn KR out of every count | `bin/lib/__init__.py`, beside `kr_checks` |
| **Readers.** `parsers.load_linkage` and `load_snapshot` take an optional `kr_fold` callable (parsers still imports nothing from `bin/`); `perry-goals krs` (both levels), `overall_kr_model`, `perry-goals list`, `perry-state` (payload and `phase.kr_progress`), `perry-lint` all read folded and publish `status` / `revisions` | `viewer/parsers.py`, `bin/perry-goals`, `bin/perry-state`, `bin/perry-lint` |
| **`okr.jsonl` kind.** `kr_revision` in `STORED` (fields read from the schema), its `fields` typed as an object, a whole-record key, and `store_only_kinds=("kr", "kr_revision")` so `write_okr_and_store` keeps it through every `commit` | `bin/perry_md_store.py` |
| **The verbs.** `perry-goals kr add|restate|withdraw`, `--actor` required, `--dry-run`, one `kr_add` / `kr_restate` / `kr_withdraw` event; `check` and `measure` refuse a withdrawn KR | `bin/perry-goals` |
| **Contract.** `perry-goals/list/3.6`: `status`, `withdrawn_at`, `withdrawn_reason`, `revisions[]`, and a `semantics` entry because restated values now fold | `schema/goals-list-contract.md`, `LIST_SEMANTICS` |
| **Docs.** `phases.md § kr`, the plan-phase finalize sentence, `score-phase` step 1, `pivots.md` step 3, the `goals/SKILL.md` index row (net −35 bytes), `reference/next.md` | `goals/`, `reference/next.md` |

**Net lines** (`git diff --numstat 5e5407ea..12c941de`):

- **Production Python** +1,050 / −30, **net +1,020**: `bin/perry-goals` +691/−19,
  `bin/lib/__init__.py` +232/−1, `bin/perry_md_store.py` +42/−1,
  `bin/perry-state` +36/−4, `bin/perry-lint` +31/−1, `viewer/parsers.py` +18/−4.
- **Tests (Python)** +791 / −12, **net +779**. The new module
  `tests/test_goals_kr_revisions.py` is 731 of them (49 tests). The other 60
  are one-line registries and version pins in nine modules.
- **Fixtures** +39/−5: `durations.json`, `shipped-semantics.json` and
  `contract-key-parity.json`.
- **Schema and docs** +186/−7.

## 2. `OKR.md` and the render gate: established first

Spec item 4 said to check the current write path before rendering. It is:

- Since TASK-236 (ADR-019), `OKR.md` carries **no KR row**. `kr` is a
  `store_only_kinds` kind: `okr.jsonl` holds it, no byte of `OKR.md` renders it,
  and `perry-goals krs --level overall` is the surface the KR tables became.
- `write_okr_and_store` derives the store's projected kinds from `OKR.md`
  (objective headings, `## Commitments`, the version table) and keeps every
  other stored record, `kr` included.
- The gate is `render(OKR.md, final store) == OKR.md`, byte for byte. Its
  docstring predates TASK-236 and says the KR rows are in the file.

So **an appended `kr_revision` passes the gate without weakening it.** It is a
store-only kind like `kr`. Every overall `kr` write leaves `OKR.md` exactly as
it was, and runs the same `md_store.render` comparison on the store it would
leave (`append_okr_record`). The gate function itself is unchanged.

**Deviation from § 5.7 / spec item 4, and why.** The spec asks for the folded
KR and the `withdrawn <date>: <reason>` marker to be rendered in `OKR.md`.
There is no KR row in `OKR.md` to render them in. They are rendered on the
surface that replaced those rows: `krs --level overall`, and the phase
`krs` too.

- Putting KR rows back into `OKR.md` would reverse TASK-236.
- Writing folded words into rows the store derives from would rewrite the KR
  record.

Both are outside this row.

**The one case that could not pass the gate honestly is refused, not
weakened.** An `OKR.md` that still carries KR table rows (a pre-TASK-236
layout) renders them from the unfolded record. After a restate it would keep
showing the old words, and folding the words into the file would rewrite the
canonical record. Every overall `kr` write refuses there, names TASK-236 and
`perry-okr diff`, and writes nothing
(`test_an_okr_md_that_still_carries_kr_rows_is_refused`, mutation M7b).

A store the file already disagrees with is also refused
(`test_a_store_the_file_already_disagrees_with_is_refused`, M7c). This is
stricter than `commit`, which reports that drift and takes the file's value.
An append that does not touch the file has no file value to take.

**The PMO decides.** Either the render on `krs` satisfies § 5.7's `OKR.md`
clause, or `DESIGN-022 § 9` needs an entry saying so. Nothing in `perry/` was
edited.

## 3. End to end, through the real CLI

The run used a fresh copy of `tests/test_goals_kr_writer.py § make_project`.
It called `python3 bin/perry-goals … --root <copy>` with `PERRY_PROJECT` and
`PERRY_HOME` unset. The script is `$TMPDIR/perry-scratch/<worktree>/e2e.sh`.
The quotes below are from its log, trimmed to the keys the spec names.

### Phase KR

```
$ perry-goals kr add P004-O1-KR2 --objective O1 --text "p90 next-action length" --set target=400 --reason "phase 004 needs it" --actor pmo
perry-goals: wrote linkage.jsonl — kr add P004-O1-KR2
  +linkage.jsonl  {"kind": "kr", "phase": "004-now", "objective": "O1", "id": "P004-O1-KR2", "title": "p90 next-action length", "target": 400}
  exit 0
$ perry-goals check P004-O1-KR2 --id p90 --direction decrease --baseline 1702 --target 400 --label "p90 length" --actor pmo      → exit 0
$ perry-goals measure P004-O1-KR2 --check p90 --value 1051 --evidence evidence/2026-09/m.md --actor pmo                         → exit 0
  krs --json → {"state": "measured", "met": false, "target": 400.0, "status": "active", "revisions": []}
$ perry-goals kr restate P004-O1-KR2 --set target=300 --reason "tightened after review" --actor pmo
perry-goals: wrote linkage.jsonl — kr restate P004-O1-KR2 · target: 400 → 300
  exit 0
  krs --json → {"target": 300.0, "state": "measured", "status": "active", "revisions": [{"op": "restate", "revised_at": "2026-09-18T13:29:47+08:00", "reason": "tightened after review", "actor": "pmo", "changes": [{"field": "target", "before": 400, "after": 300}]}]}
$ perry-goals kr withdraw P004-O1-KR2 --reason "mistyped: duplicates P004-O1-KR1" --actor pmo
perry-goals: wrote linkage.jsonl — kr withdraw P004-O1-KR2
  exit 0
  krs --json → {"status": "withdrawn", "withdrawn_at": "2026-09-18T13:29:47+08:00", "withdrawn_reason": "mistyped: duplicates P004-O1-KR1", "revisions": [<restate>, {"op": "withdraw", …}]}
  phase.kr_progress → {'commit_total': 2, 'measured': 0, 'met': 0, 'unmeasured': 2} · withdrawn: 1 [{'id': 'P004-O1-KR2', 'withdrawn_at': '2026-09-18T13:29:47+08:00', 'reason': 'mistyped: duplicates P004-O1-KR1'}]
$ perry-goals measure P004-O1-KR2 --check p90 --value 400 --evidence evidence/2026-09/m.md --actor pmo
perry-goals: refused — P004-O1-KR2 was withdrawn at 2026-09-18T13:29:47+08:00 (mistyped: duplicates P004-O1-KR1), and withdrawal is terminal: a withdrawn KR takes no `measure` (DESIGN-022 § 5.7). Its records stay in the store. To track the goal again, add it under a new id — `perry-goals kr add <NEW-KR-ID> --objective <O> --text "…" --reason "…" --actor <who> --root …/e2e`. Nothing was written
  exit 1
$ perry-goals krs
| P004-O1-KR2 | p90 next-action length — withdrawn 2026-09-18: mistyped: duplicates P004-O1-KR1 | 300 | — |
```

Before the withdrawal, the phase had three commit KRs (`P004-O1-KR1`,
`O2-KR1`, `P004-O1-KR2`). After it, `commit_total` is 2 and the withdrawn KR
is reported beside the count.

`phase.kr_progress` is computed by `perry-state § next_kr_progress` over the
real `perry-state --json` payload. The new fact
`phase.kr_progress.withdrawn` is `1`. The restate and the withdrawal landed in
the same second; the fold applied them in file order, the tie-break § 5.7 states.

### Overall KR, with `OKR.md` at each step

```
  OKR.md sha256 20e135718742cbdc · diff: none (0 lines)                 ← before
$ perry-goals kr add O4-KR2 --okr-version "v4: 2026-09-15" --objective O-14 --text "Perry is used on SkyTonight weekly" --set "metric=≥ 4 weeks" --reason "v4 gap" --actor pmo
perry-goals: wrote okr.jsonl — kr add O4-KR2 (v4: 2026-09-15)
  +okr.jsonl  {"kind": "kr", "version": "v4: 2026-09-15", "objective": "Objective 4 — Objective 4", "objective_id": "O-14", "id": "O4-KR2", "text": "Perry is used on SkyTonight weekly", "metric": "≥ 4 weeks", "stretch": "", "deadline": "", "linked": "", "qualifier": "", "form": "table", "order": 3}
  OKR.md sha256 20e135718742cbdc · diff: none (0 lines)
$ perry-goals check O4-KR2 --id weeks --direction at_least --target 4 --label "weeks used" --actor pmo         → exit 0
$ perry-goals measure O4-KR2 --check weeks --value 2 --evidence evidence/2026-09/m.md --actor pmo              → exit 0
  OKR.md sha256 20e135718742cbdc · diff: none (0 lines)
$ perry-goals kr restate O4-KR2 --set "text=Perry is used on SkyTonight every week" --reason "clearer" --actor pmo
perry-goals: wrote okr.jsonl — kr restate O4-KR2 (v4: 2026-09-15) · text: "Perry is used on SkyTonight weekly" → "Perry is used on SkyTonight every week"
  OKR.md sha256 20e135718742cbdc · diff: none (0 lines)
  krs --json → {"text": "Perry is used on SkyTonight every week", "status": "active", "revisions": [{"op": "restate", …, "changes": [{"field": "text", "before": "Perry is used on SkyTonight weekly", "after": "Perry is used on SkyTonight every week"}]}]}
$ perry-goals kr withdraw O4-KR2 --reason "folded into O4-KR1" --actor pmo
perry-goals: wrote okr.jsonl — kr withdraw O4-KR2 (v4: 2026-09-15)
  OKR.md sha256 20e135718742cbdc · diff: none (0 lines)
  krs --json → {"status": "withdrawn", "withdrawn_at": "2026-09-18T13:29:48+08:00", "withdrawn_reason": "folded into O4-KR1", …}
$ perry-goals measure O4-KR2 --check weeks --value 4 --evidence evidence/2026-09/m.md --actor pmo
perry-goals: refused — O4-KR2 (v4: 2026-09-15) was withdrawn at 2026-09-18T13:29:48+08:00 (folded into O4-KR1), and withdrawal is terminal: … `perry-goals kr add <NEW-KR-ID> --okr-version "v4: 2026-09-15" --objective <O> --text "…" --reason "…" --actor <who> --root …/e2e`. Nothing was written
  exit 1
$ perry-goals krs --level overall
| O4-KR2 | Perry is used on SkyTonight every week — withdrawn 2026-09-18: folded into O4-KR1 | ≥ 4 weeks | — | — |
```

`okr.jsonl` gained exactly three lines: one `kr` and two `kr_revision`. Every
prior byte is unchanged. `.perry/events.jsonl` holds, in order:

- `kr_add`, `check`, `measure`, `kr_restate` (with `changes`), `kr_withdraw`
  for the phase KR;
- the same five for the overall KR.

`perry-lint` on the copy reports `linkage store: 14 record(s), 0 malformed`
and no `kr-revision-malformed`. `OKR store: … 3 row(s) drifted` is the
fixture's own three objective records that have no heading in its `OKR.md`.
It was there before the first write.

`TestPhaseEndToEnd` and `TestOverallEndToEnd` assert these sequences
in-process. The overall one also asserts the byte gate after each step.

## 4. Refusals

Every refusal is a test in `TestRefusals`. It asserts:

- the exit code;
- byte snapshots of `linkage.jsonl`, `okr.jsonl`, `OKR.md` and
  `.perry/events.jsonl`, unchanged;
- each named recovery fragment.

| Verb | Refused when | The message names |
|---|---|---|
| add | id exists (active) | `perry-goals kr restate <id> … --root` |
| add | id exists and is withdrawn (phase and overall) | `never reused`, `perry-goals krs` |
| add | the Objective already has 4 active KRs (a withdrawn KR frees its slot; positive case asserted) | `perry-goals kr withdraw` |
| add | level unsaid (an id legal at both levels, no `--okr-version`) | `--okr-version ""` |
| add | current phase scored / OKR version not current | `history is not revised`, `perry-goals krs` / the current label |
| add | objective not in the phase; id names another phase; `--set` an identity field; no `--reason` | the objectives, `P004-…`, `identity field`, `--reason` |
| restate | identity field (`id`, `objective`, `phase`; `version`, `objective_id`, `order`) | `perry-goals kr withdraw` |
| restate | names no field / changes nothing / unknown or mistyped field | `--set`, `perry-goals krs`, the settable fields |
| restate | withdrawn KR | `terminal`, `perry-goals kr add` |
| restate | scored phase / past version / resolves to nothing / bare overall id in two versions / no `--reason` | `perry-goals krs [--level overall]`, `--okr-version "v4: …"` |
| withdraw | twice; no `--reason`; scored phase or past version; resolves to nothing | as above |
| check, measure | withdrawn KR | `perry-goals kr add` |
| overall writes | `OKR.md` still carries KR rows / store already drifted from the file | `TASK-236`, `perry-okr diff` |
| all | a flag the op does not take (e.g. `kr withdraw --set`) | exit 2, the op's flags |
| all | missing or empty `--actor` | exit 2 (`test_actor_required`, one case per op) |

**`[user-verify]` messages**, one per verb, as printed:

```
$ perry-goals kr add P004-O1-KR2 --objective O1 --text reuse --reason r --actor pmo      (after it was withdrawn)
perry-goals: refused — `P004-O1-KR2` already exists in linkage.jsonl and is withdrawn; KR ids are never reused (DESIGN-022 § 5.7). Choose a new id — `perry-goals krs` lists the ids in use. Nothing was written
$ perry-goals kr restate P004-O1-KR2 --set id=X --reason x --actor pmo
perry-goals: refused — `kr restate` refused: `id` is an identity field of the KR and cannot be set with --set. A KR is renamed or moved by withdrawing it and adding a new one: `perry-goals kr withdraw P004-O1-KR2 --reason "…" --actor <who> --root …`, then `perry-goals kr add …`. Fields --set may name: title, metric, target, current, due, stretch, linked, asserted_at. Nothing was written
$ perry-goals kr withdraw P004-O1-KR2 --reason again --actor pmo      (already withdrawn)
perry-goals: refused — P004-O1-KR2 was withdrawn at … (mistyped), and withdrawal is terminal: a withdrawn KR takes no `withdraw` (DESIGN-022 § 5.7). Its records stay in the store. To track the goal again, add it under a new id — `perry-goals kr add <NEW-KR-ID> --objective <O> --text "…" --reason "…" --actor <who> --root …`. Nothing was written
```

The `OKR.md` row of a withdrawn KR is the last `krs --level overall` line in § 3.

## 5. Mutations

`$TMPDIR/perry-scratch/<worktree>/mutate.py` ran each mutation on a fresh
`git archive` of the code head `12c941de`, with every `__pycache__` purged.
Each exact substring was asserted to occur once, so an anchor that misses
aborts rather than running green. The script then ran the named modules in that copy.

| # | Mutation | Red |
|---|---|---|
| M1 | fold applies revisions in file order, not `revised_at` | `TestTheFold.test_revisions_apply_in_revised_at_order_not_file_order` |
| M2 | fold accepts a revision after `withdraw` | `TestTheFold.test_withdraw_is_terminal…`, `TestReaders.test_perry_lint_names_a_hand_appended_revision…` |
| M2b | writer revises a withdrawn KR | `TestRefusals.test_restate_a_withdrawn_kr`, `test_withdraw_twice` |
| M3 | `add` reuses a withdrawn id | `test_add_reusing_a_withdrawn_id`, `test_add_reusing_a_withdrawn_overall_id` |
| M4 | writer accepts a restate of an identity field | `test_restate_an_identity_field_at_either_level`, `test_add_setting_an_identity_field` |
| M4b | fold applies an identity field | `TestTheFold.test_an_identity_field_is_not_applied_at_either_level`, the lint test |
| M5 | a withdrawn KR counted in `phase.kr_progress` | `TestPhaseEndToEnd…`, `TestTheFold.test_a_withdrawn_kr_leaves_every_count` |
| M6 | `measure` accepted on a withdrawn KR | `TestPhaseEndToEnd…`, `TestOverallEndToEnd…` |
| M7 | overall KRs rendered from the unfolded record (`overall_kr_model` without the fold) | `TestOverallEndToEnd…`, `test_commit_carries_a_revision_through_the_okr_md_gate` |
| M7b | an `OKR.md` carrying KR rows not refused | `test_an_okr_md_that_still_carries_kr_rows_is_refused` |
| M7c | the byte gate skipped on the KR append | `test_a_store_the_file_already_disagrees_with_is_refused` |
| M8 | the `kr_*` event omitted | `TestPhaseEndToEnd…`, `test_actor_required…test_each_mode_records_its_explicit_actor` |
| M9 | `perry-state` reads an unfolded snapshot | `TestReaders.test_perry_state_reads_the_restated_values` |
| M10 | `perry-goals list` reads an unfolded snapshot | `test_perry_goals_list_publishes_status…`, `test_the_overall_list_row_folds_its_own_store` |
| M11 | `krs` (phase) reads unfolded | `TestPhaseEndToEnd…` |
| M12 | the per-Objective cap counts withdrawn KRs | `test_add_beyond_the_cap_counts_active_krs_only` |
| M13 | `perry-lint` skips the revision findings | the lint test |
| M14 | `kr_revision` not a store-only kind of `okr.jsonl` | `test_every_record_the_writer_appends_lints_clean`, the lint test |

**Two mutations were green in round 1, and each became a test:**

- **M9 was green.** `perry-state`'s counts use `status`, which comes from the
  fold view whether or not the snapshot was folded, so nothing read the
  restated words in the payload. `test_perry_state_reads_the_restated_values`
  now holds it.
- **M14 was red only through an unrelated lint assertion.**
  `test_every_record_the_writer_appends_lints_clean` now holds it directly: no
  drift finding names a `kr_revision` key.

The table above is the re-run of all 18 on the final code head: all red.

## 6. Suites

| Run | Tree | Result |
|---|---|---|
| Baseline full | worktree at `5e5407ea`, before any edit | 154 modules · 4,312 tests · green |
| Baseline slow | clean `git archive` of `5e5407ea` (see below) | 158 modules · 4,415 tests · green |
| Affected, round 1 | `2f4fcfc5` | 13 of 154 modules red: the registries and contract pins listed in § 1, and `test_blank_cell_is_one_rule` (a local named `out`, bound elsewhere in the file to a `—`-bearing list); all fixed |
| Affected, final | `e935e8ce` | 159 of 159 selected, 155 run · green |
| **Full** | code head `12c941de`, `PERRY_PROJECT`/`PERRY_HOME` unset | **155 modules · 4,361 tests · all green** |
| **Slow** | code head `12c941de`, unset | **159 modules · 4,464 tests · all green** |
| `git diff --check 5e5407ea..HEAD` | | clean |

The full and slow tiers on the commit that adds this file are quoted in the
hand-off.

**One baseline was discarded.** The first slow-tier baseline was taken in the
worktree while the schema was already being edited, and one module went red
because of that edit. It was re-run on a clean `git archive` of `5e5407ea` in
scratch (green, as quoted above).

`tests/durations.json` records the new module at 0.77 s (1.31, 0.77 and
0.65 s alone, source `2026-09-18-task264-d3`, ref `7ed1333c`).

**Registries and pins each gained one entry.** None was loosened:

- `GATED`, the `test_actor_required` cases and its example set, the
  `write_atomic` call-site list, `PASTEABLE_WRITER_PHRASES` 56 → 58 (two new
  rooted hand-backs), and the declared-kinds set;
- the `3.5` → `3.6` pins;
- `shipped-semantics.json`;
- the `perry-goals/list` entry of `contract-key-parity.json`, only that
  entry. `--record` also rewrote `perry-task/list/2.4` from this repository's
  live state, and that part was not kept.

## 7. Deviations, findings and open questions

**Verified:**

1. **Folded KR in `OKR.md` → rendered on `krs`** (§ 2). This is a deviation
   from the letter of § 5.7 / spec item 4, and the PMO decides it.
2. **`okr.jsonl` had no `stores.declared` entry.**
   - Its kinds' fields live in `perry_md_store.STORED`, as `stores.note` says.
   - The new entry declares `kr_revision` only, and its description says so.
     `STORED["kr_revision"]` reads its fields from there.
   - `identity_fields` is a key inside both `kr_revision` declarations: the
     list § 5.7's table gives, read by `lib.kr_identity_fields`.
3. **Two exact equality tests are left as written.**
   - `objective_kr_summary` and `next_kr_progress` keep their return shapes,
     because `test_kr_checks` and `test_next_section` assert them by exact
     equality.
   - The withdrawn report is therefore `lib.withdrawn_krs` and
     `perry-state § next_kr_withdrawn`, plus the new next fact
     `phase.kr_progress.withdrawn`.
4. **`kr restate` records only the fields that change.** A named field
   already at that value is reported as `unchanged` and not recorded. If none
   change, the write is refused.
5. **`kr add` requires `--reason`, per "all three refuse".** The `kr` record
   has no reason field, so the reason goes on the `kr_add` event only.
6. **How `kr add` picks its level.** Without `--okr-version`, only a `P<NNN>-`
   id is taken as a phase KR. `O2-KR1` is legal at both levels and is refused
   with the two spellings.
7. **The per-Objective cap (4) is a constant in `perry-goals`.** It exists
   only as prose (`goals/SKILL.md § Style rules`), and a schema threshold
   would have been a second schema change.
8. **`revised_at` is `lib.event_stamp()`**: local time with an offset, as
   § 5.7's example is. The fold compares it through `ts_moment`.
9. **A pre-existing defect, not this row's; nothing was changed.**
   - `perry-goals commit` blanks every minted objective `id` whose heading is
     in `OKR.md`. `write_okr_and_store` re-derives those records with
     `id: ""`, a store-only field.
   - Probed on a clean `5e5407ea`:
     `[('v4', 'Objective 1 — Objective 1', 'O-11')] → [('v4', …, '')]`,
     with a "hand edit" warning.
   - After that, `krs --level overall` refuses the whole register (stranded
     KRs).
   - Perry's own `OKR.md` has no `## Commitments`, so this repository has not
     hit it.
   - `test_commit_carries_a_revision…` works around it by leaving the
     objective headings out of its fixture, and says why.

**Assumed, not verified:**

10. **The viewer shows unfolded KRs.**
    - `viewer/` calls `load_snapshot()` without the hook, so it shows the
      record's words and no status.
    - `perry-task`'s two `load_snapshot` calls read no KR, so they were left
      unfolded.
    - The viewer is outside this row.
11. **`perry-task add --kr` / `perry-goals link` may still attach an edge to a
    withdrawn KR.** § 5.7 names only `check` and `measure`.
12. **`krs[].revisions[]` subkeys are `not_observable` in the key-parity
    baseline.**
    - The witness project has no `okr.jsonl`, so its first KR row cannot
      carry a revision.
    - Filling it would change that fixture's KR source.
    - The subkeys are asserted directly in `test_goals_kr_revisions`.
13. **No `DESIGN-022 § 9` entry or `ARCHITECTURE.md` change was written.**
    Both are PMO / user documents. Rows for them, if any are wanted, are the
    PMO's call.

**Stop conditions:** none was hit. Phase 004's checks were not declared,
`P004-O4-KR2` was not restated, and no live KR was written.

## Repair round (USER-966), 2026-09-18

> Scope: V4 review `c0d5cd00:perry/evidence/2026-09/TASK-264-D3-review/review.md`
> (PASS-WITH-FINDINGS), findings F1, F3, F5 and F2 (the template).
> Built on `b6101c77`, on the same branch. Code head `001cac10`; this section
> is committed on top of it.
> Not in scope, and not changed: F4, F6, F7, TASK-467 (the `commit`
> objective-id bug).

### F1 — `perry-state` counted and showed withdrawn KRs

**Change** (`bin/perry-state`):

- `phase.kr_total` now leaves withdrawn KRs out.
- A new `phase.kr_withdrawn` reports the withdrawn count beside it. Existing
  field names are unchanged.
- Every KR entry in `phase.objectives[].krs[]` and `okr.objectives[].krs[]`
  now carries `status`, `withdrawn_at`, `withdrawn_reason` and `revisions`.
  These come from the same fold, and the overall KRs are keyed by the
  version label.
- `--compact` projects `status` on all three KR lists and projects
  `phase.kr_withdrawn`.
- `--dashboard` reads `… / 1 KRs (+1 withdrawn)`.
- `goals/SKILL.md`'s snapshot rule says a withdrawn KR shows as withdrawn and
  is not in `<KRs total>`.

**Tests extended, none weakened:**

- `test_compact_payload`: the key map gains `phase.kr_withdrawn`, and the
  three name tuples gain `status`.

**Test:**
`TestReaders.test_perry_state_leaves_a_withdrawn_kr_out_of_kr_total_and_marks_it`
checks `kr_total` and `kr_withdrawn` before and after, the `status` on both
lists, the compact payload and the dashboard line.

No contract page documents `perry-state`'s `phase` or `okr` block; the goals
contract's `kr_total` is `perry-goals list`'s and is unchanged.

**Mutations, all red:**

| Mutation | Red test |
|---|---|
| F1a — `kr_total` counts withdrawn KRs | that test |
| F1b — phase KR entries carry no `status` | that test |
| F1c — overall KR entries carry no `status` | that test |
| F1d — compact drops `status` | that test and `test_compact_payload…test_each_projection_still_picks_out_the_names_it_is_meant_to` |

### F3 — a withdrawn KR still accepted new task edges

**Change:**

- `perry-task add --kr <withdrawn>` is refused. The refusal names the
  withdrawal, `perry-goals krs` and `--unlinked`. Status comes from
  `lib.kr_revisions`.
- `perry-goals link`'s `Register` builds its graph with
  `kr_fold=lib.fold_kr_records`. A new `refuse_withdrawn_target` refuses an
  edge (`link <TASK> <KR>`) or a Project (`link --project`) on a withdrawn KR,
  and names the active KRs and `link --unlinked <TASK>`.

**Tests:** in `TestRefusals`, each with byte snapshots and an active-KR control:

- `test_perry_task_add_kr_to_a_withdrawn_kr`
- `test_link_an_edge_or_a_project_to_a_withdrawn_kr`
- `test_link_reads_the_folded_graph`

**Mutations, all red:**

| Mutation | Red test |
|---|---|
| F3a — `add --kr` accepts a withdrawn KR | the `add` test |
| F3b — `link` accepts a withdrawn KR | the `link` test |
| F3c — `link` reads the unfolded graph | `test_link_reads_the_folded_graph` |

### F5 — the overall append bypassed `assert_owned`

**Change:**

- `append_okr_record` now writes through the lane's
  `write_atomic(state_root, store, …)`.
- `owned_by_goals` now includes `okr.jsonl`, which is `owner: goals` in
  `schema § claims`. Before this change `assert_owned` would have refused it.
- The call-site registry in `test_okr_store_is_the_source` names the gated
  call.

**Test:** `TestRefusals.test_the_overall_append_goes_through_the_lane_gate`.

- The test swaps `assert_owned` for a refusing stub and runs `kr withdraw`
  on an overall KR in-process.
- It expects exit 1, the gate asked once about `okr.jsonl`, and no byte
  moved.

**Mutation, red:** F5, putting back the direct `lib.write_atomic(store, …)`,
turns that test red.

### F2 — the shipped OKR template prescribed KR tables

**Change:**

- `goals/state/OKR_TEMPLATE.md` loses its three KR tables and gains the
  pointer paragraph Perry's own `perry/OKR.md` carries: KRs live in
  `okr.jsonl`, are added with `perry-goals kr add … --actor`, and are read
  with `krs --level overall`. The objective headings stay.
- `goals/reference/setup.md § Structural contract` no longer prescribes a KR
  table. It says `OKR.md` holds the version blocks and objective headings,
  that KRs are added by the `kr add` verb, and that a file carrying KR rows is
  refused.
- `goals/reference/elicitation.md` and `planning.md` carry no such
  instruction, so they were not changed.

**Tests:**

- `TestAProjectFromTheTemplate.test_the_template_carries_no_kr_rows`: the
  scan finds no `kr` site, and the objective headings survive.
- `…test_a_project_instantiated_from_it_accepts_an_overall_kr_add`: the
  template is filled, then `perry-okr write --from-file`, then
  `perry-okr migrate-ids`, then `kr add O1-KR1`. The test expects exit 0, an
  unchanged `OKR.md`, and the KR under `Objective 1`.

**`test_parsers.TemplateContract.test_okr_template_yields_objectives_and_krs`
was rewritten, not weakened.** It read `KR-O1.1` out of the template's table,
which USER-966 removes. It now asserts, against the model the template ships:

- every objective parses;
- the store's KRs land under each objective by heading;
- `stretch` is read;
- a new check: no KR is read from the template's markdown.

`perry-lint --templates` is clean. `test_shipped_vocabulary`,
`test_procedures_call_the_tool`, `test_actor_required` (the new example names
`--actor`) and `test_pointers_resolve` are green.

**Mutation, red:** F2, putting one KR table row back in the template, turns
both template tests and `test_parsers…test_okr_template_yields_objectives_and_krs`
red.

### Method, suites and size

The script is `$TMPDIR/perry-scratch/<worktree>/mutate_repair.py`. Each run:

- takes a fresh `git archive` of `001cac10`;
- purges every `__pycache__`;
- asserts each anchor occurs exactly once;
- runs the named modules.

All 9 repair mutations were red.

| Run | Result |
|---|---|
| Affected, `--base b6101c77`, at `be888f95` | 120 modules; 1 red, `test_pointers_resolve` (a relative pointer in `setup.md`), fixed in `001cac10` and green alone |
| Final affected, full, slow and `git diff --check` | quoted in the hand-off, on the commit carrying this section |

Net lines against `5e5407ea`, at code head `001cac10`:

- **production Python** +1,138 / −40, net **+1,098**. This round added +78
  of them.
- **test Python** +986 / −19, net **+967**. This round added +188 of them.
