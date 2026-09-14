# TASK-237 — V4 review over deliverables 1, 2 and 3

> Criteria: `perry/evidence/2026-09/TASK-237-spec.md`, the original spec as
> amended by Amendments 2026-09-14 (1)–(8), read in order. Byte-identity was
> dropped by USER-932. The user's consent covers deleting `BOARD.md`, the
> `files[id=board]` and cadence schema edits, and the V5-signed hand-off text.
>
> Under review: the merges `9549626e`, `cb88d848`, `47dce04a`, `161c927c`,
> `0ec65094`, `0f1ed007`, `13522369` and the PMO's `9839d110`, at the pinned
> base `112526f5`.
>
> **Result: FAIL, on one finding (F1).** The deliverables do what their
> results claim on this repository's state, and every guard I mutated
> reddened except one pre-existing carry-forward (R4). But 3a's board-less
> write path now writes into a pre-ADR-019 consumer project whose Perry state
> sits under a state root only its `.perry/config.md` declares. That write
> used to refuse. It now succeeds at exit 0 and installs a second, empty
> project at the root, and every surface then reports that project. The shape
> is on disk today at `aimark`.

---

## 0. Base check

| | |
|---|---|
| branch | `worktree-agent-aaefe4ca93f9c84b6` |
| arrived at | `583f024f97d8736468e61469e2667de85eeb56c4` |
| tree | clean (`git status --porcelain` printed nothing) |
| `git merge-base --is-ancestor 112526f5 HEAD` | **exit 1**: stale |
| action | `git merge --ff-only 112526f5`, on this branch only |
| re-asserted | exit 0; HEAD `112526f5ac59d9389806b76a84117d2b6cd7e51b` |

**Method for everything below.** Every measurement ran on `git archive
112526f5` copies under my scratchpad, never in the worktree. The tools always
ran from the archive, with `PERRY_HOME` set to it, `HOME` empty and every
`PERRY_*` variable unset. Project copies hold the archive's `.perry/` and
`perry/`, with `evidence/` symlinked. The only run in the worktree is the suite
(§ 7), with nothing writing to it. The pre-TASK-237 comparison tree is `git
archive d04197a3`, the first parent of `9549626e`. The scripts sit in the
scratchpad and are not committed.

## 1. `perry-tasks board` (D1, Amendment (2) as amended by (4))

### 1.1 Cell-whole, checked against the stores directly

This check does not reuse the test module. I wrote a checker that imports
nothing from `perry_store` or `viewer/tables`. It has its own column-to-field
map for all five registers, its own splitter for unescaped `|`, and its own
grouping of open tasks by `P0`/`P1`/`P2`. It parses the board's output and
compares it with the JSONL stores.

| run | exit | bytes | records / rows printed | cells compared / unequal | problems |
|---|---|---|---|---|---|
| this repository's state, no `BOARD.md` | 0 | 154,661 | 131 / 131 (94 open tasks, 33 asks, 4 risks) | 1,624 / 0 | 0 |
| the same with a garbage `BOARD.md` | 0 | same bytes as absent | — | — | 0 |
| edge fixture (below) | 0 | 156,652 | 140 / 140 | 1,708 / 0 | 0 |

- **Every id appears exactly once** as a row id, in its declared section.
- **Every header equals the declared column list.** That is 15 columns for the
  task tables, 6 for asks, 4 for risks, 7 for cadence and 3 for intake.
- **The longest open next action is whole.** It is TASK-391's, 2,218 B, and
  the task is `not_started`.
- **The title is `# Board — Perry`**, and `{{` appears 0 times.

**The edge fixture** is a board-less copy with rows written through the tools:
- two cadence rows, one with a `|` in its title;
- two intake rows, one of them resolved;
- a risk with `|` and backticks.

Four tasks were planted by hand with the groups `p1`, `P10`, `""` (with no
integer `order`) and `P0`.

What the render did with them:
- `p1`, `P10` and `(no group)` are printed under their own `##` sections and
  named on stderr.
