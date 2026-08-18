# V4 · round 4 — TASK-067, row integrity

> Reviewer: fresh context. I did not write any of this. I read the round-3
> review for claims to break, not for agreement.
>
> **Everything destructive was run on copies under scratchpad.** The live
> checkout was read only — `git log`, `git show`, `git blame`, `grep`, `wc`,
> and three `python3 bin/perry-lint` runs. Nothing was planted into it, nothing
> was `checkout`/`stash`/`reset`/`clean`ed, nothing was committed. `git status`
> on the live tree at the end of this round: **empty**, and `bin/` contains no
> `plant-*`, no `bin/lib/`, no `viewer/sub/`, no `perry-guardprobe`.
>
> **The tree moved three times under this round, and that is recorded rather
> than smoothed over.** HEAD was `a14ec19` when the round was dispatched,
> `fc8786a` when I started reading, `75e9196` when I took snapshot 1, and
> `d595097` when I finished. Between snapshot 1 and snapshot 2, `bin/perry-goals`,
> `bin/perry-task`, `bin/perry-diagnose` and `tests/test_goals_writer.py` all
> changed in the working tree; those changes are now committed as `d595097`.
> Snapshot 2 (`scratchpad/r4/tree2`) is **byte-identical to the live tree at
> `d595097`** for all eleven files under review — `viewer/tables.py`,
> `viewer/parsers.py`, `tests/test_row_integrity.py`, `bin/perry-lint`,
> `bin/perry-task`, `bin/perry-goals`, `bin/perry-decide`, `bin/perry-state`,
> `bin/perry-diagnose`, `bin/perry-conform`, `tests/test_goals_writer.py` —
> verified with `cmp`. Every finding below is re-measured on snapshot 2 unless
> it says otherwise, so nothing here describes a state that no longer exists.

Criteria: `perry/evidence/2026-08/TASK-067-finding.md § What must be true when
this is fixed`, six checkboxes. Nothing else was scored.

Baseline on snapshot 2: `python3 tests/parallel` → **43 modules · 1372 tests ·
76.7s · all green**. `python3 bin/perry-lint` on the live repo: **✓ clean**.

| # | Criterion | Verdict |
|---|---|---|
| 1 | refused at the writer, **naming the field** and the character | **NOT MET** — four sites, § 3 |
| 2 | the guard is the round trip, not a character list | met — § 6 M1/M2 |
| 3 | **every** reader goes through one splitter | met as a fact (enumerated, § 4); the guard enforcing it is **untested** and blind to three reader spellings |
| 4 | a row reads the same with the event log absent | met — measured, § 5 |
| 5 | `ragged-row` is a finding, both directions, at the row's own line | met — § 2; catalog/`WHY` clause still vacuous, not scored |
| 6 | the three repaired rows round-trip | met — 1224 rows, 0 failures, § 5 |

**Verdict: FAIL**, on criterion 1 — the same criterion round 3 failed on, at
four different sites, none of them the two round 3 named. Both decisive tests
(a) and (b) pass, and § 1 and § 2 say so in full before § 3 takes it apart.

---

## 1 · Decisive test (a) — thirteen plants, six caught, seven green

Planted into a copy (`scratchpad/r4/pl_t2`, an rsync of snapshot 2), then run
against `tests.test_row_integrity.TestEveryoneReadsTheRowTheSameWay`. Removed
afterwards; the pristine module is 26/26 green and the eight reviewed files
still checksum-match the live tree.

