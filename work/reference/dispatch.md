# `/pmo dispatch <task-id>` — fully automated end-to-end

Same goal as `delegate` (see `delegate.md`) but **fully automated**. PMO renders the prompt, fires it at an executor, watches for completion, parses the result, runs any objective verification commands declared in the spec, writes an evidence file, updates BOARD + journal, and reports back. Subjective verification stays with the user (status moves to `review`, not `done`).

Executor contract: `claude-subagent | opencode-subagent | codex | manual`. `manual` routes to `delegate`; automated dispatch strictly follows the host matrix in `../../reference/host-capabilities.md`.

## 0 · Whether to dispatch at all

Dispatch has a **fixed cost that does not scale down with the change**: a
separate checkout, a pinned base, a brief, a baseline the agent must measure for
itself, a result document, a merge, and a verification pass by whoever merges
it. It also has failure modes the change itself does not have. Measured across
**eight dispatches in one session on 2026-09-07**: **seven were handed a base
~500 commits stale** (`TASK-381`), **two collided in a shared scratchpad**
(`TASK-373`), **one left a planted mutation in its tree** when it stopped, and
**one reddened the suite by following its scratch-location brief exactly**
(`TASK-385`). Four of those are rows that exist only because work was
dispatched.

**Do it inline when all three hold:**

- the change is **small and already specified** — you can state the edit and its
  acceptance in one sentence each, before starting;
- it needs **no fresh judgement** — nothing about it improves by being decided
  by someone who has not seen your reasoning;
- **you can verify it yourself** with a command whose output you would have
  asked the agent for anyway.

**Dispatch when any of these hold:**

- the work needs **a context you should not be carrying** — a wide enumeration,
  a long file read, a mutation battery;
- it needs **a judgement you are not entitled to make**, because you wrote the
  thing being judged — that is `review.md`, not this page;
- it is **long enough that doing it inline would crowd out the session's own
  work**, which is a real cost and not a stylistic one.

**The test is not size, it is whether a second context earns its setup.** A
forty-line edit you can state and check is cheaper inline even though it is real
work. A five-line edit that needs the whole suite enumerated to know it is right
is not.

## Pre-flight (any failure → refuse and fall back to `delegate`)

