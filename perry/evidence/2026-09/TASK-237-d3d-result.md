# TASK-237 deliverable 3d — result

Branch `worktree-agent-a436e340cf180bb31`. Acceptance:
`perry/evidence/2026-09/TASK-237-spec.md § Amendment 2026-09-14 (8) § Deliverable 3d`.
Documents and the two named test pins only. No code, schema, contract, store or
`ARCHITECTURE.md` change.

Commits:
- `9b9e064b` — the signed contract change, the git-boundaries re-pin, the sweep and R10 lines;
- the commit carrying this file.

## 0. Base check

| | |
|---|---|
| arrived at | `583f024f97d8736468e61469e2667de85eeb56c4` |
| tree | clean (`git status --porcelain` empty) |
| `git merge-base --is-ancestor e7a77111 HEAD` | exit 1 |
| action | `git merge --ff-only e7a77111` on this branch only; re-asserted: ancestor |

## 1. The signed contract change and the `SKILL.md` compressions

**Exactly the signed text** (3c result § 5.3, V5 2026-09-14):

| place | before | after |
|---|---|---|
| `SKILL.md § The hand-off contract`, `work` row | `` `BOARD.md` (incl. `## Intake`, `## Cadence`), `journal/`, … `` | `` `tasks.jsonl` + its 4 register stores (`perry-tasks board` prints them), `journal/`, … `` |
| same section, refusal cases | `` `goals` writing `BOARD.md` `` | `` `goals` writing `tasks.jsonl` `` |
| `tests/test_ownership.py § SCHEMA_PATH_TO_CONTRACT` | `"BOARD.md": "BOARD.md"` | `"BOARD.md": "tasks.jsonl"` |
| `tests/test_ownership.py § FOREIGN_WRITES` | `goals` and `decide` forbid `"BOARD.md"` | both forbid `"tasks.jsonl"` |
| `tests/test_ownership.py § test_the_contract_names_concrete_refusal_cases` | `` "`BOARD.md`" `` | `` "`tasks.jsonl`" `` |
| `goals/SKILL.md:51` | ``PMO is the only writer of `BOARD.md`, `journal/`, …`` | ``PMO is the only writer of `tasks.jsonl`, `journal/`, …`` |
| `reference/adoption.md:29` | `` `pmo` still writes `BOARD.md` `` | `` `pmo` still writes `tasks.jsonl` `` |

No other ownership fact moved: the rest of the `work` row, the `goals` and
`decide` rows, the other two refusal cases and the sign-off block are
byte-identical.

**Why the map's KEY is still `"BOARD.md"`.** `SCHEMA_PATH_TO_CONTRACT` is keyed by
`schema/state-schema.json § files[].path`, and `files[id=board]` is still
declared there (3c made it non-required; it did not remove it). Only the
contract CELL the key maps to is the signed text. Changing the key would be a
schema edit, which hard limit 1 forbids.

**Budget.** Measured, not the spec's estimate:

| state | `SKILL.md` bytes | vs 20,480 |
|---|---|---|
| base `e7a77111` | 20,461 | 19 B headroom (the spec said about 23) |
| signed row + refusal case | 20,491 | 11 B over; the row cost **+30 B** (the spec said about 45) |
| after the compression | **20,457** | 23 B headroom |

**Compressions (one):**

| where | before | after | bytes |
|---|---|---|---|
| `SKILL.md § Mandatory first move`, step 2, "When `stale: true`" | ``It stays a recommendation, never an automatic retirement: `abandoned` is set by the user, never by Perry deciding a run has gone stale.`` | ``It stays a recommendation: `abandoned` is set by the user, never by Perry deciding a run has gone stale.`` | −34 |

The dropped clause restates the clause after the colon: an automatic retirement
is Perry setting `abandoned` itself, which the kept clause forbids. The rule — the
user retires a stale run, Perry never does — is unchanged. No test pins the
dropped words (`grep -rn 'never an automatic retirement' tests/` is empty).

## 2. `git-boundaries.md` and the re-pin

`work/reference/git-boundaries.md`, both inside the governed span
`## Git Role Boundaries` → `## Time Estimation for Coding Agent Tasks`:

