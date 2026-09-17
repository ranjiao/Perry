# Snapshot details — captured normal repository state

Source: `compact.json`, `next.json`, captured with `bin/perry-state --compact` and `bin/perry-state --section next` in `/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/task-446`; compact generated_at `2026-09-17T16:39:09`. State root is that checkout's `perry/`. This is a capture of the pinned checkout, not a claim about later main. Titles resolved by `bin/perry-explain`, retained in the corresponding ID.txt files. Active software-ops glossary maps Phase to Phase and Commitment to Key result; no vocabulary changes needed here.

Overall OKR v4: 2026-09-15. Period, elapsed/total days and overall percentages: — (not supplied). Overall objectives:
- The user always knows where the project stands and what to do next — progress unknown.
- The skill is the product: plans are asked for, drafted and approved — progress unknown.
- Changing Perry stays cheap, and its architecture stays where the user put it — progress unknown.
- Perry is used for real outside its own repository — progress unknown.

Phase 004-guided, active, started 2026-09-15, day 3, 12 KRs. Objective titles:
- The user always knows where they are and what to do next — completion unknown.
- Plans are asked for, drafted and approved — completion unknown.
- What the user reads and decides fits on one screen, and is recorded — completion unknown.
- Changing Perry gets cheaper, and its architecture holds — completion unknown.

No phase current is asserted: total 12, asserted 0, unasserted 12, measured 0, stale 0. No KR-done count or percentage is inferred. Declared cost: “Spend cap: **$0** in new paid APIs, models or infra. Perry stays stdlib Python.” Wiring is doc-only; the capture also says the cost this phase measures is iteration time (`tests/durations.json`). Spent: —; no measured cost in this payload.

Open tasks 99: P0 0, P1 64, P2 35; blocked 2. Pending user decisions 3 (all requests retained):
- USER-952 “KR revision scope”: TASK-264 D3 has no append-only KR supersession/withdrawal representation. Land check/measure and leave D3 blocked for separate design, or authorize this round to design and implement typed KR revisions/withdrawals with the required schema and reader changes? Asked 2026-09-16; oldest idle_days 1; blocks TASK-264 “DESIGN-022 B — goals writes KR records, their checks and their measurements”.
- USER-955 “Real interview project”: TASK-191 assumed SkyTonight had no OKR, but doc/perry/OKR.md is active. Choose another no-OKR real project for the interview or allow isolated fixtures first while retaining the real interview as incomplete. Asked 2026-09-17; blocks TASK-191 “DESIGN-020 phase C — the SkyTonight interview, scored by the unchanged rubric”. Idle: —.
- USER-958 “Architecture V5 sign-off”: V5 sign-off for reviewed TASK-451 candidate 232c3e92: code-root architecture claim, explicit module cap 600, shared lint/cost resolver. V4 and architecture PASS; 4299 affected tests and mutation proof pass. See TASK-451-delivery/candidate.diff and TASK-451-review/review.md. Accept on report, specify items personally checked, or defer. Full/slow merged acceptance remains required before integration. Asked 2026-09-17; blocks TASK-451 “DESIGN-017 A1 — the schema anchors the architecture document at the code root”. Idle: —. These are captured request claims, not this executor's verification.

Risk RX-003 “The V4 review found `OKR.md § Commitments` is written by two modes that disclaim the goals cascade, with no declared owner. That is a hand-off-contract question, so TASK-026 now blocks phase D as well as phase G.” Referenced TASK-026: “Rewrite `SKILL.md § The hand-off contract` — goals/work/decide ownership, both moves, 3 refusal cases — **V5**”.
Last decision ADR-021 “OKR v4 consolidates to four Objectives and withdraws the roles Objective”, 2026-09-15.
Last weekly 2026-W38 (age —); last handoff 2026-09-15, 2d ago.

Selector position, in returned order: OKR v4: 2026-09-15 done; Phase 004, day 3 done; 2026-W38 plan unknown; last weekly 2026-W38 done.
Primary: /perry work triage — 2 queue item(s) are past their SLA, the longest-waiting being TASK-270 “perry-config unset can empty the config store at exit 0, after which every writer refuses with a false cause and perry-lint calls the store valid”.
Alternate: /perry decide handoff DESIGN-013 — DESIGN-013 is a locked design with no implementation tasks yet (9 such design(s)). DESIGN-013 title: “A fact with a schema lives in the store; a document holds what has none”.
Unknown causes, in returned order:
- drafts.drafted — plan drafts have no source until TASK-444 builds them.
- phase.kr_progress.met_ratio — 12 of 12 commit key results in phase 004 lack declared checks or required check measurements.
- week.planned — week plans have no source until TASK-444 records a finalized week.
- commitments.due — perry-state does not compute which commitments are due.
- phase.days_since_snapshot — perry-state computes no date for the last phase snapshot.
TASK-444 title: “DESIGN-020 phase D — a planning draft survives interruption and is finalized through tools”.

The already authorized implementation continues; this captured recommendation does not authorize switching to triage.

Supplied phase KR measures (all currents null/unknown; null target means absent, not zero):
- P004-O1-KR1 “Fixture states for which `perry-state --section next` yields the expected primary rule”: current unknown, target 5.
- P004-O1-KR2 “State-changing subcommands whose procedure carries the closing step, as a guard enumerates them”: current unknown, target absent.
- P004-O1-KR3 “Cadence lag on this repository while phase 004 is active”: current unknown, target absent.
- P004-O2-KR1 “Issues `reference/input-quality.md § 1` surfaces on the OKR produced by the first-OKR interview on `~/proj/SkyTonight`”: current unknown, target 0.
- P004-O2-KR2 “Hand appends to `okr.jsonl` or `linkage.jsonl` after the `goals` KR writer lands”: current unknown, target 0.
- P004-O2-KR3 “Planning-draft behaviours shown on a fixture”: current unknown, target 2.
- P004-O3-KR1 “Size of the rendered `/perry` snapshot”: current unknown, target absent.
- P004-O3-KR2 “User decisions made during phase 004 that have a `USER-` record in `asks.jsonl`”: current unknown, target absent.
- P004-O3-KR3 “90th-percentile length of an open row's Next action”: current unknown, target 400.
- P004-O4-KR1 “Test time per executor round, and the suite's total”: current unknown, target absent.
- P004-O4-KR2 “`DESIGN-017` structural rules running before merge, each shown red under its mutation”: current unknown, target 7. DESIGN-017 title: “The architecture document is written by the agent and decided by the user”.
- P004-O4-KR3 “L2 reference pages over the 32,768-byte tier budget”: current unknown, target 0.
