# V4 · fresh-context review of the `review` queue — 067, 037, 042, 050, 034

> Reviewer: fresh context. Built none of this; scored against the criteria files
> named per section, not against the builders' narratives.
> **Everything below was run**, on an `rsync` snapshot of
> `/Users/bytedance/proj/Perry`'s working tree taken at the start of this
> session. Nothing was written to Perry's state files. `~/proj/gimegime-pmo` and
> `~/proj/PolyForge` were never touched directly; the only reads of them were
> the ones `tests/test_goals_writer.py` performs itself during the one baseline
> suite run.
> Every mutation was one edit in place on the snapshot, `__pycache__` cleared
> around each run, each reverted and confirmed byte-identical to the live file
> afterwards (`cmp`).
> Rung of this document: **V4**, except § 5 which is explicitly **V3 only**.

**Baseline reproduced:** `bash tests/run` → schema drift guard clean,
**1258 tests, OK** (no failures, no skips), all `bin/` scripts answer `--help`,
both sample projects lint clean. Matches the stated baseline exactly.

| Row | Criteria scored against | Verdict |
|---|---|---|
| TASK-067 | `perry/evidence/2026-08/TASK-067-finding.md § What must be true when this is fixed` | **FAIL** |
| TASK-037 | `perry/evidence/2026-08/TASK-037-spec.md` | **FAIL** |
| TASK-042 | `goals/reference/phases.md § commit <promise>` | **FAIL** |
| TASK-050 | no criteria file on the row — see § 4; scored against the round-1 review's posed question | **FAIL** |
| TASK-034 | `perry/evidence/2026-08/TASK-034-lifecycle.md` | **V3 holds; NOT signed — V5 is the user's** |

**Not reviewed:** TASK-027, TASK-028, TASK-052, TASK-053. TASK-019 / 020 / 040 /
044 belong to another reviewer and were left alone.

---

## 1 · TASK-067 — row integrity · **FAIL**

Criteria: the six checkboxes in `TASK-067-finding.md § What must be true when
this is fixed`.

| Criterion | Verdict |
|---|---|
| a value that cannot read back is **refused at the writer**, naming field and character | **does not hold** — two writers bypass `render_row` entirely (F1); a third reaches `tables.py` but mangles instead of refusing (scored under TASK-037) |
| the guard is stated as the round trip, not a character list | holds — `viewer/tables.py § render_row`, two clauses |
| **every** reader goes through one splitter | **does not hold** — `viewer/parsers.py:224` (F3) |
| a row reads the same with the event log absent | not re-verified this round |
| a ragged row is a finding, both directions | **holds, and it works** — it is what surfaced F1 |
| the three repaired rows round-trip | holds (`tests/test_row_integrity.py`, 17/17 green) |

### Finding 1 — `bin/perry-decide` writes table rows by f-string, and `perry-lint` calls its own output an error

`bin/perry-decide § render_index` builds `DECISIONS.md` rows as
`f"| {link(a)} | {a['title']} | {a['type']} | …"` (lines 248 and 256). It never
calls `render_row`, so TASK-067's writer guard does not exist on this path.
`a['title']` is free user text taken from an ADR's own heading.

Reproduced end to end on a throwaway project, tool-created throughout:

```
$ perry-decide bootstrap
$ perry-decide new pipe-title --title 'Use A | not B' --type architecture
perry-decide: wrote ADR-001                        rc=0

DECISIONS.md:
| ADR | Title | Type | Date | Sunset / Notes |
|---|---|---|---|---|
| [ADR-001](decisions/ADR-001-pipe-title.md) | Use A | not B | architecture | 2026-08-18 | — |

split_row → 6 cells against a 5-cell header:
  Title='Use A'  Type='not B'  Date='architecture'  Sunset='2026-08-18'

$ perry-lint --root <proj>
✗ perry/DECISIONS.md:8 [ragged-row] row '…| Use A | not B |' has 6 cell(s)
  but its header has 5 — every column after the extra `|` is shifted
```

Perry's own linter reports Perry's own writer's output as an error, at writer
exit 0. That is TASK-067's opening sentence — *"the writer can destroy the table
it writes to"* — reproduced in a third tool, after the fix. The good news is
that guard 3 works; the bad news is what it caught.

