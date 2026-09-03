# TASK-256 — round 1, V4 review

> Reviewer: dispatched review agent (fresh context; did not write this change)
> Criteria: `perry/evidence/2026-09/TASK-256-spec.md` — the only authority
> Under review: `main` at `c506ca5`
> Result: **FAIL**

## 0. Checkout provenance

The worktree was handed over at **`d49964e`**, the known-bad cut this project
keeps producing — **211 commits behind `main`**, and it predates the row
entirely. Verified rather than assumed:

```
git rev-parse HEAD                      d49964eee33940108893aa7f4edeb4e49e4ef668
git merge-base HEAD main                d49964e…      (ancestor, not diverged)
git rev-list --count HEAD..main         211
```

Every path named in the brief resolves at `main`, checked before any reading
began (`git cat-file -e main:<path>` for the spec, the result and the tool). All
reading was therefore done through `git show main:<path>`, and all execution on
`git archive main` copies under a uniquely named scratch directory
(`…/scratchpad/t256-rev-9f3a1c/copy`, `…/copy2`). **The live checkout was never
written to**; `git status --porcelain` was empty at the start and the only write
this round made anywhere in the repository is this file.

The archive copies were checked against the object store before anything was
planted, so the "restored" column below compares two independently derived
digests rather than a value against itself:

```
bin/perry-restore-check                 copy f4e78142f531 = main f4e78142f531
tests/test_restore_check.py             copy becb6ba495d6 = main becb6ba495d6
work/reference/review-constraints.md    copy 1ab26f7156ac = main 1ab26f7156ac
work/reference/review.md                copy a318088fa53a = main a318088fa53a
work/reference/dispatch.md              copy a84915769dad = main a84915769dad
work/reference/delegate.md              copy 8f26f4532444 = main 8f26f4532444
tests/run · bin/README.md · durations.json                    all SAME
```

**`main` moved during this round**, from `c506ca5` to `7b8951e` (one commit,
`TASK-066`, unrelated). `git diff c506ca5 main` over every file this row touches
is **empty**, so nothing measured here is invalidated. This branch sits at
`7b8951e` so its citations resolve; the measurements are pinned to `c506ca5`.

Restores were verified with `git show main:<path>` read out of the original
repository's object store — **not** with `bin/perry-restore-check`, which is the
thing under review (rule 2).

---

## 1. What holds

Confirmed rather than accepted. Every item below was executed.

**The bound is real.** The spec's own enumeration command, run verbatim on
`main`, returns the three sites this change added and nothing else. The `Size`
line's claim of *0 sites before* is consistent with that.

**The `dispatch.md` / `delegate.md` scope call is correct.** The author's stated
ground was that neither file contains any occurrence of `mutat`. Checked, both
case-sensitively and with `-i`: **exit 1, no output**, on two files of 29 429 and
10 135 bytes. Neither page prescribes the harness, so a pointer added to either
would be a reference with no caller. The call is right and the ground given for
it is true.

**The circularity control is two-directional and cannot rot.** This is the
sharpest thing in the test module and it survives being attacked from three
sides — each planted line-anchored, with an assert on the old text, restores
verified against `git show main:<path>`:

| planted in `tests/test_restore_check.py` | result |
|---|---|
| `old_ok = md5(f) == BASE[1]` → an independent comparison (the old check made to look like it catches the corrupted baseline) | **RED** — `test_old_check_misses_a_corrupted_baseline` |
| `new_ok = f.read_bytes() == truth` → `md5(f) == BASE[1]` (the new check made circular) | **RED** — `test_new_check_catches_a_corrupted_baseline` |
| the corrupt-before-snapshot setup removed entirely | **RED** — `test_new_check_catches_a_corrupted_baseline` |

The author's claim that the control asserts the **old check does pass** the
corrupted baseline is true, and it is what makes the first row above red. The
demonstration cannot decay into one that demonstrates nothing. Spec Verification
item 1: **met**.

**The guidance mutations are red.** Author's mutations 4, 5 and 6, re-planted:

| planted | result |
|---|---|
| `review-constraints.md:53` section heading renamed away | **RED** ×2 (`test_constraints_carry_the_rule`, `test_the_section_exists_in_exactly_one_file`) |
| `review-constraints.md:70` reason sentence gutted, rule kept | **RED** (`test_the_rule_states_its_reason`) |
| `review-constraints.md:56` `git show <ref>:<path>` removed from the rule | **RED** (`test_constraints_carry_the_rule`) |
| `review.md:157` the pointer replaced by a verbatim second copy of the reason | **RED** (`test_review_references_and_does_not_recopy`) |

