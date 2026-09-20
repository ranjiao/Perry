# TASK-469 — V4 review (round 2)

Date: 2026-09-20. Reviewer: fresh-context review agent (Claude Opus 5), not the
implementer of either round. Criteria: `perry/evidence/2026-09/TASK-469-spec.md`
— the only authority for PASS/FAIL.

## Identity of what was reviewed

- **Range:** `ed5d9894..9cec11a8`, branch `coding/task-469-round2`, merged to
  `main` at `3f397a85`. The branch opens with the merge `87792e63`, which brings
  `main` into round 1's delivery (pinned 21 commits back at `be5b83cf`), so the
  round-2 work proper is `c44d5a64` (fixes + guards) and `9cec11a8` (result
  evidence). Round 2's own diff is `87792e63..c44d5a64`: `SKILL.md`,
  `work/SKILL.md`, `reference/startup.md`, `reference/hand-off-contract.md`,
  `tests/test_startup_routing.py` — five files, nothing else.
- **The merge preserved the reviewed bytes.** `bin/perry-restore-check 9cec11a8`
  reports `SKILL.md`, `{goals,work,decide}/SKILL.md`, `reference/startup.md` and
  `tests/test_startup_routing.py` byte-identical to `main` at `9980d990`.
- **Where I worked:** my own worktree
  `/Users/bytedance/proj/Perry/.claude/worktrees/agent-a2d2c8a5adb6f9a51`, on a
  branch `review/task-469-round2-v4` cut from `main` at `9980d990`. Nothing was
  written to `/Users/bytedance/proj/Perry/perry` and no Perry write tool was run.
  This file and its commits are the round's only output.

## 1. Suite

`bash tests/run --tier affected --base ed5d9894`, with `PERRY_PROJECT` and
`PERRY_HOME` unset:

| Run | Result |
|---|---|
| `--tier affected --base ed5d9894` | green — 61 modules · 1889 tests · 72.3s. Selection: 64 of 161 modules, 3 held back to the slow tier. Tree guard clean. **This is not a green suite and I do not report it as one.** |

`test_host_support.TestOpenCodeDispatchLimit` did not fire. I did not run the
`full` or `slow` tiers; see `not-checked:`.

## 2. Mutations — the second kind, re-aimed

The author's claim under test is that four mutations "keep every guarded literal
while flipping the meaning" were **green before this round** and are killed now.
I did not re-run the author's four. I invented six of the same shape, aimed at
the guards the author added, plus three controls that must die.

