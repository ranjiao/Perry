# Shared goal discussion and question bank

Loaded through `goals/SKILL.md` for first OKR, revision and commitments.
The deliverable is a useful draft for review, not a claim that planning
persistence or finalize writers exist. Keep `reference/input-quality.md` as the
unchanged quality authority. Phase and week procedures live at their own entrances.

## Route and reuse

Use the requested horizon, declared tracks in `.perry/config.jsonl`, and the
snapshot's existing OKR/phase facts. Read the selected track's mode contract for
its spine: `project` decomposes goals through phases; `pipeline` and `queue`
use commitments. Do not infer a route from the project's name, apparent maturity,
repository size or an empty file. An unreadable or ambiguous state is unknown,
not proof that there is no OKR. In a mixed project, use the explicitly selected
track/horizon; a queue track does not redirect an explicit overall revision.
If selection is still consequentially ambiguous, ask one routing question and
wait. Count it in the chosen route's budget; switching labels never resets it.

| Route | Evidence for entry | Cap before visible draft | Next unanswered gap → draft destination |
|---|---|---|---|
| First OKR | Overall goals requested, no existing OKR confirmed | 8 | Q1 mission/horizon; Q2 focus; Q3 evidence; Q4 boundaries → first overall draft |
| Revision | Existing OKR and a requested material change or pivot | 5 | Q9 change/affected goals, then affected Q1–Q8 gaps → proposed new version with change reasons |
| Commitments | Selected pipeline/queue spine or explicit `commit` request | 3 | Q10 promise terms, Q3 resolution evidence or Q5 arrival/baseline gap → proposed commitment row and operational unknowns |

For each turn identify the selected route and the next unanswered consequential
gap with its draft destination, in plain language. If none remains, draft now.
Selecting a route never starts a phase or week, revises other tracks, or creates
a commitment. `init` with an existing OKR offers revision only if change is wanted;
`revise` without one reports that mismatch instead of inventing an old version.

Reuse explicit opening answers and accepted existing wording with provenance:
name the message, or document/version/section that supplied each carried answer.
An earlier decision remains an earlier decision, not consent to a new horizon,
threshold or commitment. Distinguish observed facts, accepted wording, proposals,
rejected suggestions and unknowns in the visible draft. Skip only unchanged,
explicit answers; read proposals in old drafts as proposals. On revision preserve
unaffected accepted wording verbatim and show before → proposed after plus the
reason for each affected goal. A clear new user correction supersedes the older
intent in this draft; retain the old source and the correction so the change is
reviewable. Ask only about unresolved meaning or consequences.

The commitments route reuses the same bank, without manufacturing Objectives or
KRs. Show arrival rate/source (or unknown), SLA/date, beneficiary and what resolved
means. Reuse declared SLA as existing policy, never as consent to a new promise.
Unsupported `To whom` or `Due` stays unknown and prevents a write. Once the user
explicitly approves the exact supported create/amend operation, follow
`goals/reference/phases.md § commit <promise>` through `bin/perry-goals commit`.
An explicit complete `commit` instruction can already supply that approval;
an interview answer or draft edit cannot. Extra operational context is not a new
writer field. Never invent an arrival-rate field or manually edit the register.

## Use the bank

Read the user's opening context and relevant project descriptions already in
scope. Distinguish observed facts (with a source), the user's decisions, proposed
targets and unknowns. A repository name, empty data file or missing analytics is
not evidence of zero users, zero incidents or zero current capability. Propose
answers grounded in what was actually read or said; label an unsupported baseline
`unknown`, and a proposed target `proposed — not yet accepted`. Do not turn an
example or a hypothetical number into a project fact.

For an overall draft, default to **one qualitative objective and at most three KRs**. Use the solo/fewer
qualification in rubric 1.5; do not add objectives to satisfy its generic 2–4
range. Each KR must earn its place by representing a distinct outcome. Do not
force Learn/Build/Validate tracks or quotas of principles/anti-goals.

Use Q1–Q4 as a coverage guide, filling their proposed answers from known context;
choose the next consequential unresolved gap anywhere in the bank, not the next
number in a script. Q5 commonly addresses an unknown baseline. Q5–Q8 address
remaining gaps, not a mandatory second form. `Skip when` means the
specified answer is explicit and unchanged in the selected route's context, not
inferred from confidence or project age. Show its source in the draft.