**The green mutation the author found is genuinely closed.** Re-planted at
`bin/perry-restore-check:83`, `f"{ref}:{rel}"` → `f"HEAD:{rel}"`:

```
RED  exit=1
  FAIL: test_the_ref_argument_is_honoured
  restore bin/perry-restore-check == git show main:bin/perry-restore-check -> True
        (md5 f4e78142f531 vs f4e78142f531)
```

Exactly one test fails, and it is the one the finding bought. That is the right
shape: the fix is load-bearing and nothing else was covering for it.

**Three more helper mutations are red**, including the two that matter for the
self-check:

| planted in `bin/perry-restore-check` | result |
|---|---|
| `:142` `ok=actual == committed,` → `ok=True,` | **RED**, 5 tests |
| `:198` the refusal gate → `if False:` | **RED** (`test_mutated_helper_refuses`) |
| `:109` `if committed != SELF.read_bytes():` → `if False:` | **RED** (`test_mutated_helper_refuses`) |
| `:224` the bad-ref usage guard disabled | **RED** (`test_bad_ref_is_a_usage_error_not_a_pass`) |

**Exit 2 is reachable in every argument-shaped way that matters.** Enumerated
and each one executed: `--root` with no value, unknown option, fewer than two
positionals, no positionals, a path outside any git repo, a ref that is not a
commit, a tree-ish that is not a commit, and `--root` at a non-repo directory —
**all exit 2** with a specific message. `-h` exits 0 and prints the docstring.

**Suite and lint.** `bash tests/run` on the archive copy: **114 modules · 3258
tests · 397.9s · all green, exit 0**, tree guard clean at both ends.
`python3 bin/perry-lint --root .` → **0 errors**, 37 warnings, all pre-existing
and none about this change. Spec Verification item 4: **met**. (The author
reported 112/3149 and 26 warnings on their branch; `main` has gained modules and
rows since. The suite is green, so "no redder than the baseline" holds.)

**No linter for other people's harnesses was built.** Spec Verification item 3:
**met**.

The author's tally — 9 planted, 8 red, 1 green-by-design control, 1 GREEN found
and closed — **is confirmed**. Nothing in the account was found to be false about
what it planted or what came back.

---

## 2. Finding — three helper mutations come back GREEN, and one of them makes the tool vouch for a corrupt file

This is the FAIL. It is the same class of finding the author found and closed at
mutation 9, in the same function, and it is unclosed.

### 2.1 The multi-path verdict is unguarded

`bin/perry-restore-check:231`

```python
ok = all(r["ok"] for r in results)
```

Change `all` to `any` and **all 15 tests in `tests/test_restore_check.py` stay
green.** Nothing in the module passes more than one path — checked
mechanically: every one of the ten `run_helper(...)` call sites passes exactly
one.

The mutant is not benign. In a two-file repository where `a.py` was restored and
`b.py` was not:

```
shipped  (all)   exit 1
  ✓ a.py matches HEAD (bf072e911907…)
  ✗ b.py: b.py does not match HEAD:b.py (8 bytes on disk vs 2 at ref)

mutant   (any)   exit 0        <-- vouches for a corrupt file
```

Multi-path is the **documented** interface, in both places this row wrote it
down:

- `bin/perry-restore-check:25` — `perry-restore-check <ref> <path> [<path> ...]`
- `work/reference/review-constraints.md:85` — `` `bin/perry-restore-check <ref> <path> …` ``

and it is the natural call for a round that mutated several files and verifies
them in one go — which is what a round following the new rule does. The shipped
line is correct; the guard over it does not exist, so the aggregation across
paths is verified by nothing.

Spec **Verification item 2** says, in full: *"A named test asserts the guidance
says what it must. **If you ship a helper, the test mutates the helper and shows
the check go red.**"* Here the helper is mutated and the check stays green. That
is a miss against a numbered criterion, not a reviewer's extra demand.
`work/reference/review.md § What V4 does not judge` places it precisely: *"a
mutation comes back green | **V4** | the guard does not work, or the test does
not test it … This is a product finding wearing a test's clothes."*

### 2.2 Two sibling branches of `check()`, same class

Both flip to a false OK under a one-token edit and both stay green:

