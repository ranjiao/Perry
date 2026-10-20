> Completed 2026-10-18. See evidence/2026-10/TASK-490-formal-switch-20261018.md. The snapshot below is historical; do not resume its activation steps.

# Formal kernel cutover — resume handoff

## 0 Resume point

User approved formal switching on 2026-10-18: “现在可以正式切换了”. Approval persists; do not ask again. No live import, ADR activation, product merge, push/tag/publication occurred.

Stop cause: context gate213253/200000 OVER; work/reference/budget-boundary.md forbids new dispatch. Fresh session must run startup/recovery/interrupted/head/status gates, retrieve the existing review, fix/re-review, and use an independent integrator. Root authored the implementation and cannot self-merge.

## Current source boundaries

- Primary Perry: `/Users/bytedance/proj/Perry`, main `558e698f3e3672e5f1a9004eca4aa00555305529`. Dirty `.perry/events.jsonl`, `perry/tasks.jsonl` and untracked TASK-490/491 evidence/journals are this chat's PMO records; preserve them. No primary product edits.
- Candidate: `/Users/bytedance/.codex/worktrees/task-490-kernel-cutover/Perry`, branch `codex/task-490-kernel-cutover`, clean `da04f3f71ad29de5f12d4999a22a400ad9c2d178` as last checked. Root implemented this candidate.
- aiMark candidate: `/Users/bytedance/.codex/worktrees/task-491-aimark-kernel/aimark`, clean branch `codex/task-491-kernel-query`, `1efee323ed982c3d7d73ce74d84c503911d2d31f`.
- aiMark primary: `/Users/bytedance/proj/aimark`, main `b4944762e6babc2189bc3d704104933504c09899`; 9 tracked WIP files plus `src/preview-tab.ts` and `src/preview-tab.test.ts`. Preserve all WIP; do not commit unrelated work or overwrite `src/server.ts`. Earlier isolated combined-WIP checks passed, but integration must check the actual final source.
- SkyTonight primary: unrelated dirty work remains untouched. Use latest backup manifest for head/hashes; recheck before action.

## Independent review already running

Collaboration agent `/root/cutover_review` was spawned fresh (`fork_turns=none`), explicitly through `work/reference/review.md`. It has no write authority to candidates/main/live stores, only isolated mutations and scratch report. Check its completion/message; do not dispatch duplicate review while it runs. It will report a uniquely named file under `/tmp/perry-scratch/Perry`.

Reviewed Perry range is the above primary base through candidate head; criteria `perry/evidence/2026-09/TASK-490-spec.md`, present at base. aiMark criteria `perry/evidence/2026-09/TASK-491-spec.md`, above base/head. Review excludes not-yet-executed live activation from pre-cutover readiness and must not claim final TASK-490 acceptance. It also assesses static architecture attention semantically.

Concrete findings NOT yet fixed (reviewer mutation report still pending):
- Five explicit active journal writes: packs/software-ops/architecture.md:90,97; incidents.md:43,84; runbooks.md:60.
- Additional conflicting instructions: work/reference/digests.md:191 suggests a journal note; git-boundaries.md:11 grants journal/tasks.jsonl PMO ownership; conversational.md:38 calls journal status append routine.
- Native read defect: runbooks.md:75 discovers deployed tasks via BOARD.md+journal, missing new native tasks after cutover.
- Historical lane/add-task notes are explicitly retired and should remain historical. No candidate edit was made this turn.
- Adapter fresh checks so far:40/40 targeted tests; copied-store parity Perry489/489 (23open), Sky32/32 (1open), zero core-field differences. Await final verdict/mutations; do not infer PASS from this update.

Global review precheck has30 historical findings, none for selected490/491 exhibits. `/tmp/perry-scratch/Perry/switch-20261018-review-precheck.json`; written specs have Bound. Do not rewrite unrelated history or claim global lint green.

## Validation already recorded

Candidate da04f3f7 complete committed-head gate: 162 modules / 4116 root tests, 110.6s, exit0; tree guard unchanged. Separate kernel run279 tests, one original platform skip. Candidate diff check clean. This validates that exact head only; it does not waive newly found procedure defects.

