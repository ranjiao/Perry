# TASK-018 — `modes/project.md`, the proven no-op

> Source: `perry/design/DESIGN-003-work-modes.md` § 6 phase C (locked 2026-08-16)
> Dispatch mode: manual
> Executor: manual (this is the task that protects Perry's existing users; a "close enough" extraction is exactly the failure it exists to prevent)
> Estimated cycle: medium
> Subjective verification: (none — the check is a byte diff)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P0 — the don't-break-what-works gate for the whole design
- **Attribution**: unlinked

### Deliverable

1. `modes/project.md` containing today's Perry behavior **extracted verbatim**:
   the OKR → phase → week spine, the P0/P1/P2 priority model, the phase-closes-
   on-KRs rule, and today's triage questions.
2. The router (`SKILL.md`) loads one mode file per declared track, after the
   config read.
3. Absent a `## Tracks` section in `.perry/config.md`, one implicit track named
   `main`, mode `project` — DESIGN-003 goal 7.

### Verification — V3

**Every existing fixture produces a byte-identical dashboard before and after.**
Capture `bin/perry-state --dashboard` output for each fixture on the current
`main`, apply the change, re-run, `diff` must be empty. A non-empty diff means
the extraction rewrote behavior instead of moving it, and the task is not done.

Second check: `bin/perry-lint --root .` green on all fixtures, unedited.

### Dependencies

TASK-015 (`mode` enum and `tracks[]` must exist to be read).

### Out of scope

- Any of the other three modes. `pipeline` is TASK-019, `queue` TASK-020,
  `inquiry` TASK-022.
- Improving today's project-mode behavior. Improvements are a separate task
  after the no-op is proven; mixing them makes the diff check worthless.

## Notes

DESIGN-003 §7 names the risk this task answers: *"generalizing weakens the
software path Perry is good at"*. The mitigation is that this phase is
deliberately a **proven** no-op, not an asserted one — hence the byte diff
rather than a reviewer's judgment.

Context-budget check belongs here too: measure tier-0 line count after this
lands. DESIGN-003 §7 requires it before phase E, and this is the first point
where the router carries a mode table at all.
