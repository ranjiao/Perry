# TASK-217 — four pages disagree on whether the retro is written before or after score-phase

> Dispatch mode: manual
> Executor: manual (subjective — this is a decision about Perry's own pipeline, not an implementation; see § This is a decision)
> Estimated cycle: small
> Subjective verification: which ordering is correct — the one thing no scan can answer
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: unlinked
- **Source**: found during `/perry work end-phase-retro` for phase #002, 2026-08-28. Intake row 5, discharged the same day.

## The contradiction, as four quotations

| page | what it says | implied order |
|---|---|---|
| `goals/SKILL.md:154` | `evidence/<YYYY-MM>/retro.md` \| pmo \| "Read by OKR `score-phase` **after PMO writes it**; never written" | retro **before** score |
| `work/reference/subcommands.md:401` | "**Triggered when OKR `score-phase` is about to run** (or explicitly by the user)" | retro **before** score |
| `goals/reference/phases.md:229` (step 5) | "**Hand the retro summary to `work`; do not write it.** … Print the summary and the target path … and let `/perry work` write it." | retro **after** score |
| `goals/reference/phases.md:155, 162` | `plan-phase` **reads** `evidence/retro.md` and its `§ Health metrics` | only constrains retro **before** `plan-phase` |

The first two and the third are not reconcilable. Either `work` writes the
retro and `goals` then scores against it, or `goals` scores and hands `work` a
summary to write. Both are shipped, in the same skill, describing the same file.

## What actually happened on 2026-08-28

The live run is the tiebreaker for *behaviour*, not for *intent*:

- `goals score-phase` ran and wrote `phase/002-fields-are-typed.md § Retro —
  phase scored` — scores, what went well, lessons, carry-overs.
- It did **not** write `evidence/2026-08/retro.md`. That file did not exist
  until `end-phase-retro` was run later the same day.
- By then `plan-phase 003` had also run, so `phase/CURRENT` already pointed at
  #003 — and `end-phase-retro`'s own procedure says to read "journal entries
  since **the current phase** started", which by that point was a phase one day
  old. The retro had to be aimed at #002 by hand.

So the shipped behaviour follows `phases.md:229`, and the ordering in
`goals/SKILL.md:154` and `subcommands.md:401` is the one that did not happen.
That is evidence about which page is stale — it is **not** evidence about which
ordering is right.

## This is a decision, not a patch

Picking an order changes what each command may assume:

- **Retro before score** makes the retro the input to scoring: `score-phase`
  reads per-KR outcomes and evidence paths that `work` already established.
  Cost: `work` must mark each KR `achieved|partial|missed|dropped` before
  `goals` has computed a single score, so the two lanes each produce a per-KR
  verdict and they can disagree.
- **Retro after score** makes the retro the record of a decided phase, and the
  input to `plan-phase` only. Cost: `phases.md` step 5's hand-off writes a
  summary into a file `work` may also be writing — and `rollover` step 1 then
  guards on a file that neither command is clearly responsible for producing.

The 2026-08-28 run produced both artifacts with a deliberate split — `goals`
took scores and goal-level narrative, `work` took evidence links, board
metrics, health check and carry-overs — and **nothing in the design enforces
that split**. It held because it was done by hand.

**Therefore this row belongs to the `/perry decide close-phase` RFC**, not to a
doc sweep. It is that RFC's first question, and the second is whether the four
steps (`score-phase` → `end-phase-retro` → `rollover` → `plan-phase`) become
one router-level orchestrator on the `adopt` / `diagnose` precedent — a
sequence that spans two writers and therefore cannot live inside either lane.
The ordering and the merge are the same question: an orchestrator has to state
the order to run it.

## Deliverable

1. One ordering, decided and written in **one** page.
2. The other three pages cite it rather than restate it. Restating is how four
   copies drifted in the first place, and `reference/project-archetypes.md`
   already names the rule: *one document, one owner, one copy*.
3. `work/reference/subcommands.md:401`'s trigger sentence and
   `goals/SKILL.md:154`'s "after PMO writes it" clause both updated to the
   decided order — or deleted in favour of the citation.
4. The per-lane split of retro content (scores vs execution record) stated
   wherever the order is stated, so the 2026-08-28 hand-split becomes the
   design rather than a habit.

## Verification — V3

1. **Sweep, don't sample.** `grep -rn "retro\.md"` across the skill returned 23
   hits on 2026-08-28, of which 8 are the `okr-vN-retro.md` decoy (a different
   file, `OKR.md` overflow). Re-run it after the change and show that no two of
   the remaining hits describe opposite orders.
2. **Mutation.** Reintroduce one reversed sentence and show the check that
   enforces the ordering turns red. **If no such check can be written**, say so
   explicitly and fall back to deliverable 2 — the ordering stated once and
   cited everywhere else — because an uncheckable rule restated in four places
   is exactly the shape that produced this row.
3. `python3 -m unittest discover -s tests` green, including
   `tests/test_ownership.py` as widened by **TASK-216**.

## Out of scope

- The two ownership statements already corrected on 2026-08-28
  (`goals/SKILL.md:126`, `work/reference/subcommands.md:902`). Those were
  unambiguous — they contradicted their own files and the observed behaviour —
  and needed no decision.
- The guard that would have caught them: **TASK-216**.
