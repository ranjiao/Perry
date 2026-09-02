"""`## Top risks` is a projection of a record store — ADR-007 again.

TASK-040. The row was minted as *"Top risks becomes a table with id / opened /
cleared"*, failed review, and the re-review found the root cause was **four
implementations** of "what is a risk row". ADR-007 then superseded the premise:
the answer to a register four readers disagree about is not a better table.

So this file checks two things, in this order, because the order is the
argument:

1. **The store can reproduce what it replaces, byte for byte, before it holds
   a single field the table could not.** A migration that cannot reproduce
   what it replaces has not read it, and a renderer that quietly keeps a cell
   verbatim passes `cmp` while reproducing nothing — so the report's own
   fallback counters are asserted to be zero, not just the bytes.

2. **The four readers are one function, by identity and not by agreement.**
   `tests/test_risks.py` compares the reader's predicate against the writer's
   over a corpus, which is the best a test can do while there are two. There
   is one now, so the assertion is `is`.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

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

#: Perry's own register, quoted from `perry/BOARD.md` — an open row with no
#: `Opened` date, a cleared row carrying one inside its `Status` cell, and
#: prose in the `Risk` cells with backticks, an em-dash and a strikethrough in
#: it. The section this store has to reproduce is a real one or the byte gate
#: is being run against text written to pass it.
REGISTER = (
    "| ID | Risk | Opened | Status |\n"
    "|---|---|---|---|\n"
    "| RX-001 | Perry is half-adopted: `.perry/config.md` exists and flips "
    "`is_adopted()`. | | open |\n"
    "| RX-002 | ~~`LOAD-03` (10 decisions queued on the user)~~ — cleared "
    "2026-08-16 when DESIGN-003's 8 rows were decided. | | cleared 2026-08-16 "
    "— the queue drained |\n"
    "| RX-003 | DESIGN-003 phase G rewrites `SKILL.md § The hand-off "
    "contract`. | 2026-08-18 | open |\n"
)


def board_with(section: str) -> str:
    h = "| ID | Title | Owner | Status | Next action | Evidence |"
    sep = "|" + "|".join(["---"] * 6) + "|"
    return (
        "# Board — T\n\n"
        f"## P0 (must finish this period)\n\n{h}\n{sep}\n\n"
        f"## P1\n\n{h}\n{sep}\n\n"
        f"## P2\n\n{h}\n{sep}\n\n"
        "## Top risks (one-line; full list in `PROJECT_STATE.md`)\n\n"
        f"{section}\n"
    )


def derive(text: str, current: list[dict] | None = None):
    """(board, ops, records) for a board given as text."""
    import tempfile
    tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
    tmp.write(text)
    tmp.close()
    board = PT.Board(Path(tmp.name))
    return board, PT, S.risk_records(board, PT, current)


class TestByteIdentityComesFirst(unittest.TestCase):
    """Item 1. **Before `cleared` exists**, the store has to put the section
    back exactly as it found it."""

    def test_the_section_round_trips_byte_for_byte(self):
        text = board_with(REGISTER)
        board, ops, records = derive(text)
        rendered, report = S.risk_render(board, records, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["rows_from_store"], 3)

    def test_no_cell_survived_as_a_literal(self):
        """`cmp` alone cannot tell a rebuilt cell from a copied one.

        `describe_cell` keeps a cell verbatim when no stored field claims it
        and keeps prose around a stored value as a prefix/suffix. Both are
        legitimate and both come back byte-identical, so a renderer that
        reproduced nothing would pass the test above. These three counters are
        what makes the byte result mean something.
        """
        board, ops, records = derive(board_with(REGISTER))
        _, report = S.risk_render(board, records, ops)
        self.assertEqual(report["cells_verbatim"], {})
        self.assertEqual(report["cells_wearing_decoration"], {})
        self.assertEqual(report["cells_the_store_and_board_disagree_on"], [])
        self.assertEqual(report["rows_verbatim"], [])
        self.assertEqual(report["rows_not_on_board"], [])

    def test_byte_identity_does_not_depend_on_the_new_field(self):
        """**The ordering the row asked for, as a test.**

        `cleared` is the field the register could not express in a cell. If
        the byte gate needed it, the gate would be testing the new field
        rather than the migration. Stripped from every record, the section
        still reproduces — because `cleared` renders into no column at all.
        """
        text = board_with(REGISTER)
        board, ops, records = derive(text)
        stripped = [{k: v for k, v in r.items() if k != "cleared"}
                    for r in records]
        rendered, report = S.risk_render(board, stripped, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["cells_verbatim"], {})

    def test_a_wrong_stored_value_reddens_the_gate(self):
        """A renderer that cannot be made to print a wrong value cannot be
        shown to print a right one."""
        text = board_with(REGISTER)
        board, ops, records = derive(text)
        records[0]["status"] = "cleared 2020-01-01"
        rendered, report = S.risk_render(board, records, ops)
        self.assertNotEqual(rendered, text)
        self.assertIn("cleared 2020-01-01", rendered)
        self.assertEqual(
            [d["column"] for d in report["cells_the_store_and_board_disagree_on"]],
            ["Status"])

    def test_a_pipe_in_a_risk_statement_round_trips(self):
        section = ("| ID | Risk | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-001 | the header `\\| ID \\| Risk \\|` is ambiguous | "
                   "2026-08-01 | open |\n")
        text = board_with(section)
        board, ops, records = derive(text)
        self.assertEqual(records[0]["risk"],
                         "the header `| ID | Risk |` is ambiguous")
        self.assertEqual(S.risk_render(board, records, ops)[0], text)

    def test_every_row_of_the_register_is_a_record(self):
        """**The store does not decide what a project may call a risk.**

        A first cell this tool would not have minted — `| 2 待核项 |`, from a
        real board — is still a row of the register, so it becomes a record and
        renders from one. Filtering rows against an id pattern here would
        invent a rule and quietly demote somebody's row to layout;
        `perry-lint`'s `bad-id` check is where a handle that does not match the
        declared pattern is reported, and reporting is the whole posture.
        """
        section = ("| ID | Risk | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-001 | first | | open |\n"
                   "| 2 待核项 | not a handle this tool would mint | | |\n")
        text = board_with(section)
        board, ops, records = derive(text)
        self.assertEqual([r["id"] for r in records], ["RX-001", "2 待核项"])
        rendered, report = S.risk_render(board, records, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["rows_verbatim"], [])

    def test_a_repeated_id_does_not_leave_a_hole_in_the_order(self):
        """`order` is a position among the rows the STORE holds, not among the
        lines — the rule `board_order` states for tasks. A second row carrying
        an id the store already has is not a second record, and letting it
        advance the counter would leave a gap in a sequence whose only job is
        to say which record comes before which."""
        section = ("| ID | Risk | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-001 | first | | open |\n"
                   "| RX-001 | a duplicate somebody pasted | | open |\n"
                   "| RX-002 | second | | open |\n")
        _b, _o, records = derive(board_with(section))
        self.assertEqual([(r["id"], r["order"]) for r in records],
                         [("RX-001", 0), ("RX-002", 1)])

    def test_columns_resolve_by_name_in_both_directions(self):
        """`schema/README.md § Columns resolve by name`. A register a human
        wrote is not obliged to put `ID` first, and reading the id off
        `cells[0]` while writing every other cell by resolved name is how one
        row's value lands in another row's column."""
        section = ("| Status | Risk | ID | Opened |\n"
                   "|---|---|---|---|\n"
                   "| open | the vendor contract lapses | RX-001 | 2026-08-01 |\n")
        text = board_with(section)
        board, ops, records = derive(text)
        self.assertEqual(records[0]["id"], "RX-001")
        self.assertEqual(records[0]["status"], "open")
        rendered, report = S.risk_render(board, records, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["rows_from_store"], 1)
        self.assertEqual(report["cells_verbatim"], {})

    def test_a_localized_register_round_trips(self):
        """`reference/i18n.md`: a board may be written in the project's own
        language, and columns resolve by name."""
        section = ("| 编号 | 风险 | 提出 | 状态 |\n"
                   "|---|---|---|---|\n"
                   "| RX-001 | 供应商合同到期 | 2026-08-01 | open |\n")
        text = board_with(section)
        board, ops, records = derive(text)
        self.assertEqual(records[0]["risk"], "供应商合同到期")
        self.assertEqual(records[0]["opened"], "2026-08-01")
        self.assertEqual(S.risk_render(board, records, ops)[0], text)


class TestOpenedAndClearedAreReal(unittest.TestCase):
    """Item 3, including the trap on the other side of it."""

    def test_a_cleared_risk_carries_both_dates(self):
        _b, _o, records = derive(board_with(REGISTER))
        by_id = {r["id"]: r for r in records}
        self.assertEqual(by_id["RX-002"]["cleared"], "2026-08-16")
        self.assertEqual(by_id["RX-003"]["opened"], "2026-08-18")

    def test_a_risk_with_neither_date_is_not_invented_one(self):
        """**The `current: 0` defect, one register over.** A default that
        stands in for an unrecorded fact reads as a recorded one."""
        _b, _o, records = derive(board_with(REGISTER))
        by_id = {r["id"]: r for r in records}
        self.assertEqual(by_id["RX-001"]["opened"], "")
        self.assertEqual(by_id["RX-001"]["cleared"], "")

    def test_a_risk_cleared_without_a_date_carries_no_date(self):
        section = ("| ID | Risk | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-001 | the vendor contract lapses | | cleared |\n")
        _b, _o, records = derive(board_with(section))
        self.assertEqual(records[0]["cleared"], "")
        self.assertEqual(records[0]["status"], "cleared")

    def test_the_store_is_what_cleared_means_once_there_is_one(self):
        """ADR-007 decision 2: the store is the value, the prose is a
        projection of it. A hand edit to the `Status` cell does not silently
        replace a stored date — `check_risk_store_drift` reports it."""
        stored = [{"id": "RX-002", "risk": "x", "opened": "",
                   "cleared": "2026-08-16", "status": "cleared 2026-08-16",
                   "order": 0}]
        section = ("| ID | Risk | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-002 | x | | cleared 2099-01-01 |\n")
        _b, _o, records = derive(board_with(section), stored)
        self.assertEqual(records[0]["cleared"], "2026-08-16")

    def test_perry_state_emits_a_cleared_risks_dates(self):
        """A cleared risk is not in `items` — it is not a top risk — so before
        `cleared_items` its dates were emitted by nothing at all."""
        p = Project(board=board_with(REGISTER))
        out = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"],
            capture_output=True, text=True)
        risks = json.loads(out.stdout)["risks"]
        self.assertEqual([r["id"] for r in risks["cleared_items"]], ["RX-002"])
        self.assertEqual(risks["cleared_items"][0]["cleared_on"], "2026-08-16")
        self.assertNotIn("RX-002", [r["id"] for r in risks["items"]])
        self.assertEqual([r["opened"] for r in risks["items"]
                          if r["id"] == "RX-003"], ["2026-08-18"])


class TestTheReadersAreOneFunction(unittest.TestCase):
    """Item 4. `tests/test_risks.py` asserts the reader and the writer AGREE
    over a corpus, which is the strongest claim available while there are two
    of them. These assert there is one."""

    def test_the_register_header_predicate_is_one_object(self):
        self.assertIs(PT.is_risk_header, P.is_risk_register_header)

    def test_the_bullet_and_placeholder_rules_are_one_object(self):
        self.assertIs(PT._RISK_BULLET, P._RE_RISK_BULLET)
        self.assertIs(PT._RISK_PLACEHOLDER, P._RE_RISK_PLACEHOLDER)

    def test_the_columns_are_one_list(self):
        self.assertIs(PT.RISK_COLUMNS, P.RISK_COLUMNS)

    def test_the_writer_asks_the_store_which_table_is_the_register(self):
        """`bin/perry-task § risk_section_shape` used to scan the section
        itself. It delegates now, so "which table is the register" is answered
        once for the writer, the reader and the renderer."""
        board, ops, _ = derive(board_with(REGISTER))
        self.assertEqual(PT.risk_section_shape(board)[0], "table")
        self.assertEqual(S.risk_section_shape(board, ops)[0], "table")

    def test_clearing_a_risk_a_human_retired_is_refused(self):
        """The concrete cost of the fourth copy. `cmd_risk_clear` knew three
        of the eight words the reader knows, so a risk retired as `mitigated`
        read as live here and as cleared everywhere else — and clearing it
        again overwrote the first clear's date and its reason."""
        section = ("| ID | Risk | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-001 | the vendor contract lapses | | mitigated "
                   "2026-01-04 — renewed |\n")
        p = Project(board=board_with(section))
        rc, out = p.run("risk-clear", "RX-001", "--reason", "again")
        self.assertEqual(rc, 1)
        self.assertIn("already cleared", json.dumps(out))
        self.assertIn("mitigated 2026-01-04 — renewed", p.board())


