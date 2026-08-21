# TASK-045 — retire the runtime tolerance branches, behind the conformance marker

**Merged locally 2026-08-21** from `coding/task-045-retire-tolerance` @ `e8f899a`.
Rung **V3**, not the V4 the row carried — no independent review round ran.
`merge-check` alongside TASK-040: nothing new is red. Post-merge suite:
**80 modules · 2331 tests · 2 red**, both pre-existing.

The count, the full 19-item enumeration, the mutation result and the ADR-004
quote are in the merge commit. Two things worth keeping here.

## The precondition was verified before dispatch, not assumed

The row sat blocked three days on `044 → 047 → 045`, and the blocker was the
gate shipping `advisory`. Checked at dispatch: `perry-conform status` →
`gate: enforce`; TASK-044 done V4, TASK-047 done V5.

## Verified independently after the merge

`bin/perry-state:897` says `"High-stakes"` is *"a PREFIX this file accepts and
the schema does not declare"*. `schema/state-schema.json:2068` declares
`"match": "^High-stakes|^高风险操作"` — that prefix. **The comment is stale and
the code is right**, which is what the agent reported and did not change.

## Why one retirement is the honest answer

Every row of ADR-004's own *Context* table had already been discharged some
other way — the four-column intake by resolving columns **by name**, TASK-040's
two by `require_migrated` plus `risk-migrate`, M-8 by `--group` which the ADR
then declined to decide, and `parse_due` by the ADR saying it *"is not covered
by this"*.

And the reframing: **the schema absorbed most of the tolerance rather than the
tools shedding it.** `## Top risks` carries `"optional": true`, `Idle` is
declared *"Read when present so no existing board breaks"*, `Last evidence` was
demoted from required. Those read as tolerance branches in the code and are
declared shapes in the schema. Deriving the list from the code alone — the
thing the spec warned against — deletes several of them.

## On the rung

V4 asked for an independent fresh-context review of the enumeration. One agent
produced it and the PMO checked the ADR quote, the diff boundaries and one of
the four findings. That is V3.
