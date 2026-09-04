# TASK-263 — V4 fresh-context review

> Reviewer: fresh-context V4 reviewer. Did not write the round; deciding PASS/FAIL.
> Branch: `review/task-263-v4`, cut from `main` at `1d3fd17`. No code changed by this review.
> Criteria: `perry/evidence/2026-09/TASK-263-spec.md` — `## Bound` and `## Verification`.
> Under review: `perry/evidence/2026-09/TASK-263-result.md` (1,158 lines), merged at `13fdb7e`.

**Verdict: PASS**, 8 of 8 criteria met, with one documentation defect recorded
in C2 that must be corrected but changes no number in the census.

---

## C0 — the two figures re-derived, not inherited — MET

The report claims `bin/perry-lint` and `bin/perry-task` are byte-identical at
`5601e45`, `2d2a06c` and `7f890f9`, verified by content hash. I re-derived this
rather than inheriting it, because it is what makes every line number in the
document usable.

    git show 5601e45:bin/perry-lint | shasum -a 256   873a7e82e2491f9f…
    git show 2d2a06c:bin/perry-lint | shasum -a 256   873a7e82e2491f9f…   identical
    git show 7f890f9:bin/perry-lint | shasum -a 256   873a7e82e2491f9f…   identical
    git show 5601e45:bin/perry-task | shasum -a 256   8666185c6b0344f0…
    git show 2d2a06c:bin/perry-task | shasum -a 256   8666185c6b0344f0…   identical
    git show 7f890f9:bin/perry-task | shasum -a 256   8666185c6b0344f0…   identical

The report's published prefixes (`dc673fff…0337`, `7e6679dc…32cb`) match neither
sha256 nor the git blob sha1, so I identified the algorithm rather than assume a
mismatch: they are **MD5**.

    md5 -q bin/perry-lint    dc673fffb08705739558900173900337    matches `dc673fff…0337`

Line counts, re-derived at `2d2a06c` and in the worktree:

    5144 bin/perry-lint      5144 claimed    ✓
    7851 bin/perry-task      7851 claimed    ✓

The commit correction in § 0 is sound: the round measured at `2d2a06c`, not the
`5601e45` the brief named, and the byte-identity is what makes that a
non-deviation rather than an excuse. Re-derived, it holds.

**Read-only confirmed.** Every TASK-263 commit
(`8959a80 01705294 2284471 a0c1fd6 96d07e8 4327785 7c1b3f5 cdda90e ff9964f 31473db c161dfc`)
touches `perry/evidence/2026-09/TASK-263-result.md` and nothing else. Neither
tool in scope was modified. Consistent with the Bound and with § 11.

## C1 — Appendix A reproduction from the published tables — MET

This is the round's own strongest claim and the first thing I ran. I did not
reuse any of the round's tooling. I wrote a harvester that:

1. extracts the **first `python` fence of Appendix A verbatim** and `exec`s it,
   so `check()` and `support_sets()` are the published functions, not my
   paraphrase of them;
2. parses every table row in §§ 4.1-4.5 and 5.1-5.5 out of the markdown,
   taking the category from the section heading (or the bucket column for the
   support tables);
3. feeds the harvested regions to the published `check()`.

One correction to my own instrument on the way: my first splitter split cells on
every `|`, including the markdown-escaped `\|`, and reported the two
`register_section_shape` / `risk_section_shape` rows as malformed. That was my
bug, not the document's — those rows carry `\|` correctly (see C7).

Result, honouring the escape:

    Appendix A loaded verbatim: 49 lines, functions ['ast', 'check', 'support_sets']
    rows parsed: 364   malformed-width rows: 0

    === bin/perry-lint ===
    regions harvested FROM THE DOCUMENT: 132
    code-column mismatches: 0
    zero-code-line regions: 0
      check() PASSED. total 5144 (file is 5144) CLOSES
        TYPED 649 · TRANSPORT 83 · AGENT 535 · OBSOLETE 972
        SUPPORT:cli-plumbing 485 · imports 50 · docstring 1000 · comment 1034
        SUPPORT:blank 335 · shebang 1

    === bin/perry-task ===
    regions harvested FROM THE DOCUMENT: 232
    code-column mismatches: 0
    zero-code-line regions: 0
      check() PASSED. total 7851 (file is 7851) CLOSES
        TYPED 2029 · TRANSPORT 40 · AGENT 148 · OBSOLETE 1110
        SUPPORT:cli-plumbing 432 · imports 31 · docstring 2104 · comment 1469
        SUPPORT:blank 487 · shebang 1

    OVERALL: REPRODUCES

