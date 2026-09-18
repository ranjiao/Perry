# TASK-468 result — bind usage measurement to the actual host and session

Date: 2026-09-18. Author: Coding Agent (Claude Opus 5, a Claude Code child
session in an isolated worktree). This is an ordinary RESULT. It awards no
V4 and no architecture verdict.

## Stop condition: the phase line budget is exceeded

**The delivery is +166 net Python/test lines against a budget of ≤ 0.** It is
not ready for integration until someone with the authority decides. The
branch carries the full implementation so the decision can be made against
real code and measured figures, not an estimate.

| | Added | Deleted | Net |
|---|---:|---:|---:|
| `bin/perry-context-budget` (production) | 230 | 151 | **+79** |
| `tests/test_context_budget.py` (tests) | 168 | 81 | **+87** |
| Total | 398 | 232 | **+166** |

Measured with `git diff --numstat c48e25fe <head> -- bin tests`. No other
Python or test file changed.

**Simplification already taken, all behaviour-preserving:**

- The 4 MB tail read and its full-scan fallback are gone. Dedup, cumulative
  deltas, coverage and totals need every record, so the file is now streamed
  once.
- The newest-file selector and the slug helper are gone, and the spec
  requires that.
- The ceiling lookup is one ordered loop instead of three copied
  try-blocks.
- The config read is a single `read_text` guarded by `OSError`.
- `--composition` reuses the shared record reader.
- The tests load the schema ceiling once.
- The legacy rationale moved to `bin/README.md` as prose, not Python.

**What would be needed.** A recorded decision (a `USER-` ask) that does one of
the following:

1. **Grants TASK-468 an exception of +166 lines.** This is the delivery as it
   stands.
2. **Authorises removing `--composition`.** That is about 109 lines: a
   53-line function, about 20 lines of printing and a 36-line test class.
   This alone still leaves about **+57**, so it needs an exception as well.
   `--composition` is a user-facing diagnostic mode, and it produced the
   52%/26% figure `AGENTS.md` cites. Removing it is a scope decision, so I did
   not take it.

**Smallest honest alternative inside ≤ 0.** A binding-only delivery:

- Keep the identity lookup (`host_identity`, `bind`, `locate`), the identity
  check against the file, and the `unknown` outcomes.
- Keep Claude's per-message dedup, because the context figure needs it.
- Defer the rest to a follow-up row:
  - the Codex adapter;
  - children and coverage;
  - the five-category totals and the provenance block.

That meets criterion 1 and the Claude half of criterion 2. It fails
criteria 3 and 4 and the Codex half of 2, so it is not TASK-468 as written.

## Identity

- Base: `c48e25fe2ca9be598fe7be919b246eaefa30356e`. At dispatch the worktree
  was on 0b5bf99e, with no local commits. I fast-forwarded it to base before
  any work.
- Branch: `worktree-agent-abf710762750f9d9b`.
- Commits:
  - 26a4053c: frozen baseline only, committed before any tool edit;
  - 04e91c18: implementation, tests and docs;
  - the commit that adds this file.
- Files changed: `bin/perry-context-budget`, `tests/test_context_budget.py`,
  `bin/README.md` (the table row, plus a new `### perry-context-budget`
  section under § The argument, per tool), `reference/host-capabilities.md`
  (one matrix row and one paragraph), and the evidence under
  `perry/evidence/2026-09/`.

## What changed

- **Binding.** `bin/perry-detect-host` names the host first, so a variable
  inherited from an outer host is not read. The transcript is then the one
  whose name carries the host's own session id. `CLAUDE_CODE_SESSION_ID`
  matches `~/.claude/projects/*/<id>.jsonl`. `CODEX_THREAD_ID` matches
  `~/.codex/sessions/*/*/*/rollout-*-<id>.jsonl`. The file's records must name
  the same session.
- **`unknown`, exit 0.** Each of these reports `unknown` with its reason:
  zero or several matches; a contradicting file; a Claude child session,
  which inherits its parent's id; OpenCode; an unidentified host; a
  transcript with no usage.
- **`--session`.** The session it names is `current` when its records name the
  host's session. It is `historical` when they name another; then the verdict
  is `historical`, the figures are still reported, and it never exits 1. It is
  `explicit` when the host gives no identity.
- **Adapters.** Both read into five categories: `input` (uncached),
  `cached_input`, `cache_creation`, `output`, and `reasoning`, which is a
  subset of output and never added to it.
  - Claude: counts once per message id, and uses `thinking_tokens` as the
    reasoning figure.
  - Codex: takes deltas of the cumulative `total_token_usage`. It skips a
    repeat and treats a drop as a counter restart. `input` is `input_tokens`
    minus cached and cache-write input.
