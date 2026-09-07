# TASK-277 — result

> Design: `design/DESIGN-015-linkage-is-a-store.md`, implementation plan row **B**
> Branch: `task-277-linkage-import`, cut from `main` at `555ced0`; merged as `b493493`

## Provenance of this document — read this first

**The implementing agent was killed by a session rate limit on 2026-09-04 with
its work committed and no RESULT block written.** This document was written by
the PMO on 2026-09-07, and every claim below is the PMO's own measurement
against merged `main`, not a report transcribed from the agent. Each one names
the command that produced it so a reviewer can re-run it rather than believe
it. Nothing here is the agent's testimony, because the agent left none.

The V4 reviewer should treat this exhibit exactly as `review.md § 2 rule 3`
says: as the previous round's claim, not as evidence.

## The count, and why it is not the spec's 93

```
$ python3 -c "…count perry/linkage.jsonl by kind…"
total 121
by kind {'kr': 6, 'edge': 15, 'unlinked': 100}
```

**121 records: 6 `kr` + 15 `edge` + 100 `unlinked`.**

> **CORRECTED 2026-09-07, after TASK-277's V4 round.** This section first
> derived the delta as `11 − 2 + 6 = 15`, reading the spec's `11 edge` as a
> real measurement and attributing six edges to rows "added after 09-02".
> **That derivation is wrong, and the round found a better one.** The right
> evidence was already in the tree and this document did not use it:
> `phase/snapshots/2026-09-02-003-linkage-pre-kr2-withdrawal.md` holds the
> register as it stood that day, and it carries **17 edges, not 11** — including
> `TASK-283` and all five DESIGN-015 rows. Nothing was added after 09-02. The
> arithmetic reached the right total by a route that was not what happened,
> which is the failure mode `knowledge/verification/numbers-migrate-between-sentences.md`
> is about.

**The reconciliation, done structurally rather than arithmetically.** Diff the
09-02 snapshot against the current register and the **only** structural change
is `P003-O2-KR2` removed, taking exactly `TASK-050` and `TASK-099` with it:

| | 2026-09-02 snapshot | now | change |
|---|---|---|---|
| `kr` | 7 | 6 | `P003-O2-KR2` withdrawn |
| `edge` | 17 | 15 | `TASK-050`, `TASK-099` — they sat under that KR |
| `unlinked` | 86 | 100 | the board opened rows |

**Zero edges added. Zero `unlinked` removed.** The withdrawal is recorded by
`USER-911` and `USER-912` in `asks.jsonl` and in
`phase/003-storage-code.md § Changes / Pivots`. `TASK-050` and `TASK-099`
survive in `phase/003-linkage.md:76` as prose, in no `tasks:` field.

**So the spec's `7 kr + 11 edge + 75 unlinked = 93` was never the register's
state on the day it was cited** — the register held 17 edges that day. The
spec's instruction *"Re-measure the register first and say so in the result if
it has moved since"* is therefore doubly right, and this is that re-measurement.

The spec's line *"the 11 edges are exactly TASK-203, 209, 067, 229, 095, 233,
247, 099, 050, 215, 262 — neither invented nor dropped"* resolves cleanly:
**nine of the eleven are present, and the two absent ones are absent because the
KR they named was withdrawn — not dropped by the import.** Proven by the
snapshot, not argued.

The 15 edges now in the store, by KR:

```
P003-O1-KR1  TASK-203
P003-O1-KR2  TASK-209, TASK-067
P003-O1-KR3  TASK-229
P003-O2-KR1  TASK-095, TASK-233, TASK-247, TASK-283
P003-O2-KR3  TASK-215, TASK-262
P003-O3-KR2  TASK-276, TASK-277, TASK-278, TASK-279, TASK-281
```

This is field-for-field the six `tasks:` lists in `phase/003-linkage.md`
frontmatter (lines 16, 24, 32, 42, 48, 57): `1+2+1+4+2+5 = 15`.

## `via` — the field that could have wrecked the KR chain

**All 100 `unlinked` and all 15 `edge` records carry `via: link`. None carries
`via: add`.**

```
via   {('edge','link'): 15, ('unlinked','link'): 100}
actor {('edge','goals'): 15, ('unlinked','goals'): 100}
```

This is the single most consequential thing in the row and it is correct.
`P003-O3-KR2` counts rows linked **in the same action as `add`**. These records
were swept out of a document that does not record how its entries got there, so
`via: add` would have been a claim nobody could support — and it would have
inflated the exact KR this design exists to make honest, in the store that is
about to become the authority for it. Nothing downstream could have detected
it. `via: link` is the honest answer for a record whose provenance the document
does not carry, and `actor: goals` is right because the `goals` lane is the
document's only writer.

## The document is byte-unchanged

The spec requires `phase/003-linkage.md` to be read-only in this row.

