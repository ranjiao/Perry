# TASK-159 — result

> Date: 2026-08-21 · Executor: claude-subagent · Merged locally
> Branch: `coding/task-159-project-root` · Cycle time: ~55 min
> 5 files, +222/−47 · `tests/test_project_root.py` new, 24 tests

## It took the first shape and reached the third on the way

`PROJECT_ROOT` is now unambiguously where `.perry/` is anchored — what
`$PERRY_PROJECT` and `perry-state --root` already meant. `STATE_ROOT =
resolve_state_root(PROJECT_ROOT)`. And `resolve_project_root` is the inverse
`walk_design`'s own comment said nobody had written.

**The inverse needed no new stored field, because the anchor already is one:**

> `.perry/` cannot move, since it holds the pointer, so the project root is the
> nearest ancestor whose pointer resolves **back** to this state root.

Storing a second field would have stored the same fact twice — *"the exact
defect class this file's comments document at eleven other sites"* — and it is
precisely what would have needed the schema release the user is asleep for.

## What the other two would have cost, in its words

- **Launcher exports the state root** — makes today's viewer reading correct and
  leaves `perry-state --root` disagreeing with both, so `kr_chain` (which passes
  that value straight through) **breaks the chain card TASK-146 landed hours
  earlier**. It also contradicts `bin/README.md`'s declared `$PERRY_PROJECT`
  precedence that **ten other `bin/` tools read**, so the one-line fix propagates
  to all of them.
- **A new declared field** — a per-task release, and it would put a second,
  *writable* answer beside an anchor that cannot lie, with nothing keeping them
  in sync.

## Measured on this repository, pointed where the launcher points it

```
before   tasks 0 · adrs 0 · phase None · design 0
after    tasks 38 · adrs 9 · phase 002-fields-are-typed · design 8
```

The viewer was rendering **completely blank** on Perry's own project, from the
directory its own launcher exports.

## Item 4 — five reverts, five different reds

| revert | failures |
|---|---|
| `load_snapshot`'s default root back to `PROJECT_ROOT` | 6 |
| `/architecture` + `/file/<rel>` read from `PROJECT_ROOT` again | 2 |
| the CWD walk stops reading `.perry/config.md` | 1 |
| `resolve_project_root` drops the round trip, takes the first anchor | 1 |
| `walk_design` handed the state root as its project root again | 1 |

**The last one is the one that shows the inverse doing something the bounded
walk cannot**: a state root five levels down renders `/design` as *"1 task"* with
the exact root and *"no refs"* with the four-level walk.

`tests/test_kr_chain_render.py` is green under all five — this row does not touch
what TASK-146 landed, and **its degraded-mode wording is exercised here, not
changed.**

## The schema said to do this

`schema/README.md § Where the files are` turned out to **require** it: rule 1
declares `.perry/` is anchored at the project root — *that is the inverse*; rule
2 requires one resolver, and `resolve_state_root` is untouched and still the
only one; and it states `files[]` paths are relative to the **state** root,
which is the published reason `/file/<rel>` had to move.

## Five questions handed back, two of them small and real

1. `bin/perry-state:1818` assigns the **state** root to `P.PROJECT_ROOT`, a
   global that now definitively means the project root. **A no-op today** —
   `load_snapshot`'s default binds at def time — but it is a fourth spelling
   sitting one line from a comment explaining the third. **Two lines to delete.**
2. `perry-state --json` spells the state root `project.root`. A published
   contract, so it was read for what it is and said so in the test rather than
   renamed — *"but it is the same confusion in the payload's own vocabulary."*
3. `bin/perry-state § resolve_root` and `viewer/parsers.py` are now the same
   predicate in two bodies, asserted against each other rather than folded,
   because `bin/perry-state` was out of scope. **The fold is one import.**
4. `resolve_state_root`'s escape guard compares a resolved child against a
   possibly-unresolved parent, so on a symlinked path it rejects the project's
   own subdirectory. Never bites in production; cost the agent a fixture.
5. The launcher exports `pwd` verbatim with no `--root`. Started somewhere that
   is neither root, the viewer still degrades — **but it now degrades to exactly
   what `perry-state` says about the same directory**, so the two no longer
   disagree.
