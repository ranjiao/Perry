VERDICT: PASS-WITH-FINDINGS

# TASK-264 D3 — independent V4 review

> Candidate: `worktree-agent-aebd0dddb8b7a2f89`, head `b6101c77` (code head `12c941de`), base `5e5407ea`.
> Reviewer: an independent Coding Agent, in its own worktree. It did not write the candidate.
> Contract: `TASK-264-D3-spec.md`, `DESIGN-022 § 5.1–5.3, § 5.7, § 9` and User Decisions 5–7, `ADR-022`, `USER-952` and `USER-965`.
> Method: I formed my view from the contract and the diff first. I read `TASK-264-D3-result.md` afterwards and checked each claim.
> Scope: nothing was fixed, merged or pushed. This file is the only write under `perry/`. Every probe ran on a copy under the session scratchpad.

## Summary

§ 5.7 is implemented as specified: one fold rule, both levels, the three verbs, and the refusals. The schema change stays within `USER-952` and `USER-965`, and the `OKR.md` byte gate is untouched. Both suite tiers are green, and 26 of my 27 mutations turn a named test red. The one green mutation is equivalent, because the check it touches reads only identity fields.

There are no blocking defects. There are two Medium findings:

- `perry-state` publishes KR lists and a KR count that ignore withdrawal. This is a gap the author did not list.
- The `OKR.md` deviation needs a `DESIGN-022 § 9` entry before this lands.

## Findings, by severity

### Medium

**F1. `perry-state` still counts a withdrawn KR in `phase.kr_total`, and two of its KR lists carry no `status`.** The author did not list this.

- `bin/perry-state:2039` — `kr_total` is `len(P.phase_key_results(...))`, which still includes a withdrawn KR. `--dashboard` prints it (`bin/perry-state:3008`), and so does `--compact` (`:2859`).
  - Measured on a copy of this repository's own state, after `kr withdraw P004-O3-KR1`: `phase.kr_total` stayed at `12`, and the dashboard still read `4 objectives / 12 KRs`.
  - `phase.kr_progress` did drop it, from `12 of 12` to `11 of 11`.
- `bin/perry-state:2032-2037` (`phase.objectives[].krs[]`) and `:2008` (`okr.objectives[].krs[]`) publish the folded words but no `status`, `withdrawn_*` or `revisions`.
  - After `kr restate O3-KR5 --set metric=…` and `kr withdraw O3-KR5`, `okr.objectives[2].krs[4]` read `{"id": "O3-KR5", …, "metric": "probe metric", "stretch": true}`. Nothing in that entry says the KR is withdrawn.
  - Only `linkage.objectives[].krs[]` carries `status`.
- Against § 5.7:
  - Rule 4 says **every** KR reports `status` and `revisions[]`.
  - *Counting* says a withdrawn KR leaves **every** denominator.
- Why this is not High: the one count a rule reads (`phase.kr_progress` → `R-phase-closable`) is correct. The problem is what a consumer or the standup displays.

**F2. The `OKR.md` deviation is sound for this repository, but it needs a `DESIGN-022 § 9` entry, and it refuses template-born projects.** Point 4 of the brief has the details. The two follow-ups:

1. The PMO records the substitution of `krs --level overall` for `OKR.md` in `§ 9`, as `ADR-022`'s reopen clause invites.
2. The shipped template and `setup.md` stop prescribing KR tables. That inconsistency predates this row: it dates from TASK-236.

### Low

**F3. A withdrawn KR still accepts new task edges.** The author lists this.

- `perry-task add --kr P004-O3-KR1` on the withdrawn KR, with `--dry-run`, printed `would write TASK-467 (add) → tasks.jsonl + linkage.jsonl + journal + event`.
- `perry-goals link` builds its graph unfolded (`bin/perry-goals:1443`, `P.load_linkage(self.state_root, self.number)` with no hook).
- § 5.7 does not require this refusal, and the counts are unaffected because the KR leaves them anyway. But new work gets attributed to a KR that will never be scored, and `perry-lint` says nothing. Worth a row only if it is observed.

