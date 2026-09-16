# TASK-459 — result: `test_md_store` derives the OKR store's size instead of pinning it

> Branch `coding/task-459-md-store-counts` · base `a2028df8` (main's tip at dispatch)
> Written 2026-09-16 by the Coding Agent. One file changed: `tests/test_md_store.py`.

## 1. Base check

Worktree HEAD at dispatch was `0b5bf99e`, an ancestor of `a2028df8`, tree clean.
`git merge --ff-only a2028df8` fast-forwarded; branch created off that tip. No
push, no PR.

## 2. Baseline, measured in this worktree at `a2028df8`

`python3 -m unittest tests.test_md_store` alone: **76 tests, 8 failures** — the
eight the Bound enumerates, no more and no fewer:

```
TestTheByteGateCanFail.test_the_store_intact_is_a_pass
TestTheByteGateCanFail.test_removing_the_objective_records_fails_the_gate
TestTheObjectiveIdIsMinted.test_the_render_gate_still_holds_after_the_mint
TestTheObjectiveIdIsMinted.test_the_mint_writes_the_store_and_leaves_okr_md_alone
TestTheObjectiveIdIsMinted.test_only_the_two_id_fields_move
TestTheObjectiveIdIsMinted.test_a_later_mint_continues_the_numbering_and_reuses_what_is_there
TestTheObjectiveIdIsMinted.test_one_objective_across_two_versions_is_one_id
TestTheObjectiveIdIsMinted.test_every_kr_carries_the_id_of_the_objective_above_it
```

The live store at this base holds **70 records: 14 `objective`, 52 `kr`, 4
`version`**, across `v2: 2026-08-17`, `v3: 2026-09-01` and `v4: 2026-09-15`.
The 14 objective records carry **10 distinct titles** and so **10 distinct ids**,
`O-1 … O-10`.

## 3. What changed

Each of the eight assertions is replaced by the relation it was standing in for,
with every number read from the store the test itself loaded.

| Test | Was pinned | Now derived |
|---|---|---|
| `test_the_store_intact_is_a_pass` | `out["kinds"]["objective"] == 10` | `== sum(1 for r in p.okr_records() if kind == "objective")` — diff's census and the store on disk agree |
| `test_removing_the_objective_records_fails_the_gate` | `removed == 10` | `removed == sum(... kind == "objective")` — the subtraction stays exact, only its source moves |
| `test_the_render_gate_still_holds_after_the_mint` | `out["kinds"]["objective"] == 10` | same as the first, on the minted store |
| `test_the_mint_writes_the_store_and_leaves_okr_md_alone` | `ids == {"O-1" … "O-6"}` | `ids == {f"O-{n}" for n in range(1, len(titles) + 1)}` — one contiguous run from `O-1`, one id per DISTINCT title |
| `test_only_the_two_id_fields_move` | `moved["id"] == 10`, `moved["objective_id"] == 38` | counted off `before`, the unminted store the case built — EVERY objective record gained an `id`, EVERY kr record an `objective_id` |
| `test_a_later_mint_continues_the_numbering…` | `len(first) == 6`, `new == "O-7"`, `minted == ["O-7"]` | the ids already there are a contiguous run from `O-1`; `highest = len(first)`; `new == f"O-{highest + 1}"` |
| `test_one_objective_across_two_versions_is_one_id` | `len(objectives) == 10` | `len(objectives) > len(titles)` (the premise: some Objective really is repeated) and `len(ids) == len(titles)` (the claim: one id per Objective, never one per record) |
| `test_every_kr_carries_the_id_of_the_objective_above_it` | `len(krs) == 38` | `krs` non-empty, and the join is TOTAL: `{(kr.version, kr.objective)} - set(heading_id) == set()` |

No assertion was deleted, none was replaced by `>= 1`, and no state file was
touched. `perry/okr.jsonl` and `perry/OKR.md` are byte-identical to the base.

### The synthetic version block

`"v4: 2026-10-01"` becomes a class constant `LATER_VERSION = "v99: 2099-10-01"`,
with the comment the spec asks for. It is deliberately **not** `v<current + 1>`:
the case was written as `v4` while the store held `v3`, then OKR v4 landed for
real (`15369956`) and the synthetic block collided with the live one — the
breakage this row exists to undo. Choosing `v5` would re-arm the same trap for
the next revise. `v99` is past any version this repository reaches by revising
its OKR, and the case is about the mint's arithmetic, not about which version
number comes next.

### The two numbers the module now derives (verification 5)

1. **14** — the `objective` records in `perry/okr.jsonl`. Derived at test time by
   `sum(1 for r in p.okr_records() if r.get("kind") == "objective")`, and used by
   both census assertions and by the byte gate's subtraction. It was `10`.
2. **52** — the `kr` records. Derived by `sum(1 for r in before if r.get("kind")
   == "kr")` as the number of `objective_id` fields the mint must move. It was
   `38`.

Two more that were literals and are now read: **10**, the distinct Objective
titles, which sets the mint's contiguous run `O-1 … O-10` (was the typed set
`{"O-1" … "O-6"}`); and **`O-11`**, the id a later mint hands a new Objective,
computed as `f"O-{highest + 1}"` (was the typed `"O-7"`).

