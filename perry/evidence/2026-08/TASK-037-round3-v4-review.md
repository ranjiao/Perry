# TASK-037 — V4, round 3

Criteria: `perry/evidence/2026-08/TASK-037-spec.md`. Under review: `bin/perry-goals`
as a writer, and `viewer/tables.py` (`check_cell`, `cell_spans`, `splice_cell`,
`append_cell`, `render_row`, `UnrenderableCell`).

All destructive work was done on a **copy** of the repository at
`…/scratchpad/perry-copy` (rsync of the working tree, `__pycache__` and `.git`
excluded). The repository under review was read only; `perry-lint` was the only
tool run against it. Every probe project was a throwaway temp directory.

The round-2 claim under test: *"the amend path contradicted the create path in
three places … Fixed by moving `cell_spans`/`splice_cell`/`append_cell` into
`viewer/tables.py` beside `split_row` and sharing one `check_cell`. A pipe
round-trips so it is escaped; a line break cannot, so it is refused."*

**The first half of that claim is false.** `render_row` does not call
`check_cell` and never has. There are two independently-written guards, they do
not agree, and the disagreement is reachable from the same two subcommands
round 2 was about. A third implementation — the literal `.replace("\n", " ")`
the commit message says it removed — is still in the file, four lines below the
docstring that indicts it.

---

## 1 · The enumeration (rule 1)

The category: *every path in every Perry writer that puts a user-supplied value
into a table cell.* Every such write in `bin/` and `viewer/` reaches a markdown
row through exactly one of three functions, all in `viewer/tables.py`. There is
no hand-built row carrying a user value anywhere — `grep` for `f"|`, `" | ".join`
and `"|".join` across `bin/` and `viewer/*.py` returns only separator-row
constructions (`perry-task:709,760,842,2722`, `perry-migrate:424,534`) and
regex alternations, none of which carry a value.

| # | function | the rule it applies to a value | callers that can reach it with user input |
|---|---|---|---|
| 1 | `render_row` — `viewer/tables.py:113,119` | refuse if `out.splitlines()` yields more than one line; then refuse if it does not round-trip through `split_row` | `perry-task` (12 sites: `add`, `status`, `next`, `prioritize`, `risk-add`, `intake`, `ensure_columns`, `new_section`…), `perry-goals` **create** (`append_table_row`, :369), `perry-decide` index (:254,262), `perry-conform` (:398), `perry-migrate` (:423,533,537) |
| 2 | `check_cell` — `viewer/tables.py:143`, called only from `splice_cell:202` | refuse if the value contains `\n` or `\r` | `perry-goals` **amend/close/miss**, via `Okr.set_cell` (:345) — six CLI paths: `--id --promise`, `--id --to`, `--id --by`, `--id --discharged-by`, `--close --discharged-by`, `--miss --reason` |
| 3 | `append_cell` — `viewer/tables.py:214` | **never refuses**; silently collapses `\n` to a space and escapes `\|` by hand | `perry-goals.widen` (:358,361) — today's two arguments are a schema-derived column name and `""`, so not reachable from a flag. Latent. |

Three implementations of one rule. Round 2 found four and removed one.

`grep -rn 'replace("\\n"' bin/ viewer/*.py` now returns exactly one
value-mangling site: `viewer/tables.py:214`. That is the shape of the round-2
defect, still in the tree, inside the module the round-2 commit created to
prevent it.

## 2 · The five probed values, on all ten cell-writing paths

Ten paths were run on a throwaway project for each of five values: a line
break, a lone carriage return, a pipe, an escaped pipe, and whitespace only.
Four create paths (`--promise`, `--to`, `--by`, `--discharged-by` on a new
row), four `--id` amend paths, `--close --discharged-by`, `--miss --reason`.

| value | create | amend / close / miss | agree? |
|---|---|---|---|
| `first\n\nsecond` | refused, rc 1 | refused, rc 1 | ✅ |
| `first\rsecond` | refused, rc 1 | refused, rc 1 | ✅ |
| `A \| B` | escaped, `A \\\| B` on disk, reads back `A \| B` | same | ✅ |
| `A \\\| B` (already escaped) | `A \\\\\| B` on disk, reads back `A \\\| B` | same | ✅ |
| `"   "` (whitespace only) | **refused, rc 1** | **rc 0, cell erased** | ❌ **F4** |

So the two characters round 2 named are fixed on both sides, and the pipe is
carried consistently. The fifth value is not, and two further character classes
that were not probed by round 2 are not either.

## 3 · Findings

### F1 — the "one shared check" is two checks, and they disagree at the CLI

