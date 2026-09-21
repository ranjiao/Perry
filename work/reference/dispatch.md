# `/pmo dispatch <task-id>` — fully automated end-to-end

Same goal as `delegate` (see `delegate.md`) but **fully automated**. PMO renders the prompt, fires it at an executor, watches for completion, parses the result, runs any objective verification commands declared in the spec, writes an evidence file, updates BOARD + journal, and reports back. Subjective verification stays with the user (status moves to `review`, not `done`).

Executor contract: `claude-subagent | opencode-subagent | codex | manual`. `manual` routes to `delegate`; automated dispatch strictly follows the host matrix in `../../reference/host-capabilities.md`.

## 0 · Whether to dispatch at all

See `dispatch-preflight.md § 0 · Whether to dispatch at all`.

## Pre-flight (any failure → refuse and fall back to `delegate`)

First the before-dispatch budget checkpoint, `budget-boundary.md § Budget boundary`: `OVER` dispatches nothing. Then `dispatch-preflight.md § Pre-flight (any failure → refuse and fall back to delegate)`.

## Dispatch

> **Stage moves and status changes go through `bin/perry-task`.** This file is
> loaded on its own, so the invariant stated in `reference/subcommands.md` does
> not reach it — restated here rather than assumed: `perry-task start` /
> `status` / `stage` write the task store and journal through a durable recovery
> marker, then render the board and append the event. A normal failure rolls the
> pair back; a crash is completed on the next locked Perry run. Hand-editing a row here shows up at the next standup as a
> post-tool edit, and dispatch runs often enough that doing so would bury the
> signal in noise dispatch itself created. — per executor

**If the task carries a role**, the prompt is rendered from its card first —
`delegate.md § Render from the role card` and `§ Knowledge injection`, which
this file does not restate. Role and executor are different axes: the card says
who is being hired, the `Executor:` field says what instantiates it, and
`bin/perry-dispatch-limit` counts the latter only. A card's `executors` field
may narrow which runtimes are acceptable; it never grants a slot.

## The tree the agent works in

> **A dispatched agent works in its own git worktree. The primary checkout is
> never switched by an agent; it merges the agent's branch afterwards, and that
> merge is the only code operation it performs.**

This is the rule; `git-boundaries.md` and `delegate.md` reference it and do not
restate it. It governs every executor, not only the native subagents.

**What each side does.**

- The agent gets an isolated worktree and commits on its own branch. **Whether
  it then pushes is the project's answer, not this file's** — where `git push`
  and `origin` are in `.perry/hook.md § High-stakes operations`, which is the
  default list bootstrap writes, the agent commits and stops there
  (`git-boundaries.md`).
- **Pin the base SHA in the prompt, and make the agent ASSERT it.** A worktree
  branches from wherever the tool cuts it, which is not necessarily where the
  work being reviewed lives. Stating the branch point is half the rule and the
  half that does not work on its own: it tells the agent what to expect and
  leaves it to notice.

  **The brief carries three things and the agent does three things.** The brief
  names the base SHA, says main's tip, and says what to do when they differ.
  The agent runs `git log --oneline -1` and
  `git merge-base --is-ancestor <base> HEAD`, **fast-forwards its own branch
  only** when it is behind on a strict ancestor with a clean tree, and
  **reports what it found either way** — including when the base was correct,
  because "I checked and it was fine" and "I did not check" are different
  answers and only one of them is evidence.

  **Measured three times, and the record accumulates rather than being
  replaced.** On 2026-09-02 four agents were cut from a `main` that contained
  none of the specs they were told to read. On 2026-09-07 three agents were
  handed a base 496
  commits stale; all three noticed at their own cost and invented **three
  different** recovery protocols, and one reviewer could not check out at all
  and rebuilt the tree from `git archive` (`TASK-381`). On 2026-09-12 it
  happened **five more times**, two of them trees that did not contain the code
  the agent was sent to review — and it cost **nothing**, because every brief
  pinned the base and every agent asserted it. The difference between those two
  days is this bullet.

  **What this does not fix.** The worktree is cut by the harness, outside this
  repository; the recurring stale base was already 102 commits behind at one
  session's start, and the branches sitting on it have no worktree attached, so
  it is neither a pool nor a tip. Perry has no code on that path. This is a
  mitigation that has been measured to work, not a repair.

  Worktrees share the object database, so `git show <branch>:<path>` reaches
  anything committed — say so, or inline the spec.
