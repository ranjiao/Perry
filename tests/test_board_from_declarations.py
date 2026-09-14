"""TASK-237 deliverable 1 — `perry-tasks board` prints the board from the stores alone.

`TASK-237-spec.md § Amendment (2)` (USER-932 answer 3): with no `BOARD.md`, a
render that reads only the four stores, `.perry/config.jsonl`,
`schema/state-schema.json` and `work/state/BOARD_TEMPLATE.md` prints every row
once, in its declared section, with every declared column and every cell whole.

**No expectation in this module comes from a `BOARD.md`, and no test here reads
one.** An expectation derived from the file is the defect, not the check
(`§ What deliverables 1 and 2 must not do`, item 3). Expectations come from:

* the STORES, read as JSONL here, and turned into cell text by `expected_cell`
  below — written here, not imported from `bin/perry_store.py`, so a mutation of
  the renderer's own cell rule cannot move the expectation with it;
* `schema/state-schema.json § files[id=board]` for sections and columns;
* `COLUMN_FIELD` below for which store field a column shows — also written
  here, for the same reason.

The output is read back with `viewer/tables.py § split_row`, the one reader,
which undoes the one escaping rule (`\\|`).

Two projects. `Fixture` holds every shape the render has to carry: a pipe in a
cell, a 2,500-byte cell, an empty and a two-item list, a null, a closed task,
a task in an undeclared group, a record with no `order`, an intake row. The
LIVE STORES are copied from this checkout into a temp project with no
`BOARD.md`, so the longest real next action is checked whole.

Run: python3 tests/parallel test_board_from_declarations
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin" / "perry-tasks"
sys.path.insert(0, str(ROOT / "viewer"))
from tables import split_row  # noqa: E402

import inproc  # noqa: E402

SCHEMA = json.loads((ROOT / "schema" / "state-schema.json").read_text(encoding="utf-8"))
SPEC = next(f for f in SCHEMA["files"] if f.get("id") == "board")
TERMINAL = ("done", "dropped")
REGISTERS = ("tasks", "asks", "risks", "intake")

#: The column a register's record shows each field under. `None` is a column
#: the store holds no field for (`Idle`, an age), which prints empty.
COLUMN_FIELD = {
    "tasks": {"ID": "id", "Title": "title", "Owner": "owner", "Status": "status",
              "Next action": "next_action", "Evidence": "evidence",
              "Track": "track", "Verification": "verification",
              "Stage": "stage", "Arrived": "arrived",
              "Commitment": "commitment", "Stage since": "stage_since",
              "Parent": "parent", "Depends on": "depends_on", "Role": "role"},
    "asks": {"USER-id": "id", "Needed from user": "needed", "Blocks": "blocks",
             "Status": "status", "Asked": "asked", "Idle": None},
    "risks": {"ID": "id", "Risk": "risk", "Opened": "opened", "Status": "status"},
    "intake": {"Arrived": "arrived", "Request": "request", "Outcome": "outcome"},
}

#: A heading each register's declared table sits under, so the table spec is
#: found through the schema's own `under` pattern rather than by index.
SECTION_NAME = {"tasks": "P1", "asks": "User Input Queue",
                "risks": "Top risks", "intake": "Intake"}


def table_spec(register: str) -> dict:
    return next(t for t in SPEC["tables"]
                if re.search(t["under"], SECTION_NAME[register]))


def declared_columns(table: dict) -> list[str]:
    return list(table["columns"]) + list(table.get("optional_columns") or {})


def expected_cell(rec: dict, field: str | None) -> str:
    if field is None:
        return ""
    v = rec.get(field)
    if isinstance(v, list):
        v = ", ".join(v)
    return ("" if v is None else str(v)).strip()


def read_stores(state: Path) -> dict[str, list[dict]]:
    out = {}
    for name in REGISTERS:
        p = state / f"{name}.jsonl"
        out[name] = ([json.loads(l) for l in p.read_text(encoding="utf-8").split("\n")
                      if l.strip()] if p.exists() else [])
    return out


def sections(text: str) -> list[dict]:
    """`[{title, header, rows}]` per `## ` section that holds a table.

    A header cell's trailing ` †` is TASK-262's not-stored mark, and is
    dropped here: whether it is on the right columns is
    `test_board_names_its_sources`'s question, and this module's is whether
    the declared columns are there. Only a HEADER cell is touched; a row cell
    is compared whole."""
    out, title, lines = [], None, text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            title = line[3:].strip()
        if line.startswith("|") and i + 1 < len(lines) and lines[i + 1].startswith("|"):
            header = [c[:-len(" †")] if c.endswith(" †") else c
                      for c in split_row(line)]
            j = i + 2
            rows = []
            while j < len(lines) and lines[j].startswith("|"):
                rows.append(split_row(lines[j]))
                j += 1
            out.append({"title": title, "header": header, "rows": rows})
            i = j
            continue
        i += 1
    return out


def home_of(register: str, rec: dict, titles: list[str]) -> str:
    """The section title a record must be printed under."""
    if register != "tasks":
        return next(t for t in titles if re.search(table_spec(register)["under"], t))
    group = rec.get("group") or ""
    for t in titles:
        h = next((h for h in SPEC["headings"] if re.search(h["match"], t)), None)
        if (h and re.search(table_spec("tasks")["under"], t)
                and re.search(h["match"], group)):
            return t
    return group or "(no group)"


def population(stores) -> list[tuple[str, dict]]:
    return ([("tasks", r) for r in stores["tasks"] if r.get("status") not in TERMINAL]
            + [(n, r) for n in ("asks", "risks", "intake") for r in stores[n]])


def board(root: Path):
    return inproc.run("perry-tasks", ["board", "--root", str(root)])


LONG = ("Re-measure the whole board with the file gone | then compare every cell "
        "against its store value, not against a file. ") * 25


def task(tid, order, group="P1", status="not_started", **kw):
    rec = {"id": tid, "title": f"title of {tid}", "summary": "", "owner": "Coding Agent",
           "status": status, "priority": "P1", "track": "main", "stage": "",
           "stage_since": "", "arrived": "", "verification": "V3", "evidence": "",
           "next_action": f"next for {tid}", "depends_on": [], "design_refs": [],
           "commitment": "", "parent": "", "group": group, "role": "",
           "created": "2026-09-14", "order": order}
    rec.update(kw)
    return rec


class Fixture:
    """A board-less project holding every shape the render has to carry."""

    TASKS = [
        task("TASK-010", 1, next_action=LONG, evidence="a | b"),
        task("TASK-011", 0, depends_on=["TASK-010", "ADR-001"], stage=None),
        task("TASK-012", None, group="P0 (must finish this period)"),
        task("TASK-013", 2, group="P2", status="done"),
        task("TASK-014", 3, group="P2", status="blocked"),
        task("TASK-015", 0, group="Someday"),
    ]
    ASKS = [{"id": "USER-001", "needed": "a threshold | or two", "blocks": "TASK-010",
             "asked": "2026-09-01", "status": "open", "answered": False, "order": 0}]
    RISKS = [{"id": "RX-001", "risk": "the store is wrong on a row", "opened": "",
              "cleared": "", "status": "open", "order": 0}]
    INTAKE = [{"order": 0, "arrived": "2026-09-10", "request": "print the board",
               "outcome": "", "discharged": False}]

    def __init__(self, tasks=None):
        self.tmp = tempfile.mkdtemp(prefix="t237d1-")
        self.root = Path(self.tmp)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.jsonl").write_text(json.dumps(
            {"kind": "setting", "key": "state_root", "label": "State root",
             "value": "perry", "order": 0}) + "\n", encoding="utf-8")
        self.state = self.root / "perry"
        self.state.mkdir()
        for name, recs in (("tasks", self.TASKS if tasks is None else tasks),
                           ("asks", self.ASKS), ("risks", self.RISKS),
                           ("intake", self.INTAKE)):
            (self.state / f"{name}.jsonl").write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs),
                encoding="utf-8")

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


def live_copy() -> tuple[str, Path]:
    """This checkout's stores and config, in a temp project with no BOARD.md."""
    tmp = tempfile.mkdtemp(prefix="t237d1-live-")
    root = Path(tmp)
    (root / ".perry").mkdir()
    shutil.copy2(ROOT / ".perry" / "config.jsonl", root / ".perry" / "config.jsonl")
    settings = {r["key"]: r["value"] for r in
                (json.loads(l) for l in (ROOT / ".perry" / "config.jsonl")
                 .read_text(encoding="utf-8").split("\n") if l.strip())
                if r.get("kind") == "setting"}
    state = root / settings.get("state_root", "")
    state.mkdir(parents=True, exist_ok=True)
    for name in REGISTERS:
        src = ROOT / settings.get("state_root", "") / f"{name}.jsonl"
        if src.exists():
            shutil.copy2(src, state / f"{name}.jsonl")
    return tmp, state


