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

    #: `(argv, the file it would have written, the store that feeds it)`.
    #:
    #: **The third column is the repair.** `_disturb` used to disturb
    #: `tasks.jsonl` for every board renderer, and a renderer reads its OWN
    #: store, so `risks-render`, `intake-render` and `asks-render` had nothing
    #: to carry and were skipped. `perry-tasks` and `--write` are spelt in
    #: every row rather than factored out, so this table reads as the vector a
    #: caller types.
    WRITES = (
        (("perry-tasks", "write", "--from-board"), "tasks.jsonl", "tasks.jsonl"),
        (("perry-tasks", "risks-write", "--from-board"), "risks.jsonl", "risks.jsonl"),
        (("perry-tasks", "intake-write", "--from-board"), "intake.jsonl", "intake.jsonl"),
        (("perry-tasks", "asks-write", "--from-board"), "asks.jsonl", "asks.jsonl"),
        (("perry-tasks", "render", "--write"), "BOARD.md", "tasks.jsonl"),
        (("perry-tasks", "risks-render", "--write"), "BOARD.md", "risks.jsonl"),
        (("perry-tasks", "intake-render", "--write"), "BOARD.md", "intake.jsonl"),
        (("perry-tasks", "asks-render", "--write"), "BOARD.md", "asks.jsonl"),
    )

    def setUp(self):
        self.p = Project()
        # **One row in each of the four registers.** The fixture used to open
        # a task and nothing else, so three of the four stores never minted
        # and five of the eight commands below took the `skip` branch without
        # reporting it. What hid behind those skips, measured 2026-09-10:
        # `bin/perry-tasks:516` `flags=flags` → `flags=flags - {"--dry-run"}`
        # makes `risks-render --write --dry-run` rewrite BOARD.md, and the
        # FULL suite stayed green.
        self.p.run("add", "--title", "a row so every store has something")
        self.p.run("risk-add", "--title", "a risk so the risks store has one")
        self.p.run("intake", "--title", "a request so the intake store has one")
        self.p.run("ask", "--needed", "an answer so the ask store has one")
        for argv, _target, _source in self.WRITES:
            run(*argv, "--root", str(self.p.root))  # mint the stores

    #: Which side to disturb so the command has real work to do. A store
    #: writer is measured by whether it RECREATES a store that is not there; a
    #: board renderer by whether it carries a changed store into the board.
    KIND = {"tasks.jsonl": "store", "risks.jsonl": "store",
            "intake.jsonl": "store", "asks.jsonl": "store",
            "BOARD.md": "board"}

    #: `store → (a cell value in it, what to change that value to)`. Each is a
    #: rendered, NON-identifying cell: changing an id would make the record
    #: one the board has no line for, and the renderer would refuse rather
    #: than carry it — a different behaviour, and not the one under test.
    CELL = {
        "tasks.jsonl": ('"not_started"', '"blocked"'),
        "risks.jsonl": ('"status": "open"', '"status": "mitigated"'),
        "intake.jsonl": ('"outcome": "—"', '"outcome": "noted"'),
        "asks.jsonl": ('"blocks": "—"', '"blocks": "TASK-001"'),
    }

    def _disturb(self, target: str, source: str):
        """Make the command's output differ from what is on disk.

        `("absent", None)` — the target was removed and a dry run must not put
        it back. `("bytes", b"...")` — the target must still hold exactly
        these.

        **There is no third answer any more.** This used to return
        `("skip", None)` for a fixture it could not disturb, and the caller
        `continue`d past it in silence; the floor of `exercised >= 2` then
        passed on two of eight commands. Every precondition it used to skip
        on is now asserted, so a fixture that stops minting a store fails here
        and names it.
        """
        path = self.p.root / target
        store = self.p.root / source
        self.assertTrue(store.exists(),
                        f"the fixture minted no {source}, so nothing below "
                        f"exercises {target}")
        if self.KIND[target] == "store":
            path.unlink()          # a dry run must not put it back
            return ("absent", None)
        self.assertTrue(path.exists(), f"the fixture wrote no {target}")
        old, new = self.CELL[source]
        text = store.read_text(encoding="utf-8")
        self.assertIn(old, text, f"{source} does not carry {old} to change")
        store.write_text(text.replace(old, new, 1), encoding="utf-8")
        return ("bytes", path.read_bytes())

    def test_a_dry_run_writes_nothing_that_the_real_run_would_write(self):
        """**Each command carries its own control, and the fixture is disturbed
        first.**

        The previous version minted every store in `setUp` and then compared
        bytes. That made the non-dry-run twin a byte NO-OP — the store already
        equalled what `write --from-board` derives — so the comparison could not
        tell a dry run from a real one. A V4 round disabled the dry-run gate at
        `bin/perry-tasks:234` and the FULL suite stayed green while
        `perry-tasks write --from-board --dry-run` rewrote its store and printed
        `wrote`, which is TASK-253's original defect verbatim. The same
        mutation at `bin/perry-config:117` rewrote `.perry/config.jsonl` while
        printing "Nothing was written."

        The old `reached >= 2` guard counted commands that EXITED 0, not
        commands that would have changed bytes, which is why it did not notice.

        **And then two of the eight carried all of it.** `_disturb` returned
        `skip` for five commands the fixture could not disturb, the loop
        `continue`d past them without a word, and a floor of two was enough to
        stay green. Measured 2026-09-10: `bin/perry-tasks:516` `flags=flags` →
        `flags=flags - {"--dry-run"}` makes `risks-render --write --dry-run`
        rewrite BOARD.md, and the full suite stayed green. All eight are
        exercised now and the floor is the length of the table.
        """
        exercised = []
        for argv, target, source in self.WRITES:
            path = self.p.root / target
            with self.subTest(command=" ".join(argv[1:])):
                mode, before = self._disturb(target, source)
                dry = run(*argv, "--root", str(self.p.root), "--dry-run")
                if mode == "absent":
                    self.assertFalse(
                        path.exists(),
                        f"{' '.join(argv[1:])} --dry-run created {target}")
                else:
                    self.assertEqual(
                        path.read_bytes(), before,
                        f"{' '.join(argv[1:])} --dry-run wrote to {target}")
                self.assertEqual(dry.returncode, 0, dry.stderr[-300:])
                # The control, per command: the same call without --dry-run
                # must change what the dry run left alone. Without this the
                # case above passes for a command that can do nothing at all.
                out = run(*argv, "--root", str(self.p.root))
                self.assertEqual(out.returncode, 0, out.stderr[-300:])
                if mode == "absent":
                    self.assertTrue(
                        path.exists(),
                        f"{' '.join(argv[1:])} did not write {target}, so the "
                        f"dry-run check above proved nothing")
                else:
                    self.assertNotEqual(
                        path.read_bytes(), before,
                        f"{' '.join(argv[1:])} changed no bytes, so the "
                        f"dry-run check above proved nothing")
                exercised.append(" ".join(argv[1:]))
        self.assertEqual(
            len(exercised), len(self.WRITES),
            "a command in the table did not both refuse a dry run and write "
            "without one. Exercised: " + ", ".join(exercised))


