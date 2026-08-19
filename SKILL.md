---
name: perry
description: Perry — a virtual project office for solo or small projects, with one entrance. Use for a where-are-we project snapshot or standup; setting, revising or scoring goals (OKR, objectives, key results, phases); planning a week; running a task board and triaging blockers; logging decisions and ADRs; drafting or locking a design doc / RFC; weekly status, session handoff, and delegating work to agents; converting an existing project into tracked state (/perry adopt); and auditing how a project is structured for agent work (/perry diagnose). Three lanes live inside it — goals (objectives, phases, commitments), work (board, journal, evidence), decide (RFCs and decisions) — reached as "/perry goals plan-phase", "/perry work triage", "/perry decide lock". The former names okr / pmo / design keep working as permanent aliases. They are NOT separate skills. State lives at the project root in OKR.md, phase/, BOARD.md, journal/, DECISIONS.md and design/.
---

# Perry — virtual project office

> *Perry runs the office. You run the project.*

Perry is one skill with three internal lanes sharing a project's state files. This file is the entrance and the router. It is **tier 0**, read on every invocation, so it carries the commands, the ordering-critical steps and one pointer per subject; the bodies live one file away under `reference/`.

Activate on `/perry`, on the word "Perry", on a session wanting a "where are we" overview without naming a lane, and on a user asking how Perry works. Only goal-setting → `goals`; only execution → `work`. `/perry help` does **not** trigger the snapshot.

## One skill, three lanes

**Perry registers exactly one skill: `perry`.** The lanes live under `$PERRY_HOME/<lane>/SKILL.md`, are **loaded on demand by this router**, and are not separately invocable commands. Read a lane's SKILL.md in full before acting on it.

Earlier versions symlinked them as sibling skills so `/okr`, `/pmo` and `/design` worked directly. That was withdrawn: the host's skill namespace is shared, and those names collide with design-review, design-html, an entire `design:` plugin family and lark-okr. Claiming a common English word in a namespace Perry doesn't own is the same error as claiming a project's own `design/` directory — see `## Configuration`. `setup` removes the stale links on upgrade.

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

Each lane's files are the ownership table below; each lane's SKILL.md carries its own subcommand index. Handled here instead of in a lane: the snapshot, `adopt`, `diagnose`, `relocate`, `help`, and confirming `.perry/config.md`.

> **Reading the lane docs**: `goals/SKILL.md`, `work/SKILL.md`, `decide/SKILL.md`, everything under `*/reference/`, everything under `packs/`, and everything under this directory's own `reference/` are written in shorthand — they say `/pmo triage` where the user would now type `/perry work triage`. That is routing vocabulary for the agent, not a command the user can type, so it is left as-is. Translate it only when quoting a command back to the user.
>
> The carve-out is defined by **who reads the file last**: exactly the pages an agent re-renders before a user sees them. It does **not** cover — `bin/`, already-rendered output; `*/state/*_TEMPLATE.md`, `state/*_TEMPLATE.md` and `templates/`, copied verbatim into the user's repo; `setup`, whose banner is read right after install; lane frontmatter `description:`, read by the host; **this file**, `SKILL.md`; and `reference/host-capabilities.md`, which owns per-host translation and must name the live entrance.
>
> `tests/test_shipped_vocabulary.py` is that list, mechanically. Adding a class there without adding it here is how this carve-out silently grew last time.

**Vocabulary**: `reference/glossary.md` defines Perry's terms — read it before coining one, and add the entry in the same change.

## The hand-off contract (the most important rule)

> **Signed off: Ran Jiao, 2026-08-16.** Checked: the drafted contract section,
> `perry/design/DESIGN-003-work-modes.md § 5.9` (blast radius), and
> `perry/evidence/2026-08/TASK-026-spec.md`; approved as written, without
> per-line reconciliation against `schema/state-schema.json § files[].owner`
> — `tests/test_ownership.py` covers that agreement mechanically.
>
> Recorded at this precision on purpose. V5's whole value is saying **what was
> actually checked**; writing "reviewed" or inflating it into a line-by-line
> audit would make the rung a label instead of a record. `perry-lint` cannot
> check this section at all — a wrong contract shows up later as silent
> cross-lane writes, not as a lint error, which is why it is the one thing in
> Perry that requires a human gate.

**The invariant, unchanged since Perry had three registered skills:**

> **Each lane reads the others' files freely. No lane writes outside its own.**

The table is that sentence applied to a file list. It is a **file-ownership** contract, not a skill-registration one — it held when the lanes were separate skills and holds now they are loaded on demand.