`render_row` guards with `len(out.splitlines()) > 1` (`viewer/tables.py:113`).
`check_cell` guards with `"\n" in v or "\r" in v` (`viewer/tables.py:143`).
`render_row` does not call `check_cell`, and `check_cell` does not call
`render_row`. Python's `str.splitlines()` splits on eleven boundaries, not two:
it also splits on `\v`, `\f`, `\x1c`, `\x1d`, `\x1e`, `\x85`, `U+2028` and
`U+2029`.

For six characters, therefore, `perry-goals commit` gives two answers for one
value — the exact defect of round 2, on a different alphabet:

```
$ perry-goals commit --track ops --promise $'first<U+2028>second' --to Fin --by '3 days'
perry-goals: refused — the value 'firstU+2028second' contains a line break …   (rc 1)

$ perry-goals commit --id ops/1 --promise $'first<U+2028>second'
perry-goals: wrote OKR.md § Commitments — ops/1                                 (rc 0)
| ops/1 | ops | first<U+2028>second | Finance | 3d | active | — |
```

Reproduced identically for `\x0c` (form feed — what a paste out of a PDF
carries) and `\x85`. Unit-level, on the pristine copy:

| char | `render_row` (create) | `check_cell` (amend) |
|---|---|---|
| `U+2028`, `U+2029`, `\v`, `\f`, `\x85`, `\x1c` | refuses | **accepts** |
| `\n`, `\r` | refuses | refuses |

Which side is *right* is a second question — Perry's own reader splits on `"\n"`
(`bin/perry-goals:263`, `self.text.split("\n")`), so `U+2028` does not in fact
break a row and `render_row`'s refusal is the over-strict one. But the spec's
rule is not "be strict", it is *one rule, one implementation*, and a user who
gets a refusal from `commit` and a write from `commit --id` for the same
keystrokes is looking at the same bug they were shown last round.

**Mutation, both directions** (copy only; `__pycache__` cleared and the
whole-second boundary waited past before each run):

- **M2** — `viewer/tables.py:113` → `if False:`. The four **create** paths go
  green (they write a truncated row); all six amend paths stay red.
