# Board — Perry

> Live working memory. Current open work only — closed tasks leave this file.
> History of what happened on a given day: `journal/2026-08/2026-08-16.md`
> Per-task spec / deliverable / audit: `evidence/2026-08/<TASK-ID>-*.md` (P0/P1 always have a `<TASK-ID>-spec.md`)
> Auto-dispatch a task: `/pmo dispatch <TASK-ID>` (requires spec.Dispatch mode = auto)
>
> Last updated: 2026-08-16 (9th pass — TASK-015 + TASK-018 closed at V3)
> Hard cap: ≤200 lines. If you're over, run `/pmo triage`.
>
> **Bootstrapped 2026-08-16** from the hand-off of DESIGN-001 and DESIGN-002, both
> locked the same day. Every row cites its design phase. Perry has no `OKR.md`, so
> every row is **declared unlinked** — not guessed into a KR.

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-026 | Rewrite `SKILL.md § The hand-off contract` | User + Agent | not_started | DESIGN-003 phase G — unblocked (TASK-015 closed). Lands **first and alone**; needs your V5 sign-off, so it is not agent-closable | `evidence/2026-08/TASK-026-spec.md` |

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-016 | `perry-lint --verification` (advisory) | Coding Agent | not_started | DESIGN-003 phase B — blocked-by TASK-015 | `evidence/2026-08/TASK-016-spec.md` |
| TASK-017 | Rung capture at `close-task` + distribution in `perry-state` | Coding Agent | not_started | DESIGN-003 phase B — blocked-by TASK-016 | `evidence/2026-08/TASK-017-spec.md` |
| TASK-019 | `modes/pipeline.md` | Coding Agent | not_started | DESIGN-003 phase D — blocked-by TASK-018 | `evidence/2026-08/TASK-019-spec.md` |
| TASK-020 | `modes/queue.md` + `BOARD.md § Intake` + triage drain | Coding Agent | not_started | DESIGN-003 phase D — blocked-by TASK-018 | `evidence/2026-08/TASK-020-spec.md` |
| TASK-024 | Extract `packs/software-ops/` from `pmo/reference/` | Coding Agent | not_started | DESIGN-003 phase F — the pack-abstraction test; a failed extraction is a design finding, not a bug | `evidence/2026-08/TASK-024-spec.md` |
| TASK-027 | Lane rename goals/work/decide + aliases | Coding Agent | not_started | DESIGN-003 phase G — blocked-by TASK-026 | `evidence/2026-08/TASK-027-spec.md` |

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-021 | Recurrence register + `OKR.md § Commitments` | Coding Agent | not_started | DESIGN-003 phase D — blocked-by TASK-020 | — |
| TASK-022 | `modes/inquiry.md` | Coding Agent | not_started | DESIGN-003 phase E — blocked-by TASK-018 | — |
| TASK-023 | `SRC-` ids in digests + `perry-lint --provenance` | Coding Agent | not_started | DESIGN-003 phase E — blocked-by TASK-022 | — |
| TASK-025 | Pack loader + display glossary | Coding Agent | not_started | DESIGN-003 phase F — blocked-by TASK-024 | — |
| TASK-028 | diagnose/adopt mode detection + both READMEs | User + Agent | not_started | DESIGN-003 phase G — blocked-by TASK-027 | — |

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
| TASK-015 | Schema: `mode` + `verification_rung` enums, `work_modes`/`verification` blocks, optional `## Tracks` + `## Intake` table specs, i18n columns — **V3** | `schema/state-schema.json`, `tests/test_work_modes.py`; lint output on all 3 fixtures byte-identical to the pre-change baseline, no fixture edited |
| TASK-018 | `modes/project.md` + router step 3b + `perry-state.parse_tracks` — **V3** | `modes/project.md`, `SKILL.md § Mandatory first move` step 3b, `bin/perry-state`; `perry-state --dashboard` byte-identical on all 3 fixtures before/after |

## Top risks (one-line; full list in `PROJECT_STATE.md`)

- Perry is half-adopted: `.perry/config.md` exists and flips `is_adopted()`, so lint demands a full state tree it does not have yet. Recorded in ADR-001 as a candidate finding for DESIGN-002.
- ~~`LOAD-03` (10 decisions queued on the user)~~ — cleared 2026-08-16 when DESIGN-003's 8 rows were decided and USER-001/002 were answered. `bin/perry-diagnose --root .` now reports 0 errors and no `LOAD-*` finding.
- DESIGN-003 phase G rewrites `SKILL.md § The hand-off contract` — the one rule that keeps lanes composable, and `perry-lint` cannot see a bad edit to it. Mitigation is in DESIGN-003 §7: TASK-026 lands first and alone, with V5 sign-off and an ownership-refusal fixture.
