# TASK-191 readiness and constructive OKR discussion audit

Date: 2026-09-17. Source: detached `d45e42c69f5145aae4dc5c8e1987bb5344847945`.
Repository: `/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/okr-discussion-audit`.
Status: preparatory analysis only. **Not a real human interview, V4 review, acceptance, or task completion.**

## Conclusion and evidence boundary

The first-OKR route is available for a future real interview, but discussion quality is unproven. Its concrete strengths are grounded proposals, explicit unknowns, one-question-and-wait, one push per vague answer, and a draft-only exit. Its weaknesses are proposal-led anchoring and insufficiently explicit propagation of corrections into subsequent proposals. These are first-route review findings, not evidence that a real interview failed.

Existing-project routing, escape/premise handling, and shared phase elicitation are explicitly deferred. Their absence must not be misreported as TASK-190 failing its bounded deliverable. They nevertheless explain how the wider product can still produce agent-authored goals followed by a confirmation question. A confirmation at the end cannot establish that the goal was constructively discussed.

Only the named guidance, task records, current phase, relevant design sections, startup/ownership guidance and selected existing tests were inspected. No live SkyTonight files were accessed. No tests, interviews, writers, dispatches, task transitions or dependency changes were performed. The sole authored artifact is this report outside the checkout. The update check was skipped to preserve the user's read-only constraint. Root AGENTS.md applies; discovered template AGENTS files do not govern these source paths. A targeted memory lookup returned no relevant entries and supplied no findings.

Read-only startup receipts: recovery `blocking: false`, no interrupted pipelines, clean detached checkout, host `codex-cli`. `perry-state --compact` identified active phase 004, day 3. Counts/status came from that command; task details came from `bin/perry-task list --json`, not journal reconstruction. The user's specified audit replaces the ordinary interactive next-action prompt; no phase was started.

## Task readiness and ownership

The task-detail command at this head returned:

| Task and title | State / dependency | Ownership and permitted preparation |
|---|---|---|
| TASK-191 — SkyTonight interview, unchanged rubric | blocked; `blocked_by: [USER-955]`; `startable: false`; depends on TASK-190 and USER-955; required verification V4; no evidence paths | Coding Agent facilitates; a real user supplies answers; later independent review judges the transcript. This report prepares scenarios only. |
| TASK-192 — Routing and smart-skip, by track spine | not_started; blocked by TASK-191; not startable | Coding Agent: horizon/spine routing and reuse of confirmed answers. |
| TASK-193 — Escape hatch and premise challenge | not_started; blocked by TASK-191; not startable | Coding Agent: bounded disagreement, refusal and premise correction behavior. |
| TASK-194 — plan-phase uses the same bank | not_started; blocked by TASK-191; not startable | Coding Agent: shared phase interview for first and subsequent phases. |
| TASK-465 — Guided initialization through first approved plan | not_started; blocked by TASK-192/193/194/444; not startable | Coding Agent: orchestration, not another bank or planning state machine. |

These are a dated command snapshot, not durable state updates. TASK-191's current next action explicitly forbids fabricated user answers. USER-955 concerns the unsuitable first-OKR project: TASK-190-result.md:43–48 reports SkyTonight already has an active OKR. This audit relies on that recorded fact, not a fresh external-project inspection. Authorization for preparation does not resolve USER-955 or unblock successors.

Relevant written boundaries: `perry/evidence/2026-09/TASK-190-spec.md:15–27` limits delivery to first-OKR and assigns the real gate to TASK-191; `perry/design/DESIGN-011-the-okr-is-elicited-not-collected.md:202–213` makes the real transcript the gate before wider routing; `perry/phase/004-guided.md:62–63,73–87` requires the user's own answers, forbids substitution, and defines a later phase-day fallback. Day 3 is not that day-14 fallback, and this analysis claims neither fallback activation nor KR progress.

## Behavioral findings

All paths below are repository-relative and line ranges refer to the pinned head. “Risk” describes a plausible instruction-driven failure, not an observed human transcript.

### 1. Drafted-answer anchoring: first-route risk, not permission to remove drafted answers

Evidence: `goals/reference/setup.md:23–26`; `goals/reference/elicitation.md:24–44,49–65,69–75,79–85`. Every normal opening question supplies a proposed answer, choices put the proposal first as Recommended, and Q3 can ask for acceptance of a whole scorecard. This implements the locked design (`perry/design/DESIGN-020-guided-planning.md:361–381`); drafting itself is not a defect.

