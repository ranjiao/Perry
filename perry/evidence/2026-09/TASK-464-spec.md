# TASK-464 — Pack capability discovery and project configuration

Date: 2026-09-17. Owner: Coding Agent. Priority: P1. Verification: V3 plus independent scenario review.
> Dispatch mode: manual
> Executor: codex
> Estimated cycle: medium
> Subjective verification: independent conversational scenario review
> Touches architecture: root sections 2, 3 and 5; existing config and lane ownership
> Deployed: no

User approved the deduplication and task adjustments in chat. This spec records
work to do, not implementation or permission to change locked architecture.
KR attribution: explicitly unlinked pending a fitting approved KR; neither
O2-KR3 nor P004-O2-KR3 is expanded by this task.

## Deliverable

A user-facing capability discovery and control procedure backed by the existing
Packs configuration and loader. Explain purpose, current effective selection,
default versus explicit configuration and effects before changes. Distinguish
available pack, active pack and capability configured with a ready adapter.

## Acceptance criteria

1. A user can discover available and active packs and their effects without
   knowing the pack terminology or file layout in advance.
2. Explicit project-scoped enable/disable uses the existing writer. Verify and
   document absence/default versus explicit empty/disabled semantics first;
   never silently treat a requested disable as restoration of the default.
3. Disabled software-ops removes its optional routing and gates consistently
   across goals/work/discovery. Existing user-approved project requirements and
   safety rules are not silently erased. Explain concrete conflicts before changes.
4. Disabling/re-enabling preserves existing artifacts and policies. Missing or
   unknown configured packs are reported honestly rather than claimed active.
5. software-ops activation alone does not enable version allocation. Release
   setup reuses TASK-463 policy/adapter readiness and existing conventions.
6. No repeated enablement questions during routine work. All behavior is shown
   through fixtures and independent user-intent scenarios, not phrase-count tests.

## Files in scope

Existing pack/config loader and writer only as needed; reference/config.md;
pack descriptions; conditional router/lane references; targeted tests and docs.
Identify exact implementation paths at dispatch after inspecting the existing
contracts. No new schema or architecture authority is granted by this scope.

## Dependencies

TASK-024 and TASK-025 delivered the underlying extraction/loader. TASK-463
supplies release guidance. This task does not redo those completed deliveries.

## Verification

Fixtures: default config, explicit selection, explicit disable, unknown pack,
re-enable preserving bytes, active pack with unconfigured version capability.
Independent scenarios: discover, explain, enable, disable with existing records.
Run relevant contracts and final merge checks before acceptance.

## Out of scope

Marketplace/install system, additional domain packs, release runtime adapters,
publication, KR edits and initialization orchestration (TASK-465).

## Bound

One bundled software-ops pack; existing configuration; discovery and lifecycle
controls plus their conditional consumers. No arbitrary plugin platform.