At each response, use the latest accepted intent and briefly show substantive
changes. A changed beneficiary, capacity, objective or evidence invalidates the
dependent proposed KRs, thresholds and commitments: name what no longer follows,
withdraw it from the current proposal, and visibly propose replacements or mark
the affected fields undecided. Recheck their mission alignment, measurement basis
and feasibility; do not merely acknowledge a correction or relabel the old metrics.
Explain what the revised focus or scorecard would demonstrate in practice and
which supplied facts support the recommendation. Reduced capacity is not evidence
for an invented lower target; an unknown baseline is not proof of attainability.

Keep accepted user wording and explicit rejected suggestions visible in the draft
conversation; do not reintroduce a rejected metric under a new name. Keep unaffected
explicit facts without reconfirming them. When an answer conflicts with earlier
context, show the conflict: apply a clear correction directly, and ask only if its
meaning or the dependent choice remains unresolved. User corrections are accepted
intent; the agent's replacement targets and commitment labels remain proposals
until the user accepts them. Silence or confidence is not acceptance.

Ask **one question at a time and wait**. Count every question and follow-up that
asks the user for an answer toward the **route cap above before showing the draft**;
reflection text must not hide a second independent question. A
scorecard choice may present one coherent proposed set for acceptance or editing.
On a vague answer, name the single most consequential gap and offer one grounded
rewrite; push at most once for that answer, within the same budget. If still
unknown or the budget is spent, retain it explicitly and draft now. Do not loop
until every rubric issue disappears. Already supplied answers need no ritual
confirmation; fewer than four questions is fine when the user supplied the facts.

Render a `choice` as 2–3 options, the grounded proposal first with `(Recommended)`;
explain the practical difference briefly. Render a `sentence` as a proposed
sentence followed by `Use this | Edit it | Say it differently`. Use the configured
language and the host's prompt rendering from `$PERRY_HOME/reference/host-capabilities.md`.
The seven fields below guide the agent; do not expose the whole bank to the user.

## Q1 · Who benefits, and over what horizon?

Kind: sentence
Draft answer: Combine the user's stated beneficiary, problem and horizon into “Over [horizon], this project helps [beneficiary] achieve [change] because [reason].” Attribute the source; mark any missing part unknown rather than inventing a market or date.
Ask: “I propose this mission and horizon: [sentence]. What would you change?”
Push until you hear: A recognizable beneficiary and useful change, with an overall horizon that can bound the first draft. If absent, offer the closest supported rewrite and keep the remaining gap explicit.
Red flags: “Make a great product”; naming a technology as the mission; assuming every project needs customers or revenue; a deadline silently derived from the current phase.
Produces: Mission and Period; the mission clause to which the objective must trace (rubric 1.6).
Skip when: The user already stated both the mission's beneficiary/change and the horizon clearly.

## Q2 · What single change matters most?

Kind: choice
Draft answer: From the mission, propose one qualitative directional objective and show its mission clause. Offer one genuinely different emphasis only if context supports it; “edit the proposal” is preferable to fabricated alternatives.
Ask: “For this first period, which outcome should we organize around: [grounded focus] (Recommended), [supported alternative], or your edited focus?”
Push until you hear: A qualitative outcome worth pursuing that serves the mission, narrow enough for one objective. Move numerical success criteria into the candidate KRs instead of the title.
Red flags: A task list called an objective; metrics in the objective title; copying three generic tracks; a second objective with no distinct reason.
Produces: One Objective and its Mission alignment, with ≤3 KR slots (rubric 1.1, 1.5, 1.6).
Skip when: One clear qualitative objective and its mission connection are already explicit.

## Q3 · What evidence would prove the change?

