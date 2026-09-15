"""TASK-237 deliverable 3b — `## Cadence` gets a store; the board names its project.

`TASK-237-spec.md § Amendment 2026-09-14 (5) § Deliverable 3b`, items 1 and
(the board-title half of) 2, and item 3's `project.name`:

1. `cadence.jsonl` is declared in `schema/state-schema.json § claims`, and its
   records carry the register's columns **as written** — prose in `Next due`
   and aperiodic frequencies are data, never normalised.
2. `cadence-add` / `cadence-done` write the store, the event and the journal,
   with or without `BOARD.md`.
3. `perry-state § cadence` and `perry-tasks board` read the store.
4. `perry-tasks cadence-write --from-board` imports a board-only register, and
   refuses what it cannot hold.
5. `perry-tasks board` titles itself with the project's name and prints no
   template prose; `perry-state § project.name` is the same rule.

**No expectation here comes from a `BOARD.md`.** Expectations are the records
this module writes, the cells this module types into a board it builds (for
the import, whose input IS a board), and the arguments a command was given.
A board appears as absent, as FORGED (rows no store holds), as the render of
the stores, or as the import's input.

Run: python3 tests/parallel test_cadence_store
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import inproc

ROOT = Path(__file__).resolve().parent.parent
STATE_TOOL = ROOT / "bin" / "perry-state"
sys.path.insert(0, str(ROOT / "viewer"))
sys.path.insert(0, str(ROOT / "bin"))
from tables import split_row  # noqa: E402

SCHEMA = json.loads((ROOT / "schema" / "state-schema.json").read_text(encoding="utf-8"))
BOARD_SPEC = next(f for f in SCHEMA["files"] if f.get("id") == "board")

CONFIG = [{"kind": "setting", "key": "state_root", "label": "State root",
           "value": "perry", "order": 0}]

#: One periodic row, one aperiodic row, one row whose `Next due` is prose.
CADENCE = [
    {"id": "CAD-001", "title": "weekly close", "owner": "PMO Agent",
     "frequency": "weekly", "next_due": "2026-09-21", "last_run": "2026-09-14",
     "last_evidence": "evidence/close.md", "order": 0},
    {"id": "CAD-002", "title": "board maintenance", "owner": "PMO Agent",
     "frequency": "continuous", "next_due": "n/a", "last_run": "",
     "last_evidence": "", "order": 1},
    {"id": "CADENCE-003", "title": "月末复盘", "owner": "PMO+User",
     "frequency": "monthly",
     "next_due": "**2026-08-31**（7 月版 ✅ 8/3 补作 → `evidence/2026-08/retro.md`；"
                 "6 月版跳过）",
     "last_run": "", "last_evidence": "", "order": 2},
]

#: The column each stored field is printed under, written here rather than
#: imported from `bin/perry_store.py`, so a mutation of the store's own map
#: cannot move the expectation with it.
COLUMN_FIELD = {"ID": "id", "Recurring task": "title", "Owner": "owner",
                "Frequency": "frequency", "Next due": "next_due",
                "Last run": "last_run", "Last evidence": "last_evidence"}

FORGED_BOARD = """# Board — forged

## Cadence (recurring)

