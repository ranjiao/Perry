# PMO task creation

### `add-task` (interactive)
After OKR `plan-week` (or any other source) proposes a task and the user approves, PMO does THREE things — the third is conditional on priority.

**First, an input-quality pass** (`$PERRY_HOME/reference/input-quality.md § 4 Task`): check the task's Verification is falsifiable (not "looks good"), Deliverable is an artifact (not an activity), **Summary is written for a reader who was not in this conversation** (§4.6), Owner is a single value from the Owner model, Priority is justified (P0 only if it blocks a Must-Have), and a `kr:` linkage is present when the task came from `plan-week`. Surface ≤3 issues, advisory + override — fix with the user or write as-is with a one-line journal reason. Never silently rewrite. (Tasks arriving already-clean from `plan-week`, which ran the same §4 pass, usually pass with `✓ Input quality: clean`.)

**Write the `--summary`, and write it for a stranger.** This is the one field on the row whose whole job is to be legible to somebody who was not here. The title is shorthand — `D009 step 3 — the O-1 mint and the write-back to the store` is perfectly clear to the two of you and says nothing to the person who opens the board in three weeks. The summary is what `perry-explain <ID>` prints and what a front-end renders, so a row without one is a row nobody can pick up without re-reading a design document.

`perry-task add` **refuses without it** — the same hard refusal `--deliverable` and `--verification` already carry, and for the same reason. It is a hard gate rather than an advisory because **the advisory version has already been tried on this exact field and measured**: `--summary` was an optional flag from contract 1.11, nothing asked for it and nothing checked it, and it reached 25 of 114 open rows. `DESIGN-003 § 4` decision 4's "advisory first, hard gate next" does not apply here, because its stated reason is retroactive invalidation and `add` has no retroactive half — it governs only rows minted from now on. The rows minted before are reported, not refused, by `perry-lint --summaries`.

Two or three sentences of plain language: *why this row exists* and *what is true when it is done*. Cite the design or decision it comes from if there is one — a leading `DESIGN-012 § 5.1.` then the explanation is this project's house style and is encouraged, not penalised. What `add` refuses is **structural only**: a summary that folds to the title again, one containing no sentence, one under five words. It does not judge whether the prose reads well, and you should not write to please it — write to be understood.

```
--summary "Perry ships two opposite orderings of the phase-close pipeline.
           Nothing picks one, so whoever runs it picks by which page they read."
```

**Then, the KR-attribution gate** (`$PERRY_HOME/reference/okr-linkage.md`) — hard, not advisory: resolve the task's KR by stable ID through `linkage.jsonl` (explicit `kr:` → Project ID → registered alias). If it resolves to exactly one KR, set `kr:` and continue. If it resolves to zero or many — a drifted/ambiguous name, or a Project no registry row claims — **do NOT fuzzy-match**: ask the user (`AskUserQuestion`, header `"KR attribution"`, options = the candidate KR IDs + text, plus "Other → new/none"). Record the chosen KR in the spec, then **hand the result to `okr`**, which is the only writer of `phase/` (`goals/reference/linkage.md`):

