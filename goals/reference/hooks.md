# OKR per-project hooks

The root procedure owns agreed hook edits; goals proposes its preferences and
reads the actual hook. Do not edit shipped skill pages or write the root hook
from this lane. Load this page when `init` /
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
- Operating Principles to retain in the approved goal narrative attachment:
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

## Safety source

The root-owned `.perry/safety.json` supplies the reviewed policy, with role
additions forming an additive union. Hook prose is context, not the machine
list. Goals preserves existing restrictions and follows the root procedure for
changes; native goal approval never authorizes a high-stakes external action.
Read `$PERRY_HOME/reference/safety-policy.md` and `config.md`.
