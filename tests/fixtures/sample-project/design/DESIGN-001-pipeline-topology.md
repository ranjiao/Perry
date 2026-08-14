# DESIGN-001: Pipeline topology

> Status: locked
> Date: 2026-07-20 · Locked: 2026-07-28
> Author: User   · Implementation owner: Coding Agent
> Linked OKR: KR-O1.1
> Supersedes: —   · Superseded by: —

## 1. Problem

`deploy.sh` shells out to three separate scripts with no shared failure
handling; a partial failure at step 2 leaves staging half-updated (observed
2026-07-14, 2026-07-18).

## 2. Goals

1. One entry point with a single exit code.
2. Rollback completes in ≤ 10 minutes from any failed step.

## 3. Non-Goals

- Not touching the recommender deploy path.
- Not introducing a workflow engine.

## 4. User Decisions

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Rollback strategy | Re-deploy previous tag / Snapshot restore | Re-deploy previous tag | 2026-07-26 |

## 5. Architecture

```
merge -> build -> stage -> verify -> promote
                     |         |
                     +-- rollback (previous tag)
```

## 6. Implementation plan

| Phase | Scope | Proposed PMO task(s) | Owner |
|---|---|---|---|
| A | Single-entry deploy script with rollback | REL-001 | Coding Agent |

## 7. Risks & mitigations

| Risk | Detection | Mitigation |
|---|---|---|
| Rollback races a running promote | promote lock file present | refuse rollback while lock held |

## 8. Open questions (optional)

- Whether promote should be gated on the flake report (see DESIGN-002).
