# Adoption sources — the harvest catalog

Loaded with `reference/adoption.md` during `/perry adopt` stages 0–1 (scan and
harvest). This file is the **catalog of what adoption may read, how much to trust
it, and what it may emit**. Keeping it separate from the procedure is what lets a
non-code project be adopted without touching the pipeline: a research project
harvests a doc folder where a code project harvests git, and stages 2–5 are
identical.

## Trust tiers

Every source declares a tier. The tier caps the confidence any candidate derived
from it may carry.

| Tier | Kind of source | Max confidence | Why |
|---|---|---|---|
| **A** | **Declarative** — someone wrote it down on purpose for a reader | `high` | A roadmap bullet is a statement of intent. It can be stale, but it is not a guess. |
| **B** | **Behavioral** — a record of what happened | `medium` | A commit tells you work occurred; it does not tell you whether it was wanted, finished, or worth continuing. |
| **C** | **Structural** — the shape of the artifact itself | `low` | A directory layout is evidence of nothing but a directory layout. Useful for clustering, weak for candidates. |

A candidate whose evidence spans tiers takes the **highest** tier present, but
only if the tier-A source states the thing outright. Convergence across three
tier-C signals is still `medium` at best.

## The catalog

### Tier A — declarative

| Source | Detector | Reads | May emit |
|---|---|---|---|
| `readme` | `README*` at root | Purpose, status, roadmap sections, "not yet implemented" | `objective` (strawman), `task`, `knowledge` |
| `roadmap` | `ROADMAP*`, `TODOS*`, `PLAN*`, `docs/roadmap*` | Unchecked boxes, milestone lists, dated sections | `task`, `phase`, `kr` (strawman) |
| `adr` | `decisions/`, `adr/`, `docs/adr/`, `*ADR-*.md` | Existing decision records | `decision` (transcribe) |
| `design` | `design/`, `rfc/`, `docs/design/`, `*RFC*.md` | Existing design docs | `design` (transcribe) |
| `changelog` | `CHANGELOG*` | Release arc, feature themes, dates | `phase` (history), `knowledge` |
| `agent_md` | `CLAUDE.md`, `AGENTS.md`, `.cursorrules` | Declared conventions, constraints, invariants | `decision`, `knowledge`, `arch` |
| `docs_tree` | `doc/`, `docs/`, `wiki/` | Everything else written for humans | `knowledge`, `design`, `arch` |
| `manifest` | `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod` | Name, description, scripts, deps | project metadata, `arch` |

**Note on `roadmap`**: an unchecked box is the single highest-yield adoption
signal in existence — it is a task the user already wrote, already scoped, and
already declined to finish. Treat it as `high` confidence and expect most of the
board to come from here when the file exists.

### Tier B — behavioral

| Source | Detector | Reads | May emit |
|---|---|---|---|
| `git_recent` | `.git/` | Commits in the depth window, grouped by scope/path | `phase` (what is being worked on **now**), `cluster` seeds |
| `git_arc` | `.git/` + tags | Tags, release cadence, long-run themes | `phase` (history), `knowledge` |
| `git_branches` | `git branch -a` | Stale/unmerged branches | `task` (unfinished work) |
| `issues` | `gh` CLI authenticated, or a tracker in the hook | Open issue titles, labels, milestones | `task` (**linked, never mirrored**), `cluster` seeds |
| `prs` | `gh` CLI | Open + recently closed PRs | `task`, `decision` (rationale in PR bodies) |

**`git_recent` is the strongest inference adoption makes.** "What has this repo
been doing for the last N days" is a fair statement of the current phase. It is
still proposed, never written.

**`issues` is link-only.** It may emit a task candidate carrying `ext: gh#412`,
which lands in the task's `evidence/<YYYY-MM>/<TASK-ID>-spec.md`. It may never
copy the issue body into Perry as though Perry now owned it.

### Tier C — structural

| Source | Detector | Reads | May emit |
|---|---|---|---|
| `modules` | directory walk | Top-level module map, sizes | `arch` (skeleton), `cluster` seeds |
| `markers` | grep | `TODO`, `FIXME`, `HACK`, `XXX` with surrounding context | `task` (`low` unless corroborated) |
| `tests` | test dir / runner config | Presence, coverage shape, skipped tests | `task`, `risk` |
| `deps` | lockfiles | Pinned-old, deprecated, security-flagged deps | `risk` |

