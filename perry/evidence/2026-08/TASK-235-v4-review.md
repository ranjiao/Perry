# TASK-235 — V4 review, round 1

**PASS**, with one required correction before merge: a load-bearing code comment
in `bin/perry-decide` states something about the removed ADR-004 gate that is
measurably false, and it understates a real safety loss. Nothing about the
behaviour, the tests, the record or the contract is wrong.

Reviewed at `0926e97`, tip of `coding/task-235-decisions-index`, in a detached
read-only worktree. Every destructive probe ran against `git archive` copies of
`HEAD` and of `main` under `scratchpad/rjv235/`, never against the reviewed tree.
All harness files are prefixed `rjv235-`.

Graded against `perry/evidence/2026-08/TASK-235-spec.md` — **which is not on this
branch.** It was committed to `main` after the fork point `ee0b36a`, so it was
read with `git show main:…`. The branch is not missing anything; noting it so the
next reader does not repeat the search.

---

## 1 · The declared gap is closed. I ran the full suite on a quiet machine.

```
$ cd <worktree>            # 0926e97
$ bash tests/run
1. schema drift guard … ✓ clean
98 modules · 2892 tests · 458.4s · 8 workers
✗ 2 module(s) red
```

**3 failures, and all three are the pre-existing ones the author named at
`ee0b36a`:**

| Module | Test | Signature |
|---|---|---|
| `test_diagnose` | `…test_the_queue_register_reconciles_with_the_queue_on_this_repository` | `2 != 0` |
| `test_diagnose` | `TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks` | `['ACTION-7','D009-1','D010-2','PROJ-003','SPEC-007']` |
| `test_kr_progress_provenance` | `…test_no_current_in_the_payload_claims_to_be_a_measurement` | `the register carries no asserted current` |

**Ruling on § 8.1's expectation: it was right.** 2892 tests is the measured
number, `2892 − 2882 = +10` is the measured delta, and the failure set is
identical to the fork point's. `test_procedures_call_the_tool` is green, so
`b57a34a` holds. The author was correct to label it an expectation; it is now a
measurement.

**Board state for these numbers.** Taken on the branch's own tree, whose
`perry/BOARD.md` / `perry/tasks.jsonl` are `ee0b36a`'s (§ 9: the author did not
touch them). On that board `test_contract_key_parity` is **green** — the two
data-dependent witness tests the brief warns about did not fire, because
`conformance.in_progress_with_no_live_run` is empty on this board. So the
baseline here is **3, not 5**, and the difference from the brief's `main` figure
is board state, not code. `main` has since moved to `208e0d3`, whose own commit
subject says the two extra failures there are not a regression.

Machine: load average 7.5 at launch, one other agent's suite in flight
(`scratchpad/rv8-main-6c0d041`). 458s wall, vs the author's 595s under load 32–51.

`perry-lint` on the tree: **0 errors**, 4 pre-existing `NS-01` warnings, and no
missing-claimed-file report. Spec verification item 3 satisfied.

---

## 2 · The thing most likely to be wrong: there is no replacement index, and the guard is real

**Searched the branch for a replacement index under any name and found none.**

- `git diff --diff-filter=A ee0b36a..HEAD` adds exactly three files: the result
  doc and two zh fixture ADR bodies. No index was added under any name.
- `bin/perry-decide` has exactly two write sites: `:379` (the ADR body in
  `cmd_new`) and `:403` (`_flip` rewriting an ADR body). `render_index` and
  `index_rows` are gone.
- `find . -name 'DECISIONS*'` returns only `templates/{ops,software}/DECISIONS.md`
  — both **unmodified by this branch** and both an append-only *prose journal*
  for a foreign project with no store, not an index of ADR files. Correct under
  DESIGN-013 § 5.1, and `bin/perry-diagnose:129` now says so in place.
- The doc diff consistently says the index is gone; nothing instructs a human or
  an agent to maintain a substitute.

**The guard has the property claimed.** `TestNothingWritesAnIndex.assert_only_adr_bodies`
computes `Project.files()` — `root.rglob("*")`, every file at any depth — and
asserts every entry other than `.perry/config.md` matches
`^decisions/ADR-\d+-[^/]+\.md$`. It names no filename, so `assertFalse(DECISIONS.md.exists())`'s
hole is genuinely closed. Its five members cover every write command the tool has.

### I tried to defeat it. Two attempts.

**Attempt 1 — an index under a name the test does not anticipate.** Mutation 4's
`ADRS.md` is caught (below). So are `INDEX.md`, `decisions/README.md`,
`decisions/index.md`, `.perry/anything.md` — the regex rejects every one of them
and `rglob` sees every depth.

