# F1 corrected scenarios — hypothetical, NOT real human transcripts

Authored inputs and actual proposed agent responses for independent semantic
review. No live commitment commands are executed; these are not automated proof
of model behavior, TASK-191 evidence or an acceptance verdict.

## 1. Complete explicit terms: no repeated intake, existing writer authorization

Fixture: selected queue track support, declared SLA 3d. User:
“Create a new support commitment to Finance: reconciliation questions resolved
and confirmed by Finance, Due 3d, note ‘within the track SLA’.”

Proposed agent response (0/3 intake questions):
> Your instruction specifies the support track, Finance, the resolution promise
> and Due 3d, and explicitly asks to create it. I will use those exact terms with
> the existing commitment writer. This promises confirmed resolution within 3d;
> a writer refusal will stop the operation.

Reviewable proposed operation, NOT executed:
`bin/perry-goals commit --actor goals --root <fixture> --track support --promise 'Reconciliation questions resolved and confirmed by Finance' --to Finance --due 3d --by-when-note 'within the track SLA'`

Consequence: no question repeats party/Due and no extra consent is fabricated.
Authorization comes from this exact create instruction, not the declared SLA.
A request merely to draft the same complete terms would remain a draft.

## 2. Missing terms: one at a time; an answer is not create authorization

Same fixture. User: “Draft a support promise to resolve reconciliation questions.
I haven't chosen who it is to or how soon.”

Proposed agent response (Q1/3 → To whom):
> The draft promise is resolving reconciliation questions on support. The party
> and Due are unknown. Who should receive this promise?

[Stop and wait.]
User: “Finance.”
Proposed agent response (Q2/3 → Due):
> The party is Finance. The track's existing 3d SLA could be the draft's Due;
> using it would promise resolution, not just acknowledgement, within 3d.
> Should this draft use 3d, or a different deadline in your words?

[Stop and wait.]
User: “Leave Due unknown.”
Proposed agent response (no repeated Due question):
> Draft only: support / resolve reconciliation questions / to Finance / Due
> unknown by your choice. No commitment can be written while Due is unknown.
> Your answers edit the draft; they do not authorize creating an active promise.

Consequence: explicit Finance is reused, no date is inferred from policy, no
bundled party/clock question, no write or automatic consent.

## 3. Three questions exhausted: handoff cannot ask a fourth

Fixture: declared support queue (SLA 3d) and invoices queue (SLA 5d). User:
“Draft a reconciliation-resolution promise; I haven't picked the terms.”

Agent Q1/3: “Which declared track should carry the promise: support or invoices?”
[Wait.] User: “Support.”
Agent Q2/3: “The track is support. Who should receive this promise?”
[Wait.] User: “Finance.”
Agent Q3/3: “The party is Finance. Support's declared 3d SLA would promise
resolution within 3d. Should the draft use that, or a different deadline?”
[Wait.] User: “I don't know the deadline; draft now.”

Proposed agent response at the commitment handoff (no Q4):
> Draft — not written: support / reconciliation questions resolved / to Finance /
> Due unknown. Track and party come from your answers; the 3d track policy has
> not been accepted for this promise. The three intake questions are spent.
> Due remains required and unknown, so the writer cannot be called.

Complete-terms alternative to the final user answer:
“Use 3d. Create that exact support promise to Finance: reconciliation questions
resolved, Due 3d.”
Proposed agent response (still no Q4):
> You supplied Due 3d and explicitly authorized this exact create operation.
> I will submit the support reconciliation-resolution promise to Finance with
> Due 3d through the existing writer, subject to its refusals.

Consequence: exhaustion stops further intake, not an already fully specified,
explicitly authorized supported operation. Unknown fields still stop writes.
