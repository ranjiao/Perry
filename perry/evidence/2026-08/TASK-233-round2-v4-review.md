# TASK-233 — V4 review, round 2

**PASS.**

Reviewed `coding/task-233-config-readers` at `812f276` (worktree
`…/scratchpad/review-233r2`, read-only). Every destructive check ran on my own
`git archive` extracts under `…/scratchpad/rj233/`; nothing was written into the
reviewed tree, no write-side Perry tool was run anywhere, and
`perry-conform declare` was not run.

Round 1's blocker is closed, and closed in the form the block asked for: the two
`bin/perry-state` sites are converted, each carries its own named guard, the two
guards are provably not one guard, and the residue is declared as a **count**
with the command that produces it rather than as a sweep.

---

## 1 — Both sites closed, each with its own guard, and the guards are independent

Reproduced the round-1 defect first, on my own extract of `632c198` with
`.perry/config.md` deleted, store untouched, `PERRY_PROJECT` unset,
`PERRY_HOME` = the extract, cwd a subdirectory:

    $ (cd subdir && python3 ../bin/perry-lint | head -1)
    perry-lint · …/rj233/demo-r1 (state root: perry/)          ← converted walk finds it
    $ (cd subdir && python3 ../bin/perry-state --json)
    root=       …/rj233/demo-r1/subdir
    installed=  False
    warnings=   ['No Perry state found — run /perry for first-time setup.']

Exactly the string the row quotes as its own justification, still produced one
file over. Same commands on `812f276`:

    root= …/rj233/demo-r2/perry   installed= True   warnings= []
    settings_source= store        tracks_source= store

**The independence cross-check reproduces both halves.** My own driver
(`…/scratchpad/rj233/rj_v4_mut.py` — unique name, outside the repo; refuses a
non-unique anchor, asserts the target GREEN and selector > 0 tests before
mutating, clears `__pycache__`, sleeps past the mtime boundary, restores from
captured text and asserts md5):

| mutation | selector | result |
|---|---|---|
| revert `resolve_root` walk (`bin/perry-state:2616`) | `test_the_installed_gate_counts_a_store_only_project_as_installed` | **GREEN — independent** |
| revert `build` gate (`bin/perry-state:2026`) | `test_the_walk_finds_a_store_only_project_from_a_subdirectory` | **GREEN — independent** |

The author's conclusion is correct: one test covering both would have been a
false guard. The reason each needs what it needs also holds on reading — the
walk's `cwd` fallback hides the walk from the project root itself (hence cwd
below it, with `BOARD.md` parked at the *state* root so the walk's first
disjunct cannot answer), and the gate needs `--root` plus a project with no
`BOARD.md` / `OKR.md` / `design/DESIGN-*.md` so its other disjuncts cannot.

## 2 — Mutations: 5 of 5 RED, reproduced on my own driver

All five, not a spot-check. Every one md5-verified restored; driver printed
`ALL RESTORED, md5-verified`.

| # | mutation | anchor | pre | post | reddened |
|---|---|---|---|---|---|
| R1 | walk reverts to the markdown test | `bin/perry-state:2616` | GREEN | **RED** | `test_the_walk_finds_a_store_only_project_from_a_subdirectory` |
| R2 | `installed` gate reverts | `bin/perry-state:2026` | GREEN | **RED** | `test_the_installed_gate_counts_a_store_only_project_as_installed` |
| R3 | X4 — `store-default` collapsed into `store` | `viewer/parsers.py:356` | GREEN | **RED** | `test_a_store_with_no_setting_records_says_store_default` |
| R5 | X4 again, payload selector alone | `viewer/parsers.py:356` | GREEN | **RED** | `test_the_distinction_reaches_the_payload` |
| R4 | `configured` forgets the store | `viewer/parsers.py:401` | GREEN (3) | **RED** | **both** `TestPerryStateAsksItToo` site tests |

## 3 — X4 is guarded at both levels

`TestAStoreThatDeclaresNoSettingsSaysSo` asserts the predicate
(`config_store_settings` on a track-only store → `({}, CONFIG_STORE_DEFAULT)`)
and the payload (`parse_config(...)["settings_source"]`). R3 reddens the
predicate test, R5 the payload test independently. Neither is vacuous: the
predicate test asserts `values == {}`, which a `None` (unusable store) return
would fail, so the fixture is proven to parse.

## 4 — Every guard here fails under some mutation, including both controls

