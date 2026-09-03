# TASK-308 — result

- **Branch**: `coding/task-308-bound-before-the-round`
- **Branched from**: `548f206` ("Escalation override recorded before either row is dispatched"), `main` at dispatch time.
- **Worktree cut at**: `d49964e` — ~140 commits behind, the stale cut the brief warned of. Re-branched onto `548f206` before any work. The spec resolved on disk; nothing was reconstructed.
- **Dispatched under** the first `exit 3` escalation override on this project (`perry/evidence/2026-09/2026-09-03-escalation-override.md`). Touches `bin/perry-lint` and `tests/` only. No push, no PR, no merge, no `main`, no `schema/state-schema.json`, nothing under `claims`.

## Before-state — re-derived, not quoted

The spec cites `47fa45a`: 144 specs / 17 bound / 127 without. On `548f206`:

```
specs on disk (evidence/*/*-spec.md) : 146     (spec said 144)
specs carrying a `## Bound`          :  19     (spec said 17)
specs without                        : 127     (unchanged)
`criteria-unbounded` reported        :   0
```

The two specs added since `47fa45a` both carry a bound, so both totals moved by
two and the *missing* count did not. The spec's headline is stale on the two
numbers that do not matter and exact on the one that does.

`criteria-unbounded = 0` confirmed on two surfaces:

- `perry-lint --root .` — 0 errors, 26 warnings: `NS-01` 5,
  `spec-scope-unscannable` 11, `summary-missing` 10. The rule is absent.
- `perry-lint --root . --reviews` — 23 findings: `verdict-malformed` 9,
  `v4-close-without-verdict` 10, `review-rounds-exhausted` 2,
  `review-with-no-verdict` 2. Absent again.

Cause confirmed as specified. `bin/perry-lint:2463` reads
`fields.get("criteria", "")` inside `for fields, line in parse_verdicts(text)`.
That loop body runs only for a spec some verdict block already cites, and a
verdict block exists only after a round has scored. On 127 specs it has never
spoken.

## What changed

`check_specs` (`bin/perry-lint`) — the pass that already reports
`spec-scope-unscannable`, already walks `evidence/**/*-spec.md` through
`SPEC_FILE_RE`, already runs in the default `perry-lint --root .`, and already
carries the cap/stats/summary machinery — now also reports **`spec-unbounded`**.

The verdict-side `criteria-unbounded` is untouched. Both docstrings now state
which question each answers and say not to unify them, and
`TestBothHalvesOfTheBoundRuleSurvive` fails if someone does.

Presence and shape only. `_BOUND_RE` — the matcher the verdict-side check
already used — is shared, not duplicated: one answer to "what counts as a
bound", the same discipline that makes `check_specs` read
`P.ESCALATION_TOUCHES` from the gate rather than restate it. No judgement of a
bound's content: `test_a_bound_is_not_judged_on_its_content` asserts that a
bound reading `TBD.` is accepted.

## Severity — chosen and argued

**`warn`, capped at `DRIFT_ROWS_SHOWN` (10) named individually plus one
remainder finding, with the exact count in `stats` and every path under
`perry-lint --specs --json`.** In the default pass that is 11 lines, not 127.

Why this one: it is the answer this very function already gives to the
identical problem — 45 unscannable specs reported as 10 + 1 — and the answer
`check_summaries` gives to 89 and the six store-drift checks give via
`DRIFT_ROWS_SHOWN`. `reference/diagnose.md` names a wall of red as strictly
worse than no check, and the cap is this codebase's settled response. A second
answer here would mean two rules for "how does a check report a large true set".

Why **not** "only specs newer than a date": the check's answer would depend on
when it is asked and would drift silently as the tree ages. It is also not
enumerable — you cannot state the last element of "specs newer than X", so the
check would violate the rule it enforces.

Why **not** "only rows at `review` or being dispatched": that reintroduces the
defect being fixed. Scoping to board state would make the spec-side check
consult a row's status the way the verdict-side one consults a verdict, and the
whole property is that this decides from the spec alone, knowing nothing about
verdicts or the board, before anyone chooses to dispatch.
`test_the_spec_side_check_reads_no_verdict` pins that: `check_specs` must not
mention `parse_verdicts`, `BOARD.md`, `events.jsonl` or `tasks.jsonl`.

Why `warn` and not `error`: report, do not refuse — the row's `Out of scope`,
on the `DESIGN-003 § 4` decision 4 and TASK-284 `scope_scanned` precedent. An
error would retroactively block 127 existing rows, and `.perry/hook.md` forbids
rewriting history to make a gate pass. `--strict` still promotes per-run, so one
dispatcher can choose to be stopped without that choice being made for everyone.

The argument is written into the `check_specs` docstring, not only here.

## After-state

`perry-lint --root .` — **0 errors, 37 warnings** (was 26; +11 = 10 named + 1
remainder). New census line, printed every run whether good or bad:

```
· specs:  45 of 146 present the escalation gate no scope to scan …
· bounds: 127 of 146 spec(s) carry no `## Bound` — a round against those has no
          finite set to check and no last element (`perry-lint --specs --json`
          names every one)
