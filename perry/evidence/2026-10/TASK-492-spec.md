# TASK-492 — DESIGN-023: goals and decide on native kernel

Date: 2026-10-19. Required verification: V3.

## Authority

User explicitly repeated: “继续，把 goals、decide 和根看板也迁到新架构，完成剩余切换。” Locked DESIGN-023 decisions and §6 F/G/H are the plan of record. Session rollover is controlled by the agent environment/user (TASK-496); there is no token ceiling. This authorizes scoped implementation, isolated verification and local integration preparation; final drop/V5 acceptance remains against a concrete reviewed artifact.

## Acceptance criteria

1. Extend the process template (not domain logic in kernel) with objective, KR, check, phase, design and ADR item types and appropriate relations/metrics. Existing task/ask/risk items, events and identities are preserved.
2. Reconcile real copied Perry and SkyTonight goals/versioned OKR/linkage/check/phase/design/ADR data. Re-key IDs shared across OKR versions, retain exact legacy IDs as labels; preserve facts/unknowns without inventing metric current values. Existing ADR filename ceiling must prevent ID reuse.
3. Goals and decide procedures use kernel CLI for structured state, owned narrative documents as attachments. No legacy structured writes or journal writes remain; old goals/decide writers retire/freeze consistently. Preserve approval, attribution, human V5 and phase-close ordering.
4. New migration commands are one-shot skill-side adapters, not a kernel compatibility API. Dry-run/plan, safe idempotency, source hashes, native replay/export and current-store reconciliation must be demonstrated. Never import over a nonempty live store or add fabricated history to seed an ID. If a generic kernel capability is actually missing, produce a bounded isolated proposal before changing its governing contract.
5. Write the ADR025-scheduled OKR-items successor through decide at activation, with actual prior authority and typed links. Final live activation follows reviewed code and fresh backups; no phase/goals replanning is implied.

## Bound

Enumeration: the locked DESIGN-023 §6 selected row and its directly reachable tools, lane references and consumers. Exact tool/check/consumer inventory is an artifact of H, not an unbounded claim. No unrelated project changes, remote publication or kernel growth beyond written concepts/commands/guards.

## Dispatch

Dispatch mode: auto
Executor: codex
Subjective verification: final dropped-check table and H sign-off remain with the user.
Touches architecture: root §2/§3/§6, bin and kernel module documents; target reconciliation under the explicitly requested cutover.
Deployed: no
