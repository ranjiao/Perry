# TASK-473 — token-efficiency iteration: independent static and safety acceptance

Date: 2026-09-21. Reviewer: Review Agent (Claude Opus 5, fresh context, isolated
worktree `agent-a344254e237254712`). I wrote none of TASK-468–472 and was not
asked to agree with them. Criteria: `TASK-473-spec.md`, and the plan
`2026-09-18-token-efficiency-iteration-plan.md` for targets and the eight safety
scenarios.

**Scope, as the user set it (USER-976).** Static and safety acceptance only. No
live before/after runtime session was run. Runtime savings (criteria 1–3) are
**UNMEASURED**, and runtime acceptance stays **OPEN** under criterion 6. Byte
counts below are static declared file bytes. They are not tokens and are never
used as a proxy for token savings. USER-972 applies: Claude Code self-usage reads
`unknown` in every session.

## Verdict in one paragraph

**The iteration is not accepted. Criteria 4 and 5 fail on this evidence, and
criteria 1–3 are unmeasured.** Identity binding holds: every negative fixture I
mutated went red. What fails is independent of runtime:

- **close-task misses the ≥30% static target against the pinned pre-iteration
  baseline:** −28.04%. TASK-470 reported −30.09% against a mid-iteration base.
- **Three of the five deliveries (TASK-469, TASK-470, TASK-471) tripped an
  architecture trigger but have no integration architecture review on record.**
- **Only TASK-468 has an on-disk exact-candidate receipt** (merge-check receipt,
  full and slow logs). The other four have recorded counts only.
- **TASK-469 closed at V3 after three V4 FAILs.**
- **One safety scenario has no fixture**: changed source after a handoff.
- **Three prose safety rules survive a meaning-flip mutation**: the blocking
  stop, never-resume, and the Change route's definition.

## Freeze

| | SHA | How chosen |
|---|---|---|
| Candidate | `42d0651fa50ecd0152db158d4ca0b600466ce9c3` | Integrated `main` given by the PMO. My worktree was fast-forwarded to it (`--ff-only`), and it is clean. |
| Pre-iteration baseline | `820da3b1849df4f7155baf976b1045c6590bd129` | The first of the five deliveries to merge was TASK-468, at `8a3f56d5`. This is that merge's first parent. It is product-identical to `c48e25fe`, TASK-468's frozen baseline (`TASK-468-baseline/`): `git diff --stat c48e25fe 820da3b1` touches only `perry/` and `.perry/`. My five bills at `820da3b1` equal that baseline's recorded bills byte for byte. |

Each tree was extracted with `git archive` into a scratch directory derived with the
`perry-scratch-derivation` block. The host refused the inline `$(git …)`, so I ran
`git rev-parse --show-toplevel` and `echo $TMPDIR` separately:
`$TMPDIR/perry-scratch/agent-a344254e237254712/{base,cand,mut,true,logs,tools}`.
Every log cited below is kept there, pass or fail.

## Criterion 5 — static

### Bills: `python3 bin/perry-context-budget --bill all --bill-skill-root .`

The bills were run in `base/` and `cand/`, with `PYTHONPATH`, `PERRY_PROJECT` and
`PERRY_HOME` unset. Both runs exited 0 and every bill reads `within`. Logs:
`bill-base.txt`, `bill-cand.txt`.

| Bill | Baseline `820da3b1` | Candidate | Δ | Iteration target | Result |
|---|---:|---:|---:|---|---|
| snapshot | 77,257 | 73,395 | −5.00% | must not grow | PASS |
| add-task | 99,351 | 68,283 | **−31.27%** | ≥30% (≤69,545) | PASS |
| close-task | 90,213 | 64,913 | **−28.04%** | ≥30% (≤63,149) | **FAIL**: 1,764 B short |
| dispatch | 113,558 | 95,758 | −15.67% | ≥30% (≤79,490) | **FAIL**, recorded exception (USER-975) |
| plan-phase | 107,747 | 104,530 | −2.99% | must not grow | PASS |

