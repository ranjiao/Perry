# TASK-448 — the replay: 50 merges through the `COVERS` selector

> Design: `DESIGN-021 § 6` phase A, the gate · Spec: `TASK-448-spec.md` deliverable 5
> Branch: `coding/task-448-covers-and-replay` · declarations and stopwatch as committed at `3da8ad1e`

## Verdict

**FAIL.** The median merge selects **100.0%** of the suite's module-seconds; the
gate is ≤ 50%. 30 of 50 merges widen to the full suite. The three most frequent
reasons, counted in merges:

1. **`tests/` helper — 27 merges** (the only rule that fired in 17 of them)
2. **`schema/` — 10 merges**
3. **`bin/lib/` — 9 merges**

`viewer/parsers.py` fired in 8. The unmatched-path rule fired in none: every path
these 50 merges changed falls under some module's `COVERS`.

By the spec, `DESIGN-021 § 6` phase A's gate is not met, so the selector is
redesigned before any brief switches (`TASK-449`). What the redesign would have
to move is measured under *What makes the selection wide*, below.

## Method

- **Enumeration.** `git log --merges --first-parent -50 --format=%H bb178072`.
  Size 50. Last element: row 50, `59e90e61` (2026-09-07). Every row is below.
- **Changed paths.** `git diff --name-only --no-renames M^1 M` per merge. With
  `--no-renames`, a rename reports both the old and the new path.
- **Selector.** `tests/selection.py § select`, which is `DESIGN-021 § 5.2` as
  implemented in this row, run against **today's** declarations (the tree at
  `3da8ad1e`), not the modules as they stood at each merge. A module deleted
  since then is not counted, and a module added since is.
- **Share.** Selected module-seconds ÷ suite module-seconds, from
  `tests/durations.json`, read through `tests/parallel § load_durations`. That is
  1,055.6 s over 144 modules; the three unmeasured modules count 0. The
  `modules` column counts `test_selection.py`.
- **One reading of § 5.2.** "A `tests/` helper that is not a `test_*.py`" is read
  literally: any changed path under `tests/` other than `tests/test_*.py`
  selects the full suite, including `tests/durations.json` and
  `tests/fixtures/**`. The sensitivity to that reading is measured below.
- **Reproduce.** `python3 tests/selection.py --replay 50 --base bb178072` prints
  the table and summary that follow, byte for byte. It reads git and writes
  nothing. It ran from the checkout; no worktree or archive was created for it.

## Per merge — the selector's own output

