# TASK-096 — V4 review: the six exemptions

**Criteria** — the row's Deliverable (`perry-task list --json`, journal
`2026-08-19.md:183`): *"Audit every procedure in work/, goals/ and decide/
reference pages for a step that hand-edits a rendered file, and rewrite it as:
call the tool for fields, then generate the document from what it returned.
ADR-007 rule 3."* Verification: *"a fresh reviewer walks the procedures and
finds no step that edits a rendered file."*

**Under review** — `tests/test_procedures_call_the_tool.py` and the rewritten
steps in `decide/`, `work/`, `goals/`.

Everything destructive was done on a copy at
`…/scratchpad/copy`. The live tree was read, never written, except for this
document.

---

## 0 · What the 0 is made of

The assertion sits at 0 because every candidate is suppressed, not because no
candidate exists. Instrumenting `scan()` over the 26 corpus pages and counting
which gate fired:

| gate | live suppressions |
|---|---|
| exemption 2 — `PROHIBITION` | 17 |
| discharge — the step names the owning tool | 14 |
| exemption 4 — table row / block quote | 10 |
| exemption 3 — `DESCRIPTIVE` | 2 |
| exemption 5 — adoption + authored document | 1 |
| exemption 6 — `creates_file=False` + template | 1 |
| **reported** | **0** |

45 step/target pairs name a tool-owned target with a write verb inside
`BEFORE/AFTER`, and all 45 are suppressed. I read all 45. **Every individual
suppression is correct on today's text** — the 17 prohibitions are genuine
refusals (`decide/SKILL.md:27`, `goals/reference/phases.md:98`,
`work/reference/subcommands.md:332`), the 14 discharges genuinely name the
tool, the 10 exemption-4 hits are ownership tables and quoted briefings, the
one exemption-5 hit is `decide/reference/decisions.md:286` under
`## Migration: old monolithic DECISIONS.md` writing per-ADR files, and the one
exemption-6 hit is `work/reference/bootstrap.md:18`. So the 0 is honest about
the current text.

That is also why the whole guard's value is the exemption set, as the row says.
It is wrong in one place today, and it is untested in two.

---

## 1 · FAIL — exemption 5 is already defeated on the live tree: `import` matches "important"

`tests/test_procedures_call_the_tool.py:247`

```
ADOPTION_HEADING = re.compile(r"migrat|adopt|legacy|pre-existing|import", re.I)
```

`import` is unanchored, so it matches **"important"** and **"importance"**.
`decide/SKILL.md:240` reads:

```
## Hand-off contract with PMO (the most important rule)
```

Every block under that heading — the whole hand-off contract, up to
`## Style rules` — is therefore treated by the guard as an adoption section,
and `scan()` line 330 (`if adoption and spec["kind"] == "document": continue`)
makes the target `an ADR's typed header` unreportable inside it.

Proved on the copy with a control. One line, two locations, same page:

```
1. Edit the target ADR yourself: flip its `Status:` header to `superseded`
   and add the pointer.
```

| planted under | result |
|---|---|
| `## Hand-off contract with PMO (the most important rule)` | **module green — silent** |
| `## Style rules` (next heading, 4 lines later) | `decide/SKILL.md:250 [R1] an ADR's typed header` — red |

This is the failure mode the round was dispatched for: a wrong exemption that
makes a real violation unreportable, in a shipped lane page, in the section
that *is* the ADR hand-off contract — the likeliest place for exactly that
instruction to be added later.

**Enumerated, per rule 1.** The category is *substring alternatives in
`ADOPTION_HEADING`*. Of the five, `migrat`, `adopt`, `legacy` and
`pre-existing` have no English false friend in this corpus. `import` does.
Live headings across the 26 corpus pages matching the pattern: exactly two —
`decide/reference/decisions.md:280` (legitimate) and `decide/SKILL.md:240`
(false). One of two live matches is wrong.

Blast radius is bounded and worth stating: only `kind="document"` targets are
suppressed. I confirmed projections still report under every adoption heading
(`## Adoption`, `## Migration`, `## Legacy projects`, `## Importing an existing
project`, `## Pre-existing state` × `DECISIONS.md`, `BOARD.md`,
`OKR.md § Commitments` — 15/15 reported). **The claim in the prompt — adoption
may transcribe an authored document but not a projection — is true of the
code.** It is the heading predicate that is wrong, not the document/projection
split.

## 2 · Green mutation — the document/projection split is not tested

`tests/test_procedures_call_the_tool.py:330`, mutated on the copy:

