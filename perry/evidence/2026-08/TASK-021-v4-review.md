# TASK-021 — V4 review (`BOARD.md § Cadence` gets a writer)

> Reviewer: fresh-context agent, 2026-08-17. Rubric: `TASK-021-spec.md`.
> Baseline: 600 tests OK, `perry-lint` clean. Verified against a **copy** of
> `~/proj/gimegime-pmo` (original untouched) and a zh fixture copy.
>
> **Verdict: FAIL.** The register genuinely has a writer, `Next due` is
> genuinely computed, the arithmetic has one implementation with two callers,
> and both "surface by age" procedures now read the computed field. That is most
> of the task, and it works on a real project's board. But three of the five
> rubric sections have a defect, and two are in exactly the places the rubric
> flagged as most likely missed.
>
> Filed by the agent that received the report, at the reviewer's precision.

## MAJOR — 1. `parse_due` takes the first date *anywhere* in the cell, so a row reading `n/a` is reported overdue

`viewer/parsers.py:747-772` (`parse_due`), consumed at `bin/perry-state:406`.

The cell is free prose by design, and the regex is
`re.search(r"\d{4}-\d{2}-\d{2}", raw)` over the **whole** cell — including file
paths and parentheticals that describe *past* runs. The bare-date rule also
unconditionally beats the ISO-week rule, even when the bare date appears after
the week token.

Established by an end-to-end run (`perry-state --section cadence`):

| `Next due` cell | frequency | reported |
|---|---|---|
| `n/a （见 evidence/2026-08/2026-08-03-retro.md）` | monthly | `due: 2026-08-03`, **14 days overdue** |
| `2026-W40（上次 2026-01-05 完成）` | quarterly | `due: 2026-01-05`, **224 days overdue** |

Dashboard line from the same run:
`🔁 Cadence : 2 registered · 2 overdue (oldest: CAD-002 @ 224d)`.

This is not hypothetical prose. It is the convention the live register uses —
`**2026-08-31**（7 月版 ✅ 8/3 补作 → evidence/2026-08/retro-2026-07.md；6 月版跳过）`.
That cell survives only because its bare date happens to come first and the
parenthetical uses the short form `8/3`. Writing the same note with a full date,
or citing a dated evidence filename, flips it.

Rubric item 4 replaces the agent's eyeball with a computed field, and item 3's
argument — echoed verbatim in `parse_frequency`'s docstring,
`viewer/parsers.py:687-690` — is that *a confidently wrong value is worse than
an admitted unreadable one*. `parse_frequency` honours that rule; `parse_due`
does not. No test covers a cell where a date appears in a path or after an ISO
week (`tests/test_cadence.py:175-190` tests only cells where the intended date
is first).

## MAJOR — 2. The overdue sort — rubric item 4's central claim — has no test that can fail on it

`bin/perry-state:435` (`overdue.sort(key=lambda r: -r["days_overdue"])`),
guarded by `tests/test_cadence.py:422-432`.

Established by reverting: deleting the sort line and running the **full suite**
gives `Ran 600 tests ... OK`. The guarding test adds `old` (37 days) before
`newer` (12 days), so board order already equals sorted order and the assertion
is satisfied by its own setup. The code itself is correct — adding the rows in
the opposite order in a temp project produced `[('CAD-002', 30), ('CAD-001', 5)]`
— it is simply unverified.

