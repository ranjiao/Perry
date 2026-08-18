# Knowledge promotion — the one question at the three capture points

Loaded when `close-task`, `end-phase-retro` or `/pmo incident close` reaches its
capture point. DESIGN-006 § 5.4, phase B.

Domain knowledge — *how to do this correctly* — is the one kind of memory Perry
had no home for. It is captured **where it is produced**, at gates people
already run, and there is deliberately no `add-knowledge` ritual to tend. A
wiki nobody was asked to maintain is a wiki nobody maintains.

## The rule

> **Evidence proposes; the user declares.**

A card is never written because an agent found the finding interesting. The
capture point *offers* a draft, pre-filled from the evidence that was just
written; the user confirms; the `work` lane writes it. Same asymmetry as
`$PERRY_HOME/reference/adoption.md § The one rule`, and the same reason: a store
of plausible agent-authored claims is one nobody can ever again tell apart from
fact, and agents then execute against it.

The other half is phase A's, promoted from advisory to refusal here:

> **A sourceless card is refused, not written blank.**

`perry-lint --knowledge` reports a card missing provenance *afterwards*. The
write path refuses it *now*, because now is when the person who knows the answer
is still in the room. `bin/perry-knowledge promote` carries that refusal; you do
not need to pre-check it, and you must not work around it.

## When it fires

Run this first — it is read-only and it answers the question mechanically:

```
"$PERRY_HOME/bin/perry-knowledge" propose \
    --source "<the evidence citation the close just wrote>" \
    --rung "<the rung chosen at the close>" --root . --json
```

`fires: false` → **ask nothing.** Say nothing about it either; a capture point
that narrates its own silence is the same interruption it was avoiding. The
four mechanical reasons it returns:

| `reason` | Why nothing is asked |
|---|---|
| `no-source` | the close cited no evidence, so `Source:` would be something the agent chose rather than something the run produced |
| `source-unresolvable` | the citation names no file, task id or `SRC-n` in the project. A citation that looks checkable and is not is worse than none |
| `rung-unverified` | the close was `V0`/`V1` — the agent attesting its own artifact. A claim whose provenance bottoms out there is exactly the confident error the card schema exists to keep out |
| `already-promoted` | a card already cites this source. Asking twice is the nag that teaches people to dismiss the question |

`fires: true` is **permission to consider asking, not an instruction to ask.**
Three more conditions are judgement, and no tool can answer them:

- **You must have a draft.** Not a topic worth writing about — an actual claim
  in one line, and an actual tripwire naming the observable condition under
  which it stops being true. If you cannot write both from the evidence in
  front of you, there is nothing to propose and you ask nothing. This is the
  condition that keeps the capture point off most closes, and it is the point:
  a question that fires on every close is one people learn to dismiss, and then
  it fires on the one that mattered.
- **The claim must outlive its task.** "The export query needed an `is_test`
  filter" is a claim about the world and will be true of the next report too.
  "TASK-041 was harder than estimated" is a retro line. If the claim cannot be
  stated without naming the task, it belongs in the evidence file it came from.
- **A tripwire is not a date.** "upstream schema change on `<system>`" is a
  tripwire. "when it feels old" is not — `Last verified` already covers the
  passage of time, and a card whose only invalidation signal is age goes stale
  in silence.

It never fires on `drop-task`. A dropped row produced no verified finding, and
DESIGN-006 § 5.4 names three capture points, not four.

## The one question

**One `AskUserQuestion`, never a form.** A card has five fields; four are
derived or pre-filled and never asked:

| Field | Where it comes from |
|---|---|
| `Kind` | `knowledge`, unless the claim names an external system and how to read it authoritatively — then `source-of-truth` |
| `Owner role` | `—` before `.perry/roles/` exists; the single declared role when there is one; the task row's `Role:` otherwise |
| `Source` | the evidence citation the close just wrote — pre-filled, never typed |
| `Last verified` | today |

