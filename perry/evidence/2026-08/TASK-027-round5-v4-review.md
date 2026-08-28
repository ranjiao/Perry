# TASK-027 — round-5 V4 review (lane rename `goals`/`work`/`decide` + aliases)

> Reviewer: fresh-context agent, 2026-08-18. Rubric: `perry/evidence/2026-08/TASK-027-spec.md`.
> Prior round read and distrusted: `perry/evidence/2026-08/TASK-027-round4-review.md`.
> Baseline on `feat/work-modes`, re-taken at the end of the round against
> `3f6b95d`: `python3 tests/parallel` → **37 modules · 1322 tests · green**;
> `python3 bin/perry-lint` → **clean, exit 0**. **Neither sees any finding below.**
>
> All mutations were run on copies at
> `…/scratchpad/perry-copy` (tree as of ~17:50) and `…/scratchpad/perry-copy2`
> (tree as of 18:2x, after `3f6b95d`). The project under review was not
> modified; this file is the round's only write.
>
> **The tree moved under this round.** Four commits landed while I was working
> (`3c36ec1`, `b658329`, `8028371`, `f434486`, `3f6b95d`), plus uncommitted edits
> to `bin/perry-explain` and `work/SKILL.md` from a concurrent session. Every
> finding below was re-verified against the tree at `3f6b95d`, and the B-1
> mutation was re-run on a fresh copy of it: **still green with both viewer
> mutations in place** (37 modules · 1322 tests · rc 0).
>
> **Verdict: FAIL.** Two blocking findings. Both are the same category the row's
> `next_action` names — *the rename reached the documents a reviewer reads and
> not the artifacts a user receives* — and both live in surfaces that are in
> **neither** the carve-out's exempt list **nor** the guard's enforced list.

---

## 1 · The category, enumerated

The row's `next_action` asks for the category, not a list. The category here is
**"every shipped surface where a lane name reaches a human with no agent step
left to translate it."** So I enumerated the shipped tree top-level and asked of
each directory: is it *exempted* by `SKILL.md:40`, is it *enforced* by
`tests/test_shipped_vocabulary.py`, or is it in **neither** list?

`WITHDRAWN` below is the guard's own pattern
(`tests/test_shipped_vocabulary.py:88`), applied by me over the whole tree
(`.git`, `__pycache__` and the agent worktrees under `claude/` excluded).

| Shipped path | `WITHDRAWN` lines today | Exempt by `SKILL.md:40` | Enforced by `test_shipped_vocabulary` | Verdict |
|---|---:|---|---|---|
| `SKILL.md` | 2 | no | yes (`TestTheRouterAndTheInstallerAreTypeable`) | both excused as historical notes — OK |
| `setup` | 1 | no | yes (same class) | excused historical note — OK |
| `bin/` | 1 | no | yes (`--help` executed on all 16 tools; AST over the 10 Python tools) | the one hit is `bin/perry-state:739`, a **function** docstring — correctly exempt, never printed |
| `goals/`, `work/`, `decide/` SKILL.md bodies | 23 / 80 / 8 | **yes** | frontmatter `description:` only | OK |
| `*/reference/` | (in the above) | **yes** | no | OK |
| `packs/` | 24 | **yes** | pointer resolution only | OK |
| `reference/` (shared root) | 7 | **yes** | `host-capabilities.md` only, which is clean | OK — but see M-2 |
| `*/state/`, `state/` | 0 | no | yes (`TestShippedTemplatesAreTypeable`) | OK |
| `README.md`, `README_cn.md` | 0 | no | yes (`TestEveryCommandTheReadmeShowsExists`) | OK |
| `INSTALL.md` | 0 by this pattern | no | `tests/test_entrance.py` | out of scope (TASK-028) — see § 5 |
| `AGENTS.md` | 0 | no | no | clean today |
| `modes/` | 0 | **no** | **no** | in neither list — m-1 |
| `schema/` | 0 by this pattern | **no** | **no** | in neither list — m-1 |
| `templates/` | 0 | **no** | **no** | in neither list — m-1 |
| **`viewer/`** | **16** | **no** | **no** | **B-1** |

