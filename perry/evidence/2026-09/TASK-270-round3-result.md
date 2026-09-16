# TASK-270 round 3 — result

> Branch `coding/task-270-state-root-unset`, merged with main `3df4f61f`.
> Written 2026-09-16 by the Coding Agent, under USER-949.
> Touches architecture: none.

## 1. Merging main: `tests/durations.json` as a union

`git merge main` (main at `3df4f61f`, carrying TASK-416's `a4311a9c`) conflicted
in `tests/durations.json` only. All three module entries had auto-merged:
`test_empty_config_store` and `test_state_root_unset` from this branch, and
`test_kr_checks` from main. The only conflict was the two adjacent source
stamps, `2026-09-16-task270` and `2026-09-16-task416`, and both were kept.
Merge commit: `776a308b`.

I checked it by machine, not by eye:

- The file parses, and no conflict markers are left.
- Against `git show main:tests/durations.json` and this branch's pre-merge file:
  for both `modules` and `sources`, no key is lost and no value changed on
  either side. The two null module entries (`test_handed_back_root.py`,
  `test_scratch_is_per_agent.py`) are identical on main.
- `python3 -m unittest tests.test_durations_provenance`: 24 tests, OK.

## 2. What USER-949 asked for, and what was built

`perry-config set "State root" <value>` **refuses** when all three hold:

- the value moves where state resolves;
- the current resolved root holds a canonical store;
- the root the value would resolve to holds none.

It exits 1 and writes nothing. It names both roots and the stores found, and
says every later read and write would move to a root with none of the
project's state. It names `/perry relocate <path>` (`SKILL.md § /perry relocate`).

**It proceeds when** the current root holds nothing, when the target already
holds a store (relocate's case, or pointing back at an existing root), or when
the value resolves where state already is (e.g. `./perry` for `perry`).

**One presence test, shared.** `viewer/parsers.py § canonical_stores_under(state_root)`
returns the canonical stores present, with names from `canonical_store_names()`
and the `exists_or_unreadable(...) is not False` test. There are three callers:
`parsers.installed` (which held the test inline before), `perry-config § unset`'s
refusal, and `perry-config § set`'s refusal. The round-2 local helper
`stores_held_at` is gone.

**One resolution rule, shared.** `set` has to know where a value it has not
written *would* resolve. `resolve_state_root`'s rule moved, unchanged, into
`parsers.state_root_for(project_root, raw)`, and `resolve_state_root` now calls
it. The value is normalised by `store.stored_value`, the same call `cmd_set`
stores it through. Moving the rule moved one blank-spelling exemption with it.
`tests/test_blank_cell_is_one_rule.py`'s `EXEMPT` now keys the `State root`
path set to `state_root_for`, with the same set and the same reason.

No flag, and no bypass for relocate: `set --force` exits 2.

**`unset` is unchanged.** The round-2 reading stands: it proceeds when the root
already resolves to the project root. It still refuses whenever the root it
leaves holds a store. It does not exempt a project root that also holds stores;
USER-948 did not ask for that, and nothing here changes it.

## 3. The `set` hazard, before and after

The same project as rounds 1 and 2: the sample project in `<p>/perry/`,
`.perry/` at `<p>/`, `State root: perry`.

### Before: `776a308b` (round 2 plus the merge)

```
$ perry-config set "State root" elsewhere
perry-config: set 'State root' — <p>/.perry/config.jsonl now holds 6 record(s)
exit 0
State root now: "value": "elsewhere"
$ perry-task add (plain)
perry-task: wrote TASK-001 (add) → tasks.jsonl + journal + event
exit 0
files under elsewhere/: [elsewhere/journal/2026-09/2026-09-16.md elsewhere/tasks.jsonl ]
perry/tasks.jsonl last id: "id": "REL-009"
$ perry-task list
  TASK-001   P2  not_started  after set elsewhere
  1 open · 0 in_progress · 0 closed · 14 event(s)
```

### After: this branch

```
$ perry-config set "State root" elsewhere
perry-config: refused — `State root` resolves to `perry/`, which holds Perry state (asks.jsonl,
cadence.jsonl, linkage.jsonl, risks.jsonl, tasks.jsonl), and 'elsewhere' would resolve to
`elsewhere/`, which holds none of it. Setting it would move every later read and write to a root
with none of this project's state: the next write would start a second, empty store there and
every read would stop seeing these. Nothing was written. To move Perry's state, use
`/perry relocate <path>` (`SKILL.md § /perry relocate`) — it moves every claimed path first and
sets `State root` after, and it is reversible.
exit 1
State root now: "value": "perry"
$ perry-task add (plain)
perry-task: refused — neither --kr nor --unlinked was passed. This project has a `linkage.jsonl` …
exit 1                                   (its own rule: the project's linkage store is still found)
files under elsewhere/: []
perry/tasks.jsonl last id: "id": "REL-009"
$ perry-task list        (last lines)
  REL-002    P0  blocked      Flake detector
  REL-009    P1  not_started  Pipeline docs refresh
  3 open · 1 in_progress · 1 closed · 13 event(s)
```

## 4. Relocate's order, and the other cases that proceed

`reference/router-subcommands.md § /perry relocate` runs **step 5** (`git mv`
each existing claimed path) before **step 6** (`perry-config set --root .
"State root" <path>`). So relocate never calls `set` before the files are at
the target, and there is nothing to report about its order. The reproduction
follows the same order: every claim not anchored at the project, moved if it
exists, then `set`. Output from this branch:

```
### relocate's order: move every claimed path into newroot/, then set
moved: OKR.md phase/ tasks.jsonl risks.jsonl asks.jsonl cadence.jsonl linkage.jsonl PROJECT_STATE.md decisions/ journal/ evidence/ weekly/ handoff/ inputs/ design/
$ perry-config set "State root" newroot
perry-config: set 'State root' — <p>/.perry/config.jsonl now holds 6 record(s)
exit 0
$ perry-task list
  REL-009    P1  not_started  Pipeline docs refresh
  3 open · 1 in_progress · 1 closed · 13 event(s)

### pointing back at a root that already holds state
$ perry-config set "State root" other
exit 0

### a value that does not change where state resolves
$ perry-config set "State root" ./perry
exit 0

### the current root holds nothing
$ perry-config set "State root" elsewhere
exit 0
```

`test_relocates_own_order_proceeds` pins the `newroot` case. `/perry relocate .`
is not tested separately; by the code it takes the same path, because after the
move the old root holds nothing and `set` proceeds whatever the target holds.

## 5. The remaining path (unchanged, not fixed)

A config store emptied from outside Perry (a hand truncation, a bad merge) is
accepted as a usable empty store since round 1. If it had declared
`State root`, the setting is gone with it, and the next write resolves to the
project root. Neither refusal sees this, because no `perry-config` command runs
on that path, and by the user's choice the writers are not guarded.

## 6. Mutations

Each ran on a fresh `git archive HEAD` copy under
`$TMPDIR/perry-scratch/a6b9b6f3cf741ea56/<name>/`, against
`tests/test_state_root_unset.py`. The control copy (R3-M0) was green.

| # | Mutation | Result | Red on |
|---|---|---|---|
| 1 | The `set` refusal removed (the call → `pass`) | **red**, 16 | `test_set_refuses_to_strand_a_state_root_holding_the_projects_rows`, `test_set_dry_run_refuses_the_same_way`, `test_every_canonical_store_alone_is_state_on_both_sides` (7), `test_set_and_unset_ask_the_one_presence_test` (7) |
| 2 | The target-holds-state exemption removed | **red**, 8 | `test_every_canonical_store_alone_is_state_on_both_sides` (the 7 target-side subtests), `test_pointing_back_at_a_root_that_holds_state_proceeds` |
| 3 | The presence check copied into `set` instead of shared, with one side changed (the copy skips `linkage.jsonl`) | **red**, 3 | `test_every_canonical_store_alone_is_state_on_both_sides` (`linkage.jsonl` current and target), `test_set_and_unset_ask_the_one_presence_test` (`linkage.jsonl`) |

No mutation came back green.

Mutation 2 did **not** turn `test_relocates_own_order_proceeds` red. In that
test the old root is empty after the move, so the "current root holds nothing"
exemption lets `set` through independently. The target-side exemption is pinned
by the target-side subtests and by `test_pointing_back_…` instead. If relocate
ever copied rather than moved, only those would catch it.

## 7. Tests and durations

- `bash tests/run --tier affected --base 3df4f61f`, first run, on `f724869e`:
  2 modules red.
  - `test_blank_cell_is_one_rule`: 2 failures, both from the exemption keyed
    to the old function name. Fixed in `5e86c3db`.
  - `test_host_support § test_concurrent_mixed_registers_do_not_exceed_global_cap`:
    `4 != 3` under contention. Re-run alone it was green (35 tests), and this
    row touches nothing it covers, so I attribute it to load, not to the change.
- Second run, on `5e86c3db`: selected 150 of 150 modules ("this change is wide",
  `viewer/parsers.py`), 147 run, 4172 tests, green. Tree guard: nothing moved.
- `tests/durations.json`: `test_state_root_unset` grew from 8 to 18 tests, so its
  2.31s was stale. I re-timed it alone three times (17.10 / 9.37 / 9.60s, median
  9.60) under source `2026-09-16-task270-r3`. load1 was 152.71, so the figure is
  likely high; `test_empty_config_store`, timed in the same window for
  comparison, ran 18–22s against its recorded 5.01s. No other module was
  re-timed. `test_durations_provenance` is OK.
- The full `bash tests/run` is quoted in the reply that carries this file, run
  on the commit that contains it.
