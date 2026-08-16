# TASK-026 — Rewrite `SKILL.md § The hand-off contract`

> Source: `perry/design/DESIGN-003-work-modes.md` § 6 phase G, § 5.9, § 7 (locked 2026-08-16)
> Dispatch mode: manual
> Executor: manual — **not dispatchable.** `perry-lint` cannot detect a bad edit to this section; a wrong contract shows up later as silent cross-lane writes, which is the one failure Perry has no other guard against
> Estimated cycle: medium
> Subjective verification: the contract's correctness — mitigated by the ownership-refusal fixture below, but the sign-off is a human judgment
> Touches architecture: (none — but this section *is* Perry's architecture in the sense that matters)
> Deployed: no

## Schema

- **Owner**: User + Agent — V5 verification requires a named human signing what
  they checked; an owner of `Coding Agent` on a task that cannot close without
  the user would be a lie the board tells at every standup
- **Priority**: P0
- **Attribution**: unlinked

### Deliverable

`SKILL.md § The hand-off contract` rewritten for the post-DESIGN-003 lane cut:

| Lane | Owns |
|---|---|
| `goals` (was `okr`) | `OKR.md` (incl. the new `## Commitments`), `phase/` |
| `work` (was `pmo`) | `BOARD.md` (incl. `## Intake`), `journal/`, `PROJECT_STATE.md`, `evidence/`, `weekly/`, `handoff/` |
| `decide` (was `design`) | `design/<DESIGN-ID>-<slug>.md`, **`DECISIONS.md`, `decisions/`** |

The invariant does not change and must be restated as-is: **each lane reads the
others' files freely; no lane writes outside its own.** This is a file-ownership
contract, not a skill-registration one.

**This task lands first and alone**, as a single revertible commit. No aliases,
no renames elsewhere, no docs — those are TASK-027 and TASK-028.

### Verification — V5

Two parts, both required:

1. **Fixture**: each lane attempts a write outside its declared ownership and
   must refuse. Minimum three cases — `goals` writing `BOARD.md`, `work`
   writing `DECISIONS.md` (the newly moved file, i.e. the case this change
   creates), `decide` writing `journal/`.
2. **Fresh-context reviewer** reads the new contract against DESIGN-003 §5.9's
   blast-radius table and confirms every listed surface is accounted for.
3. **Human sign-off** recorded with name, date, and *what was checked* — not
   "reviewed".

### Dependencies

TASK-015.

### Out of scope

- Lane aliases (`/perry okr` → `goals`) — TASK-027.
- Renaming the lane directories and their SKILL.md files — TASK-027.
- `README.md` / `README_cn.md` — TASK-028.

## Notes

DESIGN-003 §7 records this as the riskiest row in the plan, and §5.9 explains
why the plan originally hid that: phase G reads like rename-plus-docs, and the
contract rewrite was buried inside it. The section being edited is the one
`SKILL.md` itself calls *"the most important rule"* — the thing that survived
the collapse from three registered skills to one entrance, precisely because it
was never about skill registration.

If this task cannot be completed confidently, the correct escalation is to
revisit DESIGN-003 §4 decisions 5 and 6, not to ship a hedged contract.
