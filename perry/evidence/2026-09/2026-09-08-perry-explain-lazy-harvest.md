# `perry-explain` scanned 735 files to answer questions that read two

> **Date**: 2026-09-08 · branch `drop-projected-markdown` @ `f78b60f0`
> **Found while**: working the suite-time ranking top-down, per the user's
> instruction to optimise the most expensive tests first.
> **Rung**: V3 — commands and output below, id-set diff included.

## The finding, and it is not in the tests

`test_glossary` was the suite's most expensive module per test — 35.9s over 7
tests, 5.1s each — and `test_every_term_resolves_through_explain` is why: it
loops 20 glossary terms and spawns `perry-explain` for each.

The first hypothesis was the process boundary, and it was wrong. Measured:

```
subprocess  perry-explain V4 : 1402 ms
in-process  main(["V4"])     : 1238 ms
                              ------
process overhead              :  164 ms   (12%)
real work                     : 1238 ms   (88%)
```

Converting the loop to in-process would have bought 3.3s of the 28s. The
profile said where the rest went:

```
harvest()                       1.986s cumulative
  735 x Path.read_text()        0.692s
  732 x blank_code_spans()      0.488s
  138379 x find_ids()           0.130s
```

And `main`'s own structure said why it was wasted:

```
770  entries = harvest(root)        unconditional
803  rung = rung_entry(want)        returns 0, never touches entries
815  term = glossary_entry(want)    returns 0, never touches entries
852  entries.get(want)              the first real use
```

`rung_entry` reads `schema/state-schema.json`. `glossary_entry` reads
`reference/glossary.md`. **Neither needs the corpus, and both ran after a full
corpus scan whose result was then discarded.** Every `perry-explain V4` and
every glossary lookup paid 1.2 seconds for nothing.

## The change

`harvest` is called through a `entries_now()` closure that computes it once, on
first use. `--all` and `--dangling` take it explicitly; the ID-lookup tail takes
it where the fast paths have already returned. No call site lost the scan; the
two that never used it stopped paying for it.

`bin/perry-explain` only. No test file was edited.

## Measured

```
                                     before     after
perry-explain V4                     1402 ms     44 ms     32x
perry-explain "verification rung"    1402 ms     44 ms
perry-explain TASK-399               1402 ms     50 ms
perry-explain ADR-019 (needs it)     1402 ms    942 ms     unchanged path

tests/test_glossary.py                35.9 s    2.63 s     14x
tests/test_rung_vocabulary.py         30.8 s    3.70 s      8x   (not targeted)

full suite wall                      128.4 s   106.5 s     see Correction
```

`test_rung_vocabulary` was not touched and was not the target. It resolves
rungs, which is the same fast path, so it took the win for free — both modules
left the top ten entirely.

## The verification that matters

```
$ diff <(sort ids-before.txt) <(sort ids-after.txt)
$ echo $?
0
```

**3393 test ids, identical, with identical outcomes** — not merely the same
count. `tests/parallel --ids` before and after, compared as sets, because this
runner has previously reported 1207 tests against 1287 and looked like a win.
Still 2 modules red and 3 tests failed: the same pre-existing three this branch
started with.

## What this corrects in the plan

The suite-time analysis put this cost under W4, in-process fixture building,
whose premise is that the process boundary is the cost. For `perry-explain`
that premise is false — the boundary is 12% and the tool's own wasted work is
88%. W4 remains right for the writer-heavy modules where a fixture row is built
by spawning `perry-task`; it was the wrong instrument here.

The general lesson for the rest of the ranking: **measure the split before
choosing the fix.** One in-process call against one subprocess call says which
of the two you are looking at, and costs a minute.

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
