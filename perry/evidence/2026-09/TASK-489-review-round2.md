# TASK-489 — review round 2: V4 FAIL on 91e1ff5e; architecture BLOCKED on 91e1ff5e, then PASS on befe556c

Criteria: `TASK-489-spec.md` (main). Three fresh-context reviewers ran, each
in its own isolated worktree. None of them wrote the importer. Each reported
that `/Users/bytedance/proj/Perry/.git/perry` and
`/Users/bytedance/proj/SkyTonight/.git/perry` were absent before and after its
runs.

## V4 review round 2 — FAIL, on `91e1ff5e` (round 3's head)

This is TASK-489's second V4 FAIL. Under `work/reference/review.md` § 6, the
next step is the user's decision, not a third round run automatically.

**Criteria 1–5 hold for both projects.** The reviewer re-derived them with
Python 3.11, outside the importer's own report.
- This repository: 599 of 599 ids, with exact fields, including 104 answers
  and 2 reasons. There are 74 attachments and 251 of 251 edges.
- SkyTonight: 34 of 34 ids and 40 edges.
- The `items.jsonl` hashes match the author's.

**Two behaviours FAIL.**
1. **Kernel replay order.** `kernel/perry_kernel/commands.py:1213–1215` skips
   the field check while an item has no type yet. `store.py:610–618` writes the
   value anyway, and a later `type` change in the same event creates the item.
   So a field change placed before `type` replays unchecked. The reviewer's
   examples were an enum value of `P9`, an undeclared field and an integer
   question. Each was refused when placed after `type`. The spec's carried
   item asks for this gap to be closed. **It is not fixed at `befe556c`.**
2. **Key-result forms.** The importer recognised only the phase form
   `P003-O2-KR3`. `perry-task ask --blocks O3-KR4` is accepted by the old
   writer, and the importer then failed closed. **Round 4 fixed this at
   `befe556c`**: it now uses the schema's declared KR id pattern.

**Mutants.** The reviewer ran 43, and 3 survived: M18–M20. The importer's own
checks for criteria 1, 2 and 4 can be forced true, and every test stays green.

**Findings that are not a FAIL.**
- A replayed `state_root` change is accepted.
- `event_ids` reads a multi-id `task` value as one id. This has no effect
  today.
- A self-edge is dropped and appears only in the JSON output.
- An answer of `—` is imported as text.
- Documents:
  - § 5.8 step 2 overclaims;
  - the README's KR wording is too narrow;
  - `kernel/ARCHITECTURE.md`'s "There are no others" (round 4 changed it).

```
=== VERDICT ===
task: TASK-489
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-489-spec.md
checked: All runs used /Users/bytedance/.local/bin/python3.11, and the tier ran with it first on PATH. Perry: the importer ran on a copy of perry/ and .perry/ (sha256 identical to the report and to 9509170c/801ada10) into a fresh --work under my scratch directory. A code copy (git archive 91e1ff5e) also ran it on the live root; perry/ and .perry/ fingerprints were the same before and after. SkyTonight: the importer ran on a copy and on the real root. The whole-tree path+size+mtime and state-byte fingerprint was the same before, after and at the end (entries=11776 listing=cc1ffb46 state=66806604). Both live-store paths were absent before and after. The independent check (verify.py) reads the old files with json.loads and the store only through bin/perry-kernel. It checks counts per type and state; every id via query and item get; field fidelity including answer and reason; state, attachments and edges; create and move times recomputed by the Dates rule; next ids by item create --dry-run against id, task and record.id, and against any full id under any key of any old event; a second import and a dry-run import refused; export unchanged; a fresh re-import and re-export byte-identical. The report's secondary counts (skipped next actions, dropped fields, creation sources, late asked dates, link events) were re-derived. Adversarial scratch projects (15, plus the old writer perry-task ask --blocks O3-KR4) and crafted exports (field before type x3, state_root change). Mutants: 43, each anchored by line number, __pycache__ cleared and a 1.2 s wait, the targeted module (tests.test_kernel_migrate or kernel/tests/run.py) then the affected tier, each restore checked by bin/perry-restore-check against 91e1ff5e and by bytes against git show. Importer M1-M17, M21, M22 and kernel K1-K21 (replay checks, template in force, F1, F2, F3, F4 x3, F6) killed; M18, M19, M20 survived. The affected tier was green before and after: 160 modules, 4539 tests. git diff --check is clean.
not-checked: the full untiered bash tests/run, the slow tier (4 held-back modules) and tests/merge-check; the default python3 3.9.6; another machine timezone (zoneless ts is read as local time); concurrent importer runs; replay ordering cases beyond field, state, attach and rel before or after type within one event; documents outside round 3 item 9 and the § 5.7/5.8 diff; a repeat of the architecture review; whether TASK-492 intends to cover overall-form KR ids.
proof: kernel/perry_kernel/commands.py:1213-1215 ("item_type = store.item_type(primary) ...; if item_type is None: return") skips the field check for an item not yet typed, and kernel/perry_kernel/store.py:610-618 writes the value row anyway; the later type change in the same event creates the item. Input: a copy of the SkyTonight export the importer wrote, with TASK-001's create event listing {"key":"field:priority","before":null,"after":"P9"} before its type change and items.jsonl to match. perry-kernel import gives ok and verified, and item get TASK-001 gives priority "P9". Control: the same value after type gives export_invalid ("P9" is not one of P0, P1, P2). The same holds for an undeclared field "bogus" and for an ask question of 42 on the Perry export. Spec "Carried from TASK-487": close the gap where import does not check replayed field values against the template in force. Second behaviour: bin/perry-kernel-migrate:458 (P.kr_objective_id, phase form only, viewer/parsers.py:4568). Input: perry-task ask --needed "..." --blocks O3-KR4 (exit 0, stored verbatim), then the importer exits 1 "NOT reconciled", with O3-KR4 unresolved and nothing for TASK-492, against spec § Round 3 item 4 ("The one exception is a key-result id"). Criteria 1-5 themselves PASS. Perry: counts equal (task 18/2/1/2/321/144, ask 3/104, risk 2/2); 599/599 ids with exact fields (104 answers, 2 reasons), 74 attachments, 251/251 edges, 0 time mismatches; next TASK-495>494, USER-1007>1006, RX-005>4; store_not_empty twice; export unchanged; fresh re-import identical; items sha256 a516bd22. SkyTonight: counts equal (task 31/1, risk 2); 34/34 ids, 40 edges; next TASK-033>32, USER-001, RX-003>2; refused; replay identical; items sha256 a8ce77e9.
=== END VERDICT ===
```

