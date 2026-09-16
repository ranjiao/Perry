# TASK-448 — the replay: 50 merges through the `COVERS` selector

> Design: `DESIGN-021 § 6` phase A, the gate · Spec: `TASK-448-spec.md` deliverable 5
> Branch: `coding/task-448-covers-and-replay` · round 2 after `USER-940` (2026-09-16)

## Verdict, both rounds

| | round 1 (`e76cb084`) | round 2 (after `USER-940`) |
|---|---|---|
| **median share** | **100.0%** | **75.9%** |
| mean share | 75.1% | 67.9% |
| merges that widen to `full` | 30 of 50 | 23 of 50 |
| `tests/` helper fired | 27 merges | 19 merges |
| `schema/` fired | 10 merges | 10 merges |
| `bin/lib/` fired | 9 merges | 9 merges |
| `viewer/parsers.py` fired | 8 merges | 8 merges |
| evidence-only floor | 32 modules · 33.7% | 27 modules · 31.6% |
| verdict | **FAIL** | **FAIL** |

**Still FAIL.** The gate is a median of 50% or less. The two levers `USER-940`
pulled are worth 24.1 points of median between them, and the remaining 25.9 sit
mostly in one place: the modules that read this repository's own state root,
which the user has explicitly not decided yet.

Round 1's per-merge table is in this file's previous revision (`e76cb084`); the
summary rows above carry everything it said about the totals.

## What changed between the rounds

1. **`tests/durations.json` is no longer a `tests/` helper** (`USER-940` 1). It
   is matched through `COVERS`, where `test_durations_provenance`,
   `test_parallel_runner` and `test_slow_selector` declare it. It had widened 20
   of the 50 merges on its own. `tests/selection.py § STOPWATCH` carries the
   reason; every other path under `tests/` is still a helper.
2. **Seven modules that declared `perry/` or `.perry/` wholesale now declare the
   files they read** (`USER-940` 2): `test_asks_list`,
   `test_board_from_declarations`, `test_board_less_reads_and_writes`,
   `test_board_names_its_sources`, `test_live_state_expectations`, `test_risks`
   and `test_task_writer_core`. **Twenty-six kept the broad declaration**, and
   that set is listed below: each one reads the whole state root, not a file of
   it.
3. Main merged in: `test_architecture_rules.py` (TASK-453) declares
   `ARCHITECTURE.md`, `bin/`, `viewer/` and `tests/run`. The suite is 145
   modules, 1,056.4 module-seconds.

## Method (unchanged from round 1 except where noted)

- **Enumeration.** `git log --merges --first-parent -50 --format=%H bb178072`.
  Size 50. Last element: row 50, `59e90e61` (2026-09-07). The base is the same
  commit as in round 1, so the two rounds replay the same 50 merges.
- **Changed paths.** `git diff --name-only --no-renames M^1 M` per merge.
- **Selector.** `tests/selection.py § select` against the declarations in the
  working tree, not the modules as they stood at each merge.
- **Share.** Selected module-seconds ÷ suite module-seconds from
  `tests/durations.json`, read through `tests/parallel § load_durations`: 1,056.4 s
  over 145 modules, the three unmeasured counting 0.
- **Reproduce.** `python3 tests/selection.py --replay 50 --base bb178072`.

## Per merge — the selector's own output, round 2

