# TASK-278 — round 3 result

> Criteria: `perry/evidence/2026-09/TASK-278-spec.md`. Every destructive probe
> was `--dry-run` in a `git archive` scratch copy under my own worktree
> (`.scratch/`). The primary checkout at `/Users/bytedance/proj/Perry` was not
> touched.

## 0. Base — it was wrong, and I reset

The worktree I was handed was at `d49964e`, **527 commits behind `main`**, with
no commits of its own. `TASK-381` again.

```
git merge-base --is-ancestor 6282ae1 HEAD   ->  NO       (bad base)
git rev-list --count main..HEAD             ->  0        (no commits of my own)
git rev-list --count d49964e..main          ->  527
```

Reset onto `main`'s tip **`7b2173c`**, which is a descendant of the required
`6282ae1` (the only commit between them is the round-3 dispatch itself). After
the reset `git merge-base --is-ancestor 6282ae1 HEAD` passes.

**Two numbers in the dispatch were already stale, and I did not silently adopt
either.**

- `bin/perry-lint --root .` prints `0 error(s)` as required, but
  **`linkage store: 123 record(s), 1 row(s) drifted`**, not the `122` the brief
  predicted. `perry/linkage.jsonl` is **byte-identical** between `6282ae1` and
  `7b2173c` (`git diff` over that path is empty), so the brief's number was
  stale when written rather than changed by the dispatch. The drifted row is
  `P003-O3-KR2`, which is `TASK-383`'s known unclearable drift.

## 1. Baseline — the brief predicted one red; the true base has three modules red

My first `bash tests/run`: **119 modules · 3414 tests · 2 modules red**. That
measurement was itself wrong, and I only found out because I re-measured the
base at the end. **The base's real state is 3 modules red**, and my final tree
matches it exactly.

| module | failing test(s) | attributed |
|---|---|---|
| `test_diagnose` | `test_perry_itself_passes_its_own_id_checks` | `TASK-380`, as the brief predicted |
| `test_linkage_import` | `test_no_live_record_was_imported_as_declared_at_add`, `test_the_store_accounts_for_the_register_in_both_directions` | **not predicted** — `TASK-383`'s drift |
| `test_contract_key_parity` | `test_without_the_witness_the_four_are_unobservable`, `test_the_same_mutation_is_silent_without_the_witness` | **not predicted, and GREEN in my first baseline run** |

**`test_linkage_import`** — re-run alone before attributing it (43 tests, same
2 reds, not order-dependent). Its own JSON names the cause:

```
"in_store_not_in_register": ["TASK-382→P003-O3-KR2", "TASK-383→P003-O3-KR2"],
"register_total": 121, "store_total": 123, "accounted": false
```

`TASK-382` and `TASK-383` were filed with `--kr`, so `add` wrote two `edge`
records the register document does not carry — `TASK-383`'s own reproduction,
already on `main`. The brief's "expect exactly one red" was written before
those two rows were filed.

**`test_contract_key_parity` is the one I nearly got wrong, and it is worth
recording as a method failure rather than hiding.** It was GREEN in my baseline
parallel run and RED in my final one, which reads exactly like a regression I
caused. Re-running it alone did not settle it either — the standing lesson says
re-run a red module alone, and alone it is red *in both trees*. What settled it
was running the **whole parallel suite at the base commit**, where it is also
red. So my baseline's green was the flaky observation, not my tree's red. **A
single baseline run is not a baseline for a test that flips between runners**,
and I would have shipped a false "no new failures" claim on the strength of it.

Final: `119 modules · 3425 tests · 3 modules red` — the same three the base
has. **No new failures.**

**One more red was mine, and it was the scratch directory itself.**
`test_header_index_is_the_only_fold` went red with 108 "newly uncovered"
entries, every one of them under `.scratch/` — my `git archive` copies of
Perry's own source, which that test walks as if they were the repo's. It is
green at base and green again once the copies are removed. **The brief's "all
scratch work inside your own worktree" (`TASK-373`) collides with the repo
-scanning tests**: a `.scratch/` holding a Perry source tree turns that module
red on its own. Worth a row, or a `.scratch/` exclusion in the walker.

## Bound

**The enumeration is over `viewer/parsers.py § parse_yaml_subset § parse_map`'s
own branches, not over the two examples the tree happens to carry.** It has
three axes and I found the third only because a green mutation forced me to
look for it.

**Axis 1 — the VALUE shape. Exactly 7, and 4 carry a resolvable id.**

