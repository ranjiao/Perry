# DESIGN-023: Perry is one system where it should be two — a PMO kernel and the skill that drives it

> Status: locked
> Date: 2026-09-24 · Locked: 2026-09-24
> Author: Perry maintainer (agent draft)   · Implementation owner: Coding Agent; the user approves phase E's switch and gives the one V5 sign-off at phase H
> Linked OKR: O3-KR1, O3-KR4 (`perry/OKR.md` v4, Objective 3 — changing Perry stays cheap, and its architecture stays where the user put it)
> Supersedes: —   · Superseded by: —
> Revisits: `DESIGN-014`, including its User Decisions 1 and 3 (its three categories of `bin/` become two halves; `perry-state` and `perry-diagnose` go), `DESIGN-013` (holds, sharpened to one home per concept), `DESIGN-004 § 4` and `DESIGN-005` decisions 1–2 (both rejected a database; decision 2), `DESIGN-007` (decision 12), `DESIGN-015` and `DESIGN-022` (decisions 4 and 8), `DESIGN-016` (the `bin/` contract), `DESIGN-020 § 9` and `ADR-023` (decision 5, now `ADR-024`), `ADR-006` and `ADR-019` (the store's medium and location, decision 2), `ADR-018` and `ADR-020` (decisions 7, 9 and 10), `ADR-002` (the store's scope). The reconciliation of every earlier design and ADR is `ADR-025`
> Sign-off: User Decisions 1–7 answered by Ran Jiao in session on 2026-09-24 — 1 and 2 in discussion, 3–7 through the choice prompt, each taking the recommendation. Locked by the user the same day, `draft` → `locked` without an `in_review` hold, on the DESIGN-013 precedent. Before the lock, the input-quality pass added § 5.6 (affected surfaces) and § 5.7 (the rejected alternative). Revised the same day after a review of every earlier design and ADR (`ADR-025`): User Decisions 8–12 answered by Ran Jiao through the choice prompt, each taking the recommendation.

## 1. Problem

Perry does two jobs: deterministic project-state management, and the agent
procedures that use it. Today both jobs live in one system, and the boundary
between them runs through the middle of files. Measured 2026-09-24 with `wc`:

| | size |
|---|---|
| `bin/` executables and libraries | 42,958 lines |
| `tests/` | 107,651 lines |
| `viewer/` | 8,878 lines |
| shipped skill prose — `SKILL.md`, the three lanes, `reference/`, `modes/`, `packs/` | 12,994 lines |
| `schema/state-schema.json` | 125,235 bytes — 29 enums, 27 claims, 10 cross-file rules |
| project state under `perry/`, `*.md` only | 196,031 lines |
| commits 2026-08-24 → 2026-09-24 | 2,063, of which 1,221 touch only `perry/` (merge commits are counted there) |

Three couplings make every change expensive.

1. **The code knows the method.** `perry-task` has 31 subcommands. `rung`,
   `signoff-offer`, `cadence-add` / `cadence-done`, `risk-add` / `risk-clear` /
   `risk-migrate`, `intake` / `route` / `resolve-intake` / `intake-sweep`,
   `track` / `stage`, `prioritize` and `design-link` put OKR, rungs V1–V5,
   tracks, registers and board sections into code and schema. Changing a rule
   of the method means changing code, tests and schema, then cutting a release.
2. **The code reads and writes markdown.** `bin/perry_md_store.py` (1,853 lines)
   stores `OKR.md` by heading. `bin/perry_store.py` renders a board and imports
   `--from-board`. `perry-lint` has advisory modes over the glossary, review
   verdicts, knowledge cards, provenance, specs and summaries. `perry-diagnose`
   resolves ids in prose through `lib.PERRY_CITATION_FAMILIES`. DESIGN-014 says
   code does not judge what a document means; this is the code side crossing
   that line anyway. The cost shows up in the test suite. On 2026-09-21, two
   PMO commits turned `main` red even though they touched only `perry/`: one
   through a repo-relative evidence path, one through an open-question id cited
   in prose. Drafting this document hit a third case. While its five User
   Decision rows were still open, they pushed `perry-diagnose`'s LOAD-03 over
   its threshold, and
   `tests/test_diagnose.py § test_perry_itself_passes_its_own_id_checks`
   failed. A draft design with open questions is ordinary work, and here it
   turned the suite red.
