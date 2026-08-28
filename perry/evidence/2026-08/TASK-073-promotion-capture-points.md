# TASK-073 — DESIGN-006 phase B: the promotion question, and the write it can refuse

> Source: `perry/design/DESIGN-006-roles-and-knowledge.md § 5.4`, § 6.1 phase B.
> Builds on: `perry/evidence/2026-08/TASK-072-knowledge-cards.md` (phase A).
> Rung: **V3**. Everything below is a run.

## What shipped

- **`bin/perry-knowledge`** — the write path. `propose` is read-only and
  answers *should the capture point fire, and with what pre-filled*; `promote`
  writes `knowledge/<topic>/<slug>.md` and re-renders `## Cards by topic` in
  `knowledge/INDEX.md`, touching no other section of it.
- **`work/reference/promotion.md`** — one procedure, quoted from three capture
  points rather than copied into them.
- Capture points wired: `close-task` and `end-phase-retro` in
  `work/reference/subcommands.md`, incident close in
  `packs/software-ops/incidents.md`.
- `tests/test_knowledge_promotion.py` — 31 tests. Suite 1129 → 1160.

## Why a new tool and not a `perry-task` subcommand

Three reasons, in the order they decided it.

`perry-task` is 3,939 lines and `TASK-066` exists to split it; adding a
subcommand needs an argument it does not have here. The promotion write shares
nothing with the board — not the row model, not the journal line, not the event
log — so it would be a fourth unrelated domain inside the file whose size is
already a tracked problem.

**Prose alone cannot refuse.** § 6.1 phase B's verification is *a sourceless
write is refused*. A refusal that lives in a procedure document is a refusal an
agent can talk itself past, and phase A already put the advisory version in the
linter. The deliverable is specifically the thing prose cannot be.

And the write is small and closed: one file created, one section of one index
re-rendered, nothing else. That is the shape `perry-decide` has for `decide`,
and copying it cost 560 lines with no new concepts.

`bin/README.md` said "only two tools write project files". It now says three,
with the reason: a knowledge card is the one state file whose **absence is
safer than a wrong version of it**, and only a write path can enforce that.

## The one question

`reference/user-load.md` caps what a person can carry and this adds a prompt to
a ritual people already run, so the budget is one `AskUserQuestion`. A card has
five fields; four are derived or pre-filled and never asked:

| Field | Source |
|---|---|
| `Kind` | `knowledge` by default; `source-of-truth` when the claim names an external system |
| `Owner role` | `—` before roles exist · the single declared role when there is one · else **refused**, naming the roles |
| `Source` | the evidence citation the close just wrote — pre-filled, never typed |
| `Last verified` | today |

What is left is the claim and the tripwire, and **both are shown already
drafted**, so the question is a confirmation and not an interview:

```
Keep this as a knowledge card?
  Claim:        the monthly export must exclude tenants flagged `is_test`
  Invalid when: the `tenants` table stops carrying `is_test`
[ Write it (Recommended) ] [ Write it — my wording ] [ Skip — nothing durable ]
```

`Owner role` is the field where "derive or refuse" bites. One declared role is
one right answer and asking would be a second prompt; several declared roles
with no `Role:` on the row is a genuine gap, and a card nobody owns is a card
nobody re-verifies — so it refuses and names the candidates rather than writing
a dash.

**A skip writes nothing, anywhere.** No journal line, no "promotion declined"
note, no re-ask. A log of what the user chose not to keep is exactly the nag
this design spends its whole budget avoiding.

## When it fires, and when it does not

`propose` is the mechanical half — four reasons to stay silent, all tested:

| `reason` | Line |
|---|---|
| `no-source` | the close cited no evidence, so `Source:` would be something the agent chose rather than something the run produced |
| `source-unresolvable` | the citation names no file, task id or `SRC-n`. A citation that looks checkable and is not is worse than none |
| `rung-unverified` | the close was `V0`/`V1` — the agent attesting its own artifact |
| `already-promoted` | a card already cites this source |

The rung floor is the one line DESIGN-006 does not draw, and the argument for
drawing it here: phase A's `Source:` check asks *can a reader re-open this*,
and at V1 the answer is "yes, and it says an agent thought so". A store whose
provenance bottoms out there is the confident-error farm § 5.3 exists to
prevent, arriving through the front door. It declines to **ask**; `promote`
still writes if the user asks outright, because a user declaring always
outranks what the evidence proposed.

Three more conditions are judgement and stay in `promotion.md`, because a tool
that pretended to answer them would be guessing:

- **You must have a draft** — an actual one-line claim *and* an actual
  tripwire. This is the condition that keeps the capture point off most closes,
  and it is the point: a question that fires on every close is one people learn
  to dismiss, and then it fires on the one that mattered.
