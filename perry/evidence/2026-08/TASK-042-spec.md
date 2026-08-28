# TASK-042 — acceptance criteria

**Written before the round, by the author.** `work/reference/review.md § 1`: a
reviewer with no written criteria invents its own bar, so the round's verdict
reports what that agent happened to value. This file is the only authority for
PASS/FAIL.

## What the work claims

`OKR.md § Commitments` is owned by the `goals` lane, and a commitment's
`By when` cell must name a time a reader can act on. `bin/perry-goals`'s
`CLOCK_RE` is the gate. Round 2 FAILed it because the rule was **enforced in
English and not in Chinese**: the character class `[天日周月年]` matched any
stray `日` or `年`, so `日后再说`, `改天` and `年后再说` were accepted and
written into `OKR.md` as live deadlines, while the English `when we get to it`
was correctly refused.

## What must be true when this is done

1. **The two languages give the same verdict for the same meaning.** For every
   pair of phrases that mean the same thing in English and Chinese, `commit`
   accepts both or refuses both. This is the property; a list of phrases is
   not.
2. **An unquantified, unbounded unit is refused — in BOTH languages.**

   > **Corrected 2026-08-18 after round 3.** This criterion previously read
   > "refused in Chinese, *the way a bare English unit already was*". **A bare
   > English unit was never refused.** `bin/perry-goals` requires only
   > wordhood in English, so `--by week` writes a live commitment row while
   > `--by 周` is refused — round 2 reversed the asymmetry instead of removing
   > it, and this file inherited the false premise from the source comment that
   > claims the two halves impose the same standard. The reviewer had to catch
   > the spec as well as the code, which is what a criteria file is supposed to
   > make unnecessary.
   >
   > **Criteria 1 and 2 cannot both hold unless the ENGLISH half grows the
   > quantity-or-bound requirement.** Loosening the Chinese half satisfies
   > criterion 1 and brings every round-2 phrase straight back.

   A time unit counts only when **quantified** (a digit, or a quantity word)
   or **bounded** (`季度末`, `月底`, `本周内`, `end of Q3`, `by month end`).
   `week`, `月`, `year` and `周` alone are all refused.
3. **`每周一次` and `逐月` still pass.** A recurrence is a schedule, and an
   existing test asserts it. If a fix breaks that test, the test is right and
   the fix is wrong.
4. **`3d` and `2w` pass.** They are the shorthand Perry's own `## Tracks`
   examples use, and a rule that refuses them makes a legitimate SLA
   unwritable.
5. **A refusal names the cell and writes nothing.** No partial `OKR.md`, no
   journal line, no event.
6. **Nothing outside `goals` is written.** `OKR.md` and `phase/` only — the
   hand-off contract.

## How to check it

Drive `bin/perry-goals commit` on a **copy** of a project, both languages.
Mutate: relax the quantifier requirement and confirm the language-parity test
goes red. A green mutation is a finding either way.

## Out of scope

The English half's word boundary (landed under TASK-021), and any commitment
column other than `By when`.
