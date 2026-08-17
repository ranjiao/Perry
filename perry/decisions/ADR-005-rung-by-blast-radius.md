# ADR-005 — V4 is for what runs on someone else's project

> Status: active
> Type: Process
> Date: 2026-08-17
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

Perry's own tasks have been closing at **V4** — a fresh-context reviewer
scoring against written acceptance criteria — more or less by default.
`work_modes.modes.project.default_rung` is already `V3`; the escalation was
habit, not policy.

V4 is the most expensive rung that is not a human. It costs a rubric written
before the work, a reviewer that has not seen the reasoning, and usually a
second round because the first one fails. That cost is worth paying where a
defect reaches a stranger's files. It is not obviously worth paying for a
refusal message or a documentation pointer inside Perry's own repo.

It has also been earning its keep, which is why this is a narrowing rather than
a removal. The 2026-08-17 round found, at V4 and at no lower rung: a writer
that silently deletes live risks, an intake queue that can never be drained on
a real project, dead commands stamped into every user's `BOARD.md`, and two
guards written that same week that could not fail on the defects they named.

## Options

**A · Keep everything at V4.** Correct and slow. Rejected because the rung is
being spent uniformly on work whose failure modes are not uniform.

**B · Drop to V3 across the board.** Rejected: every finding listed above was
found by a V4 and by nothing else. V3 would have shipped all of them.

**C · Rung by blast radius.** **Chosen.**

## Chosen

**The rung follows who is hurt when it is wrong**, not who wrote it.

| Rung | For |
|---|---|
| **V5** | Anything matching `.perry/hook.md § High-stakes operations` — unchanged, and it already overrides everything below |
| **V4** | Code or documents that **run on a project Perry did not create**: the migration pipeline, every writer's refusal path, the tolerant readers, and every published contract (`perry-task/list`, `perry-goals/list`, `perry-decide/list`) |
| **V3** | Everything internal to this repo: Perry's own board hygiene, its evidence files, refactors with no behaviour change, and tests |

Two rules that do not move:

- **Consequence still beats category.** A V3-by-this-table task that turns out
  to touch a published contract is V4, and `perry-lint --verification` reports
  the mismatch either way.
- **V3 is a reproducible run, not an assertion.** Dropping a rung is not
  permission to stop verifying. Mutation discipline — revert the fix, confirm
  the test goes red — applies at every rung, and its absence is what made three
  of the last round's twelve claimed mutations fail to reproduce.

## Consequences

- Most of DESIGN-005's remaining work is V4 by this table, not less: contracts
  and writers are exactly the outward-facing category. The saving lands on the
  internal work around them.
- Under ADR-004 the migration pipeline becomes the highest-value V4 surface in
  the project, since it is the only thing that touches a stranger's files at
  all.
- A rung recorded on a row is now a claim about blast radius, so it should be
  possible to disagree with it in review. That is deliberate.

## What would reopen this

- A V3-closed internal task ships a defect that a V4 would have caught. One
  instance is an anecdote; a second is a mispriced trade.
