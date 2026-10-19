# TASK-493 — DESIGN-023: root dashboard and next step from kernel

Date: 2026-10-19. Required verification: V3.

## Authority

User explicitly repeated: “继续，把 goals、decide 和根看板也迁到新架构，完成剩余切换。” Locked DESIGN-023 decisions and §6 F/G/H are the plan of record. Session rollover is controlled by the agent environment/user (TASK-496); there is no token ceiling. This authorizes scoped implementation, isolated verification and local integration preparation; final drop/V5 acceptance remains against a concrete reviewed artifact.

## Acceptance criteria

1. Root combined snapshot and every active lane snapshot obtains current structured facts/counts/metrics from kernel queries, follows cursors and preserves unknown/stale/error distinctions. No legacy perry-state/goals/task readers determine current work/goals/decision state.
2. Next-step reasoning is an explicit bounded skill procedure using query facts, not a deterministic rule evaluator or method code added to the kernel. Mission, narrative, evidence and existing user approval boundaries remain visible.
3. Startup recovery, malformed/interrupted adoption/diagnosis and concurrent state safety are preserved by concrete replacements before old implementations are removed. No automatic resume. Config, packs, host capability, ownership and user-language routing remain usable.
4. Migrate reachable shared references, pack paths and external consumers required by the new snapshot contract; retire obsolete executable recommendations. Demonstrate known representative states (empty/missing, active/blocked/review, unmeasured/partial metrics, pending human input, interrupted/error) with native calls.
5. Exact final complete checks, consumer smoke and independent review/integration prove the implemented scope; no invented counters or renderer-only acceptance.

## Bound

Enumeration: the locked DESIGN-023 §6 selected row and its directly reachable tools, lane references and consumers. Exact tool/check/consumer inventory is an artifact of H, not an unbounded claim. No unrelated project changes, remote publication or kernel growth beyond written concepts/commands/guards.

## Dispatch

Dispatch mode: manual
Executor: manual
Subjective verification: final dropped-check table and H sign-off remain with the user.
Touches architecture: root §2/§3/§6, bin and kernel module documents; target reconciliation under the explicitly requested cutover.
Deployed: no
