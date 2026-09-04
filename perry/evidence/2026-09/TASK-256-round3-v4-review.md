# TASK-256 — round 3, V4 review

> Reviewer: dispatched review agent (fresh context; did not write this change)
> Criteria: `perry/evidence/2026-09/TASK-256-spec.md` — the only authority
> Answering: `perry/evidence/2026-09/TASK-256-round3-result.md`
> Under review: `main`, measurements pinned at `841124f`
> Result: **PASS**

The round-2 FAIL is fixed and I re-derived it from both sides rather than
taking it: the mutation the previous reviewer found green is red now, with
nothing skipped, and putting round 2's test file back makes it green again with
the false skip. The control the reviewer prescribed behaves as prescribed. I
planted 22 mutations of my own; 19 are red, three are green, and none of the
three can make the tool report a good restore over a bad one. Two rows fall out
and are named below.

---

## 0. Provenance, and how the measurements were taken

The worktree was handed over at `d49964e` — the stale cut this project keeps
producing, the same one all three previous rounds were handed. Verified rather
than assumed:

```
git log --oneline -1        d49964e chore: consolidate test suite and project state
git log --oneline -1 main   841124f TASK-283 and TASK-256 round 3 land; …
```

`main` is checked out in the primary worktree, so `git checkout main` is not
available here. The branch **`review/task-256-round3-v4`** was cut from `main`
explicitly (the name was checked against `git branch --list "*task-256*"`
first — `coding/task-256-restore-check`, `coding/task-256-round2`,
`coding/task-256-round3`, `review/task-256-v4` and `review/task-256-round2-v4`
already exist) and stub-committed with NOT-YET-CHECKED placeholders before any
reading, then committed again after each section.

All destructive work was done on a `git archive` copy of `main` under
`…/scratchpad/t256r3/copy`, `git init`-ed and committed so the module has an
object store of its own. The copy was checked against the live object store
**before anything was planted**, so every "restored" line below compares two
independently derived digests rather than a value against itself:

| file | copy | `main:` | copy `HEAD:` |
|---|---|---|---|
| `bin/perry-restore-check` | `8cd3027409dd` | `8cd3027409dd` | `8cd3027409dd` |
| `tests/test_restore_check.py` | `0be169d89fce` | `0be169d89fce` | `0be169d89fce` |
| `work/reference/review-constraints.md` | `05739202ac1a` | `05739202ac1a` | `05739202ac1a` |
| `bin/README.md` | `a1f09573cadd` | `a1f09573cadd` | `a1f09573cadd` |
| `work/reference/review.md` | `a318088fa53a` | `a318088fa53a` | `a318088fa53a` |

`bin/perry-restore-check` is at `8cd3027409dd…`, the digest rounds 2 and 3 both
report — **the tool is byte-identical to what round 2 shipped.** Round 3's claim
that it changed no code is true.

**`bin/perry-restore-check` was NOT used to verify any restore in this review.**
It is the subject. Every restore is `git show HEAD:<path>`, single path, one
file at a time; after each, the disk digest is compared to the object-store
digest and `git status --porcelain` is confirmed empty. Every plant is anchored
by line number **with an assert that the old text is present at that line** — a
non-matching anchor raises rather than no-opping into a false green. It fired
once, on `:265`, where I had guessed the line number one off; I re-anchored.
`__pycache__` is cleared before each run and after each restore, and each plant
waits past the whole-second boundary (`sleep(1.05 - time()%1)`).

**Baseline in the copy**: `ran=25 rc=0 n_failing=0 n_skipped=0`, tree clean.

The default temp directory is outside every repository on this machine, decided
by asking git rather than by argument:

```
tempdir = /var/folders/6g/…/T
git -C <tempdir> rev-parse --show-toplevel
  rc=128  fatal: not a git repository (or any of the parent directories): .git
```

---

## 1. Item 1 — re-planting the round-2 FAIL. **MET**

`bin/perry-restore-check:118`, `"unverifiable"` → `"clean"`:

