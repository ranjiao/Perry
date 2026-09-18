# TASK-468 independent V4 review

Date: 2026-09-18. Reviewer: Claude Opus 5, a fresh-context Claude Code child session in an isolated worktree. I am not the author of the candidate.
Target: branch `worktree-agent-abf710762750f9d9b`, head `5f182d3c`, base `c48e25fe`. I reviewed `git diff c48e25fe 5f182d3c` against the following:
- `TASK-468-spec.md`;
- the iteration plan;
- the four findings carried from `TASK-456-457-integration/acceptance.md`;
- the user decision granting TASK-468 a +166 net Python/test line exception (recorded on main at `36c0822f`, after this base);
- `AGENTS.md`, `ARCHITECTURE.md` and `bin/ARCHITECTURE.md`;
- `reference/host-capabilities.md`.

I formed my view from the contract, the diff and real host data before I read `TASK-468-result.md` and `TASK-468-mutation.log`.

VERDICT: FAIL

The binding work, which is criterion 1, is sound. So are the fixtures for the seven identity categories, the OpenCode outcome, the frozen baseline and the four carried fixes. Two defects break criteria 3 and 4 on real host data while the whole suite stays green:

- The Codex adapter double-counts the usage that forked children inherit from their parent.
- The Claude adapter reports coverage as `complete` while it ignores workflow children.

Both fixes are small and stay inside the files already in scope.

## Findings, ranked

### High

**H1. Codex children forked from their parent double-count the parent's usage. This breaks criterion 3 (cumulative deltas, no double count) and criterion 4 (totals).**

- **Code.**
  - `bin/perry-context-budget:206`: `base = prev if prev and ... else {}`. A rollout's first `token_count` is always taken as a delta from zero.
  - `:221-231` collects the children.
  - `:430` sums the children into `usage`.
- **Real schema.** A Codex child spawned with forked history has `forked_from_id` and `subagent_history_start_ordinal` in its `session_meta`. Its cumulative counter starts at the parent's running total. The first `token_count` carries `total_token_usage.input_tokens` equal to the parent's total at spawn time, with `last_token_usage.input_tokens == 0`.
  - Example: child `019fa22e…` starts at 13,882,473. That value appears among the parent `019fa19d…`'s own totals.
- **Measured, read-only, parent `019fa19d-4566-7d30-886e-b96f3deb76e9` bound by `PERRY_HOST=codex-cli CODEX_THREAD_ID=…`:**
  - the tool reports input plus cached input of 131,928,122 and says `coverage: complete`;
  - the true figure, with each child's inherited first total removed, is 104,163,176;
  - the overstatement is 27,764,946 (+26.7%), exactly 2 × 13,882,473.
- **Prevalence on this machine.** 17 of 75 Codex child rollouts carry an inherited first total, together 192,678,794 input tokens that would be counted twice.
- **Why the suite misses it.** The fixture `tests/test_context_budget.py:242-248` builds a child whose counter starts from zero, so it does not model the real schema. `bin/README.md:735-742` describes the rule as though the counter always starts clean.
- **Scope of the damage.** The Perry-cwd children in the baseline all start fresh (I checked all three), so the frozen baseline is not affected.
- **Fix direction.** Make a child's first snapshot the base when its `last_token_usage` differs from its `total_token_usage`, or sum `last_token_usage` directly. Add a fixture that inherits a total.

**H2. Claude workflow children are neither found nor counted as spawned, and coverage still says `complete`. This breaks criterion 4 ("Missing child usage yields partial coverage").**

- **Code.**
  - `bin/perry-context-budget:225` globs only `<id>/subagents/*.jsonl`.
  - `:171-172` counts only `Agent`/`Task` tool uses as spawns.
