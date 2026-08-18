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
2. **An unquantified, unbounded unit is refused in Chinese**, the way a bare
   English unit already was: a Chinese time unit counts only when
   **quantified** (a digit, or one of 一二两三四五六七八九十百半几数每逐) or
   **bounded** (`季度末`, `月底`, `本周内` and the like).
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