```
E2  bin/perry-restore-check:118   ran=25 rc=1 RED n_failing=1 n_skipped=0
      RED: test_helper_outside_any_repository_refuses
    restored md5=8cd3027409dd782a5e0f11e2246acd2a matches_object=True tree_clean=True
```

**25 ran, 1 failure, no skip.** Exactly the shape the PMO measured, re-derived
rather than taken. The only line in the output containing the word "skip" is the
assertion message itself, which names the directory git was asked about:

```
precondition: git reports no work tree containing
/var/folders/6g/…/T/t256-loose-ur4vto3f, so self_check() must return
'unverifiable' — a helper that says anything else here is misreporting, which
is the whole point of this test and must not be allowed to skip it
```

**The causality control — the part that makes this more than a coincidence.**
Round 3 changed only the test. So I put round 2's test file back (`git show
9fe61142:tests/test_restore_check.py`) into the copy, left the tool alone, and
planted the identical mutation:

```
E2@r2  bin/perry-restore-check:118  ran=25 rc=0 *** GREEN *** n_skipped=1
       SKIP: the temp directory is itself inside a git repository,
             so this case is not reachable here
```

Green, with the false skip, on the identical tool. Red, with no skip, on round
3's. **The fix is the cause, measured from both sides**, and the round-2
reviewer's finding is reproduced rather than assumed.

`E2b` — the same branch broken a second, independent way (verdict *and* detail
rewritten, so the assertion is not pinned to one token) — is **RED** on the same
test. So is a third variant of my own, `N2`, which is the sharpest of the set:

```
N2  :118  "unverifiable" -> "modified"   ran=25 rc=1 RED
      RED: test_helper_outside_any_repository_refuses
```

`N2` matters because the tool's *behaviour* is unchanged under it — `"modified"`
is also `!= "clean"`, so the gate still refuses and the exit code is still 2.
The only thing that catches it is the round-3 assertion on the verdict itself.
That is the assertion doing work no other test in the module does.

## 2. Item 2 — the prescribed control, `TMPDIR` inside a real work tree. **MET**

A fix that turned the skip into an unconditional failure would be wrong. It did
not. A real repository was created at `…/t256r3/outer-repo`, git confirmed it
contains `outer-repo/tmp-in-repo` (`rc=0`, toplevel printed), and the module was
run with `TMPDIR` pointed there:

```
CTL  TMPDIR-in-repo (unmutated)   ran=25 rc=0 GREEN n_failing=0 n_skipped=1
Ran 25 tests in 5.380s
OK (skipped=1)
  SKIP: TMPDIR is itself inside a git repository (…/t256r3/outer-repo), so a
        helper placed there is not outside every repository and this case is
        unreachable on this machine — git said so, not the tool under test
```

`OK (skipped=1)`, exactly as round 3 reports. The reason printed is **true and
checkable**: it names the toplevel, and I verified independently that git does
report that toplevel for that directory. It also names who decided. This is the
opposite of round 2's message, which asserted something false about the
environment because it had inferred it from the subject of the test.

## 3. Item 3 — the declared residual. **ACCEPTABLE.** Measured, not conceded.

Round 3 states plainly that on a machine whose `TMPDIR` sits inside a
repository the test does not run and the mutation would be green there. I did
not take that on the round's word either — I planted E2 *with* `TMPDIR` inside
the work tree:

```
E2t  :118 "unverifiable" -> "clean"   [TMPDIR inside a repo]
     ran=25 rc=0 *** GREEN *** n_skipped=1
