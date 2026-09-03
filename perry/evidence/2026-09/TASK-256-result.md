# TASK-256 — result

> Branch: `coding/task-256-restore-check`
> Baseline: `main` at `47fa45a`
> Spec: `perry/evidence/2026-09/TASK-256-spec.md`
> Worktree handed over at: `d49964e` — **145 commits behind `main`**, re-cut (§ 0)

## 0. The worktree was not cut at the baseline

The brief named `main` at `47fa45a` and warned that worktrees on this project
have been handed over at `d49964e`. This one was.

```
git rev-parse HEAD                              d49964e   (as handed over)
git merge-base HEAD main                        d49964e   (ancestor, not diverged)
git rev-list --left-right --count HEAD...main   0   145
```

`d49964e` predates the spec itself, so the row's own criteria file does not
exist there. The branch was therefore cut from `47fa45a`:

```
git checkout -b coding/task-256-restore-check 47fa45a
git rev-list --left-right --count HEAD...main   0   0
```

**`main` then moved underneath this row, mid-run.** It was `47fa45a` when this
branch was cut and `ba6d31a` when the work finished — eight commits, the
`TASK-067` merge among them. Nothing on `main` was touched by this row; the
overlap is one file, `tests/durations.json`, where both changes append an entry
to the same dict. Every measurement below is pinned to a named ref, so none of
them is invalidated by the move, but whoever merges this should expect that one
conflict and nothing else.

## 1. The bound, re-run

The spec's own enumeration command, on `47fa45a`:

```
grep -rn "md5\|restore" work/reference/review.md \
                        work/reference/review-constraints.md \
                        work/reference/dispatch.md
    → no output, exit 1
```

**0 sites**, as the spec's `Size` line claims. The absence is the finding.

Two further observations inside the bound, neither of which changes the
deliverable:

- `work/reference/dispatch.md` and `work/reference/delegate.md` contain **no
  occurrence of "mutat" at all**. They never prescribe the harness, so there is
  nothing in them to correct, and a pointer added to them would be a reference
  with no caller. This matches the spec's own `Remainder`: the prescription
  lived in the PMO's ephemeral briefs and in a memory file outside this
  repository, not in these two pages. They are left alone deliberately, not
  overlooked.
- `bin/perry-lint:2113` already cites `review-constraints.md § You are a
  reader` by section name rather than restating it — the reference-don't-copy
  precedent this change follows.

## 2. The circularity, reproduced

Scratch harness `task256-circularity-abd3fb21.py` (uniquely named per the
brief), run against `bin/perry-task` at `47fa45a`. Both rows execute the
identical code path; they differ only in whether the file was already corrupted
when the snapshot was taken.

```
truth ref          : git show 47fa45a:bin/perry-task  (md5 67106a482237…)

                     OLD check | NEW check | actual file state
honest restore     :      True |      True | file is ORIGINAL
corrupted baseline :      True |     False | file is ALREADY-WRONG
```

**The old check reports `True` in both rows.** `BASE[1]` is the digest of
`BASE[0]` and `BASE[0]` is what was just written back, so the assertion cannot
fail when the write succeeds. It verifies the write happened, not that the file
is right.

This is the control the spec's `Verification` item 1 requires: a baseline
snapshotted from an already-corrupted file is **caught by the new pattern
(`False`) and missed by the old one (`True`)**. It is now executable rather
than prose — `tests/test_restore_check.py § TestCircularity` asserts both
halves, including that the old check *does* pass the corrupted baseline, so the
demonstration cannot rot into one that demonstrates nothing.

## 3. The rule — one home, one reference

**Home:** `work/reference/review-constraints.md § Verify a restore against an
independent source`. That file is read by every V4 round by path and is
documented as never being retyped into a prompt, which is the property this rule
needs.