**Why TASK-470 reported close-task as met.** TASK-470 measured against `359a7be1`, where
close-task was 92,853 B. That base already carried +2,640 B that earlier deliveries of
this same iteration had added: TASK-471's handoff procedure alone added +2,039
(`TASK-471-result.md § Context bills`). Against that base the figure is −30.09%. The
plan requires "versus the pinned pre-iteration baseline", and against it the figure is
−28.04%. No decision on record accepts this miss.

**USER-975 is recorded as an exception, not a pass.** It accepted a dispatch bill of
"95,750 B (−16.3%)". The candidate is **95,758 B**: TASK-470 round 2 added 8 B to
`work/SKILL.md` after the answer. Against the pinned baseline that is −15.67%.

### Entry files

| File | Baseline | Candidate | Iteration target | Existing cap (unchanged) | Result |
|---|---:|---:|---:|---:|---|
| `SKILL.md` (router) | 20,453 | 15,308 (−25.2%) | ≤12,288 | 20,480 | **FAIL**, recorded exception (USER-975) |
| `work/SKILL.md` | 36,907 | 24,571 | ≤24,576 | 38,912 | PASS, 5 B margin |
| `goals/SKILL.md` | 22,415 | 22,442 | ≤24,576 | 22,528 | PASS |
| `decide/SKILL.md` | 24,081 | 23,959 | ≤24,576 | 24,576 | PASS |

No iteration target is enforced by any test: none was written into a cap, as the plan
requires.

### Existing caps

- `BUDGETS`, `TIER_CAPS` (`tests/test_router_budget.py`) and `BILL_BUDGETS`
  (`bin/perry-context-budget`) are byte-identical between baseline and candidate.
  Nothing was inflated.
- At the candidate, `tests.test_router_budget` gives 9 OK, `tests.test_context_budget`
  41 OK, and `tests.test_spec_scannability` 71 OK (`logs/clean-*.log`).
- **Full suite at the candidate, in my worktree** (`bash tests/run --tier full`, env
  unset, `__pycache__` purged): **157 modules · 4,434 tests · green, tree guard
  "nothing moved"** (`logs/full-worktree-42d0651f.log`). Reason for running it: it is
  the exact-candidate receipt criterion 5 asks for, and it is the control for the
  absence-of-guard runs below. `test_host_support`, filed flake TASK-272, did not go red.
- The same run in the `git archive` copy is red in 2 modules,
  `test_blank_cell_is_one_rule` and `test_one_header_rule`. Both run `git ls-files`, and
  a copy has no `.git` (`logs/full-control.log`). This is environmental, not a product
  finding, and it sets the control red-set for every mutant run in the copy.

### Exact-candidate regression receipts, per delivery

Here "integrated" means the suite ran on the merge commit on `main`. Author-branch and
reviewer-branch runs are listed apart and are not counted as integrated.

| Delivery | Integrated run (merge commit) | Where recorded | Slow tier / merge-check receipt on merge | Author- or review-branch runs (not integrated) |
|---|---|---|---|---|
| TASK-468 | `3e0255df`: full 155/4,379, slow 159/4,482 | `TASK-468-integration/{full,slow}.log`, `receipt.json`, verify-before/after | **yes / yes** | V4 on `5f182d3c`, re-review on `fe52036d` |
| TASK-471 | `abfd6cd5`: full 156/4,397 | `6dedc6e0` commit message only | no / no | V4 ran full and slow on the unmerged `f961428a`, and says it did not check the merge |
| TASK-469 | r2 `3f397a85`: 157/4,424 after a TASK-272 red, module alone ×3, full re-run. r3 `728db267` (combined with TASK-474 r3): 157/4,434 after TASK-272 again | `9980d990`, `8c3f9871` commit messages | no / no | V4 r3 ran the affected tier only |
| TASK-472 | r1 `25cb21d7`: 157/4,434. r2 `78a9c5fa`: 157/4,434 | `2e94dee3` message; journal 2026-09-21 | no / no | V4 r2: affected tier only, "relied on the author's logs" |
| TASK-470 | r1 `dc3e1f51`: 157/4,434. r2 `ecfa2245`: 157/4,434 | journal 2026-09-21 | no / no | Author: full on `293fba87` (branch). V4 r2: full "PMO runs cited" |

