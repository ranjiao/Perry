# DESIGN-010: Autopilot cannot dispatch anything, and the spec is why

> Status: draft
> Date: 2026-08-27 · Locked: —
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: KR-O5.3, KR-O5.4 (`perry/OKR.md` v2, Objective 5 — Tasks are executed by roles that know things)
> Supersedes: —   · Superseded by: —
> Revisits: `work/reference/autopilot.md`

## 1. Problem

`/perry work autopilot` ran on this project for the first time on 2026-08-21 and
**dispatched nothing.** Every safety gate passed; the plan came out empty.

```
open rows                          36
eligible                            0

  no spec                          32
  spec carries no `Dispatch mode:`  1   (TASK-050 — acceptance criteria, not a dispatch spec)
  already past dispatch             1   (TASK-094, at `review`)
  already in flight                 1   (TASK-153)
  blocked on an open dependency     4
```

69 spec files exist under `perry/evidence/`. **Exactly three belong to a row that
is still open**, and none of the three is dispatchable.

Autopilot's stated precondition is *"You have ≥ 3 P0/P1 specs ready to dispatch
(`Dispatch mode: auto`, all dependencies resolved)."* **That has never been true
on this project**, and the cause is the working pattern rather than an oversight:
**the PMO writes a spec at dispatch time, for one row, having first re-verified
that row's findings against today's code.** The spec and the dispatch are one
act, so a queue never accumulates.

### The pattern is not laziness — it is what keeps the dispatches correct

Three rows dispatched on 2026-08-21, all three re-scoped *at dispatch time*:

| row | what a pre-written spec would have said | what was true that day |
|---|---|---|
| **TASK-037** | fix three defects from a V4 review | **all three were already fixed** by TASK-119's rewrite of the same file |
| **TASK-040** | *"Top risks becomes a table with id/opened/cleared"* | ADR-007 had made a better table the wrong answer entirely |
| **TASK-045** | retire the tolerance branches | precondition (`gate: enforce`) had to be checked that day, and a constraint had to reach the prompt **verbatim** or the agent would delete fallbacks adoption needs |

And two more, from the same day, showing the failure mode is not hypothetical:

- **TASK-171's spec said the gap was 3 event kinds. It was 11.** The spec
  measured the document against *this project's log*; the deliverable measured
  it against *the writer*. Documenting only the spec's three would have left the
  new test red on its first run.
- **The TASK-114 delegation prompt v1** said aiMark was pinned nine versions
  back and asked for a constant that already existed. It was rendered one day
  before it was read.

**A stale spec is not a slow spec. It is a wrong one, and it is wrong in a way
the agent cannot detect** — the agent has no reason to doubt the document it was
handed.

## 2. Goals

1. Autopilot has a non-empty eligible list on this project without anyone
   pre-writing specs.
2. A row whose description no longer matches the code is **refused, with the
   discrepancy named**, rather than dispatched against a stale premise.
3. The escalation gate's guarantee is **not weakened**. Specifically: a machine
   author cannot green-light itself past `.perry/hook.md § High-stakes
   operations`.
4. Autopilot stops carrying its own copy of a rule the contract already answers.
5. Every count autopilot reports — eligible, skipped, and why — traces to a
   payload field, not to a hand-rolled classification.

## 3. Non-Goals

- **Autopilot closing a task.** Subjective verification is human; every dispatch
  still lands at `review`. Unchanged.
- **Autopilot deciding scope.** A spec that has to choose between two
  architectures is a row for a human, not a scout's output.
- **Replacing the PMO loop.** When a person is at the keyboard, writing the spec
  at dispatch time is still better, because the person can ask.
- **Retrying a failed dispatch.** One attempt per run stays.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Does the scout write a spec file, or a prompt held in memory | write the file (Recommended) / hold it in the run | TBD | — |
| 2 | What a machine-authored spec's `Out of scope` is worth to the gate | nothing — fail closed on any hit (Recommended) / same as a human's / green-lights only fragments the row already disclaimed | TBD | — |
| 3 | What the scout does when the row is stale | refuse and report (Recommended) / re-scope it itself / refuse and open a follow-up row | TBD | — |
| 4 | Is the scout's own output reviewed before build runs | no, the refusal is the review (Recommended) / a second scout must agree | TBD | — |

**Decision 2 is the one that matters.** It is § 5.2.

## 5. Architecture

### 5.1 Two stages, because the expensive step is not writing

```
  scout(row)  ──►  a spec, or a refusal naming what no longer matches
                        │
                        ▼
              escalation gate  ──►  refuse / proceed
                        │
                        ▼
  build(spec) ──►  a branch at `review`
```

**`scout` is a dispatch.** It reads the row, re-verifies its claims against
today's code, and produces either a spec or a refusal. That is precisely the work
the PMO does today and it is not cheap — which is the honest cost of this design,
stated up front: autopilot's dispatch count roughly doubles.

**What it buys** is the thing the table in § 1 measures: three of three rows
dispatched that day needed re-scoping, and a fourth had its gap understated by
8 of 11. Cheap wrong dispatches are more expensive than paired correct ones.

### 5.2 Why a machine author cannot keep the `Out of scope` green-light

The escalation scan is `perry-state --escalation-scan <spec>`. Its rule, in
`viewer/parsers.py`:

```python
disclaims = matching_escalations(_section(body, ESCALATION_DISCLAIMS), fragments)
green = set(disclaims)
for hits in touches.values():
    for f in hits:
        if f not in green and f not in refuse:
            refuse.append(f)
```

**A spec that lists a high-stakes fragment under `## Out of scope` green-lights
itself past the gate.**

That is correct when a **human** wrote the spec: it is a written commitment by an
author who knows what the work involves, and the document is the record of that
commitment. It becomes **a permission slip the dispatcher signs for itself** the
moment the dispatcher writes the spec.

