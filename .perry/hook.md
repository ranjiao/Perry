# Perry hook — Perry

> **Tier 1** (user-read-and-edit). Owned by you, not by Perry.
> Hooks are **pure additions** to Perry's generic behavior — they never override a core rule.
> Read at every standup by `/perry`, and by every lane.

## High-stakes operations

> **This section is a safety gate, not documentation.** `/pmo dispatch` scans
> every spec's `Files in scope` / `Deliverable` against this list and refuses on
> a match; `/pmo autopilot` skips matching rows and refuses to run at all while
> the list is empty. Each backticked fragment is matched case-insensitively at
> **its own word edges** — `origin` matches `git push origin main` and does not
> match "original", `design/` still matches every path beneath it — so the
> backticked fragments are what does the work and the prose before them is for
> you.
>
> **A fragment matches the form you wrote, not its inflections.** `adopt` does
> not match "adopted" — that is the point — and by the same token `ln -s` does
> not match `ln -sf`. Where both forms matter, both are listed below. This used
> to be a bare substring test, and on 2026-08-20 it read `origin` out of "its
> original bytes" and `adopt` out of "on an adopted project" and stopped two
> dispatches that touched no remote and ran no adoption. A gate that cries wolf
> on ordinary English gets waved through; worse, the cheapest way to pass it was
> to reword the spec, which is the one thing a safety gate must never reward.
> TASK-107.

- Host skill installation — `setup`, `~/.claude/skills`, `~/.agents/skills`, `ln -s`, `ln -sf`, `ln -snf`, `ln -sfn`, repointing or removing an existing symlink
- System package installs — `brew install`, `npm install -g`, Homebrew bootstrap, Xcode CLT
- **Writing into a project Perry does not own** — `adopt` commit stage, `diagnose` execute stage, `relocate`, `git mv`
- **The claim surface** — `claims`, `state-schema.json`, anything that changes which paths Perry writes into someone else's project
- Publishing to a public repo — `git push`, `origin`, `gh release`, `publish`, `publishes`, `publishing`, `published`, tag creation
- Git history rewrites — `push --force`, `--force-with-lease`, `rebase` onto `main`, tag deletion
- Destructive filesystem operations — `rm -rf`, `rm -fr`, `rm -f`, bulk delete, overwriting a project's own `design/`, `evidence/`, `knowledge/`, `inputs/`
- Self-update — `git pull` inside `$PERRY_HOME`

**Why this list is not the template's default list.** Perry has no database, no
cloud infrastructure, no deployed service, no billing and no runtime, so
`terraform` / `k8s` / `iam` / `DROP TABLE` / `migrate --down` / paid-API lines
were dropped rather than carried as decoration — the template asks for exactly
that pruning, and an unpruned gate is one nobody rereads.

The two bolded rows have no analogue in any generic list and are Perry's actual
signature risk: **Perry's failure mode is writing files into a namespace it was
never given.** That is what `perry/design/DESIGN-002-namespace-collision.md`
exists to fix, and `origin` here is a public repo, so a bad `claims[]` edit
reaches other people's projects on the next `git pull`.

## Project specifics

If the project is **Perry**:
- Roadmap source-of-truth: `perry/BOARD.md` + `perry/design/` (locked designs are the plan of record)
- Prefer MCP tools: —
- Decision tag types: Process | Architecture | Tooling | Design
- Cost ceiling source: — (no `OKR.md`, no phase, so no ceiling to enforce)
- Special agents available: —
- Promotion / staging path: — (a skill repo; `main` is the only stage)

## Autopilot defaults

> Recognized by `work/reference/autopilot.md`.

```
Autopilot defaults:
- max_dispatches: 10
- max_duration_min: 120
- max_failures: 3
- excluded_tasks:
```

`excluded_tasks` is deliberately empty. The four DESIGN-003 tasks that must not
be automated (TASK-015, TASK-018, TASK-024, TASK-026) already carry
`Dispatch mode: manual` in their specs, which is the gate that actually holds —
listing them here too would create a second copy to keep in sync, and Perry's
own rule is one fact, one place.

## Configuration notes

> **Moved here from `.perry/config.md` on 2026-08-30 (TASK-233), verbatim.**
> That file is a projection of `.perry/config.jsonl` now: `perry-config render`
> rebuilds it from the store with no copy of it on disk, and what a store holds
> is settings and track rows — never prose. Prose in the projection survives a
> render only while a file is there to copy it out of, which is a guarantee
> that ends the first time the file is deleted or a project is cloned without
> it. This file is not rendered from anything, so it cannot lose them.
> `reference/config.md § Prose in this file is layout` is the general rule.

### What the two tracks carry

`intake` carries the work that ARRIVES — a defect an agent found mid-run, a
sibling a sweep turned up, a review finding. It is not decomposed from a goal,
it shows up, and its useful questions are queue questions: what has been
waiting longest, how deep is the backlog, what keeps recurring.

`main` carries the work that is DECOMPOSED — the phase, its KRs, the rows that
serve them.

Declared 2026-08-20 as the experiment in TASK-133. `Default rung` is V3 rather
than queue mode's V2 default: an arriving row here is a code defect, and a
resolution note is not evidence that it is fixed.

### Why the state root is not `.`

Perry's own `design/` directory is the **design lane skill**
(`decide/SKILL.md`, `decide/state/design_TEMPLATE.md`), not a folder of design
documents. Pointing the state root at the project root would make Perry claim
its own source tree, and every lint run would report `decide/SKILL.md` as a
malformed design doc.

`okr/` and `pmo/` are lane skills for the same reason. `.perry/` stays at the
project root: it holds this pointer, so it cannot sit behind it.

This is the collision described in `perry/design/DESIGN-002-namespace-collision.md`
— Perry is its own proof case, and this file is the escape hatch that document
argues should be offered automatically rather than written by hand.

See `schema/README.md § Where the files are`.