**Attempt 2 — an index disguised as an ADR body**, i.e. a real rendered index
table written to `decisions/ADR-000-index.md`, which *does* satisfy the regex.
This is the only escape from `TestNothingWritesAnIndex` I could construct, and it
**escapes that guard** — `test_decide_writer` stays green. It does not survive
the suite: `test_decide_status_enum` goes red with 3 failures, because
`read_adr_records` globs `ADR-*.md` and reads the fake back as an ADR, corrupting
the status counts. So the writer side is sealed by the guard and the reader
together, and I could not get an index through.

**Residual hole, reported not fixed:** the guard covers `bin/perry-decide`'s
write commands only. Nothing prevents a *hand-committed* index appearing in
`perry/decisions/` in a future session. `test_ownership.test_decisions_specifically_is_owned_by_decide_everywhere`
now carries an explicit `assertNotIn("DECISIONS.md", claims)` with a DESIGN-013
§ 4.1 message, which covers the schema half. That is the right amount of guard
for this row; naming it so nobody assumes more.

---

## 3 · Claims, each with a measurement

### Claim 1 — `perry-decide list` prints every ADR, same counts ✅

`python3 bin/perry-decide list --root .` prints ADR-001…ADR-010, all `active`,
with the same types, and `10 active · 10 total`. The deleted file's header said
`Active: 10`. `--json` additionally carries `date`, `path`, `deciders`,
`supersedes`, `lines` — a superset of every column the index had. Nothing lost.

Nit, not a defect: the *human* render prints id/status/type/title and the count
line but not `date`, and never printed `expired_sunsets`. Both were already true
on `main`, so no regression — but `perry-decide list` is now the only surface, so
"the terminal drops half its payload" (the author's own words about
`missing_type`) still applies to `expired_sunsets`.

### Claim 2 — grep, and the historical record ✅

`grep -rn 'DECISIONS.md' bin/ tests/ schema/ reference/ templates/ SKILL.md */SKILL.md`
returns **47**, matching § 9's count, and I checked the categories: foreign-project
detection (`perry-diagnose DECISION_NAMES`, `project-archetypes.md`,
`templates/*`), historical narrative in test docstrings, and the author's own
"what was deleted and why" notes. No live self-reference.

**The record is intact, and this is the check that mattered most.**
`git diff --name-status ee0b36a..HEAD` touches `perry/` in exactly two ways:
`D perry/DECISIONS.md` and `A perry/evidence/2026-08/TASK-235-result.md`. **Zero
modifications under `perry/journal/`, `perry/design/`, `perry/decisions/` or any
existing `perry/evidence/` file.** Nothing was rewritten.

### Claim 3 — `mint_id` reads the ADR files alone ✅

On a throwaway project against the branch tree: `bootstrap` writes `decisions/`
and nothing else; ten `new` calls mint ADR-001…010 with `find . -type f` showing
no index at any point; the eleventh mints `ADR-011`. Minting with the index
absent, proved.

### Claim 4 — THE CONTRACT FINDING. Reproduced, and I rule it acceptable. ✅

Reproduced verbatim on the branch:

```
$ ls DECISIONS.md            → No such file or directory
$ rm decisions/ADR-011-eleven.md
$ perry-decide new twelve --title Twelve --type Process
perry-decide: wrote ADR-011                     ← REISSUED
```

**Ruling: "declared and pinned" is an acceptable close, and the framing that it
"made ADR deletion ordinary" does not survive measurement.** Four grounds:

1. **This row does not introduce reissue.** `main` reissues too (claim 5). What
   changed is determinism, and determinism is strictly better than a coin flip.
2. **This row adds no deletion path.** There is no `perry-decide purge`. An ADR
   leaves `decisions/` only when a human runs `rm`. Deletion is exactly as
   ordinary as it was.
3. **The detector that went was not a detector.** I measured what `main` had:
   ```
   MAIN, immediately after rm ADR-003:   indexed_without_file = ['ADR-003']
   MAIN, after ONE unrelated write:      indexed_without_file = []
   ```
   The signal had a one-command half-life. Removing a check that erases itself is
   this project's own house rule, not a loss.
4. **The fix genuinely needs a different lane shape.** `perry-task`'s rule rests
   on `.perry/events.jsonl`; `perry-decide` writes no events at all. Teaching it
   to is a row, not a hunk.

The pin — `test_a_deleted_adr_number_is_reissued_and_that_disagrees_with_purge` —
asserts the behaviour as it is and its failure message tells the next person what
to change and where. That is the correct shape for a declared disagreement.

