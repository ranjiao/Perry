# TASK-131 — result · **KR-O2.4 reaches 0**

> Date: 2026-08-21 · Executor: claude-subagent · Merged locally
> Branch: `coding/task-131-document-keys` · Cycle time: ~35 min
> 4 files, +99/−3. **No payload changed** — the diff contains no executable code.

## The number, per contract

| contract | before | after |
|---|---|---|
| `perry-decide/list/1.0` | 0 | 0 |
| `perry-events/list/1.0` | 0 | 0 |
| `perry-goals/list/2.1` | **5** | 0 |
| `perry-roles/list/1.0` | 0 | 0 |
| `perry-task/list/1.13` | **9** | 0 |
| **total** | **14** | **0** |

`documented_not_emitted` was **0** throughout and still is — the direction that
would mean a contract promises something absent.

**17 → 14 → 0**, across three rows that were not all about it.

## The unplaceable pair, and it is a second mechanism

`okr.objectives[]` and `phase.objectives[]` **could not be tabulated for a
reason that is not TASK-161's.** Both are non-empty on this repository, so
emptiness does not apply. They carry **identical children**, so a table of
`id, title, krs` scores coverage 1.00 *and* precision 1.00 against **both**, and
`place()` breaks on the tie and returns `None`.

> A table here would have looked like documentation and left the count at 14.

Declared in the **jsonc sketch** instead — which yields real nested paths the
checker reads — and the contract states the reason in place. **No key is left
unplaced.**

## Item 3 — live output against documented type, not against a reading of the code

Ten keys checked. The one worth quoting:

```
conformance.sections_read[].priority   doc `string | null`
                                       live "P0" AND live None
                                       — both branches in one payload, entry 0 vs entry 1
```

*which is why the row is typed as a union.*

## Item 4 — the tables are scored, not merely present

Deleting one row from each new table: `sections_read[] § rows` → metric 1,
naming that path; `semantics[] § note` → metric 1; and
`evidence_not_found[] § paths` → **metric 2**, because dropping to one key falls
below `place()`'s two-key floor and **takes its sibling `id` unplaced with it.**

## Item 5 — nothing moved from undocumented to unplaced

`unassigned` is **identical** before and after: 18 both runs.

## The second checker needed teaching, exactly as predicted

`test_task_writer § test_the_contract_document_lists_exactly_these_keys` needed
three new named key sets — `SEMANTICS_KEYS`, `SECTIONS_READ_KEYS`,
`EVIDENCE_NOT_FOUND_KEYS`. Without them `version`, `fields`, `note`, `heading`
and `paths` belonged to no set and **would have been reported as phantom** —
the same failure `depends_on_unknown[]` hit hours earlier.

## Three payload defects spotted, reported, not fixed

1. **`conformance.sections_read[].priority` is `null` for "no priority" while
   `tasks[].priority` uses `""` for the same fact — in the same payload.** Two
   spellings of one absence. A fix is a retype, so a version bump and a
   different review.
2. `sections_read` reports `"P0"` and `"P0 (must finish this period)"` as two
   groups, of which only the first normalizes. Faithful to the store; whether it
   *should* be is a board-shape question.
3. **The recorded parity fixture had already drifted before this row touched
   it** — it recorded the `asks` table as unplaced and did not record the idle
   entry. Today `asks` is populated and both idle collections are empty. *Board
   state moving under a recorded fixture, and nothing asserts it is fresh.*

## Two questions worth the user's eye

- **`place()` ties on structurally identical sibling containers and reports
  neither.** The sketch routes around it here; the next such pair with no
  natural sketch home has no route. Same symptom as TASK-161, different cause —
  ambiguity, not emptiness.
- **The two checkers still hold two models of what a key table is.** The parity
  check reads dotted paths and the sketch; `test_task_writer` reads bare names
  from table rows only. *"They agree today because I made both pass by hand, not
  because anything makes them agree."*
