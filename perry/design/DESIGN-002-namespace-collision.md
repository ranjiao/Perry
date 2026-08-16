# DESIGN-002: Namespace collision with the host project

> Status: locked
> Date: 2026-08-16 · Locked: 2026-08-16
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: —
> Supersedes: —   · Superseded by: —

## 1. Problem

Perry writes sixteen paths into a project it does not own — fifteen under the
state root, plus `.perry/` at the project root. `SKILL.md:16`
already names the principle — *"Claiming a common English word in a namespace
Perry doesn't own is the same error as claiming a project's `design/`
directory"* — and `State root:` in `.perry/config.md` is the escape hatch. The
mechanism is right. The wiring around it has four holes, and Perry's own repo
demonstrates the failure.

**P1 · First-time setup never asks. Only `adopt` does.**
`SKILL.md § First-time setup` step 2 asks Document language and Repo layout in
a single `AskUserQuestion`, then step 3 asks new-vs-existing. **State root is
not among them.** The instruction to ask exists only in the reference section
at `SKILL.md:224` ("**Ask the user** when the project already uses a directory
Perry claims") and in `reference/adoption.md:167`, which is the adopt path.

So a greenfield `/perry` → `/okr init` in a folder that already owns `design/`
writes Perry's files straight over the project's namespace, with no question
asked. The escape hatch is only offered on the one path where the user was
already going to be interviewed.

**P2 · The claim surface has no single source of truth, and every existing list is incomplete.**
Three lists exist. All three disagree, and the most authoritative is the least
complete:

| Source | Knows about |
|---|---|
| `schema/state-schema.json → files[]` | 13 paths: `BOARD.md`, `OKR.md`, `phase/`, `design/`, `DECISIONS.md`, `PROJECT_STATE.md`, `ARCHITECTURE.md`, `runbook/`, `.perry/*` |
| `SKILL.md:224` prose | 5: `OKR.md`, `BOARD.md`, `phase/`, `design/`, `journal/` |
| `reference/adoption.md:167` prose | 5: `design/`, `OKR.md`, `BOARD.md`, `phase/`, `journal/` |

Meanwhile `pmo/SKILL.md` and `okr/SKILL.md` state tables also write
`journal/`, `evidence/`, `weekly/`, `handoff/`, `decisions/`, `knowledge/`
and `inputs/` — **seven directories that appear in no collision check and in no
schema `files[]` entry.** The adopted aimark project contains all of them.

The consequence is precise: a project that owns `evidence/`, `weekly/`,
`knowledge/` or `inputs/` collides silently *even on the adopt path*, because
the check is prose enumerating a subset of a list that is itself missing them.

**P3 · Nothing computes the collision.**
`bin/` ships `perry-lint`, `perry-state`, `perry-diagnose`, `perry-explain`,
and five more. None answers "what would Perry claim in this folder, and what is
already taken?" The check is agent judgment against a hand-maintained prose
list — the exact shape that drifts, and has.

**P4 · The check runs once and never again.**
`schema/README.md:139` is explicit about the asymmetry: *"`bin/perry-lint` now
refuses to judge anything outside `.perry/` until the project is actually
adopted, but that only covers the before; the state root is what covers the
after."* That holds only if the state root was set correctly at the start. A
project adopted at `State root: .` that later adds its own `design/proposal.md`
now has lint reporting the user's file as a malformed Perry design doc — the
precise failure the state root exists to prevent, arriving by a route the state
root does not cover.

**Perry's own repo is the proof case.** Perry's `design/` directory holds the design
*lane skill* (`design/SKILL.md`, `design/state/design_TEMPLATE.md`). Perry
cannot adopt itself at root without claiming its own source tree. This document
is filed at `perry/design/DESIGN-002-*.md` for that reason.

## 2. Goals

1. **One authoritative list** of every path Perry claims, machine-readable,
   with no second copy in prose.
2. Collision is detected on **every** entry path — greenfield setup, adopt, and
   diagnose — not only on adopt.
3. A deterministic check the agent runs rather than a judgment it makes, so the
   answer is the same across sessions and hosts.
4. A collision that appears **after** setup is surfaced as a collision, not as
   malformed Perry state.
5. The user is asked at most **one** question about this, with the consequence
   of each option stated in terms they can evaluate.
6. Perry can adopt Perry.

## 3. Non-Goals

- **Not per-file remapping.** Ten `State root`-style pointers is a resolver
  nobody can reason about and two readers can disagree on. All-or-nothing stays
  — see decision #2 for the argument.
- **Not renaming Perry's files** to reduce collision odds (`PERRY_BOARD.md` and
  friends). The names are good and are what makes the state readable by a human
  who has never used Perry.
