# TASK-323 — V4 review, round 2

> Reviewer: independent V4 round. Did not write the census, did not write round 1.
> Criteria: `perry/evidence/2026-09/TASK-323-spec.md`, including its `## Bound`.
> Under review: `main` at `7ea0bff`. Census `3a9b979`; bound script `1042ba6`;
> round-1 corrections `db12fa4`.

**Checkout.** This worktree branched from `d49964e`
(`chore: consolidate test suite and project state`) — the same base round 1 got,
~90 files behind `main`. Nothing under review is in my working tree. Every
artifact was reached through `git show main:<path>`; every measurement ran
against a `git archive main` copy in a scratch directory, re-`git init`ed so the
bound script's `git ls-files` domain step works. **All cited paths resolved.**
The live tree was never written to.

**Measurement point.** `main` was `7ea0bff` throughout. This is *later* than
every previous measurement — the census measured on `5720730`, the PMO
re-derived on `c7627cd`, round 1 measured on `5c76aa2`. Where a number below
differs from round 1's, I say so and give the reason.

**Result: PASS.** Both of round 1's blocking findings are fixed, and I verified
both from scratch rather than inheriting the correction. Every figure in the
`## Bound` is now exactly true of the delivered artifact at a commit no previous
round measured. Every `uncaught` row — the load-bearing half, the half a user
actually chooses against — reproduced under my own mutations with red controls.
One `caught` verdict is false and six more are true-but-mislabelled; I enumerate
that category in full below and file it as a follow-up row, because it moves no
number either reading depends on.

---

## 1 · The two edits to the criteria file: both describe the artifact

This was the round's assigned question, and it has a clean answer. `db12fa4`
touched exactly two files under review, with exactly two edits, and I read the
whole diff:

**Edit 1 — the census figure, `21 rows — 13 caught` → `20 rows — 12 caught`.**
I did not inherit this. Parsed straight out of
`main:perry/evidence/2026-08/TASK-067-finding.md`, splitting each row on
unescaped pipes and reading the verdict column positionally:

```
data rows 20   caught 12   uncaught 8   other 0
(every row exactly 5 columns)
```

**20 / 12 / 8.** The corrected figure is right and the original was wrong. The
edit states its own provenance in the file — the PMO copied the figure out of
the delivering agent's RESULT block and never counted the table.

**This edit is checkable and it moved toward the artifact, not away from it.**
Worth naming what it did *not* do: round 1's F3 argued the *demonstrable* census
is 19 rows / 11 caught. Quietly adopting that number would have been the bend —
absorbing a reviewer's proposed remedy into the bar so the bar matches whatever
survives. The correction states the delivered count instead and leaves F3 to be
argued on its merits. That is the right call.

**Edit 2 — the `ragged-row` exhibit.** The false quote stays in the body with a
dated blockquote under it that retracts it: *"That output is from a synthetic
fixture, not from the baseline the line names."* I checked all three of its
claims:

- *`perry/BOARD.md:12` is prose and no table has a 7-column header; the widths
  present are 3, 4, 6, 11 and 15.* Measured on the reviewed HEAD — the board's
  tables are 3, 15, 15, 11, 6, 6, 3, 4 cells wide. Line 12 is
  `> locked the same day. Every row cites its design phase…`. **True**, and the
  stated width set is exactly right.
- *The claim was reproduced at 16-vs-15.* Reproduced independently — see § 3.
- *`ragged-row` fires only inside a schema-recognised table.* Reproduced
  independently — see § 3.

**This is an errata, not a relaxation.** It retracts an exhibit, records the
true reproduction, and then *adds a limitation that makes the artifact's own
claim weaker* — the backstop reading (B) leans on turns out not to fire outside
a recognised schema. An edit written to bend a bar does not volunteer a new fact
that cuts against the reading the project's own precedent favours. Neither edit
removes a verification clause, weakens a threshold, or narrows the population.

**Verdict on the assigned question: both edits are descriptions of the delivered
artifact.** The `## Bound` having been written after delivery remains a real
structural weakness of this row's process, and the spec says so itself. What
saves it here is that every figure in it is now mechanically checkable and I
checked all of them.

---

## 2 · Every figure in the `## Bound`, re-derived at `7ea0bff`

Nothing in this table is inherited from round 1 or from the correction.

