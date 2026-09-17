# PMO decisions and risk

## Decisions & risk

### ~~`decide <topic>`~~ — moved to the `decide` lane

ADR recording left this lane on 2026-08-16, when the signed hand-off contract
(`$PERRY_HOME/SKILL.md § The hand-off contract`) gave `decisions/` to
`decide`. It is now **`/perry decide adr <topic>`**, with the
same `--supersede` / `--expire` / `--archive` lifecycle, and the full procedure
lives at `$PERRY_HOME/decide/reference/decisions.md`.

**`work` no longer writes `decisions/` at all.** If a request
lands here that would, route it — do not write and mention it afterwards. That
is the refusal case the contract names.

The migration for a pre-Perry project that keeps all its ADRs in one file moved with it.

### `risk`

**Raising a risk and clearing one both go through the tool.**

```bash
"$PERRY_HOME/bin/perry-task" risk-add --actor <actor>   --title "<the risk, in your words>" [--opened YYYY-MM-DD]
"$PERRY_HOME/bin/perry-task" risk-clear <RX-ID> --actor <actor> --reason "<why it is over>"
"$PERRY_HOME/bin/perry-task" risk-migrate --actor <actor>            # bullets → the table, once
```

`## Top risks`, as `perry-tasks board` prints it from `risks.jsonl`, is a table
— `| ID | Risk | Opened | Status |` — and the
rule is the one `## Intake` and `## User Input Queue` already follow: **the tool
owns the row and every computed cell; the agent owns the prose cell.** `risk-add`
mints the `RX-NNN`, stamps `Opened`, and writes the record, the journal line
and the event together. `Risk` is your sentence and nothing rewrites it.

Do not hand-write a row and do not retire a risk by striking it through. That
was the old shape and it had two defects nothing could fix from the outside: a
`~~struck-through~~` risk is decoration, not a field, so it stayed in every
count forever — one on Perry's own board survived a day past being cleared —
and with no id column the reader split the first sentence on whitespace and
published `id: "Perry"`, `title: "is half-adopted: …"`.

**A cleared risk stays on the board.** `risk-clear` writes
`cleared <date> — <reason>` into `Status` and the row remains: it is the record
that the mitigation worked. It simply stops counting.

**The section is a projection of a record store** (TASK-040, ADR-007 applied to
this register the way it had been applied to `BOARD.md`, the file TASK-237 later deleted). `bin/perry_store.py` holds
the record shape — `id`, `risk`, `opened`, `cleared`, `status`, `order` — and
renders it back through the same functions the task store uses, so the two
cannot drift into two renderers.

```bash
"$PERRY_HOME/bin/perry-tasks" risks-build   # derive the records; write nothing
"$PERRY_HOME/bin/perry-tasks" risks-diff    # render them back and byte-compare
"$PERRY_HOME/bin/perry-tasks" risks-write --from-board   # the ONE-WAY import
```

`cleared` is the field the four columns could not hold: the day a risk stopped
being live rides inside the `Status` cell's prose, so the record carries it
typed and the cell keeps rendering it as prose — the same arrangement a task's
`summary` has, stored with no column of its own. **A risk with neither date
carries neither**; `""` is the honest answer for a risk raised before the
register existed or retired without a day recorded, and today's date would be
a claim about the project's history that nothing in its files supports.

`perry-lint` reports a hand edit to the section as `risk-store-drift`, at
`warn` — the severity `store-drift` uses for a `BOARD.md` a project still holds, and for the same
reason: the store is authoritative, so drift never changes what a risk is, and
`perry-tasks risks-render --write` restores the projection. The check is silent
and says so when there is no `risks.jsonl`: *no store* and *clean* are
different answers.

**`risks-write --from-board` is the one-way import**, the same act
`perry-tasks write --from-board` performs for tasks and `perry-okr write
--from-file` for `OKR.md`: it mints `risks.jsonl` for a project that has none,
is run once at adoption, and is never the direction a drifted section wants —
that is `risks-render --write`. `--from-board` is required, because the flag
is the consent and there is no other behaviour.

