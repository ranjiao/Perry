# TASK-304 — result

> Branch: `coding/task-304-durations-provenance-b`
> Base: `d49964e` (worktree HEAD; stale relative to `coding/task-247-config-predicate`)
> Date: 2026-09-02
> Rung: V4

Every figure below carries the ref it was taken at.

## Status

IN PROGRESS — reproduction recorded, mechanism not yet written.

## 1. Reproduction (before any change), at `d49964e`

Driven through `tests/parallel`'s own `load_durations()` and `schedule()`, over
the live glob `tests/test_*.py`. Machine load at this reading: `13.64 46.56
48.20` (1/5/15 min).

    recorded: 103   on disk: 108

**Recorded but not on disk — 2:**

| module | recorded | rank by recorded seconds |
| --- | --- | --- |
| `test_migrate.py` | 97.25 | **1 of 103** |
| `test_conformance.py` | 21.84 | 33 of 103 |

The file's largest entry is a module that was deleted when USER-910 took
migration out. It holds the head of the recorded ranking:

    test_migrate.py            97.25   *** DOES NOT EXIST ***
    test_track_move.py         94.96   ON DISK
    test_goals_writer.py       86.22   ON DISK
    test_purge.py              85.95   ON DISK
    test_diagnose.py           83.25   ON DISK

**On disk but not recorded — 7, each sorting as `inf`:**

`test_config_store_readers.py`, `test_context_budget.py`,
`test_header_index_is_the_only_fold.py`, `test_phase_kr_declared_once.py`,
`test_register_store_invariant.py`, `test_register_substitution.py`,
`test_tree_guard.py`.

The actual head of `schedule()` over the live glob is those seven, in name
order, ahead of every measured module:

    test_config_store_readers.py            inf (unrecorded)
    test_context_budget.py                  inf (unrecorded)
    test_header_index_is_the_only_fold.py   inf (unrecorded)
    test_phase_kr_declared_once.py          inf (unrecorded)
    test_register_store_invariant.py        inf (unrecorded)
    test_register_substitution.py           inf (unrecorded)
    test_tree_guard.py                      inf (unrecorded)
    test_track_move.py                      94.96
    test_goals_writer.py                    86.22

**A precision the spec's summary is worth stating exactly.** `schedule()` sorts
the *glob's* result, so `test_migrate.py` never actually enters the order — the
hint may reorder, never select, and `tests/test_parallel_runner.py` holds that
line. What is true, and is the defect, is that **the file's own ranking is
headed by a module that cannot run**, and that the schedule's real head is seven
modules the file does not mention at all. Neither condition was reported by
anything.

Other figures confirmed at this ref:

- recorded serial total **1968.9s**, against a measured 162.4s at 8 workers =
  1299 worker-seconds. The recorded numbers describe no run that has happened.
- `test_header_rule_harness.py` recorded at **25.53s**; measured 265.996s and
  260.74s at `d49964e`, the very commit that wrote the file. 10x low.
