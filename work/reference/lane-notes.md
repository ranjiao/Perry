# The `work` lane — why it reads the way it does

Not loaded by any subcommand. `work/SKILL.md` keeps each rule in its one-line
form and points here for the reasoning and history behind it; nothing on this
page is needed to run a subcommand correctly.

Moved out of `work/SKILL.md` on 2026-09-21 (TASK-470) to cut what every `work`
invocation loads. The prose is carried over unchanged; the heading each passage
came from is named above it.

## The single entrance

From the lane header. The shorthand `/pmo <subcommand>` used throughout
`work/SKILL.md` and its `reference/` pages is routing vocabulary for the agent,
not a command the user can type; translate it when quoting a command back to
them. Rationale for the single entrance: `$PERRY_HOME/SKILL.md § One skill,
three lanes`.

## `perry-task` is the writer

From `§ How this file is organized`.

`perry-task` is the writer, and it changes how this lane works: Perry had nine read tools and none, so "never compute a number by reading files and eyeballing it" protected the way out and not the way in. **All six statuses have a tool path** — `add`/`route`, `start`, `status` (`blocked`, `review`, and anything the named subcommands don't cover), `done`, `drop` — plus `stage`, `intake`, `resolve-intake`, `ask`/`answer` for `## User Input Queue`, `cadence-add`/`cadence-done` for the recurrence register, and `list`, which writes nothing and is the read path a front-end uses. Each write records the task store and journal through a durable recovery marker, then renders the board and appends an event. Two renames are not claimed to be atomic: an ordinary failure rolls back and a crash is completed on the next locked Perry run. The gates, the refusals and the exact per-subcommand contract are in `reference/subcommands.md`.

**Hand-editing still works and is still legitimate.** It is reported, not refused: `perry-state` counts a row with no creating event as `unrecorded` and shows it in the standup's `🔀 Drift` row. That visibility is the whole mechanism — see `perry/design/DESIGN-004-deterministic-writes.md § 5.4`.

## Why the rungs are looked up, not remembered

From `§ How this file is organized`.

**The rungs are `V0`–`V6` and you do not have to remember them.** `"$PERRY_HOME/bin/perry-explain" V4` prints what a rung is, where it is defined, and the two rules that govern it — read from `schema/state-schema.json § verification`, which is the only place they are written. A session that has never seen this project can resolve the vocabulary in one command instead of inferring it from a board cell.

## Why a V4 row has a convention at all

From `§ How this file is organized`.

Perry ran ten V4 rounds in one night with no convention and they spelled the verdict five different ways; rows then sat at `review` after their review had already failed, and it was the user who noticed rather than any check.

## Why two file models

From `§ Two file models`.

Perry organises files along **two orthogonal axes**. Confusing them is what produces the "1000-line unreadable board" anti-pattern AND the "I have to render markdown in VSCode just to read my own OKR" anti-pattern. The axes themselves, with their tables: `state-files.md § Two file models`.

## Why the tool-mediated set stops where it does

From `§ State files & size discipline`.

Everything outside the task lifecycle — `journal/` prose, `PROJECT_STATE.md`, `evidence/`, `weekly/`, `handoff/` — is still written directly, and deliberately: decision 3 scoped the first release to the task lifecycle, and those files carry judgment rather than state transitions.
