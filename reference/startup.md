# Startup routing — the cases behind the route table

Tier 2. Read when the route is unclear, or to check a case. The procedure is
`SKILL.md § Mandatory first move: combined snapshot`: the route table and
steps −2 to 3. This page restates none of it. It says what counts as project
state, why each route reads what it reads, when a result must be read again,
and the eight cases the table was accepted against (TASK-469).

## What counts as a project-state read

Any read under the project: the state root, `.perry/` (the config store,
dossiers, events, roles), `AGENTS.md`, the code. Any `perry-state`,
`perry-task`, `perry-tasks`, `perry-explain` or `perry-lint --root .` call.

Not project state: Perry's own shipped pages under `$PERRY_HOME` and
`perry-detect-host`, which reads the environment. `perry-update-check` reads
neither, but it can fetch, so only the Change route runs it.

Step 1 reads `.perry/config.jsonl` before the recovery gate. That order
predates routing and is kept: the config store is not recovered by the task
command, and the chat language must be known before the gate reports.

## Explain — why it reads nothing of the project

A question about Perry is answered from Perry's pages: the router, a lane's
subcommand index and `help`, a `reference/` page. The project cannot change
the answer, so reading it only costs context and risks answering a different
question ("how does triage work" is not "what needs triage"). Reply in the
user's language; the config store is not read for it.

A lane's `help` is this route: load that lane's `SKILL.md` for its index and
the one reference its row names. It never runs the lane's snapshot. Rows that
depend on an optional pack are shown marked as needing that pack, not
filtered: finding out whether it is active would mean reading the config
store.

An explanation writes nothing, not even a hook, a config default or a
closing-step record.

## Query — one projection, after the gates

The gates exist because a projection read over a pending transaction or a
malformed dossier reports a state that is about to change or is wrong. So a
query runs step 2 in full before its one read:

- `blocking: true` → stop and report every path and error. The question goes
  unanswered, and nothing else of the project is read, not even a listing.
- an interrupted run → render its card and ask, exactly as step 2 says. Never
  resume. Answer the question only after the user's choice, and only if that
  choice leaves the question standing.

Then read only what the question needs: `--section <name>` for one top-level
key, `perry-explain <ID>` for one id, `perry-task list --json` for task rows.
Nothing of these runs before step 2, not even to check that the question can
be answered. The one extra read allowed is `perry-explain <ID>` for an id the
answer names without its title (`SKILL.md § Style rules`). No dashboard, no
mode file, no `next` block, no second read to "add context".

`installed: false` means this folder has no Perry state. Say so and offer
`/perry`. First-time setup writes the config store, so a query never starts
it.

## Change — every gate, then the owner

Steps −2 to 3 run as written, including First-time setup on
`installed: false`. Bare `/perry`, or asking for the overview, continues to
step 6 and renders the snapshot unchanged.

A lane or router subcommand continues with its own procedure instead. The
lane skips its steps −3 to −1, which the router just ran, and keeps the rest:
its config and hook reads, its own state read, the ownership table, the
hook's high-stakes list, evidence and verification rules. Nothing the lane
gates on is lifted because the router ran first.

## Why three router sentences are worded the way they are

Each replaced a sentence a V4 round proved false or unreachable (TASK-469
round 1 FAIL, `perry/evidence/2026-09/TASK-469-v4-review.md`).

- **"except step 1's `.perry/config.jsonl`"** (route table). The router used
  to assert "Nothing reads state before step 2" as an absolute, eight lines
  above the step that reads the config store. This page's own definition of a
  project-state read includes it, so the tier-0 absolute was false by the
  tier-2 definition shipped beside it, and only a reader who opened this page
  found out (D2).
- **"on a Change route only"** (step 1). First-time setup writes. A Query that
  started it would turn a question into a mutation, ahead of the recovery gate.
  The rule was written here and not there, so the route that needed it never
  saw it (D2).
- **"not even a listing"** (step 2). This clause lived only on this page. The
  blocking path never opens this page, so the one agent that obeyed it had
  never read it — its round-2 trace lists no read of this file (D3).

The pattern in all three: **a correction is only a correction where the
behaviour is driven.** A rule on this page governs a reader who came here, and
the failing routes are precisely the ones that do not.

## The pack rule is scoped by route

USER-974 (2026-09-20) chose principle A: the pack-eligibility procedure never
runs on the Explain route, whatever Explain is loading, and pack-dependent
content — rows and the `packs/` pages `help <subcommand>` opens — is shown
**marked** rather than filtered, hidden or withheld. Each of those three is a
decision about which pack is active, and that decision needs the read an
ungated route may not do.

**It took two V4 rounds to get that sentence into the file that drives the
behaviour.** Round 1 wrote the correction *here*, on this page, which line 3
says is read only "when the route is unclear" — the help route is not unclear
and never opens it. Round 2 moved it into `work/SKILL.md` and scoped it to help
**rows**, leaving "before loading software-ops references" standing in the same
sentence; `work/SKILL.md § help` reaches exactly that for five pack
subcommands. The instance was fixed twice and the category outlived both.

The third round enumerated four sites instead of one: `work/SKILL.md`,
`goals/SKILL.md`, and two in `reference/config.md` — `/perry help` being sent
at a procedure whose step 1 reads the config store and the project payload, and
work help being told to *hide* inactive pack commands. The last two required
widening that row's declared scope, which is recorded in its spec rather than
done quietly.

## Once per operation, refreshed when invalidated

An operation is one request carried to its end, including its route into a
lane. Within it, a gate that ran is not run again.

- `$PERRY_HOME` and `$HOST`: once per session.
- The update check: at most once per session; it throttles itself as well.
- Recovery and interrupted-run gates: once per operation that reads state.
  They are read-only and cheap, and a new request is where another session's
  write can have landed.
- A state payload is reusable only until something moves it: a write by this
  operation (read the projection the next step needs again), a failed write,
  the user saying something changed, or a new operation. An old capture is
  never presented as current (`reference/snapshot.md § Step 4 — render the
  combined dashboard`).

## Unclear or mixed intent

Ask one question with the three routes as its options, before any state read;
detecting the host to render the prompt is allowed. A request mixing an
explanation with a write takes the Change route. Status then a write is a
Query answered first, then a Change with its own gates.

The route is the agent's reading of the request. No script classifies it:
keywords confuse "how is a task closed" with "close this task", and a
classifier's wrong answer would skip a gate silently (NN-4).

## The eight cases

| Case | Example request | Route | Reads | Never |
|---|---|---|---|---|
| Explanation | "How does Perry decide what's next?" | Explain | router, `reference/next.md` | config, state, update check, modes, dashboard |
| Help | `/perry help work` | Explain | router, `work/SKILL.md` index and `help` | the standup |
| Overview | `/perry` | Change | steps −2 to 6 | skipping a gate or the snapshot |
| Narrow status | "Is TASK-NNN blocked?" | Query | config, recovery, interrupted, one `perry-task list --json` | dashboard, `--compact`, modes, update check |
| Task mutation | "Mark TASK-NNN done" | Change | steps −2 to 3, then `work/SKILL.md` from step 0 and its subcommand's page | repeating steps −2 to −1 in the lane |
| Blocking recovery | any state route, `blocking: true` | stop | config, recovery | any further state read or write |
| Interrupted run | any state route, one run found | card, ask | config, recovery, interrupted | resuming, setup, dashboard before the answer |
| Unclear | "perry tasks?" | ask | router | any state read before the answer |