**F4. `restate` checks a field's type but not its declared format or reference.**

- `kr restate P004-O1-KR1 --set asserted_at=never --set linked=NOPE --set due=someday` exited 0.
- `asserted_at` is declared `format: iso-datetime`, and "absent when there is no `current`".
- `linked` named no overall KR.
- `typed_kr_value` (`bin/perry-goals:3901`) checks type only.
- This is not a regression: `perry-lint` does not flag these values on a raw `kr` record either (probed). But the verb makes the bad value easier to write, and it lands where no reader validates it.

**F5. The overall append bypasses `assert_owned`.**

- `append_okr_record` writes with `lib.write_atomic(store, prior_text + line)` (`bin/perry-goals:4032`).
- The phase path goes through the lane's gated `write_atomic(state_root, …)`.
- The only precedent for writing `okr.jsonl` ungated is `write_okr_and_store`, and there the store write follows a gated `OKR.md` write in the same function. Here there is no gated write at all.
- `tests/test_okr_store_is_the_source.py` lists the call site. Its own comment asks "check it is gated", and it is not.

**F6. `parsers.load_snapshot()` and `load_linkage()` return unfolded KRs by default.** The author lists this.

- NN-1 holds: the hook is a callable passed in, and `parsers` still imports only the stdlib.
- The one reader now answers two ways, depending on the caller. In this repository the only unfolded consumers are:
  - the `parsers.__main__` smoke print;
  - `perry-task`'s two snapshots, which read no KR;
  - `perry-goals link` (F3).
- So the "viewer" gap is Low today. It will catch the next tool that forgets `kr_fold=`.

**F7. `phase.kr_progress.withdrawn` is a count, and the reasons live elsewhere.** The author lists this.

- `objective_kr_summary` and `next_kr_progress` keep their shapes. `withdrawn_krs` and `next_kr_withdrawn` are separate helpers, and the fact publishes only `len(...)`.
- The reasons are on `linkage.objectives[].krs[]`, and `reference/next.md` says so.
- That reads § 5.7's "`withdrawn: n` with each reason" loosely but acceptably. The shapes were kept because of two exact-equality tests, which is a sound reason.

### Info

- **F8.** `_KR_IDENTITY_FALLBACK` (`bin/lib/__init__.py`) is a second copy of the identity list. It is used only when the schema is unreadable, and it is the union of both levels, so it refuses more restatements, never fewer. Acceptable.
- **F9.** The fold accepts a hand-appended `restate` of a field the level's `kr` record does not carry. For example, `colour`, or `order` on a phase KR: the phase `identity_fields` omit `order`, which is not a phase field. The writer refuses both, and § 5.7's lint list only asks for "non-identity". No action.
- **F10.** `kr_identity_fields` parses the 123 KB schema on every `kr_revisions` call, a few times per command. This is negligible.

## The brief's nine points

### 1. § 5.7 conformance, point by point

