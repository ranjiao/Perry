# Planning drafts — save, review, resume

Loaded by `init` (first OKR) and by `/perry plan` when a draft already exists.
DESIGN-020 § 5.5; TASK-444's draft-only slice. **This slice ends at "draft
saved / approved; overall finalize unavailable".** It never says "OKR
created", and never writes `OKR.md`, `okr.jsonl`, `linkage.jsonl`, `phase/`,
`phase/CURRENT` or tasks.

## The file

`<state root>/plans/okr/<YYYY-MM-DD>-<slug>.md` (slug: `a-z0-9` and hyphens).
Typed frontmatter the tool writes, then a body in the target document's shape
that you and the user write. The body is useful from the first answer: record
accepted wording, rejected suggestions, unknowns and **the exact pending
question**, so a new session can resume without reconstructing anything.

| Field | Meaning |
|---|---|
| `horizon` / `route` / `target` | `okr` / `first` / `"OKR.md"`. Other horizons (`phase`, `week`, `commitments`) and `revision` are refused as unsupported |
| `status` | `interviewing` → `drafted` → `approved`; `abandoned` is terminal. `finalized` is vocabulary only here |
| `step` | the pending question (`q1`–`q8`) while interviewing, **chosen by you** — never `max(answered)+1`; `""` otherwise |
| `answered` | coverage: unique q-ids. Not a count — a follow-up may revisit an id |
| `questions_asked` | every question actually asked, follow-ups included; `--ask` adds one. The tool refuses a ninth: at eight, draft with explicit unknowns |
| `approved_sha256` | set only by `draft approve`; cleared by any change. See *Approval* |
| `decided_by` | the `--actor` of the `approve` or `abandon` that set the status; cleared by any later update. Drafts append no event, so this is the record of who decided |
| `created` / `updated` / `finalized_refs` | dates of the file and of its last write; `[]` in this slice |

Python validates these fields and hashes the body. It never reads the body: it
cannot tell whether prose "looks complete". Readiness is your explicit
`--status drafted`.

## Commands

All take `--root <project>`; writers need `--actor <who>`; `--json` gives the
payload; `--dry-run` validates and writes nothing. `draft` must be the first
argument. Unknown, repeated, valueless or mode-foreign flags exit 2.

```
"$PERRY_HOME/bin/perry-goals" draft create --root . --horizon okr --route first \
    --date <YYYY-MM-DD> --slug <slug> --target OKR.md --body-file <tmp.md> \
    --step <qN> [--answered q1,q2] [--ask] --actor <who> --json
"$PERRY_HOME/bin/perry-goals" draft show --root . --path plans/okr/<file>.md
"$PERRY_HOME/bin/perry-goals" draft update --root . --path <p> --expect-sha256 <sha> \
    [--body-file <tmp.md>] [--step <qN>|""] [--answered q1,q2] \
    [--status interviewing|drafted] [--ask] --actor <who> --json
"$PERRY_HOME/bin/perry-goals" draft approve --root . --path <p> --expect-sha256 <sha> --actor <who> --json
"$PERRY_HOME/bin/perry-goals" draft abandon --root . --path <p> --expect-sha256 <sha> --actor <who> --json
"$PERRY_HOME/bin/perry-goals" draft finalize --root . --path <p> --json   # refused, see below
```

- `--body-file` is a scratch file holding the **whole body** (never a
  frontmatter). To change one section, copy the body from `draft show`, edit
  only that section, and check the other bytes survived. If a correction
  changes what later proposals depend on, update those too.
- `--expect-sha256` is the `sha256` of your last `draft show` (or write). A
  mismatch means the file changed — usually the user edited it. Nothing is
  written; re-read, keep their edits, redo your change against that version.
  There is no overwrite flag. The project lock serializes Perry writers only;
  the re-read narrows, and does not close, the race with an open editor.
- `create` refuses when the file exists (it returns the existing path; resume
  it), when an overall OKR already exists, and for a `--date` later than today.
  Every write refuses on an uninstalled project, and while `perry-state
  --section recovery` is blocking. A disk or permission error is a refusal
  (exit 1, `io_error: true` under `--json`), never a traceback.
- A draft whose frontmatter is broken refuses every write, `abandon`
  included, and names each field to fix. Fix those lines by hand, then re-read.

## The loop

1. After the first answer, `create` with the answer in the body and the next
   question as `--step`, `--ask`. Persist each question (`update --ask
   --step <qN>`) **before** showing it, and each answer before asking the
   next. A crash between saving and showing costs one question slot; on
   resume show the recorded pending question and do not `--ask` again.
2. When no consequential gap remains, `update --status drafted --step ""`.
3. **Review**: `draft show`, then show the absolute `file` path and a summary
   of 12 lines or fewer, and ask
   `Approve (Recommended) | Change a section | I'll edit the file | Abandon`.
   The premise challenge and the rubric run before approval, as in
   `reference/setup.md`.
   - *Change a section* → edit that section as above, `update`, review again.
   - *I'll edit the file* → **stop the turn**. The next `/perry` shows the draft
     waiting (`R-draft-waiting`); re-read it then — the file is the truth.
   - *Abandon* → `draft abandon`. The file stays as a record.
   Continued discussion, "Use this" on one answer, silence, confidence or a
   clean rubric are not approval of the draft.
4. **Approve** only on the explicit choice, with the `sha256` of the version
   the user just reviewed.
5. Then say: *draft approved; overall finalize is unavailable* — and stop.

## Approval

`approved_sha256` is SHA-256 of the sorted, compact, unescaped JSON of
`horizon, route, target, created, step, answered, questions_asked`, one LF,
and the exact body bytes. Every reader recomputes it: `approval_valid` is
false the moment any of those bytes change, even though the file still says
`approved`. Reading never repairs it and never rewrites status — show the
current content and ask for a fresh approval. A hand-typed status or hash is
not consent. Any `update` returns an approved draft to `drafted`.

## Finalize is unavailable

`draft finalize` exits 1 with `written: false` and the missing writers: an
overall-OKR authoring writer, and the KR add/restate/withdraw writer
(`TASK-264`). Nothing is written. Do not hand-author `OKR.md` and import it,
and do not finalize on startup — not even a validly approved draft.

## Where it shows

`perry-state`: an **interviewing** draft is an `interrupted` row
(`pipeline: plan`, its `step`, `interview_answers`, `questions_asked`); a
**drafted** one — or an approved one whose content changed — counts in
`drafts.drafted`, which fires `R-draft-waiting`. A malformed, linked or
misnamed entry under `plans/` is a `drafts.errors` row (path and errors) — show
it to the user; it blocks nothing but writes to that file — and
`drafts.drafted` is then null rather than zero. Dotfiles (`.DS_Store`) and
editor backups (`*~`, `*.swp`, `*.bak`) are ignored. Stale after
`stale_run_days` (30) like any run; stale never abandons a draft.
