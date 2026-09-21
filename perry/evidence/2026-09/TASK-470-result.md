# TASK-470 result — shrink runtime instructions and per-command load sets

Date: 2026-09-21. Author: Coding Agent (Claude Opus 5). Not reviewed: V4 is still
owed by a fresh-context reviewer. No merge, push, tag or release allocation.

## Identity

- **Worktree:** `.claude/worktrees/agent-ada7876f9365ee1fc`, branch `worktree-agent-ada7876f9365ee1fc`.
- **Created at:** `0b5bf99e` (origin/main, ~365 commits behind local main, no commits of its own, clean tree). **Fast-forwarded to `359a7be1` by PMO authorisation** (`git merge --ff-only 359a7be1`, run in the worktree only).
- **Frozen base:** `359a7be16844df61437d99eb857cc940e2a5d3f8`.
- **Code head:** `293fba8785e520eada0f7d18b9fc2c30e526abe9` — every number below is measured on this tree. The evidence commit on top of it adds only this file.
- **Criterion 1 (reuse):** the bills are `bin/perry-context-budget --bill` (TASK-457) unchanged; the caps are `tests/test_router_budget.py` (TASK-456) unchanged. No CLI, budget, bill or parser was added or changed. The iteration targets (router 12 KiB, lanes 24 KiB, −30 %) are delivery targets and were **not** written into any cap (plan: "do not tighten a locked cap without its normal decision process").

## Baseline

Re-measured at `359a7be1` with `python3 bin/perry-context-budget --bill all --bill-skill-root . --json`. It equals the PMO's figures at `78a9c5fa` byte for byte (the commit between them is PMO evidence only), so the PMO baseline and targets stand.

## Entry files

| File | Before | After | Iteration target | Existing cap (unchanged) |
|---|---:|---:|---:|---:|
| `SKILL.md` (router) | 20,371 | **15,308** | ≤ 12,288 — **missed by 3,020** | 20,480 |
| `work/SKILL.md` | 37,585 | **24,563** | ≤ 24,576 — met | 38,912 |
| `goals/SKILL.md` | 22,383 | 22,442 | ≤ 24,576 — met | 22,528 |
| `decide/SKILL.md` | 23,932 | 23,959 | ≤ 24,576 — met | 24,576 |

`goals` and `decide` grew by 59 and 27 bytes: exact-reference updates only (`first-run.md § The procedure` step 3; `input-quality-rubrics.md § 1/§ 3`; the goals index row naming the new rubric page).

## The five static bills

