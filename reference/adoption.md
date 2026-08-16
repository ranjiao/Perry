# Adoption — converting an existing project into Perry state

Loaded when `/perry adopt` fires. Not loaded on routine snapshots or first-time
setup of a genuinely new project.

`okr init` and `pmo bootstrap` both assume a blank slate: one interviews the user
from zero, the other writes empty templates. Neither reads the project. An
existing project already contains most of the answers — in git history, README,
roadmap docs, ADR folders, open issues, TODO comments — but those are
**evidence**, not declarations.

## The one rule: evidence proposes, the user declares

**Adoption never writes a state file directly, and never writes anything the user
did not choose.** It writes exactly one artifact of its own — the dossier — and
everything that reaches `OKR.md` / `BOARD.md` / `design/` gets there through the
normal subcommands after the user accepted it.

This is the same class of gate as `pmo` "no `done` without evidence" and `okr`
"never infer attribution". It guards the property `schema/README.md` exists to
protect: *a number on the dashboard must be traceable to a field somebody wrote
down.* Adoption is inference by nature, so without this rule a freshly adopted
project's dashboard is a pile of plausible guesses that nobody can distinguish
from fact ever again.

Three corollaries, all load-bearing:

- **One writer per file survives adoption.** Adoption is an orchestrator. `okr`
  still writes `OKR.md`, `pmo` still writes `BOARD.md`, `design` still writes
  `design/`. Adoption owns only `.perry/adoption/`.
- **Nothing is materialized mid-pipeline.** Stages 0–3 write only the dossier. A
  user who abandons adoption halfway has an untouched project.
- **Harvested evidence is quoted, never translated.** The dossier and everything
  materialized from it are written in `Document language` — but a citation is a
  claim about what a source *says*, so a README line, a commit subject, an issue
  title or a TODO comment is reproduced in the language it was written in, with
  the paraphrase alongside if one helps. Translating a quote and then citing it
  turns evidence into assertion, which is the one thing this pipeline exists to
  prevent. Adoption also asks for `Document language` during `confirm`, next to
  `State root`, when `.perry/config.md` does not exist yet — an existing
  project's own docs are the best available evidence for which language it
  should be. See `reference/i18n.md`.

## The asymmetry: what may be inferred, and what may not

Evidence records what was *done*. It contains no information about what winning
means. So the three layers are authored differently, and this is not negotiable:

| Layer | Authored by | Why |
|---|---|---|
| `OKR.md`, `phase/` | **The user**, from an evidence-drawn strawman | git history has zero information about intent. A plausible-looking inferred Objective is worse than no Objective, because the whole cascade inherits it. |
| `BOARD.md` tasks | **Evidence**, user-triaged in bulk | "what is unfinished" is genuinely legible from TODOs, open issues, and stale branches. High volume, reliable inference. |
| `design/`, `decisions/`, `knowledge/` | **Transcribed only** | Converted where a real source document exists. Never invented. |

### Declared is not inferred

The rule bites on goals **derived** from evidence. A goal the user *wrote down* in
a tier-A source — an `objective:` field in a native manifest, a "Mission" heading
in the README, a stated phase — is a **transcription**, and forcing it through a
strawman interview is pointless friction. Transcribe it, show the citation, and
let the user correct it.

The distinction survives contact with reality because the two almost never come
together: projects state their purpose and almost never state a measurable KR.
On the first real adoption test the objective and the current phase were both
declared outright, and there was **not one KR anywhere in the repo** — so the
strawman rule still applied to every single KR. That is the normal shape.

### Transcribe to convert, not to copy

The third row has a second clause that only shows up on a real project: **if the
source document is already in the repo and readable where it is, do not
transcribe it.** Copying `design/global-search.md` into `design/DESIGN-001-*.md`
produces two copies of one document, which is the duplication
`pmo/SKILL.md § Style rules` forbids outright — and the copy starts rotting
immediately.

Transcribe when Perry's structure adds something the source cannot provide: an
ADR log that gives a decision an audit trail and a supersession chain, a design
doc that needs the lock gate. Otherwise **reference it** and move on. On the
first real adoption run this killed two of the three transcription candidates —
a design doc that was fine where it was, and a digest of the project's own
`SIGNING.md`. `knowledge/` is for **external** material dropped in `inputs/`; a
document already in the repo is not external.