| planted | shape | guard |
|---|---|---|
| `bin/lib/deep/w2.py` | f-string row, **subdirectory two levels deep** | **red** |
| `bin/plant-w1` | `f"\| TASK-{n} \| {t} \| Coding Agent \|"` — literal first cell | **red** |
| `viewer/rowwriter.py` | **class method** returning `f"\| {a} \| {b} \|"` | **red** |
| `bin/lib/deep/r1.py` | `line.strip("\|").split("\|")`, **two levels deep** | **red** |
| `viewer/sub/deeper/r5.py` | **class method** reader, two levels deep | **red** |
| `bin/plant-r6` | `.strip('\|').split('\|')` — single quotes | **red** |
| `bin/plant-w4` | `"\| " + " \| ".join(cells) + " \|"` | green *(documented)* |
| `bin/plant-w5` | `"\| %s \| %s \|" % (a, b)` | **green** |
| `bin/plant-w6` | `"\| {} \| {} \|".format(a, b)` | **green** |
| `bin/plant-w7` | `"\| " + a + " \| " + b + " \|"` | **green** |
| `bin/plant-r2` | `line.strip("\|").split("\|", 6)` | **green** |
| `bin/plant-r3` | `re.split(r"\\\|", line.strip("\|"))` | **green** |
| `bin/plant-r4` | `SEP = "\|"` … `line.strip(SEP).split(SEP)` | **green** |

**Round 3's two reported blind spots are genuinely fixed.** A file in a
subdirectory *two* levels deep is now seen (round 3 planted one level down and
got nine greens), a class method is seen, and `HAND_ROW_RE` now catches an
f-string whose first cell is a literal.

**Seven shapes still walk through, and the two halves are not equally
serious.** The four writer shapes have a backstop: a writer that emits a
malformed row produces a *file* the `ragged-row` finding judges, which § 2
demonstrates. The three reader shapes have **no backstop at all** — a reader
that splits a well-formed row on a raw `|` produces no artifact, mis-reads
silently, and is exactly the defect the finding's § 2 is about ("the escape
reached exactly one of the splitters — and not the one the contracts read
through"). `.split("|", 6)`, `re.split(r"\|", …)` and a `SEP` constant are three
ordinary ways to write the one that bit. Round 3 planted all three and reported
them; the guard was widened for the two axes round 3 called out and not for
this one.

I do not fail the task on this: criterion 3 is written about the tree's state,
and § 4 shows that state is correct.

---

## 2 · Decisive test (b) — the row's own line, on four samples in three files

Round 3 found `ragged-row` reporting the section heading's line. Verified with
**four** ragged rows at four known, different lines and different distances
from their headings, because one sample cannot tell a constant offset from a
coincidence and two cannot tell it from a coincidence twice.

Hand-written board, no `render_row` anywhere in the fixture:

```
EXPECT line  7  | INT-1 | 2026-08-01 | a | b |            (## Intake, first data row)
EXPECT line 13  | TASK-900 | … | not_started |            (## P0, first data row)
EXPECT line 44  | TASK-903 | … | not_started | x          (## P0, 36 lines after the heading)
EXPECT line 70  | RISK-1 | ragged risk | 2026-08-01 |     (## Top risks, last section)

✗ perry/BOARD.md:13 [ragged-row] … has 4 cell(s) but its header has 7 …
✗ perry/BOARD.md:44 [ragged-row] … has 5 cell(s) but its header has 7 …
✗ perry/BOARD.md:7  [ragged-row] … has 4 cell(s) but its header has 6 …
✗ perry/BOARD.md:70 [ragged-row] … has 3 cell(s) but its header has 6 …
```

Four for four. And a second run on two rows at lines 24 and 34 (16 and 26 lines
past `## P0`) reported 24 and 34.

**Across files, not just BOARD.md.** On a copy of Perry's own state I chopped
the last two cells off the first data row of each of three files by hand:

```
✗ perry/BOARD.md:19     [ragged-row] row 'TASK-044 …' has 5 cell(s) …
✗ perry/OKR.md:49       [ragged-row] row 'KR-O1.1' has 3 cell(s) …
✗ perry/DECISIONS.md:12 [ragged-row] row '[ADR-001](…)' has 3 cell(s) …
```

All three exact.

