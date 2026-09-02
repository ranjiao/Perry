# TASK-284 — spec

> Dispatch mode: auto
> Executor: claude-subagent (procedure + tooling in this repository; stdlib only, no MCP)
> Estimated cycle: medium
> Subjective verification: which of the three fixes to take is a judgement — say which and why the others were left
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P0
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked — the skill's own quality, no phase-003 KR covers it
- **Verification rung**: V4

## Why this is P0

**A spec written by following the documented procedure disarms the dispatch
safety gate, and the failure is indistinguishable from a clean pass.**

`work/reference/subcommands.md § add-task` step 3 says the spec file contains
"the same schema" as the journal block. `perry-task add` renders that block as
**bullets** — `- **Deliverable**: …` — verifiable in
`perry/journal/2026-09/2026-09-02.md` around the `### TASK-283` entry.
`viewer/parsers.py:2353 § _section` matches only `^## <heading>`, so a bullet is
invisible to it. `scan_spec_escalations` then reports `touches: {}` and
`verdict: pass`, having scanned 35 high-stakes fragments against nothing.

**Measured 2026-09-02:** 129 spec files; 84 carry a `## Deliverable` or
`## Files in scope` heading; **45 do not**, and every one of the 45 returns
`verdict: pass` with `touches: []`. That is 35% of this project's specs passing
the safety gate because the gate cannot see their scope.

Found by doing exactly what the procedure says: four `DESIGN-015` specs written
to the documented schema all scanned empty; rewritten with `## ` sections, one
of them **correctly refused** on `claims` and `state-schema.json`.

## Files in scope

- `work/reference/subcommands.md` — `add-task` step 3.
- `viewer/parsers.py` — `_section` and `scan_spec_escalations`, if the fix is
  reader-side.
- `bin/perry-lint` — if the fix is a report.
- `tests/` — the guard.

Re-derive line numbers before editing.

## Deliverable

A spec written by following `add-task` is **scannable**. Three fixes are
available; take one, and say why you left the others:

1. **Procedure-side** — `add-task` names the required `## ` shape for
   `Files in scope` / `Deliverable` / `Out of scope` **and says why**, so the
   author knows the gate depends on it. Cheapest; does nothing for the 45
   existing specs.
2. **Reader-side** — `_section` also reads the bullet shape the tool actually
   renders. Fixes the 45 at once; widens a parser used well beyond this gate,
   so check every other `_section` caller before choosing it.
3. **Report-side** — `perry-lint` reports a spec whose scanned sections are
   absent, so a silent empty scan becomes a visible finding. Does not prevent
   it; makes it impossible to miss.

Whichever is chosen, **a spec must not be able to present zero scope to the
gate without something saying so.**

## Out of scope

- **The gate's citation-vs-write blindness** — `diagnose` matching a filename,
  `evidence/` matching a row's own output. That is `TASK-290`, a different
  defect in the same tool. Fixing either alone leaves the gate wrong; do not
  fold them together.
- **Rewording any existing spec to pass.** `.perry/hook.md` says rewording is
  the one thing a gate must never reward.
- `schema/state-schema.json` and any declaration file.
- Any project other than Perry's own.

## Verification

- Re-run the census: 129 specs, count those without a scannable heading. It is
  **45** today. After the fix, that number is 0, or every member of it is
  reported by something.
- A spec written by following `add-task` verbatim, from scratch, scans with a
  non-empty `touches` when its scope names a high-stakes fragment. Write one
  and show it.
- **Mutation**: strip the `## ` headings from a currently-scannable spec and the
  new check goes red. A green mutation is a finding either way.
- If fix 2 is chosen: enumerate every `_section` caller and show none of them
  changes answer. That parser is used far beyond this gate.
- `bash tests/run`: baseline failure count and the runner that produced it.
  Note that `tests/test_parsers.py` is currently red for an unrelated reason
  tracked as `TASK-292`.

## Bound

The finite set: **one procedure section (`add-task` step 3), one reader
(`_section` / `scan_spec_escalations`), one census (129 specs, 45 unscannable).**
Size 3. The round ends when the census number is driven to 0 or made visible.

A fourth fix somebody prefers is a new row, not an extension. `TASK-290`'s
defect is explicitly out of the set — if you find yourself fixing intent
matching, you have left this round.
