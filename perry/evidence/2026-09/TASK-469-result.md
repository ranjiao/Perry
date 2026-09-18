# TASK-469 result — bounded startup routing

Date: 2026-09-18. Author: Coding Agent (Claude Opus 5). Not reviewed: V4 is still
owed by a fresh-context reviewer. No merge, push, tag or release allocation.

## Identity

- **Base:** `be5b83cf6d76b2ee655d1b002a4abfbeaa6b9ac3`. The worktree started 315 commits stale at `0b5bf99e` with no local commits, and was fast-forwarded to main's tip.
- **Branch:** `worktree-agent-af202feafc663d266`.
- **Commits:**
  - `078d6da2`: routing, lane pointers, `reference/startup.md`, guard.
  - `86121e40`: fixes found by the transcript run.
  - This evidence commit.
- **Tree for the numbers below:** the code head is `86121e40`; this file adds no shipped bytes.

## What changed

- **`SKILL.md` § Mandatory first move.** A route table now comes before step −2, with exactly three routes:
  - **Explain** runs step −2, then only the pages that answer.
  - **Query** runs −2, −1, 1 and 2, then one projection.
  - **Change** runs −2 to 3. Bare `/perry` goes on to 3b–6. A lane skips its own −3 to −1 and keeps its gates.

  Added lines:
  - "Unclear → ask which."
  - "Nothing reads state before step 2."
  - "Once per operation; re-read after a write."

  Steps −2 to 3 are unchanged in wording and order. Recovery still runs before interrupted, which runs before the state read. First-time setup stays guarded.
- **Router bytes paid for by moving rationale out (P1).** None of these was a rule:
  - the interrupted-gate rationale sentence;
  - the "abandoned adoption reports `installed: false`" rationale, which `reference/snapshot.md § Why the interrupted-run gate exists` already holds;
  - a restatement of snapshot.md's steps 3b–6.
- **The three lanes.**
  - Their steps −3 to −1 are one pointer to the router's startup: set `$PERRY_HOME`, host, update check, then the blocking recovery and interrupted-run gates before the lane reads state.
  - "Always run before any subcommand" becomes "any subcommand but `help`; a question takes the Explain or Query route".
  - Before this change, **no lane named the recovery gate at all**.
- **`reference/startup.md` (new, L2, 6,111 B).** Rationale only, no restated step. It covers:
  - what counts as a project-state read;
  - per-route reasons;
  - the rules for when a read is reused and when it is refreshed;
  - unclear and mixed intent, and why no classifier decides it (NN-4);
  - the table of eight cases.
- **`reference/snapshot.md`.** The header names the route table and the recovery gate. At step 6 the lane starts after its −3 to −1.
- **`reference/host-capabilities.md`.** One sentence, in "Detect once per session" only: no re-detection on the hand-off to a lane, and an explanation needs no detection unless the answer depends on the host. The TASK-471 caveat area is untouched.
- **`tests/test_startup_routing.py` (new, 7 tests).** A structural guard. It checks shape, never intent.

## Acceptance criteria → evidence

| AC | Evidence | Verdict |
|---|---|---|
| 1. Three paths. Explain avoids the dashboard, update check, mode load and state reads. | The route table. `test_explain_runs_no_state_config_or_update_step` (killed by M1). Transcript cases 1–2: no project command ran. | Met |
| 2. A query checks recovery first and reads only the projection. Blocking and interrupted keep stop/choice. Never resumes implicitly. | Query runs step 2 (`test_every_state_route_runs_the_recovery_gates`, M2). Order recovery → interrupted → state (`test_recovery_precedes_interrupted_precedes_state`, M5). Round-2 cases 4, 6, 7. | Met, with the note on case 4 below |
| 3. Mutation keeps all gates. `/perry` still produces the snapshot. | Change runs −2 to 3 (M4). Lanes keep hook, ownership, evidence and high-stakes rules; nothing was removed from them. Case 3 produced the full snapshot. Case 5 went through the router gates, then the lane, then the write. | Met |
| 4. One shared contract; no repeated ritual within an operation; results refreshed after writes. | The lane pointers (`test_each_lane_defers_its_startup_to_the_router`, M8–M10). Refresh rules are in `startup.md § Once per operation`. Case 5 re-listed after its write. | Met |
| 5. Eight agent-reviewed cases with expected reads, actual reads and a decision. No Python classifier. | The matrix below. The test grades structure only. | Met |
| 6. All eight cases meet their outcomes; pointers and guards valid; fixed and conditional load sets logged. | Round 1: 6 of 8 clean; cases 4 and 5 read extra. Fixed in `86121e40`. Round 2 (4, 6, 7): gate order clean. Full and slow suites green. Load sets are below. | Met for safety and route. Case 5 read more than a minimal Change would (below). |

