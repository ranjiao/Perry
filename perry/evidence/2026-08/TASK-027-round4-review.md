# TASK-027 — round-4 V4 review (lane rename + aliases)

> Reviewer: fresh-context agent, 2026-08-17. Rubric: `TASK-027-spec.md`.
> Baseline: 600 tests OK, `perry-lint` clean. **Neither sees any finding below.**
>
> **Verdict: FAIL.** Three blocking findings, all in the same place: *the rename
> was applied to the documents a reviewer reads and not to the artifacts a user
> receives.*
>
> Filed by the agent that received the report, at the reviewer's precision.

## What holds

| Rubric item | Status |
|---|---|
| D1 — directories renamed | Pass |
| D3 — router lane table / routing reference / help | Pass with residue (m-1) |
| D4 — lane frontmatter `name:` **and** `description:` | `name:` pass, `description:` **FAIL** (M-2) |
| V4-1 — alias fixture, all six names | Pass, mutation-tested |
| V4-3 — no lane gained or lost a file vs TASK-026 | Pass; only delta is the two templates moving `work/state/` → `decide/state/`, which the contract requires |
| V4-2 — audit of `/pmo `/`/okr `/`/design ` | **FAIL** (B-1, B-2, B-3, m-6) |

**Round 3's two blocking findings are genuinely closed and genuinely guarded.**
Each guard was reverted and confirmed to fail: the install-root directory list,
the alias map, the lane-directory existence check, and the withdrawn-command
scan.

## BLOCKING

### B-1 · Perry prints withdrawn commands to the user from `bin/`, and one names a subcommand the signed contract deleted

`bin/perry-state` builds the `warnings[]` array that `reference/i18n.md:23`
classifies as chat output and `work/SKILL.md:116` calls "a ready-made
`warnings` array". Reproduced against a shipped fixture, no mutation:

```
$ python3 bin/perry-state --json --root tests/fixtures/sample-project \
    | python3 -c "import json,sys;print(json.load(sys.stdin)['warnings'])"
['ADR-002 sunset criteria passed 16d ago — run /pmo decide --expire ADR-002.']
```

And from `perry-lint --json` on a project with an unarmed hook:

```
hook-high-stakes-armed :: no high-stakes operations list — /pmo dispatch's
safety re-validation and /pmo autopilot's safety scan have nothing to match against
```

Occurrences: `bin/perry-state:803` (`/pmo triage`), `:820` (`/pmo dispatch`,
`/pmo autopilot`), `:826` (`/pmo decide --expire`), `:833`
(`/pmo architecture review`); `bin/perry-lint:621-622`.

**`:826` is not fixable by alias translation.** `decide <topic>` was removed
from the `work` lane by the signed contract — `work/reference/subcommands.md:267`
tombstones it, and `work/SKILL.md:253` says *"`work` no longer writes
`DECISIONS.md` or `decisions/` at all."* So `/perry work decide --expire` is as
dead as `/pmo decide --expire`; the only live form is
`/perry decide adr --expire`. Perry is printing a command that exists in
neither the old nor the new vocabulary.

The shorthand carve-out does not cover this: `SKILL.md:41` scopes it to lane
SKILL.md files and `*/reference/`, and its escape hatch is *"Only translate it
when quoting a command back to the user."* `bin/` output **is** that quote,
already rendered, with no agent step left to translate it. Round 3 recorded this
exact defect and it was fixed only in the prose the reviewer read, not in the
code that generates the strings.

### B-2 · Withdrawn commands are written verbatim into every user's project via the shipped state templates

`work/reference/bootstrap.md:18` writes `BOARD.md` from
`state/BOARD_TEMPLATE.md`; `decide/reference/decisions.md:128,187-188,203-204`
writes ADRs and `DECISIONS.md` from the `decide/state/` templates. The text
lands in the user's repo and stays there. 14 hits across 9 templates:

- `work/state/BOARD_TEMPLATE.md:6` — `> Auto-dispatch a task: /pmo dispatch {{TASK-ID}}`
- `work/state/BOARD_TEMPLATE.md:9` — `> Hard cap: ≤200 lines. If you're over, run /pmo triage.`
  — these two sit at the top of every user's `BOARD.md`, the most-read file Perry produces
- `work/state/hook_TEMPLATE.md:5,9,11` — `/pmo`, `/okr`, `/design`; `/pmo dispatch`; `/pmo autopilot`
- `work/state/incidents_INDEX_TEMPLATE.md:10`, `runbook_INDEX_TEMPLATE.md:9`,
  `runbook_TEMPLATE.md:42,49`, `knowledge_INDEX_TEMPLATE.md:3`