| line | before | after | why |
|---|---|---|---|
| 11 (PMO row, Commits) | ``work docs (`BOARD.md`, `journal/`, …)`` | ``work docs (`tasks.jsonl`, `journal/`, …)`` | item 2. **Replaced, not removed**: the Commits column lists what the PMO commits, and every PMO task write lands in `tasks.jsonl`; removing it would leave that list naming no file the task writes land in, and the signed `work` row now names `tasks.jsonl` first. |
| 26 (split layout) | ``If `.perry/config.md` records `Repo layout: split` `` | ``If `.perry/config.jsonl` records `Repo layout: split` `` | R10; line 26 sits before the end anchor at line 28, so it is **inside the pinned span** and folds into the same re-pin |

`git diff e7a77111 -- work/reference/git-boundaries.md`: those two tokens, nothing else.

| | base `e7a77111` | `9b9e064b` |
|---|---|---|
| span, measured (`governed_text`) | 4,267 chars / 24 lines | 4,273 chars / 24 lines |
| SHA-256 | `e89b1321cd55a7a910322b6045e33b6763717c760d753175816f4a53a5dc45af` (= the old pin) | `0a85b4b6d716887b1edd45dd30337276c6aad90ccc7c178a746e65088bdecaec` |

The pin comment said "4,269 chars / 26 lines" before this round; measured at
base it was already 4,267 / 24. The new comment carries the measured count, the
reason, and the previous digest, in the form TASK-381's re-pin used. The commit
message of `9b9e064b` states the reason: the file named was deleted by
TASK-237 3c.

## 3. Sweep lines (3c § 8.2 `sweep (R3)`), before and after

Located by content on `e7a77111`; line numbers are the base's.

### `work/SKILL.md`

| line | before | after |
|---|---|---|
| 3 (frontmatter) | `Maintains BOARD.md (live working memory — current open work only, ≤200 lines), journal/…` | `Maintains the task board (tasks.jsonl and its register stores, printed by perry-tasks board — live working memory, current open work only), journal/…` |
| 117 | `` `BOARD.md`, `journal/`, ADRs, evidence, … are written in `Document language` `` | `` Task records, `journal/`, ADRs, evidence, … `` |
| 183 | `"BOARD.md is 240 lines, over the 200-line cap → run triage …"` | ``"A `BOARD.md` this project still holds is 240 lines, over its 200-line cap → run triage …"`` |
| 186 | ``the mutation did not land in `BOARD.md` `` | ``the mutation did not land in `tasks.jsonl` `` |

Line 3 keeps every trigger word (`board`, status, weekly planning, blocker
triage, delegation, …) and drops only the claim that a `BOARD.md` is maintained,
with its `≤200 lines`. The printed board has no line cap
(`work/reference/state-files.md:49`, written by 3c), so the cap goes with the file
rather than moving to the printed board. Line 183 is scoped to a held board, the
same scope `state-files.md:49` and `subcommands.md:380` already carry.

### `goals/SKILL.md`

| line | before | after |
|---|---|---|
| 3 (frontmatter) | `…the work lane, which appends approved ones to BOARD.md.` | `…which appends approved ones to the task store (tasks.jsonl).` |

Trigger words unchanged. (Line 51 is § 1's signed line.)

### `work/reference/conversational.md`

| line | before | after |
|---|---|---|
| 74 | ``Inside `BOARD.md`, `journal/`, … — those files are reference material`` | ``Inside task records (and the board `perry-tasks board` prints from them), `journal/`, … — those are reference material`` |

### `work/reference/subcommands.md`

| line | before | after |
|---|---|---|
| 101 | ``if intake is pushing `BOARD.md` toward the 200-line cap, **say so as a finding** …`` | ``if intake is pushing a `BOARD.md` the project still holds toward its 200-line cap, **say so as a finding** … The board `perry-tasks board` prints is not a file and has no line cap, so a board-less project has no cap for intake to push against.`` |
| 440 (+ 443 in the same sentence) | ``BOARD.md § Top risks` is a table … writes the board row, the journal line and the event`` | ``## Top risks`, as `perry-tasks board` prints it from `risks.jsonl`, is a table … writes the record, the journal line and the event`` |
| 458 | ``(TASK-040, ADR-007 applied to this register the way it was applied to `BOARD.md`)`` | ``… the way it had been applied to `BOARD.md`, the file TASK-237 later deleted)`` — now history |
| 478 | ``the severity `store-drift` uses for `BOARD.md` `` | ``the severity `store-drift` uses for a `BOARD.md` a project still holds`` — now held |
| 518 | ``once `BOARD.md § Top risks` is a table, that table is the register and `PROJECT_STATE.md` is no longer merged into it`` | ``once `## Top risks` is a table on a held board, or `risks.jsonl` exists, that register is the one read and `PROJECT_STATE.md` is no longer merged into it`` |
| 612 | ``Creating a queue-mode row also creates `BOARD.md § Intake` if it is absent, with its three columns … a section nothing creates …`` | ``Creating a queue-mode row also creates the intake register, `intake.jsonl`, if it is absent — printed by `perry-tasks board` as `## Intake`, with its three columns … a register nothing creates …`` |