| Lane | Only writer of | Proposes, never writes |
|---|---|---|
| **`goals`** (`goals/`) | `OKR.md` — **including `## Commitments`** — and `phase/<NNN>-<slug>.md` | weekly tasks, handed to `work` |
| **`work`** (`work/`) | `BOARD.md` (incl. `## Intake`, `## Cadence`), `journal/`, `PROJECT_STATE.md`, `evidence/`, `weekly/`, `handoff/` | KR attribution edges, handed to `goals` |
| **`decide`** (`decide/`) | `design/<DESIGN-ID>-<slug>.md`, **`DECISIONS.md` and `decisions/`** | implementation tasks on lock, handed to `work` |

**Two changes from the previous contract** — `DECISIONS.md` + `decisions/` moved from `work` to `decide`, and `OKR.md § Commitments` became explicitly `goals`. **The lane names and the directories now agree**, an edit needing no second signature because the ownership set above is byte-identical across it. Both accounts: `reference/hand-off-contract.md`.

**What "only writer" forbids.** A lane needing a change in another lane's file **asks in chat and stops** — it does not write and apologise, and not "just this once" because the other lane is not loaded. Three cases that must refuse: `goals` writing `BOARD.md`; `work` writing `DECISIONS.md`; `decide` writing `journal/`.

## Mandatory first move: combined snapshot

Always run this first. Steps −2 to 3 are ordering-critical; the rest is `reference/snapshot.md`.

−2. **Set `$PERRY_HOME`** — if unset, derive it from the path of the SKILL.md you just read: the directory containing this top-level SKILL.md (it also contains `bin/`, `reference/`, `modes/`, `packs/`, `goals/`, `work/`, `decide/`). For a lane SKILL.md, use the grandparent. Every `$PERRY_HOME/bin/<script>` call needs this step.

−1. **Detect host once**: `bash "$PERRY_HOME/bin/perry-detect-host"` → `claude-code` | `opencode` | `codex-cli` | `unknown`. Remember as `$HOST`, then read `$PERRY_HOME/reference/host-capabilities.md`. On `unknown`, default to `claude-code`, say so once, recommend setting `PERRY_HOST`.

0. **Auto-update check**: run `bash "$PERRY_HOME/bin/perry-update-check"`. It is throttled to once per 7 days; surface output verbatim. OpenCode and Codex may run this bounded check synchronously.

1. **Read `.perry/config.md`** for document language, chat language and repo layout. If absent and any state file exists, prompt for first-time setup. **Everything rendered from here uses the chat language**; files use `Document language`. Contract: `reference/i18n.md`.

2. **Check for an interrupted run — before anything else reads project state.**

   ```
   "$PERRY_HOME/bin/perry-state" --section interrupted
   ```

   Deterministic, read-only, stdlib-only. One row per pipeline someone walked
   away from mid-run. **Every number on the card comes from this payload** —
   never eyeball the dossier's frontmatter, which would be estimating how much
   of the user's own work survived. The gate exists because such a run is
   otherwise **invisible**: `reference/snapshot.md § Why the interrupted-run gate exists`.

   None found → step 3 unchanged. One → render the card, then ask; do **not** run
   First-time setup and do not render the dashboard first. More than one → list
   them with stage and age and ask which.

   **When `stale: true`** (no movement in `stale_after_days`, default 30, from
   `schema/state-schema.json § thresholds`), say so and move `Abandon it` first
   with the `(Recommended)` tag. It stays a recommendation, never an automatic
   retirement: `abandoned` is set by the user,
   never by Perry deciding a run has gone stale. **Never resume without asking.**

   The card, its three answer branches and the flag-mismatch refusal:
   `reference/snapshot.md § The interrupted-run card`.

3. **Compute the state — one call**:
   ```
   "$PERRY_HOME/bin/perry-state" --json
   ```
   `installed: false` → jump to **First-time setup** below — **but only if step 2 found no interrupted run.** An abandoned adoption reports `installed: false` too, because stages 0–3 write no state file; treating that as a fresh project is the failure step 2 exists to prevent. Otherwise the payload carries everything the dashboard needs; a field it lacks prints `—`.

The rest is `reference/snapshot.md`: **3b** load one mode file per distinct `mode` in `project.config.tracks[]` (never empty; a mode with no file means no rules — say so and fall back rather than skip). **3c** apply `project.config.packs[]`'s glossary to prose only. **4** render the dashboard in the exact shape given there, `—` for empty, never fabricated, **every ID carrying its title**. **5** suggest 1–3 next actions, then **6** ask "What do you want to do?", routing to `$PERRY_HOME/goals/SKILL.md`, `$PERRY_HOME/work/SKILL.md` or `$PERRY_HOME/decide/SKILL.md` — read the lane file in full first.

