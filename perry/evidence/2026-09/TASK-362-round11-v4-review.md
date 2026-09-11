# TASK-362 — V4 round 11

**Reviewed at `7f43a11c`** (`Merge task-362-blank-rung`), which is where the
round-10 fix landed and what my worktree is checked out at. Main has since
moved to `fe0292fb`, four merges ahead; `git diff 7f43a11c fe0292fb` over the
four files this round touches — `bin/perry-state`, `bin/perry-task`,
`tests/test_compact_payload.py`, `tests/test_task_writer_core.py` — is **empty**,
so this verdict carries to `fe0292fb` for the code it judges.

**Charge:** criterion 13 and the fix that answered round 10's FAIL on it, plus
criterion 5, which round 10 did not reach. Criteria file:
`perry/evidence/2026-09/DESIGN-016-spec.md`. The other twelve criteria belong
to rows already closed and I did not judge them.

`perry-lint --reviews` reports this row `review-rounds-exhausted`. That is a
reason to be exact about what I did and did not establish, not a licence to
find something. **Both criteria are met.** What I found that is real is filed
below as rows, and § 3's `not-checked` line says what I could not reach.

## 0 · Baseline, in this tree

`bash tests/run` at `7f43a11c`, worktree
`/Users/bytedance/proj/Perry/.claude/worktrees/agent-aad246401ebf6d1e8`:

```
124 modules · 3561 tests · 3 modules red · 4 tests failed
  test_contract_key_parity  TestAWitnessProjectMakesAnEmptyCollectionObservable
                            .test_without_the_witness_the_four_are_unobservable
  test_contract_key_parity  TestTheWitnessedKeysRedden
                            .test_the_same_mutation_is_silent_without_the_witness
  test_resume               TestStaleRuns.test_a_fresh_run_is_not_stale
  test_diagnose             TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks
```

Exactly the four the charge names — the three from the spec's Baseline section
plus TASK-436's permanent dangling `USER-920`. `test_compact_payload` and
`test_task_writer_core` are both green.

**Every mutation below was line-anchored** (a helper that replaces lines
`[start,end]` and prints the block it removed — never `str.replace`), and every
restore was verified with `bin/perry-restore-check 7f43a11c <path>` against
`git show`, not against a snapshot. `__pycache__` was cleared and two seconds
waited past the second boundary before each run.

**One correction to the record.** I was stopped by a rate limit with M9 applied
and left it stranded in the tree; the coordinator reverted it and told me. I
had run **no measurement** between applying M9 and being stopped, so nothing
earlier is contaminated. I re-applied M9 deliberately afterwards and it is
reported below. The tree was verified byte-identical to `7f43a11c` before the
criterion-5 measurements and again at the end.

## 1 · Criterion 13 — the vocabulary equals the store and the schema

> `perry-state --compact` carries tracks, their modes, and the stages legal on
> each, and those values equal what `.perry/config.jsonl` and `schema/` hold.

### 1.1 The criterion's own test, and whether its guards do anything

`tests/test_compact_payload.py § TestItCarriesTheVocabulary §
test_every_cell_equals_the_store_up_to_how_a_blank_is_spelled` carries three
guards. I broke each one separately rather than reading them.

| # | mutation | result |
|---|---|---|
| M4 | `bin/perry-state:640-641` — `shown()` returns `col(key)`, so the blank marker stops being put back | **RED** at line 600, the `blanks_seen` guard: *"9 track cells are blank in the store and --compact published every one of them unchanged: `track_from_record` has stopped putting the blank marker back, which moves the payload"* |
| M5 | `bin/perry-state:640-641` — `shown()` returns `col(key) or "V9"`, a blank published as a **real** value | **RED** at line 584, the blank-vs-real guard. So the tolerance distinguishes two spellings of nothing from a genuine disagreement; it is not a blanket "differences are fine" |
| M6 | `bin/perry-state:633-635` — `col()` appends `x` to every non-empty cell, so a **declared** value is published differently | **RED** (also reddens `test_the_stages_legal_on_a_track_are_in_it`) |
| M7 | `tests/test_compact_payload.py:533-540` — the fixture declares **every** track field, so the store holds no blank | **RED** at line 599: *"this fixture declares no blank track cell, so the tolerance above was never exercised"* |

So, to the three questions put to me: the test **does** distinguish a blank
spelled two ways from a real disagreement (M5, M6); it **cannot** be satisfied
by a payload that never normalises (M4); and it **does not** pass vacuously on
a fixture with no declared blank (M7). All three guards are load-bearing.

