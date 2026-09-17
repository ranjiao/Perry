# TASK-444 readiness and bounded implementation proposal

Date: 2026-09-17. This is a read-only readiness analysis, not implementation, acceptance, or a V4 verdict.

**Recommendation:** separate a first-OKR draft persistence/edit/resume slice from canonical finalization. The slice has a coherent home in the existing goals CLI and typed readers, but **is not demonstrated feasible under the required net Python/test lines ≤ 0 budget**. Do not dispatch it as budget-compliant on the strength of reuse alone. The parent remains incomplete: KR creation/revision/withdrawal and complete overall/phase authoring writers are absent. A bounded commitment update is an existing supported destination for a later finalize demonstration; it is not a substitute for the first-OKR acceptance path.

## 1. Evidence boundary and authorization

- Checkout: `/private/tmp/perry-scratch/Perry/okr-isolated-20260917/planning-draft-audit`.
- Exact HEAD: `9051a43f78bb4e2f892c678c9b4ab54df8bfa376`, detached, clean at inspection. No alternate branch or unmerged candidate was treated as available code.
- The requested external spec, `/Users/bytedance/proj/Perry/perry/evidence/2026-09/TASK-444-spec.md`, is byte-identical to this base's `perry/evidence/2026-09/TASK-444-spec.md`; SHA-256 `5f4a68a2b83cd347046d20b23b96061a98408ab1937970a9f29890fb231eae5a`.
- Applicable `AGENTS.md`, root and routed Perry skills, current phase 004, DESIGN-020 decision 5 and §5.5, root architecture decided constraints, and the relevant bin architecture were inspected. No ancestor AGENTS file was found above the checkout.
- USER-959 permits isolated implementation before the real interview. It does not supply interview answers or acceptance evidence. TASK-191's real interview and TASK-465's delivery acceptance remain separate. No SkyTonight files were opened or written.
- **The `plans/` namespace is already consented:** DESIGN-020 decision 5 explicitly includes the one `claims[]` entry. The older phase text asking for that consent again is not a reason to repeat the question.
- **TASK-264 D3 is not authorized by that consent:** USER-952 remains pending. Do not implement KR add/restate/withdraw or invent its representation inside this slice.
- No code, test, dependency, PMO, goal, or architecture files were changed. No tests, test suite, mutation run, or broad corpus audit was performed. This report is the only authored deliverable. The update checker was omitted to preserve the requested read-only boundary.

Observed startup facts, from the tools rather than a manual dashboard reconstruction:

| Read | Result at the exact base |
|---|---|
| `bin/perry-state --section recovery` | `blocking: false`; no pending transactions or malformed dossiers |
| `bin/perry-state --section interrupted` | `[]` |
| `bin/perry-state --compact` | Installed; state root is this isolated checkout's `perry/`; phase `004-guided`, active |
| `bin/perry-state --section next --lane goals` | `primary: null`; `drafts.drafted` and `week.planned` explicitly unknown because their draft source does not exist |
| `bin/perry-task list --all --json --limit 1000`, selected rows only | TASK-444: not_started, startable=false, blocked_by TASK-264. TASK-264: blocked, blocked_by USER-952. TASK-191: blocked by USER-955. TASK-465 still depends on TASK-444 and TASK-191, among other rows. |

These are base-specific facts. The task reader already distinguishes authorization for an isolated child from the parent's blocked dependency. Nothing in this analysis changes those records.

Source anchors below are repository-relative at the stated HEAD. The external spec is the one exception. Core sources: `perry/evidence/2026-09/TASK-444-spec.md:9-34`; `perry/design/DESIGN-020-guided-planning.md:153-206,342-422`; `ARCHITECTURE.md:138-166,240-295`; `bin/ARCHITECTURE.md §3`.

## 2. Exact existing writer inventory

`bin/perry-goals` actually dispatches six commands: `list`, `krs`, `commit`, `link`, `measure`, `check` (`COMMANDS`, lines 3656 onward). It uses a legacy argument parser, not a full SURFACE. The similarly named skill procedures are not additional CLI writers.

