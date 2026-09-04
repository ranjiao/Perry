# TASK-285 — round 3, V4 review

> **Checkout**: isolated worktree `.claude/worktrees/agent-a8803d8a359b0f41c`,
> on `review/task-285-v4-r3`, cut from **`main` at `cc3684a`**. The worktree's
> own HEAD was an unrelated branch (`d49964e`); `main` is checked out by the
> primary checkout and I did not switch it — the branch was cut from `main`
> by ref, which is the rule this very row lands.
>
> **All destructive work was done on `git archive main` extracts** under
> `scratchpad/w285r3` and `scratchpad/w285d`, verified byte-identical to
> `main` by sha256 on all four files before any mutation. The project under
> review was never written to except for this document.
>
> `bin/perry-restore-check` was **not** used, per the brief.

Criteria: `perry/evidence/2026-09/TASK-285-spec.md`, including its `## Bound`
and `## Out of scope`, plus the round-3 claims in `TASK-285-result.md`.

---

## Verdict in one line

**FAIL.** The allowlist is the right instrument and it is drawn too small.
**Four of round 2's twelve green mutations are still green** — including a
retraction of the row's headline deliverable placed three lines below the
now-byte-pinned blockquote, in the file this row designates as the rule's
single home, with all eleven guards reporting `OK`. Round 2's decisive finding
was a retraction the guard could not see; pinning the blockquote to exact bytes
did not remove that retraction, it moved it one line down.

Every criterion the brief listed is individually MET — the four digests are
real, each pinned region reddens on a one-character change, the negative
control fires, the rationale really is unpinned, the suite is green and lint is
at 0 errors, and there is no collision with TASK-339. The FAIL is on the round's
own central claim: *"every normative region is pinned … any addition, removal
or rewording reddens"*. Three normative lines that already exist are not
pinned, and additions inside the same section are not seen at all.

---

## 1. The rule is present, and the other two files agree with it — **MET**

`work/reference/dispatch.md:53-57` carries the section and the rule blockquote:

```
$ grep -n "worktree\|isolation" work/reference/dispatch.md | head
55:> **A dispatched agent works in its own git worktree. The primary checkout is
64:isolation instruction is an instruction to run `git checkout -b` *in the shared
84:- The agent gets an isolated worktree and commits on its own branch. **Whether
99:**The merge cannot be delegated into the worktree**, and this was measured
123:- **Pass `isolation: "worktree"`. It is not optional** — see § The tree ...
124:- Sub-agent shares parent cwd, and that is a fact about the *process*, not a
      licence for the *tree*: ...
```

A reader who reads only the executor section learns the flag to pass
(`dispatch.md:123`), and the bare *"Sub-agent shares parent cwd"* that the spec
identified as the licence is corrected in place rather than deleted
(`dispatch.md:124`). Spec Verification item 1 holds.

`git-boundaries.md:17` states it as the premise its role table depends on and
points at `dispatch.md § The tree the agent works in` rather than restating it;
the role table gained a `Works in` column (`git-boundaries.md:8-14`).
`delegate.md:158` states it for the paste-back path and references the same
section. **Neither contradicts the rule**, and neither carries a second
authoritative copy.

Spec Verification item 4 (no file in `work/reference/` still orders an
unconditional push or PR as the default path) holds on inspection:
`git-boundaries.md:19` and `delegate.md:160` both condition on
`.perry/hook.md § High-stakes operations`.

## 2. The four sha256 pins match the text they claim to pin — **MET, 4 of 4**

Recomputed independently. `visible()` was **re-implemented** in the checking
script rather than imported, and the region boundaries re-typed, so a broken
helper could not reproduce its own breakage:

```
$ python3 scratchpad/w285r3/digests.py <worktree>
MATCH  dispatch.md § what each side does      chars=967  lines=16
MATCH  git-boundaries.md § Rules              chars=1269 lines=3
MATCH  git-boundaries.md § role table         chars=942  lines=7
MATCH  delegate.md § code-work block          chars=1070 lines=4

4 of 4 digests match live text
```

