# TASK-203 — round 5 RESULT: the exemption is bounded

> Branch `coding/task-203-round4`, continuing from round 4's tip `afb3a48`.
> Written against `perry/evidence/2026-08/TASK-203-spec.md § Amendment
> 2026-08-29 — USER-906, option B`, which binds, and against
> `perry/evidence/2026-08/TASK-203-round4-v4-review.md`, which FAILED round 4.
>
> **This document is the current one for this row.** Round 4's RESULT
> (`TASK-203-round4-result.md`) is accurate about the invariant and the twelve
> mutations and wrong in exactly two places, both named in its own banner: the
> code block in its § 1 and the conclusion of its § 6 finding 2. Everything
> else in it stands and is not repeated here.
>
> Every measurement below was taken in the worktree
> `…/5b3ba585-…/scratchpad/wt-203-new` or in a scratch **copy** of this
> repository's state. No write-side Perry tool was run against
> `/Users/bytedance/proj/Perry`; the live-board reproductions below were run
> against `cp -R`'d copies of its `.perry/` and `perry/`.

## 0. What round 4 got wrong, in one sentence

The invariant was sound — the reviewer could not break `refuse_to_shrink` from
inside, and all four known doors stayed closed. `SHRINK_ALLOWED` was not: it
granted its exemption **by command name and without a bound**, so a listed
command could shrink a canonical store by any amount, **including a shrink it
did not perform**.

## 1. Commits

| commit | what it is |
|---|---|
| `36be5bd` | the three bounded-exemption tests, on boards where a shrink is possible. **Deliberately RED.** |
| `1e42b97` | the bound: an allowed command may shrink by exactly the count it declares removing. |
| `a900585` | a guard in `declared_removal` that nothing could reach, removed. |
| `0cc3889` | the line `tests/test_intake_store.py` stopped one short of: the dangerous state it builds now has a shrink-permitted command run on it. |

## 2. The rule as implemented

`bin/perry-task`, two names and one comparison:

```python
SHRINK_ALLOWANCE: dict[str, int | str] = {
    "purge": 1, "resolve-intake": 0, "intake-sweep": "count",
}

def declared_removal(event: dict) -> int:
    rule = SHRINK_ALLOWANCE.get(event.get("event") or "")
    if rule is None:
        return 0
    if isinstance(rule, int):
        return rule
    count = event.get(rule)
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        return 0
    return count

def refuse_to_shrink(store, path, event: dict, before, after, why="") -> None:
    allowed = declared_removal(event)
    if before - after <= allowed:
        return
    raise Refused(...)
```

**An allowed command may shrink by exactly the count it declares removing.**

| command | declares | why |
|---|---|---|
| `purge` | `1` | it removes the one task it names, and `commit()`'s removal branch is `[r for r in current if r["id"] != removed_id]` |
| `resolve-intake` | `0` | it rewrites one `Outcome` cell. Round 4's own § 6 finding 2 established that it removes no record; the bound is that finding, enforced |
| `intake-sweep` | `"count"` | the rows it swept — `cmd_intake_sweep` already carries `count: len(discharged)` on its event, so nothing new is minted to make the bound readable |

Three properties this has that the frozenset did not:

1. **It is still one question about two integers.** Not "may this command
   shrink" but "is the drop the drop the caller declared". Nothing is asked
   about the board, the section's shape, the identity of a row, or when the
   gate is read. **Option A stays rejected** and stays unnecessary: WHEN you
   look does not change HOW MANY there are, and now neither does WHO is
   looking.
2. **The bound cannot be forgotten at a call site.** `refuse_to_shrink` takes
   the EVENT rather than the event name and computes `declared_removal` itself.
   There is no signature that carries the permission without the number.
3. **It fails closed.** A command nobody named declares 0. A listed command
   whose count is missing, negative, a `bool` or not an `int` declares 0 too —
   an unreadable declaration is a refusal, never a licence. The frozenset
   treated the NAME as the permission, so a sweep whose count went missing
   would still have been allowed to remove everything.

The two call sites are unchanged in number and position:

| store | call site | what it counts |
|---|---|---|
| `tasks.jsonl` | `commit()` — `bin/perry-task:2695` | `len(current)` vs `len(records)` |
| the three registers | `register_change()` — `bin/perry-task:2419` | records on disk vs records derived |

### The refusal now has two messages, because there are two failures

An ordinary write keeps round 4's text. An explicit removal over its own
declaration gets its own, naming both numbers:

