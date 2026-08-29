# TASK-203 — round 4 RESULT: one invariant, and the two places it is thinner than it looks

> Branch `coding/task-203-round4`, forked from `main` at `6c0d041`.
> Written against `perry/evidence/2026-08/TASK-203-spec.md § Amendment
> 2026-08-29 — USER-906, option B`, which binds.
>
> Every measurement below was taken in the worktree
> `…/5b3ba585-…/scratchpad/wt-203-new`. No write-side Perry tool was run
> against `/Users/bytedance/proj/Perry`.
>
> **The machine was under load average 34–47 throughout**, from seven
> concurrent agent sessions. Where that changes what a number means, it is
> said at the number rather than here.

## 0. Commits

| commit | what it is |
|---|---|
| `762bee1` | the three registers get their store writes — **and nothing that stops the write going wrong.** Deliberately RED. |
| `b09776d` | the invariant. |
| `6d45388` | the refusal's recovery line named `perry-tasks tasks-write`, which does not exist; `--dry-run` gets a test. |
| `70dfa96` | the `tasks.jsonl` call site gets a test that fails when it is deleted. |

## 1. The invariant as implemented, and where it lives

`bin/perry-task § refuse_to_shrink`, one function:

```python
SHRINK_ALLOWED = frozenset({"purge", "resolve-intake", "intake-sweep"})

def refuse_to_shrink(store, path, event_name, before, after, why="") -> None:
    if after >= before or event_name in SHRINK_ALLOWED:
        return
    raise Refused(...)
```

Two call sites, and only two:

| store | call site | what it counts |
|---|---|---|
| `tasks.jsonl` | `commit()` — `bin/perry-task:2627` | `len(current)` vs `len(records)` |
| `risks.jsonl` / `intake.jsonl` / `asks.jsonl` | `register_change()` — `bin/perry-task:2352` | records on disk vs records derived |

**Why this is not a fourth predicate.** It asks nothing about the command, the
identity of a row, or the shape of a section. It asks whether the derivation
produced fewer records than the store already holds. That one question answers
all four doors, because each of them reaches the store the same way:

- **the command name (round 1)** — a row tidied off the board by hand and then
  *any* ordinary write: the board derives n−1 records against a store of n.
- **the non-unique identity tuple (round 2)** — the same scenario with two rows
  sharing a Request. The tuple is never consulted; the count already refused.
- **the four section shapes (round 2, round 3)** — `<register>_records` returns
  `[]` for `absent`, `prose`/`bullets` and both `foreign` shapes. `0 < n` is the
  refusal. The gate does not enumerate shapes.
- **`ensure_section` ordering (round 3)** — `cmd_add`'s queue branch creates the
  section before `commit()` reads anything, so a gate that asks about the board
  is asked about a board the command already changed. **A count does not care
  when it is read.** That is exactly why option A — snapshotting the gate at
  command entry — is not needed, and it is not implemented.

**The one thing it deliberately allows.** A shrink is not always wrong; it is
wrong when nobody asked for it. `SHRINK_ALLOWED` is a frozenset of the three
names USER-906 gave, not a predicate about board state.

### What else the branch carries

