# TASK-256 — round 2, V4 review

> Reviewer: dispatched review agent (fresh context; did not write this change)
> Criteria: `perry/evidence/2026-09/TASK-256-spec.md` — the only authority
> Answering: `perry/evidence/2026-09/TASK-256-round2-result.md`
> Under review: `main`, measurements pinned at `651a5ca`
> Result: **FAIL**

The FAIL is one line wide and the fix is a two-line change. Everything the
dispatch brief named as the round's job is genuinely done, both halves, and I
re-derived every one of it. It fails on a ninth mutation the round did not
plant, in the exact branch of § 3 it claims to have closed.

---

## 0. Checkout provenance

The worktree was handed over at **`d49964e`** — the stale cut this project keeps
producing, and the same one both previous rounds were handed. Verified rather
than assumed:

```
git log --oneline -1          d49964e chore: consolidate test suite and project state
git log --oneline -1 main     651a5ca TASK-339 spec: remove the scanner, …
```

The branch `review/task-256-round2-v4` was cut from `main` explicitly and
stub-committed before any reading, then committed again after each section.

**`main` moved during this round**, from `651a5ca` to `1d3fd17` (`TASK-067`,
unrelated). `git diff 651a5ca main` over all four files this row touches is
**empty**, so nothing measured here is invalidated:

```
git diff --stat 651a5ca main -- bin/perry-restore-check tests/test_restore_check.py \
                                work/reference/review-constraints.md bin/README.md
(empty)
```

All destructive work was done on a `git archive` copy under
`…/scratchpad/t256r2-rev/copy`, `git init`-ed and committed so the helper has a
committed copy of itself to check against (round 2's own § 5 control did the
same, and it is what makes the self-check meaningful during a mutation run). The
copy was checked against the object store before anything was planted, so
"restored" below compares two independently derived digests rather than a value
against itself:

| file | copy | `git show HEAD:` |
|---|---|---|
| `bin/perry-restore-check` | `8cd3027409dd…` | `8cd3027409dd…` |
| `tests/test_restore_check.py` | `385b8890b93c…` | `385b8890b93c…` |
| `work/reference/review-constraints.md` | `95d6974424eb…` | `95d6974424eb…` |
| `bin/README.md` | `5f8d6ba5c785…` | `5f8d6ba5c785…` |
| `work/reference/review.md` | `a318088fa53a…` | `a318088fa53a…` |

These are the same four digests round 2's Control A reports, so the merged tree
is byte-identical to what the round measured.

**Restores were verified with `git show HEAD:<path>`, single path, one file at a
time — `bin/perry-restore-check` was deliberately NOT used**, it being the tool
under review. Every plant was anchored by line number *with an assert on the old
text at that line* (a non-matching anchor raises; it fired once, on the
paraphrase attack in § 7, and I re-anchored). `__pycache__` cleared before and
after each plant; each plant waited past the whole-second boundary
(`sleep(1.05 - time()%1)`). After every restore the disk digest was compared to
the object-store digest and `git status --porcelain` confirmed empty.

The live checkout was written to only for this file; its four subject files are
untouched and still hash to the four values above.

---

## 1. Item 1 — re-planting the round-1 FAIL. **MET**

`bin/perry-restore-check:255`, `all` → `any`, re-derived rather than taken:

```
M1  bin/perry-restore-check:255  'all(r["ok"] for r in results)' -> 'any(r["ok"] for r in results)'
    ran=25  rc=1  RED  n_failing=2
      - test_a_bad_path_first_still_fails
      - test_one_bad_path_among_several_fails_the_whole_run
    restored, tree clean, md5=8cd3027409dd782a5e0f11e2246acd2a
```

**Exactly the two tests the PMO named**, and no others — which is the right
shape: the new coverage is load-bearing and nothing else is covering for it.
Round 1 left all 15 tests green on this mutation; round 2's 25 go red on it.

The sibling branches of `check()` that round 1 found green are closed too:

| # | site | mutation | result | red tests |
|---|---|---|---|---|
| M2 | `:139` | `ok=False, reason="outside-repo"` → `ok=True` | **RED** | `test_a_path_outside_the_repo_is_not_a_pass` |
| M3 | `:146` | `ok=False, reason="not-at-ref"` → `ok=True` | **RED** | `test_a_path_absent_at_the_ref_is_not_a_pass` |
| M4 | `:150` | `if not resolved.exists():` → `if False:` | **RED** | `test_a_path_missing_on_disk_is_not_a_pass` |
| M8 | `:159` | `ok=actual == committed,` → `ok=True,` | **RED** (7) | `test_differing_file_exits_one`, `test_a_restore_onto_a_corrupted_baseline_is_caught`, `test_the_ref_argument_is_honoured`, + 4 |

M4 deserves a note in the round's favour. Round 1 recorded `:133` as a *genuine
equivalent mutant* for exit-code purposes — the missing file raises out of
`read_bytes()` and the process still exits 1. Round 2's decision to have the new
tests read the `--json` payload rather than only the exit code is what turns
that into a real RED (`results[0]["reason"] == "missing"`), and the round said so
in advance. That is a correct and non-obvious call, and I confirmed it bites.

## 2. Item 2 — re-planting the second half, `unverifiable`. **MET as behaviour**

The § 3 scenario reproduced from scratch: the shipped helper copied to a
directory that is not inside any repository, run against a file that does **not**
match its ref, **no flags**.

```
=== shipped — loose copy, no flags, corrupt subject.py ===
perry-restore-check: REFUSING — this script could not be checked against a committed copy.
    …/loose/shipped is not inside a git repository
  A verifier that has been changed, or that cannot show it has
  not been, cannot vouch for anything — and 'no comparison was
  made' is the more dangerous answer, not the safer one. …
exit=2
```

And with round-1 mutation 8 (`ok=actual == committed,` → `ok=True,`) planted
into that loose helper — the exact configuration that printed `✓` and exited 0
in round 1:

```
=== m8 — loose copy, no flags, corrupt subject.py ===
perry-restore-check: REFUSING — this script could not be checked against a committed copy.
exit=2
```

Round 1 gave `exit 0` and a false `✓` here. It now refuses. The gate itself is
guarded — reverting it to the literal round-1 line goes red:

| # | site | mutation | result | red tests |
|---|---|---|---|---|
| M5 | `:215` | `verdict != "clean"` → `verdict == "modified"` (the literal round-1 line) | **RED** | `test_helper_absent_at_head_refuses`, `test_helper_outside_any_repository_refuses` |
| E1 | `:215` | `and not allow_modified_self` → `and False` | **RED** (3) | + `test_mutated_helper_refuses` |
| E3 | `:125` | absent-at-HEAD `"unverifiable"` → `"clean"` | **RED** | `test_helper_absent_at_head_refuses` |
| E9 | `:127` | `"modified"` → `"clean"` | **RED** | `test_mutated_helper_refuses` |

The documents were corrected and both are guarded:

| # | site | mutation | result | red test |
|---|---|---|---|---|
| M6 | `review-constraints.md:90` | the override sentence removed | **RED** | `test_the_documented_guarantee_matches_the_tool` |
| M7 | `bin/README.md:31` | the override clause removed | **RED** | same |

**8 of the round's 8 reproduce as reported.** Nothing in its account was found
to be false about what it planted or what came back. The behaviour is fixed.
What is not established is that the *coverage* of it is real — § 3.

---

## 3. FINDING — a ninth mutation comes back GREEN, and it reopens the half of § 3 this round claims to have closed. **THE FAIL**

The round reports **"8 planted · 8 red · 0 GREEN."** I planted 17. Sixteen
behaved. One did not.

`bin/perry-restore-check:118` — the *not inside a git repository* branch of
`self_check()`, which is the branch § 3 is about:

```python
    root = repo_root(SELF)
    if root is None:
        return "unverifiable", f"{SELF} is not inside a git repository"
```

Flip that one token, `"unverifiable"` → `"clean"`:

```
E2  bin/perry-restore-check:118   ran=25  rc=0  *** GREEN ***  skipped=1
    restored, tree clean, md5=8cd3027409dd782a5e0f11e2246acd2a
```

