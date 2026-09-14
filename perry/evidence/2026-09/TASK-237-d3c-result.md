# `TASK-237` deliverable 3c — result: the file is gone

> Scope: `TASK-237-spec.md § Amendment 2026-09-14 (7) § Deliverable 3c`, with the
> two "3c addition" lists and 3b′ rows R1, R3 and R5.
>
> **Delivered: the predicate, the schema edit, the deletion, the lint, the writers
> and most of the documents. Three STOPs on documents that are not mine to
> change, and one bounded remainder.**
>
> - **Predicate.** A store counts only with a `.perry/` directory beside it. Six
>   contracts announce it with a `semantics` entry and a minor bump:
>   `perry-task/list` 2.3, `perry-asks/list` 1.3, `perry-events/list` 1.4,
>   `perry-goals/list` 3.3, `perry-decide/list` 2.2 and `perry-knowledge/list`
>   1.3. The parity baseline moved only in those versions.
> - **Schema and deletion.** `files[id=board].required` is `false` and the
>   `BOARD.md` claim carries a note. `perry/BOARD.md` is `git rm`ed.
> - **Lint and writers.** `perry-lint --root` on an archive of the final code
>   commit exits 0 with 0 errors, no `[missing-file]` and no drift finding.
>   Every `perry-task` write leaves no `BOARD.md`; 26 of 28 exit 0, and the
>   other two refuse identically at base.
> - **Payloads.** Every published read payload equals the base with `BOARD.md`
>   deleted, except its contract version and its one new `semantics` entry.
> - **Verbs.** None deleted, argued in § 4: `render`, `diff`, `verify` and the
>   register `-render`/`-diff` verbs keep their subject, a `BOARD.md` a project
>   still holds. Each refuses in one line where there is none, and none creates
>   one (measured).
> - **Found on the way:**
>   - **`perry-diagnose`'s dangling-id check read `BOARD.md` as the register for
>     `USER-`/`RX-` ids.** With the file gone it reported nine ids dangling on
>     this repository. Fixed (§ 1.3).
>   - **The lint census said "comparison incomplete — drift is unchecked"** of
>     every board register with no board. Fixed.
> - **STOP 1: `SKILL.md § The hand-off contract`** still names `BOARD.md` as
>   `work`'s file and as a refusal case. The table carries a V5 signature, and
>   `tests/test_ownership.py` reddens on the edit with "the contract needs a
>   fresh V5 signature". Reverted; proposed text in § 5.3.
> - **STOP 2: `ARCHITECTURE.md` § 6 `NN-2` and § 5's contract version** are the
>   user's under `NN-6`. Proposed text in § 5.2.
> - **STOP 3: `work/reference/git-boundaries.md § Git Role Boundaries`** is a
>   governed region pinned by a `SHA-256` digest (`test_spec_scannability`). Its line 11
>   names `BOARD.md`. Reverted; re-pinning is a deliberate decision.
> - **Left, by hard limit 7:** the lane-doc lines that DESCRIBE the board as a
>   file (§ 8, reason "sweep"). Every line that instructed a reader to open,
>   read, copy, scan or `git log` it, or an agent to write rows into it, was
>   rewritten.

---

## 0. Base check

| | |
|---|---|
| branch | `worktree-agent-a6a6f423084edacc6` |
| HEAD at dispatch | `583f024f` |
| tree | clean (`git status --porcelain` printed nothing) |
| `git merge-base --is-ancestor cac46c73 HEAD` | **exit 1**: stale |
| action | `git merge --ff-only cac46c73`, this branch only |
| re-asserted | exit 0; HEAD `cac46c73` |

Commits on this branch, oldest first:

| commit | what |
|---|---|
| `5845ed9e` | the predicate, six contracts and minors, the shipped-semantics record, the parity baseline, version pins |
| `bebba5d1` | the schema edit, `git rm perry/BOARD.md`, the lint no-board branches, the `perry-explain`/`perry-diagnose` store harvest, tests off the live board |
| `dd67eed5` | documents pass 1, the `perry-tasks` `SURFACE` summary, the census guard |
| `b7603d09` | documents pass 2 — **the final code commit**; every archive measurement below is on it unless named |
| next commit | this file only |

## 1. Enumeration

### 1.1 Changed

| # | site | change |
|---|---|---|
| C1 | `viewer/parsers.py § installed` | the store clause needs `(root / ".perry").is_dir()`; an unsearchable `.perry/` counts, on `configured`'s argument |
| C2 | `viewer/parsers.py § installed_project_root` | docstring: a bare `perry/tasks.jsonl` no longer makes `perry/` installed |
| C3 | `schema/README.md § installed` | criterion 2 is `.perry/` AND a canonical store; the no-`.perry/` case named. Also lines 30, 37, 341, 356: the aiMark resolution instruction read `.perry/config.md`, and now reads `.perry/config.jsonl § state_root` |
| C4 | `bin/perry-task` (list, events, asks), `bin/perry-goals`, `bin/perry-decide`, `bin/perry-knowledge` | contract constants bumped; one `semantics` entry each |
| C5 | the six `schema/*-list-contract.md` pages | version line, sketch, the `installed` criterion sentence, a changelog entry; the task page's `SUPPORTED` snippet `{1: 18, 2: 3}`; decide and knowledge "one entry" → two |
| C6 | `schema/state-schema.json § files[id=board]` | `"required": false` and a `note`; the `BOARD.md` claim gains a `note` |
| C7 | `perry/BOARD.md` | `git rm` |
| C8 | `bin/perry-lint § check_store_drift` | returns before derivation when no board file exists (was `store-drift-uncheckable`) |
| C9 | `bin/perry-lint § check_{risk,intake,ask,cadence}_store_drift` | no board file → no finding (was `*-store-drift-uncheckable`) |
| C10 | `bin/perry-lint` census | a `_board_absent` clause: "`N` record(s); no `BOARD.md` — nothing is projected from it, so there is nothing to drift" |
| C11 | `bin/perry-explain § harvest_register_stores` | new: task, ask, risk and cadence records are their ids' homes; the rows a board would carry contribute mentions at their store line |
| C12 | `bin/perry-diagnose § report_lines`, `§ _mention_source` | a `.jsonl` store is read whole, one record = one statement |
| C13 | `bin/perry-tasks § SURFACE.summary` | "three registers" → four, and what the tool now is |
| C14 | documents | § 5 |
| C15 | tests | § 9.1 |

