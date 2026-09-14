# TASK-237 — V4 review, round 2

> Criteria: `perry/evidence/2026-09/TASK-237-spec.md`, as amended by Amendments
> 2026-09-14 (1)–(9), plus the note "old Perry projects are not kept compatible
> (user)". Round 2 is Amendment (9): F1, R2 and R3.
>
> Under review: the merge `7523f1fe` (round 2: `b42fa3d7`, `3be743d3`,
> `5f239061`) and the PMO's record `c9301eca`, at the pinned base `c9301eca`.
>
> **Result: PASS.** F1 is closed. Every gated write refused in every
> non-installed shape and every root source I tried: 0 new files, and
> `installed` stayed false. That held for `--dry-run` too. An installed
> project's writes behave exactly as they did before round 2, and every
> documented start still installs. R2 places the row in its own section in the
> store, the list, the printed board and a held file. R3's six lines are true.
> Round 1's clean measurements hold, byte for byte against the pre-round-2
> tools. 21 of 22 mutations reddened. The one green is the equivalent S3 that
> round 2 already recorded. The suite's only reds are the two
> `test_contract_key_parity` tests TASK-335 is fixing.

---

## 0. Base check

| | |
|---|---|
| branch | `worktree-agent-a0043aa197ba59e30` |
| arrived at | `583f024f97d8736468e61469e2667de85eeb56c4` |
| tree | clean (`git status --short` printed nothing) |
| `git merge-base --is-ancestor c9301eca HEAD` | **exit 1**: stale |
| action | `git merge --ff-only c9301eca`, on this branch only |
| re-asserted | exit 0; HEAD `c9301eca` |

**Method.** Every measurement ran on `git archive` copies under my scratchpad:
- `c9301eca` ("base");
- `7523f1fe^1` ("pre-r2": main just before the round-2 merge);
- `b7c89276` ("pre-TASK-237").

The tools always ran from the archive, with `PERRY_HOME` set to it, `HOME`
pointed at an empty directory and every `PERRY_*` variable unset. The only run
in the worktree is the suite (§ 7). The scripts sit in the scratchpad and are
not committed.

**One method defect of my own, found and removed.** The scratchpad is shared
with earlier agents of this session, and my first extraction landed in a
directory that already existed. `diff -rq` against a fresh extraction found one
stale file in it, a `perry/BOARD.md` that `c9301eca` does not carry
(`git cat-file -e c9301eca:perry/BOARD.md` exits 128). Only my first
installed-project matrix copied `perry/` from that tree, so only that run saw a
held board. I discarded every first-pass number and re-ran everything below on
freshly created, uniquely named extractions. The first-pass results matched
wherever the stale file could not reach.

## 1. F1 is closed

### 1.1 The inputs

Five non-installed shapes, each a fresh directory per run:

| shape | contents |
|---|---|
| empty | nothing |
| `BOARD.md`-only | aiMark's `perry/BOARD.md` and `perry/OKR.md`, copied to the root |
| store without `.perry/` | a one-record `tasks.jsonl` at the root |
| **aiMark copy** | `aimark/.perry/config.md` (declares `State root: perry`), `aimark/perry/BOARD.md`, `aimark/perry/OKR.md` |
| **root layout** | aiMark's `config.md` with its `State root` line removed, and its board and OKR at the root |

The aiMark files were read with a copy and nothing else; no file under
`/Users/bytedance/proj/aimark` or any other project was written or run
against.

### 1.2 Every gated write, by shape

I ran the full list of writes in `bin/`, derived from each tool's
`--describe --json`:
- `perry-task`: the 27 subcommands whose `writes` is non-empty (27 plus the 4
  `READ_ONLY_COMMANDS` equals the 31 entries of `COMMANDS`);
- `perry-tasks`: `write`, `risks-write`, `intake-write`, `asks-write`,
  `cadence-write` (`--from-board`);
- `perry-okr`: `write --from-file`, `migrate-ids`;
- `perry-goals`: `commit`, `link`.

