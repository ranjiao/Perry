# TASK-489 — reconciliation: this repository

Spec: `TASK-489-spec.md`, criteria 1–5, as corrected on main at `da9d6066`
(§ Decided 2026-09-29). Project `/Users/bytedance/proj/Perry`, state root
`perry`. Round 2, run on 2026-09-29 by the Coding Agent with the importer at
`coding/task-489-importer` 97ffc87f, into a fresh temporary store only.

`$PERRY_SCRATCH` below is
`/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/agent-a990cdfa91aeda615`,
derived by hand because the sandbox refused the derivation snippet. The work
directory is `$PERRY_SCRATCH/reconcile2-perry`: the store is `store.db` there,
and the anchor is `anchor/`. The whole transcript is
`$PERRY_SCRATCH/reconcile2-perry.log`, and the importer's own report is
`$PERRY_SCRATCH/reconcile2-perry.json`.

## What changed since round 1

- **The long-cell stop is resolved.** Seven open rows hold a `Next action`
  cell of 318–351 bytes: TASK-238, 334, 220, 371, 393, 309 and 286. The
  corrected spec lists them, and option A covers them: an open row is
  imported as it is. The importer already did so, and still does.
- **Rule 1: a cell that says nothing is unset.** The old store's blank marker
  `—`, and an empty string, are not imported, in every mapped field. The
  predicate is `lib.is_blank_cell`, the one rule for such a cell. In this
  repository every cell it matched was `""` or `—`; the counts are below.
- **Rule 2: a move is never timed before its create.** A move is timed at the
  later of its rule's time and its item's create time. Two moves were
  clamped; the details are below.

## Inputs

These are read-only, and unchanged since round 1. Their bytes are identical
to `9509170c`, the branch base: `git diff --stat 9509170c HEAD -- perry .perry`
is empty, and the hashes match.

| File | sha256 |
|---|---|
| `perry/tasks.jsonl` | `090fb3835914d78c5f5ac17bd010789be92aa636dee3c39cdd52cb569e28806a` (488 rows) |
| `perry/asks.jsonl` | `42913f5681d80c3a416a0fe786aecc5920066ae8a15f1165e15dce61855334e8` (107 rows) |
| `perry/risks.jsonl` | `1cd9385b66cfbdac4387e9b3f993edd62b95feb1063c49e5a90ae04d3515e1a5` (4 rows) |
| `perry/intake.jsonl` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty) |
| `.perry/events.jsonl` | `7bd285e6ff5a6daf63cee0bc85bfa2ba8a66c4b0504d7bb89800809928a97697` (3,643 lines) |

`perry/cadence.jsonl` is absent and `intake.jsonl` holds no row. **There is no
intake or cadence row, so no stop for that case.**

## Safety

```
$ ls -d /Users/bytedance/proj/Perry/.git/perry /Users/bytedance/proj/SkyTonight/.git/perry     # before
ls: /Users/bytedance/proj/Perry/.git/perry: No such file or directory
ls: /Users/bytedance/proj/SkyTonight/.git/perry: No such file or directory
$ ls -d …                                                                                      # after
ls: /Users/bytedance/proj/Perry/.git/perry: No such file or directory
ls: /Users/bytedance/proj/SkyTonight/.git/perry: No such file or directory
```

Every byte under the checkout's `.perry/` and `perry/`, 1,473 files, gave
`state-sha256=73bb1b8ad81ee15a` both before and after the run. That value
differs from round 1's because main has since changed other `perry/` files,
such as the spec; the six input stores above did not change.

Every `bin/perry-kernel` call names `--store $PERRY_SCRATCH/reconcile2-perry/store.db`
and `--root $PERRY_SCRATCH/reconcile2-perry/anchor`, and runs with
`PERRY_KERNEL_TESTING=1`.

## The import

```
$ bin/perry-kernel-migrate --root /Users/bytedance/proj/Perry --work $PERRY_SCRATCH/reconcile2-perry --json > $PERRY_SCRATCH/reconcile2-perry.json
(exit 0)
$ jq -c .criteria $PERRY_SCRATCH/reconcile2-perry.json
{"1_counts_per_type_and_state":true,"2_every_old_id_resolves":true,"3_next_id_above_every_issued_id":true,"4_import_refuses_a_store_that_is_not_empty":true,"5_replay_reproduces_the_items":true}
$ jq -c .import.result $PERRY_SCRATCH/reconcile2-perry.json
{"dir":"$PERRY_SCRATCH/reconcile2-perry/anchor/perry/export","items":599,"events":1177,"last_seq":1177,"verified":true}
```