Six tests were added in round 2. Five are covered by R1–R5; the two *controls*
are not, so I mutated for them:

| test | mutation that reddens it |
|---|---|
| `test_the_walk_finds_a_store_only_project_from_a_subdirectory` | R1 |
| `test_the_installed_gate_counts_a_store_only_project_as_installed` | R2 |
| `test_a_store_with_no_setting_records_says_store_default` | R3 |
| `test_the_distinction_reaches_the_payload` | R5 |
| `test_the_markdown_alone_still_counts` (control) | **Z1** — `configured` forgets the markdown → RED |
| `test_a_store_with_setting_records_says_store` (control) | **Z2** — settings loop stops matching `kind: setting` → RED |

No guard here survives its own deletion, and neither control is a control that
cannot fail.

**No new test is green for the wrong reason.** Checked against the known modes:
no fixture parses zero rows (R3/R4 would have stayed green if any did); no test
greps its own source or asserts a substring over a whole file; no test builds
the dangerous state and then asserts something safe (both site tests assert on
`installed` / `project.root` from the real entry point, out of process); and
**no new fixture edits config markdown to change behaviour** — the two site
fixtures set `markdown=None` / `store=False`, which is presence, not content.
`run_state` strips `PERRY_PROJECT` (which would short-circuit the walk) and
pins `PERRY_HOME` to the tree under test; both are necessary and both are there.

## 5 — The re-run grep: count and classification verified

    $ grep -rn "config\.md" bin viewer | grep 'exists()\|is_file()'
    bin/perry-diagnose:1373:  "config": (root / ".perry" / "config.md").is_file(),
    bin/perry-diagnose:2501:  is_perry = (root / ".perry" / "config.md").is_file() or (
    bin/perry-lint:637:       if (root / ".perry" / "config.md").is_file():
    bin/perry-goals:2177:     if not (perry / "config.jsonl").exists() and not (perry / "config.md").exists():
    viewer/parsers.py:401:    return (perry / "config.jsonl").exists() or (perry / "config.md").exists()

Five hits — the reported count. Each classification checked by reading it:

- `viewer/parsers.py:401` — is `configured` itself. Correct.
- `bin/perry-goals:2177` — the wide form inlined (TASK-095). Correct.
- `bin/perry-diagnose:1373` — `perry["config"] = …is_file()`, then
  `perry["installed"] = perry["config"] or (okr and board)`. **Narrow, and it is
  the same existence-as-configured shape.** Correct, and NOT converted.
- `bin/perry-diagnose:2501` — `is_perry = …is_file() or (OKR and BOARD)`.
  Same. Correct, and NOT converted.
- `bin/perry-lint:637 § _track_context` — TASK-095's class; it walks up to find
  `.perry/config.md` and then reads `## Tracks` **out of that file as truth**.
  The classification is right, and I note the walk inside it is the same shape:
  converting the walk alone would be meaningless because the read that follows
  needs the file itself.

The stated reason for deferring `bin/perry-diagnose` checks out: that file
imports `lib` and `tables`, **not `parsers`** (`grep '^import|^from' bin/perry-diagnose`
shows no `parsers`), and it carries its own mirror of the state-root resolver
(`:967` comment). Two guards plus an import change is a row, not a line.

## 6 — Baselines, my own trees and my own hours

Fresh `git archive` extracts, `PERRY_HOME` = the tree under test, runner
`bash tests/run` (step 2 = `tests/parallel`, 8 workers). The two ran
concurrently, so wall-clock is contended; the failure sets are the measurement.

| tree | commit | started | modules | tests | failures |
|---|---|---|---|---|---|
| `…/rj233/t-632c198` | `632c198` round-1 tip | 2026-08-30 **05:01:44 CST** | 101 | 3031 | **3** |
| `…/rj233/t-812f276` | `812f276` branch tip | 2026-08-30 **05:01:46 CST** | 101 | 3037 | **3 — the same three** |

Delta **+0 modules, +6 tests, 0 new failures**. The author's `632c198` →
`d1deefb` pair (101/3031/3 → 101/3037/3) reproduces exactly; `812f276` adds only
report commits over `d1deefb`.

The three, byte-identical between the two runs:

- `test_diagnose § test_the_queue_register_reconciles_with_the_queue_on_this_repository`
  — `3 != 1 : diagnose and perry-task disagree about how many queue rows are waiting on the user`
- `test_diagnose § TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`
  — `['ACTION-7','D009-1','D010-2','PROJ-003','SPEC-007'] != []`
- `test_kr_progress_provenance § …test_no_current_in_the_payload_claims_to_be_a_measurement`
  — `the register carries no asserted current`

**Round 1's "2 failures" does not reproduce at `632c198`; I get 3**, which is
what the round-1 reviewer also got (their review records 101/3031/3 on a clone
at the same commit). So the correction stands. One nit on the *wording*: on a
`git archive` extract the board is pinned to the commit, so "the commit did not
change; the board did" cannot be the mechanism for an archive measurement — what
is actually shown is that round 1's 2 came from a **different tree** (a live
checkout carrying uncommitted board state), which is the same lesson and is why
naming the tree matters. Conclusion unaffected.