Each ran with realistic arguments, once real and once with `--dry-run` wherever
declared: 71 runs per shape. `find` was taken before and after, and `perry-state
--section installed` after.

| shape | runs | exit 1 with the gate's text | new, removed or changed paths | `installed` after | traceback |
|---|---|---|---|---|---|
| empty | 71 | 71 | 0 | false | 0 |
| `BOARD.md`-only | 71 | 71 | 0 | false | 0 |
| store without `.perry/` | 71 | 71 | 0 | false | 0 |
| aiMark copy | 71 | 71 | 0 | false | 0 |
| root layout | 71 | 71 | 0 | false | 0 |

That is **355 of 355**, `--dry-run` included (160 dry runs).

### 1.3 The root sources

The same 71 writes on the aiMark copy, by each way a tool finds its root:

| root source | refused | new paths |
|---|---|---|
| `--root <dir>` | 71 / 71 | 0 |
| no `--root`, cwd = the directory (F1 as filed) | 71 / 71 | 0 |
| `PERRY_PROJECT=<dir>`, cwd elsewhere | 71 / 71 | 0 |
| no `--root`, cwd = its `perry/` subdirectory | 71 / 71 | 0 |

### 1.4 The hunt for a write path that skips the gate

Base and pre-r2 side by side, with `ask` (and `asks-write` or `commit --dry-run`
where named):

| input | base | pre-r2 |
|---|---|---|
| aiMark copy nested at `vendor/old/` inside an installed project, cwd inside it, no `--root` | `ask` refuses at the gate, 0 files | exit 0, writes `vendor/old/{asks.jsonl,journal/,.perry/events.jsonl}` |
| the same, `perry-tasks asks-write` | walks to the installed ancestor, refuses "no BOARD.md", 0 files | the same |
| the same, `--root vendor/old` | refuses at the gate | exit 0, writes there |
| installed project, cwd `src/deep`, no `--root` | `ask` and `perry-goals commit --dry-run` refuse at the gate | `ask` installs a second project in `src/deep`; goals refuses "no OKR.md" |
| installed project, cwd = its state root `perry/` | refuses at the gate | exit 0, creates `perry/.perry/` and `perry/asks.jsonl` |
| `--root ""` with `PERRY_PROJECT` at an empty dir | exit 2 at parse ("given an empty value") | the same |
| `--root <installed>` with `PERRY_PROJECT` at an empty dir | writes the installed project; the empty dir untouched | the same |
| `.perry` a symlink, beside a `BOARD.md` | `installed: false` | the same |

**No write path skipped the gate.** `perry-task` and `perry-goals` resolve
their project root from `--root`, `$PERRY_PROJECT` or the cwd without walking
(`bin/perry-task:8869`). So from inside a subdirectory of an installed project
they now refuse, where pre-r2 installed a second project in that
subdirectory. That is a refusal where there used to be a wrong write, not a
regression.

One shape reads `installed: true` and writes at its root:
`.perry/config.md`, `perry/BOARD.md` and a stray empty `tasks.jsonl` at the
root. That is Amendment (7)'s predicate (`.perry/` plus a canonical store under
the state root), and pre-r2 does the same. It is not a gate bypass.

### 1.5 `perry-decide`, `perry-knowledge`, the renders and `perry-config`

- **The renders** (`perry-tasks render`/`risks-`/`intake-`/`asks-`/`cadence-render
  --write` and `perry-okr render --write`) are not gated. Real and dry, they
  exit 1 ("no BOARD.md") or 2 (no store) on all five shapes, with 0 files
  touched.
- **`perry-decide` and `perry-knowledge` are not gated, and they create no
  store, journal or event log.** Run in sequence on the empty,
  `BOARD.md`-only and aiMark shapes:
  - `bootstrap` creates `decisions/`;
  - `new` ×2 writes `decisions/ADR-00{1,2}-*.md`, and `status` and `supersede`
    edit them;
  - `promote --kind knowledge` writes `knowledge/t/s.md`.

  No `.jsonl`, no `journal/`, no `.perry/events.jsonl`, and `installed` stays
  false. They are outside Amendment (9)'s scope, which is canonical stores,
  journal entries and event logs.
  - On the aiMark copy these files land at the project root, not under the
    `perry/` that `config.md` declares.
  - The pre-TASK-237 tools (`b7c89276`) produce the identical file list on the
    same shape.
  - Round 2 did not touch either tool.
  - So it predates this row. It is the accepted incompatibility of an
    un-upgraded project.
