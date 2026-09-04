# TASK-263 — call-site census of `bin/perry-lint` and `bin/perry-task`

> Row: TASK-263 · Spec: `perry/evidence/2026-09/TASK-263-spec.md`
> Applies: `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md` (rules 1-3 and § 5b)
> Serves: `perry/design/DESIGN-014-how-much-python.md § 5.1`
> Rung: V4 · **Read-only. No behaviour changed by this row.**

## 0. Commit measured, and a correction to the brief

Measured at **`2d2a06c`** (`main` when the worktree was cut), **not** at
`5601e45` as the dispatch brief named. This is not a deviation from the Bound:
the Bound requires "the named stable commit", and the two files in scope are
**byte-identical** at `5601e45`, at `2d2a06c`, and at `7f890f9` (`main` at the
time of writing). Verified by content hash rather than by `diff`, because a
diff that reports nothing and a diff that was not run look the same:

    5601e45   bin/perry-lint dc673fff…0337   bin/perry-task 7e6679dc…32cb
    2d2a06c   bin/perry-lint dc673fff…0337   bin/perry-task 7e6679dc…32cb
    worktree  bin/perry-lint dc673fff…0337   bin/perry-task 7e6679dc…32cb

so every line number in this report is valid at `5601e45` as well. The report
says `2d2a06c` because that is the commit that was actually read. `main` moved
four times during this measurement (`2d2a06c` → `a27a2a5` → `a7de65e` →
`7f890f9`); neither file in scope moved with it.

Line counts confirmed by `wc -l` at that commit:

| file | lines |
|---|---|
| `bin/perry-lint` | 5,144 |
| `bin/perry-task` | 7,851 |
| `viewer/parsers.py` (out of scope, TASK-099) | 5,011 |

The brief's three figures are correct. **`DESIGN-014 § 5.1`'s figures are stale**
— it records `perry-task` at 7,522, `perry-lint` at 4,483 and `parsers.py` at
4,603, measured 2026-09-01. All three files have grown since. Recorded here as a
finding, not fixed (this row does not edit design docs).

## 1. Method — and why it is not a grep

The failure mode this row exists to avoid is classifying a line because its
*name* matched a pattern. The method used here never matches on names. It has
three mechanical steps and one judgement step, and the judgement step reads code.

**Step 1 — mechanical support extraction.** `bin/perry-lint` and `bin/perry-task`
are parsed with `ast.parse`. Four support sets are derived from the AST and the
raw text, with a fixed precedence (`shebang` > `docstring` > `comment` > `blank`)
so that no line falls in two:

- `SUPPORT:shebang` — line 1 only.
- `SUPPORT:docstring` — the full line span of the first statement of every
  `Module`, `FunctionDef`, `AsyncFunctionDef` and `ClassDef` when it is a bare
  string constant. Taken from `node.lineno`/`node.end_lineno`, not from quote
  characters.
- `SUPPORT:comment` — physical lines whose `strip()` begins with `#`.
- `SUPPORT:blank` — physical lines whose `strip()` is empty.

Everything not in a support set is a **code line**. This is a partition of
`1..N` by construction.

**Step 2 — authored regions over the code lines.** Every code line is claimed by
exactly one authored `(start, end, category, owner, note)` region. Regions were
authored by walking the AST's top-level construct list in file order and reading
each construct's body. A construct is split into several regions whenever its
call sites fall in different categories; it is never rounded to one.

**Step 3 — coverage assertion.** A checker (`check()`, reproduced in Appendix A) asserts three things and fails loudly on any of them:
overlapping regions, code lines claimed by no region, and a category total that
does not equal the file's `wc -l`. **The arithmetic in § 4 is the output of that
assertion, not a hand tally.**

**The judgement step.** For each region the question asked is *what does this
call site do to a document*, answered by reading the statements in it:

- does it read a value out of a structure that is already typed (a `dict` from
  `json.loads` of a JSONL store, a schema enum, a `Path.stat()`, a `datetime`)?
- does it move a whole body from one place to another without looking inside?
- does it ask a natural-language question of prose (a regex over a title, a
  heading, a sentence, a cell that may contain arbitrary text)?
- does it reconstruct a fact from a rendering of a store that already holds it?

**Why this is not a grep.** Two demonstrations, both of which a name-based pass
gets wrong and are recorded in § 5:

1. `perry-lint § check_file` contains regex constants and calls into
   `viewer/parsers.py`, and would read as one AGENT-OWNED block by name. Read by
   call site it splits four ways — its frontmatter arm is TYPED, its schema-enum
   arm is TYPED, its table-shape arm is OBSOLETE, and its prose arms are
   AGENT-OWNED.
2. Conversely `perry-task § heading_matches` and `§ norm` carry no regex and no
   suggestive name, and are AGENT-OWNED: they answer "is this heading that
   heading?" over prose.

**Attribution across the file boundary.** Both tools do most of their document
reading *inside* `viewer/parsers.py` (5,011 lines, imported by 12 modules under
`bin/`). `parsers.py` is `TASK-099`'s scope, not this row's. Where a call site's
document handling actually happens there, the region is classified by **what the
call site asks for**, the line count is attributed to the call site only, and the
entry says `→ parsers.py` so the two censuses can be joined without
double-counting.

## 1b. The instrument, and the two things wrong with it that had to be fixed

The method above is graded, so this section records what the measuring
apparatus got wrong rather than only what it finally reported. Both faults were
in the instrument, not in the classifications, and both were caught by making
the document verify itself (§ 1c) rather than by inspection.

**Fault 1 — the region offsets for `check_reviews`' tail were wrong.** The
first authored region list placed the `asks.jsonl` read at `2663-2676` and the
ask-`blocks` scan at `2677-2678`. Both came back holding **zero code lines**,
because those spans are entirely comment: `check_reviews` carries a 27-line
comment block at `2664-2690` and the statements do not begin until `2691`. The
zero-line regions were the tell — a region that claims a call site and
contributes nothing cannot be describing a call site. Re-reading the statement
map moved them to `2663-2704` (the store read) and `2705-2706` (the
`re.findall(r"\b[A-Z]+-\d+\b", str(ask.get("blocks")))` line). Net effect on
the totals: 2 lines from TYPED to AGENT-OWNED. **The arithmetic closed both
before and after**, which is exactly why closure alone is not sufficient
evidence and the zero-line check is also needed.

**Fault 2 — two rows of this report broke their own tables.** The generated
region tables in § 4 and § 5 render each call site's note verbatim, and two
notes contained unescaped `|`:

    | `2579-2594` | 3 | `register_section_shape` | absent|table|prose|foreign … |
    | `5330-5343` | 3 | `risk_section_shape`     | table | bullets | foreign …  |

The first rendered as a 7-cell row and the second as a 6-cell row in a 4-column
table, so both call sites were **silently dropped** by any reader parsing the
tables — six code lines of `bin/perry-task` that the prose counted and the
tables did not carry. This is not an incidental typo: it is the defect class
`ADR-007` cites by name (*"`split_row`/`render_row`/the `\|` escape"*), and
this report reproduced it in the very tables that enumerate the code that
suffers from it. Fixed by escaping the pipes in both cells and in the
generator, so a re-render cannot reintroduce them. A width check now runs over
every table in this document and reports **0** malformed rows.

Neither fault changed a single classification. Both changed what the document
could be trusted to say, which is the same thing for a census.

## 1c. Why the arithmetic in § 8 can be checked without trusting this report

The region tables in § 4 and § 5 are not a rendering of a separate working
list — **they are the list**. A reader can harvest all 364 regions from the
published tables, feed them to the `check()` function published verbatim in
Appendix A, and get § 8's numbers back. That was run as the last step:

    perry-lint: 132 regions harvested FROM THE DOCUMENT |
                code-column mismatches 0 | total 5144 (file is 5144) CLOSES
    perry-task: 232 regions harvested FROM THE DOCUMENT |
                code-column mismatches 0 | total 7851 (file is 7851) CLOSES

Three properties are asserted, not asserted-about: no two regions overlap, no
code line is unclaimed, and each row's published **code** column equals what the
checker independently computes for that row's span. The second fault above was
found by this check failing — it reported six unclaimed code lines at `2579`,
`2591`, `2592`, `5330`, `5340`, `5341`, which are precisely the two broken rows.

## 2. The four categories as applied

| category | ADR-007 basis | test used at the call site | destination |
|---|---|---|---|
| **TYPED / DETERMINISTIC** | rule 1 | reads a bounded value space (schema enum, id format, ISO date, count) or computes an exact filesystem/clock fact | **stays in Python** |
| **OPAQUE DOCUMENT TRANSPORT** | rule 2, second half ("stored and rendered verbatim") | locates, reads, stores or renders a full body without interpreting its content | **may stay** |
| **AGENT-OWNED INTERPRETATION** | rule 2, first half ("no regex asks it a question") + § 5b's *"locate the file and hand it to an agent"* | extracts or judges meaning from an unbounded value space | **moves to a named agent workflow** |
| **OBSOLETE REPRESENTATION** | rule 3 + ADR-006/ADR-010 | parses a projection (`BOARD.md`, `OKR.md`, `.perry/config.md`) for a fact one of the six JSONL stores already holds typed | **deleted** once its store read exists |

The boundary between the last two is the one that does the work: a path that
parses `BOARD.md` for a status is **not** interpretation of prose that needs an
agent — the fact is already typed in `perry/tasks.jsonl` and the parse is simply
obsolete. It is only AGENT-OWNED when no typed store holds the answer.

## 3. Support buckets, named

| bucket | what is in it | derived by |
|---|---|---|
| `SUPPORT:shebang` | line 1 | text |
| `SUPPORT:docstring` | module + every function/class docstring span | AST |
| `SUPPORT:comment` | whole-line `#` comments | text |
| `SUPPORT:blank` | whitespace-only lines | text |
| `SUPPORT:cli-plumbing` | `argparse` construction, subcommand dispatch, exit codes, `--help` contract strings, output formatting that carries no document | authored region |
| `SUPPORT:imports` | `import` statements and the `sys.path` bootstrap | authored region |

