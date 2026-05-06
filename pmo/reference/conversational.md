# Conversational conventions

These shape every PMO reply in chat. Separate from what gets written to files: file artifacts always carry the canonical IDs; chat carries the meaning.

## Restate decisions in plain language

When surfacing a decision, blocker, or open question to the user in chat, **lead with the semantic meaning**, not the raw IDs. IDs go in parentheses or in the in-flight board so they remain reverse-searchable, but the user shouldn't have to decode them mid-conversation.

- ❌ Don't write: "D-3 = USER-028 + DATA-005-E needs ratification."
- ✅ Do write: "Decision D-3 — should we lock the R-5 risk threshold at 25%, and should the system auto-detect levered ETFs? (refs: USER-028, DATA-005-E)"
- ❌ Don't write: "TASK-007 blocked on USER-014."
- ✅ Do write: "Coding task to add the dashboard scope toggle is blocked — waiting on you to confirm whether the default scope is BOS-only or all-accounts (TASK-007 / USER-014)."

A user reading the chat without opening a single file should understand WHAT is being decided and WHY it matters. The IDs let them dig deeper afterward.

This rule is for chat output only. Inside `BOARD.md`, `journal/`, `evidence/`, `DECISIONS.md`, and `weekly/`, IDs and short titles are still the canonical form — those files are reference material, not conversation.

## The in-flight board (use when it helps, not by default)

A small **4–6 row table** showing what's actively moving — meant to re-anchor a long conversation without forcing the user to re-ask "where are we". PMO decides when to include it. Don't append to every reply.

### Include it when

- The reply changes board state (task added, closed, dropped, status moved, USER input resolved, design locked).
- The user asks a "where are we / what's next / 还有啥" style question.
- A standup just ran on a fresh session (the dashboard already covers this — only add the in-flight board if the standup itself didn't render a similarly-sized list).
- More than ~10 turns have passed since the last board was shown in this session.
- The reply names a specific task / USER input / design ID and the user might want adjacent context.

### Skip it when

- The reply is a focused answer to a focused question (no state change, no scope question).
- The reply is a single delegation prompt meant to be copy-pasted into another session — the board would contaminate the prompt body.
- A board was already shown earlier in the same reply (e.g., as part of a status report).
- The reply is short (<5 lines) and self-contained.

When in doubt, skip. The user can always ask `/pmo` or `/pmo status` to see the full board.

### Format (fixed when used)

```
| ID | One-line | Status |
|---|---|---|
| <TASK-ID> | <plain-language description, ≤ 80 chars> | <status> |
| <USER-id> | <plain-language description, ≤ 80 chars> | <status> |
| <DESIGN-ID> | <plain-language description, ≤ 80 chars> | <status> |
```

### Selection rules (apply in order until you have 4–6 rows)

1. All `P0` open tasks (not_started / in_progress / blocked / review).
2. All User Input Queue items idle ≥ 3 days OR blocking a P0.
3. Any `Status: locked` design doc whose Implementation plan has not yet been turned into PMO tasks.
4. The most recent `in_progress` `P1` task.
5. If still under 4 rows, fill with the next most recent activity (any priority).

If more than 6 rows qualify, keep 6 and add a footer line: `+<n> more open · run /pmo status for full list`.
