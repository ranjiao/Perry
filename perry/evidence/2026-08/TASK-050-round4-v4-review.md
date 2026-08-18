# V4 review — TASK-050, round 4

- **Reviewer:** fresh-context V4. Did not write this code. Read the criteria
  first, then the round-3 review, and scored against the criteria only.
- **Criteria:** `perry/evidence/2026-08/TASK-050-spec.md` — the only authority
  used below.
- **Under review:** `viewer/tables.py § squash`, every header-cell resolution
  and row split in `bin/` and `viewer/`, and `tests/test_one_header_rule.py`.
- **Pinned at:** `fc8786a` for every measurement. The live checkout moved twice
  during the round (`fc8786a` → uncommitted `bin/perry-diagnose` → `75e9196`).
  Re-confirmed at `75e9196`: `tests/test_one_header_rule.py` is **byte-identical**
  across both commits (`c4f0aebd…`), and `viewer/tables.py`, `viewer/parsers.py`,
  `bin/perry-state`, `bin/perry-lint`, `bin/perry-explain` are byte-identical
  too. Only `bin/perry-diagnose` changed, in `scan_work_modes` (track
  attribution), and an AST sweep of the changed file found **no new
  header-cell resolution** — the new `.lower()` sites are `t.get("track")`
  comparisons, which are value normalizers. **Nothing below is stale.**
- **Method:** two scratch copies (`git archive HEAD | tar -x`, and an `rsync`
  of the worktree for the moving-tree check). **Nothing was planted, mutated
  or written in `/Users/bytedance/proj/Perry`.** Every plant and every mutation
  happened in a copy; each mutation was reverted from the pristine copy and
  byte-verified with `assert`, `__pycache__` cleared and `sleep 1.2` past the
  whole-second boundary on both the mutate and the revert. Both copies were
  verified byte-identical (`diff -r`) at the end.

**Verdict: FAIL**, on the category, for the fourth time. Round 3's decisive
test now passes for the two shapes round 3 happened to plant. **Nine of
seventeen new readers I planted leave the guard entirely green**, including one
planted under `bin/` — which is the spec's `How to check it`, verbatim, coming
back green again.

---

## The decisive test: plant readers the guard has not seen

The spec's `How to check it` is normative: *"Add a file under `bin/` that
resolves a header its own way and confirm the guard reports it. A guard that
only knows the files it was written against is the defect this task exists to
close — verify the category, not the instances."*

Seventeen readers were planted, one at a time, in a copy at `fc8786a`. Each
resolves a header cell with ``.strip("*` ").lower()`` — the exact rule this
task exists to eliminate. Result is `tests/test_one_header_rule.py` alone,
`__pycache__` cleared, past the second boundary, plant removed after each run.