class TestPerryConfigHonoursDryRun(unittest.TestCase):
    """The second half of goal 4a, and it was untested.

    Disabling the gate at `bin/perry-config:117` left the full suite green
    while all four writing subcommands rewrote `.perry/config.jsonl` and
    printed "Nothing was written." A tool that writes and says it did not is
    DESIGN-016 § 1.5's own subject.
    """

    #: `(argv, what it changes)`. `set`/`unset` move a setting record;
    #: `track`/`untrack` move a track record. All four write the same store.
    WRITES = (
        ("set", "Chat language", "Klingon"),
        ("unset", "Chat language"),
        ("track", "a-new-track", "--mode", "project"),
        ("untrack", "intake"),
    )

    def setUp(self):
        import config_store
        tracks = [config_store.track("main"),
                  config_store.track("intake", "queue")]
        self.p = Project(tracks=tracks)
        config_store.write_config(self.p.root, tracks=tracks,
                                  settings={"Chat language": "English"})
        self.store = self.p.root / ".perry" / "config.jsonl"

    def test_each_writing_subcommand_leaves_the_store_alone_on_a_dry_run(self):
        for argv in self.WRITES:
            with self.subTest(command=argv[0]):
                before = self.store.read_bytes()
                dry = run("perry-config", *argv, "--root", str(self.p.root),
                          "--dry-run")
                self.assertEqual(self.store.read_bytes(), before,
                                 f"perry-config {argv[0]} --dry-run wrote")
                if dry.returncode != 0:
                    continue
                out = run("perry-config", *argv, "--root", str(self.p.root))
                self.assertEqual(out.returncode, 0, out.stderr[-300:])
                self.assertNotEqual(
                    self.store.read_bytes(), before,
                    f"perry-config {argv[0]} changed no bytes, so the dry-run "
                    f"check above proved nothing")


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
        billion — deleting contract 2.0's whole behavioural change — left the
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
        missing — and this one is a MAJOR, so a conforming consumer stops at
        `major != 1` rather than reading a window as the project. The user
        took that decision on 2026-09-09; it shipped as 1.19 for a few hours
        first."""
        payload, _err = self._list()
        # 2.1 (TASK-237 3a) moved where asks/risks/intake are read from; the
        # major this test is about is unchanged.
        self.assertEqual(payload["contract"], "perry-task/list/2.1")
        self.assertIn("2.0", [e["version"] for e in payload["semantics"]])
        major = int(payload["contract"].rsplit("/", 1)[1].split(".")[0])
        self.assertEqual(major, 2, "a row-count change is a major here")


def shipped_tools() -> list[Path]:
    """Every executable in `bin/`, discovered rather than listed.

    The same discovery `tests/test_shipped_vocabulary § shipped_tools` uses,
    and the reason it is here too is the finding that produced the two classes
    below: every `--help` assertion in this suite iterated the six tools that
    declare a `SURFACE`, so the other fourteen were untested for the goal that
    says **every** tool. `perry-restore-check` read `-h` at `argv[0]` alone for
    exactly that long.
    """
    return sorted(p for p in (PERRY_HOME / "bin").iterdir()
                  if p.is_file() and not p.name.startswith(".")
                  and p.suffix != ".md" and os.access(p, os.X_OK))


def run_tool(path: Path, *argv: str, env: dict | None = None):
    """Execute `path` directly, honouring its shebang.

    Not `[sys.executable, path]`: four of the twenty are bash, and running
    those under Python raises `SyntaxError` — which looks exactly like the
    defect this module is hunting and is not one.
    """
    e = dict(os.environ)
    e.pop("PERRY_PROJECT", None)
    if env:
        e.update(env)
    return subprocess.run([str(path), *argv], capture_output=True,
                          text=True, env=e, timeout=120)


#: The spec's Bound A is 14 FILES carrying `"--root"`; one of them,
#: `perry_md_store.py`, is a library and not executable, and the executable
#: that reaches it is `perry-okr`, which names the flag nowhere in its own
#: text. So the executable population is those 13 plus `perry-okr` — still 14,
#: and derived rather than typed, so a tool that gains or loses `--root`
#: changes this set without anyone remembering to.
ROOT_READERS = tuple(sorted(
    [p.name for p in (PERRY_HOME / "bin").iterdir()
     if p.is_file() and os.access(p, os.X_OK) and p.suffix != ".md"
     and '"--root"' in p.read_text(errors="replace")] + ["perry-okr"]))


class TestHelpPrintsFromAnyPositionOnEveryTool(unittest.TestCase):
    """DESIGN-016 goal 2 says *every tool*, and the suite only ever asked six.

    `DECLARED` is what every other help assertion in this suite iterates, so
    the fourteen tools outside it were untested for a goal whose subject is
    all twenty. `perry-restore-check` read `-h` at `argv[0]` alone for exactly
    that long: `perry-restore-check --root /tmp -h` printed `unknown option
    -h` and exited 2.

    **The bar here is narrower than the goal's sentence, and deliberately.**
    Help must win over anything that would RUN — that is § 1.1's actual
    complaint, `perry-tasks render --write --help` running the render — and it
    must work from any position among arguments the tool ACCEPTS. It is not
    asserted over an argument the tool refuses: five tools answer
    `<tool> <undeclared token> -h` with the refusal rather than the help, and
    a refusal that names `--help` has run nothing and misled nobody. The six
    declaring tools resolve that collision the other way because
    `lib.scan_argv` reads the whole vector first. The inconsistency is real
    and is TASK-411, not a silent narrowing here.
    """

    def test_every_shipped_tool_answers_help_in_first_position(self):
        for tool in shipped_tools():
            with self.subTest(tool=tool.name):
                r = run_tool(tool, "--help")
                self.assertEqual(r.returncode, 0, r.stderr[-400:])
                self.assertTrue(r.stdout.strip(), "help printed nothing")

    def test_help_wins_after_a_flag_the_tool_accepts(self):
        # The position that was broken, over the population for which the
        # leading flag is legal: the fourteen `--root` readers.
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(len(ROOT_READERS), 14, ROOT_READERS)
            for name in ROOT_READERS:
                with self.subTest(tool=name):
                    r = run_tool(BIN / name, "--root", tmp, "-h")
                    self.assertEqual(r.returncode, 0, r.stderr[-400:])
                    self.assertTrue(r.stdout.strip(), "help printed nothing")

    def test_help_wins_over_a_subcommand_that_would_run(self):
        # § 1.1's defect in its own shape: the command in front of `-h` must
        # not execute. `build` reads and prints; if help loses, stdout carries
        # the render instead of the usage.
        with tempfile.TemporaryDirectory() as tmp:
            for tool, argv in READS:
                if not argv:
                    continue
                with self.subTest(tool=tool):
                    r = run_tool(BIN / tool, *argv, "--root", tmp, "-h")
                    self.assertEqual(r.returncode, 0, r.stderr[-400:])
                    self.assertIn("usage", r.stdout.lower())

    def test_help_is_not_a_traceback_anywhere(self):
        for tool in shipped_tools():
            with self.subTest(tool=tool.name):
                r = run_tool(tool, "--help")
                self.assertNotIn("Traceback (most recent call last)", r.stderr)


def shell_tools() -> list[Path]:
    """The `bin/` executables that are bash, read off their shebang.

    Four of the twenty. `run_tool`'s docstring already knew that and nothing
    else in the suite did: every `--help` assertion here iterates either the
    six declaring tools or all twenty in FIRST position, and criterion 2a —
    `--help` never runs a write — had never been asked of a shell tool at all.
    """
    return [p for p in shipped_tools()
            if p.read_bytes().split(b"\n", 1)[0].strip().endswith(b"bash")]


class TestHelpNeverRunsAWriteInTheShellTools(unittest.TestCase):
    """Criterion 2a — a FAIL-grade gate, on the four tools nobody had probed.

    `bin/perry-dispatch-limit` bound `cmd="${1:-}"` and answered `-h|--help`
    as one arm of `case "$cmd"`, so help was recognised in argument position 1
    and NOWHERE else. Measured 2026-09-10:

        perry-dispatch-limit register <TASK-ID> claude-subagent --help
          → exit 0, "🟢 Slot reserved", and
            ~/.cache/perry/in-flight/<TASK-ID>-claude-subagent.json on disk,
            byte-identical to the same call with `--help` removed.

    That is not a cosmetic help defect: the marker holds one of three global
    dispatch slots for the 4h TTL, so a caller asking what the tool takes
    consumes a real resource and the next real dispatch is refused.

    Every write these four make lands under `$HOME`, so the assertion is that
    `$HOME` is byte-identical across the call — which is why
    `perry-dispatch-limit` no longer mints its cache directory at module
    scope.
    """

    #: `tool → the argv that reaches its most side-effecting path`. Hand-
    #: written because "the vector that would write" is not derivable, and
    #: held to the derived population by the control below.
    VECTORS = {
        "perry-dispatch-limit": ("register", "TASK-999", "claude-subagent"),
        "perry-codex-preflight": ("--force",),
        "perry-update-check": ("--force",),
        "perry-detect-host": (),
    }

    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.home,
                        ignore_errors=True)

    def _home_tree(self) -> dict:
        import hashlib
        return {str(p.relative_to(self.home)):
                (hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file()
                 else "dir")
                for p in sorted(self.home.rglob("*"))}

    def test_the_vector_table_covers_every_shell_tool(self):
        """The control for the sweep: a tool added tomorrow is not skipped."""
        self.assertEqual(sorted(self.VECTORS), sorted(p.name for p in
                                                      shell_tools()))

    def test_help_from_any_position_prints_and_leaves_home_alone(self):
        for tool, vector in sorted(self.VECTORS.items()):
            for where in ("first", "middle", "last"):
                if where == "middle" and len(vector) < 2:
                    continue
                argv = {"first": ("--help", *vector),
                        "middle": (*vector[:1], "--help", *vector[1:]),
                        "last": (*vector, "--help")}[where]
                with self.subTest(tool=tool, position=where):
                    before = self._home_tree()
                    r = run_tool(BIN / tool, *argv,
                                 env={"HOME": str(self.home)})
                    self.assertEqual(r.returncode, 0, r.stderr[-400:])
                    self.assertTrue(r.stdout.strip(), "help printed nothing")
                    self.assertEqual(
                        self._home_tree(), before,
                        f"{tool} {' '.join(argv)} changed something under "
                        f"$HOME while answering --help")

    def test_the_control_is_that_the_same_call_without_help_does_write(self):
        """Without this, the sweep above passes for a tool that can do nothing.

        `register` is the one vector in the table whose no-`--help` twin
        writes on every machine — the other three reach the network, a `codex`
        binary that may not be installed, or nothing at all — so it is the one
        that is asserted, by name.
        """
        vector = self.VECTORS["perry-dispatch-limit"]
        r = run_tool(BIN / "perry-dispatch-limit", *vector,
                     env={"HOME": str(self.home)})
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        marker = (self.home / ".cache" / "perry" / "in-flight"
                  / "TASK-999-claude-subagent.json")
        self.assertTrue(marker.exists(),
                        "`register` wrote no marker, so the `--help` case "
                        "above proved nothing")
        released = run_tool(BIN / "perry-dispatch-limit", "release",
                            "TASK-999", env={"HOME": str(self.home)})
        self.assertEqual(released.returncode, 0, released.stderr[-400:])


class TestAnUndeclaredFlagIsRefusedWithASubcommandInFront(unittest.TestCase):
    """Criterion 3 over all twenty executables, with a lead each one accepts.

    `TestAnUndeclaredTokenIsRefused` above asks six tools. A V4 round asked
    all twenty **with a subcommand in front** — the position where a real
    caller types a flag — and found seven that did not answer 2:

        perry-goals krs --xyzzy            exit 1, "takes no positional …"
        perry-decide list --xyzzy          exit 0, silent
        perry-knowledge list --xyzzy       exit 0, silent
        perry-dispatch-limit list --xyzzy  exit 0, silent
        perry-explain TASK-001 --xyzzy     exit 0, silent
        perry list --xyzzy                 exit 0, silent
        perry-detect-host --xyzzy          exit 0, silent, and it PRINTS AN
                                           ANSWER

    plus `perry-update-check --xyzzy`, which refused but at exit 1.

    The user-visible form in the writers is worse than a dropped flag:
    `perry-goals` collects an undeclared token into `a.rest`, which only
    `krs` and `link` ever read, so

        perry-goals commit --track main --promise "…" --to Finance
                    --due 2026-12-01 --by-when-notes "before the Q4 board
                    meeting"

    exited 0 and filed the commitment with an EMPTY `By when note` cell,
    having swallowed the flag AND its value.
    """

    #: A subcommand each tool accepts, so the undeclared flag is reached
    #: rather than masked by "expected one of …" — the same discipline as
    #: `TestAFlagWithItsValueMissingIsRefused.LEAD`, and held to the derived
    #: population by `test_the_lead_table_covers_every_shipped_tool`.
    LEAD = {
        "perry": ("list",), "perry-churn": (),
        "perry-codex-preflight": (), "perry-config": ("show",),
        "perry-context-budget": (), "perry-decide": ("list",),
        "perry-detect-host": (), "perry-diagnose": (),
        "perry-dispatch-limit": ("list",), "perry-explain": ("TASK-001",),
        "perry-goals": ("krs",), "perry-knowledge": ("list",),
        "perry-lint": (), "perry-okr": ("build",),
        "perry-restore-check": ("HEAD", "README.md"), "perry-state": (),
        "perry-state-cost": (), "perry-task": ("list",),
        "perry-tasks": ("build",), "perry-update-check": (),
    }

    #: **Reported, not fixed here.** Three read-only tools still take an
    #: undeclared flag as a positional and drop it. `review.md § 0`'s test
    #: puts them below the line — none writes, none gates a write, and the
    #: flag cannot change the answer any of them prints — so they are rows the
    #: round files rather than work this change buys. They are named here so
    #: that a FOURTH tool joining them fails the sweep, and so that fixing one
    #: is a one-line deletion from this set rather than a rediscovery.
    STILL_DROPS = ("perry", "perry-detect-host", "perry-explain")

    def setUp(self):
        self.p = Project()
        self.p.run("add", "--title", "a row the probes can act on")
        self.home = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.home,
                        ignore_errors=True)

    #: The three that take no project and would read `--root` as a path.
    NO_ROOT = ("perry", "perry-churn", "perry-codex-preflight",
               "perry-detect-host", "perry-dispatch-limit",
               "perry-restore-check", "perry-update-check")

    def _probe(self, name: str):
        lead = self.LEAD[name]
        root = () if name in self.NO_ROOT else ("--root", str(self.p.root))
        return run_tool(BIN / name, *lead, *root, "--xyzzy",
                        env={"HOME": str(self.home)})

    def test_the_lead_table_covers_every_shipped_tool(self):
        self.assertEqual(sorted(self.LEAD),
                         sorted(p.name for p in shipped_tools()))

    def test_every_tool_but_the_named_rows_refuses_with_exit_2(self):
        for path in shipped_tools():
            if path.name in self.STILL_DROPS:
                continue
            with self.subTest(tool=path.name):
                out = self._probe(path.name)
                self.assertEqual(
                    out.returncode, 2,
                    f"{path.name} {' '.join(self.LEAD[path.name])} --xyzzy "
                    f"answered {out.returncode}, not 2\n"
                    + (out.stdout + out.stderr)[-300:])
                self.assertIn("--xyzzy", out.stdout + out.stderr,
                              f"{path.name} refused without naming the token")

    def test_the_row_list_still_describes_what_those_tools_do(self):
        """The exception list is a claim about three tools, so it is measured.

        When one of them is fixed this goes red and the fix is to delete its
        name above — which is the opposite of a skip that stays quiet forever.
        """
        for name in self.STILL_DROPS:
            with self.subTest(tool=name):
                out = self._probe(name)
                self.assertNotEqual(
                    out.returncode, 2,
                    f"{name} now refuses an undeclared flag — take it out of "
                    f"STILL_DROPS and out of the reported rows")


class TestAnUnreadableProjectRootIsRefusedNotCrashed(unittest.TestCase):
    """Goal 10: no tool exits through a traceback. `chmod 000` reached five.

    `Path.exists()` does not return `False` when the parent directory is
    unsearchable — it calls `os.stat`, which raises `PermissionError`. Two
    sites asked it outside a `try`: `viewer/parsers § config_store_records`,
    whose own docstring says it *"never raises from here"*, and
    `bin/perry-context-budget § _budget_from_store`, whose docstring says it
    *"must keep working in a directory that is not a Perry project at all"*.

    Both had a correct answer already available — `unreadable` is one of the
    three reasons `config_store_records` is documented to return.

    The population is the six tools of `READS`, which is every tool that
    resolves a project root through a declared surface, plus
    `perry-context-budget` as the independent second site.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(self._restore_and_remove)
        perry = Path(self.tmp) / ".perry"
        perry.mkdir()
        (perry / "config.jsonl").write_text(
            '{"kind": "setting", "key": "tracks", "value": "main"}\n')
        os.chmod(perry, 0o000)

    def _restore_and_remove(self):
        import shutil
        os.chmod(Path(self.tmp) / ".perry", 0o755)
        shutil.rmtree(self.tmp, ignore_errors=True)

    #: Every executable, bare — plus the subcommand forms, because the first
    #: five sites each HID the next one: fixing `perry-config`'s made
    #: `perry-task list` reach `read_events`, and fixing that one reached
    #: `bin/perry-state § events_block`. Six sites in four files, found by
    #: sweeping rather than by grepping `.exists()`, of which `bin/` and
    #: `viewer/` hold 220 and almost none of them matter.
    WITH_SUBCOMMAND = READS + (
        ("perry-task", ("add",)),
        ("perry-tasks", ("render",)),
        ("perry-config", ("set",)),
        ("perry-goals", ("krs",)),
        ("perry-decide", ("list",)),
        ("perry-knowledge", ("list",)),
        ("perry-explain", ("TASK-001",)),
        ("perry-state", ("--compact",)),
        ("perry-context-budget", ()),
    )

    def test_no_tool_exits_through_a_traceback_on_an_unreadable_root(self):
        for tool, argv in self.WITH_SUBCOMMAND:
            with self.subTest(tool=" ".join((tool, *argv))):
                r = run_tool(BIN / tool, *argv, "--root", self.tmp)
                self.assertNotIn("Traceback (most recent call last)", r.stderr,
                                 f"{tool} crashed on an unreadable root")

    def test_every_shipped_executable_survives_it_bare(self):
        # The whole population, so a tool added tomorrow is covered tomorrow.
        for tool in shipped_tools():
            with self.subTest(tool=tool.name):
                r = run_tool(tool, "--root", self.tmp)
                self.assertNotIn("Traceback (most recent call last)", r.stderr)

    def test_the_resolver_names_the_reason_rather_than_raising(self):
        # The behavioural half. A crash is the symptom; the fix is that the
        # documented vocabulary answers, so a caller can tell "no store" from
        # "a store I may not read" and say which.
        sys.path.insert(0, str(PERRY_HOME))
        import importlib
        parsers = importlib.import_module("viewer.parsers")
        records, why = parsers.config_store_records(Path(self.tmp))
        self.assertIsNone(records)
        self.assertEqual(why, parsers.CONFIG_STORE_UNREADABLE)
        self.assertIn(why, parsers.CONFIG_STORE_UNUSABLE)

    def test_the_control_is_that_a_readable_store_still_answers(self):
        os.chmod(Path(self.tmp) / ".perry", 0o755)
        sys.path.insert(0, str(PERRY_HOME))
        import importlib
        parsers = importlib.import_module("viewer.parsers")
        records, why = parsers.config_store_records(Path(self.tmp))
        self.assertEqual(why, "")
        self.assertTrue(records)


