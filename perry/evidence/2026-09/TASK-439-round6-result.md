# TASK-439 — round 6: both windows tested, and the writer tells the truth

**Rung:** V4. **Authority:** `USER-930`, answer **A**, given 2026-09-14 — a
sixth and narrow round, two changes and nothing else. Round 5 FAILed V4
(`evidence/2026-09/TASK-439-round5-v4-review.md`), the second FAIL since
`USER-928`, so `review.md § 6` sent it to the user.

---

## 1. The FAIL — a test I removed

Round 5 made the gap fixture point `phase/CURRENT` at `004-next` so that
`_register_state`'s phase match would actually be evaluated. It did that by
**replacing** the fixture's blank pointer instead of adding a second fixture.
The phase match gained a test; the between-phases window lost its only one.

That window is the state `goals/reference/phases.md § score-phase` step 7
prescribes, and the one `USER-928` answer A was built for. Reproduced by the
PMO on an archive of `f79b75a6`: reading a blank `CURRENT` as phase 003 left
all 39 module tests green, and no test in the module wrote a blank pointer.

### What landed

`between_phases()` sits **beside** `gap()`. Each has its own tests:

| fixture | `phase/CURRENT` | what it exercises |
|---|---|---|
| `gap()` | `004-next` | the store is read and the phase match evaluated |
| `between_phases()` | blank | the score-phase step 7 window itself |

`test_the_window_fixture_really_is_blank` fails if the blank pointer is ever
swapped away again, which is exactly how round 5 lost it.
`test_a_blank_pointer_is_not_read_as_a_phase` is round 5's verdict mutation
written down as a test.

## 2. ROW C — the writer's false sentence

`linkage_add_change` refused `--unlinked` with "declares no key result for the
current phase" whenever `_current_store_phase` returned `""`. It returns `""`
for two reasons: a register that loads and has nothing for the open phase, and
one that does not load at all. Reproduced on an unparseable store still holding
**6 key results for phase 003**: the sentence was false of that file — the
false-message class this row has FAILed on twice.

The writer now asks `_register_state`, as the gate already does. `unparseable`
gets "could not be read … run `perry-lint`"; the other reason keeps its
sentence, and `test_unlinked_between_phases_keeps_its_own_sentence` is the
control.

## 3. Not this round

The verdict's other six ROW findings stay in its evidence, by the user's
answer: the traceback on an unreadable `CURRENT` with `--kr`, `perry-lint`
silent on a non-UTF-8 store, `--kr` appending to an unparseable store, the
untested non-object guard, three tests that pass on round 4's refusal, and two
overclaiming sentences.

## 4. Tests

Six new tests — four on `between_phases()`, two on the writer's message — and the module is **45 tests, all green**.

## 5. Mutations

`__pycache__` cleared before every run; both edited files verified against
their pre-battery snapshots afterwards.

| # | mutation | result |
|---|---|---|
| M1 | a blank `phase/CURRENT` is read as phase 003 — **round 5's verdict mutation** | **RED** — 3, incl. `test_a_blank_pointer_is_not_read_as_a_phase` |
| M2 | the writer's `unparseable` branch removed | **RED** — `test_unlinked_on_an_unreadable_register_says_it_could_not_be_read` |
| M3 | `between_phases()` swapped back to a named phase — **round 5's own mistake** | **RED** — `test_the_window_fixture_really_is_blank` |
| M4 | the unparseable writer message says the false sentence again | **RED** — the same message test |

M1 is the one this round exists for: the exact edit that left all 39 tests
green under round 5 now reddens three. M3 is the guard against doing to this
fixture what round 5 did to the last one.

## 6. Suite

```
131 modules · 3835 tests · 87.9s · 8 workers
✗ 3 of 3835 TEST(S) failed
0. tree guard — ✓ nothing under /Users/bytedance/proj/Perry moved
```

The three are the session's standing reds: two conformance-witness keys in
`test_contract_key_parity` and the clock-dependent
`test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`.