```

Green. The residual is real and is exactly as declared. **I judge it
acceptable**, and the reasons are not "it was declared":

1. **It is not the round-2 defect wearing new clothes.** The round-2 defect was
   that *the subject could switch the guard off*: mutate the tool and the guard
   disabled itself, on any machine, including this one. That is now impossible —
   no mutation of `bin/perry-restore-check` can reach the branch, because the
   branch is decided by `git rev-parse --show-toplevel` run against the loose
   directory, in a subprocess the tool has no part in. The residual is a
   property of the *machine*, not of the code under test. Those are different
   failure classes: one is self-disabling coverage, the other is an environment
   in which a case is genuinely unreachable.

2. **The skip is now honest, and honestly loud.** It prints the toplevel git
   reported, so a reader who doubts it can check it in one command — I did. A
   skip whose stated reason is verifiable is a report; round 2's was a false
   claim. `OK (skipped=1)` is also visible in the runner output rather than
   silent.

3. **The environment is not the one this project runs in, and that is measured
   rather than assumed.** `tempfile.gettempdir()` here is `/var/folders/…/T`,
   and git says rc=128 for it. A `TMPDIR` inside a work tree is a deliberate
   act, not a default: to reach it, someone has to export `TMPDIR` into a
   checkout. Nothing in `tests/run` does.

4. **Closing it fully would cost more than it buys, and the cheap closures are
   worse.** The alternatives are (a) fail when `TMPDIR` is inside a repo, which
   makes an environment choice look like a product defect and is the thing the
   reviewer explicitly warned against; (b) relocate the loose directory to a
   guaranteed-outside path, which trades a known-true skip for a new assumption
   about the filesystem that would itself need a guard; (c) test `self_check()`
   in-process with a stubbed `repo_root`, which stops testing the shipped
   script end-to-end and would not have caught round 1's finding at all.

5. **The blast radius is bounded and the row is not the last guard.** If this
   test silently stopped running on some machine, `:118` would be unpinned
   *there* — but `:215` (M5, N8), `:125` (E3), `:127` (E9) and the refusal exit
   code (N5) are all still red on that machine, so a wrong helper still has four
   other guards between it and a commit.

I would accept a follow-up that records the skip count in the suite output so
an environment that silently stops running it is visible. That is a
strengthening, not a condition of this PASS.

## 4. Item 4 — the round's own green, the `--root` sentence. **MET, both copies red**

Round 3 added a sentence to `review-constraints.md` and `bin/README.md`, found
that deleting it was pinned by nothing, and closed it with one assertion in
`test_the_documented_guarantee_matches_the_tool`. Both copies are red under
deletion, and I broke each of them two independent ways:

| # | site | mutation | result | red test |
|---|---|---|---|---|
| D1 | `review-constraints.md:92` | `--root <copy>` sentence → "somehow." | **RED** | `test_the_documented_guarantee_matches_the_tool` |
| D2 | `bin/README.md:31` | `--root <copy>` clause → "somehow." | **RED** | same |
| D2b | `bin/README.md:31` | the whole added clause deleted | **RED** | same |
| M6 | `review-constraints.md:90` | `--allow-modified-self` renamed | **RED** | same |
| M7 | `bin/README.md:31` | `--allow-modified-self` renamed | **RED** | same |

One green, and it is the declared limit rather than a finding:

```
D1b  review-constraints.md:91  "point the **live** repository's helper at the
     copy" -> "shrug"     ran=25 rc=0 *** GREEN ***
