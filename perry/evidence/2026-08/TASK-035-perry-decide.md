# TASK-035 — `perry-decide`: writer, bootstrap, read contract

> Design: `perry/design/DESIGN-005-state-and-contracts.md` § 6 step 1
> Closes: round-4 review B2, B3, M4, M5
> Rung: V3 (reproducible run) — see below for why not V4

## What shipped

| Artifact | What it is |
|---|---|
| `bin/perry-decide` | `bootstrap` / `new` / `supersede` / `status` / `list` |
| `schema/decide-list-contract.md` | `perry-decide/list/1.0`, versioned independently per DESIGN-005 § 4 decision 5 |
| `tests/test_decide_writer.py` | 25 tests |
| `decide/SKILL.md` | `init` now has both halves; Bootstrap checks both files |
| `decide/reference/decisions.md` | step 8 no longer writes `journal/`; the closing "PMO-owned" line corrected |
| `goals/reference/{setup,pivots,phases}.md` | three stale cross-lane write instructions |
| `work/reference/conversational.md` | a fourth, found by the new guard rather than by review |
| `tests/test_ownership.py` | guard over every `*/reference/*.md` |

## The defect this closes

`work/reference/bootstrap.md` refuses to create `DECISIONS.md` and `decisions/`
— correctly, they belong to `decide` — and named a `decide` bootstrap that did
not exist. `decide/SKILL.md § init` created `design/` and said outright that it
"does not create any docs". First-time setup never invoked a `decide`
subcommand. So `adr` step 7, "update the `DECISIONS.md` index", ran against a
file no code path produced, and `decisions.count` was 0 on every Perry project
regardless of how many decisions it had made.

Verified before the fix: `perry-state --json` on this repo reported
`decisions.count: 2` **only because both ADRs and the index were written by
hand**, in a session, by an agent following a procedure that assumed the file
existed.

## Verification performed

Reproducible run, on a throwaway project:

```
new before bootstrap        → refused, names bootstrap, creates nothing
bootstrap                   → decisions/ + DECISIONS.md
bootstrap again             → refused ("one-time step")
new without --type          → refused
new ×2 with --supersedes    → ADR-001 flipped to superseded, `Superseded by:
                              ADR-002` written into the file, both index tables
                              re-rendered
list                        → 1 active · 2 total
perry-lint                  → no finding against DECISIONS.md
```

Run against this repo's real ADRs: both parse, titles resolve, `supersedes` no
longer swallows the `· Superseded by:` half of its own line.

Two behaviours mutation-verified — reverting each fails the test that names it:

- combined-field parsing (`> Supersedes: — · Superseded by: —`)
- `bootstrap` refusing a second run

The cross-lane guard was mutation-verified too, and **failed that check twice
before passing**: its exclusion regex matched `do not` but not `Don't`, and its
matcher compared the exact backticked path, so it saw `` `evidence/` `` and
missed `` `evidence/<YYYY-MM>/retro.md` `` — the form every real instruction
uses. Corrected, it immediately found a fifth stale instruction no reviewer had
reported.

## Why V3 and not V4

No fresh-context reviewer has read this. The rung records what was done, not
what it deserves — recording V4 ahead of the review is the false-record mistake
made earlier in this project and corrected there. A review is warranted before
`perry-goals` copies this shape.

## Known gaps, not defects

- `expire` and `archive` exist as `status --status`, not as named subcommands;
  `decide/SKILL.md`'s index still advertises `--expire` / `--archive` flags on
  `adr`. Reachable, differently spelled.
- Nothing calls `perry-decide bootstrap` automatically from first-time setup;
  `decide/SKILL.md § Bootstrap` prompts for it. Wiring it into the router's
  setup chain is a separate change to a file this task did not own.