- `decide/state/ADR_TEMPLATE.md:47` — `` run `/pmo decide --expire ADR-{{N}}` `` — the same doubly-dead command as B-1, stamped into every ADR with a sunset criterion
- `decide/state/DECISIONS_TEMPLATE.md:3` — `> Auto-maintained by PMO on every /pmo decide / status flip.`
- `state/diagnosis_TEMPLATE.md:54`, `state/adoption_dossier_TEMPLATE.md:17`

`ADR_TEMPLATE.md` and `DECISIONS_TEMPLATE.md` are **the two files this task
moved**. They were relocated and their contents were not read.
`DECISIONS_TEMPLATE.md:3` additionally asserts, inside the one file the signed
contract reassigned, that the lane which may no longer write it maintains it.

These files have **no guard of any kind**.

### B-3 · `reference/adoption.md:272` routes ADR materialization to a deleted subcommand, in the lane forbidden to write it

`reference/adoption.md:267-275`, the § 4 Commit table:

```
| `decision` | `decisions/ADR-NNN-*.md` | `/pmo decide` |
```

Two failures in one cell: the subcommand was deleted from `work`, and the row
assigns a `decide`-owned path to `work`, which `SKILL.md:114-116` names as one
of the three cases that must refuse. `/perry adopt` stage 4 on any project with
ADR candidates walks into it. The same table also carries `/okr init`,
`/okr plan-phase`, `/design new`, `/pmo add-task`, `/okr link`, `/pmo digest`,
`/pmo architecture init`, `/pmo risk` (lines 267-275, 383).

**Why no test catches it:**
`tests/test_ownership.py::test_no_lane_reference_page_instructs_a_write_it_may_not_perform`
iterates `(PERRY_HOME / lane / "reference").glob("*.md")` for the three lanes
only. The shared root `reference/` is outside the loop, and so are `modes/` and
`packs/`.

## MAJOR

### M-1 · `work/reference/extending.md:58` — the dangling `reference/decisions.md`, one instance of two

Inside the `work` lane this resolves to `work/reference/decisions.md`, which
does not exist (the file moved to `decide/reference/`). Round 3 recorded this
defect and repaired the sibling instance at
`work/reference/subcommands.md:273`; this one was not. The two bullets directly
above it already use the `$PERRY_HOME/…` absolute form.

### M-2 · Deliverable 4 half-done — no lane's frontmatter `description:` was updated

`name:` is correct in all three. `description:` was not touched:

- `goals/SKILL.md:3` — *"Use when the user invokes **/okr** … Hands off weekly task candidates to the **pmo skill**"*
- `work/SKILL.md:2` — *"Use when the user invokes **/pmo** … written by the **okr skill**"*
- `decide/SKILL.md:2` — *"Use when the user invokes **/design** … Hands off to PMO"*

Beyond the letter of the deliverable: these assert `/okr`, `/pmo`, `/design`
are things a user invokes and that `pmo` and `okr` are *skills*, both of which
`SKILL.md:14,16` state are false.
`tests/test_entrance.py::test_description_carries_each_lane_trigger_vocabulary`
grades only the router's description.

### M-3 · `packs/software-ops/` carries nine dangling relative pointers

```
incidents.md:41,93   MISSING `state/incident_TEMPLATE.md`   (real: work/state/…)
incidents.md:155     MISSING `state/incidents_INDEX_TEMPLATE.md`
runbooks.md:13,99    MISSING `state/runbook_TEMPLATE.md`
runbooks.md:94       MISSING `state/runbook_INDEX_TEMPLATE.md`
architecture.md:128  MISSING `dispatch.md § Pre-flight`     (real: work/reference/…)
architecture.md:189  MISSING `subcommands.md § close-task`
runbooks.md:53       MISSING `subcommands.md § close-task`
```

Before the pack extraction these resolved as siblings. This task modified both
files and did not repair them. These pages are what the `work` lane loads to
run `runbook-check`, `incident`, and the `close-task` gate, so every "create it
from the template at X" instruction points at nothing.

### M-4 · `test_the_router_does_not_tell_users_to_run_withdrawn_commands` is blind to four shapes, one already in the file

