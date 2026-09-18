# Perry token-efficiency iteration

Date: 2026-09-18. Owner: PMO Agent. Scope: plan and P0 task registration; implementation has not started.

## Authorization and outcome

The user requested a detailed iteration plan and P0 tasks based on the preceding token audit. All six work packages are P0 for this explicitly requested iteration; this does not rewrite phase 004 or its KR targets. Planning authorization is not a release, architecture sign-off, or permission to weaken any gate.

Outcome: reduce unnecessary model input and orchestration while preserving task correctness, recovery, ownership and independent verification. Task status, dependencies and verification live in the task store; this document owns scope and iteration acceptance, not a second progress board.

## Evidence and limits

The preceding audit sampled one Claude main-session transcript, bcc8bb26-9e88-4097-95fb-951ab3eeeda7: 114 distinct message usage records, 19,280,614 cached input tokens, 219,005 cache-creation tokens, 246 ordinary input tokens, 79,554 output tokens, mean context 171,051 and peak 267,041. The snapshot is historical, excludes child-session totals and includes cross-project activity. It is neither the current Codex session nor a complete Perry bill. Cached token volume is not monetary cost or subscription quota consumption.

Audit-time file sizes were 20,447 bytes for the router, 36,798 for work/SKILL.md and 49,922 for dispatch.md. Freeze a new commit-based baseline before implementation: main has advanced since that audit. Historical 52% tool-input / 26% result ratios are sample-specific, not defaults.

## Existing work to reuse

- TASK-456: reference tier budgets and section-preserving splits; currently review at inspection. Preserve its evidence and reviewer ownership.
- TASK-457: five static context bills, built on those splits; currently review at inspection. Reuse its existing perry-context-budget extension rather than build another CLI.
- TASK-309: interrupted executor work preservation. Session handoff work must inspect this row before implementation and avoid duplicating its checkpoint scope.
- Locked DESIGN-017 section 5.4 governs byte budgets, exact references and static bills. Static bills explicitly do not measure all dynamic reads. Its decision 6 defers a general behavioral-evaluation framework; this iteration uses bounded manual acceptance cases, not a new framework.

## Work packages and order

1. Session-bound usage measurement and frozen baseline. Establish reliable host/session identity, separate usage categories and expose uncertainty.
2. Intent-specific startup. Separate explanation, bounded state query and mutation paths, preserving recovery order before state access.
3. Minimal runtime instructions and bounded load sets. Reuse TASK-456/TASK-457, then reduce actual loaded material rather than merely split files.
4. Task-boundary budget checks and resumable handoffs. Bind checks to the measured session, and rotate only at safe boundaries.
5. Bounded execution and review loops. Reduce repeated reads, polling, copied shell programs and repeated review context without weakening validation.
6. Comparable before/after acceptance and independent review. Include child usage and failed/retried work; report quality alongside savings.

Dependency order: measurement precedes startup, handoff and execution optimization; startup plus accepted TASK-456/TASK-457 precede prose optimization; all five packages precede final comparison. Do not dispatch dependent rows early. Work touching the same skill/reference file is serialized. Start with measurement, then startup; schedule prose after the existing deliveries are accepted. These are delivery waves, not calendar promises.

## Acceptance targets

These are iteration targets, not achieved results or changes to existing KR metrics.

- Identity: no cross-session or cross-host false attribution in negative fixtures. Missing/ambiguous telemetry is unknown, never zero or a clean budget verdict.
- Quality: all bounded acceptance scenarios meet their written outcomes. No bypass of recovery, interrupted-run choice, permissions, file ownership, task evidence, V4 independence or V5 sign-off.
- Static load: router <=12 KiB; each lane <=24 KiB; all existing tier caps also hold. At least 30% lower unique declared bytes for add-task, close-task and dispatch versus the pinned pre-iteration baseline, with conditional reads stated separately. Do not tighten a locked cap without its normal decision process; these stricter figures are iteration delivery targets.
- Runtime: for comparable status-query, small-change and full-delivery cases, target >=30% lower median total input per successful case including cache and children. No class may regress by >10% without an explicitly recorded exception; an unexplained regression fails acceptance. Explanation-only cases must avoid project-state reads. Tool/model round reduction target is >=20% in aggregate, subordinate to quality.
- Coverage: five static bill routes from DESIGN-017, plus explanation-only and the runtime scenarios below. Report bytes separately from measured tokens; do not sum both.
- If telemetry is unavailable, mark the runtime result unmeasured and keep runtime acceptance open. Never substitute a byte estimate for measured savings or estimate account quota savings.

