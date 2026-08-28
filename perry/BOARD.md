# Board — Perry

> Live working memory. Current open work only — closed tasks leave this file.
> History of what happened on a given day: `journal/2026-08/2026-08-16.md`
> Per-task spec / deliverable / audit: `evidence/2026-08/<TASK-ID>-*.md` (P0/P1 always have a `<TASK-ID>-spec.md`)
> Auto-dispatch a task: `/pmo dispatch <TASK-ID>` (requires spec.Dispatch mode = auto)
>
> Last updated: 2026-08-16 (21st pass — DESIGN-004 handed off, 6 tasks)
> Hard cap: ≤200 lines. If you're over, run `/pmo triage`.
>
> **Bootstrapped 2026-08-16** from the hand-off of DESIGN-001 and DESIGN-002, both
> locked the same day. Every row cites its design phase. Perry has no `OKR.md`, so
> every row is **declared unlinked** — not guessed into a KR.

## Intake

| Arrived | Request | Outcome |
|---|---|---|

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on | Track | Stage | Arrived | Stage since | Parent | Commitment | Role |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TASK-050 | One normalization for a header cell, not two | Coding Agent | not_started | unblocks on PR #20; re-scope to the adoption reader (parse_board/parse_okr with no store, parse_tracks, read_conformance, parse_phase/parse_decisions) — the fifth hardening round should be a mutation harness, not another regex | — | V4 | TASK-094 | main |  |  |  |  |  |  |
| TASK-067 | The writer can destroy the table it writes to, and perry-lint cannot see it | Coding Agent | blocked | unblocks on PR #20 but does not become empty: perry-decide still writes DECISIONS.md, perry-goals still writes OKR.md § Commitments in place, perry-migrate still rewrites a stranger files, and ragged-row is still the only catch | evidence/2026-08/TASK-067-finding.md | V4 | TASK-094, TASK-095 | main |  |  |  |  |  |  |

