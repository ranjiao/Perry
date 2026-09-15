# TASK-448 — spec

> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: large
> Touches architecture: §2 (tests), §6.NN-5
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Track / mode**: main / project
- **Dependencies**: none.
- **Design**: `DESIGN-021 § 5.2` and `§ 6` phase A (locked 2026-09-15).
- **KR linkage**: `P004-O4-KR1` (edge written by `add`).
- **Verification rung**: V3.

## Why

Every executor and reviewer round runs the whole suite: 141 timed modules,
1,054.3 module-seconds (`tests/durations.json`, 2026-09-15), +3.5% since
2026-09-09. `DESIGN-021` introduces tiers, and its phase A is the gate: of 143
test modules, 84 name four or more `bin/` tools, so selecting by tool name would
select nearly everything. Each module must instead declare what it is **for**,
and a replay of real merges must show the selection is narrow enough before any
brief switches (`TASK-449`).

## Deliverable

1. **Every `tests/test_*.py` declares `COVERS`** — a tuple of repository path
   prefixes whose behaviour the module asserts, or `COVERS = ALL` for a module
   that genuinely guards everything. `ALL` is imported from the new
   `tests/selection.py`. A module covers what it asserts, not every tool it
   happens to invoke. Where a module declares `ALL`, one comment line says why.
2. **`tests/selection.py`** (stdlib), implementing `DESIGN-021 § 5.2` exactly:
   changed paths from `git diff --name-only <base>...<head>`; a changed
   `tests/test_*.py` selects itself; a changed path matching a `COVERS` prefix
   selects that module; **widening rules checked first**, each selecting the full
   suite — a changed path under `bin/lib/`, `viewer/parsers.py`, `schema/`, a
   `tests/` helper that is not `test_*.py`, or any changed path no `COVERS`
   matches; a module with no `COVERS` is always selected. A pure function over
   (changed paths, declarations), with a thin git layer.
3. **`tests/run --tier affected --base <ref> --dry-run`** prints one line per
   selected module with the rule that selected it, the selected share of
   module-seconds (from `tests/durations.json`), and `this change is wide` when
   the share exceeds half. It runs no test. No other invocation of `tests/run`
   or `tests/parallel` changes behaviour in this row.
4. **`tests/test_selection.py`**: one case per selection rule, and a guard that
   lists modules without `COVERS` (expected empty when this row lands).
5. **The replay.** For the last 50 merge commits reachable by first parent from
   the base (`git log --merges --first-parent -50 --format=%H <base>`), diff
   `M^1..M`, run the selector, and record per merge: selected module count,
   selected share of module-seconds, and the widening rule if one fired. Report
   the distribution, the median share, and the gate verdict — **PASS if the
   median share is ≤ 50%, otherwise FAIL with the three most frequent reasons** —
   at `perry/evidence/2026-09/TASK-448-replay.md`. Write it incrementally and
   commit as you go.
6. **A result** at `perry/evidence/2026-09/TASK-448-result.md`.

## Files in scope

- `tests/test_*.py` — the `COVERS` declaration and its import only
- `tests/selection.py` (new), `tests/test_selection.py` (new)
- `tests/run` — the `--tier affected --dry-run` entry only
- `tests/durations.json` — only if a module's time moves by more than 0.5 s
- `perry/evidence/2026-09/TASK-448-replay.md`, `perry/evidence/2026-09/TASK-448-result.md`

## Bound

```
Enumeration:  tests/test_*.py at the base commit
Size:         143 modules (recount at base)
Remainder:    helpers under tests/ that are not test_*.py get no COVERS
Last element: the alphabetically last tests/test_*.py

Replay:       git log --merges --first-parent -50 <base>
Size:         50 merges
Last element: the 50th (oldest) merge listed
```

## What it must not do

1. **Must not change which tests any existing command runs.** Bare `tests/run`,
   `--lint`, `--serial`, `--only`, `--slow` and every `tests/parallel` invocation
   behave exactly as at base. Tiers are `TASK-449`.
2. **Must not change `bin/`, `viewer/`, `schema/`, lane documents or contract
   pages.**
3. **Must not write into the checkout during the replay (NN-5).** Every worktree
   or archive lives under `$PERRY_SCRATCH`; `tests/tree_guard.py` stays green.
4. **Must not delete a test or weaken an assertion.** `COVERS` is a declaration.
5. **Must not write the task stores, `linkage.jsonl`, `okr.jsonl`, `phase/`,
   `.perry/events.jsonl` or the journal.**

## Verification

1. **Base check** as the brief states.
2. **`bash tests/run` on the final commit**: no reds beyond the agent's own
   measurement at base (report both). Re-run any red module alone before
   attributing it.
3. **`python3 -m unittest tests.test_selection` green, and mutations** — each on
   a fresh scratch copy, each red on a named test:
   - remove the `bin/lib/` widening rule;
   - make a module without `COVERS` unselected;
   - delete `COVERS` from one module (the guard names it).
   A green mutation is a finding.
4. **`bash tests/run --tier affected --base HEAD~1 --dry-run`** prints selection
   lines and exits 0 without running a test — output quoted in the result.
5. **The replay report** has 50 rows, the median and the verdict.

## Subjective verification

(none)

## Out of scope

- The smoke, full and slow tiers and the brief switch (`TASK-449`).
- The merge gate (`TASK-450`), the runtime ratchet, the slow tier's membership.
