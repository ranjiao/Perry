# TASK-218 — thread the closing phase id through every close stage

> Design: **DESIGN-012** § 5.1 invariant I1 (`design/DESIGN-012-close-phase.md`), locked 2026-08-28.
>
> Dispatch mode: auto
> Executor: codex (high confidence — self-contained call-site work across `bin/`, no MCP needed)
> Estimated cycle: medium
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Rung**: V4
- **Dependencies**: TASK-217 (the pages must agree on the order first, and `phases.md` step 7 must stop clearing `phase/CURRENT`)
- **KR linkage**: unlinked — see § Attribution

## Why

Each of the four phase-close stages re-reads `phase/CURRENT`. The moment one
stage advances it, every later stage is aimed at the wrong phase.

Observed 2026-08-28: `goals plan-phase 003` had already run, so `CURRENT` read
`003-storage-code` when `work end-phase-retro` was invoked for phase #002.
`end-phase-retro`'s own procedure says to read "journal entries since **the
current phase** started" — a phase one day old. Executed literally it produces
an empty retro. It was aimed at #002 by hand.

This is a data-flow bug, not a documentation bug. TASK-217 fixes the pages;
after it lands, nothing still stops the same thing happening.

## Deliverable

All four stages — `goals score-phase`, `work end-phase-retro`, `work rollover`,
`goals plan-phase` — accept the closing phase id as an **input**. The id is
resolved once, at entry, and held. No call site in `bin/` re-reads
`phase/CURRENT` during a close.

## Verification — V4

1. **Reproduce first.** Advance `phase/CURRENT` to the next phase after stage
   1, run `end-phase-retro`, and show the empty retro. The 2026-08-28 incident
   is the fixture; a fix whose failure was never demonstrated is untested.
2. **Then fix, and show the same input targeting the closing phase.**
3. **Count call sites by grepping the expression, never the name.** Phase
   #002's most expensive recurring defect was locating an implementation by
   name — it recurred roughly ten times, once finding one call site where there
   were three (`phase/002-fields-are-typed.md § Lessons for phase 003`, lesson 1).
4. Full suite green.

## Out of scope

- The `close-phase` router subcommand — **TASK-220**.
- `phases.md` step 7's `CURRENT` edit — **TASK-217**, and it is a dependency
  rather than part of this row.

## Attribution

Serves `DESIGN-012` / `KR-O2.3`, not a phase #003 KR. Phase #003's eight KRs
are all store-and-code subjects. Under `P003-O3-KR2` this row needs a **declared
`unlinked`** rather than a guessed edge, and that write belongs to `goals`
(`/perry goals link --unlinked`), not here.