- **Report.** It carries:
  - `host`, `binding`, `scope`, `session`, `parent`, `transcript`, `cwd`;
  - `last_record_at` and `transcript_age_min`;
  - `coverage` and `gaps`;
  - `usage`, including children;
  - `children` (spawned, found, with usage) and `records` (requests,
    duplicates, malformed, truncated);
  - `measured`, `estimated`, and `cost`/`quota: "unknown"`.
- **Carried fixes from the TASK-456/457 review, all four done:**
  - The rationale is restored as README prose. That covers the NN-1 direct
    config read, loud abstention, the tail scan and why it went, and the
    measured cost argument.
  - A refused bill exits 1 and prints its reason to stderr.
  - `--help` wins from any position, so `--help --bill bogus` exits 0.
  - References after a parenthetical note are kept.
  - Their marginal cost is 0 production lines and about 8 test lines. It is
    included in the +87.

## Acceptance criteria

Log: `TASK-468-mutation.log`. Each mutant ran against `tests/test_context_budget.py` alone, with every
`__pycache__` purged before the run, and was then restored (restore verified
byte-equal). The unmutated module is green (37 tests). All 19 mutants were
killed. Under M1 the three key negative fixtures fail on their assertions, not by a crash. M7 first died by a crash. I rewrote it so the
mutated tool runs, and it was then killed by an assertion.

| # | Criterion | Test(s) | Mutation → result |
|---|---|---|---|
| 1 | Explicit source or verified host identity; no newest-file verdict; historical labelled | `TestTheSessionIsBoundNeverGuessed.*`, `test_an_explicit_other_session_is_historical_and_never_gates` | M1: binding replaced by the newest transcript in any project → KILLED. Concurrent, worktree and newer-Claude-during-Codex all fail on the asserted session/context, plus 5 more. M1b: legacy newest-in-cwd-slug → KILLED (18 tests; 10 failures, 9 errors). M5: historical gates like current → KILLED |
| 2 | Claude and Codex fixtures; the seven categories; OpenCode unknown with a reason | concurrent: `test_a_concurrent_newer_session_in_the_same_project_is_not_this_one`. cwd/worktree: `test_a_worktree_cwd_still_finds_the_session_by_id_not_by_its_own_slug`. Newer unrelated: `test_a_newer_claude_transcript_during_a_codex_run_is_not_the_codex_session`. Absent identity (Claude, Codex, Claude child), ambiguous, mismatched, OpenCode, unknown host: `test_absent_ambiguous_mismatched_or_unsupported_identity_is_unknown_not_zero`. Missing usage (both hosts): `test_a_transcript_with_no_usage_yet_is_unknown_not_zero`. Malformed and truncated: `test_claude_repeats_a_message_per_block_and_it_counts_once` | M2 (child keeps the parent id), M3 (no check against the file), M4 (ambiguous takes the first), M12 (no OpenCode branch), M11 (bad lines not reported) → all KILLED |
| 3 | Categories per host schema; reasoning not double-counted; dedup; cumulative deltas | `test_claude_repeats_a_message_per_block_and_it_counts_once`, `test_codex_cumulative_totals_become_deltas_with_repeats_and_resets` | M6 (count per record) → KILLED. M7 (reasoning added to output) → KILLED. M8 (sum cumulative totals) → KILLED. M9 (no reset handling) → KILLED |
| 4 | Host, session and parent identity; source; freshness; coverage; measured vs estimated; partial when a child is missing; cost and quota unknown | `test_claude_children_are_counted_and_a_missing_one_makes_coverage_partial`, `test_a_codex_child_names_its_parent_and_is_included` | M10 (a missing child is not partial) → KILLED. M13 (Codex children dropped) → KILLED |
| 5 | Frozen baseline before workflow edits; the five static bills retained | `perry/evidence/2026-09/TASK-468-baseline/` in commit 26a4053c, which precedes 04e91c18. `TestDeclaredBills.*` (5 tests, caps unchanged) | n/a (receipt). The bill caps assertion is unchanged |
| 6 | Negative fixtures fail when binding is reverted; legacy tests green; lines ≤ 0 | M1/M1b above. Legacy gate, ceiling, composition and bill tests all green | **Lines: NOT met, +166.** See the stop condition |
| C | Carried findings | `test_cli_conflicts_and_installation_default`, `test_shared_lane_and_non_l2_paths`, `test_missing_ambiguous_and_escaping_declarations_are_refused` | C1 (help loses to a bad `--bill`), C2 (note drops later refs), C3 (refusal exits 2), C4 (refusal on stdout) → all KILLED |

