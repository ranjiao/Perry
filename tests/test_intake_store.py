"""`## Intake` is a projection of a record store — ADR-007, a third register.

TASK-196, following TASK-040 and TASK-195 exactly. The order of this file is
the argument, and it is the same order:

1. **The store reproduces what it replaces, byte for byte, before it holds a
   single field the table could not.** A renderer that quietly keeps a cell
   verbatim passes `cmp` while reproducing nothing, so the report's own
   fallback counters are asserted empty, not just the bytes.

2. **`n` is the ordinal, and what that costs is asserted rather than
   described.** An intake row has no id. `perry-task resolve-intake <n>` takes
   a position and `perry-task/list § intake.rows[].n` publishes one, so the
   store keys on `order` and `n = order + 1`. A sweep renumbers, exactly as it
   did before the store existed — and the last class here is the proof that
   the renumbering is now REPORTED rather than silent, which is the whole of
   what the store buys.

3. **"Is this row discharged?" is one function.** It was four, and they
   disagreed in both directions; a register with a store must not have five
   answers to what its own field means.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import task_actor

COVERS = (
    "bin/perry-task",
    "bin/perry-lint",
    "bin/perry-explain",
    "bin/perry-state",
    "bin/perry_store.py",
    "schema/state-schema.json",
)

import contextlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path

from task_writer_support import PT, Project

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
sys.path.insert(0, str(PERRY_HOME / "bin"))
import parsers as P  # noqa: E402
import perry_store as S  # noqa: E402

TASKS = PERRY_HOME / "bin" / "perry-tasks"
LINT = PERRY_HOME / "bin" / "perry-lint"

#: Quoted from `perry/BOARD.md § Intake` — a waiting row whose `Outcome` is the
#: em-dash the writer stamps, a request carrying backticks and a comma, one
#: carrying an em-dash of its own, and a discharged row. The section the store
#: has to reproduce is a real one, or the byte gate is being run against text
#: written to pass it.
REGISTER = (
    "| Arrived | Request | Outcome |\n"
    "|---|---|---|\n"
    "| 2026-08-21 | two test modules import `from tests.X`, and `tests` is a "
    "name another project on this machine owns | — |\n"
    "| 2026-08-21 | the suite's red set changes with the interpreter, so "
    "\"all green\" has never been a portable claim | — |\n"
    "| 2026-08-27 | perry-explain resolves P002-O1-KR1 to a table row — not to "
    "the linkage register | dropped 2026-08-28 — folded into TASK-190 |\n"
    "| 2026-08-28 | tasks[].role is typed as one string but a seam row needs "
    "two | — |\n"
)


def board_with(section: str) -> str:
    h = "| ID | Title | Owner | Status | Next action | Evidence |"
    sep = "|" + "|".join(["---"] * 6) + "|"
    return (
        "# Board — T\n\n"
        f"## Intake\n\n{section}\n"
        f"## P0 (must finish this period)\n\n{h}\n{sep}\n\n"
        f"## P1\n\n{h}\n{sep}\n\n"
        f"## P2\n\n{h}\n{sep}\n"
    )


def derive(text: str, current: list[dict] | None = None):
    """(board, ops, records) for a board given as text."""
    import tempfile
    tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
    tmp.write(text)
    tmp.close()
    board = PT.Board(Path(tmp.name))
    return board, PT, S.intake_records(board, PT, current)


class TestByteIdentityComesFirst(unittest.TestCase):
    """Item 1. **Before `discharged` exists**, the store has to put the section
    back exactly as it found it."""

    def test_the_section_round_trips_byte_for_byte(self):
        text = board_with(REGISTER)
        board, ops, records = derive(text)
        rendered, report = S.intake_render(board, records, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["rows_from_store"], 4)

    def test_no_cell_survived_as_a_literal(self):
        """`cmp` alone cannot tell a rebuilt cell from a copied one. These
        four counters are what make the byte result mean something."""
        board, ops, records = derive(board_with(REGISTER))
        _, report = S.intake_render(board, records, ops)
        self.assertEqual(report["cells_verbatim"], {})
        self.assertEqual(report["cells_wearing_decoration"], {})
        self.assertEqual(report["cells_the_store_and_board_disagree_on"], [])
        self.assertEqual(report["rows_out_of_stored_order"], {})
        self.assertEqual(report["rows_verbatim"], [])
        self.assertEqual(report["rows_not_on_board"], [])

    def test_byte_identity_does_not_depend_on_the_new_field(self):
        """`discharged` is the field the three columns cannot express. If the
        byte gate needed it, the gate would be testing the new field rather
        than the migration."""
        text = board_with(REGISTER)
        board, ops, records = derive(text)
        stripped = [{k: v for k, v in r.items() if k != "discharged"}
                    for r in records]
        rendered, report = S.intake_render(board, stripped, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["cells_verbatim"], {})

    def test_a_wrong_stored_value_reddens_the_gate(self):
        """**A renderer that cannot be made to print a wrong value cannot be
        shown to print a right one.** The first version of `describe_cell`
        fell back to verbatim on a disagreement, which derived the layout
        against the very store it was meant to be testing."""
        text = board_with(REGISTER)
        board, ops, records = derive(text)
        records[1]["request"] = "not what the board says"
        rendered, report = S.intake_render(board, records, ops)
        self.assertNotEqual(rendered, text)
        self.assertIn("not what the board says", rendered)
        self.assertEqual(
            [(d["n"], d["column"])
             for d in report["cells_the_store_and_board_disagree_on"]],
            [(2, "Request")])

    def test_decoration_is_the_value_here_and_the_counter_says_so(self):
        """**Structurally empty, and worth an assertion rather than a shrug.**

        `cells_wearing_decoration` counts a cell whose stored value sits
        inside prose the store does not hold — `~~**RX-001**~~` for a risk,
        because `strip_handle` takes the decoration off the id before the
        store sees it. No intake field is normalised on the way in: a bolded
        request IS `**a bolded request**` in the store, so the cell is the
        value and the counter is empty for a reason, not by luck.
        """
        board, ops, records = derive(board_with(
            "| Arrived | Request | Outcome |\n|---|---|---|\n"
            "| 2026-08-21 | **a bolded request** | — |\n"))
        self.assertEqual(records[0]["request"], "**a bolded request**")
        _, report = S.intake_render(board, records, ops)
        self.assertEqual(report["cells_wearing_decoration"], {})

    def test_a_column_the_store_has_no_field_for_is_layout_and_is_counted(self):
        board, ops, records = derive(board_with(
            "| Arrived | Request | Outcome | Notes |\n|---|---|---|---|\n"
            "| 2026-08-21 | a request | — | somebody's note |\n"))
        _, report = S.intake_render(board, records, ops)
        self.assertEqual(report["cells_verbatim"], {"Notes": 1})


class TestTheRegisterHasNoId(unittest.TestCase):
    """Item 2. What `n` means, stated as assertions.

    Everything here would be trivial for the risks register, which carries its
    key in a cell. None of it is trivial here, and the difference is the row.
    """

    def test_the_store_is_keyed_on_the_rows_position(self):
        _b, _o, records = derive(board_with(REGISTER))
        self.assertEqual([r["order"] for r in records], [0, 1, 2, 3])
        self.assertNotIn("id", records[0])

    def test_n_is_order_plus_one_and_that_is_what_the_writers_take(self):
        """`resolve-intake <n>` is 1-based over `section_rows`, and
        `perry-task/list § intake.rows[].n` publishes the same integer. The
        store records `order`, 0-based, and the two are the same fact.
        """
        p = Project(board=board_with(REGISTER))
        # `list` reads `intake.jsonl` only (TASK-262 round 4b retired its
        # reading of a held `## Intake`), so the register is imported first —
        # the store it reads is then the derivation of the held file.
        imported = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-tasks"),
             "intake-write", "--from-board", "--root", str(p.root)],
            capture_output=True, text=True)
        self.assertEqual(imported.returncode, 0, imported.stderr)
        out = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-task"), "list",
             "--json", "--root", str(p.root)], capture_output=True, text=True)
        rows = json.loads(out.stdout)["intake"]["rows"]
        _b, _o, records = derive(p.held_board())
        self.assertEqual([r["n"] for r in rows],
                         [r["order"] + 1 for r in records])
        self.assertEqual([r["request"] for r in rows],
                         [r["request"] for r in records])

    #: Lines that are easy for one reader to count and another to skip: a row
    #: with an empty first cell, a short row, a long row, an escaped pipe, a
    #: line with no trailing pipe, and one indented.
    AWKWARD = (
        "| Arrived | Request | Outcome |\n|---|---|---|\n"
        "| 2026-08-21 | first | — |\n"
        "|  |  |  |\n"
        "| 2026-08-22 | a \\| b | — |\n"
        "| 2026-08-23 | short |\n"
        "| 2026-08-24 | long | — | a fourth cell |\n"
        "| 2026-08-25 | no trailing pipe | —\n"
        "  | 2026-08-26 | indented | — |\n")

    def test_the_store_and_resolve_intake_count_the_same_rows(self):
        """**The invariant this store lives or dies by.**

        `perry-task resolve-intake <n>` reaches its row through
        `Board.section_rows`; the store derives `order` through
        `intake_records`. Two functions in two files, and if they ever count
        `## Intake` differently then every integer a consumer holds addresses
        a different request and nothing says so. The awkward lines are the
        ones where two readers plausibly diverge.
        """
        board, ops, records = derive(board_with(self.AWKWARD))
        keys = [ops.norm(h) for h in S.intake_table(board, ops)["header"]]
        addressable = [dict(zip(keys, cells))
                       for _line, cells in board.section_rows("Intake")]
        self.assertEqual(len(records), len(addressable))
        self.assertEqual([r["request"] for r in records],
                         [r.get("request", "") for r in addressable])
        self.assertEqual([r["order"] + 1 for r in records],
                         list(range(1, len(addressable) + 1)))

    def test_the_import_refuses_if_those_two_ever_disagree(self):
        """The gate that is not a tautology — see `cmd_intake_write`. Forced
        by making the two readers see different row counts."""
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader("perry_tasks_n_gate",
                                                      str(TASKS))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        self._held = p = Project(board=board_with(REGISTER))
        real = S.intake_records
        mod.perry_store.intake_records = lambda b, o, c=None: real(b, o, c)[:2]
        noise = io.StringIO()
        try:
            with contextlib.redirect_stderr(noise):
                rc = mod.cmd_intake_write(p.root, ["--from-board"])
        finally:
            mod.perry_store.intake_records = real
        self.assertEqual(rc, 1)
        self.assertIn("one integer two meanings", noise.getvalue())
        self.assertFalse((p.root / "intake.jsonl").exists())

    def test_two_identical_requests_are_two_records(self):
        """Position, not content. A register that deduplicated by text would
        collapse a request that genuinely arrived twice into one row and
        renumber everything after it."""
        _b, _o, records = derive(board_with(
            "| Arrived | Request | Outcome |\n|---|---|---|\n"
            "| 2026-08-21 | the same ask | — |\n"
            "| 2026-08-21 | the same ask | — |\n"))
        self.assertEqual(len(records), 2)
        self.assertEqual([r["order"] for r in records], [0, 1])

    def test_a_store_written_out_of_order_is_reported_not_obeyed(self):
        """The board cannot sit out of stored order — its position IS the key.
        What can disagree is the store with itself: a consumer that reads the
        JSONL as a list and indexes it gets a different row from one that
        honours `order`."""
        text = board_with(REGISTER)
        board, ops, records = derive(text)
        shuffled = [records[1], records[0], records[2], records[3]]
        rendered, report = S.intake_render(board, shuffled, ops)
        self.assertEqual(rendered, text)     # rendered BY `order`, not by line
        self.assertEqual(report["rows_out_of_stored_order"],
                         {"in_the_file": [1, 0, 2, 3],
                          "in_the_store": [0, 1, 2, 3]})

    def test_a_record_with_no_order_is_a_record_nothing_can_address(self):
        """`validate_risk_records` allows `order: null` — "not recorded" is a
        real answer when the record has an id. Here it is not: a record with
        no position is not addressable at all."""
        good, findings = S.validate_intake_records(
            [{"order": None, "arrived": "", "request": "x", "outcome": "",
              "discharged": False}])
        self.assertEqual(good, [])
        self.assertIn("`order` is NoneType", findings[0]["message"])

    def test_two_records_at_one_position_are_refused(self):
        good, findings = S.validate_intake_records([
            {"order": 0, "request": "a", "arrived": "", "outcome": "",
             "discharged": False},
            {"order": 0, "request": "b", "arrived": "", "outcome": "",
             "discharged": False}])
        self.assertEqual(len(good), 1)
        self.assertIn("unique row position", findings[0]["message"])


class TestDischargedIsStoredNotDerived(unittest.TestCase):
    """The field the three columns cannot express — this register's `cleared`."""

    def test_the_import_reads_it_off_the_outcome_when_the_store_is_silent(self):
        _b, _o, records = derive(board_with(REGISTER))
        self.assertEqual([r["discharged"] for r in records],
                         [False, False, True, False])

    def test_a_true_survives_a_re_import_because_discharge_is_one_way(self):
        """`check_intake_undischarged` makes discharge a one-way transition —
        "a row takes exactly one outcome" — so `True` is a fact the board
        cannot un-say, and taking its silence as `False` would delete a value
        on the second run of the command whose first run wrote it."""
        text = board_with(REGISTER)
        board, ops, records = derive(text)
        stored = [dict(r) for r in records]
        stored[0]["discharged"] = True
        again = S.intake_records(board, ops, stored)
        self.assertTrue(again[0]["discharged"])

    def test_a_false_is_recomputed_because_the_cell_can_say_that_much(self):
        """The other half of the asymmetry, and the reason it is not just
        "the store always wins": `False` means "still waiting", which the
        `Outcome` cell answers for itself."""
        board, ops, records = derive(board_with(REGISTER))
        stored = [dict(r, discharged=False) for r in records]
        again = S.intake_records(board, ops, stored)
        self.assertTrue(again[2]["discharged"])

    def test_discharged_is_typed_and_a_string_is_a_finding(self):
        good, findings = S.validate_intake_records(
            [{"order": 0, "arrived": "", "request": "x", "outcome": "",
              "discharged": "yes"}])
        self.assertEqual(good, [])
        self.assertIn("`discharged` is str", findings[0]["message"])


