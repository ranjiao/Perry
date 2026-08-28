# TASK-024 — Extract `packs/software-ops/`

> Source: `perry/design/DESIGN-003-work-modes.md` § 6 phase F (locked 2026-08-16)
> Dispatch mode: manual
> Executor: manual (this task is a design experiment as much as a refactor — its failure mode is a finding the user must see, not an error to retry)
> Estimated cycle: large
> Subjective verification: whether the extraction was "clean" — bounded by the mechanical checks below so it is not left to judgment alone
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

### Deliverable

Move out of `pmo/reference/` into a bundled `packs/software-ops/`:

- `architecture.md`
- `runbooks.md`
- `incidents.md`
- `git-boundaries.md`

Plus the subcommands they back (`architecture init|review|diff`,
`architecture-audit`, `runbook-check`, `incident`, `health-check`), which become
pack-supplied rather than core-lane.

`packs/software-ops/` still ships with Perry by default — decision 7 chose
bundled over a separate repo, so nothing about the out-of-the-box experience for
existing users changes.

### Verification — V4 (mechanical floor + reviewer)

After the move, all four must hold:

1. `pmo/reference/` contains none of the four files.
2. `python3 bin/perry-lint --root .` green.
3. `grep -rn "pmo/reference/\(architecture\|runbooks\|incidents\|git-boundaries\)"`
   returns zero hits outside `packs/software-ops/`.
4. A fixture project with the pack **disabled** still runs a full standup, and
   one with it enabled reaches the four subcommands.

**The stop condition, and it is the point of the task:** if the four files need
content edits beyond path references to work as a pack, do **not** force it.
Record `packs are wrong` as a `## Changes` entry on DESIGN-003 and stop. §7
names this as the deliberate test — *"Phase F is deliberately the test. If it
fights, drop packs and keep §5.7's glossary, which stands alone."*

### Dependencies

TASK-018.

### Out of scope

- Any third-party pack.
- The pack **loader** and the display glossary — TASK-025. This task proves the
  material can be separated; the next one makes separation a mechanism.

## Notes

This is the fix for DESIGN-003 §1.4 B8: four software-operations files sitting
in the core lane, carried by every user in every shape. It is also the honest
test of the pack abstraction, and those two things are the same work — which is
why it is one task and not two.
