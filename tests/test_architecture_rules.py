"""`ARCHITECTURE.md`'s structural rules, run in the full suite. TASK-453.

`DESIGN-017 § 5.2` turns the rules that come from the DECIDED sections of
`ARCHITECTURE.md` into checks that run before every merge to `main`. Each check
here reads typed facts only — paths, executable bits, Python import statements
read with `ast`, line counts, one sha256 — and none of them reads prose for
what it means (NN-4). Headings and `§ 8` entries are read lexically, the way
`test_pointers_resolve.py` reads `§` citations.

| Rule | From | Here |
|---|---|---|
| S1 `viewer/parsers.py` imports nothing from `bin/` | § 3, allowed directions | `TestS1ParsersImportNothingFromBin` |
| S2 one reader per state file | § 6 NN-1 | **not in this module** — USER-936 |
| S3 standard library only | the OKR anti-goal; the phase cost ceiling | `TestS3StandardLibraryOnly` |
| S4 the suite never writes its own tree | § 6 NN-5 | `TestS4TreeGuardOnEveryExitPath` |
| S5 every component is named | § 2's list | `TestS5EveryComponentIsNamed` |
| S6 size caps | the two documents' header caps | `TestS6SizeCaps` |
| S7 decided sections change only with a confirmation | § 6 NN-6 | `TestS7DecidedSectionsMatchTheConfirmedHash` |

**Every checker is a function over an input it is handed** — a source string,
a script's text, a root directory — and returns what it found. The live tests
hand it this repository and assert it found nothing; the synthetic tests hand
it an input they built and assert it found exactly the planted defect. That is
what lets each rule be shown red without touching the tree the suite runs in
(NN-5), and it is why every live expectation is `[]`: a property of whatever
the repository holds, never a count of what it holds today.

## What is not here, and why

- **S2.** NN-1's own `Check:` is a grep for `def parse_` in `bin/`. At base it
  matches 12 functions. USER-936 (2026-09-15): a name match cannot tell a value
  parser from a second reader of a state file, and misses a reader under any
  other name, so S2 does not land until NN-1's check is redone without grep.
  Nothing in this module stands in for it — no skip, no expected failure.
- **S1 on the live file is an expected failure.** USER-935 (2026-09-15) ruled
  the code the violation and `§ 3` correct. TASK-458 moves the shared modules;
  the day it lands, the live case reports an unexpected success and its
  decorator comes off.
- **Dynamic reach.** `importlib.import_module("lib")`, `__import__`, or a
  subprocess running a `bin/` tool is not an import statement, and S1 and S3
  do not see it.
- **The tier budgets of `DESIGN-017 § 5.4`** are TASK-456; S6 here is the two
  document caps. The `§ 8` hash format is TASK-454; S7 declares the text it
  hashes (`decided_text`) so TASK-454 has one definition to write down or to
  change in one place.

Run: python3 tests/parallel test_architecture_rules
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: Directories no rule walks into or counts: git's store and what tools on this
#: machine write beside the repository's content. `tests/tree_guard.py §
#: IGNORE_DIRS` is the same set for the same reason, plus `.trae`, which
#: `.gitignore` also ignores.
UNWALKED = frozenset({".git", "__pycache__", ".claude", ".gstack", ".trae"})


def repo_relative(root: pathlib.Path, path: pathlib.Path) -> str:
    return path.relative_to(root).as_posix()


def parse_source(source: str, filename: str) -> ast.AST:
    """`ast.parse`, without the compiler's warnings about the source it reads.

    An invalid escape in someone else's docstring is that file's business; it
    printed a dozen `DeprecationWarning` lines into this module's output when
    S3 read the whole tree.
    """
    import warnings                                           # noqa: PLC0415
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(source, filename=filename)


# ── the document, read lexically ─────────────────────────────────────────────

SECTION_HEADING = re.compile(r"^## §(\d+)\.")


def sections(text: str) -> dict[int, list[str]]:
    """`## §N.` → the lines under it, up to the next `## ` heading.

    A line inside a fenced block is never a heading, so a `## ` in a code
    sample cannot end a section early.
    """
    out: dict[int, list[str]] = {}
    current = None
    fenced = False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if not fenced:
            m = SECTION_HEADING.match(line)
            if m:
                current = int(m.group(1))
                out[current] = []
                continue
            if line.startswith("## "):
                current = None
                continue
        if current is not None:
            out[current].append(line)
    return out


# ── S1 ───────────────────────────────────────────────────────────────────────

S1_EXPECTED_FAILURE = (
    "Expected failure by decision: USER-935 (2026-09-15) ruled that the code is "
    "the violation and ARCHITECTURE.md § 3 stays as written. TASK-458 moves the "
    "shared modules out of bin/; when it lands this case reports an unexpected "
    "success and the expectedFailure decorator comes off.")


def bin_module_names(root: pathlib.Path) -> set[str]:
    """The top-level module names an import of something in `bin/` would use.

    `bin/*.py` files and `bin/*/` packages. `bin` itself is included so that
    `from bin import lib` is caught as well as `import lib`. The executables
    have no `.py` suffix and a hyphen in the name, so no import statement can
    name one.
    """
    names = {"bin"}
    for p in (root / "bin").iterdir():
        if p.is_file() and p.suffix == ".py":
            names.add(p.stem)
        elif p.is_dir() and (p / "__init__.py").is_file():
            names.add(p.name)
    return names


def imports_of(source: str, names, filename: str = "<source>") -> list[tuple[int, str]]:
    """`(line, module)` for every absolute import in `source` whose top-level
    module is in `names` — at module scope or inside a function alike."""
    hits = []
    for node in ast.walk(parse_source(source, filename)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in names:
                    hits.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module.split(".")[0] in names:
                hits.append((node.lineno, node.module))
    return sorted(hits)


class TestS1ParsersImportNothingFromBin(unittest.TestCase):
    """S1 — `ARCHITECTURE.md § 3`: "`parsers` imports nothing from `bin/`"."""

    NAMES = frozenset({"lib", "perry_md_store", "perry_store"})

    def test_a_bin_import_is_reported_wherever_it_sits(self):
        source = ("import json\n"
                  "def blank(value):\n"
                  "    import sys\n"
                  "    sys.path.insert(0, 'bin')\n"
                  "    import lib\n"
                  "    return lib.is_blank_cell(value)\n"
                  "from perry_md_store import stored_value\n")
        self.assertEqual([(5, "lib"), (7, "perry_md_store")],
                         imports_of(source, self.NAMES))

    def test_a_source_with_no_bin_import_is_clean(self):
        source = ("import json\n"
                  "from pathlib import Path\n"
                  "from tables import squash\n"
                  "from . import sibling\n")
        self.assertEqual([], imports_of(source, self.NAMES))

    def test_the_bin_names_come_from_bin(self):
        names = bin_module_names(ROOT)
        for name in ("lib", "perry_store", "perry_md_store"):
            self.assertIn(name, names)
        self.assertNotIn("tables", names,
                         "viewer/tables.py is viewer's own module; importing it "
                         "is not an import from bin/")

    @unittest.expectedFailure
    def test_viewer_parsers_imports_nothing_from_bin(self):
        """S1 on the live file — an expected failure: USER-935, TASK-458."""
        path = ROOT / "viewer" / "parsers.py"
        hits = imports_of(path.read_text(encoding="utf-8"),
                          bin_module_names(ROOT), str(path))
        self.assertEqual([], hits,
                         f"viewer/parsers.py imports from bin/ at {hits}. "
                         f"{S1_EXPECTED_FAILURE}")


# ── S3 ───────────────────────────────────────────────────────────────────────

S3_DIRECTORIES = ("bin", "viewer", "tests")

#: Paths under `S3_DIRECTORIES` that S3 does not read, each with its reason.
S3_NOT_SCANNED = {
    "tests/fixtures": (
        "fixture projects and frozen `*.before.py` snapshots of old test "
        "modules: data a test reads with `ast` or copies into a temporary root, "
        "never imported or run from this tree. Two snapshots import `gate`, "
        "which TASK-261 deleted, and are correct as history."),
}

#: Where a bare `import name` resolves inside this repository: the directories
#: this code puts on `sys.path` — the root, `bin/` for the tools and their
#: libraries, and a module's own directory for `viewer/` and `tests/`.
S3_IMPORT_ROOTS = ("", "bin", "viewer", "tests")

S3_SKIP_REASON = (
    "S3 needs sys.stdlib_module_names, which Python 3.10 added; this is Python "
    "{version}, which cannot tell the standard library from a third-party "
    "package, so S3 does not run here rather than pass")


def is_python_source(path: pathlib.Path) -> bool:
    """A `.py` file, or an extensionless file whose shebang names python."""
    if path.suffix == ".py":
        return True
    if path.suffix:
        return False
    try:
        with path.open("rb") as fh:
            first = fh.readline(200)
    except OSError:
        return False
    return first.startswith(b"#!") and b"python" in first


def python_sources(root: pathlib.Path) -> list[pathlib.Path]:
    out = []
    for top in S3_DIRECTORIES:
        for dirpath, dirnames, filenames in os.walk(root / top):
            here = pathlib.Path(dirpath)
            rel = repo_relative(root, here)
            dirnames[:] = sorted(
                d for d in dirnames
                if d not in UNWALKED and f"{rel}/{d}" not in S3_NOT_SCANNED)
            for name in sorted(filenames):
                if is_python_source(here / name):
                    out.append(here / name)
    return out


def repository_module_names(root: pathlib.Path) -> set[str]:
    names = set()
    for rel in S3_IMPORT_ROOTS:
        base = root / rel if rel else root
        for p in base.iterdir():
            if p.is_file() and p.suffix == ".py":
                names.add(p.stem)
            elif (p.is_dir() and p.name not in UNWALKED
                  and (p / "__init__.py").is_file()):
                names.add(p.name)
    return names


def foreign_imports(source: str, allowed, filename: str = "<source>") -> list[tuple[int, str]]:
    """`(line, module)` for every absolute import whose top-level name is not
    in `allowed`. A relative import resolves inside its package by definition."""
    hits = []
    for node in ast.walk(parse_source(source, filename)):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules = [node.module]
        else:
            continue
        for module in modules:
            if module.split(".")[0] not in allowed:
                hits.append((node.lineno, module))
    return sorted(hits)


class TestS3StandardLibraryOnly(unittest.TestCase):
    """S3 — every import in `bin/`, `viewer/` and `tests/` is in the standard
    library or resolves inside the repository."""

    def test_a_third_party_import_is_reported(self):
        source = ("import json\n"
                  "import yaml\n"
                  "from requests.adapters import HTTPAdapter\n")
        self.assertEqual([(2, "yaml"), (3, "requests.adapters")],
                         foreign_imports(source, {"json"}))

    def test_standard_repository_and_relative_imports_are_clean(self):
        source = ("import json, os.path\n"
                  "import lib\n"
                  "from tables import squash\n"
                  "from . import sibling\n"
                  "from .helpers import fixture\n")
        self.assertEqual([], foreign_imports(source,
                                             {"json", "os", "lib", "tables"}))

    def test_the_scan_reads_extensionless_python_and_skips_what_it_declares(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for d in ("bin", "viewer", "tests/fixtures"):
                (root / d).mkdir(parents=True)
            (root / "bin" / "perry-py").write_text(
                "#!/usr/bin/env python3\nimport yaml\n")
            (root / "bin" / "perry-sh").write_text(
                "#!/usr/bin/env bash\necho import yaml\n")
            (root / "viewer" / "reader.py").write_text("import json\n")
            (root / "tests" / "fixtures" / "old.before.py").write_text(
                "import gate\n")
            found = [repo_relative(root, p) for p in python_sources(root)]
        self.assertEqual(["bin/perry-py", "viewer/reader.py"], found)

    def test_every_declared_exclusion_exists(self):
        for rel in S3_NOT_SCANNED:
            self.assertTrue((ROOT / rel).is_dir(),
                            f"S3_NOT_SCANNED names {rel}, which is not a "
                            f"directory — drop the entry")

    def test_every_import_is_standard_library_or_in_the_repository(self):
        if not hasattr(sys, "stdlib_module_names"):
            self.skipTest(S3_SKIP_REASON.format(
                version=sys.version.split()[0]))
        allowed = set(sys.stdlib_module_names) | repository_module_names(ROOT)
        hits = []
        for path in python_sources(ROOT):
            rel = repo_relative(ROOT, path)
            for line, module in foreign_imports(
                    path.read_text(encoding="utf-8"), allowed, rel):
                hits.append(f"{rel}:{line} imports {module}")
        self.assertEqual([], hits,
                         "an import is neither in the standard library nor in "
                         "this repository; Perry ships stdlib-only Python")


# ── S4 ───────────────────────────────────────────────────────────────────────

S4_SNAPSHOT = "tests/tree_guard.py snapshot"
S4_VERIFY = "tests/tree_guard.py verify"
#: What running a step looks like in `tests/run`: any python invocation.
S4_RUNS_A_STEP = re.compile(r"\bpython3?\b")
TRAP = re.compile(r"^\s*trap\s+(\S+)\s+EXIT\s*$")
FUNCTION_OPEN = re.compile(r"^(?:function\s+)?(\w+)\s*\(\)\s*\{\s*$")


def is_code(line: str) -> bool:
    return bool(line.strip()) and not line.lstrip().startswith("#")


def shell_functions(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Function name → (first body index, closing-brace index), for functions
    opened at column 0 and closed by a `}` alone at column 0."""
    out = {}
    i = 0
    while i < len(lines):
        m = FUNCTION_OPEN.match(lines[i])
        if m:
            for j in range(i + 1, len(lines)):
                if re.match(r"^\}\s*$", lines[j]):
                    out[m.group(1)] = (i + 1, j)
                    i = j
                    break
        i += 1
    return out


