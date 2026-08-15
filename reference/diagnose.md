# Diagnose — auditing and refactoring how a project works with agents

Loaded when `/perry diagnose` fires. Not loaded on routine snapshots, on
`/perry adopt`, or on first-time setup.

`adopt` converts a project **into** Perry. `diagnose` asks a prior question:
**is this project's working structure sound at all?** The answer is often "yes,
leave it alone", sometimes "you need three files", and only sometimes "adopt
Perry". A diagnostic that always prescribes its own product is an installer
wearing a lab coat, and users learn to discount it within two runs.

The research this stands on — the three failure modes, the isolation ladder,
the tier discipline, the archetypes — is in
[project-archetypes.md](project-archetypes.md). This file is the procedure.

## The one rule: measure, ask, then prescribe — and prescribe the smallest thing

**Every prescription must trace to a finding, and every finding must trace to a
measurement or an answer the user gave.** No prescription may originate in
Perry's taste.

This is the same class of gate as `adopt`'s *evidence proposes, the user
declares*, and it exists for a sharper reason here. Diagnosis is inherently
judgmental: an agent asked to critique a folder will always find something to
say, and structure is the easiest thing in the world to recommend more of.
Without this rule, `/perry diagnose` becomes a machine that converts any
project into a heavier project.

Two corollaries:

- **"Do nothing" is a first-class outcome.** So is "you have too much
  structure, here is what to delete." If the scan produces no findings and the
  interview surfaces no pain, say so and stop. That run was a success.
- **The user's maintenance tolerance is a hard ceiling, not an input to
  balance.** A user who says they will maintain two files gets a two-file
  prescription, even when the scan justifies six. An unmaintained organ is
  worse than an absent one — it reports stale state that everything downstream
  believes.

## Command surface

```
/perry diagnose [--depth=quick|standard|deep] [--only=<lanes>] [--dry-run] [--recheck]
```

| Flag | Effect |
|---|---|
| `--depth` | `quick` = scan + report, no interview. `standard` (default) = scan + interview + prescription. `deep` = adds per-document triage of the doc graph. |
| `--only` | Comma-separated lanes: `context,docs,concurrency,tracking`. Default all. |
| `--dry-run` | Stop after the prescription. Writes the diagnosis doc, executes nothing. |
| `--recheck` | Re-run the scan against a previously diagnosed project and diff. See § 5. |

Runs on **any folder**. Perry state is optional and, when present, is just
another input.

## Stages

Six stages. Each records completion in the diagnosis doc's `stage:` field, so
an interrupted run resumes rather than restarting the interview.

### 0 · Scan (deterministic, read-only)

```
python3 "$PERRY_HOME/bin/perry-diagnose" --root . --json
```

Stdlib-only, read-only, exit 0 always. Returns the measurements: context load
against budget, the document reference graph, concurrency signals, tracking
spine, archetype signals, and a `findings[]` array with stable IDs.

**Every number in the report comes from this payload.** A field it doesn't
carry prints `—`. Do not eyeball a line count, do not estimate a doc count, and
do not assert an archetype the payload scored as `none`.

Render the scan verbatim first (the script's `--text` mode is the canonical
shape), then continue. The user seeing raw measurements before any opinion is
what makes the opinion credible.

**Thresholds are defaults, not laws.** The payload carries `thresholds`; when a
finding rests on one, say which and let the user push back. `reference/
project-archetypes.md § Part 5` records where the evidence is thin, and that
honesty is load-bearing — a user who catches the tool over-claiming once
discounts everything it says afterward.

### 1 · Read (what the scan can't measure)

The scan knows shapes, not meaning. Read, at `standard` depth:

- every tier-0 file, in full;
- the goal spine candidates the payload named;
- the index, if one exists;
- the three largest documents;
- for a git repo, `git log --oneline -30` — what the project is *actually*
  doing, versus what its docs say it's doing.

The gap between those last two is usually the most useful finding of the whole
run, and no script can compute it.

### 2 · Interview (the real requirement)

