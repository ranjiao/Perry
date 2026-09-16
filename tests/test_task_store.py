"""`bin/perry-tasks` — the store, and the split that is the design.

Phase 002's first slice (ADR-007, TASK-038). **It does not write yet**: it
builds the store from what exists and proves it can reproduce `BOARD.md`. A
store that cannot reproduce the document it replaces has already lost data,
which is the same posture `perry-migrate` takes.

Run: python3 tests/parallel test_task_store
"""

from __future__ import annotations

COVERS = (
    "bin/perry-tasks",
    "tests/printed_board.py",
    "tests/live_stores.py",
    "perry/tasks.jsonl",
    "perry/asks.jsonl",
    "perry/risks.jsonl",
    "perry/intake.jsonl",
    "perry/linkage.jsonl",
    "perry/okr.jsonl",
    ".perry/config.jsonl",
    ".perry/events.jsonl",
)

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin" / "perry-tasks"

from printed_board import put_printed_board  # noqa: E402
import live_stores  # noqa: E402

#: Computable from the stored twenty plus the event log. Storing any of them
#: is the "a stored value that is derived" defect, and keeping them computed is
#: why `perry-task/list` does not change shape — phase 002's `P002-O3-KR2`.
DERIVED = {"blocked_by", "blocks", "startable", "evidence_paths", "mode",
           "open", "status_text", "timeline", "updated"}


def run(*args, root=ROOT):
    return subprocess.run([sys.executable, str(TOOL), *args,
                           "--root", str(root)],
                          capture_output=True, text=True, cwd=ROOT)


class TestTheSplitIsTheDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # TASK-237 3c: this repository holds no `BOARD.md`, and `build`
        # derives FROM one, so it runs on a copy carrying the board the stores
        # print (`tests/printed_board.py`).
        cls.tmp = pathlib.Path(tempfile.mkdtemp())
        # USER-942, and NO store. `build` reads the BOARD and the EVENT LOG
        # (`bin/perry-tasks § build`) and opens no `*.jsonl` store, so the
        # copied stores were read by nothing here; `events.jsonl` is kept
        # because `build` does read it. Measured: copying no stores leaves
        # both cases below green, and never copying the event log leaves them
        # green too — they are insensitive to it, and it is copied because it
        # is read, not because a case here would notice.
        live_stores.copy_state(cls.tmp, stores=False)
        put_printed_board(cls.tmp / "perry")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_no_derived_field_is_stored(self):
        mod_stored = set(json.loads(run("build", root=self.tmp).stdout)["sample"])
        overlap = mod_stored & DERIVED
        self.assertEqual(overlap, set(),
                         f"stored a value that is derived: {overlap}")

    def test_every_stored_field_appears_in_a_record(self):
        out = json.loads(run("build", root=self.tmp).stdout)
        self.assertEqual(len(out["sample"]), out["stored_fields"])


class TestTheStoreReproducesTheBoard(unittest.TestCase):
    def copy(self):
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        # **No store.** `perry/tasks.jsonl` exists in this repository now —
        # TASK-089 made it the write target — so copying `perry/` inherits one,
        # and a test about the no-store case silently became a with-store test.
        # Three of them failed the day it was tracked, which is the transition
        # working rather than a regression. `stores=False` says it, and drops
        # the six others this case never read (it was `skip=("tasks.jsonl",)`,
        # which left them behind).
        #
        # `.perry/events.jsonl` IS read here, and is the one part of this copy
        # a case can feel: `write --from-board` recovers rows the board no
        # longer carries from the event log, and
        # `test_it_carries_closed_tasks_the_board_no_longer_holds` goes red
        # without it (109 records, 109 board rows).
        live_stores.copy_state(d, stores=False)
        # TASK-237 3c: this repository holds no `BOARD.md`; the copy gets the
        # board its stores print, which is what these imports would read on a
        # project that still holds one (`tests/printed_board.py`).
        put_printed_board(d / "perry")
        return d

    def test_verify_passes_against_a_store_it_did_not_just_build(self):
        d = self.copy()
        self.assertEqual(run("write", "--from-board", root=d).returncode, 0)
        proc = run("verify", root=d)
        self.assertEqual(proc.returncode, 0, proc.stdout[-500:])
        out = json.loads(proc.stdout)
        self.assertEqual(out["rows_missing_from_store"], [])
        self.assertEqual(out["mismatch_count"], 0)

    def test_it_carries_closed_tasks_the_board_no_longer_holds(self):
        """`done` REMOVES the row, so a store built from the board alone loses
        every finished task — the trap `check_verification` documents and
        `walk_design` repeated."""
        d = self.copy()
        run("write", "--from-board", root=d)
        out = json.loads(run("verify", root=d).stdout)
        self.assertGreater(out["records"], out["board_rows"],
                           "the store holds no more than the live board does, "
                           "so closed work was dropped")

    def test_a_hand_edit_after_the_write_is_reported(self):
        """**`verify` used to compare the store against the board it had just
        been built from — a tautology that could never fail.** This test caught
        it: the planted hand edit passed, because both sides saw the same
        edited value. The store is read from disk now, which is the only thing
        independent of the board.
        """
        import re
        d = self.copy()
        run("write", "--from-board", root=d)
        board = d / "perry" / "BOARD.md"
        board.write_text(re.sub(
            r"^(\| TASK-\d+ \| )([^|]+)", r"\1a title nothing wrote",
            board.read_text(), count=1, flags=re.M))
        self.assertEqual(run("verify", root=d).returncode, 1,
                         "a hand edit went unreported")

    def test_verifying_with_no_store_is_not_a_pass(self):
        """Exit 2, not 0. "Nothing to verify" and "verified" are different
        answers and a consumer branching on rc must be able to tell them
        apart."""
        d = self.copy()
        self.assertEqual(run("verify", root=d).returncode, 2)


class TestItWritesNothingYet(unittest.TestCase):
    def test_build_and_verify_touch_no_file(self):
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        # **`tasks.jsonl` and no other store**, and this is the one site here
        # that reads one: `verify` loads the store FROM DISK
        # (`bin/perry-tasks § verify`), and with no store it exits 2 at the
        # door — which would make "build and verify touch no file" true of a
        # command that did nothing. The other six stores are opened by
        # neither verb.
        live_stores.copy_state(d, stores=("tasks",))
        before = {p: p.read_bytes() for p in d.rglob("*") if p.is_file()}
        run("build", root=d)
        run("verify", root=d)
        after = {p: p.read_bytes() for p in d.rglob("*") if p.is_file()}
        self.assertEqual(before, after, "build/verify wrote to the project")


if __name__ == "__main__":
    unittest.main()
