# TASK-237 deliverable 3b — result: the cadence store, the board's title, the 3a gaps

> Scope: `TASK-237-spec.md § Amendment 2026-09-14 (5) § Deliverable 3b`, with
> Amendment (4) pulled in whole.
>
> `perry/BOARD.md`, the repository's real stores (`perry/*.jsonl`,
> `.perry/events.jsonl`), `ARCHITECTURE.md`, `.perry/hook.md`, `work/` and
> `modes/queue.md` are unchanged on this branch. No id was minted and no row
> opened. The one `schema/state-schema.json` change is the cadence claim.
> Every `BOARD.md` deletion happened in scratch copies. The two consumer boards
> were read only to copy them.
>
> **Delivered, with one STOP.**
>
> - **Item 1, the cadence store: delivered.**
>   - `cadence.jsonl` is claimed; its records hold every column of the
>     register, as written.
>   - `cadence-add` and `cadence-done` write the store, the event and the
>     journal, with and without the file, and re-render the file when it
>     exists.
>   - `perry-state § cadence` and `perry-tasks board` read the store.
>   - `perry-tasks cadence-{build,render,write,diff}` is the one-way import.
>   - The import round-trips both scratch copies: every cell equal, and the
>     render byte-identical.
> - **Item 2, Amendment (4): STOPPED on the predicate, as the dispatch instructs.**
>   - The enumeration it demands before the change (§ 3.1) finds four
>     documented ways of starting a project that end with markdown only and no
>     store. All four are `installed: true` today and would be
>     `installed: false` under the new criterion.
>   - The worst is the `work` bootstrap (`work/reference/bootstrap.md`
>     step 2): `BOARD.md` + `PROJECT_STATE.md`, no `.perry/config.jsonl`, no
>     `*.jsonl`. Every session after it would re-offer the bootstrap.
>   - So none of the following was built: the `installed` predicate and its
>     README entry, the six `installed` keys and contract bumps, the detection
>     walks, `board`'s refusal on a non-installed directory, and the asks
>     exit-code text.
>   - **Board title and prose do not depend on the predicate, and were
>     delivered.** The title is the project's name, no template prose is
>     printed, and `{{` never appears. D1 choice C1 and its guards are updated.
> - **Item 3, the 3a gaps: delivered.**
>   - `perry-diagnose` reads `asks.jsonl` and `intake.jsonl`.
>   - Three `perry-lint` checks no longer go quiet without the file. The
>     fourth, `done-needs-evidence`, is argued quiet (§ 5).
>   - `project.name` follows the title's rule.
>   - A shipped `semantics` entry leaving a payload now reddens a named test.
> - **Found and fixed during measurement:**
>   - **`perry-lint` NS-01.** It flagged `perry/cadence.jsonl` as a file
>     "Perry did not write" — TASK-197's `asks.jsonl` defect, one register
>     over (§ 6.1).
>   - **The pinned counts that a fifth register moves.** These are the census
>     tests, the hand-back count, the direction-B ratchet and the header-fold
>     remainder. Each was updated with its reason (§ 7.1).

---

## 0. Base check

| | |
|---|---|
| branch | `worktree-agent-acfc5d717ae2a8cc9` |
| HEAD at dispatch | `583f024f` |
| tree | clean (`git status --short` printed nothing) |
| `git merge-base --is-ancestor 37adba9e HEAD` | **exit 1**: stale |
| action | `git merge --ff-only 37adba9e`, this branch only |
| re-asserted | exit 0; HEAD `37adba9e` |

Commits on this branch, oldest first:

| commit | what |
|---|---|
| `2bbdb4b3` | the code and the two new test modules |
| `bc4f9e48` | two guards: the cadence lint census, and the badly-typed rule name |
| `32c416ee` | the `perry-lint` NS-01 fix and its guard |
| `982ac9ce` | the durations entries |
| next commit | test updates for the pinned counts the full suite found (§ 7.1), the durations source, and this file |

Measurements are on `git archive` copies:
- base `37adba9e`;
- final `2bbdb4b3` (payloads, write matrix, import);
- `32c416ee` (lint re-capture after the NS-01 fix, and the mutation battery).

The commit after `32c416ee` changes only `tests/`, `tests/durations.json` and
this file.

## 1. Enumeration: sites changed and left

**Method.**
- **Sites.** A grep of `cadence`, `Cadence`, `NO_STORE_COMMANDS`, `project_name`
  and `BOARD.md` over `bin/`, `viewer/` and `tests/`. Each hit was filtered to
  "does this site read, write or pin the cadence register, the board's title or
  prose, or one of 3a's named gaps".
- **Pinned counts.** The full suite found every test pinning a count or a set
  that a fifth register moves (§ 7.1).

### 1.1 Changed