This matters beyond coverage: `work/reference/subcommands.md:95` now instructs
the agent in bold that the list "**is already sorted oldest-first**" and to stop
scanning the table. That promise is the only thing standing between the
procedure and the eyeball it replaced, and nothing enforces it. It also
contradicts `TASK-021-recurrence-register.md:83-87` ("Twenty behaviours verified
by reverting them … Every one went red") and `tests/test_cadence.py:10-13`.

For contrast, four neighbouring guards *do* fail on what they name — verified
individually: `Cadence` in `NON_TASK_SECTIONS`; the cadence events staying out
of `TASK_EVENTS`; `days > 0` vs `>= 0`; the `unreadable_frequency` / `undated`
appends.

## MAJOR — 3. `done` on a Cadence row refuses with a message that is false and says nothing about why

`bin/perry-task:391` (`Board.find`), reached because `Cadence` is in
`NON_TASK_SECTIONS` (`bin/perry-task:300`). Guarded by
`tests/test_cadence.py:526-531`.

Rubric item 5: *"`perry-task done` refuses a Cadence row, **and says why**."*
The refusal half holds; the explanation half does not:

```
DONE:    perry-task: refused — CAD-001 is not a row on the board
STATUS:  perry-task: refused — CAD-001 is not a row on the board
NEXT:    perry-task: refused — CAD-001 is not a row on the board
DROP:    perry-task: refused — CAD-001 is not a row on the board
RETITLE: perry-task: refused — CAD-001 is not a row on the board
```

`CAD-001` **is** a row on the board — the tool wrote it one command earlier, and
`perry-state --json` lists it. This is verbatim the defect class the same file
documents at `bin/perry-task:305-312` (*"a message that was false, about rows
the same tool had just printed"*), reintroduced for a different section.

The guarding test asserts only `code == 1` and that the row survives, so it
cannot see this. No test anywhere asserts the message text for `done`.

## MINOR

- **4 · The reader tolerates `###` sub-groups inside `## Cadence`; every writer
  stops at the first one.** `viewer/parsers.py:824-828` (new in this task)
  handles a `###` sub-group label; `bin/perry-task:498-512` (`section_rows`)
  breaks on the first non-blank non-`|` line and sees zero rows. On such a board
  `cadence-done` refuses ("not a row in `## Cadence`" — false again) while
  `cadence-add` **succeeds** and widens the header to 7 columns while padding
  none of the sub-grouped rows, leaving a ragged table that lints clean. Held at
  MINOR because no surveyed register uses this shape — but the divergence was
  created by this task, since `_parse_cadence` is new.
- **5 · `cadence.unreadable_frequency` never reaches the human surface.**
  `bin/perry-state:1061-1070` renders `count`, `overdue` and `undated` and drops
  it. A row unreadable on *both* axes falls into `unreadable_frequency` only
  (the `undated` branch is gated on `kind == "period"`), so it appears nowhere.
  Measured: a row with frequency `每周五` and `Next due` `—` is in the JSON and
  absent from the dashboard line.
- **6 · Two procedures over one payload, already unequal.**
  `work/reference/subcommands.md:95` names `cadence.overdue`, `cadence.undated`
  **and** `cadence.unreadable_frequency`; `modes/queue.md:245-249` — the other
  file the rubric names — omits the third.

## Informational

- `_parse_cadence` keeps positional fallbacks for five columns
  (`viewer/parsers.py:846-857`), against rubric item 2's "never by position".
  The docstring argues these reproduce pre-existing behaviour for headers the
  build cannot resolve, and `Last run` correctly has none. Defensible; noted
  because the rubric's wording is absolute.
- `cadence-done` on `CADENCE-NIGHTLY-RESEARCH` rewrote its `Next due` from the
  project's own `continuous` to `n/a`. `Next due` is a tool-owned derived cell so
  this is within contract, but it is a project's spelling being normalised.
- `cadence-add` on a `## Cadence` written as prose refuses cleanly and writes
  nothing — correct per the out-of-scope clause, though the message names no way
  forward.
- **The producer's account cites `scratchpad/mutate.py` as the reverting
  harness; no such path exists in the repo, and it reports "488 tests" against
  600 today.** Neither is a defect in the artifact; both mean the V4 reviewer
  cannot reproduce the claimed twenty-mutation run, which is why this review ran
  its own.
- Rubric item 1 fully verified: both subcommands write board + journal + event
  under one lock; `mint_cadence_id` returned `CAD-004` on the real register
  numbered `CADENCE-000/002/003` and correctly skipped the number-free
  `CADENCE-NIGHTLY-RESEARCH`; no procedure instructs a hand edit.

## What must change

1. **Bound `parse_due`'s date search** (`viewer/parsers.py:747-772`) so a date
   inside a path or a trailing parenthetical cannot become the due date — take
   the leading token of the cell rather than searching the whole string, and
   prefer an ISO week that appears before any bare date. A cell whose leading
   token is `n/a` must yield `None`. Add tests for both cells above; both
   currently report overdue.
2. **Make the overdue sort falsifiable** (`tests/test_cadence.py:422-432`):
   register the newer row first so board order and sorted order differ, then
   confirm the test goes red with `bin/perry-state:435` deleted.
3. **Give `done` (and `status`/`next`/`drop`/`retitle`) a Cadence-specific
   refusal** that is true and explains the rule — `## Cadence` is not a task
   section, a recurrence has no end, and the row is retired by removing it.
   Assert the message text in `test_done_cannot_close_a_cadence_row`.

Findings 4–6 are not blocking, but 4 should at least be recorded: the reader and
the writers now disagree about what a `## Cadence` section contains, and the
writers respond to that disagreement with another false "not a row" message.
