# TASK-448 — the replay: 50 merges through the `COVERS` selector

> Design: `DESIGN-021 § 6` phase A, the gate · Spec: `TASK-448-spec.md` deliverable 5
> Branch: `coding/task-448-covers-and-replay` · round 3 after `USER-942` (2026-09-16)

## Verdict, three rounds

| | round 1 (`e76cb084`) | round 2 (`USER-940`) | round 3 (`USER-942`) |
|---|---|---|---|
| **median share** | **100.0%** | **75.9%** | **73.3%** |
| mean share | 75.1% | 67.9% | 64.6% |
| merges that widen to `full` | 30 of 50 | 23 of 50 | 23 of 50 |
| merges at or above 50% | 33 | 30 | 28 |
| evidence-only floor | 32 modules · 33.7% | 27 modules · 31.6% | **19 modules · 23.0%** |
| modules declaring the whole state root | 33 | 26 | **18** |
| suite total (`tests/durations.json`) | 1,055.6 s | 1,056.4 s | **962.8 s** |
| verdict | FAIL | FAIL | **FAIL** |

**Still FAIL, and the reason has changed shape.** Rounds 1 and 2 failed because
too much was selected by declaration. Round 3 failed because of the widening
rules alone: 23 merges select the full suite before a single `COVERS` is
consulted, and 5 more land above half without one firing.

**The arithmetic the next decision faces.** A median at or below 50% needs at
least 26 of the 50 merges at or below 50%. Today 22 are — 16 of them under 25%.
The 28 that are not break down as 23 `full` and 5 between 50% and 99.9%. **No
further narrowing of declarations can reach the gate**, because declarations do
not decide any of those 23.

## What changed in round 3

`USER-942` took the 8 heaviest of round 2's 26 broad modules off the live state
root. Ranked by their recorded seconds, worked down:

| module | was | conversion | now |
|---|---|---|---|
| `test_board_render` | 32.58 s | copies the stores and the anchor, not all of `perry/` | 1.24 s |
| `test_store_is_canonical` | 21.59 s | **no code change** — it already passed `--root` on every call; the broad declaration was simply wrong | 0.69 s |
| `test_task_store` | 18.64 s | the same copy, plus `.perry/events.jsonl` | 1.55 s |
| `test_decoration_changes_nothing` | 16.27 s | the stores plus `OKR.md` and `phase/`, the documents it decorates | 4.51 s |
| `test_review_verdicts` | 10.68 s | the opt-in case runs on this module's own fixture | 8.01 s |
| `test_rung_vocabulary` | 5.86 s | `--root` at the fixture project | 0.96 s |
| `test_contract_page_snippets` | 4.79 s | the page's blocks run against the fixture project | 1.24 s |
| `test_count_fields` | 1.88 s | `--root` at the fixture project | 0.51 s |

112.29 s of declared-broad time became 18.71 s, and the same eight modules were
re-timed alone under a stamped source (`2026-09-16-task448-r3`), which is most of
why the suite total falls to 962.8 s.

`tests/live_stores.py` is the shared copy helper: the stores, the anchor, and
optionally `OKR.md` and `phase/`.

## Method (unchanged from rounds 1 and 2 except the stopwatch)

- **Enumeration.** `git log --merges --first-parent -50 --format=%H bb178072`,
  the same base and therefore the same 50 merges as both earlier rounds.
- **Changed paths.** `git diff --name-only --no-renames M^1 M`.
- **Selector.** `tests/selection.py § select` against the declarations in the
  working tree.
- **Share.** Selected module-seconds ÷ suite module-seconds from
  `tests/durations.json`, read through `tests/parallel § load_durations`:
  962.8 s over 145 modules, the three unmeasured counting 0. **The stopwatch
  moved this round**, so a share is not comparable to round 2's by seconds; the
  proportions and the module counts are.
- **Reproduce.** `python3 tests/selection.py --replay 50 --base bb178072`.

## Per merge — the selector's own output, round 3

