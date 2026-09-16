# TASK-270 — result

> Branch `coding/task-270-empty-config-store`, base `538d94a7` (main's tip at dispatch).
> Written 2026-09-16 by the Coding Agent.
> Inputs: `TASK-270-spec.md` and `TASK-270-reproduction-2026-09-16.md`. At dispatch
> both sat untracked in the PMO's checkout and are not on this branch.
> Touches architecture: none. No section of `ARCHITECTURE.md` or `bin/ARCHITECTURE.md` changes.

## 1. The rule, and why

**A writer refuses `.perry/config.jsonl` exactly when the store may hide a
declaration. That means bytes that did not parse (`unreadable`) or a record that
did not validate (`invalid`). Record count is not part of the rule. An empty store
is usable, and it answers DESIGN-003's defaults.**

I took the rule from the refusal's own stated reason. Writing "would stamp
DESIGN-003's implicit `main` over whatever this project actually declares and
lose that track's mode, stages, WIP and SLA". That is true only when a
declaration might exist and could not be read. A store that parsed and validated
in full has had every declaration read. A settings-only store has already been
accepted on those terms since TASK-095 round 2 (`store-default`). An empty store
is the same case with no settings either. It declares no track, so there is
nothing for `main` to stamp over. A project with no store at all already gets
that answer, and so does every other register (`perry-tasks`: "An EMPTY store is
a store").

The code gave two reasons for classifying an empty store `invalid`. Both were
false by 2026-09-16:

- "`perry-config write --from-file` never produces one": that importer is gone
  (DESIGN-016, `0f367ff7`), and `perry-config unset` of the last setting produces
  one at exit 0.
- "an interrupted write still produces one": `perry-config` is the only writer of
  the file, and it writes through `lib.write_atomic`, which is `os.replace`. A
  reader sees the old store or the new one, never a torn empty file.

**Outcome 4 was decided together with this.** Emptying the store is allowed, so
`unset` does not refuse. It says what it leaves behind instead.

**Must-not 3 holds.** A non-empty store with a record that does not validate is
refused exactly as before, with the same wording (asserted by
`test_a_non_empty_invalid_store_is_refused_exactly_as_before`).

## 2. Where the shared predicate lives

`viewer/parsers.py § config_store_unusable(project_root) -> str`. It returns `''`
when a writer may act, otherwise `unreadable` or `invalid`. It is built on
`config_store_records`, the existing one reader, whose empty-store branch no
longer returns `invalid`. It lives in `parsers.py`, not `bin/lib`, because that is
where the classification already was (NN-1), and all three tools already import it.

| Caller | What it does with the predicate |
|---|---|
| `bin/perry-task § main` | refuses a write when the predicate is non-empty (reads still pass) |
| `bin/perry-goals § tracks_of` | refuses when the predicate is non-empty |
| `bin/perry-lint § check_config_store` | the census verdict (`comparison_performed`) is `not unusable`. If the predicate says unusable while lint's own findings named nothing, lint emits a warning saying so instead of printing clean. |
| `bin/perry-state § TRACKS_STORE_UNUSABLE` | now *is* `parsers.CONFIG_STORE_UNUSABLE` (identity asserted), not a second set holding the same two strings |

Other changes:

- **Outcome 3.** `perry-lint § looks_like_perry_state` treats an empty file at a
  file claim anchored at `project` as Perry's own. Those claims are
  `.perry/config.jsonl` and `.perry/events.jsonl`, both inside `.perry/`, which is
  Perry's anchor. State-root stores are still judged by their first record.
- **Outcome 4.** When a write leaves no records, `perry-config § write` prints a
  note on stderr, so `--json` stdout stays one object. `unset` and `untrack` share
  that path. The note says the store stays usable, what the defaults now are
  (including `State root` being the project root), and how to recover:
  `perry-config set <label> <value>` or `perry-config track <name>`. Under
  `--dry-run` it says "would leave".
- **Census.** An empty usable store now prints its own line instead of
  `0 record(s), all valid`.

## 3. Reproduction: before and after

Run on a copy of `tests/fixtures/sample-project` under
`$TMPDIR/perry-scratch/a6b9b6f3cf741ea56/`, with `PERRY_PROJECT` and `PERRY_HOME`
unset. Paths are shortened to `<copy>`. Lint output is filtered to the lines about
the config store and NS-01. The `evidence/` and `inputs/` NS-01 warnings are
fixture content and appear the same in both runs.

### Before: `538d94a7`

```
$ perry-config unset "Document language" … "Last updated"    (five commands)
perry-config: unset 'Last updated' — <copy>/.perry/config.jsonl now holds 0 record(s)
exit 0                                                         (all five exit 0)
records: 0  bytes: 0

$ perry-task add
perry-task: refused — the track register cannot be read: `.perry/config.jsonl` exists but
holds records that do not validate. `.perry/config.jsonl` is the only register, so writing
now would stamp DESIGN-003's implicit `main` over whatever this project actually declares
and lose that track's mode, stages, WIP and SLA. Nothing was written. Repair the store —
`perry-lint` names the records that do not validate.
exit 1

$ perry-lint --root <copy>
  ⚠ .perry/config.jsonl [NS-01] `.perry/config.jsonl` holds 1 file(s) Perry did not write. …
  · config store: 0 record(s), all valid

$ perry-config set "Document language" English
perry-config: set 'Document language' — <copy>/.perry/config.jsonl now holds 1 record(s)
exit 0
$ perry-task add
perry-task: wrote REL-010 (add) → tasks.jsonl + linkage.jsonl + journal + event
exit 0
```

### After: this branch

```
$ perry-config unset "Document language" … "Code repo path"   (four commands, as before)
$ perry-config unset "Last updated"
perry-config: note — this leaves `.perry/config.jsonl` holding no records. The store stays
usable: the project declares no settings and no tracks, so every setting reads its default
(`State root` is the project root) and every writer works against DESIGN-003's one implicit
track `main`, mode `project`. To declare one again: `perry-config set <label> <value>` or
`perry-config track <name>`.
perry-config: unset 'Last updated' — <copy>/.perry/config.jsonl now holds 0 record(s)
exit 0
records: 0  bytes: 0

$ perry-task add
perry-task: wrote REL-010 (add) → tasks.jsonl + linkage.jsonl + journal + event
exit 0

$ perry-lint --root <copy>
  · config store: empty — this project declares no settings and no tracks, so every writer
    uses the defaults (`perry-config set <label> <value>` or `perry-config track <name>` declares one)
  (no NS-01 line for .perry/config.jsonl)

$ perry-config set "Document language" English
perry-config: set 'Document language' — <copy>/.perry/config.jsonl now holds 1 record(s)
exit 0
$ perry-task add
perry-task: wrote REL-011 (add) → tasks.jsonl + linkage.jsonl + journal + event
exit 0
```

The same copy with an **invalid** record appended, on this branch. The refusal is unchanged:

```
$ perry-goals commit --track main …
perry-goals: refused — the track register cannot be read: `.perry/config.jsonl` exists but holds records that do not validate. …
exit 1
$ perry-task add …
perry-task: refused — the track register cannot be read: `.perry/config.jsonl` exists but holds records that do not validate. …
exit 1
$ perry-lint --root <copy>
  ⚠ .perry/config.jsonl [config-store-badly-typed] track/intake — `mode` is list, expected string or null. …
  · config store: 5 valid record(s), and at least one that is not — every writer refuses the store whole
```

On the empty store, `perry-goals commit` now gets past the register and refuses
for this fixture's own reason (no `## Commitments` section).

## 4. Mutations

Each mutation ran on a fresh `git archive HEAD` copy under
`$TMPDIR/perry-scratch/a6b9b6f3cf741ea56/<name>/`, against
`tests/test_empty_config_store.py` and `tests/test_track_register_source.py`.
An unmutated control copy (M0) was green in both.

| # | Mutation | Result | Red on |
|---|---|---|---|
| 1 | The empty-store message restored to "holds records that do not validate": `if not good: return None, CONFIG_STORE_INVALID` put back in `parsers.config_store_records` | **red**, 6 + 1 | `test_perry_task_add_writes_on_an_empty_store`, `test_perry_goals_passes_the_register_on_an_empty_store`, `test_the_end_to_end_reproduction`, `test_the_parser_classifies_an_empty_store_as_usable`, `test_a_blank_lines_only_store_is_the_same_empty_store`, `test_every_shape_gets_one_answer_from_every_tool`; `test_track_register_source § test_an_empty_store_answers_like_a_settings_only_store` |
| 2a | Predicate forked on the writer side: `perry-task` also treats an empty file as `invalid` | **red**, 3 | `test_every_shape_gets_one_answer_from_every_tool`, `test_perry_task_add_writes_on_an_empty_store`, `test_the_end_to_end_reproduction` |
| 2b | Predicate forked on the linter side: census keyed on `not unusable and bool(good)` | **red**, 2 | `test_every_shape_gets_one_answer_from_every_tool`, `test_the_end_to_end_reproduction` |
| 3 | `NS-01` flags the empty config store again (the anchor clause disabled) | **red**, 2 | `test_an_empty_config_store_is_not_a_collision`, `test_an_empty_state_root_store_is_still_judged_by_its_record` |
| 4 | A writer accepts a genuinely invalid non-empty store: `perry-task` refuses only `unreadable` | **red**, 3 | `test_a_non_empty_invalid_store_is_refused_exactly_as_before`, `test_every_shape_gets_one_answer_from_every_tool` (two subtests) |

No mutation came back green.

## 5. The State-root investigation (reported, not fixed)

**Question:** on a project whose state root is `perry/`, does
`perry-config unset "State root"` make the next write land at the project root?
**Yes. The unset is silent, and the next write exits 0 and creates a second,
empty-headed state tree at the project root.** Reproduced on this branch and
independent of this change: `resolve_state_root` answered the project root for a
missing `state_root` before and after.

Setup: a copy of `tests/fixtures/sample-project` moved to `<p>/perry/`, with
`.perry/` at `<p>/`.

```
$ perry-config set --root <p> "State root" perry
perry-config: set 'State root' — <p>/.perry/config.jsonl now holds 6 record(s)
exit 0
$ perry-task add --root <p> --title "before unset" … --unlinked
perry-task: wrote REL-010 (add) → tasks.jsonl + linkage.jsonl + journal + event
exit 0                                       → lands in perry/tasks.jsonl (REL-009, REL-010)

$ perry-config unset --root <p> "State root"
perry-config: unset 'State root' — <p>/.perry/config.jsonl now holds 5 record(s)
exit 0                                       (no warning of any kind)

$ perry-task add --root <p> --title "after unset" … --unlinked
perry-task: refused — --unlinked needs `linkage.jsonl` and this project has none … `TASK-001` would file …
exit 1                                       (refused by accident: no linkage store at the root)

$ perry-task add --root <p> --title "after unset, plain" …
perry-task: warning — TASK-001 was created without `--kr`, and this project has no `linkage.jsonl` …
perry-task: wrote TASK-001 (add) → tasks.jsonl + journal + event
exit 0

files created at the project root:  tasks.jsonl, journal/2026-09/2026-09-16.md
./tasks.jsonl:  {"id": "TASK-001", "title": "after unset, plain", …}
perry/tasks.jsonl last id:  REL-010   (untouched)

$ perry-task list --root <p>
  TASK-001   P2  not_started  after unset, plain
  1 open · 0 in_progress · 0 closed · 15 event(s)
```

So a single exit-0 command:

- hides the project's ten rows from every read;
- restarts the id family at `TASK-001`, where the project's prefix is `REL`;
- writes a new `tasks.jsonl` and `journal/` beside the user's own files.

The only warning printed is about the missing linkage store, not the move. This
is the larger hazard the spec anticipated. Fixing it changes where a project's
state lives, which is the claim surface and the user's decision. Two possible
shapes, neither built:

- `perry-config unset "State root"` refuses (or asks for `--force`) when the
  declared root holds Perry state and the project root does not;
- or a writer refuses when the resolved state root holds no canonical store
  while a declared one did.

## 6. Tests

- `bash tests/run --tier affected --base 538d94a7`: selected 148 of 148 modules
  ("this change is wide", because `viewer/parsers.py` is touched). 145 modules,
  4106 tests, green. Three harness self-tests were held back to `--tier slow`.
  Tree guard: nothing moved.
- The full `bash tests/run` is quoted in the reply that carries this file, run on
  the commit that contains it.

## 7. Noticed, not changed

- The `unreadable` refusal in both writers still ends "`perry-lint` names the
  records that do not validate". For a torn store, lint names it
  `config-store-unreadable` rather than naming records. The wording is slightly
  off, but it is outside the four outcomes.
- `NS-01` still judges an **empty state-root store** (e.g. `tasks.jsonl`) by its
  first record, so an empty one would still be called foreign. Out of scope; the
  test pins today's behaviour so a widening is deliberate.
- `tests/durations.json` has no entry for `test_empty_config_store.py`. The runner
  flags it; `--record` re-times the whole tree, which this row did not do.