Evidence: `perry/evidence/2026-10/TASK-490-repair-20261018.md`, `TASK-490-checks/repair-20261018-validation.json`, full log and test migration inventory. No V4/V5 self-award; task state remains in_progress/review.

Tests MUST pin candidate PERRY_HOME and unset PERRY_PROJECT; inherited PERRY_HOME points to primary. Focused repair checks then final complete gate and diff check.

Architecture: original and approved-target baselines/checkpoints are recorded in the cited repair report. Both latest delivery checkpoints are fresh but attention(target_changed,incomplete_coverage). Preserve the real original start, refresh delivery after fixes, and obtain independent semantic adjudication; never forge a clean/static acceptance.

Architecture update: reviewer found no new Python boundary contradiction, but pack findings leave semantic attention unresolved. Root ARCHITECTURE.md §4:195–202 still diagrams legacy perry-task→JSONL→journal as active; treat descriptive mismatch separately and respect user-owned architecture rules.

## Backups and prepared imports

Latest backup: `/Users/bytedance/.codex/backups/perry-kernel-cutover-20261018-729d3d9601/manifest.json`. Readable hashed Perry442316800-byte and SkyTonight33904640-byte state archives; aiMark WIP patch/untracked archive. Live kernel stores absent at backup time.

Latest fresh isolated reconciliation (candidate da04f3f7): `/tmp/perry-scratch/Perry/switch-20261018-prepared.json` and per-project migration reports. Perry489tasks/108asks/4risks; Sky32tasks/0asks/2risks; all five import criteria true. These exports have NO lifecycle rehearsal fixture records.

- Perry export `/private/tmp/perry-scratch/Perry/formal-Perry-ad535ae5/anchor/perry/export`
- Sky export `/private/tmp/perry-scratch/Perry/formal-SkyTonight-4db89cf3/anchor/doc/perry/export`

A PMO next-action write accompanies this handoff, so re-run backup + reconciliation before live import; current prepared Perry export is stale. Never use exports from lifecycle rehearsal flows (they include fixture items), and never copy rehearsal SQLite files into live storage.

## Remaining switch sequence

1. Fix complete independent-review finding category in isolated candidate; add meaningful regression guards for the actual missed procedure branches. Commit, revalidate and get corrected-head fresh review. Preserve all unrelated work.
2. Authorized independent integrator reads release/README.md, work/reference/git-boundaries.md, packs/software-ops/releases.md and tests/merge-check --help. Allocate Perry patch release on integration branch using current main/current VERSION and unique delivery ID. Validate merged candidate with complete gate and release checks. No self-merge. No push/tag/publication authorization implied.
3. Integrate coupled aiMark adapter locally, retaining primary WIP. Use isolated combined-tree validation first; controlled stash/reapply only with backups/hash checks and no unrelated commit. Test actual combined final tree. Inspect any running app before restart; never kill by process pattern.
4. Refresh backup and reconciliation after state changes. Stage fresh export under each real state root, preserving existing files; dry-run native import, then import at real --root with state_root perry/doc/perry. Never copy rehearsal DBs. Compare all IDs/fields/states/seq/events, export bytes and repeat-import refusal. Preserve failed artifacts; never roll back over new native events.
5. Decide lane owns ADRs; read decide/SKILL.md and decide/reference/decisions.md. Mint store/rung successors sequentially via perry-decide new --supersedes ADR-006 / ADR-020; fill bodies at returned paths. Archive ADR-010 through tool. Drafts: /tmp/perry-scratch/Perry/cutover-20261018-{store,rung}-adr-body.md, grounded in DESIGN-023/ADR-025. Old dry-runs both previewed ADR-026; no ID reserved.
6. Final real-anchor aiMark/native smoke and immutable receipt. Close tasks through native kernel only if all written criteria truly pass. Journal/legacy work registers stay frozen; goals/decide/root legacy dashboard migration remains TASK-492/out of scope. User switch approval is actual, but never fabricate a human actor or independent review.

