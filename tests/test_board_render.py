"""`perry/tasks.jsonl` → `BOARD.md`, and the bar is `cmp`, not "equivalent".

TASK-088, phase 002, ADR-007's first slice. **A renderer with no byte
comparison is the thing this task exists to prevent**, and the reason is one
`viewer/tables.py § render_row` already argues one row down: it refuses to
column-align because aligning "turns a one-cell edit into a whole-table diff
and buries the change nobody can then review". A renderer that normalizes does
that to the whole file, on the first write, forever — and nothing may stop
writing the board until it can be regenerated.

Two properties, and passing only the first is the failure mode:

1. **The bytes match.** `test_perrys_own_board` and `test_a_board_shaped_like
   _the_second_real_project` compare whole files.
2. **The bytes come from the STORE.** A renderer that copied the row lines
   would pass (1) perfectly. So every stored field is mutated on disk and the
   render has to move with it, and the one escape hatch that could hide a
   copy — the verbatim fallback — is asserted to be EMPTY on Perry's board and
   COUNTED everywhere else.

The second fixture is Perry's own shapes plus the ones measured on the second
real project on this machine, which is private and cannot be committed: a
`~~**ID**~~` id cell, a status cell that is two states in one sentence, a cell
with no space before its closing pipe, an escaped `\\|`, CJK headings that are
not `## P0`, and a row whose first cell is prose rather than a handle.

Run: python3 tests/parallel test_board_render
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
TOOL = ROOT / "bin" / "perry-tasks"

#: The shapes measured on the second real project, in one board. Written by
#: hand and NOT through `render_row`, because a fixture built by the writer
#: under test can only prove the writer agrees with itself.
SECOND_PROJECT_BOARD = """# Board — Fixture

> Live working memory. 前次 **2026-08-13**（一段带 `|` 转义的说明：\\| 是值不是分隔符）
>
> Last updated: 2026-08-13

## Open — 投资线（政策 · 配置 · 到期动作）

| ID | Title | Owner | Status | Next action |
|---|---|---|---|---|
| **USER-G1** | **P0** Gate 1 RM 问询（kr:P-O2.1）| User | not_started | 发 draft v2 |
| ~~**ALLOC-01**~~ | ✅ 部分解 —— IPS-01 一直存在 | Coding Agent | **迁移 done，占比目标 not_started** | 归档 |
| DUOL-TRIGGER1 | 表格引用 `\\| ID \\| Risk \\|` 在正文里 | User | in_progress | 复核 |

## P2 (低优先 carry)

