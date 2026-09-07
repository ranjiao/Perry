# ADR-017 step 3 — `tests/`, classified rather than substituted

<!-- [[old-form]] · This document is ABOUT the pre-ADR-017 overall-KR form.
     Every `KR-O<n>.<m>` below is the artifact under discussion, not a live
     cross-reference. Per `reference/style.md`, it must not be migrated.
     Document-level marker, following the precedent set by
     `ADR-017-corpus-result.md` and `ADR-017-rename-result.md`; § 8 records
     why that is weaker than a same-line marker. -->

> Task: ADR-017 step 3 — the KR-grammar migration in `tests/`
> Date: 2026-09-07
> Base SHA: **`339f553`** ("ADR-017 step 2 merged: one grammar at both levels, and the template that undoes it")
> Branch: `worktree-agent-a9b45ac0cc9a60ae5`
> Result: **79 occurrences classified. 27 renamed, 52 left.** Of the 27, **2 are guarded by an assertion and both were mutated red**; the other 25 are prose or unguarded data, measured as such rather than assumed.

## 0. Base verification

The worktree was handed **`d49964e`**, **570 commits behind `main`**, with
**zero commits of its own** and a clean tree — the `TASK-381` defect again.
`main` was exactly `339f553`, so the branch was reset onto it:

    $ git rev-list --count main..HEAD   # commits of its own
    0
    $ git rev-list --count HEAD..main   # behind
    570
    $ git reset --hard 339f553
    $ git merge-base --is-ancestor 339f553 HEAD && echo OK
    OK

Steps 1 and 2 confirmed present at that base:

    $ grep -c 'KR-O[0-9]*\.[0-9]*' perry/OKR.md
    0

### Baseline, verified rather than trusted

Full suite in this worktree at `339f553`, `PERRY_PROJECT`/`PERRY_HOME` unset,
per `knowledge/verification/a-single-baseline-run-is-not-a-baseline.md` — the
whole suite, not the red modules alone:

    120 modules · 3448 tests · 104.5s · 8 workers
    ✗ 3 of 120 MODULE(S) red
    ✗ 4 of 3448 TEST(S) failed

The dispatch's arithmetic was right, and the four are the four named:

| module | test | owner |
|---|---|---|
| `test_contract_key_parity` | `TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable` | `TASK-335` |
| `test_contract_key_parity` | `TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness` | `TASK-335` |
| `test_diagnose` | `TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks` | `TASK-380` |
| `test_linkage_import` | `TestThisProjectsOwnImport.test_the_store_accounts_for_the_register_in_both_directions` | `TASK-383` |

`perry-lint --root .` — **0 errors, 29 warnings**, OKR store 0 drifted,
linkage store 123 records / **1 drifted** (the pre-existing `TASK-383` row).
Identical to step 2's recorded figures.

## 1. The count, reconciled

    $ grep -roE 'KR-O[0-9]+\.[0-9]+' tests/ | wc -l
    79
    $ grep -rlE 'KR-O[0-9]+\.[0-9]+' tests/ | wc -l
    27

**79 occurrences across 27 modules**, matching the dispatch exactly. Note the
27/27 coincidence is that — a coincidence. The occurrence count and the file
count are not the same measurement and several files carry more than one id on
a line (`test_i18n.py:190` carries four).