`tests/test_work_modes.py:870-878` skips any line where
`line.strip().startswith(">")` **or** `"shorthand" in line`, and matches only
`` `/okr ``, `` `/pmo ``, `` `/design `` — backtick, slash, name, trailing
space. Four withdrawn forms inserted into `SKILL.md` all passed unnoticed:

```
> Tip: run `/pmo triage` to see the board.          ← blockquote exemption
Or just type `/okr` for goals, or `/design`.        ← no trailing space
The standup is `pmo triage`; the ADR step is `design decide`.   ← no leading slash
```

The third shape is **not hypothetical** — `SKILL.md:677` already reads
`` (e.g., `okr score` …, `pmo triage` …, `design decide`) ``, and `:679`/`:686`
read `` `pmo dispatch` ``. The blockquote exemption is also broader than
intended: `SKILL.md:43` and `:53-64` are ordinary blockquotes carrying no
shorthand disclaimer.

## MINOR

- **m-1 · Router residue outside its own declared carve-out.** `SKILL.md:41`
  exempts lane SKILL.md and `*/reference/`; it does not exempt `SKILL.md`
  itself. Stale: `:316` "combining OKR, PMO, and design concerns", `:677`, `:679`,
  `:686`, `:744` "run by okr / design / pmo". `:704` in the same section *was*
  updated to `decide` — the inconsistency inside one section marks these as
  misses rather than choices.
- **m-2 · `work/SKILL.md:36`** still lists `decide` among the live subcommands
  `reference/subcommands.md` covers, while the index at `:242-267` omits it and
  `:253` tombstones it.
- **m-3 · `reference/okr-linkage.md:121`** cites `state/linkage_TEMPLATE.md`;
  from the shared root that resolves to a path that does not exist (real:
  `goals/state/linkage_TEMPLATE.md`). Same table's Skill column reads `okr` /
  `pmo` at lines 121-126.
- **m-4 · `packs/software-ops/architecture.md:216`** and
  `work/reference/subcommands.md:258` cite `goals/SKILL.md § plan-phase`. That
  section has never existed in that file, before or after the rename; the
  procedure is `goals/reference/phases.md`. The rename updated the path half of
  a citation whose section half was already wrong.
- **m-5 · `TestRouterNamesOnlyRealThings`'s docstring** claims *"Every directory
  and command the router prints must exist."* Its regex reads exactly one
  parenthetical. Every other directory the router names is ungraded.
- **m-6 · Rubric item 2** requires the audit output as evidence and a list of
  intentional leftovers; only the spec exists under `perry/evidence/`.
  `SKILL.md:41`'s class-level carve-out is a defensible substitute but silently
  omits `bin/`, `*/state/`, the shared root `reference/`, `packs/`, and the
  router itself — which is where every finding above lives.

## Informational

- **i-1** `README.md:111,253` and `README_cn.md:113,255` advertise
  `/perry pmo decide <topic>`. READMEs are TASK-028 by the spec's own
  out-of-scope, but this shows deliverable 2's promise ("the rename costs
  nothing at the command line") is not true in general: `pmo → work` resolves
  the lane and then dies on a subcommand that changed lanes.
  `tests/test_entrance.py:84`'s `(?<!perry )` lookbehind exempts precisely this
  form.
- **i-2** Two writers for `DECISIONS.md`'s header, already drifted:
  `decide/reference/decisions.md:187` says write it from the template (header
  attributes it to PMO), while `bin/perry-decide bootstrap` reads no template
  at all and emits a different header.

## What must change

1. **B-1** — rewrite the command strings in `bin/perry-state:803, 820, 826, 833`
   and `bin/perry-lint:621-622` to `/perry <lane> <sub>` form. `:826` must
   become `/perry decide adr --expire <ID>`. Verify with
   `python3 bin/perry-state --json --root tests/fixtures/sample-project`.
2. **B-2** — update the 14 occurrences in `*/state/*_TEMPLATE.md` and
   `state/*_TEMPLATE.md`. `decide/state/DECISIONS_TEMPLATE.md:3` must stop
   attributing the file to PMO. **Add a test over `*/state/*.md`** — these are
   user-delivered artifacts and have no guard.
3. **B-3** — fix `reference/adoption.md:267-275` and `:383`, routing
   `decisions/ADR-NNN-*.md` to `/perry decide adr`. Extend
   `test_no_lane_reference_page_instructs_a_write_it_may_not_perform` to cover
   the shared root `reference/`, `modes/` and `packs/`.
4. **M-1** — `work/reference/extending.md:58` → `$PERRY_HOME/decide/reference/decisions.md`.
5. **M-2** — update `description:` in all three lane SKILL.md files.
6. **M-3** — repair the nine pointers in `packs/software-ops/`.
7. **M-4** — narrow the two exemptions in `tests/test_work_modes.py:871` (match
   the shorthand disclaimer specifically, not every blockquote and every line
   containing the word) and widen the literal set to the no-trailing-space and
   no-leading-slash forms. Then fix what it newly reports (m-1).