| # | site | change |
|---|---|---|
| C1 | `schema/state-schema.json § claims` | `cadence.jsonl`, `work`/`state`/`file`, beside `asks.jsonl` — the one schema edit |
| C2 | `bin/perry_store.py` | the cadence register: `CADENCE_STORED`, `CADENCE_FIELD_BY_COLUMN`, `cadence_store_path`, `cadence_section_shape`, `cadence_table`, `cadence_record`, `cadence_records`, `validate_cadence_records`, `cadence_plan`, `cadence_render` — the ask register's shape, every column stored |
| C3 | `perry_store § BOARD_STORES`, `DECLARED_BOARD_REGISTERS` | cadence added, so `declared_board` fills `## Cadence` from the store (and a board-less write mutates a board carrying the rows) |
| C4 | `perry_store § declared_board`, `DECLARED_BOARD_CHOICES` "prose" / "placeholder rows" / "which rows" | title from `project_name`; only `#` headings and tables printed; a heading carrying an unfilled `{{…}}` raises `UnfilledPlaceholder` |
| C5 | `bin/perry-task § REGISTER_EVENTS`, `REGISTER_SPEC`, `REGISTER_IDENTITY`, `REGISTER_ID_KEYED` | `cadence-add` / `cadence-done` → the `cadence` register, through `register_change` and the same transaction, shrink invariant and substitution report as the other three |
| C6 | `perry-task § NO_STORE_COMMANDS` and its refusal in `main` | removed (3a's stop) |
| C7 | `perry-task § load_register_records` | the rule name in the duplicate-id refusal comes from `REGISTER_RULE_NOUN`; `key[:-1]` would have named `cadenc-store-badly-typed` |
| C8 | `perry-task § declared_write_board` | passes the project name |
| C9 | `perry-task § NON_TASK_REFUSAL["Cadence"]` | "retire it: delete the row" was true when the file was the register; it now says no verb retires a row and what the next cadence write does with a hand deletion (§ 2.4) |
| C10 | `bin/perry-tasks` | `cadence-build/render/write/diff`, `SURFACE`, dispatch; `cmd_board` passes the name and catches `UnfilledPlaceholder` |
| C11 | `viewer/parsers.py § parse_board`, `load_snapshot`, `_cadence_from_store`, `CADENCE_STORE`, `is_cadence_register_header` | a cadence store is read instead of the section |
| C12 | `parsers § project_name` (was `_resolve_project_name`) | one rule for `perry-state § project.name` and the board title (§ 4) |
| C13 | `bin/perry-lint § check_cadence_store_drift`, its stats, census line, `--json` key | the ask check, one register over |
| C14 | `perry-lint § looks_like_perry_record` | knows the cadence record (§ 6.1) |
| C15 | `perry-lint § check_verification`, `check_reviews`, `resolves_somewhere` (+ `ids_the_board_would_carry`) | no longer silent with no file (§ 5.2) |
| C16 | `bin/perry-diagnose § open_user_asks`, `§ scan_work_modes` intake count | read the stores (§ 5.1) |
| C17 | `tests/fixtures/shipped-semantics.json`, `test_semantics_on_every_payload § TestAShippedEntryNeverLeaves` | the shipped-entry guard (§ 5.4) |

### 1.2 Left, each with its reason

| # | site | why |
|---|---|---|
| L1 | `bin/perry-state § build` `installed`, `resolve_root`; `perry-lint § is_adopted` and its walk; `parsers § _resolve_project_root`; `lib § resolve_project_root`; `perry-explain § typed_task_lookup`; `perry-diagnose § scan_tracking`, `§ diagnose` | the `installed` predicate STOP (§ 3) |
| L2 | the six list payloads, their contracts, `schema/README.md`, the parity baseline | same STOP: the `installed` keys are defined by the predicate |
| L3 | `schema/asks-list-contract.md § Exit codes` | the reconciliation is written against `installed: false`; changed once, with the key |
| L4 | `perry-tasks board` refusal on a non-installed directory | same STOP |
| L5 | `perry-lint:1571` `done-needs-evidence` | argued quiet (§ 5.2) |
| L6 | `perry-state § cadence_report`, `parse_frequency`, `parse_due` | unchanged: they read `cadence_items`, which now come from the store |
| L7 | `perry-task § cmd_cadence_add` / `cmd_cadence_done` bodies, `check_frequency`, `stamp_due`, `mint_cadence_id` | unchanged: they mutate whichever board `main` built, file or declared, and `register_change` derives the store from it — 3a's L7 |
| L8 | `perry-tasks render` / `diff` / `verify`, `*-render --write` | 3c |
| L9 | `perry-state § board.lines`, `board.last_updated`; `list § conformance.missing_projection` | describe the file (3a § 2.1) |
| L10 | docs: `bin/README.md`, `work/`, `modes/queue.md`, `ARCHITECTURE.md` | 3c, by the spec |

### 1.3 Surprises

1. **`perry-lint` NS-01 on the store Perry writes** (§ 6.1). No test module saw
   it: the payload-diff copies did. `looks_like_perry_record` holds a hand-kept
   tuple per store, and this is the second register to miss it.
2. **The adoption paths do not create `.perry/config.jsonl`.** First-time setup
   still tells the agent to write `.perry/config.md`, a file ADR-019 deleted
   and `configured()` no longer reads (§ 3.1). That is what turned the predicate
   into a stop.
3. **A hand-deleted cadence row under an add is not refused.** `cadence-add`
   mints a fresh id, so the count holds and TASK-243's substitution report
   applies instead of USER-906's shrink refusal. My first test asserted a
   refusal and was wrong about the guard (§ 2.4).
4. **`purge` no longer moves a present `BOARD.md`** that `perry-tasks board`
   rendered. The only byte it changed was the `> Last updated:` stamp, and the
   prose-free board carries no such line (§ 6.2).
5. **aiMark's `per task` frequency** imports, but `cadence-add` and
   `cadence-done` refuse it (`check_frequency`), unchanged. The imported row
   cannot be run without `--frequency` (§ 9 R2).

## 2. The cadence store and the import

### 2.1 Records

`CADENCE_STORED = (id, title, owner, frequency, next_due, last_run, last_evidence, order)`.
Each value is the cell as `markdown_tables` split it. There is no decoration
stripping (except the id handle, as for every id-keyed register), no blank
normalisation, no date parsing. A column the row lacks is `""`. `perry-state §
cadence_report` still computes `frequency_kind`, `due` and `days_overdue` at
read time and reports what it cannot read.

### 2.2 Writers and readers

- `cadence-add` and `cadence-done` reach the store through `REGISTER_EVENTS` →
  `register_change` → `commit()`'s canonical set.
  - This is the path the other three registers use; there is no second
    mechanism.
  - With no file, the board they mutate is `declared_board`'s, which now
    carries the stored rows.
  - With the file, it is re-rendered as before.
- `perry-state § cadence` reads `parse_board(…, cadence=records)`.
- `perry-tasks board` fills `## Cadence` from the store.

### 2.3 The import, measured on scratch copies

The two consumer boards were copied with `cp` into the scratchpad and only the
copies were used. Each skeleton project holds `.perry/config.jsonl` (state root
`.`) and the copied `BOARD.md`.

`scratchpad/import_roundtrip.py`, tools from `git archive 2bbdb4b3`:

| copy | section rows | records | cells compared (independent splitter) | mismatches | `cadence-render` vs file | `cadence-diff` | copy untouched |
|---|---|---|---|---|---|---|---|
| Gimegime-pmo | 5 (5 columns) | 5 | 25 | **0** | byte-identical, 53,466 B | `identical: true`, exit 0 | yes |
| aimark | 1 (6 columns) | 1 | 6 | **0** | byte-identical, 5,073 B | `identical: true`, exit 0 | yes |

- The comparison splits each row on unescaped `|` with a splitter written in the
  script, not Perry's `split_row`.
- The prose cells land whole, including every character of:
  - `**2026-08-31**（7 月版 ✅ 8/3 补作 → …；6 月版跳过）`
  - `**2026-W32 friday-review (8/7)**（W31 版 …）`
  - `2026-W32（W23–W31 停摆；…）`
- The aperiodic frequencies land whole too: `continuous`, `hourly` and
  `per task`, and `Next due` values `n/a`, `continuous` and `ongoing`.

**The import's gates.** These are `cmd_asks_write`'s, in its order: the
`--from-board` consent, the claim, the section shape, the store on disk being
readable, no repeated id, the byte gate, and the records readable back. There
are **two more**, because this store promises every cell:

- a row whose `ID` holds no handle is refused;
- a column no stored field holds (`Notes`) is refused.

The byte gate cannot see either — the renderer leaves such a row or cell
verbatim and `cmp` stays clean with the cell missing from the store. Each gate
has a test and a mutation (§ 7).

### 2.4 What a hand edit does now

| edit | next write | result |
|---|---|---|
| a cadence row deleted from `BOARD.md` only | `cadence-done` on another row (3 → 2) | **refused** by `refuse_to_shrink`, store byte-identical |
| the same | `cadence-add` (3 → 3) | **written**, the lost record reported on stderr and in the event's `substituted` (TASK-243) |
| a prose `Next due` edited in the file | `perry-lint` | `cadence-store-drift`, one finding naming the row |

## 3. `installed` and the predicate: STOPPED

### 3.1 The enumeration the dispatch requires before the change

**Criterion under test:** `.perry/config.jsonl` at the project root, OR any
`*.jsonl` claim with `anchor: state` under the state root. `BOARD.md`,
`OKR.md`, `phase/` and `design/` alone do not count.

**Test fixtures.** Every fixture project passes:

| fixture | markers | passes |
|---|---|---|
| `tests/fixtures/sample-project` | `.perry/config.jsonl`, BOARD, OKR, phase, linkage.jsonl | yes |
| `tests/fixtures/sample-project-zh` | `.perry/config.jsonl`, BOARD, OKR, phase | yes |
| `tests/fixtures/second-project` | `.perry/config.jsonl`, OKR | yes |
| `tests/fixtures/witness-project` | `.perry/config.jsonl`, BOARD, OKR, phase, tasks.jsonl, linkage.jsonl | yes |
| in-test shape: `test_semantics_on_every_payload § test_the_key_is_there_on_a_project_with_no_state_at_all` | `.perry/config.md` + `BOARD.md` | **no** — a test shape, not a supported one |

**Adoption paths.** Verified line by line:

| path | what it writes, in order | today | new criterion |
|---|---|---|---|
| `work` bootstrap, `work/reference/bootstrap.md` step 2 | `BOARD.md`, `PROJECT_STATE.md`, empty dirs, `knowledge/INDEX.md`, `.perry/hook.md`, a journal line. No `perry-config`, no `perry-task`. The same file says "`installed: true` — a `.perry/config.jsonl` alone is enough", and no step creates one | `true` (BOARD.md) | **`false`** |
| first-time setup, `SKILL.md` step 3 | "Confirm the project-wide preferences … into `.perry/config.md`" — the file ADR-019 deleted; `configured()` reads only `config.jsonl` | `false` alone; `true` once goals/work follow | `false` until a store exists |
| goals-only start, `goals/reference/setup.md` step 9 | "Write `OKR.md` from `state/OKR_TEMPLATE.md`" — no `okr.jsonl`, no config; step 10 runs `plan-phase`, which writes `linkage.jsonl` | `true` (OKR.md) | `false` until `plan-phase` completes |
| decide-only start, `decide/SKILL.md § init` and `§ new` | `design/README.md`, `decisions/` (`perry-decide bootstrap`), then `design/DESIGN-*.md` — no jsonl, no events | `true` (`design/DESIGN-*.md`) | **`false`** |
| `/perry adopt`, `reference/adoption.md § 4` | `.perry/config.md` (setup), `OKR.md`, then `phase/` + `linkage.jsonl`, `BOARD.md` via `add-task` (→ `tasks.jsonl`) … Completion is gated on `perry-lint`, whose `is_adopted` accepts `OKR.md` or `phase/` | `true` | `true` with a phase or tasks; **`false`** for `--only=design,knowledge,arch`, or with no phase and no accepted task |

**Verdict:** shapes Perry supports today lose `installed`, and the work
bootstrap is one of them. Per the dispatch, "If a shape Perry supports today
would lose it, stop and report", and I stopped. Nothing that reads the
predicate was changed.

### 3.2 What would unblock it (a decision, not done here)

One of:
- (a) setup and the lane bootstraps create `.perry/config.jsonl`
  (`perry-config set …`) before writing any markdown, and the docs stop
  naming `.perry/config.md`;
- (b) the criterion keeps one markdown marker for a transition;
- (c) the user accepts that those shapes read as not installed until their
  first store write.

(a) touches `SKILL.md`, `work/`, `goals/`, `decide/` and `reference/`; the
first two are 3c's territory.

## 4. The board's title and prose

- **Rule.** The title is `parsers § project_name(project_root)`. It would read a
  `.perry/config.jsonl` setting if the schema declared one, and it declares none
  (keys on this repository: `document_language`, `chat_language`,
  `repo_layout`, `state_root`, `pmo_repo_path`, `code_repo_path`,
  `last_updated`), so the title is the project root's directory name.
  - **No config key was added.**
  - `perry-state § project.name` calls the same function. Before, it read
    `BOARD.md`'s H1 and fell back to the STATE root's name (`perry`).
- **What prints.** The template's `#` headings and its tables. The `>`
  instruction block, the `Last updated: {{YYYY-MM-DD}}` line and the Top risks
  HTML comment are not printed. Blank runs collapse to one.
  - A heading that still carries a `{{…}}` placeholder refuses the render
    (exit 1, nothing on stdout), because no declared source fills it. The
    shipped template has none.
- **Measured.** This repository's copy of the `git archive` with the file present:
  - `perry-tasks board` went from 156,083 B (`# Board — {{project name}}`,
    prose included) at base to 155,011 B (`# Board — Perry`) at final;
  - with the three cadence fixture rows, 155,327 B;
  - `{{` appears 0 times in either final output.
- **`DECLARED_BOARD_CHOICES` "prose".** This is D1's C1, rewritten. The guard
  that pinned C1 — `test_bin_surface § OWN_OUTPUT`'s board fingerprint
  `# Board — {{project name}}` — now pins
  `## Top risks (one-line; full list in `PROJECT_STATE.md`)`, a template heading
  no fixture board on disk carries.

## 5. The 3a gaps

### 5.1 `perry-diagnose` (3a R3, L11)

- `open_user_asks`: when `asks.jsonl` loads, the open asks are its records whose
  `status` `ask_is_answered` calls unanswered, cited `perry/asks.jsonl:<line>`.
  The file is not read.
- `scan_work_modes`' intake count: `len(intake.jsonl)` when it loads; the
  evidence line names `intake.jsonl`.
- Measured by `test_board_less_gaps` in three states: absent, rendered, and
  forged (the forged file answers `USER-001`, opens `USER-777` and carries five
  intake rows). All three give the store's answer.

### 5.2 The `perry-lint` checks that went quiet (3a R5, L9)

| check | before, no file | now | why |
|---|---|---|---|
| `check_verification` | `return findings` before the event pass | board pass skipped, event pass runs | the event pass judges every `perry-task done`; skipping it with the file silenced every tool-made closure |
| `check_reviews` | `return findings` before `live`, the event pass and every `review` check | `live`/`rungs` from the store's open records, everything below runs | the rows the file would carry are exactly those records |
| `resolves_somewhere` (id tokens) | looked only in the file and the event log | with no file, `ids_the_board_would_carry` (open tasks, asks, risks, cadence) | a card citing an open task or an ask read as dangling |
| `done-needs-evidence` (`:1571`) | returns quietly | **left quiet, argued** | its subject is a `done` ROW on the board. A rendered board carries no terminal row (`DECLARED_BOARD_CHOICES` "which rows"), so a rendered file gives this check nothing either; only a hand-kept row can fire it. With no file there is no hand-kept row. `check_verification`'s event pass is what judges tool closures |

The test uses the same fixture with the file absent and rendered from the
stores, and asserts findings equal across the two. Each fix has a mutation.

### 5.3 `project.name`

§ 4. Measured: base, file deleted: `"perry"`. Final, file deleted: `"Perry"`.
Present and deleted are equal at final.

### 5.4 A shipped `semantics` entry cannot leave (3a R7)

`tests/fixtures/shipped-semantics.json` records the 17 entries the seven
payloads ship, by version and fields:
- `perry-task/list` 11;
- `perry-events/list` 2;
- `perry-goals/list` 3;
- `perry-asks/list` 1;
- the other three 0.

`TestAShippedEntryNeverLeaves` asserts three things:
- every recorded entry is still in its payload;
- every live entry is recorded;
- the record covers every contract.

Mutation M9 empties `perry-asks/list`'s array and reddens it; G12 adds an
unrecorded entry and reddens the other direction.

## 6. Payload diff and write matrix

### 6.1 Payload diff

**Method.** `scratchpad/payload_diff.py` and `analyse_pd.py`:
- two copies per tool tree of that tree's own state: `.perry/config.jsonl`,
  `.perry/events.jsonl`, and `perry/` with `evidence/` symlinked;
- both copies in a directory named `Perry`;
- `perry/BOARD.md` removed from one copy;
- `PERRY_HOME` set to the tree, `HOME` to an empty directory;
- key paths compared with the copy root and the tree path normalised, and
  clocks masked;
- `perry-lint` compared as counts, stats and a set of findings.

**Fixtures.**
- `live` is the repository's state (0 cadence rows).
- `cadence` puts three rows into `## Cadence`:
  - periodic: `CAD-001 weekly 2026-09-21`;
  - aperiodic: `CAD-002 continuous n/a`;
  - prose: `CADENCE-003 monthly **2026-08-31**（7 月版 ✅ …）`.

  At final they are also imported into `cadence.jsonl` before the file is
  removed.

**Final, present → deleted** (both fixtures):

| surface | exit | differs |
|---|---|---|
| `perry-task list --json`, `list --all --limit 0 --json` | 0 / 0 | `conformance.missing_projection` `""` → path — file exception (3a) |
| `perry-task asks --all --json`, `events --json` | 0 / 0 | equal |
| `perry-state --json` | 0 / 0 | `board.lines` 188 → 0 (cadence: 190 → 0), `board.last_updated` → `""` — file exceptions. **`project.name` equal** (3a's `Perry` → `perry` is gone) |
| `perry-state --section cadence` | 0 / 0 | **equal** (cadence fixture: 3 items, cells as written) |
| `perry-goals`, `perry-decide`, `perry-knowledge list --json` | 0 / 0 | equal |
| `perry-tasks board` | 0 / 0 | **byte-equal** (155,011 B live; 155,327 B cadence) |
| `perry-lint --json` | 0 / 1 | + `missing-file BOARD.md` (3c), + the `*-store-drift-uncheckable` warnings, including `cadence-store-drift-uncheckable` on the cadence fixture — 3a § 2.3's set plus cadence |

**Base → final, file present:**

| surface | differs | reason |
|---|---|---|
| `list`, `list --all`, `asks --all`, `events`, `perry-state --json`, `§ cadence`, `goals`, `decide`, `knowledge` | **equal** (both fixtures) | — |
| `perry-tasks board` | `# Board — {{project name}}` → `# Board — Perry`; 156,083 → 155,011 B (live), 155,327 B (cadence); the prose block and the Top risks comment gone; the cadence fixture's rows printed from the store | Amendment (4) item 3 |
| `perry-lint --json` | `cadence_store_drift` block added (`store_present`, `comparison_performed`, `records`, `drifted`); census line `no cadence.jsonl` / `cadence store: 3 record(s), 0 row(s) drifted` | the census covers every declared store |

**Base → final, file deleted:**

| surface | differs | reason |
|---|---|---|
| `perry-state --json` | `project.name` `"perry"` → `"Perry"`; cadence fixture: `board.cadence` 0 → 3, `board.tasks[]` gains the three cadence-as-task rows | § 5.3; the store is read |
| `perry-state --section cadence` | cadence fixture: `count` 0 → 3, the three items, `overdue: [CADENCE-003]` | 3a's R1, closed |
| `perry-tasks board` | as with the file present | § 4 |
| `perry-lint --json` | `cadence_store_drift` block; cadence fixture: `cadence-store-drift-uncheckable` | as above |
| everything else | equal | — |

**Found here and fixed:** the first final capture had
`NS-01 perry/cadence.jsonl — holds 1 file(s) Perry did not write` in the
cadence fixture's lint. `looks_like_perry_record` knew tasks, risks, asks,
intake, okr, config and linkage records, and not cadence. Fixed in `32c416ee`
and guarded (`test_the_store_is_claimed_as_a_file_perry_wrote`, mutation G15).
Re-captured at `32c416ee`, base → final present lint differs only in the four
`cadence_store_drift` keys.

### 6.2 Write matrix

**Method.** `scratchpad/write_matrix.py`:
- the fixture is 3a's (`TASKS`, `ASKS`, `RISKS`, `INTAKE`, `CONFIG` from the
  final archive's `test_board_less_reads_and_writes.py`), plus the three
  cadence rows;
- in the present state `BOARD.md` is that tree's own `perry-tasks board`
  render;
- at base, which has no store, the cadence rows are typed into that render's
  `## Cadence`, base's only cadence register;
- every write runs in both states on fresh copies, with `PERRY_HOME` set to
  the tree.

| write | base exit present / deleted | final exit present / deleted | final: stores, events, journal equal across states | final: present file re-rendered | final: deleted created `BOARD.md` |
|---|---|---|---|---|---|
| add, start, track, stage, ask, answer, next, risk-add, risk-clear, done, drop, intake, route, resolve-intake, intake-sweep, retitle, rung, evidence, prioritize, status, depends (21) | 0 / 0 | 0 / 0 | yes | yes | no |
| summary, design-link | 0 / 0 | 0 / 0 | yes | no — no board column (as 3a) | no |
| purge | 0 / 0 | 0 / 0 | yes | **no** — see below | no |
| **cadence-add** | 0 / **1** | 0 / **0** | yes | yes | no |
| **cadence-done** (periodic `CAD-001`) | 0 / **1** | 0 / **0** | yes | yes | no |
| **cadence-done** (aperiodic `CAD-002`) | 0 / **1** | 0 / **0** | yes | yes | no |
| **cadence-done** (prose `CADENCE-003`) | 0 / **1** | 0 / **0** | yes | yes | no |

- **Base deleted.** Every cadence write refuses: "`cadence-add` writes its row
  into the board file and nowhere else…" (3a's stop).
- **Base present → final present.** Exit codes, events and journal text are
  equal for every write. The stores differ only in `cadence.jsonl`, which base
  does not have.
- **Cadence rows after each cadence write.** Read by `perry-state --section
  cadence`, they are equal across all three runs: base present (board-held
  register), final present, and final deleted.
- **The prose row keeps its prose until it is run.** `cadence-done CADENCE-003
  --on 2026-09-01` stamps `next_due 2026-10-01`, `last_run 2026-09-01` and the
  evidence path, and the other rows are byte-unchanged.
- **`purge`.** 3a's base table says the file was re-rendered. It moved only by
  its `> Last updated:` stamp: a purged record is terminal and has no line. The
  board `perry-tasks board` prints since § 4 carries no such line, so nothing in
  a rendered file moves. `test_board_less_reads_and_writes` exempts `purge`
  from its re-render assertion, with that reason.

## 7. Tests and mutations

### 7.1 Tests

**New modules:**

| module | tests | alone, median of 3 |
|---|---|---|
| `tests/test_cadence_store.py` | 26 | 1.29 s (1.24 / 1.29 / 1.48) |
| `tests/test_board_less_gaps.py` | 6 | 0.26 s (0.57 / 0.26 / 0.20) |

- The two modules' test counts come from their `--ids` runs.
- Both are timed with `python3 -m unittest` from `tests/`, load1 9.17, and
  entered in `tests/durations.json` under source `2026-09-14-task237-d3b`.

**Where expectations come from.**
- The records the module writes.
- For the import, the cells the module types into the board it builds.
- The arguments a command was given.
- `COLUMN_FIELD`, written in the test.

A board appears only absent, forged, rendered from the stores, or as the
import's input.

**Changed tests, each with its reason in place:**

| test | change | reason |
|---|---|---|
| `test_board_less_reads_and_writes` | cadence writes join `WRITES`; the refusal test is gone; stores compared include `cadence`; `purge` exempt from the re-render assertion | 3a's stop is resolved; § 6.2 `purge` |
| `test_cadence § test_a_periodic_row_with_an_unreadable_due_cell_is_a_finding` | the unreadable cell is planted in the store record | the store is the register; a hand edit to the file is drift |
| `test_duplicate_ids_are_refused` | `REGISTER_ID_KEYED` includes `cadence`; `REGISTER_SPEC["cadence"][5]` is set | cadence is id-keyed |
| `test_register_store_invariant § test_every_section_event_declares_the_store_it_touches` | expects the empty set | cadence was the one exception |
| `test_bin_surface` | registers include `cadence`; `cadence-write` fingerprint; board fingerprint (§ 4); **the direction-B ratchet: literal 15 → the set derived from the declared registers** (5 pairs per prefixed register, now 20) | a fifth register brings the same five shared reads; a literal 20 would admit any five |
| `test_store_drift` | `CENSUS_LINES` gains `cadence.jsonl` | a declared store has a census line |
| `test_handed_back_root` | `PASTEABLE_WRITER_PHRASES` 68 → 72 | four new rooted hand-backs, named in the comment |
| `test_header_index_is_the_only_fold` | `is_cadence_register_header` watched and driven | the sibling predicates are |
| `test_decoration_changes_nothing` | both projects under a directory named `Perry` | `project.name` is the directory's name |
| `test_semantics_on_every_payload` | `TestAShippedEntryNeverLeaves` | § 5.4 |

### 7.2 Mutations

**Method.** `scratchpad/mutate.py`, on `git archive 32c416ee` under the scratchpad.
For each mutation:
- the anchor is asserted to occur exactly once, and every one did;
- every `__pycache__` is removed;
- the named modules run with `--ids`, and the red test ids are collected;
- the file is restored and compared with `git show 32c416ee:<path>`.

The control, run unmutated before the battery over all 138 tests of the
modules used, had no red. **Every restore compared equal.**

| # | mutation (file) | red: named tests | result |
|---|---|---|---|
| M1 | **a `BOARD.md` read put back into the cadence read**: `load_snapshot` passes `cadence=None` (`viewer/parsers.py`) | NoBoard and Forged `.test_perry_state_carries_every_stored_cell_as_written`; Forged `.test_no_forged_row_reaches_a_payload` | RED (3) |
| M2a | **one put back into the cadence write**: `cadence-add` / `cadence-done` removed from `REGISTER_EVENTS`, so the row lands in the board only (`bin/perry-task`) | `test_board_less_reads_and_writes …test_each_write_lands…`, `…test_a_write_is_the_same…`; `test_cadence_store …test_add_lands_the_record…`, `…test_done_recomputes…`, `…test_an_aperiodic_frequency…`, `…test_a_row_deleted…shrink`, `…substitution`, `…test_a_repeated_id…` | RED (8) |
| M2b | the declared write board built without the cadence store (`bin/perry_store.py § BOARD_STORES`) | the two write tests in `test_board_less_reads_and_writes`; `test_cadence_store` board-print ×2, lint drift, and five write tests | RED (10) |
| M3 | **the import loses a prose cell**: `next_due` cut at `（` (`perry_store § cadence_record`) | `TestTheImport.test_every_cell_is_stored_as_written`; `…test_done_recomputes_the_due_date_and_leaves_every_other_cell_alone`; `…test_a_hand_edit_to_a_prose_cell_is_drift…` | RED (3) |
| M4 | drop `installed` from one payload | — | **not run: the predicate STOP (§ 3)** |
| M5 | accept `BOARD.md` in the predicate | — | **not run: STOP** |
| M6a | **one `{{` printed**: the title's placeholder left unfilled (`declared_board`) | `test_the_title_is_the_project_directory_name`, `…heading_placeholder…refuses`, `…every_template_heading…`, board-print ×2, and seven write/lint tests the refusal stops | RED (12) |
| M6b | the template's prose lines printed again (`declared_board`) | `test_no_placeholder_is_printed`, `test_no_template_prose_is_printed` | RED (2) |
| M7 | `board` printing on a non-installed directory | — | **not run: STOP** |
| M8 | **`perry-diagnose` reads asks from the board again** (`if False:`) | `TestDiagnoseReadsTheRegisterStores.test_open_asks_are_the_stores_unanswered_asks` | RED (1) |
| M9 | **a `semantics` entry removed**: `perry-asks/list` ships `[]` (`bin/perry-task`) | `TestAShippedEntryNeverLeaves.test_no_shipped_entry_left_a_payload_or_changed_its_fields` | RED (1) |
| G1 | import: the no-handle row guard removed (`perry-tasks`) | `TestTheImport.test_it_refuses_a_row_it_would_not_store` | RED (1) |
| G2 | import: the unstored-column guard removed | `TestTheImport.test_it_refuses_a_column_no_field_holds` | RED (1) |
| G3 | import: the claim guard removed | `TestTheImport.test_it_refuses_when_the_claim_is_not_declared` | RED (1) |
| G4 | the unfilled-heading-placeholder guard removed (`perry_store`) | `test_a_heading_placeholder_no_source_fills_refuses` | RED (1) |
| G5 | the ratchet: `cadence-build` reads `--write` (`if "--write" in flags: return 2`) | `test_bin_surface …test_the_pairs_direction_b_cannot_see_are_all_shared_reads`, `…test_every_flag_only_this_subcommand_reads_is_declared_by_it` | RED (2) |
| G5b | the same read as a dead assignment (`_probe = "--write" in flags`) | none | **GREEN — equivalent**: an unused binding changes no behaviour, and `tests/surface_reads.py` counts a read only where its result flows onward (a condition or a bound argument). This was the first shape of G5 I ran, and it is recorded rather than dropped |
| G5c | the ratchet's derived set without `cadence-` (test module) | `…test_the_pairs_direction_b_cannot_see_are_all_shared_reads` | RED (1) — the set assertion is live on its own, not only its exclusive-read sibling |
| G6 | `check_verification` returns again with no file (`perry-lint`) | `…test_closures_in_the_event_log_are_judged_with_no_file` | RED (1) |
| G7 | `check_reviews` returns again with no file | `…test_reviews_run_on_the_stores_rows_with_no_file` | RED (1) |
| G8 | `resolves_somewhere` ignores the stores with no file | `…test_a_source_naming_an_open_task_resolves_with_no_file` | RED (1) |
| G9 | `perry-diagnose` intake count from the board | `…test_the_intake_count_is_the_stores` | RED (1) |
| G10 | `project_name` from the STATE root (`parsers`) | `TestProjectNameIsTheSameRule…`, `test_the_title_is_the_project_directory_name` | RED (2) |
| G11 | `check_cadence_store_drift` not called | `…test_with_no_file_it_is_uncheckable…`, `…test_a_hand_edit_to_a_prose_cell_is_drift…` | RED (2) |
| G12 | an unrecorded `semantics` entry added | `…test_every_live_entry_is_recorded`; `TestNothingWasInventedToFillThem.test_the_minor_that_added_the_key_is_not_itself_an_entry` | RED (2) |
| G13 | the rule noun back to `key[:-1]` (`perry-task`) | `…test_a_repeated_id_in_the_store_is_refused_by_its_lint_rule` | RED (1) |
| G14 | `DECLARED_BOARD_REGISTERS` without cadence | board-print ×2, lint drift, five write tests | RED (8) |
| G15 | `looks_like_perry_record` without the cadence tuple | `…test_the_store_is_claimed_as_a_file_perry_wrote` | RED (1) |

**No mutation of a real defect stayed green.** G5b is the one green, an
equivalent mutation, argued above.

**Not mutated:**
- the `test_board_less_reads_and_writes` `purge` exemption, which loosens a
  guard rather than adding one;
- the pinned-count updates in § 7.1, which are the guards themselves being
  re-pointed. Each was red before its update in the first full suite run, which
  is the mutation evidence that it is live.

## 8. Suite

| run | tree | modules · tests | red modules · red tests | tree guard |
|---|---|---|---|---|
| `bash tests/run`, foreground, nothing written during it | `982ac9ce` | 136 · 3,935 | 6 · 9 | "nothing … moved" |
| `bash tests/run`, final | SUITE_FINAL_TREE | SUITE_FINAL_COUNTS | SUITE_FINAL_RED | SUITE_FINAL_GUARD |

**First run.** The reds were the three pre-existing ones and six caused here.
- **Caused here:** each of the six was re-run alone, red at this code and
  green at base `37adba9e` (`python3 -m unittest <ids>` against the base
  archive's `tests/`: 6 tests, OK). Each was then fixed as in § 7.1.
  - `test_decoration_changes_nothing …on_a_bolded_board`
  - `test_handed_back_root …count_of_pasteable_writer_hand_backs_is_held`
  - `test_header_index_is_the_only_fold …the_uncovered_remainder_is_the_measured_one`
  - `test_store_drift` ×3 (`TestTheCensusCoversEveryDeclaredStore`)
- **The harness** also rejected the durations stamp as undefined; the source
  is now declared.

SUITE_FINAL_NOTE

## 9. Rows this work names (none minted)

- **R1 — the `installed` predicate needs a decision before it can land** (§ 3).
  Setup and the lane bootstraps must create `.perry/config.jsonl`, or the
  criterion must keep a transition marker, or those shapes accept
  `installed: false` until their first store write. Everything in Amendment (4)
  except the board title and prose waits on it.
- **R2 — aiMark's `per task` cannot be run.** `check_frequency` refuses it, so
  `cadence-done CAD-001` needs `--frequency`, which rewrites the stored cell. The
  vocabulary (`parsers._APERIODIC`) lacks `per task`; Gimegime's
  `continuous` / `hourly` are in it.
- **R3 — no verb retires a cadence row.** With a store, deleting the row from
  the file is drift and the next write refuses or reports it (§ 2.4).
- **R4 — the ask import has the two holes the cadence import refuses.**
  - A row with no `USER-` handle, and a column no field holds, pass its byte
    gate and are dropped from the store.
  - `Idle` is the deliberate exception.
  - The risks import likely shares the row case; not measured.
- **R5 — setup and adoption docs still write `.perry/config.md`** (`SKILL.md`
  step 3, `reference/adoption.md § 4` row 1, `reference/i18n.md:17`,
  `work/reference/bootstrap.md:51`). The config claim's note and
  `reference/diagnose.md:476` name `perry-config write --from-file`, which
  ADR-019 removed. These are from the enumeration agent's sweep; I verified
  `SKILL.md`, `bootstrap.md` and `adoption.md` myself.
- **R6 — `looks_like_perry_record` is a hand-kept union.** A new id-keyed store
  draws NS-01 until someone adds its tuple, and cadence is the second register
  to hit it. It could derive from `claims[]` and the stores' field tuples.
- **R7 — `resolve_state_root` silently ignores a declared state root when
  handed an unresolved project root** (`/var/…` vs `/private/var/…` on macOS),
  because the containment check compares a resolved child with an unresolved
  parent. Every tool resolves first, and my test did not.
- **R8 — `test_contract_page_snippets.py` still has no durations entry**
  (3a R6, unchanged).

## What I did not check

- **Everything behind the STOP:** the four directory shapes of Amendment (4)'s
  verification list, the contract bumps, the parity re-record, `board`'s
  refusal.
- **A localized cadence register.** The glossary aliases (`例行节奏`,
  `例行任务`, `下次到期`) resolve through `norm`, but no zh board was imported.
- **`### ` sub-groups inside `## Cadence` under the import.** `markdown_tables`
  keeps one table across them, so it should import. Not built.
- **A malformed `cadence.jsonl` with no file.** `load_register_store` returns
  `None`, the section is parsed from a file that does not exist, and the
  reader reports 0 rows at exit 0. A write refuses (`declared_write_board`
  validates). The lint check reports `cadence-store-unreadable`. The reader
  path was not exercised — 3a's same caveat, now for a fifth store.
- **`--dry-run` cadence writes; concurrency.**
- **`/perry relocate` and `perry-lint --claims` rendering the new claim**
  beyond the suite.
- **The viewer** (`viewer/templates/`) with a cadence store.
- **`cadence-done` on an imported Gimegime row whose frequency is readable but
  whose `Next due` is prose.** § 6.2 ran the fixture's equivalent (`CADENCE-003`);
  the real copy was not written to.
