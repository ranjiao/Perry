# Autonomous delivery review criteria

Written before independent review, 2026-09-17. This restates the existing TASK-413/423/427 summaries and implementation bounds without expanding them.

## Bound

Two immutable deliveries based on edf6b143a1b6cf8de3f2d84c53bc5e5d9cebf41e: 8972f759 (TASK-413/427, three changed files) and 05ad0f3b (TASK-423, six changed files). Review only the changed behavior and tests, not a repository-wide cleanup. No merge or publication in this round.

## TASK-413

1. Independent fixture: four open and two terminal tasks; bound.open_total and closed_total reflect the selected population before truncation for --all limits 1, 3, 0 and open-only limit 1.
2. Window counts and truncation stderr agree with that fixture.
3. Mutating open_total to total is caught by this regression test; restoring it is green. No product counting change in this task.

## TASK-427

1. Unknown flags return exit 2 without changing fixture bytes; legal flag suggestions use existing SURFACE or scan_argv declarations.
2. Known subcommand suggestions exclude flags belonging only to another subcommand; --help and -h remain offered. Before a subcommand is selected, the tool-wide set is labelled as declared rather than falsely scoped.
3. Existing valid invocations and refusal gates remain intact. Bound: parse_surface and scan_argv changes, four CLI regression cases and added synthetic surface tests.

## TASK-423

1. perry list, perry-detect-host, perry-explain reject an undeclared --xyzzy with exit 2, name the token, and print no normal answer.
2. perry-goals krs rejects a stray positional with exit 2 at phase and overall levels, in text and JSON modes; JSON remains a refused object.
3. Host --help --xyzzy refuses rather than hiding the bad token. Valid documented calls remain supported, and the twenty-executable unknown-flag sweep has no exceptions.

## Architecture

Independently check full ARCHITECTURE.md against both diffs: no forbidden dependency or state ownership, no prose interpretation, existing exit-code contract respected, tests write only to temporary fixtures. Read work/reference/review-constraints.md. Run affected tier on each immutable candidate against the pinned base, plus independent targeted probes/mutation. Report checked and not-checked explicitly; do not claim combined-state verification.
