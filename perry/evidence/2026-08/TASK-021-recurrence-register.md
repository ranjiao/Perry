# TASK-021 — `## Cadence` gets a writer

> Rung: V3 (reproducible run)
> Scope: the recurrence register only. `OKR.md § Commitments`, named in the
> same row, is the `goals` lane's and is untouched — Perry now has a real OKR.

## The defect

Third writerless board section, and the one whose stored value is **computed**.

| | |
|---|---|
| `Next due` | derived from `Frequency` + the last run, and a human retyped it after every occurrence |
| readers | `perry-state`'s `board.cadence` count, `work/reference/subcommands.md § triage`, `modes/queue.md` triage step 5 |
| writers | none |

Two of those readers instructed the agent to "surface Cadence rows past their
`Next due` by age" — an instruction to eyeball a table, which is the one thing
Perry's oldest rule forbids, written a release before anything could compute
an age.

What a hand-maintained computed cell actually looks like, from
`~/proj/gimegime-pmo/BOARD.md § Cadence`:

```
| CADENCE-003 | Weekly PMO status report | PMO Agent | weekly |
  **2026-W32 friday-review (8/7)**（W31 版 ✅ 8/3 补作；W25–W30 缺口收口 …）|
```

A due date, a bolded ISO week, and a parenthetical listing which nine
occurrences were skipped — because nobody re-derives `frequency + last run`
weekly. `perry-state` now reports that row and one other as **8 days overdue**,
which is the first time either has been a number.

## What shipped

`perry-task cadence-add` / `cadence-done`; `parsers.Cadence` and
`_parse_cadence`; the recurrence arithmetic (`parse_frequency`, `advance`,
`next_due_after`, `parse_due`) in `viewer/parsers.py`; `cadence_report` in
`bin/perry-state` and a `🔁 Cadence` dashboard row.

**`Last run` is new, and it is the point.** `Next due` is an absolute date, so
unlike `Idle` it does not rot overnight — but it is wrong the instant the
ritual runs, and nothing on the board said what it had been computed from. The
input is stored now and the derived value is stamped from it, so a due date can
be checked instead of trusted. Same discipline as `Stage since`, `Arrived`
and `Asked`.

**`Last evidence` went the other way — required to optional.** A live register
does not have the column and had been carrying a `table-columns` lint error for
it since the schema was written. `cadence-done` creates the column when it has
something to put there, so requiring it up front bought nothing. gimegime-pmo:
60 → 59.

**The arithmetic is in `parsers.py`, not in the writer.** It has two callers
that must agree — the writer stamps `Next due` and the reader parses it back to
decide what is overdue — and a writer and reader holding separate copies of a
period table is the same shape as the column-order split this repo has now paid
for three times.

## Verification performed

```
cadence-add ×4, one per frequency  → four different due dates, computed
cadence-add --frequency continuous → recorded; Next due `n/a`
cadence-add --frequency "whenever" → refused, nothing written
cadence-add on a board with no
  `## Cadence`                     → section created AFTER the priority tables
cadence-add on a board numbering
  its rows CADENCE-NNN             → minted the next number in THAT sequence,
                                     not a second one starting at 001
cadence-done                       → Last run + Last evidence stamped,
                                     Next due recomputed from the row's cell
cadence-done, evidence omitted     → refused
cadence-done on a 5-column
  register                         → `Last evidence` created, not dropped
localized (zh) board, add + done   → `## 例行节奏`, `上次执行`, read back clean
perry-lint                         → clean on Perry and on the templates;
                                     gimegime-pmo 60 → 59
488 tests                          → green
```

**Twenty behaviours verified by reverting them** (`scratchpad/mutate.py`: apply
the inverse edit, run the one test, require red, restore). Every one went red,
including the four that matter most — `cadence-done` leaving `Next due` alone,
`Next due` stamped as today regardless of frequency, cadence columns read
positionally, and `Last run` given a positional fallback.

**Two tests passed for the wrong reason and were fixed.** `refuses without
evidence` asserted only the exit code — with the guard removed, writing `None`
into a cell raises and also exits 1, so the test was satisfied by a traceback.
It now asserts a refusal. And `a row due today is not overdue` could not fail,
because `days_overdue` was tested for truthiness and 0 is falsy; the check is
`is not None` now, so a `days >= 0` bug is visible.

## Found while building it

- **`perry-task list` folded every event carrying an id into `tasks`.** A
  `USER-` row raised by `ask` arrived as a task with `status: "pending"`,
  `open: false` and no priority, counted in `closed` — against a contract that
  says in as many words that these sections are not in this payload.
  **Pre-existing**, reproduced on clean `HEAD`; `cadence-add` would have put
  its rows in the same place. Fixed, contract bumped to `1.3` with the
  semantic correction called out, and the classification is now a partition of
  `COMMANDS` that a test asserts is total — so a future subcommand fails there
  rather than leaking silently.
- **`## Cadence` had no parser of its own.** `_parse_task_table`'s positional
  fallbacks put `Frequency` in `status` and `Next due` in `next_action`, so
  every cadence row in `perry-state --json` claimed a status of `weekly` — a
  value the enum does not contain, which `tests/test_i18n.py` special-cases by
  heading to stay green. One parse now feeds both views; the legacy projection
  is pinned byte-identical against both real boards and the fixture.
- **Perry's own dogfooding caught a doc defect in this work.**
  `test_perry_itself_passes_its_own_id_checks` failed twice on this work — a
  literal user-input id written into a changelog entry as an illustration, and
  a literal cadence id written into this file's own verification log. Both are
  dangling ids, exactly what `perry-diagnose` reports on other projects. The
  skill that reports this must not commit it, and it did not.

## What could not be parsed on the real registers

Nothing. All five `Frequency` cells and all five `Next due` cells on
`~/proj/gimegime-pmo` resolve — `continuous` and `hourly` as aperiodic,
`monthly`/`weekly` as periods, and the three prose `Next due` cells to
`2026-08-31`, `2026-08-09` and `2026-08-09`. `~/proj/Perry`'s register is an
empty placeholder row.

Two things are worth naming anyway:

- `CADENCE-NIGHTLY-RESEARCH` and `CADENCE-OQ-A-WATCH` carry **no number**. They
  read fine and cannot collide with a minted id, so nothing was done about
  them, but any future code that assumes a cadence id ends in digits is wrong.
- An ISO week resolves to its **Sunday**, chosen so a weekly ritual is not
  reported late on Monday. It is a judgement, not a fact the cell states.

## Not done here

- **`OKR.md § Commitments`**, the other half of this row's title. Out of
  scope — the `goals` lane owns that file.
- **Perry does not fire recurrences and still does not.** `modes/queue.md` and
  DESIGN-003 § 3 are explicit that the register records what repeats and the
  host's cron does the firing. `cadence-done` is how a run gets recorded, not
  how it gets triggered.
- **`cadence` is exposed only through `perry-state --json`**, which is not a
  frozen contract. Putting it in `perry-task list` would be a `1.x` addition
  and a separate decision; the contract's own "what this does not cover"
  section says so, and nobody has asked.
- **No way to retire a cadence row through the tool.** A recurrence ends by
  deleting the row, which is a hand edit. `drop` is a task verb and `done`
  correctly refuses a section the task path cannot see.
