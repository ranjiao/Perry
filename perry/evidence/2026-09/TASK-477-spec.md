# TASK-477 — perry-diagnose honours the schema's code anchor

Date: 2026-09-21. Owner: Coding Agent. Priority: P1. Required verification: V4.
> Touches architecture: bin/perry-diagnose ownership scan (reads the schema's anchor).
> Dispatch mode: auto
> Executor: claude-subagent
> Subjective verification: independent review against the written bounded criteria
> Deployed: no

Authorization: USER-988 (2026-09-21, in chat), scope as proposed. Found by
TASK-452's round-2 V4 review (`perry/evidence/2026-09/TASK-452-review/round2-v4.md`).

## Deliverable

`bin/perry-diagnose` decides which Markdown files Perry owns by prefixing every
path `perry_owned_globs()` reads from `schema/state-schema.json § files[]` with
the state-root prefix (`bin/perry-diagnose:2641-2645`). Since TASK-451,
`files[id=architecture]` (and `architecture-module`) carry `"anchor": "code"`.
Make the ownership scan prefix each declared path by its own anchor: a
code-anchored path relative to `lib.anchor_root(<perry root>, <state root>,
"code")` (A1's shared resolver; reuse it, no second resolver), a state-anchored
or unanchored path at the state root as today, `.perry` paths unchanged. The
schema-unreadable fallback list keeps working.

## Acceptance criteria

1. Fixture with state root `perry/`, code root unset, a root `ARCHITECTURE.md`
   and a stale `perry/ARCHITECTURE.md`: the root document is in `perry_owned`
   and not reported as an orphan; `perry/ARCHITECTURE.md` is not in
   `perry_owned`.
2. Fixture with a configured split code root (`code_repo_path`): the code-root
   document is Perry-owned; the project-root and state-root copies are not.
3. State-anchored files (e.g. `OKR.md`, `phase/*`) are still matched at the
   state root in both fixtures.
4. Reverting the anchor-aware prefix makes the new test fail; the unmodified
   candidate and the affected tier pass.

## Files in scope

`bin/perry-diagnose` (`perry_owned_globs` and its caller only); one new or
extended test in `tests/test_diagnose.py`.

## Bound

Three layouts: single root with stale state-root decoy, split code root, state
files unchanged. One anchor value besides the default (`code`). Net Python/test
physical lines ≤ +15 against the base. No change to other scans' logic beyond
what receives `perry_owned`.

## Verification

Isolated fixtures, candidate PERRY_HOME, PERRY_PROJECT unset, fresh TMPDIR under
the scratch derivation. `bash tests/run --tier affected --base <pinned base>`;
one reverting-fix proof with `__pycache__` purged; `git diff --check`. Record
the exact commit and line delta.

## Out of scope

`schema/state-schema.json`, other readers of the anchor, `viewer/`,
`<component>/ARCHITECTURE.md` module-document globbing beyond what the fix
naturally covers, live PMO state, foreign writes, release, publication and main
integration. A separate reviewer awards V4; the integrator owns merged full/slow
acceptance.