```

That mangles the sentence into nonsense while leaving the literal `` `--root
<copy>` `` on the page, so the substring guard still passes. Round 2 declared
this limit for its guard in writing, the round-2 reviewer confirmed it by
attack rather than discovering it, and round 3 declared it again for the new
assertion and put it in the docstring. Declaring a limit accurately is the
opposite of the defect. Not counted against the round.

## 5. Item 5 — my own mutations. **22 planted · 19 red · 3 GREEN**

Round 3's eight code mutations, re-derived rather than accepted — every one
reproduces with the same named tests:

| # | site | mutation | result | red tests |
|---|---|---|---|---|
| E2 | `:118` | `"unverifiable"` → `"clean"` | **RED** | `test_helper_outside_any_repository_refuses` |
| E2b | `:118` | verdict *and* detail rewritten | **RED** | same |
| M1 | `:255` | `all(...)` → `any(...)` | **RED** (2) | `test_a_bad_path_first_still_fails`, `test_one_bad_path_among_several_fails_the_whole_run` |
| M2 | `:139` | `ok=False, reason="outside-repo"` → `ok=True` | **RED** | `test_a_path_outside_the_repo_is_not_a_pass` |
| E3 | `:125` | absent-at-HEAD → `"clean"` | **RED** | `test_helper_absent_at_head_refuses` |
| E9 | `:127` | `"modified"` → `"clean"` | **RED** | `test_mutated_helper_refuses` |
| M5 | `:215` | `verdict != "clean"` → `== "modified"` | **RED** (2) | `test_helper_absent_at_head_refuses`, `test_helper_outside_any_repository_refuses` |
| M8 | `:159` | `ok=actual == committed` → `ok=True` | **RED** (7) | incl. `test_a_restore_onto_a_corrupted_baseline_is_caught`, `test_the_mutation_would_otherwise_have_been_silent` |

**Nine mutations of my own, six of them at sites no round has touched:**

| # | site | mutation | result | red tests |
|---|---|---|---|---|
| N2 | `:118` | `"unverifiable"` → `"modified"` (behaviour unchanged) | **RED** | `test_helper_outside_any_repository_refuses` |
| N3 | `:146` | `ok=False, reason="not-at-ref"` → `ok=True` | **RED** | `test_a_path_absent_at_the_ref_is_not_a_pass` |
| N4 | `:150` | `if not resolved.exists():` → `if False:` | **RED** | `test_a_path_missing_on_disk_is_not_a_pass` |
| N5 | `:236` | the refusal `return 2` → `return 0` | **RED** (3) | `test_helper_absent_at_head_refuses`, `test_helper_outside_any_repository_refuses`, `test_mutated_helper_refuses` |
| N7 | `:276` | `return 0 if ok else 1` → `return 0` | **RED** (3) | `test_differing_file_exits_one`, `test_the_ref_argument_is_honoured`, `test_a_restore_onto_a_corrupted_baseline_is_caught` |
| N8 | `:215` | `and not allow_modified_self` → `and False` | **RED** (3) | the three refusal tests |
| **N1** | `:89` | `repo_root` `return None` → `return probe` | **GREEN** | — |
| **N6** | `:199` | `--root=X` parsing → `root_arg = a` | **GREEN** | — |
| **N9** | `:265` | `if verdict != "clean":` → `if False:` | **GREEN** | — |

A green mutation is a finding, so each was measured rather than argued about.

**N1 is an equivalent mutant, and I established that by running it, not by
reading it.** `repo_root` returning the probe directory instead of `None`
changes nothing observable:

```
                            shipped                      n1
self_check verdict          'unverifiable'               'unverifiable'
  (detail)                  "… not inside a git repo"    "HEAD:… does not exist in …"
gate, no flags              rc=2 REFUSING                rc=2 REFUSING
path outside any repo       rc=2                         rc=2
path inside a repo          identical (rev-parse succeeds, the branch is dead)
```

The mutated branch only fires when `rev-parse` fails, and both routes out of
that end in `unverifiable` / exit 2. Only the human-readable detail string
differs. Nothing to fix.

**N6 fails loud.** `--root=DIR` is implemented but is not in the tool's own
usage line (`[--root DIR] [--json] [--allow-modified-self]`), so it is an
undocumented spelling. Broken, it does not answer wrongly — `root` becomes a
non-existent path, `rev-parse` fails and the tool exits 2 with
`HEAD is not a commit in --root=…`. A coverage hole in an undocumented
convenience whose failure mode is a refusal. Worth a line in a row, not a FAIL.

**N9 is a genuine hole and the one worth filing.** Suppressing `:265` removes
the `! self-check <verdict>: <detail>` line, and no test notices:

```
shipped, --allow-modified-self, loose helper:
  ! self-check unverifiable: …/perry-restore-check is not inside a git repository
    ✓ f.py matches HEAD (10036162d3c5…)        rc=0
n9, same call:
    ✓ f.py matches HEAD (10036162d3c5…)        rc=0
