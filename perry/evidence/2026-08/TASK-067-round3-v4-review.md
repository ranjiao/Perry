# V4 · round 3 — TASK-067, row integrity

> Reviewer: fresh context. I did not write any of this and did not read the
> author's reasoning for agreement — I read it for claims to break.
>
> **Everything below was run on copies under scratchpad.** The live checkout
> was read (`git log`, `git show`, `grep`, one `python3 bin/perry-lint`) and
> never written to, never planted into, never `checkout`/`stash`/`reset`. Five
> other rounds are running against that same tree and a planted file makes the
> guard legitimately red for whoever is watching.
>
> Snapshot taken at **`c24de3f`**. HEAD moved to **`b658329`** mid-round; I
> re-checksummed and every file under review — `viewer/tables.py`,
> `viewer/parsers.py`, `tests/test_row_integrity.py`, and all nine
> `bin/perry-*` python tools — is **byte-identical** between my copy and the
> live tree, so nothing here is stale.
>
> `git status` on the live tree at the end of this round: **empty**. Nothing of
> mine is in it.

Criteria: `perry/evidence/2026-08/TASK-067-finding.md § What must be true when
this is fixed`, six checkboxes. Nothing else was scored.

Baseline, on the copy: `python3 tests/parallel` → **35 modules · 1304 tests ·
85.3s · all green**. (The prior round recorded one pre-existing failure in
`test_diagnose`; it is gone.) `python3 bin/perry-lint` on the real repo: **✓
clean**.

| # | Criterion | Verdict |
|---|---|---|
| 1 | refused at the writer, **naming the field and the character** | **NOT MET** — two sites, § 3 |
| 2 | the guard is the round trip, not a character list | met |
| 3 | **every** reader goes through one splitter | met in fact; its **guard is blind again**, § 4 |
| 4 | a row reads the same with the event log absent | met — measured, § 2 |
| 5 | `ragged-row` is a finding, both directions | met in substance; catalog/`WHY` clause unmet, § 5 |
| 6 | the three repaired rows round-trip | met — 33/33 |

**Verdict: FAIL**, on criterion 1. The central defect is genuinely fixed and I
could not break it; § 1 says so in detail before § 3 takes it apart, because
both halves are true and a review that reports only the second is not a
measurement.

---

## 1 · The two decisive tests both pass

### (a) A brand-new writer and a brand-new reader are both caught

On the copy, I created two files that did not exist when the guard was
written:

```
bin/perry-newwriter :  return f"| {task_id} | {title} | {owner} |"
bin/perry-newreader :  return [c.strip() for c in line.strip("|").split("|")]
```

`tests/test_row_integrity.TestEveryoneReadsTheRowTheSameWay` →

```
FAIL: test_no_tool_splits_a_row_on_a_raw_pipe
      ['bin/perry-newreader:6'] != []
FAIL: test_no_tool_writes_a_row_by_hand
      ['bin/perry-newwriter:6'] != []
```

Both halves red. Removed; the copy's 6,911-file checksum manifest is
**byte-identical** before and after, and the 19 `test_row_integrity` tests are
green again. This is the exact failure round 2 FAILed on and it is fixed for
the shapes round 2 used. § 4 is about the shapes it did not use.

### (b) A hand-destroyed row is no longer silent-clean

I copied the whole project and wrote the original corruption into
`perry/BOARD.md` **by hand** — a row ending mid-cell with no closing `|`, a
blank line, and the tail as a loose paragraph:

```
| TASK-067 | The writer can destroy the table it writes to | Coding Agent | review | first paragraph of the next action

second paragraph of the next action | evidence/2026-08/TASK-067-finding.md | V4 |
```

`python3 bin/perry-lint --root <copy>`:

```
✗ perry/BOARD.md:15 [ragged-row] row 'TASK-067 | The writer can destroy the
  table it writes to | C' has 5 cell(s) but its header has 7 — the trailing
  column(s) read as empty
1 error(s), 0 warning(s)
```

That is the original defect's silent `✓ clean`, gone. And it is the
`ragged-row` check doing it, not something else — see the mutation in § 6,
where disabling that one `if` puts the same destroyed board back to `✓ clean`.

**One thing (b) does not fix, and it is worth naming.** The *compounding* half
of the original defect is still live on a hand-edited board. On the destroyed
copy:

```
$ perry-task add --title "after the damage" --priority P0 …
perry-task: ⚠ conformance (advisory) — … no longer matches: 1 error(s).
perry-task: wrote TASK-081 (add) → board + journal + event
```