`TestTheCarveOutSaysWhatThisFileEnforces` pins the prose carve-out to the test
file, so the two lists cannot disagree. **Nothing checks that their union covers
the tree**, and that is exactly how `viewer/` — 16 lines, 7 files, a browser page
and a README addressed to "non-technical users" — sits outside both.

---

## BLOCKING

### B-1 · `viewer/` is a shipped user-facing surface the rename never reached, and no test can see it

`viewer/` ships inside `$PERRY_HOME` (`bin/perry-viewer:23` —
`VIEWER_DIR="$PERRY_HOME/viewer"`), is started from chat by a subcommand `work`
declares (`work/SKILL.md:35`, `:106`), and `work/SKILL.md:94` calls it a **tier 3
consumption surface**. Its output is HTML in a browser and its README is
addressed to end users. Seven withdrawn commands are shipped in it.

**The rendered page — proved by rendering it, not by reading it.**
`viewer/templates/architecture.html:16` is inside the `{% if not exists %}`
branch that `viewer/serve.py:208-222` takes for every project with no
`ARCHITECTURE.md` — i.e. every project before `architecture init` is ever run.
Rendered with `serve.py`'s own template filters stubbed:

```
$ python3 - <<'EOF'   # jinja2 3.1.6, loader = viewer/templates
  ... render architecture.html with exists=False ...
RENDERED /architecture HTML — lines naming a withdrawn command:
  line 94: <div class="card"><div class="t-muted">No ARCHITECTURE.md at the project
           root. It's lazy-created on first <code>/pmo architecture init</code>.</div></div>
```

`/pmo architecture init` is printed into the page in a `<code>` block, which is
the strongest possible "type this" signal a web page has. The live form is
`/perry work architecture init` (`work/SKILL.md:261`).

**The README.** `viewer/README.md`, six hits, five of them imperative:

```
19: **Easiest (no shell needed):** just ask the agent — **`/pmo viewer`** (alias
20: `/pmo browse`). It starts the server in the background, waits until it's up
22: with `/pmo viewer stop`. This is the recommended path for non-technical users;
68: Read-only by deliberate choice — every mutation goes through `/pmo`,`/okr`,
69: `/design` in chat. …
```

Line 22 says in so many words that this is *the recommended path for
non-technical users*, and line 68-69 says "in chat" — there is no reading of the
carve-out under which these are agent routing vocabulary. Live forms:
`/perry work viewer`, `/perry work browse`, `/perry work viewer stop`,
`/perry work` · `/perry goals` · `/perry decide`.

The spec's own out-of-scope names `README.md`, `README_cn.md` and `INSTALL.md`
and **nothing else**; `viewer/README.md` is not among them, and rubric item 2
says user-facing strings including READMEs must be current.

**Mutation — the guard is not merely missing these, it cannot see the class.**
A *fresh* withdrawn command inserted into the body of every viewer page:

```
inserted after viewer/templates/base.html:70 (inside <body>, below {% block content %})
  <div class="banner">No board yet — run <code>/pmo triage</code> in chat, or <code>/okr score</code>.</div>
  → full suite: 36 modules · 1310 tests · GREEN
```

```
inserted after viewer/README.md:34
  Ask the agent `/pmo triage` or `/okr score` at any time.
  → full suite: GREEN
```

For contrast, the same string on each class the repair *did* claim goes red, and
every one was reverted and re-run green:

