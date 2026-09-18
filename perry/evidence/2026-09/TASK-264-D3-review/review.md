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

---

# Re-review: the repair round (USER-966)

VERDICT: PASS

> Candidate: head `4dd6b457` (code head `001cac10`) on `worktree-agent-aebd0dddb8b7a2f89`, built on `b6101c77`. Base `5e5407ea`.
> Scope (USER-966): fix F1, F3 and F5; F2 is the template and `setup.md`. F4 and F6 are recorded only. The `commit` objective-id bug is TASK-467.
> Method: I reviewed `git diff b6101c77 4dd6b457` before reading the author's repair section, then checked its claims. Every probe ran on copies under the session scratchpad. My branch was moved onto `4dd6b457` with this file's first commit replayed on top.

## The four findings

| Finding | Status | Where |
|---|---|---|
| **F1** — `perry-state` counted and showed withdrawn KRs | **Resolved** on every `perry-state` surface | `bin/perry-state:1857-1871` (the overall fold, keyed by the version label), `:2029` (`okr.objectives[].krs[]`), `:2054` (`phase.objectives[].krs[]`), `:2063-2064` (`kr_total` without the withdrawn KRs, and a new `kr_withdrawn`), `:2871`, `:2884` and `:2900` (`--compact`), `:3035` (dashboard) |
| **F3** — a withdrawn KR accepted new task edges | **Resolved** | `bin/perry-task:3887-3899` (`add --kr`); `bin/perry-goals:1449-1453` (`link` reads the folded graph), `:1643` (`refuse_withdrawn_target`), `:1680` (edge), `:1813` (Project) |
| **F5** — the overall append bypassed `assert_owned` | **Resolved** | `bin/perry-goals:4066` (gated `write_atomic`), `:750` (`okr.jsonl` added to `owned_by_goals`, matching `owner: goals` in `schema § claims`) |
| **F2** — the template and `setup.md` prescribed KR tables | **Resolved** | `goals/state/OKR_TEMPLATE.md:57-61` (KR tables removed, pointer paragraph added, objective headings kept); `goals/reference/setup.md:46-58` (no KR table; points at the `kr add` verb) |

### F1, surface by surface

I measured each surface on a fresh copy of this repository's state, after `kr withdraw P004-O3-KR1` and `kr withdraw O3-KR5 --okr-version "v4: 2026-09-15"`:

| Surface | Before the repair (`b6101c77`) | After (`4dd6b457`) |
|---|---|---|
| `phase.kr_total` | 12 | **11**, and `phase.kr_withdrawn: 1` |
| Dashboard line | `4 objectives / 12 KRs` | `4 objectives / 11 KRs (+1 withdrawn)` |
| `phase.objectives[].krs[]` | no `status` | `status` on every entry (0 missing); `P004-O3-KR1` reads `withdrawn` |
| `okr.objectives[].krs[]` | no `status` | `status` on every entry (0 missing); `O3-KR5` reads `withdrawn` with its reason |
| `--compact` | no `status`, no withdrawn count | `status` projected on all three KR lists; `phase.kr_withdrawn: 1` |
| `schema/README.md` | — | Documents no `perry-state` phase or okr block, and says `perry-state --json` "is not a frozen contract". Nothing to update |

**One residue, Low (F11 below).** The documented payload that does carry `phase.kr_total` is `schema/goals-list-contract.md:383`, which belongs to `perry-goals list`. It still counts the withdrawn KR (`bin/perry-goals:1208`), and read **12** on the same copy where `perry-state` read **11**. The author left it unchanged on purpose, and said so. It is defensible, since the contract defines it as "counted from the phase's objectives" and a withdrawn KR stays in `krs[]`. But two payloads now publish a key with the same name and different answers.

### F3, probed

On the same copy:

- `perry-task add --kr P004-O3-KR1` (the withdrawn KR, written for real, not `--dry-run`) was refused. The message names the withdrawal, `perry-goals krs` and `--unlinked`.
- The same command with `--kr P004-O3-KR2` (an active KR) is accepted under `--dry-run`.
- `perry-goals link TASK-193 P004-O3-KR1` was refused, and the message lists the 11 active KRs and `link --unlinked TASK-193`.
- `diff -rq` against a pre-copy: no bytes moved.

`perry-task`'s only edge writer is `linkage_add_change`, called from `commit` for an `add` event only, and `--kr` is written verbatim, so matching the exact phase key `(id, "")` is enough. `link` refuses after the token is resolved, so a Project id or alias that resolves to a withdrawn KR is refused too.

## The two rewritten tests

**`test_parsers.TemplateContract.test_okr_template_yields_objectives_and_krs` (`tests/test_parsers.py:64`): honest, not weakened.**

- The original made four claims against the template's markdown:
  1. the objectives parse;
  2. every objective has KRs;
  3. `KR-O1.1` is read;
  4. the `Stretch?` column is read.