`cli-plumbing` and `imports` are authored regions over **code** lines; the other
four are mechanical. All six are reported separately in § 4.

## 4. `bin/perry-lint` — 5,144 lines

    TYPED / DETERMINISTIC          649
    OPAQUE DOCUMENT TRANSPORT       83
    AGENT-OWNED INTERPRETATION     535
    OBSOLETE REPRESENTATION        972
    SUPPORT:cli-plumbing           485
    SUPPORT:imports                 50
    SUPPORT:docstring            1,000
    SUPPORT:comment              1,034
    SUPPORT:blank                  335
    SUPPORT:shebang                  1
    ------------------------------------
    TOTAL                        5,144   = wc -l   ✓ closes

**The headline: 972 of the 2,239 lines that land in one of the four categories
— 43% — are OBSOLETE REPRESENTATION.** That is the largest of the four, and it
is larger than TYPED. (Against the wider base of all 2,774 *code* lines — the
four categories plus `cli-plumbing` and `imports` — it is 35%. Every percentage
in this report uses the four-category base; both bases are given here so neither
can be misread.) `perry-lint`'s single biggest activity is checking renders of
stores that already hold the answer typed.

Two independent corroborations that the number is not an artefact of how the
regions were drawn:

- The **drift-census subtotal alone** (`_cell`, `_board_line_of`, `_order_drift`,
  the four `_empty_*_drift_stats` and the five `check_*_store_drift` functions)
  is **540 code lines**, against `DESIGN-014 § 5.1`'s estimate of "~918" — but
  DESIGN-014 was counting *physical* lines including this file's very heavy
  comment and docstring blocks. Re-measured on the same physical basis those
  regions span **1,229 physical lines**, so DESIGN-014's ~918 sits between the
  two and neither figure contradicts it.
- `check_file`'s table pass alone (`929-1233`) is **191 code lines**, the single
  largest region in the file, and every table the schema declares
  (`BOARD.md` × 5, `OKR.md` × 2, `phase/*.md` × 1, `.perry/config.md` × 1) is a
  render of a store. There is no table spec in the schema whose target is not
  store-backed — checked by enumerating `schema/state-schema.json § files[].tables`,
  not by name.


### 4.1 TYPED / DETERMINISTIC — 649 code lines

| lines | code | owning function | call site |
|---|---:|---|---|
| `151-156` | 3 | `module` | HERE/PERRY_HOME/SCHEMA_PATH — exact filesystem facts |
| `342-371` | 19 | `load_glossary` | loads the JSON schema into module tables |
| `431-445` | 4 | `module` | SCHEMA_THRESHOLDS / TASK_STATUSES / CARD_* from the schema |
| `446-458` | 9 | `_days_since` | ISO date -> whole days |
| `459-610` | 123 | `check_frontmatter` | typed validation of a YAML frontmatter store |
| `650-661` | 4 | `module` | TYPED_CELL / _TYPED_CELL_KINDS |
| `662-687` | 9 | `_accepts` | schema-declared prose for a typed cell kind |
| `688-692` | 2 | `module` | _TRACK_CONTEXTS cache, _STATE slot |
| `722-812` | 19 | `_track_context` | track register via perry-state declared_tracks_detail |
| `822-832` | 3 | `check_file` | line count vs the schema's tier cap |
| `844-852` | 6 | `check_file` | the plain over-cap finding |
| `1234-1252` | 3 | `check_cross_file` | root/.perry path arithmetic |
| `1271-1318` | 12 | `check_cross_file` | phase/CURRENT pointer resolves on disk |
| `1319-1351` | 11 | `check_cross_file` | tasks.jsonl store ids + parsed linkage frontmatter |
| `1359-1489` | 52 | `check_cross_file` | linkage edges compared against typed store ids |
| `1719-1738` | 19 | `check_verification` | close events out of events.jsonl |
| `1748-1757` | 1 | `module` | summary_shape = lib.summary_shape |
| `1758-1800` | 20 | `check_summaries` | tasks.jsonl read and open/closed partition |
| `1911-1922` | 12 | `resolves_somewhere` | path-form token resolved on the filesystem |
| `2167-2183` | 15 | `verdict_citations` | each candidate path resolved on the filesystem |
| `2190-2191` | 1 | `module` | GLOSSARY_PATH |
| `2287-2329` | 11 | `rounds_before_escalation` | env, config store and schema threshold |
| `2346-2416` | 4 | `check_reviews` | setup and accumulators |
| `2417-2431` | 14 | `check_reviews` | closed rows out of events.jsonl |
| `2537-2568` | 21 | `check_reviews` | status events out of events.jsonl |
| `2569-2625` | 30 | `check_reviews` | review history and days-at-review from events.jsonl |
| `2626-2662` | 36 | `check_reviews` | rung events; review-with-no-verdict |
| `2663-2704` | 14 | `check_reviews` | asks.jsonl read, record by record |
| `2707-2743` | 22 | `check_reviews` | round counting against the declared limit |
| `2819-2835` | 15 | `check_knowledge` | Seen: ISO date staleness against the threshold |
| `2922-2924` | 1 | `module` | SPEC_FILE_RE — a filename suffix, not a prose probe |
| `3130-3136` | 5 | `_rel` | path relativisation |
| `3193-3232` | 17 | `_well_typed` | store records split by declared type |
| `3267-3286` | 6 | `module` | _STORED_FIELDS and siblings — the stores' field lists |
| `4165-4177` | 5 | `is_adopted` | filesystem predicate |
| `4191-4250` | 31 | `check_claims` | which claimed paths exist and who wrote them |
| `4251-4253` | 1 | `module` | CLAIM_ROW_KEYS |
| `4254-4301` | 20 | `check_ns_collisions` | NS-01 from check_claims' rows |
| `4302-4341` | 20 | `looks_like_perry_state` | adoption provenance — ADR-007 decision 4 keeps this |
| `4342-4344` | 1 | `module` | _EVENT_FIELDS |
| `4345-4397` | 28 | `looks_like_perry_record` | JSONL key-set membership |

### 4.2 OPAQUE DOCUMENT TRANSPORT — 83 code lines

| lines | code | owning function | call site |
|---|---:|---|---|
| `813-821` | 7 | `check_file` | locate + read the whole body, dispatch on declared format |
| `1633-1645` | 5 | `check_verification` | locate BOARD.md |
| `4178-4190` | 11 | `iter_targets` | glob the files a spec claims; hands whole paths on |
| `4800-4812` | 13 | `main` | --templates: locate every template and hand it to check_file |
| `4813-4912` | 47 | `main` | project walk: resolve root, glob each spec, call check_file |

### 4.3 AGENT-OWNED INTERPRETATION — 535 code lines

| lines | code | owning function | call site |
|---|---:|---|---|
| `211-214` | 2 | `strip_comments` | removes HTML comments from a prose body |
| `215-230` | 13 | `headings` | ATX heading extraction with fence tracking |
| `231-247` | 14 | `section_body` | section slicing by heading match |
| `409-414` | 3 | `field_re` | alternation matching a `Name:` header field in prose |
| `415-430` | 3 | `heading_re` | matcher for a section heading in prose |
| `611-649` | 12 | `spec_claims` | discriminator read out of a document by regex |
| `853-859` | 6 | `check_file` | required_at_status: `Status:` regexed out of design/*.md |
| `901-928` | 25 | `check_file` | header_fields: `Name: value` regexed out of a document body |
| `1490-1507` | 15 | `check_cross_file` | design/*.md Status + Implementation-plan emptiness |
| `1538-1580` | 12 | `check_cross_file` | hook.md escalation bullets, via parsers.py |
| `1581-1584` | 2 | `module` | DATE_RE / RUNNABLE_RE — probes over evidence prose |
| `1585-1605` | 3 | `high_stakes_fragments` | escalation_union over hook + role prose |
| `1606-1632` | 17 | `rung_satisfied` | does this evidence PROSE satisfy this rung |
| `1646-1690` | 21 | `check_verification` | judge(): rung + high-stakes match over id+title prose |
| `1801-1854` | 30 | `check_summaries` | summary_shape(title, summary) — a prose comparison |
| `1855-1857` | 1 | `module` | SRC_RE — SRC-n ids scanned out of prose |
| `1858-1873` | 4 | `field_value` | `Name: value` regexed out of a document |
| `1874-1886` | 3 | `card_kind` | Kind: read out of a knowledge card |
| `1887-1910` | 2 | `resolves_somewhere` | a Source: cell tokenised as prose |
| `1933-1943` | 2 | `undecorate` | markdown emphasis stripped so a heading matches |
| `1979-2075` | 49 | `check_role_cards` | role-card section set — .perry/roles/*.md |
| `2076-2082` | 4 | `module` | VERDICT_KEYS / _VERDICT_BLOCK |
| `2083-2115` | 17 | `parse_verdicts` | === VERDICT === blocks parsed out of evidence prose |
| `2116-2128` | 3 | `module` | _CITE_LINE / _CITE_BAD / _CITE_SCRATCH |
| `2129-2166` | 10 | `verdict_citations` | path claims tokenised out of a verdict field |
| `2184-2189` | 1 | `module` | _BOUND_RE — `## Bound` presence in a spec document |
| `2192-2195` | 2 | `module` | _GLOSS_ENTRY |
| `2196-2212` | 14 | `parse_glossary` | ### term + prose + Implemented: parsed out of a document |
| `2213-2286` | 42 | `check_glossary` | glossary entries, and term-usage grep over the repo |
| `2432-2494` | 49 | `check_reviews` | verdict blocks parsed out of every evidence/**/*.md |
| `2705-2706` | 2 | `check_reviews` | task ids re.findall'd out of an ask's prose `blocks` field |
| `2744-2809` | 34 | `check_knowledge` | knowledge-card required fields out of prose |
| `2810-2818` | 8 | `check_knowledge` | Source: resolution |
| `2836-2921` | 60 | `check_provenance` | SRC-n ids and origin/date fields out of digests |
| `2925-3126` | 50 | `check_specs` | ## Files in scope / ## Deliverable / ## Bound in spec prose |

### 4.4 OBSOLETE REPRESENTATION — 972 code lines

