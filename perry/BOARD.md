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

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on | Track | Stage | Arrived |
|---|---|---|---|---|---|---|---|---|---|---|
| TASK-050 | One normalization for a header cell, not two | Coding Agent | blocked | unblocks on PR #20; re-scope to the adoption reader (parse_board/parse_okr with no store, parse_tracks, read_conformance, parse_phase/parse_decisions) — the fifth hardening round should be a mutation harness, not another regex | — | V4 | TASK-094 | main |  |  |
| TASK-067 | The writer can destroy the table it writes to, and perry-lint cannot see it | Coding Agent | blocked | unblocks on PR #20 but does not become empty: perry-decide still writes DECISIONS.md, perry-goals still writes OKR.md § Commitments in place, perry-migrate still rewrites a stranger files, and ragged-row is still the only catch | evidence/2026-08/TASK-067-finding.md | V4 | TASK-094, TASK-095 | main |  |  |

## P1

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on | Track | Stage | Stage since | Arrived | Parent | Commitment | Role |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TASK-077 | DESIGN-006 F — a finance-shaped role runs one real task end to end | Coding Agent | not_started | Run the finance-shaped role end to end on a copy of gimegime-pmo, then write the extraction report. | evidence/2026-08/TASK-077-context.md | V5 | TASK-073, TASK-075, TASK-076 | main |  |  |  |  |  |  |
| TASK-094 | Delete the header rule and the row splitter for the three stores | Coding Agent | review | PR #20 merged but the row does NOT close on it: verification item 1 asked for 0 call sites and BOARD.md keeps 13 splits / 87 resolutions on four storeless registers — needs a scope decision, not a close | evidence/2026-08/TASK-094-dispatch-2026-08-20-1958.md | V3 | TASK-090, TASK-092 | main |  |  |  |  |  |  |
| TASK-095 | Remove the parser for the three stores; keep what adoption needs | Coding Agent | not_started | — | — | V4 | TASK-094 | main |  |  |  |  |  |  |
| TASK-097 | Migrate the two real projects to the store, at V5 | Coding Agent | not_started | — | — | V5 | TASK-092 | main |  |  |  |  |  |  |
| TASK-099 | Sweep bin/, viewer/ and tests/ for document handling that ADR-007 made dead | Coding Agent | not_started | — | — | V4 | TASK-095 | main |  |  |  |  |  |  |
| TASK-102 | Evidence becomes a typed relation: {path, kind, round}, not one prose cell | Coding Agent | not_started | — | — | V4 | TASK-090, TASK-092 | main |  |  |  |  |  |  |
| TASK-123 | the goals writer takes the file as truth and derives the store, which is the opposite direction from the KR | Coding Agent | not_started | — | — | V4 |  | main |  |  |  |  |  |  |
| TASK-129 | Agent is five strings that do not join, and role has never once been written | Coding Agent | not_started | unblocked: work owns .perry/agents.jsonl → .perry/roles/ as of the 2026-08-20 signature; needs a spec, then dispatch | — | V3 | TASK-128 | main |  |  |  |  |  |  |
| TASK-144 | the event log timestamp has no zone and the register has one, so ordering them is a guess | Coding Agent | not_started | — | — | V3 |  | intake | triaged |  | 2026-08-20 |  |  |  |
| TASK-155 | the register updated field carries two facts, so appending an edge silently re-dates every asserted number in the file | Coding Agent | not_started | — | — | V3 |  | intake | triaged |  | 2026-08-21 |  |  |  |
| TASK-165 | an id must dangle once before the report exemption can cover it | Coding Agent | not_started | RE-SCOPED 2026-08-21: the quoted-output case resolved itself once TASK-162 landed, because TASK-126 report rule needs BOTH halves — the document names a check AND the id has been reported on. The residual cost is that an id must go red once before it can be exempted | — | V4 | — | intake | triaged |  | 2026-08-21 |  |  |  |
| TASK-166 | a closed row whose title was lost is invisible to the check and unreachable by the writer | Coding Agent | not_started | — | — | V3 |  | intake | triaged |  | 2026-08-21 |  |  |  |
| TASK-168 | perry-task events returns the log's head while three places promise its tail | Coding Agent | not_started | aiMark reads 437 KB on every project to work around it (aimark/doc/perry-contract-gaps-4.md § 5.1). Reproduced here: --limit 6 returns seq 0-5 dated 2026-08-16, five days stale, with nothing in the payload saying so | — | V3 |  | main |  |  |  |  |  |  |
| TASK-169 | perry-knowledge/list/1.0 ships every field aiMark asked for and has no contract page | Coding Agent | not_started | aiMark's round-4 TOP priority was 'build a read surface for cards' on the grounds that perry-knowledge is propose/promote only. It is not: list --json already emits topic, slug, claim, kind, owner_role, source, last_verified, invalidated_by, path, stale plus total/stale aggregates. The gap is that schema/ has no page for it, which is where a consumer looks. Same class as conformance.missing_projection | — | V3 |  | main |  |  |  |  |  |  |
| TASK-170 | an answered USER- ask is in no register a consumer can query | Coding Agent | not_started | live on this board today: asks.items is [] and asks.open is 0 after USER-015 and USER-016 were answered, while TASK-040 still names USER-016 in depends_on. aimark/doc/perry-contract-gaps-4.md § 5.3 | — | V3 |  | main |  |  |  |  |  |  |
| TASK-173 | an Objective is not a record, so it has no durable address | Coding Agent | not_started | NEEDS AN RFC: DESIGN-007 § 5.3 already plans a Goal store and this is the row it is missing. Measured: all five objectives return id ''; okr.jsonl holds {kr 34, version 2} and zero objective rows. aiMark accepts the reasoning against minting O1/O2 from position and asks for a minted id or a blessed stable key instead — it will not invent one itself | — | V4 |  | main |  |  |  |  |  |  |