Every region is non-empty, resolves to live prose, and its first and last lines
are normative text — not a pin over nothing. This is a real improvement on the
two previous designs and it should be said plainly.

## 3. Mutating each pinned region reddens a named test — **MET**

One character changed inside each of the four regions, each anchored by line
number **and** an assertion on the old text at that line:

```
RED  A1  region 1 dispatch.md:84  'isolated' -> 'isolatod'
RED  A2  region 2 git-boundaries.md:18  one char in the Rules bullet
RED  A3  region 3 git-boundaries.md:9   one char in a role-table cell
RED  A4  region 4 delegate.md:158       one char in the reference
         all four reddened test_the_normative_bullets_are_pinned  (Ran 11)
```

Plus, on the rule blockquote itself:

```
RED  C1  a SINGLE EXTRA SPACE inside the rule   -> test_the_rule_is_pinned_verbatim
RED  C2  heading renamed 'RENAMED-AWAY'         -> +test_dispatch_states_the_rule...
RED  C3  section commented out, UNCLOSED '<!--' -> 8 of 11 tests red
```

`visible()` does strip an unclosed comment (spec Verification item 3 holds).
Baseline GREEN (Ran 11) and post-restore GREEN (Ran 11) on every battery; all
three files md5-identical to the pre-mutation snapshot afterwards.

## 4. The negative control (generic, not Perry-specific) — **MET**

```
RED  C4   'This repository is public, ...' into dispatch.md
RED  C4b  the same sentence into git-boundaries.md
          both reddened test_the_rule_is_generic_not_perry_specific  (Ran 11)
```

The assertion exists, it is a NOT-in, and it fires in both shipped files when
project-specific text is reintroduced.

## 5. The deliberate non-pinning of rationale — **MET (control passes)**

Three separate rewrites of explanatory prose, none touching the rule block or
any pinned region, all GREEN — so the round did implement the line
`USER-914` chose, rather than pinning everything and calling it an allowlist:

```
GREEN  P1  the 2026-09-02 observed-failure bullet reworded
GREEN  P2  the local-merge argument's prose lead-in reworded
GREEN  P3  the 'invisible from inside' paragraph reworded
```

## 6. Suite and lint — **MET**

```
$ python3 bin/perry-lint --root .
0 error(s), 37 warning(s)

$ bash tests/run
0. tree guard — the tree the suite started in is the tree it ends in
✓ nothing under …/agent-a8803d8a359b0f41c moved
✓ all green
(exit 0)
```

Fully green, tree guard clean. Note for the record: the two known
`test_contract_key_parity` anti-vacuity controls (TASK-335, the 4-hour idle
threshold at `bin/perry-task:6303`) were **not** red on this run — the clock
was on their side. Spec Verification items 5 and 6 hold.

## 7. The live conflict with TASK-339 — **no collision**

`TASK-339` (`coding/task-339-remove-the-scanner`, head `b855e47`) rewrites
`dispatch.md` step 4 — `@@ -9,19 +9,104 @@`, +94/-8 — replacing the escalation
scanner with a written judgement procedure. That hunk sits at lines 9-27;
TASK-285's pinned material begins at line 53. The two do not overlap, and the
guard slices by `str.index()` on content rather than by line number, so the
+85-line shift is invisible to it.

Tested rather than reasoned: TASK-285's guard, taken from `main`, run against
TASK-339's `dispatch.md`:

```
$ cp dispatch-339.md w285x/work/reference/dispatch.md
$ python3 -m unittest tests.test_spec_scannability.TestTheAgentGetsItsOwnTree
Ran 11 tests in 0.054s
OK
```