| Mutation | Result | Test that caught it |
|---|---|---|
| `work/state/BOARD_TEMPLATE.md:6` → `` `/pmo dispatch …` `` | RED | `TestShippedTemplatesAreTypeable.test_no_shipped_template_writes_a_withdrawn_command_into_a_project` |
| `setup:588` banner → `/perry okr … · /perry pmo …` | RED | `TestTheRouterAndTheInstallerAreTypeable.test_the_setup_banner_names_the_three_live_lanes_and_no_others` |
| `bin/perry-dispatch-limit:25` (bash `--help`) → `/pmo dispatch` | RED | `TestEveryShippedToolsHelpIsTypeable.test_no_tools_help_output_names_a_withdrawn_command` |
| `goals/SKILL.md:3` `description:` → `/okr …` | RED | `TestLaneFrontmatterDescribesALaneNotACommand.test_no_description_promises_a_withdrawn_command` |
| `reference/host-capabilities.md:62` `/perry`→`/pmo` | RED | `TestHostCapabilitiesNamesTheOneLiveEntrance.test_the_page_uses_no_withdrawn_command_anywhere` |
| `SKILL.md:25` alias map scrambled to `okr → work` | RED | `TestLaneAliases.test_the_command_surface_shows_the_alias_map` |

So the guard is real for its declared classes and blind to this one. This is the
round-4 shape repeated one level up: round 4 quoted `bin/` strings and the repair
guarded `bin/`; round 5 quoted `--help` and the repair guarded `--help`. Nobody
enumerated *which shipped trees exist*.

`tests/test_router_budget.py:39` is corroborating: its
`SHIPPED_DIRS = ("reference", "modes", "packs", "schema", "templates")` also
omits `viewer/`. `viewer/` is missing from the repository's shipped-surface
accounting generally, not just from this guard.

### B-2 · Printed strings still name the lane `PMO`, including the `help` output deliverable 3 names by name

The repair already accepted that a bare `PMO` noun is in-category — it added
`TestShippedTemplatesAreTypeable.test_the_decisions_header_does_not_attribute_the_file_to_pmo`,
which asserts `assertNotRegex(text, r"\bPMO\b")`. It pinned that assertion to
**one file's first six lines**. `\bPMO\b` is not in `WITHDRAWN`, so nothing else
in the tree is checked for it, and two live instances remain:

**(a) `bin/perry-lint:881-882` — a `Finding` printed to the user.** The guard's
own docstring says `perry-lint` fills `Finding.message` and
`reference/i18n.md § chat output` sends it straight to chat. Reproduced on a
copy of the shipped fixture, **no mutation**:

```
$ cp -R tests/fixtures/sample-project $SCRATCH/lintproj
$ printf '# DESIGN-003 — x\n\n> Status: locked\n\n## 6. Implementation plan\n\n## 7. Next\n' \
    > $SCRATCH/lintproj/design/DESIGN-003-x.md
$ python3 bin/perry-lint --root $SCRATCH/lintproj
  ✗ design/DESIGN-003-x.md [locked-design-has-plan] Status: locked but the
    Implementation plan section is empty — PMO has nothing to open tasks from
```

`PMO` is a lane that no longer exists; the owner of that hand-off is `work`.

**(b) `reference/router-subcommands.md:117` — inside the `/perry help` output
block.** Deliverable 3 requires "`SKILL.md`'s lane table, routing reference, and
**`help` output** updated". `:92-94` introduces the block as `Suggested format:`
followed by a fence — it is text to be printed, not prose to be re-rendered:

```
  /perry decide <sub>    Design-doc / RFC / decision stewardship (alias: /perry design) …
            Use when: drafting an RFC, locking user decisions, handing off
            implementation tasks to PMO.                       ← :117
```

The page sits in the shared root `reference/`, which the carve-out exempts — but
the carve-out's escape hatch is *"Translate it only when quoting a **command**
back to the user."* `PMO` is not a command, so an agent obeying the carve-out
literally prints it verbatim. The three live lane words are already spelled
correctly on `:104`, `:110`, `:116` of the same block, so this is a miss, not a
choice.

---

## MAJOR

### M-1 · `templates/`, `modes/` and `schema/` are in neither list either

Same hole as B-1, no live instance today, which is the only reason they are
MAJOR rather than blocking. `templates/` is the more serious of the three:
`templates/README.md:5` says *"The prescribe and execute stages of
`/perry diagnose` copy from here"*, i.e. these files land **in the user's own
repository** exactly like `*/state/*_TEMPLATE.md` — the class B-2 of round 4 was
raised for — and they are not covered by
`TestShippedTemplatesAreTypeable.template_files()`, which globs only
`*/state/*.md` and `state/*.md`. Mutations, full suite:

```
templates/software/STATE.md  + "> Triage the board with `/pmo triage`."   → GREEN
modes/project.md             + "> Run `/pmo triage` to sort the board."    → GREEN
```

### M-2 · The guard's `bin/` coverage is `--help` for all tools but source-scan for Python only

`TestBinPrintsOnlyLiveCommands.python_tools()` filters on a `python` shebang, so
the five `bash` tools are scanned **only** through their `--help` output. Any
other string a bash tool prints is unguarded:

```
bin/perry-viewer, after :43   echo "Start it from chat with /pmo viewer instead." >&2   → GREEN
```

No live instance today (I scanned all 16 executables), so this is a shape defect
rather than a defect. It matters because `bin/perry-viewer:43,57,72,75,78,81,85`
already print a column of user-facing messages that no test reads.

---

## MINOR

- **m-1 · Nothing asserts that "exempt ∪ enforced = the shipped tree."**
  `TestTheCarveOutSaysWhatThisFileEnforces` pins the two lists to each other and
  is well built; it cannot notice a directory absent from both. A test that
  walks the top level of `$PERRY_HOME` and requires each entry to be named by one
  list or the other would have caught B-1, M-1 and any future `viewer/`.

- **m-2 · Rubric item 2's artifact is still not in evidence.** The row's
  `evidence_paths` is `["perry/evidence/2026-08/TASK-027-spec.md"]` — the spec
  and nothing else. The spec says *"The audit output is the evidence; list what
  was intentionally left."* `SKILL.md:40` plus the test file's docstring are a
  defensible substitute for the list, and I would have accepted them — except
  that the list they give is the one that omits `viewer/`, `templates/`, `modes/`
  and `schema/`. Round 4 filed this as m-6 and the substitute inherited the same
  gap.

- **m-3 · Rubric item 1 has no executable fixture.** There is no alias fixture
  anywhere under `tests/`; `TestLaneAliases` says outright *"the router is prose
  — so what is testable is that the router documents every alias."* I accept
  that: routing is an LLM reading `SKILL.md`, and there is nothing to call. The
  substitute does check the pairing, and I broke it to confirm — scrambling
  `SKILL.md:25` to `okr → work · pmo → goals` goes RED. All six names are covered
  (three new via `$PERRY_HOME/<lane>/SKILL.md` existence, three old via the
  `old → new` map). Recording it so the next round does not go looking for a
  fixture that cannot exist.

- **m-4 · `viewer/parsers.py:517`** (class docstring, `` `okr plan-phase` ``) and
  **`viewer/serve.py:1`** (module docstring, *"a project's PMO state"*) are
  internal and not printed. Listed for completeness; not defects.

- **m-5 · `tests/test_decoration_changes_nothing` was flaky, and is now fixed —
  recorded because it cost this round two mutation results.** On my 17:50 copy it
  went red 1 run in 3 on an **unmutated** tree
  (`test_every_reader_reports_the_same_thing_on_a_bolded_board (reader='perry-state')`),
  which made a GREEN mutation read as RED twice before I isolated it by re-running
  the clean copy. `8028371` (18:08, `generated_at` unscrubbed) is the fix; four
  consecutive runs on the current tree are green. No action — the entry exists so
  a later round reading this document's mutation table knows why two rows there
  needed a retry.

- **m-6 · Withdrawn.** My first run reported `35 modules · 1304 tests · green`
  and later runs reported 36 then 37. I recorded this as a possible discovery
  gap in `tests/parallel`; it is not. `tests/test_rung_vocabulary.py` and one
  other module were added by a concurrent session at 18:16 and 18:2x. The runner
  is fine. Left in place rather than deleted because "the count changed" is
  exactly the observation a later round would re-make, and it should find the
  answer here.

---

## What holds (checked, and where it was broken to confirm)