### 1.2 The `schema/` half — `stage_list` for a track declaring no stages

This is the half of criterion 13's sentence that the store comparison does not
reach, and there are **two producers** of `stage_list`: the declared branch
computes `split_stages(stages) or default_stages_for(mode)`
(`bin/perry-state § track_from_record`), while the implicit branch carries
`stage_list: []` outright (`bin/perry-state:313 § DEFAULT_TRACK`). Two
producers of one value is the shape round 10's finding had, so I measured it
rather than reasoning about it.

Measured on `--compact`, a declared track with a blank `stages` cell, per mode:

```
project    stage_list=[]                                              schema=[]                      MATCH
pipeline   ['brief','draft','review','approved','published']          same                           MATCH
queue      ['new','triaged','in_progress','resolved']                 same                           MATCH
inquiry    ['open','researching','answered']                          same                           MATCH
```

and the same project said two ways — a declared `main`/project track with every
cell blank, against a project declaring no track at all — publishes
`stage_list: []` from both branches. **They agree.** They agree because
`project` mode's `default_stages` is `''` and `DEFAULT_TRACK`'s mode is always
`project`, which is a coincidence the code does not state; see ROW-5.

Pinned by a test, not only by my measurement:

| # | mutation | result |
|---|---|---|
| M9 | `bin/perry-state:543` — `default_stages_for` returns the schema's stages **reversed** | **RED**, full suite: `test_wip_and_stages.TestTheReaderAndTheWriterAgreeAboutStages.test_a_blank_stages_cell_reports_the_modes_vocabulary` and `test_track_move.TestBothDirectionsOfTheFieldQuestion.test_a_staged_non_queue_destination_gets_stage_since_and_no_arrived` — 6 of 3561 failed against the baseline's 4 |

### 1.3 The round-10 fix, and the four tests that pin it

`bin/perry-task § cmd_done` now routes the track's `default_rung` through
`lib.is_blank_cell` instead of a bare `or`.

| # | mutation | reddened |
|---|---|---|
| M1 | `bin/perry-task:4269-4272` → the pre-fix bare `or` | `test_every_blank_spelling_falls_back_to_the_modes_default`, `test_what_done_stamps_is_what_done_would_accept`, `test_declaring_the_track_changes_nothing_a_row_carries` (3 of 4) |
| M2 | the mode default wins **unconditionally** | `test_a_declared_rung_still_beats_the_modes_default` — and only that one |
| M3 | the blank rule narrowed to `("", "—")`, so the other 16 spellings leak | `test_every_blank_spelling_falls_back_to_the_modes_default` — and only that one |

**No mutation came back green.** The class has **four** tests, not five; the
commit's "Five tests, in two places" counts the compact-payload one, and is
right.

**What each test can and cannot distinguish**, enumerated rather than sampled:

| test | reddens on | cannot distinguish |
|---|---|---|
| `test_every_blank_spelling_falls_back_to_the_modes_default` | M1, M3 | a fallback that wins unconditionally (green under M2) — which is why the next test exists |
| `test_a_declared_rung_still_beats_the_modes_default` | M2 | the blank direction entirely (green under M1 **and** M3) |
| `test_what_done_stamps_is_what_done_would_accept` | M1 | **only exercises `—`**, so every other blank spelling is out of its reach (green under M3); and a wrong-but-*valid* rung. Its stated property is broader than what it runs — see ROW-1 |
| `test_declaring_the_track_changes_nothing_a_row_carries` | M1 | see below — its reach is one cell, not the record |

The last one claims comparing every cell "is what makes this catch the next
consumer instead of only this one". Measured: under M1 the two records differ
in **`verification` and nothing else**, and in the configuration the test runs
(project mode, track `main`, every cell blank) `verification` is the only cell
a track-cell consumer writes — `stage` is `""` in project mode and every other
cell is constant or comes from the row's own arguments. The test is not wrong;
its **stated reach** is. ROW-4.

### 1.4 Is the `main`-only isolation honest?

The class names its track `main` in every mode to stay clear of TASK-435. I
confirmed TASK-435 is real and that the isolation is not hiding a case the fix
gets wrong. Measured on throwaway temp projects:

```
A  project-mode track 'ops', default_rung V5, added --track ops
   → row stores track='main', closes at verification='V3'      ← TASK-435
B  queue-mode track 'ops', BLANK default_rung, added --track ops
   → row stores track='ops', closes at verification='V2'       ← the fix works
C  queue-mode track 'ops', default_rung V6, added --track ops
   → row stores track='ops', closes at verification='V6'       ← declared wins
```

A is TASK-435 exactly: `cmd_add` drops the track on a project-mode track, the
row stores `main`, and the close reads the implicit track's cell. The **rung
selection is correct given the track it was handed** — the defect is upstream,
in `cmd_add`. B and C show the fix is name-agnostic and works on a track that
is not `main`. **The isolation is honest.** What it costs is that no test in
the class runs a non-`main` track name; the code does not branch on the name,
and B and C cover it by measurement.

### 1.5 Verdict on criterion 13

**Met.** Both halves of its sentence are pinned by named tests that go red
when the code that implements them is broken — the store half by M4/M5/M6/M7,
the schema half by M9 — and the fix that answered round 10 is pinned by
M1/M2/M3 with the negative and positive directions separated. Nine mutations
on this criterion, none green.

## 2 · Criterion 5 — `--compact` is a strict projection

> A standup reads its state for under 5,000 tokens. `perry-state --compact` is
> a strict projection of `--json`: every key it emits carries the same value as
> the corresponding key in `--json` from the same process. `SKILL.md` step 3
> calls it.

Three sub-claims. The grading table marks 5 **FAIL**, and its stated harm — *"a
key result at 43% published as 100%, and the reader cannot tell"* — is the
projection, not the size.

**(c) `SKILL.md` step 3 calls it.** `SKILL.md:130`, inside step 3 "Compute the
state — one call", is `"$PERRY_HOME/bin/perry-state" --compact`. Met.

**(b) The projection.** I did not re-walk rounds 4–9; I wrote an independent
check and ran two representative mutations.

The check reads only `STATE.COMPACT` (the field *list*, because the question is
whether the values agree, not which fields exist) and supplies its own dotted
walker and its own reimplementation of all six projection kinds, then compares
`--compact` against the projection of `--json` on **real** projects rather than
a scratch fixture:

```
Perry's own state          52 declared fields compared · 0 disagreements · 0 undeclared top-level keys
tests/fixtures/sample-project   52 declared fields compared · 0 disagreements · 0 undeclared top-level keys
```

(`generated_at` excluded: two invocations, two honest clocks.)

| # | mutation | reddened |
|---|---|---|
| C5-M1 | `bin/perry-state:2367-2368` — `project_value` returns `len(value) + 1` for `count`. **This is round 4's mutation, which was green then** | **RED**, 8 named tests, including `test_the_six_kinds_are_checked_against_a_second_opinion`, `test_a_scalar_is_carried_verbatim_and_a_list_is_counted` and `TestEveryProjectionKindIsFedDataThatDistinguishesIt.test_each_kind_maps_its_input_to_the_declared_output` |
| C5-M2 | `bin/perry-state:2298-2300` — `linkage.objectives` repointed at `phase.objectives`. **Round 6's worst case** | **RED**, 4 named tests, including `TestTheFullFixtureReachesTheDarkPaths.test_the_numbers_are_the_ones_the_full_payload_carries`, which is the real-data one |

Both of the defects the criterion's own history says were once invisible are
now caught by named tests. Met.

**(a) Under 5,000 tokens.** Holds by measurement, and is **not pinned as an
absolute bound** by any test.

```
perry-state --json     on Perry's own state   247,668 bytes
perry-state --compact  on Perry's own state    11,305 bytes   ≈ 2,800 tokens
```

Comfortably under 5,000, and a 22× cut. What pins it is
`TestItIsSmallerByTheOrderOfMagnitudeThatWasThePoint`, and it asserts a
**relative** fraction — `len(narrow) < len(full) / 3` — plus the growth
property (twelve more rows cost under 200 bytes) and the control that the row
count is still reported. A relative bound passes at 80,000 bytes if `--json` is
250,000. Filed as ROW-3, not a FAIL: § 0 puts a cost below the line, an
oversized payload announces itself to whoever reads it, and the criterion's own
grading row names the projection as the harm.

**Verdict on criterion 5: met.**

## 3 · What I found, and why none of it is a FAIL on this row

### ROW-1 — `done` stamps a rung its own validator refuses, in a shape the fix did not close

**This is the substantive finding of the round, and it belongs to a new row.**

