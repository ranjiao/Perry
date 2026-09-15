# TASK-453 — result: S1 and S3–S7 land; S2 not done, by decision (USER-936)

> Executor: claude-subagent · Branch: `coding/task-453-architecture-rules` · Base: `bb178072`
> Commits: `9e3cf9d4` (the test module); the commit carrying this file and `tests/durations.json`.

## 1. Base check

- Worktree HEAD at start: `0b5bf99e`, a strict ancestor of `bb178072`; tree clean.
- `git merge --ff-only bb178072` fast-forwarded; branch
  `coding/task-453-architecture-rules` created at `bb178072`.

## 2. Read before changing anything

Read in full at `bb178072`: `ARCHITECTURE.md`, `bin/ARCHITECTURE.md`,
`perry/evidence/2026-09/TASK-453-spec.md`, and `DESIGN-017 § 1.4`, `§ 5.1`,
`§ 5.2` and `§ 6`; USER-934 and USER-935 in `perry/asks.jsonl`. USER-936 was
read in the primary checkout's `perry/asks.jsonl`, where the PMO recorded it
mid-task.

## 3. Baseline, measured in this worktree at `bb178072`

`bash tests/run`. Neither `PERRY_PROJECT` nor `PERRY_HOME` is set in this shell
(`printenv` exit 1), so this is the `env -u` run. **2 of 140 modules red,
10 of 3934 tests failed**; the tree guard passed. Both reds re-run alone
(`python3 tests/parallel <module>`) and reproduce identically:

| Module | Alone | Failing | What it asserts against |
|---|---|---|---|
| `test_md_store.py` | 9 of 76 red | `TestTheObjectiveIdIsMinted` (6), `TestTheByteGateCanFail` (2), `TestThisRepositoryIsReproducedByteForByte.test_okr` | this repository's live `perry/OKR.md`: `14 != 10` objectives; `0 != 13` KRs against KR lines |
| `test_okr_krs_render.py` | 1 of 40 red | `TestTheShippedOkr.test_the_shipped_okr_md_carries_no_kr_table_rows` | 13 KR table rows (first: `O1-KR1 … carried → v4`) in the shipped `OKR.md` |

Both read the OKR document that base commit `15369956` (OKR v4) rewrote. They
are not this task's and were not investigated.

## 4. What landed — `tests/test_architecture_rules.py`

32 tests: 30 pass, 1 skip (S7), 1 expected failure (S1 live). Every checker is
a function over an input it is handed and returns what it found; each live test
asserts `[]`, and each synthetic test asserts the exact planted defect.

| Rule | Outcome on this tree | Live test |
|---|---|---|
| S1 `viewer/parsers.py` imports nothing from `bin/` | **expected failure** — `import lib` (line 94) and `import perry_md_store` (line 378), both inside functions. Checker proven on two synthetic sources: one with `bin/` imports, reported; one without, clean. The reason names USER-935 and TASK-458 | `TestS1…test_viewer_parsers_imports_nothing_from_bin` |
| S2 | **not done, by decision — USER-936.** No test, no skip, no expected failure | — |
| S3 standard library only | green on 3.11 (194 files); **skips** on 3.9 | `TestS3…test_every_import_is_standard_library_or_in_the_repository` |
| S4 tree guard on every exit path | green | `TestS4…test_tests_run_verifies_the_tree_on_every_exit_path` |
| S5 every component named | green, with a declared exempt list | `TestS5…test_every_component_is_named` |
| S6 size caps | green: 323 / 500 and 195 / 600 | `TestS6…test_every_architecture_document_is_within_its_cap` |
| S7 decided sections match the confirmed hash | **skips** — no `User-confirmed` entry carries a hash | `TestS7…test_decided_sections_match_the_newest_confirmed_hash` |

One correction to the spec's S1 text: `tables` is `viewer/tables.py`, not a
`bin/` module, so importing it is not an S1 hit.

### The skips, quoted (verification 4)

- S3, under `/usr/bin/python3` (3.9.6):
  `skipped 'S3 needs sys.stdlib_module_names, which Python 3.10 added; this is Python 3.9.6, which cannot tell the standard library from a third-party package, so S3 does not run here rather than pass'`
