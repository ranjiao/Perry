# TASK-237 deliverable 3b′ — result: every start writes the config store first; one `installed` predicate

> Scope: `TASK-237-spec.md § Amendment 2026-09-14 (6) § Deliverable 3b′`,
> which pulls in Amendment (4) items 1 and 2.
>
> `perry/BOARD.md`, `ARCHITECTURE.md`, `.perry/hook.md`,
> `schema/state-schema.json` and the repository's real stores (`perry/*.jsonl`,
> `.perry/events.jsonl`, `.perry/config.jsonl`) are unchanged on this branch. No
> id was minted and no row opened. No other project on disk was read or written.
>
> **Delivered, all four parts, no stop.**
>
> - **Starts.** Every documented start writes `.perry/config.jsonl` first,
>   through `perry-config set`. That covers first-time setup, the `work`
>   bootstrap, `goals init`, `decide init` and every `/perry adopt --only=`
>   subset. No start section names `.perry/config.md`. A guard reads the start
>   sections by heading and **executes** their `perry-config set` lines.
> - **One predicate.** `viewer/parsers.py § installed`: the config store, or any
>   canonical store under the state root. `BOARD.md`, `OKR.md`, `phase/` and
>   `design/` do not count. `perry-state`, all six payloads, `board`, and all
>   nine deliverable-2 sites call it. The criterion is written once, in
>   `schema/README.md § installed`, and each contract cites it.
> - **Six payloads.** `installed` on each, with a minor bump and one `semantics`
>   entry apiece:
>   - `perry-task/list` 2.2, `perry-asks/list` 1.2, `perry-events/list` 1.3;
>   - `perry-goals/list` 3.2, `perry-decide/list` 2.1, `perry-knowledge/list` 1.2.
>
>   The asks exit-code text is reconciled.
> - **`board` refusal.** `perry-tasks board` exits 1 on a non-installed
>   directory, with the reason on stderr and nothing on stdout.
> - **Found and fixed on the way:**
>   - Mutation M1a was equivalent: an unpublished builder carried the key.
>   - Mutation G3 stayed green: the guard's heading match was too loose.
>   - The full suite found 15 reds this change caused. Each was attributed alone
>     at this code and at base, then fixed (§ 8). One was `SKILL.md` breaking
>     its byte budget.

---

## 0. Base check

| | |
|---|---|
| branch | `worktree-agent-a6e7b8b025a4be772` |
| HEAD at dispatch | `583f024f` |
| tree | clean (`git status --porcelain` printed nothing) |
| `git merge-base --is-ancestor 746dc8cd HEAD` | **exit 1**: stale |
| action | `git merge --ff-only 746dc8cd`, this branch only |
| re-asserted | exit 0; HEAD `746dc8cd` |

Commits on this branch, oldest first:

| commit | what |
|---|---|
| `572a902b` | starts, predicate, six payloads, contracts, `board` refusal, the two new modules, version pins, parity baseline |
| `91610742` | two mutation findings: M1a's unpublished key removed, G3's heading match tightened |
| `55b2b4dc` | durations entries for the two new modules |
| `1c26d27a` | the 15 suite reds, fixed (§ 8) |
| next commit | this file only |

## 1. Start enumeration and doc changes

### 1.1 Enumeration

This was re-derived from the router (`SKILL.md § First-time setup`,
`§ Router subcommands`) and each lane's `§ Bootstrap` and `init`, not taken
from the dispatch's list.

| # | start | doc | first write before | first write now |
|---|---|---|---|---|
| S1 | first-time setup | `SKILL.md § First-time setup` step 3 | `.perry/config.md` (deleted by ADR-019) | `perry-config set` ×4 (`reference/first-run.md § Writing the config store`) |
| S2 | `work` bootstrap | `work/SKILL.md § Bootstrap`, `work/reference/bootstrap.md` | `BOARD.md`, `PROJECT_STATE.md` | step 0: `perry-config set` ×4 when the store is absent |
| S3 | goals-only start (`goals init`) | `goals/SKILL.md § Bootstrap`, `goals/reference/setup.md § init` | `OKR.md` | step 0: `perry-config set` ×4 when absent |
| S4 | decide-only start (`decide init`, then `new`) | `decide/SKILL.md § init`, `§ Bootstrap` | `design/README.md`, `decisions/` | step 0: `perry-config set` ×4 when absent |
| S5 | `/perry adopt`, every `--only=` subset | `reference/adoption.md` stage 3 step 0, stage 4 row 1 | `State root:` into `.perry/config.md` (on a collision); `.perry/config.md` via setup | `perry-config set "State root"` on a collision; stage 4 row 1 is the store, **first, whatever `--only` names** |

