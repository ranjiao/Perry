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

NOT YET WRITTEN — see criteria below.

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

## 6. Suite and lint

```
$ python3 bin/perry-lint --root .
0 error(s), 37 warning(s)
```

Full suite: NOT YET CHECKED.

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

## Findings

NOT YET WRITTEN.