def tree_guard_gaps(text: str) -> list[str]:
    """How `tests/run` could exit after running a step without the tree guard
    verifying. Lexical: comment lines are ignored, and a function body is not
    a step until something calls it."""
    lines = text.splitlines()
    functions = shell_functions(lines)
    in_function = {k for start, end in functions.values()
                   for k in range(start - 1, end + 1)}
    top = [(i, line) for i, line in enumerate(lines)
           if is_code(line) and i not in in_function]

    snapshot = next((i for i, line in top if S4_SNAPSHOT in line), None)
    if snapshot is None:
        return [f"no line runs `{S4_SNAPSHOT}`"]
    gaps = []
    for i, line in top:
        if i < snapshot and S4_RUNS_A_STEP.search(line):
            gaps.append(f"line {i + 1} runs a step before the snapshot: "
                        f"{line.strip()}")

    traps = [(i, TRAP.match(line).group(1)) for i, line in top
             if TRAP.match(line)]
    after = [(i, handler) for i, handler in traps if i > snapshot]
    if not after:
        gaps.append("no `trap <function> EXIT` follows the snapshot")
        return gaps
    trap_at, handler = after[0]
    for i, line in top:
        if snapshot < i < trap_at and (S4_RUNS_A_STEP.search(line)
                                       or re.search(r"\b(exit|exec)\b", line)):
            gaps.append(f"line {i + 1} can run a step or exit between the "
                        f"snapshot and the trap: {line.strip()}")
    for i, other in after[1:]:
        gaps.append(f"line {i + 1} replaces the EXIT trap with `{other}`")
    for i, line in top:
        if i > trap_at and re.match(r"^\s*exec\b", line):
            gaps.append(f"line {i + 1} `exec`s, which skips the EXIT trap")

    if handler not in functions:
        gaps.append(f"the EXIT trap names `{handler}`, which is not a function "
                    f"defined in this script")
    else:
        start, end = functions[handler]
        if not any(S4_VERIFY in line for line in lines[start:end]
                   if is_code(line)):
            gaps.append(f"`{handler}`, the EXIT trap, never runs `{S4_VERIFY}`")
    return gaps