Enumerated and **not** starts, each with its reason:
- `/perry diagnose` asks about any folder and converts nothing into Perry.
- `/perry relocate` moves an installed project.
- `perry-decide bootstrap` and `perry-task add` are tools a start calls, not
  documented starts in their own right. `perry-task add` writes `tasks.jsonl`,
  a canonical store, so it installs on its own.

No start had a stated reason not to create `.perry/`, so hard limit 7 did not
fire. Adoption's corollary says "stages 0–3 write only the dossier". Stage 3
step 0 already wrote the state-root answer immediately, and the doc calls that
the LOSSLESS precedent (`adoption.md § The resume contract`). Only its target
file changed.

### 1.2 Doc changes

| file | change |
|---|---|
| `SKILL.md` | step 1 reads `.perry/config.jsonl` only; step 3 writes the store first and cites `reference/first-run.md § Writing the config store`; step 2 and the chat-language line no longer name the deleted file; the summary line and `§ Configuration` state the store |
| `reference/first-run.md` | new `§ Writing the config store`, carrying the four commands (moved out of the router for its byte budget, § 8) |
| `work/reference/bootstrap.md` | step 0; the trailer no longer says setup writes `.perry/config.md` |
| `work/SKILL.md` | step 0 reads the store; `§ Bootstrap` cites the criterion and step 0 |
| `goals/reference/setup.md` | `init` step 0 |
| `goals/SKILL.md` | step 0 and the heartbeat read name the store; `§ Bootstrap` points at `init` step 0 |
| `decide/SKILL.md` | step 0 reads the store; `init` step 0; `§ Bootstrap` points at it |
| `decide/reference/decisions.md` | the ADR language read and the ADR refusal gate read the store (a start that always found `.perry/config.md` absent would refuse every ADR) |
| `reference/adoption.md` | lines 40 and 136; stage 3 step 0 command; the resume row; the stage 4 row |
| `reference/i18n.md` | `:17` where the two settings live; the lane checklist's first read |

The four step-0 reads are part of the start, not incidental. `work/SKILL.md`
step 0 says "If the file is missing and any state file already exists, prompt
the user to run top-level `/perry` first-time setup". Once starts write only
the store, a lane still reading `.perry/config.md` would find it missing on
every session.

### 1.3 The guard

`tests/test_starts_write_the_config_store_first.py` reads 15 sections, each
located by its heading line. A section runs to the next heading of the same or
higher level, and a heading that matches 0 or 2+ lines fails by name. It judges
no meaning. It reads two literals:

1. `.perry/config.md` appears in no guarded section.
2. Every section that performs a first write carries a `"$PERRY_HOME/bin/perry-config" set` line. **Those lines are executed**, with `<…>` placeholders replaced, in an empty directory:
   - `perry-state --section installed` must read `false` before and `true` after;
   - every command must exit 0.

## 2. The predicate and the detection walks

### 2.1 The predicate

`viewer/parsers.py`:

- **`canonical_store_names()`** reads `schema/state-schema.json § claims`: a
  `kind: file`, `anchor: state` path ending `.jsonl`. On 2026-09-14 that is
  `asks`, `cadence`, `intake`, `linkage`, `okr`, `risks` and `tasks`. An
  unreadable schema answers `()`, which narrows the criterion and never widens
  it.
- **`installed(project_root)`** is `configured(root)`, or a canonical store
  that exists (or cannot be searched) under `resolve_state_root(root)`.
- **`installed_project_root(start)`** is the walk: the first installed ancestor,
  handed to `resolve_project_root`.

  **Why the hand-off:** `perry/tasks.jsonl` makes `perry/` installed on its own
  terms, so a walk from below the state root meets it first. The inverse returns
  the ancestor whose `.perry/` points back at `perry/`. Without it, A1, A2, A3
  and A5 go red (mutation G5, 9 tests).

### 2.2 The nine sites

`tests/test_board_less_project_is_recognised.py` names all nine, and all nine
now call the predicate or the walk.

