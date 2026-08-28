# TASK-128 — the exact change awaiting a signature

> Source: `perry/design/DESIGN-007-the-entity-model.md § 4` decision #2, `§ 5.3`, `§ 6` step 2
> Dispatch mode: none — this is a human gate, not work
> Deployed: no

## What was already decided, and by whom

- **2026-08-19, signed by Ran Jiao** — DESIGN-007 decision #2: *the store is the
  definition, the card is rendered output.* Not reopened here.
- **DESIGN-007 § 5.3** already names the paths: `.perry/agents.jsonl` is the
  store, `.perry/roles/*.md` is what it renders to. Not chosen here.
- **2026-08-20, chosen by the user** — the writing lane is **`work`**.

What is left is the one thing that has always required a human: **moving a row
in the ownership table.**

## The edit, in full

One line changes in `SKILL.md § The hand-off contract`. The `work` row gains
its fifth and sixth path:

```diff
-| **`work`** (`work/`) | `BOARD.md` (incl. `## Intake`, `## Cadence`), `journal/`, `PROJECT_STATE.md`, `evidence/`, `weekly/`, `handoff/` | KR attribution edges, handed to `goals` |
+| **`work`** (`work/`) | `BOARD.md` (incl. `## Intake`, `## Cadence`), `journal/`, `PROJECT_STATE.md`, `evidence/`, `weekly/`, `handoff/`, **`.perry/agents.jsonl` → `.perry/roles/`** | KR attribution edges, handed to `goals` |
```

Nothing else in that section moves. `goals` and `decide` are untouched.

## What this costs, stated before the signature rather than after

1. **`.perry/roles/*.md` becomes drift-reported.** A hand edit to a role card
   will read as drift, exactly as it does for `BOARD.md` today. This is the
   same trade already accepted for the board on 2026-08-19; it is repeated
   here because it applies to a file that has never had it.
2. **`schema/state-schema.json` says the opposite today.** Its note on
   `.perry/roles/*.md` reads *"OWNER IS `user`, NOT A LANE"* and gives the
   reason. That note becomes wrong on the same commit and must change with it.
3. **`SKILL.md` lands at 20,457 bytes against a 20,480 cap** — 23 bytes of
   headroom. The account of this change therefore goes to
   `reference/hand-off-contract.md`, which is uncapped and is already where the
   section points for both prior accounts. **The next contract change will not
   fit and will force a trim of the router first.**
4. **The paragraph below the table still reads "Two changes from the previous
   contract".** It describes the 2026-08-16 edit and stays accurate about that
   edit; it does not mention this one, because there is no room. Anyone reading
   the table alone will see three lanes and no history of the third change.

## What the signature is attesting

Not that the code is right — none is written yet. That **this row is the
correct owner**, which is the one thing no test can check: a wrong contract
surfaces later as silent cross-lane writes, never as a lint error.

`tests/test_ownership.py` refuses a lane-owned path the contract does not list.
It refused this one, correctly, and it will accept it the moment the row lands.

## After the signature

TASK-129 unblocks: the Agent store, typed `may_touch[]` / `must_escalate[]`,
the card rendered rather than authored, and `events.actor` carrying an id
instead of the six free-text values it holds today.