and the row landed **between the truncated head and its spilled tail**:

```
| TASK-067 | … | review | first paragraph of the next action
| TASK-081 | after the damage | Coding Agent | not_started | — | — |  |

second paragraph of the next action | evidence/…-finding.md | V4 |
```

The finding's own closing note says *"the corruption pattern requires a writer
that no longer exists."* It does not — a hand edit reproduces it, which is the
case decisive test (b) exists for, and the tool then compounds it at rc=0. The
advisory line does now name that something is wrong, which is more than the
original had. **No criterion covers this**, so it is not what fails the task.

---

## 2 · Criterion 4, measured rather than assumed

`perry-task list --json` over the real 20-row board, then the same board with
`.perry/events.jsonl` **deleted**, comparing `next_action` / `evidence` /
`verification` per row:

```
rows differing between event-log-present and absent: 0
```

Then the case that would actually diverge — a row carrying escaped pipes and
**no event at all**, hand-inserted:

```
| TASK-0NN | escaped pipe row | … | quotes a header \| ID \| Risk \| Opened \| and then some | — | V2 |

with    events → next_action 'quotes a header | ID | Risk | Opened | and then some'
without events → next_action 'quotes a header | ID | Risk | Opened | and then some'
perry-state: reads the row.   perry-lint: ✓ clean (correctly — the row is well formed)
```

Criterion 4 holds, including on the payload aiMark reads.

---

## 3 · Criterion 1 is not met — the finding

The criterion, verbatim:

> A cell value that would not read back as itself is **refused at the writer**,
> naming the field and the character. **Not encoded, not stripped silently** —
> the user asked to store something the format cannot hold.

### 3a · `viewer/tables.py:214` — `append_cell` still encodes, and still strips silently

```python
def append_cell(line: str, value: str) -> str:
    body = line.rstrip()
    value = str(value).replace("\n", " ").replace("|", "\\|").strip()   # :214
    if not body.endswith("|") or body.endswith("\\|"):
        return render_row(split_row(line) + [value])                    # :219
    return body + (f" {value} |" if value else "  |")
```

Reproduced:

```
append_cell("| a |", "x\n\ny")   →  '| a | x  y |'          the paragraph break is gone, silently
check_cell("x\ny")               →  UnrenderableCell: contains a line break
```

`.replace("\n", " ")` **is** "encoded … stripped silently", in
`viewer/tables.py` — the one module this whole task exists to make canonical —
two functions below `check_cell`, which refuses the identical value. The
previous round found this exact rule divergence in `bin/perry-goals §
splice_cell` and it was fixed by routing `splice_cell` through `check_cell`.
`append_cell`, its neighbour, kept the old rule. That is *fixing the instance,
not the category*, inside the file whose docstring says duplicating a rule
"would be the defect these functions exist to prevent."

The same line breaks the round trip the other way. On the fallback branch the
value is escaped once at :214 and again by `render_row` at :219:

```
append_cell("| a | b",  "x|y")   →  '| a | b | x\\|y |'  →  split_row → 'x\|y'   ✗
append_cell("| a | b |", "x|y")  →  '| a | b | x\|y |'   →  split_row → 'x|y'    ✓
```

A value that does not read back as itself, produced by the module whose stated
invariant is that a value reads back as itself.

**Honest severity.** Not user-reachable today: the only caller is
`bin/perry-goals § widen` (`:358`, `:361`), which passes a hard-coded column
name and `""`. So the shipped CLI does not currently mangle anything through
this path. It is a latent divergence in shared code, and criterion 1 is written
about the writer, not about which flags happen to reach it. A reviewer who
reports "unreachable, therefore fine" is the reviewer who signed off on
`splice_cell` one round ago.

(Related, minor: `append_separator_cell` is still in `bin/perry-goals:226`
rather than `viewer/tables.py`. It writes only dashes, so nothing is at risk —
noted because three of the four functions moved and one did not.)

### 3b · The refusal names the character and the value, never the field

`UnrenderableCell` carries `index` **and it is never printed**.

```
$ perry-task add … --next $'first para\n\nsecond para'
perry-task: refused — the value 'first para\n\nsecond para' contains a line break
            — a markdown table row is one line.

$ perry-task add … --title $'title\nbroken'
perry-task: refused — the value 'title\nbroken' contains a line break
            — a markdown table row is one line.
```

