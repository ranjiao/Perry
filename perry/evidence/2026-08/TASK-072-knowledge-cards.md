# TASK-072 — DESIGN-006 phase A: knowledge cards carry provenance or they are reported

> Source: `perry/design/DESIGN-006-roles-and-knowledge.md § 5.3`, § 6.1 phase A.
> Rung: **V3**. Everything below is a run.

## What shipped

- `schema/state-schema.json § files[id=knowledge-card]` — five fields, and a
  `discriminator` saying a card is told from a digest by its `Kind:`.
- `thresholds.knowledge_stale_days: 90`, read by the linter rather than written
  in it.
- `work/state/knowledge_card_TEMPLATE.md`, and `## Cards by topic` in the index
  template.
- `perry-lint --knowledge` — the four provenance fields, a resolvable `Source:`,
  and staleness.

## Two decisions worth the record

**`Owner role: —` is silent until the project has roles.** `§ 5.3` writes the
field as *"`finance` — or `—` before roles exist"*, so warning on it today would
put a finding on every card in every project until phase C lands. A check that
fires on the documented correct answer is one people learn to ignore. It becomes
a finding the moment `.perry/roles/` holds a card, because then there is an
answer and a blank means nobody is accountable.

**`--knowledge` and `--provenance` skip each other's files.** Cards and digests
share `knowledge/*/*.md`. A card is a claim the project made; a digest is a
source it read. Neither is malformed for not being the other. The discriminator
is declared once in the schema and read by both — and the first version of this
was wrong in a way worth recording: `--provenance` did not call
`load_glossary`, so `CARD_KINDS` was empty, `card_kind()` returned `None` for
everything, and every card was reported as *"digest carries no `Id: SRC-<n>`"*.
Caught by a test that runs both checks over one tree.

## The KR-O5.1 problem, and what was done about it

`perry/OKR.md` KR-O5.1 reads *"lint live · 0 violations"*. **Zero violations
over zero cards is trivially true** and cannot tell "provenance is enforced"
from "nobody has written a card". Two answers:

1. `--knowledge` prints and returns the **card count** alongside the violation
   count, so the KR is read as a pair.
2. Perry wrote its **first real card** — `knowledge/toolchain/pycache-staleness.md`
   — and `tests/test_knowledge_cards.py` asserts the count is above zero and the
   findings empty. The KR can no longer be met by an empty set.

The card records a real incident from this session: a mutation harness that
edits a file, runs a test, and restores it within the same second leaves a
`.pyc` Python considers valid, so the suite reports failures the source does not
contain. It cost two agents a confusing run each before the cause was named.
