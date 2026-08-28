# Delegation prompt for an aiMark coding agent — round 5

> Rendered 2026-08-28 against `~/proj/Perry` at `8ce9fcf` on branch
> `feat/work-modes`. Every version, count and payload quoted below was taken
> from a command run on that tree, not from a document.
> Perry has **not** executed this work. Paste the block below into a fresh
> session **in the aiMark repository**.
>
> **Where aiMark reads Perry from.** `resolvePerryHome` probes
> `~/.claude/skills/perry`, which is a symlink to `/Users/bytedance/proj/Perry`.
> That checkout is **652 commits ahead of `origin/main`** and none of this has
> been pushed — so aiMark already sees everything below, and reading GitHub
> would show you a week-old Perry. Read the working tree.

---

You are working in the aiMark repository at `/Users/bytedance/proj/aimark`.
Perry lives at `/Users/bytedance/proj/Perry` and is **read-only to you** — read
its contract documents and run its read tools; change nothing in it.

## 0 · Round 4 is answered — all seven asks, with dispositions

Your `doc/perry-contract-gaps-4.md` (2026-08-21) made seven asks. Perry
re-measured every load-bearing number in it and **every one checked out**
(`perry/evidence/2026-08/aimark-contract-gaps-4-triage.md`). Here is what
happened to each.

| your § | ask | disposition |
|---|---|---|
| 3 | a read surface for knowledge cards — *your stated top priority* | **already existed when you asked.** Now documented. |
| 5.1 | `events` returns the log's HEAD, three places say tail | **fixed** — `perry-events/list/1.1` |
| 5.2 | the event-kind table is missing kinds | **fixed** — 26 kinds, derived from the writer by a test |
| 5.3 | an answered `USER-` ask is in no register | **fixed** — `perry-task/list/1.15` |
| 1 | a document listing for four unreachable collections | **DEFERRED by the user**, knowingly |
| 2 | `DESIGN-NNN` as a listed handle | **DEFERRED** with §1, same decision |
| 4 | an Objective record with a minted id | **accepted, designed, decided — not yet shipped** |

### 0.1 — § 3: the surface was built before you asked, and no page said so

`perry-knowledge list --json` returns `perry-knowledge/list/1.0` and has for
some time. Measured here today:

```
{ "contract": "perry-knowledge/list/1.0", "project_root": …, "state_root": …,
  "cards": [ { "path", "topic", "slug", "kind", "claim", "owner_role",
               "source", "last_verified", "invalidated_by", "stale" } ],
  "total": 1, "stale": 0 }
```

All nine fields you asked for, typed, plus the aggregate you called a bonus.
**Why you could not find it: there was no contract page.** `schema/` held six
files and this was not one of them, and `schema/README.md` said *three*
contracts. That is the finding, and it is the same defect class as
`conformance.missing_projection` — *it ships, it is real, and no page a
consumer reads announced it*. `schema/knowledge-list-contract.md` now exists.

**Two things to know before you render it.**

- `stale` is a boolean per card and a count on the payload, and **the payload
  does not carry the threshold that produced it**. That is a recorded, unfixed
  finding on Perry's intake queue. Render "N cards unverified" from `stale`;
  do not print a number of days you would have to read `state-schema.json` to
  know.
- This payload has **no `semantics` array**. Rule 3 still applies to the major.

### 0.2 — §§ 1 and 2: deferred by the user, and the cost is on the record

`TASK-172` is open and `not_started`, carrying this note verbatim:

> DEFERRED 2026-08-21 by the user: aiMark reads the directories directly for
> now. THE COST, stated so it is on the record: aiMark then owns a reader of
> Perry's LAYOUT, and `perry relocate` moves every claimed path — a consumer
> holding `perry/design/` breaks silently the first time a project moves its
> state root. aiMark's own document says it did not want this; the decision
> overrides that knowingly.

You do not need to argue this again. **What is worth doing is making the break
loud instead of silent**: if `perry-docs.ts` holds Perry's directory names,
resolve them against the `state_root` every contract payload already returns
rather than against a literal `perry/`, and render an explicit "this project's
layout moved" state when a claimed directory is absent. That converts the
deferred cost from a silent wrong answer into a visible one, and it needs
nothing from Perry.

### 0.3 — § 4: decided, five rows open, still `""` today

You were right that an Objective is not a record. Perry agreed, wrote
`DESIGN-009`, locked it, and the user chose **option A** on all four open
decisions. Five rows now exist — `TASK-181` … `TASK-185`, step 1 through step
5: objective rows in `okr.jsonl`, byte-for-byte re-render of `OKR.md` from
them, the `O-1` mint and write-back, the payload filling
`okr.objectives[].id`, and a proof that the id survives a rename and a reorder.

**All five are `not_started`.** Measured today:

```
objectives: [('', 'The four work modes are usable, not just…'),
             ('', 'Every piece of state is queryable and wr…'),
             ('', 'Perry is landed on three named real proj…'),
             ('', 'aiMark manages projects through Perry'),
             ('', 'Tasks are executed by roles that know th…')]
```

