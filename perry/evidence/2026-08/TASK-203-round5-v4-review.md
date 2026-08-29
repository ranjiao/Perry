# TASK-203 — V4 round 5 review

**PASS.**

The bound is real and the fifth door is closed. I reproduced round 4's defect on
this repository's own data at `afb3a48` and watched the same command refuse at
the tip with the store byte-identical, on both `resolve-intake` and
`intake-sweep`. The register still works: the whole intake lifecycle runs green
on an in-sync copy. `MR` — the round-4 reviewer's own mutation — now reddens a
**named behavioural test on a drifted board**, which is the specific finding
round 4 closed on. Every guard I probed dies under its own deletion, including
the three sub-clauses of the fail-closed `count` check. Spec item 5 is closed:
`discover` gives the identical six failures on the tip and on a copy of round
4's tip, so the three `test_risks_store` extras are proven pre-existing.

**I did find a way to destroy canonical records silently — a count-preserving
substitution (§ 3).** I am ruling it **NON-BLOCKING** and recommending it as its
own row. It is not a shrink, the binding amendment is a count rule, and closing
it needs a per-record identity predicate — round 2's door, and exactly the
"fifth predicate" the amendment forbids. But it is a real, reproducible, silent
loss and the next round should not discover it by accident.

Everything below was run on **copies** in
`scratchpad/rjv5-203r5/{tree,tree2,at-afb3a48,state-src,d_*}`. Nothing was
written inside `scratchpad/review-203r5` and no write-side Perry tool touched
`/Users/bytedance/proj/Perry`; the live-board runs used `cp -R`'d state. No
`git checkout`/`stash`/`reset`/`clean` anywhere. Harness and probe files are all
prefixed `rjv5_`.

---

## 0. The tree is clean and matches its commit