- **Real data.** Claude Code writes the children of the `Workflow` tool under `<id>/subagents/workflows/wf_*/agent-*.jsonl`.
  - Session `-Users-bytedance-proj-Gimegime-pmo/c5e0ef07…` made 2 `Workflow` calls and has 213 workflow child transcripts, 211 of them with usage.
  - Those children hold input 2,266,819, cached 14,483,563, cache creation 4,057,489 and output 230,703.
  - The report says `children {spawned 1, found 1, with_usage 1}` and `coverage: complete`. The missing uncached input is about 9.5 times the 239,300 it does report.
- **Scope.** Workflow directories exist today only under two non-Perry projects on this machine, `Gimegime-pmo` and `PolyForge`. It does not affect the baseline. The tool ships to every project, though, and the one signal that exists to prevent understatement says `complete`.
- **Fix direction.** Glob `subagents/**/*.jsonl`. Also treat child files that no spawn accounts for, or unknown spawning tools, as a coverage gap rather than as silence.

### Medium

**M1. Claude reasoning is reported as a measured `0` when the host did not record it.**

- `bin/perry-context-budget:179` reads `(usage.get("output_tokens_details") or {}).get("thinking_tokens", 0)`.
- 63 of the 179 top-level Claude transcripts on this machine have no `output_tokens_details` at all. `c5e0ef07…` reports `reasoning: 0` beside 1,975,385 output tokens.
- The report lists `usage` under `measured`, and `estimated` is `[]`.
- The spec's Bound says missing telemetry is unknown, not zero. The category should be `null` or `unknown` and named in `gaps`. The existing fixtures always carry `thinking_tokens`, so nothing tests the absent case.

### Low

- **L1. An explicit `--session` with no host identity still gates** (`:424-425`, `:509`, `:524`).
  - I judge the author's reading as compliant. Criterion 1's first sentence accepts "an explicit session source". The prohibition is on *implicit* newest-file selection, and no implicit path can reach a verdict. Mutations R1 and R1b are both killed, and every path through `bind()` (`:396-409`) is either `--session` or an exact-id lookup that requires exactly one match.
  - The residual risk is presentation. A child agent can pass its parent's file and get `OVER`, exit 1, or `OK`. `OK` exits 0, the same as `unknown`. The `scope: explicit` label carries the distinction in JSON, and the text output prints it after the session id.
  - Acceptable. The stricter variant, where `explicit` never gates, is a one-line change if the PMO wants it.
- **L2. A resumed or forked Claude transcript is permanently `unknown`.**
  - `:180-181` needs exactly one `(agentId, sessionId)` pair. A resumed file carries the old id on its first records and the new id after that.
  - Real case: `-Users-bytedance-proj-Gimegime-pmo/a7306ee0…` has 541 records under `868a412f…` and 430 under `a7306ee0…`. Bound by host identity it reports "records session None".
  - This is fail-safe, not wrong. It affects 1 of 179 real transcripts.
- **L3. `host` in the JSON is overwritten by the transcript's format** (`:423` replaces `:475`).
  - When `--session` names another host's file, the running host is lost. For example, in Claude, `--session <codex rollout>` reports `host: codex-cli` with `identity: null`.
  - Provenance should keep both the running host and the transcript's host.
- **L4. Cross-tool dependency.** Undocumented in `bin/ARCHITECTURE.md`.
  - `host_identity()` (`:115-116`) runs `bin/perry-detect-host` as a subprocess, with no timeout and no guard against `OSError`. It is the first `bin/` tool that executes another `bin/` tool.
  - This is not an import, so the letter of `bin/ARCHITECTURE.md §3` holds. The coupling is to detect-host's single-token output, which that script calls its durable contract.
  - `bin/ARCHITECTURE.md` §1–§3 ("The one tool that reaches outside", the reader list) still does not mention reading `~/.codex/sessions` or the detect-host dependency. The author disclosed this (deviation 10).
  - The fix is a descriptive follow-up and does not block.
  - NN-1 is about Perry state files, and transcripts are not state files. The direct `.perry/config.jsonl` read is the pre-existing named deviation, and its reasoning is now restored in `bin/README.md`.