| site | before | now |
|---|---|---|
| A1 `parsers § _resolve_project_root` | `configured ∨ BOARD.md ∨ OKR.md` walk | `installed_project_root` |
| A2 `lib § resolve_project_root` | same, a copy | `installed_project_root` |
| A3 `perry-state § resolve_root` | same, a copy | `installed_project_root` |
| A4 `perry-state § build` | `BOARD.md ∨ OKR.md ∨ configured ∨ design/DESIGN-*.md` | `P.installed(perry_root)` |
| A5 `perry-lint § main` walk | `BOARD.md ∨ OKR.md ∨ configured` | `installed_project_root` |
| A6 `perry-lint § is_adopted` | `configured ∨ BOARD.md ∨ OKR.md ∨ phase/` | `P.installed` |
| A7 `perry-explain § typed_task_lookup` | `configured ∨ BOARD.md ∨ OKR.md ∨ phase/` | `installed` |
| A8 `perry-diagnose § scan_tracking` | `config ∨ (okr ∧ board)` | `P.installed`; `okr`, `board` and `phase` stay as on-disk facts |
| A9 `perry-diagnose § diagnose` `is_perry` | `configured ∨ (OKR.md ∧ BOARD.md)` | `P.installed` |

Left alone, each with its reason:
- `perry-lint § _track_context` and `perry-goals § tracks_of` ask about the
  config store only, never a markdown marker.
- `parsers:5090 board_on_disk` describes the file rather than detecting a
  project.

**The anti-vacuity setUp is kept unchanged.** A new subclass,
`MarkdownNoLongerStopsTheWalk`, plants `BOARD.md` and `OKR.md` in a directory
between the working directory and the project, after that setUp has run. Its
tests:
- A1, A2, A3 and A5 walk past the marked directory;
- A4, A6, A8 and A9 call the marked directory not installed.

The subclass re-runs the parent's nine tests as well (the fixture is a
superset). That costs about a second.

### 2.3 Fixtures and adoption paths the criterion affects

The four fixture projects under `tests/fixtures/` each hold
`.perry/config.jsonl` (`TASK-237-d3b-result.md § 3.1`). The in-test shapes that
lost `installed` are the § 8 reds, each fixed by writing the config store or a
canonical store. Every adoption path writes the store first (§ 5.2).

## 3. The six payloads and the contracts

### 3.1 The key

Each payload computes `P.installed(project_root)` beside `contract`. Versions:

| payload | before | after | `semantics` entry |
|---|---|---|---|
| `perry-task/list` | 2.1 | **2.2** | `{version: "2.2", fields: ["installed"]}` |
| `perry-asks/list` | 1.1 | **1.2** | `1.2` |
| `perry-events/list` | 1.2 | **1.3** | `1.3` |
| `perry-goals/list` | 3.1 | **3.2** | `3.2` |
| `perry-decide/list` | 2.0 | **2.1** | `2.1`, the first entry |
| `perry-knowledge/list` | 1.1 | **1.2** | `1.2`, the first entry |

Each entry's note says:
- what an empty payload used to be indistinguishable from;
- what `installed: false` now says;
- the criterion.

**A tension, named rather than smoothed.** The contract doctrine says a key
addition belongs in the Changelog and not in `semantics`. See
`test_semantics_on_every_payload § TestNothingWasInventedToFillThem`, and the
decide and knowledge pages' former "empty, and that is the answer" sections.
Amendment (4) item 1 asks for one entry per contract, and the dispatch lists
removing one as a mutation. I followed the amendment. Each page's Changelog and
entry note say it was entered at the user's decision. The tests that pinned the
doctrine were updated, each with its reason:
- `EMPTY_TODAY` is now roles only;
- `KEY_ADDED_AT` names decide 1.1 and knowledge 1.1.

### 3.2 Contracts

Every page:
- states its new version;
- carries `installed` in its sketch;
- has an `installed` paragraph citing `schema/README.md § installed`;
- has a Changelog entry for the new version.

Beyond that:
- **asks** and **knowledge** add an `installed` row to their top-level key
  table.
- **decide** and **knowledge**: `semantics` now carries an entry, so their key
  sections are rewritten and a `semantics[]` key table is added. Otherwise the
  parity check reports `semantics[].version/fields/note` as undocumented.
- **task**: rule 3's snippet now pins `SUPPORTED = {1: 18, 2: 2}`.
  `test_contract_page_snippets` executes it against the live payload.

**`schema/asks-list-contract.md § Exit codes`, reconciled.** `0` covers a
directory with no register and a directory that is not a Perry project: `asks`
is `[]`, the counts are 0, and `installed` says which case it is. A register
that does not exist is an empty register, not an unreadable one. `1` stays for
a register that exists and cannot be read.

### 3.3 The parity baseline

`python3 tests/contract_key_parity.py --record`. `git diff -U0` of
`tests/fixtures/contract-key-parity.json` shows only these changes.

