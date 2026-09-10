# DESIGN-019: A risk nothing brings back is a claim that rots in public

> Status: draft
> Date: 2026-09-10 · Locked: —
> Author: PMO Agent   · Implementation owner: Coding Agent
> Linked OKR: —
> Supersedes: —   · Superseded by: —
> Revisits: `work/state/BOARD_TEMPLATE.md § Top risks`, `work/reference/subcommands.md § triage`, `viewer/parsers § TopRisk`

## 1. Problem

**Perry's published top risk describes a file that no longer exists.**

`RX-001` says `.perry/config.md` exists and flips `is_adopted()`, so lint
demands a state tree the project has not got. ADR-019 deleted that file. The
condition cannot occur. `perry-state --compact` publishes it as `risks.top` on
every read, and `work/SKILL.md:169` renders it into the standup as
`🚧 Top risk`. Nothing has noticed, because **nothing ever brings a risk back**.

Measured 2026-09-10 on this repository:

| | |
|---|---|
| risk records | 4 — three open, one cleared |
| risk writes in `.perry/events.jsonl` | **0**. Two lines mention `RX-`, both `next` events on tasks |
| rows with an `opened` date | **0 of 4** |
| `age_days` in the payload | `null` |
| last risk cleared | 2026-08-16 |
| `value` / `threshold` / `max1` / `max2` | `null` on all four |
| `severity_rank` | `""` |

**The mechanism is complete and the practice is empty.** There is a store, four
verbs on each side, a parser, a drift check in `perry-lint`, and 83 tests. What
there is not is a single risk that was authored through `perry-task risk-add`:
all four were imported from the markdown table by `risks-write --from-board`,
which is why every `opened` cell is blank. `cmd_risk_add`'s docstring says *"the
tool mints the id and stamps the date"*, and it does. Nobody has run it.

### 1.1 Three defects under the one symptom

**The record shape is quantitative and the content is prose.** `TopRisk` carries
`value`, `threshold`, `max1` and `max2` — the shape of a measured indicator
crossing a boundary — and every one is null on every row. Whoever designed the
record expected risks to be numbers. They are being used as sentences.

**Severity is a vocabulary nowhere enforced.** `viewer/parsers § TopRisk` names
four values in a comment — `top` / `watch` / `accept` / `resolved` — and
nothing checks them. `severity_rank` ships as `""`, so a consumer cannot order
what it is given.

**Nothing ages a risk.** `perry-lint` checks that the store and the board agree
and says nothing about whether a row is still true. Compare the neighbours: a
task has staleness, WIP breaches and an SLA; an intake row is reported by age
after 14 days; an ADR has a sunset and `perry-state` publishes
`decisions.expired_sunsets`. A risk is written once and read never.

## 2. Goals

1. A risk carries a **deadline** — a date by which it must be handled — and the
   state payload reports one that has passed.
2. There is a decidable rule for when a risk is the right record, so that
   "should this be a risk or a task" stops being a judgement each time.
3. The record shape carries what risks actually hold and nothing else.
4. `severity` is a closed vocabulary a consumer can order.
5. `RX-001` is cleared, because the condition it names cannot occur.

## 3. Non-Goals

- **Not measuring risks.** Goal 3 removes the numeric fields rather than finding
  someone to populate them. A project that wants a measured indicator has KRs,
  which are built for it and have a contract.
- **Not a new lane or a new tool.** Risks stay in the `work` lane on the
  existing store.
- **Not automatic expiry.** See Decision 1: a deadline that silently voids a
  risk would make the register lie in the other direction.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | What brings a risk back | expiry (auto-invalidate on timeout) / **a deadline: handle before a stated date** / nothing | **a deadline** | 2026-09-10 |
| 2 | Where a risk is reviewed | `triage` / `mid-phase-review` / a new cadence point | **`triage`** | 2026-09-10 |
| 3 | When a risk is the right record | **a condition being watched with no action assigned; the moment it has an action it becomes a task and the risk cites it** / free judgement | **the rule** | 2026-09-10 |
| 4 | The numeric fields | keep and populate / **delete** | **delete** | 2026-09-10 |
| 5 | `severity` | free text / **closed vocabulary** | **closed vocabulary** | 2026-09-10 |
| 6 | Dropping `value`, which IS schema-declared | — | **OPEN — claim surface** | — |

