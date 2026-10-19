# Knowledge promotion

Evidence proposes; the user declares. A card is a durable claim the project can
re-check, not an agent's interesting guess. Work owns knowledge documents. Read
`reference/operating-rules.md` and `tools/helper-contracts.md` first. The retained
`tools/knowledge.py` is a read-only API; it has no propose/promote writer.

## Capture points

After closing a verified task, or once for an end-phase retro, consider a card
only if actual evidence supports a durable one-line claim and an observable
invalidation condition. Dropped tasks do not trigger promotion. For incident
closure, include the card choice inside its existing knowledge question; add no
extra interview. A digest records a source the project read; a card records a
claim the project made.

Read the complete existing cards and source references before proposing one.
Missing/unresolvable source, low unverified evidence, duplicate source/claim or
no durable tripwire means no proposal. Ask nothing in that case. A date alone is
not a tripwire. Sources and task IDs must resolve to the actual evidence, not a
similar filename or a placeholder. Cite the close/retro/incident evidence exactly.

## The one question

Draft the claim, source, invalidated-by condition, owner and verification date
from evidence. Show the actual draft and ask whether to keep it, correct its
wording or skip. No automatic card creation. A skip writes nothing and is not
raised again for that task; the evidence already records what happened.

## The write

Only after the actual user choice, work writes an ordinary Markdown card under
`knowledge/<topic>/<slug>.md` using `work/state/knowledge_card_TEMPLATE.md`.
Require real Claim, Source, Invalidated by, Kind, Last verified and an actual
owner when roles are declared. Check both target and parent collisions, including
symlinks, immediately before writing; refuse an existing target. Preserve other
cards and every unrelated index section. Update only `Cards by topic` in the
knowledge index, without creating a second current task or goal register.

Before committing, open the exact source and card, verify the source supports the
claim, inspect the tripwire and date, and read the retained helper with explicit
project/document roots according to `tools/helper-contracts.md`. Report helper
errors and unresolved sources, never call a read success semantic verification.
A sourceless card or placeholder owner is refused, not written blank. Re-read
concurrently edited index bytes before applying a narrow update. Card creation
is a skill document write, not a kernel mutation or hidden compatibility CLI.

For source digests use `digests.md`; for incident capture use
`packs/software-ops/incidents.md`.
