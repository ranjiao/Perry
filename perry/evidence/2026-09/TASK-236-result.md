# TASK-236 — result

> Spec: `perry/evidence/2026-09/TASK-236-spec.md`
> Branch: `coding/task-236-okr-kr-tables`, from `a9e582a8` on `main`
> Rung: V4. `perry-okr render --write` is a write path and the row deletes 38
> rows of a tier-1 document on the strength of a store (`ADR-020`, `review.md
> § 0` question 1).
> Verdict on the second deliverable: **POSITIVE, qualified** — see § 3.

## 0. The gate, re-run in this tree BEFORE any edit

`DESIGN-009 § 6` step 2. Run on `a9e582a8` with a clean tree, as the first act
of the round:

```
$ git status --porcelain          # empty
$ bin/perry-okr diff
{
  "lines_from_store": 51,
  "lines_verbatim": [],
  "records_not_in_the_file": [],
  "cells_verbatim": {},
  "cells_wearing_decoration": {},
  "cells_the_store_and_the_file_disagree_on": [],
  "records_out_of_stored_order": [],
  "kinds": {
    "objective": 10,
    "kr": 38,
    "version": 3
  },
  "identical": true,
  "every_line_and_cell_came_from_the_store": true
}
exit 0
```

Both keys `true`. `kinds` re-measured here rather than copied from the spec:
**10 objective / 38 kr / 3 version — identical to the spec's numbers, no
divergence to report.**

### 0.1 The order was load-bearing, and this round can now prove it rather than assert it

The spec says a gate run after the deletion "passes vacuously". That is not a
prediction any more. Running `diff` on a tree with the tables already deleted
and all 38 records still in the store:

```
 identical: true
 every_line_and_cell_came_from_the_store: true
 kinds: {"objective": 10, "version": 3}          ← no `kr` key at all
 records_not_in_the_file: 38
 exit 0
```

**Both keys still report `true` and the exit code is still 0.** The KRs have
simply left the question. A round that ran the gate second would have quoted
two `true`s that said nothing about the 38 rows it was about to delete. This
is the sixth instance of that defect class the spec names, caught by ordering
rather than by luck.

## 1. What changed

| File | Change |
|---|---|
| `perry/OKR.md` | 38 KR rows + their 10 headers/separators deleted (68 lines). 10 `### Objective N` headings, 2 `## v<N>` blocks and the 3 `## Versioning log` rows stay — the Bound's remainder. One pointer block added per version block. |
| `bin/perry-goals` | `krs --level overall` — `overall_kr_model`, `cmd_overall_krs`, `render_overall_krs`; `--version <v>|all`; the malformed/duplicate/absent-store refusals. `write_okr_and_store` no longer reports store-only kinds as rows the file stopped rendering. |
| `bin/perry_md_store.py` | `Doc.store_only_kinds`; `OKR` declares `("kr",)`; `plan` excludes those kinds from `records_not_in_the_file`. |
| `tests/test_okr_krs_render.py` | New. 18 tests; the guard and its four mutations. |
| `tests/test_md_store.py`, `test_store_drift.py`, `test_phase_kr_declared_once.py`, `test_handed_back_root.py` | Retargeted off cells that no longer exist. Detailed in § 5. |
| `tests/durations.json`, `tests/fixtures/live-state-expectations.json` | Registration and a renamed baseline entry. |

`schema/state-schema.json` was **not** touched — see finding F-1, which is the
reason this row does not fully land.

## 2. Verification 2 — all 38 rows, enumerated, field by field

