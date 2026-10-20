# Proposed kernel revision: monotonic prefix floors

Status: independently reviewed candidate; actual user approval pending.
Candidate: `32bcf99c0832676c7c5ae125621cf88107c70dec`.
Source: `/Users/bytedance/.codex/worktrees/kernel-prefix-floor/Perry`.

Perry has 22 design documents numbered through DESIGN-023, with DESIGN-018
absent. The activated store already holds work items/events. Existing item
creation cannot skip 018, and import correctly refuses a nonempty store. The
migration therefore stops before writing rather than reusing a historical ID,
creating a placeholder record or editing SQLite.

The candidate adds optional `ceilings` input to existing `template apply`.
For example, after importing actual DESIGN-017, reserving `{"DESIGN":18}` makes
the next real design DESIGN-019. Prefixes must be declared by the submitted
compatible template; floors are strict bounded integers and can only rise.
Equal/lower values do nothing. Same-version identical-template reservations
write only existing ceiling events. Invalid inputs, incompatible templates and
dry runs leave the store unchanged. Eight concepts, twelve command groups and
four guard kinds remain unchanged. The additive surface version becomes 1.1.

Verification:

- Complete isolated kernel suite: 286 tests, 285 passed and one APFS platform skip.
- Independent bounded review: PASS; eleven focused/boundary tests passed.
- Actual-source copied migration: Perry appends all 204 F items while preserving
  its original 602 items/1200 events exactly; SkyTonight appends 60 items while
  preserving 34 items/68 events exactly. Both rehearsals are idempotent.
- No live store, primary source, architecture approval, release or V5 sign-off
  was changed or granted by these rehearsals.

Independent review:
`/tmp/perry-scratch/Perry/TASK-492-prefix-floor-independent-review-n_14wyqk.md`.
Receipts: `/tmp/perry-scratch/Perry/remaining-cutover-psi33eiz/`, under
`Perry-floor-rehearsal/receipt.json` and `SkyTonight-floor-rehearsal/receipt.json`.
Architecture delivery has explicit pending target-change attention, with the
real pre-edit baseline retained at `TASK-492-prefix-floor-architecture/`.

Approval records a bounded revision to DESIGN-023 permitting this input and
its surface 1.1 contract. It does not approve dropped H checks, user V5,
publication, or any unrelated kernel growth. DESIGN-023 §7 explicitly says:
“A kernel change needs the user's approval in a revision, never inside a task.”
