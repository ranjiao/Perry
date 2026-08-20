# TASK-079 — Migration writes a file the user marked read-only, via rename

> Moved off `BOARD.md` by triage on 2026-08-20. The row's `Next action` cell had
> grown to 1253 characters of reasoning and measurement — detail the board is
> not the place for, per `work/reference/subcommands.md § triage` ("row inflated
> → propose moving detail to `evidence/<YYYY-MM>/<TASK-ID>-*.md`, leaving only
> Status + Next action + Evidence path on the board").
>
> Priority P1 · status `not_started` · rung V4
> · depends on —
> · blocked by —

## The cell, verbatim

FOUND 2026-08-18 while fixing TASK-044's planning crash, by asserting what I ASSUMED rather than what happens — the test failed and the code was right. write_atomic writes a .tmp and calls Path.replace, and A RENAME NEEDS WRITE PERMISSION ON THE DIRECTORY, NOT ON THE TARGET. So a file the user has chmod-ed read-only is migrated like any other, and nothing in the plan says the bit was there. THE QUESTION IS A POLICY ONE ABOUT SOMEBODY ELSE'S FILES and I deliberately did not decide it mid-fix: (a) the bit is an explicit user signal and ADR-004's whole posture is 'the user declares', so migration should refuse or at least name it; (b) it may be incidental — copied off a read-only medium, or a stale mode from an archive — and refusing would block a migration for a reason unrelated to shape. PINNED BY A TEST TODAY: the file IS migrated, and the restore point carries its original bytes, so the recovery path covers it — which is what makes the current behaviour survivable rather than merely undetected. NOT TRUE TODAY: that the plan mentions the mode at all. Whichever way this is decided, TASK-044-spec says migration is 'not silent — every file it touched, listed, with what changed in each', and a permission it overrode belongs in that list.

## What is still undecided — USER-004

The policy half of this row was minted as `USER-004` on 2026-08-20, because the
cell above says outright that it was deliberately not decided and names two
defensible readings:

- (a) the read-only bit is an explicit user signal, and ADR-004's posture is
  "the user declares", so migration should refuse or at least name it;
- (b) it may be incidental — copied off a read-only medium, or a stale mode from
  an archive — and refusing would block a migration for a reason unrelated to
  shape.

An agent cannot pick between those on the user's behalf: both are about how much
authority Perry claims over somebody else's files.

The other half does not wait on it. `TASK-044-spec` already requires the
migration plan to be "not silent — every file it touched, listed, with what
changed in each", and a permission it overrode belongs in that list under either
reading. That is why the row stays `not_started` rather than `blocked`.
