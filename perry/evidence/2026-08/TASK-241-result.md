# TASK-241 — a decorated path in `.perry/conformance.md` is no longer a declaration

> Branch `coding/task-241-conformance-decoration`, forked from `main` at `658e8c9`.
> Every write-side command in this record ran against `git archive` copies or
> synthetic `mktemp` projects. Nothing was run against `/Users/bytedance/proj/Perry`
> or any other worktree, and `perry-conform declare` was never run against a real
> project — adoption proposes, the user declares (`SKILL.md:197`).

---

## 1 · Which mechanism, and why it took two

The spec offered a choice: refuse a row that cannot round-trip, or strip
decoration only where a documented rule says it may be. I took the round trip,
as instructed — **and it does not reach all three shapes.** It closes two of
them completely; the third needed the second mechanism as well.

### The round trip — `render_row(parsed cells) == line`

`viewer/parsers.py § read_conformance`, after the header skip and the numeric
version check:

```python
canonical = render_row([rel, str(int(ver)), declared, route or "declare"])
...
if canonical != line:
    rec.unreadable.append((i, line.strip()))
    continue
```

The canonical form is `render_row` — the same writer `bin/perry-conform § render`
uses to produce the file — so this adds **no second definition** of what a
declaration looks like. It is **one property, not a list of decorations**, which
is the whole reason for it: a list closes the three shapes that have been found
and is defeated by the fourth. TASK-050 spent nine V4 rounds on this same file
learning that.

It closes the **backticked** and **indented** rows, and every other decoration
written *inside* the row — measured below, it also now refuses a five-cell row,
a `07` version cell, an empty route cell, and a row with trailing whitespace,
none of which it refused before.

### Fence tracking — and why the round trip cannot do this one

**A fenced row is byte-for-byte identical to a genuine one.** What makes it not
a declaration is *where it sits*, not how it is written, so no property of the
row can see it. Measured, with the round trip in and fence tracking out (this is
mutation **M2** below): the fenced trap parses as a real declaration and the
verdict flips.

So `read_conformance` now tracks fences:

```python
_FENCE = re.compile(r"^\s*(?:`{3,}|~{3,})")
...
if _FENCE.match(line):
    in_fence = not in_fence
    continue
...
if in_fence:
    rec.unreadable.append((i, line.strip()))
    continue
```

**This corrects a claim in the TASK-226 V4 review**, which called
`render(parse(row)) == row` *"a complete detector for this class."* It is a
complete detector for **in-row** decoration. The review's own row-12 check was
`render(parse(f)) == f` over the **whole file** — that one *does* catch the
fenced row, because `render()` drops the fence lines — but a whole-file fixed
point cannot be the reader's rule: the reader would then have to know
`perry-conform`'s `HEADER`, which is the second definition this file exists to
avoid. Per-row round trip plus fence tracking is the same coverage without the
coupling.

Both refusals report through `ConformanceRecord.unreadable`, which the spec
correctly identified as where this belongs — it already existed for exactly
this, and `perry-conform status` already prints it
(`bin/perry-conform:541,560`), and the enforce-gate refusal message already
appends `(N row(s) … could not be read)` (`bin/perry-conform:335`). No new
surface was invented.

---

## 2 · The three traps, planted, each with its own named test

`tests/test_conformance.py § TestADecoratedRowIsNotADeclaration`. Everything
reads through `perry-conform status` and `verdict` — the surface the gate reads
— not the parser in isolation.

| shape | named test |
|---|---|
| backticked path cell | `test_a_backticked_path_cell_is_not_a_declaration` |
| indented row | `test_an_indented_row_is_not_a_declaration` |
| row inside a ``` fence | `test_a_row_inside_a_code_fence_is_not_a_declaration` |
| the laundering | `test_a_planted_row_is_not_laundered_by_the_next_declare` |
| asterisk, unchanged | `test_an_asterisked_path_reads_exactly_as_it_did_before` |
| bolded header, unchanged | `test_a_bolded_header_row_is_still_not_a_row` |
| the real record still reads | `test_perrys_own_record_is_read_without_a_single_refusal` |

**Three shapes, three tests, per the spec.** One test covering all three would
pass with two of the three regressed — and here it would also hide that the
three are stopped by two different mechanisms (M1 and M2 below redden disjoint
sets).

**Each of the three carries its own control.** Before planting the decorated
row it plants the *undecorated* one and asserts the verdict really does flip to
`conformant`:

