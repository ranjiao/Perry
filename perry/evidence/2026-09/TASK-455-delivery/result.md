# TASK-455 implementation handoff

Base: 3034c249b8f116c5e1ae975685bbf9358a4471b2
Commit: 779e74675515a6d669e4c8317c3f583201d86ff2
Branch: codex/task-455-phase004-20260917
Checkout / PERRY_HOME: /private/tmp/perry-scratch/Perry/phase004-k4_waa0n/task-455
TMPDIR: /private/tmp/perry-scratch/task-455/phase004/tmp; PERRY_PROJECT unset for verification and reviewer children.
Authorization: USER-957 and this TASK-455 dispatch. This is a coding delivery, not V4/V5 acceptance or task closure.

## Scope

Exactly four committed product paths:
- work/reference/dispatch.md: six typed diff trigger classes, fresh exact-candidate integration review, bounded executor context, removal of executor compliance certification, merge acceptance reference.
- work/reference/review.md: independent reviewer brief and two bounded walkthrough fixtures, negative mutation/revert checks.
- packs/software-ops/architecture.md: corresponding integration references, removal of conflicting self-attestation/completion-time and legacy draft gate exemptions.
- tests/test_spec_scannability.py: intentional Claude brief hash repin and explanatory comment only; existing tests and assertions retained.

Net Python/test lines: 3 inserted / 3 removed = 0. No dependency, parser, backend, schema or architecture rule added. No live or copied PMO stores edited; fixture commits exist as synthetic Git objects only, without materializing the evidence file in a PMO checkout. No decided architecture, release allocation, push, merge or publication.

Exact diff: product.diff. Exact path diff: paths.txt. Frozen root/module architecture, schema, host matrix, Git boundaries, dispatch high-stakes step 4 and scratch/isolation region compare byte-for-byte equal to base (unchanged-contracts.json).

Intentional guard repin: only the Claude executor Build prompt instruction changed from full architecture + author compliance to bounded context + ordinary RESULT. Old digest 0338efa0df46fc8d09a6a8938e4c85eeb2388ef7161607c7c40c390a6ca79f3c; new digest eadb199709db6f5ac79902af3aa432c2bda2d230c3d6bdd883e410cf4a9198fe. Unrelated normative bytes preserved.

## Verification

One suite at a time; at most four workers; runner source read, never tests/run --help.
- python3 -m unittest discover -s tests -p test_spec_scannability.py: 71 tests PASS (targeted.log).
- python3 tests/parallel test_pointers_resolve test_host_support -j 4: 40 tests / 2 modules PASS (pointers-host.log).
- bash tests/run --tier smoke: PASS, including tree guard (smoke.log).
- python3 tests/parallel --tier affected --base 3034c249b8f116c5e1ae975685bbf9358a4471b2 -j 4: PASS on committed 779e74675515a6d669e4c8317c3f583201d86ff2; 569 tests / 21 executed modules, 27.3 seconds (affected.log).
- git diff --check: PASS; checkout clean after commit.

The selection contains 22 modules; test_merge_gate.py is explicitly held back by the runner as slow-tier. Full/slow and merged-candidate checks belong to the integrator and were not run. This is green for affected, not a green full suite.

### Printed affected selection (verbatim)

```text
tier affected · 3034c249b8f116c5e1ae975685bbf9358a4471b2...HEAD · 4 changed path(s) · running the modules below
  test_actor_required.py                       covers work/: work/reference/dispatch.md
  test_blank_cell_is_one_rule.py               COVERS = ALL
  test_claims.py                               covers tests/test_: tests/test_spec_scannability.py
  test_escalation_boundaries.py                covers work/reference/dispatch.md: work/reference/dispatch.md
  test_host_support.py                         covers packs/software-ops/architecture.md: packs/software-ops/architecture.md
  test_live_state_expectations.py              covers tests/test_: tests/test_spec_scannability.py
  test_merge_gate.py                           covers work/reference/dispatch.md: work/reference/dispatch.md
  test_module_run_guard.py                     covers tests/: tests/test_spec_scannability.py
  test_next_closing.py                         covers packs/software-ops/: packs/software-ops/architecture.md
  test_ownership.py                            covers packs/: packs/software-ops/architecture.md
  test_pointers_resolve.py                     covers packs/: packs/software-ops/architecture.md
  test_procedures_call_the_tool.py             covers packs/: packs/software-ops/architecture.md
  test_procedures_read_the_contract.py         covers packs/: packs/software-ops/architecture.md
  test_reference_pages_are_reachable.py        covers work/: work/reference/dispatch.md
  test_restore_check.py                        covers work/reference/review.md: work/reference/review.md
  test_review_verdicts.py                      covers work/reference/review.md: work/reference/review.md
  test_role_cards.py                           covers packs/software-ops/: packs/software-ops/architecture.md
  test_router_budget.py                        covers packs/: packs/software-ops/architecture.md
  test_scratch_is_per_agent.py                 covers work/reference/dispatch.md: work/reference/dispatch.md
  test_shipped_vocabulary.py                   covers packs/: packs/software-ops/architecture.md
  test_spec_scannability.py                    changed: tests/test_spec_scannability.py
  test_starts_write_the_config_store_first.py  covers work/: work/reference/dispatch.md
selected 22 of 158 modules · 210.0 of 1723.3 module-seconds (12.2%)
  held back — test_merge_gate.py is the slow tier's (tests/parallel § HARNESS_SELF_TESTS): run `bash tests/run --tier slow`
```

