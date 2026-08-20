# TASK-127 — the contract docs and the payloads they describe are never diffed against each other

> Source: `perry/OKR.md § Objective 2` (KR-O2.4) and `schema/README.md`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: no
> Touches architecture: no — this adds a check; it changes no contract and bumps no version
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: KR-O2.4 (overall OKR v2, due 2026-09-30)

## Why this row exists

KR-O2.4's metric is a count: *contract-payload keys documented but not emitted,
or emitted but not documented*. **Nothing in the repository computes it.**

`tests/test_contract_invariance.py` is the closest thing and it measures
something else: it captures the payload's SHAPE — every field path and the type
at it — and compares that against a recorded baseline, so a key that is emitted
and undocumented passes cleanly, and a key documented and never emitted is
invisible to it because it was never in the baseline. The other seven modules
that read a contract file (`test_count_fields`, `test_role_on_rows`,
`test_task_writer`, `test_task_summary`, `test_prioritize`, `test_goals_contract`,
`test_goals_writer`) each assert that **one named field** is mentioned in the
prose. Seven spot checks are not a count.

So the KR currently cannot be scored except by hand, which is the same defect
`perry-goals list` has for KR progress.

## The denominator is wrong in the KR text

KR-O2.4 says "across all three contracts". There are **five**:

| File | Contract |
|---|---|
| `schema/task-list-contract.md` | `perry-task/list/1.11` |
| `schema/goals-list-contract.md` | `perry-goals/list/2.0` |
| `schema/decide-list-contract.md` | `perry-decide/list/1.0` |
| `schema/events-list-contract.md` | `perry-events/list/1.0` |
| `schema/roles-list-contract.md` | `perry-roles/list/1.0` |

**Do not measure three and report 0.** Measure what is there, report the count
per contract, and hand the KR-text correction back — the `goals` lane owns that
sentence and this row does not edit it.

## Deliverable

1. A mechanical two-way diff, per contract file, between the field paths the
   **document declares** and the field paths the tool **actually emits**:
   - `documented_not_emitted`
   - `emitted_not_documented`
2. Discovery is by glob, not by a hand-written list, and the run **names how
   many contract files it found**. A contract added later must not be silently
   skipped — that is the failure mode this whole row is about.
3. A per-contract baseline that lives in a **file**, not in a memory or a
   docstring, so the number can be compared across runs by someone who was not
   here.
4. Where the two sides genuinely cannot be compared mechanically — a payload
   whose keys are data rather than schema, a documented key behind a flag not
   set in a plain run — say so **per contract, by name**, with the reason.
   A silently narrowed denominator is worse than a smaller one that is stated.

## Verification — V3

1. **The check discriminates in both directions**, proved by mutation, not by
   asserting a test exists:
   - remove one documented key from its emit site → red, naming that key;
   - add one emitted key the document does not declare → red, naming that key;
   - revert both and the count returns to its baseline.
2. The per-contract counts are printed, and the run prints the number of
   contract files discovered. Deleting one contract file changes that number.
3. Adding a sixth contract file with one documented, unemitted key is reported
   without any edit to the check.
4. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Baseline

The suite's baseline must be measured **in your own worktree**, not taken from
this file. As of this writing `feat/work-modes` is reconciled with the remote
and `test_diagnose` is the one known red — its cause is TASK-126, a check whose
only live references are inside the record describing its own fix, and it is not
yours. Two open PRs (#19, #20) are not merged; cut your worktree from
`feat/work-modes` as it stands and say what your baseline was.

## Files in scope

- a new check, plus its baseline file
- the test module that exercises it
- `schema/README.md` only if it must describe where the baseline lives

## Out of scope

- **Editing any contract document's content, or bumping any contract version.**
  This row measures the gap; closing the gap is whatever rows the measurement
  produces.
- Editing KR-O2.4's text. Report the five-vs-three discrepancy; the `goals`
  lane makes that edit.
- `tests/test_contract_invariance.py`'s baseline. It measures shape and stays.
