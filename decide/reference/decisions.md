# `adr <topic>` and the `decisions/` library

The `decide` lane's ADR (Architecture Decision Record) machinery. One file per decision under `decisions/<ADR-ID>-<slug>.md`. **Those files are the whole record**, and `perry-decide list` is the whole view of them.

## One directory, and a command instead of an index

```
<project_root>/
└── decisions/
    ├── ADR-NNN-<slug>.md
    ├── ADR-NNN-<slug>.md
    ├── ADR-NNN-<slug>.md
    └── ...
```

| Surface | Purpose | Lifetime | Read frequency |
|---|---|---|---|
| `perry-decide list` | id / status / type / title for every ADR, plus counts, expired sunsets, and the two conformance findings | Computed on every call from the files; nothing is stored | Every standup |
| `decisions/<ADR-ID>-<slug>.md` | One file per decision: Context / Options / Chosen / Consequences / Evidence / Sunset criteria | Append-only after creation; status field flips on supersede/expire/archive | On demand when the user or PMO needs the full reasoning |

**There used to be a `DECISIONS.md` index here and TASK-235 deleted it.**
DESIGN-013 § 5.3: it was twelve rows of pure projection whose own header told
the reader not to edit it, and `perry-decide list` already printed the same
content. § 4.1 of that design records what goes with it and calls it a real
property given up rather than an implementation detail — the rows were markdown
links into `decisions/`, so a reader browsing the repository on the web
navigated by them and now lands in the directory listing instead. A terminal
command cannot be linked to. **The design says outright that the implementing
row must not quietly re-add an index under another name**, and this page is
where a future reader would go looking for permission to.

## Language: configured doc language is mandatory

Before drafting any ADR, **read `.perry/config.md` § Document language**. The ADR's narrative content — Context, Options, Chosen, Consequences, Sunset criteria — MUST be written in that language. Citations (file paths, commit SHAs, code refs, evidence paths), the ADR id, and the `Type:` / `Status:` / `Date:` / `Supersedes:` **values** stay English regardless — they are matched by `bin/perry-state` and every downstream reader. There is no index heading left to localize — `perry-decide list` prints ids, statuses and titles as the files spell them; the full contract, including which field *names* may be localized and which may not, is `$PERRY_HOME/reference/i18n.md`.

This rule applies to all PMO-written artifacts but is called out explicitly here because ADRs are long-lived records the user reads months later. Mixed-language ADRs are hard to skim — one language per file, end to end.

Superseding or expiring an ADR does **not** translate it. An ADR is a record of what was decided and how it was written down at the time; if the project's document language later changes, existing ADRs keep theirs (`reference/i18n.md § Switching language mid-project`).

## Status model

Every ADR carries a `Status:` field. The values are declared **once**, in
`$PERRY_HOME/schema/state-schema.json § enums.decision_status`, and
`bin/perry-decide` reads them from there — this list and the one in
`schema/decide-list-contract.md` describe that enum, they do not define it.
`tests/test_decide_status_enum.py` fails if the three ever disagree. Five values:

- **proposed** — drafted and awaiting the user. The decision is written down but
  **not adopted**: it governs nothing yet. Before this value existed a draft ADR
  had to be filed as `active`, so a proposal was indistinguishable from a
  decision in force. An agent may write a `proposed` ADR unasked; only the user
  moves it to `active`. It renders in its own `## Proposed (awaiting the user)`
  section of the index, never under Active and never under "historical".
