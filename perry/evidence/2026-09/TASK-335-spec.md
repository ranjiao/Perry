# TASK-335 — spec

> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Touches architecture: no
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Track / mode**: main / project
- **Verification rung**: V3 — a reproducible run. This is a test-only change,
  with no write path and no schema change.
- **User decision, 2026-09-14**: "只改测试：在冻结副本上测" (change only the
  tests: measure on a frozen copy). Chosen over adding a pinnable clock to
  `bin/`, and over leaving the reds.

## Why

`tests/test_contract_key_parity.py` has two tests that have been standing reds
on every full run:

- `TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`
- `TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness`

The row's own measurement found the cause, and the PMO confirmed it on
2026-09-14. The tests' `blind` measurement is `parity.measure(witness=None)`,
which reads **Perry's live checkout**. `conformance.in_progress_with_no_live_run`
fills as soon as an `in_progress` row goes 4 hours without an event
(`bin/perry-task`, `in_progress_idle_hours`). Today that row is `TASK-436`, so
the key becomes observable without the witness and both anti-vacuity assertions
fail.

**The tests go red with the passage of time alone, on an unchanged tree.**
Closing `TASK-436` would turn them green and fix nothing. Widening the assertion
would bring back the vacuity TASK-132 built this class to remove.

## Deliverable

1. **Both `live` and `blind` measure a frozen copy, not the live checkout.** The
   two classes that assert on `blind` get a temporary copy of Perry's state (the
   files the measured commands read). In the copy, every clock-dependent input
   those assertions rely on is pinned, so each collection in `MUTATED` is empty
   without the witness regardless of when the suite runs. For example, restamp
   the latest event of every `in_progress` / `review` row to now, or whatever the
   enumeration below shows is needed.
   - `live` (witness on) and `blind` (witness off) must measure **the same**
     frozen copy, so that the only difference between them is the witness.
2. **Enumerate every clock-dependent collection** in `WITNESSED` / `MUTATED`
   (`in_progress_with_no_live_run`, `review_idle`, `expired_sunsets`,
   `moved_tasks`, …) and freeze each one the blind assertions depend on. Say in
   the result which you froze and why each of the others is not clock-dependent.
3. **Keep the anti-vacuity and prove the freeze is load-bearing.**
   - The existing witness controls stay as they are.
   - Add a control: the same copy **without** the freeze, with an `in_progress`
     row aged past the threshold, fills `in_progress_with_no_live_run` in the
     blind run. That shows the freeze, not luck, is what empties it.

## Files in scope

- `tests/test_contract_key_parity.py` (the two classes, their `setUp`, and the
  helpers they use).
- `tests/contract_key_parity.py`, **only** if `measure()` cannot take a root
  already. It accepts `root`, so prefer not to touch it.
- `perry/evidence/2026-09/TASK-335-result.md`, written.

## Bound

Enumeration: every assertion in the two classes that reads `self.blind` or
`self.live`, and every collection named in `WITNESSED`. Size: derive it. The
last element is the last `WITNESSED` entry.

## What it must not do

1. Change `bin/`, `viewer/`, `schema/`, any contract page, or
   `tests/fixtures/contract-key-parity.json`, the recorded baseline.
2. Change the witness fixture, `tests/fixtures/witness-project`.
3. Weaken an assertion: no `assertIn` that used to be `assertEqual`, and no
   condition skipped when the live board happens to fill a collection.
4. Write to Perry's live stores, or change `TASK-436` or any other row.

## Verification

1. The module is green at the final commit **while `TASK-436` is still
   `in_progress` and idle**. That is today's state, which is exactly the state
   that reddens it.
2. **The time machine.** In a `git archive` copy, age every live `in_progress`
   event by 30 days. The module must stay green. Then remove the freeze: the two
   original tests must go red.
3. Mutations, each reddening a named test:
   - remove the freeze;
   - remove the witness from `live`;
   - make `blind` read the live checkout again;
   - delete the new freeze control.
4. The full suite on the final commit. With `test_resume` fixed at `d6723ae0`,
   the expected reds are **zero**. Name any red, and re-run it alone at the code
   and at base before attributing it.
