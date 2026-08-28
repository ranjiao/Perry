# `/pmo delegate <task-id> <role>` — render manual prompt

Generate a self-contained delegation prompt for another agent. The user pastes
it into a fresh Claude / codex session manually. PMO does not execute the work
itself.

`<role>` names a card in `.perry/roles/` — the project's own declaration of who
it hires (DESIGN-006 § 5.2). There is no built-in list of agent types: what used
to be three names written into this file is now three cards a project can copy,
edit, or ignore (`packs/software-ops/roles/`). **A project that has declared no
role card behaves exactly as it did before roles existed** — see § Roleless
projects below, which is the fallback that used to be the only path.

For automated end-to-end execution use `dispatch` instead (see `dispatch.md`).

## Record the delegation before rendering the prompt

```
"$PERRY_HOME/bin/perry-task" status <TASK-ID> --status in_progress \
    --next "delegated to <role>; awaiting paste-back"
```

This is the only state `delegate` writes, and it is not optional. Rendering a
prompt leaves no trace anywhere — board, journal, events — so without this call
a delegated task is byte-for-byte indistinguishable from one nobody has
touched. `triage` asks "Owner is an agent but no recent delegation prompt in
chat?", and chat is not a surface any tool can read: the check was written
against evidence that only ever existed in a scrollback. One tool call moves it
onto state that `perry-state` and a front-end can both see.

It stays `in_progress` rather than `review` on purpose — the work has been
handed out, not handed back. `review` is where `dispatch` puts a row when a
result has actually arrived.

## Render from the role card

```
"$PERRY_HOME/bin/perry-state" --section roles
```

One read gives the whole roster and everything the prompt needs. `declared: 0`
→ skip this section entirely and go to § Roleless projects.

If `<role>` names no card, **stop and say so** — list `cards[].name` and ask
which. Improvising a prompt for a role the project never declared is how the
hardcoded list got written in the first place.

For the matching card:

| Block | Goes into the prompt as | Kind |
|---|---|---|
| `context` | verbatim, under "Who you are" | advisory — it shapes behaviour |
| `may_touch` | verbatim, under "Scope" | advisory — it shapes behaviour |
| `knowledge` | § Knowledge injection below | advisory, but stale flags are not |
| `must_escalate` | § Escalation below | **hard** — this is the enforcement |
| `accepted_by`, `default_rung` | stated in the prompt, and enforced at close | gate |

`context` and `may_touch` are copied, not summarized. They are short by
schema (`Context` is 3–6 lines) precisely so that pasting them costs nothing;
paraphrasing them is how a boundary loses its edges one delegation at a time.

`accepted_by` and `default_rung` feed the close-task gate the way a mode's
default rung does (DESIGN-003 § 5.3). **The stricter of the mode's rung and the
role's rung wins** — a `pipeline` track that closes at V3 does not lower a role
that asks for V5, and a role that asks for V2 does not lower a track that asks
for V4. State the resulting floor in the prompt so the receiving agent knows
what its output will be judged against.

## Knowledge injection (DESIGN-006 § 5.4)

Inject every card the role subscribes to — `cards[].knowledge`, already
resolved from `loads.knowledge` topics — and nothing else. Subscription, not
volume: a role that loads `reporting` gets `knowledge/reporting/`, not the whole
store.

**A stale card is injected with its flag visible.** `stale: true` → head the
injected card with `⚠ unverified since <last_verified> (<age_days>d)`, and
append its `invalidated_by` tripwire. The three ways to handle a stale card are
not equivalent:

- dropping it → the agent works without a claim the project believes, and
  re-derives it, badly;
- injecting it unmarked → the agent works from a claim nobody has checked this
  quarter and cannot tell;
- injecting it flagged → the agent knows what it is standing on.

Only the third is honest, and it is the only one that lets the agent report back
"this card is wrong now", which is how the card gets fixed.