- **L5. The Codex `cache_write_input_tokens` inclusion rule is unpinned.**
  - Mutation R7, which stops subtracting cache-write from input, survives, because no fixture carries a nonzero value.
  - Real data: the field is present in all 28,927 snapshots I read, and it is always 0. `total_tokens == input_tokens + output_tokens` holds in every one of them.
  - So the rule is harmless today and the host does not verify it. Either report `unknown` when the field is nonzero or add a fixture that pins the assumption.
- **L6. The baseline omits some plan fields.**
  - Plan §Comparison protocol asks for cache condition, tool capabilities, fixture state and the task acceptance criteria. The receipt has commit, host environment, models and effort, bills, inventories and aggregates, but none of those four.
  - The runtime matched runs are correctly deferred to TASK-473.
- **L7. Stale consumer prose.** `work/reference/autopilot.md:209` still says that `unknown` means the host keeps no transcript. `unknown` now also covers absent, child and ambiguous identity. Behaviour is compatible, since autopilot reads only the exit status. This is out of scope and disclosed (deviation 9).

### Info

- The tool ignores `CODEX_HOME` and `CLAUDE_CONFIG_DIR` relocations. The result is `0 transcripts`, which reports `unknown`. That is safe.
- Codex malformed-count handling (`:209-211`) has no fixture. The malformed and truncated fixture covers Claude only.
- A refused bill and an over-cap bill now both exit 1. JSON `status` distinguishes them. The only consumers are the tool's own tests.

## Per-criterion judgement

| # | Result | Basis |
|---|---|---|
| 1 | PASS | `bind()` takes only `--session` or an exact-id lookup that must match exactly one file. The file's records must name the host's id. `historical` never gates. R1, R1b and R12 are killed. Real check: this child session reports `unknown` (absent identity). The same tool with the child flag blanked binds the parent `bcc8bb26…` by id. |
| 2 | PASS | These fixtures are present and assert outcomes, not crashes: Claude and Codex; concurrent sessions; a cwd/worktree mismatch; a newer unrelated transcript, including a newer Claude transcript during a Codex run, with `CODEX_THREAD_ID`, `CLAUDECODE` and `CLAUDE_CODE_SESSION_ID` all set; absent identity for Claude, Codex and a Claude child; missing usage on both hosts; malformed and truncated lines, on Claude only. OpenCode reports `unknown` with a reason, and R6 is killed. |
| 3 | **FAIL** | Claude categories, dedup and reasoning-inside-output are correct against the real schema (`thinking_tokens` exists under `output_tokens_details`). Codex reasoning-inside-output is confirmed by `total_tokens == input + output` in 28,927 of 28,927 snapshots. The Codex delta rule is wrong for forked children (H1). A missing reasoning figure becomes 0 (M1). The cache-write rule is unpinned (L5). |
| 4 | **FAIL** | Provenance fields are present, and cost and quota are always `unknown`. A missing Agent/Task child gives `partial`, and R5 and R10 are killed. Workflow children are invisible and coverage says `complete` (H2). |
| 5 | PASS | Commit `26a4053c` holds the receipt and precedes `04e91c18`. `commit` = `c48e25fe…`, and its sha256 matches the README. The five bills are retained with unchanged caps. The field gaps are L6. |
| 6 | PASS (lines by exception) | Negative fixtures fail when binding is reverted. Legacy tests are green. Net +166 = `bin/perry-context-budget` +79 and tests +87, which I verified with `git diff --numstat`. The user's +166 exception (main `36c0822f`) covers it. I saw no padding: the code is dense and has no dead helpers. |
| Carried | PASS | (1) The rationale, including the NN-1 config-read deviation, is restored in `bin/README.md § perry-context-budget`. (2) A refused bill exits 1 with the reason on stderr. (3) `--help --bill bogus` exits 0 and prints usage. (4) Refs after a `( … )` note are kept. |

## Privacy of the baseline

