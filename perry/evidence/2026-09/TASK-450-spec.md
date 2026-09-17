# TASK-450 — full merge-result gate and duration recording

Date: 2026-09-17. Owner: Coding Agent. Priority: P1. Rung: V3 with independent review.
> Dispatch mode: auto
> Executor: codex
> Estimated cycle: medium
> Subjective verification: none
> Touches architecture: sections 2, 3, NN-3, NN-5; test harness and integration procedure
> Deployed: no

User authorized the recommended batch; locked DESIGN-021 phase C defines scope.

## Deliverable

Implement DESIGN-021 section 5.3: tests/merge-check supports the full tier on
an isolated merge result of the exact current base and candidate, records timing
provenance when explicitly requested, and integrates the successful record through
the authorized coding/integrator boundary. Preserve existing failure attribution.
Do not edit main or merge automatically. A moved base or candidate invalidates
its acceptance receipt; report exact refs/tree and outcomes.

## Acceptance criteria

1. One-candidate full gate actually runs all full-suite stages, not a duplicate
   partial list missing script syntax/help checks. Selected-check diagnosis is
   clearly not a full merge acceptance.
2. Run in isolated scratch; merge conflicts, failed commands or failing tests
   yield nonzero without writing product state in the caller checkout.
3. Retain existing base/candidate/pair failure attribution and truthful limits.
4. Explicit recording emits durations with provenance for the tested merged
   code. Update durations provenance validation in the same change as required
   by the design. Never claim a not-yet-created commit hash or overwrite an
   untested accepted record. Explain how the final recorded artifact is verified.
5. Primary procedure calls the real supported full/record interface before merge,
   checks the candidate/current base still match, and respects code commit ownership.
   Preserve current full+slow requirement; no change to release-record rules.
6. Fault fixtures demonstrate conflict, red base, red candidate, interaction,
   failure in the omitted suite stage, and base movement; clean pass receipt
   proves which tree was tested. New tests are behavioral, not wording mirrors.

## Files in scope

tests/merge-check, tests/run and tests/parallel only as needed for reuse and
record transport; targeted harness/provenance tests; test duration registration;
work/reference/dispatch.md integration section and related merge documentation.
No other test-selection redesign.

## Dependencies

Existing phase A/B selector and tier implementation already landed. Coordinate
shared dispatch.md edits with TASK-443 and TASK-464. Phase D ratchet remains
TASK-455 and is not implemented here.

## Verification

Targeted harness fixtures plus independent review; clean-env merged full and
slow suites before acceptance, git diff --check. Record exact base/candidate/tree.
No real remote requests are needed for local tests.

## Out of scope

Remote CI/admin settings, branch protection, publication, schema/architecture
edits, budget ratchet, automatic merges and edits to other worktrees.

## Bound

DESIGN-021 phase C and its existing merge-check interface; no new merge service.
