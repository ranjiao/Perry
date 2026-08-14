# Board — Sample Project

> Live working memory. Current open work only — closed tasks leave this file.
>
> Last updated: 2026-08-14
> Hard cap: ≤200 lines. If you're over, run `/pmo triage`.

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| REL-001 | Deploy script hardening | Coding Agent | in_progress | finish rollback path | evidence/2026-08/REL-001-spec.md |
| REL-002 | Flake detector | Coding Agent | blocked | waiting on USER-014 | evidence/2026-08/REL-002-spec.md |

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| REL-009 | Pipeline docs refresh | PMO Agent | not_started | draft outline | — |

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## Cadence (recurring; doesn't consume P0 slots)

| ID | Recurring task | Owner | Frequency | Next due | Last evidence |
|---|---|---|---|---|---|
| CAD-001 | Friday review | PMO Agent | weekly | 2026-08-15 | weekly/2026-32.md |

## User Input Queue

| USER-id | Needed from user | Blocks | Idle | Status |
|---|---|---|---|---|
| USER-014 | Confirm staging env default | REL-002 | 6d | open |

## Top risks (one-line; full list in `PROJECT_STATE.md`)

- **DEPLOY-FLAKE 4.2%** TOP RISK — staging runs still flaky; blocks the 3-green-runs KR.
