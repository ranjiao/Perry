"""The store is the canonical file, so every tool that touches it must say so.

ADR-007 decision 2 made `perry/tasks.jsonl` what a field MEANS and `BOARD.md`
rendered output. Three V4 rounds — TASK-089's and TASK-093's two — found that
the tools around it had not caught up, in three different ways, and this suite
pins the answers.

**1. A remedy that destroyed what it repaired.** `perry-lint § store-drift`
printed *"or run `perry-tasks write` to re-derive the store from the file"* in
the same sentence that called `tasks.jsonl` "what the field means".
`perry-tasks write` runs `BOARD.md` → store, which is the migration direction,
so on the ordinary drift case — `perry-task` wrote the store, the board is
stale — the remedy overwrote the canonical value with the projection and
reported success. Measured on a copy: `status: in_progress` and a next action
the board did not have, gone, with an unchanged record count. There was no
command for the other direction at all, which is why the wrong one was being
recommended; `render --write` is that command.

**2. Three unguarded `TypeError`s.** The store is a file a person can open, and
every check indexed, sorted or compared its fields without asking what they
were. `id` as a list is unhashable; a store mixing `id: 3` with `id: "TASK-001"`
kills `sorted(set(...))`; `order` as `"3"` kills the sort in `_order_drift`.
Each exited the WHOLE lint at rc 2 with **no findings** — so one bad line
reported the same as a clean project, only louder. TASK-093 enumerated four
instances of "a guard that crashes instead of reporting"; these were the fifth,
sixth and seventh, and `_order_drift` was added by the fix for the first four.

**3. A finding that named the wrong row.** `_board_line_of` matched the id in
any cell, so a closed row still named in an open row's `Depends on` resolved to
that other row's line — and `check_store_drift` uses it as the predicate for
"the board carries this row". It reported `TASK-088 — the file carries this
row` against the line where **TASK-089** is written.

Run: python3 tests/parallel test_store_is_canonical
"""

from __future__ import annotations

import json
import contextlib
import importlib.machinery
import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINT = ROOT / "bin" / "perry-lint"
TASKS = ROOT / "bin" / "perry-tasks"


class Fixture(unittest.TestCase):
    """Perry's own project, copied WITH its store — the canonical arrangement."""

    def project(self) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        shutil.copytree(ROOT / "perry", d / "perry")
        shutil.copytree(ROOT / ".perry", d / ".perry",
                        ignore=shutil.ignore_patterns("*.lock"))
        self.assertTrue((d / "perry" / "tasks.jsonl").exists(),
                        "this fixture is the WITH-store case; if the repo "
                        "stopped tracking its store, that is the news")
        return d

    def records(self, d: pathlib.Path) -> list[dict]:
        text = (d / "perry" / "tasks.jsonl").read_text(encoding="utf-8")
        return [json.loads(l) for l in text.split("\n") if l.strip()]

    def put(self, d: pathlib.Path, recs: list[dict]) -> None:
        (d / "perry" / "tasks.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs),
            encoding="utf-8")

    def sh(self, tool: pathlib.Path, *args: str):
        """**Not `run`.** `TestCase.run` is the method unittest calls to
        EXECUTE a test. Naming a helper `run` overrode it, so every test
        "ran" by shelling out once and returning — `countTestCases()` said 10
        and the runner said `Ran 0 tests ... OK`. A suite that passes with
        every test uncalled is the sibling of the test that passes with its
        subject deleted, and it is louder about being fine.

        `tests/parallel` fails a module contributing zero tests, which is the
        backstop that would have caught this on the next full gate.
        """
        return subprocess.run([sys.executable, str(tool), *args],
                              capture_output=True, text=True, cwd=ROOT)


