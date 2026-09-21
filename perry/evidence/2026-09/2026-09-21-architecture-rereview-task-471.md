# Architecture re-review — TASK-471 integration, after USER-978

This re-runs the integration architecture review of TASK-471. The first run,
`perry/evidence/2026-09/2026-09-21-architecture-review-task-471.md`, was BLOCKED
for two reasons: root §6 NN-1 was contradicted at head, and module documents
were missing. USER-978 (`perry/asks.jsonl`) decided both. The PMO applied the
decisions in `2225d076`, which is merged at `16124fb0`. The brief is
`work/reference/review.md § Integration architecture reviewer brief`. I followed
`work/reference/review-constraints.md`. The reviewer did not implement TASK-471
or USER-978 and was given no author compliance verdict.

## Compliance block (verbatim)

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: independent architecture reviewer, Claude Opus 5 subagent, fresh context, not the TASK-471 author and not the USER-978 editor; timestamp: 2026-09-21T06:12:37Z
Base: 1d5e164994aa81d4deebe19cdc4167b6dd2110ba (TASK-471 merge first parent); USER-978 edits reviewed as 90b88d0b3088b3675b8987e009be5cba6d4b1bbb..head
Head: 16124fb062c3ca1863fdaf5f834c2cb423158732
Triggers:
  - Listed boundary paths: FALSE. Neither the TASK-471 product diff (1d5e1649..abfd6cd5) nor the USER-978 product diff (`git diff --name-status 90b88d0b 16124fb0 -- . ':!perry' ':!.perry'`: ARCHITECTURE.md, bin/ARCHITECTURE.md, bin/perry-goals, tests/test_phase_lifecycle.py, work/reference/dispatch.md, work/reference/review.md) touches viewer/parsers.py, bin/lib/, schema/ or SKILL.md.
  - New top-level directory: FALSE. `git ls-tree --name-only` lists the same 27 entries at 90b88d0b and 16124fb0.
  - New bin executable: FALSE. In `git diff --raw 90b88d0b 16124fb0 -- bin/`, bin/ARCHITECTURE.md is 100644 -> 100644 and bin/perry-goals is 100755 -> 100755, both M. TASK-471 added none either (first review).
  - Contract-version change: FALSE. No schema/ file changed. No §5 line changed in ARCHITECTURE.md, and no version string appears in the +/- lines.
  - Root architecture edit: TRUE. ARCHITECTURE.md 169dc2ff -> c55132dd changes §2 (:101-102, :115-116), §6 NN-1 (:250-252), §7 OQ-2 (:316-319) and §8 (:364-372).
  - Module architecture edit: TRUE. bin/ARCHITECTURE.md goes f92438bf -> bf7ffff2 (TASK-471, §2 :64-70), then bf7ffff2 -> ec994948 (USER-978: header :5, §2 :77-80, §8 :201-205).
