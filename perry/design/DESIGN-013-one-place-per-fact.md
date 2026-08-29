# DESIGN-013: A fact with a schema lives in the store; a document holds what has none

> Status: locked
> Date: 2026-08-29 · Locked: 2026-08-29
> Author: Perry maintainer   · Implementation owner: Coding Agent
> Linked OKR: KR-O2.1 (`perry/OKR.md` v2, Objective 2 — every piece of state is queryable and writable by deterministic code)
> Supersedes: —   · Superseded by: —
> Revisits: `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md` (§ 6 decision 2, superseded by ADR-010), `reference/adoption.md`, `work/reference/subcommands.md`, `goals/reference/phases.md`
> Sign-off: User Decisions 1-4 answered by Ran Jiao in session on 2026-08-29, so this went `draft` -> `locked` without an `in_review` hold — that state exists to await exactly this sign-off. **Two answers went further than the recommendation**: D3 deletes `DECISIONS.md` where the draft recommended keeping it as a rendered view, and D4 decides `BOARD.md` now where the draft recommended deferring. Both consequences are recorded in § 4.1 rather than left in the option text.

## 1. Problem

Perry stores typed state in `.jsonl` and renders it into markdown. ADR-007
decision 2 made `BOARD.md` rendered output and a hand edit to it drift; TASK-092
did the same for `OKR.md` and `.perry/config.md`. The projection was kept because
a human reads it.

That decision bought a permanent tax, and on 2026-08-29 a census of every markdown
file under `perry/` measured what it costs and, more importantly, **what it is
actually buying**.

### 1.1 · The measurement

| File | bytes | inside table rows | outside | longest cell |
|---|---|---|---|---|
| `BOARD.md` | 43,289 | **42,099 (97%)** | 1,190 (2%) | **2,825 B** |
| `OKR.md` | 12,275 | 6,340 (51%) | 5,935 (48%) | 192 B |
| `DECISIONS.md` | 1,834 | 1,394 (76%) | 440 | 68 B |
| `phase/003-storage-code.md` | 13,905 | 2,224 (16%) | 11,681 | 307 B |
| `phase/003-linkage.md` | 4,923 | 0% table — YAML 3,573 B + prose 1,344 B | | |

Aggregates, for the directories the census must not disturb:

| Directory | files | bytes | table |
|---|---|---|---|
| `evidence/` | 325 | 1,929,966 | 8% |
| `journal/` | 9 | 512,546 | 2% |
| `design/` | 13 | 297,814 | 24% |
| `handoff/` | 9 | 102,320 | 11% |
| `decisions/` (ADR bodies) | 9 | 42,566 | 9% |
| `weekly/`, `knowledge/` | 3 | 8,929 | **0%** |

### 1.2 · What the numbers say, one file at a time

**`BOARD.md` is 97% table.** The natural language an agent reads is *inside the
cells* — `Next action` and `Summary` are paragraphs, and the longest single cell
is 2,825 bytes. Strip the tables and 1,190 bytes remain: a title, nine lines of
header prose, and eight empty `##` headings.

That prose is **already in `tasks.jsonl`**, because the board is rendered from it.
So on this file the question "should the tables leave the markdown" has no
content: there is no markdown-only prose to leave behind. The only coherent
version of the proposal is *delete the file and render it on demand*, and that
reverses ADR-007 decision 2, which the user made personally on 2026-08-19.

**`OKR.md` is 51/48 with a longest cell of 192 bytes.** Here the split is real.
The prose is Mission, Operating Principles, Anti-Goals and the per-objective
narrative — none of which belongs in a record, and one of which is the rule this
whole design serves:

> Never compute a number by reading files and eyeballing it. Perry's oldest rule;
> `bin/perry-state` exists because of it.

The tables are genuinely tabular and `okr.jsonl` already holds 34 KR records and
2 version records. Dropping the tables from `OKR.md` costs nothing that is not
recoverable by a command.

**`DECISIONS.md` is a 12-row index that already declares itself a view**, in its
own third line: *"Rendered by `bin/perry-decide` from `decisions/ADR-*.md`. Those
files are the record; this file is a view of them … do not hand-edit rows here,
they are overwritten."* It is a projection whose source is a set of documents
rather than a store. `perry-decide list` already prints it.