| Clause | Verdict | Evidence |
|---|---|---|
| Fold order: `revised_at`, compared as moments; file order on ties | ✓ | `placed.sort(key=(moment, line))` in `kr_revisions` (`bin/lib/__init__.py:2245`). Mutations R1 and R2 are red |
| Restate overwrites only the named fields | ✓ | `view["fields"].update(fields)`, laid over the record by `fold_kr_records`. R20 is red |
| Withdraw is terminal | ✓ | In the fold, a later revision is a finding and is not applied (R3 red). In the writer, `refuse_withdrawn_kr` runs before `restate`, `withdraw`, `check` and `measure` (R26, R9 and R10 red) |
| `status`, `withdrawn_at`, reason, `revisions[]` with before and after | ✓ on `krs` (both levels), `list` and `perry-state § linkage`. ✗ on two `perry-state` lists (F1) | `before` is the folded value just before that revision applies (R19 red) |
| Refusals, each naming its recovery | ✓ | Each refusal in § 5.7 has a test in `TestRefusals` that snapshots `linkage.jsonl`, `okr.jsonl`, `OKR.md` and the event log. The recovery for a scored phase or past version is a read (`perry-goals krs`) rather than a passing command. That is reasonable, since history cannot be revised |
| `check` and `measure` refuse a withdrawn KR | ✓ | R9 and R10 are red |
| A withdrawn KR leaves every denominator and is reported as withdrawn | Partly | `phase.kr_progress` ✓ (R8 red), `phase.kr_progress.withdrawn` ✓ (R27 red), cap counts active only ✓ (R22 red). `phase.kr_total` ✗ (F1). § 5.2's per-Objective counts have no publisher other than `next_kr_progress` |
| One event per write | ✓ | `write_kr_change` appends one event. The phase end-to-end test asserts the exact event list (R18 red) |
| `--dry-run` writes nothing | ✓ | `diff -r` against a pre-copy showed no byte moved after a `kr restate --dry-run` on a copy of the real state. R17 is red |
| `--actor` required; `--reason` required | ✓ | `test_actor_required` covers each op. R23 is red |

### 2. Schema scope

The schema diff is `+100 −0`. No existing entry changed.

- `kr_revision` is declared on `linkage.jsonl`.
- `stores.declared["okr.jsonl"]` is a new entry that declares `kr_revision` only.

**Judgement: within the authorization.** `USER-952` and Decision 5 authorize declaring the kind "on `linkage.jsonl` and `okr.jsonl`". `okr.jsonl` had no `stores.declared` entry, so declaring a kind there cannot be done without one.

- The entry's store-level keys (`owner: goals`, `anchor: state`, `format: jsonl`, `discriminator: kind`) repeat the existing `claims[]` entry for `okr.jsonl` and contradict nothing.
- Its `description` says that no other kind of the store is declared or changed.
- `identity_fields` is a new key, but it sits inside each `kr_revision` declaration, which is the new kind. It is the one place § 5.7's identity list is stated as data, and `lib.kr_identity_fields` reads it.
- **A tension to note, not a violation.** `stores.note` describes `stores.declared` as the stores "whose records are NOT a projection of a markdown document". `okr.jsonl` is partly a projection. The new entry's description addresses this: `kr_revision`, like `kr`, projects from nothing.

### 3. Architecture

- **NN-1.** `viewer/parsers.py` imports only the stdlib. `kr_fold` is a callable handed in by `bin/`, so there is no `viewer` → `bin` import edge and the §3 direction holds. `parsers` still reads each file once, and `lib` only orders and applies records, as § 9's 2026-09-16 entry settled. The cost is F6.
- **The `OKR.md` gate is unchanged and not weakened.**
  - No hunk touches `write_okr_and_store`, `md_store.plan` or `md_store.render`.
  - The only change on that path is `store_only_kinds=("kr", "kr_revision")`. It keeps a revision out of `records_not_in_the_file`, which is where a line-less record would otherwise be reported.
  - A `kr_revision` has no line in the file, so the byte comparison loses nothing.
  - `append_okr_record` runs the same `render(OKR.md, final) == OKR.md` comparison before appending.
  - On a copy of this repository's state, a restate and a withdraw of `O3-KR5` left `OKR.md`'s md5 unchanged, and `perry-okr diff` still reported `identical: true` and `every_line_and_cell_came_from_the_store: true`.
- **The fold rule is stated once**, in `lib.kr_revisions`.
  - The writer asks the fold for `status` and for the current value a restate would change.
  - `perry-lint` prints the fold's own findings (`kr_revision_findings`) rather than keeping a second list.
  - The writer's refusals (identity field, no field, no reason) are pre-write checks of the same conditions, not a second rule.

### 4. The author's deviation

