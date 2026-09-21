# Architecture review — TASK-471 integration (late gate)

This is the independent integration architecture review that `work/reference/dispatch.md § Architecture review`
requires. TASK-471 (session budgets at safe task boundaries) changed `bin/ARCHITECTURE.md` and was merged at
`abfd6cd5` without this review. The gap was found by `perry/evidence/2026-09/TASK-473-acceptance.md`.
The brief is `work/reference/review.md § Integration architecture reviewer brief`. The reviewer did not implement
the change and was given no author compliance verdict.

## Compliance block (verbatim)

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: independent architecture reviewer, Claude Opus 5 subagent, fresh context, not the TASK-471 author; timestamp: 2026-09-21T05:58:42Z
Base: 1d5e164994aa81d4deebe19cdc4167b6dd2110ba
Head: abfd6cd5fa906baa459a23bd3aa0b6c168f84659
Triggers:
  - Listed boundary paths: FALSE. `git diff --name-status 1d5e1649 abfd6cd5` touches no viewer/parsers.py, bin/lib/, schema/ or SKILL.md.
  - New top-level directory: FALSE. `git ls-tree --name-only` gives the same top-level entries at base and head.
  - New bin executable: FALSE. `git diff --raw -- bin/`: perry-context-budget is 100755 -> 100755 (M); ARCHITECTURE.md and README.md are 100644 -> 100644. Nothing was added or renamed.
  - Contract-version change: FALSE. No schema/*-contract.md or state-schema.json changed. No version or contract string appears in any +/- line of the product diff. Root §5 versions are unchanged because the root blob is identical. The handoff template's new § 0 is not schema-declared: schema mentions handoff/ only as a path, and parsers.walk_handoff reads by filename.
  - Root architecture edit: FALSE. ARCHITECTURE.md blob 169dc2ff is the same at base, at head and at 4414ddee.
  - Module architecture edit: TRUE. bin/ARCHITECTURE.md f92438bf -> bf7ffff2, with §2 lines 64-66 rewritten.
Context:
  - Root ARCHITECTURE.md §1 (:43-56), §2 (:58-136), §3 (:138-166), §5 (:211-238) and §6 (:240-295) were read at base. The file is byte-identical at head, so the line numbers are the same.
  - Component mapping from root §2:
      bin/perry-context-budget, bin/README.md, bin/ARCHITECTURE.md -> `bin/` (:60-73); module document bin/ARCHITECTURE.md, read at base and head.
      work/reference/{autopilot,dispatch,review,subcommands}.md, work/state/handoff_TEMPLATE.md -> lanes (:100-118); no module document.
      reference/host-capabilities.md -> `modes/, packs/, reference/, templates/` (:120-127); no module document.
      tests/test_context_budget.py -> `tests/` (:129-132); no module document.
  - MISSING module documents: lanes, reference/ and tests/. §2 declares no module document for any of them. OQ-2 (:310-312) says the module-document contract is undeclared.
  - Unresolved facts: root §2 is agent-written and is not in the header's user-confirmed list (:3). The mapping is unambiguous by path, but it rests on an unconfirmed §2.
  - Later main (abfd6cd5..4414ddee) was checked. TASK-470 (293fba87, 9c1a2b7c) moved `§ Budget boundary` from subcommands.md to work/reference/budget-boundary.md. The body is byte-identical apart from one trailing blank line. All six pointers were re-aimed: dispatch.md:13 and :410, review.md:430, task-close.md:122, autopilot.md, host-capabilities.md:71, and handoff_TEMPLATE.md:11 and :115. bin/perry-context-budget, bin/ARCHITECTURE.md, bin/README.md and tests/test_context_budget.py are unchanged since the head. Nothing reverted or contradicted TASK-471.
Rules:
- ARCHITECTURE.md:43-56 (§1 scope: skill on three hosts, no service, not unattended, no state outside the project) — holds. The new Budget boundary says "Perry never resets the host session or schedules one: the user opens it" (subcommands.md@head:228+). perry-context-budget now reads less outside the project: the `~/.claude/projects/*/<id>.jsonl` glob was removed from locate() (perry-context-budget@head:126-130).
- ARCHITECTURE.md:156-157 (allowed directions; tools import parsers, parsers import nothing from bin/) — holds. The diff adds no import. perry-detect-host remains a subprocess, not an import (host_identity, :112-124).
- ARCHITECTURE.md:160 (Forbidden: a second reader of any state file) — holds for the diff: no parse was added. The pre-existing reader is recorded under NN-1 below.
- ARCHITECTURE.md:161-162 (Forbidden: a lane computing a number) — holds. The Budget boundary runs one gate and says "never restate either" for the session binding and ceiling. Handoff § 0 "Budget" carries the gate's printed figure.
- ARCHITECTURE.md:163-165 (Forbidden: a tool reaching another project) — holds. Host transcripts are not a project. The diff narrows the reads to ~/.codex/sessions, plus the caller's explicit --session path.
- ARCHITECTURE.md:166 (Forbidden: an agent writing ARCHITECTURE.md) — holds. The root file is untouched.
- ARCHITECTURE.md:216-221 (§5 bin -> agent exit contract) — not touched. The exit semantics are unchanged: OVER exits 1 and unknown exits 0, observed as rc=0 under PERRY_HOST=claude-code. A bad flag still exits 2.
- ARCHITECTURE.md:223-238 (§5 task-list 2.4, perry-state, schema <-> template) — not touched.
- ARCHITECTURE.md:242-248 (§6 NN-1 one reader per state file, no exception listed) — CONTRADICTS at head. This is pre-existing and not introduced by the diff. bin/perry-context-budget:74-90 (declared_ceiling) parses .perry/config.jsonl itself. It has done so since 68843150 (2026-08-31), at base and at head, and still does at 4414ddee. viewer/parsers.py owns config parsing (:85). bin/README.md:790 calls this "a named NN-1 deviation". USER-971 (perry/asks.jsonl:72, answered 2026-09-18) decided to "record it as an NN-1 Known exception in ARCHITECTURE.md §6". That decision was never applied: the root blob 169dc2ff has not changed since before 2026-09-18, and NN-1 has no Known exceptions line. TASK-471 edited this tool and bin/ARCHITECTURE.md's description of what it reads, but did not apply USER-971.
- ARCHITECTURE.md:250-259 (NN-2 store is truth) — not touched. No store is written or rendered.
- ARCHITECTURE.md:261-267 (NN-3 no unperformed write reported) — holds. The tool stays read-only. An `unknown` verdict is printed as "UNKNOWN — not gating", never as within budget.
- ARCHITECTURE.md:269-276 (NN-4 bin decides nothing about meaning) — holds. The change removes an environment heuristic, and claude-code maps mechanically to unknown (bind, :418-421).
- ARCHITECTURE.md:278-283 (NN-5 suite never writes into its tree) — holds. tests/test_context_budget.py uses tempfile.mkdtemp (:70) and sets HOME to the fixture (:85-87).
- ARCHITECTURE.md:285-295 (NN-6 agent describes, does not decide) — holds. No root section was edited.
- bin/ARCHITECTURE.md@head:62-70 (§2, what perry-context-budget reads outside the project) — holds against the code. HOST_IDENTITY has only codex-cli (:57). locate() globs only ~/.codex/sessions (:126-130). Claude binds only via --session (bind :412-421). The children() walk under `<--session path>/subagents` runs only after an explicit --session.
- bin/ARCHITECTURE.md@head:94-95 (§3 "a tool never parses a state file itself") — contradicts, pre-existing. This is the same declared_ceiling read as NN-1. bin §3 is not in that document's confirmed list (:3).
- bin/ARCHITECTURE.md@head:96-99 (no tool imports a tool; lib imports no tool) — holds. The only cross-tool use is a subprocess.
- bin/ARCHITECTURE.md@head:100-101 (lock spans read/decide/write) — not touched (read-only tool).
- bin/ARCHITECTURE.md@head:152-156 (NN-B1 --help runs nothing) — holds. Only the docstring changed, and --help printed and exited.
- bin/ARCHITECTURE.md@head:158-166 (NN-B2 undeclared token refused) — holds. --bogus exits 2 (argparse, unchanged).
- bin/ARCHITECTURE.md@head:168-174 (NN-B3 one resolver, lib.resolve_project_root) — not touched by the diff. Pre-existing observation: perry-context-budget@head:503 resolves `--root`, then `$PERRY_PROJECT`, then cwd, with no walk and without lib.resolve_project_root. Not charged to this candidate.
- bin/ARCHITECTURE.md@head:176-182 (NN-B4 --help is usage first, soft) — not touched materially. The docstring keeps its prose-first shape.
- Module documents for lanes, reference/ and tests/ — no rules can be checked because no document exists (see Context).
Decision: BLOCKED. (1) At head, root §6 NN-1 (ARCHITECTURE.md:242-248) is contradicted by bin/perry-context-budget:74-90. The contradiction is pre-existing, not introduced by this diff. The user has already decided the resolution (USER-971), but the decided exception was never recorded, so the rule is not resolved. The same read contradicts bin/ARCHITECTURE.md:94-95. (2) The module documents for three touched components (lanes, reference/, tests/) do not exist. Under the brief's walkthrough fixture 1, an absent module document is missing context. The diff itself contradicts no rule.
User decision required: none new for NN-1, because USER-971 decided it. Applying it is an edit to a confirmed §6 rule in the user's file (ARCHITECTURE.md:166, :289-291). The user must either make that edit or explicitly authorise an agent to add the NN-1 Known exceptions line as worded in USER-971; this review then needs to be re-run. Separate question: does a §2 component with no declared module document count as "missing context" that blocks every lane or reference change, or as "none declared" (see OQ-2, ARCHITECTURE.md:310-312)?
Not checked: no full or targeted test suite was run (the PMO did not require one, and the claims were checked by reading the code plus two direct tool runs). Plain-CLI Claude subagent identity was not checked (no plain-CLI session was available; USER-972 accepts this). TASK-471's V4 criteria and behaviour beyond the architecture rules were not checked. perry-context-budget was not run under a fixture HOME, because the worktree guard refused a HOME override; the claude-code branch returns before any transcript lookup. Scratch was the session scratchpad outside the repository, not the perry-scratch-derivation path, because the worktree guard refused that block's command substitution.
=== END COMPLIANCE ===
```

