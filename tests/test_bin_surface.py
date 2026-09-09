"""DESIGN-016 C1 — the declaration and the code agree, in both directions.

`SURFACE` inside each tool is what its parser reads, what `--describe --json`
prints, what `bin/perry list` indexes and what the generated usage block says.
That is only safe while the declaration and the code cannot drift, so this
module holds them together:

- every declared subcommand is REACHABLE — the tool dispatches it;
- every dispatchable subcommand is DECLARED — nothing is reachable and unlisted;
- for `perry-task`, every flag a handler reads is declared for that subcommand,
  re-derived from the source rather than trusted. That direction is the one
  that matters: `--kr` and `--design` were each accepted by a flat 46-flag
  table and dropped by the handler, twice, and nothing compared the two.

Run: python3 tests/parallel -j 4 test_bin_surface
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(os.environ.get("PERRY_HOME")
                  or Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(PERRY_HOME / "tests"))
sys.path.insert(0, str(PERRY_HOME / "bin"))
sys.path.insert(0, str(PERRY_HOME / "viewer"))

import inproc  # noqa: E402
import lib  # noqa: E402

BIN = PERRY_HOME / "bin"
PERRY = BIN / "perry"

#: The tools that declare a surface today. `bin/perry list` reports the rest as
#: undeclared rather than hiding them, and this list is what C1 has converted.
DECLARED = ("perry-task", "perry-tasks", "perry-okr", "perry-config",
            "perry-state", "perry-diagnose")


def surface(tool: str) -> dict:
    return inproc.load(tool).SURFACE


class TestEveryDeclarationIsWellFormed(unittest.TestCase):

    def test_check_surface_finds_nothing(self):
        for tool in DECLARED:
            with self.subTest(tool=tool):
                self.assertEqual(lib.check_surface(surface(tool)), [])

    def test_the_name_is_the_file_name(self):
        for tool in DECLARED:
            with self.subTest(tool=tool):
                self.assertEqual(surface(tool)["name"], tool)

    def test_every_subcommand_has_a_summary(self):
        for tool in DECLARED:
            for sub in surface(tool).get("subcommands", ()):
                with self.subTest(tool=tool, sub=sub["name"]):
                    self.assertTrue(sub.get("summary"),
                                    "a line in `perry list` with nothing on it")


class TestDeclaredAndDispatchableAreTheSameSet(unittest.TestCase):
    """Neither direction alone is enough: a declaration listing a subcommand
    nobody dispatches sends a caller at a refusal, and a subcommand nobody
    declares is now unreachable, because the parser refuses what the
    declaration does not list."""

    def test_every_declared_subcommand_is_reached(self):
        """Behavioural, not a regex over the dispatch: each subcommand is RUN
        against an empty project, and what is asserted is that the tool did not
        answer "that is not a subcommand". Whatever else it says — a refusal, a
        missing file, an empty store — means the name reached its handler."""
        with tempfile.TemporaryDirectory() as empty:
            for tool in ("perry-task", "perry-tasks", "perry-okr",
                         "perry-config"):
                for sub in surface(tool).get("subcommands", ()):
                    with self.subTest(tool=tool, sub=sub["name"]):
                        out = subprocess.run(
                            [sys.executable, str(BIN / tool), sub["name"],
                             "--root", empty],
                            capture_output=True, text=True)
                        blob = out.stdout + out.stderr
                        self.assertNotIn("is not a subcommand", blob)
                        self.assertNotIn("expected one of", blob)
                        self.assertNotIn("expected build", blob)

    def test_a_name_that_is_not_declared_is_refused(self):
        """The control for the case above: the refusal it looks for is
        reachable, so a tool that never refuses anything cannot pass."""
        for tool in ("perry-task", "perry-tasks", "perry-okr", "perry-config"):
            with self.subTest(tool=tool):
                out = subprocess.run(
                    [sys.executable, str(BIN / tool), "no-such-subcommand"],
                    capture_output=True, text=True)
                self.assertEqual(out.returncode, 2)

    def test_every_name_the_source_dispatches_is_declared(self):
        """The other direction, read off each tool's own command table."""
        for tool, names in (
                ("perry-task", set(inproc.load("perry-task").COMMANDS)),
                ("perry-config", set(inproc.load("perry-config").COMMANDS)),
                ("perry-okr", set(inproc.load("perry-okr").store.COMMANDS))):
            declared = {s["name"] for s in surface(tool).get("subcommands", ())}
            for name in sorted(names):
                with self.subTest(tool=tool, sub=name):
                    self.assertIn(name, declared)


