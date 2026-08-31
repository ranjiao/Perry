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

### The criteria must be bounded

A criterion is bounded when the author can name, **before the round**, the
finite set the round will check and its size. "Every reader in `bin/` and
`viewer/`" is not a set until someone says which readers those are and counts
them.

An unbounded criterion does not fail a round. It fails to **end** one.
TASK-050 asked for a category:

> "No reader resolves a header cell by its own rule. The check is a
> **category** — an enumeration over the tree — not a list of file names."

Proving that no reader *anywhere* does X is a search with no last element, and
the rounds are that search:

| round | what escaped the guard |
|---|---|
| 8 | the corpus was pruned — "30 of 30" was measured on a subset of itself |
| 9 | a one-line alias |
| 10 | a header row carried through a dict key |
| 11 | **PASS** |

Round 11 did not pass because round 10 named the last hole. It passed because
round 10 **changed the criterion** — from *the set is empty* to *the remainder
is measured and listed* — and the PASS says so in its own words:

> "A measured, listed remainder of 8 out of 76 DOES discharge the amendment."

**Eleven rounds ended on the round the criterion became decidable.** Ten of
them were spent proving a universal negative over a live tree, by a reviewer
who was right every single time. That is the shape to recognise: the rounds
were not failing to find the answer, the question had no last answer.

So the criteria file carries this block, and `perry-lint --reviews` reports its
absence as `criteria-unbounded`:

```
## Bound
Enumeration: grep -rn 'header_index(' bin/ viewer/   ← the command that produces the set
Size:        58 call sites on 68e63cf
Remainder:   readers reached only through `perry_store.load()`; out of scope
             because they never see a raw header row
```

Three criterion shapes, and what to write instead:

| written as | why it cannot end | write instead |
|---|---|---|
| "no X anywhere in the tree" | universal negative over a growing set | "these N sites, listed; the remainder is M, listed" |
| "every X does Y" | "every" is not a set | the command that enumerates X, and the number it returns **today** |
| "the guard cannot be evaded" | evasions are not a finite set | "these K evasion shapes, enumerated; a K+1th is a new row, not this round" |

This does not soften § 2 rule 1. Rule 1 says enumerate the category rather than
chase the next instance, and it is right — the failure it names is real and
cost TASK-044 three rounds. **The bound is what makes rule 1 finishable.**
Without it, "enumerate the category" and "prove a universal negative" are the
same instruction, and TASK-050 is what that costs.

A round may only widen the bound by **filing a new row**, never by re-opening
this one. A remainder that turns out to matter is a defect with its own ID,
its own criteria, and its own bound.

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

### What V4 does not judge

V4 answers one question: **does this code do the wrong thing on an input the
user can produce?** Everything else the round can see is somebody else's job,
and giving it to V4 is the second reason rounds do not converge.

Measured on this board — 79 review documents, 54 `## Finding` headlines, 5 of
them meta — **22 of the remaining 49 are about the round's own artifact rather
than the product**:

> "the harness is a regression corpus, not a harness" · "the corpus was pruned"
> · "the reported baseline was incomplete" · "the commit record misreports a
> mutation" · "three citations point at a file the branch does not carry" · "a
> claimed filing, on the branch, that is not there" · "the code comment's
> factual claim is false" · "the KR reframing must become an edit"

Not one of those is a defect a user could hit. They are real — every one was
correctly found — and they exist because the protocol **manufactures an
artifact**, and the artifact has more failure modes than the code does. Round
N+1 then audits round N's artifact, which is a loop with no product in it.

So the line, and it is not "stop caring about test quality":

| finding | rung | why |
|---|---|---|
| a mutation comes back **green** | **V4** | the guard does not work, or the test does not test it. § 2 rule 2. This is a product finding wearing a test's clothes. |
| a guard reports **correct** code | **V4** | a false positive is a defect users switch the guard off over |
| the cited path is not on the branch | **pre-check** | `perry-lint --reviews` → `citation-not-on-branch` |
| the criteria carry no bound | **pre-check** | `criteria-unbounded` |
| the baseline / corpus / mutation table is incomplete | **the author, before dispatch** | it is the author's exhibit; an incomplete exhibit is not sent |
| a comment, a KR or a commit message misstates something | **file a row** | a documentation defect with its own ID, never a FAIL on this one |

**The pre-check runs before the round is dispatched, not inside it.**

```
"$PERRY_HOME/bin/perry-lint" --reviews --strict     # red → fix the exhibit, do not dispatch
```

A round dispatched over a red pre-check pays a full fresh-context review to
learn something a regex knew. That is the most expensive way this board has
found to discover a broken citation, and it found it four times.

**A FAIL must name a behaviour.** `proof:` points at the line that is wrong and
`checked:` names the input that reaches it. A FAIL whose proof is "the evidence
does not establish this" is not a FAIL — it is the pre-check, arriving late and
costing a round.

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

## 6 · Two FAILs is a decision, not a third round

**After the second FAIL on a row — two being the default limit, see the end of
this section — you may not dispatch another round.** File the ask instead.
`perry-lint --reviews` reports the row as `review-rounds-exhausted` until an
open ask in `asks.jsonl` names it in `blocks`.

This is the most expensive rule on the page and it was bought with the whole
board. Measured on Perry's own state: **20 rows entered V4 and 74 rounds were
burned.** Ten rows needed three or more. TASK-050 and TASK-249 each reached
**round 11**. TASK-095 FAILed five times, and the escalation that ended it —
USER-905 — was filed by hand at round 5, after which the user picked a
principle and round 6 PASSed on the first try.

Read the five TASK-095 FAILs in the journal and they are one sentence:

> Every one is the same shape: two situations answered as one, one step to
> the left of the last.

Rounds 3, 4 and 5 were not finding new defects. They were re-deriving one
undecided principle differently each time — and each round costs a dispatch, a
fresh-context review and a fix cycle, with the session paying its entire
context on every turn of all three. **Rounds after the second are the most
expensive thing Perry does and the least likely to converge.**

The second FAIL is the signal, and it is legible at the second FAIL. Rule 1
says enumerate the category rather than find the next instance; **two FAILs
means the category is not a category — it is a fork nobody has taken.** The
deliverable is no longer a fix, it is the choice:

```
"$PERRY_HOME/bin/perry-task" ask --needed "<A vs B, and which you recommend>" \
                                 --blocks <TASK-ID>
```

Write it the way USER-905 was written, because that is the one that worked:
state the two readings so each is defensible **applied consistently**, show
that the current code holds both, name your recommendation with its reason,
and say what is already true (which tool computes the rule today, what is
merged, what is not). The user picks a principle; the next round applies it
everywhere and PASSes.

**Two is a measured default, not a law.** It is
`schema § thresholds.review_fail_rounds_before_escalation`; a project sets its
own with `- Review rounds before escalation: N` in `.perry/config.md`, and a
single run overrides both with `PERRY_REVIEW_ROUNDS=N`. The finding names
which of the three set the limit it is enforcing. Raise it for work that
genuinely converges by accretion; `1` makes every FAIL a decision point.

A `review-rounds-exhausted` finding is never cleared by running the round
anyway.