class CellWhole:
    """The three properties, asserted over one project. Mixed into two cases."""

    root: Path
    state: Path

    def render(self):
        out = board(self.root)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertFalse((self.state / "BOARD.md").exists(),
                         "this case must run with no BOARD.md on disk")
        return out.stdout

    def test_every_declared_column_is_in_its_section(self):
        got = sections(self.render())
        titles = [s["title"] for s in got]
        template_headings = [l[3:].strip() for l in
                             (ROOT / SPEC["template"]).read_text(encoding="utf-8")
                             .split("\n") if l.startswith("## ")]
        checked = 0
        for s in got:
            spec = next((t for t in SPEC["tables"] if re.search(t["under"], s["title"])),
                        None)
            if spec is None and s["title"] not in template_headings:
                spec = table_spec("tasks")          # an undeclared group's section
            with self.subTest(section=s["title"]):
                self.assertIsNotNone(spec, f"{s['title']!r} has no declared table")
                self.assertEqual(s["header"], declared_columns(spec))
                for row in s["rows"]:
                    self.assertEqual(len(row), len(s["header"]), row[:1])
                checked += 1
        for h in SPEC["headings"]:
            with self.subTest(heading=h["label"]):
                self.assertTrue(any(re.search(h["match"], t) for t in titles),
                                f"declared heading {h['label']} printed no table")
        self.assertGreaterEqual(checked, len(SPEC["headings"]))

    def test_every_store_row_appears_exactly_once_in_its_declared_section(self):
        got = sections(self.render())
        titles = [s["title"] for s in got]
        stores = read_stores(self.state)
        pop = population(stores)
        self.assertTrue(pop, "an empty population asserts nothing")
        printed = sum(len(s["rows"]) for s in got)
        self.assertEqual(printed, len(pop),
                         f"{printed} rows printed for {len(pop)} store rows")
        for register, rec in pop:
            with self.subTest(register=register, row=rec.get("id", rec.get("order"))):
                home = home_of(register, rec, titles)
                cols = declared_columns(table_spec(register))
                key = cols[0]
                want = expected_cell(rec, COLUMN_FIELD[register][key])
                where = [s["title"] for s in got for row in s["rows"]
                         if s["header"] == cols and row[0] == want]
                if register == "intake":
                    self.assertIn(home, where)
                else:
                    self.assertEqual(where, [home])

    def test_every_cell_equals_the_store_value(self):
        got = sections(self.render())
        titles = [s["title"] for s in got]
        stores = read_stores(self.state)
        for register in REGISTERS:
            pop = [r for n, r in population(stores) if n == register]
            by_home: dict[str, list[dict]] = {}
            for r in pop:
                by_home.setdefault(home_of(register, r, titles), []).append(r)
            for home, recs in by_home.items():
                s = next(s for s in got if s["title"] == home)
                graded = sorted(
                    enumerate(recs),
                    key=lambda nr: (not isinstance(nr[1].get("order"), int),
                                    nr[1].get("order") if isinstance(
                                        nr[1].get("order"), int) else 0, nr[0]))
                cols = s["header"]
                self.assertEqual(len(s["rows"]), len(recs), home)
                for row, (_n, rec) in zip(s["rows"], graded):
                    for col, cell in zip(cols, row):
                        with self.subTest(section=home, row=row[0][:12], column=col):
                            self.assertEqual(
                                cell, expected_cell(rec, COLUMN_FIELD[register][col]))


