# TASK-285 — result

> Rung of this document: **V3** — every claim below is a run, reproduced here.
> Written by the PMO lane, which is also the executor. That is why the row goes
> to `review` and not to `done`: the fix and its guard were written by the same
> session, which is exactly what V4 exists to catch.

## What the row was

`work/reference/dispatch.md` told a dispatched agent to work on a feature branch
and said **nothing** about tree isolation. Measured on `5720730` before the
change:

```
$ grep -in "worktree\|isolation" work/reference/dispatch.md
(no output)
```

What it did say, at `dispatch.md:55`, was *"Sub-agent shares parent cwd"* —
stated as a neutral fact about the executor, and read as a licence for the tree.

## The change

One rule, written once in `dispatch.md § The tree the agent works in`, referenced
from `git-boundaries.md` and `delegate.md` and restated in neither:

> A dispatched agent works in its own git worktree. The primary checkout is
> never switched by an agent; it merges the agent's branch afterwards, and that
> merge is the only code operation it performs.

Three files, plus the guard:

| File | What changed |
|---|---|
| `work/reference/dispatch.md` | The `§ The tree the agent works in` section — the rule, the two observed failures, `isolation: "worktree"` named as the flag to pass, the merge half, and the measured reason the merge cannot happen inside the worktree. `Sub-agent shares parent cwd` corrected in place rather than deleted. |
| `work/reference/git-boundaries.md` | The role table gains a **Works in** column; the Rules list gains the isolation premise and stops ordering an unconditional push and PR. |
| `work/reference/delegate.md` | The roleless code-work block and the `Git expectation` required field, same two corrections. |
| `tests/test_spec_scannability.py` | `TestTheAgentGetsItsOwnTree`, 7 tests, using the file's existing `visible()` so a commented-out rule reddens rather than passes. |
| `tests/test_role_cards.py` | One pinned string updated — see § The test I broke. |

## The scope widened once, on a user decision

Writing the rule surfaced a second contradiction in the same files, live rather
than cosmetic. `git-boundaries.md:17` said *"Coding Agent pushes a feature branch
and opens a PR"* and `delegate.md:159` said *"**Push the branch and open a PR**"*
— flatly, with no condition. `git push` and `origin` are in the default
`.perry/hook.md § High-stakes operations` list Perry's own bootstrap writes, so
**following the shipped procedure trips the gate the same procedure arms.**

Put to the user 2026-09-03 as three options — PR flow with the V4 reviewer
merging, PR flow with the user merging, or keeping the local merge. **Answer:
keep the local merge.**

The reason the merge cannot be delegated into the worktree was measured on a
throwaway repository rather than asserted:

```
$ git checkout main                      # from the second worktree
fatal: 'main' is already used by worktree '…/wtprobe'
$ git push ../wtprobe HEAD:main
 ! [remote rejected] HEAD -> main (branch is currently checked out)
```

Both routes refused. A merge outside the primary checkout is therefore a merge
on the remote — a PR — which needs the hook to permit a push. So a project has
exactly two available shapes and its hook already chooses between them; the
shipped files now say that instead of assuming one.

**The shipped files stay generic.** The first draft of this change wrote *"this
repository is public"* into `dispatch.md` and `git-boundaries.md`. Those files
ship to every project, where the sentence would be false. Corrected before
commit, and `test_the_rule_is_generic_not_perry_specific` is the NOT-in that
holds it — the assertion exists because the mistake was made.

## Verification

### The guard is mutated, and two mutations came back green

Nine mutations, each anchored by an `assert old in src` so a non-matching anchor
raises instead of silently reporting OK, each restored by writing back bytes
snapshotted **before** any mutation and checked with `md5` against that snapshot
— not against bytes the mutation itself wrote. `__pycache__` cleared and 1.1 s
waited before every run.

```
baseline: GREEN

  GREEN  M1 dispatch.md: the section heading is gone
  RED    M2 dispatch.md: the flag name is wrong
  RED    M3 dispatch.md: section commented out with an UNCLOSED <!--
  RED    M4 dispatch.md: the shared-cwd correction is dropped
  RED    M5 dispatch.md: the merge half is unnamed
  GREEN  M6 git-boundaries.md: the rule reference is gone
  RED    M7 delegate.md: the rule reference is gone
  RED    M8 delegate.md: the unconditional push order comes back
  RED    M9 dispatch.md: a project-specific sentence returns to a shipped file

GREEN MUTATIONS (each one is a finding): [1, 6]
post-restore: GREEN
```

**M1 was a real guard defect.** `assertIn("## The tree the agent works in", src)`
is a substring test, and `## The tree the agent works in RENAMED-AWAY` still
contains it — so the guard could not see a section that no longer existed under
that name. Fixed by pinning the heading to a whole line:
`assertRegex(src, r"(?m)^## The tree the agent works in$")`.

**M6 was my harness's defect, not the guard's.** The mutation used
`str.replace(old, new, 1)` and `git-boundaries.md` carries `own worktree` four
times, so it removed one of four and the property never left the file. Re-run
replacing all four:

```
  RED    M1-retry heading renamed (was GREEN before the fix)  (occurrences replaced: 1)
  RED    M6-retry ALL occurrences removed from git-boundaries.md  (occurrences replaced: 4)

still green: none
post-restore: GREEN
```

Recording the distinction rather than reporting "9 of 9 red" after the fact: one
of the two greens was a bug in the thing under test and one was a bug in the
instrument, and they are not the same finding.

### The test I broke, and why it was the test that was wrong

`test_role_cards.TestGoal7NoRolesChangesNothing.test_delegate_still_documents_the_path_for_a_project_with_no_cards`
pinned the literal string `Do NOT merge own PR`. The change makes the PR
conditional on the hook, so on a project where pushing is escalated there is no
PR to not-merge and the sentence asserted something that could not happen.

