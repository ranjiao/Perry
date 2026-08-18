# TASK-051 / TASK-052 — V4 review

> Reviewer: fresh context. I did not build any of this and did not read the
> builder's reasoning before running the tool.
> Reviewed at `feat/work-modes` @ `e866ca8`; the work under review is `ec958a1`.
> Rubric: `perry/evidence/2026-08/TASK-044-spec.md`, read in full.
> Everything below was run on **copies**. `~/proj/gimegime-pmo` and
> `~/proj/PolyForge` were snapshotted once each and never touched again. No
> Perry state file was written; this file is the only write to this repo.

| | Verdict |
|---|---|
| **TASK-051** — recognize a table by shape, not vocabulary | **PASS**, with two required corrections to what the code says about itself |
| **TASK-052** — assert what the file now says | **FAIL**, on one finding. The fix is one line and moves none of the numbers the two tasks are pinned to |
| **ADR-004** reopening criterion | **NOT MET.** All five guarantees hold. ADR-004 stands; TASK-045 and TASK-047 are not cancelled |

---

## 1 · What I ran, and what reproduced

| Check | Result |
|---|---|
| Suite | `python3 -m unittest discover -s tests` — **1006 tests, OK**, 2 skipped |
| gimegime-pmo baseline | **59 errors**, 28 warnings; **791** whole-tree ids across 454 `.md` files |
| PolyForge baseline | **13 errors** |
| Dry run | 582 lines. Complete unified diff per file. No summary, no count, no elision |
| **Dry run writes nothing** | 507 files sha256'd before and after: **0 changed, 0 added, 0 removed**. Asserted on bytes, not on code |
| **Dry run = real run** | `diff dryrun.txt apply.txt` differs in exactly four places: `dry run`/`apply`, `would migrate`/`migrated`, and the two post-run lines (restore point, declarations). **All 569 diff-body lines byte-identical** |
| Apply | **30 file(s) migrated, 4 left as found**; lint **59 → 15**; ids **791 → 806**, **0 lost**, +15 minted `SRC-*`, each declared as `field-added` |
| Losslessness, recomputed by me over the 30 changed files | **0** files lost a non-whitespace character · **0** lost an id · **0** changed a per-section row count |
| **Restore** | `perry-migrate restore <run-id>` → all **507 files byte-identical** to the pre-run hashes; the 30 conformance declarations withdrawn; the only residue is the restore-point JSON, which the module docstring says is deliberate ("the record that the run happened") |
| PolyForge | **Refused**, one sentence, and the 13 findings named as Perry's own — I checked: **all 13 are in `.perry/diagnose/2026-08-17-diagnosis.md`**, a file Perry wrote |
| Mutation | 8 mutations of my own choosing, run against a scratch copy: **8/8 KILLED** |

Every number the builder reported reproduces exactly. The previous reviewer's
last line ("791 whole-tree, +15 minted, 0 lost") is correct; I re-derived it
rather than repeating it.

### My mutations (all killed)

| Reverted | Tests that went red |
|---|---|
| `is_the_schemas_table` → `True` | `test_a_minority_of_the_schemas_names_is_not_a_vocabulary`, `test_a_table_sharing_no_column_with_the_schemas_is_not_widened` |
| `is_the_schemas_table` → the literal pre-TASK-051 rule (`>= 1` shared name) | `test_a_minority_of_the_schemas_names_is_not_a_vocabulary` |
| `meaning()` → `[]` | 4 tests |
| `reading_changed` → `[]` | 2 tests |
| `prose_rewritten` → `[]` | 1 test |
| `enum_claims` → `[]` | 8 tests |
| `negated()` → `False` | 3 tests |
| `cells()` → empty `Counter` | `test_a_cell_can_be_lost_while_every_character_survives` |

Every guard shipped in `ec958a1` has a test that dies without it. The
`cells()` mutation is the one the commit message says used to survive; it does
not survive now.

---

## 2 · TASK-051 — **PASS**

### The rule is right, and I checked the cost by building the excluded case

I wrote my own fixture — a board with a `| ID | Meaning |` legend under
`## P0 holding` and a real task table under `## P1` — and ran HEAD against it.
HEAD **refuses** the legend and names it:

