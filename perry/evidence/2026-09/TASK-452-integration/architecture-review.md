# TASK-452 — integration architecture review (fresh context)

Integrator: PMO, 2026-09-21. Reviewer: a fresh `general-purpose` subagent that
did not implement the candidate and received no author attestation. Candidate
7791e2a9 merged `--no-ff` onto main 27206828 as `integ/task-452` 13733b21
(tree c8c99851). Integrator trigger facts: listed boundary paths TRUE
(`viewer/parsers.py`, `schema/README.md`); new top-level directory, new bin
executable, contract-version change, root and module architecture edits FALSE.

Verbatim:

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: independent architecture reviewer (Claude Opus 5). Fresh context. Not the TASK-452 author. No author attestation was received. Read-only: nothing was written, checked out or run against either checkout. Timestamp: 2026-09-21T10:10Z.
Base: 272068285fdc105e116940a5fd7b375ed2c551fe
Head: 13733b21e66c0da7f8cceef2bc1afa45885a784b
Triggers:
- `git diff 27206828 13733b21` is byte-identical to diff.patch. The integ tree HEAD is 13733b21e66c….
- Listed boundary paths: TRUE. `viewer/parsers.py` and `schema/README.md` changed.
- New top-level directory: FALSE. Name-status shows only four M entries, and `--summary` is empty.
- New bin executable: FALSE. `bin/perry-state` is 100755 on both sides (`--raw`), and nothing was added or renamed.
- Contract-version change: FALSE.
  - No `schema/*-contract.md` changed, and none of the nine contract pages publishes the `architecture` payload. A grep found only the unrelated `type` enum text in decide-list-contract.md:94.
  - Payload shape is unchanged: `architecture` is still `encode(snap.arch_meta)` (bin/perry-state:2192) and keeps its `status` key. Only the value changes, and it is now always "".
  - The only consumer of `status`, the draft warning, is removed. The compact render at bin/perry-state:3076-3078 does not read `status`.
  - Root §5 (212-239) has no architecture-payload contract.
- Root architecture edit: FALSE. Module architecture edit: FALSE. No `*ARCHITECTURE.md` path is in the diff.
Context:
- Root ARCHITECTURE.md, read in full: §1 (43), §2 (58-137), §3 (139-167), §4 (169-210), §5 (212-239), §6 (241-303), §7 (305-330).
- Component mapping, confirmed against §2:
  - `bin/perry-state` → `bin/` (60-73). Module document: bin/ARCHITECTURE.md.
  - `viewer/parsers.py` → "viewer/parsers.py — the one reader" (83-91). No module document is declared, so none is missing.
  - `schema/README.md` → `schema/` (93-98). No module document is declared.
  - `tests/test_parsers.py` → `tests/` (130-133). Module document: tests/ARCHITECTURE.md exists (§2 does not link it) and was read.
- Module documents read: bin/ARCHITECTURE.md (§1-§8) and tests/ARCHITECTURE.md (§1-§5).
- Base state checked: `lib.anchor_root` (A1) already exists at bin/lib/__init__.py:1124-1130. The base schema already has three `"anchor": "code"` entries: `files[architecture]`, `files[architecture-module]` and `claims[14]`.
- Unresolved facts: none.
Rules:
- Root §1:43-56 (stdlib-only; no semantic judgement; no out-of-project state) — holds. `anchor_root` resolves `code_repo_path` relative to the project root (lib:1129). It adds no dependency and makes no semantic judgement.
- Root §2:83-91 (parsers owns architecture parsing and project/state-root resolution) — holds. Parsing stays in `parse_arch_meta` (parsers:4025). The new code-root resolution lives in `bin/lib § anchor_root`, which was on base (A1) and is not a parsers-owned resolver. The diff only hands its result in: parsers:5207 and 5235 `read((code_root or root) / "ARCHITECTURE.md")`.
- Root §2:93-98 (schema owns declared shape) — holds. README:350 now says "the architecture documents `"anchor": "code"`". That matches state-schema.json, where exactly `architecture`, `architecture-module` and `claims[14]` (ARCHITECTURE.md) are code-anchored.
- Root §3:157-158 ("Tools import `parsers`; `parsers` imports nothing from `bin/`") — holds for this diff. `bin/perry-state` calls `lib.anchor_root` and passes a `Path` into `P.load_snapshot(..., code_root=code_root)` (perry-state:1752-1753). The parsers hunks add no import; the docstring at parsers:5209-5210 states the constraint.
  - Observation, not caused by this diff: parsers already has two lazy function-scope imports of `bin/` modules. One is `import lib` at parsers:90-95; the other is `import perry_md_store` at parsers:377-381. Both are unchanged here and not attributable to TASK-452. Whether they are compatible with 158 is a separate question.
