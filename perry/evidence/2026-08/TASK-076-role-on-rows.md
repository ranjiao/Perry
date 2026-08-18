# TASK-076 — DESIGN-006 phase E: `role` on rows, and the asymmetry that is Goal 7

> Source: `perry/design/DESIGN-006-roles-and-knowledge.md § 5.2`, decision #4,
> § 6.1 phase E. Rung: **V3**. Every claim below is a run or a mutation.

## What shipped

- `Role` as an **optional** board column, declared in
  `schema/state-schema.json` beside `Track`, `Verification` and `Depends on` —
  the mechanism that already existed for exactly this.
- `role` on every task in `perry-task/list`, **contract 1.7 → 1.8**, always
  present and `""` when absent.
- `perry-task add --role <name>`, and `check_role`.

## The refusal is conditioned on the project, never on the value

Decision #4 says *required when roles declared*. The asymmetry is the design:

| project | `add` with no `--role` | `add --role x` |
|---|---|---|
| no `.perry/roles/*.md` | **accepted**, no column, no mention of roles anywhere | accepted and filed |
| has role cards | **refused**, and the refusal lists the roles that exist | refused unless `x` has a card |

**Goal 7 is the reason this is not simply a required column.** A project that
never hears of roles must behave exactly as it does today — no new column, no
flag to learn, and **no refusal naming a concept it has not adopted**. A test
asserts the last of those specifically, because an error message is the most
likely place for a new subsystem to leak into a project that never asked for it.

`test_a_role_passed_anyway_is_filed_not_refused` covers the other direction: the
flag is inert rather than an error on a roleless project, so one script works on
both kinds.

## Mutations

5 written, 5 red. **M1 is the one that matters**: making the role
unconditionally required — the obvious way to write this feature — turns three
Goal 7 tests red, including the one asserting no refusal mentions roles.

## What is not done

- **The triage stale-knowledge line** is part of phase E's payload and is not
  written. It belongs in the `work` lane's triage procedure, and phase B was
  live in that area while this landed; splitting one section between two agents
  is how a procedure ends up saying two things. Left for whoever lands next,
  named here rather than quietly dropped.
- The close gate does not yet read `Accepted by` / `Default rung` from the card.
  That is phase D's half — *"the stricter of mode-rung and role-rung wins"* —
  and phase D is in flight.
