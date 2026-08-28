# TASK-210 — the id scanner reads inline code as prose

Dispatch mode: auto · Verification: V3 · Re-verified 2026-08-28 against `ece2a58`

## The measurement

`perry/evidence/2026-08/TASK-158-spec.md` quotes one regex twice — **line 18
inside a ``` fence, line 25 inside `inline backticks`**:

```
$ perry-explain Z0-9
  defined    NOWHERE — this ID is referenced but never defined
  mentioned  perry/evidence/2026-08/TASK-158-spec.md:25
```

**Line 25 only.** The scanner already knows code is not prose — `bin/perry-explain:356`
skips a fenced block with `if raw.lstrip().startswith("```")`, **a line-based
test that inline spans never reach.**

`Z0-9` is a fragment of `[A-Z][A-Z0-9]{1,9}-\d{1,4}`. **It is not a borderline
id; it is a character class.**

## Why this is P1 and lands before TASK-179

TASK-179 asks you to choose how to pay for ids quoted in evidence records. Its
three options all treat the dangling entries as **real citations**. At least one
is not:

```
FOO-001   a spec's example of an unknown family — a real mention
Z0-9      a regex fragment inside a code span — NOT AN ID
RX-005 · USER-904 · TASK-007 · TASK-9999   real mentions
```

**Removing the false positives costs nothing**, because a genuine citation
appears in prose somewhere too and the scanner still sees it there.
`TASK-179` now depends on this row.

## What to decide and state

- **Where the skip lives.** `walk_md` is in `bin/lib/__init__.py:904`; the fence
  test is in `perry-explain`. If `perry-diagnose` or `perry-lint` scan
  independently, **an inline-span skip in one of them is the asymmetry TASK-202
  just spent a row removing.** Grep for the scan, not for the name.
- **Nested and unbalanced backticks.** ``` ``a `b` c`` ``` is legal markdown and
  an unbalanced one is common in prose. Say what you do with each.
- **Whether a fenced block's skip should move too.** Line-based works today
  because fences start a line. It is not obviously wrong; say whether you left
  it.

## Files in scope

`bin/perry-explain`, `bin/lib/`, `bin/perry-diagnose` **if** the enumeration
shows a second scanner, `tests/`.

## Out of scope

- TASK-179's decision itself. **Narrow the list; do not decide it.**
- `perry/` — read-only. The documents that legitimately quote ids stay as they
  are; that is the whole point.

## Verification

1. `perry-explain Z0-9` resolves to **nothing at all** — not "defined nowhere",
   but absent from the id set.
2. **The dangling list before and after**, both printed. Only the code-span
   entries leave.
3. A genuine citation that appears **only** inside a code span: say what
   happens and why that is right. This is the case the change could get wrong.
4. Mutation with counts.
5. `perry-lint` unchanged; suite **90 modules, one red** (`test_diagnose`) —
   and note that `test_diagnose`'s dangling assertion **may change count**. If
   it does, that is this row working; report the new list rather than adjusting
   the test to fit.

**Do not run `perry-conform declare`.** No push. No `main`.
