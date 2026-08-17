# `adr <topic>` and the `decisions/` library

The `decide` lane's ADR (Architecture Decision Record) machinery. One file per decision under `decisions/<ADR-ID>-<slug>.md`. `DECISIONS.md` at the project root is **an index only** — it lists which ADRs exist and their current status, but does not hold the decision content itself. Same split rationale as BOARD.md vs journal/: keep the always-loaded file small; one decision per file scales.

## Two-file split

```
<project_root>/
├── DECISIONS.md                         # INDEX only (≤200 lines, like BOARD.md)
└── decisions/
    ├── ADR-NNN-<slug>.md
    ├── ADR-NNN-<slug>.md
    ├── ADR-NNN-<slug>.md
    └── ...
```

| File | Purpose | Lifetime | Read frequency |
|---|---|---|---|
| `DECISIONS.md` | Index table: ADR ID / Title / Type / Date / Status + link to the per-ADR file | **Rendered by `bin/perry-decide` from the ADR files** on every write — never hand-edited, never appended to | Every standup (light scan of recent active entries) |
| `decisions/<ADR-ID>-<slug>.md` | One file per decision: Context / Options / Chosen / Consequences / Evidence / Sunset criteria | Append-only after creation; status field flips on supersede/expire/archive | On demand when the user or PMO needs the full reasoning |

The index keeps PMO's standup-time decision awareness cheap (single ≤200-line file, no per-ADR content); the per-ADR files preserve the full reasoning indefinitely and grow with project age.

## Language: configured doc language is mandatory

Before drafting any ADR, **read `.perry/config.md` § Document language**. The ADR's narrative content — Context, Options, Chosen, Consequences, Sunset criteria — MUST be written in that language. Citations (file paths, commit SHAs, code refs, evidence paths), the ADR id, and the `Type:` / `Status:` / `Date:` / `Supersedes:` **values** stay English regardless — they are matched by `bin/perry-state` and the viewer. The `DECISIONS.md` index heading and its column headers localize through the glossary (`## Active` → `## 进行中`, `| ADR | Title | Type | Date |` → `| ADR | 标题 | 类型 | 日期 |`); the full contract, including which field *names* may be localized and which may not, is `$PERRY_HOME/reference/i18n.md`.

This rule applies to all PMO-written artifacts but is called out explicitly here because ADRs are long-lived records the user reads months later. Mixed-language ADRs are hard to skim — one language per file, end to end.

Superseding or expiring an ADR does **not** translate it. An ADR is a record of what was decided and how it was written down at the time; if the project's document language later changes, existing ADRs keep theirs (`reference/i18n.md § Switching language mid-project`).

## Status model

Every ADR carries a `Status:` field. Four values:

