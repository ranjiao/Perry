# TASK-203 — V4 round 4 review

**FAIL.**

The invariant is real, the twelve mutations are real, and the four known doors
are genuinely closed. There is a **fifth door**, and it is the same defect the
row has failed three rounds for: an ordinary-looking command silently truncates
a canonical register store at exit code 0, with `perry-lint` reporting the wreck
as `0 row(s) drifted`.

The door is `SHRINK_ALLOWED`. The exemption is granted **per command name and
without a bound** — a command on the list may shrink a store by any amount, for
any reason, including a shrink it did not perform. `resolve-intake`, which the
author's own § 6 finding 2 establishes *removes no record at all*, therefore
carries an unbounded licence to destroy the whole store. The author's conclusion
that the permission "is simply unused" is false: it is unused only on a board
that has not drifted, and the drifted board is the entire subject of this row.

---

## 1. The defect, on this repository's own data

Reproduced against `/Users/bytedance/proj/Perry`'s state **copied to a scratch
directory** — nothing was written to the repository. Tip code
(`afb3a48`, `bin/perry-task` md5 `a9af2381b6835ce702629ef5ac23c2b8`).

```
$ cp -R /Users/bytedance/proj/Perry/.perry  $D/
$ cp -R /Users/bytedance/proj/Perry/perry   $D/
$ python3 bin/perry-tasks intake-write --from-board --root $D     # the gated first mint
perry-tasks: wrote …/perry/intake.jsonl (28 intake record(s))
  11781 bytes / 28 records / md5 04570df7315eecbe4c83d5a7694e7342

# 24 of the 28 `## Intake` rows tidied off BOARD.md by hand — the state
# `/pmo triage` produces and the state TASK-203-merge-hold.md documents.

$ python3 bin/perry-task intake --title 'a request' --root $D          # ORDINARY write
perry-task: refused — `intake` would take …/intake.jsonl from 28 record(s) to 5,
and an ordinary write may never make a canonical store smaller (USER-906).
Nothing was written.
rc=1 ; store unchanged at 28 records                          ← the invariant works

$ python3 bin/perry-task resolve-intake 1 --outcome dropped --reason x --root $D
perry-task: wrote intake row 1 (resolve-intake) → tasks.jsonl + intake.jsonl
                                                  + journal + BOARD.md + event
rc=0
  after: 1420 bytes / 4 records / md5 1065b3f4ab5a36aa409ee1725e9a45d0

$ python3 bin/perry-lint --root $D
  0 error(s), 4 warning(s)
  · intake store: 4 record(s), 0 row(s) drifted
```

**11781 bytes / 28 records → 1420 bytes / 4 records. Twenty-four canonical
records destroyed, exit code 0, `perry-lint` clean.** Compare
`TASK-203-merge-hold.md`: *8240 bytes / 24 records → 0, exit code 0,
`0 error(s)`, `intake store: 0 record(s), 0 row(s) drifted`.* Same signature,
same store, same repository, one command over.

The same hole on `intake-sweep`, which shrinks **more than it swept** — again on
this repository's own intake data, copied to scratch (the live board had grown
to 31 intake rows by the time I ran this):

```
minted from BOARD.md                                31 records / 13643 bytes
perry-task resolve-intake 2 …                       31 records   (legitimate discharge)
# 25 rows hand-tidied off `## Intake`; 6 remain, one of them the discharged row
perry-task intake-sweep    rc=0  "wrote 1 row(s) (intake-sweep) → … intake.jsonl …"
                                                     5 records / 1770 bytes
