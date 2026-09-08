# `perry-diagnose` read the same corpus 3.79 times

> **Date**: 2026-09-08 · branch `drop-projected-markdown` @ `77076965`
> **Rung**: V3 — commands and output below, id-set diff included.

## The measurement that was wrong, and how it was caught

`test_diagnose` was the ranking's top module at 44.3s, and it is
subprocess-bound: 38.1 of its 39.2 seconds are child processes, 121 of them
`perry-diagnose`. Four of those calls diagnose Perry itself, at **6.53s each**
against 0.285s for a fixture, so the module's cost is those four.

`cProfile` on `perry-diagnose --root .` reported `Path.resolve()` at 92,674
calls and **2.52s cumulative**, and there was an obvious cause:
`bin/perry-diagnose:1153` called `root.resolve()` inside a per-token loop where
`root` never changes. Hoisted it out.

**6.53s → 6.44s.** The fix was correct and bought nothing.

The profiled run was 8.58s and the unprofiled one 6.53s: the 2 second gap is
cProfile's own per-call accounting, and at 92,674 calls that overhead *is* the
2.52s it reported. **A function called ~100k times cannot be sized with
cProfile.** The hoist is kept — it is free and it is right — but it is worth
0.1s, not 2.5s.

Re-measured with a wall clock around the top-level phases, no per-call
accounting:

```
total                     6.02 s
  scan_user_load          3.13 s  (52%)
  scan_docs               2.48 s  (41%)
  scan_decision_mentions  1.28 s  (21%)
```

## The actual defect

Counting `Path.read_text` by path:

```
2791 calls over 736 distinct files = 3.79 reads per file
556 files read exactly 4 times, 118 twice, 41 five times
schema/state-schema.json 9 times · perry/BOARD.md 8 times
```

Each scan phase walks the corpus for its own reason and none of them knew
another had just read the same bytes.

## The change

`read_text` memoises on `(path, cap)`. Keyed on `cap` as well as path because
`cap` truncates and two callers may disagree — keying on the path alone would
hand a 400k caller the shorter string an earlier, stricter caller asked for.

**The cache is per RUN, not per process**, cleared at the top of `diagnose()`.
That is not defensive: `tests/test_diagnose.load_bin_module` imports this module
and calls it more than once in one process, so a process-lifetime cache would
serve the first run's bytes for a file the second run rewrote. Verified:

```
diagnose(fixture)            -> payload A
rewrite fixture/OKR.md
diagnose(fixture)            -> payload B
A != B                       -> the cache did not leak
```

## Measured

```
perry-diagnose --root .        6.53 s -> 5.42 s   (-17%)
tests/test_diagnose.py          39.2 s -> 36.0 s   (-8%)
full suite wall                106.5 s -> 106.4 s  see Correction
```

**The suite wall did not move and that is the honest result.** 3.2 CPU-seconds
across 8 workers is 0.4s, inside the noise of a machine whose same-commit runs
have spanned 106-166s today. The value here is the user-facing command:
`/perry diagnose` is a thing a person waits for.

## Verification

```
$ diff <(sort ids-before.txt) <(sort ids-diag.txt) ; echo $?
0
```

3393 test ids, identical, identical outcomes, the same 3 pre-existing reds.

## Not done

`scan_user_load` is still 3.13s and is the largest remaining phase. It runs
`perry-explain`'s `harvest`, which does its own `path.read_text` and so does not
go through this cache. Routing it through would need a reader parameter on
`harvest`, which is a cross-module API change; stopped short of it deliberately.

---

## Correction, 2026-09-08 evening — the wall-time figure in this file

The `full suite wall` line above is not evidence and is withdrawn as a claim.
Whole-suite wall on this machine is not separable from load: the same commit
measured 106s, 117s, 122s, 128s and 166s across one afternoon. A `-17%` derived
from two such numbers is noise with a sign.

The per-module figures in this file **stand** — they were measured back to back
on one machine state, and the load-robust re-measurement confirms them:
`test_glossary` 52.3s -> 3.09s and `test_rung_vocabulary` 41.7s -> 4.06s
against a run whose median module ratio was 1.00.

The defensible total for all four cuts is **-343 CPU-seconds, -26.8%**, and the
method that produces it is in
`evidence/2026-09/TASK-399-result.md § Appendix`. Two modules this change was
never aimed at — `test_task_store` and `test_register_minters` — are in that
table, because a product fix reaches callers nobody enumerated.
