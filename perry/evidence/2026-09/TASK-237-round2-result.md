# TASK-237 round 2 — result: a write refuses where nothing is installed; R2 lands in its group; R3 prose

> Scope: `TASK-237-spec.md § Amendment 2026-09-14 (9)`, against the V4 round 1
> verdict `TASK-237-v4-review.md` (F1, R2, R3).
>
> `schema/state-schema.json`, `ARCHITECTURE.md`, `viewer/parsers.py` (the
> `installed` predicate) and every real store (`perry/*.jsonl`,
> `.perry/events.jsonl`, `.perry/config.jsonl`) are unchanged on this branch. No
> published payload's keys or versions changed. No id was minted and no row
> opened. `/Users/bytedance/proj/aimark` was only copied from (two files); no
> other project was read or written.
>
> **Delivered, all three parts. One design point is flagged for the PMO, not a
> stop (§ 1.3): the check lives in one function, reached from four dispatch
> boundaries, because no single call site is reached by every write and by no
> read.**
>
> - **F1.** `lib.refuse_write_unless_installed` is the one gate. On the aiMark
>   copy, an empty directory and a `BOARD.md`-only directory, the five named
>   writes refuse 30 of 30 runs (real and `--dry-run`), with 0 new files and
>   `installed` still `false`. At `c62dfe6c` 20 of those 30 exited 0, and the
>   14 real runs among them installed a project.
> - **R2.** Placement per C7, not refusal (§ 5). The six writes that raised
>   `KeyError` now land in the task's own `## <group>` section, the one
>   `perry-tasks board` prints it under, with and without a held board.
> - **R3.** The six lines, prose only.
> - **Found on the way:** the refusal's first text handed back `perry-config
>   set` without the root (`test_handed_back_root` reddened; fixed), and
>   mutation R2b stayed green until the R2 test got a narrow held board (§ 7).

---

## 0. Base check

| | |
|---|---|
| branch | `worktree-agent-a2129327bdadf9cfe` |
| arrived at | `583f024f97d8736468e61469e2667de85eeb56c4` |
| tree | clean (`git status --porcelain` printed nothing) |
| `git merge-base --is-ancestor c62dfe6c HEAD` | **exit 1**: stale |
| action | `git merge --ff-only c62dfe6c`, this branch only |
| re-asserted | exit 0; HEAD `c62dfe6c895e35baf7c653007e623edd1a5aeae7` |

Commits on this branch, oldest first:

| commit | what |
|---|---|
| `b42fa3d7` | the gate, its four calls, R2's `Board.section`, R3's six lines, eight fixtures installed, the new test module |
| `3be743d3` | R2 on a narrow held board (mutation R2b was green without it) |
| next commit | this file only |

**Method.** Every measurement ran in scratch copies with `PERRY_HOME` set to the
tools tree under test, `HOME` pointed at an empty scratch directory and every
`PERRY_*` variable unset. Three trees: this branch, `git archive c62dfe6c`
("base") and `git archive b7c89276` ("pre-TASK-237"). The scripts sit in the
scratchpad and are not committed.

## 1. The write-path enumeration and where the check lives

### 1.1 Every `bin/` tool, by what it writes

Enumerated by grepping every file under `bin/` for the write primitives
(`write_atomic`, `write_text`, `write_bytes`, `open(…, "a"/"w")`, `os.replace`,
`mkdir`), then reading each hit's caller.

| tool | subcommands that write | what they write | in scope? |
|---|---|---|---|
| `perry-task` | the 27 `--describe` declares with `writes` | `tasks.jsonl` and the register stores, `linkage.jsonl`, the journal, `.perry/events.jsonl`; the transaction marker inside `commit()` | **gated** |
| `perry-tasks` | `write`, `risks-write`, `intake-write`, `asks-write`, `cadence-write` (all `--from-board`) | one canonical store each | **gated** |
| `perry-tasks` | `render`, `risks-render`, `intake-render`, `asks-render`, `cadence-render` (`--write`) | `BOARD.md` only | not a store, journal or event: not gated |
| `perry-okr` (`perry_md_store.main`) | `write --from-file`, `migrate-ids` | `okr.jsonl` | **gated** |
| `perry-okr` | `render --write` | `OKR.md` only | not gated |
| `perry-goals` | `commit`, `link` | `okr.jsonl` / `linkage.jsonl`, `OKR.md`, `.perry/events.jsonl` | **gated** |
| `perry-config` | `set`, `unset`, `track`, `untrack` | `.perry/config.jsonl` only | **the exception**: this write is the start |
| `perry-decide` | `bootstrap`, `new`, `supersede`, `status` | `decisions/ADR-*.md`, `design/` directories; no event (`bin/perry-decide:260`) | not a store, journal or event: not gated |
| `perry-knowledge` | `promote` | a knowledge card and `knowledge/INDEX.md` | not gated |
| `perry-restore-check` | — | the caller's file under a mutation harness, not project state | not gated |
| every other `bin/` tool | none | — | — |

### 1.2 The gate

`bin/lib/__init__.py`, after `resolve_project_root`:

- `declared_writes(surface, sub)`: the `writes` list a `SURFACE` declares.
- `write_needs_installed(writes)`: yes when a path names a canonical store (by
  file name, read from `parsers.canonical_store_names()`, so from `§ claims`),
  the journal or `.perry/events.jsonl`. `.perry/config.jsonl`, `BOARD.md` and
  `OKR.md` alone do not.
- `refuse_write_unless_installed(project_root, writes, refused)`: when the
  write needs it and `parsers.installed(project_root)` is false, it raises the
  tool's own `Refused`. The predicate is called, never restated.

The four calls, each at its tool's dispatch boundary and before its lock:

| tool | where | scope passed |
|---|---|---|
| `perry-task` | `main`, right after the project and state root resolve, before the track register, lock, board and dispatch | `declared_writes(SURFACE, args.cmd)` |
| `perry-tasks` | `main`'s lock block, before `project_lock` | `declared_writes(SURFACE, cmd)`, after the `--register` alias rewrite |
| `perry_md_store` | `main`'s lock block, before `project_lock` | `declared_writes(face, cmd)` |
| `perry-goals` | `main`'s writing branch, before `project_lock` | `("okr.jsonl", "linkage.jsonl", ".perry/events.jsonl")`: the tool declares no `SURFACE` |

**`--dry-run` gets the same answer** because every call runs before dispatch,
and every dry-run is decided inside the handlers.

**The refusal** names the root, the two conditions of `schema/README.md §
installed`, and "Nothing was written". When `.perry/config.md` exists at the
root it adds that the project predates ADR-019, and hands back `"$PERRY_HOME/
bin/perry-config" set 'State root' <dir> --root <root>` with a pointer to
`reference/first-run.md § Writing the config store`. Otherwise it hands back
the `Document language` set line, also with the root.