class TestAHandEditIsReported(unittest.TestCase):
    """Item 2. Reported at the severity the board's own drift check uses —
    `warn`, because the store is authoritative and rendering restores the
    projection. Reported, not refused."""

    def _lint(self, root: Path) -> dict:
        out = subprocess.run(
            [sys.executable, str(LINT), "--root", str(root), "--json"],
            capture_output=True, text=True)
        return json.loads(out.stdout)

    def _project(self, section: str, store: list[dict]) -> Project:
        # **Held on `self`.** `Project` owns a `TemporaryDirectory`, which
        # deletes the tree when the object is collected — so
        # `self._lint(self._project(...).root)` linted a path that no longer
        # existed and every drift assertion in this class failed with an empty
        # finding list, which is exactly what "no store" looks like.
        self._held = p = Project(board=board_with(section))
        (p.root / "risks.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in store))
        return p

    STORE = [{"id": "RX-001", "risk": "the vendor contract lapses",
              "opened": "2026-08-01", "cleared": "", "status": "open",
              "order": 0}]
    SECTION = ("| ID | Risk | Opened | Status |\n"
               "|---|---|---|---|\n"
               "| RX-001 | the vendor contract lapses | 2026-08-01 | open |\n")

    def test_a_clean_register_reports_nothing_and_says_it_compared(self):
        payload = self._lint(self._project(self.SECTION, self.STORE).root)
        self.assertEqual(payload["risk_store_drift"],
                         {"store_present": True, "comparison_performed": True,
                          "records": 1, "drifted": 0})
        self.assertEqual(
            [f for f in payload["findings"]
             if f["rule"].startswith("risk-store")], [])

    def test_a_hand_edited_cell_is_reported_as_a_warning(self):
        edited = self.SECTION.replace("the vendor contract lapses",
                                      "somebody typed this in by hand")
        payload = self._lint(self._project(edited, self.STORE).root)
        drifted = [f for f in payload["findings"] if f["rule"] == "risk-store-drift"]
        self.assertEqual(len(drifted), 1, drifted)
        self.assertEqual(drifted[0]["severity"], "warn")
        self.assertIn("RX-001", drifted[0]["message"])
        self.assertIn("`risk`", drifted[0]["message"])
        self.assertEqual(payload["risk_store_drift"]["drifted"], 1)
        # **Reported, not refused, and never an error.** A drifted register
        # still has a valid register shape, and the conformance gate's boundary
        # is precise: warnings are quality signals, errors are shape
        # violations. (The fixture board carries unrelated `missing-section`
        # errors, so `payload["errors"]` is not the assertion here — the
        # severity of THIS rule is.)
        self.assertEqual({f["severity"] for f in payload["findings"]
                          if f["rule"].startswith("risk-store")}, {"warn"})

    def test_a_hand_added_row_the_store_never_saw_is_reported(self):
        extra = self.SECTION + "| RX-002 | typed in by hand | | open |\n"
        payload = self._lint(self._project(extra, self.STORE).root)
        drifted = [f for f in payload["findings"] if f["rule"] == "risk-store-drift"]
        self.assertEqual(len(drifted), 1, drifted)
        self.assertIn("RX-002", drifted[0]["message"])
        self.assertIn("the store has no record of it", drifted[0]["message"])

    def test_a_stored_risk_the_section_does_not_render_is_reported(self):
        store = self.STORE + [{"id": "RX-002", "risk": "second", "opened": "",
                               "cleared": "", "status": "open", "order": 1}]
        payload = self._lint(self._project(self.SECTION, store).root)
        drifted = [f for f in payload["findings"] if f["rule"] == "risk-store-drift"]
        self.assertEqual(len(drifted), 1, drifted)
        self.assertIn("renders no row for it", drifted[0]["message"])

    def test_the_field_with_no_column_cannot_drift_and_is_not_lost(self):
        """**`cleared` renders into no cell, so nothing in the file can
        disagree with it** — and that is a property, not a hole.

        It is carried across every rebuild from the store, exactly as a task's
        `summary` is (`bin/perry-task § store_records`, ADR-009): a value the
        projection cannot express must not be recoverable from prose, or the
        store stops being what the field means. A hand edit that contradicts
        it is still caught, through the column that does exist — asserted in
        the test below.
        """
        store = [dict(self.STORE[0], cleared="2026-09-09")]
        payload = self._lint(self._project(self.SECTION, store).root)
        self.assertEqual(payload["risk_store_drift"]["drifted"], 0)
        self.assertEqual(
            [f for f in payload["findings"]
             if f["rule"] == "risk-store-drift"], [])

    def test_a_hand_written_cleared_date_is_reported_through_status(self):
        store = [dict(self.STORE[0], cleared="2026-08-16",
                      status="cleared 2026-08-16 — the vendor renewed")]
        edited = self.SECTION.replace("| open |", "| cleared 2099-01-01 |")
        payload = self._lint(self._project(edited, store).root)
        drifted = [f for f in payload["findings"] if f["rule"] == "risk-store-drift"]
        self.assertEqual(len(drifted), 1, drifted)
        self.assertIn("`status`", drifted[0]["message"])
        self.assertIn("2099-01-01", drifted[0]["message"])

    def test_a_row_moved_by_hand_is_reported_once_for_the_section(self):
        """`order` is a fact about a sequence, not about a row. Comparing it
        like the other fields turns one moved row into a finding for every row
        beneath it — the whole-section diff `order` exists to prevent,
        re-created inside the report about it (`_order_drift`)."""
        section = ("| ID | Risk | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-002 | second | | open |\n"
                   "| RX-001 | first | | open |\n")
        store = [{"id": "RX-001", "risk": "first", "opened": "", "cleared": "",
                  "status": "open", "order": 0},
                 {"id": "RX-002", "risk": "second", "opened": "", "cleared": "",
                  "status": "open", "order": 1}]
        payload = self._lint(self._project(section, store).root)
        drifted = [f for f in payload["findings"] if f["rule"] == "risk-store-drift"]
        self.assertEqual(len(drifted), 1, drifted)
        self.assertIn("file RX-002 → RX-001", drifted[0]["message"])
        self.assertIn("store RX-001 → RX-002", drifted[0]["message"])

    def test_no_store_is_not_a_clean_store(self):
        self._held = p = Project(board=board_with(self.SECTION))
        payload = self._lint(p.root)
        self.assertEqual(payload["risk_store_drift"]["store_present"], False)
        self.assertEqual(payload["risk_store_drift"]["comparison_performed"],
                         False)
        self.assertEqual(
            [f for f in payload["findings"]
             if f["rule"].startswith("risk-store")], [])

    def test_a_badly_typed_record_is_named_and_does_not_kill_the_lint(self):
        store = [dict(self.STORE[0], order="0")]
        payload = self._lint(self._project(self.SECTION, store).root)
        bad = [f for f in payload["findings"]
               if f["rule"] == "risk-store-badly-typed"]
        self.assertEqual(len(bad), 1, bad)
        self.assertIn("`order`", bad[0]["message"])
        self.assertEqual(payload["risk_store_drift"]["comparison_performed"],
                         False)

    def test_the_risks_store_is_not_reported_as_a_file_perry_did_not_write(self):
        """`looks_like_perry_record` knew one record shape. A risks store has
        fields outside `STORED`, so without this it is reported as foreign
        against Perry's own claim, on every project that has one."""
        import importlib.machinery
        import importlib.util
        spec = importlib.util.spec_from_loader(
            "perry_lint_mod",
            importlib.machinery.SourceFileLoader("perry_lint_mod", str(LINT)))
        lint = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lint)
        p = self._project(self.SECTION, self.STORE)
        self.assertTrue(lint.looks_like_perry_record(p.root / "risks.jsonl"))


