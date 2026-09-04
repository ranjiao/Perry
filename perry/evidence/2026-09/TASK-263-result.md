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
`DESIGN-014 § 5.1`'s placement of it in category A.** 2,029 of its 3,790 code
lines — 54% — are TYPED / DETERMINISTIC: id minting, the store+journal
transaction with its recovery marker, the never-shrink invariant, schema-enum
validation and the refusals. Only 148 lines (3.9%) are AGENT-OWNED. The 1,110
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
| `2579-2594` | 3 | `register_section_shape` | absent|table|prose|foreign for a board section |
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
| `5330-5343` | 3 | `risk_section_shape` | table | bullets | foreign for `## Top risks` |
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
