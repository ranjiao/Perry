# TASK-455 independent V4 and architecture review

Result: PASS against the bounded external spec. No product finding within the four criteria.

Reviewer: fresh independent review session, not the implementing author. Date: 2026-09-17.
Criteria: /Users/bytedance/proj/Perry/perry/evidence/2026-09/TASK-455-spec.md (read externally; not copied into the candidate).
Base: 3034c249b8f116c5e1ae975685bbf9358a4471b2
Exact tested head: 779e74675515a6d669e4c8317c3f583201d86ff2
Checkout: /private/tmp/perry-scratch/Perry/phase004-k4_waa0n/review-task-455

Read applicable AGENTS.md, review-constraints.md, review.md including all four rules, relevant locked DESIGN-017 decisions/§5.3/§5.4/D3, current phase operating rules, root architecture and Git boundaries. Recovery was nonblocking; interrupted runs empty; initial checkout clean. Author result and fixture metadata were treated as inputs to verify, not verdict authority. No task-state, release, decided architecture or primary-checkout changes; no commit, push or merge.

## Criteria findings

1. **PASS — six trigger classes.** dispatch.md:466–488 requires immutable base/head, name-status, modes/summary and full diff; enumerates all six classes; explicitly treats unknowns as unresolved. Reader and evidence fixtures independently demonstrate selection (separate outputs below). Agent boundary walkthrough: a rename uses both old/new paths (470); chmod of an existing bin file triggers (478); a new directory requires absence at base (477); differing version declarations require on-demand examination (479); root removal/rename triggers (480); module removal/rename uses both component indexes (481). A missing version fact cannot be recorded false (486). These are reviewer-applied procedure readings, not executable semantic tests.
2. **PASS — fresh exact-candidate review.** dispatch.md:495–514 and review.md:483–530 connect the fresh context, exact diff, root §1/3/6, agent-selected module context and rule-cited holds/contradicts/not-touched answers. Decided contradiction blocks for a user decision; descriptive drift requires correction. Changing either SHA/diff invalidates the judgment. review.md:500–501 explicitly refuses missing module context. The reader fixture accordingly produces BLOCKED, not an invented approval.
3. **PASS — bounded executor context and preserved safeguards.** Enumerated the three automated briefs: Claude (dispatch.md:331), OpenCode (340), Codex (354), plus manual handoff reference (448–449). All use bounded context and ordinary RESULT, with no author award of the fresh gate. The only test repin covers the intentional Claude Build prompt change; assertions remain unchanged. Exact protected-region comparison retained in unchanged-contracts.json verifies pre-flight step 4, scratch/isolation, host matrix, Git boundaries, delegate, root/module architecture and schema. Objective verification, ordinary RESULT, task review/human sign-off and no-self-merge remain separate. The two comment removals are harmless; Python/test diff is exactly +3/-3, net 0.
4. **PASS — two independent walkthroughs and two mutations.** reader-walkthrough.md cites actual root rule lines and reports NN-1 holds with missing module context BLOCKED. evidence-walkthrough.md records all six false and no review block. semantic-mutations.md rejects pointer loss and restored self-attestation with specific procedure reasons. The self-attestation reversion also makes the existing guard red in the affected tier. No semantic classifier, backend, command, registry, dependency, new task field or architecture rule was introduced.

## Verification receipts

All test children received exported PERRY_HOME equal to the canonical review checkout above, PERRY_PROJECT unset, and TMPDIR=/tmp/perry-scratch/review-task-455/phase004/tmp. Runner syntax was read from source; tests/run --help was never run.

- smoke.log: `bash tests/run --tier smoke`, exit 0, tree guard clean.
- affected.log: `python3 tests/parallel --tier affected --base 3034c249b8f116c5e1ae975685bbf9358a4471b2 -j 4`, exit 0; 569 tests in 21 modules, 32.5 seconds. Printed selection has 22 modules; test_merge_gate is explicitly held back for slow tier.
- mutation-affected.log: same affected command once, with exactly base's Claude Build prompt line restored at dispatch.md:331; exit 1, exactly 1/569 tests fails: TestTheAgentGetsItsOwnTree.test_the_governed_regions_are_pinned. This demonstrates detection of reverting the fix while retaining head's guard.
- pointer-mutation.diff and pointer-restore.json: exact line 495 mutation, independent semantic rejection and restore against committed head. This pointer check is agent-owned; no claim a test detected meaning.
- self-attestation-mutation.diff and restore.json: exact mutation plus independent git-show/file SHA-256 equality for all four changed paths. No Python source was mutated, so stale Python bytecode does not affect the procedure mutation.
- restored-targeted.log: targeted spec-scannability, pointer and host confirmation, exit 0 (111 tests / 3 modules); no redundant restored affected/full run.
- product.diff, paths.txt, tested-sha.txt, fixtures.json, reader/evidence-facts.txt and reader/evidence.diff preserve exact inputs. final-status.txt records clean code status. `git diff --check` passed.

