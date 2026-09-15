# TASK-453 — spec

> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Touches architecture: §2, §3, §6 (read only — S1–S7 encode existing rules; no rule text changes)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Track / mode**: main / project
- **Dependencies**: none.
- **Design**: `DESIGN-017 § 5.2` and `§ 6` D1 (amended and locked 2026-09-15).
- **KR linkage**: `P004-O4-KR2`.
- **Verification rung**: V3.

## Why

`ARCHITECTURE.md`'s rules are enforced by nothing: 0 of 97 September result
files carry the compliance block, and `perry-state` cannot see the document.
`DESIGN-017` turns the rules that come from DECIDED sections into structural
checks that run in the full suite before every merge.

## Deliverable

1. **`tests/test_architecture_rules.py`** with S1–S7 as `DESIGN-017 § 5.2`
   defines them, each reading typed facts only (paths, `ast` imports, sizes,
   hashes):
   - **S1** — `viewer/parsers.py` imports nothing from `bin/`.
     **At base this rule is red, and USER-935 (2026-09-15) ruled that the code is
     the violation, not the rule.** `viewer/parsers.py` puts `bin/` on
     `sys.path` (lines 91–92) and imports `lib`, `perry_md_store` and `tables`.
     Implement S1 exactly as written, test its checker on two synthetic sources
     (one with a `bin/` import, reported; one without, clean), and mark the
     live-file case `unittest.expectedFailure` with a reason naming USER-935 and
     TASK-458. The suite stays green while the violation stands, and the day
     TASK-458 lands the case reports an unexpected success.
   - **S2** — no `def parse_` in `bin/` outside `perry_store.py` and
     `perry_md_store.py` (NN-1's own `Check:`).
   - **S3** — every import in `bin/`, `viewer/` and `tests/` is in
     `sys.stdlib_module_names` or resolves inside the repository. On a Python
     without `sys.stdlib_module_names` (3.9, `/usr/bin/python3`) the test
     **skips with a stated reason** rather than passing silently.
   - **S4** — `tests/run` invokes `tests/tree_guard.py` on every exit path
     (NN-5).
   - **S5** — every top-level directory and every `bin/` executable appears in a
     `§ 2` heading or in `bin/perry list`, or on an exempt list declared in the
     test with a reason per entry.
   - **S6** — `ARCHITECTURE.md` ≤ 500 lines; each module document (today
     `bin/ARCHITECTURE.md`) ≤ 600 lines. Tier budgets for prose are `TASK-456`.
   - **S7** — sha256 of `§ 1`, `§ 3`'s `Forbidden` lines and `§ 6` equals the
     `hash:` recorded in the newest `User-confirmed` `§ 8` entry. **While no entry
     carries a hash, the test skips with the reason "no confirmed hash recorded;
     TASK-454 records the first"** — never a silent pass.
2. **A proposed `Check:` line for every `§ 6` rule**, written in the result file —
   not in `ARCHITECTURE.md`. `§ 6` is decided (NN-6); `TASK-454` applies them
   with the user's confirmation.
3. **A result** at `perry/evidence/2026-09/TASK-453-result.md`.

## Files in scope

- `tests/test_architecture_rules.py` (new)
- `tests/durations.json`
- `perry/evidence/2026-09/TASK-453-result.md`

## Bound

```
Enumeration:  S1–S7 of DESIGN-017 § 5.2
Size:         7 rules
Remainder:    rules not derived from a decided section are out of scope
Last element: S7
```

## What it must not do

1. **Must not edit `ARCHITECTURE.md`, `bin/ARCHITECTURE.md`, `bin/`, `viewer/`
   or `schema/`.**
2. **Must not fix a product violation a rule finds.** Stop, report it in the
   result with the evidence, and handle the rule as S1's decision above says.
3. **Must not write the task stores, `linkage.jsonl`, `okr.jsonl`, `phase/`,
   `.perry/events.jsonl` or the journal.**

## Verification

1. **Base check** as the brief states.
2. **`bash tests/run` on the final commit**: no reds beyond the agent's own
   measurement at base.
3. **Mutations**, each on a fresh scratch copy, each red on a named test:
   S1 make the checker skip `lib` imports (the synthetic case turns red); S2 add `def parse_x` to a `bin/`
   tool; S3 add `import yaml` to a `bin/` file; S4 remove the tree-guard call from
   a copy of `tests/run`; S5 add an unnamed top-level directory; S6 grow
   `ARCHITECTURE.md` to 501 lines; S7 on a copy with a fabricated confirmed hash,
   edit `§ 6`. A green mutation is a finding.
4. The S3 and S7 skips print their reasons — quoted in the result.

## Subjective verification

(none)

## Out of scope

- The `§ 8` hash format and applying `Check:` lines (`TASK-454`), the merge-time
  review (`TASK-455`), prose tier budgets (`TASK-456`).