## Architecture review round 2 — BLOCKED, on `91e1ff5e`

**The block.** The importer's own `REFERENCE_SPLIT` re-implemented a split
that `perry-task` already does. That contradicts two lines the user decided:
- root `ARCHITECTURE.md` § 3:176, "`bin/` never re-implements a parse";
- NN-1.

**The user's answer.** On 2026-10-07 the user chose option B: the importer
holds no split of its own, and no exception is recorded. This is spec
§ Round 4. The full COMPLIANCE block is in the session transcript.

## Architecture review round 3 — PASS, on `befe556c` (round 4's head)

The block is verbatim:

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: independent architecture reviewer, fresh-context subagent, not the task author, given no author compliance verdict; timestamp: 2026-10-07T14:57:45Z
Base: 9509170c78ef47d4c0ee907f0b71e7a2df2f2dbc
Head: befe556c3e67c5c507cf9543d9785efae405d730
Triggers:
- Listed boundary paths: false. `--name-status` touches no `viewer/parsers.py`, `bin/lib/`, `schema/`, `SKILL.md`, `goals/`, `work/` or `decide/`.
- New top-level directory: false. The top-level `ls-tree` is identical at base and head.
- New bin executable: true. `A bin/perry-kernel-migrate`, mode 000000 → 100755.
- Contract-version change: false. Kernel `describe` is byte-identical at base and head (21,403 bytes, `cmp`), with `surface` 1.0. No `schema/*-contract.md` changed. `perry-task` (`perry-asks/list/1.4`) is unchanged. Root § 5 is unchanged.
- Root architecture edit: false. `ARCHITECTURE.md` is not in the diff.
- Module architecture edit: true. `bin/ARCHITECTURE.md`, `kernel/ARCHITECTURE.md` and `kernel/architecture/sections/§5-contracts.md` changed.
Context:
- Root sections read at base: § 1 (43–57), § 2 (58–153, for the mapping), § 3 (154–183), § 5 (227–255) and § 6 (256–321).
- Mapping: `bin/**` maps to `bin/ARCHITECTURE.md`. `kernel/**` maps to `kernel/ARCHITECTURE.md` and its § 5 file. `tests/` has no module document, and root § 2:145–148 declares none. `perry/evidence/` is project state.
- Also read: the TASK-489 spec (round 4 decision) and DESIGN-023 Goal 1, § 3, decision 13, § 6 row D and § 7, all at `a95fc07f`.
- Unresolved facts: none.
Rules:
- ARCHITECTURE.md:45–56 (§ 1) — holds — stdlib only; the importer writes only under `--work`; the temp lock file is existing `perry-task` behaviour, not a registry; a recovery write finishes an earlier requested command.
- ARCHITECTURE.md:172–173 (allowed directions) — holds — the importer imports `lib`, `parsers` and `perry_store`; `parsers` is unchanged.
- ARCHITECTURE.md:176 (Forbidden: a second reader) — holds — `REFERENCE_SPLIT` is gone, and the enumeration in (a) finds no split.
- ARCHITECTURE.md:177–178 (Forbidden: a lane computes a number) — not touched.
- ARCHITECTURE.md:179–181 (Forbidden: a tool reaches another project) — holds — `lib.resolve_project_root`; the importer passes `--root` and strips `PERRY_PROJECT` and `PERRY_STORE` from both subprocesses.
- ARCHITECTURE.md:182 (Forbidden: an agent writes `ARCHITECTURE.md`) — holds — the root file is not in the diff.
- ARCHITECTURE.md:229–237 (§ 5, `bin/` → agent) — holds — the importer declares `SURFACE`, uses exits 0/1/2, and prints a JSON refusal with `--json`.
- ARCHITECTURE.md:258–272 (NN-1) — holds — every state-file read goes through `parsers`, `perry_store` or the published `blocks_ids`; the key-result pattern is declared schema data, the same practice as `perry-goals:4175`.
- ARCHITECTURE.md:274–284 (NN-2) — holds — no `BOARD.md` is read, and the export and store go only into a scratch anchor.
- ARCHITECTURE.md:286–292 (NN-3) — holds — a read that changed the project gives exit 1 and names the file (verified on a scratch copy).
- ARCHITECTURE.md:294–301 (NN-4) — holds — mechanical rules only.
- ARCHITECTURE.md:303–308 (NN-5) — holds — three `bin/` test modules left a scratch copy unchanged; the new tests use `mkdtemp` roots.
- ARCHITECTURE.md:310–320 (NN-6) — holds — no root edit; `bin` § 6 and § 7 unchanged; no NN-K* deleted.
- bin/ARCHITECTURE.md:144–150 (a tool never parses a state file) — holds — as NN-1.
- bin/ARCHITECTURE.md:151–153 (a tool never imports another) — holds — `perry-task` and `perry-kernel` run as subprocesses; precedent at base.
- bin/ARCHITECTURE.md:154 (`lib` imports no tool) — not touched.
- bin/ARCHITECTURE.md:155–156 (the lock spans read, decision and write) — not touched — the importer writes nothing in the project.
- NN-B1 :212–216 — holds — help is handled first in `main`; `test_bin_argument_contract` passes with the count at 15.
- NN-B2 :218–226 — holds — `lib.parse_surface`; `test_bin_surface` declares seven tools; passed.
- NN-B3 :228–254 — holds — `lib.resolve_project_root`.
- NN-B4 :256–262 — holds — usage comes first, and the reasoning is in `bin/README.md § perry-kernel-migrate`.
- kernel/ARCHITECTURE.md:92–93 (allowed directions) — holds — callers → CLI → store; the kernel calls nothing back.
- kernel/ARCHITECTURE.md:95–106 (Forbidden) — holds — no new import, process or path in `commands.py` or `store.py`; `test_boundaries` and `test_vocabulary` passed.
- NN-K1 :147–151 and NN-K2 :153–157 — hold — kernel suite passed.
- NN-K3 :159–163, NN-K5 :175–179 and NN-K7 :188–191 — not touched.
- NN-K4 :165–173 — holds — a replayed change gives `export_invalid` and is never accepted.
- NN-K6 :181–186 — holds — refusals are `KernelError` envelopes.
- NN-K8 :193–197 — holds — a replayed relation change that flips nothing is refused.
- NN-K9 :199–202 — holds — the live store was absent before and after the suite.
- NN-K10 :204–208 — holds — no ceiling is lowered.
- §5-contracts.md 5.1, 5.7 and 5.8 — holds — wording only; no new code or key; `surface` 1.0.
Decision: PASS — no contradictions and no missing context. Correct drift item 1 in the next change; it is not blocking, because the same subsection gives the stop condition and the README gives the cause.
User decision required: none for architecture. For V4 or the user: does the schema-declared pattern satisfy spec round 4, item 3 ("stop and report")? Is the residual recovery write acceptable under the spec's Bound?
Not checked:
- the full `bash tests/run`, `git diff --check` and `tests/merge-check`;
- a SkyTonight import (I ran only on a scratch copy of this repository);
- V4 scoring of the acceptance criteria;
- the ceiling rule (`id`, `task`, `record.id`) against `perry-task`'s own minting (`perry-task:1711–1792`, which also reads journal text) — this is for V4, not NN-1;
- the content of the evidence reports;
- mutation testing;
- round 1–3 kernel correctness beyond the boundary rules.
=== END COMPLIANCE ===
```

**The PMO's answers to the reviewer's two questions** (2026-10-07):
- **The KR pattern.** The id pattern `schema/state-schema.json` declares for a
  `kr` record counts as an existing reader under round 4, item 3.
  `perry-goals` reads the same pattern the same way. Nothing restates the
  grammar.
- **The residual recovery write.** A pending `perry-task` recovery marker can
  be completed by the `perry-task asks` read. The write finishes an earlier,
  requested command. The importer detects it, stops and names the file.
  Neither project holds a marker, and SkyTonight has no ask, so `perry-task`
  never runs there. The wording "it never writes the project" is corrected in
  the next change, per drift item 1.

## Where this stands

- **Open, for the user (`review.md` § 6, two FAILs):**
  - the kernel replay-order gap, which is FAIL 1;
  - the importer self-check mutants M18–M20.
- **Already fixed at `befe556c`:** FAIL 2.
- **Owed in the next change:**
  - drift item 1 from the round-3 architecture review;
  - the V4 documentation findings: § 5.8 step 2 and the README's KR wording.
