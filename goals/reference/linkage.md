# `okr link` — owning `phase/<NNN>-linkage.md`

Loaded when `/okr link` fires, or whenever PMO hands over an attribution result.

The linkage graph is the one Perry file that is machine-written and machine-read
on both sides: Perry resolves KR attribution through it, and the frontend draws
the project's O→KR→task chain from it. `okr` is its **only writer** — PMO reads
it and hands changes over, because PMO never writes `phase/`.

Shape, field list and the three load-bearing rules: `$PERRY_HOME/schema/README.md
§ The linkage contract`. Attribution rules: `$PERRY_HOME/reference/okr-linkage.md`.

## The four moments it changes

| When | What |
|---|---|
| `plan-phase` | Created from `state/linkage_TEMPLATE.md` — objectives + KRs, `tasks: []`, `unlinked: []`, one `projects[]` entry per Project. See `phases.md`. |
| `plan-week` | Each approved task id appended to its KR's `tasks[]`. See `weekly.md` step 7. |
| **PMO hand-off** (`add-task`, `coordinate`, `digest`) | PMO resolved — or failed to resolve — a task's KR and hands the result here. This file. |
| `score-phase` | Snapshotted with the phase, then carried forward or retired. See `phases.md`. |

Every write bumps `updated` to a full ISO datetime:

```
date -u +%Y-%m-%dT%H:%M:%SZ
```

A day-only value is **dropped by both readers**, not guessed at — so a graph with
`updated: 2026-08-14` reports "never updated", which is worse than the truth.

## `link` — accepting PMO's hand-off

PMO's attribution gate (`work/reference/subcommands.md § add-task`) ends in one of
three outcomes, and each maps to one edit here. PMO prints the outcome; `okr`
performs the write.

### 1. Resolved → append the edge

```
/okr link <TASK-ID> <KR-ID>
```

Append `<TASK-ID>` to that KR's `tasks[]`. Refuse if:
- the KR id is not in this phase's graph → say so, list the phase's KR ids;
- the task already appears under a **different** KR → refuse and surface both.
  A task under two KRs makes its attribution ambiguous, and `bin/perry-lint`
  rejects it. Move it, don't duplicate it.

If the task is currently in `unlinked[]`, remove it there in the same edit —
otherwise it renders as both attributed and drifting.

### 2. A name was confirmed as an existing Project → append the alias

```
/okr link --alias <PROJECT-ID> "<the other name>"
```

Append to that project's `aliases[]`. This is what makes name drift survivable:
a later progress report arriving under the old name resolves to the same KR
instead of failing. Refuse if another project already claims that name or alias
— that ambiguity is exactly what the registry exists to prevent, and the linter
rejects it.

**Only on the user's confirmation.** Never merge two names because they look
alike; that is the fuzzy match the whole gate forbids.

### 3. Unresolved → declare it unlinked

```
/okr link --unlinked <TASK-ID>
```

Append to `unlinked[]`. This is a **declaration**, not an inference: never
populate the list by subtracting linked tasks from `BOARD.md`, which would report
the entire un-triaged backlog as drift the day the graph is written.

An unlinked task is a User-Input-Queue item. Surface it at the next snapshot so
the user can attribute it; do not quietly attach it to the nearest-sounding KR to
make a number look complete.

### 4. A new Project appeared mid-phase

```
/okr link --project <PROJECT-ID> <KR-ID> "<name>"
```

Append to `projects[]` with `objective` derived from the KR id (`P-O1.2` → `O1`;
they must agree or the linter refuses) and `status: active`. Flip `status` to
`done` / `dropped` as the Project resolves — the entry stays, because a retired
Project's name must keep resolving for historical progress reports.

## After any write

```
"$PERRY_HOME/bin/perry-lint" --root .
```

It parses the graph with the **same reader Perry uses**, so a pass means Perry
can read it. It also checks: no task under two KRs, no two projects sharing a
name or alias, every project's `objective` agreeing with its `serves` KR, and
every KR id present in the phase file.

## What `okr` must not do here

- **Not invent a number.** `target` / `current` are numbers or absent. A KR whose
  target is prose ("最大回撤 ≤15%", "vs 1pp 线") gets a `metric:` string and no
  `target`. Half of real KRs are ceilings; a ceiling drawn as a progress bar
  reports a risk budget as two-thirds achieved.
- **Not fill an empty KR.** A KR with zero tasks is the most valuable thing the
  chain shows — a commitment nobody is working on. Do not invent a task for it.
- **Not drop a done task.** Completed work stays in `tasks[]`; that is what an
  achieved KR looks like.
- **Not leave `{{placeholder}}` behind.** Both readers refuse a frontmatter
  containing `{{…}}` outright, because every placeholder is a valid YAML string
  and an unfilled template would otherwise render as a committed OKR.