1. `evidence/<YYYY-MM>/<TASK-ID>-spec.md` exists.
2. Spec contains `Dispatch mode: auto` (default `manual` — explicit opt-in required).
3. Spec contains `Executor: claude-subagent | opencode-subagent | codex` (not `manual`). **If spec is `Dispatch mode: auto` but `Executor` is missing**, use the host-native choice UI for a one-shot choice; do NOT silently default. Offer `claude-subagent | codex | manual` on Claude Code, `opencode-subagent | codex | manual` on OpenCode, and `codex | manual` on Codex CLI. Persist the answer only if the user explicitly says "save this for next time". A spec pinned to another host's native executor is a hard host mismatch: refuse and request a spec edit or `/perry work delegate`. Matrix: `../../reference/host-capabilities.md`.
4. **Safety re-validation — you perform this judgement, and no command performs it for you.**

   Until 2026-09-04 this step was `"$PERRY_HOME/bin/perry-state" --escalation-scan <spec>` and the exit code was the verdict. That command is gone. `USER-916`: *"不要用python代码来检查文件语义。应该去掉这个检查逻辑，让agent自己来判断gate."* — Python is not to judge a document's meaning, `ADR-007` decision 3 says the Python layer never parses a document at all, and five rounds of trying to make the match correct ended with the measurement that settles it: **formatting alone moved the verdict in both directions.** A bold marker or a sentence-final full stop cleared a declared write to the claim surface; bolding an own-tree path `**perry/evidence/…**` made the gate *refuse*, because the head `**perry` contains a `*`. A reader has no such failure mode. The judgement is yours.

   **This is not "read the list and eyeball it".** That is what the step said before TASK-107 and it refused two dispatches in one day over the words "original" and "adopted". Work the five steps below in order, and write the answer down where the user can see it. A gate whose reasoning is not written is not reviewable.

   ### 4.1 — Get the list, and check it is armed

   Read `.perry/hook.md § High-stakes operations` **in full — the bullets and the prose around them**, not just the backticked spans. Then read `## Must escalate` in every `.perry/roles/*.md`.

   **The list is the union of the two, and a role only ever ADDS** (`DESIGN-006 § 5.2`, goal 6). A role that could subtract would let hiring one quietly narrow what the project refuses to do unsupervised, and nothing would show it — a narrowed gate passes everything it is asked, cheerfully. With no roles declared the union is the hook's list unchanged.

   `"$PERRY_HOME/bin/perry-state" --section project` still prints both halves and their union under `project.escalation` (`project`, `roles`, `union`, `origins`, `armed`) — it *extracts a declared list*, which is a bounded value space and stays in Python. It does not read the spec and it renders no verdict. Use it to show the user the list; the reading of the spec is yours.

   **If both halves are empty or absent** (`escalation.armed: false`), nothing is being screened. Do not treat that as a pass. Say so in one line — *"no high-stakes list in `.perry/hook.md`, so nothing is being screened; `/pmo` bootstrap writes the default list"* — and require an explicit go-ahead in chat before dispatching. `AskUserQuestion` is not sufficient here; this is a safety gate, per `SKILL.md § User-prompt convention`. (`/pmo autopilot` refuses outright in the same situation — `autopilot.md` pre-flight step 0.)

   **Bullets that arm nothing.** `perry-lint` reports a hook bullet carrying no extractable backticked span. When you read the section yourself that distinction stops mattering for *your* judgement — you can read an unbackticked sentence — but it still matters for what you tell the user, because `escalation.armed` and the delegation prompt are computed from the spans. Read the prose; report the gap.

   ### 4.2 — Get what the round does

   Read the spec's `## Files in scope` and `## Deliverable` in full, then `## Out of scope`.

   - `Files in scope` is the enumerated list of paths the round will write. It is a declaration.
   - `Deliverable` is prose describing the outcome.
   - `Out of scope` is what the spec has stated in writing that it does not do.

   **If neither `Files in scope` nor `Deliverable` is present and non-empty, you have nothing to judge from.** Do not read that as clean. Say so — *"this spec offers neither `## Files in scope` nor `## Deliverable`, so there is nothing here to screen; `subcommands.md § add-task` step 3 has the `## ` shape"* — and require an explicit go-ahead in chat, exactly as for an unarmed hook. 45 of Perry's own 149 specs are in that state, so this is common and is not by itself a reason to refuse the row; it is a reason not to claim you screened it. `perry-lint --root .` reports the condition across every spec at once, before any single dispatch reaches this step.

   ### 4.3 — Decide ownership of every path, BEFORE you tidy any text

   **This step comes first and its order is the point.** The characters that identify a foreign root are the same characters you would otherwise strip as formatting noise. `~` in `~/other-project/evidence/` is the marker that says *someone else's home*; `*` in `**perry/evidence/**` is markdown emphasis. Strip formatting first and you lose the ownership signal with it; treat every such character as an anchor and you refuse your own tree. **So classify the root before you normalise anything, and disambiguate by pairing, not by stripping:**

   > An emphasis marker comes in a **balanced pair** wrapping a span — `**perry/evidence/2026-09/**`, `_schema/state-schema.json_`. An anchor is **unpaired and sits at the head of the path itself** — the `~` in `~/other-project/`, the `$` in `$PERRY_HOME/inputs/`, the leading `/` in `/srv/data/`.

   That test needs no stripping pass at all, which is why it is stated this way.

   Then, on the path as written:

   - **Relative is internal, and that is the entire rule.** A relative path resolves against the root of the project this spec belongs to, so `evidence/`, `perry/evidence/2026-09/x.md` and `evidence/**/*-spec.md` all name *this* project's tree and cannot name anyone else's.
   - **Foreign is exactly five shapes:**
     1. absolute — `/srv/data/`
     2. home anchor — `~/.claude/skills`, `~/other-project/evidence/`
     3. variable anchor — `$PERRY_HOME/inputs/`
     4. upward escape — `../sibling/design/`
     5. **unresolved root — `<target>/evidence/`, `{{project}}/design/`.**

   **Shape 5 is a judgement made in the safe direction on purpose, and it is the one clause most likely to be dropped when this rule is rewritten.** A root nobody has resolved is not a root known to be this project. A gate that guesses *"probably mine"* about a placeholder is the guessing this whole step exists to stop. Keep it.

   **Why ownership decides anything at all.** The hook's destructive-filesystem bullet reads *"overwriting a project's **own** `design/`, `evidence/`, `knowledge/`, `inputs/`"* — it is about a tree Perry does not own. So:

   | Path as written in the spec | Root | Verdict on the `evidence/` entry |
   |---|---|---|
   | `perry/evidence/2026-09/` | relative → this project | **allowed** — this project's own tree; the bullet is not about it |
   | `**perry/evidence/2026-09/**` | `**` is a balanced pair → emphasis, not an anchor; head is `perry` → this project | **allowed** — identical to the row above |
   | `~/other-project/evidence/2026-09/` | unpaired `~` at the head → home anchor → foreign | **REFUSED** — a project Perry does not own |
   | `$PERRY_HOME/inputs/` | unpaired `$` at the head → variable anchor → foreign | **REFUSED** |
   | `<target>/evidence/` | unresolved root | **REFUSED** — shape 5 |

   A bare directory name on its own — `design/`, `evidence/` — **cannot say whose directory it is**, so where a spec writes one with no root at all, ask which tree the surrounding sentence puts it in and refuse if the answer is not this one.

   ### 4.4 — For each list entry, ask one question: does this round DO it, or does it only NAME it?

   **Doing refuses. Naming does not.** This is the whole judgement, and it is the one a reader makes effortlessly and a matcher cannot make at all. Six tells, each with a case behind it from this repository's own corpus:

   1. **A file in this tree, versus the operation the hook means.** The hook's `diagnose` is the *`diagnose` execute stage* — Perry running its diagnosis against a project. `bin/perry-diagnose` and `tests/test_diagnose.py` are files in this repository. Editing the file is not running the stage. (`TASK-108`, refused by the scanner on `diagnose`.)
   2. **Quoted as data.** A fragment appearing inside a list of fragments — hook entries being added, matcher examples, test fixtures — is data this round *handles*, not an operation it *runs*. `TASK-107`'s `Deliverable` names `~/.claude/skills`, `ln -s`, `ln -sf`, `ln -snf`, `publish`, `published`, `rm -rf`, `--force-with-lease` and `$PERRY_HOME` — every one of them as an example of what its matcher must still match. That round installs no host skill, publishes nothing and deletes nothing.
   3. **Cited as precedent.** *"the `adopt` / `diagnose` precedent the router already states"*, *"one row beside `adopt` / `diagnose` / `relocate`"* — a reference to behaviour that already exists. (`TASK-220`.)
   4. **The ordinary English word.** `setup` in *"the harness re-does setup per test"* is a common noun; the hook's `setup` is host skill installation. Test: **substitute an everyday synonym and see whether the sentence stays true.** *"the harness re-does its preparation per test"* — still true, so it was the English word. *"run `/perry preparation`"* — false, so that one is the operation. (`TASK-244`.)
   5. **The line states its own verb and the verb is read.** *"setup and hook code that reads repository documents — read."*, under a section opening *"Read-only survey. The only file this round writes is its own report."* A round that has told you its verb has answered this question already. (`TASK-099`.)
   6. **The spec pre-commits to stopping.** *"`schema/state-schema.json` — only if a new field is declared. **This is the claim surface; changing it is escalated.** If the design points that way, stop and file the question rather than editing it."* with `Out of scope` confirming *"Editing `schema/state-schema.json` … is a separate, user-authorised step."* That is a spec that has read the gate and bound itself to it. **Read it as compliance, not as a contradiction** — the scanner read it as one and refused, which taught rows that quoting the gate is expensive. Carry the pre-commitment into the delegation prompt verbatim so the executing agent inherits it.

   **What makes it a DOING**, on the other side:

   - the round's own verb takes the operation as its object — *"the forms … **are added to** `.perry/hook.md`"*, *"both **change in this edit**"*;
   - any foreign-rooted path from 4.3 appears anywhere in scope;
   - the round would run the command, not merely edit the file that contains it.

   **`Files in scope` cannot be cancelled by `Out of scope`; `Deliverable` can.** `Files in scope` is an enumeration of write targets, so a spec that lists a path there and *also* disclaims it has contradicted itself — and a contradiction is not a pass. Report the disagreement to the user and let them resolve it; do not pick the reading that dispatches. This is distinct from tell 6, where the spec resolves its own tension by naming the escalation and pre-committing to stop.

   ### 4.5 — Standing entry: this round does not rewrite the gate that constrains it

   **Not from the hook's bullets, and stated here rather than added there.** `.perry/hook.md`'s content is the user's, and this file does not edit it. But a round whose `Files in scope` names `.perry/hook.md`, `work/state/hook_TEMPLATE.md`, or this step of this file is a round that changes what Perry refuses to do unsupervised — in this project, and for `hook_TEMPLATE.md` in every project Perry adopts afterwards. **Escalate it and say why.** An agent that may widen its own gate has no gate.

   This is what refuses `TASK-107`, whose `Files in scope` reads *"`.perry/hook.md`, `work/state/hook_TEMPLATE.md` — the matching rule sentence"* and whose `Deliverable` item 5 says the dropped forms *"are added to `.perry/hook.md` and to the template's defaults"*. It is **not** refused by the nine high-stakes fragments its `Deliverable` quotes — those are tell 2, and a procedure that refused on them is the same procedure that refuses `TASK-244` on the word `setup`.

   If the user would rather have this as a hook bullet, that is theirs to add and this paragraph then defers to it; if they would rather not have it at all, strike this sub-step. It is written down so that the verdict is reproducible either way.

   ### 4.6 — Say the verdict, in writing

   Record, in the dispatch evidence file and in chat:

   - which list you screened against, and whether it was armed;
   - which sections of the spec you read, and whether either was missing;
   - every list entry you found in the spec, each marked **doing** or **naming**, with the tell and the quoted line;
   - the verdict: **allow**, **refuse**, or **ask**.

   **`ask` is a real outcome and the honest one when you are unsure.** In interactive dispatch it is a question to the user in chat. Under `/pmo autopilot` it is a **skip** — see `autopilot.md` pre-flight step 0 and the `Skipped — high-stakes` disposition; autopilot runs unattended, so an unsure judgement there resolves in the safe direction without asking.