**The `phase/` pair is a genuine duplication with no check** — the same KR id,
title, metric and target in a markdown table and in a YAML frontmatter, and
`perry-lint` reports drift for four stores and nothing for this pair. It is
**out of scope here** and owned by TASK-157, because it is a defect that has
already produced a wrong number rather than an architecture question.

**Everything under `evidence/`, `journal/`, `design/`, `decisions/`, `handoff/`,
`weekly/` and `knowledge/` is a document.** `design/`'s 24% is each document's own
`User Decisions` table — part of that document, not a projection of anything.
`evidence/` and `journal/` are the record of what happened; rewriting them would
make the record disagree with itself.

### 1.3 · What the tax actually is

Every markdown table Perry writes must also be **parsed**, and parsing them is
where this project's most expensive open work lives:

- **TASK-050** — seven failed V4 rounds, on the single rule that a header cell
  has one normalization. Round 7 measured four LIVE header resolutions that
  revert to the historical defect with 2,882 tests green.
- **TASK-067** — the writer can destroy the table it writes to, and `perry-lint`
  cannot see it.
- **TASK-199** — `BOARD.md` carries two truth models and nothing marks the boundary.
- **TASK-234** — `.perry/conformance.md`'s row splitter is the *sixth*
  implementation of `split_row`, found by a V4 reviewer after five were unified.

Plus the projection machinery itself: the drift concept, `render --write`
recovery, the two-rename canonical pair and its crash recovery — a large part of
DESIGN-004.

**None of that tax is paid for prose.** It is paid entirely for reading back
tables that a store already holds.

## 2. Goals

1. **State a rule that decides where any given fact lives**, so this question is
   answered once rather than per file.
2. **Retire the markdown-table read path for the files where the tables are pure
   projection**, and with it the parsers that exist only to read them back.
3. **Do not lose the prose.** Mission, principles, anti-goals, narrative,
   reasoning and history stay in documents, unchanged and un-schematised.
4. **Prove the pattern on a cheap file before betting the board on it.**

## 3. Non-Goals

1. **Not touching `evidence/`, `journal/`, `design/`, `decisions/`, `handoff/`,
   `weekly/` or `knowledge/`.** They are documents. The record of what happened
   is never rewritten.
2. **Not moving prose into stores.** A 2,825-byte `Next action` is already an
   awkward JSON field; this design does not make that worse, and a jsonl line
   carrying a paragraph is a bad diff and a worse read.
3. **Not the `phase/` duplication** — TASK-157.
4. **Not `.perry/config.md`** (TASK-233) or `.perry/conformance.md` (TASK-234).
   Both are decided or filed separately and neither is a document/store split of
   the kind this design is about.

## 4. User Decisions

| # | Question | Options | Answer | Notes |
|---|---|---|---|---|
| 1 | Is the rule "a fact with a schema lives in exactly one store; a document holds what has no schema; no field lives in both"? | adopt as stated \| adopt with changes \| reject | **adopt as stated** | § 5.1. Adopting it means the current architecture violates it in **both** directions, and the rest of this document is the consequence. |
| 2 | Does `OKR.md` stop carrying its KR tables, with `perry-goals` printing them instead? | yes \| no | **yes** | § 5.2. The cheap, reversible proof of the pattern. `okr.jsonl` already holds the 34 records. |
| 3 | Does `DECISIONS.md` stop existing, with `perry-decide list` as the surface? | delete it \| keep it as a rendered view \| keep as-is | **delete it** | § 5.3. It already declares itself a view and is 12 rows of pure index. |
| 4 | Does `BOARD.md` stop existing, with a CLI render as the surface — superseding ADR-007 § 6 decision 2? | yes, and supersede it \| no, keep the projection \| defer until 2 and 3 have run | **yes, and supersede it** | § 5.4. **Recommended: defer.** This is the expensive one and the only one that reverses a signed decision. |

### 4.1 · Consequences accepted, 2026-08-29

**D3 went past the recommendation.** The draft recommended keeping `DECISIONS.md`
as a rendered view, on the ground that its rows are markdown links into
`decisions/ADR-*.md` and a reader browsing the repository on the web navigates by
them. The answer is **delete**. The consequence accepted: **that link surface
goes, and nothing replaces it in the repository itself** — a web reader lands in
`decisions/` and reads the directory listing. `perry-decide list` is a terminal
surface and cannot be linked to. This is recorded because it is a real property
being given up, not an implementation detail; the implementing row must not
quietly re-add an index to avoid it.

