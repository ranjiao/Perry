"""A row is one line, it reads back as itself, and everyone reads it the same.

Three guards, one subject: the markdown table row. They exist because all three
failed at once on Perry's own board, and nothing noticed.

`perry-task add --next "<text with blank lines>"` wrote raw newlines into a
table row. The row ended mid-cell with no closing `|`, the tail landed in the
document as loose paragraphs, and the *next* `add` parsed the truncated line as
the table's last row and inserted into the middle of the spilled text. Three
rows destroyed — TASK-064, TASK-065, TASK-066 — through a full `perry-lint`
run, the conformance gate, and a commit. `perry-lint` said `✓ clean`.

Behind it:

1. `render_row` escaped `|` and nothing else. The escape had been added weeks
   earlier, after a `Next action` quoting a markdown header shifted `Risk` into
   `Verification` — so the guard was shaped around the one character that had
   bitten, and the next member of the same category walked through.
2. The escape reached exactly one of the splitters: the one that WRITES.
   `viewer/parsers.py` — the read side of all three frozen contracts — had nine
   sites doing `line.strip("|").split("|")`, and `bin/perry-lint` a tenth. On a
   row `perry-task` itself wrote, they read one cell more than the writer had
   written, truncating `next_action` at the backslash and sliding the rest into
   `evidence`. `perry-task list --json` looked right only because the event log
   carried the true values and was merged over the board read — which is no
   help at all on a project with `has_event_log: false`, i.e. every row of the
   only external consumer.
3. Nothing compared a row's cell count to its header's. Every column read is
   index-guarded (`if ci >= len(row): continue`), so a short row read as one
   whose trailing columns are empty, and empty is legal for `Evidence`.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))

import tables as T  # noqa: E402
import parsers as P  # noqa: E402


def load(name: str, path: Path):
    spec = importlib.util.spec_from_loader(
        name, importlib.machinery.SourceFileLoader(name, str(path)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


HEADER = ["ID", "Title", "Owner", "Status", "Next action", "Evidence",
          "Verification"]


def board_with(rows: list[str]) -> str:
    """A minimal conformant board carrying `rows` under `## P0`."""
    return "\n".join([
        "# Board", "",
        "## Intake", "",
        "| ID | Arrived | Ask | Status |",
        "|---|---|---|---|",
        "", "## P0", "",
        T.render_row(HEADER),
        "|" + "---|" * len(HEADER),
        *rows,
        "", "## P1", "",
        T.render_row(HEADER),
        "|" + "---|" * len(HEADER),
        "", "## P2", "",
        T.render_row(HEADER),
        "|" + "---|" * len(HEADER),
        "", "## Cadence", "",
        "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |",
        "|---|---|---|---|---|---|",
        "", "## User Input Queue", "",
        "| ID | Needed from user | Blocks | Asked | Status |",
        "|---|---|---|---|---|",
        "", "## Top risks", "",
        "| ID | Risk | Opened | Severity | Cleared |",
        "|---|---|---|---|---|",
        "",
    ])


class TestARowIsOneLine(unittest.TestCase):
    """Guard 1 — the writer refuses what a markdown table cannot carry."""

    def test_a_cell_with_a_line_break_is_refused(self):
        with self.assertRaises(T.UnrenderableCell) as cm:
            T.render_row(["TASK-001", "t", "o", "not_started",
                          "first line\n\nsecond paragraph", "—", "V2"])
        self.assertEqual(cm.exception.index, 4)
        self.assertIn("one line", cm.exception.why)

    def test_a_carriage_return_is_refused_too(self):
        """The rule is `splitlines`, not the `\\n` character. A lone `\\r` ends
        a line for every Python reader in this repo, and a guard that only
        knew about `\\n` would be the same shape of mistake one character
        later."""
        with self.assertRaises(T.UnrenderableCell):
            T.render_row(["a", "b\rc"])

    def test_the_round_trip_alone_would_NOT_have_caught_it(self):
        """The reason this guard has two clauses, asserted rather than
        described.

        `split_row` scans a string for `|` and has no notion of a line, so it
        reads a cell containing `\\n` back unchanged: the round trip holds on
        precisely the value that destroys the file. The first version of this
        guard was that comparison alone and let a multi-line `--next` straight
        through. Reverting `render_row`'s `splitlines` clause must therefore
        turn `test_a_cell_with_a_line_break_is_refused` red — and this test
        exists so the *reason* is on the record and not folklore."""
        cells = ["a", "first line\n\nsecond", "c"]
        naive = "| " + " | ".join(cells) + " |"
        self.assertEqual(T.split_row(naive), cells,
                         "if this ever fails, the two-clause guard can collapse")

    def test_a_pipe_is_still_stored_because_escaping_round_trips(self):
        """The rule is not "no structural characters". `|` can be carried, so
        it is carried; `\\n` cannot, so it is refused. A guard that banned both
        would lose a `Next action` that legitimately quotes a table."""
        row = T.render_row(["a", "quotes: | ID | Risk |", "c"])
        self.assertEqual(len(row.splitlines()), 1)
        self.assertEqual(T.split_row(row), ["a", "quotes: | ID | Risk |", "c"])

    def test_an_empty_cell_list_is_refused(self):
        """The round-trip clause's one reachable trigger today, and the reason
        this test exists at all.

        Mutating that clause on its own leaves every other test green: with
        escaping intact there is no ordinary single-line value that fails to
        read back. Measured, not assumed — removing the escape is caught by the
        five escaping tests whether the clause is present or not, so the clause
        was a blind guard by this project's own definition until something
        could turn it red.

        `render_row([])` produces `|  |`, which reads back as one empty cell —
        a zero-column row is not a thing, and a table row Perry cannot describe
        should be refused rather than emitted. The clause's real job is wider:
        it asserts that `render_row` and `split_row` stay each other's inverse,
        so a future change to either that breaks the pair fails loudly here
        instead of silently shifting a user's columns."""
        with self.assertRaises(T.UnrenderableCell):
            T.render_row([])

    def test_the_refusal_names_the_cell_it_refused(self):
        with self.assertRaises(T.UnrenderableCell) as cm:
            T.render_row(["a", "b", "c\nd"])
        self.assertEqual(cm.exception.index, 2)
        self.assertEqual(cm.exception.value, "c\nd")