A line break in the same field is worse and silent: `--title $'line one\nline
two'` writes an ADR whose own heading block is broken, and the index row comes
back with `Type` and `Date` empty. rc=0, no warning, and `ragged-row` does not
fire because the row still has five cells.

`bin/perry-conform:395` has the identical shape —
`rows = [f"| {d.path} | {d.shape_version} | {d.declared} | {d.route} |"` — so
`.perry/conformance.md` is written *and* read (F3) entirely outside the one
rule. `tests/test_decide_writer.py` contains no occurrence of `render_row`,
`split_row`, `pipe` or `escape`.

**Smallest fix.** Route both through `viewer/tables.py § render_row`
(`out += [render_row([link(a), a['title'], a['type'], a['date'], a['sunset'] or
'—'])]`) and translate `UnrenderableCell` at each tool's `main`, which is the
wiring `perry-task` and `perry-goals` already have.

### Finding 2 — the category guard is a literal-string grep over a hardcoded file list, and a new reader walks straight past it

`tests/test_row_integrity.py:239 test_no_reader_carries_its_own_splitter`
iterates a hardcoded tuple of eight paths and matches the literal substring
`strip("|").split("|")`.

I added `bin/perry-newreader` to the snapshot — a plausible new contributor's
reader carrying `[c.strip() for c in line.strip().strip("|").split("|")]`, the
*exact* literal the guard greps for, plus its own header rule. Result:

```
tests/test_row_integrity.py   → Ran 17 tests   OK
tests/test_one_header_rule.py → Ran  6 tests   OK
```

Neither guard noticed. `test_one_header_rule.py § READERS` already solves this
correctly — it enumerates everything in `bin/` plus `viewer/parsers.py`, and its
comment says why ("not a curated list of offenders … a NEW reader is caught
too"). TASK-067's splitter guard was never brought up to it. (The header guard
missed the same file for a different reason, scored in § 4.)

### Finding 3 — the sixth splitter, still live

`viewer/parsers.py:224`, inside `read_conformance`:

```python
cells = [c.strip().strip("`") for c in m.group(1).split("|")]
```

Reproduced at HEAD, on a row `render_row` produced correctly:

```
render_row      : | design/DESIGN-9 \| draft.md | 2 | 2026-08-18 | declare |
split_row       : ['design/DESIGN-9 | draft.md', '2', '2026-08-18', 'declare']
read_conformance: declarations {} · unreadable [(7, '| design/DESIGN-9 \| …')]
```

A declaration Perry wrote reads back as no declaration at all. Named by the
round-4 review; it has not moved. Exploitability is narrow (a `|` in a path),
but the criterion is categorical and `.perry/conformance.md` is the file ADR-004
turns on.

**Smallest fix for F2 + F3.** Two lines: route `parsers.py:224` through
`split_row`, and replace the guard's hardcoded tuple + literal substring with
`test_one_header_rule.READERS` and
`re.compile(r'\.split\(\s*["\']\|["\']\s*\)')`. I ran that regex over `bin/`,
`viewer/`, `templates/`, `setup/`, `packs/`, `modes/`, `goals/`, `work/` and
`decide/`: exactly two hits — `parsers.py:224` (the defect) and
`parsers.py:1451` (`phase.status … .split("|")[0]`, a value normalizer, which
`test_one_header_rule`'s own stated doctrine legitimately exempts).

### One thing I checked and cleared

`bin/perry-goals § cell_spans` is a second scan of a row and could plausibly
disagree with `split_row`. It does not: exhaustive fuzz over
`{a, |, \, space, \|}` to length 5 in 1- and 2-cell rows — **3905 inputs, 0
divergences** once span text is unescaped. That duplication is redundant, not
divergent.

---

## 2 · TASK-037 — the `perry-goals` writer · **FAIL**

Criteria: `TASK-037-spec.md`, in particular *"do not copy `Board` to do it …
Duplicating it into `bin/perry-goals` creates two implementations of one rule,
which is the single defect class the last five review rounds kept finding."*

### What holds, and it is real

- **The gate.** `TestByteIdentity` loads and writes back Perry's `OKR.md`,
  `sample-project/OKR.md`, `OKR_TEMPLATE.md`, `~/proj/gimegime-pmo/OKR.md` and
  `~/proj/aimark/perry/OKR.md` — five files, no skips in my run, all
  byte-identical. `test_the_corpus_actually_disagrees` asserts the corpus keeps
  the shapes the gate is about, which is the right guard on a round-trip test,
  and `test_a_file_with_no_trailing_newline_round_trips` covers the
  `splitlines()` trap explicitly.
- **The extraction is genuine.** `viewer/tables.py` exists (150 lines:
  `split_row` / `render_row` / `squash` / `UnrenderableCell`), and `perry-task`,
  `perry-goals`, `perry-lint`, `perry-migrate`, `perry-state`, `perry-diagnose`
  and `perry-explain` all reach it. `perry-lint § norm` is asserted to *be*
  `squash`.
- **Column resolution is table-local and by name** throughout `perry-goals`
  (`column_spellings` / `column_at` / `canonical_of` / `header_language`), all
  through `squash`.

### The finding — the write-side rule has two implementations, and they have diverged

`cell_spans` / `splice_cell` / `append_cell` / `append_separator_cell` stayed in
`bin/perry-goals`. The builder called that *"a real, if small, instance of the
duplication this task's spec is about."* Asked to judge whether it is still
small: **no** — because it no longer merely duplicates, it *contradicts* the
canonical rule, on the exact criterion TASK-067 was opened to establish.

`splice_cell:275` and `append_cell:288` both do
`.replace("\n", " ").replace("|", "\\|")` — encode-and-strip, silently, at exit
0 — where `render_row` raises `UnrenderableCell`. Same tool, same session, same
value, opposite behaviour depending only on whether the row already exists:

```
# CREATE  → viewer/tables.py § render_row
$ perry-goals commit --track ops --promise $'line one\n\nline two' --to Finance --by "within the track SLA"
rc=1  perry-goals: refused — the value 'line one\n\nline two' contains a line
      break — a markdown table row is one line.