- USER-966 removes the rows, so claims 2–4 can no longer be true of the template's markdown. Asserting them there would mean restoring the thing the decision removed.
- The new version keeps claim 1 unchanged. It moves claims 2–4 to the model the template now ships: a store keyed by the template's objective headings, including the trailing `<!-- … -->` note, which the parser strips. The test gives the reason in its docstring.
- It adds one guard that is new and strictly stronger: no KR is read from the template's markdown.
- **What is lost.** The markdown `Stretch?` column is no longer read from a shipped file. The parsing itself is still covered by `test_overall_kr_grammar`, `test_md_store` and `test_goals_contract`.
- **What is slightly circular.** The test builds the store from the same headings it then checks. What it proves is that the template's headings key correctly, which is a real property of the template. It is not an end-to-end read.
- `TestAProjectFromTheTemplate` in `test_goals_kr_revisions` covers the end-to-end path.

**`test_compact_payload`: extended, not weakened.** The diff only adds names:

- `phase.kr_withdrawn` in the key-kind map;
- `status` in the three projection tuples.

No existing entry was removed or loosened. My mutations F1f and F1g turn it red.

## Mutations

Method:

- `scratchpad/mutate2.py` ran each mutation on a fresh copy of `git archive 4dd6b457`.
- Before each run it purged every `__pycache__` and ran `python3 -B` with `PERRY_PROJECT` and `PERRY_HOME` unset.
- Each anchor had to occur exactly once, or the run aborted.
- Modules run: `test_goals_kr_revisions`, `test_compact_payload`, `test_parsers`, `test_okr_store_is_the_source`, `test_kr_checks`, `test_next_section`, `test_goals_kr_writer`, `test_actor_required` and `test_pointers_resolve`.
- The unmutated control, S0, was green.

| # | Mutation | Result | Red tests |
|---|---|---|---|
| S0 | control: no mutation | GREEN | — |
| F1a | phase.kr_total counts withdrawn KRs | RED | `test_perry_state_leaves_a_withdrawn_kr_out_of_kr_total_and_marks_it` |
| F1b | okr.objectives[].krs[] carry no status | RED | `test_perry_state_leaves_a_withdrawn_kr_out_of_kr_total_and_marks_it` |
| F1c | phase.objectives[].krs[] carry no status | RED | `test_perry_state_leaves_a_withdrawn_kr_out_of_kr_total_and_marks_it` |
| F1d | overall status keyed without the version label | RED | `test_perry_state_leaves_a_withdrawn_kr_out_of_kr_total_and_marks_it` |
| F1e | dashboard drops the withdrawn suffix | RED | `test_perry_state_leaves_a_withdrawn_kr_out_of_kr_total_and_marks_it` |
| F1f | --compact drops phase.kr_withdrawn | RED | `test_every_field_is_projected_by_the_kind_this_file_expects`, `test_perry_state_leaves_a_withdrawn_kr_out_of_kr_total_and_marks_it` |
| F1g | --compact drops status from okr.objectives | RED | `test_each_projection_still_picks_out_the_names_it_is_meant_to`, `test_perry_state_leaves_a_withdrawn_kr_out_of_kr_total_and_marks_it` |
| F3a | perry-task add --kr accepts a withdrawn KR | RED | `test_perry_task_add_kr_to_a_withdrawn_kr` |
| F3b | link accepts an edge to a withdrawn KR | RED | `test_link_an_edge_or_a_project_to_a_withdrawn_kr` |
| F3c | link --project accepts a withdrawn KR | RED | `test_link_an_edge_or_a_project_to_a_withdrawn_kr` |
| F3d | link reads the unfolded graph | RED | `test_link_reads_the_folded_graph` |
| F5a | overall append back to ungated lib.write_atomic | RED | `test_no_other_subcommand_writes_OKR_md`, `test_the_overall_append_goes_through_the_lane_gate` |
| F5b | okr.jsonl dropped from owned_by_goals | RED | `test_a_project_instantiated_from_it_accepts_an_overall_kr_add`, `test_add_check_measure_restate_withdraw_then_measure_refused`, `test_add_reusing_a_withdrawn_overall_id`, `test_commit_carries_a_revision_through_the_okr_md_gate`, `test_every_record_the_writer_appends_lints_clean`, `test_perry_goals_list_publishes_status_and_the_folded_values`, `test_perry_state_leaves_a_withdrawn_kr_out_of_kr_total_and_marks_it`, `test_the_overall_append_goes_through_the_lane_gate`, `test_the_overall_list_row_folds_its_own_store` |
| F2a | a KR table row back in the template | RED | `test_a_project_instantiated_from_it_accepts_an_overall_kr_add`, `test_okr_template_yields_objectives_and_krs`, `test_the_template_carries_no_kr_rows` |
| F2b | setup.md prescribes the KR table again | GREEN | — |
| R1 | (round 1) fold applies revisions in file order | RED | `test_revisions_apply_in_revised_at_order_not_file_order` |
| R9 | (round 1) measure accepted on a withdrawn KR | RED | `test_add_check_measure_restate_withdraw_then_measure_refused` |
| R13 | (round 1) perry-state reads an unfolded snapshot | RED | `test_perry_state_reads_the_restated_values` |

