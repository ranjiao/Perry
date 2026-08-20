# TASK-098 — the half of `--reviews` that was missing

## What was wrong

`--reviews` reported **a verdict that arrived and was ignored**
(`fail-verdict-left-at-review`). Nothing reported the opposite: **a row at
`review` for which no round was ever sent.**

Found by the user asking whether TASK-093 was finished. It was not — it sat at
`review` because I had moved it there and never dispatched the round, and
`--reviews` called the board clean. Two symmetric failure modes, one covered.

## The check

```
python3 bin/perry-lint --reviews
```

Reports a row that is at `review`, declares **V4**, and has no verdict block
naming it — with **how long it has sat there**.

**The age is reported and not judged.** A row sent an hour ago and one
forgotten a week ago are the same *state*; only the reader knows which. A
threshold here would be the checker guessing, and the message says so: *"Either
a round is in flight, or one was never sent — only you can tell those apart."*

Three narrowings, each with a reason rather than a place on a list:

- **V4 only.** That is the rung meaning *a fresh reviewer ran*. V2 and V3 make
  no such claim, and asking them for a verdict turns the finding into noise on
  every board that uses `review` as an ordinary status.
- **No verdict block only.** A round that has returned is the other check's
  business; reporting both would name every row twice.
- **Unknown, not zero,** when no event records the move. Silence about *when*
  is not the same as *today*, and a row whose move predates the event log must
  not read as fresh.

## Verified

Run on this board it named exactly the three rows whose rounds were in flight —
TASK-089, TASK-091, TASK-096 — and excluded TASK-093, which carries a round-1
verdict. Four mutations red: suppressing the guard (6 tests), dropping the V4
narrowing, and turning the unknown age into zero.

## What was NOT checked

- No project other than Perry's own. On a board where `review` means something
  different, this could be noise — the V4-only narrowing is the mitigation and
  it is untested against a real foreign board.
- It cannot tell in-flight from forgotten, by design. If that distinction ever
  needs to be mechanical, the dispatch itself would have to leave a record, and
  nothing does today.

=== VERDICT ===
task: TASK-098
rung: V3
result: PASS
criteria: this file § The check
checked: the three narrowings, each mutated red; the live board naming exactly
         the rows whose rounds are in flight and excluding the one with a
         verdict; the age reported rather than judged
not-checked: any project but this one; whether in-flight can ever be told from
             forgotten without a dispatch record
proof: (none — this is a PASS)
=== END VERDICT ===