Context:
  - Root ARCHITECTURE.md at head: §1 (:43-56), §2 (:58-137), §3 (:139-167), §6 (:241-300) and §7 (:301-361) were read. §5 was read only to confirm it is unchanged. The header (:3) names the confirmed sections: §1, §3 Forbidden, §5 versions, §6 and §7.
  - Component mapping (root §2):
      bin/perry-context-budget, bin/README.md, bin/ARCHITECTURE.md -> `bin/`. The module document is bin/ARCHITECTURE.md, read at head (ec994948).
      work/reference/{autopilot,dispatch,review,subcommands}.md, work/state/handoff_TEMPLATE.md -> the lanes. §2 declares no module document.
      reference/host-capabilities.md -> `modes/, packs/, reference/, templates/`. §2 declares no module document.
      tests/test_context_budget.py -> `tests/`. §2 declares no module document.
      ARCHITECTURE.md -> the root document itself.
  - Module documents: bin/ARCHITECTURE.md exists and was checked. The lanes, reference/ and tests/ have none because root §2 declares none. Under USER-978 (3), recorded at ARCHITECTURE.md:316-319, dispatch.md:337-338 and review.md:563-564, that is not missing context.
  - Drift since the first review: `git log 4414ddee..16124fb0` on every TASK-471 product file plus ARCHITECTURE.md and budget-boundary.md shows only 2225d076. bin/perry-context-budget, bin/README.md and tests/test_context_budget.py are byte-unchanged since abfd6cd5.
  - Unresolved facts: none. Root §2 is agent-written (not in :3's confirmed list), but the mapping is unambiguous by path.
Rules:
- ARCHITECTURE.md:243-252 (§6 NN-1, one reader per state file, and its new Known exception) — holds. The exception text (:250-252) says: perry-context-budget reads one key (`session_context_ceiling`) of `.perry/config.jsonl` directly, because it must work outside a Perry project. The USER-971 answer (perry/asks.jsonl:72) says exactly this, with nothing added. The code matches it. `declared_ceiling` (bin/perry-context-budget:74-90) opens only `<root>/.perry/config.jsonl` and returns only the record where `kind == "setting"` and `key == CEILING_SETTING_KEY` ("session_context_ceiling", :71). The tool's other file reads are schema/state-schema.json § thresholds under PERRY_HOME (:103-106, not project state), host transcripts (:130, :136, :241-244, :434) and skill sources in --bill mode (:330-344). No other bin/ tool invokes the exception: `grep -rn "USER-971\|Known exception" bin/ viewer/ work/reference/ SKILL.md reference/ tests/` finds only bin/ARCHITECTURE.md:80 and :203. The `def parse_` check (:249) gives the same pre-existing list, with no new entry. Pre-existing and not charged, because the candidate touches none of these tools: other bin/ tools decode state stores themselves, for example bin/perry-lint:3130 (asks.jsonl, 2026-08-31), bin/perry-tasks:269 and :2312 (tasks.jsonl, 2026-08-19) and bin/perry-task:5513 (okr.jsonl, 2026-08-28). viewer/parsers.py already has readers for two of them (`load_task_store` :1556, `load_register_store` :1591). None cites the USER-971 exception.
- ARCHITECTURE.md:250-252 vs USER-978 (2) — holds. The PMO wrote USER-971's exception into §6 NN-1 with a §8 entry (:364-372), as decided. No other §6 rule changed (`git diff 90b88d0b 16124fb0 -- ARCHITECTURE.md` has one §6 hunk).
- ARCHITECTURE.md:314-319 (§7 OQ-2) vs USER-978 (3) — holds. The addition says a component §2 declares no module document for has none, and that a reviewer does not count its absence as missing context. It marks OQ-2 "partly answered" and leaves shape, cap, owner and drift open. That is the decision and no more.
- work/reference/review.md:562-565 and work/reference/dispatch.md:336-339 (reviewer rule) vs USER-978 (3) — holds. Both insert the same one-sentence rule. USER-978 names "the reviewer brief" (review.md). The dispatch.md sentence restates the same rule in the integrator's selection text, which would otherwise read "Missing root/module context ... cannot silently produce a pass". It adds no scope. The surrounding "Missing documents ... are unresolved, not safe" and "unknown is never false" are unchanged.
- ARCHITECTURE.md:43-56 (§1 scope) — not touched. No §1 hunk. TASK-471 holds as the first review found (no session reset or schedule; reads narrowed to ~/.codex/sessions plus an explicit --session).
- ARCHITECTURE.md:158-167 (§3 allowed directions and Forbidden) — not touched. No §3 hunk. "A second reader of any state file" (:161) is covered by NN-1 above. "An agent writing ARCHITECTURE.md" (:167): the agent's §6/§7 edits were authorised by USER-978 (2) and (3), and its §2/§8 edits are the descriptive sections that NN-6 (:291-295) lets an agent write.
- ARCHITECTURE.md:212-240 (§5 contracts and versions) — not touched. No hunk.
- ARCHITECTURE.md:289-295 (NN-6, who may change what) — holds. Changes to confirmed sections are limited to NN-1 and OQ-2, both decided by the user before landing. The §2 changes are descriptive and checked against the code. :101-102 drops the router line count and names tests/test_router_budget.py's cap, which exists (:36-37, "20 KiB"). :115-116 cites reference/first-run.md § The recommended order for a new project, which exists (:62). The router points to first-run.md (SKILL.md:140), and that file's procedure (:34) leads into the section.
- ARCHITECTURE.md other §6 rules (NN-2 to NN-5) — not touched. There are no hunks, and the TASK-471 diff writes no store and does not change the recommendation rule, as the first review found.
- bin/ARCHITECTURE.md:98 (§3, "A tool never parses a state file itself") — descriptive mismatch, not a confirmed section (bin header :3 confirms only §6 and §7). perry-context-budget:74-90 is an exception to it, and the rule line was not qualified. The §2 text at :79-80 notes the exception, so no reader of both is misled, but the rule line is stale. The pre-existing reads listed under NN-1 above also contradict this line.
- bin/ARCHITECTURE.md:77-80 (new §2 text) — DESCRIPTIVE MISMATCH. "It is also the one tool that reads a state file itself" is false against the code. bin/perry-lint:3130, bin/perry-tasks:269 and :2312, and bin/perry-task:5513 each read and decode a state store themselves. "It" is the one tool with a recorded NN-1 exception; that claim would be true. "runs no external program" is defensible, because it only runs bin/perry-detect-host through bash (:118-119, already stated at :67-70), but it is loose.
- bin/ARCHITECTURE.md:5 and :201-205 (header, §8) — holds. "Last reviewed" is now 2026-09-21. §8 gains an entry for TASK-471's §2 rewrite (6bb4dc6f) and for the USER-978 edit, which closes the previous review's drift items 1-3.
- bin/ARCHITECTURE.md:156-187 (NN-B1 to NN-B4) — not touched. bin/perry-context-budget is unchanged since the first review. NN-B3 is pre-existing at perry-context-budget:503 (`--root`, then $PERRY_PROJECT, then cwd, with no lib.resolve_project_root), predates TASK-471 and is not charged.
Decision: BLOCKED — no rule contradiction and no missing context. Both earlier blockers are resolved: NN-1's Known exception matches USER-971 and the code, and undeclared module documents are "none" under USER-978. One descriptive mismatch needs correction and re-review, per the brief. bin/ARCHITECTURE.md:79-80 says perry-context-budget is "the one tool that reads a state file itself", and bin/perry-lint:3130, bin/perry-tasks:269/:2312 and bin/perry-task:5513 show it is not. Suggested correction, agent-writable because §2 and §3 of the module document are descriptive: say instead that it is the one tool with a *recorded* NN-1 exception, and qualify bin/ARCHITECTURE.md:98 with a pointer to that exception.
User decision required: none for this candidate. Separately, and not charged: the pre-existing direct store reads (bin/perry-lint:3130, bin/perry-tasks:269/:2312, bin/perry-task:5513) are either not NN-1 parses or unrecorded NN-1 contradictions. USER-971 treated the same pattern as an NN-1 deviation, so the user may want to rule on them. That belongs to whoever next touches those tools, not to this candidate.
Not checked: no test suite was run (the PMO ran the full suite green, 158/4452, on this tree; the review is by reading code and diffs). bin/perry-context-budget was not executed. The pre-existing store reads were found by grep for `read_text`/`open(` over bin/perry-*; the search is not exhaustive, and the list is illustrative. The bin/perry-goals changes in 8a9d5ec1 were read only far enough to see that they cite no NN-1 exception; a parallel re-review covers them. TASK-471's V4 criteria were not re-checked. No scratch files were written, so the perry-scratch-derivation block was not needed.
=== END COMPLIANCE ===
```

## Supporting notes

**Setup.** The worktree was cut from origin/main at 0b5bf99e. It had no branch commits and a clean tree. It was fast-forwarded to 16124fb0 (`git merge --ff-only`, as the PMO authorised).

**What changed since the first review.** Between 4414ddee (the point the first review checked up to) and 16124fb0, the only commit on any TASK-471 product file or on either architecture document is 2225d076. So the review is the first review's findings plus that commit's edits.

**USER-971 wording against ARCHITECTURE.md:250-252.** USER-971 says "perry-context-budget reads one key (session_context_ceiling) of .perry/config.jsonl directly because it must work outside a Perry project." The §6 line says the same thing, plus the path prefix `bin/` and the ask id with its date. It adds no other key, file or tool, and no condition.

**Why the new §2 sentence is the blocker, and why it is small.** The PMO asked whether the new text in bin/ARCHITECTURE.md is accurate against the code. Most of it is. One clause makes a uniqueness claim that the code refutes. Other tools also decode state stores themselves, for example bin/perry-lint:3130, which reads asks.jsonl line by line with `json.loads`. The claim is false even if JSONL decoding is not counted as an NN-1 "parse", because the sentence says "reads a state file itself", not "parses". The fix is a wording change in an agent-writable section, and it needs no user decision.

**Items from the first review, at head.**
1. Root §6 NN-1 contradicted: resolved (ARCHITECTURE.md:250-252).
2. Missing module documents for the lanes, reference/ and tests/: resolved as "none declared" (USER-978 (3); ARCHITECTURE.md:316-319; review.md:563-564; dispatch.md:337-338).
3. bin/ARCHITECTURE.md had no §8 entry and a stale "Last reviewed": resolved (:5, :201-205).
4. "The one tool that reaches outside" named only perry-codex-preflight: resolved (:77-78).
5. The module document never mentioned the config read: resolved (:79-80). The same sentence introduced the mismatch above.
6. NN-B3 at perry-context-budget:503: still present, pre-existing, not charged.