**The original corruption shape.** A row ending mid-cell with no closing `|`,
a blank line, and the tail as a loose paragraph — the literal TASK-064 damage —
reports at its own line 12, and both directions (short and long) carry the
right explanatory half of the message. Mutation M3 (§ 6) is the proof that
`ragged-row` and nothing else is what makes it visible.

**One case that is not checked and is not a criterion:** a table under a
section the schema does not name at all is never visited, so a ragged row in
`## Unknown Perry Table` in `BOARD.md` is not reported. The criterion's
"headers Perry does not recognize" case — a *known* section with unknown
columns — is covered and I reproduced it.

---

## 3 · Criterion 1 is not met — four sites, enumerated

The criterion, verbatim:

> A cell value that would not read back as itself is **refused at the writer**,
> naming the field and the character. Not encoded, not stripped silently — the
> user asked to store something the format cannot hold.

Round 3 failed this on `append_cell` and on "the refusal never names the
field". `append_cell` is genuinely fixed (M5 in § 6 is red on three tests). The
naming half is not, and enumerating rather than re-checking the two sites round
3 named produced four.

### 3a · `bin/perry-decide` does not refuse at all, and loses data at rc=0

```
$ perry-decide new probe --title $'title one\n\ntitle two' --type architecture
perry-decide: wrote ADR-007                                             rc=0

perry/DECISIONS.md:
| [ADR-007](decisions/ADR-007-probe.md) | title one |  |  | — |

'title two' in DECISIONS.md: False
$ perry-lint --root <copy>
  ✓ clean
```

Three losses on one call, all silent: the second paragraph of the title is
gone, and the `Type` cell (`architecture`) and the `Date` cell are **empty**.
The mechanism, read after measuring:

- `bin/perry-decide:369` writes `f"# {aid} — {args.title}"` — the raw
  multi-line value — into the ADR file's H1.
- `bin/perry-decide:144` — `header_fields`' `break` on the first non-`>`,
  non-`#`, non-blank line — hits the spilled `title two` and abandons the
  `> Status: / > Type: / > Date: / > Deciders:` block wholesale.
- `bin/perry-decide:180` keeps only the first `# ` line, so `title` is
  `"title one"`.
- `bin/perry-decide:254` renders the index row from those values through
  `render_row`, which correctly accepts them: by then every value is one line.

`perry-decide` imports `render_row` (`:70`) and does **not** import or catch
`UnrenderableCell`, so there is no refusal channel to reach.

**This was already written down, with both halves and the fix.**
`perry/evidence/2026-08/review-queue-v4.md:79-82`:

> A line break in the same field is worse and silent: `--title $'line one\nline
> two'` writes an ADR whose own heading block is broken, and the index row comes
> back with `Type` and `Date` empty. rc=0, no warning …

and its "smallest fix": *"Route both through `viewer/tables.py § render_row` …
**and translate `UnrenderableCell` at each tool's `main`**, which is the wiring
`perry-task` and `perry-goals` already have."* The routing was done; the
translation was not, and the pipe half of the pair was fixed while the line-break
half — named in the same paragraph — was left. That is rule 1's failure shape
inside the task whose own finding document is about rule 1's failure shape.

### 3b · `bin/perry-task` names the **wrong** flag

Same offending value on two flags. `Title` is column 1 and `Next action` is
column 4, and `line_break_at` returns the *first* offending index, so the
exception is about `--title`:

```
$ perry-task add --title $'alpha\nbeta' --next $'alpha\nbeta' …
  [instrumented raise]  index=1 value='alpha\nbeta' field=''
perry-task: refused — --next was given 'alpha\nbeta', which contains a line break …
```

`bin/perry-task:4080-4085` walks a fixed name order — `("next", "title",
"deliverable", …)` — and takes the first argument whose value string-equals
`exc.value`. `next` precedes `title`, so it wins. The block's own comment says

> Exact match only — a near-miss would name the wrong flag, which is worse than
> naming none.