class TestTheMigrationSurface(unittest.TestCase):

    def _tasks(self, root: Path, *argv):
        return subprocess.run([sys.executable, str(TASKS), *argv,
                               "--root", str(root)],
                              capture_output=True, text=True)

    def test_risks_diff_is_green_on_a_section_it_can_reproduce(self):
        p = Project(board=board_with(REGISTER))
        out = self._tasks(p.root, "risks-diff")
        self.assertEqual(out.returncode, 0, out.stderr)
        report = json.loads(out.stdout)
        self.assertTrue(report["identical"])
        self.assertEqual(report["source"], "board")
        self.assertEqual(report["rows_from_store"], 3)

    def test_risks_diff_reddens_when_the_store_and_the_section_disagree(self):
        p = Project(board=board_with(REGISTER))
        (p.root / "risks.jsonl").write_text(json.dumps(
            {"id": "RX-001", "risk": "not what the board says", "opened": "",
             "cleared": "", "status": "open", "order": 0}) + "\n")
        out = self._tasks(p.root, "risks-diff")
        self.assertEqual(out.returncode, 1)
        report = json.loads(out.stdout)
        self.assertFalse(report["identical"])
        self.assertEqual(report["source"], "store")
        self.assertIn("not what the board says",
                      report["first_difference"]["rendered"])

    def test_risks_render_write_refuses_without_a_store(self):
        """Rendering the section from records derived out of that same section
        writes the file back over itself and reports success."""
        p = Project(board=board_with(REGISTER))
        before = p.board()
        out = self._tasks(p.root, "risks-render", "--write")
        self.assertEqual(out.returncode, 2)
        self.assertIn("nothing to render", out.stderr)
        self.assertEqual(p.board(), before)

    def test_risks_build_names_the_shape_it_found(self):
        p = Project(board=board_with("- H · the vendor contract lapses\n"))
        report = json.loads(self._tasks(p.root, "risks-build").stdout)
        self.assertEqual(report["register"], "bullets")
        self.assertEqual(report["records"], 0)

    def test_risks_write_refuses_without_the_explicit_direction(self):
        """`--from-board` is the consent, not a modifier on a default.

        The import runs the direction ADR-007 decision 2 made backwards, so
        the flag is required and the refusal names the command that runs the
        other one."""
        p = Project(board=board_with(REGISTER))
        out = self._tasks(p.root, "risks-write")
        self.assertEqual(out.returncode, 1)
        self.assertIn("--from-board", out.stderr)
        self.assertIn("risks-render --write", out.stderr)
        self.assertFalse((p.root / "risks.jsonl").exists())


