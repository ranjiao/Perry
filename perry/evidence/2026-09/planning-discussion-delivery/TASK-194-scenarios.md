# TASK-194 hypothetical walkthroughs — NOT real human transcripts

Authored scenario inputs and actual proposed responses, not real interview
records, automated proof of model behavior, TASK-191 acceptance or V4/V5 review.
All paths/IDs below are fictional fixtures unless explicitly called delivery
artifacts. No phase, task, ask, journal or canonical goal record was written.

## A. First phase reuses approved overall context

Criteria: 1–4. Fixture: project track; approved OKR v1 Mission “Help volunteers
find their shifts”; O1 “Volunteers can prepare without coordinator help”; overall
Anti-Goal “No paid tools”; principle “Keep shift details private”; no active phase.
User: “Plan our first phase: focus on finding the shift location. Exclude reminders.
I can observe four volunteers for one session. Don't assume a spending budget.”

Actual proposed agent response (Q1/5, shared Q3 → KR/DoD):
> I reuse v1's mission, no-paid-tools boundary and privacy rule. This phase would
> test finding the shift location; reminders are excluded by your message.
> I suggest observing whether each of the four volunteers can find the location
> without coordinator help: that would show whether this slice advances v1's
> preparation goal. Baseline and success threshold are unknown. Should that be
> our evidence (Recommended), or do you want a different observation?

User: “Yes. Must-Have: at least three of those four find it unaided by phase end.
One observation session only. If arranging it stalls by phase day 7, reduce to
two volunteers, success threshold to be decided then.”

Actual proposed agent response (visible draft, 1/5 interview questions):
> Phase draft — not active. Focus: find shift locations; reminders excluded.
> Rules: privacy and no paid tools, sourced from OKR v1.
> Cost: budget and wiring unknown; I have not turned “no paid tools” into $0 spend.
> User contribution: one session with four volunteers, from your message; no USER-id.
> Degradation: independent work/task IDs unknown; no autonomous fallback asserted.
> Reduction: at phase day 7, stalled observation → two volunteers; new target undecided.
> Objective: volunteers can find their shift location without help, serving v1 O1.
> Proposed KR/DoD: at least 3/4 unaided by phase end; baseline unknown; Must-Have.
> Not Doing: reminders and repeated observation sessions. Process: cadence stays with work.
> Start date, final phase number and approval remain unset. No phase was created.

Draft consequences: ten sections appear; unknown budget, wiring and baseline
are not invented. Four-person evidence is user-supplied capacity, not a guaranteed
baseline. A reduction rule with an undecided replacement target remains visible
as incomplete. See the expanded first-phase draft below for reviewer inspection.

## B. Subsequent phase uses prior learning; scope/capacity correction changes targets

Criteria: 1, 2, 3, 5; inherited TASK-466.
Fixture: same approved overall v1, latest phase 001 scored, no active phase.
Retro says 3/4 found the correct location; one stale address caused failure. It
proposes reminders as future work but does not approve them. User:
“Next phase should stop stale addresses causing missed shifts. I can do two
observations with four volunteers. Keep privacy and no paid tools.”

Actual proposed agent response (Q1/5, shared Q2/Q9 → Focus):
> Phase 001's retro reports 3/4 successful lookups and one stale address; that
> does not establish how often stale data occurs. I propose focusing this phase
> on volunteers reaching the current location after an address change. That
> tests the observed failure; the retro's reminder idea remains a proposal.
> Should this be the phase focus, or would you describe the desired end state
> differently?

User: “Use that. Propose four of four reaching the new location across two
observations as Must-Have, and reduce to one observation at phase day 7 if needed.”
Actual proposed agent response (Q2/5, shared Q4 → Not Doing):
> The current draft proposes 4/4 reaching the changed location across two
> observations as Must-Have. Phase-day 7 would reduce to one observation, so the
> evidence would cover fewer occasions. I suggest deferring reminders and general
> onboarding: that concentrates effort on the stale-address failure. Use those
> exclusions, edit them, or say it differently?

User: “Cut it further: only two volunteers and one observation. Threshold is
both of the two reaching the changed location. I have one hour total, not two
sessions. No reminders. Remove the day-7 reduction, since one observation is
already the minimum. Don't assume I will recruit anybody.”

