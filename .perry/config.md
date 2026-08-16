# Perry configuration

- Document language: English
- Repo layout: single
- State root: perry
- PMO repo path: /Users/bytedance/proj/Perry
- Code repo path: —
- Last updated: 2026-08-16

## Why the state root is not `.`

Perry's own `design/` directory is the **design lane skill**
(`design/SKILL.md`, `design/state/design_TEMPLATE.md`), not a folder of design
documents. Pointing the state root at the project root would make Perry claim
its own source tree, and every lint run would report `design/SKILL.md` as a
malformed design doc.

`okr/` and `pmo/` are lane skills for the same reason. `.perry/` stays at the
project root: it holds this pointer, so it cannot sit behind it.

This is the collision described in `perry/design/DESIGN-002-namespace-collision.md`
— Perry is its own proof case, and this file is the escape hatch that document
argues should be offered automatically rather than written by hand.

See `schema/README.md § Where the files are`.
