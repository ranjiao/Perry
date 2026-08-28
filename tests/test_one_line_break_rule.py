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


# ── the same rule, the other writer ───────────────────────────────────────

#: A `queue` track, because `## Commitments` is the spine of exactly the
#: `queue` and `pipeline` modes and `commit` refuses to create the section
#: without one. `main` is `project` so the fixture also holds a track that
#: cannot take a commitment.
GOALS_CONFIG = """# Perry configuration

- Document language: English
- Repo layout: single
- State root: .

## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| ops | queue | commitments | intake -> doing | — | 5d | weekly | V2 |
| main | project | okr | — | — | — | — | V2 |
"""

#: Schema-shaped, because the fixture is DECLARED rather than gate-exempt and
#: `perry-conform declare` refuses a file that does not match Perry's shape.
#: The `## Commitments` table starts empty and with `Discharged by` already
#: present, so no test here is also exercising a widening.
GOALS_OKR = """# OKR — fixture

## Mission

Ship it.

## Operating Principles

- One line, one cell.

## Anti-Goals

- not this

## Commitments

| Id | Track | Promise | To whom | Due | Status | Discharged by |
|---|---|---|---|---|---|---|

---

## v1: 2026-08-01

### Objective 1 — Refusals name the flag

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O1.1 | Unnamed refusals | unnamed = 0 | no | 2026-09-01 |

## Versioning log

- v1: 2026-08-01 — initial.
"""


def declare(root: pathlib.Path) -> None:
    """The fixture the reproduction uses: a project whose `OKR.md` is
    DECLARED, not one with the conformance gate switched off.

    An advisory gate prints `perry-goals: ⚠ conformance (advisory) — …` onto
    stderr, which is the stream a byte-exact refusal is read from — the
    assertion below would be pinning the gate's wording as well as the
    refusal's. Declaring is also what a real project does (ADR-004), so the
    refusal is being read in the state a user reads it in.
    """
    (root / ".perry").mkdir()
    (root / ".perry" / "config.md").write_text(GOALS_CONFIG)
    (root / "OKR.md").write_text(GOALS_OKR)
    d = subprocess.run(
        [sys.executable, str(ROOT / "bin" / "perry-conform"), "declare",
         "OKR.md", "--root", str(root)], capture_output=True, text=True)
    assert d.returncode == 0, d.stdout + d.stderr


class TestPerryGoalsRefusalNamesTheFlagToo(unittest.TestCase):
    """`bin/perry-goals`' half, which is where TASK-037 came back from twice.

    Its `check_due` docstring has stated the rule since the `By when` split —
    *"the refusal says so and names the flag, so a user is never guessing
    where their words go"* — and its whitespace refusal obeyed it while its
    line-break sibling, on the same tool and the same value, printed

        perry-goals: refused — was given 'a\\n\\nb', which contains a
        line break …

    with nothing at all in front of `was given`. Both prior rounds of this row
    failed on the same shape: the one refusal that had been quoted got fixed
    and its siblings kept the defect. So this asserts **every flag that
    reaches a cell**, from a table, not the one that was reported.
    """

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = pathlib.Path(self.dir.name)
        declare(self.root)
        self.assertEqual(0, self.goals(
            "commit", "--track", "ops", "--promise", "a promise",
            "--to", "a party", "--due", "3d").returncode)

    def goals(self, *argv):
        return subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-goals"), *argv,
             "--root", str(self.root)],
            capture_output=True, text=True)

    #: Every flag of `commit` whose value becomes a markdown cell, with a
    #: command that reaches that cell. Enumerated rather than sampled: the
    #: create path and the amend path are different code, and the two ways of
    #: filling `Discharged by` are different flags into one column.
    PATHS = {
        "--promise": ("commit", "--track", "ops", "--promise", "{v}",
                      "--to", "p", "--due", "3d"),
        "--to": ("commit", "--track", "ops", "--promise", "p",
                 "--to", "{v}", "--due", "3d"),
        "--by-when-note": ("commit", "--track", "ops", "--promise", "p",
                           "--to", "p", "--due", "3d",
                           "--by-when-note", "{v}"),
        "--discharged-by": ("commit", "--track", "ops", "--promise", "p",
                            "--to", "p", "--due", "3d",
                            "--discharged-by", "{v}"),
        "--promise (amend)": ("commit", "--id", "ops/1", "--promise", "{v}"),
        "--to (amend)": ("commit", "--id", "ops/1", "--to", "{v}"),
        "--by-when-note (amend)": ("commit", "--id", "ops/1",
                                   "--by-when-note", "{v}"),
        "--discharged-by (amend)": ("commit", "--id", "ops/1",
                                    "--discharged-by", "{v}"),
        "--discharged-by (close)": ("commit", "--close", "ops/1",
                                    "--discharged-by", "{v}"),
        "--reason (miss)": ("commit", "--miss", "ops/1", "--reason", "{v}"),
    }

    def test_every_flag_that_reaches_a_cell_is_named_in_its_own_refusal(self):
        for label, argv in self.PATHS.items():
            flag = label.split(" ")[0]
            with self.subTest(path=label):
                r = self.goals(*[a.format(v="a\n\nb") for a in argv])
                self.assertEqual(1, r.returncode, r.stdout + r.stderr)
                self.assertIn("contains a line break", r.stderr)
                self.assertTrue(
                    r.stderr.startswith(f"perry-goals: refused — {flag} was "
                                        f"given "),
                    f"{label} does not name its flag: {r.stderr!r}")

    def test_two_flags_do_not_produce_the_same_message(self):
        """The property the count is for. `index` is a column position, so
        before this every one of the ten read identically."""
        seen = {}
        for label, argv in self.PATHS.items():
            seen[label] = self.goals(
                *[a.format(v="a\nb") for a in argv]).stderr
        for label, text in seen.items():
            flag = label.split(" ")[0]
            for other in set(self.PATHS) - {label}:
                other_flag = other.split(" ")[0]
                if other_flag == flag:
                    continue
                self.assertNotIn(
                    f"{other_flag} was given", text,
                    f"{label}'s refusal names {other_flag}")

    def test_the_refusal_is_byte_exact(self):
        """The reproduction from the spec, as bytes. The old text began
        `refused — was given`, with the flag simply missing."""
        r = self.goals("commit", "--track", "ops", "--promise", "a\n\nb",
                       "--to", "p", "--due", "3d")
        self.assertEqual(
            "perry-goals: refused — --promise was given 'a\\n\\nb', which "
            "contains a line break — a markdown table row is one line. "
            "A register cell is one line of a markdown table.\n",
            r.stderr)

    def test_the_refusal_reaches_json_stdout(self):
        """The handler used to sit at module level, where there is no `args`
        and so no way to answer `--json`: rc 1, and stdout empty."""
        r = self.goals("commit", "--track", "ops", "--promise", "a\n\nb",
                       "--to", "p", "--due", "3d", "--json")
        self.assertEqual(1, r.returncode)
        self.assertEqual(
            "--promise was given 'a\\n\\nb', which contains a line break — "
            "a markdown table row is one line. A register cell is one line "
            "of a markdown table.",
            json.loads(r.stdout)["refused"])

    def test_the_whitespace_refusal_is_unchanged(self):
        """**The other side of the fix.** This refusal already obeyed the
        rule; a change here would mean the fix went in the wrong place."""
        r = self.goals("commit", "--id", "ops/1", "--promise", "   ")
        self.assertEqual(
            "perry-goals: refused — --promise was given only whitespace, "
            "which would erase the Promise cell rather than change it. "
            "Pass the new text, or use --close / --miss to retire the row. "
            "Nothing was written\n",
            r.stderr)

    def test_nothing_was_written(self):
        """A refusal that had already appended the row would name the flag
        and still have destroyed the table."""
        before = (self.root / "OKR.md").read_text()
        self.goals("commit", "--track", "ops", "--promise", "a\n\nb",
                   "--to", "p", "--due", "3d")
        self.goals("commit", "--id", "ops/1", "--promise", "a\n\nb")
        self.assertEqual(before, (self.root / "OKR.md").read_text())