| # | branch | value becomes | carries a resolvable id | round 2's line scan saw it |
|---|---|---|---|---|
| A | `tasks: ["A"]` / `[A]` flow list | `['A']` | **yes** | yes |
| B | `tasks: \|` block scalar | `['A\n']` | no — keeps its newline, `kr_for_task` matches exactly | no |
| C | `tasks: A` bare scalar | `['A']` | **yes** | yes |
| D | `tasks:` + `- A` indented deeper | `['A']` | **yes** | **NO — the gap** |
| E | `tasks:` + `- A` at the key's own indent | `['A']` | **yes** | **NO — the gap** |
| F | `tasks:` + `k: v` nested map | `["{'id': 'A'}"]` | no — stringified dict | no |
| G | `tasks:` with nothing | `[]` | no | no |

**Axis 2 — the KEY spelling. Exactly 2.** `parse_map` does
`key.strip().strip("\"'")`, so `tasks:` and `"tasks":` are the same key to
every reader. **I missed this on the first pass and a green mutation found it**
— see § 5, M5/M7/M8/M9.

**Axis 3 — the LOCATION. Exactly 2.** `schema/state-schema.json` puts a
`tasks` key in `objectives[].krs[].tasks` and `agents[].tasks` and nowhere
else; `unlinked` is a top-level id array (deliberately not a reference on
either the store or the document side) and `projects[]` has no tasks.

**So the space is 7 × 2 × 2 = 28 cells, of which 4 × 2 × 2 = 16 carry a task
id a reader resolves.**

- **Detection covers all 16.** Structural read plus text, unioned.
- **Location covers 8 of 16** — the bare-key half. The 8 quoted-key cells
  refuse *without* a line number rather than with one. Deliberate: no writer
  Perry has emits a quoted key, and widening the locator regex to match one
  would close that reporting gap while removing the only input that proves the
  structural half does anything at all.

**The set has a last element, and I checked the obvious candidate for an
eighth branch.** A flow list split across physical lines is **not** a shape:
`parse_yaml_subset` raises `unexpected indent`, so `parse_linkage` returns
`error` and the register declares nothing. Measured in `.scratch/enumerate.py`,
`.scratch/branches.py` and `.scratch/keyaxis.py`.

**Round 2 covered A and C at the bare key and missed D and E** — both block
shapes, in both locations, so **4 of the 16 id-carrying cells were open** and
`purge` deleted rows those registers named.

## 2. The fix — detection is structural, location is separate

`bin/perry-task § live_references`. The three parts, because collapsing any two
of them is how this row got here:

1. **Detection is structural**, through the same `parse_linkage` every other
   reader uses. All KRs are walked rather than `kr_for_task`'s first match.
2. **Location is a separate region scan** (`_tasks_list_regions`) that pins the
   line the id actually sits on — for a block list the `- "TASK-NNN"` item,
   which is the line a reader deletes. Reverting to `parse_linkage` alone was
   refused by the brief and would have been wrong: the model carries no line
   numbers.
3. **The two are unioned with the TEXT, not merely with each other.** This is
   mine, not the brief's: `parse_linkage` is all-or-nothing, so a register whose
   frontmatter does not parse returns a `Linkage` carrying **no objectives**, and
   a purely structural guard goes blind exactly where a register is most likely
   to be broken — the same permanent loss through a different door. Every
   located line is reported whether or not the parse confirms it, and anything
   the parse confirms is reported even when no line can be pinned to it.

## 3. The two-armed differential, confound stripped

**Confound sweep first.** `TASK-087` appears **once** in `perry/tasks.jsonl` —
its own record, verified by reading it — and **zero** times in `perry/BOARD.md`,
`perry/okr.jsonl` and `perry/linkage.jsonl`. Its only live reference is
`perry/phase/002-linkage.md:69`. Nothing to strip.

Two `git archive` copies of `HEAD`, verified by `diff -rq` to differ in
**`bin/perry-task` and nothing else**. In both, `002-linkage.md:69` was
rewritten from `tasks: ["TASK-087"]` to the equivalent block list,
line-anchored with an assert on the old text; the script then asserted both
arms hold a **byte-identical** register and that `parse_linkage` resolves the
edge (`kr_for_task('TASK-087') -> 'P002-O3-KR2'`). `--dry-run` only.

| arm | code | register | `purge TASK-087 --dry-run` |
|---|---|---|---|
| A | base `7b2173c` | block list | **NOT REFUSED** — `would write TASK-087 (purge) → tasks.jsonl + journal + BOARD.md + event` |
| B | **+ my fix** | block list | **REFUSED** — `TASK-087 is named by 002-linkage.md:70 krs[].tasks` |

