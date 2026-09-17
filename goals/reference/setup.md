# `okr init` / `okr revise` — creating and versioning the overall OKR

Loaded when `/okr init` or `/okr revise` fires. Not loaded on routine snapshots.

## `init` — first-time bootstrap of overall OKR

Run when `OKR.md` doesn't exist.

0. **Write the config store first, when `.perry/config.jsonl` does not exist.** A goals-only start is a start: `OKR.md` alone does not make a project installed (`$PERRY_HOME/schema/README.md § installed`), so without the store every session would offer first-time setup again. Ask the preference questions `$PERRY_HOME/SKILL.md § First-time setup` step 3 asks, then write the answers before any other file:

   ```
   "$PERRY_HOME/bin/perry-config" set --root . "Document language" "<language>"
   "$PERRY_HOME/bin/perry-config" set --root . "Chat language" "follow user"
   "$PERRY_HOME/bin/perry-config" set --root . "Repo layout" "<single or split>"
   "$PERRY_HOME/bin/perry-config" set --root . "State root" "<state root>"
   ```

   When the store already exists (first-time setup ran), this step writes nothing.

Then use `$PERRY_HOME/goals/reference/elicitation.md` for the **first-OKR question
bank**. Read it before asking; do not turn the fields below into another form.

1. Propose grounded answers from the user's context, then ask one question at a
   time. Default to one objective and at most three KRs; the normal short path is
   four to five questions, with eight total before a visible draft (including
   clarification/push questions). Keep unsupported facts explicitly unknown.
2. Show the compact first-OKR draft in chat, with source/assumption distinctions,
   boundaries and remaining unknowns. This delivery does not persist a planning
   draft or provide resume/finalize machinery; do not claim those operations ran.
3. Run `$PERRY_HOME/reference/input-quality.md § 1 Overall OKR` on that draft.
   Surface ≤3 issues with concrete rewrites, advisory + override. The rubric is
   unchanged, including its solo-project qualification for fewer objectives.
4. Stop at the visible draft and quality feedback. Do not hand-append canonical
   goal stores or invent a writer to finalize it, and do not auto-run `plan-phase`.
   The owning approval/persistence/writer flow must exist before finalization;
   this first-OKR bank does not claim to supply that separate implementation.

### Structural contract

The existing overall-OKR document contract remains: KRs are written as a **table** under each `### Objective <N> — <title>` heading, with ids matching `KR-O<n>.<m>`:

```
| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O1.1 | Cut median release time | median ≤ 12 min | no | 2026-09-01 |
```

This is the target document shape, not permission to bypass a missing writer.
This shape is declared in `$PERRY_HOME/schema/state-schema.json` and checked by `bin/perry-lint`. It is also what `bin/perry-state` reads — a KR written as a prose bullet instead will not be counted anywhere. After writing, run:

```
"$PERRY_HOME/bin/perry-lint" --root .
```

## `revise` — produce a new OKR version

Used when goals materially change between versions (new constraints, new mission, big learnings). Soft fork:

1. Show current `OKR.md` summary.
2. Walk through what's changing per Objective / KR.
3. Increment version number, set new date.
4. Append the new version under `## v<N>: YYYY-MM-DD`. Old versions stay readable for historical audit.
5. Re-check the current phase OKR — does it still serve the new overall? If not, suggest `/okr score-phase` (close current) + `/okr plan-phase` (start new aligned with revised goals).
6. Tell **`decide`** to record it: `/perry decide adr <slug> --type Process`. Not PMO — `decisions/` moved to the `decide` lane on 2026-08-16.

**Tier 1 cap**: `OKR.md` ≤ 200 lines. If appending a version would exceed it, move historical `## v<N>` retro blocks to `phase/snapshots/okr-vN.md` and keep the current version + version log in the main file. Verify before writing, not after.
