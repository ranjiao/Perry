# aiMark round 4 — triage, with every load-bearing claim re-measured

> Source: `/Users/bytedance/proj/aimark/doc/perry-contract-gaps-4.md`, 2026-08-21.
> Measured here on `~/proj/Perry` with `/usr/bin/python3`, the same board aiMark
> measured. **Every number in the request checks out.** Two of its conclusions
> do not, and one of those changes its top priority completely.

## The document counts are exact

| collection | aiMark | measured |
|---|---|---|
| `evidence/` | 210 | **210** |
| `decisions/` | 9 | **9** |
| `design/` | 8 | **8** |
| `handoff/` | 7 | **7** |
| `journal/` | 6 | **6** |
| `knowledge/` | 1 | **1** |

## § 3 — the ask is already built, and that is the finding

aiMark's stated top priority — *"if you only take one"* — is a read surface for
knowledge cards, on the grounds that **`perry-knowledge` is `propose` / `promote`
only: there is no read side at all.**

That is wrong, and the way it is wrong matters.

```
$ python3 bin/perry-knowledge list --json
{ "contract": "perry-knowledge/list/1.0", ..., "total": 1, "stale": 0,
  "cards": [ { "path": …, "topic": …, "slug": …, "kind": …, "claim": …,
               "owner_role": …, "source": …, "last_verified": …,
               "invalidated_by": …, "stale": false } ] }
```

The nine fields the request asks for, typed —
`{topic, slug, claim, kind, owner_role, source, last_verified, invalidated_by, path}`
— are **all nine of them there**, plus the aggregate it called a bonus: a per-card
`stale` flag and `total` / `stale` counts. The "cards nobody has re-verified"
strip is one call away and always was.

**Why a careful consumer could not find it.** There is no
`schema/knowledge-list-contract.md`. `schema/` holds six files and this is not
one of them:

```
decide-list-contract.md  events-list-contract.md  goals-list-contract.md
roles-list-contract.md   state-schema.json        task-list-contract.md
```

A tool that emits a `contract:` string and has **no contract document** is
invisible to anyone reading `schema/`, which is precisely where a consumer is
told to look — and `schema/README.md` still says *three* contracts (TASK-130).

This is the same defect class an aiMark agent surfaced earlier the same day
about `conformance.missing_projection`: **it ships, it is real, and no version
or page a consumer reads ever announced it.** `tests/contract_key_parity.py`
cannot see either, because it compares documented against emitted *within a
contract page that exists*.

So § 3 is not a build. It is a page and an announcement.

## § 5.1 — events returns the HEAD, and three places say TAIL

Reproduced exactly:

```
$ python3 bin/perry-task events --json --limit 6
returned seq: [0, 1, 2, 3, 4, 5]
first ts: 2026-08-16T18:33:04   last ts: 2026-08-17T00:55:19
```

726 events in the log; those six are the **oldest**, five days stale, with
nothing in the payload saying so. The three places that say otherwise:

- `schema/events-list-contract.md:3` — *"The event log's **tail**"*
- `schema/events-list-contract.md:21` — *"…a question about the log's tail"*
- `perry-task events --help` — *"the event log's TAIL, in log order"*

aiMark's workaround is a 437 KB read on every project. Either the first page
becomes the tail or three lines are corrected; **the payload must not keep
saying one and doing the other.**

## § 5.2 — three kinds missing from the key table, not two

aiMark named `intake` and `answer`. Measured against the live log:

```
live kinds  : add answer ask depends done drop evidence intake next
              prioritize retitle rung start status
documented  : add depends done drop evidence next prioritize retitle rung
              stage start status track
live-not-doc: answer  ask  intake
```

`ask` is missing too. (`stage` and `track` are documented and not yet exercised
— not a defect.)

## § 5.3 — confirmed, and it is live on this board today

```
$ python3 bin/perry-task list --all --json   →   asks: {"items": [], "open": 0}
```

`USER-015` and `USER-016` were both answered on 2026-08-21 and are gone from the
register entirely, while `TASK-040`'s record still names `USER-016` in
`depends_on` — correctly, a satisfied dependency stays. So that id is in **no**
register a consumer can query: not `tasks[]`, not `asks.items`, not
`depends_on_unknown`.

aiMark is right that inferring the entity's kind from three arrays it is absent
from is set arithmetic, and right to refuse it.

## § 2 — verified, and latent exactly as stated

```
perry-decide list  →  9 rows, every id ADR-*
                      types: Architecture 4, Process 3, Design 2
tasks declaring a DESIGN-/ADR- dependency  →  0 of 164
```

`type: Design` is a category of ADR and is not the eight `design/DESIGN-NNN-*.md`
documents. The id family is blessed by
`task-list-contract.md § depends_on_unknown` and listed by nothing.

## § 4 — verified, including the store-name discrepancy

All five objectives return `id: ""`. `perry/okr.jsonl` holds `{kr: 34,
version: 2}` and **no objective row** — the contract is reflecting the store
faithfully; there is no row to hang an id on.

The small one is real:

```
perry/design/DESIGN-007-the-entity-model.md:429
  | Goal + KR | `perry/goals.jsonl` | `OKR.md` |
```

The file on disk is `perry/okr.jsonl`, and `claims[]` declares `okr.jsonl` as of
2026-08-21. **DESIGN-007 is the stale one.**

## What this triage does not settle

§ 1 (a `perry-docs/list` contract) and § 4 (an Objective record with a minted id)
are both **design decisions, not implementations**. § 4 in particular is a
DESIGN-007 gap — `§ 5.3` there already plans a Goal store and this is the row it
is missing — and minting an id for an entity that has never had one is the kind
of change ADR-007 and DESIGN-008 both took an RFC to make.

Rows are opened for both, flagged as needing a decision first.
