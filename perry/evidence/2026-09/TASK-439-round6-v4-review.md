# TASK-439 — round 6, V4 review

Under review: `15e8084b` ("TASK-439 round 6, USER-930 answer A: both windows
tested, and the writer tells the truth") — `bin/perry-task §
linkage_add_change`'s `--unlinked` refusal, and
`tests/test_add_refuses_without_an_answer.py` (`between_phases()` beside
`gap()`, four window tests, two writer-message tests). Criteria:
`perry/evidence/2026-09/TASK-439-spec.md`, as scoped by `USER-928` answer A and
`USER-930` answer A. I wrote none of the six rounds and reviewed none of them.
I read round 5's verdict and took none of its conclusions as settled.

**Result: FAIL**, on one finding charged FAIL. Both of the round's claims
reproduce as written: round 5's verdict mutation now reddens three tests, and
the writer's new branch is pinned and its control is too. But the window's new
fixture writes `""`, a spelling `goals/reference/phases.md § score-phase` step
7 does not name. The spelling it names first, **deleting `phase/CURRENT`**,
reaches `number == ""` through its own branch of `_register_state`. Two edits to
that branch leave all 3833 tests at the baseline's result. One is a
single-token deletion that makes every `add` in the window end in a traceback.
The other is the obvious shape of the recorded ROW-A fix, and it brings back
round 2's FAIL-2 cell for cell. Five more findings are charged ROW.

---

## 0 · Base check — wrong as predicted, recovered

| step | command | result |
|---|---|---|
| HEAD as cut | `git log --oneline -1` | **`583f024f`** "Merge bin-contract-phase-a…" |
| does it carry the work | `git merge-base --is-ancestor 15e8084b HEAD` | **no** (exit 1) |
| distance | `git rev-list --count 583f024f..15e8084b` | **144** |
| tree | `git status --short` | clean, no output |
| branch | `git branch --show-current` | `worktree-agent-a65672d21bf5228a8` |
| parent of the commit | `git log --format='%h %p' -1 15e8084b` | `15e8084b 89f67aef` |

HEAD lacked the commit and the tree was clean, so I fast-forwarded **my own
branch only**: `git merge --ff-only 15e8084b` (145 files). Re-asserted:
`git log --oneline -1` → `15e8084b`, and `git merge-base --is-ancestor 15e8084b
HEAD` exit 0. `15e8084b` is `main`'s tip at dispatch, so "strict ancestor of
main" does not apply, as the dispatch said.

**Method.** `perry-task add` is a write tool, so nothing was run against the
project. Every probe and mutation ran in **`git archive 15e8084b` copies**
under the session scratchpad, in my own subdirectory `t439r6v4-a65672/`. That
means three copies: `head/` (unmutated probes), `mut/` and `suite/`
(mutations). The probes drive the copy's real binary on temporary projects
built by the suite's own `tests/test_add_writes_the_edge.py § Fixture.project`.
The live tree was written only by this file. Before writing it:
`bin/perry-restore-check 15e8084b bin/perry-task
tests/test_add_refuses_without_an_answer.py` → both ✓.

`review-constraints.md` says a round does not commit. The dispatch asks for this
verdict to be committed on my own branch, and I followed the dispatch for this
one file and nothing else.

---

## 1 · What reproduces

- **The module has 45 tests, all green** on the archive copy (`BASE`).
- **Claim 1, M1.** Round 5's MF, re-run as **R1** (`bin/perry-task:2850`
  `number = P.linkage_phase_number(slug)` → `… or "003"`), is **RED, 3**:
  `test_a_blank_pointer_is_not_read_as_a_phase`,
  `test_in_the_window_the_honest_answer_is_refused_and_the_row_still_files`,
  `test_the_window_files_the_row_with_a_warning`. That matches the result's
  count and its "incl.".
- **Claim 1, M3.** Swapping `between_phases()`'s pointer back to `003-storage`
  (`tests/…:544`) is **RED, 4**, including
  `test_the_window_fixture_really_is_blank`. **`gap()` is still `004-next`**
  (`:528`), so the fixture was added beside it and nothing was replaced.
  `test_the_phase_match_is_load_bearing` still holds.
- **Claim 2, M2.** **R7**: the writer's new condition (`:2792`) → `False` is
  **RED, 1**: `test_unlinked_on_an_unreadable_register_says_it_could_not_be_read`.
  **R6**: `== "unparseable"` → `!= "declared"`, so that a no-phase register
  also gets "could not be read", is **RED, 1**:
  `test_unlinked_between_phases_keeps_its_own_sentence`. The control does
  control something.
- **The new writer sentence is true where it fires**, on every store that
  reaches it (§ 3). On a conflict marker, a mid-line truncation and a BOM,
  `perry-lint --root <project>` names the `JSONDecodeError` with its column.

---

## 2 · FAIL-1 — the window is pinned for `""`, and its prescribed spellings reach `number == ""` through branches no test enters

### The enumeration the lead asked for

`_register_state` (`bin/perry-task:2848-2850`):

```python
pointer = state_root / "phase" / "CURRENT"
slug = pointer.read_text(encoding="utf-8").strip() if pointer.exists() else ""
number = P.linkage_phase_number(slug)
```

Every spelling a user or `score-phase` can leave, and the code path by which
it reaches "no phase":

| spelling | who produces it | path to `number == ""` | a test writes it? |
|---|---|---|---|
| file deleted | **step 7's first spelling**: "delete the file" | `if pointer.exists() else ""` | **no** |
| `(none)` | **step 7's second spelling**; also **this repository's own pointer**, `ba29671f` 2026-08-28 | `.strip()` → regex `^(\d{3})\b` fails | **no** |
| `none`, `—` | accepted as blank by `bin/perry-goals:1434` and `bin/perry-lint:1309` | regex fails | no |
| `""` | a truncating editor, `: > CURRENT` | `.strip()` → `""` | **yes**: `between_phases()` |
| `"\n"`, `"  \t\n"` | an editor that saves a newline | `.strip()` → `""` | no, but the same line as `""` |

`grep -rn 'CURRENT").unlink\|(none)' tests/*.py` finds no test that deletes the
pointer or writes `(none)`. Every shared fixture names a real phase
(`sample-project` `002-release-pipeline`, `witness-project` `001-witness`).

**Behaviour on the unmutated code, all nine spellings × 6 store states × 3
flags = 162 runs** (§ 3's table is the summary). With an intact register, every
blank spelling behaves identically: neither flag files the row with the window
warning, `--unlinked` is refused with the no-phase sentence, and `--kr` files.
**The product is right on every spelling today.** The finding is about what
guards it.

### The mutations

All in the archive copy, anchored by line number, run on the module and then on
the full suite. The baseline was 131 modules, 3833 tests, 5 red.

| # | `bin/perry-task` | edit | module | full suite |
|---|---|---|---|---|
| **R2b** | **:2849** | delete ` if pointer.exists() else ""` | **GREEN** 45/45 | **GREEN**: 3833, same 5 reds |
| **R2c** | **:2849** | `slug = …` → `try: slug = pointer.read_text(…).strip()` / `except OSError: return ("unparseable", "")` | **GREEN** 45/45 | **GREEN**: 3833, same 5 reds |
| R2 | :2849 | `else ""` → `else "003-storage"` (a missing pointer read as the open phase) | GREEN | GREEN, same 5 |
| R3 | :2850 | `… or ("003" if slug else "")` (a non-numeric pointer read as 003) | GREEN | GREEN, same 5 |

"Same 5 reds" is by module and per-module count
(`test_blank_cell_is_one_rule` 1, `test_contract_key_parity` 2,
`test_one_header_rule` 1, `test_resume` 1). § 7 names them.

**What the product does under each, measured** (intact register, the fixture's
KRs for 003):

| `phase/CURRENT` | R2b: neither / `--unlinked` / `--kr` | R2c: neither / `--unlinked` / `--kr` |
|---|---|---|
| `""` | files + warns / refused / files | files + warns / refused / files |
| `(none)` | files + warns / refused / files | files + warns / refused / files |
| **deleted** | **traceback `FileNotFoundError` / traceback / traceback** | **refused: "exists and could not be read" / refused / `--kr` files** |

**R2b** makes every `perry-task add` fail with a Python traceback, on every
project that has a register, from the moment step 7 is followed as written
until the next `plan-phase`. That covers `--kr`, `--unlinked` and neither flag.
The spec's own rung argument names exactly this consequence: *"a defect in it
either blocks every `add` or lets through the thing it exists to catch"*.

**R2c is the more likely of the two, and the reason is on the record.** Round 5's
ROW-A, left in evidence by `USER-930`, is *"`add --kr` tracebacks on an
unreadable `phase/CURRENT`"*, with the recorded fix *"guard the `CURRENT` read"*.
That guard goes on this exact line, and `FileNotFoundError` is a subclass of
`OSError`. A guard that treats an unreadable pointer like an unreadable register
therefore reclassifies a **deleted** pointer too. Measured, that restores
round 2's FAIL-2 cell for cell, in step 7's first spelling:
- neither flag is refused, with a sentence false of that project ("could not be
  read");
- `--unlinked` is refused;
- only `--kr` files, and in the window no key result exists for an open phase,
  so that `--kr` is a guess.

`between_phases()`, which writes `""`, stays green through both. That state is
what `USER-928` answer A was granted to prevent.

### Why FAIL and not ROW

- **It is round 5's FAIL-1, one spelling over, and round 5 named the spelling.**
  Round 5 charged a green mutation restoring round 2's FAIL-2 in the window as
  FAIL. Its § 9 asked for *"a gate test for the cleared pointer, **absent and
  `(none)`**, the two spellings step 7 names"*. R2c is that consequence for
  "absent", through a branch the new fixture does not execute.
- **`review.md § 2`** puts a green mutation at V4: *"the guard does not work, or
  the test does not test it."* That applies twice here, across the whole suite.
- **It answers `§ 0` question 3**: a gate weakened, or an `add` blocked, on the
  one state the user decided, reached by following the documented procedure.

**The strongest case against, stated so the user can weigh it.** `USER-930`
answer A says *"a fixture with a **BLANK** `phase/CURRENT` is added"*, and the
round did exactly that. But the same answer gives the purpose: *"so both the
phase match **and the score-phase step 7 window** are exercised"*. Step 7 spells
that window "delete the file or write `(none)`". `""` is a third spelling that
shares none of the deleted file's code path. If the user meant `""` literally
and accepts that the other two spellings go unpinned, this FAIL is theirs to
overrule. The reproduction above says what that would accept.

### What would make it pass

Run `between_phases()`'s window assertions over **the deleted file and
`(none)`** as well as `""`: a parameter or two sibling fixtures. At minimum run
`test_the_window_files_the_row_with_a_warning` and
`test_in_the_window_the_honest_answer_is_refused_and_the_row_still_files`.
R2b and R2c should then go red, and R1 and M3 should stay red. No product code
needs to change.

---

## 3 · Every message path, and whether each clause is true of the state that reaches it

The states come from the 162-run matrix: 6 stores (intact, conflict marker,
mid-line truncation, UTF-8 BOM, non-UTF-8 byte, no store) × 9 pointers (`003`,
`004-next`, `""`, `\n`, whitespace, `(none)`, `none`, `—`, deleted) × 3 flags.
Mode-`000` and directory stores were not re-driven (§ 8).

| id | site | fires on | clauses |
|---|---|---|---|
| G2 | `cmd_add` :3848 | intact × `003`, neither | true |
| G1 | `cmd_add` :3836 | conflict/truncated/BOM/non-UTF-8 × **every** pointer, neither | carries `--root`. **"It is NOT the between-phases window" is false when the pointer is cleared** (ROW-2); "a truncated write … lands here" is round 5's ROW-G |
| FA | fallback :4066 | no store × every pointer, neither | true |
| FN | fallback :4066 | intact × `004-next` and every blank spelling, neither | true for the blank spellings. **"the window step 7 opens" is false for `004-next`** (ROW-3) |
| W2 | writer :2740 | no store × every pointer, `--unlinked` | true (TASK-394's, unchanged) |
| W3 | writer :2754 | OSError on read | not re-driven (§ 8) |
| **W4 (new)** | writer :2792 | conflict/truncated/BOM × every pointer, `--unlinked` | "could not be read" true on all 27. **"Run `perry-lint`, which says why" is false whenever `add` reached the project through `--root` or `PERRY_PROJECT`** (ROW-1); "This is NOT a register with nothing for the current phase" is at odds with W5 on a cleared pointer (ROW-2) |
| W5 | writer :2800 | intact × `004-next` and every blank spelling, `--unlinked` | true |
| — | writer, non-UTF-8 store | `--unlinked` and `--kr` → traceback before W4 is reached | round 5's ROW-B, unchanged, not this round's |

No refusal fires on a state where the row should have been filed, and no row is
filed on a state that should have refused.

---

## 4 · ROW findings — real, reported, not charged against the row

### ROW-1 — the writer's new refusal hands back `perry-lint` without the project's root, and bare `perry-lint` then vouches for a different store

`bin/perry-task:2798`: *"Run `perry-lint`, which says why."* The gate's
refusal for the same store (`:3845`) says
`perry-lint{lib.root_flag(ctx['project_root'])}`. `lib.root_flag`'s docstring
(TASK-253) exists because a printed command without its root runs against the
reader's cwd. `perry-task` resolves its project from `--root`, then
`PERRY_PROJECT`, then cwd (`:8667`); `perry-lint` resolves from `--root` or
cwd only (`:5879`). Measured, `add --unlinked --root <conflicted project>`
refused with W4, then:

| where the reader runs the printed `perry-lint` | output |
|---|---|
| `--root <that project>` | `linkage-store-unreadable … JSONDecodeError …` (true) |
| cwd = another, clean project | `· linkage store: 4 record(s), 0 malformed` |
| cwd = the tool checkout (where the fixture runs `add` from) | **rc 0**, `· linkage store: 258 record(s), 0 malformed` |

**Why ROW.** It is a message defect: the refusal is right and nothing is
written. The writer has no `ctx`, so the fix is a parameter. It is new in this
round, and it is the class this row has FAILed on before, so it is worth filing
promptly.

### ROW-2 — an unparseable register in the window: the refusal is unpinned, undecided, and its messages contradict themselves

- **R4** (`:2845`) makes `_register_state` read the pointer before the store,
  the order `_current_store_phase` uses eleven lines below. It is **GREEN on
  the module and the full suite** (3833, same 5).
- Under R4, a conflicted register with a cleared pointer, in all three
  spellings, **files the row at rc 0** behind "`linkage.jsonl` declares no key
  result for the current phase". That brings back round 3's FAIL-1, in the
  window. `--unlinked` gets the same false sentence, which is round 5's ROW-C.
  `TestAnUnreadableRegisterIsItsOwnAnswer.unparseable()` only ever uses
  `003-storage`.

**Why ROW and not FAIL.** Unlike FAIL-1, it is not settled which outcome is
right in this cell. `USER-928` A stands the gate down where no current phase
exists; round 5 refuses where the register cannot be read; this cell is both.
Filing loses nothing the intact-register window does not already lose, since
`--unlinked` is refused there as well. Refusing only asks for the store to be
repaired first. The current messages were written without the cell in mind:
- G1 tells a project whose `phase/CURRENT` was just cleared *"It is NOT the
  between-phases window"*;
- W4 says *"NOT a register with nothing for the current phase"* on a pointer
  where W5 says exactly that of an intact register.

This is a decision to take and then pin, not a defect to charge.

### ROW-3 — the fallback warning says the step-7 window is open when `phase/CURRENT` names an open phase

On `gap()`'s own state, intact register × `004-next`, the warning says
*"the window `goals/reference/phases.md § score-phase` step 7 opens, until the
next `plan-phase`"* (quoted in full from the probe). Step 7 clears the pointer;
this pointer names phase 004. That is `plan-phase` step 1 having run without
the register being written. `test_the_warning_does_not_claim_the_store_is_missing`
pins only the substring "no key result for the current phase". The code is
round 5's, not this round's. **ROW**: warning wording, and the row files
correctly.

### ROW-4 — three of the six new tests are thinner than their names

- **`test_a_blank_pointer_is_not_read_as_a_phase`, the absence assertion.**
  - **R8**: an unrelated `Refused` injected on every no-phase `add` (`:4066`)
    reddens 8 tests and leaves this one **green**. It passes on any failure that
    prints something else.
  - **R9**: R1 (blank read as 003) plus rewording the gate to
    ``neither `--kr` nor `--unlinked` `` (`:3851`) leaves it **green** while the
    blank pointer *is* read as a phase. It is coupled to one wording.
  - In both runs its siblings held the class
    (`test_the_window_files_the_row_with_a_warning`,
    `test_in_the_window_the_honest_answer_is_refused…`). On its own it cannot
    fail for the reason its name gives. The fix is to assert `returncode == 0`
    beside the absence check.
- **`test_the_window_files_the_row_with_a_warning`** asserts only that
  `"warning"` appears. **R5** (a blank pointer classified `absent`, `:2850`) is
  **GREEN on the module and full suite**, while the window's warning becomes
  *"this project has no `linkage.jsonl`"*, false about a file the caller can
  see. That is the sentence round 3 split out, and it is pinned only on
  `004-next`.
- **`test_unlinked_between_phases_keeps_its_own_sentence`** is named for the
  window but runs on its class's `gap()`, which is `004-next`. **R10** gives
  `--unlinked` on an intact register with a cleared pointer *"`linkage.jsonl`
  exists and could not be read"*. It is **GREEN on the module and full suite**:
  the writer's W5 sentence is unpinned on every blank spelling.

**Why ROW.** Every consequence is a false sentence on a refusal or a warning,
and no behaviour changes. FAIL-1's fix touches the same tests.

### ROW-5 — the new message inherits round 5's overclaim

W4 repeats *"a truncated write and a merge conflict both land here"*. As
round 5's ROW-G measured, a truncation at a line boundary or to zero bytes lands
in `no-phase` or `declared` instead. Recorded, not re-measured.

---

## 5 · The four leads, answered

1. **Blank has more than one spelling.** Nine enumerated (§ 2). All reach the
   same state on the unmutated code, over every store. Only `""` is covered;
   the deleted file and `(none)` take distinct code paths. That is FAIL-1.
2. **Every message path.** Ten paths (§ 3). One new false clause in the new
   message (ROW-1), and two contradictions in the unparseable × window cell
   (ROW-2). One pre-existing false clause (ROW-3).
3. **Six new tests, each failing for its name's reason?**
   `test_the_window_fixture_really_is_blank`: yes (M3, M3b).
   `test_the_window_files_the_row_with_a_warning`: its return-code half yes,
   its warning half no (R5). `test_in_the_window_the_honest_answer…`: yes (R1,
   R8). `test_a_blank_pointer_is_not_read_as_a_phase`: not on its own (R8, R9).
   `test_unlinked_on_an_unreadable_register_says_it_could_not_be_read`: yes
   (R7). `test_unlinked_between_phases_keeps_its_own_sentence`: yes for `gap()`
   (R6), and it does not test the window its name says (R10).
4. **The absence assertion.** It can pass on an unrelated failure (R8) and on a
   reworded gate (R9). Its siblings keep the class honest.

---

## 6 · Mutation table

All mutations were anchored by line number, with the anchor asserted to occur
exactly once on that line. The test-file anchor was asserted unique in the
file. Before every run `__pycache__` was cleared and a 1.2 s wait taken. Each
restore was written from `git show 15e8084b:<path>` bytes and asserted equal to
them after every mutation. The harness also asserted both files equal those
bytes **before** each mutation, so no mutation started from a dirty baseline.

| # | site | mutation | module (45) | full suite (3833) |
|---|---|---|---|---|
| BASE | — | none | green | 5 red (§ 7) |
| R1 | :2850 | blank read as 003 (round 5's MF / the author's M1) | **RED 3** | — |
| R2 | :2849 | a missing pointer read as `003-storage` | GREEN | GREEN (same 5) |
| **R2b** | **:2849** | **`if pointer.exists()` guard deleted** | **GREEN** | **GREEN (same 5)** |
| **R2c** | **:2849** | **`try/except OSError → "unparseable"`** | **GREEN** | **GREEN (same 5)** |
| R3 | :2850 | a non-numeric pointer read as 003 | GREEN | GREEN (same 5) |
| R4 | :2845 | pointer read before store, early `no-phase` | GREEN | GREEN (same 5) |
| R5 | :2850 | blank pointer → `absent` | GREEN | GREEN (same 5) |
| R6 | :2792 | writer: `== "unparseable"` → `!= "declared"` | **RED 1** | — |
| R7 | :2792 | writer's new branch disabled (the author's M2) | **RED 1** | — |
| R8 | :4066 | unrelated refusal on every no-phase `add` | RED 8, absence test green | — |
| R9 | :2850 + :3851 | R1 + gate reworded | RED 4, absence test green | — |
| R10 | :2792 | writer tells a cleared pointer "could not be read" | GREEN | GREEN (same 5) |
| M3 | tests :544 | fixture → `003-storage` (the author's M3) | **RED 4** | — |
| M3b | tests :544 | fixture → `(none)` | RED 1 (guard only) | — |

The author's M4 (the false sentence restored in the new branch) was not re-run.
R7 removes the same branch and reddens the same test.

---

## 7 · The suite

On the `git archive` copy, baseline: **131 modules · 3833 tests · 5 red**:
- `test_contract_key_parity` ×2 and `test_resume` ×1, the three standing reds
  the result names;
- `test_one_header_rule` ×1 and `test_blank_cell_is_one_rule` ×1, which round 5
  recorded as artefacts of an archive copy not being a repository.

Every full-suite mutation run reproduced exactly those modules and counts. The
runner wrote no per-test ids file on full runs, so the comparison is by module
and per-module count, not by test id.

The result reports 3835 tests, and my copy counts 3833. Round 5 saw the same
two-test gap, and no verdict here rests on the total.

---

## What I did not check

- **The live project under any write tool.** Every `add` here ran against a
  fixture project from an archive copy.
- **Mode-`000` and directory `linkage.jsonl`** (writer W3, gate G1) were not
  re-driven this round. Round 5 did, and this round did not touch those paths.
- **`phase/CURRENT` unreadable** (UTF-16, directory, mode `000`). That is round
  5's ROW-A, left in evidence by `USER-930`, and not re-driven. R2c models its
  likely fix; it does not test it.
- **Windows**, and a real editor's output for any spelling.
- **Whether `score-phase` tooling, as opposed to its procedure page, writes
  `phase/CURRENT`.** I found no writer in `bin/`. The spellings come from
  `phases.md § score-phase` step 7, `perry-goals`/`perry-lint`'s accepted
  sets, and this repository's own history.
- **`perry-task intake` and `route`** as entry points.
- **Per-test identity of the five suite reds** on mutated runs (§ 7): module
  and count only.
- **The author's M4** as written (§ 6).
- **The design of any fix**, including the right answer for ROW-2's cell.
- **`perry-lint --reviews --strict` on this document**, which is the
  dispatcher's pre-check.

```
=== VERDICT ===
task: TASK-439
rung: V4
result: FAIL
grade: FAIL — `§ Verification` item 3 (mutation) against `§ What it must not
       do` item 4 as answered by USER-928 A and USER-930 A ("so both the phase
       match and the score-phase step 7 window are exercised"): step 7's first
       spelling, a DELETED phase/CURRENT, reaches the no-phase state through a
       branch no test enters, and edits there that block every add or restore
       round 2's FAIL-2 ship through the whole suite
criteria: perry/evidence/2026-09/TASK-439-spec.md
checked: base was 583f024f, 144 behind, clean — fast-forwarded own branch only
         to 15e8084b and re-asserted; module 45 green on a git archive copy;
         the author's M1/M2/M3 reproduced (R1 red 3, R7 red 1, M3 red 4);
         9 phase/CURRENT spellings x 6 store states x 3 flags = 162 add runs
         on fixture projects, every message classified and its clauses judged;
         perry-lint on the three stores that reach the new message, with and
         without --root and from three cwds; 15 line-anchored mutations, 7 of
         them also across the full suite (3833 tests, baseline's 5 reds by
         module and count every time); product behaviour measured under R2b,
         R2c, R4, R5 and R10; every restore verified against git show
         15e8084b:<path>; live tree verified with bin/perry-restore-check
         15e8084b (2 files ✓)
not-checked: the live board under any write tool; mode-000/directory stores and
         unreadable phase/CURRENT (round 5 drove them; out of this round's
         scope); Windows; score-phase tooling beyond phases.md; intake and
         route; per-test ids of the suite reds; the author's M4 as written; the
         design of any fix, including ROW-2's undecided cell; perry-lint
         --reviews on this document
proof: FAIL-1 — tests/test_add_refuses_without_an_answer.py:544 writes only
       `""`; goals/reference/phases.md:282 prescribes "delete the file or write
       `(none)`". A deleted pointer reaches `number == ""` at
       bin/perry-task:2849 via `if pointer.exists() else ""`, which no test
       enters. Deleting that guard (R2b) makes every `add --kr/--unlinked/
       neither` on a register-holding project with no phase/CURRENT exit 1
       with FileNotFoundError; replacing it with `try/except OSError: return
       ("unparseable", "")` (R2c, the shape of round 5's recorded ROW-A fix)
       makes the same project refuse neither-flag and --unlinked and accept
       only --kr — round 2's FAIL-2. Both leave 45/45 module tests and
       3833 suite tests at the baseline's result.
=== END VERDICT ===
```
