# TASK-249 — round 4 V4 review (the delta `03493d6 → f8bc100`, confirmed)

- **Branch / tip reviewed**: `coding/task-249-suite-writes` @ `f8bc100`
- **Scope**: the delta from `03493d6` to `f8bc100` only — five commits,
  four files (`tests/run`, `tests/tree_guard.py`, `tests/test_tree_guard.py`,
  `perry/evidence/2026-08/TASK-249-result.md`). I did not re-derive what
  round 3 confirmed.
- **Baseline measured in this session**: `main` @ `4716e39`. It did **not**
  move during this round — `git rev-parse HEAD` on the live checkout read
  `4716e39` at the start and at the end.
- **Merge probe**: `4716e39` + `f8bc100` = `4f93630`, `ort`, clean, 6 files,
  no conflicts.
- **Reviewer**: fresh-context V4, read-only. Every experiment ran in my own
  detached worktrees under the scratchpad, in `git archive` copies of the tip,
  and on a case-sensitive disk image I created. **No tree under review was
  modified.** The live checkout at `/Users/bytedance/proj/Perry` was never
  written to (`git status --porcelain` empty, HEAD `4716e39`, at both ends).
  No write-side Perry tool was run against the project or any worktree of it;
  `perry-conform declare` and `perry-tasks render` were never invoked; no
  identifiers minted; `perry/BOARD.md` and `perry/tasks.jsonl` untouched.
- **Verdict: PASS.** The round-3 blocker is closed by a test that is red both
  ways the brief asked for. The two behaviour changes in `tests/run` are both
  correct and neither is accept-everything nor refuse-anything-unusual. All
  three `df8d536` fixes are genuinely closed, each demonstrated by a paired
  revert. The four open green mutations are each open for a true reason.
  The final tree is byte-identical to git's own objects for `f8bc100`.
  **This row merges.**

---

## 0. Baselines, counted the way the brief requires

The failure count is the **sum of the per-module `FAILED (failures=N)` lines**.
`grep -c '^FAIL:'` reads 3 on every one of my three logs and is wrong; the
`✗ N module(s) red` line reads 3 and counts MODULES. All three logs show the
same disagreement, so the trap round 3 documented reproduces here:

```
grep -o 'FAILED ([a-z=0-9, ]*)' <log>        -> failures=2, failures=1, failures=1
sum                                          -> 4      (the failure count)
grep -c '^FAIL:'                             -> 3      (a header was eaten)
the "✗ N module(s) red" line                 -> 3      (right, but MODULES)
errors=                                      -> 0      (a different word)
```

`bash tests/run` from each worktree root with `PERRY_PROJECT` unset, bracketed
at both ends by `git ls-files -z | xargs -0 md5 -q | md5 -q` and by
`git status --porcelain`. Run sequentially; the machine is shared with other
agents, so wall times are recorded, not compared.

| tree | modules | tests | seconds | **failures** | red modules | step 0 | tracked md5 (pre → post) | `git status` |
|---|---|---|---|---|---|---|---|---|
| `main` @ `4716e39` | 104 | 3124 | 239.7 | **4** | 3 | n/a (no guard on `main`) | `58f92a84…` → `58f92a84…` | empty / empty |
| branch tip `f8bc100` | 104 | 3122 | 248.1 | **4** | 3 | `✓ nothing under … moved` | `dea55634…` → `dea55634…` | empty / empty |
| merge probe `4f93630` | 105 | 3148 | 268.7 | **4** | 3 | `✓ nothing under … moved` | `8b2c1943…` → `8b2c1943…` | empty / empty |

**The same four by name on all three trees**, none in a file this branch
touches:

- `test_diagnose § test_the_queue_register_reconciles_with_the_queue_on_this_repository` (the eaten header)
- `test_diagnose § test_perry_itself_passes_its_own_id_checks`
- `test_heading_title § test_none_of_them_contains_its_own_id`
- `test_kr_progress_provenance § test_no_current_in_the_payload_claims_to_be_a_measurement`

**No `test_host_support`.** The known intermittent did not recur in my three
runs.