`762bee1` is the feature the row was originally for — the three registers being
written by an ordinary command at all. It rebuilds, rather than patches, the
parts of `coding/task-203-register-stores` the three reviews found sound:
`REGISTER_EVENTS`; the register store joining `replace_canonical_pair`'s
canonical set so the recovery marker covers it; `carry_forward_is_addressable`
(round 2/3's `positions_still_hold`), which is **not** the invariant — § 5; and
a success line naming the files the write actually touched, which is the sixth
verification step `TASK-203-premeasurement.md` asked for, since `→ store` was
unconditional template text and was false on `risk-add`, `intake`, `ask` and
`answer` at the moment it printed.

## 2. The regression test came first, and was red

`main` at `6c0d041` carries none of the register-store code, so a test asserting
"the store is not truncated" is **vacuously green** there. The honest sequencing
is therefore two commits, and a reviewer can reproduce both numbers:

```
$ git checkout 762bee1 && cd tests
$ python3 -m unittest test_register_store_invariant
Ran 37 tests — FAILED (failures=24, errors=7)

$ git checkout b09776d && cd tests
$ python3 -m unittest test_register_store_invariant
Ran 37 tests — OK
```

The 7 errors at `762bee1` are the five unit tests of `refuse_to_shrink`, which
does not exist at that commit. The 24 failures are the doors. (The tip carries
39 tests; the two extra came in `6d45388` and `70dfa96`.)

Outside the suite, on a probe project with the same queue-mode track shape this
repository declares in `.perry/config.md § Tracks`:

```
before:  intake.jsonl  344 bytes / 3 records   md5 6f6438d04960f0aad12f94eb0c9e619c
         `## Intake` deleted from BOARD.md by hand
$ bin/perry-task add --title "a queue task probe" --track ops …
perry-task: refused — `add` would take …/intake.jsonl from 3 record(s) to 0,
and an ordinary write may never make a canonical store smaller (USER-906).
Nothing was written.
rc=1
after:   intake.jsonl  344 bytes / 3 records   md5 6f6438d04960f0aad12f94eb0c9e619c
$ bin/perry-lint
  1 error(s), 5 warning(s)
  · intake store: 3 record(s), 3 row(s) drifted
```

At `762bee1` the identical command exits **0**, leaves **0 bytes**, and
`perry-lint` reports `0 error(s)` and `intake store: 0 record(s), 0 row(s)
drifted` — the merge-hold reproduction, on a store with records to lose.

## 3. Every door it closes, with the named test that proves it

All tests are in `tests/test_register_store_invariant.py` unless named
otherwise.

| door | found by | named test |
|---|---|---|
| queue-track `add` empties a present intake store | merge-hold, round 3 | `TestTheReproduction.test_an_ordinary_add_on_a_queue_track_cannot_empty_a_present_intake_store` |
| the refusal writes nothing at all — not half a transaction | — | `TestTheReproduction.test_a_refused_register_write_writes_nothing_at_all` |
| the refusal names the store and a way forward **that exists** | — | `TestTheReproduction.test_the_refusal_names_the_store_and_a_way_forward` |
| `--dry-run` previews the refusal, not the write | — | `TestTheReproduction.test_a_dry_run_previews_the_refusal_rather_than_the_write` |
| **door 1** — a row tidied off the board by hand, then any ordinary write | round 1 finding 1 | `TestTheFourDoors.test_door_one_a_row_tidied_off_the_board_by_hand_refuses_the_next_write` |
| **door 2** — a duplicate Request, the discharged one tidied out | round 2 finding 1 | `TestTheFourDoors.test_door_two_a_duplicate_request_tidied_out_refuses_rather_than_fabricating` |
| **door 3** — every unreadable shape × every register (12 cells) | round 2 finding 2 | `TestTheFourDoors.test_door_three_no_section_shape_on_any_register_may_empty_a_present_store` |
| **door 3, `foreign` alone** — 6 cells, stated on its own | round 3 finding 2 | `TestTheFourDoors.test_door_three_the_foreign_shape_is_refused_on_every_register` |
| **door 4** — `ensure_section` rebuilding a section from one row, all three registers | round 3 finding 1 | `TestTheFourDoors.test_door_four_a_register_command_may_not_rebuild_its_section_from_one_row` |
| `intake-sweep` may still shrink | spec item 7 | `TestExplicitRemovalStillWorks.test_intake_sweep_may_shrink_the_intake_store` |
| `purge` may still shrink `tasks.jsonl` | spec item 7 | `TestExplicitRemovalStillWorks.test_purge_may_shrink_the_task_store` |
| `resolve-intake` is not blocked | spec item 7 | `TestExplicitRemovalStillWorks.test_resolve_intake_is_not_blocked_and_does_not_in_fact_shrink` |
| the rule itself, at the boundary and on the allowlist | — | `TestTheInvariantItself` (5 tests) |
| `commit()` actually asks it about `tasks.jsonl` | § 6 finding 1 | `TestTheTaskStoreCallSiteIsWired.test_commit_asks_the_invariant_about_tasks_jsonl` |
| an ordinary write reaches its store; lint prints a verdict; `intake-diff` clean | spec items 1–2 | `TestTheOrdinaryWriteReachesItsStore` (5 tests) |
| `REGISTER_EVENTS` complete both ways | round 1 finding 4 | `TestTheMapIsComplete` (4 tests) |

## 4. The four round-3 findings that are not the invariant

**1. The `foreign` shape had no test on any register.** Round 3's legend table
was appended to the end of the board file, which put it under `## Top risks`,
because `ensure_section` anchors `## Intake` before `## P0`. Three things close
it here, and the first two are controls that exist only to stop this module
repeating the mistake:

- `TestTheFixturesAreTheShapeUnderTest.test_every_shape_fixture_really_is_the_shape_it_claims`
  hands all 15 fixture boards (3 registers × 5 shapes) to `perry_store`'s own
  `<register>_section_shape` and asserts the answer.
- `…test_the_foreign_legend_lands_inside_the_named_section` asserts the legend
  text is inside the named section's body — the precise defect, as a fact about
  the text.
- `test_door_three_the_foreign_shape_is_refused_on_every_register` re-asserts
  the shape **inside** the behaviour test, so the assertion cannot pass through
  a section that is not foreign.

Both `foreign` variants are covered: a second table under the heading, and the
key column renamed (`Request`→`Ask`, `Needed from user`→`Wanted`,
`Risk`→`Hazard`).

**2. The uniqueness test could not tell uniqueness from adjacency.**
`TestTheCarryForwardJoin.test_a_repeated_identity_is_no_identity_even_when_no_two_are_adjacent`
is a unit test on `carry_forward_is_addressable` with stored identities
`A, B, A, B` — duplicated at 0/2 and 1/3, **never adjacent** — and derived rows
sitting at exactly the stored positions. Two control assertions inside the test
make the claim falsifiable rather than asserted: no two neighbouring identities
are equal, and every derived row matches its stored position, so the positional
check cannot be what answers. Mutation **M6** replaces the uniqueness clause
with a consecutive-only one; that is the distinction round 3 said could not be
made.

**3. `load_register_records` let `JSONDecodeError` escape.** It now raises
`Refused` naming the file, the **line number** and the parser's message, in the
shape `load_task_records` already uses.
`TestTheStoreIsReadHonestly.test_a_corrupt_line_in_a_register_store_is_a_refusal_not_a_traceback`
asserts no `Traceback`, the store's name, and `line 5`.

**4. `readable_as_register`'s `section` parameter was dead.** The function is
now `register_section_shape(board, key)` — the heading is looked up from
`REGISTER_SPEC`, which is where it is declared — and it returns the shape
string rather than a bool, so the refusal can say *"`## Intake` is currently
`prose`, not a table this store can read"*.
`…test_register_section_shape_reads_every_argument_it_takes` asserts the
signature is `(board, key)` and that both names appear in the body.

## 5. What the invariant does NOT cover, and what covers it instead

**A row REPLACED by hand does not move the count.** Delete a discharged intake
request and append a new one: the board still derives n records against a store
of n, the invariant is silent, and a positional merge would hand
`discharged: True` at position k to a request that is still waiting — with its
`Outcome` cell reading `—` and `perry-lint` reporting `drifted: 0`, because
`discharged` has no board column to compare against.

`carry_forward_is_addressable` answers that, and this RESULT states plainly what
it is: **not the invariant, and not a gate on any write.** It decides only
whether the one stored field a register's board has no column for —
`discharged`, `cleared`, `answered` — may be carried across. Answering `False`
drops a boolean; it never permits a write `refuse_to_shrink` forbids and never
forbids one it permits. The end-to-end proof is
`TestTheCarryForwardJoin.test_a_row_replaced_by_hand_does_not_hand_its_discharge_to_the_newcomer`,
which is an `rc == 0` write — the store IS updated — asserting the newcomer is
not marked discharged.

Keeping it is the one place round 4 kept a predicate from an earlier round, and
it is a judgement call. The reasoning: the invariant answers *may this write
happen*, this answers *is this join addressable* — two questions with two
consequences, and collapsing them would either block a legal write or fabricate
a discharge. Round 3's reviewer measured the same guard as *"over-broad, and
correctly so"*, and its error direction is safe: a discharged row is
re-reported as waiting, never the reverse.

## 6. Two findings that are thinner than the rest, stated as findings

### Finding 1 — the `tasks.jsonl` call site survived its own deletion, and now does not

**The precise shape, because "reddens nothing" was too coarse.** Two
mutations bracket it:

- **M2**, emptying `SHRINK_ALLOWED`, reddens **21** tests, **14 of them in
  `test_purge`** — `perry-task purge` refuses end-to-end through the CLI. So
  `commit()`'s call site IS reached on every task write, and its allowlist
  branch is exercised by an ordinary command.
- **M3**, deleting the call site outright, reddened **nothing** before
  `70dfa96` and reddens exactly **one** test after it. What was unreachable was
  never the call, only its *refusal* branch.

The original measurement, and why it mattered: deleting

```python
refuse_to_shrink("tasks", perry_store.store_path(state_root),
                 event.get("event") or "", len(current), len(records))
```

from `commit()` reddened **nothing**. `TestTheInvariantItself` unit-tests the
rule; it says nothing about whether `commit()` asks it. A refusal branch that
survives its own deletion is the shape TASK-095 shipped and was failed for, so
leaving it as "an assertion" would have been the wrong answer.

**Why it is hard to reach, stated rather than worked around.** `commit()` builds
`records` FROM `current` by removing at most one record and appending at most
one, so the only branch that shortens the task store is `purge` — which is in
`SHRINK_ALLOWED`. The one other input that shortens it is a store carrying the
subject's id twice, and `load_task_records` refuses a duplicate id before
`commit()` ever sees it. **The state the guard exists for is unreachable through
the CLI today.**

`70dfa96` adds
`TestTheTaskStoreCallSiteIsWired.test_commit_asks_the_invariant_about_tasks_jsonl`,
which constructs that state deliberately by replacing `load_task_records` for
the duration of one `commit(..., dry_run=True)` call. **It proves the refusal
branch is wired. It does not claim the state is reachable**, and the test's own
class docstring says so in those words. `--dry-run` is used deliberately: a
build with the call site deleted then writes nothing while still going red.

    M3, before 70dfa96:  Ran 178 — 0 red
    M3, at the tip:      Ran 178 — FAILED (failures=1)
                         RED test_commit_asks_the_invariant_about_tasks_jsonl

A reviewer who holds that a call site reachable only under a monkeypatch should
not ship has a fair case for deleting those two lines. I kept them because they
are the same function the three registers call, at the one place that can see
both counts, and because `commit()`'s task branch is exactly the code a future
edit would break without noticing.

### Finding 2 — `resolve-intake` does not reduce any count

`cmd_resolve_intake` rewrites the row's `Outcome` cell:

```python
ctx["board"].lines[idx] = render_row(
    [intake.get(k, "") if k != "outcome" else text for k in keys])
```

The row stays on the board and `intake.jsonl`'s record count does not move. So
one of the three names USER-906 put in the invariant never exercises its
permission. Spec verification item 7 says *"`resolve-intake` and `intake-sweep`
reduce the count"* — of those two, only `intake-sweep` does.

**Whose mistake is it? Neither's.** USER-906's list is a *permission* list, not a
prediction: it names the commands that are ALLOWED to remove records. In today's
implementation discharge and removal are two commands — `resolve-intake` marks
the outcome, `intake-sweep` takes discharged rows off the board — so the
permission is simply unused. The command is right as written (the cleared/
discharged row staying visible is a deliberate rule this repository states in
`cmd_risk_clear` and `modes/queue.md`), and the permission is right as granted:
if discharge and sweep were ever merged, the list would already be correct.

**I did not adjust `SHRINK_ALLOWED` to match the finding.** All three names are
still there. `test_resolve_intake_is_not_blocked_and_does_not_in_fact_shrink`
asserts `rc == 0` **and** that the count is unchanged — the test records that
the allowance is unused rather than pretending it fires — and the constant's own
comment in `bin/perry-task` says the same thing at the declaration.

## 7. The two converted tests, and why each had to be

Both asserted the behaviour this row exists to change. Neither was "adjusted to
pass".

**`tests/test_asks_store.py`** — `test_the_ordinary_writer_still_writes_the_section_and_that_is_drift`
→ `test_the_ordinary_writer_reaches_the_store_and_leaves_no_drift`.
Its own docstring names this row as the thing that would convert it:

> **Deliberately not converted (TASK-203).** `perry-task answer` writes the
> board and not the store, exactly as `risk-add` and `perry-task intake` still
> do. Converting one register's writers alone would make an ordinary command
> mint a store as a side effect on a project that never ran the gated import.
> What the store adds today is that the divergence is REPORTED rather than
> silent — which is this assertion.

TASK-203 is the row that converts all three registers at once, which is the
condition that docstring set. The assertion is now the other half of the same
fact — `drifted == 0` — **plus** two the old test did not make: that the record
carries the answer text, and that `answered` is `True`. The drift READING is not
lost: it belongs to a hand edit, and the other four tests in
`TestDriftIsReportedRatherThanAbsorbed` edit `BOARD.md` directly and still make
it.

**`tests/test_intake_store.py`** — `test_a_sweep_moves_n_and_the_store_is_what_says_so`,
name unchanged. It asserted `intake_store_drift.drifted == 3` after a sweep and
then ran the import to fix it. `intake-sweep` now writes the store inside the
same transaction as the board, so the renumbering is recorded as it happens and
there is no window in which the two disagree. The reading the test exists for is
unchanged and still asserted — `before[2] != after[2]`, *"n = 2 is a different
row"* — and two assertions were added: the stored requests are the two survivors
in order, and their `order` values are `[0, 1]`. The drift half belongs to a
hand edit, and `test_a_row_deleted_by_hand_reports_every_row_it_renumbered`
thirty lines up is where it is proved.

## 8. Mutations

**The harness.** `scratchpad/t203r4/mutate.py`, run against the tip `70dfa96`.
Each mutation is anchored **by line number**, the exact old text is asserted to
start at that line before anything is replaced (an anchor miss aborts the whole
run and prints what it found), every `__pycache__` under the repo is cleared
before and after, the harness sleeps past the next whole second because CPython
validates a cached `.pyc` on mtime-in-whole-seconds plus size, and the file is
restored and re-checked by `md5`. Every line below carries `[restored, md5 ok]`
from that check. Anchors were re-derived at the tip and each is asserted
**unique** in the file.

Modules run per mutation: `test_register_store_invariant` (39),
`test_intake_store` (50), `test_asks_store` (42), `test_purge` (47) = **178**,
which is the number in every `Ran` line below. The full suite was not re-run per
mutation; a mutation that reddens a test in a module not listed would not have
been seen.

**Two harness runs before this one are discarded, not reported.** The first was
killed mid-mutation by a foreground timeout and left the tree dirty. The second
had **two instances of my own harness running against the same worktree at
once** — each took the other's mutation as its `original`, so restores wrote
mutants back and red sets included tests that a mutation could not touch. That
is what produced the six "successful write" failures I flagged earlier as
possible load flakes. They were not flakes and they were not load: **they are
M10's red set** — `test_a_row_replaced_by_hand…`,
`test_ask_and_risk_add_reach_their_stores_too`,
`test_intake_on_a_project_with_no_store…`,
`test_intake_sweep_may_shrink_the_intake_store`,
`test_resolve_intake_is_not_blocked…` and
`test_the_lint_prints_a_drift_verdict…`. One harness had M10 applied to the file
while the other ran the tests, and the result was attributed to M1, M2, M3 and
M5 in turn. A control run on the same tree was green throughout, which is what
said the tree was fine and the harness was not.

The harness now refuses to start if another instance has this directory as its
cwd, or if the worktree is dirty. Both refusals fired in practice: the dirty
check caught a tree left mutated by the killed run and printed the anchor it
expected against the `if True:` it found.

Every line below is the harness's own output. `[restored, md5 ok]` is the
harness asserting the file came back byte-identical.

| # | anchor | what it changes | result |
|---|---|---|---|
| **M1** | `bin/perry-task:2215` | `if after >= before or event_name in SHRINK_ALLOWED:` → `if True:` — **the invariant deleted** | 23 failures / **12 named tests**: all four doors, all four reproduction tests, both boundary unit tests, and `test_commit_asks_the_invariant_about_tasks_jsonl` |
| **M2** | `bin/perry-task:2179` | `SHRINK_ALLOWED = frozenset({...})` → `frozenset()` | 21 named tests, **14 of them in `test_purge`** — `perry-task purge` refuses end-to-end. Also `test_intake_sweep_may_shrink_the_intake_store` and the converted `test_a_sweep_moves_n_and_the_store_is_what_says_so` |
| **M3** | `bin/perry-task:2627` | the `tasks.jsonl` call site → `pass` | **1**: `test_commit_asks_the_invariant_about_tasks_jsonl`. Before `70dfa96` this was **0** — § 6 |
| **M4** | `bin/perry-task:2215` | `after >= before` → `after > before` — the boundary off by one | 49 named tests. Every equal-count write refuses; the boundary is load-bearing, and `test_growing_and_holding_steady_are_both_fine` is the unit test that says so |
| **M5** | `bin/perry-task:2317` | the uniqueness clause → `if False:` | **1**: `test_a_repeated_identity_is_no_identity_even_when_no_two_are_adjacent` |
| **M6** | `bin/perry-task:2317` | uniqueness → **consecutive-only** (`any(a == b for a, b in zip(ids, ids[1:]))`) | **1**: the same test. Round 3 measured this exact weakening as **green across all 2815 tests**; the distinction it said could not be made is now made |
| **M7** | `bin/perry-task:2321` | the positional identity check → `if False:` | **1**: `test_a_row_replaced_by_hand_does_not_hand_its_discharge_to_the_newcomer` — the case the invariant cannot see (§ 5) |
| **M8** | `bin/perry-task:2257` | `except json.JSONDecodeError` → `except ZeroDivisionError` — the traceback escapes again | **1**: `test_a_corrupt_line_in_a_register_store_is_a_refusal_not_a_traceback` |
| **M9** | `bin/perry-task:2352` | the shape early-return moved **above** `refuse_to_shrink` — **round 2/3's architecture, rebuilt** | 8 failures / **2 named tests**: `test_door_three_no_section_shape_on_any_register_may_empty_a_present_store` and `…the_foreign_shape_is_refused_on_every_register`. The ORDER is the fix, and it is tested |
| **M10** | `bin/perry-task:2714` | `if register:` → `if False:` — the register store leaves the canonical set | 8 named tests: every "the write reaches its store" test, including **both converted tests** |
| **M11** | `bin/perry-task:2151` | `"add": "intake"` removed from `REGISTER_EVENTS` | 8 named tests: the whole reproduction, doors 1 and 2, and `test_the_two_task_events_that_touch_intake_are_declared` |
| **M12** | `bin/perry-task:7239` | the success line back to the flat `"store + journal"` template | **1**: `test_the_success_line_names_the_register_store_only_when_one_is_written` |

**Twelve mutations, twelve reddened a named test. None was green.** All twelve
printed `[restored, md5 ok]`, and the worktree is clean at `70dfa96` with
`bin/perry-task` matching its committed blob (`a9af2381b6835ce702629ef5ac23c2b8`).

Three of them are worth reading twice:

- **M6** is round 3's own counter-example. It said a guard tripping only on
  *consecutive* equal identities was green across all 2815 tests, so the shipped
  test could not tell uniqueness from adjacency. Here it reddens one named test
  and nothing else.
- **M9** rebuilds **round 2/3's architecture** — the shape gate consulted before
  the invariant, so an unreadable section silently skips the write instead of
  refusing. It reddens both door-3 tests. The ORDER of those two lines is the
  fix, and the order is tested.
- **M3** is the finding in § 6: 0 red before `70dfa96`, 1 red after.

## 9. Baselines — the runner, the tree, and the load

Runner: `bash tests/run`. Tree: the worktree
`…/5b3ba585-…/scratchpad/wt-203-new`. `test_diagnose`'s queue-register test
reconciles against the LIVE board, so a worktree carrying different intake rows
gives a different number; this worktree carries `main`'s at `6c0d041`.

| tree | commit | modules | tests | failures | load avg while measuring |
|---|---|---|---|---|---|
| before | `6c0d041` (`main` at fork) | 98 | 2882 | 3 | ~1 (machine quiet) |
| after | `b09776d` (the invariant) | 99 | 2919 | 3 | 34 |
| **tip** | **`70dfa96`** | **99** | **2921** | **3** | **34–48** |

The tip is the number that describes what ships. The load figure is stated
because a number measured at load 48 with the condition named is usable and the
same number without it is not: seven agent sessions were running concurrently on
this machine, and the suite took 498s against 343s on the quiet run.

The failure **set** is byte-identical in all three:

- `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`
- `test_diagnose` … `test_the_queue_register_reconciles_with_the_queue_on_this_repository`
- `test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`

+1 module and +39 tests are `tests/test_register_store_invariant.py`.
**This change adds no failure.** `main` at `6c0d041` reproduces the `70eae67`
figure the spec quotes (98 / 2882 / 3), so the branch is measured against the
number the spec names.

### One flake, recorded rather than explained away

On the first post-fix full run,
`test_host_support.TestOpenCodeDispatchLimit.test_concurrent_mixed_registers_do_not_exceed_global_cap`
failed `2 != 3`. It did not appear in the before run, did not appear in the
second post-fix full run, and passed 3/3 in isolation. It exercises
`bin/perry-dispatch-limit`, a bash script this change does not touch, under
8-way parallel load on a machine at load average 34. I am recording that it
appeared once; I am not claiming to have diagnosed it.

## 10. What I did NOT do, and what I could not verify

1. **The full suite was not re-run per mutation.** Each mutation ran four
   modules (178 tests). A mutation that reddens something in one of the other 95
   modules would not have been seen.

2. **`python3 -m unittest discover -s tests` was not run on either tree.** The
   spec notes the two runners disagree by 3 on this repository; I measured with
   `bash tests/run` on both trees and did not run the discover form, so that
   figure is neither confirmed nor used here. Spec verification item 5 asks for
   it and I did not produce it.

3. **A localized board was not exercised.** Round 3 verified the register code
   against a `zh` board; I did not. `register_section_shape` delegates to
   `perry_store`'s shape functions through `_ops()`, which is the i18n-aware
   path, and `tests/run` step 4 lints `tests/fixtures/sample-project-zh` clean —
   but no zh board was driven through a refusal.

4. **Crash recovery and the transaction marker were not re-tested this round.**
   The register store joins `replace_canonical_pair`'s canonical set, which
   already stages an arbitrary number of entries and records every pre-image;
   rounds 1 and 3 each exercised `os._exit(9)` at every rename boundary against
   that same code, and this round changed neither the marker nor the staging. I
   did not re-run that harness, so the claim rests on their measurements plus
   the fact that the list this round appends to is the same list.

5. **Concurrency between two Perry writers was not exercised**, and neither was
   the `recover_stale_lock` TOCTOU round 3 named as a possible flake mechanism.

6. **The refusal is now reachable in ordinary use, and that is a cost I did not
   measure.** A project whose board and store have drifted — a hand-tidied
   intake row, a renamed column, a `## Intake` section removed by `/pmo triage`
   — will find the *next* write refused, including writes that have nothing to
   do with that register. That is what option B asks for, and the refusal names
   both recovery directions. I did not measure how often this repository's own
   board is in such a state, and a reviewer may reasonably want that measured
   before merge.

7. **An unrelated `add` on a project with a healthy `## Intake` and no store
   will now MINT `intake.jsonl`.** That is the row's goal (`claims[]` stores
   that exist on disk, 4 of 6 → 6 of 6) and it is also a side effect of a
   command that has nothing to do with intake. It is deliberate and it is the
   behaviour round 1's own comment worried about; I am naming it rather than
   leaving it to be discovered.