Exactness is not the property that prevents this. Two flags carrying the same
exact value is the case, and the message points the user at a flag that is
fine.

### 3c · `bin/perry-task` names **no** flag for any row-cell flag outside its list

The list at `:4080` has twelve names. `perry-task` has thirty-plus flags and
several free-text ones land in row cells and are not in it. Measured on a copy
of Perry's own board (rc=1, board byte-identical, `perry-lint` clean after):

```
add --owner      $'need one\n\nneed two'  → refused — was given '…', which contains a line break
add --role       $'…'                     → refused — was given '…', …
add --commitment $'…'                     → refused — was given '…', …
ask --needed     $'…'                     → refused — was given '…', …
```

Four flags, four refusals, no field named in any of them — the exact message
shape round 3 failed the task for, on flags round 3 did not try. `intake
--title` and `add --title`/`--next` (alone) do name their flag, which is why
checking the two flags the previous round used would have shown this fixed.

### 3d · `bin/perry-goals` names no field on any path, and `field` is dead code

`bin/perry-goals:1560`:

```python
where = f"{exc.field} " if exc.field else ""
```

`UnrenderableCell.field` is **never set anywhere in the repository**.
`viewer/tables.py:108 § naming()` — added for exactly this — has **zero call
sites**, and none of the four `raise UnrenderableCell(...)` sites
(`viewer/tables.py:153, 160, 181, 236`) passes `field=`. So `where` is always
`""`:

```
commit --promise $'a\n\nb'            → perry-goals: refused — was given '…', which contains a line break …
commit --promise X --to X (same X)    → identical
commit --promise ok --to $'a\n\nb'    → identical
```

Three paths, one message, no field. The comment above it states the design —
*"The flag is carried on the exception instead, set by whoever raises it"* — and
the wiring that would set it does not exist.

**This handler was rewritten during my round** (`d595097`, committed after my
snapshot 1). On snapshot 1 it was worse: the block was copied from
`bin/perry-task` into module scope where `args` is not defined, so **every**
`UnrenderableCell` refusal in `perry-goals` ended in

```
  File ".../bin/perry-goals", line 1496, in <module>
    _v = getattr(args, _name, None)
NameError: name 'args' is not defined
```

at rc=1 with nothing written — and `tests/test_goals_writer.py`'s
`test_the_amend_paths_refuse_what_create_refuses` stayed green because it
asserts only `returncode == 1` and that the file is unchanged, both of which an
unhandled traceback satisfies. I record it because it is the same defect one
step earlier and because it shows what the current fix was aimed at; the
verdict rests on the committed state, where the crash is gone and the field is
still not named.

### 3e · Adjacent, reproducible, and not scored

`--out-of-scope`, `--deliverable` and `--verification` still accept raw
newlines at rc=0 and write them verbatim into `journal/…md`, splitting a
`- **Out of scope**:` bullet across paragraphs. Round 3 reported the same shape
for two of the three. No value reaches a table cell, so criterion 1 does not
reach it — but it is the same category one file over, which is what the finding
says to state as a category.

Also unscored: `perry-task intake --title X` on a board whose `## Intake` table
lacks the `Ask`/`Request` columns writes an **empty** row at rc=0 and discards
the title. That is a missing-column drop, not a value that fails to round-trip,
so it is a different category from criterion 1.

---

## 4 · Criterion 3 — the fact holds; the guard that keeps it holding is untested

**Enumerated, not spot-checked.** Every file under `bin/` and `viewer/` that is
not `.md`/`.json`, swept for any `.split(` or `re.split(` touching a `|`:

```
bin/perry-decide:149   re.split(r"\s+·\s+|\s+\|\s+", …)   an ADR `> Status:` header line
bin/perry-knowledge:227 re.split(r"[\s,;·|]+", …)          a token list
bin/perry-lint:614     re.split(r"[|/,]", value)[0]        a value normalizer
bin/perry-lint:1183    re.split(r"[\s,;·|]+", …)           a token list
bin/perry-migrate:675  re.split(r"[|/,]", raw…)[0]         a value normalizer
bin/perry-task:250     re.split(r"\s+§|\s+\(", …)          not a pipe at all
viewer/parsers.py:1468 .split("|", 1)[0]                   a `Status:` header field
```

