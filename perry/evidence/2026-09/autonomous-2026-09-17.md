# Autonomous task advancement — 2026-09-17

Status: local implementation and independent V4 review complete; all three tasks await integration. Authorized by the user: "我接下来要离开电脑一段时间，你尽可能独立的推动task往下走。我晚点回来检查".

## Execution boundary

User authorization covers independent selection and reversible implementation of already-defined tasks. No unresolved user decision is answered, no specification or executor pin is changed, no task is closed, no branch is merged or pushed. Existing dirty PMO files belong to this session and are preserved.

Strict autopilot was inspected but not activated: its only host-matching auto specification (TASK-218) requires a behavior that dropped TASK-217 never delivered. The first-run marker remains absent. Inline work follows work/reference/dispatch.md section 0: small, already specified, command-verifiable changes. P0/P1 tasks without written criteria are not implemented.

## Selected work

- TASK-427 — unknown flags name the legal set. Acceptance from the existing task summary: exit 2; list accepted flags using existing declarations; no writes on the error path. No new argument or command.
- TASK-423 — reject undeclared flags in the three named read-only tools and return exit 2 for stray krs positionals, preserving valid reads.
- TASK-413 — list-bound total coverage. Acceptance from the existing task summary: independent fixture totals across mixed open/terminal states and truncated/unbounded windows; the recorded open_total=total mutation must fail. Product count behavior is unchanged.

## Checkout

- Base: `edf6b143a1b6cf8de3f2d84c53bc5e5d9cebf41e`
- Branch: `codex/autonomous-413-427-20260917`
- Worktree: `/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-autonomous-h21ewziw/perry-review-fixes-h21ewziw`

## Validation so far

- TASK-427: four real CLI cases failed before the fix because accepted flags were missing.
- TASK-413: the open_total=total mutation failed on the three --all limit cases (1, 3, 0); source restored.
- TASK-413/427: affected tier and full suite passed (154 modules, 4304 tests); commit `8972f759`. See [receipt](autonomous-413-427-receipt.md).
- TASK-423: eight failing baseline subcases reproduced; targeted 3 modules / 127 tests passed after implementation. Final full suite passed (154 modules, 4301 tests); commit `05ad0f3b`. The initial run found one old exit-1 assertion, updated to the requested exit 2. See [receipt](autonomous-423-receipt.md).
- No independent-review claim.

## Dispatch limitation

Codex CLI 0.148.0 passes the version check but the smoke test exits 1. The preflight exposes only the first 20 log lines, which include an unknown gpt-6-astra metadata warning but not the final error; that warning alone is not diagnosed as the cause. No model or authentication configuration was changed. No independent reviewer has run. The [work skill](../../../work/SKILL.md) routes dispatch to [dispatch.md](../../../work/reference/dispatch.md); its Codex preflight rule says "Exit non-0 → **refuse + surface stderr verbatim + fall back to delegate**" and the architecture review section selects `codex exec` on this host. Review was left pending rather than self-awarded.

## Skips

