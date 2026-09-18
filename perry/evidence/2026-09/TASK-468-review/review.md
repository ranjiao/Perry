# TASK-468 independent V4 review

Date: 2026-09-18. Reviewer: Claude Opus 5, a fresh-context Claude Code child session in an isolated worktree. I am not the author of the candidate.
Target: branch `worktree-agent-abf710762750f9d9b`, head `5f182d3c`, base `c48e25fe`. I reviewed `git diff c48e25fe 5f182d3c` against the following:
- `TASK-468-spec.md`;
- the iteration plan;
- the four findings carried from `TASK-456-457-integration/acceptance.md`;
- USER-969;
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
| 6 | PASS (lines by exception) | Negative fixtures fail when binding is reverted. Legacy tests are green. Net +166 = `bin/perry-context-budget` +79 and tests +87, which I verified with `git diff --numstat`. USER-969 covers it. I saw no padding: the code is dense and has no dead helpers. |
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
- `bash tests/run --tier slow`: SLOW_RESULT.
- `git diff --check c48e25fe 5f182d3c`: clean.
- No red module, so nothing needed a re-run alone.

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