| Existing surface | What it can actually do | Prerequisites and limits relevant to finalize |
|---|---|---|
| `perry-goals list`; `krs [--level overall]` | Read goals / declared KRs | No goal creation. Overall KRs come from `okr.jsonl`; phase KRs from `linkage.jsonl`. |
| `perry-goals commit --actor A --track T --promise TEXT --to TEXT --due DATE_OR_SLA [--by-when-note TEXT]` | Add one commitment, mint its ID; may add the Commitments section to an existing OKR | `Okr.__init__` refuses a missing `OKR.md` (362-367). Section creation requires a pipeline or queue track. Valid track/due and drift checks apply. Does not create an overall OKR. |
| `perry-goals commit --actor A --id ID [--promise TEXT] [--to TEXT] [--due VALUE] [--by-when-note TEXT] [--discharged-by TEXT]` | Update named fields of one existing commitment | Useful bounded supported destination. ID must already exist. Cannot silently re-date a missed active commitment. Existing drift policy still applies; a finalizer must not silently add `--accept-hand-edit`. |
| `perry-goals commit --close ID --discharged-by TEXT --actor A`; `--miss ID --reason TEXT`; `--migrate` | Close/miss a commitment; migrate the legacy clock columns | Existing operations, not planning-route creation. Migration is a separate operation and must not be smuggled into finalize. |
| `perry-goals link --actor A TASK KR`; `--alias PROJECT NAME`; `--project PROJECT KR NAME`; `--unlinked TASK` | Append attribution/project/alias/unlinked records; an edge can remove its previous unlinked declaration | Requires a current phase and usable existing linkage register. Resolves to existing KRs; does not create objectives, KRs, phase prose, or `phase/CURRENT`. Existing exact-duplicate cases can return `already`. |
| `perry-goals check KR [--okr-version V] --id S --direction D --target N [--baseline N] --label TEXT --actor A` | Append a typed check declaration to linkage | Requires an existing, writable KR. Superseding a check declaration is not superseding or withdrawing a KR. |
| `perry-goals measure KR [--okr-version V] --check S --value N --evidence PATH --actor A` | Append a measurement for an existing declared check | Evidence and typed target resolution are validated. Does not create the KR. Both check/measure write `linkage.jsonl`, including checks for an overall KR. |
| `perry-okr write --from-file` | Import the existing canonical-path `OKR.md` into `okr.jsonl`, with loss/malformed-store safeguards | It has no input draft path or typed overall-creation interface. It requires the file to exist. Authoring a canonical OKR by hand first would bypass the missing writer. |
| `perry-okr render --write` | Render existing stored records into the projection; can scaffold a missing projection from an existing store | Not an authoring API for new mission/principles/version/KRs. It refuses missing stores and unplaceable records; opaque layout is not manufactured from interview answers. |
| `perry-okr migrate-ids` | Mint stable Objective IDs for already stored records | Migration, not Objective authoring. `build`, `verify`, and `diff` are read surfaces. |
| `perry-task add --actor A --title TEXT --summary TEXT --deliverable TEXT --verification TEXT --kr KR_OR_PROJECT_OR_ALIAS` or `--unlinked`, with owner/priority/rung/etc. | Work's writer can create one proposed weekly task and its attribution | Goals must hand off to work. Each add has its own recoverable canonical transaction. No existing batch-week transaction, draft operation ID, caller-selected task ID, or add idempotency key is exposed. |

Goals writers expose `--root`, `--json`, and `--dry-run`; all mutating goals commands require a nonempty single-line actor. `--dry-run` is a preflight of that call, not a reservation of its later outcome. Never infer writer success just from a dry-run result.

Sources: `bin/perry-goals:1-125,342-367,706-758,761-895,1782-1890,2459-2764,3482-3658,3660-3920`; `bin/perry-okr:1-68`; `bin/perry_md_store.py:1394-1790`; `perry-task add --help`; `bin/perry-task:3290-3360`.

### Which destination can really finalize?

1. **A single commitment on an already initialized fixture is supported by an owning writer.** The smallest useful parent demonstration is updating one known commitment with `commit --id`, because the ID already exists and a retry cannot mint another goal. Example shape, not an executed command: `perry-goals commit --root <isolated-project> --id <existing-id> --promise <approved-text> --actor <actor> --json`. A successful, checked result can be referenced by its ID, `OKR.md`, and `okr.jsonl`. This demonstrates only the commitments/revision route.
2. **New commitment creation also has a writer**, but its generated ID and crash-before-draft-receipt window need additional reconciliation before automatic retries are safe. Do not advertise exactly-once creation yet.
3. **A week has per-task writers**, but completing 3–5 tasks across separate calls is not a transactional week finalizer. A durable association from every approved proposal item to the allocated task ID is missing. A later writer failing must not label the whole week finalized.
4. **First/revised overall OKR and first phase cannot presently finalize their full destination.** Missing: authorized KR add/restate/withdraw; complete overall document/version authoring; complete phase prose/objective/KR creation plus `phase/CURRENT` publication. TASK-264 alone would not fill all of these gaps. `plan-phase`/`revise` prose procedures and `perry-goals link` are not those missing tools.

