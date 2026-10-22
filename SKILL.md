---
name: perry
description: Perry — one virtual project office for solo or small projects. Use for project snapshots or standups; setting, revising or scoring OKR goals, objectives, key results and phases; weekly planning; task boards and blockers; decisions, ADRs, RFCs or design docs; weekly status, session handoff and agent delegation; existing-project adoption (/perry adopt); or agent-work structure audits (/perry diagnose). Internal lanes are goals, work and decide, reached as "/perry goals plan-phase", "/perry work triage" and "/perry decide lock". Permanent aliases: okr, pmo, design. They are NOT separate skills.
---

# Perry — virtual project office

> *Perry runs the office. You run the project.*

Three lanes share project state. This router keeps commands, ordering gates and reference pointers; details live under `reference/`.

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
| **`work`** | `/perry work …` (alias `pmo`) | `$PERRY_HOME/work/SKILL.md` | task/ask/risk items, execution, reviews, dispatch and handoffs |
| **`decide`** | `/perry decide …` (alias `design`) | `$PERRY_HOME/decide/SKILL.md` | RFCs, design docs, locked decisions, ADRs |

Each lane's files are the ownership table below; each lane's SKILL.md carries its own subcommand index. Handled here instead of in a lane: the snapshot, `adopt`, `diagnose`, `relocate`, `help`, and root-owned preferences and `.perry/safety.json`.

> **Reading the lane docs**: `goals/SKILL.md`, `work/SKILL.md`, `decide/SKILL.md`, everything under `*/reference/`, everything under `packs/`, and everything under this directory's own `reference/` are written in shorthand — they say `/pmo triage` where the user would now type `/perry work triage`. Translate that agent shorthand when quoting a user command.
>
> `templates/process/` contains JSON applied through the kernel;
> `templates/scaffolds/` contains standalone artifact starting points. For a new
> project's state owner, mode and pack choices, read `reference/new-projects.md`.
> Native setup never copies a scaffold's parallel state registers.
> Shared rules live in `reference/`; each lane keeps its own `reference/` and
> `templates/`. Software-specific templates live in `packs/software-ops/templates/`.
>
> The carve-out is defined by **who reads the file last**: exactly the pages an agent re-renders before a user sees them. It does **not** cover — `bin/`, rendered output; `*/templates/*_TEMPLATE.md` and `templates/`, copied verbatim into the user's repo; `setup`, install banner; `CHANGELOG.md`/`release/`; lane frontmatter `description:`, read by the host; **this file**, `SKILL.md`; and `reference/host-capabilities.md`, which owns per-host translation and must name the live entrance.
>
> The vocabulary carve-out is a skill review checklist. New shipped surfaces must be classified here when introduced.

**Vocabulary**: `reference/glossary.md` defines Perry's terms — read it before coining one, and add the entry in the same change.

## The hand-off contract (the most important rule)

> **Signed off: Ran Jiao, 2026-08-16.** Checked: the drafted contract section,
> `perry/design/DESIGN-003-work-modes.md § 5.9` (blast radius), and
> `perry/evidence/2026-08/TASK-026-spec.md`; approved as written, without
> per-line reconciliation against the former `schema/state-schema.json § files[].owner`
> — the lane review must check the ownership agreement.

The historical signature records Perry's ownership design; it does not name
the approver for a user's project. Use that project's actual owner and policy.
See [project-neutral design](reference/design-principles.md).

**The invariant, unchanged since Perry had three registered skills:**

> **Each lane reads the others' files freely. No lane writes outside its own.**

The table is that sentence applied to a file list. It is a **file-ownership** contract, not a skill-registration one — it held when the lanes were separate skills and holds now they are loaded on demand.

