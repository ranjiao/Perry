# DESIGN-009: An Objective is a title string, and every link to it is a guess

> Status: draft
> Date: 2026-08-27 · Locked: —
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: KR-O4.1, KR-O4.2 (`perry/OKR.md` v2, Objective 4 — aiMark manages projects through Perry)
> Supersedes: —   · Superseded by: —
> Revisits: `DESIGN-007-the-entity-model.md § 5.3`

## 1. Problem

**Perry's OKR has five Objectives and not one of them has a name a program can
hold.**

Measured on this project, 2026-08-27:

```
$ perry-goals list --json → okr.objectives
id=''  title='The four work modes are usable, not just declared'
id=''  title='Every piece of state is queryable and writable by deterministic code'
id=''  title='Perry is landed on three named real projects'
id=''  title='aiMark manages projects through Perry'
id=''  title='Tasks are executed by roles that know things'
```

```
$ perry/okr.jsonl → kinds
{'kr': 34, 'version': 2}      objective rows: 0
```

The contract is reflecting the store faithfully. **There is no row to hang an id
on.** An Objective exists as a title string *denormalized onto each KR record*:

```json
{"kind": "kr", "id": "KR-O1.1",
 "objective": "Objective 1 — The four work modes are usable, not just declared", …}
```

Five distinct values of that field are all five Objectives there are.

### What this costs, concretely

- **An Objective page has no durable address.** aiMark asked for one and cannot
  build it (`aimark/doc/perry-contract-gaps-4.md § 4`).
- **A rename orphans every link to it.** The only identifier is the prose.
- **KR identity inherits the instability.** KR ids are unique on this board —
  27 KRs, 27 distinct ids — but the contract does not *promise* uniqueness, so
  aiMark keys on `(level, objective, id, index)`. That composite **embeds the
  objective title**, so a well-formed `KR-O1.1` becomes unstable because the
  string above it might be edited.
- **`KR-O1.1` already encodes an objective the payload cannot resolve.** The
  `O1` inside the KR id refers to something with no record.

### Why the obvious fix was already refused, correctly

`schema/goals-list-contract.md § Not here` states it:

> **Objective ids invented from position.** `OKR.md` writes `### Objective 1 —
> <title>`, and that "1" is ordinal prose, not a handle. … Deriving `O1`, `O2`
> from order would mint a key the file never stated, and a consumer would key on
> it right up until two headings were reordered.

That reasoning is right and this design does not touch it. aiMark agrees and
explicitly declines to mint one itself — *"a handle we minted ourselves would be
worse than none."*

### The asymmetry that makes this tractable

**The phase level already solved this, and nobody noticed the overall level had
not.**

`perry/phase/002-linkage.md` carries:

```yaml
objectives:
  - id: O1
    title: "The three stores are stores"
    krs: [ … ]
```

and `perry-goals list --json` returns `phase.objectives[].id` populated —
`O1`, `O2`, `O3` — while `okr.objectives[].id` is `""` for all five.

The contract already says why this is legitimate: `objectives[].id` is *"filled
from the linkage register when it names one and left `""` otherwise."* **A
register that STATES the id is not the same thing as deriving it from heading
order.** The phase has such a register. The overall OKR does not.

## 2. Goals

1. Every Objective in `OKR.md` has an id that is **stated in a store**, not
   derived from position, order, or title.
2. That id **survives a rename** of the Objective's title and **survives a
   reorder** of the headings, and there is a test that proves both.
3. `perry-goals list --json § okr.objectives[].id` is non-empty on this project,
   and a consumer can address an Objective by it.
4. Nothing that reads `okr.objectives[].title` or `krs[]` today changes shape.
   The version moves additively.
5. `OKR.md` is **not re-rendered**. The id lands in the store and in the
   markdown only where the markdown already has a cell for it.

## 3. Non-Goals

- **Minting ids from heading order.** Refused above; refused here.
- **Changing `KR-O<n>.<m>` ids.** They are the user's, they are on the board,
  and 27 of them resolve today. Whatever an Objective's id turns out to be, it
  does not renumber a KR.
- **A `phases.jsonl` store.** DESIGN-007 § 5.3 plans one; that is a separate
  step and this design must not require it.
- **Making the linkage register the Objective's home.** It is a *graph*, it is
  phase-scoped, and there is no overall-OKR equivalent. Growing one would put an
  entity's truth in a file whose job is edges.
- **Solving the same problem for Commitments or Anti-Goals.** Both are prose
  registers with their own questions.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | What shape is the id | `O-1` sequential minted / `OBJ-<hash>` content-free / reuse the `O<n>` inside KR ids | TBD | — |
| 2 | Where the id is written back | store only (Recommended) / store + a new `OKR.md` column / store + an HTML comment anchor | TBD | — |
| 3 | What happens to the five existing Objectives | mint on next `perry-okr write` / mint by an explicit one-off migrate command (Recommended) / user names all five by hand | TBD | — |
| 4 | Does `krs[].objective` keep carrying the title | keep the title and add `objective_id` (Recommended) / replace the title with the id | TBD | — |

**On decision 1.** The `O1` in `KR-O1.1` is tempting and is the trap: it is the
*ordinal* the contract already refused, arrived at from a different direction. A
KR id was minted when the KR was written, so it records the objective's position
**at that moment** — reorder the headings and `KR-O1.1` sits under Objective 3
while still spelling `O1`. Choosing it means accepting that the id is a
historical artefact rather than a pointer.

**On decision 4.** `krs[].objective` currently carries the whole heading string,
including the `Objective 1 — ` prefix. Replacing it with an id is smaller and
breaks every consumer that renders a KR grouped under a heading. Adding
`objective_id` beside it is additive and is what a `1.x` bump permits.

## 5. Architecture