- **Not auto-relocating** on detection. Moving a user's files is out of scope
  in every direction; Perry moves its own or asks.
- **Not migrating existing projects.** A project already at `State root: .` and
  working stays working; this design changes what happens at setup and what
  gets reported afterward.
- **Not resolving the `.perry/` anchor.** It is at the project root by
  necessity (it holds the pointer) and a project owning `.perry/` is a case
  worth failing loudly on, not designing around.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Where the claim list lives | New `claims[]` in schema / Extend `files[]` / Separate manifest file | **New `claims[]` in schema** | 2026-08-16 |
| 2 | State root granularity | All-or-nothing, as today / Per-path remap / All-or-nothing + per-path opt-out | **All-or-nothing, as today** | 2026-08-16 |
| 3 | Default state root for new projects | Ask when collision detected / Always `perry/` / Always `.` | **Ask when collision detected** | 2026-08-16 |
| 4 | Post-setup collision behavior | Lint warns, names it a collision / Lint errors / Silent, as today | **Lint warns, names it a collision** | 2026-08-16 |
| 5 | How the check ships | Standalone `bin/perry-claims` / Fold into `perry-lint --claims` / Agent-side only | **Fold into `perry-lint --claims`** | 2026-08-16 |

All five resolved 2026-08-16. Rows 2 and 5 changed the design — see the
consequences recorded below.

Notes on the non-obvious ones:

- **#1** — the first draft argued that extending `files[]` would mean inventing
  per-file contracts for `journal/` and `evidence/`. **That was wrong.**
  `template` is optional (`config` carries none, and `bin/perry-lint:609` skips
  entries without one), `headings: []` with no `frontmatter` is legal and
  common, and `pmo/state/` already ships `journal_TEMPLATE.md`,
  `evidence_TEMPLATE.md`, `weekly_TEMPLATE.md`, `handoff_TEMPLATE.md`,
  `knowledge_INDEX_TEMPLATE.md` and `ADR_TEMPLATE.md`. Extending `files[]` is
  cheap.

  The reasons that survive are granularity and blast radius. `files[]` describes
  **files Perry validates**; a claim describes **territory Perry occupies**, and
  the two are not the same unit — Perry writes
  `journal/<YYYY-MM>/<YYYY-MM-DD>.md`, but the thing that collides with a user's
  folder is `journal/`, and no prefix of that glob is the claim. Folding the
  seven missing directories into `files[]` would also switch on lint validation
  of `evidence/`, `weekly/`, `handoff/`, `knowledge/`, `inputs/` and
  `decisions/` as a side effect of wanting a collision check.
- **#2** — per-path remap sounds friendlier (a project owning only `design/`
  moves one directory instead of ten) but multiplies the resolver's states from
  2 to 2^16, and `schema/README.md § Where the files are` rests on **"One
  resolver"** as a safety property. Uniform relocation keeps every reader's
  mental model to a single prefix. The cost — moving fifteen paths to dodge one
  collision — is paid once, at setup, by a machine.

  **Chosen strictly, without the per-path opt-out.** The `Ignore:` list that the
  third option would have added is therefore *not* part of this design; every
  reference to it below has been removed, and `NS-01` offers two remedies rather
  than three. A project that collides moves its state root or moves its file.
- **#3** — defaulting to `perry/` unconditionally eliminates the problem by
  construction and is genuinely tempting. It is rejected as the default because
  it makes the common case (an empty or greenfield folder, no collision) worse
  for every user in order to protect a minority, and it silently changes the
  layout every pre-existing Perry project assumes. Ask-on-collision keeps the
  clean case clean.

## 5. Architecture

### One list, generated everywhere it is used

Add `claims[]` to `schema/state-schema.json`, as a sibling of `files[]`:

