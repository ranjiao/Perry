# ADR-003 — OKR v2 adds Objective 5 for the runtime layer (DESIGN-006)

> Status: active
> Type: Process
> Date: 2026-08-17
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

`DESIGN-006` ("Roles and knowledge") resolved all six user decisions on
2026-08-17 — the same day OKR v1 was set. None of v1's four objectives covers
the runtime layer it defines, and `reference/okr-linkage.md` is a hard gate:
an implementation phase that cannot resolve to a KR is `unlinked` and excluded
from every roll-up. The design's § 8 required settling linkage before handoff.

## Options

1. **`goals revise` — add an objective** (chosen). Honest admission that scope
   grew; costs a same-day version bump and a fifth objective on a board that
   had four.
2. **Attach to O3** ("Perry is landed on three named real projects").
   Defensible only via phase F's real-project pass condition; O3's KRs measure
   lint errors and adoption, which knowledge-layer work does not move — a weak
   attribution that would inflate O3's roll-up. Rejected as the guessed
   linkage the gate exists to forbid.
3. **Stay unlinked, defer implementation** to the next OKR version. Most
   conservative; rejected because the design's decisions were fresh and the
   user chose to proceed.

## Chosen

Option 1. `OKR.md` v2 (2026-08-17) adds **Objective 5 — "Tasks are executed by
roles that know things"**, `KR-O5.1`–`KR-O5.4`, all commit, no stretch —
KR-O5.4 is `DESIGN-006` phase F's pass condition, and marking it stretch would
permit the abstraction to go unvalidated for the whole period. O1–O4 carried
over unchanged (restated in the v2 block because readers parse only the
current version block). `DESIGN-006`'s header now links `O5 / KR-O5.1–KR-O5.4`.

## Consequences

- OKR grows to five objectives — above the 1–3 the `goals` lane recommends for
  solo projects. Accepted consciously; v2's retro should say whether five was
  dilution.
- `DESIGN-006` implementation phases A–F attribute cleanly; nothing lands
  `unlinked`.
- KR ordering encodes the design's decision #1 (knowledge first): O5.1/O5.2
  deadlines precede O5.3/O5.4.

## What would reopen this

- v2 retro finds five objectives diluted execution → fold O5 into a leaner v3.
- `DESIGN-006` is dropped or superseded before phase A starts → O5 has no
  design behind it and must be revised out, not left dangling.
- KR-O5.4's finance-shaped end-to-end run proves infeasible by 2026-11-01 →
  re-scope the KR rather than silently re-dating it.
