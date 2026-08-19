---
name: decide
description: The `decide` lane of the `perry` skill — not a separate command. Loaded on demand by $PERRY_HOME/SKILL.md when a request is reached as /perry decide … (alias /perry design …). Design-doc and decision steward. Owns design/<DESIGN-ID>-<slug>.md, DECISIONS.md and decisions/ — RFC-style architecture / process / interface design documents and ADRs that lock decisions BEFORE the `work` lane opens implementation tasks. Read this lane when the user asks to draft an RFC or architecture doc, record or expire an ADR, lock a design decision, or add user-decision rows to a design. Hands off to the `work` lane once a doc reaches "Design locked": `work` opens implementation tasks whose evidence files back-reference the design ID. Reads OKR.md / phase/ for goal context and BOARD.md to surface in-flight implementation work for any locked design.
---

# design — Perry's design-doc steward

> **This is a lane inside `/perry`, not a separate command.** Perry registers one skill;
> this file is loaded on demand by the router when a request needs design-doc / RFC stewardship.
> Invoke as `/perry design <subcommand>` — or just `/perry <subcommand>`, since
> subcommand names are unique across lanes. The shorthand `/design <subcommand>`
> used throughout this file and its `reference/` pages is routing vocabulary for
> the agent, not a command the user can type; translate it when quoting a command
> back to them. Rationale for the single entrance: `$PERRY_HOME/SKILL.md § One
> skill, three lanes`.

Part of the **Perry** skill set (`okr` + `pmo` + `design`). The "decided" layer that sits between OKR's "why" and PMO's "how": before non-trivial implementation work fans out into many tasks, the design skill produces a single locked document that names the problem, the user decisions, the architecture, and the non-goals.

Voice: structured, decision-oriented, friction-friendly. The design skill refuses to mark a doc "Design locked" unless the User Decisions section is fully resolved — it would rather show an open question than write fiction.

## Companion skills

Pairs with **`pmo`** and **`okr`**. Hand-off rules:
- `decide` is the **only writer** of `design/<DESIGN-ID>-<slug>.md`, **`DECISIONS.md` and `decisions/ADR-NNN-*.md`**.
- `design` reads `OKR.md` / `phase/` for goal context (read-only) and reads `BOARD.md` to surface which implementation tasks reference each locked design.
- Once a doc reaches **Design locked**, `design` hands off to `pmo`: print a list of proposed implementation tasks (each tagged with the design ID); user approves; `pmo add-task` writes them to `BOARD.md`. PMO's evidence files for those tasks back-reference the design ID in their first lines.
- `design` never writes `BOARD.md`, `journal/`, `OKR.md`, `phase/`, `evidence/`, or any other Perry-owned file.

## When this skill activates

Trigger on any of:
- The user invokes `/design` or types "design doc" / "RFC".
- The user types "/design help" or "/design help <subcommand>" — see `### help` under the Subcommand index; do NOT trigger the Design Snapshot for help.
- The user says "let's design X before we build it", "lock the architecture", "write the user decisions for Y", "what's the design for Z".
- A new session opens in a project that contains a `design/` directory.
- PMO surfaces a design-shaped task (multi-system, irreversible, or with multiple open user decisions) and routes the planning step here before delegating implementation.

## Mandatory first move: the Design Snapshot

Always run before any subcommand. If `design/` doesn't exist, see Bootstrap.

