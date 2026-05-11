# `/pmo decide <topic>` and the `decisions/` library

PMO's ADR (Architecture Decision Record) machinery. One file per decision under `decisions/<ADR-ID>-<slug>.md`. `DECISIONS.md` at the project root is **an index only** — it lists which ADRs exist and their current status, but does not hold the decision content itself. Same split rationale as BOARD.md vs journal/: keep the always-loaded file small; one decision per file scales.

## Two-file split

```
<project_root>/
├── DECISIONS.md                         # INDEX only (≤200 lines, like BOARD.md)
└── decisions/
    ├── ADR-001-perry-skill-migration.md
    ├── ADR-002-r1z-alphabet-acceptance.md
    ├── ADR-003-data-pipeline-split.md
    └── ...
```

| File | Purpose | Lifetime | Read frequency |
|---|---|---|---|
| `DECISIONS.md` | Index table: ADR ID / Title / Type / Date / Status + link to the per-ADR file | Auto-maintained by PMO on every `decide` / status change | Every standup (light scan of recent active entries) |
| `decisions/<ADR-ID>-<slug>.md` | One file per decision: Context / Options / Chosen / Consequences / Evidence / Sunset criteria | Append-only after creation; status field flips on supersede/expire/archive | On demand when the user or PMO needs the full reasoning |

The index keeps PMO's standup-time decision awareness cheap (single ≤200-line file, no per-ADR content); the per-ADR files preserve the full reasoning indefinitely and grow with project age.

## Language: configured doc language is mandatory

Before drafting any ADR, **read `.perry/config.md` § Document language**. The ADR's narrative content — Context, Options, Chosen, Consequences, Sunset criteria — MUST be written in that language. Citations (file paths, commit SHAs, code refs, evidence paths) and the structural keywords (Type / Status / Date / Supersedes) stay in English regardless.

This rule applies to all PMO-written artifacts but is called out explicitly here because ADRs are long-lived records the user reads months later. Mixed-language ADRs are hard to skim.

## Status model

Every ADR carries a `Status:` field. Four values:

