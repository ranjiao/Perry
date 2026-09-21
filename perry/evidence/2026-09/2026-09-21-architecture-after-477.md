# ARCHITECTURE.md after TASK-477 — 2026-09-21 (USER-989)

USER-989 records the exact OQ-1 sentence swap, proposed in chat and approved
("两处都改") before the edit was made. The preamble comment update is
descriptive (outside the eight sections).

Candidate `pmo/architecture-after-477` `5651e663466cbad0da5e94b1d402bb2f9e24a37b`,
base main `5898c0ed`: `ARCHITECTURE.md` +12/−8, 461 lines, eight sections.

## Architecture review (fresh context) — summary of the returned block

Reviewer: independent, fresh context, read-only; 2026-09-21T19:35:32+0800.
Triggers: root architecture edit TRUE; the other five FALSE. Unresolved: none.

- NN-6 (`ARCHITECTURE.md:293-297`, schema `files[id=architecture].note`) —
  holds: USER-989 (`perry/asks.jsonl:90`) quotes old and new sentence; head §7
  matches word for word; the only §7 change is that swap; OQ-1's original text
  and OQ-2…OQ-8 kept; §6 byte-identical; §8 gains an entry, loses nothing.
- §1, §3 Forbidden, §5, §6 NN-1…NN-5 — not touched. Pre-existing tension noted:
  §3 line 167 ("An agent writing `ARCHITECTURE.md`. This file is the user's.")
  against NN-6 and the schema note (DESIGN-017 D2 / TASK-454 territory).
- New OQ-1 sentence (311-313) — holds: TASK-451/452/477 done; `a2a12a8f` on main
  (the durations commit after integration `9259f0c6`, matching OQ-1's citation
  convention); `bin/perry-diagnose:2642-2646` prefixes by anchor via
  `lib.anchor_root`; the root ARCHITECTURE.md is not among perry-diagnose's 21
  orphans on this repository.
- "Last reader that ignored the code anchor" — holds: perry-state (1483,
  1751-1753), perry-lint (4993, 5706), perry-diagnose (2642), parsers
  `load_snapshot` (5235) honour it; `perry-task:6722/8345`, `perry-goals:1215`
  and `parsers.py:5641` call `load_snapshot` without `code_root` but none
  consumes `arch_meta` (only perry-state, 1987/2192), so no output depends on it.
- Preamble (26-29) — holds (schema anchor code; `--section architecture` exists
  true, section_count 8; perry-diagnose owns it; §7 OQ-1 closed; "then
  anchored" is true history). Line 17's "`exists: false` until 2026-09-09" was
  already imprecise at base; the new paragraph fills the gap.
- 500-line cap (461) and eight sections — hold.

Decision: **PASS**. User decision required: none (optional follow-up: §3:167
wording against NN-6, pre-existing).
Not checked: the chat behind USER-989 (relied on asks.jsonl:90); no suite run;
other-repo mentions of ARCHITECTURE.md only where relevant.

## Acceptance

| Step | Result |
|---|---|
| Full gate | `merge-check --base main delivery=pmo/architecture-after-477 --tier full`: green on tree `ab4b845d`, base `5898c0ed`, 158 modules / 4,462 tests |
| Durations | on a separate `integ/arch-after-477` `3d4f0906` (candidate ref left at `5651e663`); `--verify-receipt` VERIFIED |
| Slow gate | `tests/run --tier slow` at `3d4f0906`: 162 modules · 4,565 tests · all green |
| Merge | refs rechecked; `git merge --ff-only integ/arch-after-477` → main `3d4f0906` |
