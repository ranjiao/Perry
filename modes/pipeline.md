# Mode · `pipeline` — the item ships, and the next one starts

> Loaded by the router for any track whose `Mode` is `pipeline`.
> DESIGN-003 § 5.1. Covers content and copywriting (16.4% of observed agentic
> work), document processing (4.1%), sales operations (4.0%) and legal matters
> (1.3%) — see the confidentiality limit at the bottom before using it for the
> last of those.

Unlike `modes/project.md`, this file carries rules rather than references,
because pipeline's rules exist nowhere else in Perry yet.

## The mode contract

| Slot | Value |
|---|---|
| **Ends when** | The item ships — or is explicitly dropped |
| **Unit that gets an ID** | The deliverable, not the task. One ID per thing that will leave the building |
| **Spine** | `OKR.md § Commitments` — promise · to whom · by when · status |
| **Horizon** | The cycle: the set of items due in this stretch. Closes when they have shipped or been dropped, and a dropped item must say so, not quietly roll |
| **Calendar** | **Binding** |
| **Item states** | The track's declared stage vocabulary. Default: `brief → draft → review → approved → published` |
| **WIP control** | A limit **per stage**, not a priority |
| **Triage asks** | Which item is aging in which stage? |
| **Default rung** | **V5** — a shipped deliverable is outward-facing by definition |
| **Signature failure** | Everything sits in `review` forever |

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

## Stages, and why the vocabulary is declared per track

The default `brief → draft → review → approved → published` fits writing. It
does not fit a legal matter (`intake → research → draft → partner review →
filed`), an invoice run, or a document-extraction batch. So the stage list is
**declared in the track register** (`.perry/config.md § Tracks`, the
`Stages / SLA` cell), and a pack may supply a default for its domain.

Two rules hold whatever the vocabulary:

1. **Stages are ordered and an item is in exactly one.** An item in two stages
   is a tracking bug, not a nuance.
2. **The last stage is the one that leaves the building**, and reaching it is
   what `done` means in this mode. An item that is `approved` but not
   `published` is not done, however finished it feels.

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
recording **what they checked** — and `perry-lint --verification` reports any
close below V5 on a row matching the project's high-stakes list.

V4 (a fresh-context reviewer against a written rubric) is a genuine step and
belongs *before* the human gate, not instead of it. It is what makes the human's
job small enough that they actually do it — which is the real reason review
stages jam.

## Triage in this mode

Ordered. The first question is not "what's important" but "what's stuck":

1. **Oldest item per stage.** Anything older than the stage's expected dwell
   time is named with its age, its commitment, and who it is promised to.
2. **Stages at their WIP limit.** Which one, and what is upstream of it.
3. **Commitments due before the next triage**, and whether their items are far
   enough along to make it.
4. **Items with no commitment.** Work in a pipeline that nobody asked for and
   nobody is waiting on is either a missing commitment row or a thing that
   should not be in flight.

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
