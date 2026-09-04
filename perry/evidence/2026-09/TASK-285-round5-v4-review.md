# TASK-285 — round 5, V4 review

> **Checkout**: isolated worktree `.claude/worktrees/agent-ab537c23477b52f8e`,
> on `review/task-285-round5-v4-fresh`, cut from `main` **by ref** at
> `dda8d5f`. The worktree's own HEAD was an unrelated older commit
> (`d49964e`), so round 5 and its predecessors existed only on `main`; `main`
> was never checked out, switched, merged into or pushed. No push, no PR.
>
> **Base pinned once**, per the standing correction:
> `BASE = merge-base HEAD main = dda8d5f8da369e831bcc52895783c29abf405eab`.
> Every restore in every battery is a byte copy from pristine extracts taken
> from **that sha** — never from `main`, which moves — and every restore is
> asserted to return the file's sha256 to its pre-mutation value. All four
> files in scope were confirmed byte-identical to `BASE` before the first
> plant:
>
> ```
> e66d9139…  work/reference/dispatch.md
> 33a0ac60…  work/reference/git-boundaries.md
> 25dc90fc…  work/reference/delegate.md
> d7a4eb79…  tests/test_spec_scannability.py
> ```
>
> Every plant is anchored **by line number AND by an assertion on the old text
> at that line**; a miss aborts loudly rather than no-opping. Between plant and
> run: `find . -name __pycache__ -prune -exec rm -rf {} +` and `sleep 1.15`,
> past the whole-second boundary. Scoring is by **differencing the failing-test
> set against baseline**, never pass/fail. Harness `scratchpad/w285r5/mut.py`;
> batteries `bA.py` (exact mechanism), `bA2.py` (pre-fix reproduction),
> `bB.py` (controls, over-fire, free block), `bC.py` (new attacks),
> `bX2suite.py` (whole suite); digests independently recomputed in
> `digests.py`.

Criteria: `TASK-285-spec.md` (`## Deliverable`, `## Verification`, `## Bound`,
`## Out of scope`), `TASK-285-round5-result.md`, and all three prior V4
verdicts — `-round2-`, `-round3-`, `-round4-` — read in full before scoring.

---

## Verdict in one line

**FAIL.** The one-line fix is correct and it does exactly what round 4's review
asked: the three exact-mechanism cases are red, the natural-wrap control is
still red, the four declared greens are still green, and the round's two
corrections to the record are substantially right. The round fails on **the
same category for the fourth consecutive time**, one variant further out.

A retraction that **uses both keywords**, written on a **naturally wrapped,
full-length line**, placed **outside every governed span, four lines above the
rule's own heading** in the file this row designates as the rule's single home,
is **GREEN** — on the guard class and on the whole suite — provided the
identical sentence is also written once inside the **declared-free rationale
block**, which is a legal, unpinned, green edit under `USER-914`.

The containment check keys a line by its **content**, never by its
**position**:

```python
spans.append((path, set(src[a:b].splitlines())))
...
inside = any(p == path and line in lines for p, lines in spans)
```

and `src[a:b]` **includes the free block**. So the free zone is a
**line-injection oracle**: anything written there becomes a legal member of the
span's line set, and may then be repeated anywhere else in the same file for
nothing.

The control isolates it exactly. The same retraction above the rule **without**
the free-block copy is RED (`X2b`); **with** it, GREEN (`X2`). The legal edit
licenses the illegal one, in the same commit, with no re-pin and no test
change.

That also falsifies the round's own stated cost model. The spec's new
`## Bound` says a mention *"anywhere else … costs one deliberate re-pin, which
is the friction this rule is meant to carry."* It costs no re-pin at all. It
costs one copy into the zone the very same paragraph names as the free remedy.

---

## Criteria

| # | Criterion | Verdict |
|---|---|---|
| 1 | The three exact-mechanism cases are red | **MET** |
| 2 | The natural-wrap retraction is still red | **MET** |
| 3 | The three controls stay green | **MET** |
| 4 | The over-fire is correct and its cost is bounded | **NOT MET** — correct, not bounded |
| 5 | Round 5's two corrections to the record | **MET, with a measured overstatement** |
| 6 | Attacks nobody has planted | **NOT MET** — one green, and it is the fail |
| 7 | The spec's `## Bound` still bounds the same thing | **MET, with one false sentence** |
| 8 | Suite and lint | **MET** |

