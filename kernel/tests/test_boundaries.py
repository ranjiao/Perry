"""The kernel's boundaries (§ 3; NN-K1, NN-K2) and the thin wrapper
(acceptance criterion 10).

The scans read Python source with `ast`; they never import what they scan.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import unittest

from support import PACKAGE, WRAPPER, clean_env, mkdtemp

SOURCES = sorted(PACKAGE.glob("*.py"))
PROCESS_MODULES = {"subprocess", "multiprocessing", "pty", "pexpect",
                   "concurrent"}
PROCESS_CALLS = {"system", "popen", "fork", "forkpty", "posix_spawn",
                 "posix_spawnp", "startfile"}
PROCESS_PREFIXES = ("exec", "spawn")


def tree(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def docstrings(module: ast.Module) -> set[int]:
    """The ids of every docstring node, so a scan of string literals can
    leave the documentation alone."""
    out = set()
    for node in ast.walk(module):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                out.add(id(body[0].value))
    return out


class TestTheKernelImportsOnlyTheStandardLibrary(unittest.TestCase):

    def test_imports(self):
        self.assertGreaterEqual(len(SOURCES), 8)
        stdlib = set(sys.stdlib_module_names)
        found = []
        for path in SOURCES:
            for node in ast.walk(tree(path)):
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    if node.level:  # relative: inside perry_kernel
                        continue
                    names = [node.module or ""]
                else:
                    continue
                for name in names:
                    top = name.split(".")[0]
                    if top not in stdlib and top != "perry_kernel":
                        found.append(f"{path.name}: {name}")
        self.assertEqual(found, [])

    def test_the_scan_would_see_a_forbidden_import(self):
        stdlib = set(sys.stdlib_module_names)
        for source in ("import lib", "from viewer import parsers",
                       "import perry_store"):
            node = ast.parse(source).body[0]
            name = (node.names[0].name if isinstance(node, ast.Import)
                    else node.module)
            self.assertNotIn(name.split(".")[0], stdlib)


class TestTheKernelRunsNoCommandAndReadsNoMarkdown(unittest.TestCase):
    """NN-K2, with no exceptions."""

    @staticmethod
    def offences(source: str, name: str = "<source>") -> list[str]:
        module = ast.parse(source)
        docs = docstrings(module)
        out = []
        for node in ast.walk(module):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = ([a.name for a in node.names]
                         if isinstance(node, ast.Import)
                         else [node.module or ""])
                for n in names:
                    if n.split(".")[0] in PROCESS_MODULES:
                        out.append(f"{name}: imports {n}")
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id == "os":
                    attr = node.attr
                    if attr in PROCESS_CALLS or attr.startswith(
                            PROCESS_PREFIXES):
                        out.append(f"{name}: os.{attr}")
            elif isinstance(node, ast.Name) and node.id == "__import__":
                out.append(f"{name}: __import__")
            elif (isinstance(node, ast.Constant)
                  and isinstance(node.value, str) and id(node) not in docs):
                if ".md" in node.value.lower() or "markdown" in \
                        node.value.lower():
                    out.append(f"{name}: string {node.value!r}")
        return out

    def test_no_process_and_no_markdown_in_the_package_or_the_wrapper(self):
        found = []
        for path in [*SOURCES, WRAPPER]:
            found += self.offences(path.read_text(encoding="utf-8"), path.name)
        self.assertEqual(found, [])

    def test_the_scan_would_see_each_offence(self):
        for source in ("import subprocess", "from subprocess import run",
                       "import os\nos.system('x')", "import os\nos.execv(1, 2)",
                       "import os\nos.spawnl(1)", "import os\nos.popen('x')",
                       "open('README.md')", "x = '*.md'",
                       "__import__('subprocess')"):
            with self.subTest(source=source):
                self.assertTrue(self.offences(source))
        self.assertEqual(self.offences('"""Reads no README.md."""'), [])


class TestTheWrapper(unittest.TestCase):
    """Acceptance 10: `bin/perry-kernel --help` exits 0 and executes nothing,
    and the wrapper holds no logic beyond importing the package."""

    def test_help_exits_zero_and_executes_nothing(self):
        tmp = mkdtemp(self)
        store = tmp / "never.db"
        env = clean_env(PERRY_STORE=str(store), PERRY_KERNEL_TESTING=None,
                        PERRY_PROJECT=str(tmp / "no-such-project"))
        for argv in (["--help"], ["-h"], ["item", "create", "--help"],
                     ["init", "--input", "{}", "--root", str(tmp), "-h"],
                     ["import", "--help", "--store", str(store)]):
            with self.subTest(argv=argv):
                before = sorted(os.listdir(tmp))
                proc = subprocess.run([str(WRAPPER), *argv], cwd=str(tmp),
                                      env=env, capture_output=True, text=True,
                                      timeout=60)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("usage: perry-kernel", proc.stdout)
                self.assertEqual(proc.stderr, "")
                self.assertEqual(sorted(os.listdir(tmp)), before)
        self.assertFalse(store.exists())

    def test_the_wrapper_is_an_import_and_a_call(self):
        self.assertTrue(os.access(WRAPPER, os.X_OK))
        text = WRAPPER.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("#!/usr/bin/env python3\n"))
        self.assertLessEqual(len(text.splitlines()), 15)
        module = ast.parse(text)
        kinds = [type(n).__name__ for n in module.body]
        self.assertEqual(kinds, ["Expr", "Import", "ImportFrom", "Expr",
                                 "ImportFrom", "If"])
        banned = (ast.FunctionDef, ast.ClassDef, ast.For, ast.While, ast.Try,
                  ast.With, ast.Lambda)
        self.assertFalse([n for n in ast.walk(module)
                          if isinstance(n, banned)])
        path_setup = module.body[3].value
        self.assertEqual(ast.unparse(path_setup.func), "sys.path.insert")
        self.assertIn("/ 'kernel'", ast.unparse(path_setup))
        self.assertEqual(module.body[4].module, "perry_kernel")
        guard = module.body[5]
        self.assertEqual(ast.unparse(guard.test), "__name__ == '__main__'")
        self.assertEqual([ast.unparse(s) for s in guard.body],
                         ["sys.exit(main())"])


if __name__ == "__main__":
    unittest.main()
