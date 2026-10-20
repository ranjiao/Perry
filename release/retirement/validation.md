# H source validation

The new local full suite passed: **281 native tests (1 platform skip)** and
**150 helper/release/source tests**. The same 281 native tests passed in an
isolated Git project containing no Markdown. The skip is APFS rejecting a raw
non-UTF-8 directory name; surrogate CLI input is still tested. Seven synthetic
integration harness self-tests also passed. These are source results, not the
retired corpus, independent combined-tree acceptance or user sign-off.

Real reds include missing-store prevention, evidence/human guards, forbidden
architecture calls, stale/tampered checkpoint evidence, source/mode/symlink
mutation, merge conflicts, moved refs, modified receipts/transcripts, broken
knowledge provenance, ownership violations, unarmed escalation and self-review.
The method-as-data test adds an enum field plus prose in a temporary fixture,
creates/reads it through the same native CLI and checks unchanged kernel hashes.
Kernel lifecycle/worktree/export/replay tests retain their behavioral assertions.

Two initial failures were corrected transparently: old wrapper-name assertions,
and missing anchor metadata in the first Markdown-free test fixture. The final
full and Markdown-free runs passed. Exact commands, log hashes and scope are
[validation.json](validation.json).

The real pre-edit architecture checkpoint is durable outside the executor tree.
Final delivery is fresh but **attention**, with target_changed,
incomplete_coverage and target_change_requested. Static facts are not semantic
approval. The local report browser was unavailable; the saved report is linked
through validation.json, with no claim of rendered-browser review.

No product version was allocated. Release allocation/checks and actual merged
full/slow receipts belong to the independent integrator. F/G-owned source and
external projects were deliberately not edited. Their combination, aiMark adapter
coverage, store/export/backup/rollback receipts and actual user H/V5 decision are
still required. The [420 drops](dropped-checks.tsv) remain proposals.
