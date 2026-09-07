# TASK-395 — how this was found, and the two measurements behind it

> Found 2026-09-08 while removing a dead no-op in
> `tests/test_md_store.py`'s `test_render_write_puts_a_drifted_file_back_in_line`.

## The dead line, and what git says about it

The test's setup carried:

```python
before.replace("| KR-O1.1 |", "| KR-O1.1 |", 1)
      .replace("3 of 3 modes live", "SEVEN of 3 modes live")
```

The first call is an identity — needle and replacement are the same string.

**It was born that way.** `git log -L 1225,1227:tests/test_md_store.py` shows
exactly two commits touch it: `96822a4e` (2026-08-20), the commit that **created**
the file, where it is already identical; and `50305274`, ADR-017 step 3, which
renamed both halves to `| O1-KR1 |` — **making it match the file again without
making it do anything.** It never held a differing second argument, so the
hypothesis that it "lost its second argument" is not what happened.

## Measurement 1 — restoring it makes the test fail

Writing the mutation it would have been, in a `git archive` copy:

```python
before.replace("| O1-KR1 |", "| O1-KR9 |", 1)
```

```
FAILED (failures=1)
AssertionError: '…O1-KR9 | Non-`project` modes running on live t…'
                 != '…O1-KR1 | Non-`project` modes running on live t…'
```

**`O1-KR9` is still in the file after `render --write`.** So the behaviour the
line would assert **does not exist**, and it could not have passed on the day it
was written either. That is why it was deleted rather than restored.

## The defect this row is about

`render` matches each row to its store record **by id**. A hand-edited id
therefore matches no record, and `render` **passes the line through verbatim** —
which is the documented fallback `TestTheByteGateCanFail` relies on, and is
correct in general.

But `perry-okr diff` **does** report the drift. So:

| | id drifted | prose cell drifted |
|---|---|---|
| `diff` reports it | **yes** | yes |
| `render --write` repairs it | **no** | yes |

**Two tools disagree about whether the file can be put back in line, and nothing
states the limit.** A caller who reads `diff`'s report and runs `render --write`
gets an exit 0 and a file still carrying the drift.

## Measurement 2 — the surviving assertion still measures

The test keeps one drift, in a cell whose row still resolves. To show that is not
also decoration, `bin/perry_md_store.py:936` — `render`'s first body line — was
replaced with `return text, {}`, so the renderer returns its input unchanged:

```
FAILED (failures=1)
```

**Red.** The remaining assertion genuinely measures that `render --write` repairs
the drift.

**A correction worth recording**: the first attempt at that mutation came back
**green**, and it was **not** a finding — the insertion had landed inside the
docstring of a *different function* nineteen lines below, and never executed.
Checking that a mutation reached the code is what separates "the guard does not
work" from "the harness does not work"; here it was the second.

## What was not touched

`tests/fixtures/live-state/md_store.before.py:406` carries the same dead line and
is a **sha256-pinned frozen artifact** — `tests/test_live_state_expectations.py`
pins its digest. It is a record of what the file was, not a copy to keep in sync,
and it was left byte-identical.