```

`perry-lint --root . --specs --json` — `unbounded: 127`, and 127
`spec-unbounded` findings: the cap is on the naming, never on the count.
`perry-lint --root . --json` carries `specs: {specs: 146, unscannable: 45,
unbounded: 127, checked: true}`.

## Verification

**Main property** — `test_the_whole_point`: a spec with no `## Bound` is
reported by the DEFAULT pass (`--specs` asserted absent from the argv), and
`assert_no_review_anywhere` walks the entire fixture tree asserting no file
contains `=== VERDICT ===` and no file is named like a review. Without that
assertion a green result would be consistent with the old verdict-side check
having fired, and the test would prove nothing about speaking before a round.

**Control** — `test_a_spec_that_has_a_bound_is_silent`: reported count 0 and no
finding. Guarded further by `test_the_two_fixtures_differ_only_in_the_bound`
(`BOUND_SPEC.startswith(UNBOUND_SPEC)`, so the pair cannot be measuring some
other difference) and `test_neither_fixture_trips_the_other_rule`.

**Verdict-side check still fires** — `test_review_verdicts.py`
`TestTheCriteriaMustBeBounded`, 5 tests, all pass unchanged; the module's 72
tests pass. Mutation M7 deletes its call site and turns both it and the
both-halves guard red.

**Shape, not substring** — `test_the_word_alone_is_not_a_bound`: prose, a
`- **Bound**:` bullet and a `Bound:` line are each still reported.
`test_a_nested_bound_still_counts`: `### Bound` counts, matching the
verdict-side reading.

### Mutations — 7 planted, 7 red, 0 green

Each anchored by line number **with an assert on the old text** (a non-matching
anchor raises rather than no-opping); `__pycache__` cleared and 1.1 s slept past
the whole-second boundary around every apply and restore.

| # | mutation | paired test | result |
|---|---|---|---|
| M1 | revert the new call site (`if False and …`) | `test_the_whole_point` | RED |
| M2 | fire on every spec (`if True or …`) | `test_a_spec_that_has_a_bound_is_silent` | RED |
| M3 | substring `"Bound" not in` instead of the shape regex | `test_the_word_alone_is_not_a_bound` | RED |
| M4 | uncap the named list | `test_the_named_list_is_capped_but_the_count_is_not` | RED |
| M5 | promote `warn` → `error` | `test_it_is_advisory` | RED |
| M6 | kill the loop (`for md in []`) | `test_the_whole_point` | RED |
| M7 | delete the verdict-side half | `TestTheCriteriaMustBeBounded` + both-halves guard | RED |

**Round 1 produced one GREEN and it was chased, not waved off.** M6 was first
paired with the *control* test and came back green. Investigated in
`m6.py`: the dead check is RED against the main property test, RED against the
whole class (10 failures) and RED against the module — green only against the
control alone. That is correct behaviour, not a hole: a control's job is to
catch the check OVER-firing, and a check that reports nothing is silent on a
bounded spec too. The pairing was wrong in the harness, not the suite. Re-run
with the pairing corrected: 7 red, 0 green.

**Restores verified against `git show HEAD:<path>`** via `bin/perry-restore-check`
— never against a harness snapshot, which is the circular check TASK-256 names.
All 7 restores reported `✓ bin/perry-lint matches HEAD (3a6efbd3d212…)`, exit 0.

### Suite

| | baseline (`548f206`) | after |
|---|---|---|
| modules | 113 | 113 |
| tests | 3162 | 3179 (+17) |
| result | all green | all green |
| tree guard | clean | clean |

Baseline measured on this branch before any edit and committed before the run.
`perry-lint --root .` at **0 errors**, as required.

## The Bound's own Remainder

The row's `## Bound` asks for the count of criteria files that are **not**
`*-spec.md` — `review.md § 1` allows a `## What must be true when this is done`
section in a task's own evidence file — and leaves whether the spec-side pass
should reach them to a new row.

**Count: 1** — `perry/evidence/2026-08/TASK-065-extraction.md`. (Three files
carry that section; the other two, `TASK-042-spec.md` and `TASK-050-spec.md`,
are specs and are already covered.) Not addressed here, per the Bound. This is
also the concrete blind spot that makes deleting the verdict-side check a real
loss rather than a theoretical one, and it is written into that check's
docstring.

## Notes — where this brief and spec were wrong

1. **The census moved.** 146/19/127, not 144/17/127. Both totals grew by two;
   the missing count did not. Re-derived, as instructed.
2. **The Bound's TASK-067 example does not hold.** It states "TASK-067 uses one"
   of the non-spec criteria sections. TASK-067 has a `*-spec.md`, and no
   TASK-067 evidence file carries
   `## What must be true when this is done` — the only non-spec file that does
   is `TASK-065-extraction.md`. The Bound's *claim* is wrong; its *point* — that
   such files exist and are outside this row — is right, and the Remainder above
   reports the real count.
3. **One green mutation occurred and is reported above** rather than being
   quietly re-paired. The finding was in the harness, and the evidence for that
   claim is the mutation run against three different targets, not an assertion.
4. Four pre-existing assertions in `tests/test_spec_scannability.py` needed
   updating: they pinned the exact `specs` stats dict or the exact findings
   list, and the existing fixtures legitimately trip the new orthogonal rule.
   Scoped to the rule under test rather than adding a bound to `BULLET_SPEC`,
   which is reproduced verbatim from what `perry-task add` renders and whose
   docstring claim would otherwise become false.

## Files changed

- `bin/perry-lint`
- `tests/test_spec_scannability.py`
- `perry/evidence/2026-09/TASK-308-result.md` (this file)