### 1.3 Flagged for the PMO: "one place"

The amendment asks for the check in one place that every write path reaches.
**The check is in one place:** one function, one predicate call, one message.
It is reached from four call sites, one per writing tool. No subcommand carries
a copy.

A single call site in `bin/` that every write reaches would have to be one
all four tools share. The only one is `lib.project_lock`. Reads reach it too:
`perry-task list/events/asks`, `perry-tasks build/verify/diff` and `perry-config
show` all take the lock. Gating there would refuse reads on a non-installed
directory, where each read payload must exit 0 with `installed: false`
(Amendment (4)). Or each caller would pass a "this is a write" flag, which puts
the decision back at the call.

**No write path fails to reach the gate**, so this is not a stop. Two things
keep the four call sites from drifting:
- `test_the_table_covers_every_declared_write` derives the gated set from each
  tool's `--describe` and from `perry-goals`' `COMMANDS`;
- mutations C1–C5 (§ 7) remove or empty each call and redden a named test.

If the PMO reads "one place" as one call site, the lock-with-a-flag shape is
the only one I found, and it is the per-call decision the amendment rules out.

## 2. F1 matrices

### 2.1 The aiMark copy, an empty directory and a `BOARD.md`-only directory

**Inputs.** `aimark/.perry/config.md` (declares `State root: perry`) and
`aimark/perry/BOARD.md` (26 table lines) were copied into a scratch skeleton.
Each cell below is a **fresh** copy of its shape. The write ran from inside the
directory with no `--root` and `PERRY_PROJECT` unset. `find` was taken before
and after, and `perry-state --section installed` was read both times (the
pre-TASK-237 tree has no section, so its `--json` was read).