The expectation was captured from `perry/OKR.md` **before** the deletion, by a
parser written for this round that does not import `perry_md_store` — so the
comparison can witness the store being wrong, which one built from the store
could not (`TASK-182`'s bar). Compared against
`perry-goals krs --level overall --version all --json` **after** the deletion.

Fields compared per row: `text`, `metric`, `stretch`, `deadline`, `objective`.
Key is `(version, id)`, because `O1-KR1` exists in both version blocks with
different text and keying on `id` alone would collapse them.

```
rows in OKR.md before deletion : 38
rows perry-goals renders after : 38
38 rows x 5 fields = 190 field comparisons
ROWS THAT DIFFER: none
```

| # | version | objective | KR id | line in OKR.md @ a9e582a8 | reproduced by perry-goals |
|---|---|---|---|---|---|
| 1 | v2: 2026-08-17 | Objective 1 | `O1-KR1` | 65 | yes — 5/5 fields |
| 2 | v2: 2026-08-17 | Objective 1 | `O1-KR2` | 66 | yes — 5/5 fields |
| 3 | v2: 2026-08-17 | Objective 1 | `O1-KR3` | 67 | yes — 5/5 fields |
| 4 | v2: 2026-08-17 | Objective 2 | `O2-KR1` | 73 | yes — 5/5 fields |
| 5 | v2: 2026-08-17 | Objective 2 | `O2-KR2` | 74 | yes — 5/5 fields |
| 6 | v2: 2026-08-17 | Objective 2 | `O2-KR3` | 75 | yes — 5/5 fields |
| 7 | v2: 2026-08-17 | Objective 2 | `O2-KR4` | 76 | yes — 5/5 fields |
| 8 | v2: 2026-08-17 | Objective 3 | `O3-KR1` | 82 | yes — 5/5 fields |
| 9 | v2: 2026-08-17 | Objective 3 | `O3-KR2` | 83 | yes — 5/5 fields |
| 10 | v2: 2026-08-17 | Objective 3 | `O3-KR3` | 84 | yes — 5/5 fields |
| 11 | v2: 2026-08-17 | Objective 3 | `O3-KR4` | 85 | yes — 5/5 fields |
| 12 | v2: 2026-08-17 | Objective 4 | `O4-KR1` | 91 | yes — 5/5 fields |
| 13 | v2: 2026-08-17 | Objective 4 | `O4-KR2` | 92 | yes — 5/5 fields |
| 14 | v2: 2026-08-17 | Objective 4 | `O4-KR3` | 93 | yes — 5/5 fields |
| 15 | v2: 2026-08-17 | Objective 4 | `O4-KR4` | 94 | yes — 5/5 fields |
| 16 | v2: 2026-08-17 | Objective 5 | `O5-KR1` | 104 | yes — 5/5 fields |
| 17 | v2: 2026-08-17 | Objective 5 | `O5-KR2` | 105 | yes — 5/5 fields |
| 18 | v2: 2026-08-17 | Objective 5 | `O5-KR3` | 106 | yes — 5/5 fields |
| 19 | v2: 2026-08-17 | Objective 5 | `O5-KR4` | 107 | yes — 5/5 fields |
| 20 | v3: 2026-09-01 | Objective 1 | `O1-KR1` | 131 | yes — 5/5 fields |
| 21 | v3: 2026-09-01 | Objective 1 | `O1-KR2` | 132 | yes — 5/5 fields |
| 22 | v3: 2026-09-01 | Objective 1 | `O1-KR3` | 133 | yes — 5/5 fields |
| 23 | v3: 2026-09-01 | Objective 2 | `O2-KR1` | 139 | yes — 5/5 fields |
| 24 | v3: 2026-09-01 | Objective 2 | `O2-KR2` | 140 | yes — 5/5 fields |
| 25 | v3: 2026-09-01 | Objective 2 | `O2-KR3` | 141 | yes — 5/5 fields |
| 26 | v3: 2026-09-01 | Objective 2 | `O2-KR4` | 142 | yes — 5/5 fields |
| 27 | v3: 2026-09-01 | Objective 2 | `O2-KR5` | 143 | yes — 5/5 fields |
| 28 | v3: 2026-09-01 | Objective 3 | `O3-KR1` | 155 | yes — 5/5 fields |
| 29 | v3: 2026-09-01 | Objective 3 | `O3-KR2` | 156 | yes — 5/5 fields |
| 30 | v3: 2026-09-01 | Objective 3 | `O3-KR3` | 157 | yes — 5/5 fields |
| 31 | v3: 2026-09-01 | Objective 4 | `O4-KR1` | 163 | yes — 5/5 fields |
| 32 | v3: 2026-09-01 | Objective 4 | `O4-KR2` | 164 | yes — 5/5 fields |
| 33 | v3: 2026-09-01 | Objective 4 | `O4-KR3` | 165 | yes — 5/5 fields |
| 34 | v3: 2026-09-01 | Objective 4 | `O4-KR4` | 166 | yes — 5/5 fields |
| 35 | v3: 2026-09-01 | Objective 5 | `O5-KR1` | 172 | yes — 5/5 fields |
| 36 | v3: 2026-09-01 | Objective 5 | `O5-KR2` | 173 | yes — 5/5 fields |
| 37 | v3: 2026-09-01 | Objective 5 | `O5-KR3` | 174 | yes — 5/5 fields |
| 38 | v3: 2026-09-01 | Objective 5 | `O5-KR4` | 175 | yes — 5/5 fields |

The `objective` column is abbreviated here; the full authored heading was
compared, not the number. Note rows 28–30: v3's Objective 3 is a different
objective (`O-6`, *"The skill is the product"*) from v2's (`O-3`), and the
render attaches them correctly.

---

## 3. THE READ-SURFACE REPORT

> This is the row's second deliverable, written as a finding.
> `DESIGN-013 § 7` and `ADR-010 § What would reopen this` both say that if
> this report is negative, `TASK-237` stops and returns to `DESIGN-013`.

### 3.1 Verdict

**A CLI render IS a good enough reading surface for these key results.
POSITIVE, with one qualification that is mitigated and one loss that is real
and not recoverable.**

**But the verdict is on READING, and this round found a separate problem that
is not about reading and that `TASK-237` should weigh before proceeding: this
row closes the only supported path for a user to AUTHOR a key result, and
opens no replacement (finding F-2).** That is stated here rather than buried
in § 6 because the gate exists to catch things the decision did not anticipate,
and this is one.

### 3.2 What the render does better than the file did

1. **Completeness.** `perry-goals krs --level overall --version all` prints all
   38 KRs across both version blocks in one view. Opening `OKR.md` required
   scrolling two blocks — and it was already an *incomplete* history, because
   `## v1` was moved out to `phase/snapshots/okr-v1.md` on 2026-09-03 for the
   tier-1 200-line cap. The file had already stopped being the whole answer.
2. **Nothing is elided.** Every cell prints whole. The longest KR text on this
   project is 341 characters (`O2-KR5`) and it renders in full.
3. **Same shape.** The output is the same five-column markdown table, through
   `tables.render_row` — the one row renderer in the repository, which escapes
   a `|` in a cell and REFUSES a cell holding a line break rather than writing
   a row that swallows the rest of the table.
4. **It says what it is.** The render prints *"This is a render, not a file:
   the store is the only place these values live"* and lists the versions the
   store holds, so a reader who sees one block knows others exist.
5. **It refuses rather than printing a short table.** A malformed record, a
   duplicate key, or an absent store all exit 1 and name the cause. The failure
   mode this project has actually paid for — `TASK-437`, where `perry-goals`
   published a plausible number computed from 156 of 429 records — is a reader
   that drops what it cannot read and prints the rest. This one does not.

### 3.3 The qualification, and how far it is mitigated

**A reader who opens `perry/OKR.md` now finds objective headings with nothing
under them.** That is a worse document than it was, and no CLI command fixes
it for someone who is reading the file rather than running a tool.

Mitigated, not solved: each version block now carries a pointer naming the
store, the command, and the reason. So the file answers *"where did they go"*
in place, which an empty heading does not. It does not answer *"what are
they"*, and a reader browsing the repository on the web still cannot see a key
result without a shell.

This loss is **the same class** `DESIGN-013 § 4.1` already accepted for
`DECISIONS.md` (*"a web reader lands in `decisions/` and reads the directory
listing"*) — but it lands for the first time on a **tier-1 authored document**
rather than on a projection, which is a difference `ADR-015` cares about and
`DESIGN-013` did not discuss. See § 3.5.

### 3.4 The negative finding inside the positive verdict: the discoverable surface is the wrong one

`perry-goals list --level overall` already existed and is what a reader is
likeliest to try first. Measured on this tree:

- it prints **19** of the 38 KRs (the current version only);
- it **truncates** KR text to a fixed column width — `O1-KR1` prints as
  *"Non-`project` modes running on a live track "* and stops;
- `Metric / Target`, `Stretch?` and `Deadline` all print as `—`.

So the obvious command gives a materially worse view than the file did, and
only `krs --level overall` is adequate. **This does not make the verdict
negative** — an adequate surface exists, is documented in `--help`, and is
named in `OKR.md` itself at both pointers. It does mean the render being good
enough is a property of *one specific command*, and `TASK-237` should not
generalise from "a CLI render was fine for the OKR" to "a CLI render is fine",
because the OKR had two and one of them was not.

### 3.5 The `ADR-015` tier-1 boundary, argued rather than left to be discovered

The spec asks for this explicitly, and the answer is not the one the spec
anticipated. The spec says *"after this row it is a tier-1 document whose KR
half is a render"*. **It is not.** The KRs are not rendered into `OKR.md` at
all — they are absent from it. `perry_md_store.render` fills existing lines and
never creates them, so with no KR rows in the file there is nothing for the
renderer to write there, ever.

That matters, because it means the boundary **holds, and more cleanly than the
spec expected**:

- `OKR.md` does not become half-projection. It becomes a *smaller authored
  document*. Everything still in it — mission, operating principles,
  anti-goals, the objective headings, every rationale paragraph, the
  versioning log — is exactly as hand-editable as before, and a hand edit to a
  projected cell is still reported as drift (`test_store_drift`, retargeted to
  a `## Versioning log` cell and still red under mutation M3).
- `ADR-015`'s tier-1 rule is about whether hand editing is *legitimate*. For
  everything the file contains, it still is.
- There is precedent within the file itself: the whole `## v1` block left
  `OKR.md` on 2026-09-01 without anyone arguing the file stopped being tier 1.

**Where the argument does NOT hold is writing, and that is F-2.** `ADR-015`
says *"Tier 1 stays the user's, and hand editing it stays legitimate"*, and for
key results that sentence is now void: there is no longer anything to hand-edit
and no tool that writes one. `ADR-015`'s own cost note anticipated the shape —
*"a user who wants to fix a board cell by hand now cannot. The tool path must
cover what hand editing covered"* — and for `BOARD.md` it could name the tool
path that does (`perry-task`'s six statuses plus `next`/`retitle`/`evidence`/
`rung`/`prioritize`/`depends`). **For `okr.jsonl` there is no such tool.**

### 3.6 What this says about `TASK-237`, since that is what the gate is for

On the question the gate actually asks — *is a CLI render good enough to read*
— the answer is yes, and `TASK-237` is not blocked by this report.

Two things carry forward rather than generalise:

1. **The asymmetry in F-2 runs in `TASK-237`'s favour.** The reason this row is
   uncomfortable is that the goals lane has no KR writer. `BOARD.md` does not
   have that problem: `perry-task` is a complete writer, which `ADR-015` § 
   Consequences already states. So the worst finding here is one `TASK-237`
   does not inherit.
2. **§ 3.4 does not carry forward for free.** `BOARD.md`'s replacement surface
   must print a 2,825-byte `Next action` cell whole. This row's adequate
   surface prints a 341-byte cell whole; its *inadequate* one truncates to a
   column width. `TASK-237` should verify the cell-whole property on the real
   maximum rather than assume it.

---

## 4. Mutations

Every claim below was shown by reverting the thing the guard guards and
watching a NAMED test go red. Product files were restored from byte copies
taken before the round and re-diffed afterwards; no mutation residue remains.

| # | What was broken | Where | Result | Named test(s) that went red |
|---|---|---|---|---|
| M1 | Render drops the last KR of every objective (`rows` → `rows[:-1]`) | `bin/perry-goals § overall_kr_model` | **RED — 7 tests** | `test_version_all_renders_every_declared_kr`, `test_the_default_is_the_current_version_only`, `test_one_version_can_be_named`, `test_the_markdown_render_prints_every_kr_whole`, `test_a_blank_cell_renders_as_a_dash_and_not_as_the_word_none`, `test_a_kr_reattached_to_the_wrong_objective_reddens`, `TestTheShippedOkr.test_every_stored_kr_reaches_the_render` |
| M2 | `--version all` silently returns the current version only | `bin/perry-goals § overall_kr_model` | **RED — 5 failures + 1 error** | `test_version_all_renders_every_declared_kr`, `test_an_okr_jsonl_emptied_of_its_krs_reddens`, `test_the_markdown_render_prints_every_kr_whole`, `test_a_kr_reattached_to_the_wrong_objective_reddens`, `test_every_stored_kr_reaches_the_render` |
| M3 | `store_only_kinds` filter removed from `records_not_in_the_file` | `bin/perry_md_store.py § plan` | **RED — `perry-okr verify` exit 1, and 5 tests** | `test_store_drift.test_an_edited_okr_cell_is_reported`, `.test_the_human_census_goes_red`, `.test_untouched_files_are_clean`, `test_lint_and_the_tool_agree_on_a_clean_tree`, `.test_lint_and_the_tool_agree_on_an_edited_tree` |
| M4 | **Anti-vacuity, on the LIVE store.** All 38 `kind: kr` records deleted from `perry/okr.jsonl` | `perry/okr.jsonl` | **RED — 4 tests. See § 4.1** | `test_okr_krs_render.TestTheShippedOkr.test_every_stored_kr_reaches_the_render`, `test_md_store.test_every_kr_carries_the_id_of_the_objective_above_it`, `.test_only_the_two_id_fields_move`, `.test_the_shipped_reader_gets_every_kr_from_the_store` |
| M5 | **The `TASK-182` trap itself.** `check_roster` derives its expectation from the payload it compares | `tests/test_okr_krs_render.py` | **RED — 3 tests** | `test_a_corrupted_kr_field_reddens`, `test_a_deleted_kr_record_reddens`, `test_an_okr_jsonl_emptied_of_its_krs_reddens` |

**No mutation came back green.** M5 is the one worth reading twice: the three
mutation cases assert that `check_roster` *raises*, so a guard rewritten to
compare the payload against itself stops raising and those three go red
immediately. A self-referential guard cannot be introduced here quietly.

The spec's mutations 3 and 4 — corrupt one record, then delete one — are also
permanent tests rather than one-off demonstrations
(`TestAMutationReddens.test_a_corrupted_kr_field_reddens` and
`.test_a_deleted_kr_record_reddens`), deliberately separate cases because a
guard can notice a changed cell and be blind to a missing row.

### 4.1 M4 in full, because it is the finding the spec asked for

With all 38 KR records removed from the live `perry/okr.jsonl`:

```
bin/perry-okr diff    →  exit 0
                         identical: true
                         every_line_and_cell_came_from_the_store: true
                         kinds: {"objective": 10, "version": 3}
bin/perry-okr verify  →  exit 0
```

**Both of the tools that used to guard these records are silent.** That is not
a defect introduced by this round — it is the direct, intended consequence of
`ADR-019`'s trade, which makes drift impossible rather than detected and
therefore takes the detector away with the duplicate. It is written down here,
and in `Doc`'s own docstring, because a gate that has stopped covering
something must say so rather than keep reporting `true`.

What reddens instead is `tests/test_okr_krs_render.py`. That module is the
replacement gate, and M4 is the demonstration that it is one.

---

## 5. The suite

```
baseline @ a9e582a8 :  127 modules, 3665 tests, 3 failed
after this round    :  128 modules, 3684 tests, 3 failed
```

The three are the pre-existing ones named in the dispatch, unchanged and not
attributable to this row:

- `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`
- `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness`
- `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`

`+1` module and `+19` tests: `tests/test_okr_krs_render.py` (18) and one added
to `test_md_store.py`.

**One red was investigated and is not mine.** An intermediate full-suite run
showed `test_host_support.TestOpenCodeDispatchLimit.test_concurrent_mixed_registers_do_not_exceed_global_cap`
failing. Re-run alone twice: **OK both times** (35 tests). It launches 20
concurrent dispatches against a global cap of 3 and is load-sensitive; it was
green in the baseline run, red in one middle run, and green in the final run.
Nothing in this row touches dispatch limits. Recorded rather than attributed.

### 5.1 Tests retargeted, and why each is a move rather than a deletion

Every one of these asserted something about a cell of a KR table in
`perry/OKR.md`. The claims survive; the cell they land on moved to the
`## Versioning log`, which `OKR.md` still projects. Each was confirmed still
capable of failing — M3 reddens five of them.

| Test | Was | Now |
|---|---|---|
| `test_md_store.test_an_okr_kr_field` → `test_an_okr_table_field` | mutated a `kr` record's `deadline` | a `version` record's `date` |
| `test_md_store.test_an_okr_hand_edit` | `\| 3 of 3 modes live \|` | `\| v1 \| 2026-08-17 \|`, column `Date` |
| `test_md_store.test_an_appended_hand_edit_is_counted_rather_than_hidden` | appended to a KR metric cell | appended to the same `Date` cell |
| `test_md_store.test_a_deleted_line_is_reported_rather_than_dropped` | deleted the `O1-KR1` row | deletes the `v1` row — **and is now also the control for `store_only_kinds`**, because it deletes a kind that is still projected |
| `test_md_store.test_a_cell_the_store_forgot_fails_the_gate` | blanked a `kr.metric` | blanks a `version.what` |
| `test_md_store.test_a_cell_wearing_unstored_words_fails_the_gate` | decorated a KR cell | decorates the `Date` cell |
| `test_md_store.test_render_write_puts_a_drifted_file_back_in_line` | drifted a KR cell | drifts a `## Versioning log` cell |
| `test_store_drift` × 3 | `\| 3 of 3 modes live \|` | `\| v1 \| 2026-08-17 \|` |
| `test_phase_kr_declared_once.test_every_linked_value_names_an_overall_kr_this_project_declares` | historical overall KRs scanned out of `OKR.md`'s rows | **unions** that scan with `okr.jsonl`; the markdown scan is kept because an adopted project's `OKR.md` still carries those rows |

Two were **rewritten rather than retargeted**, because their premise was the
duplication itself:

- `test_md_store.test_the_store_holds_every_kr_the_shipped_reader_reads` →
  `test_the_shipped_reader_gets_every_kr_from_the_store`. It compared two
  readers of one file; there is one copy now, and with the tables gone both
  sides returned the empty set — it would have passed for exactly the reason
  its own `assertTrue(read)` line existed to refuse. It now asserts the reader
  a consumer actually runs (`parse_okr(text, krs=load_okr_store(...))`, the
  `load_snapshot` path) sees exactly the store's current-version KRs.
- `test_md_store.test_perry_goals_list_is_identical_before_and_after_the_store_exists`
  now builds a small pre-migration `OKR.md` that still carries KR tables,
  instead of copying this repository's. The claim is about the **migration** —
  minting a store must not move a reader's payload — and copying a file that
  has already migrated made both sides empty, which is the vacuity its
  `assertGreater` guarded against.

One new test was added for the other half of the change:
`test_the_markdown_arm_now_finds_no_krs_in_the_shipped_okr`. A KR table
reappearing in `perry/OKR.md` would restore the second copy `ADR-019` removed,
and this catches it before drift does.

`tests/test_handed_back_root.PASTEABLE_WRITER_PHRASES` went 65 → 66. That
guard caught a real defect in this round's own code — see F-4.

---

## 6. Findings

### F-1 · BLOCKER — the row cannot fully land without a `schema/state-schema.json` edit, which this round is forbidden to make

`perry-lint` now reports **one** new warning on this repository:

```
⚠ perry/OKR.md [missing-table] no table found under /^(Objective|目标) \d+/
0 error(s), 57 warning(s)          (was 0 errors, 56 warnings)
```

`schema/state-schema.json § files[id=okr].tables[0]` declares that table with
`under: "^(Objective|目标) \\d+"` and **no `"optional": true`**, and
`bin/perry-lint:1249` warns when a declared, non-optional table's section
exists with no table under it. The `### Objective N` headings must stay — the
spec's Bound requires it — so the section exists and the table does not.

**The fix is one key**: `"optional": true` on that table spec. `bin/perry-lint`
already honours it and documents the precedent (`## Top risks` is a bullet list
on unmigrated projects). I have not made the edit: `schema/state-schema.json`
is on `.perry/hook.md § High-stakes operations`, the spec forbids it in
*What it must not do* 3, and the dispatch says a schema change is a finding to
report rather than an edit to make.

Two things worth knowing before that decision:

- It is a **warning, not an error**. `perry-lint` still exits 0 with 0 errors,
  so nothing is gated on it today. But `O3-KR1` targets *"`perry-lint` reporting
  zero errors"* for adoption, and a permanent warning on Perry's own tier-1
  document is a bad example for a tool whose census is its product.
- I measured **one** warning, not ten. `found_any` in `check_file` is
  initialised once per table spec, not per section, so ten empty objective
  sections produce a single finding.

**Recommendation**: mark the table `optional` with the user's authorisation,
in this row or a follow-up, before `TASK-237` runs. Leaving it teaches readers
to ignore a `missing-table` warning, which is the one warning that would catch
a KR table being deleted by accident on a project that still uses them.

### F-2 · The row closes the only supported path for authoring a key result, and opens none

Argued in § 3.5; stated here as the finding it is.

Before this row a user authored a KR by typing a table row into their own
tier-1 `OKR.md` and running `perry-okr write --from-file` to mint the store.
After it, measured in this tree:

```
$ bin/perry-okr write --from-file
perry-okr: refusing to overwrite .../perry/okr.jsonl.
  This command derives the store FROM OKR.md ... 48 stored value(s) would be
  replaced by what it happens to say:
    kr/…/O1-KR1: in the store, no line in the file — the whole record would be dropped
    … (38 KR records, plus 10 objective ids blanked)
```

The refusal is **correct** — running it would destroy all 38 records — but it
means the document authoring path is now closed by construction. And
`bin/perry-goals` has no subcommand that writes a `kind: kr` record:
`commit` writes `## Commitments`, `link` writes `linkage.jsonl`, `krs` and
`list` are reads. This is not new in itself — `O2-KR1` records that the goals
lane has no deterministic write tool, and notes that authoring v3 *"required
hand-appending `okr.jsonl`"* — but this row removes the workaround that made
that survivable.

So the only remaining way to add or revise a KR is to hand-edit `okr.jsonl`,
which is a tier-2 store that `ADR-015` says a hand edit to should be *refused*.

**Left unfixed, deliberately.** Building a KR writer for the goals lane is
`O2-KR1`'s own work, it is not in this row's Bound, and it is a write path that
would need its own V4 round. Filing it is the right move, not smuggling it in
here. It belongs to whoever schedules `O2-KR1`, and `TASK-237` should know it
exists.

### F-3 · The spec's `viewer/parsers.py` measurement is wrong: **zero** lines retire, not 26

The spec says *"Deleting the tables retires one function in `viewer/parsers.py`:
`_parse_krs`, 26 lines of code"* and tells me to report the measured number.
Measured here:

- `_parse_krs` is `viewer/parsers.py:2486-2512` — **27 lines**, not 26.
- It has **two** callers. `parsers.py:2671` is the OKR arm, reached only when
  `stored_krs is None`. `parsers.py:2770` is inside `parse_phase` and is
  **unconditional**.
- `parsers.py:2763-2767` is a pre-existing comment saying so in as many words:
  *"`_parse_krs` still runs, and TASK-157 did not make it dead code: … an
  ADOPTED project's does, and so does a Perry project that has not migrated."*

**So nothing retires.** The function stays live for phase documents on every
project, and its OKR arm stays live for any project without an `okr.jsonl`.
What this row buys in `viewer/parsers.py` is that Perry's own OKR stops taking
the markdown arm — a behaviour change, not a deletion. The spec's own
instruction — *"Report the measured number; do not claim more"* — is what this
finding discharges. No code was removed from `viewer/parsers.py` in this round.

### F-4 · A defect in this round's own code, caught by an existing guard

`overall_kr_model`'s no-store refusal hands the reader
`perry-okr write --from-file` — a writer — and I wrote it without a `--root`.
`tests/test_handed_back_root` caught it:

```
FAIL test_no_pasteable_writer_is_handed_back_without_the_root
  ["bin/perry-goals:2869 'perry-okr write --from-file'"]
```

Fixed by appending `lib.root_flag(project_root)`, and
`PASTEABLE_WRITER_PHRASES` raised 65 → 66 with the reason recorded at the
constant. Noted because that guard's own docstring predicted "an eighteenth"
and this is it — the guard working, on new code, within an hour of it existing.

### F-5 · A fourth pre-existing suite red the dispatch did not name

The dispatch names three. There is a fourth, unrelated to this row:
`tests/test_contract_page_snippets.py` is on disk and absent from
`tests/durations.json`. It makes `tests/run` print

```
✗ not in durations.json: test_contract_page_snippets.py
```

and fails two tests in `test_durations_provenance` when that module is run
directly (`test_every_module_on_disk_is_listed`,
`test_the_live_file_parses_into_the_declared_shape`). Verified pre-existing by
computing the same set difference against `a9e582a8`'s `durations.json`: the
module was missing there and is missing now; my own module registered
correctly. **Left unfixed** — it is one line in a file this row has no business
editing beyond its own entry, and it is somebody's row, not a footnote to
mine.

---

## 7. Constraint 5 — what stops the KR tables being written back

The spec asks what guards `perry-okr render --write` from restoring what this
row removes. There are two guards, and the first is structural:

1. **`render` fills lines; it never creates them.** `perry_md_store.render`
   calls `plan`, which walks the sites the *file* scans into and matches each
   to a record. A record with no site renders nothing at all. So with no KR
   rows in `OKR.md` there is no line for a KR record to render into, and no
   amount of re-rendering produces one.
2. **`render --write` refuses outright when a stored record has no line** —
   `bin/perry_md_store.py:1467-1480`, `DESIGN-016 A5`. Demonstrated in this
   round on a copy before `store_only_kinds` existed:

   ```
   perry-okr: refusing to write OKR.md — 38 stored record(s) have no line in
   it to render into, and `render` fills lines rather than creating them.
   Nothing was written.
   exit 1
   ```

After `store_only_kinds`, guard 2 no longer fires for `kr` (that is its
purpose — the refusal was permanent and meaningless), and guard 1 still holds.
Verified on this tree:

```
$ bin/perry-okr render --write
perry-okr: rewrote .../perry/OKR.md — 0 line(s) changed, 131 unchanged,
                                      from 51 stored record(s)
$ grep -c '^| O[0-9]-KR' perry/OKR.md
0
```

`test_okr_krs_render.TestTheShippedOkr.test_the_shipped_okr_md_carries_no_kr_table_rows`
asserts it, and `test_the_markdown_arm_now_finds_no_krs_in_the_shipped_okr`
catches the rows returning by any other route.

**The residual, stated rather than hidden**: `scan_okr` still *recognises* a KR
table. If someone hand-writes one back into `OKR.md`, it will be scanned and
adopted again. I did not remove KR scanning, because `perry-okr write
--from-file` is the documented migration path for a project whose `OKR.md`
still carries tables, and removing it would break adoption for exactly the
projects `ADR-010` names. That is a deliberate trade, not an oversight, and
the new test is what notices if it happens on this project.

## 8. Out of scope, untouched

- `schema/state-schema.json` — F-1, reported not edited.
- `ARCHITECTURE.md § 2` — **not edited, and no stop-and-ask raised, because
  nothing in this round contradicts it.** Read rather than assumed: the only
  mention of the file is `§2 › viewer/parsers.py`, *"Owns: `BOARD.md`,
  `OKR.md`, phase, linkage, config and architecture parsing"*. That is still
  true — `scan_okr` still scans the objective headings, the version blocks and
  the `## Versioning log`, and `_parse_okr_objectives` still reads the
  headings. What changed is which *kinds* the parse yields, which § 2 does not
  enumerate. If a reviewer reads that line as claiming the KR tables
  specifically are parsed, that is a `DESIGN-017` stop-and-ask and a follow-up
  row.

  **One stale number there, which this row makes one worse and did not
  create.** `§2 › tests/` is headed *"125 modules"*; there were **127** on
  disk at `a9e582a8` and there are **128** now. Not edited — the dispatch
  forbids editing `ARCHITECTURE.md § 2` without asking, and a stale count in a
  document nobody executes is a row to file, not a thing to fix in passing
  (`review.md § 0`, *"a false statement in something nobody executes"*).
- `TASK-237`, `TASK-262` — gated on § 3.
- `phase/<NNN>-<slug>.md`'s KR tables — different file, different row
  (`TASK-157` already did that one).
- The 10 `objective` and 3 `version` records — the Bound's remainder, all 13
  still projected and still compared.
