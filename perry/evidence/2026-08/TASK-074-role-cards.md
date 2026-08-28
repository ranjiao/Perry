# TASK-074 — DESIGN-006 phase C: a role card is a hiring contract, never a workflow

> Source: `perry/design/DESIGN-006-roles-and-knowledge.md § 5.2`, § 6.1 phase C.
> Rung: **V3**. Every claim below is a run or a mutation.

## What shipped

- `schema/state-schema.json § files[id=role-card]` — `.perry/roles/*.md`, three
  header fields, and a **closed** section set.
- `work/state/role_card_TEMPLATE.md`.
- `packs/software-ops/roles/` — `coding`, `research`, `review`: the three that
  were hardcoded in `work/reference/delegate.md`.
- The check, folded into `perry-lint --knowledge` — one flag for the DESIGN-006
  layer rather than a second one nobody remembers.

## The rejection is the design, and it is a closed set

Decision #1 makes a role card a hiring contract the harness instantiates, never
a workflow. `## Workflow` is only the **first spelling** of the violation:
`## Steps`, `## Procedure`, `## How to`, `## Process`, `## 步骤`, `## 流程` are
the same thing wearing other names, and a guard written against the literal
string is the instance-shaped guard this project has found in every review
round.

So the check is **the four allowed sections, closed** — anything else is
reported. A workflow-like heading additionally gets a sharper message, because
it made decision #1's exact mistake and deserves to be told which rule it broke
rather than "unknown section".

`test_a_section_nobody_thought_of_is_rejected_by_the_CLOSED_SET` is the one that
proves it is a category: `## Notes` is on no blacklist and is still reported.
Mutation **M1** turns the closed set into a blacklist containing every workflow
spelling *and* `Notes`; three tests go red.

**The cost, stated:** a card cannot carry `## Why this role exists`. Deliberate
— each of the four blocks has a mechanical consumer (prompt, injection,
pre-flight union, close gate) and a fifth is prose nothing reads.

## The signed contract refused this, and was right

The first version declared `owner: work`. `tests/test_ownership.py` failed with:

> *the set of schema-owned files missing from the signed contract changed. If a
> file was added, the contract needs a fresh V5 signature — not a quiet entry
> in this test.*

**Not worked around.** The right answer was that a role card is not lane state
at all: it is a declaration the project makes about itself, like
`.perry/hook.md`, which is `user`-owned for the same reason. § 5.2's existence
test — a role is warranted only after a real permission or acceptance collision
— is a human judgement, and `packs/` ships templates rather than written cards.
`owner: user`, the contract's ownership table does not move, and no second
signature is owed.

## Goal 7 — a project with no roles behaves exactly as today

Three tests: no `.perry/roles/` at all, an empty one, and Perry itself. The same
no-op property `modes/project.md` holds for work modes, and the reason a project
can ignore this whole layer.

## The three shipped cards differ, on purpose

§ 5.2's existence test says a role is warranted only when it has a permission
boundary or an acceptance standard *distinct from the default*. Shipping three
identical cards would be the thing the doc warns against, so a test asserts
their `Default rung` values are not all the same — `review` sits at V4 because
scoring work it did not build is the whole of what it is for.

## Mutations

5 written, 5 red. The one that mattered is M1: replacing the closed set with a
blacklist of every spelling anyone thought of, which is the shape this check
exists to avoid.

## Not done, and next

Phase D (`delegate`/`dispatch` integration, TASK-075) is unblocked by this and
by phase A. The **escalation union** is its safety property: a role's list must
ADD to the project's high-stakes list, never replace it, or hiring a role
quietly narrows what the project refuses to do unsupervised.
