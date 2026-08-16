---
adoption: 1
project: "{{project name}}"
root: "{{absolute path to the project root}}"
depth: standard
mode: fresh
lanes: [okr, board, design, knowledge, arch]
started: "{{YYYY-MM-DD}}T{{HH:MM:SS}}Z"
updated: "{{YYYY-MM-DD}}T{{HH:MM:SS}}Z"
stage: scan
sources:
  - id: SRC-001
    kind: readme
    tier: A
    path: "README.md"
    read: false
  - id: SRC-002
    kind: git_recent
    tier: B
    path: ".git"
    read: false
clusters:
  - id: CL-01
    name: "{{cluster name — the work, not the source}}"
    seed: commit_scope
    kr: "{{P-O1.1 once attributed, else omit}}"
candidates:
  - id: CAND-001
    kind: task
    confidence: high
    cluster: CL-01
    evidence: ["SRC-001#L12-40", "git:0000000"]
    proposal: "{{one line — what this candidate asserts}}"
    target: "BOARD.md"
    status: pending
---

# Adoption dossier — {{project name}}

> **Owner**: the top-level `perry` skill, via `/perry adopt`. It is the **only**
> file adoption writes. `OKR.md`, `BOARD.md`, `design/` and the rest are written
> by their owning skills at stage 4, through the normal subcommands.
> **Tier**: 2 (agent-state, no line cap).
> **Spec**: `adoption: 1`. Contract in `$PERRY_HOME/schema/state-schema.json`;
> procedure in `$PERRY_HOME/reference/adoption.md`.

## What each part is for

| Key | Purpose |
|---|---|
| `stage` | Where the pipeline stopped. `--resume` reads this and nothing else. Advance it only after the stage's writes are durable. |
| `mode` | `fresh` (no Perry state) or `merge` (re-adoption — duplicates are surfaced to the user, never auto-dropped). |
| `sources[]` | What was detected and whether it was actually read. The scan writes these with `read: false`; harvest flips them. |
| `sources[].tier` | A / B / C. **Caps the confidence** of anything derived from it — see `reference/adoption-sources.md § Trust tiers`. |
| `clusters[]` | Triage units. Seeded from commit scopes / module boundaries / issue labels. Capped at 8. |
| `clusters[].kr` | The result of the cluster→KR attribution pass. Absent = not yet attributed; every task in the cluster inherits this edge. |
| `candidates[]` | Proposals, never state. Nothing here has touched the project. |
| `candidates[].evidence[]` | Citations in the declared forms (`path#Lx-y`, `git:sha`, `gh#id`, `fs:path@mtime`). A candidate with no citation is dropped, not softened. |
| `candidates[].status` | `pending` → `accepted` / `edited` / `rejected` / `deferred`. **Rejections are kept** so `--recheck` does not re-propose them forever. |
| `candidates[].target` | Which state file it would land in — and therefore which skill writes it. |

## Rules (do not violate)

- **This file is the only thing adoption writes** until stage 4. A user who
  abandons adoption halfway has an untouched project.
- **A candidate is not state.** Nothing here appears on a dashboard, in a
  roll-up, or in a count of open work.
- **Confidence describes Perry's reading of the evidence**, not whether the
  candidate is a good idea. A `high`-confidence candidate can still be rejected.
- **Never delete a rejected candidate.** It is the "don't ask me again" record,
  and it is a large part of why the dossier outlives the adoption run.
- **Objectives and KRs here are a strawman.** They exist to start the `okr init`
  interview, never to be written as-is. See `reference/adoption.md § The
  asymmetry`.

Validate after every write: `"$PERRY_HOME/bin/perry-lint" --root .`