So: **keep your composite key.** Do not build against an id that does not exist
yet, and do not mint one yourself — that answer has not changed.

Also, the small one you flagged: `DESIGN-007 § 5.3` named the store
`perry/goals.jsonl` and the file is `perry/okr.jsonl`. You were right; the
design document was the stale half.

---

## 1 · The task: move four anchors, and act on what moved

`src/perry-cli.ts § CONTRACT_TESTED` reads:

```ts
task: "1.14",  goals: "2.1",  decide: "1.0",  events: "1.0",
```

Live today:

| contract | you | live | kind of gap |
|---|---|---|---|
| `perry-task/list` | 1.14 | **1.18** | one additive, two MEANING |
| `perry-goals/list` | 2.1 | **2.2** | one MEANING |
| `perry-events/list` | 1.0 | **1.2** | one behaviour fix, one MEANING |
| `perry-decide/list` | 1.0 | **1.0** | unchanged |
| `perry-knowledge/list` | — | **1.0** | new to you |
| `perry-roles/list` | — | 1.0 | your own known debt |

Your constant's own comment sets the bar — *"it is only honest if it is bumped
when the changes are actually read and acted on."* Four of the six entries
below need a code change; the rest need a read and a decision.

### 1.15 — an answered ask is in a register again (your § 5.3)

Your ask was *"either keep answered asks in `asks.items` carrying their
answered status, or let the edge declare its own kind."* Perry took the first.
Delete the set-arithmetic inference you described — an id in `depends_on`, in
no register, absent from `depends_on_unknown` — and read the register.

### 1.16 — the drift block reads `null`, not `0` — **MEANING**

`drift.drift`, `drift.unrecorded`, `drift.unrecorded_sample`, `drift.orphaned`
and `drift.stale_done` are **`null`** when `drift.checked` is `false`, where
they used to be `0` / `[]`. A count nobody computed is an unknown value, and
Rule 1 has always named `null` as this payload's unknown.

**If you render a drift badge from the count, gate it on `checked`.** A `0`
badge on an unchecked tree is the exact failure this bump exists to end.

### 1.17 — `tasks[].evidence_relations[]` — **ADDITIVE**

The `Evidence` cell was one string doing four jobs: which documents, how many
tests, what kind of verification, and sometimes a section reference that is not
a file. Measured on Perry's own board: **139 rows carry an evidence cell, 28
name more than one thing**, and 45 spans reached neither `evidence_paths` nor
`conformance.evidence_not_found`.

`evidence_paths` and `conformance.evidence_not_found` are **byte-identical** —
that is why there is no `semantics` entry. If you were rendering the raw
`evidence` string because the paths array was not enough, **this array replaces
your parser**: one entry per thing the cell names, in cell order, each keeping
its span verbatim beside whatever Perry could resolve.

### 1.18 / events 1.2 — `ts` carries its offset — **MEANING**

Every event appended from now on stamps `2026-08-28T02:15:22+08:00`. **Every
line written before the cutover carries no zone at all** and is read as the
reading machine's local time. The log is append-only; nothing was rewritten.
This touches `tasks[].created`, `tasks[].updated`, `tasks[].timeline[].ts` and
`events[].ts`.

**What breaks:** a hardcoded `%Y-%m-%dT%H:%M:%S`, a fixed-width slice, or any
comparison of two stamps as strings. A real ISO-8601 parse needs no change —
but note that a single Activity feed now contains **both** shapes, so anything
that groups by a string prefix, or sorts by text, is now mixed-format. Perry's
feed is returned in log order and you already refuse to re-sort it; keep that.

### goals 2.2 — the staleness stamps are UTC with a `Z` — **MEANING**

`krs[].current_provenance.asserted_at`, `krs[].current_staleness.since` and
`moved_tasks[].at` are UTC now; `at` in particular is no longer the local text
the event log holds. The bug it fixed is worth knowing because you render the
result: a register stamp and a log stamp were compared **as text**, so on this
UTC+8 machine a task that moved *before* a number was asserted was reported as
having moved after it.

### events 1.1 — the first page is the TAIL (your § 5.1)

Fixed. Verified today:

```
$ perry-task events --json --limit 4
seq [877, 878, 879, 880]   ts 2026-08-28T11:13:50+08:00 … 11:17:58+08:00
```

**Delete the workaround.** You request a window larger than any real log — 437
KB, 75 ms, cached — and slice the end yourself. That can go.

### events — `purge` is a kind you must handle (not a version)

`perry-task purge` shipped: it is the store's only removal path. `purge` is the
only kind that says a row **stopped existing** rather than stopped moving.
**A front-end holding a cached row must drop it.** The removed record rides on
the log line under `record` and is deliberately not projected onto the payload.

The kind list is no longer hand-kept — a test derives the emittable set from the
writer and fails in either direction. It documents **26** kinds; 14 are live on
this board. Your decision to derive filter chips from the payload rather than a
fixed menu remains the right one.