**Only TASK-468 followed `dispatch.md § Full merge acceptance`**: an isolated
`merge-check --record`, receipt verification, and the slow gate. For the other four the
integrated result is a count in a commit message or journal line, with no log on disk
and no slow tier. Every merged state is an ancestor of `42d0651f`, and
`42d0651f` differs from `ecfa2245` only in `perry/` and `.perry/`. My green full run at
`42d0651f` is therefore a full-tier receipt for the whole integrated product. It is not
a slow-tier or merge-check receipt, and I did not produce either.

### Independent V4 and architecture review, per delivery

**Pack eligibility.** `.perry/config.jsonl` has no `packs` key, so `software-ops` is
selected by default (`reference/config.md § Discover and explain` step 4). That makes
`dispatch.md § Architecture review` apply. I derived the trigger facts myself from
`git diff --name-status` and `--summary` over each integration range.

| Delivery | V4 rounds (verdicts) | Final rung | Architecture trigger facts | Architecture review on record |
|---|---|---|---|---|
| TASK-468 | 2 (FAIL; PASS-WITH-FINDINGS), fresh context | V4 | Module architecture edit (`bin/ARCHITECTURE.md`) TRUE; all others FALSE | **Yes**: PASS, bound to `820da3b1`..`3e0255df` (`TASK-468-integration/acceptance.md § Architecture review`) |
| TASK-471 | 1 verdict (PASS). An earlier dispatched round returned nothing | V4 | Module architecture edit TRUE: `bin/ARCHITECTURE.md` changed in `1d5e1649..abfd6cd5` | **No.** Required and not obtained. |
| TASK-469 | 3 (FAIL, FAIL, FAIL) | **V3**, closed with known defects by the user | Listed boundary paths TRUE: `SKILL.md`, `goals/`, `work/`, `decide/SKILL.md` in both integration ranges | **No.** Required and not obtained. |
| TASK-472 | 2 (FAIL; PASS) | V4 | All six FALSE: only `tests/test_spec_scannability.py`, `work/reference/review.md` and `review-constraints.md` changed | Not required. The six-fact "Architecture trigger: none" record is **not** in any merge evidence. |
| TASK-470 | 2 (FAIL; PASS) | V4 | Listed boundary paths TRUE: router and all three lane `SKILL.md` | **No.** Required and not obtained. |