**Skip any question the scan already answered.** Asking a user something
visible in their own filesystem is how a consultation loses credibility in the
first thirty seconds.

Cap at **six questions**. Use `AskUserQuestion` (numbered free-text on Codex,
per `host-capabilities.md`). Each is outcome-framed: it asks about pain the
user has felt, not about architecture they may not have vocabulary for.

| # | Question | Ask when | What it settles |
|---|---|---|---|
| **Q1 · Output** | "What does this project actually produce, and who consumes it?" | Archetype confidence is `low` or `none`. | The archetype. **The user's answer always overrides the scan's guess** — the scan reads folder names, the user knows the project. |
| **Q2 · Collision** | "When you have two things to work on at once, what do you do today — wait, run two sessions in the same folder, or something else?" | Always. | Current isolation rung. Note that "wait" is a legitimate answer, not a confession. |
| **Q3 · Loss** | "In the last month, how many times did agent work get overwritten, lost, or redone because two sessions collided?" | Always. | The escalation trigger. **< 2 means do not prescribe isolation machinery**, whatever the branch count says. |
| **Q4 · Retrieval** | "Last time you needed to know why something was decided the way it was — where did you look, and did you find it?" | Always. | Whether the doc pile functions as memory, and whether a decision log is missing or merely unused. |
| **Q5 · Done** | "Take one thing currently in flight. How would you know it's finished? What would have to be true?" | Always. | The verification gap. If the answer is "it looks right" or "I read it", there is no loop, and that is usually the single highest-value finding in the run. |
| **Q6 · Tolerance** | "How much process are you willing to keep current every week — two files, five, or a full board?" | Always, and **ask it last**. | The ceiling on the prescription. Ask it after the pain is on the table, so the answer is informed rather than defensive. |

Two more, situational:

- **Audience** — "Who else reads these files: just you, teammates, or only the
  agent?" Ask when the project has more than one contributor in `git log`.
  Multi-reader projects need explicit written contracts where a solo project
  can rely on the user's memory.
- **Attachment** — "Anything here you want left alone no matter what?" Ask
  before any execute stage. Cheap, and it prevents the one mistake that ends
  trust permanently.

Record every answer verbatim in the diagnosis doc. Prescriptions cite them the
same way findings cite measurements.

### 3 · Prescribe

Compose the prescription in this fixed order, because each layer constrains the
next:

1. **Confirm the archetype** (`software` / `knowledge-base` / `ops` /
   `none-of-these`). `none-of-these` is real — say so and prescribe from the
   invariants in `project-archetypes.md § Part 4` alone rather than forcing a
   template.
2. **Check the invariants first.** The six in Part 4 apply to every project. A
   project failing an invariant has a problem no template fixes, so those
   findings outrank archetype-fit findings every time.
3. **Apply the maintenance ceiling from Q6.** Rank candidate changes by
   findings closed per unit of ongoing upkeep, then cut the list at the
   ceiling. State what you cut and why — a user who sees the deferred items can
   ask for them later.
4. **Size against the minimum viable spine.** If the project is below the floor
   (`project-archetypes.md § Part 2`), prescribe the floor and nothing more. If
   it is far above the floor with no matching pain, prescribe **subtraction**.
5. **Route Perry honestly.** Perry earns a prescription when the project needs
   goal cascade, cross-session handoff, or evidence-backed tracking, and the
   user's tolerance is a board or more. Otherwise recommend three files and say
   plainly that Perry would be overkill. Only then does `/perry adopt` follow.

Each prescription item carries:

```
| # | Change | Closes | Cost | Reversible | Needs |
|---|--------|--------|------|-----------|-------|
| 1 | Split CLAUDE.md: keep 38 rule lines, move 210 lines to skills/ | CTX-01 | ~10 min | yes (moves only) | approval |
```

`Closes` is a finding ID or a quoted interview answer. **An item that closes
neither does not go on the list** — that is the one rule, enforced at the point
it is easiest to violate.

### 4 · Execute (gated)

Execution is opt-in per item. The user picks which to run; a bulk "all" is
allowed but is never the default.