## 4. Verification

### 4.1 The module alone, on the final commit

```
$ python3 -m unittest tests.test_md_store     # PERRY_PROJECT / PERRY_HOME unset
Ran 76 tests in 4.9s
OK
```

76 tests, 0 failures.

### 4.2 `tests/durations.json` — not touched, and why

The spec puts it in scope only if the module's time moves by more than 0.5 s.
It did not. The recorded figure is `4.9` s. Nine runs of the green module on a
settled machine: 12.364, 8.336, 5.140, 4.815, 4.558, 4.521, 5.046, 5.084, 4.637.
The first three were taken under concurrent load; the floor is **4.52 s** and the
settled band is 4.5–5.1 s, straddling the recorded 4.9. The spread on
*identical code* is larger than the threshold, so no move is attributable and the
file is left alone.

### 4.3 Mutations

Each on a fresh `git archive` copy of the final commit, under
`$TMPDIR/perry-scratch/`. Nothing was written into the checkout.

| # | Mutation | Expected | Observed | Verdict |
|---|---|---|---|---|
| M1a | A fifth Objective **with** a KR appended to `OKR.md` *and* `okr.jsonl` (a realistic revise; store → 15 objective, 53 kr) | relation tests stay green; the byte gate still fails on REMOVAL | 76 tests, **OK**. `test_removing_the_objective_records_fails_the_gate` passed with the subtraction now **15**, adapted on its own | ✅ as specified |
| M1b | The same fifth Objective **with no KR** | relation tests stay green | 76 tests, **OK** (after the narrowing in § 5) | ✅ |
| M2 | Delete one `kr` record's `objective_id` from `perry/okr.jsonl`, exactly as worded | the "every KR carries the id…" case goes red | **RED — but on a different test**: `test_the_shipped_store_carries_an_id_for_every_objective`. See the finding in § 5 | ⚠️ caught, by another case |
| M2b | The mint gives every KR the same `objective_id` (`bin/perry_md_store.py`) | the named case goes red | **RED**, 46 subtests of `test_every_kr_carries_the_id_of_the_objective_above_it` | ✅ |
| M2c | One `kr` names an Objective heading no `objective` record carries | the named case goes red | **RED**, 1 failure, on the new total-join line and its own message | ✅ |
| M3 | Break the mint's numbering: pass one stops reading the existing ids (`highest = max(highest, 0)`) | the "a later mint continues the numbering" case goes red | **RED**, exactly 1 failure: `test_a_later_mint_continues_the_numbering_and_reuses_what_is_there` | ✅ |

No mutation the spec says should be red came back green on the assertion it
targets.

## 5. Findings and choices a reviewer should check

### 5.1 Finding — the join must be total ONE way, not both (found by mutation)

`test_every_kr_carries_the_id_of_the_objective_above_it` was first written here
with the join asserted total in **both** directions: every KR names an Objective
record that exists, *and* every Objective record is named by at least one KR.
M1b — a fifth Objective appended with no KRs yet — turned that red:

```
AssertionError: Items in the second set but not the first:
('v4: 2026-09-15', 'Objective 5 — A fifth objective the next revise adds')
```