# AMEND   → bin/perry-goals § splice_cell            (all three amend paths)
$ perry-goals commit --miss  ops/7 --reason         $'line one\n\nline two'     rc=0
$ perry-goals commit --id    ops/7 --promise        $'para one\n\npara two'     rc=0
$ perry-goals commit --close ops/7 --discharged-by  $'closed one\n\nclosed two' rc=0

| ops | ops/7 | para one  para two | Finance | within SLA | closed | oldest-first · line one  line two · closed one  closed two |
```

The user's paragraph breaks are gone and nothing says so. The round-4 review
found two of these three paths; `--id --promise` is the third, and it mangles
the `Promise` cell itself — the one column a human reads this register for.

`grep` for `splice_cell`, `append_cell`, `line break` and `UnrenderableCell` in
`tests/test_goals_writer.py` returns **zero hits**: the amend path's value
handling is entirely uncovered, which is how the divergence survived a
1258-test suite.

Secondary, not the blocker: the spec names `ensure_columns` / `append_row` /
`replace_row` as part of the surgery to move; they are still `Board` methods in
`bin/perry-task`, and `perry-goals § Okr.widen` (lines 432-435) is a second
implementation of `ensure_columns` with different alignment behaviour.

**Smallest fix.** Move the four helpers into `viewer/tables.py` beside
`split_row`, and make `splice_cell` / `append_cell` raise `UnrenderableCell` on
a line break instead of collapsing it. `bin/perry-goals § main` already
translates `UnrenderableCell` into the refusal channel — the wiring exists and
the create path already uses it.

---

## 3 · TASK-042 — `commit` stops being prose · **FAIL**

Criteria: `goals/reference/phases.md § commit <promise>`, rule by rule. Nine of
the ten hold, each verified by running it against a fixture project:

| Rule | Result |
|---|---|
| §1 refused when the section is absent and no track is `pipeline`/`queue` | holds — the refusal names both modes and both mode files |
| §2 `Id` minted per track, spanning table **and** `events.jsonl` | holds — minted `ops/8`; I hand-deleted that row; next mint was `ops/9`, not `ops/8` |
| §3 `--to` has no default | holds, with the specified sentence |
| §4 `pipeline` needs a date | holds |
| §4 queue track with no `SLA` cell refused | holds (the `bare` track) |
| §5 row written `active` with `Discharged by` empty | holds |
| §6 board-side link printed as a hand-off, not performed | holds |
| §7 `--close` refused while `Discharged by` empty | holds, with the specified sentence |
| §7 `--miss` appends, never replaces | holds |
| §9 `By when` edit refused on a past-dated `active` row | holds, verbatim wording |

### The finding — the clock category is enforced in English and not in Chinese

Rule §4: *"'Names no clock' is enforced as the **category**, not as those three
examples: the cell must carry a date, the word `SLA`, or a unit of time.
`eventually` and `有空再说` are refused for the same reason `soon` is."*

The criteria file deliberately picks a Chinese example to make that point. Run
against a `queue` track with a declared SLA:

| `--by` | verdict |
|---|---|
| `soon`, `ASAP`, `when we get to it`, `eventually`, `有空再说` | REFUSED ✓ |
| `next sprint`, `before launch`, `1 fortnight` | REFUSED ✓ |
| `one day`, `within the track SLA`, `5 days` | ACCEPTED ✓ |
| **`改天`** ("some other day") | **ACCEPTED** |
| **`日后再说`** ("we'll talk about it later") | **ACCEPTED** |

Both were written into `OKR.md` as live `By when` values:

```
| ops | ops/11 | p | Fin | 改天       | active |  |
| ops | ops/12 | p | Fin | 日后再说   | active |  |
```

`日后再说` is the same idiom family as the criteria file's own refused example
`有空再说` — `…再说` = "we'll get to it later" — and it is the direct Chinese
translation of `when we get to it`, which the tool refuses in English. It passes
because `CLOCK_RE` (`bin/perry-goals:935`) ends in a bare single-character class
`[天日周月年]`, so **any** occurrence of 日 or 天 anywhere in the prose counts
as naming a clock. The English half of the same regex requires a whole word
(`\b(?:day|days|week|…)\b`), so the two languages are not held to the same
category. In practice a Chinese `queue` track has no clock check at all — almost
any Chinese scheduling prose contains one of those five characters.

This is not the "sincerity" carve-out the criteria allow (`one day` passes and
no parser can do better). `one day` names a unit; `日后再说` names none — the
character is incidental to the phrase. Perry ships a Chinese fixture project and
a full i18n glossary, so this is a shipped surface, not a hypothetical.

**Smallest fix.** Require a quantity before the bare CJK unit and keep the
already-anchored spellings:

```python
r"|(?:\d+|[一二三四五六七八九十两半几])\s*[天日周月年]"
r"|小时|分钟|工作日|季度|时限|本周|本月|周内|日内|月底|年底"
```

`5天`, `两周`, `本月底` still pass; `改天`, `日后再说`, `有空再说` all refuse.

### Two gaps that are conformant as written, but worth closing

- **`--miss` then re-date.** §9's refusal keys on `Status == active`, so
  `--miss ops/7` followed by `--by 2027-01-01` is accepted and the row becomes
  `2027-01-01 | missed` — the original deadline is gone from the file, which is
  the outcome the doctrine sentence ("never silently re-dated") is about. The
  enforcement paragraph names `active` explicitly, so this is conformant to the
  letter.
- **A new past date onto a prose `By when`.** `--by 2020-01-01` on an `active`
  row whose current value is `within SLA` is accepted, creating an
  already-missed active commitment at rc=0. Not covered either way.

---

## 4 · TASK-050 — one normalization for a header cell · **FAIL**

**First, a structural problem with the row itself.** `perry-task list --all
--json` reports TASK-050 with `evidence: "—"` and `evidence_paths: []`, and
`verification: "V4"`. Per `schema/state-schema.json § verification` a V4 is
scored against a written acceptance-criteria file; this row names none. The only
written criterion is the question posed in
`perry/evidence/2026-08/TASK-050-053-057-060-v4-review.md § TASK-050` — *"is
there any remaining place in `bin/` or `viewer/` that normalizes a header cell
by a second rule?"* — which is a review artifact, not a spec. I scored against
that. **This row cannot honestly carry a V4 until it names a criteria file.**

### The delivered work is substantial, and I confirmed it behaviourally

Not by grep. I wrote a transform that decorates **every markdown table header
cell** in a project with the divergence shape (`Next action` → `**Next**
action`; single-word cells → `**Foo**`), applied it to a copy of Perry itself —
**115 files**, including `perry/BOARD.md`
(`| **ID** | **Title** | **Owner** | **Status** | **Next** action | …`),
`perry/OKR.md`, `perry/DECISIONS.md`, the knowledge cards and
`packs/software-ops/pack.md § Glossary` (`| **Term** | **Shown** as |`) — and
diffed six tools' complete output against the undecorated copy:

```
perry-state --json            identical except the root path
perry-diagnose --json         identical except the root path
perry-task list --all --json  identical except the root paths
perry-goals list --json       identical except the root paths
perry-explain                 byte-identical
perry-knowledge list          byte-identical
```

Same sweep over `tests/fixtures/sample-project`: identical. Direct probe of the
round-1 failing case — `perry-state.parse_tracks` on
`| Track | Mode | … | Default rung |` decorated six ways (`**Default rung**`,
`**Default** rung`, `` `Default` rung ``, `Default  rung`, `Default rung*`):
`default_rung='V2'` in all six. All four named sites are genuinely fixed.

### The finding — a fifth site, live and reproducible, in `viewer/parsers.py`

`viewer/parsers.py:1568`, inside `_parse_legacy_tripwire_table`:

```python
if cells[0].lower() in {"day", ""}:
    continue          # the header row
