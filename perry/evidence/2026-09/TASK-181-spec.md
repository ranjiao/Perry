# TASK-181 — spec

> Design: `design/DESIGN-009-*.md` § 6 step 1
> Dispatch mode: auto
> Executor: claude-subagent (stdlib-only store work in this repository; no MCP)
> Estimated cycle: medium
> Subjective verification: whether the record shape is the one step 2's renderer will need — the next step is the real judge
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked directly, but see below — this row is the HEAD of the chain that gates `P003-O2-KR3`
- **Verification rung**: V4

## Why this row matters more than its own KR

`TASK-262` carries phase KR `P003-O2-KR3` and is blocked on `TASK-236`, which is
blocked on `TASK-181` and `TASK-182`. This row is the head of that chain, so it
is the first thing that has to move for that KR to become reachable at all.

`DESIGN-009` § 6 step 1: *"The record shape and the mint, with `perry-okr build`
producing objective rows and `verify` byte-comparing. **No id written yet.**"*
The design also says steps 1 and 2 are worth landing alone, because they make
the store hold what `OKR.md` says without introducing a new concept.

**Measured 2026-09-02:** `perry/okr.jsonl` holds 38 `kr` records and 3 `version`
records and **no objective records at all**. Today an Objective exists only as a
title string repeated inside every `kr` record's `objective` field
(`bin/perry_md_store.py:196`), which is the defect `DESIGN-009` is named after.

## Files in scope

- `bin/perry-okr` — `build` and `verify`.
- `bin/perry_md_store.py` — the record shape, around :196 and the scanner below it.
- `perry/okr.jsonl` — gains objective records.
- `tests/` — the guard.

## Deliverable

`perry-okr build` produces `kind: objective` records alongside the existing `kr`
and `version` records, and `perry-okr verify` field-compares them against
`OKR.md`. **No id is minted in this row** — that is step 3, and writing one here
would decide by accident what `DESIGN-009` decides on purpose.

## Out of scope

- Minting or writing `id` on an objective. Step 3.
- The renderer rebuilding `OKR.md`. That is `TASK-182`, step 2, and it is the
  gate that proves this row's record shape was right.
- **The declaration files, and this one has a stop condition.** If the record
  shape cannot be added without changing them, **STOP and report it in your
  RESULT block** rather than editing: they are on this project's high-stakes
  list and a spec that touches them is refused by the dispatch gate on purpose.
- Editing `OKR.md` itself. It belongs to the `goals` lane; this row changes the
  tool, not the document.
- Any project other than Perry's own.

## Verification

- `perry-okr build` emits one objective record per Objective heading in
  `OKR.md`, and the count matches the headings. State both numbers.
- `perry-okr verify` field-compares clean against the current `OKR.md`.
- **`OKR.md` is byte-unchanged by this row.** Verify with a checksum taken
  before and after, and compare against the BEFORE value — not against the
  bytes you just wrote.
- The existing 38 `kr` and 3 `version` records survive untouched: same count,
  same content. A build that silently reshapes them fails.
- **Mutation**: break the objective-record branch and show a NAMED test goes
  red. A green mutation is a finding either way — the guard does not work, or
  the test does not test it.
- Clear `__pycache__` and wait past the second boundary before re-running; a
  same-size edit reverted inside one second runs stale bytecode.
- `bash tests/run`: report the baseline failure count you started from and the
  runner that produced it. Two runners in this project disagree, so a bare
  number is not evidence.

## Bound

The finite set this round checks, named before the round:

**One record kind, one store, one document class.** Size 3:

1. The `objective` record shape in `bin/perry_md_store.py § STORED` and its
   scanner.
2. `perry/okr.jsonl` — the 10 emitted records, against 10 Objective headings
   in `perry/OKR.md`, with `kr: 38` and `version: 3` unchanged.
3. `perry-okr verify` clean, and `perry/OKR.md` byte-unchanged.

The round is over when those three are checked. **Deliberately not the
category "the record shape is right for every OKR document anywhere"** — that
has no last element, and step 2 (`TASK-182`) is the declared gate for whether
this shape was right: `DESIGN-009 § 6` says *"if the renderer cannot rebuild
the five headings from records, the records are wrong."*

### Out of the set, stated so the reviewer does not chase them

- **The `record_key` choice.** The author keyed an Objective on
  `(version, heading)`, so a renamed heading is REPORTED rather than followed.
  That is a deliberate judgement the author flagged: the alternative available
  at step 1 is the `Objective <N>` ordinal, which `schema/goals-list-contract.md
  § Not here` refuses and `DESIGN-009` decision 1 calls the trap. Making an id
  survive a rename is steps 3-5. **Review whether the reasoning is sound and
  recorded, not whether a different key would be better.**
- **`goals/state/OKR_TEMPLATE.md`'s third heading** carries a trailing HTML
  comment that leaks into `title`. `heading` still round-trips and the renderer
  reads `heading` only, so nothing is broken; the author reported it. It is a
  NEW ROW if it matters, not this round's failure.
- **The one red in the after-suite**
  (`test_host_support…test_concurrent_mixed_registers_do_not_exceed_global_cap`)
  is already tracked as `TASK-272`, a known flaky mixed-register test. The
  author judged it load-induced — three other agents' suites were running — and
  said explicitly that this is their judgement rather than evidence. **Treat it
  as an open question, not as a settled pass.**