| class | count | fate |
|---|---|---|
| live reference | **17** | renamed |
| deliberate old-form fixture | **33** | left — and now the only load-bearing old grammar |
| historical quotation | **16** | left |
| incidental string | **11** | 10 renamed, 1 left — § 4 |
| `test_same_action_linkage.py` (`TASK-281` round 2's) | **2** | left, not mine |
| | **79** | **27 renamed / 52 left** |

    $ grep -roE 'KR-O[0-9]+\.[0-9]+' tests/ | wc -l    # after
    52

## 2. The finding that decided the largest class

**`tests/fixtures/sample-project/` is the OLD-grammar arm of step 1's own
test, and renaming it would have deleted step 1's evidence.**
`tests/test_overall_kr_grammar.py` binds `SAMPLE` to that fixture and then:

- `test_the_unmodified_old_grammar_project_still_lints_clean` lints it as-is;
- `test_the_old_grammar_still_resolves_through_perry_goals_list` asserts it
  resolves exactly `["KR-O1.1", "KR-O1.2", "KR-O1.3", "KR-O2.1"]`;
- `new_grammar_project()` **derives the NEW-grammar arm by rewriting SAMPLE at
  runtime**, and asserts `assertGreater(touched, 0, "the rewrite touched no
  file, so every assertion below would be about the OLD grammar wearing a new
  name")`.

A sweep over `tests/fixtures/` would have turned that guard's own premise
false: `touched` would be `0` and the module would fail — loudly, which is the
good case. The bad case is subtler and is the one the dispatch warned about:
the old-form arm and the new-form arm would have become the same assertion
written twice, and step 1's compatibility half would have stopped being tested
by anything while every test still passed.

This is the dispatch's rule made concrete — *a test asserting the new form is
accepted and one asserting the old form still parses are both correct today.*

## 3. Per-occurrence classification — all 79

Line numbers as measured at `339f553`. Every rename was applied to an
**enumerated `(file, line, expected-count)` list** with a per-line assertion,
never by substitution over a file; all 26 line assertions passed, which is
itself the check that the classification is addressed at the right text.

### 3.1 Live reference — renamed (17)

| file:line | n | the text | why live |
|---|---|---|---|
| `contract_key_parity.py:3` | 1 | *"The number `KR-O2.4` asks for and nothing computed"* | `O2-KR4` exists today, worded *"Contract-payload keys documented but not emitted…"* — the module computes that KR's metric |
| `contract_key_parity.py:471` | 1 | *"`KR-O2.4` read 0 with all fifteen unverified"* | same KR, present-tense claim about its number |
| `contract_key_parity.py:620` | 1 | `f"(KR-O2.4 metric: {gone + extra})"` | **emitted into the report** and asserted on — mutation A |
| `test_contract_key_parity.py:1` | 1 | module docstring, *"`KR-O2.4`'s number"* | the module's subject |
| `test_contract_key_parity.py:97` | 1 | *"`KR-O2.4` says 'all three contracts' and there are five"* | quotes the live KR's own wording, which `perry/OKR.md:76` still carries |
| `test_contract_key_parity.py:306` | 1 | *"`KR-O2.4` reads 12 or 0 for the same source tree"* | present-tense claim |
| `test_contract_key_parity.py:536` | 1 | *"`KR-O2.4` read 0 with all fifteen unverified"* | present-tense claim |
| `test_contract_key_parity.py:689` | 1 | `self.assertIn("KR-O2.4 metric: ", text)` | **the assertion over `:620`** — mutation A |
| `test_events_feed.py:471` | 1 | *"`KR-O2.4` would move for a reason that has nothing to do with the payload"* | a claim about the live KR's number moving |
| `test_knowledge_cards.py:197` | 1 | *"`KR-O5.1` reads 'lint live · 0 violations'"* | `O5-KR1`'s Metric/Target column is **verbatim** `lint live · 0 violations` |
| `test_knowledge_cards.py:210` | 1 | *"Perry declares `KR-O5.1` and has written no card"* | assertion **message** for the same live KR |
| `test_track_move.py:11` | 1 | *"why declaring one did not meet `KR-O1.1`"* | `O1-KR1` is *"Non-`project` modes running on live tracks"*; the sentence reasons about that live KR's semantics |
| `test_md_store.py:397` | 1 | *"the register `DESIGN-003 § 5.2` defines and `KR-O1.3` is about"* | `O1-KR3` is live (`perry/OKR.md:67`) |
| `test_md_store.py:504` | 1 | *"`okr.jsonl` already carries `KR-O1.1` twice"* | **measured**: `perry/okr.jsonl` carries `"id": "O1-KR1"` exactly twice today. Leaving it makes the comment wrong about the store — step 2's `DESIGN-015:154` case, inverted the same way |
| `test_md_store.py:602` | 1 | *"`okr.jsonl` already carries `KR-O1.1` twice, discriminated by `version`"* | same, in a docstring |
| `test_md_store.py:1226` | 2 | `before.replace("| KR-O1.1 |", "| KR-O1.1 |", 1)` | `Project` copies **this repo's own `perry/OKR.md`**, which step 2 renamed — the needle named a row that no longer exists. **This line is dead either way; see § 5** |

### 3.2 Deliberate old-form fixture — left (33)

Now the only place in the repository where the old overall grammar is
load-bearing.

| file:line | n | why it must stay old |
|---|---|---|
| `fixtures/sample-project/OKR.md:34,35,36,42` | 4 | `SAMPLE` — step 1's old-grammar arm (§ 2) |
| `fixtures/sample-project/PROJECT_STATE.md:13` | 1 | same fixture; `perry-lint` reads it whole |
| `fixtures/sample-project/design/DESIGN-001…:6` | 1 | same fixture, `Linked OKR` header |
| `fixtures/sample-project/design/DESIGN-002…:5` | 1 | same fixture, `Linked OKR` header |
| `fixtures/sample-project/phase/002-linkage.md:15,23,32` | 3 | same fixture; the `linked:` edges the old-form arm resolves |
| `test_overall_kr_grammar.py:49` | 1 | `OLD_OVERALL = "KR-O3.1"` — the constant naming the old form |
| `test_overall_kr_grammar.py:340` | 4 | `test_the_old_grammar_still_resolves_through_perry_goals_list` — the compatibility assertion itself |
| `test_overall_kr_grammar.py:360` | 1 | `assertNotIn("KR-O1.1", out, "an old-form id survived in a project that has none")` — asserts the old form is **absent** from the new-grammar copy; renaming it would invert the test |
| `test_parsers.py:200,202` | 2 | the phase **bullet** fallback reading `- KR-O1.1: the overall family, untouched`; its sibling `test_the_pre_migration_kr_bullet_is_not_read` is the `P-O1.1` half. This pair is the bullet path's both-forms coverage |
| `test_phase_kr_declared_once.py:393,396,399` | 3 | asserts `linked: "KR-O1.1"` against a `copytree(SAMPLE)` project — bound to the fixture above |
| `test_i18n.py:190` | 4 | asserts the **zh** fixture's ids — judgement, § 4.1 |
| `fixtures/sample-project-zh/OKR.md:34,35,36,42` | 4 | the zh twin — judgement, § 4.1 |
| `fixtures/sample-project-zh/phase/001-release-pipeline.md:50,51,68` | 3 | the zh twin's `Linked overall KR` column |
| `test_parsers.py:54` | 1 | `assertIn("KR-O1.1", ids)` over **`goals/state/OKR_TEMPLATE.md`**, which still mints the old form and is outside this step's scope — § 6 |

### 3.3 Historical quotation — left (16)

| file:line | n | why |
|---|---|---|
| `fixtures/live-state/md_store.before.py:166,406(×2),445` | 4 | **a frozen git blob.** `test_live_state_expectations.py` pins its SHA-256 (`test_the_fixtures_have_not_been_edited`) and compares it byte-for-byte against `git show` (`test_the_fixtures_are_what_git_holds`). It is `md_store.py` *as the repair found it*; editing it is editing history, and two guards say so |
| `test_risks.py:60(×2),81,317(×2)` | 5 | *"The two real projects surveyed while designing the columns. **Neither had migrated, both are quoted verbatim**, and both must keep parsing."* These are aiMark's board bullets. aiMark has **not** migrated — `ADR-017`'s own "What would reopen this" names it as an unmigrated consumer. Renaming would falsify a verbatim quotation of a foreign project |
| `test_phase_kr_declared_once.py:418,419` | 5 | *"`f15d234` populated `phase/001-linkage.md`'s eight `linked:` values from the retro score table … so all eight of phase 001's edges — `KR-O1.1`, `KR-O1.2`, `KR-O1.3`, `KR-O2.1`, `KR-O3.4` — were deleted"*. A dated report of what a past commit destroyed, in the spelling it destroyed |
| `fixtures/interrupted-adoption/.perry/adoption/2026-08-10-dossier.md:25,26` | 2 | dossier `content:` captured at `2026-08-10T10:14:00Z`, months before this ADR. `ADR-017`: *"A stale reference in an old row is history."* |

### 3.4 Incidental string — 10 renamed, 1 left (11)

The class the dispatch said to **decide and say which way**. My rule, applied
uniformly and stated so it can be argued with:

> Rename an incidental id when it sits in **a project fixture or store record
> Perry itself would mint today** — an `OKR.md` document, an `okr.jsonl`
> record, a linkage register — because those are examples of Perry's own data
> shape and shipping them in a dead grammar teaches the wrong shape. Leave it
> when it is a quotation, a frozen artifact, bound to a fixture that must stay
> old, or when the old spelling is the point being made.

| file:line | n | decision | why |
|---|---|---|---|
| `test_purge.py:322,326` | 2 | **rename** | a synthetic `okr.jsonl` record and the assertion naming it (`okr.jsonl KR-O1.1.linked`). A store record — mutation B |
| `test_row_integrity.py:796,802` | 2 | **rename** | `STORED_OKR`'s table row and `STORED_KR_RECORD`'s `id`, a document/record pair — mutation C |
| `test_md_store.py:519` | 1 | **rename** | `OBJECTIVE_FORMS`, a synthetic `OKR.md` — mutation D |
| `test_one_line_break_rule.py:259` | 1 | **rename** | a scaffolding `OKR.md` inside a state fixture; the module is about line-break refusals — mutation E2 |
| `test_linkage_import.py:82` | 1 | **rename** | `linked: "KR-O2.1"` in `FIXTURE_REGISTER`. It also **stops dangling**: `O2-KR1` resolves against the live OKR and `KR-O2.1` no longer does — mutation E1 |
| `fixtures/witness-project/OKR.md:31` + `phase/001-linkage.md:9,22` | 3 | **rename** | a whole second live project fixture, read by `contract_key_parity` today. Not dated history, not bound to step 1's grammar test. Checked first that the parity **baseline JSON holds no ids** (it does not), so nothing recorded pins the old spelling — mutation E3 |
| `test_phase_kr_declared_once.py:425` | 1 | **leave** | *"a shape check would accept `KR-O9.9`"* — a deliberately **nonexistent** id illustrating shape-acceptance versus resolution. Step 1 widened the shape check to accept **both** forms, so the sentence is still true as written; and it sits inside the historical paragraph at `:418`–`:419`. The old spelling is the point |

### 3.5 `test_same_action_linkage.py` — left, not mine (2)

`TASK-281` round 2 owns this file, `bin/lib/__init__.py` and `bin/perry-task`'s
`--kr` path. Its two occurrences are:

    tests/test_same_action_linkage.py:307        linked: "KR-O2.3"
    tests/test_same_action_linkage.py:353        …, "linked": "KR-O2.3"}) + "\n"