- S7, under 3.11 and 3.9:
  `skipped 'no confirmed hash recorded; TASK-454 records the first'`

## 5. Mutations (verification 3)

Each on its own `rsync` copy of the worktree under
`$TMPDIR/perry-scratch/agent-a435e369f332c0c74/`, run with
`python3 -m unittest discover -s <copy>/tests -p test_architecture_rules.py -v`.
No mutation touched the worktree: `git status` shows only this file untracked,
and `git diff 9e3cf9d4 --stat` was empty after all seven.

| Rule | Mutation | Result | Red test |
|---|---|---|---|
| S1 | `imports_of` skips `alias.name == "lib"` | **red** (1) | `test_a_bin_import_is_reported_wherever_it_sits` |
| S2 | `def parse_x` appended to `bin/perry-churn` | green — **by decision** (USER-936; S2 is not implemented). Not a finding | — |
| S3 | `import yaml` appended to `bin/perry_store.py` | **red** (1): `bin/perry_store.py:2350 imports yaml` | `test_every_import_is_standard_library_or_in_the_repository` |
| S4 | the `tests/tree_guard.py verify` call in `tests/run` replaced by `true` | **red** (1): `` `finish`, the EXIT trap, never runs `tests/tree_guard.py verify` `` | `test_tests_run_verifies_the_tree_on_every_exit_path` |
| S5 | `mkdir unnamed/` at the root | **red** (1): `` top-level directory `unnamed/` is in no § 2 heading and is not exempt `` | `test_every_component_is_named` |
| S6 | `ARCHITECTURE.md` grown 323 → 501 lines | **red** (1): `ARCHITECTURE.md is 501 lines; the cap is 500` | `test_every_architecture_document_is_within_its_cap` |
| S7 (a) | a fabricated `- 2026-09-16 · v1 · **User-confirmed** (NN-6) · hash: sha256:2434ed7c…7160` at the top of `§ 8` | green, and the live S7 test **ran** (`ok`, not skipped) | — |
| S7 (b) | on (a), NN-1's rule text in `§ 6` edited | **red** (1): "a decided section changed without a confirmation — ask the user, then record the confirmation in § 8 … hash to d75e31ec…c401" | `test_decided_sections_match_the_newest_confirmed_hash` |

No implemented rule's mutation stayed green.

## 6. Findings and choices a reviewer should check

1. **S3 does not read `tests/fixtures/`** (`S3_NOT_SCANNED`, with a reason). Two
   frozen snapshots there, `tests/fixtures/live-state/md_store.before.py:50` and
   `v5_signoff.before.py:40`, import `gate`, which TASK-261 (`6ce1f5b4`)
   deleted. They are data: `tests/live_state_expectations.py` reads them with
   `ast.parse` and nothing imports or runs them. Counting them would make S3 red
   on history rather than on code. If the user reads "every import in `tests/`"
   to include fixtures, S3 is red at base and needs a decision.
2. **S5's exempt list** (`S5_EXEMPT_DIRECTORIES`, `S5_EXEMPT_EXECUTABLES`),
   each with a reason: `.git`, `.claude`, `.gstack`, `.trae`, `__pycache__`
   (tool state; the last four exist in the primary checkout, where the merge
   suite runs); `.github`, `.vscode`; `bin/perry` (the index, which `perry
   list` does not list); and **`state/`**. `state/` holds the diagnosis and
   adoption report templates, ships as content, and no `§ 2` heading names it.
   It is exempted so the rule can land. The exemption's own reason says it may
   be a `§ 2` omission, and `§ 2`'s list is the user's (DESIGN-017 decision 3).
   A guard test, `test_no_exemption_is_for_a_directory_section_2_already_names`,
   goes red if `§ 2` later names an exempted directory, so the entry cannot
   outlive the fix. Raised as a `§ 7` question below.
3. **S5 reads `bin/perry list --json`** (`tools[].tool` plus `undeclared`), the
   tool's payload, not its human text.