What is left is the claim and the tripwire, and those are shown **already
drafted** so the question is a confirmation rather than an interview:

```
AskUserQuestion — header: <TASK-ID>
  question: "Keep this as a knowledge card?
             Claim: <the one-line claim you drafted>
             Invalid when: <the tripwire you drafted>"
  options:
    - "Write it (Recommended)"    → the draft as shown
    - "Write it — my wording"     → the user corrects the claim or the tripwire
    - "Skip — nothing durable"    → nothing is written
```

`Write it` is the recommendation because you only reached this question by
having a draft you believe. `Skip` is one keystroke, and **a skip writes
nothing, anywhere** — no journal line, no note, no "promotion declined" record,
and it is not raised again for this task. The evidence file is already the
record of what happened; a log of what the user chose not to keep is the nag
this design spent its whole budget avoiding.

## The write

The `work` lane writes it — `knowledge/` is tier-2 under `work`
(`schema/state-schema.json § files[].owner`, `$PERRY_HOME/SKILL.md § The
hand-off contract`). No fourth writer, no new lane.

```
"$PERRY_HOME/bin/perry-knowledge" promote \
    --topic <topic> --slug <slug> \
    --claim "<the one-line claim>" \
    --source "<the citation from propose's prefill, verbatim>" \
    --invalidated-by "<the tripwire>" \
    --body-file <a file holding the claim body, ≤ ~30 lines> \
    --root .
```

It writes `knowledge/<topic>/<slug>.md` and re-renders `## Cards by topic` in
`knowledge/INDEX.md`, touching no other section of that index. **Do not write
the card by hand** — a hand-written card is how one arrives without a source,
which is the thing this whole phase exists to make impossible.

It refuses, and nothing is written, when: `--source` is missing or a dash; the
source resolves to nothing; `--invalidated-by` is missing; `--claim` is missing;
the card already exists; the project declares roles and no owner was given or
derivable. **Read the refusal and fix the input — never re-run with a
placeholder.** A card carrying `Source: —` would pass nothing and mislead
everything.

One topic, one claim per card. A topic that outgrows the subscription budget is
the signal to split topics, not to raise the cap (DESIGN-006 § 5.4).

## Where each capture point differs

**`close-task`** — one question, after the close is written. `--source` is the
evidence citation handed to `perry-task done --evidence`; `--rung` is the rung
chosen at pre-close gate 3. This is the ordinary case and the only one that
fires per task.

**`end-phase-retro`** — **at most one question for the whole retro**, and only
for a lesson the retro itself already identified as recurring across two or more
tasks. `--source` is `evidence/<YYYY-MM>/retro.md`. Batching is the named risk
in DESIGN-006 § 7 — a retro that offers six cards produces six rubber stamps —
so if the phase produced several durable claims, write one and note in the retro
that the others are candidates. The next close will offer them where they
belong.

**`/pmo incident close`** — **zero added questions.** The existing three-question
gate (`$PERRY_HOME/packs/software-ops/incidents.md`) already asks about
knowledge; the card is an option inside that Q1, alongside the digest. The
distinction Q1 now has to make: a **digest** is a source the project read, a
**card** is a claim the project made and can re-check. An incident that taught a
rule — "restart the daemon before the migration, never after" — is a card. An
incident that pointed at somebody else's document is a digest. `--source` is the
incident file.

## See also

- `$PERRY_HOME/perry/design/DESIGN-006-roles-and-knowledge.md § 5.3, § 5.4` — the
  card schema and the write/read paths this implements.
- `$PERRY_HOME/reference/user-load.md` — why this is one question and not five.
- `$PERRY_HOME/work/state/knowledge_card_TEMPLATE.md` — the shape, with the
  guidance on `Invalidated by` that most drafts get wrong.
- `reference/digests.md` — the other half of `knowledge/`: sources the project
  read, and the index build that owns every section but `## Cards by topic`.
