# TASK-335 — result

> Spec: `evidence/2026-09/TASK-335-spec.md` · Rung: V3 · Change: tests only
> Branch: `worktree-agent-ae08e8b55e69dfaee` · Code commits: `ef48004c`,
> `f3521349`, `3ac11420`, then this file and `tests/durations.json`

The two anti-vacuity tests read Perry's live checkout, so they went red with the
passage of time alone. Both `live` and `blind` now read **one copy of the tree**
in which every clocked `WITNESSED` collection is pinned empty. A control plants
aged state in the same kind of copy and shows each collection fills without the
freeze and empties with it. Nothing under `bin/`, `viewer/` or `schema/` changed,
and neither did any contract page, `tests/fixtures/contract-key-parity.json`,
`tests/fixtures/witness-project`, `tests/contract_key_parity.py`, or any row.

## 0 base check

- On arrival HEAD was `583f024f` and the tree was clean.
  `git merge-base --is-ancestor b71d8ce5 HEAD` failed (exit 1).
- I ran `git merge --ff-only b71d8ce5` on this branch only, and re-asserted:
  exit 0. Arrived at **`b71d8ce5`**.
- At base the module is red on exactly the two tests the spec names, both on the
  subtest `conformance.in_progress_with_no_live_run[].means` (35 tests, 2 failures).

## 1 the clock-dependent enumeration

All six `WITNESSED` collections, in order. The last one is `tasks[].evidence_relations`.

| collection | reads the clock? | where | frozen? |
|---|---|---|---|
| `expired_sunsets` | **yes**: `a["sunset"][:10] < f"{date.today():%Y-%m-%d}"` for an `active` ADR | `bin/perry-decide § cmd_list` | **yes** |
| `krs[].current_staleness.moved_tasks` | no: a linked task's state-move `ts` against the register's `asserted_at`, both through `lib.ts_key`, with no `now` | `bin/lib/__init__.py` staleness block | no (see below) |
| `conformance.depends_on_unknown` | no: a `depends_on` id that no register carries is set membership | `bin/perry-task § resolve_dependency_edges` | no |
| `conformance.in_progress_with_no_live_run` | **yes**: `now - updated >= in_progress_idle_hours` (4), `now=datetime.now()`, and not in the live dispatch markers | `bin/perry-task § stranded_row_findings`, `§ live_dispatch_ids` | **yes** |
| `conformance.review_idle` | **yes**: `now - updated >= review_idle_days * 24` (72h) | `bin/perry-task § stranded_row_findings` | **yes** |
| `tasks[].evidence_relations` | no: the evidence cell against the files on disk | `bin/perry-task § evidence_relations` | no |

Why each frozen collection is frozen:

- **`in_progress_with_no_live_run`** is the one that broke. It is in `MUTATED`,
  and it filled on 2026-09-14 when TASK-436 went 4 hours without an event.
- **`expired_sunsets`** is in `MUTATED`. Today it is empty by data: no ADR
  carries a dated sunset, since every one reads `—`. But the first ADR written
  with a future sunset would fill it on that date, on an unchanged tree. That
  is exactly this defect's failure mode, so it is pinned too.
- **`review_idle`** is not in `MUTATED`, and no blind assertion depends on it.
  The idle-table mutation asserts only the `in_progress_with_no_live_run` key.
  It is the same function and the same clock, so pinning it costs nothing. It
  also makes the blind reading independent of the calendar for every clocked
  collection, not just the two that are asserted.

Why the other three are not clock-dependent:

- **`moved_tasks`** compares two timestamps that are both data, and no `now` is
  involved. On a frozen copy nothing appends to the log or the register, so it
  cannot move. It does depend on the machine's local zone, because a zoneless
  log line is read as local time (TASK-144). That is the machine, not the clock.
  Also, `krs[0]` (`O1-KR1`) is unasserted today (`evaluated: false`), so its
  `moved_tasks` is `[]` regardless.
- **`depends_on_unknown`** is membership of an id in the registers.
- **`evidence_relations`** is the cell and the file tree.

Not pinned, and why: the dispatch markers under `~/.cache/perry/in-flight`,
compared by mtime against `time.time()` and `PERRY_DISPATCH_STALE_TTL`. A live
marker can only remove a row from `in_progress_with_no_live_run`, never add one.
It cannot fill a collection the blind tests hold empty. The directory was empty
when measured. The control's planted ids are held by no marker.

The thresholds themselves come from `schema/state-schema.json § thresholds`,
not from the project. So a copy cannot pin them by config, and the freeze pins
the rows' last event instead.