A future finalize dispatcher must preflight the **whole destination**, including document, stores, pointer, and attribution, before its first canonical write. For unsupported OKR/phase routes, return a concrete missing-capabilities list with `written: false`; keep `OKR.md`, `okr.jsonl`, all phase files, `linkage.jsonl`, and `phase/CURRENT` byte-identical. No importer workaround, partial version creation, or “make the file first” instruction.

## 3. Smallest coherent child proposal

Proposed child title: **First-OKR draft persistence, current-content review, and explicit resume in isolated fixtures**. Do not mint a task ID or alter PMO state in this analysis.

Scope: only `horizon: okr`, `route: first`, `target: OKR.md`; installed isolated projects with no existing overall OKR. Save a meaningful draft after the first answer, preserve edits and rejected proposals, resume the pending question, produce the ≤12-line summary/file path, and safely record or refuse explicit approval. **No canonical finalization is implemented by this child.** Phase, week, commitments, and revision creation are explicit unsupported routes, even though their enum vocabulary is retained for the parent contract.

The user-facing child stops with “draft saved/approved; overall finalize unavailable”, not “OKR created”. It must not start a phase, create tasks, update KRs, run releases, or touch another project. It is smaller than implementing every horizon, a transaction coordinator, and the full new-project router together.

### Proposed CLI, all new and not available at this base

Extend `bin/perry-goals` with one command, `draft`, whose first positional argument is a mode. Do not migrate unrelated goals commands to a new parser framework.

```text
perry-goals draft create --root ROOT --horizon okr --route first --date YYYY-MM-DD
  --slug SLUG --target OKR.md --body-file FILE --step qN
  [--answered q1,q2] [--ask] --actor ACTOR [--dry-run] [--json]

perry-goals draft show --root ROOT --path plans/okr/YYYY-MM-DD-SLUG.md [--json]

perry-goals draft update --root ROOT --path PATH --expect-sha256 SHA
  [--body-file FILE] [--step qN|""] [--answered q1,q2]
  [--status interviewing|drafted] [--ask] --actor ACTOR [--dry-run] [--json]

perry-goals draft approve --root ROOT --path PATH --expect-sha256 SHA
  --actor ACTOR [--dry-run] [--json]

perry-goals draft abandon --root ROOT --path PATH --expect-sha256 SHA
  --actor ACTOR [--dry-run] [--json]

perry-goals draft finalize --root ROOT --path PATH [--json]
  # Child: capability refusal only; never writes anything.
```

`show` is the read used by resume; no mutation merely because a session resumes. Explicitly classify show/finalize-refusal as reads before the present writer gate: otherwise `READ_COMMANDS`, `ACTOR_SURFACE`, and main's default `Okr(...)` initialization would incorrectly demand an existing OKR for the draft that precedes it. All modes have exact allowed-flag sets; reject mixed modes, stray positionals, unknown flags, irrelevant flags, and valueless flags at exit 2. No `--accept-hand-edit`, free `--status approved`, or `--status finalized` escape hatch.

`show --json` returns the validated metadata, project-relative and absolute file paths, raw-file SHA-256, approval validity, and capability/refusal details. It may transport the body verbatim; it never summarizes it. The agent reads it and produces the summary. `--expect-sha256` is the raw digest returned by the last read, not a caller's guess based on a timestamp. `--body-file` carries only opaque UTF-8 body bytes; it cannot smuggle replacement frontmatter.

### File and schema scope

Exactly one new claim:

```json
{"path":"plans/","kind":"dir","owner":"goals","anchor":"state"}
```

The location and claim are already authorized. `owner: goals` is the concrete proposed ownership mapping for the draft; weekly canonical tasks still belong to work. Add `plans/` to the goals ownership predicate and the lane's ownership documentation, and reconcile the explicit schema-to-contract mapping in `tests/test_ownership.py`. Do not mark the new row as covered by the historical 2026-08-16 V5 signature, and do not grow that test's “known ownership gaps” whitelist. Reference the later DESIGN-020 decision for this addition.

Declare one `files[]` entry for `plans/*/*.md`, state anchored, optional, YAML frontmatter with an opaque body. Recognized-but-unimplemented horizons must be visible as unsupported rather than silently skipped. There is no new JSONL goal store and no shadow copy of canonical KRs. The human-editable draft is an explicitly noncanonical planning artifact; finalized copies are history.

