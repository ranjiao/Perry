"""A design's implementation rows must be counted from a DECLARED edge.

Two rounds are recorded here and the second did not undo the first.

`ae505b3` fixed the original defect: `pending hand-off` counted live board
rows, and `done` REMOVES the row, so a design whose implementation tasks had
all finished reported `impl_refs: 0` and Perry called it never handed off.
`DESIGN-004` is `bin/perry-task` itself, shipping, reported as pending.

**TASK-139** found that the fix bought the property with the wrong currency.
It counted a SUBSTRING of each row's `id + title + next_action + evidence`,
plus every raw line of `.perry/events.jsonl`. So:

- prose counted as implementation. Measured on `b4799f9`, `DESIGN-001`
  reported `impl_refs=18` and all eighteen were rows that merely MENTIONED the
  id in a sentence — two of them `TASK-139`'s own dispatch events, the row
  filed to fix the count inflating it;
- the actual implementation did not count. `TASK-001`…`TASK-006`, all `done`
  at V3 with evidence, contributed zero, because they never wrote the id in
  any field.

A false positive had become a false NEGATIVE, which is worse: the first was
visible. The count now comes from `design_refs`, a field of the canonical store
(`bin/perry_store.py § STORED`), read out of `perry/tasks.jsonl` — which the
close path never empties, because `done` removes the row from the PROJECTION.

The two classes below are the two controls TASK-139 § Verification names, and
they pull against each other on purpose: one says prose must stop counting, the
other says closing a row must not stop it counting. A fix that satisfies only
one of them is the defect facing the other way.

Run: python3 tests/parallel test_design_handoff
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import pathlib
import shutil
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


class DesignFixture(unittest.TestCase):
    """A whole project in a temp dir.

    Nothing here reads the live repository. An earlier version of this file
    walked up to the host project's `.perry/events.jsonl`, so a PMO prose edit
    reddened the suite — the defect TASK-292 carries.
    """

    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        (self.dir / "design").mkdir()
        (self.dir / "design" / "DESIGN-009-a-thing.md").write_text(DOC)
        (self.dir / ".perry").mkdir()

    def store(self, *records):
        (self.dir / "tasks.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in records))

    def events(self, *objs):
        (self.dir / ".perry" / "events.jsonl").write_text(
            "".join(json.dumps(o) + "\n" for o in objs))

    def refs(self):
        docs = P.walk_design(self.dir, None, project_root=self.dir)
        return docs[0].impl_refs


class TestAClosedRowStillCounts(DesignFixture):
    """Control 2. `ae505b3`'s property, which must not regress."""

    def test_no_store_at_all_is_zero(self):
        self.assertEqual(self.refs(), 0)

    def test_a_closed_row_that_declares_the_design_counts(self):
        """The property `ae505b3` bought, kept — and now bought structurally.

        `status: done` is the whole point. Closing removes the row from
        `BOARD.md`; it does not remove the record, so the edge survives.
        """
        self.store({"id": "TASK-900", "status": "done",
                    "design_refs": ["DESIGN-009"]})
        self.assertEqual(self.refs(), 1)

    def test_it_survives_the_event_log_being_deleted(self):
        """Strictly stronger than the log scan it replaces.

        `bin/perry-task:42` calls `.perry/events.jsonl` "DERIVED AND
        DISPOSABLE" and says anything load-bearing that lives only there is a
        bug. Counting closed rows by scanning that log WAS such a thing:
        deleting a file the tool says may be deleted would have dropped every
        locked design back into `pending hand-off`. It must not any more.
        """
        self.store({"id": "TASK-900", "status": "done",
                    "design_refs": ["DESIGN-009"]})
        (self.dir / ".perry" / "events.jsonl").write_text("")
        self.assertEqual(self.refs(), 1)
        (self.dir / ".perry" / "events.jsonl").unlink()
        self.assertEqual(self.refs(), 1)

    def test_open_and_closed_rows_are_counted_alike(self):
        self.store({"id": "TASK-900", "status": "done",
                    "design_refs": ["DESIGN-009"]},
                   {"id": "TASK-901", "status": "in_progress",
                    "design_refs": ["DESIGN-009"]},
                   {"id": "TASK-902", "status": "dropped",
                    "design_refs": ["DESIGN-009"]})
        self.assertEqual(self.refs(), 3)