Two different fields, two identical message shapes, neither naming `--next` or
`--title`. `bin/perry-task:4012–4016` and `bin/perry-goals:1409` both format
`exc.value` and `exc.why` and drop `exc.index`. Worse above 60 characters:
`bin/perry-task:4012` truncates the echoed value to `[:60]`, so a user who
pasted the same long paragraph into two flags gets neither the field name nor
enough of the value to tell which one was refused.

The criterion names two things the message must carry. It carries one.

### 3c · Not a criterion, but adjacent and reproducible

`--deliverable` and `--verification` accept raw newlines at rc=0 and write them
verbatim into `journal/…md`:

```
- **Deliverable**: a thing
exists
- **Verification**: lint clean

and green
```

Neither value reaches a table cell, so criterion 1 does not reach it either.
It is the same shape of defect — a line-structured state file broken by an
embedded newline from a free-text flag — one file over, and it is the shape
the finding says to state as a category rather than as an instance.

---

## 4 · Criterion 3 holds; the guard that keeps it holding is instance-shaped again

**The fact holds, and I enumerated rather than spot-checked.** Every python
tool in `bin/` and every `viewer/*.py` imports `split_row` from
`viewer/tables.py` (`perry-task`, `perry-goals`, `perry-lint`, `perry-migrate`,
`perry-state`, `perry-diagnose`, `perry-explain`, `parsers.py`; `perry-decide`
and `perry-conform` import `render_row`). A regex sweep for
`.split("|")` / `.split('|')` over `bin/`, `viewer/`, `packs/`, `setup/`,
`templates/`, `modes/`, `goals/`, `decide/`, `state/`, `schema/`, `work/`,
`reference/` returns **zero** hits. Round 2's sixth splitter
(`viewer/parsers.py § read_conformance`) now goes through `split_row`
(`:228`). The three surviving bare-pipe splits are **value** normalizers, not
row splitters, and each is correct: `viewer/parsers.py:1459`
(`.split("|", 1)[0]` on a `Status:` header field), `bin/perry-lint:594` and
`bin/perry-migrate:675` (`re.split(r"[|/,]", value)[0]`). `bin/perry-decide:149`
splits an ADR header line on ` | `, which is a different format.

**And then I probed the guard, because round 2's FAIL was that the guard could
not see a new file.** Nine more files on the copy, all defective, all in the
same two categories the two tests name:

| planted | shape | guard |
|---|---|---|
| `bin/perry-probe-w2` | `f"\| TASK-{n} \| {t} \| Coding Agent \|"` | **green** |
| `bin/perry-probe-w4` | `"\| %s \| %s \|" % (a, b)` | **green** |
| `bin/perry-probe-w5` | `"\| {} \| {} \|".format(a, b)` | **green** |
| `bin/perry-probe-w3` | `"\| " + " \| ".join(cells) + " \|"` | green *(documented limit)* |
| `bin/perry-probe-r2` | `line.strip("\|").split("\|", 6)` | **green** |
| `bin/perry-probe-r3` | `re.split(r"\\\|", line.strip("\|"))` | **green** |
| `bin/perry-probe-r4` | `SEP = "\|"` … `line.strip(SEP).split(SEP)` | **green** |
| `bin/lib/rows.py` | **both** defects, verbatim | **green** |
| `viewer/sub/reader.py` | the round-2 literal, verbatim | **green** |

`tests/test_row_integrity.py:270-272`:

```python
out = [p for p in sorted((PERRY_HOME / "bin").iterdir())
       if p.is_file() and not p.name.endswith((".md", ".json"))]
out += sorted((PERRY_HOME / "viewer").glob("*.py"))
```

`iterdir()` + `is_file()` skips every subdirectory; `glob("*.py")` is not
`rglob`. So **`bin/lib/` is invisible to this guard** — and `bin/lib/` is not
hypothetical. `TASK-065` is an open row on this board whose entire subject is
creating it, and this task's own criteria file names it:

> (If TASK-065 has landed, this is a call into `bin/lib/`; if not, an import.)

The guard's own docstring says *"a guard that cannot see a new file is a guard
against the files that already had the bug."* It cannot see a new **directory**,
and it is the directory the criteria expect the splitter to move into. Round 2
found this one level up; this is the same defect one level down.

`bin/perry-probe-w2` is the second axis: `HAND_ROW_RE` is
`f['"]\s*\|\s*\{`, so it matches only an f-string whose **first cell begins
with interpolation** — the exact lexical shape `bin/perry-decide` happened to
have. `f"| TASK-{n} | {t} |"` is the same defect and walks through.

