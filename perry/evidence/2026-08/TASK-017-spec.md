# TASK-017 — Rung capture at `close-task` + distribution in `perry-state`

> Source: `perry/design/DESIGN-003-work-modes.md` § 6 phase B (locked 2026-08-16)
> Dispatch mode: auto
> Executor: codex (mechanical extension of two existing scripts + one subcommand)
> Estimated cycle: small
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

### Deliverable

1. `close-task <id>` asks for the verification rung before writing the
   status-change line. The mode's default rung is pre-selected, so the common
   case costs the user zero input (DESIGN-003 §7's mitigation against the
   ladder becoming bureaucracy).
2. `bin/perry-state` reports the rung distribution across closures in the
   current phase / period.
3. The standup renders one line from it, e.g.
   `🔬 Verification : V1=6 · V3=2 · V5=1 (9 closures this phase)`.

Consistent with `pmo/SKILL.md § Mandatory first move` step 2: the number comes
from the payload, never from reading the board and counting by eye.

### Verification — V3

A fixture project with a known set of closed rows at known rungs renders the
exact expected standup line. Test pins the string.

### Dependencies

TASK-016 (the rung must be lintable before it is prompted for, or `close-task`
will happily record rungs the linter then rejects).

### Out of scope

- Refusing a close on a low rung — still advisory this release.
- Back-filling rungs onto historical `done` rows. They stay unrated; the
  distribution line reports them as `unrated: N` rather than guessing.

## Notes

The distribution line is the early-warning signal for DESIGN-003 §7's stated
risk: "rung distribution collapses to V1". If it does, the ladder is being
routed around and the design needs revisiting rather than enforcing harder.
