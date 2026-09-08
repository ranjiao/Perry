# TASK-402 (W4) — the premise was falsified twice before the row was worked

> **Written**: 2026-09-08, before any in-process conversion was attempted.
> **Why this exists**: W4's spec opens by asserting that the process boundary is
> the cost. Two modules at the head of the ranking were measured and it was not.
> Read this before converting anything.

## What W4 assumes

> *"Those calls need no process boundary. Loading the tool once per worker and
> calling `main(argv)` takes the same call from 121 ms to 4.0 ms."*

That is true of `perry-task` on a fixture. It was false of both modules at the
top of the ranking, and acting on it would have bought a fraction of the win
while changing how tests execute — the V5 risk this row already carries.

## Module 1 — `test_glossary`, the worst cost per test at 5.1s

```
subprocess  perry-explain V4 : 1402 ms
in-process  main(["V4"])     : 1238 ms
                              --------
boundary                     :  164 ms   12%
the tool's own work          : 1238 ms   88%
```

In-process conversion was worth 3.3s of a 28s test. The other 25s was
`main()` calling `harvest(root)` unconditionally — 735 files — and then
resolving rungs and glossary terms through two fast paths that never read it.

Fixed in the product: `35.9s -> 2.63s`, and `test_rung_vocabulary` took
`30.8s -> 3.70s` for free because it uses the same fast path. No test file was
edited. Full account:
`evidence/2026-09/2026-09-08-perry-explain-lazy-harvest.md`.

## Module 2 — `test_diagnose`, the ranking head at 44.3s

This one **is** subprocess-bound — 38.1 of 39.2 seconds are child processes —
and W4 still would not have fixed it. 121 calls, but four of them diagnose Perry
itself at **6.53s each against 0.285s for a fixture**. Those four are the module,
and they are real work, not startup.

The defect was that `perry-diagnose` read the corpus **3.79 times**: 2791
`read_text` calls over 736 distinct files, 556 of them exactly four times. A
per-run read cache took `6.53s -> 5.42s`. Full account:
`evidence/2026-09/2026-09-08-perry-diagnose-read-cache.md`.

**Subprocess-bound does not mean boundary-bound.** That distinction is the whole
of this page.

## Where W4 is still right

Measured on the tool W4 actually targets, on the live project:

```
subprocess  perry-task list --all --json : 250.5 ms
in-process  main(argv)                   : 115.2 ms   (import once: 28.8 ms)
                                           --------
boundary                                 : 135.3 ms   54%
```

**54% is the number W4 was written for.** It holds for the modules that build a
fixture ROW by spawning `perry-task` — `test_task_writer_*`, `test_track_move`,
`test_purge` — which are mid-ranking, not the head. Convert those.

## The procedure this row should follow

For each candidate module, in this order, before writing any conversion:

1. **Split the cost.** One in-process `main(argv)` against one subprocess call
   on the same root. A minute. If the boundary is under ~40%, the fix is in the
   tool and this row is the wrong instrument.
2. **Wall-clock, do not cProfile, anything called ~100k times.** `cProfile`
   reported `Path.resolve()` at 92,674 calls and 2.52s inside `perry-diagnose`;
   hoisting the loop-invariant that caused it moved 6.53s to 6.44s, because the
   2s was the profiler's own per-call accounting. Wrap the top-level phases in
   `time.perf_counter()` instead.
3. **Count, do not infer.** Counting `read_text` by path is what found the 3.79.
4. **Compare the `--ids` SET.** Three conversions were verified this way today,
   all with an empty diff over 3393 ids.

## The larger claim is unaffected

The analysis's headline — 1188 of 1860 CPU-seconds inside `bin/perry-*`
subprocesses — is a ratio and stands. What does not follow is that the
*boundary* is where those seconds go. On two of two modules examined, it was the
tools doing avoidable work while the boundary was a minority of the call.