```
$ git diff b493493^1 b493493 --stat -- perry/phase/003-linkage.md
(no output)
```

An empty diffstat across the merge is byte-equality, and it is stronger than a
recorded `md5` pair because it is re-derivable by anyone at any later time.

## `agents: []` and `projects: []`

Both are empty in the register frontmatter (`phase/003-linkage.md:59-60`), and
the store holds **zero** records of either shape — asserted, not silently
produced: the `by kind` census above returns exactly three kinds, and neither
`agent` nor `project` is among them.

## The seventh store behaves correctly, and its verdict is honest

```
$ bin/perry-lint --root .
  · linkage store: 121 valid record(s), comparison incomplete — drift is unchecked, not clean
```

`unchecked, not clean` is the phase-003 operating rule and the property
`TASK-229` measured for the other six stores. It says the comparison is *not
possible yet* rather than *passed* — the readers still read the document, which
is `TASK-278`'s row, not this one. A store that reported `clean` here would be
claiming a comparison nothing performed.

## What landed

```
$ git diff --stat b493493^1 b493493
 bin/perry-lint                            |  48 +-
 bin/perry-tasks                           | 749 +++++++++++++++++++++++++++++-
 perry/evidence/2026-09/TASK-277-result.md |   6 +
 perry/linkage.jsonl                       | 121 +++++
 tests/durations.json                      |  11 +
 tests/test_linkage_import.py              | 747 +++++++++++++++++++++++++++++
 6 files changed, 1677 insertions(+), 5 deletions(-)
```

No reader moved, which is what the spec requires of row B.

## What is NOT checked here, and is the reviewer's to check

Stated plainly because `review.md § 2 rule 4` makes it the author's job to say
where the ground is uncovered:

- **The 747-line `tests/test_linkage_import.py` was not mutated by the PMO.**
  Whether those tests can go red is unmeasured. This is the largest uncovered
  area and the first place a round should go.
- **The 749 lines added to `bin/perry-tasks`** — the importer — were read for
  their output, not audited line by line. Whether re-running the import is
  idempotent, and what it does against a register that has moved again, is
  unmeasured.
- **The 48-line change to `bin/perry-lint`** was verified only by the one census
  line it prints. Its behaviour with `perry/linkage.jsonl` absent was **not**
  re-measured by the PMO; `TASK-276`'s round measured that property before the
  file existed, which is not the same test.
- **Full-suite state and lint error count at merge** were not recorded by the
  PMO on this row.

---

## Addendum 2026-09-07 — the V4 round answered the four uncovered areas

Recorded here so the next reader does not re-open them. Full account in
`evidence/2026-09/TASK-277-v4-review.md`.

- **`tests/test_linkage_import.py` reddens.** 14 line-anchored mutations of the
  production code, **12 red, 1 green, 1 re-run**. The green one is `M10`, the
  `linkage: 1` spec-version gate — the guard itself works (a `linkage: 2`
  register is refused with the store untouched), so it is a **test-coverage gap
  and not a live defect**, and it is now `TASK-376`. It was the only uncovered
  branch found in the importer.
- **The importer is idempotent** across three consecutive re-runs, and survived
  **21 adversarial registers**, each on its own fresh extraction: eleven refused
  with nothing written, a corrupted store refused with exit 2 rather than
  overwritten, and a register that has moved again accepted correctly — including
  the whole-KR-removal case, which reproduces the `P003-O2-KR2` scenario above.
- **The `bin/perry-lint` change is a genuine bug fix, not scaffolding.** Without
  it the next lint run after the import raises `NS-01` on Perry's own store and
  tells the user to relocate away from it. `looks_like_perry_record` has exactly
  one production caller and it passes `schema`; no call site was missed.
- **The absent-store census holds.** With `perry/linkage.jsonl` moved aside the
  line reads `no linkage.jsonl — drift against the linkage store is unchecked,
  not clean`, 0 errors in both states. Neither state claims `clean`.

One correction the round owed and paid: its `M9` left a stray trailing byte in
the register that survived into three later mutations. It was caught with
`git status`, restored from the ref, and `M10` and `M1` re-run on a
verified-clean tree — the table above is the re-verified one. `phase/003-linkage.md`
is clean on `main`, checked independently here.

The one finding that outlives this row: **the store carries no uniqueness or
mutual-exclusion invariant** — a duplicate `edge`, a duplicate `unlinked`, or a
task that is *both* linked and declared unlinked all import silently and pass
every gate. `DESIGN-015 § 5.2` derives *never-asked* as "neither an `edge` nor an
`unlinked` record", and a row holding **both** is a state that derivation has no
reading for. It is **pre-existing** — the same contradictory register reports
`0 error(s)` at the merge base — and the importer is right to mirror the register
faithfully. Filed as `TASK-375`.
