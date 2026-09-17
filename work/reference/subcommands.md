# PMO subcommands — full reference

The standup ritual + dispatch + delegate live in SKILL.md / `dispatch.md` / `delegate.md`. Everything else is here.

## Planning

See `planning.md § Planning`.

### `plan-week`

See `planning.md § plan-week`.

### `triage`

See `planning.md § triage`.

## Cadence (recurring; never consume P0 slots)

### `status` (a.k.a. `friday-review`)
This week's PMO status report using the format in `reporting-format.md`. Reads `perry-task list --json` + this week's journal entries. Save to `weekly/<YYYY-WW>.md`.

### `monday-plan`
Run at start of week. Reads `perry-task list --json` + last week's `weekly/<YYYY-WW>.md` if any. Output: priorities, P0 set, blockers needing user input, scope cuts. Append to current week's `weekly/` file AND write a `## Notes` entry in today's journal.

### `midweek-check`
Mid-week pulse. Reads `perry-task list --json` + journal entries since Monday. Output: P0 movement check, blocker escalations, cost-ceiling progress, tests/verification reminders. Write to today's journal.

### `mid-phase-review`
Triggered manually (or surfaced by the standup when ≥40–60% of phase day budget elapsed). Reads `perry-task list --json` + journal entries since the current phase started (resolve start date from the phase file header). Mark each Objective `on_track | at_risk | off_track` based on KR progress. Apply any **Phase Scope Reduction Rule** declared in `phase/<NNN>-<slug>.md`. Recommend scope cuts. Save to `evidence/<YYYY-MM>/midphase-review-<NNN>-<slug>.md`.

**Inline health-check** (added to mid-phase-review): run `/pmo health-check` (see `reference/health-check.md`) and fold its findings — audit violations, runbook gaps, incident patterns — into the mid-phase-review report. The detailed report lives at `evidence/<YYYY-MM>/health-check-<YYYY-MM-DD>.md`; the mid-phase-review summarises the top decision items inline.

**Digest archive review** (added to mid-phase-review): if `knowledge/` exists, scan for active digests with no reference in the task store / `journal/` / `evidence/` / `decisions/` / `phase/` for ≥ `archive_inactive_days` days (default 90; override per-project hook). For each candidate, use `AskUserQuestion` (header = digest basename, options): `Archive (Recommended) | Keep active — still relevant | Mark eternal — never propose archive | Delete entirely`. On Archive: flip `Status: archived` in the digest header + record `Archived: <date> (reason: <user input>)`. On Eternal: flip `Status: eternal`. On Delete: `git rm` source + digest. Update `knowledge/INDEX.md`. See `work/reference/digests.md § Archive lifecycle` for full detail. (Note: `health-check` already includes the digest stale scan; running it here is the same scan, surfaced for the user to act on.)

### `end-phase-retro`
Triggered when OKR `score-phase` is about to run (or explicitly by the user). Reads `perry-task list --all --json` + all journal entries since the current phase started + `evidence/<YYYY-MM>/` for the calendar months the phase spanned. For each KR: mark `achieved | partial | missed | dropped`, link evidence file. Capture lessons. Identify carry-over candidates. Save to `evidence/<YYYY-MM>/retro.md` (using the calendar month at scoring time). This is OKR's input for `plan-phase` of the next phase.

**Inline health-check** (added to end-phase-retro): run `/pmo health-check` (see `reference/health-check.md`). The retro additionally folds in:
- **Incident feedback-loop ratio**: of all incidents resolved during this phase, how many produced derived changes (architecture / runbook / digest)? A low ratio + recurring components = a structural problem worth a KR in next phase's OKR.
- **Audit drift trend**: how many `ARCHITECTURE.md`-vs-code drift items from the last audit are still open at phase-end? Carry them into next phase's OKR as either resolution KRs, deferral ADRs, doc edits, or `Not Doing` lines (see `goals/reference/phases.md § plan-phase <slug>`).
- **Runbook coverage**: count of deployed components without runbook, vs same count at phase start. Drift in this number is a red flag.

These three numbers go into `evidence/<YYYY-MM>/retro.md` § "Health metrics" section so OKR's `plan-phase` for next phase can read them directly.

**Knowledge promotion** (DESIGN-006 § 5.4; procedure in `reference/promotion.md`): **at most one question for the whole retro**, and only for a lesson the retro itself already identified as recurring across two or more tasks. Run `"$PERRY_HOME/bin/perry-knowledge" propose --source "evidence/<YYYY-MM>/retro.md" --root . --json` first — `fires: false` means ask nothing — and write it with `perry-knowledge promote`, never by hand. Batching is the named risk (DESIGN-006 § 7): a retro that offers six cards produces six rubber stamps. If the phase produced several durable claims, promote one and note the rest as candidates in the retro; the next `close-task` will offer them where they belong.