## 2 the freeze, and how the copy is built

**What the measured commands read.** Measured with an audit hook on `open` and
directory listing while `measure()` ran all six contracts against the checkout:

- `perry/`: `tasks.jsonl`, `asks.jsonl`, `intake.jsonl`, `risks.jsonl`,
  `linkage.jsonl`, `okr.jsonl`, `OKR.md`, `phase/`, every ADR and DESIGN page,
  and `knowledge/`;
- `.perry/`: `config.jsonl`, `events.jsonl`, `hook.md`;
- `packs/software-ops/pack.md`;
- directory listings of `.`, `bin` and `viewer`.

Evidence cells are resolved with `stat`, which the hook does not see, and they
name files anywhere in the project, `bin/` and `tests/` included. So the copy is
the whole tree, not the stores alone.

**`copy_of_perry`** is `shutil.copytree(parity.ROOT, dest)` leaving out `.git`,
`.claude` and `__pycache__`. `.claude/` holds other sessions' whole worktrees in
the main checkout.

- **Fidelity:** `measure()` on an unfrozen copy equals `measure()` on the
  checkout with only `root` removed, both with the witness and without. There
  were 0 differences each way.
- **Rejected alternative:** a hybrid copy (real `perry/` and `.perry/`, every
  other entry a symlink) also read 0 differences and copied in 0.5s against
  0.9–2.3s. I rejected it: a symlink is a path back into the live tree, and this
  row may not write there.
- **Once per module.** `frozen_copy()` builds the copy on first use and removes
  it through `unittest.addModuleCleanup`. The control builds its own.

**`freeze_the_clock(root)`**:

- **Idle rows get an appended event, not a restamp.** Every `in_progress` or
  `review` row in the copy's `perry/tasks.jsonl` gets one `next` event stamped
  now (`bin/lib § event_stamp`'s shape). The event restates the row's
  `next_action` unchanged, so the row's last event is seconds old.
- **Why not restamp in place**, as the spec's example suggests: TASK-436's
  latest event is a `start`, a state move (`to: in_progress`). Moving a state
  move after a KR's `asserted_at` fills `moved_tasks`, one of the four
  collections the blind tests hold empty. A `next` event's `to` is prose, not a
  status, so `lib._is_state_move` is false and nothing moves.
- **Sunsets are pushed out.** Which sunsets count comes from `perry-decide list`
  on the copy, the tool's own reading. It is not parsed here. Each dated sunset
  becomes `9999-12-31` on the `>` header lines of that ADR.
- **Today's freeze report:** restamped `TASK-436`, `TASK-237`, `TASK-335`;
  sunsets `[]`.

**`refuse_the_checkout(root)`** runs before the first write in each writer. It
raises when the target is the checkout or inside it. This was added after a
mutation showed it was needed (section 5).

**Wiring:**

- `TestAWitnessProjectMakesAnEmptyCollectionObservable` now reads
  `live = measure(frozen_copy())` and
  `blind = measure(frozen_copy(), witness=None)`. The two readings moved from
  `setUp` to `setUpClass`. No case writes to either, and reading per case was 14
  measurements once two cases were added. No assertion changed.
- `TestTheWitnessedKeysRedden.mutate` calls
  `compare(copy, frozen_copy(), witness=witness)` for both witness values.
- **`tests/contract_key_parity.py` is unchanged.** `measure(root, witness)` and
  `compare(path, root, witness=...)` already pass `--root` to every command.
  `discover()` still globs the checkout's `schema/`, which is right: the pages
  are the thing measured, not project state.

## 3 the new control

`TestTheFreezeIsLoadBearing` builds a second copy and plants three pieces of
aged state in it, independent of whatever the live board holds:

- `CTL-001`, `in_progress`, whose `add` and `start` events are 30 days old;
- `CTL-002`, `review`, whose `add`, `start` and `status` events are 30 days old;
- `ADR-999-freeze-control.md`, `active`, with `Sunset: 2000-01-02`.

It reads the blind comparison and the tool payload of `task-list-contract.md`
and `decide-list-contract.md`, then applies `freeze_the_clock` to **the same
copy** and reads both again.

- `test_without_the_freeze_aged_state_fills_every_clocked_collection` — for
  each of the three clocked collections, the planted id is in the tool's
  collection. The key is also in none of `not_observable`,
  `documented_not_emitted` or `emitted_not_documented`.
- `test_the_freeze_empties_every_clocked_collection_again` — the freeze
  restamped both planted rows and pushed `ADR-999`. Each collection is `[]`, and
  each key is in `not_observable` with its collection named in the reason.

Three guards were added to the witnessed class:

- `test_live_and_blind_read_one_frozen_copy` — both readings' `root` is the
  frozen copy and is not the checkout. `live.witness` is the witness and
  `blind.witness` is empty.
- `test_the_freeze_has_its_control` — the control class exists, with exactly
  its two cases.
- `test_the_writers_refuse_the_checkout` — the guard refuses the checkout and
  `perry/` inside it, and accepts the frozen copy. It calls the guard only,
  never a writer.

The ids `CTL-001`, `CTL-002` and `ADR-999` exist only inside temporary copies.
They are in no store.

## 4 the time machine

The harness is `scratchpad/mutate.py <commit> timemachine`. It takes a
`git archive` copy and, in its `.perry/events.jsonl`, moves every event of every
row whose status is `in_progress` or `review` 30 days back: 52 events, on
`TASK-237`, `TASK-335` and `TASK-436`.

| step (at `3ac11420`) | result |
|---|---|
| as committed | OK, 40 tests |
| freeze removed (`_FROZEN["freeze"] = {}`) | FAILED (failures=2): `test_without_the_witness_the_four_are_unobservable`, `test_the_same_mutation_is_silent_without_the_witness` |
| restored (bytes equal `git show 3ac11420:tests/test_contract_key_parity.py`) | OK, 40 tests |

The same three readings came out identically at `ef48004c` and `f3521349`.

## 5 mutation table

The harness is `scratchpad/mutate.py 3ac11420 mutations`. For every row:

- a fresh `git archive` of `3ac11420`;
- the anchor is asserted to occur exactly once;
- `__pycache__` is cleared;
- the module is run with `python3 -m unittest discover`;
- the file is restored and compared with `git show 3ac11420:tests/test_contract_key_parity.py`;
- the archive's `.perry/events.jsonl`, `perry/tasks.jsonl` and
  `perry/decisions/` file set are compared with the commit.

The unmutated run was OK, 40 tests, with the stores unchanged.

| # | mutation | result | red tests | stores changed |
|---|---|---|---|---|
| M1 | remove the freeze (module copy built unfrozen) | failures=2 | `test_without_the_witness_the_four_are_unobservable`, `test_the_same_mutation_is_silent_without_the_witness` | none |
| M2 | gut `freeze_the_clock` (return before pinning) | failures=3 | the two above + `test_the_freeze_empties_every_clocked_collection_again` | none |
| M3 | remove the witness from `live` | failures=7 | `test_every_key_in_those_collections_is_actually_compared`, `test_live_and_blind_read_one_frozen_copy`, `test_not_observable_still_names_anything_left_uncovered` | none |
| M4 | `blind` reads the live checkout (`measure(witness=None)`) | failures=2 | `test_live_and_blind_read_one_frozen_copy`, `test_without_the_witness_the_four_are_unobservable` | none |
| M5 | `mutate()` reads the live checkout when blind | failures=1 | `test_the_same_mutation_is_silent_without_the_witness` | none |
| M6 | delete the freeze control class | errors=1 (38 tests) | `test_the_freeze_has_its_control` | none |
| M7 | the freeze skips `review` rows | failures=1 | `test_the_freeze_empties_every_clocked_collection_again` | none |
| M8 | the freeze skips sunsets | failures=1 | `test_the_freeze_empties_every_clocked_collection_again` | none |
| M9 | the sunset rewrite touches no header line | failures=1 | `test_the_freeze_empties_every_clocked_collection_again` | none |
| M10 | the control plants rows that are not aged | failures=2 | `test_without_the_freeze_aged_state_fills_every_clocked_collection` | none |
| M11 | the control plants no expired sunset | failures=2 | both control cases | none |
| M12 | the control guard names a case that does not exist | failures=1 | `test_the_freeze_has_its_control` | none |
| M13 | the copy step returns the checkout itself | failures=8, errors=2 (30 tests) | `setUpClass` of both classes (the guard refuses), `test_removing_a_witnessed_key_from_its_page_is_reported`, `test_the_same_mutation_is_silent_without_the_witness` | **none** |
| M14 | the write guard never refuses | failures=2 | `test_the_writers_refuse_the_checkout` | none |
| M13+M14 | both at once | failures=3 | `test_live_and_blind_read_one_frozen_copy`, `test_the_writers_refuse_the_checkout` | **`.perry/events.jsonl`, `perry/tasks.jsonl`, `perry/decisions/`** |

**Findings, in the order they were found:**

1. **At `ef48004c`, the version of M13 without a guard wrote the archive's own
   stores.** The control's `setUpClass` appended `CTL-*` rows and events, and
   wrote `ADR-999` into that tree, before any assertion ran. The guard test
   failed, but only after the write. The next run in the same archive then
   errored on duplicate ids. In a real checkout, that defect writes Perry's live
   stores. Fixed at `f3521349` with `refuse_the_checkout`, called before the
   first write. M13 now leaves the stores unchanged, and the pair M13+M14 shows
   what the guard prevents.
2. **At `f3521349`, M14 was green.** While the copy step is correct the guard
   never sees a checkout, so nothing could notice it was gone. Fixed at
   `3ac11420` with `test_the_writers_refuse_the_checkout`.

**Which reds depend on the board.** M1, M4 and M5 redden the two original tests
because the source tree has an idle `in_progress` row: today TASK-436, and every
row in the time machine. On a board with no clocked row those two would stay
green under M1 and M5. The mutations that do not depend on the board are:

- **M2**, which reddens the control;
- **M4**, which reddens `test_live_and_blind_read_one_frozen_copy`.

Nothing makes "`mutate()` reads the live checkout" (M5) red independently of the
board. `compare()` does not report which root it read. See "What I did not check".

## 6 durations

Each figure is the module alone through `python3 tests/parallel
test_contract_key_parity --times`, on a `git archive` copy, taken three times
(`scratchpad/timing.py`).

| commit | runs | median | tests |
|---|---|---|---|
| `b71d8ce5` (base) | 5.20 / 5.12 / 5.19 s | **5.19 s** | 35 (2 red) |
| `3ac11420` (final code) | 7.03 / 6.14 / 6.00 s | **6.14 s** | 40 |

- **It grew by about 0.95s**, which is the two tree copies. `tests/durations.json`
  now records `test_contract_key_parity.py` at 6.14s under a new source
  `2026-09-14-task335`, in the existing single-module note style.
- The previously recorded 9.83s came from a loaded `-j 8` sweep on 2026-09-09.
- The first working version, with per-case readings, took 13.9s wall in one
  `discover` run. Moving the two readings to `setUpClass` removed most of that.

## 7 suite on the final commit

The full suite runs in the foreground, with no writes during the run, on the
commit that carries this file. The totals and the SHA are in the dispatch
report. Writing them here would create another commit, and that commit would
then not be the one the suite ran on.

## 8 rows named (none minted)

- `TASK-335`: this row, `in_progress`. Not changed.
- `TASK-436`: the idle `in_progress` row whose age reddened the tests. Still
  `in_progress` and idle (75.4h at the last probe). Not changed.
- `TASK-237`: `in_progress`. Restamped only inside temporary copies.
- `TASK-132`: the row that built the witness classes. Cited only.

No row was opened, closed or edited, and no id was minted. `CTL-001`, `CTL-002`
and `ADR-999` exist only in temporary copies.

## What I did not check

- **No board-independent guard that `mutate()` reads the frozen copy.**
  `compare()` does not report which root it read, so M5 goes red only when the
  source tree has an idle row. Adding `root` to `compare()`'s return would give
  it one, but that is a change to `tests/contract_key_parity.py` and it is not
  needed for the spec's deliverable.
- **Clock reads outside `WITNESSED`.** These were not examined:
  `bin/perry-task` around line 1254 (an age in days), `bin/perry-goals` around
  line 1064 (an age) and line 2578 (a phase `current < date.today()`), and
  anything in `perry-state`. They may move other modules that read the live
  checkout, such as `test_contract_invariance` or
  `test_the_live_roles_page_names_no_collection_and_stays_unassigned`. Nothing
  in the two classes this row covers depends on them.
- **The freeze's `now` is the build time.** A measurement more than 4 hours
  after `frozen_copy()` ran would refill `in_progress_with_no_live_run`. The
  module takes seconds, so this was not guarded.
- **Copy time in the main checkout.** The copy includes untracked and ignored
  entries other than `.git`, `.claude` and `__pycache__`. If the main checkout
  holds a large `.gstack/` or `.trae/` (both gitignored), the copy there is
  slower than the 0.9–2.3s measured in this worktree. That checkout was not
  touched, so it was not measured.
- **Other machines and zones.** Runs were on this machine only (darwin, UTC+8).
  `load1` was not sampled for the timings.