**Condition on the PMO, not on the author:** § 9 says the board was not touched,
so neither the id-retirement row nor the gate-restoration row (§ 5 below) exists
anywhere except in prose. Both must be filed on merge or the declaration
evaporates.

### Claim 5 — TASK-214 was larger than filed. Reproduced on `main`. ✅

This is the strongest thing in the row and it holds exactly:

```
# main @ 208e0d3, throwaway project, ADR-001…013
$ rm decisions/ADR-013-d13.md
index still names ADR-013? 1
### WITHOUT an intervening write
$ perry-decide new fourteen …   → wrote ADR-014        (number remembered)

### WITH one UNRELATED write
$ perry-decide status ADR-001 --status archived
after an UNRELATED status flip, index names ADR-013? 0
$ perry-decide new fourteen …   → wrote ADR-013        ← REISSUED
```

Same starting state, opposite outcome, decided by an unrelated command. Reissue
on `main` was **non-deterministic**, not self-erasing. TASK-214 as filed described
a smaller defect than the one that was there, and this row closes the real one.

### Claim 6 — nine mutations. I ran **all nine**, not four. ✅

Every anchor line matched the author's table byte-for-byte before mutation
(`bin/perry-decide` 107/254/288/345/379/418/435/457, `viewer/parsers.py:2671`).
Every restore verified by `md5`. Run against a copy.

| # | Named test that went red | Total failures | Author claimed |
|---|---|---|---|
| 1 | `TestWriting.test_ids_are_minted_and_the_files_are_the_only_output` | 7 | +6 ✓ |
| 2 | `TestTheBootstrapThatDidNotExist.test_bootstrap_creates_the_directory_and_no_file` | 9 | +8 ✓ |
| 3 | `TestNothingWritesAnIndex.test_supersede_writes_no_index` | **1** | only ✓ |
| 4 | `TestNothingWritesAnIndex.test_status_writes_no_index` | **1** | only ✓ |
| 5 | `TestReadingIsTolerant.test_ids_are_minted_above_a_hand_added_file` | 5 | +4 ✓ |
| 6 | `TestListContract.test_the_three_index_keys_are_gone_and_stay_gone` | 3 / 2 modules | +2, 2 modules ✓ |
| 7 | `TestOneBinding.test_the_status_a_new_adr_is_born_with_is_one_the_schema_declares` | 2 | +1 ✓ |
| 8 | `TestPerrysOwnConfiguration.test_the_snapshot_off_perrys_own_project_root_is_not_empty` | 2 modules | 2 modules ✓ |
| 9 | `TestNothingIsRemovedOrRetyped.test_the_shipped_version_is_recorded_in_its_own_changelog` | **1** | only ✓ |

**Mutation 4's "red ALONE" verified across the whole suite, not just its module.**
I ran the complete 2892-test suite with `status` re-adding the index as `ADRS.md`:

```
98 modules · 2892 tests · 196.5s
test_decide_writer  FAIL: test_status_writes_no_index          ← the mutation
test_diagnose       ×2   (pre-existing)
test_kr_progress    ×1   (pre-existing)
test_host_support   ×1   (TestOpenCodeDispatchLimit — a load flake; green in my clean run)
```

Exactly one test in ~2,900 notices an index re-added under a different filename.
The claim is true, and mutation 9 is notable for the same reason: `2.0 → 2.1`
does **not** trip `test_the_major_version_did_not_move`, so the new standing
changelog test really is the only door, and a `--record` cannot open it.

### Claim 7 — `viewer/parsers.py`, and the merge advice for `coding/task-050-header-index` ✅

- **Three hunks, exactly as tabled**: `@@ -2550,50 +2550,129 @@`,
  `@@ -3860,7 +3939,6 @@`, `@@ -3934,7 +4012,7 @@`. Nothing else in the file
  differs from `ee0b36a`.
- **Zero header/table calls added.** Every `heading_is` / `split_row` occurrence
  on a `+` line is inside a comment. The removed `parse_decisions` contained
  exactly two live sites — `heading_is(line[3:].strip(), "Active")` and
  `cells = split_row(line)` — and both are inside the replaced section.
- **So this branch removes two header sites from `viewer/parsers.py` and adds
  none.** TASK-050's merge advice ("take the deletion") is safe to act on.
- **The change was mandatory.** `bin/perry-state:2225` builds `decisions.count`
  and `decisions.last` from `snap.adrs`. On the branch,
  `perry-state --json` reports `count: 10, last: ADR-010`. Mutation 8 (the
  reader returning nothing) is red in `test_parsers` and
  `test_project_root_resolution` — the silent-zero regression is guarded.
