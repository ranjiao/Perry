# TASK-491 — aiMark native kernel adapter

Date: 2026-10-15. Status: ready for review; integration is coupled to TASK-490.

## Authorization and ownership

The user approved the TASK-490/TASK-491 scope and then explicitly authorized an isolated aiMark committed-HEAD checkout: “可以，从已提交 HEAD 隔离适配”. Primary aiMark WIP was preserved.

- Base: `b4944762e6babc2189bc3d704104933504c09899`.
- Branch: `codex/task-491-kernel-query`. Commits: `d47f312` and final `1efee32` (native source labels).
- Checkout: `/Users/bytedance/.codex/worktrees/task-491-aimark-kernel/aimark`.
- Architecture checkpoint: not applicable to this TypeScript-only task; Python facts cannot certify it.

## Result

Native query/events/template reads replace the production legacy task calls. All pages must share the kernel sequence; concurrent changes cause a bounded retry. Cache validation uses the kernel sequence, including flow/history. Existing task views receive a local projection of native items; no compatibility command is added to Perry. The board drawer uses the same snapshot.

Form actions use native create/update/move and optimistic seq checks. Unsupported legacy-only fields refuse explicitly. Evidence stays opaque except for explicit attachments. The application cannot lower a rung at close or impersonate a human V5 signer. Goal/decide readers remain on their existing contracts until their planned cutover.

## Verification

- Against candidate Perry `fb7bdc4c`: typecheck, frontend build and **1002/1002 tests passed** across 61 files. Log: `TASK-491-checks/standalone-final.log`.
- A separate temporary checkout combined this commit with the primary aiMark tracked WIP and its two untracked preview-tab files: typecheck, build and **1010/1010 tests passed** across 62 files. Log: `TASK-491-checks/combined-final.log`. This is compatibility evidence, not an integration or device-acceptance claim.
- Hash verification: all 11 primary WIP files stayed byte-identical. `TASK-491-checks/primary-wip-preservation.json`.
- Real imported Perry parity: **489 rows, 23 open**, all IDs and six core fields agree. Open-row next_action/evidence also agree after the importer's blank normalization. Closed next_action values are intentionally omitted by the reviewed importer and are excluded from this parity claim. `TASK-491-checks/task491-parity-results.json`.
- `git diff --check` passed. No push, main merge, live store switch or desktop/device acceptance occurred.

## Acceptance

1. No production gateway call uses the legacy task executable; the retained legacy parsing exports/tests are not production readers.
2. Real task-row parity is evidenced above; native lifecycle, dependency and cache-refresh behavior is tested.

The same-release condition remains pending TASK-490 acceptance.