### 5.1 The record

A third `kind` in `perry/okr.jsonl`, beside `kr` and `version`:

```json
{"kind": "objective", "id": "<minted>", "version": "v2: 2026-08-17",
 "title": "The four work modes are usable, not just declared",
 "heading": "Objective 1 — The four work modes are usable, not just declared",
 "order": 0}
```

`title` and `heading` are two fields on purpose. `heading` is what the markdown
line says, byte for byte, and is what the renderer reproduces; `title` is the
part after the em dash, which is what a consumer displays. Today one string is
doing both jobs, which is why `krs[].objective` carries the ordinal prefix into
every KR record.

**`version` is on the record**, because `OKR.md` holds `v1` and `v2` side by
side and each has its own five Objectives. That is not hypothetical: `okr.jsonl`
already holds `KR-O1.1` **twice**, discriminated by `version` and `order`.

### 5.2 Where the id comes from

Minted by `perry-okr` at the moment an Objective is first written to the store,
using the same mechanism `perry-task` uses to mint `TASK-NNN`: read the highest
existing, add one, write it down. **The id is stated by the writer, not derived
by any reader**, which is exactly the property the contract's refusal asks for.

An Objective whose record already carries an id keeps it — through a rename,
through a reorder, through a new `OKR.md` version that repeats it.

### 5.3 What the reader does

`viewer/parsers.py § load_snapshot` gains no new parsing. The objective rows come
out of the store like the KR rows do, and `okr.objectives[].id` is filled from
them instead of from the linkage register. **The linkage-register path stays**
for the phase level, which has no `phases.jsonl` yet.

### 5.4 Blast radius

| Touched | Why |
|---|---|
| `bin/perry_md_store.py § STORED` | a fourth kind's field list |
| `bin/perry-okr` | mint, build, render, verify, diff for the new kind |
| `viewer/parsers.py` | fill `okr.objectives[].id` from the store |
| `schema/goals-list-contract.md` | `2.1 → 2.2`, additive; **and its `## Not here` entry rewritten**, because "objective ids are not here" stops being true |
| `schema/state-schema.json` | only if a new `OKR.md` column is chosen in decision 2 |
| `perry/okr.jsonl` | five new records on this project, via decision 3 |

**Not touched**: `perry/tasks.jsonl`, `BOARD.md`, the phase linkage register,
`KR-O<n>.<m>` ids anywhere.

## 6. Implementation plan

1. **The record shape and the mint**, with `perry-okr build` producing objective
   rows and `verify` byte-comparing. No id written yet.
2. **`perry-okr render` reproduces `OKR.md` byte-for-byte** with objective rows
   in the store. This is the gate: if the renderer cannot rebuild the five
   headings from records, the records are wrong. Same bar as `risks-diff`.
3. **The mint and the write-back**, per decisions 1–3.
4. **`okr.objectives[].id` filled from the store**, contract to `2.2`, `Not
   here` rewritten.
5. **The two survival tests** — rename the title, reorder the headings, id
   unchanged both times.

Steps 1 and 2 are worth landing alone: they make the store hold what `OKR.md`
says without any new concept, and step 2 is what proves the record shape is
right before an id is minted into it.

## 7. Risks & mitigations

| # | Risk | Blast radius | Detection signal | Mitigation |
|---|---|---|---|---|
| 1 | The mint runs twice and an Objective gets two ids | every link to the objective silently splits | `perry-okr verify` reports two records with the same `(version, order)` | mint only when the record has no id; assert idempotence in step 3's test |
| 2 | `heading` / `title` split loses a byte and `OKR.md` re-renders differently | the user's own file rewritten | step 2's byte-compare; `cells_verbatim` must be `{}` | step 2 gates step 3 — no id is minted until the render round-trips |
| 3 | `v1` and `v2` Objectives with the same heading collide | history collapses into the current version | `okr.jsonl` already carries `KR-O1.1` twice; a test asserts the two `v1`/`v2` Objective rows are distinct records | `version` is part of the record, not part of the id |
| 4 | A consumer keys on `objectives[].id` before it is stable | the thing this design exists to prevent, reintroduced | the contract's `2.2` entry states when the id is minted and what it survives | do not ship `2.2` until step 5's survival tests pass |
| 5 | The `Not here` rewrite reads as reversing the refusal | a future reader mints ids from position, citing this doc | — | the rewrite must say the refusal **stands** and that a stated id is a different thing from a derived one |

## 8. Open questions

- **Does `KR-O<n>.<m>` become a lie once Objectives can be reordered?** Today the
  `O<n>` matches the heading's ordinal by construction. After this design an
  Objective can move and its KRs keep an id spelling the old position. That is
  survivable — a KR id is a handle, not a path — but it should be *stated*
  somewhere rather than discovered.
- **Should `phase.objectives[]` migrate off the linkage register onto the same
  shape?** DESIGN-007 § 5.3 plans `phases.jsonl`. Doing it here would double the
  blast radius; not doing it leaves two mechanisms for one question, which is the
  defect class this project keeps paying for.

## 9. Changes (append-only after lock)

## 10. References

- `aimark/doc/perry-contract-gaps-4.md § 4` — the request, and its measured
  diagnostic that `okr.jsonl` holds zero objective rows.
- `perry/evidence/2026-08/aimark-contract-gaps-4-triage.md` — every number in
  that request re-measured here.
- `schema/goals-list-contract.md § Not here` — the refusal this design preserves.
- `DESIGN-007-the-entity-model.md § 5.3` — the Goal store this is the missing row
  of. **Note**: that table names it `perry/goals.jsonl`; the file on disk and in
  `claims[]` is `perry/okr.jsonl`. DESIGN-007 is the stale one.
- `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md` — the store-is-truth
  posture this inherits.
