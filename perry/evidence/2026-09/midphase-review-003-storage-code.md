# Mid-phase review — phase #003 storage-code

> **Date**: 2026-09-08 · **Phase day**: 12 (started 2026-08-28)
> **Written by**: `work` lane. Reads `phase/003-storage-code.md`,
> `perry/linkage.jsonl`, `perry/tasks.jsonl`, `.perry/events.jsonl` and the
> journal from 2026-08-28 onward. **Writes nothing outside `evidence/`** —
> every phase-file change proposed here is handed to the `goals` lane.
> **Inline health check**: `evidence/2026-09/health-check-2026-09-08.md`.

## Verdict

| Objective | Verdict | Why |
|---|---|---|
| **O1** — Every declared store exists, and one command checks all of them | **on_track** (met) | 3 of 3 KRs at target; 4 of 4 linked rows `done` |
| **O2** — The code reads a store, not a rendered file | **at_risk** | KR1 met and measured; KR3 has **never been asserted** and its only open row has not started |
| **O3** — The phase's KRs cover the work that actually runs | **off_track** | 20% against a 100% target, and the gap is 12 rows nobody was asked about |

## KR register at day 12

Values from `perry/linkage.jsonl`, provenance from `perry-state --json`.

| KR | Target | Current | Provenance | Linked rows | Verdict |
|---|---|---|---|---|---|
| P003-O1-KR1 — declared stores that exist on disk | 6 | 6 | asserted 2026-09-03 | 1/1 done | met |
| P003-O1-KR2 — stores one lint run gives a drift verdict for | 6 | 6 | asserted 2026-09-03, **stale** | 2/2 done | met, number untrusted |
| P003-O1-KR3 — stores reporting `unchecked` when removed | 6 | 6 | TASK-229 evidence | 1/1 done | met |
| P003-O2-KR1 — `bin/` sites reading the track register from markdown | 0 | 0 | asserted 2026-09-03, **stale** | 4/4 done | met, number untrusted |
| P003-O2-KR3 — the render distinguishes projected from canonical | — | — | **never asserted** | 1/2 done | unmeasured |
| P003-O3-KR2 — rows answering the KR question in their own `add` | 100% | **20%** | measured, recomputed every read | 4/8 done | missed |

## Definition of Done at day 12

| # | Item | State |
|---|---|---|
| 1 | Six stores get a drift verdict; each reports `unchecked` when removed | met (O1-KR2 + O1-KR3) |
| 2 | `intake.jsonl` / `asks.jsonl` exist, imported by their own commands | met (O1-KR1) |
| 3 | The four named `parse_tracks` sites read `.perry/config.jsonl` | met (O2-KR1) |
| 4 | The adoption-reader guard exists and goes red — **or** the phase records that its reader has no caller | met **by the second branch**, recorded 2026-09-02 (`USER-911`) |
| 5 | Every `main`-track row opened under the gate carries a KR edge or an `unlinked` declaration from its own `add` | **missed — 3 of 15** |
| 6 (nice) | The render distinguishes projection from canonical | not started (`TASK-262`) |
| 7 (nice) | `TASK-050`'s mutation harness replaces the regex round | met |

**Four of five Must-Haves are met on day 12 of a phase whose predecessor took
until scoring to reach 0.89.** The phase is not in trouble on delivery. It is
in trouble on two things delivery does not fix, below.

## Finding 1 — DoD item 5 is missed by 12 rows, and the writer that fixes it landed yesterday

`P003-O3-KR2`'s measurement (`bin/lib § same_action_linkage`, recomputed on
every read) at day 12:

```
numerator   3   TASK-382, TASK-383, TASK-394
denominator 15  TASK-381 .. TASK-395
never answered  TASK-381, TASK-384, TASK-385, TASK-386, TASK-387, TASK-388,
                TASK-389, TASK-390, TASK-391, TASK-392, TASK-393, TASK-395
declared unlinked at add:  (none)
```

`declared_unlinked_at_add` is **empty**, and that is the whole finding.
`TASK-394` ("`add` has no way to declare a row serves no KR") built exactly
that writer, merged 2026-09-07, verified at V3, and now sits at `review`
awaiting its V4. So the second of the KR's two legal answers has had a writer
for **one day**, against a 15-row denominator accumulated over twelve. The
20% is not evidence the gate does not work; it is evidence the gate was half
built for most of the window it is measured over.

**And the register disagrees with itself about this KR.**
`perry-lint --root .` reports exactly one drifted linkage row, and it is this
one:

```
⚠ perry/linkage.jsonl [linkage-store-drift] P003-O3-KR2 differs between the
  store and phase/003-linkage.md. The store is what the readers answer from
  (DESIGN-015 § 5.6), so the document is the stale side unless `perry-goals`
  wrote it last.
```