3. **State follows the branch.** The store is a set of git-tracked files under
   the state root, so every checkout has its own copy and its own lock. Two
   checkouts each minted `TASK-002`. `git merge` saw two lines of text, not one
   contested identity. Since 2026-09-11 the user has confirmed every task-store
   write personally to make up for this.

Host tooling that is not project management at all shares the same `bin/`:
`perry-context-budget`, `perry-dispatch-limit`, `perry-codex-preflight`,
`perry-detect-host`, `perry-churn`, `perry-state-cost`, `perry-update-check`.

## 2. Goals

1. **Two halves, one direction.** A kernel (code) and a skill (markdown). The
   skill calls the kernel. The kernel references no skill path and no name a
   process template defines. A test checks this by grepping the kernel source
   for every type, state and field name in the shipped template.
2. **The kernel runs without markdown.** Its suite passes in a checkout with every
   `*.md` removed.
3. **The kernel runs without an agent.** A scripted end-to-end test drives a full
   lifecycle through the CLI alone. It runs init and applies a template, then
   creates items of each type and moves each through every transition. It
   relates and attaches items and queries them. Finally it exports, imports
   into an empty store and re-exports; the second export must be byte-identical
   to the first.
4. **Method changes are data.** Adding a state, a field or a verification level
   changes the template file and the skill's prose, and the kernel diff is
   empty. This is shown once before cutover.
5. **One store per project.** Two worktrees of one repository write concurrently.
   They mint distinct ids and each sees the other's writes at once. A test
   covers this.
6. **The kernel has a concept budget.** At most 8 concepts (§ 5.1) and 12
   top-level commands, declared in `kernel/ARCHITECTURE.md` and checked by a
   test. Adding one means revising this design, not opening a task.
7. **The old `bin/` is gone.** At cutover, `bin/perry-*`, `perry_store.py`,
   `perry_md_store.py` and `schema/state-schema.json` are deleted. Every check
   they held has a recorded disposition (§ 6, phase H).

## 3. Non-Goals

- **A general workflow engine.** No expression language, no scripts or hooks, no
  user-defined guard kinds, no plugins. A rule the four guards in § 5.2 cannot
  express goes to the skill, or reopens this design.
- **Multi-user use, a server, or sync between machines.** The JSONL export is a
  backup and a review surface, not replication.
- **A UI beyond the CLI.** `viewer/` is § 8.
- **Markdown in the kernel.** The kernel never reads, parses, lints or renders
  markdown, in any mode.
- **Changing the method.** The first template reproduces today's work, goals and
  decide rules as they are. Pruning them is a separate decision.
- **Migrating historic prose.** The 196,031 lines of state markdown stay as
  documents. Only structured records are imported.
- **Compatibility with pre-split projects.** They are upgraded by the importer,
  as TASK-237 did for `BOARD.md`.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Kernel scope | Generic kernel + template / Method hard-coded in kernel | **Generic kernel + template** | 2026-09-24 |
| 2 | Where the store lives | Shared store at git common dir / Per-branch files (today) | **Shared store at git common dir** | 2026-09-24 |
| 3 | Guard split | Split by shape/meaning (Recommended) / All in kernel / All in agent | **Split by shape/meaning** | 2026-09-24 |
| 4 | Where OKR lives | Kernel items (Recommended) / Markdown only | **Kernel items** | 2026-09-24 |
| 5 | Next-step recommendation | Skill decides (Recommended) / Kernel evaluates rules | **Skill decides** | 2026-09-24 |
| 6 | Migration path | New kernel, lane by lane (Recommended) / Refactor bin in place | **New kernel, lane by lane** | 2026-09-24 |
| 7 | Process for this refactor | Light: V3, one V5 (Recommended) / Full current process | **Light: V3, one V5** | 2026-09-24 |
| 8 | KR progress | Metric field, kernel computes (Recommended) / Agent judges | **Metric field, kernel computes** | 2026-09-24 |
| 9 | Conditional guards | One `when` condition (Recommended) / Four unconditional guards | **One `when` condition** | 2026-09-24 |
| 10 | Verification for store and importer | V4 for B and D (Recommended) / V3 throughout | **V4 for B and D** | 2026-09-24 |
| 11 | aiMark | Moves at phase E (Recommended) / Compatibility output | **Moves at phase E** | 2026-09-24 |
| 12 | DESIGN-007's unbuilt decisions | Drop (Recommended) / Carry into template | **Drop** | 2026-09-24 |