The gap is that “grounded” does not by itself expose the reasoning behind a preferred metric or threshold. A defensible draft can still anchor the user on an agent-selected outcome. Q2 appropriately forbids fabricated alternatives, and Q3 permits an undecided target; retain those protections. The smallest behavioral correction is to explain the supported consequence of the recommended focus/metric and keep the user's edit path genuinely open. Unsupported choices remain proposed, even if surrounding facts are sourced. Do not add an obligatory extra question or force alternatives without context.

Observable failure: after the user rejects the chosen outcome, the agent changes the label but retains its original success metric. Owner: TASK-191 readiness findings against TASK-190's first route; any bank correction needs separately authorized scope, not silent expansion into TASK-192 or TASK-465.

### 2. Follow-ups recognize gaps but do not explicitly propagate corrections

Evidence: `goals/reference/elicitation.md:31–39,90–115,129–142`. The bank selects baseline/scoreability/commitment follow-ups and caps a vague-answer push. It does not lack response sensitivity entirely. However, it does not explicitly require invalidating dependent proposals when a clear answer changes the mission, capacity or evidence model. “Start with Q1–Q4” (`:24–29`) can still be followed as a sequence of approvals rather than a developing discussion.

Minimal expected behavior: identify what the correction changes, drop the invalidated proposal, and choose the next unresolved consequence of the latest answer. A capacity reduction must change candidate commitments, not merely append a capacity note. Distinguish useful pushback from ritual reconfirmation of facts already supplied. Owner: first-route behavior under TASK-191; cross-route carry-forward under TASK-192; premise disagreement under TASK-193.

### 3. Stop-and-wait exists; successful execution remains unverified

Evidence: `goals/reference/elicitation.md:31–39` explicitly says one question and wait, counts follow-ups toward eight, and allows unknowns after one push. `goals/reference/setup.md:33–36` and `elicitation.md:144–149` prohibit finalization and auto-starting a phase. These are implemented boundaries, not missing features.

Failure to end the turn after a question, inventing the user's reply, or treating silence/default selection as assent would violate current instructions. A coherent scorecard is permitted as one choice (`elicitation.md:34`), but hiding several independent decisions in that question is not (`:32–33`). A hypothetical walkthrough cannot establish compliance by an actual human-facing run. Owner: TASK-191 observation; TASK-444 owns later persisted draft/edit/approval mechanics, as referenced by TASK-465-spec.md:32–36.

### 4. Escape and premise disagreement are missing intentionally

Evidence: `goals/reference/elicitation.md:3–7` excludes these flows. In contrast, retained `DESIGN-011:144–195` requires one concrete push, an anti-sycophancy table, one two-question negotiation on “just do it,” immediate yield on second refusal, and disagreement returning to the source question. `DESIGN-020:379–411` retains this behavior before approval.

The bank already has the single-push rule, so calling all constructive challenge absent would be wrong. What is absent from the loaded first-route procedure is the explicit escape/premise workflow and interviewer-response calibration. The resulting risk is accepting the agent's summary without ever giving the user a distinct opportunity to reject a foundational assumption. Owner: TASK-193, blocked by TASK-191. Do not use this gap to self-award a first-route failure or waive the gate.

### 5. Premature approval: route-specific protection and misleading surrounding prose

Evidence: first-init stops safely at a visible “not finalized” draft (`elicitation.md:129–149`, `setup.md:27–36,70–72`). Yet `goals/SKILL.md:178–181` still describes init as creating an OKR, and `setup.md:59–64` moves revision from walking changes to appending a version without the new explicit draft/premise/approval sequence. The phase procedure does require confirmation (`phases.md:206–208`), so it does not authorize wholly unconfirmed writes; it simply does not specify the discussion that should precede confirmation.

Locked `DESIGN-020:403–418` distinguishes editing, explicit approval and tool finalization. “I'll edit” ends the turn; missing/refusing writers stop finalization. Approval of one suggested answer is not approval of a final plan. A rubric-clean table is also not user approval (`reference/input-quality.md:15–20,33–36`). Owner: TASK-193 for premise timing, TASK-192 for revision route, TASK-444 for persisted approval/finalization; TASK-465 integrates only after those components. This audit does not establish which writer binaries are currently implemented.