GUARDED_SCRIPT = """#!/usr/bin/env bash
set -e
# a refusal before anything has run costs the guard nothing
[ -n "${REFUSE:-}" ] && exit 2
python3 tests/tree_guard.py snapshot "$ROOT" "$MANIFEST"
finish() {
  if python3 tests/tree_guard.py verify "$ROOT" "$MANIFEST"; then
    echo ok
  fi
  exit 0
}
trap finish EXIT
python3 tests/parallel
[ "${1:-}" = "--lint" ] && exit 0
exit 0
"""


class TestS4TreeGuardOnEveryExitPath(unittest.TestCase):
    """S4 — `ARCHITECTURE.md § 6 NN-5`: `tests/tree_guard.py` runs on every
    exit path of `tests/run`."""

    def test_a_guarded_script_has_no_gap(self):
        self.assertEqual([], tree_guard_gaps(GUARDED_SCRIPT))

    def test_a_trap_that_never_verifies_is_a_gap(self):
        script = GUARDED_SCRIPT.replace(
            'python3 tests/tree_guard.py verify "$ROOT" "$MANIFEST"', "true")
        gaps = tree_guard_gaps(script)
        self.assertEqual(1, len(gaps), gaps)
        self.assertIn("never runs", gaps[0])

    def test_a_step_before_the_trap_is_a_gap(self):
        script = GUARDED_SCRIPT.replace(
            "trap finish EXIT\npython3 tests/parallel\n",
            "python3 tests/parallel\ntrap finish EXIT\n")
        gaps = tree_guard_gaps(script)
        self.assertEqual(1, len(gaps), gaps)
        self.assertIn("between the snapshot and the trap", gaps[0])

    def test_a_replaced_trap_is_a_gap(self):
        script = GUARDED_SCRIPT.replace("python3 tests/parallel\n",
                                        "trap - EXIT\npython3 tests/parallel\n")
        gaps = tree_guard_gaps(script)
        self.assertEqual(1, len(gaps), gaps)
        self.assertIn("replaces the EXIT trap", gaps[0])

    def test_no_trap_is_a_gap(self):
        gaps = tree_guard_gaps(GUARDED_SCRIPT.replace("trap finish EXIT\n", ""))
        self.assertEqual(1, len(gaps), gaps)
        self.assertIn("no `trap <function> EXIT`", gaps[0])

    def test_tests_run_verifies_the_tree_on_every_exit_path(self):
        text = (ROOT / "tests" / "run").read_text(encoding="utf-8")
        self.assertEqual([], tree_guard_gaps(text))