**17 of the 18 mutations are red** (S0 is the control). That covers each fix at least once (F1 seven ways, F3 four, F5 two, F2 once) and three of my first-round mutations (R1, R9 and R13), which are still red. **F2b is green.** I then ran the full default tier on that copy, and it was still green (155 modules), so nothing guards `setup.md`'s prose against prescribing KR tables again. I record this as Info (F13), not a defect. The template itself is guarded (F2a is red), and a test that judged the meaning of a procedure page would come close to NN-4.

## Template regression (point 4)

`scratchpad/template_flow.sh` ran on a fresh `git init` folder, with `PERRY_PROJECT` and `PERRY_HOME` unset.

| Step | Result |
|---|---|
| `perry-lint --claims` | exit 0 |
| `perry-config set` × 4 (Document language, Chat language, Repo layout, State root `perry`), as in `reference/first-run.md § Writing the config store` | exit 0 each |
| `perry-goals draft create --horizon okr --route first … --body-file <the shipped template, placeholders filled>` | exit 0, `status: interviewing` |
| `draft update --status drafted`, then `draft approve` | exit 0 each; `approval_valid: true` |
| `draft finalize` | exit 1 by design (TASK-444: no overall authoring writer) |
| `OKR.md` from the approved body, then `perry-okr write --from-file`, then `perry-okr migrate-ids` | exit 0; 3 objective ids minted |
| `perry-goals kr add O1-KR1 --okr-version "v1: 2026-09-18" --objective O-1 …` | exit 0; `OKR.md` unchanged; `krs --level overall` lists it under "Objective 1 — Alpha" |

**No regression.** The one `perry-lint` error in the resulting project is `Due = 'filled'` in `## Commitments`, which is my own placeholder fill and not the template's.

Two things the run surfaced:

- **F12, Low, new.** `draft finalize` still lists "a KR add/restate/withdraw writer (TASK-264, not built)" as missing (`bin/perry-goals:4345-4348`, `DRAFT_MISSING`), and `goals/reference/planning.md:103-105` says the same. After this row that writer exists, so the refusal names one false reason. Finalize is still correctly unavailable, because the overall authoring writer is still missing.
- **Pre-existing, not this row's.** The template's `### Objective 3 — {{title}}     <!-- delete this block if only 2 Os -->` heading is printed with its comment by `krs --level overall` if the user keeps it. The `perry-okr` import step is itself something `planning.md` tells an agent not to do by hand. There is still no sanctioned path from an approved first-OKR draft to `OKR.md`, which is TASK-444's known gap.

## Suites and size

| Run | Result |
|---|---|
| `bash tests/run`, `PERRY_PROJECT` and `PERRY_HOME` unset, pycache purged | **155 modules · 4,368 tests · all green** (104.8 s) |
| `bash tests/run --tier slow`, same | **159 modules · 4,471 tests · all green** (188.5 s) |
| `git diff --check 5e5407ea 4dd6b457` | clean |

No module was red, so none needed re-running alone. The mutation driver ran at the same time as the suites, in separate directories, and nothing went red.

Net lines, measured with `git diff --numstat` at code head `001cac10`:

| Scope | Against `5e5407ea` | This round (against `b6101c77`) |
|---|---|---|
| Production Python (`bin/`, `viewer/`) | +1,138 / −40, **net +1,098** | net **+78** |
| Test Python | +986 / −19, **net +967** | net **+188** |
| Docs and schema (`goals/`, `schema/`, `reference/`) | +203 / −34 | — |

These match the author's figures exactly.

## Remaining findings, by severity

No Medium or High findings remain.

**Low**

- **F4** — `restate` checks type, not format. Recorded only, per USER-966.
- **F6** — `parsers` returns unfolded KRs unless the caller passes the hook. Recorded only, per USER-966. Its live instance, `perry-goals link`, is fixed by F3.
- **F7** — `phase.kr_progress.withdrawn` is a count, with the reasons elsewhere. Unchanged and acceptable.
- **F11 (new)** — `perry-goals list`'s `phase.kr_total` (`bin/perry-goals:1208`, `schema/goals-list-contract.md:383`) still counts withdrawn KRs, while `perry-state`'s now does not: 12 against 11 on the same project. Fix it with a `perry-goals/list` minor and a `semantics` note, or document the difference.
- **F12 (new)** — `DRAFT_MISSING` (`bin/perry-goals:4348`) and `goals/reference/planning.md:105` still say the TASK-264 KR writer is not built.

**Info**

- **F8, F9, F10** — as in round one.
- **F13 (new)** — no test guards `setup.md` against prescribing KR tables again (F2b is green on the full tier).
- **TASK-467** — out of scope, not reviewed.

## What I could not verify

- The rewritten `test_parsers` case against a template edited by hand in the ways a user would edit it. I checked only the shipped file and my filled copy.
- Consumers outside this repository, such as aiMark, that may read `perry-state`'s `phase.kr_total`, whose meaning changed in this round (it now excludes withdrawn KRs).
