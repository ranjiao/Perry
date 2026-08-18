# Mode · `pipeline` — the item ships, and the next one starts

> Loaded by the router for any track whose `Mode` is `pipeline`.
> DESIGN-003 § 5.1. Covers content and copywriting (16.4% of observed agentic
> work), document processing (4.1%) and sales operations (4.0%). **Not legal
> matters yet** — see *Known limit — confidentiality* at the bottom.

Unlike `modes/project.md`, this file carries rules rather than references,
because pipeline's rules exist nowhere else in Perry yet.

## The mode contract

| Slot | Value | Where it is written |
|---|---|---|
| **Ends when** | The item ships — or is explicitly dropped | — |
| **Unit that gets an ID** | The deliverable, not the task. One ID per thing that will leave the building | `BOARD.md` row |
| **Spine** | `OKR.md § Commitments` — id · track · promise · to whom · by when · status. `By when` is a **date** for pipeline rows; queue rows in the same table may carry prose | Written by the **goals** lane |
| **Horizon** | The cycle, declared explicitly (`2026-W34`, `until 2026-09-30`) | `.perry/config.md § Tracks` → `Cycle` |
| **Calendar** | **Binding** — see *What "binding" does and does not mean* below | — |
| **Item states** | Two orthogonal fields: `Status` (the global lifecycle enum, unchanged) and `Stage` (this track's vocabulary) | `BOARD.md` → `Status`, `Stage` |
| **Stage vocabulary** | Default `brief → draft → review → approved → published` | `.perry/config.md § Tracks` → `Stages` |
| **WIP control** | A limit per stage | `.perry/config.md § Tracks` → `WIP` |
| **Dwell time** | Expected time in stage before triage flags it | `.perry/config.md § Tracks` → `SLA` |
| **Stage clock** | The date the item entered its current stage | `BOARD.md` → `Stage since` |
| **Commitment link** | The `Id` of the promise this item discharges | `BOARD.md` → `Commitment` |
| **Triage asks** | Which item is aging in which stage? | — |
| **Default rung** | **V5** — a shipped deliverable is outward-facing by definition. Three layers: the mode default (`work_modes.modes.pipeline.default_rung`), a per-track override (`Tracks` → `Default rung`), and the per-row value | `BOARD.md` → `Verification` |
| **Signature failure** | Everything sits in `review` forever | — |

### `Status` and `Stage` are orthogonal, and that is the point

`Status` keeps its global meaning in every mode — `not_started`, `blocked`,
`in_progress`, `review`, `done`, `dropped` — and stays enum-checked by
`schema/state-schema.json`. `Stage` says *where in this track's pipeline* the
item sits. An item can be `in_progress` at stage `draft`, or `blocked` at stage
`approved` waiting on a client.

They are separate columns because merging them was the first thing this mode got
wrong: a stage vocabulary written into `Status` fails lint, and one written
nowhere at all makes every rule below uncomputable. `Stage` is **not**
enum-checked in the schema, because the vocabulary is per-track rather than
global — the track register is what declares it.

**`dropped` is a `Status`, never a stage.** A dropped item leaves the ordered
vocabulary entirely — there is no `dropped` stage to move it to, and adding one
would put a terminal state into a sequence every WIP and dwell number is
computed over.

**Where it died is recorded, and it is not recorded on the board.** `perry-task
drop` removes the row: `BOARD.md` holds open work, and a dropped item is not
open work. The stage it reached goes into the two surfaces that survive the
removal — the journal's status-change line (`… → dropped · at stage: review ·
reason: …`) and the `drop` event's `stage` field — alongside the reason, like
every other drop. That is the diagnostic that matters here: three items dying at
`review` is a fact about the review stage, not about the three items, and it is
recoverable by reading the journal or the log rather than by keeping dead rows
on the board.

This file said the opposite until a review checked it — that the row's `Stage`
cell "keeps the last stage it reached" — while the only drop path deleted the
cell along with the row and wrote the stage nowhere. It is recorded now; the
claim was corrected rather than implemented, because keeping the row would
require every count in this file and in `modes/queue.md` to start excluding it.

## The calendar is binding here, and that is not a contradiction

`goals/SKILL.md § Why phases, not months` argues that calendar boundaries are
human-team theater and that a horizon should close when its results are hit.
That argument is correct — **for product work**. It does not survive contact
with a campaign launch, a client deadline, a filing date or an issue date, where
the date is not a proxy for progress but the actual commitment someone else is
relying on.

So the two rules invert cleanly rather than conflicting:

- **Project mode**: the date is advisory, the goal is binding. Shipping late is
  usually better than shipping the wrong thing.
- **Pipeline mode**: the date is binding, the scope is negotiable. When an item
  cannot make its date at full scope, the move is to **cut the item's scope and
  say so**, not to slip the date silently.

A missed commitment is a status change like any other and gets a journal line
naming what was promised, to whom, and what happened. Perry does not quietly
re-date a promise made to someone who is not in the room.

### What "binding" does and does not mean

**It is a norm the agent must uphold, not a mechanism that stops anything.**
Nothing in Perry refuses a write because a date passed: there is no lint for an
overdue commitment, no check that a missed date produced its journal line, no
alarm at midnight. Compare V5, which *does* have a named check
(`perry-lint --verification`). Saying "binding" without this paragraph would be
advisory wearing a stronger adjective, which is what an independent review of
this file called it.

So the operative difference between advisory and binding here is **what the
agent does when the two conflict**:

| | Project mode (advisory) | Pipeline mode (binding) |
|---|---|---|
| Date slips | Acceptable; the goal governs | **Not** acceptable silently — cut scope and say so, or record the miss with who was promised what |
| Triage surfaces | Stale rows by idle time | Items whose commitment date falls before the next triage, whatever their stage |
| Scope | Fixed by the goal | Negotiable, and the first thing to move |

If a future release wants binding to be a mechanism, the check to build is an
overdue-commitment lint over `OKR.md § Commitments` — recorded here so it is a
known gap rather than an unnoticed one.

**The same concession covers every other control in this file, and it has to be
said out loud or the concession is decorative.** The WIP limit, "the last stage
is what `done` means", and queue's "`Arrived` is never lost" are all norms the
agent upholds; none has a lint. WIP is the awkward one, because this mode calls
it the central control. The checks a future release would build are: WIP
overflow, an item in no stage, and a `done` row that never reached the terminal
stage.

**One of the three is now a rule a script catches.** `perry-state --json` →
`project.config.tracks[].wip_breaches` names every stage at or over its declared
limit, with the count and the limit, and `stage_counts` carries the whole
distribution — so this mode's triage step 2 reads a number instead of asking an
agent to eyeball a board the triage procedure forbids eyeballing. A track that
declares no `WIP` reports counts and no breaches: silence is the right answer
where the project made no promise.

The other two — an item in no stage, a `done` row that never reached the
terminal stage — are still norms the agent upholds. This paragraph is the
record of which is which, and it moves one line at a time as they land.

## Stages, and why the vocabulary is declared per track

The default `brief → draft → review → approved → published` fits writing. It
does not fit a legal matter (`intake → research → draft → partner review →
filed`), an invoice run, or a document-extraction batch. So the stage list is
**declared in the track register**. (An earlier draft said a pack could supply a
domain default; no such layer exists — no pack-default mechanism, no declared
precedence between track, pack and mode — so the clause was removed rather than
left as a promise.)

```markdown
## Tracks      (in .perry/config.md)

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| blog | pipeline | commitments | brief→draft→review→approved→published | review:2 | 5d | 2026-W34 | V5 |
```

- **`Stages`** — arrow-separated, ordered. Absent → the default above.
- **`WIP`** — per-stage limits, **by name only**: `stage:n`, comma-separated,
  e.g. `review:2,draft:4`. A stage not named has no limit. (Name form only —
  a positional grammar was considered and dropped; two grammars is one parser
  too many.) **Default: `review:3` and no other limit**, because review
  is the stage that jams and an unlimited review queue is this mode's signature
  failure.
- **`SLA`** — expected dwell time in a stage before triage flags it. One value
  for the track; `5d` means five **calendar** days, and an item sitting in any
  stage that long is surfaced. **No default in any mode** — a turnaround time is
  a commitment the project makes to someone, and inventing one would put words
  in the user's mouth. A track without `SLA` cannot run triage step 1, and
  triage reports that as a finding rather than skipping the step silently. This is the **single home for SLA** in both pipeline and queue mode
  — an earlier draft of these two files put it in two different places.
- **`Cycle`** — what bounds the current horizon. An ISO week, a date
  (`until 2026-09-30`), or a named campaign. Without it the horizon cannot
  close, because "the items due in this stretch" defines the stretch by itself.

Three rules hold whatever the vocabulary:

1. **Stages are ordered and an active item is in exactly one.** An item in two
   stages is a tracking bug, not a nuance. **Active** means `Status` is neither
   `done` nor `dropped` — the same definition `modes/queue.md` counts depth
   with, so the two modes cannot disagree about what is in flight. A row
   `perry-task drop` retired is not on the board and so cannot be counted at
   all; the `Status: dropped` case this excludes is the row a project archives
   **by hand** into a section of its own (`## Done this period` and its
   equivalents), which the reader does see. Both routes end in the same count.