They are a register `linked:` value and the matching store record — the exact
shape that round is changing — and renaming them under a concurrent round
would have collided in the one field both rounds touch. **The file is
byte-untouched** (`git diff --name-only` does not list it). It is the reason
`tests/` will still hold 2 old-form occurrences after that round unless it
handles them, and it should.

## 4. Two judgements worth arguing with

### 4.1 The Chinese twin stays old-form with the English one

`test_i18n.py:190` and `fixtures/sample-project-zh/` (11 occurrences together)
are **not** pinned by step 1's test — only the English `SAMPLE` is. I left them
anyway, for three reasons, and this is the call in this step I hold least
tightly:

1. The pair exists so the *same* project in two languages yields the same
   payload shape. Migrating one half would introduce an asymmetry no test
   guards and that a later reader would reasonably mistake for a bug.
2. `test_i18n` exercises an old-form project through the **Chinese heading
   matchers** — a reader path `test_overall_kr_grammar` does not cover. That is
   real both-grammars coverage and renaming would silently retire it.
3. `test_diagnose.py:2682` iterates `("sample-project", "sample-project-zh")`
   as a pair, and `test_md_store.py:440` reads both `OKR.md`s in one loop.

The counter-argument, stated fairly: nothing *asserts* the zh fixture must be
old-form, so a future round may migrate it with the English one when step 1's
arm is retired. It should move as a pair or not at all.

