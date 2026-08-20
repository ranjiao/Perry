# TASK-066 — Split perry-task by subcommand group

> Moved off `BOARD.md` by triage on 2026-08-20. The row's `Next action` cell had
> grown to 467 characters of reasoning and measurement — detail the board is
> not the place for, per `work/reference/subcommands.md § triage` ("row inflated
> → propose moving detail to `evidence/<YYYY-MM>/<TASK-ID>-*.md`, leaving only
> Status + Next action + Evidence path on the board").
>
> Priority P2 · status `not_started` · rung V4
> · depends on TASK-065, TASK-038
> · blocked by TASK-038

## The cell, verbatim

RECONSIDER UNDER ADR-007 2026-08-19. Splitting perry-task by subcommand group was sized against a tool that parses and writes markdown. Under ADR-007 that tool loses its board reader, its row renderer and its cell escaping — TASK-090, 094 and 095 between them. The split may be unnecessary at the smaller size, or may want different seams. Do not start this before TASK-095; sizing a refactor against code that is about to be deleted is how a refactor becomes wasted.
