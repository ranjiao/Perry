# TASK-019 — `modes/pipeline.md`

> Source: `perry/design/DESIGN-003-work-modes.md` § 6 phase D (locked 2026-08-16)
> Dispatch mode: auto
> Executor: codex (self-contained authoring against a fully specified table)
> Estimated cycle: medium
> Subjective verification: the stage vocabulary's default set — a reviewer judgment, not a test
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

### Deliverable

`modes/pipeline.md` implementing the `pipeline` column of DESIGN-003 §5.1:

- **Spine**: commitments (party · deliverable · due) → current cycle.
- **Horizon closes** when the cycle's items shipped or were dropped.
- **Calendar is binding** — due dates are the spine, not advisory. This is the
  explicit inversion of `okr/SKILL.md § Why phases, not months`, which stays
  correct for `project` mode and wrong here (DESIGN-003 §1.4 B1).
- **Item states**: a declared stage vocabulary, default
  `brief → draft → review → approved → published`, overridable per pack.
- **WIP limit per stage**, replacing P0/P1/P2 as the throttle.
- **Triage asks**: which item is aging in which stage.
- **Default rung**: V5 — a shipped deliverable is outward-facing by definition.

### Verification — V4

Fresh-context reviewer, given only DESIGN-003 §5.1's `pipeline` row and this
file, judges whether the file implements the row. The reviewer **must not** have
seen the implementation session — the fresh-context rule from
`reference/project-archetypes.md § 3.B`.

### Dependencies

TASK-018 (the mode-loading mechanism, and the no-op must be proven first).

### Out of scope

- Any domain pack's stage names — legal matter stages, content calendar stages.
  Packs supply those (TASK-024/025); this file supplies the default and the
  contract for overriding it.
- Confidentiality / client separation. DESIGN-003 §8 flags this as unresolved
  and says pipeline mode should not be recommended for legal work until it is.
  **Note that limitation in the file itself.**

## Notes

The signature failure to guard against, from §5.1: everything sits in `review`
forever. The stage-aging triage question is the organ that catches it, so it is
not optional prose.