| ID | Recurring task | Owner | Frequency | Next due | Last run | Last evidence |
|---|---|---|---|---|---|---|
| CAD-777 | forged ritual | nobody | daily | 2026-01-01 | 2025-12-31 | forged.md |
"""

TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:\d{2}|Z)?")


def jsonl(records) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").split("\n")
            if l.strip()]


def by_id(records, rid):
    return next(r for r in records if r.get("id") == rid)


class Project:
    """A configured project, state root `perry/`, holding a cadence store."""

    def __init__(self, cadence=CADENCE, board: str | None = None):
        self.tmp = tempfile.mkdtemp(prefix="t237d3b-")
        self.root = Path(self.tmp)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.jsonl").write_text(jsonl(CONFIG),
                                                          encoding="utf-8")
        (self.root / ".perry" / "events.jsonl").write_text("", encoding="utf-8")
        self.state = self.root / "perry"
        (self.state / "evidence").mkdir(parents=True)
        (self.state / "evidence" / "run.md").write_text("# run\n", encoding="utf-8")
        (self.state / "tasks.jsonl").write_text("", encoding="utf-8")
        if cadence is not None:
            self.store.write_text(jsonl(cadence), encoding="utf-8")
        if board is not None:
            self.board.write_text(board, encoding="utf-8")

    @property
    def store(self) -> Path:
        return self.state / "cadence.jsonl"

    @property
    def board(self) -> Path:
        return self.state / "BOARD.md"

    def task(self, argv):
        return inproc.run("perry-task", list(argv) + ["--root", str(self.root)])

    def tasks(self, argv):
        return inproc.run("perry-tasks", list(argv) + ["--root", str(self.root)])

    def state_json(self, *argv) -> dict:
        out = subprocess.run([sys.executable, str(STATE_TOOL), *argv,
                              "--root", str(self.root)],
                             capture_output=True, text=True, cwd=self.tmp)
        if out.returncode != 0:
            raise AssertionError(out.stderr[-600:])
        return json.loads(out.stdout)

    def journal(self) -> Path:
        return (self.state / "journal" / f"{date.today():%Y-%m}"
                / f"{date.today():%Y-%m-%d}.md")

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


def board_section(text: str, heading_prefix: str) -> dict:
    """`{header, rows}` of the first table under a `## <prefix>…` heading."""
    lines = text.split("\n")
    at = next(i for i, l in enumerate(lines) if l.startswith(f"## {heading_prefix}"))
    i = next(j for j in range(at + 1, len(lines)) if lines[j].startswith("|"))
    header = split_row(lines[i])
    rows = []
    j = i + 2
    while j < len(lines) and lines[j].startswith("|"):
        rows.append(split_row(lines[j]))
        j += 1
    return {"header": header, "rows": rows}


# ── the claim ──────────────────────────────────────────────────────────────


class TestTheClaim(unittest.TestCase):

    def test_the_store_is_declared_beside_the_other_registers(self):
        claims = {c["path"]: c for c in SCHEMA["claims"]}
        self.assertIn("cadence.jsonl", claims)
        for sibling in ("risks.jsonl", "intake.jsonl", "asks.jsonl"):
            with self.subTest(sibling=sibling):
                self.assertEqual(
                    {k: claims["cadence.jsonl"][k] for k in ("kind", "owner", "anchor")},
                    {k: claims[sibling][k] for k in ("kind", "owner", "anchor")})

    def test_the_register_verbs_come_from_the_claim(self):
        self.assertEqual(inproc.load("perry-tasks").registers().get("cadence"),
                         "cadence-")


# ── reads ──────────────────────────────────────────────────────────────────


class ReadsTheStore:
    board_text: str | None = None

    def setUp(self):
        self.p = Project(board=self.board_text)
        self.addCleanup(self.p.close)

    def test_perry_state_carries_every_stored_cell_as_written(self):
        got = self.p.state_json("--section", "cadence")["cadence"]
        self.assertEqual(got["count"], len(CADENCE))
        self.assertEqual(
            [(i["id"], i["title"], i["owner"], i["frequency"], i["next_due"],
              i["last_run"], i["last_evidence"]) for i in got["items"]],
            [(c["id"], c["title"], c["owner"], c["frequency"], c["next_due"],
              c["last_run"], c["last_evidence"]) for c in CADENCE])
        kinds = {i["id"]: i["frequency_kind"] for i in got["items"]}
        self.assertEqual(kinds["CAD-002"], "aperiodic")
        self.assertEqual(kinds["CAD-001"], "period")

    def test_board_prints_every_stored_row_cell_whole(self):
        out = self.p.tasks(["board"])
        self.assertEqual(out.returncode, 0, out.stderr)
        table = board_section(out.stdout, "Cadence")
        spec = next(t for t in BOARD_SPEC["tables"] if re.search(t["under"], "Cadence"))
        columns = list(spec["columns"]) + list(spec.get("optional_columns") or {})
        self.assertEqual(table["header"], columns)
        self.assertEqual(table["rows"],
                         [[c[COLUMN_FIELD[col]] for col in columns] for c in CADENCE])


class TestReadsWithNoBoard(ReadsTheStore, unittest.TestCase):
    board_text = None

    def test_the_fixture_carries_every_shape(self):
        """Anti-vacuity: a periodic, an aperiodic and a prose `Next due` row."""
        self.assertFalse(self.p.board.exists())
        sys.path.insert(0, str(ROOT / "viewer"))
        import parsers as P
        kinds = {c["id"]: (P.parse_frequency(c["frequency"]) or ("",))[0]
                 for c in CADENCE}
        self.assertEqual(sorted(kinds.values()), ["aperiodic", "period", "period"])
        self.assertTrue(any("（" in c["next_due"] and "**" in c["next_due"]
                            for c in CADENCE))


class TestReadsWithAForgedBoard(ReadsTheStore, unittest.TestCase):
    board_text = FORGED_BOARD

    def test_no_forged_row_reaches_a_payload(self):
        self.assertIn("CAD-777", self.p.board.read_text(encoding="utf-8"))
        blobs = (json.dumps(self.p.state_json("--section", "cadence")),
                 self.p.tasks(["board"]).stdout)
        for blob in blobs:
            self.assertNotIn("CAD-777", blob)
            self.assertNotIn("forged ritual", blob)


# ── writes ─────────────────────────────────────────────────────────────────


def landed(p: Project, argv) -> dict:
    events_before = (p.root / ".perry" / "events.jsonl").read_text(encoding="utf-8")
    journal_before = p.journal().read_text(encoding="utf-8") if p.journal().exists() else ""
    out = p.task(argv)
    norm = lambda s: TS.sub("<TS>", s.replace(str(p.root), "<ROOT>"))  # noqa: E731
    return {"exit": out.returncode, "stderr": out.stderr, "stdout": out.stdout,
            "store": read_jsonl(p.store),
            "store_text": p.store.read_text(encoding="utf-8") if p.store.exists() else None,
            "events": norm((p.root / ".perry" / "events.jsonl")
                           .read_text(encoding="utf-8")[len(events_before):]),
            "journal": norm((p.journal().read_text(encoding="utf-8")
                             if p.journal().exists() else "")[len(journal_before):])}


class TestTheWritesLandInTheStore(unittest.TestCase):

    def test_add_lands_the_record_the_event_and_the_journal_with_no_board(self):
        p = Project(cadence=None)
        self.addCleanup(p.close)
        got = landed(p, ["cadence-add", "--title", "nightly research",
                         "--frequency", "hourly", "--owner", "Job Daemon"])
        self.assertEqual(got["exit"], 0, got["stderr"])
        self.assertEqual(len(got["store"]), 1)
        rec = got["store"][0]
        self.assertEqual((rec["id"], rec["title"], rec["owner"], rec["frequency"]),
                         ("CAD-001", "nightly research", "Job Daemon", "hourly"))
        self.assertIn('"event": "cadence-add"', got["events"])
        self.assertIn("CAD-001", got["journal"])
        self.assertFalse(p.board.exists(), "a write created BOARD.md")
        self.assertIn("cadence.jsonl", got["stdout"])

    def test_done_recomputes_the_due_date_and_leaves_every_other_cell_alone(self):
        p = Project()
        self.addCleanup(p.close)
        ran = date(2026, 9, 10)
        got = landed(p, ["cadence-done", "CAD-001", "--evidence",
                         "perry/evidence/run.md", "--on", f"{ran:%Y-%m-%d}"])
        self.assertEqual(got["exit"], 0, got["stderr"])
        rec = by_id(got["store"], "CAD-001")
        self.assertEqual((rec["last_run"], rec["next_due"], rec["last_evidence"]),
                         (f"{ran:%Y-%m-%d}", f"{ran + timedelta(weeks=1):%Y-%m-%d}",
                          "perry/evidence/run.md"))
        for other in CADENCE[1:]:
            with self.subTest(row=other["id"]):
                self.assertEqual(by_id(got["store"], other["id"]), other)
        self.assertIn('"event": "cadence-done"', got["events"])
        self.assertTrue(got["journal"].strip())
        self.assertFalse(p.board.exists())

    def test_an_aperiodic_frequency_is_stored_as_given(self):
        p = Project()
        self.addCleanup(p.close)
        got = landed(p, ["cadence-done", "CAD-002", "--evidence",
                         "perry/evidence/run.md", "--on", "2026-09-12"])
        self.assertEqual(got["exit"], 0, got["stderr"])
        rec = by_id(got["store"], "CAD-002")
        self.assertEqual(rec["frequency"], "continuous")
        self.assertEqual(rec["last_run"], "2026-09-12")

    def test_a_write_is_the_same_with_and_without_the_file(self):
        """Store, event and journal equal; the present file keeps its bytes and
        stderr names it retired (TASK-262 round 4a — it was re-rendered)."""
        cases = (["cadence-add", "--title", "monthly close", "--frequency",
                  "monthly", "--on", "2026-08-31"],
                 ["cadence-done", "CADENCE-003", "--evidence",
                  "perry/evidence/run.md", "--on", "2026-09-01"])
        for argv in cases:
            with self.subTest(write=argv[0]):
                absent, present = Project(), Project()
                self.addCleanup(absent.close)
                self.addCleanup(present.close)
                render = present.tasks(["board"])
                self.assertEqual(render.returncode, 0, render.stderr)
                present.board.write_text(render.stdout, encoding="utf-8")
                before = present.board.read_text(encoding="utf-8")
                a, b = landed(absent, argv), landed(present, argv)
                self.assertEqual((a["exit"], b["exit"]), (0, 0),
                                 a["stderr"][-300:] + b["stderr"][-300:])
                self.assertEqual(a["store_text"], b["store_text"])
                self.assertEqual(a["events"], b["events"])
                self.assertEqual(a["journal"], b["journal"])
                self.assertEqual(present.board.read_text(encoding="utf-8"), before,
                                 "a write rewrote the retired BOARD.md")
                self.assertIn("is a retired board", b["stderr"])
                self.assertNotIn("is a retired board", a["stderr"])
                self.assertFalse(absent.board.exists())

    def hand_deleted(self) -> Project:
        """A project whose file lost `CAD-002`'s row by hand; the store did not."""
        p = Project()
        self.addCleanup(p.close)
        render = p.tasks(["board"])
        row = next(l for l in render.stdout.split("\n") if l.startswith("| CAD-002 "))
        p.board.write_text(render.stdout.replace(row + "\n", ""), encoding="utf-8")
        return p

    #: **Both rewritten for TASK-262 round 4a.** The write built its board from
    #: the held file, so a row deleted from the file alone was about to leave
    #: the store: `cadence-done` was refused as a shrink (3 → 2) and
    #: `cadence-add` reported `CAD-002` as substituted away. A write now builds
    #: from `cadence.jsonl`, so the hand edit reaches neither: no record moves,
    #: nothing is refused or reported, and the file keeps the edit. The shrink
    #: refusal and the substitution report are still in `commit()`;
    #: `tests/test_register_store_invariant.py` and
    #: `tests/test_register_substitution.py` hold them.

    def test_a_row_deleted_from_the_file_alone_is_not_a_retirement(self):
        """The store is the register: a hand-deleted row is not a retirement."""
        p = self.hand_deleted()
        held = p.board.read_bytes()
        out = p.task(["cadence-done", "CAD-001", "--evidence",
                      "perry/evidence/run.md"])
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertEqual([r["id"] for r in read_jsonl(p.store)],
                         [r["id"] for r in CADENCE])
        self.assertEqual(by_id(read_jsonl(p.store), "CAD-002"), CADENCE[1])
        self.assertEqual(p.board.read_bytes(), held)

    def test_a_hand_deletion_under_an_add_destroys_and_reports_nothing(self):
        p = self.hand_deleted()
        out = p.task(["cadence-add", "--title", "x", "--frequency", "weekly"])
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("CAD-002", out.stderr)
        last = read_jsonl(p.root / ".perry" / "events.jsonl")[-1]
        self.assertNotIn("substituted", last)
        self.assertEqual(by_id(read_jsonl(p.store), "CAD-002"), CADENCE[1])


    def test_a_repeated_id_in_the_store_is_refused_by_its_lint_rule(self):
        """`load_register_records` names the rule a reader runs to find it —
        `cadence-store-badly-typed`, not `key[:-1]`'s `cadenc-…`."""
        p = Project()
        self.addCleanup(p.close)
        render = p.tasks(["board"])
        p.board.write_text(render.stdout, encoding="utf-8")
        p.store.write_text(jsonl(CADENCE + [dict(CADENCE[0], title="dup")]),
                           encoding="utf-8")
        store = p.store.read_bytes()
        out = p.task(["cadence-add", "--title", "x", "--frequency", "weekly"])
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("`cadence-store-badly-typed`", out.stderr)
        self.assertEqual(p.store.read_bytes(), store)