```
perry-task: refused — `resolve-intake` would take …/perry/intake.jsonl from 30
record(s) to 4 — a drop of 26 — but `resolve-intake` removes 0 record(s). An
explicit removal may shrink a canonical store by exactly what it removes and no
more (USER-906). Nothing was written.
If the board is right and the store is stale, the explicit board-to-store
direction is `perry-tasks intake-write --from-board`; if the store is right,
`perry-tasks intake-render --write` puts the records back on the board.
```

## 3. The defect, reproduced and closed on this repository's own data

Both reproductions were run **side by side**: the same drifted state built
twice, driven once by round 4's tip (`bin/perry-task` md5
`a9af2381b6835ce702629ef5ac23c2b8`, extracted from `afb3a48` with `git archive`
— no checkout) and once by this branch's tip (md5
`f282d2395f1eae6c5fa077f3e11f958a`). State is `cp -R` of
`/Users/bytedance/proj/Perry`'s `.perry/` and `perry/` as of 2026-08-30, minted
with the gated `perry-tasks intake-write --from-board` at **13041 bytes / 30
records / md5 `61eece8755d571c838d417e5439d63e5`**, then 26 of the 30 `##
Intake` rows tidied off `BOARD.md` by hand — the `/pmo triage` state.

### `resolve-intake` — the V4 review's § 1

| | round 4 (`afb3a48`) | round 5 (`a900585`) |
|---|---|---|
| rc | **0** | **1** |
| line | `wrote intake row 1 (resolve-intake) → …` | `refused — … a drop of 26 — but resolve-intake removes 0 record(s)` |
| store after | **1431 bytes / 4 records** | 13041 bytes / 30 records, **md5 unchanged** |
| `perry-lint` | `0 error(s)` · `intake store: 4 record(s), 0 row(s) drifted` | `0 error(s)` · `intake store: 30 record(s), 26 row(s) drifted` |

**26 canonical records destroyed at exit code 0 with lint reporting the wreck as
clean, versus a refusal and an honest drift count.** The left column is the
signature of `TASK-203-merge-hold.md`.

### `intake-sweep` — same board, one row discharged by hand first

| | round 4 | round 5 |
|---|---|---|
| rc | **0** | **1** |
| line | `wrote 1 row(s) (intake-sweep)` | `refused — … a drop of 27 — but intake-sweep removes 1 record(s)` |
| store after | **1121 bytes / 3 records** | 13041 bytes / 30 records, **md5 unchanged** |
| `perry-lint` | `intake store: 3 record(s), 0 row(s) drifted` | `intake store: 30 record(s), 27 row(s) drifted` |

It reported sweeping one row and removed twenty-seven records.

### The register still works — the whole intake lifecycle, on an in-sync copy

A bound that also blocks the sweep has broken the register. On a live-board copy
with the board and store in sync, driven only by this branch's tip:

```
start                                             30 records
resolve-intake 1 --outcome dropped     rc=0    →  30 records
intake-sweep                           rc=0    →  29 records
intake --title 'an ordinary new request' rc=0  →  30 records
perry-lint:  0 error(s), 4 warning(s) · intake store: 30 record(s), 0 row(s) drifted
```

## 4. The tests, and why they are not round 4's tests

**Round 4's test for this allowance ran on a clean board.**
`test_resolve_intake_is_not_blocked_and_does_not_in_fact_shrink` builds
`self.fixture(build_board())`, where no shrink is possible, and asserts
`rc == 0` and `len(records) == 4` — both true with the allowance and both true
without it. The reviewer's mutation `MR` (drop only `"resolve-intake"` from the
allowlist) reddened two tests, **both assertions about the constant**. The one
test offered as the record that "the allowance is unused" is the one test that
cannot tell. That test is kept, because it does say something — the invariant
does not block the ordinary discharge — and its docstring now says exactly what
it does and does not claim.

`TestTheExemptionIsBounded` is the new class. **Every test in it runs on a board
where a shrink IS possible, and asserts that as a control first**, through a
shared `drifted()` helper that raises before any behaviour is asserted:

```python
self.assertEqual(len(f.records("intake.jsonl")), 4, "control: minted whole")
tidy_intake_rows_off_the_board(f, keep)
self.assertEqual(len(board.section_rows("Intake")), len(keep), "control: tidied")
self.assertEqual(len(f.records("intake.jsonl")), 4,
                 "control: the STORE still holds every record, so a derivation "
                 "from this board shrinks it — a shrink is possible here")
```

