# TASK-256 — round 2 result

> Author: dispatched coding agent (repository-local, stdlib only, no MCP)
> Criteria: `perry/evidence/2026-09/TASK-256-spec.md`
> Answering: `perry/evidence/2026-09/TASK-256-round1-v4-review.md` (FAIL)
> Branch: `coding/task-256-round2`, cut from `main` at `5601e45`

## 0. Provenance, and a correction to the brief

The worktree was handed over at **`d49964e`** — the stale cut this project keeps
producing, and the third time today. Verified rather than assumed:

```
git log --oneline -1          d49964e chore: consolidate test suite and project state
git log --oneline -1 main     5601e45 TASK-330 lands, and the two findings it refused to fix become their own rows
```

The branch was therefore cut from `main` explicitly and stub-committed before
any work, so the round would survive being lost. It was: **HTTP 529 killed this
agent four times.** Everything below was re-verified on the surviving branch.

**One premise in the brief was understated.** The brief said the known FAIL is
`ok = all(...)` → `any` at `bin/perry-restore-check:231`, "as the PMO
understands it". That is a correct account of § 2.1 and it is only *part* of the
FAIL. The review carries a second finding of equal standing:

> **§ 3** — *the self-check's advertised guarantee is false in the configuration
> this project prescribes.*

`self_check()` returns three verdicts and the refusal gated on one, so
`unverifiable` answered anyway. The board's own `next_action` names both
("FIX BOTH"); the brief's summary paragraph named one. Both are fixed here.
The review also carries § 2.2 (two sibling branches, same class) and § 4/§ 5,
which it explicitly assigns to their own rows.

---

## 1. Reproduction of the round-1 FAIL

Done first, before anything was changed, on a `git archive` copy checked against
the object store — `copy f4e78142f531 = main f4e78142f531` — so the "before"
state is measured, not asserted.

### § 2.1 — the aggregate verdict is unguarded

`bin/perry-restore-check:231`, `all` → `any`, planted line-anchored with an
assert on the old text:

```
planted bin/perry-restore-check:231  'all(r["ok"] for r in results)' -> 'any(...)'
  now:     ok = any(r["ok"] for r in results)

Ran 15 tests in 5.507s
OK                                        <-- all fifteen GREEN
```

And the mutant is not benign. Two files, one restored and one not:

```
=== mutant (any) ===
  ✓ a.py matches HEAD (60b725f10c9c…)
  ✗ b.py: b.py does not match HEAD:b.py (8 bytes on disk vs 2 at ref)
exit=0                                    <-- vouches for a corrupt file

=== shipped (all) ===
  ✓ a.py matches HEAD (60b725f10c9c…)
  ✗ b.py: b.py does not match HEAD:b.py (8 bytes on disk vs 2 at ref)
exit=1
```

The mutant prints the `✗` **and exits 0**. Multi-path is the documented
interface, at the tool's own line 25 and in `review-constraints.md`.

### § 2.2 — both siblings, same class, also green

| planted | tests |
|---|---|
| `:122` `entry.update(ok=False, reason="outside-repo",` → `ok=True` | Ran 15 · **OK** |
| `:129` `entry.update(ok=False, reason="not-at-ref",` → `ok=True` | Ran 15 · **OK** |

### § 3 — `unverifiable` answers anyway

Round-1 mutation 8 (`ok=actual == committed,` → `ok=True,`) planted into a copy
sitting outside any repository — which is what a `git archive` scratch copy is,
the workflow `review-constraints.md § You are a reader` prescribes — run with
**no flags**, against a file that does **not** match its ref:

```
  ! self-check unverifiable: …/loose/perry-restore-check is not inside a git repository
  ✓ b.py matches HEAD (3b5d5c371295…)
exit=0
```

```json
{ "ok": true,
  "self_check": "unverifiable",
  "expected_md5": "3b5d5c3712955042212316173ccf37be",
  "actual_md5":   "626e65b52c074fdd75dcee41257f10a8" }
```

Its own JSON reports two disagreeing digests and `"ok": true`. The round-1
author did not reproduce this one; it reproduces exactly as the review states.

---

## 2. The fix, and why that shape

Two halves, because the review found two things.

### 2.1 The gate — `bin/perry-restore-check:215`

```python
-    if verdict == "modified" and not allow_modified_self:
+    if verdict != "clean" and not allow_modified_self:
```

