# ADR-001: Perry tracks itself, with state under `perry/`

> Type: Process
> Status: Active
> Date: 2026-08-16
> Deciders: Perry maintainer

## Context

Perry had no state of its own. Design work on the skill was happening in
conversation and landing directly as edits, with no locked document naming the
problem or the decisions behind it.

Two things forced the question on 2026-08-16:

1. Two design documents were drafted (DESIGN-001, DESIGN-002) and needed a home.
2. Perry's own `design/` directory is the **design lane skill**
   (`design/SKILL.md`, `design/state/design_TEMPLATE.md`), not a folder of design
   documents — so Perry could not adopt itself at the project root without
   claiming its own source tree. `okr/` and `pmo/` are lane skills for the same
   reason.

This is exactly the collision DESIGN-002 describes. Perry is its own proof case.

## Decision

Perry tracks itself with `State root: perry`, recorded in `.perry/config.md`.
`OKR.md`, `BOARD.md`, `design/`, `journal/`, `decisions/` and the rest live under
`perry/`; `.perry/` stays at the project root because it holds the pointer.

Design documents are authored through the design lane and locked before
implementation opens. DESIGN-001 and DESIGN-002 were both locked 2026-08-16 with
all ten user-decision rows resolved, and handed off to a bootstrapped `BOARD.md`
as TASK-001…006 and TASK-010…014.

## Consequences

**Good.** The escape hatch DESIGN-002 argues for is now exercised by Perry
itself, so the mechanism has a live user. Design decisions on the skill acquire
an audit trail and a supersession chain instead of living in chat.

**Cost.** Writing `.perry/config.md` flips `is_adopted()` at
`bin/perry-lint:543`, which returns true on that file alone. Perry went from
"not a Perry project — lint judges nothing" to "adopted — lint requires the full
state tree" the moment the pointer was written, before any state existed. That
gap is recorded as a risk on the board and is a candidate finding for DESIGN-002:
**the state-root pointer and the adoption flag are the same switch**, and they
should probably not be.

**Not done.** No `OKR.md` and no `phase/`, so every board row is declared
unlinked rather than guessed into a KR. Goals for Perry itself are a separate
exercise.

## Alternatives considered

- **State root `.`** — rejected: `design/`, `okr/` and `pmo/` are source
  directories. Lint would report `design/SKILL.md` as a malformed design doc.
- **Keep design docs outside Perry's own tooling** (e.g. `docs/rfc/`) — rejected:
  it would leave the design lane with no dogfooding at all, and the collision
  problem DESIGN-002 exists to solve would have stayed theoretical.
- **Rename the lane directories** so `design/` is free — rejected as far more
  invasive than a state-root pointer, and it would break every existing install's
  symlink layout.

## References

- `perry/design/DESIGN-002-namespace-collision.md` — the design this instantiates
- `.perry/config.md` — the pointer, with its own rationale block
- `schema/README.md § Where the files are` — the two safety rules
- `bin/perry-lint:543` — `is_adopted()`, the switch this decision trips
