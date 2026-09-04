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

