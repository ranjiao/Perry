# Independent task review

Read `kernel.md`, `review-constraints.md` and the written acceptance criteria before
requesting review. Refuse a V4 review without written criteria. Use a genuinely
fresh context that did not implement the change; the author cannot self-award V4.
Give the reviewer exact base/delivery commit, diff, criteria, bound, test evidence,
architecture target documents and start/delivery checkpoint paths. Keep it read-only.

Each actionable finding cites source/evidence and explains the user-visible failure.
Separate a contradiction from an evidence gap. Return PASS/FAIL against each written
criterion and explicit untested limits. The reviewer must not merge, mutate task
state, expand scope, or treat a structural guard as evidence of correctness.

Save the review under `evidence/<month>/`, attach it to the task with `attach add`,
and record its actual actor identity. Use `task-close.md` for the closing transition;
V4's `verified_by` is the reviewer, not the implementing session. A FAIL produces a
concrete next_action; a PASS alone cannot fill a missing historical baseline.
<!-- next-close: work review -->

## 2 — Review constraints

Every reviewer reads `review-constraints.md`. Mutation-based evidence is restored
against an independent committed baseline and verified with `perry-restore-check`.
A test asserting its own restore bytes is not independent restoration evidence.
