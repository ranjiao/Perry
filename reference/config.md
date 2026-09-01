# `.perry/config.md` — repo layout, state root, tracks

Tier 1. Loaded on demand from `SKILL.md § Configuration`, which carries the
field list and points here for what each field means.

Extracted from `SKILL.md` on 2026-08-18 (TASK-064) to keep the tier-0
router inside its byte budget. The prose is carried over unchanged.

## Repo layout options

Perry supports two layouts. Pick one at first-time setup; record the choice in `.perry/config.md`.

### Option A — single repo (default for non-code projects)

Everything (OKR, TASKS, evidence, design, handoff, weekly) lives in one repo at the project root. Use this when:
- The project does not produce code (research notes, ops runbooks, business planning, personal projects without a codebase).
- The project ships code but the volume of code commits is low and PMO commits will not pollute the history.

This is the simplest layout. No cross-repo references; everything is one `git log` away.

### Option B — two-repo split (PMO docs ↔ code)

PMO docs live in `<project>-pmo/` (this repo, where Perry's state files sit); code lives in `<project>/`. Use this when:
- The project ships code AND has been observed to suffer from branch contention between PMO doc commits and code commits, OR PMO commits visibly pollute code commit history.
- The user explicitly prefers the separation.

Cross-reference convention:
- PMO docs reference code via `<commit-SHA> path/to/file.py` (commit SHA pinned, not branch — survives rebases).
- Code commits reference PMO task IDs in commit messages (e.g., `Closes TASK-007`).
- Each repo has its own `.git/`; neither repo is a submodule of the other.

Trigger to migrate from A → B: ≥ 2 incidents of branch contention or commit-history pollution within a month. Capture the trigger as an ADR under `decisions/` (`Type: Process`) before splitting.

When B is in effect, `.perry/config.md` records both paths so every child skill knows where to look. Delegation prompts to Coding Agents must explicitly state which repo their work targets.

### `.perry/config.md` shape

```
# Perry configuration

- Document language: <English | 中文 | ...>
- Chat language: <follow user | English | 中文 | ...>
- Repo layout: <single | split>
- State root: <. | relative path>
- Packs: <comma-separated pack names, or absent for software-ops>
- Conformance gate: <advisory | enforce>   (optional; default enforce)
- Review rounds before escalation: <N>    (optional; default 2)
- Session context ceiling: <200k | N>     (optional; default 200k)
- PMO repo path: <absolute path>
- Code repo path: <absolute path or — if single>
- Last updated: <YYYY-MM-DD>

## Tracks            (optional; absent = one implicit `main` track, mode `project`)

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| main | project | phase/ | — | — | — | — | V3 |
```

### Prose in this file is layout, and `.perry/hook.md` is where it belongs

**`.perry/config.md` is a projection of `.perry/config.jsonl`** (ADR-007,
TASK-092). The store holds the preamble's `- Key: value` settings and every row
of `## Tracks`; every other byte of the file is layout. `perry-config render`
reproduces layout byte for byte **while a copy of the file is on disk to read it
from**, and `perry-config render --write` rebuilds the whole file from the store
alone when there is not — the shape above, the stored settings, the stored
table, and nothing else.

So the contract has two halves and only one of them is a promise:

- **Settings and track rows are recoverable.** Delete the file and
  `perry-config render --write` brings it back; every reader answers from the
  store meanwhile, so nothing depends on the file existing (TASK-233).
- **Prose is not.** It survives a render only while a file is there to copy it
  out of, and that guarantee ends the first time the file is deleted, or a
  project is cloned without it, or a fresh checkout renders before the file is
  restored. It is not stored, on purpose:
  [DESIGN-013](perry/design/DESIGN-013-one-place-per-fact.md) § 5.1 puts a
  schema'd fact in exactly one store, and § 5.5 rejects moving prose into one by
  name — a store is already a bad home for a paragraph.

**Write the explanation in `.perry/hook.md` instead.** It is tier 1, it is
yours, it is read at every standup by `/perry` and by every lane, and nothing
renders it — so a render cannot destroy it and a deletion cannot lose it. Perry
carries its own two configuration notes there, moved out of `.perry/config.md`
on 2026-08-30 under `## Configuration notes`: what its `intake` track carries
versus `main`, and why its state root is not `.`.

A note left in `.perry/config.md` is not an error and nothing will delete it.
`perry-config verify` reports it as a line the store does not hold, which is
true and is the point: it is a line one command away from being gone.

`## Tracks` is what turns on `pipeline` / `queue` / `inquiry` mode. A project
that never writes it behaves exactly as Perry did before DESIGN-003 — that is
the point — but a user who never hears the section exists cannot reach three of
the four modes at all, so **first-time setup offers it** (below) and `adopt`
proposes one before it proposes goals.

Children read this file before any output. If the file is missing, prompt the user to run first-time setup.

The field **names** above stay English in every language — this is the file that declares the language, so it has to be readable before the language is known. `Chat language` is optional; absent means `follow user`. See `reference/i18n.md`.

### `State root` — where Perry's files live

**`perry` is the default that setup writes**, as of 2026-08-17. It puts Perry's whole tree under `perry/`, leaving the project's own `design/`, `evidence/` and `knowledge/` untouched — removing the namespace-collision class rather than detecting it case by case.

**The code fallback is still the project root, and must stay that way.** A project whose config has no `State root` line keeps its files exactly where they are. Changing the fallback would send every reader into a subdirectory that does not exist and make an adopted project's entire history vanish from every tool at once. **The default governs what setup writes; it never governs where an existing project is looked for.** Earlier projects wrote `.` and are not migrated — `perry relocate` is there for anyone who wants to move, and "no automatic rewrite of a project's existing structure" is an Anti-Goal.

Two shapes in circulation is two code paths a reader can disagree about, and one already did: `bin/perry-goals` passed the project root where the state root was wanted, and the bug was invisible on every `.`-rooted project — including the test fixture. That is why the default moved, and why `tests/test_claims.py` now asserts every tool resolves through `resolve_state_root` rather than reaching for the project root itself.

**Do not enumerate the claimed paths here.** `schema/state-schema.json § claims[]` is the one authoritative list, and `perry-lint --claims --root .` computes the collision against it. This paragraph used to name five paths while the skills wrote eighteen, so a project owning `evidence/` or `knowledge/` collided silently — a second, hand-maintained copy is what drifted. Run the check; don't recite a list.

`.perry/` itself **never moves**: it is the anchor that marks the folder as a Perry project and it holds this pointer, so it cannot sit behind the pointer. Every reader resolves the root the same way — `viewer/parsers.py § resolve_state_root` is the one implementation, and `schema/state-schema.json` declares which files are anchored at the project root (`anchor: project`) rather than the state root.

Adoption asks this question during `confirm`, before anything is materialized (`reference/adoption.md`).

### The two cost budgets — `Review rounds before escalation`, `Session context ceiling`

Both are **measured defaults, not laws**, and both follow the precedence
`Conformance gate` established: the environment beats this file, which beats
the shipped value in `schema/state-schema.json § thresholds`. Every consumer
reports which of the three answered, so a budget that stops work can be argued
with by editing the register that actually set it.

| | default | env | read by |
|---|---|---|---|
| `Review rounds before escalation` | 2 | `PERRY_REVIEW_ROUNDS` | `perry-lint --reviews` |
| `Session context ceiling` | 200000 | `PERRY_CONTEXT_CEILING` | `perry-context-budget`, and `autopilot` through it |

**Where the two numbers come from.** On this repository, 20 rows entered V4 and
**74 rounds** were burned; ten rows needed three or more and two reached round
11. Separately, 25 sessions over 18,941 turns spent **8.43 billion tokens, 99.1%
of it `cache_read`** — the accumulated context, re-read every turn — so the
bill is `Σ over turns (context at that turn)` and a long run is superlinear.
Replaying those turns against a cap, 200k costs 58.3% less for the same work.

Raise `Review rounds before escalation` for a project whose reviews genuinely
converge by accretion; `1` makes every FAIL a decision point. Raise
`Session context ceiling` for a project doing genuinely wide reads, knowing the
cost of doing so does not grow linearly.

### `Conformance gate` — deleted

This setting is gone (`TASK-261`). Under ADR-004 every writer gated on a
**declared** marker — *this file matches Perry's shape, at shape version N, and
the user said so* — and refused a file nobody had declared.

It never caught anything. `.perry/conformance.jsonl` held 23 records at the
end, all `route: declare`, all files in Perry's own repository: zero
disagreements, because the disagreement the design exists to surface needs a
foreign project that drifts and Perry has never been pointed at one. The gate,
its ledger, `bin/perry-conform` and `bin/perry-migrate` are all deleted.

**What this changes for you**: nothing refuses a write for want of a
declaration. A writer that can render a file writes it. `perry-lint` still says
whether a file matches the schema — that half was never the gate.

A `- Conformance gate:` line left in an existing `.perry/config.md` is inert.
Nothing reads it and nothing reports it.