Kind: choice
Draft answer: Propose the smallest scorecard of one to three outcomes from the stated objective. For each show baseline with source or unknown, metric/unit, proposed target, deadline tied to the horizon, and proposed commit/stretch. A target is a choice, not a measured fact. If context gives no defensible number, label target undecided and route its gap to Q6.
Ask: “Would this proposed scorecard demonstrate the outcome: [compact scorecard] (Recommended), or should we edit the outcome/threshold? We can narrow it to the strongest single KR if needed.”
Push until you hear: Observable changes rather than work performed, with each score expressed as number + unit + deadline; an explicit baseline or an acknowledged measurement gap.
Red flags: “Ship feature” as the success measure; counting hours instead of benefit; fake zero baselines; target numbers presented as already agreed; three KRs measuring the same outcome.
Produces: Candidate KRs and measurement gaps; outcome, measurable target, baseline and small count (rubric 1.2–1.5); candidate commitment labels for 1.8.
Skip when: The user supplied ≤3 outcome KRs with explicit measurement, baseline status, deadline and commitment labels.

## Q4 · What will this period deliberately refuse?

Kind: sentence
Draft answer: Propose concrete anti-goals from stated scope, time, cost or safety constraints. Separate enduring principles from this period's exclusions. Where no constraint was given, label the suggested refusal as a choice rather than attributing it to the user.
Ask: “I propose these boundaries: [short refusal sentence]. Which boundary needs changing?”
Push until you hear: At least one concrete tempting action the project will not take during this period, and any known constraint that makes the chosen scope feasible.
Red flags: “No wasted time”; “quality first” as an anti-goal; inventing a budget or safety policy; turning an existing requirement into an optional exclusion.
Produces: Anti-Goals and any grounded Operating Principles (rubric 1.7); scope constraints for evaluating the scorecard.
Skip when: Concrete period refusals and known constraints are already stated.

## Q5 · Close the baseline gap

Kind: choice
Draft answer: For the highest-value unknown baseline, name the actual available evidence and propose a feasible observation method. State that its result is not known yet; do not replace an unknown with the desired starting value.
Ask: “For [metric], should we use [existing evidence] (Recommended if available), measure it by [proposed method], or leave the baseline explicitly unknown in this draft?”
Push until you hear: Either an attributed current value or a concrete way to obtain one, whose timing/source remain proposals until accepted. If neither is available, keep the uncertainty visible.
Red flags: “Probably zero”; inferred current values from absence of telemetry; claiming that a plan to measure satisfies the baseline check already.
Produces: KR baseline and source, or explicit unknown plus proposed measurement action (rubric 1.4); evidence for checking 1.8. A future measurement plan does not make 1.4 clean today.
Skip when: Every proposed KR baseline is already explicitly supported by evidence or the user has already chosen to leave it unknown.

## Q6 · Make the score decidable

Kind: sentence
Draft answer: Rewrite the weakest candidate KR into “[outcome metric] from [known baseline/unknown] to [proposed target] [unit] by [deadline], checked with [evidence].” If the current KR is an output, explain the user-visible result it should demonstrate, grounded in Q1/Q2.
Ask: “I suggest this scoreable version of [KR]: [sentence]. What target or evidence would you change?”
Push until you hear: One outcome with a unit, threshold and deadline that a reviewer can score; do not imply the suggested threshold is proven realistic.
Red flags: A more elaborate activity list; a percentage without a denominator; “soon”; a test that measures implementation completeness but not the chosen outcome.
Produces: The KR's outcome, target/unit/deadline and evidence definition (rubric 1.2, 1.3).
Skip when: All candidate KRs are outcome-based and already have explicit numbers, units and deadlines.

## Q7 · Separate commitment from stretch