```

The round-2 reviewer's § 5 acceptance of the breaking change rested partly on
this line — *"the escape hatch … is not silent — the `!` line still prints, so
a waived self-check is visible in the transcript."* It is pinned by nothing.

**Why this is not the FAIL.** I traced the reachability rather than assuming
it: the gate at `:215` returns 2 whenever `verdict != "clean"` and the override
was not passed, so `:265` is reachable **only** for a caller who explicitly
passed `--allow-modified-self`. Under N9 the `ok` verdict, every `✓`/`✗` line
and both exit codes are unchanged — the tool cannot vouch for a bad restore,
which is the outcome the round-2 FAIL turned on (`e2m8` printed `✓` and exited
0 over a corrupt file). N9 costs a warning to an operator who asked to waive the
warning. By `review.md §` the finding line — *"a mutation comes back green |
V4 | the guard does not work, or the test does not test it"* — this is real and
it is mine to report, which I am doing; it is not a miss against a numbered
criterion of `TASK-256-spec.md`, whose Verification item 2 is about the *check*
going red, and the check does.

**Row to file: the `!` self-check advisory line is pinned by nothing.** One
assertion in `test_helper_absent_at_head_refuses` or a sibling —
`assertIn("! self-check", stdout)` on an `--allow-modified-self` run — closes
it. I did not write it: reviewers do not write.

## 6. A second row — the sentence round 3 added is not true of a `git archive` copy

Round 3 added, to both shipped pages, *"from a scratch copy the better move is
usually to point the **live** repository's helper at the copy with `--root
<copy>`, which answers correctly and needs no override."* The guard checks the
string is present. Nobody checked the advice works. I did, on the shipped tool:

| copy made by | `.git`? | live helper `--root <copy>`, honest | corrupt | copy's own helper, no flags |
|---|---|---|---|---|
| `git archive` extract | no | **rc=2** `HEAD is not a commit in <copy>` | **rc=2** same | rc=2 REFUSING |
| `cp -R` | yes | rc=0 `✓ bin/README.md matches HEAD` | rc=1 `✗ … does not match` | rc=1 `✗ …` |

The advice is true for a copy that carries an object store and **false for a
bare `git archive` extract** — which is the copy named two sentences earlier in
the very same paragraph (*"which is the case in a `git archive` scratch
copy"*). An agent hitting the refusal there and following the new sentence gets
a second exit 2.

**This is not a FAIL, on the project's own rubric.** `review.md`'s finding
table: *"a comment, a KR or a commit message misstates something | **file a
row** | a documentation defect with its own ID, never a FAIL on this one."*
It is also strictly an addition beyond the criteria — the round-2 reviewer
labelled it *"Optional, and not required to clear the FAIL"* — the failing case
was already unanswerable by every route (all four columns exit 2 for the bare
archive, so nothing regressed), and the failure is a loud refusal rather than a
wrong answer. But the sentence should say *a copy that has its own object store
(`cp -R`, or `git archive` + `git init` + a commit — what rounds 2 and 3 both
actually used)*, because a claim on a shipped page that is false for the
workflow the same paragraph names is the shape this project keeps paying for.

## 7. Item 6 — suite and lint. **MET**

PLACEHOLDER-SUITE

`python3 bin/perry-lint --root .` → **0 error(s), 37 warning(s)** — the same
count rounds 2 and 3 and the round-2 V4 review all report. The warnings are
pre-existing census lines (unbounded specs, blank summaries); none concerns
this change. Spec Verification item 4: **met**.

No linter for other people's harnesses was built. Spec Verification item 3:
**met**.

## 8. The question the project asked: can the standing warning narrow?

Every spec dispatched here for over a week warns agents not to use
`bin/perry-restore-check` and to use `git show <ref>:<path>` instead. The
round-2 reviewer said it must stand *"for now"* and that once § 3 closed it
should narrow to two permanent exclusions. **§ 3 is closed. It can now narrow
to exactly those two** — and I checked the specific thing that would block it,
which is whether any surviving green lets the tool report a good restore over a
bad one.

Every branch that decides `ok` or the exit code is now pinned, re-derived here:
`:139` (N3's sibling M2), `:146` (N3), `:150` (N4), `:159` (M8), `:255` (M1),
`:215` (M5, N8), `:236` (N5), `:276` (N7), and all three verdicts of
`self_check` — `:118` (E2, E2b, N2), `:125` (E3), `:127` (E9). My three greens
are the whole of what is not pinned, and none of them touches a verdict: N1 is
an equivalent mutant, N6 exits 2, and N9 removes an advisory line while leaving
`ok` and both exit codes intact.

The two exclusions, verified live rather than inherited:

1. **A round that touches `bin/perry-restore-check` itself must use `git
   show`.** Permanent and unfixable by any self-check — a wrong helper that has
   been *committed* passes its own self-check, which the tool's own docstring
   states. This review followed the rule; so did round 3.

2. **Any tree with tracked symlinks**, until `:134` stops deriving `rel` from
   `p.resolve()`. Re-derived on the shipped, unmutated tool at `main`:

   ```
   git status --porcelain           M link.py
   perry-restore-check --root <repo> HEAD <repo>/link.py
     ✓ other.py matches HEAD (b71bb12bb7a7…)      exit=0
   ```

   git calls the file modified; the tool reports a good restore, having
   silently answered about a different file. `git ls-tree -r main | grep
   ^120000` returns **0** tracked symlinks, so it is vacuous in Perry today and
   permanent until `:134` changes. `:134` is unchanged: `resolved = p.resolve()`.

**Nothing else blocks the narrowing.** One thing a narrowed brief should say
rather than exclude, because the tool reports it loudly rather than getting it
wrong: in a bare `git archive` scratch copy the helper cannot answer at all —
every route exits 2 (§ 6), because there is no object store to compare against.
That is a limit of the copy, not of the tool, and it is why the fallback in
`review-constraints.md` — `git -C <live-root> show <ref>:<rel>` — remains the
instrument for that case. Outside the two exclusions,
`bin/perry-restore-check <ref> <path> …` is the better instrument than a
hand-rolled loop.

Narrowing the warning is a **new row**, as round 3 says. This review is not it.

## 9. What I did not check

- **Windows and non-POSIX path handling.** macOS only.
- **The rounds that already consumed `bin/perry-restore-check`.** Not
  identified, not re-run.
- **Concurrency**, and the `TASK-298` shared-scratchpad collision.
- **The other 113 test modules** beyond the full-suite runs below.
- **The `--json` consumer contract** beyond reading the payload.
- **`perry-lint --reviews --strict`** — a pre-check, runs before dispatch.
- **The spec's `Remainder`** — the PMO's ephemeral briefs and the out-of-repo
  memory file, out of reach as the spec says.
- **One asymmetry I noticed and did not chase**: the new precondition asks git
  about `str(loose)` (`/var/folders/…`) while the helper asks about
  `SELF.resolve().parent` (`/private/var/folders/…`). On macOS these differ as
  strings. Both resolve to the same directory and no repository boundary sits
  between them, so the two questions cannot disagree here; on a filesystem
  where one could, they might. Not a defect I can demonstrate.

## 10. Verdict

The round was dispatched to fix one line-wide FAIL and it fixed it, in the
place the reviewer named, with the pattern the reviewer named, and it proved it
the way the reviewer asked. It kept the control the reviewer prescribed working
rather than converting the skip into a failure. It declared the residual
plainly, and the residual survives inspection because it is an environment
property that no mutation of the subject can reach — which is a different
failure class from the one that produced the round-2 FAIL. It found a green of
its own, in a sentence it had itself added, and closed it in the guard that
already existed rather than filing it. Its account of what it planted and what
came back is accurate in every particular I re-derived.

Two rows fall out — the unpinned `!` advisory line, and a sentence that is
false for the copy form its own paragraph names. Neither is a criterion miss;
by this project's own finding table the second is explicitly a filed row rather
than a FAIL, and the first cannot produce a wrong verdict.

PLACEHOLDER-RESULT