class TestTheLintCensusCarriesTheCadenceStore(unittest.TestCase):
    """`check_cadence_store_drift`: `check_ask_store_drift`, one register over."""

    @staticmethod
    def lint(p: Project) -> dict:
        out = subprocess.run([sys.executable, str(ROOT / "bin" / "perry-lint"),
                              "--json", "--root", str(p.root)],
                             capture_output=True, text=True, cwd=p.tmp)
        return json.loads(out.stdout)

    def test_the_store_is_claimed_as_a_file_perry_wrote(self):
        """Without this every project holding the store gets an `NS-01`
        against Perry's own claim — measured on the payload-diff copies of
        this change before it was fixed: `cadence.jsonl holds 1 file(s) Perry
        did not write`. Matched on `file`, not on a message substring."""
        p = Project()
        self.addCleanup(p.close)
        lint = inproc.load("perry-lint")
        self.assertTrue(lint.looks_like_perry_record(p.store))
        self.assertEqual(
            [f for f in self.lint(p)["findings"]
             if f["rule"] == "NS-01" and f["file"].endswith("cadence.jsonl")], [])

    def test_with_no_file_it_is_silent_and_counts_the_records(self):
        """TASK-237 3c: no board file, nothing to drift from — no
        `cadence-store-drift-uncheckable` (which said drift was unknown)."""
        p = Project()
        self.addCleanup(p.close)
        got = self.lint(p)
        self.assertEqual(got["cadence_store_drift"]["records"], len(CADENCE))
        self.assertTrue(got["cadence_store_drift"]["store_present"])
        self.assertNotIn("cadence-store-drift-uncheckable",
                         [f["rule"] for f in got["findings"]])

    def test_a_hand_edit_to_a_prose_cell_is_drift_and_the_render_is_not(self):
        for edited in (False, True):
            with self.subTest(edited=edited):
                p = Project()
                self.addCleanup(p.close)
                text = p.tasks(["board"]).stdout
                if edited:
                    self.assertIn(CADENCE[2]["next_due"], text)
                    text = text.replace(CADENCE[2]["next_due"], "2026-09-30")
                p.board.write_text(text, encoding="utf-8")
                got = self.lint(p)
                drift = [f for f in got["findings"] if f["rule"] == "cadence-store-drift"]
                self.assertTrue(got["cadence_store_drift"]["comparison_performed"])
                self.assertEqual(got["cadence_store_drift"]["drifted"], int(edited))
                self.assertEqual(len(drift), int(edited))
                if edited:
                    self.assertIn(CADENCE[2]["id"], drift[0]["message"])