## Bounded mutation / revert evidence

External document copies only; no production mutation planted. mutation-guard.py runs the existing TestTheAgentGetsItsOwnTree.test_the_governed_regions_are_pinned against each copy.
- Restored executor self-attestation: existing guard FAIL (one failure); reverted copy PASS.
- Removed fresh reviewer pointer: outside the existing pinned region, so that guard stays green. Detection belongs to the independent semantic reviewer; no claim that Python detected meaning.
- Both reverted documents independently equal git show 779e74675515a6d669e4c8317c3f583201d86ff2:work/reference/dispatch.md. See mutation-guard.log and fixture-receipt.log.

The two exact synthetic fixture base/head pairs are retained in fixtures.json, with reader.diff and evidence.diff. They are not product delivery commits. Reviewer-authored evidence (fresh context /root/scenario_reviewer):
- [Reader walkthrough](reader-walkthrough-review.md): rule-cited compliance block; BLOCKED for missing module context, NN-1 holds.
- [Evidence-only selection](evidence-walkthrough-selection.md): six false facts, no trigger, no compliance block.
- [Semantic mutation review](mutation-review.md): both mutations FAIL, both restored copies PASS and byte-identical to committed source; no bounded procedure defect found.
These outputs do not award task V4/V5 or integration approval.

## Limitations and handoff

The frozen component list identifies viewer/parsers.py but supplies no reader module document. The reader walkthrough must return a cited rule finding and BLOCKED for missing context; this is expected fail-closed behavior, not a fabricated pass. The evidence-only fixture records all six triggers false and no architecture review block.

This task's independent V4 acceptance, human V5 if applicable, release allocation and main integration are not performed here. The implementation cannot self-award them. Existing procedure remains authoritative until TASK-455 is independently accepted. No claim of architecture-review automation or durable PMO evidence persistence is made; the main PMO owns persistence.

## ARCHITECTURE COMPLIANCE — existing dispatch procedure

This author block is supplied for THIS delivery under the existing procedure, as explicitly required by the dispatch; it is not the new independent integration gate.

=== ARCHITECTURE COMPLIANCE ===
Touched sections: §2 lanes and packs/tests; §3 procedure/tools boundary; §6.NN-4, §6.NN-5, §6.NN-6.
Compliance check:
- §1 and §2: shipped agent procedures remain the procedure owner; no service, backend or dependency added.
- §3: no new reader, numeric computation in a lane, foreign tool root or architecture write; the four-path product diff is bounded.
- §6.NN-4 (ARCHITECTURE.md:271): agents judge meaning; Python retains only the existing pinned-byte assertion. Semantic pointer-loss detection is explicitly agent-owned.
- §6.NN-5 (ARCHITECTURE.md:280): smoke's tree guard passes; suites use isolated TMPDIR and canonical candidate PERRY_HOME; no PMO store writes.
- §6.NN-6 (ARCHITECTURE.md:287): frozen root/module architecture and decided rules remain byte-identical; USER-957 authorizes implementing locked DESIGN-017 D3, not deciding new rules.
New §7 questions opened: none; existing absent module-document context is reported rather than silently accepted. Main PMO owns any subsequent decision/evidence persistence.
=== END COMPLIANCE ===

=== RESULT ===
Branch: codex/task-455-phase004-20260917
PR: n/a — local commit only; no push authorized
Files changed: 4 (listed above)
Tests: 569/569 affected, plus 71 targeted and 40 pointer/host tests; smoke PASS
Cycle time: not separately measured
Notes: Independent V4/main integration pending; reviewer fixture evidence does not close the task.
=== END RESULT ===
