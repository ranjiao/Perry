# V4 review — TASK-050, round 3

- **Reviewer:** fresh-context V4. Did not write this code, did not read the
  builder's reasoning before scoring.
- **Criteria:** `perry/evidence/2026-08/TASK-050-spec.md`, read first and in
  full. It is the only authority used below.
- **Under review:** `viewer/tables.py § squash`, and every header-cell
  resolution and row split in `bin/` and `viewer/`.
- **Pinned at:** `b658329` for the mutation work, re-confirmed at
  `3f6b95d` for every finding. `tests/test_one_header_rule.py` — TASK-050's
  own guard — is **byte-identical** across those two commits
  (`f62a3972…`), so nothing below is stale.
- **Method:** the tree was extracted with `git archive` into two scratch
  copies. **Nothing was planted, mutated or written in
  `/Users/bytedance/proj/Perry`.** Both copies were verified byte-identical to
  their commit, and free of extra files, at the end. The live checkout moved
  under me four times mid-round (`c24de3f → b658329 → 3f6b95d`, plus
  uncommitted work in `bin/perry-explain` by another round); that is why
  everything is pinned.

**Verdict: FAIL**, on the category, for the third time — and the decisive test
the spec prescribes is the one that fails.

---

## The decisive test: plant a new reader

The spec's `How to check it` is normative: *"Add a file under `bin/` that
resolves a header its own way and confirm the guard reports it."*

Two plausible new readers were planted at `3f6b95d`, each resolving a header
cell by ``.strip("*` ").lower()`` — the exact rule this task exists to
eliminate — and each carrying its own splitter:

- `bin/perry-standup` — a one-line standup over `## P0`, top level.
- `bin/lib/rows.py` — shared row helpers, i.e. the directory TASK-065 exists
  to create.

Result, whole suite, `__pycache__` cleared, past the second boundary:

| guard | verdict |
|---|---|
| `tests/test_one_header_rule.py` — **TASK-050's guard** | **6 tests OK — green** |
| `tests/test_decoration_changes_nothing.py` — criterion 5 | 3 tests OK — green |
| `tests/test_row_integrity.py` — TASK-067's guard | **red**, `['bin/lib/rows.py:5', 'bin/perry-standup:11']` |

The only guard that fires is the one belonging to a different task, and it
fires on the **splitter**, never on the header rule. TASK-050's guard reports
nothing about a new reader that resolves a header cell its own way. That is the
spec's decisive test, and it is green. **Criterion 1 fails.**

### Three separate blind spots, isolated one at a time

`test_one_header_rule` is category-shaped in *one* dimension only —
`READERS` iterates `bin/` rather than naming files, which is a real
improvement over the previous round. Everything else about it is
instance-shaped.

**(a) It cannot see a subdirectory.** The same file, byte for byte, moved:

```
bin/lib/rows.py          →  6 tests OK        (green)
bin/perry-rows-probe     →  FAILED (failures=2)
```

`READERS` is built from `(PERRY_HOME / "bin").iterdir()` filtered by
`is_file()` (`tests/test_one_header_rule.py:42-46`). `iterdir()` does not
descend, so `bin/lib/` is invisible. This is **the identical category defect
that commit `3f6b95d` had just fixed in `tests/test_row_integrity.py`** —
"the guard could not see a subdirectory — three rounds, one category" — left
unfixed one file over, in the guard whose whole subject is that category.

**(b) It matches a spelling, not a shape.** `SECOND_RULE`
(`test_one_header_rule.py:56-58`) requires a list comprehension whose iterable
is literally named `cells` or `split_row(`. Measured, on files that otherwise
import both `split_row` and `squash`:

| planted form | guard |
|---|---|
| `low = [c.strip("*` ").lower() for c in cells]` | **red** (2 failures) |
| `keys = [h.strip("*` ").lower() for h in header]` | **green** |

Renaming one local variable is enough. Nothing about the second form is
adversarial — `header` is the more natural name for a header row.

**(c) The complement test is gated on the file already being fixed.**
`test_every_reader_that_resolves_headers_reaches_the_one_rule` skips any file
whose source does not contain `split_row(`. A reader that carries its own
splitter is therefore excluded from the header check entirely — and *"carries
its own splitter AND its own header rule"* is precisely the combination this
task's history says co-occurs: the fourth file nobody had named
(`bin/perry-explain`) carried both. The guard exempts exactly the shape that
bit.

