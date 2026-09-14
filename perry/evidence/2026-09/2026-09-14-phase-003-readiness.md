# Phase 003 — close readiness, measured 2026-09-14

**Read-only.** Nothing here scores the phase; `score-phase` does that. This
file measures today's state against `phase/003-storage-code.md § Definition of
Done` and the six KRs, so the close starts from numbers rather than memory.
Measured on `161c927c` and `49581b73` (main). The lint and store-removal runs
used a `git archive` copy.

## Definition of Done

| # | item | measured | state |
|---|---|---|---|
| 1 | `perry-lint --root .` prints a drift verdict for six stores, and `unchecked` for each whose file is removed | with all stores present, exit 0 and one line each: tasks 434 records 0 drifted, risks 4/0, intake 0/0, asks 33/0, OKR 51/0, linkage 258 records 0 malformed. Removing each of the six in turn prints "`no <store>.jsonl` — … unchecked, not clean" for that store (cadence.jsonl, the seventh store, arrived today in `TASK-237` 3b) | **met** |
| 2 | `intake.jsonl` and `asks.jsonl` exist, imported by their own commands | both on disk (asks 33 records, intake 0) | **met** (the import history is not re-derived here) |
| 3 | the four named `parse_tracks` call sites read `.perry/config.jsonl` | `grep -rn 'parse_tracks(' bin viewer` finds no call site. `P003-O2-KR1` reads current 0, target 0 | **met** |
| 4 | the adoption-reader guard goes red, **or** the phase records in writing that the reader has no caller | recorded: § Changes / Pivots 2026-09-02 (`USER-911`) withdraws `P003-O2-KR2`, because no adoption reader exists | **met, by the written branch** |
| 5 | every `main`-track row opened after the gate lands carries a KR edge or an `unlinked` declaration written by its own `add` | see `P003-O3-KR2` below. Everything turns on what "the gate lands" means | **open: a scoring decision** |
| 6 (nice) | the render distinguishes projection from canonical (`P003-O2-KR3`, `TASK-262`) | not started. The spec was drafted today (`evidence/2026-09/TASK-262-spec.md`); dispatch waits on `TASK-237` 3c | **not met** |
| 7 (nice) | `TASK-050`'s mutation harness replaces the regex round | `TASK-050` done at V4 (`evidence/2026-08/TASK-050-round11-v4-review.md`) | **met** |

## KRs (`perry-goals list --json`)

| KR | current | target | note |
|---|---|---|---|
| P003-O1-KR1 | 6 | 6 | met |
| P003-O1-KR2 | 6 | 6 | met |
| P003-O1-KR3 | 6 | 6 | met |
| P003-O2-KR1 | 0 | 0 | met |
| P003-O2-KR3 | — | — | no measurement defined. `TASK-262`'s spec proposes one; writing it is the goals lane's job |
| P003-O3-KR2 | **33.3** | 100 | **measured, 20 of 60** |

### `P003-O3-KR2`, broken down (`bin/lib § same_action_linkage`)

- **Population:** 60 rows, TASK-381 … TASK-440. These are the `main`-track rows
  whose own `add` event carries a `kr` key. That key was first written by the
  **advisory** gate, which warned and filed the row anyway.
- **Numerator:** 20.
  - Linked at `add`: 4 (TASK-382, 383, 394, 439).
  - Declared `unlinked` at `add`: 16 (TASK-396–405, 434–438, 440).
- **Never answered:** 40 (TASK-381, 384–393, 395, 406–433).
- **Consistency:** `store_edge_without_event` 0 and `event_kr_without_store_edge`
  0. The two files agree.

**The refusing gate landed today.** `TASK-439` closed at V4 on 2026-09-14, and
from that point `add` refuses when a register declares the phase. Only
TASK-440 was opened after it, and TASK-440 answered: 1 of 1. The 40
never-answered rows were filed under the advisory gate. They **cannot be
repaired**, because the KR's clause is "in the same action as `add`" and a later
`perry-goals link` records `via: link`.

**So two readings of item 5 are both honest, and they give different scores:**
- **the gate is the advisory one**, where the measurement starts: 33.3%,
  missed;
- **the gate is the refusing one** that item 5's "the gate lands" requires: 1
  of 1 since 2026-09-14. That sample is too small to call a result, and the
  retro would say so.

This is the user's call at `score-phase`, not something to settle by editing
the computation.

## What blocks a close today

1. **`TASK-237`.** 3b is merged partially and stopped on the `installed`
   predicate, which waits on the user. 3c, the deletion, has not started.
   `TASK-262` waits on 3c.
2. **The item-5 / `P003-O3-KR2` reading** above.