The requirement the test protects — *the no-self-merge rule survives the roleless
path* — is unchanged and still pinned; it now pins `Do NOT merge own work`,
which is the requirement rather than the noun. The reason is in a comment at the
assertion, so the next author does not read it as drift.

### Suite and lint

```
$ python3 tests/parallel -j 4
110 modules · 3094 tests · 147.5s · 4 workers
✓ all green

$ python3 bin/perry-lint --root .
0 error(s)
```

Before the fix to `test_role_cards.py` the same suite was `1 of 110 modules red ·
1 of 3094 tests failed`, and that one red is the test named above. No other
module moved.

## What this row did not do

- **The code-fence hole.** `visible()` strips comments, not fenced blocks, so a
  rule moved inside a fence is invisible to a reader while the guard stays
  green. That is `TASK-318`, already filed, and fixing it here would fix one
  guard rather than the class.
- **Nothing was pushed**, no hook entry was changed, and the 99 unpushed commits
  are still unpushed. The local-merge answer is most of why.
- **No existing branch was re-isolated.** The rule governs the next dispatch.

## The first dispatch under the new rule

`TASK-323` was delegated before this landed and ran as a paste-back. The next
automated dispatch is the first test of whether the rule as written is
followable — if an agent reads `§ The tree the agent works in` and still shares
the tree, the section is prose rather than a procedure and this row is not done.

---

# Rounds 1 and 2 — appended 2026-09-03

**This document reported the pre-round-1 state until now**, which round 2
noticed and recorded as an observation rather than a fail reason. It was right
to: an exhibit that stops tracking the work is how a reader ends up trusting a
number nobody re-measured.

## Round 1 — FAIL, two findings, both created by this change

1. **Seven green mutations.** Softening the rule to *"A dispatched agent MAY
   work in its own git worktree where convenient"* left all seven guards green.
   Every assertion pinned the presence of words; none pinned modality.
2. **`dispatch.md` still required `PR URL:`** with `"n/a — direct push"` as its
   only alternative, so on a project whose hook escalates a push a compliant
   agent had no truthful value for a field step 4 gates the `review` transition
   on. Three files, three answers.

Fixed at `db12fa4`: a modality test rejecting eight hedges, a clause-level
property check for push orders, `Branch:` made the unconditional RESULT field.

## Round 2 — FAIL, twelve green mutations, and the fix was the wrong shape

The decisive one kept the pinned imperative **verbatim**, used none of the
eight hedges, and added one sentence inside the rule's own blockquote:

> Where a worktree is impractical, sharing the primary checkout instead is an
> acceptable alternative.

`Ran 9 tests / OK`. The headline deliverable stood retracted and the test
written for exactly that defect stayed green. Two synonyms — `publishes its
feature branch … raises a pull request` — walked past the "property" check in
the role table. The reviewer's summary is the finding:

> **A denylist over English has now lost this argument twice.**

That is correct, and it is a design error rather than a regex error. An English
retraction is not eight items long, and the next one would not have been on the
list either.

## What landed instead — an allowlist

**The rule block and every normative region are pinned to exact bytes.** The
blockquote is compared literally; four normative regions — `dispatch.md`'s
"what each side does", `git-boundaries.md`'s role table and Rules list, and
`delegate.md`'s code-work block — are pinned by `sha256`. Any addition,
removal or rewording reddens, including ones nobody predicted.

**Rationale is deliberately not pinned.** The observed failures, the measured
`git` output and the local-merge argument can all be improved without touching
a test. What cannot change silently is what an agent is *told to do*. That line
— normative pinned, explanatory free — is why this is four regions and not the
whole 62-line section.

Same move this project has now chosen three times: `USER-904` took one
`header_index` over a smarter detector, `USER-906` took one invariant over a
fourth predicate, and this takes one exact surface over a cleverer filter.

## Mutations against the pinned guard

Round 1's, round 2's, and new ones aimed at the pin itself — **thirteen
planted, thirteen red**, including the two that defeated the previous design:

| mutation | before | now |
|---|---|---|
| retraction inside the blockquote, imperative verbatim | GREEN | **RED** |
| role table, two synonyms apart (`publishes` / `raises a pull request`) | GREEN | **RED** |
| rule softened to `MAY … where convenient` | GREEN (r1) | **RED** |
| flag bullet made optional | GREEN (r1) | **RED** |
| "what each side does" inverted | GREEN | **RED** |
| delegate's reference negated | GREEN | **RED** |
| shared-cwd correction inverted | GREEN | **RED** |
| boundaries premise made unconditional | GREEN | **RED** |
| role table's worktree column inverted | — | **RED** |
| `Branch:` field made optional | — | **RED** |
| heading renamed | — | **RED** |
| section commented out, unclosed `<!--` | — | **RED** |
| **a single extra space inside the rule** | — | **RED** |

Every run asserts a test actually executed (`Ran N`, N > 0) — round 2's
reviewer recorded scoring a GREEN having run zero tests, and nearly filing an
honest fix as vacuous.

Suite 110 modules / 3096 tests green; `perry-lint --root .` 0 errors.

## What is still not covered, stated rather than left to the next round

- **A fifth normative region nobody has written yet** is unpinned by
  construction. The pin covers what exists; it cannot cover a rule added later
  in a file it does not read. That is the honest limit of an allowlist.
- The code-fence hole (`TASK-318`) is unchanged and still excluded.
- No real dispatch has been run against the rule. Its first live test was this
  session's four agents, all of which took `isolation: "worktree"` and left the
  primary checkout on `main` — recorded, but that is one observation and not a
  guard.