class TestOnePrimitiveAnsweredTwice(unittest.TestCase):
    """`exists_or_unreadable` is spelled in two files and must not diverge.

    `viewer/parsers.py` is imported by `perry_md_store`, and `bin/lib` is
    imported before `viewer/` is on the path, so neither can take the other at
    module scope. That is a real cycle and not an excuse: this holds the two
    bodies to the same answer on the three inputs that exist.
    """

    def setUp(self):
        sys.path.insert(0, str(PERRY_HOME))
        sys.path.insert(0, str(BIN))
        import importlib
        self.a = importlib.import_module("viewer.parsers").exists_or_unreadable
        self.b = importlib.import_module("lib").exists_or_unreadable
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(self._clean)

    def _clean(self):
        import shutil
        os.chmod(self.tmp / "shut", 0o755)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_two_spellings_agree_on_all_three_answers(self):
        (self.tmp / "there").write_text("x")
        shut = self.tmp / "shut"
        shut.mkdir()
        (shut / "inside").write_text("x")
        os.chmod(shut, 0o000)
        cases = {
            "present": (self.tmp / "there", True),
            "absent": (self.tmp / "missing", False),
            "unreadable parent": (shut / "inside", None),
        }
        for name, (path, want) in cases.items():
            with self.subTest(case=name):
                self.assertIs(self.a(path), want)
                self.assertIs(self.b(path), want, "the two spellings diverged")



