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

import pathlib
import subprocess
import sys
import unittest

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


class TestTheRefusalNamesTheFlag(unittest.TestCase):
    def run_task(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-task"), *args],
            capture_output=True, text=True, cwd=ROOT)

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
        unparseable records).
        """
        a = self.run_task("add", "--title", "x\ny", "--deliverable", "d",
                          "--verification", "V2 lint").stderr
        b = self.run_task("next", "TASK-038", "--next", "x\ny").stderr
        self.assertIn("--title", a)
        self.assertIn("--next", b)
        self.assertNotIn("--title", b)


if __name__ == "__main__":
    unittest.main()