## First-time setup

When `/perry` runs in a project with no Perry state files at all **and step 2 found no interrupted run**. If a dossier or diagnosis exists with a non-terminal `stage`, this does not run — the user already answered these questions.

1. Briefly explain Perry (≤3 sentences).

2. **Run the namespace check before asking anything**, silently:

   ```
   python3 "$PERRY_HOME/bin/perry-lint" --claims --root . --json
   ```

   Read-only, exit 0 always. It resolves every path in
   `schema/state-schema.json § claims[]` against this folder and returns
   `collisions` plus a `suggested_state_root`.

   - **`collisions: 0`** → write `State root: perry` and **ask nothing** — the
     clean case must cost zero questions.
     ``reference/first-run.md § Why `perry` is the default state root, not `.` ``.
   - **`collisions > 0`** → add State root as a **third question in the same
     `AskUserQuestion` call** below. No extra round trip.

   Never enumerate the claimed paths here; run the check
   (`reference/first-run.md § Why the namespace check runs before anything is asked`).

3. **Confirm the project-wide preferences before any file is written**, into `.perry/config.md`. One `AskUserQuestion` call: two questions, or three when step 2 found a collision:
   - **Document language** (header `"Language"`): `English | 中文 | other`, `(Recommended)` on whichever the user has been typing. Each `description` gives the consequence: files get this language; IDs and status words stay English.
   - **Repo layout** (header `"Repo layout"`): `Single repo (Recommended) | Split repo (PMO ↔ code)`.
   - **State root** (header `"State root"`) — **only when** step 2 reported a
     collision. `Put Perry's files under <suggested>/ (Recommended) | Use the
     project root anyway | Another directory`. Name the colliding path and its
     owner in the question; the user cannot evaluate the options otherwise.

   **Don't ask about chat language.** Write `Chat language: follow user` and mirror what the user types. Document language governs **files**, chat language **replies**. Wordings: `reference/first-run.md`.

4. **New project or existing one** — `AskUserQuestion`, header `"Starting point"`: `New project — start from goals (Recommended if the folder is nearly empty) | Existing project — analyze what's here first`. The second routes to **`/perry adopt`**. **Then offer tracks, once, and only when it would change something.** `reference/first-run.md § New project or existing one, and when to offer tracks`.

5. **Recommend the order** — `/perry goals init` → `/perry goals plan-phase <slug>` → `/perry work` → `/perry decide init` → `/perry goals plan-week`. **Do not skip `/perry decide init`**: it creates the decision files, which `work`'s bootstrap correctly refuses to write. `reference/first-run.md § The recommended order for a new project`.

6. Ask "Run `/perry goals init` now?" — if yes, read `$PERRY_HOME/goals/SKILL.md` and follow its `init`. If no, stop.

## Router subcommands

Handled here, not in a lane. `adopt` and `diagnose` span all three lanes, so they are orchestrated here and materialized through the lanes' own subcommands — neither is a fourth writer. Procedures: `reference/router-subcommands.md`

| Subcommand | The rule that governs it |
|---|---|
| `/perry adopt [--depth=quick\|standard\|deep] [--only=…] [--resume] [--recheck]` | **Evidence proposes, the user declares.** Five resumable stages: scan, harvest, infer, confirm, commit. Writes one file of its own, `.perry/adoption/<YYYY-MM-DD>-dossier.md`. **Read `reference/adoption.md` first**; sources and trust tiers are `reference/adoption-sources.md`. |
| `/perry diagnose [--depth=…] [--only=…] [--dry-run] [--resume] [--recheck]` | `adopt` converts a project **into** Perry; `diagnose` asks whether its working structure is sound at all, on any folder. **Every prescription traces to a finding, and every finding to a measurement or an answer the user gave.** Six stages: scan, read, interview, prescribe, execute, recheck. **Zero findings** and pure **subtraction** are first-class. **Read `reference/diagnose.md` first.** |
| `/perry help [<lane>]` | The three lanes and when to use each. With a lane name or alias, render that lane's own `help`. Does **NOT** trigger the snapshot ritual. |

### `/perry relocate <path>` — moving Perry's state root

`/perry relocate <path>` · `/perry relocate . --dry-run`