### 4.2 No `[[old-form]]` markers were added to the 52 survivors

`reference/style.md` requires a same-line `[[old-form]]` on a deliberately
quoted **obsolete** id. I added none, deliberately:

- **Every existing `[[old-form]]` marker in `tests/` is on `P-O1.1`** — the
  dead phase form — across `test_cadence.py` (4), `test_parsers.py` (2),
  `test_overall_kr_grammar.py` (2), `test_md_store.py` (1),
  `test_linkage_task_exists.py` (1). Not one is on `KR-O<n>.<m>`. The
  convention in this directory already reserves the marker for the form that
  is **dead**.
- The old overall form is **not dead**: step 1 deliberately kept it parsing,
  and § 2's fixtures are live inputs exercising that, not quotations of
  something obsolete. Marking them would assert an obsolescence that ADR-017
  step 1 specifically declined to create.
- Markers cannot go in the fixture data at all. `[[old-form]]` inside a KR
  table cell of `sample-project/OKR.md` changes what the parser reads.

**This leaves a real gap and I am naming it rather than closing it**: a
same-line grep over `tests/` does not distinguish deliberate survivors from
oversights. It becomes closable only when the old overall form is actually
retired — which is a decision after this one, not inside it.

## 5. Mutation — and two of the four came back green

Per `knowledge/verification/mutate-every-fix-and-distrust-green.md`. Of the 26
lines changed, **most are docstrings, comments and assertion messages, which no
assertion reads** — mutating those is vacuous by construction. The lines a test
actually reads were mutated one at a time, each run **module-alone with
`tests/__pycache__` cleared first** (step 2's stale-`.pyc` trap), and each file
restored and `cmp`-checked byte-identical.

Reference points, unmutated, after the rename: `test_contract_key_parity` 2
failing (the baseline pair), `test_purge` 0, `test_row_integrity` 0,
`test_md_store` 0, `test_linkage_import` 1 (the baseline `TASK-383` red),
`test_one_line_break_rule` 0.

| # | site | mutation | result |
|---|---|---|---|
| **A** | `contract_key_parity.py:620` producer ↔ `test_contract_key_parity.py:689` assertion | `(O2-KR4 metric:` → `(O9-KR9 metric:` in the **producer only** | **RED — 2 → 3.** The new red is exactly `TestWhatCouldNotBeComparedIsNamed.test_the_report_prints_the_file_count_and_a_total`. Reverted → 2. The renamed assertion still reads the emitted id |
| **B** | `test_purge.py:322` record ↔ `:326` assertion | record `id` → `O9-KR9`, **assertion left** | **RED — 0 → 1**, `TestItRefusesALiveReference.test_the_goals_store_linked_field_is_refused`. Reverted → 0 |
| **C** | `test_row_integrity.py:796` ↔ `:802` | record `id` → `O9-KR9` (document row left) | **GREEN** |
| **C2** | same | document row → `O9-KR9` (record left) | **GREEN** |
| **D** | `test_md_store.py:519` | `\| O1-KR1 \|` → `\| ZZ-Q9 \|` (not even a valid id) | **GREEN** |
| **E1** | `test_linkage_import.py:82` | `linked` → `O9-KR9` | **GREEN** (only the baseline `TASK-383` red) |
| **E2** | `test_one_line_break_rule.py:259` | id → `O9-KR9` | **GREEN** |
| **E3** | `witness-project` all 3 ids | → `O9-KR9` | **GREEN** (only the baseline pair) |

**Two guarded assertions, both proven. Six green mutations, and the green is
the finding, not a pass.** What each green means:

- **C/C2**: `TestNoRowIsSplitForAStore` counts **which reader functions are
  called** (`split_row`), never a cell value. The document row and its store
  record can disagree — in either direction — and nothing notices. The ids
  there are genuinely decorative.
- **D**: the `OBJECTIVE_FORMS` tests are about **Objective heading** forms; the
  KR row is scaffolding. A syntactically invalid id passes.
- **E1/E2/E3**: unguarded fixture data, as classified.

**So six of my 27 renames are unverifiable by mutation.** They are not
regressions — those ids were equally unguarded before I touched them, and the
suite is no redder — but I will not claim they are *verified*. The dispatch's
bar (*"a renamed id in a test that no longer fails when its subject breaks is
worse than the old grammar"*) is met in the sense that none of them got worse;
it is **not** met in the sense that these six sites never measured their id at
all. That is a pre-existing property of those tests and a candidate row of its
own, not something this rename introduced or can fix.

**Separately, one dead line found and not fixed here.** `test_md_store.py:1226`
reads `before.replace("| KR-O1.1 |", "| KR-O1.1 |", 1)` — needle and
replacement are the **same string**, so the call is an identity no-op. It is
doubly dead now, because `Project` copies this repo's `perry/OKR.md` and step 2
renamed those rows, so the needle matched nothing either. All the drift the
test measures comes from the second `.replace`. I renamed the needle so it
stops naming a row that does not exist, and **filed the dead call separately**
rather than inventing a mutation for it inside a grammar migration. The
identical dead line at `fixtures/live-state/md_store.before.py:406` must
**not** be repaired — it is the sha256-pinned frozen blob.

## 6. Suite after the change

Full suite, same worktree, `__pycache__` cleared, `PERRY_PROJECT`/`PERRY_HOME`
unset:

| | baseline (`339f553`) | after |
|---|---|---|
| modules | 120 | 120 |
| tests | 3448 | 3448 |
| red modules | 3 | **3 — the same three** |
| failed tests | 4 | **4 — the same four, by name** |

`test_contract_key_parity` (2), `test_diagnose` (1), `test_linkage_import` (1).
**Nothing traded, nothing repaired, nothing new.** No test needed updating to
keep the suite level — unlike step 2, which broke and repaired one.

`perry-lint --root .` — **0 errors, 29 warnings**; OKR store 0 drifted;
linkage store 123 records / 1 drifted (`P003-O3-KR2`, the `TASK-383` row).
Unchanged from baseline and from step 2.

`git diff --name-only` lists **12 files, all under `tests/`**; nothing in
`bin/`, `viewer/` or `goals/` was touched. 26 lines changed, each a
`KR-O<n>.<m>` → `O<n>-KR<m>` substitution and nothing else.

## 7. The two guards the dispatch named — measured, not predicted

### `kr-id-legacy-form` still fires

`LEGACY_KR_ID_RE` is `\bP-O\d+\.\d+\b` — the dead **phase** form, disjoint from
`KR-O\d+\.\d+` by construction, so nothing in this step could reach it. Checked
anyway, on a copy in `/tmp`, with a control:

    $ python3 bin/perry-lint --root /tmp/…/proj          # control, unplanted
    exit=0 ; kr-id-legacy-form occurrences: 0

    $ printf '\n| P-O1.1 | A stray legacy id | 1 | - |\n' >> …/phase/002-linkage.md
    $ python3 bin/perry-lint --root /tmp/…/proj
    exit=1
    ✗ phase/002-linkage.md:64 [kr-id-legacy-form] P-O1.1 — the pre-TASK-180
      phase-KR form, whose phase is not in the id. …

**Fires, and refuses** (exit 1, not merely reported). The control run proves
the finding is caused by the planted id and not standing in the fixture
already. `test_overall_kr_grammar.TheDeadPhaseFormIsStillRefused` is green in
the full run above, which is the in-suite half of the same check.

### Both overall grammars still parse

    $ perry-goals list --root tests/fixtures/sample-project --level overall --json
    ['KR-O1.1', 'KR-O1.2', 'KR-O1.3', 'KR-O2.1']          # OLD, untouched

    $ perry-goals list --root /tmp/…/newg/proj --level overall --json
    ['O1-KR1', 'O1-KR2', 'O1-KR3', 'O2-KR1']              # NEW, rewritten copy
    $ perry-lint --root /tmp/…/newg/proj → exit=0, 0 bad-id

Both resolve, both lint clean, same count. Step 1's property survives step 3 —
which is exactly what leaving the 33 old-form fixtures buys.

## 8. What I did NOT check

- **I did not verify that each renamed live reference points at the *right*
  KR.** I verified each renamed id **resolves** and, for `O2-KR4` and `O5-KR1`,
  that the KR's own wording in `perry/OKR.md` matches what the test says about
  it. I did not audit `O1-KR1` and `O1-KR3` the same way beyond confirming they
  exist and are about the subject the docstring claims. Same gap the corpus
  round and step 2 both declared.
- **Six of the 27 renames are unverifiable by mutation** (§ 5). I measured that
  rather than assuming it, but measuring it does not fix it.
- **I did not fix the six sites that never measured their id.** `C`, `C2`, `D`,
  `E1`, `E2`, `E3` are tests whose fixture ids are decorative. Adding
  assertions there is a test-quality change, not a grammar migration, and
  conflating them would hide the rename inside a larger diff.
- **I did not close `goals/`'s dependency**, and step 3 cannot. `goals/state/OKR_TEMPLATE.md`
  still carries 6 old-form ids, which is *why* `test_parsers.py:54` had to stay
  old-form: it asserts what the template contains. **That assertion is the one
  live reference in `tests/` I could not rename**, and it will need renaming in
  the same commit that moves the template. Until then Perry keeps minting
  old-form ids into freshly-initialised projects — step 2's § 7 raised this and
  it is still open.
- **I did not add `[[old-form]]` markers** (§ 4.2), so a same-line grep over
  `tests/` still cannot separate deliberate survivors from oversights.
- **I did not touch `test_same_action_linkage.py`** and did not coordinate with
  `TASK-281` round 2. Its 2 occurrences are unclassified by me; I read them
  only far enough to confirm they are a `linked:` value and its store record.
- **I did not re-measure the corpus outside `tests/`.** Step 2's census of 421
  survivors is taken as given.
- **I did not check aiMark.** `test_risks.py` quotes its unmigrated board and
  that quotation is now load-bearing evidence that a real consumer still writes
  the old form.
- **I did not run the suite more than once per state.** Baseline and after are
  one full run each; the four reds were identical by name across both, and each
  mutation was re-run module-alone, but I did not repeat the full suite to test
  for flake beyond that.

## 9. References

- `perry/decisions/ADR-017-one-kr-id-grammar.md` — the decision and its `## Changes`
- `perry/evidence/2026-09/ADR-017-rename-result.md` — step 2, the data rename
- `perry/evidence/2026-09/ADR-017-corpus-result.md` — the per-occurrence classification method
- `perry/evidence/2026-09/ADR-017-readers-round2-result.md` — step 1, and the `goals/` dependency
- `reference/style.md` — the `[[old-form]]` rule
- `perry/knowledge/verification/mutate-every-fix-and-distrust-green.md`
- `perry/knowledge/verification/a-single-baseline-run-is-not-a-baseline.md`
