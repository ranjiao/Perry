# TASK-237 — result for deliverables 1 and 2 (USER-931 answer A)

> Scope: `TASK-237-spec.md § Amendment 2026-09-14` only. Deliverable 3, the
> deletion, was not touched. `BOARD.md`, `tasks.jsonl`, `asks.jsonl` and
> `schema/state-schema.json` are unchanged on this branch.
>
> **Deliverable 1 is NOT delivered, and that is the reported outcome.** From
> what the tree declares, a board render with no `BOARD.md` cannot be
> byte-identical to the live file. Hard limit 5 applies: stop, and report exactly
> which bytes differ and why. § 2 does that, and § 2.4 proves the list is
> complete.
>
> **Deliverable 2 is delivered.** No code site needed a change, because all nine
> already accept `.perry/config.jsonl`. Two of the nine (A2 `bin/lib`, A5 the
> `perry-lint` walk) were guarded by no test, measured by mutation, and the prose
> keyed the session trigger and bootstrap on the file. § 3.

---

## 0. Base check

| | |
|---|---|
| branch | `worktree-agent-a00cb81588fef0c24` |
| HEAD at dispatch | `583f024f` ("Merge bin-contract-phase-a: …") — the stale base the dispatch predicted |
| `git merge-base --is-ancestor 02825582 HEAD` | **1**: HEAD did not contain the spec |
| tree | clean (`git status --porcelain` printed 0 lines) |
| action | `git merge --ff-only 02825582` on **this branch only**; `main` and every other ref untouched |
| re-asserted | `--is-ancestor` → **0**; HEAD `02825582eb6e` ("TASK-237's spec amended: the reading surface comes first (USER-931 answer A)") |

## 1. Baseline, measured in this worktree before any edit

- `bin/perry-tasks render --root .` exit 0, `cmp`-equal to `perry/BOARD.md`.
  **The file is 157,242 bytes, not the 154,151 the gate recorded.** The store
  moved between that measurement and `02825582`. sha256 `7de77de6…0758`.
- Register reports, from a scratch copy of the state (`perry-tasks diff`,
  `risks-diff`, `asks-diff`, `intake-diff`):

  | register | rows from store | verbatim rows | verbatim cells | decorated | disagreements |
  |---|---|---|---|---|---|
  | tasks | 98 | 0 | 0 | 0 | 0 |
  | risks | 4 | 0 | 0 | 0 | 0 |
  | asks | 32 | 0 | **`Idle`: 32** | 0 | 0 |
  | intake | 0 | 0 | 0 | 0 | 0 |

- The suite: named in § 5.

## 2. Deliverable 1 — the declared skeleton cannot reproduce the live board

### 2.0 The stop, stated plainly

**Deliverable 1 stops at hard limit 5.** Byte-identity with `perry/BOARD.md`
cannot be reached without breaking hard limit 2 (editing
`schema/state-schema.json`) or hard limit 3 (building the render from
`BOARD.md`). So no store-only render command was built, `bin/perry-tasks` and
`bin/perry_store.py` are unchanged, and nothing on this branch prints a
"close" board. The files added for D1 are the measurement script
(`tests/task237_board_skeleton_probe.py`, § 2.2–2.4) and this report.

**What the declarations cannot supply.** § 2.3 has **13 differences** between
the declared skeleton and the live file. **Twelve are layout that exists only
in the file**: bytes it holds that no store, schema entry, template or config
key declares.

1. L1 — the title's project name (`Perry`)
2. L2 — the three header-prose lines filled from an older template (`/pmo dispatch`, dated paths)
3. L3 — the `Last updated` date the writer stamps
4. L4 — the `/pmo triage` wording
5. L5 — the four-line "Bootstrapped 2026-08-16" paragraph
6. L6 — the `## Intake` section and its position before `## P0`
7. L7 — the task tables' column set and order, which differs between P1 and P0/P2
8. L8 — Cadence's column set, and its placeholder row (no cadence store exists)
9. L9 — the User Input Queue's column order
10. L10 — the two `Idle` cells holding `—`
11. L11 — the whole `## Done this period` section
12. L13 — the 22 `Depends on` cells holding `—` over an empty stored list

**The thirteenth, L12, runs the other way.** The template carries a 9-line
comment under `## Top risks` that the live file does not have.

§ 2.4 proves the twelve are the whole gap: supplied from outside the stores,
they reproduce the file `cmp`-exact. Closing the gap needs a decision this row
may not take (§ 2.6), and the report does not paper over it: no prose, no
column order and no placeholder was added to any render to make the bytes match.

