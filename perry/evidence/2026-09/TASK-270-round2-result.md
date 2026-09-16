# TASK-270 round 2 — result

> Branch `coding/task-270-state-root-unset`, base `81d5dda1` (main, with round 1 merged).
> Written 2026-09-16 by the Coding Agent, under USER-948.
> Touches architecture: none.

## 1. What USER-948 asked for, and what was built

`perry-config unset "State root"` **refuses** when the state root the setting
points at holds Perry state. It exits 1, writes nothing, names the root and the
stores found there, says what removing the setting would do, and names
`/perry relocate <path>` (`SKILL.md § /perry relocate`) as the reversible move.

There is no override. `perry-config` had no `--force`-style flag, and none was
added: `unset --force` still exits 2 as an undeclared token. Writers are not
guarded.

Code: `bin/perry-config`.

- **`STATE_ROOT_KEY`** is `store.setting_key("State root")`, the same key
  `parsers.declared_state_root` reads.
- **`stores_held_at(state_root)`** gives the canonical stores present under the
  root. Names come from `parsers.canonical_store_names()`, which reads the
  schema's claims; no list is written in the tool. Presence uses
  `parsers.installed`'s test, where an unsearchable path counts.
- **`refuse_unset_over_held_state(project_root, state_root)`** is called in the
  `unset` branch after the label is found to be declared and before `write`, so
  `--dry-run` refuses the same way. The `state_root` it checks is the one
  `main` already resolved with `P.resolve_state_root(root)`.

**Two cases proceed.**
- A declared root that holds no store: there is nothing to strand, so this is
  the decision's "may proceed" case.
- A declared root that already is the project root (`State root: .`): removing
  the setting moves nothing. This is my reading of the decision. Its subject is
  the move to the project root, and a root that already is the project root
  cannot move. Say so if that reading is wrong.

## 2. The round-1 hazard, re-run on this branch

The same script as round 1 § 5: the sample project copied into `<p>/perry/`,
`.perry/` at `<p>/`.

```
$ perry-config set --root <p> "State root" perry
perry-config: set 'State root' — <p>/.perry/config.jsonl now holds 6 record(s)
exit 0
$ perry-task add "before unset" … --unlinked
perry-task: wrote REL-010 (add) → tasks.jsonl + linkage.jsonl + journal + event
exit 0

$ perry-config unset --root <p> "State root"
perry-config: refused — `State root` points at `perry/`, which holds Perry state (asks.jsonl,
cadence.jsonl, linkage.jsonl, risks.jsonl, tasks.jsonl). Removing the setting would move every
later read and write to the project root, where none of that state is: the next write would
start a second, empty store there and every read would stop seeing these. Nothing was written.
To move Perry's state, use `/perry relocate <path>` (`SKILL.md § /perry relocate`) — it moves
every claimed path with `git mv` and is reversible; `/perry relocate .` moves it to the project root.
exit 1

$ perry-task add "after unset" … --unlinked
perry-task: wrote REL-011 (add) → tasks.jsonl + linkage.jsonl + journal + event
exit 0                                   → still perry/tasks.jsonl; nothing created at <p>/

$ perry-task list --root <p>
  REL-001    P0  in_progress  Deploy script hardening
  REL-002    P0  blocked      Flake detector
  REL-009    P1  not_started  Pipeline docs refresh
  REL-010    P2  not_started  before unset
  REL-011    P2  not_started  after unset
  5 open · 1 in_progress · 1 closed · 15 event(s)
```

The next plain `add` (no link flag) was refused for its own reason: the project
has `linkage.jsonl`, so the KR question must be answered. In round 1 the same
command wrote `TASK-001` at the project root.

## 3. The "may proceed" cases

```
### State root declared, never written to
$ perry-config set "State root" perry
perry-config: set 'State root' — <p>/.perry/config.jsonl now holds 6 record(s)
exit 0
perry/ holds: []
$ perry-config unset "State root"
perry-config: unset 'State root' — <p>/.perry/config.jsonl now holds 5 record(s)
exit 0
state_root record left: 0

### State root declared as `.` over a populated project root
$ perry-config unset "State root"
perry-config: unset 'State root' — <p>/.perry/config.jsonl now holds 5 record(s)
exit 0
```

