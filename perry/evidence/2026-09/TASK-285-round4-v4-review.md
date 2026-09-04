# TASK-285 — round 4, V4 review

> **Checkout**: isolated worktree `.claude/worktrees/agent-ab278a2c91c8630d8`,
> on `review/task-285-round4-v4`, cut from `main` **by ref** at `13650c4`. The
> worktree's own HEAD was an unrelated older commit (`d49964e`, 379 commits
> behind `main`), so round 4 existed only on `main`; `main` was never checked
> out, switched, merged into or pushed.
>
> **Base pinned once**, per the standing correction: `BASE = git merge-base
> HEAD main = 13650c4d476d1292ed657ed83a4ee332215c3c43`. Every restore in every
> battery is a byte copy from pristine extracts taken from **that sha**, never
> from `main` and never from a floating ref, and each restore is asserted to
> return the file's sha256 to its pre-mutation value. `bin/perry-restore-check`
> was not used.
>
> Every plant is anchored **by line number AND by an assertion on the old text
> at that line**; a miss aborts loudly rather than no-opping. Between plant and
> run: `find . -name __pycache__ -prune -exec rm -rf {} +` and `sleep 1.1`.
> Scoring is by **differencing the failing-test set against baseline**, never by
> pass/fail.

Criteria: `perry/evidence/2026-09/TASK-285-spec.md` (including `## Bound` and
`## Out of scope`), `TASK-285-round3-v4-review.md` (the FAIL this round answers),
and `TASK-285-round4-result.md`.

---

## Verdict in one line

**FAIL.** The inversion is correct and it works: **all twelve of round 2's
greens are now red**, every insertion *inside* a governed span reddens, and the
free zone is genuinely un-widenable into normative text. The round fails on its
**second** line — the containment invariant — which does not hold the property
it states. `test_every_mention_of_the_rule_is_inside_a_governed_region` tests
`line in span`, a **substring** test, not membership in the span's lines. So a
retraction placed outside every governed span, **using the word `worktree`**,
passes as long as one deliberate line break leaves the matching line short
enough to be a substring of the span. The mutation the PMO verified as RED
(`D2` below) goes GREEN with one carriage return inserted mid-sentence.

Planted four lines above `## The tree the agent works in` — in the file this row
designates as the rule's single home — the row's headline deliverable stands
retracted with **the entire 3,253-test suite green**.

This is not the round's declared limit. The declared limit is *"a retraction
that never says `worktree` or `isolation`"*. This retraction says it.

---

## Criteria

### 1. Spec Verification 1 — the rule is present and the executor section names the flag — **MET**

```
$ grep -n "worktree\|isolation" work/reference/dispatch.md | head -4
140:> **A dispatched agent works in its own git worktree. The primary checkout is
149:- The agent gets an isolated worktree and commits on its own branch. …
220:- **Pass `isolation: "worktree"`. It is not optional** — see § The tree …
221:- Sub-agent shares parent cwd, and that is a fact about the *process*, not a
      licence for the *tree*: …
```

A reader who reads only `### \`Executor: claude-subagent\`` learns the flag
(`:220`), and the bare *"Sub-agent shares parent cwd"* the spec named as the
licence is corrected in place rather than deleted (`:221`).
`git-boundaries.md:17` and `delegate.md:158` both reference
`dispatch.md § The tree the agent works in` and neither restates it.

The spec's original enumeration is untouched and still holds:

```
$ grep -l "The tree the agent works in" work/reference/*.md | wc -l
       3
$ grep -c "worktree\|isolation" work/reference/autopilot.md
0
```

### 2. Spec Verification 2 — the guard is mutated and reddens in each of the three files — **MET**

The three digests were **recomputed independently** — `visible()`
re-implemented, every anchor re-typed from the rendered document, not imported
from the test:

```
$ python3 scratchpad/w285r4/digests.py <worktree>
MATCH  dispatch.md § the tree + § Executor: claude-subagent
        span=5271c/86l  pinned=4121c  free=1148c
        first pinned line: '## The tree the agent works in'
        last  pinned line: '- Sub-agent shares parent cwd, and that is a fact about the *process*,'
MATCH  git-boundaries.md § Git Role Boundaries      span=4269c/26l  pinned=4267c
MATCH  delegate.md § required fields + roleless path span=3036c/39l  pinned=3034c

3 of 3 digests match live text
```