class TestProseDoesNotCount(DesignFixture):
    """Control 1. The mutation that would have caught the b4799f9 state."""

    def test_a_row_that_only_mentions_the_design_does_not_count(self):
        """TASK-139 § Verification 3, stated as it is stated there: a row whose
        `next_action` names a design it does not implement.

        This is the exact shape of all eighteen refs `DESIGN-001` carried.
        """
        self.store({"id": "TASK-901", "status": "in_progress",
                    "title": "why DESIGN-009 is wrong about caching",
                    "next_action": "read DESIGN-009 before starting",
                    "evidence": "see DESIGN-009 § 4",
                    "design_refs": []})
        self.assertEqual(self.refs(), 0)

    def test_a_mention_beside_a_real_edge_does_not_add_to_it(self):
        """The count is edges, not documents-that-say-the-word. One row that
        implements it and three that discuss it is one."""
        self.store({"id": "TASK-900", "status": "done",
                    "design_refs": ["DESIGN-009"]},
                   {"id": "TASK-901", "next_action": "DESIGN-009 DESIGN-009",
                    "design_refs": []},
                   {"id": "TASK-902", "title": "DESIGN-009", "design_refs": []},
                   {"id": "TASK-903", "evidence": "DESIGN-009"})
        self.assertEqual(self.refs(), 1)

    def test_prose_in_the_event_log_does_not_count(self):
        """The other half of the b4799f9 count: fifteen of `DESIGN-001`'s
        eighteen were raw log lines, and two of those were the dispatch events
        of the row filed to FIX the count. A metric that rises because the PMO
        wrote about the problem is not measuring the problem."""
        self.events(
            {"event": "next", "id": "TASK-901",
             "title": "a design back-reference lives in a cell DESIGN-009"},
            {"event": "done", "id": "TASK-902",
             "next": "implements DESIGN-009 phase A"},
            {"event": "summary", "id": "TASK-903", "to": "DESIGN-009"})
        self.assertEqual(self.refs(), 0)

    def test_an_id_that_is_a_prefix_of_another_does_not_bleed(self):
        """A substring match counted `DESIGN-0091` as `DESIGN-009`. An edge is
        an exact id."""
        self.store({"id": "TASK-900", "status": "done",
                    "design_refs": ["DESIGN-0091"]})
        self.assertEqual(self.refs(), 0)


def perry_task_module():
    spec = importlib.util.spec_from_loader(
        "perry_task",
        importlib.machinery.SourceFileLoader(
            "perry_task", str(ROOT / "bin" / "perry-task")))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestTheWriter(unittest.TestCase):
    """`perry-task design-link` — the only way the edge is meant to be set."""

    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        (self.dir / "design").mkdir(parents=True)
        (self.dir / "design" / "DESIGN-009-a-thing.md").write_text(DOC)
        (self.dir / "design" / "README.md").write_text("# not a design\n")
        self.mod = perry_task_module()

    def args(self, **kw):
        a = self.mod.Args()
        a.id = kw.get("id", "TASK-900")
        a.design = kw.get("design")
        a.clear = kw.get("clear", False)
        a.actor = "agent"
        a.dry_run = True
        return a

    def ctx(self, record):
        return {"state_root": self.dir, "project_root": self.dir,
                "tasks_by_id": {record["id"]: record}, "board": None}

    def test_known_design_ids_reads_the_filenames(self):
        """`README.md` is not a design, and the id is the part of a design's
        identity its freeform bilingual header cannot get wrong."""
        self.assertEqual(self.mod.known_design_ids(self.dir), {"DESIGN-009"})

    def test_it_refuses_a_design_with_no_document(self):
        """The field's whole value is that prose cannot fake it. An edge to a
        design that does not exist is a typo the count would read as shipped
        implementation."""
        record = {"id": "TASK-900", "status": "done", "design_refs": []}
        with self.assertRaises(self.mod.Refused) as caught:
            self.mod.cmd_design_link(self.args(design="DESIGN-404"),
                                     self.ctx(record))
        self.assertIn("DESIGN-404", str(caught.exception))

    def test_it_refuses_naming_no_design_at_all(self):
        record = {"id": "TASK-900", "status": "done", "design_refs": []}
        with self.assertRaises(self.mod.Refused):
            self.mod.cmd_design_link(self.args(), self.ctx(record))

    def test_it_refuses_a_no_op(self):
        """"Which designs does this row implement" must not have an answer
        that depends on how many times the flag was run."""
        record = {"id": "TASK-900", "status": "done",
                  "design_refs": ["DESIGN-009"]}
        with self.assertRaises(self.mod.Refused):
            self.mod.cmd_design_link(self.args(design="DESIGN-009"),
                                     self.ctx(record))


if __name__ == "__main__":
    unittest.main()