- The planted `P0` task lands under P0.
- `## Intake` is printed after the task sections with both rows.
- No record went missing or landed in the wrong section, and no column was
  dropped.

### 1.2 It never opens `BOARD.md`: proven by an audit hook and a marker

`perry-tasks board` ran in-process under a `sys.addaudithook` that logged every
`open`, `os.listdir`/`os.scandir` and subprocess event. It ran twice. The first
run had a `BOARD.md` at the state root and another at the project root, both
carrying a marker string and forged rows. The second run had neither.

- **The data files opened, identical in both runs:** `.perry/config.jsonl`,
  `perry/{tasks,asks,risks,intake}.jsonl`, `schema/state-schema.json`,
  `work/state/BOARD_TEMPLATE.md` and the tool itself. `cadence.jsonl` was
  absent, so it was not opened.
- **Nothing else was touched.** No open event names a `BOARD.md`; the one
  `BOARD` hit is the template. No subprocess ran.
- **The marker never reached stdout.**
- **The output did not change.** Stdout was byte-identical with the planted
  files and without them. It was also byte-identical to the real executable's
  output.

Mutation B1 (§ 6) puts one read of the file back, and two named tests redden.

### 1.3 It refuses where nothing is installed

`board` exits 1 with 0 B on stdout for every non-installed shape in § 2.

## 2. Detection and `installed` (D2, Amendments (4), (6), (7))

Every surface ran with `--root <dir>`. Each cell below is `installed`/exit.
"walk" is `perry-state --json` run from `<dir>/deep/er` with no `--root`. "lint"
is `perry-lint --root <dir>`'s exit.

