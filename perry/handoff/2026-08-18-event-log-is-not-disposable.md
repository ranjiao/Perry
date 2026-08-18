# Hand-off to `decide` — `DESIGN-004 § 5.3`'s disposability claim is false

**From:** `work`, 2026-08-18, at `fed289c`.
**To:** the `decide` lane. `DESIGN-004` is that lane's file. **It was not opened
for writing.** This is the "raise it and stop" half of
`SKILL.md § The hand-off contract`.

## The claim

`perry/design/DESIGN-004-deterministic-writes.md § 5.3`:

> **It is derived state and must stay disposable.** Delete it and Perry still
> works; `BOARD.md` and `journal/` remain canonical. What is lost is history
> resolution and drift detection, not truth.

It is load-bearing. The same paragraph says it is *"the constraint that keeps
the design from becoming a database with a markdown export"*, and
`bin/perry-task` cites it in code to justify never letting a frozen contract
depend on the log for a value the markdown determines.

## The measurement

Perry's own state, copied, log deleted, same call:

| | `open` | `closed` | `tasks[]` |
|---|---|---|---|
| with `.perry/events.jsonl` | 39 | **35** | **74** |
| without it | 39 | **0** | **39** |

`perry-lint` stays clean and `perry-state` still reports the board, so the
"Perry still works" half holds. **The "not truth" half does not.**

## Why this is truth and not history resolution

`DESIGN-004 § 1.3` states the reader problem it was written to solve, in the
consumer's own words:

> **"What is the full set of tasks?"** `BOARD.md` holds open work only; closed
> rows leave it.

A closed row leaves the board **by design**. Its only machine-readable record
afterwards is the event log — `journal/` holds the same fact as dated prose,
which is exactly the reconstruction these contracts exist to replace. So
deleting the log does not degrade history resolution: it deletes 35 of 74 tasks
from every contract payload, and with them the answer to the question the design
was written to answer.

The two sections contradict each other, and § 5.3 is the one that is wrong.

## What this is not

**Not an argument that the log should be un-tracked.** The opposite. The
practice — `.perry/events.jsonl` committed to git, 74,097 bytes and the
second-highest-churn file in the repo — has been correct all along, and it is
the *document* that is out of step. Nobody was following a bad rule; the rule
was written down in a form nothing enforced, and reality quietly did the right
thing.

## What it changes for TASK-038

`TASK-038` — *"the log becomes canonical, `BOARD.md` becomes a projection"* —
reads today as a change of policy. On this measurement it is closer to
**recognising a state that already exists**: the log is already the sole record
of 35 tasks, and calling it derived is what leaves that undefended. That
strengthens the sequencing verdict already recorded on its row (P1, gate met)
rather than changing it.

## What it changes for TASK-070

`TASK-070` asks whether Perry's own state should be pruned, and names this
tension: *"DESIGN-004 § 5.3 calls the event log derived and disposable — if it
is disposable, say why it is tracked."*

**Answered, and in the direction that shrinks the task.** The log is not a
retention candidate at all; it is canonical-in-practice and must be kept whole.
TASK-070's scope is therefore `journal/` and `evidence/` only. Measured at
`fed289c`:

| area | bytes | files |
|---|---|---|
| `perry/evidence` | 174,151 | 36 |
| `perry/design` (**stays** — architecture record) | 148,182 | 6 |
| `perry/journal` | 127,599 | 3 |
| `.perry` (74,097 of it the event log) | 79,711 | 4 |
| **`perry/` + `.perry/`** | **642,170** | of 3,111,696 tracked — **20.6%** |

Note `evidence/` is now the largest of the three, above `journal/`, which the
audit that opened TASK-070 did not have — it named the journal.

## The question, which is `decide`'s and not `work`'s

**Does `§ 5.3` get corrected, and to what?** Three shapes, not ranked:

1. The log is **canonical for closed rows and derived for open ones** — which is
   what the code actually does today, and the narrowest true statement.
2. The log is canonical, full stop — which is TASK-038's position, and makes
   § 5.3 a thing TASK-038 deletes rather than corrects.
3. § 5.3 stands and the **contracts** change: `list --all` reconstructs closed
   rows from `journal/` when no log is present, restoring disposability by
   giving the claim an implementation. This is the only branch that keeps the
   design's stated constraint, and it is expensive.

`§ 9` is append-only, and a correction to a locked doc's architecture section is
the kind of thing it exists to hold.

## What this hand-off touched

`perry/handoff/` and `perry/BOARD.md` only. `DESIGN-004` is unmodified — verify
with `git log -1 --stat -- perry/design/DESIGN-004-deterministic-writes.md`.
