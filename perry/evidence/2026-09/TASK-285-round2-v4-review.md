# TASK-285 — round 2, V4 review

> **Checkout**: isolated worktree `.claude/worktrees/agent-a49db7baeac2de9d9`,
> branched from **`d49964e`** — the same stale base round 1 got, ~90 files
> behind. Everything under review is on `main` at **`7ea0bff`**; worktrees share
> the object database, so `git show main:<path>` reached all of it. **Every path
> cited in the prompt resolved. Nothing was reconstructed.**
>
> **All destructive work was done on `git archive main` copies** in scratch:
> `scratchpad/w285r2` (mutation battery) and `scratchpad/w285g` (`git init`-ed,
> for the suite and the verbatim reproductions). The project under review was
> never written to. `git status --porcelain` in this worktree is empty apart
> from this document.

Criteria: `perry/evidence/2026-09/TASK-285-spec.md`, including its `## Bound`.

---

## Verdict in one line

**FAIL.** The round-1 fixes close the two mutations round 1 actually ran and
leave the *categories* open one level out. **Twelve mutations came back GREEN**,
including a retraction sentence added to the rule's own blockquote — *"Where a
worktree is impractical, sharing the primary checkout instead is an acceptable
alternative"* — which inverts the row's headline deliverable from mandatory to
optional while `test_the_rule_is_mandatory_and_not_merely_available`, the test
written for exactly that defect, reports `Ran 9 tests / OK`.

This is round 1's finding 2 arriving again with different words in it. Round
1's own note said the fix was *"instance-shaped where the round asked for
category-shaped"*; the repair was hedge-literal-shaped where the defect is
modality-shaped, and hedge-literal-shaped is the same shape one level out.

**Round 1's finding 1 is genuinely fixed** — `dispatch.md`'s required-field
list, its `PR URL:` conditioning, and the RESULT template now agree with
`delegate.md` and `git-boundaries.md`, and I reddened all three by reverting
them independently.

---

## 0. What I did before believing anything

Every mutation below was **line-anchored** (1-based line number *plus* an
expected fragment on that line, so a drifted anchor raises rather than silently
mutating the wrong place — never `str.replace(old, new, 1)`), restored from
bytes snapshotted **before any mutation** and md5-verified against that
snapshot, with `__pycache__` cleared and 1.1 s slept before every run. Every run
asserts `Ran N tests` with `N > 0`, so a run that executes nothing can never be
scored as a pass — round 1 recorded being burned by exactly that.

Harness: `scratchpad/mut.py`, batteries `battery.py` / `battery2.py`.
Baseline and post-restore were GREEN (`Ran 9 tests`) on every battery.

---

## 1. Finding 1 (FAIL) — twelve green mutations; the M1 category is still open

```
baseline: GREEN (Ran 9)

  GREEN N1   retraction sentence INSIDE the rule blockquote (no listed hedge)
  GREEN N1b  "That is what we suggest; it binds nobody" INSIDE the blockquote
  GREEN N2   retraction in the paragraph immediately AFTER the blockquote
  GREEN N2b  "the agent normally shares the primary checkout" in the same section
  GREEN N3   flag bullet given an escape clause, "not optional" kept verbatim
  GREEN N4   unconditional push+PR reworded past the four ordering literals
  GREEN N4b  the same rewording in delegate.md
  GREEN N5   a CAUGHT order rescued by "hook" inside its OWN clause
  GREEN N6   pipe-delimited row without a leading pipe -> neighbour cell rescues
  GREEN N10  delegate's reference NEGATED, both pinned literals kept
  GREEN N11  shared-cwd correction inverted, "not a licence" kept
  GREEN N12  git-boundaries' premise made conditional on host support

  RED   N7a  CONTROL: `Branch: <name>` — always reverted
  RED   N7b  CONTROL: RESULT template reverted to `# or "n/a — direct push"`
  RED   N7c  CONTROL: `PR URL:` unconditioned again
  RED   N8   CONTROL: unclosed `<!--` before dispatch.md's section
  RED   N9   CONTROL: round 1's B7 verbatim ("MAY ... where convenient")
  RED   N13  CONTROL: unclosed `<!--` before git-boundaries' Rules

