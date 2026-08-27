# TASK-144 spec — the log stamps local time, the register stamps UTC, and one comparison spans both

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: medium
> Measured 2026-08-28.

## The measurement

```
event log ts   '2026-08-28T02:15:22'    ← no zone
register       '2026-08-21T10:04:08Z'   ← UTC, with Z
UTC now        2026-08-27T18:18:26Z
local now      2026-08-28T02:18:26 CST
```

The row says the log "has no zone and the register has one". **It is worse than
that: the log stamps *local* time.** On this machine that is **UTC+8**, so a log
timestamp reads eight hours later than the same instant in the register.

And the two are compared, as strings, in one expression:

```python
# bin/lib/__init__.py:606
since = provenance["asserted_at"]          # from the register — UTC
...
# bin/lib/__init__.py:631
at = _ts_key(event.get("ts", ""))          # from the log — local
if not at or at <= since:
    continue
```

That is `current_staleness` — *"has a linked task moved since this number was
asserted?"* — and its answer is wrong inside an eight-hour window on this
machine, and by whatever the offset is on any other.

## What makes this delicate

- **`.perry/events.jsonl` is append-only and 778 entries deep.** Existing
  timestamps cannot be rewritten to add a zone without rewriting history. Decide
  what happens to them and say so: interpreted as local, interpreted as UTC, or
  explicitly unknown.
- **A timestamp is a sort key.** `perry-task events` orders by log order and the
  contract says *"timeline order is array order and is authoritative"*, so
  changing the stamp format must not change any ordering. Prove it.
- **`_ts_key` exists precisely because these strings are compared.** It is the
  one place that already knows both shapes reach it. Start there.
- **Three writers stamp times**: `bin/perry-task` (the log), `bin/perry-goals`
  (the register's `updated`), and whatever writes `asserted_at`. Find them all
  before changing one.

## The choice, and you must argue it

**A — the log gains a zone.** New events stamp UTC (or an offset). Old ones are
interpreted by a stated rule.
**B — the register drops its `Z`** and both are local.
**C — neither format changes; the comparison converts.**

**C is the smallest and may be the worst**: it leaves two shapes in the tree and
the next comparison written by someone who has not read this row is wrong again.
**A is a write-format change on an append-only log.** Say which and why.

Whichever you take, **`_ts_key` must end up the only place that knows.** A second
converter is this project's most-paid-for defect.

## Verification

1. A staleness computation that spans the offset gives the right answer.
   Construct it: assert a register number, append an event two hours later in
   *local* terms, and show `stale` is what it should be — before your change it
   is wrong, after it is right.
2. **No ordering changes anywhere.** `perry-task events` over the full log,
   before and after, is identical — the same 778 in the same order.
3. Old, zoneless entries behave by the rule you stated, and that rule is written
   down in the contract or the schema, not only in a docstring.
4. `_ts_key` is the only converter. Prove it with a search.
5. Mutation: reverting reddens a test that names the skew, not merely
   "something differs".
6. `perry-lint --root .` — 0 errors, **0 rows drifted**.

## Out of scope

- **Do not rewrite `.perry/events.jsonl`.** If your design needs old entries
  changed, stop and report — that is a migration and a decision.
- `perry/` otherwise untouched. `git diff -- perry/` must end empty.
- Do not touch `schema/state-schema.json` unless a declared shape genuinely
  moves; if it does, **stop and report** rather than editing it.

## Ground rules

- Branch `coding/task-144-one-clock`, commit there, **no PR, no push**.
- **Commit as soon as you have something coherent, and keep committing.**
- `PYTHONNOUSERSITE=1 /usr/bin/python3` explicitly — Perry is stdlib-only and
  that flag is what proves it.
- `tests/parallel -j 4`. Verify yours is the only one with a pattern that
  **cannot match your own argv**:
  `ps -Ao pid,command | grep "python3 tests/paralle[l]"`. Write scratch files to
  a path containing your own branch name.
- **Never `git checkout` while a suite is in flight** — it reverts the tree
  mid-run and the reading is worthless. An agent did that tonight, caught it,
  and reran.
- Expected baseline: **83 modules · 2457 tests · 2 red** —
  `test_contract_invariance` (a union-typed key) and `test_diagnose` (two
  failures, one order/parallel sensitive). **Neither is yours.**
- Another agent is in `bin/perry-state` and `viewer/parsers.py`. You need
  `bin/lib/`, `bin/perry-task` and `bin/perry-goals`.