−3. **Set `$PERRY_HOME`** — if unset in env, derive from this SKILL.md's path: it's the perry/ root dir (the grandparent of `decide/SKILL.md`).
−2. **Detect host** — `bash "$PERRY_HOME/bin/perry-detect-host"`. Remember as `$HOST` and read `$PERRY_HOME/reference/host-capabilities.md` once. All later references to `AskUserQuestion` in this file follow that matrix (Codex = numbered free-text fallback).
−1. **Run the weekly auto-update check** — `bash "$PERRY_HOME/bin/perry-update-check"`. Throttled to once per 7 days; surface any output verbatim.
0. **Read `.perry/config.md`** if present, for document language, chat language and repo layout. Design docs are written in `Document language`; the snapshot and every `AskUserQuestion` are rendered in `Chat language` (mirror the user when unset). Section headings localize through the glossary in `schema/state-schema.json § i18n`; `DESIGN-NNN` ids, slugs, `Status:` values (`draft` | `in_review` | `locked` | …) and code references stay English in every language — a `User Decisions` row may read `| 1 | 缓存后端 | Redis \| Memcached \| DynamoDB | TBD | — |`, with the question localized and the options left as the literal identifiers they name. Contract: `$PERRY_HOME/reference/i18n.md`. If on a split layout and a design doc references code, paths must be absolute (or commit-SHA-pinned) so the code repo can be located.
1. **Read `.perry/hook.md`** if present (project-specific hook).
2. **Compute the state — one call**: `"$PERRY_HOME/bin/perry-state" --section design`. Deterministic, read-only. It scans `design/` for every `*.md`, normalises each `Status:` (`draft` | `in_review` | `locked` | `superseded` | `dropped`) and `Date:`, and cross-checks `BOARD.md` for implementation rows that back-reference each design ID — so `pending_handoff` lists exactly the locked docs PMO hasn't opened tasks from. Every count in the snapshot comes from this payload.
3. **Read a doc's full text** only when the conversation is about its content (`decide`, `lock`, `revise`, or a question about one doc). The payload answers "how many, which status, how stale" without loading them all.
4. **Render the headline + snapshot.** Two parts, in order:

   **Part A — TL;DR** (exactly one line, plain language, **no leading ID**). The single most important thing about the design lane right now, in human terms. If nothing is pressing, say so explicitly — don't manufacture urgency. Examples:
   - `TL;DR: DESIGN-002 is locked but has no implementation tasks yet — run handoff.`
   - `TL;DR: DESIGN-003 has 3 open user decisions blocking lock — run decide.`
   - `TL;DR: Nothing in review — design lane is quiet.`

   **Part B — Snapshot** — fixed shape, no further preamble:

   ```
   📐 Design docs · <project name>

   Locked   : <count>   (oldest unimplemented: <DESIGN-ID> @ <days>d)
   In review: <count>   (oldest: <DESIGN-ID> @ <days>d)
   Draft    : <count>
   Superseded/Dropped: <count>

   <DESIGN-ID> · <title> ............ <Status> · <date> · impl <done>/<total>
   <DESIGN-ID> · <title> ............ <Status> · <date> · impl <done>/<total>
   ...                               (top 5 by recency or lock date)
   ```

   Use `—` for empty fields. Never fabricate.

5. **Suggest 1–3 next actions**:
   - "DESIGN-002 in_review for 8d → run `lock` or `revise`"
   - "DESIGN-001 locked 5d ago, no impl tasks in BOARD.md → run `handoff DESIGN-001`"
   - "DESIGN-003 has 3 open user decisions → run `decide DESIGN-003`"

6. Then ask: **"What do you want to do?"**

## Status model

A design doc carries exactly one of these states in its `Status:` header:

- `draft` — being written; sections may be incomplete; no commitment.
- `in_review` — author thinks it's done; awaiting user sign-off on the User Decisions section.
- `locked` — User Decisions resolved, architecture frozen for the implementation that follows. Edits after lock require a `## Changes` entry with date + reason; structural pivots require `revise` (new version) or `supersede` (new doc).
- `superseded` — replaced by a newer doc. Header must point to the successor (`Superseded by: DESIGN-XXX`).
- `dropped` — abandoned without superseding. Header must include a `Drop reason:` line.

**Locking rule (non-negotiable)**: a doc cannot move to `locked` while any User Decision row is unanswered or marked TBD. Refuse the move and list the open rows.

## Document schema

Every design doc uses these sections in this order. Sections marked **required** must be present at lock time; optional sections may be empty if irrelevant.

1. **Header** (required) — `# DESIGN-<id>: <Title>` then a metadata block:
   ```
   > Status: <draft | in_review | locked | superseded | dropped>
   > Date: <YYYY-MM-DD> · Locked: <YYYY-MM-DD or —>
   > Author: <role or name>   · Implementation owner: <role or "TBD">
   > Linked OKR: <O-id / KR-id, or —>
   > Supersedes: <DESIGN-XXX or —>   · Superseded by: <DESIGN-XXX or —>
   ```
2. **Problem** (required) — what specific pain or constraint this design exists to address. Concrete: cite incidents, file paths, observed behavior, not abstract goals.
3. **Goals** (required) — what success looks like; numbered, testable.
4. **Non-Goals** (required) — what this design will deliberately NOT do. Often more important than Goals.
5. **User Decisions** (required) — table of decisions only the user can make, with the chosen option and date. ALL rows must be resolved before lock.
   ```
   | # | Decision | Options | Chosen | Date |
   |---|---|---|---|---|
   ```
