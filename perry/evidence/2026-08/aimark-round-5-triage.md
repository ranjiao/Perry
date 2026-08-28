# aiMark round 5 — triage

> Source: `~/proj/aimark/doc/perry-contract-gaps-5.md`, measured against Perry
> at `fbcc308`. **Every number below I re-measured here** rather than accepting
> from the document; where its account differs from mine, both are stated.

## Acceptance: 8 of 8 done

Including the one this round was for — `perry-knowledge/list/1.0` is **adopted**,
wired end to end. Round 4 deferred that decision; it is now closed.

Their suite went **699 pass / 1 fail → 726 pass / 0 fail**, and the one failure
was their own new guard working.

## § 2.1 — two event kinds no writer emits. **Their diagnosis is wrong, and the truth is worse.**

```
1 migration              ← not in § The event kinds
1 migration-correction   ← not in § The event kinds
```

They attribute both to `bin/perry-migrate` and ask to *"widen the derivation to
every binary that appends to the log."*

**No binary writes either kind.** `bin/perry-migrate`'s four `migration` hits are
`schema.get("migration")` — reading a schema *section* of that name, not writing
an event. I checked all of `bin/`.

**Both were hand-appended, and one of them by me.** TASK-180's agent wrote the
`migration` event because the migration needed one and no tool could emit it;
I wrote `migration-correction` at `f691923` for the same reason.

So the proposed fix cannot work — **there is no binary to widen the derivation
to.** `TestTheDocumentedKindsAreTheWriters` guarantees *"§ The event kinds equals
what `bin/perry-task` can put in the log"*, and that sentence is still true. What
is false is the consumer-facing one they quote: *"a kind not in these two tables
is a kind this feed cannot emit."* **A hand edit made it false.**

The real defect is the absence the hand edit papered over: **Perry has no writer
for a migration event**, so the one time a migration needed to record itself, an
agent wrote JSON by hand into an append-only log. Documenting the two kinds
without building the writer would bless that.

## § 2.2 — `ts` order is not log order. **Confirmed, and it was my call.**

```
seq 891  2026-08-28T00:00:00+08:00  migration   ← twelve hours backwards
```

I hit this at merge time and resolved it by append order after checking that the
log is **not** ts-sorted — the base already carries an inversion at seq 66-67
from 2026-08-17. Their first `perry-time.ts` assertion was that log order and
instant order agree; **it failed on this row, and they concluded the assertion
was wrong rather than the log.** Same conclusion, reached independently.

Their ask is a page edit and it is right: the contract's stated reason for *"do
not re-sort"* is that second-precision ties are real, **which sounds like a
rounding problem.** A deliberately backdated stamp is a different and stronger
reason, and the page should say so.

## § 5.2 — `semantics` on 2 of 5 payloads. **Confirmed, and worse than they measured.**

They report 1 of 4. Measured here:

```
perry-task/list/1.18     9 entries
perry-events/list/1.2    2 entries
perry-goals/list/2.2     key absent
perry-decide/list/1.0    key absent
perry-knowledge/list/1.0 key absent
```

Their consequence is exact: `CONTRACT_TESTED.goals = "2.2"` **can never go red**,
because `changed` is empty on that payload by construction. It is an honest
comment, not a guard — and goals 2.2 is a textbook `semantics` entry (no key
added, one value's meaning changed, and the UTC/local note is genuinely useful).

Their argument for shipping an **empty** array first is the same one that put
`contract` on an empty knowledge store: *a consumer checks before it looks, and
a key that appears only when there is something to say is one a consumer cannot
check.*

## § 4 — the write contract. Two asks, both small, both well-argued.

**4.2 · `seq` on the write result and on `perry-task list`.** One integer,
closing the window where a poll cannot tell a stale read from a fresh one.

Checked: **`seq` is not a stored field** — the events feed computes it from
position at read time (`total: 908`, newest `seq: 907`). That is the right shape
for an append-only log and makes their *"the log already has the number"* true in
substance.

They rejected two alternatives with reasons I agree with: returning **the record**
would be a second projection of a task in a separately-versioned payload — *the
two-readers-of-one-file bug in a new place* — and returning **the payload again**
costs a full `list` per write and still says nothing about position.

**4.3 · optional `--if-seq <n>` compare-and-set**, refused with a sentence.
Optional is load-bearing: a write without it behaves exactly as today. Their
rejection of last-writer-wins is the sharp part — *the write has already landed
by the time the diff is reported, so the report is an explanation rather than a
choice*, and the case that matters is two agents closing the same row minutes
apart, **which is the normal state of this board.**

They explicitly do not want a conflict-resolution API: *"a dialog that offered
'overwrite anyway' would be aiMark deciding something it has no information
about."*

**Verbs 1–4 need nothing new.** 5 and 6 (`evidence`/`next`/`rung`, `ask`/`answer`)
need no contract either — only the result shape 4.2 asks for. `intake` writes are
**explicitly not wanted yet**, because TASK-196 is changing that register and a
shape frozen now would freeze against the wrong thing. That is the right call and
it is theirs.

## § 5.1 — their own finding, reported anyway

Their conformance suite was running against an **empty fixture**: 84 assertions →
1741, because every row-shaped assertion passed by having nothing to iterate.
They call it *"the finding this round is least comfortable reporting"*. It is
their defect and their fix; it is recorded here because **it is the same class
Perry has paid for repeatedly** — a guard whose green means nothing.

## Rows opened

| row | from |
|---|---|
| **TASK-204** | § 2.1 — a writer for migration events, so no future migration hand-writes JSON |
| **TASK-205** | § 5.2 — `semantics` on goals, decide and knowledge; goals to 2.3 |
| **TASK-206** | § 4.2 — `seq` on write results and on `perry-task list` |
| **TASK-207** | § 4.3 — optional `--if-seq` compare-and-set with a refusal sentence |
| intake | § 2.2 — the page's reason for "do not re-sort" is a rounding problem; the real reason is a backdated stamp |

**Not opened**: `perry-roles/list` (their debt, stated), `okr.objectives[].id`
(TASK-181..185 already carry it), `perry-docs/list` (§ 7 — deferred by the user
on 2026-08-28, and their § 7 makes the cost loud rather than reopening it).