- The primary checkout merges with `git merge --no-ff <branch>` once the row's
  verification allows it, keeping the row's work one identifiable commit, then
  removes the worktree and deletes the branch.

**The merge cannot be delegated into the worktree**, and this was measured
rather than assumed — git refuses both routes while the primary checkout holds
`main`:

```
$ git checkout main                      # from the second worktree
fatal: 'main' is already used by worktree '…'
$ git push <primary> HEAD:main
 ! [remote rejected] HEAD -> main (branch is currently checked out)
```

So a merge outside the primary checkout means a merge on the *remote* — a PR,
which needs the hook to permit a push. **A project therefore has exactly two
shapes available, and its hook already chooses between them**: push escalated →
agent commits, primary checkout merges; push permitted → agent opens a PR and
the verifying lane merges it. Read the hook once per dispatch; do not re-derive
the argument.

### Where the agent puts a scratch file

> **A dispatched agent's scratch directory is DERIVED FROM ITS WORKTREE and
> lives OUTSIDE the repository. It is never a shared directory the agent is
> asked to namespace inside.**

Every dispatched prompt carries this block verbatim, and the agent re-derives it
in each command rather than remembering a name:

```sh
# perry-scratch-derivation — do not edit without re-reading TASK-421
PERRY_SCRATCH="${TMPDIR:-/tmp}/perry-scratch/$(basename "$(git rev-parse --show-toplevel)")"
mkdir -p "$PERRY_SCRATCH"
```

**The agent contributes nothing to the uniqueness, and that is the whole
mechanism.** The distinguishing component is the worktree directory name, which
the dispatching tool minted when it honoured `isolation: "worktree"` — the agent
reads it, it does not choose it. So an agent that writes the dumbest possible
filename, `$PERRY_SCRATCH/baseline.txt` — the exact name that collided four
times — still cannot collide with a concurrent agent, because the parent differs
by construction. **"Pick a unique name" is what failed; this asks for no name at
all.**

**Outside the repository is the other half, and it is load-bearing.** An in-repo
scratch directory reddens two tree-walkers that scan by name at any depth:
`tests/header_rule.py` admits any Python-parseable file it finds as a real
reader, and `tests/tree_guard.py` reports the tree as moved. A round that put
copies of Perry source in an in-repo `.scratch/` turned a named test red while
obeying its brief. `${TMPDIR:-/tmp}` is invisible to both, so the isolation
costs no test its coverage.

**What this inherits, and what it therefore does not promise.** The scratch
isolation is exactly as strong as the worktree isolation above it and no
stronger: an agent dispatched **without** `isolation: "worktree"` resolves
`--show-toplevel` to the shared checkout, and two such agents get the same
scratch root. That is not a second hole to close but the same one — which is why
the flag is mandatory rather than recommended.

**Where the normative part of this section ends.** Everything above this
paragraph, plus the whole of § `Executor: claude-subagent` below, is pinned
byte-for-byte by `tests/test_spec_scannability.py::TestTheAgentGetsItsOwnTree`:
a sentence added, removed or reworded anywhere in it reddens a named test, and
re-pinning is a deliberate second edit in the same commit. Everything from the
next heading to the end of this section is **rationale, and deliberately not
pinned**, so the two observed failures and the argument can be improved without
touching a test. Nothing there grants an exception — a sentence in it that reads
like one is a defect, not a rule. Normative text goes above this paragraph.

### Why it is a rule and not a preference

This file used to say "work on a feature branch" and nothing about the tree, and
a branch instruction with no isolation instruction is an instruction to run
`git checkout -b` *in the shared working tree*. Observed live, twice, in one
day:

- **2026-09-02** — TASK-247 was dispatched as a `claude-subagent` told to create
  `coding/task-247-config-predicate`. It did, in the shared tree, so the PMO's
  own checkout moved onto that branch. Every PMO write afterwards — journal,
  evidence, board — committed there. A `git add -A` in the agent's commit would
  have swept two lanes into one code commit.
- **2026-09-03** — the bill arrived: four V4 review documents and 91 journal
  lines were on that branch and not on `main`, while a merge commit bearing the
  branch's name sat in `main`'s history and a commit message asserted the work
  was live on `main`. True of the code, false of the records.

The failure is also **invisible from inside**: TASK-247's own agent reported that
every `bash tests/run` step 0 failed naming only PMO-lane paths, and that this
"cannot be distinguished from a real tree-guard failure by the guard's own
output".

### `Executor: claude-subagent` (Claude Code only)

- **Host gate**: requires `$HOST = claude-code`. On OpenCode or Codex this executor is unavailable — refuse per the strict matrix in `../../reference/host-capabilities.md`.
- Use the `Agent` tool with `subagent_type: general-purpose`.
- Build prompt = **bounded architecture context + architecture preamble (see § Architecture preamble below)** + spec full text + project hook safety constraints + Git expectation block (see `git-boundaries.md`) + standard RESULT format. The author reports implementation facts, not an architecture verdict.
- Async-ness from spec's size hint: `Estimated cycle: small` → `run_in_background: false`; `medium | large` → `run_in_background: true`.
- **Pass `isolation: "worktree"`. It is not optional** — see § The tree the agent works in, below.
- **Include the `perry-scratch-derivation` block verbatim** — see § Where the agent puts a scratch file. A prompt that hands out a shared directory and asks the agent to namespace inside it is the defect that section exists to remove; it has been observed five times.
- Sub-agent shares parent cwd, and that is a fact about the *process*, not a licence for the *tree*: without `isolation`, the agent's `git checkout -b` moves the shared working tree, and every other lane's writes land on its branch. For split-repo projects: instruct sub-agent to use `git -C <code-repo-path> ...` for every git command (do NOT `cd`; preserves parent cwd state).

### `Executor: opencode-subagent` (OpenCode only)

- **Host gate**: requires `$HOST = opencode`; refuse on Claude Code or Codex CLI.
- Use the `Task` tool with `subagent_type: general`.
- Build the same complete prompt as `claude-subagent`: bounded architecture context/preamble + spec + safety constraints + git expectation + standard RESULT contract (no author compliance block).
- The call is always synchronous. On return, release the slot and continue directly to objective verification; architecture review belongs to integration. Do not rely on a background notification or write an awaiting-completion message after Task has returned.
- Task shares the project context. For split repos, retain the explicit absolute code-repo path and `git -C` instruction.

### `Executor: codex`

- **MANDATORY pre-flight** before the first codex dispatch in any session (or after the 6h smoke cache expires):
  ```
  bash "$PERRY_HOME/bin/perry-codex-preflight"
  ```
  The script: (a) `codex --version` ≥ `PERRY_CODEX_MIN_VERSION` (default `0.100.0`); (b) smoke test (`codex exec "Reply with just: PERRY_OK"`, 60s timeout if `timeout` / `gtimeout` is installed). Cached 6h at `~/.cache/perry/codex-smoke-pass`. Exit non-0 → **refuse + surface stderr verbatim + fall back to delegate**. Catches stuck CLI / broken auth / version-rejected-by-API BEFORE we fire async dispatch that would silently hang.