class TestPerryTaskDeclaresTheFlagsItsHandlersRead(unittest.TestCase):
    """The direction `--kr` and `--design` broke, re-derived rather than
    trusted: walk each handler's AST for `args.<attr>` reads, map them back to
    flags, and require the declaration to list them."""

    @classmethod
    def setUpClass(cls):
        cls.src = (BIN / "perry-task").read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.src)
        cls.funcs = {n.name: n for n in cls.tree.body
                     if isinstance(n, ast.FunctionDef)}
        seg = cls.src[cls.src.index("def parse(argv"):
                      cls.src.index("# The single source of truth")]
        cls.flag_of = {}
        for flag, attr in re.findall(r'"(--[a-z-]+)":\s*"([a-z_]+)"', seg):
            cls.flag_of.setdefault(attr, flag)
        for flag, attr in (("--dry-run", "dry_run"), ("--json", "as_json"),
                           ("--all", "all"), ("--clear", "clear"),
                           ("--unlinked", "unlinked")):
            cls.flag_of.setdefault(attr, flag)

    def _reads(self, node, depth=0, seen=None):
        seen = seen if seen is not None else set()
        out = set()
        for n in ast.walk(node):
            if (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                    and n.value.id == "args"):
                out.add(n.attr)
            if isinstance(n, ast.Call) and depth < 2:
                name = (n.func.id if isinstance(n.func, ast.Name)
                        else n.func.attr if isinstance(n.func, ast.Attribute)
                        else None)
                passes = any(isinstance(a, ast.Name) and a.id == "args"
                             for a in n.args) or any(
                    isinstance(k.value, ast.Name) and k.value.id == "args"
                    for k in n.keywords)
                if name in self.funcs and name not in seen and passes:
                    seen.add(name)
                    out |= self._reads(self.funcs[name], depth + 1, seen)
        return out

    #: `cell_writer(field, flag, …)` builds its handler as a closure over
    #: `getattr(args, flag)`, which no AST walk can see. The flag is the call's
    #: second argument, so it is read from the call site instead.
    CELL_WRITERS = dict(re.findall(
        r'^cmd_([a-z_]+) = cell_writer\(\s*"[a-z_ ]+",\s*"([a-z_]+)"',
        (BIN / "perry-task").read_text(encoding="utf-8"), re.M))

    def test_every_flag_a_handler_reads_is_declared_for_that_subcommand(self):
        face = surface("perry-task")
        universal = lib.always_accepted(face)
        table = re.findall(r'"([a-z-]+)": (cmd_[a-z_]+)',
                           self.src[self.src.index("COMMANDS = {"):
                                    self.src.index("def project_lock")])
        for name, fn in table:
            sub = lib.surface_subcommand(face, name)
            with self.subTest(sub=name):
                self.assertIsNotNone(sub, f"{name} is dispatched and undeclared")
                declared = set(sub.get("flags", ())) | universal
                if fn in self.funcs:
                    attrs = self._reads(self.funcs[fn])
                else:                       # a `cell_writer` closure
                    attrs = {self.CELL_WRITERS[fn.removeprefix("cmd_")],
                             "actor", "dry_run"}
                wanted = {self.flag_of[a] for a in attrs if a in self.flag_of}
                missing = sorted(wanted - declared - {"--root"})
                self.assertEqual(missing, [],
                                 f"{name} reads {missing} and does not declare "
                                 f"them, so the parser refuses what the handler "
                                 f"wants")

    def test_the_derivation_finds_something(self):
        """The control: if `_reads` returned nothing the case above would pass
        for every subcommand and prove nothing."""
        self.assertIn("title", self._reads(self.funcs["cmd_add"]))


class TestTheIndexIsDerivedFromTheDeclarations(unittest.TestCase):

    def _perry(self, *argv):
        return subprocess.run([sys.executable, str(PERRY), *argv],
                              capture_output=True, text=True)

    def test_list_names_every_declared_tool_and_subcommand(self):
        out = self._perry("list")
        self.assertEqual(out.returncode, 0, out.stderr)
        for tool in DECLARED:
            self.assertIn(tool, out.stdout)
            for sub in surface(tool).get("subcommands", ()):
                self.assertIn(sub["name"], out.stdout)

    def test_the_json_index_carries_the_same_counts(self):
        payload = json.loads(self._perry("list", "--json").stdout)
        by_name = {t["tool"]: t for t in payload["tools"]}
        for tool in DECLARED:
            with self.subTest(tool=tool):
                self.assertEqual(
                    len(by_name[tool]["subcommands"]),
                    len(surface(tool).get("subcommands", ())))

    def test_describe_reaches_one_subcommand(self):
        payload = json.loads(self._perry("describe", "tasks", "render").stdout)
        self.assertEqual(payload["subcommand"], "render")
        self.assertIn("BOARD.md", payload["writes"])

    def test_an_unconverted_tool_is_reported_rather_than_hidden(self):
        """`perry list` says which tools have no declaration yet. A silent
        omission would make the index look complete while it is not."""
        out = self._perry("list")
        self.assertIn("not yet declaring a surface", out.stdout)
        self.assertIn("perry-lint", out.stdout)

    def test_forwarding_runs_the_tool(self):
        out = self._perry("state", "--root", str(PERRY_HOME), "--dashboard")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("Project", out.stdout)


class TestDescribeAnswersForEveryDeclaredTool(unittest.TestCase):

    def test_each_tool_prints_its_own_declaration(self):
        for tool in DECLARED:
            with self.subTest(tool=tool):
                out = subprocess.run(
                    [sys.executable, str(BIN / tool), "--describe", "--json"],
                    capture_output=True, text=True)
                self.assertEqual(out.returncode, 0, out.stderr)
                payload = json.loads(out.stdout)
                self.assertEqual(payload["tool"], tool)
                self.assertEqual(
                    len(payload["subcommands"]),
                    len(surface(tool).get("subcommands", ())))


if __name__ == "__main__":
    unittest.main()
