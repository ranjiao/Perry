# TASK-368 — spec

> Design: none. This row is a measured engineering complaint, and
> `evidence/2026-09/TASK-402-premise.md` is the document that governs it
> Dispatch mode: manual
> Executor: claude-subagent — touches no `bin/` tool, only `tests/`
> Estimated cycle: large, and it is meant to be run in slices
> Subjective verification: which modules are worth converting, and whether a
> converted module still fails for the reasons it used to
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P0
- **Track / mode**: main / project
- **Dependencies**: `TASK-263` — done. **`TASK-402` — done, V5 signed
  2026-09-08, and it changed this row's premise; read the next section before
  anything else**
- **KR linkage**: declared unlinked — this is suite cost, not a phase-003 KR
- **Verification rung**: V4

## The row's title is no longer true, and that is the first thing to fix

This row was filed on **2026-09-04** and says *"The suite has no unit seam"*.

**It has one.** `tests/inproc.py` was added on **2026-09-08** by `TASK-402`,
which loads a `bin/` tool once per process and calls `main(argv)` in-process,
returning something shaped like `subprocess.CompletedProcess` so a call site
does not have to change. Ten modules use it today.

So this row is no longer "build a seam". It is **"finish adopting one, where
adopting it pays"** — and the second half of that sentence is the part
`TASK-402` measured and this row must not discard.

**`TASK-402`'s counter-examples, which refute the naive version of this row:**

| tool measured | boundary as a share of the call |
|---|---|
| `perry-goals list` | 95% |
| `perry-task list --all --json` | 54% |
| `perry-diagnose`, the ranking head | 33% |
| `perry-explain` | 12% |

On the two modules at the **head** of the cost ranking the boundary was a
minority: those tools were doing avoidable work, and converting them would have
bought a fraction of the win. A row that converts 369 call sites because they
are subprocesses would spend most of its effort on the 12% and the 33%.

`TASK-402-premise.md § "The procedure this row should follow"` is therefore
**binding on this row**, not advisory.

## Why the row still exists

The seam is adopted by **10 of 127** test modules. Measured at `583f024f`:

```
test modules                              127
modules that launch a subprocess          107
subprocess.run / Popen / check_output     369 call sites
modules importing inproc                   10
inproc.run call sites                      18
suite wall clock                          114.4s   (124 modules, 8 workers)
```

The row was filed against 324 call sites and there are now 369. The cost is
growing, and nothing stops a new module from being written against the old
pattern.

## Files in scope

`tests/` only. **No file under `bin/` or `viewer/` may change.** If a conversion
requires a tool change, that is a finding and its own row, not a change made
here.

- `tests/inproc.py` — read; extend only if a measured gap requires it, and say so.
- the test modules this row converts — written.
- `perry/evidence/2026-09/TASK-368-result.md` — written.

## Bound

```
Commit:       583f024f — re-derive every figure in the agent's own tree first
Enumeration:  the 107 test modules that launch a subprocess
Size:         107 modules, 369 call sites
This row:     the modules that pass step 1 of the procedure below. The set is
              DERIVED by measurement, not chosen, and the report lists both the
              modules converted and the modules measured and rejected
Excluded by name and not by measurement: `test_project_root_resolution`,
              `test_host_support`, and the `PERRY_PROJECT` cases in
              `test_tree_guard`. Their SUBJECT is the process boundary — exit
              codes as a shell sees them, stderr as a stream, argv parsing, root
              resolution from cwd. Converting one would delete the test
Last element: the lowest-ranked module that passed step 1
```

## The procedure, which is not optional

For every candidate module, in this order, **before writing any conversion**:

1. **Split the cost.** One in-process `main(argv)` against one subprocess call
   on the same root. **If the boundary is under 40%, do not convert it** — the
   fix is in the tool and this row is the wrong instrument. Record the number
   either way.
2. **Wall-clock, never `cProfile`, for anything called ~100k times.** `cProfile`
   reported `Path.resolve()` at 92,674 calls and 2.52s inside `perry-diagnose`;
   removing the cause moved 6.53s to 6.44s, because the 2s was the profiler's
   own accounting.
3. **Count, do not infer.**
4. **Compare the `--ids` SET before and after.** `TASK-402` verified three
   conversions this way, empty diff over 3,393 ids.

## Deliverable

1. The converted modules, each measured in and measured out.
2. `perry/evidence/2026-09/TASK-368-result.md` carrying, per module examined:
   the boundary share, converted or rejected, the before and after time, and
   the `--ids` set diff.
3. A **suite total** before and after, same machine, same worker count.
4. A one-line statement of what the remaining un-adopted modules would be worth,
   so whoever picks up the next slice knows whether to.

## What it must not do

1. **It must not convert a test whose subject is the boundary.** See Bound.
2. **It must not change any `bin/` tool** to make a conversion possible.
3. **It must not convert a module it did not measure.** A conversion with no
   step-1 number in the report is not delivered, however fast it made things.
4. **It must not report a speed-up as the result.** `TASK-402`'s V5 signature
   says this explicitly: it covers that the conversions did not change what the
   tests REPORT, and it does **not** cover that the tests still catch what they
   used to. This row inherits that gap and must close it for its own
   conversions — see Verification 3.
5. **It must not leave a module half-converted.** Mixed modules were where
   `TASK-402`'s shared-helper rounds went wrong.

## Verification

1. **Every converted module is green, and the suite's red set is unchanged.**
   Three reds are known on `583f024f` and are not this row's:
   `test_contract_key_parity` ×2 and `test_resume.test_a_fresh_run_is_not_stale`.
   Re-derive the baseline in your own tree; a baseline taken in a checkout with
   uncommitted changes is wrong.
2. **The `--ids` set diff is empty** for every converted module.
3. **Mutation, and this is the rung.** For each converted module, pick a test
   whose failure the module exists to catch, break the `bin/` code it covers,
   and show that test **still goes red after conversion**. A conversion that
   makes a test faster and blind is the defect this row is most likely to ship,
   because the in-process path shares module globals the subprocess did not.
   `TASK-402`'s signature explicitly does not cover this. At least one mutation
   per converted module, named.
4. **A rejected module is reported with its number.** "Measured 22%, not
   converted" is a delivered result.
5. **The suite total is wall-clock on one machine with the worker count stated.**

## Out of scope

- Making any `bin/` tool faster. That is where the 12% and the 33% modules'
  cost actually lives, and it is a different row.
- Parallelism, worker counts, or the runner itself.
- Converting the three boundary-subject modules named under Bound.
- `tests/` fixtures that are slow for reasons other than process launch.
