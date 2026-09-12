# TASK-236 — round 2, V4 fresh-context review

> Criteria: `perry/evidence/2026-09/TASK-236-spec.md` — its `## Bound`,
> `## What it must not do`, `## Verification` and `## Out of scope`, and
> nothing else.
> Under review: `991e3c32` (round 2, implemented inline by the PMO on `main`,
> reviewed by nobody before this round).
> Round 1's verdict: `perry/evidence/2026-09/TASK-236-round1-v4-review.md` —
> **FAIL**, one charged defect plus four ROW-grade findings.
> Reviewed in an isolated worktree. **This is the row's second FAIL.** See § 8.

---

## 0. Base check — the handed worktree was WRONG again, and was corrected first

The dispatch warned that four agents in a row were handed stale trees. Mine was
the fifth.

```
$ git log --oneline -1
583f024f Merge bin-contract-phase-a: DESIGN-016's thirteen closed rows …
$ git merge-base --is-ancestor 991e3c32 HEAD   → NOT an ancestor
```

Measured rather than guessed:

| | |
|---|---|
| handed HEAD | `583f024f` |
| `git rev-list --count 991e3c32..HEAD` | **0** |
| `git rev-list --count HEAD..991e3c32` | **118** |
| `git merge-base --is-ancestor HEAD 991e3c32` | **YES** — strict ancestor |
| `git status --porcelain` | 0 lines — nothing of mine to lose |

A clean **118-commit fast-forward deficit**, not a divergent lineage: the tree
did not contain the round-2 code it was sent to review. I fast-forwarded **my
own branch only** — the shared checkout was never touched — and re-verified:

```
$ git merge --ff-only 991e3c32
$ git log --oneline -1
991e3c32 TASK-236 round 2: the render refuses rather than printing a table short of the store
$ git merge-base --is-ancestor 991e3c32 HEAD   → ANCESTRY OK
```

Everything below is measured on `991e3c32`, which is main's tip and is itself
the round-2 commit. **This is the fifth consecutive stale-worktree dispatch on
this project. It is a dispatch defect, not a row defect, and I attribute
nothing to the row for it.**

### Mutation hygiene, stated once

**No file in the repository was modified at any point in this round.** Every
mutation below was planted on isolated `git archive` extractions in the
scratchpad (`r2rev/pre` at `991e3c32^`, `r2rev/post` at `991e3c32`), so the
"restore" for the repository is that there was never a write. Confirmed at the
end of the round:

```
$ git status --porcelain          → 0 lines
$ git diff 991e3c32 --stat        → empty
$ shasum -a 256 bin/perry-goals   → 66028ad9ae1d79b0…
$ shasum -a 256 perry/okr.jsonl   → 14fa2cc8b4a98218…   (round 1's baseline)
```

Within the scratch trees every mutated file was restored and verified by
sha256 against the bytes read before the mutation **and** re-verified by
re-running the module green; each table below carries its restore column.
`__pycache__` was cleared and a full second allowed to pass around every
source mutation.

---

## 1. The FAIL is NOT fixed. It is narrowed from five inputs to four.

**This is the finding, and it is the same defect round 1 charged, in the same
function, reachable by a single-field edit round 1 did not happen to sweep.**

### 1.1 The behaviour

`bin/perry-goals:2978-2979` computes the residual that makes the command
refuse:

```python
    stranded = [k for k in krs
                if k.get("version") in wanted and id(k) not in placed]
```

`wanted` is always a list of version strings the store actually holds
(`bin/perry-goals:2923-2937`; `order` is built only from records whose
`version` is truthy). So for a `kr` record whose `version` is **absent or
blank**, `k.get("version") in wanted` is `None in wanted` or `"" in wanted` —
**always `False`**. The record is never placed by the join above and is never
counted as stranded below. It is emitted nowhere, nothing refuses, and
`bin/perry-goals:3065` prints the survivors' count as fact.

That is round 1's FAIL sentence with one word changed.

### 1.2 Is such a record valid input? Yes — the store's own validator accepts it.

`bin/perry_md_store.py:559 validate_records` type-checks only the fields that
are **present** (`for field, value in rec.items()`), and `STORED["kr"]`
(`bin/perry_md_store.py:246`) is a tuple of permitted names, not required ones.
A `kind: kr` record with no `version` key, or with `"version": ""`, is returned
in `good` with no finding. `perry-lint` reports 0 errors on it.

