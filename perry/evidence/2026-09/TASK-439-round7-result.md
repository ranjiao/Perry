# TASK-439 — round 7: every spelling step 7 can leave

**Rung:** V4. Round 6 FAILed V4 (`evidence/2026-09/TASK-439-round6-v4-review.md`);
it is the first FAIL since `USER-930` was answered, so the escalation guard
allows a round. `USER-930`'s narrow scope still governs: tests only, and the
verdict's five ROW findings stay in its evidence.

---

## 1. The FAIL

Round 6 added `between_phases()` beside `gap()` and wrote `""` into
`phase/CURRENT`. `goals/reference/phases.md § score-phase` step 7 does not
write that. It says to clear the pointer by **deleting the file or writing
`(none)`**, and this repository wrote `(none)` on 2026-08-28.

A deleted pointer goes through its own branch in `_register_state` —
`pointer.read_text(...) if pointer.exists() else ""` — and no test ran it.
Reproduced by the PMO on an archive of `15e8084b`: making a deleted pointer
read as phase 003 left all 45 module tests green. The reviewer drove two edits
on that branch that each pass the whole suite: removing the `exists()` guard
tracebacks every `add` on a project with a register, and wrapping the read in
`try/except` reproduces round 2's FAIL-2.

No product code was wrong. The guard against the next edit breaking it was.

## 2. What landed — tests only

`WINDOW_SPELLINGS` names every way a user can leave "no current phase", each
run as its own `subTest` so a regression names the spelling it broke:

| spelling | where it comes from |
|---|---|
| `deleted` | step 7, first half |
| `(none)` | step 7, second half, and what this repository wrote |
| `blank` | round 6's fixture |
| `newline only` | an editor saving an emptied file |

| test | what it pins |
|---|---|
| `test_every_window_spelling_is_really_what_it_says` | anti-vacuity for the fixture: a spelling that silently became another is how rounds 5 and 6 each lost part of this window |
| `test_every_window_spelling_files_the_row_with_a_warning` | exit 0, a warning, and no traceback — the last is the reviewer's first edit |
| `test_in_every_window_spelling_the_row_files_while_unlinked_is_refused` | round 2's FAIL-2, on every spelling — the reviewer's second edit |

Module: **48 tests, all green** — including after the tightening in § 4.

## 3. Not this round

The verdict's five ROW findings stay in its evidence under `USER-930`'s narrow
scope: the refusal's `perry-lint` hand-back carries no `--root`; an
unparseable register while `CURRENT` is cleared has no test and the gate's
"NOT the between-phases window" is false there; the fallback warning claims the
step-7 window when `CURRENT` names an open phase; three tests are thinner than
their names; and the new message repeats round 5's claim about truncated writes.

## 4. Mutations

`phase/CURRENT` is read in **two** places, so every mutation ran at each:
`_register_state`, which the gate asks, and `_current_store_phase`, which the
`--unlinked` writer asks. `__pycache__` cleared before every run; the file
verified against its pre-battery snapshot afterwards.

**A disclosure first.** The first battery anchored on the read line alone, which
occurs twice. The helper refused both replacements — correctly — but the run
after each still printed OK against unmodified code. Those three results were
discarded, not reported; every row below is from the re-run with per-function
anchors.

| mutation | gate site | writer site |
|---|---|---|
| M1 — a deleted pointer reads as phase 003 (**round 6's verdict mutation**) | **RED** — 2 (`deleted`) | **RED** — 1 (`deleted`) |
| M2 — `(none)` reads as phase 003 | **RED** — 2 (`(none)`) | **RED** — 1 (`(none)`) |
| M3 — the `exists()` guard removed | **RED** — 2 (`deleted`) | **GREEN, then RED after the fix below** |
| M4 — the `deleted` spelling silently writes a blank | **RED** — `test_every_window_spelling_is_really_what_it_says` | — |

### The green at the writer site was a test that could not tell a refusal from a crash

With the guard removed at `_current_store_phase`, `--unlinked` on a deleted
pointer raised `FileNotFoundError`. The window test asserted only that
`--unlinked` did not exit 0, and a traceback does not exit 0 either — so it
stayed green. That is the shape round 5's reviewer found, repeated in the round
meant to close it.

The test now requires a clean refusal: `refused` in stderr and no `Traceback`.
Re-run, writer-site M3 is **RED** on `(spelling='deleted')`.

## 5. Suite

```
131 modules · 3838 tests · 80.1s · 8 workers
✗ 3 of 3838 TEST(S) failed
0. tree guard — ✓ nothing under /Users/bytedance/proj/Perry moved
```

The three are the session's standing reds: two conformance-witness keys in
`test_contract_key_parity` and the clock-dependent
`test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`.