**`markers` needs a corroboration rule.** A bare `# TODO: fix this` from four
years ago is noise, and adopting it wastes the user's triage budget on candidates
they will reject. Emit at `low` unless the marker is corroborated by a tier A/B
source (named in the roadmap, touched by a recent commit, referenced by an
issue) — in which case promote to `medium`.

**`markers` is a fallback, not a primary source.** A project disciplined enough to
be worth adopting usually keeps its TODOs in a roadmap file rather than in code
comments — the first real adoption test found **zero** markers across 62 modules
while `TODOS.md` carried 18 tasks. Expect this source to earn its keep only on
repos with no roadmap at all.

## Depth matrix

Depth controls which sources run, and the window on the windowed ones.

| Source | `quick` | `standard` (default) | `deep` |
|---|---|---|---|
| `readme`, `manifest`, `agent_md` | ✅ | ✅ | ✅ |
| `roadmap` | ✅ | ✅ | ✅ |
| `adr`, `design` | — | ✅ | ✅ |
| `changelog` | — | ✅ | ✅ |
| `docs_tree` | — | ✅ (headings + first ¶) | ✅ (full read) |
| `git_recent` | 30d | 6mo | 6mo |
| `git_arc` | — | tags only | tags + release notes |
| `git_branches` | — | ✅ | ✅ |
| `issues` | — | titles + labels | titles + bodies |
| `prs` | — | — | ✅ |
| `modules` | top level | ✅ | ✅ + per-module pass |
| `markers` | ✅ | ✅ | ✅ |
| `tests`, `deps` | — | — | ✅ |

`quick` exists for "just get me a board by lunch" and is honest about it: it
cannot produce an architecture skeleton or transcribe designs. `deep` is for a
project the user intends to run through Perry for a long time.

## Scale limits (do not read a repo linearly)

A five-year repo has thousands of commits and adoption must not attempt to read
them. Hard limits, regardless of depth:

- **Commits are read as aggregates, never individually.** Group by scope/path/week
  and read the *shape*: which areas are hot, which are dormant. Individual SHAs
  are cited as evidence, not narrated.
- **Cap the harvest at ~200 evidence records.** Past that, the triage cost exceeds
  the value of adoption; tighten the depth or the `--only` lanes instead.
- **Cap `docs_tree` at 40 files** at `standard`. Prefer headings over bodies.
- **Never read `node_modules/`, `vendor/`, build output, or lockfile contents**
  beyond dependency names.

If a project exceeds these, say so in the scan and let the user narrow the scope.
Silently truncating would report partial coverage as complete — the same failure
mode as a half-parsed linkage graph.

## Non-code projects

Perry supports research, ops, and business projects, which have no git scope
convention and often no git at all. Those swap the source set; the pipeline does
not change.

| Source | Detector | Reads | May emit |
|---|---|---|---|
| `doc_folder` | a directory of `.md` / `.docx` / `.pdf` | Titles, headings, dates | `knowledge`, `task`, `objective` (strawman) |
| `fs_timeline` | file mtimes | What was worked on when, in the absence of git | `phase`, `cluster` seeds |
| `meeting_notes` | `notes/`, `meetings/`, dated filenames | Decisions, action items | `decision` (transcribe), `task` |
| `spreadsheet` | `.xlsx` / `.csv` trackers | Row-per-task trackers | `task` |

For these, clustering seeds come from `fs_timeline` and folder structure rather
than commit scopes, and `git_*` sources are simply absent from the scan output.

## Provenance format

Every evidence record cites its source in a form that can be re-opened:

| Source kind | Citation form | Example |
|---|---|---|
| file | `<path>#L<start>-<end>` | `TODOS.md#L40-52` |
| git commit | `git:<short-sha>` | `git:5f1941f` |
| git aggregate | `git:<scope>@<window>` | `git:parsers@30d` |
| issue / PR | `<tracker>#<id>` | `gh#412` |
| filesystem | `fs:<path>@<mtime>` | `fs:notes/q3.md@2026-07-02` |

An evidence record that cannot produce one of these is dropped. "The repo feels
like it's about X" is not a citation.

## Adding a source

Sources are additive. To add one:

1. Add a row to the right tier table above: detector, what it reads, what it may
   emit. **A source may never emit a candidate kind above its tier's confidence
   cap.**
2. Add a column entry to the depth matrix — a new source defaults to `deep` until
   its cost is understood.
3. Declare its citation form in § Provenance format.
4. Add a fixture case under `tests/fixtures/pre-adoption-project/` so the scan
   output is tested rather than asserted.

No change to `reference/adoption.md` should be needed. If one is, the pipeline is
leaking source-specific logic and that is the bug.
