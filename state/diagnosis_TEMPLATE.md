---
diagnosis: 1
project: "{{project name}}"
root: "{{absolute path to the project root}}"
depth: standard
lanes: [context, docs, concurrency, tracking]
started: "{{YYYY-MM-DD}}T{{HH:MM:SS}}Z"
updated: "{{YYYY-MM-DD}}T{{HH:MM:SS}}Z"
stage: scan
archetype:
  scanned: "{{software | knowledge-base | ops | null}}"
  scanned_confidence: "{{high | medium | low | none}}"
  confirmed: "{{what the user said — this wins, always}}"
maintenance_ceiling: "{{Q6 answer: e.g. 'three files' | 'a board' | 'unknown'}}"
measurements:
  always_loaded_lines: 0
  always_loaded_budget: 200
  docs_total: 0
  docs_orphaned: 0
  has_index: false
  has_spine: false
  has_decision_log: false
  has_check: false
  extra_worktrees: 0
findings:
  - id: CTX-01
    severity: error
    source: scan
    title: "{{one line, from bin/perry-diagnose}}"
    status: open
interview:
  - q: Q3
    asked: "In the last month, how many times did agent work get lost to a collision?"
    answer: "{{verbatim}}"
prescription:
  - id: RX-1
    change: "{{one line — what actually changes on disk}}"
    closes: ["CTX-01"]
    cost: "{{~10 min}}"
    reversible: true
    status: proposed
moves:
  - from: "{{path before}}"
    to: "{{path after}}"
    rx: RX-1
restore_point: "{{branch name, or .perry/diagnose/<date>-backup/, or null}}"
---

# Diagnosis — {{project name}}

> **Owner**: the top-level `perry` skill, via `/perry diagnose`. It is the
> **only** file diagnose writes. Changes to Perry state files go through
> `/okr`, `/pmo`, `/design`; changes to the project's own documents are made
> directly at stage 4, and every one of them is recorded in `moves[]`.
> **Tier**: 2 (agent-state, no line cap).
> **Spec**: `diagnosis: 1`. Procedure in `$PERRY_HOME/reference/diagnose.md`;
> the research it applies is in `$PERRY_HOME/reference/project-archetypes.md`.

## What each part is for

| Key | Purpose |
|---|---|
| `stage` | Where the pipeline stopped: `scan` → `read` → `interview` → `prescribe` → `execute` → `done`. A resumed run reads this and nothing else. |
| `archetype.scanned` | What `bin/perry-diagnose` inferred from folder shapes. May be `null`; that is an honest answer, not a failure. |
| `archetype.confirmed` | What the user said the project is. **Overrides `scanned` unconditionally** — the scan reads directory names, the user knows the project. |
| `maintenance_ceiling` | The Q6 answer. A **hard cap** on the prescription, not a factor to weigh. An unmaintained organ reports stale state that everything downstream believes. |
| `measurements` | Copied from the scan payload. Every number in the report comes from here; a field the scan didn't carry stays absent and prints `—`. |
| `findings[]` | `source: scan` (measured) or `source: interview` (the user reported it). Nothing else may be a finding — an observation with neither behind it is Perry's taste, and taste does not get an ID. |
| `findings[].status` | `open` → `closed` / `accepted-risk` / `disputed`. `disputed` is real: the user may reject a threshold, and thresholds are calibrated defaults rather than laws. |
| `prescription[].closes` | The finding IDs this change resolves. **An item that closes nothing does not belong on the list.** This is the rule that is easiest to violate and most expensive to lose. |
| `prescription[].status` | `proposed` → `accepted` / `done` / `declined` / `deferred`. |
| `moves[]` | Every file relocation, `from → to`. This is what makes the whole run reversible by hand, so it is written as each move happens, not batched at the end. |
| `restore_point` | The branch or backup directory created before the first change. Stage 4 may not begin while this is `null`. |

## Rules (do not violate)

- **Every prescription traces to a finding; every finding traces to a
  measurement or an interview answer.** No exceptions, and no prescriptions
  that originate in Perry's preferences.
- **Zero findings is a valid result.** So is a prescription of pure
  subtraction. A diagnostic that must find something to justify itself is one
  the user stops reading.
- **Nothing is deleted.** Moves and pointers only; deletion is proposed as a
  task the user performs.
- **No file is rewritten unless it was read in full.** The user's words survive
  a refactor; only their location changes.
- **Declined prescriptions are kept**, never re-proposed on `--recheck` unless
  the underlying finding materially changed. Repeating rejected advice is how a
  tool trains its user to skip it.
- **The ceiling wins over the evidence.** If the scan justifies six changes and
  the user will maintain two, prescribe two and say what was cut.

## After execution

Re-run the scan and record both counts, so the refactor is judged by movement
rather than by assertion:

```
"$PERRY_HOME/bin/perry-diagnose" --root . --text
```

On a Perry project, `"$PERRY_HOME/bin/perry-lint" --root .` must also pass
before `stage: done`.
