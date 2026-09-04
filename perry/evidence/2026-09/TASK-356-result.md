# TASK-356 — the store-ownership restore assertion was scoped to the whole row

Branch `task-356-cell-scoped-restore`, cut from `main` at `dda8d5f`.
One file changed: `tests/test_board_render.py`.

## 1. The reproduction

`tests/test_board_render.py:240`, inside
`TestTheBytesComeFromTheStore.test_every_rendered_field_moves_when_the_store_moves`,
subtest `field='status'`:

```
AssertionError: 'dropped' unexpectedly found in
"| TASK-348 | ADR-007 census part 1 — viewer/ and the nineteen remaining bin/ tools
 | Coding Agent | not_started | MEASURED ON main 2026-09-04, … and two of its own
 table rows carried unescaped pipes that silently dropped six call sites, which is
 the exact defect class ADR-007 names. | — |  | TASK-263 | main | …"
```

The prose that triggers it is TASK-348's `next_action`:

> two of its own table rows carried **unescaped pipes that silently dropped
> six call sites**, which is the exact defect class ADR-007 names.

The sentinel for `status` is the ordinary English word `dropped`. The word
that collides is in the `Next action` cell — a different column from the one
the subtest grades. Nothing about the renderer moved; the board's own English
did.

This is the fixed point of a receding fix. The `row_of` docstring already
records the previous round: the assertion used to be over the whole *board*,
was narrowed to the whole *row* because "`dropped` is in four other rows'
prose", and the same word has now caught up with it one scope later.

## 2. The sentinel census — required, and it finds a second live trap

Seven fields, seven sentinels, measured against Perry's live board
(145 rendered id rows):

| field | sentinel | rows whose text already contains it | where |
|---|---|---|---|
| `status` | `dropped` | **7** | `Title`, `Next action` |
| `owner` | `Nobody` | **1** | `Title` ("Nobody has seen this history") |
| `verification` | `V6` | 0 | — |
| `depends_on` | `TASK-001, TASK-002` | 0 | — |
| `evidence` | `evidence/nothing.md` | 0 | — |
| `title` | `A TITLE NOTHING WROTE` | 0 | — |
| `next_action` | `AN ACTION NOTHING WROTE` | 0 | — |

**Three of the seven sentinels are ordinary words or tokens that prose
produces**, and two of them already do so on today's board:

- `dropped` — ordinary English verb; 7 live rows.
- `Nobody` — ordinary English pronoun; 1 live row. **The identical trap, one
  board row from firing.** Fixing `status` alone would have left it loaded.
