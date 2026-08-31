# Glossary — the vocabulary, and the brake on adding to it

Tier 1. Read when a term in Perry's own prose is unfamiliar, and **before
coining one**.

## Why this file is a constraint, not a reference

An agent-run project grows vocabulary faster than it grows code. A single
working session can invent a dozen terms and start citing them in the same
breath — each one obvious to the session that coined it and opaque to the next
session and to the human reading the board. That cost is invisible while it is
being incurred and unpayable afterwards, because by then the term is in forty
board cells.

So this file does two jobs, and the second is the important one:

1. **It says what each term means**, once, where `perry-explain` can find it.
2. **It makes a new concept cost something.** Every entry must name where the
   term is *implemented* — a tool, a schema field, a test. An entry that names
   nothing declares `prose-only`, and `perry-lint --glossary` counts those and
   prints the number. A concept that exists only in prose is this
   repository's most-found defect (*a rule stated in prose that nothing
   implements*), and the count is what keeps it from being free.

**The rule for adding a term.** Before inventing one, check whether an entry
here already covers it — most "new" concepts are a second name for an existing
one, which is the *other* recurring defect (*N implementations of one rule*)
wearing vocabulary's clothes. If it is genuinely new, add the entry **in the
same change that introduces the term**, and name what implements it.

## Format

```
    ### <term>
    <one line: what it is>
    Implemented: <path>[ § <section>]   |   prose-only
```

(Indented so the parser does not read this example as an entry — which it did,
and `--glossary` reported the template as a broken path on its first run.)

`Implemented:` is checked — the path must exist. `prose-only` is legal and
counted, never silently allowed.

---

### verification rung
How much proof a task needs before it counts as finished. `V0`–`V6`; run
`bin/perry-explain V4` for any single rung.
Implemented: schema/state-schema.json § verification

### V4
A fresh-context reviewer scoring against **written** acceptance criteria. Both
halves are the rung: a reviewer who saw the reasoning, or a review with no
written bar, is V1 with a different label.
Implemented: work/reference/review.md

### V5
A named human signing off, recording **what they actually checked** — and what
they did not. The one rung no tool can verify.
Implemented: schema/state-schema.json § verification

### acceptance criteria
The written bar a V4 is judged against, authored **before** the round. Criteria
written after a result are a negotiation with the result.
Implemented: work/reference/review.md

### verdict block
The fixed `=== VERDICT ===` shape a review returns: one block per row, with
`result`, `checked`, `not-checked` and, on a FAIL, `proof`.
Implemented: work/reference/review.md

### instance-shaped guard
A check written against the case that was found rather than the category it
belongs to — a hardcoded file list, a single call site. It passes forever and
catches nothing new. Perry's own row-integrity guard was instance-shaped three
rounds running.
Implemented: tests/test_row_integrity.py

### green mutation
Breaking the code a check claims to protect and watching the check stay green.
It is a finding either way: either the guard does not work or the test does not
test it.
Implemented: work/reference/review.md

### read contract
A versioned, frozen JSON payload a front-end may code against —
`perry-task/list`, `perry-goals/list`, `perry-decide/list`. Minor versions add
keys; a removal or retype is a major.
Implemented: schema/task-list-contract.md

### field path
A path to one key inside a contract payload — `conformance.evidence_not_found[].id`.
**Not** a Key Result id. Called `key path` for one afternoon until a reader
took it for `KR`, which is what `key` already means here.
Implemented: tests/test_contract_invariance.py

### semantics
The array in a read contract's payload naming which fields **changed meaning**
in which minor version. Exists because "1.x only adds keys" does not cover a
value that was computed wrongly.
Implemented: schema/task-list-contract.md

### startable
An open row that is not itself waiting on a reviewer or a blocker and has
nothing unfinished under it. Derived, never stored.
Implemented: schema/task-list-contract.md

### drift
The board and the event log disagreeing — a state change that happened without
a tool writing it, usually a hand edit. Reported, never refused. Under ADR-007
the same word covers the board disagreeing with the task store, which
`perry-lint` reports as `store-drift` at `warn` and on the same posture.
Implemented: bin/perry-state

### intake
Queue mode's inbox: work that has arrived but not yet been routed onto the
board.
Implemented: schema/state-schema.json

### conformance
Two unrelated things, and the collision is deliberate only in that both are
named in the schema: (a) the block in a read contract naming what the board did
**not** parse cleanly; (b) a file's declared shape version under
`perry-conform`.
Implemented: schema/task-list-contract.md

### the hand-off contract
Each lane reads the others' files freely; no lane writes outside its own. The
one rule that keeps the three lanes composable.
Implemented: reference/hand-off-contract.md

### lane
One of `goals`, `work`, `decide` — loaded on demand by the router. Not a
separately invocable skill.
Implemented: SKILL.md

### work mode
Which shape a track has: `project`, `pipeline`, `queue`, `inquiry`. Determines
the spine, the horizon, the item states and the default rung.
Implemented: modes/project.md

### track
A named stream of work inside one project, declared in `.perry/config.md §
Tracks`. A blank `Track` cell means the implicit `main` track.
Implemented: schema/state-schema.json

### knowledge card
A reusable claim about how to do something correctly, with mandatory
provenance. Distinguished from a digest by its `Kind:`.
Implemented: bin/perry-lint

### role card
A project's own declaration of who it hires — there is no built-in list of
agent types.
Implemented: work/state/role_card_TEMPLATE.md