A clean-board version of any of these tests does not merely pass; it **fails its
own control**. That is the structural answer to "a check that cannot fail on the
thing it names".

| command | the named behavioural test | the board it runs on |
|---|---|---|
| `resolve-intake` | `test_resolve_intake_may_not_shrink_a_store_it_removes_nothing_from` | store 4 records, board 2 rows — 2 records at stake |
| `intake-sweep` | `test_intake_sweep_may_not_shrink_by_more_than_the_rows_it_swept` | store 4, board 2 (one discharged) — it sweeps 1 and 3 were about to go |
| `intake-sweep` | `test_intake_sweep_may_shrink_by_exactly_the_rows_it_swept` | in-sync board with **two** discharged rows — 4 → 2, so a bound written as the literal `1` is red |
| `purge` | `test_purge_removes_the_one_record_it_names_and_leaves_the_other` | a two-record store — round 4's purge test ran 1 → 0, where "removed exactly one" and "removed everything" are the same number |
| `purge` | `test_purge_may_not_take_two_records_with_one_removal` | a store carrying the subject's id twice |

### The line the suite stopped one short of

Separately from the class above, and the more useful of the two findings the
round-4 review left on method rather than on code:
`tests/test_intake_store.py § test_a_row_deleted_by_hand_reports_every_row_it_
renumbered` **builds the exact dangerous state** — a hand-deleted `## Intake`
row against a minted 4-record store, with a docstring that says outright that
`resolve-intake 2` now addresses what `resolve-intake 3` addressed yesterday —
and then runs only `perry-lint`. **Nothing in the whole suite then ran a
shrink-permitted command on that board.** One more step is the entire defect.

`0cc3889` extracts the board-building so both tests run on the same state, says
in the lint-only test's docstring that it is deliberately lint-only and where
the other question is asked, and adds
`test_a_shrink_permitted_command_on_that_same_board_is_refused` to ask it.
Mutation **MB1b** below confirms it is red under round 4's exact rule.

**A test that constructs the dangerous state and then asserts something safe
about it reads as coverage and is not.** That is the general lesson this round
takes, and it is why `TestTheExemptionIsBounded.drifted()` asserts the danger
before it asserts the behaviour.

The last one is the one honest asterisk on this table and it is declared rather
than smoothed over. `commit()`'s removal branch drops **every** record matching
`removed_id`, so a duplicated id is a drop of 2 against a declaration of 1 — but
`load_task_records` refuses a duplicate id before `commit()` ever sees one, so
the state is constructed by replacing the loader for the duration of one
`commit()` call, exactly as `test_commit_asks_the_invariant_about_tasks_jsonl`
does. **It proves the declaration is what bounds the write; it does not claim
the duplicate is reachable through the CLI.** The test's docstring says so. The
reachable half of the purge bound is the row above it, and mutation MB6 below
shows sixteen `test_purge` tests standing behind it end to end.

Unit tests of `refuse_to_shrink` and `declared_removal` are kept in
`TestTheInvariantItself`, and its docstring now says in its first line that
assertions of that kind do not count on their own and why.

## 5. Mutations

Harness `scratchpad/r5b_mutate.py` — **uniquely named**, refuses to start on a
dirty tree, refuses to start if another `r5b` lock exists in the worktree,
anchors by line number, **asserts the old text is present before replacing it**,
clears every `__pycache__` under `bin/` and `tests/` and sleeps past the whole
second boundary on both sides, restores from an in-memory copy and compares
`md5`. Every row below restored to md5 `36dc10b06465e7fd30573e61079cb264`
(the file at `1e42b97`; the tip is `f282d2395f1eae6c5fa077f3e11f958a` after
`a900585`, which is a comment-and-dead-guard change re-verified separately).

Modules per mutation: `test_register_store_invariant`, `test_intake_store`,
`test_asks_store`, `test_risks_store`, `test_purge` — **238 tests, control
green** (239 from `0cc3889` onward).

**MB1, MR and MB7 were each re-run at the shipped tip** (`f282d2395f1eae6c5fa07
7f3e11f958a`, after `a900585` shifted the anchors by four lines) and reddened
the same named tests, so the mutation evidence is about the file that ships and
not only about the file at `1e42b97`.

