# TASK-489 — review round 1: V4 FAIL, architecture PASS, on 8649b63b

Candidate: `9509170c78ef47d4c0ee907f0b71e7a2df2f2dbc..8649b63bd114fa13d3642cf2b47239cfeb09e28c`
(branch `coding/task-489-importer`). Criteria:
`TASK-489-spec.md`, as amended on main at `da9d6066`.

Two fresh-context reviewers ran in their own isolated worktrees, and neither
wrote the importer. Both reported both live-store paths absent before and after
their runs: `/Users/bytedance/proj/Perry/.git/perry` and
`/Users/bytedance/proj/SkyTonight/.git/perry`. The V4 reviewer also reported
SkyTonight's fingerprint identical before and after.

## V4 review — FAIL

**Criteria 1–5 hold for both projects.** The reviewer re-derived them from the
old files with `json.loads` alone and read the kernel only through
`bin/perry-kernel`:
- this repository: 599 of 599 ids, with field, state, type, edge and
  attachment fidelity;
- SkyTonight: 34 of 34 ids;
- every count in the author's reports matched.

**The FAIL.** The blank rule is wider than the spec.
- The code: `bin/perry-kernel-migrate:119–124` delegates to
  `lib.is_blank_cell`.
- The effect: values the old writer accepts are imported as unset. Examples
  are `TBD`, `none`, `?`, `n/a`, `待定` and `-`.
- The spec: only `—` and an empty string are unset.
- Today's data: not affected. Both projects hold only those two spellings.

**Mutants.** The reviewer ran 25 and 23 were killed. The two survivors are
M8 and M9: the importer's own checks for criteria 3 and 5 were forced
always-true, and the tier stayed green.

**Findings that are not a FAIL** (paraphrased; the verbatim review is in the
session transcript):
1. The reports say ask answers and risk clearing reasons are not in the old
   stores. They are. The status cells hold them, for example USER-001's
   "30 days" and RX-001's reason. For 104 asks and 2 risks that text is not
   carried.
2. An ask's `blocks` cell is split only on commas and whitespace, so a cell
   using a semicolon loses its edges. The run still says reconciled.
3. A risk status of `mitigated`, `resolved`, `closed` or `retired` maps to
   cleared. The spec names only a status that begins with "cleared".
4. Ceilings read only the `id` key of old events. On current data the `task`
   key changes nothing.
5. The three USER→`P003-O2-KR3` edges are dropped, and no row records
   restoring them.
6. Old-log timestamps without a zone are read in the local time of the machine.
   This is `lib.ts_moment`'s documented rule.
7. A failed kernel read during reconciliation would end in a traceback.
8. Found by reading only: replay does not check `attach:` refs the way a live
   write does.

