# verification/numbers-migrate-between-sentences — a count measured for one claim gets reused in a sentence about a different claim, and stays plausible

- Kind: knowledge
- Owner role: —
- Source: TASK-234 round 3 · evidence/2026-08/TASK-234-round3-v4-review.md; TASK-241; the PMO's own briefs, 2026-08-29
- Last verified: 2026-08-30
- Invalidated by: a convention that every number in a record carries the command that produced it, enforced by something that can fail

A number is measured, correctly, for one purpose. Later a sentence needs a
number of roughly that shape, and the measured one is close enough to reach
for. It is not re-measured, because it was measured — the memory of having
counted is doing the work that the counting did.

Three instances in one session, all caught by someone other than the author:

| the number | true of | reused to claim | found by |
|---|---|---|---|
| **17** | tests *moved* in § 4.3 | tests *routed through* the helper | the round-3 reviewer, wrapping the helper at runtime: **14 methods, 16 invocations** |
| **5 failures** | the suite an hour earlier | the suite now | the PMO, after the figure had reached three review briefs |
| a proof of a *whole-file* check | what the reviewer showed | a proof that a detector was *complete for its class* | a second reviewer, after it had passed through a spec, a RESULT and a commit message |

The shape is constant: **the number survives the move because nothing about it
looks wrong.** It is the right order of magnitude, it came from a real
measurement, and the sentence it lands in is about a neighbouring property of
the same object. Nothing in the text records which question it answered, so
nothing in the text can contradict it. A reviewer who re-derives the *claim*
still passes it; only a reviewer who re-derives the *number* catches it.

## What actually catches it

Not care, and not review — all three of these were written carefully and read
by someone. What caught them was **re-measuring the number against the sentence
it now sits in**, using an instrument chosen for the new question:

- the 17 fell to wrapping the helper and counting invocations at run time,
  because that is what "routed through" means, and reading § 4.3 is not.
- the 5 fell to re-running the suite.
- the proof fell to reading what the reviewer had actually demonstrated.

So the rule is not "check your numbers". It is: **a number quoted in support of
a claim must have been produced by an instrument aimed at that claim.** If the
record cannot say which command produced it, the number is a memory, and a
memory is not a measurement.

## The cheap defence

Carry the command with the number, in the same sentence, always — the way this
project already requires for "these were the rest" (which must be a command
whose output is the empty set, or be written as a count). A number with its
command attached cannot migrate: moving it to a new claim visibly moves a
command that does not answer the new question, and that is legible to any
reader, including the author a day later.
