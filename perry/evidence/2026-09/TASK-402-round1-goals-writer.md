# TASK-402 round 1 — `test_goals_writer` in-process

> **Date**: 2026-09-08 · branch `drop-projected-markdown` @ `eeb58ae7`
> **Rung**: V5 is the row's; this round is **V3 evidence toward it** — the
> id-set proof and the order-dependence check are here, the independent review
> the rung requires is not.

## Why this module and not the ranking head

Per `TASK-402-premise.md`, the split was measured before anything was written.
`perry-goals list` against a fixture:

```
subprocess   67.2 ms
in-process    3.5 ms      (one-time import 26.2 ms)
             --------
boundary     63.7 ms      95%
```

95% is what W4 was written for. For contrast, measured the same way on the two
modules above this one in the ranking: `perry-explain` 12%, `perry-diagnose`'s
expensive calls 33%. Same method, three different answers — which is why the
row now carries the procedure rather than the instrument.

Call census inside the module: **224 subprocess calls, 29.5s of 31.75s (93%)**
— `perry-goals` 194 times at 139 ms, `perry-lint` 30 times at 84 ms.

## The change

`tests/inproc.py`, new. It returns an object shaped like
`subprocess.CompletedProcess` — `returncode`, `stdout`, `stderr` — so **no call
site moved**; only the one helper `GoalsFixture.run` did. 194 call sites are
untouched.

What it is faithful about, and what it is not, is written in the module
docstring rather than here, because that is where the next person converting a
module will be standing. The part that matters most: **module-level state in a
tool persists across in-process calls where a child process would start
clean.** `bin/perry-diagnose` grew a `_TEXT_CACHE` earlier today and it is
cleared per run *because of this file*. `perry-goals`' two module globals were
read before converting — `_SCHEMA` is a schema file and `_PERRY_STATE` is a
sibling module, both root-independent, so sharing them across calls with
different roots is safe.

## Measured

```
tests/test_goals_writer.py    31.75 s -> 16.10 s     112 tests, all pass
full suite wall              106.4 s  -> 101.0 s
```

## Verification

**Id set, not count.** The runner has previously reported 1207 tests against
1287 and looked like a win, so the set is what gets compared:

```
$ diff <(sort ids-before.txt) <(sort ids-w4.txt) ; echo $?
0
```

3393 ids, identical, identical outcomes, the same 3 pre-existing reds.

**Order dependence.** W4's spec requires that a converted module also pass
outside the parallel schedule, because in-process calls share what a child
process would not. Run with the method order reversed:

```
112 tests, 0 failures, 0 errors
```

It also passes alone and under the parallel runner, both above.

## What this round does NOT establish

- **The V5 the row carries.** V5 is an independent reviewer against written
  criteria, and the writing session cannot produce it. This is the artifact a
  review would read, not the review.
- **That the remaining 16.1s is boundary.** It was not re-split after the
  conversion. The 30 `perry-lint` calls in this module are still subprocesses
  and were left alone deliberately: one instrument per round, so the id-set
  diff attributes to one change.