```
✗ BOARD.md — left byte-identical.
    · [table-columns] table under section at line 3 is missing column(s)
      ['Title','Owner','Status','Next action','Evidence']; parsers key on
      these headers. Found: ['ID','Meaning']
```

Then I restored the pre-TASK-051 rule in a scratch tree and ran the **same**
fixture through it. The legend is widened, and `perry-task` reads rows that
were never tasks. That is the defect, reproduced independently of the suite.

**Is refusing a genuine minority-name board an acceptable cost? Yes — and
more defensibly than the docstring argues.** I built a plausible legacy board
(`| ID | Title | Owner |` under `## P0`) and ran it through both rules:

- **HEAD** refuses with an actionable `perry-lint` finding naming the three
  missing columns.
- **The old rule** widens it — and then **TASK-052's `reading_changed` refuses
  the file anyway**: `assertion: 2 task(s) Perry did not read before and reads
  now: [('<id>','Ship the parser','Alice','','P0'), ...]`.

So the class is refused either way. TASK-051 does not newly exclude it; it
moves the refusal earlier and replaces a cryptic assertion violation with a
lint finding a user can act on. That is a straightforward improvement, and the
two changes are genuine defence in depth rather than one rule stated twice.

### Two required corrections — the code understates its own cost

1. **The threshold is not "2 of 6".** `len(present) > len(cols) - len(present)`
   is a *strict majority*, so a 6-column spec needs **4** present: `| ID |
   Title | Owner |` (3 of 6) is refused too. For the 4-column phase-KR and
   risk tables it needs 3 of 4, so only a table missing exactly one column can
   ever be widened. For the 2-column `Tracks` spec in `.perry/config.md`,
   widening is **unreachable by construction** (missing 0 → skip; missing 1 →
   `1 > 1` is false). The docstring's "a genuine table written with only two of
   six names is refused … one hand edit away" should say: *at most two missing
   columns, and for 4-column tables at most one*.
2. **The blast radius is the file, not the table.** "the same outcome as any
   other table Perry does not recognise" is not the observed outcome: an
   unrecognized table leaves a residual, and a file with any residual is left
   byte-identical **in whole**. On my fixture the correctly-recognized `## P1`
   and `## P2` widenings were discarded along with the refused `## P0`
   ("0 file(s) would migrate, 1 left as found"). On the real project this is
   why `phase/004` keeps its `Status: 进行中` — a value
   `schema § migration.enum_aliases` already maps to `active` — because the
   `| 种子 | Owner | Deliverable |` table beside it was refused.

Neither changes the verdict. Both are sentences in a docstring that is
otherwise the best documentation in this repo, and they are the sentences a
future reader will rely on.

### One pre-existing crash this decision makes reachable — file separately

On a project where **every** file is blocked, `perry-migrate apply` prints
`restore point: None` and then dies:

```
File ".../bin/perry-migrate", line 1486, in render
    print(f"     undo with: perry-migrate restore {applied['run']}{r}")
KeyError: 'run'
```

`apply_plan`'s empty-plan early return omits `"run"`; `render` reads it
unconditionally. I confirmed the same lines exist at `ec958a1^`, so this is
**not** a TASK-051 regression — but TASK-051's refusal is what makes an
all-blocked project a normal outcome, and `apply` is the next thing that user
types. Smallest fix: guard the block on `applied.get("restore_point")`, or add
`"run": None` to the early return. One line, one test.

---

## 3 · TASK-052 — **FAIL**

### What passes

The three checks are real, and they are not the four losslessness assertions
renamed. `reading_changed` caught the TASK-051 defect class on a fixture I
wrote (above). `enum_claims` re-reads the retained value through the same
vocabulary and dies when `negated()` is reverted. `prose_rewritten` dies when
stubbed. Each docstring's stated blind spot is accurate — I checked all three
against the code rather than taking them on trust. `meaning()` refuses on the
same terms as `losslessness()`, and a refused file is left byte-identical.

### On TASK-068 specifically: correctly scoped, and I would not fail on it

