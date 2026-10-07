# TASK-489 — reconciliation: this repository

Spec: `TASK-489-spec.md`, criteria 1–5, with § Round 3 (decided by the PMO)
and § Round 4 (decided by the user, option B), on main at `a95fc07f`. Project
`/Users/bytedance/proj/Perry`, state root `perry`. Round 4, run on 2026-10-07
by the Coding Agent with the importer at `coding/task-489-importer` 7095bffd,
into a fresh temporary store only.

`$PERRY_SCRATCH` below is
`/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/agent-a0d8e01dec029a860`,
derived by hand because the sandbox refused the derivation snippet. The work
directory is `$PERRY_SCRATCH/reconcile4-perry`: the store is `store.db` there,
and the anchor is `anchor/`. The importer's own report is
`$PERRY_SCRATCH/reconcile4-perry.json`. The independent check below is
`$PERRY_SCRATCH/verify.py`, and its output is
`$PERRY_SCRATCH/verify4-perry.json`.

## What changed in round 4

The round-2 architecture review blocked the importer's own split of a
reference cell. The user chose option B: the importer holds no split of its
own (spec § Round 4).

- **`depends_on` (item 1).** Each entry is taken whole. `tasks.jsonl` holds
  `perry-task § parse_depends` output, and this was checked first, by loading
  `bin/perry-task` in a scratch script (`$PERRY_SCRATCH/depends_check.py`):
  of 186 entries on 488 tasks, every one gives `parse_depends(entry) ==
  [entry]`, no list repeats an entry, and every list's `, ` join parses back
  to itself.
- **`Blocks` (item 2).** An ask's ids are the `blocks_ids` that
  `perry-task asks --all --json --root /Users/bytedance/proj/Perry` publishes,
  run as a subprocess. Its payload covers the same 107 asks with the same
  `Blocks` cells as `asks.jsonl`, and holds 79 ids. On every cell they equal
  the tokens round 3's split read (`$PERRY_SCRATCH/blocks_compare.py`): no
  cell differs, and no non-blank cell names no id.
- **Key results (item 3).** A key-result id is one that matches the id
  pattern `schema/state-schema.json` declares for a `kr` record of
  `linkage.jsonl`, `^(?:P\d{3}-)?O\d+-KR\d+$`, read through
  `lib.load_schema`. It takes both forms `_BLOCKS_ID` returns.
- **`REFERENCE_SPLIT` is removed (item 4).** A reference that resolves to no
  imported id still makes the run "not reconciled".

**The result is the same import.** `items.jsonl` is byte-identical to round
3's, sha256 `a516bd22…`, so the edges are the same 251. `events.jsonl`
differs only in the `at` of events 1 and 2, `init` and `template apply`,
which are timed at each run's own time (`$PERRY_SCRATCH/compare34.py`).

**The `perry-task asks` read, checked before it ran here.**
- On two scratch copies of `.perry/` and `perry/`, it changed no file under
  the copy (`$PERRY_SCRATCH/asks_probe.py`), and wrote nothing under
  `~/.cache/perry`.
- It is not free of writes outside the project. Like every `perry-task`
  command, it takes the project lock, a 0-byte file in the system temp
  directory keyed to the state root (`lib.project_lock`). On a fresh copy it
  created that file (`$PERRY_SCRATCH/lock_probe.py`). For this repository the
  file already existed, `perry-task-47cc6b34b8a24907.lock`; the run left it
  0 bytes and moved its mtime.
- Before any command, reads included, `perry-task` finishes a write that a
  crashed command left pending, named by a recovery marker in the state root.
  Neither project holds such a marker. If one did, the import stops: it
  compares every file under the state root and `.perry/` before and after
  the read.

## What changed in round 3 (unchanged in round 4)

Round 1's V4 review failed on the blank rule. The PMO's round-3 rules
(spec § Round 3) changed the importer as follows:

- **Blank cells (item 1).** A cell is unset when `lib.is_blank_cell` says so.
  That is the project's one blank rule, and the importer already used it.
  It takes an empty string and `—`, and also `-`, `n/a`, `TBD`, `none`, `?`,
  `待定` and the other declared spellings. This repository holds only `""`
  and `—`, so the import is unchanged by this rule.
- **Answers (item 2).** An answered ask's `answer` is now carried. It is the
  text `parsers.ask_answer` returns, or the status cell verbatim where that
  text is empty.
- **Reasons (item 3).** A cleared risk's `reason` is now its status cell
  verbatim. `parsers.status_is_cleared` decides "cleared".
- **The closing event.** The item's one move sets its `answer` or `reason`,
  as a live `item move` that sets a field writes it.
- **References (item 4).** A reference that resolves to no imported id makes
  the run "not reconciled". A key-result id is listed "for TASK-492"
  instead. Round 4 replaced how the references are read; see above.
- **Kernel errors (item 5).** A kernel call refused while reconciling is
  reported under `kernel.errors`, and the run is "not reconciled". No
  traceback is printed. This run had none.
