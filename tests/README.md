# Native and helper acceptance suite

`bash tests/run` runs the complete **new** source suite: the entire native
`kernel/tests/run.py` suite and every `tests/test_*.py` helper test. The kernel
runner retains its live-store detection and explicit-store prevention.
`bash tests/run --slow` (or `--tier slow`) adds real local Git integration
self-tests. Both tiers reject source changes, nonzero stages and empty suites.
No dependencies, network services or project activation are needed.

This is not a passing result for the removed legacy full/slow corpus. The
immutable-base inventory is [test-disposition.json](test-disposition.json).
Each source path has its original SHA and proposed disposition. These preserve historical source-retirement proposals; actual user approval and final V5 are separate dated cutover records. Safety checks now
combine native structural guards, explicit skill procedures and the red
fixtures in `test_document_checks.py`. A lexical document check cannot decide
whether evidence is true or whether a human actually approved an operation.

Retained behavior includes architecture scanning, unknown/dynamic-call limits,
snapshot-bound analysis, checkpoint tamper/freshness checks, session telemetry,
local release allocation and publication refusal, consumer release update
safety, and knowledge/role/churn helper output. Architecture's prose byte pin
and retired model fixture assertion, plus telemetry's retired schema-presence
assertion, are removed explicitly in the disposition artifact. Native resolver
agreement with deleted `bin/lib` is replaced with direct temporary-anchor
invariants. The native wrapper fixture now invokes `bin/perry`; the executable
banners follow its `perry` basename. Direct in-process CLI tests retain the
kernel's unchanged default `perry-kernel` program name.

The work-template suite keeps decision 13's exact task/ask/risk declarations
and drives their complete transition/guard matrix. Full-template syntax,
type counts and stored version use the shipped data. An expanded temporary
template reruns all work assertions unchanged; an invalid extra type still
fails validation. Goals/decide additions MUST carry their separate F acceptance
suite. These work tests do not establish those lanes' process semantics.

## Independent integration

Commit reviewed source, then an independent integrator runs, for example:

```sh
python3 tests/merge-check --base <immutable-main-SHA> \
  --candidate <immutable-candidate-SHA> --tier full --record /external/new/full
python3 tests/merge-check --verify-receipt /external/new/full/receipt.json
python3 tests/merge-check --base <immutable-main-SHA> \
  --candidate <immutable-candidate-SHA> --tier slow --record /external/new/slow
```

The helper resolves local refs once, clones locally, merges in the clone and
runs its `tests/run`. The caller checkout, its WIP, live state and refs remain
untouched. Conflicts, any red stage, a zero-exit source write and refs moving
during tests refuse a receipt. Verification checks receipt/transcript hashes,
unchanged input refs and a reconstructed exact merged tree. It does not rerun
tests. Receipts are unsigned local evidence; independent review and named
human sign-off remain separate. Use immutable SHAs for durable receipts.

There is no PR discovery, pairwise blame search, timing artifact import or
legacy `--checks`/`--all-open` mode. CI supplies fetched candidate/base commits
explicitly. Release allocation and `release/manage.py check --base ... --ref ...`
remain separate mandatory integration gates under `release/README.md`.

Real red self-tests cover planted failing suites, silent source mutation,
merge conflict, moved refs, modified receipts and modified transcripts. The
source guard excludes `.git` and Python bytecode; it observes files and modes
inside the tested checkout, not arbitrary writes elsewhere. The native suite's
store safety is a separate guard. Static import checks cannot prove behavior
of dynamic imports or arbitrary shell code; these stay visible review limits.
