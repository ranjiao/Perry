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

import task_actor

COVERS = ("bin/perry-task", "bin/perry_store.py")

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
sys.path.insert(0, str(ROOT / "tests"))
import inproc  # noqa: E402
import parsers as P  # noqa: E402
import store_fixture  # noqa: E402

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

    def test_it_collapses_a_repeated_id(self):
        """**Mutation M9.** One design named twice is one edge, not two — the
        count is edges, and a doubled id would report a design as twice as
        implemented as it is."""
        record = {"id": "TASK-900", "status": "done", "design_refs": []}
        captured = {}
        self.mod.commit = lambda *a, **k: captured.update(event=a[4]) or {}
        out = self.mod.cmd_design_link(
            self.args(design="DESIGN-009, DESIGN-009, design-009"),
            self.ctx(record))
        self.assertEqual(out["design_refs"], ["DESIGN-009"])

    def test_it_refuses_a_no_op(self):
        """"Which designs does this row implement" must not have an answer
        that depends on how many times the flag was run."""
        record = {"id": "TASK-900", "status": "done",
                  "design_refs": ["DESIGN-009"]}
        with self.assertRaises(self.mod.Refused):
            self.mod.cmd_design_link(self.args(design="DESIGN-009"),
                                     self.ctx(record))


class TestTheFieldIsDeclared(unittest.TestCase):
    """`design_refs` must be in `perry_store.STORED`, not merely present in
    whatever dict happened to be written.

    **The mutation that caught this.** Deleting it from `STORED` left every
    round-trip test green, because the carry re-adds the key to the record dict
    afterwards and `store_text` serialises whatever keys it finds. What is lost
    is the TYPE CHECK: `validate_records` skips fields it does not know, so an
    undeclared field is a field nothing validates — a string where a list
    belongs would reach `walk_design` and be iterated character by character.
    """

    def setUp(self):
        sys.path.insert(0, str(ROOT / "bin"))
        import perry_store
        self.store = perry_store

    def test_it_is_declared(self):
        self.assertIn("design_refs", self.store.STORED)

    def test_a_string_where_a_list_belongs_is_reported(self):
        good, findings = self.store.validate_records(
            [{"id": "TASK-900", "design_refs": "DESIGN-009"}])
        self.assertEqual(good, [])
        self.assertEqual(len(findings), 1)
        self.assertIn("design_refs", findings[0]["message"])
        self.assertIn("list of strings", findings[0]["message"])

    def test_a_list_of_strings_is_accepted(self):
        good, findings = self.store.validate_records(
            [{"id": "TASK-900", "design_refs": ["DESIGN-009"]}])
        self.assertEqual(findings, [])
        self.assertEqual(good[0]["design_refs"], ["DESIGN-009"])

    def test_record_builds_the_field_as_a_list(self):
        """**Mutation M11.** `record()` rebuilds each record in `STORED` key
        order and needs the list branch, or `design_refs` is written as the
        empty STRING.

        The round-trip tests cannot see it: `store_records` overwrites the
        value from the canonical store immediately afterwards — but only when
        the store parses. On the malformed-store path the carry is skipped and
        this is the value that gets written, and a `""` where a list belongs is
        the exact shape `validate_records` rejects.
        """
        built = self.store.record({"id": "TASK-900",
                                   "design_refs": ["DESIGN-009"]}, 0)
        self.assertEqual(built["design_refs"], ["DESIGN-009"])

    def test_record_defaults_the_field_to_an_empty_list(self):
        built = self.store.record({"id": "TASK-900"}, 0)
        self.assertEqual(built["design_refs"], [],
                         "a missing edge set is [], never the empty string")

    def test_a_record_written_before_the_field_existed_stays_valid(self):
        """Additive, exactly as `summary` was under TASK-106. No migration."""
        good, findings = self.store.validate_records(
            [{"id": "TASK-900", "title": "written in August"}])
        self.assertEqual(findings, [])
        self.assertEqual(good[0].get("design_refs"), None)


