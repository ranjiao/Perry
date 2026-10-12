# TASK-495 — local main integration receipt

The independently reviewed architecture analysis delivery was merged locally into main on 2026-10-12. No push, tag or publication occurred. Version: `0.1.24`.

## Exact commits and trees

- Main base: `f5565a38990570531c6e867e77cfaa376b5db349`.
- Independently reviewed product head: `61751b09400f305cf5255f7b75464f025a2bc3fb`.
- Full gate candidate: `b91b72f5b9827df800d2c9ecfd5507da0fe9b947`; tree `7d95767ed06ad2ccc9eb5f9c574039e2cb87bf69`.
- After importing only emitted durations: `b93c92beebca1bd6eb0dd1b20d67e03a55047f34`.
- Slow-tested final tree: `6e73e507e9f4e83797dc6e1ede67637c3bb4bb57`.
- Local main merge: `40a2605348ad13130aacf5f8f25fe2beb9299656`, with exactly that slow-tested tree.
- Full/slow code identity excluding only durations: `a7f33746ad69ecc06c671268226b4d89e35fde97face06fa0b596dcfb323539e`.

## Verification

- Full combined-tree gate: 161 modules, 4,587 tests, PASS; 235.0 seconds.
- Imported full duration artifact: provenance verification PASS, 27 tests; verified again after slow and on the exact main merge.
- Slow combined-tree gate: 165 modules, 4,690 tests, PASS; 242.1 seconds.
- Release check against the exact main base: PASS, one new version `0.1.24`.
- Diff whitespace check: PASS. Main and candidate were clean and base unchanged immediately before merge; merged tree equality was asserted afterward.
- The first full run failed a stale delegate-contract pin. The author corrected it, the independent reviewer rechecked the pin and unchanged guard semantics, and the complete gate was rerun. The failed log remains alongside the successful logs.

Receipts and logs: [integration artifacts](TASK-495-integration/). Committed logs normalize terminal color escapes and trailing whitespace; original logs remain under `/tmp/perry-scratch/Perry/`. JSON receipts retain their emitted content. The full receipt stores `artifact_verified: false` because it is the original emitted receipt; the separate main verification log records successful artifact import verification. Do not modify the emitted receipt to invent a different original outcome.

Independent review provenance: [round 1 FAIL](TASK-495-review-round1.md), [round 2 PASS](TASK-495-review-round2.md), [round 3 pin-correction PASS](TASK-495-review-round3.md), against [written criteria](../../../bin/perry_architecture/REVIEW-CRITERIA.md). The product author, fresh reviewer and integrating agent are separate roles. The verdict is the independent reviewer's; integration does not self-award V4.

## Remaining boundary and task state

TASK-495 remains in `review`. No historical TASK-495 pre-edit architecture checkpoint was recorded, so the newly introduced close gate cannot certify a pre-edit comparison. No baseline was reconstructed after the edits. This missing historical evidence does not undo the independent product review or the verified local merge, and it is not reported as completed architecture-checkpoint acceptance.

Lifecycle invocation remains host workflow enforcement; raw task-state CLI calls do not invoke a model or force architecture checkpoint creation. Static Python coverage does not prove runtime behavior, excluded content, non-Python code or semantic interpretation. User control over target changes remains required.

This evidence and the supported task-state transition are a later PMO-only commit. Its HEAD/tree differ from the tested main merge above; the full/slow claims are bound to the exact recorded merge tree, not silently extended to later project-state metadata.
