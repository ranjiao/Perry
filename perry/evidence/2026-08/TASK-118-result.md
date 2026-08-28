# TASK-118 — the three minters were right and their docstrings were not

**From `coding/task-118` @ `af68614`.** Rung **V3**. `bin/perry-task` +94/−33
and `tests/test_register_minters.py` (298 lines). **`perry/` and
`.perry/events.jsonl` byte-identical**, verified.

## My spec's central claim was wrong

I wrote that three minters *"mint from a rendered projection"* while the store
is canonical. **They do not, because there is nothing for those registers to be
a projection of.**

`## User Input Queue`, `## Cadence` and `## Top risks` are **projections of
nothing** — no store exists for any of them. The `USER-` ids that appear in
`perry/tasks.jsonl` are **references a task makes** (`TASK-114 depends_on:
["USER-015"]`), not rows. Reading the board for those registers is reading their
canonical form.

What ADR-007 actually asks of a minter is `minting_records`' **shape**: *the
register's canonical form, plus the ids that have left it.* **All four minters
already had that shape.** Three of them *described* it wrongly, citing a
function that changed underneath them.

So no source changed and no id moved — renumbering was never on the table, which
is the opposite of what my spec implied. What changed is that **the shape is now
named once and implemented once**: `minting_text` sits directly beside
`minting_records` so the correspondence is physically visible, and
`mint_register_id` does the numbering.

Three minters were **six byte-identical lines** each. They are now one call.

## The latent bug, found by grepping the expression rather than the name

All three read `e.get("id", "")`. For a log line holding `"id": null` that
returns **`None`**, and `re.findall(pattern, None)` raises **`TypeError`** — not
a `Refused`. **It kills `ask`, `cadence-add` and `risk-add` together.**

`read_events` deliberately keeps whatever JSON a line held. `minting_records`
and `perry-goals § mint_commitment_id` both guard this. **These three did not.**

**I checked whether this is latent or live**: 828 events on this repository, **0
with `id` null and 0 with the key absent.** Latent. Reproduced by the agent
before the fix; mutation M5 restores the old expression and three tests go red.

This is the fifth time in two days that grepping the *expression* rather than
the function name found something a name-grep missed.

## My spec's table was one call site short — again

`mint_risk_id` has **two** callers, not one:

```
4446  ensure_risk_table   — risk-migrate allocating a block of ids
4595  cmd_risk_add
```

Both are now covered. **That is the sixth spec of mine in two days to locate a
call site once where there were two or three.** It is no longer a coincidence
and it belongs in how I write specs, not in a list of apologies.

## Purge safety: safe, and for two of the three it was inherited rather than chosen

`purge` is a task-store path and does not reach these registers. Their rows leave
when a human deletes a line, and the `ask` / `cadence-add` / `risk-add` that
minted the id survives in **two** independent records — the append-only log *and*
the journal line `commit()` writes. So nothing here is load-bearing on the log
alone, which matters because this module's own docstring calls that log
*"derived and disposable"*.

**But the provenance differs, and the agent said so rather than reporting a
uniform pass:**

- `mint_risk_id`'s docstring **named the pruning case** — `RX-` was deliberate.
- `mint_user_id` and `mint_cadence_id` said only *"like `mint_id`"* — they had
  the property **by inheritance from a sentence that was false.**

**The one genuinely unsafe case**, now asserted rather than left to be found: an
id hand-written onto the board and never routed through the tool. Nothing else
ever held it, so deleting that row does free the number. **Irreducible without a
store.**

`mint_risk_id`'s docstring now says what it should read the day `risks.jsonl`
exists — the store plus what left it, a one-element swap in `minting_text`.

## Mutation proof: 15 of 15

8 shared mutations — board dropped, log dropped, journal dropped, journal widened
to the whole state root, null-guard removed, reissue-the-highest, `default=-1`,
padding dropped — plus family-specific ones. Per minter: **`USER-` 10/10, `CAD-`
10/10, `RX-` 11/11**, the extra being `ensure_risk_table` allocating from a
literal instead of the minter.

## `bin/perry-decide` is the same defect one file over, and worse

Measured, not changed — it was out of scope and stayed out.

```python
bin/perry-decide:242   """Next ADR number from max(files ∪ index).
    Both, for the reason `perry-task.mint_id` learned the hard way …"""
```

**It cites the same function my spec cited, and it too has been wrong since
ADR-007.** Two things make it worse than the three above, and I confirmed both:

1. Its second source is `DECISIONS.md`, which **`render_index` rebuilds from the
   ADR files on every write** — so the "departed" half **erases itself**. Two
   sources that collapse to one. Measured in a temp project: delete the highest
   ADR file, run any status flip, and the next `new` is handed **`ADR-003`
   back**.
2. **`perry-decide` reads `.perry/events.jsonl` zero times** (confirmed:
   `grep -c` → 0). The three `perry-task` minters were saved by the log; this one
   has no such accident to fall back on.

Also measured and left alone: `perry-goals § mint_commitment_id` — same shape,
**honest docstring** naming the hand-delete case, already guards a null id via
`(cid or "")`. And `perry-migrate § id_minter` seeds `SRC-` from every `.md`
under the state root — a different register and a different question, noted as
the contrast for why the three read `journal/` rather than the whole tree.

## Numbers, computed against both revisions

Next ids on the live project, loaded against the real board, log and journal:
**`USER-904`, `CAD-001`, `RX-005` — identical before and after**, matched through
the CLI with `--dry-run`. I re-ran `perry-task ask --dry-run` myself: `USER-904`.
`USER-903`, `RX-004` and `USER-016` all still resolve through `perry-explain`.

**Perry's own board has no `CAD-` rows at all**, so "the highest live `CAD-`" —
which my spec asked it to preserve — is none. It said so instead of inventing a
number.

`perry-lint`: **0 errors, 3 warnings, 173 records, 0 rows drifted**, before and
after. It also noted that `--root perry` reports 4 warnings because the log lives
at the repo root — a difference in invocation, not in state.

Suite: **86 modules, 2572 tests**, one red — `test_diagnose`, the standing one.