Locked fields from DESIGN-020 §5.5:

```yaml
---
horizon: okr
route: first
status: interviewing
step: q4
answered: [q1, q2, q3]
target: "OKR.md"
created: 2026-09-17
updated: 2026-09-17
finalized_refs: []
questions_asked: 3
approved_sha256: null
---
```

**The final two fields are proposed additions, not fields approved by the locked example.** Their exact definitions must be settled in the bounded child contract before implementation; USER-959 and the `plans/` consent do not implicitly approve arbitrary schema extensions.

| Choice | Minimal concrete proposal and reason |
|---|---|
| `questions_asked` | Integer 0–8 for this first-OKR slice. Increment once with `--ask` when durably recording the next actual question; no prose counting. `answered` is coverage, not a question budget: follow-ups can revisit the same q-ID. Persisting only `answered` cannot enforce the current bank's eight-question total across sessions. |
| `approved_sha256` | Null or 64 lowercase hexadecimal digits. Set only by explicit approve mode after a fresh byte comparison. Clear on every material draft update. Needed to detect edits after an approved draft is left on disk. |
| Empty step | Exact `step: ""` outside interviewing; q1–q8 while interviewing. A numeric q-ID is a coverage address, not an instruction to advance numerically. |
| `finalized_refs` | Empty in every child-authored draft. Parent should choose an array of exact IDs/relative paths; no invented operation ledger hidden in this field. Parent success/failure journaling is a separate contract choice. |
| Schema discriminator | **Do not add `planning: 1` just to satisfy the linter.** Existing `check_frontmatter` unconditionally expects `spec_key/spec_version`. Make that discriminator optional only for specs without it; existing adoption/diagnosis declarations and validation stay intact. The approved horizon/route/status fields suffice to identify this file shape. |
| Other metadata | Do not add `approved: true`, `consent`, `quality_passed`, semantic approval scores, answer classifications, a duplicate body, or an operation framework. CLI actor follows the existing typed actor convention; it does not prove human consent. |

If the two additional fields are not accepted, the genuinely smaller alternative is **save/edit/show/abandon only**: no durable approval, and no claim that cross-session question-budget enforcement is implemented. Do not quietly claim the same child acceptance with those fields omitted. This is a scope reduction, not this report's recommended full slice.

Validate required keys/types, real ISO dates, `created <= updated`, unique q-IDs, q-ID range, status/step consistency, empty child refs, exact target, and horizon/path agreement. Reject duplicate/unknown metadata keys instead of the YAML subset reader's current last-value-wins map behavior. Reuse `P.split_frontmatter` and `P.parse_yaml_subset`; place the plan-specific reader/validation in `viewer/parsers.py`, including any narrowly needed duplicate-key check. No second YAML reader in the CLI.

### Create/update/edit/approval rules

