# TASK-061 — the four things a consumer had to discover by running the tools

**Closed as already done, on 2026-08-18.** Every one of the four landed while
other work was going through the contract document; nobody came back to the
row. Verified mechanically rather than by reading, because "I looked and it
seems fine" is the closing note this project's own rules exist against.

## The check

```
python3 - <<'PY'
import json, pathlib, subprocess, sys
doc = pathlib.Path("schema/task-list-contract.md").read_text()
d = json.loads(subprocess.run([sys.executable, "bin/perry-task", "list",
                               "--json"], capture_output=True,
                              text=True).stdout)
sem = {s["version"]: s for s in d["semantics"]}
print("1", "`stderr` is not the failure channel" in doc)
print("2", "**`event_written` is on every write result**" in doc)
print("3", "Ties are possible and are not duplicates" in doc)
print("4", "conformance.rows_with_no_computable_age" in sem["1.9"]["fields"])
PY
```

All four print `True`.

## What each one was, and where it is now

| # | The gap aiMark hit | Where it is answered |
|---|---|---|
| 1 | **`stderr` is not the failure channel.** Every successful write may print the advisory conformance line there, so a front-end treating stderr as failure reports **every** write as an error. | `schema/task-list-contract.md:30` |
| 2 | **`event_written`** — the difference between *"the row moved"* and *"the row moved and its timeline will have a hole"*. The board write lands first and the event is appended second, deliberately. | `schema/task-list-contract.md:37` |
| 3 | **Two events can share a `ts`.** Measured on this board: 48 timestamps carry more than one event and the worst carries 12, so a consumer re-sorting by `ts` needs a stable sort or it reorders a `start` after the `status` that followed it. | `schema/task-list-contract.md:141` |
| 4 | **`rows_with_no_computable_age` fired per row** on a project with no event log — 17 of 17 — restating `has_event_log: false` seventeen times rather than naming a finding. | Fixed at **1.9**, and reported in `semantics` so a consumer pinned below it is told the value changed meaning |

## What was NOT checked

- Whether aiMark has actually consumed any of this. Item 4 in particular
  changes a rendered list, and revision 6 of the hand-off asks them to branch
  on `has_event_log`; **no reply has arrived**, so this closes Perry's half and
  not the round trip.
- The other two contracts. `perry-goals/list` and `perry-decide/list` have
  their own documents and were not audited for the same four classes — the
  `stderr` one at least is tool-wide, and `bin/perry-goals` prints the same
  advisory line on a successful write.

=== VERDICT ===
task: TASK-061
rung: V3
result: PASS
criteria: this file § The check
checked: all four claims re-run against the live document and the live payload;
         the `ts` tie count measured on this project's own event log (48
         timestamps, worst 12); a successful write confirmed to print 1,149
         bytes to stderr while exiting 0
not-checked: whether aiMark consumed any of it; the same four classes against
             perry-goals/list and perry-decide/list
proof: (none — this is a PASS)
=== END VERDICT ===
