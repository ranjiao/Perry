# TASK-163 — two readers disagree about whether a dash is a clock

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: small
> Localized and verified 2026-08-28.

## The measurement

```
'—'            lib.is_blank_cell = True     raw truthiness = True    ← disagree
''             lib.is_blank_cell = True     raw truthiness = False   ← agree
'2026-09-30'   lib.is_blank_cell = False    raw truthiness = True    ← agree
```

**They disagree on exactly one input: the declared blank marker.**

The two readers:

- **`bin/perry-state:424`** — `elif lib.is_blank_cell(str(sla or "")):` → the row
  goes to `sla_no_clock`. A dash reads as **no clock**.
- **`bin/perry-task:5519-5521`** —
  ```python
  conformance["rows_with_no_computable_age"] = [] if not conformance[
      "has_event_log"] else sorted(
      t["id"] for t in tasks.values()
      if t["open"] and not t["updated"]
      and not t["stage_since"] and not t["arrived"])
  ```
  `not t["arrived"]` is raw truthiness. A dash is truthy, so the row is **not**
  reported. A dash reads as **a clock**.

The row's own note, from 2026-08-21, says when it bites:

> **harmless on a tool-written board because the writer emits an empty string,
> live on a hand-edited one.**

And `bin/perry-task:364` already declares the vocabulary:

```python
ABSENT = {"", "—", "-", "–", "n/a", "na", "tbd", "无", "none"}
```

So the tool **has** a blank-cell rule, in two places, and this call site uses
neither.

## The deliverable, from the row

> the declared blank marker means the same thing to both clockless readers.
> After: a hand-written dash is clockless to both, an empty cell is clockless to
> both, and a real date is a clock to both.

## Before you change it, answer one question

**`ABSENT` (in `bin/perry-task`) and `lib.is_blank_cell` are two spellings of
one idea.** Read both. Say whether they agree on every input — `n/a`, `无`,
`tbd`, a lone `-`, whitespace — and if they do not, say which is right and
whether unifying them belongs in this row or a follow-up.

**Do not add a third.** Whatever this call site ends up using must be one of the
two that already exist, or the two must become one.

## Verification

1. The three cases above give the same verdict from both readers. Paste all six.
2. A hand-edited board with `Arrived: —` reports that row in
   `rows_with_no_computable_age`, and the same board reports it in
   `sla_no_clock`. **Build that fixture** — the tool-written board cannot show
   this, which is why it went unnoticed.
3. A row with a real date is in **neither**.
4. The 1.9 `semantics` behaviour is unchanged: the array is still empty when
   `has_event_log` is false.
5. Mutation: restoring raw truthiness reddens a test that names the dash.
6. `perry-lint --root .` — 0 errors, and `rows_with_no_computable_age` on this
   repository is unchanged (the writer emits `""`, so it should be).

## Out of scope

- `bin/perry-state`'s side is already correct — do not change it.
- Do not touch `schema/state-schema.json` or `perry/`. `git diff -- perry/` must
  end empty.
- If `ABSENT` and `is_blank_cell` genuinely disagree, **report it**; only unify
  them if that is the smaller change than leaving two.

## Ground rules

- Branch `coding/task-163-a-dash-is-not-a-clock`, commit there, **no PR, no
  push**.
- **Commit as soon as you have something coherent, and keep committing.**
- `PYTHONNOUSERSITE=1 /usr/bin/python3` explicitly.
- `tests/parallel -j 4`. Verify yours is the only one with a pattern that
  **cannot match your own argv**:
  `ps -Ao pid,command | grep "python3 tests/paralle[l]"`. Scratch files under a
  path containing your branch name. **Never `git checkout` while a suite runs.**
- Expected baseline: **83 modules · 2471 tests · 2 red** —
  `test_contract_invariance` and `test_diagnose`. **Neither is yours**; another
  agent owns the first.
