# Architecture analysis integration review criteria

Authority: user requests in this conversation, including independent review and
merge only when sound (2026-10-12). This document fixes the review scope before
the independent reviewer runs; it does not change the user's target architecture.

## Bound

Enumeration: `git diff --name-only db06e70c...HEAD` on the architecture feature
branch, plus the four existing lifecycle consumers below for integration context.
Size: 30 changed files before adding this criteria file; 31 including it.
Lifecycle paths: direct work, automated dispatch, manual delegate handoff, close.
Remainder: scheduled checks, automatic repairs, non-Python parsing, hostile
filesystem attackers, distributed persistence, full runtime call resolution,
and human acceptance of inferred component names are outside this slice.

## Acceptance

1. Static facts come from real Python files without executing target code.
   Architecture interpretation is supplied by the host agent with current
   snapshot/evidence binding; manual grouping is not required by the normal flow.
   Scope limits and unknowns must not be reported as full compliance.
2. The four lifecycle paths above lead eligible tasks through start before first
   edit and delivery before accepting evidence. Checkpoint requirements must be
   discoverable at their actual entry points. Missing/stale/wrong-task or wrong-
   stage evidence cannot be silently accepted as an architecture check. Identify
   any reliance on agent instructions rather than deterministic enforcement;
   do not claim raw task-state commands automatically invoke a model.
3. A task's start baseline and delivery results survive the executor checkout's
   removal when stored as instructed. Retries preserve prior evidence. Test the
   finite cases: normal roundtrip, retry, interrupted/partial write, task mismatch,
   checkout mismatch, scan-setting change, stale analysis/review, stale source,
   target edit/deletion, baseline/receipt change, absent start evidence, and
   source/coverage change outside a checked rule. No post-edit scan masquerades
   as a pre-edit baseline. Delivery uses the recorded start, not replacement rules.
4. Existing blind spots are reported briefly; definite or semantic drift, new
   blind spots, and requested/actual target changes produce an attention result
   with inspectable target/source evidence. The user controls target revisions.
   Normal results do not cause a report to open. No scheduler is introduced.
5. The saved report and receipt refer to the same code, target, interpretation,
   baseline and comparison. Freshness verification must not publish a false
   success for any case in criterion 3. Local corruption fails intelligibly.
6. Tests exercise meaningful failure cases and real-code validation remains
   explicitly scoped. Changed commands fit Perry's surface, stdlib, pack and
   release contracts. Integration must test the actual combined main tree and
   satisfy release checks before merging; no push or publication is authorized.

Report concrete, reproducible correctness or integration findings with priority,
criterion, file/line and minimal reproduction. Cosmetic preferences alone are not
merge blockers. Re-review fixes against the same criteria and affected invariants.