| `## Bound` states | I measured | |
|---|---|---|
| `89 members` | 89 | ✓ |
| `27 W1 · 18 W2 · 38 R1 · 6 R2` | 27 / 18 / 38 / 6 | ✓ |
| `last element viewer/tables.py:280` | `W1 viewer/tables.py:280 check_cell()` | ✓ |
| 8 dropped by exclusion | `89 member(s); 8 excluded` | ✓ |
| `Census: 20 rows — 12 caught, 8 uncaught` | 20 / 12 / 8 | ✓ |
| `Shapes: 13 rows — 4 red controls, 9 green` | 13 rows, 4 red, 9 green, 4 labelled `control` | ✓ |
| 5 bash tools contribute 0 members | 5 bash tools, all `#!/usr/bin/env bash` | ✓ |
| checked for `cut -d'\|'` / `awk -F'\|'` / `IFS='\|'` | 0 / 0 / 0 hits | ✓ |

The size is stable across three commits' worth of drift (`5720730` → `c7627cd` →
`5c76aa2` → `7ea0bff`), which is itself evidence the rule is measuring a real
property rather than a snapshot.

### 2a · Attacking the domain, which round 1 did not

Round 1 attacked the member *rule* and could not move the 89. I attacked the
**domain** instead — the bound's closure argument is "every tracked Python file
except `tests/`", and if a tracked Python file that can build a row sits outside
it, the set is closed over the wrong tree.

```
tracked files             820
tracked python files      147
IN domain                  21   (the 21 the script walks)
OUT of domain             126   (every one of them under tests/)
```

All 126 excluded files are under `tests/`, which the rule names explicitly
(*"a fixture is not a write path"*). The 159 row-shaped constructs I found
outside the domain are all in `tests/` — fixtures and the header-rule harness's
own prose about `.split("|")`. The only non-Python tracked executables are the
five bash tools, already accounted for. **The domain is closed and it is the
right domain.**

Two domain members are worth naming because nobody has: the bound includes
`templates/knowledge-base/bin/kb-lint` and `templates/ops/bin/deliverable-lint`
— files Perry ships *into other projects*. They contribute no members, so
nothing changes, but a bound over "this repository" that silently includes
Perry's outbound templates is a fact the next round should know it inherited.

---

## 3 · The `ragged-row` schema limit is real — reproduced with my own control

Assigned explicitly. Baseline on an untouched archive copy:
`0 error(s), 16 warning(s)`, 0 `ragged-row` — byte-identical to the census's
stated baseline, at a commit two ahead of where the census measured it.

**A · w4–w7 into the real `## P0` table (recognised schema, 15-column header):**

```
--- Next action = 'audit | then ship' ---
  w4  16 cell(s) vs header 15 -> 2 error(s), 17 warning(s)  ragged=1
     ✗ perry/BOARD.md:24 [ragged-row] row 'TASK-900 | T | me | not_started |
       audit | then ship | — | V4' has 16 cell(s) but its header has 15
  w5 / w6 / w7  identical
  render_row  15 cell(s) -> 0 error(s), 17 warning(s)  ragged=0

--- Next action = 'need one\n\nneed two' ---
  w4-w7  5 cell(s) vs header 15 -> 1 error(s), 18 warning(s)  ragged=2
  render_row  REFUSED: cell 4: contains a line break
```

**B · the identical rows in a section the schema does not recognise** — a
`## Backstop probe` heading, a well-formed 7-column header, four 8-cell rows:

```
-> 0 error(s), 17 warning(s)   ragged=0
```

**C · my control, which B needs to mean anything** — the same 8-cell row placed
inside the recognised `## P0` table instead:

```
-> 3 error(s), 17 warning(s)   ragged=1
   ✗ perry/BOARD.md:24 [ragged-row] row 'TASK-900 | T | me | Doing | audit |
     then ship | — | V4' has 8 cell(s) but its header has 15
```

Same rows, same widths, same file. Recognised section: reported. Unrecognised
section: silent. **The limit recorded in the correction is real**, and B without
C would not have shown it — an 8-cell row producing 0 errors is equally
consistent with "the check is schema-gated" and "my plant was malformed". It is
schema-gated.

This is the single most consequential fact the round-1 corrections added, and it
is recorded in the right place: it is load-bearing against reading (B), whose
entire backstop is this check, and `add --group` lets a project file work under
headings the schema does not know.

---

## 4 · The uncaught rows all reproduce, and generalise further than claimed

I cut **every** separator row in `perry/BOARD.md` by one cell, one at a time,
restoring between each:

```
 line  hdr  sep  planted  verdict
   18    3    3        2  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE
   23   15   15       14  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE   <- the census's own plant
   29   15   15       14  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE
  102   11   11       10  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE
  152    6    6        5  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE
  158    6    6        5  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE
  179    3    3        2  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE
  184    4    4        3  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE
```

All eight invisible, all byte-identical to the clean baseline. **Three red
controls** — data rows in three different tables cut the same way:

```
  data row line  24 cut 15 -> 14: ('1 error(s), 16 warning(s)', 1, 1)
  data row line  30 cut 15 -> 14: ('1 error(s), 16 warning(s)', 1, 1)
  data row line 103 cut 11 -> 10: ('1 error(s), 16 warning(s)', 1, 1)
```

**One thing neither the census nor round 1 tried: widening.** A separator cut
*narrow* is invisible; a separator made one cell *too wide* is also invisible:

```
  sep line 23  15 -> 16 cells: ('0 error(s), 16 warning(s)', 0, 0)
```

That matters because `bin/perry-goals:322`'s own comment records the shipped bug
as a *narrow* separator (7-cell header, 6-cell separator). The blind spot is
two-sided. This strengthens the census's row; it is not a defect in it.

My separator line numbers are 152/158/179/184 where round 1 reported
151/157/178/183 — `perry/BOARD.md` moved by one line between `5c76aa2` and
`7ea0bff`. Board drift, not a discrepancy.

All nine `uncaught` census citations resolve at `7ea0bff` and say what the
census says they say — I opened every one, including `perry-task:7431`
(`if isinstance(_v, str) and _v.strip() == exc.value:`, still true) and the
seven hand-built separator constructors.

---

## 5 · The 13 shapes and the read table reproduce exactly

All 13 planted as real files under `bin/` in an archive copy, `__pycache__`
cleared and 1.05 s slept past the whole-second boundary before each run, both
detector tests run against each, plants removed between:

```
 shape   expect    READ guard   WRITE guard   offenders reported
    w1  control         green           RED   ['bin/plant-w1:3']
    w2  control         green           RED   ['bin/plant-w2:3']
    r1  control           RED         green   ['bin/plant-r1:3']
    r6  control           RED         green   ['bin/plant-r6:3']
    w4  w5  w6  w7        green         green   —
    r2  r3  r4  r7  r8    green         green   —
no plants present -> READ green  WRITE green   (before and after)
```

