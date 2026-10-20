# `/pmo digest` — read external documents, retain the gist

PMO's mechanism for handling **external input documents** the user provides (PDFs, spreadsheets, screenshots, pasted markdown, research papers, vendor contracts, etc.). Goal: human-style "read once, take notes, cite later" — NOT vector RAG, NOT auto-retrieval. PMO writes a structured digest per source, stores both source and digest in a topic-organized library, and references the digest by path in subsequent specs / decisions / work documents.

This is an Agent skill procedure, not a native CLI or background service.
Resolve the configured document root; inputs and knowledge paths below are
relative to that root. Existing source ownership and user authority still apply.
The kernel has no digest item or automatic source-age/referrer classifier.

## Two directories — clear separation

```
<agreed_document_root>/
├── inputs/                              # raw drop zone — user puts anything here
│   ├── 2025-12-09-vendor-acme-contract.pdf  # waiting to be digested
│   ├── pasted-error-budget-thresholds.md    # user paste, not yet processed
│   └── ...
└── knowledge/                           # post-digest organized library
    ├── vendor-acme/
    │   ├── 2025-12-09-contract.pdf       # moved from inputs/ on digest
    │   └── 2025-12-09-contract-digest.md
    ├── deploy-platform/
    │   └── 2026-05-01-snapshot.md
    ├── research/
    │   └── kubernetes-best-practices-2024-digest.md
    ├── _shared/                         # cross-topic / project-constitution
    │   └── USER-002-constraints-digest.md
    └── INDEX.md                         # Agent-maintained during the approved operation
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

1. Resolve the source under the agreed inputs root and inspect ownership. A source elsewhere requires an explicitly authorized copy/staging plan; never move a foreign or user-owned original merely to satisfy this layout.
2. Hash the source (SHA-256). Used later to detect source changes.
3. Detect file kind: `.md` / `.txt` (read directly), `.pdf` (use Read tool's PDF support), `.xlsx` / `.csv` (Read), screenshot images (Read).

### Reading + drafting

4. Read the full source. For long docs, read in chunks but produce ONE coherent digest.
4a. **Auto-classify document type** (see `## Document-type auto-detection` below). Two classes: `project-context` (default schema) vs `research-style` (academic paper / industry tech report — uses the extended schema). High-confidence classifications proceed silently; low-confidence cases ask the user once via `AskUserQuestion`.
5. Draft the digest using the schema matching the detected type (see `## Digest schemas`). Save to a working file at `inputs/<basename>-digest.draft.md` so the user can see progress.

### Verification (Q6: b+c locked)

6. Surface the **draft Key Facts** (5-15 bullets) to the user via `AskUserQuestion`, batched ≤4 at a time:
   - Header: `"Fact <N>"`
   - Options: `Correct (Recommended) | Refine wording | Wrong — drop | Source unclear — flag`
   - For "Refine" / "Wrong" / "Source unclear", follow up with a free-text prompt for the correction or note.
7. Surface the **draft Topics** (header `"Topics"`): user picks from existing knowledge subfolders (each as a multi-select option) + a free-text "new topic" option. Determines which `knowledge/<topic>/` subfolder.
8. Surface the **draft TL;DR**: `Accept (Recommended) | Refine | Reject — re-read source`.

### Move + commit

9. Choose target folder: `knowledge/<topic>/`. Create the subfolder if new.
10. With actual approval of the exact source/destination and checked collisions, move the owned staged source into knowledge. Preserve user originals, attached historical sources and untracked work; retain hashes and the actual operation in the digest.
11. Write the final digest: `knowledge/<topic>/<basename>-digest.md` (using the verified content).
12. Update `knowledge/INDEX.md` (see `## INDEX.md` below).
13. Record the source, destination, topics and verified facts in the digest itself. If this fulfils a task, attach the digest with kernel `attach add` and update that task through `$PERRY_HOME/reference/kernel.md`. Do not append a work journal entry.
14. Reply to user with the digest path + topic + 1-line summary.

### Refresh existing digest

`/pmo digest knowledge/<topic>/<existing-digest>.md --refresh`:
- Re-hash the source. If unchanged, exit "no refresh needed".
- If changed, or the user requests a new interpretation/template, re-read the affected source and surface changed claims. An unchanged hash alone does not prove continued relevance or acceptance.
- Per Q6c (user can hand-edit), respect any sections marked `<!-- user-edited -->` — do NOT overwrite without explicit AskUserQuestion confirmation.
- Update `Source SHA-256` and `Last digested` fields.

