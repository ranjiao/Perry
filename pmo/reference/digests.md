# `/pmo digest` — read external documents, retain the gist

PMO's mechanism for handling **external input documents** the user provides (PDFs, Excels, screenshots, pasted markdown, research papers, term sheets, etc.). Goal: human-style "read once, take notes, cite later" — NOT vector RAG, NOT auto-retrieval. PMO writes a structured digest per source, stores both source and digest in a topic-organized library, and references the digest by path in subsequent specs / decisions / journal entries.

## Two directories — clear separation

```
<project_root>/
├── inputs/                              # raw drop zone — user puts anything here
│   ├── 2025-12-09-term-sheet.pdf        # waiting to be digested
│   ├── pasted-r5-thresholds.md          # user paste, not yet processed
│   └── ...
└── knowledge/                           # post-digest organized library
    ├── gavi/
    │   ├── 2025-12-09-term-sheet.pdf    # moved from inputs/ on digest
    │   └── 2025-12-09-term-sheet-digest.md
    ├── bos/
    │   └── 2026-05-01-snapshot.md
    ├── research/
    │   └── jegadeesh-titman-1993-digest.md
    ├── _shared/                         # cross-topic / project-constitution
    │   └── USER-002-constraints-digest.md
    └── INDEX.md                         # auto-maintained
```

**Lifecycle**: `inputs/` → `/pmo digest <path>` → both source + digest move to `knowledge/<topic>/`. `inputs/` is transient; ideally empty after every digest pass.

## What lives in `inputs/` vs `knowledge/`

| | `inputs/` | `knowledge/` |
|---|---|---|
| **Purpose** | Drop zone for raw material the user provides | Curated library of digested sources |
| **Lifetime** | Ephemeral (should drain to 0 between sessions) | Long-lived, project knowledge base |
| **Organization** | Flat (no subfolders) — drop and forget | Topic-grouped subfolders |
| **PMO behavior** | Standup detects undigested files; prompts user to digest | Standup surfaces count + stale flags; PMO references when writing specs |
| **Git policy** | Markdown / text committed; PDF / Excel / screenshots gitignored. Keep originals locally. | Same — markdown/digests committed; large binaries gitignored. |

## `/pmo digest <path>` — the only command

Argument: a path inside `inputs/` (relative or absolute), or a magic string `--paste` to capture chat-pasted text inline.

### Pre-flight