**Digest archive review** (same procedure as `mid-phase-review`; second pass per phase): re-scan archive candidates and process via `AskUserQuestion`. Phase-end is the safer gate — anything still un-referenced after a full phase is more likely truly inactive. Also at phase-end, **rebuild `knowledge/INDEX.md` fully** (not just incrementally): re-grep all references for `Last referenced` dates, recompute counts, alphabetize within topics. Cheap operation (~2-3 sec for 30 digests).

## Decisions & risk

See `decisions-risk.md § Decisions & risk`.

### ~~`decide <topic>`~~ — moved to the `decide` lane

See `decisions-risk.md § ~~decide <topic>~~ — moved to the decide lane`.

### `risk`

See `decisions-risk.md § risk`.

### `nudge`

See `decisions-risk.md § nudge`.

## Task lifecycle

### `add-task` (interactive)

See `add-task.md § add-task (interactive)`.

### `close-task <id>`

Read `planning.md § triage` for the stage-change invariant before moving a stage.

Apply `$PERRY_HOME/reference/config.md § Pack capabilities and controls` before
gates 1 and 2: software-ops must be selected and present, unless an independent
project requirement mandates the specific check. Preserve and name that source
when the pack is disabled. All other acceptance/verification/safety gates remain.

If an approved project release policy applies, read `$PERRY_HOME/packs/software-ops/releases.md` for delivery/publication receipts. Closing is not a version bump; partial delivery does not complete a task. Existing acceptance and close gates still decide. With no policy, continue without version intervention or an enablement question.
Reject if no evidence path provided.

**Pre-close gate 1 — `Touches architecture:` requires review agent PASS** (see `$PERRY_HOME/packs/software-ops/architecture.md § close-task gate`):
1. Open `evidence/<YYYY-MM>/<TASK-ID>-spec.md`. If header has `Touches architecture:` non-empty:
   - Find the latest dispatch evidence file for this task (`evidence/<YYYY-MM>/<TASK-ID>-dispatch-*.md`, latest mtime).
   - Verify it contains an `## Architecture review` section ending with `PASS`. `FAIL` or missing → refuse close.
2. **If review missing or FAIL**, use `AskUserQuestion` (header = TASK-ID, options): `Re-dispatch to fix (Recommended) | Override — close without arch review (NOT recommended) | Keep as review`. "Override" requires written reason; logged as `architecture-override: <reason>` in journal.
3. `Touches architecture: (none)` or field absent → skip this gate.

**Pre-close gate 2 — `Deployed: yes` requires a runbook** (see `$PERRY_HOME/packs/software-ops/runbooks.md § close-task gate`):
1. Open the spec. If header has `Deployed: yes`:
   - `Runbook:` field must be present AND point at an existing file.
   - The referenced runbook file must have all four mandatory sections (What / Healthy / Failures / Escalation), non-empty.
   - The spec must contain an `## Observability` section with non-empty Success signal / Failure diagnosis / Runbook path.
2. **If any check fails**, refuse close. Use `AskUserQuestion` (header = TASK-ID, options): `Add runbook now (Recommended) | Keep as review until runbook exists | Override — close without runbook (NOT recommended)`. "Override" requires a written reason; the override is logged under `## Status changes` as `runbook-override: <reason>`.
3. `Deployed: no` or field absent → skip this gate.

**Pre-close gate 3 — record the verification rung** (DESIGN-003 § 5.3; `schema/state-schema.json § verification`):

Before flipping status, capture **how** this was verified, not just that evidence exists. Pre-select the track's `Default rung` from its record in `.perry/config.jsonl` (V3 for `project`, V5 for `pipeline`, V2 for `queue`, V4 for `inquiry`), so the ordinary case costs the user no decision at all — they confirm rather than choose.

Two rules override the default, and neither is optional:

- **Consequence beats mode.** If the task matches `.perry/hook.md § High-stakes operations` — outward-facing, irreversible, or carrying money, legal or safety exposure — the rung is **V5 minimum** whatever the mode default says. `perry-lint --verification` reports the mismatch as `consequence-needs-signoff`, so a close below V5 on a high-stakes row will surface at the next standup regardless.
- **V4 needs a rubric, V5 needs a signature.** A `V4` close must cite the acceptance-criteria file the reviewer scored against, and that reviewer must not have seen the reasoning that produced the artifact. A `V5` close must record **name, date, and what was checked** — "reviewed" is not what was checked. At V5 the signature is *selected* rather than composed; the procedure is the next block.

