# TASK-132 spec — the parity check cannot see keys inside a collection this project leaves empty

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: medium
> Measured on this repository 2026-08-27, **after** TASK-176 landed.

## The number on the row is stale; here is today's

The row says 23 keys. Measured tonight:

```
perry-decide/list/1.0        3 keys unobservable
perry-goals/list/2.1         4
perry-task/list/1.15         8
perry-events, roles, knowledge  0
                            ──
                            15 keys, across FOUR empty collections
```

| contract | the empty collection |
|---|---|
| `perry-decide` | `expired_sunsets` |
| `perry-goals` | `krs[].current_staleness.moved_tasks` |
| `perry-task` | `conformance.depends_on_unknown` |
| `perry-task` | `conformance.in_progress_with_no_live_run` |

**Re-measure before you start and report your own number.** It moves with the
board, which is the whole problem.

## Why this matters more since tonight

TASK-176 fixed a *neighbouring* case and proved the general shape. Its finding,
in its own words: a table documenting two same-shaped collections read **0
findings while half of it was undocumented**, purely because only one of the two
arrays happened to be non-empty that minute.

`not_observable` is the same defect wearing an honest label. The parity check is
correct to say *"I cannot check this"* — but 15 keys that nothing has ever
verified are 15 places where the contract and the payload could already
disagree, and **KR-O2.4 reads 0 either way.**

`conformance.in_progress_with_no_live_run` is on both lists: TASK-176 taught the
page to name it, and it is *still* unobservable tonight because it is empty.
Those are two different problems on one key and this row is the second.

## The scope

**Make the unobservable observable, without lying about the live board.**

The obvious move — assert against a fixture payload — already has a seam:
TASK-176 added a documented `payload=` argument to `compare()` precisely because
no tool on disk emits the shape it needed. **Read how that seam works before
designing anything.**

What the fix must not do:

- **Do not fabricate entries into Perry's own state** to make a collection
  non-empty. A real `depends_on_unknown` entry means a real broken dependency;
  manufacturing one to satisfy a checker is the defect this project refuses
  hardest.
- **Do not delete the `not_observable` reporting.** It is honest and it is how
  this row was found. Whatever you add, `not_observable` must still name
  anything that remains unchecked.
- **Do not change KR-O2.4's definition.** If newly-observable keys turn out to
  be genuinely undocumented, **that is a finding and the number goes up** —
  report it, do not paper it.

## Verification

1. Your own measurement of today's unobservable count, before and after, per
   contract.
2. The keys you made observable are **actually checked** — a mutation that
   removes one from its contract page reddens something. Do this for at least
   one key per collection you cover.
3. **`not_observable` still reports whatever you did not cover**, by name.
4. **No entry was added to `perry/`.** `git diff -- perry/` must end empty.
5. If KR-O2.4 moves, say by how much and name every key. A rise is a result,
   not a failure.
6. `perry-lint --root .` — 0 errors.

## Out of scope

- The oscillation itself — that a collection's emptiness changes what is
  measurable at all — is TASK-176's finding and it explicitly left the general
  case open. **You may narrow it; you are not required to close it.** Say which
  you did.
- Do not touch `schema/state-schema.json` or `perry/`.

## Ground rules

- Branch `coding/task-132-unobservable-keys`, commit there, **no PR, no push**.
- **Commit as soon as you have something coherent, and keep committing.**
- `PYTHONNOUSERSITE=1 /usr/bin/python3` explicitly — Perry is stdlib-only as of
  tonight, and that flag is what proves it.
- `tests/parallel -j 4`. Verify yours is the only one with a pattern that
  **cannot match your own argv**:
  `ps -Ao pid,command | grep "python3 tests/paralle[l]"`.
- Expected baseline: **80 modules · 2369 tests · 2 red** —
  `test_contract_invariance` (a union-typed key) and `test_diagnose` (two
  failures). **Neither is yours.**