Every figure in § 8 reproduces exactly from the document's own published tables.
132 + 232 = **364 regions**, matching § 1c. The per-row assertion the round
asked for — each published `code` column against what the checker independently
computes for that row's span — comes back **0 mismatches on both files**, and
**0 zero-code-line regions**, so Fault 1's failure mode is absent from the
filed document.

Region counts stated in the § 5 headings also check out exactly: TYPED 117,
TRANSPORT 2, AGENT 9, OBSOLETE 91.

### The closure is load-bearing — negative control

Closure is only evidence if the checker can fail. I perturbed the harvested
region list four ways:

| perturbation | `check()` |
|---|---|
| drop one region (lint) | caught — `28 unclaimed code lines: [4345, 4362, …]` |
| overlap two regions (task) | caught — `overlapping regions: [(1625, …)]` |
| shrink a region by 1 line, end on a **blank** line | **not caught** |
| shrink a region by 1 line, end on a **code** line | caught — `1 unclaimed code lines: [2704]` |
| drop the last 3 regions (task) | caught — `188 unclaimed code lines` |

The one miss is by design and the document states it: a region may span support
lines, which the support sets absorb and count once. Shrinking past a *code*
line is caught. The checker is real.

I also confirmed the limit the round asserts about it: **relabelling one
region's category leaves `check()` passing at 5,144.** Closure is blind to
misclassification. That is exactly why the round's warning that "a clean sum is
not proof" is correct, and why C2 below is the substance of this review.

## C2 — by call site, never by grep over a name — MET, with a defect recorded

The classifications are genuinely by call site. I verified this three
independent ways by opening the code, not by trusting § 1.

**The showcase pair holds.** `parse_depends` (`593-617`, OBSOLETE) splits a
`Depends on` *cell* on `_DEPENDS_SPLIT`, strips handles and dedupes.
`store_depends` (`618-622`, TYPED) is
`{r["id"]: list(r.get("depends_on") or []) for r in records}` over the typed
records. Four characters apart in the name, adjacent in the file, opposite
categories, and correctly so.

