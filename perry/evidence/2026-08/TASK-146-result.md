# TASK-146 — result

> Date: 2026-08-21 · Executor: claude-subagent · Merged locally
> Branch: `coding/task-146-viewer-provenance` · Cycle time: ~55 min
> 5 files: `viewer/serve.py` (+91), `viewer/templates/_macros.html` (+104),
> `phase.html` (+12), `viewer/README.md` (+22), `tests/test_kr_chain_render.py`
> (new, 16 tests)

## It corrected the row it was given

TASK-120's finding #3 said the viewer *"renders the chain view from
`viewer/parsers.py`"*. **Measured: it renders no KR `current` anywhere.**
`P002-O1-KR1` appears on zero pages, `PMOSnapshot.linkage` is parsed and **no
template has ever read it** — `grep -rn linkage viewer/templates/` is empty.
Confirmed independently by the PMO.

So the row was not *"move a consumer onto a derivation"* but **"build the
consumer, and build it so it cannot show the number alone."** That is why
`viewer/parsers.py` is untouched: **it never was the source of this number, so
there was nothing there to stop being it.**

## Why `perry-state --json` and not `bin/lib`

`bin/lib` is importable and the import would be one line — but
`kr_progress_provenance` **takes** its inputs rather than fetching them. Calling
it would have meant the viewer stating three things it does not know:

1. **where `.perry/events.jsonl` sits** relative to a state root that may be a
   subdirectory — `viewer/parsers.py` documents that there is no stored inverse
   of `resolve_state_root` and walks up four levels rather than solve it, and
   `bin/perry-state` had to say the same thing again in its own words;
2. **how to read that log** — a third spelling would join
   `perry-state § raw_events` and `perry-goals § read_events`;
3. **how to index task status across the store *and* the projection**, since a
   closed row leaves `BOARD.md`.

Staleness needs (1) and (2), so `events=[]` was not an option. The payload has
answered all three in one place and is a published contract. Cost: `/phase`
0.109s against 0.008s for a page with no chain; **no other page pays it.**

## What the card actually says, on this repository

```
P002-O1-KR1  current 0.0 · target 1.0 · metric 1 of 1 (baseline: the markdown is canonical)
        asserted by the author, not measured · source linkage-register ·
        dated 2026-08-20T20:32:00 (the register's own timestamp, not this KR's)
        no linked task has changed state since 2026-08-20T20:32:00
        linked tasks 4 · closed 4 · open 0

P002-O2-KR2  current 0.0 · target 0.0 · metric 0 (baseline 5 live copies across 4 rounds)
        asserted by the author, not measured · source linkage-register
        linked tasks 2 · closed 0 · open 2
```

**No percentage, no bar, and no `met` / `achieved` / `complete` anywhere in the
card** — asserted in the negative over the *whole card*, not only those two rows.
The tally is a count of **tasks**, in its own unit, beside `current` and never
inside it. *The render puts the contradiction in front of the reader and draws
no conclusion from it.*

Note the parenthetical it chose to render: **"the register's own timestamp, not
this KR's"** — TASK-155's finding, surfaced to the reader rather than hidden
behind a plausible date.

## Item 3, asserted both ways

```
P002-O1-KR3  current not asserted · target not asserted · metric reported
        the register gives this KR no `current`, and nothing here supplies one
        `current` was never asserted, so there is nothing to go stale
```

Positively (the words) **and negatively**: `re.search(r"current\s+(-?\d)")` must
not match, and neither `%` nor `—%` may appear. And the other half of the same
rule — **when the payload does not arrive the card says why and renders no KR at
all**; it never falls back to the register's bare number.

## Item 4 — reverting reddens the render, not a helper

The tests call `serve.py § phase` and assert on its **HTML**. Flask and
`markdown` are the viewer's opt-in dependencies and the suite must not require
them, so both are replaced with the smallest stand-ins the module body needs
(the Flask stub keeps every `@app.template_filter` registration) and
`render_template` is wired to a **real Jinja environment over the real
templates**. Everything between the route function and the page is shipped code.

| revert | failures |
|---|---|
| route stops passing `chain=` | 15 of 16 |
| provenance line dropped from the macro | 10 |
| linked-task tally dropped | 6 |
| staleness line dropped | 4 |
| absent `current` defaults to `0` | 4 |

**No helper-only test exists in the module** — `kr_chain`'s return value is never
asserted on directly.

## The one thing here that needs a decision

**A new dependency direction.** `bin/` imports `viewer/` in a dozen tools;
`viewer/serve.py` now invokes `bin/perry-state` at request time. It is a
subprocess, not an import, so **there is no cycle** — but it is the first time
the viewer depends on `bin/` at all, and `viewer/README.md` now says so out loud.

If Perry would rather the viewer stayed a pure renderer, the alternative is a
lane function that assembles the derivation's three inputs and lives in `bin/lib`
beside it — a change to the derivation's module, which was out of scope here.

## And a pre-existing defect it found on the way

`viewer/parsers.py § _resolve_project_root` returns the directory holding
`BOARD.md` — the **state** root — while `bin/perry-viewer` exports
`PERRY_PROJECT` as the **project** root and `perry-state --root` expects the
project root. On a project whose state lives in a subdirectory — *Perry's own* —
those are different directories, and **the viewer renders an empty snapshot when
pointed at the project root.**

Same missing inverse that decided the source question above, now load-bearing for
two things. In that degraded configuration the chain still refuses to invent: the
payload reports *"no event log, so whether a linked task has moved … cannot be
evaluated"* and the card prints exactly that.