perry-lint:  0 error(s) · intake store: 5 record(s), 0 row(s) drifted
```

It reports sweeping **one** row and removes **twenty-six** records. `purge` on
`tasks.jsonl` is not exposed the same way, because `commit()` builds `records`
from `current` and can shorten it by at most one.

### Why this is a defect and not the spec working as written

The amendment says *"Only an explicit removal command — `purge`,
`resolve-intake`, `intake-sweep` — may reduce a record count."* Read as a bare
membership test, the implementation obeys it. But the sentence the amendment is
enforcing is the one above it — *"An ordinary write may never SHRINK a canonical
store"* — and the shrink above is not the removal `resolve-intake` was permitted
for. `resolve-intake` removes nothing. Every record it destroyed here is a
record the command never touched, on rows it never addressed.

The list is a permission to remove **what the command removes**, not a permission
to persist whatever the board happens to derive to. The fix is still a count, not
a fifth predicate and not option A: an allowed command may shrink by exactly the
number of records it removed (`resolve-intake` 0, `intake-sweep` the rows it
swept, `purge` 1) and `refuse_to_shrink` refuses the rest. That stays inside
option B — it asks nothing about the command, the identity or the board, only
whether the drop in the count is the drop the caller declared.

### The suite cannot see it, and I measured that too

My own mutation (`MR`, `bin/perry-task:2179`): remove **only** `"resolve-intake"`
from `SHRINK_ALLOWED`, leaving `purge` and `intake-sweep`. Across the four
modules the author mutated (178 tests):

```
RED(2): test_each_of_the_three_named_commands_may_shrink
        test_the_allowlist_is_exactly_the_three_commands_user_906_named
        [restored, md5 ok]
```

Both are assertions about the constant — one is a direct unit call on
`refuse_to_shrink("intake", …, "resolve-intake", 3, 0)`, the other compares the
frozenset to a literal. **No behavioural test depends on `resolve-intake` being
allowed to shrink**, because the one behavioural test,
`test_resolve_intake_is_not_blocked_and_does_not_in_fact_shrink`, runs on a
**clean** board (`self.fixture(build_board())`) where no shrink is possible. It
asserts `rc == 0` and `len(records) == 4` — which is true whether the allowance
exists or not. The test the author offers as the record that "the allowance is
unused" is precisely the test that cannot tell.

The suite gets one line away from the defect and stops.
`tests/test_intake_store.py § test_a_row_deleted_by_hand_reports_every_row_it_renumbered`
builds the exact precondition — a `## Intake` row deleted by hand against a
minted 4-record store — and then runs only `perry-lint`. Its own docstring says
*"deleting the first row really does mean `resolve-intake 2` now addresses what
`resolve-intake 3` addressed yesterday"*. Nothing in the suite then runs
`resolve-intake` on that board.

---

## 2. Rulings on the three declared gaps

**Gap 1 — the `tasks.jsonl` call site proves wiring, not reachability. RULING:
KEEP the two lines.** The author's own framing is right and the mutation numbers
back it (M2 reddens 14 `test_purge` tests through the CLI, so the site is
reached; M3 reddens exactly one test, and only since `70dfa96`). A monkeypatch-
only *refusal branch* on a guard whose *call* is exercised end-to-end is not the
TASK-095 shape — TASK-095's guard was never reached at all. The state is
unreachable today only because `load_task_records` refuses a duplicate id first;
that is a second guard, not an argument for deleting the first, and `commit()`'s
task branch is exactly the code a future edit breaks silently. The test's own
docstring says what it does and does not claim, which is the honest form. This
does not block.

**Gap 2 — `resolve-intake` holds a permission it never exercises. RULING: this
is the blocking defect.** It is not latent and the permission is not unused: § 1
above uses it to destroy 24 canonical records on this repository's own intake
data. The author reasoned about the allowance on a clean board, wrote a test on
a clean board, and did not try it on the drifted board that is this row's whole
subject. An unbounded name-keyed exemption inside a security-shaped invariant is
a hole, and here it is a reachable one on the single most routine triage command
in the register.

**Gap 3 — nobody measured how often a real board sits in the drifted state that
now refuses the next write. RULING: measured, and it does NOT block.** On
`/Users/bytedance/proj/Perry` as of 2026-08-30 (state copied to scratch):
`risks.jsonl` is 4 records at **0 drift**; `intake.jsonl` and `asks.jsonl` **do
not exist**, so the first ordinary write mints rather than refuses. All three
ordinary register writes come back clean on the live board copy:

```
risk-add --dry-run   rc=0  "would write RX-005 (risk-add) → … risks.jsonl …"
intake   --dry-run   rc=0  "would write the row (intake) → … intake.jsonl …"
ask      --dry-run   rc=0  "would write USER-910 (ask)  → … asks.jsonl …"
```

