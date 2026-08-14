# OKR — Sample Project

> **Owner**: `okr` skill (only writer). PMO and other skills read for snapshots.
> **Period**: 6 months
> **Status**: Active

Long-term reference for the system.

## Mission

Ship a release pipeline the team trusts without a human in the loop.

## Operating Principles

- No production deploy without a green staging run.
- Auditability before performance.
- Cost stays under the declared ceiling.

## Anti-Goals

- No new paid API integrations this period.
- No untested refactors of the deploy path.

---

## v1: 2026-06-01

### Objective 1 — Make releases boring

Releases should stop being an event.

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O1.1 | Cut median release time | median ≤ 12 min | no | 2026-09-01 |
| KR-O1.2 | Remove manual gates | manual steps = 0 | no | 2026-09-01 |
| KR-O1.3 | Same-day rollback | rollback ≤ 10 min | yes | 2026-09-01 |

### Objective 2 — Trust the signal

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O2.1 | Flake rate down | flaky runs ≤ 1% | no | 2026-09-01 |

<!--
## v2: YYYY-MM-DD
(example block — must not be parsed as the current version)
-->

## Versioning log

- v1: 2026-06-01 — initial draft.
