# TASK-148 — result

> Date: 2026-08-21 · Executor: claude-subagent · Merged locally
> Branch: `coding/task-148-one-startable` · Cycle time: ~2h15m wall, most of it
> waiting on three suites sharing the machine
> 4 files: `bin/lib/__init__.py` (+72), `bin/perry-task` (+11/−66),
> `tests/one_startable_rule.py` (328), `tests/test_one_startable_rule.py` (336)

## The guard is an AST scan, and that is the finding

The two copies were **not textually alike** — different variable names, the
waiting set inlined on one side and named on the other. **A regex for either
spelling misses the other, which is how the second copy survived.**

And it counts homes by **enclosing function, not by file**. Both copies lived in
one file, so a per-file count would have called that one home and **stayed green
through the entire defect**. A test asserts exactly that.

It asserts *exactly one* home, so it also reddens if the rule vanishes, and it
holds no list of blessed files — moving the rule elsewhere stays green, copying
it does not. Verified against the pre-change file: it names both real homes.

## Item 1 — payloads diffed at four sites, byte-identical

A fixture built once through the tool's own writer and kept on disk, so before
and after ran against identical inputs; determinism proved by capturing twice
before changing anything.

| site | reading |
|---|---|
| `perry-task list --json --all` on this repository | 149 rows, 32 startable, 0 blocked_stale |
| the same on a fixture **with** a store | 6 rows, 2 startable, 1 stale |
| the full `_cmd_list_from_board` payload on a **no-store** fixture, called as `bin/perry-task:1547` calls it | — |
| `perry-tasks build` on that fixture, at the CLI, stashed and unstashed | — |

`diff -r` on all four: identical. **No contract bump — nothing came up that
wanted one**, which is item 1 passing rather than an omission.

## Item 2 — and it corrects the record twice over

`_cmd_list_from_board` is **not on the `list` dispatch table at all**; its only
route is `store_records` (`bin/perry-task:1547`), which **every write goes
through** and which `perry-tasks build/write/verify` calls.

So the original claim that the board path is dead is wrong twice: it is
reachable from the CLI *and* reachable from a test. The two paths are asserted
to agree row for row on `(status, depends_on, blocked_by, startable,
blocked_stale)` over a graph that answers four different ways, plus an
anti-vacuity test that the graph is not uniform.

## Item 3, done in the working tree rather than only in a fixture

```
places the startable rule is stated: 2
  bin/lib/__init__.py § resolve_startability
  bin/perry-task § _reintroduced_copy_of_the_rule
exit=1
```

3 of 19 unit tests red; removing the copy returned exit 0 and 19/19.

## It found the baseline red, independently of its sibling

At `ce89cde`, clean tree, before touching anything:
`test_the_queue_register_reconciles_with_the_queue_on_this_repository` fails
`1 != 0`, on all three runs. **Not a flake, not `test_host_support`.**

Root cause it established: `perry-diagnose` scans the whole repo including test
fixtures and counts `tests/fixtures/sample-project/BOARD.md:36 — USER-014` as one
of Perry's own open decisions; `perry-task` reads only `perry/BOARD.md`, where
all four USER rows are answered, and reports 0. **Every one of Perry's own queue
rows being answered is what exposed it.** Now TASK-153.

**The PMO's "all green" reading was taken at an earlier commit and quoted as
though it held at `ce89cde`.** Two agents caught it independently; the third was
sent a correction mid-run.

## One question worth keeping

`_cmd_list_from_board` computes `startable`, `blocked_stale` and `blocks` on
**every write** and then discards them, because `perry_store.record` keeps only
the twenty stored fields. Not a defect, and not something to change inside a
de-duplication — but somebody eventually asks why the write path computes a
graph it throws away.

## Merged

`--no-ff`, after `merge-check` cleared the pair `t148 × t149` and correctly
attributed `test_diagnose` to the base rather than to either branch. Post-merge:
**72 modules · 2078 tests · 1 red — TASK-153 only.** `perry-lint` 0 errors.
