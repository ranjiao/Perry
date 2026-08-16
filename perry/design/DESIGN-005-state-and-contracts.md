# DESIGN-005: Three domains, three different levels of finished

> Status: draft
> Date: 2026-08-17
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: — (Perry has no `OKR.md`; declared unlinked, not guessed)
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

Each row is a real fork. Recommendations are given, not assumed.

| # | Question | Options | Recommendation |
|---|---|---|---|
| 1 | **Is hand-editing `BOARD.md` (and `OKR.md`, `DECISIONS.md`) a feature to keep, or a transitional artifact?** Every other row depends on this one. | (a) keep — markdown stays canonical, hand-edits stay legitimate and reported · (b) drop — a structured store becomes canonical and markdown becomes a rendered view that hand-edits do not survive · (c) split — canonical markdown for goals and decisions (low volume, high prose), structured for tasks | **(c)**, see §5.1 |
| 2 | **If anything becomes structured, which store?** | (a) JSONL append-only · (b) JSON document · (c) YAML · (d) SQLite | **(a)** — see §5.2; it already exists and already survived the concurrency test |
| 3 | **Do goals and decisions get write tools?** | (a) both · (b) decisions only · (c) neither | **(a)** — §1.3's missing-bootstrap failure is a writer-shaped hole |
| 4 | **Does aimark call `perry-*` tools, or keep its own parser?** Reverses or confirms `schema/README.md`'s recorded decision. | (a) call the tools · (b) keep the parser, and add "columns resolve by name, never by position" to the schema as a binding rule · (c) both — tools when Python is present, parser as fallback | **(a)**; if (b), the schema addition is mandatory, not optional |
| 5 | **Contract versioning** — one version for all three read contracts, or one each? | (a) one each (`perry-task/list/1.0`, `perry-goals/list/1.0`, …) · (b) a single `perry/state/1.0` | **(a)** — they will not move together |
| 6 | **Does the event log become canonical for tasks** (markdown as projection), or stay derived? | (a) stays derived · (b) becomes canonical | tied to #1; **(a)** if #1 is (a) or (c) |

## 5. Architecture (conditional on §4)

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

So the recommendation for #1 is (c): **goals and decisions stay canonical
markdown with writer tools; tasks move their canonical row data into the
append-only log, with `BOARD.md` remaining a first-class human view.**

### 5.2 · If tasks go structured, the store is the log that already exists

`.perry/events.jsonl` is append-only, `O_APPEND`, git-diffable, and already
carries every transition. Making it canonical is a **reclassification, not a new
file** — which is what keeps ADR-002 satisfied. `BOARD.md` becomes a projection
of "open rows", regenerable at any time.

The cost, stated plainly: **hand-editing `BOARD.md` stops being authoritative.**
An edit would be read as a request to be reconciled, or overwritten on the next
render. That is decision #1 and it is not reversible cheaply.

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

1. `perry-decide list --json` + `perry-decide` writer + the missing bootstrap (§1.3)
2. `perry-goals list --json`
3. `perry-goals` writer
4. Tasks storage change — **only if #1 resolves to (b) or (c), and last**

Steps 1–3 are independent of every decision in §4 except #3 and #5.

## 7. Risks & mitigations

| Risk | Mitigation |
|---|---|
| A `perry-goals` writer reformats prose-heavy `OKR.md` and a human's wording is lost | text-level edits like `perry-task`'s `Board`, never a parse-and-render round trip; byte-identity test against the existing file before any write path ships |
| The read contracts are built, then drift from what the tools emit | the same arrangement that already failed five times. `TestListContract` reads the contract document's own tables back against the payload; every new contract copies that test, not just the pattern |
| Decision #1 stays unanswered and steps 1–3 get built against an assumption | steps 1–3 are chosen precisely because they do not depend on #1. Step 4 is hard-blocked on it, stated in §5.5 |
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

—

## 10. References

- `perry/design/DESIGN-003-work-modes.md` — tracks, modes, verification ladder
- `perry/design/DESIGN-004-deterministic-writes.md` — the task writer
- `perry/decisions/ADR-002-no-cross-project-registry.md` — working directory is the scope
- `schema/task-list-contract.md` — the first frozen read contract
- `schema/README.md § Consumers` — the aimark parser decision, and its measured cost
