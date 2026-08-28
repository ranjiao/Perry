"""`pending hand-off` counted live board rows, and `done` removes the row.

So a design whose implementation tasks are all **finished** reported
`impl_refs: 0`, and `perry-state` turned that into "pending hand-off".
`DESIGN-004` is `bin/perry-task` itself — 3,300 lines shipping, seven close
events against its id — and Perry reported it as never handed off.

This is the trap `bin/perry-lint § check_verification` documents in its own
docstring, repeated in a second reader that did not know about it. Two readers,
one rule, one of them wrong: the defect this repository finds most often after
"a rule in prose that nothing implements".

Run: python3 tests/parallel test_design_handoff
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "viewer"))
import parsers as P  # noqa: E402

DOC = """# DESIGN-009 — a thing

> Status: locked 2026-08-01

## 1. Problem
x

## 6. Implementation plan
| Phase | Scope | Proposed PMO task(s) | Owner |
|---|---|---|---|
| A | x | TASK-900 | Coding Agent |
"""


class TestAClosedTaskStillCounts(unittest.TestCase):
    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        (self.dir / "design").mkdir()
        (self.dir / "design" / "DESIGN-009-a-thing.md").write_text(DOC)
        (self.dir / ".perry").mkdir()

    def event(self, **kw):
        (self.dir / ".perry" / "events.jsonl").write_text(
            json.dumps(kw) + "\n")

    def refs(self, project_root=None):
        docs = P.walk_design(self.dir, None,
                             project_root=project_root or self.dir)
        return docs[0].impl_refs

    def test_no_board_and_no_events_is_zero(self):
        self.assertEqual(self.refs(), 0)

    def test_a_closed_task_naming_the_design_counts(self):
        """The whole bug: this used to be 0 because the row was gone."""
        self.event(event="done", task="TASK-900",
                   next="implements DESIGN-009 phase A")
        self.assertEqual(self.refs(), 1)

    def test_a_design_nothing_mentions_stays_zero(self):
        """The signal has to keep meaning something — an event log that makes
        every design look handed off is not a fixed metric, it is a broken one
        in the other direction."""
        self.event(event="done", task="TASK-900", next="unrelated work")
        self.assertEqual(self.refs(), 0)

    def test_the_state_root_may_sit_under_the_project_root(self):
        """`.perry/` is anchored to the PROJECT root and `walk_design` receives
        the STATE root, which is `perry/` on this very repository. Passing the
        state root as both is what made the first fix report 0 anyway."""
        proj = self.dir
        state = proj / "perry"
        (state / "design").mkdir(parents=True)
        shutil.copy(proj / "design" / "DESIGN-009-a-thing.md",
                    state / "design" / "DESIGN-009-a-thing.md")
        self.event(event="done", task="TASK-900", next="DESIGN-009 phase A")
        docs = P.walk_design(state, None)      # no project_root: must walk up
        self.assertEqual(docs[0].impl_refs, 1)


class TestPerrysOwnDesignsReportTruthfully(unittest.TestCase):
    def test_the_write_side_design_is_not_pending_handoff(self):
        """`DESIGN-004` IS `bin/perry-task`. If this ever reads 0 again, the
        board-only count is back."""
        proc = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-state"), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        docs = json.loads(proc.stdout)["design"]["docs"]
        d4 = next(d for d in docs if d["id"] == "DESIGN-004")
        self.assertGreater(d4["impl_refs"], 0)


if __name__ == "__main__":
    unittest.main()
