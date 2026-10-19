# Goal attribution — shared goals/work rule

Resolve by exact identity, otherwise ask. Never match a task/Project to a KR by
similar wording. A legacy label alone is insufficient when versions repeat it.

Resolution order: native contributes_to relation or migrated KR work_items;
then exact phase-scoped Project ID in project_registry; then confirmed exact
alias. Zero or multiple candidates means a visible unresolved question, excluded
from progress, with candidate IDs and human titles. A declared no-KR answer is
resolved-unlinked; never-asked work remains unresolved. Never fabricate a mapping.

Goals owns attribution and Project/alias declarations; work proposes changes and
creates approved tasks. Use native kernel rel/item operations with current seqs,
following goals/reference/linkage.md. No legacy linkage/events/journal writer.
The importer disambiguates a repeated overall label only from explicit version,
phase Source version, or typed task design_refs whose design Linked OKR names the
same KR and one version. It refuses ambiguous joins, not guesses by date/title.

Registry declarations retain phase scope and exact IDs/names/aliases. A name
claimed by multiple Projects requires resolution before a new write. New phase
carry-over requires approval. Task completion is not a measured KR value, and
unlinked work never becomes metric progress merely to complete the dashboard.
