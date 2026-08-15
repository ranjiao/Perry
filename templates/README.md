# `templates/` — archetype scaffolds

Runnable starting points for the three archetypes in
[`reference/project-archetypes.md`](../reference/project-archetypes.md). The
prescribe and execute stages of `/perry diagnose` copy from here.

| Archetype | Directory | Native verification? |
|---|---|---|
| Software / product development | [`software/`](software/) | Yes — tests, build, lint |
| Personal knowledge base | [`knowledge-base/`](knowledge-base/) | No — `bin/kb-lint` constructs one |
| Ops / content / team-process | [`ops/`](ops/) | No — `bin/deliverable-lint` + a human gate |

## How to use them

**By hand:** copy the archetype directory's contents into your project root,
then edit every `{{placeholder}}`. Nothing here depends on Perry being
installed — that is the point. Each scaffold stands alone.

**Through diagnose:** `/perry diagnose` proposes individual files from these
scaffolds as prescription items, one per finding it closes. It never copies a
whole directory over an existing project, because a scaffold that overwrites a
user's own `AGENTS.md` destroys the content the refactor was supposed to
preserve.

## The rules the scaffolds encode

Three things are deliberate in all three, and they are the parts worth keeping
if you change everything else:

1. **The tier-0 file stays under ~60 lines.** Every scaffold's `AGENTS.md` is
   short enough to read in one screen. A rules file that outgrows the budget
   stops being obeyed rather than failing loudly, so the scaffolds practice
   what the research prescribes.
2. **There is exactly one runnable check**, and it is one command. Software
   projects inherit theirs; the other two ship a linter, because "construct a
   verification loop" is hand-waving unless something concrete comes with it.
3. **Every shared surface is append-only.** The log, the journal, the decision
   record. This is what lets a second session start without waiting for the
   first, and it needs no worktrees, no locks, and no tooling.

## `AGENTS.md` vs `CLAUDE.md`

The scaffolds ship `AGENTS.md` because more hosts read it. For Claude Code,
symlink rather than copy — two rule files drift apart and the agent obeys
whichever it happened to read:

```bash
ln -s AGENTS.md CLAUDE.md
```
