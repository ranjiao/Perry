# verification/a-single-baseline-run-is-not-a-baseline — for a test that flips between runners, one measurement of "before" is a coin toss, and re-running it alone does not settle it

- Kind: knowledge
- Owner role: —
- Source: TASK-278 round 3 · evidence/2026-09/TASK-278-round3-result.md, 2026-09-07; corroborated by the TASK-276 and TASK-277 V4 rounds the same day
- Last verified: 2026-09-07
- Invalidated by: a runner that reports the same verdict for a module however it is invoked, or a baseline convention that records the base commit and the invocation together

The rule this refines is *re-run a red module alone before attributing it*. That
rule is right and it is **not sufficient**. A test can be red alone in **both**
trees and still flip green in a parallel run — so running it alone answers a
different question than the one the baseline was asked.

**The instance that nearly shipped a false claim.** `test_contract_key_parity`
was **green** in round 3's baseline and **red** at the end of its work. The
author re-ran it alone, as the rule says. It was **red alone in both trees**, so
the isolated run could not distinguish "my change did this" from "it was already
like that". Only a **full parallel run at the base commit** showed it red there
too. **The baseline's green was the flake** — not the final red — and a single
run had recorded the flake as the fact everything else was compared against.

**Three baselines of the same repository on one day, all correctly measured, all
different:**

| who | measured | why it differed |
|---|---|---|
| TASK-276's V4 | **1** red | measured at `1032e76` |
| TASK-277's V4 | **2** red | measured at `0724fa6` — a different base, said so |
| the PMO, later | **3** red | two rows filed with `--kr` had made a stale invariant fail |

None of them was wrong. The number is a property of *a commit and an
invocation*, and a baseline that records neither cannot be compared to anything.

## What to do instead

- Record the **base commit** and the **exact invocation** beside the number. A
  bare "1 red" is not a baseline.
- When a red appears at the end that was not there at the start, run the **full
  suite at the base**, not just the module alone. The isolated run is the second
  check, not the first.
- Treat a **green** in a baseline as needing the same suspicion as a red. This is
  the whole lesson: the round looked for an explanation of its new red and the
  defect was in the green it started from.
- A baseline measured in another tree, or before other work landed, is not
  yours. `TASK-381` — six of seven agents this week were handed a stale base —
  is the same failure one level up.