Cell = exit · new paths · `installed` before→after. `next` names `TASK-001`.
The argv: `ask --needed x`; `add --title … --priority P1 --deliverable d
--verification v --rung V2 --summary … --next n`; `next TASK-001 --next …`;
`risk-add --title …`; `cadence-add --title … --frequency weekly`.

**aiMark copy** (`.perry/config.md` + `perry/BOARD.md`):

| write | this branch | base `c62dfe6c` | pre-TASK-237 `b7c89276` |
|---|---|---|---|
| `ask` | **1 · 0 · false→false** | 0 · 6 (`asks.jsonl`, `journal/…/2026-09-14.md`, `.perry/events.jsonl` at the root) · false→**true** | 1 · 0 · false→false |
| `add` | **1 · 0 · false→false** | 0 · 5 (`tasks.jsonl`, journal, `.perry/events.jsonl`) · false→**true** | 1 · 0 · false→false |
| `next` | **1 · 0 · false→false** | 1 · 0 · false→false ("TASK-001 is not a task") | 1 · 0 · false→false |
| `risk-add` | **1 · 0 · false→false** | 0 · 6 (`risks.jsonl`, journal, events) · false→**true** | 1 · 0 · false→false |
| `cadence-add` | **1 · 0 · false→false** | 0 · 6 (`cadence.jsonl`, journal, events) · false→**true** | 1 · 0 · false→false |
| each with `--dry-run` | **1 · 0 ×5** | 0 · 0 ×4, `next` 1 | 1 · 0 ×5 |

**Empty directory:**

| write | this branch | base | pre-TASK-237 |
|---|---|---|---|
| `ask`, `add`, `risk-add`, `cadence-add` | **1 · 0 · false→false** ×4 | 0 · 6–7 (`.perry/`, events, journal, the store) · false→**true** ×4 | 1 · 0 · false→false ×4 |
| `next` | **1 · 0** | 1 · 0 (not a task) | 1 · 0 |
| each with `--dry-run` | **1 · 0 ×5** | 0 · 0 ×4, `next` 1 | 1 · 0 ×5 |

**`BOARD.md`-only directory** (aiMark's board copied to the root):

| write | this branch | base | pre-TASK-237 |
|---|---|---|---|
| `ask`, `add`, `cadence-add` | **1 · 0 · false→false** ×3 | 0 · 6–7 · false→**true** ×3 | 0 · 6–7 · **true→true** ×3 |
| `risk-add` | **1 · 0** | 1 · 0 (board risks are bullets: "run `risk-migrate`") | 1 · 0 (the same) |
| `next` | **1 · 0** | 1 · 0 (not a task) | 1 · 0 |
| each with `--dry-run` | **1 · 0 ×5** | 0 · 0 ×3, 1 ×2 | 0 · 0 ×3, 1 ×2 |

**Totals.** This branch refuses **30 of 30** runs (3 shapes × 5 writes × real
and dry-run), with 0 new paths, `installed` false throughout, no traceback,
and the gate's text on stderr. Every refusal on the aiMark copy carries the
pre-ADR-019 sentence and the `'State root' <dir> --root <root>` line. The
pre-TASK-237 tree **refused all 20** on the aiMark copy and the empty directory.
It wrote on the `BOARD.md`-only directory, which it counted as installed then;
Amendment (4) item 2 removed that. Base wrote on all three shapes.

### 2.2 The other gated writers, on an empty and a `BOARD.md`-only directory

With `--root`; the `BOARD.md`-only shape also holds a one-line `OKR.md`.

| run | this branch, both shapes | base, empty | base, `BOARD.md`-only |
|---|---|---|---|
| `perry-tasks write --from-board` | **1 · gate · 0 new** | 1 (no `BOARD.md`) | **0 · wrote `tasks.jsonl`**, installed still false |
| `… write --from-board --dry-run` | **1 · gate** | 1 | 0 · 0 new |
| `perry-tasks risks-write`, `intake-write` | **1 · gate** | 1 | 1 (a refusal of its own) |
| `perry-tasks asks-write --from-board` | **1 · gate** | 1 | **0 · wrote `asks.jsonl`** |
| `perry-tasks cadence-write --from-board --dry-run` | **1 · gate** | 1 | 0 · 0 new |
| `perry-okr write --from-file` | **1 · gate** | 2 (no `OKR.md`) | **0 · wrote `okr.jsonl`** |
| `perry-okr migrate-ids` | **1 · gate** | 2 | 2 |
| `perry-goals commit --track main --promise smoke` (and `--dry-run`) | **1 · gate** | 1 (no `OKR.md`) | 1 (no `## Commitments`) |
| `perry-goals link --unlinked TASK-001` | **1 · gate** | 1 (no phase) | 1 (no phase) |
| `perry-tasks build` (a read) | 1 on empty (no `BOARD.md`), 0 on board-only; **no gate** | 1 | 0 |
| `perry-task list --json` (a read) | 0, `installed: false`; **no gate** | 0 | 0 |
| `perry-config set 'Document language' English` | **0**, creates `.perry/config.jsonl`, installed **true** | 0, true | 0, true |

Three base imports wrote a canonical store into a directory that was not
installed. Each now refuses.

## 3. Installed-project write matrix

Every `perry-task` subcommand whose `--describe` `writes` is non-empty: 27. Each
ran on a **fresh copy of this repository's state** (`.perry/` and `perry/`,
with `perry/evidence` symlinked for the evidence checks). Its prerequisites
ran first, in the same copy. Snapshotted: every store's digest and record
count, the event log's appended lines, the journal's size, and any `BOARD.md`.
Run once with base tools and once with this branch's.