The criteria below are checked a second time with commands that do not go
through the importer: `grep` on the old files, and `bin/perry-kernel` on the
store.

## Criterion 1 — equal counts per type and per status

```
$ grep -o '"status": "[a-z_]*"' perry/tasks.jsonl | sort | uniq -c
   2 "status": "blocked"
 321 "status": "done"
 144 "status": "dropped"
   1 "status": "in_progress"
  18 "status": "not_started"
   2 "status": "review"
$ grep -o '"answered": [a-z]*' perry/asks.jsonl | sort | uniq -c
   3 "answered": false
 104 "answered": true
$ grep -oE '"status": "(open|cleared)' perry/risks.jsonl | sort | uniq -c
   2 "status": "cleared
   2 "status": "open
$ bin/perry-kernel query --store … --root … --input '{"count_by":["type","state"],"limit":1}' | jq -c '.result.counts[] | [.key.type, .key.state, .n]'
["ask","answered",104]
["ask","pending",3]
["risk","cleared",2]
["risk","open",2]
["task","blocked",2]
["task","done",321]
["task","dropped",144]
["task","in_progress",1]
["task","not_started",18]
["task","review",2]
```

| Type | Status | Old | Kernel |
|---|---|---|---|
| task | not_started / blocked / in_progress / review / done / dropped | 18 / 2 / 1 / 2 / 321 / 144 | 18 / 2 / 1 / 2 / 321 / 144 |
| ask | pending / answered | 3 / 104 | 3 / 104 |
| risk | open / cleared | 2 / 2 | 2 / 2 |

**PASS.**

## Criterion 2 — every old id resolves

```
$ grep -ho '"id": "[A-Z]*-[0-9]*"' tasks, asks, risks | sort -u > old-ids;  wc -l
     599
$ bin/perry-kernel query … --input '{"limit":0}' | jq -r '.result.items[].id' | sort -u > kernel-ids;  wc -l
     599
$ comm -3 old-ids kernel-ids | wc -l
       0
$ (each of the 599 ids through bin/perry-kernel item get)
  item get failed for 0 of 599 ids
```

**PASS.**

## Criterion 3 — the next id is above every id ever issued

```
(highest TASK id in the old stores and .perry/events.jsonl, grep)  494   → ["dry_run","TASK-495"]
(highest USER id)                                                  1006  → ["dry_run","USER-1007"]
(highest RX id)                                                    004   → ["dry_run","RX-005"]
$ grep -o '"event": "purge", "id": "[A-Z]*-[0-9]*"' .perry/events.jsonl
"event": "purge", "id": "TASK-081"
"event": "purge", "id": "TASK-082"
"event": "purge", "id": "TASK-083"
```

Each next id comes from `bin/perry-kernel item create … --dry-run`. The
ceilings the importer seeded are TASK 494, with log-only ids 081–083; USER
1006; and RX 4. No `ceiling:` event was needed, because the purged ids sit
below the highest stored one. `tests/test_kernel_migrate.py § TestTheCeilings`
covers the case where one does not. **PASS.**

## Criterion 4 — `import` refuses a store that is not empty

```
$ bin/perry-kernel import --store … --root … --input '{"state_root":"perry"}'
perry-kernel: store_not_empty: …/reconcile2-perry/store.db holds 1177 event(s); import needs an empty store
(exit 1)
```

**PASS.**

## Criterion 5 — replaying the imported events reproduces the imported items

```
cb347f63a7cd9697fa538e821524ee5c0e952e7550ca89d5480f59da9234523c  anchor/perry/export/items.jsonl
e41fe9155a1a075739531c5787b23f0ed6421485f7edd1cc1e5becbc5fd811bd  anchor/perry/export/events.jsonl
$ bin/perry-kernel export --store … --root …
["unchanged",{"items.jsonl":"cb347f63a7cd9697","events.jsonl":"e41fe9155a1a0757"}]
sha256 after: identical
$ (fresh store: import from that export, then export)
["written",599,1177,true]
"unchanged"
$ cmp items.jsonl second/items.jsonl    (exit 0)
$ cmp events.jsonl second/events.jsonl  (exit 0)
```

`import` itself answered `"verified": true`. It replays every event, holding
each change to the template in force, and compares the replayed items with
`items.jsonl` byte for byte. **PASS.**

## Cells that said nothing: unset, not imported (rule 1)

Per mapped field, from the importer. `grep -c` on `"<field>": ""` and
`"<field>": "—"` gives the same counts.