Every span is non-empty and begins and ends on normative prose. One character
changed inside each, line-anchored with an assertion on the old text:

```
BASELINE  Ran 13  failing=none
RED  A1  dispatch.md:149        'isolated' -> 'isolatod'
RED  A2  git-boundaries.md:18   one char in the Coding-Agent Rules bullet
RED  A3  delegate.md:157        the code-work bullet shortened
RED  E4  git-boundaries.md:9    the role table's `Works in` cell reversed
         all four -> test_the_governed_regions_are_pinned
POST-RESTORE  Ran 13  failing=none   (post == baseline: True)
```

**The three things the PMO verified, re-derived from scratch rather than
inherited — all three reproduce:**

```
RED   D1  dispatch.md:142  retraction INSIDE the span, 3 lines below the pinned
                           blockquote  -> test_the_governed_regions_are_pinned
RED   D2  git-boundaries.md:40  retraction APPENDED OUTSIDE every governed span
                           -> test_every_mention_of_the_rule_is_inside_a_governed_region
GREEN D3  dispatch.md:194  the free rationale REWRITTEN WHOLESALE  (control)
```

**And all four of round 2's survivors, which round 3 was failed for, are now
red** — each in round 2's *actual* variant, keeping the pinned literal and
reversing the sense:

```
RED  M1  dispatch.md:220       N3:  escape clause appended, 'not optional' KEPT
RED  M2  dispatch.md:221       N11: shared-cwd correction INVERTED, 'not a licence' KEPT
RED  M3  git-boundaries.md:17  N12: premise made CONDITIONAL, literals kept
RED  M5  delegate.md:158       N10: delegate's reference negated
RED  M4  git-boundaries.md:19  V4-item-4: an unconditional push order in new words
         -> test_no_shipped_procedure_orders_an_unconditional_push
SUMMARY 10 planted, 10 red, 0 GREEN
```

That is the round's own claim and it is true: **12 of 12 closed.**

### 3. Spec Verification 3 — `visible()`, including an unclosed `<!--` — **MET**

```
RED  C1   dispatch.md:141  a SINGLE EXTRA SPACE inside the rule blockquote
          -> test_the_rule_is_pinned_verbatim (+2 more)
RED  C2   dispatch.md:138  heading renamed 'RENAMED-AWAY'
          -> test_dispatch_states_the_rule_and_names_the_flag (+2 more)
RED  C3   dispatch.md:137  an UNCLOSED '<!--' above the section
          -> 10 of 13 guards red
RED  C4   dispatch.md:145  'This repository is public, …'
RED  C4b  git-boundaries.md:5  the same sentence
          -> both test_the_rule_is_generic_not_perry_specific
```

### 4. Spec Verification 4 — no unconditional push/PR — **MET**

```
$ grep -rn "push the branch\|open a PR\|opens a pull request" work/reference/*.md
delegate.md:160       - **Push and PR only if the project's hook permits it.** …
git-boundaries.md:19  - **Whether the agent pushes is the project's answer …**
review-constraints.md:39  - Do not commit, push, or open a PR. …
```

Every order carries its condition, and `M4` shows the property is guarded per
clause rather than per literal.

### 5. Spec Verification 5 — suite no redder than baseline — **MET**

```
$ bash tests/run
0. tree guard — ✓ nothing under …/agent-ab278a2c91c8630d8 moved
✓ all green                                             (exit 0)

$ python3 tests/parallel -j 4
114 modules · 3253 tests · 610.0s · 4 workers
✓ all green                                             (exit 0)
```

None of the brief's known flakes fired: `test_contract_key_parity`,
`test_one_primitive`, `test_one_choke_point` and `test_host_support` were all
green on this run.

### 6. Spec Verification 6 — lint at 0 errors — **MET**