## P1

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on | Track | Stage | Stage since | Arrived | Parent | Commitment | Role |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TASK-077 | DESIGN-006 F — a finance-shaped role runs one real task end to end | Coding Agent | not_started | Startable — all four dependencies are done. Write the first non-software role card (the real blocker; every shipped card is software-shaped). Decision and the two record corrections: evidence/2026-08/TASK-077-notes.md. The run and the V5 signature stay with the user. | evidence/2026-08/TASK-077-context.md | V5 | TASK-073, TASK-075, TASK-076, TASK-200 | main |  |  |  |  |  |  |
| TASK-095 | Remove the parser for the three stores; keep what adoption needs | Coding Agent | in_progress | dispatched to claude-subagent 2026-08-28; awaiting RESULT | — | V4 | TASK-094 | main |  |  |  |  |  |  |
| TASK-097 | Migrate the two real projects to the store, at V5 | Coding Agent | not_started | — | — | V5 | TASK-092 | main |  |  |  |  |  |  |
| TASK-099 | Sweep bin/, viewer/ and tests/ for document handling that ADR-007 made dead | Coding Agent | not_started | — | — | V4 | TASK-095 | main |  |  |  |  |  |  |
| TASK-129 | Agent is five strings that do not join, and role has never once been written | Coding Agent | not_started | unblocked: work owns .perry/agents.jsonl → .perry/roles/ as of the 2026-08-20 signature; needs a spec, then dispatch | — | V3 | TASK-128 | main |  |  |  |  |  |  |
| TASK-155 | the register updated field carries two facts, so appending an edge silently re-dates every asserted number in the file | Coding Agent | not_started | Promoted to P1 on 2026-08-28 for breaching the intake track's 5d SLA. The row arrived from intake carrying a title and nothing else — no summary, deliverable or verification — so the first step is to investigate the defect and write evidence/2026-08/TASK-155-spec.md, which subcommands.md:708 requires of every P0/P1 row. | — | V3 | — | intake | triaged |  | 2026-08-21 |  |  |  |
| TASK-173 | an Objective is not a record, so it has no durable address | Coding Agent | not_started | DESIGN-009 drafted 2026-08-21: design/DESIGN-009-the-objective-is-a-record.md. Four User Decisions open — id shape, write-back location, how the five existing objectives get minted, and whether krs[].objective keeps the title. The key finding: the PHASE level already solved this. phase/002-linkage.md states id: O1 and the payload carries it, while okr.objectives[].id is '' for all five — and the contract already says a STATED id is legitimate where a DERIVED one is not | — | V4 | TASK-181, TASK-182, TASK-183, TASK-184, TASK-185 | main |  |  |  |  |  |  |
| TASK-177 | OKR setting is a ten-field checklist where it should be an elicitation | Coding Agent | not_started | DESIGN-011 drafted 2026-08-21: design/DESIGN-011-the-okr-is-elicited-not-collected.md. Four User Decisions open. Step 2 is the gate — run the question bank against a project with no OKR.md and run the rubric on the output; goal 3 (the rubric surfaces ZERO issues) is measured there or it is not measured | — | V4 | TASK-190, TASK-191, TASK-192, TASK-193, TASK-194 | main |  |  |  |  |  |  |
| TASK-179 | writing about an id costs a dangling entry, and three records tonight paid it | Coding Agent | not_started | Startable — TASK-210 is done. Decide the rule for the five dangling ids, then make the reconcile test assert that decision: widen the report mark beyond the paragraph, exempt evidence records wholesale, or accept the cost in writing. The list and its shape: evidence/2026-08/TASK-179-notes.md. | evidence/2026-08/TASK-179-notes.md | V4 | TASK-210 | main |  |  |  |  |  |  |
| TASK-181 | D009 step 1 — objective rows exist in okr.jsonl, with no id yet | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-182 | D009 step 2 — perry-okr render rebuilds OKR.md byte-for-byte from objective records | Coding Agent | not_started | — | — | V3 | TASK-181 | main |  |  |  |  |  |  |
| TASK-183 | D009 step 3 — the O-1 mint and the write-back to the store | Coding Agent | not_started | — | — | V3 | TASK-182 | main |  |  |  |  |  |  |
| TASK-184 | D009 step 4 — okr.objectives[].id is filled from the store and the contract moves to 2.2 | Coding Agent | not_started | — | — | V3 | TASK-183 | main |  |  |  |  |  |  |
| TASK-185 | D009 step 5 — an Objective id survives a rename and a reorder, proved | Coding Agent | not_started | — | — | V3 | TASK-184 | main |  |  |  |  |  |  |
| TASK-186 | D010 step 2 — a spec declares its author, and the escalation scan reports it | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-187 | D010 step 3 — a machine-authored spec is fail-closed at the escalation gate | Coding Agent | not_started | — | — | V3 | TASK-186 | main |  |  |  |  |  |  |
| TASK-188 | D010 step 4 — the scout, run by hand on ten real rows and scored against what the PMO actually decided | Coding Agent | not_started | — | — | V4 | TASK-187 | main |  |  |  |  |  |  |
| TASK-189 | D010 step 5 — autopilot becomes the two-stage scout-then-build loop | Coding Agent | not_started | — | — | V4 | TASK-188 | main |  |  |  |  |  |  |
| TASK-190 | D011 step 1 — a question bank for the first-ever-OKR route | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-191 | D011 step 2 — a real transcript, scored by the rubric that stays unchanged | Coding Agent | not_started | — | — | V4 | TASK-190 | main |  |  |  |  |  |  |
| TASK-192 | D011 step 3 — routing and smart-skip, by track spine | Coding Agent | not_started | — | — | V3 | TASK-191 | main |  |  |  |  |  |  |
| TASK-193 | D011 step 4 — the escape hatch and the premise challenge | Coding Agent | not_started | — | — | V3 | TASK-191 | main |  |  |  |  |  |  |
| TASK-194 | D011 step 5 — plan-phase uses the same question bank | Coding Agent | not_started | — | — | V3 | TASK-191 | main |  |  |  |  |  |  |
| TASK-199 | BOARD.md carries two truth models in one file and nothing marks the boundary | Coding Agent | not_started | — | — | V4 | TASK-196, TASK-197, TASK-198 | main |  |  |  |  |  |  |
| TASK-203 | an ordinary write does not update its store, for either the risks or the intake register — one row, both registers | Coding Agent | not_started | pre-flight clean and Executor: claude-subagent, but the concurrency cap is 2/2 (TASK-095, TASK-209 in flight). Queued — dispatch when a slot frees. | — | V3 | — | main |  |  |  |  |  |  |
| TASK-204 | Perry has no writer for a migration event, so TASK-180 hand-wrote JSON into an append-only log | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-206 | a write returns no seq, so a poll cannot tell a stale read from a fresh one | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-207 | no compare-and-set on a write, and the board demonstrably moves between a read and a write | Coding Agent | not_started | — | — | V3 | TASK-206 | main |  |  |  |  |  |  |
| TASK-208 | perry-diagnose asks 'is this ask answered' with a word search over free prose, and disagrees with the store in both directions | Coding Agent | not_started | — | — | V3 | TASK-179 | main |  |  |  |  |  |  |
| TASK-209 | perry-lint's store-drift census covers tasks.jsonl only, so ADR-007's guarantee holds for one store of five | Coding Agent | in_progress | dispatched to claude-subagent 2026-08-28; awaiting RESULT | — | V3 | — | main |  |  |  |  |  |  |
| TASK-211 | perry-dispatch-limit exits 0 on an unknown subcommand, so a typo silently disables the concurrency cap | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-212 | a locked decision that gets no task row does not ship, and nothing links a design's plan step to the work that discharges it | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-216 | the foreign-write guard scans reference pages only, and misses the third-person verb a summary table uses | Coding Agent | not_started | — | evidence/2026-08/TASK-216-spec.md | V3 | — | main |  |  |  |  |  |  |
| TASK-217 | four pages disagree on whether the retro is written before or after score-phase | Coding Agent | not_started | — | evidence/2026-08/TASK-217-spec.md | V3 | — | main |  |  |  |  |  |  |
| TASK-218 | thread the closing phase id through every close stage, so no stage re-reads phase/CURRENT | Coding Agent | not_started | — | evidence/2026-08/TASK-218-spec.md | V4 | TASK-217 | main |  |  |  |  |  |  |
| TASK-220 | the close-phase router subcommand, over the four unchanged lane subcommands | Coding Agent | not_started | — | evidence/2026-08/TASK-220-spec.md | V4 | TASK-217, TASK-218 | main |  |  |  |  |  |  |
| TASK-221 | a phase close that stopped halfway is visible at the next snapshot, resolved from state | Coding Agent | not_started | — | evidence/2026-08/TASK-221-spec.md | V3 | TASK-217 | main |  |  |  |  |  |  |
| TASK-226 | a row entered .perry/conformance.md with neither of its two documented writers running | Coding Agent | not_started | — | evidence/2026-08/TASK-226-spec.md | V4 | — | main |  |  |  |  |  |  |
| TASK-139 | a design back-reference lives in a cell the close path clears, so a finished design reports as never handed off | Coding Agent | not_started | Promoted to P1 on 2026-08-28 for breaching the intake track's 5d SLA. The row arrived from intake carrying a title and nothing else — no summary, deliverable or verification — so the first step is to investigate the defect and write evidence/2026-08/TASK-139-spec.md, which subcommands.md:708 requires of every P0/P1 row. | — | V3 | TASK-102 | intake | triaged |  | 2026-08-20 |  |  |  |
| TASK-157 | plan-phase still authors the KR block by hand in a file documented as machine-written | Coding Agent | not_started | Promoted to P1 on 2026-08-28 for breaching the intake track's 5d SLA. The row arrived from intake carrying a title and nothing else — no summary, deliverable or verification — so the first step is to investigate the defect and write evidence/2026-08/TASK-157-spec.md, which subcommands.md:708 requires of every P0/P1 row. | — | V3 | — | intake | triaged |  | 2026-08-21 |  |  |  |
| TASK-229 | no store and clean are different answers, and that has been measured for two of six stores | Coding Agent | not_started | — | evidence/2026-08/TASK-229-spec.md | V3 | TASK-209 | main |  |  |  |  |  |  |
| TASK-219 | retro-cites-phase-scores — a cross_file check that the retro cites the scores rather than re-deriving them | Coding Agent | not_started | — | evidence/2026-08/TASK-219-spec.md | V3 | — | main |  |  |  |  |  |  |