The first fixture-inspection helper mistakenly compared directory tree hashes when testing directory-name equality; a comment changes its containing tree hash. Corrected the scratch-only helper to compare `git ls-tree -d --name-only`, re-ran successfully, and retained check.py. No product code change or failed product assertion resulted.

## ARCHITECTURE REVIEW PASS

This is the separately requested architecture assessment of TASK-455, not approval of a future combined integration candidate. The four-path actual diff has no listed boundary path, new top-level directory, new bin executable, contract-version change, root architecture edit or module architecture edit. Under the new selection procedure it records no trigger. This requested independent assessment still checks the changed procedure against the binding rules.

Component mapping: work/reference pages belong to the lanes (ARCHITECTURE.md:100–118); the architecture pack belongs to packs/reference (120–127); the pinned guard belongs to tests (129–132). DESIGN-017 §5.4 is explicitly the interim skill-prose module document (its §8), and was read. Root §2 supplies no separate tests module document; this assessment does not invent one or authorize a triggered candidate with missing module context.

| Rule citation | Independent assessment |
|---|---|
| ARCHITECTURE.md:49–55, §1 | holds: no new runtime, service, dependencies or code judging meaning |
| ARCHITECTURE.md:103, §2; DESIGN-017:304, P1 | holds: procedure stays in lane references; pack points to dispatch selection and review brief |
| ARCHITECTURE.md:156, §3 | holds: no dependency-direction change |
| ARCHITECTURE.md:160, §3; :244, NN-1 | not touched: no parser implementation changes |
| ARCHITECTURE.md:161, §3 | holds: no dashboard arithmetic introduced in lanes |
| ARCHITECTURE.md:163, §3 | not touched: no project-root resolution change; isolation stays byte-identical |
| ARCHITECTURE.md:166, §3; :287, NN-6 | holds: no root/module architecture edit or decided-rule change; procedure preserves user decision gate |
| ARCHITECTURE.md:252, NN-2 | not touched: no store or projection changes |
| ARCHITECTURE.md:263, NN-3 | not touched: no write-command behavior changes |
| ARCHITECTURE.md:271, NN-4; DESIGN-017:273, §5.3 | holds: fresh agents judge compliance; executable guard remains byte/lexical-only |
| ARCHITECTURE.md:280, NN-5 | holds for this change: test logic unchanged, smoke tree guard clean, tests use isolated temporary roots |

No decided-section contradiction identified. Reader fixture BLOCKED is an expected refusal for absent context, not a TASK-455 acceptance failure and not a synthetic integration PASS.

Limits: no full/slow suite, combined merge gate, release, publication, V5/human sign-off, real executor-host launch, S1–S7 implementation, broader scenario corpus or audit of pre-existing architecture contradictions. Main integrator owns combined candidate/full/slow acceptance. Executable tests do not establish prose meaning; semantic judgments above are this reviewer's.

=== VERDICT ===
task: TASK-455
rung: V4
result: PASS
criteria: /Users/bytedance/proj/Perry/perry/evidence/2026-09/TASK-455-spec.md
checked: criteria 1–4 on 3034c249b8f116c5e1ae975685bbf9358a4471b2..779e74675515a6d669e4c8317c3f583201d86ff2; six trigger classes; three executor briefs and manual reference; two independent semantic walkthroughs; pointer-loss and reverting-fix self-attestation mutations in authorized isolated review checkout; smoke, affected and restored targeted checks; exact restore hashes and clean status
not-checked: full/slow/combined merge gate; deployment/release/publication; V5; actual host executor launches; S1–S7 and unbounded scenario coverage; absent reader module document prevents fixture integration approval
proof: work/reference/dispatch.md:466–514; work/reference/review.md:483–560; reader-walkthrough.md; evidence-walkthrough.md; semantic-mutations.md; smoke.log; affected.log; mutation-affected.log; restored-targeted.log; unchanged-contracts.json; restore.json; final-status.txt
=== END VERDICT ===
