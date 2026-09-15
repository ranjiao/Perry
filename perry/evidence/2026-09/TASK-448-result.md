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