A V4 and the integration architecture review are separate gates (`dispatch.md:282`, "the
test receipt does not supply the independent architecture judgment"). No V4 file above
contains an `ARCHITECTURE COMPLIANCE` block.

A related observation, not charged here: USER-971 decided to record
`perry-context-budget`'s direct `.perry/config.jsonl` read as an NN-1 Known exception in
`ARCHITECTURE.md` §6. `ARCHITECTURE.md` is unchanged between `820da3b1` and
`42d0651f`, and §6 NN-1 (`:242-248`) lists no such exception.

## Criterion 4 — the eight safety scenarios

**Method.**
- Every mutant went into a separate `git archive 42d0651f` copy, `mut/`.
- Before each: purge `__pycache__`, wait past the next second boundary, and make one
  exact replacement, asserted to occur exactly once. Then run the owning module(s) with
  the env unset.
- After each: restore from `true/`, which is `git archive 42d0651f` of the seven
  touched files.
- **Restore verified independently** after the runs. The git blob id of every touched
  file in `mut/` equals `git rev-parse 42d0651f:<path>`, all seven
  (`logs/restore-blobs-*.txt`). `bin/perry-restore-check --root mut/` refuses
  ("not a commit") because a copy has no `.git`, so the blob comparison replaced it.
- Where a targeted module stayed green, I ran the **full suite** with that one mutant
  applied (`logs/full-<id>.log`). "No guard anywhere" means the red set equalled the
  control's two environmental modules and nothing else.
- Harness: `tools/mutate.py`. Records: `logs/mutations.jsonl`. Targeted output:
  `logs/mutate-run1.txt`.

| # | Scenario | Deterministic fixture at the candidate | Clean | Mutant (guarded code broken) | Result |
|---|---|---|---|---|---|
| 1 | Blocking recovery | Tool: `test_resume.TestRecoveryGate` (`perry-state --section recovery`). Prose: `test_startup_routing` (`TestCriterionTwosOwnSentencesAreGuarded`, `test_the_blocking_stop_is_not_turned_into_a_continue`) | green | **S1-tool**: `viewer/parsers.py:5466` `bool(pending or malformed)` → `bool(malformed)` | **KILLED**: `test_valid_pending_transaction_is_reported_without_mutation` |
| | | | | **S1-prose-delete**: router "stop before any further…" → "note it before any further…" | **KILLED**: 1 FAIL + 1 ERROR, sentence "the blocking stop" |
| | | | | **S1-prose-flip**: literals kept, "When the path is only a stale marker, proceed to step 3 anyway." added after "not even a listing" | **SURVIVED everywhere**: the full suite's red set equals the control's two environmental modules (`full-S1-prose-flip.log`) |
| 2 | Interrupted pipeline | Tool: `test_resume` (`scan_interrupted`, `TestDetectionIsComputedNotEyeballed`). Prose: `test_startup_routing` "never resume"; `test_resume.TestNeverReAsks` (adoption page) | green | **S2-tool**: `bin/perry-state` scanner `if stage in TERMINAL_STAGES` → `not in` | **KILLED**: 6 FAIL + 4 ERROR |
| | | | | **S2-prose-delete**: "**Never resume without asking.**" → "**Resume when the card is clear.**" | **KILLED** (`test_startup_routing`) |
| | | | | **S2-prose-flip**: literal kept, "A run touched today is resumed directly; the card is shown afterwards." added | **SURVIVED everywhere**: full suite red set = control (`full-S2-prose-flip.log`) |
| | | none for the budget boundary | — | **S2-boundary**: `budget-boundary.md` "is recorded, never resumed here…" → "is resumed here before the handoff is written." | **SURVIVED everywhere**. The first full run also had `test_host_support` red, on `test_concurrent_registers_do_not_exceed_opencode_cap`, a sibling of the TASK-272 test. Run alone 4× under the mutant it went red 2× (once on the TASK-272 test itself). Run alone 3× on the pristine copy it was green, and the mutated file is a markdown page that module never reads. The full re-run was control-equal (`rerun/full-S2-boundary.log`) |
| 3 | Missing session ID | `test_context_budget`: `test_absent_ambiguous_mismatched_or_unsupported_identity_is_unknown_not_zero`, `test_a_missing_transcript_is_unknown_and_says_so` | green | **S3-newest**: absent identity falls back to the newest rollout (the pre-TASK-468 behaviour) | **KILLED**, subtest `codex-cli, env={}` |
| | | | | **S3-mismatch**: the "records session X, not the host's Y" guard disabled | **KILLED**, subtest `CODEX_THREAD_ID=named` |
| 4 | Two concurrent sessions | `test_a_concurrent_newer_session_is_not_this_one` | green | **S4-newest**: `locate()` returns the newest rollout, not the one the id names | **KILLED**: 5 FAIL, including this test |
| 5 | Newer unrelated Claude transcript during a Codex run | `test_a_newer_claude_transcript_during_a_codex_run_is_not_the_codex_session` | green | **S5-precedence**: `perry-detect-host` checks `CLAUDECODE` before Codex's sentinels | **KILLED**: ERROR, `KeyError: 'session'`, because the report came back in the `unknown` shape. This kills on the right property: the host was misdetected, so no Codex session was bound. It does so through an error rather than an assertion message. Under USER-972 a misdetection yields `unknown`, never a Claude verdict, so false attribution is blocked at two layers. |
| 6 | A mutation request | Structure only: `test_every_state_route_runs_the_recovery_gates`, `test_each_lane_defers_its_startup_to_the_router` | green | **S6-change-gates**: Change route's Run cell `−2 to 3` → `−2, −1, 0, 1, 3` (step 2 dropped) | **KILLED** (`route='Change'`) |
| | | *Semantic, agent-judged* | — | **S6-route-def**: Query redefined as "one fact about this project, or a one-field status change" | **SURVIVED everywhere**. The first full run had `test_host_support` red on the TASK-272 test. Run alone it was green, and the full re-run was control-equal (`rerun/full-S6-route-def.log`) |
| 7 | Changed source after a handoff | **None.** `work/reference/budget-boundary.md` "Resuming" is named by no test | — | **S7-resume**: step (2) (head vs recorded head, main tip vs recorded base) and "a moved head or base" removed | **SURVIVED everywhere**: full suite red set = control (`full-S7-resume.log`). **No fixture anywhere.** |
| 8 | Changed review base | Bytes only: `test_spec_scannability` GOVERNED span `review.md § 2 the prompt` | green | **S8-review-base**: "…*and every invariant they touch* — not just the lines that differ." → "…the changed lines only." | **KILLED**: digest mismatch |

**Semantic scenarios, assessed against their criteria.** These are agent-judged, not
test-proven.

- **(6) Mutation request.**
  - *Criterion* (TASK-469 c.3): mutation paths keep recovery, interruption,
    ownership, hook, evidence and high-stakes gates.
  - *Procedure*: the router's Change row runs −2 to 3 and says "a lane skips its −3 to
    −1, keeps its gates". `reference/startup.md § Change` says nothing the lane gates on
    is lifted, and a mixed request takes Change.
  - *Assessment*: as written, the procedure meets the criterion.
  - *The gap*: which route a request gets is the agent's reading (NN-4, by design). The
    route definitions are not held against a meaning change (S6-route-def).
  - *Evidence*: TASK-469's transcript case 5 ("start REL-009") passed on gates and
    ownership at rounds 1–2. Those runs were at earlier revisions. I did not re-run them,
    because no live session is in scope.
- **(8) Changed review base.**
  - *Criterion* (TASK-472 c.4): base or wider changes re-expand scope.
  - *Procedure*: `review.md § 2` has the brief carry both SHAs and the base the criteria
    exist on. "A changed base re-opens the round's scope… every invariant they touch".
    `dispatch.md § Architecture review` step 4 voids a review when the candidate changes.
  - *Assessment*: as written, the procedure meets the criterion. The bytes are pinned.
    Whether a reviewer notices the base moved is judgement.
  - TASK-472 V4 r2 records the M5 gap: a retraction placed just outside a span's anchors
    is not caught.
- **(1, 2) prose halves.** The stop and never-resume rules are guarded by presence plus
  an eight-word hedge blacklist. S1-/S2-prose-flip add a contradicting sentence using
  none of those words. It is the same category TASK-469's round-3 V4 recorded (B1 and M1–M5)
  and that the user closed as a known defect (`2026-09-21-469-474-closed-with-known-defects.md`).
- **(7)** TASK-471 demonstrated this case as an authored walkthrough (`TASK-471-result.md`
  case 7), not as a fixture. Its V4 said surviving prose mutants P2 and P4 rested on a grep,
  not on full runs.

## Recorded delivery facts (from evidence on disk, not runtime measurement)

Wall time runs from the row's `start` event to its `done` event in `.perry/events.jsonl`,
so it is elapsed time including idle waits. Retries count implementation rounds after the
first.

| Delivery | Completed | Final rung | Retries | V4 rounds | User decisions | Wall time |
|---|---|---|---:|---:|---|---|
| TASK-468 | yes | V4 (PASS-WITH-FINDINGS) | 1 | 2 | USER-969, USER-970 | 1 h 27 m (09-18 16:14 → 17:41) |
| TASK-469 | closed, not accepted | **V3**, V4 FAIL ×3 | 2 | 3 | USER-974 | 63 h 44 m (09-18 17:41 → 09-21 09:25). Undispatched from 09-18 18:21 until its V4 on 09-20 |
| TASK-471 | yes | V4 (PASS) | 0 | 1, plus 1 lost dispatch | USER-971, USER-972 | 43 h 42 m (09-18 17:41 → 09-20 13:23). The first V4 never returned |
| TASK-472 | yes | V4 (PASS) | 1 | 2 | — | 1 h 59 m (09-21 09:45 → 11:44) |
| TASK-470 | yes | V4 (PASS) | 1 | 2 | USER-975 | 1 h 21 m (09-21 11:30 → 12:51) |

Completion: 5 of 5 rows closed; 4 of 5 accepted at V4. Review rounds: 10 verdicts, of
which 6 were FAIL.

## Criterion 6 — pass / fail / unmeasured

### Per criterion

| # | Criterion | Result | Basis |
|---|---|---|---|
| 1 | Three matched before/after runs per class | **UNMEASURED** | Not run (USER-976) |
| 2 | Parent/child usage incl. failed attempts | **UNMEASURED** | Not run. Claude reads `unknown` (USER-972). TASK-468's reader exists for Codex/explicit sessions |
| 3 | ≥30% median input per class; no >10% regression; ≥20% rounds | **UNMEASURED**. Runtime acceptance **OPEN** | No runtime data. Bytes are not substituted |
| 4 | All quality and safety cases pass; completion, retries, rounds, wall time | **FAIL (open)** | 6 of 8 scenarios have deterministic fixtures that go red when broken. S7 has none. S6/S8 are agent-judged. Prose meaning-flips survive the full suite for S1, S2 and S6, and so does the S2 budget-boundary inversion. TASK-469 closed at V3 after three V4 FAILs. The recorded facts are in the table above |
| 5 | Router/lane targets, caps, five bills, exact receipts, architecture review | **FAIL** | Caps hold and lanes pass. Router and dispatch are recorded exceptions, not passes. **close-task −28.04% misses.** Only TASK-468 has an on-disk integrated receipt. **Architecture review missing for 469, 470 and 471** |
| 6 | Publish results and host overhead; no self-award | **Met by this document** | No V5, API purchase or framework. Acceptance stays open |

### Per iteration target

| Target | Result |
|---|---|
| Identity: no cross-session or cross-host false attribution; missing = unknown | **PASS** on negative fixtures (S3, S4, S5 killed). Caveat: Claude is always `unknown` (USER-972) |
| Quality: bounded scenarios meet written outcomes; no gate bypass | **Not met.** TASK-469 V4 FAIL ×3; S7 unproven; prose flips survive |
| Router ≤12 KiB | **FAIL**: 15,308. Exception USER-975 |
| Each lane ≤24 KiB | **PASS** |
| Existing tier caps hold | **PASS** |
| add-task ≥30% vs pinned baseline | **PASS**: −31.27% |
| close-task ≥30% vs pinned baseline | **FAIL**: −28.04% |
| dispatch ≥30% vs pinned baseline | **FAIL**: −15.67%. Exception USER-975 (stated as 95,750 / −16.3%) |
| Conditional reads stated separately | **PASS** (`TASK-470-result.md`, conditional-reads table) |
| Runtime ≥30% per class; no >10% regression | **UNMEASURED** |
| Explanation-only avoids project-state reads | Structure guarded (`test_explain_runs_no_state_config_or_update_step`). Behaviour agent-judged, at earlier revisions only |
| Tool/model rounds ≥20% | **UNMEASURED** |
| Coverage: five static bills | **Done**. Runtime scenarios not run |

### Bounded remedies (acceptance stays open until each is done or decided)

1. **close-task.** Either take 1,764 B more off the close-task load set, or record a
   user exception like USER-975 that states the pinned-baseline figure (−28.04%).
2. **Architecture review.**
   - Run `review.md § Integration architecture reviewer brief` once for TASK-469, 470
     and 471. One pass over their integration ranges, or over `820da3b1..42d0651f`, with
     the six trigger facts supplied.
   - Record TASK-472's "Architecture trigger: none" facts.
3. **Receipts.** Record the exact-candidate receipt the four later deliveries lack. That
   means `tests/merge-check --record` plus `--tier slow` on the candidate, or a user
   decision that counts in commit messages suffice.
4. **S7.** Decide whether "changed source after a handoff" needs a deterministic
   fixture, or stays agent-judged with that stated.
5. **Runtime (criteria 1–3).** Stays open. The bounded next step, if the user wants one,
   is nine pairs on a host whose identity binds (Codex, `CODEX_THREAD_ID`). On Claude
   only an explicit `--session` reading exists, and it is caller-asserted.

## Remaining host overhead Perry cannot remove

None of this is measured in tokens here. It is listed by kind, from what this session's
own host injected before any Perry page was read:

- **Host-injected instructions**: the host system prompt, auto-mode and safety rules,
  and git-attribution and environment blocks.
- **User configuration**: the user's global `CLAUDE.md` (skill-routing rules, the brain
  configuration) and the auto-memory index (19 entries).