class TestTheIdThatIsNotARowNamesItsFlagToo(unittest.TestCase):
    """`--id`, `--close` and `--miss` all take a value, so a mistyped command
    feeds the NEXT flag to the id: `commit --id ops/1 --close
    --discharged-by x` refused with `'--discharged-by' is not a row`, naming
    neither the flag that swallowed the value nor the one left without one.
    """

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = pathlib.Path(self.dir.name)
        declare(self.root)

    def goals(self, *argv):
        return subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-goals"), *argv,
             "--root", str(self.root)],
            capture_output=True, text=True)

    def test_each_id_carrying_flag_is_named(self):
        for flag in ("--id", "--close", "--miss"):
            with self.subTest(flag=flag):
                r = self.goals("commit", flag, "nope/9", "--promise", "x",
                               "--reason", "x", "--discharged-by", "x")
                self.assertEqual(1, r.returncode)
                self.assertIn(f"{flag} was given 'nope/9', which is not a row",
                              r.stderr)

    def test_the_track_names_its_flag(self):
        """Kept apart from `--due` below so that one revert reddens one
        refusal — the two are different functions and different fixes."""
        r = self.goals("commit", "--track", "nope", "--promise", "p",
                       "--to", "p", "--due", "3d")
        self.assertIn("--track was given 'nope', which is not declared",
                      r.stderr)

    def test_the_due_names_its_flag(self):
        r = self.goals("commit", "--track", "ops", "--promise", "p",
                       "--to", "p", "--due", "soon-ish")
        self.assertIn("--due was given 'soon-ish'", r.stderr)
        self.assertIn("`Due` is typed", r.stderr)

    def test_a_track_read_out_of_the_file_names_no_flag(self):
        """The other half of the same rule. `--migrate` and the amend path
        pass the row's OWN `Track` cell to `track_named`, and naming `--track`
        there would send the user to fix a flag they never passed."""
        (self.root / "OKR.md").write_text(
            (self.root / "OKR.md").read_text().replace(
                "|---|---|---|---|---|---|---|",
                "|---|---|---|---|---|---|---|\n| ops/9 | gone | p | p "
                "| 2026-09-01 | active |  |"))
        r = self.goals("commit", "--id", "ops/9", "--due", "2027-01-01",
                       "--accept-hand-edit")
        self.assertEqual(1, r.returncode, r.stdout + r.stderr)
        self.assertIn("track 'gone' is not declared", r.stderr)
        self.assertNotIn("--track", r.stderr)


if __name__ == "__main__":
    unittest.main()