- **1.** The kernel knows items, types, fields, transitions, guards, relations,
  events and attachments. OKR, rungs and tracks are one process template, and
  that template is data the skill ships.
- **2.** One `sqlite3` store that every worktree resolves to, plus a
  deterministic JSONL export (§ 5.3). This changes ADR-006 (events stop being
  disposable) and the store location ADR-019 assumes. The ADR that records both
  is written at phase E, when the store starts to govern the work lane
  (ADR-025).
- **3.** The kernel checks anything it can decide without reading for meaning: a
  field is set, the actor is a named human, related items are closed, a count is
  under a limit. Whether evidence proves the acceptance criteria stays with the
  agent and the V4 reviewer. *All in kernel* is today's direction. *All in
  agent* gives up the guarantee ADR-020 made part of the write path.
- **4.** Objectives, KRs and phases become item types with numeric fields,
  because KR progress is measured by command (DESIGN-022). The mission,
  operating principles and retros stay prose. *Markdown only* drops the goals
  half of the kernel, and KR progress stops being computed.
- **5.** *Skill decides* matches the split, but it reverses DESIGN-020 § 9 (the
  user's decision of 2026-09-15 that the same state gives the same
  recommendation) and ADR-023. *Kernel evaluates rules* keeps that determinism.
  Goal 1 then allows it only if the rules are written over kernel queries
  (counts of items by type and state), never over template names. The real
  question is whether a deterministic recommendation is worth a rule evaluator
  in the kernel. **Chosen: the skill decides.** That reverses a recorded user
  decision, so ADR-024 supersedes ADR-023, and DESIGN-020 carries a
  `## Changes` entry pointing here.
- **6.** Refactoring `perry-task` in place means working against its markdown
  projections and 107,651 lines of tests that hold its current shape. A new
  kernel with an importer lets each lane cut over whole.
- **7.** *Light*: kernel tasks close at V3, backed by tests. The cutover closes
  once at V5 with the user's sign-off, and one release is allocated at cutover
  instead of one per task. *Full*: a V4 fresh-context review and a release per
  task, as today. Narrowed by decision 10.
- **8.** A `metric` field holds `current`, `target`, `baseline` and
  `direction` (`up` or `down`). The kernel derives `met` and `fraction` from
  them by one fixed formula and returns both from `get` and `query`. It is a
  field type, not a ninth concept, and it brings no expression language. The
  kernel never runs a command. The skill runs a check's declared command,
  writes the value with `item update`, and the event records the command, so
  DESIGN-022's rule that only a command measures a KR holds. Phase A fixes how
  several checks on one KR roll up (DESIGN-022 User Decision 2). The rule is
  not configurable.
- **9.** A guard may carry one `when`: it applies only when a named field of
  the item has one of the listed values, for example `high_stakes: [true]`.
  `limit` counts per value of a named field, such as track and stage, and has
  a `mode` of `refuse` or `warn`. Today's WIP limits only warn. This covers
  the three conditional rung rules in use: high-stakes work needs V5
  (DESIGN-003 § 5.3 rule 1), each track has its own default rung (DESIGN-008
  decision 1), and WIP is reported per track stage. There are still four
  kinds and no expression language.
- **10.** Phases B (the store) and D (the importer) close at V4, reviewed by a
  fresh context against written criteria. ADR-018 § Chosen A spends V4 where
  a defect destroys state that cannot be recreated, and these two phases are
  exactly that. The other phases close at V3 and phase H at V5.
- **11.** aiMark calls `perry-task` in six places (`~/proj/aimark`, measured
  2026-09-24, last commit 2026-09-23). Its move to `query` ships in the same
  release as phase E, and the kernel keeps no compatibility command. The
  `schema/*-contract.md` files retire at phase H. From then on `describe` is
  the kernel's one versioned contract, and DESIGN-005's rules apply to it:
  every key always present, a minor version only adds, a major bump is
  refused without the user.
- **12.** Several DESIGN-007 decisions were signed off and never built: the
  Agent store (2, 8), a spec for every task (5) and the Run (7, 10). They are
  dropped, and DESIGN-007 records it. None of them runs today, so the first
  template has nothing to reproduce (§ 3). A later template can add a type,
  which would demonstrate Goal 4. The task tree (decision 1) is the `parent`
  relation and is kept.

## 5. Architecture

### 5.1 The two halves

