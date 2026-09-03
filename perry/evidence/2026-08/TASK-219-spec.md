# TASK-219 — typed provenance from phase scores to retro

> Design: **DESIGN-012** § 5.4 and User Decision 4 (`design/DESIGN-012-close-phase.md`), locked 2026-08-28.
> Dispatch mode: manual
> Executor: manual — this changes Perry's own typed provenance contract
> Estimated cycle: small
> Subjective verification: whether the typed provenance is the complete input used by the retro agent
> Touches architecture: DESIGN-012 mechanism revised by ADR-007; outcome unchanged
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Rung**: V3
- **Dependencies**: —
- **KR linkage**: unlinked — see § Attribution

## Why

Decision 1 put the retro after scoring, so its inputs can cite authoritative
phase-score records. That invariant should be represented directly: each retro
generation records the typed KR/status references it consumed.

Python must not re-derive agreement by parsing the phase and retro Markdown.
The agent generates the retro from the typed payload; the tool verifies only
that the cited records exist and match the recorded ids and versions.

## Deliverable

A structured phase-score/retro provenance contract containing the phase id,
score-record version, and the complete typed list of KR ids and statuses passed
to the retro agent. The generated retro links to that provenance record but
remains an opaque natural-language artifact.

The verification path validates ids, versions and typed values only. It does
not scan headings, tables or status words in `retro.md` or a phase document.

## Bound

One typed phase-score/retro provenance record, the tool path that creates and
validates it, the agent input assembled from it, and their direct tests. No
other evidence-document or phase-close behavior is in this round.

## Verification — V3

1. Mutate a typed KR status or score-record version; the retro input/provenance
   must change or validation must fail.
2. Mutate only wording or layout in `retro.md`; typed validation must be
   unchanged, proving Python does not interpret the document.
3. Full suite green.

## Out of scope

- A `files[]` spec or cross-file prose check for `evidence/`.
- Any quality judgement about whether the retro explains the scores well; that
  remains agent/human review.

## Attribution

Serves `DESIGN-012` / `KR-O2.3`. Declared `unlinked` against phase #003 by
`goals`; see TASK-218 § Attribution for the same reasoning.
