# The router's own subcommands — `adopt`, `relocate`, `diagnose`, `help`

Tier 1. Loaded on demand from `SKILL.md § Router subcommands`. These four are
handled in the router rather than in a lane, so the router carries the dispatch
line and the governing rule for each, and the procedures live here.

Extracted from `SKILL.md` on 2026-08-18 (TASK-064) to keep the tier-0
router inside its byte budget. The prose is carried over unchanged.

## `/perry adopt` — converting an existing project

For a project that already exists — code, docs, git history, an issue tracker — the blank-slate `init` chain above throws away the answers the project already contains. `/perry adopt` reads them instead.

```
/perry adopt [--depth=quick|standard|deep] [--only=okr,board,design,knowledge,arch] [--resume] [--recheck]
```

**Read `reference/adoption.md` before running it.** The one rule that governs the whole pipeline: **evidence proposes, the user declares.** Adoption writes exactly one file of its own — `.perry/adoption/<YYYY-MM-DD>-dossier.md` — and everything that reaches `OKR.md` / `BOARD.md` / `design/` gets there through the normal subcommands after the user accepted it. File ownership is unchanged: adoption is an orchestrator, not a fourth writer.

Five stages, each resumable: **scan** (read-only report) → **harvest** (cited evidence) → **infer** (candidates, clustered) → **confirm** (goals authored by the user from a strawman; tasks triaged by cluster; designs/ADRs transcribed only where a source doc exists) → **commit** (materialize, then `perry-lint` must pass). `--recheck` re-runs the harvest against an adopted project and reports drift — work that landed in the repo but never on the board.

Sources, trust tiers, and the depth matrix (including non-code projects) are in `reference/adoption-sources.md`.

## `/perry relocate <path>` — moving Perry's state root

```
/perry relocate <path>          # e.g. /perry relocate perry
/perry relocate . --dry-run     # show the moves, touch nothing
```

Moves every path Perry claims under a new state root and rewrites
`State root:` in `.perry/config.md`. `.perry/` itself never moves — it holds
the pointer, so it cannot sit behind it.

This exists because the state root is chosen **once**, at setup, and projects
grow. A project adopted at `.` that later adds its own `design/proposal.md`
gets `NS-01` (`reference/diagnose.md § Finding catalog`), and relocation is one
of its only two remedies — the other being moving your own file. There is no
per-path opt-out by design, so doing this by hand across fifteen paths is where
someone loses a journal directory.

**Procedure:**

1. **Refuse on a dirty tree.** Same discipline as `diagnose` requiring a restore
   point: `git status --porcelain` must be empty, or stop and say so. Not a git
   repo → copy the tree to `.perry/relocate-<YYYY-MM-DD>-backup/` first.
2. **Compute the moves** from `schema/state-schema.json § claims[]`, never from
   a hand-written list — that is what drifted before. Skip `anchor: project`.
3. **Check the destination is free**:
   ```
   python3 "$PERRY_HOME/bin/perry-lint" --claims --root . --state-root <path>
   ```
   A destination with collisions of its own is refused, not merged into.
4. **Show every move `from → to` and confirm** (`AskUserQuestion`, header
   `"Relocate"`, options: `Move <n> paths | Show the full list first | Cancel`).
   Never move a user's files without the list in front of them.
5. **`git mv` each existing path** (plain `mv` outside git). Paths that do not
   exist are skipped silently — a project without `runbook/` is not an error.
6. **Rewrite `State root:`** in `.perry/config.md`, adding a short `## Why the
   state root is not \`.\`` block naming what collided.
7. **Verify**: `perry-lint --root .` must pass, and `perry-lint --claims` must
   report zero collisions. If either fails, print the `from → to` list so the
   move is reversible by hand, and stop.

`--dry-run` stops after step 4 and writes nothing.

**What it never does.** It never moves a file it did not put there — only paths
Perry claims, and within them only files Perry wrote. It never deletes. It never
relocates *into* a directory that already collides. And it never runs on a dirty
tree, because the `git mv` set is the only thing making it reversible.

## `/perry diagnose` — auditing how a project works with agents

`adopt` converts a project **into** Perry. `diagnose` asks the prior question: **is this project's working structure sound at all?** It runs on any folder, including one that has never heard of Perry, and the right answer is often "leave it alone" or "you need three files" rather than "adopt Perry".