| mutation | anchor | change | red |
|---|---|---|---|
| **MB1** | `bin/perry-task:2269` | `if before - after <= allowed:` → `if after >= before or name in SHRINK_ALLOWANCE:` — **round 4's exact rule restored** | 12 failures / **6 named**, including all three new behavioural tests: `test_resolve_intake_may_not_shrink_a_store_it_removes_nothing_from`, `test_intake_sweep_may_not_shrink_by_more_than_the_rows_it_swept`, `test_purge_may_not_take_two_records_with_one_removal` |
| **MB2** | `:2193` | `"resolve-intake": 0` → `99` | 3 / **`test_resolve_intake_may_not_shrink_a_store_it_removes_nothing_from`** + 2 unit |
| **MB3** | `:2193` | `"intake-sweep": "count"` → `1` (a literal instead of the declared count) | 8 + 1 error / **`test_intake_sweep_may_shrink_by_exactly_the_rows_it_swept`**, `test_a_sweep_moves_n_and_the_store_is_what_says_so` + 3 unit |
| **MB4** | `:2193` | `"intake-sweep": "count"` → `99` | 8 / **`test_intake_sweep_may_not_shrink_by_more_than_the_rows_it_swept`** + 3 unit |
| **MB5** | `:2193` | `"purge": 1` → `99` | 4 / **`test_purge_may_not_take_two_records_with_one_removal`** + 3 unit |
| **MB6** | `:2193` | `"purge": 1` → `0` | 17 failures + 4 errors / **21 named, 16 of them in `test_purge`** — `perry-task purge` refuses end to end — plus `test_purge_removes_the_one_record_it_names_and_leaves_the_other` and `test_purge_may_shrink_the_task_store` |
| **MB7** | `:2214` | the fail-closed guard on `count` → `if False:` | 5 / **`test_a_declaration_this_tool_cannot_read_declares_nothing`** |
| **MB9** | `:2419` | `register_change`'s call site passes `{}` instead of `event` | 5 / **`test_intake_sweep_may_shrink_the_intake_store`**, `test_intake_sweep_may_shrink_by_exactly_the_rows_it_swept`, `test_intake_sweep_may_not_shrink_by_more_than_the_rows_it_swept`, `test_resolve_intake_may_not_shrink_a_store_it_removes_nothing_from`, `test_a_sweep_moves_n_and_the_store_is_what_says_so` — the event reaches the gate |
| **MB10** | `:2695` | `commit()`'s call site passes `{}` instead of `event` | 16 failures + 2 errors / **18 named, 16 in `test_purge`** |
| **MR** | `:2193` | the reviewer's own: drop `"resolve-intake"` from the map entirely | **2 — and one of them is now `test_resolve_intake_may_not_shrink_a_store_it_removes_nothing_from`, a named behavioural test on a drifted board.** Under round 4 this mutation reddened only two assertions about the constant. This is the specific finding the round-4 review closed on |
| **M1** | `:2269` | the invariant deleted — `if True:` | 34 failures / **17 named**: all four doors, all four reproduction tests, the three new bounded tests, `test_commit_asks_the_invariant_about_tasks_jsonl` |
| **M6** | `:2384` | round 3's exact consecutive-only weakening of the uniqueness clause | **1 — `test_a_repeated_identity_is_no_identity_even_when_no_two_are_adjacent`.** Green across 2815 tests in round 3; still red here, so round 5's change did not re-open it |
| **MB1b** | `:2273` | MB1 again, after `0cc3889`, against **239** tests | 13 / **7 named** — MB1's six plus **`test_a_shrink_permitted_command_on_that_same_board_is_refused`**, the line the suite had been stopping short of |

MB6 was interrupted once by a two-minute command timeout, leaving the mutation
in the tree. It was restored by hand from the recorded old text and md5-verified
back to `36dc10b06465e7fd30573e61079cb264` **before** it was re-run to
completion; `git status --porcelain` was empty at that point. No `git checkout`,
`stash`, `reset` or `clean` was run at any time in this round.

There is no MB8: the mutation it would have been — deleting
`not isinstance(rule, bool)` from `declared_removal` — reddens nothing, because
`rule` is a literal in this file and nothing can reach that branch. The honest
answer to a guard that survives its own deletion is to delete it, which is what
`a900585` does; the guard that matters is the one on `count`, which arrives on
the event and has MB7 behind it.

## 6. Baselines — the runner, the tree, the board state, and the load

**Runner:** `bash tests/run`, 8 workers.
**Tree:** this worktree at `0cc3889`.
**Board state:** `perry/` is `main` at `6c0d041` plus this row's round-4 and
round-5 evidence files — i.e. the same board state round 4's numbers were taken
on, which is why the two `test_contract_key_parity` witness tests the spec warns
about (data-dependent on `conformance.in_progress_with_no_live_run` being
non-empty on the LIVE board) do not appear in the red set here.
**Load:** load average 8–15, from three other concurrent agent sessions.

