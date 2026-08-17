# TASK-040 — `BOARD.md § Top risks` becomes a table with a writer

> Source: `schema/state-schema.json` → `BOARD.md` → `^Top risks\b|^主要风险`; the same "reader with no writer" class as TASK-039 (`## User Input Queue`) and TASK-021 (`## Cadence`)
> Dispatch mode: manual
> Estimated cycle: medium
> Subjective verification: whether the column set is the right one — a judgement about what a risk register needs to record, not a fact a test settles
> Touches architecture: `work` lane's ownership of `BOARD.md`; `perry-task/list` is a **frozen** contract
> Deployed: no

**This file is the rubric a V4 reviewer scores against.**

## What must be true

### 1 · A risk can be opened and cleared by a tool

- [ ] `ID`, `Risk`, `Opened`, `Status` are written per the schema, resolved by
      name and never by position.
- [ ] Opening and clearing each write board + journal + event together.
- [ ] Clearing records *when* and does not delete the row's history. A risk
      that vanishes when it clears leaves no record that it was ever run.

### 2 · A bullet list is a valid `## Top risks`

This is the requirement most likely to have been missed, and the schema says
it in as many words: this table is skipped **when the section is present but
still holds a bullet list**, and *"every Perry project except Perry itself was
on bullets the day this landed"*.

- [ ] A bullet-list section is read, not rejected, and not rewritten.
- [ ] `perry-lint` does not report it as malformed.
- [ ] The writer's behaviour on such a section is deliberate and stated —
      whether it refuses, or converts on request. **Automatic conversion is a
      defect**: "no automatic rewrite of a project's existing structure" is an
      Anti-Goal in Perry's own OKR.

### 3 · The frozen contract did not move

`perry-task/list` is published to another program (aiMark) and versioned
separately from Perry.

- [ ] Any key added to the payload is additive and the contract's minor
      version moved with it.
- [ ] `schema/task-list-contract.md § Changelog` records the change.
- [ ] No existing key changed shape. A consumer built against the prior
      version still parses.
- [ ] Risk rows do **not** appear in `tasks` / `open` / `closed`. A risk is
      not a task; counting it as one inflates every board number permanently.

### 4 · Analysis stayed with the agent

The user's own framing when this was split from TASK-039: *User Input Queue
and Cadence suit deterministic code; Top risks is non-standard analytical
judgement and suits an agent.* So the tool records risks; it does not rank,
score or decide them.

- [ ] Nothing in the tool assigns severity, priority or likelihood.
- [ ] The procedure that reads this section still asks the agent to judge.

## Out of scope

- Migrating any project's bullet list.
- Linking risks to tasks. No source asks for it and a link nothing reads is
  the defect this task exists to remove.

## The open question for the reviewer

The column set is `ID | Risk | Opened | Status` — four columns, and no owner,
no mitigation, no review date. Say whether that is sufficient or under-built,
and argue it from what a reader of this section needs, not from what other
risk registers conventionally carry. This is the one item on this rubric with
no right answer in the sources; it is the row's `Subjective verification`.

## Verification the reviewer should expect to find

| Rung | Check |
|---|---|
| V1 | `perry-lint` clean |
| V2 | tests covering the bullet-list fallback and each refusal |
| V3 | a run against a real project still on bullets |
| V4 | this file, scored by someone who did not build it |

Each refusal verified by reverting it and confirming the test goes red.