1. **Root and safety gate:** resolve through `lib.resolve_project_root`, then `P.resolve_state_root`. Reuse `lib.refuse_write_unless_installed`. Use an explicit isolated `--root`; never reinterpret `.perry/config.jsonl`'s live `pmo_repo_path` as the destination. Existing recovery safety must pass before a draft write; an unrelated interrupted pipeline requires explicit selection, never automatic continuation. Do not import `perry-state` into a new writer to obtain the gate: shared typed recovery inspection belongs in the reader, while state/CLI consume it.
2. **Create once:** derive the destination from validated date/slug/horizon; if it exists, refuse and return the existing path. Do not suffix-and-create another draft automatically. `lib.write_atomic` replaces existing paths, so an existence check plus that function alone is not create-only. Reuse `lib.stage`, then an exclusive publication primitive (same-directory `os.link` refusing EEXIST, with temp cleanup), under the project lock. Stage only after all validation. No generic transaction class is needed.
3. **Update by comparison:** lock spans read, validate, compare, and write. Compare raw bytes/digest with `--expect-sha256` before making changes; re-read immediately before publication. On mismatch, return a conflict and the current digest/path; write nothing. Re-read the file, preserve the user's edits, and have the agent prepare the new body against that version. Do not offer an overwrite flag.
4. **Opaque prose:** Python may copy/hash bytes and update typed metadata; it does not locate “KR2”, interpret acceptance, merge sentences, run the rubric, or select a next question. For chat changes, the agent edits the requested body section in its candidate copy and checks that unrelated bytes survive. If a correction changes dependencies, name those affected proposals and update them as the existing bank requires; “edit only that section” must not freeze now-invalid downstream proposals.
5. **Lifecycle:** create interviewing; updates may stay interviewing or become drafted. Agent signals readiness explicitly; the tool never tests whether prose looks complete. drafted → approved requires approve mode. Any authored-content/target/coverage change to approved returns to drafted (or interviewing if more questions are explicitly required) and clears the approval digest. abandoned is terminal and retained. Child never writes finalized. Dates update only on an actual write; reads are byte-preserving.
6. **Review and stop:** re-read, show a useful absolute path and ≤12 lines, then offer approve/change-section/edit-file/abandon. Choosing file edit ends the turn. Continued discussion, “Use this” for a single proposed answer, silence, confidence, and a clean rubric are not whole-draft approval.
7. **Bind approval to content:** the reviewed raw digest must still match at approve time. Store `approved_sha256` over a precisely defined image: UTF-8 canonical JSON of `horizon, route, target, created, step, answered, questions_asked` (sorted keys, compact separators, no ASCII escaping), one LF, then the exact opaque body bytes. Exclude lifecycle bookkeeping `status, updated, finalized_refs, approved_sha256` to avoid self-reference. Metadata is rendered in a stable shape; raw digest is still used for optimistic write comparison. The approval content digest changes for body whitespace, destination, question state, or route changes.
8. **Resume approval safely:** readers recompute integrity and return `approval_valid: false` on mismatch, even if the file says approved. Reading does not rewrite status. Display the changed current content and require fresh explicit approval; never repair the hash automatically. A hand-typed status/hash is not authentication or proof of user consent. Even a valid approved draft must not trigger automatic finalization on startup.
9. **Honest concurrency limit:** a project lock serializes Perry writers, not arbitrary editors. Hash checks detect edits already published before the comparison; POSIX replace is not a compare-and-swap against an uncooperative editor. A final recheck narrows but does not eliminate the last-instant race. Do not claim absolute no-lost-update guarantees. A stronger guarantee would require a separately scoped coordinated edit/publication protocol, not a fictitious guarantee from `write_atomic`.

## 4. Integration seams and failure boundaries

### Question step and current-content approval

`goals/reference/elicitation.md:24-59` explicitly chooses the next consequential unresolved gap, counts every follow-up, and propagates user corrections. Therefore **do not implement `step = max(answered)+1`**, infer answered questions from headings, or equate three questions asked with q1/q2/q3 answered. `step` is chosen by the agent. Save the exact pending question and accepted/rejected wording in the opaque body so a new session can interpret it without reconstructing it from metadata.

Persist the pending question, step, and `--ask` increment before presenting it; persist the resulting meaningful body after the answer and before the next question. A crash after saving the question but before showing it conservatively consumes a question slot; resume displays the already recorded pending question without incrementing again. This is preferable to repeating an unseen or answered question and resetting the budget. At eight, draft with explicit unknowns rather than asking another question.

Premise challenge and unchanged rubric remain agent procedures before approval, not Python predicates. Their text and any override reason can live in the body. Re-reading a draft must not count as a new rubric run; a changed scope may require a fresh user-visible review, never an inferred pass. The existing first-OKR bank ends at a visible chat draft; replace only that final seam when persistence is actually available.

### State/recovery/next

- Add a single typed plan scan in `viewer/parsers.py`, consumed by `bin/perry-state` and goals. Use `P.split_frontmatter`/`P.parse_yaml_subset` only on frontmatter. Body bytes may be hashed or transported, never semantically inspected. No broad dossier refactor as a prerequisite.
- Feed valid plans into a new `drafts` payload on **both installed and uninstalled branches**. A plan can survive lost config; it must be visible before bootstrap. Do not use the mere presence of a plan to change the existing installed predicate.
- Report malformed/escaping/unreadable plans through the existing recovery error collection with `pipeline: plan`, exact path, and errors. Preserve pending task transactions and adoption/diagnosis errors, with `recovery.blocking` still winning. Never turn “scan failed” into an empty drafts list or zero count.
- Proposed projection: interviewing plans appear in `interrupted` as `pipeline: plan`, `stage: interviewing`, next `step`, dates, horizon/route, `interview_answers = len(answered)`, and `questions_asked`. Set inapplicable dossier counters to null; do not fabricate Objective/KR counts from body prose.
- **Drafted plans go to `drafts`, not `interrupted`.** Otherwise R-interrupted (ordered before R-draft-waiting) permanently masks the review path, contrary to DESIGN-020's “I'll edit the file → R-draft-waiting” behavior. Approved plans can appear as an explicit interrupted-finalization item, with “writer unavailable” in this child; they never execute automatically. This stage selection is a concrete public projection choice to specify, not an existing implementation.
- Set `drafts.drafted` from validated drafted plans plus stale-approved plans needing current-content review. On scan errors leave it unknown and report recovery; do not compute a comforting zero from only the valid subset. `week.planned` stays unknown: this child finalizes no week. No “no week drafts means unplanned” inference yet.
- R-draft-waiting already emits `/perry plan`, but the router has no implemented planning entrance at this base. Add only the narrow existing-draft resume/review route and its pointer in this child; do not ship a recommendation with no handler. When there is no existing supported draft, name the supported first-init entrance and unsupported horizon rather than claiming the full phase/week router exists.
- Update the plan-specific card in `reference/snapshot.md`; its current adoption text “Nothing has been written to the project yet” is false after a draft file is saved. The plan card should say canonical goals have not been finalized. Do not archive plans into `.perry/<pipeline>/archive`; abandonment keeps the state-root plan in place.
- Use the existing 30-day stale threshold as the proposed plan threshold, explicitly add its applicability rather than hardcode a new value. Stale never means abandoned automatically.