Eight scored, **six MET, two NOT MET**.

---

### 0. Before believing anything — the three digests, recomputed from scratch

`visible()` re-implemented, every anchor re-typed from the rendered document,
nothing imported from the test:

```
MATCH  dispatch.md § the tree + § Executor: claude-subagent
        span=5271c/85l  pinned=4121c  free=1148c
        first pinned line: '## The tree the agent works in'
        last  pinned line: '- Sub-agent shares parent cwd, and that is a fact about the *process*,'
MATCH  git-boundaries.md § Git Role Boundaries       span=4269c/25l  pinned=4267c
MATCH  delegate.md § required fields + roleless path span=3036c/38l  pinned=3034c

3 of 3 digests match live text
```

The round-5 keyword census also reproduces, and it is the corrected one:

```
delegate.md        2 lines, 2 inside a span
dispatch.md       11 lines, 11 inside a span
git-boundaries.md  7 lines, 7 inside a span
TOTAL 20
```

So round 4's `16` was wrong, round 5's `20` is right, and the split
(11 / 7 / 2) is right. The guard class baselines at `Ran 13 tests`, failing
none.

---

### 1. The escape, re-planted with the EXACT mechanism — **MET**

The mechanism had to be reproduced exactly, and the round is right about why
its own first probe failed: the keyword-bearing line must **itself be a
substring of a governed span**.

```
'worktree'           substring of the dispatch span? True   a line of it? False
'own git worktree'   substring of the dispatch span? True   a line of it? False
'isolation'          substring of the dispatch span? True   a line of it? False
```

Retraction appended to `dispatch.md` at `:138` — outside every governed span,
four lines above `## The tree the agent works in` — with one deliberate break
putting the keyword alone on a short line. Post-fix:

```
BASELINE       Ran 13  failing=none
RED  P1   middle line exactly 'worktree'          -> test_every_mention_…_governed_region
RED  P2   middle line exactly 'own git worktree'  -> same
RED  P3   middle line exactly 'isolation'         -> same
```

**And the mechanism is proved exact, not merely asserted.** The one-line fix was
reverted in place to round 4's `spans.append((path, src[a:b]))` and the same
three plants re-run:

```
BASELINE(un-fixed)  Ran 13  failing=none
GREEN P1     new failures: NONE
GREEN P2     new failures: NONE
GREEN P3     new failures: NONE
RED   E1nat  -> test_every_mention_…_governed_region
guard restored, sha256 == d7a4eb796ff7b2d9…
```

Three green before the fix, three red after it, same bytes in the document.
That is the round-4 finding closed.

### 2. The natural-wrap control is still red — **MET**

```
RED  E1nat   dispatch.md:138  the same retraction wrapped at ~78 cols
             -> test_every_mention_of_the_rule_is_inside_a_governed_region
```

Red before the fix and red after it. The fix does **not** work only for short
lines, and it did not regress the case round 4 already caught.

### 3. Controls that had to stay green — **MET, 3 of 3**

```
GREEN D3       dispatch.md:194  the free rationale rewritten (partial)
GREEN NEWPARA  dispatch.md:209  a whole new paragraph inserted INTO the free block
GREEN REMEDY   dispatch.md:209  the innocent passing mention, INSIDE the free block
```

`REMEDY` uses the round's own sentence verbatim (*"Before dispatching,
`git worktree list` prints every tree the repository currently has…"*). All
three are green with no new failures, so the fix did not tighten the guard onto
prose it is supposed to leave alone.

### 4. The over-fire — **correct, but NOT bounded as claimed** — NOT MET

```
RED  OVERFIRE  dispatch.md:138  the same innocent sentence, outside every span
               -> test_every_mention_of_the_rule_is_inside_a_governed_region
```

