# TASK-113 — Three checks read the project living around them

> Source: three simultaneous reds on 2026-08-20 after an ordinary day's work, none of them a regression
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## The three, and why they are one defect

Each broke because the project moved, not because anything regressed. This class
was already fixed once today — `test_board_render` asserted
`rows_from_store > 20` and was relaxed to `> 0` with the reason written down:
*"Closing a task removes one projected row, so a fixed live-row count makes
project progress break this test."* The same shape grew back twice more within
hours, which is why this row exists rather than three separate patches.

1. **`test_v5_signoff.TestHistoryIsNotRewritten.test_the_three_existing_v5_closes_still_read`**
   asserts a set of exactly **three** V5 closes. Three more were signed the day
   it shipped. The property it defends — a new signature does not rewrite an old
   record — is real and must survive; the count is not the property.

2. **`test_one_line_break_rule.TestTheRefusalNamesTheFlag.test_two_flags_do_not_produce_the_same_message`**
   uses **TASK-038** as a live fixture. That row was closed hours later and left
   the board, so the tool now answers `TASK-038 is not a row on the board` and
   the assertion about flag naming never runs. Note the failure mode: the test
   does not report "my fixture vanished", it reports the feature broken.

3. **`LOAD-02` reports `REL-00` dangling**, and its only source is this line in a
   **signed V5 record**:

   > `- the dangling-id check reports [] — TASK-107 resolves and REL-00 is gone *(Perry verified)*`

   Writing that a code is gone is what brings it back. This is `LOAD-03`'s defect
   one field over — prose *about* a thing counted as the thing — and TASK-108
   fixed that one by counting records rather than mentions.

## Deliverable

1. The V5-close test asserts the **property** — that every signature already in
   the journal still parses and still reads with its disposition headings intact
   — over however many exist, rather than over a fixed set of three.
2. The flag-refusal test builds its own row instead of borrowing a live one. A
   fixture that a future close can delete is not a fixture.
3. An id appearing inside a **signed record**, or inside prose reporting the
   result of a check, is not counted as a reference. Writing that a code is gone
   must not resurrect it.
4. **No signed V5 record is edited.** The journal is append-only, and
   `TestHistoryIsNotRewritten` exists to say so. The fix is in the checkers.

## Verification — V3

1. Close any further row, or add a further V5 signature, and all three stay
   green. Demonstrate it rather than reasoning about it.
2. Each check still fires on the defect it was written for: a V5 record whose
   dispositions were rewritten fails item 1's test; a refusal that names the
   wrong flag fails item 2's; a genuinely dangling id still fails `LOAD-02`.
   A check relaxed into always passing is worse than the red it replaced.
3. `git diff -- perry/journal/` is empty at the end.
4. A mechanical sweep over the suite naming any **remaining** test that asserts a
   count taken from live project state — reported, not necessarily fixed, so the
   next one is found before it goes red.
5. `python3 tests/parallel`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `tests/test_v5_signoff.py`
- `tests/test_one_line_break_rule.py`
- `bin/perry-diagnose` — the reference counting for item 3
- focused tests for each

## Out of scope

- Anything under `perry/` — the PMO's state, and item 4 forbids editing the
  journal specifically.
- `bin/perry-task`'s refusal behaviour. Item 2 changes a fixture, not the tool.
- The other user-load findings.
- `schema/state-schema.json`, `claims`.
- Closing without the V3 evidence above.

## Changes

- 2026-08-20 — **High-stakes gate cleared by the user, bounded.** The scan
  refuses on `diagnose`, from `.perry/hook.md`'s "Writing into a project Perry
  does not own — `adopt` commit stage, `diagnose` execute stage, `relocate`,
  `git mv`". Same whole-word match as TASK-108, and the same granularity gap:
  the rule guards the **execute stage**, this row touches the reference counting.
  Bound: no change to the diagnose execute stage, no write to any project
  outside this repository, no change to which paths Perry claims — and, specific
  to this row, **no edit to any signed record under `perry/journal/`**.