```json
"claims": [
  { "path": "OKR.md",        "kind": "file", "owner": "okr",    "anchor": "state" },
  { "path": "design/",       "kind": "dir",  "owner": "design", "anchor": "state" },
  { "path": "journal/",      "kind": "dir",  "owner": "pmo",    "anchor": "state" },
  { "path": "evidence/",     "kind": "dir",  "owner": "pmo",    "anchor": "state" },
  { "path": "weekly/",       "kind": "dir",  "owner": "pmo",    "anchor": "state" },
  { "path": "handoff/",      "kind": "dir",  "owner": "pmo",    "anchor": "state" },
  { "path": "knowledge/",    "kind": "dir",  "owner": "pmo",    "anchor": "state" },
  { "path": "inputs/",       "kind": "dir",  "owner": "pmo",    "anchor": "state" },
  { "path": "decisions/",    "kind": "dir",  "owner": "pmo",    "anchor": "state" },
  { "path": ".perry/",       "kind": "dir",  "owner": "perry",  "anchor": "project" }
]
```

— and the rest, covering all twenty. Every `files[]` entry's path must appear
in or beneath a `claims[]` entry; a test asserts this, so adding a state file
without declaring its claim fails CI.

**Both prose lists are then deleted, not updated.** `SKILL.md:224` and
`reference/adoption.md:167` stop enumerating paths and point at the manifest
instead. A hand-maintained second copy is what produced P2, and updating it
reproduces the defect on a delay.

### `perry-lint --claims` — the deterministic check

```
python3 "$PERRY_HOME/bin/perry-lint" --claims --root . [--state-root <path>] [--json]
```

A third mode alongside the existing `--templates`, not a new binary. This fits
the tool as built: `--templates` already lints Perry's own
`state/*_TEMPLATE.md` and never touches a project root at all, so `perry-lint`
is already a multi-mode tool whose modes have different scopes and different
gates. `--claims` is the third such mode, and it is explicitly **not** subject
to the `is_adopted()` guard at `bin/perry-lint:631` — a collision check that
only ran on adopted projects would answer the question after the moment it
mattered.

Stdlib-only, read-only, exit 0 always — the same discipline as the default mode.
Reads `claims[]`, resolves against the candidate state root, and reports what
already exists and is not Perry's:

```
🚧 Namespace check · aimark · candidate state root: .

   Claimed by Perry : 16 paths
   Already present  : 1 collision, 2 benign

   ✗ design/          exists · 1 file, not Perry-shaped (design/global-search.md)
   · CHANGELOG.md     exists · not claimed by Perry
   · README.md        exists · not claimed by Perry

   Suggested state root: perry/   (0 collisions)
```

"Not Perry-shaped" is decided by the same parser `perry-lint` uses, so a
directory containing genuine Perry docs is a **re-adoption**, not a collision —
the two must not be conflated, and only a parse can tell them apart.

The output is a payload, not a decision. Every consumer below renders from it.

### Where the check runs

| Entry point | Behavior |
|---|---|
| `/perry` first-time setup | Run the check *before* step 2. If collisions > 0, add State root as a third question in the existing `AskUserQuestion` call — no extra round trip. If 0, write `State root: .` without asking. **This closes P1.** |
| `/perry adopt` stage 3 step 0 | Replace the prose check with the payload. The existing question and options are unchanged. |
| `/perry diagnose` | Report collisions as a finding rather than acting on them — diagnose does not adopt. New finding id below. |
| `perry-lint` default mode | On an adopted project, run the claim check as part of the normal lint pass and emit `NS-01` on drift. **This closes P4.** |

### The post-setup collision (P4)

Today a project adopted at `State root: .` that later grows its own
`design/proposal.md` gets that file reported as malformed Perry state. The fix
is a distinct finding rather than a parse failure:

```
NS-01  warn   A path Perry claims now holds files Perry did not write
              why it bites  Perry will read these as its own state and report
                            them as broken, and the next lint run will say your
                            file is malformed. It is not — it is in a folder
                            Perry claimed.
              what to do    Move Perry's state under `perry/` (one command,
                            reversible), or move your file out of the claimed
                            folder.
              evidence      design/proposal.md, design/rfc-2.md
```

`NS-01` joins the `bin/perry-diagnose` finding catalog in
`reference/diagnose.md`, whose test suite already fails on an id with no
catalog entry — so the catalog stays honest for free.

### Relocation

If the user picks a new state root on a project that already has state at the
old one, the move is mechanical: `git mv` each existing claimed path under the
new root, rewrite `State root:` in `.perry/config.md`, re-run `perry-lint`.
Worth a subcommand — `/perry relocate <path>` — because doing it by hand across
fifteen paths is where a user loses a journal directory. With decision #2 taken
strictly, relocation is the *only* remedy for a project that outgrows its state
root, which raises this from a convenience to a requirement.

Perry adopting Perry is then just this: `State root: perry`, because
`design/` is the lane skill.

## 6. Implementation plan

