# TASK-448 — result

> Branch: `coding/task-448-covers-and-replay` · base `bb178072` · Executor: claude-subagent
> Design: `DESIGN-021 § 5.2`, `§ 6` phase A · Replay: `TASK-448-replay.md`

## 1. Outcome

| Deliverable | State |
|---|---|
| 1. `COVERS` on every `tests/test_*.py` | 143 of 143 at base, plus `test_selection.py`. One declares `ALL`, with its reason on the line above |
| 2. `tests/selection.py` | § 5.2 as a pure function `select(changed, declarations)`, with a thin git layer |
| 3. `tests/run --tier affected --base <ref> --dry-run` | prints the selection and runs no test (§ 4) |
| 4. `tests/test_selection.py` | 34 tests: one or more per rule, plus the undeclared-module guard, which is empty |
| 5. The replay | **FAIL**: median share 100.0%, above the 50% gate (`TASK-448-replay.md`) |
| 6. This result | — |

**The gate did not pass.** Per `DESIGN-021 § 6` phase A, the selector is
redesigned before `TASK-449` switches any brief. The replay report measures
three levers; none of them is changed here.

## 2. Base check and baseline

- At dispatch HEAD was `0b5bf99e`, a strict ancestor of `bb178072`, with a clean
  tree. Fast-forwarded with `git merge --ff-only bb178072`, then created the
  branch.
