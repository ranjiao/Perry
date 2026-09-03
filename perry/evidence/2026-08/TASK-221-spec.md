# TASK-221 — a phase close that stopped halfway is visible at the next snapshot

> Design: **DESIGN-012** § 5.3 and User Decision 3 (`design/DESIGN-012-close-phase.md`), locked 2026-08-28.
> Dispatch mode: manual
> Executor: manual — this changes Perry's own typed phase-close state
> Estimated cycle: medium
> Subjective verification: (none)
> Touches architecture: DESIGN-012 detection mechanism revised by ADR-007; recovery outcome unchanged
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Rung**: V3
- **Dependencies**: TASK-217
- **KR linkage**: unlinked — see TASK-218 § Attribution

## Why

Phase #002 was left halfway through close with no structured record of the
completed stages. Inferring that state from a phase document's `Status:` line
would make natural-language Markdown a machine protocol.

The close path must instead emit typed stage events or update a typed close
record. Deterministic artifact existence and `phase/CURRENT` checks may confirm
the record, but Python never parses phase or retro prose to choose a stage.

## Deliverable

`perry-state --section interrupted` gains a half-closed-phase row resolved from
a typed phase-close record/event sequence with these states: `not_started`,
`scored`, `retro_written`, `current_cleared`, and `complete`.

The record carries phase id, completed stage, timestamps and artifact refs.
Artifact existence and the exact `phase/CURRENT` pointer are deterministic
cross-checks. The retro body and phase document are opaque. The snapshot
reports the typed resume stage and artifact refs for the consuming agent.

This preserves DESIGN-012's four-stage outcome while revising its detection
mechanism to comply with ADR-007. It adds no natural-language parser and no
resumable prose dossier.

## Bound

The typed phase-close record/event writer, the five-state resume resolver, the
`perry-state --section interrupted` serializer, and their direct tests. The
last element is the `complete` state fixture and its deterministic artifact and
`phase/CURRENT` cross-checks.

## Verification — V3

1. Construct each typed state and assert the resolved resume stage.
2. Delete or mismatch a referenced artifact or `phase/CURRENT`; the snapshot
   must fail closed instead of guessing from document prose.
3. Change `Status:` or retro wording without changing typed state; the resolved
   stage must remain unchanged.
4. Full suite green.

## Out of scope

- Parsing phase status, retro headings or retro content.
- A resumable natural-language dossier.
