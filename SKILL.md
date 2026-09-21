---
name: perry
description: Perry — one virtual project office for solo or small projects. Use for project snapshots or standups; setting, revising or scoring OKR goals, objectives, key results and phases; weekly planning; task boards and blockers; decisions, ADRs, RFCs or design docs; weekly status, session handoff and agent delegation; existing-project adoption (/perry adopt); or agent-work structure audits (/perry diagnose). Internal lanes are goals, work and decide, reached as "/perry goals plan-phase", "/perry work triage" and "/perry decide lock". Permanent aliases: okr, pmo, design. They are NOT separate skills.
---

# Perry — virtual project office

> *Perry runs the office. You run the project.*

Perry has three internal lanes sharing project state. This tier-0 router is read on every invocation, so it keeps commands, ordering-critical steps and one pointer per subject; bodies live under `reference/`.

Activate on `/perry`, on the word "Perry", on a session wanting a "where are we" overview without naming a lane, and on a user asking how Perry works. Only goal-setting → `goals`; only execution → `work`.

## One skill, three lanes

**Perry registers exactly one skill: `perry`.** The lanes live under `$PERRY_HOME/<lane>/SKILL.md`, are **loaded on demand by this router**, and are not separately invocable commands. Read a lane's SKILL.md in full before acting on it.

Legacy sibling skills were withdrawn to avoid host namespace collisions; `setup` removes their stale links.

### Command surface

```
/perry                          combined snapshot (the default)
/perry <lane> <subcommand>      /perry goals plan-phase · /perry work triage · /perry decide lock
                                aliases: okr → goals · pmo → work · design → decide
/perry <subcommand>             allowed when the subcommand name is unambiguous
/perry adopt | diagnose | relocate <path> | help    handled here, not in a lane
```

**Most** subcommand names are unique across the lanes, so `/perry plan-phase` resolves without one. **Five are not**, and a bare invocation must ask rather than guess: `plan-week`, `handoff`, `status`, `revise`, `init`.

| Lane | Reached as | Loaded from | Subject |
|---|---|---|---|
| **`goals`** | `/perry goals …` (alias `okr`) | `$PERRY_HOME/goals/SKILL.md` | objectives, phases, KRs, weekly proposals |
| **`work`** | `/perry work …` (alias `pmo`) | `$PERRY_HOME/work/SKILL.md` | board, journal, cadence, dispatch, status |
| **`decide`** | `/perry decide …` (alias `design`) | `$PERRY_HOME/decide/SKILL.md` | RFCs, design docs, locked decisions, ADRs |

Each lane's files are the ownership table below; each lane's SKILL.md carries its own subcommand index. Handled here instead of in a lane: the snapshot, `adopt`, `diagnose`, `relocate`, `help`, and writing `.perry/config.jsonl`.

> **Reading the lane docs**: `goals/SKILL.md`, `work/SKILL.md`, `decide/SKILL.md`, everything under `*/reference/`, everything under `packs/`, and everything under this directory's own `reference/` are written in shorthand — they say `/pmo triage` where the user would now type `/perry work triage`. That is routing vocabulary for the agent, not a command the user can type, so it is left as-is. Translate it only when quoting a command back to the user.
>
> The carve-out is defined by **who reads the file last**: exactly the pages an agent re-renders before a user sees them. It does **not** cover — `bin/`, rendered output; `*/state/*_TEMPLATE.md`, `state/*_TEMPLATE.md` and `templates/`, copied verbatim into the user's repo; `setup`, install banner; `CHANGELOG.md`/`release/`; lane frontmatter `description:`, read by the host; **this file**, `SKILL.md`; and `reference/host-capabilities.md`, which owns per-host translation and must name the live entrance.
>
> `tests/test_shipped_vocabulary.py` is that list, mechanically. Adding a class there without adding it here is how this carve-out silently grew last time.

**Vocabulary**: `reference/glossary.md` defines Perry's terms — read it before coining one, and add the entry in the same change.

## The hand-off contract (the most important rule)

> **Signed off: Ran Jiao, 2026-08-16.** Checked: the drafted contract section,
> `perry/design/DESIGN-003-work-modes.md § 5.9` (blast radius), and
> `perry/evidence/2026-08/TASK-026-spec.md`; approved as written, without
> per-line reconciliation against `schema/state-schema.json § files[].owner`
> — `tests/test_ownership.py` covers that agreement mechanically.

**The invariant, unchanged since Perry had three registered skills:**

> **Each lane reads the others' files freely. No lane writes outside its own.**

The table is that sentence applied to a file list. It is a **file-ownership** contract, not a skill-registration one — it held when the lanes were separate skills and holds now they are loaded on demand.