| # | merge | date | subject | paths | modules | share | widening rule (paths) |
|---|---|---|---|---|---|---|---|
| 1 | `de4dc685` | 2026-09-15 | Merge TASK-441: six live-phase test modules measure a copy with pha... | 9 | 145 | 100.0% | tests/ helper (1) |
| 2 | `8489a2c8` | 2026-09-15 | Merge TASK-262 round 4b: no reader other than the imports reads a h... | 74 | 145 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); schema/ (4); tests/ helper (23) |
| 3 | `80ef880b` | 2026-09-15 | Merge TASK-262 round 4a: perry-task writes never read or rewrite a ... | 44 | 145 | 100.0% | bin/lib/ (1); schema/ (1); tests/ helper (1) |
| 4 | `942d7749` | 2026-09-15 | Merge TASK-262 round 3 result: stopped on contract pins, nothing im... | 1 | 27 | 31.6% | — |
| 5 | `f53b10b9` | 2026-09-15 | Merge fix/hidden-reds-and-waits: two reds hidden behind --slow, two... | 4 | 10 | 15.8% | — |
| 6 | `282e6acb` | 2026-09-15 | Merge TASK-262 round 2: perry-task SURFACE writes names what each w... | 6 | 97 | 74.4% | — |
| 7 | `ddf60594` | 2026-09-15 | Merge TASK-262 round 1: perry-tasks board names each section's stor... | 9 | 145 | 100.0% | tests/ helper (1) |
| 8 | `5c790cff` | 2026-09-14 | Merge TASK-237 round 2 V4 review: PASS | 1 | 27 | 31.6% | — |
| 9 | `80c8eeb1` | 2026-09-14 | Merge TASK-335: the parity anti-vacuity tests read one frozen copy | 3 | 33 | 36.7% | — |
| 10 | `7523f1fe` | 2026-09-14 | Merge TASK-237 round 2: a write refuses where nothing is installed;... | 20 | 145 | 100.0% | bin/lib/ (1); schema/ (1) |
| 11 | `13522369` | 2026-09-14 | Merge TASK-237 3d: the V5-signed hand-off contract, the git-boundar... | 22 | 68 | 52.8% | — |
| 12 | `0f1ed007` | 2026-09-14 | Merge TASK-237 3c: BOARD.md is deleted; installed needs .perry/; a ... | 72 | 145 | 100.0% | viewer/parsers.py (1); schema/ (8); tests/ helper (4) |
| 13 | `0ec65094` | 2026-09-14 | Merge TASK-237 3b-prime: starts write the config store first; one i... | 56 | 145 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); schema/ (7); tests/ helper (2) |
| 14 | `161c927c` | 2026-09-14 | Merge TASK-237 3b (partial): cadence store, board title and prose, ... | 22 | 145 | 100.0% | viewer/parsers.py (1); schema/ (1); tests/ helper (1) |
| 15 | `47dce04a` | 2026-09-14 | Merge TASK-237 3a: reads answer from their stores, and writes land ... | 17 | 145 | 100.0% | viewer/parsers.py (1); schema/ (2); tests/ helper (1) |
| 16 | `cb88d848` | 2026-09-14 | Merge TASK-237 D1: perry-tasks board prints the whole board from th... | 8 | 102 | 77.5% | — |
| 17 | `9549626e` | 2026-09-14 | Merge TASK-237 D1+D2: the board-less project is recognised; byte-id... | 6 | 145 | 100.0% | tests/ helper (1) |
| 18 | `c7618a96` | 2026-09-12 | Merge TASK-439: `perry-task add` refuses a row that answers the KR ... | 11 | 107 | 79.0% | — |
| 19 | `4babb645` | 2026-09-12 | Merge TASK-430: 58 modules that silently reported a clean pass, and... | 6 | 145 | 100.0% | tests/ helper (3) |
| 20 | `687579bd` | 2026-09-12 | Merge TASK-236: OKR.md's 38 KR rows come out, and the byte gate is ... | 11 | 145 | 100.0% | tests/ helper (1) |
| 21 | `fe9b922e` | 2026-09-11 | Merge v4-round-411-412-419-431: four PASSes, and one green that sho... | 1 | 27 | 31.6% | — |
| 22 | `7c89ad05` | 2026-09-11 | Merge v4-review-348-368-421: three PASSes, and a finding aimed at t... | 1 | 27 | 31.6% | — |
| 23 | `cf3611ec` | 2026-09-11 | Merge TASK-437: one wrong-root call site, and the reason it was inv... | 4 | 65 | 51.5% | — |
| 24 | `076ae21a` | 2026-09-11 | Merge spec-437 | 1 | 27 | 31.6% | — |
| 25 | `ce9041f0` | 2026-09-11 | Merge evidence-411: TASK-411's measurements, which existed only in ... | 1 | 27 | 31.6% | — |
| 26 | `9c30782a` | 2026-09-11 | Merge task-436-diagnose-dangling: one of four paths closed, and the... | 4 | 55 | 44.5% | — |
| 27 | `b5b7d023` | 2026-09-11 | Merge task-419-review-rounds-criteria: the exhaustion counter reads... | 5 | 89 | 66.4% | — |
| 28 | `6affdd38` | 2026-09-11 | Merge task-412-contract-snippets: three defects in a snippet nothin... | 3 | 145 | 100.0% | schema/ (1) |
| 29 | `89617487` | 2026-09-11 | Merge task-431-blank-cell: one blank-cell rule, nine sites not three | 13 | 145 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); tests/ helper (4) |
| 30 | `575f9dee` | 2026-09-11 | Merge task-421-scratch-collisions | 7 | 47 | 42.0% | — |
| 31 | `fef35967` | 2026-09-11 | Merge task-368-inproc-slice-1 | 10 | 145 | 100.0% | tests/ helper (1) |
| 32 | `292bce3e` | 2026-09-11 | Merge worktree-agent-afe8ae683f09b6754 | 1 | 27 | 31.6% | — |
| 33 | `4efc810f` | 2026-09-11 | Merge task-362-round11-review | 1 | 27 | 31.6% | — |
| 34 | `70458893` | 2026-09-11 | Merge specs-five-spinouts: specs for TASK-412, 419, 421, 431 and 436 | 5 | 27 | 31.6% | — |
| 35 | `fe0292fb` | 2026-09-11 | Merge evidence/task-239-result | 1 | 27 | 31.6% | — |
| 36 | `899f3ffd` | 2026-09-11 | Merge review/task-400-v4-round1 | 1 | 27 | 31.6% | — |
| 37 | `8e81e5ee` | 2026-09-11 | Merge task-426-restore-check | 2 | 20 | 17.4% | — |
| 38 | `1632095d` | 2026-09-11 | Merge task-411-declaration-both-ways | 2 | 145 | 100.0% | tests/ helper (1) |
| 39 | `7f43a11c` | 2026-09-11 | Merge task-362-blank-rung: done stamped a verification its own vali... | 3 | 83 | 56.4% | — |
| 40 | `ee3f46f6` | 2026-09-11 | Merge specs-348-368: specs for TASK-348 and TASK-368 | 2 | 27 | 31.6% | — |
| 41 | `583f024f` | 2026-09-11 | Merge bin-contract-phase-a: DESIGN-016's thirteen closed rows, and ... | 89 | 145 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); schema/ (3); tests/ helper (3) |
| 42 | `4ebc0693` | 2026-09-09 | Merge suite-cost-round3: TASK-400 to review, TASK-402 closed, DESIG... | 25 | 145 | 100.0% | tests/ helper (4) |
| 43 | `f2016f12` | 2026-09-08 | Merge suite-cost-round2: one shared helper, 21 modules, CPU 1278s t... | 2 | 145 | 100.0% | tests/ helper (1) |
| 44 | `fa2df316` | 2026-09-08 | Merge drop-projected-markdown: ADR-019, and four cuts at the suite'... | 137 | 145 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); schema/ (4); tests/ helper (25) |
| 45 | `724f91a5` | 2026-09-07 | Merge TASK-394: add --unlinked writes the declaration, and the KR d... | 8 | 145 | 100.0% | bin/lib/ (1) |
| 46 | `26bcec72` | 2026-09-07 | Merge TASK-281 round 2: whitespace no longer inflates the KR, and t... | 4 | 145 | 100.0% | bin/lib/ (1) |
| 47 | `883d9d26` | 2026-09-07 | Merge ADR-017 step 3: 27 of 79 renamed, 52 deliberately left | 13 | 145 | 100.0% | tests/ helper (3) |
| 48 | `51c32095` | 2026-09-07 | Merge ADR-017 step 2: one grammar at both levels, in one commit | 21 | 37 | 38.8% | — |
| 49 | `4e88cd52` | 2026-09-07 | Merge TASK-278 round 3's V4: PASS, proved as a superset rather than... | 1 | 27 | 31.6% | — |
| 50 | `59e90e61` | 2026-09-07 | Merge TASK-281's V4: FAIL, and both defects reproduce in one comman... | 1 | 27 | 31.6% | — |