**All 25 tests pass.** And the way they pass is the finding:

```
test_helper_outside_any_repository_refuses (TestHelperSelfCheck)
A `git archive` copy has no `.git` — and that is the prescribed workflow. ...
  skipped 'the temp directory is itself inside a git repository,
           so this case is not reachable here'
```

The one test written this round to close the outside-a-repository half of § 3
**skips itself**, and the reason it prints is false — the temp directory is not
inside a repository. The skip fires because the test establishes its own
precondition by *running the helper under test and asking it for its own
verdict* (`tests/test_restore_check.py:453-457`):

```python
probe = self.run_helper("--allow-modified-self", "--json", "HEAD", …, helper=dest)
if json.loads(probe.stdout)["self_check"] != "unverifiable":
    self.skipTest("the temp directory is itself inside a git "
                  "repository, so this case is not reachable here")
```

A helper that misreports the verdict therefore disables the guard whose whole
purpose is to catch it misreporting the verdict.

**This is not an unknowable subtlety.** The sibling test one method above,
`test_helper_absent_at_head_refuses`, establishes the same kind of precondition
with `assertEqual` — which *fails* rather than skips — and its comment says
exactly why: *"precondition: this helper must be unverifiable, not merely
modified — otherwise this test proves nothing."* That is why E3 is RED and E2 is
GREEN. The round wrote both methods, in the same class, in the same round, and
used the load-bearing pattern in one and the self-disabling one in the other.

### It is not an equivalent mutant, and it is worse than round 1

Four helper variants, all run from a loose directory with **no flags**, against
the same corrupt `subject.py` in a throwaway repository:

| variant | output | exit |
|---|---|---|
| `shipped` | `REFUSING — … not inside a git repository` | **2** |
| `m8` (round-1 mutation 8 only) | `REFUSING — …` | **2** |
| `e2` (this mutation only) | `✗ subject.py: … does not match HEAD` — **and no `!` line at all** | 1 |
| `e2m8` (both) | `  ✓ subject.py matches HEAD (06cc59c6d133…)` | **0** |

The `e2m8` row is round-1 § 3's false PASS, restored in full: a mutated verifier
vouching for a file that does not match its ref, from a scratch copy, with no
flags. It is **quieter than round 1 was** — round 1 at least printed
`! self-check unverifiable:` above the `✓`; under E2 the verdict is `"clean"`, so
that line is suppressed and there is no warning of any kind. The `e2` row shows
the same silence even without the second mutation.

### Which claim it falsifies, and whose code it is

It does not touch the aggregate verdict (§ 2.1 — genuinely closed, M1/E7 red).
It does not touch the gate (`:215` — M5/E1 red). It falsifies the round's
coverage claim for the **`unverifiable` refusal**, specifically its
outside-a-repository half — one of the two halves the round's headline says it
fixed, and the half its own prose calls *"exactly what a `git archive` scratch
copy is, the workflow `review-constraints.md § You are a reader` prescribes."*
Of § 3's two reachable cases, the round pinned the absent-at-HEAD one (E3 red)
and left the not-in-a-repository one pinned by nothing that can fail.

The mutated line is **pre-existing code the round left alone**. The test that
was supposed to pin it is **code the round wrote this round**, and is the reason
the mutation is invisible.

### Why this is a FAIL and not a filed row

Spec **Verification item 2**, in full: *"A named test asserts the guidance says
what it must. **If you ship a helper, the test mutates the helper and shows the
check go red.**"* Here the helper is mutated and the check stays green. That is
a miss against a numbered criterion, not a reviewer's extra demand — and it is
the identical criterion, and the identical shape, that round 1 failed on:
`work/reference/review.md § What V4 does not judge` — *"a mutation comes back
green | **V4** | the guard does not work, or the test does not test it."*

I record the aggravating fact plainly: the skip also means this test can stop
testing silently for an innocent reason — on any machine whose `TMPDIR` sits
inside a repository, it has never run at all and no one would know.

## 4. Item 3 — the controls. **MET**

A tool that refuses everything satisfies items 1 and 2 and is useless. It does
not refuse everything.

