# The next step is a skill procedure

Authority: ADR-024 and DESIGN-023 decision 5. The agent applies the table below
top to bottom, using the native capture in `reference/snapshot.md`. The first
matching row supplies the primary suggestion. Show the facts and IDs behind
it. This procedure runs no evaluator, changes no state and dispatches nothing.
An explicit user request takes priority. Unknown facts cannot satisfy a row.

| Order | Evidence | Suggestion |
|---|---|---|
| 1 | recovery hazard, malformed config/store or failed native query | repair the named path/error before other work |
| 2 | nonterminal adoption/diagnosis/plan restore point | offer resume/archive/abandon; wait for the user's choice |
| 3 | a requested action is already authorized | continue that action through its owning lane |
| 4 | a task in review requires independent review or human acceptance | review the criteria/evidence or present the concrete sign-off artifact |
| 5 | a named design is locked with an unexecuted work handoff | decide hands its agreed scope to work |
| 6 | nonterminal asks block otherwise ready work | surface the question with its blocked task and the recorded age, if known |
| 7 | a phase KR is unmeasured, has a failed/obsolete check or has no declared check | goals declares/repairs/runs the check; an obsolete measurement cannot close the phase |
| 8 | all committed phase KRs are measured and met, with a native event/attachment proving its retro | propose goals phase scoring, after the lane's approval gate |
| 9 | all committed phase KRs are measured and met, with no recorded retro | work proposes the end-phase retrospective before goals scoring |
| 10 | no current objective or phase in an applied goals template | goals proposes goals/phase planning, with the user's scope |
| 11 | a startable task has written criteria and its priority outranks other startable tasks | propose it by title; never silently start it |
| 12 | a declared open high risk | surface it and propose work risk review |
| 13 | none of the above has sufficient facts | say no supported next step was found and list the relevant unknowns |

Equal-priority tasks use stable ID order for presentation; the user can choose.
The task's `blocked_by`/`startable` is authoritative. A review item's existence
is not a passing verdict, and a passing verdict is not human acceptance. Never
fabricate a human actor, reviewer freshness or a numerical measurement.

For a phase-close suggestion inspect the complete KR set and the native metric
and rollup results. Missing children, withdrawn/ambiguous membership, stale
measurements or missing retrospective evidence prevent claiming closability.
Do not infer that a retro exists merely because a file has that name. If the
process template has no metadata for a decision, report the missing fact.

Weekly review age, SLA, WIP, due commitments and architecture-review age are
unknown unless a native item/event explicitly records the required facts.
The removed rules table cannot fill these gaps. A lane may offer its named
procedure on request without claiming that an unknown threshold was crossed.

## Closing step

After an approved write, re-query the affected items and relevant relations.
State what changed, the verification boundary and one supported next action.
Honor a user's silence preference. A suggestion is never approval to execute.
For read-only help and narrow queries, answer the request without an extra
planning question. When a procedure cannot yet be represented by the applied
template, report the gap instead of recreating a legacy register.

The lane indexes are the finite routing checklist: each indexed command either
appears in the table's owning-lane procedure or is explicitly invoked by the
user. Help, status, dashboards and read-only inspection are never autonomous
writes. New commands require updating their lane index and this checklist in
the same change; no deterministic recommendation code belongs in the kernel.
