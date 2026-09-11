# TASK-348 — call-site census of the other 22 files

> Row: TASK-348 · Spec: `perry/evidence/2026-09/TASK-348-spec.md`
> Applies: `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md` (rules 1-3 and § 5b)
> Serves: `perry/design/DESIGN-014-how-much-python.md § 5.1` and `§ 6` step 1
> Composes with: `perry/evidence/2026-09/TASK-263-result.md` (the other two files)
> Rung: V4 · **Read-only. No behaviour changed by this row.**

## 0. Commit measured, and two corrections to the brief

Measured at **`7f43a11c`** (`main` when the worktree was cut), **not** at
`583f024f` as the Bound pins. This is not a deviation: **all 22 files in scope
are byte-identical at the two commits**, so every line number in this report is
valid at `583f024f` as well. Verified by asking git directly rather than by
eye — `git diff --stat 583f024f 7f43a11c --` over the 22 paths returns nothing.
`583f024f..7f43a11c` is four commits and it does touch `bin/perry-task`
(+14 lines), but that file is `TASK-263`'s and is excluded here.

**The Bound's size figure is confirmed exactly.** Re-derived with `wc -l` in
this worktree before starting:

| | spec | re-derived | |
|---|---:|---:|---|
| files | 22 | 22 | matches |
| lines | 27,132 | **27,132** | matches |

Every one of the 22 per-file counts matches the spec's list as well. The
arithmetic in § 10 sums to 27,132 and the checker asserts it.

### Correction 1 — the enumeration is 23 files, not 22

The spec describes its corpus as *"every `.py` and every executable under
`bin/` and `viewer/` **except** the two `TASK-263` already covered"*, and then
lists 22 files. **That list is one file short of its own sentence.**
`bin/perry` — a 162-line Python executable, `#!/usr/bin/env python3`, the index
that `perry list` and `perry describe` run — is under `bin/`, is executable, is
not `perry-task` and is not `perry-lint`. Enumerated mechanically:

```
executables under bin/ and viewer/            20
  minus perry-task, perry-lint (TASK-263's)   -2      = 18
non-executable .py under bin/ and viewer/      5      (lib/__init__.py,
                                                       perry_md_store.py,
                                                       perry_store.py,
                                                       parsers.py, tables.py)
                                              ----
the category the spec's sentence describes     23
the spec's file list                           22     bin/perry is missing
```

Why it was missed is checkable and is not carelessness: **`bin/perry` was added
on 2026-09-09** (`8b302a61`, DESIGN-016 C1/C4), five days after the row was
filed on 2026-09-04 and two days before the spec was re-measured on 2026-09-11.
The re-measurement correctly caught the *growth* of the 21 files it already
knew about — 24,005 → 27,132 — and did not catch the file that had appeared in
the same window. That is the precise failure mode the Bound's own note warns
about (*"the count belongs to a commit and not to the row"*): re-measuring the
known list is not the same as re-enumerating the category.

**`bin/perry` is measured anyway, in § 10.23, with its own arithmetic kept
separate**, so the Bound's 22-file denominator stays exactly 27,132 and the gap
is still reported rather than quietly absorbed. It contributes **15 TYPED lines
and nothing else** — no OBSOLETE, no AGENT, no TRANSPORT — so including it
would not move a single conclusion. That is the reason to report it plainly
rather than to argue about it: the gap costs the census nothing, and the only
thing at stake is whether the next row inherits a list or an enumeration.

### Correction 2 — four of the 22 files are not Python

`bin/perry-dispatch-limit` (448), `bin/perry-update-check` (192),
`bin/perry-codex-preflight` (150) and `bin/perry-detect-host` (101) are
**`#!/usr/bin/env bash`** — 891 lines, 3.3% of the corpus. `TASK-263`'s
instrument is `ast.parse`, and it does not merely mis-measure these files, it
raises `SyntaxError` on the first one it is handed. The census could not have
been completed by porting that instrument alone, and a report that did not say
so would be claiming a method it had not used. What was done about it is § 1b.

## 1. Method — and why it is not a grep

The failure this row exists to avoid is classifying a line because its *name*
matched a pattern; `TASK-263`'s V4 recorded a defect for exactly one such slip.
The method here is `TASK-263`'s, deliberately unchanged so the two censuses
compose into one list rather than two lists that happen to be adjacent.

**Step 1 — mechanical support extraction.** Each file's support sets are
derived from the AST and the raw text with a fixed precedence
(`shebang` > `docstring` > `comment` > `blank`) so no line falls in two. The
function is `TASK-263-result.md` Appendix A, copied verbatim; it is reproduced
again here as Appendix A so this report stands alone. Everything not in a
support set is a **code line**. This is a partition of `1..N` by construction.

**Step 2 — authored regions over the code lines.** Every code line is claimed
by exactly one authored `(start, end, category, owner, note)` region. Regions
were authored by walking the AST's top-level construct list in file order and
reading each construct's body. **A construct is split into several regions
whenever its call sites fall in different categories; it is never rounded to
one.** 1,018 regions over 22 files.

**Step 3 — coverage assertion.** A checker asserts overlapping regions,
unclaimed code lines, and a category total that is not `wc -l`, and fails
loudly on any of them. **Every number in § 4 and § 10 is that assertion's
output, not a hand tally.**

**Step 4 — a zero-code-region check.** Any region contributing 0 code lines is
reported as an error. This is not redundant with step 3: a region can claim a
span that is entirely comment, close the arithmetic perfectly, and still be
describing nothing. It is the check that caught `TASK-263`'s Fault 1, and it
was run over all 1,018 regions here. **0 zero-code regions.**

**Step 5 — a pipe check.** `TASK-263`'s Fault 2 was two notes containing an
unescaped `|`, which silently dropped two rows out of the published tables. The
generator that renders § 10 escapes every `|`, and a check reports any note
still carrying one. **0 unescaped pipes over 1,018 notes.**

**The judgement step.** For each region the question asked is *what does this
call site do to a document*, answered by reading the statements in it:

- does it read a value out of a structure that is already typed (a `dict` from
  `json.loads` of a JSONL store, a schema enum, a `Path.stat()`, a `datetime`)?
- does it move a whole body from one place to another without looking inside?
- does it ask a natural-language question of prose?
- does it reconstruct a fact from a rendering of a store that already holds it?

**Why this is not a grep.** Four demonstrations, each of which a name-based
pass gets wrong, and each verified by reading the body rather than the name:

1. `viewer/parsers.py § parse_yaml_subset` sits in the file DESIGN-014
   condemns as representation layer, is 115 code lines of document parsing, and
   is **TYPED**: it implements a bounded YAML grammar deterministically, and
   its live caller is `bin/perry-lint § 488-495` reading *spec frontmatter*,
   which no store holds.
2. `bin/perry_store.py § duplicate_record_ids` and `§ duplicate_row_ids` differ
   by four characters, sit 64 lines apart, and land in opposite categories: the
   first walks `risks.jsonl` records (TYPED), the second walks
   `table["rows"]` / `row["cells"]` (OBSOLETE).
3. `bin/perry-state`'s payload key literally named `board` is **store**-backed —
   `parse_board(text, tasks=load_task_store(root))` reads no task row out of
   `BOARD.md` when `tasks.jsonl` exists — while `§ reconcile_drift`, whose body
   is a `json.loads` loop over `.perry/events.jsonl`, splits: 27 of its lines
   are that loop and 20 take their row set from a second deliberate markdown
   parse.
4. `bin/perry-goals § mint_commitment_id` is id minting, the METHOD's own TYPED
   example — and **one line of it** (`2165`) sources an id list from markdown
   `Id` cells and is OBSOLETE. A function rounded to one category hides that.

**Attribution across the file boundary.** Where a call site's document handling
actually happens inside `viewer/parsers.py`, the entry says `-> parsers.py`,
the line count is attributed to the call site only, and `parsers.py`'s own lines
are counted once, in its own section. The same rule `TASK-263` used for the
`parsers.py` boundary is used here for the `perry-task` / `perry-lint` boundary:
five call sites in scope call into those two files, they are named in § 8, and
their lines stay in `TASK-263`'s denominator.

## 1b. What the corpus did to the instrument

`TASK-263`'s instrument is AST-based and four files in scope have no AST. A
second extractor was written for them (Appendix B), with three properties that
matter for whether the two halves can be added together:

- **The same bucket names and the same precedence** (`shebang` > `comment` >
  `blank`). There is no docstring concept in sh, so that bucket is reported as
  0 rather than omitted, and the bucket list is identical on both sides.
- **The `usage()` heredoc is an authored `SUPPORT:cli-plumbing` region**, which
  is exactly where `TASK-263` puts `--help` contract strings in the Python
  files. So the two halves compose without inventing a bucket.
- **Heredoc bodies are tracked**, because a line beginning `#` inside a heredoc
  is data, not a comment. Without this the mechanical extractor silently moves
  usage text into `SUPPORT:comment` and the two halves stop meaning the same
  thing.

**One residual asymmetry, stated rather than worked around.** Because sh has no
docstring bucket, explanatory prose in the four shell files all lands in
`SUPPORT:comment` — 230 lines, 26% of their total. Per-bucket sums across the
two halves are therefore only meaningful if `docstring` and `comment` are added
together first. `bin/perry-detect-host` is the pathological case: 44 of its 101
lines are comments, **16 of which are its shipped `--help` text**, printed by
`sed -n '2,16p' "$0"`. A mechanical bucket is holding a contract string that
belongs in `cli-plumbing`, and no rule available here recovers it without
letting authored regions overrule the mechanical buckets — which would break
the partition. Its `cli-plumbing` count is understated by 16 lines. Flagged,
not fixed.

## 1c. Why the arithmetic can be checked without trusting this report

The region tables in § 10 are not a rendering of a separate working list —
**they are the list**. A reader can harvest all 1,018 regions from the published
tables with a ten-line regex, feed them to the `check()` function in Appendix A
(or Appendix B for the four shell files), and get § 4's numbers back. That was
run as the last step, parsing this document's own markdown. Its output, in
full, for the six largest files and the four shell ones:

```
files with tables: 23
malformed table rows: 0
viewer/parsers.py          151 regions harvested FROM THE DOCUMENT | code-column mismatches 0 | total 4,902 (file is 4,902) CLOSES
bin/perry-goals            136 regions harvested FROM THE DOCUMENT | code-column mismatches 0 | total 3,138 (file is 3,138) CLOSES
bin/perry-diagnose          82 regions harvested FROM THE DOCUMENT | code-column mismatches 0 | total 2,818 (file is 2,818) CLOSES
bin/perry-state            133 regions harvested FROM THE DOCUMENT | code-column mismatches 0 | total 2,657 (file is 2,657) CLOSES
bin/lib/__init__.py         46 regions harvested FROM THE DOCUMENT | code-column mismatches 0 | total 2,154 (file is 2,154) CLOSES
bin/perry-tasks             85 regions harvested FROM THE DOCUMENT | code-column mismatches 0 | total 1,928 (file is 1,928) CLOSES
bin/perry-dispatch-limit    28 regions harvested FROM THE DOCUMENT | code-column mismatches 0 | total   448 (file is   448) CLOSES
bin/perry-update-check      15 regions harvested FROM THE DOCUMENT | code-column mismatches 0 | total   192 (file is   192) CLOSES
bin/perry-codex-preflight   12 regions harvested FROM THE DOCUMENT | code-column mismatches 0 | total   150 (file is   150) CLOSES
bin/perry-detect-host        8 regions harvested FROM THE DOCUMENT | code-column mismatches 0 | total   101 (file is   101) CLOSES
...
TOTAL regions harvested from the published tables: 1026
files failing: 0
```

(1,026 = the 22 files' 1,018 plus `bin/perry`'s 8.)

**Four properties are asserted, not asserted-about.** No two regions overlap;
no code line is unclaimed; no region is empty of code; and **each row's
published `code` column equals what the checker independently computes for that
row's span** — which is the check that would catch a row silently dropped or
mangled by the markdown. `malformed table rows: 0` is the direct test for
`TASK-263`'s Fault 2: any row that did not parse as a five-cell table row would
be printed there.

Four properties are asserted, not asserted-about: no two regions overlap, no
code line is unclaimed, no region is empty of code, and each file's totals
equal its `wc -l`.

## 1d. What I read myself, and what I did not

**This matters more than usual for this row, and the spec does not ask for it,
so it is stated before the results rather than buried after them.**

27,132 lines is more than one reader gets through carefully. The corpus was
split: I read and classified **three files myself, line by line** — the three
`DESIGN-014 § 5.1` category B condemns, because they are what question 2 turns
on — plus `bin/perry`. The other **eighteen files were classified by delegated
readers** working from a single written method (the same four categories, the
same support buckets, the same two `TASK-263` precedents, the same instrument).

| | files | lines | share |
|---|---:|---:|---:|
| read line by line by me | 3 (+`bin/perry`) | 8,505 | 31% |
| delegated, then verified | 19 | 18,627 | 69% |

What I did to the delegated 69%, in full:

1. **Ran the checker on every region list myself.** All 22 close; I did not
   take a reported count on trust. Two lists failed their first run and were
   returned.
2. **Ran the zero-code and pipe checks myself**, over all 1,018 regions.
3. **Audited a random sample of ten delegated regions** against the code —
   seeded, so the sample is reproducible: `random.seed(348)`. Nine were right.
   **One was wrong, and is corrected in this report** (§ 9.1); the correction
   is 2 lines and it is recorded rather than silently applied.
4. **Read every delegated file's non-TYPED destination claims** against the
   tree, because those are what a later row would act on.

What I did **not** do: read all 18,627 delegated lines myself. A reviewer
picking ten regions at random from those files is sampling work I sampled, not
work I read. The one error the sample found was a real one, at a rate of 1 in
10 — so the honest expectation is that **more misclassifications of that size
remain**, and the right posture toward any single delegated region is the
posture toward any single measured line: reproducible from its line range, and
worth re-reading before a deletion is made on it. The four category *totals*
are robust to errors of this size — the corrected region moved 2 lines of
11,000 — but an individual row is not.
## 1e. The method, stated per file

`§ 6` of the spec's *What it must not do* requires the method to be stated per
file, not once for the corpus, because "I did not grep" is a claim that has to
be checkable against the file it is made about. `R` = read in full; the
`stmts` column names the constructs whose statement map was used to split them
rather than round them.

| file | how it was decided | split by statement map |
|---|---|---|
| `viewer/parsers.py` | R, by me. AST construct list in file order; the ~230 lines of dataclasses classified by **the source their producers read**, not by their names | `parse_board`, `parse_okr`, `_parse_okr_objectives`, `parse_phase`, `parse_top_risks`, `walk_design`, `_load_ops_counts`, `load_snapshot` |
| `bin/perry-goals` | R. `okr.jsonl`'s actual contents read first (38 `kr`, 10 `objective`, 3 `version`) so "a store already holds it typed" was a fact rather than an assumption | `Okr`, `write_okr_and_store`, `kr_rows`, `build`, `cmd_link`, `cmd_commit`, `register_drift`, `migrate_commitments`, `main` |
| `bin/perry-diagnose` | R. Store test applied **before** the flat markdown rule, because this tool scans folders Perry does not own (§ 2) | `open_user_asks`, `scan_docs`, `scan_work_modes`, `scan_tracking`, `scan_concurrency`, `split_dangling`, `evidence_for` |
| `bin/perry-state` | R, then **the `parsers.py` implementation of every `P.*` call it makes was read** to find where each fact physically comes from. Two conclusions checked by running the tool (`--section risks`, `--section user_input_queue`) | `build`, `reconcile_drift`, `roles_profile`, `parse_config`, `dossier_records` |
| `bin/lib/__init__.py` | R. Rule applied uniformly: produces/consumes a markdown cell, row, column, table or heading → OBSOLETE, whatever it is called | `task_status_index` (the only one that actually split), checked on `plan`, `same_action_linkage`, `kr_progress_provenance`, `blank_code_spans`, `summary_shape` |
| `bin/perry-tasks` | R, by me. Every `cmd_*` interleaves a typed store read/write with a board derivation or a byte-compare gate, so all seven were split | all seven `cmd_*`, and `main` by subcommand |
| `bin/perry_md_store.py` | R, by me. The file is two things wearing one name — the `okr.jsonl`/`config.jsonl` record shape, and the `OKR.md` scanner/renderer | `main`, by subcommand |
| `bin/perry_store.py` | R. Classified by whether the call site produces or consumes a markdown cell/row/table, or a `.jsonl` record | `risk_record`, and the four `*_plan`/`*_render` pairs checked for internal mixing |
| `bin/perry-explain` | R. `harvest`'s 100-line loop split at the four branches it actually contains (filename, table row, heading, YAML) plus the mention accumulator | `harvest`, `typed_task_lookup` |
| `bin/perry-churn` | R, every function. **No markdown parse exists anywhere in the file**, so nothing could be OBSOLETE; it is `git log --numstat`, path classification and calendar arithmetic | — |
| `bin/perry-knowledge` | R. The card *files are* the record (no store), so reading them is not OBSOLETE; `INDEX.md § Cards by topic` is a render of those files and is | `cmd_promote`, `read_cards` |
| `bin/perry-decide` | R. Classified against the ADR markdown, which `DESIGN-013 § 5.3` made **canonical** when it deleted `DECISIONS.md` — so no projection is being parsed | `cmd_status`, `cmd_supersede`, `cmd_new` |
| `bin/perry-state-cost` | R, every function. Each is `git ls-tree`/`rev-list`/`cat-file --batch-check`/`count-objects` output parsed to integers, or schema `claims` matched by path prefix. **Does not import `re`** | — |
| `viewer/tables.py` | R, every function. Splitting, splicing, widening and rendering a `\| a \| b \|` row is a rendered table → OBSOLETE; the two exceptions are in § 9 | `render_row`, `check_cell` |
| `bin/perry-context-budget` | R, every function. Transcript records are JSONL with a typed `usage` object; block kinds are a four-value enum; the ceiling comes from flag/env/store/schema | `ceiling`, `main` |
| `bin/perry-config` | R, **every path traced to the file it opens**. The only document it touches is `.perry/config.jsonl` | `main` |
| `bin/perry-restore-check` | R. Every fact comes from `git show <ref>:<path>` and `hashlib.md5`; it reads no project state at all | `main` |
| `bin/perry-okr` | R. 20 code lines: imports, a `SURFACE` built by `store.surface(store.OKR)`, a `--help` branch, one delegation | — |
| `bin/perry-dispatch-limit` | R line by line (no AST). Every call site asked what it touches: `mkdir` mutex, `kill -0`, mtime-vs-TTL, atomic rename, a charset gate, a closed executor enum | — (sh; heredoc map from Appendix B) |
| `bin/perry-update-check` | R line by line. Discriminator was **which git surface it reads**: `status --porcelain`, `rev-parse`, `rev-list --count` — machine contracts. `SKILL.md` appears only inside `[ -f ... ]`; the file is never opened | — |
| `bin/perry-codex-preflight` | R line by line. `command -v`, `sort -V`, a cache mtime vs TTL, an exit code, a sentinel-token test | — |
| `bin/perry-detect-host` | R line by line. A closed four-token output alphabet reached from env sentinels and `ps -o comm=` globs | — |

**Where a name would have produced the wrong answer**, per the four worked
examples in § 1 and the ten negative controls in § 9. The two rules applied
everywhere, and the reason each exists:

- **A function is never rounded to one category.** `perry-goals §
  mint_commitment_id` is TYPED id minting with one OBSOLETE line in it;
  `perry-state § reconcile_drift` is a store loop with 20 of its 47 lines
  reading a second markdown parse.
- **A name is never the evidence.** `perry_store § duplicate_record_ids` and
  `§ duplicate_row_ids` differ by four characters and land in opposite
  categories; `perry-goals § tracks_of` has comments about
  `.perry/config.md § Tracks` throughout and reads `.perry/config.jsonl`.

## 2. The four categories as applied

| category | ADR-007 basis | test used at the call site | destination |
|---|---|---|---|
| **TYPED / DETERMINISTIC** | rule 1 | reads a bounded value space (schema enum, id format, ISO date, count), computes an exact filesystem/clock fact, or reads/writes a typed JSONL record | **stays in Python** |
| **OPAQUE DOCUMENT TRANSPORT** | rule 2, second half | locates, reads, stores or renders a full body without interpreting its content | **may stay** |
| **AGENT-OWNED INTERPRETATION** | rule 2, first half + § 5b | extracts or judges meaning from an unbounded value space | **moves to a named agent workflow** |
| **OBSOLETE REPRESENTATION** | rule 3 + ADR-006/ADR-010 | parses or writes a projection for a fact one of the JSONL stores already holds typed | **deleted** once its store read exists |

The boundary that does the work is the last two, and it is the same boundary
`TASK-263` drew: a path that parses `BOARD.md` for a status is **not**
interpretation needing an agent — the fact is typed in `perry/tasks.jsonl` and
the parse is simply obsolete. It is only AGENT when **no typed store holds the
answer**.

Two of `TASK-263`'s rulings were carried across unchanged, because changing
either would have made the two censuses incomparable:

- **Heading and column matching against a declared spelling set** — the i18n
  glossary, `squash`, `header_index`, alias tables, "is this heading that
  heading?" — is **OBSOLETE**, not AGENT. It is a bounded lookup that exists
  only to read a render.
- **The cadence family is OBSOLETE with no destination store on disk**
  (`TASK-263 § 7.5`). Its destination is `perry/cadence.jsonl`, which does not
  exist yet.

One boundary case `TASK-263` never had to rule on came up here and is recorded
because it changes counts: **markdown structure inside a document Perry does
not own.** `bin/perry-diagnose` scans arbitrary user projects — `AGENTS.md`,
`README`, `.cursor/rules`. A `## heading` read there is markdown structure
(→ OBSOLETE by the flat rule) but for a fact no store will ever hold
(→ "deleted once its store read exists" can never fire). **The store test was
applied first**: no store, unbounded prose, so AGENT. That ruling moves roughly
83 lines in `perry-diagnose` and is the reason its AGENT count is not near zero.

## 3. Support buckets, named

| bucket | what is in it | derived by |
|---|---|---|
| `SUPPORT:shebang` | line 1 | text |
| `SUPPORT:docstring` | module + every function/class docstring span | AST (0 for sh) |
| `SUPPORT:comment` | whole-line `#` comments, heredoc bodies excluded | text |
| `SUPPORT:blank` | whitespace-only lines | text |
| `SUPPORT:cli-plumbing` | argv/argparse, subcommand dispatch, exit codes, `--help` and `SURFACE` contract strings, refusal copy, output formatting that carries no document | authored region |
| `SUPPORT:imports` | `import` statements, the `sys.path` bootstrap, `SourceFileLoader` sibling loads | authored region |

## 4. The census

### 4.1 Totals over the 22 files

```
    TYPED / DETERMINISTIC          6,440
    OPAQUE DOCUMENT TRANSPORT        167
    AGENT-OWNED INTERPRETATION       847
    OBSOLETE REPRESENTATION        3,546
    SUPPORT:cli-plumbing           2,705
    SUPPORT:imports                  335
    SUPPORT:docstring              5,898
    SUPPORT:comment                4,838
    SUPPORT:blank                  2,339
    SUPPORT:shebang                   17
    ------------------------------------
    TOTAL                         27,132   = wc -l   closes
```

