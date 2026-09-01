# TASK-203 — why the branch is held out of `main`

Measured 2026-08-29, after USER-906 was answered with option B.

`coding/task-203-register-stores` (3 commits, tip `d075698`) merges into
`main` without a conflict and its suite is at baseline. It is held anyway,
and this file is the measurement that says why.

## The reproduction, on this repository's own data

The round 3 reviewer measured the truncation on a synthetic project with a
queue-mode track named `ops`. This repository declares a queue-mode track of
its own — `.perry/config.md § Tracks` carries `intake | queue | standing |
new→triaged→in_progress→resolved | 6 | 5d | weekly | V3`, declared 2026-08-20
under TASK-133 — so the same door is reachable here.

Probe worktree at `main` + `coding/task-203-register-stores`:

```
$ bin/perry-task intake --title "probe alpha"   # ×3, to create the store
$ wc -c perry/intake.jsonl
    8240 perry/intake.jsonl        # 24 records, derived from the board's ## Intake
$ md5 -q perry/intake.jsonl
72349d0104a113a327bcf3e003dcd0a9
```

An ordinary `add` onto the queue track, with the board's `## Intake` section
present, is SAFE — 8240 bytes in, 8240 bytes out:

```
$ bin/perry-task add --title "a queue task probe" --track intake --priority P2 \
    --deliverable "…" --verification "…"
perry-task: wrote TASK-232 (add) → tasks.jsonl + intake.jsonl + journal + BOARD.md + event
$ wc -c perry/intake.jsonl
    8240 perry/intake.jsonl
```

Remove the `## Intake` section from `BOARD.md` — the state a project has
before its first intake row, and the state `/pmo triage` can produce — and the
identical command destroys the store:

```
$ python3 -c "…"   # delete the ## Intake section, nothing else
$ wc -c perry/intake.jsonl
    8240 perry/intake.jsonl        # 24 records
$ bin/perry-task add --title "second queue probe" --track intake --priority P2 \
    --deliverable "…" --verification "…"
perry-task: wrote TASK-233 (add) → tasks.jsonl + intake.jsonl + journal + BOARD.md + event
$ wc -c perry/intake.jsonl
       0 perry/intake.jsonl        # 0 records
$ bin/perry-lint
  0 error(s), 5 warning(s)
  · intake store: 0 record(s), 0 row(s) drifted
```

**Exit code 0. 24 records to 0. `perry-lint` calls it clean.**

`cmd_add`'s queue branch calls `ensure_section("Intake")` at `bin/perry-task:2973`
before `commit()` asks the gate at `:2549`, so the gate sees a freshly created,
readable, EMPTY table, answers yes, derives `[]`, and writes zero bytes.

## Why that is a merge blocker and the other three branches were not

`coding/2026-08-29-overnight-batch` carries TASK-095's four wrong rounds and was
merged, because the writer was measured on this repository's data first and does
NOT refuse here — this project's config store and its `## Tracks` table agree, so
the regression the round 5 reviewer found is not reachable on `main`.

This branch is the opposite: the defect IS reachable on `main`, it destroys a
canonical store rather than blocking a write, it is silent, and the linter
reports the result as clean. There is no recovery short of the event log.

Merging it would also make the row's own fix harder to verify: the invariant
USER-906 chose — an ordinary write may never SHRINK a canonical store — has to
be proved against a store that still has records to lose.

## What round 4 does

Round 4 starts from `main`, not from this branch. The branch stays for reference;
whether it is rebased or abandoned is round 4's call once the invariant is in
place. Requirements are on the row's Next action.

The regression test comes FIRST and must be red before the fix: 24 records to 0
on `perry-task add --track intake` with the `## Intake` section absent.