All four TASK-285 anchors survive TASK-339's rewrite intact
(`## The tree the agent works in`, `**What each side does.**`,
`**The merge cannot be delegated`, `Read the agent's RESULT block. Required
fields:` — 1 occurrence each). **No re-pinning will be required when TASK-339
lands.** This is the friction `USER-914` accepted not being charged: worth
recording before the merge rather than after.

---

## Finding 1 (FAIL) — four of round 2's twelve greens are still green

The question this round exists to answer is not "does an allowlist work" but
"is the failure mode that produced twelve greens closed". Round 2's twelve were
replayed. **Eight are now RED. Four are still GREEN**, and one of them is the
decisive category with the sentence moved down by one line.

```
round 2's finding          now
  N1   retraction INSIDE the blockquote        RED   (byte-pinned — genuinely fixed)
  N1b  "it binds nobody" inside the blockquote RED
  N2b  "what each side does" inverted          RED
  N4   publishes … raises a pull request       RED
  N4b  the same rewording in delegate.md       RED
  N5   order rescued by "hook" in its clause   RED
  N6   table row with no leading pipe          RED
  N10  delegate's reference negated            RED
  ------------------------------------------------------------------
  N2   retraction one line BELOW the block     GREEN  ← still open
  N3   flag bullet escape clause               GREEN  ← still open
  N11  shared-cwd correction reversed          GREEN  ← still open
  N12  boundaries premise made conditional     GREEN  ← still open
```

Each replay is line-anchored with an assertion on the old text at that line;
baseline GREEN (Ran 11) and post-restore GREEN (Ran 11), all three files
md5-identical to the pre-mutation snapshot afterwards.

### 1.1 The decisive one — the retraction just moves one line down

Round 2 killed the guard with a retraction inside the rule's blockquote. Pinning
the blockquote to exact bytes closes that. It does not close the retraction; it
relocates it. **Nothing existing is touched** — this is a pure insertion into
`dispatch.md § The tree the agent works in`, immediately after the pinned block:

```
> **A dispatched agent works in its own git worktree. The primary checkout is
> never switched by an agent; it merges the agent's branch afterwards, and that
> merge is the only code operation it performs.**

**When the rule does not apply.** On small rows, and on hosts with no
worktree support, sharing the primary checkout is the accepted practice and
no reviewer should treat it as a defect.

This is the rule; `git-boundaries.md` and `delegate.md` reference it and do not
restate it.
```

```
$ find . -name __pycache__ -exec rm -rf {} +; sleep 1.1
$ python3 -m unittest tests.test_spec_scannability.TestTheAgentGetsItsOwnTree
Ran 11 tests in 0.011s
OK
```

The row's headline deliverable is retracted, in the file the row designates as
its single home, three lines below the rule — and the guard reports OK. The
same insertion works in the other two files: between `git-boundaries.md`'s role
table and its `### Rules` (*"Worktree isolation is advisory"*), and above
`delegate.md`'s pinned code-work block (*"Worktree isolation is optional for
pasted prompts"*). Both GREEN.

### 1.2 Three normative lines that already exist are not pinned

N3, N11 and N12 are **not** insertions and are not covered by the round's
declared limit. They are edits to existing normative text — text the spec's own
`## Deliverable` names — that the allowlist does not reach, and whose tests are
still `assertIn` over a substring window, which is the exact pattern that lost
twice:

| line | what it says | the test | window |
|---|---|---|---|
| `dispatch.md:123` | the flag bullet, *"It is not optional"* | `test_the_rule_is_mandatory_and_not_merely_available` | `assertIn("not optional", src[i:][:200])` |
| `dispatch.md:124` | the shared-cwd correction, *"not a licence"* | `test_the_shared_cwd_line_no_longer_reads_as_a_licence` | `assertIn("not a licence", src[i:i+400])` |
| `git-boundaries.md:17` | the isolation **premise** | `test_the_other_two_files_reference_the_rule` | `assertIn("own worktree")` + `assertIn("The tree the agent works in")` |

Keep the literal, append the escape:

```
- **Pass `isolation: "worktree"`. It is not optional** for rows the PMO judges
  large; on small rows the shared parent tree is fine — see § The tree …

- Sub-agent shares parent cwd. Calling that "not a licence" for the tree
  overstated it: in practice sharing is fine, and `isolation` is there for the
  rows that need it. …
```

Both GREEN. `git-boundaries.md:17` is sharper still, because **the pin's own
boundary excludes it**. `normative_regions()` starts the `§ Rules` slice at
`- **Coding Agent commits its own work.**`, which is line 18. Line 17 — the one
sentence in that file that states TASK-285's rule — sits immediately above the
pin's first byte. Replacing it with a bare pointer (*"See `dispatch.md § The
tree the agent works in` for the project's own worktree conventions"*) is
GREEN, because `own worktree` still appears four times in the role table above.
That is round 1's A6b defect surviving into round 3 by a different route.

## Finding 2 — two claims in the result document are not true as written

Both are about coverage, and both would let the next reader believe the
category is closed.

1. > *"The rule block and every normative region are pinned to exact bytes. …
   > Any addition, removal or rewording reddens, including ones nobody
   > predicted."*

   **"every normative region" is false.** The flag bullet, the shared-cwd
   correction and `git-boundaries.md`'s premise are normative and unpinned, and
   *"any addition … reddens"* is false for any addition outside the four
   regions — which is where the retraction in 1.1 lives.

2. > *"Round 1's, round 2's, and new ones aimed at the pin itself — thirteen
   > planted, thirteen red"*

   The thirteen do go red — I reproduced the extra-space, renamed-heading,
   unclosed-`<!--`, blockquote-retraction and two-synonym rows and all were RED.
   But the sentence reads as *round 2's set replayed*, and four of round 2's
   twelve were not replayed and are not red. The table's rows *"shared-cwd
   correction inverted"* and *"boundaries premise made unconditional"* name
   categories round 2 recorded as GREEN while testing only the trivial variant
   (delete the pinned literal), not round 2's own (keep the literal, reverse the
   sense). Both variants were run here; see § 3 of the battery output.

## What is genuinely fixed, and should not be lost in a FAIL

- **The four digests are real.** 4 of 4 recomputed against live text from an
  independently re-implemented `visible()`; every region non-empty and
  normative. A one-character change in any of them reddens a named test.
- **The blockquote pin closes round 2's decisive N1 and N1b**, and the
  two-synonym walk-past (N4/N4b) and the clause-rescue holes (N5/N6) with it.
  Eight of twelve is real progress, not a rewrite.
- **The rationale really is unpinned.** Three independent prose rewrites stayed
  green, so the line `USER-914` drew — normative pinned, explanatory free — is
  implemented rather than merely asserted.
- **The negative control fires** in both shipped files.
- **No collision with TASK-339.** Nothing to re-pin when it lands.
- The spec's `## Bound` holds: `grep -l "The tree the agent works in"
  work/reference/*.md` is still exactly 3, and `autopilot.md` still carries no
  copy.

## Two cosmetic notes, not fail reasons

- The `NORMATIVE` comment at `tests/test_spec_scannability.py:670` says *"this
  is three regions"*; there are four.
- The spec's `## Bound` records the guard at **7 tests / 9 mutations**; it is
  now 11 tests. Growing a guard is right, but the bound was the thing that was
  supposed to be countable, and it was not updated.

## What would close this

Not a bigger denylist — that argument has now been lost three times. The
allowlist is the right instrument; it is drawn too small. Either extend the
pinned set to the three normative lines it currently misses
(`dispatch.md:123`, `dispatch.md:124`, `git-boundaries.md:17` — note the last
needs only moving the existing slice's start up by one bullet), or pin the
whole `## The tree the agent works in` section minus an explicitly delimited
rationale block, so that *the complement of the pin is what is declared free*
rather than the pin being an enumeration of remembered places.
