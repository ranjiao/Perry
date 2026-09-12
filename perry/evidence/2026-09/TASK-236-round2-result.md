# TASK-236 — round 2 result

> Status: implemented and measured; **not reviewed**.
> Criteria: `perry/evidence/2026-09/TASK-236-spec.md`.
> Round 1's verdict: `perry/evidence/2026-09/TASK-236-round1-v4-review.md` —
> **FAIL**, one defect, in code this row added.
> Executor: the PMO session, inline on `main`, per `ADR-018 § B`: the defect is
> named to the line, reproduced, and verifiable by a command the reviewer
> already ran.

## 0. The FAIL, reproduced before anything was changed

`overall_kr_model` joins by iterating OBJECTIVES:

```python
rows = [k for k in krs
        if k.get("version") == version
        and k.get("objective_id") == obj.get("id")]
```

A `kr` record matching no objective is emitted **nowhere**, and the renderer
then prints the survivors' count as fact.

Measured on the live store, on a scratch copy, before the fix — orphan ONE
`kr`'s `objective_id`:

| | |
|---|---|
| `perry-goals krs --level overall --version all` | **37 of 38 rows, exit 0** |
| `perry-okr diff` | `identical: true`, `every_line_and_cell_came_from_the_store: true` |
| `perry-lint` | `0 error(s)`, `OKR store: 51 record(s), 0 row(s) drifted` |

**A key result disappears from the only surface that carries it and every gate
stays green.** That is `review.md § 0`'s second question — a tool reporting a
wrong answer to someone with no way to detect it — and it is why round 1 was
right to FAIL rather than file it.

## 1. The fix, and why refusing is not a new rule

The residual is computed and the command **refuses** rather than printing a
short table.

`cmd_krs`, forty lines up in the same file, already states the rule about a
half-read graph: *"would print a KR table missing whichever rows it dropped,
which is the one thing this command must never do."* The same sentence was
true of `overall_kr_model` and had no code. This is where it becomes code.

**Scoped to the WANTED versions, deliberately.** With `--version v2` the v3
records are out of scope rather than orphaned, and a residual check that did
not scope itself would refuse every correct store carrying two version blocks.
`M2` below is the mutation that proves the scoping load-bearing.

The refusal names the count, names each record, and says where the fix is — the
store — and it names the thing that cannot see the problem: *"`perry-okr diff`
cannot see this — a record with no line to land in is invisible to a byte
comparison."* That is round 1's own finding about the byte gate, carried into
the message a user will actually read.

## 2. All five corruptions round 1 named

Each planted on a scratch copy of the live store, command re-run, store
restored and `git diff` verified empty:

| corruption | before | after |
|---|---|---|
| `objective_id` orphaned | 37 rows, exit 0 | **REFUSED, exit 1** |
| `objective_id` blanked | 37 rows, exit 0 | **REFUSED, exit 1** |
| `objective_id` removed | 37 rows, exit 0 | **REFUSED, exit 1** |
| unknown `version` | 37 rows, exit 0 | **REFUSED, exit 1** |
| blank `id` + orphaned | 37 rows, exit 0 | **REFUSED, exit 1** |

## 3. The guard

`tests/test_okr_krs_render.TestAKrThatBelongsToNoObjectiveIsRefused`, 8 tests,
on a fixture project the test writes — no live-state literals, per `TASK-404`.

All five shapes are covered rather than only the one that bit, because a test
that covers the one that bit is a test the second shape re-opens. Two of the
eight are the anti-vacuity half:

- `test_a_healthy_store_still_renders` — a refusal that fires on every store
  would pass every other assertion in the class and make the command useless.
- `test_a_narrowed_version_does_not_strand_the_other_block` — the scoping.

## 4. Mutations — four, none green

| # | Broken | Result |
|---|---|---|
| M1 | the residual check removed | RED — 6 tests |
| M2 | the residual not scoped to the wanted versions | RED — 4 tests |
| M3 | `placed` never recorded | RED — 13 tests |
| M4 | the blank-id placeholder dropped from the message | RED — 1 test |

`bin/perry-goals` restored and sha256-verified after each. `M2` is the one
worth reading: without the scoping, a correct two-version store refuses, so the
narrowing is not decoration.

## 5. What round 1 found and this round did NOT change

**MX-5, the green mutation, is still green and still not charged.** A corrupted
`metric` *value* is caught by nothing — `diff`, `verify`, `lint` and the guard
modules all pass. Round 1 measured the same corruption on the pre-change tree
and it WAS caught, so this row did remove a real detector. That is `ADR-019`'s
single-copy trade, disclosed in the original result's § 4.1, and it is a
different question from this FAIL: the reader still sees all 38 rows.

**Round 1's ROW-grade finding about `ADR-015` is untouched.** F-2 — this row
closed the only supported path for a user to AUTHOR a key result — satisfies
`ADR-015 § What would reopen this` trigger 1 on its own evidence, and no entry
and no ask exists. That belongs to the goals lane, not to this round.

## 6. Suite

`bash tests/run`: **3 of 3,711 failed** — `test_contract_key_parity` (2) and
`test_resume` (1), the pre-existing set by name, both modules reproducing when
run alone. Tree guard clean: *nothing under /Users/bytedance/proj/Perry moved*.
The suite grew by exactly the 8 tests this round adds.
`perry-lint`: 0 error(s).
