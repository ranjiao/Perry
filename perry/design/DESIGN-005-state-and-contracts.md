# DESIGN-005: Three domains, three different levels of finished

> Status: locked
> Date: 2026-08-18 · Locked: 2026-08-17
> Author: Perry maintainer   · Implementation owner: Coding Agent (Perry repo)
> Linked OKR: KR-O2.1, KR-O2.2, KR-O4.2 (`perry/OKR.md` v2). This line
> previously read *"Perry has no `OKR.md`; declared unlinked, not guessed"*,
> which was true when written and stopped being true when the OKR was
> created the same day.
> Supersedes: —   · Superseded by: —
> Requested scope: goal + decision + task, storage **and** interface, in one
> design, each with deterministic state an external program can query.

## 1. Problem

The question that opened this was about format — is a markdown document a
sensible place to keep task rows, given a Python tool operates on part of it
like a database table?

The measurements say the format is a real cost but not the deepest one. The
deepest one is that **Perry has three domains of state and only one of them is
finished.**

### 1.1 · The asymmetry, as it stands today

| | **Goals** | **Decisions** | **Tasks** |
|---|---|---|---|
| Canonical files | `OKR.md`, `phase/<NNN>-<slug>.md`, `phase/<NNN>-linkage.md` | `DECISIONS.md`, `decisions/ADR-NNN-*.md` | `BOARD.md`, `journal/` |
| **Write tool** | **none** | **none** | `bin/perry-task` |
| Event log | none | none | `.perry/events.jsonl` |
| Drift detection | none | none | `perry-state § board.drift` |
| **Frozen read contract** | **none** | **none** | `perry-task/list/1.0` |
| What a reader gets | full objectives + KRs + phase + linkage, via `perry-state --json` | **`count`, `last`, `expired_sunsets` — a summary. The set is not listable.** | the full set, open and closed, with per-task timeline |
| Who creates the files | `goals` bootstrap | **nobody — see §1.3** | `work` bootstrap |

`bin/perry-task` is the only writer in `bin/`. Nine other scripts read.

### 1.2 · What the format actually costs, measured

Format handling is **25% of `bin/perry-task`** (the `Board` class, header alias
resolution, `split_row`/`render_row`, `check_header`). Nearly every blocking
defect in the TASK-033 migration came out of that quarter:

| Defect | The document/table conflict behind it |
|---|---|
| `add` wrote a row of blank cells at exit 0 on a `编号 \| 标题 \| …` board | column headers may be written in the document language — a **document** property; a table has no such thing |
| Cadence rows counted as drift forever | the tool's row-set and the document's sections disagreed — *the document holds other things* |
| `--commitment` accepted and discarded | values land by header mapping; no header, silent drop |
| `owner` read the track, `status` read the owner, `open` counted zero | the writer placed cells by name, the only reader read them by position |
| `mint_id` scans the whole board text as a backstop | an admission that the table's boundary is not reliable |
| byte-identity preservation is a hard requirement | the file is human-authored, so the tool may not normalize anything it did not touch |

**`perry-lint` reported the fourth one clean.** A schema declares *which columns
exist*, not *how a reader must find them* — which is why two parsers in one
repository, written to one schema, disagreed silently.

### 1.3 · Two failures that are not about format at all

- **Nothing creates `DECISIONS.md` or `decisions/`.** `work/reference/bootstrap.md`
  refuses to (correctly — they moved to `decide`), and says *"`decide`'s own
  bootstrap creates them"*. `decide/SKILL.md` has no such step: `init` creates
  `design/` and explicitly *"does not create any docs"*. First-time setup never
  invokes a `decide` subcommand. So `decide adr` step 7, *"update `DECISIONS.md`
  index"*, runs against a file that does not exist, and every project reports
  `decisions.count = 0` forever. Round-4 review, verified.
- **A closed task's id was reissued** when `.perry/events.jsonl` was deleted —
  a file the tool declares disposable. Found by demonstrating where state lives,
  not by review. Fixed, but it is the shape of the risk: something load-bearing
  living only in the derived file.

Both are "a procedure asserted in one file and absent from the one it names" —
the same defect the format produces, in a place the format cannot explain.

### 1.4 · What is already right, and must not be lost

- `BOARD.md` has a **200-line soft cap and holds open work only**. It is not
  asked to be a database; volume lives in `journal/` and the event log. The
  "large concurrent dataset" pressure the format question implies is bounded by
  design, not by luck.