```
┌──────────────────────────── skill (markdown) ────────────────────────────┐
│ SKILL.md · goals/ work/ decide/ · reference/ · packs/                    │
│ process template: templates/process/perry.json   (data, owned here)     │
│ documents: design/ decisions/ evidence/ handoff/ weekly/ knowledge/      │
└────────────────┬──────────────────────────────────────────────────────────┘
                 │  CLI · JSON in, JSON out · the only direction
┌────────────────▼─────────────── kernel (Python stdlib) ──────────────────┐
│ template · item · field · transition · guard · relation · event ·       │
│ attachment                 store: sqlite3 under <git-common-dir>/perry/ │
└───────────────────────────────────────────────────────────────────────────┘
```

The kernel's eight concepts (Goal 6):

| Concept | What it is |
|---|---|
| Template | JSON that declares item types, fields, states, transitions, guards, relation kinds and id prefixes. It is versioned, and applying a new version is an event |
| Item | One record of a declared type, with an id minted from that type's prefix |
| Field | A typed value: `text`, `int`, `number`, `date`, `enum` (optionally ordered), `actor`, `ref`, `list` or `metric` (decision 8) |
| Transition | A named move between two states of a type, carrying guards |
| Guard | One of four kinds (§ 5.2) |
| Relation | A typed edge between two items: `blocks`, `parent`, or a kind the template declares |
| Event | An append-only record of every write: actor, time, and each changed field's value before and after (ADR-022). It is the store's history |
| Attachment | An opaque reference from an item to a path or URL, with an optional content hash. The kernel never opens it |

Commands: `init`, `template` (apply, show, validate), `item` (create, get,
update, move), `rel`, `attach`, `query`, `events`, `export`, `import`,
`describe`. Every command takes and returns JSON. Every write supports
`--dry-run`. A refusal exits non-zero with a machine-readable error code.
- `item create` takes relations and attachments and writes them in the same
  transaction. An edge made at `add` cannot half-land (DESIGN-015 § 5.3).
- `query` returns the derived fields: `startable`, `blocked_by`, and a
  metric's `met` and `fraction`. No lane derives them again.
- `describe --json` reports the command surface only, and is byte-identical
  across projects (DESIGN-016 § 5).
- `template show --json` returns the applied template.

`describe` and `template show` together are the only place the skill learns
the data model.

### 5.2 Guards

| Kind | Refuses a create or a transition unless |
|---|---|
| `required` | the listed fields are set — an evidence path, a reason, a next action — and an ordered enum is at least a minimum value, such as `rung ≥ V3` |
| `actor` | the actor has the required kind (`human`, `agent`) or is the named person, as for a V5 sign-off |
| `relations_closed` | every item related by the listed kind is in a terminal state, as for dependencies |
| `limit` | at most N items sit in the target state, counted per value of a named field, as for WIP per track stage. Its `mode` is `refuse` or `warn` |

Any guard may carry one `when` condition (decision 9). Guards run on `create`
as well as on transitions.

The actor is whatever the caller declares. For a single-user local tool that is
the same trust as today's `--signer`: the guard makes a V5 close name a human,
but it does not authenticate one (DESIGN-010 risk 3).

Meaning is not a guard. Whether evidence proves the criteria, or a design's
decisions are really settled, belongs to the skill (decision 3).

### 5.3 The store

- **Location.** There is one store per project anchor, meaning the directory
  that holds `.perry/`. The store is
  `$(git rev-parse --git-common-dir)/perry/<anchor>.db`, where `<anchor>` is
  that directory's path relative to the worktree root, slugged, and `root`
  for the top level. Every worktree resolves the same file, and a fixture
  project under `tests/fixtures/` gets its own. Outside git the store is
  `<anchor>/.perry/perry.db`. ADR-002 holds: a project is still the folder
  with a `.perry/` anchor, and nothing lists them.
- **Test isolation.** Every command takes `--store <path>` and `PERRY_STORE`,
  and `--store` wins. Kernel tests always pass a temporary store, and so do
  V4 reviewers who corrupt a store on purpose. The suite fails if the live
  store changes while it runs. This is the kernel's form of
  `tests/tree_guard.py`, which cannot see inside `.git/` (TASK-249).
- **Transactions.** The store runs `sqlite3` in WAL mode with one transaction
  per command. Ids are minted inside that transaction, so two writers cannot
  mint the same id.