| lines | code | owning function | call site |
|---|---:|---|---|
| `163-165` | 1 | `module` | PLACEHOLDER — {{...}} left in a RENDERED state file |
| `192-206` | 1 | `module` | KR_ID_RE — a KR id scanned out of phase markdown |
| `207-210` | 2 | `module` | LEGACY_KR_ID_RE + RE_COMMENT |
| `248-262` | 2 | `tables` | markdown table extraction |
| `263-303` | 26 | `tables_with_lines` | markdown table extraction, with row offsets |
| `304-315` | 1 | `module` | norm = squash — the header-cell fold |
| `316-324` | 3 | `module` | COLUMN/FIELD/HEADING_ALIASES — localized header spellings |
| `325-332` | 1 | `module` | MODE_NO_DEFAULT — checked against config.md's track table |
| `333-338` | 1 | `module` | STAGE_SEPARATORS — checked against a rendered Stages cell |
| `339-341` | 1 | `module` | UNDECLARED_CELL — the empty-cell sentinel set |
| `372-382` | 8 | `accepted` | accepted header spellings for a column |
| `383-390` | 5 | `column_index` | position of a column in a rendered header row |
| `391-408` | 6 | `canonical_column` | folded localized header key -> schema column |
| `833-843` | 11 | `check_file` | intake_rows(raw) — undischarged intake counted out of BOARD.md |
| `860-900` | 23 | `check_file` | required-heading presence over rendered state files |
| `929-1233` | 191 | `check_file` | the whole table pass over BOARD/OKR/phase/config renders |
| `1253-1270` | 16 | `check_cross_file` | legacy KR ids scanned out of every phase/*.md |
| `1352-1358` | 7 | `check_cross_file` | own_krs fallback: KR ids re-scanned out of phase markdown |
| `1508-1537` | 17 | `check_cross_file` | BOARD.md tables re-read for done-without-evidence |
| `1691-1718` | 23 | `check_verification` | BOARD.md section+table walk for done rows |
| `1739-1747` | 8 | `check_verification` | board-declares-no-rungs, counted off the board walk |
| `1923-1932` | 8 | `resolves_somewhere` | SRC-n / task-id token substring-searched in BOARD.md |
| `1944-1973` | 20 | `intake_rows` | ## Intake table counted out of BOARD.md |
| `1974-1978` | 3 | `heading_is_intake` | is this heading the Intake heading |
| `2330-2345` | 13 | `rounds_before_escalation` | the same setting parsed out of .perry/config.md |
| `2495-2536` | 34 | `check_reviews` | BOARD.md tables re-read for live status and rung |
| `3127-3129` | 1 | `module` | DRIFT_ROWS_SHOWN |
| `3137-3150` | 6 | `_cell` | a cell read out of a rendered row |
| `3168-3192` | 8 | `_board_line_of` | find a row's line number inside BOARD.md |
| `3287-3306` | 3 | `_empty_store_drift_stats` | drift census scaffolding |
| `3307-3530` | 97 | `check_store_drift` | BOARD.md vs tasks.jsonl |
| `3531-3536` | 3 | `_empty_risk_store_drift_stats` | drift census scaffolding |
| `3537-3679` | 102 | `check_risk_store_drift` | rendered risks vs risks.jsonl |
| `3680-3685` | 3 | `_empty_intake_store_drift_stats` | drift census scaffolding |
| `3686-3802` | 88 | `check_intake_store_drift` | rendered intake vs intake.jsonl |
| `3803-3808` | 3 | `_empty_ask_store_drift_stats` | drift census scaffolding |
| `3809-3947` | 102 | `check_ask_store_drift` | rendered asks vs asks.jsonl |
| `3948-3970` | 8 | `module/_empty_md_store_drift_stats` | OKR + config drift scaffolding |
| `3971-4115` | 93 | `check_md_store_drift` | OKR.md / .perry/config.md vs their stores |
| `4116-4164` | 23 | `_order_drift` | row ORDER in the render vs the store |


### 4.5 Authored support regions — 535 code lines

These are **code** lines placed in a named support bucket, listed here so the
region list is reconstructable in full from this document. The other four
support buckets (`docstring`, `comment`, `blank`, `shebang`) are derived
mechanically and need no table.

| lines | code | bucket | owning function | what it is |
|---|---:|---|---|---|
| `141-150` | 8 | `SUPPORT:imports` | `module` | stdlib imports |
| `157-162` | 5 | `SUPPORT:imports` | `module` | sys.path bootstrap + lib/parsers/tables imports |
| `166-191` | 16 | `SUPPORT:cli-plumbing` | `Finding` | the finding record and its two renderers |
| `693-721` | 13 | `SUPPORT:imports` | `_state_module` | lazy SourceFileLoader import of bin/perry-state |
| `3151-3167` | 10 | `SUPPORT:imports` | `_tasks_module` | SourceFileLoader import of bin/perry-tasks |
| `3233-3266` | 14 | `SUPPORT:imports` | `_store_module/_md_store_module` | SourceFileLoader imports |
| `4398-4414` | 15 | `SUPPORT:cli-plumbing` | `render_claims` | claims table output |
| `4415-4470` | 54 | `SUPPORT:cli-plumbing` | `main` | argv parsing, --help, schema load |
| `4471-4799` | 239 | `SUPPORT:cli-plumbing` | `main` | one dispatch arm per --flag: call, count, print |
| `4913-5138` | 155 | `SUPPORT:cli-plumbing` | `main` | severity tally, --json payload, human report, exit code |
| `5139-5144` | 6 | `SUPPORT:cli-plumbing` | `module` | __main__ guard |

## 5. `bin/perry-task` — 7,851 lines

    TYPED / DETERMINISTIC        2,029
    OPAQUE DOCUMENT TRANSPORT       40
    AGENT-OWNED INTERPRETATION     148
    OBSOLETE REPRESENTATION      1,110
    SUPPORT:cli-plumbing           432
    SUPPORT:imports                 31
    SUPPORT:docstring            2,104
    SUPPORT:comment              1,469
    SUPPORT:blank                  487
    SUPPORT:shebang                  1
    ------------------------------------
    TOTAL                        7,851   = wc -l   ✓ closes

**`perry-task` is the opposite shape to `perry-lint`, and that confirms
`DESIGN-014 § 5.1`'s placement of it in category A.** 2,029 of its 3,327
four-category lines — 61% — are TYPED / DETERMINISTIC: id minting, the store+journal
transaction with its recovery marker, the never-shrink invariant, schema-enum
validation and the refusals. Only 148 lines (4.4%) are AGENT-OWNED. The 1,110
OBSOLETE lines are one identifiable layer, not a diffuse condition:
`class Board` and the fifteen header/column/section helpers that serve it.

**Two additional splits worth stating in prose, because they are the census's
sharpest results:**

1. **`parse_depends` (593-617, OBSOLETE) and `store_depends` (618-622, TYPED)
   are the same fact read two ways, and they sit adjacent in the file.**
   `parse_depends` splits a `Depends on` *cell* on `[,，;；、\s]+`, strips
   `~~`/`**`/`` ` `` decoration off each token and dedupes. `store_depends` is
   `{r["id"]: list(r.get("depends_on") or []) for r in records}` — four lines,
   over the typed store. The second is already the replacement for the first;
   nothing has to be designed, only deleted. Its deletion dependency is
   `_cmd_list_from_board`, `check_depends` and `cmd_depends`, the three
   in-file callers.
2. **`_cmd_list_from_board` (421 physical lines) and `cmd_list` (187) are the
   same published payload built twice** — once by walking `BOARD.md`'s task
   tables, once from `tasks.jsonl`. Both emit the same frozen
   `LIST_CONTRACT` shape. The board version's only in-file caller is
   `store_records`; the store version is the replacement and already exists.

### The auto-split method for the command functions

Seventeen `cmd_*` functions and `commit()` interleave store work and board work
statement by statement, so rounding each to one category would have been the
error the spec forbids. Each was split mechanically: for every **top-level
statement of the function**, the set of call names reachable from that
statement's subtree (via `ast.walk`) is intersected with two helper sets —
BOARD-side (parses or edits `BOARD.md` text) and STORE-side (reads or writes a
typed JSONL store). A statement reaching only BOARD helpers is OBSOLETE, only
STORE helpers is TYPED, and neither inherits the function's declared default.
Adjacent statements of one category merge into one region. **The two helper
sets were established by reading each of the ~80 helpers, not by matching their
names** — `store_depends` and `parse_depends` differ by four characters and land
in opposite sets. `cmd_add`, for example, comes out as five regions:
`3370-3448` TYPED, `3449-3450` OBSOLETE (`target_section`), `3451-3511` TYPED,
`3512-3519` OBSOLETE (`widen_target_section`, `ensure_section`, `append_row`),
`3520-3562` TYPED.

### 5.1 TYPED / DETERMINISTIC — 2029 code lines, 117 regions

| lines | code | owning function | call site |
|---|---:|---|---|
| `179-182` | 3 | `module` | HERE/PERRY_HOME/SCHEMA_PATH |
| `358-361` | 2 | `load_schema` | schema load |
| `406-408` | 1 | `module` | ABSENT_RETIRED_SEE_LIB_IS_BLANK_CELL |
| `618-622` | 2 | `store_depends` | the same edges, straight from the typed records |
| `623-645` | 12 | `find_cycle` | deterministic DFS over typed edges |
| `646-720` | 24 | `check_depends` | edge validation against the store |
| `1287-1296` | 8 | `days_between` | date arithmetic |
| `1453-1463` | 3 | `declared_roles` | glob .perry/roles/*.md for declared names |
| `1464-1496` | 17 | `check_role` | role validated against the declared set |
| `1497-1523` | 12 | `check_rung` | rung validated against the schema enum |
| `1524-1543` | 7 | `check_priority` | priority validated against the schema enum |
| `1625-1646` | 5 | `module` | ID_RE / DEFAULT_PREFIX / PREFIX_RE / RESERVED / _ID_SHAPE |
| `1647-1659` | 10 | `task_id_prefixes` | declared id families |
| `1660-1716` | 22 | `resolve_prefix` | which family a new id mints into |
| `1717-1723` | 4 | `mint_id` | next id, never reused |
| `1724-1752` | 4 | `minting_records` | the store plus everything purge removed |
| `1807-1824` | 5 | `mint_register_id` | register id minting |
| `1825-1828` | 2 | `events_path` | path to events.jsonl |
| `1829-1847` | 14 | `read_events` | events.jsonl -> records |
| `1872-1894` | 20 | `load_task_records` | tasks.jsonl -> records |
| `1895-1902` | 5 | `hydrate_task_projection` | store record hydration |
| `1903-1916` | 11 | `task_record` | one record by id |
| `1939-2013` | 37 | `store_records` | the records a write will store |
| `2088-2098` | 5 | `module/_transaction_path/_digest` | transaction marker |
| `2099-2124` | 22 | `_safe_transaction_entry/_remove_transaction` | transaction marker |
| `2125-2190` | 49 | `recover_transaction` | deterministic crash recovery |
| `2191-2268` | 28 | `module` | REGISTER_EVENTS/SPEC/IDENTITY — event -> store routing |
| `2269-2310` | 15 | `substituted_away` | records this write does not carry forward, by identity |
| `2311-2394` | 30 | `substitution_report` | the loud line |
| `2395-2399` | 3 | `module` | SHRINK_ALLOWANCE |
| `2400-2425` | 10 | `declared_removal` | how many records the event declares it removes |
| `2426-2506` | 25 | `refuse_to_shrink` | the never-shrink invariant over typed counts |
| `2507-2578` | 38 | `load_register_records` | a register store as it is on disk |
| `2739-2791` | 44 | `replace_canonical_pair` | store+journal with rollback and recovery |
| `2813-3011` | 85 | `commit` | the store+journal transaction; the board band is the render path |
| `3027-3170` | 85 | `commit` | the store+journal transaction; the board band is the render path |
| `3237-3251` | 5 | `stages_of` | the track's declared stage vocabulary |
| `3252-3270` | 4 | `entry_stage` | the stage a row is born in |
| `3271-3284` | 4 | `check_stage` | stage validated against the vocabulary |
| `3285-3311` | 13 | `track_of` | the declared track by name |
| `3370-3448` | 43 | `cmd_add` | validate + mint + commit, with the board-row band split out |
| `3451-3511` | 34 | `cmd_add` | validate + mint + commit, with the board-row band split out |
| `3520-3562` | 23 | `cmd_add` | validate + mint + commit, with the board-row band split out |
| `3565-3630` | 18 | `cmd_start` | status transition + commit |
| `3631-3681` | 14 | `module` | PROVENANCE_/SIGNED_ constants |
| `3713-3736` | 14 | `signoff_options` | the one place an option is minted |
| `3737-3771` | 26 | `parse_item_selection` | --checked 1,3 / all / none |
| `3772-3808` | 25 | `resolve_signer` | the signer's name, filled in |
| `3809-3850` | 30 | `build_signoff` | the sign-off record |
| `3851-3873` | 14 | `render_signoff` | the record RENDERED into the journal block |
| `3874-3909` | 24 | `signoff_from_args` | assemble the signature `done` was given |
| `3910-3969` | 44 | `cmd_signoff_offer` | read-only prompt build |
| `3970-3977` | 8 | `cmd_done` | close + commit |
| `3979-3984` | 6 | `cmd_done` | close + commit |
| `3986-4042` | 31 | `cmd_done` | close + commit |
| `4045-4055` | 4 | `cmd_stage` | stage move + re-stamp |
| `4057-4068` | 8 | `cmd_stage` | stage move + re-stamp |
| `4075-4082` | 8 | `cmd_stage` | stage move + re-stamp |
| `4104-4156` | 7 | `cmd_track` | move onto another declared track |
| `4158-4189` | 23 | `cmd_track` | move onto another declared track |
| `4195-4195` | 1 | `cmd_track` | move onto another declared track |
| `4198-4218` | 16 | `cmd_track` | move onto another declared track |
| `4221-4240` | 11 | `cmd_status` | any other status transition |
| `4242-4259` | 10 | `cmd_status` | any other status transition |
| `4265-4269` | 5 | `cmd_status` | any other status transition |
| `4271-4280` | 10 | `cmd_status` | any other status transition |
| `4283-4315` | 8 | `cmd_depends` | declare/replace/clear depends_on |
| `4318-4321` | 4 | `cmd_depends` | declare/replace/clear depends_on |
| `4324-4324` | 1 | `cmd_depends` | declare/replace/clear depends_on |
| `4326-4335` | 10 | `cmd_depends` | declare/replace/clear depends_on |
| `4338-4357` | 12 | `known_design_ids` | design ids that have a document |
| `4358-4438` | 42 | `cmd_design_link` | declare/replace/clear design links |
| `4460-4519` | 22 | `repair_off_board_cell` | write one cell of a record with no board row |
| `4587-4609` | 10 | `module` | cmd_next / cmd_retitle |
| `4610-4652` | 31 | `cmd_summary` | rewrite the non-projected summary field |
| `4659-4668` | 3 | `module` | cmd_rung / cmd_evidence |
| `4669-4695` | 6 | `cmd_drop` | remove a row with a reason |
| `4697-4698` | 2 | `cmd_drop` | remove a row with a reason |
| `4700-4717` | 13 | `cmd_drop` | remove a row with a reason |
| `4862-4937` | 18 | `cmd_purge` | take a record out of tasks.jsonl |
| `4944-4974` | 24 | `cmd_purge` | take a record out of tasks.jsonl |
| `5035-5037` | 1 | `module` | USER_ID_RE |
| `5038-5047` | 2 | `mint_user_id` | next USER-NNN |
| `5048-5068` | 8 | `cmd_ask` | put a question to the user |
| `5076-5083` | 8 | `cmd_ask` | put a question to the user |
| `5086-5091` | 5 | `cmd_answer` | record the answer |
| `5094-5108` | 15 | `cmd_answer` | record the answer |
| `5147-5157` | 9 | `check_frequency` | frequency validated against a closed set |
| `5158-5166` | 7 | `parse_on` | --on parsed to a weekday/day number |
| `5167-5176` | 3 | `stamp_due` | the next due date computed |
| `5362-5381` | 2 | `mint_risk_id` | next RX-NNN |
| `5620-5620` | 1 | `cmd_risk_add` | raise a risk into the board table |
| `5664-5665` | 2 | `cmd_risk_clear` | retire a risk in the board table |
| `5756-5762` | 1 | `cmd_route` | move an intake row onto the board |
| `5764-5772` | 9 | `cmd_route` | move an intake row onto the board |
| `5775-5788` | 9 | `cmd_route` | move an intake row onto the board |
| `5790-5850` | 29 | `cmd_route` | move an intake row onto the board |
| `5853-5865` | 10 | `cmd_route` | move an intake row onto the board |
| `5868-5904` | 9 | `cmd_prioritize` | move a row to another priority section |
| `5906-5907` | 2 | `cmd_prioritize` | move a row to another priority section |
| `5909-5929` | 3 | `cmd_prioritize` | move a row to another priority section |
| `5931-5937` | 7 | `cmd_prioritize` | move a row to another priority section |
| `5941-5970` | 15 | `cmd_prioritize` | move a row to another priority section |
| `6104-6174` | 31 | `live_dispatch_ids` | ids holding a dispatch slot |
| `6175-6219` | 8 | `rows_with_no_computable_age` | open rows with no clock, from typed fields |
| `6220-6423` | 96 | `stranded_row_findings` | the four conformance entries, over typed rows |
| `6478-6492` | 5 | `dependency_satisfied` | one declared edge, resolved |
| `6493-6535` | 12 | `resolved_edge` | one depends_on id with what it is attached to |
| `6536-6578` | 19 | `resolve_dependency_edges` | blocked_by / blocks set in place |
| `6579-6630` | 26 | `_cmd_list_from_board` | payload scaffolding — superseded whole by cmd_list |
| `6698-7001` | 110 | `_cmd_list_from_board` | the event-log half, and the typed enrichment |
| `7002-7190` | 144 | `cmd_list` | the same payload from tasks.jsonl — the replacement path |
| `7191-7193` | 1 | `module` | _PERRY_STATE |
| `7235-7248` | 2 | `split_stages` | the stage vocabulary of a Stages cell |
| `7249-7255` | 2 | `default_stages` | the mode's default vocabulary |
| `7410-7546` | 56 | `cmd_events` | the event log's tail, in log order |
| `7565-7582` | 2 | `project_lock` | serialize the whole read-modify-write |

### 5.2 OPAQUE DOCUMENT TRANSPORT — 40 code lines, 2 regions

| lines | code | owning function | call site |
|---|---:|---|---|
| `3173-3199` | 19 | `append_block` | append a body under the last `## heading` of the day |
| `3200-3236` | 21 | `append_status_change` | append under the last `## Status changes` |

### 5.3 AGENT-OWNED INTERPRETATION — 148 code lines, 9 regions

| lines | code | owning function | call site |
|---|---:|---|---|
| `409-455` | 23 | `evidence_paths` | free-text Evidence cell split into path spans |
| `456-458` | 1 | `module` | EVIDENCE_SEPARATORS |
| `459-568` | 35 | `evidence_relations` | the same cell typed into {text,path,kind} by regex |
| `1397-1399` | 1 | `module` | _IDISH — id-shaped tokens in prose |
| `1400-1452` | 9 | `idish_tokens_that_resolve_nowhere` | ids scanned out of a prose cell |
| `3682-3712` | 18 | `check_no_user_claim` | refuse a drafted option that ASSERTS what a person did |
| `4723-4738` | 3 | `names_id` | does this TEXT cite tid as an id, or merely contain it |
| `4739-4746` | 2 | `module` | _REFERENCE_SCAN constants |
| `4747-4861` | 56 | `live_references` | every place a surviving record or register NAMES tid |

### 5.4 OBSOLETE REPRESENTATION — 1110 code lines, 91 regions

| lines | code | owning function | call site |
|---|---:|---|---|
| `362-366` | 3 | `board_table_spec` | the BOARD.md P[012] table spec |
| `367-405` | 4 | `columns_for` | which BOARD.md columns this row sets |
| `569-576` | 2 | `module` | HANDLE_RE / DEP_ID_RE — id shapes read out of cells |
| `577-589` | 2 | `strip_handle` | strikethrough/bold stripped off a rendered id cell |
| `590-592` | 1 | `module` | _DEPENDS_SPLIT |
| `593-617` | 11 | `parse_depends` | a `Depends on` CELL split into ids |
| `721-730` | 4 | `canonical_column` | a header cell folded back to a schema column |
| `731-744` | 1 | `module` | PRIORITY_RE — BOARD.md section headings |
| `771-1243` | 259 | `Board` | BOARD.md as lines: locate, widen, insert, replace, remove |
| `1244-1247` | 2 | `module` | _ALIASES/_DISPLAY column maps |
| `1248-1286` | 17 | `_build_column_maps` | schema i18n -> board header spellings |
| `1297-1309` | 5 | `norm` | the header-cell fold |
| `1310-1333` | 4 | `header_keys` | a rendered header row -> keys |
| `1334-1337` | 2 | `id_column_keys` | which header key is the id column |
| `1338-1361` | 10 | `header_language` | which language a rendered header is in |
| `1362-1368` | 4 | `display_name` | key -> displayed header text |
| `1369-1371` | 1 | `module` | _HEADINGS |
| `1372-1396` | 11 | `heading_spellings` | accepted spellings of a board section heading |
| `1544-1579` | 9 | `heading_matches` | does this line open the `## ` section called name |
| `1580-1582` | 1 | `module` | REQUIRED_KEYS — the six board columns |
| `1583-1600` | 10 | `check_header` | refuse a board header whose columns cannot be placed |
| `1601-1624` | 4 | `widening_columns` | which board columns a section must gain |
| `1753-1806` | 9 | `minting_text` | the same, for a register with NO store: ids out of TEXT |
| `1848-1871` | 5 | `_Ops/_ops` | the two rules perry_store resolves a BOARD through |
| `1917-1925` | 7 | `module` | _STORE_TO_BOARD — store field -> board column |
| `1926-1938` | 10 | `task_projection_row` | locate the board row, then fill its cells |
| `2014-2058` | 36 | `refuse_store_drift` | board and store compared before a write |
| `2059-2073` | 3 | `parsed_status` | a `Status` CELL -> the enum value in it |
| `2074-2087` | 2 | `unstorable_status_rows` | rows whose board Status the store cannot hold |
| `2579-2594` | 3 | `register_section_shape` | `absent` \| `table` \| `prose` \| `foreign` for a board section |
| `2595-2642` | 16 | `carry_forward_is_addressable` | stored records vs the rows now at those keys |
| `2643-2738` | 51 | `register_change` | the register store DERIVED FROM THE BOARD as mutated |
| `2792-2794` | 1 | `module` | LAST_UPDATED_RE |
| `2795-2812` | 9 | `stamp_last_updated` | rewrite `> Last updated:` in the render |
| `3012-3026` | 4 | `commit` | the store+journal transaction; the board band is the render path |
| `3312-3347` | 15 | `target_section` | which BOARD.md section a new row is filed in |
| `3348-3369` | 8 | `widen_target_section` | add columns to that board section |
| `3449-3450` | 1 | `cmd_add` | validate + mint + commit, with the board-row band split out |
| `3512-3519` | 4 | `cmd_add` | validate + mint + commit, with the board-row band split out |
| `3978-3978` | 1 | `cmd_done` | close + commit |
| `3985-3985` | 1 | `cmd_done` | close + commit |
| `4056-4056` | 1 | `cmd_stage` | stage move + re-stamp |
| `4069-4074` | 6 | `cmd_stage` | stage move + re-stamp |
| `4085-4103` | 5 | `widen_row_section` | add columns to whichever board section holds a row |
| `4157-4157` | 1 | `cmd_track` | move onto another declared track |
| `4190-4194` | 3 | `cmd_track` | move onto another declared track |
| `4196-4197` | 1 | `cmd_track` | move onto another declared track |
| `4241-4241` | 1 | `cmd_status` | any other status transition |
| `4260-4264` | 5 | `cmd_status` | any other status transition |
| `4270-4270` | 1 | `cmd_status` | any other status transition |
| `4316-4317` | 2 | `cmd_depends` | declare/replace/clear depends_on |
| `4322-4323` | 2 | `cmd_depends` | declare/replace/clear depends_on |
| `4325-4325` | 1 | `cmd_depends` | declare/replace/clear depends_on |
| `4445-4447` | 1 | `module` | _BOARD_TO_STORE |
| `4448-4459` | 9 | `_row_is_on_the_board` | does the projection hold a line for this id |
| `4520-4586` | 39 | `cell_writer` | read+write one board cell, then commit |
| `4696-4696` | 1 | `cmd_drop` | remove a row with a reason |
| `4699-4699` | 1 | `cmd_drop` | remove a row with a reason |
| `4938-4943` | 6 | `cmd_purge` | take a record out of tasks.jsonl |
| `4977-5016` | 31 | `cmd_resolve_intake` | discharge an `## Intake` board row |
| `5017-5034` | 14 | `cmd_intake` | create the `## Intake` board section and a row |
| `5069-5075` | 7 | `cmd_ask` | put a question to the user |
| `5092-5093` | 2 | `cmd_answer` | record the answer |
| `5111-5128` | 8 | `module` | CAD_ID_RE / CADENCE_COLUMNS / FREQ_HELP |
| `5129-5146` | 2 | `mint_cadence_id` | next CAD-NNN out of the register's TEXT |
| `5177-5233` | 30 | `cmd_cadence_add` | write a row into the cadence board table |
| `5234-5305` | 47 | `cmd_cadence_done` | record an occurrence, recompute Next due, in the board |
| `5306-5329` | 5 | `module` | RISK_ID_RE / RISK_COLUMNS / is_risk_header / _RISK_* patterns |
| `5330-5343` | 3 | `risk_section_shape` | `table` \| `bullets` \| `foreign` for `## Top risks` |
| `5344-5361` | 16 | `refuse_foreign_risk_table` | refuse a `## Top risks` Perry did not write |
| `5382-5398` | 8 | `risk_bullets` | risk bullets located in the markdown |
| `5399-5488` | 39 | `ensure_risk_table` | convert `## Top risks` bullets to a table in place |
| `5489-5526` | 18 | `require_migrated` | refuse a write into an unmigrated section |
| `5527-5581` | 31 | `cmd_risk_migrate` | the bullets->table conversion |
| `5582-5619` | 17 | `cmd_risk_add` | raise a risk into the board table |
| `5621-5621` | 1 | `cmd_risk_add` | raise a risk into the board table |
| `5624-5663` | 28 | `cmd_risk_clear` | retire a risk in the board table |
| `5666-5666` | 1 | `cmd_risk_clear` | retire a risk in the board table |
| `5682-5707` | 7 | `check_intake_undischarged` | undischarged `## Intake` rows |
| `5708-5755` | 29 | `cmd_intake_sweep` | move discharged intake rows off the board |
| `5763-5763` | 1 | `cmd_route` | move an intake row onto the board |
| `5773-5774` | 2 | `cmd_route` | move an intake row onto the board |
| `5789-5789` | 1 | `cmd_route` | move an intake row onto the board |
| `5851-5852` | 2 | `cmd_route` | move an intake row onto the board |
| `5905-5905` | 1 | `cmd_prioritize` | move a row to another priority section |
| `5908-5908` | 1 | `cmd_prioritize` | move a row to another priority section |
| `5930-5930` | 1 | `cmd_prioritize` | move a row to another priority section |
| `5938-5940` | 2 | `cmd_prioritize` | move a row to another priority section |
| `5973-6103` | 46 | `board_sections` | `## Top risks`, `## User Input Queue` and board drift |
| `6424-6477` | 25 | `ask_register` | the `## User Input Queue` board table read back |
| `6631-6697` | 45 | `_cmd_list_from_board` | the BOARD.md task-table walk |


### 5.5 Authored support regions — 463 code lines

These are **code** lines placed in a named support bucket, listed here so the
region list is reconstructable in full from this document. The other four
support buckets (`docstring`, `comment`, `blank`, `shebang`) are derived
mechanically and need no table.

| lines | code | bucket | owning function | what it is |
|---|---:|---|---|---|
| `166-178` | 11 | `SUPPORT:imports` | `module` | stdlib imports |
| `183-191` | 7 | `SUPPORT:imports` | `module` | sys.path bootstrap + lib/perry_store/parsers imports |
| `192-199` | 1 | `SUPPORT:cli-plumbing` | `Refused` | the refusal exception |
| `200-321` | 100 | `SUPPORT:cli-plumbing` | `module` | LIST_CONTRACT/LIST_SEMANTICS — the published payload contract |
| `322-357` | 23 | `SUPPORT:cli-plumbing` | `module` | EVENTS_CONTRACT/EVENTS_SEMANTICS |
| `745-770` | 24 | `SUPPORT:cli-plumbing` | `module` | NON_TASK_REFUSAL — refusal copy |
| `7194-7228` | 13 | `SUPPORT:imports` | `perry_state` | SourceFileLoader import of bin/perry-state |
| `7229-7234` | 4 | `SUPPORT:cli-plumbing` | `module` | READ_ONLY_COMMANDS / TASK_ROW_COMMANDS |
| `7256-7353` | 69 | `SUPPORT:cli-plumbing` | `Args/parse` | argv parsing |
| `7354-7409` | 23 | `SUPPORT:cli-plumbing` | `module` | TASK_EVENTS / EVENT_FIELD / SECTION_EVENTS output tables |
| `7547-7564` | 16 | `SUPPORT:cli-plumbing` | `module` | COMMANDS dispatch table |
| `7583-7844` | 167 | `SUPPORT:cli-plumbing` | `main` | dispatch, ctx assembly, output, exit codes |
| `7845-7851` | 5 | `SUPPORT:cli-plumbing` | `module` | __main__ guard |

## 6. Destinations — every non-typed entry

The spec requires each non-typed path to name its owning function, its
downstream callers, a concrete replacement store/manifest or agent workflow,
and its deletion dependency. Entries are grouped by destination; the owning
functions in each group are listed in full, so the union of the groups is the
complete set of non-typed owners (4 + 26 + 27 in `perry-lint`, 2 + 7 + 63 in
`perry-task`).

### 6.1 OBSOLETE → `perry/tasks.jsonl`, rendered by `perry-tasks render --write`

| | |
|---|---|
| **Owners (`perry-task`)** | `Board` (259), `cell_writer` (39), `refuse_store_drift` (36), `_cmd_list_from_board` (45), `task_projection_row` (10), `_row_is_on_the_board` (9), `parsed_status` (3), `unstorable_status_rows` (2), `target_section` (15), `widen_target_section` (8), `widen_row_section` (5), `heading_matches` (9), `check_header` (10), `widening_columns` (4), `columns_for` (4), `board_table_spec` (3), `canonical_column` (4), `norm` (5), `header_keys` (4), `display_name` (4), `id_column_keys` (2), `header_language` (10), `heading_spellings` (11), `_build_column_maps` (17), `_Ops/_ops` (5), `strip_handle` (2), `parse_depends` (11), `board_sections` (46), `module` const blocks (30), plus the OBSOLETE bands of `cmd_add` (5), `cmd_stage` (7), `cmd_status` (7), `cmd_track` (5), `cmd_depends` (5), `cmd_done` (2), `cmd_drop` (2), `cmd_purge` (6), `cmd_prioritize` (5), `cmd_route` (6), `commit` (4) |
| **Owners (`perry-lint`)** | `check_file` (225), `check_store_drift` (97), `_order_drift` (23), `_cell` (6), `_board_line_of` (8), `_empty_store_drift_stats` (3), `tables` (2), `tables_with_lines` (26), `accepted` (8), `column_index` (5), `canonical_column` (6), the `check_cross_file` BOARD band (17), the `check_verification` board bands (31), the `check_reviews` board band (34) |
| **Downstream callers** | inside `perry-task`, every `cmd_*` reaches `Board` through `ctx["board"]`; `main` constructs it. Inside `perry-lint`, `main` calls `check_file` per schema spec and `check_store_drift` on the default pass. |
| **Destination** | `perry/tasks.jsonl` already holds every field these paths read — `store_records`, `load_task_records`, `task_record` and `store_depends` are the typed readers, and `cmd_list` already publishes the identical `LIST_CONTRACT` payload from them. The render direction is `perry_store.render` + `perry-tasks render --write`. |
| **Deletion dependency** | `BOARD.md` must stop being hand-editable in fact and not only in doctrine — `ADR-007` decision 2 accepted this and `perry-state § drift` measured `drift: 0`. Concretely: `cell_writer`, `cmd_*` and `commit` must write the record and re-render rather than edit lines, at which point `Board` and its fifteen header helpers have no caller. `_cmd_list_from_board` is deletable as soon as `store_records` stops calling it. |

### 6.2 OBSOLETE → `perry/risks.jsonl` · `perry/intake.jsonl` · `perry/asks.jsonl`

| | |
|---|---|
| **Owners** | `perry-task`: `ensure_risk_table` (39), `cmd_risk_migrate` (31), `cmd_risk_clear` (29), `cmd_risk_add` (18), `require_migrated` (18), `refuse_foreign_risk_table` (16), `risk_bullets` (8), `risk_section_shape` (3), `cmd_resolve_intake` (31), `cmd_intake_sweep` (29), `cmd_intake` (14), `check_intake_undischarged` (7), `ask_register` (25), `cmd_ask` (7), `cmd_answer` (2), `register_change` (51), `carry_forward_is_addressable` (16), `register_section_shape` (3). `perry-lint`: `check_risk_store_drift` (102), `check_intake_store_drift` (88), `check_ask_store_drift` (102), `intake_rows` (20), `heading_is_intake` (3), the three `_empty_*_drift_stats` (9) |
| **Downstream callers** | `commit` → `register_change`; `main` → the `cmd_risk_*` / `cmd_intake*` / `cmd_ask` arms; `_cmd_list_from_board` and `cmd_list` → `ask_register`, `board_sections` |
| **Destination** | all three stores exist and are validated today — `perry_store.risk_records`, `.intake_records`, `.ask_records`, routed by `REGISTER_SPEC` (2203-2217). `register_change` derives them **from the board as mutated**; the replacement is to write the store directly and render the section from it, exactly as `REGISTER_SPEC` already names the readers for. |
| **Deletion dependency** | `register_change`'s board-derivation is the single choke point: once the `cmd_risk_*` / intake / ask writers append to their store, `register_section_shape`, `carry_forward_is_addressable`, `risk_bullets`, `ensure_risk_table` and `require_migrated` (the bullets→table migration) all lose their callers, and `perry-lint`'s three drift censuses lose their subject. |

### 6.3 OBSOLETE → `perry/okr.jsonl`

| | |
|---|---|
| **Owners** | `perry-lint`: `check_cross_file` legacy-KR band `1253-1270` (16), `own_krs` fallback band `1352-1358` (7), `KR_ID_RE` / `LEGACY_KR_ID_RE` (2) |
| **Downstream callers** | `main` → `check_cross_file` on the default pass |
| **Destination** | `perry/okr.jsonl` holds KR records typed; `bin/perry-okr render --write` produces `OKR.md` and the phase files' KR tables. The id-shape check becomes a store-record validation (a KR id either is or is not a record key), which is `ADR-007` rule 1 rather than a `re.findall` over markdown. |
| **Deletion dependency** | the phase markdown must stop being a KR source. `check_cross_file`'s own comment already says of the legacy form *"nothing reads the old form any more"* — the `own_krs` fallback at `1352-1358` is the last reader that would, and it exists only because `parse_linkage` can return an empty KR set. |

### 6.4 OBSOLETE → `.perry/config.jsonl`

| | |
|---|---|
| **Owners** | `perry-lint`: `rounds_before_escalation` band `2330-2345` (13), `check_md_store_drift`'s config half (part of 93), `MODE_NO_DEFAULT` (1), `STAGE_SEPARATORS` (1), `UNDECLARED_CELL` (1), `COLUMN/FIELD/HEADING_ALIASES` (3) |
| **Downstream callers** | `check_reviews` → `rounds_before_escalation`; `check_file` → the alias tables; `main` → `check_md_store_drift` |
| **Destination** | `.perry/config.jsonl` is canonical and `bin/perry-config` reads it; `rounds_before_escalation` **already prefers the store** (`2324-2328`) and only falls through to `.perry/config.md` at `2330-2335`. That fallthrough is the whole deletable region. |
| **Deletion dependency** | none beyond removing the markdown fallback branch — the store path above it is live and tested. This is the smallest and cheapest deletion in the census. |

### 6.5 OBSOLETE → a store that does not exist yet: `perry/cadence.jsonl`

| | |
|---|---|
| **Owners** | `perry-task`: `cmd_cadence_done` (47), `cmd_cadence_add` (30), `mint_cadence_id` (2), `minting_text` (9), `CAD_ID_RE` / `CADENCE_COLUMNS` / `FREQ_HELP` (part of `module`) |
| **Downstream callers** | `main` → the `cadence add` / `cadence done` arms; `mint_register_id` → `minting_text` |
| **Destination** | **a seventh JSONL store, `perry/cadence.jsonl`, built on the `risks.jsonl` pattern** — same `REGISTER_SPEC` tuple shape (`section`, `store_path`, `records`, `validate`, `section_shape`, `(table, id_column)`), same render. This is the one OBSOLETE group in the census whose destination store **is not on disk today**; it is named here as the concrete thing to build, not as "improve the parser". |
| **Deletion dependency** | the store must be created first. `minting_text` (1753-1806) is the tell: its own docstring says it is `minting_records` *"for a register that has no store"*, and cadence is now the only such register — `USER-` and `RX-` ids reach it too, but `asks.jsonl` and `risks.jsonl` exist, so those two calls are already redundant with `minting_records`. |

### 6.6 AGENT-OWNED → the V4 review workflow (`work/reference/review.md`)

| | |
|---|---|
| **Owners** | `perry-lint`: `check_reviews` (51), `check_specs` (50), `parse_verdicts` (17), `rung_satisfied` (17), `verdict_citations` (10), `check_verification § judge` (21), `VERDICT_KEYS` / `_VERDICT_BLOCK` / `_CITE_*` / `_BOUND_RE` / `DATE_RE` / `RUNNABLE_RE` (10) |
| **Downstream callers** | `main` → `check_reviews` (`--reviews`), `check_specs` (`--specs`), `check_verification` (`--verification`); all three also run capped on the default pass |
| **Destination** | the reviewing agent already reads the evidence document. `rung_satisfied` asks *"does this evidence prose name a command / a rubric / a date"* and `check_specs` asks *"does this spec offer a scannable scope and a `## Bound`"* — both are judgements the V4 reviewer is already making and is better at. What survives as Python is the **typed** half: `tasks.jsonl § verification` is an enum, and a `## Bound` either exists as a heading or does not. The prose judgement moves to the round; the enum check stays. |
| **Deletion dependency** | the `=== VERDICT ===` block must stop being the transport. Its fields (`task`, `rung`, `result`, `criteria`, `checked`) are five typed values embedded in prose; written by the reviewing agent through a tool call into a store, `parse_verdicts` and `_VERDICT_BLOCK` have nothing to parse. `verdict_citations`' path-existence half (`2167-2183`, already counted TYPED) survives that move unchanged. |

### 6.7 AGENT-OWNED → the knowledge lane

| | |
|---|---|
| **Owners** | `perry-lint`: `check_provenance` (60), `check_knowledge` (42), `card_kind` (3), `field_value` (4), `spec_claims` (12), `resolves_somewhere` prose band (2), `SRC_RE` (1) |
| **Downstream callers** | `main` → `check_knowledge` (`--knowledge`), `check_provenance` (`--provenance`); `check_file` → `spec_claims` per schema spec |
| **Destination** | a knowledge-card store on the `risks.jsonl` pattern holding the four provenance fields (`Kind`, `Source`, `Received`, `Seen`) typed, with the card's *body* left as unparsed prose. `card_kind` is the giveaway: it exists solely to re-derive, by regex over a document, the discriminator that `schema § files[id=knowledge-card].discriminator` already declares — the record would carry it as a field. |
| **Deletion dependency** | `field_value` is shared with `check_file`'s header-field loop (§ 6.8), so it outlives this group by one step. |

### 6.8 AGENT-OWNED → the document-generating agent (ADR-007 § 5b, "locate the file and hand it to an agent")

| | |
|---|---|
| **Owners** | `perry-lint`: `check_role_cards` (49), `check_glossary` (42), `parse_glossary` (14), `check_file` header/status bands (31), `check_cross_file` design band (15) and hook band (12), `high_stakes_fragments` (3), `headings` (13), `section_body` (14), `strip_comments` (2), `undecorate` (2), `field_re` (3), `heading_re` (3), `field_value` (4), `_GLOSS_ENTRY` (2). `perry-task`: `check_no_user_claim` (18) |
| **Downstream callers** | `main` → `check_file` (per `design`, `role-card`, `hook`, `architecture` spec), `check_glossary` (`--glossary`), `check_cross_file`; `signoff_options` → `check_no_user_claim` |
| **Destination** | `ADR-007 § 5b` settles this one by name: `design/*.md` and `.perry/roles/*.md` are documents and *"Python should not be parsing them at all, not even leniently"*. The lane agent that writes a design doc or a role card asserts its own `Status`, its section set and its escalation list; `perry-lint`'s job shrinks to **locating** the file (which is § 6.11's transport) and reporting that an agent has not been run over it. The one exception carved out and kept typed: `.perry/hook.md`'s escalation list becomes a typed `high_stakes: [string]` array in `.perry/config.jsonl`, with the prose rationale staying in `hook.md` unparsed — the union in `high_stakes_fragments` then reads an array instead of extracting bullets. |
| **Deletion dependency** | `headings`, `section_body`, `strip_comments` and `undecorate` are the shared markdown lexer and are the LAST of this group to go — they have callers in every other group. They are deletable only when § 6.1-6.5's renders and § 6.6-6.7's stores are all done. |

### 6.9 AGENT-OWNED → a field split, on `ADR-007`'s own `By when` precedent

| | |
|---|---|
| **Owners** | `perry-task`: `evidence_relations` (35), `evidence_paths` (23), `live_references` (56), `names_id` (3), `idish_tokens_that_resolve_nowhere` (9), `_REFERENCE_SCAN` consts (4). `perry-lint`: `check_summaries` shape band (30), the `check_reviews` ask-`blocks` line `2705-2706` |
| **Downstream callers** | `cmd_list` and `_cmd_list_from_board` → `evidence_paths`, `evidence_relations`; `cmd_purge` → `live_references` → `names_id`; `main` → `idish_tokens_that_resolve_nowhere` |
| **Destination** | `ADR-007` decision 3 split `By when` into `due` (typed) + `by_when_note` (prose) and **deleted `CLOCK_RE` rather than giving it a sixth round**. The same split applies three times here: `tasks.jsonl § evidence` → typed `evidence_paths: [path]` + prose `evidence_note`; `asks.jsonl § blocks` → typed `blocks: [task_id]` + prose; `tasks.jsonl § next_action` → prose, with any cited id carried in a typed field. `evidence_relations`' own docstring already did this analysis on 139 live cells and concluded that `round` *"has no bearer"* — it is the strongest argument in the repository for the split, made by the function that would be deleted by it. |
| **Deletion dependency** | one migration over the live corpus (139 evidence cells here), then the readers go. `live_references` and `names_id` survive only as long as an id can be cited inside prose; with `blocks` and `depends_on` typed, `cmd_purge`'s safety scan becomes a store query. |

### 6.10 AGENT-OWNED → the writing agent, already decided

`perry-lint § check_summaries` shape band (`1801-1854`, 30 lines) calls
`lib.summary_shape(title, summary)`, which folds case and punctuation to ask
whether a summary restates its title. **TASK-330 already removed two of this
function's four checks on 2026-09-03** on the ground that how well a summary
reads is the writing agent's job. The remaining `summary-repeats-title` is the
same kind of question and goes the same way; `summary-missing` is a
presence test on a typed field and stays. Deletion dependency: none — the store
half of `check_summaries` (`1758-1800`, 20 lines, already TYPED) is
independent of it.

### 6.11 OPAQUE DOCUMENT TRANSPORT — 123 lines, and all of it may stay

| owner | lines | what it moves | may it stay? |
|---|---:|---|---|
| `perry-lint § main` (`4800-4912`) | 60 | resolves the project root, globs each schema spec's path, hands whole files to `check_file` | yes — locating a file is exactly what `ADR-007 § 5b` leaves to Python |
| `perry-lint § iter_targets` | 11 | globs the files a spec claims | yes |
| `perry-lint § check_file` (`813-821`) | 7 | `path.read_text()` and dispatch on the declared format | yes |
| `perry-lint § check_verification` (`1633-1645`) | 5 | locates `BOARD.md` | yes, though its subject disappears with § 6.1 |
| `perry-task § append_status_change` | 21 | appends a status line under the last `## Status changes` of the day | yes, with the caveat in § 7.7 |
| `perry-task § append_block` | 19 | appends a multi-line block under the last `## <heading>` of the day | yes, with the caveat in § 7.7 |

The journal is the one document in Perry that is **append-only prose written by
a tool and read by a human**, and neither of these two functions interprets what
it appends. That is the category's definition, so they stay.

## 7. Ambiguous regions, listed explicitly

The spec requires these to be named rather than absorbed. Nine were found. In
each case the call site was placed in one category and the reason it could have
gone elsewhere is recorded here.

### 7.1 `perry-lint § check_file` is target-multiplexed — the largest ambiguity in the census

`check_file` (`813-1231`, 262 code lines across four regions) is generic over a
`spec` from `schema/state-schema.json` and is called once per file spec. Its
three loops therefore hit store-backed renders and prose documents *in the same
code*. The fan-out, counted by enumerating `schema § files[]` rather than by
reading names:

| loop | region | targets | store-backed | prose document | classified |
|---|---|---|---:|---:|---|
| `spec["tables"]` | `929-1233` | `BOARD.md`×5, `OKR.md`×2, `phase`×1, `config.md`×1 | **9** | **0** | OBSOLETE — unambiguous |
| `spec["headings"]` | `860-900` | board 6, okr 6, phase 10, design 7, architecture 1, hook 1 | 22 | 9 | OBSOLETE (dominant) |
| `spec["header_fields"]` | `901-928` | phase 2, config 8, design 2, knowledge 4, card 5, role 3 | 10 | **14** | AGENT-OWNED (dominant) |
| `required_at_status` | `853-859` | `design/*.md` only | 0 | 1 | AGENT-OWNED — unambiguous |

**The tables loop is not ambiguous at all**, which is the useful finding: there
is no table spec in the schema whose target is not store-backed, so all 191 of
its code lines are OBSOLETE without a judgement call. The two middle rows are
genuinely split and were assigned by which population dominates. A reader who
wants the other split can move 23 lines (`860-900`) from OBSOLETE to
AGENT-OWNED and 25 (`901-928`) the other way; the file total is unaffected.

### 7.2 The shared markdown lexer — `headings`, `section_body`, `strip_comments`, `undecorate`

31 code lines, classified **AGENT-OWNED**. They are called by nine functions
spanning both populations (`check_file` and `check_verification` over renders;
`check_cross_file`, `check_reviews`, `check_specs`, `check_role_cards`,
`check_glossary`, `check_knowledge`, `check_provenance` over prose). The
classification follows the *surviving* caller set: once § 6.1-6.5 delete the
render readers, every remaining caller is a prose document. Under the opposite
rule — classify by today's call count — they would be OBSOLETE.

### 7.3 `perry-lint § check_frontmatter` — 123 lines, classified TYPED

This validates `phase/*-linkage.md` against typed field rules (`required`,
`type`, `pattern`, `enum`, `enum_by_stage`). YAML frontmatter is a **typed
serialization**, not prose, so rule 1 governs and Python owns it. Under a strict
reading of rule 3 — *"the Python layer never parses a document at all"* — it is
still Python parsing a `.md` file, and would be AGENT-OWNED. It is the single
largest TYPED region in `perry-lint` and therefore the most consequential of the
nine; it is called out so the count can be re-derived either way.

### 7.4 `perry-task § commit` band `3012-3026` — classified OBSOLETE, contains the legitimate direction

This 15-line band holds `stamp_last_updated(board)`, `unstorable_status_rows`,
`register_change` — all board-parse — **and** `perry_store.render(board, records,
_ops())`, which is the render direction `ADR-007` explicitly endorses. It is
counted OBSOLETE because the render call is passed the *parsed* `Board` so it
can preserve the file's hand layout, and so it cannot outlive `Board`. A render
that regenerates `BOARD.md` wholesale from the store would be TYPED. This is the
one place in the census where a legitimate operation is counted in a condemned
category, and the reason is a dependency, not the operation.

### 7.5 The cadence family — OBSOLETE with no destination store on disk

`cmd_cadence_add`, `cmd_cadence_done`, `mint_cadence_id`, `minting_text` and
their constants (88 code lines) parse and write a `## Cadence` board table.
Every other OBSOLETE group in this census points at a JSONL store that already
exists; **this one points at `perry/cadence.jsonl`, which must be built first**
(§ 6.5). Naming it as OBSOLETE is a judgement that the board table is a
projection-in-waiting rather than the canonical form; the alternative reading is
that cadence is simply not yet in scope for `ADR-007` at all.

### 7.6 `perry-lint § looks_like_perry_state` / `looks_like_perry_record` — 48 lines, classified TYPED

`looks_like_perry_state` reads the first bytes of a file and tests for the
markers `Owner**: \`perry\`` and `$PERRY_HOME`. That is Python reading a
document. It is classified TYPED because **`ADR-007` decision 4 names this
population explicitly as the survivor**: *"What survives is adoption of a
foreign project, which is parsing by definition."* The answer is a bounded
boolean over a fixed marker, not a question put to prose.

### 7.7 `perry-task § append_block` / `append_status_change` — TRANSPORT that locates by heading

40 code lines. They append a body under *the last* `## <heading>` of the day's
journal file, so they must find that heading — a parse. They are TRANSPORT
because they never interpret what they append or what they append it beside, and
the journal has no store. If the journal ever becomes a store, they become
OBSOLETE together.

### 7.8 `perry-lint § resolves_somewhere` and `§ verdict_citations` — split three and two ways

Both tokenise a prose cell and then test each token against the filesystem.
`resolves_somewhere` splits into AGENT-OWNED (`1887-1910`, tokenising), TYPED
(`1911-1922`, path existence) and OBSOLETE (`1923-1932`, `tok in
BOARD.md.read_text()` — a substring search of a render). `verdict_citations`
splits AGENT-OWNED (`2129-2166`) / TYPED (`2167-2183`). Rounding either to one
category would have been the error the spec forbids; the boundaries are the
statement boundaries where the string stops being prose and becomes a path.

### 7.9 `perry-lint § PLACEHOLDER` (`{{...}}`) — 1 line, classified OBSOLETE

A `{{…}}` marker is a mechanical token, not prose, which argues TYPED. It is
classified OBSOLETE because what it detects — an unfilled field in a rendered
state file — is a fact the store answers directly (the field is absent or
empty), and the marker only exists because the file is authored as a template.

## 8. Arithmetic

Both files close exactly. The totals below are the output of the coverage
assertion described in § 1 step 3, which fails on overlap, on an unclaimed code
line, and on a total that is not `wc -l`. It reported neither an overlap nor a
gap on either file.

### `bin/perry-lint`

    TYPED / DETERMINISTIC            649
    OPAQUE DOCUMENT TRANSPORT         83
    AGENT-OWNED INTERPRETATION       535
    OBSOLETE REPRESENTATION          972
          (four categories)      2,239
    SUPPORT:cli-plumbing             485
    SUPPORT:imports                   50
                (authored support)    535
    SUPPORT:docstring              1,000
    SUPPORT:comment                1,034
    SUPPORT:blank                    335
    SUPPORT:shebang                    1
             (mechanical support)   2,370
    ----------------------------------------
    649 + 83 + 535 + 972 + 535 + 2,370 = 5,144
    wc -l bin/perry-lint            = 5,144      remainder 0

### `bin/perry-task`

    TYPED / DETERMINISTIC          2,029
    OPAQUE DOCUMENT TRANSPORT         40
    AGENT-OWNED INTERPRETATION       148
    OBSOLETE REPRESENTATION        1,110
          (four categories)      3,327
    SUPPORT:cli-plumbing             432
    SUPPORT:imports                   31
                (authored support)    463
    SUPPORT:docstring              2,104
    SUPPORT:comment                1,469
    SUPPORT:blank                    487
    SUPPORT:shebang                    1
             (mechanical support)   4,061
    ----------------------------------------
    2,029 + 40 + 148 + 1,110 + 463 + 4,061 = 7,851
    wc -l bin/perry-task                   = 7,851      remainder 0

**Reproducing it.** `ast.parse` both files, derive the four mechanical support
sets with the precedence `shebang > docstring > comment > blank`, take the
complement as the code set, and check the authored region list in § 4 and § 5
covers it exactly once. The region lists are the tables in those sections; the
`(start, end)` pairs are disjoint and in file order.

## 9. Cross-file summary

| | `perry-lint` | `perry-task` | both |
|---|---:|---:|---:|
| physical lines | 5,144 | 7,851 | 12,995 |
| all code lines | 2,774 | 3,790 | 6,564 |
| **four-category lines** (the base for every % below) | 2,239 | 3,327 | 5,566 |
| TYPED / DETERMINISTIC | 649 (29%) | 2,029 (61%) | 2,678 (48%) |
| OPAQUE DOCUMENT TRANSPORT | 83 (4%) | 40 (1%) | 123 (2%) |
| AGENT-OWNED INTERPRETATION | 535 (24%) | 148 (4%) | 683 (12%) |
| OBSOLETE REPRESENTATION | **972 (43%)** | 1,110 (33%) | **2,082 (37%)** |
| support (authored + mechanical) | 2,905 | 4,524 | 7,429 |

**Three results.**

1. **The two files are opposite shapes, and `DESIGN-014 § 5.1` put them in the
   right categories.** `perry-task` is 61% TYPED — the write core, exactly the
   "what only code can do" column. `perry-lint` is 29% TYPED and 43% OBSOLETE:
   its single largest activity is checking renders of stores that already hold
   the answer.

2. **OBSOLETE is the largest category across both files at 2,082 code lines —
   larger than AGENT-OWNED by 3:1.** That is the census's main correction to the
   framing `ADR-007` is usually summarised with. The ADR is remembered for
   *"no regex asks prose a question"*, and 683 lines do that. But three times as
   much code is not asking prose anything — it is re-deriving, out of a
   rendering, a fact that a JSONL store one directory away already holds typed.
   **Most of the removable code is deletable without an agent being involved at
   all**, which makes it cheaper and lower-risk than the ADR's headline suggests.

3. **Only 123 lines — 2% — are OPAQUE DOCUMENT TRANSPORT**, and all of it may
   stay. The "locate the file and hand it to an agent" posture `ADR-007 § 5b`
   prescribes is barely implemented in these two files; almost everything that
   touches a document today either interprets it or parses a projection.

**What that implies for `DESIGN-014`'s implementation plan**, stated as a
measurement and not a recommendation: of the 5,566 code lines in these two
files, 2,678 are load-bearing determinism that stays, 123 are transport that
stays, and 2,765 have a named destination elsewhere — 2,082 of them into stores
that already exist on disk (with the single exception of cadence, § 6.5), and
683 into agent workflows.

## 10. Defects found and NOT fixed

This row measures; it changes no behaviour. Three defects were found while
reading and are recorded rather than repaired.

1. **`DESIGN-014 § 5.1`'s line counts are stale.** It records `bin/perry-task`
   at 7,522, `bin/perry-lint` at 4,483 and `viewer/parsers.py` at 4,603,
   measured 2026-09-01. At `2d2a06c` they are 7,851, 5,144 and 5,011 — all
   three have grown, `perry-lint` by 15%. `§ 1`'s "97,474 lines of Python" and
   the 10:1 ratio are correspondingly stale. Not fixed: this row does not edit
   design docs, and `DESIGN-014` is `locked`.

2. **`bin/perry-lint § load_glossary`'s docstring justifies the function with a
   tool that no longer exists.** Lines 354-369 read: *"`bin/perry-conform` needs
   the same validation on one file, and a second copy of this loop is exactly
   the two-implementations-of-one-rule defect ADR-004 is about."* `bin/perry-conform`
   was deleted by TASK-261 / USER-910 along with the ledger, the three gate call
   sites and `bin/perry-migrate` — `bin/README.md § 183-195` records the removal.
   The function should stay (its other reason — that `main()` was the only way to
   reach `check_file` correctly — is still true), but its stated reason names a
   caller that cannot call it.

3. **`bin/perry-task`'s module docstring contradicts itself about what is
   canonical.** Line 43 reads *"Delete .perry/events.jsonl and Perry still
   works — **markdown is canonical**."* Lines 9-12 and 29-32 of the same
   docstring say the opposite and say it deliberately: *"the task RECORD, in
   perry/tasks.jsonl"* is slot 1, *"`BOARD.md`, RE-RENDERED from (1)"* is slot 3,
   and *"It used to be `BOARD.md` in slot (1) and there was no store (ADR-007,
   TASK-089). The board is rendered output now."* The docstring already carries
   one self-correction of exactly this kind two paragraphs earlier (*"this line
   said 'max(board ∪ journal ∪ events)' and has been wrong since ADR-007 made
   the store canonical"*), so the pattern is known; line 43 is the one that was
   missed. The surrounding claim — that the event log is derived and disposable
   — is still true; only its stated reason is now false.

None of the three affects a test or a runtime path.

## 11. What this row did not do

- It did not measure `viewer/parsers.py` (5,011 lines, imported by 12 modules
  under `bin/`). Where a call site's document handling happens there, the entry
  says `→ parsers.py` and only the call site's own lines are counted, so this
  census and `TASK-099`'s can be joined without double-counting. The affected
  call sites are `perry-lint § high_stakes_fragments`, `§ check_cross_file`'s
  hook band, `§ check_cross_file`'s linkage band, and `perry-task § board_sections`.
- It did not measure the other tools in `DESIGN-014`'s tables, or the tests.
- It changed no behaviour, deleted nothing, and edited neither tool.

## Appendix A — the coverage assertion

Read-only, stdlib only. It derives the four mechanical support sets from the
AST and the raw text, takes the complement as the code set, and asserts that
the authored regions in § 4 and § 5 cover that set exactly once. It fails
loudly on an overlap, on an unclaimed code line, and on a total that is not
`wc -l`. **The numbers in § 8 are this function's output, not a hand tally.**

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

A region may span support lines (a function's region runs from its `def` to the
line before the next construct, blank lines and comments included); those lines
are absorbed by the support sets and counted once, there. That is why the
region tables in § 4 and § 5 carry a separate **code** column — the region's
`(start, end)` span is larger than the lines it contributes to its category.

The per-statement split used for `commit()` and the seventeen `cmd_*` functions
(§ 5) walks each top-level statement's subtree for `ast.Call` names and
intersects them with two helper sets established by reading each helper:

```python
def split(fn_node, BOARD, STORE, default):
    for st in fn_node.body:
        names = {(c.func.id if isinstance(c.func, ast.Name) else c.func.attr)
                 for c in ast.walk(st)
                 if isinstance(c, ast.Call)
                 and isinstance(c.func, (ast.Name, ast.Attribute))}
        b, s = names & BOARD, names & STORE
        yield st.lineno, st.end_lineno, (
            "OBSOLETE" if (b and not s) else
            "TYPED"    if (s and not b) else default)
```
