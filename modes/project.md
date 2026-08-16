# Mode · `project` — a goal is met, and the work ends

> Loaded by the router for any track whose `Mode` is `project`, and for the
> implicit `main` track of every project that has declared no tracks at all.
> DESIGN-003 § 5.1.

**This file adds nothing to Perry's behavior. That is the point.**

`project` is the shape Perry was built for, and its rules already live in
`okr/SKILL.md` and `pmo/SKILL.md`. Copying them here would create a second
authoritative copy of a rule that already has one — the exact failure
`reference/project-archetypes.md § Part 1.2` calls *"one document, one owner,
one copy"* and that Perry refuses everywhere else. So this file **declares which
existing rules constitute the mode** and points at them. The other three modes
carry real rules, because their rules exist nowhere else yet.

The consequence to hold onto: a project that never declares a track gets this
file, this file changes nothing, and the behavior is bit-identical to Perry
before DESIGN-003. That is goal 7, and `tests/test_work_modes.py` plus the
dashboard byte-diff in TASK-018's evidence are what prove it rather than assert
it.

## The mode contract

| Slot | Value | Owned by |
|---|---|---|
| **Ends when** | The goal is met — commit KRs largely hit | `okr/reference/phases.md` |
| **Unit that gets an ID** | Task | `pmo/reference/subcommands.md § add-task` |
| **Spine** | `OKR.md` objectives → `phase/<NNN>-<slug>.md` | `okr/SKILL.md` |
| **Horizon** | The phase. Closes on KR progress, **not** on a date | `okr/SKILL.md § Why phases, not months` |
| **Calendar** | Advisory. The 80%-of-commit-KRs prompt and the 14-day snapshot heartbeat are nudges, never enforcement | `okr/SKILL.md` |
| **Item states** | `not_started → blocked → in_progress → review → done → dropped` | `pmo/SKILL.md § Status, Priority, Owner models` |
| **WIP control** | `P0` / `P1` / `P2`. Cadence work sits under `## Cadence` and does not consume P0 slots | `pmo/SKILL.md` |
| **Triage asks** | Is this still the right task? What is stale, inflated, or `done` with no evidence? | `pmo/reference/subcommands.md § triage` |
| **Default rung** | **V3** — reproducible run. This mode is the one with a native verification loop: tests, build, lint, run by the agent with output shown rather than asserted | `schema/state-schema.json § verification` |
| **Signature failure** | Spec-free "vibe" implementation; a tier-0 file grown past its cap; `done` rows with no evidence path | `reference/project-archetypes.md § 3.A` |

## Why V3 is the default here and nowhere else

Software is the only shape with a verification loop it did not have to
construct. A test suite, a build exit code and a linter all return a signal the
agent can read, so V3 is reachable at no extra cost and anything less is a
choice to skip a check that already exists.

The consequence rule still overrides it: a task in this mode that deploys,
publishes, spends money, or is otherwise outward-facing or irreversible needs
**V5** regardless (`schema/state-schema.json § verification`). The mode default
is a floor for ordinary work, never a ceiling on a risky one.

## What this mode does *not* assume

Recorded because these are the assumptions that leaked into every other shape
before DESIGN-003, and naming them here is what keeps them scoped:

- **That the calendar is theater.** It is, for product work. It is not for
  month-end close, a filing deadline, or a campaign launch — `pipeline` and
  `queue` mark the calendar binding for exactly that reason.
- **That work is planned rather than arriving.** Project-mode work comes from
  `plan-week`. Queue-mode work arrives from outside and needs an intake organ
  this mode has no use for.
- **That a goal exists to attribute a task to.** Project mode resolves every
  task to a KR (`reference/okr-linkage.md`). A queue of inbound requests has
  standing commitments instead, and forcing an objectives cascade onto it
  produces goals nobody set.

## See also

- `perry/design/DESIGN-003-work-modes.md § 5.1` — the four-mode table this row
  comes from, and the three rejected alternatives to the track object.
- `modes/pipeline.md`, `modes/queue.md`, `modes/inquiry.md` — the modes that
  carry rules rather than references.
