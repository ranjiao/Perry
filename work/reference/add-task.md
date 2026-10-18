# Add a task

## `add-task`

Read `kernel.md` and `reference/input-quality.md §4 — Task rubric`. Resolve the user's
request into a bounded deliverable, out-of-scope list and falsifiable acceptance
criteria. Propose a new specification in chat before writing it; honor prior
session approval rather than asking twice. P0/P1 tasks require written criteria.

Choose priority, owner, track and verification. Incoming defects/requests use
`intake`; phase-decomposed tasks use `main`. Apply the hook's high-stakes boundary
and the corresponding V5 floor. Identify dependencies by actual item IDs; inspect
the referenced items and stable goals linkage. Unknown linkage remains unknown,
excluded from KR progress, and is handed to goals for resolution.

Use `item create` with title, summary, priority, owner, track, verification and
next_action; use `blocks` relations for known task dependencies and attachments
for existing specifications/designs. The returned ID is authoritative. Write an
approved new spec under that ID, including `## Files in scope`, `## Deliverable`,
`## Acceptance criteria`, `## Bound` and `## Out of scope`; then attach it with
`attach add`. Do not hand-edit a store, mint an ID or append a journal row.

Read the created item, confirm its fields/relations/attachments, then state its
next action. There is no register-specific intake, route or cadence command.
<!-- next-close: work add-task -->

Executor: claude-subagent | opencode-subagent | codex | manual. This is host
execution metadata, not a kernel task field; follow `dispatch.md`.

3. **For P0 and P1 tasks**, ALSO write `evidence/<YYYY-MM>/<TASK-ID>-spec.md` carrying written criteria and the dispatch-routing fields below — **in `## ` sections, not in the journal block's bullets.** Attach this spec to the task. P2 may keep criteria in its item fields — promote a P2 to P1 → write the spec at promotion time.

   **`Files in scope`, `Deliverable` and `Out of scope` are `## ` headings, with the text underneath them.** Not `### `, not `- **Deliverable**: …`. The spec body is `## ` sections throughout; these three are the ones a machine reads:

   ```
   ## Files in scope
   - `path/one.py` — what changes there.

   ## Deliverable
   What exists when this is done.

   ## Out of scope
   What this deliberately does not touch.
   ```

   **The shape is load-bearing, not a style rule.** `dispatch` pre-flight step 4 screens the spec against `.perry/hook.md § High-stakes operations` by reading exactly those three sections (`work/reference/dispatch-preflight.md` step 4), and its reader — `viewer/parsers.py § _section` — matches `^## <heading>` and nothing else. A scope written as an `h3` or as a bullet is invisible to it. **The spec does not then fail the gate; it disarms it.** Every high-stakes fragment is matched against the empty string, and the scan returns `touches: {}`, `verdict: pass`, **exit 0 — byte-identical to a spec that was read in full and found genuinely clean.** `perry-lint --specs` (and the default `perry-lint --root .`) reports such a spec; the report does not undo it, and the spec is only safe in the shape above.

   **The spec takes `## ` headings.** Do not copy a historical journal block into a spec; write the sections. The measurements behind both paragraphs: `add-task-notes.md § Why the spec shape is load-bearing`.

   **Required header fields in every spec file** (used by `dispatch` and `close-task`):
   The software-ops `Touches architecture`, `Deployed`, `Runbook` and
   Observability requirements below follow the pack eligibility rule in
   `$PERRY_HOME/reference/config.md § Pack capabilities and controls`. With
   inactive software-ops, impose them only where the project independently
   requires them; do not delete existing task commitments or relax high-stakes
   verification. Other dispatch fields remain required.
   ```
   > Dispatch mode: auto | manual               # default 'manual'; 'auto' is explicit opt-in
   > Executor: claude-subagent | opencode-subagent | codex | manual # only consulted when Dispatch mode = auto
   > Estimated cycle: small | medium | large    # informs sync vs async + cycle-time tracking
   > Subjective verification: <list, or '(none)'>
   > Touches architecture: <comma-separated §-section refs (§2, §3, §6.NN-3), or '(none)'>   # used by dispatch pre-flight + review agent; see $PERRY_HOME/packs/software-ops/architecture.md
   > Deployed: yes | no                          # default 'no'; 'yes' triggers runbook + observability gate at close
   > Runbook: runbook/<slug>.md                  # required ONLY when Deployed: yes; path must exist before close-task
   ```

   **When `Deployed: yes`, the spec ALSO requires an `## Observability` section** with three sub-fields (see `$PERRY_HOME/packs/software-ops/runbooks.md § Spec contract`):
   ```
   ## Observability
   - Success signal:   <log line / metric / endpoint / `command` output that proves it's working>
   - Failure diagnosis: `<single command>` — one line that answers "what's broken right now"
   - Runbook path:     runbook/<slug>.md
   ```

   **Choosing executor (spec writer responsibility)**:
   - `claude-subagent`: small task, needs MCP tools the parent session has, needs codebase familiarity.
   - `opencode-subagent`: OpenCode-native codebase work through synchronous `Task(subagent_type: general)`.
   - `codex`: medium/large self-contained, no MCP dependency, save Claude Code quota.
   - `manual`: high-stakes per project hook (production deploys, prod credentials, .env, paid APIs, cost ceiling raise) OR subjective decision-making (research candidate selection, design choices).

   Commit to the choice with one inline reason: `> Executor: codex (high confidence — pure analytics task, no MCP needed)`.
