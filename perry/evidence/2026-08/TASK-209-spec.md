# TASK-209 — the store-drift census covers two of six stores, so ADR-007's guarantee is checked for two

> Serves **P003-O1-KR2** (`phase/003-storage-code.md`): *stores for which one run of `perry-lint --root .` prints a drift verdict.* Target **6 of 6**, baseline **2 of 6**.
>
> Dispatch mode: auto
> Executor: claude-subagent (codex ruled out by the user on 2026-08-28 — quota)
> Estimated cycle: small
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Rung**: V4
- **Dependencies**: —
- **KR linkage**: `P003-O1-KR2`

## Baseline, measured 2026-08-28

One run of `perry-lint --root .` on this project prints:

```
· store: 220 record(s), 0 row(s) drifted            ← tasks.jsonl   ✅ a drift verdict
· risks store: 4 record(s), 0 risk(s) drifted       ← risks.jsonl   ✅ a drift verdict
· no `intake.jsonl` — drift ... is unchecked, not clean   ← an ABSENCE line, not a drift verdict
· no `asks.jsonl`  — drift ... is unchecked, not clean    ← an ABSENCE line, not a drift verdict
                                                     ← okr.jsonl        NOTHING
                                                     ← .perry/config.jsonl  NOTHING
```

**Two of six.** And the two that print nothing already have working
comparators: `perry-okr diff` and `perry-config diff` both ran clean on
2026-08-28 (`"identical": true`, exit 0). `grep -n "perry-okr\|perry-config"
bin/perry-lint` returns **zero matches** — the census calls neither.

> **The row's title is off by one.** It says *"covers `tasks.jsonl` only"*; the
> census covers tasks **and** risks. The KR's baseline of 2 is the correct
> number. Recorded rather than silently corrected.

## Files in scope

`bin/perry-lint`, and its tests.

## Deliverable

One run of `perry-lint --root .` prints a drift verdict for all six declared
stores. `okr.jsonl` and `.perry/config.jsonl` are wired to the comparators that
already exist rather than growing a third and fourth implementation of the same
comparison — that duplication is the defect ADR-004 and this whole phase exist
to stop.

**Keep the absence line distinct from a clean verdict.** *No store* and *clean*
are different answers, and `perry-lint` already says so for `intake.jsonl` and
`asks.jsonl`. Do not collapse them to make the count reach six.

## Verification — V4

1. `perry-lint --root .` prints a verdict line naming each of the six stores.
2. **Mutation, once per newly covered store**: hand-edit a real cell in
   `OKR.md`, run the census, see it go red; restore. Same for
   `.perry/config.md`. A census that cannot be shown to fail for a store is not
   covering it (phase #002 lesson 4) — and this is exactly how `P002-O1-KR3`
   scored 0.33: its metric said "reported" without saying by what, and nobody
   edited a cell in each file for nine days to find out.
3. Removing a store file still reports `unchecked`, not `clean`.
4. `python3 -m unittest discover -s tests` green.

## Out of scope

- Making `intake.jsonl` and `asks.jsonl` exist — **TASK-203** and its follow-up.
  This row makes the census *cover* six stores; two of them will honestly report
  as absent until those rows land, and that is the correct output, not a gap.
- `P003-O1-KR3`, which asks whether each store reports `unchecked` when removed.
  Currently **zero tasks**, and it stays that way until someone opens one.
