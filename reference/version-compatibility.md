# Native cutover and compatibility

The final candidate has one native entry point, `bin/perry`. `describe` is the
versioned contract; consumers must reject unsupported majors and error envelopes.
No legacy CLI, old typed state contract or hidden compatibility command remains.
Historical documents stay historical and do not govern current-state reads.

## Existing projects

A missing native store is a migration/recovery condition. Do not bootstrap over
history. Legacy task/ask/risk migration belongs to the reviewed E cutover;
goals/decide rehearsal uses `tools/goals_decide_migrate.py` and its documented
reconciliation. H does not recreate the retired work importer. Rehearsals must
use an explicit temporary `--store` with `PERRY_KERNEL_TESTING=1`; never copy a
rehearsal database into a live location. Activation needs source/store/export/
backup receipts, exact source hashes, consumer probes and rollback limits for
each actual project. Source tests do not constitute activation or user acceptance.

Native export/import/replay are the backup/recovery interfaces. Preserve exact
validated exports; never edit them. Import uses the declared native contract and
an authorized actual project anchor. Inspect errors and compare re-exports before
accepting recovery. Frozen legacy registers and prose are not fallbacks for
current-state counts.

## Consumers

aiMark must use native probes and its reviewed goals/decide adapters. Knowledge,
role and churn reads use skill-side helpers under `tools/`, whose versioned output
shapes are documented there. The viewer's source retirement is a reviewable
proposal pending final acceptance after required consumers are covered. No
source deletion means the user has accepted a dropped behavior.

## Verification boundary

`tests/run` is the new stdlib kernel/helper acceptance facade. Its full/slow tiers
are not claims about the deleted legacy corpus. The finite test disposition
records each retired test. Independent integration uses the exact base/head
candidate and the new `tests/merge-check` receipt. Live activation and final H V5
remain outside source implementation.

The preference-prose migration is a provisional H design consequence for review
and final V5 acceptance; this source candidate performs no live preference edit.