- The **append-only file won the concurrency test**: eight parallel writes,
  `events.jsonl` took all of them, the read-modify-write document lost three
  before a lock was added.
- **`perry-task/list/1.0` already proves the shape of the answer** for one
  domain: a versioned payload with every key always present, locked by tests,
  and explicitly independent of what the storage does underneath.

## 2. Goals

1. **One story for all three domains** — goals, decisions and tasks get the same
   answer to "where does it live, who writes it, how does a program read it".
2. **Deterministic external query for each**, versioned and test-locked, so
   aimark (or anything else) codes against a contract rather than a file format.
3. **No second record of the same fact.** ADR-002's constraint, unchanged.
4. **Whatever the storage answer is, the read contracts do not move with it.**

## 3. Non-Goals

- A cross-project registry. Closed by ADR-002.
- A server, daemon, or background process.
- Migrating history. Whatever is decided applies going forward; existing
  markdown stays readable.
- Deciding aimark's internals. This design fixes what Perry publishes.

## 4. User Decisions

All six resolved 2026-08-17 by Ran Jiao. Recommendations were given, not assumed.

| # | Question | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | **Is hand-editing `BOARD.md` (and `OKR.md`, `DECISIONS.md`) a feature to keep, or a transitional artifact?** Every other row depends on this one. | (a) keep — markdown stays canonical, hand-edits stay legitimate and reported · (b) drop — a structured store becomes canonical and markdown becomes a rendered view that hand-edits do not survive · (c) split — canonical markdown for goals and decisions (low volume, high prose), structured for tasks | **(c) split** | 2026-08-17 |
| 2 | **Which store for the structured half?** | (a) JSONL append-only · (b) JSON document · (c) YAML · (d) SQLite | **(a) JSONL** — `append-only` amended 2026-08-18 by [ADR-006](../decisions/ADR-006-task-store-is-not-the-log.md): the store is JSONL **rewritten in place**, one object per task; append-only is the *log's* property and stays there. The format choice is unchanged, and (d) is not revisited | 2026-08-17 · amended 2026-08-18 |
| 3 | **Do goals and decisions get write tools?** | (a) both · (b) decisions only · (c) neither | **(a) both** | 2026-08-17 |
| 4 | **Does aimark call `perry-*` tools, or keep its own parser?** Reverses or confirms `schema/README.md`'s recorded decision. | (a) call the tools · (b) keep the parser, and add "columns resolve by name, never by position" to the schema as a binding rule · (c) both — tools when Python is present, parser as fallback | **(a) call the tools** | 2026-08-17 |
| 5 | **Contract versioning** — one version for all three read contracts, or one each? | (a) one each (`perry-task/list/1.0`, `perry-goals/list/1.0`, …) · (b) a single `perry/state/1.0` | **(a) one each** | 2026-08-17 |
| 6 | **Does the event log become canonical for tasks** (markdown as projection), or stay derived? | (a) stays derived · (b) becomes canonical | **(b) becomes canonical** — consequence of #1, not separately asked | 2026-08-17 |

**#6 was not put to the user as its own question, and that is recorded here
rather than hidden.** Choosing (c) on #1 *is* choosing (b) on #6: the option the
user read said a hand-edited task row "gets overwritten on the next tool write —
but not silently; the difference is surfaced first", which is markdown-as-
projection. Asking it again as an independent fork would have been asking the
same question twice in different words.

> This row's parenthetical previously read *"tied to #1; (a) if #1 is (a) or
> (c)"* — which contradicted §5.1 and §5.2 in the same document, both of which
> describe the log becoming canonical under (c). A decision row asserting the
> opposite of the section it points at is the exact defect five review rounds
> kept finding in this project, committed here by its own author. Corrected at
> resolve time, before it could be built against.

**What would reopen #1**, the only one that is expensive to change later: a user
who edits `BOARD.md` by hand often enough that reconciliation prompts become
noise rather than a safety net. That is a usage observation, not an argument —
if it happens, the answer is (a), not a bigger reconciler.

### 4.1 · What each answer settles

- **#1 = (c)** → §5.1 stands as written. `OKR.md`, `phase/` and `decisions/`
  remain canonical hand-editable markdown; task rows do not.
- **#2 = (a)** → `.perry/events.jsonl` is *reclassified*, not replaced. No new
  file, so ADR-002's "no new derived data" holds unchanged.
- **#3 = (a)** → `perry-goals` and `perry-decide` are both built, and
  `perry-decide` carries the missing bootstrap from §1.3.