**Control A — a genuine restore still verifies OK, multi-path, no flags**, run
in the copy against this row's own four files:

```
  ✓ bin/perry-restore-check matches HEAD (8cd3027409dd…)
  ✓ tests/test_restore_check.py matches HEAD (385b8890b93c…)
  ✓ work/reference/review-constraints.md matches HEAD (95d6974424eb…)
  ✓ bin/README.md matches HEAD (5f8d6ba5c785…)
exit=0
```

Four paths, exit 0, **no `!` line** — the self-check returned `clean`, so the new
gate does not fire on the normal case. This is also the multi-path interface the
whole round-1 finding was about, exercised positively.

**Control B — `--allow-modified-self` still answers, in both directions**, from
the loose copy the new gate would otherwise refuse:

```
B1  corrupt file:   ! self-check unverifiable: …
                    ✗ subject.py: … does not match HEAD:subject.py     exit=1
B2  honest restore: ! self-check unverifiable: …
                    ✓ subject.py matches HEAD (06cc59c6d133…)          exit=0
```

The escape hatch works, discriminates correctly, and is **not silent** — the `!`
line still prints, so a waived self-check is visible in the transcript.

**Control C — the tool still says "bad" when things are bad in a real repo**:
Case B in § 5 below, exit 1 on a two-path call with one corrupt path.

## 5. Item 4 — the declared breaking change. **Not too broad.**

This is the judgement call, and the answer turned on measuring the cases rather
than reasoning about them. The round declares: *"An agent running the tool from a
scratch copy, or from a worktree cut before the tool landed, now gets exit 2
where it used to get an answer."* True. But the case that matters for reviewers
on this project — destructive work in a copy — is **not** the case that broke.

**Case A/B — the reviewer's actual workflow is unaffected, and needs no flag.**
A reviewer works destructively in a scratch copy and verifies restores using the
**live repository's own** helper via `--root`. The helper's `SELF` is then in the
live repo, clean, so the gate never fires:

```
$ <live>/bin/perry-restore-check --root <copy> HEAD <copy>/bin/perry-restore-check <copy>/bin/README.md
  ✓ bin/perry-restore-check matches HEAD (8cd3027409dd…)
  ✓ bin/README.md matches HEAD (5f8d6ba5c785…)
exit=0

# one path then corrupted in the copy
  ✓ bin/perry-restore-check matches HEAD (8cd3027409dd…)
  ✗ bin/README.md: … does not match HEAD:bin/README.md (19698 bytes on disk vs 19690 at ref)
exit=1
```

No flag, no `!` line, correct in both directions. This is how the tool should be
used from a copy and it costs nothing.

**Case C — the pure `git archive` copy was never answerable anyway, so the
refusal takes nothing away.** Running the archive copy's *own* helper against
the archive copy's own files:

```
no flags:                 REFUSING — … is not inside a git repository        exit=2
--allow-modified-self:    …/arch/bin/README.md is not in a git repository;
                          pass --root                                        exit=2
```

The escape hatch does not help here — and it should not, because a `git archive`
copy has **no object store**, so there is no independent source to compare
against and the tool could never have answered about it. Round 1 exited 2 in this
configuration too, for the same second reason. **Nothing regressed.**

**What genuinely narrowed** is one case: running a *detached copy of the helper*
against paths in a real repository. That went from "answers, with a warning
above the `✓`" to "exit 2". `--allow-modified-self` covers it completely
(Control B, both directions), the refusal message names the flag, and both
shipped pages now name it too.

**Verdict on the judgement call: the refusal is not too broad.** The dominant
reviewer workflow needs no flag; the workflow that now refuses was never capable
of a correct answer; the one real narrowing has a documented, working,
non-silent escape. The round's choice of refusal over a warning is also the
correct application of the round-1 author's own argument — *"a warning inside a
verifier is a line an agent scrolls past"* — to a warning that was printing to
**stdout, above a `✓`**. `unverifiable` means no comparison was made at all,
which is the more dangerous verdict, not the safer one. I agree with the call
and with the reasoning given for it.