## 4. `set "State root" <other>` has the same hazard (reported, not fixed)

On the same relocated project (`State root: perry`):

```
$ perry-config set --root <p> "State root" elsewhere
perry-config: set 'State root' — <p>/.perry/config.jsonl now holds 6 record(s)
exit 0                                   (no warning)
$ perry-task add --root <p> --title "after set elsewhere" … (plain)
perry-task: warning — TASK-001 was created without `--kr`, and this project has no `linkage.jsonl` …
perry-task: wrote TASK-001 (add) → tasks.jsonl + journal + event
exit 0
files under elsewhere/: elsewhere/journal/2026-09/2026-09-16.md elsewhere/tasks.jsonl
perry/tasks.jsonl last id: REL-009       (untouched)
$ perry-task list --root <p>
  TASK-001   P2  not_started  after set elsewhere
  1 open · 0 in_progress · 0 closed · 14 event(s)
```

This is the same failure as round 1 § 5, reached by the other verb:

- the project's rows vanish from every read;
- ids restart at `TASK-001`;
- a second state tree appears, this time under `elsewhere/`.

The same happens when the new value escapes the project, because
`resolve_state_root` then answers the project root. That was not reproduced
separately; it is read off `parsers.resolve_state_root`. `set` is outside
USER-948, so this needs its own decision. It is also the path
`/perry relocate` itself uses to write the setting, *after* it has moved the
files, so a guard on `set` would have to let that call through.

## 5. The remaining path (the review's § 7 candidate, not fixed)

Round 1 made an empty `.perry/config.jsonl` a usable store. If a project that
declared `State root: perry` has its config store emptied from outside Perry (a
hand truncation, a bad merge), the store is accepted, `State root` reads its
default, and the next write lands at the project root. This round's guard does
not see that path, because it lives in `perry-config unset` and no `unset` ran.
The user chose not to guard the writers, so this path stays open. `perry-config
set` / `track` are also unguarded against it (§ 4).

## 6. Mutations

Each ran on a fresh `git archive HEAD` copy under
`$TMPDIR/perry-scratch/a6b9b6f3cf741ea56/<name>/`, against
`tests/test_state_root_unset.py`. The control copy (R2-M0) was green.

| # | Mutation | Result | Red on |
|---|---|---|---|
| 1 | Refusal removed (`refuse_unset_over_held_state(...)` → `pass`) | **red**, 10 | `test_unset_refuses_over_a_state_root_holding_the_projects_rows`, `test_the_projects_rows_still_list_after_the_refusal`, `test_dry_run_refuses_the_same_way`, `test_every_canonical_store_alone_is_state` (7 subtests) |
| 2 | Check pointed at the project root (`stores_held_at(Path(project_root))`) | **red**, 10 | the same four tests, same 10 failures |
| 3 | Store names hardcoded to a list missing `tasks.jsonl` | **red**, 2 | `test_unset_refuses_over_a_state_root_holding_the_projects_rows` (message no longer names `tasks.jsonl`), `test_every_canonical_store_alone_is_state` (the `tasks.jsonl` subtest) |

No mutation came back green.

## 7. Durations

`tests/durations.json` gains `test_empty_config_store.py` (round 1's module,
unmeasured since its merge) and `test_state_root_unset.py` (new this round).
Each was timed alone three times with `python3 tests/parallel -j 1 --times
<module>` at `f6ec8281`, and the median recorded:

- `test_empty_config_store`: 4.98 / 5.78 / 5.01s → 5.01
- `test_state_root_unset`: 2.42 / 2.31 / 2.28s → 2.31

The source is `2026-09-16-task270`, with load1 24.9. No other module was
re-timed. The runner now reports "every module on disk is accounted for".

## 8. Tests

- `bash tests/run --tier affected --base 81d5dda1` on `f6ec8281`: selected 25
  of 149 modules. 25 modules, 657 tests, green. Tree guard: nothing moved.
- The full `bash tests/run` is quoted in the reply that carries this file, run
  on the commit that contains it.