### 6. Phase route has concrete collection pressure and contradictory write guidance

Evidence: `goals/reference/phases.md:164–200` enumerates ten mandatory output sections and prescribes 2–4 objectives / 3–5 KRs, then proceeds to rubric, confirmation and writing (`:204–226`). No shared interview call or five-question cap is specified in that plan-phase procedure. The broader lane also caps phase KRs at four (`goals/SKILL.md:193`), making the “3–5” instruction inconsistent even within existing guidance. The unchanged phase rubric inherits the solo/fewer qualification (`reference/input-quality.md:48,55`). Required output structure should not become ten user questions or force invented objectives.

The same page directs appending objective/KR JSON records and defends agent authoring (`phases.md:214–216`), while locked `DESIGN-020:413–418` prohibits hand-appending when a writer is missing. That is a documented instruction conflict, not proof of a currently missing executable. Minimal resolution in future route work: route to the approved owner flow and stop if it is unavailable; do not repair writers or schema inside an interview task.

Owner: TASK-194 for phase elicitation/reuse and its boundary; TASK-444 / existing goals writer work for finalization. TASK-465 consumes the route. TASK-190 expressly excludes it (`TASK-190-spec.md:25–27`).

## Route coverage, without claiming a repository-wide runtime audit

| Locked route and cap (`DESIGN-020:353–359`) | Evidence in bounded source | Remaining ownership |
|---|---|---|
| First OKR, ≤8; shortest 4–5 | setup.md:20–36 loads bank, stops at chat draft | TASK-191 real quality gate; TASK-444 persistence |
| Revision, ≤5 | setup.md:55–66 retains old revision procedure; bank explicitly excludes it | TASK-192 routing/reuse; TASK-193 premise; owning finalizer |
| Phase, ≤5 | phases.md:148–226 still separate collection/write procedure | TASK-194 shared bank; TASK-192 route selection |
| Week, ≤2 | Design requires it; bank excludes phase/week at elicitation.md:3–5 | DESIGN-020 phase E covers it collectively; detailed weekly implementation was not inspected |
| Commitments, ≤3 | phases.md:16–22,63–66 describes field gathering plus a writer, not the shared interview | TASK-192 spine routing; phase-E implementation must name coverage explicitly |

`DESIGN-020:487–494` assigns phase/week/commitments collectively to TASK-192/193/194. The current individual task descriptions emphasize routing, escape, and phase reuse. Week/commitments route ownership therefore needs to be made explicit in future dispatch criteria, not silently treated as covered or implemented here. TASK-465-spec.md:63–70 explicitly keeps later phase/week workflows with their existing implementation tasks.

## Six hypothetical dialogue scenarios — NOT real human transcripts

Every user and agent utterance below is authored solely as an illustrative review stimulus. None was spoken by a real interview participant. These are expected behaviors, not executed tests, scores, acceptance receipts or substitutes for TASK-191. Proposed numbers are fictional choices, never measured project facts.

### 1. A grounded proposal still anchors the wrong outcome

Hypothetical user: “This is a solo learning project for families; I want children asking their own questions. Four weeks.”
Hypothetical agent proposal: “Count completed lessons as the scorecard?”
Hypothetical user correction: “No. Completing lessons could still be passive.”
Expected next agent utterance: “Then completion does not show the change you want. We could observe whether a child initiates a question after an activity; the baseline and threshold are still unknown. Would that evidence reflect your goal?” **Stop and wait.**

Observe: original completion metric is withdrawn, the new metric has a stated connection to the user's correction, no made-up baseline/threshold, no auto-accepted scorecard. Failure: retain lesson count under a renamed ‘curiosity’ objective. Owner: first-route TASK-191 review; bank correction scope if authorized. Evidence: elicitation.md:60–75,100–105. This is a fictional project, not SkyTonight.

### 2. A clear capacity answer changes the next question

Hypothetical user: “Improve reliability.”
Hypothetical agent: “That does not yet say what failure to reduce. From the incident example you supplied, I suggest tracking failed saves. Is that the right outcome?” **Wait.**
Hypothetical user: “Yes, but I have only two hours per week and no failure count.”
Expected next agent utterance: “The count is unknown, and the earlier broad commitment would exceed that capacity. Shall we first use a small observation sample to inform a target, leaving the target undecided in this draft?” **Wait.**

