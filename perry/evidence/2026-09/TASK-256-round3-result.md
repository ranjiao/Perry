# TASK-256 — round 3 result

> Executor: dispatched coding agent (repository-local, stdlib only, no MCP)
> Answering: `perry/evidence/2026-09/TASK-256-round2-v4-review.md` — **FAIL**
> Criteria: `perry/evidence/2026-09/TASK-256-spec.md`
> Branch: `coding/task-256-round3`, cut from `main` at `1cd269e`

The round-2 FAIL is one line wide and it is fixed. The reviewer's finding
reproduced exactly before anything was touched, is red now under a named test,
and the case the skip was written for still works rather than failing. Round 2's
own eight mutations all still bite. One further green turned up — in a sentence
**this round added** — and is fixed too, in the guard that already existed.

---

## 0. Provenance

The worktree was handed over at the stale cut this project keeps producing.
Verified rather than assumed, before any reading:

```
git log --oneline -1        d49964e chore: consolidate test suite and project state
git log --oneline -1 main   1cd269e TASK-256 round 2 FAILs V4: a test asked …
```

`coding/task-256-round3` was cut from `main` explicitly and stub-committed, and
committed again after every step — HTTP 529/403 killed several agents on this
project in the last day and only committed work survived.

**`main` moved during this round**, `1cd269e` → `cc3684a` (`TASK-263`,
unrelated). `git diff 1cd269e cc3684a` over the four files this row touches or
measures is **empty**, so nothing below is invalidated:

```
git diff --stat 1cd269e cc3684a -- bin/perry-restore-check \
        tests/test_restore_check.py work/reference/review-constraints.md bin/README.md
(empty)
```

`main`'s six new paths are all `TASK-263` state and evidence.

