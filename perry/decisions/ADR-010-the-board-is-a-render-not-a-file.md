# ADR-010 — BOARD.md stops existing; the board is what a command prints

> Status: active
> Type: Architecture
> Date: 2026-08-29
> Deciders: Ran Jiao
> Supersedes: ADR-007 § 6 decision 2 (that one sentence only)   · Superseded by: —
> Sunset: —

## Context

ADR-007 § 6 decision 2 asked *"Does `BOARD.md` stop being hand-editable?"* and
answered *"Yes — it becomes rendered output, and a hand edit becomes drift."* The
file was kept because a human reads it. That was decided 2026-08-19, and the
measurement offered before deciding was `drift: 0` on this project.

On 2026-08-29 a census of all 380 markdown files under `perry/` measured what the
kept projection is actually made of:

- **`BOARD.md` is 43,289 bytes, of which 42,099 — 97% — are inside table rows.**
  101 rows. The longest single cell is **2,825 bytes**.
- The 1,190 bytes outside the tables are a title, nine lines of header prose, and
  eight `##` section headings.
- The natural language an agent reads is *inside the cells*: `Next action` and
  `Summary` are paragraphs. That prose is already in `tasks.jsonl`, because the
  board is rendered from it.

So there is no markdown-only content on this file to preserve. Keeping the
projection buys one thing — a file you can open — and costs the read-back path
for 101 rows of typed fields.

That read-back path is where this project's most expensive open work lives:
**TASK-050** (seven failed V4 rounds on the single rule that a header cell has
one normalization; round 7 measured four LIVE header resolutions that revert to
the historical defect with 2,882 tests green), **TASK-067** (the writer can
destroy the table it writes to and `perry-lint` cannot see it), **TASK-199**
(two truth models in one file with nothing marking the boundary), and
**TASK-234** (a row splitter that was the sixth implementation of `split_row`,
found by a V4 reviewer after five were unified).

ADR-007 § 6 decision 4 already anticipated the direction: *"the readers for
`BOARD.md`, `OKR.md` and `.perry/config.md` go when those become stores."* What
it did not say is that the rendered file goes too.

## Options

1. **Keep `BOARD.md` as a rendered projection.** The status quo, and what
   ADR-007 § 6 decision 2 chose. Costs the table read-back path permanently, for
   1,190 bytes of content that is not in the store.
2. **Keep it and mark the boundary between its two truth models** — TASK-199.
   Reduces confusion, keeps the parser.
3. **Delete it; the board is what `perry-tasks`/`perry-state` prints.** Removes
   the file and the reason to parse a board table. Costs: the file you can open,
   GitHub-web readability, and it makes the CLI render the entire read surface
   for a 2,825-byte cell.

Option 3 was recommended for **deferral** in DESIGN-013's draft — until the same
move had been proved on `OKR.md` and `DECISIONS.md`, which are cheaper. The
recommendation was declined in favour of deciding now.

## Chosen

**Option 3.** `BOARD.md` stops existing. The board is what a command prints, from
`tasks.jsonl` and `risks.jsonl`.

**Precisely what is superseded: one sentence** — that `BOARD.md` exists as
rendered output. This does **not** restore hand-editability; it removes the
artifact, which is a different thing and a further step in the same direction.
ADR-007's `## Decision` rules 1, 2 and 3 — typed fields belong to Python, prose
is never parsed, the agent protocol inverts — stand unchanged and are what
DESIGN-013 § 5.1 extends.

**Gated on the render, not on the decision.** DESIGN-013 § 6 orders
`DECISIONS.md`, then `OKR.md`, then `BOARD.md`. The `OKR.md` step must report in
writing on whether the CLI render is a good enough reading surface. If that
report is negative, the board step stops and returns to DESIGN-013 rather than
proceeding because the decision was already made.

## Consequences

**The cost, stated plainly: there is no board file to open.** Today a human — or
an agent, or a GitHub web reader — opens `perry/BOARD.md` and sees the work.
After this, seeing the work requires running a command. That is a real loss of a
real property and it is the main argument against.

**The CLI render is a prerequisite, not a follow-up.** A `Next action` of 2,825
bytes has exactly one readable form once the markdown is gone. `perry-state
--json` is a payload, not a reading surface.

**Every lane's entrance ritual is rewritten.** `SKILL.md`, `work/SKILL.md`,
`goals/SKILL.md` and `decide/SKILL.md` all open by reading the board. That cost
belongs inside the implementing row, not discovered during it.

**What this buys.** The board table read-back path goes, and with it the reason
TASK-050, TASK-067, TASK-199 and TASK-234 exist in the form they do. Drift
detection for the board, `render --write` recovery for it, and its half of the
two-rename canonical pair go with it.

**Two real projects are affected.** gimegime-pmo and PolyForge are markdown-
canonical or mid-migration. Their path is `perry-migrate`, and ADR-004's
migrate-once posture still applies — this must not become a second migration for
a project that already ran one.

## What would reopen this

- The `OKR.md` step reports that a CLI render is a worse reading surface than the
  markdown it replaced. That is the stated gate and it reopens this before the
  board is touched.
- A host where running a command is not available but reading a file is — the
  decision assumes every Perry surface has a shell.
- Evidence that the loss of a linkable, web-readable board costs more than the
  parser did. `drift: 0` was the measurement offered in 2026-08-19; the
  equivalent here is how often anyone actually opens the file.