Observe: one initial push, follow-up responds to actual capacity/evidence, measurement plan is not called a measured baseline, uncertainty remains if unresolved. If the question budget is exhausted, show the draft instead of another question. Failure: continue Q4 mechanically or assert ‘zero failures now.’ Owner: TASK-191; cross-session reuse belongs TASK-192. Evidence: elicitation.md:31–39,87–115.

### 3. An unanswered question is a real boundary

Hypothetical user: “Help me set the first OKR.”
Hypothetical agent: “Who should benefit from this project?” **No reply arrives.**
Expected behavior: the interview turn ends with that question. No hypothetical user answer is generated; no second question, proposed acceptance, canonical write or next-phase launch follows.

Observe: absence of an answer remains absence, including an unsubmitted recommended choice. A provisional draft is possible only under the explicit draft/escape rules and must remain visibly uncertain, never accepted. Failure: ‘You probably mean customers, so here is the approved plan.’ Owner: TASK-191 stop/wait; TASK-444 future resume. Evidence: elicitation.md:31–39,144–149; DESIGN-011:146–155.

### 4. Two refusals exercise the escape hatch

Hypothetical user: “Just do it.”
Expected agent utterance: “Two more questions would make the KRs scoreable; I can ask those, or draft with the gaps visible.” **Wait for the choice, rather than asking both questions at once.**
Hypothetical user: “No more questions. Draft it.”
Expected behavior: immediately draft from available context, preserve unknowns, show up to three rubric issues, and stop at the applicable draft boundary. No third negotiation; no fabricated override reason or approval.

Observe: at most one offer, no coercive repeated push, no declaration that missing baselines pass. Failure: refuse all drafting until every field is supplied, or bypass the rubric. Owner: TASK-193; TASK-191 stays incomplete. Evidence: DESIGN-011:165–176; setup.md:30–36. This scenario describes missing route behavior to implement, not a passing existing feature.

### 5. Premise disagreement and premature approval

Hypothetical user supplies an already formed OKR, then says: “Looks good; I will edit the target.”
Hypothetical premise statement: “This objective exists to grow paid usage.”
Hypothetical user: “Disagree. This period is about trust; paid growth comes later.”
Expected agent utterance: “Then paid usage does not support this period's objective. I will return to that focus and revise only the affected parts. What observable change would demonstrate trust?” **Wait.**

Observe: pasted OKR skips redundant interview questions, disagreement reopens the producing question, stale metrics are revised visibly, and ‘I will edit’ ends the turn without approval/finalization. After corrections, run the unchanged rubric once on the reviewable draft before explicit approval. Approval must refer to the actual revised draft; a missing writer still stops finalization. Failure: treat ‘looks good’ as blanket approval, keep the paid-growth KR, or write before the user's edit. Owner: TASK-193 premise/escape; TASK-444 edit/approval; TASK-192 smart-skip. Evidence: DESIGN-011:172–190; DESIGN-020:403–418.

### 6. Phase planning reuses context and the bank

Hypothetical user: “Keep our approved mission and anti-goals. Next phase should test whether people return; we can spend two weekends.”
Expected agent utterance: “I will carry those approved boundaries forward. For this phase, should the focus be evidence of return use within those two weekends, with expansion deferred?” **Wait.**
Hypothetical user: “Yes, but do not commit me to recruiting ten people.”
Expected behavior: remove that proposed human commitment, adapt scope/evidence, and ask only the next unanswered phase-specific question. Use the same bank, ≤5 questions including follow-ups, then a visible phase draft containing focus, concrete not-doing, verifiable DoD, KRs and appetite. Carry unknown metrics openly; do not fill ten sections by inventing decisions.

Observe two variants of this same scenario: OKR with no prior phase; OKR with a scored prior phase whose relevant learning is reused. An active phase must not silently be replaced or closed. A queue-spine variant must select commitment questions (arrival/SLA/resolved), not force project-growth KRs. Missing writer blocks finalization; no hand-append fallback. Owner: TASK-194 phase reuse; TASK-192 routing; TASK-465 initialization integration. Evidence: DESIGN-020:353–359; phases.md:152–175,204–216; TASK-465-spec.md:27–39.

## Proposed minimal acceptance criteria — not approved task changes