## Document-type auto-detection

Every digest run classifies the source into one of **two** types. The classification controls which schema/template is used downstream. **NO user-facing flag** — the agent decides from signals in the document itself, asks the user only when uncertain.

### The two types

- **`project-context`** (default) — anything the user drops in to give PMO project background: vendor contracts, internal docs, constraints lists, screenshots, user notes, regulatory text. Uses `work/templates/digest_TEMPLATE.md`. Typical length < 5000 words.
- **`research-style`** — academic papers, industry tech reports, white papers, formal technical notes. Uses `work/templates/digest_paper_TEMPLATE.md` (extended schema with Method / Results / Limitations / Reproducibility / Applicability / Followup citations). Typical length ≥ 8 pages.

### Classification signals

Compute weighted evidence from the source. These are Agent selection heuristics, not native guards or a mechanical semantic classifier. **Each signal toward `research-style` = +1 point. ≥3 points → high-confidence `research-style`. 0–1 points → high-confidence `project-context`. 2 points → ambiguous, ask user.**

| Signal | Counts toward `research-style` if … |
|---|---|
| Length | ≥ ~5000 words / ≥ 8 pages (PDF page count, or ≈ 30K chars in markdown/text) |
| Structural markers | Source contains explicit "Abstract", "References" / "Bibliography", numbered figure captions ("Figure 1: …"), equation blocks, DOI string, arXiv ID (`arXiv:NNNN.NNNNN`) |
| Citations density | ≥ 10 distinct external citations / bibliography entries |
| File source / URL | Path or URL contains `arxiv` / `acm` / `ieee` / `nature` / `springer` / `ssrn` / `nber` / named research-org domains; or filename pattern `<author>-<year>-<topic>.pdf` / pure arXiv ID `NNNN.NNNNN.pdf` |
| Writing style | First-person plural method narration ("We propose / We evaluate / Our results show"), hypothesis-testing language, defined notation introduced early |
| Section structure | Has at minimum 3 of: Introduction / Background / Method (or Approach / Methodology) / Experiments / Results / Discussion / Conclusion / Limitations |

### Behavior by confidence

- **High-confidence `research-style`** (≥ 3 signals): proceed silently with `digest_paper_TEMPLATE.md`.
- **High-confidence `project-context`** (≤ 1 signal): proceed silently with `digest_TEMPLATE.md`.
- **Ambiguous** (2 signals, or specifically conflicting evidence): one `AskUserQuestion` call, header `"Doc type"`, options: `Research-style — paper / tech report (Recommended) | Project-context — internal doc / constraints / notes`. User picks once, no further prompts; chosen template applies through the rest of the digest run.

The classification is logged in the digest's front-matter `Doc type:` field for audit. If the user disagrees later, they can manually flip the field and re-run `/pmo digest <existing-digest>.md --refresh` to regenerate with the alternative schema.

### Why no flag

The user already drops the source file at `inputs/<path>`. Adding `--paper` would force a decision the agent can make from the document's own structure — extra cognitive load with no upside. Auto-detect with explicit fallback to confirmation is the cleaner contract.

## Digest schemas (two variants share lifecycle, differ in schema)

Both schemas share: front-matter (Id / Source / SHA / Status / Topics / Referenced by), placement under `knowledge/<topic>/`, the same `Status: active | archived | eternal | superseded` lifecycle, the same `archive_inactive_days` archive-candidate detection, the same `knowledge/INDEX.md` registration.

They differ in **body sections** to match what's worth capturing about each type.

### Project-context schema (template at `work/templates/digest_TEMPLATE.md`)

