# First-time setup — the procedure and its reasons

Tier 1. Loaded on demand from `SKILL.md § First-time setup`, which keeps the
gate that decides whether this runs at all. This page is the one body of the
procedure: run its steps in order.

Extracted from `SKILL.md` on 2026-08-18 (TASK-064); steps 1–3 followed on
2026-09-21 (TASK-470), carried over unchanged, and the router's one-line
summaries of steps 4–6 were dropped in favour of the bodies below.

## The procedure

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

3. **Confirm the project-wide preferences; write them to `.perry/config.jsonl` first** (`reference/first-run.md § Writing the config store`). One `AskUserQuestion` call: two questions, or three when step 2 found a collision:
   - **Document language** (header `"Language"`): `English | 中文 | other`, `(Recommended)` on whichever the user has been typing. Each `description` gives the consequence: files get this language; IDs and status words stay English.
   - **Repo layout** (header `"Repo layout"`): `Single repo (Recommended) | Split repo (PMO ↔ code)`.
   - **State root** (header `"State root"`) — **only when** step 2 reported a
     collision. `Put Perry's files under <suggested>/ (Recommended) | Use the
     project root anyway | Another directory`. Name the colliding path and its
     owner in the question; the user cannot evaluate the options otherwise.

   **Don't ask about chat language.** Set it to `follow user` and mirror what the user types. Document language governs **files**, chat language **replies**. Wordings: `reference/first-run.md`.

Steps 4–6 are the next two sections, in order.

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
   - Then, run `/perry work` — bootstraps the execution files (`journal/<current-YYYY-MM>/`, `PROJECT_STATE.md`, `evidence/`, `weekly/`, `handoff/`; `decisions/` belongs to the `decide` lane) and runs the first standup.
   - Then, run `/perry decide init` — creates `design/` **and** `decisions/` (via `perry-decide bootstrap`). **Do not skip this step.** It was absent from this chain for a release: `work`'s bootstrap correctly refuses to create the decision directory and names a `decide` bootstrap, `decide`'s `init` only made `design/`, and nothing here invoked `decide` at all — so every project that followed this list ended up with no decision record, and `adr` wrote its index row into a file that did not exist.
   - Finally, run `/perry goals plan-week` — proposes the first batch of weekly tasks, which `/perry work` then writes as BOARD rows + a journal entry under `## New tasks added`.
6. Ask: "Run `/perry goals init` now?" — if yes, read `$PERRY_HOME/goals/SKILL.md` and follow its `init` subcommand. If no, stop and let the user proceed at their own pace.

## Writing the config store

Step 3's answers (`§ The procedure`) go into `.perry/config.jsonl`
**before any other file**, through the tool and never by hand. The store is the
first write of every start: a project whose only files are markdown is not
installed (`schema/README.md § installed`), so it would be sent back to
first-time setup on every session.

```
"$PERRY_HOME/bin/perry-config" set --root . "Document language" "<language>"
"$PERRY_HOME/bin/perry-config" set --root . "Chat language" "follow user"
"$PERRY_HOME/bin/perry-config" set --root . "Repo layout" "<single or split>"
"$PERRY_HOME/bin/perry-config" set --root . "State root" "<state root>"
```

`State root` is `perry` unless step 2 found a collision and the user chose
otherwise. `Chat language` is never asked; it is `follow user`.

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