class TestAFlagWithItsValueMissingIsRefused(unittest.TestCase):
    """Criterion 10a: a bad invocation is exit 2, on every tool that takes a
    value-flag.

    `--root` with nothing after it was **silently dropped** by four tools, and
    in one of them that is a gate. `bin/perry-lint` read
    `argv[i] if i < len(argv) else None`, so the flag became no flag and the
    tool linted the CURRENT DIRECTORY; `bin/README.md § --quiet` says that mode
    is read by its exit code alone and `§ Lint after every tier-1 write` makes
    it a gate. A V4 round measured it with a clean cwd and a dirty named
    project:

        perry-lint --quiet --root <named>   exit 1   (correct)
        perry-lint --quiet --root           exit 0, no stdout, no stderr

    The gate passed, silently, about a project the caller never named.
    `perry-explain` and `perry-decide` carried the same line, and the six
    declaring tools were already correct because `lib.parse_surface` refuses it
    centrally.

    The population is every executable in `bin/` that names `--root`, so a tool
    that gains the flag tomorrow is covered tomorrow.
    """

    #: A subcommand each tool actually accepts, so `--root` is reached instead
    #: of being masked. **The first version of this sweep probed `<tool>
    #: --root` bare**, and for a tool that requires a subcommand that returns 2
    #: from "expected one of …" — the right code for the wrong reason. It
    #: passed `perry-goals` and `perry-knowledge` while both silently dropped
    #: the value, and `perry-goals commit … --root` wrote into the cwd's
    #: project with the named one untouched. A V4 round found it by re-probing
    #: WITH a subcommand.
    LEAD = {"perry-goals": ("krs",), "perry-knowledge": ("list",),
            "perry-decide": ("list",), "perry-task": ("list",),
            "perry-tasks": ("build",), "perry-okr": ("build",),
            "perry-config": ("show",)}

    def test_no_tool_treats_a_valueless_root_as_no_root(self):
        for name in ROOT_READERS:
            with self.subTest(tool=name):
                lead = self.LEAD.get(name, ())
                out = run_tool(BIN / name, *lead, "--root")
                self.assertNotEqual(
                    out.returncode, 0,
                    f"{name} {' '.join(lead)} --root with no value exited 0 — "
                    f"it answered about some project, and not the one the "
                    f"caller named")
                self.assertEqual(
                    out.returncode, 2,
                    f"{name} --root with no value should be exit 2, a bad "
                    f"invocation; got {out.returncode}\n"
                    + out.stderr[-300:])

    def test_an_empty_root_is_refused_rather_than_reinterpreted(self):
        """`--root ""` used to mean no `--root` at all.

        `lib.resolve_project_root` tests truthiness, so an empty value fell
        through to `$PERRY_PROJECT` and then to the walk up from the cwd:
        `perry-task add --root "$PROJ" …` with `PROJ` unset exited 0 having
        written into whichever project the cwd resolves to, while the one the
        caller named was untouched. § 1.1's own defect, through the commonest
        shell idiom there is.

        Checked from INSIDE a different project, because that is what makes
        the old behaviour a wrong answer rather than a crash.

        **The population is `ROOT_READERS`, derived, and that is the finding
        that rewrote this test.** It used to name four tools by hand — twenty
        lines below a sweep that derives all fourteen — and the refusal it was
        checking lived in `lib.parse_surface`, which only the six
        surface-declaring tools call. So four hand-picked declaring tools
        passed while the eight that parse their own vector did not refuse at
        all. Measured 2026-09-10, from inside a different project:
        `perry-goals commit --track main --promise … --root ""` exited 0
        having written `OKR.md`, `okr.jsonl` and `.perry/events.jsonl` into
        the cwd's project, with the named one untouched.
        """
        other = Project()
        other.run("add", "--title", "the project the caller did not name")
        self.assertEqual(len(ROOT_READERS), 14, ROOT_READERS)
        for tool in ROOT_READERS:
            lead = self.LEAD.get(tool, ())
            with self.subTest(tool=tool):
                out = subprocess.run(
                    [str(BIN / tool), *lead, "--root", ""],
                    capture_output=True, text=True, cwd=str(other.root),
                    env={k: v for k, v in os.environ.items()
                         if k != "PERRY_PROJECT"})
                self.assertEqual(out.returncode, 2, out.stdout[:200])
                # The message, not just the code: five of the fourteen already
                # exited 2 on this vector for an unrelated reason — a missing
                # positional, a directory that is not a git repository — which
                # is the "right code for the wrong reason" this class's own
                # `LEAD` comment was written about.
                self.assertIn("empty value", out.stderr,
                              f"{tool} exited 2 without saying that --root "
                              f"was empty:\n" + out.stderr[-300:])

    def test_the_one_spelling_of_the_empty_root_rule(self):
        """Goal 14b, at the size it can actually be held to.

        The refusal above is now asked of fourteen tools that each parse their
        own argument vector, which is exactly the shape that grows N copies of
        one rule — `bin/lib`'s own docstring counts six primitives that had
        fourteen implementations. So the rule is a function, every tool calls
        it, and the sentence the caller reads exists once.
        """
        sys.path.insert(0, str(BIN))
        import importlib
        lib = importlib.import_module("lib")
        self.assertIsNone(lib.empty_root_error("--root", "/tmp"))
        self.assertIsNone(lib.empty_root_error("--title", ""),
                          "the rule is about --root, not about every flag")
        self.assertIn("empty value", lib.empty_root_error("--root", ""))
        # Nobody spells the sentence themselves. `bin/lib` states it; the
        # thirteen other files may only name the function.
        sentence = lib.empty_root_error("--root", "")[:40]
        spelt_in = sorted(p.name for p in BIN.iterdir()
                          if p.is_file() and p.suffix != ".md"
                          and sentence in p.read_text(errors="replace"))
        self.assertEqual(spelt_in, [], f"{spelt_in} carry a second copy of "
                                       f"the message `lib` already owns")

    def test_the_lead_subcommands_are_ones_the_tools_accept(self):
        """The control for the vector above.

        A `LEAD` entry naming a subcommand the tool refuses would put the sweep
        straight back where it was: exit 2 for the wrong reason. Each must be
        accepted when `--root` carries a value.
        """
        with tempfile.TemporaryDirectory() as tmp:
            for name, lead in self.LEAD.items():
                with self.subTest(tool=name):
                    out = run_tool(BIN / name, *lead, "--root", tmp)
                    self.assertNotIn("expected one of", out.stderr)
                    self.assertNotIn("unknown argument", out.stderr)

    def test_the_control_is_that_the_flag_works_with_a_value(self):
        """Without this, a tool that refused every invocation would pass."""
        with tempfile.TemporaryDirectory() as tmp:
            ok = 0
            for name in ROOT_READERS:
                out = run_tool(BIN / name, "--root", tmp, "--help")
                if out.returncode == 0:
                    ok += 1
            self.assertEqual(ok, len(ROOT_READERS),
                             "a tool refuses --root even with a value")


