# TASK-439 — round 7, V4 review

Under review: `1c515a30` ("TASK-439 round 7: every spelling score-phase step 7
can leave"). It changes one file, `tests/test_add_refuses_without_an_answer.py`:
it adds `WINDOW_SPELLINGS`, the `window()` fixture and three tests over them,
and tightens `test_in_every_window_spelling_the_row_files_while_unlinked_is_refused`.
No product code changed. The criteria are
`perry/evidence/2026-09/TASK-439-spec.md`, as scoped by `USER-928` answer A and
`USER-930` answer A. I wrote none of the seven rounds and reviewed none of
them. I read round 6's FAIL and the round-7 result, and I took none of their
conclusions as settled.

**Result: PASS.** Round 6's FAIL is closed. Every product edit to the two
`phase/CURRENT` read sites makes the module go red on the spelling it breaks.
That covers the deleted pointer, `(none)`, blank and newline, at both the gate
and the writer. It includes round 6's two suite-green edits, R2b and R2c. The
author's per-site mutation table reproduces cell for cell, and so does their
disclosed first-draft green. I extended the spelling list to 22 pointer states.
All 19 non-numeric ones take one of the three branches the four fixtures
already cover.

Five findings, all ROW, and none of them is a product edit that passes on its
own:
- a drift of `WINDOW_SPELLINGS` that the round's own fixture test cannot see
  (ROW-1);
- crash-for-refusal at 8 of 9 `add`-path refusal sites (ROW-2);
- a BOM before a real phase (ROW-3);
- a missing `phase/` directory (ROW-4);
- the author's suite line (ROW-5, not a defect).

---

## 0 · Base check — wrong as predicted, recovered

| step | command | result |
|---|---|---|
| HEAD as cut | `git log --oneline -1` | **`583f024f`** "Merge bin-contract-phase-a…" |
| does it carry the work | `git merge-base --is-ancestor 1c515a30 HEAD` | **no** (exit 1) |
| tree | `git status --short` | clean, no output |
| branch | `git branch --show-current` | `worktree-agent-a8f12e932379bcf22` |
| main's tip at dispatch | `git log --oneline -3 02825582` | `02825582` → parent `1c515a30` → `865b8946` |

HEAD lacked the commit and the tree was clean, so I fast-forwarded **my own
branch only**, with `git merge --ff-only 02825582` (148 files). Then I
re-asserted: `git log --oneline -1` gives `02825582`, and
`git merge-base --is-ancestor 1c515a30 HEAD` exits 0.

`git diff --stat 1c515a30 02825582` touches only `.perry/events.jsonl`,
`perry/BOARD.md`, `perry/evidence/2026-09/TASK-237-spec.md`, the 2026-09-14
journal and `perry/tasks.jsonl`. So `bin/perry-task` and the test module are
byte-identical at both refs. Before writing this file,
`bin/perry-restore-check 1c515a30 bin/perry-task
tests/test_add_refuses_without_an_answer.py` gave both ✓.

**Method.** `perry-task add` is a write tool, so nothing was run against the
project. Every probe and mutation ran in a **`git archive 1c515a30` copy** in my
own scratch subdirectory `t439r7v4-a8f12e/`. There were three copies: `base/`
for unmutated probes, and `mut/` and `suite/` for mutations. The probes drive
the copy's real binary on projects built by the suite's own
`tests/test_add_writes_the_edge.py § Fixture.project`, the call `window()`
itself makes.

The live tree was written only by this file. `review-constraints.md` says a
round does not commit. The dispatch asks for this verdict to be committed on my
own branch, and I followed the dispatch for this one file and nothing else.

**A collision in my own harness, disclosed.** I started a foreground
mutation run on `mut/` while a background full-suite run was still using it.
The background harness's own post-restore check caught that
(`AssertionError: bin/perry-task differs from git show 1c515a30 after N2740
(restore)`). A restore can only turn a mutated file back into the green
original. So the reds from that window stand, and the two results that could
have been false greens were discarded: N2754 (module) and N2740 (suite). Both
were re-run alone in the foreground, and the tables below carry only the
re-runs. After that, concurrent runs used separate copies (`mut/`, `suite/`).
The harness asserts both files equal `git show 1c515a30` before and after every
mutation.

---

## 1 · What reproduces

- **The module has 48 tests, all green** on the archive copy.
- **The author's mutation table**, re-run independently:

| author | mine | site | result claimed | result measured |
|---|---|---|---|---|
| M1 gate | G1 | `bin/perry-task:2849` `else ""` → `else "003-storage"` | RED 2 (`deleted`) | **RED 2**, both `[spelling='deleted']` |
| M1 writer | W1 | `:2868` same | RED 1 | **RED 1** `[spelling='deleted']` |
| M2 gate | G2 | `:2850` `"(none)"` read as `003-storage` | RED 2 | **RED 2** `[spelling='(none)']` |
| M2 writer | W2 | `:2869` same | RED 1 | **RED 1** `[spelling='(none)']` |
| M3 gate | G3 | `:2849` delete ` if pointer.exists() else ""` | RED 2 | **RED 2** `[spelling='deleted']` |
| M3 writer | W3 | `:2868` same | RED 1 after the tightening | **RED 1** `[spelling='deleted']` |
| M4 | T3 | `tests/…:588` `pointer.unlink()` → `pointer.write_text("")` | RED, fixture test | **RED 1** `test_every_window_spelling_is_really_what_it_says [spelling='deleted']` |
| disclosed first draft | T4W3 | `tests/…:628-631` removed (the `Traceback` and `refused` assertions) + W3 | green | **GREEN**, so the tightening is what makes W3 red |

- **Round 6's "what would make it pass"**:
  - R2b is my G3: **RED 2**.
  - R2c is my G4 (`:2849` → `try: … except OSError: return ("unparseable", "")`): **RED 2**, `[spelling='deleted']`.
  - R1 is my G5 (`:2850` `… or "003"`): **RED 11**, across all four spellings and the three older window tests.
  - R3 is my G6 (a non-numeric pointer read as 003): **RED 2** `[(none)]`, where round 6 measured it green.
- **Both sites at once**, which is how a real "fix" would land:
  - GW3 (guard removed at both): **RED 2**.
  - GW4 (`try/except OSError` at both): **RED 2**.
- **The writer site on its own**: W5 (blank read as 003) is **RED 5**, and W6
  (non-numeric) is **RED 1**.
- **W4**, `:2868` → `try: … except OSError: return ""`, is **GREEN**, and
  correctly so. It is an equivalent mutant: `""` is what the `else` branch
  already returns for a deleted pointer, and the only other thing it changes is
  a traceback on an unreadable pointer.

---

## 2 · The spelling enumeration (lead 1)

`_register_state` (`:2848-2850`) and `_current_store_phase` (`:2867-2869`) read
the pointer identically. `linkage_phase_number` (`viewer/parsers.py:4117`)
matches `^(\d{3})\b` after `.strip()`. A pointer therefore reaches "no current
phase" by exactly **three branches**:
1. `exists()` is false;
2. `.strip()` leaves `""`;
3. the regex fails on a non-empty slug.

The four fixtures enter all three: `deleted` enters branch 1, `blank` and
`newline only` enter branch 2, and `(none)` enters branch 3.

**Unmutated behaviour, 22 pointer states × 3 flags = 66 `add` runs**
(`neither` / `--unlinked` / `--kr <store KR>`):

| `phase/CURRENT` | branch | neither | `--unlinked` | `--kr` | fixture? |
|---|---|---|---|---|---|
| `003-storage\n` (control) | — | refused | rc 0, declared | rc 0 | (every other class) |
| deleted | 1 | rc 0 + warning | refused | rc 0 | **yes** |
| no `phase/` directory at all | 1 | same | same | same | no (ROW-4) |
| dangling symlink | 1 | same | same | same | no |
| `(none)\n` | 3 | same | same | same | **yes** |
| `(none)` no newline, `(none)\r\n` | 3 | same | same | same | no, but the same branch and the same line |
| `(None)`, `NONE`, `none`, `—` | 3 | same | same | same | no, same branch |
| `""` | 2 | same | same | same | **yes** |
| `\n` | 2 | same | same | same | **yes** |
| `  \t \n`, `\r\n` | 2 | same | same | same | no, same branch |
| BOM only, BOM + `\n`, BOM + `(none)` | 3 | same | same | same | no, same branch |
| **BOM + `003-storage`** | 3 | **rc 0 + warning** | **refused** | rc 0 | no (ROW-3) |
| `003-storage\r\n` | — | refused | rc 0, declared | rc 0 | no, and correct |
| a non-UTF-8 byte | — | traceback | traceback | traceback | round 5's ROW-A, left in evidence by `USER-930` |
| `CURRENT` is a directory | — | traceback | traceback | traceback | round 5's ROW-A |

No tool writes `phase/CURRENT`. I checked with
`grep -rn CURRENT bin goals templates | grep -i 'write_text\|unlink\|rm \|echo'`,
which returns nothing. Every spelling is hand-typed from `phases.md:282`
("delete the file or write `(none)`").

Every step-7 spelling is tested. Every other window spelling shares a branch
and a line with a tested one. The mutations that break a branch (G1–G6, W1–W3,
W5, W6) go red. So the list is complete **for the edits it exists to catch**.
The two states it does not reach are below.

---

## 3 · Findings — all ROW

### ROW-1 — the fixture test checks `window()` against `WINDOW_SPELLINGS` and never checks `WINDOW_SPELLINGS` against the names it gives: a one-token drift puts round 6's FAIL back, and the whole suite stays green

`test_every_window_spelling_is_really_what_it_says` (`tests/…:593-602`)
compares what `window()` wrote with `self.WINDOW_SPELLINGS[spelling]`. That is
a comparison of the fixture with its own table. It catches `window()` drifting
from the dict (T3, red). It cannot catch the dict drifting from the key's
meaning, and that is the drift its docstring names: *"a spelling that silently
became another one is how round 5 lost this window"*.

| # | edit | module | full suite |
|---|---|---|---|
| T1 | `tests/…:577` `"deleted": None,` → `"deleted": "",` | GREEN 48 | — |
| T2 | `:578` `"(none)": "(none)\n",` → `"(none)": "",` | GREEN 48 | — |
| **T1G3** | T1 + round 6's R2b (`bin/perry-task:2849` `exists()` guard deleted) | **GREEN 48** | **GREEN**: 3836, the baseline's 5 reds by name |
| T1G4 | T1 + round 6's R2c (`try/except OSError → "unparseable"`) | GREEN 48 | — |
| T2G2 | T2 + `(none)` read as phase 003 | GREEN 48 | — |
| T5G3 | `:577` entry deleted + R2b | GREEN 48 | — |

Under T1G3 the subTest is still named `spelling='deleted'` while it runs a blank
pointer. Meanwhile every `add` on a project with a register and no
`phase/CURRENT` ends in `FileNotFoundError`, which round 6 measured for R2b.

**Why ROW.** No edit to product code passes today. G3 alone is red, and the
guard's failure needs a test-file edit that a reviewer of that diff would see.
It is the same class as round 6's ROW-4 ("tests thinner than their names"),
which was graded ROW. The fix is one line per key: assert each key against a
literal (`deleted` → not `exists()`, `(none)` → `"(none)"`, …) rather than
against the table. It is recorded because rule 2 says a green mutation is a
finding either way, and because round 5 lost this window to exactly this kind
of test edit.

### ROW-2 — at 8 of the 9 refusal sites on the `add` path, a crash that carries its message passes as a refusal; round 7 fixed the category at one of them (lead 2)

Round 7's disclosure is that a test could not tell a refusal from a crash.
Enumerated across the category: every `raise Refused(` that `add` can reach, in
two crash shapes. The first is `raise RuntimeError(` with the message text
kept, so the traceback's last line still carries it. The second is a
`NameError` raised before the message is built, so the text is absent, which is
the shape of the author's `FileNotFoundError`. `main` prints a refusal as
`perry-task: refused — …` (`:8793`) and lets anything else propagate.

| `bin/perry-task` | refusal | crash, message kept (module) | crash, message lost (module) | full suite |
|---|---|---|---|---|
| :2731 | writer, `--kr` + `--unlinked` (defence in depth; `cmd_add` refuses first at :3675) | GREEN | GREEN | not run: unreachable from `add` |
| :2740 | `--unlinked`, no store | GREEN | GREEN | message lost: **RED**, `test_same_action_linkage…test_a_project_with_no_store_refuses_the_declaration` |
| :2754 | store `OSError` on read | GREEN | GREEN | message lost: **GREEN**, 5 baseline reds by name |
| :2793 | `--unlinked`, unparseable store | GREEN | RED 1 | — |
| **:2800** | `--unlinked`, no phase (the window) | **RED 4** | **RED 5** | — |
| :3675 | `--kr` + `--unlinked` | GREEN | RED 1 | — |
| :3712 | blank `--kr` | GREEN | RED 3 | — |
| :3838 | neither flag, unparseable store | GREEN | RED 1 | — |
| :3850 | **neither flag, register declares** (the gate) | GREEN | RED 5 | message kept: **GREEN**, 5 baseline reds by name |

Tests in the module that assert **only** a non-zero exit, and so pass on a
crash of either shape:
- `test_neither_flag_is_refused` (:106);
- `test_in_the_window_the_honest_answer_is_refused_and_the_row_still_files`
  (:561-562);
- `test_the_honest_answer_is_not_refused_while_the_row_is_filed` (:673);
- `test_an_unparseable_register_is_refused` (:760);
- `test_the_gap_and_the_unreadable_store_are_told_apart` (:808-810).

Their message-reading siblings catch the message-lost shape everywhere except
:2731 (unreachable) and :2754. Only the new test asserts `refused` and no
`Traceback`, and only on :2800.

**What the product does under C3850, measured through the module.**
`TestNothingWasWritten`'s three tests stay green, so no row, event or id is
written. The exit code is 1 either way, and the traceback's last line carries
the refusal text. What changes is presentation: a Python traceback in place of
`perry-task: refused —`, and under `--json` no `{"refused": …}` payload.

**Why ROW.** No state is corrupted, no gate is weakened, and no wrong answer is
reported. The command still stops and still writes nothing. The one site where
a crash would sit inside the between-phases window, :2800, is the site round 7
pinned. :2754 (an unreadable store) is round 5's territory, which `USER-930`
left in evidence. The fix pattern is already in the module: assert `refused`
and no `Traceback` wherever a refusal is asserted.

### ROW-3 — a BOM before a real phase reads as "no current phase", and `add` files the row behind the window's warning

With `phase/CURRENT` = `﻿003-storage\n` and a register declaring 003:
- neither flag: **rc 0**, the row is filed, and the warning says *"`linkage.jsonl`
  declares no key result for the current phase"*;
- `--unlinked`: **refused**.

`read_text(encoding="utf-8")` keeps U+FEFF, and `str.strip()` does not remove
it. The read tools agree that the pointer is broken:
- `perry-lint --root` exits 1: `✗ phase/CURRENT [current-phase-resolves]
  points at '﻿003-storage' but phase/﻿003-storage.md does not exist`;
- `perry-state` warns *"phase/CURRENT points at a phase file that does not
  exist."*

**Why ROW.** This behaviour predates round 7 and round 7 did not change it.
`add` agrees with every other reader (`parsers.load_snapshot:4895-4901`,
`perry-goals:1432`) that no phase resolves, and `perry-lint` reports it as an
error. The consequence is the pre-row outcome (a filed row and a warning) on a
pointer the project's own linter is already flagging. The warning's clause is
false of this store. That is the false-message class, and `§ 2` files it as a
row.

### ROW-4 — a missing `phase/` directory reads as a separate state only under a mutation no test sees

G7 (`:2849` `else ""` → `else ("" if pointer.parent.is_dir() else
"003-storage")`) is **GREEN on the module and on the full suite** (3836, the
baseline's 5 by name). W7, the same edit at `:2868`, is **GREEN on the module**.
Unmutated, a missing `phase/` behaves exactly like a deleted `CURRENT` (§ 2).

**Why ROW.** Step 7 deletes the file, not the directory. A project with a
register and no `phase/` directory has lost its phase documents and snapshots
too, and the mutation is contrived: nothing in the code distinguishes the two
today. Recorded so the enumeration is complete rather than implied.

### ROW-5 — the result's suite line and mine differ, and nothing rests on it

The result reports 3838 tests with 3 reds. My archive copy has **131 modules ·
3836 tests · 5 red**:
- `test_contract_key_parity` ×2 and `test_resume` ×1, the three the result
  names;
- `test_one_header_rule` ×1 and `test_blank_cell_is_one_rule` ×1, which rounds
  5 and 6 recorded as artefacts of an archive copy not being a repository.

Round 6 saw the same two-test gap. It is not a defect.

---

## 4 · The four leads, answered

1. **Is the spelling list complete?** Yes, for its purpose. There are three
   branches and 19 non-numeric spellings, and every one shares a branch and a
   line with a fixture (§ 2). The out-of-list states are BOM + a real phase
   (ROW-3), a missing `phase/` (ROW-4), and the unreadable pointers already in
   evidence.
2. **Other tests that assert only non-zero?** Five, named in ROW-2. The category
   was enumerated over nine refusal sites in two crash shapes.
3. **Can the fixture test pass if `window()` and `WINDOW_SPELLINGS` drift
   together?** Yes. It passes whenever the dict drifts at all, and with R2b on
   top the whole suite stays green (ROW-1).
4. **Both read sites.** Confirmed independently, cell for cell, including the
   writer's M3 and the author's first-draft green (§ 1).

---

## 5 · Mutation table

Every mutation was line-anchored, with the expected text asserted on that line
and asserted unique on it. Anchors were checked against the original numbering
and applied bottom-up. Before each run: `__pycache__` cleared and a 1.2 s wait.
Both files were asserted equal to `git show 1c515a30:<path>` before every
mutation and again after its restore. The module ran with `python3 -m unittest`,
named failures included; the full suite ran with `tests/parallel`, reds compared
**by test id** with the baseline.

| # | site | module (48) | full suite (3836) |
|---|---|---|---|
| BASE | — | green | 5 red (§ ROW-5) |
| G1 / W1 | 2849 / 2868, deleted → 003 | RED 2 / RED 1 | — |
| G2 / W2 | 2850 / 2869, `(none)` → 003 | RED 2 / RED 1 | — |
| G3 / W3 | 2849 / 2868, `exists()` guard removed | RED 2 / RED 1 | — |
| G4 / W4 | 2849 / 2868, `try/except OSError` | RED 2 / GREEN (equivalent) | — |
| G5 / W5 | 2850 / 2869, blank → 003 | RED 11 / RED 5 | — |
| G6 / W6 | 2850 / 2869, non-numeric → 003 | RED 2 / RED 1 | — |
| G7 / W7 | 2849 / 2868, no `phase/` dir → 003 | GREEN / GREEN | G7: GREEN, 5 baseline |
| GW3 / GW4 | both sites | RED 2 / RED 2 | — |
| T1, T2, T1G4, T2G2, T5G3 | `WINDOW_SPELLINGS` drift (± product) | GREEN | — |
| T1G3 | drift + R2b | GREEN | GREEN, 5 baseline |
| T3 | `window()` writes blank for `deleted` | RED 1 | — |
| T4W3 | tightening removed + W3 | GREEN | — |
| C2731 … C3850 | crash, message kept | RED only at 2800 (4) | C3850: GREEN, 5 baseline |
| N2731 … N3850 | crash, message lost | GREEN at 2731, 2740, 2754; RED elsewhere | N2740: RED (+1 named, § ROW-2); N2754: GREEN, 5 baseline |

---

## What I did not check

- **The live project under any write tool.** Every `add` here ran against a
  fixture project from an archive copy.
- **Windows, and a real editor's output** for any spelling. The BOM and CRLF
  states were written as bytes.
- **Unreadable pointers and stores** (mode `000`, UTF-16, directory,
  non-UTF-8). These are round 5's ROW-A and ROW-B, left in evidence by
  `USER-930`. I recorded their current tracebacks (§ 2) and did not re-grade
  them.
- **One unnamed extra red in the re-run N2740 suite pass.** That run reported
  6 modules and 7 tests red. It names `test_same_action_linkage` in addition to
  the baseline modules, and my output filter cut the list before a sixth. The
  red I cite for N2740 is the named one. The extra one is unattributed, and I
  did not re-run it alone.
- **Full-suite runs** for T1, T2, T1G4, T2G2, T5G3 and W7. These are test-only
  edits, or the writer twin of G7, whose gate form was run.
- **`perry-task intake` and `route`** as entry points.
- **The product's `--json` output under the crash mutants.** It is inferred
  from `main`'s handler at `:8789-8794`, not driven.
- **The design of any fix**, including ROW-1's literal expectations.
- **Round 6's five ROW findings.** They stay in evidence under `USER-930`, and I
  did not re-drive them.

```
=== VERDICT ===
task: TASK-439
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-439-spec.md
checked: base was 583f024f, clean, lacked 1c515a30 — fast-forwarded own
         branch only to 02825582 and re-asserted ancestry; module 48 green on
         a git archive copy of 1c515a30; the author's M1-M4 at BOTH read sites
         (bin/perry-task:2849-2850 gate, :2868-2869 writer) and their
         first-draft green reproduced cell for cell; round 6's R2b and R2c now
         RED; 22 phase/CURRENT states x 3 flags = 66 add runs on fixture
         projects; perry-lint and perry-state on a BOM pointer; 42 line-anchored
         mutations (read sites, WINDOW_SPELLINGS drift, crash-for-refusal at 9
         add-path refusal sites in two shapes), 5 also across the full suite
         (3836 tests), reds compared by id; every restore verified against git
         show 1c515a30; live tree verified with bin/perry-restore-check
         1c515a30 (2 files ✓)
not-checked: the live board under any write tool; Windows and real editors;
         unreadable pointers/stores (round 5 ROW-A/B, in evidence); one unnamed
         extra red in the N2740 suite re-run; full-suite runs for the test-only
         drift mutants and W7; intake and route; --json output under crash
         mutants; the design of any fix; round 6's ROW findings
proof: tests/test_add_refuses_without_an_answer.py:576-633 runs the window over
       deleted, (none), blank and newline; bin/perry-task:2849 guard removed
       (R2b) and replaced by try/except OSError (R2c) are each RED 2
       [spelling='deleted'], and :2868 guard removed is RED 1. Five ROW
       findings, none a product edit that passes alone — ROW-1: tests/…:577
       "deleted": None -> "" plus bin/perry-task:2849 guard removed leaves the
       full suite at baseline, because :593-602 checks window() against its own
       table; ROW-2: raise RuntimeError at :3850 keeps the suite green, and
       only :2800 of 9 refusal sites asserts `refused` and no Traceback
=== END VERDICT ===
```
