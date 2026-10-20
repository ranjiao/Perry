# Root procedures

These are skill operations, not native CLI subcommands. Load the owning lane for
all mutations. Read `operating-rules.md` before project state.

## `/perry adopt`

Follow `adoption.md`: scan → harvest → infer → confirm → materialize → recheck.
Evidence proposes; the user declares. Source claims, goals, attribution and
transcribed decisions cannot be invented from commit messages.

## `/perry diagnose`

Follow `diagnose.md`: measure → read → interview → prescribe → gated execute →
recheck. Offer the smallest justified change, including zero findings or removal.
There is no hidden deterministic diagnosis or current-state parser behind this
procedure. Retain measurements and uncertainty with each finding.

## `/perry relocate <path>`

This relocates ordinary skill documents only. Store migration is a separate,
explicitly authorized operation using native export/import and backup receipts.

1. Resolve both absolute roots and ownership; require a clean relevant tree.
2. Enumerate the finite owned document paths and every attachment/reference that
   would change. Include plans, knowledge, evidence and linked module documents
   actually in use. Do not use a removed schema's claims as an implicit list.
3. Check exact destination collisions, including symlinks and foreign roots.
   Show every from → to and proposed reference update for user agreement.
4. Retain a restorable Git/source checkpoint. Move owned documents, never delete
   or overwrite foreign content. A cross-repository move needs each repo's
   authority and independently reviewable commits.
5. Owning lanes update their references. Use native `attach` operations with
   actual actor and read sequences for changed attachments. Document-root
   preference changes use `config.md`; never edit JSONL or copy SQLite.
6. Open affected references, query affected items and verify the complete move
   list against the checkpoint. Record unresolved references; do not declare a
   partially relocated project complete. Follow `next.md`.
