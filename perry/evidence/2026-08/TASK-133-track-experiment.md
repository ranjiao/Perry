# TASK-133 — the first non-`project` track, and what a mixed spine actually costs

> Date: 2026-08-20 · Run by: PMO Agent, in the main checkout
> Question it was run to answer: DESIGN-003's `mode` enum bundles *spine*
> (how goals decompose) with *flow* (how an item advances). Is that coupling
> mechanical, or only prose?

## Answer: it is prose. The mechanism was never coupled.

The three measurements below are the whole result.

## 1 · Declaring the track — KR-O1.3 holds, with one condition

One track added to `.perry/config.md § Tracks`:

```
| intake | queue | standing | new→triaged→in_progress→resolved | 6 | 5d | weekly | V3 |
```

| | measured |
|---|---|
| files changed by the declaration | **1** (`.perry/config.md`) |
| state files rewritten | **0** — `BOARD.md`, `perry/tasks.jsonl` and `OKR.md` byte-identical by md5 before and after |
| `perry-lint` | 0 errors, 3 pre-existing NS-01 warnings |
| both tracks parsed | yes, with `stage_list`, `wip`, `sla`, `cycle`, `default_rung` all resolved |

**The condition, and it is the one raised against this KR earlier:** this repo
has **no `.perry/config.jsonl`**. `perry-config verify` says so —
*"no store on disk yet"*. So the config is still a plain document here and the
edit is genuinely one file. The moment someone imports the config store
(TASK-092/097's act), the same declaration becomes a file **and** a store write,
and a hand edit becomes reported drift. **KR-O1.3 is not falsified today; it is
falsified the day the store lands**, and nothing currently warns about that.

## 2 · The central test — a queue-track row carried a `kr:` edge with zero friction

A probe row was created on the `intake` track and attached to `P002-O1-KR3`, a KR of
a `project`-mode phase:

```
attribution.linked      4 → 5
attribution.linkage_error  ''
TASK-134 in unlinked    False
perry-lint              0 errors
```

Nothing refused it. Nothing warned. Searched for a gate and found none:

- no code in `bin/perry-state` or `bin/perry-task` conditions a KR edge on a
  track's mode;
- `perry/phase/002-linkage.md` contains neither `mode` nor `track`;
- *"No objectives cascade"* appears twice, both in `modes/queue.md` — at line 16
  (the contract table's `Spine` cell) and line 188 (prose). It is a
  documentation statement, not an implemented rule.

**So "organise goals with `project`, advance tasks with `queue`" already runs.**
What is missing is not the mechanism — it is that the mode file tells the agent
not to, and that triage therefore never asks the KR question on a queue track.

The probe row was dropped and its edge removed; `linked` is back to 4.

## 3 · Three defects the experiment surfaced, none of them the one it was testing

**TASK-135 — a declared track cannot be populated.** `--track` is accepted by
`add` (at creation) and `route` (intake row → task). There is no
`perry-task track <id>`, and `status --track` is refused. So a project that
declares a second track starts it **empty and cannot move any existing work
onto it**. The six rows that genuinely arrived rather than being decomposed —
TASK-124, 125, 126, 130, 131, 132 — belong on `intake` and cannot get there.
This is why `intake` is declared and empty right now, and why KR-O1.1 is not
met by this experiment.

**TASK-136 — the SLA is decoration.** The track carries `sla: 5d`. `perry-state`
computes `stage_counts` and `wip_breaches` for it and nothing else. The only
consumer of a track SLA anywhere is `lib/__init__.py § classify_due`, which
governs a **Commitments `Due` cell**, not a row clock. `today − Arrived` is
computed nowhere. `modes/queue.md` says a track *without* an SLA "cannot run the
breach step, and triage reports that rather than skipping it" — a track *with*
one cannot run it either, and nothing reports that.

**TASK-137 — a new queue row is born in the second stage.** `intake` declares
`new→triaged→in_progress→resolved`; the probe row was created with
`stage: triaged`, skipping `new`.

## 4 · What this says about the design question

The user's reading is right and cheaper to act on than it looked:

- **Claim 1 — one folder, several shapes — was already designed.** DESIGN-003
  § 5.1 rejected per-project mode explicitly, calling it "empirically wrong",
  and named *this repository* as the counterexample. `1..N` tracks is the
  answer; `TeckWork` is two rows in one table.
- **Claim 2 — `mode` is two axes wearing one name — is a new finding.** It is
  not in § 8's open questions, and § 5.1's own semantics table is the evidence:
  every row of it is an independent axis, and the four modes are four diagonal
  picks. `Default rung` is arguably a third axis (consequence), since this very
  track overrode queue's V2 to V3 for a reason that has nothing to do with flow.

**The cheap shape of a fix**: keep `Mode` as a preset **name** that expands to a
`(spine, flow, default_rung)` triple, and let a track override any leg. A
project writing only `Mode: project` changes by zero bytes. What it costs is a
one-time judgement, slot by slot, about which axis each of `modes/*.md`'s ~40
contract rows belongs to — and some are genuinely ambiguous ("the unit that gets
an ID" reads like spine but drives the board's row shape, which is flow).

That judgement is an RFC, not a task. This file is its measurement.