- **`perry-config`.** On an empty dir and on the aiMark copy:
  - `unset` and `untrack` refuse ("is not declared; nothing was written");
  - `set` creates `.perry/config.jsonl` and installs, and a following `ask`
    then lands.
  - On the aiMark copy, `set 'State root' perry` makes the next write land
    under `perry/`. `set 'Document language' English` alone makes it land at
    the root. The gate's pre-ADR-019 refusal names `set 'State root' <dir>`,
    so a user who follows it gets the first outcome.

## 2. The gate does not break installed projects or starts

### 2.1 Every `perry-task` write on a copy of this repository's state

This is a board-less copy of `c9301eca`'s `.perry/` and `perry/`, with
`evidence/` symlinked. Each of the 27 writes ran in a fresh copy, after its
prerequisites, once with base tools and once with pre-r2 tools. Snapshotted:
- every store's digest and record count;
- event-log lines and the last event's name;
- the journal's total size;
- every `BOARD.md` before and after.

| write | exit (base = pre-r2) | stores changed (records before→after) | event | journal | `BOARD.md` before / after |
|---|---|---|---|---|---|
| add (`--unlinked`) | 0 | tasks 434→435, linkage 258→259 | `add` | grew | none / none |
| start, track, stage, next, retitle, summary, rung (V4), evidence, prioritize, status, depends, design-link, done, drop | 0 each | tasks 434→434 | its own name | grew | none / none |
| ask | 0 | asks 33→34 | `ask` | grew | none / none |
| answer (the minted ask) | 0 | asks 34→34 | `answer` | grew | none / none |
| cadence-add | 0 | cadence none→1 | `cadence-add` | grew | none / none |
| cadence-done (CAD-001) | 0 | cadence 1→1 | `cadence-done` | grew | none / none |
| risk-add | 0 | risks 4→5 | `risk-add` | grew | none / none |
| risk-clear (RX-003) | 0 | risks 4→4 | `risk-clear` | grew | none / none |
| intake | 0 | intake 0→1 | `intake` | grew | none / none |
| route | 0 | intake 1→1, tasks 434→435 | `route` | grew | none / none |
| resolve-intake | 0 | intake 1→1 | `resolve-intake` | grew | none / none |
| intake-sweep | 0 | intake 1→0 | `intake-sweep` | grew | none / none |
| purge (a `VFRTWOPRB-001` probe, added `--unlinked` and dropped first) | 0 | tasks 435→434 | `purge` | grew | none / none |
| risk-migrate | 1 | — | — | — | none / none: "`## Top risks` is already a table (4 row(s))" |

**All 27 are identical between base and pre-r2** in exit, stores changed with
counts, event, journal growth and board presence. The gate's text appears in
none.

**Two of my first inputs were wrong, and both trees agreed on each:** `add`
without `--unlinked` (this project has a `linkage.jsonl`), and a `purge` whose
prerequisite `add` lacked it.

### 2.2 Every documented start, executed from its doc

I found the starts by grepping `SKILL.md`, `work/`, `goals/`, `decide/`,
`reference/` and `modes/` for `bin/perry-config" set`. That found 17 lines in
five files. `SKILL.md` carries none and points at `reference/first-run.md`.

Each run of lines executed in a fresh empty directory, with its placeholders
filled (`English`, `single`, `perry`, `x`) and `--root` pointed at the
directory. Then `perry-task add`, `perry-task ask` and `perry-tasks board` ran.