```
99 modules · 2929 tests · 194.1s · 8 workers · 2 module(s) red
  test_diagnose               (2)  test_perry_itself_passes_its_own_id_checks
                                   + the queue-register reconciliation
  test_kr_progress_provenance (1)  test_no_current_in_the_payload_claims_to_be_
                                   a_measurement
```

**Round 4's tip was 99 modules / 2921 tests / 3 failures on this runner and this
board state. This round adds 8 tests and no failures: 2921 + 8 = 2929, and the
red set is identical, name for name.** None of the three is mine and none of
them touches a register store. An earlier run at `0e6afd0`, before the eighth
test landed, read 99 / 2928 / 3 with the same red set.

### Spec item 5 — `python3 -m unittest discover -s tests`

Run to completion this round, from the repository root, single-process, on this
worktree at `0e6afd0` — one test before the tip, so 2928 rather than 2929:

```
Ran 2928 tests in 629.683s
FAILED (failures=6, skipped=1)
```

The six, named:

| failure | also red under `tests/run`? |
|---|---|
| `test_diagnose.test_perry_itself_passes_its_own_id_checks` | yes |
| `test_diagnose.test_the_queue_register_reconciles_with_the_queue_on_this_repository` | yes |
| `test_kr_progress_provenance.test_no_current_in_the_payload_claims_to_be_a_measurement` | yes |
| `test_risks_store.TestTheReadersAreOneFunction.test_the_columns_are_one_list` | **no** |
| `test_risks_store.TestTheReadersAreOneFunction.test_the_register_header_predicate_is_one_object` | **no** |
| `test_risks_store.TestTheReadersAreOneFunction.test_the_bullet_and_placeholder_rules_are_one_object` | **no** |

**The three-failure disagreement the spec names is these three, and they are
runner artifacts on their face.** All three are `assertIs` identity assertions —
`PT.RISK_COLUMNS is P.RISK_COLUMNS`, `PT.is_risk_header is
P.is_risk_register_header` — and under a single-process `discover` the `parsers`
module is imported twice under two identities (once through `bin/perry-task`'s
own `sys.path` insertion of `bin/lib`, once directly by the test module), so two
equal lists are not the same object: `['ID', 'Risk', 'Opened', 'Status'] is not
['ID', 'Risk', 'Opened', 'Status']`.

Measured, not assumed: `test_risks_store` is **green under both runners in
isolation, on this tree and on a `git archive` copy of round 4's tip `afb3a48`**
(53 tests, OK, four ways). It is the whole-tree single-process run that
reddens them.

<!-- DISCOVER-BASELINE -->

## 7. What I did NOT do, and what I could not verify

1. **The `tasks.jsonl` call site keeps its two lines and its monkeypatched
   test.** The V4 round-4 review RULED on this — "KEEP the two lines", not
   TASK-095's shape, does not block — and `test_purge_may_not_take_two_records
   _with_one_removal` is a second test of the same constructed shape, added for
   the same reason and declared the same way in § 4.
2. **Refusal frequency on real boards.** RULED measured and non-blocking by the
   round-4 review. Re-measured incidentally here: `main`'s `## Intake` now mints
   30 records against a board with 30 rows and **no discharged row at all**, so
   `intake-sweep` on the live board refuses for its own reason ("no discharged
   intake rows to sweep") before the invariant is reached, and the ordinary
   register writes come back rc 0 on an in-sync copy (§ 3).
3. **The full suite was not re-run per mutation.** Five modules / 238 tests per
   mutation, as in round 4, for the same reason.
4. **Crash recovery at the rename boundaries was not re-tested** in this round.
   The bound is evaluated strictly before anything is staged, so it does not
   reach `replace_canonical_pair`, but I did not re-run round 4's `os._exit(9)`
   probes.
5. **A localized (`zh`) board was not driven through a bounded refusal.**
6. **Concurrency between two Perry writers was not exercised.**
7. **`asks.jsonl` and `risks.jsonl` remain unexposed to this defect by
   construction** — no command declares a removal on either store, so no command
   may shrink them at all. That is unchanged from round 4 and was not re-probed
   beyond the shape matrix and the suite.
8. **I did not re-measure `main` at `6c0d041`** (98 / 2882 / 3 under
   `git archive`). My numbers are the branch tip only, on the board state named
   in § 6.
