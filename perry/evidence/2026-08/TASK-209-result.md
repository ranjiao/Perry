# TASK-209 — result: the store-drift census covers six stores, not two

> Serves **P003-O1-KR2** (`perry/phase/003-storage-code.md`): *stores for which
> one run of `perry-lint --root .` prints a drift verdict*. Target **6 of 6**,
> baseline **2 of 6** (tasks, risks).
>
> Verified 2026-08-29 by the PMO, against code that had already landed. Rung **V3**.

## Why this file is written a day after the code landed

The row was dispatched on 2026-08-28 and its `Next action` still read
`dispatched to claude-subagent; awaiting RESULT` when this session opened. The
dispatch limiter reported **no active dispatches**, and the work was already on
`main`. The agent's run stalled on a watchdog before it could report back, and
the commit was made on the user's explicit instruction — recorded in the commit
message of `e993d85`.

So the row sat `in_progress` while its deliverable was merged and green. That is
the third instance in two days of the limiter's bookkeeping disagreeing with
what actually ran (`journal/2026-08/2026-08-28.md` records the other two: an ESC
that killed two agents, and a reserved slot whose dispatch call was never made).
**The verification below was therefore run fresh rather than taken from the
commit message**, because a self-report from a run that did not finish is not
evidence.

## What landed

| Commit | Subject |
|---|---|
| `e993d85` | TASK-209: the store-drift census covers six stores, not two |
| `b7cef79` | TASK-209 fix: the entry point goes last, so the appended tests run standalone |
| `5cac6b5` | Merge `coding/task-209-store-drift-census` |

`bin/perry-lint` +220 lines, `tests/test_store_drift.py` +289 lines.

## Verification, re-run 2026-08-29

**1 · The census prints a verdict line for all six declared stores.**
`python3 bin/perry-lint --root .`:
```
  · store: 225 record(s), 0 row(s) drifted
  · risks store: 4 record(s), 0 risk(s) drifted
  · no `intake.jsonl` — drift against the intake store is unchecked, not clean
  · no `asks.jsonl` — drift against the ask store is unchecked, not clean
  · OKR store: 36 record(s), 0 row(s) drifted
  · config store: 9 record(s), 0 row(s) drifted
```
Six lines for the six projection stores declared in `schema/state-schema.json §
claims[]` — `tasks.jsonl`, `okr.jsonl`, `risks.jsonl`, `intake.jsonl`,
`asks.jsonl`, `.perry/config.jsonl`. Baseline was two: `okr.jsonl` and
`.perry/config.jsonl` printed nothing at all while `perry-okr diff` and
`perry-config diff` both worked and the census called neither.

**2 · The test suite is green.** `python3 tests/test_store_drift.py`:
```
...............................................
Ran 47 tests in 37.632s

OK
```

**3 · The gate has been shown able to go red** — the phase's operating rule, and
phase 002's lesson 4. `e993d85`'s message records two mutations and one removal
run on a scratch copy of the state root before the green was believed: editing
`KR-O1.1`'s metric cell moves the OKR line to `1 row(s) drifted` and warnings 4
→ 5; editing the intake track's WIP cell moves the config line to `1 row(s)
drifted`; deleting `okr.jsonl` produces `unchecked, not clean`.

That third check is re-run independently and at six-store scale in
**`evidence/2026-08/TASK-229-result.md`**, which removes every one of the six in
turn. All six report `unchecked`. The two claims are therefore not resting on
the same unfinished run.

## Verdict

**6 of 6.** `P003-O1-KR2` is at target. ADR-007's guarantee — a store is
canonical and its markdown is a projection — is now checkable for every store
Perry declares, rather than for one of six.

## What this does not close

`P003-O1-KR2` also carries **TASK-067** (*the writer can destroy the table it
writes to, and `perry-lint` cannot see it*), which is `blocked` and untouched by
this row. A census that reports drift is not the same as a writer that cannot
ragged-row its own table.
