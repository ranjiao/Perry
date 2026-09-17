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

Then use `$PERRY_HOME/goals/reference/elicitation.md` for **Route and reuse** and
the shared question bank. Read it before asking; do not turn the fields below
into another form. A selected commitments spine uses that route, not this
overall template. Unknown state never proves this is a first OKR.

1. Follow the bank's **Use the bank** response handling: propagate corrections
   through dependent proposals and choose the next consequential unresolved gap.
   Ask one question, then wait; Q1–Q4 guide coverage, not a fixed sequence.
   Default to one objective and at most three KRs, with eight questions total
   before a visible draft (including every clarification/push question).
   Keep unsupported facts explicitly unknown and unaccepted targets proposed.
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

## `revise` — draft a new OKR version

Used when goals materially change between versions (new constraints, new mission, big learnings). Soft fork:

1. Read the current accepted `OKR.md` version and the user's requested change.
   Follow `elicitation.md`'s revision route; reuse explicit answers with sources.
   Show what changed, why, and which Objectives/KRs it invalidates. Preserve
   unaffected accepted wording; do not replay the first-OKR interview.
2. Choose the next consequential affected gap from the shared bank. Ask one
   question and wait, at most five before a visible draft, counting routing,
   clarifications and pushes. Corrections invalidate dependent proposals under
   **Use the bank**; new thresholds never inherit old approval.
3. Show the proposed new version in chat, with before/after changes, reasons,
   source distinctions and unknowns. Its proposed version/date is not an append
   receipt. Use the bank's draft/quality procedure on the resulting version.
4. Keep edits separate from approval of the current draft. Finalize only through
   an available owning approval/persistence/writer flow; if missing or refusing,
   name the gap/message and stop. Do not append a version, render a fabricated
   canonical input file, or hand-write stores to work around missing tooling.
   Historical versions remain unchanged.
5. Surface any consequence for the current phase as a proposed follow-up, never
   an automatic phase close/start. After a supported approved revision, hand the
   decision to `decide` via `/perry decide adr <slug> --type Process`; the goals
   lane does not write the decision or PMO records.

**Tier 1 cap**: `OKR.md` ≤ 200 lines. Before any supported write, review overflow
handling under `goals/SKILL.md`: propose archiving historical version retros or
trimming; a draft does not itself authorize moving history or writing a version.

## Completion routing

After completed writes from `init`, `revise`, follow [the shared closing step](../../reference/next.md#closing-step); its skip rules apply.
<!-- next-close: goals init --> <!-- next-close: goals revise -->
First/revision chat drafts are unfinished planning: do not close or bypass an unavailable writer to trigger this step.