- **#4 = (a)** → **reverses** `schema/README.md`'s recorded decision that aiMark
  implements the schema rather than calling a tool. aiMark now shells out to
  `perry-*` and takes a Python 3 dependency. That README section must be
  rewritten from "here are two live options" to a settled decision naming this
  one, with the old rationale preserved as history — it was correct when made.
- **#5 = (a)** → three independent version strings; `perry-task/list/1.0` is
  unaffected by anything the other two do.
- **#6 = (b)** → §5.5's highest-risk row is now in scope rather than hypothetical.
  It stays **last** in §6, because everything else is useful without it and
  nothing else needs it first.

## 5. Architecture

> §4 is resolved, so nothing below is conditional any more.

### 5.1 · Why the three domains should not get the same storage answer

They differ on the axis that matters — **how much of the content is prose a
human argues with**:

| | Volume | Prose share | Changes per week | Hand-edited in practice |
|---|---|---|---|---|
| Goals | 1 `OKR.md` + 1 phase file | high — objectives, anti-goals, operating principles | low | yes, deliberately |
| Decisions | 1 index + N ADRs | very high — Context / Options / Consequences | very low | yes, deliberately |
| Tasks | tens of rows, churning daily | low — six short cells | **high** | increasingly not |

A decision record is an argument; a task row is a tuple. **The format tax is
paid per write**, and tasks are where the writes are. Applying one storage
answer to all three would either put ADR prose into a database or leave the
churning tuples in the format that has produced every blocking defect.

This is what #1 = (c) settles: **goals and decisions stay canonical markdown
with writer tools; tasks move their canonical row data into the append-only log,
with `BOARD.md` remaining a first-class human view.**

### 5.2 · The task store, and the log beside it

**Amended 2026-08-18 — [ADR-006](../decisions/ADR-006-task-store-is-not-the-log.md).**
This section previously read *"The task store **is** the log that already
exists"*, and argued that making `.perry/events.jsonl` canonical was *"a
reclassification, not a new file — which is what keeps ADR-002 satisfied"*.

Decision #1 chose a structured store for tasks and decision #2 chose JSONL.
Neither said the store and the log are one file. This section did, and the
reason it gave does not hold: `ADR-002` is *no cross-project registry*, objects
to *"state that outlives and outranks the thing it describes"*, contains no
clause against a file **inside** a project, and explicitly exempts
`.perry/events.jsonl` as *"inside the project it describes, under an
already-claimed path"*. That was the only stated reason for one file.

What the fusion cost, measured on Perry's own state:

- Every full-set read is **O(events)**, not O(tasks) — 173 events for 75 tasks,
  a ratio that only rises, because a task accrues events forever and has one
  current state.
- **57% of the log's bytes are `next` events** — cell overwrites whose
  historical value is near zero — dominating the file that must be traversed to
  answer *"what is the full set of tasks?"*, which is `§ 1.3`'s own question.

**Three layers, one job each.**

| | file | grows with | disposable |
|---|---|---|---|
| **truth** | `perry/tasks.jsonl` — one JSON object per task, current state, **rewritten in place** | project scope | no |
| **view** | `BOARD.md` — the open subset, rendered | open work | yes, regenerable |
| **history** | `.perry/events.jsonl` — append-only, `O_APPEND`, git-diffable | activity | **yes** |

The store sits under the **state root**, not `.perry/`. Location is the claim:
`.perry/` holds configuration and derived artifacts, and putting canonical
state there is what let the fusion look reasonable for a release.

The cost, stated as plainly as the sentence it replaces: **hand-editing
`BOARD.md` stops being authoritative.** An edit is read as a request to be
reconciled, or overwritten on the next render. That is decision #1, unchanged,
and it is still the part that is not cheap to reverse.

What this does **not** change: `perry-task/list` is a frozen contract and keeps
its shape — where a value is read from is not a contract fact. And it is not a
step toward a database; option (d) stays rejected, and `§ 5.1`'s argument for
why the three domains get different answers is untouched.


### 5.3 · The read contracts — the part that is unconditional

**These are worth building whatever §4 decides**, because they are what makes
the storage question survivable. Each is a versioned payload, every key always
present, locked by tests, documented in `schema/`:

