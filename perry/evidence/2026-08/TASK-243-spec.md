# TASK-243 — a count-preserving substitution destroys canonical records silently, and the drift report goes DOWN as it happens

> Consolidated from the board row 2026-08-30. The row's own fields are the
> acceptance criteria; this file is where a V4 reviewer reads them.

## Why this row exists

Found by the TASK-203 round 5 V4 reviewer 2026-08-30, ruled non-blocking for that row and filed here. Swap N ## Intake rows on the board by hand — same count, different rows — and any register-touching command persists the swap, INCLUDING resolve-intake, which declares 0 removals and is therefore inside its bound. Measured: 10 canonical records lost, 10 gained, rc 0, and perry-lint going from '16 row(s) drifted' to '0 row(s) drifted' as the records are destroyed. Also reproduced on asks.jsonl on the zh fixture. TASK-203's invariant does not catch it and is not supposed to: USER-906 chose a COUNT rule, and 32 to 32 is not fewer. The reviewer's reason for filing rather than blocking is the part worth keeping — closing it needs a per-record IDENTITY predicate, which is round 2's door and the fifth predicate the amendment explicitly forbids, and no tool path reaches it today because every tool-produced case is a shrink and is already refused.

## Deliverable

—

## Verification — V4

V4

## Out of scope

—

## Where to start

Blocked until TASK-203 lands. Start from evidence/2026-08/TASK-203-round5-v4-review.md, which carries the reproduction and the reasoning for why it was filed rather than blocked. Note the reviewer's own framing: no tool path reaches this today because every tool-produced case is a shrink and is already refused — so this is a hand-edit path, which makes 'report loudly' a serious candidate answer rather than a fallback.
