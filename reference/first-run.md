# First-time setup — the parts the router points at

Tier 1. Loaded on demand from `SKILL.md § First-time setup`, which keeps the
namespace check and the `AskUserQuestion` block and points here for the rest.

Extracted from `SKILL.md` on 2026-08-18 (TASK-064) to keep the tier-0
router inside its byte budget. The prose is carried over unchanged.

## Why `perry` is the default state root, not `.`

**`perry` is the default, not `.`.** Two shapes in circulation is two code
paths a reader can disagree about, and one already did: `bin/perry-goals`
passed the project root where the state root was wanted, and the bug was
invisible on every `.`-rooted project — including the test fixture. A
subdirectory also removes the whole namespace-collision class rather than
detecting it, which is what the check above exists for.

## Why the namespace check runs before anything is asked

Without this step Perry claims a namespace it was not given. The escape
hatch used to be offered only on the adopt path, so a greenfield `/perry` in
a folder that already owned `design/` wrote straight over it with no question
asked — and every later lint run reported the user's own file as a malformed
Perry design doc. Never enumerate the claimed paths here; run the check.

## New project or existing one, and when to offer tracks

4. **Ask whether this is a new project or an existing one** — one `AskUserQuestion` (header `"Starting point"`, options: `New project — start from goals (Recommended if the folder is nearly empty) | Existing project — analyze what's here first`). The second option routes to **`/perry adopt`**: Perry reads the project's own evidence (README, roadmap, git history, existing design/ADR docs, TODOs, issues) and proposes candidates the user confirms, instead of interviewing from a blank slate. Read `reference/adoption.md` before running it. Adoption writes no state file directly — it produces a dossier, the user confirms it, and the normal subcommands materialize the result.

   **Then offer tracks, once, and only when it would change something.** If the
   folder shows a shape other than software — a `clients/` or `deliverables/`
   tree, a mail or ticket export, a `sources/`-shaped folder — ask one
   `AskUserQuestion` (header `"Work shape"`, options drawn from
   `$PERRY_HOME/modes/`: `One kind of work (Recommended if unsure) | Several
   kinds — set up tracks | Tell me the difference`). On the second, write a
   `## Tracks` table. On a plain software project, **skip the question
   entirely** — the implicit `main` track is right and asking costs a decision
   for nothing.

   For a new project, recommend the order below.

## The recommended order for a new project

5. Recommend the order:
   - First, run `/perry goals init` — interview to create `OKR.md` (mission, Operating Principles, 1–3 Objectives + KRs, Anti-Goals, version v1).
   - Then, run `/perry goals plan-phase <slug>` — creates the first phase OKR (`phase/001-<slug>.md`) with all 10 mandatory sections.
   - Then, run `/perry work` — bootstraps the execution files (`BOARD.md`, `journal/<current-YYYY-MM>/`, `PROJECT_STATE.md`, `evidence/`, `weekly/`, `handoff/`; `DECISIONS.md` and `decisions/` belong to the `decide` lane) and runs the first standup.
   - Then, run `/perry decide init` — creates `design/` **and** `DECISIONS.md` + `decisions/` (via `perry-decide bootstrap`). **Do not skip this step.** It was absent from this chain for a release: `work`'s bootstrap correctly refuses to create the decision files and names a `decide` bootstrap, `decide`'s `init` only made `design/`, and nothing here invoked `decide` at all — so every project that followed this list ended up with no decision record, and `adr` wrote its index row into a file that did not exist.
   - Finally, run `/perry goals plan-week` — proposes the first batch of weekly tasks, which `/perry work` then writes as BOARD rows + a journal entry under `## New tasks added`.
6. Ask: "Run `/perry goals init` now?" — if yes, read `$PERRY_HOME/goals/SKILL.md` and follow its `init` subcommand. If no, stop and let the user proceed at their own pace.
