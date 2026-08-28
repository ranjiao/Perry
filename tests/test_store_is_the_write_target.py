"""`perry-task` writes `perry/tasks.jsonl`, and `BOARD.md` is rendered from it.

TASK-089, phase 002, ADR-007's first slice. The recoverable pair is **store +
journal** now: ordinary failures roll back and crash recovery completes the
transaction, with `BOARD.md` and the event log as derived artefacts.

**The acceptance is one command, run after every kind of write:**
`perry-tasks diff` reports `identical: true`. It is the only check that grades
the thing that could actually go wrong — the store and the document disagreeing
— and it is a byte comparison, so there is no judgement in it to get wrong.

The two decisions TASK-088 measured and handed here get a suite each:

  decision 1  a `Status` cell the store cannot hold (`**迁移 done，占比目标
              not_started**`) refuses writes to ITS ROW, and to no other row.
  decision 2  authored row order is RECORDED (`order`), so the first render
              does not reorder somebody's board.

Run: python3 tests/parallel test_store_is_the_write_target
"""

from __future__ import annotations

import contextlib
import io
import json
import importlib.machinery
import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

from gate import GATE_OFF   # tests/gate.py — why this fixture opts out

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASK = ROOT / "bin" / "perry-task"
TASKS = ROOT / "bin" / "perry-tasks"