**Choose** the rung here and hand it to `perry-task done`'s `--rung`. Do not write it into the row or the journal yourself — the tool writes both, and doing it here as well produces a duplicate journal line and an edit to a row the next command removes. **Advisory this release** by DESIGN-003 § 4 decision 4: a missing or unsatisfiable rung is reported, never refused, because a hard gate on day one would retroactively invalidate every `done` row written before rungs existed. The number to watch is `unrated` in `perry-state`'s `board.verification` — it is what should shrink before the gate hardens.

**Pre-close gate 3, second half — at V5 the signature is SELECTED from what Perry measured, never composed from memory** (TASK-109). Rungs V1–V4 stop at the paragraph above; only a V5 close continues here.

The first half of a V5 close is a read-only offer. It writes nothing:

```bash
"$PERRY_HOME/bin/perry-task" signoff-offer <TASK-ID> --json \
    --measured "<a fact Perry measured during this task>" \
    --restated "<a claim Perry is only passing along>"
```

Both flags repeat. `signoff-offer` numbers the items, labels each with its provenance, and the numbering it prints is the numbering `done --checked` reads back — one function mints both, so a prompt whose option 3 is the tool's option 4 cannot happen.

**`--measured` is what Perry ran**: the objective-verification commands and their output, the scope cross-check, the diffs it took. **`--restated` is what Perry is only repeating** — a dispatch RESULT line, a claim from the spec, a subjective-verification item the spec declared. That distinction is the product. Selecting a `--measured` item means *I checked this too*; selecting a `--restated` one means *I checked a claim Perry only passed along*. Flatten them and the rung records acceptance where it promised verification.

**Perry may draft only facts it measured. It may never draft a claim about what the user did.** `claims[] carries zero changed lines in the diff` is yours to draft — you ran the diff. `the user reviewed the diff` is not, and the tool refuses it by pattern rather than by review note: drafting the signature and collecting a keystroke is Perry certifying its own work, which is the failure V5 exists to prevent.

Render the payload's `options` with **`AskUserQuestion`** (`multiSelect: true`, header = TASK-ID). On a host with no selection UI, print the payload's `prompt` — the numbered free-text fallback of `reference/host-capabilities.md § Prompt rendering`. Then ask the free-text half once: *anything you checked that Perry did not offer?* Rendering differs per host; the record does not.

Hand the answer to the same call that closes the row — this is one tool call, not a close plus a write:

```bash
"$PERRY_HOME/bin/perry-task" done <TASK-ID> --actor <actor> --evidence "<path>" --rung V5 \
    --measured "…" --restated "…" \
    --checked "1,3" \
    [--not-looked-at "4"] \
    [--also "<what they checked that was not offered>"]
```

Pass the same `--measured` / `--restated` items back unchanged: the record holds every offered item, not only the selected ones. `--checked` also accepts `all`, `none`, or one flag per number, because that is what the free-text host hands back.

- **Name and date are filled in** from `git config user.name` and today. They are the two fields a human should never be retyping, and `--signer` exists only for the case where git has no name.
- **Unselected items are recorded, not dropped**, as `accepted on report` — strictly more than the free-text paragraph could say, which could not distinguish the two at all.
- **`not looked at` is never a default.** It is reached only by the user naming the item, which is what keeps it the user's statement rather than Perry's.
- **A V5 close with nothing checked and no free text is refused, not written blank.** An empty signature is the failure the rung exists to prevent, and it must not be reachable by pressing return.

The tool writes the signature block into today's journal under `## V5 sign-off` and the structured record into the close event, in the same transaction as the row. **Do not also write the signature into the evidence file by hand** — a second copy is a second answer to the question the rung asks, and the two rot apart. The signatures already recorded in `evidence/2026-08/` keep their own shape; this adds a path, it does not rewrite them.

**Pre-close gate 4 — inquiry mode** (`modes/inquiry.md`). On an inquiry-mode track:
1. `evidence/<YYYY-MM>/<ID>-answer.md` must exist — the question restated, the answer, the claims with their `[SRC-n]` citations, and what would change the answer. The mode's signature failure is re-deriving the same synthesis every session, and its one cause is the answer living in chat.
2. `perry-lint --provenance --root .` must report no `citation-dangling` for that file. This is the half of the bar `modes/inquiry.md` calls the mode's test suite; the rung is the other half, and shipping only the rung leaves the script unrun.
3. **A parent may not close before its children.** Any row whose `Parent` is this ID must be `done` or `dropped` first. An answered parent over an open child means either the child was not load-bearing — drop it and say why — or the answer is premature.