The third row of the table is the one that gets violated under pressure. A project with
undocumented decisions is *not* a project that needs Perry to write ADRs for
them — inventing an ADR for a decision nobody recorded manufactures history and
gives the rationale a false provenance. Surface it as a **task** ("capture why we
chose X") and let the user write it.

## Command surface

```
/perry adopt [--depth=quick|standard|deep] [--only=<lanes>] [--resume] [--recheck]
```

| Flag | Effect |
|---|---|
| `--depth` | How much to read. Default `standard`. Matrix in `reference/adoption-sources.md § Depth`. |
| `--only` | Comma-separated lanes: `okr,board,design,knowledge,arch`. Default all. |
| `--resume` | Continue from the dossier's `stage:` + `step:`. A **shorthand**: `SKILL.md` step 2 detects an interrupted run without it, so this only skips the card. A `--depth` / `--only` that disagrees with the dossier is refused, not merged. |
| `--recheck` | Drift mode against an already-adopted project — see § Recheck. |

Top-level first-time setup (`SKILL.md § First-time setup`) asks whether this is a
fresh start or an existing project, and routes here for the latter. The
`okr init` → `plan-phase` → `pmo` chain is unchanged for fresh starts.

## Stages

Five stages. Each records its position in the dossier before handing on —
`stage:` for which stage, `step:` for where inside it.

### The resume contract

Three properties, and every stage below is written to hold all three. They exist
because the expensive part of this pipeline is an interview that asks the user to
author goals, and a user will close that window.

**DISCOVERABLE.** An interrupted run is found at entry, without a flag.
`SKILL.md § Mandatory first move` step 2 owns this. It cannot live here: stages
0–3 write no state file, so an abandoned run is indistinguishable from a virgin
project by the only check the entrance used to make.

**POSITIONED.** Resume re-enters at `step`, not at the top of `stage`. `confirm`
and `commit` are each many ordered sub-steps; re-running `confirm` from sub-step
0 re-asks the whole interview, which is the experience that caused the
abandonment in the first place.

**LOSSLESS.** *Every user declaration is persisted the instant it is made.*

That last one is not a new requirement — it is **evidence proposes, the user
declares** extended to the axis of time. A declaration that lives only in
conversation memory makes the governing rule hold *within one session*, which is
not a property worth having. The precedent already existed: stage 3 step 0 writes
the state-root answer to `.perry/config.md` immediately rather than deferring it
to `commit`. Everything else the user authors now behaves the same way, via
`declarations[]`.

Note what LOSSLESS does **not** license. It is not permission to materialize
state early — corollary 2 above still holds, and a user who abandons adoption
halfway still finds an untouched project. Declarations are durable *inside the
dossier*; the project is written only at stage 4.

### 0 · Scan (read-only, no files written)

Detect what is harvestable and report it. Runs the source detectors in
`reference/adoption-sources.md`, counts what each would yield, and prints:

```
🔎 Adoption scan · <project> · depth=<d>

   Tier A (declarative)  : README.md, CHANGELOG.md, docs/ (14 files), TODOS.md
   Tier B (behavioral)   : git — 412 commits, 6 mo window, 9 commit scopes
   Tier C (structural)   : 63 modules, 28 TODO/FIXME markers
   Existing Perry state  : none
   Estimated candidates  : ~40–60 · clusters ~6–8
```

Then ask whether to proceed. A scan that finds almost nothing is a legitimate
answer — say so and recommend `okr init` instead. Adoption is not always worth it.

### 1 · Harvest (evidence, no interpretation)

Read the detected sources and record what they say, with provenance. **Every
harvested claim carries a citation** — `path:line` for files, a commit SHA for
git, an issue number for a tracker. Same discipline as a digest's `(§N)` cites;
an uncitable claim is dropped, not softened.

Writes `sources[]` in the dossier. No candidates yet — separating "what the
project says" from "what Perry thinks it means" is what makes stage 2 reviewable.

### 2 · Infer (candidates, never state)

Turn evidence into `candidates[]`. Each carries `kind`, `confidence`,
`evidence[]`, `cluster`, and a proposed `target` file. Nothing is written outside
the dossier.

Confidence is about *Perry's reading of the evidence*, not about whether the
candidate is a good idea:

| Confidence | Means |
|---|---|
| `high` | The source states it outright (an open issue, a doc heading, an unchecked roadmap box). |
| `medium` | It follows from convergent evidence (a stale branch + matching TODO + a commit scope). |
| `low` | One weak signal. Include it, flag it, expect rejection. |

Then **cluster** (see § Clustering). Clustering happens here, not at confirm, so
that `--resume` picks up a stable grouping.

### 3 · Confirm (the interview)

Ordering matters and is fixed, because attribution depends on goals existing:

0. **Where Perry's files go.** Before any goal talk, run

   ```
   python3 "$PERRY_HOME/bin/perry-lint" --claims --root .
   ```

   which resolves every path in `schema/state-schema.json § claims[]` against
   the project and reports what is already taken. **Do not enumerate the claimed
   paths in prose** — this step used to name four of them while the skills wrote
   eighteen, so a project owning `evidence/` or `knowledge/` collided silently.
   `design/` is the common collision, but it is not the only one, and the list
   is not this file's to keep. If anything
   collides, **ask** (`AskUserQuestion`, header `"State root"`, options:
   `Put Perry's files under perry/ (Recommended) | Use the project root anyway |
   Another directory`) and record the answer as `State root:` in
   `.perry/config.md`.

   Perry must not claim a namespace it was not given. An existing
   `design/global-search.md` is its author's document, not a malformed Perry
   design doc, and adopting on top of it would make every future lint run report
   the user's own file as broken. `bin/perry-lint` now refuses to judge anything
   outside `.perry/` until the project is actually adopted, but that only covers
   the before; the state root is what covers the after.

1. **Goals first.** Render the strawman OKR — Objectives and KRs drawn from
   evidence, each showing its citation — then run the *normal* `okr init`
   interview with those as the starting draft. The user rewrites freely. The
   input-quality pass (`reference/input-quality.md § 1`) runs as it always does.
   Do not skip the interview because the strawman looks good.
2. **Phase second.** The current phase is the one inference that is genuinely
   strong: recent commit activity is a reliable statement of what is being worked
   on *now*. Propose it, still let the user author the KRs.
3. **Clusters third.** Triage cluster by cluster (see § Clustering).
4. **Attribution fourth.** Map each accepted cluster to a KR (see § Attribution).
5. **Transcriptions last.** Existing design docs, ADRs, and documents worth
   digesting — one confirmation each, since volume here is low.

Every outcome is recorded in the candidate's `status`. **Rejections are kept**,
not deleted — see § Rejections are memory.

#### Resuming inside `confirm`

Write `step:` **before** starting each sub-step, and append to `declarations[]`
**as soon as** the user finishes one — not at the end of the stage, and never at
stage 4. The six values of `adoption_step_confirm` map one-to-one onto the six
numbered sub-steps above, in order:

| `step:` | Sub-step | On resume |
|---|---|---|
| `state_root` | 0 · Where Perry's files go | Skip if `.perry/config.md` already carries `State root:` |
| `goals` | 1 · Objectives + KRs | Skip if a `declarations[]` entry has `step: goals` — **re-render it back to the user, do not re-ask** |
| `phase` | 2 · The current phase | Skip if a declaration has `step: phase` |
| `clusters` | 3 · Cluster triage | Resume at the first cluster whose candidates are still `status: pending` |
| `attribution` | 4 · Cluster → KR | Resume at the first cluster with no `kr:` |
| `transcriptions` | 5 · Designs / ADRs / digests | Resume at the first `design`/`decision`/`knowledge` candidate still `pending` |

The last three resume from per-item state rather than from `step` alone, because
they are loops — `step` says which loop, the items say how far. `step` is still
written, so a resume never has to infer which loop it was in.

**Re-render, never re-ask.** On resuming at `goals` with a declaration already
banked, print what the user authored and ask only whether they want to change it.
Silently accepting it is worse — the user cannot tell whether their hour of work
survived — and re-asking discards it.

### 4 · Commit (materialize)

Write in dependency order, each through its owning subcommand:

| Candidate kind | Target | Written by |
|---|---|---|
| — | `.perry/config.md` | `/perry` setup (language + repo layout) |
| `objective`, `kr` | `OKR.md` | `/okr init` |
| `phase`, phase KRs | `phase/001-<slug>.md` + `phase/<NNN>-linkage.md` | `/okr plan-phase` |
| `design` | `design/<ID>-<slug>.md` | `/design new` |
| `task` | `BOARD.md` + journal | `/pmo add-task` |
| — | linkage `tasks[]` edges | `/okr link` (from the cluster→KR map) |
| `decision` | `decisions/ADR-NNN-*.md` | `/pmo decide` |
| `knowledge` | `knowledge/<topic>/` | `/pmo digest` |
| `arch` | `ARCHITECTURE.md` | `/pmo architecture init` |
| `risk` | `PROJECT_STATE.md § Risks` | `/pmo risk` |

**`commit` is resumable and idempotent.** It writes through nine subcommands, and
a session that dies partway leaves some of them done. Two rules make re-entry
safe:

1. **Skip what already landed.** A candidate carrying `materialized_as` is not
   re-materialized, and a declaration carrying `materialized_as` is not
   re-written. Set both at the moment the write succeeds, and advance `step:`
   with them, so re-running stage 4 always completes rather than duplicating.
2. **`mode` is decided once, at stage 0, and never recomputed.** Merge mode is
   determined from Perry state that existed *before this dossier began*. Without
   this, a half-finished commit is indistinguishable from a partially adopted
   project: the next run finds the `OKR.md` it wrote itself, flips to
   `mode: merge`, and starts asking the user to resolve its own output as
   "possible duplicates".

`commit` writes **from `declarations[]`**, never from a re-render of
`candidates[].proposal`. The proposal was Perry's strawman; the declaration is
what the user actually authored, and the two diverge the moment the user edits
anything.

Then:

1. Run `"$PERRY_HOME/bin/perry-lint" --root .` — **adoption is not complete
   until it passes.** A conversion that produces malformed state is worse than no
   conversion, because every downstream reader silently zeroes.
2. Write `decisions/ADR-001-perry-adoption.md` (`Type: Process`) recording what
   was adopted, from which sources, at which depth, and — explicitly — **which
   parts were user-authored and which were transcribed**.
3. Set the dossier's `stage: done`; leave it in place as the audit record.
   `done` and `abandoned` are the two terminal values — the entry gate skips
   both. **`abandoned` is set only by the user**, via the entry card, and never
   by Perry deciding a run has gone stale.
4. Run the post-adoption report (§ Post-adoption report).

### 5 · Recheck (ongoing)

`/perry adopt --recheck` re-runs stages 0–2 against an already-adopted project
and diffs the candidates against live Perry state. It exists because adopted
projects fail in one predictable way: **the user keeps shipping and stops telling
the board.** A greenfield project builds the habit alongside the code; an adopted
one has years of momentum that routes around Perry.

Output is a drift report, not a write:

```
🔄 Adoption recheck · <project> · <N>d since adoption

   New work not on the board   : 4  (commit scopes: viewer, schema)
   Board rows with no activity : 2  (TASK-014 idle 23d, no commits touch its paths)
   New docs not digested       : 1  (doc/rendering-pipeline.md)
   Previously rejected, unchanged: 9 (not re-proposed)
```

Each line routes to an existing subcommand. Recheck never writes state itself.

## Clustering

Cluster-batch triage is what makes stage 3 survivable: a real project yields
40–60 candidates, and per-item confirmation loses the user around item 15. But it
makes cluster *quality* load-bearing, so the method is declared rather than
improvised.

**Seed from four signals that already exist in most repos, in this order:**

1. **The roadmap file's own headings** — a project that keeps a `TODOS.md` /
   `ROADMAP.md` has usually already grouped its own work, and those groups beat
   anything Perry would derive. Free, authored by the user, and semantic.
2. **Conventional-commit scopes** — `feat(okr):`, `fix(viewer):`. Only useful when
   the project actually uses them consistently; measure before relying on it (on
   the first real adoption test, 11 of 113 commits carried a scope, spread across
   6 scopes — useless as a seed).
3. **Module / directory boundaries** — candidates whose evidence paths share a
   top-level module.
4. **Issue labels / milestone names** — where a tracker exists.

**Rules:**

- **Cap at 8 clusters.** More than 8 and the user is doing per-item triage with
  extra steps; force a merge pass first.
- **A cluster is named after the work, not the source.** "webhook reliability",
  not "TODOs in src/api".
- **Show one candidate in full per cluster** — the user is accepting a group, so
  they need to see a concrete member to judge what the group means.
- **`low` confidence candidates are listed but never accepted by a group accept.**
  They require an explicit pick. A bulk accept must not smuggle in Perry's weakest
  guesses.
- Candidates that fit no cluster go to `cluster: misc` and are triaged per-item.

Rendering: one `AskUserQuestion` per cluster (header = cluster name, options =
`Accept all (N) | Review one by one | Reject all | Defer`). Drill-in follows the
`digest` verification pattern — batched ≤ 4.

## Attribution — the cluster → KR pass

Adopted tasks hit a chicken-and-egg: `reference/okr-linkage.md` is a hard gate
requiring every task to resolve to a KR, but the OKR does not exist until the
user authors it mid-adoption.

Resolving each task individually means 40 decisions. Letting them all land
`unlinked` means a freshly adopted project opens with a permanent `🔗 Unlinked`
warning — exactly the "un-triaged backlog reported as drift on day one" failure
that `schema/README.md § The linkage contract` calls out.

**So attribution is done per cluster.** After the OKR and phase are confirmed,
render the accepted clusters against the phase KRs (`AskUserQuestion`, header =
cluster name, options = candidate KR ids + "none of these → unlinked"). Every task
in the cluster inherits the edge; the edges are handed to `/okr link`, which owns
`phase/<NNN>-linkage.md`.

This is ~6 decisions instead of ~40, and every edge is still **declared by the
user**. It is not a relaxation of the gate — it is the same gate at cluster
granularity.

Two things it does not do:

- **It does not fuzzy-match a cluster to a KR by name.** The user picks, always.
- **It does not force a fit.** "None of these → unlinked" is a first-class answer,
  and a task the user overrides out of its cluster's KR gets its own edge.

## Rejections are memory

A rejected candidate stays in the dossier as `status: rejected`, with its
evidence. It is **not** deleted.

Without this, `--recheck` re-proposes the same 12 dead TODO comments every quarter
and the feature trains the user to ignore it. The dossier is the project's
"don't ask me again" record, and that is a large part of its long-term value.

`status: deferred` is the distinct case: ask again next recheck.

## One dossier per run

Dossier paths are dated (`.perry/adoption/<YYYY-MM-DD>-dossier.md`), so a run
resumed on a later day must **not** open a new file. Resume writes the existing
dossier: `updated:` moves, `started:` does not. `--recheck` and "start over" are
the only things that create a second one, and "start over" archives the first to
`.perry/adoption/archive/` rather than leaving two live files under the same glob.

If more than one non-terminal dossier somehow exists, the entry gate lists them
and asks; it never picks by date. Two live dossiers means two different answers
to "what did the user already decide", and guessing between them is exactly the
class of inference this pipeline forbids.

## Merge mode (re-adoption)

If Perry state already exists (a partially adopted project, or one adopted at
`--depth=quick` being deepened), adoption runs in **merge mode**:

- Candidates that appear to duplicate existing state are surfaced as **possible
  duplicates for the user to resolve** — never auto-dropped.
- Auto-dedupe would be a fuzzy name match deciding what is already tracked. That
  is the same class of guess `reference/okr-linkage.md` forbids, and it fails in
  the worse direction: silently dropping real work.
- Existing state is never overwritten. Adoption only adds.

## Post-adoption report

The first standup after adoption is a special case — the user needs to see what
just entered their project and, more importantly, what Perry is *unsure* about:

```
🅿  Adoption complete · <project> · <N> candidates → <M> accepted

   ✅ Declared by you    : 3 Objectives, 9 KRs, phase #001 <slug>
   📋 Adopted to board   : 22 tasks in 6 clusters
   📐 Transcribed        : 2 designs, 1 ADR, 4 digests
   🔗 Unlinked           : 3 tasks (no KR fit — surfaced, not guessed)
   ❌ Rejected           : 14 (kept in the dossier; not re-proposed)
   ⚠  Not adopted        : issue tracker (linked, not mirrored — see specs)
```

Then hand off to the normal standup.

## What adoption never does

- **Never writes a state file directly.** Everything goes through the owning skill.
- **Never infers an Objective or KR.** Strawman only; the user authors.
- **Never invents an ADR or a design doc** for a decision nobody recorded.
- **Never backfills the journal.** `journal/` starts at the adoption date. One
  pre-adoption summary and a `PROJECT_STATE.md` history section is the whole of
  it. Synthesizing dated entries for days Perry was not present fabricates an
  audit trail, and git history is already the archival record.
- **Never mirrors an external issue tracker.** The tracker stays authoritative for
  its own issues; an adopted task references it (`gh#412`) in its
  `evidence/<YYYY-MM>/<TASK-ID>-spec.md`. Two sources of truth means a board that
  rots within a month.
- **Never fuzzy-matches** — not for attribution, not for dedupe.
- **Never re-asks a question the user already answered.** A banked declaration is
  re-rendered for confirmation, never discarded and re-put.
- **Never resumes without being asked to.** Detection is automatic; continuation
  is the user's call, every time.
- **Never completes without `perry-lint` passing.**

## See also

- [adoption-sources.md](adoption-sources.md) — the source catalog: detectors, trust
  tiers, what each source may emit, and the depth matrix. Non-code projects are
  handled here, not in this file.
- [okr-linkage.md](okr-linkage.md) — the attribution gate the cluster→KR pass
  implements.
- [input-quality.md](input-quality.md) — runs unchanged on the strawman OKR.
- [../schema/state-schema.json](../schema/state-schema.json) — the dossier
  contract (`adoption: 1`).
- [../pmo/reference/bootstrap.md](../pmo/reference/bootstrap.md) — the greenfield
  path adoption replaces for existing projects.