- **The claim must outlive its task.** If it cannot be stated without naming
  the task, it belongs in the evidence file it came from.
- **A tripwire is not a date.** `Last verified` already covers the passage of
  time.

It never fires on `drop-task` — a dropped row produced no verified finding, and
§ 5.4 names three capture points, not four.

The three differ in cost, deliberately: `close-task` adds **one** question;
`end-phase-retro` adds **at most one for the whole retro**, and only for a
lesson the retro already found recurring (batching is § 7's named risk — six
offered cards produce six rubber stamps); incident close adds **zero**, because
its three-question gate already asks about knowledge and the card is one more
option inside Q1, beside the digest. The distinction Q1 now has to draw is real
and was not stated anywhere: a **digest** is a source the project read, a
**card** is a claim the project made and can re-check.

## The V3 run

A real close, then the capture point, on a scratch project:

```
$ perry-task done TASK-001 --evidence evidence/2026-08/TASK-001-export-fix.md --rung V3
perry-task: wrote TASK-001 (done) → board + journal + event

$ perry-knowledge propose --source "TASK-001 · evidence/2026-08/TASK-001-export-fix.md" --rung V3 --json
  "fires": true, "reason": "ready",
  "prefill": {"Kind": "knowledge", "Owner role": "—",
              "Source": "TASK-001 · evidence/2026-08/TASK-001-export-fix.md",
              "Last verified": "2026-08-18"}

$ perry-knowledge promote --topic reporting --slug test-tenants --claim … --source … --invalidated-by …
perry-knowledge: wrote knowledge/reporting/test-tenants.md

$ perry-lint --knowledge
  ✓ 1 card(s), every provenance field present and resolving
```

And the refusal, in the four shapes that matter:

```
$ perry-knowledge promote … (no --source)
refused — --source is required and is not satisfied by a dash: a card that
cannot say where its claim came from is refused, not written blank …

$ perry-knowledge promote … --source "—"
refused — (same)

$ perry-knowledge promote … --source evidence/2026-08/never-written.md
refused — resolves to no file, task id or `SRC-n` … a claim citing a source
nobody can re-open is a claim about the agent's memory

$ perry-knowledge promote … (no --invalidated-by)
refused — name the observable condition under which this stops being true …
```

Nothing is written on any of them — the topic directory is not created either,
which one of the tests asserts specifically, because a refusal that leaves
debris is a refusal people work around.

## The phase-A defect this found

`resolves_somewhere` and `check_knowledge` both computed the project root as
`state_root.parent if state_root.name else state_root`. `resolve_state_root`
returns the **project root** by default, so on every project that has not moved
its state — `State root: .`, the common case — that expression named the
directory *above the project*. Two consequences, both live:

- `.perry/events.jsonl` was looked for outside the project, so a card citing
  the task id of a **closed** row was reported `card-source-dangling`. The row
  is gone from `BOARD.md` by then; the event log is the only place the id
  survives.
- `.perry/roles/` was looked for outside the project, so `card-unowned` — the
  finding phase A wrote for exactly the moment roles land — **could not fire on
  a flat-layout project at all**.

Neither was covered: phase A's fixture is flat, so the second check was blind in
its own test suite, and no test cited a closed task. Fixed by passing
`project_root` rather than deriving it (four lines in `bin/perry-lint`), and
pinned by `TestTheProjectRootIsPassedNotDerived` — including the complement, so
a rule that fired on every card could not pass it.

The default lint is unaffected: neither function runs outside `--knowledge`.
`gimegime-pmo` stays at **59** errors and `PolyForge` at **11**.

## Mutation table

19 mutations, each anchored **by line number** with the current line text
asserted before the swap — never `str.replace`, which is how a mutation in this
project once hit the wrong copy of a three-times-repeated string. `__pycache__`
cleared before and after every run (`perry/knowledge/toolchain/pycache-staleness.md`).

