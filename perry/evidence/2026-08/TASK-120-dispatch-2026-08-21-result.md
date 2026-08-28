# TASK-120 — result

> Date: 2026-08-21 · Executor: claude-subagent · PR: https://github.com/ranjiao/Perry/pull/24
> Branch: `coding/task-120-kr-progress-provenance` · Cycle time: ~35 min
> `perry-goals/list` **2.0 → 2.1**, additive: four keys added, none removed or
> retyped. `schema/state-schema.json` **untouched** — verified by diff, and the
> hard stop was live, so this is a real avoidance rather than luck.

## The shape: Perry exposes the contradiction, it does not resolve it

One derivation in `bin/lib/__init__.py`, three sibling keys per KR, emitted by
both payloads. Verified on this repository:

```
P002-O1-KR1  current 0.0  target 1.0
        provenance  state=asserted  measured=false  source=linkage-register
        completion  total 4  done 4  open 0
P002-O2-KR2  current 0.0  target 0.0
        provenance  state=asserted  measured=false
        completion  total 2  done 0  open 2
```

`P002-O1-KR1` no longer reads as 0-of-1 progress: it reads as **an author's assertion
of 0 against four closed tasks**, and Perry resolves neither. `P002-O2-KR2` can no
longer be read as met, because nothing claims the zero was measured.

**No `met` / `achieved` / `progress` / `ratio` key exists** — asserted as an
absence in the tests. No percentage is emitted anywhere: counts only, in their
own unit, so the tally cannot be misread as a metric value. That is the line the
spec drew and it held.

## What it rejected, and one of the rejections is the interesting one

- any ratio or percentage;
- a conformance entry for *"`current` disagrees with its tasks"* — that would be
  Perry inferring the metric from the edges, which is the forbidden move one
  step removed;
- **any new authored field in the register.** `asserted_at` reuses the
  register's existing top-level `updated`, and `asserted_scope: "register"` is
  emitted so a reader cannot mistake it for a per-KR date. **That choice is what
  kept `schema/state-schema.json` out of the change** — the agent found the
  cheap path around a gate rather than asking for a release.

## The tally is what flips P002-O1-KR1, not the staleness check

Worth recording because it is counter-intuitive: P002-O1-KR1 is **not stale by any
timestamp test** — all four of its tasks closed *before* the register's
`updated`. The contradiction is visible only because the completion tally sits
beside the number. A design that shipped staleness alone would have left that
KR reading exactly as wrongly as before.

## Staleness, both directions on one fixture

```
not stale  "no linked task has changed state since 2026-08-15T12:00:00"
stale      "1 linked task changed state after 2026-08-15T12:00:00:
            TASK-003 (in_progress → done)"
           moved_tasks: [{id, from, to, at}]   ·  only that KR goes stale
```

The fixture also carries a `next` event dated after the assertion, **so a check
keyed on the event name rather than on whether `to` is a status would redden.**

## Parity, stated separately as instructed

`perry-goals/list` **before**: 0 documented-not-emitted, **5** emitted-not-documented.
**After**: 0 and **5** — the same five, byte-identical, TASK-131's, not hidden
inside. Documented 54 → 77, emitted 59 → 78. Repo-wide total unchanged at 17.

## Four findings handed back

1. **The `Z` problem, unresolved and documented in the contract.** The register
   writes `updated` as ISO with a `Z`; `.perry/events.jsonl` writes `ts` as naive
   local time. There is no honest conversion, so the `Z` is **stripped rather
   than applied**, and a register written within a few hours of a task move can
   order wrongly. Fixing it means deciding what the event log's `ts` means — a
   row of its own, touching every consumer.
2. **`tests/fixtures/contract-shapes.json` is stale w.r.t. its own recorder.**
   `--record` wants to add an `empty_lists` block to two contracts and drop a
   trailing newline. The agent refused to re-record rather than hide unrelated
   drift in this row. **Someone will eventually re-record it into an unrelated
   diff.**
3. **`viewer/serve.py` renders the chain view from `viewer/parsers.py`**, not
   through `bin/lib`, so the viewer still shows `current` with no provenance.
4. **`measured` is `false` everywhere, by construction, until something re-runs
   a metric.** Honest — and it means `stale` is Perry's only mechanical opinion
   about a KR number.

## Two notes on this project's own rules

- The `current: 0` default the spec targeted lives in
  `goals/state/linkage_TEMPLATE.md:13`, which writes it into every new register.
  That is **authoring**, belongs to TASK-119's writer, and was correctly not
  touched. `_num()` already returned `None` for an unwritten value, so V3 item 2
  was true but untested; it is now locked by four tests.
- **TASK-091's Definition of Done makes `bin/` a place where the history of that
  defect cannot be written down.** The agent's first draft of a comment named the
  deleted symbol and reddened `test_goals_writer`; it rewrote the comment to
  describe the symbol without naming it. Same family as TASK-126 and TASK-112 —
  a guard that forbids describing the thing it guards.

## Process error, mine

The worktree was cut from `feat/work-modes` **before** I committed the spec, so
the agent had to fetch it with `git checkout e71d7c0 -- <path>`. Corrected for
TASK-122 and TASK-141: commit the spec, *then* cut the worktree.