| Contract | Command | Covers |
|---|---|---|
| `perry-task/list/1.0` | `perry-task list --all --json` | **exists** — tasks, open and closed, with timeline |
| `perry-goals/list/1.0` | `perry-goals list --json` | objectives, KRs, phase, linkage edges, attribution state |
| `perry-decide/list/1.0` | `perry-decide list --json` | **the set of decisions** — id, title, status, type, date, sunset, supersedes, ADR path. Today only `count`/`last` are exposed. |

Rules, identical across all three and already stated in
`schema/task-list-contract.md`:

1. every declared key is always present — unknown is `""`, `null` or `[]`
2. `1.x` → `1.y` may only **add** keys
3. `contract` is the version handle; a consumer checks major and refuses loudly

### 5.4 · The writers

| Tool | Writes | Refuses |
|---|---|---|
| `perry-task` | `BOARD.md`, `journal/`, events | **exists** |
| `perry-goals` | `OKR.md`, `phase/`, `phase/<NNN>-linkage.md` | a KR edge to an unresolvable id; a phase file for a phase that exists |
| `perry-decide` | `DECISIONS.md`, `decisions/ADR-NNN-*.md` | an ADR with no Context/Options/Chosen; an index row for a missing file; **creates both on first use — §1.3** |

Each takes the same project lock, so a write in one lane cannot interleave with
a write in another.

### 5.5 · Blast radius

| Change | Risk | Why |
|---|---|---|
| Read contracts (§5.3) | **low** | additive; nothing existing reads them |
| `perry-decide` writer + bootstrap | **low** | closes a hole where nothing exists today |
| `perry-goals` writer | **medium** | `OKR.md` is prose-heavy; a writer that reformats it is worse than none |
| **Tasks → log canonical (§5.2)** | **highest** | changes what "the truth" is. Hand-edit semantics change, `perry-state`, the viewer, aimark and every procedure that says "the board is canonical" move together. Must be last, and must not start until #1 is answered. |

## 6. Implementation plan

All four are in scope; §4 is resolved. Steps 1–3 do not depend on step 4 and
must not wait for it.

| # | Step | Rung | Why here |
|---|---|---|---|
| 0 | Record decision 4's reversal in `schema/README.md` — **done at resolve time** | V2 | it invalidates a published instruction to another repo's author; leaving it stale for one commit is how aiMark gets built against the wrong contract |
| 1 | `perry-decide` — writer, the missing bootstrap (§1.3), and `perry-decide/list/1.0` | V4 | `DECISIONS.md` exists nowhere today, so this is the only step that closes a total gap rather than improving a partial one |
| 2 | `perry-goals/list/1.0` — read contract only | V4 | additive; `perry-state` already parses everything it needs |
| 3 | `perry-goals` writer | V4 | riskiest of the markdown three — `OKR.md` is prose the user argues with |
| 4 | Tasks: **the task store** becomes canonical (`perry/tasks.jsonl`), `BOARD.md` becomes a projection, the event log stays a log | **V5** | changes what "the truth" is; the only step that needs the user to accept a behavior change they will feel |

**Step 4 stays last for a reason that survived the decision going its way.**
Steps 1–3 are useful whether or not it ships, and it needs none of them first.
Sequencing it last keeps the expensive, hardest-to-reverse change behind three
cheap ones that will have exercised the contract pattern by then.

`perry-task/list/1.0` does not move in any of these steps. That is the property
that lets aimark start now, against step 0's contract, in parallel with all four.

## 7. Risks & mitigations

| Risk | Mitigation |
|---|---|
| A `perry-goals` writer reformats prose-heavy `OKR.md` and a human's wording is lost | text-level edits like `perry-task`'s `Board`, never a parse-and-render round trip; byte-identity test against the existing file before any write path ships |
| The read contracts are built, then drift from what the tools emit | the same arrangement that already failed five times. `TestListContract` reads the contract document's own tables back against the payload; every new contract copies that test, not just the pattern |
| aiMark is built against the schema route while decision 4 says otherwise | `schema/README.md § Consumers` was rewritten at resolve time, not deferred to step 1 — that instruction lives in the file another repo's author reads |
| Step 4 lands and a hand-edited board row is discarded without the user seeing it | the reconcile prompt is the deliverable, not a nicety. `unrecorded` already detects the edit; step 4 must surface it as a diff to accept or reject, and V5 exists on that row to make the user judge exactly this |
| Tasks move to the log, and a user's hand-edit is silently discarded | never silently — an edit with no event is already detected as `unrecorded`; if the log becomes canonical the same detector must surface the edit as a reconcile prompt, not overwrite it |
| Three writers, three locks, one project | all three take the same `.board.lock`; a lane cannot interleave with another |

