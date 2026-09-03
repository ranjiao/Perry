# TASK-256 — result

> Branch: `coding/task-256-restore-check`
> Baseline: `main` at `47fa45a`
> Spec: `perry/evidence/2026-09/TASK-256-spec.md`
> Worktree handed over at: `d49964e` — **145 commits behind `main`**, re-cut (§ 0)

## 0. The worktree was not cut at the baseline

The brief named `main` at `47fa45a` and warned that worktrees on this project
have been handed over at `d49964e`. This one was.

```
git rev-parse HEAD                        d49964e   (as handed over)
git merge-base HEAD main                  d49964e   (ancestor, not diverged)
git rev-list --left-right --count HEAD...main   0   145
```

`d49964e` predates the spec itself, so the row's own criteria file does not
exist there. The branch was therefore cut from `47fa45a`:

```
git checkout -b coding/task-256-restore-check 47fa45a
git rev-list --left-right --count HEAD...main   0   0
```

Every measurement below is on `47fa45a` plus this branch's own commits.
Nothing on `main` was touched; nothing was pushed.

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
  nothing in them to correct and a pointer added to them would be a reference
  with no caller. This matches the spec's own `Remainder`: the prescription
  lived in the PMO's ephemeral briefs and in a memory file outside this
  repository, not in these two pages. They are left alone deliberately.
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
halves, including that the old check *does* pass the corrupted baseline, so
the demonstration cannot rot into one that demonstrates nothing.

## 3. The rule — one home, one reference

**Home:** `work/reference/review-constraints.md § Verify a restore against an
independent source`. That file is read by every V4 round by path and is
documented as never being retyped into a prompt, which is the property this
rule needs.

It states the rule (`git show <ref>:<path>`, never the harness's own
snapshot), the reason in the spec's required one-sentence form (*the assertion
cannot fail when the write succeeds*, with the two-line control), and the
`TASK-325` incident that makes it non-hypothetical.

**Reference:** `work/reference/review.md § 2 rule 2` gains one sentence
pointing at that section by name. It carries no reasoning, no code block and no
control table — the explanation exists in exactly one file.

`tests/test_restore_check.py § TestGuidanceSaysIt` enforces all of this:
`test_review_references_and_does_not_recopy` fails if the explanation ever
appears in `review.md`, and `test_the_section_exists_in_exactly_one_file`
fails if the section is ever duplicated anywhere under `work/reference/`.

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

1. The tool's truth comes from `git show <ref>:<path>` — git's object store is
   content-addressed and lives outside the working tree, so no in-tree mutation
   can change what it returns. The data source is out of reach by construction.
2. The tool compares **its own bytes** against `git show HEAD:<its own path>`
   before answering anything, and **refuses** (exit 2, distinct from the exit 1
   it uses for a real mismatch) when they differ. That self-check is not
   circular — its truth also comes from the object store, not from the file
   being checked. A legitimate editor passes `--allow-modified-self`; the
   cheapest path is not the silent one.

The hole this does **not** close, stated rather than papered over: a wrong
helper that has been *committed* passes its own self-check. That case belongs
to the test suite, and `TestHelperSelfCheck` is it.

Refusing rather than warning follows `tests/run § step 0a`'s own reasoning —
refusing costs a flag, and a warning in a verifier is a line an agent scrolls
past.

## 5. Mutations

Every mutation was planted in a throwaway `git init` repository or a temp
directory. **The live checkout was never written to** — the step-0 tree guard
confirms it below. Restores were verified against `git show`, not against a
snapshot; where the mutation target was a temp copy, the discard *is* the
restore and no snapshot exists to be circular about.

| # | what was mutated | anchor | result |
|---|---|---|---|
| 1 | `bin/perry-restore-check` — `ok=actual == committed,` → `ok=True,` | committed copy in a throwaway repo, line 142 | **red** — refuses (exit 2), `test_mutated_helper_refuses` |
| 2 | the same mutation, self-check waived with `--allow-modified-self` | as above | **red** — falsely passes a `MUTATED` file (exit 0), which is what proves mutation 1 bites; `test_the_mutation_would_otherwise_have_been_silent` |
| 3 | subject file corrupted *before* the snapshot | temp repo | **red** under the shipped tool (exit 1), green under the old check — `test_a_restore_onto_a_corrupted_baseline_is_caught` |
| 4 | `review.md` — explanation text pasted in as a second copy | temp copy of the file | **red** — `test_review_references_and_does_not_recopy` |
| 5 | `review-constraints.md` — section heading removed | temp copy | **red** — `test_constraints_carry_the_rule` |
| 6 | `review-constraints.md` — reason sentence removed, rule kept | temp copy | **red** — `test_the_rule_states_its_reason` |

**5 planted, 5 red, 0 green** on the guards. Mutation 2 is a deliberate
green-by-design control rather than a finding: it exists to show that the
mutation in row 1 really would have been silent without the self-check, which
is what makes row 1 mean something.

**One anchor did not match, and that is a finding about my own instrument.**
The first draft of `test_mutated_helper_refuses` replaced
`b"return actual == committed"` — a string that does not occur in
`bin/perry-restore-check`; the real line is `ok=actual == committed,`. The
substitution silently no-opped, the helper was never mutated, and the test
still passed. This is exactly the failure the brief names: *a non-matching
anchor silently no-ops and reports a meaningless OK*. `_planted_copy` now
asserts `after != before` before writing, so a stale anchor fails loudly
instead of producing a green that means nothing.

## 6. Tests

Baseline measured on this branch before any edit:

```
env -u PERRY_PROJECT bash tests/run
  1. schema drift guard                    ✓ clean
  2. 111 modules · 3134 tests · 356.5s     ✓ all green
  3. bin/ scripts parse and --help         ✓
  4. sample projects lint clean (en, zh)   ✓
  0. tree guard                            ✓ nothing moved
exit 0
```

After (results in § 7).

## 7. Results

Filled in after the post-change run; see the RESULT block reported with this
row.

## 8. What is deliberately not built

No check that inspects an agent's scratch directory for a bad harness. Those
are written ad hoc in temp directories no check can reach, the spec forbids it
in two places, and a guard that claimed to police the practice would be the
fourth guard-over-behaviour failure on this board this week. This row fixes the
**instruction** and ships an **opt-in tool**. It does not police anyone:
`bin/perry-restore-check` is called or it is not, and nothing fails if an agent
hand-rolls the loop correctly instead.

## 9. Files changed

| file | change |
|---|---|
| `work/reference/review-constraints.md` | **+1 section** — the rule, its reason, the control, the tool. The one home. |
| `work/reference/review.md` | **+1 sentence** in § 2 rule 2 — a pointer, no second copy |
| `bin/perry-restore-check` | **new** — the helper, with its own self-check |
| `bin/README.md` | **+1 table row** for the new tool |
| `tests/run` | `bin/perry-restore-check` added to step 3's parse-and-`--help` list |
| `tests/test_restore_check.py` | **new** — 14 tests: the control, the guidance, the helper, the helper's self-check |
| `perry/evidence/2026-09/TASK-256-result.md` | this file |

Nothing under `claims`, nothing in `schema/state-schema.json`, no push, no PR,
no merge, `main` untouched.
