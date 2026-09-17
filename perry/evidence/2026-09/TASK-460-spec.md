# TASK-460 — Next-step KR progress uses declared checks

Date: 2026-09-17. Owner: Coding Agent. Priority: P1. Required verification: V4.
> Touches architecture: perry-state consumer of typed KR position, DESIGN-022 C.

> Dispatch mode: auto
> Executor: codex
> Subjective verification: independent review against this written scope
> Deployed: no

Authorization: USER-957, continuing phase 004 under its approved autonomy. No push, publication, foreign project write, or architectural decision edit.

## Deliverable

Replace next_kr_progress's current/target heuristic with the typed state/met position already derived by TASK-416. Preserve one derivation function; consume the existing payload. No metric prose parsing or second direction comparison implementation.

## Acceptance criteria

1. Declared at_most/decrease ceiling at 400 with measured value 1702 is not met; at or below the ceiling is met. Existing at_least/increase and done declarations follow the shared derivation.
2. Undeclared, unmeasured, due and measured KRs are counted consistently with DESIGN-022 5.2's shared derivation. A KR missing any required check measurement cannot make the phase closable. Stretch KRs are excluded. Legacy numeric target/current alone cannot invent direction or met.
3. Multiple checks require all to be met; mixed/unmeasured checks keep met unknown. No phase/invalid linkage continues to fail closed without crash.
4. R-phase-closable and measurement counts are demonstrated for three fixtures: zero measured, half measured, all met. Reverting the change makes the ceiling regression fail. Existing next-step rule contracts remain stable.

## Files in scope

bin/perry-state next_kr_progress, adjacent next_facts unknown explanation, and existing encode_linkage_objective/payload construction needed to attach lib.kr_checks/lib.kr_position output using already loaded linkage records/events; existing tests/test_next_section.py and, only if needed, existing typed KR integration fixture modules. Shared bin/lib position derivation is already implemented and should be reused rather than changed. No schema, registry, live KR, goals writer, or next-rule threshold changes.

## Bound

The current-phase commit KR aggregation consumed by next_facts and R-phase-closable; the 5 existing typed directions, four typed states, stretch exclusion, multi-check completeness, phase/linkage absence. No overall scoring, new derived values or hidden measurement writes.

## Verification

Pin base before implementation. Run affected tier and independent typed-payload/end-to-end fixtures; retain a reverting-fix failure. Set PERRY_HOME to candidate and unset PERRY_PROJECT. Avoid unnecessary parallel suite repetitions; -j 4. Tests never touch live stores.

## Out of scope

KR revisions/withdrawals (USER-952), due-check recommendation TASK-461, phase KR measurement writes, human scoring, publication and main integration. Coding agent commits code/tests to its feature branch and returns SHA, exact checks and architecture compliance.

## Scope clarification after dependency probe

The first dispatch produced no product changes. Its blocker report established the missing existing-consumer wiring. This clarification authorizes that wiring under USER-957 and, for the architecture declaration, USER-933; it does not revise a locked decision. Retain the original failing probes as evidence. Do not invoke `tests/run --help`: it starts the default suite. Read runner source for syntax. Run smoke plus `python3 tests/parallel --tier affected --base 7ffcc6337bc5c8b31d2e8992c251e23299bff1ea -j 4` sequentially and report the selection. Net Python/test lines must be <=0 without deleting meaningful coverage or compressing statements just to meet the count.