## Transcript matrix

**Method.** A fresh-context general-purpose agent read `$PERRY_HOME/SKILL.md` and followed it. It was given only the request and a fixture path, never the expected reads. It worked on disposable copies of `tests/fixtures/sample-project` (clean, mutation, and blocking, which adds a malformed `.perry-task-transaction.json`) and `tests/fixtures/interrupted-adoption` (one stale adopt dossier). The copies are under the session scratchpad, never this repo's `perry/`. Raw logs: scratchpad `t469/transcripts.md` (round 1, at `078d6da2`) and `t469/transcripts-round2.md` (cases 4, 6, 7 at `86121e40`).

| # | Case, request | Expected route and reads | Actual reads and commands | Decision | Outcome |
|---|---|---|---|---|---|
| 1 | Explanation: "How does Perry decide what to recommend next?" | Explain: router + `reference/next.md`; no project read | `reference/next.md` only; no command | Explained | Pass |
| 2 | Help: `/perry help work` | Explain: router + `work/SKILL.md` index | `work/SKILL.md`, `reference/config.md` § Pack capabilities; no project read | Printed the index with pack rows marked conditional | Pass. Pack-row handling is now written in `startup.md` |
| 3 | Overview: `/perry` | Change: steps −2 to 6 | detect-host, update-check, config, recovery, interrupted, `--compact`, `--section next`, `perry-explain` ×2; host-capabilities, snapshot, `modes/project.md`, next | Snapshot within 12 lines, then "What do you want to do?" | Pass |
| 4 | Narrow status: "Is REL-002 blocked, and on what?" | Query: config, recovery, interrupted, one projection | **R1:** `perry-task list --json` **before the gates**, then the gates, then `perry-explain` and the list again. **R2:** detect-host, config, recovery, interrupted, `perry-explain REL-002` (found only the spec), `perry-task list --json` | Answered: blocked on USER-014 ("Confirm staging env default") | R1 fail (read state before gates). R2 pass on order; two projection reads, the first a miss |
| 5 | Task mutation: `/perry work start REL-009` | Change: −2 to 3, then the work lane from step 0 and its subcommand page | Router gates, `--compact`; lane: hook, `--json`, `--dashboard`, journal ×2, `perry-dispatch-limit list`, `next --lane work`, `subcommands.md`, `conversational.md`, `start --dry-run`, `start`, re-list. Also one stray `diff` against the clean fixture | REL-009 is `in_progress`, written to the store and journal | Pass on gates and ownership. Over-read: `--dashboard`, dispatch list and the stray diff were the agent's own additions |
| 6 | Blocking recovery: "How many tasks are open?" (blocking fixture) | Stop after recovery | **R1:** config, recovery, then an `ls` after the stop. **R2:** detect-host, config, recovery, stop | Reported the path and the `JSONDecodeError`; no count | R1 minor fail (a listing after the stop). R2 pass |
| 7 | Interrupted run: same request (interrupted fixture) | Card, then ask; no setup, no resume | R2: detect-host, config (missing), recovery, interrupted, snapshot.md card section | Card; `Abandon it (Recommended)` first because stale; stopped at the question | Pass (R1 also passed apart from an `ls`) |
| 8 | Unclear: "perry tasks?" | Ask before any state read | detect-host, `reference/startup.md` | One question offering the three routes | Pass |

No case resumed a run, wrote in an Explain or Query route, or skipped recovery on a state route in round 2.

## Bytes and bills (`bin/perry-context-budget --bill all`)

| File | Before (be5b83cf) | After (86121e40) | Cap |
|---|---:|---:|---:|
| `SKILL.md` (L0) | 20,453 | 20,426 | 20,480; `test_next_section` growth guard 20,457 |
| `goals/SKILL.md` | 22,415 | 22,237 | 22,528 |
| `work/SKILL.md` | 36,907 | 36,658 | 38,912 |
| `decide/SKILL.md` | 24,081 | 23,932 | 24,576 |
| `reference/snapshot.md` (L2) | 16,426 | 16,675 | 32,768 |
| `reference/host-capabilities.md` (L2) | 6,931 | 7,083 | 32,768 |
| `reference/startup.md` (L2, new) | — | 6,111 | 32,768 |

| Bill | Before | After | Δ | Budget |
|---|---:|---:|---:|---:|
| snapshot | 78,165 | 78,539 | +374 | 80,000 |
| add-task | 99,351 | 99,075 | −276 | 100,000 |
| close-task | 90,213 | 89,937 | −276 | 95,000 |
| dispatch | 113,558 | 113,282 | −276 | 115,000 |
| plan-phase | 107,747 | 107,542 | −205 | 110,000 |

