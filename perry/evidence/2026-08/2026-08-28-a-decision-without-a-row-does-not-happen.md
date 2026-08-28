# DESIGN-007: five plan steps had task rows and all five shipped; nine had none and none did

> Measured 2026-08-28, while assembling the open user decisions. It changes
> what "make a decision" costs, so it is written before the decisions are made.

## The count

`DESIGN-007-the-entity-model.md` is `locked` (2026-08-19) and carries a
fourteen-step implementation plan.

| | steps | outcome |
|---|---|---|
| **had a `TASK-` row** | 5 | **5 of 5 `done`** — TASK-090, 105, 106, 102, 092 |
| **had no row** | 9 | **0 of 9 shipped** |

Verified against the live store rather than inferred:

```
#3  Task stores `phase`      → perry/tasks.jsonl has no `phase` field
                               schema/task-list-contract.md: 0 hits for "phase"
#4  KR id P<NNN>-O<n>-KR<m>  → 0 traces anywhere (now TASK-180)
#5  every Task has a spec    → `perry-task add` does not require one
#7  a Run is recorded        → no runs store, no run-kind event in 828 events
#2/#8 Agent is a store       → no agents store, no `.perry/roles/`
    V5 re-signature on the hand-off contract → not done
```

## The mechanism, stated plainly

**A locked decision that gets a task row ships. One that does not, does not.**

Five for five and nought for nine is not a sample that supports subtlety. The
decision being *locked* did nothing on its own; `Status: locked` and a numbered
plan are both satisfied by a document that changed no code.

This is the third instance of the shape found in two days, and the other two
were each treated as a one-off:

- **`.perry/config.jsonl`** — TASK-092 shipped half its title. The phase KR
  honestly recorded `1 of 2`, and no row carried the other half.
  (`2026-08-28-a-kr-with-no-open-task.md`)
- **DESIGN-007 #4** — locked nine days, zero traces, and `perry-lint:1122`
  recovers the phase from a *filename* because the id does not carry it.
  (`2026-08-28-a-locked-decision-that-never-shipped.md`)

They are one finding. **Perry has no link from a locked decision to the work
that discharges it**, so a decision's implementation is carried by whoever
happens to remember it.

## What it implies for the twelve open decisions

DESIGN-009, DESIGN-010 and DESIGN-011 each carry four unresolved User Decisions
and each says *"ALL rows must be resolved before this doc can move to `Status:
locked`"*.

**Resolving them produces three more locked documents.** On this evidence that
is not the same as producing the work. **A decision should be resolved and given
a row in the same action**, or the twelve join the nine.

The cheap version needs no new concept: `decide lock` already hands
implementation tasks to `work` — the hand-off contract says so in as many
words — *"`decide` … Proposes, never writes: implementation tasks on lock,
handed to `work`"*. **That hand-off is documented and did not happen for nine of
fourteen steps.** Whether it is unimplemented or merely unenforced is the row.

## The check that would have caught it

A locked design with a plan step naming no task, and no task naming the design,
is a decision nobody owns. Both halves are already queryable:
`tasks[].depends_on` accepts a `DESIGN-` handle, and `perry-explain` resolves
one. **Nothing joins them.**
