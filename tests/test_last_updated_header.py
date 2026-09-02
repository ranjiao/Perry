"""`BOARD.md`'s `> Last updated:` is stamped by the writer. TASK-215.

The header read `2026-08-16 (21st pass — DESIGN-004 handed off, 6 tasks)` on
**2026-08-29** — thirteen days stale on a file `perry-task` re-renders dozens of
times a day. `perry-state` publishes it as `board.last_updated` and the standup
prints it, so a number every reader takes at face value was maintained by
nobody.

**Why the writer and not the renderer.** `perry_store.render` is the tidier
home and it is the wrong one: `perry-tasks render --byte-compare` and
`perry-lint`'s store-drift census both compare a fresh render against the file
on disk. A renderer that stamped today's date would report the board as drifted
every morning until somebody happened to write to it — a guard that goes red on
the passage of time. *"Last updated" means the last WRITE, and a re-render is
not a write*, so `commit()` stamps it and a pure `render --write` leaves it
alone. `TestARenderIsNotAWrite` is that distinction.

**The editorial parenthetical is dropped, deliberately.** A rendered file's
header is not a place for prose nobody re-derives; `journal/` is where "21st
pass, 6 tasks" belongs and already carries it.

Run: python3 tests/parallel test_last_updated_header
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path

from task_writer_support import PT, TASKS, TOOL, BOARD, Project

TODAY = f"{date.today():%Y-%m-%d}"

#: A board whose preamble carries the header, in the shipped shape — the stale
#: value and the editorial note included, because both are what was there.
STALE = "> Last updated: 2026-08-16 (21st pass — DESIGN-004 handed off, 6 tasks)"


def board_with_header(extra_row: str = "") -> str:
    head, rest = BOARD.split("\n", 1)
    return f"{head}\n\n{STALE}\n{rest}{extra_row}"


def header_of(text: str) -> str | None:
    m = re.search(r"^>\s*Last updated\s*:\s*(.*)$", text, re.M)
    return m.group(1).strip() if m else None


class TestTheWriterStampsIt(unittest.TestCase):

    def test_an_ordinary_write_makes_the_header_today(self):
        p = Project(board=board_with_header())
        self.assertEqual(header_of(p.board()),
                         "2026-08-16 (21st pass — DESIGN-004 handed off, 6 tasks)")
        p.run("add", "--title", "a task")
        self.assertEqual(header_of(p.board()), TODAY)

    def test_a_second_write_leaves_it_alone(self):
        """Idempotent: the same day must not rewrite the line and dirty a diff."""
        p = Project(board=board_with_header())
        p.run("add", "--title", "a task")
        before = p.board()
        p.run("add", "--title", "another task")
        self.assertEqual(header_of(p.board()), TODAY)
        self.assertEqual(before.count("Last updated"),
                         p.board().count("Last updated"))

    def test_the_payload_reports_the_same_value(self):
        """`perry-state` publishes it; the two must not disagree."""
        p = Project(board=board_with_header())
        p.run("add", "--title", "a task")
        proc = subprocess.run(
            [sys.executable, str(TOOL.parent / "perry-state"),
             "--root", str(p.root), "--json"],
            capture_output=True, text=True)
        import json
        self.assertEqual(
            json.loads(proc.stdout)["board"]["last_updated"], TODAY)


class TestItDoesNotInventOrMisfire(unittest.TestCase):
    """Both halves of not-crying-wolf."""

    def test_a_board_without_the_header_does_not_get_one(self):
        """The header is Perry's own template convention, not a required
        section. Adding it to somebody else's board would be this tool writing
        a line the project never asked for."""
        p = Project()
        self.assertIsNone(header_of(p.board()), "fixture drifted")
        p.run("add", "--title", "a task")
        self.assertIsNone(header_of(p.board()),
                          "a header was invented on a board that had none")

    def test_a_task_row_mentioning_the_phrase_is_not_the_header(self):
        """**The live case.** `TASK-215`'s own title contains "Last updated
        header", and it sits in a table row on the board this ships with. A
        matcher that did not anchor on the quote line would have rewritten a
        task's title on the first write.
        """
        row = ("| TASK-900 | BOARD.md's Last updated: header is stale | "
               "Coding Agent | not_started | — | — |\n")
        p = Project(board=board_with_header())
        board = p.root / "BOARD.md"
        board.write_text(board.read_text().replace(
            "## P2", row + "\n## P2", 1))
        p.run("add", "--title", "a task")
        self.assertIn("BOARD.md's Last updated: header is stale", p.board(),
                      "the stamp rewrote a task row that merely says the words")
        self.assertEqual(header_of(p.board()), TODAY)


class TestARenderIsNotAWrite(unittest.TestCase):
    """The reason this lives in `commit()` and not in `render`.

    A renderer that stamped the date would make `perry-tasks render
    --byte-compare` and `perry-lint`'s store-drift census report the board as
    drifted every morning until someone wrote to it — a check that goes red on
    the passage of time and teaches people to ignore it.
    """

    def test_render_write_does_not_restamp(self):
        p = Project(board=board_with_header())
        stale = header_of(p.board())
        subprocess.run([sys.executable, str(TASKS), "render", "--write",
                        "--root", str(p.root)], capture_output=True, text=True)
        self.assertEqual(header_of(p.board()), stale,
                         "a re-render moved a date that records writes")

    def test_byte_compare_is_clean_after_a_write(self):
        p = Project(board=board_with_header())
        p.run("add", "--title", "a task")
        out = subprocess.run(
            [sys.executable, str(TASKS), "render", "--byte-compare",
             "--root", str(p.root)], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0,
                         "the stamp made the render disagree with the file:\n"
                         + out.stdout[-800:] + out.stderr[-800:])


class TestTheMatcherIsOneRule(unittest.TestCase):
    """A localized board says the same thing in its own words."""

    def test_the_chinese_spelling_is_matched(self):
        self.assertTrue(PT.LAST_UPDATED_RE.match("> 最后更新: 2026-08-16"))

    def test_a_full_width_colon_is_matched(self):
        self.assertTrue(PT.LAST_UPDATED_RE.match("> Last updated： 2026-08-16"))

    def test_a_bare_mention_is_not(self):
        self.assertIsNone(PT.LAST_UPDATED_RE.match(
            "| TASK-900 | the Last updated: header | a | b |"))


if __name__ == "__main__":
    unittest.main()
