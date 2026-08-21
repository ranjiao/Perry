# TASK-171 spec — the events key table is missing three event kinds the live log carries

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: small
> Source: `aimark/doc/perry-contract-gaps-4.md § 5.2`. aiMark named two; there
> are three.

## The measurement

```
live kinds  : add answer ask depends done drop evidence intake next
              prioritize retitle rung start status
documented  : add depends done drop evidence next prioritize retitle rung
              stage start status track
live-not-doc: answer  ask  intake
```

`stage` and `track` are documented and not yet exercised on this log. **That is
not a defect** — the contract describes what the tool can emit, not what this
project happened to do.

`intake` rows have an **empty `task`**: they are written against the queue, not
against a row. That has to be said, because a consumer indexing events by `task`
drops them silently.

## The deliverable

1. `ask`, `answer` and `intake` documented in
   `schema/events-list-contract.md`'s event key table, each with what it means
   and what its `task` field carries.
2. **A test that compares the documented set against the set the tool can
   actually emit** — derived from the writer, not from a hand-kept list. A hand
   list is how this table came to be missing three kinds, and re-writing the
   hand list by hand fixes today and not the class.

That second item is the row. Find where the event kinds are actually written
(`bin/perry-task`) and make the test read from there.

## Two things to be careful about

- **The contract moved to `perry-events/list/1.1` today** (TASK-168 flipped the
  first page to the tail). Documenting kinds that already ship **is not a version
  bump** — this project has a stated precedent for that, quoted in
  `schema/task-list-contract.md`'s *"Not a version"* note. Do not move the
  version, and say in the changelog that you did not and why.
- **`tests/contract_key_parity.py` may or may not see this.** It compares
  documented paths against emitted paths; the `event` field's *values* are not
  paths. Check whether KR-O2.4 moves. If it does not, say so — that is itself
  worth knowing, because it means an enum can go stale where a key cannot.

## Verification

1. The documented set equals the set the writer can emit, proved by the new
   test rather than by eye.
2. Deleting one kind from the table reddens that test.
3. Adding a new event kind to `bin/perry-task` without documenting it reddens
   that test. **This is the direction that matters** — the table went stale
   because nothing noticed a new kind.
4. `intake`'s empty `task` is stated.
5. KR-O2.4's value before and after, with a sentence on whether this contract's
   enums are inside its reach.
6. `perry-lint --root .` — 0 errors.

## Out of scope

- Do not change the version. Do not change any behaviour of `perry-task events`.
- Do not touch `schema/state-schema.json` or `perry/`. `git diff -- perry/`
  must end empty.
- **`bin/perry-task`'s `asks` register belongs to TASK-170**, running in
  parallel. Read `bin/perry-task` freely; do not edit it unless the test in
  item 2 genuinely requires it, and say so if it does.

## Ground rules

- Branch `coding/task-171-event-kinds`, commit there, **no PR, no push**.
- `/usr/bin/python3` explicitly; **measure your own baseline** first.
- `/usr/bin/python3 tests/parallel -j 4`. Verify yours is the only
  `tests/parallel` on the machine before trusting a reading — and **do not write
  a wait-loop whose own command line contains the pattern it waits on**; one on
  this machine today spun at 100% CPU forever and made that check report a false
  positive for every agent.
- Expected baseline: **80 modules · 2355 tests · 2 red** —
  `test_contract_invariance` and `test_diagnose`. **Neither is yours.**
