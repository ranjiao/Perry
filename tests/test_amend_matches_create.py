"""`bin/perry-goals`: the amend path must answer exactly as the create path.

The task this belongs to has failed three V4 rounds, every time on the same
shape and never on the same flag: **the same tool, given the same value,
returning two different answers depending on which subcommand carried it.**

Round 2 found a line break refused on create and collapsed on amend. Round 3
found six more characters doing it, and then two more flags:

- **whitespace-only ERASED the cell on amend** — covered in
  `test_goals_writer.py` beside the line-break case, at CLI level and against
  the file, because the first version here asserted that the guard's *source
  construct* existed and stayed green when the condition inside it was mutated
  to `if False:`;
- **`append_separator_cell` assumed a trailing `|`** where `append_cell`
  explicitly handles its absence, so widening a table written without trailing
  pipes produced a 7-cell header, a 6-cell separator and 7-cell rows — rc 0, no
  warning, `perry-lint` silent.

Run: python3 tests/parallel test_amend_matches_create
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "viewer"))
from tables import append_cell, split_row  # noqa: E402


def goals():
    spec = importlib.util.spec_from_loader(
        "perry_goals",
        importlib.machinery.SourceFileLoader(
            "perry_goals", str(ROOT / "bin" / "perry-goals")))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestAWidenIsAtomic(unittest.TestCase):
    """Both halves of one widen must make the same assumption, or the table is
    ragged the moment it lands."""

    def setUp(self):
        self.g = goals()

    def test_a_table_with_trailing_pipes(self):
        self.assertEqual(
            len(split_row(append_cell("| a | b |", "c"))),
            len(split_row(self.g.append_separator_cell("| --- | --- |"))))

    def test_a_table_without_trailing_pipes(self):
        """Markdown allows it and real boards use it. This is the case that
        produced a header and separator of different widths."""
        self.assertEqual(
            len(split_row(append_cell("| a | b", "c"))),
            len(split_row(self.g.append_separator_cell("| --- | ---"))))

    def test_the_widened_separator_is_still_a_separator(self):
        out = self.g.append_separator_cell("| --- | ---")
        self.assertTrue(all(set(c) <= set("-: ") and c.strip()
                            for c in split_row(out)), out)


if __name__ == "__main__":
    unittest.main()