**The test arithmetic closes to the test.** `git ls-tree` of both trees differs
by exactly one module each way: `test_register_substitution.py` on `main` only,
`test_tree_guard.py` on the branch only. Counted directly on `main`,
`test_register_substitution` is **26**; `test_tree_guard` on the tip is **24**
(round 3 measured 21 — the delta adds three tests). So `3124 − 26 + 24 = 3122`
on the branch and `3124 + 24 = 3148` merged. Both observed exactly.

**The branch moves the failure count nowhere: 4 across 3 red modules, the same
four by name, on all three trees.**

---

## 1. The blocker's pin — the main thing, and it holds

`test_every_ignored_name_is_a_bullet_in_the_list_of_what_is_missed` reads the
`## What it does NOT catch, said plainly` section of `tests/tree_guard.py`'s
docstring, derives `sorted(IGNORE_DIRS | IGNORE_NAMES | IGNORE_SUFFIXES)`,
asserts the derived set is non-empty, and requires each name to appear in that
section.

Nine mutations on a `git archive` copy of the tip, baseline GREEN (24 tests)
asserted before the first and after the last, every anchor asserted present and
unique, `__pycache__` cleared and a sleep past the whole-second boundary before
every run, restore verified against **git's own blob shas** for `f8bc100`:

| # | mutation | verdict | test(s) that died |
|---|---|---|---|
| B1 | the `.claude` / `.gstack` bullet **deleted** | **RED** | `test_every_ignored_name_…`, alone (2 subTests) |
| B2 | a fifth ignored dir `.venv`, **the equality pin moved with it**, no bullet | **RED** | the same, alone |
| B3 | B2 **+ a truthful bullet, in the wrong section** (*What is ignored*) | **RED** | the same, alone |
| B9 | a fifth `IGNORE_NAMES` entry `notes.txt`, names pin moved with it | **RED** | the same, alone |
| B8 | control: B2 **+ a truthful bullet in the right section** | GREEN | — (correct: the honest fix passes) |
| B4 | B2 + a bullet that **names `.venv` and describes it backwards** | **GREEN** | — |
| B5 | ignored dir `.claudex` — **no bullet at all** | **GREEN** | — |
| B6 | `IGNORE_SUFFIXES += ".md"` (blinds `perry/BOARD.md`), suffix pin moved with it | **RED** | `test_the_four_files_of_this_row_are_never_invisible`, `test_a_module_that_writes_into_the_root_turns_the_suite_red` — **not** the new pin |
| B7 | a **fourth** ignore mechanism, inline in `manifest` (`and d != "evidence"`) | **GREEN** | — |

**B1 and B2 are the two cases the brief named, and both are red.** B2 is the
one that matters: adding `.venv` to `IGNORE_DIRS` *and* moving
`test_all_three_ignore_lists_are_the_documented_ones`'s equality set with it —
the edit that defeats the equality pin alone — is caught by the new test and by
nothing else. The blocker is genuinely closed.

**B3 and B9 close two ways round it I tried.** A bullet placed in the adjacent
*"What is ignored, and the one rule that decides it"* section does not satisfy
the test: the section is bounded at the next `\n## `. And the pin covers all
three lists, not just `IGNORE_DIRS`.

### Three ways to satisfy the new test without a truthful bullet

All three are green, and the row does not name any of them.

- **B4 — a bullet that names the directory and lies about it.** The bullet
  *"`.venv`. Fully hashed like any other directory; every write under `.venv`
  is reported, so nothing is missed here"* — the exact inversion of what the
  entry means — is green. This is the same shape as MP4/MP5 on the sibling
  pin, which the delta *did* stop overstating; here it is unstated.
- **B5 — no bullet at all.** Adding `.claudex` to `IGNORE_DIRS` is green,
  because the section already contains the literal string `.claudex/` — in the
  `.claude` bullet's own control sentence, *"The same writes into `.claudex/`
  are reported"*, which is now the opposite of the truth. The assertion is
  `assertIn(name, section)`: a **substring** of the section, not a bullet.
  The test's name says *is a bullet in the list*; what it checks is *appears
  somewhere in the section*.
- **B6 — a name that is a substring of the prose.** `IGNORE_SUFFIXES += ".md"`
  blinds the guard to every markdown file in the tree, including
  `perry/BOARD.md` — the file this row's real defect moved — and the new pin
  is **green**, because `TASK-0NN-result.md` appears in the section. It is
  caught, twice, by `test_the_four_files_of_this_row_are_never_invisible` and
  by the planted-write test. **The layering works**; the new pin is not what
  catches it.

