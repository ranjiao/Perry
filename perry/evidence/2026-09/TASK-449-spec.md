# TASK-449 — spec

> Row: DESIGN-021 phase B — tests run in tiers, and the briefs switch to smoke plus affected
> Priority P1 · Owner Coding Agent · Rung V3 · Phase 004, Objective 4
> Written 2026-09-16 by the PMO. Base: main's tip at dispatch.
> Unblocked by `USER-943`: phase A's gate is 75% of module-seconds and the replay measured 73.3%.

## Why

`tests/run` has one size: all of it. Every executor round and every review round
pays for 964 seconds of module time to check a change that usually touches a
handful of modules. Phase A built the selector and measured it; this row is the
part a person notices.

What exists after phase A (`4ade25d0`): all 146 modules declare `COVERS`,
`tests/selection.py` turns changed paths into a module set as a pure function,
and `tests/run --tier affected --base <ref> --dry-run` prints that set and runs
nothing. Every other `--tier` spelling exits 2.

## Deliverable

`DESIGN-021 § 5.1`'s four tiers, and `§ 5.5`'s briefs.

### 1. `tests/run --tier smoke|affected|full|slow [--base <ref>] [--dry-run]`

| Tier | Contains | Budget |
|---|---|---|
| `smoke` | `perry-lint --templates` (today's step 1), every shipped script compiles and answers `--help` (today's step 3), and the tree guard's hash check | ≤ 30 s wall |
| `affected` | the modules `tests/selection.py` selects for `--base`, plus `smoke` | median ≤ 60 s wall |
| `full` | every module except the slow set — today's bare `tests/run` | — |
| `slow` | today's `--slow`: `tests/parallel § HARNESS_SELF_TESTS` | — |

- **Bare `tests/run` becomes `--tier full` and must behave exactly as it does
  today**, step for step, including `--lint`, `--serial`, `--only` and `--slow`.
  Those four flags keep working and keep their meaning; `--slow` is now a
  spelling of `--tier slow`.
- `--dry-run` keeps its phase-A meaning for any tier: print the selection and
  run nothing.
- `--tier affected` without `--base` exits 2 and says so. An unknown tier still
  exits 2 before anything runs.
- Every tier runs inside the tree guard, on every exit path (`NN-5`).

### 2. `tests/parallel --tier <name> [--base <ref>]`

The same four names, so a caller that wants the parallel harness does not have
to reconstruct the module set. `--slow`, `--times` and `--record` keep their
current behaviour; `--record` still runs the whole tree, always.

### 3. The briefs (`§ 5.5`)

| Role | Runs | Written in |
|---|---|---|
| Executor | `--tier affected --base <the pinned base>` each round, and quotes the printed selection in its RESULT | `work/reference/dispatch.md` |
| V4 reviewer | `--tier affected --base <the same base>`, plus its own mutations | `work/reference/review.md` |

Both pages must say plainly: **a red in `affected` is a red; a green in
`affected` is not a green suite.** The full run still happens at merge
(`TASK-450`), and until that row lands the primary checkout keeps running
`tests/run` itself — say that too, rather than implying the merge gate exists.

## Files in scope

- `tests/run`, `tests/parallel`, `tests/selection.py` (only if the tier entry needs it)
- `tests/test_selection.py`, or a new `tests/test_tiers.py` if that is cleaner — declare `COVERS` on whichever you add
- `work/reference/dispatch.md`, `work/reference/review.md`
- `tests/durations.json` only if a module's time moves by more than 0.5 s
- `perry/evidence/2026-09/TASK-449-result.md`

## Bound

```
Enumeration:  the four tiers of DESIGN-021 § 5.1 and the two briefs of § 5.5
Size:         4 tiers, 2 pages
Remainder:    the merge gate (TASK-450), the ratchet (§ 5.4), the slow tier's
              membership (phase E) are other rows
Last element: work/reference/review.md
```

## What it must not do

1. **Must not change which tests bare `tests/run` runs**, nor `--lint`,
   `--serial`, `--only` or `--slow`. A caller that does not pass `--tier` sees
   no difference.
2. **Must not change the selector's rules.** `USER-943` left the widening rules
   as `§ 5.2` writes them, and the gate at 75%. Selection is phase A's; this row
   only runs what it selects.
3. **Must not build the merge gate or the ratchet**, and must not claim in prose
   that either exists.
4. Must not touch `bin/`, `viewer/` or `schema/`.
5. Must not write into the checkout: every test and mutation works under a
   temporary root, and the tree guard stays green (`NN-5`).

## Verification

1. **Base check** as the brief states.
2. **`bash tests/run` on the final commit**, with `PERRY_PROJECT` and
   `PERRY_HOME` unset: green, and the same module and test counts as bare
   `tests/run --tier full`. Quote both.
3. **`bash tests/run --tier smoke`**: green, and **report its wall time against
   the 30-second budget**. If it does not fit, say so with the number rather
   than trimming what smoke contains.
4. **`bash tests/run --tier affected --base HEAD~1`**: green, and report its
   wall time and the selection it ran. Then **measure the affected median**
   across at least five recent single-commit bases and report each, against the
   60-second budget.
5. **`bash tests/run --tier slow`** runs the harness self-tests and nothing is
   lost against today's `--slow`.
6. **Mutations**, each on a fresh scratch copy, each red on a named test:
   - `--tier affected` silently running the full set instead of the selection;
   - `--tier smoke` skipping the tree guard;
   - bare `tests/run` diverging from `--tier full`.
   A green mutation is a finding.
7. Quote the two brief changes, so the prose can be read without opening the files.

## Subjective verification

- [user-verify] Read `work/reference/dispatch.md`'s brief section: is what the
  executor is told to run unambiguous in one reading?

## Out of scope

- `TASK-450` (the merge gate, `--record` at merge), `§ 5.4`'s ratchet, phase E's
  slow-tier membership, and `TASK-312` / `TASK-401`.
