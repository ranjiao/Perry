# TASK-221 — a phase close that stopped halfway is visible at the next snapshot

> Design: **DESIGN-012** § 5.3 and User Decision 3 (`design/DESIGN-012-close-phase.md`), locked 2026-08-28.
>
> Dispatch mode: manual
> Executor: manual — **a gate result, and a false positive worth recording.** `.perry/hook.md § High-stakes operations` matches the fragment `claims` in this row's deliverable, where the sentence is *"**NO** new `claims[]` path"* — the opposite of the risk the gate guards. The scanner is boundary-matched but polarity-blind, the same defect the journal recorded on 2026-08-28 for `下单` firing on `系统永不下单`. Rewording to pass is what the hook explicitly refuses to reward, so the wording stands and this is dispatched by hand.
> Estimated cycle: medium
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Rung**: V3
- **Dependencies**: TASK-217 — the resume table cannot tell stage 2 from stage 3 until `phases.md` step 7 stops clearing `phase/CURRENT` (invariant I2)
- **KR linkage**: unlinked — see TASK-218 § Attribution

## Why

Phase #002 was left `scored`, with no `evidence/retro.md`, and a `rollover`
that never ran. **Nothing anywhere recorded that.** The next session's only
signal was a phase file that said `scored` and a `CURRENT` already pointing at
its successor.

Decision 3 chose to detect this from state rather than mint a file, because a
close is four mechanical stages whose progress is already legible from what
they leave behind — and `.perry/hook.md` lists changes to the claim surface as
a high-stakes operation, so not needing one is worth the constraint.

## Deliverable

`perry-state --section interrupted` gains a half-closed-phase row, resolved by
`DESIGN-012 § 5.3`'s table:

| phase `Status:` | `evidence/<YYYY-MM>/retro.md` | `phase/CURRENT` | resume at |
|---|---|---|---|
| `active` | — | the closing phase | stage 1 — nothing ran |
| `scored` | absent | the closing phase | stage 2 |
| `scored` | present | the closing phase | stage 3 |
| `scored` | present | empty / `(none)` | stage 4 |
| `scored` | present | a *newer* phase | complete |

Surfaced at the next `/perry` snapshot, through the gate that already renders
one row per pipeline someone walked away from. **No new `claims[]` path and no
dossier.**

## Verification — V3

1. The five rows become a test fixture: construct each state, assert the
   resolved stage.
2. **The mutation is I2 landing by halves.** If `score-phase` still clears
   `phase/CURRENT`, rows 3 and 4 collide — after stage 1 the state would read
   *scored / retro absent / CURRENT empty*, which the table cannot place. The
   fixture must fail when that happens, because that is precisely when the
   recovery path would otherwise be silently wrong.
3. Full suite green.

## Out of scope

- A resumable dossier or any new claimed path. Decision 3 refused both.
