# TASK-236 — round 3 result: USER-927 answer (B)

> Status: implemented and measured; **not reviewed**.
> Criteria: `perry/evidence/2026-09/TASK-236-spec.md`; the defect is round 2's
> V4 FAIL, `TASK-236-round2-v4-review.md`.
> Executor: the PMO session, inline on `main`.
> **This is not a third review round.** `review.md § 6` made two FAILs a
> decision; `USER-927` was that decision and the user answered **(B)** on
> 2026-09-13. This implements the answer.

## 0. Two corrections that changed the answer before it was given

**(1) B needed no schema authorisation.** `schema/state-schema.json §
stores.declared` holds only `linkage.jsonl` and `.perry/config.jsonl` —
`okr.jsonl` is not declared there at all. Its field list is the `STORED`
constant in `bin/perry_md_store.py`, plain Python. The PMO's earlier note that
B required the user's authorisation on a high-stakes file was **wrong**.

**(2) B alone covers the render, so A is not a needed stopgap.**
`bin/perry-goals § overall_kr_model` calls `md_store.validate_records` BEFORE
it renders and refuses on any malformed record. Demonstrated by giving one
`kr` a wrong-typed `metric` — a shape the validator already caught:

```
perry-goals: refused — 1 record(s) in `okr.jsonl` are badly typed and this
command will not print a table with them silently missing (… `metric` is int,
expected string or null). `perry-lint` names them too; nothing was printed
```

So a rule at that boundary reaches every reader that crosses it.

## 1. The defect

`STORED` is a **whitelist, not a contract**. `validate_records` iterates
`rec.items()` and type-checks only what is PRESENT, so a record missing a field
entirely passed. Round 2's residual then scoped itself with
`k.get("version") in wanted`, and for an absent version that reads
`None in wanted` — always False. Placed by no objective, counted by no
residual, printed by nobody, and the count printed as fact.

## 2. THE FIRST DRAFT WAS WRONG AND THE SUITE CAUGHT IT IN ONE RUN

It required `version` **and** `objective_id` on a `kr`, and `version` and `id`
on an `objective`. `tests/test_md_store` went **24 failures, 3 errors**
immediately.

Both extra fields are **legitimately blank by design**: `DESIGN-009` step 1 has
`derive` write `id: ""` and `objective_id: ""`, and step 3's `migrate-ids` is
the only thing that ever fills them.
`test_no_id_is_minted_in_this_row` asserts that emptiness on purpose.
Requiring them would have condemned every store between step 1 and step 3.

**`version` carries no such story**: every record has always had one, because
`OKR.md` holds several version blocks side by side and a record naming no block
belongs to nothing.

## 3. What landed

```python
REQUIRED = {"kr": ("version",), "objective": ("version",)}
```

checked before the type loop, reporting `absent` and `blank` differently.

**Two layers, each holding the half it can decide.** The validator refuses what
it can judge alone — an absent or blank `version`. The residual in
`overall_kr_model` refuses what needs the join — an unknown version, an
orphaned `objective_id`, a blank objective `id` — because it runs after the
join and knows which objectives exist.

| shape | refused by |
|---|---|
| `version` absent | **validate_records** ← round 2's FAIL |
| `version` blank | **validate_records** ← round 2's FAIL |
| `version` unknown | the residual |
| `objective_id` orphaned | the residual |
| objective `id` blank | the residual |

All five at exit 1. Store restored and `git diff` verified empty after each.

## 4. Every consumer, on the record round 2 let through

| | |
|---|---|
| `perry-goals krs` | rc=1 |
| `perry-okr diff` | rc=2 |
| `perry-okr verify` | rc=2 |
| `perry-lint` | `OKR store: 50 valid record(s), comparison incomplete — drift is unchecked, not clean` |

That is B's whole claim, measured: one change at the boundary, every reader.

## 5. Mutations — five, none green

| # | Broken | Result |
|---|---|---|
| M1 | the rule removed | RED — 3 tests |
| M2 | blank no longer counts, only absent | RED — 1 |
| M3 | absent no longer counts, only blank | RED — 3 |
| M4 | the over-reach restored (`objective_id` required) | RED — the test that pins it must NOT be |
| M5 | the message loses the field name | RED — 2 |

`__pycache__` cleared before every run, after `TASK-381` showed a same-second
restore leaves bytecode Python trusts. `bin/perry_md_store.py` restored and
sha256-verified.

## 6. Suite

Full run, `tests/run`, at the tip of this change:

```
130 modules · 3767 tests · 76.5s · 8 workers
✗ 2 of 130 MODULE(S) red
✗ 3 of 3767 TEST(S) failed
0. tree guard — ✓ nothing under /Users/bytedance/proj/Perry moved
```

The three reds are the session's standing pre-existing ones, none of them in
a module this change touches:

| module | test | why it is not this change |
|---|---|---|
| `test_contract_key_parity` | `TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable` | conformance witness keys; no OKR record in it |
| `test_contract_key_parity` | `TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness` | same pair, same cause |
| `test_resume` | `TestStaleRuns.test_a_fresh_run_is_not_stale` | clock-dependent staleness threshold |

`tests/test_md_store.py` alone: **72 tests OK**, including the 10 new ones in
`TestTheJoinFieldsAreRequiredNotMerelyPermitted`.
