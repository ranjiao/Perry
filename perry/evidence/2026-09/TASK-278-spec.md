# TASK-278 — spec

> Design: `design/DESIGN-015-linkage-is-a-store.md` (locked 2026-09-02), implementation plan row **C**
> Dispatch mode: manual
> Executor: codex (medium, self-contained: six call sites across four files, no MCP needed)
> Estimated cycle: medium
> Subjective verification: (none) — the mutation test is the acceptance
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: TASK-277
- **KR linkage**: P003-O3-KR2

## Files in scope

- `bin/perry-goals` — lines 1657 and 3033 as of 2026-09-02.
- `bin/perry-task` — line 4491 as of 2026-09-02.
- `bin/perry-lint` — lines 1200 and 1231 as of 2026-09-02.
- `viewer/parsers.py` — line 4503 as of 2026-09-02.
- `tests/` — the mutation guard.

**Re-derive every line number before editing.** Count call sites, never names:
phase 002's most expensive recurring defect was locating an implementation by
grepping its name, and it recurred roughly ten times.

## Deliverable

The six call sites in `DESIGN-015 § 5.6` read `linkage.jsonl` instead of
`phase/<NNN>-linkage.md`.

`bin/perry-task:4491`'s line regex is replaced by `json.loads` — **not by a
second regex**. Its own comment says why the regex existed ("markdown with a
YAML-shaped block in it, not a YAML document"), and that reason is gone once
the source is JSONL. `bin/perry-lint:1231`'s exclusion and `:1200`'s check are
**rewritten against the store, not deleted**.

## Out of scope

- Backfilling the 16 never-asked or 75 declared rows — phase 004.
- `tasks.jsonl`'s `Next action` prose — deferred 2026-09-02, `DESIGN-015 § 8`.
- Any project other than Perry's own.
- `schema/state-schema.json` — row A owns that edit.
- Changing what `add` writes — that is row D, and the order matters.

## Verification

- **The gate must be shown able to go red**: restore one moved call site to
  the document and a named test fails. A pass that was never falsifiable is
  not evidence (phase 003 operating rule).
- `perry-state --section attribution` and `--section linkage` return the same
  numbers before and after: `linked=5`, 75 declared, 16 never-asked.
- `bash tests/run` shows no new failures against the pre-existing baseline;
  name the baseline and the runner, since the two runners disagree.