## P2

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on | Track | Stage | Arrived |
|---|---|---|---|---|---|---|---|---|---|---|
| TASK-066 | Split perry-task by subcommand group | Coding Agent | not_started | Re-size the split after the markdown reader, row renderer and cell escaping are gone. | evidence/2026-08/TASK-066-context.md | V4 | TASK-065, TASK-038 | main |  |  |
| TASK-112 | the sign-off drafting guard cannot describe itself, so a true statement about it is refused | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-116 | the mention list is write-only, mislabelled, and two of its carve-outs are unpinned | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-137 | a new queue row is born in the second stage, not the first | Coding Agent | not_started | — | — | V2 |  | main |  |  |
| TASK-172 | four of six document collections are unreachable through any contract | Coding Agent | not_started | DEFERRED 2026-08-21 by the user: aiMark reads the directories directly for now. THE COST, stated so it is on the record: aiMark then owns a reader of Perry's LAYOUT, and perry relocate moves every claimed path — a consumer holding perry/design/ breaks silently the first time a project moves its state root. aiMark's own document says it did not want this ('a second reader of your layout is the thing this whole integration exists to avoid'); the decision overrides that knowingly | — | V4 | — | main |  |  |
| TASK-198 | ## Cadence becomes a store | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-213 | bin/perry-task's ABSENT is a fourth copy of the blank-cell list, so 'Depends on: 待定' parses as a real dependency id | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-214 | perry-decide's mint_id reads max(files ∪ index) but render_index rebuilds the index from the files, so the departed half erases itself | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-215 | BOARD.md's Last updated header is twelve days stale while the file is re-rendered dozens of times a day | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-222 | score-phase's own snapshots trip NS-01, because the names it writes do not match the declared pattern | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-223 | the conformance gate cannot tell a file Perry generated from one it found, so authored files need a hand declare | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-224 | linkage-kr-exists fires only on an absent id, so a KR nested under the wrong objective lints clean | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-225 | decide/SKILL.md:220 specifies a design index that nothing renders | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-227 | the unlinked declaration path validates nothing, at the writer or at the linter | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-228 | attribution reports a declared-unlinked row in the unresolved bucket too, so the standup number counts it twice | Coding Agent | not_started | — | — | V3 |  | main |  |  |