- **Baseline at `bb178072`**, `env -u PERRY_PROJECT -u PERRY_HOME bash tests/run`:
  140 modules · 3934 tests · **2 modules red, 10 tests failed** · tree guard green.
  - `test_md_store` failed 9 tests, including
    `TestThisRepositoryIsReproducedByteForByte.test_okr`:
    `0 != 13 … a byte-identical render that dropped rows`.
  - `test_okr_krs_render` failed 1 test,
    `TestTheShippedOkr.test_the_shipped_okr_md_carries_no_kr_table_rows`:
    13 KR rows in `perry/OKR.md`.
  - Re-run alone, each module reproduced the same failures (9 of 76 and 1 of 40).
    Both assert against this repository's live `perry/OKR.md`/`okr.jsonl`, which
    `15369956` (OKR v4, the base's parent) rewrote. They are not attributable to
    this row.
- **With the declarations** (the tree committed as `eed48a88`), same command:
  141 modules · 3968 tests · **the same 2 modules and 10 tests red**, nothing
  else · tree guard green. The +1 module and +34 tests are `test_selection`.

## 3. Decisions the spec left to the implementation

Each of these errs toward selecting more, and each is written in
`tests/selection.py`'s docstring.

- **`ALL` does not count as matching a path for the unmatched rule.** If it did,
  one `ALL` module would switch that rule off for the whole suite.
- **`--no-renames`.** A rename reports the old and the new path.
- **A changed `tests/test_*.py` that no longer exists** selects nothing and does
  not widen.
- **"A `tests/` helper" is read literally**: every path under `tests/` that is not
  `tests/test_*.py`, including `tests/durations.json` and fixtures. This reading
  is the replay's largest single reason; the report gives the counterfactual.
- **Matching is a plain string prefix.** `bin/perry-task` also matches
  `bin/perry-tasks`.
- **`COVERS` is read with `ast` and never imported.** Anything but a non-empty
  tuple of relative path strings, or `ALL`, is refused (exit 2).
- **Only one `--tier` spelling is accepted.** `tests/run` accepts exactly
  `--tier affected --base <ref> --dry-run` and refuses every other `--tier` with
  exit 2 before anything runs. Before this row, an unknown first argument fell
  through to the whole suite. The dry run sits after the tree guard's snapshot
  and under its trap, so NN-5's "every exit path" still holds. On success it
  prints `✓ selection printed — no test ran` rather than `✓ all green`. Bare
  `tests/run`, `--lint`, `--serial`, `--only`, `--slow` and `tests/parallel` are
  untouched: the diff to `tests/run` adds a parse block guarded by `--tier`, one
  branch guarded by `$tier`, and one banner branch guarded by `$tier`.

**How the declarations were made.** A module declares the tool(s) and shared
files its assertions are about, and the prose or templates it asserts on. It
does not declare every tool it invokes. Where it reads this repository's own
state, it also declares `perry/` or `.perry/` (or the file). There are four such
routes: a whole-tree copy (`pinned_phase`, `copy_of_perry`), `--root` at the
checkout, `printed_board()`, or a tool run with `cwd` at the checkout and no
`--root`. The last was found by an AST scan of every `subprocess.run` whose cwd
names the checkout. Modules that walk the tree declare what the walk reaches:
`header_rule`'s reader walk and `test_one_choke_point`'s walk both include
`perry/`, where three `.py` files live.

## 4. Verification

**`python3 -m unittest tests.test_selection`** (and `tests/parallel
test_selection`): 34 tests, OK.

**Mutations.** Each ran on a fresh extraction of `git archive HEAD` under
`$PERRY_SCRATCH/mut/`, never in the checkout. Command:
`python3 -m unittest tests.test_selection`.

| Mutation | Result | Red on |
|---|---|---|
| control, unmutated | OK (34, 1 skipped: no `.git` in an archive) | — |
| remove the `bin/lib/` widening rule | FAILED (1) | `TestWideningRules.test_a_path_under_bin_lib_selects_the_full_suite` |
| a module without `COVERS` is not selected | FAILED (4) | `TestNarrowRules.test_a_module_with_no_covers_is_always_selected`, `…test_nothing_changed_selects_only_all_and_undeclared`, `…test_a_deleted_test_module_selects_nothing_and_does_not_widen`, `TestShareAndOutput.test_one_line_per_selected_module_with_its_rule` |
| delete `COVERS` from `tests/test_churn.py` | FAILED (1) | `TestTheLiveSuiteDeclares.test_no_module_is_without_covers`, whose message names `test_churn.py` |

No mutation stayed green. After all three, `git diff --quiet HEAD --
tests/selection.py tests/test_selection.py tests/test_churn.py` exited 0 in
the checkout.

**`bash tests/run --tier affected --base HEAD~1 --dry-run`** at `3da8ad1e`
(HEAD~1 = `eed48a88`, whose diff is `tests/durations.json`) exited 0. Excerpt;
the elided lines are the other 142 modules, one per line:

```
0. tree guard — recording …/agent-a4f6a808b611b5bf2
  · recorded

affected — what HEAD~1...HEAD selects (dry run)
tier affected · HEAD~1...HEAD · 1 changed path(s) · dry run, no test runs
  widened to the full suite — tests/ helper: tests/durations.json
  test_a_write_refuses_where_nothing_is_installed.py  full — tests/ helper: tests/durations.json
  …
  test_work_modes.py                                  full — tests/ helper: tests/durations.json
selected 144 of 144 modules · 1055.6 of 1055.6 module-seconds (100.0%)
this change is wide

0. tree guard — the tree the suite started in is the tree it ends in
  ✓ nothing under …/agent-a4f6a808b611b5bf2 moved

✓ selection printed — no test ran
```

`tests/test_selection.py § TestTheRunEntry` holds the same entry in a throwaway
repository. The dry run leaves a probe module's marker unwritten, and a control
`--only` run writes it. `--tier affected` without `--dry-run`, `--tier full`, and
`--tier affected --dry-run` without `--base` each exit 2 and run nothing.

**`tests/durations.json`** gained exactly one module entry, `test_selection.py`,
at 1.3 s (the median of 1.4, 1.2 and 1.3 s alone), under the stamped source
`2026-09-15-task448`. No other module was re-timed. `test_durations_provenance`
is green: 144 recorded, 144 on disk.

## 5. Findings

1. **The gate fails, and narrowing the helper rule alone would not pass it.**
   Counterfactual A reaches 76.0%. The structural floor is live-state coupling:
   40 modules read this repository's `perry/`, so any evidence-only merge costs
   33.7%.
2. **`COVERS` is a path prefix, not a file type.** The whole-tree Python walkers
   (`header_rule`, `test_one_choke_point`) are declared on the directories that
   hold Python today. A Python reader added under a prose-only prefix such as
   `packs/` would not select them. That path is matched by other modules, so the
   unmatched rule does not fire either. `full` at merge would catch it (§ 7,
   first risk).
3. **`ARCHITECTURE.md § 2` and its § 3 diagram say "136 modules"; the tree now
   has 144.** That is descriptive drift. The file is not in this row's scope, so
   it was not edited.
4. **Working notes.** The brief's scratch-derivation block, verbatim, was
   refused by this session's worktree guard because it contains `$(git …)`. The
   same path was used with its value spelled out:
   `${TMPDIR}/perry-scratch/agent-a4f6a808b611b5bf2`. Separately, `tests/selection.py`
   was briefly written into `tests/` while the baseline suite ran, and moved to
   scratch before that run ended. The tree guard was green, and both baseline
   reds reproduce alone, so the baseline is not affected.

---

# TASK-448 — round 2 (USER-940, 2026-09-16)

> Branch: `coding/task-448-covers-and-replay` · merged `main` at `ba11da7a`
> Commits: `586eb127` (merge), `cac39be0` (the two levers), plus this file

Round 1 above is unchanged and still describes what it measured. This section
records what `USER-940` asked for, what it moved, and what it did not.

## 1. What changed

**Lever 1 — `tests/durations.json` stops counting as a `tests/` helper.**
`tests/selection.py § STOPWATCH` exempts exactly that one path from the helper
rule, with the reason beside it: `tests/parallel`'s own rule is that the
stopwatch "may reorder the work, never select it", so a wrong one costs a worse
order and cannot change which modules run. It is matched through `COVERS`
instead — `test_durations_provenance`, `test_parallel_runner` and
`test_slow_selector` declare it. The exemption is one path, not a directory:
`tests/fixtures/durations.json` and `tests/durations.json.bak` are still
helpers, and `test_every_other_tests_path_is_still_a_helper` holds that. If a
day comes when no module declares the stopwatch, the unmatched rule widens on
it rather than letting it select nothing
(`test_the_stopwatch_still_widens_when_no_module_declares_it`).

**Lever 2 — seven wholesale declarations narrowed to the files actually read.**

| module | was | now reads, and declares |
|---|---|---|
| `test_asks_list` | `perry/`, `.perry/` | `perry/asks.jsonl`, `.perry/config.jsonl` — `perry-task asks --root <checkout>` |
| `test_board_from_declarations` | `perry/`, `.perry/` | the four `REGISTERS` stores it copies, and `.perry/config.jsonl` |
| `test_board_less_reads_and_writes` | `.perry/` | the six stores it copies, `.perry/config.jsonl`, `.perry/events.jsonl` |
| `test_board_names_its_sources` | `perry/`, `.perry/` | the stores `perry-tasks board` prints from, and `.perry/config.jsonl` |
| `test_live_state_expectations` | `perry/tasks.jsonl`, `.perry/` | nothing under `perry/` — every `perry/` path in it is inside a planted fixture source string, not a read |
| `test_risks` | `perry/`, `.perry/` | the stores behind `printed_board()`, and `.perry/config.jsonl` |
| `test_task_writer_core` | `perry/`, `.perry/` | the same store set behind `printed_board()` |

`perry/cadence.jsonl` was dropped from three of these before landing: the store
does not exist in this repository, and a prefix naming nothing fails
`test_every_prefix_names_something_in_the_repository`.

**Twenty-six modules kept the broad declaration.** Each reads the whole state
root rather than a file of it, by one of four routes: a `pinned_phase` copy or
`copy_of_perry`; a `copytree` of `perry/` and `.perry/`; a tool run at the
checkout with no `--root` (`perry-task list`, `perry-lint --json`,
`perry-explain`, `perry-diagnose`, `inproc.run`), which resolves paths across
the whole project; or a whole-tree Python walk. `TASK-448-replay.md` lists all
26 with the reason for each. Narrowing them is not a declaration change — it
means moving a module off the live state root, pinning a copy, or giving a tool
a `--root`, and `USER-940` holds all three. **That list is the measurement the
next decision rests on.**

**Also folded in.** `main` merged at `ba11da7a`, conflicting only in
`tests/durations.json`'s sources block, where both stamps were kept.
`tests/test_architecture_rules.py` (TASK-453) declares `ARCHITECTURE.md`,
`bin/`, `viewer/` and `tests/run`: it reads the root and module architecture
documents, walks `bin/` and `viewer/` for imports and shebangs, runs
`bin/perry list --json`, and reads `tests/run` for S4. `tests/test_next_section.py`
(TASK-442) is not in the tree and is not covered.

## 2. The replay, re-run

Same base, same 50 merges, same method and stopwatch.

| | round 1 | round 2 |
|---|---|---|
| median share | 100.0% | **75.9%** |
| mean share | 75.1% | 67.9% |
| merges widening to `full` | 30 of 50 | 23 of 50 |
| evidence-only floor | 32 modules · 33.7% | 27 modules · 31.6% |
| verdict | FAIL | **FAIL** |

Most frequent reasons, in merges: `tests/` helper 19 (was 27), `schema/` 10,
`bin/lib/` 9, `viewer/parsers.py` 8. The helper rule now fires on
`tests/fixtures/**` (9 merges) ahead of anything else; unlike the stopwatch,
those are data modules genuinely read.

**The gate is still not met**, so phase A still blocks `TASK-449`. The report's
last section sets out what the remaining 25.9 points sit in: 23 merges are
already `full` before any `COVERS` is consulted, and the rest sit near the
31.6% floor that the 26 broad modules set.

## 3. Verification

- **`python3 -m unittest tests.test_selection`**: 38 tests, OK (34 in round 1
  plus four for the stopwatch rule).
- **Mutations**, each on a fresh `git archive HEAD` extraction under
  `$PERRY_SCRATCH/mut2/`, never in the checkout:

| Mutation | Result | Red on |
|---|---|---|
| control, unmutated | OK (38, 1 skipped: no `.git` in an archive) | — |
| the stopwatch widens again (lever 1 removed) | FAILED (3) | `TestWideningRules.test_the_stopwatch_is_not_a_helper_and_selects_by_covers`, `…test_the_stopwatch_still_widens_when_no_module_declares_it`, `TestTheLiveSuiteDeclares.test_the_live_suite_declares_the_stopwatch` |
| remove the `bin/lib/` widening rule (round-1 rule) | FAILED (1) | `TestWideningRules.test_a_path_under_bin_lib_selects_the_full_suite` |
| a module without `COVERS` is not selected (round-1 rule) | FAILED (4) | `TestNarrowRules.test_a_module_with_no_covers_is_always_selected` and three others |

  No mutation stayed green. Afterwards `git diff --quiet HEAD` exits 0 and
  `git status` is empty in the checkout.
- **The full suite** at `cac39be0`, `env -u PERRY_PROJECT -u PERRY_HOME bash tests/run`:
  142 modules · 4004 tests · **1 module red, 8 tests failed**, tree guard
  green. That module is `test_md_store`, which reproduces alone (8 of 76) and
  asserts against this repository's live `perry/OKR.md`. It is the base red the
  PMO predicted for this branch after `main` merged; `test_okr_krs_render`, red
  in round 1, is green since main's `OKR.md` fix (`06e437ba`). Round 1 measured
  the same module red at 9 of 76 on the older `OKR.md`.
- **The dry run** at the round-2 tree: `bash tests/run --tier affected --base HEAD~1 --dry-run` at
  `cac39be0` exited 0, ran no test, and printed
  `widened to the full suite — tests/ helper: tests/selection.py` over 11 changed
  paths: `selected 145 of 145 modules · 1056.4 of 1056.4 module-seconds (100.0%)`,
  then `this change is wide` and `✓ selection printed — no test ran`. The selector
  widening on its own source is the helper rule working: `tests/selection.py` is a
  helper, and the stopwatch exemption is one path, not the directory.

## 4. Findings

1. **The two levers are worth 24.1 points of median and do not reach the gate.**
   Lever 1 alone accounts for most of it; lever 2 moved the evidence-only floor
   by 2.1 points, because 26 of the 33 broad modules could not be narrowed by
   declaration.
2. **The floor is now the binding constraint.** `perry/evidence/` changes in 46
   of 50 merges, and it selects 27 modules through declarations that are
   accurate: those modules really do read the whole state root. No further
   honest narrowing is available without the decisions `USER-940` holds.
3. **`tests/fixtures/**` is the next helper-rule question**, worth 9 of the 19
   remaining helper widenings — but a fixture is read by the modules that use
   it, so it has no "reorders but does not select" argument behind it.
