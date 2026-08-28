# ADR-004 — Legacy projects migrate once, or stay read-only

> Status: active
> Type: Architecture
> Date: 2026-08-17
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

Runtime compatibility with the shapes real projects already use is where
Perry's defects live. Every blocking finding in the 2026-08-17 review round is
the same sentence: *works on the board Perry created, breaks on the board the
project already had.*

| Finding | What broke on a real project |
|---|---|
| TASK-019/020 B-3 | `route` cannot drain `## Intake` on a board whose table is four columns wide — so on `~/proj/gimegime-pmo`, intake fills and never empties |
| TASK-040 B-1 | `risk-add` on a `## Top risks` holding a severity legend bolts columns onto the legend and makes every existing risk invisible to every reader. Exit 0, no warning |
| TASK-040 B-2 | `risk-add` rewrote nine of that project's bullets into table rows with no consent and no message |
| TASK-021 finding 1 | `parse_due` scrapes a date out of a file path in a free-prose cell and reports a row reading `n/a` as 14 days overdue |
| M-8 (earlier) | `add` refused outright on a board with no `## P0`/`## P1`/`## P2` |

Each was fixed by adding a tolerance branch. The count of shapes is unbounded
and the branches interact: `viewer/parsers.py` now carries positional
fallbacks, bullet-versus-table fallback, four values of `risks.source`, three
separate bullet matchers, and prose-tolerant `Frequency` parsing. Two of the
review's findings are *disagreements between two of those branches* — the
reader and the writer answering "is this a risk table?" differently, and the
reader and the writer disagreeing about `###` sub-groups inside `## Cadence`.

So the tolerance is not merely expensive; past a certain density it is the
defect generator.

## Options

**A · Keep adapting at runtime.** Every new shape becomes a branch. Rejected:
the failure mode is not "we missed one", it is that two branches drift and
silently lose data, which is what B-1 does today.

**B · Refuse at runtime, adapt by hand.** Tools refuse unfamiliar shapes and
the agent edits the file. Rejected outright: an agent hand-editing a board is
precisely what Perry exists to remove. A hand edit writes no journal line and
no event, so the board and the log diverge, drift reconciliation reports it as
`unrecorded` forever, and a front-end sees a row appear from nowhere. This
would trade a data-loss bug for a data-provenance bug.

**C · Migrate once, then own the shape.** A project adopts Perry's structure in
a single explicit operation. After that, both the reader and the writer may
assume Perry's shape. **Chosen.**

## Chosen

**C.** A project must migrate to Perry's structure to use Perry's write
features. A project that cannot or will not migrate stays **readable** but not
drivable.

This is a deliberate loss of users in exchange for a large reduction in
permanent complexity, and the exchange is only honest if the migration is good.
The work does not disappear — it moves from every tool, forever, into one
pipeline that runs once.

### Where tolerance lives now

| | Before | After |
|---|---|---|
| `/perry adopt`, `/perry diagnose` | tolerant | **tolerant, and more so** — they must read any shape to propose a migration |
| `perry-state`, `perry-task`, `perry-goals`, `perry-decide`, `perry-lint` | tolerant | **strict**, against Perry's declared shape |
| Reading an unmigrated project | tolerant | tolerant enough to *report* and to drive adoption; no writes |

Reading stays deterministic in both cases. That is not negotiable: a front-end
querying state is the reason DESIGN-005 exists, and "the agent interprets it at
runtime" would leave nothing for `perry-task/list` to return.

### The mechanism this requires, which does not exist yet

`bin/perry-lint`'s `is_adopted()` answers *"does this folder contain any Perry
file at all"* — satisfied by a `BOARD.md` existing, whatever is inside it. That
is not the fact the tools now need.

A project must carry a **declared, checkable conformance marker**: this
project's state files match Perry's shape, at shape version N. Every writer
gates on it. Its absence is a refusal that names the migration, not a guess.

Version it from the start. The shape will change again, and a project migrated
under version 1 must be distinguishable from one migrated under version 2
without re-deriving it by inspection.

### What the migration must guarantee, or this decision is not safe to hold

A mandatory migration that mangles someone's board and cannot be undone is a
worse outcome than every bug listed in the Context.

1. **Dry run first, always.** The complete diff, before anything is written.
2. **Nothing is lost.** Row counts and every id present before are present
   after — asserted by the tool, not by the reader's eye.
3. **Recoverable.** Refuse on a dirty working tree, or write a restore point.
4. **The user declares.** `perry/OKR.md:37` — *"Adoption proposes; the user
   declares."* Mandatory migration means the tool may refuse without it; it
   never means the tool may perform it unasked. TASK-040 B-2 is exactly that
   violation and is not made legal by this ADR.
5. **Partial migration is a state, not a failure.** A project may migrate its
   board and not its risks. Conformance is therefore per-file, not per-project,
   and a writer gates on the file it is about to write.

## Consequences

**Immediately true**

- `~/proj/gimegime-pmo` — 41 tasks under `## Open — 投资线` and
  `## Open — 工程线 · phase #004` — is read-only until it migrates. That is the
  cost, in the concrete case, and it is accepted.
- The findings still open are re-scoped from *adapt* to *refuse and point at
  the migration*, which is strictly less work. The two fix agents in flight
  were already told to refuse rather than adapt, so their work stands.
- `parse_due` is **not** covered by this. It is a read-side defect, and its
  failure is a confidently wrong value, not an unhandled shape. A reader that
  cannot parse a cell must say so; one that invents an answer is wrong under
  every policy.

**Becomes possible**

- The tolerance branches in the steady-state tools become deletable, one at a
  time, each behind the conformance marker. This is not licence to delete them
  now: nothing may be removed before the marker exists and the migration can
  produce it.

**Open, deliberately not decided here**

- What happens to `perry-task add --group "<heading>"`. It exists so a project
  can keep its own section names while writes stay atomic. Under mandatory
  migration that is either withdrawn, or it becomes how a migrated project
  declares extra sections. Deciding it needs the marker's shape first.

## What would reopen this

- Migration proves unbuildable to the five guarantees above. Then the choice is
  between an unsafe mandatory migration and option A, and A is better than an
  unsafe one.
- A user population appears that cannot migrate and is not served by read-only.
  The cost accepted here is "some users"; if it turns out to be most, the trade
  was mispriced.