The gate's guarantee today is *"a task that touches something dangerous is
refused unless a person wrote down that it does not."* Let a machine write that
sentence and the guarantee is *"a task that touches something dangerous is
refused unless the thing dispatching it says otherwise."* **Those are not the
same sentence.**

So: a machine-authored spec must be **fail-closed** — a hit in `Files in scope`
or `Deliverable` refuses, and `Out of scope` buys nothing. The row goes back to
the human with the fragment named. This is decision 2 and the recommendation is
the strict option.

**Provenance has to be in the artifact, not in the caller.** The scan reads a
file; the file must say who wrote it, or the same document means two different
things depending on which code path opened it.

### 5.3 Eligibility comes from the contract, not from autopilot

Autopilot classifies today with its own rule: *"status ∈ {`not_started`,
`blocked` with all blockers resolved}"*. That rule now has **exactly one
implementation** and autopilot carries a second:

- **1.12** stopped `startable` reading the stored `status`, so a row whose every
  dependency has closed is `startable: true` with `blocked_stale: true`.
- **1.14** made a `USER-` ask a node, so a row waiting on a question is correctly
  unstartable.
- **1.15** added `depends_on_resolved`, so *why* is readable too.

Autopilot reads `startable`. This half needs no RFC and is already opened as
**TASK-174**.

### 5.4 What the scout must produce, and what makes it refuse

A spec, in the shape `work/reference/dispatch.md` already requires, plus:

```
Authored by: autopilot-scout
Re-verified: <date> against <commit>
```

**It refuses when:**

- a claim on the row does not reproduce (TASK-037's three fixed defects);
- the row's title describes work a locked decision has superseded (TASK-040);
- a precondition the row names is not met (TASK-045's `gate: enforce`);
- the row's measurement is against a moving surface — *this project's log* rather
  than *the writer* (TASK-171);
- the scope requires choosing between two architectures.

**The last one is the boundary of this whole design.** A scout that re-scopes is
a planner, and planning is the user's. Decision 3.

### 5.5 Blast radius

| Touched | Why |
|---|---|
| `work/reference/autopilot.md` | the loop becomes two stages |
| `work/reference/dispatch.md` | the `Authored by` field, and what the gate does with it |
| `bin/perry-state § escalation-scan` | fail-closed branch for a machine author |
| `viewer/parsers.py § escalation payload` | provenance reaches the verdict |
| `.perry/hook.md` | **not touched** — the fragment list is the user's |

## 6. Implementation plan

1. **TASK-174** — autopilot reads `startable`. Independent, already open, no
   RFC needed.
2. **`Authored by` in the spec shape**, and the scan reporting it. Read-only:
   the verdict does not change yet.
3. **Fail-closed for machine authors**, per decision 2, with a test that a
   machine-authored spec disclaiming a fragment is *still* refused.
4. **The scout**, producing specs and refusals, run by hand on ten real rows and
   its refusals compared against what the PMO decided for those same rows.
5. **The two-stage loop**, only if step 4's refusals were right.

**Step 4 is the gate.** Ten rows, and the scout's verdicts compared against the
PMO's actual dispatch decisions from 2026-08-21, which are recorded. If the scout
would have dispatched TASK-037 against its stale findings, the design is wrong
and step 5 does not run.

## 7. Risks & mitigations

| # | Risk | Blast radius | Detection signal | Mitigation |
|---|---|---|---|---|
| 1 | The scout writes a plausible spec for a stale row | an agent works from a fresh-looking document that is wrong — the exact failure this design exists to remove, now automated | step 4's ten-row comparison | step 5 gated on step 4; the scout's refusal criteria are enumerated in § 5.4, not left to judgement |
| 2 | Fail-closed makes autopilot refuse nearly everything | autopilot is useless in a different way | count refusals in step 4 | if most refusals are `Out of scope` fragments a human would have green-lit, that is data for revisiting decision 2 — **not** grounds for weakening it mid-implementation |
| 3 | `Authored by` is forgeable | a machine spec claims a human author | the field is written by the tool that creates the file, and step 3's test asserts the scan reads the file rather than trusting the caller | never let the caller pass provenance as a flag |
| 4 | The scout's re-verification is itself stale by the time build runs | a long queue reintroduces the problem one level up | `Re-verified: <commit>` on the spec; build refuses if HEAD has moved past it in the files the spec names | scope the check to the spec's own `Files in scope` |
| 5 | Doubling the dispatch count exhausts the budget before anything is built | a run that scouts ten rows and builds none | the run summary already counts dispatches | budget scouts and builds separately |

## 8. Open questions

- **Does the scout need the escalation gate too?** It only reads and writes a
  spec file. But it reads the whole repository, and a scout that reads a
  production credential to decide whether a row is stale has done something the
  gate exists to notice.
- **Should the scout's refusals become rows?** A scout that finds TASK-037's
  three claims already fixed has produced a real finding. Filing it is right and
  it is also a write, which autopilot is otherwise forbidden from doing outside
  `review`.

## 9. Changes (append-only after lock)

## 10. References

- `perry/evidence/2026-08/autopilot-2026-08-21-1455.md` — the empty run, with
  the full skip breakdown.
- `work/reference/autopilot.md` — the current loop and its stated precondition.
- `perry/evidence/2026-08/TASK-037-result.md`, `TASK-040-result.md`,
  `TASK-045-result.md`, `TASK-171-result.md` — the four re-scopings this design
  is argued from.
- `perry/evidence/2026-08/TASK-114-delegation-prompt-v2.md § Why v1 was
  withdrawn` — the same failure in a hand-written document.
- `viewer/parsers.py § escalation` — the green-light rule § 5.2 quotes.
