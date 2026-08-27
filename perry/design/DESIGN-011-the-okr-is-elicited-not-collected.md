# DESIGN-011: The OKR is collected as ten fields where it should be elicited

> Status: draft
> Date: 2026-08-27 · Locked: —
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: KR-O1.2 (`perry/OKR.md` v2, Objective 1 — the four work modes are usable, not just declared)
> Supersedes: —   · Superseded by: —
> Revisits: `goals/reference/setup.md`, `reference/input-quality.md`

## 1. Problem

**Perry has a quality check that grades a draft. It has nothing that produces
one.**

`goals/reference/setup.md § init` says *"Conduct the interview"* and then gives a
**ten-field checklist**: period, mission, operating principles, tracks,
objectives, KRs, anti-goals, versioning, quality pass, write.

Measured: `goals/reference/setup.md` contains **zero** `AskUserQuestion` calls.
The agent asks for fields, the user fills them in, and
`reference/input-quality.md § 1` grades the result at the end.

The rubric is good and it is not the problem. Eight checks, each with a bad→good
pair, explicitly *"advisory + override, never silent rewrite"*. That posture
should survive untouched. **What is missing is everything that happens before the
draft exists.**

### The failure mode this produces

A ten-field form invites one long answer and gets ten shallow ones. The rubric
then fires on a finished document, where every issue reads as a criticism of work
already done — which is exactly when a user is least willing to redo it. The
result is `write as-is` overrides on KRs that a two-minute exchange would have
sharpened.

### What a working version looks like

`~/.claude/skills/gstack/office-hours` does this well, and the mechanisms are
transferable even though its subject is not. Studied in full at
`perry/evidence/2026-08/office-hours-elicitation-study.md`; the four that matter:

1. **Each question states the bar for what counts as an answer** — an `Ask:`, a
   `Push until you hear:`, and `Red flags:` naming answers that look like answers
   and are not. *"Healthcare enterprises" is a filter, not a person. You can't
   email a category.*
2. **Anti-sycophancy as a banned-phrase list**, each entry paired with its
   replacement. It is a table; it costs nothing.
3. **BAD/GOOD pairs of the same exchange**, calibrating *the agent's own next
   sentence*. Perry's rubric already uses bad→good on **artifacts**; this uses it
   on the interviewer.
4. **A premise challenge before any proposal** — premises rendered as
   agree/disagree statements the user must confirm, with disagreement looping
   back.

### The thing to be careful about, stated before the design

`office-hours` is adversarial **because a founder's incentive is to believe their
own pitch.** A user setting an OKR for their own project has a different failure
mode: **not self-deception but vagueness under time pressure** — writing "improve
reliability" because the specific version costs ten more minutes.

Porting the confrontational register wholesale would make Perry unpleasant to use
for a failure mode it does not have. **What transfers is the refusal to accept a
vague answer, not the suspicion that the user is lying.**

## 2. Goals

1. `/perry goals init` asks **one question at a time** and waits, rather than
   presenting a field list.
2. Every question states, in the reference file, what a real answer contains and
   what a non-answer looks like.
3. An OKR produced through the script **passes `reference/input-quality.md § 1`
   with zero issues surfaced** — the rubric finds nothing because the elicitation
   already did.
4. The question set is **routed**, so a first-ever OKR, a revision after a pivot,
   and a phase inside a running project are not the same conversation.
5. A user who says "just do it" gets a bounded negotiation, not an argument and
   not instant capitulation.
6. `reference/input-quality.md` is **unchanged** and keeps its posture. It
   becomes the back-stop, not the front.

## 3. Non-Goals

- **Porting office-hours' content.** Demand evidence, wedges, willingness to pay
  — the method transfers, the six questions do not.
- **A second persistence store.** gstack's per-question preference tuning is
  real and is a mechanism Perry would have to own. Noted, not adopted here.
- **Touching the tier-0 router.** This lives in `goals/reference/`, loaded on
  demand. Its size is a real cost and the router is read on every invocation.
- **Changing what `OKR.md` looks like.** This design changes how its content is
  arrived at, not its shape.
- **Making the rubric a hard gate.** It is advisory + override by decision, and
  a better front end is not a reason to harden the back stop.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | What routes the question set | track spine per DESIGN-008 (Recommended) / project age / ask the user directly | TBD | — |
| 2 | How hard the push is | name the gap and offer a rewrite (Recommended) / office-hours' confrontational register / accept the first answer and let the rubric catch it | TBD | — |
| 3 | Does `plan-phase` get the same treatment | yes, sharing the question bank (Recommended) / init only for now | TBD | — |
| 4 | Where the premise challenge sits | after the questions, before writing (Recommended) / not adopted | TBD | — |

**On decision 1.** DESIGN-008 already split `Mode` into **spine** and **flow**. A
`project`-spine track decomposes a goal; a `queue`-spine track manages an arrival
rate. Those want different questions, and today `init` asks the same ten of both.
The axis exists; this would be its first consumer.

## 5. Architecture

### 5.1 A question bank, not a script

`goals/reference/elicitation.md`. Each entry:

```
### Q<n> · <what it is for>

Ask:                 the question, in the user's language
Push until you hear: what a real answer contains
Red flags:           answers that look like answers and are not
Produces:            the field(s) this answer becomes
Skip when:           the condition under which it is already answered
```

**`Produces:` is the load-bearing field.** It is what keeps this an elicitation
rather than a re-skinned form: every question exists because a specific part of
`OKR.md` needs it, and a question that produces nothing does not belong.