## Comparison protocol

Before editing, capture commit, host/model/reasoning settings where available, session and parent IDs, cache condition, tool capabilities, fixture state and task acceptance criteria. Capture a fresh baseline rather than treat the single sampled transcript as a controlled experiment.

Use three matched before/after runs per runtime class (nine pairs total) on disposable fixtures: (a) bounded status query, (b) small scoped fix with targeted validation, (c) end-to-end delivery including independent review and the required integration verification. Same request, task difficulty, model settings and tools within each pair. Include unsuccessful attempts in costs and separately report completion rate, retries, review rounds, wall time, peak context and child coverage. Report medians and ranges; nine pairs are an acceptance sample, not a population-level causal claim.

Safety scenarios: blocking recovery, interrupted pipeline, missing session ID, two concurrent sessions, a newer unrelated Claude transcript during a Codex run, a mutation request, changed source after a handoff, and a changed review base. Deterministic adapters use meaningful fixtures and revert proofs; semantic routing and review scope are assessed by agents against written criteria, not regex or keyword classifiers.

Separate a cheap deterministic preflight from the final live comparison. Do not purchase API access or run an open-ended benchmark. Existing account-backed runs remain bounded by the protocol and session budget; stop and retain evidence when access or budget is unavailable.

## Delivery and review contract

Each work package has one owner, files in scope, explicit exclusions and falsifiable acceptance in its spec. Default dispatch mode is manual: this request registers work and does not start agents. Product implementations use isolated worktrees, scoped commits and targeted checks while iterating. Before integration, follow release/README.md, run the required merged-candidate gates including bash tests/run and git diff --check, and obtain fresh-context V4 against the written criteria. Implementers cannot self-award V4/V5 or merge their own work.

The phase rule net Python/test lines <=0 still applies; simplify relevant code, never delete meaningful checks or compress unreadably to satisfy it. If an adapter cannot meet the bound, record the exact conflict and seek a separate decision before implementation. No new dependency, model purchase, scheduler, claim path, task backend, automatic host conversation reset or general evaluation framework.

## Rollout, failure and rollback

Land measurement first without changing workflow behavior; verify identity failures before enabling advice. Introduce entry routing next, then prose and handoff/execution changes in separate reviewable deliveries. Preserve old command contracts or document deliberate compatibility handling. Each delivery records exact base/head and its reversal procedure. Regression rollback uses the normal reviewed change process and preserves task/evidence history; it is not a history rewrite.

At two unsuccessful review rounds, stop expanding scope: summarize unresolved acceptance failures and the concrete decision needed. New unrelated findings stay in evidence for later triage. The final report must identify remaining costs from host-injected instructions, tools, memory, model reasoning and non-Perry work which Perry cannot independently remove.

## Task registry

The registered task IDs and planned dependencies are listed below. See the task store for live status.

Authorization: USER-967; explicit unlinked attribution: USER-968.

| Task | Package | Depends on | Spec |
|---|---|---|---|
| TASK-468 | Token efficiency — bind usage measurement to the actual host and session | TASK-457 | [TASK-468-spec.md](TASK-468-spec.md) |
| TASK-469 | Token efficiency — route explanations, state queries and mutations through bounded startup | TASK-468 | [TASK-469-spec.md](TASK-469-spec.md) |
| TASK-470 | Token efficiency — shrink runtime instructions and actual per-command load sets | TASK-469, TASK-456, TASK-457 | [TASK-470-spec.md](TASK-470-spec.md) |
| TASK-471 | Token efficiency — enforce session budgets at safe task boundaries | TASK-468 | [TASK-471-spec.md](TASK-471-spec.md) |
| TASK-472 | Token efficiency — bound tool output and repeated review work | TASK-468 | [TASK-472-spec.md](TASK-472-spec.md) |
| TASK-473 | Token efficiency — verify end-to-end savings without losing correctness | TASK-468, TASK-469, TASK-470, TASK-471, TASK-472 | [TASK-473-spec.md](TASK-473-spec.md) |

Implementation scheduling starts with acceptance of the existing TASK-457 context-bill delivery, which depends in practice on TASK-456 splits. The new measurement task declares TASK-457 explicitly so two owners do not edit the same tool concurrently. Do not interpret P0 as overriding dependency or review gates.
