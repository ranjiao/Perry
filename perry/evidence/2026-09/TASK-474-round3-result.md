# TASK-474 round 3 result — USER-973 principle A

Date: 2026-09-20. Author: PMO Agent (Claude Opus 5), the same session that wrote
rounds 1 and 2 and their defects. Not reviewed: round 3's V4 is owed. Nothing was
run against this repository's own `perry/` state.

- **Base:** `818da1be` (`main`, after USER-973 and USER-974 were answered).
- **Branch:** `coding/task-474-round3`.
- **Under repair:** two V4 FAILs, `TASK-474-v4-review.md` and
  `TASK-474-round2-v4-review.md`, escalated as USER-973 rather than a third
  round dispatched on a guess.

## The principle, and what it cost

USER-973 chose **A: the writer normalises** — full A, not the cap-only variant
this PMO recommended. `phase new` now writes `"\n".join(body.splitlines()) +
"\n"`, so every boundary `splitlines()` knows becomes LF and the bytes on disk
carry only LF. The two readers that disagreed — `read_bytes().decode()` in
`perry-goals`, `read_text()` in `perry-lint` — cannot disagree about a document
this writer produced, whichever call they use.

**The accepted cost, stated in the answer**: the writer rewrites the author's
bytes, which `Okr.render` declines to do for `OKR.md` and says so in its
docstring. That is now a recorded decision rather than an open objection.

**What full A bought over the narrowed variant**: the reviewer's R3. `close`
read with `read_text()` and wrote the translated string back, so a CRLF document
lost 179 of 180 line terminators while `close` claimed to change one line, and
the snapshot was not a byte copy. `phase_text()` now decodes without
translating, everywhere in the lifecycle: **what Perry did not write, Perry does
not rewrite.** The narrowed variant would have left R3 open.

## The guard had to change, and was made positive, not deleted

Round 2 added `test_the_phase_functions_never_call_splitlines`. Principle A
requires exactly one such call. An absence assertion would have forced the
principle to be implemented somewhere it does not belong, or the guard removed.

It now pins the **count and the site**: exactly one, and it is the normaliser
inside `new`. A second guard states that no phase reader calls `read_text()`.
This is the shape USER-974's answer asks for in general — assert the rule, do
not enumerate ways around it — applied here.

## Mutation proof

Seven mutants; `__pycache__` purged and the clock advanced past a whole second
on both sides; every file restored and md5-verified.

| Mutant | Result |
|---|---|
| N1 normaliser removed | killed |
| N2 normaliser handles CRLF only | killed |
| N3 `close` reads with translation | killed |
| N4 splice drops the line's CR | killed |
| N5 cap counts `splitlines()` again | killed |
| R1 `activate`'s gate ORDER reverted | **survived → fixed → killed** |
| G1 the positive guard weakened | survived (see below) |

**R1 is the finding.** It is TASK-474's F5, and round 2 never actually fixed it.
Round 2's mutant for F5 replaced `if active:` with `if False:` — it **deleted**
the gate rather than reordering it, killed on the gate's existence, and was
reported as covering the ordering fix under a "no survivors" heading. Round 2's
reviewer caught the mislabelling; this round reproduced it, and the regression
test that was missing now exists: when the target is scored **and** another
phase holds the pointer, the refusal must name the phase holding the pointer.
With that test, reverting the order exactly goes red.

**G1 is not a finding, and the first version of it was badly aimed.** Weakening
`assertEqual(len(sites), 1)` to `assertLessEqual(..., 9)` without changing the
code survived — nothing could have detected it, because the code was unchanged.
Re-aimed, weakening the guard **and** adding a second `splitlines()` also
survived. That is true of any suite: a test edited to permit a defect permits
it. Guarding the guards is infinite regress; the mechanism for a weakened test
is a fresh reviewer reading the diff, which is what V4 is. Recorded rather than
chased.

## Suites

`PERRY_PROJECT` and `PERRY_HOME` unset, in this worktree: **157 modules / 4432
tests / all green**, tree guard clean, `git diff --check` clean.

## Not claimed

- The slow tier was not run here.
- No V4. Round 3's independent review is owed.
- No live use: phase 004 is still active, phase 005 does not exist.
- **Prose rules remain weakly guarded.** The sibling row TASK-469 records the
  same limit in detail: a rule sentence can be kept verbatim and taken back by
  a clause after it, and no string test enumerates English. This row's rules
  are mostly code, so it is less exposed — but `phase_text`'s docstring and the
  normaliser's comment are prose, and nothing checks that they still describe
  what the code does.