| Lane | Only writer of | Proposes, never writes |
|---|---|---|
| **`goals`** (`goals/`) | objective, KR, check and phase items; OKR/phase narrative attachments; drafts in `plans/` | weekly tasks, handed to `work` |
| **`work`** (`work/`) | task, ask and risk items; `evidence/`, `weekly/`, `handoff/`, **`.perry/roles/`** | KR attribution edges, handed to `goals` |
| **`decide`** (`decide/`) | design and ADR items; `design/<DESIGN-ID>-<slug>.md` and **`decisions/`** | implementation tasks on lock, handed to `work` |

**Two changes from the previous contract, and why neither needed a second signature; why the sign-off is recorded at this precision**: `reference/hand-off-contract.md`.

The table governs Perry-owned records and narratives, not every product file
with a similar directory name. Domain artifacts retain their declared owner.
Apply [project artifact and verification contracts](reference/project-contract.md)
for references, domain lifecycle and the intersection of lane/role/task authority.

**What "only writer" forbids.** A lane needing a change in another lane's file **asks in chat and stops** — it does not write and apologise, and not "just this once" because the other lane is not loaded. Three cases that must refuse: `goals` writing task items; `work` writing `decisions/`; `decide` writing work evidence. All lanes have stopped writing `journal/`.

## Mandatory first move: combined snapshot

Route before reading project state: Explain reads only skill pages; Query reads
only the requested native projection after safety; Change runs safety then the
owning lane. An explicit user request takes priority over a suggested next step.

1. Derive `$PERRY_HOME` from this file. Detect the host with the skill-side host
   helper and read `reference/host-capabilities.md`. On Change, run the bounded
   update check and surface its result. A session has no Perry token ceiling;
   the agent environment and user decide when to start another session.
2. Read host/project preferences in `.perry/hook.md` (`reference/config.md`).
   Frozen `.perry/config.jsonl` may supply unchanged migration-era root/language
   metadata only; it is never a writer or current domain-state source. Report
   conflicting or unreadable declarations before mutation; do not guess another
   state root. Read `.perry/safety.json` before dispatch/mutation and apply
   `reference/safety-policy.md`; absence does not turn a status query into setup.
3. Apply **`reference/recovery.md` in full before querying current state**.
   A pending transaction, malformed restore point or inaccessible safety path
   blocks normal state reads and writes. An interrupted adoption, diagnosis or
   plan requires the user's resume/archive/abandon choice. Never auto-resume.
4. Read `reference/snapshot.md`: use native kernel queries for all current
   tasks, asks, risks, objectives, KRs, checks, phases, designs and ADRs. Follow
   every cursor; preserve unknowns and read failures. A missing native store
   is a setup/migration condition, never an empty board or a reason to use
   frozen JSONL registers. For Query, read only the requested projection.
5. For an overview render the combined snapshot, then apply
   `reference/next.md` top to bottom and name the facts behind the suggestion.
   For an explicit action load the owning lane in full and proceed with its
   gates. Do not ask the user to select work they already named.

Host detection is cached once per session; language/preferences reads follow the operation route. Refresh safety after
an external change, and refresh affected native projections after every write or
failed write. Never present an earlier capture as current.

## First-time setup

Only bootstrap a genuinely new project after safety has cleared and the root
procedure has established there is no prior native state or unresolved migration.
Missing documents alone do not prove that a native store is absent. A nonterminal
dossier/diagnosis requires its recorded resume choice before setup.

Read `reference/first-run.md § The procedure` and follow its six steps in order: the namespace check runs before writes, preferences go to the root-owned hook prose and reviewed safety policy, then native init records the agreed document root.

## Router subcommands

Handled here, not in a lane. `adopt` and `diagnose` span all three lanes, so they are orchestrated here and materialized through the lanes' own subcommands — neither is a fourth writer. Procedures: `reference/router-subcommands.md`

