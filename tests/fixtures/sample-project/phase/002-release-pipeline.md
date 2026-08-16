# Phase #002 — release-pipeline

> **Owner**: `okr` skill (only writer). PMO reads this every standup.
> **Started**: 2026-08-01
> **Status**: active
> **Source**: `OKR.md` v1

## Phase Focus

This phase is the release pipeline. It does NOT touch the recommender, which is deferred to the next phase.

## Operating Rules

- Agent autonomy: refactors inside `pipeline/` without asking.
- User authorization required for: production deploys, credential rotation.

## Cost Ceiling (phase #002)

- Spend cap: ≤ $200 (model inference).
- Soft fallback at 80% ($160): drop to the small model for verification runs.
- Wiring status: doc-only ⚠ (no code guard yet).

## User Commitments

- Provide the current release-pipeline config at phase start.
- Phase-scoring participation.

## User-Unavailable Degradation

If user input is missing for >5 calendar days, PMO continues with REL-002 → REL-003.

## Phase Scope Reduction Rule

- **Phase-day trigger**: If by phase day 14 USER-014 is still open, Objective 2 automatically collapses to its single Must-Have deliverable.
- **KR-progress trigger**: If at phase day 14, commit KRs are <50% achieved, scope cuts to the named Must-Haves below.

---

## Objective 1 — Automate the deploy path

Remove every manual step between merge and production.

### Key Results

| Id | KR text | Metric / Target | Linked overall KR |
|----|---------|-----------------|---------------------|
| P-O1.1 | Deploy script green in staging | 3 consecutive green runs | KR-O1.1 |
| P-O1.2 | Manual gates removed | manual steps = 0 | KR-O1.2 |

### Projects (seed for PMO TASK-IDs)

- **REL-001 — Deploy script hardening**
  - Owner: Coding Agent
  - Deliverable: `deploy.sh` with rollback
  - Verification: `bash deploy.sh --dry-run` exits 0

---

## Objective 2 — Make the signal trustworthy

### Key Results

| Id | KR text | Metric / Target | Linked overall KR |
|----|---------|-----------------|---------------------|
| P-O2.1 | Flake rate measured and reduced | flaky runs ≤ 1% | KR-O2.1 |

### Projects

- **REL-002 — Flake detector**
  - Owner: Coding Agent
  - Deliverable: `tools/flake_report.py`
  - Verification: `pytest tests/tools/ -q` passes

---

## Definition of Done

### Must-Have (failure = phase missed)

- [ ] `deploy.sh` green in staging 3× consecutively (REL-001)

### Nice-to-Have (failure allowed; explained in retro)

- [ ] Rollback drill recorded

## Not Doing in this phase

- No multi-region this phase; single-region only.

## Process Note

PMO cadence is owned by the `pmo` skill.

## Changes / Pivots

- 2026-08-05 — narrowed O2 to detection only — reason: measurement first.

## Mid-phase check

- **Pace**: on-pace
- **Scope-reduction rule status**: armed