The brief asks whether `prose_rewritten`'s insertion blind spot is honest
scoping or the same defect renamed. I measured it. I wrote an insertion-aware
check using only machinery `prose_rewritten` already has — the difflib
opcodes and the schema field-name set `is_header_block` builds — and ran it
over the pre/post images of all 30 migrated files.

**Of the 30, 26 had Perry join an existing `>` block. 24 qualified through the
field-vocabulary branch. Exactly 2 qualified only through "opens immediately
under the H1":**

| File | Author's block | Verdict |
|---|---|---|
| `knowledge/auto-research/auto_research_agent_全景综述_2026.md` | 3 lines of the Karpathy seed thesis, prose | **wrong** — TASK-068 |
| `knowledge/research/2026-07-10-…-survey-00-overview.md` | `> **系列**: …` / `> **方法与置信度声明**: …` | **right** — the author's own front matter |

Both blocks are bold-label-colon shaped. No vocabulary test separates them.
Narrowing that branch really is a design decision with a regression surface,
and `prose_rewritten` is the wrong place to make it. The blind spot is filed,
reproducible, and written into the function's own docstring. **On TASK-068
alone I would pass TASK-052.**

### The blocking finding: Perry writes a value its own reader cannot read

TASK-052's principle, in its own words, is *"the question is what the tools
that consume this file will see"*. `records()` honours that for
`viewer/parsers`, and its docstring says knowledge digests are invisible to it
because *"they have no records"*. That is true of `parse_board` and friends.
It is **not** true of `perry-lint --provenance`, which is a reader Perry
ships, which runs on exactly those files, and which nothing compares.

Measured on the migrated copy:

- Before migration: **15** `source-has-no-id` findings.
- After migration: **3** — and all 3 are files migration **gave** an id:
  three digests in `knowledge/`, named in the run output rather than
  quoted here — a concrete `SRC-<n>` in prose is a reference `LOAD-02` cannot
  tell from a live one.

All three carry `> **Id**：SRC-n`. `bin/perry-lint:894` anchors on
`^>\s*Id\s*[:：]`, which a bolded label does not satisfy. So migration mints
an id, writes it, reports `field-added: Id: SRC-<n>`, **declares the file
conformant**, and Perry's own provenance reader says the digest carries no id
and nothing can cite it. The file now says something untrue about itself, and
not one of the three meaning checks looks.

This is not a documented blind spot. It is an invariant the tool has already
written down twice and enforces on one branch only:

- `header_block_end`'s docstring: *"`perry-lint --provenance` matches
  `^>\s*Id\s*[:：]`, which a bolded `> **Id**:` does not satisfy — so a digest
  whose neighbours are plain must get a plain line."*
- `test_a_new_block_is_never_bolded`, whose docstring says the same thing.

The rule is enforced for a block Perry **starts**. For a block Perry **joins**,
`fix_missing_fields` bolds by majority vote of the neighbours — which is the
cosmetic answer to a question the code already knows is not cosmetic. The one
test covering the joined path (`test_a_real_header_block_is_still_joined`)
uses a `DIGEST` fixture whose block is plain, i.e. a block Perry generated.
That is the spec's governing sentence landing exactly where it was aimed: *a
test that migrates a board Perry generated proves nothing, because Perry's own
boards are already Perry-shaped.*

This is the fourth instance of the disclaimer defect class in a different
disguise — not "metadata in somebody's paragraph" but "metadata Perry can no
longer read" — and it is inside TASK-052's stated scope rather than beside it.

### Smallest fix, verified

Perry never bolds a field it writes. In `fix_missing_fields`:

```python
label = f"**{name}**" if bold else name     # →  label = name
```

I applied exactly that to a scratch copy and re-ran the whole migration on a
fresh copy of gimegime-pmo:

| | HEAD | with the fix |
|---|---|---|
| files migrated | 30, 4 left as found | **30, 4 left as found** |
| lint errors | 59 → 15 | **59 → 15** |
| `--provenance` findings | 15 → **3** | 15 → **1** |

The remaining 1 is a fact about the project: the author's own bolded
`**Source**:` line, which migration correctly does not rewrite.

`python3 -m unittest tests.test_migrate` is **73/73 OK** with the fix — which
is itself the finding: no existing test covers the joined-bold path at all.