| share of module-seconds | merges |
|---|---|
| 0–10% | 0 |
| 10–25% | 2 |
| 25–50% | 18 |
| 50–99.9% | 7 |
| 100% (full) | 23 |

merges: 50 · median share: 75.9% · mean share: 67.9%
widening rule fired, merges: bin/lib/ 9, viewer/parsers.py 8, schema/ 10, tests/ helper 19
widening rule was the only one to fire, merges: bin/lib/ 2, schema/ 1, tests/ helper 10
VERDICT: FAIL — median share 75.9% > 50%; most frequent reasons: tests/ helper (19 merges), schema/ (10 merges), bin/lib/ (9 merges)

## What still makes the selection wide

Measured with the same selector, declarations and stopwatch; the script lived in
scratch and is not committed. No rule was changed to take these numbers.

**1. The helper rule, now without the stopwatch, still fires in 19 merges** and is
the only rule to fire in 10 of them. What it fires on now:

| helper path | merges |
|---|---|
| `tests/fixtures/**` | 9 |
| `tests/task_writer_support.py` | 3 |
| `tests/store_fixture.py` | 3 |
| `tests/parallel` | 3 |
| `tests/inproc.py`, `tests/contract_key_parity.py` | 2 each |
| nine other helpers | 1 each |

These are code and data that modules import or read, so unlike the stopwatch
there is no "it may reorder but not select" argument for exempting them. A
fixture change genuinely can change what a module asserts.