| ID | Title | Owner | Status | Next action |
|---|---|---|---|---|
| 2 待核项 | 不是 handle，是散文 | — | — | — |
| TEMPLATES-3 | 研究模板三件套 | User+Agent | not_started | agent 起草 |
"""


def run(*args, root=ROOT):
    return subprocess.run([sys.executable, str(TOOL), *args,
                           "--root", str(root)],
                          capture_output=True, text=True, cwd=ROOT)


def store_of(root: pathlib.Path) -> pathlib.Path:
    return root / "tasks.jsonl" if (root / "BOARD.md").exists() \
        else root / "perry" / "tasks.jsonl"


def records(root: pathlib.Path) -> list[dict]:
    return [json.loads(l) for l in
            store_of(root).read_text(encoding="utf-8").split("\n") if l.strip()]


def rewrite(root: pathlib.Path, recs: list[dict]) -> None:
    store_of(root).write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n",
        encoding="utf-8")


def a_live_row(root: pathlib.Path) -> str:
    """Any id currently ON the board, chosen at run time.

    **This was hardcoded to `TASK-088` and then TASK-088 was closed**, so its
    row left the board and the tests failed on a project that was fine. A test
    pinned to a live task id is a test the project itself breaks — `done`
    removes the row, the same trap `check_verification` and `walk_design` both
    documented.

    Module-level rather than a method, because two TestCase classes need it and
    a second copy would be the defect this repository spends its time removing.
    """
    text = subprocess.run(
        [sys.executable, str(TOOL), "render", "--root", str(root)],
        capture_output=True, text=True).stdout
    for line in text.split("\n"):
        m = re.match(r"\| ([A-Z]+-\d+) ", line)
        if m:
            return m.group(1)
    raise AssertionError("no rendered row carries an id")


class Project:
    """A project on disk, with its store written from its board."""

    @staticmethod
    def perry(case) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp())
        case.addCleanup(shutil.rmtree, d, ignore_errors=True)
        shutil.copytree(ROOT / "perry", d / "perry",
                        ignore=shutil.ignore_patterns("*.lock"))
        shutil.copytree(ROOT / ".perry", d / ".perry",
                        ignore=shutil.ignore_patterns("*.lock"))
        assert run("write", "--from-board", root=d).returncode == 0
        return d

    @staticmethod
    def fixture(case, board: str) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp())
        case.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / ".perry").mkdir()
        (d / ".perry" / "config.md").write_text("# Config\n", encoding="utf-8")
        (d / "BOARD.md").write_text(board, encoding="utf-8")
        assert run("write", "--from-board", root=d).returncode == 0
        return d


class TestTheBytesMatch(unittest.TestCase):
    def board_bytes(self, root: pathlib.Path) -> bytes:
        p = root / "BOARD.md"
        return (p if p.exists() else root / "perry" / "BOARD.md").read_bytes()

    def rendered(self, root: pathlib.Path) -> bytes:
        proc = subprocess.run([sys.executable, str(TOOL), "render",
                               "--root", str(root)], capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode()[:500])
        return proc.stdout

    def test_perrys_own_board(self):
        """The live file, byte for byte — and with NO verbatim fallback.

        `identical: true` alone would also be true of a renderer that copied
        every row, so the two counters are asserted beside it."""
        d = Project.perry(self)
        self.assertEqual(self.rendered(d), self.board_bytes(d))
        out = json.loads(run("diff", root=d).stdout)
        self.assertTrue(out["identical"])
        self.assertEqual(out["rows_verbatim"], [])
        self.assertEqual(out["cells_verbatim"], {})
        self.assertGreater(out["rows_from_store"], 20)

    def test_a_board_shaped_like_the_second_real_project(self):
        d = Project.fixture(self, SECOND_PROJECT_BOARD)
        self.assertEqual(self.rendered(d), self.board_bytes(d))
        out = json.loads(run("diff", root=d).stdout)
        self.assertTrue(out["identical"], json.dumps(out, ensure_ascii=False))
        self.assertEqual(out["rows_from_store"], 4)

    def test_the_shapes_that_a_re_rendered_row_would_lose(self):
        """Each one on its own line, so a failure names which shape broke.

        Every one of these is a byte a `render_row` round trip moves: it pads
        `（kr:P-O2.1）|` to `（kr:P-O2.1） |`, and `strip_handle` has already
        thrown the `~~**` away before the store sees the id."""
        d = Project.fixture(self, SECOND_PROJECT_BOARD)
        got = self.rendered(d).decode()
        for shape in ("| ~~**ALLOC-01**~~ |",
                      "（kr:P-O2.1）| User |",
                      "**迁移 done，占比目标 not_started**",
                      "`\\| ID \\| Risk \\|`",
                      "| 2 待核项 |"):
            with self.subTest(shape=shape):
                self.assertIn(shape, got)

    def test_render_is_stable_across_two_runs(self):
        d = Project.perry(self)
        self.assertEqual(self.rendered(d), self.rendered(d))


class TestTheBytesComeFromTheStore(unittest.TestCase):
    """**The half a byte comparison cannot prove on its own.**

    A renderer that emitted the board's own row lines would pass every test
    above. So each stored field is changed ON DISK and the rendered board has
    to change with it — and where it cannot, the tool has to say so rather
    than quietly print the old value.
    """

    def rendered(self, root: pathlib.Path) -> str:
        return subprocess.run(
            [sys.executable, str(TOOL), "render", "--root", str(root)],
            capture_output=True, text=True).stdout


    def row_of(self, root: pathlib.Path, tid: str) -> str:
        """The one rendered line for `tid`. **Not the whole file.**

        `assertIn(mark, whole_board)` passes on any board that happens to
        contain the word somewhere else — `dropped` is in four other rows'
        prose — which would grade the wrong thing every time."""
        got = [l for l in self.rendered(root).split("\n")
               if l.startswith(f"| {tid} ")]
        self.assertEqual(len(got), 1, f"{tid}: {len(got)} rendered rows")
        return got[0]

    def test_every_rendered_field_moves_when_the_store_moves(self):
        d = Project.perry(self)
        tid = a_live_row(d)
        marks = {"title": "A TITLE NOTHING WROTE", "owner": "Nobody",
                 "next_action": "AN ACTION NOTHING WROTE",
                 "evidence": "evidence/nothing.md", "verification": "V6",
                 "status": "dropped", "depends_on": ["TASK-001", "TASK-002"]}
        for field, mark in marks.items():
            with self.subTest(field=field):
                recs = records(d)
                row = next(r for r in recs if r["id"] == tid)
                before = row[field]
                row[field] = mark
                rewrite(d, recs)
                want = ", ".join(mark) if isinstance(mark, list) else mark
                self.assertIn(f"| {want} |", self.row_of(d, tid),
                              f"{field} did not reach the board")
                row[field] = before
                rewrite(d, recs)
                self.assertNotIn(want, self.row_of(d, tid))

    def test_a_row_missing_from_the_store_is_reported_not_silently_copied(self):
        """**`cmp` clean and "reproduced" are different results.**

        Drop a record and the board still renders byte-identically, because
        the line the store cannot fill is kept verbatim. That is the escape
        hatch, and the only thing standing between it and a renderer that
        reproduces nothing is that it is counted. So: bytes still equal, and
        the report says the row was not rendered from the store."""
        d = Project.perry(self)
        board = (d / "perry" / "BOARD.md").read_bytes()
        gone = a_live_row(d)
        rewrite(d, [r for r in records(d) if r["id"] != gone])
        self.assertEqual(self.rendered(d).encode(), board)
        out = json.loads(run("diff", root=d).stdout)
        self.assertTrue(out["identical"])
        self.assertIn(gone,
                      json.dumps(out["rows_verbatim"], ensure_ascii=False))

    def test_a_cell_the_store_cannot_reproduce_is_counted(self):
        """The second project's four off-enum status cells, in one row.

        `**迁移 done，占比目标 not_started**` is two states in one sentence, so
        `status` is `""` and the cell is kept verbatim. Byte-clean, and the
        count says which column paid for it."""
        d = Project.fixture(self, SECOND_PROJECT_BOARD)
        out = json.loads(run("diff", root=d).stdout)
        self.assertTrue(out["identical"])
        self.assertEqual(out["cells_verbatim"], {"Status": 1})

    def test_a_store_row_no_line_holds_is_reported(self):
        d = Project.fixture(self, SECOND_PROJECT_BOARD)
        recs = records(d)
        ghost = dict(recs[0])
        ghost["id"] = "GHOST-001"
        rewrite(d, recs + [ghost])
        out = json.loads(run("diff", root=d).stdout)
        self.assertIn("GHOST-001", out["rows_not_on_board"])


class TestItRendersAndNothingElse(unittest.TestCase):
    def test_rendering_without_a_store_is_not_a_pass(self):
        """Exit 2 and nothing on stdout — the same answer `verify` gives.

        Building the store from the board and rendering it back would compare
        `split_row` with `render_row` and call it a proof."""
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        shutil.copytree(ROOT / "perry", d / "perry",
                        ignore=shutil.ignore_patterns("*.lock", "tasks.jsonl"))
        shutil.copytree(ROOT / ".perry", d / ".perry",
                        ignore=shutil.ignore_patterns("*.lock"))
# **`perry/tasks.jsonl` now EXISTS in this repository** — TASK-089 made
# it the write target, so a fixture that copies `perry/` inherits a store
# whether it wants one or not. A test about the NO-STORE case has to say
# so; two of them failed the moment the store was tracked, which is the
# transition working rather than a regression.
        proc = run("render", root=d)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")

    def test_render_and_diff_write_no_file(self):
        d = Project.perry(self)
        before = {p: p.read_bytes() for p in d.rglob("*") if p.is_file()}
        run("render", root=d)
        run("diff", root=d)
        after = {p: p.read_bytes() for p in d.rglob("*") if p.is_file()}
        self.assertEqual(before, after, "render/diff wrote to the project")

    def test_diff_exits_1_and_names_the_line_when_it_is_not_identical(self):
        d = Project.perry(self)
        recs = records(d)
        tid = a_live_row(d)
        next(r for r in recs if r["id"] == tid)["title"] = "moved"
        rewrite(d, recs)
        proc = run("diff", root=d)
        self.assertEqual(proc.returncode, 1)
        out = json.loads(proc.stdout)
        self.assertFalse(out["identical"])
        self.assertIn("moved", out["first_difference"]["rendered"])
        self.assertNotIn("moved", out["first_difference"]["file"])


if __name__ == "__main__":
    unittest.main()