```markdown
# Digest — <source filename>

> Id: SRC-<n>
> Source: knowledge/<topic>/<source-filename>
> Source SHA-256: <hash>
> Received: <YYYY-MM-DD> by <user paste | file drop>
> Last digested: <YYYY-MM-DD> by PMO
> Status: active | archived | eternal | superseded
> Superseded by: <filename or —>
> Topics: <comma-separated>
> Verification level: standard | strict
> Referenced by: <observed references, method/date/coverage; unknown when unmeasured>

**`Id:` is the citation handle, and it is minted once.** Take the next unused
`SRC-<n>` across all of `knowledge/`, never reuse one, and never renumber. A
finding written a year ago that cites `[SRC-n]` has to still resolve to the same
source — that is the whole point of a stable id, and it is why the number is not
derived from position, topic or filename, all of which move. Before a write, the skill checks every cited source ID against the complete digest set and opens its source; each digest needs an actual origin and date. An unresolved or duplicate ID stops publication. Use the project's single writer and recheck uniqueness immediately before committing; no native task ID counter is reused for document citations.

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

### Research-style schema (template at `work/templates/digest_paper_TEMPLATE.md`)

For academic papers and industry technical reports. Replaces the project-context body with sections that capture what's worth knowing about research:

- **TL;DR** — paper's core claim in plain user-language (NOT the abstract verbatim).
- **Method** — sample / dataset, setup, baseline, evaluation. Specific enough to judge soundness and transferability.
- **Key results** — number + the context that makes it meaningful (not just the paper's claim).
- **Limitations** — split: author-acknowledged + reader-observed (critical reading).
- **Reproducibility** — data available? code available? method clarity? barriers to reuse?
- **Applicable to this project?** — concrete verdict (`use` / `partially use` / `don't use`) + reason + landing point.
- **Followup citations** — 2–3 max, with one-line reason each is worth pulling. NOT a dump of the references list.
- **Open questions + What PMO must remember** — same as project-context schema; carried over because they're universal.

Extra front-matter fields (`Authors`, `Published`, `Source venue` like `arXiv:NNNN.NNNNN`) are added so the bibliography surface in the digest is searchable + citeable.

The rationale for each extra section is in `## Why a different schema for research` below.

### Why a different schema for research

Academic content has properties that the project-context schema underserves:

- **Reuse value lives in the method, not the result.** A paper's "we got 92.4% on X" matters less than "they did Y, this is whether Y transfers." The Method section forces capture of what's actually reusable.
- **Claims need critical reading, not bullet-point summarisation.** Limitations (both stated and observed) is mandatory because a digest without it sells the paper, doesn't evaluate it.
- **Reproducibility is the engineering gate.** "Could I do this myself?" should be answered before the paper's results are believed at face value.
- **Papers are nodes in a citation graph.** Followup citations capture the 2-3 worth-following edges so future-you knows where to read next.
- **Generalised "Key facts" loses precision.** Numbers without dataset / cohort / baseline are decoration; the research-style schema forces context attached to each result.

If a digest of a paper would fit comfortably into the project-context schema, that's a signal the paper wasn't worth a full digest in the first place — use a short note with the saved URL in an owned evidence document, attached to the related kernel task when one exists. Do not write to the retired journal.

## `knowledge/INDEX.md` — the catalog

The work Agent updates this authored catalog during an approved digest/archive operation. A retro may request a bounded refresh; no background indexer or automatic header parser maintains it. Preserve unrelated entries and report unknown/stale counts.

```markdown
# Knowledge index — <project name>

> Last updated: <YYYY-MM-DD>
> Counts: <actual bounded inspection and date, or unknown>

## Eternal (project constitution; never archived)

- _shared/USER-002-constraints-digest (C-1..C-5)
- _shared/OKR-anti-goals-digest

## Active by topic

### vendor-acme (3)
- 2025-12-09-contract (last ref'd 5d ago, by DATA-008-C-spec.md)
- 2026-05-01-vendor-acme-q1-report (last ref'd 12d ago)
- 2026-05-07-deploy-platform-rollout-plan (last ref'd today)

### deploy-platform (4)
- ...

### research (5, 2 stale > 60d)
- ...

## Archived (12)

- 2024-Q3-old-vendor-acme-quarterly (archived 2026-08-15: superseded by 2026-05-07-deploy-platform-rollout-plan)
- 2024-old-kubernetes-paper (archived 2026-09-01: research direction pivoted)
- ...
```

## Standup integration

After startup gates, list the exact input directory and read the knowledge index
or retained `tools/knowledge.py` output. Show measured undigested files, oldest
name/date and knowledge counts only when the source actually supplies them.
Unknown/unreadable sources remain unknown. Do not parse an old dashboard payload
or claim the retired deterministic next-rule evaluator has run.

The skill may recommend digesting the oldest relevant input or reviewing stale
knowledge under `reference/next.md`; cite the observed source and reason. Load
individual digests only when the user's question or selected task needs them.
A suggestion is not authorization to archive or rewrite a source.

## Archive lifecycle

### Status field on every digest

```
> Status: active | archived | eternal | superseded
```