**`check_file` splits eight ways, not four.** § 1's first demonstration
understates itself. The harvested regions for one function span all four
categories:

    813-821   TRANSPORT  read the whole body, dispatch on declared format
    822-832   TYPED      line count vs the schema's tier cap
    833-843   OBSOLETE   intake_rows(raw) counted out of BOARD.md
    844-852   TYPED      the plain over-cap finding
    853-859   AGENT      required_at_status: `Status:` out of design/*.md
    860-900   OBSOLETE   required-heading presence over rendered state files
    901-928   AGENT      header_fields: `Name: value` out of a document body
    929-1233  OBSOLETE   the table pass over BOARD/OKR/phase/config renders

**The mechanical auto-split is exact.** § 5 predicts `cmd_add` comes out as
`3370-3448` TYPED, `3449-3450` OBSOLETE, `3451-3511` TYPED, `3512-3519`
OBSOLETE, `3520-3562` TYPED. The harvested regions match verbatim, and opening
the two OBSOLETE bands shows they are precisely the board-touching statements —
`target_section` at 3449, and `widen_target_section` / `ensure_section` /
`append_row` at 3512-3519 — with store and validation work either side. That is
a split at the call site, done mechanically, not a function rounded to one label.

### Defect: § 1's second demonstration contradicts the census's own tables

§ 1 argues the method is not a grep with two demonstrations. The second reads:

> Conversely `perry-task § heading_matches` and `§ norm` carry no regex and no
> suggestive name, and are AGENT-OWNED: they answer "is this heading that
> heading?" over prose.

**Neither is AGENT-OWNED in this census.** Both are OBSOLETE in the § 5.4 table:

    perry-task  1297-1309  OBSOLETE  norm             the header-cell fold
    perry-task  1544-1579  OBSOLETE  heading_matches  does this line open the `## ` section called name

I read both to decide which is right, and **the tables are right, the prose is
wrong.** `norm` folds a header cell through `squash` and the `_ALIASES` table
built from the schema's declared i18n column spellings — a lookup against a
declared, bounded set. `heading_matches` tests `line.startswith("## ")` and
prefix-matches `squash(head)` against `heading_spellings(name)`, again a
declared set, with an alphanumeric boundary guard. Neither puts a question to an
unbounded value space; neither is AGENT-OWNED under the § 2 test the report
itself states. OBSOLETE is the coherent placement, since both exist to read the
board projection.

Assessment: this is a **documentation defect in the argument, not an error in
the census**. It changes no number — § 8 reproduced exactly from the tables — and
the "not a grep" claim survives on demonstration 1 plus the
`parse_depends`/`store_depends` pair, both of which I verified independently.
But it sits in the one section a reader consults to decide whether to trust the
method, so it must be corrected. Had the tables matched the prose instead, the
classification would have been wrong; they do not.

## C3 — the four categories plus support sum to each file's line count — MET

Independently reproduced under C1. `649 + 83 + 535 + 972 + 535 + 2,370 = 5,144`
and `2,029 + 40 + 148 + 1,110 + 463 + 4,061 = 7,851`, both from the published
tables through the published checker, with no overlap and no unclaimed code
line. Remainder 0 on both files, as the spec requires.

## C4 — every attribution reproducible from concrete line ranges and callers — MET

Every one of the 364 rows carries an explicit `(start, end)` span, a code-line
count that I verified against the file, an owning function and a call-site note.
§ 6 supplies downstream callers per destination group. § 4.5 and § 5.5 publish
the authored support regions, which is what makes the region list reconstructable
in full from the document rather than only summarised by it — the property C1
depends on.

## C5 — ambiguous regions listed explicitly; mixed functions split — MET

Nine ambiguities in § 7, and they are genuine rather than a bucket for hard
cases. The test I applied: does each name the alternative reading *and* quantify
what moves? All nine do.

- § 7.1 gives the fan-out of `check_file` counted by enumerating
  `schema § files[].tables`, and offers the exact re-split (23 lines out,
  25 lines in).
- § 7.3 flags its own largest TYPED region (`check_frontmatter`, 123 lines) as
  the most consequential of the nine and says which way it would move.
- § 7.4 concedes the one place a legitimate operation is counted in a condemned
  category, and gives the reason (a dependency, not the operation).
- § 7.5 concedes the cadence family points at a store that does not exist.

That is the opposite of absorption. Mixed functions are split rather than
rounded: `check_file` eight ways, `cmd_add` five, `resolves_somewhere` three,
`verdict_citations` two.

I independently verified § 7.1's load-bearing claim, since it supports the
single largest OBSOLETE region (191 lines). Enumerating
`schema/state-schema.json § files[].tables`:

    board   BOARD.md            tables=5
    okr     OKR.md              tables=2
    phase   phase/NNN-*.md      tables=1
    config  .perry/config.md    tables=1
    TOTAL table specs: 9

Nine specs, four target files, all four store-backed. "No table spec in the
schema whose target is not store-backed" is correct, so those 191 lines are
OBSOLETE without a judgement call.

## C6 — every non-typed entry names a concrete destination — MET

Eleven destination groups. I checked mechanically that every non-typed region's
owner is named somewhere in § 6: **120 distinct non-typed owners, 0 unnamed.**
(My matcher initially flagged three `_empty_*_drift_stats` functions; § 6.2
names them collectively as "the three `_empty_*_drift_stats` (9)" — a false
positive on my side.)

Each group carries a destination and a deletion dependency. I read the
AGENT-OWNED groups closely, since a vague destination would be easiest to hide
there, and none is "keep the regex but make it better":

- § 6.6 → the V4 review workflow, with the typed half named that survives
  (`tasks.jsonl § verification` enum, `## Bound` presence) and the deletion
  dependency stated (`=== VERDICT ===` must stop being the transport).
- § 6.7 → a knowledge-card store on the `risks.jsonl` pattern, four named
  provenance fields typed, body left unparsed.
- § 6.8 → the document-generating agent, quoting `ADR-007 § 5b` by name, plus a
  carve-out kept typed (`hook.md`'s escalation list → `high_stakes: [string]`
  in `.perry/config.jsonl`).
- § 6.9 → a field split on `ADR-007` decision 3's own `By when` precedent,
  naming three concrete splits.
- § 6.10 → the writing agent, citing TASK-330's removal of two of the same
  function's four checks on 2026-09-03.

Minor blemish, not a criterion failure: `check_summaries`' shape band
(`1801-1854`, 30 lines) is listed in **both** § 6.9 and § 6.10, so the owner
tallies in § 6's preamble double-count it. It is an overlap, not a gap; every
non-typed entry still names a destination, and line counts come from the tables,
not from § 6.

## C7 — the recorded instrument fault is corrected, not just confessed — MET

This was the specific thing to distrust: § 1b confesses that two rows carried
unescaped `|`, rendered as 7-cell and 6-cell rows in a 4-column table, and
silently dropped six call sites. The question is whether the document I am
reading is fixed or merely apologetic.

It is fixed. The two rows at document lines 627 and 666 read:

    | `2579-2594` | 3 | `register_section_shape` | `absent` \| `table` \| `prose` \| `foreign` for a board section |
    | `5330-5343` | 3 | `risk_section_shape` | `table` \| `bullets` \| `foreign` for `## Top risks` |

Both pipes are escaped. My harvester confirms the consequence rather than the
appearance: honouring `\|`, **0 malformed-width rows across all 364**, and the
six previously-dropped code lines — `2579`, `2591`, `2592`, `5330`, `5340`,
`5341` — are claimed, with `check()` reporting no gap. With the escape *not*
honoured, I reproduced the original failure exactly (`6 unclaimed code lines`
at those six line numbers), which confirms the confession describes the real
defect and the fix is the thing that closes it. `ff9964f` is the commit.

The unescaped copies that remain at document lines 126-127 are inside § 1b's
indented code block, quoting the old broken rows deliberately. Correct.

## C8 — the headline conclusion (OBSOLETE 3x AGENT-OWNED) — MET, and robust

The claim that will steer real work: OBSOLETE 2,082 vs AGENT-OWNED 683, "larger
by 3:1", therefore "most of the removable code is deletable without an agent
being involved at all." The failure mode to hunt is a region filed OBSOLETE that
actually needs a human-or-agent judgement to replace, which would make the work
look cheaper than it is.

**I opened thirteen regions across both files and all four categories and did
not find one.** The OBSOLETE placements that carry the most weight are sound:

- `Board` (`771-1243`, 259 lines, the largest single OBSOLETE region) is
  line-level `BOARD.md` manipulation — locate a `## ` section, parse the table,
  find a row by its id cell, insert/replace/remove lines, join back. Every fact
  it reconstructs is typed in `tasks.jsonl`. Confirmed by reading
  `store_records` and `bin/perry_store.py § 530-600`: the board-parse is the
  derivation direction, `perry_store.render` the replacement.
- `ensure_risk_table` (`5399-5488`, 39 lines) was my best candidate for a hidden
  judgement, since it converts free-text *bullets* into typed table cells. It is
  not: the bullet text is copied into `Risk` byte-for-byte, `Opened` is left
  empty rather than stamped, and `Status` derives from two mechanical markers
  (`~~strikethrough~~`, `**RESOLVED`). Deterministic. OBSOLETE holds.
- `check_file`'s table pass (`929-1233`, 191 lines) — verified store-backed by
  schema enumeration under C5.
- `norm` and `heading_matches` — bounded lookups against declared spelling sets,
  as argued in C2.

The categories on the other side are also right where I checked them:
`check_no_user_claim` (`3682-3712`, AGENT) genuinely asks an unbounded prose
question — does this sentence assert what a person did; `check_role_cards`
(`1979-2075`, AGENT) tests a heading against an open family of spellings
(`## Steps`, `## Procedure`, `## How to`) that no closed set can enumerate;
`append_block` (`3173-3199`, TRANSPORT) locates the last `## heading` and
inserts without interpreting; `check_file` `813-821` (TRANSPORT) reads the body
and dispatches on the declared format; `check_frontmatter` (`459-610`, TYPED)
parses YAML frontmatter — a typed serialization — through `P.parse_yaml_subset`
and validates against typed field rules.

**Sensitivity analysis.** I re-derived the ratio under every alternative the
document itself discloses, plus my own C2 finding, stacked in the direction most
hostile to the claim:

| reading | OBSOLETE | AGENT | ratio |
|---|---:|---:|---:|
| as filed | 2,082 | 683 | **3.05:1** |
| § 7.1 both swaps | 2,084 | 681 | 3.06:1 |
| § 7.2 lexer by today's callers → OBSOLETE | 2,113 | 652 | 3.24:1 |
| § 7.4 `commit` band → TYPED | 2,067 | 683 | 3.03:1 |
| § 7.5 cadence out of scope entirely | 1,994 | 683 | 2.92:1 |
| § 7.3 `check_frontmatter` TYPED → AGENT | 2,082 | 806 | 2.58:1 |
| § 7.3 + 7.4 + 7.5 together (worst disclosed case) | 1,979 | 806 | 2.46:1 |
| worst case **plus** my C2 finding read the other way | 1,930 | 855 | **2.26:1** |

The conclusion is not resting on a generously drawn boundary. Under every lever
the round discloses, pulled simultaneously against itself, OBSOLETE still
exceeds AGENT-OWNED by more than 2:1, and the qualitative claim — most removable
code needs no agent — survives intact. The literal "3:1" is exact as filed
(2,082/683 = 3.05) and degrades gracefully, and the document names each lever
itself rather than leaving me to find them.

## Mutation discipline

This row changed no code, so behavioural mutation does not apply — there is no
behaviour to break and no test whose green could be false. I planted no
mutations in `bin/`, and the tree is clean.

What holds the document instead is its self-verification, and I tested the
instrument rather than inheriting its verdict: the published `check()` was
`exec`'d verbatim from Appendix A rather than reimplemented; the regions were
harvested from the published tables rather than from the round's working list;
and the checker was shown to fail on a dropped region, an overlap, a shrunk
code-ending region and a truncated list, while passing a relabelled category.
That last result is the boundary of what closure can prove, and it is why the
thirteen opened regions in C8 — not the arithmetic — are the evidence behind
this verdict.

## Known reds not attributable to this row

`tests/test_contract_key_parity.py`'s two anti-vacuity controls decay with
wall-clock time (`bin/perry-task:6303`, a 4-hour idle threshold against Perry's
own live board) — **TASK-335**. Not this row's; this row touches no test.

## Verdict

**PASS.** 8 of 8 criteria met.

Every written criterion in `## Verification` is satisfied, and the two figures I
was told to re-derive rather than inherit both hold. The document does what it
claims: 364 regions harvested from its own published tables, fed to its own
published checker, reproduce § 8 exactly on both files with zero code-column
mismatches. The instrument fault it confesses is corrected in the filed
document, not merely admitted. The headline conclusion survives every
sensitivity the round discloses, stacked together.

**One correction required before this census is cited as method:** § 1's second
"why this is not a grep" demonstration names `perry-task § heading_matches` and
`§ norm` as AGENT-OWNED; both are OBSOLETE in § 5.4, and the tables are the ones
that are right. Fix the prose, not the classification. It changes no number.

**One blemish worth tidying:** `check_summaries`' shape band `1801-1854` is
listed as an owner in both § 6.9 and § 6.10, double-counting it in § 6's
preamble tallies.