Line **70** is the `- "TASK-087"` item line, not the `tasks:` key on 69 — the
refusal names the line to edit.

**The shape is legal, not a malformed file I invented**: `bin/perry-lint --root
perry` grades the block-list register **`0 error(s)`**.

## 4. Flow lists still work — no regression

Same fixed code, registers **unmodified**:

| row | base `7b2173c` | with my fix |
|---|---|---|
| `TASK-028` | refused — `001-linkage.md:16 krs[].tasks (and 1 more: 001-linkage.md:105 agents[].tasks)` | **identical** |
| `TASK-046` | refused — `001-linkage.md:24 krs[].tasks (and 1 more: 001-linkage.md:103 agents[].tasks)` | **identical** |
| `TASK-087` | refused — `002-linkage.md:69 krs[].tasks` | **identical** |

Byte-identical refusals, and the same lines the round-2 V4 review recorded.

## 5. Mutation — 13 planted, graded three times, every green closed

Line-anchored with an assert on the old text (never `str.replace` on a
repeated string); `__pycache__` cleared and **1.2s slept past the whole-second
boundary** before every run; every restore written from `git show <my ref>:<path>`
and hash-compared — **my own branch's commit, never `main`**. Harness:
`.scratch/mutate.py`. Control (no edit): **GREEN** in all three rounds.

**`test_linkage_import` is excluded from the graded set** and this is stated
rather than buried: it carries the 2 pre-existing reds from § 1, and a red
control makes every verdict below meaningless. Graded against the other **9**
modules.

### Round A — 7 red, 6 GREEN

