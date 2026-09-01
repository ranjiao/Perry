# ADR-012 — The projection may be stale; freshness is the agent's job, not a gate

> Status: active
> Type: Architecture
> Date: 2026-09-01
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

On 2026-09-01, writing `OKR.md` v3 turned up a hole, measured on a scratchpad
copy rather than reasoned about:

- Append two records to `okr.jsonl`, the canonical store, and run `perry-okr
  render --write`. The command reports *"rendered from 38 stored record(s)"* and
  **the file is byte-unchanged** — a version heading is layout, and layout is
  reproduced verbatim rather than generated.
- `perry-okr diff` then reports `identical: true`, exit 0. `perry-okr verify`
  reports `drift_count: 0`, `byte_identical: true`, exit 0.
- `perry-lint` reports `38 record(s), 2 row(s) drifted`.

So a record added to the canonical store can be invisible in the projection,
and the two tools named after that store both say it is fine. One question,
three tools, two answers — the same class as `TASK-243` and `USER-909`.

The obvious reading is "fix the two tools". The cost of that reading is
measured and known: `evidence/2026-08/2026-08-31-representation-layer-delete-list.md`
prices the drift machinery at **~3,100 lines** and records that it has caught
**zero real incidents** on this repository — every non-zero drift reading in
Perry's history came from a V4 reviewer deliberately corrupting a store to
demonstrate a bug — while generating `TASK-031`, `067`, `093`, `203` and `243`.
`ADR-011` already condemns it as Tier B, conditional on nothing reading a
rendered file as authority.

## Options

1. **Enforce consistency.** Make the store→projection direction a guarantee:
   every store write renders, and a mismatch is an error. This is the reading
   that treats the measurement above as a bug, and it buys the guarantee at the
   price of the machinery that has never caught anything.
2. **Report it, do not enforce.** Keep a check that names a stale projection
   without refusing anything. Cheaper than 1, and still a permanent surface to
   maintain and to keep correct across every store.
3. **Tolerate staleness.** No guarantee is offered. A stale projection is an
   ordinary state, the agent notices it and re-renders.

## Chosen

**Option 3.** Consistency between a `.jsonl` store and its `.md` projection is
**not guaranteed and not enforced.** The store is canonical; the projection is a
convenience that may lag it.

**Detection is the agent's, by modification time**, at the point where it is
about to rely on a projection:

```
mtime(store) > mtime(projection)   ⇒   re-render, then proceed
```

**The judgement is "re-render", not "stale".** mtime gives an ordering, and an
ordering is not a verdict — the import direction (`perry-okr write
--from-file`) and a plain re-render both leave the store newer than the file
without anything being wrong. This repository is in exactly that state as this
ADR is written: `okr.jsonl` is 19 seconds newer than `OKR.md`, because v3 was
imported from the file, and `perry-okr diff` reports the two identical.

That false positive costs nothing, and that is what makes the rule safe:
**rendering is idempotent.** Re-rendering an already-current projection
rewrites the same bytes. So the rule never needs to be right about *why* the
ordering is what it is — it only needs to be cheap when it is wrong.

## Consequences

**`ADR-011` Tier B loses its last argument for staying.** Its precondition was
that no code path reads a rendered file as authority. This decision adds that
even when one is read, being out of date is not an error — so the census is
checking a property nobody is promised. Tier B's line count does not change;
its justification gets shorter.

**`perry-okr diff` / `verify` and `perry-lint`'s drift lines become development
tools, not gates.** They still answer a real question and they may still
disagree with each other. Nothing is promised on the strength of their answers,
so their disagreement stops being a defect that must be closed. The intake row
that recorded it is discharged by this decision rather than fixed.

**Detection has to exist somewhere or the rule is aspirational.** "The agent
notices" is a procedure, and Perry's own history says an instruction with no
surface behind it does not run — `goals/reference/setup.md § init`'s ten-field
checklist is the standing example. A one-line mtime comparison belongs in the
state payload the snapshot already reads, and `TASK-266` is that row. It
replaces ~3,100 lines with a subtraction.

**The reverse direction is NOT decided here.** A projection *newer* than its
store may be a hand edit or may be a fresh render, and mtime cannot tell them
apart — `.perry/config.md` is 29 hours newer than `.perry/config.jsonl` right
now, and nothing in this ADR says which of the two that is. Perry's Operating
Principle — *"Every write goes through a tool. A hand edit is reported, never
refused"* — is unchanged and is restated in `OKR.md` v3. This decision governs
store-newer-than-projection only, because that is the direction the measurement
was about and the direction the user decided.

**What is given up, plainly.** A reader who opens `OKR.md` or `BOARD.md`
directly can be looking at yesterday's numbers with nothing on the page saying
so. Under `ADR-010` and `ADR-011` those files are on their way out and the
render is becoming the reading surface, which is why the loss is acceptable
here and would not have been in August.

## What would reopen this

- **A stale projection read as truth, costing something real.** Not a fixture:
  an actual decision taken off a lagging file. That is the incident the drift
  census never produced in a year, and it would be the argument for option 2.
- **The reverse direction turning out to matter more than expected** — someone's
  hand edit to a projection being silently overwritten. That reopens the
  question this ADR deliberately left alone.
- **A consumer outside Perry reading a projection**, where "the agent
  re-renders" is not available because there is no agent in the loop.
