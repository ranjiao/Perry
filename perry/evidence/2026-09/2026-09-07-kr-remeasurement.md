# Phase 003 — two KR re-measurements, 2026-09-07

> Written by the PMO. Every number below is a command re-run on `2070265`, not
> a claim. The phase's own operating rule: *every KR movement cites a command's
> output, never a claim* — `phase/003-storage-code.md § Operating Rules`.

Two KRs needed measuring and neither was work: `P003-O2-KR1` carried **no
asserted value at all** while all four of its linked rows were `done`, and
`P003-O1-KR2`'s asserted value had gone **stale** when `TASK-067` moved after it.

## `P003-O2-KR1` — target 0, measured 0. **DoD item 3 is met.**

*"Call sites in `bin/` that read the track register from `.perry/config.md` as
truth while `.perry/config.jsonl` exists, excluding the drift-comparison
reader."*

**Counted as invocations, never as mentions** — this phase's first operating
rule, and the defect it names cost roughly ten recurrences in phase 002.

```
$ grep -rn "parse_tracks(" bin/ viewer/ | grep -v "def parse_tracks"
bin/perry-state:1172:    return parse_tracks(cfg.read_text(errors="replace")), source
```

**Exactly one invocation.** A name-based grep returns **eighteen** hits across
`bin/perry-task`, `bin/perry-diagnose`, `bin/perry-lint`, `bin/perry-goals`,
`bin/perry_md_store.py` and `bin/perry-state` — and **seventeen of them are
comments and docstrings** naming the function. Counting names here would have
reported the KR as massively unmet.

That one call sits inside `declared_tracks_detail` (`bin/perry-state:1158`),
which reaches it **only when there is no store**:

```python
stored, source = stored_tracks(project_root)
if stored is not None:
    return stored, source          # <- the store, on any project that has one
cfg = project_root / ".perry" / "config.md"
if not cfg.exists():
    return [dict(DEFAULT_TRACK)], source
return parse_tracks(cfg.read_text(errors="replace")), source   # <- fallback only
```

Observable confirmation rather than inference — `perry-state --json` on this
project:

```
tracks_source = store
```

**So the count of call sites reading the markdown as truth while the store
exists is 0, and the target is 0.** `current: 0` is now recorded.

**This may have been true for days with nothing saying so.** All four linked
rows — `TASK-095`, `TASK-233`, `TASK-247`, `TASK-283` — were already `done`, and
the KR's `current_provenance` read `unasserted`. A Definition-of-Done item can
sit met and unrecorded, and nothing in the system says so; that is worth more
than the number.

## `P003-O1-KR2` — still met, and its population has grown past its target

*"Stores for which one run of `perry-lint --root .` prints a drift verdict."*
Target 6, asserted 6 on 2026-09-03 — then `TASK-067` moved `review → done` at
`2026-09-04T03:06:30Z`, after the assertion, which is what `perry-state`
reports as stale.

One run now prints **seven**, not six:

```
· store:         372 record(s), 0 row(s) drifted
· risks store:     4 record(s), 0 risk(s) drifted
· intake store:    0 record(s), 0 row(s) drifted
· ask store:      21 record(s), 0 ask(s) drifted
· OKR store:      51 record(s), 0 row(s) drifted
· config store:    9 record(s), 0 row(s) drifted
· linkage store: 121 record(s), 0 row(s) drifted
```

The seventh is `linkage.jsonl`, added **during this phase** by `TASK-276` /
`277` / `278`, and its verdict is **real** — before row C merged the same line
read *"comparison incomplete — drift is unchecked, not clean"*.

**`current` was deliberately left at 6 against target 6.** Raising both to 7 is
a **KR change**, which belongs to the user and not to a re-measurement. Flagged
for scoring: on the honest reading this KR is **7 of 7**.

## The drift verdict proved itself on this edit, independently of its review

Adding `current: 0` to the register and **not** yet syncing the store produced:

```
⚠ perry/linkage.jsonl [linkage-store-drift] P003-O2-KR1 differs between the
  store and phase/003-linkage.md. The store is what the readers answer from
  (DESIGN-015 § 5.6), so the document is the stale side unless `perry-goals`
  wrote it last.
· linkage store: 121 record(s), 1 row(s) drifted
```

`TASK-278`'s claim that the verdict is real is therefore corroborated by an
edit its author never made and its reviewer has not yet seen. Note also what it
did **not** flag: the `metric:` prose changes on both KRs produced no drift,
which is correct — `DESIGN-015 § 5.4` keeps the prose in the document and the
typed facts in the store, and the comparison covers the typed facts only.

## What this measurement cost, and the row it belongs to

Recording a fresh measurement date meant bumping the register's `updated:`
field. Doing so **rewrote `declared_at` on all 115 `edge` and `unlinked`
records** to today — 115 records claiming a declaration action that never
happened. This is `TASK-155` exactly, filed 2026-08-21 and 17 days past its
5-day SLA, reproduced here for the first time.

`updated:` was reverted, restoring every `declared_at`. Verified by diffing the
store against its pre-edit copy **in both directions**: it now differs by
**exactly one field**, the `current: 0` that was the point.

**The defect forces a choice between two falsehoods**, and this is the record of
which was taken: bump `updated` and 115 provenance dates become false, or leave
it and `perry-state` reports today's measurement as stale — which both KRs now
wrongly show. **The stale flag was chosen because it is a visible wrong answer
and a re-dated declaration is an invisible one.**

## Verified after

```
0 error(s), 38 warning(s)
· linkage store: 121 record(s), 0 row(s) drifted
```