Real-transcript checks:

- **Codex rollout** (read-only, `--session`): the context was 121,698, equal to
  the host's own `last_token_usage.input_tokens`. `input` plus `cached_input`
  was 2,397,634, equal to the cumulative `input_tokens`.
- **41 MB Claude transcript:** 1.27 s wall. 3,389 requests from 8,174 records.
  Coverage was partial: 25 of 110 spawned children had no transcript.
- **This child session, with no `--session`:** `unknown`, "absent identity".
  At base, the same session with `--root` on the checkout reported the
  parent's 352,067 as `OVER`.

## Baseline receipt

`perry/evidence/2026-09/TASK-468-baseline/README.md` and `receipt.json`
(sha256 `6cf3d642…d6d1`). It was captured at c48e25fe on 2026-09-18 at
16:18:59 +0800, before any edit.

- **Settings:** host claude-code (Desktop), model claude-opus-5, effort high,
  child session.
- **Static bills:** all five, with per-file bytes and sha256.
- **Claude inventory:** 58 sessions and 512 subagent files.
- **Parent session aggregate:** 167 distinct messages from 300 records.
- **Codex inventory:** 459 rollouts, 19 of them Perry's, with their
  aggregates.
- **The legacy gate's false attribution:** the parent's 352,067 reported for
  the child.

It holds paths, counts and numbers only; no transcript content was copied.

## Suites

- **Baseline, at c48e25fe in this worktree, before edits:**
  - `bash tests/run`: 155 modules, 4,373 tests, 99.5 s, green;
  - `tests/run --only test_context_budget`: green.
- **Per round, on the implementation:**
  - `--tier affected --base c48e25fe`: 19 modules, 714 tests, green;
  - `test_context_budget`, `test_bin_argument_contract`, `test_host_support`,
    `test_shipped_vocabulary` and `test_bin_surface` directly: 240 tests,
    green.
- **Final full and slow:** recorded below, after the commit that adds this
  file.

## Deviations and open questions

1. **Line budget exceeded (+166).** This is the stop condition above, and it
   needs a decision.
2. **Explicit `--session` with no host identity still gates.** Its scope is
   `explicit`, which is the caller's assertion. I read criterion 1 as
   accepting an explicit source, so it can yield a verdict. The stricter
   reading is that only a verified identity gates. That is a one-line change
   if the reviewer prefers it.
3. **A Claude child session cannot measure itself.** It is `unknown`, because
   its only exported id is the parent's. The child's own
   `subagents/agent-<id>.jsonl` is not identifiable from the environment
   alone.
4. **Detection inherits `perry-detect-host`'s precedence.** Claude Code
   started from inside a Codex shell would be detected as `codex-cli` and bound
   to the outer Codex thread. `PERRY_HOST` overrides that. I did not test it
   against a real nested launch.
5. **Codex `cache_write_input_tokens` is an assumption.** I treat it as inside
   `input_tokens`, as `cached_input_tokens` is, so it is never added twice.
   The host does not document this. It was 0 or absent in every Perry rollout
   I inspected.
6. **Codex spawn detection is a structural rule.** Coverage counts
   `function_call`/`custom_tool_call` records named `spawn_agent`, and children
   are found by `parent_thread_id` in their first record. It holds for rollouts
   through cli 0.155.
7. **The JSON payload changed.** `scanned_whole_file` is gone, many fields are
   new, and `verdict` can be `historical`. `autopilot` reads only the exit
   status. Other consumers were not found by grep.
8. **The bill exit contract changed.** A refused bill is 1, not 2, per the
   carried finding and `bin/ARCHITECTURE.md` §5.
9. **`work/reference/autopilot.md` is now incomplete.** It still says
   `unknown` "means the host keeps no transcript this tool can read", and
   `unknown` now also covers absent, child and ambiguous identity. It is out
   of scope and unedited.
10. **`bin/ARCHITECTURE.md` is not updated.** Descriptively, it should mention
    two things: the tool now calls `perry-detect-host`, and it reads
    `~/.codex/sessions`. It is out of scope and unedited.
11. **The baseline capture script is quoted, not committed.** It is inside the
    baseline README, not a `.py` file, so it does not count as Python. Its
    sha256 is recorded.
