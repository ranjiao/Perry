"""One rule for "this value cannot be a table cell" — there were two.

`viewer/tables.py`'s own docstring said `render_row` and `check_cell` shared a
check. They did not. `render_row` used `len(out.splitlines()) > 1`; `check_cell`
used `"\\n" in v or "\\r" in v`. **`str.splitlines()` splits on eleven
boundaries, not two**, so for `U+2028`, `U+2029`, `\\v`, `\\f`, `\\x85` and
`\\x1c` the create path refused and the amend path accepted — the defect the
amend path had just been fixed for, on a different alphabet.

A reviewer proved it with two mutations that do not overlap: killing one guard
greened only the create paths, killing the other greened only the amend paths.
One check would have meant one mutation reddening all ten.

Also here: a refusal now names the **flag**, because `index` is a column
position and means nothing to the person who typed the command — `--next` and
`--title` produced identical refusals and neither said what to fix.

Run: python3 tests/parallel test_one_line_break_rule
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

from gate import GATE_OFF   # tests/gate.py — why this fixture opts out

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "viewer"))
import tables as T  # noqa: E402

#: Every boundary `str.splitlines()` breaks on that is not LF or CR. These are
#: the six that diverged, enumerated from the language rather than from the
#: bug report — the bug report named two.
EXOTIC = {
    "U+2028 line separator": " ",
    "U+2029 paragraph separator": " ",
    "vertical tab": "\v",
    "form feed": "\f",
    "NEL (U+0085)": "\x85",
    "file separator": "\x1c",
}


class TestBothPathsAgree(unittest.TestCase):
    def test_the_two_ordinary_line_breaks(self):
        for name, ch in (("LF", "\n"), ("CR", "\r")):
            with self.subTest(char=name):
                self.assertIsNotNone(T.line_break_at([f"a{ch}b"]))

    def test_every_exotic_boundary_too(self):
        """The create path already refused these; the amend path accepted
        them. Enumerated, so a seventh boundary cannot arrive unnoticed."""
        for name, ch in EXOTIC.items():
            with self.subTest(char=name):
                self.assertIsNotNone(
                    T.line_break_at([f"a{ch}b"]),
                    f"{name} is a line break to str.splitlines() and must be "
                    f"refused by both paths")

    def test_render_row_and_check_cell_give_the_same_verdict(self):
        """The property, not a list. Any value either refuses, both refuse."""
        for name, ch in {**EXOTIC, "LF": "\n", "CR": "\r"}.items():
            with self.subTest(char=name):
                v = f"a{ch}b"
                self.assertRaises(T.UnrenderableCell, T.render_row, [v])
                self.assertRaises(T.UnrenderableCell, T.check_cell, v)

    def test_an_ordinary_value_passes_both(self):
        """A guard that refuses everything is not a guard."""
        self.assertIsNone(T.line_break_at(["a b", "x|y", ""]))
        self.assertEqual(T.check_cell("x|y"), "x\\|y")


class TestTheOneRuleIsOneFunction(unittest.TestCase):
    def test_neither_caller_carries_its_own_test(self):
        """The defect was two spellings of one idea. This pins that there is
        one — a second `splitlines()` or `"\\n" in` in either function means
        the split is back."""
        src = (ROOT / "viewer" / "tables.py").read_text()
        body = src[src.index("def render_row"):src.index("def cell_spans")]
        for spelling in (".splitlines()", '"\\n" in', "'\\n' in"):
            self.assertNotIn(
                spelling, body,
                f"a caller spells the line-break test itself ({spelling!r}); "
                f"`line_break_at` is the rule")


class TestRefusedIsDefinedWhereItIsRaised(unittest.TestCase):
    def test_splice_cell_out_of_range_raises_a_defined_exception(self):
        """`Refused` lived in `bin/perry-goals` and did not travel with the
        move, so a reachable path raised `NameError` — a traceback where a
        refusal belongs, and nothing at all under `--json`."""
        with self.assertRaises(T.UnrenderableCell):
            T.splice_cell("| a | b |", 9, "x")


BOARD = """# Board — T

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
"""


class TestTheRefusalNamesTheFlag(unittest.TestCase):
    """The refusal names the FLAG, proven on a row this test owns.

    **The fixture used to be `TASK-038` on Perry's own board.** That row was
    closed on an ordinary afternoon and left the board, so `next TASK-038`
    started answering `TASK-038 is not a row on the board` — and the assertion
    about flag naming stopped running. Read the failure carefully, because that
    is the dangerous half: the test did not report *my fixture is gone*, it
    reported *the feature is broken*. A red that misnames its own cause is
    worse than no red, and the same shape had already been fixed once that day
    (`c9018ae`, a `rows_from_store > 20` that a close made false).

    A fixture a future close can delete is not a fixture. This class builds its
    own project and its own row, so the only thing that can redden it is the
    refusal changing.
    """

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = pathlib.Path(self.dir.name)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n" + GATE_OFF)
        (self.root / "BOARD.md").write_text(BOARD)
        seed = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-tasks"), "write",
             "--from-board", "--root", str(self.root)],
            capture_output=True, text=True)
        self.assertEqual(seed.returncode, 0, seed.stdout + seed.stderr)

    def run_task(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-task"), *args,
             "--root", str(self.root)],
            capture_output=True, text=True)

    def a_row(self) -> str:
        r = self.run_task("add", "--title", "A row this test owns",
                          "--deliverable", "d", "--verification", "V2 lint",
                          "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads(r.stdout)["id"]

    def test_two_flags_do_not_produce_the_same_message(self):
        """Both flags must be ones that actually reach a table cell.

        The first version of this test used `--deliverable`, which on this
        board shape is **not a column** — it is input-quality material and
        reaches only the JSON event, where a newline escapes correctly. So
        nothing refused it, the test went red, and the finding was mine: I had
        asserted a refusal for a value that never touches markdown.

        Worth the words because the probe that found it also wrote three junk
        rows onto the live board before I noticed — the rows are dropped, and
        the event log was checked line-by-line for a raw newline (0
        unparseable records). Nothing here can repeat that either: every write
        lands under `--root` in a temp directory.
        """
        tid = self.a_row()
        a = self.run_task("add", "--title", "x\ny", "--deliverable", "d",
                          "--verification", "V2 lint").stderr
        b = self.run_task("next", tid, "--next", "x\ny").stderr
        self.assertIn("--title", a)
        self.assertIn("--next", b)
        self.assertNotIn("--title", b)

    def test_the_fixture_row_is_reachable_before_the_refusal_is_asserted(self):
        """The guard against the failure that started this.

        `next` on a row that is not on the board also exits 1 with a message on
        stderr, so a vanished fixture and a broken refusal are the same shape
        from the outside — which is exactly how the old red pointed at the
        wrong thing for hours. This asserts the row is there and writable
        FIRST, so the two can never again be confused.
        """
        tid = self.a_row()
        ok = self.run_task("next", tid, "--next", "one ordinary line")
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertNotIn("is not a row on the board", ok.stderr)
        bad = self.run_task("next", tid, "--next", "x\ny")
        self.assertEqual(bad.returncode, 1)
        self.assertNotIn("is not a row on the board", bad.stderr)


if __name__ == "__main__":
    unittest.main()
