# TASK-285 — round 5 result

> **Checkout**: isolated worktree `.claude/worktrees/agent-a82a62fdb170d04f0`,
> on `coding/task-285-round5-span-lines`, cut **from `main` by ref**. The
> worktree's own HEAD was an unrelated older commit (`d49964e`), so round 4 and
> its V4 review existed only on `main`; `main` was never checked out, switched,
> merged into or pushed. No push, no PR.
>
> **Base pinned once**, per the standing correction:
> `BASE = git merge-base HEAD main = 9923a087f400f8cf0c93ac6969bf858120060deb`.
> Every restore in every battery is a byte copy from pristine extracts taken
> from **that sha** — never from `main`, which moves — and every restore is
> asserted to return the file's sha256 to its pre-mutation value.
>
> Every plant is anchored **by line number AND by an assertion on the old text
> at that line**. That assertion earned its place this round: it aborted a
> 19-line wholesale-rewrite plant because `dispatch.md:212` is `output".` and
> not the line I had written down. Without it the plant would have landed
> somewhere else and reported a false GREEN — round 4's own harness fired once
> on a blank line for want of exactly this.
>
> Between plant and run: `find . -name __pycache__ -prune -exec rm -rf {} +`
> and `sleep 1.1`, past the whole-second boundary. Scoring **differences the
> failing-test set against baseline**, never pass/fail.

Criteria: the round-4 V4 review's FAIL (`TASK-285-round4-v4-review.md`),
`TASK-285-round4-result.md`, and `TASK-285-spec.md`.

---

## The fix, in one line

`tests/test_spec_scannability.py:934`, as shipped by round 4:

```python
inside = any(p == path and line in span for p, span in spans)
```

`line in span` is a **substring** test against the span's whole text where
membership in the span's **lines** was meant. Now:

```python
spans.append((path, set(src[a:b].splitlines())))
...
inside = any(p == path and line in lines for p, lines in spans)
```

## 1. The escape, reproduced first — with the exact mechanism

The mechanism is exact and had to be reproduced exactly. The keyword-bearing
line must **itself be a substring of a governed span**; a short line merely
invented is not one, which is why the PMO's first probe did not reproduce it:

```
'own git worktree'   substring of the dispatch span? True
'worktree'           substring of the dispatch span? True
'isolation'          substring of the dispatch span? True
```

So the retraction is appended to `dispatch.md` — **outside every governed
span** — with the word present and one deliberate line break putting it alone
on a short line:

```
**When this does not apply.** On a small row the agent need not have its
own
worktree
and may share the primary checkout; that is accepted practice, and no
reviewer should treat it as a defect.
```

Against the guard class, **before** the fix, scored by differencing:

```
BASELINE          failing=none                              Ran 13  OK
GREEN P1          middle line = 'worktree'          new failures: NONE  Ran 13  OK
GREEN P2          middle line = 'own git worktree'  new failures: NONE  Ran 13  OK
GREEN P3          middle line = 'isolation'         new failures: NONE  Ran 13  OK
RED   E1-natural  wrapped naturally at ~78 cols
                  -> test_every_mention_of_the_rule_is_inside_a_governed_region
post-restore sha256 == pre: True
```

And `P1` against the **whole suite**, not merely the class:

```
$ bash tests/run
✗ 1 of 114 MODULE(S) red
✗ 1 of 3253 TEST(S) failed
```

— which is **exactly the baseline** (§ 6). The row's headline deliverable
stands retracted at the foot of the file this row designates as the rule's
single home, and the suite is no redder than it was.

## 2. After the fix — the three PMO cases and the reviewer's set

All planted post-fix, all restored to `BASE` sha256, scored by differencing.
Every RED below is the same named test:
`test_every_mention_of_the_rule_is_inside_a_governed_region`.