# ── S5 ───────────────────────────────────────────────────────────────────────

#: Top-level directories that are not components, each with its reason.
S5_EXEMPT_DIRECTORIES = {
    ".git": "git's own store",
    ".claude": "agent worktrees and host settings on this machine; "
               "`.gitignore` ignores `.claude/worktrees/`",
    ".gstack": "a host tool's local state, ignored by `.gitignore`",
    ".trae": "a host tool's local state, ignored by `.gitignore`",
    "__pycache__": "bytecode",
    ".github": "the hosting service's CI workflow configuration; it runs the "
               "suite and is not a part of Perry",
    ".vscode": "one editor's workspace settings",
    "state": "the diagnosis and adoption report templates. Unnamed in § 2 as "
             "of 2026-09-15 and possibly an omission rather than an exemption: "
             "§ 2's list is the user's (DESIGN-017 decision 3), so this entry "
             "stands until the user names the directory there or confirms the "
             "exemption. TASK-453's result raises the question",
}

#: `bin/` executables that are neither in `bin/perry list` nor in a § 2 heading.
S5_EXEMPT_EXECUTABLES = {
    "perry": "the index itself: `perry list` enumerates the tools it indexes, "
             "not itself",
}


def named_in_section_2(text: str) -> tuple[set[str], set[str]]:
    """What the `### ` headings of § 2 name, as (top-level directories, tokens).

    A backticked token with a `/` names the directory before its first slash:
    `bin/` names `bin`, `viewer/parsers.py` names `viewer`, `.perry/` names
    `.perry`. Every backticked token is returned as well, so a heading that
    names `bin/<tool>` names that tool.
    """
    directories, tokens = set(), set()
    for line in sections(text).get(2, []):
        if not line.startswith("### "):
            continue
        for token in re.findall(r"`([^`]+)`", line):
            token = token.strip()
            tokens.add(token)
            if "/" in token:
                directories.add(token.split("/")[0])
    return directories, tokens


