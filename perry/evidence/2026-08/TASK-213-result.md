# TASK-213 — result: four readers, one blank-cell rule

> Branch `coding/2026-08-29-overnight-batch`. Rung **V3**. Measured 2026-08-29.

## The defect

`bin/perry-task` carried

```python
ABSENT = {"", "—", "-", "–", "n/a", "na", "tbd", "无", "none"}
```

and three readers matched against it with `.lower() in ABSENT`:
`evidence_paths`, `evidence_relations`, and `parse_depends`.
`lib.is_blank_cell` is the one rule — it reads the declared spellings out of
`schema/state-schema.json § i18n.blank_cell` — and this set was the **fourth
copy** of it.

## What the copy missed, measured

| value | old `ABSENT` | `is_blank_cell` |
|---|---|---|
| `待定` | False | **True** |
| `不适用` | False | **True** |
| `暂无` | False | **True** |
| `**—**` | False | **True** |
| `` `n/a` `` | False | **True** |
| `" — "` | False | **True** |
| `—` `n/a` `na` `tbd` `无` `none` | True | True |
| `TASK-050` | False | False |

So on a Chinese board `Depends on: 待定` parsed as a **real dependency id**, and
`depends_on_resolved` reported a task waiting on a row that does not exist and
never will.

## Why the swap is safe — measured, not cited

TASK-163 established `is_blank_cell` is a strict **superset**. This row
re-measures it rather than citing it: **every value the old set called absent,
the one rule also calls absent.** Nothing any caller treated as empty became
present. `TestTheSupersetHolds` is that measurement, and it is the assertion
that would have to fail before any of the behaviour change could be a
regression. It carries a control — a rule that called everything blank would
pass the superset test and be useless.

## After

```
parse_depends('待定')             -> []
parse_depends('**—**')           -> []
parse_depends('TASK-050')        -> ['TASK-050']
parse_depends('TASK-050, 待定')   -> ['TASK-050']      # the mixed cell
parse_depends('TASK-050、TASK-051') -> ['TASK-050', 'TASK-051']
```

`evidence_paths` and `evidence_relations` read every placeholder as no
evidence, and a real path still reads.

## Two things this row got wrong first, and both are recorded because they were

**The first draft's mutation was green.** Reverting the three head-rule call
sites passed all ten tests: `parse_depends` reaches the same answer through its
token loop, so its head rule is redundant for these inputs, and
`evidence_paths` / `evidence_relations` were **never exercised at all**. A row
whose deliverable names four call sites needs a test that reaches four.
`TestTheEvidenceReadersToo` was written after that green, and reverting the
head rules now costs 5 failures.

**Retiring the name broke two importers, and the full suite caught it.**
`tests/test_evidence_relation.py:54` read `ABSENT = PT.ABSENT` under the comment
*"Read off the tool so this module cannot disagree with it"* — the right
instinct, pointed at the wrong rule — and `tests/test_task_writer.py:2192` did
the same inline. Both now go through `lib.is_blank_cell`, so they agree with the
tool **and** with a Chinese board. I should have swept for importers before
renaming; the category discipline this repository applies to source applies to
a constant's readers too.

`tests/test_conformance.py`'s `C.ABSENT` is a different module's constant
(`bin/perry-conform`) and is untouched.

## Mutation

| mutation | result |
|---|---|
| put a local set back in `parse_depends` | 1 failure |
| revert the three head-rule call sites | 5 failures |

Each restored byte-identical (`md5` checked).