# ── the import ─────────────────────────────────────────────────────────────


def import_board(header: list[str], rows: list[list[str]]) -> str:
    """A board whose `## Cadence` holds exactly these cells, as typed."""
    table = ["| " + " | ".join(header) + " |",
             "|" + "---|" * len(header)]
    table += ["| " + " | ".join(r) + " |" for r in rows]
    return ("# Board — import\n\n## P1\n\n"
            "| ID | Title | Owner | Status | Next action | Evidence |\n"
            "|---|---|---|---|---|---|\n\n"
            "## Cadence (recurring; 不占槽位)\n\n" + "\n".join(table) + "\n")


FIVE = ["ID", "Recurring task", "Owner", "Frequency", "Next due"]
FIVE_ROWS = [
    ["CADENCE-000", "Execution board maintenance", "PMO Agent", "continuous", "n/a"],
    ["CADENCE-002", "End-month retrospective", "PMO+User", "monthly",
     "**2026-08-31**（7 月版 ✅ 8/3 补作 → `evidence/2026-08/retro.md`；6 月版跳过）"],
    ["CADENCE-NIGHTLY", "research nightly — cost ≤ $5/day", "Job Daemon + PMO",
     "hourly", "continuous"],
    ["CADENCE-OQ-WATCH", "每周扫信号(passive)", "User + PMO", "weekly",
     "2026-W32（W23–W31 停摆；并入 friday-review）"],
]
SIX = ["ID", "Recurring task", "Owner", "Frequency", "Next due", "Last evidence"]
SIX_ROWS = [["CAD-001", "Keep `AIMARK.md` current", "Coding Agent", "per task",
             "ongoing", "`CLAUDE.md:10-27`"]]