**Each claim that describes a tool was measured**, not reasoned:
- line 518 is `viewer/parsers.py § load_snapshot`: `risks.jsonl` is read when
  present, else a board table, else the bullet merge.
- line 612 was run on a scratch project with no board (the `e7a77111` archive's
  tools, `PERRY_HOME` set to it). A queue-track `perry-task add` printed
  `wrote TASK-001 (add) → tasks.jsonl + intake.jsonl + journal + event`, and
  `intake.jsonl` appeared. After one `perry-task intake`, `perry-tasks board`
  printed `## Intake`.

### `modes/pipeline.md`

| line | before | after |
|---|---|---|
| 50 | ``perry-task drop` removes the row: `BOARD.md` holds open work`` | ``perry-task drop` takes the row off the board: `perry-tasks board` prints open work`` |

Measured on the same scratch project: after `perry-task drop TASK-002`, the
record stays in `tasks.jsonl` with `"status": "dropped"`, and `perry-tasks
board` prints no `TASK-002` row. "Removes the row" is therefore true of the
printed board, not the store, and the line now says the board.

### `modes/inquiry.md`

| line | before | after |
|---|---|---|
| 70 | ``BOARD.md` has no nesting, so the edge is a cell`` | ``The board has no nesting (`perry-tasks board` prints flat tables), so the edge is a cell`` |

### `modes/queue.md` — the intake section

| line | before | after |
|---|---|---|
| 76 (heading) | ``### `BOARD.md § Intake` `` | ``### `## Intake` `` |
| 78 | `Untriaged external requests, one line each, with the date they arrived:` | … `The records are intake.jsonl; perry-tasks board prints them as this section for a person, and perry-task list --json carries them as intake for a program:` |
| 94–95 | ``It lives inside `BOARD.md` rather than a separate `INTAKE.md` because DESIGN-003 decision 3 chose zero new claimed paths, and `BOARD.md` is already a path Perry claims.`` | ``It is a register beside the task store rather than a separate `INTAKE.md`. DESIGN-003 decision 3 first put it inside `BOARD.md`, so that it claimed no new path; that file is deleted (TASK-237), and the register is `intake.jsonl`, declared in `schema/state-schema.json § claims`.`` |
| 99–106 (the 200-line cap argument) | "The cost of that choice is real … untriaged requests compete with the 200-line board cap. **That cost is the feature.** An intake that overflows the board … surface it as a finding, not … raise the cap … If it recurs, revisit decision 3 — do not quietly relax it." | "The design's risk table named what the file placement cost: untriaged requests competed with the 200-line board cap, and this page argued that cost was the feature. **That clause is dropped: the board `perry-tasks board` prints is not a file and has no line cap**, so there is no cap for intake to overflow. A `BOARD.md` a project still holds keeps its cap (`work/reference/state-files.md`), and intake pushing it there is still reported as a finding (`work/reference/subcommands.md § triage`)." |
| 137–141 | ``the same live/history split `BOARD.md` and `journal/` use … a board could overflow on a year of recorded drops, which would destroy the argument above: overflow is supposed to mean …`` | ``the same live/history split the board and `journal/` use … a year of recorded drops would read as intake pressure, which is supposed to mean …`` |

**Which I did: dropped the clause, not restated it.** Restating the cap argument
for the rendered board would need a size the printed board is measured against,
and there is none: `perry-tasks board` has no line cap. Inventing one is a new
rule (hard limit 2). The held-board case keeps its cap and its finding, which
are already rules elsewhere (`state-files.md:49`, `subcommands.md:101`, `:380`).
The "live/history" paragraph kept its point — discharged rows must leave, or
recorded drops read as pressure — without leaning on the dropped argument.