Sources: `bin/perry-state:1593-1820,1843-1848,2073-2074,2398-2470,2894-2895`; `reference/next-rules.json:32-56`; `reference/snapshot.md:20-62`; `viewer/parsers.py:4033-4242`. The existing dossier scan contains its own limited frontmatter extraction despite the decided single-reader boundary. That is a reuse/paydown candidate, not permission to add another parser in a tool.

### Path containment

For child writes, require the resolved state root to stay inside the explicitly selected isolated project. Reject absolute plan paths, `..`, empty components, extra depth, wrong extension, malformed date/slug, horizon/path mismatch, and a child target other than literal `OKR.md`. Restrict slug to an explicit ASCII alphanumeric/hyphen grammar. Resolve and check containment; reject symlinks in the plans directory, horizon directory, and destination, including dangling links. Do not rely on `startswith` string checks or `glob` silently ignoring bad names.

The reader should enumerate unexpected entries under claimed `plans/` and report invalid names/links without following them outside the root. `--body-file` is a read-only input, permitted outside the project as a scratch file; reject directories, unreadable files, and self-input ambiguity. No body-provided path becomes a write destination. Validate before creating directories/staging; `--dry-run` must not leave even an empty `plans/` tree. Hostile concurrent directory replacement is beyond a path.resolve check; if that becomes part of the required threat model, use directory-fd operations in a separately measured implementation rather than claiming the check solves it.

### Atomicity and finalization recovery

| Boundary | Actual guarantee / required handling |
|---|---|
| Draft only | One file containing metadata and body, atomically replaced using existing helpers. Failed preflight/conflict leaves it unchanged; temp-stage failures clean up. No new PMO journal or canonical goal writes. |
| `perry-goals commit` | `write_okr_and_store` validates in memory, then writes **OKR.md first, okr.jsonl second** (879-884), then appends a derived event. Its docstring says “or neither”, but the implementation has no recoverable multi-file transaction marker. A crash can leave drift. Preserve and expose that limitation. |
| `link`, `check`, `measure` | One atomic linkage-store replacement followed by a derived event. Event failure is returned as `event_written: false`; canonical success is not undone. |
| `perry-task add` | Canonical task/register/linkage/journal entries use `replace_canonical_pair` and `.perry-task-transaction.json`; derived event follows. Recovery may be required before any next write. This covers one add, not a whole week and its draft receipt. |
| Canonical success → draft receipt | Separate writes today. If the writer succeeds and draft finalization fails, report “canonical result exists; draft receipt pending”, retain exact returned IDs/paths, and reconcile before any retry. A nonzero/ambiguous writer outcome is not proof of zero writes. |

Do not import `perry-task` transaction internals into goals: bin architecture forbids tool-to-tool imports except its named existing task/tasks pair. Do not extract a new generic transaction framework to make this slice look complete. Reuse the owning writer through its public entry point; never hold a project lock while spawning another command that needs the same lock.

For the later **single existing commitment update** demonstration: bind the exact approved body to the typed writer arguments shown to the user; preflight; invoke the owning writer; verify the known commitment and projection/store consistency; then write refs and finalized. On partial failure, stop for reconciliation of that known ID and the observed bytes. Repeated finalize of a recorded finalized draft returns its references without invoking the writer. Re-entry after an ambiguous result must not issue a blind new `commit` call. If the event alone failed but canonical state is verified, report the event warning; do not mint/rewrite a goal to recreate the event.

