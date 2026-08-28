# TASK-040 — risks are still read from a markdown table and are not records in the store

**Merged locally 2026-08-21** from `coding/task-040-risks-store` @ `660d251`.
`tests/merge-check --base feat/work-modes t037=… t040=…`: nothing new is red on
the merged result. Zero file overlap with TASK-037.

**The row does not close on this merge.** It stops at a declaration only the
user can give — see *The stop*.

## What the row was re-scoped to, and why

It was opened as *"Top risks becomes a table with id/opened/cleared"* — a
markdown-table task. Its second V4 round failed, and the re-review found the
root cause "worse than reported: **four implementations**". Then ADR-007
overturned the premise: **for a register four readers disagree about, the
answer is not a better table.** It was checked that risks are still read from
the markdown table at `perry/BOARD.md:96`, and the row was retitled to what its
own last note said: risks become records in the store. Rung V4 → V3.

## The count on the row was wrong, and the agent corrected it

Not four implementations. **Six implementations of three questions**, across
two files:

| question | implementations |
|---|---|
| is this table the register | `parsers._has_risk_header` · `perry-task.is_risk_header` + `risk_section_tables` |
| is this line a risk bullet | `parsers._RE_RISK_BULLET`/`_RE_RISK_PLACEHOLDER` · `perry-task`'s own pair |
| does this `Status` cell mean cleared | `parsers._RE_CLEARED` (8 words) · an inline `^(?:cleared\|resolved\|closed)\b` in `cmd_risk_clear` (3 of those 8) |

The row's "four" counted **tools**. `perry-state` was never an independent
reader — it consumes the `Snapshot` that `parsers` builds.

**After: three implementations, one per question**, all in `viewer/parsers.py`
— the bottom of the import graph, which `perry-task`, `perry-lint`,
`perry-state` and `perry_store` all already import. `perry-task`'s four names
are **bindings** to those objects, and the tests assert `is` identity rather
than agreement over a corpus, so a future copy re-introduces the defect
visibly.

**A real defect fell out of the third question.** `_RE_CLEARED` knows eight
words; `cmd_risk_clear` knew three. So a risk a human retired as `mitigated` or
`已缓解` read as **live** to `risk-clear` and as **cleared** to everyone else —
and clearing it again overwrote the first clear's date and reason. Refused now,
tested.

## What resisted, and was left alone

`bin/perry-lint`'s schema-driven section walk is **not a risks reader** — it is
the generic `state-schema.json` checker that walks every declared section by
regex. Giving it the risks rule would put a special case inside a loop whose
whole value is that it has none. Its one genuinely register-shaped answer,
`looks_like_perry_record`, does now ask `perry_store.RISK_STORED`.

## Byte identity, proved before any field was added

Verified independently on the merged tree:

```
$ python3 bin/perry-tasks risks-diff --root perry
{
  "register": "table",          "rows_from_store": 4,
  "rows_verbatim": [],          "rows_not_on_board": [],
  "cells_verbatim": {},         "cells_wearing_decoration": {},
  "cells_the_store_and_board_disagree_on": [],
  "rows_out_of_stored_order": {},
  "identical": true
}
```

`cells_verbatim: {}` is the part that makes the bytes mean something: **no cell
survived as a literal.** The store renders through the same
`row_descriptor` / `describe_cell` / `render_lines` the task store uses.

A test then strips `cleared` from every record and the section still reproduces
byte for byte — the "before any field is added" ordering as an assertion rather
than a claim. Reverting reddens it separately from the drift report: one test
corrupts a stored value and asserts the render diverges at the right column;
another hand-edits a cell and asserts exactly one `risk-store-drift` warning.

**A risk with neither date renders as itself and stores `""` for both.**
`opened` is `""` on a row migrated from a bullet — the day it was raised is
recorded nowhere — and `cleared` is `""` on an open risk *and* on a cleared
risk whose row names no day. Not today's date, not a zero. That is the same
defect as the `current: 0` default this project has already paid for, and it
has its own test.

## The stop — one `claims[]` entry, and it is the user's

`perry/risks.jsonl` is a canonical record file in the state root, and every one
of those is declared in `schema/state-schema.json § claims` with an owner and an
anchor, the way `tasks.jsonl` is. Writing an undeclared one puts a file Perry
does not admit to owning into the user's project, which is what the claim
surface exists to prevent.

Verified independently:

```
$ python3 bin/perry-tasks risks-write --from-board --root perry
perry-tasks: refusing to write `risks.jsonl`.
  … What is missing is the DECLARATION … That declaration is the user's to
  give. Until it lands, `risks-build` derives the records and `risks-diff`
  checks the projection, both without writing anything.
```

**Needed:**

```json
{"path": "risks.jsonl", "kind": "file", "owner": "work", "anchor": "state"}
```

After which `risks-write --from-board` can be enabled and `risk-add` /
`risk-clear` can write the store.

Everything reachable without it landed. The drift report is **live code** gated
on the file existing, and today reports `store_present: false,
comparison_performed: false` — rather than a clean register it never compared.

## It declined to grow the versioned payload, and that was right

Adding `cleared_items[]` to `perry-task list --json` took **KR-O2.4 from 0 to
22**. `tests/contract_key_parity.py § place` refuses to assign one key table to
two containers that fit it equally well, and `items[]` and `cleared_items[]`
are the same eleven keys.

It **backed the change out of the versioned contract** rather than duplicate a
key table or edit the KR's own measuring instrument. `perry-state --json §
risks` gained `cleared_items[]` instead, which is not versioned. Before it,
`cleared_on` was emitted by nothing at all: a cleared risk is correctly not in
`items` — it is not a top risk — so the one field it exists to carry had no
emitter.

KR-O2.4 is 0.

## Left open

1. **`contract_key_parity.place` cannot document two identically shaped
   containers.** The instrument is right to refuse an ambiguous page, but that
   means `perry-task list --json` can never grow a second list of an existing
   entry shape without either duplicating a key table or teaching `place` about
   tied containers. **It is a change to how KR-O2.4 is measured, so it is the
   user's call.**
2. **The risk *encoder* is still two implementations.** `perry-state §
   encode_risk` and `perry-task § cmd_list`'s risk dict are two answers to
   "what does a risk look like in a payload", and they **already differ** —
   `perry-state` emits `value`/`threshold`/`max1`/`max2`, `perry-task` does not.
   Same shape of defect, one layer up.
3. **Three registers left**: `## Cadence`, `## Intake` and `## User Input
   Queue` are still document-shaped. The `risk_section_shape` / `risk_table` /
   `risk_plan` trio is deliberately thin enough to be the template, but was not
   generalised into a `Register` abstraction — two instances is not a pattern,
   and inventing one before the third would be guessing.
