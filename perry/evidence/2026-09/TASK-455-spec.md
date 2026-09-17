# TASK-455 — Independent architecture review at integration

Date: 2026-09-17. Owner: Coding Agent. Priority: P1. Required verification: V4.
> Touches architecture: shipped review and dispatch procedures, DESIGN-017 D3.
> Dispatch mode: auto
> Executor: codex
> Subjective verification: independent review of bounded procedure scenarios
> Deployed: no

Authorization: USER-957 and the phase's explicit autonomy for locked DESIGN-017. TASK-450 and TASK-453 are done in the task store. Existing user confirmations, high-stakes screening, host matrix, isolation and no-self-merge rules remain binding.

## Deliverable

Move the architecture compliance judgment to fresh review of the exact integration candidate. Select it using the typed diff facts listed in DESIGN-017 section 5.3. Narrow executor architecture context to root sections 1, 3 and 6 plus each touched component's module document. The executor no longer certifies its own compliance.

## Acceptance criteria

1. The merge procedure checks all six bounded trigger classes: listed boundary paths; new top-level directory; new bin executable; contract-version change; root architecture edit; module architecture edit. A diff touching only perry/ invokes no architecture review. Unknown trigger/context facts are exposed rather than silently called safe.
2. A triggered review uses a fresh context, exact base/head/diff, root sections 1/3/6 and touched module documents selected by the agent from the confirmed component list. It answers holds/contradicts/not touched per relevant rule, with rule-line citations, in a merge-evidence ARCHITECTURE COMPLIANCE block. A decided-section contradiction goes to the existing user decision gate.
3. Every supported executor brief stops requesting an author compliance block or unconditional full architecture injection. It preserves task RESULT, Git/worktree isolation, scratch derivation, host eligibility, verification and high-stakes screening. A task author cannot award the fresh-review gate.
4. Two explicit walkthrough fixtures demonstrate the procedure: viewer/parsers.py change yields a review block citing a rule; perry/evidence-only change yields a recorded no-trigger result and no review block. A removed required pointer or restored executor self-attestation is detected by the existing structural fixture/guard or the fresh semantic reviewer. No Python prose-meaning classifier is introduced.

## Files in scope

work/reference/dispatch.md architecture injection/compliance/review sections and merge acceptance references; work/reference/review.md merge-time architecture reviewer brief; packs/software-ops/architecture.md corresponding integration references if needed to avoid contradictory instructions; existing tests/test_spec_scannability.py or existing architecture instruction guard for intentionally changed lexical/pinned contracts only. Leave the pre-flight high-stakes gate section 4, the host matrix, decided architecture documents and schema untouched.

## Bound

Six trigger classes above, two scenario walkthroughs, three automated executor brief variants plus manual handoff references if this change touches them. No new backend, registry, command, semantic parser, task store field or architecture rule. Agent judgment owns meaning. Net Python/test lines <=0; preserve meaningful existing safety checks, including the unmodified scratch/isolation block.

## Verification

Exact base/head and path diff; targeted existing pointer/instruction tests; smoke; committed affected tier with four workers; two reviewer-authored scenario outputs retained as evidence. Any test hash update must name exactly the intentional changed procedure and preserve unrelated normative text. Read runner source rather than tests/run --help. Set canonical candidate PERRY_HOME, unset PERRY_PROJECT, and use isolated TMPDIR.

## Out of scope

Changing the high-stakes gate that constrains this task; changing decided architecture/confirmed hashes; S1-S7 implementations; foreign writes; release allocation; publication; main integration. Code/prose changes are committed by the coding role in its isolated branch. V4 and main integration are separate.
