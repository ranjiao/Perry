# TASK-169 spec — `perry-knowledge/list/1.0` ships every field aiMark asked for and has no contract page

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: small
> Source: `aimark/doc/perry-contract-gaps-4.md § 3`, re-measured here
> 2026-08-21 (`evidence/2026-08/aimark-contract-gaps-4-triage.md`).

## This is a page and an announcement, not a build

aiMark's round-4 **top priority** — *"if you only take one"* — asks for a read
surface for knowledge cards, on the stated grounds that `perry-knowledge` is
`propose` / `promote` only and *"there is no read side at all"*.

It exists:

```
$ /usr/bin/python3 bin/perry-knowledge list --json
{ "contract": "perry-knowledge/list/1.0",
  "project_root": …, "state_root": …, "total": 1, "stale": 0,
  "cards": [ { "path", "topic", "slug", "kind", "claim", "owner_role",
               "source", "last_verified", "invalidated_by", "stale" } ] }
```

All nine fields the request names are there, plus the aggregate it called a
bonus.

**Why a careful consumer could not find it: `schema/` has no page for it.**

```
decide-list-contract.md  events-list-contract.md  goals-list-contract.md
roles-list-contract.md   state-schema.json        task-list-contract.md
```

A tool that emits a `contract:` string and has no contract document is invisible
to anyone reading `schema/`, which is where a consumer is told to look. This is
the same defect class as `conformance.missing_projection` — it ships, it is
real, and no page a consumer reads announces it.

## The deliverable

1. **`schema/knowledge-list-contract.md`**, in the shape the four existing
   contract pages use. Read `roles-list-contract.md` first — it is the newest
   and the smallest, and it is the closest model.

   It must document **every emitted path**, top-level and per-card, including
   `total`, `stale` and the per-card `stale` flag. Derive the list from the
   payload, not by reading the source and hoping.

2. **`schema/README.md` stops saying three contracts.** Count them and say the
   number, and state how a reader is meant to discover a new one. *(There is a
   row for the README's other staleness — the goals pin — at TASK-130. Fix the
   count and the discovery sentence here; leave TASK-130's pin alone if it is
   a separate line.)*

3. **`tests/contract_key_parity.py` covers it.** That instrument compares
   documented against emitted, and it could not see this contract because there
   was no page. Adding the page must bring it under the same guard that
   KR-O2.4 measures — **and KR-O2.4 must still be 0 when you are done.** If
   registering it takes KR-O2.4 above 0, that number is the finding: report it
   with the list of keys, and do **not** edit the instrument to make it pass.

## What `stale` means, and why it has to be stated

`perry-knowledge --help` is emphatic that `Invalidated by` is what makes a card
*revisable instead of accumulating* — *"without it the card goes stale in
silence, which is the failure mode the whole card schema exists for."*

The payload already computes a `stale` flag. **The page must say what predicate
produces it**, in the same words the code uses, because a consumer that renders
"3 cards unverified since June" from a flag it does not understand is the second
reader this whole arrangement exists to prevent. Read the implementation and
state the rule; do not invent a plausible one.

## Verification

1. Every key the live payload emits appears in the page. Prove it by diffing the
   documented set against the emitted set programmatically, and paste the
   output — not by eye.
2. `tests/contract_key_parity.py` includes the contract, and **KR-O2.4 is 0**.
3. `schema/README.md`'s contract count equals the number of contract pages,
   checked by a test rather than by a human counting.
4. The `stale` predicate stated on the page matches the implementation. Assert
   it, do not assert *a* rule that happens to be true for today's one card.
5. `perry-lint --root .` — 0 errors.

## Out of scope

- **Do not add a field to the payload.** aiMark asked for a read surface, not a
  richer one; the surface exists. If you find a field that plainly should exist,
  say so in the report and do not add it.
- Do not touch `bin/perry-knowledge`'s behaviour. If the page cannot honestly
  describe what the code does, that is a finding — **report it and stop**,
  rather than adjusting either to match.
- Do not touch `schema/state-schema.json`, `schema/events-list-contract.md`
  (another agent is in that file), or `perry/`. `git diff -- perry/` must end
  empty.

## Ground rules

- Branch `coding/task-169-knowledge-contract-page`, commit there, **no PR, no
  push**.
- `/usr/bin/python3` explicitly; **measure your own baseline** first.
- `/usr/bin/python3 tests/parallel -j 4`. Verify yours is the only
  `tests/parallel` running before trusting a reading.
- Expected baseline: **80 modules · 2334 tests · 2 red** —
  `test_contract_invariance` (a union-typed key, see
  `evidence/2026-08/contract-invariance-union-types.md`) and `test_diagnose`
  (`['TASK-007','TASK-9999']`, TASK-165). **Neither is yours.** A different set
  is a difference to report, not to absorb.
