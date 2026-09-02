# ADR-013 — An ADR id is an address, and is never reissued

> Status: active
> Type: Architecture
> Date: 2026-09-02
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

`perry-decide` mints an ADR id by taking the maximum of the `ADR-NNN-*.md` files
on disk and adding one. It writes no events. So the set of files is the only
memory the minter has, and deleting a file erases a number from that memory.

Measured on `d49964e`, 2026-09-02, on throwaway projects:

- Mint ADR-001…003, `rm decisions/ADR-003-three.md`, then `perry-decide new
  four` → **`wrote ADR-003`**. The id now names a different decision than it
  named an hour earlier.
- Mint ADR-001…005, `rm decisions/ADR-002-two.md` (a *middle* id), then
  `perry-decide new six` → **`wrote ADR-006`**. The gap is not filled.

So the defect is narrower than it was first described: **only the highest id is
reissued**, because only the highest id contributes to `max()`. A hole in the
middle is inert.

The stake is that an ADR id is cited as a name. In this repository today:
`ADR-007` appears 321 times, `ADR-004` 237, `ADR-001` 154 — in other ADRs, in
design docs, in board rows, in commit messages. A citation resolves by number
and by nothing else. If a number can name two decisions, every citation to it
becomes ambiguous retroactively, and nothing reports that it happened.

`perry-task` already answers this question the other way. Its help states that
ids are minted from "the canonical store plus every id `purge` has taken out of
it (`minting_records`), never reused" — an id it has issued is retired through
the append-only event log and cannot come back. Two writers, one project, and
opposite answers to *what is an id*.

The disagreement was declared rather than resolved by `TASK-235`, which pinned
it with `test_a_deleted_adr_number_is_reissued_and_that_disagrees_with_purge`,
and raised as `USER-909` on 2026-08-29.

## Options

1. **Durable high-water mark — chosen.** `perry-decide` appends a mint event to
   `.perry/events.jsonl`, and `mint_id` takes `max(ADR files ∪ mint events)`.
   - Pros: makes the two writers agree on principle rather than by accident;
     `.perry/events.jsonl` is owned by `perry` in
     `schema/state-schema.json § claims[]`, not by a lane, so writing it is not
     a hand-off-contract breach; the scope is one code path, not an event
     surface on every command.
   - Cons: `perry-decide` gains an event surface it does not have today. The
     event log is declared derived and disposable, so deleting it re-exposes
     the defect — mitigated, not eliminated.

2. **Forbid deletion: an ADR may only be superseded.**
   - Pros: arguably what a decision record *should* mean. History is not
     deleted, and `superseded` already exists for the case.
   - Cons: **there is nothing to enforce it in.** `perry-decide` has exactly
     five commands — `bootstrap`, `new`, `supersede`, `status`, `list` — and no
     delete. An ADR leaves `decisions/` when a human runs `rm`. This option can
     only ever be a documented rule plus an after-the-fact lint detector, and
     reissue still happens when the rule is broken.

3. **Accept reissue; declare an id a slot rather than an address.**
   - Pros: honest, and costs nothing to implement.
   - Cons: silently invalidates every existing citation. Rejected.

4. **Leave it declared and pinned, as `TASK-235` left it.**
   - Pros: nothing is hidden; the named test tells the next reader what to
     change. A legitimate close.
   - Cons: the ambiguity remains real whenever the top ADR is deleted.

A fifth option was considered and is **foreclosed**: storing the high-water mark
in a counter file beside the ADRs. `tests/test_decide_writer.py:461` asserts
`ADR_ONLY = ^decisions/ADR-\d+-[^/]+\.md$` over every file in the project — that
guard is `TASK-235`'s own deliverable, and a counter file would break it. The
remaining durable home is the event log, which is why option 1 is narrower than
"give `perry-decide` an event surface" and still lands there.

## Chosen

**Option 1 — a durable high-water mark in `.perry/events.jsonl`.** An id, once
issued, is never issued again; `perry-decide` and `perry-task` state the same
rule about what an id is.

This overrides the recommendation recorded on `USER-909` itself, which was
option 2 followed by option 1. Option 2 was dropped on measurement: it has no
command to refuse in.

## Consequences

- `mint_id` in `bin/perry-decide` takes `max(ADR files ∪ mint events)`. Deleting
  the highest ADR file no longer lowers the next id.
- `perry-decide` writes to `.perry/events.jsonl` for the first time. It still
  does not write `journal/` — that remains a hand-off-contract refusal.
- The existing pin `test_a_deleted_adr_number_is_reissued_and_that_disagrees_with_purge`
  asserts the behaviour this ADR changes. It is **inverted, not deleted** — the
  disagreement it names stops being true and the test should say so.
- The middle-gap case stays as it is: `ADR-002` deleted from five leaves the
  next mint at `ADR-006`. Ids are not compacted and holes are permanent.
- Deleting `.perry/events.jsonl` re-exposes reissue for ids whose files are also
  gone. The log is declared derived and disposable
  (`bin/perry-task --help`), so this is a bounded, stated limitation rather than
  a guarantee — the file set alone cannot carry this fact.
- Nothing here prevents a human `rm`. This ADR makes deletion *safe for ids*, it
  does not make an ADR undeletable.

## Evidence

- `perry/evidence/2026-08/TASK-235-v4-review.md` — claims 4 and 5: the
  reproduction, and the measurement that reissue on `main` was non-deterministic
  (the same starting state gave opposite outcomes depending on one unrelated
  status flip) rather than merely present.
- Reproductions run for this ADR on `d49964e`, 2026-09-02, recorded above:
  top-id reissue and middle-gap non-reissue.
- `USER-909`, answered 2026-09-02 — the decision and its three reshaping
  measurements.
- `TASK-240` — the implementing row.

## What would reopen this

- The event log stops being written or is made non-durable, removing the only
  place the high-water mark lives.
- A second minter for ADR ids appears (a front-end, an import path), at which
  point `max(files ∪ events)` is no longer computed in one place.
- Ids acquire meaning beyond identity — ordering, grouping, or a namespace per
  lane — in which case what "never reissued" protects needs restating.
