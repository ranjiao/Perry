# TASK-157 — the KR tables removed from `perry/phase/`, and what they said

> The record of a deletion. `phase/00N-<slug>.md` stopped carrying a KR table
> on 2026-08-29 (TASK-157, under DESIGN-013 § 5.1). Git holds the bytes at
> `8abd30d`; this file holds the part a reader of the phase document would
> otherwise have to go looking for — **which of those cells said something the
> register does not**. `bin/perry-goals krs --phase <NNN>` prints what the
> register says now.
>
> The retro scoring tables (`| KR | Score | Measured |`) are NOT part of this
> and were not touched: they record what happened to a KR, which is document
> work. Only the declaration table — the one `schema/state-schema.json`
> describes — was removed.

## Method

Every row of every removed declaration table, compared word by word against the
register's `title` + `metric` for the same KR, both read at `8abd30d`, the
commit this work forked from. Two verdicts:

- **carried** — the register holds every word the cell did. Nothing was lost.
- **document said more** — the cell carried at least one word the register does
  not. These are the only lines where the deletion removed prose.


## `perry/phase/001-work-modes-live.md` — 8 row(s) removed

| KR | verdict | words only the document had |
|---|---|---|
| P001-O1-KR1 | carried | — |
| P001-O1-KR2 | carried | — |
| P001-O1-KR3 | **document said more** | `baseline:` |
| P001-O1-KR4 | carried | — |
| P001-O2-KR1 | carried | — |
| P001-O2-KR2 | carried | — |
| P001-O3-KR1 | **document said more** | `here`, `there` |
| P001-O3-KR2 | carried | — |

## `perry/phase/002-fields-are-typed.md` — 8 row(s) removed

| KR | verdict | words only the document had |
|---|---|---|
| P002-O1-KR1 | carried | — |
| P002-O1-KR2 | carried | — |
| P002-O1-KR3 | **document said more** | `baseline:` |
| P002-O2-KR1 | carried | — |
| P002-O2-KR2 | carried | — |
| P002-O2-KR3 | carried | — |
| P002-O3-KR1 | carried | — |
| P002-O3-KR2 | carried | — |

## `perry/phase/003-storage-code.md` — 8 row(s) removed

| KR | verdict | words only the document had |
|---|---|---|
| P003-O1-KR1 | **document said more** | `were` |
| P003-O1-KR2 | carried | — |
| P003-O1-KR3 | carried | — |
| P003-O2-KR1 | carried | — |
| P003-O2-KR2 | **document said more** | `fails`, `file`, `non-adoption`, `parses`, `projected`, `reverting`, `that`, `when` |
| P003-O2-KR3 | **document said more** | `canonical`, `from`, `markdown`, `projected`, `reader`, `sections`, `still`, `store`, `tell`, `which` |
| P003-O3-KR1 | **document said more** | `carry-over`, `edges`, `file`, `first`, `movement`, `this`, `with` |
| P003-O3-KR2 | carried | — |

## Summary

- **17** row(s) said nothing the register does not.
- **7** row(s) carried at least one word the register does not. Each cell is quoted in full below, because a summary of deleted prose is not the prose.

### `P001-O1-KR3`

- **KR text cell**: Switching a track's mode edits one file and rewrites no state, shown by a revert test (baseline: unproven)
- **Metric / Target cell**: 1 file · 0 rewrites
- **Linked overall KR cell**: KR-O1.3 — carried across into the register's new `linked` field

### `P001-O3-KR1`

- **KR text cell**: A state file can declare it is Perry-shaped, at a version, and every writer gates on that declaration (baseline: `is_adopted()` answers only "is there any Perry file here")
- **Metric / Target cell**: 1 marker, all 3 writers gating
- **Linked overall KR cell**: KR-O3.4 — carried across into the register's new `linked` field

### `P002-O1-KR3`

- **KR text cell**: A hand edit to a rendered file is reported rather than honoured, at the severity the user picks (baseline: it is honoured)
- **Metric / Target cell**: reported
- **Linked overall KR cell**: — — carried across into the register's new `linked` field

### `P003-O1-KR1`

- **KR text cell**: Stores declared in `claims[]` that exist on disk (baseline 4 of 6 — `intake.jsonl` and `asks.jsonl` were built by TASK-196 / TASK-197 and never imported)
- **Metric / Target cell**: 6 of 6
- **Linked overall KR cell**: KR-O2.1 — carried across into the register's new `linked` field

### `P003-O2-KR2`

- **KR text cell**: The adoption/migration reader is fenced into one named module, with a mechanical guard that fails when a non-adoption call site parses a projected file — and the guard is shown able to go red by restoring one removed call site (baseline: no boundary; `viewer/parsers.py` is 3,973 lines serving both roles)
- **Metric / Target cell**: guard live · reverting one call site turns it red
- **Linked overall KR cell**: KR-O2.3 — carried across into the register's new `linked` field

### `P003-O2-KR3`

- **KR text cell**: `BOARD.md`'s two truth models are marked in the file, so a reader can tell which sections are projected from a store and which are still canonical markdown (baseline: nothing marks the boundary — TASK-199)
- **Metric / Target cell**: boundary marked
- **Linked overall KR cell**: KR-O2.1 — carried across into the register's new `linked` field

### `P003-O3-KR1`

- **KR text cell**: Open `main`-track rows in neither `objectives[].krs[].tasks[]` nor a declared `unlinked[]` — the never-asked state (baseline 45 of 45 at phase start, measured by `perry-state --section attribution` on 2026-08-28; the 5 carry-over edges declared with this file are the first movement)
- **Metric / Target cell**: 0
- **Linked overall KR cell**: KR-O2.3 — carried across into the register's new `linked` field

## What was NOT done

**Nothing above was merged into the register.** Rewording a KR is a `goals`-lane
write and this row is not one: TASK-157 removes the second copy, it does not
adjudicate which copy was right. Where a phrase above matters, the register is
the file to edit, and the `goals` lane owns that edit.

`Linked overall KR` is the one column that WAS carried across verbatim, into
the register's new optional `linked` field. It is the only one of the table's
four columns the register had no field for, so deleting the table without it
would have deleted a fact rather than a duplicate.