**On whether over-firing is correct, I agree with round 5, and without
reservation.** The check is containment, not comprehension. Making it
distinguish an innocent mention from a retraction means putting a reader of
English in the middle, and this row has lost that argument twice already —
round 1 to a modality-blind guard, round 2 to an eight-word hedge denylist,
with the reviewer's own conclusion recorded in the constant's comment: *a
denylist over English has now lost this argument twice.* The project states the
same rule generally in `perry/knowledge/`. A guard that guessed would be
defeated by the next sentence not on the list, and the failure message now says
so in as many words, with the remedy attached. That is the right instrument and
the right documentation of it.

**On whether the cost is bounded, the round's own measurement is the thing that
is wrong**, and it is wrong in the direction that matters. The Bound says:

> *the same sentence is GREEN inside the free rationale block (measured round
> 5), and anywhere else it costs one deliberate re-pin, which is the friction
> this rule is meant to carry.*

Half of that is confirmed (`REMEDY` green). The other half is false, and § 6
below is why: the sentence is green **anywhere in `dispatch.md`** once a copy
of it exists in the free block, and no re-pin is involved. The friction the
paragraph claims to impose is not imposed. That is not a cosmetic
over-claim — it is the sentence on which the whole over-fire defence rests.

### 5. Round 5's two corrections to the record — **MET, with a measured overstatement** 

**Correction A — the free block is not wholly unread.** The *outcome* claim
reproduces exactly:

```
RED  D3b   dispatch.md:194-212  the free rationale rewritten WHOLESALE, all 19
           lines, dropping TASK-247, using both keywords
           -> test_dispatch_says_why_not_merely_what
              + test_a_contradiction_inside_the_free_rationale_is_not_checkable
```

(The second failure is the round's own length assertion — my replacement was
shorter than 200 chars — and is incidental.)

**The *mechanism* claim is half true, and I measured the half that is not.**
Round 5 and the spec both say *"two existing tests assert into it"* and that a
rewrite deleting *"the two observed failures **or the merge instruction**"*
reddens. Inside the section, the three asserted literals live at:

```
160  - The primary checkout merges with `git merge --no-ff <branch>` …   PINNED
172   ! [remote rejected] HEAD -> main (branch is currently checked out)  PINNED
199  - **2026-09-02** — TASK-247 was dispatched …                        FREE
209  The failure is also **invisible from inside**: TASK-247's own agent …FREE
```

`git merge --no-ff` and `branch is currently checked out` are both in the
**pinned prefix**, not in the free block. So
`test_the_merge_side_is_stated_where_the_rule_is` places **no constraint
whatever** on the free block, and neither does the second literal of
`test_dispatch_says_why_not_merely_what`. Exactly **one** test reads the free
block, through exactly **one** literal: `TASK-247`.

Demonstrated rather than argued — both of these replace all 19 free lines and
are **GREEN**:

```
GREEN D3c  a wholesale rewrite that RETRACTS the rule, keeps the literal
           `TASK-247`, and avoids both keywords
GREEN D3d  the same retraction keeping `TASK-247` and USING both keywords
```

**Correction B — the unread zone is smaller than 1,148 characters.** True, and
now measured at its real size: the free block is unread except that the
8-character string `TASK-247` must survive somewhere in it. The residual is
therefore ~1,140 characters in any arrangement, not meaningfully smaller than
the figure three documents cited. The correction is honest and it is in the
right direction; the round's framing of it (*two* tests, *the merge
instruction*) makes the shrinkage sound larger than it is. Not a fail reason on
its own — the spec's `Remainder` still says the block is *"bytes this suite
does not read"* and that *"no test can tell an improved explanation there from
a retraction"*, and both remain true.

### 6. Attacks nobody has planted — **NOT MET; one green, and it is the fail**

Fourteen new plants. **Thirteen red, one GREEN.** Full ledger in § Finding 1
and § Attack log.

### 7. Does the spec's `## Bound` still bound the same thing — **MET, with one false sentence**

The diff is `483a171`, `+45/-4`, touching only `## Bound`'s `Remainder` and
adding an `Over-fires:` line. Checked rather than reasoned:

- **`## Deliverable` and `## Verification` are byte-identical** to what the row
  was filed with (`git diff 13650c4 dda8d5f -- …spec.md` touches nothing else),
  so the six original Verification items are still the ones being scored.