### 5.2 Routing

```
first-ever OKR      →  mission, objectives, KRs, anti-goals        (the full set)
revision            →  what changed, and which KRs it invalidates
phase inside a live project  →  focus, not-about, definition of done
queue-spine track   →  arrival rate, SLA, what "resolved" means
```

Plus **smart-skip**: a question whose answer is already in the user's opening
message, or in the existing `OKR.md`, is not asked. The user should never be
asked something they have already said.

### 5.3 The push, and its ceiling

One question, then **stop and wait**. On a vague answer, **one** push that names
the gap and offers a concrete rewrite:

> *"'Improve reliability' is not measurable — there is no number and no
> deadline, so nothing can tell you at phase end whether you did it. Something
> like 'p99 latency ≤ 300 ms by 2026-09-30' would. What is the number?"*

**One push, then take what you get.** The rubric is still behind this, and a
second push on the same field spends the user's patience on the thing the
back-stop already covers.

The anti-sycophancy table applies to the agent's own sentences:

| Never | Instead |
|---|---|
| *"That's a good objective"* | say what makes it good, or push |
| *"You might want to add a metric"* | *"This has no metric. Without one, nothing can score it."* |
| *"That could work"* | say whether it will, and what is missing |

### 5.4 The escape hatch

1. *"just do it"* → **one** offer: *"Two more questions, then I'll draft it —
   they're the two that decide whether the KRs are scoreable."* Ask the two the
   routing table ranks highest.
2. Second refusal → **yield immediately**. Draft from what exists and let the
   rubric do its job.
3. A fully-formed OKR pasted in → skip to the premise challenge.

**The rubric always runs.** It is the thing that cannot be skipped, because it is
advisory anyway — the user can override every issue, and that override is
recorded.

### 5.5 The premise challenge

Before writing, state back what was heard, as statements to agree or disagree
with:

```
PREMISES
1. The project's mission is <…> — agree?
2. Objective 2 exists because <…>, which traces to the mission clause <…> — agree?
3. You are NOT trying to <…> this period — agree?
```

Disagreement loops back to the question that produced the premise.

**This is the step that would have caught three of this project's own defects
this week** — TASK-037's already-fixed findings, TASK-040's obsolete title, and
the v2 delegation prompt's stale out-of-scope prose. Stating a premise out loud
is what makes a stale one visible.

### 5.6 What does not change

`reference/input-quality.md`, byte for byte. Goal 3 is that it finds **nothing**
— not that it stops running.

## 6. Implementation plan

1. **The question bank**, for the first-ever-OKR route only. No routing, no
   escape hatch. Prove the shape on one path.
2. **A real transcript**: run it against a project that has no `OKR.md`, and run
   the rubric on the output. Goal 3 is measured here or it is not measured.
3. **Routing and smart-skip**, per decision 1.
4. **Escape hatch and premise challenge**, per decisions 2 and 4.
5. **`plan-phase`**, per decision 3, reusing the bank.

**Step 2 is the gate.** If a bank-produced OKR still trips three rubric checks,
the questions are wrong and steps 3–5 are decoration.

## 7. Risks & mitigations

| # | Risk | Blast radius | Detection signal | Mitigation |
|---|---|---|---|---|
| 1 | The script is longer than the form and slower to no benefit | `init` becomes something users avoid, and OKRs get written by hand outside Perry | step 2's transcript — count questions and rubric issues | a question that does not name a `Produces:` field is cut |
| 2 | The confrontational register ports with the method | Perry becomes unpleasant for a failure mode it does not have | read the rendered prose aloud; if it sounds like an interrogation it is wrong | decision 2, and § 1's statement of the different failure mode |
| 3 | The push loops and the user cannot get out | worse than no elicitation | one push per field, asserted in the reference file | the escape hatch yields on the **second** refusal, not the third |
| 4 | Smart-skip skips a question the user only half answered | a field filled from a partial answer, with no push | `Skip when:` states a **condition**, not a judgement call | a skipped question's field is shown in the premise challenge, so a wrong skip surfaces before writing |
| 5 | The bank drifts from the rubric | two documents disagreeing about what a good KR is — this project's most-paid-for defect | a test that every rubric check in § 1 has a question whose `Produces:` covers it | the bank cites the rubric row it serves |

## 8. Open questions

- **Does this belong to `goals` alone?** `decide new` and `work add-task` run the
  same rubric on their own inputs. The bank might be shared, which would make it
  a `reference/` file rather than a `goals/reference/` one — and would make its
  size a cost three lanes pay.
- **Is `AskUserQuestion` the right instrument for an open question?** It renders
  2–4 options. *"What is this project's mission?"* has no options, and the host
  matrix's Codex fallback is free text anyway. The reference file has to say
  which questions are choices and which are prose.

## 9. Changes (append-only after lock)

## 10. References

- `perry/evidence/2026-08/office-hours-elicitation-study.md` — the study this
  design is drawn from, with all nine mechanisms and a verdict on each.
- `~/.claude/skills/gstack/office-hours/SKILL.md` lines 872–1697 — the skill
  itself, minus gstack's shared preamble.
- `goals/reference/setup.md § init` — the ten-field checklist this replaces.
- `reference/input-quality.md § 1` — the rubric that stays exactly as it is.
- `perry/design/DESIGN-008-track-axes.md` — the spine/flow axis decision 1 would
  make its first consumer.