## P2

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on | Track | Stage | Arrived |
|---|---|---|---|---|---|---|---|---|---|---|
| TASK-066 | Split perry-task by subcommand group | Coding Agent | not_started | Re-size the split after the markdown reader, row renderer and cell escaping are gone. | evidence/2026-08/TASK-066-context.md | V4 | TASK-065, TASK-038 | main |  |  |
| TASK-112 | the sign-off drafting guard cannot describe itself, so a true statement about it is refused | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-116 | the mention list is write-only, mislabelled, and two of its carve-outs are unpinned | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-117 | two tools disagree about whether the board has drifted when the event log is absent | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-118 | the id minters read three sources and the canonical store is not one of them | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-124 | the conformance corpus reads a project outside the repo and has no committed substitute | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-125 | the Anti-Goals-inside-a-version insert case runs only on the author machine | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-130 | schema README says three contracts and pins goals at a version that shipped two ago | Coding Agent | not_started | — | — | V2 |  | main |  |  |
| TASK-132 | the parity check cannot see 23 keys because Perry own state leaves four collections empty | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-137 | a new queue row is born in the second stage, not the first | Coding Agent | not_started | — | — | V2 |  | main |  |  |
| TASK-139 | a design back-reference lives in a cell the close path clears, so a finished design reports as never handed off | Coding Agent | not_started | — | — | V3 | TASK-102 | intake | triaged | 2026-08-20 |
| TASK-145 | the contract shape baseline is stale against its own recorder | Coding Agent | not_started | — | — | V2 |  | intake | triaged | 2026-08-20 |
| TASK-147 | nothing outside describe_cell proves the table and bullet paths stay separated | Coding Agent | not_started | — | — | V3 |  | intake | triaged | 2026-08-21 |
| TASK-154 | a heading naming a second id leaves a hole in the title it produces | Coding Agent | not_started | — | — | V2 |  | intake | triaged | 2026-08-21 |
| TASK-156 | a declared linkage edge to a task that never existed is invisible | Coding Agent | not_started | — | — | V3 |  | intake | triaged | 2026-08-21 |
| TASK-157 | plan-phase still authors the KR block by hand in a file documented as machine-written | Coding Agent | not_started | — | — | V3 |  | intake | triaged | 2026-08-21 |
| TASK-158 | the citation families are hardcoded in the tool, so a project with its own id family gets noise on every legitimate citation | Coding Agent | not_started | — | — | V3 |  | intake | triaged | 2026-08-21 |
| TASK-161 | a contract page cannot tabulate a collection this project state leaves empty | Coding Agent | not_started | — | — | V3 |  | intake | triaged | 2026-08-21 |
| TASK-163 | two readers disagree about whether a dash is a clock | Coding Agent | not_started | — | — | V3 |  | intake | triaged | 2026-08-21 |
| TASK-164 | perry-state assigns the state root to a global that means the project root | Coding Agent | not_started | — | — | V2 |  | intake | triaged | 2026-08-21 |
| TASK-167 | three smoke-test rows and a blank line are in the live store | Coding Agent | not_started | — | — | V2 |  | intake | triaged | 2026-08-21 |
| TASK-171 | the events key table is missing three event kinds the live log carries | Coding Agent | not_started | measured: live-not-doc = ask, answer, intake. aiMark named two of the three | — | V3 |  | main |  |  |
| TASK-172 | four of six document collections are unreachable through any contract | Coding Agent | not_started | NEEDS A DECISION FIRST: whether documents are a lane's business at all, and whether DESIGN-NNN belongs here or in perry-decide. aiMark suspects not the latter, because design docs are written and versioned differently. § 2 is latent: 0 of 164 tasks declare a DESIGN-/ADR- dependency today | — | V4 |  | main |  |  |

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
