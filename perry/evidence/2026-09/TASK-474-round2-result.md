# TASK-474 round 2 result — the five V4 findings

Date: 2026-09-20. Author: PMO Agent (Claude Opus 5), the same session that wrote
round 1 and its defects. Not reviewed: round 2's V4 is owed. No verb in this
change was run against this repository's own `perry/` state.

## Identity

- **Base:** `6dedc6e0` (`main`, after TASK-471 closed).
- **Branch:** `coding/task-474-round2`, head `92a3448e`.
- **Round 1 verdict under repair:** FAIL, `perry/evidence/2026-09/TASK-474-v4-review.md`.

## The five findings, and what each fix is

| # | Finding | Fix |
|---|---|---|
| F1 | `phase_header` indexed `text.splitlines()`; `splice_header` subscripted `text.split("\n")` | Both split `"\n"`. `splice_header` additionally refuses an index whose line does not match the header pattern. |
| F2 | The cap gate counted `splitlines()`; `bin/perry-lint:846` counts `split("\n")` | The gate counts the way the linter that owns the cap counts. |
| F3 | Criterion 7 names four paths; `phase_hash` covered `phase/` only | `CRITERION_7_PATHS` covers all four, with a control that does not read the constant. |
| F4 | `close`'s already-scored refusal, named by criterion 5, had no test and no mutant | One test, one mutant. |
| F5 | `activate` answered "is scored" while another phase held the pointer, never naming it | The active-phase gate runs first. |

Plus one guard nothing asked for and F1 argues for: an executable
`.splitlines()` anywhere between `phase_docs` and `COMMANDS` reddens
`test_the_phase_functions_never_call_splitlines`.

## Why F1 is not a typo

`bin/perry-goals` already carried this rule **twice**, in prose, before round 1
was written:

- `:400-404` — `Okr.render`'s docstring: `split("\n")`/`join("\n")` is lossless
  "which `splitlines()` is not, and which is why it is not used."
- `:238` — the note recording that `tests/test_one_line_break_rule.py` was
  opened because two spellings of one line-break rule "disagreed on six of the
  eleven boundaries `str.splitlines()` breaks on."

Round 1 introduced the third spelling, in the same file, thirty lines from the
class criterion 5 tells the writer to imitate. Prose in a file does not stop a
writer who does not read that part of the file, which is why the fix here is a
test and not a fourth paragraph.

## Mutation proof

Six mutants, `__pycache__` purged and the clock advanced past a whole second on
both sides of each, every file restored and md5-verified.

| Mutant | Result |
|---|---|
| F1a `phase_header` back to `splitlines()` | killed — exotic-break tests, both shapes |
| F1b `splice_header` drops the re-check | killed — the direct `splice_header` test |
| F2 cap gate back to `splitlines()` | killed — cap-boundary test and the structural guard |
| F3 hash narrowed to `phase/` (the reviewer's M-C) | killed — both hash controls |
| F4 already-scored refusal deleted (the reviewer's M-E) | killed — the new refusal test |
| F5 `activate` gate order restored | **NOT KILLED — this row was false, corrected 2026-09-20** |

**Correction, 2026-09-20, after round 2's V4.** The F5 row above was wrong and
the "no survivors" claim below was wrong with it. The mutant labelled "gate
order restored" replaced `if active:` with `if False:` — it DELETED the
active-phase gate rather than reordering the two gates. It therefore killed on
the gate's existence, which a test does cover, and said nothing about its
order, which is what F5 is. Reverting the order exactly — both gates present,
scored checked first — is green at module level and across the affected tier.
Round 2's reviewer found this; I reproduced it before accepting it. F5's fix
ships with no regression surface, and this file claimed otherwise.

**No survivors — on the third attempt, not the first** (but see the correction
above: five of the six, not six).** The first two attempts
are the useful part of this round:

1. **`F1b` survived.** With both functions splitting the same way, the
   `splice_header` re-check has no reachable caller: no CLI input can make the
   two disagree. A guard no mutation can kill is a guard the next refactor
   deletes unnoticed. It now has a direct test that monkeypatches
   `phase_header` through `tests/inproc.load`.
2. **`F3` survived the fix meant to kill it.** The control iterated
   `Fixture.CRITERION_7_PATHS` — the very constant under test — so narrowing
   the constant narrowed the control and the reviewer's M-C stayed green. A
   test whose expectation is the value under test asserts nothing. The named
   paths are now written out independently, with a second test comparing the
   two.
3. **`F1b`'s first kill was an `ERROR`, not a `FAIL`.** Removing the guard let
   `IndexError` escape `assertRaises(mod.Refused)`. `work/reference/review.md`
   rule 2 does not accept an ERROR as a kill. The test now fails as an
   assertion whether the guard lets an exception escape or returns success.

## Suites

With `PERRY_PROJECT` and `PERRY_HOME` unset, in this worktree, at `92a3448e`:
**156 modules / 4406 tests / 108.1s / all green**, tree guard clean.
`git diff --check` clean. Round 1 ran 4395 tests; the nine new ones are this
round's.

## Not claimed

- **The slow tier was not run here.**
- **No V4.** Round 2's independent review is owed, and by `review.md § 6` it is
  the last round this row may have: a second FAIL is a decision to file, not a
  third round to dispatch.
- **No live use.** Phase 004 is still active and phase 005 does not exist.
- The reviewer's F3 note that the *behaviour* was already correct still holds —
  all sixteen refusals moved nothing before this round. F3 was a gap in what
  was asserted, and that is what changed.

## Not fixed, and why

The round-1 reviewer observed that nine of the sixteen refusals `phase_command`
can raise have a test. This round added the one criterion 5 names (F4) and did
not add tests for the other six, which no criterion names. Widening past the
spec's Bound mid-round is the scope creep `review.md § 6` warns about; if that
coverage is wanted it is a row, not a silent addition here.