Kind: choice
Draft answer: Compare each candidate threshold with its supported baseline and the user's stated capacity. Propose commit only where real progress is needed; label capacity assumptions. Put already achieved facts in context, not among future goals.
Ask: “I propose [set] as commitments and [optional set] as stretch (Recommended); should we narrow commitments or edit the thresholds?”
Push until you hear: A deliberate commitment/stretch distinction, with no knowingly already-met target masquerading as a commitment. Unknown capacity/baselines remain uncertainties, not proof of attainability.
Red flags: Easy targets chosen only to look green; every uncertain idea marked must-achieve; inventing baseline progress to justify a stretch target.
Produces: KR commitment labels and any accepted threshold corrections (rubric 1.8; preserves 1.5's small scope).
Skip when: Labels are explicit, targets are not already met according to known evidence, and the user has stated the relevant capacity constraints or acknowledged them unknown.

## Q8 · Preserve the rules that outlast the period

Kind: sentence
Draft answer: Distill only the user's stated enduring constraints into a short principles sentence. Keep temporary exclusions under Anti-Goals and explicitly say when no enduring principles were supplied.
Ask: “These sound like lasting rules rather than this period's goals: [sentence]. Keep or edit them?”
Push until you hear: Grounded invariants, or an explicit choice that none is being declared yet. Do not invent five to ten principles to fill a template.
Red flags: Generic virtues; new safety restrictions attributed to the user; a task deadline presented as a lasting principle.
Produces: Operating Principles and separation from period Anti-Goals (supports rubric 1.7; no additional rubric requirement).
Skip when: Enduring principles, or the user's choice not to declare any yet, are explicit; also skip when no such gap affects this first draft.

## Q9 · What changed, and what does it invalidate?

Kind: sentence
Draft answer: Compare the requested change with the accepted goal version. Propose a concise change statement naming affected Objectives/KRs and why; retain unaffected wording and identify any dependent threshold or commitment that no longer follows.
Ask: “I read the change as [before → after, reason and affected goals]. What needs correcting?”
Push until you hear: A concrete change and its consequence for the selected horizon, or an explicit unresolved impact to carry into the draft.
Red flags: Re-interviewing the whole mission; rewriting unrelated accepted KRs; treating old approval as permission for new thresholds.
Produces: Revision reason and affected goal sections; the dependent scorecard gaps to address through Q3/Q5/Q6/Q7.
Skip when: The change, its scope and affected goals are already explicit; propagate it directly and ask only about unresolved consequences.

## Q10 · What promise is being made?

Kind: sentence
Draft answer: Assemble the supported promise to a named party, its date/SLA and resolution definition, using the declared track and user wording. Show arrival rate/source or unknown as context; unsupported terms remain undecided. Explain what this promise would oblige the track to do.
Ask: “I propose this promise: [terms and practical consequence]. Use this, edit it, or say it differently?”
Push until you hear: A recognizable party, what counts as resolved and an explicit clock, or named unknowns. Queue Due uses an accepted typed SLA/date; pipeline Due needs an ISO date. A declared track SLA is required by the queue writer.
Red flags: An invented SLA; arrival volume guessed from backlog; a promise to nobody; drafting treated as permission to write; silently changing track policy.
Produces: Commitment Promise / To whom / Due / By when note; resolution evidence and arrival-rate uncertainties in draft context.
Skip when: These exact terms are already supplied; discuss only changed or missing terms, then use the existing writer only with explicit operation approval.

## Show the draft and the remaining issues

Display one compact **[selected route] draft — not finalized** in chat. For overall goals: Period; Mission;
Operating Principles (or none supplied); one qualitative Objective with its mission
clause; a ≤3-row KR scorecard with baseline/source, target/unit, deadline and
commit/stretch; Anti-Goals; and explicit unknowns/proposed assumptions. Carry over
accepted wording and make suggested changes visible. A complete-looking table is
not evidence that an unknown was resolved. Do not turn measurement follow-ups into
extra KRs merely to fill slots. For revision, include change reasons and affected
goals with unchanged wording preserved. For commitments, show the proposed row
and remaining operational unknowns, without an objectives cascade.

Run `$PERRY_HOME/reference/input-quality.md § 1` once against this actual draft
where applicable; for a commitments-only draft state which Objective/KR checks
are inapplicable rather than inventing an OKR or a replacement rubric.
The entries' `Produces` fields map all eight checks; coverage is not a passing
score. Surface at most three highest-value issues with concrete rewrites, including
missing baselines or undecided targets. Preserve advisory + override and record
any user's stated override reason in the draft conversation; do not fabricate a
journal receipt or silently rewrite their answers. If clean, say so briefly.

This bank stops at that visible draft and quality feedback. It does not create
`plans/`, claim resume support, write canonical goal stores, call an imagined
finalize command or automatically start a phase. Approval/persistence/finalization
must use the owning implementation when available; do not substitute manual store
writes for missing tooling. The explicit commitment operation described under
**Route and reuse** retains its existing writer; it does not supply overall
planning finalization. No end-to-end interview quality gate is claimed here;
that requires the independent transcript review, beyond mechanical pointer checks.