class TestOneRuleForDischarged(unittest.TestCase):
    """Item 3. It was four functions and they disagreed in both directions."""

    def test_the_reader_and_the_writers_call_the_same_function(self):
        src = (PERRY_HOME / "bin" / "perry-task").read_text()
        # 4 → 3 at TASK-262 round 4b: the fourth call was `list`'s reading of
        # a held `BOARD.md § Intake` for a project with no intake store, and
        # that fallback is retired. The three left are the writers' and the
        # `_cmd_list_from_board` builder's.
        self.assertEqual(src.count("P.intake_is_discharged"), 3,
                         "a fourth answer to `is this row discharged` appeared "
                         "in bin/perry-task, or one stopped asking")
        self.assertNotIn("not in INTAKE_UNSET", src)

    def test_the_cells_the_two_old_rules_disagreed_about(self):
        """`_NO_DATE` carried `待定` and `INTAKE_UNSET` did not; `INTAKE_UNSET`
        carried `pending` and `_NO_DATE` did not. Both spellings are ones a
        human types, and each counted as discharged on one side of the repo
        and waiting on the other. TASK-042's round-3 V4 review found the set
        had no Chinese member at all and it went unchanged for want of a
        caller that had to care."""
        for cell in ("待定", "pending", "n/a", "无", "—", "", "?"):
            with self.subTest(cell=cell):
                self.assertFalse(P.intake_is_discharged(cell))
        for cell in ("dropped 2026-08-28 — folded in", "TASK-190", "routed"):
            with self.subTest(cell=cell):
                self.assertTrue(P.intake_is_discharged(cell))

    def test_the_store_asks_the_same_question_as_the_reader(self):
        """By identity, not by agreement — the assertion `tests/test_risks.py`
        could only make once the four risk predicates became one."""
        board = board_with(REGISTER)
        _b, _o, records = derive(board)
        import tempfile
        tmp = Path(tempfile.mkdtemp()) / "BOARD.md"
        tmp.write_text(board, encoding="utf-8")
        parsed = P.parse_board(tmp.read_text(encoding="utf-8")).intake
        self.assertEqual([r["discharged"] for r in parsed],
                         [r["discharged"] for r in records])

    def test_a_decorated_outcome_is_read_the_same_way_by_both(self):
        self.assertFalse(P.intake_is_discharged("**—**"))
        self.assertFalse(P.intake_is_discharged(" `n/a` "))