I walked every string in `receipt.json`. It holds:
- commit and timestamp;
- host environment values (entrypoint, SDK and app version, effort, session id, the child flag);
- bill paths;
- the Claude and Codex directory paths;
- one transcript path and name;
- the first and last rollout filenames.

Everything else is numeric. `README.md` holds counts, aggregates, model names, the two legacy-gate results and the capture script's source. **No transcript content, tool input or tool output was copied.** No leak.

## Output-shape consumers

`git grep` over the tree, excluding `perry/` history:

- **`scanned_whole_file`.** No consumer outside the old tests.
- **The `historical` verdict.**
  - `work/reference/autopilot.md:199` runs the gate and branches only on exit status. `historical` exits 0, and so does `unknown`.
  - Autopilot never passes `--session`, so it cannot receive `historical`.
- **Bill exit 1.**
  - No consumer outside `tests/test_context_budget.py`.
  - `CHANGELOG.md:11` and `release/records.jsonl` (0.1.16) describe the bill without exit codes.
- **Other references.** `tests/test_bin_argument_contract.py` and `tests/test_blank_cell_is_one_rule.py` use the tool, and both are green.
- **Skill pages.** No skill page parses the JSON.

Compatibility risk is low. L7 is the only stale prose.

## My measurements (read-only; nothing copied into the repo)

