"""Decorating a header must not change what any tool reports.

`tests/test_one_header_rule.py` checks the **shape of the source** — a header
cell resolved by a rule other than `squash`. Its regex matches a list
comprehension over cells, and a V4 reviewer showed that misses the scalar form:
`if cells[0].lower() in {"day", ""}` asks "is this the header row", which is a
header question, and on a header written `**Day**` it skipped nothing, so the
header was counted as data and every id after it shifted.

This module asks the question the other way round and does not care how the code
is written: **take a real project, bold every header cell, and assert every
reader reports exactly what it reported before.** A sixth spelling nobody
thought of fails here without anyone updating a regex.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
READERS = {
    "perry-state": ["--json"],
    "perry-task": ["list", "--all", "--json"],
    "perry-lint": ["--json"],
}

#: A header row: every cell is a short label, none is an id or a date. Matching
#: on "the line after it is a separator" is what makes this the HEADER rather
#: than a row that happens to look like one.
SEP = re.compile(r"^\s*\|\s*:?-{2,}")


def bold_headers(text: str) -> str:
    """Every header cell wrapped in `**`, nothing else touched."""
    lines = text.split("\n")
    out = list(lines)
    for i, line in enumerate(lines[:-1]):
        if not line.strip().startswith("|") or not SEP.match(lines[i + 1]):
            continue
        cells = line.split("|")
        out[i] = "|".join(
            c if not c.strip() else f" **{c.strip()}** " for c in cells)
    return "\n".join(out)


class TestDecorationIsInvisible(unittest.TestCase):
    def run_reader(self, name: str, root: Path):
        r = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / name), *READERS[name],
             "--root", str(root)],
            capture_output=True, text=True)
        try:
            payload = json.loads(r.stdout)
        except json.JSONDecodeError:
            return {"rc": r.returncode, "stdout": r.stdout}
        # **Every** absolute path is scrubbed, not three named keys. The two
        # fixtures live in different temp directories, so a path anywhere in
        # the payload differs for a reason that has nothing to do with header
        # decoration — `project.root` is one, and naming keys one at a time is
        # how a test ends up asserting the difference it created itself.
        return json.loads(re.sub(r'"/private/var/folders/[^"]*"', '"<path>"',
                                 re.sub(r'"' + re.escape(str(root)) + r'[^"]*"',
                                        '"<path>"', json.dumps(payload))))

    _SNAPSHOT: Path | None = None

    @classmethod
    def snapshot(cls) -> Path:
        """**One copy of the live tree, shared by both fixtures.**

        Copied twice, the plain and bolded projects were taken at different
        moments — and Perry tracks itself, so a `perry-task` write landing
        between them made the two differ **for a reason that has nothing to do
        with bolding**. The test failed once, exactly that way, while the board
        was being written mid-run. Both fixtures now derive from the same
        bytes, so the only thing that can differ is the decoration.
        """
        if cls._SNAPSHOT is None or not cls._SNAPSHOT.exists():
            tmp = tempfile.mkdtemp()
            shutil.copytree(PERRY_HOME / "perry", Path(tmp) / "perry")
            shutil.copytree(PERRY_HOME / ".perry", Path(tmp) / ".perry",
                            ignore=shutil.ignore_patterns("events.jsonl"))
            cls._SNAPSHOT = Path(tmp)
        return cls._SNAPSHOT

    def project(self, bold: bool) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        shutil.copytree(self.snapshot(), root, dirs_exist_ok=True)
        if bold:
            for f in (root / "perry").rglob("*.md"):
                f.write_text(bold_headers(f.read_text(errors="replace")),
                             encoding="utf-8")
            cfg = root / ".perry" / "config.md"
            cfg.write_text(bold_headers(cfg.read_text(errors="replace")),
                           encoding="utf-8")
        return root

    def test_every_reader_reports_the_same_thing_on_a_bolded_board(self):
        """Perry's own state, which is the largest real board available and the
        one whose shapes the readers were written against."""
        plain, bold = self.project(False), self.project(True)
        for name in READERS:
            with self.subTest(reader=name):
                self.assertEqual(
                    self.run_reader(name, plain),
                    self.run_reader(name, bold),
                    f"{name} reads a bolded header differently — some rule "
                    f"other than `squash` is resolving a header cell")

    def test_a_parser_the_corpus_cannot_reach_gets_no_fake_coverage(self):
        """**A test that passes with the code deleted is not coverage.**

        `_parse_legacy_tripwire_table` reads a `## Trip-wires` table Perry's own
        state does not contain, so the corpus above cannot reach it. I wrote a
        targeted test for its header check and then mutated the check away —
        the test stayed green. The reason: `if not in_table: continue` skips
        every line before the separator, so the header row never reaches that
        branch and **no spelling of it ever could**. The reviewer's finding was
        a real shape with no reachable consequence.

        The dead half was deleted rather than fixed. What is asserted here is
        the half that *is* reachable — a data row with an empty first cell —
        and it is asserted by removing the branch and watching this go red.
        """
        sys.path.insert(0, str(PERRY_HOME / "viewer"))
        import parsers as P
        with_blank = ("## Trip-wires\n\n"
                      "| Day | Condition | Response |\n|---|---|---|\n"
                      "|  | orphaned row | — |\n"
                      "| 3 | over budget | cut scope |\n")
        rows = P._parse_legacy_tripwire_table(with_blank)
        self.assertEqual([r.when for r in rows], ["3"],
                         "a row with no day was counted as a trip-wire")

    def test_the_fixture_really_does_decorate_something(self):
        """A test whose input is unchanged asserts nothing. This is the
        anti-vacuity check the header-rule module's own regex lacked."""
        plain = (PERRY_HOME / "perry" / "BOARD.md").read_text()
        bolded = bold_headers(plain)
        self.assertNotEqual(plain, bolded)
        self.assertIn("**ID**", bolded)
        self.assertNotIn("**TASK-", bolded, "a data row was decorated too")


if __name__ == "__main__":
    unittest.main()
