# DESIGN-001: Resumable interactive pipelines

> Status: locked
> Date: 2026-08-16 · Locked: 2026-08-16
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: —
> Supersedes: —   · Superseded by: —

## 1. Problem

Perry has two long interactive pipelines — `/perry adopt` (5 stages) and
`/perry diagnose` (6 stages). Both are front-loaded with the most expensive
thing in the product: an interview that asks the user to author goals or
declare tolerances. Both claim to be resumable. Neither survives the session
ending mid-run.

The trigger case is ordinary, not exotic: adoption stage 3 asks the user to
write an Objective set and a KR table from a strawman. That is a
thirty-to-sixty-minute task with real thinking in it. Users will close the
window. They will come back in a new agent session, days later, and type
`/perry adopt` again.

Four concrete defects, in severity order.

**P1 · An interrupted run is invisible at entry.**
`SKILL.md:127` fires first-time setup when a project has "no Perry state files
at all". Adoption stages 0–3 deliberately write no state files
(`reference/adoption.md § The one rule`, corollary 2: *"Nothing is materialized
mid-pipeline"*). So an abandoned run leaves only
`.perry/adoption/<date>-dossier.md` with `stage: confirm`, and the entry check
reads the project as virgin. The next session re-runs first-time setup, re-asks
document language and repo layout, re-asks new-vs-existing, and routes to a
fresh `/perry adopt` starting at stage 0. Because the dossier path is dated
(`.perry/adoption/*.md`), the second run writes a *sibling* file rather than
colliding — no warning, and the "rejections are memory" record
(`reference/adoption.md § Rejections are memory`) is now split across two files
that `--recheck` will read inconsistently.

`--resume` does not rescue this. It is opt-in by flag, and the user who
abandoned a run mid-interview is precisely the user who does not know the flag
exists.

**P2 · `confirm` is one enum value covering six sub-steps, including the long one.**
`adoption_stage` is `[scan, harvest, infer, confirm, commit, done]`.
`state/adoption_dossier_TEMPLATE.md:51` states that `stage` is what
*"`--resume` reads and nothing else"*. Stage 3 is six ordered sub-steps: state
root → goals → phase → clusters → attribution → transcriptions
(`reference/adoption.md § 3 · Confirm`). Resuming at `confirm` therefore
restarts at sub-step 0 and re-runs the entire interview — reproducing the exact
experience that caused the abandonment.

**P3 · Authored content has nowhere durable to live during `confirm`. This is data loss, not inconvenience.**
`OKR.md` is not written until stage 4. During stage 3 the user's authored
Objectives and KRs exist only in the dossier, and the dossier cannot hold them.
The per-candidate fields are `proposal` (Perry's strawman), `status`, and
`resolution` — whose schema note reads *"one line: why rejected / what the user
edited it to."* A single KR carries id, statement, metric, target, baseline,
stretch flag and deadline. One line cannot store one KR, let alone nine.

So the authored work survives only in the conversation transcript and dies with
the session. Fixing P1 and P2 without fixing P3 returns the user to a correctly
positioned interview that has forgotten what they wrote — which is worse than
restarting, because it looks like it worked.

Note the asymmetry: **`diagnose` already solved this problem and `adopt` did
not.** `schema/state-schema.json → files[id=diagnosis].interview[]` carries
`{q, asked, answer}` with the note *"verbatim; prescriptions cite it"*. The
pattern exists in the codebase; adoption simply lacks it.

**P4 · `commit` is not sub-resumable, and a half-commit is misread as merge mode.**
Stage 4 materializes through nine subcommands in dependency order
(`reference/adoption.md § 4 · Commit`). `stage` advances only *after* a stage's
writes are durable, so a session that dies after `OKR.md` and `phase/` but
before `BOARD.md` still records `stage: confirm`. The next run finds `OKR.md`
present, flips to `mode: merge` per `§ Merge mode`, and begins surfacing
adoption's own half-written state to the user as *"possible duplicates for the
user to resolve"*. The recovery field already exists —
`candidates[].materialized_as`, *"the real id it became at stage 4"* — but no
rule instructs the commit stage to consult it.

**Minor · dated filenames make "which dossier" ambiguous.** Resuming on a later
day yields two paths both valid under the `.perry/adoption/*.md` glob, with no
declared precedence.

**The same hole exists in `diagnose`, inverted.** `reference/diagnose.md
§ Stages` claims *"an interrupted run resumes rather than restarting the
interview"*, but the command surface has no `--resume` flag at all, and stage 2
is a six-question interview. It persists answers (P3 solved) but cannot be
resumed (P1, P2 unsolved).

## 2. Goals

1. A new agent session entering an interrupted pipeline **detects it without a
   flag** and offers the user a choice before doing anything else.
2. Resuming re-enters at the **sub-step** the user stopped at, not the top of
   the stage.
3. Everything the user **authored or declared** is durable at the moment they
   said it. A pipeline abandoned at any point loses zero user input.
4. Re-running `commit` after a partial materialization **completes it** rather
   than duplicating it or misclassifying the project as merge-mode.
5. A user can say **"I am not going to finish this"** and stop being asked,
   without destroying the rejection record that `--recheck` depends on.
6. One contract covers **both** `adopt` and `diagnose`, so the third
   interactive pipeline inherits it rather than reinventing it.

## 3. Non-Goals

- **Not making adoption shorter.** The interview length is correct; goal
  authoring is the value, not the overhead. This design makes the length
  survivable, not smaller.
- **Not resuming silently.** A run resumed without the user's say-so is a run
  that re-materializes decisions they may no longer stand behind. Detection is
  automatic; continuation is always confirmed.
- **Not materializing state before `commit`.** The guarantee that a user who
  abandons adoption halfway has an untouched project is load-bearing and stays.
  Durability is achieved inside the dossier, not by early writes.
- **Not a lockfile, daemon, or process-level state.** The dossier is the only
  mechanism. Two concurrent adoptions of one project is out of scope.
- **Not backfilling resumability into already-abandoned dossiers.** Existing
  dossiers without `step:` resume at stage granularity, as today.
- **Not changing `okr init`'s own interview.** Adoption drives it; if that
  interview needs internal checkpointing, that is a separate design.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Where authored content lives | Top-level `declarations[]` / Per-candidate `authored` block / Both | **Top-level `declarations[]`** | 2026-08-16 |
| 2 | Entry-time behavior on detection | Offer a choice / Require `--resume` / Resume silently | **Offer a choice** | 2026-08-16 |
| 3 | How an abandoned run is retired | New `abandoned` stage value / Separate `status:` field / Move file to an archive path | **New `abandoned` stage value** | 2026-08-16 |
| 4 | Scope of this change | Shared contract, both pipelines / `adopt` only / `adopt` now, `diagnose` later | **Shared contract, both pipelines** | 2026-08-16 |
| 5 | Sub-step tracking mechanism | Explicit `step:` field / Derive from existing per-item fields | **Explicit `step:` field** | 2026-08-16 |

All five resolved 2026-08-16. Every choice matched the drafted recommendation,
so § 5 Architecture stands as written and needs no revision.

Notes on the non-obvious ones:

- **#1** — `declarations[]` mirrors the shape `diagnosis.interview[]` already
  proves out, keeps authored text in one readable block rather than scattered
  across candidate rows, and handles declarations that are not candidates (the
  state-root answer, the phase slug). A per-candidate `authored` block keeps
  each edit next to the strawman it replaced, which reads better on review.
  They are not exclusive; "Both" costs one more field.
- **#3** — deleting the dossier is *not* an option, because it destroys the
  don't-ask-me-again record. Whatever is chosen must retire the run while
  preserving `candidates[].status: rejected`.
- **#5** — derivation is cheaper (no schema change: `clusters[].kr` absent
  means not yet attributed, `candidates[].status: pending` means not yet
  triaged) but cannot represent "the goals interview finished", and inferring
  position from side-effects is the class of guess Perry forbids elsewhere.

## 5. Architecture

### The contract

Three properties, named so both pipelines can be checked against them:

```
DISCOVERABLE  an interrupted run is found at entry, without a flag
POSITIONED    resume re-enters at the sub-step, not the stage
LOSSLESS      a user declaration is durable the instant it is made
```

LOSSLESS is the deep one, and it follows from a rule Perry already has.
`reference/adoption.md` governs the whole pipeline with **evidence proposes,
the user declares** — and `reference/diagnose.md` mirrors it with **measure,
ask, then prescribe**. A declaration that lives only in conversation memory
makes that rule hold *within one session only*. Persisting the declaration at
the moment it is made is not a new requirement; it is the existing requirement
extended to the axis of time.

There is already a precedent in the code for exactly this: adoption stage 3
step 0 writes the state-root answer to `.perry/config.md` **immediately**,
before any goal talk, rather than deferring it to `commit`. That is LOSSLESS
applied to one field. This design generalizes it.

### Frontmatter changes

Both `files[id=adoption]` and `files[id=diagnosis]` gain:

```yaml
stage: confirm          # unchanged, coarse position
step:  goals            # NEW — fine position within the stage
```

`step` is enum'd per stage. New enums in `schema/state-schema.json`:

| Enum | Values |
|---|---|
| `adoption_step_confirm` | `state_root`, `goals`, `phase`, `clusters`, `attribution`, `transcriptions` |
| `adoption_step_commit` | one per row of the § 4 · Commit target table, in dependency order |
| `diagnosis_step_interview` | `q1` … `q6`, `audience`, `attachment` |
| `diagnosis_step_execute` | `rx-<n>` — the prescription item in flight |

`adoption_stage` and `diagnosis_stage` both gain a terminal value
`abandoned` (pending decision #3).

Adoption gains a durable record of declarations (pending decision #1):

```yaml
declarations:
  - step: goals
    at: "2026-08-16T14:22:00Z"
    content: |
      ## Objective 1 — The opt-in control plane
      | Id | KR | Metric / Target | Stretch? | Deadline |
      ...
```

`content` is verbatim, multi-line, and is what `commit` hands to
`/okr init` — the strawman in `candidates[].proposal` is never re-read once a
declaration supersedes it.

### Entry sequence

A new step 0 in `SKILL.md`, before both the standup and first-time setup:

```
1. glob .perry/adoption/*.md and .perry/diagnose/*.md
2. parse `stage:`; select entries where stage not in (done, abandoned)
3. if none      → current behavior, unchanged
   if exactly 1 → render the interrupted-run card, then ask
   if >1        → list them, ask which to act on first
```

The card states position and cost, so the choice is evaluable — per
`reference/user-load.md`, an ID never travels alone and a question the user
cannot predict the consequences of should not be asked:

```
⏸  Interrupted run · /perry adopt · aiMark
   Stopped 3d ago at stage 3 (confirm) · step: goals
   Already decided : state root `perry/`, document language English
   Already authored: 2 Objectives, 9 KRs
   Not yet done    : phase, 6 clusters, attribution, 2 transcriptions
   Nothing has been written to the project yet.
```

Then one `AskUserQuestion`, header `"Interrupted run"`:
`Resume where you left off (Recommended) | Start over (archives this dossier) | Abandon it`.

**Start over** moves the dossier to
`.perry/adoption/archive/<date>-dossier.md` and begins a fresh run — the
rejection record survives and `--recheck` reads the archive.
**Abandon** sets `stage: abandoned` in place.

This makes `--resume` a shorthand rather than the only door: it skips the card
and continues. That is the right relationship — the flag serves the user who
knows what they want, the card serves the user who does not.

### Commit idempotency

Two rules, both stated in `reference/adoption.md § 4 · Commit`:

1. **Skip what already landed.** A candidate with `materialized_as` set is not
   re-materialized. This makes stage 4 re-runnable to completion after any
   interruption.
2. **`mode` is decided once, at stage 0.** Merge mode is determined from Perry
   state that exists *before this dossier began* — recorded as
   `mode: merge` at scan time and never recomputed. State written by this
   dossier's own commit stage can never cause a mode flip.

Rule 2 is what stops a half-commit from re-entering as a merge and asking the
user to disambiguate its own output.

### Diagnose parity

`diagnose` gains `--resume` in its command surface, the same entry-card
treatment, and `step:` on its interview and execute stages. Its execute stage
has an additional constraint the adopt pipeline does not: `restore_point` must
be non-null before execute begins, and on resume it must be **re-validated**
(the branch may be gone), not trusted from the file.

## 6. Implementation plan

| Phase | Scope | Proposed PMO task(s) | Owner |
|---|---|---|---|
| A | Schema: `step:` field + 4 step enums, `abandoned` stage value, `declarations[]` on adoption. Update `state/adoption_dossier_TEMPLATE.md` and the diagnosis template. | TASK-001 | Coding Agent |
| B | `SKILL.md` entry step 0: interrupted-run detection, the card, the three-way choice, archive path. Applies to both pipelines. | TASK-002 | Coding Agent |
| C | `reference/adoption.md`: per-sub-step resume rules for `confirm`; LOSSLESS rule for declarations; commit idempotency rules 1–2; dossier precedence rule. | TASK-003 | Coding Agent |
| D | `reference/diagnose.md`: add `--resume` to the surface, sub-step rules, restore-point re-validation on resume. | TASK-004 | Coding Agent |
| E | `bin/perry-lint`: validate `step:` against the stage's enum; flag a dossier whose `stage` is non-terminal and older than N days as a stale run. | TASK-005 | Coding Agent |
| F | Tests: a fixture dossier stopped at `confirm/goals` and one at `commit/board`; assert entry detection fires and resume re-enters correctly. | TASK-006 | Coding Agent |

Phases A–C are the minimum that fixes the reported scenario. D–F can follow.

## 7. Risks & mitigations

| Risk | Detection | Mitigation |
|---|---|---|
| `step:` drifts out of sync with the prose sub-steps in `reference/adoption.md`, so resume lands in the wrong place | Test fixture per step value; lint validates `step` against the stage enum | Generate the enum list and the reference's sub-step headings from one source, or add a test asserting they match |
| A stale dossier from an abandoned experiment nags the user at every `/perry` entry | User reports; the card appearing on unrelated invocations | The `abandoned` terminal state, plus a lint staleness warning that suggests retiring it |
| `declarations[].content` diverges from what `commit` actually writes, so the audit trail lies | Compare declaration content to the materialized file during Phase F tests | `commit` writes *from* the declaration, never from a re-render; record `materialized_as` on the declaration too |
| The entry card fires on a project where the user genuinely wants a fresh start, adding friction | — | "Start over" is a first-class option on the card, one keypress, and it archives rather than deletes |
| Resuming a run started under a different `--depth` or `--only` silently mixes scopes | `depth` and `lanes` are already in the dossier frontmatter | On resume, state the original depth/lanes in the card; a mismatch with new flags is refused, not merged |

## 8. Open questions

- Should the interrupted-run card appear on **every** `/perry` invocation, or
  only on `/perry adopt` / `/perry diagnose`? Appearing everywhere is more
  discoverable and more annoying. Leaning: everywhere, but collapsed to one
  line on the standup once the user has seen it in full.
- Is there a case for `declarations[]` on `diagnosis` too, or is
  `interview[].answer` already sufficient there? Its prescriptions are Perry's,
  not the user's, so probably sufficient.
- ~~N for the stale-run lint warning.~~ **Resolved 2026-08-16: 30 days.** Long
  enough that a genuinely paused adoption is not nagged, short enough to catch
  one that is actually dead. Declared once, in
  `schema/state-schema.json § thresholds.stale_run_days`, so `perry-lint` and
  the entry card cannot disagree about when a run is stale. It remains a
  calibrated default, not a law — the finding says so in its own text.

## 9. Changes (append-only after lock)

- 2026-08-16 — Stale-run threshold set to **30 days** (§8 open question) —
  USER-001 answered; declared in `schema/state-schema.json § thresholds` rather
  than hardcoded in either reader.
- 2026-08-16 — Detection moved from a prose `ls` to
  `perry-state --section interrupted` — the gate was telling the agent to read
  `stage:` by eye, which is the estimating `schema/README.md` forbids
  everywhere else, and here it would have been estimating how much of the
  user's own work survived.
- 2026-08-16 — `parse_yaml_subset` gained block-scalar support. Not anticipated
  by this design and load-bearing for it: `declarations[].content` is specified
  as verbatim multi-line, but the reader rejected block scalars outright, so
  every real dossier would have failed lint — and `reference/adoption.md § 4`
  makes a clean lint the gate on adoption completing at all.

## 10. References

- `reference/adoption.md` — § The one rule (corollary 2, no mid-pipeline
  materialization), § 3 · Confirm, § 4 · Commit, § Merge mode, § Rejections are
  memory
- `reference/diagnose.md` — § Stages (the unbacked resume claim), § 4 · Execute
  (restore point)
- `reference/user-load.md` — the constraint on the entry card's question
- `schema/state-schema.json` — `files[id=adoption]`, `files[id=diagnosis]`,
  `adoption_stage`, `candidate_status`
- `state/adoption_dossier_TEMPLATE.md:51` — "`--resume` reads this and nothing
  else"
- `SKILL.md:127` — the first-time-setup entry condition this design amends