**The fact holds.**

- `md_store.OKR.scan(perry/OKR.md)` finds `objective: 14` and `version: 4` sites, and **no `kr` site**.
- `kr` has been a `store_only_kinds` kind since TASK-236 (closed at V4 in `f15803f6`).
- `perry-goals krs --level overall` is the surface that renders the rows.
- On the copy, the withdrawn row rendered as:

```
| O3-KR5 | Contract-payload keys … (carried from v3) — withdrawn 2026-09-18: probe withdraw | probe metric | yes | 2026-11-17 |
```

**Judgement: this meets the intent of § 5.7 for this repository.**

- § 5.7 asks for three things: the folded words are what a reader sees, a withdrawn row stays visible with its marker, and the gate is not weakened. All three hold on the surface that carries overall KR rows.
- Reinstating KR rows in `OKR.md` would reverse TASK-236. Folding revised words into the file would rewrite the record, which § 5.7 forbids. Refusing the legacy layout, rather than writing a file that would show the old words, is the NN-3 answer.

**It leaves two gaps.**

1. **The design text.** § 5.7 still says "`OKR.md` renders the folded KR". `ADR-022` lists "the render gate cannot carry the folded KR" as a reopen trigger. A `§ 9` entry recording the substitution is the PMO's to write (F2).
2. **Template-born projects.**
   - `goals/state/OKR_TEMPLATE.md` still ships KR tables: scanning it finds `kr: 6`.
   - `goals/reference/setup.md § Structural contract` still prescribes them.
   - So a project whose `OKR.md` came from the shipped template has every overall `kr` write refused.
   - The refusal names a recovery: delete the tables, check `perry-okr diff`, then re-run.
   - The inconsistency predates this row and dates from TASK-236. It is not this row's defect, but the new verb makes it visible.

### 5. Mutations

Method:

- `scratchpad/mutate.py` ran each mutation on a fresh copy of `git archive b6101c77`.
- Before each run it purged every `__pycache__` and ran `python3 -B` with `PERRY_PROJECT` and `PERRY_HOME` unset.
- Each anchor had to occur exactly once, or the run aborted.
- Each mutation ran five modules: `test_goals_kr_revisions`, `test_kr_checks`, `test_next_section`, `test_goals_kr_writer` and `test_actor_required`.
- R0, the unmutated control, was green.

