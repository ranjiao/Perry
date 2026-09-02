# TASK-293 — round 2, V4 review

- **Reviewer**: fresh-context V4 agent, isolated worktree
  `.claude/worktrees/agent-a9139eef5dfb8c231`, branched from `main` at `d49964e`
- **Criteria**: `perry/evidence/2026-09/TASK-293-spec.md`, read from
  `coding/task-247-config-predicate`
- **Under review**: `0c42651` on `decide/task-293-reverse-index` (round 1 was
  `c85c49c`)
- **Round 1**: `perry/evidence/2026-09/TASK-293-round1-v4-review.md` — FAIL on
  one sub-claim inside D-02
- **Protocol**: `work/reference/review.md`,
  `work/reference/review-constraints.md`
- **Result**: **PASS**

I wrote nothing into the tree under review. `perry-lint` and `perry-decide` were
run against `git archive` copies in a private scratch subdirectory
(`…/scratchpad/v4-293-r2/copy-<ref>/`). No Perry write tool was run anywhere.

The author of the fix is the PMO — the same role that wrote the spec and that
wrote the sentence round 1 failed. I re-derived every figure with my own
instrument before reading the entry's, and I did not take the fix's arithmetic,
the commit message's arithmetic, or round 1's arithmetic as given.

---

## 1 · Scope of this round

Round 1 passed ten of eleven findings by re-implementation, and passed D-02's
substantive correction. It failed on `DESIGN-014:283`, which claimed
`__pycache__/*.pyc` is **tracked** in this repository and cited `5,994` and
`36,390` on that basis. I did not redo the ten. What follows is the failed
sub-claim, the fix for it, and the three things the fix could plausibly have
broken.

`0c42651` touches **one file**, `perry/design/DESIGN-014-how-much-python.md`,
in **one hunk**: 21 insertions, 5 deletions.

```
$ git diff --name-status c85c49c 0c42651
M       perry/design/DESIGN-014-how-much-python.md
$ git diff -U0 c85c49c 0c42651 | grep -c '^-[^-]'
5
```

---

## 2 · The three numbers, re-derived with git

I wrote my own counter rather than reading the entry's: for a ref and a prefix,
take every path `git ls-tree -r` reports, read each blob with `git show`, count
newlines, and classify Python by `*.py` or a `python` shebang on line 1 and
bash by `*.sh`/`*.bash` or a `bash`/`sh` shebang. Nothing touches a working
tree. Every tracked file under `bin/` ends in a newline at both refs, so newline
count and line count coincide and the instrument cannot be off by one.

| | `d3f9f4b` claimed | mine | `d49964e` claimed | mine |
|---|---|---|---|---|
| tracked files under `bin/`, all types | **30,396** | **30,396** (21 files) | **30,371** | **30,371** (21 files) |
| of which Python | **29,258** | **29,258** (16 files) | — | 29,233 (16) |
| of which `bash` | 842 | **842** (4 files) | 842 | **842** (4) |
| `bin/README.md` | 296 | **296** | 296 | **296** |

`29,258 + 842 + 296 = 30,396` and `29,233 + 842 + 296 = 30,371`. All three
figures the fix asserts reproduce exactly, from git, on a ref that cannot move.

Warning 2's four bash tools reproduce with them: `perry-codex-preflight` 150,
`perry-detect-host` 101, `perry-dispatch-limit` 404, `perry-update-check` 187
— sum 842, and those are the only four non-Python executables under `bin/`.

### The `.pyc` are untracked, and I can show where 36,390 came from

```
$ git ls-tree -r --name-only d3f9f4b | grep -c __pycache__      → 0
$ git ls-tree -r --name-only 0c42651 | grep -c pyc              → 1
      perry/knowledge/toolchain/pycache-staleness.md   ← a filename, not bytecode
$ git log --all --name-only --pretty=format: -- '*.pyc'         → empty
$ git log --all --name-only --pretty=format: -- '*__pycache__*' → empty
      (over `git rev-list --all` = 1,412 commits, not only the additions)
$ git ls-files | grep -c '\.pyc$'                               → 0
$ git show 0c42651:.gitignore | sed -n '11,12p'
      __pycache__/
      *.pyc
```