### 1.2 Left, each with its reason

| # | site | why |
|---|---|---|
| L1 | `bin/perry-task § main`, `§ commit` re-render | a `BOARD.md` a project still holds is still read and re-rendered. § 4 argues it |
| L2 | `perry-tasks render`/`diff`/`verify`, `*-render`/`*-diff`, `build`/`write --from-board`, `*-build`/`*-write` | § 4 |
| L3 | `perry-task --describe` `writes` lists naming `BOARD.md` (27 writes) | true on a held board; row R7 |
| L4 | `schema/state-schema.json` prose outside `files[id=board]` and its claim | the consent covers only that edit; row R6 |
| L5 | `perry-state § board.lines`, `board.last_updated`; `perry-task/list § conformance.missing_projection` | describe the file (3a's file exceptions); row R8 |
| L6 | `perry-lint` board-row checks (`done-needs-evidence`, the review checks) | they judge rows of a held board; with no file 3b made the event/store passes run |
| L7 | `SKILL.md` ownership table and refusal case | STOP 1 |
| L8 | `ARCHITECTURE.md` § 6 `NN-2`, § 5 version | STOP 2 |
| L9 | `git-boundaries.md:11` | STOP 3 |

### 1.3 Surprises

1. **`perry-diagnose` resolved ids through `BOARD.md`.** `test_diagnose §
   test_perry_itself_passes_its_own_id_checks` went red on the deletion.
   - `USER-004`, `USER-015`, `USER-906`, `USER-925`, `RX-002` and `RX-003` had
     their homes in board register rows.
   - `V4-1`, `V4-2` and `V4-3` had no home. Their one report mention was
     `TASK-436`'s row, whose table paragraph names `perry-diagnose`, which
     exempted their other mentions.
   - A store record as a home fixed six. The mention half fixed the other
     three only after a second fault: `perry-diagnose § read_text` caps a file
     at 400,000 B, and `tasks.jsonl` is 571,579 B, so line 366 was past the cap.
     Found with a per-mention debug run against a base archive.
2. **Two of the three spec-listed `SKILL.md` edits are a signed contract**
   (STOP 1). The spec's "3c addition" list names the ownership table; the test
   names it V5-signed.
3. **A governed documentation region** (STOP 3). `git-boundaries.md:11` was not
   on the spec's lists, and my first pass touched it.
4. **`verify` does not crash without a file.** Its handler reads `BOARD.md`
   unguarded, but the `build` call ahead of it refuses first (§ 4 measurement).
5. **The adopt counterfactual.** `perry-task add` alone installs a directory: it
   creates `.perry/events.jsonl`, so `.perry/` exists beside the store (§ 7.1).
6. **`TASK-274` left `perry-diagnose`'s `user_load.dangling_in_reports`.** Its
   task record is now its home. At base it was reported-only.

## 2. Predicate

`installed(root)` is `configured(root)`, or `.perry/` is a directory AND a
canonical store exists (or cannot be searched) under `resolve_state_root(root)`.

**The contract rule was checked before bumping.** `schema/README.md` and each
page say `1.x → 1.y` only adds keys, and a removal or a retype is a major. A
narrowed meaning is neither. `perry-goals/list/2.2` shipped a meaning change as a
minor. No page's rule made it a major, so there was no stop.

**Each citing contract was re-read.** The sentence "`.perry/config.jsonl` at the
project root, or a canonical store under the state root" was false in five
pages (`task`, `events`, `goals`, `decide`, `knowledge`) and is corrected. The
`asks` page's `installed` row cites the README without spelling the criterion.
The notes of the shipped 3b′ entries are history and were not edited.

**Parity baseline** (`tests/contract_key_parity.py --record`), whole `git diff
-U0`: the six entry keys and their `contract` values — `asks` 1.2→1.3, `decide`
2.1→2.2, `events` 1.3→1.4, `goals` 3.2→3.3, `knowledge` 1.2→1.3, `task`
2.2→2.3. Nothing else moved: no key count, no witness.

**`tests/fixtures/shipped-semantics.json`** gains the six entries (36 lines added,
none removed).

**`test_installed_is_one_predicate`** gains:
- `tasks_only_without_dot_perry` → `false`;
- `dot_perry_and_tasks` → `true`;
- one `bare_store_<name>` → `false` per declared store;
- the per-store `true` rows now carry `.perry/`.

**`test_explain_typed_tasks`** is inverted back
(`test_a_tasks_jsonl_with_no_dot_perry_is_not_claimed`). The half 3b′ established
is kept as `test_a_tasks_jsonl_beside_dot_perry_is_claimed`.

## 3. Schema and deletion

- `files[id=board]`: `required: true` → `false`, plus a `note`. The headings and
  tables stay declared because `perry-tasks board` lays the board out from them.
- The `BOARD.md` claim stays and carries a note: `/perry relocate` moves a board
  a project still holds, and the `--from-board` imports read it under the state
  root.
- `perry-lint --templates`: clean.
- `git rm perry/BOARD.md` in `bebba5d1`.

## 4. The verbs and the hand-backs

**Decision: nothing is deleted this round.** Three reasons, each measured or
cited:

1. **Their subject still exists.** It is a `BOARD.md` a project still holds.
   3b measured two consumer boards with cadence rows no store holds:
   `Gimegime-pmo` 5 and `aimark` 1. Writers still re-render such a file, so a
   hand edit there is drift. `NN-2` requires drift to be reported and never
   silently absorbed or overwritten, and `render --write` is the remedy
   `perry-lint` names. Deleting it would leave that finding with no remedy.
2. **Stopping the writers' re-render is not a no-file change.** It would strand
   those projects' board-only rows before anyone imports them, and this round
   may not touch another project to import them first.
3. **With no file they already have no effect**, measured on the final archive.
   Every invocation below exits 1 with one line, `perry-tasks: refused — no
   BOARD.md at <state root>`, no traceback, and no file created or changed:
   - `build`, `verify`, `render`, `render --write`, `diff`, `write --from-board`;
   - `risks-{build,render,render --write,diff,write --from-board}`;
   - `intake-`, `asks-` and `cadence-` `{build,render --write,diff,write --from-board}`.

   `board` exits 0.

**What changed instead.** The `SURFACE` summary, `bin/README.md`'s tool row and
usage note, and `bin/ARCHITECTURE.md § 5` say these verbs act on a held board,
refuse without one, and that no command creates one. **`ADR-019`'s precedent is
followed at the point it applies:** there the projection stopped existing for
every project. Here it stops for projects that no longer hold one. Row R5 names
the retirement and its precondition.

**Hand-backs that name a `render --write`, and when each is reachable:**

| site | reachable when |
|---|---|
| `perry-task:2017` | a held board's derived records differ from the store |
| `perry-task:2470` (shrink refusal) | a write removes records the board still shows; a declared board is built from the stores, so it cannot shrink against them |
| `perry-task:3130` | an open record the projection has no row for; a declared board carries every open record |
| `perry-task:3409`, `:9073` | an `OSError` writing a board that exists |
| `perry-task:5127` | an open record missing from the projection; as `:3130` |
| `perry-task:5682` | a terminal record still on a board; a declared board carries no terminal row |
| `perry-lint` drift remedies (`:4098`, `:4243`, `:4392`, `:4522`, `:4654`, `:5066`) | a drift finding; with no file none is emitted, and G1–G6 hold that |

No verb was deleted, so none of these names a deleted verb. That they are
unreachable without a file is argued for `perry-task` and not measured on a
board-less project (row R9); the lint half is guarded.

## 5. Documents

### 5.1 Rewritten

| spec item | file:line | now |
|---|---|---|
| 3c addition (root) | `AGENTS.md:24`, `:38` | eyeballing `bin/perry-tasks board`; "There is no `BOARD.md` to edit" |
| | `ARCHITECTURE.md § 2` `viewer/parsers.py` | owns the store readers, the `installed` predicate, and the reader of a held board |
| | `ARCHITECTURE.md § 4` sentence and write diagram | the board is `perry-tasks board`; a held `BOARD.md` is re-rendered, never created |
| | `ARCHITECTURE.md § 8` | a changelog entry naming STOP 2 |
| | `README.md`, `README_cn.md` file tree | the `BOARD.md` line removed from both |
| | `SKILL.md` ownership table | **STOP 1**, reverted |
| 3c addition (`bin/`) | `bin/ARCHITECTURE.md § 1`, § 2 `perry_store.py` row, § 5, § 8 | the reader counts from `perry-tasks board`; verbs act on a held board |
| | `bin/README.md § For an agent` fallback | `perry-task list --json` for tasks, asks and risks; `OKR.md` for goals; `perry-tasks board` for a person |
| | `bin/README.md` tool row, the recovery paragraph, write slot (3), usage note | render/diff on a held board only; none created |
| | `bin/perry-tasks` `SURFACE` summary | four registers |
| hook | `.perry/hook.md:52` | "the task store — `perry-tasks board` for a person, `perry-task list --json` for a program" |
| 3b′ R3 | `SKILL.md § relocate`, `reference/router-subcommands.md:31`, `:59` | `State root` set with `perry-config set`; a note goes to `.perry/hook.md` |
| | `reference/config.md` | rewritten around `.perry/config.jsonl`. The deleted projection's `render`/`verify` section is gone, and a leftover `.perry/config.md` is named inert |
| | `reference/i18n.md:67`, `:232` (language switch) | setting labels; `perry-config set "Document language"` |
| | `reference/diagnose.md:476` `MODE-02` | marked retired with `ADR-019`, remedy `—` (it named two deleted verbs) |
| | `modes/pipeline.md`, `modes/queue.md`, `modes/inquiry.md` | track cells → the track register in `.perry/config.jsonl`; `BOARD.md` row/column cells → the task record |
| | `decide/state/ADR_TEMPLATE.md:12` | `.perry/config.jsonl` |
| 3b′ R5 | `work/reference/bootstrap.md` step 0, step 2 | step 2 creates files **under the state root** step 0 wrote, and **no `BOARD.md`** |
| cadence | `modes/queue.md:198` | the register is `cadence.jsonl`, printed as `## Cadence` |
| open/read instructions | `work/reference/subcommands.md` (plan-week, weekly, plan-week, mid-week, mid-phase, digest scan, retro, handoff snapshot and read-first list, rollover, `git log`, triage's "do not update", intake step 0, cap rule) | `perry-task list --json` / `perry-tasks board` / the task store |
| | `goals/SKILL.md` (read table, evidence citation, state cross-check, hand-off), `goals/reference/weekly.md`, `goals/reference/phases.md:266`, `goals/state/phase_TEMPLATE.md` | the task record / `perry-task list --json` / `perry-task add` |
| | `decide/SKILL.md` (lines 3, 25, 26, 27, 47, 75, 224, 234, 255, 257, 267) | the task store / `perry-task list --json` |
| | `work/SKILL.md` (71, 83, 87, 94, 284, 286) | the task store, `perry-tasks board` |
| | `work/reference/state-files.md:15`, `:49`; `digests.md:268`; `autopilot.md:228`; `handoff_TEMPLATE.md:91`, `:100`; `reference/adoption.md:273`; `reference/first-run.md:47`; `modes/pipeline.md:241` | as above |

`SKILL.md` is 20,457 B against its 20,480 B budget; the lane pages are within theirs.

**Doc guard.** No guard checks a doc for an instruction to open `BOARD.md`, and
none was built. The mutation "restore one doc's `open BOARD.md` instruction"
therefore has no test to redden. Two existing guards did bite on this round's
documents (STOP 1, STOP 3), and `test_ownership §
test_no_lane_page_instructs_a_write_it_may_not_perform` reddened on my first
wording of `decide/SKILL.md:255`, which was then reworded.

### 5.2 STOP 2: `ARCHITECTURE.md`, proposed rather than edited (`NN-6`)

**§ 6 `NN-2`, the sentence the deletion makes false:** "a mutating command
writes the record, then renders the file from it." For this repository there
is no file. Proposed replacement:

> - **Rule**: a mutating command writes the record first. Every reading of it —
>   a payload, `perry-tasks board`, and a projection file a project still
>   holds — is derived from the record; a projection file is re-rendered from it
>   and never created. A projection edited by hand is drift, and drift is
>   REPORTED — never silently absorbed and never silently overwritten.

**§ 5's `perry-task list --json` version** says 2.1. The tool emits 2.3 (2.2 from
3b′, 2.3 from this round). Proposed:

> - `schema/task-list-contract.md`, version **2.3** (2.2 adds `installed`; 2.3
>   narrows it to a store with `.perry/` beside it). …

§ 4's read-path label "contract 2.0" is descriptive but left untouched, so that
§ 4 and § 5 do not disagree more than they already do.

### 5.3 STOP 1: the signed hand-off contract, proposed

`SKILL.md § The hand-off contract` row `work` and the refusal sentence.
`tests/test_ownership.py` requires `` `BOARD.md` `` as a refusal case, maps
`files[].path` `BOARD.md` to a contract cell, and says a changed ownership row
"needs a fresh V5 signature — not a quiet entry in this test". Proposed, for
the user's signature, with the test's `SCHEMA_PATH_TO_CONTRACT`,
`FOREIGN_WRITES` and refusal-case literal updated in the same change:

> | **`work`** (`work/`) | `tasks.jsonl` + its 4 register stores (`perry-tasks board` prints them), `journal/`, … |
>
> Three cases that must refuse: `goals` writing `tasks.jsonl`; …

The row costs about 45 B more than today, and `SKILL.md` has 23 B of headroom.

## 6. Measurements on `git archive b7603d09`

The base is `git archive cac46c73`. Tools always ran from their own tree, with
`PERRY_HOME` set to it, `HOME` empty and `PERRY_PROJECT` unset.

### 6.1 Lint on the final archive (no `BOARD.md`)

| | base, `BOARD.md` deleted | final |
|---|---|---|
| `perry-lint --root <copy>` exit | 1 | **0** |
| errors | 1 — `missing-file BOARD.md` | **0** |
| `[missing-file]` findings | 1 | **0** |
| warnings | 44 | 40 |
| drift findings | `store-drift-uncheckable`, `risk-`, `intake-`, `ask-store-drift-uncheckable` | **none** |
| lines naming `BOARD.md` | — | the four census lines, "`N` record(s); no `BOARD.md` — nothing is projected from it, so there is nothing to drift" |

The four missing warnings are exactly the four uncheckable findings.

### 6.2 Write matrix

**Method.** `scratchpad/verify_final.py § matrix`. Every subcommand with a
non-empty `writes` in `perry-task --describe --json` runs on a fresh copy of the
archive's own `.perry/` and `perry/` (`evidence/` symlinked). Prerequisites run
first. The subject is `TASK-137` (not started, V2), with a second open task for
`--on`, an open risk, the first design id, and
`perry/evidence/2026-09/TASK-237-spec.md` as evidence.
"`BOARD.md` after" is a recursive search of the copy.

| subcommand | exit | `BOARD.md` after |
|---|---|---|
| add (`--unlinked`), answer, ask, cadence-add, cadence-done, depends, design-link, done, drop, evidence, intake, intake-sweep, next, prioritize, resolve-intake, retitle, risk-add, risk-clear, route, rung, stage, start, status, summary, track (26) | **0** | none |
| purge | 1 — "Removing the record would leave that reference pointing at an id nothing resolves" | none |
| risk-migrate | 1 — "… will not touch a row that has an id" | none |

**Both exit-1 rows were attributed at base.** They ran with `DROP_BOARD=1` on
`git archive cac46c73` and gave the same exit and the same refusal. `purge`'s
subject was added with `--unlinked`, which writes a linkage record naming it.
`risk-migrate` has no bullets to migrate on a store-backed register (3a). The
first matrix run had two argument errors of mine, since corrected:
- `add` without `--kr`/`--unlinked`, refused on a project with `linkage.jsonl`;
- `rung` to the rung the task already had.

### 6.3 Payload diff

**Method.** Base archive with `perry/BOARD.md` deleted, against the final
archive. Each ran on its own tree's state, root paths normalised, and was
compared key path by key path.

| payload | exit base / final | differs |
|---|---|---|
| `perry-task list --json` | 0 / 0 | `contract` 2.2→2.3; + `semantics[12]` (`version`, `fields[0]`, `note`) |
| `list --all --limit 0 --json` | 0 / 0 | the same |
| `asks --all --json` | 0 / 0 | 1.2→1.3; + `semantics[2]` |
| `events --json` | 0 / 0 | 1.3→1.4; + `semantics[3]` |
| `perry-state --json` | 0 / 0 | **equal** |
| `perry-goals list --json` | 0 / 0 | 3.2→3.3; + `semantics[4]` |
| `perry-decide list --json` | 0 / 0 | 2.1→2.2; + `semantics[1]` |
| `perry-knowledge list --json` | 0 / 0 | 1.2→1.3; + `semantics[1]` |

**No other difference.** Each list payload differs in exactly 4 paths. Measured
the same way on `dd67eed5`: identical.

### 6.4 `perry-tasks board` on the final archive

Exit 0, 154,609 B, titled with the archive directory's name.

## 7. Starts and the five-directory table

### 7.1 Every documented start

**Method.** `scratchpad/starts_rerun.py` at `b7603d09`, one fresh directory per
start.
- The `"$PERRY_HOME/bin/perry-config" set` lines are read out of each doc
  section and executed.
- The steps after them are followed by hand, as the doc says.
- The counterfactual runs the same steps without the store lines.

| start | doc section | config lines, exits | steps after | all 7 surfaces `installed` | `board` | `BOARD.md` created | without the store step |
|---|---|---|---|---|---|---|---|
| first-time setup | `reference/first-run.md § Writing the config store` | 4, all 0 | `perry-lint --claims` (0) | **true** | 0 | no | false |
| `work` bootstrap | `work/reference/bootstrap.md` | 4, all 0 | step 2 as now written: `PROJECT_STATE.md`, six dirs, `knowledge/INDEX.md` under the state root; `.perry/hook.md`; journal line | **true** | 0 | no | false |
| goals init | `goals/reference/setup.md § init` | 4, all 0 | `OKR.md` from the template | **true** | 0 | no | false |
| decide init + new | `decide/SKILL.md § init` | 4, all 0 | `design/README.md`, `perry-decide bootstrap` (0), `DESIGN-001` from the template | **true** | 0 | no | false |
| adopt, every lane | `reference/adoption.md` | 1, 0 | OKR + phase, `perry-task add` (0), a design doc, a card, `ARCHITECTURE.md` | **true** | 0 | no | true |
| adopt `--only=okr` | the same | 1, 0 | OKR + phase | **true** | 0 | no | false |
| adopt `--only=board` | the same | 1, 0 | `perry-task add` (0) | **true** | 0 | no | true |
| adopt `--only=design` | the same | 1, 0 | a design doc | **true** | 0 | no | false |
| adopt `--only=knowledge` | the same | 1, 0 | a card | **true** | 0 | no | false |
| adopt `--only=arch` | the same | 1, 0 | `ARCHITECTURE.md` | **true** | 0 | no | false |
| adopt `--only=design,knowledge,arch` | the same | 1, 0 | the three | **true** | 0 | no | false |

The two counterfactual `true`s are `perry-task add`. It writes `tasks.jsonl` and
creates `.perry/events.jsonl`, so the tightened predicate still holds.

### 7.2 Five directories

Every surface ran at the final archive with `--root <dir>`; each cell is `installed` / exit.

| directory | expected | task | asks | events | goals | decide | knowledge | `perry-state` | `board` exit, stdout |
|---|---|---|---|---|---|---|---|---|---|
| empty | false | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | 1, 0 B |
| `BOARD.md` only | false | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | 1, 0 B |
| `tasks.jsonl` only, no `.perry/` | false | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | false/0 | 1, 0 B |
| `.perry/` + `tasks.jsonl` | true | true/0 | true/0 | true/0 | true/0 | true/0 | true/0 | true/0 | 0, 1,114 B |
| config only | true | true/0 | true/0 | true/0 | true/0 | true/0 | true/0 | true/0 | 0, 1,106 B |

## 8. Remaining-mention census

`grep -rn 'BOARD\.md' bin/ viewer/ SKILL.md AGENTS.md README.md README_cn.md
ARCHITECTURE.md work/ goals/ decide/ modes/ reference/ schema/` at `b7603d09`:
**369 lines**. The same grep over `git archive cac46c73` gives 428.

Reasons:
- **held**: acts on or describes a `BOARD.md` a project still holds (render,
  import, drift, reader);
- **import**: the `--from-board` import family;
- **no-file**: says there is no board, or what happens without one;
- **history**: changelog, rationale, a measurement or a quoted past record;
- **template**: a shipped template's guidance;
- **schema**: `state-schema.json` text outside the consented edit (R6);
- **signed**: STOP 1; **governed**: STOP 3;
- **sweep**: describes the board as a file Perry keeps, and is left by hard
  limit 7 (R3).

### 8.1 Code and schema (279 lines)

| file | hits | lines | reason |
|---|---|---|---|
| `bin/perry-task` | 87 | 118–271, 8330–8340 | history (shipped `semantics` notes) |
| | | 699–864, 1006–1019, 1166, 1556, 2017–2021, 3038–3170, 3391, 3599, 7187–7357, 7713, 7783 | held (`Board`, the re-render, refusals and hand-backs on a held board) |
| | | 4924–6749 | history (docstrings), and the held-board refusals at 5117 and 5632 (§ 4) |
| | | 8044–8097, 8904 | no-file (`declared_write_board`'s refusals, `main`'s board path) |
| | | 8657–8767 | held (`SURFACE` `writes`; R7) |
| | | 9049–9080 | held (the success line names a board only when one was rendered) |
| `bin/perry-tasks` | 49 | 6, 61–410, 591–1704, 2046–2288 | import / held (the verbs of § 4) |
| | | 1857–1950 | held / import (`SURFACE`) |
| `bin/perry-lint` | 36 | 271, 848, 1465, 1842, 2133–2149, 3889–3926, 5085, 6065 | history |
| | | 1571–1818, 2772–3220 | held (board-row checks) |
| | | 4006–4594 | held (drift checks), no-file (their branches) |
| | | 6272–6279 | no-file (the census clause) |
| `viewer/parsers.py` | 26 | 467–671 | history (the predicate's docstrings: `BOARD.md` does not count) |
| | | 1085–1542, 1737, 2245, 3765, 5071–5219 | held (`parse_board`, `load_snapshot`, `board_on_disk`) |
| `bin/perry-diagnose` | 20 | all | held (on-disk facts about a folder's own board) / history |
| `bin/perry_store.py` | 13 | all | held / import (renderers, section shapes) and the declared board's choices |
| `bin/lib/__init__.py` | 12 | all | history (resolver and lock docstrings) |
| `bin/perry-state` | 9 | all | held (`board.lines`, `last_updated`) / history |
| `bin/perry-goals` 5, `bin/perry_md_store.py` 3, `bin/perry-knowledge` 2, `bin/perry-okr` 1, `bin/perry-decide` 1 | 12 | all | history |
| `bin/perry-explain` | 2 | 583, 598 | history (this round's harvest docstring) |
| `schema/state-schema.json` | 13 | 1194 (claim), 1341 (`files[id=board]`) | held (the consented edit) |
| | | 285, 1205–1240, 1400–1410, 1529, 2266 | schema (R6) |

### 8.2 Documents (90 lines)

| file:line | reason |
|---|---|
| `bin/ARCHITECTURE.md:53`, `:124`; `bin/README.md:43`, `:192`, `:379`, `:560`, `:567` | held |
| `bin/ARCHITECTURE.md:120`; `bin/README.md:164`, `:563`, `:614`; `AGENTS.md:39`; `work/SKILL.md:108`; `work/reference/bootstrap.md:29`; `work/reference/subcommands.md:103` ("do not open"); `goals/reference/phases.md:99` ("does not write"); `schema/README.md:379`; `schema/asks-list-contract.md:25` | no-file |
| `bin/README.md:572`, `:580`, `:592`, `:606`; `reference/adoption.md:438` | import |
| `ARCHITECTURE.md:72`, `:143`, `:152`; `work/reference/state-files.md:15`, `:49`; `work/reference/subcommands.md:380`, `:636` | held |
| `bin/ARCHITECTURE.md:178`, `:189`; `bin/README.md:394`; `ARCHITECTURE.md:209` (`NN-1` rationale), `:279`, `:292`; `work/reference/subcommands.md:19`; `goals/reference/linkage.md:110`; `reference/hand-off-contract.md:68`, `:73`; `schema/README.md:254`; `schema/task-list-contract.md:79`, `:181`, `:182`, `:452`, `:566`, `:711`, `:715`, `:725`, `:1121`; `schema/asks-list-contract.md:163` | history |
| `schema/task-list-contract.md:368` (`missing_projection`'s definition) | held (R8) |
| `reference/i18n.md:52` (an invariant file name) | held |
| `SKILL.md:72`, `:77`; `goals/SKILL.md:51`; `reference/adoption.md:29` (restate the signed table) | signed |
| `work/reference/git-boundaries.md:11` | governed |
| `work/state/PROJECT_STATE_TEMPLATE.md:4`, `:36`; `work/state/evidence_TEMPLATE.md:4`; `work/state/journal_TEMPLATE.md:20` | template |
| `work/SKILL.md:3` (frontmatter), `:117`, `:183`, `:186`; `work/reference/conversational.md:74`; `work/reference/subcommands.md:101`, `:440`, `:458`, `:478`, `:518`, `:612`; `goals/SKILL.md:3` (frontmatter); `modes/pipeline.md:50`; `modes/inquiry.md:70`; `modes/queue.md:76`, `:94`, `:95`, `:137`; `reference/i18n.md:214`; `reference/adoption.md:16`, `:52`; `reference/diagnose.md:404`; `reference/router-subcommands.md:18`; `reference/input-quality.md:4`, `:81`; `schema/task-list-contract.md:92`, `:104`; `schema/goals-list-contract.md:167` | sweep (R3) |

## 9. Tests and mutations

### 9.1 Tests

**New:**
- `tests/printed_board.py`, a helper and not a module: the board
  `perry-tasks board` prints from this repository's stores.
  - Measured on a scratch copy: `render` over it is byte-identical to the file;
    `diff` and every `*-diff` exit 0; `verify` reports 0 mismatches.
  - What it no longer proves, and each caller says so: that a HAND-KEPT board
    round-trips.
- In `test_board_less_reads_and_writes`:
  - `test_a_board_less_project_lints_with_the_errors_it_has_with_the_file`
    replaces the 3a test that expected `[missing-file]`;
  - `test_no_board_draws_no_drift_finding`;
  - `test_the_census_says_there_is_nothing_to_drift`.
- `test_explain_typed_tasks`: § 2.
- `test_installed_is_one_predicate`: § 2.

**Changed:**
- `test_cadence_store § test_with_no_file_it_is_silent_and_counts_the_records`
  (was `…_uncheckable_…`).
- Off this repository's deleted board onto `printed_board`: `store_fixture §
  full_project`, `test_board_render § Project.perry`, `test_task_store`,
  `test_store_drift:512`, `test_risks § TestPerrysOwnBoard`,
  `test_task_writer_core § …round_trips`, `test_decoration_changes_nothing`.
- Version pins, each with a one-line reason: `test_bin_argument_contract`,
  `test_asks_list`, `test_contract_page_snippets`, `test_decide_status_enum`,
  `test_events_feed` ×2, `test_goals_writer`, `test_measured_krs_declare_a_target`
  ×2, `test_stranded_rows`, `test_task_summary`.

No test module was added, so `tests/durations.json` is unchanged.

**First full run after the deletion** (uncommitted tree): 11 red modules and 29
red tests — the three pre-existing, and 26 caused here. Attribution:
- `test_module_run_guard`, `test_diagnose` and `test_risks` were re-run alone
  at base (`git archive cac46c73`): 309 tests, green. So this change caused
  them.
- `test_module_run_guard`'s four reds were `test_risks`' three, reached through
  its dotted invocation.
- The rest read this repository's `perry/BOARD.md` by path.

After fixing them, the run reached the three pre-existing reds. The first
documents pass then reddened `test_ownership` ×4 and `test_spec_scannability` ×1:
STOP 1, STOP 3 and my `decide/SKILL.md:255` wording.

### 9.2 Mutations

**Method.** `scratchpad/mutate.py`, on fresh extractions of `git archive
dd67eed5`. `b7603d09` changes only four documents, none a mutation site or a
module used. For each mutation:
- every anchor is asserted to occur exactly once;
- every `__pycache__` is removed;
- the named modules run through `tests/parallel`;
- the FAIL/ERROR ids are collected;
- the file is restored and compared with `git show dd67eed5:<path>`.

**Control.** Unmutated, the eight modules used (320 tests): no red. **Every
restore compared equal.**

| # | mutation (file) | red: named tests | result |
|---|---|---|---|
| M1 | **a `BOARD.md` render put back into one writer**: `commit` writes the board with no file on disk (`bin/perry-task`) | `test_board_less_reads_and_writes § TestEveryWriteLandsWithNoBoard.test_each_write_lands_its_record_event_and_journal_line` | RED |
| M2 | **a store without `.perry/` accepted** (`if not anchored:` → `if False:`, `viewer/parsers.py`) | `test_installed_is_one_predicate § test_perry_state_answers_by_the_criterion`, `§ test_every_payload_says_installed_by_the_one_criterion`, `§ test_board_refuses_where_nothing_is_installed`; `test_explain_typed_tasks § test_a_tasks_jsonl_with_no_dot_perry_is_not_claimed` | RED (4) |
| M3a | **`perry-lint` requires the file again**: `files[id=board].required` true (`schema/state-schema.json`) | `test_board_less_reads_and_writes § TestLintOnABoardlessProject.test_a_board_less_project_lints_with_the_errors_it_has_with_the_file` | RED |
| M3b | **the same, in code**: the missing-file gate names the board (`bin/perry-lint`) | the same test | RED |
| M4a | **one new `semantics` entry removed**: `perry-decide/list` 2.2 (`bin/perry-decide`) | `test_semantics_on_every_payload § TestAShippedEntryNeverLeaves.test_no_shipped_entry_left_a_payload_or_changed_its_fields` | RED |
| M4b | the same, `perry-task/list` 2.3 (`bin/perry-task`) | the same test | RED |
| G1 | the tasks drift check's no-board return removed (`bin/perry-lint`) | `§ TestLintOnABoardlessProject.test_no_board_draws_no_drift_finding` | RED |
| G2 | risks: no-board branch warns `uncheckable` again | the same | RED |
| G3 | intake: the same | the same | RED |
| G4 | asks: the same | the same | RED |
| G5 | cadence: the same | `test_cadence_store § TestTheLintCensusCarriesTheCadenceStore.test_with_no_file_it_is_silent_and_counts_the_records` | RED |
| G6 | the census's no-board clause never answers (`_board_absent = False`) | `§ TestLintOnABoardlessProject.test_the_census_says_there_is_nothing_to_drift` | RED |
| G7 | `perry-explain`: `harvest_register_stores` not called | `test_diagnose § TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks` | RED |
| G8 | `perry-explain`: records are homes but carry no mentions | the same | RED |
| G9 | `perry-diagnose`: a JSONL store read as one paragraph again | the same | RED |
| G10 | `perry-diagnose`: a store read under the 400 KB cap again | the same | RED |

**No mutation stayed green.** The doc-guard mutation was not run: no such guard
exists (§ 5.1).

**One gap in the battery.** G7–G10 are caught only by a test over this
repository's own state. A fixture-level test of the store harvest does not
exist (row R9).

## 10. Suite

| run | tree | modules · tests | red modules · red tests | tree guard |
|---|---|---|---|---|
| `bash tests/run`, foreground, nothing written during it | `b7603d09` (final code) | **138 · 3,963** | **2 · 3** | "nothing … moved" |
| `bash tests/run` on the commit carrying this file | reported in the hand-off message | | | |

**Reds by id: the three pre-existing ones the dispatch names.**
- `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`
- `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness`
- `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`

**Against base** (138 · 3,960): +3 tests. They are the explain split and the two
new lint tests in `test_board_less_reads_and_writes`. The harness's only
durations complaint is `test_contract_page_snippets.py`, pre-existing.

## 11. Rows this work names (none minted)

- **R1 — the signed hand-off contract still names `BOARD.md`** (STOP 1). This
  needs the user's V5 signature for § 5.3's text, together with
  `tests/test_ownership.py`'s maps and `goals/SKILL.md:51`, and
  `reference/adoption.md:29`'s restatement.
- **R2 — `ARCHITECTURE.md` § 6 `NN-2` and § 5's version** (STOP 2). § 5.2's text
  is for the user.
- **R3 — the descriptive lane-doc sweep.** § 8.2's "sweep" lines describe the
  board as a file Perry keeps: the `work` and `goals` frontmatter descriptions,
  the intake section of `modes/queue.md` (its 200-line-cap argument), the
  risk-register section of `subcommands.md`, and the input-quality rubric names.
- **R4 — `git-boundaries.md § Git Role Boundaries`** names `BOARD.md` among
  work docs inside a SHA-pinned region (STOP 3).
- **R5 — retire the board-projection verbs and the writers' re-render** once no
  consumer project holds a board.
  - Precondition: `Gimegime-pmo` and `aimark` import their board-only
    registers (`cadence-write --from-board` and the rest).
  - Then `render`/`diff`/`verify` and the register `-render`/`-diff` verbs have
    no subject anywhere; § 4 is the argument.
- **R6 — `schema/state-schema.json` prose outside the consented edit.** The
  store claims' "projected from `BOARD.md`" notes, the `i18n` invariant example,
  the `Arrived`/`Parent` column descriptions, and lines 1529 and 2266 would each
  be a second schema edit.
- **R7 — `perry-task --describe` declares `BOARD.md` in `writes` for 27
  subcommands.** True on a held board. A consumer keying a matrix off it, as this
  round did, reads a write that never happens on a board-less project.
- **R8 — `perry-task/list § conformance.missing_projection`** is now non-empty on
  every board-less project. Its documented meaning is the file's path. A consumer
  that read it as a warning sees one permanently; its key and meaning cannot
  move in this round.
- **R9 — two unmeasured edges.**
  - The `perry-task` hand-backs in § 4 are argued unreachable without a board,
    not measured.
  - The store harvest behind `perry-diagnose`'s id check is guarded only through
    this repository's state (§ 9.2).
- **R10 — `.perry/config.md` mentions outside 3b′ R3's list.**
  - `reference/glossary.md:144`, `reference/snapshot.md:129`,
    `reference/input-quality.md:21`;
  - `work/reference/subcommands.md:348`, `:610`, `:807`,
    `work/reference/review.md:441`, `work/reference/git-boundaries.md:26`;
  - `goals/reference/phases.md:84`;
  - `modes/queue.md:61` (history);
  - the last line of `reference/config.md` (a leftover file is inert).
- **R11 — 3b′ R2 (`tests/fixtures/contract-shapes.json` stale)** is unchanged.

## What I did not check

- **Another project.** No consumer board was read or written. The claim that
  `Gimegime-pmo` and `aimark` hold board-only rows is 3b's measurement.
- **A `.perry` that is a regular file beside a store.** The predicate asks
  `is_dir()`, but `configured()` may answer yes through
  `exists_or_unreadable(.perry/config.jsonl)` on such a path. Not measured.
- **The interviews.** The starts were run mechanically with fixed answers, as in
  3b′. No host ran a start from its docs.
- **The viewer** (`bin/perry-viewer`) with no board.
- **`perry-diagnose` on a project whose stores are malformed.**
  `harvest_register_stores` skips an unparsable line; the lint reports it.
- **Localized boards and templates** under the import verbs.
- **The mutation battery on `b7603d09` itself.** It ran on `dd67eed5`; the
  commit after it changes four documents, none of them a mutation site or a file
  the modules used read.
