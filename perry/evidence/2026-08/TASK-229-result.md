# TASK-229 — result: *no store* and *clean* are six different answers, measured

> Serves **P003-O1-KR3** (`perry/phase/003-storage-code.md`): *stores that report
> `unchecked` rather than `clean` when the store file is removed, **measured by
> removing each one***. Target **6 of 6**, baseline **2 of 6**.
>
> Measured 2026-08-29 by the PMO. Rung **V3**.

## How it was run

The spec declares `Executor: manual — the procedure removes state files. It is
safe only against a scratch copy.` That instruction was followed literally: the
repository was copied to a scratch tree and **every removal below happened
there**, never in `/Users/bytedance/proj/Perry`.

```
rsync -a --exclude .git --exclude __pycache__ --exclude 'worktree*' \
  /Users/bytedance/proj/Perry/ <scratch>/t229/
cd <scratch>/t229
```

Each store was moved aside with `mv <store> <store>.bak`, `python3 bin/perry-lint
--root .` was run, and the store was moved back before the next one. The lines
below are that command's actual output, filtered to the census, not a summary.

## Baseline — every store that exists, in place

```
  · store: 225 record(s), 0 row(s) drifted
  · risks store: 4 record(s), 0 risk(s) drifted
  · no `intake.jsonl` — drift against the intake store is unchecked, not clean
  · no `asks.jsonl` — drift against the ask store is unchecked, not clean
  · OKR store: 36 record(s), 0 row(s) drifted
  · config store: 9 record(s), 0 row(s) drifted
```

Six declared projection stores, six lines. `intake.jsonl` and `asks.jsonl` are
absent on this project today — they are the two the baseline already counted,
and they are re-measured below rather than assumed.

`.perry/events.jsonl` is a seventh declared `.jsonl` in `claims[]` and is **not**
one of the six: it is the event log, derived and disposable, projected from
nothing. The census is right not to carry a line for it.

## The six removals, one quoted verdict each

**1 · `perry/tasks.jsonl` removed**
```
  · no `tasks.jsonl` — drift against the store is unchecked, not clean
```

**2 · `perry/okr.jsonl` removed**
```
  · no `okr.jsonl` — drift against the OKR store is unchecked, not clean
```

**3 · `perry/risks.jsonl` removed**
```
  · no `risks.jsonl` — drift against the risks store is unchecked, not clean
```

**4 · `perry/intake.jsonl` removed** (already absent — the baseline case, re-read)
```
  · no `intake.jsonl` — drift against the intake store is unchecked, not clean
```

**5 · `perry/asks.jsonl` removed** (already absent — the baseline case, re-read)
```
  · no `asks.jsonl` — drift against the ask store is unchecked, not clean
```

**6 · `.perry/config.jsonl` removed**
```
  · no `.perry/config.jsonl` — drift against the config store is unchecked, not clean
```

## Verdict

**6 of 6.** No store reports `clean` while absent. `P003-O1-KR3` is at target,
and unlike its identically-numbered predecessor `P002-O1-KR3` — which scored
0.33 because its metric said "reported" without saying by what — every one of
the six numbers above is a removal that actually happened.

The two answers stay textually distinct in both directions, which is what makes
the check meaningful rather than tautological: a present store says
`N record(s), 0 row(s) drifted`, an absent one says `unchecked, not clean`.
Neither sentence can be mistaken for the other by a reader or by a grep.

## Finding, filed rather than fixed here

**The tasks store is the only one of the six whose census line does not name
it.** Present, it reads `· store: 225 record(s)`; absent, `drift against the
store is unchecked`. The other five all carry their name — `risks store`, `OKR
store`, `config store`, `intake store`, `ask store`. On a six-line census the
unnamed line is the one a reader has to count positions to identify, and
`tasks.jsonl` is the store that matters most.

This is a one-word defect in `bin/perry-lint` and it is **not** fixed in this
row: TASK-229's deliverable is six measurements, and changing the string the
measurement quotes in the same commit would leave the evidence above describing
output that no longer exists. Filed to `## Intake`.