## 7 — The explanation of how § 4's false claim got past round 1: both halves true

**Half one — "round 1 had no test that ran `bin/perry-state` for this property
at all."** Verified the strong way rather than by reading. On a fresh extract of
`812f276` I reverted **both** sites and ran the whole suite
(`…/scratchpad/rj233/run-bothreverted.log`, started 05:08 CST):

    101 modules · 3037 tests · 171.3s · 8 workers
    ✗ test_config_store_readers.py
        FAIL: TestPerryStateAsksItToo.test_the_installed_gate_counts_a_store_only_project_as_installed
        FAIL: TestPerryStateAsksItToo.test_the_walk_finds_a_store_only_project_from_a_subdirectory
    ✗ test_diagnose.py            (the two pre-existing)
    ✗ test_kr_progress_provenance.py (the one pre-existing)

Across 3,037 tests, **the only thing that notices the defect is the class round 2
added.** Round 1's suite contained no guard for it, which is exactly the claim.
`tests/test_config_store_readers.py` at `632c198` reaches `perry-state` only
through `load_bin_module` (in process) and never as a subprocess.

**Half two — the docstring carried the same false claim and is corrected.**
`viewer/parsers.py § configured` at `632c198` ended
`…already asked it the wide way; these are the rest.` At `812f276` it says six,
splits them by round, and names `bin/perry-diagnose § scan_tracking` and
`§ diagnose` as **NOT converted**. Both halves hold, so the explanation is worth
what it claims to be.

## 8 — The self-caught false positive: `assertIn` was the right call

Reproduced the trip. On a fresh extract of `812f276` I restored the round-2
first-draft assertion:

    -        self.assertIn("document_language", values)
    +        self.assertEqual(values["document_language"], "English")

    $ python3 -m unittest discover -s tests -p test_live_state_expectations.py
    - ["tests/test_config_store_readers.py:533  "
    -  "TestAStoreThatDeclaresNoSettingsSaysSo.test_a_store_with_setting_records_says_store\n"
    -  "    assertEqual(<live>, 'English')\n"
    -  "    live: values['document_language']"]
    AssertionError: 24 != 23 : the recorded floor and the live sweep disagree
    FAILED (failures=2, skipped=3)

24 against 23, from that assertion, exactly as reported.

**`assertIn` did not weaken a real check.** Three reasons, each checked:

1. The value is asserted elsewhere at the level a reader actually consumes it —
   `TestParseConfigReadsTheStore.test_every_setting_comes_from_the_store_when_both_are_there`
   asserts `cfg["language"] == "English"` through `parse_config`, which reaches
   the same `config_store_settings` dict via `SETTING_FIELDS`. A wrong value
   there still reddens.
2. The **discriminating** half of this control — `assertEqual(why, CONFIG_FROM_STORE)`
   — is untouched, and it is the half that makes it a control for
   `…_says_store_default`.
3. The control can still fail: Z2 (settings loop stops matching `kind: setting`)
   reddens it *through the `assertIn`*.

Recording a 24th floor entry to keep a redundant assertion would have been the
worse trade, and naming it in the report rather than fixing it quietly is the
behaviour the before/after pair exists to produce.

## 9 — Other claims spot-checked

- **Byte comparison.** On my own extract: original `.perry/config.md` md5
  `cf1756f695ebd119784d8af4befc3a32`; deleted; `perry-config render --write --root .`
  → exit 0, `9 stored record(s)`; rebuilt md5 `cf1756f695ebd119784d8af4befc3a32`,
  `cmp` clean. Reproduced.
- **The spec's corrected item 1.** On an extract of the fork point `658e8c9`
  with the file deleted: `render --root . >/dev/null 2>&1` → **exit 2**; the same
  command piped into `head` → **exit 0**. The PMO's error and its mechanism both
  reproduce; the author's correction is right.