| Phase | Scope | Proposed PMO task(s) | Owner |
|---|---|---|---|
| A | `claims[]` in `schema/state-schema.json`, covering all sixteen. Test asserting every `files[]` path is covered by a claim. | TASK-010 | Coding Agent |
| B | `perry-lint --claims` — new mode, `--json` and `--text`, Perry-shaped detection reusing the parser already in the file. Exempt from the `is_adopted()` guard. | TASK-011 | Coding Agent |
| C | Wire into first-time setup (third question, conditional) and adoption stage 3 step 0. Delete both prose path lists. | TASK-012 | Coding Agent |
| D | `NS-01` finding: `bin/perry-diagnose` emitter + catalog row in `reference/diagnose.md` + `WHY` entry. | TASK-013 | Coding Agent |
| E | `/perry relocate <path>` subcommand. Perry's own repo is the test case. | TASK-014 | Coding Agent |

A–C are the minimum that closes P1–P3. D closes P4. E is what makes the escape
hatch usable after the fact — and with decision #2 taken strictly it is the only
remedy, so it is not optional polish.

## 7. Risks & mitigations

| Risk | Detection | Mitigation |
|---|---|---|
| `claims[]` drifts from what the skills actually write — the same defect one level up | A skill writes a path no claim covers | Test that walks `pmo/`, `okr/`, `design/` state tables and asserts every path appears in `claims[]`; fails CI |
| A third question at first-time setup makes onboarding heavier for everyone | User feedback; drop-off at setup | The question is **conditional** — asked only when the check finds a collision, which is the minority case. Zero collisions costs zero questions |
| With no per-path opt-out, a project that collides on one directory must relocate all fifteen paths or move its own file — some users will do neither and live with a permanent `NS-01` | `NS-01` warnings that persist across many lint runs | `NS-01` stays `warn`, never `error`, so a user can knowingly live with it; `relocate` (phase E) makes the real fix one command |
| Perry-shaped detection misfires and calls a re-adoption a collision, or vice versa | Fixture with a real Perry `design/` and a foreign one | Reuse the lint parser rather than a second heuristic; both cases get a test fixture |
| `relocate` loses files on a partial move | Post-move `perry-lint` | Use `git mv` and require a clean tree, as `diagnose` requires a restore point; refuse on a dirty tree rather than proceeding |

## 8. Open questions

- Should `claims[]` carry the seven undeclared directories only, or should
  `files[]` also gain real entries for `journal/` and `evidence/` so lint can
  validate their contents? That is a larger change and probably its own design.
- Is `NS-01` a diagnose finding, a lint finding, or both? Decision #4 puts it
  in lint; whether `bin/perry-diagnose` should also emit it is still open.
  Leaning both, with lint as the one that catches it early.
- ~~Should `--claims` be exempt from `--strict`?~~ **Resolved 2026-08-16: yes,
  exempt.** Decision #2 was taken strictly, so there is no per-path opt-out — a
  project that knowingly keeps one file in a claimed folder would otherwise have
  permanently red CI and no way to accept it. Same reasoning that keeps `NS-01`
  at `warn`. Callers branch on the `collisions` count in `--json` instead.

## 9. Changes (append-only after lock)

- 2026-08-16 — `--claims` exempted from `--strict` (§8 open question) —
  USER-002 answered. A collision never sets a non-zero exit.
- 2026-08-16 — `claims[]` shipped with **18** paths, not the sixteen this
  document counted. `tests/test_claims.py` caught `architecture/` and
  `incidents/` on its first run — both written by PMO, both missing from the
  count in §1. The drift guard found drift in the document that specified it.

## 10. References

- `SKILL.md:16` — the namespace principle this design enforces
- `SKILL.md:224` — `State root`, and the ask that first-time setup does not make
- `SKILL.md § First-time setup` — steps 2–3, where the question is missing
- `reference/adoption.md:167` — the adopt-path check and its 5-path prose list
- `schema/README.md § Where the files are` — the two safety rules, incl. "One
  resolver"
- `viewer/parsers.py § resolve_state_root` — the single resolver, and the
  "One resolver" property decision #2 protects
- `bin/perry-lint:609,631` — the optional-`template` skip and the `is_adopted()`
  guard `--claims` must sit outside of
- `reference/diagnose.md § Finding catalog` — where `NS-01` lands
- [DESIGN-001](DESIGN-001-resumable-pipelines.md) — the sibling entry-sequence
  change; both add a step before the pipeline starts