Round 1 checked additions only (`--diff-filter=A`); I checked every commit on
every ref, and the result is the same. The claim "no `.pyc` appears in any
commit in the repository's whole history" holds.

The complementary half of the fix's diagnosis — that these are machine-local
artefacts `find` sees and git does not — is directly demonstrable, and it is
what makes the correction the right correction rather than a plausible one:

```
$ find /Users/bytedance/proj/Perry/bin -name '*.pyc' | wc -l    → 5   (untracked)
$ find /Users/bytedance/proj/Perry/bin -type f -exec cat {} \; | wc -l → 34,363
$ (clean git-archive copy of 0c42651, no bytecode on disk)
  find bin -type f -exec cat {} \; | wc -l                      → 30,371
```

The developer checkout carries five untracked `.pyc` under `bin/` today and the
`find` sweep there returns **34,363** — not `36,390`, which is what it returned
whenever the original sentence was written, and not `30,371`, which is what git
says. Three different answers from one command on one repository. That is the
fix's claim ("a `find` sweep on any particular machine will differ by however
much bytecode happens to be sitting there, which is why no such number is
quoted here") measured rather than asserted, and it is why dropping the figure
rather than re-deriving it is the correct remedy.

`review.md § 2` rule 2 asks for mutation, and there is no code here to mutate.
The nearest available equivalent is this: rather than re-reading the corrected
sentence, I ran the discredited instrument on a third occasion and watched it
produce a third number. The claim the entry now makes is the one that survives
that.

---

## 3 · The recursive failure mode — does the corrected entry carry a bad number?

Every figure and factual claim introduced by `0c42651`, checked:

| written | verdict |
|---|---|
| `bin/README.md` (296) | ✅ |
| 842 lines of `bash` | ✅ |
| `d3f9f4b` bin/ tracked total **30,396** | ✅ |
| of which **29,258** Python | ✅ |
| `d49964e` same instrument **30,371** | ✅ |
| `.pyc` untracked, in no commit | ✅ (all 1,412 commits, all refs) |
| `git ls-files` returns none | ✅ |
| `.gitignore` lines 11-12 | ✅ verbatim, at those line numbers |
| "Corrected 2026-09-02 after a V4 FAIL" | ✅ commit dated 2026-09-02; round 1 was a FAIL |
| "first said the `.pyc` were *tracked*, and cited 5,994 and 36,390" | ✅ verbatim against the `c85c49c` blob |

Nothing new is unmeasured. The pinned ref `d3f9f4b` is a commit object, not a
branch name, so `30,396` and `29,258` will still resolve after the branch moves
— and it has: `coding/task-247-config-predicate` is at `5047ee4` today.

One wording nit, not a finding: the entry says *"The reviewer's proof was that
the false claim sat inside a warning written 'because this document's numbers
get re-cited'."* Round 1's `proof:` line was the falsity itself; the
re-citation point was the second of four reasons it failed the round rather
than being recorded as a nit. The characterisation is loose about which part
was the proof. It is a statement about a review document, not a number about
this repository, and it does not misrepresent the outcome.

---

## 4 · The declared departure — compliance, and here is why

Round 1's suggested remedy ended *"drops `5,994` and `36,390` altogether."* The
author dropped them as **claims** and kept them **named** in the correction
note, said so in the commit message, and invited this round to overrule it.

**I hold this is compliance.** Four reasons, in the order they weigh:

1. **The criteria file is the authority, and the review is not.** `review.md
   § 1`: the acceptance criteria are *"the only authority for PASS/FAIL"*.
   The spec's criterion is *"Every number and path you write reproduces."*
   `5,994` and `36,390` are not written here as measurements of anything —
   they appear only inside a sentence whose entire subject is that they were
   wrong, after the correct figure has been given with its ref. And as what
   they are actually asserted to be — *the figures this warning previously
   cited* — they reproduce exactly, against `c85c49c`'s blob. There is no
   reading of the corrected paragraph under which `36,390` is offered as the
   answer to anything.
