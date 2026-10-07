# TASK-489 — reconciliation: SkyTonight

Spec: `TASK-489-spec.md`, criteria 1–5, with § Round 3 as decided by the PMO
on main at `d2cae7ff`. Project `/Users/bytedance/proj/SkyTonight`; its state
root is `doc/perry`, from its `.perry/config.jsonl`. Round 3 ran on
2026-10-07, by the Coding Agent, with the importer at
`coding/task-489-importer` a3bc4e80, into a fresh temporary store only.
**SkyTonight is read-only, and nothing was written under it.**

`$PERRY_SCRATCH` below is
`/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/agent-a0d8e01dec029a860`,
the Perry worktree's scratch directory. It was derived by hand, because the
sandbox refused the derivation snippet. The work directory is
`$PERRY_SCRATCH/reconcile3-skytonight`. The importer's report is
`$PERRY_SCRATCH/reconcile3-skytonight.json`. The independent check is
`$PERRY_SCRATCH/verify.py`, and its output is
`$PERRY_SCRATCH/verify3-skytonight.json`.

## What changed in round 3

The round-3 rules (spec § Round 3) change nothing that SkyTonight holds:

- **Blank cells (item 1).** A cell is unset when `lib.is_blank_cell` says so.
  Here the only such cells are two `—` cells in `next_action`, both on `done`
  rows, as in round 2.
- **Answers and reasons (items 2 and 3).** SkyTonight has no ask store, and
  neither of its two risks is cleared. So no `answer` or `reason` is
  carried: 0 and 0.
- **References (item 4).** Every `depends_on` entry resolves. No reference
  resolves to nothing, and none names a key result, so nothing is listed for
  TASK-492.
- **Kernel errors (item 5).** No kernel call was refused.
- **Ceilings (item 6).** The old log names ids only under `id`. No event
  carries `task` or `record`.

`items.jsonl` is byte-identical to round 2's, sha256 `a8ce77e9…`. To compare
the events, the round-2 importer (`8649b63b`) was run again into
`$PERRY_SCRATCH/round2again-skytonight`. Its `events.jsonl` differs from this
round's only in the `at` of events 1 and 2, `init` and `template apply`, which
are timed at each run's own time (`$PERRY_SCRATCH/events_diff.py`).

## Inputs

These are read-only, and unchanged since round 1:

| File | sha256 |
|---|---|
| `doc/perry/tasks.jsonl` | `efad45d20780c324056ac884c4ce7489d3520344d2ce338c75b51c5adac8d425` (32 rows) |
| `doc/perry/risks.jsonl` | `b654ac0f3ae1ff0700c6b3671e36671b0124471b16aacf6f42474b101d1ffe2b` (2 rows) |
| `.perry/events.jsonl` | `b13af863c405f5d30dbdfa701a52ff97912e404e8da4683220776fed49ab5416` (209 lines) |
| `.perry/config.jsonl` | `e4b22d3798b3b7af1f891c7e363f1afb062a3a6ab8fd7e4b8a4ab1d7af7675ea` |

`asks.jsonl`, `intake.jsonl` and `cadence.jsonl` are absent. **There is no
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

The whole SkyTonight tree was fingerprinted with
`$PERRY_SCRATCH/fingerprint.py` before the round-3 import, after it, and
after the round-2 re-run above. The two `ls -d` checks gave the same answer
at each of those three points. The fingerprint covers every entry's path,
size and mtime, `.git` included, and every byte under `.perry/` and
`doc/perry/`:

```
before:          entries=11776 listing-sha256=59dde36f75ef34e5 state-files=282 state-sha256=e8689645fbc5a738
after round 3:   entries=11776 listing-sha256=59dde36f75ef34e5 state-files=282 state-sha256=e8689645fbc5a738
after re-run:    entries=11776 listing-sha256=59dde36f75ef34e5 state-files=282 state-sha256=e8689645fbc5a738
```

The values are not comparable with round 2's, which another script computed.

Every `bin/perry-kernel` call names
`--store $PERRY_SCRATCH/reconcile3-skytonight/store.db` and
`--root $PERRY_SCRATCH/reconcile3-skytonight/anchor`, and runs with
`PERRY_KERNEL_TESTING=1`.

## The import