**Five safety rules, all mandatory:**

1. **A restore point before the first change.** In a git repo: commit any dirty
   tree first (ask), then create `perry/diagnose-<YYYY-MM-DD>`. Not a repo:
   copy every file that will be touched to
   `.perry/diagnose/<YYYY-MM-DD>-backup/`, preserving relative paths. Never
   begin without one.
2. **Move, never delete.** Demoting a document means moving it and leaving a
   pointer behind. Merging means one file absorbing another's content, with the
   source moved to an archive path — not removed. Deletion is only ever
   *proposed*, as a follow-up task the user performs. Every move is recorded
   `from → to` in the diagnosis doc, which is what makes the whole run
   reversible by hand.
3. **Content is rewritten only with the content in view.** Never regenerate a
   file the agent has not read in full. Splitting a 900-line rules file means
   reading all 900 lines and deciding where each goes — not writing a fresh
   file from an impression of it. The user's words survive the refactor; only
   their location changes.
4. **Perry state goes through its owning skill.** If the prescription touches
   `OKR.md`, `BOARD.md`, or `design/`, route through `/okr`, `/pmo`, `/design`
   as `adopt` does. Diagnose writes exactly one file of its own —
   `.perry/diagnose/<YYYY-MM-DD>-diagnosis.md` — and one class of change on
   its own authority: non-Perry documents in the project's own tree.
5. **Anything outward-facing stops and asks.** Rewriting a public README,
   touching CI config, or changing anything that runs on push is confirmed
   separately from the batch approval, in its own words.

**Then verify, in the same run:** re-run `bin/perry-diagnose` and show
before/after on the finding counts. A refactor that doesn't move the numbers
either didn't work or wasn't needed, and both are worth saying out loud. If the
project is a Perry project, `bin/perry-lint --root .` must also pass before the
run is called complete.

### 5 · Recheck

`/perry diagnose --recheck` re-runs stages 0–1 against a previously diagnosed
project and diffs against the last diagnosis doc:

```
🔄 Diagnose recheck · <project> · <N>d since last

   Findings closed        : 4  (CTX-01, DOC-02, TRK-03, TRK-04)
   Findings reopened      : 1  (CTX-01 — always-loaded back to 240 lines)
   New findings           : 2
   Prescribed, not done   : 3  (items 4, 6, 7)
   Declined last time     : 2  (not re-proposed)
```

**Declined items are memory.** A prescription the user rejected stays in the
doc as `status: declined` and is not raised again unless its finding materially
changes. Re-proposing the same rejected advice every quarter is exactly how a
tool trains its user to skip it.

Reopened findings are the interesting line: `CTX-01` coming back means the
tier-0 file regrew, which is a *process* finding (nothing is enforcing the
budget), not a repeat of the original.

## Finding catalog

Every ID `bin/perry-diagnose` can emit. A stable ID with nowhere to look it up
is a worse experience than prose, so this table is the lookup, and the test
suite fails if the scanner gains an ID that is not listed here.

| ID | Severity | Fires when | Usual prescription |
|---|---|---|---|
| `CTX-01` | error | Always-loaded files exceed the line budget. | The demotion |
| `CTX-02` | warn | `CLAUDE.md` and `AGENTS.md` both exist, neither a symlink. | Keep one, symlink the other |
| `CTX-03` | error | A tier-0 file names a path that no longer resolves. | Fix or drop the reference |
| `CTX-04` | warn | No always-loaded instruction file at all. | The spine install (rules file) |
| `CTX-05` | warn | The only tier-0 file is empty. | Fill it, or delete the placeholder |
| `DOC-01` | warn | ≥30% of docs are reachable from nothing (only past 12 docs). | The orphan sweep |
| `DOC-02` | error | ≥12 documents and no index. | The index build |
| `DOC-03` | warn | Two documents claim the same title. | Merge; reference, don't copy |
| `DOC-05` | info | A document exceeds the single-doc line cap. | Fine in tier 2; a problem if it loads unconditionally |
| `CON-01` | warn | Parallel work is evident and no isolation rule is written down. | The lane declaration |
| `CON-02` | info | Files with very high commit churn — the contention surface. | Split live state from append-only history |
| `CON-03` | info | Multiple worktrees with no named integration step. | Name the merge reviewer |
| `TRK-01` | error | No goal spine. | The spine install |
| `TRK-02` | warn | Every goal file is older than the staleness threshold. | Update or retire it |
| `TRK-03` | error | No check the agent can run. | The constructed check |
| `TRK-04` | warn | No decision log. | The spine install (decisions file) |
| `FIT-01` | info | Far more process than work. | The subtraction |
| `FIT-02` | info | Below the minimum viable spine. | The floor, and nothing more |

