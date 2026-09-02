# TASK-263 — spec

> Design: `design/DESIGN-014-how-much-python.md` § 5.1, first step of its implementation plan
> Dispatch mode: manual
> Executor: manual — **a gate result, recorded rather than worked around.** `perry-state --escalation-scan` returns `verdict: refuse`, `refuse: ['evidence/']`, because `## Files in scope` and `## Deliverable` name `perry/evidence/2026-09/TASK-263-result.md` — the file this row exists to produce. The refusal is a false positive: `evidence/` is on `.perry/hook.md`'s list to stop a tool writing into a *foreign* project's evidence directory, not to stop a Perry row producing its own. **The spec was NOT reworded to pass.** `.perry/hook.md` says in its own words that rewording is the cheapest way through and the one thing a gate must never reward, so the wording stands and the row is delegated by hand. Filed as intake 2026-09-02 with a census: 20 of 125 specs are refused, and `diagnose` / `design/` / `evidence/` account for 14 of those causes by matching a citation rather than a write. Original routing, kept for a session where the gate can tell the two apart: `claude-subagent` — measurement over this repository's own source, no MCP, no production code.
> Estimated cycle: medium
> Subjective verification: whether the category boundary the report draws is the one DESIGN-014 § 5.1 means — a human reads the report and says so
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked — this serves `DESIGN-014`, not a phase-003 KR
- **Verification rung**: V4

## Why

`DESIGN-014 § 5.1` splits `bin/` into three categories. Two of its rows are not
measurements but admissions: `bin/perry-task` is listed as **"part of 7,522"**
and `bin/perry-lint` as **"part of 4,483"**, because neither file is one thing
and nobody has counted which part is which. Together they are roughly 40% of
`bin/`.

Until those two rows carry a number, § 5.1's conclusion — that the 10:1 ratio
is one condemned layer plus one unwritten authoring surface, not a pile of
tools that should not exist — rests on an estimate for its two largest files.

## Files in scope

**This row measures; it does not change behaviour.** The only file it creates is
its own report.

- `bin/perry-task` — read.
- `bin/perry-lint` — read.
- `perry/evidence/2026-09/TASK-263-result.md` — written.

## Deliverable

`perry/evidence/2026-09/TASK-263-result.md`: a per-call-site attribution of
`bin/perry-task` and `bin/perry-lint` into `DESIGN-014 § 5.1`'s categories —
**A** determinism-bearing, **B** representation layer, **C** code standing in
for prose — with a line count per category per file, and the total that replaces
"part of 7,522" and "part of 4,483".

Every line of both files lands in exactly one category or in an explicitly named
fourth bucket (imports, CLI plumbing, docstrings). **A leftover bucket is a
legitimate result; a silently-dropped remainder is not** — the category counts
plus the leftovers must sum to the file's line count, and the report must show
that sum.

## Out of scope

- Changing any behaviour in either file. This row is a measurement.
- `schema/state-schema.json`, `claims`, and every other declaration file.
- Deleting or thinning anything — `TASK-265` carries the `perry-state` thinning,
  and the category-B deletions are `ADR-011`'s, not this row's.
- The other tools in § 5.1's tables; their numbers are already whole-file counts.
- Any project other than Perry's own.

## Verification

- **By call site, never by grep over a name.** This is the phase's operating
  rule and it is also the row's title: phase 002's most expensive recurring
  defect was locating an implementation by grepping its name, once over-counting
  and once missing a whole second reporter. State the method you used and why it
  is call-site-based.
- The three category counts plus the named leftover bucket **sum to the file's
  total line count**, shown for each file. An unexplained remainder fails.
- Every attribution is reproducible: for each category, name at least three
  concrete line ranges and why each belongs there, so a reader can check the
  rule rather than trust the total.
- Ambiguous regions get their own list with the ambiguity stated, not a coin
  flip. A function that both validates against the schema (A) and renders a
  drift table (B) is the case to expect.
- The report ends with the two sentences that would replace `DESIGN-014 § 5.1`'s
  "part of 7,522" and "part of 4,483" cells, written so they can be pasted in.
  **Do not edit `DESIGN-014` yourself** — `design/` belongs to the `decide` lane.