- resolved → `/perry goals link <TASK-ID> <KR-ID>` (appends the edge to that KR's `tasks[]`), and pass the same id to `perry-task add --actor <actor> --kr <KR-ID>` below
- a name confirmed as an existing Project → `/perry goals link --alias <PROJECT-ID> "<name>"`
- unresolved, or the user is unavailable → pass **`--unlinked` on the `perry-task add` below**, which declares in the row's own creating action that it serves no key result. **Do not omit both flags: `add` refuses a row that answers neither** (TASK-439), and omitting `--kr` was what this bullet used to say — it filed the row behind a warning and left it in `never_answered` permanently, because a later `perry-goals link` writes `via: "link"`, which `P003-O3-KR2` excludes by design. Declaring at `add` is the only form the KR counts. `/perry goals link --unlinked <TASK-ID>` remains the path for a row that is *already* filed. The tool records `KR linkage: unlinked` in the definition block itself, which is what keeps the row out of every KR roll-up until the standup surfaces it. **`--unlinked` is a declaration to mean, not a way past the refusal** — if the KR simply has not been looked up yet, look it up and pass `--kr`; `reference/okr-linkage.md` forbids guessing one, and the record `--unlinked` writes cannot be withdrawn by any `perry-task` command. (This sentence also claimed the declaration stays VISIBLE — naming `perry-lint`, then `perry-state § attribution`. Both were measured false and the claim was deleted under `USER-928` answer C: `linkage-unlinked-exists` warns only on an id that is **not** a row in `tasks.jsonl`, and `attribution.declared_unlinked` is scoped to `phase/CURRENT` — 143 standing declarations on Perry's own board, 116 reported. No reader reports a healthy standing declaration from a past phase.) This bullet used to say "write the BOARD row with `attribution: unlinked`" — there is no such column in `schema/state-schema.json` and there never was, so the instruction produced either a cell nothing reads or a widened board nobody asked for.

Print the exact command — **in its `/perry <lane> …` form**, since this string is quoted to the user and `/okr` is a withdrawn host command that `setup` deletes and that collides with `lark-okr`. Don't edit `phase/` yourself.

**Mode columns — the write path, not just the column.** A column nobody writes is not a control. For a row on a track whose mode is not `project`, `add-task` sets these in the same edit that creates the row:

| Track mode | Set at creation |
|---|---|
| `pipeline` | `Track`, `Stage` = the first stage of the track's `Stages`, `Stage since` = today, `Commitment` if the row discharges one |
| `queue` | `Track`, `Stage` = first post-intake stage, `Arrived` = the date it arrived (carried from `## Intake`, or today for a row raised directly), `Commitment` if applicable |
| `inquiry` | `Track`, `Stage` = `open`, `Stage since` = today, `Parent` = the question this was split from, or blank for a root |
| `project` | nothing extra — this is today's behavior, unchanged |

**Add the column if the board has none.** You cannot set a cell in a column with no header, and `BOARD_TEMPLATE.md` ships six columns — so the first non-`project` row on a board also adds the headers it needs, in the same edit. `perry-task add` and `route` do this via `ensure_columns`; nothing is expected of you.

(An earlier draft justified this as "the same clause `close-task` already has for `Verification`." There is no such clause. `Verification` is a declared *optional* column in `schema/state-schema.json`, but `close-task` removes the row rather than stamping it — the rung is written to the journal line and the event, which is where `perry-task list` reads it from. The back-reference pointed at a precedent that never existed; the rule stands on its own.)

A pipeline- or inquiry-mode board must carry `Stage` and `Stage since`; a queue-mode board must carry `Stage` and `Arrived`. They are optional in the schema so that no pre-DESIGN-003 board is invalidated, **not** so a mode track can skip them — a track that does is missing the clock its own triage reads.

**An existing row changes track with `perry-task track <ID> --actor <actor> --track <track>`, never by hand.** The table above is about creation, and for a long time creation and `route` were the only two entrances a track had — so a project that declared a second track started it empty and had no tool path for the work already on the board. Moving a row is one command and it re-stamps the destination's clock in the same write: onto a `queue` track it sets `Stage` to the first post-intake stage and `Arrived` (carrying an existing one rather than restamping it, so a move cannot erase an in-flight breach); onto a staged non-queue track it sets `Stage` and `Stage since`; onto a track that reads neither it **clears** `Stage` / `Stage since` / `Arrived` and writes what they held into the journal line and the event. A track with no record in `.perry/config.jsonl` (`perry-config show`) is refused by name, with the declared ones listed — the tool does not create a track, because a typo that invented one would be counted as real by every reader afterwards. Editing the `Track` cell by hand instead drops the clock, which is the same defect this section records for `Arrived` one paragraph up.

**Creating a queue-mode row also creates the intake register, `intake.jsonl`, if it is absent** — printed by `perry-tasks board` as `## Intake`, with its three columns (`Arrived`, `Request`, `Outcome`). Intake is the organ queue mode is built on and the first thing `triage` walks; a register nothing creates means step 0 no-ops forever, and `modes/queue.md`'s warning about a track "whose intake is always empty while work is clearly happening" would describe the guaranteed default rather than a risk.