| # | mutation | A | named test that killed it |
|---|---|---|---|
| M1 | location-only detection (round 2's code restored) | red | `test_site_3_a_block_list_refusal_names_the_item_line` + 2 |
| M2 | textual half deleted (structural only) | red | `test_site_3_a_register_that_does_not_parse_still_protects_a_row` + 2 |
| M3 | flush block items dropped | red | `test_site_3_a_block_list_at_the_keys_own_indent_still_protects_a_row` |
| M4 | no block items collected | red | 3 block tests |
| M5 | declared-but-unlocated fallback removed | **GREEN** | — |
| M6 | agents label collapsed into `krs[].tasks` | **GREEN** | — |
| M7 | structural walk stops at first KR | **GREEN** | — |
| M8 | structural agents read removed | **GREEN** | — |
| M9 | parse never consulted at all | **GREEN** | — |
| M10 | `tasks:` regions never found | red | 3 block tests |
| N3 | edge phase filter always true (round 2's green) | red | `test_an_edge_naming_another_phases_kr_stays_out_of_this_slice` |
| N1 | empty phase takes the whole store (round 2's green) | **GREEN** | — |
| N8 | document `phase:` branch nulled (round 2's green) | red | `test_the_documents_own_phase_field_names_the_phase_when_the_filename_cannot` |

**M1 is verification 3**: restoring round 2's scan makes named tests fail for
the block shape specifically.

### Why each green survived, and what closed it

**M5 / M7 / M8 / M9 were one root, and it is the uncomfortable finding of this
round.** M9 removes the structural read *entirely* (`if False:` over the parse)
and **nothing went red**. The structural read — the actual deliverable — was
dead weight as tested, because in every fixture the line locator already found
the id. Only the malformed-register case made the *textual* half load-bearing;
nothing made the *structural* half load-bearing.

Closing them required extending the enumeration onto **axis 2, the key**, which
I had missed: `parse_map` strips quotes from keys, so `"tasks": [...]` is a real
edge that the locator's `(\s*)tasks:` cannot see. That input is caught by the
structural read alone. `.scratch/keyaxis.py` measured it.

**M6 survived for a subtler reason worth recording.** Collapsing the agents
label into `krs[].tasks` left the string `agents[].tasks` in the output anyway,
because the structural fallback re-adds it without a line — so
`assertIn("agents[].tasks", …)` passed *with the bug present*. Both agents tests
now assert the label **together with its line**.

**N1 is an equivalent mutant for every realistic store**, which is why round 2
and my round A both saw it green: the `any(kind == "kr")` guard below returns
`None` regardless. It is observable on exactly one input, and that input is the
argument for the guard — with no phase number the prefixes become `"-"` and
`"P-"`, which **match** rather than match nothing, so a record whose `phase`
begins with a dash is adopted by a caller that could not name a phase at all.
Proved in `.scratch/n1.py` and asserted directly.

### Round B — 12 red, 1 GREEN

Every closure held except one. The `krs[]` quoted-key test closed M5, M7 and M9
but left **M8** green: it exercises only the KR half, and the two halves of the
structural read are independent code needing independent inputs. Closed with
`test_site_3_a_quoted_agents_tasks_key_is_caught_structurally_too`.

### Round C — 13 red, 0 GREEN

Re-graded at `d46fb18`, control GREEN, both files restored and hash-verified
(`bin/perry-task` `1e034c85d98ae433`, `viewer/parsers.py` `da657ee7507d99be`).

| # | mutation | A | B | C | closed by |
|---|---|---|---|---|---|
| M1 | location-only detection (round 2 restored) | red | red | red | 3 block tests |
| M2 | textual half deleted | red | red | red | the unparseable-register test + 2 |
| M3 | flush block items dropped | red | red | red | `…block_list_at_the_keys_own_indent…` |
| M4 | no block items collected | red | red | red | 3 block tests |
| M5 | declared-but-unlocated fallback removed | **GREEN** | red | red | both quoted-key tests |
| M6 | agents label collapsed into `krs[].tasks` | **GREEN** | red | red | both agents tests, now line-attributed |
| M7 | structural walk stops at first KR | **GREEN** | red | red | `…quoted_tasks_key…` |
| M8 | structural agents read removed | **GREEN** | **GREEN** | red | `…quoted_agents_tasks_key…` |
| M9 | parse never consulted at all | **GREEN** | red | red | both quoted-key tests |
| M10 | `tasks:` regions never found | red | red | red | 3 block tests |
| N3 | edge phase filter always true | red | red | red | `test_an_edge_naming_another_phases_kr…` |
| N1 | empty phase takes the whole store | **GREEN** | red | red | `test_no_phase_number_reads_the_document…` |
| N8 | document `phase:` branch nulled | red | red | red | `test_the_documents_own_phase_field…` |

**6 greens found, 6 greens closed, and the two that mattered were mine, not
round 2's.**

## 6. Lint and drift — unregressed

`bin/perry-lint --root .` after the fix: **`0 error(s), 39 warning(s)`**,
`linkage store: 123 record(s), 1 row(s) drifted` — identical to the baseline in
every store line.

## 7. Commits

| commit | what |
|---|---|
| `0d23b5b` | the guard: structural detection, separate location, unioned with the text |
| `42b355c` | round 2's three open greens (N1, N3, N8) |
| `0909998` | the six greens my own round found; locator now skips `#` comments |
| `d46fb18` | M8, the last green — the agents half needed its own input |

## 8. What I did not check

- **Whether all ~30 rows the registers name are protected.** I verified the
  three flow probes, the block conversion of `TASK-087`, and the fixture cases;
  I did not re-sweep the rest.
- **`test_linkage_import` and `test_contract_key_parity` were excluded from the
  mutation grading set** because a red control makes every verdict meaningless.
  Their reds are about Perry's live state and about a flaky witness fixture, not
  about this guard, and nothing here touches them — but I did not confirm that
  by mutating against them.
- **The full 119-module suite under each mutation.** Graded against 9 modules
  with a green control. A wider grading can only turn a green red, not the
  reverse — so no green above rests on the narrowing.
- **The 8 quoted-key cells refuse without a line number**, by choice. I did not
  measure how a user experiences that refusal, and I did not check whether any
  register anywhere is actually written with a quoted key (none in this repo).
- **Whether `_tasks_list_regions`' item run can over-collect on a register
  shape I did not construct.** Over-collecting costs an over-report, not a
  deletion, so I treated it as the safe direction rather than bounding it.
- **Concurrency.** I ran alone; no interleaved `purge` and `link`.
- **Projects other than Perry**, beyond the fixture projects the suite builds.
- **Whether `perry-goals link` can CREATE a block list from nothing.** It
  appends to one and preserves it, which is what the defect needs; a block-style
  register arrives by hand-editing or inheritance, not by first write. Unchanged
  from the V4 review's finding.
- **`perry-lint`'s own site-4 helper under mutation** — this diff does not touch it.
- **Rows E and F**, and whether this fix survives the document strip `TASK-280`
  performs. If `phase/<NNN>-linkage.md` sheds its schema'd half, the document
  half of this guard has nothing left to read and the union collapses to the
  store — that is a real interaction and I did not model it.
- **Shape B (`tasks: |`) is a latent reader bug I did not fix.** `parse_linkage`
  turns it into `['TASK-087\n']`, so `kr_for_task` never matches and the READER
  silently loses the edge. Both sides agree it is not a reference, so `purge` is
  consistent — but a register written that way declares an edge no reader
  honours. Out of scope here; worth a row.