- **active** (default at creation) — currently in effect, governs ongoing work
- **superseded** — replaced by a newer ADR. Header has `Superseded by: ADR-NNN`. The superseding ADR has `Supersedes: ADR-NNN` (bidirectional link).
- **expired** — time-boxed acceptance whose sunset criterion fired (e.g., a temporary error-budget acceptance reaching its sunset date). The decision is no longer in effect; the user must take a new action. Header records the trigger reason + date.
- **archived** — historical record only; no longer governing, no superseding ADR, no active sunset. Used for decisions whose context has passed (e.g., a 5月 project decision that's irrelevant from 9月 onward).

Files **never move** on status change — only the `Status:` header field flips. This avoids breaking inbound links from journal entries / specs / other ADRs.

Every flip goes through the tool, which re-renders the index in the same call
and refuses a value the enum does not declare — including the two that move an
ADR in and out of `proposed`:

```bash
"$PERRY_HOME/bin/perry-decide" status ADR-NNN --status proposed   # draft it, unadopted
"$PERRY_HOME/bin/perry-decide" status ADR-NNN --status active     # the user adopts it
```

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

## Subcommand: `adr [<topic>]` and `--supersede` / `--expire` / `--archive`

### `/perry decide adr <topic>` — new ADR

**The typed fields are the tool's; the reasoning is yours.** That is ADR-007
rule 3 — *call the tool to write the fields, then generate the document from
what it returned* — and it is why the numbered walk below no longer contains a
step that composes an id, opens a template, or edits an index. Those three
steps existed here for a release, and the id one is the reason: a number
arrived at by eye is reused the first time two ADRs are filed in one session,
and a reused id does not dangle visibly.

1. **Read `.perry/config.md`** for document language. If absent, refuse and ask user to run top-level `/perry` first-time setup.
2. **Walk Context → Options → Chosen → Consequences** interactively with the user:
   - Use `AskUserQuestion` (header `"ADR Type"`) to pick Type from project hook's declared list (default `Process | Architecture | Operations | Risk | Cost | Design | Tooling`).
   - Use `AskUserQuestion` for binary / small-set yes/no in the Options walk if relevant.
   - Free-text prompt for Context, Options, Chosen rationale, Consequences.
3. **If time-bound**: ask for Sunset criteria explicitly (`AskUserQuestion` header `"Sunset"`, options): `Date-based (Recommended for documented exceptions) | Metric-threshold | Event-triggered | None — permanent decision`. Capture the actual triggers.
4. **Slug the title**: `<short-kebab>` (5-8 words max), lowercase, hyphenated. It is an *argument*, not a filename you compose — the tool joins it to the id it mints.
5. **Create the record with the tool.**

   ```bash
   "$PERRY_HOME/bin/perry-decide" new <slug> --title "…" --type <Type> \
       [--sunset "…"] [--deciders "…"] [--supersedes ADR-NNN]
   ```

   One call does what three separate hand steps used to ask for — *determine
   the next `ADR-NNN` by scanning and incrementing*, *write the file from the
   template*, *add a row to the index* — and it does them in one write: it mints the
   id from the files that exist, writes the header block with `Status`, `Type`,
   `Date`, `Supersedes` and `Sunset` filled, and **re-renders the index from
   every ADR on disk**. `--json` returns the id and the path; take both from
   the result rather than reconstructing them. `--dry-run` prints the plan and
   writes nothing.

6. **Generate the body at the path it returned.** `perry-decide new` writes a
   skeleton and says so in its own result: *"the ADR body is a skeleton — fill
   Context / Options / Chosen / Consequences by hand; this tool writes
   structure, never reasoning."* That split is ADR-007 rules 1 and 2 — the
   header is typed and belongs to Python, the argument is unbounded prose and
   belongs to you, and nothing parses the second. Leave the header block alone.
7. **Do not write the journal.** `journal/` is the `work` lane's file, and
   `$PERRY_HOME/SKILL.md § The hand-off contract` names *"`decide` writing
   `journal/`"* as one of three cases that must refuse. This step used to
   instruct it as a numbered instruction in the lane's primary procedure — the
   instruction was the bug, not the contract.

   If the decision deserves a line in today's journal, print the hand-off and
   stop: *"`ADR-NNN` recorded; if today's journal should note it, that is
   `/perry work`'s to write."* Asking and stopping is the contract; writing and
   apologising is the thing it forbids.
8. **Reply with the ADR path** + 1-line summary.

### `/perry decide adr --supersede ADR-NNN` — new ADR replacing an old one

Same flow as new ADR, with the supersession **passed to the tool** rather than
performed as three follow-up edits:

1. Create the successor with `--supersedes`:

   ```bash
   "$PERRY_HOME/bin/perry-decide" new <slug> --title "…" --type <Type> \
       --supersedes ADR-NNN
   ```

   In one call it fills the successor's `Supersedes`, flips the predecessor to
   `superseded`, fills its `Superseded by`, and re-renders the index — **in that
   order**, which is the ordering the old step 2 spelled out for a person to
   keep. It refuses if `--supersedes` names an ADR that does not exist, so a
   chain cannot be half-linked by a typo.

2. When both ADRs already exist, the same move is one command:

   ```bash
   "$PERRY_HOME/bin/perry-decide" supersede <OLD> <NEW>
   ```

3. Then generate the successor's body, as in step 6 above. Its References
   section should say what changed at the framing level; that is the part no
   tool can supply.

### `/perry decide adr --expire ADR-NNN [<trigger-note>]`

For time-boxed ADRs whose sunset fired:

1. **Flip the field with the tool**, which re-renders the index in the same
   call and refuses a status outside the declared set:

   ```bash
   "$PERRY_HOME/bin/perry-decide" status ADR-NNN --status expired
   ```

2. **Then write the account into the body**: a `## Status change` entry reading
   `Expired <YYYY-MM-DD> — <trigger note>`. `perry-decide` writes the field and
   deliberately not this — the status is typed and the reason is prose, and
   ADR-007 rule 2 is that Python never touches the second.
3. Surface the expiration in chat: "ADR-NNN has expired; you may need a new ADR to handle the now-uncovered situation."

### `/perry decide adr --archive ADR-NNN <reason>`

For ADRs whose context has passed (project pivot, scope change, etc.):

1. **Flip the field with the tool**, index re-rendered in the same call:

   ```bash
   "$PERRY_HOME/bin/perry-decide" status ADR-NNN --status archived
   ```

2. **Then write the account into the body**: a `## Status change` entry reading
   `Archived <YYYY-MM-DD> — <reason>`. Same split as `--expire`.

Use sparingly. Most retired ADRs should be `superseded` (have a successor) or `expired` (sunset hit). `archived` is for "this decision is just no longer relevant" — should be rare.

## Sunset / expiration auto-check

At every standup, PMO scans active ADRs with `Sunset criteria` for any date-based trigger that has passed today's date. If any fired but Status is still `active`:
- Surface in the dashboard as a 🚨 alert
- Suggest action: "ADR-NNN sunset date passed; run `/perry decide adr --expire ADR-NNN` or take the required action."

Metric-based and event-based triggers are NOT auto-checked (PMO can't reliably evaluate them without project-specific instrumentation). They are listed in the ADR for human reference; the user invokes `--expire` when they observe the trigger.

## Standup integration

The standup ritual (in `SKILL.md § Mandatory first move`) runs `perry-decide list --json` — headers only, never the ADR bodies — for:
- Total count by status (`active`, `total`)
- Most recent active ADR (for the `📝 Last decision` dashboard line)
- Any active ADRs with date-based sunsets that have passed (`expired_sunsets`)

It used to read an index file for the same three things. The command reads the
same headers the index was rendered from, so the standup cost is unchanged and
there is no longer a second copy that can be stale.

PMO reads specific `decisions/ADR-NNN-*.md` bodies only when needed — e.g., when an ongoing task references that ADR, or when the user asks "what did we decide about X".

## Bootstrap

Run once per project, from `decide/SKILL.md § init` — **not** from `/pmo`
bootstrap, which correctly refuses to create either path (`work/reference/bootstrap.md`).

1. **Create the pair with the tool.**

   ```bash
   "$PERRY_HOME/bin/perry-decide" bootstrap
   ```

   It makes `decisions/` and renders the index, and refuses if either already
   exists — safe on an existing project, useless to run twice.

   This replaces four hand steps (make the directory, copy the index template,
   copy the ADR template for a bootstrap marker, add that marker's row to the
   index), and the replacement is not cosmetic: **nothing ever ran them.**
   First-time setup invoked no `decide` subcommand at all, so every later step
   that "updates the index" was editing a file no code path produced, and every
   Perry project reported zero decisions forever.

2. **Then record the adoption as a real decision**, if the project wants one —
   through the same `adr` walk above, not from a template:

   ```bash
   "$PERRY_HOME/bin/perry-decide" new adopt-perry --type Process \
       --title "Adopt Perry's state layout for this project"
   ```

   and fill Context / Chosen / Consequences in the file it returns. There is no
   template-shaped "bootstrap marker" any more: a decision whose reasoning
   nobody wrote is a row, not a record, and it was pre-filling four fields with
   sentences no one had said.

## Migration: old monolithic `DECISIONS.md`

Projects that adopted Perry before this split still have a single-file `DECISIONS.md` with all ADRs inline. Migration is a **one-time manual operation** the user runs interactively with PMO — no dedicated subcommand. Procedure:

1. PMO reads the old `DECISIONS.md` top-to-bottom; identifies ADR boundaries (lines matching `^## ADR-NNN — `).
2. For each ADR: extract content; parse Type / Status / Date / Supersedes from the header section; slug the title (≤8 words, lowercase, hyphenated).
3. Write each to `decisions/ADR-NNN-<slug>.md` in the new schema (canonicalize header fields per `$PERRY_HOME/decide/state/ADR_TEMPLATE.md`). **Transcription is the exception, and this is the one place it applies**: the source is a document Perry did not write, so reading it is parsing by definition (ADR-007 § 6, answer 4) and there is nothing to call a tool with until the per-ADR files exist. The ids are the ones the old file already used — they are being *preserved*, not minted.
4. **Move the old monolithic file aside, then read the set back.**

   ```bash
   git mv DECISIONS.md evidence/<YYYY-MM>/decisions-pre-split.md
   "$PERRY_HOME/bin/perry-decide" list
   ```

   Nothing needs rendering: `decisions/` is the record, and `list` reads it.
   `total` must equal the number of `^## ADR-NNN — ` headers step 1 counted in
   the old file — that is the check that every transcribed ADR made it in, and
   `missing_type` names any whose header did not survive the transcription.

   `perry-decide bootstrap` is **not** run here. It creates `decisions/` and
   refuses when it already exists, which after step 3 it does.
5. Print the hand-off line for `work` to journal, if the migration deserves one. This lane does not write `journal/` — see step 7 of the `adr` walk above.
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
- `decisions/` is **`decide`-owned** — moved from `work` on 2026-08-16 by the signed hand-off contract, so that a settled decision and the document that settles it have one owner. `work` and `goals` read it freely and never write it. (This line said the opposite for a release; it was the concluding sentence of the moved lane's own reference.)
