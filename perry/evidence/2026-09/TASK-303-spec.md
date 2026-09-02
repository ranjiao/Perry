# TASK-303 — spec

> Dispatch mode: auto
> Executor: claude-subagent (test-harness surgery in this repository; stdlib only, no MCP)
> Estimated cycle: large
> Subjective verification: whether a walker that legitimately needs untracked files has been mis-converted — a human checks the exceptions list
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked
- **Verification rung**: V4

## Why

Measured 2026-09-02 on this repository:

```
git ls-files                     →   791 files   (the repository)
find .claude/worktrees -type f   → 7,675 files, 130 MB, ten agent worktrees
```

**Forty-four files under `tests/` walk the filesystem** — `rglob`, `os.walk`,
`PERRY_HOME.glob` or `shutil.copytree` — and **not one excludes `.claude/`.**
So whenever agents have worktrees checked out, every one of them sees roughly
**ten repositories instead of one**.

**Sixteen of them use `copytree`**, which does not merely scan the extra files
but copies them:

```
store_fixture.py            ← a SHARED HELPER; fixing it once may fix several
test_attribution_buckets    test_board_render        test_decoration_changes_nothing
test_linkage_writer         test_md_store            test_ns_collision
test_one_startable_rule     test_parsers             test_phase_kr_declared_once
test_resume                 test_task_store          test_unlinked_declaration
test_work_modes
```

**Two symptoms, one root.** The correctness one is live:

```
FAIL: test_the_uncovered_remainder_is_the_measured_one
      (test_header_index_is_the_only_fold.TestOnlyHeaderIndexFoldsAHeaderCell)
AssertionError: Lists differ: 270 additional elements
First extra element 8:
  ('carried', '.claude/worktrees/agent-a0e8e0b03c5bdb787/bin/perry_md_store.py', '_table_sites')
```

It **looks flaky and is not** — it appears and disappears with agent activity.

The cost one is the 286.4s the other 107 modules take with the binding module
excluded. **That figure is this row's target.**

## The fix shape is already proven twice, in this repository

`TASK-258` replaced `shutil.copytree` with `git archive` in
`tests/test_tree_guard.py` and measured **4.6× faster per copy** (0.42s vs 1.9s
for 846 entries). More importantly for this row: **`git archive` and
`git ls-files` see tracked files only, so they exclude `.claude/worktrees` by
construction** — no exclusion list for anybody to maintain and no list to go
stale when a new untracked directory appears.

Prefer that over adding `.claude` to an ignore pattern. An ignore list is a
second place the truth lives.

## Files in scope

The forty-four walkers, **minus two**:

- **`tests/test_header_rule_harness.py` is `TASK-244`'s** and is being worked
  concurrently. Do not touch it.
- **`tests/test_tree_guard.py` is already converted** by `TASK-258` (branch
  `coding/task-258-tree-guard-fixture`, unmerged). Read it as the worked
  example; do not redo it.

Start with `tests/store_fixture.py`, the shared helper — measure how many
modules it serves before touching anything else.

## Deliverable

A tree-walking test sees **the repository**, not the repository plus every
worktree checked out under it.

`test_header_index_is_the_only_fold` is green **with worktrees present**, and
the ranked per-module timings drop.

**Some walkers may legitimately need untracked files** — a test about NS-01
namespace collisions, for instance, is *about* files Perry did not write. Those
are exceptions, not failures: convert what should be converted, list what
should not, and say why for each. A blanket conversion that breaks a test whose
subject is untracked files would be the wrong reading of this row.

## Out of scope

- **Deleting the worktrees.** They are other agents' working state, one of them
  belongs to a live agent, and a staleness check on them was already wrong once
  today. Measure with them present.
- `tests/test_header_rule_harness.py` (`TASK-244`) and `tests/test_tree_guard.py`
  (`TASK-258`).
- What any test is testing. This row changes what a harness SEES, never what it
  asserts.
- `tests/run` and `tests/parallel`'s reporting (`TASK-251`).
- Any project other than Perry's own.

## Verification

- **`test_header_index_is_the_only_fold` passes with the ten worktrees still on
  disk.** Prove the worktrees were there — count them in the same run.
- Ranked per-module timings before and after, on a quiet machine, **with the
  load average reported both times.** On this machine today the same module
  ran in 15s and in 283s depending on load; a timing claim without a load
  figure is not evidence.
- **The suite still finds what it found.** Name the baseline failure set
  explicitly. It is currently two modules red:
  `test_header_index_is_the_only_fold` (this row) and `test_parsers`
  (`TASK-292`, fixed on an unmerged branch — do not fix it here).
- **Mutation, and it is the acceptance**: point one converted walker back at
  the filesystem and its test must go red **while worktrees are present**. A
  conversion that passes either way has not been shown to do anything.
- Clear `__pycache__` and wait past the second boundary before each re-run.

## Bound

**One root, one conversion pattern, one exceptions list.** Size 3:

1. the census — which of the forty-four walkers were converted, which were
   listed as legitimate exceptions, and why for each;
2. the conversion itself, starting from `store_fixture.py`;
3. the red test green with worktrees present, plus the mutation.

**A module that is slow for a different reason is a new row.** The round ends
when no walker sees `.claude/worktrees` except the ones that are declared to
need it.