2. **This is the spec's own house style, applied one level up.** The rule
   governing all eleven edits: *"Where a body sentence is now false, the
   `## Changes` entry says so and quotes it; the sentence stays. That is the
   whole point of an append-only record."* The spec asks every one of these
   entries to name the wrong thing rather than remove it. An entry that
   corrected itself by silent deletion would be the one document on the branch
   not doing what the branch is for.
3. **The figures are on the permanent record regardless, and deletion removes
   only the retraction.** `TASK-293-round1-v4-review.md` is committed on
   `coding/task-247-config-predicate` and quotes both numbers at length,
   including inside its machine-read `proof:` line. A future reader following
   the evidence trail meets `5,994` and `36,390` whatever DESIGN-014 says.
   Deleting them from DESIGN-014 would not unpublish them; it would delete the
   only pointer telling that reader they were retracted, which inverts the
   remedy.
4. **The residual risk round 1 named is addressed by placement.** The danger
   was that the paragraph is written *"because this document's numbers get
   re-cited"*. In the corrected text the reusable figure comes first, bolded,
   with its ref; the two retracted figures come last, in a sentence beginning
   *"This warning first said…"* and ending in the proof that they were false.

**Where the author's own argument does not carry.** The commit message
justifies this by *"an append-only record cannot correct itself by quietly
deleting the thing it got wrong."* That principle does not actually apply here,
and the author's own diff shows why: the five deleted lines were removed
outright, because the entry containing them was added by this branch and has
never merged (`git merge-base --is-ancestor c85c49c main` → false; the string
`find bin -type f` does not occur in `DESIGN-014` at `d49964e`). Nothing
append-only was violated by the deletion, so nothing append-only compelled the
naming either. The naming is right for reason 3, not for the reason given.
That is a weaker argument in support of a correct outcome — worth recording,
not worth failing.

Had the branch already merged, the calculus would be the same but the
justification stronger, and the deletion would itself have been the violation.

---

## 5 · The lock rule, and where the correction note sits

**Five deletions, all inside this branch's own unmerged entry.**

```
$ git show d49964e:perry/design/DESIGN-014-how-much-python.md | grep -c 'find bin -type f'
0
$ git merge-base --is-ancestor c85c49c main   → exit 1  (not merged)
```

The deleted text does not exist on `main`, in any shape. It was authored by
`c85c49c` eleven hours earlier on an unmerged branch. No locked body text is
touched: `DESIGN-014`'s header is `Status: locked · Date: 2026-09-01`, and the
document's sections are unchanged in count and position except inside `## 9.
Changes`.

**The correction note is inside the Changes entry; no new section exists.**

```
$ git show 0c42651:…DESIGN-014… | grep -n '^## '
  11 / 61 / 80 / 100 / 130 / 180 / 201 / 220 / 233 / 379
       ## 9. Changes  ← 233        ## 10. References ← 379
```

The hunk lands at 279–305, inside `## 9. Changes`, as the tail of list item 1
of the D-02 bullet. The same ten `## ` headings appear at `c85c49c`; only
`## 10. References` moves, by the 16 net lines added. Nothing in the repository
cites `DESIGN-014` by line number, so the shift breaks no citation.

### Gates

| | `c85c49c` | `0c42651` |
|---|---|---|
| `perry-lint --root .` (scratch copies) | 0 errors, 5 warnings | 0 errors, 5 warnings — identical set |
| `perry-decide list` | — | `11 active · 12 total`, 12 ADRs parsed |
| store lines printed by lint | six | six — tasks, risks, intake, ask, OKR, config |

The commit message's "perry-lint 0 errors before and after" is true. The six
store lines are D-03's subject and re-confirm it in passing.

---

## 6 · The two secondary items round 1 did not charge

