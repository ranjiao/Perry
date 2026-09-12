# TASK-236 — round 1, V4 fresh-context review

> Criteria: `perry/evidence/2026-09/TASK-236-spec.md` — its `## Bound`,
> `## What it must not do`, `## Verification` and `## Out of scope`, and
> nothing else.
> Under review: `ec499b54`, merged at `687579bd`; F-1's follow-up `6032bb45`.
> Reviewer base: `85c6f747`. Reviewed in an isolated worktree.

## 0. Base check — the handed worktree was WRONG, and was corrected before anything else

The dispatch told me to check rather than assume. I did, and it was wrong.

```
$ git log --oneline -1
583f024f Merge bin-contract-phase-a: DESIGN-016's thirteen closed rows …
$ git merge-base --is-ancestor 85c6f747 HEAD   → NOT an ancestor
```

Measured rather than guessed:

| | |
|---|---|
| handed HEAD | `583f024f` |
| `git merge-base HEAD 85c6f747` | `583f024f` — HEAD **is** the merge base |
| `git rev-list --count 85c6f747..HEAD` | **0** |
| `git rev-list --count HEAD..85c6f747` | **110** |
| `687579bd` / `ec499b54` ancestors of handed HEAD | **NO** — the row's own work was absent |

So this was not a divergent lineage but a clean **110-commit fast-forward
deficit**: the worktree did not contain the code it was sent to review. The
tree was clean (`git status --porcelain` → 0 lines, nothing of mine to lose),
so I fast-forwarded **my own branch only** — the shared checkout was never
touched — and re-checked:

```
$ git merge --ff-only 85c6f747
$ git log --oneline -1
85c6f747 TASK-383's premise was checked instead of specced …
85c6f747 ancestor YES · 687579bd ancestor YES · ec499b54 ancestor YES
```

Everything below is measured on `85c6f747`. **This is the third round on this
project handed a stale worktree; it is a dispatch defect, not a row defect, and
I attribute nothing to the row for it.**

---

## 1. The gate, reproduced in both halves — the load-bearing check

The dispatch says the round rests on this. I reproduced both halves from
scratch, against **identical pre-change code** (`a9e582a8` extracted twice into
the scratchpad), varying only whether `OKR.md` still carries its KR tables.

### Half A — gate BEFORE the deletion

```
$ pre/bin/perry-okr diff --root pre
  "records_not_in_the_file": [],
  "kinds": { "objective": 10, "kr": 38, "version": 3 },
  "identical": true,
  "every_line_and_cell_came_from_the_store": true
exit 0
```

**Byte-identical to the block the result quotes in its § 0**, including
`lines_from_store: 51` and all ten payload keys. 38 KR rows in the file, 38
`kind: kr` records in the store.

### Half B — same code, tables deleted, all 38 records still in the store

```
$ postdel/bin/perry-okr diff --root postdel
  "identical": true
  "every_line_and_cell_came_from_the_store": true
  "kinds": { "objective": 10, "version": 3 }        ← no `kr` key at all
  records_not_in_the_file: 38   (all 38 of kind `kr`)
  lines_from_store: 13
exit 0
```

**Confirmed exactly as the result claims.** Both booleans still `true`, exit
still 0, `kr` gone from `kinds`, 38 records stranded. The two keys and the exit
code are wholly insensitive to `records_not_in_the_file` being non-empty: the
gate is **structurally blind to a record with no line to land in**. A round that
gated second would have quoted two `true`s that said nothing whatever about the
38 rows it was deleting.

### Is the round's ordering claim established, or merely asserted?

**Established — and by the payload's own content, not by trust.** Temporal
ordering is not auditable from git in principle, but it does not need to be:
the block the result quotes carries `kinds.kr = 38`, `lines_from_store: 51` and
`records_not_in_the_file: []`, and Half B proves a post-deletion run **cannot
produce those values** — it yields `lines_from_store: 13`, no `kr` key, and 38
stranded records. The quoted gate output is a fingerprint of a tree with the
tables present. It could only have been produced before the deletion.

That is a genuinely good piece of work, and § 0.1 is the strongest section of
the result: it converts the spec's *prediction* of vacuity into a measured
demonstration.

### One thing the round did not say, which I record rather than charge

Under the **shipped** code the last remaining signal is also gone. `store_only_kinds`
excludes `kr` from `records_not_in_the_file`, so at `85c6f747`:

```
$ bin/perry-okr diff      → records_not_in_the_file: []   identical: true   exit 0
```

