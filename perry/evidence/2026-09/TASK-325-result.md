# TASK-325 — result

> Branch: `coding/task-325-summaries`. Baseline: `main` at `a6ca21f`.
> Instrument: `perry/evidence/2026-09/TASK-325-census.py`, committed alongside.
> Status: IN PROGRESS — this file is committed early on purpose (TASK-309).

## 0. The worktree was not cut at the baseline

The tool cut this worktree at **`d49964e`**, an ancestor of `main` and 96 files
/ ~17,900 lines behind it. `d49964e` is the commit five of tonight's rows quote
as their measurement point, so it is not a random ref — but it is not the
briefed baseline. Everything below was done on a branch cut from `main` at
`a6ca21f`, stated here because the brief asked for the commit to be named
rather than assumed.

## 1. Re-derivation of the filed numbers

Re-measured on `a6ca21f` with the committed census script. Every figure in the
brief holds:

| claim | brief | re-measured on `a6ca21f` | verdict |
|---|---|---|---|
| rows total | 319 | **319** | holds |
| open rows | 114 | **114** | holds |
| rows carrying a summary | 49 | **49** | holds |
| open rows carrying one | 25 | **25** | holds |
| open rows blank | 89 | **89** | holds |
| `--summary` instructions in `work/reference/*.md` | zero | **zero**, across the 8 files that mention the word | holds |
| `perry-lint` checks on the field | zero | **zero** — all 10 mentions are prose or `check_claims`' own summary dict | holds |

Two corrections, neither of which changes the work:

- **The spec's `## Backfill` prose says "90 open rows are blank"; its own
  `## Bound` says 89.** 89 is right. The brief carried the correct figure.
- The spec's "40 of 49 under a wider pattern" re-measures to **39 of 49** with
  a slightly different instrument (id / backtick / path / `.md` / `.py`). This
  is instrument spread, not disagreement, and the conclusion is unchanged —
  except that the conclusion drawn from it is wrong, which is §2.

## 2. THE FINDING: the diagnosis in the spec is not supported by the data

The spec's causal claim is that **"the field degraded into a second title"**.
Measured across all 49 summaries on the board, that is false. Not one of them
is structurally a second title:

```
open rows by rule:
  missing        89
  repeats-title   0
  no-sentence     0
  fragment        0
```

The 49 that exist are, as a population, good: shortest 132 characters / 22
words, median 485 characters / 84 words, and **every single one contains at
least one complete sentence**. There is no degraded summary on this board to
find.

Worse for the spec, its single named example refutes its own predicate. It
offers *"it opens with a bare id (`TASK-218` opens with `DESIGN-012 I1`)"* as a
structural symptom. Ten of the 49 open with a bare id — TASK-218, 219, 220,
221, 236, 237, 238, 182, and closed 235, 260 — and **all ten are among the best
summaries on the board.** TASK-218's reads in full:

> DESIGN-012 I1. Today each of the four phase-close stages re-reads
> phase/CURRENT, so the moment one stage advances it every later stage aims at
> the wrong phase. That is the 2026-08-28 failure, and it is a data-flow bug
> rather than a documentation one.

A leading citation followed by an explanation is this project's house style.
Had `opens-with-a-bare-id` been implemented as proposed, the check would have
shipped at **0% precision on its entire true-positive set** — ten findings,
ten false. That is the third guard-over-English failure on this project in two
days, and it was caught by measuring the corpus before writing the check
rather than after.

**So the problem is not degradation. It is absence, and only absence.** The
count that matters is 89, and every one of those 89 rows carries the field
because Contract 1.11 gave it to them, not because anyone declined to fill it.

## 3. Baseline suite is not green at `a6ca21f`

`python3 tests/parallel -j 4` on the untouched baseline: **110 modules, 3098
tests, 253.0s, exit 1** — one pre-existing failure,
`test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`,
over dangling `ADR-018` / `ADR-020` references. Unrelated to this row and not
introduced by it. Baseline for "no redder than" is therefore **3097 of 3098**,
not a green suite.

<!-- sections 4+ appended as the work lands -->