**B7 is the one gap with no backstop.** An ignore added *outside* the three
lists — one line in `manifest`'s `os.walk` filter — is invisible to the new
pin, to the equality pin, and to the four-files test, as long as it does not
hide one of those four files. `test_the_four_files_of_this_row_are_never_invisible`'s
docstring says it catches "a fourth list invented tomorrow"; it catches one
only when the fourth list hides one of the four named files. That claim is
bounded rather than wrong, and it predates this delta.

**Judgement.** The blocker is closed: the edit that actually happened, and the
edit that defeats the equality pin, are both red. The residue is that the test
is satisfiable by a substring rather than by a bullet, and its name and
docstring do not say so — the same "the name claims more than the assertion
reads" shape that round 3 made the delta fix on the *other* pin. **Fix or
file, not a blocker.**

---

## 2. `tests/run` — the two behaviour changes, swept

Both changes are in the suite entry point, so every future run goes through
them. Sweep re-run from scratch on a `git archive` copy at `f8bc100`, `bash
tests/run --lint`, `REFUSED` = rc 2 with a banner before step 1.

| # | spelling | round 3 (`03493d6`) | **round 4 (`f8bc100`)** | right? |
|---|---|---|---|---|
| 1 | `$ROOT` exactly | ACCEPTED | **ACCEPTED** | yes |
| 2 | `$ROOT/` trailing slash | ACCEPTED | **ACCEPTED** | yes |
| 3 | symlink alias of `$ROOT` | ACCEPTED | **ACCEPTED** | yes |
| 4 | `/tmp` spelling of a `/private/tmp` root | ACCEPTED | **ACCEPTED** | yes |
| 5 | `$ROOT/.` | ACCEPTED | **ACCEPTED** | yes |
| 6 | doubled slash | ACCEPTED | **ACCEPTED** | yes |
| 7 | `$ROOT/tests/..` | ACCEPTED | **ACCEPTED** | yes |
| 8 | `.` (relative, cwd is `$ROOT`) | ACCEPTED | **REFUSED — "is a relative path"** | **changed, and right** |
| 9 | `tests/..` (relative) | ACCEPTED | **REFUSED — "is a relative path"** | **changed, and right** |
| 10 | `..` (relative parent) | REFUSED | **REFUSED — "is a relative path"** | yes |
| 11 | the whole path UPPERCASED | REFUSED (false) | **ACCEPTED** | **changed, and right here** |
| 12 | one component case-flipped | REFUSED (false) | **ACCEPTED** | **changed, and right here** |
| 13 | a genuinely foreign directory | REFUSED | **REFUSED — "points somewhere else"** | yes |
| 14 | a path that does not exist | REFUSED | **REFUSED**, `resolves to = (nothing …)` | yes |
| 15 | a **file**, not a directory | REFUSED | **REFUSED** | yes |
| 16 | the empty string | ACCEPTED | **ACCEPTED** | yes — matches `os.environ.get(…) or Path.cwd()` |
| 17 | a subdirectory of `$ROOT` | REFUSED | **REFUSED** | yes |
| 18 | `$ROOT` with a trailing space | REFUSED | **REFUSED** | yes |

Exactly the two intended movements, and nothing else moved.

### Twelve spellings the sweep does not cover

| # | spelling | verdict | note |
|---|---|---|---|
| E1 | **firmlink** `/System/Volumes/Data$ROOT` | ACCEPTED | same dev+inode, a different string, **no symlink in the path** — the nearest thing to a bind mount this machine allows. `stat -f '%d %i'` identical on both. |
| E2 | a symlink whose **name contains a newline** | ACCEPTED | the quoting holds; `-ef` resolves it |
| E3 | `$ROOT` with a **trailing newline** | REFUSED | correct — a different path |
| E4 | leading double slash `//private/tmp/…` | ACCEPTED | POSIX-legal spelling of `$ROOT` |
| E5 | through a **symlinked parent component** | ACCEPTED | correct |
| E6 | `$ROOT/./` | ACCEPTED | correct |
| E7 | uppercased **+ trailing slash** | ACCEPTED | correct on this filesystem |
| E8 | uppercase via the `/tmp` spelling (two foldings at once) | ACCEPTED | correct |
| E9 | a value that looks like a `test` operator (`/ -o /x`) | REFUSED | **no operand injection** — `[ … -ef … ]` sees one word |
| E10 | `$ROOT/tests/../tests/..` | ACCEPTED | correct |
| E11 | a single space | REFUSED — "relative" | correct |
| E12 | a single tab | REFUSED — "relative" | correct |
| E13 | an unexpanded `~/proj/Perry` | REFUSED — "relative" | refuses safely; see the nit below |