| # | merge | date | subject | paths | modules | share | widening rule (paths) |
|---|---|---|---|---|---|---|---|
| 1 | `de4dc685` | 2026-09-15 | Merge TASK-441: six live-phase test modules measure a copy with pha... | 9 | 144 | 100.0% | tests/ helper (2) |
| 2 | `8489a2c8` | 2026-09-15 | Merge TASK-262 round 4b: no reader other than the imports reads a h... | 74 | 144 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); schema/ (4); tests/ helper (23) |
| 3 | `80ef880b` | 2026-09-15 | Merge TASK-262 round 4a: perry-task writes never read or rewrite a ... | 44 | 144 | 100.0% | bin/lib/ (1); schema/ (1); tests/ helper (2) |
| 4 | `942d7749` | 2026-09-15 | Merge TASK-262 round 3 result: stopped on contract pins, nothing im... | 1 | 32 | 33.7% | — |
| 5 | `f53b10b9` | 2026-09-15 | Merge fix/hidden-reds-and-waits: two reds hidden behind --slow, two... | 4 | 144 | 100.0% | tests/ helper (1) |
| 6 | `282e6acb` | 2026-09-15 | Merge TASK-262 round 2: perry-task SURFACE writes names what each w... | 6 | 144 | 100.0% | tests/ helper (1) |
| 7 | `ddf60594` | 2026-09-15 | Merge TASK-262 round 1: perry-tasks board names each section's stor... | 9 | 144 | 100.0% | tests/ helper (2) |
| 8 | `5c790cff` | 2026-09-14 | Merge TASK-237 round 2 V4 review: PASS | 1 | 32 | 33.7% | — |
| 9 | `80c8eeb1` | 2026-09-14 | Merge TASK-335: the parity anti-vacuity tests read one frozen copy | 3 | 144 | 100.0% | tests/ helper (1) |
| 10 | `7523f1fe` | 2026-09-14 | Merge TASK-237 round 2: a write refuses where nothing is installed;... | 20 | 144 | 100.0% | bin/lib/ (1); schema/ (1) |
| 11 | `13522369` | 2026-09-14 | Merge TASK-237 3d: the V5-signed hand-off contract, the git-boundar... | 22 | 73 | 55.0% | — |
| 12 | `0f1ed007` | 2026-09-14 | Merge TASK-237 3c: BOARD.md is deleted; installed needs .perry/; a ... | 72 | 144 | 100.0% | viewer/parsers.py (1); schema/ (8); tests/ helper (4) |
| 13 | `0ec65094` | 2026-09-14 | Merge TASK-237 3b-prime: starts write the config store first; one i... | 56 | 144 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); schema/ (7); tests/ helper (3) |
| 14 | `161c927c` | 2026-09-14 | Merge TASK-237 3b (partial): cadence store, board title and prose, ... | 22 | 144 | 100.0% | viewer/parsers.py (1); schema/ (1); tests/ helper (2) |
| 15 | `47dce04a` | 2026-09-14 | Merge TASK-237 3a: reads answer from their stores, and writes land ... | 17 | 144 | 100.0% | viewer/parsers.py (1); schema/ (2); tests/ helper (2) |
| 16 | `cb88d848` | 2026-09-14 | Merge TASK-237 D1: perry-tasks board prints the whole board from th... | 8 | 144 | 100.0% | tests/ helper (1) |
| 17 | `9549626e` | 2026-09-14 | Merge TASK-237 D1+D2: the board-less project is recognised; byte-id... | 6 | 144 | 100.0% | tests/ helper (2) |
| 18 | `c7618a96` | 2026-09-12 | Merge TASK-439: `perry-task add` refuses a row that answers the KR ... | 11 | 144 | 100.0% | tests/ helper (1) |
| 19 | `4babb645` | 2026-09-12 | Merge TASK-430: 58 modules that silently reported a clean pass, and... | 6 | 144 | 100.0% | tests/ helper (4) |
| 20 | `687579bd` | 2026-09-12 | Merge TASK-236: OKR.md's 38 KR rows come out, and the byte gate is ... | 11 | 144 | 100.0% | tests/ helper (2) |
| 21 | `fe9b922e` | 2026-09-11 | Merge v4-round-411-412-419-431: four PASSes, and one green that sho... | 1 | 32 | 33.7% | — |
| 22 | `7c89ad05` | 2026-09-11 | Merge v4-review-348-368-421: three PASSes, and a finding aimed at t... | 1 | 32 | 33.7% | — |
| 23 | `cf3611ec` | 2026-09-11 | Merge TASK-437: one wrong-root call site, and the reason it was inv... | 4 | 144 | 100.0% | tests/ helper (1) |
| 24 | `076ae21a` | 2026-09-11 | Merge spec-437 | 1 | 32 | 33.7% | — |
| 25 | `ce9041f0` | 2026-09-11 | Merge evidence-411: TASK-411's measurements, which existed only in ... | 1 | 32 | 33.7% | — |
| 26 | `9c30782a` | 2026-09-11 | Merge task-436-diagnose-dangling: one of four paths closed, and the... | 4 | 59 | 46.6% | — |
| 27 | `b5b7d023` | 2026-09-11 | Merge task-419-review-rounds-criteria: the exhaustion counter reads... | 5 | 92 | 68.1% | — |
| 28 | `6affdd38` | 2026-09-11 | Merge task-412-contract-snippets: three defects in a snippet nothin... | 3 | 144 | 100.0% | schema/ (1) |
| 29 | `89617487` | 2026-09-11 | Merge task-431-blank-cell: one blank-cell rule, nine sites not three | 13 | 144 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); tests/ helper (4) |
| 30 | `575f9dee` | 2026-09-11 | Merge task-421-scratch-collisions | 7 | 144 | 100.0% | tests/ helper (1) |
| 31 | `fef35967` | 2026-09-11 | Merge task-368-inproc-slice-1 | 10 | 144 | 100.0% | tests/ helper (1) |
| 32 | `292bce3e` | 2026-09-11 | Merge worktree-agent-afe8ae683f09b6754 | 1 | 32 | 33.7% | — |
| 33 | `4efc810f` | 2026-09-11 | Merge task-362-round11-review | 1 | 32 | 33.7% | — |
| 34 | `70458893` | 2026-09-11 | Merge specs-five-spinouts: specs for TASK-412, 419, 421, 431 and 436 | 5 | 32 | 33.7% | — |
| 35 | `fe0292fb` | 2026-09-11 | Merge evidence/task-239-result | 1 | 32 | 33.7% | — |
| 36 | `899f3ffd` | 2026-09-11 | Merge review/task-400-v4-round1 | 1 | 32 | 33.7% | — |
| 37 | `8e81e5ee` | 2026-09-11 | Merge task-426-restore-check | 2 | 19 | 17.3% | — |
| 38 | `1632095d` | 2026-09-11 | Merge task-411-declaration-both-ways | 2 | 144 | 100.0% | tests/ helper (1) |
| 39 | `7f43a11c` | 2026-09-11 | Merge task-362-blank-rung: done stamped a verification its own vali... | 3 | 82 | 56.4% | — |
| 40 | `ee3f46f6` | 2026-09-11 | Merge specs-348-368: specs for TASK-348 and TASK-368 | 2 | 32 | 33.7% | — |
| 41 | `583f024f` | 2026-09-11 | Merge bin-contract-phase-a: DESIGN-016's thirteen closed rows, and ... | 89 | 144 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); schema/ (3); tests/ helper (4) |
| 42 | `4ebc0693` | 2026-09-09 | Merge suite-cost-round3: TASK-400 to review, TASK-402 closed, DESIG... | 25 | 144 | 100.0% | tests/ helper (5) |
| 43 | `f2016f12` | 2026-09-08 | Merge suite-cost-round2: one shared helper, 21 modules, CPU 1278s t... | 2 | 144 | 100.0% | tests/ helper (1) |
| 44 | `fa2df316` | 2026-09-08 | Merge drop-projected-markdown: ADR-019, and four cuts at the suite'... | 137 | 144 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); schema/ (4); tests/ helper (26) |
| 45 | `724f91a5` | 2026-09-07 | Merge TASK-394: add --unlinked writes the declaration, and the KR d... | 8 | 144 | 100.0% | bin/lib/ (1); tests/ helper (1) |
| 46 | `26bcec72` | 2026-09-07 | Merge TASK-281 round 2: whitespace no longer inflates the KR, and t... | 4 | 144 | 100.0% | bin/lib/ (1) |
| 47 | `883d9d26` | 2026-09-07 | Merge ADR-017 step 3: 27 of 79 renamed, 52 deliberately left | 13 | 144 | 100.0% | tests/ helper (3) |
| 48 | `51c32095` | 2026-09-07 | Merge ADR-017 step 2: one grammar at both levels, in one commit | 21 | 41 | 40.5% | — |
| 49 | `4e88cd52` | 2026-09-07 | Merge TASK-278 round 3's V4: PASS, proved as a superset rather than... | 1 | 32 | 33.7% | — |
| 50 | `59e90e61` | 2026-09-07 | Merge TASK-281's V4: FAIL, and both defects reproduce in one comman... | 1 | 32 | 33.7% | — |