class TestTheMigrationSurface(unittest.TestCase):

    def _tasks(self, root: Path, *argv):
        return subprocess.run([sys.executable, str(TASKS), *argv,
                               "--root", str(root)],
                              capture_output=True, text=True)

    def test_intake_diff_is_green_on_a_section_it_can_reproduce(self):
        p = Project(board=board_with(REGISTER))
        out = self._tasks(p.root, "intake-diff")
        self.assertEqual(out.returncode, 0, out.stderr)
        report = json.loads(out.stdout)
        self.assertTrue(report["identical"])
        self.assertEqual(report["source"], "board")
        self.assertEqual(report["rows_from_store"], 4)

    def test_intake_diff_reddens_when_the_store_and_the_section_disagree(self):
        p = Project(board=board_with(REGISTER))
        (p.root / "intake.jsonl").write_text(json.dumps(
            {"order": 0, "arrived": "2026-08-21",
             "request": "not what the board says", "outcome": "—",
             "discharged": False}) + "\n")
        out = self._tasks(p.root, "intake-diff")
        self.assertEqual(out.returncode, 1)
        report = json.loads(out.stdout)
        self.assertFalse(report["identical"])
        self.assertEqual(report["source"], "store")
        self.assertIn("not what the board says",
                      report["first_difference"]["rendered"])

    def test_intake_render_write_refuses_without_a_store(self):
        p = Project(board=board_with(REGISTER))
        before = p.board()
        out = self._tasks(p.root, "intake-render", "--write")
        self.assertEqual(out.returncode, 2)
        self.assertIn("nothing to render", out.stderr)
        self.assertEqual(p.board(), before)

    def test_intake_build_names_the_shape_it_found(self):
        p = Project(board=board_with("some prose about the queue\n\n"))
        report = json.loads(self._tasks(p.root, "intake-build").stdout)
        self.assertEqual(report["register"], "prose")
        self.assertEqual(report["records"], 0)

    def test_intake_build_counts_what_is_still_waiting(self):
        """The count the register exists for: an over-cap board means "the
        queue is not being drained" only if undischarged rows are countable."""
        p = Project(board=board_with(REGISTER))
        report = json.loads(self._tasks(p.root, "intake-build").stdout)
        self.assertEqual(report["records"], 4)
        self.assertEqual(report["undischarged"], 3)

    def test_intake_write_refuses_without_the_explicit_direction(self):
        p = Project(board=board_with(REGISTER))
        out = self._tasks(p.root, "intake-write")
        self.assertEqual(out.returncode, 1)
        self.assertIn("--from-board", out.stderr)
        self.assertIn("intake-render --write", out.stderr)
        self.assertFalse((p.root / "intake.jsonl").exists())