| # | merge | date | subject | paths | modules | share | widening rule (paths) |
|---|---|---|---|---|---|---|---|
| 1 | `de4dc685` | 2026-09-15 | Merge TASK-441: six live-phase test modules measure a copy with pha... | 9 | 145 | 100.0% | tests/ helper (1) |
| 2 | `8489a2c8` | 2026-09-15 | Merge TASK-262 round 4b: no reader other than the imports reads a h... | 74 | 145 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); schema/ (4); tests/ helper (23) |
| 3 | `80ef880b` | 2026-09-15 | Merge TASK-262 round 4a: perry-task writes never read or rewrite a ... | 44 | 145 | 100.0% | bin/lib/ (1); schema/ (1); tests/ helper (1) |
| 4 | `942d7749` | 2026-09-15 | Merge TASK-262 round 3 result: stopped on contract pins, nothing im... | 1 | 19 | 23.0% | — |
| 5 | `f53b10b9` | 2026-09-15 | Merge fix/hidden-reds-and-waits: two reds hidden behind --slow, two... | 4 | 10 | 17.4% | — |
| 6 | `282e6acb` | 2026-09-15 | Merge TASK-262 round 2: perry-task SURFACE writes names what each w... | 6 | 93 | 71.4% | — |
| 7 | `ddf60594` | 2026-09-15 | Merge TASK-262 round 1: perry-tasks board names each section's stor... | 9 | 145 | 100.0% | tests/ helper (1) |
| 8 | `5c790cff` | 2026-09-14 | Merge TASK-237 round 2 V4 review: PASS | 1 | 19 | 23.0% | — |
| 9 | `80c8eeb1` | 2026-09-14 | Merge TASK-335: the parity anti-vacuity tests read one frozen copy | 3 | 25 | 28.6% | — |
| 10 | `7523f1fe` | 2026-09-14 | Merge TASK-237 round 2: a write refuses where nothing is installed;... | 20 | 145 | 100.0% | bin/lib/ (1); schema/ (1) |
| 11 | `13522369` | 2026-09-14 | Merge TASK-237 3d: the V5-signed hand-off contract, the git-boundar... | 22 | 61 | 47.1% | — |
| 12 | `0f1ed007` | 2026-09-14 | Merge TASK-237 3c: BOARD.md is deleted; installed needs .perry/; a ... | 72 | 145 | 100.0% | viewer/parsers.py (1); schema/ (8); tests/ helper (4) |
| 13 | `0ec65094` | 2026-09-14 | Merge TASK-237 3b-prime: starts write the config store first; one i... | 56 | 145 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); schema/ (7); tests/ helper (2) |
| 14 | `161c927c` | 2026-09-14 | Merge TASK-237 3b (partial): cadence store, board title and prose, ... | 22 | 145 | 100.0% | viewer/parsers.py (1); schema/ (1); tests/ helper (1) |
| 15 | `47dce04a` | 2026-09-14 | Merge TASK-237 3a: reads answer from their stores, and writes land ... | 17 | 145 | 100.0% | viewer/parsers.py (1); schema/ (2); tests/ helper (1) |
| 16 | `cb88d848` | 2026-09-14 | Merge TASK-237 D1: perry-tasks board prints the whole board from th... | 8 | 101 | 75.2% | — |
| 17 | `9549626e` | 2026-09-14 | Merge TASK-237 D1+D2: the board-less project is recognised; byte-id... | 6 | 145 | 100.0% | tests/ helper (1) |
| 18 | `c7618a96` | 2026-09-12 | Merge TASK-439: `perry-task add` refuses a row that answers the KR ... | 11 | 103 | 76.5% | — |
| 19 | `4babb645` | 2026-09-12 | Merge TASK-430: 58 modules that silently reported a clean pass, and... | 6 | 145 | 100.0% | tests/ helper (3) |
| 20 | `687579bd` | 2026-09-12 | Merge TASK-236: OKR.md's 38 KR rows come out, and the byte gate is ... | 11 | 145 | 100.0% | tests/ helper (1) |
| 21 | `fe9b922e` | 2026-09-11 | Merge v4-round-411-412-419-431: four PASSes, and one green that sho... | 1 | 19 | 23.0% | — |
| 22 | `7c89ad05` | 2026-09-11 | Merge v4-review-348-368-421: three PASSes, and a finding aimed at t... | 1 | 19 | 23.0% | — |
| 23 | `cf3611ec` | 2026-09-11 | Merge TASK-437: one wrong-root call site, and the reason it was inv... | 4 | 57 | 44.8% | — |
| 24 | `076ae21a` | 2026-09-11 | Merge spec-437 | 1 | 19 | 23.0% | — |
| 25 | `ce9041f0` | 2026-09-11 | Merge evidence-411: TASK-411's measurements, which existed only in ... | 1 | 19 | 23.0% | — |
| 26 | `9c30782a` | 2026-09-11 | Merge task-436-diagnose-dangling: one of four paths closed, and the... | 4 | 48 | 37.3% | — |
| 27 | `b5b7d023` | 2026-09-11 | Merge task-419-review-rounds-criteria: the exhaustion counter reads... | 5 | 84 | 62.6% | — |
| 28 | `6affdd38` | 2026-09-11 | Merge task-412-contract-snippets: three defects in a snippet nothin... | 3 | 145 | 100.0% | schema/ (1) |
| 29 | `89617487` | 2026-09-11 | Merge task-431-blank-cell: one blank-cell rule, nine sites not three | 13 | 145 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); tests/ helper (4) |
| 30 | `575f9dee` | 2026-09-11 | Merge task-421-scratch-collisions | 7 | 39 | 34.4% | — |
| 31 | `fef35967` | 2026-09-11 | Merge task-368-inproc-slice-1 | 10 | 145 | 100.0% | tests/ helper (1) |
| 32 | `292bce3e` | 2026-09-11 | Merge worktree-agent-afe8ae683f09b6754 | 1 | 19 | 23.0% | — |
| 33 | `4efc810f` | 2026-09-11 | Merge task-362-round11-review | 1 | 19 | 23.0% | — |
| 34 | `70458893` | 2026-09-11 | Merge specs-five-spinouts: specs for TASK-412, 419, 421, 431 and 436 | 5 | 19 | 23.0% | — |
| 35 | `fe0292fb` | 2026-09-11 | Merge evidence/task-239-result | 1 | 19 | 23.0% | — |
| 36 | `899f3ffd` | 2026-09-11 | Merge review/task-400-v4-round1 | 1 | 19 | 23.0% | — |
| 37 | `8e81e5ee` | 2026-09-11 | Merge task-426-restore-check | 2 | 20 | 19.1% | — |
| 38 | `1632095d` | 2026-09-11 | Merge task-411-declaration-both-ways | 2 | 145 | 100.0% | tests/ helper (1) |
| 39 | `7f43a11c` | 2026-09-11 | Merge task-362-blank-rung: done stamped a verification its own vali... | 3 | 83 | 59.9% | — |
| 40 | `ee3f46f6` | 2026-09-11 | Merge specs-348-368: specs for TASK-348 and TASK-368 | 2 | 19 | 23.0% | — |
| 41 | `583f024f` | 2026-09-11 | Merge bin-contract-phase-a: DESIGN-016's thirteen closed rows, and ... | 89 | 145 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); schema/ (3); tests/ helper (3) |
| 42 | `4ebc0693` | 2026-09-09 | Merge suite-cost-round3: TASK-400 to review, TASK-402 closed, DESIG... | 25 | 145 | 100.0% | tests/ helper (4) |
| 43 | `f2016f12` | 2026-09-08 | Merge suite-cost-round2: one shared helper, 21 modules, CPU 1278s t... | 2 | 145 | 100.0% | tests/ helper (1) |
| 44 | `fa2df316` | 2026-09-08 | Merge drop-projected-markdown: ADR-019, and four cuts at the suite'... | 137 | 145 | 100.0% | bin/lib/ (1); viewer/parsers.py (1); schema/ (4); tests/ helper (25) |
| 45 | `724f91a5` | 2026-09-07 | Merge TASK-394: add --unlinked writes the declaration, and the KR d... | 8 | 145 | 100.0% | bin/lib/ (1) |
| 46 | `26bcec72` | 2026-09-07 | Merge TASK-281 round 2: whitespace no longer inflates the KR, and t... | 4 | 145 | 100.0% | bin/lib/ (1) |
| 47 | `883d9d26` | 2026-09-07 | Merge ADR-017 step 3: 27 of 79 renamed, 52 deliberately left | 13 | 145 | 100.0% | tests/ helper (3) |
| 48 | `51c32095` | 2026-09-07 | Merge ADR-017 step 2: one grammar at both levels, in one commit | 21 | 32 | 31.6% | — |
| 49 | `4e88cd52` | 2026-09-07 | Merge TASK-278 round 3's V4: PASS, proved as a superset rather than... | 1 | 19 | 23.0% | — |
| 50 | `59e90e61` | 2026-09-07 | Merge TASK-281's V4: FAIL, and both defects reproduce in one comman... | 1 | 19 | 23.0% | — |

