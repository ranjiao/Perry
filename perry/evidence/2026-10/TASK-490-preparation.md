# TASK-490 — native work cutover preparation

Date: 2026-10-15. Status: in progress; not accepted for live switching.

## Authorization and isolated delivery

The user approved the proposed TASK-490 / TASK-491 scope: “可以，按这个范围继续”. Implementation and testing precede live-switch approval.

- Base: `558e698f`. Branch: `codex/task-490-kernel-cutover`. Initial implementation: `fb7bdc4c`; current follow-up: `5daae778`.
- Executor checkout: `/Users/bytedance/.codex/worktrees/task-490-kernel-cutover/Perry`.
- Work procedures now call native kernel item/query/event/relation/attachment operations.
- All 27 old write verbs refuse before project discovery/recovery/actor checks, including dry runs. Discovery advertises no write capabilities.
- Old reads refuse pending transactions rather than replaying them. The importer preserves that refusal and still detects concurrent source changes.
- The carried mixed-template event regression independently tests each item-change key, in both orders.

Current follow-up and full-gate evidence: [approved targets and tests](TASK-490-approved-targets-and-tests.md). The sections below retain the earlier preparation measurements.

## Earlier architecture evidence

Durable store: `/Users/bytedance/proj/Perry/perry/evidence/2026-10/TASK-490-architecture`.

- Real pre-edit start: `TASK-490/start-20261015T110335Z-9f43813978`.
- Current comparison: `TASK-490/delivery-20261015T113145Z-676804fc0a`.
- Scope: import roots `bin,kernel,viewer`, excludes `tests,kernel/tests,perry,.git`.
- Freshness verification passed on the committed implementation, with **attention**, not semantic acceptance. Known reasons: new static call/bytecode-cache unknowns and the intentional mismatch with the still-unmodified bin target's legacy-writer description.
- Opening the report through Codex was requested; the host returned `queued`, so rendered UI acceptance is not claimed. No target document was changed. Proposed edits: `TASK-490-target-proposal.patch` (dry application check passed). Python facts do not certify Markdown procedures, TypeScript, runtime or device behavior.

## Verification

- Kernel suite: **279 tests, 278 passed and 1 existing skip**.
- Retired-writer boundary: **3 tests passed**, including every write verb and dry-run variant, and pending-transaction read immutability.
- Importer: **63 tests passed**, including late-marker refusal and concurrent-change detection.
- Documentation pointer and manual architecture-contract checks: **41 tests passed**.
- Both Perry and SkyTonight imported into isolated temporary stores and reconciled all five criteria (counts/states, ID resolution, ID ceilings, non-empty refusal and replay).
- Work lifecycle rehearsal: **34 native calls** on the Perry copy and **21** on SkyTonight, including task/ask/risk creation, dependency edges, blocked/start/submit/done, required evidence refusal, stale-write refusal, events and export. All expected outcomes passed.
- Initial full repository gate failed: **77 of 162 modules**, with the runner counting **1474 failed assertions/subtests among 4549 test methods**. This is retained as failure evidence, not waived. Later focused fixes do not establish a green full suite. Final committed-tree full gate also failed: **75 of 162 modules**, runner-counted **1267 failed assertions/subtests among 4550 methods**, 188.1 seconds. The tree guard confirmed no file changed. `TASK-490-checks/final-tree-full.log` is the authoritative run for fb7bdc4c; see the follow-up for the later committed tree.
- `git diff --check` and source compilation passed.

Logs and scripts are in `TASK-490-checks/`. No main merge, live import, push, tag or publication occurred.

## Acceptance gaps and next work

1. Core work procedures and both-project kernel mechanisms are prepared; full host-procedure acceptance is incomplete.
2. Old writer refusal and safe reads are tested.
3. The new procedures stop work-journal appends; unrelated root/goals/decide cutovers remain staged as designed.
4. Store/rung ADRs and the scheduled ADR archive still need the decide-owned step coordinated with the actual switch. They have not been claimed as written.
5. Live-switch approval has not been requested or recorded; validation is not complete.

The old suite still creates fixtures by invoking the now-retired writer and asserts retired method/prose contracts. Migrate fixture setup and each affected assertion without dropping unrelated reader, ownership, restore, recovery or argument guarantees. Do not hide failures by skipping the full gate or re-enabling a production legacy writer.

The user has now explicitly approved the architecture proposal; it was applied in the isolated branch. See the follow-up. That approval is not permission to switch live stores before validation.