| planted | result |
|---|---|
| `:122` `entry.update(ok=False, reason="outside-repo",` → `ok=True` | **GREEN** |
| `:129` `entry.update(ok=False, reason="not-at-ref",` → `ok=True` | **GREEN** |

`:129` is the one with a real caller. A round pins its baseline to the commit it
was cut from — *which is what the new rule tells agents to do* — and asks about a
file the branch **added**. That path does not exist at the ref, `blob_at` returns
`None`, and the only thing between that and a reported PASS is an untested
`ok=False`.

Every `ok=False` branch in `check()` is untested. Only the `ok=actual ==
committed` line is covered.

### 2.3 A near-equivalent mutant, recorded rather than counted

`:133` `if not resolved.exists():` → `if False:` is also green, but the missing
file then raises out of `read_bytes()` and the process still exits 1. The
observable verdict is unchanged, so this is a genuine equivalent mutant for
exit-code purposes and is **not** part of the finding. Recorded because rule 2
says a green mutation is a finding either way, and the honest answer here is
"no-op", not "hole."

---

## 3. Finding — the self-check's advertised guarantee is false in the configuration this project prescribes

The brief asked whether exit 2 is reachable in the ways that matter and whether
the tool ever vouches when it should not. It does.

`self_check()` returns **three** verdicts — `clean`, `modified`, `unverifiable`
(`:99`–`:111`). `main()` gates the refusal on one of them:

```python
# bin/perry-restore-check:198
if verdict == "modified" and not allow_modified_self:
```

`unverifiable` is returned when the script is **not inside a git repository**
(`:101`) or when **`HEAD:<self>` does not exist** (`:108`). In both cases the
tool prints one `!` line to *stdout* and answers anyway.

Both are reachable, and the first is reachable by the workflow this project's own
constraints file prescribes: `review-constraints.md § You are a reader` says
*"copy the project to a scratch directory and work there"* and *"Plant into a
copy"*; the brief for this very round says *"Destructive work on `git archive`
copies."* **A `git archive` copy has no `.git`.** A scratch copy is also exactly
where a helper gets edited.

Demonstrated with the author's own mutation 8 (`ok=actual == committed,` →
`ok=True,`) planted into a helper sitting outside any repository, run with **no
flags**, against a file that does **not** match its ref:

```
exit: 0
  ! self-check unverifiable: …/bin/perry-restore-check is not inside a git repository
  ✓ subject.py matches HEAD (f9d9dc2bab25…)

--json:  "ok": true,  "self_check": "unverifiable",
         "expected_md5": "f9d9dc2bab2572ba95cfd67b596a6d1a",
         "actual_md5":   "5074fa3a71ce62b2c587d5b4e324f96f"
```

The two digests in its own JSON output disagree and it reports `ok: true`. The
same happens when the helper is present on disk but absent at `HEAD` — a worktree
cut before the tool landed, which is the standing condition on this board.

Two shipped documents state the guarantee without qualification:

- `work/reference/review-constraints.md:86-88` — *"refuses to answer while its
  own bytes differ from the copy committed in its repository."*
- `bin/README.md:31` — *"Refuses to answer while its own bytes differ from the
  copy committed in its repository."*

Neither is true when there is no committed copy to differ from — which is the
strictly more dangerous case, not the safer one. The result document names the
uncovered hole as *"a wrong helper that has been **committed** passes its own
self-check"*; this is a second, undisclosed hole, in the opposite direction.

The author's own quoted reasoning decides this: refusal was chosen over a warning
because *"a warning inside a verifier is a line an agent scrolls past."* That
reasoning was applied to `modified` and not to `unverifiable`, and `unverifiable`
prints its warning to **stdout**, where it sits above a `✓`.

`bin/perry-restore-check:198` is the line. Gating on `verdict != "clean"` would
close it, with `--allow-modified-self` (or a sibling flag) as the stated escape.

---

## 4. Finding — the tool answers about a different file than the one it was asked about

`bin/perry-restore-check:117`

```python
resolved = p.resolve()
```

`resolve()` follows symlinks, and `rel` is derived from the **resolved** path. So
the tool silently substitutes a symlink's target for the path it was given. With
an unmodified, unmutated helper:

```
repo: link.py -> real.py (tracked), other.py (tracked, unmodified)
then: link.py retargeted to other.py
git status --porcelain          M link.py
git diff --stat                 link.py | 2 +-

perry-restore-check HEAD link.py   ->  exit 0
  ✓ other.py matches HEAD (b71bb12bb7a7…)
```

