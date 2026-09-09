"""DESIGN-016 phase A — what a `bin/` tool does with the argument vector it is handed.

Four claims, each measured as broken on `02a2b74c` before it was written here:

- **`--root` beats `$PERRY_PROJECT`** in every project-scoped tool.
  `bin/README.md § Which project?` publishes that order and ADR-002 is why;
  `perry_md_store`, `perry-tasks` and `perry-config` read the environment
  AFTER the flag, so a caller who named a project got a different one. Two of
  those three write.
- **An undeclared token is refused**, exit 2, rather than ignored. `--wrte`
  used to render, write nothing, and exit 0 — the caller was told the run
  succeeded. `perry-diagnose` swallowed a bad `--max-files` the same way and
  kept the default cap.
- **`-h` prints from any position and runs nothing.** `perry-tasks render
  --write --help` used to run the render.
- **A write that cannot place every stored record refuses**, and a refusal
  reaches the caller as one line rather than as a traceback.

The population is the four tools DESIGN-016 § 1.1 and § 1.5 measured, plus
`perry-state` and `perry-task` as the controls that were already right.
`tests/test_project_root_resolution.py` owns the resolver itself; this module
owns what the tools do with it, which is the half its docstring says it never
covered.

Run: python3 tests/parallel -j 4 test_bin_argument_contract
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(os.environ.get("PERRY_HOME")
                  or Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(PERRY_HOME / "tests"))

import config_store  # noqa: E402
from task_writer_support import Project  # noqa: E402

BIN = PERRY_HOME / "bin"

#: `tool, argv that reaches a real code path`. `perry-okr` is `perry_md_store`
#: under its own name, and `perry-config` is the settings editor ADR-019 left.
READS = (
    ("perry-tasks", ("build",)),
    ("perry-okr", ("build",)),
    ("perry-config", ("show",)),
    ("perry-diagnose", ()),
    ("perry-state", ()),
    ("perry-task", ("list",)),
)


def run(tool: str, *argv: str, env: dict | None = None) -> subprocess.CompletedProcess:
    e = dict(os.environ)
    e.pop("PERRY_PROJECT", None)
    e.update(env or {})
    return subprocess.run([sys.executable, str(BIN / tool), *argv],
                          capture_output=True, text=True, env=e)


class TestTheFlagBeatsTheEnvironment(unittest.TestCase):
    """`--root <a>` with `$PERRY_PROJECT=<b>` answers about `<a>`, everywhere."""

    #: Written into every corner of `other` that a tool can print, so a tool
    #: that answers about the wrong project says so in its own output.
    MARK = "ONLY-IN-THE-OTHER-PROJECT"

    def setUp(self):
        self.named = Project()
        self.named.run("add", "--title", "the project the caller named")
        self.other = Project()
        for _ in range(3):
            self.other.run("add", "--title", f"a row {self.MARK}")
        run("perry-config", "set", "Chat language", self.MARK,
            "--root", str(self.other.root))

    def _answers_about_the_named_project(self, tool: str, argv: tuple[str, ...],
                                         out: subprocess.CompletedProcess):
        """**Absence of the other path is not enough** — a V4 review reverted
        the resolver to environment-first and three of these six subtests still
        passed, because a tool that prints no path cannot fail that way. Each
        tool is now asked for a VALUE that differs between the two projects."""
        blob = out.stdout + out.stderr
        self.assertNotIn(str(self.other.root), blob,
                         f"{tool} {' '.join(argv)} reported on the project "
                         f"named by $PERRY_PROJECT, not by --root")
        self.assertNotIn(self.MARK, blob,
                         f"{tool} {' '.join(argv)} carried a value that only "
                         f"exists in the project named by $PERRY_PROJECT")

    def test_every_project_scoped_tool_prefers_the_flag(self):
        for tool, argv in READS:
            with self.subTest(tool=tool):
                out = run(tool, *argv, "--root", str(self.named.root),
                          env={"PERRY_PROJECT": str(self.other.root)})
                self._answers_about_the_named_project(tool, argv, out)

    def test_the_store_tools_count_the_named_projects_records(self):
        """The measurement DESIGN-016 § 1.1 opened with, as an assertion.

        `perry-tasks build --root <one-row project>` reported the OTHER
        project's record count — 352 of them — because `$PERRY_PROJECT` won.
        """
        out = run("perry-tasks", "build", "--root", str(self.named.root),
                  env={"PERRY_PROJECT": str(self.other.root)})
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout)["records"], 1, out.stdout)

    def test_the_environment_still_wins_when_no_flag_is_given(self):
        """The order is a precedence, not a demotion: step 2 is still step 2."""
        out = run("perry-tasks", "build",
                  env={"PERRY_PROJECT": str(self.other.root)})
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout)["records"], 3, out.stdout)


class TestAnUndeclaredTokenIsRefused(unittest.TestCase):

    def setUp(self):
        self.p = Project()

    def test_every_tool_refuses_and_says_so(self):
        for tool, argv in READS:
            with self.subTest(tool=tool):
                out = run(tool, *argv, "--root", str(self.p.root), "--xyzzy")
                self.assertEqual(out.returncode, 2,
                                 f"{tool} accepted --xyzzy:\n"
                                 + out.stdout[:400] + out.stderr[:400])
                self.assertIn("--xyzzy", out.stderr)

    def test_a_misspelled_write_flag_does_not_report_success(self):
        """`--wrte` was a silent no-op that exited 0 (DESIGN-016 § 1.1)."""
        out = run("perry-tasks", "render", "--root", str(self.p.root), "--wrte")
        self.assertEqual(out.returncode, 2, out.stdout[:400] + out.stderr[:400])

    def test_a_flag_that_never_existed_is_not_a_quiet_success(self):
        """`render --byte-compare` rendered to stdout and exited 0, so a test
        asserting rc 0 on it was asserting nothing (`test_last_updated_header`
        held one)."""
        out = run("perry-tasks", "render", "--root", str(self.p.root),
                  "--byte-compare")
        self.assertEqual(out.returncode, 2, out.stdout[:400] + out.stderr[:400])

    def test_a_value_flag_with_no_value_is_refused(self):
        out = run("perry-tasks", "build", "--root")
        self.assertEqual(out.returncode, 2, out.stdout + out.stderr)
        self.assertIn("--root", out.stderr)

    def test_diagnose_refuses_a_max_files_it_cannot_read(self):
        """It used to `pass` on the ValueError and keep the default 20,000 —
        a cap the caller believes they set."""
        out = run("perry-diagnose", "--root", str(self.p.root),
                  "--max-files", "twenty")
        self.assertEqual(out.returncode, 2, out.stdout[:300] + out.stderr[:300])
        self.assertIn("--max-files", out.stderr)


class TestHelpPrintsAndRunsNothing(unittest.TestCase):

    def setUp(self):
        self.p = Project()

    def test_help_after_a_write_flag_does_not_write(self):
        board = self.p.root / "BOARD.md"
        before = board.read_bytes()
        out = run("perry-tasks", "render", "--root", str(self.p.root),
                  "--write", "--help")
        self.assertEqual(out.returncode, 0, out.stderr)
        # Since C1 a named subcommand gets ITS usage rather than the tool's
        # whole document — goal 8, and it is generated from the declaration.
        self.assertIn("perry-tasks render", out.stdout)
        self.assertNotIn("perry-tasks build", out.stdout,
                         "the whole tool's usage came back for one subcommand")
        self.assertEqual(board.read_bytes(), before,
                         "`--help` ran the render it was asking about")

    def test_help_is_the_answer_from_any_position(self):
        for argv in (("--help",), ("-h",), ("render", "--help"),
                     ("render", "--root", str(self.p.root), "--help")):
            with self.subTest(argv=argv):
                out = run("perry-tasks", *argv)
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assertTrue(out.stdout.strip(), "help printed nothing")


class TestARenderThatCannotRestoreRefuses(unittest.TestCase):
    """DESIGN-016 § 1.5 — the documented recovery path, made honest."""

    def setUp(self):
        self.p = Project()
        for n in range(3):
            self.p.run("add", "--title", f"a row to lose number {n}")
        self.board = self.p.root / "BOARD.md"

    def _delete_the_task_rows(self) -> int:
        lines = self.board.read_text().split("\n")
        kept = [l for l in lines if not l.startswith("| TASK-")]
        self.board.write_text("\n".join(kept))
        return len(lines) - len(kept)

    def test_it_refuses_and_names_what_it_cannot_place(self):
        lost = self._delete_the_task_rows()
        self.assertEqual(lost, 3, "control: three rows were deleted")
        out = run("perry-tasks", "render", "--root", str(self.p.root), "--write")
        self.assertEqual(out.returncode, 1,
                         "the recovery command reported success:\n" + out.stdout)
        self.assertIn("no line in it to render into", out.stderr)
        self.assertIn("TASK-", out.stderr)
        self.assertNotIn("| TASK-", self.board.read_text(),
                         "a refused write still changed the board")

    def test_the_detection_layer_still_reports_it(self):
        """`diff` was always right; only the writer lied. Both stay true.

        Note what `diff` does NOT say: its exit code is 0 here, because the
        render of a board with the rows deleted IS byte-identical to that
        board — the render dropped them too. `identical: true` meaning "the
        file reproduced itself" is TASK-182, and it is why the refusal reads
        `rows_not_on_board` rather than the exit code.
        """
        self._delete_the_task_rows()
        out = run("perry-tasks", "diff", "--root", str(self.p.root))
        self.assertEqual(len(json.loads(out.stdout)["rows_not_on_board"]), 3)

    def test_a_clean_write_says_what_it_changed(self):
        """The success line counted RECORDS READ, so a write and a no-op
        printed the same sentence (TASK-253 saw this from the other side)."""
        out = run("perry-tasks", "render", "--root", str(self.p.root),
                  "--write", "--json")
        self.assertEqual(out.returncode, 0, out.stderr)
        payload = json.loads(out.stdout)
        self.assertTrue(payload["wrote"])
        self.assertEqual(payload["lines_changed"], 0,
                         "an unchanged board reported changed lines")
        self.assertGreater(payload["lines_unchanged"], 0)

    def test_dry_run_touches_nothing(self):
        before = self.board.read_bytes()
        out = run("perry-tasks", "render", "--root", str(self.p.root),
                  "--write", "--dry-run", "--json")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertFalse(json.loads(out.stdout)["wrote"])
        self.assertEqual(self.board.read_bytes(), before)


class TheOtherStoreFamilyToolRefusesToo(unittest.TestCase):
    """A5 has TWO implementations and only one was tested.

    `perry-tasks` has `stranded_after_render`; `perry_md_store` — which is
    `perry-okr` and anything else built on a `Doc` — has its own copy. A V4
    review deleted the second one outright and the entire suite stayed at its
    known-red baseline, while `perry-okr render --write` on a copy with 38 KR
    rows deleted reported success and restored none of them.
    """

    OKR = ("# OKR\n\n## Objective 1 ship\n\n"
           "| **KR** | Target | Current |\n|---|---|---|\n"
           "| KR-1 | 3 | 1 |\n\n"
           "## Commitments\n\n| ID | Promise | **Due** |\n|---|---|---|\n"
           "| C-1 | do it | 2026-02-01 |\n"
           "| C-2 | do the other thing | 2026-03-01 |\n")

    def setUp(self):
        self.p = Project()
        self.okr = self.p.root / "OKR.md"
        self.okr.write_text(self.OKR)
        self.assertEqual(
            run("perry-okr", "write", "--root", str(self.p.root),
                "--from-file").returncode, 0)

    def test_it_refuses_when_a_record_has_no_line_left(self):
        self.okr.write_text(self.OKR.replace(
            "| C-2 | do the other thing | 2026-03-01 |\n", ""))
        shrunk = self.okr.read_bytes()
        out = run("perry-okr", "render", "--root", str(self.p.root), "--write")
        self.assertEqual(out.returncode, 1,
                         "the OKR store's recovery path reported success:\n"
                         + out.stdout)
        self.assertIn("no line in it to render into", out.stderr)
        self.assertEqual(self.okr.read_bytes(), shrunk,
                         "a refused write still changed the file")

    def test_the_control_is_that_an_intact_file_still_renders(self):
        out = run("perry-okr", "render", "--root", str(self.p.root), "--write")
        self.assertEqual(out.returncode, 0, out.stderr)


class TestARefusalIsOneLine(unittest.TestCase):
    """DESIGN-016 A6, goal 10 — `bin/README.md` says exit 1 prints the reason."""

    def test_a_missing_board_is_not_a_traceback(self):
        p = Project()
        p.run("add", "--title", "a row so the store has something in it")
        (p.root / "BOARD.md").unlink()
        out = run("perry-tasks", "render", "--root", str(p.root), "--write")
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        self.assertNotIn("Traceback", out.stderr)
        self.assertIn("refused", out.stderr)

    def test_the_lane_tool_and_the_store_tool_answer_alike(self):
        """`perry-task` printed one line for this condition all along; the two
        differed only in whether the `except` covered the call."""
        p = Project()
        p.run("add", "--title", "a row so the store has something in it")
        (p.root / "BOARD.md").unlink()
        lane = run("perry-task", "list", "--root", str(p.root))
        store = run("perry-tasks", "render", "--root", str(p.root), "--write")
        for out in (lane, store):
            self.assertNotIn("Traceback", out.stderr)


class TestTheWritersTakeDryRunAndJson(unittest.TestCase):
    """DESIGN-016 A3 — `bin/README.md:74` promised both on every writer."""

    OKR = ("# OKR\n\n## Objective 1 ship\n\n"
           "| **KR** | Target | Current |\n|---|---|---|\n"
           "| KR-1 | 3 | 1 |\n\n"
           "## Commitments\n\n| ID | Promise | **Due** |\n|---|---|---|\n"
           "| C-1 | do it | 2026-02-01 |\n")

    def setUp(self):
        self.p = Project()
        self.okr = self.p.root / "OKR.md"
        self.okr.write_text(self.OKR)
        imported = run("perry-okr", "write", "--root", str(self.p.root),
                       "--from-file")
        self.assertEqual(imported.returncode, 0, imported.stderr)

    def test_render_dry_run_writes_nothing_and_says_so(self):
        before = self.okr.read_bytes()
        out = run("perry-okr", "render", "--root", str(self.p.root), "--write",
                  "--dry-run", "--json")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertFalse(json.loads(out.stdout)["wrote"])
        self.assertEqual(self.okr.read_bytes(), before)

    def test_write_dry_run_leaves_the_store_alone(self):
        store = self.p.root / "okr.jsonl"
        before = store.read_bytes()
        out = run("perry-okr", "write", "--root", str(self.p.root),
                  "--from-file", "--dry-run", "--json")
        self.assertEqual(out.returncode, 0, out.stderr)
        payload = json.loads(out.stdout)
        self.assertFalse(payload["wrote"])
        self.assertGreater(payload["records"], 0)
        self.assertEqual(store.read_bytes(), before)

    def test_an_ordinary_render_still_writes(self):
        """The control: `--dry-run` is a mode, not a disabling."""
        # The commitment is what this minimal document actually stores — the
        # KR table needs the objective shape a real `OKR.md` carries, and the
        # store says so: one record after the import.
        self.okr.write_text(self.OKR.replace("| C-1 | do it |",
                                             "| C-1 | edited by hand |"))
        out = run("perry-okr", "render", "--root", str(self.p.root), "--write",
                  "--json")
        self.assertEqual(out.returncode, 0, out.stderr)
        payload = json.loads(out.stdout)
        self.assertTrue(payload["wrote"])
        self.assertGreater(payload["lines_changed"], 0)
        self.assertIn("| C-1 | do it |", self.okr.read_text(),
                      "the store's value did not come back")


class TestEveryWriterHonoursDryRun(unittest.TestCase):
    """Goal 4, asked of each writer rather than of the family.

    `perry-tasks` ACCEPTED `--dry-run` and wrote anyway — TASK-253 filed that
    on 2026-09-02, and phase A of DESIGN-016 made the flag legal without making
    it do anything, which is the accepted-and-dropped shape the design exists
    to remove. Measured 2026-09-09 before the fix: `perry-tasks write
    --from-board --dry-run` replaced a 404-record store and printed `wrote`.
    """

    #: `(argv, the file it would have written)`.
    WRITES = (
        (("perry-tasks", "write", "--from-board"), "tasks.jsonl"),
        (("perry-tasks", "risks-write", "--from-board"), "risks.jsonl"),
        (("perry-tasks", "intake-write", "--from-board"), "intake.jsonl"),
        (("perry-tasks", "asks-write", "--from-board"), "asks.jsonl"),
        (("perry-tasks", "render", "--write"), "BOARD.md"),
        (("perry-tasks", "risks-render", "--write"), "BOARD.md"),
        (("perry-tasks", "intake-render", "--write"), "BOARD.md"),
        (("perry-tasks", "asks-render", "--write"), "BOARD.md"),
    )

    def setUp(self):
        self.p = Project()
        self.p.run("add", "--title", "a row so every store has something")
        for argv, _target in self.WRITES:
            run(*argv, "--root", str(self.p.root))  # mint the stores

    def test_dry_run_changes_no_bytes_anywhere(self):
        """A register the fixture board has no section for refuses with exit 2
        — that is the storeless refusal, not a dry-run failure, and the bytes
        claim is asked of it all the same. `reached` is the control: if every
        command in the table refused, the loop would prove nothing."""
        reached = 0
        for argv, target in self.WRITES:
            path = self.p.root / target
            if not path.exists():
                continue
            with self.subTest(command=" ".join(argv[1:])):
                before = path.read_bytes()
                out = run(*argv, "--root", str(self.p.root), "--dry-run")
                self.assertEqual(path.read_bytes(), before,
                                 f"{' '.join(argv[1:])} --dry-run wrote to "
                                 f"{target}")
                if out.returncode == 0:
                    reached += 1
        self.assertGreaterEqual(reached, 2,
                                "every writer refused, so nothing above "
                                "exercised a dry run that had work to do")

    def test_the_control_is_that_the_same_command_does_write(self):
        """Without this, a tool that refused everything would pass above."""
        board = self.p.root / "BOARD.md"
        self.p.run("status", "TASK-001", "--status", "in_progress")
        (self.p.root / "tasks.jsonl").write_text(
            (self.p.root / "tasks.jsonl").read_text().replace(
                '"in_progress"', '"blocked"'))
        out = run("perry-tasks", "render", "--write", "--root", str(self.p.root))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("blocked", board.read_text(),
                      "the control write did not land")


class TestAddWritesTheDesignEdge(unittest.TestCase):
    """DESIGN-016 A4 — `--design` was accepted by the parser and dropped."""

    def setUp(self):
        self.p = Project()
        (self.p.root / "design").mkdir(exist_ok=True)
        (self.p.root / "design" / "DESIGN-042-a-fixture.md").write_text(
            "# DESIGN-042: a fixture\n\n> Status: draft\n")

    def _record(self, title: str) -> dict:
        rows = [json.loads(l) for l
                in (self.p.root / "tasks.jsonl").read_text().split("\n")
                if l.strip()]
        return next(r for r in rows if r["title"] == title)

    def test_the_edge_lands_in_the_store(self):
        self.p.run("add", "--title", "a row that implements a design",
                   "--design", "DESIGN-042")
        self.assertEqual(
            self._record("a row that implements a design").get("design_refs"),
            ["DESIGN-042"],
            "`add --design` exited 0 and wrote no edge — the row had to be "
            "relinked afterwards, which is how this was found")

    def test_a_design_with_no_document_is_refused(self):
        """The same rule `design-link` enforces: an edge to a design that does
        not exist is a typo the hand-off count would read as implementation."""
        code, out = self.p.run("add", "--title", "a row citing a ghost",
                               "--design", "DESIGN-999")
        self.assertEqual(code, 1, out)
        self.assertIn("DESIGN-999", str(out))
        rows = (self.p.root / "tasks.jsonl").read_text()
        self.assertNotIn("a row citing a ghost", rows,
                         "a refused add still wrote the row")

    def test_a_row_opened_without_the_flag_keeps_its_shape(self):
        self.p.run("add", "--title", "a row that implements nothing")
        self.assertEqual(
            self._record("a row that implements nothing").get("design_refs"),
            [], "a row opened without --design gained an edge")


class TestListIsBounded(unittest.TestCase):
    """DESIGN-016 B2, goal 6 — no call returns more rows than a declared cap
    unless the caller asked for them.

    `perry-task list --json` on Perry's own repository is 538,134 bytes and
    `--all --json` is 1,683,852 — about 420k tokens, more than the context
    window of anything that reads it.
    """

    def setUp(self):
        self.p = Project()
        for n in range(6):
            self.p.run("add", "--title", f"a row to bound {n}")

    def _list(self, *argv):
        out = run("perry-task", "list", "--root", str(self.p.root), "--json",
                  *argv)
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout), out.stderr

    def test_the_bound_is_declared_even_when_it_changes_nothing(self):
        payload, _err = self._list()
        self.assertEqual(payload["bound"]["returned"],
                         payload["bound"]["total"])
        self.assertFalse(payload["bound"]["truncated"])
        self.assertTrue(payload["bound"]["default"])

    def test_a_smaller_limit_truncates_and_says_so_twice(self):
        payload, err = self._list("--limit", "2")
        self.assertEqual(len(payload["tasks"]), 2)
        self.assertEqual(payload["bound"]["total"], 6)
        self.assertTrue(payload["bound"]["truncated"])
        self.assertFalse(payload["bound"]["default"])
        self.assertIn("2 of 6", err, "the truncation was silent on stderr")

    def test_the_default_bound_is_what_the_constant_says(self):
        """The number itself, asserted. Raising `LIST_DEFAULT_LIMIT` to a
        billion — deleting contract 1.19's whole behavioural change — left the
        suite green, because every other case here builds six rows and passes
        at any default above six."""
        import inproc
        self.assertEqual(inproc.load("perry-task").LIST_DEFAULT_LIMIT, 200)
        payload, _err = self._list()
        self.assertEqual(payload["bound"]["limit"], 200)
        self.assertTrue(payload["bound"]["default"])

    def test_a_board_over_the_default_is_truncated_without_being_asked(self):
        """Goal 6 itself: no invocation returns more rows than the declared
        ceiling unless the caller asked. Driven through the constant rather
        than by writing 201 rows, which costs ~40 seconds of fixture."""
        import inproc
        task = inproc.load("perry-task")
        was, task.LIST_DEFAULT_LIMIT = task.LIST_DEFAULT_LIMIT, 3
        try:
            out = inproc.run("perry-task",
                             ["list", "--root", str(self.p.root), "--json"])
            payload = json.loads(out.stdout)
        finally:
            task.LIST_DEFAULT_LIMIT = was
        self.assertEqual(len(payload["tasks"]), 3)
        self.assertEqual(payload["bound"]["total"], 6)
        self.assertTrue(payload["bound"]["truncated"])
        self.assertTrue(payload["bound"]["default"],
                        "a bound nobody asked for must say it was the default")
        self.assertIn("3 of 6", out.stderr)

    def test_limit_zero_is_every_row(self):
        payload, err = self._list("--limit", "0")
        self.assertEqual(len(payload["tasks"]), 6)
        self.assertIsNone(payload["bound"]["limit"])
        self.assertFalse(payload["bound"]["truncated"])
        self.assertEqual(err.strip(), "")

    def test_a_limit_that_is_not_a_number_is_refused(self):
        out = run("perry-task", "list", "--root", str(self.p.root), "--json",
                  "--limit", "many")
        self.assertEqual(out.returncode, 1, out.stdout)
        # A refusal from a `--json` command comes back as JSON on stdout, not
        # as prose on stderr — `schema/task-list-contract.md § stderr is not
        # the failure channel`.
        self.assertIn("--limit", out.stdout + out.stderr)

    def test_the_contract_version_moved_with_the_meaning(self):
        """A consumer pinned to 1.18 must be able to see that rows can now be
        missing. `semantics` is where that is said."""
        payload, _err = self._list()
        self.assertEqual(payload["contract"], "perry-task/list/1.19")
        self.assertIn("1.19", [e["version"] for e in payload["semantics"]])


if __name__ == "__main__":
    unittest.main()