| share of module-seconds | merges |
|---|---|
| 0–10% | 0 |
| 10–25% | 1 |
| 25–50% | 16 |
| 50–99.9% | 3 |
| 100% (full) | 30 |

merges: 50 · median share: 100.0% · mean share: 75.1%
widening rule fired, merges: bin/lib/ 9, viewer/parsers.py 8, schema/ 10, tests/ helper 27
widening rule was the only one to fire, merges: bin/lib/ 1, schema/ 1, tests/ helper 17
VERDICT: FAIL — median share 100.0% > 50%; most frequent reasons: tests/ helper (27 merges), schema/ (10 merges), bin/lib/ (9 merges)

## What makes the selection wide — analysis, not rules

Measured with the same selector, declarations and stopwatch. The script lived in
scratch and is not committed. No rule was changed to take these numbers.

**1. `tests/durations.json` widens 20 of the 50 merges.** Among the 27 merges the
`tests/` helper rule widened, the helper paths were:

| helper path | merges |
|---|---|
| `tests/durations.json` | 20 |
| `tests/fixtures/**` | 9 |
| `tests/task_writer_support.py` | 3 |
| `tests/store_fixture.py` | 3 |
| `tests/parallel` | 3 |
| `tests/contract_key_parity.py`, `tests/inproc.py` | 2 each |
| seven other helpers | 1 each |