- `bin/perry-migrate:1189`'s `P.parse_decisions(text)` call was correctly removed
  with the signature change; no stale caller of the old signature survives.

### Claim 8 — the defect the full run caught, and the guard still fires ✅

`b57a34a` is one line in `SKILL.md`, no test touched. I reverted the wording on a
copy and the guard fires:

```
FAIL: test_no_procedure_hand_edits_a_tool_owned_file
AssertionError: ['  SKILL.md:75  [R1] OKR.md § Commitments …']  != []
```

The fix is a real wording change, not a loosened test, and `SKILL.md` is 20,439
bytes — 41 under the 20,480 cap.

---

## 4 · Green-for-the-wrong-reason sweep, and what rode along

**Every added test has a mutation that reddens it**, with one exception:
`TestListContract.test_a_project_that_never_bootstrapped_lists_cleanly_too`
asserts `([], 0, 0)` and would stay green under a reader that always returns
empty. It is weak on its own; mutation 8 covers that failure mode elsewhere, and
`test_the_shape_is_exact_and_every_key_always_present` carries
`assertTrue(d["decisions"])` against vacuity. Acceptable.

**No vacuous fixture.** The rewritten `test_shipped_vocabulary` guard carries
`assertGreaterEqual(len(templates), 2, "…this glob is now vacuous")`. The
rewritten `test_ownership` template test carries `assertTrue(entries, "no
decide-owned files[] entry at all")`. Both are the exact anti-mode this project
keeps catching, written in by the author.

**`GATE_OFF` is used to opt the decide fixture *out* of ADR-004, i.e. to reach
the code under test, not to hide a refusal.** Now that `perry-decide` takes no
gate at all, that line is inert in `test_decide_writer` — harmless, worth a
sentence to whoever tidies it.

**Rewritten tests were strengthened, not loosened.** `test_conformance §
TestAbsentIsNotNonConformant` gained an end-to-end `perry-task` refusal it did
not have; `test_i18n` now asserts a Chinese ADR title round-trips *and* en/zh
parity where it previously only counted rows; `test_ownership.test_decisions_specifically…`
went from a hardcoded `for path in (...)` loop to an exact-set assertion plus two
explicit "the index came back" guards. `test_goals_writer`'s `FOREIGN` list kept
its size by swapping `DECISIONS.md` for `design/DESIGN-001-x.md`.

**Contract fixtures were spliced, not regenerated.** `contract-key-parity.json`
is a **4-line diff**, all inside the `perry-decide/list` entry; `perry-task/list/1.18`
is untouched, so § 7 E's finding really was left for someone else's row.
`contract-shapes.json` removes the three keys and adds `semantics` + an
`empty_lists` block; no recorded type moved and no nested key was dropped. The
fixture's `empty_lists` is recorded metadata — `test_no_key_disappeared` reads
`empty_lists` from the **live** payload, not the fixture, so adding it loosens
nothing. One nit: the splice left `contract-shapes.json` with **no trailing
newline**.

**Ride-alongs across the 61 files: none that go beyond the deletion.**
`README`/`README_cn` drop one tree line each. `perry-goals`, `perry-knowledge`,
`perry-diagnose`, `packs/software-ops/architecture.md`, the two `work/state/`
templates: each is a one-name substitution or an added comment explaining why a
`DECISIONS.md` reference *stays*. `perry-migrate` loses a dead extractor. No doc
reworded beyond its subject, no test loosened, no template altered further.

**`.perry/conformance.md`** lost the `DECISIONS.md` declaration row. I checked
whether that was forced: with the row restored on a copy, `perry-conform status`
does not show it and `test_conformance` + `test_claims` stay green. So the edit
was **optional hygiene**, not required — defensible (a signed declaration for a
deleted file is stale), but it is a coding agent editing a user-declaration
artifact without being forced to. Flagging, not objecting.

**Fixture rebuilds (§ 7 A) are faithful.** `sample-project`'s ADR bodies carried
only `> Status: active` before; they now carry `Type`, `Date` and `Sunset`
transcribed from the index rows — including zh's `Sunset: 2026-09-01 前重议` and
en's `Sunset: revisit by 2026-08-01`. `witness-project`'s ADR already held every
field, so only its index was deleted. Nothing was lost in the rebuild, and § 7 A's
warning that a real project in that state has no migration step is a genuine,
correctly-scoped finding for another row.

---

## 5 · The one required correction

**`bin/perry-decide`'s justification for removing the ADR-004 gate ends with a
statement that is false, and it understates the size of a real safety loss.**

