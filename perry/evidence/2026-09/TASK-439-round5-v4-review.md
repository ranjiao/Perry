# TASK-439 — round 5, V4 review

Under review: `f79b75a6` ("TASK-439 round 5: an unreadable register is its own
answer") — `bin/perry-task § _register_state` and the gate and fallback warning
in `cmd_add`, `bin/README.md`, `tests/test_add_refuses_without_an_answer.py`.
The same commit's `perry/asks.jsonl` change (`USER-929`, TASK-236) was ignored
as instructed. Criteria: `perry/evidence/2026-09/TASK-439-spec.md`. I wrote none
of the five rounds and reviewed none of them; I am bound by neither round 4's
FAIL nor its "what a PASS needs" list.

**Result: FAIL**, on one finding charged FAIL. Round 5's F-1 fix is real and
holds on every unparseable form I could produce. F-2's fix **moved** the gate's
test coverage instead of widening it: the phase match is now pinned, and the
between-phases window that `USER-928` answer A exists for is no longer pinned
by anything. Seven further findings are charged ROW, each with its reason.

---

## 0 · Base check — it was wrong, as predicted, and was recovered

| step | command | result |
|---|---|---|
| HEAD as cut | `git log --oneline -1` | **`583f024f`** "Merge bin-contract-phase-a…" |
| does it carry the work | `git merge-base --is-ancestor f79b75a6 HEAD` | **no** (exit 1) |
| distance | `git rev-list --count HEAD..888cf365` | **139** commits behind |
| tree | `git status --short` | clean, no output |
| strict ancestor of `main` | `git merge-base --is-ancestor HEAD main` | yes; `main` = `888cf365` |
| the tip's parent | `git log --format='%h %p' -1 888cf365` | `888cf365 f79b75a6` — as the dispatch said |
| branch | `git branch --show-current` | `worktree-agent-a3f01a9193a3e0bbf` |

All three preconditions held, so I fast-forwarded **my own branch only** with
`git merge --ff-only 888cf365` (135 files). Re-asserted after: HEAD
`888cf365`, and `git merge-base --is-ancestor f79b75a6 HEAD` exit 0.
`git diff --stat f79b75a6 888cf365` over every file in scope (`bin/perry-task`,
`bin/README.md`, `viewer/parsers.py`, `bin/lib/__init__.py`, `bin/perry-lint`,
both `test_add_*` modules) is empty, so `888cf365`'s copies **are** the commit
under review.

This is the seventh consecutive dispatch from this session to arrive at
`583f024f`.

**Method.** `perry-task add` is a write tool, so nothing was run against the
project under review. Every probe drives a **`git archive` copy** of the real
binaries — `888cf365` (round 5) and `f79b75a6^` (round 4), side by side — against
temporary projects built by the suite's own fixture
(`tests/test_add_writes_the_edge.py § Fixture.project`), under the session
scratchpad. Every mutation was made in that copy. The live tree was never
written except for this file: `bin/perry-restore-check 888cf365 bin/perry-task
bin/README.md tests/test_add_refuses_without_an_answer.py viewer/parsers.py` →
all four ✓, exit 0.

**A collision I caused, disclosed.** The session scratchpad is shared with
other agents working concurrently. My first probe and harness were written
to top-level `scratchpad/probe.py` and `scratchpad/mutate.py`, which already
existed and belonged to another agent; I overwrote both (the other agent
rewrote `probe.py` minutes later), and my first `git archive` extract went into
`scratchpad/head/` and `scratchpad/r4/`, which may have overwritten an older
copy of the same name. Nothing in any repository was touched. Every result
below comes from a clean re-extraction into `scratchpad/t439r5v4/`.

`review-constraints.md` says a round does not commit; the dispatch asks for
this verdict to be committed on my own branch. I followed the dispatch for
this one file and nothing else.

---

## 1 · What reproduces, and what round 5 got right

- **F-1 is fixed on every unparseable form, not just the tested one.** Six
  distinct ways to make `linkage.jsonl` exist and not load, each over a store
  that declares KRs for the open phase, with neither flag:

  | store | round 4 (`f79b75a6^`) | round 5 (`888cf365`) |
  |---|---|---|
  | one `<<<<<<< HEAD` line | rc=0, row filed, between-phases warning | **rc=1, refused**, nothing filed |
  | last line truncated mid-JSON | rc=0, filed | **rc=1, refused** |
  | UTF-8 BOM at byte 0 | rc=0, filed | **rc=1, refused** |
  | a non-UTF-8 byte inside a string | rc=0, filed | **rc=1, refused** |
  | mode `000` | rc=0, filed | **rc=1, refused** |
  | `linkage.jsonl` is a directory | rc=0, filed | **rc=1, refused** |

  The round-4 rows also confirm the `_register_state` docstring's measurement
  ("went from refusing to filing the row at exit 0 … a between-phases warning")
  — it is a measurement that happened, on this input.
- **Round 5's M2 reproduces.** My MA — `bin/perry-task:2836`, the gate's phase
  match → `startswith("")` — is **RED, 5 tests**, including
  `test_the_phase_match_is_load_bearing`. Round 4's green F-2 mutation is red.
- **The writer's copy of the phase match is pinned too.** MB, the same edit at
  `:2856` inside `_current_store_phase`, is RED on
  `test_the_honest_answer_is_not_refused_while_the_row_is_filed`.
- **The four states agree with the writer and the readers everywhere except
  where § 4 says.** Across 23 inputs × 4 flag variants, `--unlinked` was
  accepted in exactly the states `_register_state` calls `declared` and refused
  in every other.
- **The module has 39 tests**, as the result says.

---

## 2 · FAIL-1 — the between-phases window `USER-928` answer A was granted for is no longer pinned by any test

**The mutation.** `bin/perry-task:2832`, anchored by line number, in the
scratch copy:

```python
-    number = P.linkage_phase_number(slug)
+    number = P.linkage_phase_number(slug) or "003"
```

That makes a blank, `(none)` or absent `phase/CURRENT` read as the phase the
fixture store declares. It is precisely the state
`goals/reference/phases.md § score-phase` step 7 prescribes — *"clear
`phase/CURRENT` (delete the file or write `(none)` until the next
`plan-phase`)"* — re-classified from `no-phase` to `declared`.

**Result: GREEN.** The three `add` modules, 93 tests, green. Then the full
suite, baseline and mutated, `__pycache__` cleared and past the second boundary
each time:

```
baseline : 130 modules · 3812 tests · ✗ 5 failed
MF       : 130 modules · 3812 tests · ✗ 5 failed      — the same five, by name
```

(§ 7 names the five.) **Nothing reddens.**

**Round 5 caused this; it is not inherited.** The equivalent mutation against
round 4's code and round 4's test module (`f79b75a6^`, `bin/perry-task:2804`,
the same edit in `_current_store_phase`):

```
r4 BASE : 1 module · 32 tests · all green
r4 MF   : 1 module · 32 tests · ✗ 3 failed, including
          TestTheGateKeysOffThePhaseNotTheFile.test_the_honest_answer_is_not_refused_while_the_row_is_filed
          TestTheGateKeysOffThePhaseNotTheFile.test_the_warning_does_not_claim_the_store_is_missing
```

Round 4's `gap()` wrote `""` to `phase/CURRENT`. Round 4's verdict said that
fixture reached door 2 of its table and never door 5, and asked for *"a test
… whose fixture leaves `phase/CURRENT` naming a real phase and gives the store
records for a different one"*. Round 5 did that by **editing the one fixture**
(`tests/test_add_refuses_without_an_answer.py:512-529`, now
`"004-next\n"`) rather than adding a second. Door 5 gained a test and door 1 —
the prescribed window — lost its only one. The new class's own `gap()`
(`:634`) is a copy of the same `004-next` fixture, so it does not restore it.
This is rule 1's shape exactly: the next instance was fixed, and the category
— *every* state `_register_state` classifies `no-phase` that a user reaches by
following the documented cadence — was not enumerated.

**What the product would do under the mutation, measured.** MF applied, all
three step-7 spellings, the same four variants:

| `phase/CURRENT` | neither flag | `--unlinked` | `--kr P003-O1-KR1` (the closed phase's KR) | `--kr P003-O9-KR9` (nothing declares it) |
|---|---|---|---|---|
| blank | **refused** — "the KR question has an answer" | refused — "declares no key result for the current phase" | rc 0, filed | **rc 0, filed** |
| `(none)` | **refused** | refused | rc 0, filed | **rc 0, filed** |
| absent | **refused** | refused | rc 0, filed | **rc 0, filed** |

Unmutated, all three spellings file with a warning, in round 5 as in round 4.
Under MF, both honest answers refuse, and the only way to file a row is a
`--kr` naming a key result of a phase that is not open, or one that does not
exist. That is round 2's FAIL-2 cell for cell — and the refusal still tells the
caller to *"resolve the id through `linkage.jsonl` rather than guessing it"*.

**Why this is FAIL and not ROW.** `review.md § 2`'s table puts a green
mutation at V4 — *"the guard does not work, or the test does not test it …
a product finding wearing a test's clothes"* — and round 4 charged the same
shape (M-H, a green phase-match mutation) FAIL. The consequence is the one
`USER-928` was asked about: in the step-7 window `--unlinked` is refused by the
writer (`bin/perry-task:2780-2787`) and no key result exists for a phase that
is not open, so a gate that refuses there leaves a guessed `--kr` as the only
way to file a row — round 2's FAIL-2, which answer A exists to prevent. A
regression back to that behaviour would now ship through 3812 green tests.
That is `review.md § 0` question 3, *weaken a gate*, on the one state the user
decided.

**What would make it pass.** Keep `gap()` at `004-next` and add a second fixture
for the cleared pointer — at minimum absent and `(none)`, the two spellings
step 7 names — asserting the row files. Then MF should go red, and MA should
stay red.

---

## 3 · The enumeration — every input the leads named, and some they did not

Driven through both binaries, four variants each (`neither`, `--unlinked`,
`--kr P003-O1-KR1` which the fixture declares, `--kr P003-O9-KR9` which nothing
declares). "files" = rc 0 and one row added. r4 = `f79b75a6^`.

| # | input | `_register_state` | neither | `--unlinked` | `--kr` real / fake | judged |
|---|---|---|---|---|---|---|
| 1 | `linkage.jsonl` 0 bytes | `no-phase` | files + warns | refused | files / files | consistent with every reader; not charged (§ 4 ROW-G) |
| 2 | only blank lines | `no-phase` | files + warns | refused | files / files | same as 1 |
| 3 | only non-object JSON (`[]`, `1`, `null`, `"x"`) | `no-phase` | files + warns | refused | files / files | readers see no KR either; `perry-lint` reports each line `linkage-store-malformed` |
| 4 | valid store + `null` and `[1]` lines | `declared` | **refused** | files | files / files | right — the `isinstance` guard works (but see MC) |
| 5 | `kr` records with no `phase` field | `no-phase` | files + warns | refused | files / files | `linkage_records_for_phase` drops them too, and `perry-lint` reports *"`phase` is missing and is required"*; consistent, not charged |
| 6 | `CURRENT` = `003-some-other-slug` | `declared` (`003-storage`) | refused | files | files / files | right: the number is the key, the store's spelling is returned |
| 7 | `CURRENT` = `3-storage` | `no-phase` | files + warns | refused | files / files | `viewer/parsers.py:4856` and `linkage_phase_number` see no phase either; consistent |
| 8 | `CURRENT` with a UTF-8 BOM | `no-phase` | files + warns | refused | files / files | the reader keeps U+FEFF and matches nothing either; consistent |
| 9 | `CURRENT` blank | `no-phase` | files + warns | refused | files / files | right — answer A. **Unpinned: FAIL-1** |
| 10 | `CURRENT` = `(none)` | `no-phase` | files + warns | refused | files / files | step 7's second spelling; identical in r4. **Unpinned: FAIL-1** |
| 11 | `CURRENT` absent | `no-phase` | files + warns | refused | files / files | step 7's first spelling. **Unpinned: FAIL-1** |
| 12 | `CURRENT` in UTF-16 | raises `UnicodeDecodeError` | traceback | traceback | **traceback / traceback** (r4: files / files) | **ROW-A**, a regression |
| 13 | `CURRENT` is a directory | raises `IsADirectoryError` | traceback | traceback | **traceback** (r4: files) | ROW-A |
| 14 | `CURRENT` mode `000` | raises `PermissionError` | traceback | traceback | **traceback** (r4: files) | ROW-A |
| 15 | store mode `000` | `unparseable` | refused, names `perry-lint` | refused, "could not be read to append" | refused / refused | right; `perry-lint` names the `PermissionError` |
| 16 | store is a directory | `unparseable` | refused | refused | refused / refused | right; `perry-lint` names `IsADirectoryError` |
| 17 | store + conflict marker | `unparseable` | refused | **refused: "declares no key result for the current phase"** | files / files | ROW-C, ROW-D |
| 18 | store truncated mid-line | `unparseable` | refused | same false refusal | files / files | ROW-C, ROW-D; `perry-lint` names the column |
| 19 | store with a UTF-8 BOM | `unparseable` | refused | same false refusal | files / files | ROW-C, ROW-D; `perry-lint` names the BOM |
| 20 | a non-UTF-8 byte in a string | `unparseable` | refused, **names a `perry-lint` that reports nothing** | traceback | traceback / traceback | **ROW-B**; the tracebacks are round 4's too |
| 21 | CRLF line endings | `declared` | refused | files | files / files | right |
| 22 | no store | `absent` | files + warns | refused | files / files | right — must-not item 4 |
| 23 | intact store, current phase declared | `declared` | refused | files | files / files | the control |

**Round 4 → round 5, every cell that changed:** the six `unparseable` stores
(15-20) with neither flag, rc 0 filed → rc 1 refused (the fix); and rows 12-14
with `--kr`, rc 0 filed → traceback (ROW-A). No other cell differs.

**Is anything `unparseable` that should file?** No. Every input in 15-20 is
one no reader in the project can load (`load_linkage_store` returns `None` for
all of them), so no command can answer the KR question there, and refusing is
consistent.

**Is anything `no-phase` that should refuse?** Rows 3 and 5 are stores whose
records fail the schema. The gate agrees with every reader on them, and
`perry-lint` names both. Refusing there would make the gate stricter than the
readers — a different design, and not what round 4 asked for. Not charged.

**Does any remaining caller of `_current_store_phase` disagree with the gate?**
Its only caller is the writer, `bin/perry-task:2780`, reached only for
`--unlinked`. Measured across the 23 inputs: the two agree everywhere except
15-20, where the gate says `unparseable` and the writer says "no key result
for the current phase" (ROW-C), and 12-14, where both raise.

---

## 4 · ROW findings — real, reported, not charged against the row

### ROW-A — `add --kr` now tracebacks on an unreadable `phase/CURRENT`, where round 4 filed the row

`_register_state` is called **unconditionally** at `bin/perry-task:3817`, before
either flag is tested, and reads `phase/CURRENT` with no guard at `:2831`. The
only `except` around `main` is `except Refused` (`:8683`). So a UTF-16, directory
or mode-`000` pointer ends every `add` with a Python traceback — including
`--kr <real KR>`, which in round 4 reached that read only through the
`and`-short-circuited gate and filed at rc 0. This is round 4's ROW-6, now on
every `add` rather than on two paths.

The commit message's *"A caller passing `--kr` is not blocked"* is false for
this input.

**Why ROW.** Nothing is written, and the failure is loud. The same three inputs
also stop `perry-state --json` (rc 1, `UnicodeDecodeError`), `perry-goals list`
(traceback) and `perry-lint` (rc 2), all measured — so `add` is not the only
door this input closes, and no count reports anything wrong. UTF-16 is the one
spelling a user makes without meaning to: PowerShell 5's `>` writes it.

### ROW-B — the new refusal names `perry-lint` as the tool that says why, and on a non-UTF-8 store `perry-lint` says nothing

Row 20. `parsers.load_linkage_store` decodes strictly and returns `None`;
`bin/perry-lint:5147` reads the same file with `errors="replace"`, parses it,
and emits **no** `linkage.jsonl` finding. So the refusal's clause *"Run
`perry-lint …`, which is the tool that says WHY it will not parse"* is false
on a file one editor save can produce. And `--kr` / `--unlinked` both traceback
there (`UnicodeDecodeError` escapes the writer's `except OSError`,
`bin/perry-task:2750-2751`) — unchanged from round 4.

**Why ROW.** Refusing is right and nothing is written. The false clause comes
from the two decoders disagreeing, and `bin/perry-lint` is not in this row's
scope. That is the file where the fix belongs.

### ROW-C — in the `unparseable` state, `--unlinked` is still told the between-phases story, and the comment says that cannot happen

Rows 17-19. The writer's refusal (`bin/perry-task:2780-2787`) says
*"`linkage.jsonl` declares no key result for the current phase … `/perry goals
plan-phase` writes the phase's records"*. For those stores, every clause is
false: the file declares KRs for the open phase, and the remedy does not apply
(`perry-goals`' `Register` refuses a store it cannot load,
`bin/perry-goals:1334-1340`). Round 4 recorded this as P4b. Round 5's refusal
covers only the neither-flag path. **MH is GREEN**: routing `--unlinked` to the
new, true refusal changes no test. So the branch is unpinned, and nothing
would notice the message being fixed or broken.

`bin/perry-task:3807-3809` still says *"`_current_store_phase` is the SAME
predicate the writer uses … so the gate and the writer cannot disagree"*. The
gate now asks `_register_state`, and the two disagree on exactly these three rows.

**Why ROW.** Refused, nothing written, and the message is TASK-394's, inherited
unchanged. The comment is a documentation defect (`§ 2`: file a row).

### ROW-D — `add --kr` appends to a register `perry-goals` refuses to append to, at rc 0 with empty stderr

Rows 17-19, `--kr` real **and fabricated**. Both land after the broken line and
exit 0 with nothing on stderr. `perry-goals`' `Register` refuses the same
append on the same `None`, for a stated reason: *"a register Perry cannot read
is one this tool must not append to, because the append would be judged
against a graph nobody can see"*. One store, two writers, opposite rules.
Round 5 does not create this. It **pins** it
(`test_an_answered_row_still_files`, `:667`) and argues for it (*"this command
only consulted the file to decide whether to ask"*).

**Why ROW.** No record is lost: the writer re-emits every non-blank line,
including the broken one (`:2788-2790`), so repairing the store recovers the
edge. It is also round 4's behaviour and pre-A's. Whether `add` should follow
`Register`'s rule is a store-ownership decision, not this row's defect.

### ROW-E — MC: the non-object guard in `_register_state` is unpinned

`bin/perry-task:2835`: removing `isinstance(rec, dict) and` leaves the three
`add` modules green, and the full suite at the baseline's five reds by name.
The first full MC run showed 10 reds: the baseline five plus
`test_queue_sla` and `test_cadence`, both age-based, and three the harness did
not capture by name. The re-run with the same mutation, saving the raw output,
showed the baseline's five and nothing else, so the extras are not attributed
to MC. On row 4 the guard is what separates a correct
`declared` from an `AttributeError` traceback, and the probe shows it working.

**Why ROW.** Without the guard, the result on a store with `null` lines would
be a loud traceback with nothing written. `perry-lint` already reports those
lines as `linkage-store-malformed`, and every such line comes from a hand edit.

### ROW-F — three of the new class's six tests pass against the refusal that existed before answer A

ME — `bin/perry-task:2829` `return ("unparseable", "")` → `return ("declared",
"")`, which restores the pre-A behaviour on these stores — is RED on **one**
test: `test_it_says_what_is_actually_wrong_and_who_diagnoses_it`.
`test_an_unparseable_register_is_refused`, `test_nothing_was_written` and
`test_the_gap_and_the_unreadable_store_are_told_apart` stay green. The last one
is named for telling the two apart, but asserts only `returncode != 0` for both
the unreadable store and the declared one, so it cannot. The class holds
because one message test does. MJ — round 5's own M1, `unparseable` →
`no-phase` exactly — is RED on 5, which matches the result's count.

**Why ROW.** No mutation came back green; the class is thinner than its names.

### ROW-G — two sentences on product surfaces claim more than the code does

- `bin/README.md:439-440`: *"A register that exists but will not parse is also
  refused, and says so."* With `--kr` it is not refused (rows 17-19 file). With
  `--unlinked` it is refused and says something else (ROW-C). And on row 20
  both flags traceback.
- The neither-flag refusal's *"a truncated write and a merge conflict both land
  here"* is true of a mid-line truncation (row 18). A truncation to zero bytes
  or at a line boundary lands in `no-phase` or `declared` (rows 1, 23) and files
  or refuses by that state's rule instead.

**Why ROW.** Documentation and message wording (`§ 2`: file a row).

---

## 5 · Round 3's bound — did round 5 change it?

**No.** In the step-7 window (rows 9-11), `--kr P003-O9-KR9`, a KR no record
declares, is accepted at rc 0, identically in round 4 and round 5;
`test_a_fabricated_kr_is_still_accepted_in_the_gap` still passes, now through
`004-next` instead of a blank pointer. In the new `unparseable` state, a
fabricated `--kr` is accepted too (rows 17-19), as it was in round 4.

What round 5 changes around the bound is what else is accepted there. With
neither flag refused and `--unlinked` refused, `--kr` is the only way to file a
row on an unparseable store. That is not round 2's FAIL-2 again, because the
refusal points the caller at repairing the file (`perry-lint`), not at naming
a key result, and a real key result exists to name. On row 20, though, the pointer
leads nowhere (ROW-B).

---

## 6 · Mutation table

All in `scratchpad/t439r5v4/head` (`888cf365`), anchored by line number with
the substring asserted to occur once on that line and the edit asserted to change
exactly that one line. `__pycache__` was cleared and a 1.2 s wait taken before
every run. After every mutation the restore was written from
`git show 888cf365:bin/perry-task` bytes, verified equal, and verified again at
the end.

| # | line | mutation | 3 `add` modules | full suite |
|---|---|---|---|---|
| MA | 2836 | gate phase match → `startswith("")` (round 5's M2) | **RED** 5 | — |
| MB | 2856 | writer phase match → `startswith("")` | **RED** 1 | — |
| MC | 2835 | `isinstance` guard removed | **GREEN** | **GREEN** on re-run — 3812, same 5 reds (first run: 10, not attributed; § 4 ROW-E) |
| MD | 2829 | `unparseable` → `absent` | **RED** 4 | — |
| ME | 2829 | `unparseable` → `declared` (pre-A behaviour) | **RED** 1 | — |
| MJ | 2829 | `unparseable` → `no-phase` (round 5's M1) | **RED** 5 | — |
| **MF** | **2832** | **blank / `(none)` / absent `CURRENT` read as `003`** | **GREEN** | **GREEN — 3812 tests, same 5 reds as baseline** |
| MG | 3818 | unparseable refusal also blocks `--kr` | **RED** 1 | — |
| MH | 3819 | `--unlinked` routed to the new refusal | **GREEN** | **GREEN** — 3812, same 5 reds as baseline |
| MI | 4060 | the two warning branches swapped | **RED** 2 | — |
| r4-MF | 2804 of `f79b75a6^` | MF's edit, round 4's code and tests | **RED** 3 of 32 | — |

The r4 restore was verified against `git show f79b75a6^:bin/perry-task`.
Round 5's M3 and M4 were not re-run. M3, removing the unparseable refusal, has
the same effect as MD/MJ. M4 is a message edit, and ME already shows the
message test is the one that holds the class.

---

## 7 · The suite

`scratchpad/t439r5v4/head`, baseline: **130 modules · 3812 tests · 8 workers, 5
red**. The same five by name in the MF run:

- `test_contract_key_parity` ×2, and
  `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale` — the three
  standing reds the result names;
- `test_one_header_rule.…test_git_tracks_answers_both_ways` and
  `test_blank_cell_is_one_rule.…test_it_is_not_declared_and_nothing_writes_it`
  — artefacts of a `git archive` copy not being a repository, the same two
  round 4 recorded.

Round 5's result reports 3814 tests; my copy counts 3812. I did not reconcile
the two, and no verdict above rests on the total.

---

## 8 · What I did not check

- **The live project under any write tool.** Every `add` in this document ran
  against a fixture project from a scratch copy.
- **How the prescribed window is actually spelled on real projects.** Step 7
  names a deleted file and `(none)`; I did not look at what `score-phase`
  tooling writes, or at this repository's own history of `phase/CURRENT`.
- **Whether the "ROW" for ROW-A holds on Windows.** The UTF-16 pointer is the
  realistic input, and I produced it on macOS. I did not run anything on Windows.
- **`perry-task intake` and `route` as separate entry points** into the new
  state split. Round 4 established that `intake` reaches `cmd_add`, and there is
  no track branch in `_register_state`; I did not drive either.
- **Concurrent `add` against a store being replaced.** `replace_canonical_pair`
  stages and renames, so I assumed no torn read, and did not measure it.
- **`perry-goals link` on rows 15-20**, beyond reading its `Register` refusal.
- **A fix for FAIL-1, or for ROW-A to ROW-D.** Nothing here was designed or tested.
- **Round 5's M3 and M4** as written (§ 6 says why). M1 and M2 were re-run
  (MJ, MA) and both match the result's counts.
- **`perry-lint --reviews --strict` on this document** — the pre-check runs
  before dispatch.
- **Rounds 1, 2 and 4's verdicts as artifacts.** I read them for history and took
  none of their conclusions as settled.

---

## 9 · What a PASS needs

1. A gate test for the cleared pointer, absent and `(none)`, that goes red
   under MF, **alongside** the `004-next` test, not instead of it.
2. Nothing else is required. ROW-A to ROW-G are recorded for filing: ROW-A
   (guard the `CURRENT` read, or read it only when the gate needs it), ROW-B in
   `bin/perry-lint`, ROW-C/ROW-G's wording, ROW-D as a decision for the store's
   owner.

```
=== VERDICT ===
task: TASK-439
rung: V4
result: FAIL
grade: FAIL — `§ Verification` item 3 (mutation) against `§ What it must not
       do` item 4 as answered by USER-928 A: the between-phases window
       goals/reference/phases.md § score-phase step 7 prescribes (phase/CURRENT
       deleted or `(none)`) is where `add` must keep filing, and after round 5 no
       test in the suite pins it
criteria: perry/evidence/2026-09/TASK-439-spec.md
checked: base was 583f024f, 139 behind, clean, strict ancestor of main —
         fast-forwarded own branch only to 888cf365 and re-asserted f79b75a6;
         in-scope files shown identical between f79b75a6 and 888cf365;
         23 register / phase/CURRENT inputs x 4 flag variants driven through
         BOTH 888cf365 and f79b75a6^ binaries from git archive copies on
         fixture projects, every changed cell listed; _register_state called
         directly on each; perry-lint on 12 of the stores; perry-state,
         perry-goals and perry-lint on the three unreadable-CURRENT inputs;
         10 line-anchored mutations on 888cf365 plus MF replayed on f79b75a6^,
         full suite baseline-and-mutated for MF (3812 tests, same 5 reds by
         name); every restore verified against git show <ref>:bin/perry-task;
         live tree verified with bin/perry-restore-check 888cf365 (4 files ✓)
not-checked: the live board under any write tool; what score-phase tooling
         actually writes to phase/CURRENT; Windows; perry-task intake and route
         as entry points; concurrent add; perry-goals link on unparseable
         stores beyond reading its refusal; the design of any fix; round 5's
         M3 and M4 as written; perry-lint --reviews on this document
proof: FAIL-1 — tests/test_add_refuses_without_an_answer.py:512-529 changed
       gap() from a blank phase/CURRENT to "004-next" instead of adding a
       second fixture, and :634 copies it. Mutation bin/perry-task:2832
       `number = P.linkage_phase_number(slug)` -> `... or "003"`, which makes a
       blank, `(none)` or absent phase/CURRENT refuse `add` with neither flag
       while bin/perry-task:2780-2787 still refuses `--unlinked` there, leaves
       3812 of 3812 tests at the baseline's result (the same five reds by name).
       The same edit at f79b75a6^ bin/perry-task:2804 turns round 4's module RED,
       3 of 32. Round 5 removed the only coverage of the state USER-928 answer
       A was granted for.
=== END VERDICT ===
```