Safe autonomous retries of **new** commitments or weekly task batches need a durable per-operation association/intent and writer-supported reconciliation. Neither `approved_sha256` nor `finalized_refs: []` closes the crash-before-ID-receipt window. Fields such as `finalizing`, `operations`, `operation_id`, or `writer_receipts` are **not approved in DESIGN-020's draft schema**; do not invent them in this child. Stop on ambiguous outcomes. The parent's repeated-finalize acceptance must explicitly test this boundary before it can be claimed.

## 5. Exact proposed edit boundary and budget

No file listed here has been edited. This is the maximum bounded file list for the proposed slice; an executor should not turn it into a cleanup budget across the repository.

| Files | Bounded purpose |
|---|---|
| `bin/perry-goals` | Draft command/mode dispatch, strict flags, actor/read classification, goals ownership, root/safety gate, lock/compare/write; no changes to canonical writer semantics |
| `viewer/parsers.py` | One plan metadata/body-transport reader, strict typed validation/containment, integrity calculation; minimal shared recovery-reader seam if required by the writer gate |
| `bin/perry-state` | Consume plan records in recovery/interrupted/full payload and next facts; preserve existing startup ordering |
| `bin/perry-lint` | Reuse the plan validator; optional discriminator handling without weakening existing dossier validation |
| `schema/state-schema.json` | One consented claim, one file declaration, lifecycle/question enums/field constraints, explicit stale applicability; only the proposed public metadata choices described above |
| `schema/README.md`, `schema/next-contract.md` | Document draft payload/facts, unsupported finalize, error visibility; no unrelated contract/version changes |
| `goals/reference/planning.md` (new) | Compact procedure and CLI/field contract; no framework or new question bank |
| `goals/reference/setup.md`, `goals/reference/elicitation.md`, `goals/SKILL.md` | Replace the first-init stopping seam with persistence/review/resume; leave rubric and bank response rules intact |
| `SKILL.md`, `reference/snapshot.md`, `reference/next.md` | Narrow existing-draft `/perry plan` handling, plan card, ownership addition with DESIGN-020 provenance; no full horizon router |
| `tests/test_goals_writer.py`, `tests/test_resume.py`, `tests/test_next_section.py`, `tests/test_ownership.py` | Add bounded behavioral cases and explicit ownership mapping; preserve every meaningful existing assertion |
| `tests/test_shipped_vocabulary.py` | Register the new agent-facing reference only if required by its existing explicit vocabulary inventory |

`bin/lib/__init__.py`, `bin/perry-task`, `bin/perry-okr`, `bin/perry_md_store.py`, the unchanged rubric, decided architecture, PMO stores, and release records are **reuse/read-only**, not proposed refactor/paydown territory. Include accurate COVERS entries in touched test modules so later affected-test selection sees the actual production paths.

### Measured base sizes

Measurement: physical source lines via `Path.read_text().splitlines()`; test methods counted by Python AST names beginning `test_`. This is static measurement, not test execution. All are at the exact base; doc-comment deletion is not counted as a proposed behavioral simplification.

| File | Physical lines | Existing test methods |
|---|---:|---:|
| `bin/perry-goals` | 4,098 | — |
| `bin/perry-state` | 3,321 | — |
| `viewer/parsers.py` | 5,340 | — |
| `bin/perry-lint` | 6,151 | — |
| `bin/lib/__init__.py` | 2,649 | — |
| `bin/perry-okr` | 68 | — |
| `bin/perry_md_store.py` | 1,812 | — |
| `tests/test_goals_writer.py` | 2,012 | 114 |
| `tests/test_resume.py` | 523 | 49 |
| `tests/test_next_section.py` | 812 | 42 |
| `tests/test_ownership.py` | 679 | 27 |
| `tests/test_goals_kr_writer.py` (preserve, outside proposed edits) | 636 | 45 |

The four proposed production files total **18,910 lines**. The four principal touched test files total **4,026 lines and 232 existing test methods**. Current checkout diff is zero; no speculative phase-wide deletion credit or other branch's savings is available to spend.

### Reuse is real; deletion credit is small and unproven