- Then: Bash → `cd <code-repo-path> && codex exec "<prompt>"`.
- Always async (codex is its own session). On Claude Code, pass `run_in_background: true`. On OpenCode or Codex CLI, use shell backgrounding with log + PID; see `../../reference/host-capabilities.md § No-background-shell-tool fallback`.
- Prompt MUST be self-contained (codex doesn't see the journal, BOARD, or any prior context). Include: **bounded architecture context + architecture preamble** + spec full text + relevant project hook excerpts + git expectation + standard RESULT format (no author compliance block) + the explicit list of files codex can read for context + **the `perry-scratch-derivation` block verbatim** (§ Where the agent puts a scratch file). Self-contained means this one too: a codex session reads no startup page, so the scratch rule reaches it only if the prompt carries it.
- Capture stdout to a temp file; on completion, parse for the RESULT block.
- If the long-running codex call fails (non-0 exit / no RESULT block / timeout), per the failure handling below, mark task `review` and surface raw output. Pre-flight is the cheap pre-check; this is the post-check.

## What the executor runs each round (`DESIGN-021 § 5.5`)

> **The brief tells the agent to run `bash tests/run --tier affected --base <the
> pinned base SHA>` at the end of every round, and to paste the printed
> selection block into its result.** Not the whole suite: the whole suite is
> 964 module-seconds, and an executor that pays it on every round pays it four
> or five times for a change that touches a handful of modules.

**The sentence that goes in the prompt, and it goes in whole:**

```
Run `bash tests/run --tier affected --base <base SHA>` at the end of every
round. It runs the smoke checks — the schema drift guard, every shipped script
compiling and answering --help, and the tree guard — plus the test modules
your change selects, and it prints which modules it selected and the rule that
selected each. Paste that selection block into your RESULT.

A red in `affected` is a red: fix it before you report.
A green in `affected` is NOT a green suite. It ran the modules your change
selects and nothing else, so it cannot tell you that the rest of the suite
still passes. Say "green for --tier affected" in your result, never "the suite
is green", and quote the module count you actually ran.
```

**The other three names**, for a round that wants them: `--tier smoke` (the
cheap checks alone, ≤ 30 s), `--tier full` (every module except the harness
self-tests — exactly what bare `tests/run` has always run), and `--tier slow`
(the harness self-tests too, the old `--slow`). Bare `tests/run` is unchanged
and still means `--tier full`; `--lint`, `--serial`, `--only` and `--slow` all
keep their meaning. Add `--dry-run` to any of them to print the selection and
run nothing.

**Full merge acceptance runs on an isolated candidate.** From the primary
checkout, resolve the current base and candidate, then run the supported gate:

```bash
env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME python3 tests/merge-check \
  --base main delivery=<candidate-branch> --tier full --record <new-external-dir>
```

Use a unique scratch directory outside the checkout (the scratch rule above),
not a shared name. This invokes every `tests/run` full stage, including syntax/help
and the tree guard. `--checks` is diagnosis only. Any full failure refuses
acceptance, including a pre-existing base failure; attribution explains it but
does not excuse it. Full timings update measured modules only; deferred slow
modules keep their prior source. A new test module is initially registered as
`sec: null, source: null` in the existing duration inventory; the coding task need
not measure it by hand. The gate records measurements, not inventory discovery.
`--tier slow` is the full run plus harness tests,
not an automatic side effect of requesting a record.

The record directory holds exact input refs/SHAs, tested tree, outcome and emitted
`durations.json` hash. The main integrator coordinates its import on the tested
integration tree; the authorized Coding Agent commits that product artifact on
an integration branch. PMO does not write product files in the primary checkout.
Do not invent a future merge SHA: timing provenance cites existing base/candidate
commits and the tested tree. Keep the named input refs unchanged during this step.

After that artifact-only commit, in the clean integration checkout run:

```bash
python3 tests/merge-check --verify-receipt <new-external-dir>/receipt.json
env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME bash tests/run --tier slow
```

Receipt verification requires the same code tree except for the exact recorded
artifact, checks current input refs and runs duration provenance validation.
The separate slow gate verifies the final recorded artifact and harness; retain
both receipts. If either input ref moves, any other code changes, or a check
fails, regenerate/revalidate the affected candidate before acceptance. Immediately
before the authorized merge, recheck the receipt and exact base/candidate refs;
merge only the verified integration branch/tree. Neither command merges or writes
main, and local checks do not install remote branch protection. Existing release
record rules still apply; an agent's green `affected` is never this acceptance.
Also complete § Architecture review on the exact final integration candidate;
the test receipt does not supply the independent architecture judgment.

**What this asks of whoever merges**: when a `--tier affected` result comes
back green and the full run on the merge result goes red, the miss is a
`COVERS` entry that was not there. Add it in the same change (`DESIGN-021 § 7`,
first row) rather than widening the tier.

## Architecture preamble (prepended to every dispatched agent's prompt)

Apply `dispatch-preflight.md § Pre-flight` step 5a's eligibility. The dispatcher uses the root architecture's
confirmed §2 component list to select each touched component's module document;
it records the mapping and any missing document or unconfirmed component.
Inject root §1, §3 and §6 with source paths/line numbers and those module documents.
Read §2, §4, §5 and §8 only on demand; do not inject the full root document.
Unknown context is explicit and must be resolved before claiming the gate passed.
Manual handoffs through `delegate.md` use the same bounded context and standard
RESULT; manual authors cannot provide their own fresh-review verdict either.

```
Read the supplied root architecture §1, §3 and §6 and touched module documents
before editing. Existing architecture is binding. Surface contradictions and
missing context; a decided-section contradiction needs the existing user
decision gate before it can land. Return the standard RESULT with your exact
base/head, paths and verification evidence. Do not certify your own architecture
compliance: the integration reviewer owns that judgment in a fresh context.

=== BEGIN ARCHITECTURE CONTEXT ===
<root §1/§3/§6 and agent-selected touched module documents, with line citations>
=== END ARCHITECTURE CONTEXT ===
```

## Architecture review (the independent gate)

Apply `dispatch-preflight.md § Pre-flight` step 5a's eligibility; name any independent project requirement.
After objective verification, **before accepting the exact integration candidate**,
the integrator records immutable base/head SHAs, `git diff --name-status
<base> <head>`, `git diff --summary <base> <head>` and the full
`git diff <base> <head>`. Compare both trees (including old/new rename paths,
file modes and version declarations), not the spec's claimed touched sections.
Evaluate and record all six trigger classes as true / false / unknown with facts:

| Trigger | Typed facts to inspect |
|---|---|
| Listed boundary paths | `viewer/parsers.py`, `bin/lib/`, `schema/` (including `schema/*-contract.md`), root or lane `SKILL.md` (`goals/`, `work/`, `decide/`) changed |
| New top-level directory | A top-level directory exists at head but not base |
| New bin executable | A `bin/` executable is added, renamed in, or gains executable mode relative to base |
| Contract-version change | Base/head version declarations differ; read the relevant declarations on demand, including root §5 |
| Root architecture edit | Root `ARCHITECTURE.md` changed, added, removed or renamed |
| Module architecture edit | A component module document changed, added, removed or renamed, using the confirmed §2 index from both trees |

All false → record `Architecture trigger: none` with the six facts in merge
evidence, and run no architecture reviewer or COMPLIANCE block. A diff confined
to `perry/` (including `perry/evidence/`) has no trigger. Any true → fresh review.
Any unknown → record what is missing and resolve it before acceptance; unknown
is never false. A component root §2 declares no module document for has none;
that is not missing context (USER-978). Missing root/module context or an unconfirmed component cannot
silently produce a pass. A spec saying `(none)` cannot suppress a diff trigger.

1. **Executor selection** (unchanged host eligibility):
   - On Claude Code (`$HOST = claude-code`): `Agent(subagent_type: general-purpose, run_in_background: false)`.
   - On OpenCode (`$HOST = opencode`): `Task(subagent_type: general)` — synchronous.
   - On Codex (`$HOST = codex-cli`): `codex exec` — synchronous.
   - A hook's `Review agent executor:` pin must be host-valid (`codex | claude-subagent | opencode-subagent | (auto)`); refuse a mismatched pin, never reroute it.
2. **Fresh brief**: use `review.md § Integration architecture reviewer brief`.
   Supply exact base/head/diff and trigger facts, root §1/§3/§6 with line numbers,
   and module documents selected by the agent from the confirmed component list.
   Supply §2's selection mapping; other root sections are read on demand.
   The reviewer did not implement the candidate and receives no author compliance
   attestation or inherited implementation conversation. The author cannot award
   this gate, V4 or V5.
3. **Evidence and disposition**: preserve the reviewer's `ARCHITECTURE COMPLIANCE`
   block verbatim in merge evidence with reviewer identity and timestamp. A
   decided-section contradiction stops acceptance and goes to the existing user
   decision gate (DESIGN-017 decision 2); never auto-override it. A described
   section drift needs correction and re-review, not an invented architecture
   rule. A missing/unknown verdict blocks acceptance. Task RESULT and task status
   processing remain separate; this gate grants neither task closure nor merge
   authority. Existing high-stakes screening, verification and no-self-merge stay.
4. **Candidate binding**: immediately before merge recheck base/head and diff
   against the evidence. Any candidate change, including integration adjustments,
   invalidates the prior selection/review; repeat on the new exact candidate.
   An executor's branch review is not review of a different integration tree.

## Common (post-dispatch, before completion)

- **Every executor makes the in-flight state visible before it starts.** If the row is `not_started`, run `perry-task start`; if it is `blocked` or `review`, run `perry-task status <ID> --actor <actor> --status in_progress`; if it is already `in_progress`, run `perry-task next`. In every case set `Next action` to `dispatched <time> via <executor>; awaiting completion`. This happens after the slot is registered and before invoking the executor, including synchronous OpenCode Task. A crashed parent then leaves an honest in-progress row plus a stale-cleanable slot rather than a task that still says `not_started`.
- For OpenCode native Task, call Task synchronously after that transition, then process completion in the same turn. Do not promise a later notification.
- For asynchronous executors, reply `Dispatched <TASK-X> via <executor>. Will report when done.` OpenCode native dispatch instead reports the verified result after synchronous completion.

## Optional delivery integration

Before integrating completed work, if the project has an applicable approved
release policy, read `$PERRY_HOME/packs/software-ops/releases.md` and coordinate
its allocation/checks through the main integrator. Preserve delivery identity and
report integrated versus published accurately. No policy adds no version step;
this does not change dispatch safety or automatically close the task.

## On completion (notification arrives)

0. **Release the concurrency slot first thing**: `bash "$PERRY_HOME/bin/perry-dispatch-limit" release <task-id>`. Do this BEFORE any verification work, so a slow verification step doesn't keep blocking other dispatches. (Stale markers auto-clean after `PERRY_DISPATCH_STALE_TTL` seconds — **default 4h** (why 4h: `dispatch-notes.md § Why the stale TTL is 4h`) — covering the case where PMO crashed mid-completion. **Every reap now prints `⚠️  Reaped dispatch slot: <marker>` on stderr.** If you see that line while the agent it names is still running, the cap is short by one for the rest of that run: treat it as a real event, not noise, and raise `PERRY_DISPATCH_STALE_TTL` for the session rather than dispatching into the gap.)
1. Read the agent's RESULT block. Required fields:
   - `Branch: <name>` — always. It is what the primary checkout merges (`git-boundaries.md`), so it is required on every project whatever the push answer is.
   - `PR URL:` — **only where the project's hook permits a push.** Where `git push` / `origin` are escalated, the compliant agent opened no PR and has no truthful value for this field; requiring one there would make the honest answer unwritable and step 4 below gates the `review` transition on required fields being present. On such a project the field is `n/a — push is escalated on this project`, and that is a complete answer rather than an excuse.
   - `Files changed: <count>` + bullet list
   - `Tests: <pass>/<total>` + command used
   - `Cycle time: <minutes>` (for calibration)
   - `Notes:` (anything unusual)
2. Run **objective verification** from the spec's `Verification` section. Anything that looks like a runnable command (starts with `$`, names a CLI like `pytest` / `gh` / `gim`, or has a clearly executable shape) — run it. Capture output.
3. Cross-check against `Out of scope` — if the agent's `Files changed` list contains paths declared out-of-scope, raise a hard failure (likely scope creep or safety violation).
4. **Status decision**:
   - All objective verifications pass + no scope violation + RESULT block has all required fields → status `review` (NEVER auto-`done`; subjective verification is the user's, per the project's standing rule).
   - Anything fails → status `review` with failure annotation; no auto-retry, no auto-rollback.
   - **On a `pipeline`- or `queue`-mode track, the stage usually moves too, and
     it goes through the tool**: `perry-task stage <ID> --actor <actor> --stage <name>`, which
     re-stamps `Stage since` in the same write and refuses a stage outside the
     track's declared vocabulary. `Stage` and `Status` are orthogonal, so a
     stage move produces no status change and would otherwise leave no trace
     anywhere; a hand-edited cell leaves the dwell clock reading from whenever
     the row was created. This file is loaded on its own, so the invariant in
     `reference/subcommands.md` does not reach it.
5. Write `evidence/<YYYY-MM>/<TASK-ID>-dispatch-<YYYY-MM-DD-HHMM>.md`:
   - Header (date, executor, async, cycle time)
   - Full agent RESULT block verbatim
   - Objective verification commands + their outputs
   - Subjective verification items (copied from spec, marked `[user-verify]`)
   - PR URL + branch + commit SHA
6. `"$PERRY_HOME/bin/perry-task" status <TASK-ID> --actor <actor> --status review --next "user verifies subjective items: <…>"` — row, journal line and event together. Then record the evidence path, executor and cycle time in the dispatch evidence file, which is where per-run detail belongs.
7. Surface to user: pass/fail summary + 1-line subjective verification ask.
8. The after-task budget checkpoint: `budget-boundary.md § Budget boundary`.

## Failure handling (mark `review`, no auto-retry)

- Executor crashed / non-zero exit / timeout → release the slot (`bash "$PERRY_HOME/bin/perry-dispatch-limit" release <task-id>`), write evidence with raw output, status `review`, surface failure summary, ask user retry / fix manually / drop.
- ff-only PR push failed → same, with manual-resolution hint.
- Agent declared `done` but tests failed → same.
- The release call MUST run on every failure path, not just success — otherwise a failed dispatch leaks a slot until stale-TTL expires (4h). The sweep is the backstop for a crashed agent, not a substitute for releasing.

## Cost / quota awareness

- Each `claude-subagent` call counts against the parent CC session quota (5-hour Sonnet caps, weekly Opus caps).
- Each `opencode-subagent` call consumes the OpenCode model/session quota and blocks the dispatch flow until Task returns.
- Each `codex` call counts against OpenAI quota.
- PMO does not enforce a per-call dollar cap; spec writer chooses executor as a quota-routing hint.
- Hooks may declare project-specific quota limits (e.g., "no more than 5 dispatches per day") — PMO honors those if present.

## RESULT block format (required from any dispatched agent)

```
=== RESULT ===
Branch: <name>          # always — this is what the primary checkout merges
PR URL: <url>           # only where the hook permits a push; otherwise
                        #   "n/a — push is escalated on this project"
Files changed: <count>
  - path/file1.py
  - path/file2.py
  ...
Tests: <pass>/<total> (command: <pytest ...>)
Cycle time: <minutes>
Notes: <anything unusual>
=== END RESULT ===
```

**On `Tests:` when the round ran a tier.** Write the command as it was typed —
`bash tests/run --tier affected --base <sha>` — and put the printed selection
block in `Notes:` or in the result document. The count on that line is then the
count of what ran, which for `affected` is a subset: name it as
`green for --tier affected (N of M modules)`, not as a green suite. A result
that says "the suite is green" over a 29-module run is the sentence this whole
tier arrangement has to avoid producing (`DESIGN-021 § 5.5`).

## Completion routing

After completed writes from `dispatch`, follow [the shared closing step](../../reference/next.md#closing-step); its skip rules apply.
<!-- next-close: work dispatch -->
