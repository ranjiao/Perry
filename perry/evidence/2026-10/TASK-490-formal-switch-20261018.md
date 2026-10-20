# Formal work-kernel switch — 2026-10-18

Status: activated locally; integrated, unpublished. TASK-490 and TASK-491 acceptance evidence.

## Result and authority

The user requested the architecture switch and confirmed the exact descriptive architecture correction in this session: “应用修正并继续切换（推荐）”. The earlier formal switch approval is preserved in handoff/2026-10-18-kernel-formal-cutover.md. No human actor or V4/V5 sign-off was fabricated.

Perry main is 3bbd4a0b1badac9042f7ca78dd1ec0a51996867c, version 0.1.25. aiMark main is 09231bd25b3b79ef8f630aef0474a490f1ed056e. An independent integrator merged both. All existing primary WIP was preserved; no push, tag or publication occurred.

## Verification

- Final merged full: 162 modules / 4118 tests PASS; slow: 166 / 4221 PASS. Release checks, duration receipt verification and diff checks passed. See TASK-490-formal-switch-20261018/integration.json and its immutable receipts.
- Fresh independent behavioral and bounded architecture review: TASK-490-formal-review-20261018.md and TASK-490-formal-review-supplement-20261018.md. Named journal/native-discovery mutants were killed; restores matched git show.
- Actual Perry anchor: 489 tasks, 108 asks, 4 risks imported (601 items). Actual SkyTonight anchor: 32 tasks and 2 risks imported (34 items). Every imported item/field/relation matched the fresh rehearsal store; native re-export bytes matched, replay verified, repeat import refused and legacy canonical inputs stayed unchanged. See imports.json.
- Actual primary aiMark adapter read both live anchors: 489/489 and 32/32 tasks, zero core-field differences. Existing WIP plus adapter passed typecheck/build and 1010 tests before integration, and all 223 compared primary files matched that tested tree. See aimark-smoke.json and integration.json.
- Initial smoke harness omitted the legacy --all/limit options and compared partial legacy rows with all native rows; that invalid harness result was retained in scratch and superseded by the corrected complete read. It was not a data-loss finding.
- ADR-026 supersedes ADR-006; ADR-027 supersedes ADR-020; ADR-010 archived through the decide tool. See adrs.json.
- Latest architecture checkpoints: TASK-490-architecture/TASK-490/delivery-20261018T072944Z-ac0f53eec0 and delivery-20261018T072951Z-dcb6b41460, both verified fresh. Static target_changed/incomplete_coverage attention remains explicit; independent bounded semantic PASS does not imply complete static/runtime coverage.

## Boundary and recovery

Current work and aiMark use the native kernel. Old work registers/journal are frozen. Goals, decide and root dashboard migration remain later phases (TASK-492/493/494); this is phase E acceptance only. Browser/device acceptance was not performed. The pre-import backup is /Users/bytedance/.codex/backups/perry-kernel-cutover-20261018-66d6a5202b/manifest.json. New native events must be preserved before any rollback; never restore legacy registers over them.

Native task closure and the final export checkpoint are recorded separately in TASK-490-formal-switch-20261018/closure.json. The kernel event log, not the legacy journal, records these closures.