It refuses, writing nothing, on four conditions, and each one names itself:
`risks.jsonl` is not declared in `schema/state-schema.json § claims` (the
declaration is the user's to give, and the command reads the schema at every
call rather than assuming it); `## Top risks` is absent, a bullet list, or a
table this tool must not treat as the register; the records it derived do not
render the section back **byte for byte**, in which case the refusal names the
row and the column rather than a line number; or the store it would write is
one `validate_risk_records` could not read back. **The import appends no
event** — it raises no risk and retires none, and an event stamped today for a
row that may be nine months old is the same falsehood `opened: ""` refuses.

`cleared` is carried across from the store on disk, because it is the one
stored field the four columns cannot express: the board has nothing to say
about it, so `--from-board` cannot be read as saying `""`. Every field the
section *can* express comes from the section, and anything that replaces is
printed rather than swallowed.

**`perry-state` counts open risks only**, with `age_days` computed from
`Opened` at read time — the same rule as `Asked`/`Idle` on the User Input
Queue, and for the same reason. The cleared ones sit in `risks.cleared_items`,
never in `risks.items`: a risk that is over is not a top risk, but `cleared`
was a bare integer, so the one field a cleared risk exists to carry — the day
it ended — was emitted by nothing. `risks.source` is one of four values —
`table`, `bullets`, `mixed`, `none` — saying which form the payload was read
from; on a bullet the `id` is invented and `age_days` is `null`, and a reader
is entitled to know which it got. `mixed` means the rows came from more than
one form, which now only happens on a board that has not migrated: **once
`## Top risks` is a table on a held board, or `risks.jsonl` exists, that register
is the one read and `PROJECT_STATE.md` is no longer merged into it.** Before the table existed both
files held bullets and both ids were invented out of the prose, so a risk
written into both collapsed by accident — the invented ids were the first word
of each sentence. Minted ids can never collide with invented ones, so the merge
would double-report every shared risk, once open and once cleared. Migrating is
the project saying where its risks live, and it is read as exactly that — so a
project that kept a second list in `PROJECT_STATE.md` should `risk-add` the
still-live ones onto the board, because after migrating they stop being
counted. Measured on one real project: the merged count went 13 → 9. Four
`PROJECT_STATE.md` entries left it, three of them already marked closed there
and one still live — that one is the `risk-add` the migration asks for. The
alternative, on the same board, was 15: every shared risk counted twice, one
of them reported open and cleared at once.

**An older board keeps working, and is never converted behind your back.** A
bullet list is still read, and `risk-add` on one **refuses**: it says how many
bullets it would have to rewrite and prints `perry-task risk-migrate`, which is
the command that does it (`--dry-run --json` first shows every row it would
write). "No automatic rewrite of a project's existing structure. Adoption
proposes; the user declares" is an Anti-Goal, and a section of hand-written
risks is exactly the kind of structure it protects.

The conversion carries every bullet across **verbatim** into its own row with
`Opened` left empty — the date a pre-existing risk was raised is not recorded
anywhere and stamping today would assert it is new. A bullet the reader already
treated as resolved (`~~strike~~` or `**RESOLVED`) migrates as `cleared`, with
whatever date the human wrote in it. A placeholder (`- (no active risks)`) is
not a risk and is not migrated; a section holding only one is not asked about,
because there is nothing of yours to protect. A table under this heading with
no `Risk` column — a legend, a severity key — is refused by both commands
rather than written into: the reader reads that section's bullets, and adding
the risk columns to a legend would make it stop.

There is deliberately **no `Severity` column**: both real projects surveyed
write severity inside the sentence (`H · …`, `🔴 …`), so it stays derived from
the statement rather than becoming a column nothing on a real board fills.

**Triage has no risk step.** This section used to claim it did — "triage still
asks, for each open risk: still valid? severity changed? mitigation in place?"
— and the `planning.md § triage` procedure has never contained the word *risk*. What
exists instead is the payload: `perry-state` reports the open rows with
`age_days`, so a risk open ninety days and untouched is visible without a
procedure asking about it. Retiring one is `risk-clear`; changing what it says
is a rewrite of the `Risk` cell, which is yours. If a triage step is ever
written, note that the schema has nowhere to record "mitigation in place" —
`Status` is a binary plus a closing reason — so it would need a column first.

### `nudge`
For every User Input Queue item idle ≥5 days, surface a one-line reminder in chat with: USER-id, what's needed, what it blocks, days idle, original ask context.

After completed writes, follow `subcommands.md § Completion routing`.
