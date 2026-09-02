# ADR-016 — Zero new claimed paths becomes: every new claim carries a recorded argument

> Status: active
> Type: Architecture
> Date: 2026-09-02
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

`DESIGN-002` established that every path Perry writes is a claim on a namespace
it does not own. `DESIGN-003` goal 5 hardened that to **zero new claimed
paths**, and `DESIGN-004` goal 5 repeated it — which is why the event log went
to `.perry/` and `DESIGN-004 § 5.3` says so explicitly: *"`.perry/` is already
in `claims[]`, so this adds no new claimed path — goal 5."*

`ADR-006` then moved the canonical task store to the state root and argued
location-as-claim for it — correctly, on its own terms — **without ever naming
the rule it was setting aside.** From there the surface grew without further
discussion.

Measured 2026-09-02: **18 claims at `DESIGN-002`'s lock, 24 today.**
`DESIGN-015` proposes a 25th (`linkage.jsonl`) and `ADR-014` a 26th (the ADR
id high-water mark). Both were decided the same day, by the same session, and
neither was weighed against goal 5.

`DESIGN-015` is the one document that notices, and only as a risk row:
*"declaring `linkage.jsonl` in `claims[]` makes Perry occupy that path in every
project."* That is the goal-5 argument arriving four stores late, as a
mitigation rather than as a rule. Raised by the 2026-09-02 design-register
audit as `C-05`, whose framing is the one adopted here: *"Either goal 5 is
retired in writing — with the reason, since it is the whole basis of
`DESIGN-002`'s escape hatch — or every new store is a claims-surface change and
needs the argument `DESIGN-015` gives. Right now it is neither."*

**This is not a hypothetical cost.** `TASK-294` records that all five live
`NS-01` warnings fire on files Perry itself wrote, in directories Perry claims,
and that the remedy each offers is a no-op. The claim surface is already
producing noise that every session — including the one that filed it — trained
itself to skip.

## Options

1. **Restate the rule: every new claim carries a recorded argument — chosen.**
2. **Retire goal 5 in writing.** Honest about what has been happening.
   Rejected: it removes the basis of `DESIGN-002`'s escape hatch and leaves
   nothing between Perry and a growing surface, at the moment `TASK-294` shows
   that surface already misfiring.
3. **Reinstate goal 5 as binding — zero, and mean it.** Rejected: it reopens
   `linkage.jsonl` and the high-water mark store, both decided the same day on
   arguments that hold, and it would have to reject `ADR-006` retroactively.
4. **Leave it undecided.** Rejected — it is the current state and it is how the
   surface got from 18 to 24 unremarked.

## Chosen

**Option 1.** Goal 5 stops being *"zero new claimed paths"* and becomes:

> **A new claimed path is a decision, not an implementation detail. It is taken
> in writing, with the argument for why the fact belongs at that path rather
> than inside a claim Perry already holds, and with the cost to a project that
> has a file of that name.**

`DESIGN-015`'s risk row and `ADR-014`'s consequences section are the shape this
requires; both already meet it, which is why neither is reopened.

## Consequences

- `DESIGN-003` goal 5 and `DESIGN-004` goal 5 are superseded in substance.
  **Both documents are locked**, so each gets a `## Changes` entry pointing here
  and the goal text stays — an append-only record does not rewrite what it
  corrects.
- `ADR-006` set the rule aside without naming it. This ADR names it
  retroactively; `ADR-006`'s own decision is untouched.
- **The number becomes something to watch rather than something to hold at
  zero.** 24 today. A future phase that adds four more should be able to point
  at four arguments.
- **This does not make the surface safe.** `TASK-294` is the live evidence that
  a claim can misfire on Perry's own files; an argued claim is still a claim.
- `DESIGN-002`'s escape hatch — `/perry relocate` — is now the mitigation rather
  than the boundary, and `TASK-294` records that its remedy text is currently a
  no-op on this project. That is a defect in the hatch, not in this decision.

## Evidence

- `DESIGN-003` goal 5, `DESIGN-004` goal 5 and `§ 5.3`'s explicit appeal to it.
- `ADR-006` — the first departure, unnamed.
- `schema/state-schema.json § claims[]` — 24 entries, measured 2026-09-02.
- `DESIGN-015 § 7` and `ADR-014 § Consequences` — the argument shape now required.
- `TASK-294` — the claim surface misfiring on Perry's own files.
- The 2026-09-02 design-register audit, finding `C-05`.

## What would reopen this

- The claim count grows without the arguments existing, which would mean the
  restatement bought nothing that "zero" did not.
- `/perry relocate` stops being a real escape hatch, at which point a claim is
  no longer reversible and "zero" was the right rule after all.