def top_level_directories(root: pathlib.Path) -> list[str]:
    return sorted(p.name for p in root.iterdir() if p.is_dir())


def bin_executables(root: pathlib.Path) -> list[str]:
    return sorted(p.name for p in (root / "bin").iterdir()
                  if p.is_file() and os.access(p, os.X_OK))


def perry_list_names(root: pathlib.Path) -> set[str]:
    """Every tool `bin/perry list --json` names, declared or not."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("PERRY_PROJECT", "PERRY_HOME")}
    proc = subprocess.run(
        [sys.executable, str(root / "bin" / "perry"), "list", "--json"],
        cwd=root, env=env, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise AssertionError(f"bin/perry list --json exited "
                             f"{proc.returncode}: {proc.stderr[-800:]}")
    payload = json.loads(proc.stdout)
    return ({tool["tool"] for tool in payload["tools"]}
            | set(payload["undeclared"]))


def unnamed_components(root: pathlib.Path, text: str, listed) -> list[str]:
    directories, tokens = named_in_section_2(text)
    out = []
    for d in top_level_directories(root):
        if d not in directories and d not in S5_EXEMPT_DIRECTORIES:
            out.append(f"top-level directory `{d}/` is in no § 2 heading and "
                       f"is not exempt")
    for tool in bin_executables(root):
        if (tool not in listed and f"bin/{tool}" not in tokens
                and tool not in S5_EXEMPT_EXECUTABLES):
            out.append(f"`bin/{tool}` is in no § 2 heading, not in "
                       f"`bin/perry list`, and not exempt")
    return out


class TestS5EveryComponentIsNamed(unittest.TestCase):
    """S5 — each top-level directory and each `bin/` executable appears in a
    § 2 heading or in `bin/perry list`, or is exempt here with a reason."""

    DOCUMENT = ("# Architecture\n\n"
                "## §1. Mission & scope\n\nx\n\n"
                "## §2. Components\n\n"
                "### `bin/` — the tools\n- x\n\n"
                "### `viewer/parsers.py` — the one reader\n- x\n\n"
                "Prose naming `stray/` is not a heading.\n\n"
                "## §3. Boundaries & dependencies\n\n"
                "### `later/` — a heading in another section\n")

    def test_an_unnamed_directory_and_an_unlisted_tool_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for d in ("bin", "viewer", "stray", "later", "state", ".git"):
                (root / d).mkdir()
            for tool in ("perry-listed", "perry-unlisted", "perry"):
                path = root / "bin" / tool
                path.write_text("#!/usr/bin/env python3\n")
                path.chmod(0o755)
            (root / "bin" / "helper.py").write_text("")
            found = unnamed_components(root, self.DOCUMENT, {"perry-listed"})
        self.assertEqual(
            ["top-level directory `later/` is in no § 2 heading and is not "
             "exempt",
             "top-level directory `stray/` is in no § 2 heading and is not "
             "exempt",
             "`bin/perry-unlisted` is in no § 2 heading, not in "
             "`bin/perry list`, and not exempt"], found)

    def test_a_heading_names_the_directory_before_the_first_slash(self):
        directories, tokens = named_in_section_2(self.DOCUMENT)
        self.assertEqual({"bin", "viewer"}, directories)
        self.assertIn("viewer/parsers.py", tokens)

    def test_no_exemption_is_for_a_directory_section_2_already_names(self):
        text = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
        directories, _tokens = named_in_section_2(text)
        for d in S5_EXEMPT_DIRECTORIES:
            self.assertNotIn(d, directories,
                             f"§ 2 names `{d}/`; its exemption is dead — "
                             f"remove it")

    def test_every_component_is_named(self):
        text = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
        self.assertEqual([], unnamed_components(ROOT, text,
                                                perry_list_names(ROOT)))


# ── S6 ───────────────────────────────────────────────────────────────────────

#: `ARCHITECTURE.md`'s header: "Hard cap: ≤ 500 lines".
ROOT_DOCUMENT_CAP = 500
#: `bin/ARCHITECTURE.md`'s header: "Cap: ≤ 600 lines" — the module-document cap.
MODULE_DOCUMENT_CAP = 600
#: Fixture projects are a user's project in miniature, not this repository's
#: documents.
S6_NOT_WALKED = frozenset({"tests/fixtures"})


def line_count(path: pathlib.Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def module_documents(root: pathlib.Path) -> list[pathlib.Path]:
    """Every `<component>/ARCHITECTURE.md` below the root."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        here = pathlib.Path(dirpath)
        rel = "" if here == root else repo_relative(root, here)
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in UNWALKED
            and (f"{rel}/{d}" if rel else d) not in S6_NOT_WALKED)
        if here != root and "ARCHITECTURE.md" in filenames:
            out.append(here / "ARCHITECTURE.md")
    return out


