# TASK-436 — result

> Status: in progress. Written incrementally; each section is committed as it
> is measured.
> Binary under test: `bin/perry-diagnose` at `70458893` (unmodified for every
> number in part 1).
> Scratch: two frozen trees, `git archive 7f43a11c` (RED) and
> `git archive 70458893` (GREEN), extracted to directories this agent owns.

## 0 · The two states reproduce

Confirmed before anything else, because the spec's GREEN state is "today's
tree" and today's tree is being written to while this runs. Both were frozen
with `git archive` first, so every number below is against a fixed input.

| state | commit | `user_load.dangling` |
|---|---|---|
| RED | `7f43a11c` | `['USER-920']` |
| GREEN | `70458893` | `[]` |

Same binary, same invocation, `perry-diagnose --json --root <tree>`. The spec's
description reproduces exactly, so the instability is not wider than described.

## 1 · What actually decides it

**It is not the reference domain at all. It is the definition domain.**

The one difference between the two trees that moves the verdict is a single
line of a single file: `perry/evidence/2026-09/TASK-436-spec.md:43` — a row of
this row's own spec, in the table that records the three refuted candidates:

```
| the second `USER-920` mention that day | delete it, re-run | still clear |
```

`bin/perry-explain.harvest` treats **the first id appearing in the first cell
of any markdown table row as that id's definition point.** The branch is
guarded only against a header row and a separator row: it reads
`header_index(cells)` and skips the block only when one of the first two
column names is literally `id`, `adr`, `#`, `task` or `design`. This table's
header is `| candidate | probe | result |`, none of which is in that set, so
the block is read as a register. `find_ids(cells[0])` returns `USER-920`, and
the row is recorded as `defined: perry/evidence/2026-09/TASK-436-spec.md:43`,
`kind: "row"`, `title: "delete it, re-run"` — the second cell, taken as the
title because no `TITLE_COLS` name is present either.

`split_dangling` then never sees the id at all. Its loop opens with

```python
for e in entries.values():
    if e["defined"] or not e.get("in_tracking_doc"):
        continue
```

so a defined id is dropped before any mark, any report line, any journal
mention is considered. That is why `USER-920` is absent from **both**
`dangling` and `dangling_in_reports` in GREEN: it was not exempted by the
report rule, it was never a candidate. Confirmed directly — in GREEN,
`dangling_in_reports` does not contain `USER-920`.

In one sentence a reader can check: *writing the spec that describes the
defect cured the defect, because the spec quotes the missing id in the first
cell of a markdown table and `harvest` reads any such cell as a definition.*

### The reduction

Each row is a tree built from RED or GREEN with exactly one substitution, run
against the same unmodified binary.

| tree | construction | `dangling` |
|---|---|---|
| `red` | `git archive 7f43a11c` | `['USER-920']` |
| `green` | `git archive 70458893` | `[]` |
| `r_journal` | RED, with GREEN's whole `perry/journal/` swapped in | `['USER-920']` |
| `r_spec` | RED, plus `TASK-436-spec.md` and nothing else | `[]` |
| `g_nospec` | GREEN, with `TASK-436-spec.md` deleted | `['USER-920']` |
| `m_cell2` | `r_spec`, with the id moved from cell 1 to cell 2 of that same row | `['USER-920']` |

Rows 4 and 5 are the necessary-and-sufficient pair: adding that one file to RED
is enough to clear it, and removing that one file from GREEN is enough to
restore it. Row 6 shows the decider is the *first cell* specifically, not the
file's presence and not the id's presence in the file — the id stays in the
same row of the same document and the finding comes back.

### The spec's recorded isolation does not reproduce

The spec states: *"Isolated again, one state file at a time: swapping in that
day's journal **alone** clears it."* Against these two frozen commits it does
not. `r_journal` — RED carrying GREEN's entire journal directory — still
reports `['USER-920']`. The journal is not the deciding input at `7f43a11c`
versus `70458893`.

This also explains why all three candidates in the spec's refutation table came
back "still clear", and why each probe was sound but aimed one file away. The
deciding line *is* "a second `USER-920` mention" — it is just not the one in the
journal; it is the one in the table that records the probe. Deleting the
journal's mention leaves the spec's table row standing, so the verdict does not
move, which is exactly what was observed.

### Enumeration, not sampling

Rather than trusting the single `defined` slot, every line in each tree that
`harvest` would accept as a definition of `USER-920` was enumerated, by
replaying `harvest`'s three definition branches (table row, heading, YAML
`- id:`) over every file `walk_md` yields:

- RED: **0** definition-shaped lines.
- GREEN: **1** — `perry/evidence/2026-09/TASK-436-spec.md:43`, the table row above.

So there is no second, competing cause hiding behind the first-wins `defined`
assignment.

### Size of the domain

The spec asks for the size of the input set, derived from the code. For the
*definition* half — the half that turns out to decide this — `harvest` reads
every file `bin/lib.walk_md` yields under the project root, and within each
file three structural positions: a markdown table row's first cell, a
heading's opening token, and a `- id:` YAML key, plus
`harvest_linkage_store`. There is no path allowlist and no notion of which
documents are registers; `perry/evidence/**`, `perry/journal/**` and every
other markdown file in the tree are read for definitions on equal terms with
`perry/BOARD.md`. The only exclusions are `SKIP_DIRS`, fenced code blocks, and
the header/separator guard named above — and `ILLUSTRATIVE_PARTS` /
`PROPOSAL_SECTION`, which gate `in_tracking_doc` and the *mention* scan, not
the definition branches.

That is the lowest-precedence input the Bound asks for: there isn't a
precedence order to be last in. First write wins (`e["defined"] or ...`), in
`walk_md` order, across the entire tree.
