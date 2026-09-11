# TASK-431 — result

> Branch: `task-431-blank-cell`, from `main` at `70458893`.
> Written incrementally. Sections appear in the order they were measured.

## 0 · Baseline, taken in this tree

`bash tests/run` on `70458893` before any edit:

```
✗ 3 of 3578 TEST(S) failed
    FAIL test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable
    FAIL test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness
    FAIL test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale
```

All three are on the known-red list I was handed. `test_diagnose.
TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks` — the fourth
possible known red — was **green** in this tree. So the bar for "I broke
nothing" is: exactly these three, no others.

## 1 · The sweep — method

The Bound forbids working from the three sites the row names, because the row
exists precisely because a previous fix believed its own list was complete. So
the set below is derived, and the derivation is a program rather than a grep:
a grep for `"—"` cannot tell a cell being *tested* from an em dash being
*printed*, and this codebase prints a lot of em dashes — 175 of the 222 raw
hits are output.

`tests/sweep_blank_cell_sites.py` is the sweep, and it is also the
fourth-list guard (§ 5). It works like this:

1. Read the 17 declared spellings out of `schema § i18n.blank_cell` — both
   language lists, normalised with the same `_blank_key` reduction
   `lib.is_blank_cell` uses (casefold, strip markdown decoration, strip
   terminal sentence punctuation). Never a hardcoded copy.
2. Parse **every** Python source under `bin/` and `viewer/` with `ast` —
   including the extensionless scripts, which are found by reading the
   shebang, not by a filename list. 25 files.
3. Walk each tree for every `ast.Constant` string whose `_blank_key` is one of
   the 17.
4. Classify each hit by **direction**, by climbing the parent chain:
   - **READ** — the literal, or a `Set`/`List`/`Tuple` literal containing it,
     sits in the `comparators` of an `ast.Compare` whose op is
     `In`/`NotIn`/`Eq`/`NotEq`. The code is asking *does this value mean
     nothing*.
   - **CONST** — the container is assigned to a name. The name is then
     resolved: every `Compare` elsewhere in the same module that tests against
     that name is reported as a READ site, with the definition line. This is
     what catches `UNDECLARED_CELL`, whose seven readers are nowhere near
     line 354.
   - **WRITE** — everything else. An f-string, an `x or "—"` display default,
     a `.split("-")` argument.

Direction is the load-bearing idea. `perry-task` alone has 30 blank-spelling
literals and **one** of them is a read.

Running it on `70458893`:

```
222 literal occurrences of a declared spelling in bin/ + viewer/
├── 175 WRITE  — produced, not tested. Not this category.
├──   9 CONST containers holding declared spellings
└──  31 READ occurrences, over 19 distinct (file, function) sites
```

## 2 · The sweep returned 19 candidates, and 9 in category — not 3

**This is the row's answer, and it is not three.** The 19 candidate READ sites,
adjudicated one at a time. "In category" means: *this decides whether a cell a
human typed means nothing.*

### 2.1 · The 19, adjudicated

**In category — a cell a human typed, decided by a local rule (9 sites):**

| # | site | what it accepted as nothing, at `70458893` | named by the row? |
|---|---|---|---|
| 1 | `bin/perry-lint:354 § UNDECLARED_CELL` (9 readers: `:1129 :1175 :2134 :2942 :2970 :2989 :4265 :4282 :4303`) | 10 spellings, no Chinese | yes |
| 2 | `bin/perry-state:301 § split_stages` | `""` and `—` | yes |
| 3 | `bin/perry-state:571 § missing_defaults` | `{"", "—", "–", "-", "n/a", "tbd", "?"}` — a **fourth list**, 7 spellings, no Chinese | **no** |
| 4 | `bin/perry-state:208 § parse_config` | `blank_marker()` **and then** a re-hardcoded `"—"` | **no** |
| 5 | `bin/perry-lint:1555 § check_cross_file` | `{"—", "-", ""}` on a BOARD.md `Evidence` cell | **no** |
| 6 | `bin/perry-lint:1654 § rung_satisfied` | `("—", "-")` on the same `Evidence` cell | **no** |
| 7 | `bin/perry-explain:462 § harvest` | `v != "—"` on a decision `Status` cell | **no** |
| 8 | `viewer/parsers.py:1838 § _NO_DATE` | 9 spellings hardcoded, `无`/`待定` but not `不适用`/`暂无`/`N.A.`/`TBA` | **no** |
| 9 | `viewer/parsers.py:2094 § _ASK_STILL_OPEN` | `("pending","waiting","open","—","-")`, matched as a **prefix** | **no** |

