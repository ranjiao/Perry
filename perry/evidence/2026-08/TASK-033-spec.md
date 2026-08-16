# TASK-033 — Lane procedures call the tool

> Source: `perry/design/DESIGN-004-deterministic-writes.md` § 6 phase E, § 5.7
> Dispatch mode: manual
> Executor: manual — **the riskiest task in the plan.** A bad edit does not fail loudly; it leaves a lane describing a hand-edit while the tool exists, which is two written paths to one piece of state
> Estimated cycle: large
> Subjective verification: whether each migrated procedure still reads as one path rather than two
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

### Deliverable

`work/reference/subcommands.md` — `add-task`, `close-task`, `drop-task` and
`triage` step 0 stop describing hand-edits and call `perry-task`. `work/SKILL.md`
notes which writes are tool-mediated.

**One subcommand at a time, each with its own before/after fixture.** Not a
sweep: a half-migrated procedure is the failure mode this task creates.

### Verification — V4

Fresh-context reviewer, given the migrated procedures and DESIGN-004 § 5.7, asked
one question: **does any procedure still describe a hand-edit for state the tool
now writes?** That reviewer must not have seen the migration session — the same
rule that made the DESIGN-003 mode files fail four times when their author
reviewed them.

Plus mechanical: drift is 0 on a fixture driven entirely through the migrated
procedures.

### Dependencies

**TASK-031 — hard, not a sequencing preference.** § 5.7: drift detection must be
watching before the procedures change, or a migration is indistinguishable from
a regression. Both look like "rows appearing without events".

### Out of scope

- `goals` and `decide` lane procedures. Decision 3 scopes this release to task
  lifecycle, and those two lanes write `OKR.md` and `DECISIONS.md`.

## Notes

**Why this is the risky one, in the same shape as DESIGN-003's phase G.** It
rewrites procedures three lanes execute on every invocation. The failure is not
a crash — it is a lane that still tells the agent to hand-write a row while the
tool exists, producing drift against a procedure that instructed the agent to
create it. The drift number then reports a defect in the documentation as if it
were a defect in the agent's discipline, which is worse than no signal.