| # | File:line | Reverted | Named test | Result |
|---|---|---|---|---|
| M1 | `bin/perry-knowledge:466` | the `--source` refusal → `if False` | `TestASourcelessCardIsRefused.test_a_missing_source_is_refused_and_nothing_is_written` | RED |
| M2 | `bin/perry-knowledge:466` | `or src in UNDECLARED_CELL` dropped | `…test_a_dash_does_not_satisfy_the_source` | RED |
| M3 | `bin/perry-knowledge:474` | the resolution refusal → `if False` | `…test_a_source_that_resolves_nowhere_is_refused` | RED |
| M4 | `bin/perry-knowledge:474` | project root derived as `sr.parent` again | `TestARealCloseProducesACard.test_a_closed_task_id_still_resolves_as_a_source` | RED |
| M5 | `bin/perry-knowledge:482` | the `--invalidated-by` refusal → `if False` | `TestTheOtherMandatoryFields.test_a_card_without_a_tripwire_is_refused` | RED |
| M6 | `bin/perry-knowledge:459` | the `--claim` refusal → `if False` | `…test_a_card_without_a_claim_is_refused` | RED |
| M7 | `bin/perry-knowledge:451` | the `Kind` enum check → `if False` | `…test_a_kind_off_the_declared_set_is_refused` | RED |
| M8 | `bin/perry-knowledge:518` | the overwrite refusal → `if False` | `…test_a_card_is_never_silently_overwritten` | RED |
| M9 | `bin/perry-knowledge:111` | `UNVERIFIED_RUNGS = ()` | `TestWhenTheCapturePointDoesNotFire.test_a_self_attested_close_means_no_question` | RED |
| M10 | `bin/perry-knowledge:111` | `UNVERIFIED_RUNGS` widened to V2/V3/V5 | `…test_a_verified_close_does_fire` | RED |
| M11 | `bin/perry-knowledge:433` | the already-promoted check → `if False` | `…test_asking_twice_about_one_source_is_the_nag_this_avoids` | RED |
| M12 | `bin/perry-knowledge:415` | `propose`'s no-source branch → `if False` | `…test_no_evidence_means_no_question` | RED |
| M13 | `bin/perry-knowledge:496` | single-role derivation → `elif False` | `TestOwnerRole.test_one_role_declared_is_derived_not_asked` | RED |
| M14 | `bin/perry-lint:1214` | `rdir` derived from `state_root.parent` again | `TestTheProjectRootIsPassedNotDerived.test_an_unowned_card_is_reported_once_roles_exist` | RED |
| M15 | `bin/perry-lint:1257` | `resolves_somewhere` handed `state_root.parent` | `…test_a_card_citing_a_closed_task_is_not_dangling` | RED |
| M16 | `bin/perry-knowledge:318` | index format-hint preservation dropped | `TestTheIndexIsPatchedAndNothingElseIs.test_only_the_cards_section_changes` | RED |
| M17 | `work/reference/subcommands.md:624` | `close-task`'s route to the procedure removed | `TestTheCapturePointsCiteTheOneProcedure.test_each_capture_point_routes_to_it` | RED |
| M18 | `work/reference/subcommands.md:301` | the retro's route removed | `…test_each_capture_point_routes_to_it` | RED |
| M19 | `packs/software-ops/incidents.md:58` | incident close's route removed | `…test_each_capture_point_routes_to_it` | RED |

Every mutation went red and every test went green again on restore, which the
harness asserts rather than assumes. No green mutation to report.

M10 and `test_an_owned_card_is_not_reported` are the anti-vacuity pair: a rung
floor that rejected every rung, or an ownership rule that fired on every card,
would pass their partners and fail these.

## Gate

- `python3 -m unittest discover -s tests -q` — **1160 tests, OK** (1129 at branch point).
- `python3 bin/perry-lint` on Perry — clean.
- `python3 bin/perry-lint --knowledge` on Perry — 1 card, no findings.
- `perry-lint --root <copy of gimegime-pmo>` — **59** errors (unchanged).
- `perry-lint --root <copy of PolyForge>` — **11** errors (unchanged).

## Found and not fixed

- **`knowledge/INDEX.md` has no tool that creates it.** `promote` re-renders
  `## Cards by topic` when the index exists and refuses to invent one when it
  does not, because a cards-only index would assert "(no digests yet)" about a
  tree this tool never looked at. The digest flow that owns the other sections
  is prose (`work/reference/digests.md`), so on a project with cards and no
  index the cards are written and listed nowhere. Worth a row: either the
  digest index build becomes a tool, or `promote` learns to render both halves.
- **No size cap on a card body.** § 5.4 says cards are size-capped precisely so
  subscription stays affordable, and the template says "roughly thirty lines".
  Nothing enforces it. Deliberately not added here: a new warning class is the
  kind of thing that changes external projects' counts, and the number belongs
  in `schema/state-schema.json § thresholds` next to `knowledge_stale_days`
  rather than in the tool.
- **`Kind: source-of-truth` is writable but has no extra shape.** § 5.3 says
  such a card names an external system, its authoritative access path, and what
  falsifies it — three things, and only the third (`Invalidated by`) is a field
  today. Phase F owns the type; `promote` accepts the kind so phase F does not
  have to reopen this file.
- **`Owner role` cannot yet be pre-filled from the task row.** The `Role:`
  field lands in phase E. Until then `promote` derives it only when the project
  declares exactly one role, and refuses otherwise. When phase E lands, the
  capture point should pass the row's `Role:` through `--owner-role` and the
  refusal becomes unreachable in the ordinary case.
