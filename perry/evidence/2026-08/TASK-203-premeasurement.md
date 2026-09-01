# TASK-203 — pre-flight measurement: the risks half reproduces, and the success line is a template

> Measured 2026-08-29 by the PMO, on a scratch copy, **before** any executor
> touched the row. `TASK-203-spec.md § Baseline` asks for exactly this:
> *"The risks half is stated by the row and has not been re-measured. Measure it
> first … If the risks half does not reproduce, say so and narrow the row."*
>
> It reproduces. The row is not narrowed — it is **widened**, and the reason is
> below.

## Method

The repository was copied to a scratch tree; every write below happened there.
Each register was exercised with an *ordinary* write — the command a user or an
agent actually runs — never with the one-way importer, which is the distinction
the spec's `Deliverable` turns on.

## Result

| Register | Store | Ordinary write | Store after | Board after |
|---|---|---|---|---|
| tasks | `tasks.jsonl` | `perry-task next TASK-050` | **changed** ✅ | updated |
| risks | `risks.jsonl` | `perry-task risk-add` → `RX-005` | **byte-identical** ❌ | updated |
| risks | `risks.jsonl` | `perry-task risk-clear RX-005` | **byte-identical** ❌ | updated |
| intake | `intake.jsonl` | `perry-task intake` | **still absent** ❌ | updated |
| asks | `asks.jsonl` | `perry-task ask` → `USER-904` | **still absent** ❌ | updated |

`risks.jsonl` md5 before `risk-add`: `d247ef83ae53cf9462f77afdc4e2ba5d`.
After `risk-add`: `d247ef83ae53cf9462f77afdc4e2ba5d`.
After `risk-clear`: `d247ef83ae53cf9462f77afdc4e2ba5d`.
`grep -c "MEASUREMENT PROBE" perry/risks.jsonl` → `0`.
`grep -c "MEASUREMENT PROBE" perry/BOARD.md` → `1`.

So `risks.jsonl` is current only because it was imported once. It is a snapshot
wearing a store's name, and it has been drifting silently since — `perry-lint`
reports `risks store: 4 record(s), 0 risk(s) drifted` because the board is
rendered from the same code path the store was minted from, not because the two
were compared after a write.

## The finding the row did not predict

**Every one of those five commands printed the same success line:**

```
perry-task: wrote RX-005 (risk-add) → store + journal + BOARD.md + event
perry-task: wrote the row (intake)  → store + journal + BOARD.md + event
perry-task: wrote USER-904 (ask)    → store + journal + BOARD.md + event
```

`→ store` is **unconditional template text**, not a report of what happened. In
three of the four registers it is false at the moment it is printed.

This matters more than the missing writes themselves. `perry-task`'s whole claim
on this project is that it is *"the one deterministic way Perry's state gets
written"* — and the header of `bin/perry-task` tells the reader that a failed
store write is *"reported, not raised."* It is not reported. It is announced as
a success. An agent reading that line has been told the store is current, and
on `risks` / `intake` / `asks` it never was.

## What this changes about TASK-203

- **The risks half stands.** Do not narrow the row.
- **The row is three registers, not two.** `asks.jsonl` behaves identically and
  is listed `Out of scope` in the spec on the reasoning that *"folding both into
  one row is how a two-store change gets one store's worth of testing."* That
  reasoning is still right and the scope line should stand — but the RESULT is
  now required to propose the follow-up row, because the spec's own escape
  clause (*"if the fix is genuinely shared, say so"*) has been triggered in
  advance by measurement rather than discovered during the fix.
- **A sixth verification step is owed**: the success line must become conditional
  on the store write actually landing. A row that fixes three store writes and
  leaves the unconditional `→ store` in place has fixed the registers and left
  the lie.

## Cleanup

The probe rows (`RX-005`, one intake row, `USER-904`, and the `TASK-050 next`
edit) exist **only in the scratch tree** and were never written to
`/Users/bytedance/proj/Perry`. Nothing to revert.