These proposals reuse the existing question bank, rubric and owner flows. They create no new framework, score or dependency. TASK-191 remains the gate before implementation of TASK-192/193/194.

### TASK-192 — routing and smart-skip

1. Demonstrate first OKR, revision, phase, week and pipeline/queue commitment selection from declared state/spine and user intent; state the selected horizon in ordinary language. Do not route by project age or overwrite an active phase. Caps remain 8/5/5/2/3 respectively, including follow-ups before draft.
2. Existing approved goals and explicit opening answers are reused with their source visible; ask only for missing or changed information. A user correction supersedes the relevant carried premise and updates dependent proposals; stale data is not silently accepted. No first-ever interview on an existing approved OKR.
3. Route demonstrations cover existing-project initialization and the queue distinction; show the loaded procedure and owning downstream task. Where week/commitment interview implementation is not yet available, identify the gap instead of claiming coverage. TASK-465 consumes routing and does not recreate it.

### TASK-193 — escape hatch and premise challenge

1. Demonstrate one concrete push on a vague answer, one two-question escape offer on first refusal, immediate draft on second refusal, and pasted complete OKR going directly to premise review. All questions stop and wait and count against the route's existing cap.
2. Show grounded premises after questions and before approval; disagreement returns to the producing question and visibly revises dependent text. Praise must name evidence or the missing part, following the retained anti-sycophancy guidance. Do not demand agreement or invent the user's rationale.
3. Show the unchanged rubric once on the reviewable draft with at most three advisory issues and the actual user's override reason if given. Distinguish answer acceptance, draft editing, plan approval and writer completion. ‘I'll edit’/silence/refusal never finalizes; use TASK-444's owning flow when available, otherwise stop honestly.

### TASK-194 — shared phase elicitation

1. Both first-phase and subsequent-phase demonstrations load the same bank, reuse approved overall context and relevant prior learning, and ask ≤5 response-sensitive questions before a draft. No duplicate ten-field interview or second bank.
2. The resulting draft covers the existing ten-section output contract without manufacturing answers: explicit phase focus, phase-specific exclusions, verifiable DoD, justified KRs, appetite, user commitments and uncertainty. Apply existing §2 plus its inherited §1 checks; do not force objective/KR counts contrary to the existing solo qualification or change the rubric to fix instruction drift.
3. Show a disagreement/changed-capacity case that changes the phase proposal, explicit review/approval, and missing/refusing-writer stop. Replace the legacy hand-append path only through the established owner integration; no ad hoc canonical writes or writer implementation hidden in this task. TASK-465 reuses this path for initialization.

Future evidence for these criteria should preserve actual prompts, replies, revisions, stop boundaries and resulting draft. Hypothetical fixtures can diagnose implementation behavior, but cannot satisfy TASK-191's real participant requirement or self-award independent review.

## Existing-test inspection and what it cannot establish

No tests were run or added. Selected relevant existing tests were read:

- `tests/test_pointers_resolve.py:125–157` checks that pointers/anchors resolve and that the scan is nonempty. It cannot show a meaningful next question after disagreement.
- `tests/test_router_budget.py:246–307` checks byte budgets and section citations. A short valid pointer is not proof of route coverage or interview quality.
- `tests/test_starts_write_the_config_store_first.py:12–25,60–87` explicitly checks literals and executes config-first examples in fixtures. It does not assess goal discussion or approval.
- `tests/test_procedures_call_the_tool.py:44–75` describes structural procedure guards and exemptions. It cannot turn an unsupported semantic planning path into a valid finalizer.

`perry/evidence/2026-09/TASK-190-result.md:35–48` reports 119 historical tests passing, while explicitly denying mechanical proof of interview semantics. This report does not rerun or adopt that historical pass as present acceptance. The question-bank ending itself requires independent transcript review (`elicitation.md:148–149`).

Readiness outcome: preparatory findings and future observable checks are now available. Real human interview, unchanged-rubric result, independent review and all dependent task gates remain outstanding. No acceptance or completion is asserted.

Final read-only receipt: checkout remained clean and detached after report creation (`git status --short --branch`; empty `git diff --stat`). The report contains exactly six hypothetical scenario headings. Current rubric SHA-256 is `399cdb615d6ae7b87c5a82f5a2e26e82d9951607b0e39ac9d5bce50465a74e88`, matching TASK-190’s recorded hash. No test suite was run.