**So the refusal did not become accept-everything** (13, 14, 15, 17, 18, E3,
E9 all refused) **and it did not become refuse-anything-unusual** (5, 6, 7, 16,
E1, E2, E4, E5, E6, E10 all accepted). I could not make a true second mount
point of one filesystem on this machine — `hdiutil` will not attach an image
twice — so E1's firmlink is the strongest same-inode-different-string case I
have, and `pwd -P` canonicalises it back to `/private/…`, so it does not
discriminate `-ef` from the string comparison. Hard links to directories are
forbidden, so there is no hardlinked alias to test.

### MC1 re-run — the `-ef` revert kills exactly one test, and it is the new one

| # | mutation of `tests/run` | verdict | test(s) that died |
|---|---|---|---|
| **MC1** | `-ef` reverted to round 2's resolved-**string** comparison, relative branch kept | **RED** | **`test_a_differently_cased_spelling_of_this_root_is_this_root`, alone** |
| MC2 | the relative branch removed (relatives fall through to `-ef`) | RED | `test_a_relative_perry_project_is_refused_and_says_why`, alone |
| MC3 | still refuses relatives, **banner** reworded to "points somewhere else" | RED | the same, alone |
| MC4 | full revert to the raw-string comparison of `8dfd25e` | RED | that one + the case test + `test_other_spellings_of_this_root_are_this_root` |
| MS1 | the two `case` arms **inverted** (absolute → "relative") | RED | the case test, the relative test, `test_other_spellings_…`, `test_perry_project_equal_to_the_root_is_allowed` |

**MC1 confirmed.** Round 3's finding one layer out: the six spellings round 2's
own fix test covers are all case-identical, so it is green under a full revert
of the `-ef` change; only the new test sees it. This is the third time in this
row that a fix's own test could not observe the bug the next fix closes, and
the third time the new test is the only one that can.

### The case fix is exercised on a case-SENSITIVE filesystem — the skip path is no longer only reasoned

I created a case-sensitive APFS image (`hdiutil create -fs "Case-sensitive
APFS"`), mounted it at `/Volumes/CSPERRY`, unpacked the tip there, and pointed
`TMPDIR` at it so `tempfile.TemporaryDirectory()` — which is where the test's
copy actually lives — landed on that volume.

```
env -u PERRY_PROJECT TMPDIR=/Volumes/CSPERRY/tmp python3 -m unittest discover \
    -s tests -p test_tree_guard.py
  -> Ran 24 tests   OK (skipped=1)
  skipped 'this filesystem is case-sensitive, so
           /Volumes/CSPERRY/tmp/tmpc6lc3diu/REPO is not
           /Volumes/CSPERRY/tmp/tmpc6lc3diu/repo'
```

The skip fires, names both paths, and the other 23 tests — including the
`-ef`-dependent `test_other_spellings_of_this_root_are_this_root` and the
relative refusal — stay green there. And the **behaviour** on that volume is
the right one, which is the part the skip cannot assert:

```
CS: $ROOT exactly                        ACCEPTED
CS: $ROOT uppercased (a REAL other dir)  REFUSED  ✗ … points somewhere else
CS: /Volumes/CSPERRY/REPO (nonexistent)  REFUSED  ✗ … points somewhere else
CS: $ROOT/ trailing slash                ACCEPTED
CS: relative .                           REFUSED  ✗ … is a relative path
```

So `-ef` is not "accept any casing": it accepts exactly the casings the
filesystem folds, and refuses them where it does not. That is what the
docstring claims, and it is now measured on both kinds of filesystem rather
than argued on one. **Round 3's sharp edge A is closed, and the row's
"reasoned, not exercised" caveat can be struck.**