**Mutation discipline.** Every plant is anchored by line number **with an assert
that the old text is present at that line** — a non-matching anchor raises
rather than silently no-opping. It fired once (§ 5, on the doc mutations, after
this round's own edit shifted `review-constraints.md` by one line) and was
re-anchored. `__pycache__` is cleared before each run and after each restore;
each plant waits past the whole-second boundary (`sleep(1.05 - time()%1)`); the
file's digest is compared to the object store **before** planting so the
baseline is not assumed; every restore is `git show HEAD:<path>`, single path;
after each, the disk digest is compared to the object-store digest and
`git status --porcelain` is confirmed empty.

**`bin/perry-restore-check` was NOT used to verify any restore in this round.**
It is the subject. `bin/perry-restore-check` stayed at
`md5=8cd3027409dd782a5e0f11e2246acd2a` across all eleven code plants — that is
the object-store digest, derived independently each time, not a value compared
against itself.

## 1. Reproduction of the round-2 GREEN — reproduced exactly

Before touching anything, on the branch cut from `main`:

```
BASELINE  ran=25 rc=0 n_failing=0 n_skipped=0 tree_clean=True

E2  bin/perry-restore-check:118
    '"unverifiable", f"{SELF} is not inside a git repository"'
 -> '"clean",        f"{SELF} is not inside a git repository"'
    ran=25 rc=0 *** GREEN *** n_failing=0 n_skipped=1
      SKIP: test_helper_outside_any_repository_refuses …
            skipped 'the temp directory is itself inside a git repository,
                     so this case is not reachable here'
    restored md5=8cd3027409dd782a5e0f11e2246acd2a matches_object=True tree_clean=True

E3  bin/perry-restore-check:125   (the sibling, for contrast)
    'return "unverifiable", f"HEAD:{rel} does not exist in {root}"'
 -> 'return "clean",        f"HEAD:{rel} does not exist in {root}"'
    ran=25 rc=1 RED n_failing=1
      RED: test_helper_absent_at_head_refuses
```

All 25 pass under E2. The skip fires and **the reason it prints is false** —
confirmed directly, by asking git rather than by argument:

```
TMPDIR: /var/folders/…/T/t256-probe-8t8rxl49
git -C <that dir> rev-parse --show-toplevel
  rc=128   fatal: not a git repository (or any of the parent directories): .git
```

The temp directory is not inside a repository. The skip fired because the test
established its precondition by **running the helper under test and asking it
for its own verdict**. A helper that misreports its verdict disabled the guard
written to catch it misreporting its verdict.

## 2. The fix

`tests/test_restore_check.py`, `test_helper_outside_any_repository_refuses` —
two lines of substance, as the reviewer said.

**Git decides the precondition, never the subject.** `git rev-parse
--show-toplevel` is run in the loose directory. When git says the directory is
**not** inside a work tree, the helper's verdict is **asserted** — exactly as
the sibling method one above already does — not skipped. The skip survives only
for the environment case it was written for, is reached only when git itself
says TMPDIR is inside a repository, and its message now names the toplevel git
reported and says who decided.

The docstring records why, so the next author does not reintroduce it.

## 3. The mutation the review found is now red — and seven more

Re-run against the fixed module. Baseline `ran=25 rc=0 n_skipped=0`.

| # | site | mutation | result | red tests |
|---|---|---|---|---|
| **E2** | `:118` | `"unverifiable"` → `"clean"` | **RED** | **`test_helper_outside_any_repository_refuses`** |
| E2b | `:118` | same branch, verdict *and* detail rewritten | **RED** | `test_helper_outside_any_repository_refuses` |
| M1 | `:255` | `all(...)` → `any(...)` | **RED** (2) | `test_a_bad_path_first_still_fails`, `test_one_bad_path_among_several_fails_the_whole_run` |
| E3 | `:125` | absent-at-HEAD `"unverifiable"` → `"clean"` | **RED** | `test_helper_absent_at_head_refuses` |
| E9 | `:127` | `"modified"` → `"clean"` | **RED** | `test_mutated_helper_refuses` |
| M5 | `:215` | `verdict != "clean"` → `verdict == "modified"` (round-1 literal) | **RED** (2) | `test_helper_absent_at_head_refuses`, `test_helper_outside_any_repository_refuses` |
| M8 | `:159` | `ok=actual == committed,` → `ok=True,` | **RED** (7) | incl. `test_differing_file_exits_one`, `test_a_restore_onto_a_corrupted_baseline_is_caught` |
| M2 | `:139` | `ok=False, reason="outside-repo"` → `ok=True` | **RED** | `test_a_path_outside_the_repo_is_not_a_pass` |

**8 planted · 8 red · 0 GREEN**, every restore verified against the object
store, tree clean after each.

E2b is deliberate: it is a second, independent way to break the same branch
(the detail string rewritten as well as the verdict), so the new assertion is
not pinned to one token.

M5 is worth a note — the gate at `:215` now reddens **two** tests where round 2
measured two as well, but the second is no longer a test that could skip itself.

### Round 2's own mutations, re-derived

Five of round 2's eight are in the table above (M1, M2, M5, M8, E3/E9 family) —
more than the three asked for — and all reproduce with the same named tests
round 2 and the V4 review both reported. The remaining two, the document
guards, are in § 5. **Nothing was broken.**

## 4. The control: a temp directory genuinely inside a git repository

A fix that turns the skip into an unconditional failure would be wrong. It does
not. `TMPDIR` pointed at a directory inside a real repository:

```
$ TMPDIR=<a dir inside a real git work tree> python3 -m unittest discover \
      -s tests -p test_restore_check.py -v

test_helper_outside_any_repository_refuses … skipped
  'TMPDIR is itself inside a git repository (/private/tmp/…/t256r3/tmp-in-repo),
   so a helper placed there is not outside every repository and this case is
   unreachable on this machine — git said so, not the tool under test'

Ran 25 tests
OK (skipped=1)
```

Green, not red. The case is handled, the reason printed is now **true**, and it
names the toplevel git actually reported so a reader can check it.

**Stated plainly as a residual**: on such a machine this test still does not
run, and E2 would be green there. That is the environment case the skip exists
for and the reviewer prescribed keeping — the difference from round 2 is that
the decision is now git's, the message is true and checkable, and no mutation of
the subject can reach it. On the ordinary case (`TMPDIR` outside any
repository, which is the default on this machine and on CI) the test runs and
E2 is red.

## 5. The documentation row — and a green it produced

The reviewer separated this out as a documentation row, not part of the FAIL:
neither shipped page tells a reader working in a copy to point the **live**
helper at the copy with `--root`, which is the answer that needs no flag
(review § 5, Case A). One sentence added to each:

- `work/reference/review-constraints.md` — after the `--allow-modified-self`
  clause.
- `bin/README.md:31` — the `perry-restore-check` row.

Both doc guards still bite over the edited sentences:

| # | site | mutation | result | red test |
|---|---|---|---|---|
| M6 | `review-constraints.md:90` | the override clause removed | **RED** | `test_the_documented_guarantee_matches_the_tool` |
| M7 | `bin/README.md:31` | the override clause removed | **RED** | same |

**And then a GREEN, in this round's own new sentence.** Deleting it was pinned
by nothing:

```
D1  work/reference/review-constraints.md:92
    'with `--root <copy>`, which answers correctly and needs no override' -> 'somehow'
    ran=25 rc=0 *** GREEN ***
```

A green mutation is the finding, so it is fixed rather than filed: one assertion
added to the existing `test_the_documented_guarantee_matches_the_tool`, which
already loops over both pages. Re-run:

| # | site | mutation | result | red test |
|---|---|---|---|---|
| D1 | `review-constraints.md:92` | `--root <copy>` sentence removed | **RED** | `test_the_documented_guarantee_matches_the_tool` |
| D2 | `bin/README.md:31` | `--root <copy>` clause removed | **RED** | same |

**Doc mutations: 4 planted · 4 red · 0 GREEN** after the guard (1 green before
it, named above). It is a literal-substring guard, worth exactly what that is,
and the docstring says so — the same limit round 2 declared for its own.

The anchor guard fired here and is worth recording: `review-constraints.md:89`
no longer carried the expected text after this round's own edit shifted it by a
line, the assert raised, and the plant was re-anchored to `:90`. Without it that
mutation would have no-opped and reported a false green.

## 6. Same-shape siblings elsewhere in this module

The defect is *a test that asks the code under test whether to run*. Every
`skipTest`, every precondition, and every `assertNotIn`-style check in
`tests/test_restore_check.py` was examined. Reported whether or not changed:

1. **`test_helper_outside_any_repository_refuses` (`:453-457`)** — the FAIL.
   Fixed.
2. **`test_helper_absent_at_head_refuses` (`:425-428`)** — establishes the same
   kind of precondition from the same source (the helper's own `--json`
   `self_check`), but with `assertEqual`. **Not changed, and correct as it
   stands**: a misreporting helper makes it *fail*, which is exactly what E3
   demonstrates (RED). The defect is the skip, not the source. Left alone.
3. **`skipTest` elsewhere** — there is exactly one `skipTest` in the module, the
   one fixed. No `skipIf`/`skipUnless` anywhere.
4. **`assertNotIn` (`:143`)** — `test_review_references_and_does_not_recopy`
   asserts the explanation is *not* re-copied into `review.md`. Could an empty
   or missing `review.md` pass it vacuously? No: the same method asserts
   `assertIn("review-constraints.md", text)` and
   `assertIn("git show <ref>:<path>", text)` first, and a missing file raises
   out of `read_text`. **Not a sibling.** Left alone.
5. **Exit-code assertions that a crash could satisfy** — checked all of them.
   `assertEqual(rc, 2)` is not crash-reachable: an uncaught Python exception
   exits 1, and the two refusal tests also assert `assertIn("REFUSING",
   r.stderr)`. The `rc == 1` assertions in
   `TestHelperVerdictIsNotJustTheLastPath` read the `--json` payload and
   `results[].reason` rather than the exit code alone — round 2's own
   deliberate defence against exactly this, and it holds. **Not siblings.**
6. **`_planted_copy` (`:388-392`)** — asserts the transform actually changed the
   bytes, so a mutation whose anchor stops matching raises instead of reporting
   a meaningless OK. **Already correct**; it is the same discipline this round's
   harness uses.

**One same-shape sibling existed. It is fixed. No others.**

## 7. Suite and lint

```
bash tests/run
114 modules · 3291 tests · 177.2s · 8 workers
✓ all green
0. tree guard — the tree the suite started in is the tree it ends in
  ✓ nothing under …/agent-a0e8c399990136f0f moved
EXIT=0
```

Fully green, exit 0, tree guard clean at both ends. Baseline measured on this
branch before the change: the same 114 modules / 3291 tests, all green — the
change strengthens existing assertions rather than adding tests, so the count is
unchanged by design. **Not one bit redder.** The `test_contract_key_parity`
wall-clock reds (TASK-335) did not appear in either run.

`python3 bin/perry-lint --root .` → **0 error(s), 37 warning(s)** — the same
count round 2 and the V4 review both report. The warnings are pre-existing
census lines (unbounded specs, blank summaries); none concerns this change.

## 8. Files changed

```
bin/README.md                        |  2 +-
tests/test_restore_check.py          | 45 ++++++++++++++++++++++++++++++++----
work/reference/review-constraints.md |  6 +++--
```

`bin/perry-restore-check` is **not** changed. The FAIL was in the test that
pinned it, not in the tool.

## 9. What this round did not do, and what it leaves open

- **`bin/perry-restore-check:134`, `resolve()` follows symlinks** — a tracked
  symlink retargeted in the working tree makes the tool report a good restore
  about a *different file*. Reviewer-assigned to its own row in round 1 § 5, and
  re-confirmed live in the round-2 V4 review § 6. Vacuous on `main` today
  (0 tracked symlinks). **Not fixed — not this row.**
- **The committed-wrong-helper hole**, named in the tool's own docstring: a
  wrong helper that has been *committed* passes its own self-check. Structural
  and unfixable by any self-check. It is why a round touching
  `bin/perry-restore-check` must use `git show` — this round did.
- **The standing "use `git show` instead" warning** (review § 6). The reviewer
  said it must stand "for now", and that once § 3 is closed it should be
  **narrowed rather than retired**, to two permanent exclusions (a round that
  touches the tool itself; any tree with tracked symlinks). § 3 is closed by
  this round. Narrowing the warning is a **new row**, not a widening of this
  one, and is not done here.
- **The environment residual in § 4** — a machine whose `TMPDIR` is inside a
  repository still does not run this test. Reviewer-prescribed; message now
  true and checkable.
- **The literal-substring limit of all three document guards**, including the
  one added in § 5. A paraphrase defeats them. Round 2 declared this in writing
  and the reviewer confirmed it by attack; this round inherits the limit and
  declares it again rather than claiming more.
- **Windows / non-POSIX paths**; concurrency and the `TASK-298` shared-scratchpad
  collision; the `--json` consumer contract beyond reading the payload. Not
  examined.

## 10. Nothing outside the row was touched

`schema/state-schema.json`, `claims`, `perry/BOARD.md`, `perry/tasks.jsonl`,
`perry/journal/` and `.perry/events.jsonl` are untouched. No push, no PR, no
merge, and `main` was never switched to or written to. `git status --porcelain`
is empty.
