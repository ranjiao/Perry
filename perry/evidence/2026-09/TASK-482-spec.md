# TASK-482 — R-midweek gets a deterministic fact source

Date: 2026-09-22. Owner: Coding Agent. Priority: P2. Required verification: V4.
KR: P004-O1-KR1. Design: `perry/design/DESIGN-020-guided-planning.md § 5.10`
(stage 4, `R-midweek`), follow-up to TASK-479.
> Touches architecture: schema/state-schema.json (consented, USER-999), bin/perry-state next facts, the midweek-check procedure.
> Dispatch mode: auto
> Executor: claude-subagent
> Subjective verification: independent review against the written bounded criteria
> Deployed: no

Authorization: USER-999 (2026-09-22, in chat): the schema may change so that
`R-midweek` has a fact source.

## Problem

TASK-479 declared `R-midweek` (Wednesday, no mid-week check yet → `/perry work
midweek-check`). Its fact `today.journal_has_midweek` is always `unknown`,
because `midweek-check` (`work/reference/subcommands.md § midweek-check`) writes
prose into today's journal and nothing typed marks that it ran. The rule
therefore never fires.

## Deliverable

1. **A typed record that `midweek-check` leaves.** Choose one design and
   justify it in one paragraph against the other two:
   - (a) a schema-declared journal heading;
   - (b) an occurrence written by an existing tool path (e.g. the cadence
     register's `perry-task cadence-done`, or another existing writer);
   - (c) a typed record or event written by a small new writer verb.
   Prefer the option with the smallest schema edit that is written by a tool
   rather than by hand (ADR-007: the store is truth). A heading an agent types
   by hand is the weakest option.
2. **The schema edit it needs**, in `schema/state-schema.json`, kept to the
   minimum: the new kind, heading or field, and nothing else. USER-999 is the
   consent. State in the RESULT exactly what changed in the schema and why.
3. **The fact** in `bin/perry-state`. Rename or replace
   `today.journal_has_midweek` with a name that says what it now reads, e.g.
   `week.midweek_checked`. It is a typed boolean for the current ISO week, read
   through the one reader (NN-1). It is `unknown` only when the store itself is
   unreadable. Update `reference/next-rules.json`'s `R-midweek` predicate, the
   `reference/next.md` entry and `schema/next-contract.md` (fact name; a minor
   bump to `perry-next/1.2` if the fact list changes).
4. **The procedure**: `work/reference/subcommands.md § midweek-check` ends by
   writing that record through the tool, with no hand edit.
5. **Fixtures** in `tests/test_next_section.py`:
   - a Wednesday fixture with no record this week → `R-midweek` fires (as
     primary or alternate, whichever the order gives; assert its presence and
     position);
   - the same fixture with the record → it does not fire;
   - a record from last week does not count;
   - replace the existing `test_midweek_is_declared_with_its_fact_unknown` with
     tests of the new behaviour.

## Acceptance criteria

1. On a Wednesday with no mid-week record for the ISO week, `R-midweek` is
   returned; with the record, it is not. A previous week's record does not
   suppress it.
2. Running the documented `midweek-check` write on a fixture makes the fact
   true, through the tool alone.
3. Deleting `R-midweek` from a copy of the rule file reddens its fixture.
   Reverting the fact to always-unknown reddens the firing fixture.
4. `perry-lint --root .` on this repository stays at 0 errors, and existing
   stores stay valid under the edited schema.
5. `perry-state --section next` on this repository runs without `rule_errors`.
   Report its block before and after.
6. The coverage guard in `tests/test_next_closing.py` stays green. If a new
   writer verb is added, classify it there.
7. Affected tier green.

## Files in scope

`schema/state-schema.json`; `bin/perry-state`; `viewer/parsers.py` (only if a
reader is needed); the chosen writer (`bin/perry-task`, or none);
`reference/next-rules.json`; `reference/next.md`; `schema/next-contract.md`;
`work/reference/subcommands.md` (the midweek-check paragraph only);
`tests/test_next_section.py`; `tests/test_next_closing.py`; one test module for a
new writer verb, if there is one.

## Bound

One record kind or heading, one fact, one rule predicate. Net Python/test
physical lines ≤ +150. Lane and reference pages within their existing byte
budgets. The router `SKILL.md` is not edited.

## Verification

Isolated fixtures, candidate PERRY_HOME, PERRY_PROJECT unset, fresh TMPDIR
under the scratch derivation. `bash tests/run --tier affected --base <pinned
base>`. Reverting proofs for criterion 3, with `__pycache__` purged.
`git diff --check`. Record the exact commit and line delta.

## Out of scope

DESIGN-020 batches 2 and 3; `week.planned` (TASK-444); phase duration (UD 13);
rewriting existing journals; live PMO state; release allocation (the
integrator allocates the patch); publication; main integration.