`link.py` is modified in git's eyes and the tool reports a good restore. This is
the shipped tool reporting PASS over a file that is wrong.

**Reachability, stated honestly:** `git ls-tree -r main` finds **no** tracked
symlinks in this repository, so no agent verifying a Perry restore can hit it
today. The tool takes `--root` and arbitrary paths and is presented in
`review-constraints.md` as *the* way to verify any restore, so it is reachable
the moment it is pointed at a tree that has one. Deriving `rel` from the
unresolved path (and rejecting a path that escapes the root) would close it.

---

## 5. Findings to file as their own rows, not part of this FAIL

Per `review.md § What V4 does not judge` — *"a comment, a KR or a commit message
misstates something → file a row, never a FAIL on this one."*

### 5.1 "The explanation exists in exactly one file" is false as written

The row's headline principle is *do not write two copies*. Enumerated on `main`,
the reason sentence `cannot fail when the write succeeds` appears in:

```
work/reference/review-constraints.md:70     the declared one home
bin/perry-restore-check:14                  full restatement: pattern, reason, TASK-325
bin/README.md:31                            the rule and the reason, again
tests/test_restore_check.py:12              full restatement: pattern, reason, TASK-325
```

Four copies, three of them added by this change. A tool's `--help` and a test
module's docstring explaining themselves is defensible; asserting *"The
explanation exists in exactly one file"* while shipping four is not.
`test_the_section_exists_in_exactly_one_file` globs `work/reference/*.md` only,
so it cannot see any of the three.

### 5.2 Both one-home guards are literal-substring guards; four of five attacks defeated them

The brief asked me to try. Each attack planted into `copy2`, module run, restore
verified against `git show main:<path>`:

| attack | result |
|---|---|
| **paraphrase** the whole explanation into `review.md`, avoiding the literal reason string | **GREEN — guard defeated** |
| **partial copy** — the control table, the `TASK-325` incident and the code block copied into `review.md`, only the reason sentence left out | **GREEN — guard defeated** |
| **third file** — the exact heading in a new `work/reference/*.md` | RED — guard held |
| **subdirectory** — the whole section, reason included, in `work/reference/notes/restore.md` | **GREEN — guard defeated** (`glob("*.md")` is not recursive) |
| **paraphrased heading** — a second home whose heading differs by three words | **GREEN — guard defeated** |

The guards do catch the realistic failure — literal copy-paste — and that is
worth having. The result document's descriptions are what overreach: *"fails if
the explanation ever appears in `review.md`"* (it fails if one 34-character
string appears) and *"fails if the section is ever duplicated anywhere under
`work/reference/`"* (`anywhere under` is false; one directory level).

### 5.3 The pointer Deliverable 1 requires is invisible to the pointer guard

`work/reference/review.md:158-159` wraps the citation across a newline:

```
against the bytes you snapshotted — `review-constraints.md § Verify a
restore against an independent source` has the reason and
```

