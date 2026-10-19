---
name: goals
description: The goals lane of the perry skill. Plan and revise objectives, KRs, checks, phases and commitments through native kernel items; keep narrative drafts and retros as owned attachments. Resolve attribution by exact identity and ask on ambiguity.
---

# Goals — Perry's goal-setting partner

This is a lane inside `/perry`, loaded by the root router. Translate shorthand
`/okr` to `/perry goals` in user-facing commands. Read this file in full, then
only the selected procedure. Kernel state is authoritative; legacy `OKR.md`,
`okr.jsonl`, `linkage.jsonl` and `phase/CURRENT` are migration inputs, never writers.

## Before acting

Run the router's safety startup once, preserving recovery/interrupted refusals.
Pin `PERRY_HOME` to the actual loaded skill root; use the configured document and
chat languages, project anchor and state root. Read `.perry/hook.md`.
Read `work/reference/kernel.md`, `perry-kernel describe`, and `template show`
for the versioned command/data contracts. Every CLI call names absolute `--root`;
rehearsals also name scratch `--store` with `PERRY_KERNEL_TESTING=1`.
If the six F types are absent, report migration required. Never initialize over
an activated work store or fall back to a legacy writer.

```bash
"$PERRY_HOME/bin/perry-kernel" query --root /absolute/project --input @/absolute/scratch/query.json
```

Read bodies: `{"type":"phase","state":["phase_active"]}`,
`{"type":"objective"}`, `{"type":"kr"}`, `{"type":"check"}`.
Follow every `next_after` until `truncated:false` for complete procedures.
Read one item and its attachments with `item get`. A refusal/nonzero exit is not
empty state. Surface more than one active phase as an inconsistency; do not pick.

## Snapshot and measurement boundary

Lead with one factual sentence, then the active phase, version-scoped Objectives,
KRs, checks and unresolved attribution. Use titles with IDs. Render only kernel
counts and derived `check_metric.met`, `check_metric.fraction` and `rollup`; missing data is
`—`. Do not average checks, derive completion from closed tasks, parse a prose
metric into numbers, or claim criteria/user approval from a structural pass.
A direct child metric folds one level only, regardless of state or stretch.
Do not present an Objective's one-level rollup as a recursive KR/check aggregate.
Read measurement events for age/provenance and explain stale observations as such.
Root owns the combined dashboard/next procedure (DESIGN-023 G); this lane does
not call the retired legacy recommendation engine or maintain a second dashboard.

## Ownership and hand-off

Goals alone authors `OKR.md`, `phase/` and `plans/` narratives and their native
objective/KR/check/phase fields. Native records carry structured facts; these
Markdown documents carry rationale, rules, assumptions and retros, with no
second current KR table or structured metadata header to synchronize.
Use `attach add` with exact state-root-relative ref and optional SHA256 after
writing an owned narrative. The kernel never opens or approves it.
Goals never writes work's evidence/journal/tasks or decide's designs/ADRs.
Work creates approved tasks; goals accepts attribution through typed links.
History is native events. No procedure here appends journal or legacy events.

## Procedures

| User action | Read first | Result |
|---|---|---|
| `init`, `revise` | `reference/setup.md`, `reference/elicitation.md`, `reference/planning.md` | reviewed draft, explicit approval, new version-scoped items |
| `plan-phase <slug>` | `reference/phases.md`, `reference/elicitation.md` | approved native phase and scoped goals; attached ten-section narrative |
| `commit <promise>` | `reference/phases.md`, `reference/elicitation.md` | objective with goal_level commitment; no second register |
| `kr add/restate/withdraw`, `krs` | `reference/phases.md` | native fields/transitions, preserved history |
| `check`, `measure` | `reference/phases.md` | declared conditions; actual measured current only |
| `link`, alias, unlinked | `reference/linkage.md`, `../reference/okr-linkage.md` | explicit attribution or visible unknown |
| `score-phase`, `snapshot` | `reference/phases.md` | work retro → goals scoring/final snapshot → work close |
| `plan-week` | `reference/weekly.md` | approved proposals handed to work |
| `pivot`, `dashboard` | `reference/pivots.md` | explicit scope revision / native goal read |
| `help` | this table; selected reference if named | navigation only, no startup/write |

## Input and approval rules

Use the shared input-quality rubric as advisory coaching (at most three issues).
Keep the interview's premise/escape behavior, ≤3 consequential choices at once,
and host-native choice rendering. A clean rubric is not approval. Do not repeat
questions already answered. Never silently revise a goal, target, baseline or
commitment; record the user's reason and reviewed attachment hash in event notes.
The kernel's `approval_ref` required guard checks shape only. Actual consent and
its scope are the agent's responsibility. A historical migration reference is
not consent for a new plan. V4 remains fresh-context review; V5 remains the named
human's actual action under work's unchanged verification contract.

Keep overall narrative ≤200 lines and phase narrative ≤300 lines. Discuss a
split/trim or explicit reasoned override before exceeding those caps. Ask work
to save foreign-owned evidence. Unknown baselines stay unknown. Keep stretch
separate from commitments; do not shame stretch underdelivery.
Versions are append-only scopes: never reuse a legacy `O3-KR1` without its version
or write over prior-version items. Native IDs are minted inside the kernel.
