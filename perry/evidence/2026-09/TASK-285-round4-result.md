# TASK-285 — round 4 result

> **Checkout**: isolated worktree
> `.claude/worktrees/agent-a255a2c971f5e9642`, on
> `coding/task-285-round4-contradiction-guard`, **cut from `main` by ref** at
> `d5eaa2f`. The worktree's own HEAD was an unrelated older commit (`d49964e`,
> an ancestor of `main`), so the round-3 V4 review existed only on `main`; the
> branch was cut from `main` explicitly and `main` was never checked out,
> switched or merged into.
>
> **Base pinned once**: `BASE = d5eaa2fdfbfa25169ef0edc1dbbe18faa1278c15`.
> Every restore in every mutation battery below is
> `git show <pinned-sha>:<single path>` — a sha captured before the battery on
> *this* branch, never `main` and never a floating ref. This is the correction
> the brief carries: a round yesterday restored with `git show main:<path>`
> while `main` advanced, imported newer content into its branch, and
> `git diff main` looked clean. `bin/perry-restore-check` was not used.

Criteria: `perry/evidence/2026-09/TASK-285-round3-v4-review.md`, whose FAIL is
precise, plus `TASK-285-spec.md` including its `## Bound` and `## Out of scope`.

---

## The verdict in one line

Round 3's allowlist was an **enumeration of four remembered places**. Round 4
replaces it with **the complement of one declared free zone**: three contiguous
governed spans, pinned as *span minus its declared rationale block*. There is
now nowhere inside a governed span to insert a sentence that is not pinned,
because the pinned set is what is left over rather than a list somebody
maintained.

All four still-green mutations reproduced first, and all four are now red.

---

## 1. The four still-green mutations, reproduced before anything was touched

Run against `BASE`, unmodified, with the harness described in § 5.

```
BASELINE  Ran 62  failing=none

GREEN N2     dispatch.md:142        retraction RELOCATED three lines below the pinned blockquote
GREEN N2c    delegate.md:153        the same retraction, above the pinned code-work block
GREEN N3     dispatch.md:208        flag-bullet escape clause, the literal 'not optional' KEPT
GREEN N11    dispatch.md:209        shared-cwd correction INVERTED, 'not a licence' KEPT
GREEN N12    git-boundaries.md:17   premise made CONDITIONAL, literals kept
GREEN N12b   git-boundaries.md:17   premise replaced by a BARE POINTER
RED   N2b    git-boundaries.md:15   retraction between the role table and `### Rules`

POST-RESTORE  Ran 62  failing=none      (post-restore == baseline: True)
SUMMARY 7 planted, 1 red, 6 GREEN
```

**All four the review named (N2, N3, N11, N12) reproduce**, as do the two
supporting ones (N2c, N12b). Line numbers are the post-`TASK-339` ones — the
review quotes `dispatch.md:123`/`:124`, which `TASK-339`'s `+85`-line rewrite of
step 4 moved to `:208`/`:209`; the anchor assertion in the harness is what
established that, rather than trust.

### One divergence, reported as a finding rather than smoothed over

**`N2b` did not reproduce green at the insertion point I first chose.** The
review describes it as *"between `git-boundaries.md`'s role table and its
`### Rules`"*. Inserted literally there — immediately *above* the `### Rules`
line — it is **RED**, because round 3's role-table region sliced
`B.index("| Role | Works in |") : B.index("### Rules")`, so its end anchor is
the heading and any text before that heading falls *inside* the pinned slice.

Re-run one line lower, inside `### Rules` and above the premise bullet — the
first byte outside both of round 3's `git-boundaries.md` slices — it is green:

```
GREEN N2b2   git-boundaries.md:17   retraction INSIDE ### Rules, above the premise bullet
```

So the review's finding stands; only its stated coordinate is a line off. That
matters only because it is the kind of detail a round can use to claim a
reviewer was wrong, and it does not survive being checked.

The harness's own anchor guard fired once during this, correctly:

```
ANCHOR MISS work/reference/git-boundaries.md:14
  expected to contain: '| **User** | anywhere |'
  actually: ''
  -> the plant would have no-opped
```

Line 14 is the blank line after the table; the `User` row is 13. Without the
assertion that plant would have inserted into a blank line and reported a false
GREEN.

---

## 2. The shape, and why not a fourth substring window