| Task | Title | Reason |
|---|---|---|
| TASK-066 | Split perry-task by subcommand group | Not selected in this run; readiness and decision screening remain |
| TASK-112 | the sign-off drafting guard cannot describe itself, so a true statement about it is refused | Not selected in this run; readiness and decision screening remain |
| TASK-129 | Agent is five strings that do not join, and role has never once been written | No eligible written automatic specification found; no criteria invented |
| TASK-137 | a new queue row is born in the second stage, not the first | Not selected in this run; readiness and decision screening remain |
| TASK-172 | four of six document collections are unreachable through any contract | Not selected in this run; readiness and decision screening remain |
| TASK-173 | an Objective is not a record, so it has no durable address | Unsatisfied dependencies: TASK-184, TASK-185 |
| TASK-177 | OKR setting is a ten-field checklist where it should be an elicitation | Unsatisfied dependencies: TASK-191, TASK-192, TASK-193, TASK-194 |
| TASK-184 | D009 step 4 — okr.objectives[].id is filled from the store and the contract moves to 2.2 | No eligible written automatic specification found; no criteria invented |
| TASK-185 | D009 step 5 — an Objective id survives a rename and a reorder, proved | Unsatisfied dependencies: TASK-184 |
| TASK-186 | D010 step 2 — a spec declares its author, and the escalation scan reports it | No eligible written automatic specification found; no criteria invented |
| TASK-187 | D010 step 3 — a machine-authored spec is fail-closed at the escalation gate | Unsatisfied dependencies: TASK-186 |
| TASK-188 | D010 step 4 — the scout, run by hand on ten real rows and scored against what the PMO actually decided | Unsatisfied dependencies: TASK-187 |
| TASK-189 | D010 step 5 — autopilot becomes the two-stage scout-then-build loop | Unsatisfied dependencies: TASK-188 |
| TASK-191 | DESIGN-020 phase C — the SkyTonight interview, scored by the unchanged rubric | Unsatisfied dependencies: USER-955 |
| TASK-192 | D011 step 3 — routing and smart-skip, by track spine | Unsatisfied dependencies: TASK-191 |
| TASK-193 | D011 step 4 — the escape hatch and the premise challenge | Unsatisfied dependencies: TASK-191 |
| TASK-194 | D011 step 5 — plan-phase uses the same question bank | Unsatisfied dependencies: TASK-191 |
| TASK-204 | Perry has no writer for a migration event, so TASK-180 hand-wrote JSON into an append-only log | No eligible written automatic specification found; no criteria invented |
| TASK-206 | a write returns no seq, so a poll cannot tell a stale read from a fresh one | No eligible written automatic specification found; no criteria invented |
| TASK-207 | no compare-and-set on a write, and the board demonstrably moves between a read and a write | Unsatisfied dependencies: TASK-206 |
| TASK-212 | a locked decision that gets no task row does not ship, and nothing links a design's plan step to the work that discharges it | No eligible written automatic specification found; no criteria invented |
| TASK-218 | thread the closing phase id through every close stage, so no stage re-reads phase/CURRENT | Spec prerequisite behavior remains absent despite dependency being terminal |
| TASK-219 | retro-cites-phase-scores — a cross_file check that the retro cites the scores rather than re-deriving them | Manual specification; no automatic execution |
| TASK-220 | the close-phase router subcommand, over the four unchanged lane subcommands | Unsatisfied dependencies: TASK-218 |
| TASK-221 | a phase close that stopped halfway is visible at the next snapshot, resolved from state | Manual specification; no automatic execution |
| TASK-222 | score-phase's own snapshots trip NS-01, because the names it writes do not match the declared pattern | Not selected in this run; readiness and decision screening remain |
| TASK-224 | linkage-kr-exists fires only on an absent id, so a KR nested under the wrong objective lints clean | Not selected in this run; readiness and decision screening remain |
| TASK-231 | a measured KR number has no way into the register that does not break one of its two rules | Unsatisfied dependencies: TASK-264 |
| TASK-238 | no commit on main may fail to build standalone, and nothing checks it | Not selected in this run; readiness and decision screening remain |
| TASK-240 | an ADR id can be reissued, because perry-decide writes no events and has nothing to retire one with | No eligible written automatic specification found; no criteria invented |
| TASK-242 | linkage-kr-exists proves SOME phase has resolvable overall edges, not that THIS phase does | Not selected in this run; readiness and decision screening remain |
| TASK-252 | a register write honours board rows it was never asked about, and the durable 'somebody has seen this' surface does not exist | Not selected in this run; readiness and decision screening remain |
| TASK-254 | bin/perry-lint hands back 22 commands and every one of them drops the root | No eligible written automatic specification found; no criteria invented |
| TASK-255 | Perry never shell-quotes a path into a command it hands a reader — shlex appears nowhere in bin/ or viewer/ | No eligible written automatic specification found; no criteria invented |
| TASK-264 | DESIGN-022 B — goals writes KR records, their checks and their measurements | Unsatisfied dependencies: USER-952 |
| TASK-265 | Thin perry-state to a query over the six JSONL stores; the payload shape does not change | No eligible written automatic specification found; no criteria invented |
| TASK-266 | Nothing tells an agent a projection is behind its store — ADR-012's rule has no surface | No eligible written automatic specification found; no criteria invented |
| TASK-270 | perry-config unset can empty the config store at exit 0, after which every writer refuses with a false cause and perry-lint calls the store valid | Already at review; no automatic close |
| TASK-282 | a locked design's implementation rows need not cite it, so a finished design reports as never handed off forever | Not selected in this run; readiness and decision screening remain |
| TASK-286 | the Bound that review.md requires is never asked for where specs are written, so its absence costs rounds instead of minutes | No eligible written automatic specification found; no criteria invented |
| TASK-287 | nothing warns against writing a cross-reference to a row that has not been minted yet, and the id it guesses may land on the row doing the guessing | Not selected in this run; readiness and decision screening remain |
| TASK-291 | close-task warns after the fact on a V4 whose verdict block cannot be parsed, so 10 of 27 V4 closures carry a rung nothing confirms | USER-950 explicitly deferred to phase 005 |
| TASK-294 | every NS-01 warning Perry emits is about a file Perry itself wrote, and the remedy each one offers is a no-op | No eligible written automatic specification found; no criteria invented |
| TASK-297 | parsers.py:462 says the walk is skipped when handed an exact root, and the code walks four levels anyway | No eligible written automatic specification found; no criteria invented |
| TASK-301 | schema/README.md still tells a consumer to read the State root out of .perry/config.md, which is the render | No eligible written automatic specification found; no criteria invented |
| TASK-309 | a dispatched agent's entire round lives in its context until one final commit, so any interruption costs all of it | No eligible written automatic specification found; no criteria invented |
| TASK-312 | test_tree_guard.py is now the suite's longest module at 48-124s, and its own fix is what put it there | Not selected in this run; readiness and decision screening remain |
| TASK-334 | The header-rule guard errors instead of skipping when a file vanishes mid-walk | No eligible written automatic specification found; no criteria invented |
| TASK-340 | Three documents in the tree describe a codebase that no longer exists | Not selected in this run; readiness and decision screening remain |
| TASK-349 | ADR-007 census part 2 — the 71,158 lines of tests/ | No eligible written automatic specification found; no criteria invented |
| TASK-350 | ADR-007 census part 3 — setup and the hook readers | Not selected in this run; readiness and decision screening remain |
| TASK-352 | Records appended to okr.jsonl are invisible to the render gate that was said to cover them | No eligible written automatic specification found; no criteria invented |
| TASK-355 | Every locked design now reports zero implementation references | No eligible written automatic specification found; no criteria invented |
| TASK-369 | DESIGN-015 stores a field that is derived at read time | No eligible written automatic specification found; no criteria invented |
| TASK-371 | Nothing couples dispatching an agent to marking the row it works on | No eligible written automatic specification found; no criteria invented |
| TASK-372 | perry-restore-check --root cannot verify a git-archive scratch copy — the exact use review-constraints.md recommends | No eligible written automatic specification found; no criteria invented |
| TASK-374 | One malformed line in linkage.jsonl voids validation of every good record in the file | Not selected in this run; readiness and decision screening remain |
| TASK-375 | linkage.jsonl has no uniqueness or mutual-exclusion invariant — a task that is both linked and declared unlinked passes every gate | No eligible written automatic specification found; no criteria invented |
| TASK-377 | perry-state's design.by_status key order depends on PYTHONHASHSEED | Not selected in this run; readiness and decision screening remain |
| TASK-378 | Every tool-mediated write is stamped actor: agent, so two concurrent PMO sessions cannot tell their writes apart — and one has already misattributed the other's to a dispatched agent | No eligible written automatic specification found; no criteria invented |
| TASK-380 | main cannot have a green suite through code alone — the one red module asserts Perry's user has answered their questions | No eligible written automatic specification found; no criteria invented |
| TASK-384 | summary is mandatory to write, reported by the linter, published by one payload and not the other, and declared in no schema | No eligible written automatic specification found; no criteria invented |
| TASK-386 | A pipe-written tasks value is a hard lint error and, separately, resolves to nothing in a reader that never consults the linter | Not selected in this run; readiness and decision screening remain |
| TASK-387 | A mitigation that lives in one writer's body was not inherited by the next writer that read the same field | No eligible written automatic specification found; no criteria invented |
| TASK-390 | A design's Linked OKR line is parsed into a field nothing reads, so a design can name a KR that does not exist and every instrument stays green | No eligible written automatic specification found; no criteria invented |
| TASK-391 | A documented flag combination writes a linkage record that permanently reddens the suite, and the writer has no retraction | No eligible written automatic specification found; no criteria invented |
| TASK-393 | The shipped OKR template still mints the retired KR grammar, so a new project starts in the form ADR-017 just removed | No eligible written automatic specification found; no criteria invented |
| TASK-395 | perry-okr diff reports an id drift that render --write cannot repair, because render matches rows by the id that drifted | Not selected in this run; readiness and decision screening remain |
| TASK-396 | perry-task has no published write contract, so a newly required flag reaches a consumer as a refusal at runtime | No eligible written automatic specification found; no criteria invented |
| TASK-397 | ADR-017 changed an identifier's value space and perry-goals/list stayed at 2.3, so a consumer joining on a stored KR id gets a silent miss | No eligible written automatic specification found; no criteria invented |
| TASK-398 | an advisory a program must act on is a payload field, not a stderr line, and add still writes one under --json | Not selected in this run; readiness and decision screening remain |
| TASK-401 | every bin/ entrypoint is recompiled on every invocation because an extensionless __main__ is never bytecode-cached | No eligible written automatic specification found; no criteria invented |
| TASK-403 | four test modules use a regex to judge meaning, which ADR-007 decision 3 already ruled the Python layer never does | Not selected in this run; readiness and decision screening remain |
| TASK-422 | a crash between the board write and the event append removes a row from both halves of P003-O3-KR2, and no desync detector names it | Not selected in this run; readiness and decision screening remain |
| TASK-424 | no test compares a --compact or --json value against the store files or the schema, so a wrong build() agrees with itself | Not selected in this run; readiness and decision screening remain |
| TASK-426 | perry-restore-check's deferred import fails in exactly the deployment its docstring says it exists for | No eligible written automatic specification found; no criteria invented |
| TASK-428 | three read-only subcommands accept --dry-run and drop it, and perry-config show cannot tell an unreadable config from an absent one | Not selected in this run; readiness and decision screening remain |
| TASK-432 | --compact drops missing_defaults from project.tracks[], the one field that separates 'no honest default' from 'this mode has no such control' | Not selected in this run; readiness and decision screening remain |
| TASK-434 | The User Input Queue has no sweep, so 27 answered asks cannot leave the board | No eligible written automatic specification found; no criteria invented |
| TASK-435 | perry-task add --track is accepted and dropped on a project-mode track | No eligible written automatic specification found; no criteria invented |
| TASK-436 | perry-diagnose reads the append-only journal as a live reference, so one mistyped id dirties a project forever | Manual specification; no automatic execution |
| TASK-438 | a row can close at verification V0, which the store accepts, perry-lint passes, and the writer refuses from a caller | No eligible written automatic specification found; no criteria invented |
| TASK-440 | Next action has four writers and two guards, and the comment beside one guard says there are two writers | Spec pins claude-subagent, unavailable on this host; no executor substitution |
| TASK-444 | DESIGN-020 phase D — a planning draft survives interruption and is finalized through tools | Unsatisfied dependencies: TASK-264, TASK-191 |
| TASK-445 | Every user decision is recorded as an ask, in a card of at most 600 characters | No eligible written automatic specification found; no criteria invented |
| TASK-446 | The /perry snapshot is measured and held to one screen | Not selected in this run; readiness and decision screening remain |
| TASK-447 | An open row's Next action is held to 400 characters | Not selected in this run; readiness and decision screening remain |
| TASK-451 | DESIGN-017 A1 — the schema anchors the architecture document at the code root | No eligible written automatic specification found; no criteria invented |
| TASK-452 | DESIGN-017 A2 — perry-state finds ARCHITECTURE.md where the code is | Unsatisfied dependencies: TASK-451 |
| TASK-454 | DESIGN-017 D2 — a decided architecture section changes only with a recorded confirmation | No eligible written automatic specification found; no criteria invented |
| TASK-455 | DESIGN-017 D3 — boundary-touching merges get a fresh-context architecture review | No eligible written automatic specification found; no criteria invented |
| TASK-456 | DESIGN-017 E1 — reference pages get a byte budget, and three over-budget pages are split | Not selected in this run; readiness and decision screening remain |
| TASK-457 | DESIGN-017 E2 — five subcommands carry a context bill | Not selected in this run; readiness and decision screening remain |
| TASK-458 | viewer/parsers.py imports bin/lib, perry_md_store and tables through sys.path, against ARCHITECTURE.md § 3 | Not selected in this run; readiness and decision screening remain |
| TASK-460 | DESIGN-022 C — perry-state reads a KR's met from its declared direction | No eligible written automatic specification found; no criteria invented |
| TASK-461 | DESIGN-022 D — a due KR check is recommended, reviewed on Friday and pre-selected at scoring | Not selected in this run; readiness and decision screening remain |
| TASK-465 | Guided project initialization through the first approved plan | Unsatisfied dependencies: TASK-192, TASK-193, TASK-194, TASK-444 |