The `.join()` blind spot (`perry-probe-w3`) I do **not** count against the
task: it is stated in the guard's own comment with a measured reason (a first
version flagged 14 of which 11 were fine), and no such writer exists in the
tree today — the only ` | `.join sites are `viewer/tables.py:103` itself and
`bin/perry-lint:657`, which builds a display string.

Criterion 3 is met as a present-tense fact, so this alone is not what I fail
the task on. It is why the FAIL matters: the mechanism that is supposed to keep
criterion 3 true has now been instance-shaped twice.

---

## 5 · Criterion 5 — substance yes, catalog no

Both directions reproduced live (§ 1b for short; a long row reports *"every
column after the extra `|` is shifted"*), the check sits above the
missing-columns bail-out, and the blank-spacer and escaped-pipe rows are
correctly **not** reported.

Two shortfalls, neither of which I fail the task on:

- **No catalog row and no `WHY` entry exist.** This repo's finding catalog is
  `reference/diagnose.md § Finding catalog` with the `WHY` table at
  `bin/perry-diagnose:976` and completeness enforced by
  `tests/test_diagnose.py:592`. That covers `perry-diagnose` ids
  (`CTX-01`, `LOAD-02`, …). `ragged-row` is a **`perry-lint`** code, and not
  one of `perry-lint`'s 52 codes has a catalog row or a `WHY`. Read as "like
  every other `perry-lint` finding", the clause is satisfied vacuously; read
  against the repo's actual catalog convention, it is not satisfied at all.
  The criterion is ambiguous on its own terms, so I decline to hang a FAIL on
  it and flag it for whoever writes the next criteria file.
- **The reported line is the section heading, not the row.** The destroyed row
  at line 21 reported as `perry/BOARD.md:15`, because `Finding(… line=start)`
  at `bin/perry-lint:659` uses the section's start and `tables()` does not
  carry per-row line numbers. On a board with a long `## P0` this points a user
  a long way from the row. Cosmetic against the criterion; real for the user.

---

## 6 · Mutations — five, all red, all on a copy

One line each, anchored by **line number** with the old text asserted before
the write, never `str.replace`. `__pycache__` cleared before every run; each
mutation applied to a fresh `cp -R` so no reverted file could be read from a
same-second `.pyc`.

| # | Reverted | Result |
|---|---|---|
| A | `bin/perry-lint:650` `if len(row) == len(header):` → `if True:` | **the destroyed board of § 1b returns to `✓ clean`**; 3 tests red |
| B | `viewer/tables.py:113` one-line clause → `if False:` | 4 tests red |
| C | `viewer/tables.py:120` round-trip clause → `if False:` | 1 test red — `test_an_empty_cell_list_is_refused`, exactly the single reachable trigger the builder documented |
| D | `viewer/tables.py:51` `split_row`'s escape branch → `if False:` | red at fixture build: `UnrenderableCell: cell 4: does not read back as itself` |
| E | `viewer/tables.py:143` `check_cell`'s refusal → old silent collapse | 2 red in `test_goals_writer.TestCreateAndAmendAgreeAboutWhatACellCanHold` |

Mutation A is the one that matters: it is the proof that the `ragged-row`
check, and not some other check, is what makes a hand-destroyed row visible.
Mutation E is the proof that the **previous** round's finding is genuinely
fixed and genuinely covered — which is why § 3a, its untouched sibling, is a
finding rather than a rerun.

Mutation C confirms the builder's own honest note: with the escape intact, no
reachable single-line value fails the round-trip clause, and
`render_row([])` is its only trigger. I agree with keeping the clause and I
agree the mutation table should read *10/11 red, one unreachable by design* —
a documentation defect, not a code one, and not what fails this.

**A flake, unrelated to this task, seen once and worth recording:**
`tests/test_decoration_changes_nothing.TestDecorationIsInvisible ::
test_every_reader_reports_the_same_thing_on_a_bolded_board (reader='perry-state')`
failed on an unmodified tree with the two payloads differing only in a
timestamp (`…:00:18` vs `…:00:19`). It compares two `perry-state` runs whole,
across a second boundary. Green on the next run. Not TASK-067's, but any round
that trusts a single suite run can be misled by it.

---

## What I did not check

- **`gimegime-pmo` and `PolyForge`.** The prior round measured 59 and 13/11
  `perry-lint` errors with zero `ragged-row`; I did not re-measure either
  external project, so the "precise, not a noise wall" claim is carried
  forward from round 2, not re-verified here.
- **The `.join()` blind spot's real-world reach.** I confirmed no `.join()`
  row-writer exists in `bin/` or `viewer/` today; I did not audit whether one
  could arrive via `packs/`, `templates/` or a project's own tooling.
- **Non-python writers.** `bin/perry-codex-preflight`, `perry-detect-host`,
  `perry-dispatch-limit`, `perry-update-check` and `perry-viewer` are bash. I
  grepped them for pipe-splitting and row-building and found none, but I did
  not run them.
- **`perry-migrate`'s row rewrites end to end.** I read `:533-537` (header
  widening through `render_row`/`split_row`) and `:690` (a `> Status:` header
  field, not a table row) and judged them by reading. I did not run a migration
  against a project with ragged rows.