If the task spec lists `Subjective verification` items, **use `AskUserQuestion`** (header = TASK-ID, options = `Verified — close (Recommended) | Partial — keep as review | Reject — needs rework`) before flipping status. On `Verified — close`:
1. **Close it with the tool, not by hand.**

   ```
   "$PERRY_HOME/bin/perry-task" done <TASK-ID> --actor <actor> --evidence "<path or citation>" --rung <V1..V6>
   ```

   It removes the board row, writes the journal status-change line with the rung
   in it, and records the close event — atomically. `--rung` defaults to the
   track's `Default rung`, then the mode default, so the ordinary case needs no
   flag. **`--evidence` is required and the tool refuses without it**: Perry's
   oldest rule, enforced at write time rather than reported afterwards.

   `V0` is refused by name — it is what is being rejected, never a rung a row
   may carry.

   On a pipeline track, check the row reached the terminal stage of its `Stages`
   first: `approved` is not `published`, and closing short of the last stage is
   that mode's signature failure wearing a green checkmark.

2. The tool wrote the status-change line. Anything more the close deserves — a
   paragraph of what was learned, a correction, a finding — goes in today's
   `## Notes` by hand.
3. If the task was a Must-Have item in `phase/<NNN>-<slug>.md`, **do not tick it there** — `phase/` is the `goals` lane's file and this lane is not its writer (`SKILL.md § The hand-off contract`). Print the hand-off instead: "`<ID>` closed; it is a Must-Have in `phase/<NNN>-<slug>.md` → run `/perry goals link` to tick it." Asking and stopping is the contract; writing and apologising is the thing it forbids.
4. The original task definition (creation-day journal entry) stays untouched — that's the historical record.
5. **If `Deployed: yes`**: bump the runbook's `Last verified: <today>` field (the close is evidence the user reviewed the runbook against reality at this moment).

**Post-close capture point — knowledge promotion** (DESIGN-006 § 5.4; full procedure in `reference/promotion.md`):

After the close is written, ask whether the run produced a **reusable claim about how to do something correctly** — the one kind of memory Perry has no other home for. Run `"$PERRY_HOME/bin/perry-knowledge" propose --source "<the citation you passed to --evidence>" --rung <the rung> --root . --json` first: it is read-only and it says whether the capture point fires at all. `fires: false` → ask nothing and say nothing (`no-source`, `source-unresolvable`, a `V0`/`V1` rung, or a card already citing this source).

`fires: true` is permission to consider asking, not an instruction to ask. **You must have a draft** — an actual one-line claim and an actual tripwire — and the claim must be true of the next task too, not a fact about this one. Most closes produce neither, and the question does not fire on them; that is what keeps it from becoming the prompt people dismiss by reflex. Then **one** `AskUserQuestion` showing the drafted claim and tripwire, with `Skip — nothing durable` as a one-keystroke option that writes nothing anywhere. On confirm, `"$PERRY_HOME/bin/perry-knowledge" promote …` writes `knowledge/<topic>/<slug>.md` and re-renders `## Cards by topic` in `knowledge/INDEX.md`. **A sourceless card is refused, not written blank** — the tool enforces it; do not hand-write a card to get around a refusal.

Does not fire on `drop-task`: a dropped row produced no verified finding.

To find a closed task later: `grep "TASK-007" journal/` returns its creation entry, all status changes, and its close entry.

### `drop-task <id> <reason>`
Symmetric to `close-task`, and like it, tool-written:

```
"$PERRY_HOME/bin/perry-task" drop <ID> --actor <actor> --reason "<reason>"
```

`--reason` is required and the tool refuses without it — a dropped row that
does not say why is indistinguishable from one that was lost.

The tool removes the board row, writes the journal status-change line and
appends the closing event, atomically. **Do not remove the row by hand.** A
hand-deleted row leaves its `add` event with no row and no close, which is
exactly the `orphaned` condition `perry-state` reports — so hand-dropping
manufactures, on every drop, the false drift the detector exists to catch.

The original task definition in its creation-day journal entry stays untouched
— that is the historical record.

## Cross-session

