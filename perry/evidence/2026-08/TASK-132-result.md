# TASK-132 — a witness project makes 15 unverifiable keys verifiable

**Merged locally 2026-08-28** from `coding/task-132-unobservable-keys` @
`c4dde77`. Rung **V3**. `merge-check`: nothing new is red.

```
unobservable   15 across four empty collections  →  0
KR-O2.4         0                                →  0
```

**All 15 turned out to be correctly documented.** That is now *proved* rather
than assumed; before tonight nothing had ever compared any of them. `perry/`,
`bin/` and `schema/state-schema.json` untouched — 0 files.

The row said 23. The measurement said 15. Both the agent's count and mine agree.

## It refused the seam I pointed it at, and it was right

My spec said to read TASK-176's `payload=` seam first. **That seam hands
`compare()` a hand-written dict** — exactly the fabrication the row's own
prohibitions forbid for a real page. The agent said so and used the seam that
was already there and is honest: **`--root`**.

`tests/fixtures/witness-project/` is a second Perry project whose own state is
non-empty precisely where Perry's board is empty:

- an ADR still `active` past a 2026-06-30 sunset;
- `WIT-002` depending on `WIT-404`, an id no register carries;
- `WIT-001` `in_progress` with no dispatch slot and nothing moving it since
  2026-08-06;
- a linkage register asserted 2026-08-05 against an event log from 2026-08-06.

**The real tools read that directory and derive every entry.** Nothing is
written into a payload and nothing was added to `perry/`.

## The discipline that keeps it honest

`compare()` consults the witness **only** for paths inside a collection the
measured project left empty, and it supplies an **entry shape, never a
placement** — `boxes` is still built from the measured payload alone.

*Letting a fixture's shape decide where a live page's key table hangs would be
TASK-176's defect in a new costume.* `unassigned` and
`named_no_such_collection` are asserted byte-identical with and without the
witness, and `--no-witness` gives the pre-TASK-132 reading.

`not_observable` is intact, still named, and now says **which of the two
projects** left a collection empty.

## The mutation, and its mirror

One key per collection, deleting a real declaration from the real page:

```
expired_sunsets[].sunset                exit=1
moved_tasks[].at                        exit=1
depends_on_unknown[].unknown            exit=1
in_progress_with_no_live_run[].means    exit=1
```

And `test_the_same_mutation_is_silent_without_the_witness` runs all four with
`witness=None` and asserts **silence** — so it is the witness doing the work,
not a key that was fine anyway.

## Narrowed, not closed — and it said so

Observability is now the union of the measured project and the witness, so a
collection emptying on the live board no longer decides whether its keys are
checked, **for the collections the witness covers**. It added a fifth condition
it did not need tonight: `conformance.review_idle`,
`in_progress_with_no_live_run`'s twin from TASK-176, non-empty on the board
right now and whose six keys would go dark the day it empties.

A collection empty in **both** projects is still unobservable and is still
named. The fixture's README states the rule for extending it: **add the state,
never the finding.**

## Four things it corrected about my spec

1. **The baseline is 2372 tests, not 2369**, and `test_diagnose` fails **twice**
   under `-j 4` — the queue reconcile is **order/parallel sensitive** and
   disappears in a smaller run. That matches what I watched come and go tonight.
2. *"Read the `payload=` seam first"* pointed at the wrong tool. This row needed
   a second **project**, and `--root` already existed for that.
3. **`tests/fixtures/sample-project` is unusable as a witness.** Since the store
   read-cutover, tasks come from `tasks.jsonl` alone and that fixture has none,
   so it emits 0 tasks against a `BOARD.md` still listing three.
4. **Two traps worth a spec naming.** `paths()` collapses a list to its **first**
   element, so a condition holding on `krs[1]` and not `krs[0]` is still
   unobservable. And `bin/perry-task § TASK_EVENTS` silently skips any event
   kind outside a fixed set, so plausible-looking `created` / `review` events
   leave `updated` null and quietly empty two collections. Both cost the agent a
   cycle; both are written into the fixture's README.