Zero row splitters. `split_row` call counts: `viewer/parsers.py` 13,
`bin/perry-task` 12, `bin/perry-goals` 3, `bin/perry-migrate` 3,
`bin/perry-lint` 2, `bin/perry-state` 2, `bin/perry-diagnose` 1,
`bin/perry-explain` 1. Every `" | ".join` / `"|".join` in the tree is a
separator row or a regex alternation. The two python tools outside `bin/` and
`viewer/` — `templates/knowledge-base/bin/kb-lint` and
`templates/ops/bin/deliverable-lint` — contain no pipe handling at all, and no
row splitter exists anywhere under `packs/`, `setup/`, `templates/`, `modes/`,
`goals/`, `decide/`, `state/`, `schema/`, `work/`, `reference/`.

**Criterion 3 is met.** And both of round 3's guard fixes are **blind guards**:

- Reverting `tests/test_row_integrity.py:293` `rglob("*")` → `glob("*")` — the
  precise fix for round 3's subdirectory finding — leaves **all 26 tests
  green**. The probe at `:343` writes `bin/perry-guardprobe`, a *flat* file,
  which `glob("*")` also sees. Round 3's own "what would make this PASS" said
  *"Extend `test_the_guard_sees_a_file_that_did_not_exist_when_it_was_written`
  to plant into a **subdirectory**, which is the property the current probe does
  not have."* The `_tools()` half was done; the probe half was not, so the
  property is asserted by nothing.
- Reverting `:266 HAND_ROW_RE` to round 2's narrow `f['"]\s*\|\s*\{` leaves
  **all 26 tests green** too.

By this repository's own definition — *"a guard with no test that can turn it
red is the thing this whole document is about"* — round 3's two guard fixes are
decorative today. A future edit that undoes either one is caught by nothing.

---

## 5 · Criteria 4 and 6, measured

**Criterion 4.** `perry-task list --json` over a copy of Perry's real 21-row
board, with `.perry/events.jsonl` present and then moved aside, comparing
`next_action`, `evidence`, `verification`, `title`, `status`, `owner`,
`priority`, `stage` per row:

```
ids equal: True (21)
rows differing on read fields: 0
keys that ever differ: blocked_by, created, startable, timeline, updated   ← event-derived, expected
```

And the case that would diverge — a hand-inserted row with **no event at all**,
carrying legally escaped pipes:

```
| TASK-0NN | escaped pipe row, no event | … | quotes a header \| ID \| Risk \| Opened \| and then some | — | V2 |

with    events → next_action 'quotes a header | ID | Risk | Opened | and then some'
without events → next_action 'quotes a header | ID | Risk | Opened | and then some'
```

**Criterion 6.** Rather than trusting `test_task_writer.py`, I round-tripped
every table row in every markdown file under `perry/` through
`split_row`/`render_row`/`split_row`:

```
rows scanned under perry/: 1224   failures: 0
```

TASK-065 and TASK-066 are on the board and round-trip. TASK-064 is closed and
`done` removes the row, so it is not there to check — the surviving two are.

---

## 6 · Mutations — seven, five red, **two green**

Each is one line, anchored by line number with the old text asserted before the
write, applied to a fresh `rsync` copy so no file is ever reverted in place, and
every copy has `__pycache__` removed before the run.