| write | exit (base / branch) | stores changed (records before→after) | event | journal | `BOARD.md` |
|---|---|---|---|---|---|
| add | 0 / 0 | tasks 434→435, linkage 258→259 | `add` | grew | none |
| start, stage, track, next, retitle, summary, rung, evidence, prioritize, status, depends, design-link, done, drop | 0 / 0 each | tasks 435→435 | its own name | grew | none |
| ask | 0 / 0 | asks 33→34 | `ask` | grew | none |
| answer | 0 / 0 | asks 34→34 | `answer` | grew | none |
| risk-add | 0 / 0 | risks 4→5 | `risk-add` | grew | none |
| risk-clear (RX-003) | 0 / 0 | risks 4→4 | `risk-clear` | grew | none |
| intake | 0 / 0 | intake 0→1 | `intake` | grew | none |
| route | 0 / 0 | tasks 434→435, intake 1→1 | `route` | grew | none |
| resolve-intake | 0 / 0 | intake 1→1 | `resolve-intake` | grew | none |
| intake-sweep | 0 / 0 | intake 1→0 | `intake-sweep` | grew | none |
| purge (a `RTWOPURGE-001` probe, added and dropped first) | 0 / 0 | tasks 435→434 | `purge` | grew | none |
| cadence-add | 0 / 0 | cadence none→1 | `cadence-add` | grew | none |
| cadence-done (CAD-001) | 0 / 0 | cadence 1→1 | `cadence-done` | grew | none |
| risk-migrate | 1 / 1 | — | — | — | none: "`## Top risks` is already a table (4 row(s))", as 3a and 3c record |

**All 27 rows are identical between base and branch** in exit, stores changed
with counts, event names, journal growth and `BOARD.md` presence. 26 land their
record, event and journal line; `risk-migrate` refuses in both. The gate's text
appears in no run.

**Three first attempts were my own inputs, and both trees agreed on each.**
- `rung --rung V2` refused, because the probe was filed at V2.
- `purge` of a `TASK-441` probe refused: an evidence file names that id.
- `purge` of a `QQVFOURX-001` probe refused: the V4 review names that id.

`RTWOPURGE` was grepped for over `perry/` and `.perry/` first: 0 hits.

## 4. Starts

The start sections are the guard's own `WRITERS` table in
`tests/test_starts_write_the_config_store_first.py`, read from the tree under
test. From each section, every line invoking `"$PERRY_HOME/bin/perry-*"` ran in
a fresh empty directory with `--root` pointed at it. The placeholders were
filled with `English`, `single`, `perry`, and `x` for any other. Host detection
and the update check were skipped: they read the machine, not the project.
Then two first writes ran: `perry-task add` and `perry-task ask`.

