# TASK-489 — reconciliation: SkyTonight

Spec: `TASK-489-spec.md`, criteria 1–5. Project `/Users/bytedance/proj/SkyTonight`,
state root `doc/perry`, from its `.perry/config.jsonl`. Run on 2026-09-29 by
the Coding Agent with the importer at `coding/task-489-importer` 02af3f37,
into a temporary store only. **SkyTonight is read-only, and nothing was
written under it.**

`$PERRY_SCRATCH` below is
`/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/agent-a990cdfa91aeda615`,
the Perry worktree's scratch directory, derived by hand because the sandbox
refused the derivation snippet. The work directory is
`$PERRY_SCRATCH/reconcile-skytonight`. The whole transcript is
`$PERRY_SCRATCH/reconcile-skytonight.log`, and the importer's report is
`$PERRY_SCRATCH/reconcile-skytonight.json`.

## Inputs

These are read-only:

| File | sha256 |
|---|---|
| `doc/perry/tasks.jsonl` | `efad45d20780c324056ac884c4ce7489d3520344d2ce338c75b51c5adac8d425` (32 rows) |
| `doc/perry/risks.jsonl` | `b654ac0f3ae1ff0700c6b3671e36671b0124471b16aacf6f42474b101d1ffe2b` (2 rows) |
| `.perry/events.jsonl` | `b13af863c405f5d30dbdfa701a52ff97912e404e8da4683220776fed49ab5416` (209 lines) |
| `.perry/config.jsonl` | `e4b22d3798b3b7af1f891c7e363f1afb062a3a6ab8fd7e4b8a4ab1d7af7675ea` |

`asks.jsonl`, `intake.jsonl` and `cadence.jsonl` are absent. **There is no
intake or cadence row, so no stop for that case.** The longest `Next action`
cell is 158 bytes, on TASK-024 (`done`), and the one open row's is 83 bytes.
No row fits the long-cell case.

## Safety

```
$ ls -d /Users/bytedance/proj/Perry/.git/perry /Users/bytedance/proj/SkyTonight/.git/perry     # before
ls: /Users/bytedance/proj/Perry/.git/perry: No such file or directory
ls: /Users/bytedance/proj/SkyTonight/.git/perry: No such file or directory
$ ls -d …                                                                                      # after
ls: /Users/bytedance/proj/Perry/.git/perry: No such file or directory
ls: /Users/bytedance/proj/SkyTonight/.git/perry: No such file or directory
```

The whole SkyTonight tree was fingerprinted before and after the run: every
entry's path, size and mtime, and every byte under `.perry/` and `doc/perry/`.

```
before: entries=11776 listing-sha256=6d8d888806bc6cb2 state-files=282 state-sha256=e5cba9fef1962261
after:  entries=11776 listing-sha256=6d8d888806bc6cb2 state-files=282 state-sha256=e5cba9fef1962261
```

The same fingerprint was also taken around the first trial run, earlier the
same day, and was identical there too.

Every `bin/perry-kernel` call names `--store $PERRY_SCRATCH/reconcile-skytonight/store.db`
and `--root $PERRY_SCRATCH/reconcile-skytonight/anchor`, and runs with
`PERRY_KERNEL_TESTING=1`.

## The import

```
$ bin/perry-kernel-migrate --root /Users/bytedance/proj/SkyTonight --work $PERRY_SCRATCH/reconcile-skytonight --json > $PERRY_SCRATCH/reconcile-skytonight.json
(exit 0)
$ jq -c .criteria $PERRY_SCRATCH/reconcile-skytonight.json
{"1_counts_per_type_and_state":true,"2_every_old_id_resolves":true,"3_next_id_above_every_issued_id":true,"4_import_refuses_a_store_that_is_not_empty":true,"5_replay_reproduces_the_items":true}
$ jq -c .import.result $PERRY_SCRATCH/reconcile-skytonight.json
{"dir":"$PERRY_SCRATCH/reconcile-skytonight/anchor/doc/perry/export","items":34,"events":68,"last_seq":68,"verified":true}
```

## Criterion 1 — equal counts per type and per status

```
$ grep -o '"status": "[a-z_]*"' doc/perry/tasks.jsonl | sort | uniq -c
  31 "status": "done"
   1 "status": "in_progress"
$ ls doc/perry/asks.jsonl
ls: …/doc/perry/asks.jsonl: No such file or directory          (no ask store: 0 asks)
$ grep -oE '"status": "(open|cleared)' doc/perry/risks.jsonl | sort | uniq -c
   2 "status": "open
$ bin/perry-kernel query --store … --root … --input '{"count_by":["type","state"],"limit":1}' | jq -c '.result.counts[] | [.key.type, .key.state, .n]'
["risk","open",2]
["task","done",31]
["task","in_progress",1]
```

