# TASK-162 — result

> Date: 2026-08-21 · Executor: claude-subagent · Merged locally, **first real
> conflict of the night**, resolved by keeping both sides
> Branch: `coding/task-162-ask-as-node` · Cycle time: ~31 min
> `perry-task/list` **1.13 → 1.14** with a `semantics` entry naming **five keys
> whose meaning moved**

## Yes — and the argument is that Perry already writes this edge

> `perry-task ask --blocks TASK-114` puts the task id in the queue row's
> `Blocks` cell. `perry-task depends TASK-114 --on USER-015` puts the ask id in
> the task row's `Depends on` cell. **Two ends of one edge, written by two
> subcommands of one tool into two registers of one lane.** The only thing
> missing was a reader that joined them.

And refusing the write *"would have left `ask --blocks` declaring an edge the
graph is forbidden to know about — the same disagreement, arrow reversed."*

**The line it draws:**

> What makes something a node is **not being a task** — it is **having a state
> this tool can read that reaches a terminal value.** A task is `done`/`dropped`;
> an ask is `answered`; a `DESIGN-` or `ADR-` handle is neither and never will
> be, so those stay unknown and unsatisfied.

`answered` is `bin/perry-state § answered` — **called, not re-spelled.** Its own
docstring records it had already been written twice; *"a row's dependency being
satisfied is a worse place for a fourth copy than a dashboard count was."*

## It corrected the spec's premise

The spec said `perry-lint` and `perry-task list` *"currently do — both report
it"*. **They did not.** `perry-lint` said nothing about TASK-114 at all, because
**it carries no dependency-resolution check.** The two tools "agreed" by one of
them being silent. Now they agree by both reporting nothing:

```
depends_on_unknown: []   blocked_without_dependency: []   blocked_by_closed_rows: []
TASK-114  status=blocked  depends_on=[USER-015]  blocked_by=[USER-015]
          startable=false  blocked_stale=false
```

## It fixed the duplication before adding to it

`blocked_by`, `blocks` and `depends_on_unknown` were written out at **both**
list call sites, ~200 lines apart — *"the exact shape TASK-141 already paid for
once with `startable`. This change would have been the second fix applied
twice"* — so all three moved into `resolve_dependency_edges` first.

## And it hit the id trap in its own draft

Its first test spelled the example ids literally and **pushed `dangling` to three
entries and diagnose's queue count from 2 to 3** — *"it made an already-red check
redder."* Both are now assembled in two pieces with the reason in a comment, and
the contract prose was reworded to avoid id-shaped tokens. Post-change
`dangling` and `open_decisions_by_register` are byte-identical to its baseline:
**this branch contributes zero to either.**

## The conflict, and how it was resolved

First textual conflict of the night — `merge-check` caught it **before** a blind
merge. TASK-162's branch predated TASK-131 and TASK-160, and all three touched
`schema/task-list-contract.md`. Both sides were additive and both were kept: the
sketch takes **1.14** *and* keeps TASK-131's `semantics` row; the changelog
carries `### 1.14` above the same-day *"not a version"* note. Fixture
re-recorded; parity still **0**.

## Three questions handed back

1. **`perry-lint` has no dependency-resolution check at all**, so
   `depends_on_unknown` and `dependency_cycles` are visible only through
   `perry-task list --json`. Should lint surface the family, or is `list`
   deliberately the only mouth?
2. `depends_on_unknown` is empty again, so its key table goes back to unplaced —
   *"the check is silent about that table until the day some row is genuinely
   mistyped again."* TASK-161's shape, from the third direction.
3. **`ask --blocks` takes free text, not a validated id list.** Now that the
   other end is typed and resolved, **the two ends can disagree**: a queue row
   can say it blocks a task while that task names a different ask or none.
   Nothing checks the pair.

## A side effect worth recording

With TASK-162 landed, `dangling` is **`[]`** on this repository and `TASK-007`
and `TASK-9999` sit in `dangling_in_reports`. TASK-165 — *quoting a checker's
output re-dangles the ids inside the quote* — resolved itself, because
TASK-126's rule needs **both** halves and both are now satisfied. **The residual
cost, re-scoped onto that row: an id must go red once before the exemption can
cover it.**