| Field | `""` | `—` | Total |
|---|---|---|---|
| `tasks.summary` | 182 | 0 | 182 |
| `tasks.priority` | 31 | 0 | 31 |
| `tasks.owner` | 70 | 0 | 70 |
| `tasks.verification` | 78 | 0 | 78 |
| `tasks.next_action` | 70 | 89 | 159 |
| `tasks.evidence` | 0 | 145 | 145 |
| `tasks.title`, `tasks.track`, `asks.needed`, `risks.risk` | 0 | 0 | 0 |

Of the 89 `—` cells in `next_action`, 80 are on closed rows and 9 on open
rows. Round 1 imported the 145 `evidence` and 9 open `next_action` markers as
text. They are now unset.

## What was not carried, counted

- **`next_action` on closed tasks: 315 skipped by option A.** That is 219
  `done` and 96 `dropped`, counting only the cells that hold text. `grep`
  counts 395 closed rows with a non-empty cell: those 315 plus 80 that hold
  `—`. The 80 are counted as unset in the table above.
- **Dropped fields, rows that held a value:**

  | Field | Rows |
  |---|---|
  | `tasks.group` | 418 |
  | `tasks.stage` | 48 |
  | `tasks.arrived` | 47 |
  | `tasks.order` | 23 |
  | `tasks.stage_since` | 7 |
  | `tasks.commitment` | 0 |
  | `tasks.role` | 0 |
  | `asks.order` | 107 |
  | `risks.order` | 4 |

  `tasks.parent` held no value.
- **Status cells:** 104 asks and 2 risks say more than their state. The PMO
  noted that the answers and reasons are not in the old stores as fields, so
  nothing is lost.

## Moves clamped to their create (rule 2): 2

| Item | Rule | Rule's time | Clamped to |
|---|---|---|---|
| USER-930 | last old status event | `2026-09-13T16:16:54Z` | `2026-09-14T00:00:00Z`, its `asked` date |
| RX-002 | `cleared` (`2026-08-16`, a date) | `2026-08-16T00:00:00Z` | `2026-08-16T10:33:04Z`, the start of the old log (it has no `opened` and no event) |

Each move's `note` says so, for example
`from asks.jsonl; timed by last old status event (2026-09-13T16:16:54Z), clamped to its create`.
A `jq` pass over the exported events finds no item whose move precedes its
create:

```
$ jq -s '[group_by(.items[0])[] | … | select(.m != null and .m < .c)] | length' events.jsonl
0
```

## Date-only fields and this project's +08:00 clock

`lib.ts_moment`, the one converter, reads a date-only value as 00:00 UTC,
which is 08:00 on this project's +08:00 clock. This repository holds 107
date-only values that time an event: 105 `asked` dates and 2 `cleared`
dates. `created` and `opened` hold none. Each was compared with the item's
own events in `.perry/events.jsonl`:

- **The date lands after the item's own first event in 8 cases.** These are
  USER-015, 903, 904, 905, 906, 930, 931 and 1006, each asked between 00:16
  and 05:45 local time on its `asked` day. Their creates are timed 2h15m to
  7h44m after the ask's own event, but on the right calendar day.
- **Only USER-930 had a later event out of order.** Its answer came at 00:16
  local, before 08:00, so its move preceded its create. The clamp fixes that
  order.
- **No date falls on a different local day from its item's first event.**

**What I did:** I kept the reading and clamped the move. Reading dates as
local midnight would need a second converter, which
`tests/test_kr_progress_provenance.py § test_the_converter_has_exactly_one_home`
forbids in `bin/`, or a change to `lib.ts_moment` that every other reader
shares. Both are outside this row. Every create timed by a date says so in its
note: `timed by asked 2026-09-14, a date, read as 00:00 UTC`. If the user
wants those eight creates at their ask events instead, that is a new rule to
decide.

## Other things the reviewer should see

- **References that do not resolve: 3.** USER-927, USER-929 and USER-931 each
  block `P003-O2-KR3`, a key result; that is TASK-492's. Every other reference
  resolved, giving 251 `blocks` edges once duplicates are merged:
  - 172 task to task, all from `depends_on`;
  - 79 ask to task, from 14 `USER-` entries in `depends_on` and 76 tokens
    from the asks' `Blocks` cells.

  There are no self-edges.
- **Attachments: 74.** These are `design_refs`, kept verbatim.
- **Creation times:**
  - 457 from `created` and 105 from `asked`;
  - 32 from the first old event for the id: TASK-001 to TASK-034 with no
    `created`, and RX-001;
  - 5 from the start of the old log: RX-002, RX-003, RX-004, USER-001 and
    USER-002.
- **Move times:** 573 at the last old status event, 1 at `cleared`, and 2 at
  the creation date. Two of these were clamped, as above.
- **Events: 1,177.** That is `init`, `template apply`, 599 creates and 576
  moves.