| Rubric item | Status |
|---|---|
| D1 — `okr`/`pmo`/`design` → `goals`/`work`/`decide` on disk | Pass. No `okr/`, `pmo/`, `design/` at `$PERRY_HOME`; git rename history at `29efa6b` is complete and `a22e693` moved the two ADR templates into `decide/state/`. |
| D2 — permanent aliases at the router | Pass, mutation-verified (`SKILL.md:25`, `:34-36`). |
| D3 — lane table, routing reference, `help` output | **FAIL** — B-2(b), `reference/router-subcommands.md:117`. Table and routing reference themselves are current. |
| D4 — lane frontmatter `name:` **and** `description:` | Pass, mutation-verified on `goals`. All three name `/perry <lane>`, say "not a separate command", and no longer call a sibling lane a skill. Round-4 M-2 closed. |
| V4-1 — alias fixture, six names | Pass in substance; see m-3. |
| V4-2 — audit of `/pmo `/`/okr `/`/design ` | **FAIL** — B-1, B-2; and m-2 on the artifact. |
| V4-3 — no lane gained or lost a file vs the TASK-026 contract | Pass. Lane trees match `reference/hand-off-contract.md`; the only cross-lane moves in history are the contract-mandated `ADR_TEMPLATE.md` / `DECISIONS_TEMPLATE.md` → `decide/state/` and the `pmo/reference/decisions.md` → `decide/reference/` move. |
| Round-4 B-1 (`bin/` printed withdrawn commands) | Closed and guarded — `/perry decide adr --expire` pinned, `--help` executed on all 16 tools. |
| Round-4 B-2 (14 template occurrences) | Closed and guarded, mutation-verified. |
| Round-4 B-3 (`reference/adoption.md` commit table) | Closed — `:272` now routes `decisions/ADR-NNN-*.md` to `/perry decide adr`; the whole table at `:266-275` is in `/perry <lane> <sub>` form. |
| Round-4 M-1 / M-3 / M-4 | Closed; `TestLaneReferencePointersResolve`, `TestPackPointersResolve` and the widened router matcher all present and non-vacuous. |

---

## 5 · What I did not check

- **The `okr` / `design` HTTP routes.** `viewer/serve.py:191,237`,
  `viewer/templates/base.html:46-47`, `design.html:39,45`, `phase.html:52-53`
  and `viewer/README.md:50` name `/okr` and `/design` as **URL paths and nav
  labels**, not chat commands. I judged that a different namespace and did not
  fail the row for them — but I also did not establish that the task intended to
  leave them, because nothing in the spec, the router or the guard says either
  way. If they were meant to move, that is a seventh-through-fourteenth instance
  of B-1 and someone should say so in writing.
- **`schema/state-schema.json:114` `"PMO Agent"`** (the `owner` enum, which is
  copied into `work/state/evidence_TEMPLATE.md:12`, `journal_TEMPLATE.md:23`,
  `weekly_TEMPLATE.md:5`, `handoff_TEMPLATE.md:89,99` and
  `goals/state/phase_TEMPLATE.md:76`) and **`.perry/config.md`'s `PMO repo path`
  field**, resolved at `bin/perry-state:115` and documented at
  `reference/config.md:47`. Both are *data keys and role labels*, not lane
  routing, and the spec puts rendered display vocabulary in TASK-025 and out of
  scope. I did not treat them as this row's, and I did not verify that TASK-025
  actually covers them.
- **`INSTALL.md`.** Out of scope by the spec (TASK-028), so not graded — but it
  is worse than the READMEs were, and TASK-028 should know: `:3` still opens
  *"Perry is a four-skill set"*, `:88-89`/`:148-149` draw `okr →`/`pmo →`
  symlinks that `setup` now deletes, `:114`/`:170` tell the reader to
  `grep -E '^(perry|okr|pmo|design)$'` and "expect all four", `:118` and
  `:161-162` list four skills and four `$`-mentions, and `:200-202` show
  `/perry okr init` / `/perry okr plan-phase`.
  `tests/test_entrance.py:84`'s `(?<!perry )` lookbehind exempts every one of
  those forms.
- **aiMark** (`~/proj/aimark`), which `work/SKILL.md:94` names as the *primary*
  tier-3 consumption surface. It is outside this tree and I did not open it. If
  it renders lane names, it is in the same category as B-1.
