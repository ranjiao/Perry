# Retired checks and their replacements

This page is a procedure, not a semantic lint engine. The finite
[H disposition](../release/retirement/disposition.json) gives every original
check/mode/source path a disposition. Its source index preserves exact old
finding expressions and proposed red scenarios at the immutable source base.
Every row is still a PROPOSAL. A source audit cannot approve a deletion.

## Apply the remaining checks

1. Run [startup safety](operating-rules.md#before-state-reads) before normal state
   reads. A corrupt marker or dossier blocks; an interrupted workflow needs the
   user's choice. Do not recover using a deleted writer or edit the marker away.
2. Read the native template and query the actual items. Unknown fields/types,
   bad IDs, missing relations, broken replay and structural guards are kernel
   responsibilities. Use complete query pagination; do not parse old boards.
3. Read the actual hook, role and scoped spec. Apply
   [ownership and high-stakes](operating-rules.md#ownership-and-high-stakes-decisions)
   to actual operations, including unresolved roots. Treat code screening as
   facts, not permission. A consequential scope without written criteria stops.
4. Before closing a task, read criteria and evidence. Compare each claimed
   outcome with its actual artifact and verification method. Missing evidence,
   a review without a criterion-bound verdict, implementation self-review or
   absent named human sign-off blocks closure. Kernel guards alone do not prove
   adequacy. [Review](../work/reference/review.md) and
   [task close](../work/reference/task-close.md) own the decision.
5. Read every new knowledge claim's source and invalidation tripwire. Run the
   [knowledge helper](../tools/helper-contracts.md); resolve task citations by
   native item lookup and verify remote source contents separately. Existing
   file paths are not proof of support. Source/claim/tripwire/owner omissions
   require correction before promotion.
6. For source architecture work, preserve actual start and delivery checkpoints,
   cited target rules, analysis limits and independent review. Freshness is not
   permission to change a target. See
   [architecture analysis](../packs/software-ops/architecture-analysis.md).
7. For ordinary documents, inspect the actual document against its purpose.
   Check discoverability, necessary context, sources, named owners, readable
   summaries and explicit uncertain claims. Use the glossary to resolve ambiguous
   terms. A file-size warning or matching heading is not a semantic verdict.
   A summary that merely repeats its title gives the next executor no artifact
   or check; rewrite it with those facts. A glossary link to a missing file or
   an unowned role card must be repaired or explicitly retired.
8. For goals and decision metadata, query stable native IDs and follow the owning
   lane's procedure. Do not repair linkage/phase/decision facts by editing old
   JSONL or guessing an alias. F's import/re-keying proof and G's root queries
   need independent combined testing before H activation.
9. For diagnosis, apply [the read-only procedure](diagnose.md) and cite observed
   files, query facts and user declarations. Separate measured defects from
   judgment and unknowns. No legacy mode classifier, score or threshold is
   silently treated as current fact. Zero findings is a valid result.

## Show red, without claiming acceptance

`tests/test_document_checks.py` and `tests/test_helpers_native.py` plant real
invalid inputs. Native guard/replay/identity and architecture freshness tests do
likewise. The ledger maps these source demonstrations to the retained safety
capabilities. Where an exact old document judgment is no longer mechanical,
record the fixture, the procedure applied, the observed author finding and its
limits. A proposed scenario is not an executed demonstration. Outstanding
row-level demonstrations remain explicit blockers in the H result.

Old table grammar, board rendering, JSONL projection drift, deterministic next
recommendation, mode labels and prose byte pins have candidate dropped rows.
They cannot be approved by a passing source suite. The actual user must inspect
and accept the concrete drop list, including the changed helper API behavior.
Safety capability itself is never a dropped row.