class TestTheOneWayImport(unittest.TestCase):
    """`perry-tasks risks-write --from-board` — `## Top risks` → the store.

    The half TASK-040 stopped before. It is the same one-way import
    `perry-tasks write --from-board` performs for tasks and `perry-okr write
    --from-file` for `OKR.md`: run once, at adoption, never in reverse.
    """

    def _tasks(self, root: Path, *argv):
        return subprocess.run([sys.executable, str(TASKS), *argv,
                               "--root", str(root)],
                              capture_output=True, text=True)

    def _imported(self, section: str = REGISTER) -> Project:
        """A project whose risks store was written by the command under test.

        **Held on `self`** — `Project` owns a `TemporaryDirectory` and deletes
        the tree when it is collected, the trap `TestAHandEditIsReported`
        records one class up.
        """
        self._held = p = Project(board=board_with(section))
        out = self._tasks(p.root, "risks-write", "--from-board")
        self.assertEqual(out.returncode, 0, out.stderr)
        return p

    def _store(self, p: Project) -> list[dict]:
        return [json.loads(l) for l in
                (p.root / "risks.jsonl").read_text().split("\n") if l.strip()]

    def _lint(self, root: Path) -> dict:
        out = subprocess.run(
            [sys.executable, str(LINT), "--root", str(root), "--json"],
            capture_output=True, text=True)
        return json.loads(out.stdout)

    # ── it produces a store the register is a projection of ────────────

    def test_the_import_writes_a_record_per_register_row(self):
        p = self._imported()
        self.assertEqual([r["id"] for r in self._store(p)],
                         ["RX-001", "RX-002", "RX-003"])

    def test_risks_diff_compares_against_a_real_store_and_is_green(self):
        """**The comparison that means something.** Storeless, `risks-diff`
        renders records derived out of the very section it compares them
        against and says so (`source: "board"`). With a store on disk the
        source is the store, and `cells_verbatim: {}` is what makes the bytes
        mean something — a cell that survives as a literal is a cell the
        renderer did not rebuild from a typed field."""
        p = self._imported()
        out = self._tasks(p.root, "risks-diff")
        self.assertEqual(out.returncode, 0, out.stderr)
        report = json.loads(out.stdout)
        self.assertTrue(report["identical"])
        self.assertEqual(report["source"], "store")
        self.assertEqual(report["cells_verbatim"], {})
        self.assertEqual(report["cells_wearing_decoration"], {})
        self.assertEqual(report["cells_the_store_and_board_disagree_on"], [])
        self.assertEqual(report["rows_verbatim"], [])
        self.assertEqual(report["rows_not_on_board"], [])

    def test_the_import_is_idempotent(self):
        """Two runs, the same bytes. `RISK_STORED` fixes the key order for
        exactly this reason: a store whose lines reshuffle turns every write
        into a whole-file diff."""
        p = self._imported()
        first = (p.root / "risks.jsonl").read_bytes()
        out = self._tasks(p.root, "risks-write", "--from-board")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual((p.root / "risks.jsonl").read_bytes(), first)

    def test_a_register_with_no_rows_imports_and_reads_back_as_a_store(self):
        """**An empty store is a store, and this is the flow that reaches
        one.** `BOARD_TEMPLATE.md` ships `- (no active risks)`;
        `perry-task risk-migrate` turns that section into a table with a
        header and no rows, and importing it is the honest thing — the
        register exists and holds nothing.

        `load_risk_store` returns `[]` for a file that is absent and for one
        that is empty, and `cmd_risks_render` read the second as the first, so
        this project's `risks-diff` reported `source: "board"` about a store
        sitting on disk. `risk_table` refuses that same conflation one layer
        down and `perry-lint` asks the path; this now does too.
        """
        p = self._imported("| ID | Risk | Opened | Status |\n|---|---|---|---|\n")
        self.assertEqual((p.root / "risks.jsonl").read_text(), "")
        report = json.loads(self._tasks(p.root, "risks-diff").stdout)
        self.assertEqual(report["source"], "store")
        self.assertTrue(report["identical"])
        self.assertEqual(report["register"], "table")
        self.assertEqual(report["rows_from_store"], 0)

    def test_a_project_with_no_store_still_reports_the_board_as_the_source(self):
        """The other half of the line above: absent is not empty either."""
        self._held = p = Project(board=board_with(REGISTER))
        report = json.loads(self._tasks(p.root, "risks-diff").stdout)
        self.assertEqual(report["source"], "board")
        self.assertEqual(report["rows_from_store"], 3)

    def test_a_risk_with_no_date_is_imported_as_empty_not_as_today(self):
        """The `current: 0` defect, at the one moment it would be easiest to
        commit: an import stamping today's date on a nine-month-old risk."""
        by_id = {r["id"]: r for r in self._store(self._imported())}
        self.assertEqual(by_id["RX-001"]["opened"], "")
        self.assertEqual(by_id["RX-001"]["cleared"], "")
        self.assertEqual(by_id["RX-002"]["cleared"], "2026-08-16")
        self.assertEqual(by_id["RX-003"]["opened"], "2026-08-18")

    def test_the_field_with_no_column_survives_a_re_import(self):
        """`cleared` is the one stored field the four columns cannot express,
        so `--from-board` has nothing to read for it and the store keeps it.
        Taking the board's silence as "no date" would delete a value on the
        second run of a command whose first run wrote it."""
        p = self._imported()
        records = self._store(p)
        records[0]["cleared"] = "2026-09-09"
        (p.root / "risks.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
        out = self._tasks(p.root, "risks-write", "--from-board")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self._store(p)[0]["cleared"], "2026-09-09")

    # ── the event log: the decision, asserted ──────────────────────────

    def test_the_import_appends_no_event(self):
        """**Stated in `cmd_risks_write` and tested here.** `risk-add` /
        `risk-clear` append events because a risk was raised or retired that
        day. An import raises nothing: every event it could append would carry
        today's timestamp for a row that may be nine months old — the same
        falsehood `opened: ""` refuses one assertion up — and `perry-state`
        reads that log."""
        p = self._imported()
        self.assertEqual(p.events(), [])

    # ── refuse rather than guess ───────────────────────────────────────

    def _refused(self, section: str, *argv):
        """Run a refused import and prove ADR-004: nothing was written.

        The board AND the store are byte-compared across the call, because
        "nothing was written" is a claim about every file the command can
        touch, not only about the one it was refusing to create.
        """
        self._held = p = Project(board=board_with(section))
        store = p.root / "risks.jsonl"
        before_board = (p.root / "BOARD.md").read_bytes()
        before_store = store.read_bytes() if store.exists() else None
        out = self._tasks(p.root, "risks-write", "--from-board", *argv)
        self.assertNotEqual(out.returncode, 0)
        self.assertEqual((p.root / "BOARD.md").read_bytes(), before_board)
        self.assertEqual(store.read_bytes() if store.exists() else None,
                         before_store)
        return p, out

    def test_a_bullet_list_is_refused_rather_than_imported_as_nothing(self):
        """The shape that would otherwise pass the byte gate and be wrong.
        `risk_records` returns `[]` for bullets, rendering `[]` changes no
        line, so `cmp` is clean — and an empty store would be written over a
        section holding real risks, reported as a success."""
        _p, out = self._refused("- H · the vendor contract lapses\n")
        self.assertIn("bullet list", out.stderr)
        self.assertIn("risk-migrate", out.stderr)

    def test_a_table_that_is_not_the_register_is_refused(self):
        _p, out = self._refused("| Severity | Meaning |\n|---|---|\n"
                                "| H | drop everything |\n")
        self.assertIn("must not treat as the register", out.stderr)

    def test_a_board_with_no_such_section_is_refused(self):
        h = "| ID | Title | Owner | Status | Next action | Evidence |"
        sep = "|" + "|".join(["---"] * 6) + "|"
        self._held = p = Project(board=(
            f"# Board — T\n\n## P0 (must finish this period)\n\n{h}\n{sep}\n\n"
            f"## P1\n\n{h}\n{sep}\n\n## P2\n\n{h}\n{sep}\n"))
        out = self._tasks(p.root, "risks-write", "--from-board")
        self.assertEqual(out.returncode, 1)
        self.assertIn("no `## Top risks` section", out.stderr)
        self.assertFalse((p.root / "risks.jsonl").exists())

    DUPLICATED = ("| ID | Risk | Opened | Status |\n"
                  "|---|---|---|---|\n"
                  "| RX-001 | first | | open |\n"
                  "| RX-001 | a duplicate somebody pasted | | open |\n"
                  "| RX-002 | second | | open |\n")

    def test_a_section_the_records_cannot_reproduce_is_refused_by_row_and_cell(self):
        """**A migration that cannot reproduce what it replaces has not
        understood it**, and this is a section where that really happens.

        A repeated id is ONE record — `order` counts records, not lines — but
        `risk_plan` renders both lines from it, so the second row would come
        back carrying the first row's `Risk`. The bytes catch it; the refusal
        has to name the row and the column, because "line 23 differs" does not
        tell anyone which of their rows the store misread.
        """
        _p, out = self._refused(self.DUPLICATED)
        self.assertIn("RX-001", out.stderr)
        self.assertIn("column Risk", out.stderr)
        self.assertIn("a duplicate somebody pasted", out.stderr)
        self.assertIn("Nothing was written", out.stderr)

    def test_a_refused_import_leaves_an_existing_store_byte_identical(self):
        """ADR-004 over a store that already exists, not only over one that
        does not: a refusal must not half-write, truncate or reorder it."""
        p = self._imported()
        before = (p.root / "risks.jsonl").read_bytes()
        board = p.root / "BOARD.md"
        board.write_text(board.read_text().replace(
            "| RX-003 | DESIGN-003", "| RX-001 | DESIGN-003"))
        before_board = board.read_bytes()
        out = self._tasks(p.root, "risks-write", "--from-board")
        self.assertEqual(out.returncode, 1)
        self.assertEqual((p.root / "risks.jsonl").read_bytes(), before)
        self.assertEqual(board.read_bytes(), before_board)

    def test_an_unreadable_store_is_not_overwritten(self):
        p = self._imported()
        (p.root / "risks.jsonl").write_text("{not json\n")
        out = self._tasks(p.root, "risks-write", "--from-board")
        self.assertEqual(out.returncode, 2)
        self.assertIn("cannot be read", out.stderr)
        self.assertEqual((p.root / "risks.jsonl").read_text(), "{not json\n")

    def test_a_malformed_store_is_not_overwritten(self):
        p = self._imported()
        (p.root / "risks.jsonl").write_text(
            json.dumps({"id": "RX-001", "order": "0"}) + "\n")
        out = self._tasks(p.root, "risks-write", "--from-board")
        self.assertEqual(out.returncode, 2)
        self.assertIn("malformed", out.stderr)
        self.assertIn("`order` is str", out.stderr)

    # ── the two checks that already existed, over a REAL store ─────────

    def test_a_corrupted_stored_value_diverges_at_the_right_column(self):
        """`test_a_wrong_stored_value_reddens_the_gate` proves this over a
        store built in-process. It has to hold over the file the import
        actually wrote, or the renderer is only known to be honest about
        records a test made up."""
        p = self._imported()
        records = self._store(p)
        records[0]["status"] = "cleared 2020-01-01"
        (p.root / "risks.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
        out = self._tasks(p.root, "risks-diff")
        self.assertEqual(out.returncode, 1)
        report = json.loads(out.stdout)
        self.assertEqual(report["source"], "store")
        self.assertEqual(
            [d["column"] for d in
             report["cells_the_store_and_board_disagree_on"]], ["Status"])

    def test_a_hand_edited_cell_still_raises_exactly_one_drift_warning(self):
        p = self._imported()
        board = p.root / "BOARD.md"
        board.write_text(board.read_text().replace(
            "DESIGN-003 phase G", "somebody typed this in by hand"))
        payload = self._lint(p.root)
        drifted = [f for f in payload["findings"]
                   if f["rule"] == "risk-store-drift"]
        self.assertEqual(len(drifted), 1, drifted)
        self.assertEqual(drifted[0]["severity"], "warn")
        self.assertIn("RX-003", drifted[0]["message"])
        self.assertEqual(payload["risk_store_drift"],
                         {"store_present": True, "comparison_performed": True,
                          "records": 3, "drifted": 1})

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
        """The declaration landed on 2026-08-21 and this command exists
        because of it. It reads the schema at every call rather than assuming
        the entry, so a project on a schema that does not carry it — an old
        install, a fork, a hand-edited file — still gets the refusal instead of
        an undeclared file in its state root.
        """
        mod = self._uut("perry_tasks_uut")
        self.assertTrue(mod.risk_store_is_declared(),
                        "schema/state-schema.json no longer claims "
                        "risks.jsonl — the declaration was reverted")

        self._held = p = Project(board=board_with(REGISTER))
        real = mod.risk_store_is_declared
        mod.risk_store_is_declared = lambda: False
        noise = io.StringIO()
        try:
            with contextlib.redirect_stderr(noise):
                rc = mod.cmd_risks_write(p.root, ["--from-board"])
        finally:
            mod.risk_store_is_declared = real
        self.assertIn("What is missing is the DECLARATION", noise.getvalue())
        self.assertEqual(rc, 1)
        self.assertFalse((p.root / "risks.jsonl").exists())

    def test_an_unreadable_schema_does_not_claim_the_file_is_declared(self):
        """"I cannot see it" is not "it is there" — the same rule that makes an
        unknown dependency id unsatisfied. A schema that will not load must
        read as undeclared, or a broken install writes a file nothing claims.
        """
        mod = self._uut("perry_tasks_uut2")
        real = mod.lib.load_schema
        mod.lib.load_schema = lambda *a, **k: (_ for _ in ()).throw(
            OSError("no schema here"))
        try:
            self.assertFalse(mod.risk_store_is_declared())
        finally:
            mod.lib.load_schema = real
        self.assertIn("What is missing is the DECLARATION",
                      mod.RISK_STORE_UNDECLARED)


if __name__ == "__main__":
    unittest.main()
