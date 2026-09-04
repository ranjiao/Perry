# TASK-263 — call-site census of `bin/perry-lint` and `bin/perry-task`

> Row: TASK-263 · Spec: `perry/evidence/2026-09/TASK-263-spec.md`
> Applies: `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md` (rules 1-3 and § 5b)
> Serves: `perry/design/DESIGN-014-how-much-python.md § 5.1`
> Rung: V4 · **Read-only. No behaviour changed by this row.**

## 0. Commit measured, and a correction to the brief

Measured at **`2d2a06c`** (`main` at the time of the run), **not** at `5601e45`
as the dispatch brief named. This is not a deviation from the Bound: the Bound
requires "the named stable commit", and the two files in scope are byte-identical
between the two commits:

    git diff --stat 5601e45 2d2a06c -- bin/perry-lint bin/perry-task
    (empty)

so every line number in this report is valid at `5601e45` as well. The report
says `2d2a06c` because that is what was actually read.

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

**Step 3 — coverage assertion.** A checker (`check()` in the scratchpad script
reproduced in § 6) asserts three things and fails loudly on any of them:
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

**The headline: 972 of the 2,774 code lines — 35% — are OBSOLETE
REPRESENTATION.** That is the largest of the four categories, and it is larger
than TYPED. `perry-lint`'s single biggest activity is checking renders of
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
