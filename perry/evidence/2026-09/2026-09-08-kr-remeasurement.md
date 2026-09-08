# KR re-measurement — P003-O1-KR2 and P003-O2-KR1

> **Date**: 2026-09-08 · phase #003 storage-code, day 12
> **Why this file exists**: `perry-state --json` warned that both KRs' `current`
> was asserted before a linked task moved. The user decided on 2026-09-08 **not
> to re-assert them in the register**, because writing an assertion date is the
> same action as re-dating 115 linkage records (see § The write that was not
> made). This file is therefore the measurement of record: `score-phase` cites
> it instead of a register timestamp.
> **Commands were run on `main` at `ee5f3c42`, in `/Users/bytedance/proj/Perry`.**

## P003-O1-KR2 — stores for which one `perry-lint --root .` run prints a drift verdict

Registered: `target 6`, `current 6` (asserted 2026-09-03T06:06:45Z).

```
$ python3 bin/perry-lint --root . | grep -E "record\(s\), .* drifted"
  · store: 389 record(s), 0 row(s) drifted
  · risks store: 4 record(s), 0 risk(s) drifted
  · intake store: 0 record(s), 0 row(s) drifted
  · ask store: 23 record(s), 0 ask(s) drifted
  · OKR store: 51 record(s), 0 row(s) drifted
  · config store: 9 record(s), 0 row(s) drifted
  · linkage store: 124 record(s), 1 row(s) drifted
```

**Measured: 7 verdicts in one run, against a target of 6.**

The seventh is `linkage`, declared during this phase by TASK-276/277/278. It
prints a real verdict, not a deferred one — and the `1 row(s) drifted` it
reports is `P003-O3-KR2`, this phase's own computed KR (`store` vs
`phase/003-linkage.md`; the store is the side readers answer from, per
DESIGN-015 § 5.6).

This reproduces what the KR's own metric text already flagged for scoring:
*"on the honest reading this KR is 7 of 7."* The registered `current: 6`
against `target: 6` is not wrong — it is a smaller population than the one
that exists today. **Raising both to 7 is a KR change and belongs to the
user**, which is why this file records the number and does not write it.

## P003-O2-KR1 — `bin/` sites reading the track register from `.perry/config.md` as truth

Registered: `target 0`, `current 0` (asserted 2026-09-03T06:06:45Z).

The KR's operating rule is this phase's own: **count invocations, not
mentions.**

```
$ grep -rn "parse_tracks(" bin/ viewer/ | grep -v "def parse_tracks"
bin/perry-state:1172:    return parse_tracks(cfg.read_text(errors="replace")), source
```

**Measured: 1 invocation, 0 of which read the markdown as truth.**

The single call sits inside `declared_tracks_detail`, which returns
`stored_tracks()` first and reaches `parse_tracks` **only when there is no
store**. The KR's population is sites that read the markdown "as truth *while*
`.perry/config.jsonl` exists" — a store-absent fallback is not in it.

Observable confirmation on this project: `perry-state --json` reports
`tracks_source: "store"`.

**Verdict: 0, unchanged. The registered value is correct.**

## The write that was not made, and why

Recording either number in the register means bumping `updated:` in
`phase/003-linkage.md`. That field is read by two consumers:

| Consumer | Reads `updated:` as | Code |
|---|---|---|
| linkage records | `declared_at` — when this edge was declared | `bin/perry-tasks:1612` |
| KR provenance | `current_provenance.asserted_at` — when the number was arrived at | `bin/lib/__init__.py:1066` |

`perry/linkage.jsonl` currently holds **115 records carrying
`declared_at: 2026-09-03T06:06:45Z`**, all of them that same field. So the act
of recording one fresh measurement would:

1. re-date all 115 records to today, and
2. mark all four asserted `current` values as freshly asserted — **including
   the two that are genuinely stale**, erasing the signal being acted on.

`bin/perry-goals:2209-2224` documents this at the write site, warns on every
write that would do it (`current_assertions_redated`), and states why it is not
fixed there: a per-KR assertion date is a new field in
`schema/state-schema.json`, which is on `.perry/hook.md § High-stakes
operations` under **the claim surface**.

This is `TASK-155`, open since 2026-08-21 and reproduced live on 2026-09-07.

**User decision, 2026-09-08**: do not re-assert. Carry these measured numbers
into `score-phase` citing this file, leave the register's `stale` warning
standing because it is true, and defer `TASK-155` to phase 004.

## What this file does not settle

- **Whether `P003-O1-KR2`'s target moves 6 → 7.** A KR change, not a
  measurement. Open for the user at `score-phase`.
- **The `P003-O3-KR2` linkage drift.** Clearing it is a `perry-goals` render,
  and any render bumps `updated:` — so it carries the same cost as the write
  declined above and is deferred with it.