1. **Create the row with the tool, not by hand.**

   ```
   "$PERRY_HOME/bin/perry-task" add --actor <actor> --title "<title>" --owner "<owner>" \
       --summary "<why this row exists, for a reader who was not here>" \
       --deliverable "<the artifact>" --verification "<the falsifiable check>" \
       --priority <P0|P1|P2> [--track <track>] [--next "<next action>"] \
       [--parent <ID>] [--commitment <Id>]
   ```

   **`--summary`, `--deliverable` and `--verification` are all required and
   all three are refused if absent.** They used to be shown as optional here
   while two of them were already hard refusals in the tool, so the block a
   reader copied did not run — which is the shape TASK-325 exists to stop one
   field further along.

   It mints the ID from board ∪ journal ∪ events (never reused, never
   accidentally gapped), stamps the timestamp at call time, sets `Stage` /
   `Stage since` / `Arrived` for the track's mode, **creates any column or
   section the mode needs and the board lacks**, and writes the task store and
   journal through a durable recovery marker. A normal failure rolls both back;
   a crash between replacements is completed on the next locked Perry run.
   The event is appended afterwards, and a board file a project still holds
   is re-rendered from the store; either derived-surface write is reported if
   it fails.

   **Which id family it mints into.** `TASK-NNN` unless the board says
   otherwise, and the board says otherwise in exactly one way: if every
   numbered id in its task tables shares one prefix, a new id joins it. A board
   of `AIM-001`…`AIM-017` gets `AIM-018`, where it used to get `TASK-001` — a
   second id family appearing on a board that had one, with no way to ask for
   the first (TASK-060, reported by aiMark).

   Perry stops at *exactly one* and does not take the most common. A real board
   here carries 36 families in its task tables, declared in its own
   `## ID prefixes` section, and they are not stylistic — `IPS-*` / `ALLOC-*` /
   `DUE-*` mean one workstream and `TECH-*` / `DATA-*` another, filed in
   separate sections. Picking the plurality winner would mint an id that
   asserts a workstream nobody chose, and an id is permanent. A `TASK-001` on
   such a board is visibly Perry's and claims nothing.

   ```
   "$PERRY_HOME/bin/perry-task" add --actor <actor> --title "…" --deliverable "…" \
       --verification "…" --prefix AIM
   ```

   `--prefix` names the family outright and wins over adoption. It is how a
   front-end that cannot supply an id asks for one in the right family, and it
   is the only answer on a board carrying several. Pass the prefix, not an id
   (`AIM`, not `AIM-018`); segments join with `-` and each starts with a letter,
   so `ARCH-V2` is a prefix and `AIM-018` is refused. `USER`, `RX`, `CAD` and
   `CADENCE` are refused too — `perry-task` mints those for the queue, risk and
   cadence registers on the same board, and a task numbered in one of them
   would collide with rows the tool writes itself. `route` takes `--prefix` and
   adopts by the same rule; both verbs mint, so both had to.

   Do not hand-write the row. Every field above was one an agent supplied and
   got wrong at least once: malformed pipes, a reused ID, a timestamp that was
   an assertion, a clock nobody wound. `perry-state` reports a hand-written row
   as `unrecorded` at the next standup — reported, not refused, because editing
   your own markdown is legitimate; but it is visible, and that visibility is
   the point.

   **On a board that does not use `P0`/`P1`/`P2`**, name the project's own
   heading instead:

   ```
   "$PERRY_HOME/bin/perry-task" add --actor <actor> --title "…" --deliverable "…" \
       --verification "…" --group "Open — 工程线"
   ```

   A real year-old project files work under headings like that, and `add`
   refused it outright until TASK-019/020's review found it. Perry will **not**
   create a priority section on such a board — rewriting a project's structure
   is an Anti-Goal — but it will add the columns it needs to write a row,
   widening existing rows with empty cells rather than dropping the data that
   does not fit. Run `add` without `--group` to see the sections a board
   actually offers; the refusal lists them.

   **`route` takes `--group` too, and means the same thing by it.** It did not
   until TASK-053: the flag parsed and `route` never read it, so the intake
   drain could not run at all on a board with no `## P0`/`## P1`/`## P2` — and
   the refusal that told the user to pass the heading to `--group` was telling
   them to pass it to a flag that verb threw away. Both verbs resolve the
   landing section through one function now, so a board Perry can `add` into
   is a board Perry can `route` into.

   **Refusals are outcomes, not errors.** The tool exits 1 and writes nothing on
   a missing title, an undeclared track, a priority outside `P0`/`P1`/`P2`, a
   stage outside a track's vocabulary, or a `--stage` on a `project`-mode track
   (which has none). Read the message and fix the call; do not fall back to
   editing the file.

