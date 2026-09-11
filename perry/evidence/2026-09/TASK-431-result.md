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