**Why refuse rather than warn.** The review offered both options ("Either gate
the refusal on `verdict != "clean"`, or correct the documents"). Refusal is the
right one, and the deciding argument is the round-1 author's own, quoted in the
review: refusal was chosen over a warning because *"a warning inside a verifier
is a line an agent scrolls past."* That reasoning was applied to `modified` and
not to `unverifiable` — and `unverifiable` printed its warning to **stdout**,
where it sat directly above a `✓`. `unverifiable` is the *more* dangerous
verdict, not the safer one: `modified` means a comparison was made and failed;
`unverifiable` means **no comparison was made at all**.

**Why not a new flag.** The review allowed "`--allow-modified-self` (or a
sibling flag)". A sibling would add a second thing to remember and a second
thing to get wrong, and every existing caller and both shipped documents already
name the flag that exists. One flag, one meaning — now stated as "could not be
shown to match", which covers both non-clean verdicts. The refusal message names
which verdict it hit, so the reader is not left guessing.

**This is a deliberate behaviour change and it will bite.** An agent running the
tool from a scratch copy, or from a worktree cut before the tool landed, now
gets exit 2 where it used to get an answer. That is the point — those are
precisely the cases where the tool could not vouch for itself — and
`--allow-modified-self` is the documented escape. Declared here rather than
discovered later.

### 2.2 The guards — `tests/test_restore_check.py`, 15 → 25 tests

The shipped `all` was already correct. **What did not exist was any test that
passed more than one path** — all ten `run_helper` call sites passed exactly
one, which is why the mutant was green. The new class
`TestHelperVerdictIsNotJustTheLastPath` closes that and every `ok=False` branch
of `check()`, which the review found entirely untested.

**These tests read `--json`, not just the exit code, and that is load-bearing.**
A mutant that flips an `ok=False` branch to `ok=True` leaves the entry with no
`expected_md5` key; the human-readable printer then raises `KeyError` — which
*also* exits 1. An exit-code-only assertion would call that red and hide the
hole. This is exactly why the review recorded `:133` as a "near-equivalent
mutant": under an exit-code test it is one. Reading the payload distinguishes
it, and mutation M4 below is red because of that choice.

### 2.3 The documents

Two shipped pages stated the guarantee without qualification and were false:

- `work/reference/review-constraints.md` — *"refuses to answer while its own
  bytes differ from the copy committed in its repository."*
- `bin/README.md:31` — the same sentence.

Both now say the tool refuses unless its bytes have been **shown to match**,
name the no-committed-copy case explicitly, and name the override.

---

## 3. Mutation table

Every mutation planted **by line number with an assert on the old text at that
line** — a non-matching anchor raises rather than silently no-opping.
`__pycache__` cleared before and after each plant; each plant waited past the
whole-second boundary (`sleep(1.05 - time()%1)`) before running.

**Restores verified with `git show HEAD:<path>`, single path, one file at a
time. `bin/perry-restore-check` was deliberately NOT used** — it is the tool
under repair, and using it here would be the circularity this row exists to
kill. After every restore, disk digest compared to the object-store digest and
`git status --porcelain` confirmed empty.

| # | site | mutation | result | named tests that went red |
|---|---|---|---|---|
| M1 | `bin/perry-restore-check:255` (`:231` in round 1) | `all(...)` → `any(...)` | **RED** | `test_one_bad_path_among_several_fails_the_whole_run`, `test_a_bad_path_first_still_fails` |
| M2 | `:139` (`:122`) | `ok=False, reason="outside-repo"` → `ok=True` | **RED** | `test_a_path_outside_the_repo_is_not_a_pass` |
| M3 | `:146` (`:129`) | `ok=False, reason="not-at-ref"` → `ok=True` | **RED** | `test_a_path_absent_at_the_ref_is_not_a_pass` |
| M4 | `:150` (`:133`) | `if not resolved.exists():` → `if False:` | **RED** | `test_a_path_missing_on_disk_is_not_a_pass` |
| M5 | `:215` (`:198`) | the gate reverted to the exact round-1 line, `verdict == "modified"` | **RED** | `test_helper_absent_at_head_refuses`, `test_helper_outside_any_repository_refuses` |
| M6 | `work/reference/review-constraints.md:90` | the override sentence removed | **RED** | `test_the_documented_guarantee_matches_the_tool` [`review-constraints.md`] |
| M7 | `bin/README.md:31` | the override clause removed | **RED** | `test_the_documented_guarantee_matches_the_tool` [`README.md`] |
| M8 | `:159` (`:142`) | round-1 mutation 8 re-planted, `ok=actual == committed,` → `ok=True,` | **RED** (7) | `test_differing_file_exits_one`, `test_a_restore_onto_a_corrupted_baseline_is_caught`, `test_the_ref_argument_is_honoured`, `test_one_bad_path_among_several_fails_the_whole_run`, `test_a_bad_path_first_still_fails`, + 2 below |

