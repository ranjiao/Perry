# TASK-094 — Delete the header rule and the row splitter for the three stores

> Source: `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md` decision 4; DESIGN-005 § 5b
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: large
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: P-O2.2
- **Unblocks**: TASK-050 (P0), TASK-067 (P0), TASK-095 → TASK-099

## Why this is a deletion and not a fix

ADR-007 decision 4 settled it: the readers for `BOARD.md`, `OKR.md` and
`.perry/config.md` **go** when those become stores. All three are stores now —
TASK-088/089/090 for the board, TASK-092 for the other two, each verified
byte-identical. So none of the three is a table any more, and code that resolves
a header cell or splits a row for them is serving a shape that no longer exists.

This is also what unblocks the two P0s. `TASK-050` ("one normalization for a
header cell, not two") and `TASK-067` ("the writer can destroy the table it
writes to") both say in their own cells: **keep the row open until TASK-094
lands, then re-scope to whatever adoption still needs.** Four review rounds went
into hardening a category that is being removed rather than fixed.

## Deliverable

1. No reader resolves a header cell or splits a row **for those three files**.
   The call sites that do are deleted, not disabled.
2. What adoption needs survives. Adoption of a foreign project parses by
   definition — that is the one place markdown reading is still the job, and
   ADR-007 decision 4 says so explicitly.
3. `tests/test_one_header_rule.py` and `tests/test_row_integrity.py` shrink to
   what adoption still needs. They do not simply lose their assertions: what is
   removed is the coverage of a shape that no longer exists, and what remains
   must still fail when adoption's parsing breaks.
4. The three stores render byte-identically before and after. This change
   removes readers; it must move no output.

## Verification — V3

1. **0 header-resolution and 0 row-split call sites reach the three stores**,
   shown by a mechanical check rather than by reading — the deliverable is a
   count and the verification should be the same count.
2. `perry-tasks diff`, `perry-okr diff` and `perry-config diff` each report
   `identical` on this repository before and after, with `cells_verbatim {}` and
   `cells_wearing_decoration {}`.
3. Adoption still parses a foreign project: run it against
   `tests/fixtures/sample-project` and against a **copy** of
   `~/proj/gimegime-pmo`, never the original, and show the result is unchanged.
4. Break adoption's parsing on purpose and show the shrunken tests still fail.
   A test file that gets smaller and stops discriminating is the failure mode
   here.
5. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `viewer/tables.py`, `viewer/parsers.py` — the header rule and the row splitter
- `bin/perry_store.py`, `bin/perry_md_store.py` — only where they reach those readers
- `tests/test_one_header_rule.py`, `tests/test_row_integrity.py`

## Out of scope

- **Deleting the parser wholesale.** That is TASK-095, and it depends on this.
  This row removes header resolution and row splitting for the three stores;
  the remaining parser body is the next row's.
- `bin/perry-lint`, `bin/perry-diagnose`, `tests/test_migrate.py`,
  `tests/test_goals_writer.py`, `bin/perry-state-cost` — each is carried by an
  open unmerged branch or a live dispatch.
- `schema/state-schema.json`, `claims`, anything under `perry/`.
- Re-scoping TASK-050 or TASK-067. They unblock when this lands; the re-scope is
  theirs.
- Closing without the V3 evidence above.
