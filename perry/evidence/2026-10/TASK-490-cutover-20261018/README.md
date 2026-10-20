# TASK-490 — cutover preflight, 2026-10-18

Status: preparation completed; formal cutover not performed.

## Authority and validation condition

The user clarified “先修复” on 2026-10-18. Repair the failing complete gate
first. Formal cutover, live import and ADR activation are deferred; the earlier
switch instruction does not waive validation. TASK-490's next action records
this decision. Refresh the state backup before any later cutover because PMO
state has advanced since the rehearsal archive.

## Verified preparation

- Main remains `558e698f`; the candidate is `e890317f`, clean in its isolated checkout.
- Recovery is nonblocking; interrupted pipelines are empty.
- Full `bash tests/run`: exit 1; 46/162 modules red; runner reports 1125 failed assertions/subtests among 4631 tests. The tree guard passed. `full.log` retains the complete output.
- Both projects migrated and reconciled into fresh temporary stores. Lifecycle rehearsals passed: Perry 489 imported tasks / 34 calls, SkyTonight 32 tasks / 21 calls. See `rehearsal-results.json`.
- Readable, hashed state archives exist under `/Users/bytedance/.codex/backups/perry-kernel-cutover-20261018-dcb7c55be7`. Perry and SkyTonight canonical files still match the archive manifest after rehearsal. Their live kernel stores do not exist.
- aiMark's tracked WIP patch and both untracked files were backed up; its primary checkout was not changed.
- Store and rung ADR bodies and all three typed command dry-runs are included. They implement DESIGN-023 / ADR-025. They are previews, not active ADRs. Both new dry-runs see the same next ADR number; no number is reserved. Actual creation must mint sequentially and use returned IDs.

## Concrete switch sequence after the validation condition is resolved

1. Verify fresh recovery, canonical hashes, both imported snapshots and the accepted source commits; refresh backups if anything moved.
2. Integrate the coupled Perry/aiMark delivery with the required independent integration boundary and release records. Preserve aiMark and SkyTonight unrelated WIP. No remote push/tag/publication is part of this local switch.
3. Place validated export files under each real state root and invoke native import at its real project anchor. Never copy the rehearsal database into the live location. Read back IDs, counts, field parity, sequences and replay with the native CLI.
4. Activate the two successor ADRs through decide's tool and archive ADR-010 at the actual cutover, preserving all predecessors and links. Reconcile the related receipts before claiming TASK-490 acceptance.
5. Verify aiMark against both real anchors, freeze old work writes and record the final source/store/export/backup hashes. A failed full suite remains a failed suite if explicitly excepted; no V4 or V5 is inferred.

## Rollback limit

Before any new native work write, stop on a failed import/readback and preserve the
failed database/export for diagnosis; the source and state archives identify the
last legacy state. Do not delete or overwrite an existing store. Once new native
writes exist, preserve those events and exports and reconcile them before any
rollback; restoring only the old registers would lose new work.

The root legacy dashboard and goals/decide migration remain separately scoped.
No claim that all Perry lanes have moved to the kernel is made by phase E.