No cap or budget was raised.

**Load sets.**
- **Fixed** (every invocation): L0 only, as before.
- **Explain:** L0 plus the pages that answer.
- **Query:** L0 + `host-capabilities.md` (step −1) + the projection output.
- **Change:** unchanged from the snapshot bill. A lane request adds the lane bill, but no longer re-runs host, update check or `$PERRY_HOME`.
- **Conditional:** `reference/startup.md` (6,111 B), read only when the route is unclear. It is not in any bill, because no index row names it.

**Not claimed.**
- Runtime token savings were not measured. That is TASK-473's protocol.
- Byte figures are not token savings.
- The iteration targets (router ≤12 KiB, lanes ≤24 KiB) are TASK-470's; `work/SKILL.md` is still over 24 KiB.

## Guards and mutation proof

`tests/test_startup_routing.py` has 7 tests. `__pycache__` was purged before each mutant, and the file was restored with `git checkout` after. All 11 mutants were killed with an assertion FAIL, not an ERROR. The unmutated tree is green and the worktree was clean afterwards.

| Mutant | Killed by |
|---|---|
| M1 Explain runs step 1 | explain-runs-no-state |
| M2 Query drops step 2 | state-routes-run-gates |
| M3 Query gains step 0 | query-skips-update |
| M4 Change stops at 1 | state-routes-run-gates |
| M5 recovery and interrupted calls swapped | recovery-precedes-interrupted |
| M6 fourth route | exactly-three-routes |
| M7 case row deleted | eight-cases |
| M8 goals re-adds `perry-detect-host` | lanes-defer |
| M9 decide loses the router pointer | lanes-defer |
| M10 work loses the gates | lanes-defer |
| M11 router +60 B | existing `test_next_section` growth guard |

My first M5 renamed the call, which produced an ERROR. I replaced it with a true swap so the assertion itself fails.

## Suites

With `PERRY_PROJECT` and `PERRY_HOME` unset:
- `bash tests/run` at `078d6da2`: 156 modules, 4,386 tests, all green.
- `--tier affected` each round: green.
- Final-commit full and slow runs: see the addendum at the end. The first slow run at `5fe74346` failed on the missing durations entry (deviation 4).

`git diff --check`: clean.

## Line delta (be5b83cf..86121e40)

- **Prose:** +141 / −26 (`startup.md` +113).
- **Python and tests:** +125 / −0 (one new guard module).
- USER-970: the ≤0 rule binds Objective 4 only. This row is unlinked, so the rule does not apply. No check was deleted or weakened.

## Deviations and open questions

1. **A shared guard now reads a pointer line.** `tests/test_shipped_vocabulary.py::TestStartupRootDescriptionsNameLiveLaneDirectories` requires each lane to keep one `**Set $PERRY_HOME**` line. The lanes keep it inside their router pointer ("the grandparent of this file"), so the guard now reads a pointer. The guard was not edited.
2. **Lane subcommands no longer render the router dashboard.** `/perry work …` runs router steps −2 to 3, including the First-time setup gate, then the lane's own snapshot. Before, the router's "Always run this first" implied both dashboards. This is AC4's intended de-duplication. Decide whether it needs the user's sign-off.
3. **The Query route skips the update check.** AC1 requires this only for Explain; I extended it to Query to keep the query bounded. The update check is not a safety gate. Revert if unwanted.
4. **`tests/durations.json` lists `test_startup_routing.py` as `sec: null, source: null`.** That means "not measured", a value its schema allows. The slow tier's `test_durations_provenance` went red without the entry: it was the only red in the first final slow run at `5fe74346`. Measured figures belong at integration, as with TASK-468.
5. **Pre-existing defects the transcript agents hit.** Out of scope, not fixed, and no rows opened:
   - `reference/snapshot.md` l.71 ends mid-sentence.
   - The card's "fill from the dossier" (snapshot.md) contradicts "never the dossier's frontmatter" (router step 2).
   - The archive path `.perry/<pipeline>/archive/` does not match `.perry/adoption/`.
   - `perry-explain REL-002` resolves to the spec, not the task title.
   - `work start` has no subcommand-index row or reference section.
   - The recovery sentence names no concrete `perry-task` recovery invocation.
   - Router step 1 prompts for first-time setup before step 2's guard. The agents correctly waited for step 2, but the order is implied, not stated.
6. **Case 5 over-read.** The lane's own ritual (`--json` plus journal) legitimately follows the router's `--compact`, so the Change route reads state twice. Removing that is TASK-470's actual load-set work, not a routing decision.
7. **The transcripts are agent-run, but not V4.** The agents were fresh-context, yet I, the implementer, briefed them and graded them. V4 must re-check independently.