| contract | changed |
|---|---|
| asks | key and `contract` 1.1 → 1.2; `documented` / `emitted` 24 → 25 |
| decide | key and `contract` 2.0 → 2.1; `documented` 25 → 29, `emitted` 22 → 26 (`installed` plus `semantics[].version/fields/note`) |
| events | 1.2 → 1.3; 27 → 28 / 27 → 28 |
| goals | 3.1 → 3.2; 85 → 86 / 81 → 82 |
| knowledge | 1.1 → 1.2; 17 → 21 / 17 → 21 (`installed` plus the three `semantics[]` keys); **`witness` `"tests/fixtures/witness-project"` → `""`** |
| task | 2.1 → 2.2; 140 → 141 / 132 → 133 |
| roles | unchanged |

`documented_not_emitted` and `emitted_not_documented` are unchanged (empty) for
all six. **Named, not in the permitted set:**
- **decide and knowledge.** Their three `semantics[]` entry keys became
  observable, because the array stopped being empty. They are keys of the
  entries this row adds.
- **knowledge `witness` → `""`.** The witness project was consulted only while
  `semantics` was an empty collection. It no longer is, so no collection needed
  a witness. No finding moved.

**`tests/fixtures/contract-shapes.json` was NOT re-recorded.** A trial re-record
imported a large, unrelated diff:
- it still recorded `perry-goals/list/3.0` and `perry-task/list/2.0`;
- tens of keys added since then: `bound.*`, `krs[].current_measurement.*`,
  `tasks[].depends_on_resolved[]`;
- widened types.

The file was restored with `git checkout -- tests/fixtures/contract-shapes.json`.
`test_contract_invariance` is green against it at the final tree. That baseline
has been stale since before this row (row R2).

### 3.4 Version pins, each with its reason

Each carries a one-line `# TASK-237 3b′: …` reason:
- `test_bin_argument_contract:703`
- `test_task_summary:80`
- `test_decide_status_enum:277` (and its key set gains `installed`)
- `test_events_feed:278,300`
- `test_measured_krs_declare_a_target:149,152`
- `test_stranded_rows:610-611`
- `test_asks_list:122`
- `test_goals_writer:1573`
- `test_contract_page_snippets:411-412`
- `test_contract_key_parity` (`perry-decide/list` read from the tool, as its own
  comment said it would be "the day it moves")

The exact-shape sets gain `installed`:
- `test_goals_contract § TestShape.TOP`
- `test_decide_writer § TestListContract.TOP`
- `test_task_writer_contracts § TOP_KEYS`

## 4. The `board` refusal

`perry-tasks § cmd_board` asks `P.installed(root)` before reading anything.
When it is false the command:
- prints to stderr: `perry-tasks: refused — <root> is not an installed Perry project: no .perry/config.jsonl at its root and no canonical store under its state root (schema/README.md § installed). Nothing was printed.`;
- prints nothing on stdout;
- exits 1.

Measured in § 5.1. Guarded by
`test_installed_is_one_predicate § test_board_refuses_where_nothing_is_installed`
(mutations M9 and G16).

## 5. The four-directory table and the start re-run

### 5.1 Four directories, measured at the final code

`scratchpad/probe.py` ran against the worktree at `1c26d27a` (the probe reads
tools only). Every command ran with `--root <dir>` and `PERRY_PROJECT` unset.
- `tasksonly` holds one task record in `tasks.jsonl`. With no config the
  declared state root is the directory itself.
- Cell format: `installed` / exit code.

| directory | list | asks | events | goals | decide | knowledge | `perry-state --section installed` | `board` |
|---|---|---|---|---|---|---|---|---|
| empty | false / 0 | false / 0 | false / 0 | false / 0 | false / 0 | false / 0 | false / 0 | **exit 1, 0 B stdout** |
| `BOARD.md` only | false / 0 | false / 0 | false / 0 | false / 0 | false / 0 | false / 0 | false / 0 | **exit 1, 0 B** |
| `.perry/config.jsonl` only | true / 0 | true / 0 | true / 0 | true / 0 | true / 0 | true / 0 | true / 0 | exit 0, 1,105 B |
| `tasks.jsonl` only | true / 0 | true / 0 | true / 0 | true / 0 | true / 0 | true / 0 | true / 0 | exit 0, 1,196 B |

**At base (`746dc8cd`, the same probe):**
- no payload carried `installed`;
- `perry-state` said `true` for `BOARD.md` only and `false` for `tasks.jsonl`
  only;
- `board` exited 0 on all four.

`test_installed_is_one_predicate` asserts the same table, plus:
- `OKR.md` only, `phase/` only, `design/DESIGN-*.md` only, and all the markdown
  together: each `false`;
- one directory per declared store: each `true`;
- a store one level below an undeclared state root: `false`.

### 5.2 Every start re-run