I also confirmed the refusal cannot arm itself: an ordinary command re-renders
the board without dropping register rows (`add`, `risk-add`, `ask` each left
`## Intake` at 4 rows / 4 records). The drifted state needs a hand edit, a
triage pass or a merge — which is real, and documented, but is not the ambient
condition of an ordinary board. This is not TASK-095 round 5's mistake. It would
have been worth stating in the RESULT; it is not a reason to hold the row.

---

## 3. What I verified, and the numbers

Everything below was run on **copies** of the reviewed worktree
(`scratchpad/rjv4-203r4/{tree,mut,at-762bee1,at-b09776d,liveboard,repro}`),
never in `scratchpad/review-203r4` and never against
`/Users/bytedance/proj/Perry`. No `git checkout`/`stash`/`reset`/`clean` was run
anywhere. No write-side Perry tool touched the repository; the only write-side
runs were against copied state in `$TMPDIR`.

*Disclosure*: invoking `review-203r4/bin/perry-task` against those copies caused
CPython to write `review-203r4/bin/__pycache__/*.pyc`. No source file in the
reviewed tree was modified — `git status --porcelain` in `review-203r4` is empty
— and I left the caches in place rather than deleting files under another
agent's running suite.

### Claim 1 — the merge-hold reproduction is refused now. **VERIFIED.**
Queue-mode track, `## Intake` deleted from the board, store at 4 records:

```
add --track ops   rc=1  refused — `add` would take …/intake.jsonl from 4
                  record(s) to 0 …    store unchanged, 744 B, md5 unchanged
perry-lint:       1 error(s), 6 warning(s) · intake store: 4 record(s), 4 row(s) drifted
```

The store survives and lint reports the drift instead of blessing the wreck.
Same scenario on the live-board copy: refused at 28 records.

### Claim 2 — step 1 deliberately RED, step 2 green. **VERIFIED, and red for the right reason.**
Built by extracting `762bee1` / `b09776d` with `git show` into plain directory
copies (no checkout):

```
at-762bee1/tests $ python3 -m unittest test_register_store_invariant
Ran 37 tests — FAILED (failures=24, errors=7)
at-b09776d/tests $ python3 -m unittest test_register_store_invariant
Ran 37 tests — OK
```

The red set is the doors, not an unrelated breakage — 12 door-3 cells, 4
door-3-foreign cells, 3 door-4, door 1, door 2, the reproduction, and 7 errors
that are `refuse_to_shrink` not existing yet. The merge-hold test itself is red:
`test_an_ordinary_add_on_a_queue_track_cannot_empty_a_present_intake_store`, and
its failure message is the write succeeding
(`wrote TASK-001 (add) → tasks.jsonl + intake.jsonl …`) rather than refusing.

### Claim 3 — twelve mutations. **SPOT-CHECKED SIX, all red, all md5-restored.**
My own harness (`scratchpad/rjv4-203r4/rjv4_mutate.py`, uniquely named per the
brief), anchored by line, old text asserted before replacement, `__pycache__`
cleared and a >1 s sleep on both sides, file restored and md5-compared. Four
modules per mutation = 178 tests, control green.

| mutation | red |
|---|---|
| M1 `if True:` (invariant deleted) | 23 red / **12 named** — all four doors, all four reproduction tests, both boundary units, `test_commit_asks_the_invariant_about_tasks_jsonl` |
| M3 `tasks.jsonl` call site → `pass` | **1** — `test_commit_asks_the_invariant_about_tasks_jsonl` |
| M5 uniqueness → `if False:` | **1** — `test_a_repeated_identity_is_no_identity_even_when_no_two_are_adjacent` |
| **M6 uniqueness → consecutive-only** | **1** — the same test. **Round 3's exact weakening, measured GREEN across 2815 tests then, is RED now.** Closed. |
| M9 (my variant: shape early-return hoisted above the invariant) | 12 red / **8 named**, including both door-3 tests and doors 1, 2, 4. The ORDER is tested. |
| MR (mine) — drop only `"resolve-intake"` from `SHRINK_ALLOWED` | **2, both assertions about the constant** — see § 1 |