- **Windows / CRLF.** `test_a_carriage_return_is_refused_too` covers a lone
  `\r` in a value; I did not test a file whose every line ends `\r\n`.
- **Concurrency.** Two writers appending to the same table under the project
  lock. Out of this task's scope and I did not attempt it.
- **Whether `--verification`'s empty cell** (the finding's own "what this does
  not cover") has moved. It has not — I saw `Verification` land empty on three
  rows I wrote on a scratch project — but it is explicitly deferred to
  TASK-061, so I did not pursue it.

---

## What would make this PASS

1. `viewer/tables.py:214` — `append_cell` calls `check_cell`, like
   `splice_cell` does, so a line break is refused rather than collapsed; and
   the fallback at `:219` stops escaping a value `render_row` is about to
   escape again. One test asserting the two write helpers refuse the same
   values (the mutation-E test next door is the shape).
2. `bin/perry-task:4012` and `bin/perry-goals:1409` — print the field.
   `UnrenderableCell.index` is already carried; the header is in scope at the
   raise site, and the CLI knows which flag it read. Criterion 1 asks for the
   field and the character; it gets the character.
3. `tests/test_row_integrity.py:270-272` — `rglob` both trees rather than
   `iterdir`/`glob`, so `bin/lib/` (which `TASK-065` is about to create, and
   which this task's criteria file names by path) is not invisible; and widen
   `HAND_ROW_RE` past the one lexical shape `perry-decide` happened to have —
   `f"| TASK-{n} | …"` is the same defect. Extend
   `test_the_guard_sees_a_file_that_did_not_exist_when_it_was_written` to plant
   into a **subdirectory**, which is the property the current probe does not
   have.

Items 1 and 2 are criterion 1 and are what the FAIL is for. Item 3 is criterion
3's enforcement and is why it will come back a fourth time if it is skipped.

```
=== VERDICT ===
task: TASK-067
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-067-finding.md
checked: both decisive tests PASS on copies — a new f-string writer and a new
         raw splitter under bin/ are BOTH caught (tree byte-identical after,
         6911-file manifest), and a hand-destroyed row now reports ragged-row
         where it used to report clean; criteria 2,3,4,6 met (criterion 4
         measured: 20 real rows plus an escaped-pipe row with NO event read
         identically with and without .perry/events.jsonl); every reader in
         bin/ and viewer/ enumerated and all reach split_row, zero bare-pipe
         row splits repo-wide; 5 mutations, 5 red, incl. disabling the
         ragged-row `if` which returns the destroyed board to `✓ clean`;
         suite 35 modules / 1304 tests green on the copy; perry-lint clean on
         the real repo
not-checked: gimegime-pmo and PolyForge baselines (carried from round 2, not
         re-measured); the 5 bash tools grepped but not run; perry-migrate's
         row rewrites read, not run; CRLF files; concurrent writers
proof: viewer/tables.py:214 — append_cell does .replace("\n"," ") and returns
       at rc=0, so append_cell("| a |", "x\n\ny") == "| a | x  y |" while
       check_cell("x\ny") raises UnrenderableCell on the identical value;
       criterion 1 says "Not encoded, not stripped silently". Same line's
       double escape: append_cell("| a | b", "x|y") stores 'x\\|y', which
       split_row reads back as 'x\|y', not 'x|y'. And bin/perry-task:4012 /
       bin/perry-goals:1409 print exc.value and exc.why but never exc.index,
       so `--next` and `--title` produce identical refusals and criterion 1's
       "naming the field" is unmet.
=== END VERDICT ===
```