def size_violations(root: pathlib.Path) -> list[str]:
    out = []
    document = root / "ARCHITECTURE.md"
    if not document.is_file():
        return ["ARCHITECTURE.md does not exist at the repository root"]
    n = line_count(document)
    if n > ROOT_DOCUMENT_CAP:
        out.append(f"ARCHITECTURE.md is {n} lines; the cap is "
                   f"{ROOT_DOCUMENT_CAP}. Overflow splits per § into "
                   f"architecture/sections/")
    for path in module_documents(root):
        n = line_count(path)
        if n > MODULE_DOCUMENT_CAP:
            out.append(f"{repo_relative(root, path)} is {n} lines; the "
                       f"module-document cap is {MODULE_DOCUMENT_CAP}")
    return out


class TestS6SizeCaps(unittest.TestCase):
    """S6 — the root document ≤ 500 lines, each module document ≤ 600."""

    def plant(self, root: pathlib.Path, root_lines: int, module_lines: int):
        (root / "ARCHITECTURE.md").write_text("x\n" * root_lines)
        (root / "bin").mkdir()
        (root / "bin" / "ARCHITECTURE.md").write_text("x\n" * module_lines)
        (root / "tests" / "fixtures" / "p").mkdir(parents=True)
        (root / "tests" / "fixtures" / "p" / "ARCHITECTURE.md").write_text(
            "x\n" * 900)

    def test_documents_at_their_caps_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.plant(root, ROOT_DOCUMENT_CAP, MODULE_DOCUMENT_CAP)
            self.assertEqual([], size_violations(root))

    def test_one_line_over_either_cap_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.plant(root, ROOT_DOCUMENT_CAP + 1, MODULE_DOCUMENT_CAP + 1)
            found = size_violations(root)
        self.assertEqual(2, len(found), found)
        self.assertTrue(found[0].startswith("ARCHITECTURE.md is 501 lines"))
        self.assertTrue(found[1].startswith("bin/ARCHITECTURE.md is 601 lines"))

    def test_the_module_document_is_found(self):
        found = [repo_relative(ROOT, p) for p in module_documents(ROOT)]
        self.assertIn("bin/ARCHITECTURE.md", found)

    def test_every_architecture_document_is_within_its_cap(self):
        self.assertEqual([], size_violations(ROOT))