| start (doc lines) | steps: exit | refusals | `installed` before → after doc → after writes | add / ask / board | `BOARD.md` created |
|---|---|---|---|---|---|
| `reference/first-run.md` 61–64 | 0 ×4 | 0 | false → true → true | 0 / 0 / 0 | no |
| `work/reference/bootstrap.md` 18–21 | 0 ×4 | 0 | false → true → true | 0 / 0 / 0 | no |
| `goals/reference/setup.md` 12–15 | 0 ×4 | 0 | false → true → true | 0 / 0 / 0 | no |
| `decide/SKILL.md` 157–160 | 0 ×4 | 0 | false → true → true | 0 / 0 / 0 | no |
| `reference/adoption.md` 212 | 0 | 0 | false → true → true | 0 / 0 / 0 | no |

**`perry-config set` and `track` still install.** See § 1.5, and mutation P1 in
§ 6, which gates `set` and reddens four named tests.

## 3. R2

### 3.1 The reproduction

An installed, board-less project: a config store (`State root: perry`, track
`main`), an event log, and `perry/tasks.jsonl` holding `TASK-001` (P1) and
`TASK-9500` (group `Open — 工程线`, no priority). Each write ran in a fresh
copy, with base and with pre-r2.

| write on `TASK-9500` | pre-r2 | base | store records of `TASK-9500` | `perry-task list` | `perry-tasks board` places it under | `BOARD.md` created |
|---|---|---|---|---|---|---|
| `next`, `status`, `retitle`, `rung`, `evidence`, `depends` | **exit 1, traceback, `KeyError: 'Open — 工程线'`** | **exit 0, no traceback** | 1 | listed | `## Open — 工程线` | no |
| `start`, `summary` | 0 | 0 | 1 | listed | `## Open — 工程线` | no |
| `prioritize --priority P2` | 0 | 0 | 1 | listed | `## P2` (the group moves, as it should) | no |
| `done`, `drop` | 0 | 0 | 1 | not listed (terminal) | not printed | no |
| `track --track main`, `design-link DESIGN-001` | 1 (already on `main`; no design doc) | the same | 1 | listed | unchanged | no |

### 3.2 Edge groups, and the file a project still holds

Each group ran through the six writes that used to raise, in three board states:
- board-less;
- the printed board held as `perry/BOARD.md`;
- a six-column **narrow** held board with `## P1` and `## <group>`.

For each run I read the store, the list, the printed board and the held file.

| group | runs | exit 0, no traceback | store records | listed | printed board | held file | narrow board: column added in |
|---|---|---|---|---|---|---|---|
| `Open — 工程线` | 18 | 18 | 1 each | once | `## Open — 工程线` | `## Open — 工程线` | the group's section only (8 vs `P1`'s 7 pipes, for `status`, `rung`, `depends`) |
| `p1` | 18 | 18 | 1 each | once | `## p1` | `## p1` | `## p1` only |
| `P10` | 18 | 18 | 1 each | once | `## P10` | `## P10` | `## P10` only |
| `P3` | 18 | 18 | 1 each | once | `## P3` | `## P3` | `## P3` only |

On pre-r2 the same `p1` and `P10` runs raised 36 tracebacks.

**A group named like a register section (`Cadence`, `Intake`) is outside R2's
input set**, because those are declared headings. All 36 such runs exit 1
cleanly, with no traceback, nothing written, and the row still listed once. The
refusals name the register or say the row "is not a row on the board". The
pre-r2 tools give identical exits and messages, so this predates round 2.

**The choice is consistent with `perry-tasks board`.** In every case above, the
section `perry-tasks board` prints the row under is the section the write
edited in the held file.

## 4. R3: the six prose lines, read on `c9301eca`

