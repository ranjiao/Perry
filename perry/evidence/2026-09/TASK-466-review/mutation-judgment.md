# Reverting-fix semantic judgment

## M1 — Reverting both changed procedures to the pinned base

Input: Exactly S2's reduced-capacity fixture: 10 hours/week becomes two; previous proposed commitments are 20 independently onboarded members and 90% first-attempt success, both baselines unknown. December 31, onboarding focus and no paid acquisition are explicit.

Actual proposed reviewer response:

> Two hours/week is now the capacity, and onboarding remains the focus. Here is the draft scorecard for December 31.
> | Proposed commitment | Baseline | Target |
> |---|---|---|
> | Independent member onboarding | Unknown | 20 members |
> | First-attempt onboarding success | Unknown | 90% |
> The no-paid-acquisition boundary remains. Which onboarding outcome should take priority?

Resulting chat draft: Only the capacity cell changes. Both dependent thresholds and both commitment proposals survive unchanged; no evidence supports their feasibility under the corrected capacity. They are still labeled proposals, so mere proposal labeling has not fixed the dependency defect.

Independent judgment: FAIL of TASK-466 acceptance criteria 1 and 3 for this mutant continuation. The correction is acknowledged without withdrawing/reconsidering either dependent threshold or commitment. Keeping the numbers as proposals is still insufficient. This conclusion is independent reviewer semantic judgment of the input and output, not the result of a wording assertion.

Procedure analysis: The physically reverted bank at lines 24-39 instructs a normal Q1-Q4 path and single-question budget, but contains no per-response dependency withdrawal step; reverted setup lines 23-27 likewise contains no propagation instruction. The candidate's elicitation lines 32-48 and setup lines 23-28 explicitly prohibit M1. The base still has useful general grounding and Q7 feasibility guidance; this finding does not claim the base forces every agent to produce M1 or that the candidate guarantees all future model behavior. Removing the changed instructions fails this bounded procedure-level semantic review because the required correction propagation is no longer specified. One realistic defective continuation makes the user consequence concrete.

Comparison: S2 contains one candidate KR with target/label undecided after withdrawal. M1 contains two stale proposed commitments with old thresholds. Both have one question and unknown baselines; those mechanical properties alone cannot distinguish good behavior from bad. S4's supplied-context behavior and S5's unknown-baseline/cap rules remain present in the base, so this is a propagation regression, not a claim that every scenario fails after revert.

Provenance: Reviewer-authored hypothetical negative walkthrough, performed after reading the physically mutated files. No separate model was launched; no human acceptance, automated prose evaluator or wording-mirror test is claimed.