`bin/perry-config § cmd_track` writes `--default-rung` with **no validation**
(line 199/207: `store.stored_value(v)` and straight into the record), and
`bin/perry-task § cmd_done:4269-4272` treats any non-blank cell as a rung. So
the value goes in through Perry's own declared writer and comes out stamped on
a closed row. Measured end to end on throwaway temp projects, no hand-editing:

```
perry-config track main --default-rung banana   → exit 0, store holds 'banana'
perry-task   done <id> --evidence ...           → exit 0, verification='banana'
perry-task   done <id> --rung banana            → exit 1, "rung 'banana' is not
                                                   one of V1/V2/V3/V4/V5/V6"
   perry-lint → exit 1 (bad-enum on the config)

perry-config track main --default-rung V0       → exit 0, store holds 'V0'
perry-task   done <id> --evidence ...           → exit 0, verification='V0'
perry-task   done <id> --rung V0                → exit 1, "V0 is 'asserted' — it
                                                   is the name for what is being
                                                   refused, never a rung a row
                                                   may carry"
   perry-lint → exit 0                          ← nothing catches this one
```

Eight spellings tested; all eight were stamped verbatim and all eight refused
from a caller. `V0` is the sharp one: it is a legal value of the config enum,
so `perry-lint` passes it clean, and the row ends up carrying the one rung the
writer names as *"what is being refused"*.

This is verbatim the sentence
`TestADeclaredBlankRungIsNotARung` says it pins — **"what the writer stamps,
the writer accepts"** — and it is false for every input the class does not run,
because all four of its cases declare a **blank** rung.

**Why it is a row and not a FAIL on TASK-362.** Criterion 13 is that
`--compact`'s track values equal the store. For `banana` the store holds
`banana` and `--compact` publishes `banana` — **criterion 13's equality holds**,
and I measured that. Round 10's FAIL had a chain into criterion 13: the
criterion's own deliberate normalisation *manufactured* `—` out of `""`, and a
consumer read the manufactured value. This finding has no such chain — it is
identical before and after the fix, and it would exist if the payload
normalised nothing at all. `review.md § 1`: *"A round may only widen the bound
by filing a new row, never by re-opening this one."* Its fix sites are
`perry-config § cmd_track` and `perry-task § cmd_done`, neither of which
criterion 13 reaches.

### ROW-2 — the fix turned one silent wrong write into a traceback

`bin/perry-task:4270` raises `KeyError` when a **declared** track's `mode` is
not in `schema.work_modes.modes`. Measured both ways on a temp project (add on
a valid mode, then edit `.perry/config.jsonl` to `mode: kanban`, then `done`):

```
post-fix (7f43a11c)  done → exit 1, Traceback, KeyError: 'kanban', nothing written
pre-fix  (bare `or`) done → exit 0, row written with verification='—'
```

Reported, not counted against the row: criterion 10b grades a traceback **ROW**
(*"ugly and loud. A crash is not a silent wrong answer"*), the same store shape
**already** tracebacks at `add` (`bin/perry-task:7706 § default_stages`,
pre-existing and untouched by this fix), and refusing is strictly better than
the pre-fix behaviour of stamping `—`.

### ROW-3 — criterion 5's token bound is pinned only relatively

`TestItIsSmallerByTheOrderOfMagnitudeThatWasThePoint` asserts
`len(narrow) < len(full) / 3`, never an absolute ceiling. Measured today at
11,305 bytes (~2,800 tokens), well inside the criterion's 5,000. § 2 above.

### ROW-4 — a test docstring overstates its reach