| Type | Status | Old | Kernel |
|---|---|---|---|
| task | done / in_progress | 31 / 1 | 31 / 1 |
| ask | — | 0 | 0 |
| risk | open | 2 | 2 |

**PASS.**

## Criterion 2 — every old id resolves

```
$ grep -ho '"id": "[A-Z]*-[0-9]*"' tasks, risks | sort -u > old-ids;  wc -l
      34
$ bin/perry-kernel query … --input '{"limit":0}' | jq -r '.result.items[].id' | sort -u > kernel-ids;  wc -l
      34
$ comm -3 old-ids kernel-ids | wc -l
       0
$ (each of the 34 ids through bin/perry-kernel item get)
  item get failed for 0 of 34 ids
```

**PASS.**

## Criterion 3 — the next id is above every id ever issued

```
$ (highest TASK id in the old stores and .perry/events.jsonl) 032   → ["dry_run","TASK-033"]
$ (highest USER id)                                          none  → ["dry_run","USER-001"]
$ (highest RX id)                                            002   → ["dry_run","RX-003"]
$ grep -o '"event": "purge", "id": "[A-Z]*-[0-9]*"' .perry/events.jsonl
(none)
```

Each next id comes from `bin/perry-kernel item create … --dry-run`, and the
ceilings the importer seeded are:

```
{"TASK":{"stored_max":32,"issued_max":32,"log_only_ids":[],"seed":null},
 "USER":{"stored_max":null,"issued_max":null,"log_only_ids":[],"seed":null},
 "RX":{"stored_max":2,"issued_max":2,"log_only_ids":[],"seed":null}}
```

The log's other ids (`accepted`, `slices-v1`, `closeout-score`,
`accepted-deliverable`) carry no template prefix. **PASS.**

## Criterion 4 — `import` refuses a store that is not empty

```
$ bin/perry-kernel import --store … --root … --input '{"state_root":"doc/perry"}'
perry-kernel: store_not_empty: …/reconcile-skytonight/store.db holds 68 event(s); import needs an empty store
(exit 1)
[false,"store_not_empty","…/reconcile-skytonight/store.db holds 68 event(s); import needs an empty store"]
```

**PASS.**

## Criterion 5 — replaying the imported events reproduces the imported items

`import` answered `"verified": true`. The store's own export found both files
already holding its bytes, and a fresh store imported from that export gives
the same bytes again:

```
a8ce77e95d576ffa729eea46837d087a564da39e196e2b55ca47a8b4ce289649  anchor/doc/perry/export/items.jsonl
2a6d2387891dfa06176ab4ddf94720ef95660f0104834916a273632df9fbc6c1  anchor/doc/perry/export/events.jsonl
$ bin/perry-kernel export --store … --root …
["unchanged",{"items.jsonl":"a8ce77e95d576ffa","events.jsonl":"2a6d2387891dfa06"}]
$ (fresh store: import from that export, then export)
["written",34,68,true]
"unchanged"
$ cmp items.jsonl second/items.jsonl    (exit 0)
$ cmp events.jsonl second/events.jsonl  (exit 0)
```

**PASS.**

## What was not carried, counted

- **`next_action` on closed tasks: 31 skipped**, all on `done` rows. `grep`
  counts the same 31. Two of them held the blank marker `—`.
- **Dropped fields, rows that held a value:**

  | Field | Rows |
  |---|---|
  | `tasks.group` | 32 |
  | `tasks.order` | 1 |
  | `tasks.stage` | 0 |
  | `tasks.arrived` | 0 |
  | `tasks.stage_since` | 0 |
  | `tasks.commitment` | 0 |
  | `tasks.role` | 0 |
  | `risks.order` | 2 |

  `tasks.parent` held no value.
- **Status text beyond the state: none.** Both risks are `open`.

## Other things the reviewer should see

- **Relations: 40 `blocks` edges**, all task to task from `depends_on`, with
  no unresolved reference and no self-edge.
- **Attachments: 23**, from `design_refs` (`DESIGN-001`).
- **Times.** Every create is timed at `created` or `opened`, and every one of
  the 32 moves at the last old status event. No move precedes its create.
- **Events: 68.** That is `init`, `template apply`, 34 creates and 32 moves.
  No ceiling event was needed.
