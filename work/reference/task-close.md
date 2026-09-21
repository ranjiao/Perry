# `/pmo close-task <id>` and `drop-task` — the task lifecycle's end

Split out of `subcommands.md § Task lifecycle` on 2026-09-21 (TASK-470), unchanged. `add-task` is `add-task.md`.

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

**Then the after-task checkpoint**, once the close and any card are written: `budget-boundary.md § Budget boundary`.

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

## Completion routing

After a completed `close-task` or `drop-task` write, follow [the shared closing step](../../reference/next.md#closing-step); its skip rules apply.
<!-- next-close: work close-task --> <!-- next-close: work drop-task -->
