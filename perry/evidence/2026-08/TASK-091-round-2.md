# TASK-091 — round 2: the asymmetry had moved, not gone

**Design**: ADR-007 decision 3. **Criteria**: `perry/evidence/2026-08/TASK-042-spec.md`.
**Round 1 verdict**: FAIL — `perry/evidence/2026-08/TASK-091-v4-review.md`.
**Rung**: V4.

Round 1 confirmed all six spec criteria with its own material — 21 self-built
EN/ZH pairs, a 20-value refusal boundary, migration lossless and idempotent in
both languages, refusal writing zero files by sha256, 12 mutations with 11 red.
Then it went and read the commit's *claim* and grepped for the property instead
of trusting the diff, and the claim was false.

## The FAIL

`bin/perry-goals` carried, above its anchored date pattern, the words **"the one
spelling of 'is this cell a date'"**. `bin/perry-diagnose` carried a second one
that `search`ed:

```python
DATEISH = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
```

So `2026-09-30 or so` was **refused by the writer and counted as a dated
promise by the reader** — one cell, two answers, from the pair of tools whose
whole job is to agree about it. A uniqueness claim a `grep` disproves is worse
than no claim: it stops the next reader from grepping.

**And the rename broke Chinese registers outright.** `diagnose`'s two counters
did not move together — `dated` read `due` OR `by when`, `prose` read only
`by when` — while the schema i18n key had just gone `By when` → `Due`. So `截止`
resolved to `due`, carried prose, failed the date test, and **was counted by
neither**. Round 1 measured it across the commit on one register: a board
scoring `queue` with one standing commitment before scored **no mode and no
evidence** after, while the English board was unchanged.

## The fix

`lib.is_iso_date` is the only predicate. `bin/perry-goals`, `bin/perry-diagnose`
and the three tools that each spelled out `fullmatch(r"\d{4}-\d{2}-\d{2}")` for
a knowledge card's `Last verified` all import it — one rule, one
implementation, on the field where three copies had grown.

Both `diagnose` counters read the same cells, so they **partition** the
commitments. The test asserts the SUM, not each counter, because a per-counter
test passes on the day a third counter swallows a case.

Measured after, on four registers:

| Header / cell | dated | prose |
|---|---|---|
| `By when` / `month by month` | 0 | 1 |
| `截止` / `逐月` | 0 | 1 |
| `Due` / `2026-09-30` | 1 | 0 |
| `Due` / `2026-09-30 or so` | 0 | 1 |

Rows two and four are the two halves of the FAIL. Three mutations red.

## Both secondary findings, and one fix closed both

Round 1 listed two things it did not call the FAIL:

1. a **ZH pre-split register is invisible** to `perry-lint` and `perry-migrate`,
   because `截止` is one word for both columns so there is no missing header to
   find;
2. **`perry-lint` has no value-level check on `Due` at all** — a hand-edited
   `| … | 下周期 | active |` lints clean, so *"nothing else is accepted"* held
   for the writer only.

The schema says of that column: *"`Due` is TYPED — an ISO date (2026-09-30) or
a declared SLA token (3d, 2w) — and nothing else is accepted"*. A typed column
with a validated writer and an unvalidated file is a column whose type is a
**convention**, which is the thing ADR-007 rule 1 exists to stop.

`typed_columns` is now declared in the schema beside `enum_columns` and checked
the same way. **The value check closes (1) as a side effect**, and that is the
ADR-007 argument itself: nothing can be inferred from a header that is one word
for two columns, but the *value* still says which column it belongs in.

`warn`, not `error` — a pre-split register is a state real projects pass
through and `perry-goals commit --migrate` is the fix; an `error` would block
the migration under enforce mode.

## Two things the sweep found that reading would not have

The writer/reader parity test sweeps sixteen values through **both** paths and
asserts they agree. Two disagreed:

* **`2026-13-45` and `2026-02-30`** matched the shape and are not days. The
  writer had always parsed as well as matched; the reader had not. Three
  callers then do `date.fromisoformat()` on the strength of that answer, so a
  shape-only `True` handed each of them a `ValueError` on a hand-typed card.
  `is_iso_date` checks the calendar now.
* My first version of the finding's message named the accepted vocabulary **in
  `bin/perry-lint`**, and `test_work_modes § test_the_linter_does_not_carry_
  its_own_copy_of_the_list` went red. The guard was right: the words are the
  declaration's and only the predicate is Python's. `typed_cell_kinds` in the
  schema carries the prose and the linter reads it.

## What round 2 asks the next reviewer to check

1. **Is `warn` right for `bad-typed-cell`?** The argument is the migration
   path. The counter-argument is that `bad-enum` on the same table is `error`,
   and a reader cannot sort a column either way. Break it.
2. **Does the parity sweep actually sweep?** Sixteen values is a list. Find one
   the writer and the file check still disagree on.
3. **The three `Last verified` sites now strip decoration** where they did not
   before, and one of them (`perry-state`) feeds a staleness age. Confirm no
   card changed its reported age for the wrong reason.
4. **`re.search` for a date inside text is untouched** — four sites, named in
   the test docstring as out of scope. Decide whether that scoping is honest or
   whether the same defect is sitting there.