- **active** (default at creation): standup counts; INDEX shows in main section; PMO may reference; appears in archive-candidate scans
- **eternal**: standup highlights; INDEX shows at top; **never** appears in archive candidates. Use for project-constitutional digests (USER-002 operating constraints / OKR Operating Principles / non-negotiable frameworks). User explicitly marks; PMO never auto-promotes.
- **archived**: standup ignores; INDEX moves to bottom "Archived" section; PMO doesn't search by default but **may grep on demand** if active set returns nothing relevant
- **superseded**: behaves like archived; header has `Superseded by: <newer-digest>` so the chain is traceable

Files **never move on archive** — only the header field changes. Avoids breaking references.

### Archive-candidate detection (Q7=a, Q8=one-shot)

When an authorized review actually needs this evidence, the Agent inspects the agreed knowledge scope. There is no scheduled stale scan. Evaluate source availability, observed references and documented dates; a missing scan result is unknown. A review can propose active digests matching:

1. `Status: active` AND an actually recorded last-reference date older than the agreed threshold, with a bounded inspection of:
   - the task store (kernel `query` (all task pages; see `$PERRY_HOME/reference/kernel.md`))
   - native event/attachment evidence for the selected period (event time is not last-read time)
   - `evidence/<YYYY-MM>/**.md` for last 90 days
   - `decisions/`
   - `phase/<NNN>-<slug>.md` (current phase) and recent `phase/snapshots/`
   using the agreed `archive_inactive_days` reference (default 90 days). Absence of a link or an old mtime cannot establish the date a source was last used; unknown age prevents an age-based recommendation.
2. Source file no longer exists (orphaned digest)
3. Header has `Superseded by:` filled in but `Status:` still `active`

### Per-candidate review (AskUserQuestion)

For each candidate, header = digest basename, options:

- `Archive (Recommended)` — flip `Status: archived`, set `Archived: <date> (reason: <user input>)`. INDEX moves to Archived section on next rebuild.
- `Keep active — still relevant` — note suppression date in INDEX so it's not re-flagged for 30 days.
- `Mark eternal — never propose archive` — flip `Status: eternal`. Featured at top of INDEX.
- `Delete entirely (digest + source)` — a separate destructive scope: first show exact paths, backlinks and recoverable bytes, check ownership and actual authorization, and preserve frozen migration/acceptance evidence. Never delete a source merely because it appears old.

### "I need an archived digest"

PMO behavior:
- Default: consult active/eternal sources when relevant; never append work history to a journal. Other lanes own their decision documents.
- On user request ("the old vendor-acme contract from 2024"): grep the archived section of INDEX.md.
- Re-activate: `/pmo digest knowledge/<topic>/<digest-name>.md --refresh` (refresh subcommand re-flips status to active automatically if user confirms).

## Per-project hook overrides

Recognized in `.perry/hook.md` under `## Digest archive thresholds`:

```
- Inactive days before archive candidate: 60      # tighter than 90
- Protected topics to review: <declared topics; eternal status still needs the actual user choice>
- Topics never to digest: scratch, temp           # PMO refuses /pmo digest on inputs/ tagged with these names
```

## Bootstrap

Only when the user selects knowledge/digest work, create the needed owned paths after the root first-run collision checks; do not create these eagerly for every new project:
- Empty `inputs/` directory
- Empty `knowledge/` directory
- `knowledge/INDEX.md` from `work/templates/knowledge_INDEX_TEMPLATE.md` (just headers, no entries)

## Why this isn't RAG

- **Bounded scope**: design assumes 5-30 active digests, not thousands.
- **Manual curation**: user (with PMO assistance) decides what gets digested + archived.
- **Cited semantics**: every fact in a digest carries `(§N)` source location — PMO can re-fetch the source for the exact quote when needed.
- **No vector embeddings**: lookup is by topic folder + filename + INDEX scan. PMO reasons about which digest to consult, not a retrieval algorithm.
- **No automatic top-K injection**: digests are loaded into context only when the model decides they're relevant — same way a human consults their notes.

If a project's knowledge needs grow past ~50 active digests, the design has hit its scope and a different tool is needed (true RAG, dedicated KB system, etc.). At that point, raise it as a Perry skill design question — don't pile more digests in.

## Completion routing

After completed writes from `digest`, follow [the shared closing step](../../reference/next.md#closing-step); its skip rules apply.
<!-- next-close: work digest -->
