# TASK-216 — result: the foreign-write guard reads the summary tables too

> Branch `coding/task-216-ownership-guard`. Rung **V3**. Measured 2026-08-29.

## The defect, in two halves

`tests/test_ownership.py`'s foreign-write scan is the mechanical half of the
signed hand-off contract — the one rule `perry-lint` cannot check and
`SKILL.md § The hand-off contract` says shows up later as silent cross-lane
writes. It had two blind spots that compound:

1. **It scanned `<lane>/reference/*.md` only.** Procedures live there, which is
   why the original scan looked there — but a lane's `SKILL.md` carries the
   summary **table**, and a summary table is exactly where a stale ownership
   claim survives longest: read on every invocation, edited least.
2. **`WRITE_VERBS` matched `write` and not `writes`.** A summary table is
   written in the third person, so *"`work` writes `DECISIONS.md`"* walked
   straight past a guard built to catch that sentence.

Either alone would have hidden the defect. Together they made the guard blind
to its own subject.

## Measured before changing anything

| scan | offenders |
|---|---|
| shipped verbs, `reference/` only | **0** |
| widened verbs, `reference/` only | **1** — one false positive |
| widened verbs, `reference/` **+ `SKILL.md`** | **2** — both false positives |

**A correction to this row's own record.** The deliverable predicts **3** at the
widest, *"`goals/SKILL.md:126` (the true positive, fixed 2026-08-28) plus
`decide/SKILL.md:26`"*. It is 2, because that true positive was already
corrected in `2e41336` before this row was worked. The row's number described
the tree as it stood when the row was written. The true positive is therefore
reached by **mutation** rather than by the scan, which is what the row's own
Verification asks for.

## The two carve-outs, both measured false positives

- **`no longer`** — `work/reference/subcommands.md:424` reads *"**`work` no
  longer writes `DECISIONS.md` or `decisions/` at all.**"* That is the refusal
  the contract asks for. The existing `\bnot\b` does not cover it.
- **`hands off`** — `decide/SKILL.md:26` reads *"`design` hands off to `pmo`"*.
  That is the hand-off, not the write. The shipped carve-out had
  `hand (it |the |off)`, so it matched `hand off` and not `hands off` — **the
  same third-person blind spot as the verb list, one clause over.**

## Verification — the row's own four, all run

| mutation | result |
|---|---|
| revert the `goals/SKILL.md:126` correction | **RED** — `goals/SKILL.md:126 → writes evidence/<YYYY-MM>/retro.md` |
| drop the `no longer` carve-out | **RED** — the false positive returns |
| drop the `hands off` tolerance | **RED** — the false positive returns |
| **narrow verbs + the real defect restored** | **GREEN** |

The last is the decisive one. With the shipped verb list and the actual defect
put back, the guard reports nothing — which is the state this repository was in
while `goals/SKILL.md` claimed `evidence/retro.md` for the wrong lane and the
correction sat two files away in `goals/reference/phases.md:229`.

Each mutation restored from a byte copy and the suite re-checked green.

## What changed

- `lane_pages()` returns `<lane>/reference/*.md` **plus** `<lane>/SKILL.md`.
- `WRITE_VERBS` takes the `s` on every verb.
- `CARVE_OUT` is a named constant rather than an inline regex, with the two new
  entries documented as the measured false positives they are.
- The test is renamed `test_no_lane_page_instructs_a_write_it_may_not_perform` —
  it no longer says "reference page", because it no longer reads only those.
- Offender lines report the path relative to `$PERRY_HOME`, so a `SKILL.md`
  offender is not mislabelled `<lane>/reference/SKILL.md`.

## Suite, both runners

| runner | result |
|---|---|
| `bash tests/run` | 3 modules red / 5 failures |
| `python3 -m unittest discover -s tests` | 2786 tests / 8 failures |

Identical sets to `45a355d`, and the test count matches base exactly because
this change adds no test file — it widens one that already existed. This change
adds no failure under either runner.
