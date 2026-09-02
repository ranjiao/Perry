# TASK-284 — round 2 result

> Round 1 (`coding/task-284-spec-scannability`, `cbc2d8f`) was reviewed at V4 and
> FAILED. This round finishes inside the same bound: one procedure section
> (`add-task` step 3), one reader (`scan_spec_escalations` / its consumers), one
> census. Branch: `coding/task-284-round2b`, cut from `cbc2d8f`.

## Status

IN PROGRESS — this file is written before the work and amended as each item
lands, so a mid-run interruption still leaves the numbers that were earned.

## The census, with the ref it was taken at

The census is tree- and time-dependent. Only the **45** is stable.

Taken 2026-09-02T14:44:58Z with an independent counter
(`scratchpad/t284r2/census.py` — reads each ref's OWN `schema/state-schema.json`
heading glossary and its own file list, never `viewer/parsers.py`):

| ref | sha | `*-spec.md` | scannable | unscannable |
|---|---|---|---|---|
| `d49964e` (this branch's base) | `d49964eee3394010` | 119 | 74 | **45** |
| `coding/task-284-spec-scannability` (round 1) | `cbc2d8f1860ae512` | 119 | 74 | **45** |
| `coding/task-247-config-predicate` (live, today) | `89295085d20cfe9e` | 135 | 90 | **45** |

Round 1 recorded `134/89/45` for the live branch; that branch has taken one more
commit since, adding one scannable spec. The unscannable set is byte-identical
across all three refs — every spec written since is sectioned, which is why the
45 does not move while the denominator does.

**Shape split of the 45** (measured on the live ref): **19** carry
`### Deliverable` / `### Files in scope` (an `h3`, which `_section` does not
match); **26** carry no such section in any shape; **0** carry the bullet shape
`- **Deliverable**:` that `perry-task add` renders. This is why fix 2 was
refused in round 1 and is refused again: widening `_section` to the bullet
shape would close **none** of the 45.

