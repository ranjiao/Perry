# TASK-280 — spec

> Dispatch mode: auto
> Executor: claude-subagent (repository-local, stdlib only, no MCP)
> Estimated cycle: small
> Subjective verification: whether the surviving prose is the argument and not the data
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P2
- **Track / mode**: main / project
- **Dependencies**: `TASK-278`
- **KR linkage**: unlinked

## Why this row exists

`DESIGN-015 § 6` step E: *"`phase/<NNN>-linkage.md` sheds its schema'd half,
keeping the 7 `metric:` arguments."*

Once TASK-277 has imported the records and TASK-278 has moved the six readers to
the store, the document holds a **second copy** of data the store now owns. That
is the violation the whole design exists to remove — and until this row runs, the
two can disagree with nothing detecting it.

**The design is explicit that E may lag** (*"E is separable and can lag; F is
what turns the KR from asserted into measured and should not"*), which is why
this is P2 behind TASK-281's P2-but-load-bearing. It is cleanup, and cleanup done
early is cleanup done twice.

## The distinction this row turns on

`DESIGN-015 § 5.4`: the file **survives with its schema'd half removed — the 7
`metric:` arguments and nothing else. It is NOT a render of the store**, because
a render would put `target` and `current` in a second place, which is the
violation being removed.

So there are three categories and the middle one is the trap:

| | Fate |
|---|---|
| `id`, `tasks:`, `unlinked:`, `agents:`, `projects:` | **removed** — the store owns them |
| the `metric:` prose | **stays** — it is the ARGUMENT for a number, not the number |
| `title:` | **decide, and say why** — it is neither obviously data nor obviously argument |

**A `metric:` field that states a number is doing both jobs at once.** Today's
read like *"6 of 6 (baseline 4 of 6 …). Measured 2026-09-01: … store 255, risks 4
…"*. Removing the whole field loses the reasoning; keeping it whole leaves an
asserted count beside a computed one. **Decide which half survives and say so** —
this is the row's only real judgement.

## Files in scope

- `perry/phase/003-linkage.md` — the file that sheds.
- `perry/phase/001-linkage.md`, `002-linkage.md` — **decide whether they shed too
  and say so either way.** They hold 31 and 11 `id:` entries against 003's 9, and
  they belong to closed phases.
- `tests/` — the guards.
- `schema/state-schema.json` — **read only.** § 5.4 says the file stays `tier: 2`
  with `owner: goals` and its `exclude` from the tier-1 cap is already there. If
  something must change there, **stop and report** — that is the claim surface
  and it needs the user.

## Deliverable

`phase/003-linkage.md` holds argument and no data. Every fact it used to carry
is in `linkage.jsonl`, and nothing reads the file for a fact any more.

## Verification

1. **Before**: enumerate what the file holds by kind, and show every one of those
   records present in the store. **A record in the document with no store
   counterpart is a stop condition, not a rounding** — it means TASK-277's import
   missed something and this row would delete the only copy.
2. **After**: the file parses, `perry-lint --root .` is at 0 errors, and
   `perry-goals krs` still answers. That last one is the real test — it is the
   surface a user reads.
3. **Nothing reads it for data.** After TASK-278 the six readers in § 5.6 point
   at the store; confirm by measurement that none of them still opens this file
   for a fact, and name any that do.
4. **A control**: the `metric:` prose survives byte-identical for whichever part
   you keep. Show it.
5. **The closed phases**: whatever you decide for 001 and 002, show that
   `perry-goals krs --phase 001` and `--phase 002` behave the same before and
   after. A cleanup that silently changes what a closed phase reports is worse
   than no cleanup.
6. **Mutation**: revert the shed and show a named test go red — or state plainly
   that deleting data nothing reads cannot be caught by a test, and say what
   holds it instead. Anchor by line number *with an assert on the old text*;
   clear `__pycache__`; **verify restores against your branch's own base, never
   `main`, which moves.** A green mutation is the finding.
7. Full suite via `tests/run` no redder than the baseline **you measure**. If the
   machine is loaded, timing figures are meaningless — a bare `python3 -c pass`
   measured 4,467ms here at load 114 — so say what the load was.

## Bound

```
Enumeration: grep -c "^\s\+- id:" perry/phase/*-linkage.md
Size:        3 files, 51 id entries on 2026-09-04 — 001 has 31, 002 has 11,
             003 has 9. Plus 003's unlinked list, measured at 100 entries.
This row:    003 certainly; 001 and 002 are DECIDED here and shed only if the
             round argues they should.
Remainder:   `phase/<NNN>-storage-code.md` and the other phase documents are
             untouched — they carry no linkage records. The last element is
             003-linkage.md's final `unlinked:` entry.
```

## Out of scope

- Computing `P003-O3-KR2`. That is step F, `TASK-281`, and the design says F
  must not lag while E may.
- Any change to `schema/state-schema.json`. § 5.4 says nothing needs to move
  there; if that turns out false, it is the claim surface and the user decides.
- Deleting the file. It survives — that is § 5.4's first word about it.
- Backfilling or correcting any record. If the import was wrong, that is
  TASK-277's row, not this one's.