class TestAPositionalNoHandlerReadsIsRefused(unittest.TestCase):
    """Criterion 3, through a positional rather than a flag.

    **Nothing tested this at all**: a V4 round set `a.extra = []` in
    `bin/perry-task`, disabling the refusal outright, and the full 3,466-test
    suite came back byte-identical to its baseline.

    The refusal itself was also stopping one position too far to the right,
    on a claim in its own comment that turned out to be false — that the id is
    the only positional any of the thirty subcommands takes. Nine never read
    `args.id`, so the FIRST positional was bound to it and dropped:

        perry-task ask USER-001 --needed "the STAGING password, corrected"
          → exit 0, USER-001 untouched, a SECOND row USER-002 minted

    Which subcommands read an id is now declared as `takes_id` in `SURFACE`.
    """

    #: Derived from the tool, not typed: every subcommand whose declaration
    #: says it reads no id. A tenth added tomorrow is covered tomorrow.
    @staticmethod
    def _id_less() -> list[str]:
        import inproc
        face = inproc.load("perry-task").SURFACE
        return [s["name"] for s in face["subcommands"]
                if s.get("takes_id") is False]

    def setUp(self):
        self.p = Project()
        self.p.run("add", "--title", "a row the probes can act on")

    def _bytes(self) -> dict:
        import hashlib
        return {f: hashlib.sha256(f.read_bytes()).hexdigest()
                for f in sorted(self.p.root.rglob("*")) if f.is_file()}

    def test_a_subcommand_that_reads_no_id_refuses_one(self):
        names = self._id_less()
        # A FLOOR, not an equality. `_id_less`'s own docstring says "a tenth
        # added tomorrow is covered tomorrow", and `assertEqual(…, 9)` said
        # the opposite: a tenth id-less subcommand turned this red, and the
        # cheapest way past a red count is to edit the number rather than to
        # look at the tenth. The floor keeps what the number was actually for
        # — proof the derivation is not returning an empty set — and lets the
        # sweep below cover whatever it derives.
        self.assertGreaterEqual(len(names), 9, sorted(names))
        for sub in names:
            with self.subTest(sub=sub):
                before = self._bytes()
                out = run("perry-task", sub, "TASK-001",
                          "--root", str(self.p.root))
                self.assertEqual(out.returncode, 2, out.stdout[:200])
                self.assertIn("takes no argument", out.stderr)
                self.assertEqual(self._bytes(), before,
                                 f"{sub} wrote before refusing")

    def test_a_subcommand_that_reads_an_id_refuses_a_second(self):
        face_subs = {s["name"] for s in __import__("inproc").load(
            "perry-task").SURFACE["subcommands"]}
        for sub in sorted(face_subs - set(self._id_less())):
            with self.subTest(sub=sub):
                before = self._bytes()
                out = run("perry-task", sub, "TASK-001", "TASK-002",
                          "--root", str(self.p.root))
                self.assertEqual(out.returncode, 2, out.stdout[:200])
                self.assertIn("takes no second argument", out.stderr)
                self.assertEqual(self._bytes(), before,
                                 f"{sub} wrote before refusing")

    def test_the_declaration_matches_what_the_handlers_read(self):
        """`takes_id` is a claim about code, so it is checked against the code.

        Without this the declaration is just a second place to be wrong, and
        the parser would refuse a positional a handler genuinely wanted.

        **It covered 26 of the 30, and said nothing about the other four.**
        `cmd_next`, `cmd_retitle`, `cmd_rung` and `cmd_evidence` are
        `cell_writer` closures assigned at module scope, not `def`s, so
        `funcs` does not hold them and `if fn in funcs` dropped all four out
        of `derived` in silence — which happens to be the same answer as "it
        reads an id" and so could never have gone red. The closures are found
        by their own shape now, and the table is asserted to be wholly
        accounted for, so a fifth handler written in a third shape is a
        failure rather than a gap.
        """
        import ast
        import re as _re
        src = (BIN / "perry-task").read_text(encoding="utf-8")
        tree = ast.parse(src)
        funcs = {n.name: n for n in tree.body
                 if isinstance(n, ast.FunctionDef)}

        def reads_id(node, depth=0, seen=None):
            seen = seen if seen is not None else set()
            for n in ast.walk(node):
                if (isinstance(n, ast.Attribute)
                        and isinstance(n.value, ast.Name)
                        and n.value.id == "args" and n.attr == "id"):
                    return True
                if isinstance(n, ast.Call) and depth < 3:
                    nm = (n.func.id if isinstance(n.func, ast.Name)
                          else n.func.attr if isinstance(n.func, ast.Attribute)
                          else None)
                    passes = any(isinstance(x, ast.Name) and x.id == "args"
                                 for x in n.args) or any(
                        isinstance(k.value, ast.Name) and k.value.id == "args"
                        for k in n.keywords)
                    if nm in funcs and nm not in seen and passes:
                        seen.add(nm)
                        if reads_id(funcs[nm], depth + 1, seen):
                            return True
            return False

        #: `cmd_x = cell_writer(…)` — one implementation of "correct this cell
        #: and nothing else", closed over per column. `cell_writer.run` opens
        #: with `tid = args.id`, so every closure reads an id by
        #: construction; that is asserted rather than assumed.
        closures = {n.targets[0].id for n in tree.body
                    if isinstance(n, ast.Assign)
                    and len(n.targets) == 1
                    and isinstance(n.targets[0], ast.Name)
                    and isinstance(n.value, ast.Call)
                    and getattr(n.value.func, "id", None) == "cell_writer"}
        self.assertTrue(closures, "no `cell_writer` closure was found, so the "
                                  "four subcommands built that way are "
                                  "unaccounted for again")
        self.assertTrue(reads_id(funcs["cell_writer"]),
                        "`cell_writer` stopped reading `args.id`, so its "
                        "closures can no longer be assumed to")

        table = _re.findall(r'"([a-z-]+)": (cmd_[a-z_]+)',
                            src[src.index("COMMANDS = {"):
                                src.index("def project_lock")])
        unaccounted = sorted({fn for _n, fn in table
                              if fn not in funcs and fn not in closures})
        self.assertEqual(unaccounted, [],
                         "these handlers are neither a top-level function nor "
                         "a `cell_writer` closure, so this check silently says "
                         "nothing about them")
        derived = {name for name, fn in table
                   if fn in funcs and not reads_id(funcs[fn])}
        self.assertEqual(derived, set(self._id_less()),
                         "SURFACE's `takes_id` and what the handlers read "
                         "have drifted apart")


if __name__ == "__main__":
    unittest.main()