The spec's own F-2 (upheld by round 1) establishes that **hand-editing
`okr.jsonl` is now the only way to author a key result.** Omitting or blanking
`version` in a hand-written JSONL record is at least as ordinary a slip as
typo'ing `objective_id`, which round 2 treats as the motivating input.

### 1.3 Proved on a FIXTURE project with the shipped tool, not on Perry's store

Perry's own `okr.jsonl` is guarded by
`test_okr_krs_render.TestTheShippedOkr.test_every_stored_kr_reaches_the_render`,
which does redden (§ 4, A4). That guard covers **this repository only**. The
shipped tool is what every other project runs, so I built the fixture from
`tests/test_okr_krs_render.py`'s own `STORE` (5 KR records, 2 version blocks)
and ran `991e3c32`'s `bin/perry-goals` against it:

| fixture store (5 kr records) | invocation | exit | rendered | footer |
|---|---|---|---|---|
| healthy (control) | `--version all` | 0 | 5 of 5 | `5 key result(s) under 3 objective(s) across 2 version block(s).` |
| one kr's `objective_id` → `O-99` | `--version all` | **1** | — | **REFUSED** ← round 2's fix works |
| one kr's **`version` key REMOVED** | `--version all` | **0** | **4 of 5** | **`4 key result(s) under 3 objective(s) across 2 version block(s).`** |
| one kr's **`version` → `""`** | `--version all` | **0** | **4 of 5** | **`4 key result(s) under 3 objective(s) across 2 version block(s).`** |
| both current-block krs `version` → `""` | *(default)* | **0** | **0 of 2** | **`0 key result(s) under 1 objective(s) across 1 version block(s).`** |

The last row is the sharpest: the command reports an **entirely empty current
version block as a fact**, at exit 0, while the store holds two key results
for it.

### 1.4 Every other gate is green, exactly as in round 1

Measured on a scratch copy of the live store at `991e3c32` with one `kr`'s
`version` key removed (target `O5-KR4`):

```
perry-goals krs --level overall --version all   exit 0   "37 key result(s) …"
perry-goals krs --level overall (default)       exit 0   "18 key result(s) …"
perry-goals krs … --json                        exit 0   0 entries for that KR
perry-okr diff     exit 0   identical: true
                            every_line_and_cell_came_from_the_store: true
                            records_not_in_the_file: []
perry-okr verify   exit 0   drift_count: 0, byte_identical: true
perry-lint         exit 0   0 error(s), 55 warning(s)
```

**A key result disappears from the only surface that carries it and every gate
stays green.** That is `review.md § 0`'s second question — a tool reporting a
wrong answer to someone with no way to tell — answered yes, in new code this
row added, on the workflow the row itself forces.

### 1.5 It falsifies the named deliverable, still

`TASK-236-result.md § 3.2` claim 5 of THE READ-SURFACE REPORT reads:

> "It refuses rather than printing a short table. … The failure mode this
> project has actually paid for — `TASK-437`, where `perry-goals` published a
> plausible number computed from 156 of 429 records — is a reader that drops
> what it cannot read and prints the rest. **This one does not.**"

It still does — 4 of 5, or 37 of 38, or 0 of 2. `TASK-237` is gated on this
report and is told to weigh it, and it would be generalising from a claim that
is false. Round 1 charged this; round 2 did not correct the sentence.

---

## 2. The five corruptions, each reproduced on both trees — I did not take the table on trust

Planted by me on `r2rev/pre` (`991e3c32^`) and `r2rev/post` (`991e3c32`),
same record (`O5-KR4`, the last `kind: kr` in the live store), store restored
and sha256-verified after every single run.

`perry-goals krs --level overall --version all`:

