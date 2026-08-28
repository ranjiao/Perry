# TASK-150 / TASK-151 / TASK-152 — the three real instances the floor records

> Source: `tests/fixtures/live-state-expectations.json`, recorded by TASK-121
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: no
> Touches architecture: no — three test repairs of one shape
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P2
- **Attribution**: unlinked
- **Covers**: TASK-150, TASK-151, TASK-152 — one branch, three rows

## The three, and they are already judged

TASK-121 shipped a mechanism and **fixed none of the instances it found**, on
purpose. The floor stands at **7**: four named false positives, and these three.

| row | where | the literal |
|---|---|---|
| **TASK-150** | `test_md_store § test_okr` | `assertGreater(len(krs), 20)` over `perry/OKR.md` |
| **TASK-151** | `test_task_writer § test_every_hand_written_row_in_perrys_own_board_round_trips` | `assertGreater(len(rows), 5)` over the live `BOARD.md` |
| **TASK-152** | `test_prioritize § test_an_id_shaped_word_in_prose_is_warned_about` | `ctx` built from the live task records |

## What each was actually trying to say — do not delete the property

The counts are not the point; each is a **not-vacuous guard** bolted onto a real
property, and the repair keeps the property and moves the guard.

- **TASK-150** — the property is *the scanner did not stop early*. `> 20` was a
  proxy for "it read the whole file". A fixture whose KR count the test itself
  controls says it exactly.
- **TASK-151** — the property is *every hand-written row round-trips*. `> 5` was
  a proxy for "the corpus is not empty". Assert the round-trip over whatever
  rows exist, and take the not-empty guard from a fixture.
- **TASK-152 is the one with a second half, and it is the more fragile half.**
  The flagged line is `assertEqual(fn('the ROUND-2 defect', ctx), ['ROUND-2'])`.
  Its **neighbour** is `fn("see ADR-006 and USER-014", ctx) == []` — which needs
  **both of those ids to still resolve on this board** — and the guard says
  nothing about it, because `[]` is not a closed expectation. Repair **both**.
  The one the guard cannot see is the one that will break.

## Deliverable

All three assertions get their expectations from a fixture the test controls.
The floor drops from 7 to 4 and every remaining entry is a named false positive.

## Verification — V3

1. **The sweep reports 4, and every one is a false positive.** Re-record with
   `python3 tests/live_state_expectations.py --record`; it preserves existing
   verdicts, so nothing should be left unverdicted. **If a new hit appears,
   judge it — do not silence it to reach the number.**
2. **TASK-121's own guard test still passes**, including the assertion that at
   least one entry is a real instance — **which will now be false.** That test
   says, in its own docstring, that if every entry is a false positive you must
   *"say so here"*. **Read it and do what it asks**: this row is exactly the case
   it anticipated. Do not weaken it into vacuity; state the new situation and
   keep it able to fail.
3. **Each property still fails when broken**, on its own fixture and separately:
   make the scanner stop early → TASK-150's test reddens; break a row's
   round-trip → TASK-151's; make the prose-warning function miss a real id →
   TASK-152's; and make it *warn* about an id that does resolve → TASK-152's
   neighbour reddens. **Four mutations, four different reds.**
4. **`git diff -- perry/` empty.** These are test repairs; `perry/OKR.md` and
   `perry/BOARD.md` are not touched.
5. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `tests/test_md_store.py`, `tests/test_task_writer.py`, `tests/test_prioritize.py`
- `tests/fixtures/live-state-expectations.json` — re-recorded, verdicts preserved
- `tests/test_live_state_expectations.py` — **only** item 2's assertion
- fixtures the repairs need

## Out of scope

- The guard itself and its definition of the class.
- The four false positives — they are judged and stay.
- Any other instance you find. **Report it; it gets a row.**
