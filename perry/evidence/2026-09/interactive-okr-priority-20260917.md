# Interactive OKR priority and implementation assessment

User direction, 2026-09-17: prioritize constructive discussion that helps users design better OKRs. The user expects progressive clarification, an editable draft and explicit final approval for OKR and phase.

## Execution priority

TASK-191 real discussion evaluation, followed by TASK-192 routing and reuse, TASK-193 premise challenge/escape, TASK-194 phase reuse; TASK-444 editable draft/finalize is raised P2 to P1, alongside TASK-264 writer dependency. TASK-465 assembles the approved journey. Do not dispatch further peripheral improvements ahead of this chain. Existing isolated TASK-456/457 deliveries are preserved pending their remaining integration/review gates, not discarded or claimed merged.

DESIGN-020 decision 5 already grants plans/ claim consent. The previous TASK-444 next-action request for repeat consent was stale and is corrected. USER-955 still concerns the real interview target; this priority request is not a fabricated interview answer. USER-952 still governs missing writer representation. No existing goals or phase commitments were changed.

## Proposed discussion behavior for acceptance refinement

1. Begin with a short interpretation of the user's intended change, identifying what is known, proposed and unknown. Reuse explicit answers; do not equate available context with approval of new targets.
2. Ask the most consequential unresolved question, one at a time. Each question explains what choice it changes and offers a grounded candidate answer. React to the answer before choosing the next question.
3. Constructively challenge activity-based goals, unsupported baselines, arbitrary metrics and competing priorities. Explain the consequence, offer a better formulation or a real alternative, and retain the user's override. Avoid generic praise and forced agreement.
4. Produce an early, small draft within the locked question budget. Unknowns remain visible; no invented zero baseline, deadline or capacity. An outcome can be evidenced by a concrete observed behavior; arbitrary business metrics must not replace the user's actual goal.
5. Support edits in chat and in the draft file. Re-read edited content before presenting the next revision; preserve accepted wording and surface changed scope, thresholds and assumptions. Editing a draft is not approval to finalize.
6. Ask approval of the actual current draft. Only then use the owning writer to finalize; missing writers or stale inputs stop canonical writes. Phase planning repeats this boundary for its own scope.

These are proposed acceptance refinements within locked DESIGN-020, not a claim of delivered functionality or a changed rubric. Agent owns interpretation and questioning; Python owns typed draft state, integrity and deterministic persistence, not semantic judgment.

## Verification plan

Review conversation turns against the unchanged input-quality rubric and the locked design. Inspect whether a user's correction changes the subsequent question and draft, whether a challenge improves an outcome formulation, and whether a rejected recommendation stays rejected. Exercise unclear intent, rich prior context, user disagreement, unknown baseline, file edits, interruption and approval followed by edits. Mechanical tests check state boundaries and restoration; they cannot certify helpful dialogue.

A scripted fixture may prove mechanics but cannot replace the required real-user interview. SkyTonight's existing OKR must not be deleted to manufacture a first-run test. Existing-project revision is a separate route and should preserve current canonical goals until approval.

## Preserved peripheral deliveries

TASK-456 independent V4 and architecture PASS on 434c979e..5c7618f1; main integration/full/slow and final-head architecture review remain pending. Review: /private/tmp/perry-scratch/review-task-456-r2/phase004/review.md.
TASK-457 coding delivery b897811688dcf560c2e5f3626ada435bf9c8eae7; independent V4 and integration remain pending. Result: /private/tmp/perry-scratch/task-457/phase004/result.md. Both jobs exited successfully before slots were released.

## Started preparation

Five bounded criteria files now exist: TASK-191-spec.md, TASK-192-spec.md, TASK-193-spec.md, TASK-194-spec.md and TASK-444-spec.md. TASK-444 now requires V4 because the approval and persistence path can corrupt state if wrong. A fresh isolated read-only audit is running at d45e42c6; no task is declared implemented from these specifications.

An implementation-sequence question was presented to the user: allow isolated implementation before the real interview, retaining that interview as a release acceptance gate, or preserve the original ordering. No answer yet; dependencies and locked design remain unchanged. Source: DESIGN-011 section 6 states “Step 2 is the gate”; DESIGN-020 section 6 also gates D/E on the real transcript.