6. **Architecture** (required) — the actual design. Diagrams (ASCII or mermaid), data flow, components, interfaces, file/path layout, sequence diagrams as needed.
7. **Implementation plan** (required at lock) — ordered phases or workstreams, each with a one-line scope and the proposed PMO task ID(s). This section is the seed for PMO's `add-task` after lock.
8. **Risks & mitigations** (required) — what could go wrong; how each is detected and mitigated.
9. **Open questions** (optional) — non-blocking items deferred for later. Blocking questions belong in User Decisions.
10. **Changes** (append-only after lock) — `YYYY-MM-DD — <what changed> — <why>`. Structural changes require `revise` instead.
11. **References** (optional) — links to OKR sections, prior designs, external docs, code paths.

Templates live at `state/design_TEMPLATE.md`.

## Subcommand index

For navigation help: `/design help` prints this index; `/design help <subcommand>` prints just that row plus the matching section below.

| Subcommand | One-line | Section |
|---|---|---|
| `init` | First-time bootstrap of the lane: `design/` + README, **and** `DECISIONS.md` + `decisions/` via `perry-decide bootstrap` | Subcommands |
| `new <slug>` | Start a new design doc (interactive: title, ID, KR linkage) | Subcommands |
| `resolve <DESIGN-ID>` | Walk unresolved User Decisions rows; each → AskUserQuestion | Subcommands |
| `adr <topic>` | New ADR → `decisions/ADR-NNN-<slug>.md`; re-renders the `DECISIONS.md` index. Written by `perry-decide new` / `supersede` / `status`, never by hand | `reference/decisions.md` |
| `lock <DESIGN-ID>` | Move `in_review` → `locked`; print impl tasks for PMO `add-task` | Subcommands |
| `revise <DESIGN-ID>` | Material change after lock; appends `## Changes` | Subcommands |
| `supersede <OLD-ID> <NEW-slug>` | Replace one doc with a successor | Subcommands |
| `drop <DESIGN-ID> <reason>` | Mark `dropped` (problem went away / pivoted past) | Subcommands |
| `handoff <DESIGN-ID>` | Re-print impl tasks for a locked doc | Subcommands |
| `status [<DESIGN-ID>]` | Without arg: snapshot. With arg: that doc's full status | Subcommands |
| `help [<subcommand>]` | Print this index; with arg, print + read matching section | (handled here) |

Peer skills: `/pmo help` (execution) · `/okr help` (goals) · `/perry help` (combined overview)

### `help [<subcommand>]`

Without arg: print the **Subcommand index** table above plus a short pointer to peer skills.

With arg: locate the row for `<subcommand>`, print it, then read the matching `### <subcommand>` section below so the full procedure is in context. If the user types a subcommand that doesn't exist, suggest the closest match.

