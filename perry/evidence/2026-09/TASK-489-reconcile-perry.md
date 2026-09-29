# TASK-489 — reconciliation: this repository

Spec: `TASK-489-spec.md`, criteria 1–5. Project `/Users/bytedance/proj/Perry`,
state root `perry`. Run on 2026-09-29 by the Coding Agent with the importer at
`coding/task-489-importer` 02af3f37, into a temporary store only.

`$PERRY_SCRATCH` below is
`/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/agent-a990cdfa91aeda615`,
derived by hand because the sandbox refused the derivation snippet. The work
directory is `$PERRY_SCRATCH/reconcile-perry`: the store is `store.db` there,
and the anchor is `anchor/`. The whole transcript is
`$PERRY_SCRATCH/reconcile-perry.log`, and the importer's own report is
`$PERRY_SCRATCH/reconcile-perry.json`.

## Stopped on: seven open rows hold a `Next action` cell over 300 bytes

§ Decided 2026-09-29 says that 160 of 488 cells are over 300 bytes, and that
"every one of those is on a `done` or `dropped` row". It also says that the
longest cell on an open row is 351 bytes. Measured on the inputs below, 153 of
the 160 are on closed rows and seven are on `not_started` rows:

| Task | State | Bytes |
|---|---|---|
| TASK-238 | not_started | 351 |
| TASK-334 | not_started | 348 |
| TASK-220 | not_started | 343 |
| TASK-371 | not_started | 341 |
| TASK-393 | not_started | 335 |
| TASK-309 | not_started | 333 |
| TASK-286 | not_started | 318 |

The brief says that if any row other than a `done` or `dropped` one fits the
long-cell case, stop and report it. This is that report. Nothing here decides
it. The importer applies the rule as it is written: a closed task's
`next_action` is not imported, and an open task's is imported as it is. So
these seven cells are in the temporary store verbatim.

Whether option A covers them is the user's call, and it must be made before
row E runs the import for real. The criteria below do not depend on it.

## Inputs

These are read-only. Their bytes are identical to `9509170c`, the branch base:
`git diff --stat 9509170c HEAD -- perry .perry` is empty, and the hashes match
this worktree's copies.

| File | sha256 |
|---|---|
| `perry/tasks.jsonl` | `090fb3835914d78c5f5ac17bd010789be92aa636dee3c39cdd52cb569e28806a` |
| `perry/asks.jsonl` | `42913f5681d80c3a416a0fe786aecc5920066ae8a15f1165e15dce61855334e8` |
| `perry/risks.jsonl` | `1cd9385b66cfbdac4387e9b3f993edd62b95feb1063c49e5a90ae04d3515e1a5` |
| `perry/intake.jsonl` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty) |
| `.perry/events.jsonl` | `7bd285e6ff5a6daf63cee0bc85bfa2ba8a66c4b0504d7bb89800809928a97697` (3,643 lines) |

`perry/cadence.jsonl` is absent. `intake.jsonl` holds no row. **There is no
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

The project's state files were fingerprinted before and after the run: every
byte under `.perry/` and `perry/`, 1,473 files, gave `state-sha256=06af52f804a4cd8d`
both times.

Every `bin/perry-kernel` call names `--store $PERRY_SCRATCH/reconcile-perry/store.db`
and `--root $PERRY_SCRATCH/reconcile-perry/anchor`. It also runs with
`PERRY_KERNEL_TESTING=1`, so a call that lost its `--store` would be refused
rather than derived.

## The import

```
$ bin/perry-kernel-migrate --root /Users/bytedance/proj/Perry --work $PERRY_SCRATCH/reconcile-perry --json > $PERRY_SCRATCH/reconcile-perry.json
(exit 0)
$ jq -c .criteria $PERRY_SCRATCH/reconcile-perry.json
{"1_counts_per_type_and_state":true,"2_every_old_id_resolves":true,"3_next_id_above_every_issued_id":true,"4_import_refuses_a_store_that_is_not_empty":true,"5_replay_reproduces_the_items":true}
$ jq -c .import.result $PERRY_SCRATCH/reconcile-perry.json
{"dir":"$PERRY_SCRATCH/reconcile-perry/anchor/perry/export","items":599,"events":1177,"last_seq":1177,"verified":true}
```

The criteria below are checked a second time with commands that do not go
through the importer: `grep` on the old files, and `bin/perry-kernel` on the
store.

## Criterion 1 — equal counts per type and per status

Old stores, counted with `grep`:

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
```

The kernel store:

```
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

An ask's state is its `answered` flag. The importer refuses an ask whose flag
disagrees with `parsers.ask_is_answered` on its status cell, and none does. A
risk's state is `cleared` when `parsers.status_is_cleared` says so, and `open`
when the cell is `open`. **PASS.**

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

That is 488 tasks, 107 asks and 4 risks. The purged ids TASK-081, TASK-082 and
TASK-083 are not items: they survive only in `.perry/events.jsonl`, and
criterion 3 counts them. **PASS.**

## Criterion 3 — the next id is above every id ever issued