class TestTheWriterRefusesAndWritesNothing(unittest.TestCase):
    """Guard 1, through the CLI — a refusal must mean the file is untouched."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "perry").mkdir()
        (self.root / "perry" / "BOARD.md").write_text(board_with([]),
                                                      encoding="utf-8")
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Config\n\nState root: perry/\n", encoding="utf-8")
        self.addCleanup(self.tmp.cleanup)

    def run_add(self, next_action: str):
        env = dict(os.environ, PERRY_HOME=str(PERRY_HOME))
        return subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-task"), "add",
             "--root", str(self.root), "--title", "probe", "--priority", "P0",
             "--deliverable", "a file that exists",
             # A real check, not the rung. `--verification` takes the
             # falsifiable check; `--rung` takes the rung. This fixture said
             # "V2" — harmlessly, since it asserts nothing about the value —
             # until `add` learned to refuse a bare rung here.
             "--verification", "the row round-trips through split_row",
             "--next", next_action],
            capture_output=True, text=True, env=env)

    def test_a_multi_line_next_action_is_refused(self):
        before = (self.root / "perry" / "BOARD.md").read_bytes()
        out = self.run_add("first line\n\nsecond paragraph")
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        self.assertIn("refused", out.stderr)
        self.assertIn("one line", out.stderr)
        self.assertEqual((self.root / "perry" / "BOARD.md").read_bytes(), before,
                         "a refusal wrote to the board")

    def test_a_single_line_next_action_containing_a_pipe_is_written(self):
        out = self.run_add("quotes a table: | ID | Risk |")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        text = (self.root / "perry" / "BOARD.md").read_text(encoding="utf-8")
        row = [ln for ln in text.split("\n") if ln.startswith("| TASK-")][0]
        self.assertEqual(len(T.split_row(row)), len(HEADER))
        self.assertEqual(T.split_row(row)[4], "quotes a table: | ID | Risk |")


class TestEveryoneReadsTheRowTheSameWay(unittest.TestCase):
    """Guard 2 — one splitter. The writer's inverse, used by every reader."""

    ROW = T.render_row(["TASK-001", "t", "o", "not_started",
                        "escapes | and not the other one", "—", "V2"])

    def test_the_board_parser_reads_what_the_writer_wrote(self):
        """`viewer/parsers.py` is the read side of all three frozen contracts.
        Asserted against the BOARD ALONE, with no event log to merge over it —
        merging events is what hid this defect on Perry's own repo."""
        board = P.parse_board(board_with([self.ROW]))
        task = [t for t in board.all_tasks if t.id == "TASK-001"][0]
        self.assertEqual(task.next_action, "escapes | and not the other one")
        self.assertEqual(task.evidence, "—")
        self.assertEqual(task.verification, "V2")

    def test_the_linter_reads_the_same_cells_as_the_contract_reader(self):
        """A checker that reads a file differently from the tool that wrote it
        does not check that file. Before the fix this returned 8 cells where
        `split_row` returned 7, and `perry-lint` reported
        `bad-enum Verification = '—'` against a correctly-formed row."""
        lint = load("perry_lint", PERRY_HOME / "bin" / "perry-lint")
        found = lint.tables("\n".join([
            T.render_row(HEADER), "|" + "---|" * len(HEADER), self.ROW]))
        self.assertEqual(len(found), 1)
        header, rows = found[0]
        self.assertEqual(len(rows[0]), len(header))
        self.assertEqual(rows[0], T.split_row(self.ROW))

    def test_no_reader_carries_its_own_splitter(self):
        """The category, not the two instances that were found. A reader with
        its own `strip("|").split("|")` does not know about `\\|`, and the
        escape reaching one implementation out of eleven is what this whole
        module is about."""
        offenders = []
        for rel in ("viewer/parsers.py", "bin/perry-lint", "bin/perry-task",
                    "bin/perry-goals", "bin/perry-state", "bin/perry-diagnose",
                    "bin/perry-decide", "bin/perry-conform"):
            path = PERRY_HOME / rel
            if not path.exists():
                continue
            for n, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
                if 'strip("|").split("|")' in line:
                    offenders.append(f"{rel}:{n}")
        self.assertEqual(offenders, [],
                         "these read rows without honouring `\\|`; "
                         "use viewer/tables.py § split_row")