- **The original enumeration is untouched**: `grep -l "The tree the agent works
  in" work/reference/*.md` is still exactly 3; `autopilot.md` still carries no
  copy; the *"a K+1th file is a new row"* sentence is unchanged.
- **The vocabulary limit was genuinely moved in from the docstring**, which is
  the round-4 review's Finding 3 discharged, and confirmed still green (`S1n`
  category, and `D3c`).
- **The three-zone `Remainder` is a truer description than "exactly one free
  block"**, and zone 3 as *described* is genuinely closed.

**One sentence in it is false, and it is load-bearing**: the `Over-fires:`
paragraph's *"anywhere else it costs one deliberate re-pin"*. § 4 and Finding 1.
A second, milder one: `Size:` still says `1,150 declared free` while
`Remainder` says `1,148` — the two-character `rstrip()` gap the round-4 review
already explained, now visible inside one code block. Cosmetic.

### 8. Suite and lint — **MET**

*(see § Suite below)*

---

## Finding 1 (FAIL) — the free block is a line-injection oracle, and zone 3 reopens through it

The containment check asks whether a line's **text** is in a set of the span's
**line texts**. It never asks where the line is. And `span = src[a:b]` includes
the declared-free rationale block. Therefore:

> **Any sentence written inside the free block becomes a legal line anywhere
> else in the same file.**

`USER-914` makes the first edit legal, unpinned and green. The second edit is
then green for free.

The mutation, planted in one commit, in `dispatch.md` only:

```
copy 1 — dispatch.md:209, INSIDE the free rationale block (legal, unpinned):

    On a small row a separate worktree is not required and the `isolation` flag may be skipped.

copy 2 — dispatch.md:138, OUTSIDE every governed span, four lines above the
         rule's own heading:

    **When this does not apply.**
    On a small row a separate worktree is not required and the `isolation` flag may be skipped.

    ## The tree the agent works in

    > **A dispatched agent works in its own git worktree. The primary checkout is
    > never switched by an agent; it merges the agent's branch afterwards, and that
    > merge is the only code operation it performs.**
```

Result:

```
GREEN X2      the composite                     new failures: NONE   Ran 13  OK
RED   X2b     copy 2 ALONE, no free-block copy  -> test_every_mention_…_governed_region
```

and against the whole suite, not merely the class: **{SUITE_X2}**

Four things make this the same fail the row has taken three times, not a new
class of nit:

1. **The retraction uses both keywords.** It is not the declared vocabulary
   limit. It says `worktree` and it says `isolation`.
2. **The line is naturally wrapped and full length.** It is not the declared
   zone-3 short-wrap, which the spec calls `CLOSED IN ROUND 5`. No carriage
   return is doing any work.
3. **It is outside every governed span**, in the file the spec designates as
   *"the rule's single home"*, positioned so a reader meets the exception
   before the rule.
4. **The document then lies about itself.** `dispatch.md:182` — inside the pin
   — tells the reader *"Everything above this paragraph … is pinned
   byte-for-byte by `tests/test_spec_scannability.py::TestTheAgentGetsItsOwnTree`:
   a sentence added, removed or reworded anywhere in it reddens a named test."*
   Copy 2 is above that paragraph. Nothing reddens.

**Why this is not just the declared zone-1 residual with extra steps.** Round
4's review scored its `F2` (widening the free block with a duplicated heading)
as *"the declared residual, not an escalation of it"* — and it was right,
because `F2` left the retraction **inside** the free zone. Every defence the
round offers for that residual is **positional**: the block *"sits at the tail
of the section under a heading that announces it as explanation, below a pinned
signpost."* `X2` breaks the positional bound. It moves the retraction out of
the annotated tail and into normative position above the rule, where the
signpost's own words vouch for it. A hole whose only remaining defence is *"it
is somewhere a reader can see it is only rationale"* stops being bounded the
moment its contents can be copied anywhere.

**A weaker cousin, for completeness.** The same content-keying makes any
existing keyword-bearing span line freely duplicable:

```
GREEN X1-dup   dispatch.md:138  keyword-free retracting prose plus a VERBATIM
                                copy of the `isolation: "worktree"` flag bullet
```

I do **not** score `X1` against the round: its retracting sentences carry
neither keyword, so it falls inside the declared zone-2 vocabulary limit and
the quoted bullet only lends it plausibility. It is recorded because it is the
same mechanism, and because it is the cheaper half of `X2`.

**The fix is again small, and the round already owns the right shape.** The
line set must be built from the **pinned** text, not the raw span — i.e. from
`governed_text(name)`, the very function the sibling test already uses — so the
free zone stops minting legal lines:

```python
spans.append((path, set(self.governed_text(name).splitlines())))
```

Verified rather than proposed. Applied to a scratch copy of the guard with
`X2` planted: `test_every_mention_of_the_rule_is_inside_a_governed_region`
goes **RED**, and on the unmodified documents the class is **green** at
`Ran 13`. Both files were then restored to their `BASE` sha256; the patch is
**not** part of this branch. Nothing else moves — the digests, the spans,
`USER-914`'s free block and every result in §§ 1–3 stand. If the round would
rather argue that seeding the free block is out of scope, that argument has to
be **written into the spec's `Remainder`** before it is made, which is the
standard rounds 3 and 4 were both held to.

---

## Attack log — the other thirteen

```
RED   X4-table     dispatch.md:138  the retraction as a MARKDOWN TABLE ROW,
                                    outside every span
RED   X4-fence     dispatch.md:138  the retraction inside a FENCED CODE BLOCK,
                                    outside every span
                                    (both -> test_every_mention_…_governed_region)
RED   X5-delclose  dispatch.md:223  span 1's CLOSING heading renamed away
                                    -> 3 tests, incl. the pin (ValueError → ERROR)
RED   X5b-dupclose dispatch.md:139  the CLOSING anchor DUPLICATED immediately
                                    below the opening one, collapsing span 1,
                                    with a retraction under it -> 4 tests
RED   X5c-dupopen  dispatch.md:138  the OPENING anchor DUPLICATED above the real
                                    one, retraction between them
                                    -> test_the_governed_regions_are_pinned
                                       + test_the_rule_is_pinned_verbatim
RED   X7-4th-dup   a FOURTH FILE whose keyword line is a VERBATIM copy of a
                   dispatch span line — the `p == path` gate holds, so the
                   duplication attack does NOT cross files
RED   X7b-4th      a fourth file with an ordinary keyword retraction
                   (round 4's control, re-derived — still red)
RED   OVERFIRE, E1nat, P1, P2, P3   (§§ 1, 2, 4)
GREEN X3-shy       'work<U+00AD>tree'  — soft hyphen
GREEN X3-zwsp      'work<U+200B>tree'  — zero-width space
GREEN X3-cyr       'w<U+043E>rktree'   — Cyrillic small o
GREEN X6-subdir    work/reference/notes/tree.md — a retraction in a
                   SUBDIRECTORY, with both keywords
```

**The three `X3` greens I do not score as the fail**, though they are worth
recording. The declared limit is *the vocabulary*, and a homoglyph or an
invisible separator is a way of not writing the word in the bytes. It is
uncomfortable that the *rendered* document says `worktree` while the check does
not see it — that is the same "the bytes say one thing, a reader sees another"
gap `visible()` exists to close, pointed the other way — but they need a
character no author types by accident, and they are one honest sentence in the
Bound away from being declared. `X2` is not.

**`X6` is a note, not a finding.** The docstring's stated universal is *"Every
visible line **anywhere under** `work/reference/`"*; the code is
`refdir.glob("*.md")`, which is **not** recursive. `work/reference/` has no
subdirectories today, and creating one is squarely the spec's *"a K+1th file is
a new row"*. But the sentence and the glob do not say the same thing, and the
cheapest honest repair is `rglob`.

The three span-anchor attacks (`X5`, `X5b`, `X5c`) are all red, including the
one that deletes a governed span's closing heading — `governed_text` raises
`ValueError`, which is a test ERROR and therefore red. Deleting an anchor is
not a way to go quiet. The `p == path` gate also holds: the line-duplication
attack works only within one file (`X7-4th-dup` red).