The store's value is computed on every read and cannot be stale; the rendered
`phase/003-linkage.md` is the side that has fallen behind. Nothing on the
board is wrong because of it — every reader answers from the store — but the
one KR this phase will argue about at scoring is also the one whose document
and store do not match. Clearing it is a `perry-goals` render, and it belongs
to the `goals` lane.

**What this changes about scoring.** Scoring `P003-O3-KR2` as 0.20 would
score the wrong thing. The honest reading is that the numerator is bounded by
when each half of the gate existed, and the phase should either
(a) re-baseline the denominator to rows opened after `TASK-394` merged, or
(b) score it as-is and say in the retro why. That is a `goals`-lane decision
and this file does not take it.

## Finding 2 — two KR numbers are stale, and one is knowingly wrong

`perry-state --json` raises this as a `warnings` entry, not as a nicety:

> 2 KR `current` value(s) were asserted before a linked task moved and can no
> longer be trusted: P003-O1-KR2, P003-O2-KR1

- **`P003-O1-KR2`** was asserted 2026-09-03; `TASK-067` moved `review → done`
  at 2026-09-04T03:06:30Z. The KR's own metric already carries the honest
  answer and refuses to act on it: `linkage.jsonl` became a **seventh**
  declared store during this phase (TASK-276/277/278) and prints a real drift
  verdict, so one lint run now prints **7 verdicts against a target of 6**.
  The metric text says this out loud — *"FLAGGED FOR SCORING: on the honest
  reading this KR is 7 of 7"* — and leaves `current` at 6 deliberately,
  because raising both numbers is a KR change the user owns.
- **`P003-O2-KR1`** was asserted 2026-09-03; `TASK-283` moved after it. The
  measurement itself (2026-09-07) is sound and unusually well-documented —
  `grep -rn 'parse_tracks(' bin/ viewer/` minus its own `def` returns exactly
  one line, `bin/perry-state:1172`, reached only when no store exists — but
  the register's timestamp no longer certifies it.

**Neither was re-asserted, by decision.** Both were re-measured on 2026-09-08
and both hold — 7 verdicts in one lint run, 1 `parse_tracks` invocation of
which 0 read the markdown as truth. The measurement is at
`evidence/2026-09/2026-09-08-kr-remeasurement.md` and is what `score-phase`
cites. Writing either number into the register means bumping
`phase/003-linkage.md`'s `updated:`, which is also where 115 linkage records
take `declared_at` (`bin/perry-tasks:1612`) and where every KR takes
`asserted_at` (`bin/lib/__init__.py:1066`) — so recording one fresh number
re-dates 115 records and marks all four asserted `current` values fresh,
including the two being corrected. That is `TASK-155`, and its real fix is a
new field in `schema/state-schema.json`, which sits on `.perry/hook.md §
High-stakes operations` under the claim surface.

**User decision, 2026-09-08**: carry the honest measured numbers to
`score-phase` citing the evidence file, leave the register's `stale` warning
standing because it is true, and defer `TASK-155` to phase 004. The
`P003-O3-KR2` linkage drift is deferred with it — clearing it is a render, and
any render pays the same cost.

## Finding 3 — the phase closed 113 rows and opened 204

From `.perry/events.jsonl`, 2026-08-28 to today:

| | Count |
|---|---|
| `add` | 204 |
| `done` | 81 |
| `drop` | 32 |
| **net change in open rows** | **+91** |

Open rows now stand at 143 and `BOARD.md` at 224 lines against a 200-line cap.
Two days carry most of it: 2026-09-02 (43 added, 7 closed) and 2026-09-04
(37 added, 12 closed). 918 commits landed in the same window, so this is not
a stalled phase — it is a phase whose *discovery rate* outruns its closure
rate roughly 2.5 to 1.

This is the mechanism behind DoD item 5, not a separate problem: 204 `add`
events is the population the linkage gate has to survive, and it is where the
12 never-answered rows came from.

## Finding 4 — the intake queue's SLA breaches went from 2 to 10

`phase/003-storage-code.md § Process Note` records the count deliberately so
the phase is not planned as though the queue were empty: **3 at phase start,
2 on 2026-09-01**. Today the `intake` track (SLA `5d`, from
`.perry/config.jsonl`) reports **10 breaches**:

| Id | Over by | Title |
|---|---|---|
| TASK-155 | 13d | the register `updated` field carries two facts, so appending an edge re-dates every asserted number |
| TASK-267 | 5d | the tasks store is the only one of six whose census line does not name it |
| TASK-268 | 5d | `viewer/parsers.py:3899-3900` builds `top_risks` from `BOARD.md` while `risks.jsonl` exists |
| TASK-269 | 5d | `test_risks_store` fails under `unittest discover`, passes under `bash tests/run` |
| TASK-270 | 5d | `perry-config write --from-file` writes a zero-record store |
| TASK-271 | 5d | `tracks_source` is on two published payloads |
| TASK-272 | 5d | `test_host_support` concurrency test |
| TASK-275 | 1d | `intake-sweep` leaves the canonical intake store empty |
| TASK-289 | 1d | `perry-task --actor` is optional and defaults |
| TASK-291 | 1d | `close-task` warns after the fact on a V4 |

`TASK-155` is the oldest and is **`blocked`** — it is also, by its own title,
the row that explains Finding 2: *"the register `updated` field carries two
facts, so appending an edge silently re-dates every asserted number in the
file."* The staleness warning this review opens with is the defect TASK-155
describes, sitting unfixed for 18 days.

## Finding 5 — triage ran, and four rows' status disagreed with the facts

The mechanical half of `/perry work triage` ran on 2026-09-08 as part of this
review. `BOARD.md § Intake` was empty (`undischarged: 0`), so step 0 had
nothing to drain; the findings came from `perry-task list --all --json §
conformance`, which classifies what the payload could not.

| Row | Flag | What was true | Action taken |
|---|---|---|---|
| `TASK-394` | `in_progress_with_no_live_run` (11.9h idle) | Merged 2026-09-07, verified V3, `Stage` already `review`. The **status** had not caught up. | → `review`; next action names the pending V4 |
| `TASK-383` | `blocked_without_dependency` | Blocked on *"TASK-278's V4 round is reviewing the drift logic right now"*. That round finished — `TASK-278` is `done` at V4 PASS. No `depends_on` edge existed, so nothing could resolve it automatically. | → `not_started`, blocker recorded as cleared |
| `TASK-280` | `blocked_by_closed_rows` | `depends_on: [TASK-278]`, and TASK-278 is done. But the row **is** still blocked — on the claim surface, not on that edge. | edge cleared; the real blocker named on the row |
| `TASK-285` | `in_progress_with_no_live_run` (24h idle) | Round 6 was dispatched 2026-09-04 and its agent was killed by a session rate limit with only a stub committed. | **No action** — `triage` requires asking before re-dispatching a row a previous agent may still hold |

Board effect: `blocked` 5 → 4, `in_progress` 2 → 1, `review` 6 → 7.

### The structural blocker

`triage` asks whether the same dependency is cited in two or more rows. It is
cited in **three**, and it is not a task:

> `schema/state-schema.json` — on `.perry/hook.md § High-stakes operations`
> under **the claim surface**, so no agent can touch it without the user
> authorizing the dispatch.

- `TASK-155` — the fix is a per-KR assertion date, a new field in that file.
- `TASK-280` — `krs[].title` is `required: true` there; flipping only that
  flag in a sandbox copy took the round's errors from 6 to 0, so the schema is
  *precisely and solely* the blocker.
- The two KR numbers this review could not re-assert (Finding 2) are blocked
  by the same field TASK-155 names.

**This is one authorization, not three rows.** It is the highest-leverage
single decision available on this board, and it is the user's alone.

### Staleness, on `triage`'s own thresholds

Twelve rows have never moved since the day they were opened. `triage` measures
staleness **per priority** — P0 >= 3d, P1 >= 7d, P2 >= 14d — so **six are
stale** and six are P2s not yet at 14 days. Both P0 rows had events yesterday.

Stale: `TASK-231`, `TASK-220`, `TASK-218`, `TASK-217` (11d each),
`TASK-237`, `TASK-236` (10d each).

**Four of the six are the phase-closing machinery** — the retro-ordering
question (TASK-217), threading the closing phase id (TASK-218), the
`close-phase` router subcommand (TASK-220), and the route a measured KR number
takes into the register (TASK-231). All four were opened on phase day 1 and
none has moved since. The phase has spent twelve days on its KR work and has
not touched the tooling it needs to close.

**All four are DEFERRED TO PHASE 004 by user decision, 2026-09-08.** The
consequence is that **phase 003 closes by hand**, and it is worth stating
plainly so nobody rediscovers it at close time:

- no `close-phase` router — the four existing commands are run separately
  (TASK-220);
- in an order no document agrees on, decided once by hand for this phase
  (TASK-217);
- with the closing phase id passed manually at each stage and nothing checking
  all four got the same one (TASK-218);
- and with measured KR numbers going to `evidence/` rather than the register,
  which is the workaround this review already took (TASK-231).

None of this blocks closing. It makes closing a careful manual operation
instead of one command, and that is the trade the deferral buys.

`TASK-231` is worth naming twice: *"a measured KR number has no way into the
register that does not re-date everything else"* is Finding 2 stated as a row,
filed on day 1, and it is the reason this review's re-measurement had to be
written to `evidence/` instead of to the register.