post-restore: GREEN (Ran 9)
```

Six controls red. The author's eight mutations are real and I do not dispute
them. What they do not establish is what their own docstrings claim.

### 1.1 The decisive one — N1

`rule_block()` is the new isolation, and the hedge loop runs over it. The
mutation adds one sentence *inside the block*, keeps the pinned imperative
verbatim, and uses **none** of the eight literals:

```
> **A dispatched agent works in its own git worktree. The primary checkout is
> never switched by an agent; it merges the agent's branch afterwards, and that
> merge is the only code operation it performs. Where a worktree is impractical,
> sharing the primary checkout instead is an acceptable alternative.**
```

```
$ find . -name __pycache__ -exec rm -rf {} +; sleep 1.1
$ python3 -m unittest tests.test_spec_scannability.TestTheAgentGetsItsOwnTree
Ran 9 tests in 0.011s
OK
```

The rule is retracted in its own blockquote and the guard named
`test_the_rule_is_mandatory_and_not_merely_available` is green. N1b does it in
the author's own idiom (*"That is what we suggest; it binds nobody"*), also
green. **A NOT-in over eight literals is a denylist, and the space of English
retractions is not eight items long.** The docstring says the guard exists
because *"every assertion pinned the PRESENCE of words and none pinned their
MODALITY"* — the replacement pins the presence of a *different* set of words.

### 1.2 `rule_block()` excludes almost the whole section — N2, N2b

```python
start = src.index("## The tree the agent works in")
return src[start:src.index("\n\n", src.index(">", start))]
```

`src.index(">", start)` lands on the blockquote's first `>`; `index("\n\n", …)`
ends at the first blank line after it. So the slice is **the heading plus the
three-line blockquote and nothing else** — `dispatch.md:49–53` of a section
running to line 110. The hedge check is blind to 57 of the section's 62 lines
by construction. N2 replaces line 55 (*"This is the rule; …"*) with *"Treat this
as guidance rather than a hard requirement: a project that runs every lane in
one shared tree is not in breach."* — green. N2b inverts the `What each side
does` bullet to *"The agent normally shares the primary checkout"* — green.

The docstring's stated rationale is *"a hedge added anywhere in the section
cannot be excused"*. The slice is not the section.

### 1.3 The flag bullet's window is presence-only — N3

`flag = src[src.index('Pass `isolation: "worktree"`'):][:200]` then
`assertIn("not optional", flag)`. Keep those two words and append the escape:

```
- **Pass `isolation: "worktree"`. It is not optional** — except on rows the PMO
  judges small, where the shared parent tree is fine — see § The tree …
```

Green. This is the same defect the class was rewritten to fix, in the one
assertion the rewrite left on `assertIn`.

### 1.4 The "property check" is still four surface forms — N4, N4b

The docstring of `test_no_shipped_procedure_orders_an_unconditional_push` is
explicit:

> *"this asserts the PROPERTY — every line that commands a push or a PR carries
> a condition — rather than the absence of two sentences."*

It asserts the absence of four regex alternatives:
`push(es|ing)? the branch`, `open (a|the) PR`, `opens? a pull request`,
`go through PR`. Two synonyms defeat it. Same line, same meaning, same file:

```
RED    - **Coding Agent commits its own work.** Default expectation: the Coding
         Agent pushes its feature branch to `origin` and opens a pull request.

GREEN  - **Coding Agent commits its own work.** Default expectation: the Coding
         Agent publishes its feature branch to `origin` and raises a pull
         request; the review link goes in the RESULT block.