```
$ grep -ohE '"id": "TASK-[0-9]+"' tasks/asks/risks .perry/events.jsonl | grep -oE '[0-9]+' | sort -n | tail -1
494
$ bin/perry-kernel item create … --dry-run --input '{"actor":…,"type":"task","fields":{…}}' | jq -c '[.effect, .result.item.id]'
["dry_run","TASK-495"]
(highest USER id) 1006     → ["dry_run","USER-1007"]
(highest RX id)   004      → ["dry_run","RX-005"]
$ grep -o '"event": "purge", "id": "[A-Z]*-[0-9]*"' .perry/events.jsonl
"event": "purge", "id": "TASK-081"
"event": "purge", "id": "TASK-082"
"event": "purge", "id": "TASK-083"
```

The importer seeds each prefix's ceiling from the ids of the old stores and
every `id` in `.perry/events.jsonl`:

```
{"TASK":{"stored_max":494,"issued_max":494,"log_only_ids":["TASK-081","TASK-082","TASK-083"],"seed":null},
 "USER":{"stored_max":1006,"issued_max":1006,"log_only_ids":[],"seed":null},
 "RX":{"stored_max":4,"issued_max":4,"log_only_ids":[],"seed":null}}
```

Here the purged ids sit below the highest stored one, so no `ceiling:` event
was needed. The path that writes one when a purged id is the highest is
`tests/test_kernel_migrate.py § TestTheCeilings`. Its fixture's TASK-009 lives
only in the log, and the kernel then mints TASK-010. **PASS.**

## Criterion 4 — `import` refuses a store that is not empty

```
$ bin/perry-kernel import --store … --root … --input '{"state_root":"perry"}'
perry-kernel: store_not_empty: …/reconcile-perry/store.db holds 1177 event(s); import needs an empty store
(exit 1)
[false,"store_not_empty","…/reconcile-perry/store.db holds 1177 event(s); import needs an empty store"]
```

**PASS.**

## Criterion 5 — replaying the imported events reproduces the imported items

`import` replays every event and compares the replayed items with
`items.jsonl` byte for byte. It answered `"verified": true`, above. Since
TASK-489 it also holds each replayed change to the template in force when its
event was written.

The store's own export then finds both files already holding its bytes. A
second, fresh store imported from that export gives the same bytes again:

```
sha256 of the synthetic export, before the kernel's own export
a62f4e9f27449f7d30f52bc90f2901c91a28b44611f5fef4f02114ad549758f9  anchor/perry/export/items.jsonl
efba220d1a0cfc5f2a49ee06a0044d3a35d0cf517e879224977c7acf16d7c883  anchor/perry/export/events.jsonl
$ bin/perry-kernel export --store … --root …
["unchanged",{"items.jsonl":"a62f4e9f27449f7d","events.jsonl":"efba220d1a0cfc5f"}]
sha256 after: identical
$ (fresh store: import from that export, then export)
["written",599,1177,true]
"unchanged"
$ cmp items.jsonl second/items.jsonl    (exit 0)
$ cmp events.jsonl second/events.jsonl  (exit 0)
```

**PASS.**

## What was not carried, counted

- **`next_action` on closed tasks: 395 skipped.** That is 251 `done` and 144
  `dropped`. `grep` on `tasks.jsonl` counts the same 395 non-empty cells on
  `done` or `dropped` rows.
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

  `tasks.parent` held no value. The importer refuses a populated `parent`,
  and any populated field the mapping does not name.
- **Status text beyond the state: 104 asks and 2 risks.** An answered ask's
  cell reads `answered <date>: <answer>`, and a cleared risk's reads
  `cleared <date> — <reason>`. The mapping makes the status the state, so the
  answer and the reason are not in the store. The template declares `answer`
  and `reason`, and `parsers.ask_answer` could fill `answer`. That is listed
  as a question in the RESULT.

## Other things the reviewer should see

- **References that do not resolve: 3.** USER-927, USER-929 and USER-931 each
  block `P003-O2-KR3`. That is a key result, and OKR items are TASK-492's.
  Every other reference resolved, giving 251 `blocks` edges once duplicates
  are merged:
  - 172 task to task, all from `depends_on`;
  - 79 ask to task, from 14 `USER-` entries in `depends_on` and 76 tokens
    from the asks' `Blocks` cells. Eleven of those name the same edge twice.

  There are no self-edges.
- **Attachments: 74.** These are `design_refs`, kept verbatim, for example
  `DESIGN-023`.
- **Times.**
  - Creation dates: 457 from `created`, 105 from `asked`, 32 from the first
    old event for the id (TASK-001 to TASK-034 have no `created`, and neither
    does RX-001), and 5 from the start of the old log. Those five are RX-002,
    RX-003, RX-004, USER-001 and USER-002, which have no date and no event.
  - Moves: 573 at the last old status event, 1 at `cleared` (RX-002), and 2 at
    the creation date (USER-001 and USER-002, answered with no event).
  - Each event's `note` names its rule.
  - Two moves are timed before their creates. RX-002 is cleared
    `2026-08-16`, read as UTC midnight, but has no `opened`, so it is created
    at the log's first line, `2026-08-16T10:33:04Z`. USER-930 is asked
    `2026-09-14`, UTC midnight, and was answered at `2026-09-14T00:16:54+08:00`.
  - Both moves come after their creates in seq order.
- **Blank markers imported verbatim.** `evidence` is `—` on 145 tasks, and
  `next_action` is `—` on 9 open tasks. The kernel counts `—` as a set text
  value, so a `done` guard requiring `evidence` would pass on it.
- **Events: 1,177.** That is `init`, `template apply`, 599 creates and 576
  moves. There is no `seed ceilings` event here.