- **The viewer end to end.** Flask is broken in this machine's system Python
  (`werkzeug.urls.url_quote` ImportError), so I rendered
  `viewer/templates/architecture.html` through jinja2 directly with `serve.py`'s
  filters stubbed rather than starting the server. The `{% if not exists %}`
  branch and `serve.py:208-222`'s `exists=arch_path.exists()` were read to
  confirm the branch is the default one; the HTTP path itself was not exercised.
- **Chinese surfaces** beyond confirming `README_cn.md` carries no `WITHDRAWN`
  hit and is covered by `TestEveryCommandTheReadmeShowsExists`. I did not audit
  `tests/fixtures/sample-project-zh/`, `reference/i18n.md`'s rendered strings, or
  any translated lane vocabulary.
- **Any Windows or non-macOS path**, and `setup` was never run (standing
  constraint).
- **Round-4's m-4 pack-pointer and section-citation claims** beyond confirming
  `TestPackPointersResolve` exists, is non-vacuous, and is green. I did not
  re-enumerate the pack pointers by hand.

---

## What would make this pass

1. **B-1** — rewrite `viewer/templates/architecture.html:16` to
   `/perry work architecture init`, and `viewer/README.md:19, 20, 22, 68, 69` to
   `/perry work viewer`, `/perry work browse`, `/perry work viewer stop`,
   `/perry work` · `/perry goals` · `/perry decide`.
2. **B-2** — `bin/perry-lint:882` → name `work`, not `PMO`;
   `reference/router-subcommands.md:117` → "handing off implementation tasks to
   `work`". Widen the guard's pattern to `\bPMO\b` over the enforced classes
   instead of the one file it is pinned to today.
3. **The category, not the list** — add a test that walks the top level of
   `$PERRY_HOME` and requires every entry to be named either by `SKILL.md:40`'s
   carve-out or by a class in `tests/test_shipped_vocabulary.py`, and extend the
   scanned set to `viewer/`, `templates/`, `modes/` and `schema/`. Without it,
   the fourth surface will be found by a seventh round.
4. **M-2** — scan bash tools' whole source, not only their `--help`.
5. **m-2** — land the audit output under `perry/evidence/` and add it to the
   row's `evidence_paths`, with the exempt list stated as a partition of the
   tree.

=== VERDICT ===
task: TASK-027
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-027-spec.md
checked: category enumerated as a partition of the shipped tree (17 top-level
         paths classified exempt / enforced / neither); 6 guarded classes broken
         and confirmed red then reverted green; 4 unguarded classes broken and
         confirmed GREEN on the full suite (re-run at 37 modules · 1322 tests); /architecture page
         rendered through jinja2; perry-lint reproduced on a fixture copy with
         no mutation; D1-D4 and V4-1/V4-3 each checked; round-4 B-1/B-2/B-3 and
         M-1/M-3/M-4 confirmed closed
not-checked: viewer HTTP route + nav-label namespace (/okr, /design as URLs);
         schema "PMO Agent" owner enum and .perry/config.md "PMO repo path"
         field key (judged TASK-025 display vocabulary); INSTALL.md (TASK-028,
         but it still advertises four skills at :3,:88-89,:114,:118,:148-149,
         :161-162,:170,:200-202); aiMark; the viewer served over HTTP (Flask
         broken in system python); Chinese surfaces beyond README_cn.md; any
         Windows path; setup never run
proof: viewer/templates/architecture.html:16 prints `/pmo architecture init` into
         the rendered /architecture page, and viewer/README.md:19 tells
         "non-technical users" to type `/pmo viewer` — a fresh withdrawn command
         inserted at viewer/templates/base.html:70 and viewer/README.md:34 left
         the full suite green, so the class is unguarded, not merely missed.
         Second site: bin/perry-lint:882 prints "PMO has nothing to open tasks
         from" to the user, and reference/router-subcommands.md:117 prints "PMO"
         inside the `/perry help` output that deliverable 3 names.
=== END VERDICT ===