```

`pushes → publishes`, `opens → raises`. The second restores in full the defect
the scope was widened to remove — a shipped procedure ordering the push that
`.perry/hook.md § High-stakes operations` escalates on this very repository —
and the guard reports OK. N4b is the same in `delegate.md:160`. Round 1 filed
this as B3/B4 and said *"any rewording walks through"*; that is still true, with
a larger literal list.

Note also that `pushes its feature branch` is not caught even though
`pushes the branch` is — the phrase `git-boundaries.md` used before this change
(`"Coding Agent pushes a feature branch and opens a PR"`) matches only on its
second half.

### 1.5 Per-clause has the per-line hole inside it — N5, N6

The move from per-line to per-clause was made because *"the rest of a long
bullet … supplied a word like 'hook' … and rescued an order that carried none
of its own."* The rescue still works when the word is in the **same** clause:

```
GREEN  Default expectation: the Coding Agent pushes the branch and opens a PR,
       whatever the hook says.
```

`ordering` matches, `conditional` matches on `hook`, assertion passes — for a
clause that explicitly says the hook is irrelevant. The two regexes are
independent word-presence tests over the same string; nothing relates the
condition to the order.

N6 is the splitter itself: `clauses()` splits on `|` only when
`line.lstrip().startswith("|")`. A GFM table row written without the optional
leading pipe is never split, so a neighbouring cell rescues again —
`Coding Agent | pushes the branch and opens a PR | on every project | hook: not
consulted` is green. Lower weight than N4/N5 (this repo's tables all use leading
pipes), but it is the constructed-input class the splitter claims to have closed.

### 1.6 The remaining presence assertions, enumerated — N10, N11, N12

Rule 1 of this round is *enumerate the category*, so I did not stop at the two
tests the prompt aimed me at. Every other assertion in the class is
presence-over-a-window and each can be negated with the pinned literal intact:

- **N10** — `test_the_other_two_files_reference_the_rule` pins `own worktree`
  and `The tree the agent works in`. `delegate.md:158` becomes *"**Work in its
  own worktree** is not required; sharing the user's checkout is fine —
  `dispatch.md § The tree the agent works in` describes the ideal, not the
  requirement."* Both literals present. Green.
- **N11** — `test_the_shared_cwd_line_no_longer_reads_as_a_licence` pins
  `not a licence` in a 400-char window. *"Reading that as a licence for the tree
  is **not a licence** problem in practice: sharing the tree is fine for small
  rows."* Green.
- **N12** — `git-boundaries.md:17`'s premise made conditional on host support
  (*"works in its own worktree **where the host supports one** … Otherwise it
  works in the primary checkout"*). Green.

Seven of the class's nine tests are walkable. The two that are not —
`test_the_result_block_…` and `test_the_rule_is_generic_…` — are the two whose
subject is a *format*, not a *modality*, which is the tell.

---

## 2. What the fixes did close — verified by my own mutation, not by reading

Round 1's **finding 1 is fixed**, and it is not cosmetic. `dispatch.md:251`
now makes `Branch: <name>` the unconditional field, `:252` conditions `PR URL:`
on the hook and names the truthful alternative
(`n/a — push is escalated on this project`), and the RESULT template at
`:298–300` agrees. All three reverted independently go red:

- **N7a** — `Branch: <name>` — always removed → RED
- **N7c** — `PR URL:` unconditioned → RED
- **N7b** — template reverted to `# or "n/a — direct push" with reason` → RED

The three-way disagreement round 1 documented is gone. `git-boundaries.md:18`'s
demand for the branch name in the RESULT block is now a field the RESULT format
defines.

Round 1's two *specific* mutations are also closed: **N9** (B7 verbatim, *"MAY …
where convenient"* + *"optional otherwise"*) is RED, and the B3 literal is RED.
The fixes work on the inputs that produced them.