class TheRemedyDoesNotDestroyWhatItRepairs(Fixture):

    def _drifted(self) -> pathlib.Path:
        """A project where the STORE is right and the file is stale.

        The ordinary case, because `perry-task` writes the store and re-renders
        the board — so any disagreement is a board someone edited.
        """
        d = self.project()
        recs = self.records(d)
        target = next(r for r in recs if r.get("status") == "not_started")
        self.tid = target["id"]
        target["status"] = "in_progress"
        target["next_action"] = "ONLY THE STORE HAS THIS"
        self.put(d, recs)
        return d

    def test_write_refuses_without_the_explicit_destructive_direction(self):
        d = self._drifted()
        proc = self.sh(TASKS, "write", "--root", str(d))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("--from-board", proc.stderr)
        self.assertIn("render --write", proc.stderr)
        after = {r["id"]: r for r in self.records(d)}[self.tid]
        self.assertEqual(after["status"], "in_progress",
                         "the refusal must write nothing at all")

    def test_from_board_is_the_explicit_way_through(self):
        """The migration direction still exists — it just has to be asked for.

        Adoption imports a foreign board, and a project whose board was edited
        before it had a store needs exactly this. Removing the opt-in would
        make the refusal a wall.
        """
        d = self._drifted()
        proc = self.sh(TASKS, "write", "--from-board", "--root", str(d))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        after = {r["id"]: r for r in self.records(d)}[self.tid]
        self.assertEqual(after["status"], "not_started",
                         "--from-board is the board-wins direction and must "
                         "actually take the board's value")

    def test_render_write_is_the_direction_the_drift_case_needs(self):
        d = self._drifted()
        before = {r["id"]: r for r in self.records(d)}[self.tid]
        proc = self.sh(TASKS, "render", "--write", "--root", str(d))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        board = (d / "perry" / "BOARD.md").read_text(encoding="utf-8")
        self.assertIn("ONLY THE STORE HAS THIS", board,
                      "render --write puts the FILE in line with the store")
        after = {r["id"]: r for r in self.records(d)}[self.tid]
        self.assertEqual(after, before, "and touches the store not at all")
        lint = self.sh(LINT, "--root", str(d))
        self.assertIn("0 row(s) drifted", lint.stdout)

    def test_write_requires_explicit_import_even_when_there_is_no_store(self):
        """The refusal is about discarding, not about the command.

        A project with no store is what `write` is FOR. Refusing there would
        make adoption impossible and is the obvious over-correction.
        """
        d = self.project()
        (d / "perry" / "tasks.jsonl").unlink()
        refused = self.sh(TASKS, "write", "--root", str(d))
        self.assertEqual(refused.returncode, 1, refused.stderr)
        self.assertIn("--from-board", refused.stderr)
        proc = self.sh(TASKS, "write", "--from-board", "--root", str(d))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(self.records(d))

    def test_lint_no_longer_prescribes_the_destroying_direction(self):
        """The finding's own text, checked.

        This is a string assertion on purpose. The bug was not in the code
        `store-drift` runs — it was in the sentence it printed, and a user who
        follows Perry's instructions and loses data was failed by the sentence.
        """
        d = self._drifted()
        out = self.sh(LINT, "--root", str(d)).stdout
        self.assertIn("store-drift", out)
        line = next(l for l in out.split("\n") if "store-drift]" in l)
        self.assertIn("render --write", line)
        self.assertNotIn("run `perry-tasks write` to re-derive", line)
        self.assertIn("DISCARDS", line,
                      "the other direction may be mentioned, but never "
                      "without saying what it costs")


class ABadlyTypedStoreIsReportedNotFatal(Fixture):
    """Every shape a hand edit can produce, swept rather than spotted.

    The three crashes were found by a typed sweep — 19 fields x 9 JSON shapes —
    and not by reading, which is why this test sweeps too. Asserting the three
    known ones would pass on the day someone adds a fourth field and a fourth
    `sorted()`.
    """

    SHAPES = {"list": ["x"], "dict": {"a": 1}, "int": 3, "float": 1.5,
              "bool": True}

    def test_no_shape_of_no_field_can_kill_the_lint(self):
        for field in ("id", "order", "title", "depends_on", "status"):
            for name, value in self.SHAPES.items():
                with self.subTest(field=field, shape=name):
                    d = self.project()
                    recs = self.records(d)
                    recs[0][field] = value
                    self.put(d, recs)
                    proc = self.sh(LINT, "--root", str(d))
                    self.assertNotIn("Traceback", proc.stderr,
                                     f"{field}={value!r} killed the lint")
                    self.assertIn("(s)", proc.stdout,
                                  "the lint must still print its summary")

    def test_a_wrong_typed_field_is_named_and_the_row_excluded(self):
        d = self.project()
        recs = self.records(d)
        tid = recs[0]["id"]
        recs[0]["order"] = "3"
        self.put(d, recs)
        out = self.sh(LINT, "--root", str(d)).stdout
        self.assertIn("store-badly-typed", out)
        self.assertIn("`order` is str, expected integer or null", out)
        self.assertIn(tid, out)
        self.assertIn("unknown here rather than absent", out,
                      "excluding a record and calling the rest clean is the "
                      "silence this whole check exists to break")

    def test_diff_reports_string_and_boolean_order_as_json_findings(self):
        for value in ("3", True):
            with self.subTest(order=value):
                d = self.project()
                recs = self.records(d)
                recs[0]["order"] = value
                self.put(d, recs)
                proc = self.sh(TASKS, "diff", "--root", str(d))
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                payload = json.loads(proc.stdout)
                self.assertFalse(payload["store_valid"])
                self.assertIn("`order`", payload["store_findings"][0]["message"])
                self.assertNotIn("TypeError", proc.stderr)

    def test_the_right_types_are_read_off_the_writer(self):
        """`depends_on` is a LIST, and the live store proves it.

        The first version of the type table asserted from memory that every
        field but `order` is a string. `depends_on` is a list, so the gate
        excluded all 98 records on its first run. This test is the reason that
        cannot happen quietly: the live store must pass its own gate.
        """
        d = self.project()
        out = self.sh(LINT, "--root", str(d)).stdout
        self.assertNotIn("store-badly-typed", out,
                         "Perry's own store must satisfy the type table — if "
                         "it does not, the table is wrong, not the store")
        self.assertIn(f"{len(self.records(d))} record(s)", out,
                      "and every record must survive the gate, not merely "
                      "most of them")

    def test_a_record_with_no_id_is_reported_rather_than_skipped(self):
        """`{}` parses, is a dict, and has every field of the right type.

        Vacuously. Both earlier checks pass it and then the id-keyed dict build
        drops it with no finding — a line in the canonical store that no reader
        will ever see and nothing reports.
        """
        d = self.project()
        recs = self.records(d)
        self.put(d, [{}] + recs)
        out = self.sh(LINT, "--root", str(d)).stdout
        self.assertIn("has no `id`", out)