The one thing I would ask for is not a narrowing but a sentence: neither shipped
page tells a reader working in a copy to *point the live helper at the copy with
`--root`*, which is the answer that needs no flag. Readers who hit the refusal
will reach for `--allow-modified-self` — the flag the message names — when the
better move is usually Case A. That is a documentation row, not part of this FAIL.

## 6. Item 5 — the standing "use `git show` instead" warning. Claim verified; **must stand, narrowable later.**

The round's § 6.1 claim, verified on the shipped, unmutated tool at `main`. A
throwaway repo with a tracked symlink `link.py -> real.py`, then retargeted to
`other.py`:

```
git status --porcelain          M link.py
git diff --stat                 link.py | 2 +-

$ perry-restore-check --root <repo> HEAD <repo>/link.py
  ✓ other.py matches HEAD (b71bb12bb7a7…)
exit=0
```

**Confirmed exactly as stated**, digest and all: git calls `link.py` modified and
the tool reports a good restore, having silently answered about a *different
file* — because `rel` is derived from `p.resolve()` at `:134`. Reachability is
also as stated: `git ls-tree -r main | awk '$1=="120000"'` returns **0** tracked
symlinks, so no agent verifying a Perry restore can hit it today.

**But the round's framing is overstated.** It calls the symlink hole *"the one
reason the warning cannot be retired unconditionally."* It is not the only one.
The tool's own docstring names a second, which the round did not carry into that
sentence:

> *The hole it does NOT close, stated plainly rather than papered over: a wrong
> helper that has been **committed** passes its own self-check.*

That hole is live, and § 3 is precisely what makes it matter: the guard against a
wrong helper reaching a commit is `tests/test_restore_check.py`, and one branch
of it can be broken without any test failing. A committed helper carrying E2
would pass its own self-check, pass the suite, and answer from scratch copies
with no warning at all.

**So: must stand — for now.** Not because the tool is bad; on the evidence above
it is sound for ordinary use on this repository. Because the specific thing the
warning protects against is a wrong helper vouching for a bad restore, and this
review found the coverage against that outcome incomplete in exactly the
configuration reviewers work in.

Once § 3 is closed, the warning should be **narrowed rather than retired**, to
two permanent exclusions:

1. **A round that touches `bin/perry-restore-check` itself must use `git show`.**
   Permanent and unfixable by any self-check — the committed-wrong-helper hole is
   structural. This review followed that rule and so did round 2.
2. **Any tree with tracked symlinks**, until `:134` derives `rel` from the
   unresolved path. Vacuous in Perry today (0 symlinks) but the tool takes
   `--root` and arbitrary paths.

Outside those two, `bin/perry-restore-check <ref> <path> …` is the better
instrument than a hand-rolled loop, and Case A is the form to prescribe.

## 7. Item 6 — suite and lint. **MET**

`bash tests/run` on this branch, foreground, full run:

```
114 modules · 3291 tests · 136.4s · 8 workers
✓ all green
0. tree guard — the tree the suite started in is the tree it ends in
  ✓ nothing under …/agent-a04004b1b0b6a71d1 moved
EXIT=0
```

**Fully green, exit 0, tree guard clean at both ends.** The two
`test_contract_key_parity` wall-clock reds round 2 reported (TASK-335,
`bin/perry-task:6303`) **did not reproduce** — that module is green here. The
round's diagnosis was that they are a function of wall-clock drift against the
live board; the board has since moved and the condition is no longer tripped,
which is consistent with the diagnosis and independent of this row either way.
Round 2 reported 3278 tests; `main` has gained rows since. Not one bit redder.

`python3 bin/perry-lint --root .` → **0 error(s), 37 warning(s)** — the same
count round 2 reported. The warnings are pre-existing census lines (unbounded
specs, blank summaries); none concerns this change. Spec Verification item 4:
**met**.

No linter for other people's harnesses was built. Spec Verification item 3:
**met**.

## 8. The six findings the round left unfixed — judging each

Leaving all six was **correct**, and the round's descriptions of them are honest.
I checked three of the six rather than accepting them.

