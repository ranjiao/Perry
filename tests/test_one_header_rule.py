"""One rule for a header cell, across every reader — the category, not the list.

TASK-050 unified `viewer/parsers.py` onto `viewer/tables.py § squash` and was
reported done. A fresh-context V4 review then found **three surviving second
implementations** in files that never imported it — `bin/perry-state` (twice)
and `bin/perry-diagnose` (once) — each resolving a header cell with
`.strip("*` ").lower()`.

The two rules agree on plain text and disagree on decoration that covers only
part of a cell:

    '**Default** rung'   .lower() → 'default** rung'      squash → 'default rung'
    'Default  rung'      .lower() → 'default  rung'       squash → 'default rung'

So a project that bolded half a header lost that column silently: `parse_tracks`
reported no `Default rung` for every track, and `perry-diagnose.md_table` — which
reads the **user's** board and OKR — lost it too.

This module is the guard the previous round did not have. The previous one was
`assertIs(P.squash, PT.squash)`, which asserts two modules share a function and
says nothing about a third module that imported neither.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import re
import sys
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
from tables import squash  # noqa: E402

#: Every file that reads a Perry state file. Not a curated list of offenders —
#: the point is that a NEW reader is caught too, so this is "everything in
#: `bin/` plus the `viewer/` readers", minus the one that defines the rule.
READERS = sorted(
    [p for p in (PERRY_HOME / "bin").iterdir()
     if p.is_file() and not p.name.endswith((".md", ".pyc"))]
    + [PERRY_HOME / "viewer" / "parsers.py"])

#: A HEADER cell resolved by a rule other than `squash`. The shape that makes
#: it a header rather than a value: the result is a **list built over a row's
#: cells**, which is then used to find columns by name. A scalar `.lower()` on
#: one cell is a value normalizer — `perry-state`'s `Status` test,
#: `perry-task`'s `Outcome` test, `parse_frequency` — and those are legitimately
#: their own rules, because they normalize what a project WROTE rather than
#: which column it wrote it in. Narrowing this to the header shape is the whole
#: judgement in this module; widening it flags eight correct call sites.
SECOND_RULE = re.compile(
    r"=\s*\[[^\]]*?\.lower\(\)[^\]]*?\bfor\b\s+\w+\s+in\s+"
    r"(?:cells|split_row\()")


class TestOneRuleForAHeaderCell(unittest.TestCase):

    def test_the_two_rules_actually_diverge(self):
        """If they agreed, this whole module would be ceremony. They do not."""
        self.assertNotEqual(squash("**Default** rung"),
                            "**Default** rung".strip("*` ").lower())
        self.assertEqual(squash("**Default** rung"), "default rung")
        self.assertEqual(squash("Default  rung"), "default rung")

    def test_no_reader_resolves_a_header_cell_by_a_second_rule(self):
        offenders = []
        for p in READERS:
            src = p.read_text(encoding="utf-8", errors="replace")
            for n, line in enumerate(src.split("\n"), 1):
                if line.lstrip().startswith("#"):
                    continue          # a comment quoting the old rule is fine
                if SECOND_RULE.search(line):
                    offenders.append(f"{p.name}:{n}: {line.strip()}")
        self.assertEqual(offenders, [], "header cells resolved by a second rule:\n"
                                        + "\n".join(offenders))

    def test_every_reader_that_resolves_headers_reaches_the_one_rule(self):
        """The complement: catching the old spelling is not enough if a reader
        invents a third. A file that reads tables must reach `squash` — either
        by importing it, or through `perry-lint`'s `norm` alias, which the next
        test pins to the same object."""
        missing = []
        for p in READERS:
            src = p.read_text(encoding="utf-8", errors="replace")
            if "split_row(" not in src:
                continue              # does not read markdown tables at all
            if "squash" not in src and ".norm(" not in src:
                missing.append(p.name)
        self.assertEqual(missing, [], f"read tables without reaching `squash`: {missing}")

    def test_the_norm_alias_is_the_same_object_and_not_a_second_copy(self):
        """`bin/perry-migrate` reaches the rule as `L.norm`. That is only
        acceptable while `norm` IS `squash`; the day someone gives it a body,
        the alias becomes the fifth implementation and this goes red."""
        loader = importlib.machinery.SourceFileLoader(
            "perry_lint", str(PERRY_HOME / "bin" / "perry-lint"))
        spec = importlib.util.spec_from_loader("perry_lint", loader)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertIs(mod.norm, squash)


class TestTheDecoratedHeaderIsActuallyRead(unittest.TestCase):
    """Behaviour, not grep. A guard that only greps can be satisfied by a
    rename; this one fails if the column is lost."""

    CONFIG = (
        "# Perry configuration\n\n- State root: .\n\n## Tracks\n\n"
        "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | **Default** rung |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| ops | queue | OKR.md | new -> done | — | 3d | — | V2 |\n")

    def _parse(self, text):
        loader = importlib.machinery.SourceFileLoader(
            "perry_state", str(PERRY_HOME / "bin" / "perry-state"))
        spec = importlib.util.spec_from_loader("perry_state", loader)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.parse_tracks(text)

    def test_a_header_with_decoration_on_half_the_cell_still_resolves(self):
        tracks = self._parse(self.CONFIG)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].get("default_rung"), "V2",
                         "the bolded header lost its column")

    def test_the_plain_spelling_is_unchanged(self):
        tracks = self._parse(self.CONFIG.replace("**Default** rung", "Default rung"))
        self.assertEqual(tracks[0].get("default_rung"), "V2")


class TestTheFifthCopy(unittest.TestCase):
    """`read_conformance` resolved its header row with `.strip("` ").lower()`.

    That strips backticks and spaces and **leaves asterisks**, so a bolded
    `| **File** |` header was not recognised as the header — it was read as a
    DECLARATION whose version cell is not a number, and `perry-conform status`
    reported `unreadable row` against a correct file while `perry-lint` still
    said clean.

    The fifth live copy of this rule, in `viewer/parsers.py` — **the file the
    first pass claimed to have unified.** Found by a reviewer running an AST
    sweep over all 111 lowercasing sites rather than grepping for the ones it
    already knew about, which is the difference between checking the category
    and checking the instances.

    Neither of this task's own guards could see it: one enumerates `bin/` and
    one file of `viewer/`, and the behavioural guard's fixture bolds **whole
    cells**, where `squash` and `strip("` ").lower()` happen to agree.
    """

    def probe(self, header):
        import shutil, tempfile
        import parsers as P
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        (tmp / ".perry").mkdir()
        (tmp / ".perry" / "conformance.md").write_text(
            f"# Conformance\n\n{header}\n| --- | --- | --- | --- |\n"
            "| `BOARD.md` | 2 | 2026-08-18 | migrate |\n")
        rec = P.read_conformance(tmp)
        return list(rec.declarations), rec.unreadable

    def test_decoration_on_the_header_changes_nothing(self):
        plain = self.probe("| File | Shape version | Declared | Route |")
        for header in ("| **File** | **Shape version** | **Declared** | "
                       "**Route** |",
                       "| `File` | Shape version | Declared | Route |",
                       "|  File  |  Shape version | Declared | Route |"):
            with self.subTest(header=header):
                self.assertEqual(self.probe(header), plain)

    def test_a_bolded_header_is_not_reported_as_a_broken_row(self):
        _, unreadable = self.probe(
            "| **File** | **Shape version** | **Declared** | **Route** |")
        self.assertEqual(unreadable, [])


if __name__ == "__main__":
    unittest.main()