- Root §3:161 Forbidden (second reader) — holds. No new reader. `ARCHITECTURE.md` is still parsed only in parsers.
  - `tier1_caps` counting lines at perry-state:1483 is pre-existing behaviour; only its root changes. It now points at the same file `architecture` reads, which removes a state-vs-code split rather than adding one.
  - The other `load_snapshot` callers (perry-task:6722 and 8345, perry-goals:1215, parsers:5641) do not use `arch_meta`.
- Root §3:164-166 Forbidden (tool reaching another project) — holds. Root resolution is unchanged. `code_repo_path` is this project's own declared config, read through the shared reader (lib:1127).
- Root §3:167 Forbidden (agent writing ARCHITECTURE.md) — not touched. No architecture document is edited.
- Root §4:195-206 (one read entry point: stores → parsers → perry-state) — holds. The read still goes through parsers, and only its root differs.
- Root §5:232-234 (`--compact` is a strict projection of `--json`) — holds. The COMPACT entry `("architecture","architecture","value")` (perry-state:2934) is unchanged.
- Root §5 contract versions (task-list 2.4 etc.) — not touched.
- Root §6 NN-1:243-256 (one reader per state file; Known exceptions) — holds. The check grep (`def parse_` in bin/) lists no new parser, and every hit is pre-existing. No new exception is needed, and none of the existing ones is affected.
- Root §6 NN-2:258-267 — not touched.
- Root §6 NN-3:269-275 — not touched. perry-state is a reader.
- Root §6 NN-4:277-284 (bin decides nothing about meaning) — holds. Removing the `Status:` read (parsers:4038) and the draft warning takes a text-derived judgement out. The remaining ageing check is a date comparison (perry-state:1987-1989).
- Root §6 NN-5:286-291 (suite never writes into its tree) — holds. `test_architecture_is_read_at_the_code_root` writes only inside `tempfile.TemporaryDirectory()`. The refactored `perry_state()` helper runs `--root <tmp|FIXTURE>` read-only.
- Root §6 NN-6:293-303 — not touched. The diff contains no architecture-document edit.
- bin/ARCHITECTURE.md §3:99-106 (a tool never parses a state file itself) — holds. perry-state gains no parse, and the direct line count is pre-existing.
- bin/ARCHITECTURE.md §3:107-110 (tool imports no tool; lib imports no tool) — holds. Only `lib.anchor_root` is called.
- bin/ARCHITECTURE.md §6 NN-B1, NN-B2, NN-B4 — not touched. No surface or flag change.
- bin/ARCHITECTURE.md §6 NN-B3:178-184 (one resolver, one order) — holds. `perry_root`/`root` come from the existing resolver, and `anchor_root` derives a location from them rather than re-resolving.
- tests/ARCHITECTURE.md §3:29-33 (tests exercise production entry points and do not replace them; fixtures isolate writes) — holds. The new test runs `bin/perry-state` as a subprocess against temporary projects.
Decision: PASS — no contradictions and no missing context.
User decision required: none. One descriptive follow-up for the user to consider, not blocking: root §7 OQ-1 (307-317) still says `perry-state --section architecture` reports `exists: false` while the schema anchor stands. After A1 and this A2 that is stale. §7 is outside NN-6's freely editable sections (agents may add, not delete), so updating or closing OQ-1 is the user's call.
Not checked:
- I did not run the suite, the new test or any mutation. Test behaviour and V4 correctness are outside this gate.
- I did not audit DESIGN-017 §5/§6 A2 beyond what the architecture rules require.
- I did not judge whether the pre-existing lazy parsers→bin imports (parsers:90-95, 377-381) conform to root §3:158. They are not in this diff.
- I did not verify `code_repo_path` paths that escape the project root (for example `../other`) against ADR-002. That is A1's `anchor_root` behaviour on base and is not changed here.
=== END COMPLIANCE ===
```
