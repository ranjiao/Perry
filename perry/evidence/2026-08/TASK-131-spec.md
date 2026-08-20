# TASK-131 — emitted contract keys documented nowhere

> Source: `perry/evidence/2026-08/TASK-127-dispatch-2026-08-20-2045.md`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: no
> Touches architecture: no — documentation of keys that already ship
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: KR-O2.4 (`perry/OKR.md` v2) — *"contract-payload keys
  documented but not emitted, or emitted but not documented"*, target **0**

## The number, and it has been moving

TASK-127 built the check and measured **17**. Two rows have since brought it
down without being about it: TASK-142 documented what it added (17 → 14) and a
`depends_on_unknown[]` table closed two more.

Run `python3 tests/contract_key_parity.py` **first** and report what it says
today, per contract. That number, not this paragraph, is your baseline.

`documented_not_emitted` has been **0** throughout, which is the direction that
would mean a contract promises something absent. This row is the other
direction: keys that ship and are documented nowhere.

## What "documented" means here, and it is not obvious

The check matches a **key table** — `| \`name\` | type | meaning |` — against the
paths a payload actually emits. So:

- prose describing a collection is **not** documentation to this check, however
  good the prose is;
- **a table for a collection this project's own state leaves empty cannot be
  scored**, and is reported as unplaced rather than as documented. That is
  TASK-161, and it is the reason `review_idle[]` is prose today.

**So do not simply write tables.** For each undocumented key, decide whether it
can be tabulated at all against this repository's state, and **say which ones
cannot and why.** A table that gets scored against a neighbouring container is
worse than prose — it reports keys as missing that are merely absent.

## And there is a second checker

`tests/test_task_writer § test_the_contract_document_lists_exactly_these_keys`
reads bare key names out of the same tables and compares them against a union of
**named key sets** in that test. On 2026-08-21 a new table for
`depends_on_unknown[]` passed the parity check and **failed this one**, because
`unknown` belonged to no declared set.

**Two checkers, two models of what a key table is.** Every table you add must
satisfy both, and if you find a key that cannot satisfy both, that is a finding
worth reporting rather than working around.

## Deliverable

`emitted_not_documented` reaches **0** across every contract, or every remaining
key is named with the reason it cannot be tabulated — and that reason is one of
TASK-161's, not a new excuse.

## Verification — V3

1. **Report the before and after per contract**, separately, not as a total.
2. **Both checkers green.** Say so explicitly for each.
3. **Every added table is true**: for at least three of the keys, show the
   emitted value and the documented type agreeing on live output, not on your
   reading of the code.
4. **Deleting one row from one new table reddens the parity check** — proving
   the tables are being scored rather than merely present.
5. **The baseline file is re-recorded and nothing is silenced.** If a key moves
   from undocumented to unplaced, that is not progress and must be reported as
   what it is.
6. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`, `git diff -- perry/` empty.

## Files in scope

- `schema/*-list-contract.md`
- `tests/test_task_writer.py`'s key sets, where a new table needs one
- `tests/fixtures/contract-key-parity.json` — re-recorded
- focused tests

## Out of scope

- **Changing any payload.** This row documents what ships; it does not add,
  remove or retype a key. If a key looks wrong, **report it — do not fix it
  here**, because a payload change is a version bump and a different review.
- TASK-132's 23 unplaceable keys and TASK-161's tabulation defect — read both,
  and hand back anything that belongs to them.
