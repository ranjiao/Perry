# TASK-239 — the decide lane is fully ungated under ADR-004 after TASK-235, and the comment that records it says the opposite

> Consolidated from the board row 2026-08-30. The row's own fields are the
> acceptance criteria; this file is where a V4 reviewer reads them.

## Why this row exists

Measured by the TASK-235 V4 reviewer 2026-08-30 on both trees, PERRY_CONFORMANCE=enforce with nothing declared: on main, perry-decide new returns rc=1, refuses, and writes NO ADR body; on coding/task-235-decisions-index it returns rc=0 and writes ADR-001. The gate refused the WHOLE command on main, bodies included, and there is no reachable main state where it did not. Removing it was correct — after TASK-235 nothing in the lane has a files[] shape, so a gate on it could not fire — but the effect is that the decide lane went from fully gated to fully ungated, and perry-decide's own justifying comment closes with 'only the index write was ever gated', which is false. The comment is being corrected on the branch; this row is the capability that correction reveals is missing. Raised because the reviewer flagged that the follow-up existed 'nowhere but prose'.

## Deliverable

—

## Verification — V4

V4

## Out of scope

—

## Where to start

Blocked until TASK-235 lands. Start from the reviewer's measurement rather than re-deriving it: evidence/2026-08/TASK-235-v4-review.md carries both exit codes on both trees. The first question is not how to gate it but WHETHER ADR-004 was ever meant to cover a lane whose artefacts are prose documents — ADR-007 rule 3 says the Python layer never parses a document at all, and a conformance gate is a shape check on a document.