**Both confirmed untaken, and leaving them is right.**

1. *D-02 cites the branch by a moving ref.* Still true. `§ 9`'s D-02 entry
   opens *"Re-measured 2026-09-02 on `coding/task-247-config-predicate`"*, and
   `§ 6` step 1's 40% arithmetic names the same ref. That ref was `d3f9f4b`
   when measured, `9bea506` at round 1, and `5047ee4` now. **The fix
   incidentally improved this**: `29,258` — the branch column's `bin/` figure —
   now also appears in the corrected warning pinned to `d3f9f4b`, so the
   document itself supplies the resolution for the number most likely to be
   re-cited. The remaining loose pointers are `tests/ 65,360`, `viewer/ 4,993`
   and the 41% line.
2. *D-01's exclusion list omits `viewer/.gitignore`.* Still true. The entry
   says *"(excluding `bin/README.md` and `__pycache__`)"*; `git ls-tree -r`
   under `bin/` and `viewer/` returns 24 paths, and `viewer/.gitignore` is the
   one a reader running the stated recipe is not told to drop. The resulting
   set is right — 44 + 46 + 150 + 101 + 187 + 387 = **915**, re-derived here —
   only the recipe is one exclusion short.

Neither belongs to this round. The spec's `## Bound` is eleven findings by id,
and `review.md § 1` is explicit that *"a round may only widen the bound by
filing a new row, never by re-opening this one."* Round 1 recorded both as not
charged; charging them in round 2 would be the round auditing the round's own
artifact, which `review.md § What V4 does not judge` names as the second reason
rounds do not converge. Item 1 is the better follow-up row of the two — it is
the same class of defect as the one that failed round 1 (a figure whose pointer
does not resolve), one step milder — but it is a row, not this round.

---

## 7 · What I did not check

- **The ten findings round 1 passed**, as substance: C-01, C-02, C-04, P-02,
  P-03, D-01's per-tool cross-check against all three `§ 5.1` tables, D-03's
  three "five" sites, D-04's `git log --follow` dates and `48fffba`'s diff,
  D-05a's line shift, D-05b's schema and `perry-decide` reading. I re-derived
  D-01's six line counts and total, D-02's `bin/`/`viewer/`/`tests/` figures and
  the six store lines because my own instrument produced them anyway; the rest I
  took from round 1, which re-implemented them.
- **D-02's prose figure, 9,887 / 53 files.** Round 1 re-walked `§ 1`'s
  definition; I did not. It is unchanged by `0c42651`.
- **Whether the author's disk carried exactly 5,994 lines of bytecode** when the
  original sentence was written. Unknowable in principle, which is the point;
  I verified only that the figure is not a repository fact and that today's
  sweep on that checkout returns something else again.
- **Mutation testing.** No code is under review — one markdown file, one hunk —
  and `review-constraints.md § You are a reader` forbids planting into the tree.
  See § 2 for what I ran instead.
- **The Python test suite.** No code changed; `test_parsers` is red for
  TASK-292 and other agents were running suites during this round, so no
  outcome would be attributable to `0c42651` either way.
- **The eight Out-of-scope findings** (G-01, G-04, C-03, C-05, P-01/G-03, P-04,
  L-01), beyond observing that `0c42651` edits one in-scope file.
- **The spec's declared subjective criterion** — *"whether each Changes entry
  says the right thing"* — which the spec reserves for a human reader. I judged
  the departure in § 4 because this round was asked to; I did not judge the
  prose.
- **`ADR-007`'s locked header figures** and the audit's own 19 findings across
  28 documents; the spec's eleven are the bound.
- **Whether the branch should merge.** I did not merge, push, or touch any ref
  outside my own worktree.

---