- **Export.** `export` writes `<state root>/export/items.jsonl` and
  `events.jsonl`, sorted and deterministic; the state root is the project's
  choice (DESIGN-002). Committing the export is the user's choice. A fresh
  clone restores from it with `import`, which refuses a store that is not
  empty and checks that replaying the events reproduces the items. Nothing
  but `import` reads the export. `events` reports how many events have been
  written since the last export.
- **Claims.** The store path and the export directory are new claimed paths.
  Phase A records each one's argument (ADR-016).
- **Earlier ADRs.** ADR-006's split between truth and history holds inside the
  store: items hold current state and events hold history. The change is that
  events stop being disposable. ADR-019 also holds: the store is the only copy
  of structured state. ADR-006, DESIGN-004 and DESIGN-005 rejected a database
  as binary, not mergeable, and unreadable without a tool. Under this design
  the store never needs merging, because it does not follow the branch, and it
  is read through the CLI and the export. The store ADR at phase E records
  that reversal.

### 5.4 The skill

- Lanes read and write state only through the kernel. They never write a
  structured record into markdown, and they never restate the data model; they
  cite `describe --json`.
- Documents stay markdown files that the lanes own, as today: designs, ADRs,
  evidence, handoffs, weekly notes, knowledge. Items point to them as
  attachments. Checks on documents become agent procedures in the skill or are
  dropped (phase H): citation resolution, glossary, review verdicts,
  provenance.
- The Perry method is `templates/process/perry.json`. Its item types are task,
  ask, risk, intake, cadence, objective, KR, check, phase, design and ADR.
  Rungs V0–V6 are an ordered enum field, as
  `schema/state-schema.json § verification` declares them. V0 is always
  refused, and guards sit on the `done` transition.
- `journal/` stops being written at each lane's cutover, and the event log
  becomes the history. A V5 sign-off's signer, date and what they checked are
  fields on the item, written in the same transaction as the close. Existing
  journal files stay as documents.
- Host helpers (host detection, update check, context budget, dispatch limits)
  are not kernel. Where they go is § 8.

### 5.5 Layout after cutover

```
kernel/                  the perry_kernel package, its tests, ARCHITECTURE.md
bin/perry                the kernel CLI — one executable
SKILL.md goals/ work/ decide/ reference/ packs/ templates/process/
perry/                   this project's documents, and perry/export/*.jsonl
```

### 5.6 What this changes outside the code

- **Other projects.** `~/proj/SkyTonight` is the first project outside this
  repository (Objective 4). It holds a `.perry/` with `config.jsonl`,
  `events.jsonl` and `hook.md`. Every project that runs this skill shares
  `$PERRY_HOME`, so cutting over a lane cuts it over for all of them. For that
  reason phase D's importer runs on SkyTonight as well as on this repository,
  and phase E does not ship until both reconcile.
- **Open tasks.** 86 rows were open on 2026-09-24: 81 `not_started`, 3
  `blocked`, 2 `review`. Nearly all were written against the old `bin/`.
  Before phase B starts, `work` triages them with the user. A row that changes
  code this design deletes is dropped, with this design as the reason. A row
  about the method stays and is imported. The triage belongs to `work`, not to
  this lane.
- **Phase 004 and OKR v4.** Phase 004 is on day 10. Its KR progress is read by
  `perry-state § phase.kr_progress` from the checks `perry-goals` writes to
  `linkage.jsonl` (DESIGN-022), and phases F and G replace both. Whether the
  phase is re-planned around this design is a decision for `goals`. This
  design asks only one thing: no KR is measured by a tool once that tool's
  phase H disposition is *dropped*.
- **aiMark.** It calls `perry-task` in six places and moves to `query` in the
  same release as phase E (decision 11).
- **Hosts.** The skill still runs on Claude Code, OpenCode and Codex CLI. The
  kernel is a CLI, so nothing host-specific moves into it.
- **Tests.** The 107,651 lines of tests belong to the old `bin/`. Phase H
  deletes them with it rather than porting them. The kernel starts with its
  own suite in phase B.

### 5.7 The alternative this rejects

**Prune in place.** Keep one system and cut it down: delete the markdown
readers, shrink `perry-task`, trim the schema. This is rejected because the
couplings in § 1 are structural, not local. The method runs through the same
code path as the store, so every pruning task would still change code, schema
and tests together, and the store would still follow the branch (§ 1, item 3).
The measurements point the same way. DESIGN-014 measured `bin/` at 30,043 lines
on 2026-09-01 and set out to thin it; on 2026-09-24 it is 42,958.