| Lane | Only writer of | Proposes, never writes |
|---|---|---|
| **`goals`** (`goals/`) | `OKR.md` — **including `## Commitments`** — and `phase/<NNN>-<slug>.md`; drafts in `plans/` (DESIGN-020 UD 5, not this sign-off) | weekly tasks, handed to `work` |
| **`work`** (`work/`) | `tasks.jsonl` + its 4 register stores (`perry-tasks board` prints them), `journal/`, `PROJECT_STATE.md`, `evidence/`, `weekly/`, `handoff/`, **`.perry/agents.jsonl` → `.perry/roles/`** | KR attribution edges, handed to `goals` |
| **`decide`** (`decide/`) | `design/<DESIGN-ID>-<slug>.md` and **`decisions/`** | implementation tasks on lock, handed to `work` |

**Two changes from the previous contract, and why neither needed a second signature; why the sign-off is recorded at this precision**: `reference/hand-off-contract.md`.

**What "only writer" forbids.** A lane needing a change in another lane's file **asks in chat and stops** — it does not write and apologise, and not "just this once" because the other lane is not loaded. Three cases that must refuse: `goals` writing `tasks.jsonl`; `work` writing `decisions/`; `decide` writing `journal/`.

## Mandatory first move: combined snapshot

**Route first, reading no project state.** You judge the intent; cases: `reference/startup.md`.

| Route | Run | Then |
|---|---|---|
| **Explain**: help, how Perry works | step −2 | only the pages that answer. No update check, config, state, modes, dashboard or write |
| **Query**: one fact about this project | −2, −1, 1, 2 | only that projection: `--section <name>`, `perry-explain <ID>`, `perry-task list --json` |
| **Change**: a write, a subcommand but `help`, bare `/perry` | −2 to 3 | bare `/perry` → 3b–6; a lane skips its −3 to −1, keeps its gates |

Unclear → ask which. Nothing reads state before step 2 **but step 1's config read**. Steps run once per operation; after a write, or when state may have moved, re-read. Steps −2 to 3 are ordering-critical; the rest is `reference/snapshot.md`.

−2. **Set `$PERRY_HOME`** — if unset, derive it from the path of the SKILL.md you just read: the directory containing this top-level SKILL.md (it also contains `bin/`, `reference/`, `modes/`, `packs/`, `goals/`, `work/`, `decide/`). For a lane SKILL.md, use the grandparent. Every `$PERRY_HOME/bin/<script>` call needs this step.

−1. **Detect host once**: `bash "$PERRY_HOME/bin/perry-detect-host"` → `claude-code` | `opencode` | `codex-cli` | `unknown`. Remember as `$HOST`, then read `$PERRY_HOME/reference/host-capabilities.md`. On `unknown`, default to `claude-code`, say so once, recommend setting `PERRY_HOST`.

0. **Auto-update check**: run `bash "$PERRY_HOME/bin/perry-update-check"`. It is throttled to once per 7 days; surface output verbatim. OpenCode and Codex may run this bounded check synchronously.

1. **Read `.perry/config.jsonl`** for document language, chat language and repo layout. If it does not exist and a state file does, prompt for first-time setup — **Change route only**, since it writes; Explain and Query report the gap and stop. **Everything rendered from here uses the chat language**; files use `Document language`. Contract: `reference/i18n.md`.

2. **Check for an interrupted run, but only after recovery safety — before anything else reads project state.**

   ```
   "$PERRY_HOME/bin/perry-state" --section recovery
   ```

   This is the deterministic, read-only startup recovery gate. If
   `blocking: true`, stop before any further project-state read or mutation and
   report every exact path and error — **nothing else is read after that
   stop, not even a listing**. A pending task transaction must be
   recovered by the task command; a malformed dossier must be repaired or
   explicitly retired. Do not reinterpret either as routine PMO hygiene.

   Only after `blocking: false`, run the interrupted-pipeline gate:

   ```
   "$PERRY_HOME/bin/perry-state" --section interrupted
   ```

   Read-only; one row per pipeline left mid-run. **Every number on the card
   comes from this payload**, never the dossier's frontmatter. Why:
   `reference/snapshot.md § Why the interrupted-run gate exists`.

   None found → step 3 unchanged. One → render the card, then ask; do **not** run
   First-time setup and do not render the dashboard first. More than one → list
   them with stage and age and ask which.

   **When `stale: true`** (no movement in `stale_after_days`, default 30, from
   `schema/state-schema.json § thresholds`), say so and move `Abandon it` first
   with the `(Recommended)` tag. It stays a recommendation: `abandoned` is set by the user,
   never by Perry deciding a run has gone stale. **Never resume without asking.**

   The card, its three answer branches and the flag-mismatch refusal:
   `reference/snapshot.md § The interrupted-run card`. A `plan` draft, and
   `/perry plan`: `goals/reference/planning.md`.

3. **Compute the state — one call**:
   ```
   "$PERRY_HOME/bin/perry-state" --compact
   ```
   `installed: false` → jump to **First-time setup** below — **but only if step 2 found neither a recovery hazard nor an interrupted run.** Otherwise the payload carries everything the dashboard needs; a field it lacks prints `—`.

