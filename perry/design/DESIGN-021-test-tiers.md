# DESIGN-021: Every round runs the whole suite, and nothing stops it getting slower

> Status: locked
> Date: 2026-09-15 · Locked: 2026-09-15
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: —
> Supersedes: —   · Superseded by: —
> Revisits: `tests/run`, `tests/parallel`, `tests/merge-check`, `tests/durations.json`, `tests/test_durations_provenance.py`, `work/reference/dispatch.md` (the brief and the merge steps), `work/reference/review.md`, `goals/reference/phases.md § score-phase`, `perry/decisions/ADR-018-verification-is-calibrated-to-blast-radius.md § C`
> Sign-off: User Decisions 1–5 answered by Ran Jiao in session on 2026-09-15. Moved `draft` → `locked` without an `in_review` hold, as `DESIGN-013`, `DESIGN-014` and `DESIGN-020` did. The lock-time `reference/input-quality.md § 3` pass raised 3.6 (unlisted surfaces: `tests/test_durations_provenance.py`, `phases.md § score-phase`, the dispatch merge steps) and an undated measured number (§ 5.1's ≈ 150 s); both were fixed before lock at the user's choice — the Revisits line, § 7's new row, and § 5.1.

## 1. Problem

**Perry's suite has one size: all of it.** Every executor round and every review
round runs it, and nothing records whether the next change made it slower.

### 1.1 The cost, and its trend

Measured 2026-09-15 from `tests/durations.json` (each module timed alone,
`sec`) and its git history:

- **141 timed modules, 1,054.3 module-seconds** (17.6 minutes serial). The ten
  slowest carry 33.8% of it; seven modules take ≥ 30 s, and `test_tree_guard.py`
  alone takes 62.5 s (`TASK-312`).
- **The trend.** 1,850–1,874 module-seconds from 2026-09-02 to 09-07; a one-off
  cut to 1,284.7 on 09-08 and 1,018.7 on 09-09, when `TASK-400` moved the
  harness self-tests behind `--slow`. Then the creep resumed: **1,054.3 on
  09-15, +3.5% in six days, with 16 more modules.** A cut is not a mechanism.
- **Wall clock.** `tests/parallel` records that on 2026-08-30 the suite of 99
  modules took 589.6 s serial and a median 149.7 s across 8 workers on a loaded
  machine. On 2026-08-28 two dispatches were killed by a 600-second no-progress
  watchdog at the moment they started the suite.
- **The bookkeeping is itself a cost.** 48 commits since 2026-09-01 touch
  `tests/durations.json`, most of them re-timing one or two modules by hand.

### 1.2 How it is run

`tests/run` offers everything, `--lint`, `--serial`, `--only PREFIX` and
`--slow`; `tests/parallel` adds `-j`, `--times` and `--record`. There is no tier
and no selection by change. In `perry/evidence/2026-09/`, 126 files cite
`tests/run` and 62 cite `tests/parallel`; result files quote whole-suite totals
("141 modules / 3998 tests / 0 red"). The full suite is the default at every
step, so it is paid at every step.

### 1.3 Why "run only what changed" is not free here

Measured by counting which `bin/` tools each test module's source names
(lexical, 143 modules):

| Tools named | Modules |
|---|---|
| 0 | 3 |
| 1 | 4 |
| 2–3 | 52 |
| ≥ 4 | 84 |

`perry` is named by 140 modules, `perry-task` by 95, `perry-state` by 75,
`perry-lint` by 74. 129 modules mention a prose path and 54 mention
`viewer/parsers.py`. **A selector that maps a changed tool file to every module
naming it selects most of the suite for most changes.** The mapping has to come
from what a module is *for*, stated by its author, and whether that is narrow
enough is a measurement this design takes before anything switches over.

### 1.4 What is already decided around it

`ADR-018 § C` classified the suite: 74.9% behaviour and 23.9% convention by
lines, about 15% of module-seconds convention. Deleting tests is a separate user
decision and stays one. `tests/merge-check` already runs the suite on a merge
result and attributes a red to a change or a pair.

## 2. Goals

1. **An executor's iteration loop never runs the full suite.** It runs the
   smoke tier and the tests selected for its change, with a median wall time of
   60 s or less on this machine (the number is confirmed by § 6 phase A).
2. **The full suite runs exactly once per change, before it merges to `main`,**
   on the merge result (decision 1).
3. **The suite cannot get slower without somebody deciding it may.** A module
   over its cap, or a total over budget, is reported with the exception it
   needs.
4. **Selection is deterministic and errs toward running more.** A changed path
   no module declares selects the full suite; selection compares paths and
   judges no meaning (`ARCHITECTURE.md § 6` NN-4).
5. **Durations are recorded by the merge, not by each task commit.**
6. **Every run prints what it selected and why**, so a reviewer can check what
   actually ran.

## 3. Non-Goals

- **No third-party runner or plugin** (pytest-xdist, coverage.py). Standard
  library only, like everything else.
- **No deleting tests.** `ADR-018 § C` keeps that a user decision.
- **No weakening `tests/tree_guard.py`** to buy speed. NN-5 runs on every exit
  path of every tier.
- **No coverage-guided selection.** Line coverage would need instrumentation
  Perry does not have and a store of results it does not want; declared
  coverage is enough to test the idea.
- **No server-side CI changes.** What a remote CI runs is § 8's question.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Where the full suite runs | Before every merge to main / at phase close / daily | **Before every merge to main** | 2026-09-15 |
| 2 | How a module declares what it covers | Module-level COVERS constant (Recommended) / one central manifest / derived from names in the source | **Module-level COVERS constant** | 2026-09-15 |
| 3 | What the executor loop runs | Smoke + affected (Recommended) / smoke only / affected only | **Smoke + affected** | 2026-09-15 |
| 4 | The runtime ratchet | Total budget + 30 s module cap, exception by ask (Recommended) / warn only / module cap only | **Total budget + 30 s module cap, exception by ask** | 2026-09-15 |
| 5 | Where convention guards run | Slow tier (Recommended) / affected tier as today / decide with ADR-018 § C | **Slow tier** | 2026-09-15 |

**On 1.** Answered by Ran Jiao in session, 2026-09-15, with `DESIGN-017`'s
reversed decision 1: the structural architecture rules run in this suite, so
this is also where they are enforced.

**On 2.** A constant beside the tests is edited in the same change as the tests,
which is when its author knows what the module is for. A central manifest is a
second place to keep in step. Deriving from names in the source is § 1.3's
measurement, and it selects nearly everything.

**On 3.** Smoke alone misses the change's own regressions until merge, which
turns every red into a late one. Affected alone skips the checks that are cheap
and catch the most common breakage (a script that no longer compiles).

**On 4.** Machine load has swung single measurements by 2× (`tests/parallel`),
so a hard total at merge would be flaky. The recommendation reports at merge and
fails at phase close, on a quiet re-record.

**On 5.** Convention guards cost about 15% of module-seconds and change rarely.
Running them when the prose or harness they guard changes — and at phase close —
keeps them without paying for them on every behaviour change.

## 5. Architecture

### 5.1 Four tiers

| Tier | Contains | Who runs it, when | Budget |
|---|---|---|---|
| **smoke** | `perry-lint --templates`; every shipped script compiles and answers `--help`; `tests/tree_guard.py`'s hash check (not its self-tests) | every commit | ≤ 30 s wall |
| **affected** | modules selected by the change (§ 5.2), plus `smoke` | the executor every round; the reviewer, with its mutations | median ≤ 60 s wall |
| **full** | every module except `slow` | the primary checkout, on the merge result, before `git merge --no-ff` (decision 1) | ≈ 150 s wall as measured 2026-08-30 on 99 modules (`tests/parallel`); re-measured in phase A on today's 141; ratcheted |
| **slow** | `HARNESS_SELF_TESTS` (`tests/parallel`), convention guards (decision 5) | at phase close, and whenever a selected change touches `tests/` harness files or shipped prose the guards cover | not budgeted |

Entry: `tests/run --tier smoke|affected|full|slow [--base <ref>]`, with
`tests/parallel` accepting the same `--tier` and `--base`. Today's bare
`tests/run` becomes `--tier full`, so nothing that calls it changes meaning.

### 5.2 Selection

Each test module declares what it is for (decision 2):

```python
COVERS = ("bin/perry-task", "bin/lib/linkage", "schema/state-schema.json")
# or, for a module that genuinely guards everything:
COVERS = ALL
```

`affected` for a base ref:

1. `git diff --name-only <base>...HEAD` gives the changed paths.
2. A changed `tests/test_*.py` selects itself.
3. A changed path that is a prefix match of a module's `COVERS` selects that
   module.
4. **Widening rules, checked first**, each selecting `full`: a changed path under
   `bin/lib/`, `viewer/parsers.py`, `schema/`, or a `tests/` helper that is not a
   `test_*.py`; any changed path that no module's `COVERS` matches.
5. A module with no `COVERS` is always selected, so an undeclared module makes
   runs slower, never unsafe. A guard lists undeclared modules and the list may
   only shrink.

The run prints one line per selected module and the rule that selected it, and
when the selection exceeds half the suite's module-seconds it says *this change
is wide* and runs it anyway.

Prose changes select the shipped-prose guards (`test_shipped_vocabulary`,
`test_pointers_resolve`, `test_router_budget`, `test_ownership`), which declare
`COVERS` on the prose globs — not every module that happens to mention a path.

### 5.3 The merge gate

Before merging a branch, the primary checkout runs `tests/merge-check` for that
one candidate against `main`'s tip: `--tier full` on the merge result. Green →
`--record` refreshes `tests/durations.json` in the merge commit, so no task
commit re-times modules by hand again. Red → the existing attribution names
whether the red is pre-existing, the candidate's, or an interaction. `DESIGN-017
§ 5.2`'s architecture rules run here as part of `full`.

### 5.4 The ratchet (decision 4)

`tests/durations.json` gains a `budget` block:

```json
"budget": {"total_sec": 1054, "module_sec": 30,
           "exceptions": {"test_tree_guard.py": "USER-NNN — why it may exceed"}}
```

- **At merge:** a module whose recorded time exceeds `module_sec` with no
  exception, or a total above `total_sec` by more than the noise margin, is
  reported in the merge evidence. It does not block the merge.
- **At phase close:** a quiet re-record runs; the same conditions fail. Raising a
  budget or adding an exception is an ask, answered by the user.
- `total_sec` starts at today's 1,054 and is lowered, never raised, when a phase
  closes under it.

### 5.5 What each role is told

| Role | Runs | Written in |
|---|---|---|
| Executor | `--tier affected --base <pinned base>` each round; the printed selection in its result | `work/reference/dispatch.md` brief |
| V4 reviewer | `--tier affected` plus its mutations, on the same base | `work/reference/review.md` |
| Primary checkout | `tests/merge-check --tier full` before merge; `--record` | `work/reference/dispatch.md § merge` |
| Phase close | `--tier slow` and the ratchet's re-record | `goals/reference/phases.md § score-phase` |

## 6. Implementation plan

| Phase | Scope | Proposed PMO task(s) | Owner |
|---|---|---|---|
| A | `COVERS` on every module; `--tier affected --dry-run`; replay the last 50 merges to `main` through the selector and report the selected share of module-seconds per merge. **The gate:** if the median share is above half, the selector is redesigned before any brief changes | TASK-NNN (new) | Coding Agent |
| B | The four tiers in `tests/run` and `tests/parallel`; bare `tests/run` = `full`; executor and reviewer briefs switched | TASK-NNN (new) | Coding Agent |
| C | The merge gate in the primary checkout's procedure, with `--record` at merge | TASK-NNN (new), `TASK-238` | Coding Agent |
| D | The ratchet block, its report at merge and its failure at phase close | TASK-NNN (new) | Coding Agent |
| E | The slow tier's membership (decision 5); the phase-close step | TASK-NNN (new) | Coding Agent |
| — | Existing rows that feed this directly: `TASK-312` (`test_tree_guard.py` at 62.5 s), `TASK-401` (extensionless entrypoints recompiled every call) | `TASK-312`, `TASK-401` | Coding Agent |

## 7. Risks & mitigations

| Risk | Detection | Mitigation |
|---|---|---|
| The selector misses a test a change breaks | `full` at merge goes red on a branch whose `affected` runs were green | the red lands before `main`, not after; the widening rules and "undeclared means selected" keep misses rare; every miss adds a `COVERS` entry |
| `COVERS` rots as code moves | undeclared or unmatched paths appear in the printed selection | an unmatched changed path selects `full`, so rot is slow rather than silent |
| Selection is too wide to matter (§ 1.3) | phase A's replay | phase A is a gate; nothing switches until it passes |
| Load noise makes the ratchet flaky | the same module flips across re-records | report at merge, fail only at phase close on a quiet re-record, with a margin |
| An agent skips `affected` and runs nothing | a result without the printed selection block | the reviewer checks for the block, as it checks a base SHA today |
| The primary checkout now waits for a full run per merge | merge wall time in the journal | one full run per merge replaces one per round, which is the point |
| `tests/test_durations_provenance.py` goes red when `tests/durations.json` gains a `budget` block and is written at merge | that module fails in phase C or D | phases C and D change that test in the same change, and its provenance rule names the merge as a recording source |

## 8. Open questions

- Does a remote CI, if one still runs on push, stay on the full suite? This
  repository is 317 commits ahead of `origin/main`, so nothing has exercised it
  since.
- Is in-process invocation (`tests/inproc.py`) a larger lever than selection for
  the modules that shell out to `bin/` hundreds of times? Separate speed work;
  phase A's timings will say.
- Is 60 s the right `affected` budget? Phase A's replay sets it from data.

## 9. Changes (append-only after lock)
- 2026-09-16 — § 5.2's selection rules gain two narrowings, and phase A's gate is re-measured before anything else moves — user decision `USER-940`, from `TASK-448`'s replay (median 100.0% of module-seconds against a 50% gate). (a) `tests/durations.json` is no longer a `tests/` helper that widens to `full`; it is a covered path, declared by the three modules that read it — it alone widened 20 of 50 merges. (b) A module declares the state files it actually reads rather than `perry/` or `.perry/` wholesale; 40 modules do the latter today, which is why an evidence-only merge still selects 33.7%. The 50% gate itself is unchanged, and moving those modules off the live state root is NOT decided: it waits for the new median.
- 2026-09-16 — the costliest live-state modules move off the state root, and phase A is measured a third time — user decision `USER-942`, from `TASK-448` round 2: the two narrowings took the median from 100.0% to **75.9%** (mean 67.9%, 23 of 50 merges full, evidence-only floor 31.6%), which the 50% gate still fails. 26 of the 33 broad declarations could not be narrowed honestly — they copy the state root, or run a tool at the checkout without `--root`. The 8-10 of them carrying the most module-seconds are moved off the live state root (a pinned copy, or a `--root`), and the replay is re-run; whether the remaining ones follow is decided on that median. The gate stays at 50% and `tests/fixtures/**` is NOT exempted: a fixture is read by the modules that use it, so exempting it would be a real loosening rather than a correction.

## 10. References

- `tests/run`, `tests/parallel` (§ TASK-230, `HARNESS_SELF_TESTS`), `tests/merge-check`, `tests/durations.json`
- `perry/decisions/ADR-018-verification-is-calibrated-to-blast-radius.md § C` — the suite classified, and deletion kept a user decision
- `perry/design/DESIGN-017-the-architecture-document-is-written-by-the-agent.md § 5.2` — the structural rules this suite runs before merge
- `ARCHITECTURE.md § 6` NN-4, NN-5
- `TASK-230`, `TASK-238`, `TASK-312`, `TASK-400`, `TASK-401`