| Existing mechanism measured | Reuse / legitimate paydown assessment |
|---|---|
| `P.split_frontmatter`: 9 lines; `P.parse_yaml_subset`: 144 | Reuse avoids another parser. It deletes no existing code by itself. Strict plan keys/types/duplicates still need validation. |
| `lib.stage`: 40; `write_atomic`: 20; `project_lock`: 68 | Reuse avoids new locking/temp/replace infrastructure. These helpers remain necessary; their 128 lines are not deletion credit. |
| `inspect_dossier`: 58; `dossier_records`: 16 | Local opportunity: replace the duplicate extraction with the existing reader while preserving exact recovery errors and behavior. Moving the function to parsers is net zero. Even deleting both entire functions would free only 74 lines and would remove required behavior; realistic net savings are much smaller. |
| `count_list_items`: 19; `count_status`: 6 | Potential eventual reuse of parsed dossier metadata, but changes existing adoption/diagnosis semantics and tests. Entire deletion frees at most 25 lines before replacement costs. Not budget credit for a plan-only task without that bounded proof. |
| Test `_load`: 9; `_load_lint`: 8 in `test_goals_writer.py` | Could replace two local loaders with two existing `inproc.load` calls: approximately 15 lines saved if module caching/isolation remains equivalent. This preserves assertions but must be verified; not 17 free lines. |
| `tests/inproc.py`: 183; `tests/config_store.py`: 140; `tests/goals_actor.py`: 28 | Reuse fixtures/runner/actor setup; no new harness. Parameterized new cases can share setup while retaining each failure's assertions. Existing assertions are not disposable paydown. |

An implementation estimate, **not measured diff**, is roughly **+220–360 production lines and +140–220 test lines**, after using the existing parser, lock, atomic, fixture, and runner mechanisms. The work includes strict modes/validation, stale-edit and approval handling, safe discovery, three state surfaces, and meaningful negative tests. The recovery-reader seam may add more; it is not assumed free.

Even the invalid optimistic exercise of deleting the full 58+16+19+6-line dossier functions plus saving 15 loader lines yields only **114 lines**, versus the estimate's **360-line minimum addition**. Those functions cannot actually be deleted without preserving their jobs. The realistic local savings are smaller still. The estimate does not become a proof merely by putting it in a table, but there is no identified bounded source of enough legitimate paydown.

**Feasibility result: infeasible to commit to this slice under net Python/test lines ≤ 0 with the currently identified, authorized edit boundary.** This is a readiness blocker, not proof that every possible implementation is impossible. Both a combined-lines reading and a separate nonpositive-production/nonpositive-tests reading fail this proposed budget. TASK-444's spec explicitly applies the ceiling even though the phase narrative describes it under Objective 4; use the stricter task constraint.

Do not pay by removing assertions, shrinking tests to happy paths, minifying, deleting explanatory material solely to offset line count, migrating code into uncounted extensions, or refactoring arbitrary legacy writers. A later dispatch needs either a separately scoped and measured behavior-preserving paydown large enough to cover the diff, or an explicit budget/scope decision. A documentation-only draft procedure can fit a zero-code budget but cannot satisfy persistence/resume/approval acceptance and must be named accordingly.

## 6. Acceptance boundaries for a later implementation

The child would need targeted isolated cases for: create collision; first-answer persistence; interruption after the third actual question with a non-numeric next gap; preservation of earlier accepted/rejected wording; direct file edit; stale update token; approve-then-edit; explicit edit/abandon choices; malformed/duplicate metadata; path traversal and symlinks; recovery precedence; drafted review versus interrupted overlay; missing-writer refusal with byte snapshots of all canonical paths; and stage/publish failure leaving old bytes and no stray temp files. Tests exercise observable behavior, not copies of the implementation. Independent review must inspect the visible edit/approve flow against the written child criteria.

Parent TASK-444 still additionally needs actual owning-writer success, failure after a canonical write, receipt reconciliation, no duplicate goals on repeated finalize/resume, full-destination preflight, and the remaining horizons' explicit support boundaries. At least the supported commitment-update path must be demonstrated; that result cannot claim overall/phase initialization is complete. TASK-264 authorization and the remaining complete-authoring writer gaps need their own decisions/deliveries.

The real interview remains TASK-191/TASK-465 evidence. Fixture transcripts must be labeled synthetic and cannot fulfill that release gate. The implementing session cannot self-award V4 or V5. Full/slow merged verification and release allocation remain integration work, per `release/README.md`; none is claimed here.

**Concrete next proposal:** retain TASK-444 incomplete; use the first-OKR child boundary above only after its two exact metadata additions/projection choices and an honest line-budget resolution are recorded. Keep canonical finalization out of that child. Do not begin implementation by assuming TASK-264, importer-based goal creation, cross-file atomicity, or automatic approval already exists.
