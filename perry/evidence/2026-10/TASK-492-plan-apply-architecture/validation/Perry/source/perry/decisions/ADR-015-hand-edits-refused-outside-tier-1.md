# ADR-015 — A hand edit to a projection is refused, not reported; tier 1 stays the user's

> Status: active
> Type: Architecture
> Date: 2026-09-02
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

Perry's Operating Principle reads: *"Every write goes through a tool. A hand
edit is reported, never refused"* — and it names its own mechanism,
`DESIGN-004 § 5.4`: *"Editing your own markdown stays legitimate; drift
detection is what makes it visible."*

**That mechanism is being deleted.** `ADR-011` puts the drift census (~3,100
lines) in Tier B on the measurement that it *"caught zero real incidents"*.
`ADR-012` goes further and says so outright: the drift readers *"become
development tools, not gates … Nothing is promised on the strength of their
answers."* In the same section it restates the Operating Principle as
**unchanged**. It is unchanged in wording and gone in mechanism — "reported"
now means a number in a lint run nobody is required to read, produced by a
subsystem two ADRs have condemned.

`ADR-012` is also explicit that it does not rule the dangerous direction:

> **The reverse direction is NOT decided here.** A projection *newer* than its
> store may be a hand edit or may be a fresh render, and mtime cannot tell them
> apart.

Store-newer is safe by construction — rendering is idempotent. **Projection-newer
is the case where a re-render silently overwrites someone's edit**, and after
`ADR-012` it has neither a rule nor a detector. Raised by the 2026-09-02
design-register audit as `G-03`.

**The principle was written for a world that no longer exists.** It comes from
`ADR-004`'s posture — a real project's files predate every rule Perry has — and
`ADR-004` is superseded. `ADR-010` says `BOARD.md` stops existing; `ADR-011`
removes the representation layer; `DESIGN-013 § 5.1` makes a schema'd fact live
in exactly one store. **A file that is a rendered view of a store is not a file
hand-editing means anything to.**

## Options

1. **Refuse the hand edit outside tier 1 — chosen.**
2. **Rule the reverse direction and keep reporting** — give projection-newer a
   detector and keep hand edits legitimate everywhere. Rejected: it rebuilds the
   subsystem `ADR-011` and `ADR-012` just condemned, to protect edits to files
   that are becoming renders.
3. **Accept the hole and say so** — record that the principle no longer holds in
   that direction. Honest, and rejected because it leaves a known hole for the
   next person while the principle's wording still promises otherwise.
4. **Measure first, decide after** — the PMO's recommendation on the day. The
   user overrode it, on the ground that the design direction already settles it:
   `BOARD.md` is meant to be discarded, so the question of protecting hand edits
   to it does not arise. Recorded because the override is the decision.

## Chosen

**Option 1, with the boundary drawn at the audience tier Perry already
declares** (`work/SKILL.md § Axis B`):

- **Tier 1 stays the user's, and hand editing it stays legitimate.** `OKR.md`,
  `phase/<NNN>-<slug>.md`, `.perry/hook.md`, `.perry/roles/*.md`. These are
  authored, not projected; the user must be able to read and change them raw.
- **Tier 2 is a projection and a hand edit to it is refused, not reported.**
  `BOARD.md`, `journal/`, `tasks.jsonl` and the other stores, `PROJECT_STATE.md`.

The Operating Principle's first sentence survives — every write goes through a
tool. Its second is replaced: *a hand edit is refused where the file is a
projection, and legitimate where the file is the user's.*

## Consequences

- **The Operating Principle in `OKR.md` must change, and this ADR cannot change
  it.** `OKR.md` belongs to the `goals` lane. This is a proposal to that lane,
  and until it lands the principle's wording and this decision disagree —
  recorded here rather than left to be discovered.
- `ADR-007` decision 2 made a hand edit **drift**; this makes it **refused** for
  tier 2. That is a strengthening, not a reversal, and ADR-007 is not superseded.
- **`ADR-012`'s undecided direction is decided by removal rather than by rule.**
  If a hand edit to a projection cannot happen, a projection newer than its
  store is a fresh render, and mtime no longer has two readings to distinguish.
- Something must actually refuse. Today nothing does — writers render over a
  projection without checking. That is the implementation this ADR authorises.
- **A cost worth naming**: a user who *wants* to fix a board cell by hand now
  cannot. The tool path must cover what hand editing covered, and
  `perry-task`'s six statuses plus `next` / `retitle` / `evidence` / `rung` /
  `prioritize` / `depends` are the claim that it does. Where it does not, the
  refusal will be discovered as an obstruction, and that is the signal to widen
  the tool rather than to relax the rule.
- One measurement this ADR does **not** rest on: on 2026-09-02 the PMO
  hand-edited a scratchpad `BOARD.md` and ran `perry-tasks render --write`; the
  file was not overwritten. The control test failed, so whether the destructive
  case is reachable today is **unmeasured**. The decision is made on design
  direction, not on a demonstrated incident.

## Evidence

- `ADR-012` — the undecided reverse direction, quoted above.
- `ADR-011` — the drift census in Tier B, "caught zero real incidents".
- `DESIGN-004 § 5.4` — the mechanism the Operating Principle names.
- `work/SKILL.md § Axis B` — the tier model this boundary uses.
- The 2026-09-02 design-register audit, finding `G-03`.

## What would reopen this

- The tool path fails to cover something hand editing covered, and the refusal
  becomes an obstruction rather than a guard.
- Tier 1 grows to include something that is in fact projected, at which point
  the boundary is drawn in the wrong place.
- `BOARD.md` survives as a file people read raw, in which case the premise that
  it is a projection is wrong.

## Changes

2026-09-08 — **`ADR-019` narrows one entry of this ADR's tier-1 list:
`.perry/config.md`.** That file stops existing, so "the user must be able to
read and change it raw" no longer applies to it. Everything else in this ADR
stands: the rule itself, the tier-2 half, and the other four tier-1 paths
(`OKR.md`, `phase/<NNN>-<slug>.md`, `.perry/hook.md`, `.perry/roles/*.md`).
Status stays `active`.

Recorded here as well as in `ADR-019` because the contradiction is only
visible from this side if this file says so. Noted in the same entry: this
ADR's list called `.perry/config.md` *"authored, not projected"* on 2026-09-02,
three days after `TASK-233` had already made it a projection — so the entry was
inaccurate when written, and `ADR-019` § Relationship to ADR-015 carries the
account.