**8 planted · 8 red · 0 GREEN.**

M1–M5 are the two halves of the fix reverted: M5 is the gate half (planted as
the *literal* round-1 line, so it reverts the behaviour exactly), M1–M4 are the
guard half. M6–M7 are the document half.

**One honest qualification on M8.** Two of its seven reds —
`test_mutated_helper_refuses` and `test_the_mutation_would_otherwise_have_been_silent`
— are red because `_planted_copy`'s own anchor assert fired: those tests apply
the *same* transform to a copy of a helper that already carries it, so
`after != before` is false and the harness raises "planted mutation did not
match anything". That is the anchor guard working, not five-plus-two independent
coverage. The five listed first are genuine.

---

## 4. Controls

A tool that reported failure on everything would satisfy § 3 and be useless.

**Control A — a restore that genuinely succeeded still verifies OK, multi-path,
on this round's own four files, with the fixed tool:**

```
  ✓ bin/perry-restore-check matches HEAD (8cd3027409dd…)
  ✓ tests/test_restore_check.py matches HEAD (385b8890b93c…)
  ✓ work/reference/review-constraints.md matches HEAD (95d6974424eb…)
  ✓ bin/README.md matches HEAD (5f8d6ba5c785…)
exit=0
```

Four paths, exit 0, and **no `!` line** — the self-check returned `clean`, so
the new gate does not fire on the normal case. This is also the multi-path
interface the whole finding was about, exercised positively.

In the test module the same control is `test_two_matching_paths_exit_zero`
(two paths, both matching, exit 0, `[True, True]`) and
`test_the_override_still_works_for_an_unverifiable_helper` (the escape hatch is
documented, so it must exist).

**Control B — the § 3 scenario re-run against the fixed tool.** Same mutated
helper, same corrupt file, same absence of a repository, no flags:

```
perry-restore-check: REFUSING — this script could not be checked against a committed copy.
    …/loose2/perry-restore-check is not inside a git repository
exit=2
```

Round 1 gave exit 0 and a false `✓` here. And the override still works, which is
what keeps the refusal from being a brick wall:

```
$ … --allow-modified-self HEAD b.py
  ! self-check unverifiable: …
  ✓ b.py matches HEAD (3b5d5c371295…)
exit=0
```

---

## 5. Suite and lint

`bin/perry-lint --root .` → **0 error(s), 37 warning(s)**. The warnings are
pre-existing census lines (unbounded specs, blank summaries) and none concerns
this change.

**Baseline measured twice, and the second measurement is the one that counts.**

| run | when | result |
|---|---|---|
| my branch at the stub commit (no edits) | 2026-09-03 | 114 modules · **3268** tests · **all green** |
| my branch with the fix | 2026-09-04 | 114 modules · **3278** tests · **2 failures** |
| **the identical stub tree, re-run as a real repo, same moment** | 2026-09-04 | 114 modules · **3268** tests · **the same 2 failures, and nothing else** |

+10 tests, and **not one bit redder**. The third row is the honest control: I did
not accept my first baseline once it disagreed with the second.

### The two failures are a wall-clock time bomb, and they are not mine

```
FAIL: test_without_the_witness_the_four_are_unobservable
      (test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable)
      [conformance.in_progress_with_no_live_run[].means]
FAIL: test_the_same_mutation_is_silent_without_the_witness
      (test_contract_key_parity.TestTheWitnessedKeysRedden)
      [conformance.in_progress_with_no_live_run[].means]
```

Mechanism, from `bin/perry-task:6301`:

```python
if task["status"] == "in_progress" and task["id"] not in live \
        and idle >= in_progress_limit:
```

`idle` is measured against **wall-clock time**. Both tests are anti-vacuity
controls asserting that `in_progress_with_no_live_run[].means` is *unobservable*
in the live project without the witness fixture — i.e. that the live collection
is empty. The live board carries two `in_progress` rows (`TASK-067` and
`TASK-256`, this one). As real time advances past the idle threshold with the
worktree's event log frozen at its commit, the collection stops being empty, the
key becomes observable without the witness, and the control flips to failing.