```
$ python3 bin/perry-kernel-migrate --root /Users/bytedance/proj/SkyTonight --work $PERRY_SCRATCH/reconcile3-skytonight --json > $PERRY_SCRATCH/reconcile3-skytonight.json
(exit 0)
$ jq -c '[.reconciled, .not_reconciled_because, .kernel.errors]' $PERRY_SCRATCH/reconcile3-skytonight.json
[true,[],[]]
$ jq -c .criteria $PERRY_SCRATCH/reconcile3-skytonight.json
{"1_counts_per_type_and_state":true,"2_every_old_id_resolves":true,"3_next_id_above_every_issued_id":true,"4_import_refuses_a_store_that_is_not_empty":true,"5_replay_reproduces_the_items":true}
$ jq -c .import.result $PERRY_SCRATCH/reconcile3-skytonight.json
{"dir":"$PERRY_SCRATCH/reconcile3-skytonight/anchor/doc/perry/export","items":34,"events":68,"last_seq":68,"verified":true}
```

`verify.py` checks the criteria a second time. It reads the old files with
`json.loads`, and the store only through `bin/perry-kernel`.

## Criterion 1 — equal counts per type and per status

| Type | Status | Old | Kernel |
|---|---|---|---|
| task | done / in_progress | 31 / 1 | 31 / 1 |
| ask | — | 0 | 0 |
| risk | open | 2 | 2 |

**PASS.**

## Criterion 2 — every old id resolves

34 old ids and 34 kernel ids, the same set. `bin/perry-kernel item get`
failed for 0 of the 34. The state, every mapped field and the attachments
match the old rows: 0 mismatches. **PASS.**

## Criterion 3 — the next id is above every id ever issued

| Prefix | Highest id issued | Next id (`item create --dry-run`) |
|---|---|---|
| TASK | 32 | `TASK-033` |
| USER | none | `USER-001` |
| RX | 2 | `RX-003` |

The log has no purge, and no `ceiling:` event was needed. The log's other ids
(`accepted`, `slices-v1`, `closeout-score`, `accepted-deliverable`) carry no
template prefix. **PASS.**

## Criterion 4 — `import` refuses a store that is not empty

```
$ bin/perry-kernel import --store … --root … --input '{"state_root":"doc/perry"}'
store_not_empty: …/reconcile3-skytonight/store.db holds 68 event(s); import needs an empty store
(exit 1)
```

**PASS.**

## Criterion 5 — replaying the imported events reproduces the imported items

```
a8ce77e95d576ffa729eea46837d087a564da39e196e2b55ca47a8b4ce289649  anchor/doc/perry/export/items.jsonl
f6be2097436b529fdc7663b437b02d8446bebf881d2c62577d922e96121da712  anchor/doc/perry/export/events.jsonl
$ bin/perry-kernel export --store … --root …
effect "unchanged"; both sha256 identical after
$ (fresh store: import from a copy of that export, then export)
{"items":34,"events":68,"last_seq":68,"verified":true}; effect "unchanged"; both sha256 identical
```

`import` answered `"verified": true`. **PASS.**

## Answers, reasons and references (items 2–4)

| What | Count |
|---|---|
| Ask answers carried | 0 (no ask store) |
| Risk reasons carried | 0 (both risks are `open`) |
| Status text no field carries | 0 |
| `blocks` edges | 40, all task to task from `depends_on` |
| References that resolve to no imported id | 0 |
| For TASK-492 (key results) | none |
| Self-edges | 0 |

## Cells that said nothing: unset, not imported (item 1)

| Field | `""` | `—` | Total |
|---|---|---|---|
| `tasks.next_action` | 0 | 2 | 2 (both on `done` rows) |
| every other mapped field | 0 | 0 | 0 |

No other spelling of the one blank rule appears.

## What was not carried, counted

- **`next_action` on closed tasks: 29 skipped by option A**, all on `done`
  rows. A further 2 closed rows hold `—`, and those are counted as unset
  above.
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

## Moves clamped to their create: 0

No move needed clamping. A pass over the exported events finds no move timed
before its item's create (`$PERRY_SCRATCH/events_check.py`).

## Date-only fields and the +08:00 clock

Unchanged since round 2. The only date-only values here are the two risks'
`opened` dates. Read as 00:00 UTC, neither lands after its risk's own
`risk-add` event, and neither falls on a different local day. Each create's
note says how it was timed (`timed by opened 2026-09-16, a date, read as
00:00 UTC`).

## Other things the reviewer should see

- **Attachments: 23**, all `DESIGN-001`, from `design_refs`.
- **Times.** 32 creates are timed at `created` and 2 at `opened`. All 32 moves
  are timed at the last old status event.
- **Events: 68.** That is `init`, `template apply`, 34 creates and 32 moves.
- **No `Next action` cell fits the long-cell case.** The longest is 158 bytes,
  on TASK-024, a `done` row.