2. **The last stage is the one that leaves the building**, and reaching it is
   what `done` means in this mode. An item that is `approved` but not
   `published` is not done, however finished it feels.
3. **The cycle closes when every item in it has shipped or been dropped** — not
   when its date arrives. The date is what makes items *late*; it is not what
   makes the cycle over.

## The WIP limit is the throttle, not priority

P0/P1/P2 answers *"what matters most?"* — the right question when work competes
for attention toward a goal. Pipeline work does not compete that way: every item
has a commitment and a date, and none of them can be deprioritized into
nonexistence. What actually goes wrong is **too many things in flight at once**,
which is a throughput problem, not a ranking problem.

So each stage carries a limit. When a stage is at its limit, nothing new enters
it until something leaves. If a stage is persistently full, that is the finding:
the constraint has been located, and the fix is upstream of it.

**Review is the stage that jams**, in every observed pipeline. It is where the
work stops being the agent's and starts being a human's, and it is where the
mode's signature failure lives. `triage` therefore reports stage age before
anything else, and the oldest item in `review` is the first thing the standup
names.

## Why the default rung is V5

Everything a pipeline produces goes to someone outside the project — a client, a
publisher, a filing, a customer, an audience. That is the definition of
outward-facing, so DESIGN-003's consequence rule applies to the whole mode
rather than to occasional rows in it. A human signs off, by name, with a date,
recording **what they checked**.