1. **§ 4 `resolve()` follows symlinks.** Correct to leave — reviewer-assigned to
   its own row in round 1 § 5, and `review.md § What V4 does not judge` puts
   reviewer-assigned rows outside this FAIL. Verified live (§ 6 above); the
   round's account is accurate, its "one reason" framing is not.
2. **§ 5.1 the one-home principle ships four copies.** Correct to leave, and the
   round did what the reviewer actually asked — *correct the sentence in the
   result document* — by stating flatly that the round-1 claim is **false**.
   Verified: `grep -rl "cannot fail when the write succeeds"` returns exactly
   four files — `review-constraints.md`, `bin/perry-restore-check`,
   `bin/README.md`, `tests/test_restore_check.py`. Declining to reduce the count
   is defensible: a tool's `--help` and a test's docstring explaining themselves
   is not the copy-paste defect the principle is aimed at.
3. **§ 5.2 both one-home guards are literal-substring guards, and so is the new
   one.** Correct to leave, and the self-declaration is **true** — I attacked the
   round's own new guard with the paraphrase it says defeats it: the corrected
   guarantee in `review-constraints.md:86-88` replaced by the old *unconditional*
   claim while leaving `--allow-modified-self` on the page at `:90`.
   **GREEN — guard defeated**, all 25 tests pass. The round predicted this in
   writing before I ran it. Declaring a limit accurately is the opposite of the
   defect; it is the reason this is not a second finding.
4. **§ 5.3 the `review.md` pointer is invisible to `test_pointers_resolve`.**
   Correct to leave — round 1 assigned it to its own row and rated it low risk,
   the heading rename being caught from the other side.
5. **The `test_contract_key_parity` wall-clock reds.** Correct to leave, and the
   round proved they were not its own the right way — by re-running an identical
   stub tree as a real repo at the same moment. TASK-335. Green for me anyway.
6. **The cross-worktree tree-guard artifact** it observed and did not chase.
   Correct to report rather than chase; it is a different row.

## 9. What I did not check

- **Windows and non-POSIX path handling.** macOS only.
- **The rounds that already consumed `bin/perry-restore-check`.** I did not
  identify or re-run them. Any that ran a detached helper from a scratch copy got
  an `unverifiable` answer that this change now refuses.
- **Concurrency**, and the `TASK-298` shared-scratchpad collision.
- **The other 113 test modules**, beyond one full-suite run.
- **The `--json` consumer contract** beyond reading the payload; nothing outside
  this module pins `results[].reason`, which the new tests now depend on.
- **`perry-lint --reviews --strict`** — a pre-check, runs before dispatch.
- **The spec's `Remainder`** — the PMO's ephemeral briefs and the out-of-repo
  memory file, out of reach as the spec says.
- **`.gitattributes` / `core.autocrlf`** — absent in this repo; confirmed absent
  rather than exercised. Any such conversion errs safe (false mismatch, exit 1).

## 10. What would clear this

One change, plus its control.

1. **`tests/test_restore_check.py:453-457` — determine the precondition
   independently of the helper under test.** Ask git directly whether the temp
   directory is inside a repository (`git rev-parse --show-toplevel`, or
   `Path('.git')` lookup up the chain); if it is not, **assert** — do not skip —
   that `self_check()` returns `unverifiable`, exactly as
   `test_helper_absent_at_head_refuses` already does one method above. Keep the
   skip only for the genuine environment case it was written for (a `TMPDIR`
   that really is inside a repository), decided by git rather than by the
   subject of the test.
2. **The control that proves it:** plant `:118` `"unverifiable"` → `"clean"` and
   show the module go **red**, naming the test. That is the mutation this review
   found green.

Optional, and not required to clear the FAIL: a sentence on both shipped pages
telling a reader working in a copy to point the live helper at it with `--root`
(§ 5), so the refusal message does not steer everyone to the override flag.

The round is otherwise strong work. Both halves the brief named are genuinely
fixed and I re-derived every mutation it claimed. It corrected a false claim in
its predecessor's result rather than inheriting it, declared the limit of its own
new guard before anyone attacked it — accurately, as I confirmed — declared a
breaking change before it was discovered, and refused its own baseline once a
second measurement disagreed with the first. It fails on the same class of defect
it was dispatched to fix, one branch over, in the half of the finding it added
to the brief itself.

