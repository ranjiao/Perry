# TASK-468 — Token efficiency — bind usage measurement to the actual host and session

Date: 2026-09-18. Owner: Coding Agent. Priority: P0. Required verification: V4.
> Dispatch mode: manual
> Executor: manual
> Estimated cycle: medium
> Subjective verification: independent reviewer checks all written acceptance criteria and retained safety behavior
> Touches architecture: §3, §6; preserve existing boundaries and select touched module documents at dispatch
> Deployed: no

## Authorization and rationale

USER-967 authorizes the iteration plan and P0 task registration. USER-968 explicitly chooses unlinked attribution and independent iteration acceptance. The current budget reader can select another Claude session while Perry runs in Codex. Bind readings to verified session identity and freeze comparable usage baselines so optimization is measured against the right work.

Priority is P0 because this is a required package in the user-requested token-efficiency iteration, not an assertion that phase 004 KR targets have changed. Planning is complete when this spec and task record exist; implementation is not started or authorized for automatic dispatch by this spec.

## Deliverable

Session-bound usage mode in the existing context tool, explicit uncertainty and provenance, host fixtures and a frozen pre-change baseline.

## Files in scope

bin/perry-context-budget; tests/test_context_budget.py; reference/host-capabilities.md; relevant bin/README.md usage; task evidence. Reuse TASK-457 after acceptance.

## Acceptance criteria

1. Accept an explicit session source or a verified host-provided identity. No implicit newest-file selection may produce a current-session budget verdict. Historical explicit-session inspection must be labelled historical.

2. Cover Claude and Codex fixtures, concurrent sessions, cwd/worktree mismatches, newer unrelated transcripts, absent identity, missing usage and malformed/truncated records. OpenCode unsupported telemetry reports unknown with a reason, not a fabricated zero.

3. Preserve input, cached input, cache creation, output and reasoning categories according to each host schema; document inclusion rules and avoid double-counting reasoning already included in output. Deduplicate repeated records and use deltas for cumulative counters.

4. Report host/session/parent identity, source path, time/freshness, coverage and measured versus estimated fields. Missing child usage yields partial coverage; a partial report cannot claim total cost. Keep monetary and quota conclusions unknown without an authoritative conversion.

5. Capture the frozen baseline specified in the plan before workflow edits, including commit and host/model settings. Retain the five static bill contracts from TASK-457.

6. Negative fixtures fail when session binding is reverted; existing context and static-bill tests remain green. Respect net Python/test lines <=0; if infeasible, record the conflict before broadening scope.

## Dependencies

TASK-457. Typed dependency truth lives in perry-task list --json. Wait for accepted delivery and evidence, not merely an implementation branch. Resolve overlapping active work before editing.

## Verification

Host and usage-schema fixtures plus reverted identity-fix failure; legacy context/static-bill tests; pinned baseline receipt; fresh V4.

Before implementation freeze base/head and actual relevant commands; use targeted tests, meaningful revert/negative proof and fresh-context V4. Required integration gates and release handling remain in force. This planning session awards no verification rung.

## Bound

Two measured host adapters (Claude and Codex), one explicit unsupported-host outcome, the seven identity/error fixture categories in criterion 2, and the existing five static bills. No additional host adapters.

Read perry/evidence/2026-09/2026-09-18-token-efficiency-iteration-plan.md for shared protocol and targets. Current phase net Python/test lines <=0 and stdlib-only constraints remain binding. Missing telemetry is unknown. If a target requires changing locked architecture, expanding a claim, relaxing a phase constraint or weakening a gate, stop that implementation and record the exact decision needed. Never delete tests or hide failed runs to meet cost targets.

## Out of scope

No phase/KR edits, new dependencies, claim-surface changes, paid API purchases, external publication, automatic implementation dispatch, self-review or self-merge. No implementation of the other five work packages. No new progress register.

## KR linkage

unlinked — explicit user decision USER-968. Independent iteration targets are in the plan; no KR progress is asserted.
