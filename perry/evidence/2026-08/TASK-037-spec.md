# TASK-037 — `perry-goals`: the writer

> Source: `perry/design/DESIGN-005-state-and-contracts.md` § 5.4, § 6 step 3 (locked 2026-08-16)
> Dispatch mode: manual
> Executor: manual — **not dispatchable.** DESIGN-005 § 5.5 rates this the riskiest of the markdown three, and the risk is not one a test catches: `OKR.md` is prose the user argues with, and the failure mode is a file that still parses and no longer reads the way its author wrote it.
> Estimated cycle: large
> Subjective verification: does a written-back `OKR.md` still look like the user's document? Only a human can answer that; the byte-identity gate below is what makes the question answerable at all.
> Touches architecture: the hand-off contract — `goals` is the only writer of `OKR.md` and `phase/`
> Deployed: no

## The gate, before any write path ships

> Whatever else this task does, it does this first.

```
for every OKR.md and phase/<NNN>-*.md on this machine:
    load it, change nothing, write it back  →  byte-identical
```

Four real files exist to test against, and they are deliberately unalike:

| File | What it will break |
|---|---|
| `perry/OKR.md` | two versions (`## v1`, `## v2`) with the same date |
| `~/proj/gimegime-pmo/OKR.md` | `### Objective 1: …` with a colon, in Chinese; `### Anti-Goals` nested **inside** a version; versions `v2` and `v4` with no `v3` |
| `~/proj/aimark/perry/OKR.md` | an `## Input-quality overrides (v1)` section Perry's own template has never heard of |
| `tests/fixtures/sample-project/OKR.md` | an unfilled `## v2: YYYY-MM-DD` placeholder |

Not one of these is malformed. A writer that "cleans up" any of them has
failed, and `perry-lint` will not say so — the file still validates.

## The architecture decision this task must not get wrong

**Do not parse-then-render.** `perry-task`'s `Board` class carries the reason
in its own docstring: round-tripping through a parsed model normalizes
whitespace, alignment and column order, and every downstream reader keys on
those. The board writer edits lines in place and leaves everything it did not
touch untouched. `OKR.md` is more prose than `BOARD.md`, not less, so the same
rule applies harder.

**And do not copy `Board` to do it.** The table surgery — `split_row`,
`render_row`, `norm`, `ensure_columns`, `append_row`, `replace_row` — lives in
`bin/perry-task` today and nowhere else. Duplicating it into `bin/perry-goals`
creates two implementations of one rule, which is the single defect class the
last five review rounds kept finding — "the third positional-column parser"
was a finding in its own right.

There is already one instance to fold in while doing it: `perry-task`'s
`squash()` and `perry-lint`'s `norm()` are character-for-character the same
function under two names. (An earlier draft of this spec said `norm` existed
in three tools including `perry-diagnose`; `perry-diagnose` has `norm_title`,
which is a different function. Checked, not assumed — the claim was wrong in
the direction that would have made the extraction touch a file it has no
business touching.)

So the first commit of this task is an extraction, not a feature:

```
viewer/parsers.py   already shared, read side  (perry-goals imports it as P)
<new>               shared write side          ← the table surgery moves here
```

`perry-task` must come out of that extraction byte-identical in behaviour —
588 tests are the proof, and none of them should need editing. If any test
needs editing, the extraction changed something and the change is the bug.

## What it writes when the extraction is done

Per DESIGN-005 § 5.4:

| Writes | Refuses |
|---|---|
| `OKR.md` | a KR edge to an unresolvable id |
| `phase/<NNN>-<slug>.md` | a phase file for a phase that already exists |
| `phase/<NNN>-linkage.md` | |

`OKR.md § Commitments` is the first write path to build, because it is the one
with a live consumer and no writer at all: `modes/pipeline.md` and
`modes/queue.md` both name it as their spine, the schema specifies its six
columns, and `goals/reference/phases.md § commit <promise>` is an agent
procedure standing in for the tool. That procedure states the rules the tool
must implement, including the three refusals, and is the acceptance criteria
for **TASK-042** — which closes when `commit` stops being prose.

## Out of scope

- Step 4 (`BOARD.md` becomes a projection). DESIGN-005 § 6 puts it last and
  says explicitly that steps 1–3 must not wait for it.
- Rewriting any existing `OKR.md`. Migration is not part of a writer shipping.
- `phase/` rendering beyond what `plan-phase` already produces by hand.

## Verification

| Rung | Check |
|---|---|
| V2 | the extraction lands with 588 tests green and no test edited |
| V3 | byte-identity across all four files above, run as a test, not by eye |
| V3 | one targeted `commit` write changes exactly the lines it claims — asserted as a diff, not as a grep |
| V4 | fresh-context review |
| V5 | the user reads a written-back `OKR.md` and says it still reads like theirs |

Mutation discipline as everywhere else: each refusal verified by reverting it
and confirming the test goes red.