**The four-category base is 11,000 lines.** Every percentage below uses that
base; the wider base of all code lines (the four categories plus `cli-plumbing`
and `imports`, 14,040) is given wherever it would change a reading.

| category | lines | % of the 11,000 |
|---|---:|---:|
| TYPED / DETERMINISTIC | 6,440 | **58.5%** |
| OBSOLETE REPRESENTATION | 3,546 | 32.2% |
| AGENT-OWNED INTERPRETATION | 847 | 7.7% |
| OPAQUE DOCUMENT TRANSPORT | 167 | 1.5% |

### 4.2 Per file

| file | lines | TYPED | TRANSPORT | AGENT | OBSOLETE | four | support | regions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `viewer/parsers.py` | 4,902 | 870 | 8 | 578 | **771** | 2,227 | 2,675 | 151 |
| `bin/perry-goals` | 3,138 | 693 | 35 | 8 | **516** | 1,252 | 1,886 | 136 |
| `bin/perry-diagnose` | 2,818 | 1,028 | 12 | 93 | **217** | 1,350 | 1,468 | 82 |
| `bin/perry-state` | 2,657 | 745 | 3 | 75 | **167** | 990 | 1,667 | 133 |
| `bin/lib/__init__.py` | 2,154 | 370 | 40 | 61 | **37** | 508 | 1,646 | 46 |
| `bin/perry-tasks` | 1,928 | 318 | 0 | 0 | **585** | 903 | 1,025 | 85 |
| `bin/perry_md_store.py` | 1,675 | 352 | 0 | 0 | **419** | 771 | 904 | 43 |
| `bin/perry_store.py` | 1,667 | 224 | 0 | 0 | **570** | 794 | 873 | 47 |
| `bin/perry-explain` | 920 | 182 | 29 | 17 | **90** | 318 | 602 | 43 |
| `bin/perry-churn` | 745 | 228 | 0 | 0 | **0** | 228 | 517 | 24 |
| `bin/perry-knowledge` | 688 | 196 | 27 | 15 | **49** | 287 | 401 | 35 |
| `bin/perry-decide` | 620 | 166 | 13 | 0 | **0** | 179 | 441 | 22 |
| `bin/perry-state-cost` | 604 | 209 | 0 | 0 | **0** | 209 | 395 | 24 |
| `viewer/tables.py` | 496 | 22 | 0 | 0 | **123** | 145 | 351 | 19 |
| `bin/perry-context-budget` | 460 | 180 | 0 | 0 | **0** | 180 | 280 | 24 |
| `bin/perry-dispatch-limit` | 448 | 223 | 0 | 0 | **0** | 223 | 225 | 28 |
| `bin/perry-config` | 386 | 134 | 0 | 0 | **0** | 134 | 252 | 16 |
| `bin/perry-restore-check` | 315 | 87 | 0 | 0 | **0** | 87 | 228 | 19 |
| `bin/perry-update-check` | 192 | 95 | 0 | 0 | **0** | 95 | 97 | 15 |
| `bin/perry-codex-preflight` | 150 | 79 | 0 | 0 | **0** | 79 | 71 | 12 |
| `bin/perry-detect-host` | 101 | 39 | 0 | 0 | **0** | 39 | 62 | 8 |
| `bin/perry-okr` | 68 | 0 | 0 | 0 | **2** | 2 | 66 | 6 |
| **total (22)** | **27,132** | **6,440** | **167** | **847** | **3,546** | **11,000** | **16,132** | **1,018** |

**OBSOLETE is not spread evenly and that is the most actionable thing in the
table.** Five files carry 2,861 of the 3,546 obsolete lines — **81%** — and
**ten of the 22 files carry none at all**. Those ten are 4,021 lines
(`perry-churn`, `perry-decide`, `perry-state-cost`, `perry-context-budget`,
`perry-dispatch-limit`, `perry-config`, `perry-restore-check`,
`perry-update-check`, `perry-codex-preflight`, `perry-detect-host`), and no
row in `DESIGN-014`'s plan deletes a line of any of them.

## 5. Question 1 — does TASK-263's ratio hold outward?

**The four totals, side by side.**

| | TASK-263 (2 files) | TASK-348 (22 files) | composed (24 files) |
|---|---:|---:|---:|
| physical lines | 12,995 | 27,132 | 40,127 |
| four-category base | 5,566 | 11,000 | 16,566 |
| TYPED / DETERMINISTIC | 2,678 (48%) | **6,440 (58.5%)** | **9,118 (55.0%)** |
| OPAQUE DOCUMENT TRANSPORT | 123 (2%) | 167 (1.5%) | 290 (1.8%) |
| AGENT-OWNED INTERPRETATION | 683 (12%) | 847 (7.7%) | 1,530 (9.2%) |
| OBSOLETE REPRESENTATION | **2,082 (37%)** | 3,546 (32.2%) | **5,628 (34.0%)** |

**The answer is: half of it holds, and the half that does is the half that
matters. Stated plainly, because the spec asks for it plainly.**

**The ratio holds, and strengthens.** `TASK-263` found OBSOLETE larger than
AGENT by 3:1 — 2,082 against 683, a factor of **3.05**. Across the other 22
files the same comparison is 3,546 against 847, a factor of **4.19**. Composed
over all 24 files it is 5,628 against 1,530, **3.68:1**. So the census's main
correction to how `ADR-007` is usually summarised survives going outward and
gets sharper: the ADR is remembered for *"no regex asks prose a question"*, and
1,530 lines project-wide do that, while **nearly four times as much code is not
asking prose anything — it is re-deriving, out of a rendering, a fact a JSONL
store one directory away already holds typed.** Most of the removable code is
still deletable without an agent being involved at all.

**The headline does not hold. OBSOLETE is no longer the largest category.**
`TASK-263`'s § 9 result 2 opens *"OBSOLETE is the largest category across both
files"*, and in `perry-task` and `perry-lint` it was. Across the other 22 files
it is not, and it is not close: **TYPED is 6,440 against OBSOLETE's 3,546 — 1.8
times larger.** Composed over all 24 files TYPED is 9,118 against 5,628, and
TYPED is the largest category in the project by a clear margin.

**Why the two files were unrepresentative, which is the useful part.** The
divergence is not noise and it is not a boundary that was drawn differently.
`perry-task` and `perry-lint` are the two files in the project whose *job* is
the board: one writes it, one checks it. Selecting them and finding
representation-layer code is close to selecting on the outcome. The 22 files
outside them contain the project's determinism — id minting and the store
transaction's other half, the config store, root resolution, the git-object
walkers, the lock, the budget arithmetic, the whole of `perry-diagnose`'s folder
audit — and that determinism is 6,440 lines, larger than everything condemned.

So both of `TASK-263`'s readings need restating rather than one replacing the
other, and § 12 files a row to do it in `DESIGN-014` itself:

- **Right, and now measured project-wide:** obsolete representation outweighs
  prose-interpretation by roughly 4:1, so the bulk of the removable code needs
  a store read, not an agent.
- **Wrong as a project-level claim:** *"OBSOLETE is the largest category."* It
  is the largest category in the two files that render and lint the board. In
  `bin/` and `viewer/` as a whole, the largest category is the code that stays.

## 6. Question 2 — is "condemned in full" true?

**No. It is wrong by a factor of about five, and it is wrong in a way that
would break the project if acted on.**

`DESIGN-014 § 5.1` category B lists three files as representation layer entire,
under the heading *"Condemned by `ADR-011`, preconditions unchanged"*. Counted
by call site:

| file | lines | OBSOLETE | % of lines | TYPED | AGENT | TRANSPORT |
|---|---:|---:|---:|---:|---:|---:|
| `viewer/parsers.py` | 4,902 | **771** | 15.7% | 870 | 578 | 8 |
| `bin/perry-tasks` | 1,928 | **585** | 30.3% | 318 | 0 | 0 |
| `bin/perry_md_store.py` | 1,675 | **419** | 25.0% | 352 | 0 | 0 |
| **total condemned** | **8,505** | **1,775** | **20.9%** | **1,540** | **578** | **8** |

**1,775 of 8,505 lines.** Against their own four-category base of 3,901 the
share is 45.5% — still under half. On no reading is any of the three
representation layer entire, and in `viewer/parsers.py` — the largest single
entry in category B, and the one `§ 5.2` singles out as *"4,603 lines of parser
for a file the project has decided to delete"* — **OBSOLETE is not even the
largest category. TYPED is (870), and AGENT (578) is close behind.**

### 6.1 The finding the spec asked for: the condemned files carry typed operations nothing else implements

The spec says *"If a condemned file carries typed operations nothing else
implements, that is a finding and it changes what `ADR-011` Tier B can delete."*
It does, and the sharpest instance is not a peripheral helper — **it is the code
path every tool in `bin/` runs before it can do anything at all.**

**Every Perry tool resolves where the project's files are through a chain that
runs through two of the three condemned files.** Traced by reading each hop:

```
any of the 20 executables
  -> parsers.resolve_state_root(project_root)        [condemned file 1]
  -> parsers.declared_state_root
  -> parsers.config_store_settings
  -> parsers.config_store_records                     reads .perry/config.jsonl
  -> perry_md_store.validate_records(load_store(p))  [condemned file 3]
```

`viewer/parsers.py § config_store_records` is **the only reader of
`.perry/config.jsonl`** in the tree, and it imports `bin/perry_md_store.py`
inside the function body to validate what it read. `bin/perry-state §
_validated_config_records` is a wrapper over it and says so in its own
docstring: *"The implementation moved to `viewer/parsers.py §
config_store_records` and this is the row-shaped wrapper over it."*
**Fifteen code files under `bin/` and `viewer/` reference
`resolve_state_root`** — every executable that resolves a root, plus
`bin/lib`, `bin/perry_md_store.py` and `parsers.py` itself. (Counted excluding
`bin/README.md` and `bin/ARCHITECTURE.md`, which mention it in prose; a first
count of seventeen had included them.) Deleting either file per Tier B removes
root resolution and the typed config store from all fifteen.

That is the general case; five more specific ones, each verified by grepping
for the implementation and finding exactly one:

1. **The only `.perry/config.jsonl` reader and validator** —
   `parsers § config_store_records` / `config_store_settings` (37 TYPED lines)
   plus `perry_md_store § validate_records` / `load_store` / `STORED` /
   `record_key` (about 110 TYPED lines). No second implementation exists.
2. **The only root-resolution pair** — `parsers § resolve_state_root` /
   `resolve_project_root` / `configured` / `exists_or_unreadable`. Called before
   any tool can report anything, which is why the code sits at the bottom of
   the import graph and not in a `bin/` tool.
3. **The only YAML parser** — `parsers § parse_yaml_subset` /
   `split_frontmatter` / `_lift_block_scalars` / `_split_flow`, 178 TYPED lines,
   whose live caller is `bin/perry-lint § 488-495` reading spec frontmatter.
4. **The only ADR reader** — `parsers § read_adr_records` / `adr_header_fields`.
   `bin/perry-decide` binds it directly: `read_adrs = P.read_adr_records`.
   `DESIGN-013 § 5.3` made `decisions/ADR-*.md` canonical on purpose, so this
   is not migration debt — and `ADR-011` Tier B deleting `parsers.py` takes the
   decide lane's only ADR reader with it. **Neither DESIGN-014 table says so.**
5. **The only `linkage.jsonl` reader** — `parsers § load_linkage_store` /
   `linkage_from_store` / `linkage_records_for_phase` / `load_linkage`, about
   135 TYPED lines, consumed by `perry-state`, `perry-goals` and
   `perry-explain`.

`bin/perry-tasks`, the second condemned file, is a milder version of the same
shape: its 318 TYPED lines include
`write_store_or_say_what_would_land` — the atomic writer for `risks.jsonl`,
`intake.jsonl` and `asks.jsonl` — and `registers()`, which reads the declared
register list out of the schema. Its OBSOLETE 585 is genuinely the board
projection and genuinely goes; its typed core is the three registers' write
path.

### 6.2 What this changes about Tier B

**`ADR-011` Tier B cannot delete these three files. It can delete 1,775 lines
inside them**, and the remaining 1,540 TYPED and 578 AGENT lines need a
destination before any deletion is safe. The two are not the same operation
and `§ 5.1` currently names only the first.

Concretely, before a Tier B deletion can be scheduled, something has to own:
the config store reader and validator, root resolution, the YAML subset, the
ADR reader, and the linkage store reader. None of those is representation
layer, none of them has a second implementation, and the census found no row
filed for any of them.

### 6.3 A smaller finding in the same file: 131 lines with no production caller

While reading `parsers.py` for question 2 the conformance family came up with
no live caller. Verified rather than assumed:

- `read_conformance`, `_declaration_from`, `declaration_line`,
  `render_conformance` (TYPED, the `.perry/conformance.jsonl` store) and
  `read_legacy_conformance` (OBSOLETE, the markdown record), about **131 code
  lines with the constants**.
- Their documented caller is `bin/perry-conform`. **`bin/perry-conform` does not
  exist** — `ls bin/perry-conform` returns no such file; it was deleted by
  TASK-261 / USER-910, which `TASK-263 § 10` already recorded from the other
  direction (a `perry-lint` docstring still naming it).
- Grepping `bin/` and `viewer/` for all five functions returns nothing outside
  `parsers.py` itself. The only callers are in `tests/`.

So `.perry/conformance.jsonl` has a reader, a writer and a serialiser, and
nothing in `bin/` reaches any of them. This is neither OBSOLETE nor AGENT — it
is dead, and it is counted in this census under the categories its call sites
would have had. It is not deleted here (this row changes no behaviour) and § 12
files it.
## 7. Destinations — every non-typed group

The spec requires each non-typed path to name its owning function, its
downstream callers, a concrete replacement store/manifest or agent workflow,
and its deletion dependency, including **what happens to the call site if the
deleting row does not land**. Grouped by destination.

### 7.1 OBSOLETE → `perry/tasks.jsonl`, rendered by a command rather than a file

Owners: `perry_store § plan`/`render`/`board_order`/`cell_text`/`describe_cell`/
`render_line`/`row_descriptor`/`slot_descriptor`/`render_lines`;
`perry-tasks § build`/`plan`/`render`/`write_board_or_refuse`/`cmd_render`/
`main`'s `write --from-board` and `diff`; `parsers § _parse_task_table`/
`_split_status`/`parse_board`'s section walk; `viewer/tables.py § split_row`/
`render_row`/`render_separator`/`cell_spans`/`splice_cell`/`append_cell`;
`lib § task_status_index`'s board arm; `perry-goals § build:1107-1124`;
`perry-state`'s BOARD.md group.
Callers: `bin/perry-task` at five `markdown_tables` sites and `board_order`;
`perry-tasks`' render/write verbs; `perry-lint`'s drift census; the four skill
lanes through `perry-state --compact`.
Replacement: `perry/tasks.jsonl`, which holds every field these rebuild.
Deletion dependency: **TASK-237** (*"BOARD.md stops existing; the board is what
a command prints"*, not_started). **If TASK-237 does not land, none of it can
go** — these are the only thing keeping the projection in step with the store,
and deleting them without it turns `BOARD.md` into a permanently stale document
(which is **TASK-266**'s subject, also not_started).

### 7.2 OBSOLETE → `perry/risks.jsonl` · `intake.jsonl` · `asks.jsonl`

Owners: `perry_store § risk_section_shape`/`risk_table`/`risk_record`/
`risk_records`/`duplicate_row_ids` and the `intake_*` and `ask_*` twins;
`perry-tasks § cmd_risks_render`/`cmd_risks_write` and the intake and ask
families; `parsers § _parse_risks`/`_parse_risk_table`/`_parse_intake`/
`_parse_user_input`/`ask_is_answered`/`intake_is_discharged`;
`perry-state`'s `risks`/`user_input_queue`/`intake` payload blocks.
Replacement: all three stores are declared in `schema § claims[]` and **all
three are on disk in this repo today** — `risks.jsonl` 4 records, `asks.jsonl`
27, `intake.jsonl` 0.
Deletion dependency: **TASK-268** for risks (not_started). **Nothing is filed
for asks or intake** — see § 11 defect 1. If TASK-268 does not land, the risks
store keeps having no reader while the board keeps having one.

### 7.3 OBSOLETE → `perry/okr.jsonl`

Owners: `perry_md_store § scan_okr`/`_table_sites`/`derive`/`plan`/`render`/
`okr_heading`/`table_under`/`spellings`/`field_map`/`table_columns`;
`perry-goals § cmd_commit`/`migrate_commitments`/`read_commitments`/`Okr`'s
table machinery/`column_at`/`header_language`/`display_name`;
`parsers § _parse_krs`/`_table_rows`/`_col`/`parse_okr`'s version walk;
`perry-okr:60-61`.
Replacement: `okr.jsonl` — verified on this repo as 38 `kr`, 10 `objective`,
3 `version` records. The store **read** already exists; the missing half is a
store-first **write**: `perry-goals commit` still decides against markdown
cells and splices them.
Deletion dependency: **TASK-236** (*"OKR.md drops its KR tables"*,
not_started). **Its scope as written is the KR tables only.** Nothing in the
backlog names the `## Commitments` table's deletion — **TASK-042 covered it and
is `dropped`** — so 337 of these lines have no row at all. If TASK-236 does not
land, `perry-okr`'s 68 lines and `perry_md_store`'s 419 OBSOLETE lines stay
together, and `render --write` remains the only recovery from store/file drift.

### 7.4 OBSOLETE → `.perry/config.jsonl` (already the only register)

Owners: `perry-state`'s five `.perry/config.md` tombstones (31 lines, which
only `raise TypeError`); `perry-explain § typed_task_lookup:606-609`'s three
legacy adoption probes; `perry-diagnose § scan_tracking:1472-1477`'s
`OKR.md`/`BOARD.md` disjunct; `lib § blank_marker`/`is_blank_cell`/
`normalize_typed_cell`.
Replacement: the store, which `parsers § config_store_settings` already reads.
Deletion dependency: ADR-019's grace period for the tombstones; TASK-247's
successor for the disjuncts. **Nothing breaks today if none of it lands** —
these are dead weight rather than a second live answer.
**One deletion-order hazard, recorded because it is invisible from the table:**
`normalize_typed_cell` is markdown-cell decoration stripping, but `is_iso_date`,
`is_sla_token` and `parse_sla` — all TYPED, all validating writer input — call
it. Deleting the blank-cell group as one unit silently tightens those three
validators, which will then refuse `**2026-09-30**` where they accept it today.

### 7.5 OBSOLETE → `perry/cadence.jsonl`, which does not exist

Owners: `parsers § _parse_cadence`/`_cadence_as_task`/`parse_due`;
`perry-state § cadence_report`.
`TASK-263 § 6.5` reached the same place from `perry-task`'s side.
Deletion dependency: **TASK-198** (*"## Cadence becomes a store"*,
not_started). If it does not land there is nowhere for the fact to go and the
call sites must stay.

### 7.6 OBSOLETE → a printed index, or nothing

Owners: `perry-knowledge § render_cards_section`/`patch_index` and
`cmd_promote`'s write-back (49 lines).
Replacement: `perry-knowledge list` already publishes the same rows typed under
`perry-knowledge/list/1.1` — the `DECISIONS.md` argument `DESIGN-013 § 5.3`
used to delete the decide-lane index.
Deletion dependency: a row moving digest registration and archive metadata out
of `knowledge/INDEX.md`. None filed. Until it lands the cards section cannot go
without taking the digest half of the file with it.

### 7.7 AGENT → the id-title workflow

Owners: `perry-explain § heading_title` and its two call sites (17 lines);
`perry-knowledge § read_cards:208-209` (2 lines, reclassified here — § 9.1).
Callers: `perry-explain <ID>`; `bin/perry-diagnose:910-924`, which loads
`perry-explain` **as a module** and consumes `harvest`.
Replacement: an agent workflow resolving an id to its human name. No store
holds the title of an ADR, DESIGN or USER row.
Deletion dependency: none filed. **Note the coupling**: `perry-diagnose` is the
tool `DESIGN-014` decision 3 explicitly *kept*, and deleting `perry-explain`'s
harvest silently reduces a kept tool's finding set to `{"available": False}`
behind a bare `except Exception`.

### 7.8 AGENT → the escalation pre-flight