---

## 2 · Two hazards Perry is telling you about deliberately

**2.1 — an ADR id can be handed out twice.** `bin/perry-decide § mint_id`
takes `max(files ∪ index) + 1`, but `render_index` rebuilds `DECISIONS.md`
*from the files* — so deleting the highest ADR file removes it from the index on
the next render and the id becomes mintable again. Recorded on Perry's intake
queue 2026-08-28 and **not fixed**. If aiMark caches or links by ADR id, an id
is not proof it is the same decision; carry the title or the file path too.

**2.2 — the board is a live tree.** While this document was being written,
another agent created `TASK-200` and started it. `git status` on Perry's
checkout is not clean between reads, and two reads of `perry-task list` minutes
apart legitimately disagree. That is the system working; do not treat a moving
count as a contract violation.

---

## 3 · What is about to move under you

**`TASK-180` is `in_progress` right now** and it changes **values you key on**:

```
P-O<a>.<b>  in phase <NNN>   →   P<NNN>-O<a>-KR<b>       e.g. P-O3.1 → P002-O3-KR1
```

One-time, all historical data, **no compatibility with the old form** — the
user's decision, in those words. **Scope is `P-O*` phase KRs only.** The
overall OKR's `KR-O1.1` family (34 rows) is explicitly **out**, and touching it
would be a second migration nobody decided.

So: if you persist, cache or deep-link a **phase** KR id, every one of them
changes once, with no dual-read window. Overall KR ids do not move.

The DESIGN-009 rows in § 0.3 will later add `okr.objectives[].id` and move the
goals minor again. Nothing else in flight touches your four contracts.

---

## 4 · The ask back — and it is the important half of this round

Perry's Objective 4 is *"aiMark manages projects through Perry"*, and this is
its state today:

| KR | target | actual |
|---|---|---|
| KR-O4.1 lines in aiMark parsing Perry's markdown | 0 | your call — you own the count |
| **KR-O4.2 a versioned, test-locked WRITE contract exists** | 1 | **0 — none exists** |
| KR-O4.3 a full task lifecycle driven from the aiMark UI | 1 | 0 |
| KR-O4.4 goals and decisions writable on the same shape | 2 of 2 | 0 |

**There is no write path at all**, and Perry has declined twice to invent one —
`TASK-059` refused to freeze an agents roster into a contract ahead of the
design that defines it, and `goals/2.2` refused to add a commitments array on
the same ground: *the tool's needs, not a guess at them, should set the shape.*

You are that consumer. **So the round-5 ask is: tell Perry what the write
contract has to be**, in the same measured form your gap reports take:

1. **The verbs you actually need first**, ranked, with the screen each one is
   behind — create a task, advance a status, close with evidence, add an
   intake row, answer an ask. Not a wish list; the order you would ship them.
2. **What a write must return** for your UI to stay honest — the new record?
   the payload again? an event seq you can reconcile your cache against?
3. **What happens on a conflict**, from your side: the board moved between your
   read and your write (see § 2.2 — it demonstrably does). Do you want a
   compare-and-set on a seq, a last-writer-wins with a reported diff, or a
   refusal you render?
4. **What you refuse to do.** Your gap reports have been most useful where they
   said *"do not add a `body` field"*. The same here.

Perry will not design this from the inside. If round 5 returns nothing else, it
should return this.

---

## 5 · Acceptance

1. `CONTRACT_TESTED` reads `{task: "1.18", goals: "2.2", decide: "1.0", events:
   "1.2"}` — and each bump is accompanied by the code change it names above, or
   by a one-line comment saying why none was needed.
2. The drift badge is gated on `drift.checked`.
3. The 437 KB whole-log read is deleted and the Activity view reads the first
   page.
4. A `purge` event drops the cached row.
5. No `ts` is compared, sliced or formatted as a string anywhere.
6. The answered-ask inference is replaced by a register read.
7. `perry-knowledge/list/1.0` is either adopted (a stale-cards strip beside the
   conformance findings) or explicitly deferred with a reason — your call, but
   say which.
8. The suite is green and you report the numbers, both before and after.

## 6 · Report back

Same format as rounds 2 through 4 — `doc/perry-contract-gaps-5.md`, measured
against `~/proj/Perry`, every claim carrying the command that produced it.
Round 4's seven asks were all actionable and all acted on; that is the bar.

Include § 4 in it. That section is the reason this round exists.

## 7 · Out of scope

- Do not modify anything in `/Users/bytedance/proj/Perry`.
- Do not adopt `perry-roles/list/1.0` in this round unless it is free — you
  named it as your debt and it is not what this round is for.
- Do not build against `okr.objectives[].id`; it is `""` on every objective
  today (§ 0.3).
- Do not widen `perry-docs.ts` into a richer reader of Perry's layout. Making
  its existing assumptions fail loudly (§ 0.2) is in scope; reading more of
  Perry's directory structure is not.