Actual proposed agent response (visible draft; no automatic numerical scaling):
> You cut this phase to two volunteers in one observation, with your chosen
> threshold of both reaching the changed location. I replace the 4/4 and
> two-observation proposal with 2/2 in one observation; this tests one changed
> address occasion, not consistency across occasions. Capacity is one hour total.
> Recruitment is unknown, not your commitment. The day-7 rule is withdrawn;
> no replacement trigger is approved. Reminders remain rejected. Privacy and
> no paid tools still come from v1. Baseline for changed-address success is
> unknown; the prior 3/4 lookup result measured a different situation.
> Updated phase draft — not active: focus and Must-Have are the reduced test;
> KR deadline is phase end; commitment label, recruitment, spend and fallback
> trigger remain undecided. Drafting changed no phase records.

User: “Keep that draft as-is, including the unknowns; don't start it.”
Actual proposed agent response (premises + single advisory rubric, no writer):
> The premises are the stale-address failure from phase 001 and your narrower
> one-hour, two-volunteer observation. The draft carries no promise to recruit.
> Rubric once: baseline is missing (observe changed-address success first);
> scope reduction has no trigger (choose a supported phase-day/KR-progress
> fallback); budget/wiring is unknown (state a cap and its actual enforcement).
> Those gaps stay explicit under your as-is instruction. The draft remains
> unapproved for activation, exactly as you requested.

Draft consequences: user-specified 2/2 replaces 4/4, not an agent formula;
Must-Have, capacity, exclusion, contribution and trigger sections change together.
No reminder carry-over, invented recruitment, old-threshold reappearance or fresh
mission interview. Remaining gaps cannot be hidden by a complete-looking template.

## C. Approval with missing phase writer

Criteria: 4, 5. User input about B's current draft: “I approve this phase; start it.”
Actual proposed agent response:
> You approved the current reduced phase draft. I cannot activate it on this
> baseline: the phase persistence/finalize path belongs to TASK-444 and is not
> available. The commitment and link writers do not create a phase and its KRs.
> No phase document, phase/CURRENT or linkage records were written. The approved
> meaning remains in this chat draft; there is no saved-plan or activation receipt.

Actual read-only capability receipts: logs/goals-writer-surface.log and
logs/okr-writer-surface.log. These show the existing commands; no absent command
was invoked and no import/render fallback was attempted.

Variant: user says only “The overall OKR is approved.” Actual proposed response:
> Overall v1 is approved. That supplies context for phase planning; no phase
> proposal has been approved or started.

Variant: snapshot reports active phase 001. Actual proposed response:
> Phase 001 is active. Starting another would require a separate lifecycle
> decision. Should we discuss changes to that phase, or review it for closing?

Each variant is a separate scenario; no lifecycle action is performed.

## Expanded first-phase draft from A — ten sections, NOT active state

Proposed slug: location; phase number/start: unassigned. Sources: accepted fixture
OKR v1 and the two hypothetical user inputs in A. No `phase/` file was created.

### Phase Focus
Volunteers can find their shift location; this is not about reminders. Advances
v1 O1's independent preparation. Ends on outcome/evidence, not a calendar date.

### Operating Rules
Keep shift details private; no paid tools (accepted overall v1).

### Cost Ceiling
Spend cap and soft-fallback threshold unknown. Wiring unknown. Observation
capacity is user-supplied; it does not establish a monetary budget.

### User Commitments
User offers one observation session with four volunteers. USER-id unknown; PMO
owns any later registration. Additional recruitment contribution not inferred.

### User-Unavailable Degradation
Independent tasks/dependencies unknown; no task IDs invented. If user input is
missing for more than five days, a continuation order still needs grounding.

### Phase Scope Reduction Rule
User's proposed phase-day trigger: at day 7, if arranging the observation has
stalled, reduce to two volunteers. Replacement success threshold undecided.
The draft marks this incomplete; it is not an armed automatic rule.

### Objectives
Proposed O1: volunteers can find their shift location without help.
Discussion-only candidate KR: at least 3 of 4 observed volunteers find it unaided
by phase end; baseline unknown; Must-Have requested, commit label proposed.
Canonical KR `id`, `linked` and final phase ID await the supported writer and
stable-ID resolution; no IDs or graph records are fabricated. The canonical
phase document would point to linkage.jsonl, without duplicating the KR table.
Project seed: location observation; owner/verifier/task ID unknown; no task created.

### Definition of Done
Must-Have: user-chosen 3/4 unaided location lookup, observed in one session, tied
to the proposed KR. Baseline remains missing; a test/evidence artifact location
is still unknown. Nice-to-Have: none supplied.

### Not Doing in this phase
Reminders and repeated observation sessions (user inputs); no paid tools remains
the broader overall boundary, not the only phase exclusion.

### Process Note
Cadence belongs to work. No weekly plan, task or journal is generated by this draft.