class AFindingNamesItsOwnRow(Fixture):

    def test_a_closed_row_named_in_depends_on_is_not_a_board_row(self):
        """The predicate for "the board carries this row" is the FIRST cell.

        `done` removes the row, so a closed task with dependents is named on
        the board only inside someone else's `Depends on` cell. Matching the id
        anywhere in the line made that count as a row, and the finding pointed
        at the dependent's line number.
        """
        d = self.project()
        recs = self.records(d)
        board = (d / "perry" / "BOARD.md").read_text(encoding="utf-8")

        # **Ghosts are computed from the BOARD, not from `depends_on`.** The
        # first version of this test read the store's `depends_on` lists and
        # picked the first id with no board row — and got one that appears in
        # no board LINE either, so the branch was never entered and reverting
        # the fix left the test green. The property under test is about what
        # `_board_line_of` sees, which is board text.
        first_cells, any_cell = set(), set()
        for line in board.split("\n"):
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip().replace("*", "").replace("~", "")
                     for c in line.strip().strip("|").split("|")]
            if cells:
                first_cells.add(cells[0])
            any_cell.update(c for c in cells[1:] if c.startswith("TASK-"))
        stored_ids = {r["id"] for r in recs}
        ghosts = sorted((any_cell - first_cells) & stored_ids)
        self.assertTrue(ghosts,
                        "no id on this board is cited in a non-first cell "
                        "without having a row of its own, so the case cannot "
                        "be exercised — construct one rather than passing "
                        "vacuously")

        # Drop one ghost's record. Before the fix this reported "the file
        # carries this row" against the CITING row's line number.
        ghost = ghosts[0]
        self.put(d, [r for r in recs if r["id"] != ghost])
        out = self.sh(LINT, "--root", str(d)).stdout
        self.assertNotIn(f"{ghost} — the file carries this row", out,
                         f"{ghost} has no row on the board; it is only cited "
                         f"in a `Depends on` cell")


class PerryTasksLocksTheWholeOperation(unittest.TestCase):
    def test_board_import_derives_and_writes_inside_one_project_lock(self):
        from tests.test_store_is_the_write_target import Project, BOARD
        p = Project(self, BOARD.replace(
            "**迁移 done，占比目标 not_started**", "not_started"))
        path = ROOT / "bin" / "perry-tasks"
        spec = importlib.util.spec_from_loader(
            "perry_tasks_lock_test", importlib.machinery.SourceFileLoader(
                "perry_tasks_lock_test", str(path)))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        active = {"value": False}
        real_build, real_write = mod.build, mod.lib.write_atomic

        @contextlib.contextmanager
        def lock(*_args, **_kwargs):
            active["value"] = True
            try:
                yield
            finally:
                active["value"] = False

        def checked_build(root):
            self.assertTrue(active["value"], "source derivation escaped the lock")
            return real_build(root)

        def checked_write(path, text):
            self.assertTrue(active["value"], "replacement escaped the lock")
            return real_write(path, text)

        mod.lib.project_lock = lock
        mod.build = checked_build
        mod.lib.write_atomic = checked_write
        try:
            rc = mod.main(["write", "--from-board", "--root", str(p.root)])
        finally:
            mod.lib.write_atomic = real_write
        self.assertEqual(rc, 0)
        self.assertTrue((p.root / "tasks.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
