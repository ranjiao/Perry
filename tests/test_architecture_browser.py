"""Import facts and offline evidence for the code architecture browser."""
from __future__ import annotations

COVERS = ("bin/perry-architecture", "bin/perry_architecture/")

import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))
from perry_architecture.scan import scan
from perry_architecture.report import render


class ArchitectureBrowser(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "project"
        self.root.mkdir()

    def put(self, name, source):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        return path

    def test_scripts_imports_source_positions_and_no_execution(self):
        self.put("bin/run", '#!/usr/bin/env python3\nraise RuntimeError("NEVER RUN")\n'
                 'import pkg.child\ndef action():\n    from pkg import child\n')
        self.put("src/pkg/__init__.py", "")
        self.put("src/pkg/child.py", "from . import other\n")
        self.put("src/pkg/other.py", "import os\n")
        data = scan(self.root, ["src"])
        edges = {(e["source"], e["target"]): e for e in data["edges"]}
        self.assertIn(("bin/run", "src/pkg/child.py"), edges)
        self.assertIn(("bin/run", "src/pkg/__init__.py"), edges)
        self.assertIn(("src/pkg/child.py", "src/pkg/other.py"), edges)
        self.assertEqual(1, data["summary"]["scripts"])
        ev = [data["imports"][n] for n in edges[("bin/run", "src/pkg/child.py")]["imports"]]
        self.assertEqual([3, 5], [e["line"] for e in ev])
        self.assertEqual(["function-local"], ev[1]["contexts"])
        self.assertEqual("from pkg import child", ev[1]["statement"])

    def test_relative_parent_and_invalid_relative_are_not_guessed(self):
        self.put("src/pkg/sub/module.py", "from .. import helper\nfrom .... import nope\n")
        self.put("src/pkg/helper.py", "")
        data = scan(self.root, ["src"])
        self.assertEqual("src/pkg/helper.py", data["edges"][0]["target"])
        self.assertEqual("unresolved", data["imports"][1]["resolution"])

    def test_ambiguous_roots_missing_and_local_shadowing(self):
        self.put("a/same.py", "")
        self.put("b/same.py", "")
        self.put("os.py", "")
        self.put("main.py", "import same\nimport absent\nimport os\n")
        data = scan(self.root, ["a", "b"])
        self.assertEqual(["ambiguous", "unresolved", "internal"],
                         [i["resolution"] for i in data["imports"]])
        self.assertEqual(["a/same.py", "b/same.py"], data["imports"][0]["targets"])
        self.assertEqual(["os.py"], [e["target"] for e in data["edges"]])

    def test_failures_and_dynamic_context_remain_visible(self):
        self.put("broken.py", "def broken(\n")
        self.put("big.py", "#" * 250)
        self.put("main.py", "import sys\nsys.path.insert(0, 'generated')\nif False:\n import missing\n")
        data = scan(self.root, max_bytes=200)
        self.assertEqual(3, data["summary"]["files"])
        self.assertEqual(1, data["summary"]["parsed"])
        self.assertEqual({"parse-error", "read-error", "dynamic-import-context"},
                         {i["kind"] for i in data["issues"]})
        self.assertEqual(["conditional"], data["imports"][1]["contexts"])

    def test_exclusions_symlinks_and_nested_repositories(self):
        self.put("main.py", "import hidden\n")
        self.put("vendor/hidden.py", "")
        self.put("nested/.git", "gitdir: elsewhere")
        self.put("nested/foreign.py", "")
        self.put(".venv/installed.py", "")
        outside = self.root.parent / "outside.py"
        outside.write_text("import never\n")
        (self.root / "linked.py").symlink_to(outside)
        data = scan(self.root, excludes=["vendor"])
        self.assertEqual(["main.py"], [f["id"] for f in data["files"]])
        self.assertIn("linked.py", data["scope"]["skipped_paths"])
        self.assertEqual(1, data["summary"]["unresolved"])

    def test_encoding_multiline_evidence_and_html_injection(self):
        path = self.put("latin.py", "")
        path.write_bytes(b"# coding: latin-1\n# caf\xe9\nfrom os import (\n path,\n environ,\n)\n")
        attack = '</script><script>alert("bad")</script>'
        self.put("unsafe.py", repr(attack))
        data = scan(self.root)
        self.assertEqual((3, 6), (data["imports"][0]["line"], data["imports"][0]["end_line"]))
        html = render(data)
        self.assertNotIn(attack, html)
        embedded = html.split('<script id="data" type="application/json">')[1].split('</script>')[0]
        self.assertEqual(data, json.loads(embedded))

    def test_determinism_and_source_fingerprint(self):
        self.put("main.py", "import os\n")
        a, b = scan(self.root), scan(self.root)
        self.assertEqual(a, b)
        self.put("main.py", "import sys\n")
        self.assertNotEqual(a["snapshot"], scan(self.root)["snapshot"])
        (self.root / "src").mkdir()
        self.assertNotEqual(scan(self.root)["snapshot"], scan(self.root, ["src"])["snapshot"])

    def test_deep_expression_does_not_break_traversal(self):
        self.put("deep.py", "x = " + "+".join(["1"] * 1200) + "\nimport os\n")
        data = scan(self.root)
        self.assertEqual(1, data["summary"]["parsed"])
        self.assertEqual("os", data["imports"][0]["module"])

    def test_self_scan_does_not_create_bytecode(self):
        shutil.copytree(ROOT / "bin/perry_architecture", self.root / "perry_architecture",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "bin/lib", self.root / "lib",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(ROOT / "bin/perry-architecture", self.root / "perry-architecture")
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = subprocess.run([sys.executable, str(self.root / "perry-architecture"),
                                 "--root", str(self.root)], capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_cli_works_on_unadopted_project_and_never_writes_it(self):
        file = self.put("main.py", "import os\n")
        before = file.read_bytes()
        output = self.root.parent / "report.html"
        cmd = [sys.executable, str(ROOT / "bin/perry-architecture"), "--root", str(self.root)]
        proc = subprocess.run(cmd + ["--html", str(output), "--json"], capture_output=True, text=True)
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual(1, json.loads(proc.stdout)["summary"]["files"])
        self.assertTrue(output.is_file())
        self.assertEqual(before, file.read_bytes())
        self.assertEqual([file], list(self.root.iterdir()))
        for args in (["--html", str(file)], ["--html", str(output)],
                     ["--source-roots", ".."], ["--max-file-bytes", "0"], ["--unknown"]):
            refused = subprocess.run(cmd + args, capture_output=True)
            self.assertEqual(2, refused.returncode, args)
        self.assertEqual(before, file.read_bytes())

    def test_real_perry_dependency_has_source_evidence(self):
        # Copy only the actual files needed for a known production dependency.
        # This is a bounded integration test, not an assertion about all edges.
        for name in ("bin/perry-task", "viewer/parsers.py", "viewer/tables.py", "bin/lib/__init__.py"):
            self.put(name, (ROOT / name).read_text())
        data = scan(self.root, ["bin", "viewer"])
        edge = next(e for e in data["edges"] if e["source"] == "bin/perry-task"
                    and e["target"] == "viewer/parsers.py")
        item = data["imports"][edge["imports"][0]]
        actual = (ROOT / item["source"]).read_text().splitlines()[item["line"] - 1]
        self.assertEqual("import parsers as P", actual.strip())
        self.assertEqual(actual.strip(), item["statement"])
        self.assertEqual(hashlib.sha256((ROOT / "bin/perry-task").read_bytes()).hexdigest(),
                         next(f["sha256"] for f in data["files"] if f["id"] == "bin/perry-task"))


if __name__ == "__main__":
    unittest.main()
