# `/pmo review <task-id> [<task-id> …]` — dispatch a V4

V4 is *a fresh-context reviewer against written acceptance criteria*. Both
halves are load-bearing, and each one is a different way to fake the rung:

- A reviewer that shares the author's context re-runs the author's reasoning
  and confirms it. That is **V1 wearing a costume**.
- A fresh reviewer with **no written criteria** invents its own bar, so the
  round's verdict tells you what that agent happened to value, and the next
  round tells you what the next one valued. This is why rounds stop
  converging.

So this page has exactly two jobs: make the criteria exist before the agent is
spawned, and make the verdict come back in a shape something can read.

For handing work *out* see `delegate.md`; for automated end-to-end execution
with the architecture gate see `dispatch.md`. This page is the verification
round, which neither of those covers.

## Why this page exists

Perry's own board ran **ten V4 rounds in one night** with no convention. They
wrote the verdict **five different ways** — `FAIL`, `**Verdict**`,
`> **VERDICT —**`, `> **Verdict:**`, and a decorated section heading
(`## 1 · TASK-067 — row integrity · **FAIL**`). Three carried no line a parser
could find at all.

**A verdict no tool can read is a verdict that gets misfiled, and it was.**
Rows sat at `review` after their review had already failed — reported by the
user, not by any check — because the round's verdict lived in prose and
nothing moved the row. The multi-row rounds are worse: one round covering five
rows produced one verdict word, and which row it applied to was recoverable
only by reading.

That is this repository's own recurring defect, applied to its own process:
**a rule stated in prose that nothing implements**, and **N implementations of
one rule**. `perry-lint --reviews` now reads the block below, which is what
makes this page a convention rather than advice.

## 1 · Refuse without written criteria

```
"$PERRY_HOME/bin/perry-task" list --json     # the row's `evidence_paths`
```

The criteria file is what the reviewer is told to judge against — typically
`evidence/<YYYY-MM>/<TASK-ID>-spec.md` or a `§ What must be true when this is
done` section in the task's own evidence file. **If it does not exist, stop and
write it, or run a lower rung and say so.** Do not spawn the agent and ask it
to infer the bar; an inferred bar is the failure mode above.

The criteria are written **by the author, before the round**. Criteria written
after a FAIL are a negotiation with the result.

## 2 · The prompt

Reference the standing constraints, do not retype them. Retyping is how one
round ends up with a constraint the last round had and this one dropped.

```
Read $PERRY_HOME/work/reference/review-constraints.md and follow it.

You are reviewing <TASK-ID> at V4. You did not write this code and you are not
being asked to agree with it.

Acceptance criteria: <path>              ← the only authority for PASS/FAIL
Under review:        <paths / commit range>

<one paragraph: what the change claims to do>
```

Then the four rules below, verbatim. Each one was bought with a round that did
not converge.

### The four rules

1. **Enumerate the category. Do not find the next instance.**
   When you find a defect, the deliverable is *every* place that category
   occurs, obtained by enumeration — not the next one you happen to see.
   TASK-044 spent three rounds on "the migration write that is not guarded":
   rounds 1 and 2 each guarded the site they had seen, and round 3 enumerated
   all five and found **three** still unguarded, one of them the recovery path
   itself. Rounds 1 and 2 were not lazy; they were asked the wrong question.

2. **Mutate. Do not read.**
   A claim that code handles a case is verified by breaking the code and
   watching the check go red. **A green mutation is a finding either way** —
   either the guard does not work or the test does not test it. Revert exactly
   the line you claim to revert: anchor by line number, never
   `str.replace(old, new, 1)` on a string that occurs more than once. And clear
   `__pycache__` **and wait past the second boundary** — CPython validates
   bytecode on mtime-in-whole-seconds plus size, so a same-size edit reverted
   within one second runs the stale `.pyc` and shows you a result that never
   happened.

3. **Do not trust the previous round's verdict, including a PASS.**
   Every round in Perry's own history found real defects in what the previous
   round approved, and that includes rounds reviewing the reviewer's own fixes.
   A prior PASS narrows where to look last, not where to look first.

4. **Say what you did not check.**
   The verdict block requires it. This is the V5 signature's discipline moved
   down a rung, and it is the mechanism that makes round N+1 cheaper: without
   it, the next round re-covers the ground this one covered and misses the
   ground it skipped, which is the whole shape of a review that will not
   converge.

## 3 · The verdict block — one per row, fixed shape

Required at the end of the review document. Not a heading, not bold prose, not
a sentence — this block, so `perry-lint --reviews` can read it:

```
=== VERDICT ===
task: TASK-044
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-044-spec.md
checked: guarantees 1,2,4,5 on gimegime-pmo (365→380 ids, 59→15 errors);
         all five project-write sites enumerated
not-checked: PolyForge beyond the refusal message; any Windows path
proof: bin/perry-migrate:1204 C.declare sits outside the try added in round 1
=== END VERDICT ===
```

**One block per row reviewed.** A round covering five rows emits five blocks.
`result` is `PASS` or `FAIL` and nothing else. A `FAIL` whose `proof` does not
name a file and line is not a FAIL yet — it is a suspicion, and it goes back to
the reviewer.

## 4 · Independent rows go out as one round

Rows with no dependency between them are reviewed **concurrently**, not in
sequence. Six rows dispatched one at a time is six times the wall clock for the
same verdicts, and that is how a board of `review` rows ages.

```
"$PERRY_HOME/bin/perry-task" list --json    # `startable`, `blocked_by`
```

Two rows touching the same files still go out together — they get **separate
agents and separate verdict blocks**, because merging them produces one verdict
that fits neither row.

## 5 · After the round

Each verdict block drives exactly one call, and a FAIL never leaves the row at
`review`:

```
PASS → "$PERRY_HOME/bin/perry-task" done <ID> --evidence <review-doc> --rung V4
FAIL → "$PERRY_HOME/bin/perry-task" status <ID> --status in_progress \
           --next "<what the FAIL said, and what would make it pass>"
```

`review` means *a result is out for verification*. A row whose verdict has
arrived is no longer at `review` in either direction, and a row still sitting
there after its round returned is the defect this page was written for.
