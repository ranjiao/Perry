# TASK-471 — V4 review (independent)

Date: 2026-09-20. Reviewer: independent V4 agent, own worktree
`/Users/bytedance/proj/Perry/.claude/worktrees/agent-a2b4f400b1fb701fc`, detached at
`f961428a`. Criteria: `perry/evidence/2026-09/TASK-471-spec.md` — the only authority.

No prior V4 verdict exists for this row. A V4 was dispatched on 2026-09-18 and
recorded none; the row's `review` status is not evidence that anything passed.

## 1 · What was under review

- Range `be5b83cf..f961428a`, three commits, on `worktree-agent-a3b7edb300c9fac3d`
  (same head on `worktree-agent-aca0b262c7504d1b8`). Not merged to main.
- 11 files, +320 / −76. One code file (`bin/perry-context-budget`), one test file,
  seven prose files, one template, one result file.

## 2 · Suites, run by me on the committed head

The worktree was clean at `f961428a` for every run (`git status --porcelain`
empty), `PERRY_PROJECT` and `PERRY_HOME` unset, `__pycache__` purged first.

| Run | Result |
|---|---|
| `bash tests/run --tier affected --base be5b83cf` | **55 modules · 1819 tests · 86.8 s · green**, exit 0. Selection block present: `selected 56 of 159 modules · 410.5 of 841.9 module-seconds (48.8%)`, with `test_merge_gate.py` held back to the slow tier. |
| `bash tests/run` (= `--tier full`) | **155 modules · 4381 tests · 270.6 s · all green**, exit 0. |
| `bash tests/run --tier slow` | **159 modules · 4484 tests · 336.0 s · all green**, exit 0. |

**Both board numbers reproduce.** The row's "author full 4381 / slow 4484 green"
is true of this tree.

On the tier-selection block: only `--tier affected` emits one — a full or slow run
selects nothing, so it prints module/test counts and no selection line. The result
file records the counts for full and slow, which is what those runners print; it
records no affected run. I did not rely on the author's transcript for any of the
three numbers — I produced all three myself.

**A green `--tier affected` is not a green suite.** It is green for the 55 modules
it named. The full and slow runs above are separate evidence and are stated as such.

## 3 · Mutations on `bin/perry-context-budget`

Method: `git archive f961428a` into a scratch tree under the session scratchpad
(never the checkout under review); every edit anchored by line number against the
bytes of `git show f961428a:bin/perry-context-budget`; `__pycache__` purged and a
1.1 s wait past the second boundary around every write; restore written from
`git show` and re-verified against a **fresh** `git show` call, not against a
snapshot. Suite per mutant: `python3 -B -m unittest tests.test_context_budget`
(41 tests). Unmutated baseline: 41 OK.

| # | Mutation (line) | Result |
|---|---|---|
| Mu1 | `bind()`: the `host == "claude-code"` branch made unreachable (418) | **RED**, 3 failures |
| Mu2 | Claude binds by id again — `HOST_IDENTITY` regains `claude-code` (57), the guard disabled (418), `locate()` globs `~/.claude/projects` again (130) | **RED**, 4 failures |
| Mu2b | TASK-468's superseded rule restored: unknown only under `CLAUDE_CODE_CHILD_SESSION` (57, 130, 418) | **RED**, 4 failures |
| Mu3 | R-L1 reverted: last `session_meta` wins (207) | **RED**, 3 failures |
| Mu4 | `report` initialised `"verdict": "OK"` instead of `"unknown"` (507) | **RED**, 12 failures |
| Mu5 | R-L2/S3 reverted: the inherited zero-delta snapshot counts as a turn (225) | **RED**, 1 failure |
| Mu6 | `>=` ceiling → `>` , i.e. exactly-at-ceiling is not OVER (541) | **RED**, 1 failure |
| Mu7 | exit code pinned to 0 (557) | **RED**, 3 failures |
| Mu8 | `scope` reads `current` when the host gives no identity (454) | **RED**, 2 failures |

Nine of nine killed. No survivor. Mu2 and Mu2b are the ones that matter: they are
the two ways the R-M1 defect could come back, and the new two-shape fixture
(`test_a_claude_session_id_binds_nothing_because_a_subagent_carries_its_parents`)
fails on both. Mu6 establishes that "at ceiling" is a real, pinned case and not a
claim in a table. Every restore verified against `git show f961428a:<path>`.

## 4 · The unknown value, enumerated

Every place the `unknown` verdict is produced or consumed, and what each does:

| Site | What it does with `unknown` |
|---|---|
| `bin/perry-context-budget:507` | `report["verdict"] = "unknown"`, `context = None` — the initial value, so any path that fails to bind lands here rather than on a number |
| `bin/perry-context-budget:415-428` (`bind`) | five abstain branches: `--session` absent + OpenCode / `claude-code` / host not in `HOST_IDENTITY` / no identity / ≠1 transcript |
| `bin/perry-context-budget:533-538` | a bound transcript whose records name another session, or that carries no usage record yet, stays `unknown` with a reason |
| `bin/perry-context-budget:546` | text output: `context : unknown` / `verdict : UNKNOWN — not gating` / `why : <reason>`. Never a percentage, never a number |
| `bin/perry-context-budget:557` | exit **0** — `int(verdict == "OVER")` |
| `bin/perry-context-budget:409` (`print_bills`) | the *bill* mode fails closed the other way: `unknown` or `over` → exit 1 |
| `work/reference/subcommands.md § Budget boundary` | third table row: print `context: unknown — not measured` and the reason; **"never call it within budget"**; autopilot bounded by `--max-dispatches`; interactive bounded to one more task per answer |
| `work/reference/autopilot.md` step 7 | summary line `unknown — not measured`, **"never a clean budget"** |
| `work/reference/autopilot.md` loop, stop check | "It does **not** mean the context is fine", print the reason once, fall back to `--max-dispatches`; "the loop never passes `--session`" |
| `work/reference/dispatch.md § Pre-flight` | one line, names only the `OVER` outcome, and cites `§ Budget boundary` for the rest |
| `work/reference/review.md` | one line, names only the `OVER` outcome, and cites `§ Budget boundary` for the rest |
| `work/state/handoff_TEMPLATE.md § 0` | Budget field spells the unknown form: `unknown — not measured: <reason>` |
| `reference/host-capabilities.md` | "`unknown` is not a clean budget", points at `§ Budget boundary` |
| `bin/README.md`, `bin/ARCHITECTURE.md` | descriptive only |

No programmatic consumer of the gate's JSON exists anywhere in the tree — I
checked `bin/`, `viewer/` and `setup/`; the single hit in `bin/lib/__init__.py`
is a comment about decimal places. The gate's only consumers are the procedures
above. **Nothing treats `unknown` as a number, and nothing calls it within
budget.** Exit 0 for `unknown` is deliberate and documented in three places, and
is the only thing that lets a Claude host run at all under the user decision that
accepts Claude-as-unknown (see § 7 note 5 — the ask id is deliberately not cited
here); the
fail-safe is carried by the printed abstention plus the `--max-dispatches` bound,
not by the exit code.

Verified live, from this very session (a Claude Code Desktop subagent, so the
exact shape R-M1 is about):

```
context  : unknown
verdict  : UNKNOWN — not gating
why      : unverified identity: Claude Code gives its subagents the main session's
           CLAUDE_CODE_SESSION_ID and no verified signal tells them apart; --session
           gives only an explicit, caller-asserted reading
EXIT=0
```

## 5 · Safe stop and bounded resume, constructed rather than read

Fixture: `tests/fixtures/sample-project` copied twice into the scratchpad. One
copy took a normal `perry-task status REL-009 … --status in_progress` write
(the reference). The other ran the same write under a harness that hard-kills the
process (`os._exit(9)`) at the first `os.replace` — the point at which the durable
marker is on disk and neither half of the canonical pair has landed. This is
exactly the state criterion 3 forbids the procedure from creating, constructed so
that resumption can be observed.

- The interrupted copy carried `.perry-task-transaction.json`, `phase: commit`,
  2 entries (`tasks.jsonl`, `journal/2026-09/2026-09-20.md`), both staged, neither
  applied.
- `perry-state --section recovery --json` reported `"blocking": true` and named the
  marker — result Case 5 reproduces.
- Resuming with the next Perry command completed the transaction forward **once**:
  store row identical to the reference copy field-for-field, journal line present
  exactly once, `perry-lint` clean of any new finding. **Nothing lost, nothing
  duplicated.**

Two honest qualifications:

1. The recovery machinery is pre-existing (`bin/perry-task § recover_transaction`)
   and is not touched by this range. What TASK-471 adds is the written rule that a
   budget stop records the interruption and does not repair it, which matches what
   the machinery does.
