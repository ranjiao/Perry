# TASK-451 — integration architecture review (fresh context)

Integrator: PMO, 2026-09-21. Reviewer: a fresh `general-purpose` subagent (agent
id `af0e0772cb7e8e172`) that did not implement the candidate and was not given the
author's compliance block. Candidate 232c3e92 was merged `--no-ff` onto main
37e5de12 as `integ/task-451` db74c48a (tree 2eea78fb, the same tree the full gate
tested). The earlier branch review was against base 7ffcc633, 272 commits behind,
so it does not bind this tree.

Trigger facts recorded by the integrator before dispatch: listed boundary paths
TRUE (`schema/state-schema.json`, `bin/lib/__init__.py`); new top-level directory,
new bin executable, contract-version change, root architecture edit and module
architecture edit FALSE. Inputs: `git diff 37e5de12 db74c48a` (539 lines),
`--name-status` (six M), `--summary` (empty).

Verbatim:

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: independent architecture reviewer (Claude Opus 5 subagent). Fresh context, not the task author. I did not read the candidate's result.md or the earlier review verdict. Timestamp: 2026-09-21T08:37Z.
Base: 37e5de120e3c5db1d8f1e54297034ca3d63bda76
Head: db74c48a6ee8974b341c552113c26d05be69ee90 (`^1` = base, `^2` = 232c3e928b7f1468396795e6fb4cff21971aa940; the integ-tree HEAD equals head. A fresh `git diff 37e5de12 db74c48a` is byte-identical to diff.patch.)
Triggers:
- Listed boundary paths: TRUE. `schema/state-schema.json` and `bin/lib/__init__.py` both change (DESIGN-017 §5.3 lines 279-280).
- New top-level directory: FALSE. `git ls-tree -d --name-only` is identical at base and head.
- New bin executable: FALSE. The `bin/` name listing is identical. `perry-lint` and `perry-state-cost` stay 100755, `lib/__init__.py` stays 100644. name-status shows only M on six files.
- Contract-version change: FALSE. No `schema/*-contract.md` is in the diff. schema_version does not appear in the diff. The only "contract" hits are docstring wording.
- Root architecture edit: FALSE. ARCHITECTURE.md is blob bc1665eb at both base and head.
- Module architecture edit: FALSE. bin/ARCHITECTURE.md (5cfcb82b), tests/ARCHITECTURE.md (cc6260d4) and release/ARCHITECTURE.md (29254f74) are identical at base and head.
Context:
- Root sections read in full: ARCHITECTURE.md §1 (43-56), §2 (58-137), §3 (139-167), §5 (212-239), §6 (241-303) and §7 (305-330), at head.
- Also read: DESIGN-017 §1.4, §4, §5.1-5.3 and §6 (A1 at line 323, D2 at line 330); USER-933 (perry/asks.jsonl:34).
- Component mapping, confirmed against §2: `bin/lib/__init__.py`, `bin/perry-lint` and `bin/perry-state-cost` belong to `bin/` (§2:60-73, which declares module doc bin/ARCHITECTURE.md). `schema/state-schema.json` belongs to `schema/` (§2:93-98, no module document declared, so none is missing). `tests/test_claims.py` and `tests/test_state_cost.py` belong to `tests/` (§2:130-133). §2 has no module-document line for `tests/`, but tests/ARCHITECTURE.md exists and calls itself the `tests/` component map (line 3), so I read it.
- Module documents read: bin/ARCHITECTURE.md and tests/ARCHITECTURE.md at head.
- Unresolved facts: none.
Rules:
- ARCHITECTURE.md:53-56 (§1 scope: no state held outside the project) — holds. `anchor_root` (bin/lib:+1124) only resolves where to read. The code root comes from the project's own `code_repo_path`, which DESIGN-017 §5.1:241-242 decided. `perry-lint` and `perry-state-cost` only read or measure there. Nothing in the diff writes there.
- ARCHITECTURE.md:157-158 (allowed directions; parsers imports nothing from bin/) — holds. lib reaches parsers through the existing `_parsers()` (lib:459). `viewer/parsers.py` is not in the diff.
- ARCHITECTURE.md:161 (Forbidden: a second reader of any state file) — holds. `.perry/config.jsonl` is read through `parsers.config_store_settings` (parsers:428), not re-parsed. No `def parse_` was added: the NN-1 grep counts 15 at both base and head.
- ARCHITECTURE.md:162-163 (Forbidden: a lane computing a number) — not touched. No lane file is in the diff.
- ARCHITECTURE.md:164-166 (Forbidden: a tool reaching another project; `resolve_project_root` is the one implementation) — holds. Project-root resolution is unchanged. The code root is derived from the already-resolved project's config. Explicit module paths are confined to the code root: `iter_targets` rejects absolute paths, `..`, and symlink escapes via `is_relative_to(root.resolve())`, and test_claims exercises this with an `escape` symlink.
- ARCHITECTURE.md:167 (Forbidden: "An agent writing ARCHITECTURE.md. This file is the user's.") — holds for behaviour, with a declarative tension noted.
  - No code in the diff writes any ARCHITECTURE.md. The schema `owner` field is only echoed in report rows (perry-lint:5010, perry-diagnose:1755) and gates no write.
  - The new `owner: "perry"` and the notes "the agent authors all sections" and "this is not blanket user ownership" (state-schema.json diff lines around 1497 and 2397) read opposite to this line.
  - The user already decided exactly this change: DESIGN-017 §6 A1 (line 323) is locked and user-signed, and USER-933 consents to "drop owner: user". DESIGN-017 §1.4 (lines 81-83) records this Forbidden line as already stale against NN-6. Changing the line itself is assigned to D2 (line 330) as a user proposal. This diff does not edit the line.