| Subcommand | Rule | Reference |
|---|---|---|
| `snapshot` | Default. | `reference/snapshot.md` + `reference/host-capabilities.md` + `reference/i18n.md` + `reference/next.md` |
| `/perry adopt [--depth=quick\|standard\|deep] [--only=…] [--resume] [--recheck]` | **Evidence proposes, the user declares.** Writes only `.perry/adoption/<YYYY-MM-DD>-dossier.md`. Read references first. | `reference/adoption.md` + `reference/adoption-sources.md` |
| `/perry diagnose [--depth=…] [--only=…] [--dry-run] [--resume] [--recheck]` | **Every prescription traces to a finding, and every finding to a measurement or an answer the user gave.** Zero findings and pure subtraction are first-class. Read reference first. | `reference/diagnose.md` |
| `/perry help [<lane>]` | The three lanes; with a lane, that lane's `help`. Explain route: no snapshot. | — |

### `/perry relocate <path>` — moving Perry's state root

Moves every claimed path under a new `State root`; `.perry/` never moves. It **refuses on a dirty tree**, inventories narrative attachments and native store/export locations, confirms every `from → to` first, and never deletes. Native store relocation requires a tested export/import receipt and explicit user approval; no file move edits a kernel anchor. Steps: `reference/router-subcommands.md § /perry relocate`.

Setup and relocate finish with [the closing step](reference/next.md#closing-step) after writes. <!-- next-close: router setup --> <!-- next-close: router relocate -->

## Configuration

Host preferences belong in `.perry/hook.md` prose; high-stakes rules in `.perry/safety.json`. Frozen `.perry/config.jsonl` is migration metadata only. Field **names** stay English in every language. Repo layout, state root, tracks and pack controls — including “what else can Perry do?” and enabling or disabling optional capabilities — are `reference/config.md`.

## Style rules

Reasoning and examples: `reference/style.md § Style rules`.
- **Lead with the dashboard, not narration.** Numbers, IDs, paths. **Cite the file** for every claim. **Never invent state**: print `—` and ask.
- **An ID never travels alone.** The first time an ID appears in user-facing output it carries its human name — `REL-002 ("Flake detector")`, never a bare `REL-002`. A table with a Title column satisfies this. Native `item get` resolves one. Full rule: `reference/user-load.md`.
- **Never ask a question the user cannot evaluate.** Reframe in consequences, decide it yourself and say so, or narrow to two: `reference/user-load.md § The three exits`.
- **Don't duplicate child skills' logic.** This file routes; the children own their domains.
- **Never mint an example ID that resolves to nothing.** Use the placeholder form (`SRC-n`, `TASK-NNN`, `<DESIGN-ID>`); a concrete one is a dangling reference `LOAD-02` reports.
- **Write in the configured languages.** Chat replies follow `Chat language`, files follow `Document language`. IDs, enum values, paths, slugs and command names stay English in every language, and a quoted artifact is never translated. **A file stays in one language end to end. A chat reply mixes**: a technical term with no settled equivalent stays English, and an English idiom is replaced by a plain description, never translated word for word — `reference/i18n.md § Writing chat prose in a language that is not English`.

## User-prompt convention, per-project hooks, auto-update

- **Host-native choice UI** over free text whenever a choice has **2-4 distinct options** (`reference/host-capabilities.md § Prompt rendering`). Cap open decisions at three. It is **not** a permission grant. `reference/style.md § User-prompt convention (AskUserQuestion)`.
- **Per-project hooks** live only in the project's `.perry/hook.md`; root and lanes read them. Never add project-specific blocks to shipped SKILL.md files. `reference/style.md § Per-project hooks (optional)`
- **Auto-update** is step 0: `reference/style.md § Auto-update`.

## See also

[README.md](README.md) · [INSTALL.md](INSTALL.md) · [kernel/ARCHITECTURE.md](kernel/ARCHITECTURE.md) (the native state contract). Extracted from this router: `reference/snapshot.md`, `reference/first-run.md`, `reference/config.md`, `reference/router-subcommands.md`, `reference/style.md`, `reference/hand-off-contract.md`.