Method: one line replaced by 1-based line number (never `str.replace` over a
whole file — the transform is applied to that single line's text only);
`__pycache__` purged and 1.3 s slept past the whole-second mtime boundary on
both sides; the full `--tier affected --base ed5d9894` run each time; restore by
writing the bytes of `git show 9cec11a8:<path>` — fetched independently of
anything my harness snapshotted — then verified with `bin/perry-restore-check
9cec11a8 <path>`. **All restores passed and the tree guard reported "nothing
moved" on every run.** Harness: scratchpad `mutate.py`, `gen.py`,
`mutation-results.json`. Every edit was kept under the router's remaining 86
bytes of headroom against `test_next_section.ROUTER_BYTES_AT_BASE = 20457`, so
no result below is a byte-budget red in disguise.

### The six of the second kind — all six survive

| # | File:line | The edit (every guarded literal kept) | Affected tier |
|---|---|---|---|
| A1 | `SKILL.md:85` | Explain's `Then` cell gains a trailing qualifier: "No update check, config, state, modes, dashboard or write **unless the answer needs one**" | **GREEN** |
| A2 | `SKILL.md:89` | the step-1 qualifier is widened: "but step 1's config read**, and any projection the answer needs**" | **GREEN** |
| A3 | `SKILL.md:108` | the D3 clause is contradicted by the next sentence: "…not even a listing**. Reading the state root to confirm is expected.**" | **GREEN** ×3 |
| A4 | `SKILL.md:129` | "**Never resume without asking.** **A stale run is the exception; resume it.**" | **GREEN** |
| A5 | `work/SKILL.md:24` | D1's defect reworded in beside the fix: "before loading software-ops references, **printing the help index**, or running an optional pack's route" | **GREEN** |
| A6 | `work/SKILL.md:137` | lane ordering inverted with `before` still immediately after the gates: "interrupted-run gates before **the next operation, not before** this lane reads state" | **GREEN** ×3 |

### The three controls — all three die, on the right assertions

| # | The edit | Killed by |
|---|---|---|
| C1 | delete ", not even a listing" outright | `test_each_sentence_is_present_and_not_inverted`, `test_no_rule_is_softened_by_what_follows_it` |
| C2 | round 1's P3 re-run — Explain's `Then` cell → "plus `perry-task list --json` and the dashboard" | `test_nothing_is_added_after_the_negation`, `test_the_cell_carries_a_negation_and_it_names_every_exclusion` |
| C3 | round 1's P6 re-run — the lanes' `before` → `after` | `test_each_lane_runs_the_gates_before_it_reads_state` |

So the new guards do kill what they were aimed at. The controls are the evidence
that the six greens are real greens and not a harness that never ran the module
— `test_startup_routing.py` appears in the selection of every run ("changed:
tests/test_startup_routing.py", 64 of 161 modules selected, 61 run).

**On A3 and A6, and a red I could not reproduce.** Both came back RED on their
first pass and GREEN on three subsequent isolated re-runs each. I did not
attribute the first red; I re-ran it, which is what `test_host_support.py` —
selected on every one of these runs, and carrying the filed TASK-272
parallel-runner flake — exists to make you do. Four data points each
(RED, GREEN, GREEN, GREEN) put both in the GREEN column, and **I record that my
first-pass harness discarded the failing output, which is why the re-runs were
needed at all.** That is a defect in my harness, not in the branch.

### What the greens mean

The author's sharpening is real but it is **enumerative**: `WEASEL` is a list of
eight strings, checked in the 140 characters after five named sentences. A
rewording outside that list, or a softening of a sentence outside those five,
is invisible. Every one of my six greens is the author's own failure mode one
step out:

- **A1 walks around the list from outside it.** `WEASEL[0]` is `"unless"`. The
  `Then` cell — where criterion 1 actually lives — is not one of the five
  `sentences()`, so `"… dashboard or write **unless the answer needs one**"`
  passes every assertion in `TestTheThenCellCarriesCriterionOne`: the negation
  is present, every excluded token is inside it, nothing forbidden was added,
  and "pages that answer" survives.
- **A2 widens the qualifier the new test pins.**
  `test_the_step_one_qualifier_names_step_one_and_the_config_read` requires
  `"step 1"` and `"config read"` in the 160 characters after the absolute and
  rejects `"step 3"`, `"step 0"` and `"dashboard"`. It does not bound what
  *else* the qualifier may name, so "but step 1's config read, **and any
  projection the answer needs**" — the exact thing criterion 2 forbids — is
  green.
- **A4 is S4 with a synonym.** The author's S4 was
  `"Never resume without asking." **Unless it is stale, in which case resume.**`
  and `WEASEL` now carries both `"unless"` and `"in which case"`. `"A stale run
  is the exception; resume it."` says the same thing with neither.
- **A3 takes back the D3 fix with the sentence after it.**
  `test_the_blocking_stop_is_not_turned_into_a_continue` forbids three exact
  strings in the 600 characters after `` `blocking: true` ``: `"continue to the
  state read"`, `"listing the state root"` and `"Resume the run"`. "**Reading**
  the state root to confirm is expected" is none of them, and carries no
  `WEASEL` word either. The clause that was the entire content of the D3 repair
  can be contradicted by the sentence immediately following it.
- **A4 is the author's own S4 with a synonym.** S4 was
  `"Never resume without asking." **Unless it is stale, in which case resume.**`
  and `WEASEL` now carries both `"unless"` and `"in which case"`. `"A stale run
  is the exception; resume it."` says the same thing with neither.
- **A5 is D1 reworded.** `test_no_lane_sends_help_row_rendering_through_the_pack_procedure`
  asserts the absence of one literal, `"rendering its help rows"`. Putting
  `"printing the help index"` into the same sentence restores the defect the
  whole round is about, with both of the round's D1 guards green.
- **A6 is the author's own S3 with a different filler.** The guard now anchors
  `before` to the position immediately after `interrupted-run gates` and
  forbids `" after"` in the next 120 characters. "gates before **the next
  operation, not before** this lane reads state" satisfies both and reverses
  the rule.

This is the finding round 1 recorded as D5, moved one level up rather than
closed. It is not that the new guards are useless — C1, C2 and C3 show they
kill what they were aimed at — it is that the claim under test ("all four of
the second kind were green before; they are killed now") does not generalise to
the class, and the result presents it as if it does: "The guards were presence
assertions, so they could see a deletion and not a substitution" describes the
old guards, and the new ones are substitution assertions over a closed list,
which is the same shape one rung up.

## 3. The byte budget

| Claim | Check | Verdict |
|---|---|---|
| No cap or budget was raised | `git diff --stat ed5d9894 9cec11a8` touches no file under `bin/`, and neither `tests/test_router_budget.py` nor `tests/test_next_section.py`. `BUDGETS` is byte-identical to `be5b83cf`; `ROUTER_BYTES_AT_BASE` is `20457` at `ed5d9894` and at the head | **True** |
| `SKILL.md` is within its cap | 20,371 bytes against the 20,480 cap | **True** |
| 129 bytes freed by moving a paragraph to `reference/hand-off-contract.md` | The paragraph trim is **238** bytes, not 129; 129 is the *shortfall* it covered (20,426 + 183 = 20,609; 20,609 − 238 = 20,371). The wording is loose but the arithmetic behind it is right | True in substance |
| Nothing load-bearing left the router | The removed paragraph's three claims — `decisions/` moving `work`→`decide`, `OKR.md § Commitments` becoming `goals`, and the byte-identical-ownership-set reason no second signature was needed — are all in `reference/hand-off-contract.md:13-40`, which pre-dates this change and is still cited from `SKILL.md:75`. The ownership **table** itself, which carries the facts, is untouched | **True** |

One correction the author should carry: the binding constraint is not the
20,480 cap but `tests/test_next_section.py:72`'s growth guard at **20,457**, so
the real headroom is 86 bytes, not the 109 the result claims. Round 1's review
named that guard; round 2's result does not.

## 4. D1's category — every path by which Explain/help still reaches a state read

Enumerated, not spotted. The help route's reachable set is defined by
`reference/startup.md:31-32` — "load that lane's `SKILL.md` for its index and
**the one reference its row names**" — plus `reference/router-subcommands.md`
for bare `/perry help`. I grepped every file in that set for `perry-config
show`, `perry-state --`, `perry-lint --root` and `Pack capabilities and
controls`, and separately grepped all shipped `.md` for `Pack capabilities`.

| # | Path | Reaches | Round 2 | Verdict |
|---|---|---|---|---|
| 1 | `work/SKILL.md:23-25` "apply … `§ Pack capabilities and controls` **before loading software-ops references**" + `work/SKILL.md:294` "with arg … **read the matching reference file**" + the five index rows at `:275-279` whose reference file is `packs/software-ops/*.md` | `perry-config show --json` and `perry-state --section project` | **not fixed** — the carve-out added at `:30-37` covers *rendering help rows* only, and says so: "the one thing that procedure is NOT applied to" | **defect, F1** |
| 2 | `work/SKILL.md:23-25` → rendering the help index | same | **fixed** — print marked, do not filter | correct |
| 3 | `goals/SKILL.md:21-23` "For optional capabilities and their controls, read …" | same | left, deliberately | acceptable — the trigger named is the *discovery* operation ("optional capabilities and their controls"), which is a Query and legitimately reads. It does not name help or rendering |
| 4 | `decide/SKILL.md` | — | n/a | no pack pointer exists; `:20` already exempts `help` from the snapshot |
| 5 | `reference/router-subcommands.md:93-96` — `/perry help` offers "Optional capabilities" | same | left | acceptable — "**On that request** show …; ordinary help needs no setup question". The follow-up is its own route |
| 6 | `work/reference/{subcommands,add-task,planning,bootstrap,health-check}.md` — each names the pack procedure inside a subcommand's body; each is loaded by `help <that subcommand>` | same | left | acceptable — `work/SKILL.md:294` says the file is read "so the procedure is in context" and "`help` is navigation, not action". Reading a procedure is not running it |
| 7 | `packs/software-ops/pack.md:57` | same | left | acceptable — read only when the pack is loaded, which help does not do on its own |
| 8 | `goals/reference/phases.md:177` | same | left | acceptable — `plan-phase`, a Change |

Row 1 is the finding. Rows 6 and 7 are the same *words* in files where
`work/SKILL.md:294`'s "navigation, not action" disposes of them; row 1 is not,
because the precondition there is on **loading** the page, which is exactly what
the help route is instructed to do.

**On the author's deliberate non-fix.** The author names
`reference/config.md § Pack capabilities and controls` step 1 as the root cause
and declines to touch it because that file is not in the spec's `Files in
scope`. Judged against the written criteria: **that call is correct.** `Files in
scope` is a written constraint of the row, `reference/config.md` is not in it,
and the `Bound` section forbids widening. But the defence does not reach F1,
because F1 is in `work/SKILL.md` — a file that **is** in scope, in the very
sentence round 2 rewrote, and fixable by extending the carve-out it already
added by one clause.

## 5. Criterion 5 — judged on what exists

Criterion 5 asks for eight agent-reviewed cases recording expected reads, actual
reads and the decision, and forbids a Python keyword classifier.

- The matrix exists: `perry/evidence/2026-09/TASK-469-result.md:62-70`, eight
  rows, each with an expected route + reads column, an actual reads-and-commands
  column, a decision and an outcome. Cases 4, 6 and 7 carry both an R1 and an R2
  trace. Method, fixtures and raw-log locations are stated at `:60`.
- The negative holds: `git diff --stat ed5d9894 9cec11a8` touches no `bin/`
  file, so no classifier was added.
- **Neither round re-ran them and neither did I.** The author says so at
  `TASK-469-round2-result.md:114-117`. Round 1's reviewer says so too. So
  criterion 5 is met by an artefact that exists and is internally coherent, and
  by nothing stronger. I record it as met and as the weakest-evidenced criterion
  on the row.
- One thing the matrix itself shows, and which bears on F1: case 2
  (`/perry help work`) records the agent reading `reference/config.md § Pack
  capabilities` during help. It did not *run* the commands, which is why the row
  passes — but the read happened, on the route where round 1's D1 said it should
  not have been invited.

## 6. The other five criteria, re-derived

| AC | Finding |
|---|---|
| 1 | Three routes are defined (`SKILL.md:84-87`), and Explain's `Then` cell states the four exclusions the criterion names. **Not met** — F1 leaves an Explain request (`/pmo help runbook-check`, `incident`, `architecture`, `architecture-audit`, `health-check`) instructed to run `perry-config show --json` and `perry-state --section project` first. F3 shows the cell that carries this criterion can be taken back with one word and nothing goes red |
| 2 | The write half of round 1's D2 is genuinely fixed: `SKILL.md:97` now gates first-time setup to "**Change route only**, since it writes; Explain and Query report the gap and stop", and `test_first_time_setup_is_gated_where_step_one_prompts_for_it` pins it to step 1's own text. The ordering half is *disclosed* rather than removed — the Query route still reads `.perry/config.jsonl` before the recovery gate, and the router now says so. Given `reference/startup.md:19-21`'s standing rationale (the config store is not what the task command recovers, and the chat language must be known before the gate can report), and that the order pre-dates the row, I do not fail AC2 on it. I do record that the criterion's literal words are still not true of the config store under the implementation's own definition at `reference/startup.md:11-13` |
| 3 | Met. The Change row still routes bare `/perry` to steps 3b–6, so the explicit overview still produces the snapshot; no gate was removed from any lane in this round's diff (round 2 touched no lane but `work`, and only its preamble) |
| 4 | Met. All three lanes carry the same deferral sentence (`goals/SKILL.md:72`, `work/SKILL.md:137`, `decide/SKILL.md:42`) and `reference/startup.md § Once per operation, refreshed when invalidated` supplies the refresh rule. F5 shows the ordering word in that sentence is still walk-around-able |
| 5 | Met on what exists; see § 5 |
| 6 | The load sets are logged (`TASK-469-result.md:97-102`), but the conditional figure is now **stale**: it records `reference/startup.md` at 6,111 B, which was exact at `bb3d97d6` and is 7,392 B at the head — round 2 added 1,281 bytes to the one page the criterion asks to be logged and did not restate it. "Pointers and relevant guards remain valid": the affected tier is green, but see § 7 for a quotation in `reference/startup.md` that does not match the router it quotes |

## 7. Smaller things, recorded so the next round need not re-find them

- **`reference/startup.md:80` misquotes the router it explains.** The bullet is
  headed **"except step 1's `.perry/config.jsonl`"**; the router actually reads
  "Nothing reads state before step 2 **but step 1's config read**"
  (`SKILL.md:89`). The next bullet is headed **"on a Change route only"**; the
  router reads "**Change route only**" (`SKILL.md:97`). Both are presented as
  quotations of the route table and step 1. Nothing enforces the match, and the
  page's whole argument is that a correction must be findable where the
  behaviour is driven — a reader searching the router for either quoted string
  finds neither.
- **Step 1 now instructs a route that never reaches it.** `SKILL.md:97` ends
  "…**Change route only**, since it writes; Explain and Query report the gap and
  stop." Explain runs step −2 and nothing else (`SKILL.md:85`), so it never
  reaches step 1 to report anything. The sentence is harmless as belt-and-braces
  and is the same *shape* as the D2 defect it repairs — a tier-0 sentence that
  is not true of the procedure it sits in. Naming Query alone would be exact.
- **The result's 109 bytes of headroom is 86** against the binding growth guard.
  § 3 above.
- **"the remaining 129 bytes came from the … paragraph"** — the paragraph gave
  238; 129 was the shortfall. § 3 above.

## 8. Verdict reasoning

Round 2 does real work. D4 is closed by writing the missing runs down. D3 is
genuinely closed: the "not even a listing" clause is now in the router's own
step 2, where the blocking path reads it, and a guard refuses three named
inversions of it. D2's dangerous half — a Query able to start first-time
setup, a write, ahead of the recovery gate — is closed on the step that prompts
for it, with a guard anchored to that step's text rather than to the file. The
lane-ordering and `Then`-cell guards round 1 asked for exist. The byte
accounting is honest, no cap was raised, and nothing load-bearing left the
router.

It fails for two reasons, and they are the two the round was warned about.

**Rule 1.** D1's fix went to the instance that was named. `work/SKILL.md:23-25`
still says to apply the state-reading procedure "before loading software-ops
references", and `work/SKILL.md:294` says a `help <subcommand>` request loads
exactly that reference for five of the lane's subcommands. The new paragraph
does not merely fail to cover this — it affirms it, by calling help-row
rendering "**the one thing** that procedure is NOT applied to". The route with
no recovery gate is still told to run `perry-state --section project`.

**Rule 2.** The author's own headline claim is that four mutations which keep
every guarded literal and flip the meaning are now killed, and the result says
this is "the most likely place for this round to be wrong". It is. I did not
re-run the author's four; I aimed six of the same shape at the same guards, and
**all six are green**, while three controls aimed at the same guards all die on
the right assertions. Two of the six are the plainest possible inversions of
criteria 1 and 2 — a trailing "unless the answer needs one" on the `Then` cell,
and a widening of the step-1 qualifier to "and any projection the answer needs".
The first uses "unless", the first entry in the author's own new `WEASEL` list,
which is applied to five router sentences and not to the cell criterion 1 lives
in. Two more (A3, A6) are the author's own S2 and S3 with different filler
words, and one (A5) reopens D1 itself.

This does not mean the guards should enumerate more strings. Round 1's D5 and
this round's six greens together say the same thing the branch's own
`reference/startup.md` says about prose: a structural guard can pin a shape and
cannot read a meaning, and a criterion whose whole content is one English
sentence is not covered by asserting that sentence's characters are present and
eight particular other strings are not. What criterion 6 asks for — "relevant
guards remain valid" — is satisfied; what the result claims for them is not.

FAIL, on F1 primarily. F2 is why a third round should not simply lengthen
`WEASEL`.

=== VERDICT ===
task: TASK-469
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-469-spec.md
checked: Worked on branch review/task-469-round2-v4 cut from main at 9980d990 in my own worktree /Users/bytedance/proj/Perry/.claude/worktrees/agent-a2d2c8a5adb6f9a51; nothing written to /Users/bytedance/proj/Perry/perry and no Perry write tool run. Confirmed with bin/perry-restore-check 9cec11a8 that SKILL.md, the three lane SKILL.md files, reference/startup.md and tests/test_startup_routing.py are byte-identical on main to the branch tip, so the merge preserved the reviewed bytes. Ran `bash tests/run --tier affected --base ed5d9894` (green — 61 modules/1889 tests/72.3s, 64 of 161 modules selected, 3 held to slow, tree guard clean; NOT a green suite). Nine mutations, each replacing ONE line by 1-based line number with the transform applied to that line's text alone, __pycache__ purged and 1.3s slept past the whole-second boundary on both sides, the full affected tier run each time, restored by writing the bytes of `git show 9cec11a8:<path>` and verified with bin/perry-restore-check — all restores passed, tree guard "nothing moved" on every run. Six of my own of the author's "second kind" (keep every guarded literal, flip the meaning) ALL SURVIVED: A1 Then-cell + "unless the answer needs one"; A2 step-1 qualifier widened to "and any projection the answer needs"; A3 "not even a listing" contradicted by "Reading the state root to confirm is expected" (green on 3 isolated re-runs after one unreproducible first-pass red); A4 "Never resume without asking." + "A stale run is the exception; resume it."; A5 D1 reworded back in as "printing the help index"; A6 lane ordering to "before the next operation, not before this lane reads state" (green on 3 isolated re-runs after one unreproducible first-pass red). Three controls all died on the right assertions: C1 delete "not even a listing" -> test_each_sentence_is_present_and_not_inverted + test_no_rule_is_softened_by_what_follows_it; C2 P3 re-run -> test_nothing_is_added_after_the_negation + test_the_cell_carries_a_negation_and_it_names_every_exclusion; C3 P6 re-run -> test_each_lane_runs_the_gates_before_it_reads_state. Enumerated D1's category over the help route's whole reachable set (the three lanes' SKILL.md + every file their subcommand index's reference column names + reference/router-subcommands.md) by grep for `perry-config show`, `perry-state --`, `perry-lint --root` and `Pack capabilities and controls`: 8 paths, 1 unrepaired (F1), 1 repaired, 6 acceptable with the reason for each. Verified no cap or budget was raised (the range touches no bin/ file, no tests/test_router_budget.py, no tests/test_next_section.py; BUDGETS byte-identical to be5b83cf, ROUTER_BYTES_AT_BASE = 20457 at ed5d9894 and at head), SKILL.md 20,371 against the 20,480 cap, and that everything the router lost is preserved at reference/hand-off-contract.md:13-40. Re-derived the 129-byte claim (the paragraph gave 238; 129 was the shortfall) and the 6,111-byte load-set figure (now 7,392, stale).
not-checked: I did not run the `full` or `slow` tiers at any commit, so "green" here is the affected tier only and nothing I write is a green-suite claim. I re-ran none of criterion 5's eight cases — no fresh-context transcript was produced by me, by round 2 or by round 1's reviewer, so criterion 5 is graded on the artefact in TASK-469-result.md:62-70 and by reading the procedure, never by observing an agent. I did not re-run the author's own twelve mutations (M-series, S1-S4) and take no position on whether their specific edits are killed; my six are different edits of the same declared kind. I did not mutate reference/startup.md, reference/hand-off-contract.md, goals/SKILL.md or decide/SKILL.md at all, nor the eight-case table's row contents. I did not exercise /perry adopt, diagnose or relocate, any non-English or split-layout path, or `/pmo help runbook-check` against a fixture — F1 is established by reading the shipped instructions, not by running an agent down that route. I did not review the perry/ board or journal rows for this task, the TASK-470/471/473 boundaries, or deviations 2 and 3 beyond accepting round 1's finding that no criterion forbids them. My first-pass mutation harness discarded failing output, so I cannot say which test produced the two first-pass reds I could not reproduce.
proof: F1 — work/SKILL.md:23-25 still says "apply `$PERRY_HOME/reference/config.md § Pack capabilities and controls` before loading software-ops references or running an optional pack's route", and work/SKILL.md:294 ("With arg: print that row, then **read the matching reference file** so the procedure is in context") makes `/pmo help runbook-check` load exactly such a reference — work/SKILL.md:275-279 names `$PERRY_HOME/packs/software-ops/{architecture,runbooks,incidents}.md` as the reference file for five subcommands, and reference/startup.md:31-32 confirms the help route loads "the one reference its row names". reference/config.md:174-175 ("Read `perry-config show --root <project> --json` and `perry-state --root <project> --section project`") is that procedure's step 1. work/SKILL.md:30 does not cover it and says so: "Rendering help rows is the one thing that procedure is NOT applied to." So SKILL.md:85's "No update check, config, state, modes, dashboard or write" is still false of an Explain request, on the one route that runs no recovery gate — the same category as D1, in a file the spec's `Files in scope` lists. F2 — tests/test_startup_routing.py:246-252 (`WEASEL`) is a closed list of eight strings checked only in the 140 characters after the five phrases in `sentences()` (tests/test_startup_routing.py:225-241), and `TestTheThenCellCarriesCriterionOne` never applies it: SKILL.md:85 with " unless the answer needs one" appended is green (A1), as are SKILL.md:89 widened to "and any projection the answer needs" (A2), SKILL.md:108 followed by "Reading the state root to confirm is expected." (A3), SKILL.md:129 followed by "A stale run is the exception; resume it." (A4), work/SKILL.md:24 with "printing the help index" added (A5), and work/SKILL.md:137 reading "gates before the next operation, not before this lane reads state" (A6). Six of six survived the full `--tier affected --base ed5d9894` run while C1/C2/C3 died, so the greens are the guards' reach, not the harness's.
=== END VERDICT ===