class ImportProject(Project):
    def __init__(self, board: str):
        super().__init__(cadence=None, board=board)


class TestTheImport(unittest.TestCase):

    def expected(self, header, rows):
        out = []
        for n, row in enumerate(rows):
            cells = dict(zip(header, row))
            out.append({"id": cells["ID"], "title": cells["Recurring task"],
                        "owner": cells["Owner"], "frequency": cells["Frequency"],
                        "next_due": cells["Next due"],
                        "last_run": cells.get("Last run", ""),
                        "last_evidence": cells.get("Last evidence", ""),
                        "order": n})
        return out

    def test_every_cell_is_stored_as_written(self):
        for header, rows in ((FIVE, FIVE_ROWS), (SIX, SIX_ROWS)):
            with self.subTest(columns=len(header)):
                p = ImportProject(import_board(header, rows))
                self.addCleanup(p.close)
                out = p.tasks(["cadence-write", "--from-board"])
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assertEqual(read_jsonl(p.store), self.expected(header, rows))

    def test_the_section_renders_back_from_the_records(self):
        for header, rows in ((FIVE, FIVE_ROWS), (SIX, SIX_ROWS)):
            with self.subTest(columns=len(header)):
                p = ImportProject(import_board(header, rows))
                self.addCleanup(p.close)
                before = p.board.read_bytes()
                self.assertEqual(p.tasks(["cadence-write", "--from-board"]).returncode, 0)
                diff = p.tasks(["cadence-diff"])
                self.assertEqual(diff.returncode, 0, diff.stdout[-600:])
                report = json.loads(diff.stdout)
                self.assertTrue(report["identical"])
                self.assertEqual(report["source"], "store")
                self.assertEqual(report["rows_from_store"], len(rows))
                self.assertEqual(p.board.read_bytes(), before)

    def test_the_import_appends_no_event(self):
        p = ImportProject(import_board(FIVE, FIVE_ROWS))
        self.addCleanup(p.close)
        self.assertEqual(p.tasks(["cadence-write", "--from-board"]).returncode, 0)
        self.assertEqual((p.root / ".perry" / "events.jsonl").read_text(), "")

    def refused(self, board: str, argv=("cadence-write", "--from-board")):
        p = ImportProject(board)
        self.addCleanup(p.close)
        out = p.tasks(list(argv))
        self.assertNotEqual(out.returncode, 0, out.stdout)
        self.assertFalse(p.store.exists(), "a refused import wrote the store")
        return out

    def test_the_control_imports(self):
        """The fixture every refusal below starts from, unrefused."""
        p = ImportProject(import_board(FIVE, FIVE_ROWS))
        self.addCleanup(p.close)
        self.assertEqual(p.tasks(["cadence-write", "--from-board"]).returncode, 0)
        self.assertTrue(p.store.exists())

    def test_it_refuses_without_from_board(self):
        out = self.refused(import_board(FIVE, FIVE_ROWS), ("cadence-write",))
        self.assertIn("--from-board", out.stderr)

    def test_it_refuses_when_the_claim_is_not_declared(self):
        mod = inproc.load("perry-tasks")
        real = mod.lib.load_schema

        def without_claim(*a, **kw):
            schema = real(*a, **kw)
            return {**schema, "claims": [c for c in schema.get("claims", [])
                                         if c.get("path") != "cadence.jsonl"]}

        with mock.patch.object(mod.lib, "load_schema", without_claim):
            out = self.refused(import_board(FIVE, FIVE_ROWS))
        self.assertIn("refusing to write `cadence.jsonl`", out.stderr)

    def test_it_refuses_a_section_that_is_not_a_readable_table(self):
        prose = ("# Board — import\n\n## Cadence\n\nWe run a retro monthly.\n")
        foreign = import_board(["ID", "Recurring task", "Owner"],
                               [["CAD-001", "retro", "PMO"]])
        absent = "# Board — import\n\n## P1\n\n| ID | Title |\n|---|---|\n"
        for name, board, why in (("prose", prose, "holds no table"),
                                 ("foreign", foreign, "no `Frequency` column"),
                                 ("absent", absent, "no `## Cadence` section")):
            with self.subTest(shape=name):
                self.assertIn(why, self.refused(board).stderr)

    def test_it_refuses_a_row_it_would_not_store(self):
        rows = FIVE_ROWS + [["**", "a row with no id", "PMO", "weekly", "n/a"]]
        out = self.refused(import_board(FIVE, rows))
        self.assertIn("holds no handle", out.stderr)

    def test_it_refuses_a_column_no_field_holds(self):
        header = FIVE + ["Notes"]
        rows = [r + ["kept only in the file"] for r in FIVE_ROWS]
        out = self.refused(import_board(header, rows))
        self.assertIn("'Notes'", out.stderr)

    def test_it_refuses_a_repeated_id(self):
        rows = FIVE_ROWS + [list(FIVE_ROWS[0])]
        self.refused(import_board(FIVE, rows))