The old code at least *listed* the 38 stranded records while ignoring them in
its booleans; the shipped code does not list them either. The result discloses
the substance of this in § 4.1 and in `Doc`'s docstring, and it is the intended
consequence of `ADR-019`. Recorded for the next reader, charged to nothing.

---

## 2. Verification 2 — all 38 rows, my own enumeration

I did not read the result's table. I wrote an independent comparator
(`scratchpad/cmp_krs.py`) that hand-parses the **pre-deletion** `OKR.md` at
`a9e582a8` with a regex over table rows and **does not import
`perry_md_store`**, then field-compares it against
`perry-goals krs --level overall --version all --json` at `85c6f747`.

Key is `(version, objective heading, id)` — putting the objective heading in the
**key** rather than in the compared fields, so a KR reattached to the wrong
objective surfaces as a missing/extra key rather than a field diff.

```
rows parsed from OKR.md @ a9e582a8 : 38
rows rendered by perry-goals @ HEAD: 38
keys only in the FILE   : 0
keys only in the RENDER : 0
field comparisons: 152   MISMATCHES: 0
RESULT: ALL MATCH
```

**Verification 2 discharged.** All 38 rows are reproduced, field for field,
including the v2/v3 `O1-KR1` collision and the v3 Objective 3 re-pointing the
result flags in its § 2 note.

---

## 3. The three corrections, each verified independently

### Correction 1 — `_parse_krs` retires ZERO lines. The result CATCHES the spec's error.

Verified directly in `viewer/parsers.py` at `85c6f747`:

- `_parse_krs` is defined at **`viewer/parsers.py:2486`**.
- Caller 1 — **`viewer/parsers.py:2671`**, inside `_parse_okr_objectives`,
  guarded by `if stored_krs is None`.
- Caller 2 — **`viewer/parsers.py:2770`**, inside `parse_phase`, as
  `krs=_parse_krs(chunk)`. **Unconditional**: it sits in the `## Objective N`
  loop over a phase document with no guard of any kind, because phase files
  carry their own KR tables.
- `viewer/parsers.py:2763-2767` is a pre-existing comment saying exactly this.
- `viewer/parsers.py` is **not among the eleven files** `ec499b54` touches.

So the spec's *"retires `_parse_krs`, 26 lines"* is wrong, and **the result does
not repeat the error — it catches it** in F-3, measures 27 lines rather than 26,
names both call sites with line numbers, and quotes the pre-existing comment.
F-3 discharges the spec's own instruction (*"Report the measured number; do not
claim more"*). **Correct, and to the round's credit.**

### Correction 2 — `perry-goals list` is byte-identical before the change. The result mis-frames it mildly; the verdict does not move.

Measured, not reasoned about:

```
$ pre/bin/perry-goals list --level overall --root pre   → sha256 295f357c…2723
$ bin/perry-goals list --level overall                  → sha256 295f357c…2723
diff → *** BYTE-IDENTICAL ***
```

Identical sha256. All three properties § 3.4 cites are present in the **pre-change**
output: 19 KRs of 38, `O1-KR1` truncated at *"Non-`project` modes running on a
live track "*, and a `—` column. (In passing: § 3.4 says *"Metric / Target,
Stretch? and Deadline all print as `—`"*; the actual output carries **one** `—`
column, not three. Immaterial, and equally true on both sides.)

**My judgement.** The result does *not* claim `list` changed — it says the
command *"already existed"*, which is accurate. And the read-surface report's
question is about the surface a reader **now has**, so a pre-existing CLI
surface is legitimately in scope for the deliverable. What is mis-framed is
narrower: § 3.4 is headed *"The negative finding inside the positive verdict"*
and says the command *"gives a materially worse view than the file did"* — a
sentence that invites the reading that this row degraded `list`. It did not.
What the row removed is the **fallback**: before, a reader who found `list`
inadequate could open the file; now they cannot. That is a real cost of the row,
but it belongs in § 3.3 (where the file-reader loss is properly argued), and the
section should have stated the byte-identity outright.

**Does it change the POSITIVE-qualified verdict? No — and if anything it should
make it more positive**, since the row costs nothing on `list` that was not
already true. This is an imprecision in an evidence file, which `review.md § 2`
routes to *file a row*, never to a FAIL. It is not why this round fails.

### Correction 3 — the schema key IS scoped to the OKR KR table alone. Verified.

`6032bb45` is a 4-line diff on `schema/state-schema.json` (two real keys:
`optional` and `optional_note`). I parsed the schema and enumerated **every**
table spec in the file:

