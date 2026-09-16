# TASK-459 — spec

> Row: `test_md_store` pins the live OKR store's counts, and OKR v4 moved them, so the suite is red on main
> Priority P1 · Owner Coding Agent · Rung V3 · Unlinked (hygiene, serves no phase-004 KR)
> Written 2026-09-16 by the PMO. Base: main's tip at dispatch.

## Why

`15369956` (OKR v4) appended 4 objective and 14 `kr` records to `perry/okr.jsonl`
and rewrote `perry/OKR.md`. Eight tests in `tests/test_md_store.py` assert this
repository's live counts and now fail. Measured on main `ba11da7a`, run alone:

| Test class | Assertion | Now |
|---|---|---|
| `TestTheByteGateCanFail` (2) | `out["kinds"]["objective"] == 10`; `removed == 10` | 14 |
| `TestTheObjectiveIdIsMinted` (6) | `len(objectives) == 10`; `len(krs) == 38`; `len(first) == 6`; a synthetic `"v4: 2026-10-01"` version block; the minted id set | 14 · 52 · 10 · collides with the real v4 · gains `O-7`…`O-10` |

`06e437ba` already fixed the ninth failure and `tests/test_okr_krs_render.py` by
reformatting the v3 retro table in `OKR.md`; those are not this row's.

Every dispatch since `bb178072` reports these as baseline reds, which is exactly
the noise that hides a real one.

## Deliverable

`tests/test_md_store.py` green on main, **without pinning a count that the next
OKR revise will move again.** The row is finished when a fifth objective, or a
fifteenth KR, can be appended to `okr.jsonl` without reddening this module.

Each of the eight assertions is one of two kinds, and they are fixed differently:

1. **The count is the fixture's size** ("the fixture moved"). Derive it from the
   store at test time rather than typing it: count the records the test itself
   loaded, and assert the RELATION the test is about (the store and the file
   agree; every KR carries the id of the objective above it; a later mint
   continues the numbering).
2. **The count is the thing under test** (`TestTheByteGateCanFail` removes every
   objective record and asserts the gate fails). Keep the subtraction exact, but
   take the number from the store, not from a literal.

The synthetic `"v4: 2026-10-01"` version block must stop colliding with the real
v4: use a version this repository will not reach soon, and say in a comment why
it is not `v<current+1>`.

## Files in scope

- `tests/test_md_store.py`
- `tests/durations.json` only if this module's time moves by more than 0.5 s

## What it must not do

1. **Must not change `perry/okr.jsonl`, `perry/OKR.md` or any other state file.**
   The store is right; the test is stale.
2. **Must not weaken an assertion to make it pass** — deleting a case, or
   asserting `>= 1`, is a failure of this row. The relation each test names must
   still be checked, and must still be reddenable.
3. Must not touch `bin/`, `viewer/` or `schema/`.
4. Must not edit another test module.

## Bound

```
Enumeration:  the failing tests in tests/test_md_store.py at the base commit
Size:         8
Last element: TestTheObjectiveIdIsMinted.test_the_render_gate_still_holds_after_the_mint
Remainder:    the module's other 68 tests are green and stay untouched
```

## Verification

1. **Base check** as the brief states.
2. `python3 -m unittest tests.test_md_store` green alone on the final commit — 76
   tests, 0 failures.
3. **`bash tests/run`** with `PERRY_PROJECT` and `PERRY_HOME` unset: no reds at
   all, unless another row landed one first; re-run any red module alone before
   attributing it.
4. **Mutations**, each on a fresh scratch copy, each red on a named test:
   - append one more `objective` record to a copy of `perry/okr.jsonl` — the
     tests that assert a RELATION stay green (this is the point of the row), and
     the byte-gate case still fails when the records are REMOVED;
   - delete one `kr` record's `objective_id` — the "every KR carries the id of
     the objective above it" case goes red;
   - break the mint's numbering — the "a later mint continues the numbering"
     case goes red.
   A green mutation on the last two is a finding.
5. Quote in the result the two numbers the module now derives instead of pinning.

## Subjective verification

(none)

## Out of scope

- The KR `check` and `measurement` records of `DESIGN-022` (not built yet).
- `tests/test_okr_krs_render.py` and the `OKR.md` retro format — done at `06e437ba`.