**Sharp edge B is closed too, by decision.** Relative values were the
regression round 3 caught; they are now refused, with a banner that says it is
the relativity and not a wrong directory. Nothing in this repository exports a
relative `PERRY_PROJECT` — I grepped every producer — so the refusal costs
nothing here.

---

## 3. The three `df8d536` fixes — each closed, each demonstrated by a paired revert

The test of a fix is not that the fix is green; it is that reverting the fix
turns the attack green again. Each row below is a pair.

| # | mutation | verdict | reading |
|---|---|---|---|
| MC3 | banner reworded, **fixed** assertion | **RED** | the fix fires |
| F1c | banner reworded, assertion reverted to its `df8d536^` text | **GREEN** | the green mutation the row self-reports, reproduced |
| F1d | assertion reverted, banner untouched (control) | GREEN | the revert is otherwise inert |
| F2 | the *DIFFERENT checkout* bullet **moved to the end of its list** | **GREEN** | correct — the pin still reads its own bullet |
| F2c | the same move + terminator reverted to v1 (`doc.index`) | **RED** | both pin tests **ERROR** with `ValueError` |
| F2c2 | the same move + terminator reverted to v2 (run to end of docstring) | **RED** | `test_the_bullet_uses_the_word_…` fails — the swallowed *"Why a refusal and not a re-aim"* section contains `export` |
| F3 | all three ignore lists **emptied** | **RED** | `test_every_ignored_name_…` among 7 |
| F3c | the same, vacuity guard reverted | RED elsewhere, **`test_every_ignored_name_…` GREEN** | the guard is what stops three empty sets passing |

All three are genuinely closed, and F2c/F2c2 show the terminator fix had to be
*both* halves — the first repair traded a `ValueError` for a wrong reading.

### The same shape elsewhere in the module — one instance, harmless

`test_a_foreign_perry_project_refuses_the_run` asserts `rc == 2` and
`assertIn("refusing to run", out)` — the generic prefix, not the banner. There
are now **two** banners. MS1 (the `case` arms inverted, so every absolute path
prints the *relative* banner) leaves that test **green**; it is red only
because four sibling tests fire. So the module contains one more assertion that
would accept the wrong sentence, and it is the one the tightened relative test
is now asymmetric with. Nothing hides behind it — MS1 is caught four ways —
but if the two banners are worth distinguishing in one test they are worth
distinguishing in its sibling. **One line.**

Nothing else in the module matches the shape: I read every `assertIn` /
`assertNotIn` / `assertTrue` in the file. The remaining string assertions are
against the guard's own report lines (`M perry/BOARD.md`, `+ .perry/…`,
`nothing under`, `THE SUITE WROTE INTO THE TREE IT RAN IN`), which are outputs,
not prose.

---

## 4. The four green mutations left open — each judged

- **MP4 / MP5 (bullet inverted; bullet cut to four words) — reproduced GREEN,
  and leaving them open is right.** The class was renamed from
  `TestTheDocstringSaysWhichMechanismShipped` to
  `TestTheBulletUsesTheVocabularyOfTheMechanismSpelledInTestsRun`, and the
  docstring now spells out that it requires `refuses` present and `export`
  absent "and nothing else", with the two mutations named. The claim is now
  equal to what the code does, which is what round 3 asked for. **Sound.** The
  same shape is now unstated one class down — see B4/B5 in § 1.
- **MP3 (`unset PERRY_PROJECT`, refusal left dead under `if false`) —
  reproduced: the pin stays GREEN, and the behaviour tests kill it** (6
  failures across `test_a_foreign_perry_project_refuses_the_run`,
  `test_a_relative_perry_project_is_refused_and_says_why`,
  `test_other_spellings_of_this_root_are_this_root`). The argument is
  structurally true: no substring search distinguishes a reachable line from an
  unreachable one, and the docstring says so in those words. **Sound.**
- **MP7 (the bullet moved last) — reproduced GREEN, and it should be**
  (my F2), with a control that shows the terminator fix is load-bearing. The
  row's MP8 restores the **original** `doc.index` terminator and gets a
  `ValueError` — my F2c reproduces it. The *intermediate* repair
  (`doc[start:]` to the end of the docstring) is described in § 9.7 but is not
  in the mutation table; my F2c2 supplies it, and it fails differently — a
  wrong reading rather than a crash. **Sound, and the fix needed both
  halves.**