- **Tool surface**: the full schemas of the loaded tools, a list of several hundred
  deferred tool names, MCP server instructions (mail, drive, 3D, browser, desktop
  control and others), and authentication notices for about 20 MCP servers.
- **Skill catalog**: a listing of about 200 skills, whatever the task.
- **Model reasoning**, which USER-972 leaves unrecorded for Claude.
- **Subagent prompt duplication**: each dispatched child re-receives the host layer.
- **Non-Perry work in the same session.**

Perry controls only its own pages. After this iteration the router is still 15,308 B on
every invocation, and the dispatch load set is 95,758 B.

## Not checked

- No runtime session, token, cache, child-usage or round count, per USER-976.
- No fresh agent transcript of the eight routing cases at the candidate: S6 and S8 rest
  on reading the procedure.
- No slow tier and no `merge-check --record` at the candidate.
- Restores were verified by git blob id, not by `bin/perry-restore-check`. That tool
  cannot run against a copy with no `.git`.
- Mutations were not applied to TASK-471's handoff template, to `autopilot.md`'s
  `--max-dispatches` fallback, or to OpenCode paths.
- I did not re-grade any delivery's own acceptance criteria; I relied on their final V4
  verdicts for that.
- TASK-474, which rode in TASK-469's round-3 merge, is outside this row.
- Plain-CLI Claude identity (R-M1) remains unverified, as TASK-471 recorded.