Declared L0 + L1 + L2 bytes, shared paths counted once per load set (the tool's own rule). Hash = first 12 hex of sha256 at `293fba87`.

### snapshot: 78,456 → 73,395 (−6.5 %) — must not grow: holds

| Path | Before | After | sha256 |
|---|---:|---:|---|
| `SKILL.md` | 20,371 | 15,308 | 3765540662b3 |
| `reference/snapshot.md` | 16,675 | 16,675 | 44a5ce758dab |
| `reference/host-capabilities.md` | 7,055 | 7,059 | b140a39e24a4 |
| `reference/i18n.md` | 15,082 | 15,082 | 6671ae82a70b |
| `reference/next.md` | 19,273 | 19,271 | 7100f617e563 |

### add-task: 99,947 → 68,275 (−31.7 %) — target ≤ 69,963: met

| Path | Before | After | sha256 |
|---|---:|---:|---|
| `SKILL.md` | 20,371 | 15,308 | 3765540662b3 |
| `work/SKILL.md` | 37,585 | 24,563 | 46c81acf4092 |
| `work/reference/add-task.md` | 22,159 | 17,648 | 4ae3f2b8c3e3 |
| `reference/input-quality.md` | 9,389 | 5,286 | dac37ce6d0b2 |
| `reference/okr-linkage.md` | 10,443 | 5,470 | edd011933b73 |

### close-task: 92,853 → 64,905 (−30.1 %) — target ≤ 64,997: met (92 bytes of margin)

| Path | Before | After | sha256 |
|---|---:|---:|---|
| `SKILL.md` | 20,371 | 15,308 | 3765540662b3 |
| `work/SKILL.md` | 37,585 | 24,563 | 46c81acf4092 |
| `work/reference/promotion.md` | 8,668 | 8,668 | 611976d7521c |
| `work/reference/subcommands.md` | 26,229 | — | — |
| `work/reference/task-close.md` | — | 14,185 | 65eca24126e5 |
| `work/reference/budget-boundary.md` | — | 2,181 | 2303f60e0f01 |

Excluded by the tool (non-L2), before and after: `packs/software-ops/runbooks.md`.

### dispatch: 114,338 → 95,750 (−16.3 %) — target ≤ 80,037: **missed by 15,713**

| Path | Before | After | sha256 |
|---|---:|---:|---|
| `SKILL.md` | 20,371 | 15,308 | 3765540662b3 |
| `work/SKILL.md` | 37,585 | 24,563 | 46c81acf4092 |
| `work/reference/dispatch.md` | 31,671 | 31,416 | 6271117b3f25 |
| `work/reference/dispatch-preflight.md` | 18,848 | 17,422 | e2e0a3c0f760 |
| `work/reference/git-boundaries.md` | 5,863 | 4,860 | 9e3da73889fb |
| `work/reference/budget-boundary.md` | — | 2,181 | 2303f60e0f01 |

`budget-boundary.md` is **added** to the dispatch bill deliberately. `dispatch.md` steps "Pre-flight" and "On completion" 8 have always required the budget checkpoint; at base it lived in `subcommands.md § handoff`, which the dispatch row did not declare, so the baseline under-counted dispatch. Now that the checkpoint is its own page it is declared where it is required. Without it the after figure would be 93,569 (−18.2 %); the miss stands either way.

### plan-phase: 108,906 → 104,530 (−4.0 %) — must not grow: holds

| Path | Before | After | sha256 |
|---|---:|---:|---|
| `SKILL.md` | 20,371 | 15,308 | 3765540662b3 |
| `goals/SKILL.md` | 22,383 | 22,442 | e74460fb42b2 |
| `goals/reference/elicitation.md` | 25,429 | 25,437 | 33f7b94d47ed |
| `goals/reference/phases.md` | 31,334 | 31,342 | 038a1d3c47ef |
| `reference/input-quality.md` | 9,389 | 5,286 | dac37ce6d0b2 |
| `reference/input-quality-rubrics.md` | — | 4,715 | abbe2f484938 |

`plan-phase` runs §1 and §2 of the rubric, so the new rubric page is declared on the goals index row that already declared `input-quality.md`.

### Conditional and dynamic reads, listed apart

Not in any static bill (DESIGN-017 § 5.4: static bills do not measure dynamic reads). Same set before and after unless noted.

| Command | Read | When |
|---|---|---|
| every Change route | `reference/host-capabilities.md` | router step −1, once per operation (counted only in `snapshot`) |
| every lane standup | `reference/next.md § Rendering`, `reference/conversational.md` | step 7; every chat reply |
| every Change route | `reference/first-run.md` | only when step 3 reports `installed: false` and step 2 found nothing — **moved here from the router** |
| snapshot | `reference/startup.md`, `modes/<mode>.md`, active pack glossary, `goals/reference/planning.md` | unclear intent; step 3b per declared track; step 3c; a `plan` draft |
| add-task | `reference/config.md § Pack capabilities and controls` | spec header fields for software-ops |
| add-task | `goals/reference/linkage.md` (via `/perry goals link`) | the KR hand-off |
| close-task | `work/reference/planning.md § triage` | a stage move |
| close-task | `reference/config.md § Pack capabilities…`, `packs/software-ops/architecture.md`, `packs/software-ops/releases.md` | gates 1–2 with software-ops; a release policy |
| close-task | `work/reference/review.md` | a `V4` row |
| close-task | `modes/inquiry.md` | an inquiry track |
| dispatch | `work/reference/delegate.md § Render from the role card` | a task with a role; manual fallback |
| dispatch | `packs/software-ops/architecture.md`, `work/reference/review.md § Integration architecture reviewer brief` | step 5a with software-ops; the integration architecture review |
| dispatch | `reference/config.md § Pack capabilities…`, `packs/software-ops/releases.md` | step 5a; a release policy |
| none (never on a routine path) | `work/reference/lane-notes.md`, `add-task-notes.md`, `dispatch-notes.md`, `reference/linkage-store.md`, `reference/input-quality-rubrics.md` (work lane), `work/reference/time-estimation.md` | on a "why?" question, a store-shape question, or sizing a run |

## Relocation map

Every moved rule or passage, old location → new location. "Verbatim" means the bytes were carried over unchanged (a heading level may change). Where the old site keeps a shorter normative form, that is stated.

### Router (`SKILL.md`)

| Old heading / rule | New location | What stays in the router |
|---|---|---|
| `§ First-time setup` steps 1–3 (namespace check, the `AskUserQuestion` block, chat-language rule) | `reference/first-run.md § The procedure` — verbatim | the whole gate sentence (no state files; step 2 found nothing; non-terminal dossier/diagnosis suppresses it) and a pointer naming the section, "namespace check before any question" and "config store before any other file" |
| `§ First-time setup` steps 4–6 (one-line summaries) | already had full bodies in `first-run.md § New project or existing one…` and `§ The recommended order…` — the summaries were duplicates and were dropped | — |
| Sign-off blockquote's second paragraph, "Recorded at this precision on purpose…" | `reference/hand-off-contract.md § Why the sign-off is recorded at this precision` — verbatim | signature record (who, date, what was checked, what was not), invariant, ownership table and the three refusal cases — **byte-identical**, checked against `git show 359a7be1:SKILL.md` lines 50–54, 63–73, 77 |
| `§ Router subcommands` adopt/diagnose stage lists | `reference/router-subcommands.md § /perry adopt`, `§ /perry diagnose` — already there | each governing rule and the "read reference first" instruction |
| `§ /perry relocate` usage lines, "never moves a file it did not put there", `NS-01` | `reference/router-subcommands.md § /perry relocate` — already there | refuses on a dirty tree, moves computed from `claims[]`, confirm every `from → to`, never deletes |
| `§ Configuration`: store written first; why names stay English; `## Tracks`; pack defaults | `reference/first-run.md § Writing the config store`; `reference/config.md § What the store holds`, `§ Pack capabilities and controls` — already there | store vs hook, names stay English, one pointer |
| `§ Style rules`: the ID example's second half; the `contract 2.0` example | `reference/style.md § Style rules`; `reference/i18n.md § Writing chat prose…` — already there | every rule's one-line form, including "stays English", "idiom", "one language end to end" |
| `§ User-prompt convention` per-host tool names; auto-update detail | `reference/host-capabilities.md § Prompt rendering`; `reference/style.md § Auto-update` — already there | 2–4 options, cap at three, not a permission grant |
| `§ See also` link list | shortened; the six extracted pages are still named | README, INSTALL, schema, the six extracted pages |

Unchanged in the router, by design: the route table, steps −2 to 3 (byte-identical to base, lines 81–139), and the vocabulary carve-out note (see "Decisions needed").

### `work/SKILL.md`

| Old heading / rule | New location | What stays in the lane |
|---|---|---|
| Header blockquote: rationale for the single entrance | `work/reference/lane-notes.md § The single entrance` — verbatim | lane-not-command, `/pmo` shorthand, translate when quoting |
| Intro: OpenCode native delegation sentence | `reference/host-capabilities.md` (authority, read at step −1) — already there | pointer to host-capabilities |
| `§ How this file is organized`: `perry-task` narrative, hand-editing mechanism | `lane-notes.md § perry-task is the writer` — verbatim | every status has a tool path; gates in `subcommands.md`; **hand-editing is reported, not refused** (`🔀 Drift`) |
| same: rungs explanation | `lane-notes.md § Why the rungs are looked up` — verbatim | the `perry-explain V4` command |
| same: V4 incident history (ten rounds, five spellings) | `lane-notes.md § Why a V4 row has a convention at all` — verbatim | the whole V4 rule, including `reference/review.md`, criteria file, verdict block |
| same: glossary sentence | router `§ One skill, three lanes` "Vocabulary" line — the authority | — |
| same: eleven index rows duplicated by `§ Subcommand index` (autopilot, incidents, architecture, health-check, delegate, planning, add-task, decisions-risk, close/drop, subcommands, reporting-format) | `§ Subcommand index` rows — the authority for subcommand → page | rows the index cannot express: dispatch + preflight + budget-boundary, digests (retro archive review), promotion, runbooks gate, review, review-constraints, git-boundaries, conversational, state-files, bootstrap, extending, input-quality, okr-linkage, schema |
| `§ Two file models` Axis A table, Axis B tier definitions, per-file caps paragraph | `work/reference/state-files.md § Two file models` — verbatim | one-line form of each axis; **tier 1 hard cap: PMO/OKR refuse a write past it**; `### Axis A`/`### Axis B` headings kept (cited by `goals/SKILL.md`, packs) |
| same: why two axes | `lane-notes.md § Why two file models` — verbatim | — |
| `§ When this skill activates` (trigger list) | router activation + route table (authority) | `help` does not run the standup; digest and autopilot exemptions — moved into `§ Mandatory first move: the Standup` |
| Standup step 0 wording (language contract detail) | `reference/i18n.md` (contract) | every clause: which files use `Document language`, chat uses `Chat language`, what stays English, verbatim paths/commands/checks in delegation prompts, split-layout absolute paths, missing file → first-time setup |
| Standup step 2 list of payload fields; `--dashboard` mention | `perry-state --help` / schema | single source of every number; never eyeball; `—`; `--section`; exit non-0 fallback; `installed: false` |
| Standup step 6: three of five TL;DR examples | dropped (examples) | the TL;DR rule and two examples; the dashboard template unchanged |
| Standup step 7: reasons-lead-with-meaning sentence | `reference/next.md § Rendering` | run the section, render per next.md, never add/drop/reorder |
| `§ Companion skill`: nothing moved | — | text restored verbatim after `test_ownership` required the lane's own statement |
| `§ State files & size discipline`: fixed file list | `state-files.md § File inventory` | which writes are tool-mediated; size discipline non-negotiable; pointers |
| same: why the tool-mediated set stops where it does | `lane-notes.md § Why the tool-mediated set stops…` — verbatim | — |
| `§ Bootstrap` parenthetical procedure list | `work/reference/bootstrap.md` (authority) | trigger, the one question, config store first, the high-stakes list to confirm |
| `§ Style rules`: lead with dashboard, numbers/tables, cite the file, do not invent state | router `§ Style rules` (authority) | pointer naming those three; every lane-specific rule |
| same: input-quality bullet detail; KR-attribution resolution order and ask | `reference/input-quality.md § 4`; `reference/okr-linkage.md § The one rule` | the pass (≤3, advisory, never rewrite); the **hard gate**: resolve by ID, else ask, else `unlinked` and out of roll-ups, never fuzzy-match or fabricate |
| same: "Counts come from `bin/perry-state`" | standup step 2 (same rule) | — |
| same: R1–R5 bullets | `reference/conversational.md § Five behavioral rules` (authority) | one bullet carrying all five rules |
| `§ Extending` wording | `reference/extending.md` | pure additions, never overrides |

### Split pages

| Old heading | New location |
|---|---|
| `work/reference/subcommands.md § Task lifecycle` → `### close-task <id>`, `### drop-task <id> <reason>` | `work/reference/task-close.md` — verbatim, same heading level; `subcommands.md` keeps a one-line pointer; closing markers for both moved with them (`reference/next.md` inventory rows repointed) |
| `subcommands.md § handoff` → `#### Budget boundary` | `work/reference/budget-boundary.md § Budget boundary` — verbatim; stub kept in `subcommands.md`; citations repointed in `dispatch.md` (×2), `review.md`, `task-close.md`, `host-capabilities.md`, `handoff_TEMPLATE.md` (×2) |
| `reference/okr-linkage.md § Why ID, not name` | `reference/linkage-store.md § Why ID, not name` — verbatim; pointer stays |
| `okr-linkage.md § Resolution order`, TASK-228 history paragraph | `linkage-store.md § Why the three buckets are disjoint` — verbatim; the "disjoint / never-asked" rule stays |
| `okr-linkage.md § The linkage graph` and `§ Integrity invariants` | `linkage-store.md § The linkage graph`, `§ Integrity invariants` — verbatim; `okr-linkage.md` keeps ownership, who writes, PMO reads, pointer |
| `reference/input-quality.md § §1`, `§ §2`, `§ §3` | `reference/input-quality-rubrics.md` — verbatim; citations repointed in `goals/SKILL.md`, `goals/reference/{elicitation,setup,phases}.md`, `decide/SKILL.md` (×2), `reference/adoption.md` |
| `git-boundaries.md § Time Estimation…` body | `work/reference/time-estimation.md` — verbatim; heading kept (it is the end anchor of a governed span) with a pointer |

### Histories and measurements moved out of procedures

| Old site | New location | Rule kept at the old site |
|---|---|---|
| `add-task.md`: why `--summary` is a hard gate (25 of 114 rows) | `work/reference/add-task-notes.md § Why --summary is a hard gate` | `add` refuses without it |
| `add-task.md`: the `--unlinked` bullet's withdrawn wordings (USER-928 measurements, the non-column) | `add-task-notes.md § The unlinked bullet's history` | refuses a row answering neither; declaring at `add` is the only form that counts; not a way past the refusal; cannot be withdrawn |
| `add-task.md`: "(An earlier draft justified this…)" | `add-task-notes.md § Why the mode columns need no precedent` | the table and "add the column" |
| `add-task.md`: why track moves became a command | `add-task-notes.md § Why a row changes track by command` | the whole command rule |
| `add-task.md` step 1: why the fields were shown optional; the 36-families board; the hand-edit incidents; TASK-019/020 and TASK-053 histories | `add-task-notes.md` §§ Why all three fields…, Why exactly one prefix, Why the row is never hand-written, Why `--group` exists… | all three required; exactly one prefix (with the reason in one line); do not hand-write the row; no priority section created; `route --group` means the same |
| `add-task.md` step 2: "This step used to hand the block to the agent…" | `add-task-notes.md § Why the tool renders the definition block` | the call renders the block |
| `add-task.md` step 3: 2026-09-02 measurement; "the same schema" history | `add-task-notes.md § Why the spec shape is load-bearing` (both paragraphs whole) | `## ` shape required; the reader matches `^## ` only; **a wrong shape disarms the gate — `verdict: pass`, exit 0**; lint reports it; journal keeps bullets, spec takes `## `; do not copy the block |
| `dispatch-preflight.md § 0`: the eight-dispatch measurement | `work/reference/dispatch-notes.md § What dispatch cost in one session` | fixed cost; inline/dispatch criteria |
| `dispatch-preflight.md` step 4: the scanner's removal story (USER-916 quote, five rounds) | `dispatch-notes.md § Why no command performs step 4` | no command renders the verdict; the judgement is yours; all of 4.1–4.6 |
| step 4: the TASK-107 "eyeball" incident | `dispatch-notes.md § What "eyeball it" cost` | "This is not read-and-eyeball; work the five steps; write it down" |
| step 4.5: the TASK-107 worked case | `dispatch-notes.md § 4.5 applied` | the standing entry and its escalation |
| `dispatch.md` completion step 0 and failure handling: TASK-160 history | `dispatch-notes.md § Why the stale TTL is 4h` | default 4h; reap warning and what to do; release on every failure path; the sweep is a backstop |

Not moved, deliberately: every GOVERNED span in `dispatch.md`, `git-boundaries.md`, `delegate.md`, `review.md`, `review-constraints.md`, including the declared-free rationale block in `dispatch.md § Why it is a rule and not a preference` (moving it under `work/reference/` would put its "isolation" line outside every span, and the test requires the block to stay non-trivial); the integration gates in `dispatch.md` (see "Decisions needed").

## Guards changed

**No GOVERNED digest was re-pinned** — `tests/test_spec_scannability.py` is green unmodified. Five tests were changed, each only to follow text to its one new home; no assertion was removed or weakened:

| Test | Change |
|---|---|
| `test_claims.TestTheCheckIsWiredIn.setup_section` | grades `first-run.md § The procedure`, and **adds** an assertion that the router's `§ First-time setup` names that section |
| `test_shipped_vocabulary…test_the_readmes_show_where_state_actually_lands` | reads the `write \`State root: …\`` declaration from `first-run.md`, where it now lives |
| `test_knowledge_promotion…test_each_capture_point_routes_to_it` | the close-task capture point is read from `task-close.md` (same anchor) |
| `test_task_writer_contracts`, `test_work_modes` | `task-close.md` added to the list of procedure pages |

## Negative proofs

Harness `$PERRY_SCRATCH/tools/mutate.py`, where `$PERRY_SCRATCH` is `${TMPDIR}/perry-scratch/agent-ada7876f9365ee1fc`, derived with the `perry-scratch-derivation` block of `dispatch.md § Where the agent puts a scratch file`. Each mutant: purge `__pycache__`, wait past the next second boundary, write, run the one owning check, restore from `git show 293fba87:<path>`. Full output of every run is kept, pass or fail, under `mutations/`.

| ID | Property aimed at | Check | Expected | Got | Evidence |
|---|---|---|---|---|---|
| CAP-0 | router at exactly its L0 cap (20,480) | `test_every_budgeted_file_is_within_its_cap` | green | green | — |
| CAP+1 | router one byte over | same | red | red | `SKILL.md: L0 actual=20481 cap=20480` |
| L2-CAP+1 | a new split page one byte over 32 KiB | same | red | red | `task-close.md: L2 actual=32769 cap=32768` |
| BILL-CAP | add-task bill exactly 100,000 | `perry-context-budget --bill add-task` | exit 0 | exit 0, `within` | total 100,000 |
| BILL-CAP+1 | add-task bill one byte over | same | exit 1 | exit 1, `over` | total 100,001 |
| PTR-FILE | index row naming a missing page | `test_claims.TestEveryDeclaredSubcommandHasAProcedure` | red | red | `close-task points at task-closed.md, which does not exist` |
| PTR-FILE-BILL | the same broken pointer in the bill | `--bill close-task` | exit 1 | exit 1 | `missing file: …/task-closed.md` |
| PTR-SECTION | moved-rule pointer to a missing section | `test_every_section_citation_names_a_section_that_exists` | red | red | `task-close.md:122 → budget-boundary.md § Budget boundry` |
| PTR-SECTION-ROUTER | router pointer to the moved setup procedure | same | red | red | `SKILL.md:140 → reference/first-run.md § The procedures of setup` |

Restore: `bin/perry-restore-check 293fba87 SKILL.md work/SKILL.md work/reference/add-task.md work/reference/task-close.md` → exit 0, all four match. `git status` clean afterwards.

## Suite

- `bash tests/run --tier full` on `293fba87`: **all green** — 157 modules, 4,434 tests, 111.2 s, 8 workers; steps 0, 1, 3, 4 green; tree guard: nothing moved. `test_host_support` (filed flake TASK-272) did not go red, so no re-run was needed. Log: `$PERRY_SCRATCH/full-293fba87.log`.
- An earlier full run on the uncommitted tree was red in 8 modules / 9 tests; each was a guard objecting to a move, fixed as listed under "Guards changed" or by restoring text (`test_ownership` wanted the lane's own write-refusal and "only writer of" sentences back; `test_actor_required` and `test_procedures_call_the_tool` objected to two new sentences of mine, reworded; `test_next_closing` was split by my own mention of the index heading, reworded; `test_reference_pages_are_reachable` required the new notes pages to be named in the lane; `test_pointers_resolve` caught two relative paths). Log: `$PERRY_SCRATCH/full-1.log`.
- **A baseline full run at `359a7be1` is not claimed.** It was started, and I edited the tree while it ran; its tree guard correctly reported `SKILL.md` and `reference/first-run.md` changed. Step 2 had printed 4,434 tests green before the guard ran, but the edits may have landed during step 2, so that run is evidence of nothing. Log kept: `$PERRY_SCRATCH/suite-base.log`.
- `git diff --check 359a7be1..293fba87`: clean.

## Decisions taken — USER-975, 2026-09-21

The user answered in chat; the PMO recorded it as USER-975 on main (`9093a838`).

1. **Router ≤ 12,288 — missed at 15,308 (−24.9 % vs −39.7 %): accepted as a recorded exception.**
   What remains is the signed contract section, the route table and steps −2 to 3, the host-read
   frontmatter and the vocabulary carve-out. Option (a), moving the carve-out list, was declined:
   it saves ≈800 bytes and would still miss.
2. **dispatch ≤ 80,037 — missed at 95,750 (−16.3 % vs −30 %): accepted as a recorded exception.**
   The two integration gates (`Full merge acceptance`, `§ Architecture review`) **stay in
   `dispatch.md`**; no integration route is split off, so no gate moves.
3. **Sign-off rationale paragraph moved to `reference/hand-off-contract.md`: accepted.** Signer, date,
   checked scope, invariant and ownership table remain byte-identical in `SKILL.md`, as the
   relocation map says; the paragraph is verbatim at its new home.

Still open, and not this row's to decide: **the iteration targets are not enforced** by any test —
`work/SKILL.md` is 13 bytes under its target and `close-task` 92 under. Making any of them a cap is
a DESIGN-017 § 5.4 decision.

## Round 2 — the V4 FAIL, and what changed

Round 1's V4 (`TASK-470-v4-review.md`, `3115d09c`) FAILed on criterion 4, graded ROW: one routine-path rule was
stranded. At base, `work/SKILL.md` step 0 said *"Headings and column headers localize through the glossary in
`schema/state-schema.json § i18n`"*. Round 1 dropped that clause; the rule then lived only in `reference/i18n.md`,
which none of add-task, close-task or dispatch loads. **The relocation map above claimed every clause of step 0 was
kept. That claim was false.** The reviewer reproduced it; the PMO reproduced it again before fixing.

Branch `coding/task-470-round2`, base `3115d09c`. Full suite on the fix: 157 modules / 4,434 tests, green.

| Change | Where | Bytes |
|---|---|---:|
| Clause restored, verbatim, in step 0 | `work/SKILL.md` | +97 |
| The pack paragraph's `Why:` pointer (rationale only) moved | `work/SKILL.md` → `work/reference/lane-notes.md § Why the pack rule is scoped by route` | −77 |
| "before continuing" → "first" in step 0's missing-config line | `work/SKILL.md` | −12 |
| F2: autopilot's context-ceiling check cited `subcommands.md § Budget boundary`, reachable only through the stub | `work/reference/autopilot.md` → `budget-boundary.md § Budget boundary` | 0 |

`work/SKILL.md`: 24,563 → **24,571** (target ≤ 24,576). Bills: add-task 68,275 → 68,283, close-task 64,905 → 64,913
(84 bytes of margin), dispatch 95,750 → 95,758; snapshot and plan-phase unchanged.

The `Why:` pointer is the only thing removed to make room, and it pointed at rationale; `reference/startup.md` is
still reached from the router's Route-first step. **No guard exists for the restored clause, and none is added:** it
is a semantic rule, and code does not judge document meaning. Its protection is the V4.

Not fixed, recorded by the reviewer and not charged: F3, `add-task.md:151` still describing a scan removed on
2026-09-04 (older than this row); the section-citation guard not seeing a citation wrapped across two lines (older
than this row).

## Not claimed

- **Runtime token savings are unmeasured.** These are static declared bytes of shipped files, not tokens, not a transcript, not a session (USER-972: no runtime usage is measured on this host). Bytes are not substituted for tokens anywhere here.
- No criterion-5 or retained-meaning verdict: that is the V4 reviewer's semantic review against the relocation map above. Deterministic guards verify bytes, pointers and sections only.
- No V4, no merge, no integration architecture review.
- Dynamic reads are listed, not measured.