| corruption (one `kind: kr` record) | PRE `991e3c32^` | POST `991e3c32` | restore |
|---|---|---|---|
| baseline (control, untouched) | exit 0 · 38 key result(s) | exit 0 · 38 key result(s) | OK / OK |
| C1 `objective_id` → `O-99` (orphan) | exit 0 · **37** key result(s) | **exit 1 · REFUSED** | OK / OK |
| C2 `objective_id` → `""` (blank) | exit 0 · **37** key result(s) | **exit 1 · REFUSED** | OK / OK |
| C3 `objective_id` key REMOVED | exit 0 · **37** key result(s) | **exit 1 · REFUSED** | OK / OK |
| C4 `version` → `v9: nonesuch` (unknown block) | exit 0 · **37** key result(s) | **exit 1 · REFUSED** | OK / OK |
| C5 `id` → `""` (blank id) ALONE | exit 0 · **38** key result(s) | exit 0 · **38** key result(s) | OK / OK |
| C5′ blank `id` **AND** `objective_id` → `O-99` | exit 0 · **37** key result(s) | **exit 1 · REFUSED** | OK / OK |
| **V1 `version` → `""`** | exit 0 · **37** | **exit 0 · 37 — NOT REFUSED** | OK / OK |
| **V2 `version` key REMOVED** | exit 0 · **37** | **exit 0 · 37 — NOT REFUSED** | OK / OK |
| **V3 `version` → `""` AND `objective_id` → `O-99`** | exit 0 · **37** | **exit 0 · 37 — NOT REFUSED** | OK / OK |

**Four of round 2's five claimed corruptions reproduce exactly as claimed.**
C1–C4 go from 37-of-38-at-exit-0 to refused at exit 1. That part of the work is
real and I verified it rather than reading it.

**Two corrections to round 2's § 2 table, both ROW-grade:**

- **C5 is not an independent corruption.** A blank `id` **alone** drops
  nothing — 38 rows at exit 0 on **both** trees, the record renders with an
  empty id cell. Round 2's fifth row is labelled "blank `id` + orphaned", which
  is C1 with a cosmetic extra; the refusal fires because of the orphaning. So
  round 2's table claims five closed inputs and has closed **four**. (Round 1's
  own sweep row `id → ""` → "37 rows, SILENT DROP" is likewise wrong; I
  measured 38 on the pre-change tree. Round 2 inherited the error.)
- **V3 shows the ordering of the two conditions is what matters.** Orphan a
  record *and* blank its version and the refusal that fires for the orphan
  alone stops firing, because the version test is `and`-ed first. A user
  hand-editing a record is as likely to get both wrong as one.

---

## 3. Is refusing the right answer? Yes — and I would grade report-and-continue worse

The dispatch asks me to judge this rather than assume it. My judgement:
**refusing is proportionate, and round 2's precedent argument transfers.**

**The precedent is real, and it is this command's own.** I read `cmd_krs` and
`overall_kr_model` rather than the quotation. Refusal is already the
established posture for four separate conditions in the same code path — a
store that does not parse as JSONL, badly typed records, a duplicate
`(version, objective, id)` key, an absent store, and an unknown `--version`
(`bin/perry-goals:2898-2935`). Each refuses at exit 1 and names the cause.
Adding a fifth refusal is consistency, not a new rule; **report-and-continue
would make this one command hold two rules** — refusing for a record it cannot
type and continuing for a record it cannot place — and the second is the more
dangerous of the two, because a badly typed record at least announces itself to
`perry-lint`.

