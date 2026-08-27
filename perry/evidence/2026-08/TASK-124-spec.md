# TASK-124 — the conformance corpus reads a machine that is not this one

Dispatch mode: auto
Verification: V3
Re-verified: 2026-08-28 against `b7ca674`

## The measurement

```python
tests/test_conformance.py:440
REAL = Path(SNAPSHOT) if SNAPSHOT else Path.home() / "proj" / "gimegime-pmo"
```

A test corpus that resolves to **a directory outside the repository**, on the
author's machine, with an env-var escape hatch and **no committed substitute**.
On any other checkout the corpus is absent and whatever it proves is not proved.

**And it is four files, not one.** Before you scope this, that list is measured:

```
tests/live_state_expectations.py
tests/test_conformance.py
tests/test_goals_writer.py
tests/test_md_store.py
```

**Find out what each actually does with the outside path before treating them as
one problem.** `live_state_expectations.py` is TASK-121's guard against exactly
this class and may be reading outside the repo *deliberately, as its subject* —
if so that is not a defect and must not be "fixed". Say which of the four are
the same defect and which are not.

## The adjacent row that is already closed, and why this is not it

**TASK-111** — *"a test reads two files outside the repository, so it is
green…"* — is `done`. Read its record first
(`perry/evidence/2026-08/TASK-111-*.md`). If your change duplicates its
mechanism, use that mechanism instead of inventing a second one; **two solutions
to one question is the defect class this project pays for most.** If TASK-111's
mechanism does not fit, say why in one paragraph.

## The trap

A corpus committed into the repo is a **fixture**, and a fixture that records
what one real project happened to look like on capture day is the golden-file
failure `test_contract_invariance` spent TASK-145 escaping. `tests/fixtures/
witness-project/` (TASK-132) exists and is read through the real `--root` seam —
**that is the shape that worked here.** Whatever you commit, it must be
something whose correctness is a property of the checker, not a snapshot of a
project.

If you conclude that the honest answer is **"this test cannot be made portable
and should be deleted or explicitly skipped with its reason"**, that is an
acceptable outcome. Perry has deleted 3,977 lines this week for less. State the
argument.

## What to build

Whichever of the four are genuinely this defect: make them run and mean
something on a clean checkout with no `SNAPSHOT` set and no home directory
corpus. Preserve the `SNAPSHOT` escape hatch if it still earns its keep — say
whether it does.

## Files in scope

`tests/`, `tests/fixtures/`.

## Out of scope

- `perry/` — read-only.
- `bin/` — if a tool needs changing for a test to be portable, that is a finding
  to report, not a change to make.
- Building a second witness project. Extend the existing one or argue why it
  cannot serve.

## Verification

1. The suite passes with `SNAPSHOT` unset **and** with `$HOME` pointed at an
   empty directory. Show both runs.
2. Every test you changed still fails when the thing it checks is broken —
   **mutation proof with counts**, or it is a test that now passes by being
   vacuous, which is worse than one that skips.
3. State how many of the four files you touched and why the others were left.
4. Suite: **85 modules, 2557 tests, one red** (`test_diagnose`, standing).
   Anything else red is yours.

**Do not run `perry-conform declare`.** Do not `git push`. Do not touch `main`.