| # | Mutation | Result | Red tests |
|---|---|---|---|
| R0 | control: no mutation | GREEN | — |
| R1 | fold applies revisions in file order, not revised_at | RED | `test_revisions_apply_in_revised_at_order_not_file_order` |
| R2 | fold breaks revised_at ties in reverse file order | RED | `test_add_check_measure_restate_withdraw_then_measure_refused`, `test_equal_timestamps_apply_in_file_order`, `test_every_record_the_writer_appends_lints_clean` |
| R3 | fold accepts a revision after withdraw | RED | `test_perry_lint_names_a_hand_appended_revision_the_fold_skips`, `test_withdraw_is_terminal_and_a_revision_after_it_is_not_applied` |
| R4 | perry-lint drops the after-withdraw finding (fold unchanged) | RED | `test_perry_lint_names_a_hand_appended_revision_the_fold_skips` |
| R5 | kr add reuses a withdrawn id | RED | `test_add_reusing_a_withdrawn_id`, `test_add_reusing_a_withdrawn_overall_id` |
| R6 | writer accepts a restate of an identity field | RED | `test_add_setting_an_identity_field`, `test_restate_an_identity_field_at_either_level` |
| R7 | schema drops `objective` from the phase identity_fields | RED | `test_an_identity_field_is_not_applied_at_either_level`, `test_restate_an_identity_field_at_either_level`, `test_the_identity_fields_are_the_schema_s` |
| R8 | withdrawn KR counted in phase.kr_progress (objective_kr_summary) | RED | `test_a_withdrawn_kr_leaves_every_count`, `test_add_check_measure_restate_withdraw_then_measure_refused` |
| R9 | measure accepted on a withdrawn KR | RED | `test_add_check_measure_restate_withdraw_then_measure_refused` |
| R10 | check accepted on a withdrawn KR | RED | `test_add_check_measure_restate_withdraw_then_measure_refused`, `test_check_on_a_withdrawn_kr` |
| R11 | overall KRs rendered from the unfolded record | RED | `test_add_check_measure_restate_withdraw_then_measure_refused`, `test_commit_carries_a_revision_through_the_okr_md_gate` |
| R12 | withdrawn marker never rendered | RED | `test_add_check_measure_restate_withdraw_then_measure_refused` |
| R13 | perry-state reads an unfolded snapshot | RED | `test_perry_state_reads_the_restated_values` |
| R14 | perry-goals list reads an unfolded snapshot | RED | `test_perry_goals_list_publishes_status_and_the_folded_values`, `test_the_overall_list_row_folds_its_own_store` |
| R15 | phase `krs` reads unfolded | RED | `test_add_check_measure_restate_withdraw_then_measure_refused` |
| R16 | perry-lint cross-file check reads unfolded | GREEN | — |
| R17 | overall --dry-run writes | RED | `test_dry_run_writes_nothing` |
| R18 | two events per write | RED | `test_add_check_measure_restate_withdraw_then_measure_refused` |
| R19 | restate `before` taken from the base record, not the fold | RED | `test_revisions_apply_in_revised_at_order_not_file_order` |
| R20 | restate blanks the fields it does not name | RED | `test_equal_timestamps_apply_in_file_order`, `test_restate_overwrites_only_the_fields_it_names`, `test_revisions_apply_in_revised_at_order_not_file_order` |
| R21 | OKR.md carrying KR rows is not refused | RED | `test_an_okr_md_that_still_carries_kr_rows_is_refused` |
| R22 | cap counts withdrawn KRs | RED | `test_add_beyond_the_cap_counts_active_krs_only` |
| R23 | missing --reason accepted | RED | `test_add_without_a_reason`, `test_restate_without_a_reason`, `test_withdraw_without_a_reason` |
| R24 | restate that changes nothing accepted | RED | `test_restate_that_changes_nothing` |
| R25 | restate/withdraw in a scored phase / past version accepted | RED | `test_restate_in_a_scored_phase`, `test_restate_in_a_version_that_is_not_current`, `test_withdraw_in_a_scored_phase_or_past_version` |
| R26 | writer revises a withdrawn KR (restate/withdraw) | RED | `test_restate_a_withdrawn_kr`, `test_withdraw_twice` |
| R27 | phase.kr_progress.withdrawn fact always 0 | RED | `test_add_check_measure_restate_withdraw_then_measure_refused` |

The spec's seven are R1 (file order), R3 (a revision after withdraw), R5 (reusing a withdrawn id), R6 (restating an identity field), R8 (a withdrawn KR in `kr_progress`), R9 (`measure` on a withdrawn KR) and R11 (overall rows from the unfolded record). The brief's two extras are R13 (`perry-state` unfolded) and R4 (`perry-lint` accepting a revision after a withdraw, with the fold left intact). All nine are red.

**The one green mutation, R16, is equivalent.** `check_cross_file` reads only `kr.id`, `obj.id` and `projects[]`. A fold cannot change any of them, because identity fields are never applied. So folding there is harmless but unobservable, and no test could turn it red.

### 6. Tests

| Run | Result |
|---|---|
| `bash tests/run`, `PERRY_PROJECT` and `PERRY_HOME` unset, pycache purged | **155 modules · 4,361 tests · all green** (97.6 s, 8 workers) |
| `bash tests/run --tier slow`, same | **159 modules · 4,464 tests · all green** (133.9 s) |
| `git diff --check 5e5407ea b6101c77` | clean |
| `tests/test_goals_kr_revisions.py` alone, clean archive | 49 tests, OK |