`help` does NOT trigger the Design Snapshot (it's a navigation command).

## Subcommands

### `init` — first-time bootstrap of the whole lane
Run once per project. Two halves, and **both are required** — `init` used to do only the first:

1. **`design/`** — create the directory and write `design/README.md` documenting the local DESIGN-ID convention (default: `DESIGN-NNN` zero-padded; projects may override in their hook to use domain prefixes like `INFRA-NNN`, `API-NNN`, etc.). No design docs are created.

2. **`DECISIONS.md` + `decisions/`** — created by the tool, not by hand:

   ```
   "$PERRY_HOME/bin/perry-decide" bootstrap
   ```

   It refuses if either already exists, so it is safe to run on an existing project and useless to run twice.

> **This second half did not exist, and its absence was silent.** `work/reference/bootstrap.md` correctly refuses to create those two paths — they belong to this lane — and said "`decide`'s own bootstrap creates them". This section said the opposite: it created `design/` and stated it "does not create any docs". First-time setup never invoked a `decide` subcommand at all. So `adr`'s then-step 7, "update the `DECISIONS.md` index", ran against a file no code path produced, and every Perry project reported zero decisions forever. Found by a fresh-context review, 2026-08-17. That step no longer exists: `perry-decide` renders the index on every write, and the procedure calls it (ADR-007 rule 3, TASK-096).

### `new <slug>` (interactive)
Start a new design doc. Prompts:
1. Title.
2. ID (auto-suggest next available; user can override).
3. Linked OKR Objective/KR (optional).
4. Implementation owner (role or TBD).

Writes `design/<DESIGN-ID>-<slug>.md` from `state/design_TEMPLATE.md` with `Status: draft`. Walks the user through Problem → Goals → Non-Goals as the first writing pass; leaves User Decisions / Architecture / etc. for follow-up sessions.

**Input-quality pass** on that first writing pass: run `$PERRY_HOME/reference/input-quality.md § 3 Design doc` against Problem / Goals / Non-Goals (concrete problem, substantive Non-Goals, testable numbered Goals). Surface ≤3 issues, advisory + override. Catching a thin Non-Goals here means `lock` isn't the first time the user hears about it.

### `resolve <DESIGN-ID>`

> The `decide` alias was withdrawn. With the lane itself named `decide`,
> `/perry decide` became unparseable — a lane with no subcommand, or a
> subcommand missing its argument? An alias that makes the entrance ambiguous
> costs more than the muscle memory it saves, and the rename existed to remove
> exactly this collision rather than move it one level up.
Walk every unresolved row in the User Decisions table. For each: present the options, ask the user to pick (or to add an option), record the choice with today's date. Refuse to "decide on the user's behalf" — leave TBD if the user cannot decide now.

**Use `AskUserQuestion`** to render each row's options as buttons (header = decision number or short topic, ≤ 12 chars). The Options column in the User Decisions table is written pipe-separated (`A / B / C`) precisely so each token maps to one `AskUserQuestion` option. Batch up to 4 unresolved rows per `AskUserQuestion` call. The user can always pick "Other" to add a new option, in which case append it to the row's Options list and record the choice.

### `lock <DESIGN-ID>`
Move a doc from `in_review` → `locked`. Pre-flight checks:
- All required sections present and non-empty.
- User Decisions table has zero TBD / blank rows.
- Implementation plan section has at least one proposed task.

If any check fails, refuse the move and print the gap list. **Then run the advisory input-quality pass** (`$PERRY_HOME/reference/input-quality.md § 3`) over the whole doc — the hard checks above are the *floor* (empty section / open decision = refuse); the pass adds the softer coaching (alternatives considered, implications spelled out, risks name detection + mitigation) as ≤3 suggestions the user can fix or override. Advisory only — a clean-floor doc still locks even if the user overrides a suggestion. On success: set `Status: locked`, fill `Locked: <today>`, then **print the implementation tasks to chat** in PMO's `add-task` schema (Owner, Priority, Deliverable, Verification, Dependencies, Out of scope). **Use `AskUserQuestion`** (header `"Hand-off"`, options = `Hand to PMO now (Recommended) | Edit before handing off | Skip — manual paste later`) to collect the user's hand-off decision.

### `revise <DESIGN-ID>`
For material changes after lock that don't warrant a new doc (small architecture refinements, decision updates that don't break implementation). Walks: what's changing, why, which Implementation plan items are affected. Bumps the `Date:` (keeps `Locked:`), appends a `## Changes` entry. Writes the accompanying ADR itself — `DECISIONS.md` and `decisions/` are this lane's files (`$PERRY_HOME/SKILL.md § The hand-off contract`). Use `adr <topic>` with `Type: Design`.

**First step**: use `AskUserQuestion` (header `"Revise scope"`, options = `Decision update | Architecture refinement | Implementation re-sequence | Use supersede instead (Recommended if structural)`) to gauge the change kind. If the user picks `Use supersede instead`, route to `supersede` and stop here.

### `supersede <OLD-ID> <NEW-slug>`
Mark `OLD-ID` as `superseded`, point its header to a new doc, and run `new` to create the successor. The successor's References section must cite the predecessor and explain what changed at the framing level.

### `drop <DESIGN-ID> <reason>`
Move the design doc to `Status: dropped` with a `Drop reason:` line. Used when the underlying problem went away or the project pivoted past it. Then record the drop as a decision through `adr <topic>` with `Type: Design` — `perry-decide new` mints the id, writes the header and re-renders the index; the index is never edited here.

