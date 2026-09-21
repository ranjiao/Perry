# `add-task` — the measurements and history behind its rules

Not loaded by `add-task`. `add-task.md` keeps every rule and refusal; this page keeps the incidents, measurements and withdrawn wordings that explain them. Moved on 2026-09-21 (TASK-470); the prose is carried over unchanged, a passage split mid-sentence is marked by the sentence that opens it.

## Why --summary is a hard gate

From `add-task.md § add-task`, the `--summary` refusal.

It is a hard gate rather than an advisory because **the advisory version has already been tried on this exact field and measured**: `--summary` was an optional flag from contract 1.11, nothing asked for it and nothing checked it, and it reached 25 of 114 open rows. `DESIGN-003 § 4` decision 4's "advisory first, hard gate next" does not apply here, because its stated reason is retroactive invalidation and `add` has no retroactive half — it governs only rows minted from now on. The rows minted before are reported, not refused, by `perry-lint --summaries`.

## The unlinked bullet's history

From `add-task.md § add-task`, the KR-attribution gate's `--unlinked` bullet.

Omitting `--kr` was what this bullet used to say — it filed the row behind a warning and left it in `never_answered` permanently, because a later `perry-goals link` writes `via: "link"`, which `P003-O3-KR2` excludes by design.

(This sentence also claimed the declaration stays VISIBLE — naming `perry-lint`, then `perry-state § attribution`. Both were measured false and the claim was deleted under `USER-928` answer C: `linkage-unlinked-exists` warns only on an id that is **not** a row in `tasks.jsonl`, and `attribution.declared_unlinked` is scoped to `phase/CURRENT` — 143 standing declarations on Perry's own board, 116 reported. No reader reports a healthy standing declaration from a past phase.) This bullet used to say "write the BOARD row with `attribution: unlinked`" — there is no such column in `schema/state-schema.json` and there never was, so the instruction produced either a cell nothing reads or a widened board nobody asked for.

## Why the mode columns need no precedent

From `add-task.md § add-task`, mode columns.

(An earlier draft justified this as "the same clause `close-task` already has for `Verification`." There is no such clause. `Verification` is a declared *optional* column in `schema/state-schema.json`, but `close-task` removes the row rather than stamping it — the rung is written to the journal line and the event, which is where `perry-task list` reads it from. The back-reference pointed at a precedent that never existed; the rule stands on its own.)

## Why a row changes track by command

From `add-task.md § add-task`, `perry-task track`.

The table above is about creation, and for a long time creation and `route` were the only two entrances a track had — so a project that declared a second track started it empty and had no tool path for the work already on the board.

## Why all three fields are shown as required

From `add-task.md` step 1.

They used to be shown as optional here
while two of them were already hard refusals in the tool, so the block a
reader copied did not run — which is the shape TASK-325 exists to stop one
field further along.

## Why exactly one prefix

From `add-task.md` step 1, which id family `add` mints into.

Perry stops at *exactly one* and does not take the most common. A real board
here carries 36 families in its task tables, declared in its own
`## ID prefixes` section, and they are not stylistic — `IPS-*` / `ALLOC-*` /
`DUE-*` mean one workstream and `TECH-*` / `DATA-*` another, filed in
separate sections. Picking the plurality winner would mint an id that
asserts a workstream nobody chose, and an id is permanent. A `TASK-001` on
such a board is visibly Perry's and claims nothing.

## Why the row is never hand-written

From `add-task.md` step 1.

Do not hand-write the row. Every field above was one an agent supplied and
got wrong at least once: malformed pipes, a reused ID, a timestamp that was
an assertion, a clock nobody wound. `perry-state` reports a hand-written row
as `unrecorded` at the next standup — reported, not refused, because editing
your own markdown is legitimate; but it is visible, and that visibility is
the point.

## Why `--group` exists on `add` and `route`

From `add-task.md` step 1.

A real year-old project files work under headings like that, and `add`
refused it outright until TASK-019/020's review found it.

**`route` takes `--group` too, and means the same thing by it.** It did not
until TASK-053: the flag parsed and `route` never read it, so the intake
drain could not run at all on a board with no `## P0`/`## P1`/`## P2` — and
the refusal that told the user to pass the heading to `--group` was telling
them to pass it to a flag that verb threw away. Both verbs resolve the
landing section through one function now, so a board Perry can `add` into
is a board Perry can `route` into.

## Why the tool renders the definition block

From `add-task.md` step 2.

**This step used to hand the block to the agent, and the agent did not
produce it.** Measured the day the tool learned to: `## New tasks
added` appeared three times in the journal of the day *before* and zero
times after, so every tool-created task was one title and nothing else.
That is ADR-007 rule 3 stated as a defect — the fields were supplied to the
tool and the document was then expected to appear from somewhere.

## Why the spec shape is load-bearing

From `add-task.md` step 3. The two paragraphs as they stood before the step kept their normative sentences and pointed here.

**Why the shape is load-bearing, and not a style rule.** `dispatch` pre-flight step 4 re-validates the spec against `.perry/hook.md § High-stakes operations` by reading exactly those three sections (`work/reference/dispatch-preflight.md` step 4), and its reader — `viewer/parsers.py § _section` — matches `^## <heading>` and nothing else. A scope written as an `h3` or as a bullet is invisible to it. **The spec does not then fail the gate; it disarms it.** Every high-stakes fragment is matched against the empty string, and the scan returns `touches: {}`, `verdict: pass`, **exit 0 — byte-identical to a spec that was read in full and found genuinely clean.** Measured 2026-09-02: a spec whose `Deliverable` named `git push origin main`, `rm -rf` and `gh release` scanned `pass`/exit 0 in the bullet shape and `refuse`/exit 3 on five fragments with the identical words under `## Deliverable`; 45 of this project's own 135 specs are in the first state. `perry-lint --specs` — and the default `perry-lint --root .` — now reports a spec that presents the gate no scope, so the empty scan is visible; but the check reports it, it does not undo it, and the spec is only safe if it is written in the shape above.

**This step used to say the spec "contains the same schema" as the journal block, and that sentence is what produced the 45.** `bin/perry-task § cmd_add` renders the journal definition block as bullets, and that is correct *there*: the block sits under `### <ID> — <title>` inside `## New tasks added`, so a `## Deliverable` in it would close the section it lives in and cut one day's journal in half. The journal keeps its bullets; the spec takes `## ` headings. Same fields, two shapes, because the two files have two readers — a person scrolling a day, and a safety gate matching sections. "The same schema" was read as "the same shape", which is the only reading the rendered block supports, and following it disarmed the gate. Do not copy the journal block into a spec; write the sections.