class TestARaggedRowIsAFinding(unittest.TestCase):
    """Guard 3 — the check that would have caught the destroyed rows.

    The fixture is deliberately NOT built by `render_row`: the writer can no
    longer produce a ragged row, so a fixture it generates could never exercise
    this. The rows below are written by hand, which is what Perry's own board
    was.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "perry").mkdir()
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Config\n\nState root: perry/\n", encoding="utf-8")
        self.addCleanup(self.tmp.cleanup)

    def lint(self, rows: list[str]) -> list[str]:
        (self.root / "perry" / "BOARD.md").write_text(board_with(rows),
                                                      encoding="utf-8")
        env = dict(os.environ, PERRY_HOME=str(PERRY_HOME))
        out = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-lint"),
             "--root", str(self.root)],
            capture_output=True, text=True, env=env)
        return [ln for ln in (out.stdout + out.stderr).split("\n")
                if "ragged-row" in ln]

    def test_a_short_row_is_reported(self):
        """Two of seven columns missing. Before this check `perry-lint`
        reported `✓ clean` — reproduced on a copy of Perry's own board."""
        found = self.lint(["| TASK-001 | t | o | not_started | do the thing"])
        self.assertTrue(found, "a row missing two of seven columns linted clean")
        self.assertIn("TASK-001", found[0])
        self.assertIn("read as empty", found[0])

    def test_a_long_row_is_reported_too(self):
        """The other direction, and the one that shifts values into the wrong
        columns rather than merely losing them. A check written only for the
        case that bit would be the mistake this module documents."""
        found = self.lint(
            ["| TASK-001 | t | o | not_started | a | b | — | V2 |"])
        self.assertTrue(found, "a row with an extra cell linted clean")
        self.assertIn("shifted", found[0])

    def test_a_well_formed_row_is_not(self):
        self.assertEqual(
            self.lint([T.render_row(["TASK-001", "t", "o", "not_started",
                                     "do it", "—", "V2"])]), [])

    def test_a_row_whose_cell_holds_an_escaped_pipe_is_not(self):
        """The regression the two guards share. This row is seven cells to the
        writer and was eight to the linter, so before the splitter was unified
        it would be reported as ragged — a false accusation against a row
        Perry wrote itself."""
        self.assertEqual(
            self.lint([T.render_row(["TASK-001", "t", "o", "not_started",
                                     "quotes: | ID | Risk |", "—", "V2"])]), [])

    def test_a_table_whose_columns_perry_does_not_recognize_is_still_checked(self):
        """Why the check sits ABOVE the missing-columns branch.

        That branch bails out with `continue`, so anything after it only ever
        runs on tables Perry already understands. Comparing a row's width to
        its header's needs no interpretation of what the columns mean — and a
        table with headers Perry does not know is exactly what a project
        arriving from outside Perry has, which is the case migration exists
        for."""
        text = board_with([]).replace(
            T.render_row(HEADER) + "\n" + "|" + "---|" * len(HEADER),
            "| ID | 事项 | 负责人 |\n|---|---|---|\n| X-1 | a | b |\n| X-2 | a |",
            1)
        (self.root / "perry" / "BOARD.md").write_text(text, encoding="utf-8")
        env = dict(os.environ, PERRY_HOME=str(PERRY_HOME))
        out = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-lint"),
             "--root", str(self.root)], capture_output=True, text=True, env=env)
        blob = out.stdout + out.stderr
        self.assertIn("ragged-row", blob)
        self.assertIn("X-2", blob)

    def test_a_blank_spacer_row_is_not(self):
        """`|  |  |  |  |  |  |` is how every template ships an empty table,
        and `## Cadence` carries one on every real board. Reporting it would
        make the finding fire on Perry's own bootstrap output."""
        self.assertEqual(self.lint(["|  |  |  |"]), [])


if __name__ == "__main__":
    unittest.main()