## 6. Implementation plan

`work` mints task ids at hand-off.

| Phase | Scope | Proposed PMO task(s) | Owner |
|---|---|---|---|
| A | Kernel spec in `kernel/ARCHITECTURE.md`: the concepts, the template's JSON schema, the CLI surface, the error codes, the metric roll-up (decision 8) and the claims' arguments (§ 5.3). It carries DESIGN-016's lessons: `--root` and `--store` beat the environment, unknown keys are refused, queries are bounded by default, `--help` never executes, no tracebacks, and a no-op reads differently from a write. Adding `kernel/` to `ARCHITECTURE.md § 2` and marking NN-1 and NN-2 for phase H needs the user's confirmation (NN-6). In parallel, `work` triages the open rows (§ 5.6) with the reviews' task-level suggestions (ADR-025) | TBD at lock | Coding Agent; triage: `work` with the user |
| B | Kernel core: store, items, transitions, the four guards with `when`, relations, events, attachments, `describe`, `--store`. Tests for Goals 2, 3, 5 and 6 and the live-store check | TBD at lock | Coding Agent; closes at V4 (decision 10) |
| C | `templates/process/perry.json` for the work lane (task, ask, risk, intake, cadence), plus Goal 1's grep test | TBD at lock | Coding Agent |
| D | Importer from `tasks.jsonl`, the register stores and `.perry/events.jsonl`. Counts and ids are reconciled on this repository and on `~/proj/SkyTonight` (§ 5.6). Each prefix's id ceiling is seeded from every id ever issued, including purged task ids that survive only in the event log. Evidence is imported as one text field, never split into attachments by pattern (ADR-007). Long prose `Next action` cells are decided with the user before import (DESIGN-013 § 7) | TBD at lock | Coding Agent; closes at V4 (decision 10) |
| E | Cut over `work`: rewrite `work/SKILL.md` and its references against the kernel. The old `perry-task` becomes read-only in the same change | TBD at lock | Coding Agent; the user approves the switch (closes at V3) |
| F | `goals` per decisions 4 and 8. Objective and KR records share ids across OKR versions (`O3-KR1` exists in v2–v4), so the importer re-keys them and keeps each old id as a label. The phase-close order follows the shipped prose that DESIGN-020 § 9 adopted, not DESIGN-012 User Decision 1. `decide`: design and ADR metadata as items, with the documents attached. The ADR id ceiling is seeded from the existing filenames | TBD at lock | Coding Agent |
| G | Dashboard as kernel queries. The next step becomes a skill procedure (decision 5). Together they replace `perry-state` | TBD at lock | Coding Agent |
| H | A disposition for every remaining `bin/` tool and every `perry-lint` and `perry-diagnose` check: kernel, skill procedure, or dropped. Each check moved to the skill is first shown able to go red (DESIGN-014 § 7), and each dropped one is signed by the user. The `schema/*-contract.md` files retire (decision 11). Then delete the old `bin/`, `schema/state-schema.json` and their tests (Goal 7), and show Goal 4 once | TBD at lock | Coding Agent; the user's V5 sign-off (decision 7) |

## 7. Risks & mitigations

| Risk | Detection | Mitigation |
|---|---|---|
| The kernel grows into a workflow engine | Goal 6's budget test fails | A new concept, command group or guard kind requires `revise` of this design |
| A method rule the template cannot express, such as cadence, SLA or board sections, pushes a feature into the kernel | Phase C or F cannot represent a rule | The rule becomes a skill procedure, or the user approves a kernel change in a revision. Never inside a task |
| Checks disappear quietly when `perry-lint` and `perry-diagnose` go | Phase H's table has one row per mode and per check | Each row is marked kernel, skill procedure or dropped, and the user signs off every dropped row |
| The store sits inside `.git/`, where no one sees it, and is lost on re-clone | `events` reports events since the last export | The export is committed, `import` restores it, and phase B tests the round trip |
| Two sources of truth during migration | A lane writes through both systems | Cutover is per lane, and the old writer turns read-only for that lane in the same change |
| The rewrite stalls with both systems alive | Phase E not reached two weeks after phase B closes | `work` is cut over first and is usable on its own. `goals` and `decide` can follow later |
| Process overhead grows back around the new code | The share of commits that touch only `perry/` | Decision 7 |
| A test or a reviewer writes the live store, now shared by every worktree | The suite's live-store check fails | `--store` on every command. Tests and V4 reviewers use a temporary store (§ 5.3) |
| A safety gate is lost at phase H: the high-stakes list, or the interrupted-run gate | Phase H's disposition table | A safety gate cannot be dropped. It gets its replacement before its old code is deleted |

