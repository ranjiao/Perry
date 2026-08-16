# Board — Perry

> Live working memory. Current open work only — closed tasks leave this file.
> History of what happened on a given day: `journal/2026-08/2026-08-16.md`
> Per-task spec / deliverable / audit: `evidence/2026-08/<TASK-ID>-*.md` (P0/P1 always have a `<TASK-ID>-spec.md`)
> Auto-dispatch a task: `/pmo dispatch <TASK-ID>` (requires spec.Dispatch mode = auto)
>
> Last updated: 2026-08-16 (20th pass — round-4 review's 17 findings all closed)
> Hard cap: ≤200 lines. If you're over, run `/pmo triage`.
>
> **Bootstrapped 2026-08-16** from the hand-off of DESIGN-001 and DESIGN-002, both
> locked the same day. Every row cites its design phase. Perry has no `OKR.md`, so
> every row is **declared unlinked** — not guessed into a KR.

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence | Verification |
|---|---|---|---|---|---|---|

## P1

| ID | Title | Owner | Status | Next action | Evidence | Verification |
|---|---|---|---|---|---|---|
| TASK-019 | `modes/pipeline.md` | Coding Agent | in_progress | **V4 review FAILED** — 3 blocking (stage has no column; WIP limit has no home or default; Commitments has no track key/owner). Fix B1+B3, then re-review | `evidence/2026-08/TASK-019-020-v4-review.md` | V4 |
| TASK-020 | `modes/queue.md` + `BOARD.md § Intake` + triage drain | Coding Agent | in_progress | **V4 review FAILED** — 3 blocking (stage has no column; `Arrived` is destroyed on routing so SLA triage is uncomputable; Commitments ownership). Fix B1+B2, then re-review | `evidence/2026-08/TASK-019-020-v4-review.md` | V4 |
| TASK-027 | Lane rename goals/work/decide + aliases | Coding Agent | review | Round-3 review FAILED it: router named 3 dead dirs, routed `decide` to the wrong lane, quoted withdrawn commands. All fixed + `TestRouterNamesOnlyRealThings`. **4th review pending** | `evidence/2026-08/TASK-027-spec.md` | V4 |

## P2

| ID | Title | Owner | Status | Next action | Evidence | Verification |
|---|---|---|---|---|---|---|
| TASK-021 | Recurrence register + `OKR.md § Commitments` | Coding Agent | not_started | DESIGN-003 phase D — blocked-by TASK-020 | — | V4 |
| TASK-028 | diagnose/adopt mode detection + both READMEs | User + Agent | not_started | DESIGN-003 phase G — blocked-by TASK-027 | — | V5 |

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
| TASK-025 | Pack loader + display glossary — `Packs:` config field, `packs` contract, router step 3c — **V3** | `bin/perry-state.load_packs`, `schema § packs`, `SKILL.md` step 3c, `packs/software-ops/pack.md § Glossary`; `tests/…::TestPackGlossary` (6 tests) |
| TASK-022 | `modes/inquiry.md` — question tree via `Parent`, answer files, provenance as the mode's test suite — **V3** (rung lowered from V4, see journal) | `modes/inquiry.md`, `tests/…::TestInquiryHasDataForEveryControl` (5 tests); every column it relies on verified present in the schema |
| TASK-023 | `SRC-` ids + `knowledge/` schema entry + `perry-lint --provenance` — **V3** | `bin/perry-lint`, `schema/state-schema.json`, `work/state/digest_TEMPLATE.md`, `work/reference/digests.md`; `tests/…::TestProvenanceLint` (6 tests, all four failure modes + empty scan) |
| TASK-026 | Rewrite `SKILL.md § The hand-off contract` — goals/work/decide ownership, both moves, 3 refusal cases — **V5** | `SKILL.md § The hand-off contract` (signed Ran Jiao 2026-08-16), `tests/test_ownership.py` (13 tests) |
| TASK-024 | `packs/software-ops/` — architecture/runbooks/incidents extracted, **0 content edits**; `git-boundaries.md` kept in core; OKR phase gate made pack-conditional — **V3** (rung lowered from V4, see journal) | `packs/software-ops/`, `packs/software-ops/pack.md`, `goals/reference/phases.md`; `git diff` vs pre-move = 0 lines on all three, 0 stale refs, lint clean |
| TASK-018 | `modes/project.md` + router step 3b + `perry-state.parse_tracks` — **V3** | `modes/project.md`, `SKILL.md § Mandatory first move` step 3b, `bin/perry-state`; `perry-state --dashboard` byte-identical on all 3 fixtures before/after |
| TASK-016 | `perry-lint --verification` — missing rung, unsatisfiable rung, and high-stakes rows closed below V5 — **V3** | `bin/perry-lint`, `tests/test_work_modes.py::TestVerificationLint` (11 tests incl. the empty-scan case) |
| TASK-017 | Rung capture at `close-task` + `board.verification` distribution + standup row — **V3** | `viewer/parsers.py`, `bin/perry-state`, `work/reference/subcommands.md § close-task` gate 3, `work/SKILL.md`; `tests/…::TestRungDistribution` (5 tests) |

## Top risks (one-line; full list in `PROJECT_STATE.md`)

- Perry is half-adopted: `.perry/config.md` exists and flips `is_adopted()`, so lint demands a full state tree it does not have yet. Recorded in ADR-001 as a candidate finding for DESIGN-002.
- ~~`LOAD-03` (10 decisions queued on the user)~~ — cleared 2026-08-16 when DESIGN-003's 8 rows were decided and USER-001/002 were answered. `bin/perry-diagnose --root .` now reports 0 errors and no `LOAD-*` finding.
- The V4 review found `OKR.md § Commitments` is written by two modes that disclaim the goals cascade, with no declared owner. That is a hand-off-contract question, so TASK-026 now blocks phase D as well as phase G.
- DESIGN-003 phase G rewrites `SKILL.md § The hand-off contract` — the one rule that keeps lanes composable, and `perry-lint` cannot see a bad edit to it. Mitigation is in DESIGN-003 §7: TASK-026 lands first and alone, with V5 sign-off and an ownership-refusal fixture.
