# TASK-469 — V4 review (round 1)

Date: 2026-09-20. Reviewer: fresh-context review agent (Claude Opus 5), not the
implementer. Criteria: `perry/evidence/2026-09/TASK-469-spec.md` — the only
authority for PASS/FAIL.

## Identity of what was reviewed

- **Range:** `be5b83cf..bb3d97d6`, branch `worktree-agent-af202feafc663d266`.
  Not merged to main.
- **Commits:** `078d6da2` (routing + guard), `86121e40` (prose fixes),
  `5fe74346` (result evidence), `bb3d97d6` (durations entry + two result lines).
- **Where I worked:** my own worktree
  `/Users/bytedance/proj/Perry/.claude/worktrees/agent-a3b3fe81145ad21fd`, at a
  detached `bb3d97d6`. Nothing was written to
  `/Users/bytedance/proj/Perry/perry` (the live project state) and no Perry
  write tool was run. This file and its commit are the round's only output.

## 1. Suites — establishing what the result does not record

The result's § Suites says "Final-commit full and slow runs: see the addendum at
the end." **There is no addendum.** `perry/evidence/2026-09/TASK-469-result.md`
is 159 lines and ends at deviation 7. The author edited that very line again in
`bb3d97d6` (to add the first slow run's red) and still wrote no addendum, so the
final-commit full and slow results were never recorded.

I ran them. With `PERRY_PROJECT` and `PERRY_HOME` unset, at `bb3d97d6`, in my
worktree:

| Run | Result |
|---|---|
| `bash tests/run --tier affected --base be5b83cf` | green — 51 modules · 1601 tests · 83.2s. Selection: 54 of 160 modules, 3 held back to the slow tier. **Not a green suite.** |
| `bash tests/run --tier full` | **green** — 156 modules · 4386 tests · 278.1s. Tree guard clean. |
| `bash tests/run --tier slow` | **green** — 160 modules · 4489 tests · 224.4s. Tree guard clean. `test_durations_provenance` passes with the `sec: null` entry. |

So the unrecorded claim is true: at the final commit the suite is green on all
three tiers. The defect is that the result asserts an addendum it does not
carry — a reader of the branch cannot tell a green final run from an unrun one.
156 = 160 modules on disk minus the 4 in `tests/parallel § HARNESS_SELF_TESTS`,
which matches the author's "156 modules, 4,386 tests" figure for `078d6da2`.

## 2. Mutations — I broke it and watched

Method: line-anchored edits (never `str.replace` over a whole file), `__pycache__`
purged and 1.3 s slept past the whole-second mtime boundary before each run,
then `bash tests/run --tier affected --base be5b83cf` in full, then a restore
from `git show bb3d97d6:<path>` verified with `bin/perry-restore-check` — never
against bytes my own harness snapshotted. Every restore passed; the tree guard
reported "nothing moved" on every run. Harness: scratchpad `t469/mutate.py`,
`t469/swap.py`.

### Structural claims I re-verified (the author's M-series is not evidence to me)

| # | Mutation | Result |
|---|---|---|
| T1 | `SKILL.md:86` Query cell `−2, −1, 1, 2` → `−2, −1, 1` | **RED** — `test_every_state_route_runs_the_recovery_gates`, assertion FAIL |
| T3 | `SKILL.md:102`/`:114` recovery and interrupted calls swapped (a true swap, not a rename) | **RED** — `test_recovery_precedes_interrupted_precedes_state` |
| T4 | `decide/SKILL.md:42` drops `blocking recovery and` from the pointer | **RED** — `test_each_lane_defers_its_startup_to_the_router` |

So the table-shape guard works on the columns it parses.

### Prose mutations — six greens, and each green is a finding

The author's guard "checks shape, never intent". These are what that costs. All
six are single-line edits to tier-0 or tier-2 prose, and `--tier affected`
stayed **green** on every one.

| # | File:line | Edit | Suite |
|---|---|---|---|
| P1 | `SKILL.md:106` | on `blocking: true`, "**continue to the state read as usual** and report every exact path and error" (was "stop before any further project-state read or mutation and") | GREEN |
| P2 | `SKILL.md:89` | delete "Nothing reads state before step 2." — the entire router-side content of `86121e40` | GREEN |
| P3 | `SKILL.md:85` | Explain's **Then** cell → "the pages that answer, plus `perry-task list --json` and the dashboard" | GREEN |
| P4 | `SKILL.md:128` | "**Never resume without asking.**" → "**Resume the run and report it afterwards.**" | GREEN |
| P5 | `reference/startup.md:47` | blocking bullet → "unanswered; listing the state root afterwards is fine." — the entire content of the case-6 fix | GREEN |
| P6 | `work/SKILL.md:123` | "interrupted-run gates **before** this lane reads state" → "**after** this lane reads state" | GREEN |

**P6 is the sharpest.** `test_each_lane_defers_its_startup_to_the_router`
(`tests/test_startup_routing.py:106-124`) slices the lane's ritual at
`**Compute the state` and asserts the literals `recovery` and
`interrupted-run gates` appear in the head. It therefore cannot tell "run the
gates **before** the state read" from "run them **after**". The one word
carrying the whole of AC2's and AC3's ordering in the lanes is unguarded, and
this new module is the only thing that reads those lines at all.

**P3 is the same shape one column over.** `routes()`
(`tests/test_startup_routing.py:43-52`) captures only the **Run** cell, and
`test_explain_runs_no_state_config_or_update_step` asserts
`steps(...) == {"−2"}`. AC1's actual content — no dashboard, no update check, no
mode loading, no project-state read — lives entirely in the **Then** cell, which
nothing parses.

**P1, P4 and P5 are criterion 2's own sentences** — the blocking stop, the
never-resume rule, and the "not even a listing" clause that was `86121e40`'s
answer to the case-6 failure. Each can be inverted in place with nothing going
red. P1 and P4 are pre-existing sentences, so their exposure is not a regression
this branch introduced; P2 and P5 *are* this branch's own fix and ship with no
guard at all.

I did not mutate the eight-case table's row **contents**; reading
`test_the_cases_page_is_named_and_holds_eight_cases` is enough to see it counts
rows and never reads them, so a case row can say anything and still pass.

## 3. Criterion 2's enumeration — every route that reaches a project-state read

Rule 1 says enumerate the category, not find the next instance. The category is
"a shipped instruction that reaches a project-state read (or a write) on a route
where the delivered contract says it does not". `reference/startup.md:15-17`
supplies the definition I enumerate against: *"Any read under the project: the
state root, `.perry/` (the config store, dossiers, events, roles), `AGENTS.md`,
the code. Any `perry-state`, `perry-task`, `perry-tasks`, `perry-explain` or
`perry-lint --root .` call."*

| # | Entry point | What it reads | Gated by step 2 first? | Verdict |
|---|---|---|---|---|
| 1 | Router, Change → step 3 `perry-state --compact` (`SKILL.md:134-138`) | state root | yes | correct |
| 2 | Router, Query → one projection (`SKILL.md:86`) | state root | yes | correct |
| 3 | Router step 1, `.perry/config.jsonl` (`SKILL.md:97`) | **the config store** | **no — step 1 precedes step 2** | **defect, D2** |
| 4 | Router step 1's "if it does not exist and a state file does, prompt for first-time setup" (`SKILL.md:97`) | state-file existence, then a **write** path | **no** | **defect, D2** |
| 5 | `/perry help <lane>` → `work/SKILL.md:23-24` → `reference/config.md:174-175` | `perry-config show --json` **and** `perry-state --section project` | **no gate on Explain at all** | **defect, D1** |
| 6 | `goals/SKILL.md:20-22` — same pointer, in the always-read preamble | same | no | same category as D1 |
| 7 | `/perry help` → `reference/router-subcommands.md:93-96` | same procedure, but only "on that request" | n/a — the follow-up is its own route | acceptable |
| 8 | Lane snapshots, `{goals,work,decide}/SKILL.md` step 2 | state root | **yes — new; at `be5b83cf` no lane named the recovery gate at all** | genuine improvement |
| 9 | Lane subcommand pages, after the lane snapshot | state root | yes, transitively | correct |
| 10 | `/perry adopt`, `/perry diagnose`, `/perry relocate` — subcommands, so Change | state root | yes; `reference/adoption.md:121` still defers the gate to router step 2 | correct |
| 11 | First-time setup (`SKILL.md:142`) | writes | yes — "only if step 2 found neither" | correct |
| 12 | `work/reference/autopilot.md:147` → the lane's own first move | state root | yes, transitively | correct |
| 13 | `AGENTS.md:12-22` (this repo dogfooding itself) | runs `--section recovery` then `--section interrupted` itself | yes, independently | correct |

Ten of thirteen are correct and row 8 is a real safety gain. Rows 3, 4 and 5/6
are not.

## 4. Findings

### D1 — AC1 fails: the Explain route is still instructed to read project state

`SKILL.md:85` promises Explain "**No** update check, config, state, modes,
dashboard or write". `/perry help work` is Explain: the router's help row says
"The Explain route: no snapshot" (`SKILL.md:192`) and `work/SKILL.md:121`, a
line *this change wrote*, says "Run this before any subcommand but `help`".

But `work/SKILL.md:23-24` — unedited, in a file the spec lists in scope, in the
"How this file is organized" preamble that every load of the lane reads — still
says:

> **Pack eligibility:** apply `$PERRY_HOME/reference/config.md § Pack capabilities
> and controls` before loading software-ops references or rendering **its help rows**.

and `reference/config.md:174-175`, step 1 of that procedure, is:

> Read `perry-config show --root <project> --json` and `perry-state --root
> <project> --section project`.

So the delivered contract tells the Explain route to run `perry-state` — two
project-state reads, on the one route that runs **no recovery gate at all**.
`work/SKILL.md:26` compounds it ("Do not offer inactive pack commands as
active"), which cannot be obeyed without that read, while `work/SKILL.md:280`
says to print the index "verbatim".

The author saw this. Case 2's own trace records the agent reading
`reference/config.md § Pack capabilities`, and the remedy was written as
`reference/startup.md:32-35` ("Rows that depend on an optional pack are shown
marked as needing that pack, not filtered: finding out whether it is active
would mean reading the config store"). **That is the wrong file.**
`reference/startup.md:3` says it is "Read when the route is unclear, or to check
a case"; the help route is not unclear, does not load it, and the author's own
case-2 trace does not list it. The correcting sentence sits in a page the
failing path never opens, and the instruction that actually drives the behaviour
was left standing. Case 2 passed because that one agent happened not to run the
command, not because the procedure stopped asking for it.

This is the TASK-044 shape the round's rules name: the site that was noticed got
the fix; the site that directs the behaviour did not. `goals/SKILL.md:20-22`
carries the same pointer and was likewise left.

### D2 — AC2: the Query route reads the config store, and can start a write, before the recovery gate

`SKILL.md:89`, added in `86121e40`, states the absolute: "**Nothing reads state
before step 2.**" `reference/startup.md:15-17` defines a project-state read to
include `.perry/` and "the config store". `SKILL.md:97` is step 1 — before step
2 — and reads `.perry/config.jsonl`.

`reference/startup.md:21-24` concedes exactly this: "Step 1 reads
`.perry/config.jsonl` before the recovery gate. That order predates routing and
is kept." So the tier-0 absolute is false by the tier-2 definition shipped
beside it, and the only reader who learns that is one who opens the tier-2 page.
AC2 requires that "a state query checks recovery before project-state access";
on the delivered Query route it does not, under the implementation's own
definition of the term.

The second half of `SKILL.md:97` is worse than a read: "If it does not exist and
a state file does, **prompt for first-time setup**." First-time setup is a write
path, and `reference/startup.md:58-60` says "First-time setup writes the config
store, so a query never starts it" — a rule contradicting the step the Query
route is told to run. `SKILL.md:99` ("before anything else reads project state")
and `SKILL.md:89` both assert an ordering that `SKILL.md:97` breaks.

The ordering itself is pre-existing, and the author flags it in deviation 5's
last bullet. What is new, and what I am failing, is that this change **added a
tier-0 absolute that is not true of the procedure printed eight lines below it**,
in the criterion that is the safety one. Either step 1 moves after the gate, or
the absolute is qualified where it is written.

### D3 — the case-6 fix is in a page the round-2 agent did not read

The result's AC6 row says round 1's cases 4 and 6 were "Fixed in `86121e40`".
`git diff 078d6da2 86121e40` is four hunks. Case 4's remedy is `SKILL.md:89`,
which the agent does read. **Case 6's remedy is only `reference/startup.md:47`**
("nothing else of the project is read, not even a listing"). The round-2 trace
for case 6 (`TASK-469-result.md:69`) records "detect-host, config, recovery,
stop" — `reference/startup.md` does not appear in it. So the round-2 pass for
case 6 cannot be attributed to the change made for it; it is one agent behaving
differently on a text it never saw. Mutation P5 shows nothing else holds that
line either.

### D4 — the result asserts an addendum it does not carry

§ 1 above. `TASK-469-result.md:134` promises it; the file ends at line 159. The
claim turns out to be true — I ran the suites — but on the branch as delivered
the final-commit full and slow results do not exist, and `bb3d97d6` edited that
very line without adding them.

### D5 — the guard cannot see the criteria it is offered against

Mutations P1–P6. The result's AC1 row cites
`test_explain_runs_no_state_config_or_update_step`; P3 shows that test does not
read the cell AC1 is about. The AC2 row cites
`test_every_state_route_runs_the_recovery_gates` and
`test_recovery_precedes_interrupted_precedes_state`; those hold for the router
(T1, T3), but P6 shows the lane equivalent cannot see the ordering word. Naming
a test beside a criterion in an evidence table is not the same as that test
covering the criterion, and here it does not.

## 5. The two declared deviations, judged against the written criteria only

- **Deviation 2 — lane subcommands no longer render the router dashboard.**
  Against AC4 ("do not repeat the full ritual when routing within the same
  unchanged operation") this is what AC4 asks for, and AC3's snapshot
  requirement is written only of "Explicit `/perry` overview", which
  `SKILL.md:87` still routes to steps 3b–6. **No criterion is violated.** It is
  a user-visible behaviour change and the author is right that someone should
  sign it off; that is not a reviewer's call and I am not negotiating it.
- **Deviation 3 — the Query route skips the update check.** AC1 requires that
  omission of Explain only. No criterion requires the update check on Query and
  none forbids skipping it, and it is not a safety gate. **No criterion is
  violated.** Flagged for the user's decision, not resolved here.

## 6. Claims from the result I checked and found true

- File bytes: all seven figures match `wc -c` exactly at `bb3d97d6`.
- Bills: `add-task` 99,075 · `close-task` 89,937 · `dispatch` 113,282 ·
  `plan-phase` 107,542 — `bin/perry-context-budget --bill all` reproduces each.
  No cap or budget raised; `SKILL.md` at 20,426 is under both the 20,480 cap and
  `test_next_section.py:72`'s 20,457 growth guard.
- Prose line delta `be5b83cf..bb3d97d6` over the six doc files: `+141 / −26`,
  exactly as claimed. Python and tests `+125 / −0`.
- `git diff --check`: clean.
- "156 modules, 4,386 tests" = 160 on disk minus the 4 in
  `tests/parallel § HARNESS_SELF_TESTS`. Correct, and my own full run reproduces
  both numbers.
- The step-3 rationale removed from tier 0 ("an abandoned adoption reports
  `installed: false` too") really is preserved at
  `reference/snapshot.md § Why the interrupted-run gate exists`, which
  `SKILL.md:118-119` still points at. The **rule** stayed in tier 0; only the
  *why* moved. Sound.
- Deviation 1 is accurate and costs no coverage:
  `TestStartupRootDescriptionsNameLiveLaneDirectories` skips lines without the
  word "contains", and the base lane lines had none either.
- "Before this change, no lane named the recovery gate at all" — confirmed
  against `git show be5b83cf:{goals,work,decide}/SKILL.md`. The lane pointers are
  a real safety gain, and the strongest thing on this branch.
- AC5's negative holds: the diff touches no `bin/` file and adds no classifier.

One small inaccuracy: the result says "Steps −2 to 3 are unchanged in wording
and order", and the same bullet then lists the step-2 and step-3 wording it
removed. The **rules** are unchanged; the wording is not.

## 7. Verdict reasoning

The branch does real good: the lanes gain a recovery gate they never had, the
router's ordering is guarded against three structural breaks, and the byte
accounting is honest and reproducible. AC3, AC4 and AC5 are met. But AC1 is
contradicted by an unedited in-scope file on the one route that runs no gate
(D1); AC2's new absolute is false of the procedure printed below it, and its
Query route can reach a write before the recovery gate (D2); and the evidence
for AC6's "all eight cases meet their outcomes" does not support the case-6 half
of it (D3). D1 and D2 are prose defects in a project whose prose *is* the
program.

FAIL, on D1 primarily.

=== VERDICT ===
task: TASK-469
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-469-spec.md
checked: Detached bb3d97d6 in my own worktree (/Users/bytedance/proj/Perry/.claude/worktrees/agent-a3b3fe81145ad21fd); nothing written to /Users/bytedance/proj/Perry/perry and no Perry write tool run. Ran `bash tests/run --tier affected --base be5b83cf` (green, 51 modules/1601 tests — NOT a green suite) and, because the result's promised addendum does not exist, `--tier full` (green, 156 modules/4386 tests) and `--tier slow` (green, 160 modules/4489 tests) at the final commit. Nine mutations, each line-anchored, __pycache__ purged with a 1.3s wait past the second boundary, restored from `git show bb3d97d6:<path>` and verified with bin/perry-restore-check (all nine restores OK, tree guard clean on every run): T1 Query cell drops step 2 -> RED; T3 true swap of the recovery/interrupted calls -> RED; T4 decide lane drops `blocking recovery and` -> RED; P1 invert the blocking-recovery stop (SKILL.md:106) -> GREEN; P2 delete "Nothing reads state before step 2." (SKILL.md:89) -> GREEN; P3 give Explain's Then cell a dashboard and `perry-task list --json` (SKILL.md:85) -> GREEN; P4 invert "Never resume without asking." (SKILL.md:128) -> GREEN; P5 invert the case-6 fix (reference/startup.md:47) -> GREEN; P6 flip the lane pointer's "before this lane reads state" to "after" (work/SKILL.md:123) -> GREEN. Enumerated all 13 entry points that reach a project-state read (section 3) against reference/startup.md:15-17's own definition, by grep over every shipped .md for `perry-state`, `Mandatory first move`, `section recovery` and `Pack capabilities`. Re-derived the result's byte, bill, line-delta, module-count and diff --check figures; verified the base lanes named no recovery gate via `git show be5b83cf:`; verified the step-3 rationale survives in reference/snapshot.md.
not-checked: I ran no fresh-context agent transcripts of my own — the eight cases are graded here by reading the procedure and by mutation, not by re-running cases 1-8 against a fixture, so I did not independently reproduce any of the author's read traces. I did not exercise `/perry adopt`, `/perry diagnose` or `/perry relocate` end to end; rows 10-13 of section 3 are read-verified only. I did not mutate the eight-case table's row contents (the guard visibly counts rows without reading them). I did not check the six pre-existing defects in the result's deviation 5, the TASK-470/471/473 boundaries, or whether reference/startup.md should have earned an index row and a place in the snapshot bill. I did not run the suite at be5b83cf, so "green before and after" rests on the author's baseline claim, not mine. No non-English or split-layout path was exercised, and I did not review the perry/ board or journal rows for this task.
proof: D1 — work/SKILL.md:23-24 ("apply `$PERRY_HOME/reference/config.md § Pack capabilities and controls` before loading software-ops references or rendering its help rows") sends the Explain route into reference/config.md:174-175 ("Read `perry-config show --root <project> --json` and `perry-state --root <project> --section project`"), which SKILL.md:85 forbids that route; the correction was written to reference/startup.md:32-35, a page reference/startup.md:3 says is read only when the route is unclear and which the author's own case-2 trace does not list. goals/SKILL.md:20-22 is the second instance. D2 — SKILL.md:89 ("Nothing reads state before step 2.") is false of SKILL.md:97, which reads `.perry/config.jsonl` and may "prompt for first-time setup" before the recovery gate at SKILL.md:99-109; reference/startup.md:15-17 defines the config store as project state, and reference/startup.md:21-24 and :58-60 both concede the conflict. D3 — the only bytes 86121e40 changed for case 6 are reference/startup.md:47, and the round-2 trace for case 6 at perry/evidence/2026-09/TASK-469-result.md:69 lists no read of that file. D4 — perry/evidence/2026-09/TASK-469-result.md:134 promises an addendum; the file ends at line 159. D5 — tests/test_startup_routing.py:43-52 parses only the Run cell (mutation P3) and tests/test_startup_routing.py:106-124 slices on `**Compute the state` without checking order words (mutation P6).
=== END VERDICT ===