| share of module-seconds | merges |
|---|---|
| 0–10% | 0 |
| 10–25% | 16 |
| 25–50% | 6 |
| 50–99.9% | 5 |
| 100% (full) | 23 |

merges: 50 · median share: 73.3% · mean share: 64.6%
widening rule fired, merges: bin/lib/ 9, viewer/parsers.py 8, schema/ 10, tests/ helper 19
widening rule was the only one to fire, merges: bin/lib/ 2, schema/ 1, tests/ helper 10
VERDICT: FAIL — median share 73.3% > 50%; most frequent reasons: tests/ helper (19 merges), schema/ (10 merges), bin/lib/ (9 merges)

## What still makes the selection wide

**1. The widening rules, and nothing else, now decide the verdict.** 23 merges
are `full`: `tests/` helper fires in 19 (the only rule to fire in 10),
`schema/` in 10, `bin/lib/` in 9, `viewer/parsers.py` in 8. The unmatched rule
has never fired in any round. What the helper rule fires on, by merges:
`tests/fixtures/**` 9, `tests/task_writer_support.py` 3,
`tests/store_fixture.py` 3, `tests/parallel` 3, `tests/inproc.py` and
`tests/contract_key_parity.py` 2 each, nine others 1 each. `USER-942` holds
`tests/fixtures/**` deliberately: a fixture is read by the modules that use it.