## Left for user

- USER-952: KR supersession/withdrawal representation and schema scope.
- USER-955: real interview target, or permission for fixtures while retaining real-interview incompleteness.
- Review local tested deliveries when available; no self-awarded V4/V5.

## Return checkpoint

- TASK-413 and TASK-427: `review`, local commit `8972f759`, branch `codex/autonomous-413-427-20260917`.
- TASK-423: `review`, local commit `05ad0f3b`, branch `codex/autonomous-423-20260917`.
- Both branches are based on `edf6b143`; neither contains the other's change. Combined-state testing and any conflict resolution belong to integration after independent review.
- No active executor or automatic follow-up remains. Strict autopilot was never enabled.
- Current main PMO checks: lint 0 errors / 41 warnings; git diff --check passes; recovery nonblocking; interrupted empty.
- USER-952 (KR scope) and USER-955 (real interview project) remain unanswered. No choice made on the user's behalf.
- DESIGN-014 handoff and triage changes from earlier in this session are preserved with these receipts. No user-facing release has been published.

Next: repair or explicitly choose an allowed review executor, independently review the two immutable commits, then allocate releases and validate their combined integration on current main. Tests passing on separate coding branches are not merged-state evidence.

## CLI repair and resumed review — 2026-09-17

A full diagnostic run established the earlier failure: server HTTP 400, `The 'gpt-6-astra' model requires a newer version of Codex.` The prior CLI was 0.148.0; the earlier metadata warning was not sufficient evidence by itself. After the user upgraded, `codex --version` reports 0.154.0 and `bash bin/perry-codex-preflight --force` exits 0 with PERRY_OK validated. No model or authentication settings changed in this session.

Fresh-context independent review resumed against the two original immutable commits, using autonomous-review-criteria.md and the architecture. Required verification was explicitly set to V4 before dispatch; that records the requirement, not an earned result. Review started via codex exec in an isolated worktree. Final verdicts will be attached separately.

## Independent review complete

Fresh Codex reviewer returned V4 PASS for TASK-413, TASK-427 and TASK-423; architecture PASS for both commits. [Archived report](autonomous-review/review.md). Required reviewer-run affected tests: TASK-413/427 154 modules / 4304 tests, TASK-423 63 modules / 1738 tests, both exit 0 with unchanged trees. Mutation tier caught the intended counting regression; restored targeted test passed. Optional extra restored-tier repetition was cancelled and is not passing evidence. Two initial inherited-PERRY_HOME runs were excluded and cancelled; candidate-isolated reruns are the accepted results.

Next: a separate integrator allocates releases and validates the combined merge candidate on current main. The implementing session has not merged its own work, closed the tasks, or pushed. No reviewer remains running.