This is not my change: it fails identically on the stub tree with **zero** of my
edits present, and it was green on that same tree yesterday. It is also not the
`tests/test_one_header_rule.py` flake the coordinator warned about — that module
was green in every run here. Not fixed: different module, and the fix is either
a frozen clock or PMO-owned state. **Flagged for a row.**

---

## 6. Findings I did NOT fix

Per `review.md § What V4 does not judge`, and per the review's own § 7.3, which
assigns these to their own rows rather than to this FAIL.

1. **§ 4 — `resolve()` follows symlinks** (`bin/perry-restore-check:117`, now
   `:134`). `rel` is derived from the resolved path, so the tool answers about a
   symlink's *target* and reports a good restore over a file git calls modified.
   Reviewer-assigned to its own row. `git ls-tree -r` finds **no tracked
   symlinks** in this repository, so it is unreachable for a Perry restore today
   — but it is a genuine false-PASS path in the shipped tool, and it is the one
   reason the "use `git show` instead" warning cannot be retired unconditionally.
2. **§ 5.1 — the one-home principle ships four copies.** The reviewer asked that
   the sentence be corrected in the result document either way, so: **the round-1
   result's claim that "the explanation exists in exactly one file" is false.**
   The reason sentence appears in `review-constraints.md`, `perry-restore-check`,
   `bin/README.md` and `tests/test_restore_check.py`. What the guard actually
   asserts is that the *section heading* has one home under
   `work/reference/*.md`, and that one 34-character string is absent from
   `review.md`. I did not reduce the count — a tool's `--help` and a test's
   docstring explaining themselves is defensible, and re-litigating it is a row,
   not this fix.
3. **§ 5.2 — both one-home guards are literal-substring guards**, defeated by 4
   of the reviewer's 5 attacks. **My own new guard has the same limit and I am
   declaring it rather than overstating it:**
   `test_the_documented_guarantee_matches_the_tool` asserts the string
   `--allow-modified-self` is present in both pages. It catches the claim being
   reverted or the flag renamed. It does **not** catch a paraphrase that
   reintroduces the overstatement while keeping the flag name.
4. **§ 5.3 — the `review.md` pointer is invisible to `test_pointers_resolve`**
   because the citation wraps across a newline and the `POINTER` regex excludes
   `\n`. Untouched.
5. **The `test_contract_key_parity` wall-clock failures** in § 5 above.

## 7. What I did not check

- **Windows and non-POSIX paths.** macOS only.
- **The rounds that already consumed `bin/perry-restore-check`.** I did not
  identify or re-run them. Any that ran from a scratch copy got an
  `unverifiable` answer that this change would now refuse.
- **Concurrency**, and the `TASK-298` shared-scratchpad collision. Not
  exercised — though I did observe a cross-worktree artifact: my first
  backgrounded baseline printed a tree-guard line naming a *different* agent's
  worktree (`agent-a546bb08cbb158fc5`) before being killed. I did not chase it;
  the run was re-done in the foreground. Possibly worth a row.
- **The other 113 test modules** beyond three full-suite runs.
- **The `--json` consumer contract** beyond reading the payload. My new tests
  now depend on `results[].reason`, which nothing else pins.
- **`perry-lint --reviews --strict`** — a pre-check, runs before dispatch.
- **The spec's `Remainder`** — the PMO's ephemeral briefs and the out-of-repo
  memory file.

## 8. Files changed

| file | change |
|---|---|
| `bin/perry-restore-check` | gate on `verdict != "clean"`; refusal names the verdict; docstring states why `unverifiable` refuses |
| `tests/test_restore_check.py` | 15 → 25 tests: `TestHelperVerdictIsNotJustTheLastPath` (7), two `unverifiable` refusals + override control, one doc guard |
| `work/reference/review-constraints.md` | the false unconditional claim corrected; the override named |
| `bin/README.md` | the same sentence corrected |
| `perry/evidence/2026-09/TASK-256-round2-result.md` | this document |

No PMO-owned file was touched: `perry/BOARD.md`, `perry/tasks.jsonl`,
`perry/journal/` and `.perry/events.jsonl` are untouched, as are
`schema/state-schema.json` and everything under `claims`. Nothing was pushed and
no PR was opened.
