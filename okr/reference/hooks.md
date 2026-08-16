# OKR per-project hooks

Loaded when configuring `.perry/hook.md` for a project, or when `init` /
`plan-phase` needs to know whether the project declares OKR-specific defaults.

Generic by default; hooks are pure additions, not overrides. Most solo projects
never need one — the generic interview in `init` works fine.

## Block format

```
If the project is **<name>**:
- Default overall period: <e.g., 3 months>.
- Canonical Objective tracks: <list, with one-line descriptions>.
- Roadmap source-of-truth: <file>.
- Operating Principles to seed: <list>.
- Anti-Goals to seed: <list>.
- Cost ceiling defaults: <amount + soft threshold + wiring>.
- For KR metrics, prefer MCP tools: <list>.
- KR examples: <2–3 examples>.
```

## Skeleton example

```
If the project is **<your project name>**:
- Default overall period: <e.g., 3 months / 6 months / 1 year>.
- Canonical Objective tracks: <2–3 named tracks with one-line descriptions
  that fit your domain; e.g., "Learn / Build / Validate" or any other set>.
- Roadmap source-of-truth: <file that anchors phase/week mapping, if any>.
- Operating Principles to seed (drop these into `OKR.md` Operating Principles
  on `okr init`):
  - <invariant the system must hold>
  - <invariant the system must hold>
- Anti-Goals to seed:
  - <thing the project will NOT do>
  - <thing the project will NOT do>
- Cost ceiling defaults: <amount / period> · soft fallback at <%> · hard cap
  at <%> · check via <command or dashboard> · wiring status: <wired | doc-only>.
- For KR metrics, prefer MCP tools: <list>.
- KR examples that fit this domain:
  - <metric + target + deadline>
  - <metric + target + deadline>
```

## The one hook section that is not optional

`.perry/hook.md § High-stakes operations` is a **safety gate**, not
configuration — `/pmo dispatch` refuses specs that match it and `/pmo autopilot`
refuses to run without it. PMO bootstrap writes a conservative default list. See
`pmo/reference/extending.md`. OKR only reads the hook; it never writes it.