- `V6` — not English, but a token this project writes into free text as a
  matter of routine (`main`'s own log: "TASK-332 closes at V4"). It collides
  the day a V6 exists.

The remaining four are shaped so that prose does not produce them.

A second, sharper finding fell out of the census: **`USER-916` renders
`status: dropped` on the live board today.** So `dropped` is not merely a word
the prose contains — it is a value the graded column itself legitimately
takes. Any restore assertion of the form "the sentinel is absent" is therefore
defeatable a second way, by a row that is genuinely in that state.

### What the old rule does against prose

A row whose `title` and `next_action` are made to quote **every** sentinel at
once — the worst board this project could legitimately write — fails the old
whole-row rule on **all seven fields**, not just `status`:

```
title FAIL / owner FAIL / next_action FAIL / evidence FAIL /
verification FAIL / status FAIL / depends_on FAIL      → 7 failing fields
```

The defect was never about `status`. It was about scope.

## 3. The shape chosen

Assert on **the cell the field renders into**, and compare it for **equality
against the cell as it rendered before the mutation** rather than for absence
of the sentinel.

Cell scoping is the part that fixes the reported bug: once the assertion is
confined to one column, a field can only ever collide with its *own*
sentinel, and the six cross-column collisions the census found stop being
reachable by construction.

Equality-against-`was` is the part that closes the residual case cell scoping
leaves. `assertNotIn(want, cell)` would still fail on a row genuinely holding
`dropped` in `Status` — which `USER-916` shows is a real row, not a
hypothetical one. Comparing to the pre-mutation rendered value has no such
failure mode, and grades strictly more besides: a renderer that blanked the
cell to `—` on restore satisfied `assertNotIn` and fails this.

A precondition `assertNotEqual(was, want)` is added so the round trip cannot
go vacuous: if a field's stored value already equals its sentinel, both halves
would pass without the renderer being asked anything, and that now fails
loudly instead of passing silently.

The column is resolved **by name** through the schema glossary
(`P._column_keys`), read through `T.split_row` and `T.header_index` — the
repository's only row splitter and only header fold — rather than by a fixed
index. `viewer/parsers.py` spends its longest comment explaining that column
*order* is not constrained by the schema; a locator that hardcoded index 3
would be the same defect that comment describes, planted in the test.

A second test, `test_a_row_whose_prose_carries_every_sentinel_still_passes`,
plants every sentinel in the row's own `title` and `next_action` and runs all
seven round trips against it. It is a construction, not a scan of today's
board, deliberately: a test that scanned live prose would go red whenever the
project's own text changed, which is the defect being fixed re-introduced one
level up.

## 4. Verification

**The property still bites.** Six mutations of the renderer, each anchored by
line number with an assertion on the old text at that line, `__pycache__`
cleared and the whole-second boundary waited out between each:

| # | site | mutation | result |
|---|---|---|---|
| M1 | `bin/perry_store.py:76` | `status` removed from `FIELD_BY_COLUMN` — the Status column stops being read from the store | **RED** (`field='status'`) |
| M2 | `bin/perry_store.py:79` | `next action` removed | **RED** (`field='next_action'`) |
| M3 | `bin/perry_store.py:80` | `depends on` removed | **RED** (`field='depends_on'`) |
| M4 | `bin/perry_store.py:76` | `owner` and `status` render each other's stored field | **RED** (`field='owner'` and `field='status'`) |
| M5 | `bin/perry_store.py:292` | `depends_on` joined with `,` instead of `", "` | **RED** (`field='depends_on'`) |
| M6 | `bin/perry_store.py:293` | an empty stored value falls back to the board's own cell text | **RED** (3 other tests; the round trip stayed green — see below) |

M1 is the mutation the row asks for by name: a field stops being read from the
store, and the test names that field.

M5's first run reported `ANCHOR MISS` — the line number was off by one and the
old-text assertion refused to patch the wrong line. Recorded because it is the
anchor discipline working, not a clean result.

## 5. The green — the finding

**E1. The restore half has no independent power.** The SET half was stripped
out of the round trip and the restore half run alone against M1. It came back
**GREEN**.

The cause is structural, and is worth writing down so the next round does not
re-derive it: `BOARD.md` is a static template during these tests — only
`tasks.jsonl` is rewritten between renders — so the only stale value a
renderer can hold *is* the board's original text, and the SET half already
fails on it one assertion earlier. The restore half can only bite a renderer
that persists its own output back into the template, and
`test_render_and_diff_write_no_file` separately forbids exactly that.

M6 is the same finding from the other side: it is red for the module but the
round trip itself stayed green, because the field it perturbs
(`verification`) had `''` in both the store and the board, so neither half
could see a difference.

The half is kept regardless — the row is explicit that dropping it is the
wrong answer, and it is the only assertion asserting the cell tracks the store
in both directions — but it is now documented as costing one render and
having never been demonstrated to catch anything, rather than being presented
as load-bearing.

**E2. A hypothesis of mine that was wrong, recorded rather than dropped.** I
predicted the old whole-row rule would pass M4 (owner/status swapped), since
`| Nobody |` would still appear *somewhere* in the row — which would have
shown cell scoping to be strictly stronger at catching bugs. It does not: the
old rule goes **RED** on M4, on all seven fields. So the claim "cell scoping
catches renderer bugs the old rule missed" is **not** demonstrated and is not
made. What cell scoping fixes is the false **RED** — the board's own prose
failing a sound renderer — not a false green.

## 6. Suite

`bash tests/run`, three consecutive runs: see the RESULT block.

Known unrelated reds, each re-run alone before attribution:
`test_contract_key_parity` (TASK-335), `test_one_primitive` /
`test_one_choke_point` (TASK-341), `test_host_support` (TASK-357,
load-sensitive).