`test_declaring_the_track_changes_nothing_a_row_carries` claims comparing every
cell of the record "is what makes this catch the next consumer instead of only
this one". Measured: `verification` is the only cell that differs under M1 and
the only cell that **can** differ in the configuration the test runs. A
documentation defect (`review.md § 2`: *"a comment … misstates something → file
a row, never a FAIL on this one"*), not a broken test — M1 reddens it.

### ROW-5 — two producers of `stage_list` agree only by coincidence

`DEFAULT_TRACK` (`bin/perry-state:313`) hardcodes `stage_list: []`;
`track_from_record` computes `split_stages(stages) or default_stages_for(mode)`.
They agree today only because `project` mode's schema `default_stages` is `''`
and `DEFAULT_TRACK`'s mode is always `project`. If `project` mode ever gains
default stages, the declared and implicit `main` diverge and criterion 13's
"the same nothing, said two ways" defect returns in the stages cell. Nothing
asserts the two producers agree. Latent; no defect today (measured, § 1.2).

### ROW-6 — the criterion-13 test's field list overstates by two

`test_every_cell_equals_the_store_up_to_how_a_blank_is_spelled` iterates seven
`fields`, but `--compact`'s `fields` projection never carries `spine` or
`stages`, so `if field not in shown: continue` always skips those two and the
comparison runs over five. Its `declared_blanks` guard counts 9 blanks across
all seven store fields while `blanks_seen` can reach at most 6, so the failure
message names a denominator the loop never uses ("9 track cells … published
every one of them unchanged"). Both guards still fire correctly (M4, M7).
Cosmetic.

## 4 · Anything green that should not have been

**Nothing.** Eleven mutations across `bin/perry-task`, `bin/perry-state` and
one test fixture; every one reddened a named test.

One mutation must not be miscounted as a green. **M8** —
`bin/perry-task:3359-3362`, a simulated "sixth consumer" making `stages_of`
read the raw `stages` cell by truthiness — left the suite green, but I checked
the payload before concluding anything and it was a **no-op**: `stages_of` is
reached through `stage_list`, and in project mode the row's `stage` cell is
`""` either way, so the mutation changed no compared byte. An unfired mutation
is not evidence. What it did surface is ROW-4.

## 5 · Restore

```
bin/perry-restore-check 7f43a11c bin/perry-state bin/perry-task \
    tests/test_compact_payload.py tests/test_task_writer_core.py
  ✓ bin/perry-state                matches 7f43a11c (e777d914b532…)
  ✓ bin/perry-task                 matches 7f43a11c (ff4d553ac902…)
  ✓ tests/test_compact_payload.py  matches 7f43a11c (e527735b466a…)
  ✓ tests/test_task_writer_core.py matches 7f43a11c (82f1c9f53881…)
```

`git status` clean; final `bash tests/run` back at the baseline's four reds.

=== VERDICT ===
task: TASK-362
rung: V4
result: PASS
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criterion 13 both halves — the store half by 4 mutations on
         tests/test_compact_payload.py's three guards (marker not restored;
         blank published as a real value; a declared value altered; a fixture
         with no declared blank), the schema half by reversing
         default_stages_for (RED in test_wip_and_stages and test_track_move);
         the round-10 fix by 3 mutations on bin/perry-task:4269-4272 (bare
         `or`; fallback unconditional; blank rule narrowed to the marker), all
         RED, and each of the 4 tests in TestADeclaredBlankRungIsNotARung
         enumerated for what it can and cannot distinguish; the main-only
         isolation confirmed honest against TASK-435 by measuring a non-main
         track in three shapes. Criterion 5 — SKILL.md:130 calls --compact;
         52 declared fields compared against --json on Perry's own state and
         on tests/fixtures/sample-project with an independent walker and an
         independent reimplementation of all six kinds, 0 disagreements, 0
         undeclared keys; round 4's count mutation now RED in 8 tests and
         round 6's linkage.objectives repointing RED in 4; the token bound
         measured at 11,305 bytes (~2,800 tokens) against --json's 247,668.
         Baseline and final suite both 124 modules / 3561 tests / the 4 known
         reds; all four files restore-checked against git show 7f43a11c.
not-checked: the other twelve criteria and the twelve already-closed rows; the
         full rounds 4-9 enumerations (46/53 repointings, 45/53 `how`
         rewrites, the ten subdict children) — I ran two representatives, not
         the enumeration; criterion 5's token bound on any project larger than
         Perry's own, and it is pinned only as a relative fraction (ROW-3);
         --compact under i18n, a non-UTF-8 file, or a truncated
         .perry/config.jsonl; TASK-435 itself beyond confirming it exists and
         that the isolation is honest; whether cmd_done is correct for a
         non-main track in every mode (measured in three shapes, not
         enumerated); Windows or any non-macOS path behaviour; whether
         perry-lint --reviews clears review-rounds-exhausted for this row.
proof: n/a — PASS. Six findings are filed as rows above, none of them a defect
         criterion 13 or criterion 5 reaches; ROW-1 (bin/perry-config:199,207
         writes --default-rung unvalidated and bin/perry-task:4269-4272 stamps
         it, so `done` writes verification='V0' while `done --rung V0` exits 1,
         and perry-lint passes it) is the one worth its own round.
=== END VERDICT ===