A substring window asks *"does this literal still appear near here?"*. Every one
of round 2's four survivors keeps the literal and reverses the sense around it,
which is exactly what a window cannot see; that pattern has now lost three
times, and the brief rules it out. But a **fifth digest** would have lost too,
for a different reason: N2 adds text and touches no existing region at all, so
any pin whose coverage is *"these paragraphs"* is defeated by *"a paragraph
beside those paragraphs"*.

So the direction is inverted. `GOVERNED` now declares, per file, **one
contiguous span between two headings** plus **an explicitly delimited list of
free blocks inside it**; the pinned text is `span − free`. The property that
follows is the one that matters: **an insertion anywhere in a governed span,
touching nothing, changes the digest** — there is no seam between regions to
insert into, because there are no longer regions, only a span and a hole in it.

```
dispatch.md   § The tree the agent works in → § `Executor: opencode-subagent`
              86 lines · 5,271 chars span · 4,121 pinned · 1,150 declared free
git-boundaries.md § Git Role Boundaries → § Time Estimation …
              26 lines · 4,269 chars · all pinned, no free block
delegate.md   § Required fields in the rendered prompt → § Role ≠ executor
              39 lines · 3,036 chars · all pinned, no free block
```

Two spans deliberately reach further than round 3's:

- `dispatch.md`'s span runs **through the whole of `§ Executor:
  claude-subagent`**, which is where `:220`/`:221` (the `isolation` flag bullet
  and the shared-cwd correction) live. Ending it at the flag bullet would have
  left the seam an escape bullet inserted *above* the flag bullet slips into —
  planted as `N2d`, and red.
- `delegate.md`'s span **starts at `§ Required fields in the rendered prompt`**,
  not at the code-work block, because `delegate.md:139` also states which tree
  to create, and because the review's own `delegate.md` retraction was placed
  *above* the block.

**Digests were computed by an independently re-implemented `visible()`** with
every anchor re-typed from the rendered document
(`scratchpad/digests285.py`), not imported from the test, so a broken helper
could not reproduce its own breakage in the value that pins it.

### One document edit, in service of the shape

`dispatch.md § The tree the agent works in` was **reordered, not rewritten**:
the `**Why it is a rule and not a preference.**` block (the two dated failures
and the *invisible from inside* paragraph) moved from the middle of the section
to its tail, under a real `### Why it is a rule and not a preference` heading.
Nothing was deleted and no sentence changed meaning. This is what makes pinned
and free **contiguous** — a free zone sandwiched between the rule and the
normative bullets would have put the one unpinnable region three lines below the
rule, which is precisely N2's address.

A new pinned paragraph sits immediately above that heading and tells a reader
where the normative text stops, that everything below it is rationale, that the
guard does not pin it, and that *a sentence there granting an exception is a
defect, not a rule*.

---

## 3. After the change: 11 planted, 11 red

```
BASELINE  Ran 64  failing=none

RED  N2    dispatch.md:142       → test_the_governed_regions_are_pinned
RED  N3    dispatch.md:220       → test_the_governed_regions_are_pinned
RED  N11   dispatch.md:221       → test_the_governed_regions_are_pinned
RED  N12   git-boundaries.md:17  → test_the_governed_regions_are_pinned
RED  N12b  git-boundaries.md:17  → test_the_governed_regions_are_pinned
RED  N2b2  git-boundaries.md:17  → test_the_governed_regions_are_pinned
RED  N2c   delegate.md:153       → test_the_governed_regions_are_pinned
RED  N2d   dispatch.md:220       → test_the_governed_regions_are_pinned
           (escape bullet inserted BEFORE the flag bullet, nothing touched)
RED  N2e   delegate.md:139       → test_the_governed_regions_are_pinned
           (escape bullet in the required-fields list)
RED  N2f   dispatch.md:223       → test_every_mention_of_the_rule_is_inside_a_governed_region
           (retraction OUTSIDE every governed span)
RED  N2g   git-boundaries.md:40  → test_every_mention_of_the_rule_is_inside_a_governed_region
           (retraction in a later section of the same file)

POST-RESTORE  Ran 64  failing=none      (post-restore == baseline: True)
SUMMARY 11 planted, 11 red, 0 GREEN
```

`N2f` and `N2g` are aimed at what round 3 declared as its own limit — *"a fifth
region added later is invisible"*. They are caught by the second new test:
**every visible line under `work/reference/` that says `worktree` or
`isolation` must fall inside a governed span.** Measured on this commit those
two words occur in exactly three files and 16 lines, every one inside a span, so
the invariant is *containment*, not a hedge list: it never asks what a sentence
means, only where a sentence on this topic is allowed to live. Its limit is its
vocabulary, and § 6 states it.