**Decision 1's wording is the user's correction and it changes the design.**
The PMO proposed *expiry*, on the ADR-sunset precedent. The user's objection:
expiry implies automatic invalidation on timeout, and a risk that quietly stops
counting because nobody looked is the same rot in the other direction — the
register would then be wrong about a live risk rather than about a dead one. A
**deadline** is a commitment to handle it by a date. A passed deadline is a
finding, and the row stays exactly as live as it was.

**Decision 2 is adopted with one refinement the PMO owes it.** `triage` is the
right place to ACT: it is the recurring point where the office looks at things
needing a decision, and it already carries the age machinery a deadline needs.
But **the report must live in the state payload, not in the procedure.** A
deadline that only fires when a human happens to run `triage` reproduces § 1's
failure one level up — `RX-001` sat through every cadence point this project
has. So: `perry-state` reports a passed deadline the way it reports
`decisions.expired_sunsets`, and `triage` gains a step that discharges it.

**Decision 6 is the one thing not yours to take.** `value` is declared in
`schema/state-schema.json`, which `.perry/hook.md § High-stakes operations`
puts on the claim surface. `threshold`, `max1` and `max2` are not declared and
are referenced nowhere but the dataclass, so they go under Decision 4 without
authorization. Dropping `value` needs the user to say so.

## 5. Architecture

**A risk record gains `deadline` and loses four fields.** `deadline` is a date,
written by `risk-add` and rewritable by a new verb; `opened` is already stamped
and already correct in code.

**One predicate decides whether a deadline has passed**, in `viewer/parsers`
beside `status_is_cleared` and `status_cleared_date`, called rather than
restated — `perry-lint` and `perry-state` both need it, and § 1's neighbouring
defect (TASK-420) is exactly what a second copy of one rule costs.

**`severity` becomes a closed set** validated on write, with `severity_rank`
derived from it so a consumer can order without knowing the words.

**Decision 3's rule is enforced where it can be and documented where it
cannot.** `risk-add` cannot know whether an action exists. What it can do is
require that a risk citing a task id refuses if that row is open — a risk with
a live task is a task. The judgement half goes in `work/reference/subcommands.md`.

## 6. Implementation plan

| Phase | Scope | Owner |
|---|---|---|
| A | Clear `RX-001` and record why. One command, no code, and it stops the standup publishing a false claim today | PMO |
| B | Delete `threshold`, `max1`, `max2` from `TopRisk` and every reader; `value` waits on Decision 6 | Coding Agent |
| C | `deadline` on the record, written by `risk-add`, with the shared passed-deadline predicate | Coding Agent |
| D | `perry-state` reports passed deadlines; `perry-lint` reports them as a finding | Coding Agent |
| E | `severity` closed and validated on write; `severity_rank` derived | Coding Agent |
| F | `triage` gains the review step; `work/reference/subcommands.md` carries Decision 3's rule | Coding Agent |

## 7. Risks & mitigations

- **This design's own subject applies to it.** A register nobody uses does not
  become used because it grew a deadline field. The measurable test is whether
  a risk is authored through `risk-add` in the next phase; if none is, the
  honest next decision is to delete the register rather than to add to it again.
- **A deadline is a promise, and Perry has a finding for promises nobody kept.**
  Adding deadlines to four rows nobody revisits converts one silent problem into
  four noisy ones. Phase A exists so the register is honest before it is grown.

## 8. Open questions

- Does a cleared risk keep its deadline, or is a passed deadline on a cleared
  row meaningless? The board template says a cleared row STAYS as the record
  that the mitigation worked.
- Should `perry-diagnose` grade a project with zero risks? Perry has run for
  weeks with three, and three of them stale — an empty register and a rotten
  one look the same from outside.

## 9. Changes (append-only after lock)

- 2026-09-10 — created, with Decisions 1 to 5 answered in the same session.

## 10. References

- `work/state/BOARD_TEMPLATE.md § Top risks` — what the template promises
- `work/reference/subcommands.md § triage` — Decision 2's home
- `viewer/parsers § TopRisk` — the record shape
- ADR-019 — deleted `.perry/config.md`, which `RX-001` is about
- TASK-420 — two implementations of one rule, in the register next door
