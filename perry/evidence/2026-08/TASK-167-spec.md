# TASK-167 — three smoke-test rows are in the live store, and there is no way to remove one

Dispatch mode: auto
Verification: V3
Re-verified: 2026-08-28 against `9653156`

## The measurement

```
$ grep -E '"id": "TASK-08[123]"' perry/tasks.jsonl
{"id": "TASK-081", "title": "t", "status": "dropped", "priority": "P1",
 "created": "2026-08-18T18:48:30", …}   TASK-082 …:34   TASK-083 …:40
```

Three rows, title `t`, six seconds apart, every optional field empty. A smoke
test of `perry-task add` from 2026-08-18, left behind.

**Where they are visible, measured rather than assumed:**

| surface | count |
|---|---|
| `perry/tasks.jsonl` | 3 |
| `perry-task list --all --json` → `tasks[]` | **3 of 176** |
| `perry/BOARD.md` | **0** — `dropped` rows are not rendered |

So they are invisible to a human reading the board and present in **every
contract payload a consumer reads**. That asymmetry is the actual cost, and it
is why "they're dropped, leave them" is not an answer.

## The part that makes this a real row and not a cleanup

**`perry-task` has no removal path.** `--help` offers `drop <ID>`, which *sets a
status* — it is what put these rows in the state they are in. There is no
`purge`, no `remove`, no `forget`. The three rows cannot be taken out of the
store by any tool Perry ships.

**So the deliverable is the mechanism, and the sweep is its first use.** Do not
hand-edit `perry/tasks.jsonl`. A store this project has spent Objective 2 making
canonical does not get fixed with an editor; if it does, the row proved the
opposite of its point.

## What the mechanism has to decide, and you must state your answer

1. **What it is called** and why it is not `drop`. These must not be confusable
   at the command line — one is a project decision, one is a store repair.
2. **What it refuses.** Removing a row some other row depends on, or one a
   linkage register names, or one an evidence record cites, breaks a reference.
   The minimum bar: **it refuses a row any live reference names**, and it says
   which reference. Check `depends_on`, `parent`, `phase/*-linkage.md`
   `krs[].tasks`, and evidence documents.
3. **What it does to `order`.** Rows carry an `order` field; two of these three
   have `order: null`. Say whether removal renumbers and why.
4. **Whether it is reversible.** It is a destructive write to the user's own
   state. At minimum it emits an event carrying the removed record verbatim, so
   the row is reconstructible from the log.

## The blank line — read this before you touch it

The row's title says "and a blank line". Measured: **the blank line is
`.perry/events.jsonl:67`**, not `perry/tasks.jsonl` (which has zero). The parsers
skip it, so it costs nothing today.

**`.perry/events.jsonl` is append-only and you must not rewrite it.** Do not
compact it, do not rewrite line 67, do not "clean" the file. Instead: **prove
whether a blank line anywhere in the log is tolerated by every reader**, and if
any reader would break, say which and open the finding. That is the whole of
this half.

## Files in scope

`bin/perry-task`, `bin/lib/`, `tests/`, `schema/task-list-contract.md` (only if
the payload's meaning changes), `perry/tasks.jsonl` (only through the new tool).

## Out of scope

- `.perry/events.jsonl` — append-only, see above.
- Deciding retention policy for closed rows generally (that is TASK-110's
  territory, and it is closed with a proposal).
- Any row other than `TASK-081`, `TASK-082`, `TASK-083`.

## Verification

1. The new subcommand's refusals, each proved on a constructed case in a
   fixture project — **not** on Perry's own store.
2. The three rows are gone from `perry-task list --all --json` and the payload
   is 173 rows.
3. `tests/test_contract_invariance.py` and `tests/contract_key_parity.py` still
   pass — removal must not change the payload's *shape*.
4. A test that the removal event carries enough to reconstruct the record.
5. State the before/after row count of `perry/tasks.jsonl` in your record.

**Do not run `perry-conform declare`.** Do not `git push`. Do not touch `main`.
