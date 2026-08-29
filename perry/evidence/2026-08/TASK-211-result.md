# TASK-211 — result: the dispatch limiter says what it cannot know

> Branch `coding/2026-08-29-overnight-batch`, commit `835555d`. Rung **V3**.
> Measured 2026-08-29.

The row folded two intake findings into one, correctly: they are one tool
failing to tell its caller what it does not know.

## Half one — already fixed, and pinned rather than deleted

Filed as *"an unknown subcommand exits 0, so a typo silently disables the
concurrency cap"*. The row's own Verification names the check: *calling
`acquire`, which is not a subcommand, fails loudly.*

Re-measured before writing anything:

```
$ bash bin/perry-dispatch-limit acquire ; echo "exit=$?"
Unknown command: acquire
perry-dispatch-limit — track concurrent /perry work dispatch slots.
exit=2
```

**Already true.** The `*)` branch exits 2 and prints the usage. The row's
premise was stale. It is pinned by a test rather than struck out: an exit code
nobody asserts is one a later refactor can drop silently, and this row exists
because that exact thing happened once.

## Half two — live, and the expensive one

`list` reports marker **files** and reads as though it reports running agents.

It cannot observe. `registered_pid` is the field that looks like it would let
it, and it does not — it is the pid of `perry-dispatch-limit` **itself** at
`register` time, and that process exits within milliseconds. Measured:

```
$ bash bin/perry-dispatch-limit register TASK-999 claude-subagent
🟢 Slot reserved: TASK-999 (claude-subagent). Now 1 / 2 …
$ kill -0 49907          # the registered_pid from the marker
DEAD — the pid is the registrar's, and it exited when register returned
```

`kill -0` reports dead for **every marker ever written**, including one whose
agent is alive and working. So both failure directions are real and neither is
detectable at this layer:

| direction | what happens | seen |
|---|---|---|
| agent dies, marker stays | the slot is held until the stale sweep | 2026-08-28, an ESC killed two agents |
| marker reaped, agent lives | the cap is short by one, silently | 2026-08-21, TASK-160 |
| marker written, dispatch never made | a phantom in-flight row | 2026-08-28, 20 minutes |
| agent finished, row never closed | `list` says 0 while a row says "awaiting RESULT" | **2026-08-29, TASK-095 and TASK-209** |

Three instances in two days, every one caught by a human reading two numbers
side by side rather than by any check.

## What shipped

The deliverable offered two branches: *"list reports observation, **or** says
plainly that it reports bookkeeping and observes no process."* Observation is
not available here — the pid is not a handle and the tool never learns the
agent's — so the second branch is what ships, and it is stated every time
rather than only when something looks wrong. The caller cannot tell those
cases apart either; that is the defect.

`(no active dispatches)` gets the note too, and is the dangerous line: it reads
as *"nothing is running"* and means *"no marker file exists."* That is the
sentence misread on 2026-08-29.

**The note is on stderr**, per this file's own rule at `clean_stale`: *"`check`
and `list` have parseable stdout and a warning is not part of their answer."*
`TestStdoutStaysParseable` asserts stdout stayed exactly the listing — two
lines, no prose.

The marker itself now carries `_registered_pid_note`, so a reader who finds one
on disk without this evidence file beside it learns the same thing.

## Verification

**Shown able to go red**, three mutations, each restored byte-identical
(`md5` checked):

| mutation | result |
|---|---|
| drop the empty-listing note | 1 failure |
| move the note to stdout | 2 failures |
| unknown subcommand exits 0 again | 1 failure |

`tests/test_dispatch_limit_honesty.py` — 10 tests, each with its own `HOME`, so
the real `~/.cache/perry` is never touched.

**Suite**: 3 modules red before and after (`test_contract_key_parity` 2,
`test_diagnose` 2, `test_kr_progress_provenance` 1) — all pre-existing on
`main`. This change adds none.

## What this does NOT fix

**Nothing compares a board row claiming `dispatched` against this tool
reporting 0 in flight.** That is the check which would actually have caught all
three incidents, and it is a cross-check between two payloads — `perry-state`'s
board rows and the limiter's markers — not a property of a bash script that
knows nothing about the board. Filed to `## Intake` on 2026-08-29, where it
belongs as its own row.
