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

## DESIGN-023 F activation successor

`tools/TASK-492-adr-successor.json` is a reviewed-input candidate, not an activated
ADR or human sign-off. At activation root/decide re-reads ADR-025, DESIGN-023 and
current native IDs, verifies actual prior authority, drafts/attaches the body,
creates the ADR through the CLI, and records typed authorized_by/aligned_to links.
Obtain the actual minted ID after the filename ceiling is reconciled. This coding
agent never writes `perry/decisions/` or declares that the user signed F/H.

## Migration and refusal boundary

The one-shot `tools/goals_decide_migrate.py` reads copied actual filesystem data,
including uncommitted ADRs and superseded/archived headers. Source hashes,
version-scoped label maps and attachments are review evidence. It never reads
metadata from git HEAD as a substitute for the actual files.

Use its plan before any write. Every rehearsal names --root and --store under
its external --work directory with PERRY_KERNEL_TESTING=1. Existing native work
items/events/IDs must remain exactly unchanged. Replay/export parity, a no-write
idempotent rerun and current-source reconciliation are required independently.
A sparse filename floor that existing CLI cannot reserve is a blocker with the
bounded proposal in tools/TASK-492-kernel-proposal.md; no fake item, direct event/
SQLite edit, or import over a nonempty native store is allowed.
Live activation follows fresh backups, independent review and root/user authority;
never copy a rehearsal database into the live store. Root owns legacy H disposal.