`scratchpad/starts_rerun.py` ran against the final doc text:
- one fresh scratch directory per start;
- the `perry-config set` lines were **read out of each doc section and
  executed** (placeholders: `English`, `single`, `perry`);
- tool steps were run: `perry-lint --claims`, `perry-decide bootstrap`,
  `perry-task add`;
- human steps were followed by hand, each recorded: the template the doc names
  was copied, `design/README.md` and the journal note were written;
- the interview itself was not simulated.

The counterfactual column runs the same start without its store step.

| start | steps (after the store) | `installed`, as documented | without the store step |
|---|---|---|---|
| first-time setup | `perry-lint --claims` (read-only); steps 4–6 ask and route | **true** | false |
| `work` bootstrap | `BOARD.md`, `PROJECT_STATE.md` at the project root (step 2 says "at the project root"; followed literally), six dirs, `knowledge/INDEX.md`, `.perry/hook.md`, journal line | **true** | false |
| goals init, before `plan-phase` | `perry/OKR.md` from the template; step 10 not run | **true** | false |
| decide-only (`init`, then `new`) | `perry/design/README.md`, `perry-decide bootstrap` (exit 0), `DESIGN-001` from the template | **true** | false |
| `/perry adopt` (all lanes) | OKR and phase from templates, a design doc, `perry-task add` (exit 0), a knowledge card, `ARCHITECTURE.md` | **true** | true (`tasks.jsonl`) |
| `adopt --only=okr` | `OKR.md`, `phase/001-first.md` | **true** | false |
| `adopt --only=board` | `perry-task add` | **true** | true (`tasks.jsonl`) |
| `adopt --only=design` | a design doc | **true** | false |
| `adopt --only=knowledge` | a knowledge card | **true** | false |
| `adopt --only=arch` | `ARCHITECTURE.md` | **true** | false |
| `adopt --only=design,knowledge,arch` | the three | **true** | false |

**By hand, recorded.** My first two `perry-task add` calls were wrong:
- `--verification V3` is refused as "a rung, not a check";
- `--unlinked` is refused with no `linkage.jsonl`.

Both refusals were correct. The rows above use `--rung V3`, a check sentence,
and neither `--kr` nor `--unlinked`. Adoption's attribution pass
(`/perry goals link`) runs after a phase exists.

## 6. Payload diff

`scratchpad/payload_diff.py`:
- `git archive` copies of base `746dc8cd` and final `572a902b`;
- `bin/perry-task` changed after that only in an unprinted builder (§ 7.2 M1a);
- this repository's `.perry/config.jsonl`, `.perry/events.jsonl` and `perry/`,
  with `evidence/` symlinked, under a directory named `Perry`;
- `perry/BOARD.md` present in one copy and removed in the other;
- `PERRY_HOME` set to the tree, `HOME` to an empty directory;
- paths normalised, `generated_at` masked, JSON compared path by path.

**Base → final, identical for `BOARD.md` present and deleted:**

| surface | exit | differs |
|---|---|---|
| `perry-task list --json`, `list --all --limit 0 --json` | 0 / 0 | + `installed`; + `semantics[11]` (`version`, `fields[0]`, `note`); `contract` 2.1 → 2.2 |
| `perry-task asks --all --json` | 0 / 0 | + `installed`; + `semantics[1]`; 1.1 → 1.2 |
| `perry-task events --json` | 0 / 0 | + `installed`; + `semantics[2]`; 1.2 → 1.3 |
| `perry-goals list --json` | 0 / 0 | + `installed`; + `semantics[3]`; 3.1 → 3.2 |
| `perry-decide list --json` | 0 / 0 | + `installed`; + `semantics[0]`; 2.0 → 2.1. The comparator also prints `- semantics`: that is its placeholder for an empty list (`[]`) that is now populated, not a removal |
| `perry-knowledge list --json` | 0 / 0 | same as decide; 1.1 → 1.2 |
| `perry-state --json` | 0 / 0 | **equal** |
| `perry-state --section installed` | 0 / 0 | **equal** (`true`) |
| `perry-tasks board` | 0 / 0 | **byte-equal**, 154,515 B |

**Nothing else differs.** Present → deleted is the same at base and final:
- `conformance.missing_projection` `""` → the path;
- `board.lines` 186 → 0;
- `board.last_updated` → `""`.

Those are 3a's file exceptions.

## 7. Tests and mutations

### 7.1 Tests

**New modules:**

| module | tests | alone, median of 3 |
|---|---|---|
| `tests/test_installed_is_one_predicate.py` | 7 | 1.57 s (1.57 / 1.53 / 1.57) |
| `tests/test_starts_write_the_config_store_first.py` | 3 | 1.57 s (1.57 / 1.58 / 1.54) |