```

That is a header cell resolved by a second rule — the **identical shape** to
`bin/perry-state:123`'s `cells[0].lower() != "term"`, which round 1 counted as
one of its three offenders and which was fixed to `squash(cells[0]) != "term"`.
This one was not.

It is reachable. A repeated header row inside a long hand-maintained table — a
common pattern — is skipped when plain and parsed as data when decorated:

```
plain                    -> [('#1', '3', 'latency up')]
decorated header row     -> [('#1', '3', 'latency up')]
repeated **Day** header  -> [('#1', '3', 'latency up'),
                             ('#2', 'Day', 'Condition'),   ← phantom trip-wire
                             ('#3', '5', 'errors up')]     ← and every id after it shifts
```

### The guard cannot see it — and could not have caught one of its own three defects

`tests/test_one_header_rule.py § SECOND_RULE` is
`r"=\s*\[[^\]]*?\.lower\(\)[^\]]*?\bfor\b\s+\w+\s+in\s+(?:cells|split_row\()"` —
it only matches a **list comprehension assigned with `=`**. A scalar
`cells[0].lower()` header test cannot match it, and neither can a comprehension
that is returned rather than assigned.

Mutation, to make that concrete rather than asserted. I reverted
`bin/perry-state`'s `load_packs` fix in place — `squash(cells[0]) != "term"` →
`cells[0].lower() != "term"`, one line, `__pycache__` cleared around the run:

```
tests/test_one_header_rule.py                                    → 6 tests, OK
+ test_parsers, test_i18n, test_i18n_one_table, test_diagnose,
  test_work_modes, test_wip_and_stages, test_row_integrity,
  test_conformance                                               → 351 tests, OK
