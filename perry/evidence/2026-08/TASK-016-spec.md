# TASK-016 — `perry-lint --verification` (advisory)

> Source: `perry/design/DESIGN-003-work-modes.md` § 6 phase B (locked 2026-08-16)
> Dispatch mode: auto
> Executor: codex (self-contained lint mode over a declared schema, no MCP dependency)
> Estimated cycle: medium
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

### Deliverable

A `--verification` mode on `bin/perry-lint` that reports, for every `done` row
in `BOARD.md` and every spec file:

- a missing `verification:` rung;
- a rung the cited evidence cannot satisfy (a `V3` claim with no command and no
  output; a `V4` claim citing no rubric file; a `V5` claim with no signer name
  and date);
- a rung below the mode's declared default, or below **V5** where the task is
  marked outward-facing / irreversible — the consequence rule of DESIGN-003
  §5.3, which overrides the mode default in every mode.

**Advisory only.** Exit code stays 0 in all cases. Decision 4 deferred the hard
gate by one release so no existing `done` row is retroactively invalidated.

### Verification — V3

A fixture under `tests/fixtures/` carrying six `done` rows: three conforming
(one V2, one V3, one V5) and three non-conforming (missing rung; V4 with no
rubric; V1 on a row flagged outward-facing). Expected output pinned in the test.
`--verification` must report exactly the three non-conforming rows and exit 0.

### Dependencies

TASK-015 (the `verification:` field must exist in the schema first).

### Out of scope

- **Hard gating.** That is the next release, per decision 4. Do not add a
  non-zero exit or a refusal path in `close-task`.
- Rung capture at close time — TASK-017.
- Authoring rubrics. DESIGN-003 §8 leaves who writes them open.

## Notes

V0 ("asserted") exists in the enum so the linter has a name for what it is
rejecting. Nothing may ever be written with `verification: V0`; if the lint sees
one, that is a finding, not a valid low rung.
