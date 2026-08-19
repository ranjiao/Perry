"""`perry-lint` reports a rendered file whose bytes disagree with the store.

ADR-007 decision 2: `BOARD.md` becomes rendered output and **a hand edit
becomes drift**. The ADR left the severity unset, and this suite pins the
answer as much as the behaviour — `warn`, never `error`, on the `NS-01`
precedent (a finding about Perry's own footprint stays `warn` so a user can
knowingly live with it) and on `perry-state § reconcile_drift`, which reports
drift and honours the board anyway.

**Three cases, and the third is the one that is easy to get wrong.** A project
with a store and an edited file yields the finding; a project with a store and
an untouched file does not; a project with **no store at all** yields nothing —
`perry-tasks` does not write `tasks.jsonl` yet, so that is every real project
today, and "no store" and "clean" are different answers. The silence is
asserted rather than assumed.

Run: python3 tests/parallel test_store_drift
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINT = ROOT / "bin" / "perry-lint"
TASKS = ROOT / "bin" / "perry-tasks"


class Fixture(unittest.TestCase):
    """A copy of Perry's own project, which is the only real board there is."""

    def project(self) -> pathlib.Path:
        """A project with NO store — `self.store(d)` adds one.

        **`perry/tasks.jsonl` now exists in this repository.** TASK-089 made it
        the write target, so copying `perry/` inherits a store whether the test
        wants one or not, and every no-store assertion below silently became a
        with-store assertion. Two tests failed the moment it was tracked, which
        is the transition working rather than a regression — the fixture has to
        say which case it is building.
        """
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        shutil.copytree(ROOT / "perry", d / "perry",
                        ignore=shutil.ignore_patterns("tasks.jsonl"))
        shutil.copytree(ROOT / ".perry", d / ".perry",
                        ignore=shutil.ignore_patterns("*.lock"))
        return d

    def store(self, d: pathlib.Path) -> pathlib.Path:
        proc = subprocess.run([sys.executable, str(TASKS), "write",
                               "--root", str(d)],
                              capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr[-400:])
        path = d / "perry" / "tasks.jsonl"
        self.assertTrue(path.exists(), "the fixture wrote no store")
        return path

    def lint(self, d: pathlib.Path, *extra) -> tuple[int, dict]:
        proc = subprocess.run([sys.executable, str(LINT), "--root", str(d),
                               "--json", *extra],
                              capture_output=True, text=True, cwd=ROOT)
        self.assertTrue(proc.stdout.strip().startswith("{"),
                        f"perry-lint printed no payload: "
                        f"{proc.stdout[-300:]}{proc.stderr[-300:]}")
        return proc.returncode, json.loads(proc.stdout)

    def drift(self, payload: dict) -> list[dict]:
        return [f for f in payload["findings"]
                if f["rule"].startswith("store-")]

    def edit_a_title(self, d: pathlib.Path,
                     title: str = "a title nothing wrote") -> str:
        """Hand-edit one board cell, the way a user still can today."""
        board = d / "perry" / "BOARD.md"
        text = board.read_text()
        m = re.search(r"^\| (TASK-\d+) \| ([^|]+)", text, re.M)
        self.assertIsNotNone(m, "the fixture board carries no task row")
        board.write_text(text[:m.start(2)] + title + " " + text[m.end(2):])
        return m.group(1)


class TestAnEditedFileIsReported(Fixture):
    def test_the_hand_edit_yields_the_finding(self):
        d = self.project()
        self.store(d)
        tid = self.edit_a_title(d)
        _, payload = self.lint(d)
        rows = self.drift(payload)
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual(rows[0]["rule"], "store-drift")
        self.assertIn(tid, rows[0]["message"])
        self.assertIn("a title nothing wrote", rows[0]["message"])
        self.assertEqual(rows[0]["file"], "perry/BOARD.md",
                         "the finding does not name the file that drifted")
        self.assertIsNotNone(rows[0]["line"],
                             "the finding does not point at the row")

    def test_a_row_the_store_never_saw_is_reported(self):
        """A row typed straight into the markdown is drift of the other kind:
        the file carries it and the store has no record of it."""
        d = self.project()
        self.store(d)
        board = d / "perry" / "BOARD.md"
        text = board.read_text()
        m = re.search(r"^\| TASK-\d+ \|.*\n", text, re.M)
        row = m.group(0).replace(re.search(r"TASK-\d+", m.group(0)).group(0),
                                 "TASK-901", 1)
        board.write_text(text[:m.end()] + row + text[m.end():])
        _, payload = self.lint(d)
        rows = self.drift(payload)
        self.assertEqual(len(rows), 1, rows)
        self.assertIn("TASK-901", rows[0]["message"])

    def test_it_is_warn_and_not_a_refusal(self):
        """`NS-01`'s posture, and `reconcile_drift`'s. An `error` would go red
        on every project that has ever hand-edited a board, on the first run
        after upgrading — and under ADR-004's gate would take `BOARD.md`
        read-only with it. `--strict` is how a project opts into the stronger
        reading."""
        d = self.project()
        self.store(d)
        self.edit_a_title(d)
        rc, payload = self.lint(d)
        self.assertTrue(all(f["severity"] == "warn" for f in self.drift(payload)))
        self.assertEqual(payload["errors"], 0)
        self.assertEqual(rc, 0, "drift refused the lint instead of reporting it")
        self.assertEqual(self.lint(d, "--strict")[0], 1,
                         "--strict does not promote the warning")