- Timed with `python3 tests/parallel -j 1 --times <module>`; the median is of
  the harness's own per-module seconds. load1 11.53.
- Source `2026-09-14-task237-d3b-prime` in `tests/durations.json`.

**Where expectations come from:**
- **Four-directory module.** The files each directory is built from, and a
  store list this module reads out of `claims[]` with its own filter. Not from
  a payload, a board or a tool.
- **Start guard.** The literal instruction, and `perry-state` before and after
  running the doc's own lines.

`BOARD.md` appears only as a marker that must not count.

**Changed modules:**
- `test_board_less_project_is_recognised`: + `MarkdownNoLongerStopsTheWalk`
  (§ 2.2).
- The § 3.4 pins.
- The § 8 fixes.

### 7.2 Mutations

**Method.** `scratchpad/mutate.py` on `git archive` copies under the
scratchpad:
- `91610742` for the full battery;
- `1c26d27a` for M10, G1, G2, G3 and G20, whose anchors or guard sources moved
  after it.

For each mutation:
- the anchor is asserted to occur exactly once;
- every `__pycache__` in the copy is removed;
- the named modules run (`python3 -m unittest -v`);
- the red ids are collected;
- the file is restored and its git blob SHA-1 compared with `git ls-tree -r`
  of that commit.

**Every restore matched.** Both controls, unmutated over the 47 tests of the
modules used, had no red.

| # | mutation (file) | red: named tests | result |
|---|---|---|---|
| M1a | drop `installed` from `_cmd_list_from_board` (`bin/perry-task`) | none | **GREEN at `572a902b`: equivalent.** Its only caller, `store_records`, keeps `tasks` and discards the dict. The key was computed on every write and printed by nothing. **Removed from that builder** in `91610742`; `cmd_list` carries it |
| M1b | drop `installed` from `cmd_list` (task list) | `test_installed_is_one_predicate § test_every_payload_says_installed_by_the_one_criterion` | RED |
| M2 | drop it from `asks` | same test | RED |
| M3 | drop it from `events` | same test | RED |
| M4 | drop it from `perry-goals list` | same test | RED |
| M5 | drop it from `perry-decide list` | same test | RED |
| M6 | drop it from `perry-knowledge list` | same test | RED |
| M7 | **accept `BOARD.md` in the predicate** (`parsers § installed`) | `§ test_perry_state_answers_by_the_criterion`, `§ test_every_payload_says…`, `§ test_board_refuses…`; `MarkdownNoLongerStopsTheWalk`: all four walk tests, `§ test_a_markdown_only_directory_is_not_installed_at_any_site` | RED (8) |
| M8 | **accept `OKR.md` in the predicate** | the same 8 | RED (8) |
| M9 | **`board` prints on a non-installed directory** (`if False and …`) | `§ test_board_refuses_where_nothing_is_installed` | RED |
| M10 | **restore `SKILL.md` step 3's `.perry/config.md` instruction** | `TheDeletedFileIsNotNamed § test_no_start_section_names_the_deleted_config_file` | RED (also at `1c26d27a`) |
| M11 | **remove one `semantics` entry** (asks 1.2, deleted whole) | `test_semantics_on_every_payload § TestAShippedEntryNeverLeaves § test_no_shipped_entry_left_a_payload_or_changed_its_fields` | RED |
| G1 | a writing start loses its tool lines (`goals/reference/setup.md`) | `§ test_each_writing_start_names_the_tool`, `§ test_the_documented_lines_run_and_end_installed` | RED (also at `1c26d27a`) |
| G2 | a doc line stops being a valid invocation (`sett`, `decide/SKILL.md`) | `§ test_the_documented_lines_run_and_end_installed` | RED (also at `1c26d27a`) |
| G3 | a guarded heading renamed, `## Bootstrap` → `## Bootstrapping` (`work/SKILL.md`) | at `572a902b`: none. At `91610742` and `1c26d27a`: `§ test_no_start_section_names_the_deleted_config_file` | **GREEN, a finding, fixed.** The heading matched by bare prefix, so the neighbour guarded the renamed section. A prefix must now end at a separator |
| G4 | canonical stores hard-coded to `tasks.jsonl` | `§ test_perry_state_answers…`, `§ test_every_payload…`, `§ test_board_refuses…` | RED (3) |
| G5 | the walk returns the marker directory, not its project root | A1, A2 and A5 in both classes, plus the three `passes_a_markdown_only_directory` walks | RED (9) |
| G6 | the lib walk accepts `BOARD.md` again | `§ test_the_lib_walk_passes_a_markdown_only_directory` | RED |
| G7 | the `perry-state` walk accepts `BOARD.md` again | `§ test_perry_state_walk_passes_a_markdown_only_directory` | RED |
| G8 | the `perry-lint` walk accepts `BOARD.md` again | `§ test_the_linter_walk_passes_a_markdown_only_directory` | RED |
| G9 | the parsers walk accepts `BOARD.md` again | `§ test_the_parsers_walk_passes_a_markdown_only_directory` | RED |
| G10 | `perry-state § build` accepts `BOARD.md` again | `§ test_a_markdown_only_directory_is_not_installed_at_any_site` | RED |
| G11 | `perry-lint § is_adopted` accepts `OKR.md` again | same | RED |
| G12 | `perry-diagnose` `installed` ORs `okr ∧ board` again | same | RED |
| G13 | `perry-diagnose` `is_perry` ORs `OKR.md ∧ BOARD.md` again | same | RED |
| G14 | `asks` says `installed: true` on any directory | `§ test_every_payload_says_installed_by_the_one_criterion` | RED |
| G15 | a non-installed payload drops a key (decide `expired_sunsets`) | `§ test_a_non_installed_payload_keeps_its_empty_shape` | RED |
| G16 | `board`'s refusal reason goes to stdout | `§ test_board_refuses_where_nothing_is_installed` | RED |
| G17 | the README criterion heading removed | `TheCriterionIsWrittenOnceAndCited § test_the_readme_states_it` | RED |
| G18 | the events contract stops citing the criterion | `§ test_each_contract_that_carries_the_key_cites_it` | RED |
| G19 | the store branch ignores the state root (`state_root = root`) | none | **GREEN: equivalent.** The store branch runs only when `configured(root)` is false. With no config store `declared_state_root` has nothing to read, so `resolve_state_root(root)` is `root`. The line is kept because it states the criterion |
| G20 | `reference/first-run.md § Writing the config store` loses its lines | `§ test_each_writing_start_names_the_tool`, `§ test_the_documented_lines_run_and_end_installed` | RED (at `1c26d27a`) |