Neither tier had a red module, so none needed re-running alone.

**Existing tests.** I read all nine edited test modules and the fixture. Every edit is one of the following, and none loosens an assertion:

- a registry entry;
- a `3.5` → `3.6` pin;
- `PASTEABLE_WRITER_PHRASES` from 56 to 58, with the two phrases named;
- a new expected kind;
- a new call site in the write-site list.

`contract-key-parity.json` adds `not_observable` entries for `revisions[]` subkeys. That is a real observability gap, but the subkeys are asserted directly in the new module.

### 7. The gaps the author lists

| Gap | Severity | Note |
|---|---|---|
| `perry-task add --kr` and `perry-goals link` can attach to a withdrawn KR | Low (F3) | Reproduced. Outside § 5.7's refusal list; counts unaffected |
| The viewer shows unfolded KRs | Low (F6) | In this repository the "viewer" is `parsers.__main__`. A risk for the next tool |
| `objective_kr_summary` and `next_kr_progress` keep their shapes, with separate withdrawn helpers | Low / acceptable (F7) | Keeps two exact-equality tests intact, and the reasons are reachable in the payload |
| *(not listed)* `perry-state` `phase.kr_total`, `phase.objectives[].krs[]` and `okr.objectives[].krs[]` | **Medium (F1)** | The author's list misses this |

### 8. Size

I confirmed the author's numbers with `git diff --numstat 5e5407ea 12c941de`:

- production is `+1,050 −30`, **net +1,020**;
- tests are `+791 −12`, **net +779**, of which 731 lines are the new module.

Code that could obviously be shared (about 60 lines; no rewrite asked):

- **`write_kr_change` repeats `write_kr_writer_result`** (the `check` and `measure` writer). The only difference is one `level == "overall"` branch, so a `store`/`appender` parameter on the existing helper would cover both.
- **`append_okr_record` restates `write_okr_and_store`'s gate**: `validate_records(final)`, then `render`, then compare. `okr_store_records` restates its load-and-malformed refusal. One small `okr_store_gate(text, final)` helper would keep the gate in one place. It would also be a natural home for F5's missing `assert_owned`.
- **`main`'s `kr` print block** mirrors the `check` / `measure` print block.

## The author's claims, checked

| Claim (result file) | Checked |
|---|---|
| Net lines, production +1,020 and tests +779 | ✓ exact |
| Full tier 155 / 4,361 and slow tier 159 / 4,464, green | ✓ reproduced |
| `OKR.md` has no KR row since TASK-236, and the gate is unchanged | ✓ (point 4) |
| Every § 5.7 refusal is tested with byte snapshots | ✓ by reading `TestRefusals` |
| 18 mutations red | Not re-run as written. My own 27 independent ones cover the same ground (26 red, 1 equivalent green) |
| "No existing schema entry changed" | ✓ (`+100 −0`) |
| `write_okr_and_store` docstring predates TASK-236 | ✓ (it still speaks of KR rows) |
| Pre-existing defect: `commit` blanks minted objective ids | **Not verified.** Outside this row |

## What I could not verify

- **The pre-existing `commit` defect** (result § 7.9). Not reproduced.
- **A real template-born project.** The refusal for an `OKR.md` that carries KR rows is tested on a fixture. I only scanned the shipped template (`kr: 6`); no real template-born project was run through it.
- **Consumers outside this repository**, such as aiMark. I did not check whether any of them read `perry-state`'s `okr.objectives[].krs[]` or `phase.kr_total` in a way that F1 would mislead.
- **Concurrency and clock skew.** Two `kr` writes in the same second tie on `revised_at` and fold in file order, as designed. The writer cannot revise a KR after its withdrawal, because it asks the fold first. A hand-appended revision stamped earlier than an existing withdraw would fold before it and be accepted, by the rule as written. I reasoned about this but did not probe it.