| start | steps run (tool:exit) | `installed` before → after the doc → after the first writes | refusals |
|---|---|---|---|
| `reference/first-run.md § Writing the config store` | config:0 ×4, task:0 ×2 | false → true → true | 0 |
| `work/reference/bootstrap.md` | config:0 ×4, task:0 ×2 | false → true → true | 0 |
| `goals/reference/setup.md § init` | config:0 ×4, lint:0, task:0 ×2 | false → true → true | 0 |
| `decide/SKILL.md § init` | config:0 ×4, decide:0 (`bootstrap`), task:0 ×2 | false → true → true | 0 |
| `reference/adoption.md` | lint:0 (`--claims`), config:0, task:0 ×2 | false → true → true | 0 |

The same table at base is identical, step for step.

## 5. R2

### 5.1 The reproduction, first

This is an installed, board-less project: a config store with `State root:
perry`, `.perry/events.jsonl`, and `perry/tasks.jsonl` holding `TASK-001` (P1)
and `TASK-9500` (group `Open — 工程线`, no priority). Each task-row write ran on
a fresh copy, then `perry-tasks board` ran. It was then repeated with the file
`perry-tasks board` prints held at `perry/BOARD.md`.

| write on `TASK-9500` | base, board-less | base, held board | branch, both |
|---|---|---|---|
| `next`, `status`, `retitle`, `rung`, `evidence`, `depends` | **exit 1, traceback, `KeyError: 'Open — 工程线'`** at `section` (`bin/perry-task:738`), store unchanged | the same | **exit 0, no traceback**; the store field holds the new value; `group` unchanged |
| `start`, `summary`, `prioritize --priority P2` | 0 | 0 | 0 (prioritize moves the group to `P2`, as it should) |
| `done`, `drop` | 0 | 0 | 0; the row leaves the board (terminal) |
| `add --group 'Open — 工程线'` | 0 | 0 | 0 |
| `perry-tasks board` after each | the open row under `## Open — 工程线` | the same | the same |

That is 12 tracebacks at base and 0 of 24 runs on this branch.

### 5.2 The choice: placement per C7, not refusal

- **`perry-tasks board` already places the task.** `DECLARED_BOARD_CHOICES`
  "undeclared group" prints an open task whose group matches no declared
  heading under `## <group>`, after the last declared task section. A refusal
  would call a row unwritable that the board shows, and that `start`,
  `summary`, `prioritize`, `done`, `drop` and `add --group` already write. That
  is the "a message that was false, about rows the same tool had just printed"
  defect `Board._section_tables` records.
- **The defect is a lookup, not a policy.** `find()` answers `table["priority"]
  or table["heading"]`, so a row under any non-P heading hands its heading to
  `section()`, which indexed `PRIORITY_RE` by it. It is not board-less-only:
  the held-board column fails identically. A hand-kept board with a `## Open —
  投资线` section (the shape `Board.task_tables` documents on a real project)
  crashed on the same six writes.
- **The fix is one match.** When `priority` is not `P0`/`P1`/`P2`, `section()`
  matches `line.startswith("## ") and line[3:].strip() == priority`. That is
  exactly how `_section_tables` reads the heading, so the section found is the
  one `find()` found the row in. On a board-less project that is C7's section.
- **Nothing is written in a new place.** The write edits the row in the section
  it already sits in, and the store's `group` is unchanged. The board prints
  the row where it printed it before.

**Left as it was:** `add --group Someday` on a board-less project, into a group
no task holds yet, still refuses with "BOARD.md has no `## Someday` section".
It exits 1 cleanly and writes nothing, but it names a file that does not exist.
§ 9 names it.

## 6. R3

Each line was re-located by content at `c62dfe6c`. Prose only; no heading,
table or placeholder changed.

| file:line | before | after |
|---|---|---|
| `work/state/PROJECT_STATE_TEMPLATE.md:4` | The live work board lives in `BOARD.md`; this file is for cross-phase state. | The live work board is `tasks.jsonl` and its register stores (`perry-tasks board` prints them); this file is for cross-phase state. |
| `work/state/PROJECT_STATE_TEMPLATE.md:36` | … Each carry-over should also exist in `BOARD.md`. | … Each carry-over should also be an open task in `tasks.jsonl` (`perry-task list` shows it). |
| `work/state/evidence_TEMPLATE.md:4` | The BOARD.md `Evidence` field points here. … not in the board. | The task record's `evidence` field (`perry-task evidence`) points here. … not in the record. |
| `work/state/journal_TEMPLATE.md:20` | … BOARD.md only carries enough to know it's open. | … the task record only carries enough to know it's open. |
| `work/reference/subcommands.md:637` | `BOARD.md` is rendered afterwards and the event is appended and reported if either derived-surface write fails. | The event is appended afterwards, and a board file a project still holds is re-rendered from the store; either derived-surface write is reported if it fails. |
| `schema/README.md:254` | … which, for the four registers of `BOARD.md` that have no store, is still several things. | … which, now that every register of the board has a store, is `phase/`, `decisions/` and a `BOARD.md` a project still holds before its import. |