5. Spec contains a `Subjective verification:` section (may be `(none)`); items there will be surfaced to the user at completion, never auto-validated.
5a. **Architecture compliance pre-flight** (see `$PERRY_HOME/packs/software-ops/architecture.md § Dispatch integration`):
    - Read `ARCHITECTURE.md` at project root (full text). If `Status: draft` → log a warning but don't refuse (draft window allows iteration). If file missing AND spec's `Touches architecture:` is non-empty → refuse (spec claims sections that don't exist).
    - Read spec's `Touches architecture:` field. For every section ref listed (`§N`, `§N.NN-M`), verify it exists in the doc. Refuse on mismatch (malformed spec).
    - For each touched non-negotiable in §6 marked `Severity: hard` → use `AskUserQuestion` (header = `NN-N`, options): `Proceed — change is reviewed (Recommended only with reason) | Refuse — revise spec | Refuse — escalate to manual delegate`. "Proceed" requires a written one-line justification copied into the dispatch evidence file's header.
    - For soft non-negotiables → single `AskUserQuestion` (header = `Architecture`, multiSelect) listing each soft NN as an option with description = the rule text. Selection = acknowledgement.
    - `Touches architecture: (none)` → no friction at this stage, but the review agent still runs after completion (§ Architecture review below).
5b. **Deployed-task pre-check**: if spec has `Deployed: yes`, verify the spec contains a non-empty `## Observability` section (Success signal / Failure diagnosis / Runbook path). If missing → refuse and ask user to fix the spec first. The runbook file itself is not required to exist yet at dispatch time (often the dispatched task creates it) — only the observability spec field is mandatory.
6. **Concurrency check**: `bash "$PERRY_HOME/bin/perry-dispatch-limit" register <task-id> <executor>`. Exit 0 = slot reserved, proceed. Exit 1 = limit hit; stderr lists what's currently in flight. On limit-hit, use the host-native choice UI: `Wait — show in-flight (Recommended) | Switch to another host-valid executor | Fall back to /perry work delegate`. Defaults are 2 per automated executor and 3 total; overrides are `PERRY_MAX_DISPATCH_CODEX`, `PERRY_MAX_DISPATCH_SUBAGENT`, `PERRY_MAX_DISPATCH_OPENCODE_SUBAGENT`, and `PERRY_MAX_DISPATCH_TOTAL`. On Codex the cap is advisory across separate sessions.

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
- Build prompt = **`ARCHITECTURE.md` full text + architecture preamble (see § Architecture preamble below)** + spec full text + project hook safety constraints + Git expectation block (see `git-boundaries.md`) + RESULT format including the mandatory `ARCHITECTURE COMPLIANCE` block (see § Architecture compliance RESULT).
- Async-ness from spec's size hint: `Estimated cycle: small` → `run_in_background: false`; `medium | large` → `run_in_background: true`.
- **Pass `isolation: "worktree"`. It is not optional** — see § The tree the agent works in, below.
- **Include the `perry-scratch-derivation` block verbatim** — see § Where the agent puts a scratch file. A prompt that hands out a shared directory and asks the agent to namespace inside it is the defect that section exists to remove; it has been observed five times.
- Sub-agent shares parent cwd, and that is a fact about the *process*, not a licence for the *tree*: without `isolation`, the agent's `git checkout -b` moves the shared working tree, and every other lane's writes land on its branch. For split-repo projects: instruct sub-agent to use `git -C <code-repo-path> ...` for every git command (do NOT `cd`; preserves parent cwd state).

### `Executor: opencode-subagent` (OpenCode only)

- **Host gate**: requires `$HOST = opencode`; refuse on Claude Code or Codex CLI.
- Use the `Task` tool with `subagent_type: general`.
- Build the same complete prompt as `claude-subagent`: architecture text/preamble + spec + safety constraints + git expectation + RESULT and ARCHITECTURE COMPLIANCE contracts.
- The call is always synchronous. On return, release the slot and continue directly to objective verification and architecture review. Do not rely on a background notification or write an awaiting-completion message after Task has returned.
- Task shares the project context. For split repos, retain the explicit absolute code-repo path and `git -C` instruction.

### `Executor: codex`

- **MANDATORY pre-flight** before the first codex dispatch in any session (or after the 6h smoke cache expires):
  ```
  bash "$PERRY_HOME/bin/perry-codex-preflight"
  ```
  The script: (a) `codex --version` ≥ `PERRY_CODEX_MIN_VERSION` (default `0.100.0`); (b) smoke test (`codex exec "Reply with just: PERRY_OK"`, 60s timeout if `timeout` / `gtimeout` is installed). Cached 6h at `~/.cache/perry/codex-smoke-pass`. Exit non-0 → **refuse + surface stderr verbatim + fall back to delegate**. Catches stuck CLI / broken auth / version-rejected-by-API BEFORE we fire async dispatch that would silently hang.
- Then: Bash → `cd <code-repo-path> && codex exec "<prompt>"`.
- Always async (codex is its own session). On Claude Code, pass `run_in_background: true`. On OpenCode or Codex CLI, use shell backgrounding with log + PID; see `../../reference/host-capabilities.md § No-background-shell-tool fallback`.
- Prompt MUST be self-contained (codex doesn't see the journal, BOARD, or any prior context). Include: **`ARCHITECTURE.md` full text + architecture preamble** + spec full text + relevant project hook excerpts + git expectation + RESULT format including mandatory `ARCHITECTURE COMPLIANCE` block + the explicit list of files codex can read for context + **the `perry-scratch-derivation` block verbatim** (§ Where the agent puts a scratch file). Self-contained means this one too: a codex session reads no startup page, so the scratch rule reaches it only if the prompt carries it.
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

**Where the full suite runs today, stated plainly because the alternative is a
gap nobody is watching.** There is **no automatic merge gate**: `TASK-450`
builds it and it is not built. Until it lands, **the primary checkout runs
`bash tests/run` itself on the merge result, before `git merge --no-ff`**, and
that run — not the agent's `affected` run — is what says the suite is green.
An agent's green `affected` is a reason to merge-check, never a substitute for
it.

**What this asks of whoever merges**: when a `--tier affected` result comes
back green and the full run on the merge result goes red, the miss is a
`COVERS` entry that was not there. Add it in the same change (`DESIGN-021 § 7`,
first row) rather than widening the tier.

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
   - On OpenCode (`$HOST = opencode`): `Task(subagent_type: general)` — synchronous.
   - On Codex (`$HOST = codex-cli`): `codex exec` (sync, ~60s).
   - Per-project hook may pin `Review agent executor:` to a host-valid value (`codex | claude-subagent | opencode-subagent | (auto)`). A host-mismatched pin is refused, not rerouted.

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

4. **Status decision.** Both outcomes land through `perry-task status`, which
   writes the row, the journal line and the event together — § "On completion"
   step 6 is the same call. The annotation is passed as flags, not typed into
   a cell: `--next` is what shows on the board, `--reason` is what lands in the
   journal line and the event's `reason` field.
   - `PASS` → continue to the normal flow: `"$PERRY_HOME/bin/perry-task" status <TASK-ID> --actor <actor> --status review …`.
   - `FAIL: <ref>` →

     ```
     "$PERRY_HOME/bin/perry-task" status <TASK-ID> --actor <actor> --status review \
         --reason "architecture-failed: <ref>" \
         --next "architecture review FAILed at <ref> — re-dispatch or override"
     ```

     Then surface the FAIL message to the user; `close-task` will refuse until this is resolved (re-dispatch or explicit override).

5. **Skip conditions** (review agent does NOT run):
   - Spec's `Touches architecture: (none)` AND primary's `ARCHITECTURE COMPLIANCE` Touched sections is empty → skip (no architecture-relevant change). Note: if primary self-attests touching sections despite `(none)` in spec, run the review — primary is admitting scope drift.
   - `ARCHITECTURE.md` is `Status: draft` → run the review but mark its output `advisory`; FAIL does not block close.
   - Primary executor itself failed (objective verification failed, RESULT block malformed) → skip (no point reviewing a broken result).

6. **Cost note**: this is one extra small subagent / codex call per dispatch. Project hooks declaring tight quota may set `Skip review agent for: P2, soft-§-only` exemptions; the default is to always run.

## Common (post-dispatch, before completion)

- **Every executor makes the in-flight state visible before it starts.** If the row is `not_started`, run `perry-task start`; if it is `blocked` or `review`, run `perry-task status <ID> --actor <actor> --status in_progress`; if it is already `in_progress`, run `perry-task next`. In every case set `Next action` to `dispatched <time> via <executor>; awaiting completion`. This happens after the slot is registered and before invoking the executor, including synchronous OpenCode Task. A crashed parent then leaves an honest in-progress row plus a stale-cleanable slot rather than a task that still says `not_started`.
- For OpenCode native Task, call Task synchronously after that transition, then process completion in the same turn. Do not promise a later notification.
- For asynchronous executors, reply `Dispatched <TASK-X> via <executor>. Will report when done.` OpenCode native dispatch instead reports the verified result after synchronous completion.

## On completion (notification arrives)

0. **Release the concurrency slot first thing**: `bash "$PERRY_HOME/bin/perry-dispatch-limit" release <task-id>`. Do this BEFORE any verification work, so a slow verification step doesn't keep blocking other dispatches. (Stale markers auto-clean after `PERRY_DISPATCH_STALE_TTL` seconds — **default 4h**, raised from 1h by TASK-160 because the sweep was reaping markers 72 minutes into live runs and the cap silently stopped being the cap — covering the case where PMO crashed mid-completion. **Every reap now prints `⚠️  Reaped dispatch slot: <marker>` on stderr.** If you see that line while the agent it names is still running, the cap is short by one for the rest of that run: treat it as a real event, not noise, and raise `PERRY_DISPATCH_STALE_TTL` for the session rather than dispatching into the gap.)
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

## Failure handling (mark `review`, no auto-retry)

- Executor crashed / non-zero exit / timeout → release the slot (`bash "$PERRY_HOME/bin/perry-dispatch-limit" release <task-id>`), write evidence with raw output, status `review`, surface failure summary, ask user retry / fix manually / drop.
- ff-only PR push failed → same, with manual-resolution hint.
- Agent declared `done` but tests failed → same.
- The release call MUST run on every failure path, not just success — otherwise a failed dispatch leaks a slot until stale-TTL expires, which since TASK-160 is 4h rather than 1h. The sweep is the backstop for a crashed agent, not a substitute for releasing: it is deliberately slower than the longest cycle this project has measured (2h15m), so a leaked slot is a slot lost for the rest of the afternoon.

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
