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
2. Save the draft from the first answer on, and show it for review, through
   `$PERRY_HOME/goals/reference/planning.md` (`perry-goals draft`): each asked
   question and answer is persisted, so a closed session resumes at the
   pending question. Keep source/assumption distinctions, boundaries and
   remaining unknowns in the body.
3. Follow the bank's **Premises, edits and approval**: surface meaningful
   premises, incorporate disagreement into affected draft sections, then run
   `$PERRY_HOME/reference/input-quality.md § 1 Overall OKR` once on the resulting
   draft. Surface ≤3 advisory issues, preserving the solo-project qualification.
   A refusal uses the bank's escape; a fully pasted OKR skips the interview.
4. Stop at the reviewed or approved draft: say "draft approved; overall
   finalize is unavailable". `draft finalize` refuses and names the one
   writer still missing — the overall-OKR author. A *phase* draft does
   finalize, through `perry-goals phase new`. Do not hand-append canonical goal stores, hand-author `OKR.md` for
   an importer, or auto-run `plan-phase`.

### Structural contract

`OKR.md` carries each version's `## v<N>: <date>` block and its
`### Objective <N> — <title>` headings — **no KR table** (TASK-236, `ADR-019`).
The overall key results are records in `okr.jsonl`, each added once its version
and objective exist with the `kr add` verb of `bin/perry-goals`
(`--okr-version "<version>" --objective <O-id> --text "…"`, see
`phases.md § kr`), and printed by `perry-goals krs --level overall`.
A KR typed into `OKR.md` as a table row or a bullet is not how one is added:
every overall `kr` write refuses a file that still carries KR rows.
This is the target document shape, not permission to bypass a missing writer.
The shape is declared in `$PERRY_HOME/schema/state-schema.json` and checked by
`bin/perry-lint`. After writing, run:

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
   receipt. Use the bank's **Premises, edits and approval** on the resulting
   version, including its one-pass rubric and refusal escape. A premise
   disagreement changes that section and dependent proposals, not all wording.
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
