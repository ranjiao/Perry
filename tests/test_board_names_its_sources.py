"""TASK-262 — `perry-tasks board` says what is stored, where, and who writes it.

`P003-O2-KR3`. Three properties, on two projects — the fixture
`test_board_from_declarations` builds (every shape, an undeclared group and an
Intake section included) and this repository, read in place (`board` is
read-only):

1. every `## ` section is followed by the one line naming its store, as
   `§ claims` declares it, and the `perry-task` subcommands whose `SURFACE`
   `writes` names that store — or saying none does;
2. a column header wears `†` exactly when its register's `*FIELD_BY_COLUMN`
   map gives it no stored field, and the title's project name (which no record
   holds) wears it too, under a legend naming the mark;
3. with `tests/board_sources.py § strip` applied, the text is the board with no
   sources at all — the markers are added lines and header marks, nothing
   else.

Every expectation is `tests/board_sources.py`'s, built from the declarations.
Cell values are `test_board_from_declarations`'s, built from the stores.

Run: python3 tests/parallel test_board_names_its_sources
"""

from __future__ import annotations

COVERS = (
    "bin/perry-task",
    "schema/state-schema.json",
    "tests/board_sources.py",
    "perry/",
    ".perry/",
)

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "bin"))
sys.path.insert(0, str(ROOT / "viewer"))

import board_sources as bs  # noqa: E402
import inproc  # noqa: E402
import parsers as P  # noqa: E402
import perry_store  # noqa: E402
import test_board_from_declarations as d1  # noqa: E402


def board(root: Path):
    return inproc.run("perry-tasks", ["board", "--root", str(root)])


class Sources:
    """The three properties over one project. Mixed into two cases."""

    root: Path

    def render(self) -> str:
        out = board(self.root)
        self.assertEqual(out.returncode, 0, out.stderr)
        return out.stdout

    def test_every_section_names_its_store_and_its_writers(self):
        got = bs.measure(self.render())["sections"]
        self.assertGreaterEqual(len(got), len(bs.SPEC["headings"]),
                                "fewer sections than the template declares")
        for s in got:
            with self.subTest(section=s["title"]):
                self.assertEqual(s["got"], s["want"])

    def test_every_column_is_marked_exactly_when_it_has_no_stored_field(self):
        got = bs.measure(self.render())["columns"]
        for c in got:
            with self.subTest(section=c["section"], column=c["column"]):
                self.assertNotEqual(c["marked"], c["stored"])
        # Anti-vacuity: both answers occur, so neither half is untested.
        self.assertTrue(any(c["marked"] for c in got), "no column is marked")
        self.assertTrue(any(c["stored"] for c in got), "no column is stored")

    def test_the_title_is_marked_and_the_legend_names_the_mark(self):
        lines = self.render().split("\n")
        self.assertEqual(lines[0], f"# Board — {P.project_name(self.root)} {bs.MARK}")
        self.assertTrue(lines[1].startswith(f"> {bs.MARK} = not stored"), lines[1])
        self.assertEqual(sum(1 for l in lines if l.startswith(f"> {bs.MARK} =")), 1)

    def test_nothing_else_moved(self):
        """The strip rule yields the board with no sources, byte for byte, and
        removes exactly the legend and one line per section."""
        text = self.render()
        schema = json.loads((ROOT / "schema" / "state-schema.json")
                            .read_text(encoding="utf-8"))
        spec = next(f for f in schema["files"] if f.get("id") == "board")
        # Resolved, as the tool resolves `--root`: a temp dir under a symlink
        # (`/var` → `/private/var`) otherwise reads its `perry/` state root as
        # outside the project, and the stores load empty.
        root = self.root.resolve()
        stores, findings = perry_store.load_board_stores(P.resolve_state_root(root))
        self.assertEqual(findings, [])
        self.assertTrue(stores["tasks"], "the bare render would have no rows")
        bare, _ = perry_store.declared_board(
            spec, (ROOT / spec["template"]).read_text(encoding="utf-8"), stores,
            project_name=P.project_name(root))
        stripped = bs.strip(text)
        self.assertNotEqual(stripped, text, "the strip rule removed nothing")
        self.assertEqual(stripped, bare)
        sections = sum(1 for l in text.split("\n") if l.startswith("## "))
        self.assertEqual(len(text.split("\n")) - len(stripped.split("\n")),
                         sections + 1)