The rest is `reference/snapshot.md`: **3b** mode files, **3c** pack glossary, **4** dashboard, **5** `next` per `reference/next.md`, **6** ask "What do you want to do?" and route to `$PERRY_HOME/goals/SKILL.md`, `$PERRY_HOME/work/SKILL.md` or `$PERRY_HOME/decide/SKILL.md`, read in full first.

## First-time setup

When `/perry` runs in a project with no Perry state files at all **and step 2 found neither a recovery hazard nor an interrupted run**. If a dossier or diagnosis exists with a non-terminal `stage`, this does not run — the user already answered these questions.

Read `reference/first-run.md § The procedure` and follow its six steps in order: the namespace check runs before any question, and the answers go to `.perry/config.jsonl` before any other file.

## Router subcommands

Handled here, not in a lane. `adopt` and `diagnose` span all three lanes, so they are orchestrated here and materialized through the lanes' own subcommands — neither is a fourth writer. Procedures: `reference/router-subcommands.md`

| Subcommand | Rule | Reference |
|---|---|---|
| `snapshot` | Default. | `reference/snapshot.md` + `reference/host-capabilities.md` + `reference/i18n.md` + `reference/next.md` |
| `/perry adopt [--depth=quick\|standard\|deep] [--only=…] [--resume] [--recheck]` | **Evidence proposes, the user declares.** Writes only `.perry/adoption/<YYYY-MM-DD>-dossier.md`. Read references first. | `reference/adoption.md` + `reference/adoption-sources.md` |
| `/perry diagnose [--depth=…] [--only=…] [--dry-run] [--resume] [--recheck]` | **Every prescription traces to a finding, and every finding to a measurement or an answer the user gave.** Zero findings and pure subtraction are first-class. Read reference first. | `reference/diagnose.md` |
| `/perry help [<lane>]` | The three lanes; with a lane, that lane's `help`. Explain route: no snapshot. | — |

### `/perry relocate <path>` — moving Perry's state root

Moves every claimed path under a new `State root`; `.perry/` never moves. It **refuses on a dirty tree**, computes the moves from `schema/state-schema.json § claims[]`, confirms every `from → to` first, and never deletes. Steps: `reference/router-subcommands.md § /perry relocate`.

Setup and relocate finish with [the closing step](reference/next.md#closing-step) after writes. <!-- next-close: router setup --> <!-- next-close: router relocate -->

## Configuration

`.perry/config.jsonl` holds the settings (`perry-config set`); prose belongs in `.perry/hook.md`. Field **names** stay English in every language. Repo layout, state root, tracks and pack controls — including “what else can Perry do?” and enabling or disabling optional capabilities — are `reference/config.md`.

## Style rules

Reasoning and examples: `reference/style.md § Style rules`.
- **Lead with the dashboard, not narration.** Numbers, IDs, paths. **Cite the file** for every claim. **Never invent state**: print `—` and ask.
- **An ID never travels alone.** The first time an ID appears in user-facing output it carries its human name — `REL-002 ("Flake detector")`, never a bare `REL-002`. A table with a Title column satisfies this. `bin/perry-explain <ID>` resolves one. Full rule: `reference/user-load.md`.
- **Never ask a question the user cannot evaluate.** Reframe in consequences, decide it yourself and say so, or narrow to two: `reference/user-load.md § The three exits`.
- **Don't duplicate child skills' logic.** This file routes; the children own their domains.
- **Never mint an example ID that resolves to nothing.** Use the placeholder form (`SRC-n`, `TASK-NNN`, `<DESIGN-ID>`); a concrete one is a dangling reference `LOAD-02` reports.
- **Write in the configured languages.** Chat replies follow `Chat language`, files follow `Document language`. IDs, enum values, paths, slugs and command names stay English in every language, and a quoted artifact is never translated. **A file stays in one language end to end. A chat reply mixes**: a technical term with no settled equivalent stays English, and an English idiom is replaced by a plain description, never translated word for word — `reference/i18n.md § Writing chat prose in a language that is not English`.

## User-prompt convention, per-project hooks, auto-update

- **Host-native choice UI** over free text whenever a choice has **2-4 distinct options** (`reference/host-capabilities.md § Prompt rendering`). Cap open decisions at three. It is **not** a permission grant. `reference/style.md § User-prompt convention (AskUserQuestion)`.
- **Per-project hooks** live at `<project_root>/.perry/hook.md`; hook blocks go in the *children's* SKILL.md files, so this router stays project-agnostic. `reference/style.md § Per-project hooks (optional)`
- **Auto-update** is step 0: `reference/style.md § Auto-update`.

## See also

[README.md](README.md) · [INSTALL.md](INSTALL.md) · [schema/README.md](schema/README.md) (the state-file contract). Extracted from this router: `reference/snapshot.md`, `reference/first-run.md`, `reference/config.md`, `reference/router-subcommands.md`, `reference/style.md`, `reference/hand-off-contract.md`.