The comment (lines ~142–163) is right that the gate had to go — `DECISIONS.md`
was the only file this tool wrote with a `files[]` shape, `decisions/ADR-*.md` has
none, `verdict` returns `absent` for it and `absent` passes, so a gate on it could
not fire. Removing it rather than faking it is correct. Its final sentence is not:

> Until then `perry-decide` writes ADR bodies into an undeclared project, **which
> is what it already did for the bodies themselves; only the index write was ever
> gated.**

Measured on `git archive` copies of `main` and of `HEAD`, `PERRY_CONFORMANCE=enforce`,
nothing declared:

```
--- MAIN : bootstrap
perry-decide: wrote ['decisions/', 'DECISIONS.md']
--- MAIN : new (enforce, nothing declared)
rc=1
perry-decide: refused — DECISIONS.md already matches Perry's shape at version 2,
but no one has declared it. …
--- files written:  ./.perry/config.md  ./DECISIONS.md        ← NO ADR body

--- BRANCH : bootstrap
perry-decide: wrote ['decisions/']
--- BRANCH : new (enforce, nothing declared)
rc=0
perry-decide: wrote ADR-001
--- files written:  ./.perry/config.md  ./decisions/ADR-001-t.md   ← body written
```

On `main` the gate refused the **whole `new` command**, so no ADR body reached an
undeclared project either. There is no reachable `main` state where it did: before
`bootstrap` the file is `absent` and `new` refuses for a missing `decisions/`;
after `bootstrap` the file exists and undeclared and `new` refuses on the gate.
The clause "which is what it already did for the bodies themselves" is false in
every state.

**Why it matters more than a wording nit.** The comment's first paragraph is
honest — "this lane no longer takes a conformance gate, and that is a loss rather
than a simplification" — and § 7 B repeats it. But the closing clause is what a
future reader will use to size the follow-up row, and it tells them the change was
a non-event. It was not: `perry-decide new` went from **fully refusing** on an
undeclared project to **writing**. That is the whole of ADR-004's coverage for the
decide lane, and it is a consequence DESIGN-013 does not accept anywhere — § 4.1
accepts only the link surface.

**Fix:** delete or correct that clause so it says what was measured — that on
`main` the index's shape gated the entire command, ADR bodies included, and that
this branch leaves `perry-decide` writing into undeclared projects. Then file the
restoration row (giving `decisions/ADR-*.md` a `files[]` shape) with that
blast radius attached rather than the understated one.

This is a documentation correction on an otherwise thoroughly-verified row, which
is why it is a PASS condition and not a FAIL. Nothing depends on the clause
except the priority of the follow-up.

---

## 6 · checked / not-checked

**checked** — full `bash tests/run` on the branch tip (2892/3, quiet machine);
`perry-lint` (0 errors); `perry-decide list` and `--json` against the real
`perry/` state root; `perry-state --json` decisions payload; all nine mutations
on a copy, with `md5`-verified restores; mutation 4 against the complete suite;
two independent attempts to defeat `TestNothingWritesAnIndex`; the `b57a34a`
guard re-fired on the pre-fix wording; TASK-214's non-determinism reproduced on
`main`; the ADR-004 gate loss measured on both trees; the transient
`indexed_without_file` detector measured on `main`; every added/removed test diff
read; all 61 files' diffs read; fixture rebuilds compared field-by-field against
the deleted index rows; both contract fixtures diffed line-by-line; the whole
tree searched for a replacement index by name, by content and by writer.

**not checked** —
- **"Red ALONE across the whole suite" for mutations 3 and 9.** Verified alone
  within their own modules only. Not run suite-wide: the failure direction is
  harmless (more failures would strengthen, not weaken, the claim) and a full run
  costs ~8 min each.
- **`unittest discover` on either tree.** The spec's claim of 3 extra failures
  from a `test_risks_store` double-import artefact is still unconfirmed, by the
  author and by me.
- **§ 7 E's `perry-task/list/1.18` fixture drift** (126 vs 115 `emitted`). I
  confirmed the fixture was *not* touched, and `test_contract_key_parity` is green
  either way, so I did not independently re-derive the live numbers.
- **A full `bash tests/run` on `main`.** Another agent's run was in flight in
  `scratchpad/rv8-main-6c0d041` and re-running it would have contended for the
  machine that produced my branch number. My baseline comparison is the author's
  measured `ee0b36a` figure (2882/3), which my 2892/3 with an identical failure
  set corroborates.
- **The `viewer/parsers.py` merge against `coding/task-050-header-index`.** I
  verified the property that advice rests on (zero header sites added, both old
  sites inside the replaced block); I did not attempt the merge.
