# Mode · `pipeline` — the item ships, and the next one starts

> Loaded by the router for any track whose `Mode` is `pipeline`.
> DESIGN-003 § 5.1. Covers content and copywriting (16.4% of observed agentic
> work), document processing (4.1%) and sales operations (4.0%). **Not legal
> matters yet** — see *Known limit · confidentiality* at the bottom.

Unlike `modes/project.md`, this file carries rules rather than references,
because pipeline's rules exist nowhere else in Perry yet.

## The mode contract

| Slot | Value | Where it is written |
|---|---|---|
| **Ends when** | The item ships — or is explicitly dropped | — |
| **Unit that gets an ID** | The deliverable, not the task. One ID per thing that will leave the building | `BOARD.md` row |
| **Spine** | `OKR.md § Commitments` — track · promise · to whom · by when · status · discharged by | Written by the **goals** lane |
| **Horizon** | The cycle, declared explicitly (`2026-W34`, `until 2026-09-30`) | `.perry/config.md § Tracks` → `Cycle` |
| **Calendar** | **Binding** — see *What "binding" does and does not mean* below | — |
| **Item states** | Two orthogonal fields: `Status` (the global lifecycle enum, unchanged) and `Stage` (this track's vocabulary) | `BOARD.md` → `Status`, `Stage` |
| **Stage vocabulary** | Default `brief → draft → review → approved → published` | `.perry/config.md § Tracks` → `Stages` |
| **WIP control** | A limit per stage | `.perry/config.md § Tracks` → `WIP` |
| **Dwell time** | Expected time in stage before triage flags it | `.perry/config.md § Tracks` → `SLA` |
| **Triage asks** | Which item is aging in which stage? | — |
| **Default rung** | **V5** — a shipped deliverable is outward-facing by definition | `BOARD.md` → `Verification` |
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
vocabulary entirely; its `Stage` cell keeps the last stage it reached, so the
record says where it died. The reason goes in the journal status-change line,
like every other drop.

## The calendar is binding here, and that is not a contradiction

`okr/SKILL.md § Why phases, not months` argues that calendar boundaries are
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

## Stages, and why the vocabulary is declared per track

The default `brief → draft → review → approved → published` fits writing. It
does not fit a legal matter (`intake → research → draft → partner review →
filed`), an invoice run, or a document-extraction batch. So the stage list is
**declared in the track register**, and a pack may supply a default for its
domain.

```markdown
## Tracks      (in .perry/config.md)

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| blog | pipeline | commitments | brief→draft→review→approved→published | review:2 | 5d | 2026-W34 | V5 |
```

- **`Stages`** — arrow-separated, ordered. Absent → the default above.
- **`WIP`** — per-stage limits, `stage:n` by name, comma-separated. A stage not
  named has no limit. **Default: `review:3` and no other limit**, because review
  is the stage that jams and an unlimited review queue is this mode's signature
  failure.
- **`SLA`** — expected dwell time in a stage before triage flags it. One value
  for the track; `5d` means an item sitting in any stage for five days is
  surfaced. This is the **single home for SLA** in both pipeline and queue mode
  — an earlier draft of these two files put it in two different places.
- **`Cycle`** — what bounds the current horizon. An ISO week, a date
  (`until 2026-09-30`), or a named campaign. Without it the horizon cannot
  close, because "the items due in this stretch" defines the stretch by itself.

Three rules hold whatever the vocabulary:

1. **Stages are ordered and an active item is in exactly one.** An item in two
   stages is a tracking bug, not a nuance. Items at `Status: dropped` are
   outside the vocabulary entirely (above) and are not counted against WIP.
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

**Two different things, and only one of them is enforced.** The V5 here is the
*mode default* — it comes from `work_modes.modes.pipeline.default_rung` and is
pre-selected at `close-task`, but nothing refuses a close below it. What
`perry-lint --verification` enforces is the separate **consequence rule**: a row
matching `.perry/hook.md § High-stakes operations` that closed below V5 is
reported as `consequence-needs-signoff`. So an ordinary pipeline row closing at
V3 is currently unchecked, and a project that wants the mode default enforced
should list its publishing verbs in the hook.

V4 (a fresh-context reviewer against a written rubric) is a genuine step and
belongs *before* the human gate, not instead of it. It is what makes the human's
job small enough that they actually do it — which is the real reason review
stages jam.

## Triage in this mode

Ordered. The first question is not "what's important" but "what's stuck":

1. **Oldest item per stage.** Anything in a stage longer than the track's `SLA`
   is named with its age, its `Commitment`, and who that commitment is promised
   to. Age is measured from the last `Stage` change recorded in the journal.
2. **Stages at their WIP limit.** Compare the count of active rows per `Stage`
   against the track's `WIP` cell. Name which stage, and what is upstream of it.
3. **Commitments due before the next triage.** Read `OKR.md § Commitments` for
   rows in this `Track` whose `By when` falls before the next triage, then
   follow `Discharged by` to their board rows and report how far along each is.
   This is the step that fails silently without the `Discharged by` column.
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
