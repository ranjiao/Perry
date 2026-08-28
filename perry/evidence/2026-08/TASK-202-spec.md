# TASK-202 — the hook side of the union has no not-extractable check, and it is the half every project has

Dispatch mode: auto
Verification: V3
Re-verified: 2026-08-28 against `afd3e56`

## The asymmetry

TASK-201 fixed `escalate_unextractable` so it asks *"did this line produce a
fragment"* instead of *"does this line have a backtick"*. **That check exists
only on a `RoleCard`:**

```
viewer/parsers.py:3332   escalate_unextractable   — a RoleCard field
viewer/parsers.py:3385   set in read_role_cards
bin/perry-lint:1687      for bullet in card.escalate_unextractable
```

`hook_escalation_lines` (`:3157`) reads `.perry/hook.md § High-stakes
operations` through the **same** `escalation_fragments`, and **nothing reports a
hook bullet that contributes nothing.** Role cards are optional — DESIGN-006
Goal 7 says a project with none is never asked for one. **The hook is the half
every project has.**

## The motivating case, measured on a real project

`~/proj/gimegime-pmo`, which handles real money:

```
5 bullets → 3 fragments · 3 contribute ZERO, unwarned

  silent: Any change to risk-gate parameters (kill switch behavior,
          max_daily_loss, max_position, stale_or…)
  silent: Adding a new paid data source or LLM provider
  silent: Increasing the monthly cost ceiling above the current cap
  works:  phase=paper · phase=live · .env
```

**Three of five high-stakes rules are invisible to the gate.** And note
`max_position`: TASK-200 found the *role card* catching exactly that fragment on
a cross-line seam. **The card was compensating for a hook that could not see its
own rule** — which is why this is P1 and not tidying.

## The trap, and it is the same one TASK-156 hit

**Perry's own hook is clean**: 8 bullets → 35 fragments, **0 contributing
nothing**. So a test asserting *"this repository's hook has no dead bullets"* is
green now, green with your check deleted, and worthless — the defect class this
project has paid for most.

**Build the case.** `tests/fixtures/` and temp projects through the real
`--root` seam. TASK-201's 17 new tests are the model; its glossary test is
written per *declared language* rather than for one language, for the same
reason.

## What to decide and state

1. **Where the finding surfaces.** A role card's goes through
   `perry-lint`'s card loop. A hook has no card and no loop. Say where yours
   lands and why a reader will meet it.
2. **Severity.** `perry-lint` currently reports Perry's three `NS-01` as
   warnings and nothing here as anything. A hook bullet that names a rule the
   gate cannot enforce is arguably worse than a role card's, because there is no
   card to compensate. Argue it.
3. **Whether the two checks become one function.** They ask the identical
   question of identically-shaped input. `escalation_fragments`' docstring
   already says the two sides must extract *the same way* or "a term a role
   declares would mean something other than the same term in the hook". **The
   same argument applies to reporting.**
4. **What a project with no `.perry/hook.md` gets.** Nothing, silently — the
   TASK-117 inversion is one check over, and TASK-156 hit it too. Absence is not
   failure.

## Files in scope

`viewer/parsers.py`, `bin/perry-lint`, `tests/`, `tests/fixtures/`,
`schema/roles-list-contract.md` **only if** a payload key changes meaning — say
so and version it.

## Out of scope

- `bin/perry-state:1954` — flat-union scan, correct by accident and
  load-bearing. Not yours.
- `.perry/hook.md` on this project or any other. **`~/proj/gimegime-pmo` is
  read-only**; it is evidence, not a target.
- The three findings TASK-201 left named: `green_lit` de-duplication, headings
  with a numbering prefix, and `下单` firing on `系统永不下单`.

## Verification

1. A fixture hook with a bullet that produces no fragment is reported.
   **Before/after verdicts on the same fixture** — "it now reports" is worthless
   without "it was silent before".
2. A project with **no** hook file gets **zero** findings, not N.
3. Perry's own `perry-lint` output is **unchanged**: 0 errors, 3 warnings,
   197 records 0 drifted, risks store 4 records 0 drifted. If it moves, you have
   found something — report it rather than adjusting to fit.
4. **Mutation with counts.**
5. Suite: **89 modules, one red** (`test_diagnose`).

**Do not run `perry-conform declare`.** Do not `git push`. Do not touch `main`.