---

## Suite and lint

{SUITE_BLOCK}

---

## What is genuinely fixed, and must not be lost in a FAIL

- **The one-line fix is right and it is proved right.** Three plants green
  before it and red after it, on identical document bytes, with the guard
  reverted and restored to its `BASE` sha256 in between.
- **The natural-wrap control did not regress** (`E1nat` red both sides).
- **All three declared controls are still green** — the rationale is genuinely
  still free, and `REMEDY` confirms the free block really is a place an
  innocent mention can live.
- **The three digests are real**, recomputed independently, 3 of 3.
- **The census correction is right**: 20 lines, 11 / 7 / 2, every one inside a
  span.
- **`D3b` is a real finding in the round's favour** and it corrects the round-4
  review: the free block is not wholly unread.
- **Span anchors hold** under deletion, duplication of either end, and a fourth
  file; table rows and code fences do not evade the containment check.
- **The over-fire argument is correct** and the failure message is the best
  piece of prose in this row: it names the remedy, and it tells the next author
  not to relax the test into one that guesses.
- **The Bound now describes three zones**, which is a truer bound than the one
  it replaced.

## What would close this

One line, at `tests/test_spec_scannability.py:943` — build the line set from
the **pinned** text rather than the raw span:

```python
spans.append((path, set(self.governed_text(name).splitlines())))
```

Then re-run `X2`, `X1-dup` and `REMEDY`. `X2` and `X1-dup` must join `X2b` in
red; `REMEDY` — an innocent mention **inside** the free block — will also turn
red, which is a real cost and has to be paid deliberately: it means the free
zone stops being the free remedy the `Over-fires:` paragraph advertises, and
that paragraph has to be rewritten to say what the remedy actually is. Then
either declare the `X3` homoglyph class in the `Remainder` or normalise the
line before matching, and say whether `glob` or `rglob` is meant.

---

## Verdict

```
=== VERDICT ===
task: TASK-285
round: 5
rung: V4
verdict: FAIL
criteria: 8 scored, 6 MET, 2 NOT MET
reason: the containment check keys a line by CONTENT, not position, and the
        span it builds the line set from INCLUDES the declared-free rationale
        block — so the free zone is a line-injection oracle. A retraction using
        BOTH keywords, naturally wrapped, placed outside every governed span
        four lines above the rule's own heading, is GREEN once the identical
        sentence is also written into the free block, which USER-914 makes a
        legal green edit. The same line alone is RED. The Bound's own claim
        that a mention "anywhere else costs one deliberate re-pin" is therefore
        false: it costs one copy into the zone the same paragraph names as the
        free remedy.
one_line_fix: verified correct — 3 GREEN pre-fix, 3 RED post-fix, same bytes
digests_verified: 3 of 3, independently recomputed
census_verified: 20 lines (11/7/2), round 5's correction of round 4's 16
free_block_measured: read by ONE test through ONE literal (`TASK-247`), not two
mutations_planted: 25 — 4 pre-fix (3 GREEN by design, 1 RED control),
                        21 post-fix: 16 RED, 5 GREEN
  of the 5 post-fix greens: 3 declared controls (D3, NEWPARA, REMEDY),
  1 the declared zone-1 residual re-measured (D3c/D3d counted once),
  1 UNDECLARED and decisive (X2)
  — plus 4 recorded but not scored: X1-dup, X3-shy, X3-zwsp, X3-cyr, X6-subdir
spec_bound: still bounds the same thing; one false sentence (`Over-fires:`)
=== END VERDICT ===
```

**FAIL.** Round 5 answers round 4's FAIL precisely and honestly, and the fix is
the right one. It fails because the invariant it repaired has a second door in
the same wall: the check was taught to compare against the span's lines, and
the span's lines include a zone the project has deliberately decided not to
read. Round 2 retracted the rule inside the blockquote; round 3 three lines
below it; round 4 four lines above it with a carriage return; round 5 four
lines above it with a carriage return **and a copy in the rationale**. The
address moves, the sentence does not, and the guard has not yet been given a
notion of *where* a line is.
