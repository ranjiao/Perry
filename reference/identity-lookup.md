# Source identities and domain-role lookup

This is an Agent procedure using existing native query/items and explicit
declarations. It adds no alias index, role field, uniqueness guard or parser.
Follow [startup and capture](snapshot.md), [artifact rules](project-contract.md)
and the relevant owning lane before reading or changing project state.

## Preserve identity without a second registry

Match an original identifier together with its declared source scope: project,
tracker/list or document namespace, and version when the source reuses labels.
A matching number or similar title alone is not identity. Preserve already-issued
identifiers; do not renumber the source or fabricate native IDs.

For a task adopted into native ownership, preserve the confirmed scoped source
identity in the existing task `summary`, alongside its readable deliverable.
The attached spec cites that native item and original source instead of keeping
another editable mapping. Existing typed migration identities on other item
types retain their declared meaning. Do not invent task fields to match them.
An adoption dossier's dated mapping is a receipt of a particular run, not a live
identity registry. Changing a confirmed mapping requires actual reconciliation.

Record a domain-role association explicitly in the task's owned spec with the
role card's actual anchor/path, or cite an authoritative project role declaration.
Do not infer it from a directory, event actor, executor or generic native `owner`.
When the optional owner enum cannot describe the domain role truthfully, leave
it unknown rather than assigning a misleading enum value.

## Answer a lookup

1. Establish the requested identifier/scope or role and the finite relevant native
   population. Use only actual filters supported by `describe` and the template.
2. Follow all pages with unchanged filters and one consistent `store_seq`, using
   [snapshot](snapshot.md). Report excluded types/sources or read failures.
3. Inspect explicit source identities and, for roles, the cited specs/declarations
   and role cards. Open refs through the agreed roots. Respect read permissions.
4. Return native ID/title, exact matched source identity or role declaration,
   native task state, capture seq, evidence and any unresolved associations.
   Preserve unknown, absent and ambiguous as different outcomes. Never choose
   between different scopes merely because a title or timestamp looks newer.
5. A partial scan cannot prove uniqueness or absence. State its bounds. If the
   user needs a mutation, resolve ambiguity and re-read the target seq first.

There is no native `source_id` or domain-`role` filter in the current task
template. Report the skill-side join and its cost honestly. A generated lookup
answer is a dated projection, not a file to dual-write on later transitions.

## Adoption and resume

Use one authorized adoption writer for the confirmed candidate set. Before any
create, re-query that affected set and compare actual scoped identities, receipts
and mappings. After a partial failure, read the actual committed results; do not
repeat the whole batch. Cross-item source uniqueness is not kernel-enforced.
Duplicate/ambiguous identities or concurrent conflicting writers stop creates
until reconciled. An explicit resume choice is still required for an interrupted
dossier; lookup does not supply it.

If this method cannot satisfy a concrete filtering, cost or idempotency need,
record the requested answer, finite population, observed failure/cost,
reproducible example and attempted existing capabilities. Discuss the smallest
extension separately; a limitation itself authorizes no template/kernel change.
