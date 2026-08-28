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
| 2026-08-21 | two test modules import `from tests.X`, and `tests` is a name another project on this machine owns | — |
| 2026-08-21 | the opencode dispatch-cap test reads machine-wide state, so a second suite on the same box turns it red | — |
| 2026-08-21 | the suite's red set changes with the interpreter, so "all green" has never been a portable claim | — |
| 2026-08-21 | the contract-invariance gate records one branch of a union type and calls it the shape | — |
| 2026-08-21 | `status --status blocked` still requires a TASK- dependency, so a row waiting on a USER- ask must use --reason instead | — |
| 2026-08-21 | perry-okr and perry-config write a canonical record file with no claims guard, and perry-tasks risks-write is the only one that refuses | — |
| 2026-08-21 | the v2 delegation prompt carried v1's out-of-scope prose forward unchecked, and it described deleted code | — |
| 2026-08-21 | conformance.missing_projection ships and is documented but no version ever announced it, and key-parity cannot see that | — |
| 2026-08-21 | no test pins the drift severity at warn, so the decision recorded 2026-08-21 has no mechanical guard | — |
| 2026-08-21 | risk-add and risk-clear write the board and the event log but not risks.jsonl, so any imported project drifts on the next risk | — |
| 2026-08-21 | _would_discard's loss refusal in perry-tasks write is unreachable past the --from-board guard above it | — |
| 2026-08-21 | perry-state's hook_profile comment says the schema does not declare the High-stakes prefix and it does | — |
| 2026-08-21 | the dispatch cap leaks a slot under contention: 20 concurrent registers let a third through a cap of 2 | — |
| 2026-08-21 | DESIGN-007 names the goal store perry/goals.jsonl and the file on disk is perry/okr.jsonl | — |
| 2026-08-21 | a wait-loop whose own command line matches the pattern it waits on never exits and poisons every agent's is-a-suite-running check | — |
| 2026-08-21 | the recorded parity baseline drifts with the board: 115/115 fixture against 113/113 live, and nothing catches it | — |
| 2026-08-21 | perry-knowledge/list emits stale without the threshold that produced it, so a consumer must read state-schema.json to name the number | — |
| 2026-08-21 | contract_key_parity's docstring says five contracts and there are six | — |
| 2026-08-21 | perry-dispatch-limit list reports bookkeeping, not observation, so a killed agent holds a slot for four hours and the PMO reports it as running | — |
| 2026-08-21 | viewer/ stops being a viewer once the viewer is deleted, and the two files left in it are the shared read layer | — |
| 2026-08-21 | the report exemption covers dangling but not open_decisions_by_register, so quoting a checker's output re-opens a queue row | — |
| 2026-08-27 | an import-grep cannot see a module that reads another module as text, which is how the viewer deletion nearly broke test_parsers | — |
| 2026-08-27 | perry-state and perry-task both emit intake.oldest_undischarged and mean different things by it — a date string against a row number | — |
| 2026-08-28 | only_an_example short-circuits to 'not an example' for an id with no definition point, so the illustrative rule cannot judge an id lifted out of a report | — |
| 2026-08-28 | two writers appending to .perry/events.jsonl in parallel conflict textually, and the resolution is only safe because seq is computed at read time | — |
| 2026-08-28 | the queue-reconcile test is order/parallel sensitive: it fails under -j 4 and passes in a smaller run | — |
| 2026-08-28 | paths() collapses a list to its first element, so a condition true on krs[1] and false on krs[0] is unobservable to key parity | — |
| 2026-08-28 | perry-state's design.by_status keys come from a set, so the payload's key order flips with the hash seed and cannot be byte-compared | — |
| 2026-08-28 | two agents running tests/parallel write to the same scratchpad baseline path and overwrite each other's readings | — |
| 2026-08-28 | subcommands.md:82 and :118-128 restate contract semantics in prose and carry a TASK-162 marker proving they rot | — |
| 2026-08-28 | bin/perry-state:751 picks a drift baseline as a min over raw ts strings and the new zone guard cannot see it | — |
| 2026-08-28 | load_snapshot binds STATE_ROOT at def time, so perry-state's override can never reach it | — |
| 2026-08-28 | bin/perry-task's ABSENT is a fourth copy of the blank-cell list, so Depends on 待定 parses as a real dependency id | — |
| 2026-08-28 | diagnose and perry-task disagree about open queue rows — 2 vs 0 — and the disagreement rides along on TASK-179's red | — |
| 2026-08-28 | a row can be resolved by work in a repo Perry does not own, and Perry has no signal for it — TASK-161 and TASK-175 in one night | — |
| 2026-08-28 | a KR short of target whose every linked task is terminal is stalled, and nothing reports it — must be phase-scoped or three of four results are noise | — |
| 2026-08-28 | perry-migrate CROSS_FILE_INPUTS omits tasks.jsonl, so linkage-task-exists declines in the dry run's newly-visible delta — one-word fix | — |
| 2026-08-28 | no procedure in work/reference/subcommands.md mentions perry-task purge, so an agent will not reach for it | — |
| 2026-08-28 | perry-decide mint_id reads max(files ∪ index) but render_index rebuilds DECISIONS.md from the files, so the departed half erases itself — deleting the highest ADR hands ADR-003 back, and perry-decide reads the event log zero times | — |
| 2026-08-28 | four docstrings cite a directory on this machine as their evidence — bin/README.md:234, perry-conform:273-274 and :283, perry-goals:459 and :334; three are only fixable because TASK-124 and TASK-125 built the tests to point at | — |
| 2026-08-28 | a mutation sweep killed mid-flight leaves the tree mutated — TASK-147's was SIGTERM'd at a tool cap and its finally never ran, leaving a live mutation in bin/perry_store.py; sweeps should run detached with signal handlers | — |
| 2026-08-28 | render_line's desc.get('escape', True) default is unreachable from production — both builders always set the key | — |
| 2026-08-28 | perry-lint's store-drift census covers tasks.jsonl only — okr.jsonl's 36 records and .perry/config.jsonl are never checked for drift, so ADR-007's guarantee holds for one store of three | — |
| 2026-08-28 | the id scanner excludes fenced blocks but not inline code spans, so a regex in backticks becomes a dangling id — Z0-9 is on today's list and is not an id; fix the false positives before TASK-179's decision is made | — |
| 2026-08-28 | DESIGN-007 decision #4 (KR ids become P002-O3-KR1, locked 2026-08-19) was never implemented — zero traces in code, old form still hardcoded in perry-lint:124 and perry-explain:64, and perry-lint:1122 recovers the phase from the filename precisely because the id does not carry it | — |
| 2026-08-28 | a locked decision that gets no task row does not ship — DESIGN-007's plan went 5-for-5 with rows and 0-for-9 without; decide lock is documented to hand implementation tasks to work and did not | — |
| 2026-08-28 | escalation scan: Files in scope / Deliverable / Out of scope have NO zh alias while High-stakes operations does, so a Chinese-headed spec scans clean — half the pair is internationalised, and gimegime-pmo's document language is 中文 | — |
| 2026-08-28 | escalate_unextractable flags a line with no backtick, not a line that produced no fragment — so a backticked 2-char token like 下单 is silently dropped by the len>2 floor and raises no warning; 18 of 20 Chinese trading verbs affected | — |
| 2026-08-28 | escalation_fragments' len>2 floor is an ASCII assumption: it drops 2-character CJK tokens that are whole words, while _ESC_WORD was deliberately written ASCII-only so CJK WOULD match | — |
| 2026-08-28 | bin/perry-state:1954 scans the FLAT role union and never reads the row's Role: — correct by accident and load-bearing, since narrowing it to the row's own role would break the cross-role seam catch; pin it with a test before someone optimises it | — |
| 2026-08-28 | tasks[].role is typed as one string but a seam row needs two — a coding-owned row whose subject is a live risk cap is accountable to both roles | — |
| 2026-08-28 | DUE-* 日期型强制动作 is unrepresentable by the escalation union in principle: the union fires on a dispatch, and the danger is a dispatch that never happens | — |
| 2026-08-28 | test_host_support flakes under suite contention — third occurrence tonight, merge-check refused to attribute it once and TASK-147's sweep excluded it; it passes 3/3 alone every time | — |
| 2026-08-28 | perry-explain resolves P002-O1-KR1 and P002-O2-KR2 to a table row in TASK-120-spec.md, not to the linkage register — perry/evidence/ walks before perry/phase/ and harvest takes the first definition; 14 of 16 resolve correctly | — |
| 2026-08-28 | green_lit does not de-duplicate across touches sections while refuse does | — |
| 2026-08-28 | a heading with a numbering prefix (## §8. Executor 交付物, which gimegime-pmo uses) does not resolve — _section matches by prefix, so it is equally true of English; a decision rather than a patch | — |
| 2026-08-28 | 下单 still fires on 系统永不下单 — a boundary-free script cannot express polarity, named in the code rather than hidden | — |
| 2026-08-28 | events contract says not to re-sort because second-precision ties are real, which reads as a rounding problem — the real reason is a deliberately backdated stamp twelve hours out of log order | — |
| 2026-08-28 | perry-dispatch-limit exits 0 and prints usage on an unknown subcommand, so every 'acquire' this session was a silent no-op — the subcommand is 'register'; the concurrency cap was enforced by nothing but the caller's own counting | — |
| 2026-08-28 | BOARD.md's Last updated header reads 2026-08-16 while the board is re-rendered dozens of times a day — perry-state reports it as board.last_updated and nothing refreshes it | — |

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on | Track | Stage | Arrived |
|---|---|---|---|---|---|---|---|---|---|---|
| TASK-050 | One normalization for a header cell, not two | Coding Agent | not_started | unblocks on PR #20; re-scope to the adoption reader (parse_board/parse_okr with no store, parse_tracks, read_conformance, parse_phase/parse_decisions) — the fifth hardening round should be a mutation harness, not another regex | — | V4 | TASK-094 | main |  |  |
| TASK-067 | The writer can destroy the table it writes to, and perry-lint cannot see it | Coding Agent | blocked | unblocks on PR #20 but does not become empty: perry-decide still writes DECISIONS.md, perry-goals still writes OKR.md § Commitments in place, perry-migrate still rewrites a stranger files, and ragged-row is still the only catch | evidence/2026-08/TASK-067-finding.md | V4 | TASK-094, TASK-095 | main |  |  |

## P1

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on | Track | Stage | Stage since | Arrived | Parent | Commitment | Role |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TASK-077 | DESIGN-006 F — a finance-shaped role runs one real task end to end | Coding Agent | not_started | DECIDED 2026-08-28 by the user: draft the card first, do not run it yet. Two corrections to this row's own record: (1) the Kind: source-of-truth card type F asks for is ALREADY BUILT — state-schema.json:2112, knowledge-list-contract.md:71, perry-knowledge --kind — decision #6 confirmed 2026-08-17 and it landed with phase A; (2) gimegime-pmo has NOT been migrated to the store (no tasks.jsonl; BOARD.md/OKR.md/DECISIONS.md at the project root), so running there today exercises the legacy markdown shape, which is TASK-097's subject. What actually blocks F is that no non-software role card has ever been written — all three shipped cards are software-shaped and the only pack is software-ops. Card first via TASK-200; the run and the V5 signature stay with the user. | evidence/2026-08/TASK-077-context.md | V5 | TASK-073, TASK-075, TASK-076, TASK-200 | main |  |  |  |  |  |  |
| TASK-095 | Remove the parser for the three stores; keep what adoption needs | Coding Agent | not_started | — | — | V4 | TASK-094 | main |  |  |  |  |  |  |
| TASK-097 | Migrate the two real projects to the store, at V5 | Coding Agent | not_started | — | — | V5 | TASK-092 | main |  |  |  |  |  |  |
| TASK-099 | Sweep bin/, viewer/ and tests/ for document handling that ADR-007 made dead | Coding Agent | not_started | — | — | V4 | TASK-095 | main |  |  |  |  |  |  |
| TASK-129 | Agent is five strings that do not join, and role has never once been written | Coding Agent | not_started | unblocked: work owns .perry/agents.jsonl → .perry/roles/ as of the 2026-08-20 signature; needs a spec, then dispatch | — | V3 | TASK-128 | main |  |  |  |  |  |  |
| TASK-155 | the register updated field carries two facts, so appending an edge silently re-dates every asserted number in the file | Coding Agent | not_started | — | — | V3 |  | intake | triaged |  | 2026-08-21 |  |  |  |
| TASK-173 | an Objective is not a record, so it has no durable address | Coding Agent | not_started | DESIGN-009 drafted 2026-08-21: design/DESIGN-009-the-objective-is-a-record.md. Four User Decisions open — id shape, write-back location, how the five existing objectives get minted, and whether krs[].objective keeps the title. The key finding: the PHASE level already solved this. phase/002-linkage.md states id: O1 and the payload carries it, while okr.objectives[].id is '' for all five — and the contract already says a STATED id is legitimate where a DERIVED one is not | — | V4 | — | main |  |  |  |  |  |  |
| TASK-177 | OKR setting is a ten-field checklist where it should be an elicitation | Coding Agent | not_started | DESIGN-011 drafted 2026-08-21: design/DESIGN-011-the-okr-is-elicited-not-collected.md. Four User Decisions open. Step 2 is the gate — run the question bank against a project with no OKR.md and run the rubric on the output; goal 3 (the rubric surfaces ZERO issues) is measured there or it is not measured | — | V4 | — | main |  |  |  |  |  |  |
| TASK-179 | writing about an id costs a dangling entry, and three records tonight paid it | Coding Agent | not_started | FOURTH INSTANCE, added tonight by me: perry/evidence/2026-08/TASK-132-result.md:28 names WIT-404 while describing the witness fixture, and WIT-404 is DELIBERATELY dangling inside that fixture — an id no register carries is the whole point of it. tests/fixtures/ is illustrative so the fixture's own README does not charge the project; my record does. The dangling list is now TASK-007, TASK-9999, USER-900, USER-902, WIT-404 — five ids, every one of them added by a record describing a checker or a fixture | — | V4 | — | main |  |  |  |  |  |  |
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
| TASK-199 | BOARD.md carries two truth models in one file and nothing marks the boundary | Coding Agent | not_started | — | — | V4 |  | main |  |  |  |  |  |  |
| TASK-202 | the hook side of the escalation union has no not-extractable check at all — only role cards get one | Coding Agent | in_progress | — | — | V3 | — | main |  |  |  |  |  |  |
| TASK-203 | an ordinary write does not update its store, for either the risks or the intake register — one row, both registers | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-204 | Perry has no writer for a migration event, so TASK-180 hand-wrote JSON into an append-only log | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-205 | semantics ships on 2 of 5 payloads, so CONTRACT_TESTED.goals can never go red | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-206 | a write returns no seq, so a poll cannot tell a stale read from a fresh one | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-207 | no compare-and-set on a write, and the board demonstrably moves between a read and a write | Coding Agent | not_started | — | — | V3 | TASK-206 | main |  |  |  |  |  |  |
| TASK-208 | perry-diagnose asks 'is this ask answered' with a word search over free prose, and disagrees with the store in both directions | Coding Agent | not_started | — | — | V3 | TASK-179 | main |  |  |  |  |  |  |

## P2

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on | Track | Stage | Arrived |
|---|---|---|---|---|---|---|---|---|---|---|
| TASK-066 | Split perry-task by subcommand group | Coding Agent | not_started | Re-size the split after the markdown reader, row renderer and cell escaping are gone. | evidence/2026-08/TASK-066-context.md | V4 | TASK-065, TASK-038 | main |  |  |
| TASK-112 | the sign-off drafting guard cannot describe itself, so a true statement about it is refused | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-116 | the mention list is write-only, mislabelled, and two of its carve-outs are unpinned | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-137 | a new queue row is born in the second stage, not the first | Coding Agent | not_started | — | — | V2 |  | main |  |  |
| TASK-139 | a design back-reference lives in a cell the close path clears, so a finished design reports as never handed off | Coding Agent | not_started | — | — | V3 | TASK-102 | intake | triaged | 2026-08-20 |
| TASK-157 | plan-phase still authors the KR block by hand in a file documented as machine-written | Coding Agent | not_started | — | — | V3 |  | intake | triaged | 2026-08-21 |
| TASK-172 | four of six document collections are unreachable through any contract | Coding Agent | not_started | DEFERRED 2026-08-21 by the user: aiMark reads the directories directly for now. THE COST, stated so it is on the record: aiMark then owns a reader of Perry's LAYOUT, and perry relocate moves every claimed path — a consumer holding perry/design/ breaks silently the first time a project moves its state root. aiMark's own document says it did not want this ('a second reader of your layout is the thing this whole integration exists to avoid'); the decision overrides that knowingly | — | V4 | — | main |  |  |
| TASK-198 | ## Cadence becomes a store | Coding Agent | not_started | — | — | V3 |  | main |  |  |

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
