# TASK-285 — round 1, V4 review

> **Checkout**: isolated worktree `.claude/worktrees/agent-a9275f00880aefdc1`,
> branched from `d49964e` (`chore: consolidate test suite and project state`).
> Everything under review is on `main` at `5c76aa2`; the worktree shares the
> object database, so `git show main:<path>` reached all of it. Every cited
> path resolved — nothing was reconstructed.
>
> **All destructive work was done on `git archive main` copies** in a scratch
> directory (`scratchpad/w285`, and `scratchpad/w285g` for the git-backed suite
> run). The project under review was never modified.

Criteria: `perry/evidence/2026-09/TASK-285-spec.md`, including its `## Bound`.

---

## Verdict in one line

**FAIL.** Spec `Verification` item 4 is unmet in the landed tree — `dispatch.md`,
the file this change designates as the rule's single home, still makes `PR URL:`
a required RESULT field whose only sanctioned alternative is a direct push, on a
project whose hook escalates `git push`. Seven mutations of the new guard came
back GREEN, two of them inverting the deliverable's own rule from mandatory to
optional.

The row is close. Items 1, 2, 3, 5 and 6 all hold, the author's measured claims
all reproduced, and the three things I was asked to be sceptical about were
**all** honest. The failure is a reconciliation the change started and did not
finish, plus a guard that pins the rule's vocabulary rather than its force.

---

## 1. The author's own claims — every one reproduced

I treated the result document as data. All of it held.

### 1.1 The nine mutations reproduce, and the M6 attribution is real

Re-run independently, anchored **by line number** (never `replace(...,1)` on a
multi-occurrence string), `__pycache__` cleared and 1.1 s slept before each run,
bytes restored from a pre-mutation snapshot and md5-verified:

```
baseline: GREEN (Ran 7 tests, OK)

  RED   A1  dispatch.md:49 heading renamed -> '... RENAMED-AWAY'
  RED   A2  dispatch.md:119 flag name wrong (worktree -> sandbox)
  RED   A3  dispatch.md:48 UNCLOSED '<!--' before the section
  RED   A4  dispatch.md:120 shared-cwd correction dropped ('not a licence')
  RED   A5  dispatch.md:91 merge half unnamed (git merge --no-ff removed)
  RED   A6  git-boundaries.md ALL 4 'own worktree' removed        (replaced: 4)
  GREEN A6b git-boundaries.md ONE of 4 'own worktree' removed     (replaced: 1)
  RED   A7  delegate.md:158 rule reference removed
  RED   A8  delegate.md:160 unconditional push order restored (exact literal)
  RED   A9  dispatch.md project-specific sentence returns
post-restore: GREEN
```

**The M1 fix works.** `assertRegex(src, r"(?m)^## The tree the agent works in$")`
goes RED on the renamed heading that defeated `assertIn`.

**The M6 attribution is correct and I verified it rather than accepting it.**
`grep -c "own worktree" work/reference/git-boundaries.md` → **4** (lines 9, 10,
12, 18). A6b reproduces the author's harness bug exactly — replace one of four,
guard stays green; A6 replaces all four and the guard goes red. The distinction
between *the guard is weak* and *the instrument was weak* is real here, and the
author did not misattribute a guard defect to its instrument. This is the one
place where I most expected to find a dressed-up failure and did not.

### 1.2 `TASK-318` is genuinely filed, and the exclusion is honest

`perry/tasks.jsonl` carries `TASK-318`, `created: 2026-09-02T23:47:54+08:00` —
**the day before this row was written** — status `not_started`, filed by
TASK-284's round-2 V4 reviewer, with its own independent reasoning about
`visible()` stripping comments but not fences. It was not minted to give this
row somewhere to put an inconvenience. The out-of-scope call is legitimate.

### 1.3 The control fix is not vacuous — verified by my own mutation

`tests/test_header_rule_harness.py::TestTheCopyItselfIsClean::test_the_copy_carries_the_readers`:

```
baseline: GREEN
  RED   C1  copy drops viewer/ (NOT_COPIED gains 'viewer', SOURCELESS untouched)
  GREEN C2  BOTH sides gain 'viewer'  [the author's vacuous FIRST fix]
  RED   C3  live side stops excluding the state root ('perry' out of SOURCELESS)
  RED   C4  copy drops bin/
post-restore: GREEN
```

C1 and C4 prove the landed control still detects a copy that lost readers; C3
proves the live side is really excluding what the copy was never given. C2 is
green **by design** — it is the tautology the independent `SOURCELESS` spelling
exists to make visible, and it only fires when someone edits both spellings
together. The landed version is sound.

> **An instrument failure of my own, recorded because it is the exact trap this
> round warns about.** My first pass ran this control as
> `python3 tests/test_header_rule_harness.py TestControls.test_...`. That module's
> `__main__` block never calls `unittest.main()` — it prints a corpus report and
> exits 0 — and the class is `TestTheCopyItselfIsClean`, not `TestControls`. So
> C1/C2/C3 all came back "GREEN" having run **zero tests**, and I nearly filed
> the author's honest control fix as vacuous. Re-run through
> `python3 -m unittest`, with `assert "Ran 1 test" in out` added to the harness
> so a run that executes nothing can never again be scored as a pass.

### 1.4 Suite, lint, and the pre-change baseline

- `grep -in "worktree\|isolation"` on `5720730:work/reference/dispatch.md` → no
  output. The "measured before the change" claim is true.
- `python3 tests/parallel -j 4` on a git-backed copy of `main`:
  **110 modules · 3094 tests · all green.** (On my first, non-git copy 8 tests in
  `test_tree_guard.py` errored on `git rev-parse HEAD` — my `git archive` extract
  has no `.git`. That was my instrument, not the change; re-run under `git init`
  it is green.) Item 5 holds.
- `python3 bin/perry-lint --root .` → **0 errors**, 16 warnings. Item 6 holds.
- Bound enumeration: `grep -l "The tree the agent works in" work/reference/*.md`
  → exactly `delegate.md`, `dispatch.md`, `git-boundaries.md`. **Size 3, as
  declared.** The remainder is honest too: `autopilot.md:218` really does say
  *"Run full `/pmo dispatch <task-id>` flow (see `dispatch.md`)"*, and it carries
  no push/PR instruction of its own.

### 1.5 The edited test — I judge the author right

The burden was on the author and I think it is discharged. `delegate.md`'s
roleless block pinned `Do NOT merge own PR`. This change makes the PR
conditional on the hook, so on a project where pushing is escalated there is no
PR, and the pinned sentence asserted something that cannot occur. The
replacement pin, `Do NOT merge own work`, is **strictly broader** — it covers
both the PR case and the local-merge case that is now the default. The
requirement the test protects (no self-merge on the roleless path) is not
weakened, the assertion was not deleted or loosened, it stays in the same list,
and the reason sits in a comment at the assertion. This is a test that was
pinning a *noun* the change legitimately retired, not a test bent to fit a bug.

---

## 2. Finding 1 (FAIL) — `dispatch.md` still contracts for a PR it now forbids

**Spec `Verification` item 4**: *"No file in `work/reference/` still instructs an
agent to push or open a PR as the default path. Grep is the check, and the
assertion is a NOT-in."*

Grep, on the landed tree:

```
$ grep -n "PR URL" work/reference/dispatch.md
251:   - `PR URL:` (or "n/a — direct push" with explicit reason)
274:   - PR URL + branch + commit SHA
297:PR URL: <url>           # or "n/a — direct push" with reason
```

Line 251 sits under `## On completion` step 1, *"Read the agent's RESULT block.
**Required fields:**"* — `PR URL:` is listed **first**. Line 297 is
`## RESULT block format (required from any dispatched agent)`.

On this project the hook escalates `git push` and `origin`, so the rule this
change lands says: *the agent commits, does not push, does not open a PR, and
the primary checkout merges.* A compliant agent therefore has **no truthful
value** for a required field. `<url>` is false, and `"n/a — direct push"` is
false — there was no push. dispatch.md offers no third option, and the same
file's step 4 gates the status transition on it:

> *"All objective verifications pass + no scope violation + **RESULT block has
> all required fields** → status `review`."*

So a dispatch that follows the new rule exactly either lies in its RESULT block
or fails PMO's own completeness check. `## Failure handling` still carries
*"ff-only PR push failed"* as a named path for the same reason.

**This inconsistency is one the change created.** Before it, `git-boundaries.md`
and `delegate.md` ordered an unconditional push and PR, and dispatch.md's `PR
URL:` field was consistent with them. The change conditioned the expectation in
two files and left the third — the one it names as the rule's single home —
unconditioned. Worse, it is a *three-way* split, and the author clearly saw the
problem in one place and not the other:

| Where | What it now says about the RESULT block |
|---|---|
| `delegate.md:139` (edited by this change) | PR link required *"only where a PR is permitted"* — correctly conditioned |
| `git-boundaries.md:18` (added by this change) | the agent *"names that branch in the RESULT block"* — a field the RESULT format **does not define** |
| `dispatch.md:251, 297` (untouched) | `PR URL:` required, unconditioned; **no branch field at all** |

`git-boundaries.md` now requires a field dispatch.md never defines, and
dispatch.md requires a field git-boundaries.md's default path cannot produce.

**The counter-argument, and why it does not save the round.** One could say
lines 251/297 are a *reporting format*, not an instruction to push, and so not
literally caught by item 4's words. I do not think that survives contact: a
required output field with exactly two sanctioned values, both of which
presuppose the code left the machine, tells every dispatched agent that
push-or-PR is the expected outcome — and step 4 puts teeth on it. Item 4's own
framing is *"as the default path"*, and this is the default path of the
completion procedure. That the author conditioned the identical field in
`delegate.md:139` is the strongest evidence that it needed conditioning here
too.

**Reproduction** (read-only, on a copy):

```
$ git archive main | tar -x -C /tmp/w285 && cd /tmp/w285
$ sed -n '250,252p;296,298p' work/reference/dispatch.md
$ grep -n "High-stakes" -A 12 .perry/hook.md | grep "git push"
   # `git push`, `origin` are escalated on this project
```

This is a wrong answer on an input a user can produce — in fact on the only
input this repository can produce, since it is this repository's own hook.

---

## 3. Finding 2 (FAIL) — seven green mutations; the M1 *category* was not enumerated

The round's standing rule: *"A mutation that comes back green IS a V4 finding."*
Every mutation below was confirmed to actually execute (`Ran 7 tests ... OK`).

```
  GREEN B1  the flag moved OUT of the executor section into the rule section
  GREEN B3  git-boundaries.md push order restored in DIFFERENT WORDS
  GREEN B4  delegate.md      push order restored in DIFFERENT WORDS
  GREEN B5  the rule NEGATED in place in dispatch.md
  GREEN B6  the reference points at a section that does not exist
  GREEN B7  the rule softened from MANDATORY to OPTIONAL
  GREEN B8  'It is not optional' deleted, flag bullet kept