2. In that hard-kill, the store+journal pair recovered but the **event-log record
   for the status change was lost** (reference copy 3 `REL-009` events, recovered
   copy 2). The event is appended after the canonical pair, outside the marker —
   `bin/perry-task:2735` documents that ordering choice for the linkage edge. This
   is a property of the store at `be5b83cf` as much as at `f961428a`; `bin/perry-task`
   is not in this range. It is **out of scope for this row**, and it does not
   contradict the procedure, which tells the agent to let the write return rather
   than to kill it. I record it so the next round inherits it rather than
   rediscovering it.

## 6 · Criteria

| # | Criterion | Finding |
|---|---|---|
| 1 | TASK-309 inspected; no second checkpoint engine | Met. The only `bin/` change is `perry-context-budget`; nothing executor-side is added. The procedure only *lists* an in-flight dispatch as pending. |
| 2 | Check before a task/review dispatch and after a completion; reuse the measured source and configured ceiling; no second budget | Met. Before: `dispatch.md § Pre-flight`, `review.md`, the autopilot loop. After: `subcommands.md § close-task`, `dispatch.md § On completion` step 8. One command, no restated ceiling in any of the five call sites; the tool resolves the ceiling through its documented four-level precedence. See § 7 note 1. |
| 3 | At/over: atomic safe boundary, record pending, decline the next dispatch; never interrupt a store write or auto-resume | Met. `§ Budget boundary` `OVER` row plus the "Safe boundary" paragraph; constructed and observed in § 5. |
| 4 | Handoff carries goal, task/spec, base/head/worktree, changes, receipts, unresolved criteria, pending decisions, next command; ≤ 8 KiB, evidence by reference | Met. All nine fields are rows in `handoff_TEMPLATE.md § 0`, plus pending work and the budget verdict. Empty template measured by me: **3,666 bytes**, matching the result file. The section states "≤ 8 KiB in all; cite evidence by path, never paste logs". |
| 5 | Fresh reader verifies revision and recovery/task state; changed base or stale receipts require revalidation; no host reset or scheduler | Met. The "Resuming" paragraph orders the three checks; "Perry never resets the host session or schedules one: the user opens it." Nothing in the range adds a scheduler or a host API. |
| 6 | Below/at/over, unknown, active operation, stale handoff, changed source; unknown visible, bounded, never "within budget" | Met. Below/at/over and four unknown shapes are pinned by tests I mutated (Mu6 kills at-ceiling, Mu4 kills the unknown label); active operation constructed in § 5; stale handoff and changed source are authored walkthroughs over real `git rev-parse` output, which the result file declares as such (Deviation 5). Unknown is visible with its reason and is bounded twice: `--max-dispatches` in autopilot, one-task-per-answer interactively. |

Bound respected: two checkpoints, one handoff shape, seven cases. No executor
checkpoint engine, no host session management.

## 7 · Notes that are not failures

1. **`§ Budget boundary` says "never restate either" (the session binding or the
   ceiling); the autopilot loop restates the ceiling** as
   `${max_context:+--ceiling $max_context}`. This is not a second budget — the flag
   is the tool's own documented most-specific source, it is omitted when
   `max_context` is unset, and the autopilot text says "with the run's ceiling"
   explicitly. Criterion 2 is met. The sentence in `subcommands.md` is nevertheless
   looser than the one caller it governs, and a future reader may read them as
   contradicting. Worth one clause on the next edit of that file.
2. **The close-task bill in the result file is 5 bytes low.** The result records
   after = 92,252 and Δ = +2,039; the head actually measures **92,257**, and
   `work/reference/subcommands.md` grew 24,185 → 26,229 = **+2,044**. The recorded
   "before" (90,213) is right. Cap 95,000 is not approached either way, and no cap
   was raised (`BILL_BUDGETS` is untouched in the range). An arithmetic slip in a
   table, not a behaviour.
