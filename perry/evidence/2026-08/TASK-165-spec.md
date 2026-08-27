# TASK-165 spec — the report exemption covers `dangling` and not the queue register

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: small
> Verified live on this repository 2026-08-27.

## The measurement

```
$ perry-diagnose --root . --json → user_load
open_decisions_by_register : {"queue": 1, "design": 0}
open_decision_samples      : ["USER-900"]
dangling                   : ["TASK-007", "TASK-9999", "USER-900"]
dangling_in_reports        : ["DESIGN-900", "REL-00", "ZZZ-404", "ZZZ-405"]

$ perry-task list --all --json → asks
{"items": [], "open": 0}
```

`USER-900` is a **fixture id**. It appears in `tests/test_diagnose.py` and
`tests/test_task_writer.py` — both of which `is_illustrative` correctly reports
as illustrative — and in exactly one file that is not:

```
perry/evidence/2026-08/TASK-153-result.md:50
    from `[]` to `["USER-900"]`. A private copy would keep the old answer.
```

That line **quotes the test's own output, verbatim**, while describing the fix
TASK-153 shipped. `perry/evidence/` is not illustrative, so the line became
`USER-900`'s **definition point**, and `perry-diagnose` counts it as a pending
queue row on this project.

`test_diagnose.test_the_queue_register_reconciles_with_the_queue_on_this_repository`
is red because of it: `1 != 0`, *"diagnose and perry-task disagree about how
many queue rows are waiting on the user."*

## The shape of the defect

`user_load`'s two halves **disagree about the same id**:

| where | does it see `USER-900`? |
|---|---|
| `dangling_in_reports` — the exemption | **yes**, it covers ids quoted in reports |
| `open_decisions_by_register.queue` | **no exemption reaches here** |

So the mechanism that exists to say *"this id is quoted, not referenced"* was
built for one array and not the other. This row is that gap.

**It is not a TASK-153 regression.** TASK-153's fix works: it filters the queue
register on `is_illustrative(defined)`, and `tests/test_diagnose.py` **is**
illustrative. The evidence record is not, and nothing filters on "quoted".

## What must not be the fix

**Do not reword `TASK-153-result.md`.** TASK-142's own `means` text warns
against rewording to please a checker; the line is verbatim test output, and
falsifying it to make a check pass is worse than the red. The same applies to
`TASK-160-result.md` and `TASK-162-result.md`, which narrate `TASK-9999` for the
same reason.

**Do not add `USER-900` to an exemption list.** An id-specific carve-out is the
thing this project keeps refusing; the next quoted id would need another one.

**Do not delete the fixture's `USER-900` row.** Other tests read it.

## What the fix has to decide

`dangling_in_reports` already knows how to tell *quoted* from *referenced*.
**Read how it decides, and say whether the queue register can use the same
predicate or needs a different one** — they are close and may not be identical:

- `dangling_in_reports` asks *"is this id a reference that resolves nowhere, or a
  quotation?"*
- the queue register asks *"is this id a row of this project's queue?"*

If the same predicate serves both, **reuse it** — one rule with two
implementations is the defect this repository has paid for most. If they
genuinely differ, say precisely how.

## Verification

1. `test_the_queue_register_reconciles_with_the_queue_on_this_repository`
   passes **on this repository**, still comparing this repository's two tools.
2. `TASK-153-result.md:50` is **byte-identical**. Prove it.
3. A **real** pending queue row is still counted. Build a fixture whose
   `## User Input Queue` has a genuine pending row *and* a project note quoting
   another id, and show the count is 1, naming the right one.
4. The predicate appears **once**. Prove it with a search.
5. Mutation: reverting your change reddens item 1 and nothing else.
6. `perry-lint --root .` — 0 errors.

## Out of scope

- **`TASK-007` and `TASK-9999`** stay in `dangling`. `TASK-007` comes from a
  verbatim quote of fixture output in TASK-142's result, and `TASK-9999` from
  two records narrating the incident in which it was minted. If your change
  happens to clear them too, **say so and show why that is correct** rather than
  treating it as a bonus.
- Do not touch `schema/state-schema.json`.
- `perry/` is read-only to you. `git diff -- perry/` must end empty.

## Ground rules

- Branch `coding/task-165-quoted-ids-in-the-queue`, commit there, **no PR, no
  push**.
- **Commit as soon as you have something coherent, and keep committing.**
- `PYTHONNOUSERSITE=1 /usr/bin/python3` explicitly. Perry is stdlib-only as of
  tonight (TASK-178 deleted the viewer), and that flag is what proves it — bare
  `/usr/bin/python3` picks up a user site-packages carrying jinja2.
- `tests/parallel -j 4`. Verify yours is the only one with a pattern that
  **cannot match your own argv** — `ps -Ao pid,command | grep "python3 tests/paralle[l]"`.
- Expected baseline: **80 modules · 2369 tests · 2 red** —
  `test_contract_invariance` (a union-typed key, unrelated) and `test_diagnose`
  (TWO failures: the queue reconcile, which is yours, and
  `['TASK-007','TASK-9999','USER-900']`, which is not).
- Another agent is working in `bin/perry-task`. You should need `bin/perry-diagnose`
  and `bin/perry-explain` only.