8. **`perry-lint`'s census coverage is TASK-209 and is untouched.** What this
   round changes is what the census SAYS on a store that was about to be
   truncated: `intake store: 0 record(s), 0 row(s) drifted` becomes
   `3 record(s), 3 row(s) drifted`, because the records are still there.

9. **`asks.jsonl` is in scope and is written**, per the amendment. The original
   spec's "Out of scope" line is superseded and no follow-up row is proposed,
   because there is nothing left to follow up.

10. **The board and `perry/tasks.jsonl` were not touched.** The PMO owns those.
    `main` advanced to `91e5351` (ADR-010, DESIGN-013) while this round ran;
    `git merge-tree` reports no conflict — this branch touches `bin/perry-task`
    and four test files and nothing else.

## 11. Where this leaves the row

- Spec verification items 1 and 2 hold: after `perry-task intake` on a project
  with no `intake.jsonl`, the store exists and holds the row, `perry-lint`
  prints a drift verdict rather than *"unchecked, not clean"*, and
  `perry-tasks intake-diff` byte-compares clean —
  `TestTheOrdinaryWriteReachesItsStore`.
- Item 3 (mutation) is § 8; item 4 (the risks half) was answered by
  `TASK-203-premeasurement.md` before this round and this round makes both
  `risk-add` and `risk-clear` write their store.
- Item 5 (`discover`) is **not done** — § 10.2.
- The amendment's items 6 and 7 are § 3.
- P003-O1-KR1 moves from 4 of 6 to 6 of 6 **for any project that runs one
  ordinary register command**. It does not move for a project that runs none:
  the store mints on first write, not on install. Nothing here writes to
  `/Users/bytedance/proj/Perry`, so Perry's own count is unchanged until the PMO
  runs a register command on `main`.

## 12. Forward note — ADR-010

`main` locked ADR-010 (*"BOARD.md stops existing; the board is what a command
prints"*) while this round ran. The invariant is on the right side of it: it
protects the STORES, which survive ADR-010, and every one of the four doors is a
way the board could destroy a store. When `BOARD.md` goes, `register_change`'s
derivation-from-the-board goes with it and `refuse_to_shrink` stays — it counts
records, not rows.