**Greens.**
- **M1a and G19** are equivalent, argued above; M1a's code was removed.
- **G3** was a real hole, fixed and re-run red.

No mutation of a real defect stays green.

## 8. Suite

| run | tree | modules · tests | red modules · red tests | tree guard |
|---|---|---|---|---|
| `bash tests/run`, foreground, nothing written during it | `55b2b4dc` | 138 · 3,959 | 12 · 19 | "nothing … moved" |
| **`bash tests/run`, final**, foreground, nothing written during it | `1c26d27a` | **138 · 3,960** | **3 · 4** | "nothing … moved" |

**First run.** Ten test ids were new beyond the three pre-existing ones. They
cover 15 test methods in 9 modules (subtests count once per id above).
- **Attribution, by the rule.** The nine modules were re-run alone:
  - at this code: 304 tests, 15 red (7 failures, 8 errors);
  - at base `746dc8cd` (`git archive`): 304 tests, **OK**.

  So this change caused all fifteen.
- **Fixed in `1c26d27a`:**
  - **Markdown-only fixtures** that wrote the deleted `.perry/config.md` next to
    a `BOARD.md` now write the config store, which declares nothing they read.
    The `installed: false` payload had no `board` section (`KeyError`), or
    `perry-lint` judged nothing:
    - `test_cadence` ×2;
    - `test_work_modes` ×5;
    - `test_phase_kr_declared_once`;
    - `test_retired_tolerance`.
  - **`test_track_register_source § test_no_store_warns_about_nothing_either`.**
    Its no-config fixture gains an empty `risks.jsonl`, a canonical store that
    declares no track, so the register stays `absent`.
  - **`test_board_less_reads_and_writes` ×2** now name the store-read minors
    (2.1, 1.1). They had read the current minor, which is now the `installed`
    entry.
  - **`test_explain_typed_tasks § test_an_unadopted_projects_tasks_jsonl_is_not_claimed_by_perry`.**
    Its premise is reversed by the user's criterion: a `tasks.jsonl` at the root
    is a canonical store. The test is inverted and renamed
    `test_a_tasks_jsonl_alone_is_a_canonical_store_and_is_claimed`. The half the
    criterion keeps (markdown only, nothing claimed) is its own test. See row R1.
  - **`test_router_budget`.** `SKILL.md` was 21,156 B against its 20,480 cap
    (base 20,441). The four commands moved to
    `reference/first-run.md § Writing the config store`, the router cites them,
    and my added wording was trimmed. It is 20,464 B. The start guard and the
    re-run read the commands there.
  - **`test_shipped_vocabulary`.** It reads the default state root out of
    ``write `State root: perry` ``, which my step 2 rewording had removed. The
    literal is back.