- **active** (default at creation) — currently in effect, governs ongoing work
- **superseded** — replaced by a newer ADR. Header has `Superseded by: ADR-NNN`. The superseding ADR has `Supersedes: ADR-NNN` (bidirectional link).
- **expired** — time-boxed acceptance whose sunset criterion fired (e.g., R-1-Z acceptance reaching its sunset date). The decision is no longer in effect; the user must take a new action. Header records the trigger reason + date.
- **archived** — historical record only; no longer governing, no superseding ADR, no active sunset. Used for decisions whose context has passed (e.g., a 5月 project decision that's irrelevant from 9月 onward).

Files **never move** on status change — only the `Status:` header field flips. This avoids breaking inbound links from journal entries / specs / other ADRs.

## ADR file schema (template at `state/ADR_TEMPLATE.md`)

```markdown
# ADR-NNN — <Title in configured language>

> **Type**: Process | Architecture | Trading | Risk | Cost | Design | Tooling | ... (per project hook)
> **Status**: active
> **Date**: <YYYY-MM-DD>
> **Supersedes**: ADR-NNN (or —)
> **Superseded by**: ADR-NNN (or —)
> **Sunset criteria**: <list, only if time-boxed>

## Context

<why this decision needs to be made; observable facts driving it>

## Options

1. **Option A — <name>**
   - Pros: ...
   - Cons: ...
2. **Option B — <name>**
   - Pros: ...
   - Cons: ...
3. (anti-pattern options if useful for the audit trail)

## Chosen

**<Option label>** — <one-sentence rationale>

## Consequences

- <what changes operationally>
- <what's now true that wasn't>
- <what's now off-limits / on-limits>

## Evidence

- <PR URL / commit SHA / evidence file path / journal entry>
- ...

## Sunset criteria (only if Status carries time-bound acceptance)

- <trigger 1: date / metric threshold / event>
- <trigger 2: ...>
- Any trigger firing → file moves to `Status: expired` and the user is alerted in the next standup.
```

## `DECISIONS.md` index schema (template at `state/DECISIONS_TEMPLATE.md`)

```markdown
# Decisions index — <project name>

> Auto-maintained by PMO on every `/pmo decide` / status flip.
> Active: <count> · Superseded: <count> · Expired: <count> · Archived: <count>
> Last updated: <YYYY-MM-DD>

## Active

| ADR | Title | Type | Date | Sunset / Notes |
|---|---|---|---|---|
| [ADR-001](decisions/ADR-001-perry-skill-migration.md) | Adopt Perry skill for PMO/OKR/design workflow | Process | 2026-05-06 | — |
| [ADR-002](decisions/ADR-002-r1z-alphabet-acceptance.md) | R-1-Z 临时接受 ALPHABET 8.18% breach | Trading | 2026-05-06 | 2026-06-30 mandatory action |
| ... |

## Superseded / Expired / Archived (historical)

| ADR | Title | Status | Status date | Replaced by |
|---|---|---|---|---|
| [ADR-005](decisions/ADR-005-...) | Old data pipeline choice | superseded | 2026-08-15 | ADR-009 |
| ... |
```

## Subcommand: `/pmo decide [<topic>]` and `--supersede` / `--expire` / `--archive`

### `/pmo decide <topic>` — new ADR

1. **Read `.perry/config.md`** for document language. If absent, refuse and ask user to run top-level `/perry` first-time setup.
2. **Determine next ADR-NNN**: scan `decisions/` for highest existing `ADR-NNN-*.md`, increment. (PMO bootstrap creates ADR-001 as the bootstrap-marker; subsequent ADRs are ADR-002+.)
3. **Walk Context → Options → Chosen → Consequences** interactively with the user:
   - Use `AskUserQuestion` (header `"ADR Type"`) to pick Type from project hook's declared list (default `Process | Architecture | Trading | Risk | Cost | Design | Tooling`).
   - Use `AskUserQuestion` for binary / small-set yes/no in the Options walk if relevant.
   - Free-text prompt for Context, Options, Chosen rationale, Consequences.
4. **If time-bound**: ask for Sunset criteria explicitly (`AskUserQuestion` header `"Sunset"`, options): `Date-based (Recommended for documented exceptions) | Metric-threshold | Event-triggered | None — permanent decision`. Capture the actual triggers.
5. **Slug the title**: `<short-kebab>` (5-8 words max), lowercase, hyphenated. Final filename: `decisions/ADR-NNN-<slug>.md`.
6. **Write the ADR file** from `state/ADR_TEMPLATE.md` with all fields filled.
7. **Update `DECISIONS.md` index**: add a row in the Active section.
8. **Append journal entry** to `journal/<YYYY-MM>/<today>.md` under `## Decisions`: `ADR-NNN — <title> (Type: <type>) · decisions/ADR-NNN-<slug>.md`.
9. **Reply with the ADR path** + 1-line summary.

### `/pmo decide --supersede ADR-NNN` — new ADR replacing an old one

Same flow as new ADR, with extra steps:
1. The new ADR's header gets `Supersedes: ADR-NNN`.
2. The old ADR file's `Status:` flips to `superseded`; header gets `Superseded by: ADR-<new>`; flip happens AFTER the new ADR is written so the chain is intact.
3. `DECISIONS.md` index: new ADR in Active section; old ADR moves to Superseded section with `Replaced by` populated.

### `/pmo decide --expire ADR-NNN [<trigger-note>]`

For time-boxed ADRs whose sunset fired:
1. Flip target ADR's `Status:` to `expired`.
2. Append a `## Status change` entry in the target ADR file: `Expired <YYYY-MM-DD> — <trigger note>`.
3. Update DECISIONS.md index (move row to Expired section).
4. Surface the expiration in chat: "ADR-NNN has expired; you may need a new ADR to handle the now-uncovered situation."

### `/pmo decide --archive ADR-NNN <reason>`

For ADRs whose context has passed (project pivot, scope change, etc.):
1. Flip target ADR's `Status:` to `archived`.
2. Append a `## Status change` entry: `Archived <YYYY-MM-DD> — <reason>`.
3. Update DECISIONS.md index (move row to Archived section).

Use sparingly. Most retired ADRs should be `superseded` (have a successor) or `expired` (sunset hit). `archived` is for "this decision is just no longer relevant" — should be rare.

## Sunset / expiration auto-check

At every standup, PMO scans active ADRs with `Sunset criteria` for any date-based trigger that has passed today's date. If any fired but Status is still `active`:
- Surface in the dashboard as a 🚨 alert
- Suggest action: "ADR-NNN sunset date passed; run `/pmo decide --expire ADR-NNN` or take the required action."

Metric-based and event-based triggers are NOT auto-checked (PMO can't reliably evaluate them without project-specific instrumentation). They are listed in the ADR for human reference; the user invokes `--expire` when they observe the trigger.

## Standup integration

The standup ritual (in `SKILL.md § Mandatory first move`) reads `DECISIONS.md` (index only, not per-ADR files) for:
- Total count by status
- Most recent active ADR (for the `📝 Last decision` dashboard line)
- Any active ADRs with date-based sunsets that have passed (alert)

PMO reads specific `decisions/ADR-NNN-*.md` files only when needed — e.g., when an ongoing task references that ADR, or when the user asks "what did we decide about X".

## Bootstrap

On `/pmo` bootstrap (per `SKILL.md § Bootstrap`):
1. Create `decisions/` directory.
2. Write `DECISIONS.md` from `state/DECISIONS_TEMPLATE.md` (empty index).
3. Write `decisions/ADR-001-pmo-bootstrap.md` from `state/ADR_TEMPLATE.md` with:
   - Type: Process
   - Title: "Bootstrap PMO state for this project"
   - Status: active
   - Context: "Project started using Perry skill PMO on <date>"
   - Chosen: "Adopt Perry's BOARD / journal / decisions / evidence / weekly / handoff state layout"
   - Sunset: none (permanent)
4. Update `DECISIONS.md` to include ADR-001 in the Active section.

## Migration: old monolithic `DECISIONS.md`

If PMO standup detects `DECISIONS.md` is the **old monolithic format** (contains `## ADR-NNN` headers + content directly, no `decisions/` directory), surface in the standup's suggestions:

> "DECISIONS.md is the old single-file format. Run `/pmo decide --migrate-from-monolithic` to split into `decisions/` and rebuild index."

Migration procedure (`--migrate-from-monolithic`):
1. Read old `DECISIONS.md` top-to-bottom; identify ADR boundaries (lines matching `^## ADR-NNN — `).
2. For each ADR: extract content, parse Type / Status / Date / Supersedes from the header section, slug the title.
3. Write each to `decisions/ADR-NNN-<slug>.md` in the new schema (canonicalize header fields).
4. Rebuild `DECISIONS.md` as the index.
5. Append journal entry: `Migrated N ADRs from monolithic DECISIONS.md to decisions/ split.`
6. Show diff summary to user before commit.

Migration is one-shot and irreversible (the old format is lost in git history, but git history preserves the original). After migration, `/pmo decide` always uses the new layout.

## Per-project hook overrides

Recognized in `.perry/hook.md` under `## ADR conventions`:

```
- ADR types: Process | Architecture | Trading | Risk | Cost | Design | Tooling | Personnel
- Default ADR retention: active 90 days then candidate for archive (off by default)
- Always-active types: Trading, Risk (these never auto-archive even if untouched)
```

The `ADR types` line replaces the default type list when present.

## What this gains over monolithic DECISIONS.md

- **Standup-time cost**: bounded (index only, no full content)
- **Search**: `grep -r "<topic>" decisions/` is per-file fast
- **Audit trail**: each ADR has its own git history; bisect by ADR is clean
- **Cross-references**: spec / journal / evidence cite stable file paths instead of hash-anchors-in-a-big-file
- **Language consistency**: each ADR is written end-to-end in one language; no mid-file switches
- **Status lifecycle**: supersede / expire / archive are explicit operations with bidirectional links

What it doesn't change:
- ADR content is still append-only after creation (status flips append `## Status change` entries, never edit Chosen/Consequences in place)
- Format is still Context → Options → Chosen → Consequences → Evidence (the classic ADR shape)
- Decisions are still PMO-owned files (design / okr never write here)