### `coordinate`
Pull a snapshot of work from other Claude sessions/terminals tagged for this project (use a session-listing MCP tool if the project hook declares one; otherwise ask the user to paste summaries). Append a consolidated update to `PROJECT_STATE.md` under `## Recent cross-session work`. Distribute follow-ups by appending new tasks.

When an incoming update references a Project by **name** (progress reports usually do, and the name may have drifted), resolve it to a KR **by ID through `linkage.jsonl`** before rolling any progress up — explicit `kr:` → Project ID → registered alias (`$PERRY_HOME/reference/okr-linkage.md`). Ambiguous or unmatched → ask the user which Project/KR it is; never attribute by fuzzy name. Hand the answer to `okr` (`/perry goals link …`) rather than editing `phase/`. Unresolvable while the user is away → `/perry goals link --unlinked <id>` rather than pinning it to a guessed KR.

### `handoff`
Generate the **Day-N Status doc** — a single self-contained document a future PMO session can read instead of re-walking the conversation. Save to `handoff/<YYYY-MM-DD>.md` from `state/handoff_TEMPLATE.md`. Always include:
1. Must-Have progress count (e.g., "4/5 done")
2. Today's deliverables (code/decisions/finance)
3. User Input Queue with recommendations
4. Next ISO week's day-by-day milestones
5. Open risks with mitigations
6. BOARD snapshot — paste what `perry-tasks board` prints (or summarize if too long)
7. "Read these N files first when you resume" pointer (typically: `handoff/<this-doc>.md`, `perry-tasks board`, last 1–2 journal entries, `PROJECT_STATE.md`)

The first line of every PMO session after a handoff exists is: "Read `handoff/<latest>.md` and tell me your status." The handoff doc is the bridge.

## Phase transition

### `rollover`
Runs when a phase has been scored via `okr score-phase` and the user is ready to start the next phase. With the BOARD/journal split, rollover is mostly informational — the task store is already current; previous phase's journal entries are intact. Steps:

1. Confirm `evidence/<YYYY-MM>/retro.md` exists — **this lane's own file, written by `end-phase-retro`**, not by `okr score-phase`, which hands over a summary and does not write `evidence/` (`goals/reference/phases.md` step 5). If it is absent, prompt to run `end-phase-retro`; prompting for `score-phase` cannot produce it.
2. **Calendar-month directories** — `journal/<YYYY-MM>/` and `evidence/<YYYY-MM>/` are calendar-bound; create new month dirs only if the calendar month rolled (most rollovers do NOT need this — phases can span multiple calendar months OR fit inside one).
3. **The task store is left alone.** Open carry-forward tasks already live there; no "carry forward" step is needed because the board never had a phase boundary in the first place. If a row's task ID encodes a date or phase prefix, leave it untouched — it's the canonical handle.
4. For each unresolved task on BOARD: **use `AskUserQuestion`** (header = TASK-ID, options = `Carry forward (Recommended) | Drop with reason`). Batch up to 4 per call. For "Drop with reason", follow up with a free-text prompt for the reason, then run `perry-task drop <ID> --actor <actor> --reason "<reason>"` — the reason the user just gave, verbatim, not a paraphrase.
5. Hand off to OKR: print "OKR `plan-phase <new-slug>` is needed — pick the next phase's slug." Do **not** create the new phase file yourself — that's OKR's lane.
6. Append a `## Notes` entry to today's journal: "rollover from phase #<old-NNN>-<old-slug>; <n> rows carried; see evidence/<YYYY-MM>/retro.md".

`git log -- journal/` shows the full history per day; `git log -- tasks.jsonl` shows the task store's evolution; `git log -- phase/` shows phase progression.

## Completion routing

After completed writes from `plan-week`, `triage`, `status`, `friday-review`, `monday-plan`, `midweek-check`, `mid-phase-review`, `end-phase-retro`, `risk`, `add-task`, `close-task`, `drop-task`, `coordinate`, `handoff`, `rollover`, follow [the shared closing step](../../reference/next.md#closing-step); its skip rules apply.
<!-- next-close: work plan-week --> <!-- next-close: work triage --> <!-- next-close: work status --> <!-- next-close: work friday-review --> <!-- next-close: work monday-plan --> <!-- next-close: work midweek-check --> <!-- next-close: work mid-phase-review --> <!-- next-close: work end-phase-retro --> <!-- next-close: work risk --> <!-- next-close: work add-task --> <!-- next-close: work close-task --> <!-- next-close: work drop-task --> <!-- next-close: work coordinate --> <!-- next-close: work handoff --> <!-- next-close: work rollover -->
