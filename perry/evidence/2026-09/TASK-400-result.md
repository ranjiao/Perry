# TASK-400 — the harness's self-tests leave the default run

> **Date**: 2026-09-08 · **Rung**: V4 — a reviewer reads this against the row's
> criteria; the round that produced it cannot attest its own.

## What moved, and what deliberately did not

```
test_tree_guard.py            41.4 s / 25 tests   tests tests/tree_guard.py
test_parallel_runner.py       10.8 s / 39 tests   tests tests/parallel
test_durations_provenance.py   0.2 s / 24 tests   tests tests/durations.json
                              ------
                               52.4 s
```

The line is **what the module tests, not what it costs**.
`test_durations_provenance` is 0.2s and moved anyway, because it is about
`tests/`. `test_restore_check` is 5.2s and stayed, because it tests
`bin/perry-restore-check` — a product tool, and the one a mutation round
depends on.

**`tests/tree_guard.py` did not move.** `tests/run` step 0 runs it on every
exit path including `--lint`, and it is a different file from
`tests/test_tree_guard.py`. What is deferred is the proof that the guard can go
red, never the guard.

## The three criteria

**1. The default run is the old set minus exactly those modules.**

```
default   117 modules · 3305 tests    88 ids fewer, 0 ids added
                                      (25 + 39 + 24 = 88)
```

**2. `--slow` restores it.**

```
--slow    120 modules · 3393 tests    diff against the old set: 0 lines
```

**3. The guard still fires on a default run.** Snapshot, plant, verify,
remove, verify:

```
unchanged        exit 0
file planted     exit 1     <- still armed
planted removed  exit 0
```

## The defect this round created and its own self-tests caught

The first implementation filtered before `--only`, so naming a self-test
explicitly could not reach it:

```
bash tests/run --only test_tree_guard   ->  "no test module matches"
```

A module sitting on disk, reported absent. `test_parallel_runner`'s own cases
found it: they drive `main()` with `mod: "test_parallel_runner.py"`, which is
in the set, and got exit 2 where they expected 0 and 1. The filter now applies
to the default set only; an explicit name reaches anything.

## The thing worth carrying out of this round

The default run reported **2 red / 3 failed** while `--slow` reported **4 red /
9 failed**. The six extra were the self-tests of `tests/parallel`, broken by
this very change — and they were invisible to the default run **because this
change had just moved them out of it**.

The hazard of taking tests out of the default run was demonstrated by the
change that took them out, on its first execution. Hence the standing rule now
in `HARNESS_SELF_TESTS`' comment: **anyone editing `tests/parallel`,
`tests/run` or `tests/tree_guard.py` runs `--slow`.** That is not advice; it is
what this round paid for.