M1, M3, M5, M6 reproduce the author's counts exactly. My M9 is a variant of his
(I kept a refusal inside the non-table branch; he removed it entirely), so it
reddens more, not fewer.

### Claim 4 — the four round-3 findings. **ALL FOUR FIXED.**
1. **Vacuous foreign shape.** `test_door_three_the_foreign_shape_is_refused_on_every_register`
   loops 3 registers × 2 foreign variants = 6 cells, and inside each cell asserts
   the control `shape_of(board, ops)[0] == "foreign"` **before** asserting
   `rc != 0` and `f.raw(store) == before`. `TestTheFixturesAreTheShapeUnderTest`
   independently asserts all 15 fixtures are the shape they claim, and
   `test_the_foreign_legend_lands_inside_the_named_section` asserts the legend
   text is inside the named section's body — the precise round-3 defect, as a
   fact about text. Real on each of the three registers.
2. **Uniqueness vs adjacency.** Closed — M6, above.
3. **`JSONDecodeError` escaping.** Probed live: corrupt line 3 of `intake.jsonl`,
   then `perry-task intake` → `rc=1`, no `Traceback` in the output,
   `perry-task: refused — …/intake.jsonl line 3 cannot be read as JSON
   (Expecting value). … nothing was written.`
4. **Dead `section` parameter.** Gone; the function is
   `register_section_shape(board, key)`, both arguments read, heading looked up
   from `REGISTER_SPEC`.

### Claim 5 — baselines. **PARTLY VERIFIED.**
Runner `bash tests/run`. Tree: my copy of the reviewed worktree at `afb3a48`,
whose `perry/` state is `main` at `6c0d041` — **that is the board state my
numbers were taken on**, which is why the `test_contract_key_parity` witness
tests the brief warns about do not appear here.

```
99 modules · 2921 tests · 446.8s · 8 workers · 2 module(s) red · 3 failures
  test_diagnose  (2)  — test_perry_itself_passes_its_own_id_checks  (dangling
                        ACTION-7, ADR-010, D009-1, D010-2, …) and the queue-
                        register reconciliation
  test_kr_progress_provenance (1) — test_no_current_in_the_payload…
```