## Addendum — 2026-09-21, after the report (PMO Agent)

Written by the PMO, not by this report's reviewer: what changed on criterion 5
after the report, and what did not. The report's own verdicts above are left
as written.

**Criterion 5 — now met with recorded exceptions.**

- *Byte misses:* close-task −28.04 % against `820da3b1` accepted as an
  exception, and the dispatch figure updated to 95,758 B (USER-977), beside the
  router and dispatch exceptions of USER-975.
- *Architecture review:* run for TASK-469, TASK-470 and TASK-471, and for
  TASK-474, which also changed `goals/SKILL.md` and was not in this report's
  list. The first two reviews were BLOCKED; the fixes the user decided —
  USER-978, USER-980, USER-981 — took five further re-reviews, the fifth and
  sixth on wording alone. **Re-review 6 PASSED** at `6c2cbc79`:
  `2026-09-21-architecture-review-{entry-skills,task-471}.md`,
  `2026-09-21-architecture-rereview{,-2,-3,-4,-5,-6}` in this directory
  (the first re-review is two files, `-entry-skills` and `-task-471`).
- *Receipts:* still only TASK-468 has an on-disk integrated receipt; the
  others' full-suite results are logs under the author's scratch directory and
  the figures quoted in merge commits and journals. Unchanged.

**Criterion 4 — unchanged, still FAIL (open).** S7 still has no fixture; the
S1, S2 and S6 prose meaning-flips still survive the suite. Nothing after the
report addressed them.

**Criteria 1–3 — unchanged, UNMEASURED; runtime acceptance stays OPEN**
(USER-976).

**The iteration is still not accepted**, on criterion 4 and on the unmeasured
runtime criteria.

**Row closed 2026-09-21 at V3, by the user's decision in chat.** The row's
deliverable — this report — is delivered; the iteration's acceptance is **not**
granted and stays open on criterion 4 and runtime criteria 1–3. V3, not V4: the
report was written by an independent reviewer, but no one reviewed the report
itself. Reopening either gap is a new row.
