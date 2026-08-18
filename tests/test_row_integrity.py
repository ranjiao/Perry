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
import re

import viewer.tables as T
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

    #: `viewer/tables.py` is the one implementation and is exempt by name.
    #: Everything else in `bin/` and `viewer/` is DISCOVERED, not listed.
    EXEMPT = {"viewer/tables.py"}

    #: The read half and the write half of the same category.
    SPLIT_RE = re.compile(r"\.split\((['\"])\|\1\)")
    #: An f-string literal that starts a row and interpolates a value:
    #: `f"| {a} | {b} |"`. That is the shape that carried the defect, and it is
    #: the shape grep can tell apart.
    #:
    #: **What this cannot see, said rather than implied:** a row assembled with
    #: `" | ".join(cells)` is indistinguishable by grep from a regex
    #: alternation (`"|".join(re.escape(n) …)`) and from a separator row
    #: (`"|".join(["---"] * n)`), both of which are correct and common here. A
    #: first version flagged all three and reported 14 offenders of which 11
    #: were fine — a guard that cries wolf is one people add exemptions to
    #: until it means nothing. The join form is covered instead by the
    #: `ragged-row` lint finding, which judges the file rather than the source.
    #:
    #: **Round 3 widened it.** The previous pattern required `{` immediately
    #: after the opening `|`, so `f"| TASK-{n} | …"` — a literal first cell,
    #: which is how half the real rows are written — walked straight past. A
    #: reviewer planted exactly that and it stayed green. It now matches an
    #: f-string that opens a row and interpolates *anywhere* in it.
    HAND_ROW_RE = re.compile(r"""f['"]\s*\|(?=[^'"\n]*\{)""")

    def _tools(self):
        """Every shipped tool, globbed.

        The previous version carried a hardcoded list of eight files, so a
        reviewer added `bin/perry-newreader` with the exact defect and the
        guard stayed green. **A guard that cannot see a new file is a guard
        against the files that already had the bug** — which is the
        instance-shaped guard this project keeps finding, written into the test
        that exists to prevent it.
        """
        #: **Round 3: it could not see a subdirectory.** `iterdir()` plus
        #: `is_file()` skips directories outright and `glob("*.py")` does not
        #: descend, so a reviewer planted nine defective files and **all nine
        #: stayed green** — among them `bin/lib/rows.py` carrying both defects
        #: verbatim. `bin/lib/` is the directory TASK-065 exists to create and
        #: that this task's own criteria file names by path, so the blind spot
        #: was aimed squarely at the code that has not been written yet.
        #:
        #: Round 2 found this guard instance-shaped one level up and the fix
        #: replaced a hardcoded list with a flat glob. This is the same hole
        #: one level down. **Three rounds, one category** — so it now walks the
        #: tree rather than two directories, and the directories it skips are
        #: named with a reason rather than assumed.
        out = []
        for d in ("bin", "viewer"):
            out += [p for p in sorted((PERRY_HOME / d).rglob("*"))
                    if p.is_file()
                    and not p.name.endswith((".md", ".json", ".pyc"))
                    and "__pycache__" not in p.parts]
        return [p for p in out
                if p.relative_to(PERRY_HOME).as_posix() not in self.EXEMPT]

    @staticmethod
    def _code_lines(path):
        """Non-comment lines. A comment quoting the defect is not the defect —
        this module's own prose names both spellings repeatedly."""
        for n, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            if not line.lstrip().startswith("#"):
                yield n, line

    def test_no_tool_splits_a_row_on_a_raw_pipe(self):
        """The READ half. Any split on a bare `|` misses `\\|`, and the escape
        reaching one implementation out of eleven is what this module is about.
        Spelling-independent: `strip("|").split("|")` is the one that bit and
        not the only way to write it."""
        offenders = [f"{p.relative_to(PERRY_HOME).as_posix()}:{n}"
                     for p in self._tools()
                     for n, line in self._code_lines(p)
                     if self.SPLIT_RE.search(line)]
        self.assertEqual(offenders, [],
                         "these read a row without honouring the escape; "
                         "use viewer/tables.py split_row")

    def test_no_tool_writes_a_row_by_hand(self):
        """The WRITE half, which the previous guard did not have at all.

        `bin/perry-decide` built `DECISIONS.md` rows with an f-string, so a
        title containing a pipe produced a six-cell row against a five-cell
        header — `Type` read the tail of the title — and a line break broke the
        file silently. **Perry's own writer produced rows Perry's own linter
        reports as `ragged-row`.** A reviewer found it; this guard did not,
        because it only looked at readers.
        """
        offenders = [f"{p.relative_to(PERRY_HOME).as_posix()}:{n}"
                     for p in self._tools()
                     for n, line in self._code_lines(p)
                     if self.HAND_ROW_RE.search(line)]
        self.assertEqual(offenders, [],
                         "these build a table row by hand; use "
                         "viewer/tables.py render_row, which escapes the "
                         "delimiter and refuses a value a row cannot carry")

    def test_the_guard_sees_a_file_that_did_not_exist_when_it_was_written(self):
        """The property the hardcoded list did not have, written as a real file
        under `bin/` because that is how the blindness was demonstrated."""
        probe = PERRY_HOME / "bin" / "perry-guardprobe"
        probe.write_text('cells = [c for c in line.strip("|").split("|")]\n',
                         encoding="utf-8")
        try:
            found = [p for p in self._tools() if p.name == "perry-guardprobe"]
            self.assertTrue(found, "a new tool is invisible to this guard")
            self.assertTrue(
                [n for n, line in self._code_lines(found[0])
                 if self.SPLIT_RE.search(line)],
                "the guard did not flag a planted defect")
        finally:
            probe.unlink()


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