`visible()` still holds: **N8** (unclosed `<!--` before `dispatch.md`'s section)
and **N13** (unclosed `<!--` before `git-boundaries.md`'s `### Rules`) are both
RED. Spec item 3 holds.

---

## 3. The rest of the spec's Verification

| Item | Result |
|---|---|
| 1 — `worktree`/`isolation` in `dispatch.md`, in the executor section, flag learnable | **Holds.** `dispatch.md:119` inside `### Executor: claude-subagent`, as an order. |
| 2 — deletion of the rule reddens the guard in each file | **Holds** (N8/N13 by comment; round 1's A6/A7 by deletion, not re-run). |
| 3 — `visible()`, unclosed `<!--` reddens | **Holds** (N8, N13). |
| 4 — no file in `work/reference/` instructs a push or PR as the default | **Holds in the landed tree.** The four grep hits (`git-boundaries.md:19`, `dispatch.md:109`, `delegate.md:160`, `review-constraints.md:39`) are all conditional or prohibitive. It is the *guard* for item 4 that fails, not item 4. |
| 5 — suite no redder than baseline | **Holds.** `python3 tests/parallel -j 4` on the git-backed copy: **110 modules · 3096 tests · 153.7s · all green.** |
| 6 — `perry-lint --root .` 0 errors | **Holds.** 0 errors, 16 warnings. |

**The `## Bound`.** `grep -l "The tree the agent works in" work/reference/*.md`
→ exactly `delegate.md`, `dispatch.md`, `git-boundaries.md`. **Size 3, as
declared.** Honoured: I filed nothing about a fourth file.

Two drifts in the Bound's other two numbers, recorded and **not** treated as
findings: it declares the guard at **7 tests** and the tree carries **9** (the
round-1 fixes added two), and it declares **9 named mutations** where the
author's fix commit reports 8. Both are the spec describing `f454417` and the
tree being `db12fa4`; neither weakens anything.

---

## 4. Notes, none of which change the verdict

- **`TASK-285-result.md` was not updated by `db12fa4`.** The result document on
  `main` still reports the pre-round-1 state — *"Nine mutations … GREEN
  MUTATIONS: [1, 6]"* — with no mention of the round-1 findings, the two new
  tests, or the `Branch:`/`PR URL:` reconciliation. The fix's evidence lives
  only in the commit message. That is a bookkeeping gap in the row's artifact,
  not a defect against the spec's `Verification`, and I do not fail on it.
- `dispatch.md:275` (`PR URL + branch + commit SHA`, in the evidence-writing
  step) is still unconditioned, but it describes what PMO writes down rather
  than instructing an agent to push, so item 4's words do not reach it. Filed as
  an observation.
- The code-fence hole is `TASK-318` and excluded by the spec. I attempted no
  fence mutation.

---

## 5. What would pass this

One assertion, not twelve. The class needs something that reads the rule's
**force** rather than its vocabulary — e.g. pin the rule block to an exact
expected text (`assertEqual` on the normalised blockquote), so *any* addition,
subtraction or rewording inside it reddens and the author is forced to update
the guard deliberately. The same shape closes item 4: pin the push/PR bullets
verbatim rather than filtering them. A denylist over English will lose this
argument at every round, and this is the second round it has lost it.

---

```
=== VERDICT ===
task: TASK-285
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-285-spec.md
checked: worked entirely on `git archive main@7ea0bff` copies in scratch (w285r2 for mutations; w285g `git init`-ed for the suite and the verbatim reproductions) — the project under review was never written to; my worktree is at d49964e and every prompt-cited path resolved via `git show main:<path>`. Ran 18 mutations of my own against tests/test_spec_scannability.py::TestTheAgentGetsItsOwnTree, each anchored by LINE NUMBER plus an expected fragment on that line (never str.replace(...,1)), restored from pre-mutation bytes with md5 verification, __pycache__ cleared and 1.1s slept per run, and every run asserted to have executed `Ran 9 tests` (>0) so a zero-test run could not be scored as a pass: 12 GREEN (N1, N1b, N2, N2b, N3, N4, N4b, N5, N6, N10, N11, N12) and 6 RED controls (N7a/N7b/N7c reverting the Branch/PR-URL conditionality in prose and template independently, N8 and N13 unclosed `<!--` in dispatch.md and git-boundaries.md, N9 round 1's B7 verbatim). Read rule_block()'s slice arithmetic and confirmed by construction that it covers only heading + blockquote (dispatch.md:49-53 of a section running to :110). Confirmed the push regex is four surface-form alternatives by the pushes/opens (RED) vs publishes/raises (GREEN) contrast on the same line of git-boundaries.md. Verified spec items 1, 3, 4, 5, 6 directly: `grep -n "worktree|isolation" dispatch.md` (flag at :119 inside `### Executor: claude-subagent`), full grep of work/reference/ for surviving push/PR default instructions (4 hits, all conditional or prohibitive), `python3 tests/parallel -j 4` (110 modules / 3096 tests / 153.7s / all green), `python3 bin/perry-lint --root .` (0 errors, 16 warnings). Verified the Bound: `grep -l "The tree the agent works in" work/reference/*.md` = exactly 3 files. Read the spec, round 1's review, the result document, .perry/hook.md § High-stakes operations, review-constraints.md, and the diffs of f454417 and db12fa4.
not-checked: I did not perform a real dispatch, so whether an agent reading § The tree the agent works in actually isolates is still unverified — the same gap round 1 named and the author's own closing paragraph names. I did NOT re-run the author's own eight mutations; I attacked the two new checks by construction instead, and my controls N9/N7a-c overlap them only in part, so "the author's 8 are 8 red" is unconfirmed by me. I did not run a pre-change-commit suite, so item 5 is verified as "green", not as a delta against a baseline. I did not evaluate the code-fence hole (TASK-318, excluded by the spec) and attempted no fence mutation. I did not mutate or judge the non-claude executor sections (opencode-subagent, codex, human) — only claude-subagent is given a flag. I did not check the row's bookkeeping (.perry/events.jsonl, BOARD.md, tasks.jsonl status, journal lines) beyond noticing that TASK-285-result.md was not updated by db12fa4. I did not investigate the pre-existing 45-of-139 unscannable-spec lint warning. I did not check whether any guard OUTSIDE TestTheAgentGetsItsOwnTree has the same denylist shape — the Bound scopes the guard to that class and I honoured it.
proof: On a `git archive main | tar -x` copy, line-anchored on dispatch.md:53 (anchor fragment "merge is the only code operation it performs."), replace that line with: `> merge is the only code operation it performs. Where a worktree is impractical, sharing the primary checkout instead is an acceptable alternative.**` — then `find . -name __pycache__ -exec rm -rf {} +; sleep 1.1; python3 -m unittest tests.test_spec_scannability.TestTheAgentGetsItsOwnTree` -> "Ran 9 tests in 0.011s / OK". The row's headline deliverable is retracted inside its own blockquote and `test_the_rule_is_mandatory_and_not_merely_available` is green, because its hedge check is a NOT-in over eight literals ("MAY ", "may work", "where convenient", "if convenient", "optional", "recommended", "should work", "prefer") and the retraction uses none of them. SECOND, independently: line-anchored on git-boundaries.md:18 (anchor "Coding Agent commits its own work."), `- **Coding Agent commits its own work.** Default expectation: the Coding Agent pushes its feature branch to \`origin\` and opens a pull request.` -> FAILED (failures=1), while `- **Coding Agent commits its own work.** Default expectation: the Coding Agent publishes its feature branch to \`origin\` and raises a pull request; the review link goes in the RESULT block.` -> "Ran 9 tests / OK". Two synonyms (pushes->publishes, opens->raises) restore the exact defect the scope was widened to remove, on a repository whose `.perry/hook.md § High-stakes operations` escalates `git push` and `origin`, and `test_no_shipped_procedure_orders_an_unconditional_push` — whose docstring claims to assert "the PROPERTY … rather than the absence of two sentences" — reports OK. THIRD: `rule_block()` returns `src[start:src.index("\n\n", src.index(">", start))]`, i.e. heading + blockquote only, so a retraction one line later (dispatch.md:55 -> "Treat this as guidance rather than a hard requirement: a project that runs every lane in one shared tree is not in breach.") is invisible to the hedge check by construction — also green.
=== END VERDICT ===
```