```
/perry diagnose [--depth=quick|standard|deep] [--only=<lanes>] [--dry-run] [--resume] [--recheck]
```

**Read `reference/diagnose.md` before running it.** The governing rule: **every prescription traces to a finding, and every finding traces to a measurement or an answer the user gave.** Nothing may be prescribed because Perry prefers it — diagnosis is inherently judgmental, and without that gate this subcommand becomes a machine that converts every project into a heavier project. It writes exactly one file of its own — `.perry/diagnose/<YYYY-MM-DD>-diagnosis.md` — and changes to Perry state still go through the owning child skill.

Six stages: **scan** (`bin/perry-diagnose`, deterministic and read-only) → **read** (what a script can't measure — the gap between what the docs say and what `git log` shows) → **interview** (≤6 outcome-framed questions; the user's answers override the scan) → **prescribe** (the smallest change set, hard-capped by the user's stated maintenance tolerance) → **execute** (gated per item, restore point first, moves and never deletes) → **recheck** (drift, with declined items remembered rather than re-proposed).

It targets the three ways agent projects actually fail — concurrent sessions interfering, documents growing past the budget where they stop being obeyed, and goals drifting with no runnable check to say what is done. The research behind each, the isolation ladder, and the three archetypes are in `reference/project-archetypes.md`; runnable scaffolds are in `templates/`.

Two outcomes are first-class and must stay available: **zero findings**, and a prescription of pure **subtraction**. A diagnostic that has to find something to justify the run is one the user stops reading by the third invocation.

## `/perry help [<lane>]`

Without arg: print a compact overview of the three lanes + when to use each + a pointer to each lane's own `help`. This is the navigation entry point for users who don't know what's available yet.

Suggested format:

```
Perry — virtual project office. One command: /perry

  /perry    Combined snapshot across all three lanes.
            Use when: starting a fresh session, one-stop "where are we",
            or you don't know which lane you want. This is the default —
            you can always just type /perry.
            Common: /perry, /perry help

  /perry goals <sub>     Goal-setting (alias: /perry okr) (overall + current phase OKR + weekly proposals)
            Use when: setting goals, planning a phase, scoring KRs,
            pivoting strategy.
            Common: init, plan-phase, plan-week, score-phase, snapshot, dashboard
            Full list: /perry help goals

  /perry work <sub>      Execution stewardship (alias: /perry pmo) (BOARD, journal, dispatch, cadence)
            Use when: standup, planning the week, delegating to agents,
            tracking blockers, writing weekly status, phase rollover.
            Common: triage, plan-week, dispatch, review, friday-review, handoff
            Full list: /perry help work

  /perry decide <sub>    Design-doc / RFC / decision stewardship (alias: /perry design) (locked decisions before building)
            Use when: drafting an RFC, locking user decisions, handing off
            implementation tasks to PMO.
            Common: new, resolve, lock, adr, handoff
            Full list: /perry help decide

  The lane name is optional when the subcommand is unambiguous —
  /perry plan-phase and /perry goals plan-phase are the same thing.

  /perry adopt   Convert an EXISTING project into Perry state.
            Use when: the project already has code, docs, git history, or a
            tracker, and starting from a blank OKR would throw that away.
            Evidence proposes; you declare. Nothing is written until you accept.
            Common: /perry adopt, --depth=quick, --recheck

  /perry diagnose  Audit how a project works with agents, then refactor it.
            Use when: sessions keep interfering, the md files have become a
            jungle nobody can navigate, or there's no way to say what's done.
            Works on ANY folder — Perry not required, and "your structure is
            fine" is a valid result. Measures, interviews, prescribes the
            smallest fix, then executes it with your approval per item.
            Common: /perry diagnose, --dry-run, --recheck

First-time setup: /perry in a new project → confirms language + repo layout,
then asks new-vs-existing and routes to /perry adopt for existing projects.
Read more: $PERRY_HOME/README.md
```

With arg `goals`, `work` or `decide` (or their aliases `okr`, `pmo`, `design`): read that lane's SKILL.md and render its `help` subcommand (the lane owns the detail). Don't re-render their tables here.

`help` does NOT trigger the combined snapshot ritual.