def task_module():
    spec = importlib.util.spec_from_loader(
        "perry_task_task089", importlib.machinery.SourceFileLoader(
            "perry_task_task089", str(TASK)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

BOARD = """# Board — T

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-001 | First | User | not_started | — | — |
| TASK-002 | Second | User | in_progress | — | — |
| TASK-003 | Third | User | **迁移 done，占比目标 not_started** | — | — |
| TASK-004 | Fourth | User | not_started | — | — |

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
"""


class Project:
    """A throwaway project the writer can write into."""

    def __init__(self, case, board: str = BOARD, seed_store: bool = True):
        self.root = pathlib.Path(tempfile.mkdtemp()).resolve()
        case.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n" + GATE_OFF,
            encoding="utf-8")
        (self.root / "BOARD.md").write_text(board, encoding="utf-8")
        if seed_store:
            proc = subprocess.run(
                [sys.executable, str(TASKS), "write", "--from-board", "--root",
                 str(self.root)], capture_output=True, text=True)
            if proc.returncode:
                raise AssertionError(proc.stdout + proc.stderr)

    ADD_DEFAULTS = ("--deliverable", "a thing that exists afterwards",
                    "--verification", "the suite is green")

    def task(self, *argv) -> tuple[int, dict | str]:
        if argv and argv[0] == "add" and "--title" in argv:
            argv = (*argv, *self.ADD_DEFAULTS)
        r = subprocess.run([sys.executable, str(TASK), *argv,
                            "--root", str(self.root), "--json"],
                           capture_output=True, text=True)
        try:
            return r.returncode, json.loads(r.stdout or "{}")
        except json.JSONDecodeError:
            return r.returncode, r.stdout + r.stderr

    def tasks(self, *argv) -> tuple[int, str]:
        r = subprocess.run([sys.executable, str(TASKS), *argv,
                            "--root", str(self.root)],
                           capture_output=True, text=True)
        return r.returncode, r.stdout

    def store(self) -> list[dict]:
        p = self.root / "tasks.jsonl"
        if not p.exists():
            return []
        return [json.loads(l) for l in
                p.read_text(encoding="utf-8").split("\n") if l.strip()]

    def record(self, tid: str) -> dict:
        return next(r for r in self.store() if r["id"] == tid)

    def board(self) -> str:
        return (self.root / "BOARD.md").read_text(encoding="utf-8")

    def rows_of(self, heading: str) -> list[str]:
        """The ids of the rows under one heading, in the order they appear."""
        out, inside = [], False
        for line in self.board().split("\n"):
            if line.startswith("## "):
                inside = line[3:].strip().startswith(heading)
                continue
            if inside and line.startswith("| TASK-"):
                out.append(line.split("|")[1].strip())
        return out


class Fixture(unittest.TestCase):
    def diff_is_identical(self, p: Project, why: str = "") -> dict:
        """**The acceptance.** `perry-tasks diff` byte-compares the board on
        disk against the board the store renders."""
        rc, out = p.tasks("diff")
        report = json.loads(out)
        self.assertTrue(report.get("identical"),
                        f"{why}: the store and the rendered board disagree — "
                        f"{json.dumps(report.get('first_difference'), ensure_ascii=False)}")
        self.assertEqual(rc, 0)
        return report


class TestEveryWriteLeavesTheStoreAndTheBoardAgreeing(Fixture):
    """One assertion, after each shape of write there is.

    Split per subcommand rather than looped, so a failure names the write that
    broke it instead of the first one in a list."""

    def project(self) -> Project:
        # `TASK-003` carries the cell decision 1 refuses on, and every write
        # below is aimed at some OTHER row — which is the point: the board
        # keeps a row Perry cannot classify and the rest of it stays writable.
        return Project(self)

    def test_add(self):
        p = self.project()
        code, out = p.task("add", "--title", "New", "--priority", "P1")
        self.assertEqual(code, 0, out)
        self.diff_is_identical(p, "after add")

    def test_start(self):
        p = self.project()
        self.assertEqual(p.task("start", "TASK-001")[0], 0)
        self.assertEqual(p.record("TASK-001")["status"], "in_progress")
        self.diff_is_identical(p, "after start")

    def test_status(self):
        p = self.project()
        self.assertEqual(p.task("status", "TASK-002", "--status", "review")[0], 0)
        self.assertEqual(p.record("TASK-002")["status"], "review")
        self.diff_is_identical(p, "after status")

    def test_next_and_retitle(self):
        p = self.project()
        self.assertEqual(p.task("next", "TASK-001", "--next", "ship it")[0], 0)
        self.assertEqual(p.task("retitle", "TASK-001", "--title", "Renamed")[0], 0)
        self.assertEqual(p.record("TASK-001")["title"], "Renamed")
        self.assertEqual(p.record("TASK-001")["next_action"], "ship it")
        self.diff_is_identical(p, "after next + retitle")

    def test_prioritize(self):
        p = self.project()
        self.assertEqual(p.task("prioritize", "TASK-001", "--priority", "P2")[0], 0)
        self.assertEqual(p.record("TASK-001")["priority"], "P2")
        self.diff_is_identical(p, "after prioritize")

    def test_done(self):
        p = self.project()
        code, out = p.task("done", "TASK-002", "--evidence", "BOARD.md")
        self.assertEqual(code, 0, out)
        self.assertNotIn("| TASK-002 |", p.board(), "the row did not leave")
        self.assertEqual(p.record("TASK-002")["status"], "done",
                         "a closed row must survive in the store — the board "
                         "no longer holds it")
        self.diff_is_identical(p, "after done")

    def test_drop(self):
        p = self.project()
        self.assertEqual(p.task("drop", "TASK-004", "--reason", "no")[0], 0)
        self.diff_is_identical(p, "after drop")

    def test_a_write_to_a_section_that_is_not_a_task_table(self):
        """`ask` writes `## User Input Queue`, which the store does not hold.

        It still goes through `commit()`, so it still writes the store and
        re-renders the board — and the section it touched must come back
        untouched, because the renderer must not treat it as a task table."""
        p = self.project()
        self.assertEqual(p.task("ask", "--needed", "a decision")[0], 0)
        self.assertIn("a decision", p.board())
        self.diff_is_identical(p, "after ask")


class TestOneTaskTableDefinition(Fixture):
    SECOND_TABLE = BOARD.replace(
        "| TASK-004 | Fourth | User | not_started | — | — |",
        "| TASK-004 | Fourth | User | not_started | — | — |\n\n"
        "Prose between tables.\n\n### Deferred\n\n"
        "| ID | Title | Owner | Status | Next action | Evidence |\n"
        "|---|---|---|---|---|---|\n"
        "| TASK-005 | Fifth | User | not_started | — | — |", 1)

    def test_a_second_table_after_prose_is_stored_and_rendered_losslessly(self):
        p = Project(self, self.SECOND_TABLE)
        code, out = p.task("next", "TASK-005", "--next", "kept in the store")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.record("TASK-005")["next_action"], "kept in the store")
        self.assertNotIn("ID", [r["id"] for r in p.store()],
                         "the repeated markdown header became a task record")
        report = self.diff_is_identical(p)
        self.assertEqual(report["rows_verbatim"], [])

    def test_widening_preserves_both_tables_and_targets_the_second_row(self):
        p = Project(self, self.SECOND_TABLE.replace(
            "**迁移 done，占比目标 not_started**", "not_started"))
        code, out = p.task("depends", "TASK-005", "--on", "TASK-001")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.record("TASK-005")["depends_on"], ["TASK-001"])
        self.assertEqual(p.record("TASK-001")["depends_on"], [])
        self.assertEqual(p.board().count("| ID | Title | Owner | Status | Next action | Evidence | Depends on |"), 2)
        self.assertNotIn("ID", [r["id"] for r in p.store()])
        self.diff_is_identical(p)

    def test_duplicate_ids_refuse_even_a_non_task_mutation_and_direct_import(self):
        duplicate = self.SECOND_TABLE.replace("TASK-005", "TASK-001")
        p = Project(self, duplicate, seed_store=False)
        before = p.board()
        code, out = p.task("ask", "--needed", "a separate decision")
        self.assertEqual(code, 1, out)
        self.assertIn("duplicate task ids", out["refused"])
        self.assertEqual(p.board(), before)
        proc = subprocess.run(
            [sys.executable, str(TASKS), "write", "--from-board", "--root",
             str(p.root)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("duplicate task ids", proc.stderr)
        self.assertFalse((p.root / "tasks.jsonl").exists())


class TestCanonicalRecovery(unittest.TestCase):
    def files(self):
        root = pathlib.Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        a, b = root / "tasks.jsonl", root / "journal.md"
        a.write_text("old store\n"); b.write_text("old journal\n")
        return root, a, b

    def test_a_second_rename_failure_rolls_back_and_cleans_every_temp(self):
        mod = task_module()
        root, store, journal = self.files()
        real = mod.os.replace

        def fail_journal(src, dst):
            if pathlib.Path(dst) == journal:
                raise PermissionError("forced journal replacement failure")
            return real(src, dst)

        mod.os.replace = fail_journal
        try:
            with self.assertRaises(mod.Refused) as caught:
                mod.replace_canonical_pair(
                    root, [(store, "new store\n"), (journal, "new journal\n")])
        finally:
            mod.os.replace = real
        self.assertIn("rolled back", str(caught.exception))
        self.assertEqual(store.read_text(), "old store\n")
        self.assertEqual(journal.read_text(), "old journal\n")
        self.assertFalse((root / mod.TRANSACTION_FILE).exists())
        self.assertEqual(list(root.glob("*" + ".t" + "mp")), [])

    def test_a_crash_between_renames_is_completed_on_recovery(self):
        mod = task_module()
        root, store, journal = self.files()
        real = mod.os.replace

        def crash_on_journal(src, dst):
            if pathlib.Path(dst) == journal:
                raise SystemExit("simulated process death")
            return real(src, dst)

        mod.os.replace = crash_on_journal
        try:
            with self.assertRaises(SystemExit):
                mod.replace_canonical_pair(
                    root, [(store, "new store\n"), (journal, "new journal\n")])
        finally:
            mod.os.replace = real
        self.assertEqual(store.read_text(), "new store\n")
        self.assertEqual(journal.read_text(), "old journal\n")
        self.assertEqual(mod.recover_transaction(root), "completed")
        self.assertEqual(journal.read_text(), "new journal\n")
        self.assertFalse((root / mod.TRANSACTION_FILE).exists())
        self.assertEqual(list(root.glob("*" + ".t" + "mp")), [])

    def test_a_stage_failure_is_a_concise_refusal_and_leaves_no_temp(self):
        mod = task_module()
        root, store, journal = self.files()
        real = mod.lib.stage
        mod.lib.stage = lambda *_args, **_kw: (_ for _ in ()).throw(
            PermissionError("forced stage failure"))
        try:
            with self.assertRaises(mod.Refused) as caught:
                mod.replace_canonical_pair(root, [(store, "new"), (journal, "new")])
        finally:
            mod.lib.stage = real
        self.assertIn("Nothing was written", str(caught.exception))
        self.assertEqual(list(root.glob("*" + ".t" + "mp")), [])

    def test_replacements_preserve_existing_modes(self):
        mod = task_module()
        root, store, journal = self.files()
        os.chmod(store, 0o644); os.chmod(journal, 0o640)
        mod.replace_canonical_pair(root, [(store, "new"), (journal, "new")])
        self.assertEqual(store.stat().st_mode & 0o777, 0o644)
        self.assertEqual(journal.stat().st_mode & 0o777, 0o640)

    def test_commit_routes_the_real_command_through_the_recovery_boundary(self):
        p = Project(self, BOARD.replace(
            "**迁移 done，占比目标 not_started**", "not_started"))
        mod = task_module()
        before = p.board()
        before_store = (p.root / "tasks.jsonl").read_bytes()
        calls = []
        real = mod.replace_canonical_pair

        def stop_at_boundary(state_root, changes):
            calls.append((state_root, changes))
            raise mod.Refused("transaction boundary reached")

        mod.replace_canonical_pair = stop_at_boundary
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                code = mod.main([
                    "start", "TASK-001", "--root", str(p.root), "--json"
                ])
        finally:
            mod.replace_canonical_pair = real

        self.assertEqual(code, 1)
        self.assertEqual(len(calls), 1,
                         "commit bypassed the recoverable pair helper")
        changes = calls[0][1]
        self.assertEqual(len(changes), 2)
        self.assertIn(p.root / "tasks.jsonl", [path for path, _text in changes])
        journal = next(path for path, _text in changes
                       if path.name != "tasks.jsonl")
        self.assertEqual(journal.parent.parent.name, "journal")
        self.assertEqual(p.board(), before)
        self.assertEqual((p.root / "tasks.jsonl").read_bytes(), before_store)
        self.assertFalse((p.root / ".perry" / "events.jsonl").exists())


class TestStoreEditsRemainAuthoritativeAfterTask090(Fixture):
    def test_an_unrelated_write_preserves_and_renders_the_store_edit(self):
        p = Project(self, BOARD.replace(
            "**迁移 done，占比目标 not_started**", "not_started"))
        self.assertEqual(p.task("start", "TASK-001")[0], 0)
        records = p.store()
        records[0]["owner"] = "Store-only owner"
        (p.root / "tasks.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
        before = (p.root / "tasks.jsonl").read_bytes()
        code, out = p.task("ask", "--needed", "unrelated")
        self.assertEqual(code, 0, out)
        self.assertEqual((p.root / "tasks.jsonl").read_bytes(), before)
        self.assertIn("Store-only owner", p.board())

    def test_a_store_only_created_edit_is_preserved(self):
        p = Project(self, BOARD.replace(
            "**迁移 done，占比目标 not_started**", "not_started"))
        code, added = p.task("add", "--title", "Tool-created", "--priority", "P0")
        self.assertEqual(code, 0, added)
        records = p.store()
        next(r for r in records if r["id"] == added["id"])["created"] = \
            "1999-01-01T00:00:00"
        (p.root / "tasks.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
        before = (p.root / "tasks.jsonl").read_bytes()
        code, out = p.task("ask", "--needed", "unrelated")
        self.assertEqual(code, 0, out)
        self.assertEqual((p.root / "tasks.jsonl").read_bytes(), before)


class TestTheStoreIsWhatIsWritten(Fixture):
    def test_the_write_names_the_existing_canonical_store(self):
        p = Project(self)
        before = p.store()
        self.assertTrue(before)
        code, out = p.task("start", "TASK-001")
        self.assertEqual(code, 0, out)
        self.assertTrue((p.root / "tasks.jsonl").exists())
        self.assertEqual(out["store"], str(p.root / "tasks.jsonl"))
        self.assertEqual(out["records"], len(p.store()))

    def test_a_dry_run_writes_nothing_and_still_plans_the_store(self):
        p = Project(self)
        before = {x: x.read_bytes() for x in p.root.rglob("*") if x.is_file()}
        code, out = p.task("start", "TASK-001", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("store", out)
        after = {x: x.read_bytes() for x in p.root.rglob("*") if x.is_file()}
        self.assertEqual(before, after, "a dry run wrote to the project")

    #: A `Depends on` cell spelled in the project's own punctuation. The store
    #: holds a LIST; only `perry_store.cell_text` turns it back into a cell,
    #: and it joins with `", "`. So these bytes cannot survive a render, and
    #: the board carrying them after a write is proof the row was copied.
    CJK_DEPENDS = BOARD.replace(
        "| ID | Title | Owner | Status | Next action | Evidence |\n"
        "|---|---|---|---|---|---|\n"
        "| TASK-001 | First",
        "| ID | Title | Owner | Status | Next action | Evidence | Depends on |\n"
        "|---|---|---|---|---|---|---|\n"
        "| TASK-001 | First", 1).replace(
        "| TASK-001 | First | User | not_started | — | — |",
        "| TASK-001 | First | User | not_started | — | — | TASK-002、TASK-004 |"
    ).replace(
        "| TASK-002 | Second | User | in_progress | — | — |",
        "| TASK-002 | Second | User | in_progress | — | — |  |").replace(
        "| TASK-003 | Third | User | **迁移 done，占比目标 not_started** | — | — |",
        "| TASK-003 | Third | User | **迁移 done，占比目标 not_started** | — | — |  |"
    ).replace(
        "| TASK-004 | Fourth | User | not_started | — | — |",
        "| TASK-004 | Fourth | User | not_started | — | — |  |")

    def test_the_board_is_rendered_from_the_store_and_not_copied(self):
        """**The half `diff` cannot prove.** A `commit()` that wrote
        `board.text()` and the store side by side would pass every byte
        comparison above, because in this slice the record is still derived
        from the board — TASK-090 is what cuts that last strand.

        So the proof has to be a cell whose STORED form cannot reproduce its
        written bytes. `Depends on` is one: the store holds a list, and
        `perry_store.cell_text` is the only thing that turns a list back into a
        cell. A board still spelling it `TASK-002、TASK-004` after a write was
        copied, not rendered."""
        p = Project(self, self.CJK_DEPENDS)
        self.assertIn("TASK-002、TASK-004", p.board())
        self.assertEqual(p.task("next", "TASK-004", "--next", "x")[0], 0)
        self.assertEqual(p.record("TASK-001")["depends_on"],
                         ["TASK-002", "TASK-004"])
        self.assertNotIn("TASK-002、TASK-004", p.board(),
                         "the board kept bytes the store cannot hold, so it "
                         "was copied from the writer's own text rather than "
                         "rendered from the store")
        self.assertIn("| TASK-002, TASK-004 |", p.board())
        self.diff_is_identical(p, "after a cell was re-rendered from the store")

    def test_a_cell_the_store_rewrote_is_reported_rather_than_smoothed_over(self):
        """The same write, from the payload's side. A projection that changes a
        cell nobody asked it to change must say so — that is the difference
        between a rendered board and a board being quietly normalized."""
        p = Project(self, self.CJK_DEPENDS)
        _, out = p.task("next", "TASK-004", "--next", "x")
        rewritten = out["projection"]["cells_the_store_and_board_disagree_on"]
        self.assertEqual([(c["id"], c["column"]) for c in rewritten],
                         [("TASK-001", "Depends on")])

    def test_the_payload_counts_what_the_projection_could_not_fill(self):
        p = Project(self)
        _, out = p.task("start", "TASK-001")
        proj = out["projection"]
        self.assertGreaterEqual(proj["rows_from_store"], 4)
        self.assertEqual(proj["rows_not_on_board"], [])
        # TASK-003's cell is one the store cannot hold, so the layout keeps it
        # and the count says which column paid for it.
        self.assertEqual(proj["cells_verbatim"], {"Status": 1})


class TestAStatusTheStoreCannotHold(Fixture):
    """After migration, an unstorable projection cell is not task truth."""

    def test_the_store_record_can_be_written_despite_projection_prose(self):
        for argv in (("start", "TASK-003"),
                     ("status", "TASK-003", "--status", "review"),
                     ("done", "TASK-003", "--evidence", "BOARD.md"),
                     ("drop", "TASK-003", "--reason", "x"),
                     ("prioritize", "TASK-003", "--priority", "P1")):
            with self.subTest(cmd=argv[0]):
                p = Project(self)
                code, out = p.task(*argv)
                self.assertEqual(code, 0, out)

    def test_the_write_replaces_projection_prose_with_store_truth(self):
        p = Project(self)
        self.assertEqual(p.task("start", "TASK-003")[0], 0)
        self.assertEqual(p.record("TASK-003")["status"], "in_progress")
        self.assertNotIn("迁移 done", p.board())

    def test_a_dry_run_uses_store_truth_and_writes_nothing(self):
        p = Project(self)
        before = {path: path.read_bytes() for path in p.root.rglob("*") if path.is_file()}
        self.assertEqual(p.task("start", "TASK-003", "--dry-run")[0], 0)
        after = {path: path.read_bytes() for path in p.root.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_every_other_row_is_unaffected(self):
        """The scope that two pinned tests forced, and they were right.

        A project-wide refusal would break `the read path and the write path
        must agree about what a row is` for every row Perry reads perfectly
        well, on account of one it does not."""
        p = Project(self)
        for tid in ("TASK-001", "TASK-002", "TASK-004"):
            with self.subTest(id=tid):
                self.assertEqual(p.task("next", tid, "--next", "still fine")[0],
                                 0)
        self.diff_is_identical(p, "after writing around the unstorable row")

    def test_the_unresolved_cell_is_named_in_every_write_that_proceeds(self):
        """Counted rather than discovered later. A fallback nobody counts is
        how the store reproduces nothing while `cmp` stays clean."""
        p = Project(self)
        _, out = p.task("start", "TASK-001")
        named = out["projection"]["status_cells_the_store_cannot_hold"]
        self.assertEqual([r["id"] for r in named], ["TASK-003"])

    def test_a_board_with_no_such_cell_reports_an_empty_list(self):
        """The silence is asserted, not assumed — otherwise this check passes
        on a project where it never ran."""
        p = Project(self, BOARD.replace(
            "**迁移 done，占比目标 not_started**", "not_started"))
        _, out = p.task("start", "TASK-001")
        self.assertEqual(
            out["projection"]["status_cells_the_store_cannot_hold"], [])
        self.assertEqual(p.record("TASK-003")["status"], "not_started")


class TestRowOrderIsRecorded(Fixture):
    """TASK-089 decision 2.

    `perry-task/list` sorts by id and a real board does not: Perry's own
    `## P1` runs `TASK-047` before `TASK-038`. A store that did not record
    order would move those rows on the first render — a whole-file diff on
    somebody's project, which is what ADR-004 means by a migration having to be
    reviewable and what `viewer/tables.py § render_row` refuses one row down.
    """

    #: Authored order that disagrees with id order, in the same shape the real
    #: board does. Nothing but a recorded `order` can reproduce it.
    OUT_OF_ORDER = BOARD.replace(
        "| TASK-001 | First | User | not_started | — | — |\n"
        "| TASK-002 | Second | User | in_progress | — | — |",
        "| TASK-002 | Second | User | in_progress | — | — |\n"
        "| TASK-001 | First | User | not_started | — | — |")

    def test_the_store_records_the_authored_order_not_the_id_order(self):
        p = Project(self, self.OUT_OF_ORDER)
        self.assertEqual(p.task("start", "TASK-004")[0], 0)
        self.assertEqual(p.record("TASK-002")["order"], 0)
        self.assertEqual(p.record("TASK-001")["order"], 1)

    def test_a_write_does_not_reorder_the_board(self):
        p = Project(self, self.OUT_OF_ORDER)
        before = p.rows_of("P0")
        self.assertEqual(before[:2], ["TASK-002", "TASK-001"],
                         "the fixture is not out of id order")
        self.assertEqual(p.task("next", "TASK-004", "--next", "x")[0], 0)
        self.assertEqual(p.rows_of("P0"), before,
                         "the write reordered rows it was not asked to move")
        self.diff_is_identical(p, "after a write on an out-of-id-order board")

    def test_a_new_row_lands_last_in_its_section_and_records_that(self):
        p = Project(self)
        code, out = p.task("add", "--title", "New", "--priority", "P0")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.rows_of("P0")[-1], out["id"])
        self.assertEqual(p.record(out["id"])["order"], 4)

    def test_a_row_that_left_the_board_records_no_order(self):
        """`null`, not `0`. "Not on the board" and "first on the board" are
        different claims and a consumer sorting on the field must be able to
        tell them apart."""
        p = Project(self)
        self.assertEqual(p.task("done", "TASK-002", "--evidence", "BOARD.md")[0], 0)
        self.assertIsNone(p.record("TASK-002")["order"])
        self.assertEqual(p.record("TASK-004")["order"], 2,
                         "the rows below the closed one did not close up")

    def test_the_renderer_reports_a_board_that_disagrees_with_the_store(self):
        """`order` is a claim until something can be shown to disagree with it.

        Swap two rows in the file and `diff` says which section moved — it does
        not silently re-sort them, because re-sorting here is the whole-file
        diff the field exists to prevent."""
        p = Project(self)
        self.assertEqual(p.task("start", "TASK-001")[0], 0)
        board = p.board()
        a = "| TASK-001 | First | User | in_progress | — | — |\n"
        b = "| TASK-002 | Second | User | in_progress | — | — |\n"
        self.assertIn(a + b, board, "the fixture rows are not adjacent")
        (p.root / "BOARD.md").write_text(board.replace(a + b, b + a),
                                         encoding="utf-8")
        report = json.loads(p.tasks("diff")[1])
        moved = report["sections_out_of_stored_order"]
        self.assertEqual([s["heading"] for s in moved],
                         ["P0 (must finish this period)"])
        self.assertEqual(moved[0]["on_the_board"][:2], ["TASK-002", "TASK-001"])
        self.assertEqual(moved[0]["in_the_store"][:2], ["TASK-001", "TASK-002"])


class TestTheStoreAndTheJournalAreThePair(Fixture):
    def test_both_land_together(self):
        p = Project(self)
        self.assertEqual(p.task("start", "TASK-001")[0], 0)
        journal = list((p.root / "journal").rglob("*.md"))
        self.assertEqual(len(journal), 1)
        self.assertIn("TASK-001", journal[0].read_text(encoding="utf-8"))
        self.assertTrue((p.root / "tasks.jsonl").exists())

    def test_a_lost_event_costs_history_and_not_the_record(self):
        """The direction the loss is allowed to run. `.perry/events.jsonl`
        unwritable: the store and the journal still land, and the tool says the
        event did not."""
        import os
        p = Project(self)
        ev = p.root / ".perry"
        (ev / "events.jsonl").write_text("", encoding="utf-8")
        mode = ev.stat().st_mode
        os.chmod(ev / "events.jsonl", 0o444)
        os.chmod(ev, 0o555)
        try:
            code, out = p.task("start", "TASK-001")
        finally:
            os.chmod(ev, mode)
            os.chmod(ev / "events.jsonl", 0o644)
        self.assertEqual(code, 0, out)
        self.assertFalse(out["event_written"])
        self.assertEqual(p.record("TASK-001")["status"], "in_progress")
        self.diff_is_identical(p, "after an event append failed")


if __name__ == "__main__":
    unittest.main()