| file:line | now reads | true of a board-less project? |
|---|---|---|
| `work/state/PROJECT_STATE_TEMPLATE.md:4` | the live board is `tasks.jsonl` and its register stores (`perry-tasks board` prints them) | yes: `board` prints the task, ask, risk, cadence and intake stores (§ 5) |
| `work/state/PROJECT_STATE_TEMPLATE.md:36` | a carry-over is an open task in `tasks.jsonl` (`perry-task list` shows it) | yes |
| `work/state/evidence_TEMPLATE.md:4` | the task record's `evidence` field (`perry-task evidence`) points here | yes: `evidence` writes that field (§ 2.1) |
| `work/state/journal_TEMPLATE.md:20` | the task record carries only enough to know it is open | yes |
| `work/reference/subcommands.md:637` | the event is appended afterwards, and a board file a project still holds is re-rendered from the store | yes: § 2.1 creates no board; § 3.2's held files are rewritten by the write |
| `schema/README.md:254` | markdown still read by a consumer is `phase/`, `decisions/` and a `BOARD.md` held before its import | yes: every register has a store, and `OKR.md`'s store is named two lines above |

## 5. No regression to round 1's clean measurements

This ran on the board-less copy of this repository's state (§ 2.1's copy, with
no writes), with base tools and pre-r2 tools. Outputs were compared after
replacing the root path and `generated_at`-style clocks.

| surface | exit | bytes | equal to pre-r2 | contract · `installed` |
|---|---|---|---|---|
| `perry-task list --json` | 0 | 510,955 | **yes** | `perry-task/list/2.3` · true |
| `perry-task list --all --limit 0 --json` | 0 | 2,421,398 | **yes** | 2.3 · true |
| `perry-task asks --all --json` | 0 | 111,504 | **yes** | `perry-asks/list/1.3` · true |
| `perry-task events --json` | 0 | 26,561 | **yes** | `perry-events/list/1.4` · true |
| `perry-goals list --json` | 0 | 49,309 | **yes** | `perry-goals/list/3.3` · true |
| `perry-decide list --json` | 0 | 9,692 | **yes** | `perry-decide/list/2.2` · true |
| `perry-knowledge list --json` | 0 | 4,430 | **yes** | `perry-knowledge/list/1.3` · true |
| `perry-state --json` | 0 | 172,594 | **yes** | · true |
| `perry-tasks board` | 0 | 147,996 | **yes** | — |

- **The six contracts' versions and `semantics` are unchanged by round 2.** Every
  payload is byte-equal to pre-r2's. Round 2's diff (`git diff 7523f1fe^1
  7523f1fe --stat`) touches no contract page, no payload emitter's output, no
  `viewer/parsers.py` and no `schema/state-schema.json`.
- **`perry-tasks board` is cell-whole and never opens `BOARD.md`.**
  - I planted a garbage `BOARD.md` at the state root and at the project root,
    each carrying a marker and a forged row. The output was byte-identical to
    the run without them, and neither the marker nor the forged id appeared.
  - I also ran a parser independent of `perry_store` over the output against
    `tasks.jsonl`. It found all 94 open tasks, each exactly once, with 0 title
    or next-action mismatches. TASK-391's 2,218 B next action is whole.
- **`perry-lint --root`** on the board-less copy exits 0 with no
  `[missing-file]`, with base and with pre-r2.
- **`installed` across the shapes**, on seven surfaces: `perry-state --json`,
  `list`, `asks`, `events`, `goals list`, `decide list` and `knowledge list`.

  | directory | all seven | `board` |
  |---|---|---|
  | empty | false, exit 0 | 1, 0 B |
  | `BOARD.md` only | false, exit 0 | 1, 0 B |
  | `tasks.jsonl` only, no `.perry/` | false, exit 0 | 1, 0 B |
  | `.perry/` + `tasks.jsonl` | true, exit 0 | 0 |
  | config only | true, exit 0 | 0 |

## 6. Mutations

**Method.** Three fresh `git archive c9301eca` copies. For each mutation:
- the file was asserted byte-equal to `git show c9301eca:<path>` (saved from the
  worktree) first;
- the anchor was asserted to occur exactly once. The two line-anchored
  mutations instead asserted that the anchor sits inside the named
  subcommand's declaration;
- the edit was made, every `__pycache__` removed, and the run waited 1.1 s;
- the named modules ran concurrently through `python3 -m unittest` from
  `tests/`, and every `FAIL:`/`ERROR:` id was collected;
