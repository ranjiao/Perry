# TASK-201 — the escalation gate is half-internationalised and drops short fragments silently

Dispatch mode: auto
Verification: V3 · Priority: **P0**
Re-verified: 2026-08-28 against `94aade4`

## Why P0

The escalation gate is what stands between a dispatched agent and a high-stakes
operation. **Both defects below make it quietly pass things it should refuse**,
and both were found by TASK-200 while extracting a role card, not by any test.

## Defect 1 — half the pair is translated

`viewer/parsers.py:3347-3348`:

```python
ESCALATION_TOUCHES  = ("Files in scope", "Deliverable")
ESCALATION_DISCLAIMS = "Out of scope"
```

Those are the literal headings the scan reads out of a spec. And in
`schema/state-schema.json § i18n.headings`:

```
High-stakes operations  →  {'zh': ['高风险操作']}     ← translated
Files in scope          →  (none)
Deliverable             →  (none)
Out of scope            →  (none)
```

**The hook's side is internationalised and the spec's side is not, so a spec
written with Chinese headings scans clean** — no touches found, nothing to
refuse. Not hypothetical: `~/proj/gimegime-pmo`'s document language is 中文, and
it is the project TASK-077 is meant to run against.

`heading_is` and `_column_index` already exist for exactly this. **Find out
whether the scan can go through them rather than through literal strings** — a
second translation table would be the defect this repository pays for most.

## Defect 2 — a dropped fragment raises no warning

```python
:3152   if len(frag) > 2 and frag not in out:          # escalation_fragments
:3238   card.escalate_unextractable = [b for b in card.escalate_lines
                                       if not _BACKTICKED.search(b)]
```

`escalate_unextractable` asks **"does this line have a backtick"**. It should
ask **"did this line produce a fragment"**. A line carrying only `` `下单` ``
has a backtick, so it is not reported — and the `len > 2` floor drops it, so it
contributes nothing to the union. **Silent.**

DESIGN-006 § 7 named this failure class and shipped the backtick rule as its
fix. **This is the same class arriving through the hole that fix left.**
TASK-200 measured **18 of 20** Chinese trading verbs affected.

**The floor itself is an ASCII assumption** — `sh`, `rm` are 2 chars and noise;
`下单`, `平仓` are 2 characters and whole words. `_ESC_WORD` at `:3277` was
*deliberately* written ASCII-only so a CJK token would match unguarded, with a
comment naming the `下周期` / `next cycle` asymmetry. **The two decisions
contradict each other and the comment at `:3277` is the one that thought about
it.** Decide what the floor should be and say why — this is the judgement call
of the row, and "keep 2 for ASCII, no floor for CJK" is one answer among
several.

## What to build

1. The three spec headings resolve through the same i18n path
   `High-stakes operations` already uses.
2. `escalate_unextractable` reports a line that produced no fragment.
3. Whatever you decide about the floor, with the argument in the code.

## Files in scope

`viewer/parsers.py`, `schema/state-schema.json § i18n.headings`, `tests/`.

## Out of scope

- `bin/perry-state:1954` scanning the **flat** union rather than the row's own
  `Role:` — TASK-200 found that is **correct by accident and load-bearing**
  (narrowing it breaks the cross-role seam catch). Do not touch it; a row exists
  to pin it with a test.
- `.perry/hook.md` and `packs/*/roles/*.md` — content, not mechanism.
- `perry/` — read-only.

## Verification

1. **A fixture spec with Chinese headings**: refused before your change only if
   the fragment happens to appear anyway — show the before/after verdicts
   explicitly, because "it now refuses" is worthless without "it passed before".
2. A `Must escalate` line whose only backticked token is 2 characters is
   reported as unextractable. **Assert the warning, not just the union.**
3. **Mutation with counts** for each of the two fixes.
4. `perry-lint`: 0 errors, 3 warnings, 194 records, 0 drifted, **risks store 4
   records 0 drifted** — unchanged.
5. Suite: **88 modules, one red** (`test_diagnose`).

**Do not run `perry-conform declare`.** Do not `git push`. Do not touch `main`.
