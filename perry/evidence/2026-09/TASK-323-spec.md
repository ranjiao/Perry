# TASK-323 — spec

> Dispatch mode: auto
> Executor: claude-subagent (repository-local measurement, stdlib only, no MCP)
> Estimated cycle: large
> Subjective verification: (none) — every claim is a plant with an observed outcome
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: `P003-O1-KR2`

## Why this row exists

`TASK-067` has FAILed two V4 rounds and `perry-lint --reviews` reports
`review-rounds-exhausted`: the limit is 2, and the rule says the next step is an
ask that names the competing principles, not a third round.

That ask cannot be filed honestly today, because **the population it would ask
about has moved under it.** Checked on `main` at `5e91572`, 2026-09-03:

| Round 4's proof point | Today |
|---|---|
| `viewer/tables.py:108 naming()` has zero call sites, so every `perry-goals` refusal prints no field | **False now** — called at `bin/perry-goals:171` and `:173` |
| `bin/perry-decide` has no `UnrenderableCell` handler and writes a raw `--title` into the ADR H1 | **False now** — `bin/perry-decide:311-329` checks each flag before the write |
| `bin/perry-task` matches `exc.value` back to a flag by value, so `--title` and `--next` with the same value produce the same message, and `--owner` / `--role` / `--commitment` / `--needed` name no field at all | **Still true** — `bin/perry-task:7431` is `_v.strip() == exc.value` |

The row's own `Next action` says the same thing in its own words — *"SCOPE HAS
DECAYED — re-derive it before starting"* — and lists two more premises that have
since become false (`perry-decide` no longer writes `DECISIONS.md`;
`bin/perry-migrate` was deleted 2026-08-31).

Both failed rounds also carry `criteria-unbounded`:
`evidence/2026-08/TASK-067-finding.md` has no `## Bound`, so the round has no
finite set to check and no last element. **That is the same defect twice**: an
unbounded criterion is why each round found a different member of the population
and why neither round could be the last one.

`TASK-094` and `TASK-095` are both `done`, so `TASK-067` is not blocked. What it
lacks is a measured population.

## Files in scope

- `perry/evidence/2026-08/TASK-067-finding.md` — gains a `## Bound` and the census table. This is the criteria file both failed rounds scored against; it is the artifact this row produces.
- `viewer/tables.py` — read only. `split_row`, `render_row`, `check_cell`, `append_cell`, `splice_cell`, `naming` are the choke-point candidates; enumerate them, do not change them.
- `bin/` — read only. Every tool that builds or rewrites a table row: `perry-task`, `perry-tasks`, `perry-goals`, `perry-decide`, `perry-knowledge`, `perry-conform`, `perry-lint`, and the bash tools.
- `tests/` — read only, to record which census rows already have a guard and which have none.

## Deliverable

A revised `perry/evidence/2026-08/TASK-067-finding.md` carrying two new things.

**1 · `## Bound`** — an enumerated set with a stated last element, so a future
round can say it finished rather than say it ran out of time. State the rule
that generates the set, then list its members. A member is a
**file:line call site**, not a file and not a concept.

**2 · `## Census`** — one table, measured on the HEAD you are given, with a row
for each of:

- every path that can put a value into a table cell without that value being
  checked first, and
- every path that splits a table row without going through
  `viewer/tables.py § split_row`.

Columns: `file:line` · `direction` (write / read) · `what it does` · `verdict`
(caught / uncaught) · `by what` (the check or guard that catches it, or `—`).

**Report the shapes that stay green.** Round 4 found seven plant shapes that
nothing catches — writer-side `" | ".join`, `%`, `.format`, `+`-concat, and
reader-side `.split("|", 6)`, `re.split(r"\|", …)`, a `SEP` constant. Re-measure
each on today's HEAD and put it in the census with its current verdict. A shape
that has since acquired a guard is as much a finding as one that has not.

## Bound

Added by the PMO **after delivery and before the review round**, and said
plainly rather than dated quietly: this spec went out without one, which is the
defect the row itself is about. It is a description of what was delivered, not
a bar moved to fit it — every number below is read off the delivered artifact,
and the round's job is to disagree with them.

```
Enumeration: python3 perry/evidence/2026-09/TASK-323-bound.py
Size:        89 members — 27 W1 · 18 W2 · 38 R1 · 6 R2
             last element viewer/tables.py:280
             (re-derived by the PMO on c7627cd, matching the report)
Census:      20 rows — 12 caught, 8 uncaught
             (was written "21 rows — 13 caught, 8 uncaught": the PMO copied
             that figure out of the delivering agent's RESULT block and never
             counted the table. Corrected 2026-09-03 after the V4 round parsed
             it. Counting the delivered table: 20 data rows, 12 `caught`.
             A criteria file carrying a false number is the defect this row
             is about, in the file that decides its own PASS.)
Shapes:      13 rows — 4 red controls, 9 green
Remainder:   the 5 bash tools contribute 0 members and were checked for
             `cut -d'|'`, `awk -F'|'`, `IFS='|'` and row-shaped `echo`;
             8 nodes dropped by the three exclusion clauses E1/E2/E3
```

**The round judges the census, not the fix.** Whether either reading is the
right one is a user decision this row exists to inform, and a verdict that
picks one is out of the bound. A 90th member found by the round is a new row.

## Verification

Each census row is a claim, and each claim is a plant with an observed outcome.
Nothing in this row is established by reading.

1. For every row marked **uncaught**: plant that exact shape, run the write, and
   show the table row lands corrupt **while `perry-lint --root .` reports
   clean**. Quote both — the corrupt row and the clean verdict. An uncaught row
   with no such demonstration is not a census row; drop it or move it to caught.
2. For every row marked **caught**: plant the same shape and show the refusal,
   naming which check fired and at which line. A refusal you cannot attribute to
   a named check is an uncaught row that happened to fail for another reason.
3. Verify the `## Bound` is closed: state the rule that generates the set, then
   show that applying the rule mechanically over the tree returns exactly the
   listed members and nothing else. If the rule returns more than you listed,
   the list is wrong; if it cannot be run, the bound is not a bound.
4. **Every plant happens on a `git archive` copy in your own scratch
   directory.** The live tree is never written to. Show `git status --porcelain`
   empty at the end, and show the tree byte-identical — this project has been
   bitten twice by an agent writing into the shared checkout, filed as
   `TASK-285`.

## Out of scope

- Fixing anything at all. This row measures. `TASK-067` is the fix, and which
  principle it is fixed under is a decision for the user that this census exists
  to inform. Do not choose it and do not write code that presumes a choice.
- The `bin/perry-task:7431` flag-naming defect. It is real and it survives; put
  it in the census as an uncaught row and file nothing further on it here.
- Any project other than this one. Every measurement is on this repository.

## Notes for whoever runs this

Two readings are already visible in the record, and the census exists so the
user can choose between them against numbers rather than against a recollection.
**Do not pick one.** Name which census rows each reading would have to cover:

- **(A) every write path must refuse an unrenderable cell.** The population is
  all writers. It has no last element, which is why the criteria file has no
  `## Bound` and why both rounds failed on a member the previous round did not
  reach.
- **(B) one choke point plus one detector.** Exactly one function may render a
  value into a row; the guard becomes *nothing outside it builds a row* — a
  one-symbol surface — and `perry-lint`'s `ragged-row` is the backstop. This is
  the shape the user has already chosen twice on rows that failed this same way:
  `USER-904` (option C, `header_index`, after seven rounds) and `USER-906`
  (option B, the shrink invariant, after three).

Your checkout is a worktree branched from `main` at `5e91572`. Everything cited
above resolves there.