**D4 went past the recommendation.** The draft recommended deferring `BOARD.md`
until D2 and D3 had run, on three measured grounds: it is 97% table so this is a
deletion rather than a trim, it supersedes a signed decision, and the CLI render
becomes the *entire* read surface for a 2,825-byte `Next action`. The answer is
**do it now, with a superseding ADR**. Two consequences accepted:

1. **The CLI render is a prerequisite, not a follow-up.** The implementation plan
   in § 6 keeps its order for that reason — `OKR.md` and `DECISIONS.md` still run
   first, and the render they produce is what the board depends on. What D4
   changes is that the board is no longer *gated on a decision*; it is gated on
   the render being good, which is a question of fact.
2. **Every lane's entrance ritual is rewritten, and that cost is inside the
   `BOARD.md` row rather than discovered during it.** `SKILL.md`, `work/SKILL.md`,
   `goals/SKILL.md` and `decide/SKILL.md` all open by reading the board.

**What is NOT superseded, and this correction matters.** ADR-007 § 6 decision 2
answered *"Does `BOARD.md` stop being hand-editable?"* with *"Yes — it becomes
rendered output, and a hand edit becomes drift."* D4 does not restore
hand-editability; it removes the artifact. And ADR-007 § 6 decision 4 already
said *"the readers for `BOARD.md`, `OKR.md` and `.perry/config.md` go when those
become stores"* — so this design largely **completes ADR-007's own direction**
rather than reversing it. The single sentence superseded is that `BOARD.md`
exists as rendered output. Rules 1, 2 and 3 of ADR-007's `## Decision` stand
unchanged and are what § 5.1 extends.

## 5. Architecture

### 5.1 · The rule

> **A fact that has a schema lives in exactly one store. A document holds what
> has no schema. No field lives in both.**

The current architecture violates this in both directions, and naming both is
the point:

- **Documents hold schema'd fields.** `BOARD.md` carries `Status`, `Track`,
  `Stage`, `Verification` — every one of them typed in `schema/state-schema.json`
  and stored in `tasks.jsonl`. That is why drift detection has to exist.
- **Stores hold unschema'd prose.** `tasks.jsonl`'s `Next action` reaches 2,825
  bytes of paragraph. That is why a `tasks.jsonl` line is unreadable and its diff
  is unusable.

The second half is **not fixed by this design** and is called out as a known
violation (§ 7). Fixing it means giving prose its own home per row, which is a
bigger change than this document proposes.

### 5.2 · `OKR.md` — the proof

`OKR.md` keeps `## Mission`, `## Operating Principles`, `## Anti-Goals`, the
per-objective narrative and `## Versioning log`. It stops carrying the KR tables.
`perry-goals` gains a read-only render — the numbers come from `okr.jsonl`, which
already holds them.

This is the pattern's cheapest possible test: the tables are small, the cells are
short (192 B maximum), the store exists, and the file has 5,935 bytes of prose
that unambiguously belongs to it. If the pattern is wrong, it will be visibly
wrong here at low cost.

### 5.3 · `DECISIONS.md` — the cheapest cut

Nothing is lost by deleting it. It is 12 rows, no per-row prose, it is generated,
and its own header tells the user not to edit it. `perry-decide list` is already
the same content. The one thing to preserve is the **link surface**: the rows are
markdown links into `decisions/ADR-*.md`, and a reader browsing the repo on the
web uses them. That is the argument for "keep it as a rendered view" and it is a
real one — hence the three-way option in Decision 3 rather than a yes/no.

### 5.4 · `BOARD.md` — decided, and gated on the render rather than on a decision

`BOARD.md` stops existing. The surface is a CLI render from `tasks.jsonl` and
`risks.jsonl`.

The three measured facts that argued for deferring are still true and now become
requirements rather than reasons to wait:

1. **It is 97% table.** 42,099 of 43,289 bytes are inside table rows, so this is
   a deletion. The 1,190 bytes outside — the title, nine lines of header prose,
   eight section headings — are the only thing that could survive as a document,
   and none of it is worth a file.
2. **It supersedes ADR-007 § 6 decision 2**, which requires ADR-010 to exist
   before the row closes. See § 4.1 for what is and is not superseded.