---

## 4. The three pre-existing normative lines

| line | what it says | now covered by |
|---|---|---|
| `dispatch.md:220` | the flag bullet, *"It is not optional"* | inside `dispatch.md`'s governed span, which runs through the whole `§ Executor: claude-subagent`. `N3` and `N2d` red. |
| `dispatch.md:221` | the shared-cwd correction, *"not a licence"* | same span. `N11` red. |
| `git-boundaries.md:17` | the isolation **premise** | the span now starts at `## Git Role Boundaries`, not at the `- **Coding Agent commits its own work.**` bullet that used to be the slice's first byte. Line 17 sits inside it, along with line 5 and every Rules bullet. `N12`, `N12b`, `N2b2` red. |

The `assertIn` windows over those lines are still present. They are no longer
what covers them — they are the readable failure message, and the docstrings now
say so rather than implying coverage.

---

## 5. Method

Every plant is anchored **by line number AND by an assertion on the old text at
that line**, and aborts loudly on a miss (§ 1 shows it aborting). Between plant
and run: `find . -name __pycache__ -prune -exec rm -rf {} +` and `sleep 1.1`, so
a mutation written inside the same second as the previous read cannot be
invisible to an mtime-granular cache. Scoring is by **differencing the failing
test set against baseline**, not by pass/fail, so a pre-existing red cannot be
read as a mutation's kill. Restore is `git show <pinned-sha>:<one path>`, and
each restore is asserted to round-trip the file's sha256 back to its
pre-mutation value; the post-restore failing set is compared to the baseline
failing set at the end of every battery, and matched in all three.

---

## 6. What is NOT checkable, and what holds it

**Checkable, and now checked:** *nothing outside the declared rationale block,
inside a governed span, has changed* — because it cannot change without changing
a digest. And *no text about worktrees or isolation exists anywhere in
`work/reference/` outside those spans.*

**Not checkable:** *a contradiction written inside the free rationale block.*
`USER-914` chose normative pinned and rationale free; the free block is
therefore, by construction, 1,150 characters this suite does not read, and no
assertion can tell an improved explanation there from a retraction. Pinning it
would close the hole and undo the decision — which is not a trade this round is
authorised to make, and the brief forbids it explicitly.

A denylist over that block is not an answer either. It has lost three times, and
this project's own standing rule is that Python never parses document semantics:
English retractions are not eight items long, and the next one is not on the
list either.

So this is written down as a test rather than as a paragraph nobody reads —
`test_a_contradiction_inside_the_free_rationale_is_not_checkable` — which holds
the parts that *are* mechanical: that the free zone is exactly **one** block,
that it is bounded at both ends by pinned anchors, and that the signpost
paragraph is inside the pin and not inside the hole.

**What holds the rest is not a test, and saying otherwise would be the same
false claim round 3 was failed for:**

1. **Position.** The block is at the *tail* of the section, after every
   normative sentence, not three lines below the rule. N2's power came from
   sitting directly under the rule with the rule's authority; that address is
   now pinned.
2. **A heading that announces it.** `### Why it is a rule and not a preference`
   is a `###` sibling of the executor sections. A reader reaching an exception
   there has already read the rule, the flag, and the signpost.
3. **The signpost, which is pinned.** *"Nothing there grants an exception — a
   sentence in it that reads like one is a defect, not a rule."* That does not
   stop the sentence being written; it makes the diff that adds it legible as a
   defect to whoever reads the diff.
4. **The merge.** These files change through a reviewed diff. The residual is
   one paragraph-sized region in one file, named in the spec's `## Bound`, and
   that is a thing a reviewer can be asked to look at. An unbounded "read
   everything carefully" is not.

The honest summary: **the guard holds "the rule is stated and nothing beside it
has changed". It does not hold "nothing in the file contradicts the rule", and
after four rounds nothing mechanical will.** What changed this round is the size
of the region where that is true — from *the whole of three files minus four
paragraphs* to *one declared, headed, signposted block of 1,150 characters.*

---

## 7. Controls

**The rationale really is still free.** Four separate edits inside the free
block, three rewordings and one whole new paragraph, all GREEN:

```
GREEN P1   dispatch.md:194   the rationale's lead sentence, reworded
GREEN P2   dispatch.md:199   the 2026-09-02 observed-failure bullet, reworded
GREEN P3   dispatch.md:209   the 'invisible from inside' paragraph, reworded
GREEN P4   dispatch.md:212   a whole new rationale paragraph, inserted
```