- **Ceilings (item 6).** The ceiling reads the `id`, `task` and `record.id`
  keys of the old events.

So `items.jsonl` now differs from round 2's in 106 items: 104 asks carry an
`answer` and 2 risks a `reason`. Every other item is as in round 2. To check
this, the round-2 importer (`8649b63b`) was run again into
`$PERRY_SCRATCH/round2again-perry`. It reproduced round 2's `items.jsonl`,
sha256 `cb347f63…`. `$PERRY_SCRATCH/items_diff.py` then compared it with this
round's, item by item: 106 of 599 differ, and only in `fields.answer` (104)
and `fields.reason` (2).

## Inputs

These are read-only, and unchanged since round 1. Their bytes are identical
to `9509170c`, the branch base. `git diff --stat 9509170c a95fc07f -- perry/*.jsonl .perry/events.jsonl`
is empty, and the hashes match round 2's. Neither state root holds a
`perry-task` recovery marker (`.perry-task-transaction.json`).

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

Every byte under the checkout's `.perry/` and `perry/`, 1,474 files, gave
`state-sha256=7925ad42d9396509` before and after the round-4 import
(`$PERRY_SCRATCH/fingerprint.py`). It differs from round 3's value because
main has since changed other `perry/` files, such as the spec; the five input
stores above did not change. The two `ls -d` checks gave the same answer
before and after.

Every `bin/perry-kernel` call names `--store $PERRY_SCRATCH/reconcile4-perry/store.db`
and `--root $PERRY_SCRATCH/reconcile4-perry/anchor`, and runs with
`PERRY_KERNEL_TESTING=1`. The one `perry-task asks` call is the read described
above: the project's files were unchanged by it, and it moved the mtime of the
existing lock file in the system temp directory.

## The import

```
$ python3 bin/perry-kernel-migrate --root /Users/bytedance/proj/Perry --work $PERRY_SCRATCH/reconcile4-perry --json > $PERRY_SCRATCH/reconcile4-perry.json
(exit 0)
$ jq -c '[.reconciled, .not_reconciled_because, .kernel.errors]' $PERRY_SCRATCH/reconcile4-perry.json
[true,[],[]]
$ jq -c .criteria $PERRY_SCRATCH/reconcile4-perry.json
{"1_counts_per_type_and_state":true,"2_every_old_id_resolves":true,"3_next_id_above_every_issued_id":true,"4_import_refuses_a_store_that_is_not_empty":true,"5_replay_reproduces_the_items":true}
$ jq -c .import.result $PERRY_SCRATCH/reconcile4-perry.json
{"dir":"$PERRY_SCRATCH/reconcile4-perry/anchor/perry/export","items":599,"events":1177,"last_seq":1177,"verified":true}
```

