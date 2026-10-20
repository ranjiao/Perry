# Skill procedures and safety gates

The kernel stores state and enforces declared shape guards. The skill judges meaning.
Use `reference/kernel.md` and `bin/perry describe` for exact native inputs.
No legacy command is a compatibility interface. Never edit SQLite, JSONL exports,
or frozen legacy registers. Read all query pages before claiming complete counts.

## Before state reads

Resolve the absolute project root and declared document root from the user's
project instructions. For an existing project with unresolved layout, stop and
report the ambiguity. Run the read-only skill gate:

```bash
python3 "$PERRY_HOME/tools/document_checks.py" startup --root /absolute/project --state-root perry
```

Replace `perry` with the actual declared relative document root. A blocking
recovery error stops all later project reads and writes. Report every exact
path/error. Do not rename corrupt files out of the way. If interrupted rows
exist, show their stage/age and ask the user whether to resume, inspect or abandon;
never resume automatically. A stale row is a recommendation to abandon, never
an authorization. Read-only startup does not recover or retire anything.
After recovery and interruption clear, query the native store. A missing store
on an existing project is a migration gap, not permission to initialize.

## Ownership and high-stakes decisions

Read the actual `.perry/safety.json`, applicable hook, role additions and dispatch preflight. Follow `safety-policy.md`. Screen the actual
operations, including foreign paths, install/deploy/publish/merge and changes to
the safety gate itself. Quoted examples and editing a command's source are not
executing that command. Explain uncertain matches; do not weaken the hook.
Prepare a dispatch JSON packet and run:

```bash
python3 "$PERRY_HOME/tools/document_checks.py" dispatch --input /absolute/scratch/dispatch.json
```

Packet fields are absolute project `root`, `scope` (relative paths), `spec`, `lane`, factual `actor`, and
`authorization` (actual session instruction/reference or null). Refusal,
missing/unreviewed/unarmed structured policies, foreign ownership or unresolved authority stop the
operation. The helper checks structure; the agent still decides whether the
recorded authorization actually covers the exact action. Another lane's document
requires its owning procedure. Existing explicit authority persists; do not ask
again for an already authorized action. Integration and live activation remain
separate actions with their own authority.

## Evidence, review and acceptance

Before moving a task to done, read its criteria, open the deliverables and verify
each criterion against actual behavior/evidence. Missing evidence, failed checks,
or an unreadable artifact stop closure. Record unrun checks and limits. A field
containing an evidence path proves only that the field is present.
Use `review --input /absolute/scratch/review.json` with `verification`,
`evidence` paths, `implementer`, `reviewer`, `criteria`, `verdict`, actual `actor`
and `human_signoff` reference. A structural success is not semantic acceptance.
V4 requires a fresh context independent from implementation, its written verdict
and criterion-by-criterion evidence. V5 requires the named human's actual signoff
of the concrete immutable artifact. An agent cannot manufacture a human actor or
turn implementation authority into acceptance. Preserve kernel guard refusals.

## Ordinary document checks

Before publishing a document, the owning lane reviews: required sections; each
claim's source; ID/title consistency; resolvable references; language; ownership;
contradictory decisions; acceptance criteria and verification limits. Open each
referenced document needed to support a consequential claim. Compare duplicated
facts to native queries and remove stale current-state copies. Read prose for
meaning; a heading, regex match or small line count does not prove correctness.
Record material gaps against the criterion, with path and a concrete fix.

The old narrative regex/heading budgets, deterministic next-step evaluator,
method-specific mode/diagnosis scores and obsolete projection checks were retired
under the actual user-approved H list. The finite source inventory retains its
original proposal labels; actual approval/V5 is a separate dated record. An
absent old check is not a passing test or a new semantic verification.
Safety checks above are replacements, never dropped. Retain reviewed red cases:
a malformed recovery marker, interrupted dossier, unauthorized high-stakes scope,
foreign ownership, missing evidence, self-review and fabricated human signoff
must all stop their corresponding procedure.