**The row named 3. The sweep returned 9 in category, 6 of them new.** Site 3 is
the one that matters most for the row's own thesis: `bin/perry-state` was
already one of the three named sites, and it carries a **second, different**
hardcoded list 270 lines below the one the row points at. A fix that worked
from the row's table would have edited `split_stages`, left `missing_defaults`
alone, and shipped the defect again in the same file.

**Out of category — exempt, with the reason (10 sites):**

| site | why it is not this category |
|---|---|
| `bin/perry-churn:512` | `added == "-"` on `git --numstat` output. `-` is git's binary-file marker in a machine format Perry does not own. Not a cell. |
| `bin/perry-diagnose:2698` | `t["confidence"] == "none"` — an enum `perry-diagnose` computes three lines earlier. Nobody types it. |
| `bin/perry-explain:160` | `text[match.end()] == "-"` — one character inside an ID token, testing whether a slug continues. Not a value. |
| `bin/perry-task:4031` | `low == "none"` on a **CLI argument** to `--items`, beside `"all"`. A keyword in an argument grammar, not a cell. |
| `viewer/parsers.py:473 § resolve_state_root` | `raw in {".", "./", "—", "-"}` on the `State root` **path** setting. The set is dominated by `.`/`./`, which are paths and not blank spellings; see § 7. |
| `viewer/parsers.py:1745 § _APERIODIC` | `n/a` in a `Frequency` cell means **aperiodic**, a positive schedule answer, not an absent one. Widening it to the declared set would make `待定` a schedule. |
| `bin/perry-lint:1281`, `bin/perry-goals:1409`, `viewer/parsers.py:4792` | `slug in {"(none)", "none", "—"}` on the `phase/CURRENT` **pointer file**. Three copies of one rule, and a real finding — but a different category: the set's principal member `(none)` is not a declared blank spelling and the schema does not carry it. See § 9; filed, not fixed here. |

## 3 · The consequence, reproduced first

`tests/fixtures/second-project` copied to a temp dir, the `research` track's
`stages` cell rewritten to each spelling in turn, `perry-state --compact` read
back. Script: `tests/repro_blank_stages.py`.

**Before (at `70458893`):**

```
 stages cell | stage_list                         | stages_declared
--------------------------------------------------------------------------
         '-' | ['-']                              | True
         '–' | ['–']                              | True
       'n/a' | ['n/a']                            | True
       'N/A' | ['N/A']                            | True
      'none' | ['none']                           | True
         '无' | ['无']                              | True
         '—' | ['brief','draft','review','approved','published'] | False   <- the one that works
        'na' | ['na']                             | True
       'tbd' | ['tbd']                            | True
         '?' | ['?']                              | True
      'N.A.' | ['N.A.']                           | True
       'TBA' | ['TBA']                            | True
        '无。' | ['无。']                             | True
        '待定' | ['待定']                             | True
       '不适用' | ['不适用']                            | True
        '暂无' | ['暂无']                             | True
         '？' | ['？']                              | True
     '**—**' | ['**—**']                          | True
     '`n/a`' | ['`n/a`']                          | True
      ' 无。 ' | ['无。']                             | True

20 of 21 blank spellings produced a NON-empty stage_list with stages_declared=True
```

Every one of the six round 8 named is there, and so are the eleven it did not
try. The single spelling that behaves is the bare em dash — the one literal
`split_stages` was taught.

## 4 · A tenth reader the sweep did not find, and why

