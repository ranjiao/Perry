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

## 2 · The sweep returned 19, not 3

**This is the row's answer, and it is not three.** The 19 candidate READ sites,
adjudicated one at a time. "In category" means: *this decides whether a cell a
human typed means nothing.*

(table follows in § 3 once each adjudication is written up)

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
| `viewer/parsers.py:473 § resolve_state_root` | `raw in {".", "./", "—", "-"}` on the `State root` **path** setting. The set is dominated by `.`/`./`, which are paths and not blank spellings; see § 6. |
| `viewer/parsers.py:1745 § _APERIODIC` | `n/a` in a `Frequency` cell means **aperiodic**, a positive schedule answer, not an absent one. Widening it to the declared set would make `待定` a schedule. |
| `bin/perry-lint:1281`, `bin/perry-goals:1409`, `viewer/parsers.py:4792` | `slug in {"(none)", "none", "—"}` on the `phase/CURRENT` **pointer file**. Three copies of one rule, and a real finding — but a different category: the set's principal member `(none)` is not a declared blank spelling and the schema does not carry it. See § 6; filed, not fixed here. |

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

One addition to `bin/lib`: `blank_cell_spellings()`, which hands back the
declared set for the one caller shape that legitimately needs the set rather
than the verdict (§ 7). It is armed through `is_blank_cell` itself, not by a
second schema read.

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
