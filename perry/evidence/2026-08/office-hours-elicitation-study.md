# How `office-hours` elicits, and what Perry's OKR setting is missing

> Study made 2026-08-21 at the user's request, against
> `~/.claude/skills/gstack/office-hours/SKILL.md` (1,697 lines, of which roughly
> 830 are gstack's shared preamble — the skill itself is lines 872–1697).
> Compared against Perry's `goals/reference/setup.md` and
> `reference/input-quality.md`.

## The gap, in one sentence

**Perry has a quality check that grades a draft. `office-hours` has an
elicitation that produces one.**

Perry's `init` says *"Conduct the interview"* and then gives a **ten-field
checklist** — period, mission, principles, tracks, objectives, KRs, anti-goals,
versioning, quality pass, write. `goals/reference/setup.md` contains **zero**
`AskUserQuestion` calls. The agent asks for fields, the user fills them in, and
the rubric grades the result at the end.

`office-hours` never asks for a field. It asks a question whose *answer becomes*
a field, pushes until the answer is specific enough to be worth writing down,
and only then writes.

Perry is not starting from nothing: `reference/input-quality.md § 1` is a real
rubric with eight checks and a bad→good pair on each, and it is explicitly
*"advisory + override, never silent rewrite"*. That is the right posture and it
should survive. **What is missing is everything that happens before the draft
exists.**

## The nine mechanisms, and which transfer

### 1 · A routing question first, and it forks the whole session

Before anything else: *"what's your goal with this?"* — six options collapsing to
two modes. **Startup mode** gets an adversarial diagnostic; **builder mode** gets
an enthusiastic collaborator. Different posture, different questions, different
closing.

The skill says this outright: *"This is a real question, not a formality. The
answer determines everything about how the session runs."*

**Transfers, and Perry already has the axis.** DESIGN-008 split `Mode` into
**spine** and **flow**. A `project`-spine track and a `queue`-spine track want
genuinely different OKR conversations — one decomposes a goal, one manages an
arrival rate — and today `init` asks the same ten questions of both.

### 2 · Stage routes which questions get asked, so it never asks all of them

```
Pre-product          → Q1, Q2, Q3
Has users            → Q2, Q4, Q5
Has paying customers → Q4, Q5, Q6
Pure engineering     → Q2, Q4 only
```

Six questions exist; **at most three are ever asked**. Plus *smart-skip*: if an
earlier answer already covers a later question, drop it.

**Transfers directly.** A first-ever OKR, a second version after a pivot, and a
phase inside a running project are three different conversations. Perry runs one.

### 3 · One question at a time, and the skill says STOP

`**STOP** after each question. Wait for the response before asking the next.`
Every question is its own `AskUserQuestion`. Perry's `init` presents ten fields
as a list, which invites one big answer and gets ten shallow ones.

### 4 · Each question states the bar for what counts as an answer

This is the mechanism Perry lacks most completely. Every question carries:

- **Ask:** the question, in words
- **Push until you hear:** what a real answer contains
- **Red flags:** answers that look like answers and are not

> **Q3 — Ask:** *"Name the actual human who needs this most."*
> **Push until you hear:** a name, a role, a specific consequence.
> **Red flags:** *"Healthcare enterprises." "SMBs."* — **these are filters, not
> people. You can't email a category.**

Perry's rubric has the *judgement* (`1.2 KR is an outcome, not an output`) but
it fires **after** the draft. Moving the same judgement in front of the answer
turns grading into coaching.

### 5 · Anti-sycophancy as a banned-phrase list

Not "be direct" — an actual list of sentences never to say, each with the
replacement:

| Never say | Instead |
|---|---|
| *"That's an interesting approach"* | take a position |
| *"There are many ways to think about this"* | pick one, say what evidence would change it |
| *"You might want to consider…"* | *"This is wrong because…"* |
| *"That could work"* | say whether it **will**, and what evidence is missing |

**Highly transferable, and cheap.** It is a table.

### 6 · Pushback patterns as BAD/GOOD pairs of the same exchange

Five worked examples showing the same moment handled softly and rigorously:

> Founder: *"Everyone I've talked to loves the idea"*
> **BAD:** *"That's encouraging! Who specifically have you talked to?"*
> **GOOD:** *"Loving an idea is free. Has anyone offered to pay? Has anyone
> asked when it ships? Has anyone gotten angry when your prototype broke?
> Love is not demand."*

This is the single most transferable teaching device in the file, because it
calibrates *tone and force*, which a rubric cannot. Perry's rubric already uses
bad→good on **artifacts**; this uses it on **the agent's own next sentence**.

### 7 · An escape hatch that is a bounded negotiation, not a switch

1. User says "just do it" → *"the hard questions are the value… let me ask two
   more, then we'll move"*, choosing the two most critical for their stage.
2. User pushes back a second time → **respect it immediately**. Don't ask a third
   time.
3. A **full** skip only for a fully formed plan with real evidence — and even
   then the premise challenge and the alternatives still run.

**Transfers, with Perry's own twist:** the things Perry must never skip are
different (a KR with no baseline, an objective with a metric inside it), but the
shape — *negotiate once, then yield, and keep the two gates that are not
negotiable* — is exactly right.

### 8 · Premise Challenge before any proposal

Premises are rendered as agree/disagree statements the user must confirm:

```
PREMISES:
1. [statement] — agree/disagree?
```

Disagreement loops back and revises the understanding. **This is the step that
would have caught three of today's own defects** — TASK-037's already-fixed
findings, TASK-040's obsolete title, my own v2 delegation prompt's stale
out-of-scope prose. Stating the premise out loud is what makes a stale one
visible.

### 9 · Alternatives are MANDATORY, with a shape and a hard stop

2–3 approaches, and the composition is prescribed: one **minimal viable**, one
**ideal architecture**, one optional **creative/lateral**. Each with effort,
risk, pros, cons, what it reuses. Then a stated recommendation — and then:

> **STOP.** *"A 'clearly winning approach' is still an approach decision and
> still needs explicit user approval… Writing the recommendation in chat prose
> and continuing forward is the failure mode this gate exists to prevent."*

**Perry has this already**, in the `decide` lane: `## 4. User Decisions` with
options and a lock gate that refuses on an unresolved row. **The goals lane has
no equivalent.** An objective is chosen and written; it is never presented as
two alternatives with a recommendation.

## What does NOT transfer

- **The YC content.** Demand evidence, wedges, willingness to pay. Perry's users
  are running projects, not raising money. The *method* transfers; the six
  questions do not.
- **Length.** The skill is 1,697 lines. Perry's router is tier-0 and read on
  every invocation; this belongs in `goals/reference/`, loaded on demand, and its
  size is a real cost.
- **`gstack-question-preference` / per-question tuning.** Real, and a second
  persistence mechanism Perry would have to own. Note it; do not adopt it in the
  same change.

## The one thing to be careful about

`office-hours` is adversarial **because a founder's incentive is to believe
their own pitch**. A user setting an OKR for their own project has a different
failure mode: not self-deception but **vagueness under time pressure** — writing
"improve reliability" because the specific version takes ten more minutes.

The force should be aimed there. Porting YC's confrontational register wholesale
would make Perry unpleasant to use for a failure mode it does not have. What
transfers is **the refusal to accept a vague answer**, not the suspicion that the
user is lying.

## Recommendation

One design doc, in the `decide` lane. Its core proposal: **an elicitation script
for the goals lane**, carrying mechanisms 1, 2, 3, 4, 5, 6, 7 and 8, with 9
already solved by the `decide` lane's User Decisions table and worth mirroring
rather than reinventing.

`reference/input-quality.md` stays exactly where it is and keeps its posture. It
becomes the **back-stop** — what runs on the draft — and the elicitation becomes
the **front**, so that by the time the rubric runs it should find nothing.