| Case | New tool | Base tool (`c48e25fe`) |
|---|---|---|
| Largest Claude transcript, 58,894,850 B (`PolyForge/b258b665…`), `--session`, 3 runs | 0.17–0.25 s wall, 38–41 MB RSS; context 646,925; 2,227 requests, 2,128 duplicates; 4 of 4 children | 0.03–0.04 s, ~41 MB; context 646,925 (same figure) |
| Perry 41,212,736 B (`0387e499…`) | 1.58 s, 31 MB RSS; partial, 25 of 110 children without usage (reproduces the author's figure) | — |
| Largest Codex rollout, 405,678,590 B, `--session` | 1.44–1.60 s, ~140 MB RSS; context 159,228 | — |
| Codex host-identity bind, parent `019fa19d…` | 0.49 s wall, including the first-line scan of 459 rollouts for children | — |
| Claude host-identity bind (child flag blanked) → parent `bcc8bb26…` | `current`, context 371,662, `OVER` exit 1 | — |
| This child session, default | `unknown`, "absent identity", exit 0 | — |

The cost is about 5–10× the old tail read on the largest Claude file, but still under 2 s on a 405 MB rollout. That is acceptable for a per-iteration stop check.

Suites (`PERRY_PROJECT` and `PERRY_HOME` unset, `__pycache__` purged first):
- `bash tests/run`: 155 modules · 4,377 tests · 113.4 s · all green.
- `bash tests/run --tier slow`: 159 modules · 4,480 tests · 146.5 s · all green. This is the final clean run, on this review branch.
  - My first slow run had every test green, but the tree guard flagged `perry/evidence/2026-09/TASK-468-review/`. That was me: I created the directory while the run was in progress, so it is not a suite write.
  - My second run was red in `test_diagnose` (`test_perry_itself_passes_its_own_id_checks`, a dangling user-decision ID). The cause was this review file citing an ID that is defined only on main after `c48e25fe`. I reworded it, then re-ran `test_diagnose` alone (158 tests, OK) before the final run.
  - Neither red run is attributable to the candidate.
- `git diff --check c48e25fe 5f182d3c`: clean.

## Mutation table (mine)

Method:
- one fresh `git archive 5f182d3c` tree per mutant;
- every `__pycache__` purged;
- `python3 -B -m unittest tests.test_context_budget`;
- the unmutated tree is green.

Runner: scratchpad only, not shipped.

| # | Mutation | Result | Killing test(s) |
|---|---|---|---|
| R1 | Binding reverted to base behaviour: newest file in the cwd slug | KILLED (10 F, 9 E) | concurrent, worktree, newer-Claude-during-Codex and absent-identity fail on assertions, plus 15 others |
| R1b | Newest file across all Claude projects, file identity check kept | KILLED (5 F, 2 E) | concurrent, worktree, newer-Claude-during-Codex, absent/ambiguous, codex deltas, codex child, no-usage |
| R2 | Claude dedup dropped (key per record) | KILLED | `test_claude_repeats_a_message_per_block_and_it_counts_once` |
| R3a | Codex reasoning counted twice (added to output) | KILLED | `test_codex_cumulative_totals_become_deltas_with_repeats_and_resets` |
| R3b | Claude reasoning counted twice | KILLED | `test_claude_repeats_a_message_per_block_and_it_counts_once` |
| R4 | Codex cumulative counters summed (base always `{}`) | KILLED | `test_codex_cumulative_totals_…` |
| R5 | Missing child treated as full coverage | KILLED | `test_claude_children_are_counted_and_a_missing_one_makes_coverage_partial` |
| R6 | OpenCode reports a measured `OK`, context 0 | KILLED | `test_absent_ambiguous_mismatched_or_unsupported_identity_is_unknown_not_zero` |
| R7 | Codex cache-write not subtracted from input | **SURVIVED** | none (L5) |
| R8 | Codex child parent check dropped | KILLED | codex child, codex deltas |
| R9 | Codex repeat snapshot not skipped | KILLED | codex deltas |
| R10 | Claude `subagents/` ignored | KILLED | children/coverage test |
| R11 | Context drops `cache_creation` | KILLED | `test_all_three_input_fields_are_summed`, dedup test |
| R12 | Explicit `--session` with no identity labelled `current` | KILLED | `test_an_explicit_other_session_is_historical_and_never_gates` |

The suite is green on three real-data defects, H1, H2 and M1. No mutation is needed to show them, because the shipped code is already wrong there and no fixture models those schemas.

## Checking the author's claims

- **19 of 19 mutants killed.** Consistent with my R-series: every mutant in their table has a killing test. Their M7 exercised Claude only. My R3a covers Codex, and it is killed.
- **Criterion 1 reading (deviation 2).** Accepted as compliant, see L1.
- **"41 MB transcript 1.27 s; 25 of 110 children missing".** Reproduced: 1.58 s, the same 25 of 110.
- **"Codex context equals `last_token_usage.input_tokens`".** Confirmed at scale: the delta equals `last_token_usage` in 25,632 of 25,632 non-reset snapshots. That holds *within* one rollout. It does not rescue H1, which is about a child's first snapshot.
- **"`cache_write_input_tokens` … 0 or absent".** Confirmed: it is present and always 0 across all rollouts. The inclusion rule remains an assumption (L5).
- **"Children … `parent_thread_id` in their first record".** True, but incomplete: the first *counter* of a forked child is inherited (H1). The result and README do not mention this.
- **"Baseline committed before any tool edit".** Confirmed by commit order: `26a4053c` precedes `04e91c18`.
- **Suite counts.** My full run matches theirs: 155 modules / 4,377 tests.

## What I could not verify

- **A real non-child Claude Code session.** I could not see whether it exports `CLAUDE_CODE_SESSION_ID` *without* `CLAUDE_CODE_CHILD_SESSION`. I can only observe a child session, where both are set and the id is the parent's. With the flag blanked, the parent binds correctly. If the Desktop app marks main sessions as children too, the gate is always `unknown` and autopilot quietly falls back to `--max-dispatches`.
  - **Before merge:** the PMO should run `bin/perry-context-budget --json` once from its own main session.
- **A real nested `codex exec` under Claude Code.** I did not run one. Only the fixture covers the precedence.
- **Codex's semantics for a nonzero `cache_write_input_tokens`.** The field is never nonzero in local data.
- **Whether other hosts or versions write workflow or other child transcripts in places the adapters do not look.** I checked only the layouts present on this machine.

---

## Re-review — repair round

Date: 2026-09-18. Same reviewer, and I did not write the repair. Target: head `fe52036d` (repair code `5752ff71`), built on `5f182d3c`, base still `c48e25fe`. This review branch was replayed onto `fe52036d`. I read `git diff 5f182d3c fe52036d` and re-ran everything below myself before I read the author's repair section, and then checked its claims.

VERDICT: PASS-WITH-FINDINGS

H1, H2 and M1 are fixed, with the exact real-data figures reproduced. L3–L7 are resolved. No High remains. What is left:
- one Medium. It is a live but unverified risk on the plain Claude CLI and must be settled before any later package relies on the gate there.
- one Low I missed in round 1, which predates the repair;
- two untested repair branches.

### First-round findings

| Finding | Status | Where |
|---|---|---|
| H1 Codex forked child double count | **Resolved** | `bin/perry-context-budget:218-229`. A counter's first request, and the first after a drop, is `total − last_token_usage`, and an inherited-only snapshot is skipped. Keyed on `last_token_usage`, not `forked_from_id`, so it also fixes the one real child without `forked_from_id` (see real data). Fixture `tests/test_context_budget.py:261-270`. |
| H2 Workflow children invisible, coverage says complete | **Resolved** | `:181-182` counts `Workflow` calls. `:243` uses `rglob`. `:440-448` adds the workflow and unaccounted-child gaps, and workflow children are summed into `usage`. Fixture `:272-283`. |
| M1 unrecorded reasoning reported as 0 | **Resolved** | `:188` (no default), `:152-156` (`None` allowed for reasoning only), `:450-453` and `not_measured`. Fixture `:235-239`. |
| L3 running host overwritten | **Resolved** | `:454` uses `transcript_host`, and `host` stays the running host. |
| L4 subprocess dependency undocumented, no timeout | **Resolved** | `:117-121` (10 s timeout; `OSError`/timeout reads as `unknown`) and `bin/ARCHITECTURE.md:62-69`. |
| L5 cache-write rule unpinned | **Resolved (pinned by fixture)** | The forked-child fixture carries `cache_write_input_tokens=30` inside `input_tokens`. R7 is now killed. The host semantics are still undocumented, and the field is still always 0 in local data. |
| L6 baseline protocol fields | **Resolved** | `TASK-468-baseline/README.md § Comparison-protocol fields`. I checked the spec and plan sha256 at `c48e25fe` independently, and both match. I recomputed the 99.16% cache share (35,567,461 / 35,867,952). `receipt.json` is unchanged. |
| L7 autopilot prose | **Resolved** | `work/reference/autopilot.md:209-214`. |
| L1 explicit `--session` gates, L2 resumed Claude file is `unknown` | Unchanged, as agreed | see Desktop below |

### Real data (read-only, the same sources as round 1)

- **H1.** Parent `019fa19d…` bound by `PERRY_HOST=codex-cli CODEX_THREAD_ID=…`:
  - input + cached = 3,514,984 + 100,648,192 = **104,163,176**, exactly the independent figure;
  - 2 of 2 children, `complete`.
- **H1, no undercount.** I ran the `5f182d3c` and `fe52036d` `read_codex` on every local rollout under 100 MB (454; 5 larger ones skipped):
  - **Plain rollouts:** 379, with 0 changed totals and 0 inherited first totals. Their summed requests equal the final total, including the 2 plain rollouts that have a counter reset.
  - **Changed totals:** 17, all children with an inherited first total. In every case the change equals the inherited amount exactly.
    - 16 are `forked_from_id` children.
    - 1 is a child *without* `forked_from_id` (`019fac0b…`, 7,959,390 inherited), which the repair also handles correctly.
  - **"Resumed" rollouts:** the only rollouts with two `session_meta` records are 5 forked children. Their totals are unchanged by the repair and equal their final totals. See R-L1 for a separate defect in them.
- **H2 and M1.** `Gimegime-pmo/c5e0ef07…` via `--session`:
  - `children {spawned 1, found 1, with_usage 1, workflow_calls 2, workflow_found 213}`;
  - `coverage: partial`, with the Workflow gap;
  - input 2,506,119 = 239,300 + 2,266,819;
  - `reasoning: null`, and `not_measured` says "2174 of 2174".
- **Timing:**

  | Transcript | Time |
  |---|---|
  | Gimegime session (213 workflow children) | 0.80 s |
  | 41 MB Perry transcript | 1.22 s |
  | 405 MB Codex rollout | 1.83 s |

### Desktop limitation (outcome b)

- **Honestly documented.** Yes, for Desktop:
  - `reference/host-capabilities.md:55` (the matrix row) and `:68-72`;
  - `work/reference/autopilot.md:209-214`;
  - `bin/README.md` § perry-context-budget;
  - the tool's own reason string (`:422-424`).

  Each says `unknown` there is not a clean budget and that autopilot falls back to `--max-dispatches`. Verified from this Desktop subagent: the default run gives `unknown`, exit 0, with the Desktop reason.
- **Can a Claude subagent still get a clean verdict on its parent?**
  - By default, no.
  - With an explicit `--session <parent file>`, yes. Run from this subagent it printed `(…, explicit)`, `OVER — hand off and start a fresh session`, exit 1, with the parent's 386,228.
  - This is the L1 path, accepted in round 1 as the caller's own assertion. On Desktop it is now the *only* way to get a verdict, main session included. The explicit path is not mentioned in `host-capabilities.md`, so an agent there does not learn that an explicit verdict is unverified (R-L3).

### Remaining findings, ranked

**Medium**

- **R-M1. A plain-CLI subagent would bind its main session as `current`. This is a live risk, inferred rather than observed, and only partly documented.**
  - **Why the risk is live.** The PMO's evidence shows `CLAUDE_CODE_CHILD_SESSION` marks Desktop, not a subagent, and `AI_AGENT` is identical in the main session and in subagents. This subagent's `CLAUDE_CODE_SESSION_ID` is its parent's id. So the runtime passes the parent's id to in-process subagents, and nothing in the evidence suggests the plain CLI does otherwise. On the plain CLI there is no flag at all, so `host_identity()` (`:122`) returns the shared id and `bind()` (`:414-431`) binds the parent transcript.
  - **Simulated.** I blanked the flag in this subagent. The result was `(claude-code, session bcc8bb26…, current)`, `OVER`, exit 1 on the parent's 386,228 tokens. That is the original defect class, now labelled `current`, which the report treats as verified.
  - **Documented** only in `bin/README.md:735-736`, as "probably holds … unverified".
    - `reference/host-capabilities.md:55` still presents `CLAUDE_CODE_SESSION_ID` as binding the Claude session, with no plain-CLI caveat.
    - `work/reference/autopilot.md` does not mention it.
  - **Exposure today.** It is limited. The only instruction to run the gate is autopilot's stop check, which runs in the main session, where the binding is correct.
  - **Required before a later package enables gate-driven advice on Claude** (the plan says "verify identity failures before enabling advice"):
    - either check one real plain-CLI subagent's environment;
    - or decide to treat `claude-code` without a distinguishing signal as `unknown`.

    In either case, add the caveat to `host-capabilities.md`.

**Low**

- **R-L1 (pre-existing; I missed it in round 1). In a forked Codex child the last `session_meta` wins** (`:210`, `meta = payload`).
  - Five forked children embed their parent's `session_meta` as a second record, so `read_codex` reports the *parent's* id as the child's session.
  - Real parent `01a022e7…` reports `found 0` and the gap "3 of 3 spawned children have no usage", although those children carry usage. Coverage is correctly `partial`, but the stated reason is false and their usage is left out.
  - Real child `01a022e9…`, bound by its own `CODEX_THREAD_ID`, reports `unknown` ("records session 01a022e7…").
  - Both outcomes are fail-safe. The fix is for the first `session_meta` to win, plus a two-meta fixture.
- **R-L2. Two repair branches are untested (surviving mutants S2 and S3).**
  - S2 keys `last_token_usage` on `forked_from_id`. The fixture always sets `forked_from_id`, but real child `019fac0b…` inherits 7,959,390 tokens without it, so that regression would reintroduce the double count.
  - S3 drops the zero-delta skip (`:227-228`). A forked child with no request of its own after the fork would then report a measured context of `0` instead of "no usage record".
- **R-L3. The Desktop explicit path is undocumented** (see above).
- **L2. A resumed Claude transcript is `unknown`.** Unchanged and fail-safe.

**Info**
- The Desktop check sits in both `host_identity()` (`:122`) and `bind()` (`:422`). The second only improves the message. That is not padding worth a finding.

### Net lines (measured: `git diff --numstat c48e25fe fe52036d -- bin tests`)

| File | Added | Deleted | Net |
|---|---:|---:|---:|
| `bin/perry-context-budget` | 267 | 154 | +113 |
| `tests/test_context_budget.py` | 200 | 78 | +122 |
| Total | | | +235 |

The repair itself is +34 in the tool and +35 in tests. TASK-468 is unlinked, so the line count is not a finding. I looked for padding and found none: each added line serves one of the fixed findings or its test.

### Mutations (mine)

Method, the same as round 1:
- one fresh `git archive fe52036d` tree per mutant;
- every `__pycache__` purged;
- `python3 -B -m unittest tests.test_context_budget`;
- the unmutated tree is green.

| # | Mutation | Result | Killing test |
|---|---|---|---|
| S1 | H1: first snapshot counted whole (base `{}`) | KILLED | forked-child test |
| S2 | H1: `last_token_usage` honoured only with `forked_from_id` | **SURVIVED** | none (R-L2) |
| S3 | H1: inherited zero-delta snapshot kept as a request | **SURVIVED** | none (R-L2) |
| S4 | H2: `glob`, not `rglob` | KILLED | workflow test |
| S5 | H2: a Workflow run leaves coverage complete | KILLED | workflow test |
| S6 | H2: unaccounted child not a gap | KILLED | workflow test |
| S7 | M1: unrecorded reasoning defaults to 0 | KILLED | reasoning test |
| S8 | M1: mixed recorded and unrecorded reasoning summed as if 0 | KILLED | reasoning test |
| S9 | L3: transcript host overwrites running host | KILLED | explicit-session test |
| S10 | Desktop: `CHILD_SESSION` ignored in `host_identity` | KILLED | explicit-session test |
| S11 | Desktop: shared id verifies explicit `--session` as current | KILLED | explicit-session test |
| R7 | Codex cache-write not subtracted (re-run) | KILLED (survived in round 1) | forked-child test |
| R1 | newest file in cwd slug (re-run) | KILLED (10 F, 11 E) | concurrent, worktree, newer-Claude-during-Codex, absent identity, … |
| R2 | Claude dedup dropped (re-run) | KILLED | dedup test |
| R4 | Codex cumulative counters summed (re-run) | KILLED | forked-child, codex deltas |

### Suites (`PERRY_PROJECT` and `PERRY_HOME` unset, `__pycache__` purged)

- `bash tests/run`: 155 modules · 4,379 tests · 100.3 s · all green.
- `bash tests/run --tier slow`: 159 modules · 4,482 tests · 148.5 s · all green.
- `git diff --check c48e25fe fe52036d` and `git diff --check 5f182d3c fe52036d`: clean.

### Checking the author's repair claims

- **Net lines and suite counts.** Reproduced: +113 / +122 / +235, and 4,379 / 4,482.
- **H1, H2 and M1 real-data figures.** Reproduced exactly.
- **"All 16 mutants killed".** Consistent with S1, S4–S11 and R7. Their set did not include S2 or S3.
- **Open risk (plain CLI).** Stated honestly in the result and in `bin/README.md`, but not carried into `host-capabilities.md` (R-M1).

### Still not verified

- A real plain-CLI Claude subagent's environment (R-M1).
- A real nested `codex exec` under Claude Code.
- The semantics of a nonzero Codex `cache_write_input_tokens`.