## 8. Open questions

- Where the host helpers go: a small set of scripts on the skill side, the
  host's own configuration, or deletion.
- `viewer/` (8,878 lines): rebuild it on `query`, or retire it.
- `release/` is Perry's own release tooling and belongs to neither half. Whether
  it keeps allocating a version per task is decided under decision 7.
- The CLI's name. `bin/perry` is already DESIGN-016's forwarding index and
  keeps running during migration, so the kernel CLI cannot take that name
  before phase H.
- `.perry/config.jsonl`: settings such as languages and the state root, and
  tracks. Tracks are method and go to the template or become items. Settings
  stay a JSON file the skill reads. Phase C decides.
- The high-stakes list in `.perry/hook.md § High-stakes operations`. Code
  builds it from backticked spans today, and the dispatch pre-flight uses it.
  It is a safety gate (§ 7) and needs a structured home. Its database lines,
  dropped because Perry had no database, come back.
- The interrupted-run gate: `perry-state --section interrupted` parses
  dossier frontmatter, and the startup protocol runs it (DESIGN-001 § 5).
- Knowledge cards: `perry-knowledge` refuses a card with no source, a dangling
  source, no tripwire or no claim (DESIGN-006 goal 3). No knowledge item type
  exists yet.

## 9. Changes

- 2026-09-24 — Header and § 6 phases E and H: the one V5 sign-off (decision 7) is at phase H. Phase E's switch is approved by the user and closes at V3 — because the header said "sign-off at phases E and H", which read as two V5s.
- 2026-09-24 — Revised after the review of every earlier design and ADR
  (`ADR-025`). Added decisions 8–12 and the refinements they require:
  - the `metric` field; `when` on guards; grouped, warn-only limits; guards on
    create; ordered enums;
  - events that carry before and after values; `item create` with relations
    in one transaction; derived fields in `query`; `describe` split from
    `template show`;
  - one store per project anchor; `--store` and the live-store check; the
    export under the state root; `import` only into an empty store;
  - rungs V0–V6; `journal/` replaced by events; aiMark and the contracts;
  - importer id ceilings, evidence as text, and OKR re-keying;
  - five new open questions, and the Revisits line completed.

  The ADR for decision 2 moves from lock to phase E. Why: the review found
  that DESIGN-023 contradicted DESIGN-004, DESIGN-005, DESIGN-015, DESIGN-022,
  ADR-002, ADR-006 and ADR-018 without saying so, and did not carry
  constraints the split must keep.
- 2026-09-24 — § 5.3 and § 7: the count of events written since the last export is reported by `events`, not by `describe`. § 5.1 requires `describe` to be byte-identical across projects, and a count that differs per project breaks that. The conflict was found by the TASK-486 executor (`kernel/ARCHITECTURE.md` § 7), and the user saw the resolution in session.

## 10. References

- `perry/design/DESIGN-013-one-place-per-fact.md`, `perry/design/DESIGN-014-how-much-python.md`, `perry/design/DESIGN-020-guided-planning.md § 9`, `perry/design/DESIGN-022-kr-checks-and-measurements.md`
- `perry/decisions/ADR-002-no-cross-project-registry.md`, `perry/decisions/ADR-006-task-store-is-not-the-log.md`, `perry/decisions/ADR-019-store-is-the-only-copy-of-structured-state.md`, `perry/decisions/ADR-020-the-rung-gate-is-the-write-path-and-the-schema.md`, `perry/decisions/ADR-023-next-step-rules-cover-the-lifecycle.md`, `perry/decisions/ADR-024-next-step-is-a-skill-procedure.md`, `perry/decisions/ADR-025-earlier-designs-reconciled-with-design-023.md`
- `bin/perry-task --help` (the 31 subcommands), `bin/perry-lint --help` (the advisory modes), `bin/lib/__init__.py § PERRY_CITATION_FAMILIES`
- Measurements: `wc -l` over the paths in § 1. Commit counts come from `git log --since=2026-08-24`, split by whether `git diff-tree` names any path outside `perry/`