3. **`dispatch.md § Pre-flight` now points into `subcommands.md`, which the
   dispatch bill does not load** (dispatch bill = `SKILL.md`, `work/SKILL.md`,
   `dispatch.md`, `dispatch-preflight.md`, `git-boundaries.md`). A dispatch that
   follows the pointer reads a 26 KiB file the bill does not account for. The
   result file names the placement choice deliberately ("the section that owns
   handoffs"). No criterion covers bill placement; recorded for the next round.
4. **The two ask records that authorise this row are not on this branch.** The
   dispatch brief cites USER-971 (the NN-1 exception) and USER-972 (Claude reads
   as unknown everywhere); `perry/asks.jsonl` at `f961428a` carries neither — they
   were recorded on main at `e023fb25` and `9dddda60`, after the pinned base. Only
   USER-970 is present, and it is the only one the row's own spec and result cite,
   which is why `test_diagnose § test_perry_itself_passes_its_own_id_checks` is
   green on the head. I found this by writing "USER-972" into this review and
   watching that test turn red with `dangling: ['USER-972']` — so the id is
   deliberately not spelled in § 4. Not a defect of the row; a live trap for
   anything that quotes the brief into branch evidence, and the reason a merge
   must bring the asks with it.
5. **Tool wording vs procedure wording.** The tool prints `UNKNOWN — not gating`;
   the procedure asks the agent to print `unknown — not measured`. Both are honest
   and neither says "within budget", but the two phrasings are not the same phrase
   and only one of them is what a reader of the transcript will see.

## 8 · Prose mutations — six of seven survive

The deliverable of this row is mostly procedure text, so the same question has to
be asked of it: does anything hold it? Same method as § 3 — scratch copy, anchor
asserted to occur exactly once in `git show f961428a:<path>`, restore re-verified
against a fresh `git show`. Suite: the twelve document-contract modules the
affected tier selects (`test_pointers_resolve`, `test_procedures_call_the_tool`,
`test_procedures_read_the_contract`, `test_reference_pages_are_reachable`,
`test_spec_scannability`, `test_router_budget`, `test_work_modes`,
`test_task_writer_contracts`, `test_stranded_rows`, `test_review_verdicts`,
`test_shipped_vocabulary`, `test_parsers` — 542 tests, baseline OK).

| # | Mutation | Result |
|---|---|---|
| P1 | `#### Budget boundary` renamed to `#### Budget boundaries` | **RED**, 2 failures (`test_no_pointer_names_a_section_that_is_not_there`, `test_every_section_citation_names_a_section_that_exists`) |
| P2 | the `unknown` row deleted from the gate table | **GREEN — survived** |
| P3 | the after-task checkpoint line deleted from `close-task` | **GREEN — survived** |
| P4 | the before-dispatch checkpoint sentence deleted from `dispatch.md` | **GREEN — survived** |
| P5 | "Safe boundary" replaced with "Stop wherever you are." | **GREEN — survived** |
| P6 | the "Resuming" checklist replaced with "just carry on" | **GREEN — survived** |
| P7 | the `Base · head` row deleted from `handoff_TEMPLATE.md § 0` | **GREEN — survived** |

§ 8.1 closes the gap between "these twelve modules" and "any module".

**What this means, stated exactly.** Only the *name* of the section is pinned —
by the two citation-resolution tests, because five other files cite it. The
*content* is pinned by nothing: the rule that stops `unknown` reading as a clean
budget, both checkpoints criterion 2 asks for, the safe-stop rule of criterion 3,
the resume checklist of criterion 5 and a required field of criterion 4's handoff
can each be deleted and the suite stays green.

**This is not a criterion failure and I am not scoring it as one.** The spec puts
"existing context tests only if needed" in scope and asks criterion 6 to
*demonstrate* cases, not to regress them; the iteration plan rules out a new
evaluation framework; and the project's own standing rule is that Python does not
judge document semantics. The author declares exactly this in Deviation 5. The
behaviour that *can* be tested — the gate, the ceiling comparison, the unknown
verdict, the Claude abstention — is tested, and § 3 shows those tests bite.

It is recorded here because the next round should inherit it rather than
rediscover it: the procedural half of TASK-471 has a regression surface of zero,
and the first careless edit to `subcommands.md` will not be caught by `tests/run`.
If that is to change it is a new row, not a fix to this one.

### 8.1 · Why they survive, enumerated rather than sampled

A survivor against twelve modules is only evidence about twelve modules, so I
enumerated the whole test tree instead of sampling more of it:

```
grep -rln "Budget boundary|not measured|budget checkpoint|Safe boundary|Resume point" tests/
  tests/test_same_action_linkage.py   :1249  `if not measured:`        — unrelated
  tests/test_queue_sla.py             :151   "…was not measured"       — unrelated
  tests/test_durations_provenance.py  :148   "…means exactly 'not measured'" — unrelated
```

**No test in `tests/` names the section, its table, the safe-boundary rule, the
resume checklist or the handoff's `Resume point` at all.** Twenty-odd modules
open `work/reference/subcommands.md`, but for structural properties — headings,
byte budget, vocabulary, pointer targets, spec scannability — never for this
content. That is the whole explanation for P2–P7, and it is an enumeration of the
category, not the next instance of it.

## 9 · Verdict block

```
=== VERDICT ===
task: TASK-471
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-471-spec.md
checked: Ran on the committed head f961428a in my own detached worktree, clean tree, PERRY_PROJECT/PERRY_HOME unset, __pycache__ purged: `tests/run --tier affected --base be5b83cf` (55 modules, 1819 tests, green, selection block present — NOT a green suite), `tests/run` (155 modules, 4381 tests, all green) and `tests/run --tier slow` (159 modules, 4484 tests, all green); both board numbers reproduce independently of the author's transcript. Nine line-anchored mutations of bin/perry-context-budget in a `git archive` scratch copy, each with __pycache__ purged and a wait past the second boundary, each restored from and re-verified against a fresh `git show f961428a:<path>`: the claude-code abstain branch (418), Claude binding restored by id (57+130+418), TASK-468's superseded CHILD_SESSION rule restored (57+130+418), R-L1 last-session_meta-wins (207), report initialised OK instead of unknown (507), R-L2/S3 inherited zero-delta counted as a turn (225), at-ceiling `>=`→`>` (541), exit code pinned to 0 (557), scope `current` without an identity (454). All nine RED; no survivor. Seven prose mutations of the procedure text (renamed the cited `§ Budget boundary` heading, dropped the unknown row, the after-task checkpoint, the before-dispatch checkpoint, the safe-boundary paragraph, the resume checklist and the base/head handoff row) run against the twelve doc-contract modules (542 tests): P1 RED, P2–P7 all GREEN — the section's NAME is pinned by two citation-resolution tests, its CONTENT by nothing; confirmed by enumerating the whole `tests/` tree, where no module names the section, its table, the safe-boundary rule, the resume checklist or the handoff Resume point (§ 8). Enumerated all fourteen sites that produce or consume the `unknown` verdict across bin/, work/reference/, reference/, templates and README, and established what each does with it: none is numeric, none labels it within budget, and no programmatic consumer of the gate's JSON exists in the tree. Ran the gate live from this Claude Desktop subagent: unknown, exit 0, reason printed. Constructed a genuinely interrupted store transaction in a scratchpad fixture copy (hard kill at the first os.replace, durable marker on disk, neither half applied): `perry-state --section recovery` reported blocking true, and resuming completed it forward exactly once — store field-identical to a reference copy that took the same write uninterrupted, journal line present once, lint clean. Measured handoff_TEMPLATE.md at 3,666 bytes and all five --bill figures on the head. Read every line of the 11-file diff. All destructive work was done on `git archive` and `cp -R` copies under the session scratchpad; the checkout under review was never modified. Finally re-ran `tests/run --tier affected --base be5b83cf` on the branch carrying this review document: green, 55 modules, 1819 tests — after one red I caused myself by citing an ask id the branch does not carry (§ 7 note 4), which is evidence the id checks bite and that the head itself is clean of them.
not-checked: (0) I did not run the full suite against each surviving prose mutant one at a time — P2 and P4 were started that way and I did not wait for them; the tree-wide grep in § 8.1 is what the survival claim rests on, and a test that held this content without naming any of those five strings would not appear in it. (0b) The row's base is now 11 commits behind main (`be5b83cf..main` = 7568dc3b); the row's 11 files are disjoint from the 19 main changed, so a merge is textually clean, but I ran no suite on a merged tree — that is the integration gate's job, not this rung's. (a) Plain-CLI Claude — I am a Desktop subagent, so R-M1's plain-CLI shape stays unverified by observation exactly as the author declares; the fixture covers the shape, not a real host. (b) I did not run a live dispatch, so I did not observe a real executor completion arriving after an OVER stop, nor an autopilot loop actually taking the `--max-dispatches` fallback end to end. (c) Cases 6 and 7 (stale handoff, changed source) I checked only as written walkthroughs against the mechanics they cite; I did not re-stage the author's two-commit fixtures. (d) I did not re-measure the four bills at be5b83cf, so the result's "before" column is verified only by arithmetic against the head. (e) I did not review TASK-468's own delivery, only the four findings this row carries from it. (f) I did not run `--tier full`/`--tier slow` a second time, so a one-in-many flake in either would not have shown. (g) The event-log record lost by a hard kill (§ 5 note 2) I traced to bin/perry-task, which is outside this range; I did not enumerate every other writer with the same post-pair append ordering.
proof: n/a — PASS
=== END VERDICT ===
```