- **M1** — `viewer/tables.py:143` → `if False:`. All six **amend** paths go
  green (`| ops/1 | ops | first para` — the row truncated mid-cell, the tail
  spilled into the document, which is precisely the destruction
  `render_row`'s docstring recounts); the four create paths stay red.
  `tests.test_goals_writer` and `tests.test_row_integrity`: 2 failures.

Two guards, two mutations, no overlap. If they were one check, one mutation
would have reddened all ten paths.

### F2 — `append_cell` still carries the `.replace("\n", " ")` the commit says it removed

`viewer/tables.py:214`:

```python
    value = str(value).replace("\n", " ").replace("|", "\\|").strip()
```

It does not call `check_cell`. `append_cell("| a | b |", "x\ny")` returns
`'| a | b | x y |'` — collapsed, silently, which is the sentence `check_cell`'s
own docstring eleven lines above calls *"exactly why `render_row` refuses"*.

It also disagrees with itself about `|`, because the re-render branch
(`viewer/tables.py:219`) escapes a value that line 214 already escaped:

```
append_cell("| a | b |", "p|q")  →  '| a | b | p\|q |'      reads back as  p|q
append_cell("| a | b",   "p|q")  →  '| a | b | p\\|q |'     reads back as  p\|q
```

One value, two stored forms, decided by whether the row happened to end with a
pipe.

**Mutation M3** — `viewer/tables.py:214` → `value = str(value)`, deleting the
escaping and the collapse entirely: **36 modules · 1310 tests · all green.**
A green mutation is a finding either way, and here it is the plain one — the
function has no test coverage of its value handling at all. The round-2 commit
message states *"none of the three had any test coverage at all … The new class
covers the three amend paths"*; `append_cell` was moved and left uncovered.

Not reachable from a flag today (both call sites at `bin/perry-goals:358,361`
pass a schema-derived column name and `""`), so this is a latent third
implementation rather than a live data-loss path. It is still the category.

### F3 — `splice_cell` raises `NameError`, not a refusal

`viewer/tables.py:193`:

```python
        raise Refused(f"row has {len(spans)} cell(s); cannot write cell "
                      f"{index + 1}. Nothing was written")
```

`Refused` is not defined in `viewer/tables.py` and is not imported there. It is
`bin/perry-goals`'s own exception class (`bin/perry-goals:100`) and was left
behind when the function moved. Every out-of-range write therefore raises
`NameError: name 'Refused' is not defined`.

Reachable from the CLI on at least four invocations — a `## Commitments` table
with no `Status` column (the required-column check at `bin/perry-goals:1229`
runs on the **create** branch only, so `--close` and `--miss` walk past it with
`column_at(...) == -1`), and any row with fewer cells than its header:

```
$ perry-goals commit --close ops/1 --discharged-by done      # table has no Status column
  File ".../bin/perry-goals", line 345, in set_cell
    self.lines[index] = splice_cell(self.lines[index], column, value)
  File ".../viewer/tables.py", line 193, in splice_cell
    raise Refused(f"row has {len(spans)} cell(s); cannot write cell "
NameError: name 'Refused' is not defined
```

Also reproduced by `--miss`, and by `--id --discharged-by` / `--miss` on a
ragged row. The file is not written in any of them, so this is a bad refusal
rather than a bad write — but the class it was meant to raise says *"A refusal
is a first-class outcome, not a crash"*, and a `--json` caller gets a traceback
on stderr and nothing on stdout.

Zero coverage, and the suite proves it: line 193 is a guaranteed `NameError`
and 1310 tests are green.

### F4 — create and amend disagree about a whitespace-only value

The fifth probed value. `bin/perry-goals:1184-1187`:

```python
        if args.promise is not None:
            changes["Promise"] = args.promise
        if args.to is not None:
            changes["To whom"] = args.to
```

No `.strip()` test, where the create branch has one at `:1211` and `:1216`.

```
$ perry-goals commit --track ops --promise '   ' --to Fin --by '3 days'
perry-goals: refused — --promise is required. Nothing was written        (rc 1)

$ perry-goals commit --id ops/1 --promise '   '
perry-goals: wrote OKR.md § Commitments — ops/1                          (rc 0)
before: | ops/1 | ops | ship the vendor migration | Finance | 3d | active | — |
after : | ops/1 | ops |                           | Finance | 3d | active | — |
event : {"Promise": "   "}
```

Identical for `--to`. This is the round-2 sentence word for word — *one tool,
one value, two answers* — and it silently destroys the promise text, which is
worse than the collapse round 2 was raised for. There is no documented "clear
this cell" flag it could be read as. The event log records `"   "` while the
file records `""`, and `check_hand_edit` compares only `Status`, so nothing
downstream will notice.

The rules for `commit` are TASK-042's criteria rather than TASK-037's, so this
is not the load-bearing proof below — but it is the same category, it is in the
code under review, and it is what the fifth probe was for.

### F5 — widening corrupts a table whose rows have no trailing pipe

`append_cell` handles a missing trailing pipe explicitly
(`viewer/tables.py:215-219`). `append_separator_cell`
(`bin/perry-goals:233-235`) does not:

```python
    spans = cell_spans(line)
    last = line[spans[-1][0]:spans[-1][1]] if spans else " --- "
    return line.rstrip() + last + "|"
```

On a legal markdown table with no trailing pipes, `--miss` widens for
`Discharged by` and writes, rc 0, with no warning:

```
| Id | Track | Promise | To whom | By when | Status | Discharged by |   ← 7 cells
|---|---|---|---|---|------|                                            ← 6 cells
| ops/1 | ops | keep it up | Finance | 3d | missed | ran out of time |   ← 7 cells
```

The separator no longer matches the header, so a markdown renderer shows six
columns and drops `Discharged by` — the column the write existed to create.
`perry-lint --root` on that project reports nothing about it. This is the
spec's own stated failure mode: *"A writer that 'cleans up' any of them has
failed, and `perry-lint` will not say so."*

### F6 — the `--json` refusal contract diverges from `perry-task`

`bin/perry-goals:1403-1409` catches `UnrenderableCell` at **module level**,
outside `main()`, and ignores `args.as_json`. `bin/perry-task:4011-4021`
catches it **inside** `main()` and emits `{"refused": …}`. Measured:

```
$ perry-goals commit --id ops/1 --promise $'a\n\nb' --json
stdout: (empty)
stderr: perry-goals: refused — the value 'a\n\nb' contains a line break …    rc 1
```

Every other refusal on that tool emits `{"refused": …}` on stdout. The comment
at `bin/perry-goals:1404` describes itself as *"the twin in `bin/perry-task §
main`"*; it is not the twin, and an agent parsing `--json` sees a rc-1 with no
payload for exactly one refusal reason.

## 4 · What holds (rule 3 — re-derived, not inherited)

- **The byte-identity gate is real and ran.** All four named `OKR.md` files are
  present on this machine, including `~/proj/gimegime-pmo/OKR.md` and
  `~/proj/aimark/perry/OKR.md`; `tests.test_goals_writer.TestByteIdentity` runs
  4 tests and the out-of-repo case reports `ok`, not `skipped`.
- **`\n` and `\r` are refused on all ten cell-writing paths**, create and amend
  alike, with the wording `contains a line break — a markdown table row is one
  line`. The specific defect round 2 named is fixed for the two characters it
  named.
- **`|` round-trips on all ten paths**; an already-escaped `\|` is
  double-escaped on disk and reads back as `\|`, consistently on both sides.
- **The `squash`/`norm` fold-in landed.** `bin/perry-lint:186` is `norm = squash`,
  `viewer/parsers.py:38` imports it, `perry-task`/`perry-diagnose`/`perry-explain`/
  `perry-state` all import the same function; `tests/test_one_header_rule.py`
  asserts identity rather than equality.
- **No fourth positional-column parser** and no hand-built table row carrying a
  user value in `bin/` or `viewer/`.
- **Suite**: 36 modules · 1310 tests · ~117s on the copy. One red module,
  `test_decoration_changes_nothing` — a `perry-state` snapshot compared against
  itself across a one-second timestamp boundary (`…:50:45` vs `…:50:46`). It
  passes on re-run. Flaky, pre-existing, unrelated to TASK-037.
- **`python3 bin/perry-lint`** on the repository under review: `✓ clean`, rc 0.

## 5 · Criteria in the spec that are not yet implemented

Reported for completeness, not as the proof for the verdict — the spec calls
Commitments *"the first write path to build"*, so these may be deliberately
deferred, but they are in the spec's `Writes` / `Refuses` table and nothing in
`Out of scope` excludes them:

- `COMMANDS = {"list": None, "commit": cmd_commit}` (`bin/perry-goals:1276`) —
  there is no writer for `phase/<NNN>-<slug>.md` or `phase/<NNN>-linkage.md`.
- Neither declared refusal exists: *a KR edge to an unresolvable id*, and *a
  phase file for a phase that already exists*.

## 6 · What would make it pass

1. `render_row` and `check_cell` become one function — `render_row` calls
   `check_cell` per cell, or `check_cell` is defined as `render_row(["x", v])`
   — so that one mutation reddens all ten paths. A test that asserts the two
   agree over a character corpus including `U+2028`, `\f` and `\x85` is what
   stops this recurring on a third alphabet.
2. `append_cell` routes its value through `check_cell` and stops escaping
   twice, with a test that M3 (`value = str(value)`) turns red.
3. `viewer/tables.py` gets its own refusal type (or `splice_cell` raises
   `UnrenderableCell`), and a test covers the out-of-range branch.
4. The amend branch applies the same emptiness rule as the create branch, or
   documents an explicit clear.
5. `append_separator_cell` handles a missing trailing pipe the way `append_cell`
   already does, with the widened table's cell counts asserted.

---

=== VERDICT ===
task: TASK-037
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-037-spec.md
checked: on a COPY — all 10 cell-writing paths of `perry-goals commit` × 5 values
         (LF, lone CR, pipe, escaped pipe, whitespace-only); the write-side cell
         rule enumerated across bin/ and viewer/ (3 implementations, no
         hand-built rows); mutations M1 (tables.py:143), M2 (tables.py:113),
         M3 (tables.py:214) with __pycache__ cleared and the second boundary
         waited past; byte-identity gate confirmed running on all four real
         OKR.md; full suite 36 modules/1310 tests; `perry-lint` clean
not-checked: `perry-task`, `perry-decide`, `perry-conform`, `perry-migrate` write
         paths were read and enumerated but not run against the five values —
         they share `render_row`, so F1's create-side behaviour is theirs too;
         `phase/` writers (none exist); concurrency and the project lock; any
         non-macOS path; the historical "588 tests unedited across the
         extraction" claim
proof: viewer/tables.py:113 (`render_row`: `len(out.splitlines()) > 1`) and
         viewer/tables.py:143 (`check_cell`: `"\n" in v or "\r" in v`) are two
         separate guards — `render_row` never calls `check_cell`. Mutating :113
         greens only the create paths and mutating :143 greens only the amend
         paths, so `commit --promise $'first<U+2028>second'` is REFUSED on create
         and WRITTEN on `--id` — the round-2 defect verbatim on a different
         alphabet. viewer/tables.py:214 still reads
         `value = str(value).replace("\n", " ")…` with no `check_cell` call, and
         deleting that line entirely leaves all 1310 tests green.
         viewer/tables.py:193 raises `Refused`, which is not defined or imported
         in that module — `NameError` reaches the user from
         `perry-goals commit --close` on a table with no `Status` column.
=== END VERDICT ===