The sweep enumerates **literals**. It found `UNDECLARED_CELL`'s definition at
`bin/perry-lint:354` correctly, and resolved the nine readers *in that module*
by following the name. It did not find these:

```
bin/perry-knowledge:407  if not src   or src   in L.UNDECLARED_CELL:
bin/perry-knowledge:454  if not claim or claim in L.UNDECLARED_CELL:
bin/perry-knowledge:461  if not src   or src   in L.UNDECLARED_CELL:
bin/perry-knowledge:477  if not trip  or trip  in L.UNDECLARED_CELL:
bin/perry-knowledge:488  if not owner or owner in L.UNDECLARED_CELL:
```

`bin/perry-knowledge` loads `bin/perry-lint` through a `SourceFileLoader` at
its line 148, binds it as `L`, and reads the set across the module boundary.
There is **no blank-cell literal anywhere in `perry-knowledge`**, so a sweep
for literals is structurally blind to it. So were the three lists the schema
note names — this is a sixth consumer nobody had counted.

**It was the test suite that found it, not me.** `test_knowledge_promotion`
went red in 28 tests with `AttributeError: module 'perry_lint' has no
attribute 'UNDECLARED_CELL'` the moment I deleted the set. Had I done the
softer thing and widened `UNDECLARED_CELL` in place instead of removing it,
those five readers would have kept working, I would never have looked at
`perry-knowledge`, and the report would have said "nine readers, all fixed".
**Deleting the name rather than editing its contents is what made the
remaining readers announce themselves**, and that is the transferable part.

What this costs the guard, stated precisely: the guard in § 5 detects
**containers**, not readers. That is sufficient going forward — a
cross-module reader cannot exist unless someone first defines a container, and
the container is caught at its definition site. The blind spot was in my
enumeration of *sites to edit*, not in the guard's ability to detect a fourth
list. The sweep now reports cross-module attribute reads as well, so the next
person does not have to be lucky.

## 5 · Before and after, per site

| # | site | before | after |
|---|---|---|---|
| 1 | `bin/perry-lint § UNDECLARED_CELL` | a module set of 10; `in` at 9 sites in-module + 5 in `perry-knowledge` | **name deleted**; 14 sites call `lib.is_blank_cell` |
| 2 | `bin/perry-state § split_stages` | `if not s or s == "—"` | `lib.is_blank_cell(cell)` on the raw cell **before** separator normalisation, and per element after |
| 3 | `bin/perry-state § missing_defaults` | `{"", "—", "–", "-", "n/a", "tbd", "?"}` | `lib.is_blank_cell(col(key) or "")` |
| 4 | `bin/perry-state § parse_config` | `n != blank_marker() and n != "—"` | `not lib.is_blank_cell(n)` |
| 5 | `bin/perry-lint § check_cross_file` (done-needs-evidence) | `ev in {"—", "-", ""}` | `not ev or lib.is_blank_cell(ev)` |
| 6 | `bin/perry-lint § rung_satisfied` | `ev in ("—", "-")` | `not ev or lib.is_blank_cell(ev)` |
| 7 | `bin/perry-explain § harvest` | `v != "—"` | `not lib.is_blank_cell(v)` |
| 10 | `bin/perry-knowledge` ×5 | `in L.UNDECLARED_CELL` | `lib.is_blank_cell(...)` |

**`bin/lib/__init__.py` is unchanged apart from a comment.** I did add a
public `blank_cell_spellings()` accessor partway through, for a caller that
needs the SET rather than the verdict — and then removed it, because the
caller I wrote it for did not end up needing it and a mutation of it came back
green. § 8 mutation 14 is that story. The row's instruction was not to widen
`is_blank_cell` to fit a caller; it turned out not to need widening or
extending at all.

**One spelling was dropped: `—/—`**, from `UNDECLARED_CELL`. It is not in
`schema § i18n.blank_cell`; a whole-tree search (`grep -rn "—/—" .`) finds it
on exactly one line — its own definition. No template, fixture, test or
document writes it. Preserving it would have meant adding a spelling to a
list, which the row forbids in its first "must not".

