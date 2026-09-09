# TASK-402 round 3 — the parity helper, and two methodological corrections

> **Date**: 2026-09-08 · branch `suite-cost-round3`, from `main` @ `f2016f12`

## The conversion

`tests/contract_key_parity.py` has one subprocess call site, reached by seven
modules. `test_contract_key_parity` alone made **179 calls for 23.6 of its 24.1
seconds** across five tools, every call small — so the cost was the boundary.

Module globals checked first, per `tests/inproc.py`, for all five tools:
`perry-decide._STATUSES`, `perry-state`'s four (`_STAGE_SEPARATORS`,
`_NO_DEFAULT`, `_DEFAULT_STAGES`, `_BLANK_MARKER`), `perry-knowledge._LINT`,
plus `perry-task`'s and `perry-goals`' from earlier rounds. Every one derives
from `schema/state-schema.json` or from a sibling module; none is keyed on the
project root.

```
tests/test_contract_key_parity.py   24.1 s -> 5.2 s
```

Id set unchanged across 3393 ids; 2 modules red, 3 tests failed, all
pre-existing.

## Correction 1 — a real defect the false alarm exposed

The conversion first appeared to break the module: 4 failures and **12 errors**,
all `KeyError: 'roles'`. Everything reproduced nothing:

```
perry-state alone                        22 keys, has roles
after calls to task/decide/goals/knowledge  22 keys, has roles
after a call rooted at the witness project  22 keys, has roles
parity.run() directly                    OK
parity.measure() directly                OK
```

The cause was not the tool and not module state. It was that I ran the module
from `tests/` while the code I replaced passed **`cwd=ROOT`** to
`subprocess.run`. `inproc.run` did not change the working directory, and a tool
with no `--root` resolves its project by walking up from the cwd — so it read a
different project. From the repository root the module was always at its two
pre-existing reds.

**The false alarm was mine; the defect it exposed was real.** Dropping a `cwd=`
pin does not fail loudly, it silently reads elsewhere, and
`tests/parallel § run_module` spawns every module with `cwd=ROOT` — so the suite
would never have caught it. A hole the suite cannot see is worse than one it
reddens on.

`inproc.run` now takes `cwd`, chdir-ing and restoring around the call, and the
parity helper pins `ROOT` again. Verified by running the module from `tests/`,
where it now reaches the same two reds. The account is in `inproc.py`'s
docstring, so the next person converting a helper meets the explanation rather
than the trap.

## Correction 2 — my own aggregate figure was measuring itself

Rounds 1 and 2 quoted a whole-suite CPU total normalised by the run's median
`x`, on the argument that the median stands for load. Two runs, one after this
conversion:

```
round 2   total 602 s   x median 0.80
round 3   total 730 s   x median 0.90
```

The total went **up** after a change that only made a module faster.

The median is a load proxy **only while most modules are unchanged.** Round 2
converted 21 modules at once; those improvements moved the median itself, so
the denominator and the numerator are no longer independent. The `-41%`
reported for round 2 is withdrawn on the same grounds as the `-21%` withdrawn
earlier in the day: **a baseline contaminated by the thing being measured.**

No aggregate percentage is quoted from here. On this machine the only figure
that survives its own method is a **per-module time measured back to back in one
session**, which is what every table in these evidence files now carries.
