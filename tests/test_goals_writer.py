"""TASK-037's gate: `OKR.md` survives a round trip byte for byte.

DESIGN-005 § 5.5 rates the `perry-goals` writer the riskiest of the markdown
three, for a reason no ordinary test catches — `OKR.md` is prose the user
argued with, and a writer that tidies it produces a file that still passes
`perry-lint` and no longer reads the way its author wrote it.

So this runs against the **real** files on this machine, not against a fixture
Perry generated. They disagree about almost everything and not one of them is
malformed.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "viewer"))


def _load():
    """`bin/perry-goals` has no `.py` suffix, so import it by path."""
    spec = importlib.util.spec_from_loader(
        "perry_goals",
        importlib.machinery.SourceFileLoader(
            "perry_goals", str(ROOT / "bin" / "perry-goals")))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G = _load()

#: In-repo files, always present. `CORPUS` adds the ones that only exist on a
#: machine where those projects are checked out.
IN_REPO = [
    ROOT / "perry" / "OKR.md",
    ROOT / "tests" / "fixtures" / "sample-project" / "OKR.md",
    ROOT / "goals" / "state" / "OKR_TEMPLATE.md",
]
ELSEWHERE = [
    pathlib.Path.home() / "proj" / "gimegime-pmo" / "OKR.md",
    pathlib.Path.home() / "proj" / "aimark" / "perry" / "OKR.md",
]


class TestByteIdentity(unittest.TestCase):
    """Load it, change nothing, write it back."""

    def test_the_in_repo_files_round_trip(self):
        for path in IN_REPO:
            self.assertTrue(path.exists(), f"{path} is gone; fix this list")
            with self.subTest(path=path.name):
                doc = G.Okr(path)
                self.assertEqual(path.read_text(), doc.render())
                self.assertTrue(doc.unchanged())

    def test_the_files_outside_the_repo_round_trip_when_present(self):
        """Skipped rather than failed when those projects are not checked out
        — but never silently: a skip that prints nothing is the same as a
        check that was never written."""
        found = [p for p in ELSEWHERE if p.exists()]
        if not found:
            self.skipTest(
                f"none of {[str(p) for p in ELSEWHERE]} present on this "
                f"machine; the in-repo corpus still ran")
        for path in found:
            with self.subTest(path=str(path)):
                self.assertEqual(path.read_text(), G.Okr(path).render())

    def test_the_corpus_actually_disagrees(self):
        """A round-trip test over three files written by the same template
        proves nothing. This asserts the corpus contains the shapes the gate
        is about, so it cannot quietly become uniform."""
        texts = [p.read_text() for p in IN_REPO + ELSEWHERE if p.exists()]
        joined = "\n".join(texts)
        self.assertRegex(joined, r"(?m)^### Objective \d+[:—-]",
                         "no objective heading in the corpus at all")
        self.assertGreaterEqual(
            len({t.count("\n## v") for t in texts}), 2,
            "every file in the corpus has the same number of versions, so "
            "the multi-version shape is not being exercised")

    def test_a_file_with_no_trailing_newline_round_trips(self):
        """`splitlines()` would silently absorb the difference between a file
        ending in a newline and one that does not, and write back the wrong
        one. This is why `render` uses `split`/`join`."""
        import tempfile
        for text in ("# OKR\n\n## Mission\n\nship it",
                     "# OKR\n\n## Mission\n\nship it\n",
                     "# OKR\n\n## Mission\n\nship it\n\n\n"):
            with tempfile.TemporaryDirectory() as d:
                p = pathlib.Path(d) / "OKR.md"
                p.write_text(text)
                self.assertEqual(text, G.Okr(p).render(), repr(text))


class TestLocating(unittest.TestCase):
    """The section scanner, against the shapes the real files carry."""

    def okr(self, text: str):
        import tempfile
        self._d = tempfile.TemporaryDirectory()
        p = pathlib.Path(self._d.name) / "OKR.md"
        p.write_text(text)
        return G.Okr(p)

    NESTED = """# OKR

## v2: 2026-04-30

### Objective 1: 维持长期稳定收益

text

### Anti-Goals

- not this

## v4: 2026-05-29

### Objective 1: Insurance
"""

    def test_a_version_section_swallows_the_headings_beneath_it(self):
        """gimegime-pmo nests `### Anti-Goals` inside a version. A scanner
        that stopped at any heading would cut that version in half and a
        writer would then append into the middle of it."""
        o = self.okr(self.NESTED)
        lo, hi = o.section(r"v2\b")
        body = "\n".join(o.lines[lo:hi])
        self.assertIn("Anti-Goals", body)
        self.assertNotIn("v4", body)

    def test_a_missing_section_is_refused_not_guessed(self):
        o = self.okr(self.NESTED)
        self.assertFalse(o.has_section(r"Commitments"))
        with self.assertRaises(G.Refused):
            o.section(r"Commitments")

    def test_rows_key_by_header_not_position(self):
        """The defect `schema/README.md` names outright: columns resolve by
        name, never by position."""
        o = self.okr("""# OKR

## Commitments

| Id | Track | Promise | To whom | By when | Status |
|---|---|---|---|---|---|
| ops/1 | ops | Invoices reconciled | Finance | within the track SLA | active |
""")
        lo, hi = o.section(r"Commitments")
        rows = o.rows(lo, hi)
        self.assertEqual(1, len(rows))
        _, cells = rows[0]
        self.assertEqual("ops/1", cells["id"])
        self.assertEqual("Finance", cells["to whom"])
        self.assertEqual("within the track SLA", cells["by when"])

    def test_a_decorated_header_still_resolves(self):
        o = self.okr("""# OKR

## Commitments

| **Id** | **Track** | `Promise` |
|---|---|---|
| ops/1 | ops | Invoices reconciled |
""")
        lo, hi = o.section(r"Commitments")
        self.assertEqual("ops/1", o.rows(lo, hi)[0][1]["id"])


if __name__ == "__main__":
    unittest.main()