### 5.1 · The consequence, gone

Same script, same fixture, after the change:

```
 stages cell | stage_list                                          | stages_declared
         '-' | ['brief','draft','review','approved','published']   | False
       'n/a' | ['brief','draft','review','approved','published']   | False
         '无' | ['brief','draft','review','approved','published']   | False
     '**—**' | ['brief','draft','review','approved','published']   | False
        ... all 21 identical ...

0 of 21 blank spellings were read as a DECLARED stage list (stages_declared=True)
0 of those are a single stage named after the blank marker
```

Before: **20 of 21** had `stages_declared: true`, 20 of those a single stage
named after the marker. After: **0 of 21**.

Note what "gone" means, because the spec's word is "empty" and the payload is
not: `split_stages` now returns `[]`, and `--compact` then does what it
already did for the one spelling that worked — falls back to the *pipeline
mode's declared default* stages and reports `stages_declared: false`. The
after-state for all 21 is byte-identical to the bare `—` row of the before
table, which was the one correct row in it. The projection was not touched
(the row's third "must not").

## 6 · Suite

Baseline in this tree: 3 of 3578 red. After the `bin/` changes: **3 of 3578
red, the same three**. No test moved in either direction except
`test_handed_back_root`, below.

`tests/test_handed_back_root.py § NO_ROOT_TO_GIVE` is keyed by **line
number** — `("bin/perry-lint", "check_file", 5495)`. The comments I added
above that call pushed it to 5525 and the exemption silently stopped
matching, so the call reappeared as a finding. Updated to 5525, with a note
in the test saying that any edit above it does this. The call itself is
unchanged. **This is a latent trap for every future edit to `perry-lint`,
not something this row introduced**; it is filed in § 8.

## 7 · The narrowness judgement, which the row asked for by name

The row said `split_stages` "may genuinely want only the marker, for a
reason", and told me to make the narrowness explicit and tested if I concluded
that.

**I concluded the opposite, and the reason is the shape of the test rather
than a preference for uniformity.** The blank test in `split_stages` runs on
the WHOLE CELL, before any split. So the only track it can affect is one whose
entire pipeline is a single stage spelled exactly like a declared way of
saying "nothing here" — a track whose `stages` cell reads `none`. That track
has no pipeline to measure, and every mode that reads `stage_list` (queue,
pipeline, inquiry) is better served by being told the cell is empty and
falling back to the mode's declared default than by routing rows through a
stage nobody can address. A narrow rule here would need a positive reason, and
the only candidate — "somebody might name a stage `无`" — costs a real
pipeline nothing and buys a bogus one.

Two narrownesses DID survive, and both run the other way: a caller whose
vocabulary is deliberately WIDER than blankness. Neither is left as a bare
list that merely looks like an oversight.

1. **`viewer/parsers.py § _NO_DATE` / `parse_frequency`.** `ongoing`,
   `as needed`, `hourly` are *positive answers about a schedule*, not ways of
   writing an empty cell. `is_blank_cell` must never learn them — that would
   be widening the one rule to fit a caller, the row's second "must not", and
   it would make `待定` a cadence. So `_NO_DATE` is now `_APERIODIC` alone and
   `parse_due` asks `t.lower() in _NO_DATE or is_blank_cell(t)`: the list of
   blank spellings is gone, the cadence vocabulary stays, and
   `test_the_cadence_vocabulary_is_untouched` holds it there.

2. **`viewer/parsers.py § _ASK_STILL_OPEN`.** This is a **prefix** tuple, not
   an equality set — `ask_is_answered` calls `s.startswith(_ASK_STILL_OPEN)`.
   Its `—` and `-` members earn their place: `— not yet` is an open question
   and is *not* a blank cell, so `is_blank_cell` alone would lose it. The
   whole-cell blank test is therefore added BESIDE the prefix rule rather than
   replacing it, and mutation 11b below removes the two prefixes to show the
   half that is not redundant.

`_ASK_STILL_OPEN` is consequently the one container left in the tree holding
blank spellings as literals. It is in the sweep's `EXEMPT` list with that
reason. It is not the defect returning, because no amount of adding declared
spellings to it would be *correct*: as a prefix, `na` would match a status
beginning "named…".

## 8 · Mutations

`work/reference/review.md § 2` rule 2. Anchored by matched text with the line
number recorded, never `str.replace` on an ambiguous string; `__pycache__`
cleared and 1.2s slept past the whole-second boundary on both the mutate and
the restore, since CPython validates bytecode on mtime-in-whole-seconds plus
size; every restore taken from `git show <ref>:<path>` and then verified by
`bin/perry-restore-check`, never against bytes the harness snapshotted.
Harness: `tests/mutate_blank_cell.py`.

| # | mutation | verdict | the test that reddened |
|---|---|---|---|
| 1 | `perry-lint` suspect-separator guard reads its own set again | RED | `TestTheSweepIsTheGuard.test_no_site_decides_blankness_for_itself` |
| 2 | `split_stages` back to `== "—"` alone | RED | `test_blankness_is_tested_before_separator_normalisation` |
| 3 | `split_stages` keeps blank interior elements | RED | `test_a_blank_between_two_real_stages_is_dropped` |
| 4 | `missing_defaults` back to its own 7-element list | RED | `test_missing_defaults_reads_the_one_rule` |
| 5 | `parse_config` back to `blank_marker()` + em dash | RED | `test_no_site_decides_blankness_for_itself` |
| 6 | `done-needs-evidence` back to its own set | RED | `test_no_site_decides_blankness_for_itself` |
| 7 | `rung_satisfied` back to its own tuple | RED | `test_no_site_decides_blankness_for_itself` |
| 8 | `perry-explain § harvest` back to the em dash alone | RED | `test_no_site_decides_blankness_for_itself` |
| 9 | `perry-knowledge` decides a source cell locally again | RED | `test_perry_knowledge_no_longer_reads_it_across_the_boundary` |
| 10 | `parse_due` drops the blank test | **GREEN → fixed → RED** | `test_a_blank_marker_followed_by_a_date_still_yields_none` |
| 11 | `ask_is_answered` drops the blank test | RED | `test_a_blank_ask_status_is_still_open` |
| 11b | `_ASK_STILL_OPEN` loses its em-dash prefixes | RED | `test_a_real_answer_and_a_real_prefix_are_unchanged` |
| 12 | `intake_is_discharged` drops the blank test | RED | `test_a_blank_intake_outcome_is_not_discharged` |
| 13 | the viewer's wrapper grows a literal fallback list | RED | `test_the_viewer_does_not_reimplement_the_rule` |
| 14 | `blank_cell_spellings()` primed with the short-circuiting `""` | **GREEN → code deleted** | — |
| 15 | a new hardcoded list added to `bin/perry-context-budget` | RED | `test_the_sweep_can_see_a_fourth_list_when_one_is_added` |

Two came back green on the first pass, and both were findings rather than
noise.

**10 — `parse_due`, and my test was the thing that was wrong.** Deleting the
blank test left `test_a_blank_due_cell_yields_no_date_in_any_language`
passing, because a cell containing ONLY a marker has no date in it either way:
`parse_due` returns `None` for `无` whether it stops at the marker or scans
past it and finds nothing. The bracketed-citation case does not discriminate
either — `_ANNOTATION` cuts at the opening bracket before any token is read.
**The assertion I had written could not fail.** The input that separates the
two behaviours is a marker followed by a BARE date — `待定 2026-08-03`, which
is what a half-filled cell actually looks like: without the blank test the
marker falls through and the scan reports that date as due. That is now
`test_a_blank_marker_followed_by_a_date_still_yields_none`, over all 23
spellings, and mutation 10 is red.

**14 — `blank_cell_spellings()`, and the right fix was to delete it.** I had
added a public accessor to `bin/lib` so that a caller needing the SET rather
than the verdict could union it. The mutation was green because **nothing
called it**: the caller I wrote it for ended up asking
`t.lower() in _APERIODIC or is_blank_cell(t)`, which is the one rule at the
point of use and needs no set. So it shipped with zero callers and a docstring
naming one — a false claim in code, and a standing invitation to test a raw
cell against `_blank_key`-reduced keys and silently miss every decorated form.
It is gone, and a comment where it stood records why. **Mutation 14 is not
"fixed", it is voided**, and that is the honest label.

Mutations 7 and 11 initially reported ANCHOR-FAIL rather than a verdict, and
that is the harness working: 7's anchor `    if not ev or
lib.is_blank_cell(ev):` is a strict substring of 6's twenty-space-indented
line, so the guard counted 2 occurrences and refused rather than mutating the
wrong one — precisely the `str.replace` trap rule 2 names. Re-anchored, both
are red.

## 9 · Rows this turned up and did not fix

1. **The `phase/CURRENT` sentinel has three implementations.**
   `bin/perry-lint § check_cross_file`, `bin/perry-goals § current_phase` and
   `viewer/parsers.py § load_snapshot` each carry their own
   `slug in {"(none)", "none", "—"}`. Same defect shape as this row, different
   category: `(none)` is the set's principal member and the schema does not
   declare it, so `is_blank_cell` cannot take this over without a schema
   change. Needs its own row and its own declaration. `perry-goals §
   current_phase` documents itself as "deliberately the same rule" as
   `parsers.load_snapshot` — stated in prose, implemented twice, which is this
   repository's signature defect.

2. **The WRITE direction is unswept.** 167 of the remaining literal
   occurrences produce a blank marker rather than test for one, and roughly
   forty are `x or "—"` display defaults that hardcode the em dash instead of
   calling `lib.blank_marker()`. `blank_marker()` exists precisely so the
   spelling handed back cannot become one `is_blank_cell` would not
   recognise, and these bypass it. I classified them but did not measure the
   consequence; I am not asserting there is one.

3. **`tests/test_handed_back_root.py § NO_ROOT_TO_GIVE` is keyed by line
   number.** Three comment lines added above the call it names silently
   un-declared the exemption. Any edit to `bin/perry-lint` above line 5525
   does this again. It should be keyed by `(file, function)` the way this
   row's own guard is.

4. **`—/—` is undeclared.** Dropped from `perry-lint` with a search showing
   nothing in the tree writes it. If any real board spells an empty cell that
   way, it is a `schema § i18n.blank_cell` row, not a literal in `bin/`.

## 10 · What I did not check

Rule 4 of `review.md § 2`. These are where I would look first next.

1. **Non-Python readers.** The sweep parses Python. If a blank-cell decision
   is made in a template expression, in `packs/`, or in whatever JavaScript
   the frontend carries, this row did not look and the guard does not cover
   it.
2. **Runtime-built sets.** The sweep sees literals and the names they bind.
   A set read from a file, built by string arithmetic, or assembled at
   runtime is invisible to it. None exists in the tree today; I checked that
   by reading the 9 remaining sites, not by a mechanism.
3. **`perry-lint` against a real board.** Nine checks now call more cells
   blank. On the two shipped fixtures the lint output is byte-identical, but
   a real Chinese board with `待定` in a no-default column will now get
   `no-default` warnings it did not get before. That is the intended
   correction — I have not run it against any board outside `tests/fixtures/`.
4. **Whether the three `phase/CURRENT` copies currently disagree.** I
   established that they are three copies. I did not diff their behaviour.
5. **Ordering.** I ran `tests/run` whole, not `--serial`, so a red that only
   appears under a particular module order would not have surfaced. The reds
   I saw are the three I was told to expect.
6. **`viewer/tables.py`.** It is imported by both `bin/lib` and
   `viewer/parsers.py` and would be the natural home for a shared rule. The
   sweep found no blank-cell literal in it, so I did not open the question of
   whether the rule belongs there rather than in `bin/lib`.