Counterfactual A treats `tests/durations.json` as a path matched through `COVERS`
rather than a helper. `test_durations_provenance`, `test_parallel_runner` and
`test_slow_selector` declare it. Under A the median is **76.0%**, the mean 68.8%,
and 23 of 50 merges are full. **The verdict is still FAIL.**

**2. A merge that widens nothing still selects a third of the suite.** 40 modules,
40.1% of module-seconds, declare `perry/` or `.perry/`, because they read this
repository's own state. They do so through a whole-tree copy
(`tests/pinned_phase.py`, `copy_of_perry`), `--root` at the checkout,
`tests/printed_board.py`, or a tool run in the checkout without `--root`.
`perry/evidence/` changed in 46 of the 50 merges, so an evidence-only merge
selects 32 modules, **33.7%**. That is exactly 14 of the 20 merges that did not
widen.

**3. `bin/perry-task` alone selects 80 modules, 56.0%.** It is wide on its own,
before any widening rule. The prefix also matches `bin/perry-tasks`.

Single-path floors, for scale:

| changed path | modules | share |
|---|---|---|
| `SKILL.md` | 21 | 7.0% |
| `perry/evidence/2026-09/x.md` | 32 | 33.7% |
| `bin/perry-task` | 80 | 56.0% |
| nothing | 1 | 0.0% |

The one-module row is the only `COVERS = ALL` module, `test_blank_cell_is_one_rule`
(0.08 s). Its assertion reads every file git tracks.

## For the redesign the gate calls for

Nothing is decided here. Each lever below is a change to `DESIGN-021 § 5.2` or
to the suite, and so is the user's decision. Measured, in order of effect:

1. **Live-state coupling.** 40 modules assert against this repository's own
   `perry/`, which nearly every merge changes. That coupling alone puts 14 of the
   narrow merges at 33.7%. The only way this selector can stop running them on
   every merge is for them to stop reading the live state root.
2. **The `tests/` helper rule's scope.** `tests/durations.json` is a scheduling
   hint that `tests/parallel` may never select by. Most of `tests/fixtures/**` is
   data a few modules read. Narrowing the rule is worth 24 points of median
   (counterfactual A) and still does not pass alone.
3. **Fan-in on `bin/perry-task`.** 80 modules name it as a subject. A change to
   it is wide by construction, and `schema/` and `bin/lib/` already widen on
   their own.