Moves every path Perry claims under a new state root and rewrites `State root:` in `.perry/config.md`; `.perry/` never moves, because it holds the pointer. It **refuses on a dirty tree** — the `git mv` set is the only thing making the move reversible — and computes the moves from `schema/state-schema.json § claims[]`, never a hand-written list. It confirms every `from → to` first, never moves a file it did not put there, and never deletes. `NS-01` (`reference/diagnose.md § Finding catalog`) recommends it.

## Configuration

`.perry/config.md` is where a project's preferences live; every lane and script reads it. First-time setup creates it. Field **names** stay English in every language, because this file declares the language and must be readable before it is known. An optional `## Tracks` table turns on `pipeline` / `queue` / `inquiry` mode; absent means one implicit `main` track, mode `project`.

The field list and the four subjects with consequences worth reading before you change them are `reference/config.md`: **repo layout** (single, or the two-repo PMO ↔ code split), **state root** (`perry` is what setup writes; the *code* fallback is still the project root and must stay that way), **tracks**, and the **conformance gate** (advisory today — never run `perry-conform declare` for the user; adoption proposes, the user declares).

## Style rules

Reasoning and examples: `reference/style.md § Style rules`.
- **Lead with the dashboard, not narration.** Numbers, IDs, paths. **Cite the file** for every claim. **Never invent state**: print `—` and ask.
- **An ID never travels alone.** The first time an ID appears in user-facing output it carries its human name — `REL-002 ("Flake detector") is blocked on USER-014 ("Confirm staging env default")`, never `REL-002 blocked on USER-014`. A table with a Title column satisfies this. `bin/perry-explain <ID>` resolves one. Full rule: `reference/user-load.md`.
- **Never ask a question the user cannot evaluate.** Reframe in consequences, decide it yourself and say so, or narrow to two: `reference/user-load.md § The three exits`.
- **Don't duplicate child skills' logic.** This file routes; the children own their domains.
- **Never mint an example ID that resolves to nothing.** Use the placeholder form (`SRC-n`, `TASK-NNN`, `<DESIGN-ID>`); a concrete one is a dangling reference `LOAD-02` reports.
- **Write in the configured languages.** Chat replies follow `Chat language`, files follow `Document language`. IDs, enum values, paths, slugs and command names stay English in every language, and a quoted artifact is never translated. **A file stays in one language end to end. A chat reply mixes**: a technical term with no settled equivalent stays English — `交付了 contract 2.0`, not `交付了契约 2.0` — and an English idiom is never translated word for word, but replaced by a plain description of what happened. `reference/i18n.md § Writing chat prose in a language that is not English` has the specifics.

## User-prompt convention, per-project hooks, auto-update

- **Host-native choice UI** over free text whenever a choice has **2-4 distinct options**: Claude Code uses `AskUserQuestion`, OpenCode uses `question`, and Codex uses the numbered free-text fallback in `reference/host-capabilities.md § Prompt rendering`. Keep the same labels, recommendations, consequence-oriented descriptions, and selected value. Cap open decisions at three. It is **not** a permission grant. Conventions: `reference/style.md § User-prompt convention (AskUserQuestion)`.
- **Per-project hooks** live at `<project_root>/.perry/hook.md`; hook blocks go in the *children's* SKILL.md files, so this router stays project-agnostic. `reference/style.md § Per-project hooks (optional)`
- **Auto-update** is step 0 of the ritual: once per 7 days, fetch-and-report-only in dev mode, always exit 0. `reference/style.md § Auto-update`

## See also

- [README.md](README.md) · [INSTALL.md](INSTALL.md) — overview and install.
- [schema/README.md](schema/README.md) — the state-file contract, validated by `perry-lint`.
- [goals/SKILL.md](goals/SKILL.md) · [work/SKILL.md](work/SKILL.md) · [decide/SKILL.md](decide/SKILL.md) — the three lanes.
- Extracted from this router: [snapshot.md](reference/snapshot.md), [first-run.md](reference/first-run.md), [config.md](reference/config.md), [router-subcommands.md](reference/router-subcommands.md), [style.md](reference/style.md), [hand-off-contract.md](reference/hand-off-contract.md)
- Pipelines: [adoption.md](reference/adoption.md), [adoption-sources.md](reference/adoption-sources.md), [diagnose.md](reference/diagnose.md), [project-archetypes.md](reference/project-archetypes.md), [templates/](templates/)
- Shared: [i18n.md](reference/i18n.md), [user-load.md](reference/user-load.md), [host-capabilities.md](reference/host-capabilities.md), [input-quality.md](reference/input-quality.md), [okr-linkage.md](reference/okr-linkage.md)
