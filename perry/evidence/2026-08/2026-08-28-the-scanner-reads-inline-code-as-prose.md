# The id scanner honours a fence and not a backtick

> Found 2026-08-28 by TASK-158, which noticed that **my own spec for it** had
> added two entries to the dangling list. **This narrows TASK-179's decision and
> should be read before it is made.**

## The measurement

`perry/evidence/2026-08/TASK-158-spec.md` quotes the same regex twice:

```
line 18   inside a ``` fenced block
line 25   inside `inline backticks`
```

```
$ perry-explain Z0-9
Z0-9  —  (no title found)
  defined    NOWHERE — this ID is referenced but never defined
  mentioned  perry/evidence/2026-08/TASK-158-spec.md:25
```

**Line 25 only.** The fenced block at 18 is invisible to the scanner; the inline
code span at 25 is not. So the scanner already knows that code is not prose — it
just applies that knowledge to one of the two ways markdown spells it.

## `Z0-9` is not a borderline id. It is not an id.

It is a fragment of `[A-Z][A-Z0-9]{1,9}-\d{1,4}` — a character class, read as a
family name plus a number. No policy about "how much writing about ids should
cost" makes this entry correct. **It is a false positive, and it is fixable
without weakening anything.**

## Why this matters for TASK-179 specifically

TASK-179's decision was framed as a tradeoff: *widen the report mark, exempt
evidence records wholesale, or accept the cost in writing.* Every option treats
the dangling entries as **real citations whose cost we are choosing how to pay.**

At least one is not a citation at all. Today's list:

```
FOO-001   my TASK-158 spec's example of an unknown family — a real mention
Z0-9      a regex fragment inside a code span — NOT AN ID
RX-005    quoted in TASK-118's result record as a next-minted id
TASK-007  ·  TASK-9999   checker output quoted in fourteen records
USER-904  quoted in TASK-118's result record
```

**Excluding inline code spans removes `Z0-9` outright and costs nothing**, because
nobody cites an id they mean *only* inside a code span — a real citation appears
in prose somewhere too, and the scanner would still see it there.

That does not settle TASK-179. `FOO-001`, `RX-005` and `USER-904` are genuine
mentions and remain exactly the question they were. **But the decision should be
made against the list of real mentions, not against a list padded with a regex
fragment.**

## The other thing this says about me

**I added `FOO-001`, `RX-005`, `USER-904` and `Z0-9` to that list tonight, in
documents about this defect.** The list I reported in the handoff as
`TASK-007, TASK-9999, USER-900, USER-902, WIT-404` is now a different list, and
four of the six entries are mine, from this session.

That is not an argument for writing less. It is the measurement TASK-179 needs:
**the cost is not hypothetical and it accrues fastest when the project documents
itself well.** Which is the case for fixing the false positives first and then
deciding about the true ones.

## Scope

`perry-explain § walk_md` / `harvest` and whatever `perry-diagnose` shares with
it. **The fence rule already exists** — this is applying it to the sibling
syntax, not inventing a rule. A test needs both spellings in one fixture, or it
pins the wrong half.