=== VERDICT ===
task: TASK-256
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-256-spec.md
checked: worktree provenance (handed over at d49964e; branch cut from main at
         651a5ca and stub-committed; main moved to 1d3fd17 mid-round, diff over
         all four subject files empty); archive copy checked against the object
         store before anything was planted (5 files, all digests SAME); 17
         mutations planted line-anchored WITH an assert on the old text — the
         anchor guard fired once and was re-anchored — __pycache__ cleared and
         the whole-second boundary waited past on every plant, every restore by
         `git show HEAD:<path>` single-path with the disk digest compared to the
         object-store digest and `git status --porcelain` empty after each;
         bin/perry-restore-check NEVER used for any restore in this review; all
         8 of the round's own mutations re-derived (8 red, named tests match);
         9 further mutations of my own at :118, :122, :127, :215, :255, :263,
         :276; the § 3 scenario reproduced end-to-end with four helper variants
         from a loose directory; controls A (4 paths, exit 0, no `!` line) and B
         (--allow-modified-self, exit 1 and exit 0); the breaking change mapped
         across three configurations (live helper + --root at a copy; archive
         copy's own helper with and without the override); the § 4 symlink
         false-PASS reproduced on the shipped unmutated tool with 0 tracked
         symlinks confirmed on main; the four copies of the reason sentence
         enumerated; the round's own declared guard limit attacked and confirmed
         green; full suite `bash tests/run` (114 modules · 3291 tests · all
         green · exit 0 · tree guard clean); `perry-lint --root .` (0 errors,
         37 warnings)
not-checked: Windows/non-POSIX paths; the rounds that already consumed the tool;
         concurrency and the TASK-298 scratchpad collision; the other 113 test
         modules beyond one full-suite run; the --json consumer contract beyond
         reading the payload; `perry-lint --reviews --strict` (pre-check); the
         spec's Remainder; .gitattributes/autocrlf (absent, confirmed not
         exercised)
proof: bin/perry-restore-check:118 `return "unverifiable", f"{SELF} is not
         inside a git repository"` — change "unverifiable" to "clean" and all 25
         tests in tests/test_restore_check.py stay GREEN (rc=0, skipped=1). The
         one test written this round to close the outside-a-repository half of
         round-1 § 3, test_helper_outside_any_repository_refuses, SKIPS itself
         and prints a reason that is false, because it establishes its own
         precondition by running the helper under test and asking it for its own
         verdict (tests/test_restore_check.py:453-457, `if
         json.loads(probe.stdout)["self_check"] != "unverifiable":
         self.skipTest(...)`): a helper that misreports the verdict disables the
         guard that exists to catch it misreporting the verdict. The sibling
         test one method above, test_helper_absent_at_head_refuses, uses
         assertEqual for the same precondition and is therefore RED under the
         analogous mutation at :125 — the round wrote both, in the same class,
         and used the load-bearing pattern in one and the self-disabling one in
         the other. The mutant is not benign and is strictly worse than round 1:
         run from a loose directory with no flags against a file that does not
         match its ref, the helper carrying :118 plus round-1 mutation 8 prints
         "✓ subject.py matches HEAD (06cc59c6d133…)" and exits 0 — with NO `!`
         self-check line at all, since verdict=="clean" suppresses the warning
         round 1 at least printed. Spec Verification item 2 requires that
         mutating the shipped helper shows the check go red; this is the same
         criterion and the same shape round 1 failed on. The round's headline
         count "8 planted · 8 red · 0 GREEN" is thereby falsified. Separately
         GREEN and NOT part of this finding: :122, the `except ValueError`
         branch carrying `# pragma: no cover - repo_root guarantees
         containment` — a genuine equivalent mutant on an unreachable branch,
         correctly annotated in the source; and the paraphrase attack on
         review-constraints.md:86-88, which is the literal-substring limit the
         round declared in writing for its own new guard before I tested it, and
         which I confirmed rather than discovered.
=== END VERDICT ===