**Two different things, and neither is enforced this release.** The V5 here is
the *mode default* — from `work_modes.modes.pipeline.default_rung`, pre-selected
at `close-task`, refusing nothing. The separate **consequence rule** — a row
matching `.perry/hook.md § High-stakes operations` closing below V5 — is
*reported* by `perry-lint --verification` as a `consequence-needs-signoff`
**warning**, which is advisory for one release by DESIGN-003 decision 4.

Saying "enforced" here would be the same error this file spends a section
warning about one heading earlier. Reported and enforced are different words and
only one of them is currently true.

V4 (a fresh-context reviewer against a written rubric) is a genuine step and
belongs *before* the human gate, not instead of it. It is what makes the human's
job small enough that they actually do it — which is the real reason review
stages jam.

## Triage in this mode

Ordered. The first question is not "what's important" but "what's stuck":

1. **Oldest item per stage.** Anything in a stage longer than the track's `SLA`
   is named with its age, its `Commitment`, and who that commitment is promised
   to. Age is `today − Stage since`, both of them columns — arithmetic, not a
   journal search. An earlier draft measured it "from the last `Stage` change
   recorded in the journal", which cannot work: the journal records **status**
   changes, and this file's own orthogonality argument guarantees a
   `draft → review` move produces no status change and therefore no line.
2. **Stages at their WIP limit.** Compare the count of active rows per `Stage`
   against the track's `WIP` cell. Name which stage, and what is upstream of it.
3. **Commitments due within the track's `SLA` window.** Nothing records when a
   triage last ran or when the next one is due, so "before the next triage" is
   not a datum — read `OKR.md § Commitments` for rows in this `Track` whose
   `By when` date falls inside that window, take each
   one's `Id`, then scan `BOARD.md` for rows whose `Commitment` cell carries
   that id and report how far along each is. **The link is followed from the
   board side**, never by dereferencing the commitment row's `Discharged by`
   prose — that cell describes, it does not enumerate.
4. **Items with no commitment** — a blank `Commitment` cell. Work in a pipeline
   that nobody asked for and nobody is waiting on is either a missing commitment
   row or a thing that should not be in flight.

## What this mode does not assume

- **That work is planned in a weekly session.** Some pipelines are fed by an
  intake queue; when that is true, declare a second track in `queue` mode rather
  than bending this one.
- **That there is an objectives cascade.** A commitment is a promise to a named
  party by a date. A KR is the special case where the party is the project
  itself. Forcing objectives onto client work invents goals nobody set.

## Known limit — confidentiality

**Perry has no model for "this track's material must not leave this folder."**
No per-track access boundary, no redaction rule, no separation between clients
sharing one project, and no statement about what a dispatched agent may carry
out of a track.

That is fine for a content calendar. It is **not** fine for legal matters,
client-confidential work, anything under privilege, or personal data — and
pipeline mode should not be recommended for those until the gap is closed.
DESIGN-003 § 8 records it as open; this paragraph exists so nobody discovers it
by reading the design doc after the fact.

## See also

- `perry/design/DESIGN-003-work-modes.md § 5.1` — the four-mode table.
- `modes/queue.md` — the neighbouring mode for work that arrives rather than
  being committed to.
- `schema/state-schema.json § verification` — the rung definitions.