**The first wording of `subcommands.md:637` tripped a guard.** It named
`BOARD.md` as the subject of "is re-rendered", and
`test_procedures_call_the_tool` R1 read the step as one that writes a
`BOARD.md` row without naming the tool. The line now says "a board file". The
guard and `perry-lint --templates` are green.

## 7. Tests and the mutation table

### 7.1 Tests

**New: `tests/test_a_write_refuses_where_nothing_is_installed.py`, 11 tests.**

| class · test | holds |
|---|---|
| `TestEveryWriteRefusesWhereNothingIsInstalled.test_the_table_covers_every_declared_write` | the gated table equals `perry-task`'s 27 declared writes, `perry-tasks`' and `perry-okr`'s `.jsonl` writes, and `perry-goals`' non-read `COMMANDS` |
| `….test_each_write_refuses_and_writes_nothing` | every gated write × {empty, `BOARD.md`-only, pre-ADR-019}: exit 1, the gate's text, no traceback, the tree byte-identical, `installed` false |
| `….test_dry_run_gets_the_same_refusal` | the same with `--dry-run` wherever it is declared (at least 81 cases) |
| `….test_a_pre_adr_019_project_is_told_to_write_the_config_store_first` | the pre-ADR-019 sentence and `perry-config" set 'State root'` with `--root`; the empty shape gets no `config.md` sentence |
| `….test_the_reviewers_reproduction_run_from_the_directory` | F1 as filed: subprocess, cwd inside the copy, no `--root`, no `PERRY_*` |
| `TestTheStartStillInstalls.test_perry_config_set_installs_an_empty_directory` | `set` exits 0 and installs, and an `add` then lands |
| `….test_perry_config_track_installs_an_empty_directory` | the same for `track` |
| `….test_a_pre_adr_019_project_writes_once_its_store_declares_the_root` | after `set 'State root' perry`, `ask` exits 0 and lands under `perry/`, not at the root |
| `….test_a_read_is_not_gated` | `list`/`asks`/`events --json` exit 0 with `installed: false`; `perry-tasks build` exits 0 |
| `TestAWriteInAnUndeclaredGroup.test_the_write_lands_in_the_tasks_own_section` | the six writes × {board-less, held printed board}: exit 0, no traceback, the field written, the group and the board section unchanged |
| `….test_a_narrow_held_board_is_widened_in_the_tasks_own_section` | `rung` and `depends` on a six-column held board: the column goes into the task's section and not into `## P1` |

**Eight fixtures installed, no expectation changed.** Each built `.perry/config.md`
(read by nothing since ADR-019) with a root `BOARD.md`. That is the shape
Amendment (4) does not count as installed, so its first import or write now
refuses. Each writes the config store through `tests/config_store.write_config`
instead, the way a start does:
- `test_store_is_the_write_target.Project`, which `test_store_is_canonical`,
  `test_summary_is_asked_for` and `test_task_summary` also import;
- `test_v5_signoff.Project`, `test_id_families.Project`,
  `test_duplicate_ids_are_refused.Project`, `test_board_render.Project.fixture`;
- `test_work_modes.TestVerificationSeesToolClosedWork.project`;
- `test_knowledge_promotion.Base.project`, only when the fixture seeds a board;
- `test_linkage_writer.test_no_store_at_all`, whose project stops being
  installed once its only store is deleted.

**How they were attributed.** Before any fixture changed, the full suite at the
uncommitted code had 15 of 138 modules and 128 tests red. The 13 new modules,
run alone:
- at this code, 13 of 13 red, 125 of 376 tests;
- at `git archive c62dfe6c`, 13 modules green.

