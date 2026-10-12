# Code architecture browser

`perry architecture` computes a Python import graph from source. It needs no
Perry adoption or project state. The CLI, analyzer and offline browser have no
third-party dependencies. Python 3.11+; use a modern browser for the HTML.

## Run

From Perry's checkout, analyze Perry's product code:

```sh
bin/perry-architecture --root . \
  --source-roots bin,viewer,kernel,release \
  --exclude perry,tests,kernel/tests \
  --architecture bin/perry_architecture/perry-model.json \
  --html /tmp/perry-code-report.html
```

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

The primary view with `--architecture` is a responsibility hierarchy: overview,
components, then implementation files. The original directory graph remains a
secondary evidence view. Without a model the report opens that directory view;
it does not claim to infer semantic architecture from imports.

`perry-model.json` is an agent-authored starting model based on Perry's existing
architecture documents and source, pending human review. Its labels, boundaries
and layers are design judgments. File membership and inter-component import
relations are computed from the scanned code. The model never declares arrows.
Unassigned files, overlapping ownership and empty components appear in coverage;
new code cannot silently disappear behind a stale classification.

A model for another project is ordinary editable JSON:

```json
{
  "version": 1,
  "title": "Project architecture",
  "basis": "Reviewed responsibility boundaries",
  "components": [
    {"id": "application", "label": "Application", "layer": 0,
     "children": [
       {"id": "commands", "label": "Commands", "description": "Accept requests",
        "layer": 0, "paths": ["src/commands/*.py"]}
     ]},
    {"id": "storage", "label": "Storage", "layer": 1,
     "paths": ["src/storage/*.py"]}
  ]
}
```

Leaves use project-relative, case-sensitive `fnmatch` patterns (`*` can span
slashes); branches have children instead of paths. IDs are lowercase slugs,
unique under their parent. `layer` is 0–10 and determines vertical placement.
Names, descriptions and layers need review; they are not AST discoveries.

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

- Only static `import` and `from … import …` relations. Regular, relative,
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
  call graphs, subprocess relations, file/database I/O and architecture rules
  are outside this version. Missing edges do not prove independence.
- Graphs display at most 80 nodes at one level; the dependency list keeps all
  relationships. Search returns the first 100 files with a total count.

## Code boundaries and verification

`scan.py` returns facts; `model.py` binds optional responsibility ownership;
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