| file | table | `under` | `optional` |
|---|---|---|---|
| board | 0–3 | `^P[012]`, Intake, User Input Queue, Cadence | — |
| board | 4 | `^Top risks` | true (**pre-existing**) |
| **okr** | **0** | **`^(Objective\|目标) \d+`** | **true ← the new key** |
| okr | 1 | `^Commitments` | — (untouched) |
| phase | 0 | `^(Objective\|目标) \d+` | true (**pre-existing**) |

Before `6032bb45` there were **2** `"optional": true` in the file; after, **3**.
The added one sits in `files[okr].tables[0]`, immediately above the `Commitments`
entry, which is unchanged. **Scoped to the OKR KR table alone — confirmed.** The
`optional_note` correctly distinguishes itself from `Commitments`' different
sense of optional.

The lint effect, measured on both sides rather than taken from the commit
message:

```
$ merged/bin/perry-lint --root merged       (at 687579bd, pre-fix)
  ⚠ perry/OKR.md [missing-table] no table found under /^(Objective|目标) \d+/
  0 error(s), 56 warning(s)
$ bin/perry-lint                            (at 85c6f747, post-fix)
  0 error(s), 55 warning(s)          ← the missing-table finding is gone
$ bin/perry-lint --templates                exit 0
```

**56 → 55, one key, correctly scoped. Correction 3 verified in full.**

---

## 4. The `ADR-015` tier-1 boundary — the argument EXISTS and is substantive

The spec's *What it must not do* 2 requires the boundary to be **argued** in the
report. It is, in § 3.5, and this is not a token paragraph.

**What the argument gets right**, and I verified the mechanism rather than
accepting it:

- Its central move is to refute the **spec's own framing**. The spec says *"after
  this row it is a tier-1 document whose KR half is a render"*; § 3.5 answers
  *"It is not"* — the KRs are **absent** from `OKR.md`, not rendered into it,
  because `perry_md_store.render` fills existing lines and never creates them.
  I confirmed this by running the write path (§ 6, constraint 5 below): `render
  --write` reports *0 line(s) changed, 131 unchanged* and leaves the file
  byte-identical. So `OKR.md` becomes a **smaller authored document**, not a
  half-projection, and the boundary holds more cleanly than the spec expected.
- It reads `ADR-015` correctly: the tier-1 rule is about whether hand editing is
  *legitimate*, and for everything the file still contains it is.
- It then names, honestly, exactly where the argument **fails** — writing — and
  files it as F-2 rather than leaving it to be discovered. It ties that to
  `ADR-015`'s own cost note (*"The tool path must cover what hand editing
  covered"*) and shows `perry-okr write --from-file` now refuses by construction.

That is a real argument that engages the ADR's text and locates its break
precisely. **The spec's requirement is discharged.**

**Where it stops one step short**, which I record as a finding rather than a
FAIL. `ADR-015 § What would reopen this` trigger 1 reads:

> "The tool path fails to cover something hand editing covered, and the refusal
> becomes an obstruction rather than a guard."

F-2 **satisfies that trigger on its own evidence** — and `ADR-015` carries an
in-document precedent for what should follow: its `## Changes` entry of
2026-09-08, where `ADR-019` narrowed the `.perry/config.md` entry, recorded with
the reason *"the contradiction is only visible from this side if this file says
so."* TASK-236 narrows the `OKR.md` entry in precisely the same way — hand
editing a key result is no longer possible — and **`ADR-015` carries no entry for
it**. The result neither amends the ADR (it is not its file to amend) nor files
an ask. Graded **ROW**: a decision record that misstates the live system is a
documentation defect with its own ID (`review.md § 2`), not a V4 FAIL.

---

## 5. Mutations — mine, not the result's five

Every mutation below was planted by me. Product files were restored with
`git checkout --` and **every restore verified against `git diff --exit-code`
plus a sha256 compared to the pre-round baseline** — never against bytes I
snapshotted myself. `__pycache__` was cleared and a full second allowed to pass
before each run.

Baseline sha256, taken on a clean tree before any mutation:

```
14fa2cc8…abe0  perry/okr.jsonl
edf8376c…3cee  perry/OKR.md
5ce5f7ee…6b5d  bin/perry_md_store.py
```

