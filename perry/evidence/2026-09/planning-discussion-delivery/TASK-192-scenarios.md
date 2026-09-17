# TASK-192 hypothetical walkthroughs — NOT real human transcripts

These are authored scenario inputs and actual proposed responses written by the
implementing agent. They are semantic walkthroughs for independent review, not
executed interviews, model-behavior tests, TASK-191 evidence or V4/V5 acceptance.
Each quoted agent turn ends at its question; the next input is a separate
hypothetical turn. No project state is written.

## A. Rich context, first OKR (criteria 1, 2, 4, 5)

Declared fixture: project track, confirmed no OKR. Opening user input:
“Call it Harbor. By November 30, help volunteer coordinators fill shifts reliably.
One objective: coordinators can fill shifts without chasing people. At our last
review 6 of 10 shifts were filled without chasing, from the August rota. Aim for
8 of the next 10 by November 30; treat it as commit. No paid acquisition. Capacity
is two hours a week. No other lasting principles yet.”

Actual proposed agent response (0/8 interview questions):
> First OKR draft — not finalized. From your opening: mission is helping
> volunteer coordinators fill shifts reliably by November 30; Objective is
> “coordinators can fill shifts without chasing people.” KR: 6/10 → 8/10 shifts
> filled without chasing, measured on the rota by November 30, commit as you
> specified. Anti-goal: no paid acquisition. Capacity: two hours/week. No lasting
> principles declared. The baseline is your report of the August rota; I have
> not independently measured it. This scorecard measures less chasing, not
> recruitment growth. There are no unanswered interview fields to repeat.

Draft consequences: reuse all explicit answers with opening/rota provenance;
Harbor's name has no routing significance. No zero baseline and no new objective,
new consent or phase. Approval/premise handling is exercised in TASK-193.

## B. Existing OKR revision (criteria 1–5)

Fixture accepted OKR v2: mission “help coordinators fill shifts”; O1 “Reduce the
need to chase”; KR1 6/10 → 8/10 by November 30, commit; KR2 “retain 4 returning
volunteers by November 30,” baseline 2, commit. User input:
“Revise KR1 to cover cancellations only. Keep KR2 and the mission exactly as they
are. We have no cancellation baseline. Keep November 30.”

Actual proposed agent response (Q1/5, Q3 → KR1 evidence):
> You are narrowing KR1 to cancellations, while keeping the mission, KR2 and
> deadline. The old all-shift 8/10 threshold no longer follows; I withdraw it
> from the proposed KR1. I suggest measuring cancelled shifts filled without
> chasing: that would test recovery when a shift falls through, though its
> baseline and target remain unknown. Should we use that outcome (Recommended),
> or describe the cancellation outcome differently?

Draft consequences: accepted v2 mission/KR2 carried verbatim with source; reason
and before/after KR1 shown. No question repeats deadline or beneficiary. An old
commit label does not approve a new threshold. No version append or phase action.

## C. Conflicting old/new beneficiary and capacity (criteria 2, 3, 5; TASK-466)

Fixture: v2 above. Prior agent proposal was “monthly organizer retention 80%,”
explicitly rejected by user. New user input:
“I meant the volunteers, not coordinators. I want volunteers to know where to
show up. I only have 30 minutes a week now. Do not bring retention back.”

Actual proposed agent response (Q2/5, Q2 → Objective, dependent KRs):
> Your correction changes the beneficiary to volunteers and the outcome to
> knowing where to show up; capacity is now 30 minutes/week. I keep v2 as the old
> source and your correction as current draft intent. Coordinator chasing and
> retention no longer demonstrate this outcome, so I withdraw those proposals;
> retention remains explicitly rejected. I suggest “Volunteers can find their
> next shift's location without asking”: this tests the stated confusion,
> without assuming a feasible target from the reduced time. Is that the outcome
> you mean, or would you phrase it differently?

Draft consequences: Mission/Objective and dependent KR metric, threshold and
commitment labels reopened; capacity changed, feasibility unknown. No automatic
halving of a target, no renamed retention metric. Clear correction applied without
asking user to repeat whether they meant volunteers.

## D. Queue commitment (criteria 1, 2, 4, 5)

Fixture: selected queue track `support`, declared SLA 3d, cycle weekly; existing
commitment support/1 promises acknowledgement to requesters. Arrival rate unknown.
User input: “Draft a new promise to Finance: reconciliation questions resolved
within our existing 3d SLA. Resolved means Finance confirms the answer. Don't
change the acknowledgement promise.”

Actual proposed agent response (0/3 interview questions):
> Commitment draft — not written: support / “Reconciliation questions resolved,
> confirmed by Finance” / To Finance / Due 3d / note “within the track SLA.”
> The terms and resolution evidence come from your message; 3d is also the
> declared support SLA. This would promise a confirmed resolution within 3d,
> which is stronger than acknowledgement. support/1 stays unchanged. Arrival
> rate is unknown; the SLA does not prove capacity. Your request was to draft,
> so it has not authorized a new active promise.

Hypothetical next user input: “Approve that exact new promise; create it.”
Actual proposed agent response (writer handoff, no invented finalize command):
> You approved the new Finance promise on support with Due 3d. I can submit
> those exact terms through the existing commitment writer. If it refuses, I
> will return that refusal without editing the register by hand.

Reviewable proposed command (NOT executed against any project):
`bin/perry-goals commit --actor goals --root <fixture> --track support --promise 'Reconciliation questions resolved, confirmed by Finance' --to Finance --due 3d --by-when-note 'within the track SLA'`

Draft consequences: no objectives/phase/track-policy write; unknown arrival rate
is context, not an invented writer flag. When party or Due is missing, Q10 asks
one consequential term at a time within three questions, then drafts unknowns
and stops before writing. Explicit create authorization is distinguishable from
approval of an old SLA or an edit to this draft.