| # | file:line | reverted to | result |
|---|---|---|---|
| M1 | `viewer/tables.py:152` | `if False:` (line-break clause) | **13 red** across `test_row_integrity`, `test_one_line_break_rule`, `test_goals_writer` |
| M2 | `viewer/tables.py:157` | `if False:` (round-trip clause) | **1 red** — `test_an_empty_cell_list_is_refused`, its one reachable trigger, as the builder documented |
| M3 | `bin/perry-lint:677` | `if True: continue` (kills `ragged-row`) | **4 red**, incl. `test_each_finding_names_its_own_row`; the destroyed board of § 2 returns to `✓ clean` |
| M4 | `bin/perry-lint:694` | `line=start + 1` (drop the row offset) | **1 red** — `test_each_finding_names_its_own_row` |
| M5 | `viewer/tables.py:280` | `check_cell(raw)` → `raw.replace("\n", " ")` | **3 red** in `TestAppendCellObeysTheSameRule` |
| M6 | `tests/test_row_integrity.py:293` | `rglob("*")` → `glob("*")` | **GREEN — 26/26** |
| M7 | `tests/test_row_integrity.py:266` | round 2's narrow `HAND_ROW_RE` | **GREEN — 26/26** |

M4 is the one worth reading: round 3's finding was that `ragged-row` pointed at
the heading, and the fix *is* covered — reverting the offset arithmetic alone
turns `test_each_finding_names_its_own_row` red, and that test asserts two rows
at two different lines, which is the shape that would have caught the author's
own off-by-one. M6 and M7 are the counter-examples: the two guard fixes from
the same round have no such test.

---

## What I did not check

- **`gimegime-pmo` and `PolyForge`.** The "59 and 13 errors, zero
  `ragged-row`, precise not a noise wall" claim is now carried forward from
  round 2 through two rounds without re-measurement. I did not re-measure it
  either. Nobody has verified it since it was written.
- **`bin/perry-conform`.** It calls `render_row` (`:398`) and, like
  `perry-decide`, does not catch `UnrenderableCell`. Its cells are paths,
  a shape version and a route rather than user free text, so I judged it low
  reachability by reading and did **not** construct a path that would trigger it.
- **`perry-knowledge`.** It imports nothing from `tables`. I grepped it for
  row-building and row-splitting and found none; I did not run it.
- **The five bash tools** — `perry-codex-preflight`, `perry-detect-host`,
  `perry-dispatch-limit`, `perry-update-check`, `perry-viewer`. Grepped, not run.
- **`perry-migrate`'s row rewrites end to end.** I read `:423-424`, `:533-537`
  (header widening and row padding through `render_row`/`split_row`) and did not
  run a migration against a project with ragged rows.
- **Whether the seven green plants of § 1 can be reached from `packs/`,
  `templates/` or a project's own tooling.** I confirmed no such writer or
  reader exists in the tree today; I did not audit arrival paths.
- **CRLF / Windows.** `test_a_carriage_return_is_refused_too` covers a lone
  `\r` in a value; I did not test a file whose every line ends `\r\n`.
- **Concurrency.** Two writers appending to one table under the project lock.
- **`--verification`'s empty cell**, explicitly deferred to TASK-061 by the
  finding itself. Not pursued.
- **Everything that changed in `bin/perry-task` and `bin/perry-diagnose`
  between my two snapshots** (the `owner`/`role`-on-close change, `:1890`
  and `:2222`) — unrelated to TASK-067, read once, not reviewed.

## What would make this PASS

1. **`bin/perry-decide`** — catch `UnrenderableCell` at its `main`, and check
   `--title` before `:369` writes it into the ADR H1. The value that reaches
   `render_row` at `:254` has already been silently truncated, so guarding the
   render site alone changes nothing. `perry/evidence/2026-08/review-queue-v4.md:79`
   specified this two rounds ago.
2. **Set `exc.field` at the raise, or drop the pretence.** `naming()` exists,
   is documented as the mechanism, and is called nowhere; `perry-goals` reads
   `exc.field` and always gets `""`. Either the writers pass the column/flag
   down, or `perry-goals` grows the same (imperfect) value-matching
   `perry-task` has. As it stands one tool guesses and the other says nothing.