class TestTheOneWayImport(unittest.TestCase):
    """`perry-tasks intake-write --from-board` — `## Intake` → the store."""

    def _tasks(self, root: Path, *argv):
        return subprocess.run([sys.executable, str(TASKS), *argv,
                               "--root", str(root)],
                              capture_output=True, text=True)

    def _imported(self, section: str = REGISTER) -> Project:
        """A project whose intake store was written by the command under test.

        **Held on `self`** — `Project` owns a `TemporaryDirectory` and deletes
        the tree when it is collected.
        """
        self._held = p = Project(board=board_with(section))
        out = self._tasks(p.root, "intake-write", "--from-board")
        self.assertEqual(out.returncode, 0, out.stderr)
        return p

    def _store(self, p: Project) -> list[dict]:
        return [json.loads(l) for l in
                (p.root / "intake.jsonl").read_text().split("\n") if l.strip()]

    def _lint(self, root: Path) -> dict:
        out = subprocess.run(
            [sys.executable, str(LINT), "--root", str(root), "--json"],
            capture_output=True, text=True)
        return json.loads(out.stdout)

    def test_the_import_writes_a_record_per_register_row(self):
        p = self._imported()
        self.assertEqual([r["order"] for r in self._store(p)], [0, 1, 2, 3])

    def test_intake_diff_compares_against_a_real_store_and_is_green(self):
        p = self._imported()
        out = self._tasks(p.root, "intake-diff")
        self.assertEqual(out.returncode, 0, out.stderr)
        report = json.loads(out.stdout)
        self.assertTrue(report["identical"])
        self.assertEqual(report["source"], "store")
        self.assertEqual(report["cells_verbatim"], {})
        self.assertEqual(report["cells_wearing_decoration"], {})
        self.assertEqual(report["cells_the_store_and_board_disagree_on"], [])
        self.assertEqual(report["rows_out_of_stored_order"], {})
        self.assertEqual(report["rows_verbatim"], [])
        self.assertEqual(report["rows_not_on_board"], [])

    def test_the_import_is_idempotent(self):
        p = self._imported()
        first = (p.root / "intake.jsonl").read_bytes()
        out = self._tasks(p.root, "intake-write", "--from-board")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual((p.root / "intake.jsonl").read_bytes(), first)

    def test_a_register_with_no_rows_imports_and_reads_back_as_a_store(self):
        """An empty store is a store. The FILE decides which source this is;
        the record count decides what there is to render."""
        p = self._imported("| Arrived | Request | Outcome |\n|---|---|---|\n")
        self.assertEqual((p.root / "intake.jsonl").read_text(), "")
        report = json.loads(self._tasks(p.root, "intake-diff").stdout)
        self.assertEqual(report["source"], "store")
        self.assertTrue(report["identical"])
        self.assertEqual(report["register"], "table")
        self.assertEqual(report["rows_from_store"], 0)

    def test_a_project_with_no_store_reports_the_board_as_the_source(self):
        self._held = p = Project(board=board_with(REGISTER))
        report = json.loads(self._tasks(p.root, "intake-diff").stdout)
        self.assertEqual(report["source"], "board")
        self.assertEqual(report["rows_from_store"], 4)

    def test_the_import_appends_no_event(self):
        """It discharges nothing and routes nothing. Every event it could
        append would carry today's timestamp for a request that arrived weeks
        ago, and `perry-state` reads that log."""
        p = self._imported()
        self.assertEqual([e for e in p.events()
                          if e.get("event", "").startswith("intake")], [])

    def test_the_store_is_not_reported_as_a_file_perry_did_not_write(self):
        """It has no `id`, so `looks_like_perry_record`'s task/risk branch
        cannot see it — and without its own branch every project that imports
        one gets an `NS-01` against Perry's own claim."""
        import importlib.machinery
        import importlib.util
        spec = importlib.util.spec_from_loader(
            "perry_lint_mod_intake",
            importlib.machinery.SourceFileLoader("perry_lint_mod_intake",
                                                 str(LINT)))
        lint = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lint)
        p = self._imported()
        self.assertTrue(lint.looks_like_perry_record(p.root / "intake.jsonl"))

    # ── refuse rather than guess ───────────────────────────────────────

    def _refused(self, section: str, *argv):
        self._held = p = Project(board=board_with(section))
        store = p.root / "intake.jsonl"
        before_board = (p.root / "BOARD.md").read_bytes()
        before_store = store.read_bytes() if store.exists() else None
        out = self._tasks(p.root, "intake-write", "--from-board", *argv)
        self.assertNotEqual(out.returncode, 0)
        self.assertEqual((p.root / "BOARD.md").read_bytes(), before_board)
        self.assertEqual(store.read_bytes() if store.exists() else None,
                         before_store)
        return p, out

    def test_a_section_with_no_table_is_refused_rather_than_imported_as_nothing(self):
        """The shape that would otherwise pass the byte gate and be wrong:
        `intake_records` returns `[]`, rendering `[]` changes no line, so
        `cmp` is clean — and an empty store would be written over a section
        somebody keeps requests in, reported as a success."""
        _p, out = self._refused("a paragraph about what we are waiting on\n\n")
        self.assertIn("holds no table", out.stderr)
        self.assertIn("perry-task intake", out.stderr)

    def test_a_table_that_is_not_the_register_is_refused(self):
        _p, out = self._refused("| Source | Meaning |\n|---|---|\n"
                                "| user | asked in person |\n\n")
        self.assertIn("must not treat as the register", out.stderr)

    def test_a_board_with_no_such_section_is_refused(self):
        h = "| ID | Title | Owner | Status | Next action | Evidence |"
        sep = "|" + "|".join(["---"] * 6) + "|"
        self._held = p = Project(board=(
            f"# Board — T\n\n## P0 (must finish this period)\n\n{h}\n{sep}\n\n"
            f"## P1\n\n{h}\n{sep}\n\n## P2\n\n{h}\n{sep}\n"))
        out = self._tasks(p.root, "intake-write", "--from-board")
        self.assertEqual(out.returncode, 1)
        self.assertIn("no `## Intake` section", out.stderr)
        self.assertFalse((p.root / "intake.jsonl").exists())

    def test_a_refused_import_leaves_an_existing_store_byte_identical(self):
        """ADR-004 over a store that already exists, not only over one that
        does not: a refusal must not half-write, truncate or reorder it. A
        second table under the heading is the reachable refusal here — the
        byte gate is a tautology for this register (`cmd_intake_write` says
        why), so the shape check is what fires."""
        p = self._imported()
        before = (p.root / "intake.jsonl").read_bytes()
        board = p.root / "BOARD.md"
        board.write_text(board.read_text().replace(
            "## P0 (must finish this period)",
            "| Source | Meaning |\n|---|---|\n| user | asked |\n\n"
            "## P0 (must finish this period)", 1))
        before_board = board.read_bytes()
        out = self._tasks(p.root, "intake-write", "--from-board")
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertIn("more than one table", out.stderr)
        self.assertEqual((p.root / "intake.jsonl").read_bytes(), before)
        self.assertEqual(board.read_bytes(), before_board)

    def test_an_extra_column_is_counted_rather_than_smuggled(self):
        """What the four counters carry that the bytes cannot, for a register
        whose bytes always match: a `Notes` column no stored field claims is
        `cells_verbatim`, and a reader who saw only `identical: true` would
        believe the store held it."""
        p = self._imported()
        board = p.root / "BOARD.md"
        board.write_text(board.read_text()
                         .replace("| Arrived | Request | Outcome |",
                                  "| Arrived | Request | Outcome | Notes |", 1)
                         .replace("|---|---|---|", "|---|---|---|---|", 1)
                         .replace(" | — |\n", " | — | a note |\n"))
        report = json.loads(self._tasks(p.root, "intake-diff").stdout)
        self.assertTrue(report["identical"])
        self.assertEqual(report["cells_verbatim"], {"Notes": 3})

    def test_an_unreadable_store_is_not_overwritten(self):
        p = self._imported()
        (p.root / "intake.jsonl").write_text("{not json\n")
        out = self._tasks(p.root, "intake-write", "--from-board")
        self.assertEqual(out.returncode, 2)
        self.assertIn("cannot be read", out.stderr)
        self.assertEqual((p.root / "intake.jsonl").read_text(), "{not json\n")

    def test_a_malformed_store_is_not_overwritten(self):
        p = self._imported()
        (p.root / "intake.jsonl").write_text(
            json.dumps({"order": "0", "request": "x"}) + "\n")
        out = self._tasks(p.root, "intake-write", "--from-board")
        self.assertEqual(out.returncode, 2)
        self.assertIn("malformed", out.stderr)
        self.assertIn("`order` is str", out.stderr)

    def test_what_the_import_replaces_is_disclosed(self):
        """`--from-board` IS the instruction to prefer the section, and what
        that costs is printed rather than swallowed."""
        p = self._imported()
        records = self._store(p)
        records[0]["arrived"] = "1999-01-01"
        (p.root / "intake.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
        out = self._tasks(p.root, "intake-write", "--from-board")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("row 1.arrived", out.stderr)
        self.assertIn("1999-01-01", out.stderr)

    # ── the claim is a live guard, not a historical note ───────────────

    def _uut(self, name: str):
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader(name, str(TASKS))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        return mod

    def test_the_claim_is_declared_and_withdrawing_it_stops_the_write(self):
        mod = self._uut("perry_tasks_uut_intake")
        self.assertTrue(mod.intake_store_is_declared(),
                        "schema/state-schema.json no longer claims "
                        "intake.jsonl — the declaration was reverted")

        self._held = p = Project(board=board_with(REGISTER))
        real = mod.intake_store_is_declared
        mod.intake_store_is_declared = lambda: False
        noise = io.StringIO()
        try:
            with contextlib.redirect_stderr(noise):
                rc = mod.cmd_intake_write(p.root, ["--from-board"])
        finally:
            mod.intake_store_is_declared = real
        self.assertIn("What is missing is the DECLARATION", noise.getvalue())
        self.assertEqual(rc, 1)
        self.assertFalse((p.root / "intake.jsonl").exists())

    def test_an_unreadable_schema_does_not_claim_the_file_is_declared(self):
        mod = self._uut("perry_tasks_uut_intake2")
        real = mod.lib.load_schema
        mod.lib.load_schema = lambda *a, **k: (_ for _ in ()).throw(
            OSError("no schema here"))
        try:
            self.assertFalse(mod.intake_store_is_declared())
        finally:
            mod.lib.load_schema = real
        self.assertIn("What is missing is the DECLARATION",
                      mod.INTAKE_STORE_UNDECLARED)


class TestTheCostOfNIsReportedRatherThanSilent(unittest.TestCase):
    """**The judgement call of the row, as assertions.**

    `n` is a cursor, not a name: a row removed from `## Intake` renumbers every
    row below it, and `perry-task resolve-intake 3` then addresses a different
    request than it did yesterday. That was true before this store existed and
    the store does not repair it — repairing it would mean redefining an
    integer people already type.

    What the store adds is that it can no longer happen unnoticed.
    """

    def _tasks(self, root: Path, *argv):
        return subprocess.run([sys.executable, str(TASKS), *argv,
                               "--root", str(root)],
                              capture_output=True, text=True)

    def _lint(self, root: Path) -> dict:
        out = subprocess.run(
            [sys.executable, str(LINT), "--root", str(root), "--json"],
            capture_output=True, text=True)
        return json.loads(out.stdout)

    def _imported(self) -> Project:
        self._held = p = Project(board=board_with(REGISTER))
        out = self._tasks(p.root, "intake-write", "--from-board")
        self.assertEqual(out.returncode, 0, out.stderr)
        return p

    def _hand_delete_the_first_intake_row(self, p: Project) -> None:
        """Delete `## Intake`'s first row from the board and nothing else.

        Extracted so the two tests below run on the SAME state: one asks what
        `perry-lint` says about it, and one asks what happens if you then run a
        command on it. Round 4's suite had the first and not the second.
        """
        board = p.root / "BOARD.md"
        lines = board.read_text().split("\n")
        del lines[next(i for i, l in enumerate(lines)
                       if "two test modules import" in l)]
        board.write_text("\n".join(lines))

    def test_a_hand_deleted_row_no_longer_moves_n_for_a_write(self):
        """**The line the suite stopped one short of**, after TASK-262 round 4a.

        TASK-203 round 5 took the state above — a hand-deleted `## Intake` row
        against a minted 4-record store — one step further, running a
        shrink-PERMITTED command on it, and asserted `resolve-intake` refused
        rather than persist a 3-record store. That refusal is still in
        `commit()` (`tests/test_register_store_invariant.py §
        TestTheExemptionIsBounded` holds it), but a held file no longer
        reaches it: a write builds from the declared board, which is the
        store.

        So the same step now has a better answer and this asserts it: the
        write succeeds, `n = 1` still addresses the FIRST stored request (the
        one the hand edit deleted from the file), no record is lost, and the
        hand-edited file keeps its bytes.
        """
        p = self._imported()
        store = p.root / "intake.jsonl"
        self.assertEqual(len(store.read_text().strip().split("\n")), 4,
                         "control: the store holds four records")
        self._hand_delete_the_first_intake_row(p)
        board = p.root / "BOARD.md"
        edited = board.read_bytes()
        self.assertNotIn("two test modules import", board.read_text(),
                         "control: the hand edit removed the first row")
        tool = PERRY_HOME / "bin" / "perry-task"
        out = subprocess.run(
            task_actor.command([sys.executable, str(tool), "resolve-intake", "1",
             "--outcome", "dropped", "--reason", "a request we will not take",
             "--root", str(p.root)], 'test_intake_store'), capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        stored = [json.loads(l) for l in store.read_text().split("\n")
                  if l.strip()]
        self.assertEqual(len(stored), 4, "a record was lost")
        self.assertIn("two test modules import", stored[0]["request"])
        self.assertIs(stored[0]["discharged"], True,
                      "n = 1 addressed a different request than the store's first")
        self.assertIs(stored[1]["discharged"], False)
        self.assertEqual(board.read_bytes(), edited,
                         "the write rewrote the retired BOARD.md")

    def test_a_sweep_moves_n_and_the_store_is_what_says_so(self):
        """**The mutation this whole row exists to make visible.**

        `resolve-intake 2` discharges the second request; `intake-sweep` then
        takes every discharged row off the board. Afterwards `n = 2` addresses
        a DIFFERENT request than it did five commands ago — which was true
        before this store existed and was reported by nothing at all. Now the
        board and the store disagree and `perry-lint` names the rows.
        """
        p = self._imported()
        task = PERRY_HOME / "bin" / "perry-task"

        def numbering():
            out = subprocess.run(
                [sys.executable, str(task), "list", "--json",
                 "--root", str(p.root)], capture_output=True, text=True)
            return {r["n"]: r["request"] for r in
                    json.loads(out.stdout)["intake"]["rows"]}

        before = numbering()
        for argv in (["resolve-intake", "2", "--outcome", "dropped",
                      "--reason", "folded in", "--json"],):
            out = subprocess.run(task_actor.command([sys.executable, str(task), *argv,
                                  "--root", str(p.root)], 'test_intake_store'),
                                 capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
        # **No re-import** (TASK-262 round 4a). It was here so the store knew
        # about the discharge, back when the held board was the layout a write
        # mutated; `resolve-intake` writes the store, and re-importing the held
        # file — which no write updates now — would overwrite that discharge.
        out = subprocess.run(task_actor.command([sys.executable, str(task), "intake-sweep",
                              "--json", "--root", str(p.root)], 'test_intake_store'),
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout)["swept"], 2)

        after = numbering()
        self.assertNotEqual(before[2], after[2],
                            "the point of the test: n=2 is a different row")
        # **Converted by TASK-203.** This asserted `drifted: 3` and then ran
        # the import to fix it. `intake-sweep` now writes the store inside the
        # same transaction as the board — it is one of the three commands
        # `bin/perry-task § SHRINK_ALLOWANCE` permits to make a canonical store
        # smaller, and by exactly the rows it swept — so the renumbering is recorded as it happens and there is
        # no window in which the two disagree. The reading this test exists
        # for is unchanged: `n = 2` addresses a different request than it did
        # five commands ago, and the store is what says so.
        #
        # The drift half belonged to a hand edit to a held board, and
        # `test_a_row_deleted_by_hand_reports_every_row_it_renumbered` left
        # with TASK-262 round 4b, which retired that comparison.
        # (TASK-262 round 4b) The `drifted == 0` lint assertion that stood here
        # is gone: no board file is compared with its store any more, so the
        # register's `drifted` is its empty default whatever the files say,
        # and asserting it would pass for no reason (round 4b result F33).
        stored = [json.loads(l) for l in
                  (p.root / "intake.jsonl").read_text().split("\n") if l.strip()]
        self.assertEqual([r["request"] for r in stored], [after[1], after[2]])
        self.assertEqual([r["order"] for r in stored], [0, 1])

    def test_the_shift_is_refused_rather_than_half_absorbed(self):
        """A render that would leave a record with no row REFUSES (DESIGN-016 A5).

        **This test asserted the opposite until 2026-09-09, and it was passing
        for a reason nobody had looked at.** `## Intake` is keyed on POSITION,
        so a hand-deleted row shifts every row after it up by one. The render
        then fills row n from record n: the deleted request's text does come
        back — into the row that used to hold the NEXT one — and the LAST
        record has no row left to go into and is dropped from the board. The
        old assertion, `assertIn("two test modules import", text)`, saw the
        text return and read that as recovery. Measured on that render: the
        store held four records, the board came out with three, and the command
        exited 0 saying it had rendered.

        That state is worse than the drift it claims to repair, because the
        next honest `intake-write --from-board` would then delete the fourth
        record from the store — the shrink `USER-906` was answered with an
        invariant against.

        So the command refuses, names what it could not place, and writes
        nothing. The repair for a hand-deleted row is to put the row back, or
        to import deliberately if the BOARD is the one that is right."""
        p = self._imported()
        board = p.root / "BOARD.md"
        before = board.read_bytes()
        lines = board.read_text().split("\n")
        del lines[next(i for i, l in enumerate(lines)
                       if "two test modules import" in l)]
        board.write_text("\n".join(lines))
        shrunk = board.read_bytes()
        out = self._tasks(p.root, "intake-render", "--write")
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        self.assertIn("no line in it to render into", out.stderr)
        self.assertEqual(board.read_bytes(), shrunk,
                         "a refused write still changed the board")
        self.assertNotEqual(board.read_bytes(), before,
                            "control: the hand edit is still in place")
        # The detection layer is untouched: `diff` still reports the drift.
        self.assertEqual(self._tasks(p.root, "intake-diff").returncode, 1)


if __name__ == "__main__":
    unittest.main()