## 8. Open questions

- Does `perry-state --json` stay the combined dashboard read, with the three
  `list` contracts beside it, or does it become a composition of them?
- Should the three writers be one binary with three noun subcommands
  (`perry state task add`, `perry state goal link`) rather than three scripts?
- If the event log becomes canonical for tasks, does an equivalent appear for
  goals and decisions, or do they stay markdown-only permanently?

## 9. Changes (append-only after lock)

- **2026-08-17 · locked.** All six User Decisions resolved the same day; §4
  records what was chosen and §4.1 what each answer settles. `Implementation
  owner` was filled at lock time as `Coding Agent (Perry repo)` — decided by the
  agent rather than asked, because §3 already declares aiMark's internals a
  Non-Goal, so every step in §6 is Perry-repo work and there was no second
  candidate. Revisit if a step is handed to someone outside this repo.

- **2026-08-17 · step 4 accepted by the user, and sequenced after step 3.**
  Step 4 is the only one in this plan that needed a signature rather than a
  review, because it changes what "the truth" is: today a hand edit to
  `BOARD.md` *is* the new fact, and afterwards it raises a reconcile prompt
  instead — never silently overwritten, and never silently authoritative
  either. The user accepted that, and accepted the cost it names: editing the
  board directly stops being the last word, and a quick correction gains a
  confirmation step.

  **The acceptance was taken before step 3 starts, deliberately.** TASK-037
  builds the `goals` lane's writer, and a writer built against "the file is the
  truth" is a different writer from one built against "the log is the truth".
  Asking after would have meant either rework or a second design that quietly
  disagreed with this one.

  Sequencing is unchanged: step 4 still lands last, per §6 and §5.5's
  `highest` blast radius. What moved is that its direction is no longer an open
  question that step 3 has to guess at.

- **2026-08-18 — the task store is not the event log — [ADR-006](../decisions/ADR-006-task-store-is-not-the-log.md).**

  `§ 5.2` fused two things `§ 4` did not. Decision #1 chose a structured store
  for tasks; decision #2 chose JSONL; **neither said the store and the log are
  one file.** `§ 5.2` did, on the stated ground that it kept `ADR-002`
  satisfied — and `ADR-002` is *no cross-project registry*, has no clause
  against a file inside a project, and explicitly exempts
  `.perry/events.jsonl`. The only reason given for one file was a citation that
  does not say what it was cited for.

  Measured before deciding, on Perry's own state: every full-set read is
  **O(events)** — 173 events for 75 tasks — and **57% of the log's bytes are
  `next` events**, cell overwrites with no replay value, in the file that has to
  be traversed to answer `§ 1.3`'s own question.

  **Raised by the user**, who put it as: a log should be a log, and the full task
  set needs one place that stores it without history — because traversing the
  whole log for the full set gets worse forever. That is `§ 1.3`'s question
  turned into a storage requirement, and neither `§ 5.2` nor decision #6 had
  been asked it.

  Three layers now: `perry/tasks.jsonl` (truth, one object per task, rewritten
  in place) · `BOARD.md` (the open subset, rendered) · `.perry/events.jsonl`
  (history, append-only, **disposable again**).

  What did **not** move: decision #1 (split) · decision #2's *format* — JSONL
  over JSON, YAML and SQLite, with only the word `append-only` amended, because
  that is the log's property · `§ 5.1`'s argument · `§ 5.3`'s three read
  contracts · `perry-task/list`'s shape. Where a value is read from is not a
  contract fact.

  Sequencing is unchanged and step 4 still lands last. What moved is **what
  step 4 builds**: the store becomes canonical, not the log. Scope: `§ 4` row 2,
  `§ 5.2`, `§ 6` step 4, and the header's `Linked OKR` line, which claimed Perry
  had no `OKR.md` and stopped being true the day it was written.

  `DESIGN-004 § 5.3` is corrected by the same ADR and carries its own entry.

## 10. References

- `perry/design/DESIGN-003-work-modes.md` — tracks, modes, verification ladder
- `perry/design/DESIGN-004-deterministic-writes.md` — the task writer
- `perry/decisions/ADR-002-no-cross-project-registry.md` — working directory is the scope
- `schema/task-list-contract.md` — the first frozen read contract
- `schema/README.md § Consumers` — the aimark parser decision, and its measured cost
