# PMO status report format

Used by `status` (a.k.a. `friday-review`), `monday-plan`, `midweek-check`. Save to `weekly/<YYYY-WW>.md` for the weekly variants.

```md
## PMO Status — YYYY-MM-DD

### Summary
- Overall status: <on_track | at_risk | off_track>
- Main progress: <one line>
- Main risk: <one line>
- User decisions needed: <count + USER-ids>
- Cost ceiling status: <spent / ceiling, % of cap>

### P0
- [TASK-ID] <status> — <evidence path or blocker> — next action

### P1
- [TASK-ID] <status> — <evidence path or blocker> — next action

### Decisions Needed
- Decision: <one line>
- Why it matters:
- Deadline:

### Next 3 Actions
1. ...
2. ...
3. ...
```
