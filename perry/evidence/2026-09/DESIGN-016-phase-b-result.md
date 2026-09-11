# DESIGN-016 phase B — result

> Rows: TASK-362 (B1), TASK-363 (B2).
>
> **Reconciled 2026-09-09 after three V4 rounds.** Two claims below were true
> when written and are not now: the contract shipped as `1.19` and the user
> took it to **`2.0`** the same day (a row-count change is a major), and the
> byte figures moved — `--compact` is about 11,300 against `--json`'s about
> 259,000, not 9,198 / 258,981. Every "1.19" and every exact byte count below
> should be read with that. `reference/snapshot.md § Step 3` now states the
> ratio rather than the counts, for the reason those numbers drifted three
> times in one branch.
> Branch: `bin-contract-phase-a`, commit `b30d3b74`. Base: `4ebc0693`.
> Date: 2026-09-09 · Rung claimed: V3 · V4 pending.

## B1 — `perry-state --compact`

| Call | Bytes | Carries the vocabulary |
|---|---|---|
| `--compact` | 9,198 | yes |
| `--dashboard` | 1,053 | no |
| `--section project` | 11,681 | yes, three levels down |
| `--json` | 258,981 | yes, three levels down |

`SKILL.md` step 3 now calls `--compact`. `reference/snapshot.md § Step 3` holds
the explanation, because `SKILL.md` is 11 bytes under a 20,480-byte cap that
`tests/test_router_budget.py` enforces — the first draft of this change put it
484 bytes over.

**It is a projection and a test holds it to that.** `bin/perry-state § COMPACT`
is a tuple of `(key, path into the full payload, how)`; `project_value` applies
one entry and `project_compact` walks the tuple.
`tests/test_compact_payload.py` walks the SAME tuple, applies `project_value`
to the full payload, and compares. A field added to the spec is asserted
without editing the test; a field computed rather than projected fails.

Twelve tests, including two controls: one asserting that most of the spec
resolves to something on a real project (a spec of dead paths would pass every
case and say nothing), and one asserting a scalar is carried verbatim while a
list is counted (the projection test would pass if `project_value` were the
identity).

**What it does not carry.** A track's diagnosis — `stage_counts`, WIP and SLA
breaches — stays in `--section project`. The vocabulary is what the track IS;
the breach list is a verdict about today.

## B2 — `perry-task list` is bounded

`list --json` was 538,134 bytes on this repository and `--all --json`
1,683,852: about 420k tokens, more than the context window of the agent that
reads it. Contract `perry-task/list/1.19`:

- at most 200 rows when the caller names no `--limit`;
- `bound` in the payload — `limit`, `default`, `returned`, `total`,
  `truncated`, `order`;
- one line on stderr when it truncates;
- `--limit 0` for every row, `--limit <n>` for another ceiling.

`schema/task-list-contract.md` carries the changelog entry and the flag row;
`semantics` carries the 1.19 note for consumers that read the payload rather
than the page. Five tests in `tests/test_bin_argument_contract.py`.

## Six tests were pinned to a version and are now floors

Three modules asserted `LIST_CONTRACT == "perry-task/list/1.18"` to mean "my
change bumped the minor", so every later bump failed them for a reason none of
them is about. `test_answered_ask_is_legible`'s own docstring names that defect
— *"An assertion that encodes a moment rather than the rule is the defect this
repository has spent the most nights on"* — and the file had it. They now
assert the shipped contract is at least the version their change landed at.
`test_contract_key_parity` typed the contract NAME in five places and now reads
it from the tool.

## The parity baseline

`tests/fixtures/contract-key-parity.json` is re-recorded. Three kinds of change
are in that diff:

1. the contract name, 1.18 → 1.19;
2. `documented` 137 → 138 and `emitted` 126 → 130 — the `bound` row in the
   contract page and the four `bound.*` keys;
3. **which collections are observable moved** — `in_progress_with_no_live_run`
   and `tasks[].evidence_relations` in, `conformance.review_idle` out.

(3) is not this change: that baseline reads the LIVE board, and today's board
has rows in `review` that were `not_started` when it was last recorded. It is
the same fragility the module's two known-red cases sit on. Both are still red,
unchanged, and they reproduce on `main`.

## Suite

`bash tests/run`: 121 modules, 3392 tests, one module red —
`test_contract_key_parity`'s two, the main baseline. Tree guard clean.