- the file was restored from the `git show` copy, the caches were cleared, the
  run waited 1.1 s again, and the restore was asserted byte-equal.

**The unmutated control** was 8 modules and 205 tests, 0 red. **Every restore
compared equal.** The anchors are mine. The dry-run mutations, R2c and V1–V5
are not in round 2's table.

All tests named below are in `test_a_write_refuses_where_nothing_is_installed`
unless another module is named.

| # | guard | mutation (file:line) | red: named tests | result |
|---|---|---|---|---|
| G1 | the gate: the predicate is asked | `if P.installed(root):` → `if True:` (`bin/lib/__init__.py:603`) | 4: `test_each_write_refuses_and_writes_nothing`, `test_dry_run_gets_the_same_refusal`, `test_a_pre_adr_019_project_is_told_to_write_the_config_store_first`, `test_the_reviewers_reproduction_run_from_the_directory` | RED |
| G2 | the gate: the scope decision is honoured | `if not write_needs_installed(writes):` → `if True:` (`bin/lib/__init__.py:599`) | the same 4 | RED |
| S2 | the canonical-store clause | `Path(path).name in stores` → `False` (`bin/lib/__init__.py:571`) | 2: `test_each_write_refuses_and_writes_nothing`, `test_dry_run_gets_the_same_refusal` | RED |
| S3 | the journal and event-log clauses | both dropped, the store clause kept (`bin/lib/__init__.py:571`) | **none** | **GREEN**: equivalent (below) |
| M1 | the pre-ADR-019 instruction | `legacy = False` (`bin/lib/__init__.py:611`) | 1: `test_a_pre_adr_019_project_is_told_to_write_the_config_store_first` | RED |
| C1 | `perry-task`'s call | the call → `pass` (`bin/perry-task:8875`) | 4: as G1 | RED |
| C2 | `perry-tasks`' call | → `pass` (`bin/perry-tasks:2056`) | 2: as S2 | RED |
| C3 | `perry_md_store`'s call (`perry-okr`) | → `pass` (`bin/perry_md_store.py:1448`) | 2: as S2 | RED |
| C4 | `perry-goals`' call | → `pass` (`bin/perry-goals:3323`) | 2: as S2 | RED |
| D1 | `perry-task`'s dry-run path | call wrapped in `if not getattr(args, 'dry_run', False):` (`bin/perry-task:8875`) | 1: `test_dry_run_gets_the_same_refusal` | RED |
| D2 | `perry-tasks`' dry-run path | call wrapped in `if '--dry-run' not in flags:` (`bin/perry-tasks:2056`) | 1: `test_dry_run_gets_the_same_refusal` | RED |
| D3 | `perry-okr`'s dry-run path | call wrapped in `if '--dry-run' not in seen:` (`bin/perry_md_store.py:1448`) | 1: `test_dry_run_gets_the_same_refusal` | RED |
| D4 | `perry-goals`' dry-run path | call wrapped in `if not args.dry_run:` (`bin/perry-goals:3323`) | 1: `test_dry_run_gets_the_same_refusal` | RED |
| R2a | R2: no `KeyError` | `section()` back to `PRIORITY_RE[priority].match(line)` (`bin/perry-task:752`) | 2: `test_the_write_lands_in_the_tasks_own_section`, `test_a_narrow_held_board_is_widened_in_the_tasks_own_section` | RED |
| R2c | R2: the heading must equal the group | `line.startswith("## ") and line[3:].strip() == priority` → `line.startswith("## ")` (`bin/perry-task:753`) | 1: `test_the_write_lands_in_the_tasks_own_section` | RED |
| V1 | coverage: an import drops out of scope | `asks-write`'s `writes` → `[]` (`bin/perry-tasks:1930`) | 3: `test_the_table_covers_every_declared_write`, `test_each_write_refuses_and_writes_nothing`, `test_dry_run_gets_the_same_refusal` | RED |
| V2 | coverage: a goals write drops out of scope | the call made conditional on `args.cmd == "commit"`, so `link` is ungated (`bin/perry-goals:3323`) | 2: as S2 | RED |
| V3 | coverage: an import declares a non-store | `cadence-write`'s `writes` → `["BOARD.md"]` (`bin/perry-tasks:1944`) | 3: as V1 | RED |
| V4 | coverage: a `perry-task` write declares nothing | `ask`'s `writes` → `[]` (`bin/perry-task:8689`) | 3: `test_the_table_covers_every_declared_write` (its floor of 27), `test_a_pre_adr_019_project_is_told_to_write_the_config_store_first`, `test_the_reviewers_reproduction_run_from_the_directory` | RED |
| V5 | coverage: a `perry-task` write declares a non-store | `ask`'s `writes` → `["BOARD.md"]` (`bin/perry-task:8689`) | 4: as G1 | RED |
| P1 | the start is not gated | `perry-config`'s `write` refuses when the directory is not installed (`bin/perry-config:117`) | 4: `test_perry_config_set_installs_an_empty_directory`, `test_perry_config_track_installs_an_empty_directory`, `test_a_pre_adr_019_project_writes_once_its_store_declares_the_root`; `test_starts_write_the_config_store_first.test_the_documented_lines_run_and_end_installed` | RED |

