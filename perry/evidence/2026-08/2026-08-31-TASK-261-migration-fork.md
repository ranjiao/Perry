# The fork Tier A ran into: `perry-migrate` cannot survive it

> Escalation for `TASK-261`, written the way `work/reference/review.md § 6`
> asks — both readings defensible applied consistently, what is already true,
> and a named recommendation with its reason.

## What is already true

The ADR-004 gate and its ledger are out. 40 files, **−5,245 lines**. The suite
is green except `test_migrate` (22 failures, 9 errors) and the three modules
that are already red on a clean `git archive HEAD` export.

`bin/perry-migrate` calls `C.declare` at **14 sites**. Its *output* is a
conformance record carrying `route: migrate`. It cannot be repaired without
restoring the ledger, because the ledger is the thing it writes. Migration and
conformance were never two subsystems — the delete list called them Tier A and
Tier C, and that was wrong.

## Reading A — migration is speculation; delete it

`.perry/conformance.jsonl` held 23 records and **not one carried
`route: migrate`**. `TASK-097` — "migrate the two real projects, at V5" — has
been `not_started` since the day it was filed. A 2,393-line lossless,
dry-runnable, recoverable migrator has never moved a single foreign project.

Applied consistently: Perry is a tool for projects it starts. Adoption means
"run Perry here and let it write its own state". `TASK-097` is dropped along
with `tests/test_migrate.py` (2,900 lines). Tier C's migration half lands now
rather than later, and Tier A's total goes past 10,000 lines.

## Reading B — migration is the unbuilt half; keep it

Perry has never been pointed at a foreign project because that work was never
done, not because it is unwanted. The delete list's own note says the gate's
value *needs* a foreign project — which is an argument that the missing thing
is the project, not the mechanism.

Applied consistently: the ledger comes back for `perry-migrate` alone —
`declare`, `migrate_record`, `record_diff`, roughly 200 of the 598 deleted
lines. The **write-path gate stays deleted**. `TASK-097` becomes the next real
phase. This keeps the option and pays ~200 lines plus `test_migrate` for it.

## Recommendation: A

Not for the line count. Under B the ledger comes back to serve a consumer that
has never run — so the same measurement that justified deleting it will justify
deleting it again in three months, and the second deletion will cost what this
one cost.

If you want Perry to run on other people's projects, the cheap version is an
**importer you re-run**: read a foreign board, write Perry state, overwrite on
conflict. That is a smaller thing to build than what Reading B keeps, and it
has no declaration format of its own to drift.

## Not on the table either way

The write-path conformance gate does not come back. Nothing in this fork
reopens it.
