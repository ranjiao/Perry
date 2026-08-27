# TASK-130 — `schema/README.md`'s contract table pinned versions nothing checked

**Done 2026-08-21** by the PMO, in the main checkout. Rung **V3**.

## The row's scope grew twice before it was touched

Opened as *"says three contracts and pins goals at a version that shipped two
ago"*. TASK-169 fixed the **count** and found a second stale pin. By the time
this was done there were **three**:

```
schema/README.md      live
  perry-task/list/1.11   →  1.15
  perry-goals/list/1.0   →  2.1
  perry-events/list/1.0  →  1.1
```

All three had been correct when written. `perry-task` went stale tonight when
TASK-170 shipped `depends_on_resolved`; `perry-events` went stale this afternoon
when TASK-168 flipped the first page to the tail.

## Not fixed by correcting the numbers

Correcting them resets the clock on the same defect — a number copied into a
second place goes stale the first time the first place moves, and nothing here
was checking it.

**The version numbers are gone from the table.** It names the contract *family*;
which minor is live is the `contract` string in the payload and the page's own
first line, and the README now says so.

Two other stale claims fell out of the same read:

- **`schema/README.md:118`** still said *"the version in the first column is a
  convenience and nothing checks it… correcting them is TASK-130's row"* —
  TASK-169's note, obsolete the moment the column lost its numbers.
- **`schema/README.md:205`** said `perry-goals/list/1.0` and
  `perry-decide/list/1.0` *"do not exist yet"*. **Both exist**, are in the table
  above it, and `OKR.md` has had a store beside it since this morning. Rewritten
  to say what was true when it was written and what is true now, and to keep the
  part that still applies — *resolve columns by name, never by position* — which
  is still live for the four `BOARD.md` registers that have no store.

## The guard

`tests/test_contract_key_parity.py § test_the_contract_table_pins_no_version`.
Mutation-proved: restoring `| \`perry-task/list/1.11\` |` reddens it.

**Scoped to the table, not the file.** The prose at line 112 cites
`perry-knowledge/list/1.0` while recounting the incident where that exact
version shipped with no page — a historical fact, not a pin. A file-wide ban
would forbid the project from describing its own history.

## Left alone

`viewer/templates/` and `work/reference/viewer.md` may also cite versions.
TASK-178 is deleting both tonight; nothing to do there.
