# Board — Perry

> Live working memory. Current open work only — closed tasks leave this file.
> History of what happened on a given day: `journal/2026-08/2026-08-16.md`
> Per-task spec / deliverable / audit: `evidence/2026-08/<TASK-ID>-*.md` (P0/P1 always have a `<TASK-ID>-spec.md`)
> Auto-dispatch a task: `/pmo dispatch <TASK-ID>` (requires spec.Dispatch mode = auto)
>
> Last updated: 2026-08-16 (7th pass — all 11 hand-off tasks closed)
> Hard cap: ≤200 lines. If you're over, run `/pmo triage`.
>
> **Bootstrapped 2026-08-16** from the hand-off of DESIGN-001 and DESIGN-002, both
> locked the same day. Every row cites its design phase. Perry has no `OKR.md`, so
> every row is **declared unlinked** — not guessed into a KR.

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## Cadence (recurring; doesn't consume P0 slots)

| ID | Recurring task | Owner | Frequency | Next due | Last evidence |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## User Input Queue

| USER-id | Needed from user | Blocks | Idle | Status |
|---|---|---|---|---|
| USER-001 | Staleness threshold N | TASK-005 | — | **answered 2026-08-16: 30 days** |
| USER-002 | `--claims` vs `--strict` | — | — | **answered 2026-08-16: exempt** |

## Done this period (leaves the board at next triage)

| ID | Title | Evidence |
|---|---|---|
| TASK-001 | Schema: `step:`, 3 step enums, `abandoned`, `declarations[]` + both templates | `schema/state-schema.json`, `state/adoption_dossier_TEMPLATE.md`, `state/diagnosis_TEMPLATE.md` |
| TASK-010 | `claims[]` — 18 paths — + `tests/test_claims.py` (8 tests) | `schema/state-schema.json`, `tests/test_claims.py` |
| TASK-011 | `perry-lint --claims`, outside the `is_adopted()` guard | `bin/perry-lint` |
| TASK-002 | Entry gate: interrupted-run detection, the card, three-way choice; both routes around it guarded | `SKILL.md § Mandatory first move` step 2 |
| TASK-003 | Resume contract (DISCOVERABLE/POSITIONED/LOSSLESS), confirm sub-step table, commit idempotency, one-dossier-per-run | `reference/adoption.md`, `tests/test_resume.py` (17 tests) |
| TASK-012 | Claim check wired into First-time setup as a conditional 3rd question; both prose path lists deleted | `SKILL.md § First-time setup` step 2, `tests/test_claims.py` (13 tests) |
| TASK-004 | `diagnose --resume`, interview/execute sub-steps, restore-point re-validation, re-scan on resume | `reference/diagnose.md`, `tests/test_resume.py` |
| TASK-006 | `perry-state --section interrupted` + two fixtures; the gate now reads a payload instead of eyeballing frontmatter | `bin/perry-state`, `tests/fixtures/interrupted-adoption/`, `tests/test_resume.py` (30 tests) |
| TASK-013 | `NS-01` — scanner, emitter, catalog row, `WHY` entry | `bin/perry-diagnose`, `reference/diagnose.md` |
| TASK-014 | `/perry relocate <path>` — procedure, safety rules, command surface | `SKILL.md`, `tests/test_claims.py` (19 tests) |
| TASK-005 | `step:` cross-field validation + stale-run warning at 30d; block-scalar support in `parse_yaml_subset` | `bin/perry-lint`, `bin/perry-state`, `viewer/parsers.py`, `schema § thresholds` |

## Top risks (one-line; full list in `PROJECT_STATE.md`)

- Perry is half-adopted: `.perry/config.md` exists and flips `is_adopted()`, so lint demands a full state tree it does not have yet. Recorded in ADR-001 as a candidate finding for DESIGN-002.
- Perry trips its own `LOAD-03` (10 decisions queued on the user): 8 unresolved rows in DESIGN-003 plus USER-001/USER-002. The finding is correct; `tests/test_diagnose.py::test_perry_itself_passes_its_own_id_checks` fails until those are decided.