Interview findings get IDs in the same shape, prefixed by the question that
produced them, and carry `source: interview` in the diagnosis doc.

## Prescription patterns

The changes that actually come up, with the shape each takes.

**The demotion** (CTX-01, most common by far). A tier-0 file past budget. Read
it in full, sort every line into three piles: *changes agent behavior* (stays),
*procedure for a recurring task* (becomes a skill in tier 1), *reference*
(becomes a document in tier 2, linked from the index). Typical outcome is 200+
lines down to 30–50. Nothing is lost; the budget is recovered.

**The index build** (DOC-02). Generate `index.md` — or the archetype's
equivalent — listing every tier-2 document with a one-line purpose. Then add
one line to the tier-0 file telling the agent to read it first. The index is
the cheapest high-value artifact in this entire skill.

**The orphan sweep** (DOC-01). Present orphans in batches of ≤ 8 with their
first heading and age. Three outcomes per doc: link it from the index, move it
to an archive directory, or mark it for deletion (the user deletes). Never
auto-delete.

**The lane declaration** (CON-01). Write the isolation rung into the tier-0
file as a short explicit section: which rung, what each session owns, where the
integration step is. For rung 1, that is an ownership table. This is a
five-line change that prevents the failure mode the user actually complained
about.

**The spine install** (TRK-01). The minimum viable spine, three files, nothing
more, unless Q6 licensed more.

**The constructed check** (TRK-03, hardest and highest value). Code projects
already have one; wire it into the workflow. Non-code projects need one built —
a structural linter over the artifact format, a fresh-context reviewer against
written criteria, or a recorded human sign-off. Prescribe exactly one, the
cheapest that fits, and make it runnable in a single command.

**The subtraction** (FIT-01). Rank existing organs by "when did this last
change a decision?" Anything unused for a quarter gets proposed for archive.
This prescription is uncomfortable to give and is frequently the right one.

## What diagnose never does

- **Never prescribes without a finding or an interview answer behind it.**
- **Never deletes a file.** Moves and pointers only; deletion is the user's.
- **Never rewrites a document it has not read in full.**
- **Never exceeds the maintenance ceiling** the user gave in Q6.
- **Never asserts an archetype** the scan scored `none` and the user did not
  confirm.
- **Never treats Perry adoption as the default outcome** — it is one
  prescription among several, and frequently the wrong one.
- **Never runs the execute stage without a restore point.**
- **Never touches another project's files.** The scan resolves one root and
  stays inside it.
- **Never reports a correctly-structured project as broken** to justify the
  run. Zero findings is a valid, and good, result.

## See also

- [project-archetypes.md](project-archetypes.md) — the research: three failure
  modes, the isolation ladder, tier discipline, the three archetypes, and where
  the evidence is thin.
- [../templates/](../templates/) — runnable scaffolds the prescribe and execute
  stages copy from.
- [adoption.md](adoption.md) — the neighbouring pipeline, for when diagnosis
  concludes that Perry is in fact the right prescription.
- [host-capabilities.md](host-capabilities.md) — `AskUserQuestion` → numbered
  free-text on Codex; applies to the whole interview.
- [../state/diagnosis_TEMPLATE.md](../state/diagnosis_TEMPLATE.md) — the one
  file this pipeline writes.
