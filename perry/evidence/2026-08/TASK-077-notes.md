# TASK-077 — notes moved off the board, 2026-08-28

> Moved here by `/perry work triage` on 2026-08-28. The row's `Next action` cell
> held this verbatim; the cell is a **next step**, and this is a **record**. It
> is preserved before the cell is rewritten, because the last time
> `next_action_cites_closed` was treated as prose hygiene — 2026-08-20, on
> TASK-037 and TASK-045 — the rewrite deleted the only copy.
>
> Companion to `evidence/2026-08/TASK-077-context.md`, which stays the row's
> `Evidence` path.

## The cell, verbatim

> DECIDED 2026-08-28 by the user: draft the card first, do not run it yet. Two
> corrections to this row's own record: (1) the `Kind: source-of-truth` card
> type F asks for is ALREADY BUILT — `state-schema.json:2112`,
> `knowledge-list-contract.md:71`, `perry-knowledge --kind` — decision #6
> confirmed 2026-08-17 and it landed with phase A; (2) `gimegime-pmo` has NOT
> been migrated to the store (no `tasks.jsonl`; `BOARD.md` / `OKR.md` /
> `DECISIONS.md` at the project root), so running there today exercises the
> legacy markdown shape, which is TASK-097's subject. What actually blocks F is
> that no non-software role card has ever been written — all three shipped
> cards are software-shaped and the only pack is `software-ops`. Card first via
> TASK-200; the run and the V5 signature stay with the user.

## What this is worth keeping for

Three things, none of which is a next step:

1. **A user decision, dated.** Draft the card first; do not run it yet. The V5
   signature stays with the user.
2. **Two corrections to the row's own record**, each with a citation. A row
   whose stated blocker was already built would otherwise be re-investigated by
   whoever picks it up.
3. **The real blocker, named**: no non-software role card has ever been
   written. Every shipped card is software-shaped and `software-ops` is the
   only pack. That is what DESIGN-006 phase F is actually waiting on.

## Board state at the time of the move

`not_started` · P1 · `startable: true` · `blocked_by: []`. All four declared
dependencies — TASK-073, TASK-075, TASK-076, TASK-200 — are `done`. The row is
**not blocked**; it is unstarted, which is a different thing and the reason
this triage did not change its `Status`.