```

**B7 is the serious one.** The deliverable is *"A dispatched agent works in its
own git worktree"* and *"Pass `isolation: "worktree"`. **It is not optional**"*.
Replace those with:

```
> **A dispatched agent MAY work in its own git worktree where convenient. The primary checkout is
> never switched by an agent; it merges the agent's branch afterwards, and that
> merge is the only code operation it performs.**
...
- Pass `isolation: "worktree"` when the row happens to touch code — optional otherwise.
```

and the guard reports `Ran 7 tests in 0.008s / OK`. The rule that this entire
row exists to write has been turned into a suggestion, and nothing goes red. The
2026-09-02 failure recurs under a document that passes its own guard.

**B3/B4 restore the exact defect the scope was widened to fix.** Replacing
`git-boundaries.md:19` with *"Default expectation: the Coding Agent pushes its
feature branch to `origin` and opens a pull request; the PR link goes in the
RESULT block."* is green, because `test_no_shipped_procedure_orders_an_unconditional_push`
is a NOT-in against two exact literals — `"Push the branch and open a PR"` and
`"Code commits go through PR by default"` — plus an `assertIn(".perry/hook.md")`
that any passing mention satisfies. Any rewording walks through.

**Why this is a category miss and not a wish-list.** Rule 1 of this round: when
you find a defect, the deliverable is *every* place that category occurs. M1's
category is *a short-literal presence/absence assertion that a plausible edit
walks past*. The author fixed the **one instance** the mutation happened to
land on — the heading, now pinned to a whole line — and left the other six
tests in the class on bare `assertIn`/`assertNotIn` over short strings. B1 and
B3–B8 are that category, enumerated. The fix was instance-shaped where the round
asked for category-shaped.

I record the honest counterweight: spec item 4 itself says *"the assertion is a
NOT-in"*, so B3/B4 are the weak form the spec sanctioned, and item 2 asks only
that **deletion** redden the guard, which it does (A6, A7, B2 all red). B3–B6
alone I would have filed rather than failed. **B7/B8 are different** — they
defeat a *positive* assertion about the change's own headline deliverable, and
a guard whose subject can be inverted while it stays green is not holding that
subject down.

**Also unguarded (B1):** item 1 requires the flag to be learnable *"in the
executor section"*, but the assertion is `assertIn('isolation: "worktree"', src)`
over the whole file. Move the bullet out of `### Executor: claude-subagent` and
into the rule section and the guard is green while item 1 is false. Item 1 is
satisfied in the landed tree — this is a guard-strength finding, not a live
defect.

---

## 4. What holds

- **Item 1** — `isolation: "worktree"` is at `dispatch.md:119`, inside
  `### Executor: claude-subagent`, phrased as an order. A reader of that section
  alone learns the flag. Holds.
- **Item 2** — deletion of the rule reddens the guard in all three files
  (A6 boundaries, A7 delegate, A1/B2 dispatch); restore is green. Holds.
- **Item 3** — `visible()` is used and the unclosed `<!--` mutation (A3) is red.
  Holds.
- **Items 5 and 6** — suite green, lint 0 errors. Hold.
- **The `## Bound`** — enumeration, size and remainder all verified accurate.
  This is a good bound; it made the round checkable in a way TASK-067's was not.
- The measured `fatal: 'main' is already used by worktree` argument is sound,
  and the scope widening was a recorded user decision, not drift.

---

## 5. What I would need to see to pass this

1. `dispatch.md`'s `## On completion` required-field list and
   `## RESULT block format` conditioned the way `delegate.md:139` already is —
   with a branch field, since `git-boundaries.md:18` now demands one.
2. A guard assertion that pins the rule's **force**, not only its words — B7 red.

Neither is large. The row is one reconciliation and one assertion away.

---

## 6. Notes for whoever takes this next

- The three claims I was told to be sceptical about (M6's attribution, TASK-318's
  filing, the edited `test_role_cards` pin) were **all honest**. The result
  document does not overclaim anywhere I could measure. The failure here is
  incompleteness, not misrepresentation, and the evidence document's own
  closing paragraph — *"the next automated dispatch is the first test of whether
  the rule as written is followable"* — is the right instinct.
- Whoever fixes B7 should decide the same question TASK-318 poses: whether these
  guards are about *bytes present* or *a reader being bound*. B7 is that question
  arriving from the other direction — the bytes are present and the reader is
  not bound.

---