```
BASELINE   failing=none

RED  P1        dispatch.md   middle line exactly 'worktree'
RED  P2        dispatch.md   middle line exactly 'own git worktree'
RED  P3        dispatch.md   middle line exactly 'isolation'
RED  CLINE1    dispatch.md:138        above span 1's opening heading
RED  CLINE2    git-boundaries.md:40   D2's exact address, outside span 2
RED  CLINE3    delegate.md:170        below span 3's closing heading
RED  E2        dispatch.md:138        the bare word 'worktree' alone on its line
RED  E3        dispatch.md:138        the bare word 'isolation' alone on its line
RED  E1        dispatch.md:138        CONTROL — the same sentence wrapped
                                      NATURALLY at ~78 cols
RED  D2        git-boundaries.md EOF  round 4's verified RED, unchanged
```

`E1` and `D2` are the controls that keep the fix honest: it does **not** work
only for short lines. The naturally-wrapped retraction was red before the fix
and is red after it, and round 4's own verified-RED mutation did not regress.

## 3. Controls that had to stay green — and one that did not

```
GREEN D3       dispatch.md:194   the free rationale rewritten (partial)
GREEN NEWPARA  dispatch.md:209   a whole new paragraph inserted INTO the free block
GREEN S1n      dispatch.md:138   the DECLARED vocabulary limit — a retraction
                                 phrased without either word
RED   D3b      dispatch.md:194-212  the free rationale rewritten WHOLESALE,
                                    all 19 lines, using both keywords
                                    -> test_dispatch_says_why_not_merely_what
```

`D3b` is a **finding in the round's favour and it corrects the round-4 review's
own accounting.** Finding 3 of that review counted the 1,148-character free
block as unread surface. It is not wholly unread: two other named tests assert
*into* it — `test_dispatch_says_why_not_merely_what` requires `TASK-247` and
`branch is currently checked out` to still be cited, and
`test_the_merge_side_is_stated_where_the_rule_is` requires `git merge --no-ff`.
So the free zone is unpinned but not unguarded: prose there can be improved
freely, and a "rewrite" that quietly deletes the reason the rule exists
reddens. This is now recorded in the spec's `Remainder`.

## 4. The over-firing control, and whether it is right

Planted at `dispatch.md:138`, outside every span, an ordinary sentence that
mentions a worktree in passing and retracts nothing:

```
Before dispatching, `git worktree list` prints every tree the repository
currently has; a stale one from an abandoned row is worth pruning first.
```

**What happens: it is RED**, on
`test_every_mention_of_the_rule_is_inside_a_governed_region`.

**Is that right? Yes — and the reason it is tolerable is measured, not
asserted.** Three things:

- The check is **containment, not comprehension**. It does not ask what a
  sentence means, only where a sentence on this topic may live. Making it
  distinguish an innocent mention from a retraction means putting a reader of
  English back in the middle, and a denylist over English has now lost this
  argument twice (rounds 1 and 2) — `perry/knowledge/` states the rule for this
  project generally: *Python never parses document semantics*. A guard that
  guessed would be defeated by the next sentence that is not on the list.