class TestAFixtureProject(Sources, unittest.TestCase):

    def setUp(self):
        self.fx = d1.Fixture()
        self.root = self.fx.root
        self.addCleanup(self.fx.close)

    def test_the_fixture_prints_an_undeclared_group_and_intake(self):
        """Anti-vacuity: the two sections the template does not place."""
        titles = [s["title"] for s in bs.measure(self.render())["sections"]]
        self.assertIn("Someday", titles)
        self.assertIn("Intake", titles)


class TestThisRepository(Sources, unittest.TestCase):
    root = ROOT


class TestATableNoRegisterOwns(unittest.TestCase):
    """Choice "a table under an undeclared heading": printed as the template
    writes it. Neither project carries one, so it is built here — otherwise
    the branch that marks it is exercised by nothing."""

    EXTRA = "\n## Notes\n\n| Topic | Where |\n|---|---|\n| retro | wiki |\n"

    def render(self, sources):
        schema = json.loads((ROOT / "schema" / "state-schema.json")
                            .read_text(encoding="utf-8"))
        spec = next(f for f in schema["files"] if f.get("id") == "board")
        template = (ROOT / spec["template"]).read_text(encoding="utf-8") + self.EXTRA
        text, _ = perry_store.declared_board(spec, template, {}, project_name="x",
                                             sources=sources)
        return text

    def test_its_section_says_no_store_and_every_column_is_marked(self):
        text = self.render({"claims": bs.CLAIMS, "writers": bs.writer_surface()})
        lines = text.split("\n")
        at = lines.index("## Notes")
        self.assertEqual(lines[at + 1], bs.expected_source_line(None, bs.writer_surface()))
        got = [c for c in bs.measure(text)["columns"] if c["section"] == "Notes"]
        self.assertEqual([(c["column"], c["marked"]) for c in got],
                         [("Topic", True), ("Where", True)])
        self.assertIn("| retro | wiki |", lines)
        self.assertEqual(bs.strip(text), self.render(None))


class TestTheDeclarationsTheLinesComeFrom(unittest.TestCase):
    """What the expectations rest on, so a declaration that changes under
    them is named rather than silently absorbed."""

    def test_every_board_register_store_is_claimed(self):
        for register in bs.SECTION_NAME:
            with self.subTest(register=register):
                self.assertIsNotNone(bs.store_claim(register))

    def test_a_store_no_subcommand_declares_says_so_and_names_nobody(self):
        surface = bs.writer_surface()
        empty = {"name": surface["name"], "subcommands": []}
        line = bs.expected_source_line("risks", empty)
        self.assertIn("no `perry-task` subcommand declares a write", line)
        self.assertEqual(perry_store.section_source_line(
            "risks", bs.CLAIMS, empty), line)

    def test_the_writers_are_the_surface_s_not_the_nearest(self):
        """A write declared on `risks.jsonl` alone lands on that store's line
        and on no other."""
        fake = {"name": "perry-task", "subcommands": [
            {"name": "risk-add", "writes": ["risks.jsonl"]},
            {"name": "next", "writes": ["tasks.jsonl"]}]}
        for register, want in (("risks", "risk-add"), ("tasks", "next"),
                               ("asks", None)):
            with self.subTest(register=register):
                got = perry_store.section_source_line(register, bs.CLAIMS, fake)
                self.assertEqual(got, bs.expected_source_line(register, fake))
                if want:
                    self.assertTrue(got.endswith(f"`perry-task` {want}"), got)


if __name__ == "__main__":
    unittest.main()