`tests/test_pointers_resolve.py`'s `POINTER` regex is
`` `([\w./-]+\.md)\s*§\s*([^`\n]+)` `` — the `\n` exclusion means this citation
never matches, so it is not resolved by the guard that exists precisely to catch
renamed sections. Confirmed: repointing it at a section that does not exist
(`§ Verify a restore against a snapshot`, well-formed) leaves
`test_pointers_resolve`, `test_restore_check` and `perry-lint --root .` all
green. Low practical risk — renaming the heading is caught from the other side by
`test_constraints_carry_the_rule` — but the reference half of Deliverable 1 is
guarded by nothing.

---

## 6. What I did not check

- **Windows, and any non-POSIX path handling.** macOS only.
- **The four rounds that already used `bin/perry-restore-check` today.** The
  brief names them as the blast radius; I did not identify them, re-run them, or
  check whether any used the multi-path form or ran from a scratch copy. If any
  did, § 2.1 and § 3 apply to their verification.
- **`git show` under `.gitattributes` filters / `core.autocrlf`.** This
  repository has no `.gitattributes`, so I confirmed the absence rather than the
  behaviour. Any such conversion would make the tool report a false *mismatch*
  (exit 1), which errs safe.
- **Concurrency.** Two rounds running the tool against the same tree, and the
  shared-scratchpad collision of `TASK-298`, were not exercised.
- **The other 113 test modules**, beyond running the full suite once and reading
  `test_pointers_resolve.py`. I did not check whether any other guard duplicates
  or contradicts these 15 tests.
- **The `--json` consumer contract** beyond reading the payload once. Nothing in
  the suite asserts the JSON shape, and I did not mutate it.
- **`perry-lint --reviews --strict`**, the pre-check. It runs before dispatch,
  not inside the round.
- **The spec's `Remainder`** — the PMO's ephemeral briefs and the out-of-repo
  memory file. Out of reach from here, as the spec says.

---

## 7. What would clear this

1. A test that passes **two** paths to the helper, one matching and one not, and
   requires exit 1 — closing `:231`. And tests over the `outside-repo` and
   `not-at-ref` branches, closing `:122` and `:129`.
2. Either gate the refusal on `verdict != "clean"` (`:198`), or correct
   `review-constraints.md:86-88` and `bin/README.md:31` to say what the tool
   actually does, and add `unverifiable` to the result's stated hole list.
3. § 4 and § 5 as their own rows; § 5.1's sentence corrected in the result
   document either way.

The change is close, and the parts the spec names are done well — the control is
the best artifact on this board this week, and the author found and closed a real
green mutation inside their own instrument. It fails on the same class of defect
it found, one function over.

=== VERDICT ===
task: TASK-256
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-256-spec.md
checked: worktree provenance (d49964e, 211 behind main; every path resolved via
         `git show main:<path>`); spec Bound grep re-run verbatim; the
         dispatch.md/delegate.md scope call (grep -i "mutat" -> exit 1, no
         output, both files present); 22 mutations planted line-anchored with an
         assert on the old text into two `git archive main` copies under
         /…/scratchpad/t256-rev-9f3a1c — 9 on bin/perry-restore-check, 5 on the
         guidance files, 3 on the control, 5 attacks on the one-home guards —
         every restore verified against `git show main:<path>` read from the
         original object store, never with the tool under review; author's
         mutation 9 re-planted (RED, test_the_ref_argument_is_honoured);
         circularity control attacked from three sides (all RED); all 10
         exit-2 argument paths executed; the shipped tool probed on multi-path,
         symlink, directory, no-.git and absent-at-HEAD inputs; full suite
         `bash tests/run` on the copy (114 modules · 3258 tests · green, exit 0,
         tree guard clean); `perry-lint --root .` (0 errors, 37 warnings)
not-checked: Windows/non-POSIX paths; the four rounds that already consumed
         bin/perry-restore-check today; .gitattributes / autocrlf behaviour
         (absent in this repo, confirmed absent not exercised); concurrent use
         and the TASK-298 scratchpad collision; the other 113 test modules
         beyond one full-suite run and reading test_pointers_resolve.py; the
         --json consumer contract; `perry-lint --reviews --strict` (pre-check,
         runs before dispatch); the spec's Remainder (ephemeral briefs, the
         out-of-repo memory file)
proof: bin/perry-restore-check:231 `ok = all(r["ok"] for r in results)` — mutate
         `all` to `any` and all 15 tests in tests/test_restore_check.py stay
         GREEN; no test passes more than one path (all ten run_helper call sites
         pass exactly one). The mutant then exits 0 on
         `perry-restore-check HEAD a.py b.py` where b.py does not match the ref,
         while the shipped `all` correctly exits 1 — a false PASS on the
         documented multi-path interface (bin/perry-restore-check:25,
         work/reference/review-constraints.md:85). Spec Verification item 2
         requires that mutating the shipped helper shows the check go red.
         Same class, same function, also GREEN: :122 outside-repo ok=False ->
         ok=True, and :129 not-at-ref ok=False -> ok=True, the latter reachable
         whenever a round pins a pre-branch baseline and asks about a file the
         branch added. Second behaviour, bin/perry-restore-check:198
         `if verdict == "modified" and not allow_modified_self:` — self_check()
         also returns "unverifiable" (:101 not in a git repo, :108 absent at
         HEAD) and that verdict is never gated, so a helper carrying the
         author's own mutation 8, run with no flags from a `git archive` copy
         (the workflow review-constraints.md § You are a reader prescribes),
         prints "✓ subject.py matches HEAD" and exits 0 with "ok": true over a
         file whose own reported digests disagree (expected f9d9dc2bab25,
         actual 5074fa3a71ce), contradicting the unconditional refusal claimed
         at review-constraints.md:86-88 and bin/README.md:31.
=== END VERDICT ===