**MP1 / MP2 re-run on the delta and both are now RED on both pin tests**, so
the widened `RE_AIM` really does close the two spellings round 3 slipped past
it. One cost of the widening, which I found and the row does not name:

- **MS2 — a false positive the next editor can trip.** Adding one help line to
  the refusal's own message, `echo "  or: export PERRY_PROJECT=\"$ROOT\" first"`,
  turns **both pin tests red** with *"tests/run spells ['re-aim', 'refuse']"*.
  The anchor is "not a comment line", and an `echo` inside the refusal is not a
  comment. The edit ships neither mechanism; the message says it ships both.
  Fails red, so it is a nuisance rather than a hole, and the shape predates the
  delta (the old pattern would also have matched that line). **File.**

---

## 5. The harness defect the row self-reports — the final tree is genuinely unmodified

The row reports that one of its mutations made two edits to one file, captured
"original" bytes once per edit, and restored only to the state after the first;
every md5 check compared the file to bytes the harness had just written, and
only `diff -rq` against the tip caught it.

**I verified `f8bc100` against git's own objects, not against any digest the
row produced.**

1. `git ls-tree -r f8bc100` gives a blob sha for every tracked path. I ran
   `git hash-object` on each corresponding file and compared. Done against a
   fresh `git archive f8bc100 | tar -x` reference: **zero mismatches**.
2. The row's own worktree, `scratchpad/wt-249`, is at `f8bc100` with
   `git status --porcelain` **empty** (no modifications, no untracked files),
   and `diff -rq --exclude=.git --exclude=__pycache__` against that reference
   is **empty**. Both checked at the start and again at the end of my round.
3. My mutation copy was `diff -rq`-identical to the reference and
   `git hash-object`-identical to git's objects after the last restore, and the
   baseline re-asserted GREEN (24 tests) at the end.
4. I scanned the tip's three source files for residue from the row's own named
   mutations — `if false` outside a docstring, hardcoded `0o777` / `0o644`, a
   live `export PERRY_PROJECT`, `.venv`, `declining to start`. The only hits
   are inside docstring prose describing the mutations. The delta touches
   exactly four files and every hunk in `git diff 03493d6 f8bc100` is accounted
   for by one of the five commit messages.

**No residue. The tree is what the commits say it is.**

---

## 6. Mutations — my own, this round

Twenty-two on `git archive` copies of the tip, never on a reviewed tree.
Discipline enforced by the harness rather than remembered: **refuse to start
unless the copy is `diff -rq`-identical to a reference verified file-by-file
against git's blob shas**; baseline asserted GREEN (24 tests) before the first
and after the last; every anchor asserted **present and unique** before
replacing; `__pycache__` cleared and a sleep past the whole-second boundary
before every run; **restore by writing back `git cat-file blob <sha>` and
re-checking `git hash-object` against the tree sha** — never against bytes the
harness wrote, which is the circularity above; whole-copy `diff -rq` after
each. Runner: `python3 -m unittest discover -s tests -p test_tree_guard.py -v`
with `PERRY_PROJECT` popped, deliberately not through `tests/run --only`,
whose 25-line truncation eats `FAIL:` headers (TASK-251).

Red: B1, B2, B3, B9, B6, MC1, MC2, MC3, MC4, MS1, MS2, MP1, MP2, MP3, F2c,
F2c2, F3 — **17**.
Green **by design** (controls / stated limits): B8, F1d, F2, MP4, MP5, MP7 —
and **green as findings**: B4, B5, B7, F1c, F3c.

One harness error of my own, reported rather than hidden: my first F1c reverted
the assertion but not the message text that referenced `banner`, producing a
`NameError` rather than the intended comparison. I re-ran it against the exact
`df8d536^` text; the corrected result is in § 3.

---

## 7. What I did NOT verify

1. **I did not re-derive round 3.** The `.claude` hole's three scopes, the
   executable-count derivation, the nine `test_config_store_readers` figure,
   the `manifest`/`compare` unit behaviour, and the call-site fix were checked
   by rounds 2 and 3 and are outside this round's scope. I read the delta's
   changes to their docstrings; I did not re-measure the claims.
