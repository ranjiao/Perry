# TASK-119 — result

> Date: 2026-08-21 · Executor: claude-subagent · Merged locally
> Branch: `coding/task-119-linkage-writer` · Cycle time: ~45 min
> 10 files, +1810/−32. `bin/perry-goals` +983 — the `link` writer, its resolution
> and its four operations. Plus `tests/test_linkage_writer.py` (31 cases).

## The in-place write, and the two gates that make it trustworthy

`Register` holds the file as **lines** and never re-renders it. The parsed model
comes from `parsers.parse_linkage` — **the same reader Perry and `perry-lint`
use, no second parser** — and a separate line locator finds each `- id:` entry.

Two gates run before any write:

1. **the locator and the reader must agree** about every objective, KR, project
   and agent in the file, or it refuses rather than editing by line number;
2. **`verify` re-reads the edited text** with `parse_linkage` and compares it
   against the before-model with the one intended mutation applied — anything
   else is *"this writer's bug, not the file's. Nothing was written."*

A list append splices **inside the one line** (`tasks: ["A"]` → `tasks: ["A",
"B"]`), matching the register's own quoting and separator style.

**The file is read as bytes, not `read_text()`.** Text mode is
universal-newlines and would have silently converted a CRLF register to LF on
the first append. That is the kind of thing this project has been bitten by
before and it was caught in design, not in review.

**Byte-identity proved** on copies of this repository's `002-linkage.md` and
`001-linkage.md` and the shipped fixture (which quotes nothing and uses a block
`agents:`): line count unchanged, exactly two lines differ (`tasks:` and
`updated:`), and **putting those two old lines back reproduces the original file
byte for byte**. Refusals and no-ops are asserted the same way: `after ==
before`.

## The refusal, verbatim

```
perry-goals: refused — 'shared name' does not resolve to exactly one KR — it
matches 2 by name or alias: P-O1.1 (project PROJ-A "shared name", active);
P-O1.2 (project PROJ-B "another name", active). Attribution resolves by declared
edge, then exact Project id, then registered alias, and never by resemblance
(reference/okr-linkage.md § The one rule). Ask the user which KR TASK-500 serves
and re-run with that KR id. Nothing was written
```

Zero candidates lists the phase's KR ids instead; a match only on a `dropped`
Project **says so** rather than reporting "not found"; a task already under
another KR is refused naming both, and **`perry-lint`'s own `check_frontmatter`
is re-run afterwards** to assert `linkage-task-single-kr` was not created.

## `current: 0` is gone, and the writer never invents a number

Removed from `goals/state/linkage_TEMPLATE.md`, replaced by a comment saying
why. The writer writes **neither `target` nor `current`** on any of its four
paths — asserted as text over every added line. A register made from the
template and then linked reports `current: null`, `state: "unasserted"`.
Re-inserting the default reddens four tests.

## The finding it refused to absorb, and it is schema-gated

`goals/reference/linkage.md` requires every write to bump `updated`, and
TASK-120 reads `asserted_at` **from** `updated` at `asserted_scope: "register"`.

> So an edge appended to one KR **moves the staleness reference of every asserted
> `current` in the file**: a number that reported STALE because a linked task had
> moved reads fresh afterwards, with nothing about the number changed.

**One field is carrying two facts** — when the graph last changed, and when a
number was arrived at — *"the same shape as the `By when` column TASK-091 had to
split."*

It did not widen scope. It shipped a **mitigation**: every write that meets an
asserted `current` prints the affected KR ids on stderr and returns
`current_assertions_redated`, **so this cannot be discovered as a silent number
later.** The fix needs `schema/state-schema.json` and therefore the user — now
**TASK-155**.

## TASK-121's guard caught this row's own first draft

Three of its initial assertions read the live register as their expected value
and were flagged by the sweep that landed hours earlier. Repaired the way that
guard's own history describes — behavioural assertions moved to a synthetic
register, corpus tests take every id out of the file at runtime.

**Verified after merge: the sweep still reports 7, unchanged.** 983 lines of new
code, zero new instances of the class.

## A consequence the user meets first

`link` gates on **the register's own** conformance key, not on `OKR.md` — gating
a write on the shape of a file it does not touch would refuse for the wrong
reason. So on this project the writer refuses until:

```
perry-conform declare phase/002-linkage.md
```

**That is the user's act by design** (ADR-004: adoption proposes, the user
declares), and the refusal says exactly that, names the command, and adds that
reading is unaffected. Verified by running it.

## Four stale procedure steps found by declaring the register tool-owned

`test_procedures_call_the_tool` now covers `phase/<NNN>-linkage.md`, and
declaring it turned up four steps that appended an edge without naming a tool —
in `phases.md`, `weekly.md` (×2) and `reference/okr-linkage.md`. All fixed.

**`plan-phase` still authors the objectives/KRs block by hand from the
template**, which is the remaining hand-written part of a file documented as
machine-written — *and it is where the next `current: 0` would come from.*

## Merged

`--no-ff`, after `merge-check` attributed the one red to the base and nobody.
