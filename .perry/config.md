# Perry configuration

- Document language: English
- Chat language: 中文
- Repo layout: single
- State root: perry
- PMO repo path: /Users/bytedance/proj/Perry
- Code repo path: —
- Last updated: 2026-08-16

## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| main | project | phase/ | — | — | — | — | V3 |
| intake | queue | standing | new→triaged→in_progress→resolved | 6 | 5d | weekly | V3 |

`intake` carries the work that ARRIVES — a defect an agent found mid-run, a
sibling a sweep turned up, a review finding. It is not decomposed from a goal,
it shows up, and its useful questions are queue questions: what has been
waiting longest, how deep is the backlog, what keeps recurring.

`main` carries the work that is DECOMPOSED — the phase, its KRs, the rows that
serve them.

Declared 2026-08-20 as the experiment in TASK-133. `Default rung` is V3 rather
than queue mode's V2 default: an arriving row here is a code defect, and a
resolution note is not evidence that it is fixed.

## Why the state root is not `.`

Perry's own `design/` directory is the **design lane skill**
(`decide/SKILL.md`, `decide/state/design_TEMPLATE.md`), not a folder of design
documents. Pointing the state root at the project root would make Perry claim
its own source tree, and every lint run would report `decide/SKILL.md` as a
malformed design doc.

`okr/` and `pmo/` are lane skills for the same reason. `.perry/` stays at the
project root: it holds this pointer, so it cannot sit behind it.

This is the collision described in `perry/design/DESIGN-002-namespace-collision.md`
— Perry is its own proof case, and this file is the escape hatch that document
argues should be offered automatically rather than written by hand.

See `schema/README.md § Where the files are`.
