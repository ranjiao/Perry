# TASK-215 — result: the writer stamps `> Last updated:`

> Branch `coding/2026-08-29-overnight-batch`, commit `bb149fe`. Rung **V3**.
> Measured 2026-08-29.

## The defect

`BOARD.md`'s preamble read:

```
> Last updated: 2026-08-16 (21st pass — DESIGN-004 handed off, 6 tasks)
```

on **2026-08-29** — thirteen days stale, on a file `perry-task` re-renders
dozens of times a day. `perry-state` publishes it as `board.last_updated` and
the standup prints it, so a number every reader takes at face value was
maintained by nobody.

## The decision: the writer, not the renderer

The spec offered two branches — *"the header is written by the renderer, or
removed"*. Neither literal branch is right, and the reason is worth recording.

**Not the renderer.** `perry-tasks render --byte-compare` and `perry-lint`'s
store-drift census both compare a fresh render against the file on disk. A
renderer that stamped today's date would report the board as **drifted every
morning** until somebody happened to write to it. A check that goes red on the
passage of time is a check people learn to ignore, and this repository has
already paid for one of those.

**Not removal either.** `board.last_updated` is a published payload key;
removing it is a contract change requiring a version bump, and the field is
useful once it is true.

So: *"last updated" means the last **write***, and a re-render is not a write.
`commit()` stamps it before rendering, which also means the rendered text
carries the new header — so the next render reproduces the file byte-for-byte
and the drift check stays quiet.

## Verification

Measured on a full copy of Perry's own state (board, store, event log):

| | before | after one `perry-task next` |
|---|---|---|
| header | `2026-08-16 (21st pass — …)` | `2026-08-29` |
| `perry-lint` store drift | `225 record(s), 0 row(s) drifted` | `225 record(s), 0 row(s) drifted` |
| `render --byte-compare` | — | **clean** |
| `render --write` afterwards | — | header **unchanged** |

`perry-state --json` → `board.last_updated: 2026-08-29`, agreeing with the file.

## Two ways not to cry wolf, both tested

**A board with no such header does not get one.** The line is Perry's own
template convention, not a required section; adding it to somebody else's board
would be this tool writing a line the project never asked for.

**The matcher anchors on the quote line.** `TASK-215`'s own title contains the
words *"Last updated header"* and sits in a table row on the board this ships
with — line 94 of the fixture I measured on. A looser matcher would have
rewritten a task's title on the first write. The matcher also takes the
localized spelling and the full-width colon, so a Chinese board is not silently
skipped.

## What was dropped, deliberately

The editorial parenthetical. A rendered file's header is not a place for prose
nobody re-derives; `journal/2026-08/2026-08-16.md` is where *"21st pass,
6 tasks"* belongs and already carries it.

## Mutation

| mutation | result |
|---|---|
| don't stamp at all | 4 failures |
| drop the quote anchor | 1 failure — the task-row case |
| invent the header when absent | 1 failure |

Each restored byte-identical (`md5` checked). The third mutation's first
attempt did not match its anchor and reported a meaningless OK; it was re-run
with a unique anchor, which is the only reason it counts.

**Suite, both runners**: `bash tests/run` 3 modules red / 5 failures;
`unittest discover` 2849 tests / 8 failures — identical sets to `45a355d`. This
change adds none.
