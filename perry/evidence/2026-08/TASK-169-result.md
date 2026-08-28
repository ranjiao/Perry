# TASK-169 — `perry-knowledge/list/1.0` ships every field aiMark asked for and had no contract page

**Merged locally 2026-08-21** from `coding/task-169-knowledge-contract-page` @
`9a6d7f1`. Rung **V3**. `merge-check`: nothing new is red.
Post-merge: **80 modules · 2355 tests · 2 red**, both pre-existing.

aiMark's round-4 **top priority** was to *build* this surface. It existed. The
row was a page and an announcement, and the payload gained nothing.

## Verified independently

The instrument, run in the worktree rather than read from the report:

```
6 contract pages discovered
perry-knowledge/list/1.0   documented 16  emitted 16   dne 0   end 0
KR-O2.4 metric: 0
```

`bin/`, `perry/`, `schema/state-schema.json` and
`schema/events-list-contract.md` all untouched — 0 files.

## The `stale` predicate, and why stating it was the work

From `bin/perry-knowledge`, confirmed in the source here:

```python
stale_days = SCHEMA_THRESHOLDS["knowledge_stale_days"]["value"]   # 90
"stale": bool(age is not None and age > stale_days)
```

Three properties, each **mutation-proved** rather than asserted:

1. **Strictly greater.** 90 days is `false`, 91 is `true`. Flipping `>` to `>=`
   reddens the boundary test.
2. **An unreadable date is `false`, not `true`.** Absent, an em dash, prose, a
   calendar-impossible `2026-02-30`, and future dates all yield `false`. So
   `stale: false` means **not measurably stale**, never *"verified recently"*.
3. **`invalidated_by` is not an input.** Folding it in reddens the tripwire test.

The third is what the announcement had to get right. `perry-knowledge --help`'s
claim about `Invalidated by` is true and describes a **different mechanism**: the
tripwire is enforced at **write** time by `promote` and reported afterwards by
`perry-lint --knowledge`. The `stale` flag is the schema's own stated backstop —
`thresholds.knowledge_stale_days`'s note says so verbatim: *"`Invalidated by` is
the sharper signal — this is the backstop for a tripwire that never fired because
nobody was watching the system it names."*

A consumer rendering "3 cards unverified since June" from a flag it did not
understand is the second reader this whole arrangement exists to prevent.

## Three findings, all left as findings

**1. The recorded parity baseline was already stale at HEAD, in a
state-dependent way.** `115/115` recorded against `113/113` live, with six
`intake` rows traded for eight `asks` rows in `unassigned`. Proved not to be this
row's doing by stashing and re-measuring at HEAD.

KR-O2.4 is unaffected — the asserted fields are the two diff lists and both
stayed empty — but **the fixture's counts drift with the board and nothing
catches it**. Same defect class as `test_contract_invariance`'s union-typed key,
one fixture over: *a value read out of the project it lives in, recorded as a
literal.*

**2. `tests/contract_key_parity.py`'s docstring still says five contracts.**
There are six. Deliberately not edited in a row whose whole point was not
touching the instrument.

**3. A field that plainly should exist, and was not added.** The payload emits
`stale` and **not the threshold that produced it**. Confirmed here — the
top-level keys are `contract, project_root, state_root, cards, total, stale` and
nothing else. So a consumer cannot honestly render *"unverified for over 90
days"* without separately reading `schema/state-schema.json`, which is exactly
the read-the-schema-not-the-payload dependency the contract arrangement exists to
remove. A `stale_days` key closes it additively at `1.1`. Out of scope, so the
page instead tells consumers to read the threshold or to say *"past the project's
threshold"*.

## The README had two stale pins, not the one TASK-130 names

```
schema/README.md:86   perry-task/list/1.11    actual 1.14
schema/README.md:88   perry-goals/list/1.0    actual 2.1
```

TASK-130's title names only goals. Both left untouched per instruction; the page
instead states that the table's version column is **a convenience nothing
checks**, names the payload's own `contract` string as authoritative, and points
the pins at TASK-130 — so the table is no longer quietly wrong while that row
keeps its work.

A new test pins the README's contract **count** to `len(parity.discover())` and
requires every discovered page's filename to appear. A count alone would pass on
six rows for five pages plus an invention.

## Where the spec was wrong

- *"`tests/contract_key_parity.py` covers it"* implied work. **It did not** —
  discovery is a glob and the page registered itself. The only action was
  `--record`, and the "if KR-O2.4 goes above 0" branch never fired.
- The spec's payload sketch was accurate, so the "report it and stop" branch did
  not fire either.
