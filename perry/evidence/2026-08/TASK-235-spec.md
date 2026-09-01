# TASK-235 — `DECISIONS.md` stops existing; `perry-decide list` is the surface

> DESIGN-013 step 1, User Decision 3, answered 2026-08-29: **delete it**.
> The design is locked: `perry/design/DESIGN-013-one-place-per-fact.md`.

## Measured, 2026-08-29 at `30cc467`

`perry/DECISIONS.md` is 1,834 bytes — **76% inside table rows**, 12 rows, longest
cell 68 bytes. There is no per-row prose. Its own third line already says what it
is:

> Rendered by `bin/perry-decide` from `decisions/ADR-*.md`. Those files are the
> record; this file is a view of them. Edit an ADR, then re-run `perry-decide
> list` to refresh — do not hand-edit rows here, they are overwritten.

`perry-decide list` already prints the same content. One reader, one writer.

## The rule this serves

DESIGN-013 § 5.1, adopted as User Decision 1:

> A fact that has a schema lives in exactly one store. A document holds what has
> no schema. No field lives in both.

The ADR bodies under `decisions/` are the record. `DECISIONS.md` is a second copy
of their id, title, type, date and status.

## Deliverable

`perry/DECISIONS.md` is deleted and `bin/perry-decide` no longer writes it.
`perry-decide list` is the documented surface. Every live reference to the file —
`SKILL.md`, `decide/SKILL.md`, `schema/`, `reference/` — names the command
instead. Its `claims[]` entry in `schema/state-schema.json` is removed, and its
declaration row in `.perry/conformance.md` goes with it.

### `mint_id` — TASK-214 is inside this change, not beside it

`perry-decide`'s `mint_id` reads `max(files ∪ index)` while `render_index`
rebuilds the index from the files, so the departed half erases itself — that is
`TASK-214`, and it is now blocked on this row because **deleting the index
changes its shape**. After this change `mint_id` must read the ADR **files
alone**. Verify that it does, and that minting is still monotonic across a
delete: mint `ADR-011`, remove its file, mint again, and confirm `011` is **not**
reissued if that is the contract — or state plainly that it is, because
`perry-task purge`'s own rule is that the log keeps an id so it is never
reissued, and `perry-decide` should not silently disagree with it.

Report whether `TASK-214` is closed by this change or whether something survives.

## Verification — V4

1. `perry-decide list` prints every ADR the deleted file listed, with the same
   status counts — **10 active / 10 total** at `ADR-010`.
2. `grep -rn 'DECISIONS.md'` over `bin/`, `tests/`, `schema/`, `reference/`,
   `templates/` and every `SKILL.md` returns **zero live references**. Matches
   under `perry/evidence`, `perry/journal`, `perry/design` and `perry/decisions`
   are the historical record and **stay** — do not rewrite them.
3. `perry-lint` is at 0 errors and does not report a missing claimed file.
4. `mint_id` reads the files alone, proved by minting with the index absent.
5. **Mutation**: restore the writer and show a NAMED test goes red. A guard that
   can be deleted with the suite unchanged does not count — `perry-goals`
   shipped exactly such a tautology under TASK-095 and it was removed for it.
6. `bash tests/run` at the baseline of the commit the work forks from, named by
   **runner and tree**. `main` at `ee0b36a` is 98 modules / 2882 tests / 3
   failures under `tests/run`; `unittest discover` shows 3 more from a
   module-double-import artefact in `test_risks_store`.

## Out of scope, and this one is a decision rather than an omission

**Do not add any replacement index file.** DESIGN-013 § 4.1 records that the
markdown link surface into `decisions/ADR-*.md` is **given up** by this decision —
a web reader lands in the directory listing, and `perry-decide list` is a
terminal surface that cannot be linked to. The draft recommended keeping a
rendered view and that recommendation was declined by the user.

If the loss turns out to matter, that is a **finding to report**, not a thing to
quietly fix by re-adding an index under another name.

Also out: `OKR.md` (TASK-236) and `BOARD.md` (TASK-237). Same design, later steps.