```
=== VERDICT ===
task: TASK-285
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-285-spec.md
checked: worked entirely on `git archive main` copies in scratch (w285, and w285g with `git init` for the suite) — the project under review was never written to. Re-ran all 9 of the author's mutations line-anchored with snapshot+md5 restore, __pycache__ cleared and 1.1s slept per run: A1-A5, A7-A9 RED, A6 RED with all 4 occurrences replaced, A6b GREEN with 1 of 4 replaced (reproducing and confirming the M6 harness-defect attribution; `grep -c "own worktree" git-boundaries.md` = 4). Ran 8 further mutations of my own (B1-B8): 7 GREEN, each confirmed to have actually executed `Ran 7 tests`. Mutated the landed control `test_header_rule_harness.TestTheCopyItselfIsClean.test_the_copy_carries_the_readers` in both directions (C1 copy drops viewer/ RED, C3 live side stops excluding the state root RED, C4 copy drops bin/ RED, C2 both-spellings-edited GREEN by design) — the landed control is NOT vacuous. Verified TASK-318 exists in perry/tasks.jsonl created 2026-09-02, predating this row. Verified the Bound: `grep -l "The tree the agent works in" work/reference/*.md` = exactly 3 files, and autopilot.md:218 defers to dispatch.md and carries no push/PR text. Verified the pre-change baseline (`grep -in "worktree\|isolation"` on 5720730:dispatch.md = empty). Ran `python3 tests/parallel -j 4` (110 modules / 3094 tests / all green on the git-backed copy) and `python3 bin/perry-lint --root .` (0 errors). Grepped all of work/reference/ for surviving push/PR default instructions. Read the spec, the result document, both commits' diffs, and .perry/hook.md.
not-checked: I did not perform a real dispatch, so the only claim that matters most — that an agent reading § The tree the agent works in actually isolates — is unverified; the author names this as the real test too. I did not mutate or judge the non-claude executor sections (opencode-subagent, codex, human): the rule says it governs every executor but only claude-subagent is given a flag to pass, and I read those sections without testing them. I did not verify the row's bookkeeping (.perry/events.jsonl, BOARD.md, perry/tasks.jsonl status, journal lines) — out of V4 scope. I did not evaluate the code-fence hole (TASK-318, excluded by the spec) and did not attempt any fence-based mutation. I did not test the shipped files on a non-Perry project, so "the rule is generic" rests on the NOT-in plus reading. I did not investigate the pre-existing lint warning that 45 of 137 specs present the escalation gate no scope. My suite baseline is main@5c76aa2 only — I did not run the suite at the pre-change commit, so "no redder than baseline" is verified as "green", not as a delta.
proof: Finding 1 (spec Verification item 4). `git archive main | tar -x -C /tmp/w285; cd /tmp/w285; grep -n "PR URL" work/reference/dispatch.md` -> 251 "`PR URL:` (or \"n/a — direct push\" with explicit reason)" listed FIRST under `## On completion` step 1 "Required fields:", and 297 in `## RESULT block format (required from any dispatched agent)`. On this project `.perry/hook.md § High-stakes operations` escalates `git push` and `origin`, so the rule this change lands says the agent commits and does not push and does not open a PR — leaving no truthful value for a required field (`<url>` false, "n/a — direct push" false), while dispatch.md step 4 gates the `review` transition on "RESULT block has all required fields". The change conditioned this same field in delegate.md:139 ("only where a PR is permitted") and added a branch field requirement in git-boundaries.md:18 that the RESULT format does not define, so the three files now disagree. Finding 2 (green mutations). B7, line-anchored on the scratch copy: replace dispatch.md:51 with "> **A dispatched agent MAY work in its own git worktree where convenient. The primary checkout is" and dispatch.md:119 with "- Pass `isolation: \"worktree\"` when the row happens to touch code — optional otherwise."; then `rm -rf **/__pycache__; sleep 1.1; python3 tests/test_spec_scannability.py TestTheAgentGetsItsOwnTree -v` -> "Ran 7 tests in 0.008s / OK". The row's headline rule is inverted from mandatory to optional and the guard stays green. B3 likewise: replace git-boundaries.md:19 with "- **Default expectation: the Coding Agent pushes its feature branch to `origin` and opens a pull request; the PR link goes in the RESULT block.** See `.perry/hook.md`." -> "Ran 7 tests / OK", because test_no_shipped_procedure_orders_an_unconditional_push is a NOT-in against two exact literals.
=== END VERDICT ===
```