## Supporting notes

**Candidate.** The merge is `abfd6cd5`, with first parent `1d5e1649`. The range adds `6bb4dc6f` (the host identity
and Codex session_meta change) and `61c215d5` (budget checkpoints, the handoff § 0 and resume). It also adds `f961428a`,
whose only file is `perry/evidence/2026-09/TASK-471-result.md`. The product diff is 10 files:
`bin/ARCHITECTURE.md`, `bin/README.md`, `bin/perry-context-budget`, `reference/host-capabilities.md`,
`tests/test_context_budget.py`, `work/reference/{autopilot,dispatch,review,subcommands}.md` and
`work/state/handoff_TEMPLATE.md`.

**USER-971: the answer to the PMO's question.** The decision is still unapplied at `4414ddee`. `ARCHITECTURE.md` §6 NN-1
(`:242-248`) still has no Known exceptions entry, and `bin/perry-context-budget:74-90` still reads
`.perry/config.jsonl` directly. That leaves a confirmed §6 rule contradicted by the code. The contradiction predates
TASK-471. It was raised at the TASK-468 integration review and asked as USER-971, which was answered
2026-09-18 during TASK-471's dispatch. The TASK-471 V4 review (`TASK-471-v4-review.md:184-189`) notes that
USER-971 was not on its branch. The resolution is decided, and the remaining step is the edit.

**USER-972** (Claude reads `unknown` everywhere) is applied as decided. The code at `bind` `:418-421`, the host matrix
(`reference/host-capabilities.md:55`) and the autopilot fallback agree. A direct run with `PERRY_HOST=claude-code
CLAUDE_CODE_SESSION_ID=abc` printed `UNKNOWN — not gating` with the "unverified identity" reason, rc 0.

**Descriptive drift for correction.** None of these is a rule contradiction on its own.
1. `bin/ARCHITECTURE.md` §2 was edited without a §8 change-log entry, and "Last reviewed" still says 2026-09-15. The
   TASK-468 review raised the same follow-up.
2. `bin/ARCHITECTURE.md:72-76` "The one tool that reaches outside" still names only `perry-codex-preflight`. This is a
   TASK-468 follow-up, still open and not touched here.
3. `bin/ARCHITECTURE.md` does not mention the `.perry/config.jsonl` read that `bin/README.md:790` calls an NN-1
   deviation. Once USER-971 is applied, the module document should point at the exception.