| # | Mutation | File | Result | Named test(s) / tool behaviour | Restore |
|---|---|---|---|---|---|
| **MX-1** | one KR's `objective_id` → `O-99` (orphan) | `perry/okr.jsonl` | **RED (test) / but tool exit 0** | `test_okr_krs_render.TestTheShippedOkr.test_every_stored_kr_reaches_the_render` names `('v3: 2026-09-01','O5-KR4')`. **`perry-goals krs` exit 0, 37 rows, footer "37 key result(s)"** | `git diff --exit-code` clean; sha `14fa2cc8…abe0` ✔ |
| **MX-2** | `store_only_kinds=("kr",)` → `("kr","version")` | `bin/perry_md_store.py:979` | **RED — 1 test** | `test_md_store.TestAHandEditIsReportedAndNeitherHonouredNorOverwritten.test_a_deleted_line_is_reported_rather_than_dropped` — exactly the control § 5.1 claims it is | `git diff --exit-code` clean; sha `5ce5f7ee…6b5d` ✔ |
| **MX-3** | **anti-vacuity re-run.** all 38 `kind: kr` deleted from the LIVE store | `perry/okr.jsonl` | **RED — 4 tests** | `test_okr_krs_render.TestTheShippedOkr.test_every_stored_kr_reaches_the_render`; `test_md_store.TestTheObjectiveIdIsMinted.test_every_kr_carries_the_id_of_the_objective_above_it`; `.test_only_the_two_id_fields_move`; `test_md_store.TestTheReadContractsDoNotMove.test_the_shipped_reader_gets_every_kr_from_the_store` | `git diff --exit-code` clean; sha `14fa2cc8…abe0`, 38 records ✔ |
| **MX-4** | a KR table row hand-written back under `### Objective 1` | `perry/OKR.md:105` | **RED — 6 tests** | `test_okr_krs_render.TestTheShippedOkr.test_the_shipped_okr_md_carries_no_kr_table_rows` + 5 in `test_store_drift` | `git diff --exit-code` clean; sha `edf8376c…3cee` ✔ |
| **MX-5** | a KR's stored `metric` → `99 of 3 modes live` | `perry/okr.jsonl` | **GREEN — nothing catches it** | `perry-okr diff` exit 0 · `verify` exit 0 · `perry-lint` 0 errors · `test_okr_krs_render` OK · `test_md_store` OK · `test_store_drift` OK | `git diff --exit-code` clean; sha `14fa2cc8…abe0` ✔ |

**Final tree state: `git status --porcelain` → 0 lines. No mutation residue.**

MX-3 reproduces the result's M4 exactly — the same four tests, by name. The
anti-vacuity check is real. MX-2 and MX-4 confirm two of the round's structural
claims by breaking them, and both were caught.

### MX-5 came back GREEN — reported, and NOT charged

`review.md § 2` rule 2 says a green mutation is a finding either way, so here it
is with its grading. A corrupted **value** in the live store is caught by
nothing. I measured what the same corruption did *before* the row:

```
pre tree (KR tables still in OKR.md), same corrupted metric:
  perry-okr diff   → exit 1, identical: false,
                     cells_the_store_and_the_file_disagree_on: [ …/O1-KR1, "Metric / Target" ]
  perry-okr verify → exit 1, drift_count: 1
```

So the row **did** remove a detection capability that demonstrably existed.
**I do not charge it.** It is the direct and inherent consequence of `ADR-019`'s
single-copy trade — with the duplicate gone, a wrong stored value is no longer
*drift*, it is indistinguishable from an authored one — and the result discloses
it plainly in § 4.1 and in `Doc`'s docstring. A reader still sees all 38 rows;
one of them is wrong. That is the trade `ADR-019` chose with its eyes open.

**MX-1 is a different animal, and it is why this round fails.**

---

## 6. Finding — the render silently DROPS key results and reports a confident count

**This is the FAIL.** It is new code, in this row's central deliverable, on an
input the row itself forces users to produce.

### The behaviour

`bin/perry-goals:2943-2945` joins KRs to objectives by iterating **objectives**
and selecting the KRs that match:

```python
for obj in [o for o in objectives if o.get("version") == version]:
    rows = [k for k in krs
            if k.get("version") == version
            and k.get("objective_id") == obj.get("id")]
```

A `kind: kr` record whose `(version, objective_id)` pair matches **no** objective
is never visited by any iteration, so it is never emitted. Nothing afterwards
compares the number of KRs emitted against the number of `kr` records in scope.
`bin/perry-goals:3023` then prints the surviving count as fact.

### Enumerated, not sampled — `review.md § 2` rule 1

I swept single-field corruptions of one `kind: kr` record against an isolated
copy of `85c6f747` (`scratchpad/sweep.py`), baseline included as a control:

