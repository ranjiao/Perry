# TASK-145 — the contract shape baseline is stale against its own recorder

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: medium
> Measured 2026-08-28. **This row owns one of the suite's two standing reds.**

## The measurement

Comparing `tests/fixtures/contract-shapes.json` against what
`test_contract_invariance.capture()` produces today:

```
perry-decide/list    recorded  24  live  24  moved 0  gone 0  new  0
perry-goals/list     recorded  59  live  78  moved 0  gone 0  new 19
perry-task/list      recorded  99  live 124  moved 1  gone 0  new 25
    MOVED: intake.oldest_undischarged: NoneType -> int
```

**44 keys the fixture never recorded, and one that "moved".** The gate is right
to ignore the 44 — adding a key is a `1.x` change and is *allowed*. It fails on
the one, and that one is the red:

```
AssertionError: ['perry-task/list: intake.oldest_undischarged was NoneType, now int']
```

## The one that moved is not a retype

`schema/task-list-contract.md:301` declares it:

```
| `oldest_undischarged` | int \| null | the `n` of the longest-waiting undischarged row |
```

**Both types are contractually correct.** The fixture recorded `NoneType`
because that was the half live on the day it was captured; three intake rows
arriving supplied the other half.

**It is five landmines, not one.** Every `NoneType` in that fixture is a
union-typed key:

| path | contract | fires when |
|---|---|---|
| `perry-task/list` `intake.oldest_undischarged` | `int \| null` | **fired** — any undischarged intake row |
| `perry-task/list` `risks.items[].age_days` | `int \| null` | the first risk gets an `opened` date |
| `perry-task/list` `tasks[].created` | `string \| null` | the array's first element is a row the log knows |
| `perry-goals/list` `krs[].current` | number or absent | the array's first KR gets a number |
| `perry-goals/list` `krs[].target` | number or absent | same |

Full diagnosis: `evidence/2026-08/contract-invariance-union-types.md`.

## And it is order-sensitive, which is sharper

`shape()`'s own docstring says *"lists collapse to their first element's
shape"*, chosen so the gate does not key on length — *"keying on length would
make every board edit a contract change."*

For an array-nested union key that replaces length-sensitivity with something
narrower and less predictable: the recorded type is **whichever branch element
zero happened to have**. Re-sorting the array, re-prioritising a row, or closing
the row that used to be first can flip a type the contract never promised was
stable — **which is the outcome the docstring set out to avoid.**

## What the fix must not do

- **Do not regenerate `contract-shapes.json` from today's payload.** The
  docstring predicts that move by name: *"a golden file … would be regenerated
  by whoever broke it, which is how a snapshot stops meaning anything."*
- **Do not delete the gate.** Its catch is real and was proved by removing
  `tasks[].startable` at both emit sites and watching it go red. **Your change
  must keep that mutation red** — verify it.
- **Do not silence union keys by ignoring `NoneType`.** A key declared `int`
  that starts returning `null` must still fail.

## What it must do

**Read the declared type from the contract document**, so `int | null` accepts
either branch and `int` still fails on `null`. The pages are the authority; the
fixture is a cache of one observation.

For array-nested keys, decide and argue: a union over **every** element, or the
fixture recording the union. Element-zero must stop deciding.

## Verification

1. `test_contract_invariance` is **green** on this repository.
2. **The mutation still catches**: remove `tasks[].startable` at both emit sites
   → red. Paste it.
3. A key declared `int` that returns `null` → **red**. Build the fixture.
4. A key declared `int | null` → green on either branch, proved on both.
5. **Array order does not decide.** Reorder a collection so element zero carries
   the other branch; the verdict is unchanged.
6. The 44 added keys are still accepted without being recorded — adding a key is
   still a `1.x` change.
7. `perry-lint --root .` — 0 errors.

## Out of scope

- The other standing red (`test_diagnose`) is TASK-165/TASK-179's.
- Do not touch `schema/state-schema.json` or `perry/`. `git diff -- perry/` must
  end empty.

## Ground rules

- Branch `coding/task-145-shape-baseline`, commit there, **no PR, no push**.
- **Commit as soon as you have something coherent, and keep committing.**
- `PYTHONNOUSERSITE=1 /usr/bin/python3` explicitly.
- `tests/parallel -j 4`. Verify yours is the only one with a pattern that
  **cannot match your own argv**:
  `ps -Ao pid,command | grep "python3 tests/paralle[l]"`. Scratch files under a
  path containing your branch name. **Never `git checkout` while a suite runs.**
- Expected baseline: **83 modules · 2471 tests · 2 red** —
  `test_contract_invariance` (**yours**) and `test_diagnose` (two failures, not
  yours, one order/parallel sensitive).
