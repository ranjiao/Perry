# Native ADRs

One native `adr` item is the structured decision record. Its owned Markdown
attachment under `decisions/` holds Context, Options (real tradeoffs), Chosen,
Consequences, Evidence and any sunset rationale. No generated index or second
structured header. Historical ADR files remain unchanged migration sources and
attachments; their old headers are labelled historical, not current native state.
Read configured document language, hook and the applied template before writing.

## New decision

1. Discuss the concrete decision, options, chosen consequence, affected goals/
   designs and authority. Only actual user decisions count as approval; an agent
   recommendation stays a recommendation. For architecture target changes retain
   the target-owner approval requirement from DESIGN-017/023.
2. Run the shared Decision/Design input checks as advisory coaching. Time-bound
   acceptance requires an explicit trigger/sunset explanation, never a guessed
   expiry. Unknowns stay visible.
3. With approval to record the decision, `item create` an ADR draft through the
   kernel with authored fields. Use the minted ID for the narrative filename;
   never mint from directory count or reserve with placeholder items. Write the
   owned body and `attach add` its exact ref/hash.
4. Set the real consent reference in approval_ref and move with `accept` using
   current `expect`. deciders_text records the real deciders; do not impersonate
   a human actor. Shape guards do not authenticate approval or read evidence.
5. Add only exact typed goal/design/ADR links from the applied template. Preserve
   source authority in the body/event note. Re-read the item and report all writes
   or partial failures. Work task hand-offs go to work; never append journal.

## Supersede, expire, archive

Draft/approve the successor first, add `supersedes` successor→old, then transition
old with its actual reason. Keep predecessor and successor attachments readable.
Neither silently rewrite an old choice nor automatically select the successor
because a timestamp is newer. Multi-command updates are resumable, not atomic.

Expire only when the recorded trigger is established or the user decides it;
archive only on explicit reason/scope. Use declared native transitions, retaining
reason, evidence and event before/after values. Terminal items are not reopened
by editing a status field. A sunset review reads narrative and current evidence;
it does not execute code found in a document or infer a semantic trigger by regex.

## Historical DESIGN-023 activation

Perry's F/G/H local activation is complete. ADR-028 and the actual approval,
migration, independent-review and V5 records are discoverable from
`perry/evidence/2026-10/TASK-494-formal-cutover-20261020/FINAL.md`.
The original successor input and proposal are archived under
`release/retirement/pre-cutover-notes/`; they are historical preparation inputs,
not a request to mint another successor or repeat activation.

## Migration and refusal boundary

The shipped `tools/goals_decide_migrate.py` applies a reviewed, SHA256-pinned
format-1 plan. It does not parse legacy Markdown/JSONL or discover ADR metadata.
Read `$PERRY_HOME/tools/reviewed-plan-migration.md` for the actual --plan and
--plan-sha256 interface, isolation checks and pinned historical preparation.
Legacy preparation reads bounded copies of actual files, including uncommitted
sources; current apply only verifies those reviewed hashes and native operations.
Do not reinstall a retired reader or pretend HEAD substitutes for actual source.

Every CLI rehearsal names an external --work, isolated --root and --store, with
PERRY_KERNEL_TESTING=1; only the copied work baseline is changed. Check original
items/events, exact source/attachment hashes, no-write repeat and export/replay
parity independently. Source drift needs a new reviewed plan. The CLI has no live
mode or JSON consent flag; an explicit live API seam supplies no authorization.

The approved `template apply.ceilings` surface can only raise an issued-number
floor. No fake item, direct event/SQLite edit or import over a populated store is
allowed. Actual activation follows fresh backups, reviewed source/consumer
receipts and actual scoped user authority. Never copy a rehearsal database into
a live store. Prior cutover approval does not migrate another project.