3. **`bin/perry-task:4080`** — the guess names the wrong flag when two flags
   carry one value, and names nothing for `--owner`, `--role`, `--commitment`,
   `--needed`. Matching by value cannot distinguish two arguments holding the
   same string; the column index is already on the exception and the header is
   in scope at the write site.
4. **`tests/test_row_integrity.py:343`** — plant the probe into
   `bin/lib/deep/` and into `viewer/sub/`, and add a probe for the widened
   `HAND_ROW_RE`. Both of round 3's guard fixes currently survive being
   reverted. And the three reader spellings that still walk through
   (`.split("|", n)`, `re.split(r"\|", …)`, a `SEP` constant) have no backstop,
   unlike the writer spellings, which `ragged-row` catches.

Items 1–3 are criterion 1 and are what the FAIL is for. Item 4 is criterion 3's
enforcement, and it is the fourth consecutive round in which the guard has been
found shaped around the previous round's instance.

```
=== VERDICT ===
task: TASK-067
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-067-finding.md
checked: all three decisive tests run on copies of snapshot 2, which is
         byte-identical to the live tree at d595097 for all 11 reviewed files.
         (a) 13 plants: subdirectory-two-levels-deep, class-method and
         literal-first-cell f-string shapes are all CAUGHT (round 3's two
         blind spots are really fixed); 7 stay green — writers `" | ".join`,
         `%`, `.format`, `+`-concat (backstopped by ragged-row) and readers
         `.split("|",6)`, `re.split(r"\|",…)`, a SEP constant (backstopped by
         nothing). (b) ragged-row names the ROW's line, 4 samples at 4 known
         lines and 4 distances from their headings (7/13/44/70), plus 3
         different state files (BOARD:19, OKR:49, DECISIONS:12), plus the
         original mid-cell-spill shape at :12. (c) flag naming is wrong or
         absent — see proof. Criterion 4 measured on 21 real rows plus an
         escaped-pipe row with NO event: 0 differ with/without
         .perry/events.jsonl. Criterion 6: all 1224 table rows under perry/
         round-trip, 0 failures. Criterion 3 enumerated by hand — zero row
         splitters outside split_row anywhere in the repo. 7 mutations: M1-M5
         red, M6 and M7 GREEN (reverting rglob->glob and the widened
         HAND_ROW_RE leaves all 26 tests passing, so round 3's own guard
         fixes are untested). Suite 43 modules / 1372 tests green;
         perry-lint clean on the live repo; live tree never written to.
not-checked: gimegime-pmo and PolyForge (now carried unverified for two
         rounds); bin/perry-conform's uncaught UnrenderableCell (judged by
         reading, not triggered); perry-knowledge and the 5 bash tools
         (grepped, not run); perry-migrate's row rewrites (read, not run);
         CRLF files; concurrent writers; whether the 7 green plant shapes can
         arrive from packs/ or templates/
proof: bin/perry-decide has no UnrenderableCell handler and no check before
       bin/perry-decide:369 writes a raw --title into the ADR H1, so
       `perry-decide new probe --title $'title one\n\ntitle two' --type
       architecture` exits 0 and writes
       `| [ADR-007](decisions/ADR-007-probe.md) | title one |  |  | — |` —
       second paragraph lost, Type ('architecture') and Date emptied by the
       `break` at bin/perry-decide:144 — with perry-lint reporting ✓ clean.
       bin/perry-task:4080-4085 matches exc.value back to the first flag in a
       fixed name order, so with the same value on --title and --next the
       exception carries index=1 (Title, instrumented) and the message says
       `--next`; and --owner, --role, --commitment and --needed are not in
       that list, so their refusals name no field at all. bin/perry-goals:1560
       reads exc.field, which is never set: viewer/tables.py:108 naming() has
       zero call sites and none of the four raise sites passes field=, so
       every perry-goals refusal prints "was given '…'" with no field.
=== END VERDICT ===
```