Exactly the author's tip figure (99 / 2921 / 3) and exactly his failure set.
Machine was loaded throughout (three other agents' suites running concurrently).
I did **not** re-measure `6c0d041` at 98 / 2882 / 3.

### Spec item 5 — `python3 -m unittest discover -s tests`. **RUN, on BOTH trees. Clean.**
The author did not produce this figure. I ran it serially on the tip copy and on
a reconstructed `6c0d041` fork-point tree (new module removed, `bin/perry-task`
and the two converted test files reverted via `git show`, no checkout):

| tree | tests | red |
|---|---|---|
| `6c0d041` (fork point) | 2875 | 8 |
| tip `afb3a48` | 2914 | 9 |

`+39` tests is exactly `tests/test_register_store_invariant.py`. The tip's red
set is the fork point's **eight, unchanged**, plus one:
`test_host_support.TestOpenCodeDispatchLimit.test_concurrent_registers_do_not_exceed_opencode_cap`
— the load-sensitive `perry-dispatch-limit` bash flake the author already
recorded in his § 9, on a script this branch does not touch, and the machine
was carrying three other agents' suites while I measured.

**This change adds no failure under either runner.** The six failures that
separate `discover` from `bash tests/run` are pre-existing runner artifacts,
now proven so on the fork point rather than assumed:

- `test_store_is_canonical` and `test_task_summary` — `ModuleNotFoundError: No
  module named 'tests'` from `from tests.X import …`, which is literally row 1
  of this repository's own `## Intake` (filed 2026-08-21);
- three `assertIs` identity failures in
  `test_risks_store.TestTheReadersAreOneFunction` — `parsers` loaded twice under
  two module identities, so `PT.is_risk_header is P.is_risk_register_header`
  fails while the objects compare equal. I separately confirmed the branch's new
  module does not cause these: `test_register_store_invariant` +
  `test_risks_store.TestTheReadersAreOneFunction` run together is green, as is
  the pre-existing `test_md_store` + the same class;
- the `test_host_support` flake above.

Spec item 5 is satisfied and it is clean.

### Guards that survive their own deletion
Beyond the twelve the author mutated, the one I found is `MR` above: the
`"resolve-intake"` entry of `SHRINK_ALLOWED` has no behavioural test. That is
not merely an untested guard — it is the defect.

### New tests green for the wrong reason
Checked all the known modes and found none:
- boards parsing zero rows — `TestTheFixturesAreTheShapeUnderTest` asserts
  4/4/3 records on the built board and on the minted stores before anything else
  is claimed;
- `"tasks.jsonl"` / `"asks.jsonl"` substring — the store names are looked up
  from the `REGISTERS` table by exact filename, never matched as substrings of
  output;
- the conformance gate refusing first — fixtures write `GATE_OFF` (advisory);
  I confirmed the gate's message appears as a *warning* on runs that succeed at
  rc 0, so it is not what produces the refusals;
- legend under `## Top risks` — now asserted against, twice;
- a duplicate-Request test tripping the positional check first — the door-2 test
  and the `carry_forward` unit test both carry explicit control assertions, and
  M6 proves the distinction is made.

The one test I judge misleading is
`test_resolve_intake_is_not_blocked_and_does_not_in_fact_shrink` — not green for
a wrong reason, but green on a board that cannot exercise the thing its
docstring claims to record (§ 1).

---

## 4. Structural verdict on the invariant itself

**It is not a fourth predicate, and the author's argument for that is sound.**
`refuse_to_shrink` asks one question about two integers. The four known doors
are closed by it and I could not construct a fifth *inside* it:

- `register_change` is the only register-store writer in `bin/perry-task`
  (`bin/perry-tasks`' `*-write --from-board` importers are the sanctioned
  explicit direction and are out of scope by the spec);
- the guard is applied to `len(derived)` and the write is `store_text(records)`
  — I checked `intake_records` and confirmed `records` and `derived` always have
  the same length, since a `current` merge fills fields per row and never drops
  one, so the guard counts the number actually written;
- the guard runs before the shape early-return, before validation and before
  anything is staged, and M9 shows the order is tested;
- an ordinary re-render does not itself drop register rows, so the guard cannot
  be armed by Perry's own writes.

The fifth door is not in the invariant. It is in the exemption, which is a
name-keyed, unbounded bypass **around** the invariant — the one place round 4
kept round 1's shape, on the user's instruction, without bounding it.

---

## 5. Not checked

1. `6c0d041` under **`bash tests/run`** (98 / 2882 / 3) not re-measured — I
   measured the tip under that runner, and both trees under `discover`.
2. Six of the twelve mutations (M2, M4, M7, M8, M10, M11, M12) were not
   re-run; I spot-checked six including all three the brief singled out.
3. Full suite not re-run per mutation — same limitation the author declares.
4. Crash recovery / `os._exit(9)` at the rename boundaries not re-tested.
5. Localized (`zh`) board not driven through a refusal — same as the author's
   § 10.3.
6. Concurrency between two Perry writers not exercised.
7. `asks.jsonl` and `risks.jsonl` were exercised only through the shape matrix
   and the fixture writes. They are **not** exposed to § 1: `SHRINK_ALLOWED`
   holds `purge` (tasks), `resolve-intake` and `intake-sweep` (both intake), so
   no command may shrink the ask or risk store at all. The blast radius of the
   defect is `intake.jsonl`, which is the register this row's merge-hold
   measurement was taken on and the one the PMO writes most.

---

## 6. What would clear this

One change and one test:

- bound the allowance — an allowed command may shrink by exactly the count it
  declares removing, and `refuse_to_shrink` refuses any excess. `resolve-intake`
  declares 0, so it can no longer shrink at all; `intake-sweep` declares the rows
  it swept; `purge` declares 1;
- and the test that fails without it: the § 1 sequence, on each shrink-permitted
  command — a drifted board, an allowed command, and the assertion that the
  records it did not touch are still on disk.

Rounds 1–3 each closed one door and left another. This round closed four and
left the exemption unbounded.