```
=== VERDICT ===
task: TASK-489
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-489-spec.md
checked: Perry — importer run on a scratch copy of perry/ and .perry/ (inputs byte-identical at 9509170c/8649b63b/da9d6066) into a fresh store; SkyTonight — importer run on the real root (read-only; path+size+mtime and state-byte fingerprint identical before and after) and on a copy; both live-store paths absent before and after every run. Independent checks per project: old files via json.loads versus the kernel through bin/perry-kernel --store/--root — counts per type and state; every id resolves, with field/state/type/edge/attachment fidelity; next ids by dry-run item create versus ids issued (id, task and record.id keys scanned); second import, init-only and dry-run imports refused; export unchanged, fresh re-import and re-export byte-identical; independent Dates-rule recomputation of all create and move times; independent counts of skipped, dropped and unset cells. About 20 adversarial scratch projects (blank idioms, cycle, punctuation in blocks cells, risk words, ceiling keys, clamp, long cells, enum whitespace, duplicate/short/4-digit ids, cadence row, dangling and non-task edges, status whitespace, answered mismatch), plus the old writer perry-task on a scratch project, live export/import round trips, F1/F3/F6 probes, a leftover store after a refused import, re-run and --work guards. Mutants (25; targeted modules then the affected tier after each; pycache cleared and a 1.2 s wait; each restore verified with bin/perry-restore-check against 8649b63b): M1–M7, M10, M11 and K1–K14 killed; M8 and M9 (importer's criterion 3 and 5 self-checks) survived, tier green. Baseline affected tier: 160 modules, 4524 tests, green.
not-checked: the slow tier (4 held-back modules), the full untiered bash tests/run, git diff --check; the importer against the live main checkout /Users/bytedance/proj/Perry (a byte-identical copy was used); behaviour under another machine timezone; an intake-row stop with a reader-valid intake record (covered only by mutant M5 and the author's test); the attach-ref replay gap (by reading only); whether perry-task accepts blank idioms for title, ask needed or risk text (proven only for next action and summary; the evidence writer refused n/a); documentation beyond bin/README.md and the kernel § 5 diff; concurrent importer runs.
proof: bin/perry-kernel-migrate:119-124 — blank() delegates to lib.is_blank_cell, which treats schema § i18n.blank_cell's spellings (- – n/a na none tbd ? N.A. TBA 无 待定 不适用 暂无 ？, case- and decoration-insensitive) as unset — applied at :226-231 in Plan.add to every mapped field. Input: an open task whose next action was set with `bin/perry-task next <id> --next "TBD"` (also "none", "?", "n/a", "待定", "-"; and `perry-task summary <id> --summary` with the same values), accepted by the old writer with exit 0 and stored verbatim, is imported with next_action/summary null (scratch project: TASK-002 not_started "TBD" became null, TASK-003 in_progress "None" became null; importer exit 0, reconciled). Spec § Decided 2026-09-29: only the blank marker `—` and an empty string are unset, and an open task's next_action "is imported as it is". Criteria 1–5 themselves PASS on both projects: Perry — counts equal (task 18/2/1/2/321/144, ask 3/104, risk 2/2); 599/599 ids resolve with exact field fidelity, 251/251 edges; next ids TASK-495>494, USER-1007>1006, RX-005>4; second import refused store_not_empty; export unchanged and re-import byte-identical. SkyTonight — counts equal (task 31/1, risk 2); 34/34 ids, 40/40 edges; next ids TASK-033>32, USER-001, RX-003>2; refused store_not_empty; replay byte-identical.
=== END VERDICT ===
```

## Architecture review — PASS

**Triggers.** "New bin executable" and "module architecture edit" are true,
and the other four are false. The kernel's `describe` output is byte-identical
at base and head, and `surface` stays 1.0.

**The author's seven points.** The reviewer held all seven against the
architecture:
1. The events read goes through an existing `viewer/parsers.py` function, so
   it is not a second reader.
2. `PERRY_KERNEL_TESTING` is a declared public input.
3. Running `bin/perry-kernel` is a subprocess, not an import.
4. Root counts are stale: there are 22 tools, not 21, and 164 test modules,
   not 163. Root text is the user's.
5. OQ-B1 says "Six" `SURFACE` declarations. It is now seven, and the text is
   the user's.
6. Commit 1923203e is inside the user's 2026-09-25 decision. DESIGN-023 § 7's
   rule covers kernel changes driven by a method rule, so it is not touched.