Owners: `parsers § extracts`/`line_fragments`/`escalation_fragments`/
`unextractable_lines`/`hook_escalation_lines`/`parse_role_card`/
`read_role_cards`/`escalation_union`/`escalation_pattern`/
`matching_escalations` (about 300 lines); `perry-state § hook_profile`/
`roles_profile`; `perry-diagnose § scan_concurrency`.
Callers: `bin/perry-lint:1638`, `bin/perry-state:1972`, and
`perry-state --compact`'s `roles` key, which is a *declared* contract
(`perry-roles/list/1.1`).
Replacement: `work/reference/dispatch.md` pre-flight step 4 — the procedure
that already replaced `--escalation-scan` when TASK-339 removed it.
Deletion dependency: **TASK-350** (*"ADR-007 census part 3 — setup and the hook
readers"*, not_started). If it does not land, the `unextractable` warnings stay,
and they are the only surface that says a high-stakes bullet arms nothing.

### 7.9 AGENT → the risk-statement reader

Owners: `parsers § parse_top_risks`' bullet arm (114 lines), `_risk_severity`,
`split_severity_marker`, `load_snapshot`'s dedupe-by-statement-text.
This is the largest single AGENT block in the census and it is a genuine one:
it guesses a risk's id and title out of a human's sentence with bold-marker
heuristics, and the table form beside it is the typed alternative that already
exists.
Deletion dependency: **TASK-268**. If it does not land, a project whose risks
are bullets keeps the heuristic; a project whose risks are a table does not
need it.

### 7.10 AGENT → the document-status readers

Owners: `parsers § walk_design`'s header-field arm (50 lines),
`_norm_design_status`, `adr_header_fields`, `read_adr_records`,
`parse_project_state`, `parse_arch_meta`, `_load_ops_counts`'s `index_header`;
`perry-state § expired_sunsets`; `perry-diagnose`'s four AGENT workflows.
Replacement: an agent read, or a typed field on the document's header. For
`Sunset:` specifically a `sunset_date` field converts the site to TYPED
outright.
Deletion dependency: none filed for any of them. **`read_adr_records` must not
be deleted at all** — see § 6.1 item 4; it is the decide lane's only ADR reader.

### 7.11 TRANSPORT — 167 lines, and all of it may stay

`parsers § load_snapshot`'s four whole-body reads; `lib § stage`/`write_atomic`/
`walk_md`; `perry-goals § Okr.__init__`/`render`/`unchanged` (byte-exact body in,
byte-exact body out) and the phase/mission prose passthrough;
`perry-explain § glossary_entry`; `perry-knowledge § render_card` and
`--body-file`; `perry-decide § cmd_new`'s skeleton; `perry-diagnose § read_text`.
None of it interprets anything and none of it has a deletion dependency.
`TASK-263` found 123 such lines and observed that `ADR-007 § 5b`'s *"locate the
file and hand it to an agent"* posture was barely implemented. **That result
holds outward**: 290 lines across all 24 files, 1.8% of the base.

## 8. Ambiguous regions, listed explicitly

Listed rather than resolved silently, with the way each was called and what it
would cost to call it the other way.

1. **Markdown structure in documents Perry does not own** (`perry-diagnose`,
   ~83 lines). The flat rule says OBSOLETE; the category definition says the
   store test decides. Called **AGENT**. Calling it OBSOLETE moves ~83 lines
   and makes `perry-diagnose` read as 18% obsolete rather than 13%.
2. **`perry-diagnose § open_design_decisions`** (41 lines). Table extraction for
   a fact no store holds today. Called **OBSOLETE** on the design template's
   intent that these rows become asks. If that intent is not real, 41 lines
   move to AGENT.
3. **`perry-diagnose § derive_findings`** (292 lines). Each block is one `if`
   containing both the typed predicate and the remedy prose, so it cannot be
   split below statement level. Called **TYPED** whole. Counting the remedy
   prose as plumbing instead would move roughly 200 lines TYPED → cli-plumbing.
4. **`perry-state`'s five `.perry/config.md` tombstones** (31 lines). They parse
   nothing — they `raise`. Called **OBSOLETE** because their whole subject is
   the deleted projection. Read `perry-state`'s OBSOLETE as **136 live
   projection reads + 31 tombstones** if the narrower number is wanted.
5. **`perry-goals § render_krs` / `kr_table_columns`** (25 lines). This is not a
   stored projection — it is the *replacement* read surface TASK-157 created,
   and TASK-236's second deliverable is to judge whether a CLI render is a good
   enough read surface. Called **OBSOLETE**, flagged so the report does not read
   as "delete this": the right row is a replacement of the printer.
6. **`perry-goals § objective_rows:1038-1054`** (8 lines, the file's only AGENT
   site). Joins a document objective to a register objective **by exact match on
   the human-written heading title**. Both sides have typed ids in their own
   stores; nothing typed connects the two id spaces. Called **AGENT**; a stored
   cross-reference converts it to TYPED outright.
7. **`perry_store § risk_record` / `intake_record` / `ask_record`.** Each regexes
   a fact out of a free-text cell, which reads AGENT — but `cleared`,
   `discharged` and `answered` are *stored fields*, so a typed store does hold
   the answer. Called **OBSOLETE**. This is the highest-value application of the
   AGENT/OBSOLETE boundary in the census.
8. **`lib § blank_code_spans`** (61 lines). Transforms a body and hands it on
   (TRANSPORT-shaped) but does look inside, and the quoted-vs-asserted
   distinction it draws decides whether a citation counts. No store holds the
   answer, so OBSOLETE is excluded. Called **AGENT**.
9. **`perry-decide § _flip` / `read_adrs`.** Regex-rewrites `> Status:` in ADR
   markdown. Called **TYPED**: no store holds ADR status, and `DESIGN-013 § 5.3`
   made the ADR file the whole record deliberately. These are the first call
   sites that flip to OBSOLETE the day an ADR store exists.
10. **`parsers § parse_frequency` vs `§ parse_due`.** Both read a cadence cell.
    `parse_frequency` maps a *declared* period vocabulary and is **TYPED**;
    `parse_due` digs a date out of an annotated free-text cell and is
    **OBSOLETE**, with `perry/cadence.jsonl` as its destination.
11. **The dataclasses in `parsers.py`** (about 230 lines). Classified by the
    source their producers read: a shape with a typed-store producer is TYPED
    (`Task`, `KR`, the five `Linkage*`), a shape whose only producer reads a
    render is OBSOLETE (`UserInput`, `Cadence`, `TopRisk`, `BoardState`), a
    shape read out of a document with no store is AGENT (`ADR`, `DesignDoc`,
    `ProjectState`, `ArchMeta`, `RoleCard`). `BoardState` is the weakest call:
    it is filled from the store by `_board_tasks_from_store` and named for the
    projection.
12. **Five call sites reach into `TASK-263`'s two files** and are attributed to
    the call site only, with the callee named: `perry-tasks § build`/`plan`/
    `render`/`risk_board`/`stranded_after_render` all load `bin/perry-task` via
    `SourceFileLoader` and use its `Board` class. Their lines are counted here;
    `Board`'s 259 lines stay in `TASK-263`'s denominator.

## 9. Negative controls

The spec requires at least one call site expected to be OBSOLETE and found
TYPED. There are several, and the most useful ones run in both directions.

**Expected OBSOLETE, found TYPED:**

1. **`viewer/parsers.py § parse_yaml_subset`** (115 lines) — in the file
   `DESIGN-014` condemns as representation layer entire, doing document
   parsing, and it is a bounded YAML grammar whose live caller reads spec
   frontmatter that no store holds. With `split_frontmatter`,
   `_lift_block_scalars` and `_split_flow` this is **178 TYPED lines inside a
   condemned file**, and it is the single largest reason question 2's answer is
   what it is.
2. **`perry_store § duplicate_record_ids`** — documented as "the store-side half
   of `duplicate_row_ids`", named like it, sitting 64 lines from it, and walking
   typed records rather than cells.
3. **`perry-diagnose § broken_refs`** — regexes `MD_LINK`, `BACKTICK`,
   `WIKILINK`, which is markdown render syntax, but the fact it computes is
   `(base / tok).exists()`: an exact filesystem fact no JSONL store can hold.
4. **`perry-goals § resolve_target` / `claimed_by`** (53 lines) — TASK-263's
   "declared spelling set" shape almost exactly, and TYPED because the spelling
   set lives in `linkage.jsonl`, not in a render.
5. **`viewer/tables.py § line_break_at`** — in a file whose docstring is
   "Markdown table surgery", asking whether a value contains any of the eleven
   boundaries `str.splitlines()` breaks on. A bounded character class.
6. **`perry-codex-preflight:143`** — `grep -q "PERRY_OK"` over an **LLM's
   free-text reply**. Unbounded input, which is the AGENT trigger; but the
   extraction is a declared-literal membership test yielding a boolean, and no
   store holds "did the codex smoke pass". TYPED, and the single most arguable
   line in the four shell files.

**Expected TYPED, found OBSOLETE:**

7. **`lib § is_blank_cell` / `blank_marker`** — they read a schema enum
   (`i18n.blank_cell`), raise through `load_schema`, and are documented as "the
   one rule". A bounded lookup that exists only to read and re-write a rendered
   `—`.
8. **`perry-goals § mint_commitment_id`** — id minting is the TYPED example, and
   line 2165 sources one of its three id lists from markdown `Id` cells.
9. **`perry-state § reconcile_drift`** — a `json.loads` loop over
   `.perry/events.jsonl` whose row set comes from a second deliberate markdown
   parse. 20 of 47 lines.
10. **`perry-explain § typed_task_lookup:606-609`** — the store path, calling
    `parsers.configured()`, whose docstring says *"Zero narrow sites remain in
    `bin/` or `viewer/`"*. Four lines below it, three legacy projection probes
    are ORed onto it.

**Verified empirically rather than by reading**, because the claim was strong
enough to be worth executing: `perry-state --section risks` on this repo returns
`"source": "table"` while `perry/risks.jsonl` sits beside it holding 4 records.
Same for asks — 27 records in the store, and `user_input_queue` read off the
board.

### 9.1 A correction this report makes to its own input

`bin/perry-knowledge:208-209` was classified **TRANSPORT** by the reader that
measured it, with the note *"lifts the card's claim sentence out of its H1"*.
The line is:

```python
claim = re.sub(r"^.*?\s+[—–-]\s+", "", first[2:].strip()) if first else ""
```

That is not transport. TRANSPORT requires moving a body **without interpreting
its content**, and this decides where a card's title ends and its claim begins
by looking for a prose dash — the same operation as
`perry-explain § heading_title`, which the same reader classified **AGENT**.
Reclassified here to **AGENT**. Two lines; `perry-knowledge` reads 27 TRANSPORT
/ 15 AGENT rather than 29 / 13, and the corpus totals move from 169/845 to
167/847.

It is recorded rather than silently fixed for the reason `TASK-263` recorded
its two instrument faults: **it was found by the audit described in § 1d, which
sampled ten delegated regions and found one wrong.** A reader is entitled to
know both that the audit ran and what it caught.

## 10. Arithmetic, per file

Each block is the checker's output, followed by that file's complete region
list. The tables **are** the region list: harvested back out of this document
and fed to Appendix A's `check()`, they return these numbers.

The 22 in-scope files come first, in the spec's own order, and sum to 27,132.
`bin/perry` is last, under § 10.23, with its arithmetic kept out of that total
for the reason in § 0.

### `viewer/parsers.py` — 4,902 lines, 151 regions

```
    TYPED                           870
    TRANSPORT                         8
    AGENT                           578
    OBSOLETE                        771
    SUPPORT:cli-plumbing             61
    SUPPORT:imports                  10
    SUPPORT:docstring             1,160
    SUPPORT:comment                 955
    SUPPORT:blank                   489
    ------------------------------------
    TOTAL                         4,902   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `14-55` | 10 | imports | `module` | stdlib, dataclasses, and tables |
| `56-59` | 2 | TYPED | `module` | _SCHEMA_PATH - an exact filesystem fact |
| `60-155` | 29 | OBSOLETE | `_i18n/alias/heading_is/_column_index/_column_keys` | declared spellings of a RENDERED heading or column |
| `156-269` | 26 | OBSOLETE | `RISK_COLUMNS/is_risk_register_header/risk_bullet_text/status_is_cleared` | the four rules for reading a rendered risk row |
| `270-299` | 5 | TYPED | `exists_or_unreadable` | filesystem predicate with a third answer |
| `300-395` | 43 | TYPED | `config_store_records/config_store_settings` | the typed config store, loaded and validated |
| `396-598` | 36 | TYPED | `declared_state_root..STATE_ROOT` | state/project root resolved from the store and the filesystem |
| `599-609` | 1 | TYPED | `module` | CONFORMANCE_FILE - the jsonl store path |
| `610-614` | 1 | OBSOLETE | `module` | CONFORMANCE_LEGACY_FILE - the markdown record |
| `615-619` | 3 | TYPED | `module` | CONFORMANCE_FIELDS/KIND - the stored field order |
| `620-639` | 3 | OBSOLETE | `module` | _CONFORMANCE_ROW/_FENCE - markdown row probes |
| `640-777` | 76 | TYPED | `Declaration..render_conformance` | the jsonl declaration record, read and serialised |
| `778-917` | 48 | OBSOLETE | `read_legacy_conformance` | the .perry/conformance.md table, read once to convert it |
| `918-960` | 16 | TYPED | `Task` | the published row shape - hydrated from tasks.jsonl |
| `961-1106` | 68 | OBSOLETE | `UserInput/Cadence/Risk/TopRisk/ScopeTrigger/BoardState` | shapes whose only producer reads a rendered section |
| `1107-1116` | 8 | TYPED | `KR` | the KR shape - hydrated from okr.jsonl |
| `1117-1174` | 40 | OBSOLETE | `Objective/OKR/Phase` | document shapes carrying raw_body and raw_text |
| `1175-1269` | 47 | TYPED | `LinkageProject..Linkage` | the linkage.jsonl record shapes |
| `1270-1280` | 8 | TYPED | `OpsCounts` | filesystem counts |
| `1281-1290` | 8 | AGENT | `ADR` | the shape read out of an ADR document's header |
| `1291-1308` | 14 | TYPED | `EvidenceFile/JournalEntry` | path, mtime and size |
| `1309-1337` | 23 | AGENT | `CarryForward/ProjectState/ArchMeta` | shapes read out of PROJECT_STATE.md and ARCHITECTURE.md prose |
| `1338-1381` | 12 | AGENT | `DesignDoc` | the shape read out of a design document's header |
| `1382-1390` | 2 | TYPED | `module` | TASK_STORE and the terminal statuses |
| `1391-1414` | 9 | TYPED | `load_task_store` | tasks.jsonl -> records |
| `1415-1441` | 10 | TYPED | `_task_from_record` | one stored record -> the published Task |
| `1442-1478` | 15 | TYPED | `_records_by_group` | rows by section, ordered by the stored order field |
| `1479-1507` | 15 | TYPED | `_board_tasks_from_store` | fills the task lists, reads no markdown |
| `1508-1517` | 2 | TYPED | `parse_board` | the BoardState the registers are read into |
| `1518-1520` | 2 | TYPED | `parse_board` | store path: no task row is read from text |
| `1521-1524` | 3 | OBSOLETE | `parse_board` | Last updated: regexed out of the render |
| `1525-1570` | 36 | OBSOLETE | `parse_board` | the section walk and its heading dispatch |
| `1571-1574` | 2 | OBSOLETE | `parse_board` | the Backbone sub-group walk |
| `1575-1586` | 10 | AGENT | `parse_board` | does a free-text Blocks cell name a P0 id |
| `1587-1590` | 1 | OBSOLETE | `parse_board` | the assembled board state |
| `1591-1593` | 1 | TYPED | `module` | _STATUS_ENUM - the schema's six values |
| `1594-1615` | 9 | OBSOLETE | `_split_status` | a rendered Status cell split into enum and note |
| `1616-1732` | 61 | OBSOLETE | `_parse_task_table` | every task row of every table in a section |
| `1733-1758` | 20 | TYPED | `module` | the declared period vocabulary and unit table |
| `1759-1787` | 20 | TYPED | `parse_frequency` | a bounded period vocabulary -> (n, unit) |
| `1788-1811` | 14 | TYPED | `advance` | calendar arithmetic, no document |
| `1812-1824` | 6 | TYPED | `next_due_after` | the next occurrence, computed |
| `1825-1866` | 4 | OBSOLETE | `module` | _ISO_WEEK/_ANNOTATION/_NO_DATE - rendered-cell probes |
| `1867-1911` | 7 | OBSOLETE | `INTAKE_COLUMNS/is_intake_register_header/intake_is_discharged` | the intake register's rendered columns |
| `1912-1964` | 23 | OBSOLETE | `parse_due` | a date dug out of an annotated Next due cell |
| `1965-2043` | 48 | OBSOLETE | `_parse_cadence` | the Cadence table walked by column index |
| `2044-2067` | 11 | OBSOLETE | `_cadence_as_task` | a cadence row projected into a task row |
| `2068-2093` | 4 | OBSOLETE | `USER_COLUMNS/is_user_register_header` | the ask register's rendered columns |
| `2094-2141` | 4 | OBSOLETE | `ask_is_answered` | is this rendered Status cell still open |
| `2142-2219` | 43 | OBSOLETE | `_parse_user_input` | the User Input Queue table walked by index |
| `2220-2230` | 3 | OBSOLETE | `_risk_bullets` | risk bullets located in a section |
| `2231-2272` | 28 | OBSOLETE | `_parse_intake` | the Intake table walked by header key |
| `2273-2290` | 9 | OBSOLETE | `_parse_risks` | the risks section, table form then bullet form |
| `2291-2355` | 12 | OBSOLETE | `_parse_backbone` | the Backbone sub-tables |
| `2356-2361` | 4 | OBSOLETE | `module` | _RE_KR_ID/_RE_KR_BULLET - KR ids in a render |
| `2362-2397` | 24 | OBSOLETE | `_table_rows` | markdown table extraction, keyed by header |
| `2398-2418` | 13 | OBSOLETE | `_col` | a cell by any declared spelling of its column |
| `2419-2447` | 26 | OBSOLETE | `_parse_krs` | KR rows, table form then bullet form |
| `2448-2452` | 2 | OBSOLETE | `_clean_heading_title` | heading decoration stripped |
| `2453-2464` | 7 | OBSOLETE | `_section` | a section body sliced by heading match |
| `2465-2474` | 4 | OBSOLETE | `_strip_comments` | HTML comments removed from a body |
| `2475-2485` | 8 | OBSOLETE | `_bullets` | bullet lines of a section |
| `2486-2504` | 10 | TYPED | `OKR_STORE/load_okr_store` | okr.jsonl -> records |
| `2505-2519` | 2 | TYPED | `_heading_key` | the key a stored KR is filed under |
| `2520-2543` | 16 | TYPED | `_krs_from_store` | stored KR records -> KR, ordered by order |
| `2544-2554` | 3 | OBSOLETE | `parse_okr` | the OKR document, comments stripped |
| `2555-2559` | 1 | TYPED | `parse_okr` | store path: KRs come from okr.jsonl |
| `2560-2573` | 9 | AGENT | `parse_okr` | Mission and Operating Principles - prose |
| `2574-2581` | 8 | OBSOLETE | `parse_okr` | the version heading walk |
| `2582-2584` | 1 | AGENT | `parse_okr` | Anti-Goals - prose bullets |
| `2585-2590` | 5 | OBSOLETE | `parse_okr` | the Versioning list re-read out of the render |
| `2593-2597` | 5 | OBSOLETE | `_parse_okr_objectives` | the objective chunk split |
| `2598-2608` | 8 | OBSOLETE | `_parse_okr_objectives` | heading match, then the markdown KR arm |
| `2609-2611` | 3 | TYPED | `_parse_okr_objectives` | the stored-KR arm, keyed by version |
| `2612-2631` | 15 | AGENT | `_parse_okr_objectives` | the objective's intro prose |
| `2632-2638` | 3 | OBSOLETE | `parse_phase` | the phase document, comments stripped |
| `2639-2652` | 9 | AGENT | `parse_phase` | Started/Status header fields out of prose |
| `2653-2662` | 5 | AGENT | `parse_phase` | Phase Focus and Cost Ceiling - prose sections |
| `2663-2671` | 7 | AGENT | `parse_phase` | the scope-reduction section, either spelling |
| `2672-2689` | 14 | AGENT | `parse_phase` | scope-rule status judged from a prose line |
| `2690-2708` | 11 | OBSOLETE | `parse_phase` | the Objective heading walk |
| `2709-2754` | 34 | AGENT | `_parse_scope_triggers` | condition and response split out of a human's trigger sentence |
| `2755-2811` | 35 | OBSOLETE | `_parse_legacy_tripwire_table` | the legacy Trip-wires table |
| `2812-2822` | 1 | OBSOLETE | `module` | _RE_PCT - a percentage in a rendered cell |
| `2823-2848` | 8 | AGENT | `_risk_severity` | TOP RISK/ACCEPT judged out of the sentence |
| `2849-2865` | 8 | AGENT | `module` | _SEVERITY_RANKS/_RE_SEVERITY_MARKER - H/M/L prefixes |
| `2866-2886` | 6 | AGENT | `split_severity_marker` | the magnitude marker a human wrote |
| `2887-2905` | 11 | OBSOLETE | `_has_risk_header` | does this section carry the register header |
| `2906-2965` | 29 | OBSOLETE | `_parse_risk_table` | the risk table, read by column |
| `2966-2988` | 9 | OBSOLETE | `top_risks_section` | the Top risks section located |
| `2989-2999` | 3 | OBSOLETE | `has_risk_table` | table form or bullet form |
| `3000-3013` | 8 | OBSOLETE | `parse_top_risks` | the table arm - rows from the register |
| `3014-3127` | 52 | AGENT | `parse_top_risks` | id and title guessed out of a bullet with bold-marker heuristics |
| `3128-3130` | 1 | TYPED | `module` | ADR_ID_RE - an id shape |
| `3131-3166` | 17 | AGENT | `adr_header_fields` | Name: value pairs out of an ADR header |
| `3167-3204` | 27 | AGENT | `read_adr_records` | title and header fields out of each ADR |
| `3205-3244` | 18 | AGENT | `parse_decisions` | the active ADRs, by their prose status |
| `3245-3335` | 77 | TYPED | `walk_evidence/walk_journal/walk_handoff/walk_weekly` | filesystem walks - name, path, mtime, size |
| `3336-3344` | 7 | AGENT | `module` | _DESIGN_STATUS_ORDER - the surfacing order |
| `3345-3362` | 13 | AGENT | `_norm_design_status` | a status word judged out of prose |
| `3363-3402` | 6 | TYPED | `walk_design` | locate the design directory |
| `3403-3441` | 14 | TYPED | `walk_design` | design_refs counted out of tasks.jsonl |
| `3442-3509` | 50 | AGENT | `walk_design` | title, status, date and Linked OKR out of the header |
| `3510-3513` | 2 | TYPED | `walk_design` | the declared sort order |
| `3514-3522` | 2 | TYPED | `_date_desc_key` | a date inverted for sorting |
| `3523-3580` | 43 | AGENT | `parse_project_state` | PROJECT_STATE.md sections and its carry-forwards |
| `3581-3613` | 22 | AGENT | `parse_arch_meta` | ARCHITECTURE.md version, status and open questions |
| `3614-3627` | 6 | TYPED | `split_frontmatter` | the frontmatter block located |
| `3628-3679` | 42 | TYPED | `_lift_block_scalars` | YAML block scalars lifted out |
| `3680-3825` | 115 | TYPED | `parse_yaml_subset` | a bounded YAML grammar, parsed deterministically |
| `3826-3861` | 24 | TYPED | `_split_flow/_as_list/_num` | flow sequences and numeric coercion |
| `3862-3888` | 10 | TYPED | `LINKAGE_STORE/load_linkage_store` | linkage.jsonl -> records |
| `3889-4007` | 69 | TYPED | `linkage_from_store` | typed records -> the Linkage payload |
| `4008-4016` | 4 | TYPED | `linkage_phase_number` | the phase number a slug carries |
| `4017-4080` | 25 | TYPED | `linkage_records_for_phase` | the records belonging to one phase |
| `4081-4106` | 8 | TYPED | `load_linkage` | the store, filtered to a phase |
| `4107-4114` | 4 | TYPED | `kr_objective_id` | the objective a KR id names |
| `4115-4150` | 7 | TYPED | `phase_key_results` | declared KRs, store first |
| `4151-4165` | 6 | TYPED | `kr_metric_cell` | the metric a stored KR declares |
| `4166-4193` | 18 | TYPED | `phase_key_results_by_objective` | KRs attached by their id |
| `4194-4206` | 11 | TYPED | `_load_ops_counts` | inputs counted and aged off the filesystem |
| `4207-4216` | 8 | AGENT | `_load_ops_counts` | the first numeric line of an INDEX.md |
| `4217-4242` | 4 | AGENT | `_load_ops_counts` | three index headers read as prose |
| `4243-4290` | 4 | AGENT | `extracts` | is this fragment long enough to mean anything |
| `4291-4308` | 9 | AGENT | `line_fragments` | backticked spans lifted out of a rule line |
| `4309-4324` | 7 | AGENT | `escalation_fragments` | the union of a document's fragments |
| `4325-4345` | 2 | AGENT | `unextractable_lines` | rule lines that yield no fragment |
| `4346-4367` | 6 | AGENT | `unextractable_says` | the finding, in prose |
| `4368-4371` | 2 | AGENT | `module` | HOOK_SECTION/CARD_SECTION - where the rules live |
| `4372-4388` | 8 | AGENT | `hook_escalation_lines` | the High-stakes bullets of hook.md |
| `4389-4409` | 3 | AGENT | `hook_escalation_unextractable` | those that extract nothing |
| `4410-4443` | 18 | AGENT | `RoleCard/_ROLE_FIELD` | the role card's shape and header labels |
| `4444-4449` | 4 | AGENT | `_role_header_field` | a labelled field out of a role card |
| `4450-4463` | 11 | AGENT | `_loads_topics` | Loads: topics split out of a bullet |
| `4464-4494` | 15 | AGENT | `parse_role_card` | one role card's sections and bullets |
| `4495-4509` | 8 | AGENT | `read_role_cards` | every card under .perry/roles |
| `4510-4568` | 26 | AGENT | `escalation_union` | the project and role fragments, unioned |
| `4569-4606` | 8 | AGENT | `escalation_pattern` | a fragment compiled to a word-bounded probe |
| `4607-4652` | 3 | AGENT | `matching_escalations` | which fragments this text matches |
| `4653-4680` | 6 | AGENT | `spec_scope_sections` | does this spec offer either scope heading |
| `4681-4707` | 20 | cli-plumbing | `PMOSnapshot` | the published payload's fields |
| `4708-4731` | 3 | OBSOLETE | `PMOSnapshot.board_as_authored` | BOARD.md re-parsed as authored |
| `4732-4754` | 9 | OBSOLETE | `PMOSnapshot` | open risks and which form they came from |
| `4755-4762` | 5 | OBSOLETE | `_resolve_project_name` | the name out of the board's H1 |
| `4763-4786` | 8 | TRANSPORT | `load_snapshot` | four whole bodies read and handed on |
| `4787-4821` | 11 | TYPED | `load_snapshot` | the phase pointer resolved, linkage from the store |
| `4822-4838` | 4 | OBSOLETE | `load_snapshot` | top risks off the board render |
| `4839-4852` | 8 | AGENT | `load_snapshot` | risks deduped by their statement text |
| `4853-4854` | 1 | TYPED | `load_snapshot` | the board, with the task store supplied |
| `4855-4877` | 21 | cli-plumbing | `load_snapshot` | the payload assembled |
| `4878-4902` | 20 | cli-plumbing | `module` | the __main__ demo printout |

### `bin/perry-goals` — 3,138 lines, 136 regions

```
    TYPED                           693
    TRANSPORT                        35
    AGENT                             8
    OBSOLETE                        516
    SUPPORT:cli-plumbing            357
    SUPPORT:imports                  40
    SUPPORT:docstring               680
    SUPPORT:comment                 570
    SUPPORT:blank                   238
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                         3,138   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `112-142` | 22 | imports | `module` | stdlib imports, sys.path bootstrap, sibling modules |
| `143-147` | 2 | cli-plumbing | `Refused` | the refusal exception that becomes exit code 1 |
| `148-178` | 9 | OBSOLETE | `naming_the_flag` | names the flag behind a value no markdown cell can hold |
| `179-192` | 4 | OBSOLETE | `unrenderable_refusal` | spells the refusal for a value a markdown table row cannot carry |
| `193-207` | 6 | TYPED | `load_schema` | memoizes state-schema.json for this process |
| `208-231` | 9 | OBSOLETE | `okr_table_spec` | finds the schema's declaration of one OKR.md markdown table |
| `232-251` | 4 | OBSOLETE | `heading_pattern` | turns the schema under-regex into an OKR.md heading matcher |
| `252-271` | 6 | OBSOLETE | `column_spellings` | every declared spelling of a table column, English first |
| `272-276` | 2 | OBSOLETE | `column_at` | index of a column in a markdown header row, by name |
| `277-293` | 8 | OBSOLETE | `header_language` | which language this markdown table's header cells are in |
| `294-309` | 4 | OBSOLETE | `display_name` | how to spell a column name when widening a markdown table |
| `310-317` | 1 | OBSOLETE | `SEPARATOR_RE` | recognises a markdown table separator line |
| `318-356` | 11 | TRANSPORT | `Okr.__init__/render` | reads OKR.md's body and hands it back byte-identical |
| `357-479` | 71 | OBSOLETE | `Okr.section/table/rows/set_cell/widen` | locates headings, table rows and cells and splices them |
| `480-550` | 1 | cli-plumbing | `LIST_CONTRACT` | the payload's contract version string |
| `551-613` | 62 | cli-plumbing | `LIST_SEMANTICS` | the contract's changed-meaning notes, printed in the payload |
| `614-656` | 18 | imports | `_sibling/perry_state` | loads bin/perry-state as a module, once |
| `657-700` | 20 | TYPED | `owned_by_goals/assert_owned` | refuses a write whose path is outside this lane's own files |
| `701-711` | 3 | TRANSPORT | `write_atomic` | writes a whole file body atomically behind the lane gate |
| `712-744` | 3 | TRANSPORT | `write_okr_and_store` | renders the edited OKR.md body to be written |
| `745-745` | 1 | TYPED | `write_okr_and_store` | resolves okr.jsonl's path for this project |
| `746-746` | 1 | OBSOLETE | `write_okr_and_store` | derives store records by scanning the markdown text |
| `747-791` | 30 | TYPED | `write_okr_and_store` | loads, validates and merges okr.jsonl's prior records |
| `792-799` | 8 | OBSOLETE | `write_okr_and_store` | re-renders the store to markdown and gates on byte equality |
| `800-822` | 23 | TYPED | `write_okr_and_store` | reports store drift and records the file no longer renders |
| `823-823` | 1 | TRANSPORT | `write_okr_and_store` | writes OKR.md's body |
| `824-831` | 2 | TYPED | `write_okr_and_store` | writes okr.jsonl under the same lock |
| `832-856` | 2 | TYPED | `project_lock` | takes the one per-project lock |
| `857-860` | 2 | TYPED | `events_path` | the .perry/events.jsonl path |
| `861-884` | 18 | TYPED | `read_events` | reads the JSONL event log, skipping corrupt lines |
| `885-908` | 7 | TYPED | `commitment_events/logged_status` | filters the log by event name and reads the last status |
| `909-930` | 13 | TYPED | `append_event` | appends one JSON event record |
| `931-934` | 2 | cli-plumbing | `plain` | dataclass to dict for the payload; nothing calls it |
| `935-978` | 16 | TYPED | `kr_rows` | reads the register's numbers, task statuses and store records |
| `979-979` | 1 | TYPED | `kr_rows` | starts the flat KR list |
| `980-983` | 4 | OBSOLETE | `kr_rows` | takes the overall KRs from parsed OKR.md, not okr.jsonl |
| `984-1027` | 28 | TYPED | `kr_rows` | assembles each KR row and its current-provenance block |
| `1028-1037` | 8 | TYPED | `days_since` | days between an ISO date in the value and today |
| `1038-1054` | 8 | AGENT | `objective_rows` | matches an objective to a register id by its human-written title |
| `1055-1059` | 3 | OBSOLETE | `objective_rows` | lists an objective's KR ids off the parsed markdown |
| `1060-1075` | 4 | TRANSPORT | `build` | loads the project's documents through the one parser |
| `1076-1079` | 1 | TYPED | `build` | days since the phase started |
| `1080-1086` | 1 | TYPED | `build` | counts the phase's KRs from the linkage store |
| `1087-1094` | 4 | TYPED | `build` | reads the event log and filters KR rows by level |
| `1095-1106` | 6 | TYPED | `build` | decides which source answered: linkage, prose or none |
| `1107-1124` | 12 | OBSOLETE | `build` | collects unlinked task ids off BOARD.md's parsed rows |
| `1125-1151` | 15 | TYPED | `build` | conformance counts over the typed KR rows |
| `1152-1164` | 9 | TYPED | `build` | payload header: contract, sorted semantics, roots |
| `1165-1167` | 3 | OBSOLETE | `build` | publishes OKR.md's version, which okr.jsonl holds typed |
| `1168-1170` | 3 | TRANSPORT | `build` | carries mission, operating principles and anti-goals through |
| `1171-1172` | 2 | OBSOLETE | `build` | publishes the OKR's objectives off the markdown parse |
| `1173-1182` | 10 | TRANSPORT | `build` | carries the phase document's front matter into the payload |
| `1183-1184` | 2 | OBSOLETE | `build` | publishes the phase's objectives off the markdown parse |
| `1185-1197` | 8 | TYPED | `build` | krs, answered_by, unlinked ids and the linkage block |
| `1198-1241` | 6 | TYPED | `build` | counts objectives, KRs and stretch KRs |
| `1242-1263` | 9 | TYPED | `check_writable` | refuses a store value that is empty or spans lines |
| `1264-1276` | 2 | TYPED | `linkage_store_path` | the linkage.jsonl path |
| `1277-1345` | 41 | TYPED | `Register` | loads one phase's slice of linkage.jsonl and its graph |
| `1346-1398` | 23 | TYPED | `linkage_store_text` | appends records and retracts unlinked lines in the JSONL |
| `1399-1416` | 9 | TYPED | `current_phase` | reads the phase/CURRENT pointer |
| `1417-1428` | 8 | TYPED | `kr_ids/objective_of` | the graph's KR ids and which objective a KR sits under |
| `1429-1491` | 47 | TYPED | `resolve_target` | resolves a token to one KR by declared id, project id or alias |
| `1492-1505` | 6 | TYPED | `claimed_by` | which Project already answers to a declared name |
| `1506-1543` | 24 | TYPED | `link_edge` | appends an edge record and retracts the unlinked one |
| `1544-1546` | 1 | TYPED | `TASK_ID_SHAPE` | the shape of a task id |
| `1547-1599` | 27 | TYPED | `link_unlinked` | shape-checks the id and appends an unlinked record |
| `1600-1640` | 25 | TYPED | `link_alias` | appends a project record carrying the new alias |
| `1641-1693` | 35 | TYPED | `link_project` | appends a project record against a declared KR |
| `1694-1696` | 1 | cli-plumbing | `LINK_MODES` | the mode flags link accepts |
| `1697-1707` | 4 | cli-plumbing | `cmd_link` | reads the register out of ctx and the mode off the flags |
| `1708-1735` | 20 | cli-plumbing | `cmd_link` | one mode at a time, the usage line and the argument count |
| `1736-1739` | 3 | TYPED | `cmd_link` | shape-checks each positional as a store value |
| `1740-1748` | 8 | cli-plumbing | `cmd_link` | dispatches to the four link writers |
| `1749-1777` | 6 | TYPED | `cmd_link` | result fields and the nothing-to-write early return |
| `1778-1807` | 21 | TYPED | `cmd_link` | builds the store text and event, writes both |
| `1808-1820` | 3 | OBSOLETE | `commitment_columns` | the Commitments table's declared and optional columns |
| `1821-1841` | 4 | OBSOLETE | `FLAG_FOR_COLUMN` | maps a markdown column to the flag its text arrived on |
| `1842-1850` | 2 | TYPED | `SLA_TOKEN_RE/ISO_DATE_RE` | the two typed spellings a Due value may take |
| `1851-1867` | 7 | TYPED | `real_date/is_sla_token` | reads a Due value as a date or an SLA token |
| `1868-1906` | 14 | TYPED | `tracks_of` | reads the declared tracks from .perry/config.jsonl |
| `1907-1927` | 11 | TYPED | `track_named` | one declared track, or a refusal naming the flag |
| `1928-1973` | 28 | TYPED | `check_due` | validates --due against the track's mode and SLA |
| `1974-1997` | 17 | OBSOLETE | `commitments_table/read_commitments` | locates the markdown table and reads its rows by column |
| `1998-2035` | 14 | OBSOLETE | `legacy_due_at/unsplit_rows` | finds the retired By when column and its unsplit rows |
| `2036-2127` | 69 | OBSOLETE | `migrate_commitments` | splits a markdown column and pads every row for the new one |
| `2128-2139` | 10 | OBSOLETE | `commitment_id_at` | locates the Id column in the markdown header |
| `2140-2142` | 1 | TYPED | `ID_N_RE` | the track/n shape of a commitment id |
| `2143-2164` | 2 | TYPED | `mint_commitment_id` | mints the next id for a track |
| `2165-2165` | 1 | OBSOLETE | `mint_commitment_id` | reads the ids in use out of the markdown rows |
| `2166-2175` | 8 | TYPED | `mint_commitment_id` | the highest id across the log and okr.jsonl, plus one |
| `2176-2198` | 9 | OBSOLETE | `find_commitment` | finds a markdown row by its Id cell |
| `2199-2202` | 2 | TYPED | `COMMITMENT_FIELDS` | the commitment record's stored fields |
| `2203-2267` | 25 | TYPED | `register_drift` | loads and validates okr.jsonl before anything is decided |
| `2268-2281` | 12 | OBSOLETE | `register_drift` | derives the file's records and diffs them against the store |
| `2282-2319` | 26 | OBSOLETE | `check_register_drift` | refuses or accepts a cell the file and the store disagree on |
| `2320-2345` | 14 | OBSOLETE | `check_hand_edit` | compares the row's Status cell with the log's last value |
| `2346-2368` | 12 | OBSOLETE | `template_commitments_block` | copies the template's Commitments heading, note and header |
| `2369-2378` | 3 | cli-plumbing | `cmd_commit` | unpacks the document, the state root and the log from ctx |
| `2379-2381` | 3 | OBSOLETE | `cmd_commit` | gates the write on the file agreeing with okr.jsonl |
| `2382-2392` | 10 | cli-plumbing | `cmd_commit` | refuses incompatible flag combinations |
| `2393-2418` | 23 | OBSOLETE | `cmd_commit` | the --migrate branch: splits the clock column and writes |
| `2419-2449` | 19 | OBSOLETE | `cmd_commit` | creates the ## Commitments section from the template |
| `2450-2477` | 18 | OBSOLETE | `cmd_commit` | locates the table and refuses a register that predates the split |
| `2478-2493` | 14 | OBSOLETE | `cmd_commit` | reads the rows and prepares the widen-a-column closure |
| `2494-2498` | 5 | OBSOLETE | `cmd_commit` | finds the row to end and reads its Status cell |
| `2499-2512` | 13 | OBSOLETE | `cmd_commit` | refuses on the row's Status and Discharged by cells |
| `2513-2526` | 11 | OBSOLETE | `cmd_commit` | writes the Status cell and appends to Discharged by |
| `2527-2534` | 7 | TYPED | `cmd_commit` | the close/miss event record |
| `2535-2537` | 3 | OBSOLETE | `cmd_commit` | finds the row to amend and checks it against the log |
| `2538-2553` | 12 | OBSOLETE | `cmd_commit` | refuses re-dating a passed Due read out of the row |
| `2554-2559` | 2 | TYPED | `cmd_commit` | validates the new --due against the row's track |
| `2560-2591` | 21 | cli-plumbing | `cmd_commit` | collects the amend flags and refuses whitespace-only values |
| `2592-2596` | 5 | OBSOLETE | `cmd_commit` | writes each change into its markdown cell, widening if needed |
| `2597-2602` | 5 | TYPED | `cmd_commit` | the update event record |
| `2603-2616` | 12 | cli-plumbing | `cmd_commit` | refuses a create with no track, promise or party |
| `2617-2620` | 4 | TYPED | `cmd_commit` | resolves the track, validates --due and mints the id |
| `2621-2629` | 5 | TYPED | `cmd_commit` | the new commitment's field values |
| `2630-2647` | 15 | OBSOLETE | `cmd_commit` | checks the header, widens it and renders the row into the table |
| `2648-2655` | 7 | TYPED | `cmd_commit` | the create event record |
| `2656-2660` | 5 | TYPED | `cmd_commit` | result fields carried on every branch |
| `2661-2667` | 4 | cli-plumbing | `cmd_commit` | the --dry-run early return |
| `2668-2676` | 7 | TYPED | `cmd_commit` | names the touched keys, writes the pair and the event |
| `2677-2712` | 6 | OBSOLETE | `canonical_of` | which declared column a markdown header cell is |
| `2713-2730` | 8 | OBSOLETE | `kr_table_columns` | the header of the KR table the phase document used to carry |
| `2731-2746` | 8 | TYPED | `phase_number_to_read` | the three-digit phase number to read |
| `2747-2764` | 6 | cli-plumbing | `cmd_krs` | refuses positionals on a read-only command |
| `2765-2792` | 26 | TYPED | `cmd_krs` | reads one phase's objectives and KRs from linkage.jsonl |
| `2793-2818` | 17 | OBSOLETE | `render_krs` | renders the store as the markdown table the document had |
| `2819-2936` | 63 | cli-plumbing | `COMMANDS/Args/parse` | the subcommand table and the argv parser |
| `2937-2942` | 4 | cli-plumbing | `handoff_line` | the sentence printed after a commit write |
| `2943-2964` | 16 | cli-plumbing | `main` | parses argv, answers a parse-time refusal, checks the command |
| `2965-2967` | 3 | TYPED | `main` | resolves the project root and the state root |
| `2968-3012` | 18 | cli-plumbing | `main` | dispatches the subcommand and builds its context under the lock |
| `3013-3026` | 13 | cli-plumbing | `main` | the refusal channel, in JSON or on stderr |
| `3027-3109` | 77 | cli-plumbing | `main` | prints the payload for a human, per subcommand |
| `3110-3138` | 10 | cli-plumbing | `__main__` | the last-resort refusal handlers and the exit code |

### `bin/perry-diagnose` — 2,818 lines, 82 regions

```
    TYPED                         1,028
    TRANSPORT                        12
    AGENT                            93
    OBSOLETE                        217
    SUPPORT:cli-plumbing            259
    SUPPORT:imports                  27
    SUPPORT:docstring               285
    SUPPORT:comment                 666
    SUPPORT:blank                   230
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                         2,818   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `38-61` | 18 | imports | `module` | stdlib imports plus the sys.path bootstrap for viewer and bin |
| `62-73` | 10 | TYPED | `THRESHOLDS` | numeric budgets compared against counts and day deltas |
| `74-96` | 22 | TYPED | `module` | host rule-file names, globs and the walk skip-dir set |
| `99-113` | 2 | TYPED | `is_nested_repo` | tests for a .git entry to stop at a foreign checkout |
| `114-157` | 29 | TYPED | `module` | extension, manifest, spine, dir-hint and path-token tables |
| `158-163` | 1 | AGENT | `H1` | locates the prose title two documents are judged duplicates by |
| `164-177` | 12 | TYPED | `run_git` | shells out to git for worktree, branch and churn facts |
| `178-185` | 6 | TYPED | `is_script` | reads two bytes to test for a shebang |
| `186-204` | 6 | TYPED | `line_count` | counts the lines of a file |
| `205-220` | 12 | TRANSPORT | `read_text` | reads a whole file body and memoises it uninterpreted |
| `221-228` | 6 | TYPED | `days_since_mtime` | computes whole days between mtime and today |
| `229-232` | 2 | AGENT | `norm_title` | normalises a human title so two can be called the same |
| `233-253` | 11 | TYPED | `is_routed` | tests filename and frontmatter description key for routing |
| `254-268` | 9 | imports | `load_sibling` | imports an extensionless sibling bin script as a module |
| `306-324` | 5 | AGENT | `module` | regexes deciding whether a sentence raises an open question |
| `359-367` | 1 | OBSOLETE | `STATUS_KEYS` | the Status column spelling set from the i18n glossary |
| `368-385` | 7 | OBSOLETE | `module` | heading, column and empty-cell patterns for a rendered table |
| `386-392` | 4 | OBSOLETE | `decision_label` | renders one table cell as a line of evidence |
| `393-485` | 15 | TYPED | `open_user_asks` | collects USER- ids from the index and filters by path |
| `486-544` | 39 | OBSOLETE | `open_user_asks` | parses BOARD.md User Input Queue rows and Status cells |
| `547-599` | 41 | OBSOLETE | `open_design_decisions` | parses User Decisions tables for empty Chosen cells |
| `602-663` | 31 | AGENT | `scan_decision_mentions` | judges whether a prose line raises an undecided question |
| `772-779` | 3 | AGENT | `module` | heading and blockquote marks that call a line a quotation |
| `780-786` | 3 | TYPED | `module` | check-name token patterns over a declared identifier vocabulary |
| `787-812` | 8 | TYPED | `finding_code_re` | builds this tool's finding-code vocabulary and finds it in a line |
| `813-852` | 24 | AGENT | `report_lines` | decides which lines report on a check rather than refer to one |
| `853-887` | 16 | TYPED | `split_dangling` | collects undefined ids and the locations that mention them |
| `888-898` | 7 | AGENT | `split_dangling` | applies the report marks to decide whether an id is live |
| `901-1001` | 43 | TYPED | `scan_user_load` | assembles the human-load payload from the id index and sub-scanners |
| `1004-1032` | 19 | TYPED | `perry_owned_globs` | reads declared state-file paths out of the JSON schema |
| `1035-1047` | 9 | TYPED | `module` | Perry directory names and example-directory names |
| `1069-1108` | 37 | TYPED | `walk` | walks the tree counting md, code and other files |
| `1114-1147` | 32 | TYPED | `scan_context_load` | measures always-loaded rule files by existence and line count |
| `1150-1190` | 26 | TYPED | `broken_refs` | extracts path tokens and tests each against the filesystem |
| `1196-1201` | 6 | TYPED | `scan_docs` | opens every markdown file the walk inventoried |
| `1202-1202` | 1 | AGENT | `scan_docs` | extracts the H1 title for the duplicate judgement |
| `1203-1205` | 3 | TYPED | `scan_docs` | records path and line count per document |
| `1206-1206` | 1 | AGENT | `scan_docs` | stores the human title as the document's identity |
| `1207-1210` | 4 | TYPED | `scan_docs` | records mtime age and wikilink count |
| `1211-1250` | 32 | TYPED | `scan_docs` | resolves link tokens against the file set to build the reference graph |
| `1251-1279` | 15 | TYPED | `scan_docs` | picks index files and entry points, then lists orphans |
| `1280-1297` | 8 | AGENT | `scan_docs` | judges two documents duplicates by their normalised titles |
| `1298-1337` | 33 | TYPED | `scan_docs` | duplicate filenames, oversized docs, broken refs and totals |
| `1343-1365` | 21 | TYPED | `scan_concurrency` | reads git worktrees, branches and 90-day file churn |
| `1366-1375` | 10 | AGENT | `scan_concurrency` | searches the rules prose for a declared isolation policy |
| `1376-1391` | 14 | TYPED | `scan_concurrency` | append-only surfaces by directory name, then payload |
| `1397-1471` | 62 | TYPED | `scan_tracking` | spine, decision-log and runnable-check probes on the filesystem |
| `1472-1474` | 3 | OBSOLETE | `scan_tracking` | tests OKR.md, BOARD.md and phase/ as the adoption marker |
| `1475-1476` | 2 | TYPED | `scan_tracking` | records the state root relative to the project |
| `1477-1477` | 1 | OBSOLETE | `scan_tracking` | installed falls back to the two markdown projections |
| `1478-1488` | 10 | TYPED | `scan_tracking` | payload of spine, decisions, checks and perry flags |
| `1494-1576` | 71 | TYPED | `scan_archetype` | scores archetype from dir names, manifests and file counts |
| `1579-1708` | 112 | cli-plumbing | `WHY` | the per-finding explanation strings the report prints |
| `1711-1746` | 23 | TYPED | `scan_namespace` | lists files under claimed dirs that are not Perry-shaped |
| `1749-1786` | 14 | TYPED | `_perry_shaped` | tests filename patterns and a PERRY_HOME marker |
| `1787-1852` | 8 | TYPED | `module` | mode names, signal weights and the stage value vocabulary |
| `1853-1885` | 21 | OBSOLETE | `column_aliases` | board column names and their i18n spellings from the glossary |
| `1888-1949` | 31 | OBSOLETE | `md_table` | splits ## headings and extracts the first table by header name |
| `1952-1959` | 4 | OBSOLETE | `_as_dict` | reads rendered row cells by column index and counts filled ones |
| `1960-1999` | 16 | TYPED | `_award` | scores signals per mode and ranks them into a confidence |
| `2000-2036` | 7 | TYPED | `scan_work_modes` | reads the track register from the config store with provenance |
| `2037-2059` | 19 | OBSOLETE | `scan_work_modes` | parses BOARD.md and OKR.md tables into row dicts |
| `2060-2063` | 3 | TYPED | `scan_work_modes` | counts phase files and the CURRENT pointer |
| `2064-2064` | 1 | OBSOLETE | `scan_work_modes` | counts Objective headings in OKR.md |
| `2065-2073` | 9 | TYPED | `scan_work_modes` | counts answer files and SRC- digests on the filesystem |
| `2074-2116` | 20 | TYPED | `scan_work_modes` | awards project-wide and work-shape file evidence |
| `2117-2134` | 1 | TYPED | `scan_work_modes` | asks the register whether any track is declared |
| `2135-2141` | 2 | OBSOLETE | `scan_work_modes` | reads the Track cell of board and commitment rows |
| `2142-2168` | 15 | TYPED | `scan_work_modes` | adds the implicit main track and picks the project-wide one |
| `2169-2171` | 2 | OBSOLETE | `record_track` | reads a row's Track cell, defaulting to main |
| `2173-2187` | 5 | TYPED | `evidence_for` | copies shape evidence and adds repository evidence |
| `2188-2207` | 20 | OBSOLETE | `evidence_for` | counts filled board columns and stage values in rendered rows |
| `2208-2246` | 18 | OBSOLETE | `evidence_for` | reads Due and By when note cells to score commitments |
| `2248-2271` | 20 | TYPED | `scan_work_modes` | runs the verdict per track and assembles the payload |
| `2274-2286` | 9 | cli-plumbing | `finding` | builds the finding record the report prints |
| `2287-2578` | 254 | TYPED | `derive_findings` | decides which findings fire from the typed payload |
| `2584-2601` | 6 | TYPED | `diagnose` | clears the cache, resolves the state root and walks the tree |
| `2602-2604` | 3 | OBSOLETE | `diagnose` | adoption test falls back to OKR.md and BOARD.md existence |
| `2605-2648` | 42 | TYPED | `diagnose` | matches Perry-owned globs then runs every scanner into the payload |
| `2651-2735` | 79 | cli-plumbing | `render_text` | formats the payload as the human-readable report |
| `2739-2757` | 16 | cli-plumbing | `SURFACE` | the declared flag and exit-code contract |
| `2760-2818` | 43 | cli-plumbing | `main` | parses argv, handles help and describe, prints the payload |

### `bin/perry-state` — 2,657 lines, 133 regions

```
    TYPED                           745
    TRANSPORT                         3
    AGENT                            75
    OBSOLETE                        167
    SUPPORT:cli-plumbing            371
    SUPPORT:imports                  22
    SUPPORT:docstring               551
    SUPPORT:comment                 509
    SUPPORT:blank                   213
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                         2,657   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `42-57` | 13 | imports | `module` | stdlib imports and the sys.path bootstrap |
| `58-71` | 9 | imports | `module` | viewer/parsers.py import guard, exit 2 |
| `72-82` | 9 | TYPED | `days_since` | ISO date out of a cell, minus today |
| `83-103` | 2 | OBSOLETE | `answered` | reads a BOARD.md UIQ Status cell -> parsers.py |
| `104-125` | 6 | OBSOLETE | `idle_days` | reads BOARD.md UIQ Asked and Idle cells |
| `126-138` | 8 | TYPED | `SETTING_FIELDS` | config.jsonl setting key to payload key map |
| `139-170` | 12 | TYPED | `stored_settings` | reads settings out of config.jsonl -> parsers.py |
| `171-198` | 8 | TYPED | `parse_config` | assembles settings from the config store |
| `199-209` | 8 | TYPED | `parse_config` | track register and the declared pack name list |
| `212-225` | 5 | TYPED | `load_packs` | pack manifest presence on the filesystem |
| `226-243` | 14 | OBSOLETE | `load_packs` | parses pack.md ## Glossary markdown table |
| `244-275` | 14 | TYPED | `stage_separators` | accepted stage separators from state-schema.json |
| `276-312` | 8 | TYPED | `split_stages` | splits a stored stages field on the declared separators |
| `313-336` | 5 | TYPED | `DEFAULT_TRACK` | the implicit main track record DESIGN-003 declares |
| `337-339` | 1 | TYPED | `_NO_DEFAULT` | schema no-default column cache |
| `340-356` | 8 | TYPED | `parse_wip` | parses the track record's per-stage WIP limits |
| `357-399` | 17 | TYPED | `wip_report` | counts live task records per stage against the limit |
| `400-404` | 3 | TYPED | `SLA_*` | the three not-runnable reasons the payload carries |
| `405-494` | 45 | TYPED | `sla_report` | today minus Arrived per task record against the SLA |
| `495-513` | 15 | cli-plumbing | `sla_note` | one sentence per not-runnable reason |
| `514-524` | 5 | TYPED | `parse_iso` | one ISO date, gated by lib.is_iso_date |
| `525-548` | 14 | TYPED | `default_stages_for` | a mode's default stages from state-schema.json |
| `549-568` | 13 | TYPED | `no_default_columns` | a mode's no-default columns from the schema |
| `569-595` | 8 | TYPED | `missing_defaults` | which no-default fields the track record left blank |
| `596-613` | 3 | TYPED | `blank_marker` | the project's blank-cell marker, from lib |
| `614-671` | 22 | TYPED | `track_from_record` | one kind:track config.jsonl record to a payload dict |
| `672-730` | 8 | TYPED | `TRACKS_STORE_*` | the tracks_source enum and the unusable set |
| `731-738` | 6 | cli-plumbing | `TRACKS_STORE_WHY` | what to tell a human per unusable source |
| `739-775` | 2 | TYPED | `_validated_config_records` | loads and validates config.jsonl -> parsers.py |
| `776-831` | 10 | TYPED | `stored_tracks` | selects kind:track records and orders them |
| `832-846` | 10 | OBSOLETE | `_RETIRED_TRACK_PREDICATES` | names and message for the deleted config.md readers |
| `847-892` | 21 | OBSOLETE | `tracks_the_*` | five tombstones of the .perry/config.md table readers |
| `893-917` | 5 | TYPED | `declared_tracks_detail` | tracks plus the source that produced them |
| `918-933` | 2 | TYPED | `declared_tracks` | the plain-list entry point over the store |
| `934-956` | 14 | TYPED | `raw_events` | json.loads loop over .perry/events.jsonl |
| `957-993` | 22 | TYPED | `read_event_log` | counts events.jsonl records by event and takes the last ts |
| `994-1048` | 8 | TYPED | `reconcile_drift` | guards on the event store being present |
| `1049-1068` | 19 | TYPED | `reconcile_drift` | json.loads loop over events.jsonl into per-id sequences |
| `1069-1093` | 3 | OBSOLETE | `reconcile_drift` | takes the row set from BOARD.md as authored -> parsers.py |
| `1094-1112` | 17 | OBSOLETE | `reconcile_drift` | compares the rendered rows against the event log |
| `1113-1179` | 27 | OBSOLETE | `cadence_report` | reads BOARD.md ## Cadence rows and cells -> parsers.py |
| `1180-1220` | 20 | TYPED | `verification_distribution` | V0-V6 rungs off done events and task records |
| `1221-1242` | 6 | TYPED | `hook_profile` | presence of .perry/hook.md and the empty result shape |
| `1243-1250` | 5 | AGENT | `hook_profile` | extracts high-stakes fragments from hook prose -> parsers.py |
| `1251-1263` | 8 | TYPED | `knowledge_stale_days` | the staleness threshold from state-schema.json |
| `1264-1269` | 4 | AGENT | `_card_field` | regexes a labelled field out of a knowledge card |
| `1270-1299` | 15 | TYPED | `subscribed_knowledge` | walks knowledge/<topic>/*.md, skipping archived cards |
| `1300-1321` | 22 | AGENT | `subscribed_knowledge` | reads Kind, Last verified and the H1 out of card prose |
| `1324-1338` | 3 | AGENT | `roles_profile` | reads .perry/roles/*.md role cards -> parsers.py |
| `1339-1365` | 4 | cli-plumbing | `roles_profile` | the roles payload contract and semantics keys |
| `1366-1400` | 17 | AGENT | `roles_profile` | publishes each card's prose fields and escalation lines |
| `1403-1408` | 4 | TYPED | `TIER1_CAPS` | the declared tier-1 line caps |
| `1409-1432` | 20 | TYPED | `tier1_caps` | counts lines of the tier-1 files on disk |
| `1433-1463` | 19 | TYPED | `resolve_kr` | exact id, name or registered alias against the linkage store |
| `1464-1473` | 7 | AGENT | `expired_sunsets` | judges a prose ADR sunset criterion by mining a date |
| `1474-1487` | 12 | cli-plumbing | `encode` | dataclass to JSON encoder |
| `1488-1501` | 4 | OBSOLETE | `encode_risk` | encodes a BOARD.md Top risks row and ages it |
| `1502-1540` | 11 | TYPED | `encode_linkage_objective` | linkage store KRs with derived current provenance |
| `1541-1544` | 2 | TYPED | `TERMINAL_STAGES` | terminal pipeline stages and the schema path |
| `1545-1556` | 7 | TYPED | `stale_run_days` | the stale-run threshold from state-schema.json |
| `1557-1565` | 6 | TYPED | `recovery_enums` | the pipeline enums from state-schema.json |
| `1566-1625` | 48 | TYPED | `inspect_dossier` | dossier frontmatter validated against schema enums |
| `1626-1643` | 16 | TYPED | `dossier_records` | globs .perry/adoption and .perry/diagnose dossiers |
| `1644-1650` | 5 | TYPED | `display_path` | a path relative to the project root |
| `1651-1693` | 39 | TYPED | `scan_recovery` | reads the transaction marker JSON and dossier errors |
| `1694-1742` | 29 | TYPED | `scan_interrupted` | non-terminal dossiers with their age against the limit |
| `1743-1763` | 18 | TYPED | `count_list_items` | counts frontmatter list entries in a dossier |
| `1764-1771` | 6 | TYPED | `count_status` | counts status: <value> lines in a dossier |
| `1772-1775` | 2 | TYPED | `build` | anchors .perry/ at the project root |
| `1776-1787` | 5 | TYPED | `build` | installed: BOARD/OKR on disk or the config store |
| `1788-1800` | 10 | cli-plumbing | `build` | the not-installed payload |
| `1802-1804` | 3 | TRANSPORT | `build` | obtains the whole-state snapshot object -> parsers.py |
| `1806-1810` | 5 | TYPED | `build` | counts task records by status enum |
| `1812-1813` | 2 | TYPED | `build` | the open-status set and every task record |
| `1819-1820` | 2 | TYPED | `build` | config read, then per-stage counts and WIP breaches |
| `1821-1826` | 1 | TYPED | `build` | queue SLA breaches over the same records |
| `1835-1836` | 2 | TYPED | `build` | tests the tracks_source against the unusable set |
| `1837-1843` | 7 | cli-plumbing | `build` | warns that the track register could not be read |
| `1846-1848` | 3 | TYPED | `build` | takes the linkage store and reports it unreadable |
| `1868-1881` | 12 | TYPED | `build` | linked / unlinked / declared_unlinked over the linkage store |
| `1891-1893` | 3 | TYPED | `build` | raw events, the log's presence, the task status index |
| `1898-1904` | 7 | TYPED | `build` | linkage store records into encoded objectives |
| `1905-1921` | 13 | TYPED | `build` | rolls KR current provenance up into counts |
| `1922-1927` | 6 | cli-plumbing | `build` | warns which KR current values went stale |
| `1938-1938` | 1 | OBSOLETE | `build` | filters the BOARD.md User Input Queue rows |
| `1940-1941` | 2 | OBSOLETE | `build` | oldest unanswered ask and the open BOARD.md risks |
| `1943-1943` | 1 | OBSOLETE | `build` | the BOARD.md cadence register |
| `1945-1946` | 2 | TYPED | `build` | locked design docs awaiting hand-off |
| `1948-1951` | 4 | TYPED | `build` | BOARD.md line count against the 200-line cap |
| `1953-1959` | 7 | TYPED | `build` | tier-1 line caps and the over-cap warnings |
| `1961-1963` | 3 | TYPED | `build` | phase/CURRENT pointing at a file that is not there |
| `1965-1972` | 3 | AGENT | `build` | hook, roles and the escalation union -> parsers.py |
| `1973-1996` | 9 | AGENT | `build` | warns on high-stakes bullets that arm nothing |
| `1997-2001` | 5 | cli-plumbing | `build` | warns that the safety scan is unarmed |
| `2003-2005` | 3 | AGENT | `build` | expired ADR sunset criteria, one warning each |
| `2007-2012` | 6 | TYPED | `build` | ARCHITECTURE.md status and review age -> parsers.py |
| `2014-2019` | 6 | cli-plumbing | `build` | payload head: schema, stamp, recovery, interrupted |
| `2020-2031` | 8 | cli-plumbing | `build` | project and roles blocks, assembled from above |
| `2032-2045` | 8 | OBSOLETE | `build` | intake counts off BOARD.md ## Intake, not intake.jsonl |
| `2046-2057` | 12 | OBSOLETE | `build` | OKR.md mission, version, titles, anti-goals, log |
| `2058-2074` | 7 | OBSOLETE | `build` | phase/NNN.md number, slug, status, started, day, focus |
| `2075-2083` | 9 | TYPED | `build` | phase KRs resolved from linkage.jsonl -> parsers.py |
| `2084-2086` | 3 | OBSOLETE | `build` | phase doc cost ceiling lines and scope triggers |
| `2087-2090` | 4 | OBSOLETE | `build` | BOARD.md line count, cap and Last updated header |
| `2091-2093` | 3 | TYPED | `build` | P0/P1/P2 totals and status counts from tasks.jsonl |
| `2094-2094` | 1 | OBSOLETE | `build` | the BOARD.md cadence row count |
| `2095-2096` | 2 | TYPED | `build` | blocked and open counts over task records |
| `2097-2099` | 3 | TYPED | `build` | verification distribution and the events.jsonl summary |
| `2100-2107` | 2 | OBSOLETE | `build` | drift against BOARD.md as authored |
| `2108-2109` | 2 | TYPED | `build` | every task record, encoded |
| `2110-2120` | 9 | TYPED | `build` | attribution counts over the linkage store |
| `2121-2134` | 8 | TYPED | `build` | the linkage block, all of it store records |
| `2135-2149` | 12 | OBSOLETE | `build` | user input queue off BOARD.md, not asks.jsonl |
| `2150-2150` | 1 | OBSOLETE | `build` | the cadence block |
| `2151-2184` | 9 | OBSOLETE | `build` | risks off BOARD.md ## Top risks, not risks.jsonl |
| `2185-2189` | 5 | TYPED | `build` | ADR count and the newest active decision |
| `2190-2191` | 2 | AGENT | `build` | the expired sunset list |
| `2192-2203` | 12 | TYPED | `build` | design doc totals, statuses and hand-off queue |
| `2204-2204` | 1 | TYPED | `build` | the ARCHITECTURE.md header record |
| `2205-2208` | 4 | TYPED | `build` | operations counts and the tier-1 caps |
| `2209-2217` | 9 | TYPED | `build` | journal, weekly, handoff and evidence file facts |
| `2218-2220` | 3 | cli-plumbing | `build` | warnings, and return the payload |
| `2221-2339` | 72 | cli-plumbing | `COMPACT` | the --compact projection spec, dotted paths only |
| `2340-2349` | 7 | cli-plumbing | `_at` | reads a dotted path out of the payload |
| `2350-2358` | 7 | cli-plumbing | `_put` | writes a dotted path into the narrow payload |
| `2359-2397` | 31 | cli-plumbing | `project_value` | the five projections --compact may apply |
| `2398-2411` | 5 | cli-plumbing | `project_compact` | walks COMPACT over the built payload |
| `2412-2536` | 99 | cli-plumbing | `dash` | renders the standup rows from the payload |
| `2537-2558` | 12 | TYPED | `resolve_root` | walks up for BOARD.md, OKR.md or the config store |
| `2559-2579` | 19 | cli-plumbing | `SURFACE` | the --help / --describe contract |
| `2580-2603` | 22 | cli-plumbing | `main` | flag parsing, help, describe, exit codes |
| `2604-2608` | 2 | TYPED | `main` | resolves the project root and the state root |
| `2609-2657` | 27 | cli-plumbing | `main` | root globals, build dispatch, JSON emission |

### `bin/lib/__init__.py` — 2,154 lines, 46 regions

```
    TYPED                           370
    TRANSPORT                        40
    AGENT                            61
    OBSOLETE                         37
    SUPPORT:cli-plumbing            197
    SUPPORT:imports                  26
    SUPPORT:docstring               763
    SUPPORT:comment                 487
    SUPPORT:blank                   173
    ------------------------------------
    TOTAL                         2,154   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `30-50` | 16 | imports | `module` | stdlib imports |
| `51-58` | 3 | TYPED | `module` | install paths from __file__ and $PERRY_HOME |
| `59-122` | 26 | TRANSPORT | `stage/write_atomic` | stages and publishes a whole file body, uninspected |
| `123-135` | 7 | TYPED | `sync_directory` | fsyncs a directory by fd |
| `136-223` | 23 | TYPED | `project_lock` | flock keyed by a hash of the resolved state root |
| `224-230` | 1 | TYPED | `ISO_DATE_RE` | the anchored ISO date shape |
| `231-258` | 12 | OBSOLETE | `blank_marker` | hands back the marker a blank cell is rendered with |
| `259-268` | 4 | OBSOLETE | `normalize_typed_cell/_blank_key` | strips markdown cell decoration before a typed read |
| `269-294` | 16 | OBSOLETE | `is_blank_cell` | matches a cell against the declared blank spellings |
| `295-322` | 8 | TYPED | `is_sla_token/parse_sla` | reads a bounded <n><unit> SLA token |
| `323-350` | 10 | TYPED | `sla_deadline` | calendar arithmetic from arrived plus an SLA |
| `351-374` | 9 | TYPED | `is_iso_date` | shape and real-calendar check of one date value |
| `375-418` | 28 | TYPED | `classify_due` | one Due value to a bounded classification enum |
| `419-440` | 4 | TYPED | `load_schema` | reads schema/state-schema.json or raises the refusal |
| `441-462` | 10 | imports | `_parsers` | deferred viewer/ import with the sys.path bootstrap |
| `463-492` | 5 | cli-plumbing | `empty_root_error` | the refusal text an empty --root value earns |
| `493-530` | 15 | TYPED | `resolve_project_root` | flag, then env, then the walk up from cwd |
| `531-586` | 2 | cli-plumbing | `root_flag` | shell-quoted --root appended to a printed command |
| `587-644` | 20 | cli-plumbing | `COMMON_FLAGS/surface_flags` | the declared flag tables and their lookups |
| `645-678` | 26 | cli-plumbing | `check_surface` | internal consistency of one tool's declaration |
| `679-767` | 61 | cli-plumbing | `parse_surface` | reads argv against the declaration before dispatch |
| `768-798` | 23 | cli-plumbing | `describe_surface` | the --describe JSON dump of the declaration |
| `799-851` | 35 | cli-plumbing | `usage_lines` | generates the --help usage block |
| `852-869` | 5 | TYPED | `exists_or_unreadable` | path existence, or None when it cannot be searched |
| `870-915` | 25 | cli-plumbing | `scan_argv` | splits argv into positionals, flags and one error |
| `916-967` | 2 | TYPED | `resolve_state_root` | re-export of the one state-root path resolver |
| `968-1023` | 5 | TYPED | `TASK_STATUSES/_is_state_move` | the status enum and the event whose `to` is one |
| `1024-1044` | 4 | TYPED | `event_stamp/register_stamp` | the two clocks Perry stamps |
| `1045-1104` | 21 | TYPED | `ts_moment/ts_key` | any Perry timestamp to one UTC moment and key |
| `1105-1122` | 5 | OBSOLETE | `task_status_index` | reads status off board.all_tasks, the projection |
| `1123-1139` | 4 | TYPED | `task_status_index` | overrides from tasks.jsonl, the canonical side |
| `1140-1226` | 9 | TYPED | `COMPUTED_KR_METRICS/_corroborates` | the metric table and the store-vs-event agreement test |
| `1227-1277` | 10 | TYPED | `measured_percent` | an integer ratio to a one-decimal published percent |
| `1278-1506` | 73 | TYPED | `same_action_linkage` | counts linkage.jsonl edges against add events |
| `1507-1520` | 5 | TYPED | `computed_kr_current` | dispatches a KR id to the function that measures it |
| `1521-1723` | 100 | TYPED | `kr_progress_provenance` | provenance, staleness and tally from store and log |
| `1724-1794` | 10 | TYPED | `resolve_startability` | sets startable from the status enum and the edges |
| `1795-1842` | 11 | TYPED | `id_family/perry_named_artifact` | the id family a filename declares, by id format |
| `1843-1875` | 14 | TRANSPORT | `walk_md` | locates every markdown body belonging to the project |
| `1876-1936` | 31 | AGENT | `blank_code_spans` | decides which text in prose is quoted material |
| `1937-1983` | 3 | TYPED | `declared_id_families` | id families off filenames, no document read |
| `1984-2013` | 3 | AGENT | `the summary constants` | threshold and folds for judging a human summary |
| `2014-2030` | 4 | AGENT | `summary_tokens` | counts tokens of free text across writing systems |
| `2031-2055` | 2 | AGENT | `summary_fold` | folds a title and a summary so prose can be compared |
| `2056-2061` | 4 | AGENT | `SUMMARY_RULES_REMOVED` | the prose rules summary_shape stopped judging |
| `2062-2154` | 17 | AGENT | `summary_shape` | judges whether a human summary restates its title |

### `bin/perry-tasks` — 1,928 lines, 85 regions

```
    TYPED                           318
    OBSOLETE                        585
    SUPPORT:cli-plumbing            228
    SUPPORT:imports                  45
    SUPPORT:docstring               337
    SUPPORT:comment                 259
    SUPPORT:blank                   155
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                         1,928   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `20-38` | 14 | imports | `module` | stdlib, the viewer path bootstrap, perry_store |
| `39-41` | 1 | TYPED | `module` | STORED - the stored field order |
| `42-45` | 2 | cli-plumbing | `Refused` | the refusal exception |
| `46-69` | 10 | OBSOLETE | `build` | records DERIVED from BOARD.md by perry-task |
| `70-102` | 15 | imports | `_task_module` | SourceFileLoader import of bin/perry-task |
| `103-108` | 4 | OBSOLETE | `module` | cell_text/describe_cell/render_line re-exported |
| `109-115` | 4 | OBSOLETE | `plan` | which records the projection owes a line |
| `116-127` | 4 | OBSOLETE | `render` | the store rendered into BOARD.md text |
| `128-137` | 6 | TYPED | `STRANDED_KEYS/stranded_records` | the stranded ids a report names |
| `138-161` | 6 | OBSOLETE | `stranded_after_render` | re-plan against the rendered text |
| `162-219` | 40 | OBSOLETE | `write_board_or_refuse` | refuse, then rewrite BOARD.md |
| `220-257` | 24 | TYPED | `write_store_or_say_what_would_land` | the jsonl store written atomically |
| `258-272` | 6 | TYPED | `load_store` | tasks.jsonl -> records |
| `273-300` | 28 | TYPED | `cmd_render` | the store loaded and validated |
| `301-336` | 21 | OBSOLETE | `cmd_render` | render, write, and the byte compare with BOARD.md |
| `337-345` | 3 | OBSOLETE | `risk_board` | BOARD.md opened as a Board |
| `346-388` | 24 | OBSOLETE | `refuse_duplicate_ids` | one id on two rendered rows, by line |
| `389-416` | 6 | TYPED | `load_risk_store` | risks.jsonl -> records |
| `417-430` | 12 | cli-plumbing | `module` | RISK_STORE_UNDECLARED refusal copy |
| `431-446` | 7 | TYPED | `risk_store_is_declared` | the schema's claims list |
| `447-463` | 4 | OBSOLETE | `cmd_risks_render` | the board this section renders into |
| `464-483` | 10 | TYPED | `cmd_risks_render` | the risks store loaded |
| `484-535` | 45 | OBSOLETE | `cmd_risks_render` | derive, render and byte-compare the section |
| `536-581` | 18 | TYPED | `_would_discard` | two typed record sets compared field by field |
| `582-606` | 23 | cli-plumbing | `module` | RISK_SECTION_UNIMPORTABLE refusal copy |
| `607-665` | 2 | OBSOLETE | `cmd_risks_write` | the section-to-store import |
| `666-681` | 13 | TYPED | `cmd_risks_write` | the store path and the two write gates |
| `682-690` | 8 | OBSOLETE | `cmd_risks_write` | the rendered section's shape |
| `691-719` | 15 | TYPED | `cmd_risks_write` | the store on disk, loaded and validated |
| `720-730` | 6 | OBSOLETE | `cmd_risks_write` | duplicate rendered ids, then the derivation |
| `731-756` | 25 | OBSOLETE | `cmd_risks_write` | the byte round-trip gate on the section |
| `757-764` | 7 | TYPED | `cmd_risks_write` | the derived records validated |
| `765-776` | 9 | TYPED | `cmd_risks_write` | what the import would discard |
| `777-788` | 2 | TYPED | `cmd_risks_write` | the store written |
| `789-794` | 3 | OBSOLETE | `intake_board` | BOARD.md opened as a Board |
| `795-808` | 6 | TYPED | `load_intake_store` | intake.jsonl -> records |
| `809-822` | 12 | cli-plumbing | `module` | INTAKE_STORE_UNDECLARED refusal copy |
| `823-837` | 7 | TYPED | `intake_store_is_declared` | the schema's claims list |
| `838-849` | 4 | OBSOLETE | `cmd_intake_render` | the board this section renders into |
| `850-859` | 10 | TYPED | `cmd_intake_render` | the intake store loaded |
| `860-906` | 45 | OBSOLETE | `cmd_intake_render` | derive, render and byte-compare the section |
| `907-939` | 19 | TYPED | `_would_discard_intake` | two typed record sets compared |
| `940-959` | 18 | cli-plumbing | `module` | INTAKE_SECTION_UNIMPORTABLE refusal copy |
| `960-1004` | 2 | OBSOLETE | `cmd_intake_write` | the section-to-store import |
| `1005-1020` | 13 | TYPED | `cmd_intake_write` | the store path and the two write gates |
| `1021-1028` | 7 | OBSOLETE | `cmd_intake_write` | the rendered section's shape |
| `1029-1044` | 15 | TYPED | `cmd_intake_write` | the store on disk, loaded and validated |
| `1045-1047` | 1 | OBSOLETE | `cmd_intake_write` | records derived from the section |
| `1048-1074` | 26 | OBSOLETE | `cmd_intake_write` | the byte round-trip gate on the section |
| `1075-1088` | 7 | TYPED | `cmd_intake_write` | the derived records validated |
| `1089-1110` | 21 | OBSOLETE | `cmd_intake_write` | rendered rows counted against the header |
| `1111-1120` | 9 | TYPED | `cmd_intake_write` | what the import would discard |
| `1121-1134` | 2 | TYPED | `cmd_intake_write` | the store written |
| `1135-1140` | 3 | OBSOLETE | `ask_board` | BOARD.md opened as a Board |
| `1141-1154` | 6 | TYPED | `load_ask_store` | asks.jsonl -> records |
| `1155-1168` | 12 | cli-plumbing | `module` | ASK_STORE_UNDECLARED refusal copy |
| `1169-1183` | 7 | TYPED | `ask_store_is_declared` | the schema's claims list |
| `1184-1194` | 4 | OBSOLETE | `cmd_ask_render` | the board this section renders into |
| `1195-1204` | 10 | TYPED | `cmd_ask_render` | the ask store loaded |
| `1205-1258` | 45 | OBSOLETE | `cmd_ask_render` | derive, render and byte-compare the section |
| `1259-1279` | 19 | cli-plumbing | `module` | ASK_SECTION_UNIMPORTABLE refusal copy |
| `1280-1319` | 2 | OBSOLETE | `cmd_asks_write` | the section-to-store import |
| `1320-1335` | 13 | TYPED | `cmd_asks_write` | the store path and the two write gates |
| `1336-1343` | 7 | OBSOLETE | `cmd_asks_write` | the rendered section's shape |
| `1344-1364` | 15 | TYPED | `cmd_asks_write` | the store on disk, loaded and validated |
| `1365-1374` | 7 | OBSOLETE | `cmd_asks_write` | duplicate rendered ids, then the derivation |
| `1375-1404` | 29 | OBSOLETE | `cmd_asks_write` | the byte round-trip gate on the section |
| `1405-1412` | 7 | TYPED | `cmd_asks_write` | the derived records validated |
| `1413-1422` | 9 | TYPED | `cmd_asks_write` | what the import would discard |
| `1423-1451` | 2 | TYPED | `cmd_asks_write` | the store written |
| `1452-1485` | 16 | imports | `_sibling_module` | SourceFileLoader import of bin/perry-lint |
| `1486-1514` | 9 | TYPED | `registers` | the declared jsonl registers, from the schema |
| `1515-1599` | 83 | cli-plumbing | `module` | the SURFACE declaration |
| `1600-1642` | 21 | cli-plumbing | `main` | argv, --help and --describe |
| `1643-1664` | 19 | cli-plumbing | `main` | the register listing and root resolution |
| `1665-1674` | 5 | cli-plumbing | `main` | the project root, or the empty-root error |
| `1675-1697` | 11 | OBSOLETE | `main` | render --write, under the project lock |
| `1698-1715` | 15 | OBSOLETE | `main` | risks-render, risks-build, risks-write |
| `1716-1735` | 17 | OBSOLETE | `main` | intake-render, intake-build, intake-write |
| `1736-1759` | 17 | OBSOLETE | `main` | ask-render, ask-build, asks-write |
| `1760-1765` | 3 | OBSOLETE | `main` | render |
| `1766-1773` | 7 | OBSOLETE | `main` | build - records derived from the board |
| `1774-1877` | 56 | OBSOLETE | `main` | write --from-board, the board-to-store import |
| `1878-1926` | 47 | OBSOLETE | `main` | diff - the store against the board it renders |
| `1927-1928` | 2 | cli-plumbing | `module` | __main__ guard |

### `bin/perry_md_store.py` — 1,675 lines, 43 regions

```
    TYPED                           352
    OBSOLETE                        419
    SUPPORT:cli-plumbing             93
    SUPPORT:imports                  25
    SUPPORT:docstring               335
    SUPPORT:comment                 297
    SUPPORT:blank                   154
    ------------------------------------
    TOTAL                         1,675   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `68-85` | 15 | imports | `module` | stdlib, the viewer bootstrap, lib and perry_store |
| `86-88` | 1 | OBSOLETE | `module` | markdown_tables re-exported |
| `89-95` | 1 | cli-plumbing | `Refused` | the refusal exception |
| `96-105` | 6 | TYPED | `schema` | the schema, loaded once |
| `106-151` | 16 | OBSOLETE | `spellings/field_map/column_field` | declared spellings of a rendered column header |
| `152-174` | 12 | OBSOLETE | `table_columns` | the columns the schema declares for a table |
| `175-197` | 11 | OBSOLETE | `module` | the KR, Commitment and Version column maps |
| `198-234` | 12 | TYPED | `store_record_fields` | the declared field list of a stored record |
| `235-299` | 24 | TYPED | `STORED/_assert_every_declared_column_is_stored` | the stored field order, asserted against the schema |
| `300-341` | 16 | TYPED | `record_key` | the identity of a stored record |
| `342-362` | 10 | TYPED | `record` | one typed record, fields in stored order |
| `363-384` | 7 | TYPED | `_objectives_in_store_order` | objectives by their stored order |
| `385-558` | 90 | TYPED | `mint_objective_ids` | objective ids minted into the store |
| `559-605` | 39 | TYPED | `validate_records` | type and uniqueness over the stored records |
| `606-626` | 7 | TYPED | `store_text/load_store` | the jsonl store, read and serialised |
| `627-646` | 3 | OBSOLETE | `stored_value` | a rendered blank marker normalised away |
| `647-673` | 24 | OBSOLETE | `_table_sites` | one rendered row -> one site, by column key |
| `674-691` | 12 | OBSOLETE | `_heading_context` | the h2/h3 a line sits under |
| `692-705` | 2 | OBSOLETE | `heading_pattern` | a heading matcher in any declared spelling |
| `706-786` | 34 | OBSOLETE | `okr_heading/objective_title/table_under` | locate a section and the table under it |
| `787-891` | 68 | OBSOLETE | `scan_okr` | every KR, Commitment, Objective and Version row |
| `892-912` | 2 | OBSOLETE | `setting_key` | a rendered setting label folded to a key |
| `913-951` | 15 | OBSOLETE | `Doc/OKR/DOCS` | which file projects which store |
| `952-968` | 10 | OBSOLETE | `derive` | records DERIVED from the document |
| `969-1060` | 66 | OBSOLETE | `plan` | which lines and cells the store can fill |
| `1061-1071` | 4 | OBSOLETE | `render` | the store rendered back into OKR.md |
| `1072-1114` | 4 | OBSOLETE | `every_line_and_cell_came_from_the_store` | did the renderer fall back to copying |
| `1115-1132` | 8 | TYPED | `touches` | does this key prefix name that field |
| `1133-1167` | 16 | TYPED | `would_discard` | two typed record sets compared field by field |
| `1168-1196` | 22 | cli-plumbing | `module` | USAGE and the command list |
| `1197-1205` | 7 | OBSOLETE | `_first_difference` | the first differing rendered line |
| `1206-1262` | 44 | cli-plumbing | `surface` | the SURFACE declaration |
| `1263-1301` | 26 | cli-plumbing | `main` | argv, --help and --describe |
| `1302-1310` | 4 | TYPED | `main` | the roots and the two paths |
| `1311-1328` | 7 | OBSOLETE | `main` | render --write, under the project lock |
| `1329-1353` | 16 | OBSOLETE | `main` | build - records derived from the document |
| `1354-1363` | 9 | TYPED | `main` | the store on disk, or the refusal |
| `1364-1419` | 45 | TYPED | `main` | migrate-ids - ids minted into the store |
| `1420-1576` | 96 | OBSOLETE | `main` | render and diff - the byte compare with OKR.md |
| `1577-1585` | 9 | OBSOLETE | `main` | write --from-file - the document-to-store import |
| `1586-1624` | 33 | TYPED | `main` | the store loaded, validated, and what would be lost |
| `1625-1665` | 26 | TYPED | `main` | the derived records validated and written |
| `1666-1675` | 10 | imports | `module` | __all__ |

### `bin/perry_store.py` — 1,667 lines, 47 regions

```
    TYPED                           224
    OBSOLETE                        570
    SUPPORT:imports                  26
    SUPPORT:docstring               431
    SUPPORT:comment                 297
    SUPPORT:blank                   119
    ------------------------------------
    TOTAL                         1,667   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `31-65` | 9 | imports | `module` | stdlib, the viewer sys.path bootstrap, tables imports |
| `66-74` | 4 | TYPED | `STORED` | the twenty-one stored fields in key order |
| `75-82` | 7 | OBSOLETE | `FIELD_BY_COLUMN` | board column spelling to the field it renders from |
| `83-88` | 1 | TYPED | `TERMINAL_STATUSES` | the closed half of the status enum |
| `89-144` | 34 | OBSOLETE | `markdown_tables` | finds every markdown table block, its header and rows |
| `145-163` | 10 | TYPED | `record` | one task dict to one record in STORED key order |
| `164-188` | 15 | OBSOLETE | `board_order` | row position read off the board's rendered tables |
| `189-204` | 10 | TYPED | `store_path/store_text/load_store` | the tasks.jsonl path, its bytes, and the record read |
| `205-270` | 49 | TYPED | `validate_records` | typechecks each JSONL record against STORED |
| `271-296` | 6 | OBSOLETE | `cell_text` | renders one stored field as an escaped table cell |
| `297-383` | 26 | OBSOLETE | `describe_cell` | decides how one raw cell rebuilds from a stored value |
| `384-407` | 13 | OBSOLETE | `render_line` | joins cell descriptors back into a markdown row |
| `408-443` | 22 | OBSOLETE | `row_descriptor` | one table row line to a cell-by-cell descriptor |
| `444-477` | 20 | OBSOLETE | `slot_descriptor` | one bullet line to named slots and literal spans |
| `478-491` | 5 | OBSOLETE | `render_lines` | puts the claimed lines back into the document text |
| `492-619` | 79 | OBSOLETE | `plan` | splits BOARD.md into store-filled and layout lines |
| `620-658` | 3 | OBSOLETE | `render` | renders the text of BOARD.md from the task store |
| `659-662` | 1 | TYPED | `RISK_STORED` | the risk record's six fields |
| `663-670` | 3 | OBSOLETE | `RISK_FIELD_BY_COLUMN/RISK_SECTION` | register column spellings and its markdown heading |
| `671-674` | 2 | TYPED | `risk_store_path` | the risks.jsonl path |
| `675-711` | 13 | OBSOLETE | `risk_section_shape/risk_table` | locates the heading and the table that is the register |
| `712-747` | 15 | OBSOLETE | `risk_record` | a register row to a record, cleared off Status prose |
| `748-811` | 17 | OBSOLETE | `duplicate_row_ids` | repeated ids among the rendered table's rows |
| `812-848` | 15 | TYPED | `duplicate_record_ids` | repeated ids among the store's records |
| `849-890` | 18 | OBSOLETE | `risk_records` | derives the risks store from the section as written |
| `891-940` | 41 | TYPED | `validate_risk_records` | typechecks each risks.jsonl record |
| `941-1026` | 56 | OBSOLETE | `risk_plan` | splits the risks section into filled and layout lines |
| `1027-1071` | 3 | OBSOLETE | `risk_render` | renders the risks section text from the store |
| `1072-1077` | 1 | TYPED | `INTAKE_STORED` | the intake record's fields, keyed on order |
| `1078-1085` | 3 | OBSOLETE | `INTAKE_FIELD_BY_COLUMN/INTAKE_SECTION` | intake column spellings and its markdown heading |
| `1086-1089` | 2 | TYPED | `intake_store_path` | the intake.jsonl path |
| `1090-1121` | 13 | OBSOLETE | `intake_section_shape/intake_table` | locates the heading and the intake register table |
| `1122-1153` | 15 | OBSOLETE | `intake_record` | a row to a record, discharged off the Outcome prose |
| `1154-1176` | 11 | OBSOLETE | `intake_records` | derives the intake store from the rows as written |
| `1177-1227` | 41 | TYPED | `validate_intake_records` | typechecks each intake.jsonl record |
| `1228-1307` | 58 | OBSOLETE | `intake_plan` | splits the intake section, joined by row position |
| `1308-1395` | 3 | OBSOLETE | `intake_render` | renders the intake section text from the store |
| `1396-1402` | 1 | TYPED | `ASK_STORED` | the ask record's seven fields |
| `1403-1411` | 4 | OBSOLETE | `ASK_FIELD_BY_COLUMN/ASK_SECTION` | ask column spellings and its markdown heading |
| `1412-1415` | 2 | TYPED | `ask_store_path` | the asks.jsonl path |
| `1416-1446` | 13 | OBSOLETE | `ask_section_shape/ask_table` | locates the heading and the ask register table |
| `1447-1483` | 18 | OBSOLETE | `ask_record` | a row to a record, answered off the Status prose |
| `1484-1519` | 18 | OBSOLETE | `ask_records` | derives the ask store from the rows as written |
| `1520-1573` | 44 | TYPED | `validate_ask_records` | typechecks each asks.jsonl record |
| `1574-1642` | 56 | OBSOLETE | `ask_plan` | splits the User Input Queue into filled and layout |
| `1643-1648` | 3 | OBSOLETE | `ask_render` | renders the ask section text from the store |
| `1649-1667` | 17 | imports | `__all__` | the module export table |

### `bin/perry-explain` — 920 lines, 43 regions

```
    TYPED                           182
    TRANSPORT                        29
    AGENT                            17
    OBSOLETE                         90
    SUPPORT:cli-plumbing            145
    SUPPORT:imports                  16
    SUPPORT:docstring               197
    SUPPORT:comment                 168
    SUPPORT:blank                    75
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                           920   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `34-63` | 16 | imports | `module` | stdlib imports, PERRY_HOME bootstrap, lib re-exports |
| `65-105` | 12 | TYPED | `module` | the id grammar, the refused legacy form, the not-an-id filters |
| `106-145` | 19 | TYPED | `is_real_id/is_illustrative` | filters id-shaped non-ids and paths whose job is to explain |
| `146-171` | 14 | TYPED | `find_ids` | collects complete ids from a text by the id grammar |
| `172-190` | 11 | OBSOLETE | `module` | table-row, heading, yaml and title-column matchers over the render |
| `191-255` | 8 | OBSOLETE | `strip_md/heading_subject` | strips md decoration and finds the id a heading opens with |
| `256-321` | 7 | AGENT | `heading_title` | lifts the human name out of a heading sentence |
| `322-345` | 10 | TYPED | `harvest` | the entry record factory and the default body reader |
| `346-353` | 7 | TRANSPORT | `harvest` | walks every markdown file and reads each body whole |
| `354-355` | 2 | TYPED | `harvest` | relative path and the illustrative-path test |
| `356-363` | 6 | TYPED | `harvest` | an id-named file defines that id, at line 1 |
| `364-373` | 7 | AGENT | `harvest` | takes the id's human name from the document's first heading |
| `374-381` | 3 | OBSOLETE | `harvest` | table-header, yaml-pending and proposal-section scan state |
| `382-418` | 7 | OBSOLETE | `harvest` | toggles fenced-code state over the render |
| `419-419` | 1 | TYPED | `harvest` | collects the id tokens this line mentions |
| `420-470` | 35 | OBSOLETE | `harvest` | reads the table row: id cell, title column, status column |
| `471-485` | 8 | OBSOLETE | `harvest` | locates the heading and the id it opens with |
| `486-490` | 3 | AGENT | `harvest` | takes the heading sentence as that id's title |
| `491-506` | 14 | OBSOLETE | `harvest` | reads the `- id:` / `title:` yaml frontmatter pair |
| `507-517` | 9 | TYPED | `harvest` | records each id's mention locations and tracking-doc flag |
| `518-568` | 29 | TYPED | `harvest_linkage_store` | reads kr records out of linkage.jsonl |
| `569-593` | 20 | cli-plumbing | `label/render_one` | renders one entry for the terminal |
| `594-605` | 5 | TYPED | `typed_task_lookup` | gates on TASK id format and locates the Task store |
| `606-609` | 4 | OBSOLETE | `typed_task_lookup` | probes BOARD.md, OKR.md and phase/ for the adoption fact |
| `610-640` | 29 | TYPED | `typed_task_lookup` | loads and validates the typed Task record |
| `641-677` | 30 | cli-plumbing | `render_typed_task_result` | prints the typed Task result or the not-found refusal |
| `678-719` | 17 | TYPED | `rung_entry` | resolves a verification rung out of the schema |
| `720-751` | 21 | TRANSPORT | `glossary_entry` | locates a term's section in the glossary and hands on its body |
| `752-793` | 28 | cli-plumbing | `main` | argv parsing, --root validation, --help |
| `794-801` | 8 | TYPED | `main` | refuses a non-directory root, then the Task store fast path |
| `802-818` | 6 | TYPED | `main` | defers and memoizes the corpus scan |
| `819-833` | 13 | cli-plumbing | `main` | prints the whole glossary for --all |
| `834-838` | 5 | TYPED | `main` | computes the referenced-but-never-defined set |
| `839-852` | 12 | cli-plumbing | `main` | prints the dangling report and the no-argument help |
| `853-853` | 1 | TYPED | `main` | looks the token up as a verification rung |
| `854-864` | 10 | cli-plumbing | `main` | prints the rung |
| `865-865` | 1 | TRANSPORT | `main` | looks the token up as a glossary term |
| `866-879` | 11 | cli-plumbing | `main` | prints the glossary term |
| `880-889` | 2 | TYPED | `main` | pays for the corpus scan and tests the legacy KR id form |
| `890-899` | 10 | cli-plumbing | `main` | prints the refusal for the old phase-KR form |
| `900-906` | 6 | TYPED | `main` | lists the phase-KR ids the old form could have meant |
| `907-907` | 1 | TYPED | `main` | resolves the id in the harvested entry map |
| `908-920` | 11 | cli-plumbing | `main` | prints the not-found hint, the entry, and the exit code |

### `bin/perry-churn` — 745 lines, 24 regions

```
    TYPED                           228
    SUPPORT:cli-plumbing            241
    SUPPORT:imports                   8
    SUPPORT:docstring               170
    SUPPORT:comment                  20
    SUPPORT:blank                    77
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                           745   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `95-103` | 8 | imports | `module` | stdlib imports |
| `104-135` | 9 | TYPED | `module` | the four buckets, their labels, the test-directory set, numstat seps |
| `136-140` | 3 | cli-plumbing | `die` | error message and exit code |
| `141-247` | 102 | cli-plumbing | `parse_args` | argv parsing, flag validation and --help |
| `248-252` | 2 | TYPED | `window_start` | first day of a --days N window, today counted |
| `253-269` | 12 | TYPED | `git_out/git_toplevel` | runs git and finds the repository top level |
| `270-304` | 11 | TYPED | `resolve_state_root` | resolves the state root through lib, or says it guessed |
| `305-358` | 34 | TYPED | `detect_perry/resolve_split` | finds .perry/ and the evidence path prefix under the git top level |
| `359-386` | 26 | TYPED | `git_log` | builds and runs the git log --numstat command |
| `387-404` | 12 | TYPED | `resolved_path` | takes the destination path out of a numstat rename |
| `405-456` | 38 | TYPED | `is_doc/is_evidence/is_test` | classifies a path by extension, glob, prefix and test-name rules |
| `457-473` | 7 | TYPED | `classify` | picks one bucket for a path |
| `474-492` | 15 | TYPED | `bucket_key/new_bucket` | day/week/month key by date arithmetic, and the empty bucket |
| `493-521` | 27 | TYPED | `collect` | sums added, deleted and files per bucket from numstat |
| `522-553` | 20 | TYPED | `fill_window/totals/rows` | fills the calendar window and totals the buckets |
| `554-573` | 8 | TYPED | `shown_kinds/cell/net` | the column fold and the per-column sums |
| `574-577` | 2 | cli-plumbing | `fmt_pm` | formats +added -deleted |
| `578-634` | 49 | cli-plumbing | `print_table` | lays out and prints the table and its footers |
| `635-661` | 18 | cli-plumbing | `provenance` | prints which split ran and why |
| `662-689` | 22 | cli-plumbing | `csv_fields/print_csv/shaped` | csv columns and rows |
| `690-720` | 29 | cli-plumbing | `print_json` | serialises the run parameters and the buckets |
| `721-722` | 2 | cli-plumbing | `main` | parses argv |
| `723-729` | 7 | TYPED | `main` | refuses outside a git repository, then collects the buckets |
| `730-745` | 14 | cli-plumbing | `main` | output-format dispatch and exit codes |

### `bin/perry-knowledge` — 688 lines, 35 regions

```
    TYPED                           196
    TRANSPORT                        27
    AGENT                            15
    OBSOLETE                         49
    SUPPORT:cli-plumbing             88
    SUPPORT:imports                  29
    SUPPORT:docstring               141
    SUPPORT:comment                  63
    SUPPORT:blank                    79
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                           688   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `71-91` | 16 | imports | `module` | stdlib imports and the PERRY_HOME path bootstrap |
| `92-121` | 4 | cli-plumbing | `module` | the refusal type and the propose/list contract version strings |
| `122-132` | 2 | TYPED | `module` | the verification rungs too weak to propose a card from |
| `133-159` | 13 | imports | `lint` | loads bin/perry-lint as a module with its schema glossary |
| `160-186` | 15 | TYPED | `load_schema/card_spec/card_kinds/required_fields` | reads the card shape, kinds and header fields from the schema |
| `187-207` | 15 | TYPED | `read_cards` | walks knowledge/*.md and reads the schema Kind discriminator |
| `208-209` | 2 | AGENT | `read_cards` | splits the H1 at a prose dash to decide where the claim starts |
| `210-213` | 4 | TYPED | `read_cards` | turns the ISO Last verified into an age in days |
| `214-226` | 13 | TRANSPORT | `read_cards` | assembles the record from the card's header cells, verbatim |
| `227-234` | 3 | TYPED | `declared_roles` | lists the role cards in .perry/roles by stem |
| `235-250` | 6 | AGENT | `source_cites` | token-matches two free-text Source citations for sameness |
| `251-258` | 4 | TYPED | `slugify` | normalises a name into a safe path segment |
| `259-272` | 6 | TRANSPORT | `render_card` | renders the card body in the template's shape |
| `273-313` | 22 | OBSOLETE | `render_cards_section` | renders the ## Cards by topic index rows |
| `314-350` | 19 | OBSOLETE | `patch_index` | locates and replaces the index section and its Last updated line |
| `351-371` | 3 | TYPED | `write_atomic/project_lock` | atomic write and the one project lock |
| `372-386` | 6 | TYPED | `cmd_propose` | reads the declared roles and the call-time date |
| `387-389` | 3 | TYPED | `cmd_propose` | derives the owner when exactly one role is declared |
| `390-406` | 13 | TYPED | `cmd_propose` | composes the propose contract payload and its prefill |
| `407-423` | 17 | TYPED | `cmd_propose` | declines on no source, an unresolvable source, or a weak rung |
| `424-430` | 7 | AGENT | `cmd_propose` | asks whether an existing card already cites this source |
| `431-436` | 4 | cli-plumbing | `cmd_propose` | the ready answer and its instruction to the caller |
| `437-515` | 71 | TYPED | `cmd_promote` | refusals: kind enum, claim, source resolves, tripwire, owner, slug |
| `516-522` | 7 | TRANSPORT | `cmd_promote` | reads --body-file whole and uninterpreted |
| `523-532` | 9 | TYPED | `cmd_promote` | fills the schema-declared header fields, refusing if one is missing |
| `533-533` | 1 | TRANSPORT | `cmd_promote` | renders the card body |
| `534-543` | 8 | TYPED | `cmd_promote` | the written-record payload and the dry-run exit |
| `544-545` | 2 | TYPED | `cmd_promote` | takes the project lock and writes the card atomically |
| `546-553` | 8 | OBSOLETE | `cmd_promote` | rebuilds and rewrites the rendered INDEX.md cards section |
| `554-573` | 13 | TYPED | `cmd_list` | reads the cards and publishes the list contract with its counts |
| `574-580` | 3 | cli-plumbing | `module` | subcommand dispatch table and the args holder |
| `581-640` | 40 | cli-plumbing | `parse` | argv parsing, valueless-flag and unknown-flag refusals |
| `641-646` | 6 | cli-plumbing | `main` | subcommand dispatch |
| `647-654` | 8 | TYPED | `main` | loads the schema and resolves the project and state roots |
| `655-688` | 31 | cli-plumbing | `main` | refusal printing, terminal rendering and exit codes |

### `bin/perry-decide` — 620 lines, 22 regions

```
    TYPED                           166
    TRANSPORT                        13
    SUPPORT:cli-plumbing             85
    SUPPORT:imports                  14
    SUPPORT:docstring               126
    SUPPORT:comment                 155
    SUPPORT:blank                    60
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                           620   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `67-85` | 14 | imports | `module` | stdlib imports and the PERRY_HOME path bootstrap |
| `86-125` | 3 | cli-plumbing | `module` | the refusal type and the list contract version strings |
| `126-168` | 2 | TYPED | `module` | the ADR id grammar and the status a new ADR is born with |
| `169-224` | 15 | TYPED | `load_schema/statuses` | reads decision_status out of the schema enum, cached |
| `225-230` | 1 | TYPED | `read_adrs` | binds the shared ADR frontmatter reader in viewer/parsers |
| `231-268` | 3 | TYPED | `mint_id` | next ADR number from the ADR files, never reusing a live one |
| `269-284` | 3 | TYPED | `write_atomic/project_lock` | atomic write and the one project lock |
| `285-302` | 10 | TYPED | `cmd_bootstrap` | creates decisions/, refusing to repeat a one-time step |
| `303-307` | 3 | TYPED | `slugify` | normalises the title into a filename segment |
| `308-375` | 40 | TYPED | `cmd_new` | refusals, mints the id, checks the supersedes target exists |
| `376-388` | 13 | TRANSPORT | `cmd_new` | composes the ADR document skeleton the human fills in |
| `389-393` | 5 | TYPED | `cmd_new` | locks, writes the ADR, flips the one it supersedes |
| `394-400` | 5 | TYPED | `cmd_new` | returns the minted id and the written path |
| `401-417` | 15 | TYPED | `_flip` | rewrites the Status and Superseded by frontmatter fields |
| `418-433` | 14 | TYPED | `cmd_supersede` | refuses unless both ids exist and differ, then flips the old one |
| `434-450` | 15 | TYPED | `cmd_status` | validates the status against the schema enum, then flips |
| `451-493` | 27 | TYPED | `cmd_list` | publishes the decisions, the conformance pair and expired sunsets |
| `494-501` | 4 | cli-plumbing | `module` | subcommand dispatch table and the args holder |
| `502-564` | 42 | cli-plumbing | `parse` | argv parsing, valueless-flag and unknown-flag refusals |
| `565-570` | 6 | cli-plumbing | `main` | subcommand dispatch |
| `571-581` | 8 | TYPED | `main` | loads the schema and resolves the project and state roots |
| `582-620` | 30 | cli-plumbing | `main` | refusal printing, terminal rendering and exit codes |

### `bin/perry-state-cost` — 604 lines, 24 regions

```
    TYPED                           209
    SUPPORT:cli-plumbing            156
    SUPPORT:imports                  11
    SUPPORT:docstring               141
    SUPPORT:comment                  29
    SUPPORT:blank                    57
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                           604   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `76-88` | 11 | imports | `module` | stdlib imports and the PERRY_HOME sys.path bootstrap |
| `91-92` | 1 | TYPED | `Refused` | this tool's refusal type |
| `101-101` | 1 | TYPED | `module` | pins git's locale so quoted git errors are stable |
| `104-109` | 6 | TYPED | `git` | runs git in a repo and refuses on a non-zero status |
| `112-126` | 9 | TYPED | `repo_root` | asks git rev-parse for the work tree holding a path |
| `129-150` | 15 | TYPED | `tree_sizes` | ls-tree -z: (path, blob bytes) for every blob in a rev |
| `153-177` | 19 | TYPED | `history_sizes` | rev-list + cat-file batch-check: every blob version's size |
| `180-201` | 14 | TYPED | `packed_bytes` | count-objects -v: this clone's packed .git size in bytes |
| `204-219` | 8 | TYPED | `samples` | git log first-parent: the last sha of each calendar day |
| `222-234` | 8 | cli-plumbing | `thin` | picks N evenly spaced rows so the table fits a terminal |
| `240-270` | 19 | TYPED | `buckets` | reads schema claims into (prefix, exact, owner) buckets |
| `273-290` | 10 | TYPED | `state_prefixes` | repo-relative prefixes of the state root and .perry |
| `293-305` | 13 | TYPED | `classify` | matches a repo path against the declared claim prefixes |
| `311-344` | 34 | TYPED | `measure` | sums blob bytes and files per bucket, deduped by sha |
| `347-366` | 12 | TYPED | `breakdown` | per-file bytes and history under one tracked prefix |
| `369-412` | 40 | TYPED | `payload` | assembles the whole measurement from the git facts above |
| `418-419` | 2 | cli-plumbing | `commas` | thousands separator for a printed number |
| `422-431` | 4 | cli-plumbing | `short` | chops a path to a column heading width, tail kept |
| `434-513` | 78 | cli-plumbing | `render` | lays the measurement out as a fixed-width terminal report |
| `519-586` | 57 | cli-plumbing | `main` | hand-rolled argv scan, flag values and usage exits |
| `588-590` | 3 | TYPED | `main` | resolves the project root from --root, env or cwd |
| `591-595` | 5 | TYPED | `main` | runs the measurement; a refusal becomes exit 2 |
| `596-600` | 5 | cli-plumbing | `main` | prints JSON or the report and returns 0 |
| `603-604` | 2 | cli-plumbing | `module` | entry point |

### `viewer/tables.py` — 496 lines, 19 regions

```
    TYPED                            22
    OBSOLETE                        123
    SUPPORT:imports                   2
    SUPPORT:docstring               280
    SUPPORT:comment                  32
    SUPPORT:blank                    37
    ------------------------------------
    TOTAL                           496   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `67-72` | 2 | imports | `module` | stdlib imports |
| `73-73` | 1 | OBSOLETE | `module` | markdown's pipe-escape spelling, a table delimiter rule |
| `76-97` | 5 | TYPED | `line_break_at` | index of the first cell holding any splitlines boundary |
| `100-132` | 21 | OBSOLETE | `split_row` | parses a rendered markdown row into its cells |
| `135-158` | 9 | TYPED | `UnrenderableCell` | structured refusal type: index, value, why, flag |
| `161-189` | 4 | OBSOLETE | `render_row` | builds the markdown row and the escaped cell list |
| `197-201` | 5 | TYPED | `render_row` | refuses a value carrying a line break |
| `202-208` | 7 | OBSOLETE | `render_row` | round-trips the rendered row back through split_row |
| `211-234` | 2 | OBSOLETE | `render_separator` | renders an n-column markdown separator row |
| `237-251` | 2 | OBSOLETE | `check_cell` | one markdown table cell, normalised |
| `252-254` | 3 | TYPED | `check_cell` | refuses a value carrying a line break |
| `255-255` | 1 | OBSOLETE | `check_cell` | escapes the pipe so the cell survives the table |
| `258-291` | 26 | OBSOLETE | `cell_spans` | scans a rendered row for each cell's raw text offsets |
| `294-319` | 15 | OBSOLETE | `splice_cell` | rewrites one cell of a rendered row in place |
| `322-352` | 6 | OBSOLETE | `append_cell` | widens a rendered row by one trailing cell |
| `355-389` | 15 | OBSOLETE | `append_separator_cell` | widens a separator row in that row's own dash style |
| `392-421` | 2 | OBSOLETE | `squash` | folds a header cell's whitespace and decoration away |
| `424-462` | 16 | OBSOLETE | `HeaderIndex` | a folded header row with column lookup and row zip |
| `465-496` | 5 | OBSOLETE | `header_index` | the one fold of a header row, alias map applied after |

### `bin/perry-context-budget` — 460 lines, 24 regions

```
    TYPED                           180
    SUPPORT:cli-plumbing             75
    SUPPORT:imports                  11
    SUPPORT:docstring               123
    SUPPORT:comment                  28
    SUPPORT:blank                    42
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                           460   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `59-71` | 11 | imports | `module` | stdlib imports and the bin sys.path bootstrap |
| `76-82` | 2 | TYPED | `module` | the fallback ceiling and the transcript tail window |
| `85-93` | 8 | TYPED | `parse_size` | 200k and 200000 to one integer |
| `98-98` | 1 | TYPED | `module` | the config store key the ceiling setting mints |
| `101-146` | 21 | TYPED | `declared_ceiling` | scans .perry/config.jsonl for the ceiling setting record |
| `149-183` | 26 | TYPED | `resolve_ceiling` | flag, env, store then schema threshold, with the source |
| `186-193` | 3 | TYPED | `transcript_dir` | the host's transcript directory from the root's path slug |
| `196-207` | 6 | TYPED | `newest_transcript` | the .jsonl transcript with the newest mtime |
| `210-212` | 3 | TYPED | `_usage_of` | the usage dict of one transcript record, or None |
| `215-225` | 4 | TYPED | `context_of` | sums the three input-side token counts of a turn |
| `228-270` | 32 | TYPED | `last_usage` | seeks the tail and reads the last turn that reported usage |
| `273-349` | 62 | TYPED | `composition` | byte totals per block type and per shell command head |
| `352-364` | 12 | cli-plumbing | `main` | argparse declaration and --help |
| `372-375` | 4 | cli-plumbing | `main` | refuses an empty --root with exit 2 |
| `377-383` | 5 | TYPED | `main` | resolves home, root, ceiling and the transcript path |
| `385-396` | 12 | cli-plumbing | `main` | abstain report when no transcript exists, exit 0 |
| `398-398` | 1 | TYPED | `main` | the transcript's age in minutes from its mtime |
| `400-402` | 3 | TYPED | `main` | runs the whole-transcript composition scan |
| `403-420` | 18 | cli-plumbing | `main` | prints the composition tables or its JSON |
| `422-422` | 1 | TYPED | `main` | reads the last reported usage record |
| `423-436` | 10 | cli-plumbing | `main` | abstain report when no usage record, exit 0 |
| `438-439` | 2 | TYPED | `main` | the turn's context size and the over-ceiling test |
| `440-456` | 17 | cli-plumbing | `main` | verdict payload, printed lines and the gate exit code |
| `459-460` | 2 | cli-plumbing | `module` | entry point |

### `bin/perry-dispatch-limit` — 448 lines, 28 regions

```
    TYPED                           223
    SUPPORT:cli-plumbing             74
    SUPPORT:comment                 122
    SUPPORT:blank                    28
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                           448   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `1-11` | 1 | cli-plumbing | `module` | set -e strict-mode prologue |
| `12-48` | 4 | TYPED | `module` | reads env overrides into typed dispatch-limit integers |
| `49-64` | 9 | TYPED | `module` | typed TTL seconds, cache paths and lock-state scalars |
| `66-97` | 32 | cli-plumbing | `usage` | --help contract heredoc naming subcommands and env vars |
| `98-117` | 12 | TYPED | `mtime` | reads file mtime as an integer, accepting digits only |
| `118-130` | 11 | TYPED | `release_lock` | drops the lock dir only if this token still owns it |
| `131-162` | 29 | TYPED | `recover_stale_lock` | kill -0 on the owner pid plus age vs TTL, then renames it away |
| `163-194` | 26 | TYPED | `acquire_lock` | mkdir mutex with wait deadline, owner token and signal traps |
| `195-202` | 8 | TYPED | `validate_task_id` | rejects task ids outside the bounded filename charset |
| `203-226` | 14 | TYPED | `clean_stale` | expires markers past STALE_TTL by mtime and announces each reap |
| `227-233` | 6 | TYPED | `count_executor` | counts marker files matching one executor suffix |
| `234-239` | 5 | TYPED | `count_all` | counts every marker file in the cache dir |
| `240-290` | 24 | TYPED | `list_markers` | prints each marker name with its clock age against the TTL |
| `291-298` | 8 | TYPED | `max_for_executor` | maps a closed executor set to its typed concurrency cap |
| `299-340` | 13 | cli-plumbing | `main` | whole-vector --help scan, undeclared-flag refusal, case dispatch |
| `341-347` | 7 | cli-plumbing | `main.register` | binds two positional args and refuses a missing one with exit 2 |
| `348-352` | 5 | TYPED | `main.register` | validates the task id charset and the executor enum |
| `353-361` | 8 | TYPED | `main.register` | locks, sweeps stale, refuses a duplicate marker for this task |
| `362-375` | 13 | TYPED | `main.register` | counts markers and refuses over the per-executor or total cap |
| `376-389` | 13 | TYPED | `main.register` | writes the typed marker JSON to a temp file and renames it in |
| `390-393` | 4 | TYPED | `main.register` | re-counts markers and reports the new slot totals |
| `394-400` | 6 | cli-plumbing | `main.release` | binds the task-id arg and refuses a missing one with exit 2 |
| `401-405` | 5 | TYPED | `main.release` | validates the id, locks, unlinks that task's marker files |
| `406-412` | 6 | cli-plumbing | `main.check` | binds the executor arg and refuses a missing one with exit 2 |
| `413-416` | 4 | TYPED | `main.check` | validates the executor against the closed three-name set |
| `417-428` | 10 | TYPED | `main.check` | locks, sweeps stale, counts and exits 1 when at the cap |
| `429-434` | 5 | TYPED | `main.list` | locks, sweeps stale and lists the marker bookkeeping |
| `435-448` | 9 | cli-plumbing | `main` | bare invocation prints usage; unknown command exits 2 |

### `bin/perry-config` — 386 lines, 16 regions

```
    TYPED                           134
    SUPPORT:cli-plumbing            100
    SUPPORT:imports                  11
    SUPPORT:docstring                51
    SUPPORT:comment                  62
    SUPPORT:blank                    27
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                           386   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `20-32` | 11 | imports | `module` | stdlib imports and the viewer/bin sys.path bootstrap |
| `34-40` | 3 | cli-plumbing | `module` | the subcommand table and the track field flag map |
| `43-44` | 1 | TYPED | `Refused` | this tool's refusal type: nothing was written |
| `47-75` | 17 | TYPED | `read_records` | loads config.jsonl and refuses unless every record validates |
| `78-97` | 12 | TYPED | `renumber` | assigns each record its order, settings before tracks |
| `100-119` | 11 | TYPED | `write` | revalidates the records and replaces the store atomically |
| `120-131` | 12 | cli-plumbing | `write` | reports what was or would be written, and returns 0 |
| `134-139` | 6 | TYPED | `cmd_show` | splits the store records into settings, labels and tracks |
| `140-154` | 15 | cli-plumbing | `cmd_show` | prints them as JSON or as lines |
| `157-180` | 20 | TYPED | `cmd_set` | mints the setting key and upserts the setting record |
| `183-214` | 21 | TYPED | `cmd_track` | merges named track fields into the track record |
| `217-257` | 33 | cli-plumbing | `module` | the SURFACE contract bin/perry and --describe read |
| `260-294` | 28 | cli-plumbing | `main` | parses argv against SURFACE, help, describe, exit codes |
| `301-303` | 3 | TYPED | `main` | resolves the project root, the store path and state root |
| `309-375` | 43 | TYPED | `main` | under the lock: reads the store and dispatches each write |
| `378-386` | 9 | cli-plumbing | `module` | entry point and the refusal exit status |

### `bin/perry-restore-check` — 315 lines, 19 regions

```
    TYPED                            87
    SUPPORT:cli-plumbing             89
    SUPPORT:imports                   6
    SUPPORT:docstring                93
    SUPPORT:comment                   6
    SUPPORT:blank                    33
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                           315   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `67-73` | 6 | imports | `module` | stdlib imports |
| `75-75` | 1 | TYPED | `module` | this script's own resolved path |
| `78-81` | 4 | TYPED | `_git` | runs one git command in a repo and captures it |
| `84-90` | 6 | TYPED | `repo_root` | git rev-parse --show-toplevel for a path, or None |
| `93-103` | 5 | TYPED | `blob_at` | the committed bytes of a path at a ref, from git |
| `106-107` | 2 | TYPED | `md5` | the md5 digest of a byte string |
| `110-128` | 14 | TYPED | `self_check` | compares this file's bytes against HEAD's copy of it |
| `131-168` | 38 | TYPED | `check` | per path: digests the working copy against the ref's blob |
| `171-172` | 2 | cli-plumbing | `module` | the usage string |
| `175-195` | 4 | cli-plumbing | `_empty_root_error` | refuses an empty --root, importing lib only on that branch |
| `198-247` | 40 | cli-plumbing | `main` | help from any position, the argv scan and usage exits |
| `249-249` | 1 | TYPED | `main` | runs the self-check against git |
| `250-271` | 22 | cli-plumbing | `main` | the refusal message for a self-check that is not clean |
| `273-281` | 9 | TYPED | `main` | resolves the repo from --root or the first path's toplevel |
| `283-287` | 5 | TYPED | `main` | verifies the ref names a commit in that repo |
| `289-290` | 2 | TYPED | `main` | compares every path and folds the results into one verdict |
| `292-298` | 7 | cli-plumbing | `main` | the JSON payload and its exit status |
| `300-311` | 12 | cli-plumbing | `main` | the per-path lines and the exit status |
| `314-315` | 2 | cli-plumbing | `module` | entry point |

### `bin/perry-update-check` — 192 lines, 15 regions

```
    TYPED                            95
    SUPPORT:cli-plumbing             30
    SUPPORT:comment                  46
    SUPPORT:blank                    20
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                           192   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `1-13` | 1 | cli-plumbing | `module` | set -e strict-mode prologue |
| `14-16` | 1 | TYPED | `module` | computes the seven-day throttle window in seconds |
| `17-48` | 26 | cli-plumbing | `module` | parses --quiet --force --strict, help heredoc, exit 2 on bad flag |
| `49-64` | 12 | TYPED | `mtime_of` | reads file mtime as an integer, accepting digits only |
| `65-68` | 3 | cli-plumbing | `log/warn/fail` | quiet-aware echo helpers and the --strict exit-code selector |
| `69-100` | 20 | TYPED | `module` | resolves the install dir from env and known paths by SKILL.md test |
| `101-104` | 3 | TYPED | `module` | fails when no candidate install path exists |
| `105-119` | 10 | TYPED | `module` | resolves a symlinked install to a real path and sets IS_SYMLINK |
| `120-125` | 4 | TYPED | `module` | skips silently when the source dir is not a git checkout |
| `126-139` | 9 | TYPED | `module` | throttles on .update-check mtime against the 7-day window |
| `140-153` | 9 | TYPED | `module` | reads git porcelain dirtiness and branch name to set DEV_MODE |
| `154-163` | 5 | TYPED | `module` | fetches origin/main, counts commits behind, touches the stamp |
| `164-172` | 6 | TYPED | `module` | branches on the typed behind-count and exits 0 when current |
| `173-183` | 9 | TYPED | `module` | builds the dev-mode reason from symlink, dirty and branch flags |
| `184-192` | 7 | TYPED | `module` | attempts an ff-only pull and reports the resulting short sha |

### `bin/perry-codex-preflight` — 150 lines, 12 regions

```
    TYPED                            79
    SUPPORT:cli-plumbing             35
    SUPPORT:comment                  18
    SUPPORT:blank                    17
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                           150   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `1-8` | 1 | cli-plumbing | `module` | set -e strict-mode prologue |
| `9-17` | 5 | TYPED | `module` | reads env overrides for min version, TTLs and cache paths |
| `18-49` | 31 | cli-plumbing | `module` | parses --quiet --force, help heredoc, exit 2 on unknown flag |
| `50-65` | 12 | TYPED | `mtime_of` | reads file mtime as an integer, accepting digits only |
| `66-69` | 3 | cli-plumbing | `log/warn/fail` | quiet-aware echo helpers and the exit-1 failure helper |
| `70-73` | 3 | TYPED | `module` | tests whether codex resolves on PATH |
| `74-92` | 14 | TYPED | `module` | takes the version token from codex --version and sort -V compares |
| `93-105` | 10 | TYPED | `module` | throttles the smoke test on the cache file mtime against the TTL |
| `106-120` | 11 | TYPED | `module` | picks timeout or gtimeout and warns when neither is installed |
| `121-135` | 12 | TYPED | `module` | runs the codex smoke exec under a timeout and captures its exit |
| `136-147` | 10 | TYPED | `module` | fails on a nonzero exit or on a missing PERRY_OK sentinel token |
| `148-150` | 2 | TYPED | `module` | touches the smoke cache stamp and reports the pass |

### `bin/perry-detect-host` — 101 lines, 8 regions

```
    TYPED                            39
    SUPPORT:cli-plumbing              9
    SUPPORT:comment                  44
    SUPPORT:blank                     8
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                           101   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `1-19` | 1 | cli-plumbing | `module` | set -e strict-mode prologue |
| `20-32` | 8 | cli-plumbing | `module` | prints --help by slicing its own comment header with sed 2,16p |
| `33-46` | 12 | TYPED | `module` | folds the PERRY_HOST override onto the closed host token set |
| `47-65` | 5 | TYPED | `module` | detects codex-cli from runtime-owned CODEX_ env sentinels |
| `66-73` | 4 | TYPED | `module` | detects opencode from OPENCODE and OPENCODE_PID |
| `74-80` | 4 | TYPED | `module` | detects claude-code from CLAUDECODE and CLAUDE_CODE_ vars |
| `81-97` | 12 | TYPED | `module` | walks three parent pids, matching ps comm against host name globs |
| `98-101` | 2 | TYPED | `module` | falls back to the unknown token and always exits 0 |

### `bin/perry-okr` — 68 lines, 6 regions

```
    OBSOLETE                          2
    SUPPORT:cli-plumbing             12
    SUPPORT:imports                   6
    SUPPORT:docstring                34
    SUPPORT:comment                   5
    SUPPORT:blank                     8
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                            68   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `32-39` | 6 | imports | `module` | stdlib imports, sys.path bootstrap, lib and the store |
| `44-44` | 1 | cli-plumbing | `module` | the SURFACE bin/perry and --describe read |
| `47-59` | 6 | cli-plumbing | `main` | prints the usage block and this file's note for --help |
| `60-61` | 2 | OBSOLETE | `main` | hands every subcommand to the OKR.md projection driver |
| `62-64` | 3 | cli-plumbing | `main` | a refusal becomes a stderr line and exit 1 |
| `67-68` | 2 | cli-plumbing | `module` | entry point |

### 10.23 `bin/perry` — 162 lines, 8 regions (the enumeration gap, NOT in the 22)

```
    TYPED                            15
    SUPPORT:cli-plumbing             64
    SUPPORT:imports                  20
    SUPPORT:docstring                32
    SUPPORT:comment                  13
    SUPPORT:blank                    17
    SUPPORT:shebang                   1
    ------------------------------------
    TOTAL                           162   = wc -l   closes
```

| lines | code | category | owning function | call site |
|---|---:|---|---|---|
| `23-38` | 12 | imports | `module` | stdlib and the PERRY_HOME bootstrap |
| `39-44` | 3 | TYPED | `tool_paths` | the executables under bin, globbed |
| `45-55` | 8 | imports | `load` | SourceFileLoader import of one tool |
| `56-85` | 12 | TYPED | `surface_of` | the SURFACE dict a tool declares, or None |
| `86-114` | 23 | cli-plumbing | `cmd_list` | one line per tool and subcommand |
| `115-134` | 18 | cli-plumbing | `cmd_describe` | one tool's declared surface |
| `135-160` | 21 | cli-plumbing | `main` | list, describe, or dispatch into the tool |
| `161-162` | 2 | cli-plumbing | `module` | __main__ guard |
## 11. Defects found and NOT fixed

This row measures; it changes no behaviour. Everything below was found while
reading and is recorded rather than repaired. Ordered by what it would cost to
be wrong about.

1. **Three declared stores have no reader.** `perry/risks.jsonl` (4 records on
   disk here), `perry/asks.jsonl` (27) and `perry/intake.jsonl` (0) are declared
   in `schema § claims[]` and present, and `viewer/parsers.py` contains no
   reference to any of the three. `perry-state` reads all three registers off
   `BOARD.md` instead — confirmed by running it. **TASK-268 covers risks only;
   nothing is filed for asks or intake**, and the `intake` payload block was
   *added after* `intake.jsonl` was declared, reading `board.intake`.
2. **`bin/perry-goals § kr_rows:963-964` passes the project root where a state
   root is required.** `lib.task_status_index(state_root, board)` reads
   `<state root>/tasks.jsonl`; `perry-goals` hands it `snap.project_root` while
   `bin/perry-state:1893` hands it the state root, and the line immediately
   below passes `snap.state_root` to `load_linkage_store` with a comment
   explaining why. Measured on this worktree: `load_task_store(project_root)`
   → `None`, `load_task_store(state_root)` → **429 records**. So on Perry itself
   — and on every project whose state root is a subdirectory — `perry-goals
   list` derives `linked_task_completion` and `current_staleness` from
   `BOARD.md` alone, dropping every closed row, while `perry-state` reports the
   same KR from all 429. This is the exact failure `task_status_index`'s
   docstring says the store exists to prevent, and `build`'s own comment six
   lines earlier warns about.
3. **`bin/perry-diagnose`'s CON-03 guard is unsatisfiable.** `derive_findings`
   tests `"merge" in d["term"] or "integrat" in d["term"]`, but `d["term"]` can
   only be one of the nine strings built at `scan_concurrency:1366-1369` —
   `worktree`, `parallel session`, `ownership`, `owns`, `lane`, `one writer`,
   `concurrent`, `multi-agent`, `append-only`. None contains either substring,
   so the finding fires on every project with more than one worktree no matter
   what the rules file declares.
4. **`bin/perry-diagnose § scan_work_modes` goes permanently silent on a
   store-only project.** It reads `state_root/BOARD.md` and `OKR.md` through a
   reader that returns `""` on a missing file. A project that has stopped
   rendering the projections scores zero on every track, every verdict becomes
   `confidence: "none"`, and MODE-01 can never fire — reported to the user as
   "no distinguishing signal", indistinguishable from an unreadable folder.
   **This is what § 7.1's deletion does to a kept tool if the two rows are not
   sequenced.**
5. **`bin/perry-detect-host`'s `--help` is truncated mid-sentence.** The header
   comment runs lines 2-17; the slice is `sed -n '2,16p'`. Run: the output ends
   `"...the env override is"` and stops. The dropped line 17 states the tool's
   **exit-code guarantee**. No test pins the range, so any edit to the header
   re-cuts `--help` silently. Four SKILL.md entry points call this tool.
6. **`bin/perry-update-check:117-119` is dead, and `set -e` is why.** Line 111
   is `SRC="$(cd "$PERRY_LINK" 2>/dev/null && pwd -P)"`; under `set -e` a
   failing command substitution in an assignment terminates the script, so the
   `if [ -z "$SRC" ]` guard below can never fire from that branch — the script
   dies silently at exit 1, contradicting its own header contract (*"Always
   exits 0 unless the user explicitly passed --strict"*). A prefilter keeps it
   unreachable today, so it is latent: a guard that reads as protection and
   provides none.
7. **`bin/perry-knowledge § source_cites` matches on any shared token.** It
   splits on `[\s,;·|]+` and intersects, so `source_cites("see TASK-001", "see
   TASK-999")` → `True` and `source_cites("from the 2026-08 run", "from the
   2026-09 run")` → `True` (both probed directly). Since `cmd_propose` calls it
   against every existing card, one card whose `Source:` cell shares a prose
   word with the incoming source makes `propose` return `already-promoted` and
   suppresses the capture point for an unrelated card.
8. **131 lines of `viewer/parsers.py` have no production caller** — the whole
   conformance family, whose only documented caller `bin/perry-conform` was
   deleted. § 6.3.
9. **`bin/perry-explain § label` has no production caller.** Its only reference
   in the tree is `tests/test_diagnose.py`. `heading_title`'s docstring cites it
   as the place "where a *rendered* sentence discharges the never-travel-alone
   obligation"; that claim is no longer true of any code path.
10. **`bin/perry-context-budget` swallows a malformed `--ceiling`.** `try:
    return parse_size(flag) except ValueError: pass` falls through to env, store
    and schema, so `--ceiling 20o000` gates at a different number than the one
    asked for and exits as if it had obeyed. This is precisely the defect
    `bin/perry-state-cost:553-575` documents as *fixed* in its sibling.
11. **`TASK-090` is `done` and its claim is not true of the code.**
    `perry_store.py`'s docstring says the layout is "Derived from the board in
    this slice; TASK-090 is where the board reader goes", and TASK-090 closed as
    *"perry-task reads the store, not the board"*. The board is still the only
    input to `board_order`, `risk_records`, `intake_records`, `ask_records` and
    all four `*_plan` functions.
12. **`TASK-268`'s citation has rotted.** It names `perry-state:1631` as the
    risks call site; line 1631 is now inside `dossier_records`. The real sites
    are `build:1941` and `2161-2184`.
13. **`bin/perry-state § build()`'s documented default argument crashes.**
    `def build(root, project_root=None)` computes `perry_root = project_root or
    root` and uses it correctly at 1891-1892, but four payload lines use the raw
    parameter (2098, 2099, 2106, 2107). With `project_root=None` these raise
    `TypeError` on `None / ".perry"`. `main` always passes both, so it is
    latent; the default is unusable as documented.
14. **Smaller ones**, listed without argument: `perry-state` reads
    `.perry/events.jsonl` from disk three times per run; `viewer/tables.py:375`
    has an unreachable `" --- "` fallback; dead imports `re` in
    `perry-context-budget` and `os` in `perry-config`; `perry-config:321-337`
    carries the same comment three times (two byte-identical); dead
    `COMMITMENTS_NOTE_FROM_TEMPLATE` and `plain` in `perry-goals`;
    `lib.blank_marker`'s exception path restores the hardcoded `—` list the
    schema read was introduced to remove.

## 12. Rows this census says should be filed

Named here rather than filed: **this row may not write the task store.** The
PMO files them.

1. **Record the project-wide four totals in `DESIGN-014`, and restate
   `TASK-263`'s headline as a two-file result.** `§ 6` step 1 is now finished —
   24 files, 40,127 lines, 16,566 in the four categories — and `§ 5.1`'s three
   tables are still whole-file numbers written before any of it. The
   restatement matters more than the tables: *"OBSOLETE is the largest
   category"* is true of `perry-task` and `perry-lint` and false of the project
   (§ 5), while *"OBSOLETE is ~4x AGENT-OWNED"* is true of both and is the
   finding that should drive the plan. Whoever takes this should carry both
   sentences, because dropping either one is how the census gets remembered
   wrongly in the direction it was already remembered wrongly once.
2. **Correct `DESIGN-014 § 5.1` category B.** "Condemned in full" is false for
   all three files (§ 6). The table should carry the measured OBSOLETE line
   count per file, and the entry for `viewer/parsers.py` should record that
   OBSOLETE is not even its largest category.
3. **Give the five sole-implementation typed operations a home before Tier B
   runs** (§ 6.1): the `.perry/config.jsonl` reader/validator, root resolution,
   the YAML subset, the ADR reader, the linkage store reader. This is the row
   that makes `ADR-011` Tier B safe to schedule.
4. **File the asks and intake store reads.** TASK-268 covers risks only
   (§ 11.1).
5. **File the `## Commitments` deletion.** TASK-236's scope is the KR tables;
   TASK-042 covered Commitments and is `dropped`, leaving 337 measured lines
   with no row (§ 7.3).
6. **Delete the conformance family** — 131 lines whose tool is gone (§ 6.3).
7. **Move `bin/perry-dispatch-limit` from `DESIGN-014` category C to category
   A.** 223 of its 297 code lines are TYPED and they are specifically what
   category A is defined by — *"performs a write an agent cannot make safely"*:
   a `mkdir`-based mutex with a wait deadline and stale-owner recovery,
   `kill -0` liveness, mtime-vs-TTL expiry, and temp-file-plus-atomic-rename
   marker writes. It is not prose an agent could carry.
8. **Answer `DESIGN-014` open question 1 with the measurement.** Category C
   lists five tools totalling 2,875 lines as "code standing in for prose". Four
   of the five are measured here and the claim fails for every one:
   `perry-state-cost` 209 TYPED / **0** OBSOLETE / 0 AGENT (it does not import
   `re`), `perry-context-budget` 180 / **0** / 0, `perry-dispatch-limit` 223 /
   **0** / 0, `perry-knowledge` 196 / 49 / 15, `perry-explain` 182 / 90 / **17**.
   The only genuine category-C core found is `perry-explain § heading_title` —
   **17 lines**, not 2,875.
9. **Add `bin/perry-churn` to `DESIGN-014`.** It appears in none of the three
   tables (`grep -n churn` on the design doc returns nothing) and is 745 lines,
   228 TYPED, zero non-typed. It belongs in category A on its own terms.
10. **Fix the two live defects** — § 11.2 (`perry-goals` wrong root, wrong
   numbers in a published contract today) and § 11.3 (CON-03 always fires).
   These are the only two entries in § 11 that are wrong *now* rather than
   latent.
11. **Re-measure `bin/perry-restore-check`.** It went 315 → 364 lines on `main`
    after this census was pinned, so 49 of its lines are unmeasured here
    (§ 13). It is the only one of the 22 that moved.

## 13. What this row did not do

- **It did not measure at `main`'s current head.** Every number belongs to
  **`7f43a11c`**, and the 22 files are byte-identical at `583f024f`, the commit
  the Bound pins. `main` has since moved to `fe0292fb`, four merges ahead.
  **One file in scope changed there: `bin/perry-restore-check`, from work
  adding `tests/surface_reads.py` and `tests/test_bin_surface.py`.**
  Re-derived rather than read off the diffstat, because the two figures differ
  and the wrong one is the one a diffstat hands you: `git diff --stat` reports
  `79 ++-`, which is *churn*; `git show fe0292fb:bin/perry-restore-check |
  wc -l` is **364**, so the file went 315 → 364, a net **+49**. This report's
  `perry-restore-check` row, and only that row, is therefore stale against
  `main`: its 87 TYPED / 0 OBSOLETE is the measurement of a 315-line file, and
  49 lines of it are unmeasured. The corpus total of 27,132 is correct at the
  pinned commit and is **not** correct at `fe0292fb`, where the same 22 files
  are 27,181.
  Keeping the pin was the choice because the Bound requires it (*"pin it in
  the report's first line and measure nothing else"*) and because it is what
  makes the re-derived total match the spec exactly. Rebasing was defensible;
  an unstated mixture of the two would not have been.
- **It did not read 69% of the corpus line by line.** § 1d says exactly what was
  read, what was delegated, what verification the delegated work got, and what
  the one error the audit found implies about the rest. The four category
  totals are robust to errors of that size; an individual region is not.
- **It did not re-measure `bin/perry-task` (8,540) or `bin/perry-lint`
  (5,905).** Where a call site in scope calls into them the callee is named and
  only the call site's lines are counted, so the two censuses join without
  double-counting (§ 8.12).
- **It did not measure `tests/`.** `DESIGN-014 § 5.1` category B lists 4,601
  lines of tests as condemned alongside the three files; that figure is
  untouched here and the Bound excludes it. Several deletion dependencies in
  § 7 name tests that must move in the same change
  (`test_header_index_is_the_only_fold.py` watches `perry-diagnose § md_table`
  and `perry-goals § header_language` by name), and none of that is counted.
- **It did not act on the census.** Every move named in § 7 and every row named
  in § 12 is a later row.
- **It changed no behaviour, deleted nothing, and edited no file but this one.**

### Baseline

`bash tests/run` at `7f43a11c` before any work: **four failures, all known and
none mine** — `test_contract_key_parity` ×2, `test_resume.TestStaleRuns.
test_a_fresh_run_is_not_stale`, and `test_diagnose.TestUserLoadFindings.
test_perry_itself_passes_its_own_id_checks` (TASK-436, the dangling `USER-920`).
The tree guard reported that nothing under the worktree moved.

Re-run after the work: **the same four, and a `diff` of the two runs' `FAIL:`
lines is empty** — not "four again", but the same four tests. That is the check
worth stating, because a count can match while the membership changes.

**The tree guard tripped on the re-runs, and neither cause was this row's
work.** Run 2 flagged `perry/evidence/2026-09/TASK-348-result.md (changed)`,
which was me committing edits to this report while the suite was running —
my error, and the reason there was a run 3. Run 3 flagged
`perry/evidence/2026-09/TASK-362-round11-v4-review.md (created)`, a file this
row never touched, from another session's TASK-362 work; it is already gone
and `git status` is clean. Recorded rather than re-run into silence, because
"the guard went red and I decided it was fine" is exactly the claim a reviewer
should not have to take on trust. What is checkable instead:

```
git diff --stat 7f43a11c HEAD
 perry/evidence/2026-09/TASK-348-result.md | 2657 +++++++++++++++++++++++++++++
 1 file changed, 2657 insertions(+)
```

**This branch adds one file and changes nothing else** — no code, no test, no
store, no `.md` but this one. So no test can have changed state because of it,
and the identical `FAIL:` sets are what that predicts.

## Appendix A — the coverage assertion

`TASK-263-result.md` Appendix A, verbatim, so the two censuses compose. Used
for the 18 Python files.

```python
import ast

def support_sets(path):
    """The four mechanical support sets, with a fixed precedence."""
    src = open(path, encoding="utf-8").read()
    n = src.count("\n")                       # matches wc -l
    lines = src.split("\n")
    blank, comment = set(), set()
    for i in range(1, n + 1):
        s = lines[i - 1].strip()
        if s == "":                    blank.add(i)
        elif s.startswith("#"):        comment.add(i)
    doc = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.Module, ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef)):
            b = node.body
            if b and isinstance(b[0], ast.Expr) \
               and isinstance(b[0].value, ast.Constant) \
               and isinstance(b[0].value.value, str):
                doc |= set(range(b[0].lineno, b[0].end_lineno + 1))
    shebang = {1} if lines[0].startswith("#!") else set()
    comment -= shebang                        # precedence:
    blank -= doc; blank -= comment            #   shebang > docstring
    comment -= doc                            #   > comment > blank
    return n, {"docstring": doc, "comment": comment,
               "blank": blank, "shebang": shebang}

def check(path, regions):
    """regions: [(start, end, CATEGORY, owner, note)] over the code lines."""
    n, sup = support_sets(path)
    supported = set().union(*sup.values())
    code = set(range(1, n + 1)) - supported
    seen, dup = {}, []
    for (a, b, cat, owner, _note) in regions:
        for i in range(a, b + 1):
            if i in seen:
                dup.append((i, seen[i], (cat, owner)))
            seen[i] = (cat, owner)
    gaps = sorted(code - set(seen))
    counts = {}
    for i in code & set(seen):
        counts[seen[i][0]] = counts.get(seen[i][0], 0) + 1
    for k, v in sup.items():
        counts["SUPPORT:" + k] = len(v)
    assert not dup,  f"overlapping regions: {dup[:10]}"
    assert not gaps, f"{len(gaps)} unclaimed code lines: {gaps[:20]}"
    assert sum(counts.values()) == n, f"remainder {n - sum(counts.values())}"
    return counts
```

A region may span support lines; those are absorbed by the support sets and
counted once, there. That is why every table in § 10 carries a separate **code**
column — a region's `(start, end)` span is larger than the lines it contributes
to its category.

The zero-code check of § 1 step 4, run over all 1,018 regions:

```python
def no_empty_regions(path, regions, support):
    """A region that claims a call site and contributes no code line is not
    describing a call site — its offsets are wrong. TASK-263 Fault 1."""
    n, sup = support(path)
    code = set(range(1, n + 1)) - set().union(*sup.values())
    return [r for r in regions
            if not any(i in code for i in range(r[0], r[1] + 1))]
```

## Appendix B — the support extractor for the four shell files

`ast.parse` raises `SyntaxError` on a bash script, so the four files of § 0
correction 2 needed their own extractor. Same bucket names, same precedence,
same `check()` (it takes `support_sets` as its only file-format dependency).
The one thing it must do that the text-only reading of a Python file does not
is track heredocs, because a line beginning `#` inside a heredoc is data.

```python
import re

_HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")

def _heredoc_lines(lines):
    """Physical line numbers that sit INSIDE a heredoc body.

    The opening line is not included; the terminator is, because it is part of
    the block and carries no code of its own."""
    inside, n, i = set(), len(lines), 0
    while i < n:
        m = _HEREDOC.search(lines[i])
        if m and not lines[i].strip().startswith("#"):
            delim, dashed = m.group(2), "<<-" in lines[i]
            j = i + 1
            while j < n:
                cand = lines[j].strip() if dashed else lines[j].rstrip("\r")
                inside.add(j + 1)
                if cand == delim:
                    break
                j += 1
            i = j + 1
            continue
        i += 1
    return inside

def support_sets(path):
    """shebang / comment / blank, with heredoc bodies protected.

    `docstring` is always empty for sh and is still reported, so the bucket
    list is identical on both sides and the two halves can be summed."""
    src = open(path, encoding="utf-8").read()
    n = src.count("\n")                        # matches wc -l
    lines = src.split("\n")
    here = _heredoc_lines(lines)
    blank, comment = set(), set()
    for i in range(1, n + 1):
        if i in here:                  # heredoc body: data, never a comment
            continue
        s = lines[i - 1].strip()
        if s == "":                    blank.add(i)
        elif s.startswith("#"):        comment.add(i)
    shebang = {1} if lines[0].startswith("#!") else set()
    comment -= shebang
    return n, {"docstring": set(), "comment": comment,
               "blank": blank, "shebang": shebang}
```

The residual asymmetry this leaves — sh prose all landing in
`SUPPORT:comment`, and `perry-detect-host`'s 16 lines of shipped `--help` text
with it — is § 1b, and is flagged rather than worked around.