If the user invokes `drop` without a reason, **use `AskUserQuestion`** (header `"Drop reason"`, options = `Problem went away | Pivoted past it | Replaced by other work (Recommended if you saw it in another spec) | Other`) to nudge a categorization; require free-text elaboration after the bucket selection. Reason is mandatory — refuse to drop without one.

### `handoff <DESIGN-ID>`
For a locked doc whose Implementation plan is still un-handed-off. Re-prints the implementation task list in PMO's `add-task` format. Shortcut for re-running the lock-time prompt.

### `status [<DESIGN-ID>]`
Without an ID: print the snapshot. With an ID: print that doc's full status — section completeness, open user decisions, current `Status:`, days in current state, linked BOARD.md rows (count by status), recent Changes entries.

## State files

| File / dir | Owner | Purpose | Template |
|------------|-------|---------|----------|
| `design/<DESIGN-ID>-<slug>.md` | design | One design doc per ID | `state/design_TEMPLATE.md` |
| `design/README.md` | decide | Local DESIGN-ID convention + index | (written on `init`) |
| `DECISIONS.md` + `decisions/ADR-NNN-*.md` | decide | ADR index + one file per decision. Moved here from `work` by the signed hand-off contract, 2026-08-16 — a settled decision and the document that settles it now have one owner | `state/ADR_TEMPLATE.md` |
| `OKR.md`, `phase/<NNN>-<slug>.md` | okr | Read by design for goal context; never written | (in okr skill) |
| `BOARD.md` | pmo | Read by design to count implementation rows; never written | (in pmo skill) |

Design docs live in their own `design/` directory at the project root, parallel to `evidence/`, `weekly/`, etc. They are not stored under `evidence/` because they are decisions, not artifacts of completed work.

## Bootstrap

If `design/` doesn't exist:
> "No design lane in `<project>`. Run `init` to create `design/` and the local convention? (yes/no)"

If `DECISIONS.md` doesn't exist — which is a **separate** check, because a project can have one and not the other:
> "No decision record in `<project>`. Run `perry-decide bootstrap` to create `DECISIONS.md` and `decisions/`? (yes/no)"

Check both. They were one question for a release, and the half nobody ran is the half that never got created.

If `design/` exists but contains no docs:
> "Design lane exists, no docs yet. Run `new <slug>` to start one?"

## Hand-off contract with PMO (the most important rule)

A locked design doc is a contract: it names the problem, the chosen architecture, and the implementation phases. PMO's job after lock is to turn the Implementation plan into rich task blocks in `BOARD.md`. Each implementation task's evidence file (`evidence/<YYYY-MM>/<TASK-ID>-*.md`) must reference the design ID in its first lines so a future reader can trace any artifact back to the decision that authorized it.

Conversely, design docs **must not** restate task-level execution status — that lives in `BOARD.md` and `evidence/`. The design doc is frozen at lock time except for `## Changes` entries; ongoing implementation noise belongs in PMO's lane.

If you find yourself wanting to update a locked design with implementation details, that's a sign you should either (a) write an evidence file under PMO's lane, or (b) `revise` / `supersede` if the architecture itself changed.

## Style rules

- **Lead with the snapshot, not narration.**
- **Refuse to lock a doc with open user decisions.** Print the gap list.
- **Cite paths and IDs.** Every claim ("DESIGN-002 has 3 open decisions") points to the file.
- **Append-only after lock.** Use `## Changes` for small edits, `revise` / `supersede` for structural ones.
- **Don't duplicate PMO state.** Implementation status lives in `BOARD.md`, not in design docs.
- **Don't invent state.** If a doc is missing a required section, say so — don't fabricate one.

## Per-project hooks (optional)

```
If the project is **<name>**:
- DESIGN-ID convention: <e.g., INFRA-NNN / API-NNN / DESIGN-NNN>.
- Required extra sections: <project-specific, e.g., "Cost analysis", "Security review">.
- Default Implementation owner: <role>.
- Designs that REQUIRE additional review: <criteria, e.g., "any design touching production permissions">.
- Cross-references: <e.g., "code repo references designs by ID in commit messages">.
```

For projects without a hook, the generic schema and DESIGN-NNN convention apply.

## See also

- [../SKILL.md](../SKILL.md) — top-level Perry routing.
- [../work/SKILL.md](../work/SKILL.md) — execution stewardship; consumes locked designs.
- [../goals/SKILL.md](../goals/SKILL.md) — goal-setting; provides KR linkage for designs.