```
$ python3 bin/perry-lint --root .
  0 error(s), 37 warning(s)
```

### 7. The containment invariant holds the property it states — **NOT MET**

This is the fail. See § Finding 1.

### 8. The free block's delimiters cannot be widened to swallow normative text — **MET**

See § 2 of the attack log. Four separate attempts on both anchors; the three
that would swallow existing normative text are all red, and the one that is
green adds only text the attacker brought with him — which is the declared
residual with an extra heading, not an escalation of it.

### 9. A retraction phrased without `worktree` or `isolation` — **possible; a DECLARED limit, not a defect of this round** — **MET**

Six planted, one at each end of each of the three spans, all **GREEN**:

```
GREEN S1n  dispatch.md:138        before span 1's opening heading
GREEN S2n  dispatch.md:223        after  span 1's closing heading
GREEN S3n  git-boundaries.md:3    before span 2's opening heading
GREEN S4n  git-boundaries.md:28   after  span 2's closing heading
GREEN S5n  delegate.md:130        before span 3's opening heading
GREEN S6n  delegate.md:168        after  span 3's closing heading
```

Text used: *"On a small row the agent may work directly in the checkout the PMO
is sitting in, and no reviewer should treat that as a defect."*

**This is declared, and declared at the right place** — in the guard's own
docstring at `tests/test_spec_scannability.py:913-918`, in almost the sentence
I planted:

> *"Its limit is the vocabulary — a retraction that never says `worktree` or
> `isolation` (*"sharing the checkout the PMO is sitting in is fine on small
> rows"*) is outside its reach, which is why it is a second line and not the
> first one."*

and again in `TASK-285-round4-result.md § 3` and `§ 6`. A limit stated in the
test, in the result, and before I found it is not a hole with a label on it. I
do not score it against the round. It is **not**, however, in the spec's
`## Bound` — see § Finding 3.

### 10. A fourth file — **the behaviour is declared, but the spec and the guard disagree about what it is** — **MET, with a note**

Created `work/reference/zzz-shared-tree-note.md`, three variants:

```
RED    a fourth file carrying the retraction WITH the vocabulary
       AssertionError: zzz-shared-tree-note.md:3 talks about the isolation rule
       from outside every governed span, where nothing pins it
GREEN  the same retraction phrased WITHOUT the vocabulary          (Ran 13, OK)
RED    the vocabulary present but line-wrapped (§ Finding 1's evasion)
```

So it is **not silence**: a K+1th file that says `worktree` reddens
immediately, and the line-wrap evasion of § Finding 1 does **not** work in a
fourth file, because the check gates on `p == path` before the substring
compare. The guard is stricter than the spec here — the spec says *"A K+1th
file that should carry the rule is a new row, not a re-opening of this one"*,
while the guard makes a fourth reference page that merely mentions worktrees
impossible to add without editing this test. That is the safe direction and I
do not fail it, but the two documents do not say the same thing.

Out of the guard's reach entirely, and correctly so under the spec's K+1 rule:
`AGENTS.md`, `templates/software/AGENTS.md` and `state/diagnosis_TEMPLATE.md`
all mention worktrees and are outside `work/reference/*.md`.

### 11. Does the spec's new `## Bound` still bound the same thing — **YES, MET** (my own judgement, not inherited)

The diff is `7694853`, `+26/-3`, touching only `## Bound`.

**It bounds the same thing.** Four reasons, each checked rather than reasoned:

- **The original enumeration is untouched and still true.** `grep -l "The tree
  the agent works in" work/reference/*.md` is still exactly 3, `autopilot.md`
  still carries no copy, and the *"a K+1th file is a new row"* sentence below
  it is unchanged. The row's scope in files is where it was.
- **`## Deliverable` and `## Verification` are byte-identical.** The six
  verification items I scored above are the ones the row was filed with. A
  round that had moved the bar to fit the build would have had to touch these,
  and it did not — I scored the round against the *original* items and it meets
  five of six.
- **Every number added is accurate on this commit.** `Ran 13` (matches "13
  tests"); 86/26/39 lines and 4,121/1,148 chars all reproduce from my
  independent recompute (the spec says 1,150 free; the two-char gap is the
  final `rstrip()`, and it is a rounding note, not a discrepancy).
- **The `Remainder` records `USER-914`, which predates the round.** Round 3's
  review already scored *"the deliberate non-pinning of rationale"* as MET
  against that decision. Writing it into the Bound is recording an existing
  constraint, not minting a new exemption to fit what was built.

The size update from 7 to 13 is the round-3 review's own second cosmetic note
being closed. That is accounting.

**One reservation, which is not a scope move but is an under-measurement** —
see Finding 3: the `Remainder` says the unread surface is *"exactly one free
block"*. It is not. It is that block, **plus** everything outside the three
spans that avoids two words (§ 9, six greens), **plus** — the part nobody
declared — text that uses those words and is line-wrapped (§ Finding 1, five
greens).

### 12. The declared residual — **an honest limit stated at the right size** — **MET**

```
GREEN RFREE  dispatch.md:212  an explicit retraction written INSIDE the free
                              rationale block
```

Real, and honest:

- It is written as a **test**
  (`test_a_contradiction_inside_the_free_rationale_is_not_checkable`) that holds
  the mechanical parts — one free block, bounded at both ends by pinned anchors,
  the signpost inside the pin and not inside the hole — and says in its
  docstring what it cannot hold.
- The round's formulation is the correct one and I would not improve it: the
  guard holds *"the rule is stated and nothing beside it has changed"*, not
  *"nothing in the file contradicts the rule"*. Round 3 was failed for claiming
  the stronger sentence; this round claims the weaker one and the weaker one is
  true of the spans.
- The size is real, not rhetorical. It went from *three whole files minus four
  paragraphs* to **1,148 characters**, at the **tail** of the section, under a
  heading that announces it as explanation, below a pinned signpost that says a
  sentence there granting an exception is a defect. `D1` proves the old address
  — three lines below the rule — is now pinned.

A hole with a label on it is a hole whose label is the only thing holding it.
This one is bounded, positioned away from the rule's authority, signposted from
inside the pin, and named in the spec. That is a limit, not a label.

---

## Finding 1 (FAIL) — the containment invariant tests `line in span`, and a line break defeats it

`tests/test_spec_scannability.py:934`:

```python
inside = any(p == path and line in span for p, span in spans)
```

`line in span` is a **substring** test against the span's whole text, not
membership in the span's set of lines. Every short line is a substring:

```
'own git worktree'     substring of dispatch span? True
'worktree'             substring of dispatch span? True
'isolation'            substring of dispatch span? True
```

So the retraction is written outside every governed span, **with** the word, and
wrapped so the matching line is short:

```
**When this does not apply.** On a small row the agent need not have its
own git worktree
and may share the primary checkout; that is accepted practice.
```

which renders as one ordinary paragraph. Planted immediately above
`## The tree the agent works in` — four lines above the rule, outside the span,
in the file this row designates as the rule's single home:

```
$ find . -name __pycache__ -prune -exec rm -rf {} +; sleep 1.2
$ python3 -m unittest tests.test_spec_scannability.TestTheAgentGetsItsOwnTree
Ran 13 tests in 0.03s
OK
```

and against the **whole suite**:

```
$ bash tests/run
✓ all green
```

The same evasion works at every address the PMO's own re-derivation covered:

```
GREEN CLINE1  dispatch.md:138       above span 1's opening heading
GREEN CLINE2  git-boundaries.md:40  D2's EXACT address — the same sentence,
                                    RED without the line break, GREEN with it
GREEN CLINE3  delegate.md:168       below span 3's closing heading
GREEN E2      dispatch.md:138       the bare word `worktree` alone on its line
GREEN E3      dispatch.md:138       the bare word `isolation` alone on its line
```

**The control that makes this precise, and keeps it honest.** The same sentence
wrapped *naturally* at ~78 columns, so the matching line is long, is caught:

```
RED   E1  dispatch.md:138  '…that cannot cut its own' / 'worktree may share the
          primary checkout, and no reviewer should treat that as' / 'a defect.'
          -> test_every_mention_of_the_rule_is_inside_a_governed_region
```

So the evasion needs a **deliberate** short wrap, not an accidental one. That is
the right description of it and it does not soften the finding: deliberate is
what a mutation is, this repository's standing rule is *mutate every fix and
distrust green*, and round 3 was failed on a mutation no less deliberate than a
carriage return.

**Why this is a FAIL and not a note.** The round's second test exists precisely
to close round 3's declared limit, and it states a universal:

> *"Every visible line anywhere under `work/reference/` that says `worktree` or
> `isolation` must fall inside a governed span."*

That sentence is false of the landed guard. The pattern is the one this row has
now been failed for twice: **a stated universal that the implementation does not
deliver, found by planting the mutation the round did not plant.** Round 3's
decisive N2 sat three lines *below* the rule and is genuinely closed; the same
retraction four lines *above* it, with one line break, is green — the defeat
moved from one side of the heading to the other.

**The fix is one line**, and the round already owns the right shape:

```python
inside = any(p == path and line in span.splitlines()
             for p, span in spans)
```

**Verified rather than proposed.** Applied to a scratch copy of the guard, with
`CLINE1` planted:

```
$ python3 -m unittest tests.test_spec_scannability.TestTheAgentGetsItsOwnTree
  own git worktree
Ran 13 tests   FAILED (failures=1)
$ # …and with the mutation restored, on the unmodified documents:
Ran 13 tests   OK
```

So the change catches the evasion and does not disturb the landed text. Both
files were then restored to their `BASE` sha256; the patch is **not** part of
this branch. Nothing else in the class is affected — the digests, the spans and
`USER-914`'s free block are untouched.

## Finding 2 — the free block can be widened, but only into space the widener brought

The brief asked whether the free block's anchors can be moved to swallow a
normative sentence. **They cannot.** Four attempts:

```
RED   F1  dispatch.md:142  the free-block OPENING anchor duplicated right below
          the rule, trying to swallow the whole normative middle
          -> test_the_governed_regions_are_pinned
             + test_a_contradiction_inside_the_free_rationale_is_not_checkable
RED   F5  dispatch.md:182  the OPENING anchor moved above the SIGNPOST paragraph
          -> same two
RED   F3  dispatch.md:214  the CLOSING anchor renamed away
          -> 4 tests, incl. test_dispatch_says_why_not_merely_what
RED   F4  dispatch.md:212  the CLOSING anchor duplicated early, shrinking the
          free zone -> test_the_governed_regions_are_pinned
GREEN F2  dispatch.md:192  the OPENING anchor duplicated IMMEDIATELY above the
          real one, with a retraction between the two headings
```

`F2` is green for a structural reason worth writing down: the pinned text is
`span[0:i] + span[j:]`, and inserting a duplicate `### Why it is a rule and not
a preference\n` immediately above the real one leaves `span[0:i]` byte-identical
— the prefix ends with the same heading either way. Anything the attacker puts
*after* his duplicate heading falls in the widened hole.

But he cannot pull existing normative text into it: doing so requires moving `i`
earlier past text that is currently in the prefix, which changes the prefix and
therefore the digest (`F1`, `F5`). So `F2` buys exactly what `RFREE` already
buys — a retraction in the free zone — with a duplicated heading as the price.
It is the declared residual, not an escalation of it. Two second-order notes,
neither a fail reason:

- `test_a_contradiction_inside_the_free_rationale_is_not_checkable` asserts
  `len(spec["free"]) == 1`. That counts the **declaration**, not the document;
  under `F2` the document has two headings and one hole, and the assertion still
  passes. It is holding what it says it holds.
- `F2`'s hole opens at the *top* of the rationale zone, immediately under the
  signpost, which is the most authoritative position inside the free block. The
  round's defence 1 (*"position — the block is at the tail, not three lines
  below the rule"*) is still true of the section; it is the weakest of the four
  defences and `F2` is why.

## Finding 3 — the `Remainder` in the spec's `## Bound` is under-measured

Not a scope move (§ 11) and not a fail reason, but it is the sentence that let
the round believe the second line was tighter than it is:

> `Remainder:   exactly one free block, at the tail of dispatch.md's section …`

Measured on this commit, the surface this suite does not read is **three**
zones, not one:

1. the 1,148-character free block — declared, in the spec and in a test;
2. everything outside the three spans that avoids the two words — declared in
   the guard's docstring and the result document, **not** in the spec's Bound;
3. text that *uses* the two words, outside the spans, line-wrapped short —
   declared nowhere, and Finding 1.

A related accounting slip, cosmetic: `TASK-285-round4-result.md § 3` says the
two words *"occur in exactly three files and 16 lines"*. They occur in three
files and **20** lines (`dispatch.md` 11, `git-boundaries.md` 7,
`delegate.md` 2). Every one is inside a span, so the invariant's premise holds;
the count does not.

---

## What is genuinely fixed, and must not be lost in a FAIL

- **The inversion is the right instrument and it works.** All 12 of round 2's
  greens are red. Every insertion inside a governed span reddens, including the
  three the last review found (`M1`, `M2`, `M3`) and the decisive `D1`.
- **The three digests are real** — recomputed independently, 3 of 3, every span
  beginning and ending on normative prose.
- **Both span ends are guarded for naturally-written text**, in all three files:
  `S1`–`S6` and `E1` all red.
- **The free zone cannot be widened into normative text** (`F1`, `F3`, `F4`,
  `F5`), and the rationale is genuinely still free (`D3`, `RFREE`, `F2`).
- **A fourth file that says `worktree` reddens**, and the line-wrap evasion does
  not reach it.
- **The document edit is a reorder, not a rewrite**, and it does what it claims:
  `D1` proves N2's old address is now pinned.
- **The spec's Bound is honest accounting**, its numbers reproduce, and
  Deliverable and Verification were left alone.
- Suite fully green (3,253 tests), lint 0 errors, tree guard clean.

## What would close this

One line, at `tests/test_spec_scannability.py:934`: compare against
`set(span.splitlines())` instead of the span's text. Then re-run `CLINE1`–`3`,
`E1`–`E3` and `D2` and show the first five join `E1` and `D2` in red. Nothing
else in the round needs to move; the digests, the spans, the free zone and
`USER-914` all stand. If the round would rather argue that a deliberately
wrapped line is out of scope, that argument has to be **written into the spec's
`Remainder`** before it is made — which is the same standard round 3 was held
to for the limit it declared.

---

## Verdict

```
=== VERDICT ===
task: TASK-285
round: 4
rung: V4
verdict: FAIL
criteria: 12 scored, 11 MET, 1 NOT MET
reason: the containment invariant tests `line in span` (substring), not
        membership in the span's lines, so a retraction that USES the word
        `worktree`, placed outside every governed span, is green whenever one
        deliberate line break leaves the matching line short — the exact
        mutation the PMO verified as RED (D2) flips to GREEN with a carriage
        return, with the whole 3,253-test suite green
digests_verified: 3 of 3, independently recomputed
round_2_survivors: 4 of 4 now RED (12 of 12 closed)
mutations_planted: 44 — 29 red, 15 GREEN
  of the 15: 3 declared controls (rationale free), 7 the declared vocabulary
  limit, 5 UNDECLARED (CLINE1-3, E2, E3)
span_boundary_attacks: 12, both ends of all 3 spans — 6 red, 6 green (declared)
free_block_delimiter_attacks: 5 — 4 red, 1 green (the declared residual)
fourth_file: reddens with the vocabulary, silent without it — declared
spec_bound: still bounds the same thing; Remainder under-measured
=== END VERDICT ===
```

**FAIL.** Round 4 answers round 3's FAIL completely and correctly: the
complement shape is the right instrument, and inside a governed span there is
genuinely nowhere left to stand. It fails on the invariant it added to cover
what the spans do not — a check whose stated property is *"every line that says
`worktree` is inside a span"* and whose implementation is *"every line that says
`worktree` is a substring of a span"*. One carriage return is the whole
distance between those two sentences, and the row's headline rule can be
retracted across it with every test green.
