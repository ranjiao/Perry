# TASK-147 — one function knows a bullet from a table cell, and only its own tests say so

Dispatch mode: auto
Verification: V3
Re-verified: 2026-08-28 against `23ce1e0`

## The measurement

`bin/perry_store.py § describe_cell` (line 281) is where the two paths part.
Its own comment, at 266-269, states the invariant:

> `escape` is False for a slot that is not inside a markdown table — a
> `- PMO repo path: …` bullet in `.perry/config.md` carries no cell
> [escaping] it never had. **"Is this inside a table?" is the ONE question a
> table cell and a bullet differ on.**

That is a strong claim about a boundary, and **the references to
`describe_cell` are five, in two files**:

```
tests/test_md_store.py     4
tests/test_risks_store.py  1
```

So the separation is asserted by the tests of the function that implements it,
and by nothing else. If a caller passes the wrong `escape`, or a second code
path grows its own answer to "is this inside a table?", **nothing fails.**

## What to establish first, before building anything

**Enumerate every call site of `describe_cell` and every place that decides
`escape`.** The row's title says *"nothing outside `describe_cell`"*, and my
count above is a grep for the name. **Grep for the expression, not the name** —
six specs of mine in two days named a call site once where there were two or
three, and the last one (TASK-118) missed a second caller of `mint_risk_id` the
same way.

Then answer, with evidence:

1. **Who decides `escape`, and how many independent answers to "is this inside a
   table?" exist in the codebase?** If there is exactly one, the row is about
   pinning it. If there are two, the row is about the second one and is a bigger
   finding than its title.
2. **Is the boundary observable from outside?** A guard that can only be checked
   by calling the function it guards is worth less than one visible in a
   round trip — `.perry/config.md` bullets and a `BOARD.md` table both go through
   the store, so a test that writes both and reads both back may be available.

## The trap

`.perry/config.md` and `BOARD.md` on **this** project are the obvious corpus and
the wrong one: a test that asserts what Perry's own config currently contains is
a check reading the project around it as its expected value, which is the defect
class this repository pays for most. **Build the case.** `tests/fixtures/
witness-project/` (TASK-132) is read through the real `--root` seam, and
TASK-124 (merged tonight) is the worked example of asserting a **property**
rather than a capture-day census — read
`perry/evidence/2026-08/TASK-124-result.md`.

## What to build

A test that fails when the two paths stop being separated — specifically, when a
bullet gets cell escaping it never had, or a table cell loses escaping it needs.
It must fail for **that** reason and not because some file's current bytes
changed.

## Files in scope

`tests/`, `tests/fixtures/`, and `bin/perry_store.py` **only if** the
enumeration shows a second decider that must be unified. **Prefer reporting that
to fixing it** — say what you found and let me scope it.

## Out of scope

- `perry/` — read-only, including `.perry/config.md`.
- `viewer/tables.py § render_row` — cited by the comment, not the subject.
- `tests/test_conformance.py` and `tests/test_goals_writer.py` — other rows are
  in them tonight.

## Verification

1. **Mutation proof, and it is the whole row**: flip `escape` at each call site
   in turn and report how many assertions redden for each. **A call site whose
   flip reddens nothing is the finding.**
2. State the enumeration: every `describe_cell` call site, every decider of
   `escape`, and whether they agree.
3. `perry-lint`: **0 errors, 3 warnings, 173 records, 0 rows drifted** —
   unchanged.
4. Suite: **86 modules, one red** (`test_diagnose`, standing).

**Do not run `perry-conform declare`.** Do not `git push`. Do not touch `main`.