`missing_topic: true` → say so in one line ("the role subscribes to `<topic>`;
this project has no such topic yet"). A subscription that silently resolves to
nothing makes a role look better-briefed than it is.

## Escalation — the union, and it only ever grows

```
"$PERRY_HOME/bin/perry-state" --section project     # → .escalation
```

`escalation.project` is the project's own high-stakes list from
`.perry/hook.md`. `escalation.roles` is what each card adds. `escalation.union`
is what the dispatch pre-flight actually scans against, and it is the two
**added together**.

> **A role's `Must escalate` list is added to the project's list, never
> substituted for it.** Reversed, hiring a role would quietly narrow what the
> project refuses to do unsupervised — the opposite of what a role is for, and
> invisible, because a narrowed scan still passes everything it is asked. There
> is no mechanism by which a role grants itself anything the hook forbids
> (DESIGN-006 goal 6).

Copy the union into the prompt's safety-constraints block, and state the
escalation rule in the imperative: *stop and ask before doing any of these.*

Only **backticked spans** extract. An escalation line written as prose reads
like a rule and contributes nothing to the scan — **on either side of the
union, and both are reported**:

| Where the line is | Reported as | Payload key |
|---|---|---|
| a role card's `## Must escalate` | `role-escalation-not-extractable`, `perry-lint --knowledge` | `roles.cards[].must_escalate.unextractable` |
| `.perry/hook.md § High-stakes operations` | `hook-escalation-not-extractable`, **`perry-lint` with no flag**, and a standup warning | `hook.high_stakes_unextractable` |

Both carry the offending lines so this prompt can say the line is unenforced
rather than present it as a constraint. The hook half needs no flag because
every project has a hook and role cards are optional (goal 7) — and because
`hook.high_stakes_armed` only says the section has bullets, not that the
bullets arm anything (TASK-202).

## Required fields in the rendered prompt

- Task ID and Objective/KR linkage
- Exact deliverable + verification criteria
- Files in scope / out of scope
- Required commands or tests
- Safety constraints — the escalation union above, plus anything else the
  project's `.perry/hook.md` states
- Expected response format (file diff list + test output + 1-line summary, OR the RESULT block format from `dispatch.md`)
- **Git expectation** — see `git-boundaries.md`. For agents that produce commits, state explicitly: branch name pattern, push expectation, PR open expectation, and that the PR link must appear in the RESULT block.

## Roleless projects — the unchanged path

`declared: 0` (no `.perry/roles/`, or an empty one) is not an error and is not a
prompt to declare one. Skip the role sections entirely; the prompt is rendered
from the task and the hook exactly as it was before this layer existed, and the
pre-flight scans `escalation.union`, which with no roles *is* the hook's list.

The two blocks below are that path. They are what `packs/software-ops/roles/`
copied into `coding.md` and `research.md` when the hardcoding was closed — kept
here because a project with no cards still needs them, not because they name
agent types the system knows about.

### For code-changing work, always require

- Relevant tests before/after the change.
- No unrelated refactors.
- Clear list of changed files.
- **Commit code + tests on a feature branch** named `coding/<task-id>-<slug>` (do NOT commit directly to main).
- **Push the branch and open a PR**; provide PR URL in the RESULT block.
- **Do NOT merge own PR**; merge belongs to the user or a reviewing agent.
- If push or PR fails (auth, permissions, network), the RESULT block MUST say so explicitly so PMO can escalate.

### For research work, always require

Hypothesis / data period / universe / method / metrics / risk + failure modes / recommendation classified per the project's promotion ladder (e.g., `watch | dry-run | paper | reject`, or whatever stages the project defines in its hook).

## Role ≠ executor

The executor enum is `claude-subagent | opencode-subagent | codex | manual`.
`delegate` is the `manual` path and only renders a prompt; it does not bypass
the automated host matrix. If that prompt is later switched to dispatch,
Claude Code permits `claude-subagent`, OpenCode permits `opencode-subagent`,
Codex CLI permits neither native token, and every host permits `codex`.

`<role>` is the contract; the executor is what instantiates it. One role runs on
`claude-subagent`, `opencode-subagent`, or `codex` with no edit to its card, and
`bin/perry-dispatch-limit` counts executors, not roles — a project with four
roles and two codex slots has two slots, not eight. A card's `executors` field
may restrict which runtimes are acceptable (`any` by default); it never grants
one a slot.