| variant on one `kr` record | exit | KR rows | |
|---|---|---|---|
| baseline (untouched) | 0 | 38 | control — renders all 38 |
| `objective_id` → `O-99` (orphan) | 0 | 37 | **SILENT DROP** |
| `objective_id` → `""` | 0 | 37 | **SILENT DROP** |
| `objective_id` key removed | 0 | 37 | **SILENT DROP** |
| `version` → unknown block | 0 | 37 | **SILENT DROP** |
| `id` → `""` | 0 | 37 | **SILENT DROP** |
| `objective` heading → garbage | 0 | 38 | renders all 38 (heading is not the join key) |
| `kind` → `"kr "` | 1 | 0 | REFUSED — correct |

**Five distinct user-producible corruptions drop a key result silently.** Only a
malformed `kind` refuses.

### No other tool notices

With one KR orphaned (`scratchpad/sweep2.py`):

```
perry-okr diff     exit=0   mentions NOTHING
perry-okr verify   exit=0   mentions NOTHING
perry-lint         exit=0   0 error(s), 55 warning(s)   — unchanged
perry-goals krs    exit=0   footer: "37 key result(s) under 10 objective(s) across 2 version block(s)."
```

### Why this fails the row

1. **It is new code from this row.** `overall_kr_model` is **absent** at
   `a9e582a8` and introduced by `ec499b54` (`+def overall_kr_model`, and the
   join at `+rows = [k for k in krs`). This is not a pre-existing weakness.
2. **It answers `review.md § 0` question 2 directly** — *"make a tool report a
   wrong answer to someone with no way to tell — a count, a verdict, a rendered
   surface"*. It is all three at once: a short table, a confident footer count,
   and no second copy left anywhere to contradict it.
3. **The triggering input is the only authoring path the row leaves.** The
   result's own F-2 establishes that hand-editing `okr.jsonl` is now the sole
   way to add or revise a KR. A typo'd or omitted `objective_id` in that hand
   edit deletes a key result from the only surface that shows it. This is not an
   exotic input; it is the documented workflow.
4. **It contradicts a load-bearing claim of the named deliverable.** § 3.2 claim
   5 of THE READ-SURFACE REPORT states:

   > "It refuses rather than printing a short table. … The failure mode this
   > project has actually paid for — `TASK-437`, where `perry-goals` published a
   > plausible number computed from 156 of 429 records — is a reader that drops
   > what it cannot read and prints the rest. **This one does not.**"

   It does, on five inputs, in the same tool, with the same shape — a plausible
   number computed from 37 of 38 records. `TASK-237` is gated on this report and
   is told to weigh it; it would be generalising from a claim that is false.
5. **`DESIGN-013 § 5.4` risk 3's bar is not met**: *the render has to be good
   enough that a human running one command sees what opening the file showed
   them.* On these inputs the human sees strictly fewer rows than the file held,
   and is told a number that agrees with what they were shown.

The repository's own state is protected by `TestTheShippedOkr.test_every_stored_kr_reaches_the_render`
(MX-1 proves it reddens) — but that guard covers **Perry's own `okr.jsonl` only**.
The shipped tool carries no equivalent for any other project, and `perry-lint`,
`perry-okr diff` and `perry-okr verify` are all silent.

**Not fixed, deliberately** — a reviewer who fixes loses the ability to judge.
For the record, the refusal machinery already exists four lines above
(`bin/perry-goals:2927-2931` raises `Refused` for an unknown `--version`); it is
simply not applied to the join.

---

## 7. The rest of the criteria, checked

- **`What it must not do` 1 (order)** — discharged. § 1 above.
- **`What it must not do` 2 (tier-1 boundary argued)** — discharged as an
  argument; one ROW-grade gap in § 4.
- **`What it must not do` 3 (`schema/state-schema.json`)** — `ec499b54` does not
  touch it; the later edit is `6032bb45`, authorised, one key, correctly scoped.
- **`What it must not do` 4 (`ARCHITECTURE.md § 2`)** — not edited. The result's
  § 8 reasoning is sound: `§2 › viewer/parsers.py` claims `OKR.md` parsing, which
  remains true.
- **`What it must not do` 5 (tables written back)** — verified by running the
  write path myself:

  ```
  $ bin/perry-okr render --write
  perry-okr: rewrote …/perry/OKR.md — 0 line(s) changed, 131 unchanged,
                                      from 51 stored record(s)
  sha256 before == sha256 after (edf8376c…3cee) · KR rows: 0 · git diff clean
  ```
  Guard 1 (render fills lines, never creates them) holds. MX-4 confirms the
  guard against a table returning by hand.