- **Nothing PMO-owned was touched.** `git diff 658e8c9..812f276 --stat` shows no
  `perry/BOARD.md`, no `perry/tasks.jsonl`, no `.perry/events.jsonl`.

---

## Ruling: is a declared `bin/perry-diagnose` count an acceptable way to close a row whose KR counts call sites?

**Yes, in the form it takes here — and only in that form.**

`P003-O2-KR1` is *"call sites in `bin/` that read a projected markdown file as
truth while its store exists"*, target 0. Two `bin/perry-diagnose` sites remain
in that category on the author's own reading, so **the KR is not at 0 after this
row and the goals lane must not read the row's closure as the KR being met.**

A row is closed against its spec, not against its KR. The spec named three
deliverables and put `## Tracks` out of scope; all three are delivered and
verified. What blocked round 1 was never the non-zero number — it was the
sentence *"these were the rest"*, a completeness claim with no measurement
behind it. Round 2 replaces it with a count, the command that produces it, a
per-hit classification I re-derived independently and agree with, and a stated
reason the residue is a row rather than a line (`bin/perry-diagnose` does not
import `parsers`). That is the honest closing form, and the author's derived
rule — *"these were the rest" is a measurement, needing a command whose output
is the empty set, or it should be written as a count* — is the right rule.

**One condition on the PASS, for the PMO and not for the author:** the two
`bin/perry-diagnose` sites exist only in this report. No board row on this branch
carries them, and the author correctly did not file one. If the PMO merges
without filing that row, the count becomes evidence nobody is counting — which
is the same failure mode one register over. `bin/perry-migrate:228 § document_language`
(a value-reading regex returning `"en"` with the file absent — the same class
`parse_config` just fixed) is named in the same paragraph and belongs in the
same row or its own.

---

## checked / not-checked

**checked (all on my own `git archive` extracts, never the reviewed tree):**
the two conversions and their before-state reproduction at `632c198`; all five
declared mutations with md5-verified restore; both independence cross-checks;
two mutations of my own for the two controls; the whole-suite run with both
sites reverted (the decisive test of "round 1 had no guard"); the re-run grep,
its count and each of its five classifications; `bin/perry-diagnose`'s imports;
both baselines with tree and hour; the byte-identical rebuild and its md5; the
fork-point exit-code correction, piped and unpiped; the `assertIn` decision,
including reproducing the 24-vs-23 trip; `parsers § configured`'s docstring
before and after; the branch's diffstat against the fork point.

**not checked:**

- **The 28 round-1 mutations** were not re-run. Round 1's review verified them
  on its own driver and this round grades round 2's delta.
- **`python3 -m unittest discover -s tests`** was not run. Two reviewers have now
  hit the time cap on it; I did not retry, so the dispatch's `discover`-vs-`tests/run`
  delta of 3 is still neither confirmed nor contradicted.
- **The dispatch's archive baseline (98 / 2882 / 3)** was not reproduced. It is a
  figure of an earlier `main`; my before/after pair is measured at two commits on
  one runner and is what the no-regression claim rests on.
- **Nothing was measured on a second real project.** `~/proj/gimegime-pmo` was not
  touched.
- **The prose relocation into `.perry/hook.md`** was not re-verified line by line;
  round 1 confirmed the 29 lines verbatim and round 2 did not move them.

## Non-blocking notes

1. **Merge hazard.** The branch's own copy of `perry/evidence/2026-08/TASK-233-spec.md`
   still reads *"prints `no .perry/config.md` and **exits 0** … Filed separately as
   an intake row"*; `main`'s copy carries the PMO's correction (`9db8f45`). The
   merge must keep **main's** text — a naive resolution in the branch's favour
   would re-introduce a measurement the PMO has already retracted.
2. **`Fixture.bare()`'s docstring describes work it does not do.** It says it
   removes `BOARD.md` / `OKR.md` so a caller's OR-chain cannot answer for the
   predicate, but `Fixture.project()` never creates either, so the two
   `unlink(missing_ok=True)` calls are no-ops. The fixture *is* bare and the
   guards are sound; the comment claims a step that is not happening, which is
   the small version of the thing this row was failed for.
3. **"The commit did not change. The board did."** — see § 6. True of the lesson,
   not literally true of a `git archive` measurement at a pinned commit.