# ── the board's title and prose (Amendment (4) item 3) ─────────────────────


TEMPLATE_PATH = ROOT / BOARD_SPEC["template"]


class TestTheBoardNamesItsProjectAndPrintsNoProse(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.p = Project()
        cls.out = cls.p.tasks(["board"])

    @classmethod
    def tearDownClass(cls):
        cls.p.close()

    def test_the_title_is_the_project_directory_name(self):
        # The trailing ` †` is TASK-262's mark: no record holds the name, the
        # render supplies it. The name itself is this case's subject.
        self.assertEqual(self.out.returncode, 0, self.out.stderr)
        self.assertEqual(self.out.stdout.split("\n")[0],
                         f"# Board — {self.p.root.name} †")

    def test_no_placeholder_is_printed(self):
        self.assertIn("{{", TEMPLATE_PATH.read_text(encoding="utf-8"),
                      "the template has no placeholder left to leak")
        self.assertNotIn("{{", self.out.stdout)

    def test_no_template_prose_is_printed(self):
        # TASK-262 prints two kinds of `> ` line, and only in two places: the
        # legend, directly under the title, and one line directly under each
        # `## ` heading. A `>` line anywhere else is the template's own block
        # leaking, which is this case's subject.
        lines = self.out.stdout.split("\n")
        for n, line in enumerate(lines):
            with self.subTest(line=line[:60]):
                placed = line.startswith("> ") and n > 0 and (
                    lines[n - 1].startswith("## ")
                    or (n == 1 and line.startswith("> † = not stored")))
                self.assertTrue(line == "" or placed
                                or line.startswith(("#", "|")), line)
        self.assertFalse(re.search(r"\n\n\n", self.out.stdout))

    def test_every_template_heading_and_table_stays(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8").split("\n")
        headings = [l for l in template if l.startswith("## ")]
        printed = [l for l in self.out.stdout.split("\n") if l.startswith("## ")]
        self.assertEqual(printed, headings)
        separators = lambda ls: sum(1 for l in ls if re.match(r"^\|\s*:?-{2,}", l))  # noqa: E731
        self.assertEqual(separators(self.out.stdout.split("\n")), separators(template))

    def test_a_heading_placeholder_no_source_fills_refuses(self):
        import perry_store
        template = TEMPLATE_PATH.read_text(encoding="utf-8").replace(
            "## P2", "## P2 {{quarter}}")
        with self.assertRaises(perry_store.UnfilledPlaceholder):
            perry_store.declared_board(BOARD_SPEC, template, {}, project_name="x")
        text, _ = perry_store.declared_board(
            BOARD_SPEC, TEMPLATE_PATH.read_text(encoding="utf-8"), {},
            project_name="x")
        self.assertTrue(text.startswith("# Board — x\n"))


class TestProjectNameIsTheSameRule(unittest.TestCase):
    """3b item 3: `perry-state § project.name` without the file was the STATE
    root's directory name (`perry`). It is the project root's, like the title."""

    def test_with_no_board_and_with_a_board_naming_something_else(self):
        for board in (None, FORGED_BOARD):
            with self.subTest(board="absent" if board is None else "forged"):
                p = Project(board=board)
                self.addCleanup(p.close)
                name = p.state_json("--json")["project"]["name"]
                self.assertEqual(name, p.root.name)
                self.assertNotEqual(name, p.state.name)


if __name__ == "__main__":
    unittest.main()
