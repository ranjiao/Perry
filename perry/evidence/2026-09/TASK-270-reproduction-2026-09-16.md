# TASK-270 — re-measured before dispatch, 2026-09-16

> By the PMO, on a copy of `tests/fixtures/sample-project`, against main at `538d94a7`.
> Why: the row was opened 2026-08-29 from TASK-095 round 3, finding 2. `bin/perry-config` no longer has a `write --from-file` subcommand — `git log -S"from-file"` shows DESIGN-016's commit `0f367ff7` removed it — so the row's trigger was re-checked before any agent was spent on it.

## What no longer holds

1. **The trigger.** `perry-config write --from-file` does not exist. Its subcommands are now `show`, `set`, `unset`, `track`, `untrack`.
2. **"Refused forever."** After the store is emptied, `perry-config set --root <p> "Document language" English` writes one record, and the next `perry-task add` succeeds.

## What still holds — reproduced

```
unset "Document language"  exit 0
unset "Repo layout"        exit 0
unset "PMO repo path"      exit 0
unset "Code repo path"     exit 0
unset "Last updated"       exit 0
.perry/config.jsonl        0 records
```

Then:

| Tool | What it says | Is it true? |
|---|---|---|
| `perry-task add` | refused: "`.perry/config.jsonl` exists but holds records that do not validate … Repair the store — `perry-lint` names the records that do not validate." | **No.** The store holds no records at all, valid or otherwise. |
| `perry-lint --root` | `config store: 0 record(s), all valid` | True, and it contradicts the writer. |
| `perry-lint --root` | `[NS-01] .perry/config.jsonl holds 1 file(s) Perry did not write` | **No.** Perry wrote it, through `perry-config unset`. |

So a user who empties the store with Perry's own command, exit 0 at every step,
is told by the writer to find invalid records that do not exist, is told by the
linter that everything is valid, and is told by the linter that Perry did not
write a file it did. The one command that recovers — `perry-config set` — is
named by none of the three messages.

## The defect as it stands

1. `perry-config unset` removes the last record without saying the store is now empty, or what that does to every writer.
2. The writers' refusal on a zero-record store names the wrong cause and the wrong recovery.
3. `perry-lint` and the writers disagree about whether a zero-record store is usable.
4. `NS-01` misreports a Perry-written empty store as foreign.
