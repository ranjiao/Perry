# TASK-402 — V5 sign-off

> **Signed off: Ran Jiao, 2026-09-08.**
>
> **Checked, and this is the whole of it:**
>
> 1. **The measurement method.** One in-process `main(argv)` against one
>    subprocess call, per tool, before choosing an instrument. It gave four
>    different answers on four tools — `perry-explain` 12%, `perry-diagnose`
>    33%, `perry-goals` 95%, `perry-task` 90% — and those answers are why two
>    of the four rounds became product fixes rather than conversions.
>    `evidence/2026-09/TASK-402-premise.md`.
>
> 2. **The unfaithfulness list, accepted as a trade for speed.**
>    `tests/inproc.py`'s docstring names three ways an in-process call is not a
>    child process: module-level state persists where a child starts clean;
>    `argv` and cwd are not changed; `os._exit` takes the test process with it.
>    Two of the three drew blood the same day — `perry-diagnose`'s `_TEXT_CACHE`
>    has to be cleared per run, and a dropped `cwd` pin silently read a
>    different project.
>
> 3. **The scope of this signature, stated rather than implied.** It covers
>    *the conversions did not change what the tests report* — five id-set
>    comparisons, every one an empty diff over 3393 ids with identical
>    outcomes. **It does NOT cover *these tests still catch regressions*.** No
>    mutation was run in any of the four rounds. Under this project's own rule
>    a green that has not been shown able to go red is not evidence, and that
>    evidence is absent here by admission rather than by oversight.
>
> Recorded at this precision deliberately. V5's value is saying what was
> actually checked; writing "reviewed" would make the rung a label.

## What the row delivered

`tests/inproc.py`, and four rounds of conversion:

| round | subject | before | after |
|---|---|---|---|
| 1 | `test_goals_writer` | 31.75 s | 16.10 s |
| 2 | `tests/task_writer_support.py`, shared by **21 modules** | 275 CPU-s | see below |
| 3 | `tests/contract_key_parity.py`, shared by 7 | 24.1 s | 5.2 s |
| 4 | `test_diagnose` | 39.3 s | 21.2 s |

Round 2's individually measured modules: `test_task_writer_core` 29.8 → 4.75 s,
`test_purge` 28.2 → 2.84 s, `test_register_store_invariant` 18.2 → 11.51 s.

**No aggregate percentage is quoted.** Two were and both were withdrawn:
`-21%` rested on a load-inflated baseline, and `-41%` normalised by a median
that the conversions had themselves moved. `TASK-399-result.md § Appendix` and
`TASK-402-round3-parity-helper.md § Correction 2` carry both retractions.

## The row's own verification criteria, each answered

| criterion | result |
|---|---|
| pass/fail **id sets** identical, not merely the same size | 5 comparisons, every diff empty over 3393 ids |
| measured wall drops against the W1 baseline | per module, above; suite wall not quoted, and why is in TASK-399's appendix |
| every converted module passes under `--serial` | `test_goals_writer` 112, `test_task_writer_core` 66, `test_purge` 48, `test_intake_store` 51 all OK; `test_contract_key_parity` 2 and `test_diagnose` 1 failures, all pre-existing |
| the named exclusions stay on `subprocess` | `test_project_root_resolution`, `test_host_support` and `test_tree_guard`'s `PERRY_PROJECT` cases untouched |

## The gap this sign-off does not close

The mutation pass. Filed as its own row rather than left inside a closed one,
because "a gate is not green until it has been shown able to go red" is this
project's rule and four rounds went by without applying it to their own work.