7. The synthetic export is loaded only by kernel `import`.

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: fresh-context architecture reviewer (subagent, isolated worktree agent-a29e51226aeac4f59), not the task author; timestamp: 2026-09-29 17:14 +0800
Base: 9509170c78ef47d4c0ee907f0b71e7a2df2f2dbc
Head: 8649b63bd114fa13d3642cf2b47239cfeb09e28c
Triggers: (1) boundary paths false — no viewer/parsers.py, bin/lib/, schema/, SKILL.md in --name-status; (2) new top-level dir false — ls-tree top level identical; (3) new bin executable true — bin/perry-kernel-migrate :000000→100755, bin now 22 executables (21 at base); (4) contract-version change false — kernel surface.py not in diff, `perry-kernel describe` byte-identical base vs head, surface "1.0", last release record 2026-09-23 predates the kernel (unreleased); F6 moves a damaged token to store_corrupt, a case §5.1 already documented ("a row cannot be read back"); the new replay refusals use export_invalid, already in import's declared errors; the new tool's own bin SURFACE is a per-tool declaration under root §5:229-237; root §5 unchanged; (5) root architecture edit false; (6) module architecture edit true — bin/ARCHITECTURE.md, kernel/ARCHITECTURE.md, kernel/architecture/sections/§5-contracts.md
Context: root §1 (43-56), §3 (154-182), §6 (256-320) read in full; §2 and §5 on demand. Mapping: bin/perry-kernel-migrate, bin/README.md → bin/ (bin/ARCHITECTURE.md); tests/test_bin_* are in tests/ by path (root :145-148, no module document) and carry bin NN-B2's check (bin :204), so reviewed against bin rules too; kernel/** → kernel/ARCHITECTURE.md + §5-contracts.md; tests/test_kernel_migrate.py, tests/durations.json → tests/ (no module document, not missing per root §7 OQ-2); perry/evidence → project state. Module docs read at both SHAs. Also read at da9d6066: TASK-489-spec.md, DESIGN-023 §2-§9, TASK-487-review-round3.md, TASK-488-review-round2.md; spec history 79aac6dc (user, 2026-09-25) and 999ca0ed (PMO routing of F1-F6). Unresolved facts: none.
Rules:
- ARCHITECTURE.md:45-56 (§1 scope) — holds — no service; the scratch store is caller-named, temporary and required by the spec's Bound; no registry; the project is never written (test fingerprint)
- ARCHITECTURE.md:172-173 (allowed directions) — holds — the importer imports lib, parsers, perry_store; parsers unchanged
- ARCHITECTURE.md:176 (second reader) — holds — stores via perry_store.load_board_stores, events via parsers.load_register_store, state root via parsers.resolve_state_root, statuses via parsers.ask_is_answered/status_is_cleared; no parse re-implemented; perry.json is not a state file
- ARCHITECTURE.md:177-178 (lane computing) — not touched — no lane changed
- ARCHITECTURE.md:179-181 (tool reaching another project, and its sunset) — holds — lib.resolve_project_root (perry-kernel-migrate:841); kernel always gets an explicit --root <work>/anchor; the sunset copy list is unaffected
- ARCHITECTURE.md:182 (agent writing this file) — holds — root not edited; the stale counts are left for the user
- ARCHITECTURE.md:258-272 (NN-1 and sunset) — holds — see :176; successor clause holds: the importer never opens the store or reads the export
- ARCHITECTURE.md:274-284 (NN-2 and sunset) — holds — old records stay truth; the synthetic export is an input to import, verified by export `unchanged`; no board file touched
- ARCHITECTURE.md:286-292 (NN-3) — holds — plan-only writes nothing and says so; exit 1 when not reconciled; refusals happen before --work is created (tests assert)
- ARCHITECTURE.md:294-301 (NN-4) — holds — mapping, splitting and time rules are mechanical and reported
- ARCHITECTURE.md:303-308 (NN-5) — holds — tests use mkdtemp; 35/35 passed on a copy
- ARCHITECTURE.md:310-320 (NN-6) — holds — no edit to root; bin §6/§7 unedited; OQ-B1 deferred to the user
- bin/ARCHITECTURE.md:122-128 (tool never parses a state file) — holds — as root :176
- bin/ARCHITECTURE.md:129-131 (tool never imports another tool) — holds — perry-kernel is run as a subprocess (perry-kernel-migrate:558-569), not imported
- bin/ARCHITECTURE.md:132 (lib imports no tool) — not touched — lib unchanged
- bin/ARCHITECTURE.md:133-134 (lock spans the write) — not touched — no project write
- bin/ARCHITECTURE.md:190-194 (NN-B1) — holds — lib.parse_surface; `--work <scratch> --help` exit 0, nothing created
- bin/ARCHITECTURE.md:196-204 (NN-B2) — holds — SURFACE plus parse_surface; test_bin_surface 62 OK; argument-contract lists updated
- bin/ARCHITECTURE.md:206-232 (NN-B3 and sunset) — holds — the one resolver; no new copy
- bin/ARCHITECTURE.md:234-240 (NN-B4) — holds — usage first; the argument is in README § The argument, per tool (:828)
- kernel/ARCHITECTURE.md:82 (allowed directions skill → kernel → store) — holds — the importer reaches the store only through the CLI; §5-contracts.md:307-309 anticipates row D's importer; descriptive gap noted
- kernel/ARCHITECTURE.md:85-86 (stdlib only, no markdown) — holds — no import lines changed
- kernel/ARCHITECTURE.md:87-89 (runs no command) — holds — no subprocess or exec in kernel/perry_kernel
- kernel/ARCHITECTURE.md:90-92 (no template-declared names) — holds — the Goal 1 tests (test_vocabulary, test_work_template) pass in the 271-test run
- kernel/ARCHITECTURE.md:93-95 (other paths; only import loads the export) — holds — the kernel reads the export only in import/export
- kernel/ARCHITECTURE.md:136-197 (NN-K1..K10) — hold — K1/K2 as above; K5 both flags passed and env stripped; K6 new refusals are KernelError envelopes; K8 F1 refuses no-op relation replays for every kind; K9 live store absent; K3/K4/K7/K10 not touched
- §5-contracts.md:42, :63, :256-259, :298-303, :341-353 — hold — docs match commands.py replay_check/recorded_token and store.py open/_apply_change; no version bump required under §5.6
- DESIGN-023 §7:456 (new concept/command group/guard kind) — not touched — describe identical; budget tests pass
- DESIGN-023 §7:457 (kernel change for a method rule needs the user in a revision) — not touched — scoped to method rules the template cannot express; these changes rest on the user's 2026-09-25 decision (template-in-force checks, including 1923203e) and on row B's V4 findings F1-F4 and F6, which align code with §5.1 store_corrupt, §5.7's 5 s and NN-K8
Decision: PASS — contradictions: none; missing context: none
User decision required: none for a rule. The user must confirm descriptive corrections to text they own (root :182; bin header :3): ARCHITECTURE.md:61 and :160 (21→22 tools), :145 and :165 (163→164 test modules), bin/ARCHITECTURE.md:244 OQ-B1 ("Six"→"Seven"). If the user reads DESIGN-023 §7:457 as covering every kernel change, F1's widening to every kind, F4's code change, F6 and 1923203e have no recorded user approval — optional confirmation, not a gate.
Not checked: bash tests/run, --tier affected, tests/merge-check; tests/test_bin_argument_contract.py (not run); the md-free kernel run; perry-lint architecture modes; running the importer on the real Perry/SkyTonight stores (evidence taken as written); mutants (V4's job); Linux, and other Python or SQLite versions; the user's in-session decisions (taken from the spec and commits 79aac6dc, 9509170c, da9d6066); whether decision 13's mapping is right
=== END COMPLIANCE ===
```

**Descriptive drift the reviewer reported** (none blocks):
- **Root counts.** `ARCHITECTURE.md:61` and `:160` should read 22 tools, and
  `:145` and `:165` should read 164 test modules. The text is the user's.
- **OQ-B1.** `bin/ARCHITECTURE.md:244` should read "Seven". The text is the
  user's.
- **`bin/README.md:838`** calls `load_register_store` the one JSONL reader in
  `viewer/parsers.py`. It is not the only one.
- **`bin/ARCHITECTURE.md:83–86`** leaves out that the importer reads
  `templates/process/perry.json`.
- **`kernel/ARCHITECTURE.md:74–82`** names only the skill as a caller of the
  kernel CLI.
- **`§5-contracts.md:314–319`** describes `PERRY_KERNEL_TESTING` as the test
  harness's variable. The importer sets it too.
- **Older gaps.** `bin/ARCHITECTURE.md:122–128` does not list the two existing
  `read_events` readers. This predates the candidate.

## Where the findings go

**Round 3 of TASK-489.** The PMO decided these on 2026-10-07 and recorded them
in the spec's § Round 3:
- the FAIL and findings 1–4, 7 and 8;
- finding 5. The importer lists the three KR edges for TASK-492, which must
  restore them once key results are kernel items;
- the two surviving mutants;
- the four drift items in this candidate's own module documents.

**TASK-490.**
- The root counts and OQ-B1. They are the user's text, and the user is asked
  to confirm them.
- The `read_events` gap, which predates the candidate.

**Recorded only.** Finding 6 is the documented `lib.ts_moment` rule.
