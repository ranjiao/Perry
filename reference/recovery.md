# Safety before native state

Run this read-only procedure before any native query in a project operation.
It replaces the old `perry-state` recovery/interrupted projections. It is a
skill procedure; it does not repair, resume or mutate anything automatically.
Apply the configured document/chat languages and actual project root.

1. Resolve the document root from explicit project instructions and authored
   preferences (`config.md`). Existing `.perry/config.jsonl` is a frozen fallback
   for unchanged root/language metadata, not a new state writer. If it is needed,
   check every JSONL record and unique setting before using it. Refuse absolute
   roots, escapes, malformed/ambiguous metadata and unresolved contradictions.
   Still inspect `.perry` restore points before any setup. Then run
   `python3 tools/document_checks.py startup --root <absolute> --state-root <relative>`
   and inspect every recovery error, interrupted row and draft warning. The helper
   never repairs or resumes. Apply the following procedure to its actual facts.
2. Inspect `<state_root>/.perry-task-transaction.json`. Its mere presence is a
   blocking legacy transaction, including a malformed/unreadable marker. Name
   the path; do not delete it or start another writer. Restore/repair with the
   original transaction's backed-up files under an explicit repair plan.
3. Enumerate **all** direct `*.md` restore points in `.perry/adoption/` and
   `.perry/diagnose/`, including hidden names. Do not follow symlink paths or
   silently skip unreadable files/directories. Require opening/closing `---`
   frontmatter, no duplicate required keys, discriminator `adoption: 1` or
   `diagnosis: 1`, and a valid stage/step as listed below. A malformed record
   blocks normal state reads and writes; report each path and exact defect.
4. Inspect plan drafts under `<state_root>/plans/` using the goals draft
   procedure. An unreadable/invalid plan is reported and blocks writes to
   that plan; it never becomes a valid interrupted card. A legacy interviewing plan
   joins the interrupted-run list; drafted/approved plans wait for their owning
   procedure. New F narratives have no duplicate lifecycle frontmatter: their
   native goal/phase drafts remain visible in queries and never auto-resume. Do not finalize or re-approve a changed draft.
5. A valid nonterminal dossier requires a user choice before setup, dashboard
   or action: Resume at the recorded stage/step; archive and start over; or
   Abandon in place. A plan offers resume/abandon only. Present the stored
   answers and the remaining step without estimating counts. A flag mismatch
   (`depth`, `only`, root) must be resolved explicitly before resuming.

Terminal dossier stages are `done` and `abandoned`. Adoption stages are
`scan`, `harvest`, `infer`, `confirm`, `commit`, `done`, `abandoned`; diagnosis stages
are `scan`, `read`, `interview`, `prescribe`, `execute`, `done`, `abandoned`.
Adoption confirm steps: `state_root`, `goals`, `phase`, `clusters`,
`attribution`, `transcriptions`. Adoption commit steps: `config`, `okr`,
`phase`, `design`, `board`, `linkage`, `decisions`, `knowledge`,
`architecture`, `risks`. Diagnosis interview steps: `q1`–`q6`, `audience`,
`attachment`; execution steps match `rx-` followed by digits. An optional step
may be absent; a present step must match the stage-specific list. Unknown
stages or duplicate keys are malformed, including a purported terminal stage.
Before accepting a stage/step, cross-check the lane's current dossier procedure
and scaffold; any disagreement is an error to resolve, never a silent default.
Read the exact required enum from those documents, not a retired state schema.
The user decides whether a stale run should be abandoned; age never authorizes
abandoning it. Preserve rejected/deferred answers when archiving.

Once these file-safety checks pass, a native command's corrupt/foreign/busy
store error also blocks the operation. Follow the kernel's supported store
checks/export and backup receipt; never edit SQLite or substitute another
project's store. Optimistic `expect` and factual actor/session identity apply
to every state write. A lock or successful query is not permission to overwrite
another session's documents.

## Red demonstrations required before retirement

The delivery evidence must show: a transaction marker stops a query; malformed
frontmatter and unreadable restore points are reported; a valid interrupted
adoption in a project with no store prevents setup; a mismatched resume scope
waits for a choice; an interviewing plan never auto-resumes; foreign/corrupt
stores never fall back to JSONL; stale `expect` refuses a write. Use isolated
fixtures and record actual agent traces. A prose checklist alone is not proof
that these cases were executed.