**(d) `viewer/` is still a hardcoded one-file list.** `READERS` adds
`viewer/parsers.py` by name (`test_one_header_rule.py:46`). A new
`viewer/board_digest.py` with both defects: **green**. Criterion 1 says
"every table reader in `bin/` **and `viewer/`**"; half of that is enumerated,
half is a list of one.

---

## A fifth surviving second implementation, found by enumeration

Not "the next instance" — an enumeration over the whole population. I walked
every `.lower()`/`.casefold()` call in `bin/` and `viewer/` by AST (111 sites),
then narrowed to the 47 that sit inside a function that also splits a row, then
classified each by reading. Exactly two are header-cell questions. One is live:

**`viewer/parsers.py:232` — in the file the first pass claimed to have
unified.**

```python
cells = [c.strip("` ") for c in split_row("|" + m.group(1) + "|")]
...
rel, ver, declared, route = cells[0], cells[1], cells[2], cells[3]
if rel.lower() in ("file", "path") or not rel:
    continue           # the header row
```

The comment says `# the header row` in as many words. The rule is
``strip("` ")`` then `.lower()` — backticks and spaces, **not asterisks**. So
a bolded header is not recognised as a header, is parsed as a declaration, and
fails the `\d+` version check.

Behaviour, on a copy of Perry's own project with only that one header line
changed:

```
| File | Shape version | Declared | Route |        →  13 declarations, 0 unreadable
| `File` | `Shape version` | … |                   →  13 declarations, 0 unreadable
| **File** | **Shape version** | … |               →  13 declarations, 1 unreadable
```

Through the CLI, at `3f6b95d`:

```
$ perry-conform status --root <bolded copy>
   ✗ .perry/conformance.md:13 unreadable row: | **File** | **Shape version** | **Declared** | **Route** |
```

A correctly-formed file, reported broken, because someone bolded a header —
which is the sentence criterion 5 exists to make false. `perry-lint` still
says `✓ clean`, so the two tools disagree about the same file.

Neither TASK-050 guard sees it, and each misses it for its own reason:

- `SECOND_RULE` matches a comprehension; this is a scalar membership test.
  (`test_decoration_changes_nothing`'s own docstring already records a
  reviewer finding the scalar form and says the behavioural module is the
  answer to it — the behavioural module does not reach this file either.)
- `test_every_reader_…_reaches_the_one_rule` passes because `parsers.py`
  contains the string `squash` somewhere else.
- `test_decoration_changes_nothing` decorates `perry/**/*.md` and
  `.perry/config.md` (lines 112, 115). **`.perry/conformance.md` is never
  decorated**, and `perry-conform` is not among its three `READERS`.

Verified green on both guards with the tree otherwise pristine.

**Smallest change that would pass:** `if squash(rel) in ("file", "path")`, and
add `.perry/conformance.md` to what the behavioural module decorates plus
`perry-conform status` to its readers.

---

## Criterion 5's guard is null against the rule that actually shipped

This is the finding behind the finding, and it explains why four copies
survived three rounds.

`test_decoration_changes_nothing.bold_headers` wraps **whole cells**:
`Default rung` → `**Default rung**`. On whole-cell decoration the two rules
**agree**:

| cell | `squash` | ``strip("*` ").lower()`` | |
|---|---|---|---|
| `**ID**` | `id` | `id` | agree |
| `**Next action**` | `next action` | `next action` | agree |
| `` `Status` `` | `status` | `status` | agree |
| `**Default** rung` | `default rung` | `default** rung` | **diverge** |
| `Next  action` | `next action` | `next  action` | **diverge** |

Measured end to end. Restoring the real historical defect at
`bin/perry-state:422` — `low = [c.strip("*` ").lower() for c in cells]`, the
line the previous round's fix replaced:

```
tests/test_decoration_changes_nothing.py   Ran 3 tests   OK      ← green
tests/test_one_header_rule.py              FAILED (failures=2)
```

The behavioural guard — the one the module's docstring says catches "a sixth
spelling nobody thought of … without anyone updating a regex" — is **green with
the defect restored**. It catches a bare `.lower()` (mutating
`bin/perry-state:157` to `cells[0].lower()` does turn it red) and cannot catch
``.strip("*` ").lower()`` at all, because its fixture never produces a cell
where the two differ.