class TestTheEdgeSurvivesTheNextWrite(store_fixture.StoreFixture):
    """The edge is store-only, and `store_records` DERIVES the store from the
    board on every mutating command.

    So without an explicit carry, `design_refs` would be rebuilt as `[]` by the
    next unrelated `perry-task` call on any other row — the field would look
    like it worked and would empty itself the first time somebody moved a
    different task. `summary` has the same shape and the same guard beside it.

    This is the failure mode a test that only calls `design-link` and reads
    back cannot see.
    """

    def perry_task(self, root, *argv):
        # **In-process** (TASK-368). Measured in this tree before converting:
        # 87.8% of this module is children and the boundary is 82.5% of the
        # module. It shares `store_fixture.write_store`, which this row
        # converted, so these two sites go with it — a module left half on
        # `subprocess` is where TASK-402's shared-helper rounds went wrong.
        proc = inproc.run("perry-task", task_actor.owned([*argv, "--root", str(root)], 'test_design_handoff'))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc

    def refs_of(self, root, tid):
        for line in (root / "perry" / "tasks.jsonl").read_text().splitlines():
            if line.strip() and json.loads(line)["id"] == tid:
                return json.loads(line).get("design_refs")
        self.fail("%s left the store" % tid)

    def test_a_whole_store_rebuild_does_not_clear_the_edge(self):
        """**The mutation that caught the weak test beside this one.**

        `perry-tasks write --from-board` re-derives EVERY record through
        `store_records`, which is the only path where the explicit carry is
        load-bearing. The neighbouring test cannot reach it: `commit` copies
        every non-subject row out of the store byte-for-field, so an unrelated
        write never rebuilds the linked row at all. Removing the carry left
        that test green and this one red.
        """
        root = self.project(with_store=True)
        (root / "perry" / "design").mkdir()
        (root / "perry" / "design" / "DESIGN-009-a-thing.md").write_text(DOC)
        self.perry_task(root, "design-link", "TASK-001",
                        "--design", "DESIGN-009")

        proc = inproc.run("perry-tasks",
                          ["write", "--from-board", "--root", str(root)])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.refs_of(root, "TASK-001"), ["DESIGN-009"],
                         "a store rebuild derived the record from the board "
                         "and the board has no column for the edge")

    def test_it_can_be_linked_with_the_event_log_deleted(self):
        """**The mutation that caught the second weak test.**

        `commit`'s off-board branch only fires when the projection cannot be
        rebuilt at all. With the log present, `store_records` reconstructs a
        terminal row from the `done` event, so the branch is never reached and
        removing it stays green. Delete the log — which `bin/perry-task:42`
        says is allowed at any time — and it is the only path left.
        """
        root = self.project(with_store=True)
        (root / "perry" / "design").mkdir()
        (root / "perry" / "design" / "DESIGN-009-a-thing.md").write_text(DOC)
        self.perry_task(root, "done", "TASK-001", "--rung", "V1",
                        "--evidence", "evidence/x.md")
        (root / ".perry" / "events.jsonl").write_text("")

        self.perry_task(root, "design-link", "TASK-001",
                        "--design", "DESIGN-009")
        self.assertEqual(self.refs_of(root, "TASK-001"), ["DESIGN-009"])

    def test_linking_does_not_move_the_record_in_the_store(self):
        """**Mutation M8**, the `in_place` clause.

        `design_refs` is store-only metadata, so writing it must not turn a
        one-field edit into a whole-store reorder by moving the record to the
        last JSONL line. `summary` carries the same rule for the same reason:
        a store whose lines reshuffle turns every write into a whole-file diff.
        """
        root = self.project(with_store=True)
        (root / "perry" / "design").mkdir()
        (root / "perry" / "design" / "DESIGN-009-a-thing.md").write_text(DOC)

        def ids():
            return [json.loads(ln)["id"] for ln
                    in (root / "perry" / "tasks.jsonl").read_text().splitlines()
                    if ln.strip()]

        before = ids()
        self.assertEqual(before[0], "TASK-001", "fixture assumption")
        self.perry_task(root, "design-link", "TASK-001",
                        "--design", "DESIGN-009")
        self.assertEqual(ids(), before,
                         "the edit reordered the store; a field write is not a "
                         "reason to move history")

    def test_an_unrelated_write_does_not_clear_the_edge(self):
        root = self.project(with_store=True)
        (root / "perry" / "design").mkdir()
        (root / "perry" / "design" / "DESIGN-009-a-thing.md").write_text(DOC)

        self.perry_task(root, "design-link", "TASK-001",
                        "--design", "DESIGN-009")
        self.assertEqual(self.refs_of(root, "TASK-001"), ["DESIGN-009"])

        # A write against a DIFFERENT row. Nothing about TASK-001 changed.
        self.perry_task(root, "next", "TASK-002", "--next", "something else")
        self.assertEqual(self.refs_of(root, "TASK-001"), ["DESIGN-009"],
                         "an unrelated write rebuilt the store from the board "
                         "and dropped the edge")

    def test_a_row_that_has_already_closed_can_still_be_linked(self):
        """The historical case, and the one the whole row is about.

        `DESIGN-001`'s six implementation rows closed months before the field
        existed. If the writer could only reach rows still on the board, the
        edge would be unwritable for exactly the designs whose hand-off is in
        question. `cell_writer` refuses an off-board row on purpose; this verb
        must not.
        """
        root = self.project(with_store=True)
        (root / "perry" / "design").mkdir()
        (root / "perry" / "design" / "DESIGN-009-a-thing.md").write_text(DOC)

        self.perry_task(root, "done", "TASK-001", "--rung", "V1",
                        "--evidence", "evidence/x.md")
        # The board `perry-tasks board` prints (TASK-262 round 4a): the held
        # file is not re-rendered by `done` any more.
        board = inproc.run("perry-tasks", ["board", "--root", str(root)]).stdout
        self.assertIn("| TASK-002 |", board, "control: the board printed rows")
        self.assertFalse(
            [ln for ln in board.splitlines() if ln.startswith("| TASK-001 |")],
            "the row must be off the board before this proves anything")

        self.perry_task(root, "design-link", "TASK-001",
                        "--design", "DESIGN-009")
        self.assertEqual(self.refs_of(root, "TASK-001"), ["DESIGN-009"])

        docs = P.walk_design(root / "perry", None, project_root=root)
        by_id = {d.id: d for d in docs}
        self.assertEqual(by_id["DESIGN-009"].impl_refs, 1)

    def test_closing_the_linked_row_does_not_clear_the_edge(self):
        """The lifecycle event the row was FILED about. `done` removes the
        line from `BOARD.md`; the record and its edge must remain."""
        root = self.project(with_store=True)
        (root / "perry" / "design").mkdir()
        (root / "perry" / "design" / "DESIGN-009-a-thing.md").write_text(DOC)

        self.perry_task(root, "design-link", "TASK-001",
                        "--design", "DESIGN-009")
        self.perry_task(root, "done", "TASK-001", "--rung", "V1",
                        "--evidence", "evidence/x.md")

        # The ROW, not the string: `TASK-002` still names it in `Depends on`,
        # which is the projection doing its job, not the row surviving.
        board = inproc.run("perry-tasks", ["board", "--root", str(root)]).stdout
        self.assertIn("| TASK-002 |", board, "control: the board printed rows")
        self.assertFalse(
            [ln for ln in board.splitlines() if ln.startswith("| TASK-001 |")],
            "the fixture must actually exercise row removal")
        self.assertEqual(self.refs_of(root, "TASK-001"), ["DESIGN-009"])

        docs = P.walk_design(root / "perry", None, project_root=root)
        by_id = {d.id: d for d in docs}
        self.assertEqual(by_id["DESIGN-009"].impl_refs, 1,
                         "a closed row must still count — ae505b3's property")


if __name__ == "__main__":
    unittest.main()