**2. The state-root coupling is now the largest single cause.** `perry/evidence/`
changed in 46 of the 50 merges, and an evidence-only merge still selects 27
modules, **31.6%** of module-seconds — down from 32 and 33.7%, because seven
modules were narrowed. The 26 modules below kept `perry/` or `.perry/` because
they read the whole state root rather than a file of it. **This list is the
measurement the next decision rests on.**

| module | why it reads the whole state root |
|---|---|
| `test_contract_invariance` | `pinned_phase.pinned_copy` and `copy_of_perry` — a copy of the whole tree |
| `test_contract_key_parity` | `copy_of_perry`, `pinned_copy` |
| `test_kr_progress_provenance` | `pinned_copy` |
| `test_measured_krs_declare_a_target` | `pinned_copy` |
| `test_phase_kr_declared_once` | `pinned_copy`, and `perry-goals list --root <checkout>` |
| `test_same_action_linkage` | `pinned_copy`, and tools run at the checkout |
| `test_board_render` | `copytree(perry/)` and `copytree(.perry/)` |
| `test_decoration_changes_nothing` | `copytree(perry/)` and `copytree(.perry/)` |
| `test_task_store` | `copytree(perry/)` and `copytree(.perry/)` |
| `test_answered_ask_is_legible` | `perry-task list --all` at the checkout with no `--root` |
| `test_contract_page_snippets` | `perry-task list` and shell snippets at the checkout |
| `test_count_fields` | `perry-task list` at the checkout |
| `test_diagnose` | `perry-task list` at the checkout; `perry-diagnose` scans the project |
| `test_glossary` | `perry-explain` at the checkout — it harvests ids from the project's documents |
| `test_rung_vocabulary` | `perry-explain` at the checkout |
| `test_knowledge_cards` | `perry-lint --knowledge --json` at the checkout |
| `test_review_verdicts` | `perry-lint --json` at the checkout — `--reviews` reads evidence files |
| `test_role_cards` | `perry-lint --json` at the checkout |
| `test_ns_collision` | `perry-lint` at the checkout — `--claims` walks the claimed paths |
| `test_track_attribution` | `perry-diagnose --json` at the checkout |
| `test_store_is_canonical` | `inproc.run` at the checkout with no `--root` |
| `test_bin_surface` | `perry-state --root <checkout> --dashboard`, and live byte checks on the stores |
| `test_v5_signoff` | resolves every V5 close's evidence path under `perry/` |
| `test_header_rule_harness` | walks every Python reader in the tree; three live under `perry/evidence/` |
| `test_one_header_rule` | the same walk |
| `test_one_choke_point` | the same walk, plus `perry/evidence/2026-09/TASK-323-bound.py` |

Narrowing these is not a declaration change: it would mean moving the module off
the live state root, pinning a copy, or giving the tool a `--root`. `USER-940`
holds all three.

**3. `bin/perry-task` alone selects 81 modules, 56.0%.** Unchanged by this round.

Single-path floors:

| changed path | modules | share |
|---|---|---|
| `SKILL.md` | 21 | 7.0% |
| `perry/evidence/2026-09/x.md` | 27 | 31.6% |
| `bin/perry-task` | 81 | 56.0% |
| nothing | 1 | 0.0% |

## What the next decision would have to move

Nothing is decided here. On these numbers, no further narrowing of declarations
reaches the gate: with the helper rule and the state-root coupling as they are,
23 merges are already `full` before a single `COVERS` is consulted, and the
median of the rest sits at the 31.6% floor plus whatever the change itself
selects. The three candidates, with what each is worth:

1. **The 26 modules above stop reading the live state root** (a pinned or frozen
   copy, or `--root` at a fixture). Worth the difference between a 31.6% floor
   and a near-zero one on the 46 merges that touch `perry/evidence/`.
2. **`tests/fixtures/**` stops widening** and is declared by the modules that read
   it. Worth 9 merges of the 19 remaining helper widenings.
3. **`schema/`, `bin/lib/` and `viewer/parsers.py`** — 10, 9 and 8 merges. These
   are the design's own deliberate widenings, and narrowing them trades safety
   for speed, which is a different question from the two above.
