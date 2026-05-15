# `/pmo dispatch <task-id>` — fully automated end-to-end

Same goal as `delegate` (see `delegate.md`) but **fully automated**. PMO renders the prompt, fires it at an executor, watches for completion, parses the result, runs any objective verification commands declared in the spec, writes an evidence file, updates BOARD + journal, and reports back. Subjective verification stays with the user (status moves to `review`, not `done`).

## Pre-flight (any failure → refuse and fall back to `delegate`)

1. `evidence/<YYYY-MM>/<TASK-ID>-spec.md` exists.
2. Spec contains `Dispatch mode: auto` (default `manual` — explicit opt-in required).
3. Spec contains `Executor: claude-subagent | codex` (not `manual`). **If spec is `Dispatch mode: auto` but `Executor` is missing**, use `AskUserQuestion` (header `"Executor"`, options = `claude-subagent | codex (if installed) | manual — fall back to delegate`) for a one-shot choice this run; do NOT silently default. Persist the answer back into the spec only if the user explicitly says "save this for next time". On Codex (`$HOST = codex-cli`) **omit** the `claude-subagent` option (the executor isn't available) — see `../../reference/host-capabilities.md`. If a spec already pins `Executor: claude-subagent` on Codex, refuse the dispatch and tell the user to switch to `codex` or fall back to `/pmo delegate`.
4. **Safety re-validation**: scan spec's `Files in scope`, `Deliverable`, `Out of scope` against the project hook's high-stakes operations list (in `.perry/hook.md`). Any positive match in `Files in scope` or `Deliverable` (i.e. the task touches it) → refuse. Any positive match in `Out of scope` (task explicitly avoids it) → that's a green light for the line in question.
5. Spec contains a `Subjective verification:` section (may be `(none)`); items there will be surfaced to the user at completion, never auto-validated.
5a. **Architecture compliance pre-flight** (see `../../reference/architecture.md § Dispatch integration`):
    - Read `ARCHITECTURE.md` at project root (full text). If `Status: draft` → log a warning but don't refuse (draft window allows iteration). If file missing AND spec's `Touches architecture:` is non-empty → refuse (spec claims sections that don't exist).
    - Read spec's `Touches architecture:` field. For every section ref listed (`§N`, `§N.NN-M`), verify it exists in the doc. Refuse on mismatch (malformed spec).
    - For each touched non-negotiable in §6 marked `Severity: hard` → use `AskUserQuestion` (header = `NN-N`, options): `Proceed — change is reviewed (Recommended only with reason) | Refuse — revise spec | Refuse — escalate to manual delegate`. "Proceed" requires a written one-line justification copied into the dispatch evidence file's header.
    - For soft non-negotiables → single `AskUserQuestion` (header = `Architecture`, multiSelect) listing each soft NN as an option with description = the rule text. Selection = acknowledgement.
    - `Touches architecture: (none)` → no friction at this stage, but the review agent still runs after completion (§ Architecture review below).
5b. **Deployed-task pre-check**: if spec has `Deployed: yes`, verify the spec contains a non-empty `## Observability` section (Success signal / Failure diagnosis / Runbook path). If missing → refuse and ask user to fix the spec first. The runbook file itself is not required to exist yet at dispatch time (often the dispatched task creates it) — only the observability spec field is mandatory.
6. **Concurrency check**: `bash "$PERRY_HOME/bin/perry-dispatch-limit" register <task-id> <executor>`. Exit 0 = slot reserved, proceed. Exit 1 = limit hit; stderr lists what's currently in flight. On limit-hit, ask the user via `AskUserQuestion` (header `"Dispatch full"`, options): `Wait — show in-flight (Recommended) | Switch to other executor (if it has slots) | Fall back to /pmo delegate (manual paste)`. Default limits: 2 codex, 2 claude-subagent, 3 total — overridable via env (`PERRY_MAX_DISPATCH_CODEX`, `PERRY_MAX_DISPATCH_SUBAGENT`, `PERRY_MAX_DISPATCH_TOTAL`). On Codex the cap is advisory across separate sessions — see `../../reference/host-capabilities.md § perry-dispatch-limit`.

## Dispatch — per executor

### `Executor: claude-subagent` (Claude Code only)

- **Host gate**: requires `$HOST = claude-code`. On Codex this executor is unavailable — refuse and route per `../../reference/host-capabilities.md § Agent / subagent_type`.
- Use the `Agent` tool with `subagent_type: general-purpose`.
- Build prompt = **`ARCHITECTURE.md` full text + architecture preamble (see § Architecture preamble below)** + spec full text + project hook safety constraints + Git expectation block (see `git-boundaries.md`) + RESULT format including the mandatory `ARCHITECTURE COMPLIANCE` block (see § Architecture compliance RESULT).
- Async-ness from spec's size hint: `Estimated cycle: small` → `run_in_background: false`; `medium | large` → `run_in_background: true`.
- Sub-agent shares parent cwd. For split-repo projects: instruct sub-agent to use `git -C <code-repo-path> ...` for every git command (do NOT `cd`; preserves parent cwd state).

### `Executor: codex`

- **MANDATORY pre-flight** before the first codex dispatch in any session (or after the 6h smoke cache expires):
  ```
  bash "$PERRY_HOME/bin/perry-codex-preflight"
  ```
  The script: (a) `codex --version` ≥ `PERRY_CODEX_MIN_VERSION` (default `0.100.0`); (b) smoke test (`codex exec "Reply with just: PERRY_OK"`, 60s timeout if `timeout` / `gtimeout` is installed). Cached 6h at `~/.cache/perry/codex-smoke-pass`. Exit non-0 → **refuse + surface stderr verbatim + fall back to delegate**. Catches stuck CLI / broken auth / version-rejected-by-API BEFORE we fire async dispatch that would silently hang.
- Then: Bash → `cd <code-repo-path> && codex exec "<prompt>"`.
- Always async (codex is its own session). On Claude Code, pass `run_in_background: true`. On Codex (`$HOST = codex-cli`), wrap in shell backgrounding (`codex exec "..." > /tmp/perry-dispatch-<id>.log 2>&1 &`); see `../../reference/host-capabilities.md § Bash run_in_background → shell &`.
- Prompt MUST be self-contained (codex doesn't see the journal, BOARD, or any prior context). Include: **`ARCHITECTURE.md` full text + architecture preamble** + spec full text + relevant project hook excerpts + git expectation + RESULT format including mandatory `ARCHITECTURE COMPLIANCE` block + the explicit list of files codex can read for context.
- Capture stdout to a temp file; on completion, parse for the RESULT block.
- If the long-running codex call fails (non-0 exit / no RESULT block / timeout), per the failure handling below, mark task `review` and surface raw output. Pre-flight is the cheap pre-check; this is the post-check.

## Architecture preamble (prepended to every dispatched agent's prompt)

```
You are working in a project with a frozen architecture. The document below
is the single source of truth for system design — read it before changing
any code. Your task spec follows after the document.

Your RESULT block MUST include an `ARCHITECTURE COMPLIANCE` section listing:
- Which §-sections of the architecture document your change touches.
- For each touched section, one sentence explaining why your change is
  consistent with what the section says.
- Any new entries you believe should be added to §7 (Open questions) — i.e.,
  decisions the user needs to make that arose from your work.

A separate review agent will independently verify your attestation by reading
the same architecture document, your diff, and your compliance block. It can
fail your task. Do not paper over inconsistencies — if your change deviates
from the document, surface it explicitly and let the user resolve.

=== BEGIN ARCHITECTURE.md ===
<full file contents>
=== END ARCHITECTURE.md ===
```

## Architecture compliance RESULT block (required from primary executor)

In addition to the standard `=== RESULT ===` block, every dispatched agent appends:

```
=== ARCHITECTURE COMPLIANCE ===
Touched sections: §2 (component X added), §3 (new dep X → Y), §6.NN-3
Compliance check:
- §2: <one-sentence justification per section>
- §3: <one-sentence justification per section>
- §6.NN-3: <one-sentence justification per section>
New §7 questions opened: (none) | - <question> — recommended USER-id
=== END COMPLIANCE ===
```

If this block is missing or empty, dispatch treats it as **executor failure** — task goes to `review` with `compliance-missing` annotation. No auto-retry.

## Architecture review (the independent gate)

After the primary executor's RESULT is parsed AND objective verification (§ "On completion" step 2) passes, BUT before flipping the BOARD row to `review`, dispatch fires a second agent — the **architecture review agent**.

1. **Executor selection**:
   - On Claude Code (`$HOST = claude-code`): `Agent(subagent_type: general-purpose, run_in_background: false)` — small task, sync.
   - On Codex (`$HOST = codex-cli`): `codex exec` (sync, ~60s).
   - Per-project hook may pin `Review agent executor:` to override (`codex | claude-subagent | (auto)`).

2. **Prompt**: full `ARCHITECTURE.md` + the diff (`git diff <base>..<head>` from the primary's PR, captured with `gh pr diff <pr>` or `git diff` for direct-push) + the primary's `ARCHITECTURE COMPLIANCE` block + the literal instruction:

   ```
   Your job is to adversarially review the diff against the architecture
   document. Do not trust the primary agent's attestation.

   Independently identify any place in the diff that:
   1. Crosses a boundary forbidden by §3.
   2. Adds state ownership not declared in §2.
   3. Implements a contract incompatible with §5.
   4. Violates any §6 non-negotiable.
   5. Should have updated §7 (created new open questions the user hasn't seen).

   Output exactly one of:
   - `PASS` followed by 1–3 sentences summarizing what you verified.
   - `FAIL: <section ref>` followed by the specific issue, the diff lines that
     prove it, and what the agent would need to do to make it pass.

   Use only the architecture document as your authority. If the document is
   silent on something, that's not a violation — it's a §7 candidate.
   ```

3. **Capture output**. Append to the dispatch evidence file under `## Architecture review` section verbatim, with header (executor, timestamp).

4. **Status decision**:
   - `PASS` → continue to flip BOARD row to `review` (normal flow).
   - `FAIL: <ref>` → flip to `review` with annotation `architecture-failed: <ref>`; surface the FAIL message to the user; `close-task` will refuse until this is resolved (re-dispatch or explicit override).

5. **Skip conditions** (review agent does NOT run):
   - Spec's `Touches architecture: (none)` AND primary's `ARCHITECTURE COMPLIANCE` Touched sections is empty → skip (no architecture-relevant change). Note: if primary self-attests touching sections despite `(none)` in spec, run the review — primary is admitting scope drift.
   - `ARCHITECTURE.md` is `Status: draft` → run the review but mark its output `advisory`; FAIL does not block close.
   - Primary executor itself failed (objective verification failed, RESULT block malformed) → skip (no point reviewing a broken result).

6. **Cost note**: this is one extra small subagent / codex call per dispatch. Project hooks declaring tight quota may set `Skip review agent for: P2, soft-§-only` exemptions; the default is to always run.

## Common (post-dispatch, before completion)

- Append `## Status changes` line to today's journal: `[TASK-X] not_started → in_progress · dispatched HH:MM · executor=<name> · async=<bool>`.
- Update BOARD row: status → `in_progress`; Next action → "dispatched <time>; awaiting completion".
- Reply to user: `Dispatched <TASK-X> via <executor>. Will report when done.` Do NOT block waiting for sync; rely on runtime notification.

## On completion (notification arrives)

0. **Release the concurrency slot first thing**: `bash "$PERRY_HOME/bin/perry-dispatch-limit" release <task-id>`. Do this BEFORE any verification work, so a slow verification step doesn't keep blocking other dispatches. (Stale markers auto-clean after `PERRY_DISPATCH_STALE_TTL` seconds — default 1h — covering the case where PMO crashed mid-completion.)
1. Read the agent's RESULT block. Required fields:
   - `PR URL:` (or "n/a — direct push" with explicit reason)
   - `Files changed: <count>` + bullet list
   - `Tests: <pass>/<total>` + command used
   - `Cycle time: <minutes>` (for calibration)
   - `Notes:` (anything unusual)
2. Run **objective verification** from the spec's `Verification` section. Anything that looks like a runnable command (starts with `$`, names a CLI like `pytest` / `gh` / `gim`, or has a clearly executable shape) — run it. Capture output.
3. Cross-check against `Out of scope` — if the agent's `Files changed` list contains paths declared out-of-scope, raise a hard failure (likely scope creep or safety violation).
4. **Status decision**:
   - All objective verifications pass + no scope violation + RESULT block has all required fields → status `review` (NEVER auto-`done`; subjective verification is the user's, per the project's standing rule).
   - Anything fails → status `review` with failure annotation; no auto-retry, no auto-rollback.
5. Write `evidence/<YYYY-MM>/<TASK-ID>-dispatch-<YYYY-MM-DD-HHMM>.md`:
   - Header (date, executor, async, cycle time)
   - Full agent RESULT block verbatim
   - Objective verification commands + their outputs
   - Subjective verification items (copied from spec, marked `[user-verify]`)
   - PR URL + branch + commit SHA
6. Update BOARD row: status → `review`; Next action → "user verifies subjective items: <…>"; Evidence → path of dispatch file.
7. Append `## Status changes` to today's journal: `[TASK-X] in_progress → review · executor=<name> · cycle=<min> · evidence: <path>`.
8. Surface to user: pass/fail summary + 1-line subjective verification ask.

## Failure handling (mark `review`, no auto-retry)

- Executor crashed / non-zero exit / timeout → release the slot (`bash "$PERRY_HOME/bin/perry-dispatch-limit" release <task-id>`), write evidence with raw output, status `review`, surface failure summary, ask user retry / fix manually / drop.
- ff-only PR push failed → same, with manual-resolution hint.
- Agent declared `done` but tests failed → same.
- The release call MUST run on every failure path, not just success — otherwise a failed dispatch leaks a slot until stale-TTL expires.

## Cost / quota awareness

- Each `claude-subagent` call counts against the parent CC session quota (5-hour Sonnet caps, weekly Opus caps).
- Each `codex` call counts against OpenAI quota.
- PMO does not enforce a per-call dollar cap; spec writer chooses executor as a quota-routing hint.
- Hooks may declare project-specific quota limits (e.g., "no more than 5 dispatches per day") — PMO honors those if present.

## RESULT block format (required from any dispatched agent)

```
=== RESULT ===
PR URL: <url>           # or "n/a — direct push" with reason
Files changed: <count>
  - path/file1.py
  - path/file2.py
  ...
Tests: <pass>/<total> (command: <pytest ...>)
Cycle time: <minutes>
Notes: <anything unusual>
=== END RESULT ===
```