`P4` is the one that matters most: round 3's control only showed rewordings
stayed green, and an *insertion* staying green is what proves the free zone is a
zone rather than a set of pinned-around sentences.

One narrowing, stated because it is a real cost: the paragraph the review used
as its `P2` — *"So a merge outside the primary checkout … Read the hook once per
dispatch"* — is now **pinned**. It ends in an instruction, so it is normative by
the line `USER-914` drew; but the free zone is smaller this round than round 3's
implicit one, and that is the price of the complement shape.

**The properties round 3 established, re-verified rather than assumed** — all
RED:

```
RED  A1   dispatch.md:149        one character inside governed span 1
RED  A2   git-boundaries.md:18   one character inside governed span 2
RED  A3   delegate.md:158        governed span 3 shortened
RED  C1   dispatch.md:141        a SINGLE EXTRA SPACE inside the rule blockquote
                                 → test_the_rule_is_pinned_verbatim (+2 more)
RED  C2   dispatch.md:138        heading renamed 'RENAMED-AWAY'
                                 → test_the_rule_is_pinned_verbatim (+2 more)
RED  C3   dispatch.md:137        an UNCLOSED '<!--' above the section
                                 → 10 of 13 guards red
RED  C4   dispatch.md:145        'This repository is public …'
                                 → test_the_rule_is_generic_not_perry_specific
RED  C4b  git-boundaries.md:5    the same sentence in git-boundaries.md
                                 → test_the_rule_is_generic_not_perry_specific
SUMMARY 8 planted, 8 red, 0 GREEN
```

**The negative control fires in both shipped files, by name.**

---

## 8. Suite and lint

```
$ bash tests/run
0. tree guard — the tree the suite started in is the tree it ends in
  ✓ nothing under …/agent-a255a2c971f5e9642 moved
✓ all green                                   (exit 0)

$ python3 bin/perry-lint --root .
0 error(s), 37 warning(s)

$ python3 tests/parallel -j 4
114 modules · 3253 tests · 217.6s · 4 workers        (green)
```

`tests.test_spec_scannability`: **64 tests, was 62** — the two added are
`test_every_mention_of_the_rule_is_inside_a_governed_region` and
`test_a_contradiction_inside_the_free_rationale_is_not_checkable`;
`test_the_normative_bullets_are_pinned` was replaced in place by
`test_the_governed_regions_are_pinned`. It is the only test module this round
touches, so the suite delta is +2.

**One transient red, attributed rather than waved away.** The first
`tests/parallel` run reported `1 of 114 MODULE(S) red · 1 of 3253 TEST(S)
failed`, in a module of 6 tests. `tests/test_one_primitive` is the only 6-test
module among the brief's known-flaky set, it is `OK` run alone
(`Ran 6 tests … OK`), and the second full `tests/parallel` run and `tests/run`
were both fully green. `test_contract_key_parity` (35 tests) and
`test_host_support` (35) were green throughout. Attributed to TASK-341's known
flake, and re-run alone before attributing, per the brief.

---

## 9. Two claims from round 3 that this document does not repeat

The review found both false as written, and both were repaired in the code
comments they came from, not only here:

1. *"every normative region is pinned … any addition, removal or rewording
   reddens"* — false of round 3, and the `RULE` constant's comment now says
   plainly that pinning bytes protects bytes and not meaning, and that the
   coverage is `GOVERNED` rather than that constant.
2. The implication that round 2's twelve were replayed thirteen-for-thirteen.
   This round replays them at their real coordinates and reports the one
   coordinate that was a line off (§ 1).

The review's two cosmetic notes are also closed: the `NORMATIVE` comment that
said *"three regions"* over four is gone with the constant, and the spec's
`## Bound` now records 13 tests and the complement shape rather than the 7 it
was filed with.

---

## What this round did NOT do

- Did not pin the rationale. `USER-914` stands.
- Did not add a fourth substring window, and did not add a hedge list.
- Did not touch `main`, push, or open a PR. Did not touch
  `schema/state-schema.json`, `claims`, `perry/BOARD.md`, `perry/tasks.jsonl`,
  `perry/journal/` or `.perry/events.jsonl`.
- Did not re-pin anything for `TASK-339`: its rewrite sits at `dispatch.md:9-27`
  and the governed span begins at `:138`. The spans slice by `str.index()` on
  content, so its `+85`-line shift is invisible to them; only the mutation
  harness needed the new line numbers, which is what the anchor assertions
  caught.