```python
def assert_trap_would_have_worked(self):
    self.assertEqual(self.plant(self.canonical()), (C.CONFORMANT, 0), …)
```

So none of the three can pass because the reader stopped reading, because the
fixture stopped being lint-clean, or because the row was malformed for some
fourth reason. The trap is proved live in the same test that proves it closed.
Mutation **M7** confirms the control is not decorative: an over-strict canonical
reddens the control clause, not the assertion under it.

### End to end, before and after, on two `git archive` copies

`scratchpad/demo241.sh` — synthetic `mktemp` projects, each tree's own
`bin/perry-conform`, `PERRY_HOME` unset in both so no tree's tool ever loads
another tree's schema (the named hazard).

```
BEFORE — main @ 658e8c9 (git archive copy), shape version 2
  backticked  BOARD.md → conformant unreadable=0
  indented    BOARD.md → conformant unreadable=0
  fenced      BOARD.md → conformant unreadable=0
  asterisk    BOARD.md → undeclared  unreadable=0
  laundering: after a legitimate `declare .perry/hook.md`, the record holds:
      | .perry/hook.md | 2 | 2026-08-30 | declare |
      | BOARD.md | 2 | 2026-08-28 | declare |      ← laundered, plain, canonical

AFTER — coding/task-241 @ d8ec034 (git archive copy), shape version 2
  backticked  BOARD.md → undeclared unreadable=1
  indented    BOARD.md → undeclared unreadable=1
  fenced      BOARD.md → undeclared unreadable=1
  asterisk    BOARD.md → undeclared unreadable=0      ← identical to BEFORE
  laundering: after a legitimate `declare .perry/hook.md`, the record holds:
      | .perry/hook.md | 2 | 2026-08-30 | declare |
```

All three shapes flip a real file to **conformant** on `main` and are **refused
and reported** on the branch. The laundering is closed: the legitimate declare
of a *different* file no longer canonicalises the planted claim.

## 3 · The asterisk case did not regress

Three independent checks, all agreeing:

1. **End to end, above**: `asterisk → undeclared, unreadable=0` on `main` and on
   the branch — byte-identical behaviour.
2. **`test_an_asterisked_path_reads_exactly_as_it_did_before`**: the record still
   parses to the decorated key `**BOARD.md**`, with `unreadable == []`, and
   `BOARD.md`'s own verdict is still `undeclared`. ``strip("` ")`` never removed
   asterisks, so `| **BOARD.md** |` is *already* exactly what `render` would
   write for the key `**BOARD.md**` — the round trip lets it through by
   construction, not by an exception carved for it.
3. **The bolded `| **File** |` header** is still squashed to `file` and skipped
   *before* the guard runs, so it is not reported as an unreadable row —
   `test_a_bolded_header_row_is_still_not_a_row`, plus
   `tests/test_one_header_rule.py § TestTheFifthCopy`, both green. Mutation
   **M5** reverts `squash` to the old ``strip("` ").lower()`` and reddens both.

**Mutation M6** is the guard against the over-fix: widening the cell strip to
``strip("`* ")`` — the natural "while we are here, handle bold too" change —
would make `| **BOARD.md** |` declare the *real* key `BOARD.md`. It reddens
`test_an_asterisked_path_reads_exactly_as_it_did_before`, so the pin is live.

## 4 · Mutations — anchor, old text, named test that reddened

Harness: `scratchpad/mut241-conformance-decoration.sh`, uniquely named. It
**refuses to start on a dirty tree** (`git status --porcelain
--untracked-files=all`), **asserts the target is GREEN before mutating**
(`green_check`, which `fail`s if the run is not `OK`), anchors **by line number
with an assertion on the old text** (`fail`s on "anchor drift" otherwise),
clears every `__pycache__` and **sleeps past the whole-second boundary** before
each run, and restores from a `mktemp` backup **verified by `md5`** on every
exit path. Every restore in the log reported
`md5 039882edd56bb9ad63fb42c9a0d27de0 ✓`.

I checked **every guard I wrote, not only the one the spec names.**