## Cadence (recurring; doesn't consume P0 slots)

| ID | Recurring task | Owner | Frequency | Next due | Last evidence |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## User Input Queue

| USER-id | Needed from user | Blocks | Idle | Status | Asked |
|---|---|---|---|---|---|
| USER-001 | Staleness threshold N | TASK-005 | — | **answered 2026-08-16: 30 days** |  |
| USER-002 | `--claims` vs `--strict` | — | — | **answered 2026-08-16: exempt** |  |
| USER-003 | Please confirm whether Perry may make tasks.jsonl the authoritative Task record, with BOARD.md becoming a generated view whose direct edits are reported instead of accepted. | TASK-038 |  | answered 2026-08-20: Already decided in ADR-007 decision 2 on 2026-08-19 (Deciders: Ran Jiao): BOARD.md becomes rendered output and a hand edit becomes drift. This row was minted the same day and duplicates that decision; recorded here so the queue matches the record. TASK-038 is unblocked, and still needs its V5 signature, which is a different act from this permission. | 2026-08-19 |
| USER-004 | When migration encounters a file the user has chmod-ed read-only, should it refuse to touch that file, or migrate it and name the overridden permission in the plan? Today it migrates silently: write_atomic renames over the target, and a rename needs write permission on the directory, not on the file. | TASK-079 |  | answered 2026-08-20: Migrate and name the override; do not refuse. Reasoning recorded because the row was minted for it: refusing would block a whole migration for a reason unrelated to shape, and migration is the one road ADR-004 gives an undeclared project — a refusal there is the wall with no door that this project rejects everywhere else. The override is also reversible: the restore point carries the file's original bytes, verified under TASK-079. The 'at least name it' half of the ADR-004 posture is already satisfied by what shipped in PR #6, and TASK-115 added the guard that keeps that wording an observation rather than advice. The read-only bit stays a signal Perry reports and does not act on. | 2026-08-20 |
| USER-015 | hand perry/evidence/2026-08/TASK-114-delegation-prompt.md to an aiMark coding agent and paste its result back | TASK-114 |  | answered 2026-08-21: aiMark agent ran the v2 prompt and returned 2026-08-21. CONTRACT_TESTED is {task 1.14, goals 2.1, decide 1.0}; suite 672 pass / 0 fail verified here. Four findings came back, all four check out — see evidence/2026-08/TASK-114-result.md | 2026-08-21 |
| USER-016 | declare risks.jsonl in schema/state-schema.json § claims — {"path": "risks.jsonl", "kind": "file", "owner": "work", "anchor": "state"} — so perry-tasks risks-write --from-board can be enabled | TASK-040 |  | answered 2026-08-21: declared 2026-08-21: claims[] now carries okr.jsonl (goals/state), risks.jsonl (work/state) and .perry/config.jsonl (perry/project). The declaration alone does not enable risks-write — cmd_risks_write was never built; the refusal now reads the claim and names the gap that is actually open | 2026-08-21 |
| USER-903 | Should .perry/config.md become a rendered projection of .perry/config.jsonl? Running 'perry-config write --from-file' costs one command and moves P002-O1-KR2 from 1 of 2 to 2 of 2. The cost: a hand edit to your own config file becomes reported drift at warn. SKILL.md promises this file is 'a tier-1 file the user owns and edits directly' — OKR.md was never promised that, which is why the OKR half was uncontroversial. TASK-092 shipped the capability and deliberately left the store uncreated so the promise is not broken until you choose. See evidence/2026-08/2026-08-28-a-kr-with-no-open-task.md | — |  | answered 2026-08-28: 决定 2026-08-28：变。跑 perry-config write --from-file，.perry/config.md 成为 .perry/config.jsonl 的渲染投影，手改被报成 drift（warn）。这是对 SKILL.md「这是你手写的一等文件」承诺的有意修改，由用户做出。P002-O1-KR2 因此可以从 1/2 走到 2/2。迁移命令由用户执行，不由 Perry 代跑。 | 2026-08-28 |