2. **The full definition comes from the same call — pass the fields, don't retype the block.**

   ```
   "$PERRY_HOME/bin/perry-task" add --actor <actor> --title "…" --owner "…" --priority <P> \
       --deliverable "…" --verification "…" \
       [--depends "TASK-050, TASK-051"] [--out-of-scope "…"] [--kr <KR-ID>]
   ```

   `perry-task add` renders `### <ID> — <title>` under `## New tasks added` in
   `journal/<YYYY-MM>/<today>.md` with Owner, Priority, Track / mode,
   Deliverable, Verification, Dependencies, Out of scope and KR linkage — the
   whole schema, in the same atomic write as the row and the one-line status
   change. Absent `--kr`, the KR linkage line reads `unlinked`, which is the
   gate above landing in the record instead of in an agent's memory.

   **This step used to hand the block to the agent, and the agent did not
   produce it.** Measured the day the tool learned to: `## New tasks
   added` appeared three times in the journal of the day *before* and zero
   times after, so every tool-created task was one title and nothing else.
   That is ADR-007 rule 3 stated as a defect — the fields were supplied to the
   tool and the document was then expected to appear from somewhere.
3. **For P0 and P1 tasks**, ALSO write `evidence/<YYYY-MM>/<TASK-ID>-spec.md` carrying the same *fields* as the journal block PLUS the dispatch-routing fields below — **in `## ` sections, not in the journal block's bullets.** BOARD's Evidence column points at this spec file. P2 / backlog / watch may rely on the journal entry alone — promote a P2 to P1 → write the spec at promotion time.

   **`Files in scope`, `Deliverable` and `Out of scope` are `## ` headings, with the text underneath them.** Not `### `, not `- **Deliverable**: …`. The spec body is `## ` sections throughout; these three are the ones a machine reads:

   ```
   ## Files in scope
   - `path/one.py` — what changes there.

   ## Deliverable
   What exists when this is done.

   ## Out of scope
   What this deliberately does not touch.
   ```

   **Why the shape is load-bearing, and not a style rule.** `dispatch` pre-flight step 4 re-validates the spec against `.perry/hook.md § High-stakes operations` by reading exactly those three sections (`work/reference/dispatch-preflight.md` step 4), and its reader — `viewer/parsers.py § _section` — matches `^## <heading>` and nothing else. A scope written as an `h3` or as a bullet is invisible to it. **The spec does not then fail the gate; it disarms it.** Every high-stakes fragment is matched against the empty string, and the scan returns `touches: {}`, `verdict: pass`, **exit 0 — byte-identical to a spec that was read in full and found genuinely clean.** Measured 2026-09-02: a spec whose `Deliverable` named `git push origin main`, `rm -rf` and `gh release` scanned `pass`/exit 0 in the bullet shape and `refuse`/exit 3 on five fragments with the identical words under `## Deliverable`; 45 of this project's own 135 specs are in the first state. `perry-lint --specs` — and the default `perry-lint --root .` — now reports a spec that presents the gate no scope, so the empty scan is visible; but the check reports it, it does not undo it, and the spec is only safe if it is written in the shape above.

   **This step used to say the spec "contains the same schema" as the journal block, and that sentence is what produced the 45.** `bin/perry-task § cmd_add` renders the journal definition block as bullets, and that is correct *there*: the block sits under `### <ID> — <title>` inside `## New tasks added`, so a `## Deliverable` in it would close the section it lives in and cut one day's journal in half. The journal keeps its bullets; the spec takes `## ` headings. Same fields, two shapes, because the two files have two readers — a person scrolling a day, and a safety gate matching sections. "The same schema" was read as "the same shape", which is the only reading the rendered block supports, and following it disarmed the gate. Do not copy the journal block into a spec; write the sections.

   **Required header fields in every spec file** (used by `dispatch` and `close-task`):
   The software-ops `Touches architecture`, `Deployed`, `Runbook` and
   Observability requirements below follow the pack eligibility rule in
   `$PERRY_HOME/reference/config.md § Pack capabilities and controls`. With
   inactive software-ops, impose them only where the project independently
   requires them; do not delete existing task commitments or relax high-stakes
   verification. Other dispatch fields remain required.
   ```
   > Dispatch mode: auto | manual               # default 'manual'; 'auto' is explicit opt-in
   > Executor: claude-subagent | opencode-subagent | codex | manual # only consulted when Dispatch mode = auto
   > Estimated cycle: small | medium | large    # informs sync vs async + cycle-time tracking
   > Subjective verification: <list, or '(none)'>
   > Touches architecture: <comma-separated §-section refs (§2, §3, §6.NN-3), or '(none)'>   # used by dispatch pre-flight + review agent; see $PERRY_HOME/packs/software-ops/architecture.md
   > Deployed: yes | no                          # default 'no'; 'yes' triggers runbook + observability gate at close
   > Runbook: runbook/<slug>.md                  # required ONLY when Deployed: yes; path must exist before close-task
   ```

   **When `Deployed: yes`, the spec ALSO requires an `## Observability` section** with three sub-fields (see `$PERRY_HOME/packs/software-ops/runbooks.md § Spec contract`):
   ```
   ## Observability
   - Success signal:   <log line / metric / endpoint / `command` output that proves it's working>
   - Failure diagnosis: `<single command>` — one line that answers "what's broken right now"
   - Runbook path:     runbook/<slug>.md
   ```

   **Choosing executor (spec writer responsibility)**:
   - `claude-subagent`: small task, needs MCP tools the parent session has, needs codebase familiarity.
   - `opencode-subagent`: OpenCode-native codebase work through synchronous `Task(subagent_type: general)`.
   - `codex`: medium/large self-contained, no MCP dependency, save Claude Code quota.
   - `manual`: high-stakes per project hook (production deploys, prod credentials, .env, paid APIs, cost ceiling raise) OR subjective decision-making (research candidate selection, design choices).

   Commit to the choice with one inline reason: `> Executor: codex (high confidence — pure analytics task, no MCP needed)`.

The spec carries the same *fields* as the journal `## New tasks added` block — in the `## `-section shape of step 3, not the block's bullets; not duplication, two surfaces with different access patterns and different readers:

| File | Purpose | Lifetime |
|---|---|---|
| `journal/<YYYY-MM>/<creation-day>.md` | Historical "this was created here" record | Frozen after the day ends |
| `evidence/<YYYY-MM>/<TASK-ID>-spec.md` | Live schema for dispatch / re-dispatch / audit | Mutable as scope refines (subsequent edits must add `## Changes` log inside the file) |
| `evidence/<YYYY-MM>/<TASK-ID>-*.md` (other names) | Deliverable artifacts: reports, drill records, checklists | Per-deliverable |

When the task closes, leave the spec file in place — it's the canonical scope record.

Slug IDs are never reused or recycled across months.

If the task needs a working artifact from day one (checklist, design ladder, subtasks), the working artifact lives at `evidence/<YYYY-MM>/<TASK-ID>-<slug>.md` (separate file from the spec).

After completed writes, follow `subcommands.md § Completion routing`.