That is the exact fragility this row exists to remove. An Objective reaching
`OKR.md` and the store before its KRs are written is a legitimate intermediate
state; a KR pointing at no Objective is a defect. The assertion was narrowed to
the KR → Objective direction only, and the reason is recorded in the test's own
comment so the next reader does not "strengthen" it back. M2c confirms the kept
direction is still reddenable.

### 5.2 Finding — M2 as worded cannot reach the case it names

The spec's second mutation is "delete one `kr` record's `objective_id`" and
expects `test_every_kr_carries_the_id_of_the_objective_above_it` to go red. It
cannot, by construction, and this is a property of the class rather than of this
row's change: every case in `TestTheObjectiveIdIsMinted` starts from
`self._project()`, whose `_unminted` helper **strips `id` from every objective
record and `objective_id` from every kr record** before running `migrate-ids`.
A store-level deletion of one `objective_id` is deleted again by the fixture and
re-minted. The mutation is still caught — the module goes red on
`test_the_shipped_store_carries_an_id_for_every_objective`, which is one of the
68 untouched tests and reads the shipped store directly — so the suite is not
blind to it. M2b and M2c were added to show the named case is genuinely
reddenable by mutations that survive the fixture.

### 5.3 Choice — what "derive it from the store" means where the derivation is circular

Two of the eight pins guarded nothing but the fixture's size, and a literal
translation (`len(krs) == len([r for r in records if kind == "kr"])`) would be a
tautology — green on any store, including an empty one. Those two were given the
relation the spec names instead:

- `len(krs) == 38` → the join is total (§ 3), which is strictly stronger than the
  count it replaces: a mint that answered all 52 KRs with one id satisfies "52
  answered" and fails this.
- `len(objectives) == 10` → `len(objectives) > len(titles)`, the premise the case
  needs (some Objective really is repeated across versions), plus
  `len(ids) == len(titles)`, which is the claim the case is named for.

Each is paired with a non-emptiness guard so the relation cannot pass vacuously
on an empty store.

### 5.4 Not done, and deliberately

`tests/durations.json` (§ 4.2). Nothing under `bin/`, `viewer/` or `schema/`. No
other test module. No state file.

## 6. Full suite on the final commit

`bash tests/run`, `PERRY_PROJECT` and `PERRY_HOME` unset, on `177937e5`:

```
141 modules · 3966 tests · 144.6s · 8 workers
✗ 1 of 141 MODULE(S) red
✗ 1 of 3966 TEST(S) failed
0. tree guard — ✓ nothing under <worktree> moved
```

`tests/test_md_store.py` is green in the suite as it is alone.

### The one red is not this row's

`test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`:

```
AssertionError: Lists differ: ['OQ-4', 'OQ-5', 'OQ-6', 'OQ-7'] != []
```

Re-run alone in this worktree: same failure, same four ids. Re-run alone on a
clean `git archive` copy of the **base** `a2028df8`: **the identical failure,
the identical four ids.** It is a baseline red that arrived with the base, not
with this branch, and this branch adds nothing to the list.

Its cause is the one `CLAUDE.md` already records: `OQ-` is not one of
`lib.PERRY_CITATION_FAMILIES`, so `perry-diagnose` reads a prose mention of an
open question as a citation that resolves nowhere. The four mentions live in
`perry/evidence/2026-09/TASK-442-dispatch-2026-09-15-2101.md`, committed with the
base. Out of scope here — this row may not edit another row's evidence, and the
fix is either a citation family or a rewording of that file.

This row's own result file cites no `OQ-`, and the dangling list is unchanged
between the base and `177937e5`.

## 7. Architecture compliance

- **NN-4** (deterministic tools decide nothing about meaning): no `bin/` code was
  touched; the change is test-side and every new judgement is a set or integer
  comparison over records already parsed by `viewer/parsers.py`'s store reader.
- **NN-5** (the suite never writes into the tree it runs in): every new line
  reads. The mutations ran on `git archive` copies under `$TMPDIR`, never in the
  checkout; `tests/tree_guard.py` is green.
- **NN-2** (the store is truth; the projection is rendered): this row is the rule
  applied to a test — the store moved, so the test that described it was wrong,
  and the store was not edited to match the test.
- `ARCHITECTURE.md` was not edited (NN-6). No new §7 question is opened.
