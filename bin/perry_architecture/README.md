# Code architecture browser, v1

`perry architecture` computes a Python import graph from source. It needs no
Perry adoption or project state. The CLI, analyzer and offline browser have no
third-party dependencies. Python 3.11+; use a modern browser for the HTML.

## Run

From Perry's checkout, analyze Perry's product code:

```sh
bin/perry-architecture --root . \
  --source-roots bin,viewer,kernel,release \
  --exclude perry,tests,kernel/tests \
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

## Acceptance and interface

The approved first slice (USER-1007) is:

1. Project overview: counts and a dependency graph grouped by actual directory.
2. Module drilldown: directory navigation, breadcrumbs, search, and boundary
   neighbours visible when exploring a nested module.
3. Source evidence: each graph edge opens import records with file, original
   statement and line range; each record opens the source snapshot. The line
   input navigates elsewhere in that file. Browser Back restores prior views.
4. Human and agent share the same facts: without `--html`, JSON goes to stdout;
   `--json` also prints it with `--html`. The browser's download exports the same
   payload. No separate model-written architecture document is needed.
5. Perry's extensionless Python commands participate, and scanning never
   executes the target code or writes into the target project.

JSON schema version 1 contains `files`, `imports`, `edges`, `issues`, `scope`
and `summary`. IDs for files are project-relative POSIX paths; import IDs are
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
- A directory group is a presentation of file paths, not an inferred business
  module. Internal edges of a collapsed group appear when it is opened.
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

`scan.py` returns facts; `report.py` embeds them with `report.html`, `.css` and
`.js`; `bin/perry-architecture` exposes the CLI and Perry's discovery surface.
The module does not depend on the state kernel or project parsers.

```sh
python3 -m unittest tests.test_architecture_browser
bash tests/run
git diff --check
```

Browser acceptance: open overview, enter `bin`, select `perry-task → parsers`,
open the evidence at its reported line, search `perry-task`, jump to a line,
use Back, inspect coverage and export JSON. Report the checks actually run.
Future language adapters should produce a versioned fact payload; do not put
Perry-specific directory knowledge into the analyzer.