### 2.1 Why today's render cannot run without the file

`bin/perry-tasks § render` (`:116`) builds `mod.Board(<state>/BOARD.md)`, which
refuses at `bin/perry-task:669` when the file is absent. `perry_store.plan`
(`bin/perry_store.py:492`) iterates `board.lines`, and `render_lines` puts back
every line no record claims. The file supplies **all of the layout**: the title,
the prose, which sections exist and in what order, each table's columns and
their order, and the cells no store holds. The stores supply the row cells.
`DESIGN-016 § 8` recorded this as an open question ("Can `BOARD.md` be rebuilt
from `tasks.jsonl` at all?"). § 2.3 and § 2.4 answer it with measurements.

### 2.2 The probe: the board from declared sources only

`tests/task237_board_skeleton_probe.py probe <root>` reads exactly:

| part of the board | read from |
|---|---|
| title, header prose, heading text, section order, placeholder rows, the risks comment | `work/state/BOARD_TEMPLATE.md` |
| each table's columns | `schema/state-schema.json § files[id=board].tables[]`, `columns` then `optional_columns` |
| section order, cross-check | `§ files[id=board].headings` (it agrees with the template) |
| the `Last updated` placeholder | `.perry/config.jsonl` `last_updated`, the only declared value any placeholder names |
| rows | `tasks.jsonl` (non-terminal, `group` == heading, by `order`), `asks.jsonl`, `risks.jsonl`, `intake.jsonl`, through `perry_store.cell_text` and `tables.render_row` |

It **refuses with exit 3 if anything opens `BOARD.md`**: `open` is replaced
before the first read. Where the declarations leave something open, the probe
makes a choice and prints it to stderr as `choice:`, so every difference traces
back to a named choice.

**Result on `02825582`:** exit 0, **157,422 bytes against 157,242, not
identical. Only 2,349 of the live file's 157,242 bytes fall on lines that match
exactly.**

### 2.3 Every place the declared skeleton does not reproduce the live file

Line numbers refer to `perry/BOARD.md` on `02825582`.

| # | live bytes | what the file says | what the declarations say | why they cannot agree |
|---|---|---|---|---|
| L1 | line 1 | `# Board — Perry` | template `# Board — {{project name}}` | No declared store holds a project name. `.perry/config.jsonl` has `document_language`, `chat_language`, `repo_layout`, `state_root`, `pmo_repo_path`, `code_repo_path`, `last_updated` |
| L2 | lines 4–6 | `journal/2026-08/2026-08-16.md`, `evidence/2026-08/<TASK-ID>-*.md`, `/pmo dispatch <TASK-ID>` | `journal/{{YYYY-MM}}/{{YYYY-MM-DD}}.md`, `{{TASK-ID}}`, `/perry work dispatch {{TASK-ID}}` | The live text was filled from an **older template** at bootstrap. The words differ, not only the placeholders |
| L3 | line 8 | `Last updated: 2026-09-14` | config `last_updated` = `2026-08-16` | The line is stamped by the writer (`bin/perry-task:2932 LAST_UPDATED_RE`) and stored nowhere. The config key is a different fact |
| L4 | line 9 | `run \`/pmo triage\`` | `run \`/perry work triage\`` | older template, as L2 |
| L5 | lines 10–13 | `> **Bootstrapped 2026-08-16** from the hand-off of DESIGN-001 and DESIGN-002 …` (4 lines) | nothing | Prose specific to this project. It exists only in the file |
| L6 | lines 15–18 | `## Intake` with its table, **first** section | `tables[]` declares an `^Intake` table; `headings` and the template carry no `## Intake` | Its existence and its position come from `Board.ensure_section` (`bin/perry-task:892`), which inserts it before `## P0`. That is code behaviour, not a declaration |
| L7 | lines 22, 27, 99 | 15 columns: `… Evidence \| Verification \| Depends on \| Track \| Stage \| Arrived \| Stage since \| Parent \| Commitment \| Role`. **P1 has `Stage since \| Arrived`; P0 and P2 have `Arrived \| Stage since`** | 6 `columns` + 9 `optional_columns` in the order `Track, Verification, Stage, Arrived, Commitment, Stage since, Parent, Depends on, Role` | **Two tables on one board disagree with each other**, so one declaration cannot produce both. Column order is a history of writes: `Board.ensure_columns` (`bin/perry-task:863`) appends whatever column is missing to whatever header exists. The schema declares which columns *may* appear, not which *do*, and not where. Consequence: all 98 task rows, 73,896 bytes, differ in the probe, only because the cells are in another order |
| L8 | lines 135–137 | Cadence with 6 columns (no `Last run`) and one empty row `\|  \|  \|  \|  \|  \|  \|` | template 7 columns; schema `optional_columns: Last run, Last evidence` | Which optional columns are present is not declared. There is **no cadence store** (`TASK-198 "## Cadence becomes a store"` is an open P2 row), so the row is file-only |
| L9 | line 141 | `USER-id \| Needed from user \| Blocks \| Idle \| Status \| Asked` | template `… Blocks \| Idle \| Status` (no `Asked`); schema optional `Asked, Idle` | Order not declared, and the two declarations disagree about it |
| L10 | 2 cells | `Idle` = `—` on USER-001 and USER-002, empty on the other 30 | `ASK_FIELD_BY_COLUMN` omits `Idle` deliberately (a derived age) | Bytes in a column that has no stored field |
| L11 | lines 176–179 | `## Done this period (leaves the board at next triage)` with `\| ID \| Title \| Evidence \|`, 0 rows | nothing — not in `headings`, `tables[]` or the template | Declared nowhere |
| L12 | — | `## Top risks` has **no** HTML comment | the template carries a 9-line `<!-- Written by perry-task risk-add … -->` (577 B in the probe) | The template has something the live board does not |
| L13 | 22 cells | `Depends on` = `—` on 18 P1 and 4 P2 rows | the store holds `depends_on: []` | An empty list renders as `""`. `describe_cell` keeps the declared blank marker as layout (`bin/perry_store.py:363`), so the file holds bytes the store cannot. The other `—` cells (`Next action`, `Evidence`, …) are stored literally as `"—"` and reproduce |

**What the declared skeleton does reproduce:** the six declared headings' text
(`P0 (must finish this period)`, `P1`, `P2`, `Cadence (…)`, `User Input Queue`,
`Top risks (…)`), their relative order, template lines 3 and 7, and **every row
cell the stores hold, once the header is right**. That last point is § 2.4.

### 2.4 The list is complete: the accounting render is `cmp`-equal

A list of differences leaves open whether something is hidden behind L7's
column shuffle. So the probe script has two more modes:

- `facts <BOARD.md>` **reads the board** and writes down, as JSON, every byte no
  store holds: the non-table lines, each table's header and separator, the rows
  of tables with no store, cells in columns with no field, and blank markers.
- `accounting <root> <facts>` renders from that JSON plus the stores and
  **refuses to open `BOARD.md`**.

| run | result |
|---|---|
| accounting, state with `BOARD.md` present | exit 0, **`cmp`-equal** to `BOARD.md` |
| accounting, scratch copy with `BOARD.md` deleted | exit 0, **`cmp`-equal** to the original `BOARD.md` |

So the gap between the stores and the live file is **exactly** the facts:

| undeclared layout | lines / cells | bytes |
|---|---|---|
| non-table lines (title, prose, headings, blank lines) | 38 lines | 949 |
| table header and separator lines | 16 lines | 971 |
| rows of a table with no store (Cadence) | 1 row | 20 |
| cells in a column with no field (`Idle`) | 2 non-empty | 2 × `—` |
| blank markers over an empty stored list (`Depends on`) | 22 cells | 22 × `—` |

Every other byte, **155,323 bytes of row lines less those 24 cells**, comes out
of the stores already.

**This is accounting, not a render, and it must not become one.** The facts are
read out of `BOARD.md`. A renderer fed them passes `cmp` for exactly the reason
hard limit 3 forbids: it reproduces the file because it was built from the file.
It is committed so a reviewer can rerun the completeness claim, and no test or
command uses it.

### 2.5 Both states, measured

| state | `perry-tasks render` (today) | probe (declared only) | accounting (facts + stores) |
|---|---|---|---|
| `BOARD.md` present | exit 0, `cmp`-equal, 157,242 B | exit 0, **not equal**, 157,422 B | exit 0, `cmp`-equal |
| `BOARD.md` deleted (scratch copy) | **exit 1, 0 bytes**, `refused — no BOARD.md at …` | exit 0, byte-identical to its own file-present output; TASK-391's 2,218-byte next action present whole: **yes** | exit 0, `cmp`-equal to the original file; TASK-391 whole: yes |

**The acceptance was a command, built from the stores and the declared skeleton,
`cmp`-equal to the file. It is not met.** The probe's second column shows what
*is* reachable today without the file: every row, every column the schema
declares, every cell whole, with a 2,218-byte cell intact. It is not byte-identical.

### 2.6 What reaching byte-identity would take: a decision, not taken here

1. **Declare the layout.** Put L1–L13's facts in a declared, per-project place.
   That is a new `claims` entry, so `schema/state-schema.json` changes, which is
   hard limit 2 and on `.perry/hook.md § High-stakes operations`. And the only
   source for this project's facts is `BOARD.md` itself, so the first `cmp` after
   that import proves only that the import was faithful (§ 2.4's caveat). An
   honest acceptance then has to be measured on a project whose layout record was
   authored independently.
2. **Normalise the board once to the declared skeleton**, in one reviewed
   whole-file change: one column order for P0, P1 and P2, the template's prose,
   `## Intake` and `## Done this period` either declared or removed. After that,
   byte-identity to the declarations holds. This rewrites `BOARD.md` (hard limit
   6) and changes what `render` prints (hard limit 4), so it is the user's to decide.
3. **Drop the byte clause.** Accept USER-931's "every row, every column, every
   cell whole" as the adequacy test. § 2.5 shows that is reachable today.

→ **TASK-0NN (a)**: choose among 1–3. This is USER-931's acceptance, so it is
the user's call. It blocks deliverable 3 exactly as the gate did.

## 3. Deliverable 2 — a Perry project is not recognised by `BOARD.md` existing

### 3.1 The enumeration, re-done

Bound: `grep -rnE 'BOARD\.md' bin/ viewer/ SKILL.md work/ goals/ decide/ reference/`
gives 319 lines. They were filtered to existence and detection checks, plus a
sweep for indirect forms: board-path variables later tested, walks up the
parents, `glob`, `is_adopted`, `configured(` callers, and "no `BOARD.md`" prose.
**Size, stated before the first edit: 9 code detection sites and 6 prose lines in
2 files.** The spec's list had 8 code and 4 prose. How it differs:

- `bin/perry-task:669` and `:8720` are **not detection**. They are the board
  reader refusing to read a file that is absent: § 2.1's cause, which is D1 and
  D3 territory. Kept in § 3.4.
- Added: `bin/perry-state:1822` (the `installed` gate), `bin/perry-diagnose:1480`
  (`scan_tracking`), `:2611` (`is_perry`), and `work/reference/bootstrap.md:7`
  and `:49`.

### 3.2 The nine code sites: none changed, each with its reason and its guard

**Every one already asks `configured(d)`, meaning `.perry/config.jsonl`, beside
`BOARD.md` / `OKR.md`.** TASK-233 and TASK-247 made that conversion. No code
change was needed for a board-less configured project to be recognised.

| # | site | decides | guard on a board-less OKR-less project before this row | after |
|---|---|---|---|---|
| A1 | `viewer/parsers.py:578 § _resolve_project_root` | project root (cwd walk) | `test_project_root_resolution § test_standing_in_a_subdirectory_both_walk_up_to_the_project_root` (red under M-A1) | + `test_the_parsers_walk_finds_the_project_from_below_its_state_root` |
| A2 | `bin/lib/__init__.py:540 § resolve_project_root` | project root (walk) | **none** | `test_the_lib_walk_finds_the_project_from_below_its_state_root` |
| A3 | `bin/perry-state:2596 § resolve_root` | project root (walk) | `test_config_store_readers § test_the_walk_finds_a_store_only_project_from_a_subdirectory` (a `BOARD.md` at the state root, none at the project root) | + `test_perry_state_walks_to_the_project_from_below_its_state_root` |
| A4 | `bin/perry-state:1828 § build` | `installed`, which drives SKILL.md's first-time setup | `test_config_store_readers § test_the_installed_gate_counts_a_store_only_project_as_installed` | + `test_perry_state_calls_it_installed` |
| A5 | `bin/perry-lint:5883 § main` | project root (walk, no `--root`) | **none** | `test_the_linter_walk_finds_the_project_from_below_its_state_root` |
| A6 | `bin/perry-lint:4905 § is_adopted` | adoption, which gates every schema check | `test_config_store_readers § test_the_linter_calls_a_store_only_project_adopted` | + `test_the_linter_calls_it_adopted` |
| A7 | `bin/perry-explain:662 § typed_task_lookup` | adoption, so whether the task store is read | 4 × `test_explain_typed_tasks § TypedTaskLookup` (red under M-A7) | + `test_explain_reads_the_task_store` |
| A8 | `bin/perry-diagnose:1480 § scan_tracking` | `installed` | `test_config_store_readers § test_scan_tracking_calls_a_store_only_project_configured` | + `test_diagnose_calls_it_installed` |
| A9 | `bin/perry-diagnose:2611 § diagnose` | `is_perry` | `test_config_store_readers § test_is_perry_counts_a_store_only_project_as_perry` | + `test_diagnose_treats_it_as_perry` |

Every entry in the "before" column is a mutation result, not a reading of the
tests: it names what went red when that site's `configured` was reverted with
the new module present. "**none**" means only the new module went red. § 4.

**Why the `BOARD.md` and `OKR.md` disjuncts were left in place.** A project with
no config store is recognised *only* by them. That covers a markdown-canonical
or mid-migration project (ADR-010 names gimegime-pmo and PolyForge), and a
pre-ADR-019 project whose only configuration is `.perry/config.md`, which
`configured` deliberately no longer counts
(`test_config_store_readers § test_a_markdown_only_project_is_not_configured`).
Removing a disjunct now would send exactly those projects into first-time setup
on every session. That is the failure D2 exists to prevent, on a different
population. The disjunct goes dead when deliverable 3 deletes the file, and its
removal belongs there, with those projects' state measured first.

### 3.3 The prose: changed

The lane trigger and the bootstrap prompt now name the predicate the standup
already computes at step 2, `perry-state --json` → `installed`. That is A4, and
it accepts `.perry/config.jsonl` alone.

| site | before | after |
|---|---|---|
| `work/SKILL.md:43` | "…bootstrap procedure in a project with no `BOARD.md`" | "…in a project `perry-state --json` reports `installed: false` for" |
| `work/SKILL.md:108` | "A new session opens in a project that contains a `BOARD.md` at the root." | "A new session opens in a Perry project — one `"$PERRY_HOME/bin/perry-state" --json` reports `installed: true` for. A `.perry/config.jsonl` at the project root is enough on its own; whether a `BOARD.md` exists is not the test." |
| `work/SKILL.md:292` | "If invoked in a project with no `BOARD.md` at the project root, ask once:" | "If `"$PERRY_HOME/bin/perry-state" --json` reports `installed: false` for the project — no `.perry/config.jsonl` at its root and no Perry state files — ask once:" |
| `work/reference/bootstrap.md:3` | "…a project that has no `BOARD.md` at the project root…" | "…a project `perry-state --json` reports `installed: false` for…" |
| `work/reference/bootstrap.md:7` | "If `BOARD.md` is absent, the agent asks:" | "If `perry-state --json` reports `installed: false`, the agent asks:" |
| `work/reference/bootstrap.md:49` | "…will find `BOARD.md` present and skip the bootstrap prompt" | "…will find `perry-state --json` reporting `installed: true` — a `.perry/config.jsonl` alone is enough — and skip…" |

**No Python guard reads this prose, on purpose.** A test that pattern-matches a
sentence in `SKILL.md` is Python judging what a document means. What the prose
names is guarded instead: A4, by two tests, both mutated in § 4.

### 3.4 Left: sites that need the file's *contents*, not detection

| site | behaviour with no `BOARD.md` | belongs to |
|---|---|---|
| `bin/perry-task:669 § Board.__init__` | `Refused("no BOARD.md at …")`. `perry-tasks render`/`diff`/`build` and the three register renders all refuse | D1: this is § 2.1 |
| `bin/perry-task:8716–8721 § main` | read-only commands run with `board=None`; **every write refuses** ("needs the projection layout") | D3. Same cause as D1 → **TASK-0NN (b)** |
| `schema/state-schema.json § files[id=board].required: true` | `perry-lint` exits 1 with `✗ BOARD.md [missing-file]` on a board-less project | D3. A schema edit, high-stakes → **TASK-0NN (c)** |
| `bin/perry-diagnose:486 § open_user_asks` | looks at `root/BOARD.md`, then `root.glob("*/BOARD.md")`, bypassing `resolve_state_root` | reads the User Input Queue out of the file rather than `asks.jsonl`. D3 |
| `bin/perry-lint:4131, :4279, :4405` | `*-drift-uncheckable` warnings | D3 |
| `bin/README.md:93` | "else walk up from the cwd looking for the state files" | message only; accurate for A2, A3 and A5, which do look for `.perry/config.jsonl` too |

### 3.5 The board-less, OKR-less project, measured

**Scratch copy of this project's state:** `.perry/config.jsonl`, `.perry/hook.md`,
`.perry/events.jsonl` and the six stores; `BOARD.md` deleted; no `OKR.md`.

| command | result |
|---|---|
| `perry-state --json --root <p>` | exit 0, **`installed: true`**, no first-time-setup warning. So `work/SKILL.md § Bootstrap` as rewritten is **not triggered** |
| `lib.resolve_project_root(None)` from inside it | the project root; `configured` True; state root `<p>/perry` |
| `perry-task list --root <p>` | exit 0 (200 of 434 rows, default bound; `open_total` 98) |
| `perry-explain TASK-391 --root <p>` | exit 0, 702 B, typed store read |
| `perry-lint --root <p>` | exit 1: **one** error, `BOARD.md [missing-file]` (§ 3.4, schema), and 16 warnings |
| `perry-tasks render --root <p>` | exit 1, 0 bytes (§ 2.5) |

**The test fixture**, `tests/test_board_less_project_is_recognised.py`:
`.perry/config.jsonl` (state root `perry`) and `perry/tasks.jsonl` with one open
row, and nothing else. `setUp` refuses the fixture if a `BOARD.md`, `OKR.md`,
`phase` or `design` exists anywhere in it, or a `BOARD.md` / `OKR.md` in any
ancestor. Result: **9 of 9 sites recognise it.**

## 4. Mutations

Method, once for every row. Apply one edit, anchored by a unique enclosing
`def` or a string that occurs once in the file; the runner prints the resolved
`file:line`. Clear every `__pycache__`. Run the **whole** `bash tests/run`, one
mutation at a time, in the foreground. Restore the original bytes and check the
sha256. Before each mutation the runner refuses to start unless `git status`
shows only the untracked probe and no test process of this worktree is alive.

**The run was interrupted once, and the recovery is part of the record.** The
first runner recorded run 0 and M-A1, then stopped supervising while M-A2's
suite was still running. The process was still alive, with `bin/lib/__init__.py`
still mutated. A killed runner never reaches its restore, so the file was
restored from `HEAD` with `git checkout -- bin/lib/__init__.py`; the D2 commit
did not touch it. Its 11 orphaned suite processes, rooted at `tests/parallel`
pid 86971, were killed by PPID. A second `tests/parallel` tree alive on the
machine belonged to another agent's runner and was left alone. M-A2 through M-V
were then re-run in the foreground on the same tree state as run 0.

**Tree state for every run below:** HEAD `1d30f84d`, with
`tests/task237_board_skeleton_probe.py` untracked. That
untracked file is the source of one baseline red that is not pre-existing,
`test_header_index_is_the_only_fold § test_the_uncovered_remainder_is_the_measured_one`,
and so is the `durations.json` red for the new module. Both are fixed after the
mutation pass (§ 5), and neither can mask a mutation, because each mutation is
judged by the reds it **adds** to run 0.

**Run 0 (no mutation):** exit 1, 3 of 132 modules red, 4 of 3,847 tests
failed. Those four are the baseline: the three pre-existing reds of § 5 and the
census red caused by the untracked file. In every row below, "added" means
tests failing that did not fail in run 0. No mutation made a run-0 red pass.

| # | mutation (resolved `file:line`) | suite | added reds: **the named guard first** | verdict |
|---|---|---|---|---|
| M-A1 | `viewer/parsers.py:578` `configured(d)` → `False` | 5 mod / 6 tests | **`test_board_less_project_is_recognised § test_the_parsers_walk_finds_the_project_from_below_its_state_root`**; `test_project_root_resolution § TestTheCwdWalkMatchesPerryStates.test_standing_in_a_subdirectory_both_walk_up_to_the_project_root` | RED |
| M-A2 | `bin/lib/__init__.py:540` `_parsers().configured(d)` → `False` | 4 / 5 | **`§ test_the_lib_walk_finds_the_project_from_below_its_state_root`**, and nothing else | RED — **the new module is the only guard** |
| M-A3 | `bin/perry-state:2596` `P.configured(d)` → `False` | 6 / 7 | **`§ test_perry_state_walks_to_the_project_from_below_its_state_root`**; `test_config_store_readers § test_the_walk_finds_a_store_only_project_from_a_subdirectory`; `test_project_root_resolution § test_standing_in_a_subdirectory_both_walk_up_to_the_project_root` | RED |
| M-A4 | `bin/perry-state:1828` `P.configured(perry_root)` → `False` | 7 / 15 | **`§ test_perry_state_calls_it_installed`**, `§ test_perry_state_walks_to_the_project_from_below_its_state_root`; `test_config_store_readers § test_the_installed_gate_counts_a_store_only_project_as_installed`; 5 × `test_escalation_union`, 2 × `test_role_cards` | RED |
| M-A5 | `bin/perry-lint:5883` (walk) `P.configured(d)` → `False` | 4 / 5 | **`§ test_the_linter_walk_finds_the_project_from_below_its_state_root`**, and nothing else | RED — **the new module is the only guard** |
| M-A6 | `bin/perry-lint:4905 § is_adopted` `P.configured(project_root)` → `False` | 10 / 36 | **`§ test_the_linter_calls_it_adopted`**, `§ test_the_linter_walk_…`; `test_config_store_readers § test_the_linter_calls_a_store_only_project_adopted`; 11 × `test_escalation_union`, 10 × `test_spec_scannability`, 2 × `test_store_drift`, 2 × `test_work_modes`, 1 × `test_ns_collision` | RED |
| M-A7 | `bin/perry-explain:662` `configured(root)` → `False` | 5 / 14 | **`§ test_explain_reads_the_task_store`**; 4 × `test_explain_typed_tasks § TypedTaskLookup` | RED |
| M-A8 | `bin/perry-diagnose:1480` `"config": P.configured(root)` → `False` | 5 / 6 | **`§ test_diagnose_calls_it_installed`**; `test_config_store_readers § test_scan_tracking_calls_a_store_only_project_configured` | RED |
| M-A9 | `bin/perry-diagnose:2611` `is_perry = P.configured(root)` → `False` | 5 / 6 | **`§ test_diagnose_treats_it_as_perry`**; `test_config_store_readers § test_is_perry_counts_a_store_only_project_as_perry` | RED |
| M-V | M-A6's edit **plus** `perry/BOARD.md` written into the fixture (`tests/…recognised.py:122`) **plus** both anti-vacuity asserts disabled (`:130`, `:133`) | 10 / 37 | **`§ test_the_linter_calls_it_adopted` is NOT among them: GREEN.** Added: the three walk tests (`parsers`, `lib`, `linter`), each now stopping at `perry/` because it holds a `BOARD.md`; `test_config_store_readers § …adopted`; and the other modules M-A6 already reddened | **GREEN on the guarded test, as designed** |

**The one green is the point of M-V.** Under M-A6, with the fixture as shipped,
`test_the_linter_calls_it_adopted` is red. Give the fixture a sibling disjunct
and remove the `setUp` gate, and the same mutation of `is_adopted` leaves that
test green: the `BOARD.md` disjunct answers in `configured`'s place. That is the
OR-chain blindness `setUp` refuses. With the gate in place, M-V's fixture could
not have run at all.

**§ 3.2's "none", backed by these runs.** M-A2 and M-A5 redden **only** the new
module's test. With that module absent, reverting `configured(d)` at A2 or A5
would have left the suite at run 0's reds. Every other mutation also reddens at
least one pre-existing module, named in its row. So before this row, A1, A3,
A4, A6, A7, A8 and A9 were already guarded by a pre-existing test, and A2 and A5
were not. I did not check whether those pre-existing fixtures are board-less;
the mutation result is the claim, not the fixture's shape.

Mutation logs: `mut-<ID>.log` in the scratch run directory. They are not
committed; each row's added reds above are copied from them by a script, not by
hand.

**The spec's verification 3 was not run as written.** "Reorder one declared
heading, drop one optional column, corrupt one record: each reddens a named
test" is the mutation plan for a delivered renderer, and none was delivered.
Two of the three would mutate `schema/state-schema.json`, which is hard limit 2.

## 5. The suite

`bash tests/run`, whole, `__pycache__` cleared first, nothing else writing to
the worktree. The tree guard reported "nothing … moved" both times.

| | baseline, `02825582`, before any edit | final, the committed tree |
|---|---|---|
| exit | 1 | 1 |
| modules red | 2 of 131 | **2 of 132** |
| tests failed | 3 of 3,838 | **3 of 3,847** (+9: the new module, all passing) |

**Every red in the final run is pre-existing,** present in the baseline and
reproduced alone before any edit (`python3 -m unittest tests.<module>`):

- `test_contract_key_parity § TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`
  — alone: 2 of 35 failed
- `test_contract_key_parity § TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness`
- `test_resume § TestStaleRuns.test_a_fresh_run_is_not_stale` — alone: 1 of 49
  failed. Clock-dependent by its own docstring ("The fixture's own dates are NOT
  used for this")
- the durations drift lines `not in durations.json: test_asks_list.py` and
  `test_contract_page_snippets.py`, both modules added on `main` before
  `02825582` without an entry

**Two reds this row introduced, and removed, before the final run:**

- `test_header_index_is_the_only_fold § test_the_uncovered_remainder_is_the_measured_one`.
  The probe first sat at `perry/evidence/2026-09/`, where the header-fold
  census counts it as a product reader holding a row (`cmd_accounting`).
  Moved to `tests/task237_board_skeleton_probe.py`, beside
  `sweep_blank_cell_sites.py` and `mutate_blank_cell.py`. `tests/` is in
  `tests/header_rule.py § NOT_A_READER` for exactly this kind of file. The
  module alone afterwards: 9 of 9 OK.
- `not in durations.json: test_board_less_project_is_recognised.py`. Added,
  timed alone three times at 0.79/0.89/0.80 s and recorded at the median, with a
  source block `2026-09-14-task237`, on the terms of `2026-09-12-task439`. The
  diff is one module entry and one source block.

## 6. Rows this work names (none minted)

- **TASK-0NN (a):** USER-931's byte-identity acceptance cannot be met from the
  declarations. Choose § 2.6 option 1, 2 or 3. Blocks deliverable 3.
- **TASK-0NN (b):** every `perry-task` write refuses on a board-less project
  (`bin/perry-task:8720`), for D1's cause. Deliverable 3 cannot run until the
  writers stop filling lines in a file.
- **TASK-0NN (c):** `files[id=board].required: true` makes a board-less project
  lint red. Deleting the file requires that schema edit, which is high-stakes.

## What I did not check

- **Two processes flagged by the mutation runner's preflight, and whose they
  were.** Before M-A6, pid 22821 (a zsh wrapper) and pid 25555
  (`python3 -m unittest test_add_refuses_without_an_answer`) matched the
  preflight's filter. Both had exited before their ancestry or cwd could be
  read. `git status` was unchanged, and every mutation's suite has its own tree
  guard, which reported nothing moved. But I cannot say they were not running in
  this worktree.
- **Whether the first cleanup touched another session.** The first attempt to
  stop the orphaned suite used `pkill -f 'agent-a00cb81588fef0c24/tests/'` and
  `pkill -f 'agent-a00cb81588fef0c24/bin/perry'`. Both patterns name this
  worktree's path, but another session running a subprocess against this
  worktree's `bin/` would have matched them. The second cleanup killed by PPID
  from pid 86971 only, and it left the other agent's `tests/parallel` tree
  (under its own `mutate.py --suite`) alone.
- **The mutation pass on the final tree.** Every mutation ran on `1d30f84d`
  plus the untracked probe under `perry/evidence/`. The only differences from
  the committed tree are the probe's location (it has nothing to do with a
  detection site), two docstring paragraphs of the new test module, and one
  `durations.json` entry. None of the nine guarded tests changed. They were not
  re-mutated after those changes.

- **gimegime-pmo and PolyForge themselves.** § 3.2's reason for keeping the
  `BOARD.md` disjunct rests on ADR-010's description of them and on the
  markdown-only test. I did not open either project to count whether it has a
  `.perry/config.jsonl` today.
- **Whether `Last updated` (L3) is derivable** from `.perry/events.jsonl` (the
  date of the last board-writing event). If it is, L3 moves from "undeclared" to
  "derived". I did not test that equality, so L3 stays in § 2.3.
- **The prose rewrite on a live agent session.** It was read, not run: no agent
  was started in a board-less project to watch the lane trigger.
- **The probe's `open` guard under mutation.** The accounting mode's `cmp`
  equality on a copy with no `BOARD.md` shows that mode never needed the file.
  I did not mutate the probe to open the file to watch exit 3.
- **Localised boards.** The probe and the accounting only resolve English
  headings (`^User Input Queue`, `^Top risks`). The Chinese fixture was not measured.
- **`perry-viewer`, `perry-goals`, `perry-decide`, `perry-knowledge`,
  `perry-context-budget`:** they resolve the root from `$PERRY_PROJECT` or the
  cwd with no walk, and so have no `BOARD.md` detection to change. Their help
  text says "else walk up from cwd", which the sweep found untrue. That is
  unrelated to this row, and no row was filed for it.
