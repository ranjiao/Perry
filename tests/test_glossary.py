"""The glossary is a brake, so the brake itself has to hold.

A user pointed out that a single working session invents a dozen terms and
starts citing them in the same breath — opaque to the next session and to the
human reading the board. Measured before building: 20 terms Perry's own prose
uses, and for every one you could find *a file where the word occurs* and for
none of them *a place that says what it means*. **You could not tell a
definition from a mention.**

`reference/glossary.md` is the single definition, and `Implemented:` is what
makes a new concept cost something: name a tool, a schema field or a test, or
declare `prose-only` and be counted. A concept that exists only in prose is
this repository's most-found defect, and the count keeps it from being free.

Run: python3 tests/parallel test_glossary
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
GLOSSARY = ROOT / "reference" / "glossary.md"
LINT = ROOT / "bin" / "perry-lint"
EXPLAIN = ROOT / "bin" / "perry-explain"


def lint_glossary(root=ROOT):
    proc = subprocess.run(
        [sys.executable, str(LINT), "--glossary", "--root", str(root),
         "--json"], capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def terms():
    return [m.group(1).strip() for m in
            re.finditer(r"^### (.+?)$", GLOSSARY.read_text(), re.M)]


class TestPerrysOwnGlossaryHolds(unittest.TestCase):
    def test_it_is_clean(self):
        out = lint_glossary()
        self.assertEqual(out["count"], 0,
                         json.dumps(out["findings"], indent=1))

    def test_every_term_resolves_through_explain(self):
        """The whole point is that a session can ask. Enumerated from the file,
        so a term added without a working lookup fails here."""
        for t in terms():
            with self.subTest(term=t):
                proc = subprocess.run(
                    [sys.executable, str(EXPLAIN), t],
                    capture_output=True, text=True, cwd=ROOT)
                self.assertEqual(proc.returncode, 0, proc.stdout)
                self.assertNotIn("not found", proc.stdout)

    def test_the_prose_only_count_is_published(self):
        """Zero prose-only entries over zero terms is trivially true. The count
        is what makes the brake a measurement rather than a claim."""
        out = lint_glossary()
        self.assertIn("prose_only", out)
        self.assertGreater(out["entries"], 10)


class TestTheBrakeActuallyBrakes(unittest.TestCase):
    """Each finding proved by planting the defect, on a copy."""

    def setUp(self):
        import shutil, tempfile
        self.dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        (self.dir / "reference").mkdir()
        self.g = self.dir / "reference" / "glossary.md"

    def write(self, body):
        self.g.write_text("# Glossary\n\n" + body)

    def rules(self):
        import unittest.mock as _m
        proc = subprocess.run(
            [sys.executable, "-c",
             "import importlib.util,importlib.machinery,sys,json;"
             f"s=importlib.util.spec_from_loader('L',importlib.machinery."
             f"SourceFileLoader('L',{str(LINT)!r}));"
             "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
             f"m.GLOSSARY_PATH=__import__('pathlib').Path({str(self.g)!r});"
             "print(json.dumps([f.rule for f in m.check_glossary("
             f"__import__('pathlib').Path({str(self.dir)!r}))]))"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr[-600:])
        return json.loads(proc.stdout.strip().split("\n")[-1])

    def test_a_path_that_does_not_exist_is_reported(self):
        self.write("### widget\nA thing.\nImplemented: bin/perry-widget\n")
        self.assertIn("glossary-path-missing", self.rules())

    def test_an_entry_that_says_nothing_is_reported(self):
        self.write("### widget\nA thing.\n")
        self.assertIn("glossary-no-implementation", self.rules())

    def test_prose_only_is_legal_and_not_a_finding(self):
        """It is counted, not refused. A concept that genuinely is a convention
        must have somewhere honest to sit, or people write a fake path."""
        self.write("### widget\nA thing.\nImplemented: prose-only\n")
        self.assertNotIn("glossary-no-implementation", self.rules())
        self.assertNotIn("glossary-path-missing", self.rules())

    def test_a_term_nobody_uses_is_reported(self):
        self.write("### zzunusedconcept\nA thing.\nImplemented: prose-only\n")
        self.assertIn("glossary-term-unused", self.rules())


if __name__ == "__main__":
    unittest.main()