class TestAnUntouchedFileIsNotReported(Fixture):
    def test_a_store_written_from_the_file_is_clean(self):
        d = self.project()
        self.store(d)
        rc, payload = self.lint(d)
        self.assertEqual(self.drift(payload), [])
        self.assertEqual(rc, 0)

    def test_the_store_it_writes_is_not_reported_as_a_stray_file(self):
        """`perry-tasks write` puts `tasks.jsonl` inside the state root. A lint
        that then reported the store as an unclaimed file would make writing
        one impossible."""
        d = self.project()
        path = self.store(d)
        _, payload = self.lint(d)
        self.assertEqual([f for f in payload["findings"]
                          if path.name in f["file"]], [])


class TestNoStoreIsSilent(Fixture):
    """**The case that must be asserted rather than assumed.** `perry-tasks`
    writes nothing on an ordinary project, so this is the state every project
    is in today; a check that reported "clean" here would be answering a
    question it never asked."""

    def test_a_project_with_no_store_yields_nothing_at_all(self):
        d = self.project()
        self.assertFalse((d / "perry" / "tasks.jsonl").exists(),
                         "the fixture is not the no-store case")
        rc, payload = self.lint(d)
        self.assertEqual(self.drift(payload), [])
        self.assertEqual(rc, 0)

    def test_the_silence_is_the_missing_store_and_not_a_dead_check(self):
        """The same project, the same hand edit, twice — once without a store
        and once with. Silence then a finding is the only pair that proves the
        silence was the answer rather than the check failing to run."""
        d = self.project()
        self.edit_a_title(d)
        self.assertEqual(self.drift(self.lint(d)[1]), [],
                         "reported drift against a store that does not exist")
        self.store(d)
        self.edit_a_title(d, "a second title nothing wrote")
        self.assertNotEqual(self.drift(self.lint(d)[1]), [],
                            "the check is silent even with a store present")


class TestOneCheckMayNotKillTheLint(unittest.TestCase):
    """**Four reachable store states used to kill the whole lint**, rc 2 and no
    `--json` payload — found by a V4 round looking for the case the author had
    not listed.

    Only `json.JSONDecodeError` was caught. A store written as one JSON array —
    which is the ordinary way to get `.jsonl` wrong, `json.dump(records, f)` —
    and a bare `null` both PARSE and then die on `r.get`; a directory or an
    unreadable file die on the read itself.

    The function's own sibling guard states the rule this broke: *one check may
    not kill the lint*.
    """

    def project(self, write_store):
        import shutil
        import tempfile
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "perry").mkdir()
        (d / ".perry").mkdir()
        (d / ".perry" / "config.md").write_text("State root: perry\n")
        shutil.copy(ROOT / "perry" / "BOARD.md", d / "perry" / "BOARD.md")
        write_store(d / "perry" / "tasks.jsonl")
        return d

    def rules(self, d):
        import json
        import subprocess
        import sys
        proc = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-lint"),
             "--root", str(d), "--json"], capture_output=True, text=True)
        self.assertTrue(proc.stdout.strip(),
                        f"the lint produced no payload: {proc.stderr[-200:]}")
        return [f["rule"] for f in json.loads(proc.stdout)["findings"]]

    def test_a_whole_file_json_array_is_reported(self):
        import json
        d = self.project(lambda p: p.write_text(json.dumps([{"id": "T-1"}])))
        self.assertIn("store-unreadable", self.rules(d))

    def test_a_bare_scalar_line_is_reported(self):
        d = self.project(lambda p: p.write_text("null\n"))
        self.assertIn("store-unreadable", self.rules(d))

    def test_a_directory_where_the_store_should_be_is_reported(self):
        d = self.project(lambda p: p.mkdir())
        self.assertIn("store-unreadable", self.rules(d))

    def test_a_valid_store_still_checks(self):
        """The guard must not swallow the working case — a check that reports
        `unreadable` for everything is off, not safe."""
        import json
        d = self.project(lambda p: p.write_text(
            json.dumps({"id": "TASK-001", "title": "x"}) + "\n"))
        self.assertNotIn("store-unreadable", self.rules(d))


class TestTheMessageIsTrueOfTheFile(unittest.TestCase):
    def test_a_closed_task_is_not_called_a_row_the_file_carries(self):
        """`build()` includes CLOSED tasks from the event log, whose rows
        `done` removed — 63 of 95 on this project. Saying *"the file carries
        this row"* of a row the file does not contain was false for two-thirds
        of what that branch reported, with `line: null` and a remedy that does
        not apply."""
        import json
        import shutil
        import subprocess
        import sys
        import tempfile
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "perry").mkdir()
        (d / ".perry").mkdir()
        (d / ".perry" / "config.md").write_text("State root: perry\n")
        shutil.copy(ROOT / "perry" / "BOARD.md", d / "perry" / "BOARD.md")
        # A store holding only one row: every other derived task is "missing".
        (d / "perry" / "tasks.jsonl").write_text(
            json.dumps({"id": "TASK-001", "title": "x"}) + "\n")
        proc = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-lint"),
             "--root", str(d), "--json"], capture_output=True, text=True)
        for f in json.loads(proc.stdout)["findings"]:
            if "store has no record" in f["message"]:
                self.assertIsNotNone(
                    f["line"], f"claimed the file carries {f['message'][:40]!r} "
                               f"with no line — the board does not contain it")


if __name__ == "__main__":
    unittest.main()