### `reference/`

| file:line | before | after |
|---|---|---|
| `i18n.md:214` | ``Rule 1 applies to **chat**, not to `BOARD.md`.`` | ``… not to a task record.`` |
| `adoption.md:16` | ``reaches `OKR.md` / `BOARD.md` / `design/` `` | ``reaches `OKR.md` / `tasks.jsonl` / `design/` `` |
| `adoption.md:52` | ``| `BOARD.md` tasks | **Evidence** …`` | ``| Tasks (`tasks.jsonl`) | **Evidence** …`` |
| `router-subcommands.md:18` | ``reaches `OKR.md` / `BOARD.md` / `design/` `` | ``reaches `OKR.md` / `tasks.jsonl` / `design/` `` |
| `diagnose.md:404` | ``touches `OKR.md`, `BOARD.md`, or `design/` `` | ``touches `OKR.md`, `tasks.jsonl`, or `design/` `` |
| `input-quality.md:4` | ``… or in `BOARD.md`.`` | ``… or in a task record (`tasks.jsonl`).`` |
| `input-quality.md:81` (heading) | ``## §4 — Task rubric (`BOARD.md` row / `plan-week` proposal / `add-task`)`` | ``## §4 — Task rubric (task record / `plan-week` proposal / `add-task`)`` |

The `input-quality.md` heading keeps its `§4 — Task rubric` prefix, which every
`input-quality.md § 4 Task` pointer resolves against; `test_pointers_resolve` is
green.

### `schema/` — three sweep lines NOT changed (hard limit 1)

3c's `sweep (R3)` row also lists `schema/task-list-contract.md:92`, `:104` and
`schema/goals-list-contract.md:167`. Those are contracts; this round may not
change a contract. They stay, and are named in § 8.

## 4. R10: `.perry/config.md` mentions