The one place a hand restore could have gone wrong (MB6's timeout):

```
$ cd scratchpad/review-203r5
$ git status --porcelain          # empty — no modified, no untracked
$ git log --oneline -1            ab24b45
$ md5 -q bin/perry-task           f282d2395f1eae6c5fa077f3e11f958a
```

Empty status is checked *after* my whole round as well as before. The tip md5
matches the RESULT's claimed shipped md5, and the `git archive` extraction of
`afb3a48` matches its claimed `a9af2381b6835ce702629ef5ac23c2b8`. **Verified.**

---

## 1. The structural question — is it the last door or the sixth predicate?

It is one question about two integers, and I could not make it into a predicate
about anything else.

**No call site can carry the permission without the number.** There are exactly
three occurrences of `refuse_to_shrink` in `bin/`: the definition
(`bin/perry-task:2223`) and two calls (`:2423` in `register_change`, `:2698` in
`commit`). Both pass `event` as a required positional; `declared_removal` is
computed inside. There is no name-taking overload and no default. I also swept
every other writer of the three register stores: `bin/perry-tasks` writes them
only at the six explicit `*-write --from-board` / `*-render --write` sites the
refusal message itself points to, and `bin/perry-lint` only reads. **Verified.**

**The gate counts the number that gets written.** `register_change` gates on
`len(derived)` (derived with `current=None`) and then persists
`records_of(board, ops, current)`. I checked all three derivations
(`perry_store.intake_records`, `risk_records`, `ask_records`): each returns one
record per qualifying board row and `current` is only ever used to *merge
fields*, never to add or drop a record. So `len(records) == len(derived)`
identically, and the gate is not counting a different list than the one written.
This is the shape of a sixth door and it is not open.

**`declared_removal` fails closed on all five shapes**, run directly against
the tip:

```
unnamed command (add)  -> 0     sweep, count MISSING    -> 0
empty event {}         -> 0     sweep, count None       -> 0
no event key           -> 0     sweep, count NEGATIVE   -> 0
event None             -> 0     sweep, count True/False -> 0   ← the bool case
event 42 (non-str)     -> 0     sweep, count '99' (str) -> 0
                                sweep, count 3.0 (float)-> 0
purge -> 1 · resolve-intake -> 0 · sweep, count 3 -> 3
```

`isinstance(True, int)` is True in Python and this does not fall for it.
**Verified.**

**Doors I tried and could not open.** (a) A cross-store allowance: an
`intake-sweep` event reaches `commit`'s *task*-store call with an allowance of
`count`, so it nominally holds a licence of N on `tasks.jsonl`. Unreachable —
`commit`'s non-`purge` branches build `records` from `current` with no removal,
so the task drop is always 0. Latent asymmetry, not a defect. (b) A legitimate
removal wrongly blocked on `risks`/`asks`: I read `cmd_risk_clear`, `cmd_answer`
and `cmd_route` — all three rewrite a cell in place and the row stays, so no
command shrinks those two stores and the "no declaration" position is correct.
(c) An inflated sweep count: `cmd_intake_sweep` sets `count: len(discharged)`
from the board it just mutated, and any hand drift adds to the drop without
adding to the count, so drift always pushes it over its own bound.

---

## 2. The decisive claim — `MR` reddens a behavioural test. VERIFIED.

Harness `scratchpad/rjv5-203r5/rjv5_mut.py` (uniquely named, refuses a
non-unique anchor, asserts the old text before replacing, clears every
`__pycache__`, sleeps past the whole-second boundary on both sides, restores
from an in-memory copy and md5-verifies). Modules:
`test_register_store_invariant test_intake_store test_asks_store
test_risks_store test_purge` — **control 239 tests, OK, 103s**. Every row below
restored to `f282d2395f1eae6c5fa077f3e11f958a`.

| mutation | red |
|---|---|
| **MR** — drop `"resolve-intake"` from `SHRINK_ALLOWANCE` | **3**: `test_resolve_intake_may_not_shrink_a_store_it_removes_nothing_from` (behavioural, drifted board), `test_intake_store.test_a_shrink_permitted_command_on_that_same_board_is_refused` (behavioural, drifted board), and one constant assertion |
| **MB1** — round 4's exact rule restored (`if after >= before or name in SHRINK_ALLOWANCE:`) | 13 failures / **7 named**, incl. all three bounded behavioural tests **and `test_a_shrink_permitted_command_on_that_same_board_is_refused`** |
| **MB6** — `"purge": 1` → `0` | 17 failures + 4 errors / **21 named, 15 of them in `test_purge`** driving the CLI end to end |
| **MB7** — the fail-closed `count` guard → `if False:` | 5 failures / `test_a_declaration_this_tool_cannot_read_declares_nothing` |
| **MB9** — `register_change` passes `{}` instead of `event` | 6 named, all four sweep/resolve behavioural tests |
| **M6** — round 3's consecutive-only weakening of the uniqueness clause | **1 — `test_a_repeated_identity_is_no_identity_even_when_no_two_are_adjacent`. Still red.** |

Under round 4, `MR` reddened two assertions *about a constant*. Under round 5 it
reddens two behavioural tests that drive `perry-task resolve-intake` on a board
where a shrink is possible. **That is the round-4 → round-5 difference and it
holds.** (My MB6 count is 15 in `test_purge` where the RESULT says 16; I
de-duplicate by test name, so a name appearing in two classes collapses. Not
material.)

### The control — weaker than the RESULT claims, but the tests are not vacuous

The RESULT says *"A clean-board version of any of these tests does not merely
pass; it fails its own control."* I tested that directly with a probe
(`rjv5_probe_control.py`, written into the **copy** tree and deleted after):

* **`drifted([1, 2, 3, 4])`** — the helper called with every row kept, i.e. a
  clean board. **All three controls pass.** `drifted()` asserts (1) the store
  minted 4, (2) the board holds `len(keep)` rows, (3) the store still holds 4.
  None of them asserts `len(keep) < 4`, and tidying never touches the store, so
  control 3 is true regardless. The test then goes red on the **behaviour**
  assertion (`0 == 0 : ...`), not on the control.
* **A clean fixture bypassing the helper** (round 4's shape) — also red, also on
  the behaviour assertion.

So the useful half is true: **the test cannot pass on a clean board either way**,
and that is what stops round 4's failure repeating. The structural claim is one
assertion short — `self.assertLess(len(keep), 4, "control: a shrink is
possible")` inside `drifted()` would make the RESULT's sentence true. I am
recording this as a **claim-accuracy finding, not a defect**: no shipped code is
wrong and no test is green for the wrong reason.

### Does any guard survive its own deletion?

I went past the thirteen and killed every guard in the changed surface
individually. All died:

| guard deleted | red |
|---|---|
| `if rule is None: return 0` → `return 99` | 24 failures / **13 named**, all four doors |
| `isinstance(count, bool)` alone | 1 — `test_a_declaration_this_tool_cannot_read_declares_nothing` |
| `count < 0` alone | 1 — same test |
| `not isinstance(count, int)` alone | 1 — same test |
| `if name in SHRINK_ALLOWANCE:` (message selection) → `if False:` | 4 named |
| `if shape != "table": return None` → `if False:` | 1 — `test_the_success_line_names_the_register_store_only_when_one_is_written` |
| `carry_forward_is_addressable`'s per-row identity clause → `if False:` | 1 — `test_a_row_replaced_by_hand_does_not_hand_its_discharge_to_the_newcomer` |

**No guard in this change survives its own deletion.** The three sub-clauses of
the fail-closed check are each independently covered — including the `bool` one,
which was the one most likely to be decoration.

---

## 3. The finding: a count-preserving substitution destroys records silently

**NON-BLOCKING. Not a violation of the binding amendment. File it as its own row.**

The invariant is a count rule, so it says nothing about a derivation that
produces the **same** number of records out of **different** ones. Swap N rows
on the board by hand and any register-touching command persists the swap,
destroying N canonical records at rc 0 with `perry-lint` reporting the result as
clean — **including `resolve-intake`, which declares 0 removals.**

On the live board copied to scratch (32 intake records minted with the gated
`perry-tasks intake-write --from-board`), 10 real `## Intake` rows deleted by
hand and 10 filler rows added:

```
$ python3 bin/perry-lint --root $D          # BEFORE
  · intake store: 32 record(s), 16 row(s) drifted
$ python3 bin/perry-task resolve-intake 1 --outcome dropped --reason x --root $D
perry-task: wrote intake row 1 (resolve-intake) → … + intake.jsonl + …
rc=0
$ python3 bin/perry-lint --root $D          # AFTER
  · intake store: 32 record(s), 0 row(s) drifted

LOST: 10 records    GAINED: 10 records
```

The single-row form is more realistic and needs no filler at all: hand-delete one
`## Intake` row, then file one ordinary `perry-task intake`. `before = after =
32`, drop 0, allowed. One canonical record gone, rc 0, `0 row(s) drifted`. I
reproduced the same thing on `asks.jsonl` on the `zh` fixture: with `USER-014`
hand-deleted from `## 用户输入队列`, one `perry-task ask` replaced its record
with a freshly minted `USER-001` at equal count. (Side note for someone else's
row: the deleted row's id was **reissued**, which the project's own memory says
is not cosmetic.)

**Why I am not failing on it.**

1. The amendment binds and it is explicitly a count rule: *"Any derivation that
   would produce fewer records than the store already holds is a refusal."* 32 →
   32 is not fewer. Round 4's finding *was* a shrink — the exemption was the
   loophole. This is not a shrink at all.
2. Closing it requires comparing record **identity** across the write. That is
   round 2's door, and the amendment's own words are *"One invariant, not a
   fourth predicate."* Failing round 5 on this would be ordering the sixth
   predicate the user declined.
3. **No tool path reaches it.** All five known doors were tool-produced —
   `ensure_section`, a section that stopped parsing, a shape change — and every
   one of those produces a *shrink* and is refused. This needs a human to edit
   `BOARD.md` and swap rows, which in a board-derived-store design is a request
   to change the rows.
4. `perry-lint` reports the drift for the whole window before the write (16
   rows above). The write launders it; the state is not invisible beforehand.

**What I recommend the row say.** An ordinary write may not silently *replace*
canonical records either — a derivation whose record set differs from the stored
set other than at the rows the command addressed should refuse or warn. That is
a real question and it deserves its own spec, not a fifth patch on this one.

---

## 4. Claims verified with my own measurement

**Board state for every number below:** the branch tip's committed `perry/`
(i.e. `main` at `6c0d041` plus this row's evidence files) for the test runs, and
a `cp -R` of `/Users/bytedance/proj/Perry`'s `.perry/` and `perry/` **as of
2026-08-30** for the reproductions. The live board has grown since the author
measured — 32 intake rows where the RESULT recorded 30 — so my absolute
byte/record figures differ from theirs. The signature is identical.

### Claim 1 — both doors closed, side by side. VERIFIED.

Same drifted state built twice: minted at 14328 B / 32 rec / md5
`ffd24b46805d80b6aa3f762520a2c1be`, then 28 of the 32 `## Intake` rows tidied
off `BOARD.md` by hand.

| `resolve-intake 1 --outcome dropped` | round 4 (`afb3a48`, md5 `a9af2381…`) | tip (`ab24b45`, md5 `f282d239…`) |
|---|---|---|
| rc | **0** | **1** |
| store after | **1420 B / 4 rec** (md5 `1065b3f4…`) | 14328 B / 32 rec, **md5 unchanged** |
| `perry-lint` | `0 error(s)` · `intake store: 4 record(s), 0 row(s) drifted` | `0 error(s)` · `intake store: 32 record(s), 28 row(s) drifted` |

**Twenty-eight canonical records destroyed at exit 0 with lint calling it clean,
versus a refusal and an honest drift count.**

| `intake-sweep` (one row discharged first, 26 tidied off) | round 4 | tip |
|---|---|---|
| rc | **0** | **1** |
| line | `wrote 1 row(s) (intake-sweep)` | `refused — … a drop of 27 — but intake-sweep removes 1 record(s)` |
| store after | **1770 B / 5 rec** | 14352 B / 32 rec, **md5 unchanged** |
| `perry-lint` | `intake store: 5 record(s), 0 row(s) drifted` | `intake store: 32 record(s), 26 row(s) drifted` |

It reported sweeping one row and removed twenty-seven.

### Claim 2 — the register still works. VERIFIED, and this is the half I weighted hardest.

On an in-sync live-board copy, tip only:

```
start                                              32 records
resolve-intake 1 --outcome dropped     rc=0   →    32 records
intake-sweep                           rc=0   →    31 records
intake --title 'an ordinary new request' rc=0 →    32 records
perry-lint: 0 error(s), 4 warning(s) · intake store: 32 record(s), 0 row(s) drifted
```

The discharge does not shrink, the sweep shrinks by exactly what it swept, the
new intake grows. This is **not** TASK-095 round 5's mistake. I also confirmed
by reading that `risk-clear`, `answer` and `route` all rewrite a cell in place,
so there is no legitimate removal on `risks`/`asks` for the bound to block.

### Claim 3 — mutations. VERIFIED, six spot-checked (§ 2), including MB6 and M6.

### Claim 4 — the suite gap is closed. VERIFIED.

`test_a_shrink_permitted_command_on_that_same_board_is_refused` shares
`_hand_delete_the_first_intake_row` with the lint-only test, carries its own
control (`"control: the store holds four records"`), asserts rc != 0, the
`removes 0 record(s)` message, and **byte-equality of the store**. It is red
under MB1 — round 4's exact rule — which is the check that matters. The lint-only
test now says in its docstring that it is deliberately lint-only and where the
other question is asked.

### Claim 5 — baselines. VERIFIED, and spec item 5 is genuinely closed.

`bash tests/run` on a copy of the tip, board state as named above:

```
99 modules · 2929 tests · 360.8s · 8 workers · 2 module(s) red
  test_diagnose (2)  test_perry_itself_passes_its_own_id_checks
                     + test_the_queue_register_reconciles_with_the_queue_on_this_repository
  test_kr_progress_provenance (1)  test_no_current_in_the_payload_claims_to_be_a_measurement
```

**99 / 2929 / 3, red set identical to round 4's name for name.** None touches a
register store. Because this is the branch's committed board and not LIVE state,
the two `test_contract_key_parity` witness tests the spec warns about do not
appear — as expected.

`python3 -m unittest discover -s tests`, run to completion on **both** trees:

```
tip copy (cp -R of the git worktree):   Ran 2929 tests …  FAILED (failures=6, skipped=1)
afb3a48  (git archive extraction):      Ran 2921 tests …  FAILED (failures=6, skipped=4)
```

**The identical six, name for name**, on both: the three also red under
`tests/run`, plus `test_risks_store.TestTheReadersAreOneFunction`'s
`test_the_columns_are_one_list`, `…_register_header_predicate_is_one_object`,
`…_bullet_and_placeholder_rules_are_one_object`. The failure text is
`AssertionError: ['ID', 'Risk', 'Opened', 'Status'] is not ['ID', 'Risk',
'Opened', 'Status']` — two equal lists, two identities, the double-import
diagnosis confirmed. `test_risks_store` is **green in isolation** (53 tests, OK).
**The three extras are pre-existing on round 4's tip. Proven, not asserted.**
First time this claim has been closed on this row.

---

## 5. Rulings on the three declared gaps

**Gap 1 — the `purge` over-declaration is not CLI-reachable. RULING: ACCEPTABLE,
does not block.** The round-4 reviewer already ruled the identical shape
acceptable for `test_commit_asks_the_invariant_about_tasks_jsonl`, and the
argument transfers exactly: the *call* is exercised end to end even though this
*branch* is not. My own MB6 (`"purge": 1` → `0`) is the proof — 21 named reds,
15 of them in `test_purge` driving `perry-task purge` through the CLI, which is
not what a never-reached guard looks like (TASK-095's guard reddened nothing).
`test_purge_removes_the_one_record_it_names_and_leaves_the_other` runs 2 → 1
through the CLI, which closes round 4's real hole — a 1 → 0 purge test cannot
tell "removed exactly one" from "removed everything". The test's docstring
states what it does and does not claim. Keep both.

**Gap 2 — the unreconciled `discover` discrepancy. RULING: ACCEPTABLE; nothing
is hidden, but the stated explanation is wrong and should be corrected.** I ran
`discover` myself on **both** tree layouts — a `cp -R` of the git worktree
(the round-4 reviewer's shape) and a `git archive` extraction (the author's) —
and got the author's figures on **both**, with no `ModuleNotFoundError: No
module named 'tests'` and no `test_host_support` flake in either. So the
author's numbers reproduce and are stable across layouts; the round-4 reviewer's
two errors were environmental (a stray `tests` package on `sys.path` — which is
literally row 1 of this repository's own `## Intake`) and the third is a
recorded flake. The author's attribution to "tree layout" is **not supported by
my measurement** and should be struck from the record rather than repeated. It
hides nothing: the failure count is the identical six on both trees and neither
error moves with the bound.

**Gap 3 — the five things not re-tested. RULING: ACCEPTABLE, and I closed one of
them.** I drove a **`zh` board through a bounded refusal** myself
(`tests/fixtures/sample-project-zh`, asks store at 2 records, both
`## 用户输入队列` rows hand-deleted, `perry-task ask`):

```
perry-task: refused — `ask` would take …/asks.jsonl from 2 record(s) to 1, and an
ordinary write may never make a canonical store smaller (USER-906). …
rc=1 ; store unchanged at 2 records
```

The localized heading resolves and the refusal fires. On the rest: crash recovery
at the rename boundaries is a fair skip because the refusal is raised in
`register_change` *before* the plan is built and before anything is staged — I
confirmed the ordering by reading `commit`, so the bound cannot reach
`replace_canonical_pair` at all. Concurrency between two writers and the
full suite per mutation are standard omissions at this scale. Not re-measuring
`main` at `6c0d041` is fine: I measured the tip at 99 / 2929 / 3 and the red set
is name-for-name round 4's, which is what the delta claim needs.

---

## 6. What I did NOT check

1. **Crash recovery at the rename boundaries** — reasoned, not re-run. No
   `os._exit(9)` probe this round.
2. **Concurrency between two Perry writers.** Not exercised.
3. **The full suite per mutation.** Five modules / 239 tests each, as the author
   did.
4. **`main` at `6c0d041` was not re-measured** by me either.
5. **The remaining seven of the thirteen mutations** (MB2, MB3, MB4, MB5, MB10,
   M1, MB1b) were not re-run; I spot-checked six and swept seven guards the
   author did not mutate.
6. **`risks.jsonl` under a bounded refusal** was not driven end to end — I
   verified by reading that no command shrinks it and drove the `asks` case
   instead.
7. **The `test_contract_key_parity` and `test_board_render` data-dependent
   failures** — my board state does not produce them, so I could not
   independently confirm they are the defects the spec says they are.

---

## 7. Disclosure

Invoking `review-203r5/bin/perry-*` was avoided entirely — every run used the
copies — so no `__pycache__` was written into the reviewed worktree. `git status
--porcelain` there is empty at the end of this round, and `bin/perry-task` is
still `f282d2395f1eae6c5fa077f3e11f958a`. The mutation harness
(`rjv5_mut.py`), the clean-board probe (`rjv5_probe_control.py`, deleted after
use from the copy tree) and every scratch directory are uniquely prefixed
`rjv5`.
