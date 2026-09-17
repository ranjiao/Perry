# TASK-446 — one-screen combined snapshot

Date: 2026-09-17. Owner: Coding Agent. Priority: P2. Required verification: V4.
> Touches architecture: existing agent-rendered snapshot procedure only.
> Dispatch mode: auto
> Executor: codex
> Subjective verification: fresh reviewer checks bounded rendered examples against captured tool facts
> Deployed: no

Authorization: USER-957; current phase 004 Objective 3 and its snapshot deliverable. Current task contract says startable with no blockers. Decision-card format belongs to TASK-445 and is not changed here.

## Deliverable

Measure today's combined `/perry` rendering on this repository and reshape the existing snapshot instructions to keep the initial screen within 12 lines and 1,200 Unicode characters, with detail one level down. The agent authors the rendering; Python only counts deterministic bytes/characters/lines and validates supplied fields.

## Acceptance criteria

1. Retain a before-rendering of the existing procedure grounded in a fresh perry-state compact/next capture, and measure it. Retain the same facts in a new initial rendering of at most 12 visible lines and 1,200 Unicode characters (all visible text, whitespace, links and the next block count; wrapping depends on UI width and is not claimed controlled).
2. Initial screen communicates project/current phase position, unknown progress honestly, open/blocked task counts, pending user decisions, and the selector's primary recommendation; at most two returned alternates and unknown causes remain accessible one level down with an explicit pointer. Do not invent, reorder or replace selector recommendations. Details preserve every returned alternate/unknown and titled IDs. Do not fabricate measured KR progress from task counts.
3. Keep startup recovery/interrupted gates, no automatic resume, source provenance, active-pack glossary, and lane routing unchanged. Only rendering/detail placement may change. If a safety/recovery interruption blocks startup, show it instead of pretending a normal dashboard. Retain user choice/autonomy already granted rather than demanding a new question during ongoing authorized work.
4. Four bounded agent-authored examples (normal, many objectives/long titles/many pending items, unknown/absent measures, blocking recovery/interrupted state) demonstrate the budget and honest detail routing; use captured tool output or explicitly synthetic typed fixtures. Fresh reviewer rejects omitted pending-decision/unknown facts and oversized rendering mutations. Existing targeted pointer/contract tests, smoke, committed affected tier pass. Structural tests need not pretend to understand prose.

## Files in scope

reference/snapshot.md rendering procedure; reference/next.md rendering cross-reference only if needed to avoid contradictory full-render requirement; an existing snapshot/route/pointer instruction guard only if an intentional lexical contract changes. External scratch: tool captures, before/after examples, deterministic measurement receipt. No new product renderer, command, schema, store or semantic classifier.

## Bound

One initial snapshot and one detail level; four fixtures. Net Python/test lines <=0; retain meaningful coverage. No task/ask/goal changes, no decided architecture changes, no claims about a different screen width. Do not overwrite the separate TASK-455 dispatch/review changes or TASK-447 linter changes.

## Verification

Exact base/head, measured live before/after plus all four fixtures, targeted pointers and affected selection. Independent V4 checks source fidelity and negative semantic cases. Canonical PERRY_HOME; unset PERRY_PROJECT; isolated TMPDIR; at most four workers. No duplicated full/slow: integrator owns merged gates.

## Out of scope

User decision card design, goal declarations/scoring, suppressing information to claim the budget, operational startup gate changes, foreign writes, publication and main integration.