Nine green, four red. (`:3` not `:2` because my plants carry a shebang line;
the census's `:2` is right for its own plants.)

The read table reproduces character for character on a row `render_row` itself
wrote. **My first attempt disagreed with the census — and the census was
right.** I had dropped the `.strip("|")` that the r1/r6 shape definitions carry,
which changes the counts. Re-run with the shapes as the census actually defines
them:

```
row: | TASK-067 | T | me | in_progress | audit \| then ship | — | V4 |

  split_row (choke point)  -> 7 cells   [4]='audit | then ship'
  r2 .split("|", 6)        -> 7 cells   [4]='audit \'      <- RIGHT COUNT, wrong content
  r3 re.split(r"\|")       -> 8 cells   [4]='audit \'
  r4 SEP constant          -> 8 cells   [4]='audit \'
  r7 .rsplit("|")          -> 8 cells   [4]='audit \'
  r8 .partition("|")       -> 3 cells
```

7 / 7 / 8 / 8 / 8 / 3, exactly as claimed. The `r2` argument — a count-based
backstop is structurally incapable of covering the read side — holds.

---

## 6 · Both corrections to the record are true, and correction 1 is understated

**Correction 1 — `bin/perry-decide:332` is a third, weaker spelling.** The line
is `if isinstance(_value, str) and len(_value.splitlines()) > 1:`. Run on an
archive copy:

```
  --title 'ship\n\nit'      -> rc=1  refused, nothing written
  --title 'ship it\n'       -> rc=0  wrote ADR-018
  --title 'ship it\r'       -> rc=0  wrote ADR-019
  --title 'ship it '   -> rc=0  wrote ADR-020
```

ADR-018 carries the stray blank line the census describes, fields intact.
**ADR-020 is worse than the census says**, and neither the census nor round 1
recorded it — the U+2028 survives *verbatim into the H1 text*:

```
  ADR-018:  1 '# ADR-018 — ship it'   2 ''   3 ''   4 '> Status: active'
  ADR-020:  1 '# ADR-020 — ship it '    2 ''   3 '> Status: active'
```

So the blast radius is not only "one stray line"; on the other ten boundaries a
line-separator character lands inside a heading. Strengthens the correction.

**Correction 2 — the writers `.strip()` before they check.** Confirmed, and as
round 1 said, the census understates the scope. Every one of these is accepted
with the character silently dropped:

```
  render_row trailing LF / CR / CRLF / U+2028 / U+2029 / VT / FF / NEL /
             FS / GS / RS   -> ACCEPTED '| a | ship it |'   (11 of 11)
  render_row interior LF    -> REFUSED  cell 1: contains a line break
```

The census still says *"a trailing newline is the **one** line break this module
strips instead of refusing."* It is eleven. Round 1 flagged this; `db12fa4` did
not correct it because round 1 filed it as part of a non-blocking finding. **It
is a false sentence still standing in the artifact** — recorded here as F3
below. It is in the prose of a "correction to the record", not in a census row
and not in the `## Bound`, and the ordering it describes — strip before check —
is the finding and is correct.

---

## 7 · Findings

### F1 (new row) · What `caught` means in this census — the full enumeration

Round 1's F3 named one `caught` row whose cited check cannot fire. The brief
asked me to enumerate the category rather than stop at the one instance. I did,
across all 12. **The word `caught` is doing four different jobs:**

| | census row | claimed `by what` | does a named check fire on a plant of that shape? |
|---|---|---|---|
| 1 | `tables.py:151` | `line_break_at`, 151-155 | **YES** — raises at `tables.py:153` |
| 2 | `tables.py:156` | round-trip clause, 156-161 | **NO — cannot, for any cell value** |
| 3 | `tables.py:180` | `check_cell`, 180-182 | **YES** — raises at `tables.py:181` |
| 4 | `tables.py:236` | `splice_cell`, 236-239 | **YES** — raises at `tables.py:236`, but on an out-of-range *index*, not a cell value |
| 5 | `tables.py:141`, `:280` | "it *is* the check" | n/a — identity claim, no check fires |
| 6 | `perry-lint:887` | "never reaches a state file" | n/a — non-membership claim |
| 7 | `parsers.py:2360` | "never reaches a state file" | n/a — non-membership claim |
| 8 | `38 × R1` | `split_row` + `test_no_tool_splits_a_row_on_a_raw_pipe` | **PARTIAL** — 2 of 7 regression spellings |
| 9 | `perry-knowledge:242`, `perry-lint:1708`, `:1958` | "not a row split" | n/a — non-membership |
| 10 | `perry-lint:817` | "not a row split" | n/a — non-membership |
| 11 | `parsers.py:2554` | "not a row split" | n/a — non-membership |
| 12 | `parsers.py:3059` | "not a row split" | n/a — non-membership |

**Row 2 is the only false one, and round 1's F3 replicates exactly.** My own
harness, my own alphabet, my own seed: **216,275 planted inputs** — 16,275
exhaustive over a 25-symbol adversarial alphabet at widths 1–3, plus 200,000
random rows over a 42-symbol alphabet at widths 1–4 — and **zero reached
`tables.py:156-161`**. Every refusal in the random set (32,849 of them)
attributed to `tables.py:153`, i.e. `line_break_at`. The only input that reaches
the clause is `render_row([])`:

```
  render_row([])       -> REFUSED tables.py:160  'cell 0: does not read back as itself'
  render_row([''])     -> ok      '|  |'
  render_row([' '])    -> ok      '|  |'
```

**Row 8 measured.** I mutated nine real R1 call sites — one per file — into each
of seven regression spellings and asked whether the *named* guard reports the
site:

```
site                     bare .split("|")  .split('|')  maxsplit  re.split  SEP  .rsplit  .partition
bin/perry-diagnose:509         RED            RED        green     green   green  green    green
bin/perry-explain:417          RED            RED        green     green   green  green    green
bin/perry-goals:318            RED            RED        green     green   green  green    green
bin/perry-lint:258             RED            RED        green     green   green  green    green
bin/perry-state:256            RED            RED        green     green   green  green    green
bin/perry-task:793             RED            RED        green     green   green  green    green
bin/perry_store.py:97          RED            RED        green     green   green  green    green
viewer/parsers.py:806          RED            RED        green     green   green  green    green
```

Two of seven, at every site, reported by file and line. This is **disclosed** —
the artifact's own § *The two readings* says the detector has four blind spots
on the read half and the shapes table demonstrates all five spellings green — so
row 8 is not a false claim, but "caught, guarded by `<named test>`" reads
stronger than a guard covering two spellings out of seven.

**Rows 5–7 and 9–12 (seven rows) are `caught` by non-membership**, not by a
check firing. I verified each: `perry-lint:887`'s `" | ".join(row)[:60]` does
execute and its output does land only in a console `Finding` — I watched it
produce the truncated row text inside my own `ragged-row` findings in § 3 —
and `parsers.py:2360`'s `alt` is consumed by `re.search` two lines later as an
alternation. The four R2 read rows are token-list splits, a value normaliser, a
`Status:` field and an ADR header line. All true.

**Why this is a new row and not the verdict.** The spec's verification clause 2
sets a bar these seven rows do not meet as written, and the census's own
definition of `caught` does not cover them. But the `by what` column names the
reason for every one of them in plain words — no reader is misled about *why* a
row is marked caught — and, decisively, **the accounting that carries the
decision does not use this column.** § *The two readings* decomposes reading (A)
as "27 W1 already refusing + 7 separator builders + `perry-decide:332` +
`perry-task:7431`", which is correct and which I verified. Nothing a user
chooses against moves if row 2 is re-marked and rows 5–12 are relabelled.

**Remedy, one line each.** Re-mark row 2 as `unreachable by any cell value;
fires only on render_row([])`, and split the verdict column into `caught` /
`not an instance` so the twelve stop meaning four different things.

### F2 (new row) · `perry-decide` lets a line-separator character into an ADR heading

§ 6. `--title 'ship it '` is accepted and the character lands verbatim in
the H1. The census's blast-radius claim ("one stray line") is measured on `\n`
only. Belongs with the `perry-decide:332` third-spelling finding, which both
readings already leave open.

### F3 (nit, uncorrected from round 1) · Two false counts still standing

- *"a trailing newline is the **one** line break this module strips"* — it is
  eleven (§ 6). Round 1 said so; `db12fa4` corrected only the two blocking
  findings.
- *"the one hit is a shell pipeline"* — a row-shaped-`echo` grep over the five
  bash tools returns **three**: `bin/perry-codex-preflight:78` (a pipeline) and
  `bin/perry-dispatch-limit:309` and `:373`, both the prose message
  `codex | claude-subagent | opencode-subagent`. None is a table row, so the
  `0 members` conclusion is untouched.
- `bin/perry-lint:252-256` for a block that is 253-256 (line 252 is
  `s = line.strip()`). Confirmed again at `7ea0bff`.

---

## 8 · What reproduced without qualification

Recorded so a third round does not re-spend it: the bound's size, class split,
last element and exclusion count at `7ea0bff`; the 21-file domain and its
closure; the census table's 20 / 12 / 8; the shapes table's 13 / 4 / 9; all 13
shape verdicts with their four red controls; the read-side split table
character for character; all eight separator rows invisible when cut, with
three data-row red controls, plus widening also invisible; every one of the 22
`file:line` citations I opened resolving at `7ea0bff` to what it claims; both
corrections to the record; the `ragged-row` reproduction at 16-vs-15 and the
schema-recognition limit with its own control.

The census names both readings and picks neither. **I have not picked one
either** — that is out of the bound and it is the user's call.

---

## 9 · Safety

Every plant, every write and every tool run happened on a `git archive main`
copy under the session scratch directory. The live checkout was never written
to; no write-side Perry tool was run against the project under review; nothing
was pushed, no PR opened, no branch merged, `main` untouched. `setup` was never
run. `.perry/hook.md § High-stakes operations` was read first and nothing on it
was performed — in particular no `rm -rf`/`rm -f` against the project, no
`origin`, no `git push`. Board files inside the scratch copy were restored and
asserted byte-identical after every mutation sweep, and the scratch tree's own
`git status --porcelain` showed no source modifications (only the three ADRs my
`perry-decide` plants created, inside the scratch copy). This review document is
the only file added, on `review/task-323-v4-r2` in my own worktree.

> **One constraint tension, reported rather than routed around
> (`review-constraints.md § Report the blocker`).** That file says a reviewer
> does not commit; this round's brief instructs me to commit the review on
> `review/task-323-v4-r2`. I followed the brief, because the commit contains
> only this review document in my own isolated worktree and touches nothing
> under review. Flagging it so the difference is a decision on the record and
> not a drift.

```
=== VERDICT ===
task: TASK-323
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-323-spec.md
checked: Re-derived every ## Bound figure at main 7ea0bff (later than the census's 5720730, the PMO's c7627cd and round 1's 5c76aa2) on a git-archive copy re-git-init'ed for the script's git ls-files step — 89 members, 27 W1 / 18 W2 / 38 R1 / 6 R2 counted per class, last element viewer/tables.py:280, 8 exclusions. Counted the census table myself by splitting each row on unescaped pipes and reading the verdict column positionally: 20 data rows, 12 caught, 8 uncaught, every row exactly 5 columns — the corrected figure is right, the original was wrong. Counted the shapes table: 13 rows, 4 red, 9 green, 4 labelled control. Read the full db12fa4 diff and confirmed it touched only the two files under review with only the two claimed edits, neither removing a verification clause, weakening a threshold or narrowing the population. Attacked the bound's DOMAIN rather than its member rule: enumerated all 820 tracked files, 147 Python, 21 in domain, 126 out — all 126 under tests/, and all 159 row-shaped constructs outside the domain are in tests/; noted the domain silently includes two outbound templates (kb-lint, deliverable-lint). Enumerated the 'verdict attributed to a check that cannot fire' category across ALL 12 caught rows, not just round 1's one: fuzzed the tables.py:156 round-trip clause with 216,275 planted inputs (16,275 exhaustive over a 25-symbol adversarial alphabet at widths 1-3, plus 200,000 random over 42 symbols at widths 1-4) with zero firings, all 32,849 refusals attributing to tables.py:153, and only render_row([]) reaching the clause; traced the raising line of each peer guard (151->153, 180->181, 236->236); mutated nine real R1 call sites, one per file, into each of seven regression spellings and measured that the named guard test_no_tool_splits_a_row_on_a_raw_pipe reports 2 of 7 at every site; opened and verified all seven non-membership rows including watching perry-lint:887 emit its truncated row text inside my own ragged-row findings. Cut every one of the 8 separator rows in perry/BOARD.md by one cell, one at a time with restore between, with three data-row red controls in three different tables, and additionally WIDENED a separator (also invisible — untried by the census and by round 1). Re-planted all 13 shapes as real files under bin/ with __pycache__ cleared and 1.05s slept past the whole-second boundary, both detector tests against each, plants removed between, green-before and green-after. Reproduced the read-side split table exactly (7/7/8/8/8/3) after first getting it wrong by omitting the .strip("|") the shape definitions carry — the census was right and my harness was wrong. Planted w4-w7 and render_row into the real 15-column P0 table on both 'audit | then ship' and 'need one\n\nneed two'; planted the identical rows into an unrecognised '## Backstop probe' section (0 errors, ragged=0) WITH my own control placing the same 8-cell row inside the recognised P0 table (ragged=1) — the schema-recognition limit is confirmed and the control is what makes it mean something. Ran perry-decide new with interior \n, trailing \n, trailing \r and trailing U+2028 and read all three resulting ADRs. Exercised render_row / check_cell / append_cell / splice_cell over all 11 trailing splitlines() boundaries. Opened all 22 cited file:line citations at 7ea0bff. Grepped the 5 bash tools for cut -d'|' / awk -F'|' / IFS='|' / row-shaped echo and checked every shebang. All of it on git-archive copies in scratch; live tree untouched, git status --porcelain empty.
not-checked: I did not re-run the full test suite (110 modules / 3094 tests per db12fa4's message) — only the two detector tests in tests/test_row_integrity.py, plus perry-lint end to end. I did not re-attack the member rule with round 1's six blind-spot constructs or new ones; I re-derived the 89 and attacked the domain instead, so round 1's F4 (the bound's name-resolution prose is false for the f-string clause) is inherited unverified and remains an open follow-up. I did not trace all 38 R1 members to split_row at runtime — I mutated 9 of them, one per file. I did not verify the author's process claim that their own plants ran on archive copies, only that main's tree is intact today. I did not confirm the census's stated measurement commit 5720730 yields 89 (the script was not in the tree there). I did not test the 5 uncaught read shapes end to end through a real tool — none exists in the tree; they were planted as files only. I did not check any non-Python tree consumer outside this repository, nor the two outbound templates' behaviour in a host project. I did not evaluate whether reading (A) or (B) is correct — explicitly out of the bound.
proof: n/a — PASS
=== END VERDICT ===
