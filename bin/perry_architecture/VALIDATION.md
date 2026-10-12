# First-slice validation — 2026-10-12

Source: Perry primary checkout `db06e70c`; snapshot
`ba63e111cba99d5d802b666869b599c5291542eb27830fd690b72ec2251996c4`.
Analysis implementation is on `codex/architecture-browser`, not integrated.

- Real scan: 39 Python files, 1,442 function/class declarations, 16,376 call
  expressions. All source hashes and the cited target document hash were
  checked against the primary checkout after the run; that checkout stayed clean.
- Host-agent interpretation: 27 component nodes, including three responsibilities
  within `commands.py`. Generated from the inspected facts/source, without
  `perry-model.json`; no unassigned units. This proves coverage, not human
  agreement with the inferred responsibilities.
- Two cited kernel checks: no observed forbidden product imports; no recognized
  process-call violation, but 978 unresolved call expressions keep that check
  `unknown`. No whole-architecture compliance claim.
- Temporary copy of all 39 Python files: injected an import of `viewer/parsers.py`
  and a subprocess call; both checks reported violations with source evidence.
  A new file appeared in the diff; old analysis was refused. Removing injected
  changes restored the original snapshot. No injected code was executed.
- Portability smoke: Byteworker's real `lib/` subtree, 91 Python files, seven
  inferred responsibilities, no unassigned units. No target rules supplied.
  This is a library-subtree trial, not full-project architectural acceptance.
- Browser: component/symbol drilldown, commands.py:365 call evidence, target
  quotes, unknown status, injected violations and snapshot changes, Mermaid
  export, and narrow-screen detail closing checked. No console errors observed.
  Tested via localhost; file-protocol opening was not tested.
- `python3 -m unittest tests.test_architecture_browser`: 26 tests passed.
- `bash tests/run`: exit 0, all green; tree guard passed.
- `git diff --check`: passed.

The [software-ops workflow](../../packs/software-ops/architecture-analysis.md)
is the reproducible host-agent procedure. Reports are disposable artifacts;
source changes currently invalidate the complete interpretation, not just a
component cache. Target edits invalidate derived rules. No scheduler, auto-repair,
new model service, target-architecture edits, independent V4 or merge performed.