It states the rule (`git show <ref>:<path>`, never the harness's own snapshot),
the reason in the spec's required one-sentence form — *that assertion cannot
fail when the write succeeds* — with the two-line control beside it, and the
`TASK-325` incident that makes it non-hypothetical.

**Reference:** `work/reference/review.md § 2`, rule 2 gains one sentence
pointing at that section by name. It carries no reasoning, no code block and no
control table. The explanation exists in exactly one file.

`tests/test_restore_check.py § TestGuidanceSaysIt` enforces this rather than
trusting it: `test_review_references_and_does_not_recopy` fails if the
explanation ever appears in `review.md`, and
`test_the_section_exists_in_exactly_one_file` fails if the section is ever
duplicated anywhere under `work/reference/`.

## 4. Ship-a-helper — built it

The spec left this open and required an answer either way. **Built:
`bin/perry-restore-check`.**

The argument for is this repository's own, stated in the first line of
`bin/README.md`: *a number Perry reports must be computed, never eyeballed.* A
restore verdict is exactly such a number, six briefs a week hand-roll the loop,
and every hand-roll is a fresh opportunity to write the circular check back in.

The argument against, which the spec names: **a harness that lives in the tree
can itself be mutated**, and would then vouch for a file it should reject. That
objection is answerable rather than decisive, for two reasons:

1. The tool's truth comes from `git show <ref>:<path>`. Git's object store is
   content-addressed and lives outside the working tree, so no in-tree mutation
   can change what it returns. The data source is out of reach by construction.
2. The tool compares **its own bytes** against `git show HEAD:<its own path>`
   before answering anything, and **refuses** — exit 2, distinct from the exit 1
   it uses for a real mismatch — when they differ. That self-check is not
   circular: its truth also comes from the object store, not from the file being
   checked. A legitimate editor passes `--allow-modified-self`, so the cheapest
   path past the message is not the silent one.

The hole this does **not** close, stated rather than papered over: a wrong
helper that has been *committed* passes its own self-check. That case belongs to
the test suite, and `TestHelperSelfCheck` is it — mutation 7 below is that check
being switched off and the suite going red.

Refusing rather than warning follows `tests/run § step 0a`'s own reasoning —
refusing costs a flag, and a warning inside a verifier is a line an agent
scrolls past.

## 5. Mutations — 9 planted, 1 came back GREEN

Every mutation was planted in a throwaway `git init` repository, a temp
directory, or a `git archive` copy of this branch in the agent's own scratch
directory. **The live checkout was never mutated** — the suite's step-0 tree
guard confirms it in § 6. Restores were verified against
`git show b6ad8bf:<path>`, never against a snapshot taken by the harness doing
the restoring.

The `git archive` copy was itself checked against the ref before any mutation
was planted, so the "restored" column below compares two independently derived
digests rather than a value against itself:

```
                                        copy md5        git show b6ad8bf md5
work/reference/review-constraints.md    cbcc3b6360a4 =  cbcc3b6360a4
work/reference/review.md                a318088fa53a =  a318088fa53a
bin/perry-restore-check                 758e74a5a1d7 =  758e74a5a1d7
tests/test_restore_check.py             f1b92969bc62 =  f1b92969bc62
```

| # | target | mutation | verdict |
|---|---|---|---|
| 1 | `bin/perry-restore-check` | `ok=actual == committed,` → `ok=True,`, committed into a throwaway repo | **red** — refuses, exit 2 (`test_mutated_helper_refuses`) |
| 2 | as above | same mutation, self-check waived with `--allow-modified-self` | **green by design** — falsely passes a `MUTATED` file. This is the control that proves mutation 1 bites (`test_the_mutation_would_otherwise_have_been_silent`) |
| 3 | a subject file | corrupted *before* the snapshot, then round-tripped | **red** under the shipped tool, exit 1; green under the old check (`test_a_restore_onto_a_corrupted_baseline_is_caught`) |
| 4 | `work/reference/review.md` | the pointer replaced by a second copy of the reason | **red** — `test_review_references_and_does_not_recopy` |
| 5 | `work/reference/review-constraints.md` | section heading renamed away | **red** — `test_constraints_carry_the_rule`, `test_the_section_exists_in_exactly_one_file` |
| 6 | `work/reference/review-constraints.md` | reason sentence removed, rule kept | **red** — `test_the_rule_states_its_reason` |
| 7 | `bin/perry-restore-check` | `if verdict == "modified" and not allow_modified_self:` → `if False:` | **red** — `test_mutated_helper_refuses` |
| 8 | `bin/perry-restore-check` | `ok=actual == committed,` → `ok=True,` | **red** — 4 tests |
| 9 | `bin/perry-restore-check` | `f"{ref}:{rel}"` → `f"HEAD:{rel}"` in `blob_at` | **GREEN — finding.** See below |

### Mutation 9 is the finding

Replacing the caller's `<ref>` with a hard-coded `HEAD` inside `blob_at` passed
the entire module. **The tool took a `<ref>` argument and nothing proved it used
it.** Every test happened to pass `HEAD`, so a silent fallback to `HEAD` was
indistinguishable from correct behaviour.

That is not academic, and this row is its own witness: the mutations above are
verified against `b6ad8bf` while `main` moved to `ba6d31a` underneath them. A
round that pins its baseline to the commit it was cut from — which is precisely
what the new rule tells agents to do — is the case where a fallback to `HEAD`
compares against the wrong bytes and reports OK. The defect would have shipped
inside the tool written to stop exactly this class of error.

Closed by `test_the_ref_argument_is_honoured`, which commits a second revision
and requires the file to match `HEAD` and **not** match the first commit.
Re-planted afterwards:

```
mutation 9 (re-planted against the new test)
    RED  exit=1
    FAIL: test_the_ref_argument_is_honoured
    restored vs git show b6ad8bf:bin/perry-restore-check = True
```

**Tally: 9 planted · 8 red · 1 green-by-design control (2) · 1 GREEN finding
(9), now closed and red.**

### A no-op anchor, caught — in my own instrument

The first draft of `test_mutated_helper_refuses` replaced
`b"return actual == committed"`, a string that **does not occur** in
`bin/perry-restore-check`; the real line is `ok=actual == committed,`. The
substitution silently no-opped, the helper was never mutated, and the test
passed anyway. This is exactly the failure the brief names — *a non-matching
anchor silently no-ops and reports a meaningless OK* — and it happened while
building the fix for the adjacent one. `_planted_copy` and both scratch harnesses
now assert the edit landed (`assert after != before`, `assert count(old) == 1`)
before writing, so a stale anchor fails loudly instead of producing a green that
means nothing.

## 6. Tests

Baseline, measured on this branch before any edit:

```
env -u PERRY_PROJECT bash tests/run
  1. schema drift guard                    ✓ clean
  2. 111 modules · 3134 tests · 356.5s     ✓ all green
  3. bin/ scripts parse and --help         ✓
  4. sample projects lint clean (en, zh)   ✓
  0. tree guard                            ✓ nothing moved
exit 0
```

After:

```
env -u PERRY_PROJECT bash tests/run
  2. 112 modules · 3149 tests · 181.5s     ✓ all green
  0. tree guard  ✓ nothing under …/agent-abd3fb218067dfe6c moved
exit 0
```

**3149/3149 vs baseline 3134/3134** — one module and fifteen tests added, none
lost. `python3 bin/perry-lint --root .` → **0 errors**, 26 warnings, all
pre-existing.

### The suite caught three defects in this change

Worth recording, because the first full run after the edit was **red**, and all
three were mine:

1. `test_pointers_resolve` and `test_router_budget` both rejected the citation
   `review.md § 2 rule 2` — `§ 2` resolves to a heading, `§ 2 rule 2` does not.
   Two independent guards, same finding. Rewritten as ``` `review.md § 2`, rule
   2 ``` in all three places it appeared.
2. `test_durations_provenance` rejected the new module for having no entry in
   `tests/durations.json`. Added as `{"sec": null, "source": "never-measured"}`,
   which is what that file documents as the honest answer: the module has been
   timed standalone at ~1.5s but never under the suite's eight-worker load, and
   guessing a figure into a provenance file is the defect that file exists to
   prevent.

## 7. What is deliberately not built

No check that inspects an agent's scratch directory for a bad harness. Those are
written ad hoc in temp directories no check can reach, the spec forbids it in
two places, and a guard claiming to police the practice would be the fourth
guard-over-behaviour failure on this board this week.

This row fixes the **instruction** and ships an **opt-in tool**. It polices
nobody: `bin/perry-restore-check` is called or it is not, and nothing fails when
an agent hand-rolls the loop correctly instead. The only things asserted are
that the guidance still says what it must, and that the shipped tool still does
what it claims.

## 8. Files changed

| file | change |
|---|---|
| `work/reference/review-constraints.md` | **+1 section** — the rule, its reason, the control, the tool. The one home. |
| `work/reference/review.md` | **+1 sentence** in § 2, rule 2 — a pointer, no second copy |
| `bin/perry-restore-check` | **new** — the helper, with its own self-check |
| `bin/README.md` | **+1 table row** for the new tool |
| `tests/run` | `bin/perry-restore-check` added to step 3's parse-and-`--help` list |
| `tests/test_restore_check.py` | **new** — 15 tests: the control, the guidance, the helper, the helper's self-check, the ref-honoured test mutation 9 bought |
| `tests/durations.json` | **+1 entry** for the new module |
| `perry/evidence/2026-09/TASK-256-result.md` | this file |

Nothing under `claims`, nothing in `schema/state-schema.json`. No push, no PR,
no merge; `main` untouched by this row.