**S3 is equivalent, by enumeration, on `--describe --json` output:**
- all 27 `perry-task` writes declare `tasks.jsonl` next to `journal/` and
  `.perry/events.jsonl`;
- the five `perry-tasks` imports and both `perry-okr` store writes declare a
  canonical store and nothing else;
- `perry-goals`' named scope carries `okr.jsonl` and `linkage.jsonl`.

No writer that exists today is gated only by the journal or event-log clause,
so no test can redden S3. This matches round 2's record.

**What V4 shows about the coverage guard.** The gate's scope is each
subcommand's declared `writes`. Removing one declaration is caught, but only by
the anti-vacuity floor of 27 in `test_the_table_covers_every_declared_write`,
plus the two tests that run `ask` by name.
- **No test binds `COMMANDS − READ_ONLY_COMMANDS` to a non-empty `writes`.**
  The one test that derives writers that way, `test_cadence.py:642`, checks
  event classification instead.
- **So a new write subcommand that declared no `writes` would be ungated
  without reddening anything.** None exists today: 27 declared writes plus 4
  reads is all 31 of `COMMANDS`.
- This is a future evasion shape, not a present defect. By `review.md § 1` it
  is not this round's to widen.

## 7. The suite

I ran `bash tests/run` in the worktree at `c9301eca`, in the foreground, with
nothing else running. `git status --porcelain` was empty before and after.

| modules · tests | red modules · red tests | tree guard |
|---|---|---|
| **139 · 3,974** | **1 · 2** | "nothing … moved" |

**The reds, by id, are the expected two and no other:**
- `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`
- `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness`

TASK-335 is fixing both. `test_resume`, red in round 1, is green on this base.
No other red appeared, so nothing needed re-running alone. The harness's
durations notes name `test_a_write_refuses_where_nothing_is_installed.py` and
`test_contract_page_snippets.py` as missing from `tests/durations.json`. Those
are sort-order notes and gate nothing.

## 8. Findings

**No FAIL and no new ROW.** Each defect I looked for either did not reproduce
or is already on the record:

### Checked and not a finding