```

**Green on a mutation that restores one of the three defects this task was
FAILed for in round 1.** Reverted; `cmp` against the live file confirms
byte-identical.

Separately, the new reader added in § 1 F2 (`bin/perry-newreader`, header rule
`return [c.strip("*` ").lower() for c in cells]`) also passed all 6 tests:
`test_no_reader_resolves_a_header_cell_by_a_second_rule` misses it on the
`return` vs `=` distinction, and
`test_every_reader_that_resolves_headers_reaches_the_one_rule` skips any file
that does not contain the literal `split_row(`.

**Smallest fix.** One line — `if squash(cells[0]) in {"day", ""}` at
`viewer/parsers.py:1568` — plus widening `SECOND_RULE` to the scalar shape and
dropping the `=\s*` anchor. I ran the widened pattern

```python
re.compile(r"\[[^\]]*?\.lower\(\)[^\]]*?\bfor\b\s+\w+\s+in\s+(?:cells|split_row\()"
           r"|\bcells\s*\[\s*\d+\s*\]\s*\.lower\(\)")
```

over the full `READERS` enumeration at HEAD: **exactly one hit,
`viewer/parsers.py:1568`** — no false positives. Against known cases it flags
the round-1 `perry-state` offender, `parsers.py:1568`, the old comprehension
shape and the returned comprehension, and clears every deliberately-exempt value
normalizer (`Status`, `Outcome`, `mode`).

---

## 5 · TASK-034 — the aiMark lifecycle · **V3 verified · NOT SIGNED**

The row says this is **V5, not V4**, and says why: the acceptance is whether one
call is enough for aiMark to be built on, and only aiMark's author can say that.
**I am not signing this row.** What follows is the V3 half only — does the
lifecycle reproduce.

**It reproduces.** Fresh throwaway project rendered from
`work/state/BOARD_TEMPLATE.md`; `add → start → status review → prioritize P0 →
done --evidence --rung V3`, then one `perry-task list --all --json`:

```
contract   : perry-task/list/1.8      semantics: present
grep -c TASK-001 BOARD.md : 0         list --json (no --all) : 0 tasks
list --all --json         : 1 task
  status 'done'  priority 'P0'  open False  track 'main'
  evidence       'evidence/2026-08/probe.md'
  evidence_paths ['perry/evidence/2026-08/probe.md']
  timeline:
    add         field=status   None          -> 'not_started'
    start       field=status   'not_started' -> 'in_progress'
    status      field=status   'in_progress' -> 'review'
    prioritize  field=section  'P1'          -> 'P0'
    done        field=status   'review'      -> 'done'
```

Both of DESIGN-004 § 1.3's questions are answered by that one call: the closed
row has left the board and is still fully reported with its history, and
`updated` moves from the event rather than from a cell an agent must remember to
change. `evidence_paths` resolves on the closed row. The self-contradiction
defect the document reports finding in its own session is fixed — `priority:
'P0'` agrees with the row's own timeline. Reads are unaffected under the gate:
`PERRY_CONFORMANCE=enforce` gives `rc=0` for `perry-task`, `perry-state`,
`perry-goals` and `perry-diagnose`.

**Three ways the evidence document is stale — which matter, because it is what a
V5 signer will read.**

1. **It records `contract: perry-task/list/1.5`. HEAD serves `1.8`.** The
   lifecycle has not been re-recorded against the payload the signature is being
   asked about.
2. **Its § 3 hazard is no longer true.** The document tells aiMark that
   *"`event: "prioritize"` is the only thing that disambiguates"* a section move
   from a status move, and calls it "the one shape in this payload that can be
   misread while looking correct". Contract 1.8 added `timeline[].field`, which
   disambiguates directly — `prioritize` carries `field: "section"`, everything
   else carries `field: "status"`. A signer following this document would build
   a workaround that is no longer needed.
3. **The document's own commands no longer run as written.** `add` now refuses
   without `--deliverable` and `--verification`; the recorded run used neither,
   so reproducing the document verbatim fails at step 1. Correct refusals — but
   the document is presented as a reproduction and is not one.

**Recommendation:** re-run and re-record § "Re-run 2026-08-18" against 1.8
before the row is put in front of the user. A V5 records name, date and what was
checked, and what is on the page is now three contract minors behind.

---

## What I did not get to

- **TASK-027** — lane rename reaching every user-facing surface. The round-5
  FAIL was a category failure across every tool's `--help`; that needs its own
  sweep and I did not run it.
- **TASK-028** — diagnose/adopt mode detection + both READMEs.
- **TASK-052** — the meaning checks.
- **TASK-053** — the intake drain. Note the round-4 review recorded a FAIL with
  a specific missing test; I did not verify whether that test landed.

TASK-019 / 020 / 040 / 044 belong to another reviewer and were deliberately
untouched.

## Method notes

- Snapshot: `rsync -a --exclude=.git --exclude=__pycache__ --exclude=.claude`
  of the working tree. Every experiment ran there.
- Every mutation was reverted and verified with `cmp` against the live file.
- `bin/perry-newreader` was added to the snapshot only, and removed.
- No `perry-task`, `perry-goals`, `perry-decide`, `perry-conform declare` or
  `perry-migrate` write was run against `/Users/bytedance/proj/Perry`.
  `setup` was never run.