**The fix moves none of the reference numbers TASK-051 and TASK-052 are pinned
to.** TASK-068's note gives, as one reason for leaving this class alone, that
"refusing the file would move the reference numbers TASK-051/052 are pinned
to." That reason does not apply here, and it should not be offered again: a
metric is not a thing a fix may be weighed against.

Better still, and the version I would actually land: add the fourth reading to
`meaning()` — **every header field migration writes must be found by the
reader that consumes it**, and refuse the file otherwise. That is the rule
TASK-067 already established one layer down for table cells (*"refuses a value
a row cannot carry … reads back as itself"*), applied to the header block. It
would have caught all three files without anyone knowing about bold.

---

## 4 · ADR-004, guarantee by guarantee

The reopening criterion is *"migration proves unbuildable to the five
guarantees"*. It is **not met**.

**1 · Dry run first, always — HOLDS.** The complete diff, 582 lines, no
elision. Writes nothing, proven on 507 file hashes rather than by reading the
code. Dry run and apply produce byte-identical diff bodies, and the design
makes divergence impossible rather than unlikely: the plan carries every
post-image and `apply` is `write_text(edit.after)`.

**2 · Nothing is lost — HOLDS.** Asserted by the tool and refused on failure,
never left to the reader. I recomputed all four assertions myself over the 30
changed files: 0 characters, 0 ids, 0 row counts lost. Prose in cells the
schema has nowhere to put is carried; widened rows are padded, not rewritten.
One qualification worth recording: gimegime-pmo's **BOARD.md was refused, not
migrated** (`Status = 半解` resolves to no enum value), so the hardest single
artefact named in the spec was planned losslessly and never written. The
guarantee held over the 30 files that were.

**3 · Recoverable — HOLDS.** The choice is made and argued: a restore point,
not a dirty-tree refusal, because gimegime-pmo is a local-only repo whose
state files are routinely uncommitted and `git checkout` cannot restore what
git never saw. The cost — this is state Perry now owns, holding a copy of the
project's writing — is stated. A dirty tree is reported, not refused. The path
is exercised, not described: 507/507 files byte-identical after `restore`, and
the declarations the run wrote were withdrawn with them.

**4 · The user declares — HOLDS.** Nothing in `bin/`, `work/`, `goals/`,
`decide/`, `modes/` or `setup/` invokes `perry-migrate`; `bin/perry-conform`
only *names* the command in its refusal text. `apply` records through
`perry-conform.declare(route="migrate")`, which re-checks each file rather
than trusting migration's word. The refusal matches `risk-add`'s shape — I
triggered it live: it names the count (3 errors), names both commands, and
points at the dry run. The § 3 finding qualifies what "conformant" *measures*,
not who declared it.

**5 · Partial migration is a state — HOLDS.** Per file, and "valid" is
defined rather than gestured at: *after any run, every file is either exactly
as its author left it, or conformant*. Verified both halves on the copy:
`OKR.md` conformant @v2 and writable, `BOARD.md` undeclared with the blocking
finding named, `perry-task list` still reading the whole board. The cost noted
in § 2 (a file is all-or-nothing) is the price of that definition and is the
right side of the trade.

**Verdict: ADR-004 does not reopen.** Migration is buildable to all five
guarantees and has been built to them. The tolerance branches do not come
back. **TASK-045 and TASK-047 are not cancelled** — they remain blocked on
TASK-044, which should stay blocked until the TASK-052 fix and the `render`
crash land.

---

## 5 · Summary of required work

| # | Against | Fix |
|---|---|---|
| 1 | **TASK-052 (blocking)** | Perry never bolds a field it writes (`label = name`), or — better — a fourth reading in `meaning()`: a field migration wrote must be found by the reader that consumes it. One test using a bolded author block |
| 2 | TASK-051 (doc) | Correct `is_the_schemas_table`'s stated cost: strict majority means *at most two missing columns*, one for 4-column tables, and never for 2-column ones |
| 3 | TASK-051 (doc) | Say that a refused table blocks the whole file, not just itself |
| 4 | TASK-044 / new | `render` crashes with `KeyError: 'run'` when no file is writable. Pre-existing; TASK-051 makes it reachable |