- **`Verification` 5 (the suite)** — `bash tests/run` on a clean tree at
  `85c6f747`: **128 modules · 3697 tests · 3 failed**. The three are the
  pre-existing ones, each **re-run alone** and still red, so none is
  order-dependent:
  - `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`
  - `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness`
  - `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`

  Nothing is attributed to them. `tests/run` also prints
  `✗ not in durations.json: test_contract_page_snippets.py` — the result's F-5,
  confirmed pre-existing and not this row's. The row's own module
  `test_okr_krs_render.py` passes alone (18 tests, OK).

## 8. What I did not check

- `viewer/` beyond the two `_parse_krs` call sites and the OKR arm — I did not
  audit the aiMark payload or `phase_key_results`.
- Any project other than this repository and my scratchpad copies: no adopted
  project, no Chinese-locale `OKR.md`, no project whose `OKR.md` still carries
  KR tables (the `scan_okr` residual the result names in § 7).
- Duplicate-key and absent-store refusals (§ 3.2 claim 5's other two limbs) — I
  tested the *malformed* limb only, which refused correctly.
- The 10 `objective` and 3 `version` records beyond their role as join targets.
- `perry-goals list`'s internals — I compared its output bytes, not its code.
- Windows paths; concurrency; any `--json` consumer downstream of `krs`.
- Whether `TASK-237` should proceed: on **reading**, the report's positive
  verdict is sound and I would not block it on § 3.3 or § 3.4. My FAIL is about
  the render dropping records, not about whether a CLI render can be read.

## 9. What would change my mind

- **On the FAIL**: a demonstration that a `kr` record cannot reach a state where
  its `(version, objective_id)` matches no objective — i.e. that some writer or
  validator rejects it on the way in. I found no such writer; F-2 says there is
  none, and `perry-lint` passed every corrupted store I built. Produce that
  gate and the finding collapses to a ROW.
- **On correction 2 / § 3.4**: nothing — it is byte-identical, measured twice.
- **On the tier-1 ROW**: an `ADR-015 § Changes` entry, or an open ask naming the
  KR authoring gap, landing anywhere in the repository. I searched and found
  neither.
- **On MX-5**: if `ADR-019` did not accept single-copy storage, or if § 4.1 had
  not disclosed the loss, MX-5 would be charged rather than recorded.

---

=== VERDICT ===
task: TASK-236
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-236-spec.md
checked: gate reproduced BOTH halves on identical pre-change code — before the
         deletion identical/every_line true with kinds.kr=38, after it both
         still true at exit 0 with kr absent and 38 records stranded, so the
         ordering claim is established by the payload's own fingerprint; all 38
         KR rows re-enumerated field by field by a comparator that does not
         import perry_md_store (152 comparisons, 0 mismatches); the three
         dispatch corrections each verified independently (_parse_krs retires
         zero and F-3 catches it; perry-goals list byte-identical, same sha256;
         the schema key scoped to files[okr].tables[0] alone, lint 56 -> 55);
         constraint 5 verified by running render --write (0 lines changed);
         five own mutations MX-1..MX-5 planted, all restores verified by
         git diff --exit-code and sha256; suite 128 modules / 3697 tests /
         3 pre-existing failures, each re-run alone
not-checked: adopted or non-migrated projects and the scan_okr residual; the
         zh-locale OKR.md; duplicate-key and absent-store refusals; viewer/
         beyond the two _parse_krs call sites; perry-goals list internals;
         downstream --json consumers; Windows paths; concurrency
proof: bin/perry-goals:2943-2945 joins KRs to objectives by iterating objectives
         and selecting `k.get("objective_id") == obj.get("id")`, with no
         residual check, so a kr record matching no objective is emitted
         nowhere; bin/perry-goals:3023 then prints the surviving count as fact.
         Five single-field corruptions of one kr record (objective_id orphaned,
         blanked, or removed; version unknown; id blanked) each render 37 of 38
         rows at exit 0 under the footer "37 key result(s)", while perry-okr
         diff, perry-okr verify and perry-lint all exit 0 and say nothing.
         overall_kr_model is absent at a9e582a8 and introduced by ec499b54, and
         F-2 establishes that hand-editing okr.jsonl is now the only way to
         author a KR, so this is new code failing on the workflow the row itself
         forces. It also falsifies § 3.2 claim 5 of the read-surface report —
         the named deliverable TASK-237 is gated on.
=== END VERDICT ===