class TestAppendCellObeysTheSameRule(unittest.TestCase):
    """`append_cell` was the third writer in the canonical module, and it was
    the one still collapsing what the other two refuse.

    `viewer/tables.py § check_cell`'s docstring indicts `.replace("\\n", " ")`
    by name — it was written when that exact line was found in
    `bin/perry-goals` — and `append_cell` sat four lines below doing it anyway.
    The round that fixed `splice_cell` left its untouched sibling: a fix aimed
    at the instance rather than the category, in the module that exists to be
    the category.

    Two independent reviewers found it the same night. Deleting the line left
    all 1310 tests green, so nothing covered it either.
    """

    def test_a_line_break_is_refused_not_collapsed(self):
        with self.assertRaises(T.UnrenderableCell):
            T.append_cell("| a |", "x\n\ny")

    def test_a_carriage_return_too(self):
        with self.assertRaises(T.UnrenderableCell):
            T.append_cell("| a |", "x\ry")

    def test_a_pipe_is_stored_the_same_way_on_both_branches(self):
        """The fallback branch handed `render_row` an already-escaped value, so
        `x|y` became `x\\\\|y` and read back as `x\\|y`. The same value written
        two ways depending on whether the row happened to end in a pipe."""
        with_pipe = T.append_cell("| a |", "x|y")
        without = T.append_cell("| a ", "x|y")
        self.assertEqual(T.split_row(with_pipe)[-1], "x|y")
        self.assertEqual(T.split_row(without)[-1], "x|y")

    def test_an_empty_value_still_widens_the_row(self):
        """Widening is the reason this function exists; a blank new cell is the
        normal case and must not be mistaken for a refusal."""
        self.assertEqual(T.split_row(T.append_cell("| a |", "")), ["a", ""])

class TestRaggedRowPointsAtTheRow(unittest.TestCase):
    """The one finding whose whole job is "go look at this line".

    It reported the **section heading's** line: a row at `BOARD.md:21` came
    back as `:15`. On a board with forty rows under one heading that is not a
    small imprecision — it is the difference between a pointer and a gesture,
    in the finding a person reaches for when the board is already broken.

    Two ragged rows at known, different lines, because **one sample cannot
    tell a constant offset from a coincidence** — the first attempt at this fix
    was verified with one and was still off by one.
    """

    def lint(self, board):
        import json, shutil, subprocess, sys, tempfile
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "perry").mkdir()
        (d / ".perry").mkdir()
        (d / ".perry" / "config.md").write_text("State root: perry\n")
        (d / "perry" / "BOARD.md").write_text(board)
        proc = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-lint"),
             "--root", str(d), "--json"], capture_output=True, text=True)
        return [f["line"] for f in json.loads(proc.stdout)["findings"]
                if f["rule"] == "ragged-row"]

    BOARD = ("# Board\n\n## P1\n\n"
             "| ID | Title | Owner | Status | Next action | Evidence | "
             "Verification |\n"
             "| --- | --- | --- | --- | --- | --- | --- |\n"
             "| TASK-001 | a | Claude | not_started | — | — |\n"
             "| TASK-002 | b | Claude | not_started | — | — | V2 |\n"
             "| TASK-003 | c | Claude | not_started | — | — |\n")

    def test_each_finding_names_its_own_row(self):
        self.assertEqual(self.lint(self.BOARD), [7, 9])

    def test_a_well_formed_board_reports_none(self):
        good = self.BOARD.replace("| — | — |\n", "| — | — | V2 |\n")
        self.assertEqual(self.lint(good), [])

    def test_the_two_table_readers_are_one_scanner(self):
        """`tables()` is a VIEW of `tables_with_lines()`, not a second scan.

        Checked by shape — the function body must be exactly one `return` —
        rather than by grepping for a call it should not contain.

        **The grep version was written first and a mutation walked past it.**
        It asserted `"split_row(s)" not in body`; planting a scanner that spells
        its loop variable `s2` left it green. That is the same
        spelling-not-shape defect this session had just fixed in TASK-050's
        guard, reproduced inside the test written to prevent it — which is
        exactly why the rule is "enumerate the category" and not "remember the
        lesson".
        """
        import ast
        src = (PERRY_HOME / "bin" / "perry-lint").read_text()
        fn = next(n for n in ast.walk(ast.parse(src))
                  if isinstance(n, ast.FunctionDef) and n.name == "tables")
        body = [n for n in fn.body if not (isinstance(n, ast.Expr)
                                           and isinstance(n.value, ast.Constant))]
        self.assertEqual(
            len(body), 1,
            f"`tables()` has {len(body)} statements; a view of "
            f"`tables_with_lines()` is one `return` and anything more is a "
            f"second scanner")
        self.assertIsInstance(body[0], ast.Return)
        called = {n.func.id for n in ast.walk(body[0])
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertIn("tables_with_lines", called)


if __name__ == "__main__":
    unittest.main()
