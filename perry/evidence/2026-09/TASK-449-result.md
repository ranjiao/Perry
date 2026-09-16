# TASK-449 — result

> Row: DESIGN-021 phase B — tests run in tiers, and the briefs switch to smoke plus affected
> Branch: `coding/task-449-test-tiers` · Base: `dd129bca` (main's tip at dispatch)
> Commits: `c71e9585` (the tiers and the briefs), `b23cc488` (the stopwatch entry), plus this file
> Written 2026-09-16 by the Coding Agent.

## 1. Base check

The worktree's HEAD was `0b5bf99e`, a strict ancestor of `main` at `dd129bca`,
with a clean tree, so it was fast-forwarded to `dd129bca` and branched from
there. That is the case the brief describes; it is reported because "I checked
and it was fine" and "I did not check" are different answers.

`perry/evidence/2026-09/TASK-449-spec.md` is untracked in the primary checkout
and therefore absent from this worktree; it was read from the primary
checkout's path and is **not** carried on this branch. Nothing here cites it as
a file on the branch.

**Baseline reds: none.** Main is fully green and stayed green; the `--tier
affected --base main` run at the end of round 1 was 144 modules / 4,088 tests /
0 red.

## 2. What changed

Eight files, 1,028 insertions.

### `tests/selection.py` — one implementation of what a tier contains

`tier_modules(tier, on_disk, slow, sel)` is a pure function and `plan()` is the
thin git-backed wrapper around it. Both `tests/run` and `tests/parallel` read
their module set from here, so **the set that is printed and the set that runs
cannot drift apart** — the divergence mutation 1 plants.

| tier | modules |
|---|---|
| `smoke` | none. Its checks are `tests/run`'s steps 1 and 3 and the tree guard's hash check, none of which is a `unittest` module |
| `affected` | what `select()` picked, minus the slow tier's |
| `full` | every module on disk except the slow tier's — today's bare `tests/run` |
| `slow` | every module on disk — today's `tests/run --slow` |

The slow tier's membership is `tests/parallel § HARNESS_SELF_TESTS`, imported,
never re-declared.

**`affected` subtracts the slow tier, and prints what it subtracted.** This is
the one judgement in the row that the spec did not settle, and it is forced:
`select()` reads every module on disk, so a change that widens to the full
suite selects all 147 — `test_tree_guard.py`'s 62.5 s included. Running that as
`affected` would make the cheap tier *more expensive than `full`*, inside an
executor's iteration loop. Dropping them silently would be the other half of
mutation 1, so the drop is a printed line:

```
  held back — test_tree_guard.py is the slow tier's (tests/parallel §
  HARNESS_SELF_TESTS): run `bash tests/run --tier slow`
```

`_parallel()` now caches the loaded runner per root, because two callers read
constants out of it and exec'ing the file twice is waste inside smoke's budget.

### `tests/run` — the four tiers

```
bash tests/run --tier smoke                    # steps 0, 1, 3
bash tests/run --tier affected --base <ref>    # + what the change selects
bash tests/run --tier full                     # what bare `tests/run` runs
bash tests/run --tier slow                     # what `--slow` runs
… --dry-run                                    # print the selection, run nothing
```

**`full` and `slow` are spellings, not copies.** `--tier full` sets no variable
this script branches on, and `--tier slow` sets only `slow`, so bare
`tests/run` and `--tier full` reach step 2 through the same `else`, and
`--tier slow` through the same branch `--slow` has always taken. That is the
only way to keep a spelling honest: a parallel code path agrees today and
drifts tomorrow. `--lint`, `--serial`, `--only` and `--slow` are untouched.

Refusals, all before the guard and before step 1: an unknown tier;
`--tier affected` with no `--base`; `--base` passed to any other tier
(accepted-and-dropped is a defect, `DESIGN-016` goal 12); an unknown argument
after the tier.

**Every tier runs inside the tree guard, dry runs included** (`NN-5`). Step 4 —
the two sample-project lints — is not one of § 5.1's three smoke checks, so
`smoke` and `affected` skip it *and say so*, the same way `--only` does.

The green banner for `smoke` and `affected` is
`✓ green for --tier <name> — this is NOT a green suite`. `full` and `slow` keep
`✓ all green`.

### `tests/parallel --tier <name> [--base <ref>]`

Reads its module set from `tests/selection.py`; prints the selection and the
rule that picked each module *before* it runs them (§ 2 goal 6). `--record`,
`--times` and `--slow` keep their behaviour and `--record` still runs the whole
tree, always.

It **refuses** to combine `--tier` with `--slow`, `--record` or a positional
prefix, rather than picking a winner; refuses `--base` without a tier; and
refuses `--tier smoke` outright, because accepting it would print
`0 modules · 0 tests · ✓ all green`, which is a green from a run that verified
nothing (`NN-3`). The refusal names the remedy: `bash tests/run --tier smoke`.

### `tests/test_tiers.py` — 40 cases, new module

A minimal tree is built (not archived) whose tree guard, `perry-lint` and
`tests/parallel` are stubs that record the argv they were handed, so each run
of `tests/run` yields a **trace** — step banners, guard calls, runner argv —
and "bare run == `--tier full`" is asserted as a comparison of two runs rather
than of two lines of source. `tests/test_selection.py`'s phase-A case
"only the dry run exists" is rewritten to what is left to refuse: a tier that
cannot be planned.

### The two brief pages

Quoted in full in § 6.

### `tests/durations.json`

One new entry, `test_tiers.py` at 10.58 s, timed alone three times
(10.61/10.57/10.58 at `-j 1`) under a new source entry that says what was
measured and that no neighbour was re-timed. Without it `tests/parallel`'s own
audit reports the module as unaccounted for and it sorts as `inf`. No existing
module moved by 0.5 s, so none was re-timed.

## 3. Verification

### 3.1 The full suite on the final commit

`PERRY_PROJECT` and `PERRY_HOME` are unset in this session (checked, both
empty).

| command | modules | tests | red | step-2 wall | total wall |
|---|---|---|---|---|---|
| `bash tests/run` | 144 | 4088 | 0 | 264.2 s | 4 m 27 s |
| `bash tests/run --tier full` | 144 | 4088 | 0 | 159.5 s | 2 m 42 s |

**The same module and test counts**, which is what "bare `tests/run` becomes
`--tier full`" has to mean at the level of what ran. The wall difference is the
machine: `load1` was 30 when `--tier full` ran and past 50 when the bare run
did, and § 3.3 below measures that same 2× swing directly.

Ordering: the table's bare run was taken with this file present but not yet
committed. The suite was then run **again on the final commit**, after this
file was committed, and that run is recorded in § 3.6 — so the number above is
reproducible and the final commit is the one that was verified.

### 3.2 `bash tests/run --tier smoke` — against the 30-second budget

Green. Three consecutive runs: **2.64 s / 1.89 s / 1.93 s**, median **1.93 s**,
against a budget of 30 s — measured at `load1 54.4`, this machine carrying
other sessions' work. It fits with an order of magnitude to spare.

### 3.3 `bash tests/run --tier affected` — against the 60-second median

For this row's own change, `--base main`:

```
selected 147 of 147 modules · 964.0 of 964.0 module-seconds (100.0%)
  widened to the full suite — tests/ helper: tests/parallel
  held back — test_durations_provenance.py is the slow tier's …
  held back — test_parallel_runner.py is the slow tier's …
  held back — test_tree_guard.py is the slow tier's …
this change is wide
144 modules · 4088 tests · 166.4s · 8 workers — 0 red
```

A change that edits `tests/parallel` widens to the full suite by § 5.2's
helper rule, which is the rule working, not a miss. Total wall 174 s.

A narrow control, `--base HEAD~1` at the branch point: **41.1 s** wall for the
whole `tests/run --tier affected` invocation, 29 of 146 modules, 991 tests,
27.6% of module-seconds, 0 red.

**The median across six recent single-commit bases.** Each base is one commit's
own diff (`R^...R`); the selection is run in this worktree at 8 workers. The
column is the runner's wall; `affected` adds smoke's ~2 s on top.

| # | base | subject | modules | parallel wall |
|---|---|---|---|---|
| 1 | `f7bc10fa` | TASK-448 round 3: the result records the conversions | 19 | 42.3 s |
| 2 | `79a660cb` | TASK-442 round 6: the suppression pin follows the page | 23 | 53.2 s |
| 3 | `eb1a9db0` | TASK-448 round 3: the replay report | 19 | 112.1 s |
| 4 | `fb5c6388` | TASK-442 round 6: the result records the correction | 19 | 83.5 s |
| 5 | `5eba50eb` | TASK-442 round 6: the sunset line | 17 | 18.4 s |
| 6 | `c890d8d6` | TASK-448 round 3: the decoration fixture | 5 | 8.3 s |

**Median 47.8 s, plus ~2 s of smoke ≈ 50 s — inside the 60-second budget.**
Every one of the six was green.

**And the finding the table carries, which is not the median.** Two of the six
exceed 60 s, and the spread is **not** the selection: bases 3 and 4 select 19
modules each, exactly as base 1 does, and cost 2.0× and 2.6× what base 1 cost.
Re-measured later in the same session, base 3 came back at **65.7 s** (was
112.1) and base 4 at **103.2 s** (was 83.5), with `getloadavg()[0]` moving from
30.3 to 50.0 across the two runs. That is DESIGN-021 § 1.1's and § 4's measured
machine noise — single measurements swinging by 2× — landing on the `affected`
budget exactly as § 7 predicts it will land on the ratchet. **The 60-second
budget is met at the median and is not met on a loaded machine**, and no tier
was trimmed to make it fit. Phase D's "report at merge, fail only at phase
close on a quiet re-record" is the right shape for this number too.

### 3.4 `bash tests/run --tier slow` — nothing lost against `--slow`

| command | modules | tests | red |
|---|---|---|---|
| `bash tests/run --slow` | 147 | 4176 | 0 |
| `bash tests/run --tier slow` | 147 | 4176 | 0 |

Identical, and 3 modules and 88 tests more than `full` — the three
`HARNESS_SELF_TESTS`. `tests/test_tiers.py § test_slow_and_tier_slow_are_the_same_run`
holds it as a trace comparison as well as a count.

### 3.5 Mutations

Each on a fresh `git archive` copy of the branch under
`$TMPDIR/perry-scratch/agent-a47efed2087a66999/`, never in the checkout. The
control — the same module in an unmutated copy — was green first (40/40).

| # | mutation | file · line | red on |
|---|---|---|---|
| 1 | `--tier affected` runs the full set instead of the selection: `mods = list(tier_plan.modules)` → `mods = [m for m in all_mods if m not in HARNESS_SELF_TESTS]` | `tests/parallel:827` | `test_tiers.TestTheParallelRunnerTakesTheSameNames.test_tier_affected_asks_for_the_selection_and_not_the_tree`, and `…test_tier_slow_asks_for_the_whole_tree` — 2 failures |
| 2 | `--tier smoke` skips the tree guard: a smoke fast path inserted before `GUARD_MANIFEST=` that runs the lint and the scripts and exits | `tests/run:229` | `test_tiers.TestEveryTierRunsInsideTheTreeGuard.test_each_tier_snapshots_and_verifies` (`--tier smoke`, and `--tier smoke --dry-run`), `…test_a_red_guard_reddens_a_smoke_run`, plus 3 more — 6 failures |
| 3 | bare `tests/run` diverges from `--tier full`: the step-4 gate `[ "$tier" = "smoke" ] \|\| [ "$tier" = "affected" ]` → `[ -n "$tier" ]`, so `--tier full` skips step 4 | `tests/run:349` | `test_tiers.TestBareRunAndFullAreTheSameRun.test_the_two_runs_are_step_for_step_identical` (`steps`, `lint`) and `…test_slow_and_tier_slow_are_the_same_run` — 4 failures |

**No mutation came back green.** The three mutated copies are scratch trees;
the working tree was never mutated and `git status --porcelain` was empty
before and after each round, so there is no restore to verify against
`git show`.

### 3.6 The full suite on the final commit

Recorded by the commit that carries this line: `bash tests/run` on the branch
tip, `PERRY_PROJECT` and `PERRY_HOME` unset.

> **144 modules · 4088 tests · 0 red · `✓ all green`**

## 4. The budgets, in one place

| tier | budget | measured | verdict |
|---|---|---|---|
| `smoke` | ≤ 30 s | 1.93 s median of 3 | **met**, by 15× |
| `affected` | median ≤ 60 s | ≈ 50 s median of 6 bases | **met at the median**; 2 of 6 bases exceeded it, and the cause is machine load, not selection (§ 3.3) |
| `full` | — | 159.5–165.2 s | — |
| `slow` | not budgeted | 132–171 s | — |

## 5. What the spec left open, and what I decided

1. **`affected` vs the slow tier.** Subtracted, and the subtraction is printed
   (§ 2). Left unsubtracted, a widened `affected` runs more than `full`.
2. **`tests/parallel --tier smoke` is refused, exit 2**, with the remedy named.
   The alternative is `0 modules · 0 tests · ✓ all green`. The spec asks the
   runner to take "the same four names"; it takes the name and answers it,
   rather than producing a green over a run of nothing.
3. **An empty `affected` selection is refused, exit 2** by the runner, for the
   same reason. It is reachable only with an empty diff, since any unmatched
   path widens to `full`.
4. **`--tier` refuses to combine with `--slow`, `--record` or a prefix**, and
   `--base` is refused outside `--tier affected`, rather than accepted and
   dropped.
5. **Step 4 is not in smoke**, so not in `affected`. § 5.1 lists three things
   in smoke and the sample-project lints are not among them. Both tiers print
   that step 4 was skipped.
6. **The green banner is qualified** for `smoke` and `affected`. § 5.5's "a
   green in affected is not a green suite" is a sentence in two documents; the
   last green line of the run is where a reader actually takes the claim from.
7. **A new module, `tests/test_tiers.py`**, rather than more cases in
   `test_selection.py`: the spec allowed either, and the tier tests are about
   `tests/run`'s steps rather than about the selector.
8. **`--dry-run` for `full` and `slow` prints a count, not 143 lines.** Their
   membership is "everything on disk", which no reader needs enumerated.
9. **The spec file is not committed to this branch** (§ 1).

## 6. The two brief changes, quoted

### `work/reference/dispatch.md` — new section, `## What the executor runs each round (DESIGN-021 § 5.5)`

> **The brief tells the agent to run `bash tests/run --tier affected --base <the
> pinned base SHA>` at the end of every round, and to paste the printed
> selection block into its result.** Not the whole suite: the whole suite is 964
> module-seconds, and an executor that pays it on every round pays it four or
> five times for a change that touches a handful of modules.

The sentence that goes in the prompt, and it goes in whole:

```
Run `bash tests/run --tier affected --base <base SHA>` at the end of every
round. It runs the smoke checks — the schema drift guard, every shipped script
compiling and answering --help, and the tree guard — plus the test modules
your change selects, and it prints which modules it selected and the rule that
selected each. Paste that selection block into your RESULT.

A red in `affected` is a red: fix it before you report.
A green in `affected` is NOT a green suite. It ran the modules your change
selects and nothing else, so it cannot tell you that the rest of the suite
still passes. Say "green for --tier affected" in your result, never "the suite
is green", and quote the module count you actually ran.
```

> **Where the full suite runs today, stated plainly because the alternative is a
> gap nobody is watching.** There is **no automatic merge gate**: `TASK-450`
> builds it and it is not built. Until it lands, **the primary checkout runs
> `bash tests/run` itself on the merge result, before `git merge --no-ff`**, and
> that run — not the agent's `affected` run — is what says the suite is green.
> An agent's green `affected` is a reason to merge-check, never a substitute for
> it.

The section also names the other three tiers, says bare `tests/run` is
unchanged and still means `--tier full`, and says a miss is a `COVERS` entry to
add rather than a tier to widen. A paragraph under `## RESULT block format`
says to write the command as typed and the count as
`green for --tier affected (N of M modules)`.

### `work/reference/review.md` — new section, `### What the reviewer runs (DESIGN-021 § 5.5)`

> **The round runs `bash tests/run --tier affected --base <the same base SHA the
> author was pinned to>`, and its own mutations on top of that.** The same base,
> because a reviewer diffing against a different ref selects a different set and
> then reports a coverage gap that is an artifact of its own invocation.
>
> It prints one line per selected module and the rule that selected it. **Check
> that block is in the author's result**, the way the base SHA is checked today:
> a result with no selection block did not run a tier, and what it ran is then
> unknown. A mutation round re-runs the tier after each mutation — that is the
> point of a 40-second loop — and a mutation that comes back green is a finding,
> rule 2, whatever the tier.
>
> **A red in `affected` is a red. A green in `affected` is not a green suite**,
> and a verdict may not say it is. It ran the modules the change selects; it says
> nothing about the other hundred. If the change the round is reviewing could
> break a module the selector did not pick, that is worth `--tier full` — and
> worth saying so under `not checked:`, which rule 4 requires anyway.
>
> **There is no merge gate yet.** `TASK-450` builds it. Until then the full suite
> runs in the primary checkout, by hand, on the merge result before the merge —
> so a reviewer that assumes something downstream will catch what `affected`
> missed is assuming a mechanism that does not exist.

## 7. Out of scope, untouched

`bin/`, `viewer/`, `schema/` — not touched. The merge gate (`TASK-450`), the
ratchet (§ 5.4), the slow tier's membership (phase E), `TASK-312` and
`TASK-401` are other rows, and nothing here claims any of them exists.
`tests/selection.py`'s selection rules are unchanged: `select()`, `widening()`,
`WIDE` and `STOPWATCH` are as phase A left them, and every case in
`tests/test_selection.py` that asserts a rule still passes unedited.

## 8. Subjective verification (the user's)

- [user-verify] Read `work/reference/dispatch.md § What the executor runs each
  round`: is what the executor is told to run unambiguous in one reading?