2. **One run per tree, three trees.** The four failures agree by name across
   all three, which is why I did not repeat. A single run cannot separate a
   fifth flake from a real failure, and `test_host_support`'s absence in three
   runs is evidence about its rate, not proof it is gone.
3. **`--serial` was not run.** All three used the default parallel path.
4. **No true second mount point, and no hardlinked alias.** `hdiutil` will not
   attach one image twice and directories cannot be hard-linked, so E1's
   firmlink is as close as I got — and `pwd -P` canonicalises it, so it does
   not discriminate `-ef` from the string comparison.
5. **I did not observe a real subagent worktree appearing during a real run.**
6. **I did not audit the rest of `tests/tree_guard.py`'s prose** against the
   code, beyond the section the new pin reads and the bullet the old pin reads.
7. **B7 is a demonstration, not a proposal.** I showed a fourth ignore
   mechanism is invisible to all three pins; I did not check whether any real
   edit is likely to take that shape.
8. **The case-sensitive volume is a disk image, not the machine's own
   filesystem.** It behaves as a case-sensitive APFS volume (`aa` and `AA` are
   distinct there, verified) but it is not the environment anyone will actually
   run in.
9. **I did not verify the result document's round-4 prose line by line** —
   only the mutation table, the baseline table, and the § 9.7 self-report,
   which are what I could independently reproduce.

---

## Verdict

**PASS. This row merges.**

The round-3 blocker is closed, and closed by a test rather than by a promise:
deleting the bullet is red, and adding a fifth ignored directory with the
equality pin moved with it — the case the equality pin alone would miss — is
red too. Both behaviour changes in `tests/run` are correct and bounded: the
relative refusal is a decision with a banner that explains itself and costs
nothing in this repository, and `-ef` accepts exactly the spellings the
filesystem folds, refusing them on a case-sensitive volume, which I exercised
rather than reasoned about. MC1 kills exactly one test and it is the new one.
All three fixes from `df8d536` are genuinely closed, each with a paired revert
that turns the attack green again. The four open green mutations are each open
for a reason that is true. The final tree is byte-identical to git's own
objects for `f8bc100`, checked against `git ls-tree` and `git hash-object`
rather than against anything the row produced. The merge is clean and moves the
failure count nowhere: 4 across 3, the same four by name, on `main`, on the
tip, and on the merge.

**Fix, or file (3 items) — none blocking:**

- **The new pin is satisfied by a substring, not by a bullet, and its name says
  otherwise.** `assertIn(name, section)` passes for a name that appears
  anywhere in the section: `.claudex` needs no bullet at all (the `.claude`
  bullet's control sentence already contains the string, and now says the
  opposite of the truth), `.md` needs none either, and a bullet that names a
  directory and describes it backwards is green. Either say so in the
  docstring — the way the sibling pin now does — or require the name to open a
  `- **` bullet inside the section.
- **`test_a_foreign_perry_project_refuses_the_run` asserts the generic
  `refusing to run`, not its banner.** With two banners now, inverting the
  `case` arms leaves it green (MS1). Its tightened sibling reads the banner;
  this one should too.
- **`MS2` — the pin can be tripped red by a help line.** An `echo` inside the
  refusal's own message that mentions `export PERRY_PROJECT` is not a comment,
  so `_implemented` reads "both mechanisms" and both pin tests fail with a
  message that is false about a change that ships neither. Fails red, so it is
  a nuisance; anchoring the export pattern to a line that is not inside an
  `echo`, or simply noting it, would close it.

**One line worth adding to the row, not a defect:** round 3's § 7 item 7 and
the row's own "the skip path is reasoned, not exercised" can both be struck —
the skip fires and the behaviour is correct on a genuinely case-sensitive
filesystem, measured here.

*Every experiment ran on copies, in my own detached worktrees, or on a disk
image I created. The live checkout was never written to and is at `4716e39`
with an empty `git status`. `perry/BOARD.md` and `perry/tasks.jsonl` untouched;
no write-side Perry tool was run against the project or any worktree of it;
`perry-conform declare` and `perry-tasks render` were never invoked; no
identifiers minted.*
