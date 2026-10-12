# Code architecture browser

`perry architecture` computes a Python import graph from source. It needs no
Perry adoption or project state. The CLI, analyzer and offline browser have no
third-party dependencies. Python 3.11+; use a modern browser for the HTML.

## Run

The software-ops workflow is documented in
[architecture-analysis.md](../../packs/software-ops/architecture-analysis.md).
Use the same scan arguments throughout a run:

```sh
bin/perry-architecture --root /path/to/project --source-roots src --json > /tmp/facts.json
bin/perry-architecture --root /path/to/project --source-roots src --brief --focus 'src/core/*'
# The host agent reads facts/source and generates analysis.json and cited rules.json.
bin/perry-architecture --root /path/to/project --source-roots src \
  --analysis /tmp/analysis.json --rules /tmp/rules.json \
  --html /tmp/project-architecture.html --json > /tmp/report.json
```

For Perry use `--source-roots bin,viewer,kernel,release --exclude perry,tests,kernel/tests`.
There is no model API or automatic semantic classification in the CLI. The host
agent performs that step from evidence during the skill workflow. Generated
analysis is a disposable snapshot output, not a hand-maintained input map.

The output path must be **outside the analyzed project and not already exist**.
Choose a new filename when regenerating. The tool reads project files; it does
not change them, import their modules, run Git, install packages, or call a model.
`--root` defaults to `$PERRY_PROJECT`, then cwd; it never searches ancestors.

Other projects use the same entry point. For a typical Python `src/` project:

```sh
/path/to/Perry/bin/perry-architecture --root /path/to/project \
  --source-roots src --html /tmp/project-code-report.html
```

`--source-roots` adds comma-separated import roots inside the project. The
project root is always included. This is not a scan-path restriction. Scan all
Python files except the named `--exclude` paths/globs and default exclusions.
No `.gitignore` interpretation: the coverage panel lists the actual policy.
No source-root autodetection: configure roots to match the project being read.
Do not add both production and fixture roots unless that reflects the intended
analysis; multiple same-name candidates are reported as ambiguous.

## Architecture hierarchy and source evidence

The primary view with `--analysis` is a responsibility hierarchy: overview,
components, then implementation files. The original directory graph remains a
secondary evidence view. Without a model the report opens that directory view;
it does not claim to infer semantic architecture from imports.

`--analysis` validates exact file/symbol membership, evidence references and the
fact snapshot. Unknown members and overlap are refused; omitted members remain
visible. Source changes require regeneration. The tool validates provenance,
not semantic truth. See the workflow above for the analysis and rules contracts.

`--rules` validates exact target quotes and document hashes before checking the
two supported rule kinds. `--previous` compares file hashes and component IDs.
Renames appear as removals/additions; automatic semantic identity matching and
partial regeneration are not implemented in this first slice.

Legacy `--architecture` and `perry-model.json` remain for opening the earlier
prototype; they are not used by the code-backed analysis workflow.

Click a component for its purpose and implementation list. Click a relation for
actual import statements and source line ranges. Source opens from the scanned
snapshot, not a potentially changed working file. Outside components are hidden
in the diagram by default and can be enabled; their relations remain listed.
Browser Back restores views. Export Mermaid saves the currently visible diagram.
Export JSON gives humans and agents the same model, memberships and evidence.
Neither export establishes that a dependency is architecturally allowed.

JSON schema version 1 contains `files`, `imports`, `edges`, `issues`, `scope`
and `summary`, plus `architecture` when a model is supplied. The latter carries
normalized nodes, ownership, issues, explicit-import edges and a model hash. IDs for files are project-relative POSIX paths; import IDs are
array indices within this snapshot. An edge references the import IDs that
justify it. An import with multiple names yields a record per name. Therefore
import counts count records, not unique statements. The HTML embeds full source
of included files for offline inspection. Treat exports like a copy of the code.

`files[].sha256` hashes original source bytes. `snapshot` identifies source and
scan configuration; these are fingerprints, not Git commit claims. There is no
automatic refresh, background server, or persisted state. A report can contain
concurrent edits if the project changes during its scan. Re-scan a stable tree
when comparing versions. HTML renders source as text, never executable markup.

## What the graph means

- Static `import` and `from … import …` relations, plus symbol declarations and conservative lexical call references. Regular, relative,
  multiline, conditional, and function-local statements are included. They
  prove a declaration, not execution. Unambiguous package initializers are
  included when importing a child.
- The architecture view excludes implicit package initialization edges; these
  remain in the raw file graph. Arrows mean static reference, not runtime flow,
  state writes or control flow. Responsibility labels are explicit model input.
- A directory group in the secondary view is only a presentation of file paths.
- Namespace packages can resolve child modules without an `__init__.py`.
  Namespace-only imports have no executable file target.
- Unresolved imports can be external, missing, excluded or dependent on runtime
  path changes. They are never silently labelled confirmed third-party code.
- Standard library names come from the scanning interpreter. Local file
  candidates take precedence; configured roots are not ordered like `sys.path`.
  Import hooks, Python package shadowing across namespace roots and runtime
  import precedence are not simulated.
- Syntax/encoding/read/size failures and recognized dynamic-loading calls are
  reported. A successful CLI exit means a snapshot was produced, not full
  semantic coverage. Parsing reflects the interpreter's Python grammar.
- Symlink files/directories, nested Git repositories and generated/environment
  directories are skipped. File size limit defaults to 2 MB. Other languages,
  full runtime call graphs and file/database I/O are outside this version.
  Call expressions, literal arguments and literal SURFACE declarations are
  evidence; dynamic dispatch is not simulated. Missing edges do not prove independence.
- Graphs display at most 80 nodes at one level; the dependency list keeps all
  relationships. Search returns the first 100 files with a total count.

## Code boundaries and verification

`scan.py` returns facts; `facts.py` extracts symbols and lexical calls;
`analysis.py` validates host-agent interpretation; `audit.py` checks cited
constraints; `model.py` supports the legacy ownership map;
`report.py` embeds them with `report.html`, `.css` and
`.js`; `bin/perry-architecture` exposes the CLI and Perry's discovery surface.
The module does not depend on the state kernel or project parsers.

```sh
python3 -m unittest tests.test_architecture_browser
bash tests/run
git diff --check
```

Browser acceptance: open overview, enter project tools and kernel responsibilities,
open a component's implementation list, trace a dependency to its original import
line, switch to the raw directory view, and export Mermaid and JSON. Report the
checks actually run. Future language adapters should produce a versioned fact
payload; Perry-specific ownership stays in the separate model configuration.


Task start/delivery checkpoints use `--checkpoint start|delivery`, `--task`,
`--store`, `--analysis`, and snapshot-bound `--review`. Start requires `--rules`;
delivery requires `--baseline` and refuses replacement rules. The durable store
must be outside the analyzed checkout. `--verify-checkpoint` checks current
source/target freshness and baseline integrity. See
`packs/software-ops/architecture-analysis.md § Task checkpoints` for the host
workflow, JSON review contract and quiet/attention behavior. No browser/model
or scheduled job runs inside this command; no task state is changed.