| directory | expected | `perry-state --json` | list | asks | events | goals | decide | knowledge | `--section installed` | board | walk | lint |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| empty | false | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | 1, 0 B | false | 0 |
| `BOARD.md` only | false | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | 1, 0 B | false | 0 |
| `tasks.jsonl` only, no `.perry/` | false | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | 1, 0 B | false | 0 |
| `.perry/` + `tasks.jsonl` | true | true/0 | true/0 | true/0 | true/0 | true/0 | true/0 | true/0 | true/0 | 0, 1,382 B | true, walks to `proj` | 0 |
| config only | true | true/0 | true/0 | true/0 | true/0 | true/0 | true/0 | true/0 | true/0 | 0, 1,097 B | true, walks to `proj` | 0 |
| *extra:* `.perry/` + `BOARD.md` | — | false everywhere, board 1 | | | | | | | | | | |
| *extra:* `.perry` a regular file + `tasks.jsonl` | — | false everywhere, board 1 | | | | | | | | | | |
| *extra:* `.perry/events.jsonl` only | — | false everywhere, board 1 | | | | | | | | | | |
| *extra:* `.perry/` + `perry/tasks.jsonl`, no state root declared | — | false everywhere, board 1 | | | | | | | | | | |
| *extra:* config with `State root: perry` + `perry/tasks.jsonl` | true | true everywhere, board 0, walk resolves the project | | | | | | | | | | |
| *extra:* `.perry/config.md` (State root perry) + `perry/BOARD.md` (**aimark's shape**) | — | false everywhere, board 1 | | | | | | | | | | |
| *extra:* `.perry/config.md` + root `BOARD.md` (**Gimegime-pmo's shape**) | — | false everywhere, board 1 | | | | | | | | | | |

**The surfaces never disagree.** No shape gets two answers from `perry-state`,
the six payloads, `board` and the walk. Mutation I3, which moves `perry-state §
build` back to `configured`, reddens the one test that compares them.

**Every documented start ends `installed: true`.** The check was independent
of the guard test. I read each start section's `"$PERRY_HOME/bin/perry-config"
set` lines out of the pinned docs and executed them in a fresh directory, with
the placeholders `English`, `single` and `perry`.

| start doc | lines | exits | before | after, seven surfaces | board | `BOARD.md` created |
|---|---|---|---|---|---|---|
| `reference/first-run.md` (setup; adopt stage 4) | 4 | 0 ×4 | false | true ×7 | 0 | no |
| `work/reference/bootstrap.md` | 4 | 0 ×4 | false | true ×7 | 0 | no |
| `goals/reference/setup.md` | 4 | 0 ×4 | false | true ×7 | 0 | no |
| `decide/SKILL.md` | 4 | 0 ×4 | false | true ×7 | 0 | no |
| `reference/adoption.md` (stage 3 collision) | 1 | 0 | false | true ×7 | 0 | no |

**`schema/README.md § installed` matches `viewer/parsers.py § installed`.**
Both say: the config store, or `.perry/` as a directory AND a canonical store
under the state root, where the store names are read from `claims[]`. Both
also say that an unsearchable path counts, and that `BOARD.md`, `OKR.md`,
`phase/` and `design/` do not.

**Two shapes that exist on disk read `installed: false`.** They are the two
consumer projects in this checkout's parent directory, and § 8 F1 and R1 are
about them. I listed their files and copied five marker files each into the
scratchpad. Neither project was written.

| project | `.perry/` holds | board | JSONL stores | `.perry/config.jsonl` |
|---|---|---|---|---|
| `aimark` | `config.md` (`State root: perry`), `hook.md`, `adoption/` | `perry/BOARD.md`, 22 table rows | none | none |
| `Gimegime-pmo` | `config.md` (no state root), `hook.md` | root `BOARD.md` | none | none |

## 3. Reads and writes without the file (3a, 3b, 3c)

### 3.1 Every read payload, against the stores directly

This ran on a board-less copy of this repository's state. Each value was
compared with the JSONL, not with a previous payload.

| surface | measured | store |
|---|---|---|
| `perry-task list --all --limit 0 --json` | 434 tasks; 0 mismatches over title, status, owner, next_action, evidence, verification, priority, track, stage, group, depends_on, role, commitment, parent and summary | 434 records |
| `perry-task list --json` | 94 tasks, ids equal to the store's open ids; `bound.open_total` 94 | 94 open |
| `list.risks` | ids RX-003, RX-004; open 2, cleared 2 | 4 records, 2 open |
| `list.asks` / `asks --all` | open 0; `--all` count 33, answered 33, 0 field mismatches over needed/blocks/asked/status | 33, every status `answered …` |
| `list.intake`, `perry-state § intake` | 0 rows | 0 |
| `perry-state § cadence` | count 0 | 0 |
| `perry-state § risks` | count 2, cleared 2 | 2 open, 2 cleared |
| `list.drift` | drift 0, orphaned 0 | — |
| `list.conformance.depends_on_unknown` | `[]` | — |
| `perry-goals list --json` | 0 `linked_task_completion` with `unknown > 0` | — |
| `perry-decide`, `perry-knowledge list` | exit 0, 2.2 / 1.3, installed true | — |
| `perry-lint --root` | **exit 0, 0 errors** | — |
| `perry-diagnose --json --root` | `dangling` `[R5-14]`, 52 `dangling_in_reports` | see below |

**No dangling id is caused by the deletion.** I put the pre-deletion board
(`git show 0f1ed007^1:perry/BOARD.md`) back into the same copy and re-ran. Both
lists are identical, 0 ids on either side only. `R5-14` appears neither in that
board nor in any store.

### 3.2 Every `perry-task` write, record by record

Each of the 27 subcommands `--describe` declares with a `writes` list ran on a
fresh board-less copy. Stores, the event log and the journal were snapshotted
before the command and after it.

| subcommand | exit | record | event | journal | `BOARD.md` created | other records changed |
|---|---|---|---|---|---|---|
| add, start, track, stage, ask, answer, next, cadence-add, cadence-done, risk-add, risk-clear, intake, route, resolve-intake, intake-sweep, retitle, summary, rung, evidence, status, depends, design-link (22) | 0 | the subject only | +1, named | appended (prefix intact) | none | none |
| done, drop, prioritize | 0 | the subject | +1 | appended | none | 27 tasks' `order` renumbered, **identically with a held board and in the pre-TASK-237 tools** (28 there), so predating this row |
| purge (a `QQVFOURX-001` probe, added and dropped first) | 0 | removed | `purge` | +65 B | none | none |
| risk-migrate | 1 | — | — | — | none | refuses: "already a table (4 row(s))", as 3a and 3c record |

**Two first attempts were my own inputs.** `route --track main` is correctly
refused, because `main` is a project-mode track. `purge` of TASK-137 and of a
`ZZPROBE` id is correctly refused, because evidence files cite both ids.

**`cadence-add`/`cadence-done` round-trip.** A board-less `cadence-add` minted
`CAD-001`, and `cadence-done CAD-001 --on 2026-09-15` rewrote only that record.
Two cadence rows, one holding a `|`, print whole on the board (§ 1.1). **I did
not re-run the import** of the two consumer boards' `## Cadence`: that needs
3b's copies of their files, and 3b measured 0 mismatches.

**Carry-forward on a sequence.** Twelve register writes ran in a row
(intake ×3, resolve, ask, answer, ask, risk-clear, risk-add, cadence-add ×2,
cadence-done). Every register store ends equal between a board-less copy and a
held-board copy.

## 4. Contracts

| contract | emitted | newest `semantics` entry = minor | page names the version | keys removed / retyped since `d04197a3` | keys added |
|---|---|---|---|---|---|
| `perry-task/list` | 2.3 | 2.3 `installed` | yes | none / none | `installed` |
| `perry-asks/list` | 1.3 | 1.3 `installed` | yes | none / none | `installed`, `state_root`, `semantics[].version/fields/note` |
| `perry-events/list` | 1.4 | 1.4 `installed` | yes | none / none | `installed` |
| `perry-goals/list` | 3.3 | 3.3 `installed` | yes | none / none | `installed` |
| `perry-decide/list` | 2.2 | 2.2 `installed` | yes | none / none | `installed`, `semantics[]` keys |
| `perry-knowledge/list` | 1.3 | 1.3 `installed` | yes | none / none | `installed`, `semantics[]` keys |

**How the "removed / retyped" column was measured.** Every key path and JSON
type of each payload was flattened twice:
- once from the pre-TASK-237 tools on their own state, with the board present;
- once from the pinned tools on the pinned state, board-less.

No path left and no type changed without a null on one side, so no major was
owed. `asks[].idle` `"—"` → `""` stays a string, and USER-932's answer
accepted it.

**The PMO's prose at `9839d110` is true of the code.**
- `task-list-contract.md` says `perry-tasks board` prints the projection. It
  does, and the `state_root` comment is true (§ 3.1).
- Tracks are written by `perry-config track`, which exists: `track --help`
  shows `--mode`, `--sla`, `--stages`, `--wip` and more.
- `goals-list-contract.md` says a task's status comes from `tasks.jsonl` first.
  `bin/perry-goals:994` calls `lib.task_status_index`, which fills from the
  board's rows and then overwrites them from the store (`bin/lib/__init__.py:1117`),
  so the store wins and a held board's rows sit beneath it.

## 5. Documents

- **`SKILL.md` carries the signed substitution and no other ownership change.**
  `git diff cac46c73 112526f5 -- SKILL.md` shows four changes:
  - the `work` row now reads `tasks.jsonl` + its 4 register stores
    (`perry-tasks board` prints them);
  - the refusal case now reads `goals` writing `tasks.jsonl`;
  - 3d's stated compression ("never an automatic retirement");
  - 3c's R3 `relocate` line.

  The `goals` and `decide` rows, the two other refusal cases and the sign-off
  prose are byte-identical.
- **`ARCHITECTURE.md` matches.** § 6 NN-2 is word for word the text proposed in
  `TASK-237-d3c-result.md § 5.2` and confirmed in § 8. § 5 reads 2.3 and § 4's
  label reads 2.3, and the tool emits 2.3.
- **`BOARD.md` census** over `SKILL.md`, `AGENTS.md`, both READMEs,
  `ARCHITECTURE.md`, `bin/README.md`, `bin/ARCHITECTURE.md`, `work/`, `goals/`,
  `decide/`, `modes/`, `reference/`, `schema/*.md` and `.perry/hook.md`:
  - Every hit is history, a held board ("a project that still holds one"), the
    import verbs, a no-file statement, or a known row (R6, R8).
  - **Six are not framed that way** — four shipped templates and two
    descriptive lines — and they are R3 in § 8.
  - `.perry/hook.md` has no hit.

## 6. Mutations

**Method.** `mutate.py` ran on the scratch copy `m`. For each mutation:
- the anchor string was asserted to occur exactly once in the file;
- the edit was made on the named line;
- every `__pycache__` was removed, and the run waited 1.1 s;
- 16 modules ran through `tests/parallel --ids`, 555 tests;
- the red ids were collected;
- the file was restored from `git show 112526f5:<path>`, run from the worktree,
  and its bytes were asserted equal.

The unmutated control was 555 tests, 0 red. **Every restore compared equal.**
The anchors are mine, chosen independently of the results' mutations.

| # | guard | mutation (file:line) | red: named tests | result |
|---|---|---|---|---|
| R1 | ask store read | `asks=load_register_store(...)` → `asks=None` (`viewer/parsers.py:5258`) | 10: NoBoard and Forged `test_asks_all_is_every_stored_ask`, `test_asks_default_is_the_open_stored_asks`, `test_list_carries_the_stored_risks_asks_and_intake`; Forged `test_no_forged_row_reaches_a_payload`; NoBoard `test_perry_state_carries_the_stored_registers`; Live `test_every_stored_ask_is_listed`; `test_asks_list.TestOnPerrysOwnBoard.test_every_writer_form_row_has_answer_text` | RED |
| R2 | risk store read | `risk_records = None` (`viewer/parsers.py:5220`) | 6: NoBoard and Forged `test_list_carries_…`, `test_perry_state_carries_…`; Forged `test_no_forged_row_reaches_a_payload`; Live `test_every_open_stored_risk_is_listed` | RED |
| R3 | intake store read | `intake=None` (`viewer/parsers.py:5260`) | 2: NoBoard and Forged `test_perry_state_carries_the_stored_registers` | RED |
| R4 | cadence store read | `cadence=None` (`viewer/parsers.py:5261`) | 4: `test_cadence_store` NoBoard and Forged `test_perry_state_carries_every_stored_cell_as_written`, Forged `test_no_forged_row_reaches_a_payload`; `test_cadence.TestOverdueReport.test_a_periodic_row_with_an_unreadable_due_cell_is_a_finding` | RED |
| R5 | ask store read, dependency graph | `records = None` in `ask_register` (`bin/perry-task:7209`) | 3: NoBoard and Forged `test_an_answered_stored_ask_satisfies_its_edge`; Live `test_every_edge_to_a_stored_ask_resolves_as_an_ask` | RED |
| W1 | no writer creates `BOARD.md` | `commit` renders a declared board: `if not getattr(board, "on_disk", True):` → `if False:` (`bin/perry-task:3398`) | 4: `test_board_less_reads_and_writes.TestEveryWriteLandsWithNoBoard.test_each_write_lands_its_record_event_and_journal_line`; `test_cadence_store.TestTheWritesLandInTheStore` ×3 | RED |
| W2 | the same, one level up | `Board.declared` claims `on_disk = True` (`bin/perry-task:729`) | the same 4 | RED |
| I1 | `installed` needs `.perry/` | `if not anchored:` → `if False:` (`viewer/parsers.py:539`) | 4: `test_installed_is_one_predicate` ×3 (`perry_state_answers…`, `every_payload_says…`, `board_refuses…`); `test_explain_typed_tasks.test_a_tasks_jsonl_with_no_dot_perry_is_not_claimed` | RED |
| I2 | `installed` excludes `BOARD.md` | `if configured(root) or (root / 'BOARD.md').exists():` (`viewer/parsers.py:532`) | 8: `MarkdownNoLongerStopsTheWalk` ×5; `test_installed_is_one_predicate` ×3 | RED |
| I3 | one predicate: `perry-state` agrees | `installed = P.configured(perry_root)` (`bin/perry-state:1827`) | 1: `test_installed_is_one_predicate.test_perry_state_answers_by_the_criterion` | RED |
| I4 | the store clause is live | the canonical stores match nothing (`.jsonl` → `.nope`, `viewer/parsers.py:505`) | 9: `test_installed_is_one_predicate` ×3; `test_explain_typed_tasks.test_a_tasks_jsonl_beside_dot_perry_is_claimed`; `test_cadence.TestLinkageBelongsToItsOwnPhase` ×5 | RED |
| B1 | `board` never reads the file | one read of `state_root/BOARD.md` after the store load (`bin/perry-tasks:375`) | 2: `TestTheFileIsNeverRead.test_the_render_never_opens_board_md`, `.test_the_render_reads_only_the_declared_files` | RED |
| B2 | `board` refuses where nothing is installed | `if not P.installed(root):` → `if not True:` (`bin/perry-tasks:356`) | 1: `test_board_refuses_where_nothing_is_installed` | RED |
| S1 | the `semantics` guard | `perry-knowledge/list` 1.3's `fields` gains a name (`bin/perry-knowledge:123`) | 2: `TestAShippedEntryNeverLeaves.test_no_shipped_entry_left_a_payload_or_changed_its_fields`, `.test_every_live_entry_is_recorded` | RED |
| S2 | the same | the 1.3 entry's version becomes 1.4 (`bin/perry-knowledge:123`) | the same 2 | RED |
| C1 | carry-forward of stored non-column fields on a register write | `records_of(board, _ops(), current)` → `records_of(board, _ops(), None)` (`bin/perry-task:2709`) | **none** in 555 tests. Full `tests/parallel` in the archive: 4 of 138 modules and 5 of 3,961 tests red, the same counts as the unmutated full control, which is red for the archive environment | **GREEN** — R4 |

**What C1 is.** The same twelve-write sequence as § 3.2 ran with a mutated copy
of the tools, board-less and with a held board. Every register store is equal to
the unmutated run. So C1 is equivalent for the writes TASK-237 added. The
docstring at `bin/perry-task:2580` gives the case the carry-forward exists
for: a request replaced by hand on a held board, with the count unchanged.
Nothing in the suite builds that case. It predates TASK-237.

## 7. The suite

`env -u PERRY_PROJECT -u PERRY_HOME bash tests/run` ran in the worktree at
`112526f5`, in the foreground. Nothing wrote to the worktree during the run,
and `git status --porcelain` was empty before and after.

| modules · tests | red modules · red tests | tree guard |
|---|---|---|
| **138 · 3,963** | **2 · 3** | "nothing … moved" |

**The reds, by id, are the standing three and no other.**
- `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`
- `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness`
- `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`

No other red appeared, so nothing needed re-running alone. The harness's one
durations complaint is `test_contract_page_snippets.py`, which predates this
row.

## 8. Findings

### F1 — FAIL: a board-less write installs a second project over a consumer whose state root only `.perry/config.md` declares

**Where.** `bin/perry-task:8905–8913`:
- `main` builds `Board(state_root / "BOARD.md")` only when that file exists;
- otherwise any write builds `declared_write_board` over the stores at that
  state root.

Nothing asks whether the directory is installed, or whether its state lives
somewhere else.

**The input.** A copy of `aimark`'s five Perry marker files:
- `.perry/config.md` (`State root: perry`), `.perry/hook.md`;
- `perry/BOARD.md` (22 table rows), `perry/OKR.md`, `perry/PROJECT_STATE.md`.

From that directory, with no `--root`: `perry-task ask --needed "V4 probe?"`.

| | pinned `112526f5` | pre-TASK-237 `d04197a3` |
|---|---|---|
| exit | **0** — `wrote USER-001 (ask) → tasks.jsonl + asks.jsonl + journal + event` | **1** — `refused — no BOARD.md at <dir>/BOARD.md. Task truth is safe in …` |
| files created | `tasks.jsonl`, `asks.jsonl`, `journal/2026-09/2026-09-14.md` and `.perry/events.jsonl`, all at the **project root** | none |
| `perry-state --json` after | `installed: true`, no warning | `installed: false`, "No Perry state found — run /perry for first-time setup." |
| `perry-task list --json` after | installed true, 0 tasks, 1 open ask, `state_root` = the project root | 0 tasks |
| `perry-tasks board` after | exit 0, 1 data row | not a subcommand |
| `perry/BOARD.md` | unchanged, 22 rows, read by nothing | unchanged |

**Why it is a FAIL, by `review.md § 0`.**
- **Question 2: a tool reports a wrong answer with no way to tell.** After one
  ordinary write, every surface reports an installed project with no tasks and
  one ask. The 22-row board under `perry/` is not mentioned anywhere.
- **The one signal disappears with it.** Before the write, the only thing
  pointing the user at setup (which would declare `State root: perry` and
  recover the board) was `installed: false` with "run /perry for first-time
  setup". After it, that signal is gone.
- **aimark reads exactly these surfaces.** Its app detects projects with
  `perry-state --section installed` and draws `perry-tasks board`
  (`2026-09-14-aimark-feedback-task-237.md`), so it would show its own project
  as an empty board.
- **Question 3: the gate is gone.** The refusal that stood between that write
  and this state was removed by 3a.

**Enumerated (rule 1).** The category is a pre-ADR-019 project: `.perry/` with
`config.md`, no config store, and a held `BOARD.md`. Two shapes exist, and
both are on disk:
1. **The state root is declared in `config.md` (`aimark`).** The write lands
   outside the state and splits it: this finding.
2. **The board is at the project root (`Gimegime-pmo`).** The write lands
   beside the board and re-renders it, which is the same bytes and the same
   files as the pre-TASK-237 tools. It then flips `installed` to true. Not a
   write regression: R1.

**What I ran, and what I didn't.** I ran `ask`. The selection at `:8905` is
common to every command outside `READ_ONLY_COMMANDS`, so every write reaches
it. I did not run each write on this shape.

**The record says this population needed measuring.**
- `TASK-237-result.md § 3.2` kept the `BOARD.md` disjunct for exactly these
  projects. It said the disjunct's removal "belongs [in deliverable 3], with
  those projects' state measured first".
- Amendment (4) item 2 says "Stop and report if a project shape Perry supports
  today loses `installed`".
- 3b § 3.1 and 3b′ § 2.3 enumerated fixtures and adoption paths only. 3c lists
  "Another project" as not checked.

### R1 — ROW: `Gimegime-pmo`'s shape went from installed to not installed, and no round measured it

A directory holding `.perry/config.md`, `.perry/hook.md` and a root `BOARD.md`
changed state across this row.
- **Before:** the pre-TASK-237 `perry-state` says `installed: true`.
- **Now:**
  - every surface says `false`;
  - `perry-tasks board` refuses;
  - the standup's first move offers first-time setup.

**Why ROW.** This is the criterion the user wrote in Amendment (4) item 2
("`BOARD.md` alone no longer counts"), applied as written, so I do not grade it
FAIL. The defect is the unmeasured population, named under F1. For the user:
the two consumer projects on disk need `.perry/config.jsonl` written, the
3b′ start, before they read as Perry projects again.

### R2 — ROW: a write on a task in an undeclared group crashes on a board-less project

**The input.** A task whose `group` matches no declared heading. My probe
planted `Open — 工程线`, the kind of project heading
`task-list-contract.md § prioritize` names. Then `perry-task next <id> --next
x` runs.

**Pinned tools:** a traceback, `KeyError: 'Open — 工程线'`. The call chain:
- `bin/perry-task:5228` calls `ensure_columns`;
- `ensure_columns` (`:929`) calls `section`;
- `section` looks up `PRIORITY_RE[priority]` at `:738`, which raises.

It exits 1, and the store is unchanged. The same happens with the file
`perry-tasks board` prints held on disk.

**Pre-TASK-237 tools, held board:** `refused — TASK-9500 is not a row on the
board`.

**Related on a board-less project:**
- `add --group Someday` refuses with "BOARD.md has no `## Someday` section",
  naming a file that does not exist.
- `status`, `prioritize --group` and `add --group` into an undeclared group
  that already holds a task all work.

**Why ROW.** Nothing is written and the failure is loud.

### R3 — ROW: six documentation lines still describe `BOARD.md` as the live board

- `work/state/PROJECT_STATE_TEMPLATE.md:4`: "The live work board lives in
  `BOARD.md`".
- `work/state/PROJECT_STATE_TEMPLATE.md:36`: "Each carry-over should also exist
  in `BOARD.md`", an instruction.
- `work/state/evidence_TEMPLATE.md:4` and `work/state/journal_TEMPLATE.md:20`.
- `work/reference/subcommands.md:637`: `add`'s description says "`BOARD.md` is
  rendered afterwards", unqualified.
- `schema/README.md:254`: "for the four registers of `BOARD.md` that have no
  store". Every register has had a store since 3b.

3c tagged the four templates "template" and left them. They are not in the
known list. Prose, so a row (`review.md § 2`).

### R4 — ROW: the register carry-forward has no test that notices its removal

Mutation C1 (§ 6) stays green over the whole suite. It is equivalent for every
board-less write I ran, and the case it protects is a held board's
hand-replaced intake row. It predates TASK-237 and does not fail this row.

### Checked and not a finding

- **The `order` renumbering** on `done`/`drop`/`prioritize` is identical with a
  held board and in the pre-TASK-237 tools (§ 3.2).
- **Every `perry-diagnose` dangling id** is identical with the pre-deletion
  board restored (§ 3.1).

## What I did not check

- **Every write on F1's shape.** Only `ask` ran. The shared selection line is
  the argument for the rest.
- **The consumer projects themselves.** Only copies of their marker files ran.
  Nothing in either project was written or executed against.
- **The cadence import** of the two consumer boards (3b's measurement), and a
  localized template or board.
- **`--dry-run` writes, concurrency, the viewer, and a malformed store** on a
  board-less project.
- **The readability judgement** the spec's header leaves open: whether the CLI
  render is a good reading surface for a board. It prints whole; I did not
  judge whether it reads well.
- **The prose of every lane doc beyond the `BOARD.md` census**, and whether
  the frontmatter routing still triggers on a host.
- **R5, R6, R7, R8, R11, the P003-O3-KR2 scoring question and the standing
  reds.** Known and recorded; I found nothing that shows the record understates
  them.

=== VERDICT ===
task: TASK-237
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-237-spec.md
checked: board cell-whole over 131 live and 140 fixture records by an independent parser, and never opening the file by audit hook; installed on 12 directory shapes across 9 surfaces plus the walk; 5 documented starts executed from the docs; every read payload against the stores; 27 writes record by record; six contracts' versions, semantics and key paths against d04197a3; SKILL.md against cac46c73; ARCHITECTURE NN-2 and section 5; 16 mutations, 15 red; suite 138 modules, 3963 tests, the standing 3 red; a pre-ADR-019 consumer shape (aimark) with the pinned and the pre-TASK-237 tools
not-checked: every write on the aimark shape beyond ask; the consumer projects themselves (copies of marker files only); the cadence import of consumer boards; dry-run, concurrency, the viewer; the board's readability judgement
proof: bin/perry-task:8905 builds the declared write board whenever no board file sits at the resolved state root and never asks whether the directory is installed, so a write run in a copy of aimark's shape exits 0, installs an empty project at the root and hides its 22-row board from every surface, where the pre-TASK-237 tools refused
=== END VERDICT ===