So the two guards' blind spots line up the wrong way: exactly one of them can
see the rule that actually shipped four times, and that one is the one a new
reader walks past.

---

## What passes

**Criterion 2 — `perry-lint`'s `norm` IS `squash`, by identity. PASS.**
`bin/perry-lint:186` is `norm = squash`;
`test_the_norm_alias_is_the_same_object_and_not_a_second_copy` asserts
`assertIs`. Mutated to a distinct wrapper (`def norm(s): return squash(s)` —
same behaviour, different object): `test_one_header_rule` red. Live.
(`bin/perry-task` also defines a `norm`, at line 984; it is the glossary alias
layer and calls `squash` internally, which is the localized→English step the
spec puts out of scope.)

**Criterion 3 — no reader carries its own row splitter. PASS.**
`viewer/tables.py § split_row` honours `\|`. Enumerated the population: no
table-row split on a raw pipe survives in `bin/` or `viewer/`. The three
remaining raw-pipe splits are not table rows and each says so in a comment —
`viewer/parsers.py:1459` (prose after a `Status:` field),
`bin/perry-migrate:675` and `:1165` (`**Status:** canonical | author's words`
header-field lines), `bin/perry-decide:149` (a `>` meta line). Mutating
`bin/perry-explain:227` back to `raw.strip().strip("|").split("|")` turns
`test_row_integrity` red, and the planted files above are both caught. The
guard for this criterion is genuinely category-shaped as of `3f6b95d`.

**Criterion 4 — value normalizers keep their own rules. PASS.**
Of the 47 normalizations inside row-splitting functions, 45 are value
normalizers, path/filename checks, search queries or `##`-heading tests. None
is flagged. `SECOND_RULE`'s narrowness is a correct *judgement* about scope;
the defect is that the same narrowness is also how it misses (b) above.

**Criterion 5 — a decorated header resolves. PASS for the four tools named,
FAIL for the file above.** Perry's own board and OKR, bolded whole-cell and
partially (`**Next**  action`), produce byte-identical payloads from
`perry-state --json`, `perry-lint --json`, `perry-diagnose --json`,
`perry-explain --all --json` and `perry-task list --all --json`. Because a
matching pair proves nothing on its own, I checked the fixture was live:
`perry-diagnose.md_table` resolves `**Next**  action` → `next action` at
`3f6b95d` and **loses the column** under the mutation. `parse_tracks` is
covered behaviourally by the existing module's own synthetic config. The
failing tool is `perry-conform`, which criterion 5 does not name — but the
sentence it asserts is about decorated headers resolving, and one does not.

---

## Two null results, reported because they are results

**The whole-project criterion-5 comparison is largely vacuous, and I nearly
reported it as a pass.** Mutating each fixed site and re-running the same
plain-vs-decorated comparison over Perry's own project gave an **identical
payload every time**: `perry-state:422`, `perry-state:157`,
`perry-diagnose:1306`, `perry-explain:228`, `perry-lint:1203` are all null on
Perry's own state. Perry's `.perry/config.md` has no `## Tracks` table at all,
so `parse_tracks`' header path is never exercised by the fixture that
`test_decoration_changes_nothing` runs on. Only mutating `squash` itself moves
`perry-lint` and `perry-task`. A "the payloads match" result on this project is
not evidence about these sites.

**`bin/perry-explain`'s header keys are all single words** (`id`, `adr`,
`task`, `design`, `title`, `status`, `chosen`, …), so `squash` and
``strip("*` ").lower()`` are observationally equivalent there today: mutating
line 228 changes no output I could construct. The fix is still right, and the
payload at that site was the **splitter** (line 227), which is reachable and is
guarded.

## Scoped observations, not findings

- `viewer/parsers.py:1944` — `if first.lower().startswith("adr") and "id" in
  first.lower()` is a second header-row test in `parse_decisions`. It is dead:
  `in_table` only becomes true after the separator row, so the header never
  reaches it. Verified — plain and bolded `DECISIONS.md` both yield
  `['ADR-001']`. A latent sixth spelling; harmless today.
- The glossary invariant is still unpinned. All **174** declared spellings in
  `schema/state-schema.json § i18n` satisfy `squash(v) == v.strip().lower()`,
  so lowering the glossary keys is observationally identical to squashing them
  — and no test asserts it. The previous round recommended this; it did not
  land.