Their failure text carried the gate's sentence in every module that reached
it. The rest were three: `test_handed_back_root`, which caught the refusal
handing back `perry-config set` without the root (fixed, count still 72);
`test_procedures_call_the_tool` on the R3 line (§ 6); and three `from tests.`
imports that fail only under a bare `unittest` from `tests/`, and that under the
runner met the same gate. After the fixes, the 13 modules ran green, 376 tests.

### 7.2 Mutations

**Method.** `mutate.py` ran on `git archive 3be743d3` under the scratchpad. For
each mutation:
- the anchor was asserted to occur exactly once, and the file was asserted
  equal to `git show 3be743d3:<path>` first;
- the edit was made, every `__pycache__` was removed, and the run waited 1.1 s;
- eight modules ran through `tests/parallel --ids`:
  `test_a_write_refuses_where_nothing_is_installed`,
  `test_starts_write_the_config_store_first`, `test_board_less_reads_and_writes`,
  `test_installed_is_one_predicate`, `test_store_is_the_write_target`,
  `test_cadence_store`, `test_handed_back_root` and
  `test_board_from_declarations`;
- the file was restored from `git show 3be743d3:<path>`, run in the worktree,
  and asserted byte-equal.

When `tests/parallel` withheld the ids file (it does so when its counts
disagree, which many subtest failures in one module cause), the red tests were
named by `python3 -m unittest <module>`, one module at a time; those rows say
so.

The unmutated control: **160 tests, 0 red.** Every restore compared equal. All
test names below are in `test_a_write_refuses_where_nothing_is_installed`
unless another module is named.

| # | guard | mutation (file) | red: named tests | result |
|---|---|---|---|---|
| G1 | the installed check on the write path | `if P.installed(root): return` → `if True: return` (`bin/lib/__init__.py`) | 4, via unittest: `test_each_write_refuses_and_writes_nothing`, `test_dry_run_gets_the_same_refusal`, `test_a_pre_adr_019_project_is_told_to_write_the_config_store_first`, `test_the_reviewers_reproduction_run_from_the_directory` | RED |
| G2 | the start is not gated | `perry-config set` calls the gate with `["tasks.jsonl"]` (`bin/perry-config`) | 3: `test_perry_config_set_installs_an_empty_directory`, `test_a_pre_adr_019_project_writes_once_its_store_declares_the_root`; `test_starts_write_the_config_store_first.test_the_documented_lines_run_and_end_installed` | RED |
| R2 | no `KeyError` | `section()` back to `PRIORITY_RE[priority].match(line)` (`bin/perry-task`) | 2: `test_the_write_lands_in_the_tasks_own_section`, `test_a_narrow_held_board_is_widened_in_the_tasks_own_section` | RED |
| R2b | the heading match finds the row's own section | `== priority` → `!= priority` (`bin/perry-task`) | 1: `test_a_narrow_held_board_is_widened_in_the_tasks_own_section` | RED (green at `b42fa3d7`, before that test existed) |
| D1 | `--dry-run` passes the gate | `perry-task`'s call wrapped in `if not args.dry_run:` | 1, via unittest: `test_dry_run_gets_the_same_refusal` | RED |
| C1 | `perry-task`'s call | the call → `pass` | 4, via unittest: the four of G1 | RED |
| C2 | `perry-tasks`' call | the call → `pass` | 2: `test_each_write_refuses_and_writes_nothing`, `test_dry_run_gets_the_same_refusal` | RED |
| C3 | `perry_md_store`'s call | the call → `pass` | the same 2 | RED |
| C4 | `perry-goals`' call | the call → `pass` | the same 2 | RED |
| C5 | `perry-goals`' named scope | the tuple → `()` | the same 2 | RED |
| S1 | the scope decision | `write_needs_installed` → `return False` | 4, via unittest: the four of G1 | RED |
| S2 | the canonical-store clause | `Path(path).name in stores` → `False` | 2: `test_each_write_refuses_and_writes_nothing`, `test_dry_run_gets_the_same_refusal` | RED |
| S3 | the journal and event-log clauses | both dropped, the store clause kept | **none** | **GREEN**: equivalent, § 9 |
| S4 | the declared scope is read | `declared_writes` → `return []` | 4, via unittest: the four of G1 | RED |
| M1 | the pre-ADR-019 instruction | `legacy = False` | 1: `test_a_pre_adr_019_project_is_told_to_write_the_config_store_first` | RED |