- **active** (default at creation) — currently in effect, governs ongoing work
- **superseded** — replaced by a newer ADR. Header has `Superseded by: ADR-NNN`. The superseding ADR has `Supersedes: ADR-NNN` (bidirectional link).
- **expired** — time-boxed acceptance whose sunset criterion fired (e.g., a temporary error-budget acceptance reaching its sunset date). The decision is no longer in effect; the user must take a new action. Header records the trigger reason + date.
- **archived** — historical record only; no longer governing, no superseding ADR, no active sunset. Used for decisions whose context has passed (e.g., a 5月 project decision that's irrelevant from 9月 onward).

Files **never move** on status change — only the `Status:` header field flips. This avoids breaking inbound links from journal entries / specs / other ADRs.

## ADR file schema (template at `$PERRY_HOME/decide/state/ADR_TEMPLATE.md`)

```markdown
# ADR-NNN — <Title in configured language>

> **Type**: Process | Architecture | Operations | Risk | Cost | Design | Tooling | ... (per project hook)
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

## `DECISIONS.md` index schema (template at `$PERRY_HOME/decide/state/DECISIONS_TEMPLATE.md`)

```markdown
# Decisions index — <project name>

> Rendered by `bin/perry-decide` from `decisions/ADR-*.md` on every write.
> Active: <count> · Superseded: <count> · Expired: <count> · Archived: <count>
> Last updated: <YYYY-MM-DD>

## Active

| ADR | Title | Type | Date | Sunset / Notes |
|---|---|---|---|---|
| [ADR-NNN](decisions/ADR-NNN-<slug>.md) | Adopt Perry skill for PMO/OKR/design workflow | Process | 2026-05-06 | — |
| [ADR-NNN](decisions/ADR-NNN-<slug>.md) | Temporarily accept 8.18% error-budget overrun in deploy-service | Operations | 2026-05-06 | 2026-06-30 mandatory action |
| ... |

## Superseded / Expired / Archived (historical)

| ADR | Title | Status | Status date | Replaced by |
|---|---|---|---|---|
| [ADR-NNN](decisions/ADR-NNN-...) | Old data pipeline choice | superseded | 2026-08-15 | ADR-NNN |
| ... |
```

## Subcommand: `adr [<topic>]` and `--supersede` / `--expire` / `--archive`

### `/perry decide adr <topic>` — new ADR

1. **Read `.perry/config.md`** for document language. If absent, refuse and ask user to run top-level `/perry` first-time setup.
2. **Determine next ADR-NNN**: scan `decisions/` for highest existing `ADR-NNN-*.md`, increment. (PMO bootstrap creates ADR-NNN as the bootstrap-marker; subsequent ADRs are ADR-NNN+.)
3. **Walk Context → Options → Chosen → Consequences** interactively with the user:
   - Use `AskUserQuestion` (header `"ADR Type"`) to pick Type from project hook's declared list (default `Process | Architecture | Operations | Risk | Cost | Design | Tooling`).
   - Use `AskUserQuestion` for binary / small-set yes/no in the Options walk if relevant.
   - Free-text prompt for Context, Options, Chosen rationale, Consequences.
4. **If time-bound**: ask for Sunset criteria explicitly (`AskUserQuestion` header `"Sunset"`, options): `Date-based (Recommended for documented exceptions) | Metric-threshold | Event-triggered | None — permanent decision`. Capture the actual triggers.
5. **Slug the title**: `<short-kebab>` (5-8 words max), lowercase, hyphenated. Final filename: `decisions/ADR-NNN-<slug>.md`.
6. **Write the ADR file** from `$PERRY_HOME/decide/state/ADR_TEMPLATE.md` with all fields filled.
7. **Update `DECISIONS.md` index**: add a row in the Active section.
8. **Do not write the journal.** `journal/` is the `work` lane's file, and
   `$PERRY_HOME/SKILL.md § The hand-off contract` names *"`decide` writing
   `journal/`"* as one of three cases that must refuse. This step used to
   instruct it as a numbered instruction in the lane's primary procedure — the
   instruction was the bug, not the contract.

   If the decision deserves a line in today's journal, print the hand-off and
   stop: *"`ADR-NNN` recorded; if today's journal should note it, that is
   `/perry work`'s to write."* Asking and stopping is the contract; writing and
   apologising is the thing it forbids.
9. **Reply with the ADR path** + 1-line summary.

### `/perry decide adr --supersede ADR-NNN` — new ADR replacing an old one

Same flow as new ADR, with extra steps:
1. The new ADR's header gets `Supersedes: ADR-NNN`.
2. The old ADR file's `Status:` flips to `superseded`; header gets `Superseded by: ADR-<new>`; flip happens AFTER the new ADR is written so the chain is intact.
3. `DECISIONS.md` index: new ADR in Active section; old ADR moves to Superseded section with `Replaced by` populated.

### `/perry decide adr --expire ADR-NNN [<trigger-note>]`

For time-boxed ADRs whose sunset fired:
1. Flip target ADR's `Status:` to `expired`.
2. Append a `## Status change` entry in the target ADR file: `Expired <YYYY-MM-DD> — <trigger note>`.
3. Update DECISIONS.md index (move row to Expired section).
4. Surface the expiration in chat: "ADR-NNN has expired; you may need a new ADR to handle the now-uncovered situation."

### `/perry decide adr --archive ADR-NNN <reason>`

For ADRs whose context has passed (project pivot, scope change, etc.):
1. Flip target ADR's `Status:` to `archived`.
2. Append a `## Status change` entry: `Archived <YYYY-MM-DD> — <reason>`.
3. Update DECISIONS.md index (move row to Archived section).

Use sparingly. Most retired ADRs should be `superseded` (have a successor) or `expired` (sunset hit). `archived` is for "this decision is just no longer relevant" — should be rare.

## Sunset / expiration auto-check

At every standup, PMO scans active ADRs with `Sunset criteria` for any date-based trigger that has passed today's date. If any fired but Status is still `active`:
- Surface in the dashboard as a 🚨 alert
- Suggest action: "ADR-NNN sunset date passed; run `/perry decide adr --expire ADR-NNN` or take the required action."

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
2. Write `DECISIONS.md` from `$PERRY_HOME/decide/state/DECISIONS_TEMPLATE.md` (empty index).
3. Write `decisions/ADR-NNN-<slug>.md` from `$PERRY_HOME/decide/state/ADR_TEMPLATE.md` with:
   - Type: Process
   - Title: "Bootstrap PMO state for this project"
   - Status: active
   - Context: "Project started using Perry skill PMO on <date>"
   - Chosen: "Adopt Perry's BOARD / journal / decisions / evidence / weekly / handoff state layout"
   - Sunset: none (permanent)
4. Update `DECISIONS.md` to include ADR-NNN in the Active section.

## Migration: old monolithic `DECISIONS.md`

Projects that adopted Perry before this split still have a single-file `DECISIONS.md` with all ADRs inline. Migration is a **one-time manual operation** the user runs interactively with PMO — no dedicated subcommand. Procedure:

1. PMO reads the old `DECISIONS.md` top-to-bottom; identifies ADR boundaries (lines matching `^## ADR-NNN — `).
2. For each ADR: extract content; parse Type / Status / Date / Supersedes from the header section; slug the title (≤8 words, lowercase, hyphenated).
3. Write each to `decisions/ADR-NNN-<slug>.md` in the new schema (canonicalize header fields per `$PERRY_HOME/decide/state/ADR_TEMPLATE.md`).
4. Rewrite `DECISIONS.md` as the index per `$PERRY_HOME/decide/state/DECISIONS_TEMPLATE.md`. Active section + Superseded / Expired / Archived sections.
5. Print the hand-off line for `work` to journal, if the migration deserves one. This lane does not write `journal/` — see step 8 above.
6. Commit. Git history preserves the original DECISIONS.md so the migration is recoverable.

When a `/pmo` standup detects old-style format (no `decisions/` directory; `DECISIONS.md` contains `^## ADR-NNN — ` headers), surface the migration suggestion in the standup's "next actions" list; user kicks off the migration in chat. PMO walks the steps above, shows the user a diff summary before commit. **Do not** auto-migrate during standup — wait for explicit user confirmation.

## Per-project hook overrides

Recognized in `.perry/hook.md` under `## ADR conventions`:

```
- ADR types: Process | Architecture | Operations | Risk | Cost | Design | Tooling | Personnel
- Default ADR retention: active 90 days then candidate for archive (off by default)
- Always-active types: Operations, Risk (these never auto-archive even if untouched)
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
- `DECISIONS.md` and `decisions/` are **`decide`-owned** — moved from `work` on 2026-08-16 by the signed hand-off contract, so that a settled decision and the document that settles it have one owner. `work` and `goals` read them freely and never write them. (This line said the opposite for a release; it was the concluding sentence of the moved lane's own reference.)