1. Source exists at `inputs/<path>`. Refuse if path is anywhere else (use `mv` first).
2. Hash the source (SHA-256). Used later to detect source changes.
3. Detect file kind: `.md` / `.txt` (read directly), `.pdf` (use Read tool's PDF support), `.xlsx` / `.csv` (Read), screenshot images (Read).

### Reading + drafting

4. Read the full source. For long docs, read in chunks but produce ONE coherent digest.
5. Draft the digest using the schema below (see `## Digest schema`). Save to a working file at `inputs/<basename>-digest.draft.md` so the user can see progress.

### Verification (Q6: b+c locked)

6. Surface the **draft Key Facts** (5-15 bullets) to the user via `AskUserQuestion`, batched ≤4 at a time:
   - Header: `"Fact <N>"`
   - Options: `Correct (Recommended) | Refine wording | Wrong — drop | Source unclear — flag`
   - For "Refine" / "Wrong" / "Source unclear", follow up with a free-text prompt for the correction or note.
7. Surface the **draft Topics** (header `"Topics"`): user picks from existing knowledge subfolders (each as a multi-select option) + a free-text "new topic" option. Determines which `knowledge/<topic>/` subfolder.
8. Surface the **draft TL;DR**: `Accept (Recommended) | Refine | Reject — re-read source`.

### Move + commit

9. Choose target folder: `knowledge/<topic>/`. Create the subfolder if new.
10. Move the source file: `git mv inputs/<source> knowledge/<topic>/<source>` (or plain `mv` if source is gitignored).
11. Write the final digest: `knowledge/<topic>/<basename>-digest.md` (using the verified content).
12. Update `knowledge/INDEX.md` (see `## INDEX.md` below).
13. Append a journal entry to `journal/<YYYY-MM>/<today>.md` under `## Notes`: `Digested inputs/<source> → knowledge/<topic>/. Topics: <list>. Key facts: <count>.`
14. Reply to user with the digest path + topic + 1-line summary.

### Refresh existing digest

`/pmo digest knowledge/<topic>/<existing-digest>.md --refresh`:
- Re-hash the source. If unchanged, exit "no refresh needed".
- If changed: re-read source, diff against existing digest, surface ONLY the changed sections via AskUserQuestion (don't re-verify everything).
- Per Q6c (user can hand-edit), respect any sections marked `<!-- user-edited -->` — do NOT overwrite without explicit AskUserQuestion confirmation.
- Update `Source SHA-256` and `Last digested` fields.

## Digest schema (template at `state/digest_TEMPLATE.md`)

```markdown
# Digest — <source filename>

> Source: knowledge/<topic>/<source-filename>
> Source SHA-256: <hash>
> Received: <YYYY-MM-DD> by <user paste | file drop>
> Last digested: <YYYY-MM-DD> by PMO
> Status: active | archived | eternal | superseded
> Superseded by: <filename or —>
> Topics: <comma-separated>
> Verification level: standard | strict
> Referenced by: <auto-grep result; updated at INDEX rebuild>

## TL;DR (≤ 3 sentences)
<one paragraph>

## Key facts (with citations)
- **<fact label>**: <fact> (§<source location>)
- ...

## Open questions
- <thing PMO doesn't yet know but should track>
- ...

## What PMO must remember in future work
- <when topic X comes up, must reference Y>
- ...

## Section map (for targeted re-read)
- §1 ...
- §2 ...
```

## `knowledge/INDEX.md` — the catalog

PMO maintains this file automatically. Updated on every `/pmo digest`, archive operation, and full rebuild during `end-phase-retro`.

```markdown
# Knowledge index — <project name>

> Last updated: <YYYY-MM-DD>
> Active: <count> · Eternal: <count> · Stale: <count> · Archived: <count>

## Eternal (project constitution; never archived)

- _shared/USER-002-constraints-digest (R-1..R-5)
- _shared/OKR-anti-goals-digest

## Active by topic

### gavi (3)
- 2025-12-09-term-sheet (last ref'd 5d ago, by DATA-008-C-spec.md)
- 2026-05-01-look-capital-quarterly (last ref'd 12d ago)
- 2026-05-07-100pct-holdings (last ref'd today)

### bos (4)
- ...

### research (5, 2 stale > 60d)
- ...

## Archived (12)

- 2024-Q3-old-gavi-quarterly (archived 2026-08-15: superseded by 2026-05-07-100pct-holdings)
- 2025-jegadeesh-titman-paper (archived 2026-09-01: research direction pivoted)
- ...
```

## Standup integration

The standup ritual (in `SKILL.md § Mandatory first move`) gains:

- A scan of `inputs/` for undigested files. Count + name of oldest. If ≥ 1, surface in dashboard + suggest `digest`.
- A scan of `knowledge/INDEX.md` for active + stale + archived counts.

Dashboard line:

```
📥 Inputs    : <n> undigested (oldest: <name> @ <days>d) — run /pmo digest
📚 Knowledge : <active> active · <stale> stale · <archived> archived
```

When `inputs/` count > 0: include "drain inputs/ via /pmo digest" in the suggested next actions.

When stale ≥ 3: include "run /pmo end-phase-retro to triage archive candidates" or `mid-phase-review` (whichever is sooner).

**Digests are NOT loaded into standup context** (per Q4). Only existence + counts. PMO Reads specific digests when the user's question or task makes them relevant.

## Archive lifecycle

### Status field on every digest

```
> Status: active | archived | eternal | superseded
```

- **active** (default at creation): standup counts; INDEX shows in main section; PMO may reference; appears in archive-candidate scans
- **eternal**: standup highlights; INDEX shows at top; **never** appears in archive candidates. Use for project-constitutional digests (USER-002 R-rules / OKR Operating Principles / risk frameworks). User explicitly marks; PMO never auto-promotes.
- **archived**: standup ignores; INDEX moves to bottom "Archived" section; PMO doesn't search by default but **may grep on demand** if active set returns nothing relevant
- **superseded**: behaves like archived; header has `Superseded by: <newer-digest>` so the chain is traceable

Files **never move on archive** — only the header field changes. Avoids breaking references.

### Archive-candidate detection (Q7=a, Q8=one-shot)

Triggered automatically inside `mid-phase-review` and `end-phase-retro` (see `subcommands.md`). PMO scans `knowledge/` for active digests matching:

1. `Status: active` AND no reference to the digest path found in any of:
   - `BOARD.md`
   - `journal/<YYYY-MM>/*.md` for last 90 days
   - `evidence/<YYYY-MM>/**.md` for last 90 days
   - `DECISIONS.md`
   - `phase/<NNN>-<slug>.md` (current phase) and recent `phase/snapshots/`
   for ≥ `archive_inactive_days` (default **90 days**, override per-project hook)
2. Source file no longer exists (orphaned digest)
3. Header has `Superseded by:` filled in but `Status:` still `active`

### Per-candidate review (AskUserQuestion)

For each candidate, header = digest basename, options:

- `Archive (Recommended)` — flip `Status: archived`, set `Archived: <date> (reason: <user input>)`. INDEX moves to Archived section on next rebuild.
- `Keep active — still relevant` — note suppression date in INDEX so it's not re-flagged for 30 days.
- `Mark eternal — never propose archive` — flip `Status: eternal`. Featured at top of INDEX.
- `Delete entirely (digest + source)` — `git rm` both files; remove from INDEX. Use sparingly (loses history).

### "I need an archived digest"

PMO behavior:
- Default: only searches `Status: active | eternal` when picking references for new specs / journal / decisions.
- On user request ("the old GAVI Term Sheet from 2024"): grep the archived section of INDEX.md.
- Re-activate: `/pmo digest knowledge/<topic>/<digest-name>.md --refresh` (refresh subcommand re-flips status to active automatically if user confirms).

## Per-project hook overrides

Recognized in `.perry/hook.md` under `## Digest archive thresholds`:

```
- Inactive days before archive candidate: 60      # tighter than 90
- Auto-eternal topics: USER-002-constraints, OKR-anti-goals, R-rules
- Topics never to digest: scratch, temp           # PMO refuses /pmo digest on inputs/ tagged with these names
```

## Bootstrap

When `/pmo` bootstraps a new project (per `SKILL.md § Bootstrap`), also create:
- Empty `inputs/` directory
- Empty `knowledge/` directory
- `knowledge/INDEX.md` from `state/knowledge_INDEX_TEMPLATE.md` (just headers, no entries)

## Why this isn't RAG

- **Bounded scope**: design assumes 5-30 active digests, not thousands.
- **Manual curation**: user (with PMO assistance) decides what gets digested + archived.
- **Cited semantics**: every fact in a digest carries `(§N)` source location — PMO can re-fetch the source for the exact quote when needed.
- **No vector embeddings**: lookup is by topic folder + filename + INDEX scan. PMO reasons about which digest to consult, not a retrieval algorithm.
- **No automatic top-K injection**: digests are loaded into context only when the model decides they're relevant — same way a human consults their notes.

If a project's knowledge needs grow past ~50 active digests, the design has hit its scope and a different tool is needed (true RAG, dedicated KB system, etc.). At that point, raise it as a Perry skill design question — don't pile more digests in.