### The cap

`BOARD.md` is 225 lines against 200. Intake is empty, so this is not intake
pressure — it is 143 open rows. The only way down is closing or dropping, and
`modes/queue.md`'s rule holds: do not raise the cap.

## Phase Scope Reduction Rule — applied

`phase/003-storage-code.md § Phase Scope Reduction Rule` declares two triggers.

### Trigger #1 — KR-progress at day 10: **already spent, cannot fire**

Recorded in the phase file: the user took this exact collapse deliberately on
2026-08-31 (phase day 4) rather than waiting for the condition. A day-12
reader must not evaluate it. Confirmed spent; no action.

### Trigger #2 — phase-day 14: **armed, fires 2026-09-10, and buys nothing**

> *if by phase day 14 the read-side decision on `.perry/config.md` is still
> open, `P003-O2-KR1` collapses to the two call sites that are unambiguously
> internal and the two user-facing readers defer.*

Both halves need saying:

- **The condition is, formally, still open.** `phase/003-storage-code.md §
  User Commitments` still lists the read-side promise as undecided, and
  `perry/asks.jsonl` carries no answered ask for it. `USER-903` (2026-08-28)
  settled the **write** side only, which the phase file itself says.
- **The collapse would reduce a KR that is already at target.**
  `P003-O2-KR1` is `0` against a target of `0`, with all four linked rows
  (`TASK-095`, `TASK-233`, `TASK-247`, `TASK-283`) `done` and the measurement
  taken 2026-09-07. Collapsing its population to two call sites changes the
  number from 0 to 0.

So the trigger fires on a condition that is procedurally true and
substantively obsolete: the read side **already moved** — the four sites read
`.perry/config.jsonl`, `SKILL.md § Configuration` now describes the file as a
projection, and `.perry/hook.md § Configuration notes` records the 2026-08-30
move. The decision was taken in code and documentation and never recorded as
a decision.

**Recommendation (for the `goals` lane, not taken here):** close the
commitment as answered-in-substance with a dated note naming `USER-903`,
`TASK-233` and the 2026-09-07 measurement, and retire trigger #2 as spent —
or, if the user considers the promise genuinely still open, raise it as a real
`USER-` ask before 2026-09-10 so the trigger fires against a live question.

## Recommended scope cuts and actions

Ordered by leverage. None of these are applied by this file.

1. **Do not cut O3; re-baseline its denominator.** The KR is missed for a
   reason the phase can state precisely (Finding 1). Cutting it would discard
   the one measurement in this phase that is recomputed rather than asserted.
   → `goals` lane decision at scoring.
2. ~~**Re-measure `P003-O1-KR2` and `P003-O2-KR1`.**~~ **Done 2026-09-08** —
   `evidence/2026-09/2026-09-08-kr-remeasurement.md`. What remains is the KR
   change: **does `P003-O1-KR2`'s target move 6 → 7?** That is the user's at
   `score-phase`, not a re-measurement.
3. ~~**Unblock `TASK-155`.**~~ **Deferred to phase 004 by decision,
   2026-09-08.** It is blocked on a claim-surface authorization, not on
   another row; the board now names that.
4. ~~**Triage the never-moved rows and the board overrun.**~~ **Done
   2026-09-08** (Finding 5). The scope call was taken: TASK-217/218/220/231
   defer to phase 004, and phase 003 closes by hand. The board overrun stands
   at 225/200 — it comes down by closing or dropping rows, not by deferring
   them.
5. **Re-render `phase/003-linkage.md`** to clear the one linkage-store drift,
   which is on `P003-O3-KR2` itself (Finding 1). → `goals` lane.
6. **Answer or park `USER-917` / `USER-918`** (DESIGN-016 decisions 1 and 2,
   idle 4d). They block `TASK-362` and `TASK-365` and neither is on the
   phase's critical path — parking them explicitly is a legitimate outcome.

## Health-check summary (inline)

Full report: `evidence/2026-09/health-check-2026-09-08.md`.

- Architecture audit, runbook check and incident patterns are **N/A** on this
  project by declared absence, not by scan failure.
- Digests: 0 active, 0 archive candidates. **Four** knowledge cards, all with
  `owner —`, and `knowledge/INDEX.md` lists only three — the card written
  2026-09-07 from `TASK-278` was never indexed.
- BOARD: 224/200 lines, 12 rows idle >= 7d and never moved, **0** evidence-less
  `done` claims across 211 closures.

## What this review did not measure

- **Objective-level OKR percentages.** `perry-state --json` carries no
  progress figure for the five overall objectives, so this file prints none.
- **Whether the 918 commits map to the 113 closures.** Not attempted; the
  event log is the record used here.
