# TASK-153 spec v2 — `perry-diagnose` counts test fixtures as the project's own state

> **The design decision this row was blocked on has been made by the user on
> 2026-08-21: option A — `perry-diagnose` skips test fixtures.**
> Do not re-open it. Do not implement option B. Do not add a flag.

## The measurement

```
tests/test_diagnose.py
DecisionsAreCountedPerRecordNotPerMention
  .test_the_queue_register_reconciles_with_the_queue_on_this_repository
AssertionError: 1 != 0 : diagnose and perry-task disagree about how many
                         queue rows are waiting on the user
```

```
open_decisions_by_register : {"queue": 1, "design": 0}
sample                     : tests/fixtures/sample-project/BOARD.md:36 — USER-014
perry-task list --all      : asks.open = 0
```

`perry-diagnose` scans the **whole repository**, fixtures included, and counts a
fixture's `USER-014` as one of Perry's own open decisions. `perry-task` reads
only `perry/BOARD.md`, where every `USER-` row is answered, and reports 0.

**The numbers move.** The spec's first draft recorded `2 != 1`; it is `1 != 0`
today because two real queue rows were answered on 2026-08-21. Same defect,
different denominator — **do not treat a changed number as a different
failure.** Re-measure before you start and put your own reading in the report.

The fixture was always counted. It only became visible once every one of
Perry's own queue rows was answered: **this defect is only observable after the
real work is finished.**

## The decision, and the part still left to you

The user chose: **a fixture is not project state, and `perry-diagnose` must not
count it.**

What is still yours to get right is the objection the row was opened with:

> `perry-diagnose` runs on **any folder**, including ones that have never heard
> of Perry, and a hard-coded `tests/fixtures/` is a guess about somebody else's
> layout.

**A literal `tests/fixtures/` string is not an acceptable implementation.**

### Read this first, and answer it explicitly

`bin/perry-explain § is_illustrative` (line 105) already faces this question and
already answers it **by name, not by path**:

```python
ILLUSTRATIVE_PARTS = {
    "templates", "template", "examples", "example", "fixtures", "fixture",
    "samples", "sample", "tests", "test", "reference", "references",
    "scaffold", "boilerplate",
}
```

Your report must state, in as many words, **whether that is the same question**.
The two are close and not obviously identical:

- `is_illustrative` asks *"is an ID in this file an example rather than a
  reference?"*
- this row asks *"is this file part of the project's state?"*

If they are the same question, **reuse the function — do not write a second
spelling of it.** One rule with two implementations is the defect this
repository has paid for more times than any other; `tests/test_one_header_rule.py`
and `tests/test_risks_store.py` both exist because of it. Import it, or move it
to `bin/lib/` and have both call it, and assert `is` identity rather than
agreement over a corpus.

If they genuinely differ, **say precisely how**, and make the difference the
entire content of the new predicate — not a fresh list of directory names that
happens to overlap.

## Three prohibitions

1. **No record may be edited to make the checker pass.** `git diff -- perry/`
   must end empty. Answering a queue row, or editing a fixture, to move a
   number is out of bounds.
2. **The fixture stays where it is and keeps its `USER-014` row.** It is a
   test's furniture and other tests read it. If you find yourself changing
   `tests/fixtures/sample-project/BOARD.md`, stop.
3. **No exemption list, no flag, no `--include-fixtures`.** This repository has
   a rule that a second way to answer one question is the defect.

## Verification

1. The reconciliation test passes **on this repository**, and it still compares
   *this* repository's two tools — the property it was written for. Do not
   repoint it at a fixture project; that is option B, which was not chosen.
2. **`perry-diagnose` still works on a foreign project.** Build a fixture whose
   real state lives in a directory the new predicate might swallow, and show it
   is still counted. This is the check that catches the failure mode the
   objection names, and it must be new.
3. **The mutation**: reverting your change makes the reconciliation test red
   again, and nothing else.
4. Whatever the predicate is, there is **one** of it. Prove it with a search.
5. `perry-lint --root .` — 0 errors.

## Out of scope

- **The other `test_diagnose` failure is not yours.**
  `test_perry_itself_passes_its_own_id_checks` reports
  `['TASK-007', 'TASK-9999']` and belongs to TASK-165 — two evidence records
  narrate, in prose, the incident in which those ids were minted, which makes
  the narrating record their definition point. **Do not fix it, do not add
  either id to an exemption list, and do not edit those records.**
- `test_contract_invariance` is red for an unrelated reason, diagnosed in
  `evidence/2026-08/contract-invariance-union-types.md`. Not yours.
- Do not touch `schema/state-schema.json`.

## Ground rules

- Branch `coding/task-153-diagnose-skips-fixtures`, commit there, **no PR, no
  push**. The PMO merges locally.
- Use `/usr/bin/python3` explicitly, and **measure your own baseline** before
  touching anything. The red set on this repository differs by interpreter, so
  a count taken elsewhere does not transfer.
- `/usr/bin/python3 tests/parallel -j 4`. Verify yours is the only
  `tests/parallel` on the machine before trusting a reading — two concurrent
  runs pollute each other.
- Expected baseline: **80 modules · 2331 tests · 2 red** —
  `test_contract_invariance` (1 failure) and `test_diagnose` (2 failures, one
  of which is yours). If you see a different set, **report the difference
  rather than absorbing it.**