**S3 is equivalent, by enumeration.** Every subcommand the gate covers declares
a canonical store alongside `journal/` and `.perry/events.jsonl`:
- `perry-task`'s 27 each declare `tasks.jsonl`;
- `perry-tasks`' five and `perry-okr`'s two declare a store and nothing else;
- `perry-goals`' named scope carries `okr.jsonl` and `linkage.jsonl`.

So removing the two clauses changes no answer for any writer that exists.
**No test can redden it** without a writer that appends only the journal or an
event. None exists, so none was invented.

**Two first runs are recorded, not hidden.** At `b42fa3d7`:
- G1, D1, C1, S1 and S4 printed "1 of 8 MODULE(S) red" and wrote no ids file.
  They were red, unnamed. The fallback above names them at `3be743d3`.
- R2b was green, a real gap: every R2 board carried all fifteen columns. That
  is why `3be743d3` exists.

## 8. Suite totals on the final commit

**The final run is the commit that adds this file, and its totals are not in
it.** The dispatch requires `tests/run` in the foreground on the final commit,
after this file is committed. Writing that run's totals here would need one
more commit, which would then be the final commit, and the suite would not
have run on it. So the foreground run's totals are reported with its SHA in the
hand-back message, beside this file.

**The triage recorded here** ran on `3be743d3`, the code this file describes,
through `python3 tests/parallel --ids`:

| modules · tests | red modules · red tests |
|---|---|
| **139 · 3,974** | **2 · 3** |

- **Against base (138 · 3,963):** +1 module and +11 tests, which is
  `test_a_write_refuses_where_nothing_is_installed`.
- **The reds, by id, are the standing three and no other:**
  - `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`
  - `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness`
  - `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`

No other red appeared, so nothing needed re-running alone at that point. The
runner prints "not in durations.json" for the new module, as it already does
at base for `test_contract_page_snippets.py`. It is a sort-order note and gates
nothing.

**Earlier on this branch** the suite was not green, and § 7.1 records how each
red was attributed. At the uncommitted code, before any fixture changed, it
stood at 15 of 138 modules and 128 tests red.

## 9. Rows this work names (none minted)

- **`add --group <new group>` on a board-less project names a file that does
  not exist.** "BOARD.md has no `## Someday` section" is a clean exit 1 with
  nothing written. It is R2's neighbour, and V4 round 1 recorded it under R2;
  this round did not change it.
- **The journal and event-log clauses of the gate's scope are equivalent today**
  (mutation S3, § 7.2). Every declared writer in scope also names a canonical
  store, so dropping those clauses changes no answer. They are kept because the
  amendment scopes the journal and `.perry/events.jsonl` explicitly, and a
  future writer that appends only an event would need them. No test can make
  S3 red until such a writer exists.
- **The one-place reading** (§ 1.3), for the PMO.
- **R1 now reaches writes as well as reads.** A Gimegime-pmo-shaped project
  (`.perry/config.md` and a root `BOARD.md`) already read `installed: false`.
  Its writes and imports now refuse too, and each says to write the config
  store first. That follows Amendments (4), (7) and (9), and V4 round 1 already
  named it for the user.

## What I did not check

- **The consumer projects themselves.** Only copies of aiMark's `.perry/config.md`
  and `perry/BOARD.md` ran. Nothing under `/Users/bytedance/proj/aimark` or
  `/Users/bytedance/proj/Gimegime-pmo` was written or run against.
- **`perry-decide` and `perry-knowledge` on a non-installed directory.** They are
  outside the amendment's scope (§ 1.1), are not gated, and were not measured.
  A `decide new` there may still write an ADR file.
- **`perry-tasks *-render --write` and `perry-okr render --write` on a
  non-installed directory.** They write `BOARD.md` / `OKR.md` only, are not
  gated, and were not run there.
- **`PERRY_PROJECT` as the root source.** Roots came from `--root`, and from the
  cwd in the reviewer's reproduction.
- **Concurrency**, the viewer, a localized board heading for R2, and a
  malformed store on a non-installed directory.
- **R4, R5–R8, R11 and the standing reds.** Unchanged by this round.