# ── S7 ───────────────────────────────────────────────────────────────────────

S7_SKIP_REASON = "no confirmed hash recorded; TASK-454 records the first"
HASH_TOKEN = re.compile(r"\bhash:\s*(?:sha256:)?([0-9a-f]{64})\b")
ENTRY_DATE = re.compile(r"^- (\d{4}-\d{2}-\d{2})\b")


def forbidden_lines(section_3: list[str]) -> list[str]:
    """The bullet lines under § 3's `Forbidden` paragraph, with their indented
    continuations, up to the first blank line after them."""
    out: list[str] = []
    inside = False
    for line in section_3:
        if not inside:
            inside = line.startswith("Forbidden")
            continue
        if not line.strip():
            if out:
                break
            continue
        if line.startswith("- ") or (out and line.startswith("  ")):
            out.append(line)
        else:
            break
    return out


def _block(lines: list[str]) -> str:
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return "\n".join(lines)


def decided_text(text: str) -> str:
    """The text S7 hashes: § 1's body, § 3's `Forbidden` lines, § 6's body.

    Each part is its lines as written, outer blank lines dropped, under a fixed
    label. This is the one definition; TASK-454's `§ 8` format records the
    sha256 of exactly this string.
    """
    parts = sections(text)
    return ("## §1\n" + _block(parts.get(1, [])) + "\n"
            + "## §3 Forbidden\n" + "\n".join(forbidden_lines(parts.get(3, [])))
            + "\n" + "## §6\n" + _block(parts.get(6, [])) + "\n")


def decided_hash(text: str) -> str:
    return hashlib.sha256(decided_text(text).encode("utf-8")).hexdigest()


def change_log_entries(text: str) -> list[str]:
    """§ 8's entries in document order: a `- ` bullet at column 0 and its
    indented continuation lines."""
    entries: list[list[str]] = []
    for line in sections(text).get(8, []):
        if line.startswith("- "):
            entries.append([line])
        elif entries and line.startswith("  "):
            entries[-1].append(line)
    return ["\n".join(entry) for entry in entries]


def confirmation_verdict(text: str) -> tuple[str, list[str]]:
    """`("skip", [reason])` while no User-confirmed entry carries a hash;
    otherwise `("checked", violations)`.

    The newest User-confirmed entry is the one with the latest leading date,
    and among entries of one date the first in the document, because § 8 is
    written newest first. Once any confirmation has carried a hash, the newest
    one must carry one too.
    """
    confirmed = [(i, entry) for i, entry in enumerate(change_log_entries(text))
                 if "User-confirmed" in entry]
    if not any(HASH_TOKEN.search(entry) for _i, entry in confirmed):
        return "skip", [S7_SKIP_REASON]

    def key(item):
        i, entry = item
        m = ENTRY_DATE.match(entry)
        return (m.group(1) if m else "", -i)

    _i, newest = max(confirmed, key=key)
    first_line = newest.splitlines()[0]
    m = HASH_TOKEN.search(newest)
    if m is None:
        return "checked", [f"the newest User-confirmed § 8 entry records no "
                           f"hash: {first_line}"]
    actual = decided_hash(text)
    if m.group(1) != actual:
        return "checked", [
            f"a decided section changed without a confirmation — ask the "
            f"user, then record the confirmation in § 8. The newest "
            f"User-confirmed entry ({first_line}) records {m.group(1)}; § 1, "
            f"§ 3's Forbidden lines and § 6 hash to {actual}"]
    return "checked", []