- **Ungated `perry-decide` and `perry-knowledge` writes (§ 1.5).** On a
  non-installed directory they write ADR files and a knowledge card, and on the
  aiMark copy they land at the root instead of under `perry/`.
  - They create no canonical store, journal or event log.
  - `installed` stays false.
  - The pre-TASK-237 tools write the identical files on the same shape, and
    round 2 did not touch either tool.
  - Outside Amendment (9)'s scope. It is the accepted incompatibility of an
    un-upgraded project (the user's note).
- **A new write subcommand that declares no `writes` would be ungated (§ 6,
  V4).** No such subcommand exists. A future evasion shape, not a present
  defect.
- **Tasks grouped `Cadence` or `Intake` (§ 3.2).** They refuse cleanly with
  register-worded messages, identically before round 2. Those are declared
  headings, so R2's input set does not include them.
- **Subdirectory runs (§ 1.4).** `perry-task` and `perry-goals` run from inside
  an installed project's subdirectory now refuse. Pre-r2 installed a second
  project there. A wrong write became a refusal.
- **`.perry/config.md` plus a stray root `tasks.jsonl` (§ 1.4).** It reads
  installed, and a write lands at the root. That is Amendment (7)'s predicate,
  unchanged by round 2.

### Known items, re-read and not understated

- **R1** (accepted by the user).
- **R4** (predates TASK-237).
- **R5–R8, R11.**
- **`add --group <new group>`** naming `BOARD.md` in its refusal (round 2
  § 9), not re-measured.
- **The two `test_contract_key_parity` reds.**

Nothing I ran touches R4's carry-forward or R5–R8/R11, so I have no evidence
that the record understates them.

## What I did not check

- **The consumer projects themselves.** I ran copies of aiMark's
  `.perry/config.md`, `perry/BOARD.md` and `perry/OKR.md` only. Gimegime-pmo's
  files were not read. The "root layout" shape was built from aiMark's files,
  so a real root-layout config may differ.
- **Concurrency**, the viewer, a Windows path, a localized board heading for
  R2, and a malformed store on a non-installed directory.
- **Writes outside `bin/`.** I found `bin/` writers by `--describe` and by
  grepping for write primitives. Among the ungated tools, that grep found
  writes only in `perry-config`, `perry-decide`, `perry-knowledge` and
  `perry-restore-check`, and the last writes a caller's mutation file, not
  project state. Nothing under `viewer/` was checked for writes.
- **`add --group <new group>`**, R4's carry-forward case, and the cadence
  import of consumer boards.
- **The board's readability judgement** that the spec's header leaves open.
- **Every `perry-task` write's argument edge cases** on the gated shapes. Each
  ran with one realistic argument vector, plus `--dry-run`. The gate runs
  before any handler reads an id or a flag (`bin/perry-task:8875`), and C1/D1
  redden when that call moves or becomes conditional.

=== VERDICT ===
task: TASK-237
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-237-spec.md
checked: F1 on 5 non-installed shapes (empty, BOARD.md-only, store without .perry/, aiMark copy, root layout) x 71 gated writes each (27 perry-task, 5 perry-tasks imports, 2 perry-okr, 2 perry-goals, real and --dry-run) = 355 refusals, 0 files, installed false; the aiMark copy again by cwd, PERRY_PROJECT and subdirectory (71 each); 8 root-resolution hunts against pre-r2; renders, perry-decide, perry-knowledge and perry-config on the same shapes; 27 perry-task writes on a board-less copy of this repository identical to pre-r2; 5 documented starts executed from their docs; R2 on 4 undeclared groups x 3 board states x 6 writes plus the terminal and moving writes, and 2 register-named groups; R3's six lines; 9 read payloads byte-equal to pre-r2, board independent of BOARD.md and cell-whole over 94 open tasks, perry-lint --root clean, installed on 5 shapes x 8 surfaces; 22 mutations, 21 red and S3 equivalent; suite 139 modules, 3974 tests, the two test_contract_key_parity reds only
not-checked: the consumer projects themselves and Gimegime-pmo's real files; concurrency, the viewer, Windows paths, localized headings, malformed stores; writes outside bin/; add --group into a new group, R4's case, the cadence import; the board's readability judgement
proof: bin/lib/__init__.py:603 asks parsers.installed before any gated write, and bin/perry-task:8875, bin/perry-tasks:2056, bin/perry_md_store.py:1448 and bin/perry-goals:3323 call it before their lock and dispatch; mutations G1, C1-C4 and D1-D4 each redden tests in tests/test_a_write_refuses_where_nothing_is_installed.py, and bin/perry-task:753 matches the task's own heading, R2a and R2c redden
=== END VERDICT ===