3. **The render becomes the entire read surface** for a `Next action` that
   reaches 2,825 bytes. `perry-state --json` is the payload but it is not a
   reading surface; the render has to be good enough that a human running one
   command sees what opening the file showed them. Steps 1 and 2 of § 6 exist to
   build and prove that render on cheaper files first.

### 5.5 · Alternatives considered

- **Keep everything, add reconciles.** This is the status quo plus more checking.
  Rejected as the default because it grows the parser surface that TASK-050 has
  failed seven rounds against; but it is the honest fallback if Decision 1 is
  rejected.
- **Move prose into the stores and delete all markdown.** Rejected: § 5.1's
  second violation says a store is already a bad home for a paragraph, and this
  makes every document one.
- **Split by file rather than by field** — "these files are stores, those are
  documents". This is what the design actually proposes; the rule in § 5.1 is
  what makes the split decidable instead of per-file taste.

### 5.6 · Blast radius

`OKR.md`: `bin/perry-goals`, `viewer/parsers.py`'s OKR reader, `goals/SKILL.md`
and any lane that reads the KR table for a snapshot.
`DECISIONS.md`: `bin/perry-decide`, one reader, `SKILL.md` references.
`BOARD.md`: every lane, `SKILL.md`, `work/SKILL.md`, `reference/adoption.md`, and
the entrance ritual of every session — which is exactly why it is deferred.

## 6. Implementation plan

Ordered, and each step gates the next. All three are decided; the order is a
dependency chain, not a series of open questions.

1. **`DECISIONS.md`** (D3 — delete). Smallest surface, one reader, one writer.
   `perry-decide list` is the surface. The lost link surface is accepted in
   § 4.1 and must not be quietly re-added.
2. **`OKR.md`** (D2 — drop the KR tables). `perry-goals` renders them from
   `okr.jsonl`. The row must **report on whether the CLI render is a good enough
   read surface**, in writing. That report is step 3's input and the reason this
   step comes first.
3. **`BOARD.md`** (D4 — delete, with ADR-010). Runs after 1 and 2, and after
   ADR-010 is minted. Includes rewriting the entrance ritual in `SKILL.md`,
   `work/SKILL.md`, `goals/SKILL.md` and `decide/SKILL.md`.

## 7. Risks & mitigations

| Risk | Mitigation |
|---|---|
| The CLI render is worse than the markdown and nobody says so until the board is gone | **This is the main risk now that D4 is decided.** Steps 1 and 2 still run first and step 2 must report on read quality IN WRITING. Step 3 is gated on that report being affirmative — if it is not, step 3 stops and comes back here, rather than proceeding because the decision was already made. |
| Losing web/GitHub readability of a linkable artefact | **Accepted, not mitigated.** D3 chose deletion over a rendered view, and D4 removes the board. § 4.1 records what is given up. The mitigation that was available — keep a generated index — was declined, and the implementing rows must not re-add it to make the loss go away. |
| **The known violation this design does not fix**: stores hold unschema'd prose (`Next action`, 2,825 B) | Named here rather than left implicit. It gets worse in relative terms once markdown is gone, because the store becomes the only home. A follow-up row, not this design. |
| An agent's read path changes from "read one file" to "run a query" | `perry-state --json` is already that payload. But every lane's `SKILL.md` opens by reading the board, and step 3 must rewrite that ritual — counted as part of step 3's cost, not discovered during it. |
| Reversing a signed decision by accident | Decision 4 is worded as an explicit supersede of ADR-007 decision 2 and cannot be answered "yes" without minting that ADR. |

## 8. Open questions

1. Does the `Next action` prose problem (§ 5.1, second violation) deserve its own
   design, or is it a task row? It is the reason `tasks.jsonl` diffs are unusable
   today, independent of anything here.
2. `phase/00N-linkage.md` is YAML frontmatter with no table and 27-46% prose,
   machine-written and machine-read. Under § 5.1's rule it is a store with the
   wrong extension. TASK-157 touches it; whether it should be renamed is not
   asked there.

## 9. Changes (append-only after lock)

—

## 10. References

- `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md` — decision 2 is what
  Decision 4 would reverse.
- `perry/evidence/2026-08/TASK-157-spec.md` — the `phase/` duplication, measured.
- TASK-050, TASK-067, TASK-199, TASK-234 — the four open rows that exist because
  markdown tables are parsed.
- The census in § 1.1 was run on 2026-08-29 at `30cc467` over all 380 markdown
  files under `perry/`.