| # | shape | planted at | guard |
|---|---|---|---|
| 1 | list comp over `cells`, **subdirectory two levels deep** | `bin/lib/parse/rows.py` | red (2) |
| 2 | **class method**, list comp over `cells` | `viewer/board_digest.py` | red (2) |
| 3 | **dict comprehension** | `viewer/columns.py` | red (1 — complement only) |
| 3b | dict comprehension, file also calls `squash` on values | `viewer/columns.py` | **GREEN** |
| 4 | **generator expression** | `viewer/genread.py` | red (1 — complement only) |
| 4b | generator expression, file also calls `squash` | `viewer/genread.py` | **GREEN** |
| 5 | **helper whose header parameter is named `titles`** | `bin/lib/keys.py` | red (1 — complement only) |
| 5b | same helper, file also calls `squash` | `bin/lib/keys.py` | **GREEN** |
| 6 | list comp over `cells`, **no `.py` suffix and no shebang** | `bin/perry-rowdump` | **GREEN** |
| 6c | *the same bytes* + `#!/usr/bin/env python3` | `bin/perry-rowdump` | red (2) |
| 6d | *the same bytes* + `.py` suffix | `bin/perry-rowdump.py` | red (2) |
| 6e | *the same bytes* + `# -*- coding: utf-8 -*-` as line 1 | `bin/perry-rowdump` | **GREEN** |
| 7 | list comp whose **iterable is named `row`**, + `squash` | `viewer/rowread.py` | **GREEN** |
| 8 | **`return [ … ]`** over `cells` (no `=`), + `squash` | `viewer/hdrread.py` | **GREEN** |
| 9 | **multi-line comprehension** over `cells`, + `squash` | `viewer/mlread.py` | **GREEN** |
| 11 | **scalar header-row test** (`if cells[0].strip("*` ").lower() == "id": continue`), + `squash` | `bin/lib/scalar.py` **and** `viewer/scalar_reader.py` | **GREEN** (both) |
| 12 | private `re.split` splitter, list comp over `cells` | `bin/lib/rowsplit.py` | red (1) |

Nine green. Shapes 5b, 6, 6e, 11 are **under `bin/`**, which is the directory
the spec's own instruction names.

The two dimensions round 3 measured are genuinely fixed: `READERS` now walks
the tree (`rglob`, `tests/test_one_header_rule.py:69-77`), so `bin/lib/` and
new `viewer/` files are visible — shapes 1 and 2 are red where round 3 had them
green. That is a real improvement and it is not what this round is about.

### Why: the change to `SECOND_RULE` is not the change that was claimed

The handoff says the pattern *"matches any loop-subject identifier instead of
the literal `cells`"*. Half of that is true, and it is the half that does not
matter. `tests/test_one_header_rule.py:90-92`:

```python
SECOND_RULE = re.compile(
    r"=\s*\[[^\]]*?\.lower\(\)[^\]]*?\bfor\b\s+\w+\s+in\s+"
    r"(?:cells|cols|columns|header|hdr|split_row\()")
```

The **loop variable** is now `\w+` — any identifier. The **iterable**, which is
the thing that has to be a row, is still a five-name allowlist. So `for c in
cells` is caught and `for c in row` is not (shape 7): renaming the row, not the
cell, still walks past. `parts`, `head`, `fields`, `titles`, `first_row` — all
green.

Three more constraints in the same expression, each one a shape:

- **`=\s*\[` — a list comprehension assigned to something.** A dict
  comprehension (3b), a set comprehension, a generator expression (4b) and a
  `return [ … ]` (8) all fail to match. Shape 8 is one refactor away from the
  current code: `bin/perry-state:422` moved into a `def header_keys(cells):
  return [...]` becomes invisible.
- **One line.** The regex is applied per line
  (`test_one_header_rule.py:117-120`), so a comprehension broken across lines
  by a formatter is invisible (9) — over `cells`, the allowlisted name.
- **A comprehension at all.** A scalar header-*row* test (11) is not matched.
  This is the shape of the fifth copy that round 3 found by AST sweep
  (`viewer/parsers.py:241`). That one site is red only because
  `TestTheFifthCopy` is a hand-written behavioural test **about that one
  file**; the general rule still cannot see its like, in `bin/` or `viewer/`.

The complement test (`test_every_reader_that_resolves_headers_reaches_the_one_rule`)
is what caught 3, 4 and 5 — and it caught them only because those files never
mention `squash`. Add one `squash()` call on a **value** — which is what
`bin/perry-state`, `bin/perry-diagnose` and `bin/perry-explain` all legitimately
do — and the complement is satisfied while the header is still resolved by a
second rule. That combination is not adversarial; it is the shape of every
already-fixed file in the repository.

### The opposite failure: yes, the narrowing opened a hole

The prompt's specific question — *is a Python file with no `.py` suffix and no
shebang now invisible?* — **is yes, measured.** `_is_python`
(`tests/test_one_header_rule.py:42-66`):

```
line 52:  if p.suffix == ".py":  return True
line 54:  if p.suffix:           return False
line 57:  return "python" in p.read_text(...).split("\n", 1)[0]
```

Shapes 6 / 6c / 6d / 6e isolate it to one line of one file: **the same bytes**
are green at `bin/perry-rowdump`, red the moment `#!/usr/bin/env python3` is
prepended, red with a `.py` suffix, and green again when line 1 is a coding
declaration instead. The `diff` between the green file and the red one is one
added line.

Two consequences, and I grade them differently:

- **Real but narrow: no suffix and no shebang.** Every `bin/` script today
  carries a shebang, and a Python module without `.py` cannot be `import`ed —
  though Perry loads exactly such files by `SourceFileLoader` (this guard does
  it twice, at `:139` and `:171`), so "not importable" is not a defence here.
  A file whose first line is a docstring, a `# -*- coding:` line, or a licence
  header is invisible.
- **Wider: any non-`.py` suffix returns `False` without reading anything**
  (line 54). `viewer/` currently holds only `.py`, so nothing is missed today,
  but the rule is "trust the extension", which is the extension-list rule the
  docstring says it was written to avoid.

This is a genuine hole and it is the **smaller** of the two findings. Shapes
3b/4b/5b/7/8/9/11 need no unusual filename at all.

---

## A green mutation on a site TASK-050 itself fixed

Rule 2 says a green mutation is a finding either way. `bin/perry-state:157`:

```python
if len(cells) >= 2 and cells[0] and squash(cells[0]) != "term":
```

reverted to `cells[0].strip("*` ").lower() != "term"` — a second header rule,
restored in the glossary reader, in the file this task fixed:

```
tests/test_one_header_rule.py          Ran 8 tests   OK        ← green
tests/test_decoration_changes_nothing  Ran 3 tests   OK        ← green
python3 tests/parallel                 42 modules · 1363 tests · ✓ all green
```

**The whole suite is green with a second header rule put back.** In fairness to
the fix: for a *single-word* header cell the two rules cannot diverge in the
direction that loses a column — `squash("**Term**")` and
``"**Term**".strip("*` ").lower()`` are both `term` — so this mutation is
observationally null today. That is exactly why it matters: the site is
correct, nothing observable would break, and **nothing at all would report it
if someone changed it back.** It is the scalar shape from plant 11, occurring
in live code.

For contrast, mutating the other fixed sites individually:

| site | mutation | `test_one_header_rule` |
|---|---|---|
| `bin/perry-state:422` | `[squash(c) …]` → ``[c.strip("*` ").lower() …]`` | red (2) |
| `bin/perry-state:157` | scalar `squash()` → scalar strip/lower | **green** |
| `bin/perry-diagnose:1306` | list comp | red (1) |
| `bin/perry-explain:228` | list comp | red (1) |
| `bin/perry-lint:206` | `norm = squash` → `def norm(s): return squash(s)` | red (1) |
| `viewer/parsers.py:241` | `squash(rel)` → ``rel.strip("` ").lower()`` | red (2) |
| `viewer/tables.py:75` | `\|` escape branch → `if False:` | (row-integrity guard red) |

`tests/test_decoration_changes_nothing.py` was **green under every one of
these six mutations**, which is round 3's finding about that module unchanged:
its fixture bolds whole cells, where the two rules agree, so it is null against
the rule that actually shipped.

---

## What passes

**Criterion 2 — `perry-lint`'s `norm` IS `squash`. PASS.** `bin/perry-lint:206`
is `norm = squash`; `assertIs` at `test_one_header_rule.py:171`. Mutated to a
behaviour-identical wrapper: red. Live.

**Criterion 3 — no reader carries its own row splitter. PASS.** Enumerated
independently: exactly one raw pipe split survives in `bin/` + `viewer/` —
`viewer/parsers.py:1468`, taking the text before an inline `|` in a `Status:`
prose field, which is not a table row and says so at `:1464-1467`. The
`re.split` sites (`bin/perry-decide:149`, `bin/perry-migrate:675`,
`bin/perry-lint:614`, `bin/perry-lint:1183`, `bin/perry-knowledge:227`) split
on character *classes* in prose and field values, not on table rows.
`split_row`'s `\|` escape branch is live: `viewer/tables.py:75` → `if False:`
turns `tests/test_row_integrity.py` red.

**Criterion 4 — value normalizers keep their own rules. PASS, and the guard is
correctly narrow here.** My own AST sweep: **112** `.lower()`/`.casefold()`
sites across 13 Python files in `bin/` + `viewer/` (I count one more than round
3's 111 because `viewer/parsers.py:687` folds twice on one line). Of those, 23
sit inside a function that also splits a row. Classified by reading: every one
is a value normalizer (`Status`, `Outcome`, `mode`, `stage`, `wip`), a
`##`-heading test, a path/id check, or a document header-*field* key. None is
flagged and none should be. Cross-checked shape-first (sweep 2): every
comprehension in the tree whose element case-folds iterates aliases, paths,
dirs, stage names or ids — **not row cells**. No sixth live copy found.

**Criterion 5 — a decorated header resolves. PASS for the five tools, on a
fixture I proved live.** Two copies of Perry's own project, one plain and one
with **181 header rows partially decorated** (`Next action` → `**Next**  action`
— bolding half the cell and doubling the space, which is where the two rules
diverge; whole-cell bolding is where they agree and is why the existing
behavioural fixture is null). `perry-state --json`, `perry-lint --json`,
`perry-diagnose --json`, `perry-explain --all --json`, `perry-task list --all
--json` and `perry-conform status` produce identical payloads.

Because a matching pair proves nothing on its own, I made the fixture live and
verified it moves:

| site mutated | fixture reacts? |
|---|---|
| `viewer/tables.py:305` (`squash` itself) | `lint`, `task`, `conform` DIFFER |
| `viewer/parsers.py:241` (the fifth copy) | `conform` DIFFERS |
| `bin/perry-state:422` (`parse_tracks`) | `state` DIFFERS — **only after** I added a `## Tracks` table to `.perry/config.md`; Perry's own has none |
| `bin/perry-diagnose:1306` (`md_table`) | `diag` DIFFERS — **only after** I added an `OKR.md § Commitments` table with a `By when` column; Perry's own has none |
| `bin/perry-explain:228` | never moves — its header keys are all single words |
| `bin/perry-state:157` | never moves — single-word key, see above |

So criterion 5 is verified behaviourally and live for `perry-state`,
`perry-diagnose`, `perry-lint`, `perry-task` and `perry-conform`. **Round 3's
`perry-conform` finding is genuinely fixed:** `perry-conform status` on a
`.perry/conformance.md` whose header is `| **File** | **Shape**  version | … |`
now reports `13/14 declared and matching` with no `unreadable row`, and the
mutation at `viewer/parsers.py:241` brings the failure straight back.

One cosmetic difference, reported as a non-finding: `perry-lint`'s
`missing column(s)` message echoes the header cells **verbatim** — `Found:
['**Id**', '**By**  when', …]` versus `['Id', 'By when', …]`. The resolved
missing-column list is identical, so the header resolution agrees; only the
quoted-back text differs, which is arguably right.

---

## Null results and scoped observations, reported because they are results

- **The whole-project criterion-5 comparison is vacuous on Perry's own state
  until you add tables to it,** exactly as round 3 warned. I nearly reported a
  pass off a fixture that could not have failed: with Perry's real files,
  mutating `perry-state:422` and `perry-diagnose:1306` changes **nothing**.
  Both needed a table added to the fixture before the comparison meant
  anything. Any future round comparing payloads on Perry's own project should
  assume the answer is null until it proves otherwise.
- **`viewer/parsers.py:1953`** — `if first.lower().startswith("adr") and "id"
  in first.lower()` is a second header-row test in `parse_decisions`, still
  present and still dead: `in_table` only becomes true after the separator row,
  so the header never reaches it. Verified behaviourally — `| ADR | … |`,
  `| ADR id | … |` and `| **ADR** id | … |` all yield `['ADR-001']`. A latent
  sixth spelling; harmless today, and invisible to the guard (plant 11's
  shape).
- **The glossary/alias invariant is still unpinned, and still holds.**
  `bin/perry-state:283`, `bin/perry-diagnose:1260`, `bin/perry-migrate:740` and
  `bin/perry-lint:1277` `.lower()` the *declared* schema spellings and compare
  them against `squash`ed header cells. I checked all **85** strings under
  `schema/state-schema.json § i18n.columns` and `§ i18n.headings`:
  `squash(v) == v.strip().lower()` for every one, so the two sides agree today.
  Nothing asserts it. Two rounds have now recommended pinning this; it has not
  landed.
- **`bin/perry-diagnose` is being edited by another round** (track attribution,
  `scan_work_modes`). Its uncommitted state made 4 tests in `tests/test_diagnose.py`
  red in a worktree copy; that work landed as `75e9196` and the suite is green
  again. Not a TASK-050 finding, and the sweep confirmed it added no header
  rule.

## What I ran

- `python3 tests/parallel` on the pinned copy at baseline (**42 modules · 1363
  tests · ✓ all green**) and again at the end after every plant and mutation
  had been reverted (green, and `diff -r` clean against the pristine copy).
- **My own AST sweep**, twice, not trusting round 3's: (1) every
  `.lower()`/`.casefold()` call in `bin/` + `viewer/` with its enclosing
  function and whether that function splits a row — 112 sites, 13 files, files
  selected by `ast.parse()` succeeding rather than by suffix or shebang, so it
  is deliberately broader than the guard's own filter; (2) shape-first — every
  list/set/dict/generator comprehension in the tree whose element case-folds,
  regardless of what the iterable is called, plus every `.strip()` whose
  literal contains `*`, `` ` ``, `#` or `_`. Both sweeps re-run against the
  live worktree including the uncommitted `bin/perry-diagnose`.
- **Seventeen planted readers**, each in a copy, each removed, each run against
  the guard alone with `__pycache__` cleared and 1.2s past the second boundary.
- **Seven mutations**, each anchored by line number, each reverted from the
  pristine copy and byte-verified by `assert`; one (`perry-state:157`) also run
  against the **full 1363-test suite**.
- Plain-vs-partially-decorated payload comparison across six tools, on a
  fixture whose liveness was established by mutation for four of the six sites.
- `python3 bin/perry-lint` on the pristine copy: `✓ clean`, exit 0.

## not-checked

- **`bin/perry-goals`' 12 `squash` sites and `bin/perry-task`'s 41 `norm` /
  7 `squash` sites individually.** They read correct and the AST sweep found no
  second rule in either, but I mutated none of them one at a time. `perry-task`
  is where a hole would hurt most; it is the write side's reader.
- **`bin/perry-explain:228` and `bin/perry-state:157` behaviourally.** Both are
  observationally null on any input I could construct, because their header
  keys are single words and the two rules cannot diverge there. Verified by
  guard mutation only.
- **Localized headers.** `**状态**`, `编号`, and any localized→English mapping.
  The spec puts it out of scope; no Chinese-language board was exercised.
- **Header-*field* parsing** — `bin/perry-decide:153 header_fields`,
  `bin/perry-migrate:675`, `bin/perry-conform:282`. Each normalizes a
  `> **Status:**`-style document field with its own rule. A different category
  from a header *cell*; classified, not tested.
- **The write side.** `render_row`, `append_cell`, `splice_cell` — another
  task's subject.
- **`viewer/serve.py`.** Reaches tables only through `parsers`, so not an
  offender today; not exercised.
- **Whether the fixed sites are correct for *values*.** I checked header
  resolution only.
- **Windows paths, non-UTF-8 state files, and any locale other than the
  machine default.**
- **Whether any of the nine green plants corresponds to code someone actually
  intends to write.** They are demonstrations that the category is unguarded,
  not predictions.

=== VERDICT ===
task: TASK-050
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-050-spec.md
checked: criteria 2,3,4,5 all PASS with live mutations (7 mutations, each
         reverted and byte-verified); criterion 5 verified end-to-end on 6
         tools against a fixture proven live by mutation for 4 of 6 sites;
         the category enumerated by my own two-pass AST sweep (112 lowercasing
         sites, 13 files, files selected by ast.parse rather than by suffix);
         17 readers planted; worked entirely on scratch copies, never the live
         tree; pinned at fc8786a and re-confirmed byte-identical at 75e9196
not-checked: bin/perry-goals' 12 and bin/perry-task's 48 squash/norm sites
             individually; localized headers; header-FIELD parsing in
             perry-decide/perry-migrate/perry-conform; the write side; Windows
             paths; perry-explain:228 and perry-state:157 behaviourally
             (observationally null — single-word keys)
proof: criterion 1 still fails. tests/test_one_header_rule.py:90-92 —
       `SECOND_RULE` widened the loop VARIABLE to `\w+` but left the ITERABLE a
       five-name allowlist (`cells|cols|columns|header|hdr|split_row(`) and
       still requires `=\s*\[` on one line, so nine planted readers that
       resolve a header by `.strip("*` ").lower()` leave the module at
       "Ran 8 tests, OK": a dict comprehension, a generator expression, a
       helper whose header parameter is named `titles`, a list comp whose
       iterable is named `row`, a `return [...]`, a multi-line comprehension,
       and a scalar header-row test planted at BOTH bin/lib/scalar.py and
       viewer/scalar_reader.py — four of them under bin/, which is the
       directory the spec's `How to check it` names. Each carries one
       `squash()` call on a VALUE, which is what every already-fixed file in
       the repo does, and that alone satisfies the complement test.
       Independently, tests/test_one_header_rule.py:52-57 `_is_python` returns
       False for any non-`.py` suffix and, with no suffix, only for "python" in
       line 1: the SAME BYTES are green at bin/perry-rowdump, red at
       bin/perry-rowdump.py, red with a shebang added, and green again with
       `# -*- coding: utf-8 -*-` as line 1. And bin/perry-state:157 —
       `squash(cells[0]) != "term"` — reverted to a second rule leaves all
       1363 tests green.
=== END VERDICT ===