| # | anchor | old text → new | named test(s) that went RED | stayed green |
|---|---|---|---|---|
| M1 | `viewer/parsers.py:491` | `if canonical != line:` → `if False:` | `…_a_backticked_path_cell_is_not_a_declaration`, `…_an_indented_row_is_not_a_declaration`, `…_a_planted_row_is_not_laundered_by_the_next_declare` | fenced, asterisk, header, real record |
| M2 | `viewer/parsers.py:423` | `if in_fence:` → `if False:` | `…_a_row_inside_a_code_fence_is_not_a_declaration` | all six others |
| M3 | `viewer/parsers.py:417` | `if _FENCE.match(line):` → `if False:` | `…_a_row_inside_a_code_fence_is_not_a_declaration` | backticked, indented, real record |
| M4 | `viewer/parsers.py:492` | `rec.unreadable.append((i, line.strip()))` → `pass` | `…_a_backticked_path_cell_is_not_a_declaration`, `…_an_indented_row_is_not_a_declaration` | fenced (reported on the other branch) |
| M5 | `viewer/parsers.py:447` | `if squash(rel) in ("file", "path")…` → `if rel.strip("` ").lower() in …` | `…_a_bolded_header_row_is_still_not_a_row`, `tests/test_one_header_rule.py § TestTheFifthCopy` (2 failures) | asterisk, backticked |
| M6 | `viewer/parsers.py:434` | ``cells = [c.strip("` ")…`` → ``c.strip("`* ")`` | `…_an_asterisked_path_reads_exactly_as_it_did_before` | backticked, header, `TestTheFifthCopy` |
| M7 | `viewer/parsers.py:485` | `render_row([rel, str(int(ver)), …` → `str(int(ver) + 1)` | `…_perrys_own_record_is_read_without_a_single_refusal`, and the **control clause** inside `…_a_backticked_path_cell_is_not_a_declaration` | — |

**Nothing I wrote can be deleted with the suite unchanged.** M1–M3 cover the two
refusal mechanisms and the fence toggle separately; M4 covers the *reporting*
half, so a guard that refuses silently is not enough; M5 and M6 cover the two
behaviours the spec said must not move; M7 covers the two tests that no other
mutation reddened.

M1 leaving the fenced test green, and M2/M3 leaving the backticked and indented
tests green, is the measurement behind § 1: **the two mechanisms are disjoint,
and a single test over all three shapes would have concealed that.**

## 5 · Baselines — runner and tree

`bash tests/run`, all on 2026-08-30, same host:

| tree | runner | modules · tests | failures |
|---|---|---|---|
| `git archive` copy of **`main` @ `d2467fc`** | `bash tests/run` | 100 · 2992 | **3** in 2 modules |
| `git archive` copy of **branch HEAD `d8ec034`** | `bash tests/run` | 100 · 2999 | **3** in 2 modules |
| the **live branch worktree** (`wt-241`, all six stores minted) | `bash tests/run` | 100 · 2999 | **3** in 2 modules |

`+7 tests` is exactly the seven added here. The three failures are the same
three in all three runs, and all three are pre-existing on `main`:

- `test_diagnose.DecisionsAreCountedPerRecordNotPerMention.test_the_queue_register_reconciles_with_the_queue_on_this_repository`
- `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`
- `test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`

Two notes on the numbers, because both matter:

- **These are not the brief's 98 / 2882 / 3.** `main` has moved: it is now
  `d2467fc`, three commits ahead of my fork point `658e8c9`. I re-measured the
  `main` baseline myself on a fresh `git archive` copy rather than carrying the
  brief's figure, which is why the comparison holds.
- **The live worktree shows 3, not 5.** The brief predicted 5 on a tree with
  live board state, the two extra being `test_contract_key_parity`'s
  data-dependent witness tests. They did not fire here. I did not chase why;
  the relevant fact is that the archive copy and the live worktree of this
  branch produced **identical** results, so nothing in this change is
  board-state-dependent.
- All three commits `main` gained since my fork point touch only `perry/` and
  `.perry/` — records, specs and journal, **no code and no tests** (verified with
  `git diff --name-only`). So `2992 → 2999` is a clean comparison.

`test_board_render`'s field test — the filed defect where a row's Next action
prose contains an enum word — did not fire in any of these runs.

`python3 -m unittest discover -s tests` on the **`git archive` copy of branch
HEAD `d8ec034`**: `Ran 2999 tests in 823.634s`, **`FAILED (failures=6,
skipped=4)`**. Same test count as `bash tests/run` on the same tree, and
**exactly 3 more failures** — the brief's stated delta, and the three extra are
exactly the `test_risks_store` double-import artefact it names:

- `test_risks_store.TestTheReadersAreOneFunction.test_the_bullet_and_placeholder_rules_are_one_object`
- `test_risks_store.TestTheReadersAreOneFunction.test_the_columns_are_one_list`
- `test_risks_store.TestTheReadersAreOneFunction.test_the_register_header_predicate_is_one_object`

The other three are the same three `tests/run` reports. I did not run `discover`
on `main` or on the live worktree.

## 6 · What is outside `read_conformance`

The spec asked me to keep the edit inside the function and to say so if I could
not. **Three lines are outside it**, all in the same file, none inside another
parser:

1. `viewer/parsers.py:43` — the shared import line, now
   `from tables import UnrenderableCell, render_row, split_row, squash`.
2. `viewer/parsers.py:372–379` — the `_FENCE` pattern, module level beside
   `_CONFORMANCE_ROW`, matching the existing shape of the file.
3. `tests/test_one_header_rule.py § TestTheFifthCopy.probe` — see § 7.

**`TASK-050` at `b5e7be3` changes that same import line** (`from tables import
header_index, split_row, squash`) **and one line inside `read_conformance`**
(`squash(rel)` → `header_index([rel]).column("file", "path")`, two lines above
where my guard begins). Both are textual conflicts on merge and both resolve
mechanically:

- import → `from tables import UnrenderableCell, header_index, render_row, split_row, squash`
- header check → keep TASK-050's line; my guard sits below it, untouched.

The two changes are semantically orthogonal — theirs decides *which cell is the
header*, mine decides *whether a non-header row is canonical*. **Whoever merges
second should re-run `mut241-conformance-decoration.sh`; its M5 anchor text
(`squash(rel)`) will need updating to TASK-050's line.**

`TASK-235` replaced `parse_decisions`, which this change never touches.

## 7 · The one test fixture I changed, and why it kept its power

`tests/test_one_header_rule.py § TestTheFifthCopy.probe` wrote its data row as
`` | `BOARD.md` | 2 | 2026-08-18 | migrate | `` — **a backticked path**, which
this change now refuses. It made
`test_a_bolded_header_is_not_reported_as_a_broken_row` red, correctly.

The row is now plain. The decoration under test in that class is on the
**header**, not the path, so the row's own shape was incidental. The test keeps
all of its power: mutation **M5** reverts `squash` to the old rule and
`TestTheFifthCopy` goes red with 2 failures — measured, not asserted.

## 8 · What I did not do, and what I could not verify

- **I did not fix, and did not widen scope to, the row that is now *deleted*
  rather than laundered.** `declare` rewrites the whole file from
  `record.declarations`, so any row the reader calls unreadable is **dropped
  from the record by the next declare**. That is pre-existing — it was already
  true of the non-numeric-version rows `read_conformance` has always refused —
  but this change **enlarges the set of rows it happens to**, from one shape to
  four. A user who backticks a path now sees the row reported by
  `perry-conform status` and then silently removed by their next declare. This
  is fail-closed rather than fail-open, and strictly better than laundering, but
  it is a real edge and **it deserves its own row**: either `declare` preserves
  unreadable rows through the rewrite, or it refuses to rewrite while any exist.
  I did not file it — the PMO owns the board.
- **I did not convert the file to `.perry/conformance.jsonl`.** Out of scope per
  the spec (`TASK-234`).
- **Behaviour I changed beyond the three named shapes, deliberately and
  untested by a named test of its own**: a row with **more than four cells**, a
  **leading-zero version cell** (`07`), an **empty route cell**, and a row with
  **trailing whitespace** are now `unreadable` where they were previously parsed
  (the first three) or accepted (the last). All four are consequences of the one
  property, and all four are the safe direction. Only the four shapes in the
  table above have named tests; I verified the rest by hand, once, in a scratch
  script. **CRLF is not affected** — `Path.read_text` applies universal
  newlines, so no `\r` reaches the comparison.
- **I did not re-run `main`'s suite on the live worktree**, only on a `git
  archive` copy. The branch was measured both ways.
- **I did not verify the fenced-row behaviour against a *nested* or
  *info-stringed* fence beyond ` ```markdown ` and ` ~~~ `**, both of which I
  checked by hand and both of which are refused. A fence opened and never closed
  swallows the rest of the file — every row after it is reported unreadable,
  which is fail-closed and loud, but I have not written a named test for it.
- **`perry/BOARD.md` and `perry/tasks.jsonl` are untouched**, as instructed.
- **`bin/perry-tasks --dry-run`** was never used; the hazard did not arise.
- **The harness and the demo script are session scratch files, not committed** —
  `perry/evidence/` holds markdown only, by this repository's own convention.
  The mutation table above carries the anchor, the old text, the replacement and
  the named test for each of the seven, which is enough to rebuild either from
  scratch; the harness's own refusals are described in § 4.