- The over-fire is **not new** and the fix did not create it. A naturally
  wrapped innocent mention was already red in round 4 (`E1`'s shape). The fix
  removes an *inconsistency* — short lines escaped, long ones did not — rather
  than tightening the rule. The uniform rule is the one the docstring always
  claimed.
- **The document does not become unwritable**, which is the real risk the brief
  names. Measured:

```
GREEN REMEDY      the same innocent sentence, moved INTO the free rationale
                  block (dispatch.md:209) — no new failures
RED   INSIDE-PIN  the same sentence inside the PINNED part of the span
                  -> test_the_governed_regions_are_pinned
```

  So there is a place in this very section where a passing mention of a
  worktree can be written with **no test change and no re-pin at all**: the
  free rationale block. Everywhere else the cost is one deliberate re-pin in
  the same commit — which is the friction the guard exists to impose, not a
  side effect of it. The failure message now says this in as many words, and
  says explicitly not to relax the test into one that guesses which mentions
  are safe, so that the next author who hits it has the remedy and the reason
  rather than only an obstacle.

## 5. What is carried beyond the one-line fix

**The spec's `## Bound` now carries both.** Previously the `Remainder` read
*"exactly one free block"*.

- **The vocabulary limit is written into the Bound.** A retraction phrased
  without `worktree` and without `isolation` is green at all six span
  boundaries. Round 4 declared this in the guard's docstring
  (`:913-918`) and the round-4 review correctly scored it as a declared limit
  rather than a defect — but a docstring is not the Bound, and the spec is
  where the round after this one will look. `S1n` above confirms it is still
  green after the fix, so the limit is stated at its true size.
- **The Remainder is now three zones, not one**: (1) the free block, itself
  smaller than advertised per § 3; (2) everything outside the spans that avoids
  the two words; (3) — undeclared anywhere until the round-4 review —
  keyword-bearing text wrapped short. **Zone 3 is closed by this round**; zones
  1 and 2 remain and are declared.
- The Bound also now records the over-firing behaviour and its bounded cost,
  so that § 4 is a stated property rather than something the next reviewer
  discovers.

The guard's docstring is updated to match: it states line-set membership rather
than the substring it actually shipped, names the three mutations that proved
the difference, and corrects the keyword-line census from **16 to 20** (round 4
result § 3's slip, caught by the round-4 review; recounted here —
`dispatch.md` 11, `git-boundaries.md` 7, `delegate.md` 2, every one inside a
span, so the invariant's premise holds).

## 6. Suite and lint

```
BASELINE (BASE, unmodified tree)   ✗ 1 of 3253 TEST(S) failed
AFTER the fix                      ✗ 1 of 3253 TEST(S) failed
tree guard  ✓ nothing under …/agent-a82a62fdb170d04f0 moved

$ python3 bin/perry-lint --root .
  0 error(s), 37 warning(s)
```

The single failure is **pre-existing and unrelated**, and was re-run alone
before being attributed, per the brief's instruction:

```
FAIL: test_board_render.TestTheBytesComeFromTheStore
      .test_every_rendered_field_moves_when_the_store_moves (field='status')
AssertionError: 'dropped' unexpectedly found in "| TASK-348 | …"
```

It fails identically on the unmodified tree at `BASE`, before any change of
mine, and alone as well as in the suite — so it is not a parallelism flake. Its
cause is content in `perry/tasks.jsonl` on `main`: TASK-348's note contains the
phrase *"silently dropped six call sites"*, and the test mutates the `status`
field to `dropped` and asserts the value does not appear anywhere in the
rendered row. `perry/tasks.jsonl` is off-limits to this row and is untouched.
None of the brief's four named flakes (`test_contract_key_parity`,
`test_one_primitive`, `test_one_choke_point`, `test_host_support`) fired.

## 7. Mutation ledger

Pre-fix reproduction: 4 planted — 3 GREEN (the escape, § 1), 1 RED (the
natural-wrap control). The three greens **are** the round-4 finding, reproduced.

Post-fix: **17 planted, 13 red, 4 GREEN.** Every green is named, and every one
is a declared property confirmed rather than a defect discovered:

```
GREEN D3       the free rationale rewritten (partial)      declared: USER-914
GREEN NEWPARA  a new paragraph inserted into the free block declared: USER-914
GREEN S1n      a retraction using neither keyword           declared: the
                                                            vocabulary limit,
                                                            now in the Bound
GREEN REMEDY   an innocent mention inside the free block    declared: § 4, and
                                                            the reason the
                                                            over-fire is bounded
```

Nothing green is undeclared. Round 4's five undeclared greens
(`CLINE1`-`CLINE3`, `E2`, `E3`) are all red.

## What did not move

Round 4 is otherwise strong and was not rebuilt. Untouched and still true: the
three digests, the three spans, the free block and `USER-914`'s decision, all
twelve of round 2's closed mutations, the delimiter-attack results, and
`## Deliverable` and `## Verification` in the spec — both byte-identical, so
this round is scored against the items the row was filed with.

## Files changed

```
tests/test_spec_scannability.py            the one-line fix, its comment,
                                           the corrected docstring and an
                                           actionable failure message
perry/evidence/2026-09/TASK-285-spec.md    ## Bound — Remainder corrected to
                                           three zones; the vocabulary limit
                                           and the over-fire recorded
perry/evidence/2026-09/TASK-285-round5-result.md
```

No document under `work/reference/` was edited: every plant was restored to its
`BASE` sha256, and `git status --porcelain` is empty at the end of the round.