**2. Eighteen modules still declare the whole state root, 221.4 s.** Each was
examined and left, for one of three reasons.

*Its subject is this repository's own conformance — converting it would make
the test lie:*

| module | s | what it asserts about the live state |
|---|---|---|
| `test_diagnose` | 39.02 | `test_the_queue_register_reconciles_with_the_queue_on_this_repository` |
| `test_bin_surface` | 31.89 | that a documented command writes nothing into the live project, byte for byte |
| `test_v5_signoff` | 13.00 | every V5 close's evidence path resolves under `perry/` |
| `test_ns_collision` | 17.61 | `test_each_path_resolves_under_its_declared_root`, on this repository's two roots |
| `test_track_attribution` | 8.85 | `test_this_repository_reads_back_the_register_its_file_declares` |
| `test_role_cards` | 8.52 | `test_perry_itself_declares_no_roles_and_stays_clean` |
| `test_knowledge_cards` | 2.31 | `test_perry_itself_has_at_least_one_card` |
| `test_answered_ask_is_legible` | 3.17 | its own V3 item: *prove it against this repository, not a fixture* |
| `test_glossary` | 3.26 | every glossary term resolves through `perry-explain` against this project's documents |

*It walks the whole tree, and the tree is the subject:*

| module | s | |
|---|---|---|
| `test_header_rule_harness` | 40.30 | every Python reader in the repository; three live under `perry/evidence/` |
| `test_one_header_rule` | 11.56 | the same walk |
| `test_one_choke_point` | 6.57 | the same walk, plus `perry/evidence/2026-09/TASK-323-bound.py` |

*It measures the live register through a pinned copy, which is what the KR is:*

| module | s | |
|---|---|---|
| `test_contract_key_parity` | 7.64 | `copy_of_perry`, `pinned_copy` |
| `test_same_action_linkage` | 6.83 | the same-action KR, counted from the live linkage store and event log |
| `test_contract_invariance` | 6.89 | `pinned_copy` |
| `test_kr_progress_provenance` | 5.79 | `pinned_copy` |
| `test_phase_kr_declared_once` | 4.83 | `pinned_copy` |
| `test_measured_krs_declare_a_target` | 3.33 | `pinned_copy` |

The last group shares one helper, `tests/pinned_phase.py`, whose copy is the
whole tree on purpose — `perry-task list` resolves an evidence cell against
files anywhere in the project. Narrowing that helper would change what six
modules measure at once and is not a declaration change.

**3. Single-path floors:**

| changed path | modules | share |
|---|---|---|
| `SKILL.md` | 21 | 7.7% |
| `perry/evidence/2026-09/x.md` | 19 | 23.0% |
| `bin/perry-task` | 81 | 59.5% |
| nothing | 1 | 0.0% |

`bin/perry-task` rose from 56.0% to 59.5% as a share, because the suite total
fell while its 81 modules did not.

## What the next decision would have to move

On these numbers the gate is reachable only through the widening rules. In
order of merges affected:

1. **`tests/fixtures/**` — 9 merges.** Held by `USER-942`. Exempting it is a
   real loosening: a fixture change can change what a module asserts.
2. **`schema/` — 10 merges, `bin/lib/` — 9, `viewer/parsers.py` — 8.** The
   design's deliberate widenings. Narrowing any of them trades safety for
   speed, which is `DESIGN-021 § 5.2`'s own question, not this row's.
3. **The remaining helper paths — 10 merges.** `tests/task_writer_support.py`,
   `tests/store_fixture.py`, `tests/parallel`, `tests/inproc.py` and six others.
   Each is code a module imports, so the same objection as fixtures applies.

Nothing in the list above is a declaration. Phase A's gate has now been shown,
by measurement in three rounds, to be unreachable by declaring coverage more
precisely.
