# Pack · `software-ops`

> The first pack, and the one that tested whether packs are a real abstraction.
> DESIGN-003 § 5.6, § 4 decision 7. Bundled with Perry and active by default —
> nothing about the out-of-the-box experience changes for an existing user.

A **pack** supplies a domain's defaults, never its content: mode defaults, stage
vocabulary, artifact templates, acceptance rubrics, the high-stakes list, and a
display glossary. Perry supplies the office; a pack supplies the practice.

## What this pack supplies

| | |
|---|---|
| **Default mode** | `project` |
| **Applies when** | The track produces software — a codebase, a service, an installed tool |
| **Procedures** | `architecture.md`, `runbooks.md`, `incidents.md` |
| **Subcommands** | `architecture init / review / diff`, `architecture-audit`, `runbook-check`, `incident <slug> / close / list / archive` |
| **State it introduces** | `ARCHITECTURE.md`, `architecture/audit-history/`, `runbook/`, `incidents/` — all lazily created, none claimed unless used |
| **Gates it adds** | `close-task` gate 1 (`Touches architecture:` → review agent PASS), gate 2 (`Deployed: yes` → runbook exists) |
| **Default rungs** | Inherits `project` mode's V3. Anything `Deployed: yes` is outward-facing and takes V5 by the consequence rule |

## Glossary

The nouns Perry renders for a project running this pack. Everything not listed
keeps its default name.

| Term | Shown as |
|---|---|
| Board | Board |
| Phase | Phase |
| Commitment | Key result |

Deliberately almost empty, and that is the honest result. `software-ops` is the
domain Perry's default vocabulary was **built from**, so there is nothing to
translate — the three rows above are identities, kept to show the shape a real
pack fills in. A content pack would map `Board → Calendar`, `Phase → Cycle`,
`Item → Piece`; a legal pack would map `Board → Matters`, `Phase → Stage`,
`Task → Task` and leave `Commitment` alone. The value of the glossary is
entirely for the packs Perry does not ship.

**What a glossary may never rename**: a file name, an ID, an enum value, a
schema column key, a heading the schema matches on, or a command. Those are the
machine contract — the same line `reference/i18n.md` draws between the document
language and the tokens every parser keys on. A pack that could move them would
break every reader; the loader does not look at them at all.

## Deactivating it

A project whose tracks are all `pipeline`, `queue` or `inquiry` has no use for
any of the above. Deactivating the pack removes the three procedures from the
lane index and the two `close-task` gates with them; nothing else in Perry
depends on it. A knowledge base does not need to know what an architecture audit
is, and before this extraction it carried all three files' names in the PMO lane
index regardless.

## What the extraction found

The honest record, because DESIGN-003 § 7 made this task the test of whether the
pack abstraction survives contact with real material. It did — with two
corrections that the design did not anticipate.

**1 · `$PERRY_HOME/work/reference/git-boundaries.md` is not software-ops, and was left in core.**
TASK-024's deliverable named four files. Only three moved. `$PERRY_HOME/work/reference/git-boundaries.md`
declares which *role* may commit, push, open a PR and merge — Coding Agent
commits its own work on a feature branch, PMO Agent never commits code, nobody
merges their own PR. None of that is about software: a research vault, a content
pipeline or an ops runbook repo kept in git needs exactly the same role
boundaries, and a knowledge base with two sessions writing to it needs them
more. Moving the file would have made git etiquette conditional on a software
pack being installed, which is a worse answer than leaving a 39-line file in
core. **It stays in `work/reference/git-boundaries.md`.**

**2 · The goals lane had a hard gate keyed on `ARCHITECTURE.md`.**
`goals/reference/phases.md` refused to write a phase file until every unresolved
architecture-audit drift item had a response. That is a software-ops rule living
in the *goals* lane, where it had no business being — a content pipeline has no
architecture and no audit history, so the gate could never fire there and simply
sat in the procedure as software's assumptions in the goals lane's clothes.
Now conditional on the pack. The gate is unchanged where it applies.

**Verdict: the pack abstraction holds.** The three files moved with path
rewrites only — no content edits — which was DESIGN-003 § 7's stated pass
condition. The two corrections above are not failures of the abstraction; they
are exactly what an extraction is supposed to expose, and neither was visible
while the material sat in the core lane. That is the argument for doing the rest
of the packs.

## See also

- `perry/design/DESIGN-003-work-modes.md § 5.6` — the pack contract.
- `modes/project.md` — the mode this pack defaults to.
- `work/reference/git-boundaries.md` — deliberately *not* in this pack; see above.