- ARCHITECTURE.md:212-239 (§5 contracts, including "the schema → both sides") — holds. `perry-lint --templates` on the head tree exits 0 and reports clean. No contract page or version changes. The `--claims` row shape is preserved: same keys, and the same `free` / `exists but empty` / `collision` / `perry` states.
- ARCHITECTURE.md:243-256 (NN-1, one reader) — holds. Same evidence as :161. No Known exception is added or needed.
- ARCHITECTURE.md:258-267 (NN-2, store is truth) — not touched. No store write or projection is in the diff.
- ARCHITECTURE.md:269-275 (NN-3, a write that cannot do what it claims refuses) — not touched. Both tools are readers. Bad explicit paths raise; bad or empty flag values exit 2.
- ARCHITECTURE.md:277-284 (NN-4, deterministic tools decide nothing about meaning) — holds. Component membership is supplied by the agent (`--architecture-module`; schema note "no directory scan or inferred membership"). Python checks only path shape, existence, containment, headings and the cap.
- ARCHITECTURE.md:286-291 (NN-5, the suite never writes its tree) — holds. The new tests use `tempfile.TemporaryDirectory` and the Repo fixture. I ran `test_claims` and `test_state_cost` (52 tests, OK) and `perry-lint --templates` in the integ tree. `git status --porcelain --ignored` was byte-identical before and after.
- ARCHITECTURE.md:293-303 (NN-6, an agent may describe, not decide) — holds. ARCHITECTURE.md is unedited. The authority table in the schema note (user confirms §1, the §2 list, §3 Forbidden, §5 bumps, §6 and §7 closure) matches NN-6 and DESIGN-017 §5.1:205-214.
- bin/ARCHITECTURE.md:99-105 (a tool never parses a state file itself) — holds. The config is read via parsers, and no new direct read of a store was added.
- bin/ARCHITECTURE.md:106-108 (a tool never imports another tool) — holds. The diff adds no tool-to-tool import. The test's `inproc.load("perry-lint")` is in tests/, not a tool.
- bin/ARCHITECTURE.md:109 (`lib` imports no tool) — holds. `anchor_root` uses only `_parsers()`.
- bin/ARCHITECTURE.md:110-111 (lock spans read, decide, write) — not touched.
- bin/ARCHITECTURE.md:162-166 (NN-B1, `--help` never runs anything) — holds. The `-h` / `--help` branch is still first in the perry-lint argv loop and was not moved.
- bin/ARCHITECTURE.md:168-176 (NN-B2, undeclared token refused) — holds. `--architecture-module` is an explicit branch, unknown tokens still exit 2, a missing value exits 2, an empty value exits 2 via `lib.empty_root_error`, and combining it with a non-project mode exits 2.
- bin/ARCHITECTURE.md:178-184 (NN-B3, one resolver, one order) — holds. Project-root resolution is untouched. The diff removes the two inline anchor ternaries (perry-lint claims and files loop, perry-state-cost:251) in favour of one `lib.anchor_root`. The remaining anchor consumers are perry-diagnose:1744 (dir claims only), perry-tasks:1870 and parsers:538 (both state-anchored `.jsonl` only). None of them sees the new file claim, so no divergent resolution is left.
- bin/ARCHITECTURE.md:186-192 (NN-B4, soft: `--help` is usage first) — holds. Three usage lines were added. The long refusal rationale comments were cut, not moved into help.
- tests/ARCHITECTURE.md:29-33 (tests exercise production entry points; fixtures are isolated write targets) — holds. The test runs real `bin/perry-lint` as a subprocess with `--root <tmp>`.
- DESIGN-017 decision 5 / S6 (module document cap 600; root 500) — holds. `architecture-module` is declared `cap: 600`, `cap_kind: hard`, and the root stays 500. The test asserts that a 600-line module document gets `size-cap`.
Decision: PASS. No decided section is contradicted by behaviour. The §3:167 tension is user-decided under DESIGN-017 A1 and USER-933, and the line itself is scheduled for the user under D2. No descriptive statement in the root or touched module documents becomes false.
User decision required: none for this merge. Carry-over already planned: under DESIGN-017 D2, §3:167 still says the file is the user's while the schema now declares `owner: perry`. The user should decide that line soon so the decided text and the schema stop disagreeing.
Not checked:
- Full suite not run; only `test_claims`, `test_state_cost` and `perry-lint --templates`.
- No mutation testing.
- A2 is out of scope: I did not check whether `perry-state` / `parsers.parse_arch_meta` still look for the document at the state root. If they do, lint and perry-state would locate it differently until A2 lands. Also, `viewer/parsers.py` cannot import `bin/lib.anchor_root` (§3:158), so A2 will need its own code-root reading or a move of the resolver into parsers.
- Outside the architecture documents: schema/README.md:349-350 still says everything other than `.perry/` is `"anchor": "state"`. That is now false for ARCHITECTURE.md (`"code"`). It is a descriptive drift in the schema component's README that should be corrected, but it is not a rule in the reviewed documents.
- Behaviour when `code_repo_path` is absolute and outside the git repo for `perry-state-cost`'s `relative_to(repo)`: I saw the existing `try` but did not exercise it.
=== END COMPLIANCE ===
```