class TestAFixtureProject(CellWhole, unittest.TestCase):

    def setUp(self):
        self.fx = Fixture()
        self.root, self.state = self.fx.root, self.fx.state
        self.addCleanup(self.fx.close)

    def test_the_fixture_carries_every_shape(self):
        """Anti-vacuity: the cases above are only as strong as these shapes."""
        stores = read_stores(self.state)
        cells = [expected_cell(r, f) for n, r in population(stores)
                 for f in COLUMN_FIELD[n].values() if f]
        self.assertTrue(any("|" in c for c in cells), "no pipe in any cell")
        self.assertTrue(any(len(c.encode()) >= 2000 for c in cells), "no long cell")
        self.assertTrue(any(", " in c for c in cells), "no multi-item list")
        self.assertTrue(any(r.get("status") in TERMINAL for r in stores["tasks"]))
        self.assertTrue(any(r.get("order") is None for r in stores["tasks"]))
        for n in REGISTERS:
            self.assertTrue(stores[n], f"no {n} record")

    def test_a_closed_task_is_not_printed(self):
        text = self.render()
        self.assertNotIn("TASK-013", text)
        self.assertIn("TASK-014", text)

    def test_a_task_in_an_undeclared_group_is_printed_and_named(self):
        out = board(self.root)
        self.assertEqual(out.returncode, 0, out.stderr)
        got = sections(out.stdout)
        someday = [s for s in got if s["title"] == "Someday"]
        self.assertEqual(len(someday), 1)
        self.assertEqual([r[0] for r in someday[0]["rows"]], ["TASK-015"])
        self.assertIn("Someday", out.stderr)

    def test_a_pipe_is_escaped_once(self):
        text = self.render()
        self.assertIn("| a \\| b |", text)

    def test_a_value_with_a_line_break_is_refused_and_nothing_printed(self):
        fx = Fixture(tasks=[task("TASK-020", 0, next_action="line one\nline two")])
        self.addCleanup(fx.close)
        out = board(fx.root)
        self.assertEqual(out.returncode, 1, out.stdout[:200])
        self.assertEqual(out.stdout, "")
        self.assertIn("TASK-020", out.stderr)
        self.assertIn("Next action", out.stderr)

    def test_a_malformed_store_is_refused_and_nothing_printed(self):
        (self.state / "risks.jsonl").write_text("{not json\n", encoding="utf-8")
        out = board(self.root)
        self.assertEqual(out.returncode, 2)
        self.assertEqual(out.stdout, "")
        self.assertIn("risks.jsonl", out.stderr)


