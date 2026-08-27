# TASK-158 — id families are hardcoded, so a project with its own gets noise

Dispatch mode: auto
Verification: V3
Re-verified: 2026-08-28 against `017132d`

## Your first deliverable is to find the check. I did not.

The row says *"the citation families are hardcoded in the tool, so a project with
its own id family gets noise on every legitimate citation."* I looked and found
**candidates, not the location**, and I am telling you that rather than handing
you a guess to work from:

```
bin/perry-diagnose:1639   re.match(r"^(DESIGN|ADR|TASK|USER)-\d", stem)   ← a FILENAME check
bin/perry-diagnose:436    re.search(r"\bUSER-\d+\b", line)
bin/perry-diagnose:1918   r"^\s*[-*>]?\s*Id\s*:\s*SRC-\d+\b"
bin/perry-explain:58      r"\b((?:P-O\d+\.\d+)|(?:[A-Z][A-Z0-9]{1,9}-\d{1,4}))\b"   ← generic
bin/perry-lint:124        KR_ID_RE = r"\bP-O\d+\.\d+\b"
bin/perry-lint:1419  ·  bin/perry-migrate:847      SRC_RE
bin/perry-task:1544  ·  :4079  ·  bin/perry-decide:82
```

**`bin/perry-explain:58` is the interesting one**: it is already *generic* —
any `[A-Z][A-Z0-9]{1,9}-\d{1,4}`. So at least one tool solved this. Find out
whether that generality is right, and whether the tool the row means should
adopt it.

**Start from the symptom, not the grep.** Construct a project whose ids are a
family Perry has never heard of — `FOO-001`, or better something that is
plausible for a real user — put a legitimate citation of one in the places a
citation lives, and **run the tools until something reports noise.** That
identifies the check the row is about. Report what you ran and what fired.

If nothing fires, **say so**. "The row's premise does not reproduce on today's
code" is a real and valuable outcome — two rows tonight closed that way, and
one closed because another repository had already fixed it.

## The related decision, already made, that constrains you

`schema/task-list-contract.md:315` records a deliberate choice for
`next_action_cites_closed`:

> **Only ids in this payload are resolved**: `DESIGN-`, `ADR-` and `USER-` ids
> appear in these cells constantly and are not checked, because reporting
> "cites nothing closed" while skipping three id families would claim more than
> the data supports.

**That is a considered position, not the defect.** If your change would make
that check resolve more families, it is a contract change and needs its own
argument — do not do it as a side effect.

## What good looks like

A project declaring its own id family gets the same treatment Perry's own
families get, **without** the tool being taught that family by name. Where the
list must stay closed, it should be **read from one place** rather than repeated
— the same unification `bin/lib/` exists for, and the same one TASK-163 and
TASK-118 did for other duplicated predicates.

## Files in scope

Whichever tool your investigation identifies, plus `bin/lib/` and `tests/`.
**Name the file in your commit message** — I could not.

## Out of scope

- `bin/perry-goals` — another row is in it tonight.
- `schema/task-list-contract.md § next_action_cites_closed` — see above.
- `perry/` — read-only.

## Verification

1. **The reproduction first**: the noise, on a constructed project, before your
   change. If you cannot produce it, stop and report that.
2. The same project is quiet after, and Perry's own families still behave
   identically.
3. **Mutation proof with counts.**
4. `perry-lint`: **0 errors, 3 warnings, 173 records, 0 rows drifted**.
5. Suite: **86 modules, one red** (`test_diagnose`, standing).

**Do not run `perry-conform declare`.** Do not `git push`. Do not touch `main`.