=== VERDICT ===
task: TASK-293
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-293-spec.md
checked: the three asserted figures re-derived with an independently written git-only counter (git ls-tree + git show + newline count, no working tree touched) — tracked files under bin/ total 30,396 at d3f9f4b of which 29,258 Python, and 30,371 at d49964e, with the decomposition 29,258 + 842 bash + 296 README closing exactly at both refs and every bin/ blob ending in a newline so line and newline counts coincide; warning 2's four bash tools 150/101/404/187 summing to the 842; the .pyc claim by four independent instruments — git ls-tree at d3f9f4b/d49964e/0c42651 (0 hits, the single "pyc" match being the filename perry/knowledge/toolchain/pycache-staleness.md), `git log --all --name-only -- '*.pyc' '*__pycache__*'` over every commit on every ref rather than round 1's additions-only filter (empty across 1,412 commits), `git ls-files` (0), and .gitignore lines 11-12 verbatim; the untracked-artefact diagnosis demonstrated rather than asserted — 5 untracked .pyc under bin/ in the developer checkout, `find bin -type f -exec cat` returning 34,363 there today against 30,371 on a clean git-archive copy of the same commit, a third value from the instrument that produced 36,390; the retraction sentence's report of what the entry previously said checked verbatim against the c85c49c blob; scope — one file, one hunk, 21 insertions / 5 deletions; the lock rule — the 5 deleted lines absent from DESIGN-014 at d49964e and the entry containing them added by c85c49c on a branch `git merge-base --is-ancestor c85c49c main` reports is not merged, DESIGN-014 header still `Status: locked`, no locked body text altered; the correction note's placement — same ten `## ` headings before and after, hunk at 279-305 inside `## 9. Changes` (233) and above `## 10. References` (379), no new section, and no file in the repository cites DESIGN-014 by line number so the 16-line shift breaks nothing; gates on git-archive scratch copies — perry-lint 0 errors / 5 warnings identical at c85c49c and 0c42651 with the same six store lines, perry-decide list parsing 12 ADRs at 11 active; both secondary items confirmed untaken, with D-01's 915 re-derived (44 + 46 + 150 + 101 + 187 + 387) and viewer/.gitignore confirmed as the 24th path the stated recipe does not exclude, and the moving ref confirmed to have advanced again to 5047ee4; the declared departure judged as compliance under the spec's own "the entry says so and quotes it" rule, the criteria file being the sole PASS/FAIL authority per review.md § 1, with the author's stated append-only justification recorded as not the reason that carries it. All destructive-looking work on git archive copies in a private scratch subdirectory; nothing written to the tree under review.
not-checked: the ten findings round 1 passed, as substance — C-01, C-02, C-04, P-02, P-03, D-01's per-tool cross-check against the three § 5.1 tables, D-03's three "five" sites, D-04's git log --follow dates and 48fffba's diff, D-05a's line shift, D-05b's schema and perry-decide reading — taken from round 1's re-implementation, except D-01's six line counts and total and D-02's bin/viewer/tests figures and the six store lines, which my own instrument produced anyway; D-02's prose figure 9,887 across 53 files, unchanged by 0c42651; whether the author's disk held exactly 5,994 lines of bytecode when the original sentence was written, unknowable in principle; mutation testing, there being no code in this change and planting into the tree being forbidden; the Python test suite, no code having changed and test_parsers being red for TASK-292; the eight Out-of-scope findings G-01/G-04/C-03/C-05/P-01/G-03/P-04/L-01; the spec's declared subjective criterion, "whether each Changes entry says the right thing", reserved for a human; ADR-007's locked header figures and the audit's own 19 findings across 28 documents; whether the branch should merge — I did not merge, push, or move any ref.
proof: n/a — PASS. The round-1 proof site, perry/design/DESIGN-014-how-much-python.md:283 at c85c49c, no longer exists: the sentence "`__pycache__/*.pyc` is *tracked* in this repository (5,994 newline-counted bytes of bytecode under `bin/`)" is one of the five lines deleted by 0c42651, and its replacement at DESIGN-014:290-291 ("at `d3f9f4b`, every tracked file under `bin/` totals **30,396** lines, of which **29,258** are Python") re-derives exactly under an independently written git-only instrument.
=== END VERDICT ===