**Proportionality: "partially useful" is the wrong frame after `ADR-019`.** The
objection is that a corrupted store now makes the whole command unusable rather
than partially useful. That would carry weight if a fallback existed. It does
not: this row deleted the duplicate, so the render is the **only** surface that
carries a key result. A partial table from a sole-copy surface is not "partly
useful" to the reader — it is indistinguishable from the store genuinely
holding fewer key results, which is precisely `TASK-437`'s shape and precisely
what `DESIGN-013 § 5.4` risk 3 forbids ("a human running one command sees what
opening the file showed them").

**The refusal is actionable, which is what makes it proportionate rather than
merely safe.** I read the message it emits: it names the count, names each
record by id (with a `<no id, version …>` placeholder), says the store is where
it is fixed, tells the user what to do (give it an `objective_id` that exists,
or give the objective a record), and names the gate that cannot see the problem.
The user is not stranded; they are handed a one-line edit to a JSONL file they
already hand-edit. A refusal that says "something is wrong" would be
disproportionate. This one does not.

**The one thing I would have argued for and do not charge:** a `--json`
consumer gets exit 1 and no payload, where a partial payload plus a populated
`errors` key would serve a programmatic reader better. That is a design
preference, not a defect, and the exit code is honest either way.

**So the defect is not that it refuses. It is that it does not refuse on one of
the five inputs.** Had round 2 chosen report-and-continue I would have graded
that a FAIL on the same criterion.

---

## 4. The version scoping — correct in the direction round 2 defends, wrong in the other

Round 2 claims an unscoped residual would refuse every correct two-version
store, citing M2. **I planted M2 myself rather than believe it.** Mutation of
`bin/perry-goals` only; the store was uncorrupted throughout.

| `bin/perry-goals` | no `--version` (current block) | `--version all` | restore |
|---|---|---|---|
| **as shipped** (scoped) | exit 0 · 19 key result(s) | exit 0 · 38 key result(s) | — |
| **M2 mutant** (`and k.get("version") in wanted` removed) | **exit 1 · REFUSED — "19 key result(s) … belong to no objective"** | exit 0 · 38 key result(s) | sha `66028ad9…` ✔ |

**M2's claim is verified.** Without the scoping, the default invocation refuses
on a perfectly correct store, because the 19 v2-block records are out of scope
rather than orphaned. The scoping is load-bearing, and round 2 is right that a
naive residual is not the fix.

Confirmed in the other direction too, on the fixture — the scoping correctly
declines to over-report:

| fixture store | default (current v2 only) | `--version all` |
|---|---|---|
| healthy | exit 0 · 2 rendered | exit 0 · 5 rendered |
| orphan in the **old** (v1) block only | exit 0 · 2 rendered — correctly silent | **exit 1 · REFUSED** |
| blank `version` on a current-block kr | **exit 0 · 0 rendered** | **exit 0 · 3 of 5** |

Rows 1 and 2 are the scoping working. **Row 3 is the FAIL**: the same narrowing
that correctly excludes a known-but-unwanted version block also excludes a
record that has **no** version block at all — and a record with no version is
not out of scope, it is unplaceable.

**The two are not in tension, which is what makes this chargeable rather than a
trade-off.** A record is legitimately out of scope only when its version is a
version the store actually holds and the user did not ask for. Blank, absent,
or unknown is a different case, and `order` already distinguishes it — C4
(unknown version) refuses precisely because a truthy unknown version
self-registers in `order` and therefore lands in `wanted` under `--version
all`. Only the falsy case escapes. Round 2 reasoned about one boundary of its
own narrowing and not the other.

---

## 5. Anti-vacuity — the class CAN fail, verified by making the refusal unconditional

The dispatch asks me to confirm the anti-vacuity half is not decorative.
Mutation: `stranded = [k for k in krs if …]` → `stranded = list(krs)`, so the
refusal fires on every store including a healthy one.

```
A3 — refusal fires unconditionally
  Ran 26 tests | FAILED (failures=13)
```

**Both named anti-vacuity tests redden**, plus eleven others:

- `test_a_healthy_store_still_renders` ← named in round 2 § 3
- `test_a_narrowed_version_does_not_strand_the_other_block` ← named in round 2 § 3
- `test_every_stored_kr_reaches_the_render`, `test_version_all_renders_every_declared_kr`,
  `test_the_default_is_the_current_version_only`, `test_one_version_can_be_named`,
  `test_the_refusal_names_how_many`, `test_the_markdown_render_prints_every_kr_whole`,
  `test_a_corrupted_kr_field_reddens`, `test_a_deleted_kr_record_reddens`,
  `test_a_kr_reattached_to_the_wrong_objective_reddens`,
  `test_the_same_kr_id_in_two_versions_is_two_rows`,
  `test_a_blank_cell_renders_as_a_dash_and_not_as_the_word_none`

Restore verified (sha `66028ad9…`), module re-run green afterwards.
**Round 2's anti-vacuity claim is true.** The guard is not one that passes
whatever the code does.

**What the class does not cover, and it is the hole.** All eight new tests
parameterise `objective_id` (unknown / blank / missing) or an **unknown**
`version` string. **None supplies a record with an absent or blank `version`.**
The class is a faithful enumeration of round 1's list, and round 1's list was
one input short — which is `review.md § 2` rule 1 exactly: the round enumerated
the instances it was handed rather than the category ("a `kr` record the join
cannot place").

---

## 6. Mutation table — every restore verified

Scratch-tree mutations; the repository was never written to (§ 0).

| # | Mutation | File | Result | Restore |
|---|---|---|---|---|
| **A1** | C1–C5, V1–V3 store corruptions, ×2 trees (20 runs) | `perry/okr.jsonl` (scratch) | § 2's table — 4 closed, 3 still silent | sha256 match, every run ✔ |
| **A2 (M2)** | version scoping removed from the residual | `bin/perry-goals:2978-2979` (scratch) | **RED** — a correct store refuses on the default invocation (19 stranded) | sha `66028ad9…` ✔ |
| **A3** | refusal made unconditional (`stranded = list(krs)`) | `bin/perry-goals:2978-2979` (scratch) | **RED — 13 tests**, incl. both named anti-vacuity tests | sha `66028ad9…` ✔, module green after |
| **A4** | `version` key removed / blanked on a live-store record | `perry/okr.jsonl` (scratch) | **RED — Perry's own guards only**: `test_every_stored_kr_reaches_the_render`, `test_store_drift`, 1–4 in `test_md_store`. **The shipped tool does not refuse** (§ 1.3) | sha `14fa2cc8…` ✔ |
| **A5** | fixture project, `version` removed / blanked | fixture (temp dirs) | **GREEN — nothing catches it.** 4 of 5 at exit 0 | temp dirs deleted |

### A5 came back GREEN, and it is the charged finding

`review.md § 2` rule 2: a green mutation is a finding either way. This one is
both — the guard does not work **and** no test covers it. A4 shows Perry's own
repository is protected by a repo-specific live-state test; A5 shows every
other project is not. That is the same asymmetry round 1 named in its § 6 final
paragraph, on a new input, after the round that was supposed to close it.

---

## 7. What round 2 did NOT change — both dispositions judged

**MX-5 (a corrupted `metric` VALUE is caught by nothing) — left uncharged.
I agree, and I would have made the same call.** It is the direct consequence of
a recorded architectural decision: `ADR-019` deleted the duplicate copy, and
once there is one copy a wrong stored value is not *drift*, it is
indistinguishable from an authored one. It is disclosed in the original
result's § 4.1 and in `Doc`'s docstring, round 1 measured that the pre-change
tree did catch it, and the reader still sees **all 38 rows** with the count
correct. Charging it would be charging `ADR-019`, not this row. It is also a
materially different class from the charged finding: MX-5 shows the reader one
wrong value; § 1 hides a key result and misreports the total. **Correct
disposition.**

**Round 1's `ADR-015` ROW finding — left to the goals lane. Right not to fix,
but the deferral is not a filing.** `review.md § 2` routes a decision record
that misstates the live system to *file a row*, never to a FAIL, so round 2 was
right not to touch it and I do not charge it. But I searched
`perry/asks.jsonl` (27 rows) and found **no open ask naming the KR-authoring
gap, and no `ADR-015 § Changes` entry**. Round 1 graded it ROW, and § 6's
bargain is that "a row that was filed is not a round that was spent" — nothing
was filed. Saying it "belongs to the goals lane" assigns an owner; it does not
discharge the grade. **Re-reported here, still ROW-grade**, and it should be
filed alongside the ask § 8 requires rather than deferred a third time.

---

## 8. § 6 — this is the second FAIL. The next step is an ask, not a round 3.

Stating it plainly as the dispatch requires: **`TASK-236` now has two recorded
V4 FAILs, and `review.md § 6` forbids a third round.**
`perry-lint --reviews` will report `review-rounds-exhausted` until an open ask
in `asks.jsonl` names this row in `blocks`. Running round 3 anyway does not
clear it.

The two FAILs are the same shape one step to the left, which § 6 says is the
signature of a fork nobody has taken. The fork is **where the "this record
cannot be placed" judgement lives**, and both readings are defensible applied
consistently:

- **Reading A — the render owns it.** Fix `bin/perry-goals:2978-2979` so a
  record is out of scope only when its `version` is a version the store
  *holds* and the user did not ask for; blank, absent or unknown is stranded
  and refuses. Smallest change, preserves M2, closes the render. Leaves
  `perry-okr diff`, `verify` and `perry-lint` silent on the same record, so
  "every gate green" stays true for every other consumer.
- **Reading B — the store owns it.** Make `version` (and `objective_id`) a
  **required** field for `kind: kr` in `bin/perry_md_store.py:559
  validate_records`. Then every reader refuses at once and `perry-lint` names
  the record, which is what kills the "every gate is green" property that made
  both FAILs dangerous. But it changes the store contract for every consumer
  and may redden existing or adopted stores, and `STORED` currently encodes
  permitted fields rather than required ones — a real migration question.

**My recommendation: B, with A as the immediate stopgap** — B addresses the
class (`review.md § 2` rule 1: enumerate the category, which here is "a `kr`
record no reader can place", not "a `kr` record this render cannot place"),
while A alone fixes the one surface and leaves the next reader to rediscover
it. What is already true: A is a one-expression change and demonstrably does
not conflict with M2 (§ 4); B touches no file this row is forbidden to touch,
but does change a contract, and `schema/state-schema.json` is on
`.perry/hook.md § High-stakes operations` if the requiredness has to be
declared there.

```
"$PERRY_HOME/bin/perry-task" ask \
  --needed "TASK-236: a kr record with no `version` is placeable by nothing and
            silently dropped. A) fix the render's residual only, or B) make
            `version`/`objective_id` required in md_store.validate_records so
            every reader and perry-lint refuse. Recommend B with A as stopgap." \
  --blocks TASK-236
```

---

## 9. The rest of the criteria, re-checked rather than inherited

Round 1's PASSes narrow where I looked last, not first (`review.md § 2` rule 3).

- **`Verification` 5 (the suite)** — `bash tests/run` on a clean tree at
  `991e3c32`: **128 modules · 3711 tests · 116.2s · 3 failed.** The three are
  the pre-existing set, named:
  - `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`
  - `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness`
  - `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`

  **Nothing is attributed to them.** No new red; round 2's 8 tests pass. Tree
  guard: *"nothing under …/agent-a9161167facb882ed moved"*. The suite grew from
  3697 (round 1) to 3711 — +14, of which round 2 contributes 8.
- **`What it must not do` 3 (`schema/state-schema.json`)** — `991e3c32` does
  not touch it. Confirmed against the commit's file list (7 files).
- **`What it must not do` 4 (`ARCHITECTURE.md § 2`)** — not touched by
  `991e3c32`.
- **`What it must not do` 5 (tables not written back)** — unchanged by round 2;
  round 1 verified it by running `render --write`. I did not re-run it.
- **`Verification` 3 (mutation)** — discharged: § 5's A3 and § 6's A2 both
  redden named tests, and `test_a_corrupted_kr_field_reddens` /
  `test_a_deleted_kr_record_reddens` exist and redden.
- **`Verification` 4 (anti-vacuity)** — discharged, § 5.
- **`Bound`** — the 38/38 enumeration is round 1's, verified there by an
  independent comparator with 0 mismatches. I re-derived the counts (38 `kr`
  records on both trees) but did not re-run the field-by-field comparison.

---

## 10. What I did not check

- **The 38-row field-by-field re-enumeration.** Round 1 did it with an
  independent comparator (152 comparisons, 0 mismatches); I verified record
  counts and the render's ids, not every cell.
- **`perry-okr render --write`** — not re-run this round; round 2 did not touch
  that path.
- **The gate's two halves (`perry-okr diff` before/after deletion)** — round 1
  reproduced both on identical pre-change code. Not re-derived.
- **`viewer/parsers.py`** and the `_parse_krs` measurement — round 1's F-3
  finding accepted, not re-measured.
- **Any project other than this repository, my two scratch extractions and the
  temp fixtures** — no adopted project, no zh-locale `OKR.md`, no project whose
  `OKR.md` still carries KR tables.
- **`--level` values other than `overall`**, and `perry-goals list`.
- **Downstream `--json` consumers** of `krs` beyond parsing the payload myself.
- **Duplicate-key and absent-store refusals** — covered by existing tests I ran
  but did not mutate.
- **Windows paths; concurrency.**
- **Whether `TASK-237` should proceed** — on reading, the read-surface report's
  positive verdict is sound and I would not block it on § 3.3 or § 3.4. My FAIL
  is that § 3.2 claim 5 is still factually false, not that a CLI render is
  unreadable.
- **`.perry/events.jsonl`, `perry/BOARD.md`, `perry/tasks.jsonl`, the journal** —
  the commit's bookkeeping, not product.

## 11. What would change my mind

- **On the FAIL**: a demonstration that a `kr` record cannot reach a state where
  its `version` is absent or blank — i.e. some writer or validator rejects it on
  the way in. I looked: `validate_records` accepts it (§ 1.2), `perry-lint`
  reports 0 errors on it, and F-2 establishes hand-editing is the only
  authoring path. Produce that gate and this collapses to a ROW.
  Alternatively: show that `--version all` is not supposed to mean "every key
  result in the store", in which case the footer's wording is the defect
  instead.
- **On the C5 correction**: nothing — measured on both trees, blank `id` alone
  renders 38 of 38.
- **On refusing being proportionate**: a named consumer that must keep working
  against a partially corrupt store and has no way to fix it. I found none; the
  store is hand-edited by the same person running the command.
- **On the M2 verification**: nothing — I planted the mutant and a correct store
  refused.
- **On the `ADR-015` ROW**: an `ADR-015 § Changes` entry or an open ask naming
  the KR-authoring gap, landing anywhere in the repository. I searched
  `asks.jsonl`'s 27 rows and found neither.
- **On MX-5 staying uncharged**: if `ADR-019` had not accepted single-copy
  storage, or if the loss were undisclosed.

---

=== VERDICT ===
task: TASK-236
rung: V4
result: FAIL
grade: FAIL — Verification 2, every one of the stored KR records reachable
         through `perry-goals`, together with Deliverable 2's `DESIGN-013
         § 5.4` risk 3 bar (a human running one command sees what opening the
         file showed them). Stated explicitly rather than left to § 3's
         conservative default: this defect answers `review.md § 0`'s second
         question and it fails the row.
criteria: perry/evidence/2026-09/TASK-236-spec.md
checked: base was 118 commits stale and was fast-forwarded to 991e3c32 before
         anything (fifth such dispatch); all five corruptions round 1 named
         re-planted by me on isolated extractions of 991e3c32^ and 991e3c32 and
         C1-C4 confirmed to go from 37-of-38-at-exit-0 to refused at exit 1;
         round 2's M2 scoping claim verified by planting the unscoped residual
         (a CORRECT store then refuses on the default invocation, 19 stranded),
         and the scoping confirmed correct in the over-report direction (an
         orphan in an unwanted version block does not refuse the current-block
         render); anti-vacuity verified by making the refusal unconditional —
         13 tests redden including both named anti-vacuity tests; the finding
         reproduced on a fixture project with the shipped tool, not only on
         Perry's own store; suite 128 modules / 3711 tests / 3 pre-existing
         failures named; no repository file written at any point (git diff vs
         991e3c32 empty, sha256 of bin/perry-goals and perry/okr.jsonl
         unchanged), every scratch mutation restored and sha256-verified
not-checked: the 38-row field-by-field re-enumeration and the diff gate's two
         halves (round 1's, accepted); perry-okr render --write; viewer/ and the
         _parse_krs measurement; adopted or zh-locale projects; --level values
         other than overall; perry-goals list; downstream --json consumers;
         Windows paths; concurrency
proof: bin/perry-goals:2979 scopes the residual with
         `if k.get("version") in wanted and id(k) not in placed`, and `wanted`
         only ever holds version strings the store carries (order is built at
         bin/perry-goals:2923-2925 from records whose `version` is truthy), so
         for a kr record whose `version` is absent or blank the test is
         `None in wanted` / `"" in wanted` — always False. The record is placed
         by no objective and counted by no residual, so it is emitted nowhere
         and bin/perry-goals:3065 prints the survivors' count as fact. Input:
         one `kind: kr` record with its `version` key removed, or set to "".
         bin/perry_md_store.py:559 validate_records accepts it (it type-checks
         only fields present; STORED["kr"] at :246 lists permitted, not required,
         fields) and perry-lint reports 0 errors. Measured on the fixture from
         tests/test_okr_krs_render.py's own STORE with 991e3c32's shipped
         binary: 4 of 5 key results rendered at exit 0 under the footer
         "4 key result(s) under 3 objective(s) across 2 version block(s)."; with
         both current-block records blanked, "0 key result(s) under 1
         objective(s) across 1 version block(s)." at exit 0. On a scratch copy
         of the live store, 37 of 38 at exit 0 while perry-okr diff reports
         identical:true AND every_line_and_cell_came_from_the_store:true,
         perry-okr verify reports drift_count 0, and perry-lint reports 0
         errors. This is round 1's charged defect, in the same function, on an
         input its five-variant sweep did not include, and none of round 2's
         eight new tests supplies an absent or blank `version`. It also leaves
         TASK-236-result.md § 3.2 claim 5 — "It refuses rather than printing a
         short table … This one does not" — false, and TASK-237 is gated on
         that report.
=== END VERDICT ===
