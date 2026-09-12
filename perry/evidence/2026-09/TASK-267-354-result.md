# TASK-267 and TASK-354 — result

> Two rows, one class, one round: **a surface that contradicts what the tool
> actually does.** Both closed at **V2** — `ADR-020`'s gate answers no for
> each (a linter's output and a contract page; no write path, no
> `schema/state-schema.json`).
> Executor: the PMO session, inline on `main`, per `ADR-018 § B`.

## TASK-267 — the one census line that did not name its store

`perry-lint` prints one verdict per declared store. Six named their register;
the seventh did not.

```
· store: 433 record(s), 0 row(s) drifted          ← the tasks store
· risks store: 4 record(s), 0 risk(s) drifted
· intake store: 0 record(s), 0 row(s) drifted
· ask store: 27 record(s), 0 ask(s) drifted
· OKR store: 51 record(s), 0 row(s) drifted
· config store: 9 record(s), all valid
· linkage store: 257 record(s), 0 malformed
```

Five print sites in `bin/perry-lint`, plus `drift against the store` in the
absence branch. Now `task store:` and `drift against the task store`.

**The rename is a two-file edit and that is the good part.**
`tests/test_store_drift.py § CENSUS_LINES` is keyed by claim path, so the
wording has one declared home and changing the tool without changing the map
reddens.

### Two guards, not one

- `test_every_census_line_names_the_store_it_is_about` quantifies over **every**
  entry rather than re-checking the one that was wrong, so a bare `store` label
  reddens in whichever row someone next writes one. It also requires the
  `<register> store` convention.
- `test_no_two_stores_share_a_census_label`, because a label that names its
  register is only useful if it names ONE. Renaming the task store onto a label
  another store already held would satisfy the first test and make the census
  unreadable.

### Mutations — four, none green

| # | Broken | Result |
|---|---|---|
| M1 | the label reverted to bare `store` | RED — 3 tests |
| M2 | two stores given the same label | RED — the collision test |
| M3 | `perry-lint` printing the old wording | RED — 2 tests |
| M4 | a label losing its ` store` suffix | RED — the convention test |

Both files restored and sha256-verified between plants.

### The rename broke an unrelated module, and the guard written to prevent it did not see it

**This is the part worth reading.** The first rename was `task store:`. It is
DISTINCT from `ask store:`, so `test_no_two_stores_share_a_census_label` passed
— and:

```python
>>> "ask store:" in "task store:"
True
```

`tests/test_register_substitution.py § lint_drift` finds a register's census
line **by substring**. Asked for the `asks` register it matched the TASK line,
hit the no-event-log branch, and did `int("but")`. One rename, one unrelated
module red, caught by the full suite and not by either guard this round wrote.

Fixed at the source rather than at the consumer: the label is **`tasks store`**,
which also matches its own file name `tasks.jsonl`, and `"ask store:"` is not a
substring of it. `test_no_census_label_contains_another` is the third guard,
asserting **containment** rather than equality over every ordered pair —
because containment is the property a substring consumer actually needs, and
distinctness was not enough. M5: reverting the label to `task store` reddens
three tests including the new one.

**What this says about the other two guards.** They were written from the
defect that was in front of me — a label that names nothing — and not from the
question *what could a consumer of this string do*. The suite answered that
question for free, which is the argument for running it before believing a
green.

## TASK-354 — the contract counted twenty-six and listed twenty-seven

**It was bigger than the row said**, in three ways.

**Four prose sites, not one.** `:61`, `:243`, `:265` and `:266` all said
twenty-six. `:254` said *"a twenty-seventh kind added to the writer reddens it"*
— a page anticipating the twenty-seventh while still calling the total
twenty-six.

**The derived split beside it was wrong in both halves and did not sum.**
*"Eleven of the twenty-six … The fourteen that are live"* — eleven plus
fourteen is twenty-five. Measured 2026-09-12 against the table and the live
log: **27 documented**, **5** not yet exercised (`cadence-add`,
`cadence-done`, `risk-add`, `risk-migrate`, `track`), **22 live**.

**Four kinds are in this project's log and on no page.** `link-edge`,
`link-unlinked`, `migration` and `migration-correction`, written between
2026-08-28 and 2026-09-03 — 117 events — by writers that no longer exist.

**That last one is correct behaviour and is now stated rather than left to be
discovered.** The page documents what the writer **can emit**; a kind no tool
emits any more has no row. `TestTheDocumentedKindsAreTheWriters` derives the
emittable set from `bin/perry-task` and is green throughout, which is exactly
right — and is exactly why it could not see this row's defect. **The rot was
in a sentence beside the table, and nothing read the sentence.**

### The guard

`tests/test_events_feed.TestTheProseCountsTheKindsItLists`, 3 tests, derives
the count from the table and reddens if the prose disagrees. Anti-vacuity
first: a regex matching nothing would make every assertion pass over an empty
set.

### Mutations — three, none green

| # | Broken | Result |
|---|---|---|
| M1 | the headline sentence back to twenty-six | RED — 2 tests |
| M2 | the tail count back to twenty-six | RED — 1 test |
| M3 | a kind row deleted from the table | RED — 2 tests |

Contract restored and sha256-verified between plants.

## What these two share

Neither defect was reachable by the checks that already existed, and in both
cases the existing check was **correct and green**. `perry-lint`'s census
covers all seven stores; `TestTheDocumentedKindsAreTheWriters` compares the
table to the writer both ways. What neither could see is the *prose beside the
thing it checks* — a label, and a number. Both now have a derived guard, which
is the only kind that survives the next edit.
