# TASK-183 — DESIGN-009 step 3, the O-1 mint

Delivered 2026-09-10 on `dc88a032`, verified by the PMO on the shared checkout
before it landed. Rung V3: a reproducible run with mutation evidence.

## The render gate, which is why this step is third

The row defers itself behind step 2 in its own words: minting an id into a
record shape that cannot rebuild `OKR.md` would fasten the id to the wrong
thing. So the gate was measured on both sides rather than assumed.

| | before the mint | after the mint |
|---|---|---|
| `perry-okr diff` | `identical: true`, `cells_verbatim {}` | same, exit 0 |
| `perry-okr render` vs `OKR.md` | sha256 `877feee0…88ec45` | **the same sha256** |
| `perry-okr verify` | — | `drift_count: 0`, `byte_identical: true` |

`OKR.md` is byte-identical, which is Decision 2 satisfied by construction: the
migrate command reads `okr.jsonl` and writes `okr.jsonl` and never opens the
markdown at all.

## The row's own count was wrong, and that is the finding

**The row says five Objectives. There are six.** The store holds **ten**
`objective` records — `## v2` and `## v3` side by side — and v3 replaced
Objective 3, *"landed on three named real projects"*, with *"the skill is the
product"*. The five is a count from 2026-08-27, before v3 landed.

Ten records, six ids, grouped by exact title equality. Three things forced that
over one-id-per-record:

- § 5.2 — the id survives *"a new `OKR.md` version that repeats it"*, which only
  a shared id can do;
- § 7 risk 3 — *"`version` is part of the record, not part of the id"*;
- **the store already works this way next door**: `O4-KR1` is one id on two `kr`
  records, 38 records carrying 20 distinct ids, discriminated by `version` and
  `order`.

One-id-per-record would give *"aiMark manages projects through Perry"* — the
Objective this very design is filed under, through O4-KR1 and O4-KR2 — two
addresses. Grouping by `heading` keys on the `Objective <N>` ordinal, which
Decision 1 calls the trap. Both are refused in code and in test.

    O-1 four work modes · O-2 queryable state · O-3 landed on three projects (v2)
    O-4 aiMark · O-5 roles · O-6 the skill is the product (v3)

## A hole found while mutating, and nothing could have caught it

`objective_title` returns `""` for a heading that is only its ordinal —
`### Objective 1`, `### 目标 1`. Measured: two such records came back
`['O-1', 'O-1']`. **Two Objectives, one address, invisible by construction** —
Decision 2 keeps the id out of `OKR.md`, so no byte comparison sees it.
`migrate-ids` now refuses and names the headings. Falling back to `heading` was
rejected as the ordinal trap.

## Nothing was re-dated

The TASK-155 hazard, checked rather than asserted. Per-field over every record:

    records with any change: 48        (the 3 `version` rows untouched)
    fields that changed:  {'id': 10, 'objective_id': 38}
    fields changed that are NOT the ids: {}

`perry-goals krs --json` and `perry-goals list --json` are **byte-identical**
before and after. `perry/linkage.jsonl` has no diff at all; its `declared_at`
values still span five dates rather than collapsing to one.

## Mutation evidence

13 mutants, **0 survivors**, across 11 new tests in
`tests/test_md_store § TestTheObjectiveIdIsMinted`. Each starts from a store
with the ids stripped, so it exercises a real mint rather than the no-op branch.

**Two survived the first round and both were real.** Deleting pass one left the
idempotence test green — pass two's own guard covers a re-run, so pass one only
earns its keep on a *partly* minted store, which is the shape every future run
has when `## v4` lands and one id is missing. Without it the mint restarts at
`O-1` and collides. And dropping pass two's guard leaves the store
byte-identical while reporting ten Objectives as freshly reused on a no-op run.

## Suite

122 modules, 3,492 tests, the three pre-existing reds, tree guard clean,
`perry-lint` 0 errors, `OKR store: 51 record(s), 0 row(s) drifted`.

## For step 4 (TASK-184)

`perry-okr write --from-file` now refuses on this store: `would_discard` sees
`store="O-4" → file=""` for values `OKR.md` does not carry. That is the
documented store-is-canonical refusal working correctly, not a regression, and
step 4 should expect it.
