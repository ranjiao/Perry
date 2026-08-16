# Board — Perry

> Live working memory. Current open work only — closed tasks leave this file.
> History of what happened on a given day: `journal/2026-08/2026-08-16.md`
> Per-task spec / deliverable / audit: `evidence/2026-08/<TASK-ID>-*.md` (P0/P1 always have a `<TASK-ID>-spec.md`)
> Auto-dispatch a task: `/pmo dispatch <TASK-ID>` (requires spec.Dispatch mode = auto)
>
> Last updated: 2026-08-16 (4th pass — 6 tasks closed)
> Hard cap: ≤200 lines. If you're over, run `/pmo triage`.
>
> **Bootstrapped 2026-08-16** from the hand-off of DESIGN-001 and DESIGN-002, both
> locked the same day. Every row cites its design phase. Perry has no `OKR.md`, so
> every row is **declared unlinked** — not guessed into a KR.

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-004 | `reference/diagnose.md`: add `--resume`, sub-steps, restore-point re-validation | Coding Agent | not_started | DESIGN-001 phase D — the entry gate already offers Resume on an interrupted diagnosis, but diagnose has no procedure for it. Closing a hole opened by TASK-002. | — |

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-005 | `perry-lint`: validate `step:` against its stage enum; stale-run warning | Coding Agent | not_started | DESIGN-001 phase E — needs the N threshold from DESIGN-001 §8 | — |
| TASK-006 | Fixtures + tests for resume at `confirm/goals` and `commit/board` | Coding Agent | not_started | DESIGN-001 phase F | — |
| TASK-013 | `NS-01` finding: emitter, catalog row, `WHY` entry | Coding Agent | not_started | DESIGN-002 phase D | — |
| TASK-014 | `/perry relocate <path>` subcommand | Coding Agent | not_started | DESIGN-002 phase E — the only remedy now that #2 was taken strictly | — |

## Cadence (recurring; doesn't consume P0 slots)

| ID | Recurring task | Owner | Frequency | Next due | Last evidence |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## User Input Queue

| USER-id | Needed from user | Blocks | Idle | Status |
|---|---|---|---|---|
| USER-001 | Staleness threshold N for the stale-run lint warning (DESIGN-001 §8 — 14d is a guess with no evidence) | TASK-005 | 0d | open |
| USER-002 | Should `--claims` be exempt from `--strict`? (DESIGN-002 §8) | TASK-011 | 0d | open |

## Done this period (leaves the board at next triage)

| ID | Title | Evidence |
|---|---|---|
| TASK-001 | Schema: `step:`, 3 step enums, `abandoned`, `declarations[]` + both templates | `schema/state-schema.json`, `state/adoption_dossier_TEMPLATE.md`, `state/diagnosis_TEMPLATE.md` |
| TASK-010 | `claims[]` — 18 paths — + `tests/test_claims.py` (8 tests) | `schema/state-schema.json`, `tests/test_claims.py` |
| TASK-011 | `perry-lint --claims`, outside the `is_adopted()` guard | `bin/perry-lint` |
| TASK-002 | Entry gate: interrupted-run detection, the card, three-way choice; both routes around it guarded | `SKILL.md § Mandatory first move` step 2 |
| TASK-003 | Resume contract (DISCOVERABLE/POSITIONED/LOSSLESS), confirm sub-step table, commit idempotency, one-dossier-per-run | `reference/adoption.md`, `tests/test_resume.py` (17 tests) |
| TASK-012 | Claim check wired into First-time setup as a conditional 3rd question; both prose path lists deleted | `SKILL.md § First-time setup` step 2, `tests/test_claims.py` (13 tests) |

## Top risks (one-line; full list in `PROJECT_STATE.md`)

- Perry is half-adopted: `.perry/config.md` exists and flips `is_adopted()`, so lint demands a full state tree it does not have yet. Recorded in ADR-001 as a candidate finding for DESIGN-002.
- Perry trips its own `LOAD-03` (10 decisions queued on the user): 8 unresolved rows in DESIGN-003 plus USER-001/USER-002. The finding is correct; `tests/test_diagnose.py::test_perry_itself_passes_its_own_id_checks` fails until those are decided.