class TestThisProjectsStores(CellWhole, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp, cls.state = live_copy()
        cls.root = Path(cls.tmp)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_longest_next_action_is_whole(self):
        """TASK-391's was 2,218 bytes at 5fa66a7f. The row is not named here, so the
        case survives it closing; the length floor keeps it from going vacuous."""
        stores = read_stores(self.state)
        open_tasks = [r for r in stores["tasks"] if r.get("status") not in TERMINAL]
        longest = max(open_tasks, key=lambda r: len((r.get("next_action") or "").encode()))
        want = expected_cell(longest, "next_action")
        self.assertGreaterEqual(len(want.encode()), 1000,
                                "the live store has no long next action to check")
        got = [row for s in sections(self.render()) for row in s["rows"]
               if row and row[0] == longest["id"]]
        self.assertEqual(len(got), 1)
        cols = declared_columns(table_spec("tasks"))
        self.assertEqual(got[0][cols.index("Next action")], want)


#: Runs the tool with every file open logged, and any open of a `BOARD.md`
#: refused. Imports go through `io.open_code`, which is not patched, so the log
#: holds the data files the tool reads and nothing else.
DRIVER = r"""
import builtins, io, json, os, runpy, sys
log_path, tool, args = sys.argv[1], sys.argv[2], sys.argv[3:]
opened = []
real = {"builtins": builtins.open, "io": io.open, "os": os.open}
def note(p):
    if isinstance(p, int):
        return
    s = os.path.abspath(os.fsdecode(p))
    opened.append(s)
    if os.path.basename(s) == "BOARD.md":
        raise PermissionError("the render opened " + s)
builtins.open = lambda f, *a, **k: (note(f), real["builtins"](f, *a, **k))[1]
io.open = lambda f, *a, **k: (note(f), real["io"](f, *a, **k))[1]
os.open = lambda f, *a, **k: (note(f), real["os"](f, *a, **k))[1]
sys.argv = [tool, *args]
code = 0
try:
    runpy.run_path(tool, run_name="__main__")
except SystemExit as exc:
    code = exc.code or 0
finally:
    with real["builtins"](log_path, "w") as fh:
        json.dump(opened, fh)
sys.exit(code)
"""

GARBAGE = (b"\xff\xfe# Board \xe2\x80\x94 not this one\n## P1\n\n| ID | Title |\n|---|---|\n"
           b"| TASK-010 | forged |\n\x00\x01" + bytes(range(256)))


class TestTheFileIsNeverRead(unittest.TestCase):

    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        self.board_path = self.fx.state / "BOARD.md"

    def traced(self):
        log = self.fx.root / "opened.json"
        env = {k: v for k, v in os.environ.items() if k != "PERRY_PROJECT"}
        out = subprocess.run(
            [sys.executable, "-c", DRIVER, str(log), str(TOOL), "board",
             "--root", str(self.fx.root)],
            capture_output=True, text=True, env=env, cwd=str(self.fx.root))
        opened = json.loads(log.read_text(encoding="utf-8"))
        log.unlink()
        return out, opened

    def test_the_render_is_the_same_bytes_with_no_board_and_with_garbage(self):
        absent = board(self.fx.root)
        self.assertEqual(absent.returncode, 0, absent.stderr)
        self.board_path.write_bytes(GARBAGE)
        garbage = board(self.fx.root)
        self.assertEqual(garbage.returncode, 0, garbage.stderr)
        self.assertEqual(garbage.stdout, absent.stdout)
        self.assertNotIn("forged", garbage.stdout)

    def test_the_render_never_opens_board_md(self):
        self.board_path.write_bytes(GARBAGE)
        out, opened = self.traced()
        self.assertEqual([p for p in opened if os.path.basename(p) == "BOARD.md"], [],
                         out.stderr[-400:])
        self.assertEqual(out.returncode, 0, out.stderr[-400:])

    def test_the_render_reads_only_the_declared_files(self):
        self.board_path.write_bytes(GARBAGE)
        out, opened = self.traced()
        self.assertEqual(out.returncode, 0, out.stderr[-400:])
        home = ROOT.resolve()
        declared = {str((home / "schema" / "state-schema.json").resolve()),
                    str((home / SPEC["template"]).resolve()),
                    str((self.fx.root / ".perry" / "config.jsonl").resolve()),
                    # TASK-262: the section lines' writers are this file's
                    # `SURFACE`, read as a literal.
                    str((home / "bin" / "perry-task").resolve())}
        declared |= {str((self.fx.state / f"{n}.jsonl").resolve()) for n in REGISTERS}
        data = {str(Path(p).resolve()) for p in opened
                if not p.endswith((".py", ".pyc"))}
        self.assertLessEqual(data, declared, sorted(data - declared))
        # The log is not empty by accident: the reads that must happen, happened.
        for must in ("state-schema.json", "BOARD_TEMPLATE.md", "tasks.jsonl"):
            self.assertTrue(any(p.endswith(must) for p in data), must)


if __name__ == "__main__":
    unittest.main()
