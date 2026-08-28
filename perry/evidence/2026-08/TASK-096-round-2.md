# TASK-096 — round 2: the exemption set, after a V4 broke it

**Design**: ADR-007 rule 3. **KR**: `P002-O3-KR1`. **Rung**: V4.
**Round 1 verdict**: FAIL — `perry/evidence/2026-08/TASK-096-v4-review.md`.

The row itself asked for this round in those words: *"AWAITING a fresh V4 on the
exemption set — that is where a wrong call hides, since the main assertion sits
at 0."* It hid there.

## The failure, reproduced before it was fixed

`ADOPTION_HEADING` was `r"migrat|adopt|legacy|pre-existing|import"`. The bare
`import` matches **"important"**, and `decide/SKILL.md:240` is

```
## Hand-off contract with PMO (the most important rule)
```

`scan()` keeps `section` until the next heading, so every step under that
heading was treated as an adoption section and became unreportable for authored
documents. Reproduced with a control — the same planted step in two places:

| Planted under | Reported |
|---|---|
| `## Hand-off contract with PMO (the most important rule)` | `[]` |
| `## Style rules`, four lines lower | `(251, "an ADR's typed header", 'R1', …)` |

Two live headings matched the pattern. **One of the two was a false match.**

## The fix, and the guard that makes the next one red

`\bimport(?:s|ed|ing)?\b`. `migrat` and `adopt` stay unbounded on purpose:
every English word containing them is in the same family, and `import` is the
one stem here with a common unrelated descendant.

A tighter regex alone would not have caught this and will not catch the next
one, because **a count cannot see it** — the module's headline assertion was 0
before the fix and 0 after (measured both ways; the false exemption was hiding
nothing today, only everything written under that heading from now on). So the
new test pins the **list**: every live heading exemption 5 fires on, with the
clause saying why it is adoption. Today that set is one entry,
`decide/reference/decisions.md:280 ## Migration: old monolithic DECISIONS.md`.
A new match is a red, not a silent widening.

## Two rules were argued at length and tested by nothing

The V4 found them by mutation, and both mutations were green:

* `spec["kind"] == "document"` → `True`. The document/projection split — the
  one the row calls "the subtlest" and the docstring argues in a paragraph —
  had no test. Now `test_adoption_exempts_a_document_and_never_a_projection`
  runs the same two steps under an adoption heading and under `## Style
  rules`: under adoption the ADR file is exempt and the `DECISIONS.md` index is
  not; outside it, both report.
* `HAND_LICENCE` neutered. **R2 was not tested at all** — the rule that caught
  the two steps teaching a hand edit months after the tool closed the gap.
  `test_r2_reports_a_licensed_hand_edit_and_a_refusal_is_not_one` covers the
  rule and its own refusal clause, because a suppression with no test is how a
  guard ends up reporting the cases people know are fine.

## Mutations

| # | Mutation | Red |
|---|---|---|
| M1 | `\bimport(?:s\|ed\|ing)?\b` → `import` | `test_adoption_headings_are_actually_about_adoption` |
| M2 | `spec["kind"] == "document"` → `True` | `test_adoption_exempts_a_document_and_never_a_projection` |
| M3 | `HAND_LICENCE` neutered | `…r2…` first assertion |
| M4 | `NOT_BY_HAND` neutered | `…r2…` second assertion (line 563) |

## What this round did NOT fix, and why the number is scoped

The V4's third finding stands and is **not** fixed here: `lane_dirs()` requires
a `SKILL.md` beside a `reference/`, so the root entry point and
`packs/software-ops/*.md` are outside the corpus — and `work/SKILL.md` loads
three pack pages as work-lane procedure. **One live violation sits in the
gap**: `packs/software-ops/incidents.md:84` step 5 instructs appending a
`## Status changes` line to today's journal by hand, the section `perry-task`
owns, no tool named. `perry-task` has no subcommand that writes that line for a
non-task entity, so the fix is a procedure decision, not a rename.

`procedure_pages`'s docstring claimed "every page it can load — the whole tree".
That was false and now says what it walks. **The module's 0 is 0 across the
three lanes, not across everything an agent can be told to follow.**

Widening is TASK-101 rather than this round because it is not one line:
measured, the same scan over the root and pack pages reports **7 — one real and
six correct pages the guard cannot suppress**. A closing backtick between
subject and verb defeats the descriptive exemption twice (`` `pmo` still writes
`BOARD.md` ``), `Detect` is missing from the read verbs, and two sentences put
the target in the subject position (`the BOARD row flips to review`) where the
guard reads a state description as an order. Widening without those four
categories ships a guard that reports six correct pages, which is a guard people
switch off — and each widened exemption has to be re-checked against the three
lanes, because one that re-suppresses a lane-page violation makes the guard
weaker exactly where it is load-bearing.

## What round 2 asks the next reviewer to check

No verdict block here on purpose — this is the implementer's file. A round-2
`=== VERDICT ===` written by me would be V1 in a V4 costume, and round 1 is the
reason to care: it found a false exemption, two untested rules and a false
docstring claim, all of which I had read past.

Specifically worth attacking:

1. **Is the pinned heading list the right shape?** It is a recorded set, which
   this repo normally treats as an instance-shaped guard. The argument for it is
   that no predicate can decide whether a heading is *about* adoption — but that
   argument may be wrong, and if it is, the test is a list waiting to be
   defeated by a heading nobody adds to it.
2. **Does the `\bimport\b` boundary break a real adoption heading?** Probe
   `imports`, `importing`, `re-import`, `Importer`. `Importer` is deliberately
   not matched; decide whether that is right.
3. **Do the two new tests actually pin the branches, or only the plants?**
   Both are plant-based. A rewrite of `scan()` that keeps the plants passing
   while changing what the live pages report would be green.
4. **The three lanes still measure 0** — confirm that independently rather than
   reading it here, and confirm the fix did not un-hide a live violation
   (I measured 0 before and 0 after, which is a claim worth breaking).