**Final run: the reds, by id, are exactly the three pre-existing ones the
dispatch names.** No other red, so no further module was re-run alone.
- `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`
- `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness`
- `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`

The count is 4 red tests because the harness reports one of the parity ids
under a subtest.

**Against base** (136 modules · 3,935 tests), the final run is:
- +2 modules (the two new ones);
- +25 tests: 7 + 3 in the new modules; 14 in `MarkdownNoLongerStopsTheWalk`
  (its own 5, plus the parent's 9 it inherits); 1 net in
  `test_explain_typed_tasks`.

The harness's only durations complaint is `test_contract_page_snippets.py`,
pre-existing (3b's R8).

## 9. Rows this work names (none minted)

- **R1: a file named `tasks.jsonl` (or any canonical store name) makes a
  directory a Perry project.** This is the user's criterion, measured. A
  folder that belongs to another tool and holds `tasks.jsonl`:
  - reads `installed: true`;
  - prints a board;
  - stops every project-root walk;
  - has its records answer `perry-explain` ahead of a markdown definition.

  `BOARD.md` behaved the same way before. The new exposure is that the store
  names are more generic. Whether a store should need `.perry/` beside it is a
  decision, not a fix.
- **R2: `tests/fixtures/contract-shapes.json` is stale.** It records goals 3.0
  and task 2.0, and a re-record imports a large unrelated diff (§ 3.3).
  `test_contract_invariance` stays green, so the baseline is not guarding the
  keys it looks like it guards.
- **R3: docs outside the starts still name `.perry/config.md`.**
  - `SKILL.md § relocate` and `reference/router-subcommands.md:32,59` (relocate
    rewrites `State root:` there);
  - `reference/i18n.md:67,232`;
  - `reference/config.md` (its title and shape section);
  - `reference/diagnose.md:476` (`perry-config write --from-file`, removed);
  - `reference/glossary.md:144`, `reference/snapshot.md:129`,
    `reference/input-quality.md:21`;
  - `modes/*.md` (Tracks);
  - `work/reference/subcommands.md`, `review.md`, `git-boundaries.md`;
  - `goals/reference/phases.md:84`;
  - `decide/state/ADR_TEMPLATE.md:12`;
  - `schema/README.md:30,37,341,356` (the aiMark resolution paragraph still
    says to read `.perry/config.md`).

  None is a start. Several are instructions to read or rewrite a file no tool
  reads.
- **R4: the semantics doctrine and the amendment disagree** (§ 3.1). Future key
  additions need one rule. Either an entry for a consumer-visible key, or
  Changelog only.
- **R5: `work/reference/bootstrap.md` step 2 says "at the project root".** First
  -time setup writes `State root: perry`, and bootstrap writes `BOARD.md`
  beside `.perry/`, outside the state root it just declared. This is 3c
  territory (the file's fate), and I did not change it.
- **R6: `MarkdownNoLongerStopsTheWalk` re-runs its parent's nine tests.** A mixin
  would drop about a second.

## What I did not check

- **The interviews themselves.** The starts were re-run mechanically, with fixed
  answers. No `AskUserQuestion` flow was exercised, and no host (Claude Code,
  OpenCode, Codex) ran a start from its own docs.
- **A split repo layout, a non-English document language, or a state root other
  than `perry`** in the start re-run.
- **`/perry adopt` stages 0–3 with a collision.** Stage 3 step 0's immediate
  `perry-config set "State root"` was not exercised. That path makes
  `installed: true` before stage 4. `SKILL.md` step 2 checks for an interrupted
  run before step 3 reads `installed`, so the entrance order is unchanged, but I
  did not run it.
- **An unsearchable `.perry/` or state root** (`exists_or_unreadable` → `None`
  counts as installed) was not measured.
- **aiMark**, or any consumer, against the new payloads.
- **`viewer/`** (`bin/perry-viewer`) on a markdown-only directory. Its walk is
  `parsers § _resolve_project_root`, which is changed and guarded; the rendered
  page was not opened.
- **`perry-lint` exit codes on markdown-only projects beyond the fixtures.** An
  unadopted directory's lint no longer judges its markdown. Every fixture the
  suite lints holds a config store.
- **The payload diff at `1c26d27a`.** The measured final was `572a902b`. Between
  them `bin/` changed only by removing an unprinted builder's key (M1a), and
  the four-directory table was re-measured at `1c26d27a`.