SAMPLE = """# Architecture

## §1. Mission & scope

Perry keeps goals, work and decisions as files.

## §2. Components

### `bin/`

## §3. Boundaries & dependencies

Allowed directions: lanes → tools.

Forbidden, and each one has cost something:
- **A second reader of any state file.** `bin/` never re-implements a
  parse.
- **A lane computing a number.**

A described line after the list.

## §6. Non-negotiables

### NN-1 — One reader per state file
- **Rule**: one parser.

## §7. Open questions

## §8. Change log

{entries}
"""


def sample(entries: str = "", edit=None) -> str:
    text = SAMPLE.replace("{entries}", entries)
    return edit(text) if edit else text


class TestS7DecidedSectionsMatchTheConfirmedHash(unittest.TestCase):
    """S7 — `ARCHITECTURE.md § 6 NN-6`: the hash of § 1, § 3's `Forbidden`
    lines and § 6 equals the one the newest User-confirmed § 8 entry records."""

    def confirmed(self, digest: str, date: str = "2026-09-16") -> str:
        return (f"- {date} · v1 · **User-confirmed** (NN-6) · "
                f"hash: sha256:{digest}\n  - what changed\n")

    def test_no_recorded_hash_skips_with_its_reason(self):
        text = sample("- 2026-09-15 · v1 · **User-confirmed** (NN-6)\n")
        self.assertEqual(("skip", [S7_SKIP_REASON]), confirmation_verdict(text))

    def test_a_matching_hash_passes(self):
        digest = decided_hash(sample())
        self.assertEqual(("checked", []),
                         confirmation_verdict(sample(self.confirmed(digest))))

    def test_an_edit_to_section_6_after_the_confirmation_is_red(self):
        digest = decided_hash(sample())
        text = sample(self.confirmed(digest),
                      lambda t: t.replace("one parser.", "two parsers."))
        verdict, found = confirmation_verdict(text)
        self.assertEqual("checked", verdict)
        self.assertEqual(1, len(found), found)
        self.assertIn("a decided section changed without a confirmation",
                      found[0])

    def test_an_edit_to_a_forbidden_line_or_section_1_is_red(self):
        digest = decided_hash(sample())
        for edit in (lambda t: t.replace("A lane computing", "A lane counting"),
                     lambda t: t.replace("as files.", "as rows.")):
            with self.subTest():
                verdict, found = confirmation_verdict(
                    sample(self.confirmed(digest), edit))
                self.assertEqual(1, len(found), found)

    def test_an_edit_to_a_described_line_is_not_a_decided_change(self):
        digest = decided_hash(sample())
        for edit in (lambda t: t.replace("Allowed directions: lanes → tools.",
                                         "Allowed directions: lanes → bin."),
                     lambda t: t.replace("A described line", "Another line"),
                     lambda t: t.replace("### `bin/`", "### `viewer/`")):
            with self.subTest():
                self.assertEqual(("checked", []), confirmation_verdict(
                    sample(self.confirmed(digest), edit)))

    def test_the_newest_confirmation_is_the_one_checked(self):
        digest = decided_hash(sample())
        entries = (self.confirmed("0" * 64, date="2026-09-20")
                   + self.confirmed(digest, date="2026-09-16"))
        verdict, found = confirmation_verdict(sample(entries))
        self.assertEqual(1, len(found), found)
        self.assertIn("2026-09-20", found[0])

    def test_a_newest_confirmation_without_a_hash_is_red_once_one_has_been_recorded(self):
        digest = decided_hash(sample())
        entries = ("- 2026-09-20 · v1 · **User-confirmed** (NN-6)\n"
                   + self.confirmed(digest, date="2026-09-16"))
        verdict, found = confirmation_verdict(sample(entries))
        self.assertEqual("checked", verdict)
        self.assertEqual(1, len(found), found)
        self.assertIn("records no hash", found[0])

    def test_the_live_document_has_every_part_the_hash_covers(self):
        """Anti-vacuity: an extraction that found nothing would hash a
        constant and pass forever."""
        parts = sections((ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8"))
        self.assertTrue(any(line.strip() for line in parts.get(1, [])))
        self.assertTrue(forbidden_lines(parts.get(3, [])))
        self.assertTrue(any(line.startswith("### NN-") for line in parts.get(6, [])))

    def test_decided_sections_match_the_newest_confirmed_hash(self):
        text = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
        verdict, found = confirmation_verdict(text)
        if verdict == "skip":
            self.skipTest(found[0])
        self.assertEqual([], found)


if __name__ == "__main__":
    unittest.main()
