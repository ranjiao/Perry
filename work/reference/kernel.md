# Work lane kernel contract

Use the shipped `bin/perry describe` declaration for exact inputs. Check
`surface` major support before using a response. Every response has `ok`, `surface`,
`command`, `effect`, `events`, `store_seq`, `warnings` and a result or error. A nonzero
exit, `ok: false`, refusal or stale expectation is never an empty list or success.

## Invocation and scope

Use the actual skill root as `PERRY_HOME`. Every state call names an absolute
project root. `--input @/absolute/file.json` reads a UTF-8 file containing one JSON object.
Inline JSON and `--input -` (stdin) are also supported. Keep that
file outside the checkout, in the project-specific scratch directory described in
`dispatch.md`. Quote paths; never interpolate user prose into a shell command.

```bash
"$PERRY_HOME/bin/perry" query --root /absolute/project --input @/absolute/scratch/query.json
"$PERRY_HOME/bin/perry" item move --root /absolute/project --input @/absolute/scratch/move.json
```

The examples below show JSON input bodies, not shell strings to evaluate. Replace
placeholder IDs and actor/session values with the actual read values. An agent actor
is `{"kind":"agent","name":"<role>","session":"<actual session id>"}`.
A human actor may only represent an actual human action authorized in the session.
Use `expect: {"<ID>": <last read seq>}` on mutations of existing items. If stale,
re-read and reconcile the concurrent change; do not retry with a fabricated seq.

## Read current state

```json
{"type":"task","terminal":false,"count_by":["state","priority"],"limit":50}
```

`result.total` and `counts` are computed by the kernel. `result.items` may be
truncated. Follow `next_after` with `after` until `truncated` is false when a
procedure needs every item. Read asks with `{"type":"ask","terminal":false}`
and risks with `{"type":"risk","terminal":false}`. Read one item using
`item get` with `{"id":"<ID>"}`. `startable` and `blocked_by` are derived by the
kernel. Do not translate an unknown relation into a satisfied dependency.

Use `events` with `{"items":["<ID>"],"limit":50}` for one item's history; its
`total`, `truncated` and cursor are part of the answer. Export checkpoints and
source timestamps do not substitute for event times. Recent events are evidence
of writes, not evidence that another process is still running.

## Create, update and move

Task creation (`item create`):

```json
{"actor":{"kind":"agent","name":"<role>","session":"<actual session id>"},"type":"task","fields":{"title":"<human title>","summary":"<problem and deliverable>","priority":"P1","owner":"Coding Agent","track":"main","verification":"V3","next_action":"<one concrete action>"}}
```

The kernel mints the ID; never reserve one by editing a file. When a new spec
needs the minted ID, obtain user agreement first, create the item, write the spec
under that ID, then `attach add`. Do not create a guessed attachment ID.

`item update` takes `id`, `set`, optional `unset`, actor and `expect`. It changes
fields, not state. A state change uses `item move` with `transition` and any fields
required by that transition. Both changes land in one transaction/event.

| Destination | Transition | Required skill check / fields |
|---|---|---|
| in_progress | start | Inspect dependencies and criteria; record next_action |
| blocked | block | reason names the unresolved input/dependency |
| review | submit | Deliverable, tests and architecture checkpoints recorded |
| not_started | reset | Explain why work is returned |
| done | done | evidence; V4 also verified_by; V5 actual human actor |
| dropped | drop | reason records the authorized scope decision |

Each transition's allowed source states come from `template show`. Terminal items
cannot silently be reopened. If an operation is unsupported, explain the limit;
do not bypass the template by editing the store or applying an ad hoc template.

## Relations and documents

`rel add` / `rel remove` take `kind`, `from`, `to`, actor and optional `expect`.
A blocker A of B is `{"kind":"blocks","from":"<A>","to":"<B>"}`. For
`parent`, `from` is the child and `to` the parent. Query current edges before
replacing dependencies; do not drop another session's new edge.

`attach add` / `attach remove` take `id`, `ref`, actor, optional `hash` and
`expect`. Preserve the original ref exactly, resolving it against the documented
state root when the host opens it. A `sha256:` hash pins bytes; the kernel never
opens the document or checks its semantics. Keep the task's `evidence` field as
a authored text reference; never split legacy evidence into attachments by regex.

## Asks and risks

Create an ask with type `ask` and fields `question`. Answer it by `item move`,
transition `answer`, setting the actual `answer`. An ask blocking a task gets a
`blocks` edge. Never record an agent's recommendation as the user's answer.
Create a risk with type `risk` and fields `concern`; clear it with transition
`clear` and a reason. Do not create parallel registers for either concept.

## Export, setup and cutover

`export` takes no input object and writes the store's deterministic JSONL projection in
the recorded state root. Read `events.unexported` to see lag; do not edit exports.
The export is a recovery artifact, not a second current-state store.

For a genuinely new project only, obtain the bootstrap agreement, then `init`
with actor and `state_root`, and `template apply` with actor and the parsed shipped
`templates/process/perry.json` object. Do not initialize over missing migration
state. For an existing project, follow the reviewed import reconciliation and
switch plan; the importer creates a rehearsal store, not a live cutover.
All rehearsal commands name both an isolated `--store` and its `--root`. Verify
counts, IDs, references and ceiling reconciliation for each affected project.
Do not copy a rehearsal SQLite file into the live location: use validated export
and kernel `import` at the actual project root after the user's switch approval.
