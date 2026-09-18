# TASK-471 result — session budgets at safe task boundaries

Date: 2026-09-18. Author: Coding Agent (Claude Opus 5, a Claude Code Desktop subagent in an isolated worktree). This is the author's result, not a V4 verdict.

## Identity

- **Branch:** `worktree-agent-a3b7edb300c9fac3d`.
- **Base:** `be5b83cf6d76b2ee655d1b002a4abfbeaa6b9ac3` (main's tip at dispatch). The worktree started at `0b5bf99e`, 315 commits behind with no local commits, and was fast-forwarded to the base before any edit.
- **Commits:**
  - `6bb4dc6f`: the code round (R-M1, R-L1, R-L2, R-L3 and their prose).
  - `61c215d5`: the procedure (checkpoints, handoff shape, resume checklist).
  - The commit that adds this file is the head. It changes nothing else.

## Acceptance → evidence

| # | Criterion | Evidence |
|---|---|---|
| 1 | Inspect TASK-309 and leave executor checkpointing there | I read TASK-309 (`perry-task list`, read-only). It is about a dispatched agent committing before expensive work, and its status is `not_started`. This row adds nothing on the executor side. At a boundary, an in-flight dispatch is only *listed* as pending in the handoff, for the next session to process (`subcommands.md § Budget boundary`, "Safe boundary"). |
| 2 | Check before a task or review dispatch and after a completion. Reuse the measured source and the configured ceiling | **Before:** `dispatch.md § Pre-flight`, `review.md § 4`, and the autopilot stop check. **After:** `subcommands.md § close-task` ("Then the after-task checkpoint") and `dispatch.md § On completion` step 8. Every checkpoint runs the same `perry-context-budget`, which binds its own session and resolves the ceiling. The procedure says "never restate either", and no second number appears anywhere. |
| 3 | At or over: stop at an atomic boundary, record pending work, decline the next dispatch. Never interrupt a store write or auto-resume | The `OVER` row of the table in `§ Budget boundary`, plus its "Safe boundary" paragraph. Case 5 below shows a planted interrupted transaction: the recovery gate reports `blocking: true`, and the boundary records it rather than repairing it. |
| 4 | Handoff: goal, task/spec, base/head/worktree, changes, receipts, unresolved criteria, pending decisions, next command. At most 8 KiB, evidence by reference | `work/state/handoff_TEMPLATE.md § 0 Resume point` has those fields, plus pending work and the budget verdict. A handoff filled for this very row at a boundary measures **3,593 bytes**. The empty template is 3,666 bytes. |
| 5 | A fresh reader verifies revision and recovery/task state. A changed base or stale receipts mean revalidation. No host reset | "Resuming" in `§ Budget boundary`: recovery and interrupted gates, then head vs `git rev-parse HEAD`, then base vs main's tip, then `perry-task list --json`. "Perry never resets the host session or schedules one." See cases 6 and 7. |
| 6 | Below / at / over, unknown, active operation, stale handoff, changed source. Unknown is visible, bounded and never "within budget" | See the seven cases below. For `unknown`, the procedure prints `context: unknown — not measured` with its reason. Autopilot is bounded by `--max-dispatches`. An interactive session asks at each boundary whether to hand off now or run one more task. |

## Carried findings → change, test, mutation

| Finding | Change | Test | Mutation (killed?) |
|---|---|---|---|
| R-M1: a plain-CLI subagent would bind its main session | `host_identity()` exports no identity for `claude-code`, and `bind()` returns `unknown` with "unverified identity". The Claude branch of `locate()` is gone. | `test_a_claude_session_id_binds_nothing_because_a_subagent_carries_its_parents` covers two shapes, each with a matching transcript present: plain CLI (id, no flag) and Desktop (id + flag + `AI_AGENT`). | **M1:** the base tool is restored whole. KILLED, with 7 failures across 6 tests, the R-M1 test among them. **M1b:** a targeted revert that trusts the id unless `CLAUDE_CODE_CHILD_SESSION` is set, which was TASK-468's rule. KILLED, with 4 failures across 3 tests. |
| R-L1: the last `session_meta` wins | `read_codex` keeps the first `session_meta`. | `test_a_forked_child_is_its_own_session_not_the_parent_it_embeds`. The fixture's forked child now embeds its parent's meta second, as the five real children do. | **ML1:** `and not meta` removed. KILLED, 3 tests. |
| R-L2 S2: `last_token_usage` honoured only with `forked_from_id` | No code change needed: the fix already ignores `forked_from_id`. | `test_an_inherited_total_is_not_a_request_with_or_without_forked_from_id` has a child that inherits without `forked_from_id`, as real child `019fac0b…` does. | **S2:** KILLED. |
| R-L2 S3: the inherited zero-delta snapshot is kept | No code change. | The same test binds an idle forked child, which has no request since the fork. The expected answer is `unknown` ("no usage record"), not a measured 0. | **S3:** KILLED. |
| R-L3: the Desktop explicit path is undocumented | `reference/host-capabilities.md` now says: the only Claude verdict is `--session <file>`, labelled `explicit`, and it is the caller's assertion, never a checkpoint's gate. `subcommands.md § Budget boundary` and `autopilot.md` say the same. | The existing `test_an_explicit_other_session_is_historical_and_never_gates` asserts `explicit` for a Claude `--session`, even when the id matches. | (Covered by M1/M1b, which turn that `explicit` back into `current`.) |

The mutation method:
- one fresh copy of the tree per mutant (`.git`, `perry/`, `.perry/` and caches excluded);
- every `__pycache__` purged;
- `python3 -B -m unittest tests.test_context_budget`.

The unmutated copy (M0) is green. The runner and log are in the scratchpad (`t471/mutate.py`, `t471/mutation.log`) and are not shipped.

### R-M1: what I observed and what I chose

**Verified from this subagent's own environment.** I am a Desktop subagent. My environment has:
- `CLAUDE_CODE_CHILD_SESSION=1`;
- `AI_AGENT=claude-code_2-1-274_agent`;
- `CLAUDE_CODE_ENTRYPOINT=claude-desktop`;
- `CLAUDE_CODE_SESSION_ID=bcc8bb26-9e88-4097-95fb-951ab3eeeda7`. That id is the PMO's main transcript (`~/.claude/projects/-Users-bytedance-proj-Perry/bcc8bb26….jsonl`), not mine. Mine is `…/bcc8bb26…/subagents/agent-<id>.jsonl`.

None of my 56 variables names this subagent. The flag and `AI_AGENT` values match those the PMO recorded for the main session in `TASK-468-integration/acceptance.md`.

**Not verified.** I could not observe any of the following: a plain-CLI main session or subagent; whether the plain CLI exports `CLAUDE_CODE_SESSION_ID` at all; the main session's `CLAUDE_PID` or `CLAUDE_CODE_HOST_SESSION_ID`. I did not start a plain-CLI session, because that would start a new account-billed session outside this task's bound.

**The choice.** I took the fail-safe route: with no verified distinguishing signal, Claude reads `unknown`. On the real host, run from this subagent:
- the default gate prints `unknown` ("unverified identity…"), exit 0;
- `--session <the PMO's transcript>` prints `explicit`, **`OVER` at 417,270 tokens, exit 1**. That is the parent's context reported to a child. This is why no checkpoint passes `--session`, and why the procedure refuses to treat `explicit` as a verdict.

**Consequence.** On Claude Code the gate never gates, main session included. Autopilot there always falls back to `--max-dispatches`, and an interactive session gets the per-boundary question. A verified signal plus a fixture is what would re-enable Claude binding.

## The seven cases

The fixtures are disposable: `HOME` and the project are under the scratchpad, `t471/cases/`. The runner is `t471/cases.py` and its output is in `t471/cases.log`. Gate outputs are real runs of this head's tool with `--ceiling 200k`. The "then" column is the procedure's written step, applied by me: an authored walkthrough, not an automated semantic test.

| # | Case | Observed | Then (per `§ Budget boundary`) |
|---|---|---|---|
| 1 | Below ceiling | Codex bound by `CODEX_THREAD_ID`: `OK`, context 50,000, `current`, exit 0 | continue |
| 2 | At ceiling | `OVER`, 200,000 / 200,000, exit 1 | finish the step in hand, dispatch nothing, write handoff § 0 |
| 3 | Over ceiling | `OVER`, 250,000, exit 1 | same as case 2 |
| 4 | Unknown telemetry | `unknown`, context `null`, exit 0, for each of: Claude plain-CLI shape (a matching 250k transcript present), Claude Desktop shape, OpenCode, and Codex with no thread id. Text form: `verdict : UNKNOWN — not gating` plus the reason. The same result held on the real host from this subagent. | print `context: unknown — not measured`, never "within budget". Autopilot: bounded by `--max-dispatches`. Interactive: ask at this boundary. |
| 5 | Active operation | Sample project copy. `perry-state --section recovery` gives `blocking: false`. After planting `.perry-task-transaction.json` (phase `commit`, 1 entry), it gives `blocking: true` and names the path. | not resumed or repaired at the boundary. The handoff lists it under Pending work, and the next session's router step 2 stops on it. |
| 6 | Stale handoff | The recorded head and receipts are at `8b13ee2a`. After one more commit, `git rev-parse HEAD` gives `9f47f94b`. | head moved, so the receipts are older than the head: re-run the cited checks before relying on them |
| 7 | Changed source | The recorded base is `5c0a678d`. Main's tip is `002c1d03`. | base moved: revalidate against the new base before integrating |
| control | Unchanged | Base and head both equal their recorded values | run the recorded next command |

## Context bills (`bin/perry-context-budget --bill all`)

| Bill | Before (`be5b83cf`) | After | Δ | Cap | Spare after |
|---|---:|---:|---:|---:|---:|
| snapshot | 78,165 | 78,137 | −28 | 80,000 | 1,863 |
| add-task | 99,351 | 99,351 | 0 | 100,000 | 649 |
| close-task | 90,213 | 92,252 | +2,039 | 95,000 | 2,748 |
| dispatch | 113,558 | 113,742 | +184 | 115,000 | 1,258 |
| plan-phase | 107,747 | 107,747 | 0 | 110,000 | 2,253 |

No cap was raised.
- **snapshot:** `host-capabilities.md` shrank by 28 bytes, which leaves TASK-469 room in that file.
- **dispatch:** gains two pointer lines.
- **close-task:** carries the procedure itself, in `subcommands.md § handoff`, the section that owns handoffs.
- The autopilot rationale stays in `autopilot.md`, which no bill loads. So does the review pointer, in `review.md`.

## Suites

With `PERRY_PROJECT` and `PERRY_HOME` unset and `__pycache__` purged:

- **Code round:** `tests.test_context_budget` gave 41 tests OK.
- **First full run** (`61c215d5`'s tree before that commit): 155 modules · 4,381 tests. **One module was red:** `test_spec_scannability`, 2 tests. My new `§ Budget boundary` text said "worktree" outside every governed span, which is a deliberate containment check. I reworded it to "checkout" and re-ran the module alone: 71 OK. That fix is in `61c215d5`.
- **Final runs** on the tree committed with this file (`bash tests/run`, then `bash tests/run --tier slow`), run on the working tree before this file was committed, which differs from the head only in this line: **155 modules · 4,381 tests, all green**, then **159 modules · 4,484 tests, all green**. Both were re-run on the committed head, and the results are reported to the PMO.
- `git diff --check be5b83cf HEAD`: clean.

## Line delta (`git diff --numstat be5b83cf 61c215d5`)

| File | + | − | Net |
|---|---:|---:|---:|
| `bin/perry-context-budget` | 18 | 19 | −1 |
| `tests/test_context_budget.py` | 69 | 30 | +39 |
| **Python/test total** | | | **+38** |
| `bin/README.md` | 17 | 10 | +7 |
| `bin/ARCHITECTURE.md` | 3 | 2 | +1 |
| `reference/host-capabilities.md` | 7 | 6 | +1 |
| `work/reference/subcommands.md` | 24 | 0 | +24 |
| `work/reference/autopilot.md` | 14 | 8 | +6 |
| `work/reference/dispatch.md` | 2 | 1 | +1 |
| `work/reference/review.md` | 2 | 0 | +2 |
| `work/state/handoff_TEMPLATE.md` | 22 | 0 | +22 |

This row is unlinked, so USER-970's ≤ 0 rule does not bind it. The +39 in tests comes from four things:
- the two-shape R-M1 fixture;
- the R-L1 and R-L2 fixtures;
- moving the concurrent, ambiguous and mismatched-identity checks from Claude to Codex, the host that still binds by identity, so those checks still run;
- a `forked` switch on the Codex fixture helper.

No test was deleted without its check moving.

## Deviations

1. **Files outside the listed scope.**
   - `bin/README.md` and `bin/ARCHITECTURE.md` described Claude binding by `CLAUDE_CODE_SESSION_ID` and would have been false after R-M1, so I updated them.
   - `work/reference/review.md` gained one line so a review dispatch hits the before-dispatch checkpoint the spec names.
2. **Claude binding is off for every Claude session, the plain-CLI main session included.** This is the fail-safe reading of R-M1, as the brief directs. It widens TASK-468's Desktop-only `unknown` to all of Claude Code.
3. **Tests moved hosts.**
   - The concurrent-session, ambiguous-id and mismatched-id checks now run on Codex.
   - The worktree-slug test became the R-M1 fixture: a newer 900k transcript in the cwd slug is still present, and Claude still reads `unknown`.
   - Claude parsing tests (dedup, reasoning, children, workflow, composition, ceiling) now read their fixture by `--session`, so they report `explicit` rather than `current`.
4. **The interactive unknown fallback is a user question at each boundary.** It is bounded to one more task per answer. It is not a new count or a second budget.
5. **The seven cases are an authored walkthrough on fixtures, with real command output.** They are not an automated test of the procedure's wording. Python does not judge document meaning, and the plan rules out a new evaluation framework.
6. **Parallel-work risk.** TASK-469 also edits `reference/host-capabilities.md`. My edit touches only the matrix's telemetry cell and the paragraph below the executor table, and nets −28 bytes.

## Not verified

- Plain-CLI Claude environments, main or subagent (R-M1 stays fail-safe, not settled).
- Whether a real host completion arriving after an `OVER` stop is processed correctly by the next session. The procedure says it is, but no live dispatch was run.
- A fresh-context V4. That is for an independent reviewer.
