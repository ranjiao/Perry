# TASK-303 — the census, and the row it closed

> Produced 2026-09-02 by the dispatched agent. It changed no code and committed
> nothing, so this file is the deliverable. **Result: `already-done`.**

## Method

Every `.py` file in the repository parsed with `ast`. For each call to
`rglob` / `glob` / `iterdir` / `walk` / `copytree`, the **source text of its
root argument** was extracted and each root symbol resolved by reading its
definition. **No module was executed to measure it** — the previous attempt at
this row stalled doing exactly that, at "130 MB per probe".

## The spec's population was wrong at the first step

The dispatching spec said "forty-four walkers, sixteen using copytree",
derived by grep. Of the 43 `.walk(` hits under `tests/`, **41 are `ast.walk`** —
in-memory syntax-tree traversal that never touches a disk. Verified
independently by the PMO: 41 `ast.walk(` against 1 `os.walk(` in `tests/*.py`.

So the spec did not merely count names instead of call sites; it counted a
different function.

## 145 real filesystem sites, bucketed

| Bucket | Sites | Verdict |
|---|---|---|
| **A. bare root, recursive, unfiltered** | **3** | **the population** |
| B. bare root, recursive, already self-excluding | 2 | `bin/lib/__init__.py:939` (`SKIP_DIRS`), `tests/tree_guard.py:225` (`IGNORE_DIRS`, since TASK-249) |
| C. bare root, pattern-scoped | 3 | `schema/*-contract.md`, `decide/**/*.md` — cannot descend `.claude` |
| D. bare root, one level, dot-names filtered | 3 | `iterdir`, no recursion |
| E. named subdirectory | 65 | `ROOT/"perry"`, `PERRY_HOME/"bin"`, `root/"journal"`, … |
| F. tempdir / fixture | 56 | `SAMPLE`, `FIXTURE`, `mkdtemp()`, … |

Also verified **absent**: no `os.listdir`, `os.scandir`, `glob.glob`,
`Path.walk`, bare-name `copytree`, or shell `find` / `grep -r` walkers anywhere.

## The population is three, and all three were already fixed

| Site | Fixed by |
|---|---|
| `tests/header_rule.py:163` — `readers_under`, `root.rglob("*")` | `TASK-244` (`NOT_A_READER`) |
| `tests/test_header_rule_harness.py:1130` — `copytree(PERRY_HOME)` | `TASK-244` (`NOT_COPIED`) |
| `tests/test_tree_guard.py:102` — `copy_repo` | `TASK-258` (`git archive`) |

**The dispatch said "exactly two". It is three** — `:1130`'s `copytree` is a
distinct expensive bare-root walker that TASK-244 fixed with a *separate*
constant, not a restatement of `readers_under`. It is what made the previous
attempt stall.

**The dispatch's "only three glob the bare root" was also incomplete.** Four
more take the bare root: three one-level `iterdir` sites with dot-names
filtered, and `test_one_header_rule.py:65` `readers_under(PERRY_HOME)` — a
genuine bare-root rglob **named nowhere**. The conclusion survives; the list
did not.

## Mutation, with worktrees present throughout

Rebinding only `header_rule.NOT_A_READER` in-process against the live checkout,
read-only:

```
MUTANT  .claude NOT excluded   16 worktrees, 339 readers   10 tests  144.03s  RED
        AssertionError: ('carried', '.claude/worktrees/agent-a0e8e0b03c5bdb787/…
FIXED   .claude excluded       17 worktrees,  19 readers   10 tests   10.35s  GREEN
```

The worktree count rising 16 → 17 mid-run is independent evidence they were on
disk for both halves.

## A second beneficiary nobody named

`tests/test_one_header_rule.py:65` binds `READERS = readers_under(PERRY_HOME)`
**at module level**:

```
MUTANT  359 readers, 14.62s import   13 tests  128.03s  GREEN
FIXED    19 readers,  1.13s import   13 tests    8.11s  GREEN
```

**15.8x, green both ways** — pure cost, invisible to every failure set, and
absent from TASK-244's before/after ranking.

## One number that must never be quoted again

TASK-244 reported `1800 sites / 65.30s` for the unfixed walk. This census
measures **1350 / 55.54s** on the same code. Neither is wrong: the figure is a
function of how many agent worktrees were on disk that minute — 10 then, 17
now. The agent's phrasing is the one to keep:

> **a valid diagnosis and an invalid constant.**

The stable half reproduces exactly: 75 sites / 3.94s against TASK-244's
75 / 3.43s.

## Unresolved, as reported

- The two fix branches were never observed green **side by side in one suite
  run**; the mutation rebinds the constant in-process instead, byte-identical
  to TASK-244's value.
- `TASK-258`'s `git archive` conversion was verified **statically**
  (`git ls-files .claude .gstack` = 0), not by running `test_tree_guard`, and
  its 32.19s / 19,187-file figure was not re-derived.
