# TASK-442 — spec

> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: large
> Touches architecture: §2 (bin, lanes), §4, §5 (perry-state payload), §6.NN-1, §6.NN-4
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Track / mode**: main / project
- **Dependencies**: none.
- **Design**: `DESIGN-020 § 5.2–5.4` and `§ 6` phase A (locked 2026-09-14), with
  its `§ 9` entry of 2026-09-15 (the command decides; the agent renders).
- **KR linkage**: `P004-O1-KR1`.
- **Verification rung**: V3.

## Why

Perry's "suggest next actions" lives at five sites as example sentences with no
state behind them (`reference/snapshot.md` step 5, the `goals`, `work` and
`decide` standups, one subcommand row), so two agents reading the same project
recommend different things. `DESIGN-020` moves the judgement into a deterministic
command: typed facts, a declared rule file, the same answer for the same state.

## Deliverable

1. **`perry-state --section next [--after <subcommand>] [--lane goals|work|decide]`**
   emitting `next` as `DESIGN-020 § 5.4` specifies: `contract: perry-next/1.0`,
   `position[]`, `primary`, `alternates[]` (at most 2, each a different command),
   `unknown[]`, and a `conformance` block. `next` is also a key of the full
   `--json` payload. **`--compact` output is unchanged.**
2. **Facts (`DESIGN-020 § 5.2`)** computed only from values `perry-state` already
   computes, plus the clock (injectable for tests). New facts: `phase.kr_progress`
   (measured / met / unmeasured from the register's `current` and `target`),
   `week.iso`, `today.weekday`. **`week.planned` and `drafts[]` have no source
   until `TASK-444`** — emit them as unknown and list them in `unknown[]`; never
   infer them from another file.
3. **The rule file `reference/next-rules.json`**: the `§ 5.3` table — three
   overlays and ten `project`-spine rules — plus `queue`/`pipeline` replacements
   for rules 3–5 where `perry-state` already exposes the fact (SLA breach, WIP
   over limit, commitment due); a replacement whose fact is not exposed is
   declared and reports unknown. Each rule: `id`, `when` (typed predicates only:
   fact path, operator `eq ne lt le gt ge in exists nonempty`, value; `all` /
   `any`), `spine`, `lane`, `command`, `reason` template, `after[]`. Thresholds
   come from `schema/state-schema.json § thresholds` where one exists (read only);
   otherwise they are declared in the rule file with a note.
   Evaluation: overlays first, then declared order; a predicate over an unknown
   fact does not fire and adds that fact to `unknown[]`.
4. **`reference/next.md`**: one entry per rule id saying why it exists, and how
   an agent renders the block — the passive rendering in `§ 5.4`, and the `§ 9`
   rule that the agent may add one separately marked note and never reorders,
   adds or drops a recommendation. The closing step is `TASK-443`, not here.
5. **Pointers.** `reference/snapshot.md` step 5 and the three lane standups'
   "Suggest 1–3 next actions" steps become a pointer to rendering
   `perry-state --section next` per `reference/next.md`. The router `SKILL.md`'s
   step-5 phrase becomes the same pointer with **net bytes ≤ 0** (it is 20,457 of
   20,480 today). Lane files stay within `tests/test_router_budget.py`.
6. **The contract.** A `perry-next/1.0` row in `schema/README.md`'s contracts
   table and a page `schema/next-contract.md` (keys, types, semantics), covered by
   the key-parity test the way the other contracts are.
7. **Tests.** Five fixture projects, each with its expected primary rule written
   in the test: installed with no OKR; OKR with no phase; an active phase whose
   week plan is unknown (the test states which rule is primary and that
   `week.planned` is in `unknown[]`); a closable phase; a queue track. Deleting any
   one rule from a copy of the rule file reddens its fixture. The same state
   evaluated twice yields an identical `next` payload.
8. **A result** at `perry/evidence/2026-09/TASK-442-result.md`, with
   `perry-state --section next` run on this repository quoted.

## Files in scope

- `bin/perry-state`; `bin/lib/__init__.py` only for a shared helper
- `reference/next-rules.json` (new), `reference/next.md` (new), `reference/snapshot.md`
- `SKILL.md`, `goals/SKILL.md`, `work/SKILL.md`, `decide/SKILL.md` — the step-5 lines only
- `schema/README.md`, `schema/next-contract.md` (new)
- `tests/test_next_*.py` (new), fixtures they need; `tests/test_shipped_vocabulary.py` only to classify the new pages
- `tests/durations.json`; `perry/evidence/2026-09/TASK-442-result.md`

## Bound

```
Enumeration:  the rules of DESIGN-020 § 5.3 (3 overlays, 10 project-spine
              rules) and the queue/pipeline replacements for rules 3–5
Size:         13 + the replacements declared
Remainder:    rules DESIGN-020 does not name are out of scope
Last element: R-board-over-cap
```

## What it must not do

1. **No new reader of any state file (NN-1).** Facts come from what
   `perry-state` already reads; a fact that would need a new parse is unknown in
   this row and listed in the result.
2. **No rule judges prose (NN-4).** Predicates compare typed values only.
3. **Must not edit `schema/state-schema.json`.** It is the claim surface; its
   thresholds are read, never written. If a threshold is missing, declare it in
   the rule file.
4. **Must not change an existing `perry-state` key or value**, nor `--compact`.
   `next` is additive.
5. **Must not build the closing step (`TASK-443`), drafts (`TASK-444`) or
   `/perry plan`.**
6. **Must not write the task stores, `linkage.jsonl`, `okr.jsonl`, `phase/`,
   `.perry/events.jsonl` or the journal in the checkout**; tests use temp roots
   (NN-5).
7. **`SKILL.md` net bytes ≤ 0.**

## Verification

1. **Base check** as the brief states.
2. **`bash tests/run` on the final commit**: no reds beyond the agent's own
   measurement at base. Re-run any red module alone before attributing it.
3. **The five fixtures green, and mutations** on scratch copies, each red on a
   named test: delete one rule; let a predicate over an unknown fact fire; move
   an overlay below the project rules. A green mutation is a finding.
4. **`tests/test_router_budget.py`** and the contract key-parity test green.
5. **`perry-state --section next`** on this repository prints `position`, a
   primary or an honest empty, and `unknown` naming `week.planned`.

## Subjective verification

- [user-verify] Do the `reason` strings in the sample output read as plain
  language a user would act on?

## Out of scope

- `TASK-443` (closing step), `TASK-444` (drafts), `TASK-446` (snapshot size).