The criteria below are checked a second time without the importer.
`verify.py` reads the old files with `json.loads` and the store only through
`bin/perry-kernel`, and derives each expected value itself.

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
```

`bin/perry-kernel query` with `count_by` `["type","state"]` gives:

| Type | Status | Old | Kernel |
|---|---|---|---|
| task | not_started / blocked / in_progress / review / done / dropped | 18 / 2 / 1 / 2 / 321 / 144 | 18 / 2 / 1 / 2 / 321 / 144 |
| ask | pending / answered | 3 / 104 | 3 / 104 |
| risk | open / cleared | 2 / 2 | 2 / 2 |

`verify.py` agrees. **PASS.**

## Criterion 2 — every old id resolves

`verify.py` found 599 old ids and 599 kernel ids, the same set, and
`bin/perry-kernel item get` failed for 0 of the 599. For each item it also
compared the state, every mapped field, the `answer` or `reason`, and the
attachments with the values it derived from the old row: 0 mismatches.
**PASS.**

## Criterion 3 — the next id is above every id ever issued

| Prefix | Highest id issued (stores, and the log's `id`, `task` and `record.id`) | Next id (`item create --dry-run`) |
|---|---|---|
| TASK | 494 | `TASK-495` |
| USER | 1006 | `USER-1007` |
| RX | 4 | `RX-005` |

The log's `task` key, on 206 `link-edge` and `link-unlinked` events, reaches
TASK-440. Its `record.id` key, on the 3 purges, reaches TASK-083. Both are below TASK-494, so
reading them changes no ceiling here. The log-only ids are still TASK-081,
082 and 083, the purged ones. No `ceiling:` event was needed, because they
sit below the highest stored id. **PASS.**

## Criterion 4 — `import` refuses a store that is not empty

```
$ bin/perry-kernel import --store … --root … --input '{"state_root":"perry"}'
store_not_empty: …/reconcile4-perry/store.db holds 1177 event(s); import needs an empty store
(exit 1)
```

**PASS.**

## Criterion 5 — replaying the imported events reproduces the imported items

```
a516bd228c78ddb4b39853309a6e4b5446debc139f8baa4c472a9bc552fcbf4d  anchor/perry/export/items.jsonl
1c0805707e972745d07b789cc76984152135f8c5527ae85b30a86ca41d7001d6  anchor/perry/export/events.jsonl
$ bin/perry-kernel export --store … --root …
effect "unchanged"; both sha256 identical after
$ (fresh store: import from a copy of that export, then export)
{"items":599,"events":1177,"last_seq":1177,"verified":true}; effect "unchanged"; both sha256 identical
```

`import` itself answered `"verified": true`. It replays every event, holding
each change to the template in force, and compares the replayed items with
`items.jsonl` byte for byte. **PASS.**

## Answers and reasons carried (items 2 and 3)

| What | Count | How |
|---|---|---|
| Ask answers | 104 | all 104 from `parsers.ask_answer`; 0 needed the status cell verbatim |
| Risk reasons | 2 | the status cell verbatim, for RX-001 and RX-002 |

Each value is set by the item's move event. The export's moves carry 104
`field:answer` changes and 2 `field:reason` changes. For example, USER-001's
status cell is `**answered 2026-08-16: 30 days**`, and its `answer` is
`30 days`. RX-002's status cell is `cleared 2026-08-16`, and that whole cell
is its `reason`. RX-001's `reason` is its whole status cell, 826 bytes.

**What is not carried as text.** For the 104 answers that `ask_answer` read,
the cell's `answered <date>:` part is not in the `answer`. The date stays in
`perry/asks.jsonl` and in git history. The ask's move is timed by the Dates
rule, at its last old status event. The 3 pending asks' status cells say
`pending` and nothing more.

## References (round 4: no split of the importer's own)

Each `depends_on` entry was taken whole: 186 entries. Each ask's references
are the `blocks_ids` of `perry-task asks --all --json`: 79 ids, 76 of them
task ids and 3 key results.

- **Resolved: 251 `blocks` edges** after duplicates are merged, as in round
  3: 172 task to task, from `depends_on`, and 79 ask to task, from 14 `USER-`
  entries in `depends_on` and the 76 task ids in `Blocks` cells. No edge is a
  self-edge. `verify.py` derived the same 251 edges from the old files.
- **`Blocks` cells that say something and name no id `perry-task` reads: 0.**
- **Resolved to no imported id: 0.** An unresolved reference would make the
  run "not reconciled", with exit 1.
- **For TASK-492: 3.** These are key results, which are not kernel items yet.
  TASK-492 must restore these edges once they are. No `O<n>-KR<m>` form
  appears in this repository's cells.

  | Ask | Field | Blocks |
  |---|---|---|
  | USER-927 | `blocks` | `P003-O2-KR3` |
  | USER-929 | `blocks` | `P003-O2-KR3` |
  | USER-931 | `blocks` | `P003-O2-KR3` |

## Cells that said nothing: unset, not imported (item 1)

A cell is unset when `lib.is_blank_cell` says so. The importer counts each
field by spelling. This repository holds no spelling other than `""` and
`—`.

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
rows.

## What was not carried, counted

- **`next_action` on closed tasks: 315 skipped by option A.** That is 219
  `done` and 96 `dropped`, counting only the cells that hold text. A further
  80 closed rows hold `—`, and those are counted as unset above.
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
- **Status text no field carries: 104**, the `answered <date>:` parts above.

## Moves clamped to their create: 2

| Item | Rule | Rule's time | Clamped to |
|---|---|---|---|
| USER-930 | last old status event | `2026-09-13T16:16:54Z` | `2026-09-14T00:00:00Z`, its `asked` date |
| RX-002 | `cleared` (`2026-08-16`, a date) | `2026-08-16T00:00:00Z` | `2026-08-16T10:33:04Z`, the start of the old log (it has no `opened` and no event) |

Each move's `note` says so. A pass over the exported events finds no move
timed before its item's create (`$PERRY_SCRATCH/events_check.py`).

## Date-only fields and this project's +08:00 clock

Unchanged since round 2. `lib.ts_moment`, the one converter, reads a date-only
value as 00:00 UTC, which is 08:00 on this project's +08:00 clock. This
repository holds 107 date-only values that time an event: 105 `asked` dates
and 2 `cleared` dates.

- The date lands after the item's own first event in 8 cases: USER-015, 903,
  904, 905, 906, 930, 931 and 1006. Each was asked between 00:16 and 05:45
  local time.
- Only USER-930's move fell before its create, and the clamp fixes that.
- No date falls on a different local day from its item's first event.

Every create timed by a date says so in its note. Reading dates as local
midnight would need a second converter, which
`tests/test_kr_progress_provenance.py § test_the_converter_has_exactly_one_home`
forbids in `bin/`. If the user wants those eight creates at their ask events
instead, that is a new rule to decide.

## Other things the reviewer should see

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
- **Open `Next action` cells over 300 bytes: 7**, imported as they are:
  TASK-238, 286, 309, 334, 220, 371 and 393.