| file:line | before | after | kind |
|---|---|---|---|
| `reference/glossary.md:144` | ``declared in `.perry/config.md § Tracks` `` | ``declared as a track record in `.perry/config.jsonl` (`perry-config track`)`` | current |
| `reference/snapshot.md:129` | ``a `## Tracks` table in `.perry/config.md` — a tier-1 file the user owns and edits directly … `perry-lint` validates the `Mode` and `Default rung` cells whenever the section exists and skips it entirely when it doesn't`` | ``the track records in `.perry/config.jsonl`, which the user owns and writes with `perry-config track` … `perry-lint` validates each record's `mode` and `default_rung` whenever the store exists and reports the absence when it doesn't`` | current |
| `reference/input-quality.md:21` | ``follows `.perry/config.md § Document language` `` | ``follows the `Document language` setting in `.perry/config.jsonl` `` | current |
| `work/reference/subcommands.md:348` | ``Declare one in `.perry/config.md § Tracks` `` | ``Declare one with `perry-config track ops --sla <value>` `` | current |
| `work/reference/subcommands.md:610` | ``A track named in no row of `.perry/config.md § Tracks` is refused`` | ``A track with no record in `.perry/config.jsonl` (`perry-config show`) is refused`` | current |
| `work/reference/subcommands.md:807` | ```Default rung` from `.perry/config.md § Tracks` `` | ```Default rung` from its record in `.perry/config.jsonl` `` | current |
| `work/reference/review.md:441` | ``with `- Review rounds before escalation: N` in `.perry/config.md` `` | ``with `perry-config set "Review rounds before escalation" N` `` | current |
| `work/reference/git-boundaries.md:26` | ``If `.perry/config.md` records `` | ``If `.perry/config.jsonl` records `` | current; in the § 2 re-pin |
| `goals/reference/phases.md:84` | ``refuses if `.perry/config.md § Tracks` has no `SLA` cell for it`` | ``refuses if its track record in `.perry/config.jsonl` has no `SLA` `` | current |
| `modes/queue.md:61` | ``(It used to do worse: under ADR-004 it made `.perry/config.md` undeclarable …`` | ``(History: under ADR-004 it did worse — it made `.perry/config.md`, a file ADR-019 has since deleted, undeclarable …`` | history, marked |
| `reference/config.md:143` (last lines) | ``A `- Conformance gate:` line left in an existing `.perry/config.md` is inert.`` | ``History: a `- Conformance gate:` line left in a pre-ADR-019 `.perry/config.md` is inert.`` | history, marked |

**Sources for each tool claim:**
- `perry-config track --sla`, `track`, `set <Label> <value>` and `show`: `perry-config --help` and `perry-config track --help` on this tree.
- `snapshot.md`'s lint sentence: `bin/perry-lint § check_config_store`'s docstring. It validates the records and the `mode` / `default_rung` enums when `.perry/config.jsonl` exists, and says "'No store' and 'clean' are different answers, and the caller prints the absence".

## 5. Census, before and after

`grep -rn 'BOARD\.md'` and `grep -rn '\.perry/config\.md'` over
`SKILL.md AGENTS.md README.md README_cn.md work/ goals/ decide/ modes/ reference/`.

### `BOARD.md`: 49 → 26 lines

| file | before | after |
|---|---|---|
| `SKILL.md` | 2 | 0 |
| `AGENTS.md` | 1 | 1 |
| `work/SKILL.md` | 5 | 2 |
| `work/reference/subcommands.md` | 10 | 7 |
| `work/reference/state-files.md` | 2 | 2 |
| `work/reference/bootstrap.md` | 1 | 1 |
| `work/reference/conversational.md` | 1 | 0 |
| `work/reference/git-boundaries.md` | 1 | 0 |
| `work/state/PROJECT_STATE_TEMPLATE.md` | 2 | 2 |
| `work/state/evidence_TEMPLATE.md` | 1 | 1 |
| `work/state/journal_TEMPLATE.md` | 1 | 1 |
| `goals/SKILL.md` | 2 | 1 |
| `goals/reference/phases.md` | 1 | 1 |
| `goals/reference/linkage.md` | 1 | 1 |
| `modes/queue.md` | 4 | 2 |
| `modes/pipeline.md` | 1 | 0 |
| `modes/inquiry.md` | 1 | 0 |
| `reference/adoption.md` | 4 | 1 |
| `reference/hand-off-contract.md` | 2 | 2 |
| `reference/i18n.md` | 2 | 1 |
| `reference/input-quality.md` | 2 | 0 |
| `reference/router-subcommands.md` | 1 | 0 |
| `reference/diagnose.md` | 1 | 0 |
| `README.md`, `README_cn.md`, `decide/` | 0 | 0 |

**Every remaining hit and its reason** (3c § 8 tags; line numbers on `9b9e064b`):

| file:line | reason |
|---|---|
| `AGENTS.md:39` ("There is no `BOARD.md` to edit") | no-file |
| `work/SKILL.md:108` (whether a `BOARD.md` exists is not the test) | no-file |
| `work/SKILL.md:183` (a `BOARD.md` this project still holds, over its cap) | held (this round) |
| `work/reference/state-files.md:15`, `:49` | held |
| `work/reference/bootstrap.md:29` ("no `BOARD.md`") | no-file |
| `work/reference/subcommands.md:19` | history |
| `work/reference/subcommands.md:101` (a held `BOARD.md` pushed toward its cap) | held (this round) |
| `work/reference/subcommands.md:103` ("do not open `BOARD.md`") | no-file |
| `work/reference/subcommands.md:380`, `:637` | held |
| `work/reference/subcommands.md:459` (ADR-007 "applied to `BOARD.md`, the file TASK-237 later deleted") | history (this round) |
| `work/reference/subcommands.md:479` (`store-drift` on a held `BOARD.md`) | held (this round) |
| `work/state/PROJECT_STATE_TEMPLATE.md:4`, `:36`; `evidence_TEMPLATE.md:4`; `journal_TEMPLATE.md:20` | template |
| `goals/reference/linkage.md:110` | history |
| `goals/reference/phases.md:99` ("does not write `BOARD.md`") | no-file |
| `modes/queue.md:97` (decision 3 "first put it inside `BOARD.md`") | history (this round) |
| `modes/queue.md:108` (a held `BOARD.md` keeps its cap) | held (this round) |
| `reference/adoption.md:438` | import |
| `reference/hand-off-contract.md:68`, `:73` | history |
| `reference/i18n.md:52` (an invariant file name) | held |

No `sweep`, `signed` or `governed` line remains.

### `.perry/config.md`: 14 → 5 lines

| file | before | after |
|---|---|---|
| `reference/config.md` | 3 | 3 |
| `work/reference/subcommands.md` | 3 | 0 |
| `modes/queue.md` | 1 | 1 |
| `reference/diagnose.md` | 1 | 1 |
| `reference/glossary.md`, `reference/snapshot.md`, `reference/input-quality.md`, `work/reference/review.md`, `work/reference/git-boundaries.md`, `goals/reference/phases.md` | 1 each | 0 |

| remaining | reason |
|---|---|
| `reference/config.md:7` ("This page described `.perry/config.md` until ADR-019 deleted that file") | history |
| `reference/config.md:75` (a leftover `.perry/config.md` is inert) | no-file |
| `reference/config.md:143` (marked "History:") | history (this round) |
| `modes/queue.md:61` (marked "History:") | history (this round) |
| `reference/diagnose.md:476` (`MODE-02`, retired with ADR-019) | history |

## 6. Tests and mutations

### 6.1 Named tests

`python3 tests/parallel test_ownership test_spec_scannability test_router_budget test_pointers_resolve`
on a fresh extraction of `git archive 9b9e064b` (the mutation run's control): **4 modules · 112 tests, 0 red.**

| module | result |
|---|---|
| `tests/test_ownership.py` | green |
| `tests/test_spec_scannability.py` | green; `git-boundaries.md § Git Role Boundaries` pinned `e89b1321…45af` → `0a85b4b6…caec` |
| `tests/test_router_budget.py` | green; `SKILL.md` 20,457 / 20,480 B, `goals/SKILL.md` 21,559 / 22,528, `work/SKILL.md` 37,275 / 38,912 |
| `tests/test_pointers_resolve.py` | green |

Before the re-pin, on the uncommitted tree, the same four modules gave exactly
one red, `test_spec_scannability.TestTheAgentGetsItsOwnTree.test_the_governed_regions_are_pinned`,
which is the pin this round moves.

**Wider pre-commit run** over 21 modules that read the edited pages (the four
above, and `test_procedures_call_the_tool`, `test_shipped_vocabulary`,
`test_entrance`, `test_work_modes`, `test_queue_sla`, `test_glossary`,
`test_i18n`, `test_resume`, `test_claims`, `test_restore_check`,
`test_reference_pages_are_reachable`, `test_phase_kr_declared_once`,
`test_review_verdicts`, `test_missing_defaults`, `test_intake_signal`,
`test_task_writer_intake`): 660 tests, one red —
`test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`, one of the three
pre-existing reds the dispatch names.

### 6.2 Mutations

**Method.** `scratchpad/d3d/mutate.py`, on `git archive 9b9e064b`. For each
mutation:
- a fresh extraction is made;
- the anchor is asserted to occur exactly once. For the growth mutations,
  `SKILL.md` is asserted to be 20,457 B first;
- every `__pycache__` is removed (0 found in each fresh extraction);
- the named module runs through `tests/parallel` in that tree;
- FAIL/ERROR ids are collected;
- the file is restored and its bytes compared with the archive member.

**Every restore compared equal.**

| # | mutation (file) | red: named tests | result |
|---|---|---|---|
| control | none; the four named modules | — (112 tests) | green |
| M1 | **the old `work` ownership row restored** — `` `BOARD.md` (incl. `## Intake`, `## Cadence`) `` back in the row (`SKILL.md`) | `test_ownership.TestSchemaAgreesWithTheSignedContract.test_every_schema_file_owner_matches_the_contract`; `…test_the_gap_between_schema_and_contract_does_not_grow` | RED (2) |
| M2 | **the old git-boundaries line restored, no re-pin** — `` work docs (`BOARD.md`, … `` (`work/reference/git-boundaries.md`) | `test_spec_scannability.TestTheAgentGetsItsOwnTree.test_the_governed_regions_are_pinned` | RED |
| M3 | **`SKILL.md` grown past its budget by 1 byte** — 20,457 → 20,481 B | `test_router_budget.TestByteBudget.test_every_budgeted_file_is_within_its_cap` | RED |
| M3-edge | the same, to exactly 20,480 B (edge control) | — | green, as expected: the cap is inclusive, so 20,481 is the first failing size |
| M4 | **a rewritten doc pointed at a section that does not exist** — the `modes/queue.md` pointer this round added, `` `work/reference/subcommands.md § triage` `` → `§ Intake overflow finding` | `test_pointers_resolve.TestEveryPointerResolves.test_no_pointer_names_a_section_that_is_not_there` | RED |

**No mutation stayed green.**

## 7. Suite on the final commit

| run | tree | modules · tests | red modules · red tests | tree guard |
|---|---|---|---|---|
| `bash tests/run`, foreground, nothing written during it | `9b9e064b` (every change in this round except this file) | **138 · 3,963** | **2 · 3** | "nothing … moved"; `git status --porcelain` empty afterwards |
| `bash tests/run` on the commit carrying this file | reported in the hand-off message, because a file cannot carry the run of its own commit | | | |

**Reds by id: the three pre-existing ones the dispatch names, and no other.**
- `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`
- `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness`
- `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`

**Against base** (138 · 3,963, the same three reds): no module was added or removed and no test count moved, because this round changes pins and literals, not test functions. No red needed attribution, because none appeared beyond the three.

One note on the first attempt. An earlier `bash tests/run` on `9b9e064b` printed only its last 30 lines, and its totals were cut off. It was re-run with the full output saved to `scratchpad/d3d/suite-9b9e064b.txt`, and the row above is that run.

## 8. Rows this work names (none minted)

From 3c result § 11:
- **R1 — closed by this round** (§ 1): the signed contract no longer names `BOARD.md`.
- **R3 — closed for documents outside `schema/`** (§ 3). The three `schema/` sweep lines are left by hard limit 1:
  - `schema/task-list-contract.md:92`, `:104`;
  - `schema/goals-list-contract.md:167`.
- **R4 — closed** (§ 2).
- **R10 — closed** (§ 4).
- **R2** was applied by the PMO on main before this round and is not this round's.
- **R5, R6, R7, R8, R9, R11** are unchanged.

Found during this round, for the PMO; each is a contract or code line, so none
could be changed here:
- **N1 — `schema/task-list-contract.md:329`** still reads "A track declared in
  `.perry/config.md § Tracks`". It is a contract, and outside 3d's census, which
  covers only the lane docs.
- **N2 — `schema/task-list-contract.md` § `intake`, near line 478**, says
  `modes/queue.md` "rests its overflow argument" on the sweep rule. After § 3
  that argument is dropped; the sentence it quotes ("intake pressure is supposed
  to mean *taking on more than you discharge*") is still in `queue.md`. The
  contract's framing is now slightly stale.
- **N3 — "board row" prose** (for example `work/SKILL.md:304`, "Before writing a
  new BOARD row") names no file, so neither census grep reaches it. It reads as
  the printed board's row and was not swept.
- **N4 — `goals/reference/phases.md:99`**, "does not write `BOARD.md`
  (`SKILL.md § The hand-off contract`)". It is still true, but the contract it
  cites now names `tasks.jsonl`. Left as no-file; rewording it would be a sweep
  of a no-file line, which 3c did not tag.
- **N5 — `tests/test_ownership.py § SCHEMA_PATH_TO_CONTRACT`** keeps the key
  `"BOARD.md"` because `schema/state-schema.json § files[id=board]` still exists
  (§ 1). If R6 or a later round removes that entry, the key goes with it.

## What I did not check

- **Another project.** Nothing outside this worktree and the scratchpad was read
  or written.
- **The frontmatter's routing effect.** `work/SKILL.md:3` and `goals/SKILL.md:3`
  keep their trigger words. No host was asked to route with the new text.
  `test_entrance` and `test_shipped_vocabulary` are green.
- **The intake and drop claims on a held board.** § 3's measurements ran on a
  board-less scratch project only, with the base tools, whose code this round
  does not change.
- **Whether `perry-tasks board` prints `## Intake` from a queue-track `add`
  alone.** It did not in the measurement (no intake record existed). § 3 claims
  only that `intake.jsonl` is created, and that the section is printed once the
  register holds a record.
- **Pages outside the census directories** (`bin/`, `schema/`, `packs/`,
  `templates/`, `perry/`) for either string.
- **Chinese or other localized copies** of the edited pages. None exist under
  the census paths.