4. **S7's hashed text is defined here, and TASK-454 has to agree with it.**
   `decided_text` is `## §1\n` + § 1's body + `\n## §3 Forbidden\n` + the bullet
   lines under § 3's `Forbidden` paragraph + `\n## §6\n` + § 6's body + `\n`,
   with each body's outer blank lines dropped. The token read from a § 8 entry is
   `hash: sha256:<64 hex>` (the `sha256:` prefix optional). The newest
   confirmation is the one with the latest leading date, ties broken by document
   order (§ 8 is newest first). Once any confirmation carries a hash, the newest
   must carry one too. If TASK-454 picks another format, it changes
   `decided_text` / `HASH_TOKEN` in this one module.
5. **S4 is lexical over `tests/run`.** It reads the snapshot line, the first
   `trap <fn> EXIT` after it, the body of `<fn>`, and every top-level line
   between them, ignoring comments and function bodies. It does not simulate
   bash: an exit hidden in a sourced file or an `eval` is invisible to it.
6. **`COVERS`.** DESIGN-017 § 5.2 says this module "declares that it covers
   every path", and DESIGN-021 decision 2 makes that a module-level `COVERS`
   constant. Nothing at base defines the constant or its `ALL` value (phase A of
   DESIGN-021). DESIGN-021's selector rule 5 selects a module with no `COVERS`
   every time, which is the behaviour this module needs, so none is declared
   here rather than inventing a sentinel. Phase A should add `COVERS = ALL`.
7. **USER-936's wording and the measurement differ in one clause.** The ask
   says the 12 matches include none that reads a state file. From signatures and
   docstrings, `perry-state § parse_config` reads the project's settings, and
   `parse_depends`, `parse_wip`, `parse_verdicts` and `parse_glossary` parse
   content that comes from project files (cells, documents). This does not
   change the decision; it may matter when NN-1's check is redone.
8. **`tests/durations.json`** gains `test_architecture_rules.py` at 0.78s under
   source `2026-09-15-task453`: one module timed alone three times
   (1.11/0.78/0.77s), median, ref `9e3cf9d4`. The file was rewritten through
   `json` only after confirming a round-trip reproduces it byte for byte
   (indent 2, keys unsorted); the diff is additions only.

## 7. Proposed `Check:` lines for `ARCHITECTURE.md § 6` (deliverable 2; not applied)

`§ 6` is decided (NN-6); TASK-454 applies these with the user's confirmation.

- **NN-1**: `Check: review — a diff adding a reader of a state file outside viewer/parsers.py` — until NN-1's structural check is redone without grep (USER-936); then that test's name.
- **NN-2**: `Check: review — a diff touching a writer's record-then-projection order, or the source a payload or perry-tasks board reads`
- **NN-3**: `Check: review — a diff touching a write or render path's exit status or its report`
- **NN-4**: `Check: review — a diff in bin/ that decides from the wording of a document`
- **NN-5**: `Check: tests/test_architecture_rules.py § TestS4TreeGuardOnEveryExitPath` (and `tests/tree_guard.py` on every run)
- **NN-6**: `Check: tests/test_architecture_rules.py § TestS7DecidedSectionsMatchTheConfirmedHash`

## 8. Full suite on the final commit (verification 2)

`bash tests/run` on `c9725643` (the commit that carries this file and the
durations entry): **141 modules, 3966 tests; 2 modules red, 10 tests failed**;
tree guard passed (nothing under the worktree moved); durations 144 recorded,
144 on disk, every module accounted for.

The 10 failing tests are **identical, name for name, to the baseline's 10**
(`test_md_store` 9, `test_okr_krs_render` 1; compared as sets from the two
logs: nothing only in the final run, nothing only in the baseline). The 32 new
tests are the whole difference in count (3934 → 3966). **No reds beyond the
baseline.**

## 9. Unusual

- This session's worktree-isolation sandbox refused the brief's
  scratch-derivation block (`$(git rev-parse --show-toplevel)`), every `env -u …`
  form, and heredocs. The scratch directory was derived by hand as
  `$TMPDIR/perry-scratch/agent-a435e369f332c0c74` (the value the block
  produces), and the suite was run as plain `bash tests/run` after confirming
  neither Perry variable is set.
- The first two attempts at the baseline wrote nothing (refused, then a wrong
  `/tmp` path); the recorded baseline is the third, run before any file was
  written.