## Done this period (leaves the board at next triage)

| ID | Title | Evidence |
|---|---|---|

## Top risks (one-line; full list in `PROJECT_STATE.md`)

| ID | Risk | Opened | Status |
|---|---|---|---|
| RX-001 | Perry is half-adopted: `.perry/config.md` exists and flips `is_adopted()`, so lint demands a full state tree it does not have yet. Recorded in ADR-001 as a candidate finding for DESIGN-002. |  | open |
| RX-002 | ~~`LOAD-03` (10 decisions queued on the user)~~ — cleared 2026-08-16 when DESIGN-003's 8 rows were decided and USER-001/002 were answered. `bin/perry-diagnose --root .` now reports 0 errors and no `LOAD-*` finding. |  | cleared 2026-08-16 |
| RX-003 | The V4 review found `OKR.md § Commitments` is written by two modes that disclaim the goals cascade, with no declared owner. That is a hand-off-contract question, so TASK-026 now blocks phase D as well as phase G. |  | open |
| RX-004 | DESIGN-003 phase G rewrites `SKILL.md § The hand-off contract` — the one rule that keeps lanes composable, and `perry-lint` cannot see a bad edit to it. Mitigation is in DESIGN-003 §7: TASK-026 lands first and alone, with V5 sign-off and an ownership-refusal fixture. |  | open |
