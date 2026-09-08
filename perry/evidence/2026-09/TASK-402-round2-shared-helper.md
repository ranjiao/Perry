# TASK-402 round 2 — one helper, 21 modules

> **Date**: 2026-09-08 · branch `suite-cost-round2`, from `main` @ `604cdcc4`
> **Rung**: V5 is the row's; this is **V3 evidence toward it**.

## The lever

`tests/task_writer_support.py` is shared by **21 test modules** and contains
exactly **two** subprocess call sites. Those 21 modules are **275 of the
suite's 936 CPU-seconds — 29%**.

Split measured first, per the row's own procedure, on the call shape the helper
actually makes (`perry-task add` against a fresh fixture, not `list` against the
live project):

```
subprocess   121.0 ms
in-process    12.0 ms      (one-time import 36.5 ms)
             ---------
boundary     109.0 ms      90%
```

So ~248 of those 275 seconds are process startup.

## The safety check that came before the edit

`perry-task` is 8,294 lines and a **writer**, so its module state matters far
more than `perry-goals`' did. `tests/inproc.py` requires reading the tool for
module-level mutable state before converting. Three globals exist:

| global | source | root-dependent? |
|---|---|---|
| `_ALIASES` / `_DISPLAY` | `load_schema()["i18n"]["columns"]` | no |
| `_HEADINGS` | `load_schema()["i18n"]["headings"]` | no |
| `_PERRY_STATE` | a sibling module, loaded once | no |

All three derive from the schema at `PERRY_HOME` or from another tool, so
sharing them across calls with different roots is safe. Had any been keyed on
the project root, this conversion would have silently served one test another
test's answer.

## Measured

```
tests/test_task_writer_core.py           29.8 s ->  4.75 s   6.3x
tests/test_purge.py                      28.2 s ->  2.84 s   9.9x
tests/test_register_store_invariant.py   18.2 s -> 11.51 s   1.6x
```

Whole suite, against the stamped baseline in `tests/durations.json`:

```
CPU        1278 s -> 602 s      raw -52.9%
x median   0.80               <- this run had a 20% load tailwind
```

**Corrected for that tailwind the change is worth about -41%**, not -52.9%: a
uniform 0.80 scaling would have put the total at 1022s on its own, and 602
against 1022 is 0.59. Both numbers are given because the raw one is what a
reader will compute from the table and the corrected one is what the work did.

Wall was 75.3s against 117.0s on the previous run — reported, not claimed;
`TASK-399-result.md § Appendix` says why whole-suite wall is not evidence on
this machine.

## Verification

**Id set.** 21 modules is a wide blast radius and the count would hide a
module that stopped running:

```
$ diff <(sort ids-before.txt) <(sort ids-r2.txt) ; echo $?
0
```

3393 ids, identical, identical outcomes, the same 3 pre-existing reds.

**Order dependence**, required by W4 because in-process calls share what child
processes do not — and here what is shared is a *writer's* state. Four
converted modules run with their method order reversed:

```
test_task_writer_core   66 tests, 0 failures, 0 errors
test_purge              48 tests, 0 failures, 0 errors
test_intake_store       51 tests, 0 failures, 0 errors
test_risks_store        53 tests, 0 failures, 0 errors
```

## Found while measuring, not fixed here

`perry-task add --json` writes its no-KR advisory to stderr on every call — it
filled the terminal during the timing runs. That is `TASK-398`, filed this
morning from aiMark's round-7 feedback, and this is an independent
reproduction of it rather than a new finding.