- The `generated_at` flake in `test_decoration_changes_nothing` (red roughly
  one run in five, message `reads a bolded header differently`) is real; I hit
  it twice. Commit `8028371` fixed it during this round by measuring unstable
  keys instead of naming them. Not a finding against TASK-050.

## What I ran

- `python3 tests/parallel` at baseline on both pinned copies (1310 tests at
  `b658329`, 1314 at `3f6b95d`, `✓ all green` both) and after every mutation.
- Nine mutations, each anchored by line number, `__pycache__` cleared and
  `sleep 1.2` past the whole-second boundary, each reverted from a pre-taken
  copy and SHA-verified against `git show <commit>:<file>`:
  `perry-lint:186` (red), `perry-state:422` (red), `perry-state:157` (red),
  `perry-diagnose:1306` (red), `perry-explain:228` (red), `perry-explain:227`
  (red), `viewer/tables.py:245` (red), plus the two null-result sweeps above.
- Five planted files, all in scratch copies, all removed: `bin/perry-standup`,
  `bin/lib/rows.py`, `bin/perry-rows-probe`, `bin/perry-probe-b`,
  `viewer/board_digest.py`.
- AST enumeration of all 111 lowercasing sites in `bin/` + `viewer/`, narrowed
  to the 47 inside row-splitting functions, each classified.
- `perry-conform status` and `perry-lint` on plain / backticked / bolded copies
  of `.perry/conformance.md`.
- `perry-lint` clean (exit 0) on both scratch copies at the end.

## not-checked

- **Localized headers.** `**状态**`, `编号`, and any localized→English mapping.
  The spec puts it out of scope, and no Chinese-language board was exercised.
- **`bin/perry-goals`.** It imports `squash` at 14 sites and reads correct; I
  did not mutate any of them individually.
- **`viewer/serve.py`.** It reaches tables only through `parsers`, so it is not
  an offender today — but it is invisible to the header guard for the same
  reason `viewer/board_digest.py` was.
- **The write side.** `render_row`, `append_cell`, `splice_cell` — TASK-067's
  subject, and it changed under me at `3f6b95d`.
- **`bin/perry-knowledge`, `bin/perry-decide` header-*field* parsing.** Both
  normalize `> **Status:** …` keys with their own rule. That is a different
  category from a header *cell* and the spec does not reach it; I classified
  but did not test them.
- **Windows paths, non-UTF-8 state files, and any locale other than the
  machine default.**
- **Whether the four fixed sites are correct for *values*.** I checked header
  resolution only; the ``[c.strip("*` ") for c in split_row(s)]`` value pass
  that precedes it at `perry-state:152/407` and `perry-diagnose:1301` was read
  (and `squash(strip("*` ", c)) == squash(c)` for all inputs, so it does not
  affect the header key) but not fuzzed.

=== VERDICT ===
task: TASK-050
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-050-spec.md
checked: criteria 2,3,4 pass with live mutations (9 mutations, each reverted
         and SHA-verified); criterion 5 verified on 5 tools with a
         mutation-proven-live fixture; the header-rule category enumerated by
         AST over all 111 lowercasing sites in bin/ and viewer/; worked on two
         git-archive copies, never the live tree
not-checked: localized headers; bin/perry-goals' 14 squash sites individually;
             the write side (render_row/append_cell); header-FIELD parsing in
             perry-decide and perry-migrate; Windows paths
proof: the spec's decisive test is green — bin/perry-standup and bin/lib/rows.py,
       both resolving a header by `.strip("*` ").lower()`, leave
       tests/test_one_header_rule.py at "Ran 6 tests, OK" at 3f6b95d. The same
       file byte-for-byte is red at bin/perry-rows-probe and green at
       bin/lib/rows.py, because READERS uses `(PERRY_HOME/"bin").iterdir()`
       (tests/test_one_header_rule.py:42-46) and does not descend — the
       subdirectory blind spot 3f6b95d had just fixed in the sibling guard.
       And a fifth live copy survives at viewer/parsers.py:232,
       `if rel.lower() in ("file", "path")  # the header row`: bolding
       .perry/conformance.md's header makes `perry-conform status` report
       `✗ .perry/conformance.md:13 unreadable row` against a correct file,
       with both TASK-050 guards green.
=== END VERDICT ===
