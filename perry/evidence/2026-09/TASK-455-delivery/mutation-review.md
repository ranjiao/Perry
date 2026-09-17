# Independent semantic mutation and restore review

Reviewer: /root/scenario_reviewer; independent fresh fixture context, not implementing author; timestamp: 2026-09-17T08:32:20.367671+00:00
Reference: git show 779e74675515a6d669e4c8317c3f583201d86ff2:work/reference/dispatch.md
Scope: two disposable copies, two bounded semantic defects. No mutation of checkout, no suite execution, no task acceptance.

1. missing-pointer.md — MUTATED FAIL. At line 495 the prescribed `review.md § Integration architecture reviewer brief` connection is replaced by generic “review the candidate.” Although surrounding lines still demand fresh review and a preserved output block, they no longer route the integrator to the complete reviewer instructions, rule-by-rule assessment and fixed output contract. Merely retaining the words “Fresh brief” does not preserve that operational connection. This violates the explicit bounded pointer requirement in review.md:553–558.
   missing-pointer.restored.md — RESTORED PASS for this check. Its line 495 again routes directly to the named reviewer brief; full bytes independently match the committed source.

2. self-attestation.md — MUTATED FAIL. At line 331 the Claude executor now requires its own compliance attestation in RESULT. That orders an implementing author to supply the judgment reserved for an independent fresh integration reviewer. It conflicts with the same line's facts-only instruction, architecture preamble at lines 452–457 and fresh-brief independence at lines 499–501. Preserving those good sentences elsewhere does not cancel the new mandatory self-attestation.
   self-attestation.restored.md — RESTORED PASS for this check. The author returns implementation facts and standard RESULT; the added self-attestation requirement is absent. All three executor briefs preserve bounded context and no author compliance block. Full restored bytes independently match committed source.

Independent restore verification: Python subprocess read git show at the immutable reference above, then compared both restored files directly against those bytes, not harness snapshot bytes. Both comparisons true. Committed and both restored SHA-256: 440a4d3b905b937a08619f3acae6a6049161e7e2b04e74ea9d79b8631752003a.

These PASS results cover restoration and the two named semantic checks only. The committed procedure's two fixture selections produced their specified outcomes: reader review blocks on absent module context while retaining supported NN-1 holds; evidence-only records no trigger without an architecture review. No concrete defect found in this bounded procedure. This does not certify unrelated instructions, task V4/V5 or final integration.