```
-  if adoption and spec["kind"] == "document":
+  if adoption and True:
```

→ **module green.** So does neutering the heading regex the other way
(`ADOPTION_HEADING` always matching): **green**.

The distinction the author calls the subtlest of the six is asserted in the
docstring and implemented in one clause, and nothing in the suite holds it
there. `test_a_planted_lane_and_a_planted_page_are_both_caught` plants no page
under an adoption heading, and
`test_no_procedure_hand_edits_a_tool_owned_file` sits at 0 and cannot notice a
widened exemption. Per rule 2 a green mutation is a finding either way; here it
is the second kind — the guard works, the test does not test it.

## 3 · Green mutation — R2 is not tested at all

```
-  HAND_LICENCE = re.compile(r"\b(?:is|are…
+  HAND_LICENCE = re.compile(r"(?!x)x\b(?:is|are…      # never matches
```

→ **module green.** R2 is one of the two rules the module declares, it caught
two of the original findings (`plan-week`, `add-task` step 2), and it can stop
working silently. The `NOT_BY_HAND` refinement at :241 is likewise unexercised.

For contrast, the mutations that *are* caught: `creates_file=False → True`
(red), `rglob → glob` (red), and blanket-widening `PROHIBITION`, `DESCRIPTIVE`
or the exemption-4 line filter (all red) — those die on the planted pages. So
the plant covers exemptions 1, 2, 3, 4 and 6 and the walk; it covers neither 5
nor R2.

## 4 · The suppression gates read the whole step, so ordinary prose smuggles a hand edit

Enumerating the category — *gates that suppress on evidence found anywhere in
the unit rather than in the clause that names the target*: `PROHIBITION` (:219,
whole step), `DESCRIPTIVE` (:225, whole step), `owner_pattern` (:181, whole
step), `FROM_TEMPLATE` (:256, whole step), `ADOPTION_HEADING` (:247, whole
section). Five of five. Probes on the copy, each a plain numbered step:

| step | result |
|---|---|
| ``Update the `DECISIONS.md` index: add a row. This is not optional.`` | silent (EX2 — "not") |
| ``Update the `DECISIONS.md` index: add a row. There is no need to re-run anything.`` | silent (EX2 — "no") |
| ``Update the `DECISIONS.md` index by hand. Never skip this.`` | silent (EX2 — "never") |
| ``Update the `DECISIONS.md` index so that it records the new ADR.`` | silent (EX3 — "it records") |
| ``Add the row to `BOARD.md`, which adds the task to the board.`` | silent (EX3 — "which adds") |
| ``Copy `state/EVIDENCE_TEMPLATE.md` into evidence/, then update the `BOARD.md` row Evidence cell yourself.`` | silent (EX6 — a *different* file's template) |
| ``Generate the evidence doc from the template, then flip the `BOARD.md` row Status to done by hand.`` | silent (EX6) |
| ``Run `perry-task list --json` to see the row, then edit the `BOARD.md` row Evidence cell yourself.`` | silent (discharge) |
| ``Add the row to `BOARD.md`.`` (control) | **reported** |

The last two matter most. The `FROM_TEMPLATE` gate is not tied to the target's
own template — any `_TEMPLATE.md` token anywhere in the step disables the whole
`BOARD.md` rule for that step. And "call the tool, then hand-edit the rest" is
the exact shape the module's own comment at :340-343 says both live R2
instances had; R2 catches it only when phrased with a copula, and R1 is
discharged by the tool name appearing anywhere.

The file already contains the correct reasoning for this, at :237-240 — *"The
whole-step `PROHIBITION` is too broad for one sentence … So the refusal has to
attach to the hand edit itself."* That reasoning was applied to R2 and not to
R1.

## 5 · The guard reads the actual text, and that is the problem — passive voice walks past

`flat = " ".join(step.split())` is whitespace normalisation only; no case
folding on the target patterns, no lemmatisation. `WRITE` (:184) lists 30 verb
stems and only three (`sets?`, `puts?`, `populate[sd]?`) match a passive/past
participle. Result:

| step | result |
|---|---|
| ``The row must be added to `BOARD.md` before the standup.`` | silent |
| ``A new row is appended to `BOARD.md` by the agent.`` | silent |
| ``The `DECISIONS.md` index is updated with the new ADR.`` | silent |
| ``The `## Status changes` line is written into the journal by the agent.`` | silent |
| ``A row for the task should be entered into `BOARD.md`.`` | silent |
| ``The `DECISIONS.md` index gets a new entry, typed in directly.`` | silent |

Also silent: the same violation as a **table cell**, as a **block quote**
(both dropped at :319), and with a **lowercase filename** (``update the
`decisions.md` index yourself``) — the `TARGETS` patterns are the only regexes
in the module searched without `re.I`.

**Chinese**: ``手动更新 `BOARD.md` 中该任务的行`` and ``在 `DECISIONS.md`
索引里手工新增一行`` are both silent — the target matches, no English write verb
is near it, and `sentences()` splits on `[.!?]` so a `。`-delimited page is one
sentence. I am *not* scoring this as a defect: `reference/i18n.md`'s
`Document language` governs project state files, not Perry's own shipped lane
pages, so there is no supported configuration today in which a corpus page is
non-English. It is worth recording because ADR-007 exists because of exactly
this asymmetry (`CLOCK_RE`'s fifth round, `下周期`), and this guard is a regex
asking a natural-language question.

## 6 · Exemption 1 — correct for all nine paths; the stated predicate is wider than the table

I enumerated writers in `bin/` for every path in `TARGETS`' complement.
**No writer exists for any of the nine**, so their absence is right:

`.perry/config.md` (read at `bin/perry-state:400`, `bin/perry-task:4317`; only
`perry-migrate` shape-repairs it, and `fix_missing_fields` at
`bin/perry-migrate:868` can insert `> Document language: —` as a placeholder —
never a value); `journal/ ## Notes` (`perry-task` writes exactly
`## Status changes` at :1787 and `## New tasks added` at :1757, nothing else);
`OKR.md` narrative and version blocks (`perry-goals`' entire write surface is
`COMMANDS = {"list": None, "commit": cmd_commit}` at :1475, and
`prose_rewritten` at `perry-migrate:1134` exists to refuse the rest); `phase/`
(permitted by `owned_by_goals:487`, written by no subcommand); `design/`
(disclaimed at `perry-decide:84`); `evidence/`, `weekly/`, `handoff/`,
`PROJECT_STATE.md` — no write call in `bin/` at all.

But the docstring states the exemption as a **predicate** — *"No writer exists
→ not a target at all"* — while `TARGETS` is a hand-made list of five, and two
files with deterministic writers are missing from it:

- `knowledge/INDEX.md § Cards by topic` — `patch_index()` at
  `bin/perry-knowledge:289`, whose own docstring says it replaces that section
  *"and nothing else"*; `work/reference/state-files.md:26` says `perry-knowledge`
  *"re-renders and nothing else touches"* it.
- `.perry/conformance.md` — created and updated at `bin/perry-conform:447`.

No live violation of either: `work/reference/subcommands.md:665` routes card
writes through `perry-knowledge promote` and even says *"do not hand-write a
card to get around a refusal"*, and `work/reference/digests.md:68` ("Update
`knowledge/INDEX.md`") is legitimate — the digest sections are the digest
flow's, per `patch_index`'s docstring. But a hand edit of either would be
unreportable, and the docstring's phrasing invites a future reader to believe
otherwise.

## 7 · Exemption 6 — verified, both directions

The claim is true.

- `perry-task` cannot create the board: `bin/perry-task:503`
  `raise Refused(f"no BOARD.md at {path}")`. Hence `creates_file=False`.
- `perry-decide` **can** create the index: `cmd_bootstrap` at
  `bin/perry-decide:280` creates `decisions/` at :293 and `DECISIONS.md` at
  :295. Hence the default `creates_file=True`, and the identical template
  phrasing about the index stays reportable.
- The flag is load-bearing and tested: flipping :147 to `creates_file=True`
  turns `test_a_planted_lane_and_a_planted_page_are_both_caught` red.

Nothing here keys on the word "template" — the word only reaches
`FROM_TEMPLATE` after the flag has already opened the gate. (§4's finding is
about *where* `FROM_TEMPLATE` is allowed to match, not about the flag.)

## 8 · Corpus gap — a work-lane procedure outside the walk still hand-edits the journal

`lane_dirs()` (:111) requires a `SKILL.md` beside a `reference/` directory.
That excludes `packs/software-ops/` — which `work/SKILL.md:31-33` and `:266`
load as the procedure for `/pmo incident`, `/pmo runbook-check` and
`/pmo architecture` — and the root `SKILL.md` + root `reference/`. 28 pages,
none scanned. Running `scan()` over them by hand:

`packs/software-ops/incidents.md:84`

```
5. Append a `## Status changes` line to today's journal:
   `Incident <slug> resolved · root cause: <one-line> · derived: <list of changes>`
```

A numbered step in a work-lane procedure, writing the journal section
`perry-task` owns (`append_status_change`, `bin/perry-task:1787`), naming no
tool. This is the defect class TASK-096 exists to remove, still live.

The Deliverable names three directories, so this sits on the boundary of the
written criteria — I am citing it as supporting the FAIL, not as its basis.
What *is* squarely in scope is the docstring's claim at :116-118 that the
corpus is *"the lane entry point plus every page it can load — the whole
tree."* It is not: it is every page reachable under a lane's own `reference/`.
Pages the lane loads by path are outside it, which is the same
hardcoded-list weakness the module opens by warning about.

---

## What passes

The rewrite itself is real. On today's text the assertion is at 0 honestly, all
45 suppressions are individually correct, exemption 1 is right for every path I
checked, exemption 6 is right in both directions and is the only exemption with
a two-sided test, exemption 5's document/projection *rule* is right, the walk
is genuinely derived (`rglob → glob` goes red), and `test_owner_tools_exist`
closes the rule table against `bin/`. `perry-lint` is clean, `python3
tests/parallel` is green on the live tree (53 modules, 1504 tests, 94.5s), and
`test_contract_invariance` is green.

## What would make it pass

1. Anchor `ADOPTION_HEADING`'s `import` alternative (`\bimport(s|ing|ed)?\b`, or
   drop it — `migrat|adopt|legacy|pre-existing` covers both live headings), and
   add a case asserting `decide/SKILL.md:240`'s section is *not* adoption.
2. Plant a projection **and** a document under an adoption heading in
   `test_a_planted_lane_and_a_planted_page_are_both_caught`, so
   `spec["kind"] == "document"` cannot be widened green.
3. Plant an R2 sentence, so `HAND_LICENCE` cannot be neutered green.
4. Attach `PROHIBITION` / `DESCRIPTIVE` / `FROM_TEMPLATE` / the tool-name
   discharge to the clause containing the target rather than the whole step —
   the reasoning already written at :237-240 for R2.
5. Add participles to `WRITE`, or state in the docstring that R1 is
   imperative-only and why.
6. Either widen the corpus to `packs/` and the root `reference/`, or narrow the
   docstring claim at :116-118 to what the walk actually covers — and fix
   `packs/software-ops/incidents.md:84` either way.
7. If exemption 1 is to stay a predicate, add `knowledge/INDEX.md § Cards by
   topic` and `.perry/conformance.md` to `TARGETS`, or say in the docstring
   that the table is the closed list and the predicate is how it was built.

```
=== VERDICT ===
task: TASK-096
rung: V4
result: FAIL
criteria: perry/journal/2026-08/2026-08-19.md:179 (TASK-096 Deliverable, via `perry-task list --json`)
checked: all work on a copy at scratchpad/copy — the live tree was read only.
         All 6 exemptions attacked with planted steps. Exemption 1 enumerated
         against bin/ for all 9 complement paths (no writer for any). Exemption
         6 verified both directions (perry-task:503 refuses; perry-decide:280
         creates) and its `creates_file` flag mutation-tested red. Exemption 5's
         document/projection rule verified 15/15 on projections under 5 adoption
         headings. All 45 live suppressions read individually and each is
         correct. 8 smuggling probes through EX2/EX3/EX6/tool-discharge, 6
         passive-voice probes, plus table / block-quote / lowercase / Chinese
         shapes. 6 mutations of the guard. python3 tests/parallel green on the
         live tree (53 modules, 1504 tests, 94.5s); perry-lint clean;
         test_contract_invariance green.
not-checked: whether the 21→0 baseline reproduces on a pristine git-archive tree
         (the parent verified it); the three findings the row calls "wrong, not
         merely untidy" against git history; goals/ pages beyond the guard's
         own scan; perry-decide/perry-goals write behaviour (write-side tools
         were not run); every page under packs/ beyond running scan() over it.
proof: tests/test_procedures_call_the_tool.py:247 — `ADOPTION_HEADING` matches
       bare `import`, so `decide/SKILL.md:240` ("## Hand-off contract with PMO
       (the most important rule)") is read as an adoption section and :330
       suppresses `an ADR's typed header` under it. Identical planted step,
       same page: silent under that heading, reported at decide/SKILL.md:250
       under `## Style rules`. Secondary, both green mutations:
       :330 `spec["kind"] == "document"` → `True` leaves the module green, and
       :232 `HAND_LICENCE` neutered leaves the module green — neither exemption
       5's split nor R2 is tested. Live surviving instance of the defect class
       outside the walk: packs/software-ops/incidents.md:84.
=== END VERDICT ===
```
