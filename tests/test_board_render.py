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

COVERS = (
    "bin/perry-tasks",
    "viewer/tables.py",
    "tests/printed_board.py",
    "tests/live_stores.py",
    "perry/tasks.jsonl",
    "perry/asks.jsonl",
    "perry/risks.jsonl",
    "perry/intake.jsonl",
    "perry/linkage.jsonl",
    "perry/okr.jsonl",
    ".perry/config.jsonl",
)

import json
import pathlib
import re
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin" / "perry-tasks"

sys.path.insert(0, str(ROOT / "viewer"))
import parsers as P                                             # noqa: E402
import tables as T                                              # noqa: E402

import inproc                                                   # noqa: E402
from printed_board import put_printed_board                     # noqa: E402
import live_stores  # noqa: E402

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
| **USER-G1** | **P0** Gate 1 RM 问询（kr:P001-O2-KR1）| User | not_started | 发 draft v2 |
| ~~**ALLOC-01**~~ | ✅ 部分解 —— IPS-01 一直存在 | Coding Agent | **迁移 done，占比目标 not_started** | 归档 |
| DUOL-TRIGGER1 | 表格引用 `\\| ID \\| Risk \\|` 在正文里 | User | in_progress | 复核 |

## P2 (低优先 carry)

| ID | Title | Owner | Status | Next action |
|---|---|---|---|---|
| 2 待核项 | 不是 handle，是散文 | — | — | — |
| TEMPLATES-3 | 研究模板三件套 | User+Agent | not_started | agent 起草 |
"""


def run(*args, root=ROOT):
    # **In-process** (TASK-368). Measured in this tree before converting: 158
    # `perry-tasks` calls, and the boundary is 97.7% of one against a fixture.
    # The MODULE number is lower because four of its tests render Perry's own
    # board, which is real work rather than startup — three probes gave 46.5%,
    # 41.3% and 51.8%, median 46.5%, which clears the 40% gate but is nowhere
    # near the 97.7% a single call suggests. `perry-tasks`' two module globals
    # (`_TASK_MODULE`, `_LINT_MODULE`) are sibling-module handles.
    return inproc.run("perry-tasks", [*args, "--root", str(root)],
                      cwd=str(ROOT))


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
    text = inproc.run("perry-tasks", ["render", "--root", str(root)]).stdout
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
        # USER-942: the stores and the anchor, not the whole state root.
        # `render`, `diff` and `verify` read the stores, the config and the
        # template; `evidence/`, `journal/` and `design/` were carried along by
        # `copytree` and read by nothing here (`tests/live_stores.py`).
        live_stores.copy_state(d, events=False)
        # TASK-237 3c: this repository holds no `BOARD.md`. The board a
        # project that still holds one would carry is the one its stores
        # print, so the copy gets that (`tests/printed_board.py`).
        put_printed_board(d / "perry")
        assert run("write", "--from-board", root=d).returncode == 0
        return d

    @staticmethod
    def fixture(case, board: str) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp())
        case.addCleanup(shutil.rmtree, d, ignore_errors=True)
        # Installed the way a start installs a project (TASK-237 round 2): the
        # import below writes `tasks.jsonl`, which refuses where nothing is.
        import config_store
        config_store.write_config(d)
        (d / "BOARD.md").write_text(board, encoding="utf-8")
        assert run("write", "--from-board", root=d).returncode == 0
        return d


class TestTheBytesMatch(unittest.TestCase):
    def board_bytes(self, root: pathlib.Path) -> bytes:
        p = root / "BOARD.md"
        return (p if p.exists() else root / "perry" / "BOARD.md").read_bytes()

    def rendered(self, root: pathlib.Path) -> bytes:
        # This call site asked for BYTES — `capture_output` without
        # `text=True` — and `board_bytes` above compares against
        # `read_bytes()`. `inproc.run` always decodes, so the encode here is
        # what keeps the comparison a byte comparison rather than quietly
        # making it a str one. TASK-368.
        proc = inproc.run("perry-tasks", ["render", "--root", str(root)])
        self.assertEqual(proc.returncode, 0, proc.stderr[:500])
        return proc.stdout.encode("utf-8")

    def test_perrys_own_board(self):
        """Perry's board, byte for byte — and with NO verbatim fallback.

        Since TASK-237 3c the board is the one `perry-tasks board` prints from
        this repository's stores, put on disk in a copy; it was the hand-kept
        file before.

        `identical: true` alone would also be true of a renderer that copied
        every row, so the two counters are asserted beside it."""
        d = Project.perry(self)
        self.assertEqual(self.rendered(d), self.board_bytes(d))
        out = json.loads(run("diff", root=d).stdout)
        self.assertTrue(out["identical"])
        self.assertEqual(out["rows_verbatim"], [])
        self.assertEqual(out["cells_verbatim"], {})
        # Closing a task removes one projected row, so a fixed live-row count
        # makes project progress break this test. The zero-fallback assertions
        # above and the field-mutation tests below prove store ownership; here
        # we only need to show that the live board exercised that path.
        self.assertGreater(out["rows_from_store"], 0)

    def test_a_board_shaped_like_the_second_real_project(self):
        d = Project.fixture(self, SECOND_PROJECT_BOARD)
        self.assertEqual(self.rendered(d), self.board_bytes(d))
        out = json.loads(run("diff", root=d).stdout)
        self.assertTrue(out["identical"], json.dumps(out, ensure_ascii=False))
        self.assertEqual(out["rows_from_store"], 4)

    def test_the_shapes_that_a_re_rendered_row_would_lose(self):
        """Each one on its own line, so a failure names which shape broke.

        Every one of these is a byte a `render_row` round trip moves: it pads
        `（kr:P001-O2-KR1）|` to `（kr:P001-O2-KR1） |`, and `strip_handle` has already
        thrown the `~~**` away before the store sees the id."""
        d = Project.fixture(self, SECOND_PROJECT_BOARD)
        got = self.rendered(d).decode()
        for shape in ("| ~~**ALLOC-01**~~ |",
                      "（kr:P001-O2-KR1）| User |",
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
        return inproc.run("perry-tasks",
                          ["render", "--root", str(root)]).stdout


    def row_of(self, root: pathlib.Path, tid: str) -> str:
        """The one rendered line for `tid`. **Not the whole file.**

        `assertIn(mark, whole_board)` passes on any board that happens to
        contain the word somewhere else — `dropped` is in four other rows'
        prose — which would grade the wrong thing every time."""
        got = [l for l in self.rendered(root).split("\n")
               if l.startswith(f"| {tid} ")]
        self.assertEqual(len(got), 1, f"{tid}: {len(got)} rendered rows")
        return got[0]

    def cell_of(self, root: pathlib.Path, tid: str, column: str) -> str:
        """The one rendered CELL for `tid`'s `column`. **Not the whole row.**

        TASK-356. Narrowing from the whole board to the whole row was the
        previous fix and it was not narrow enough: a row carries this
        project's own English in `Title`, `Summary` and `Next action` BY
        DESIGN, so a sentinel that is an ordinary word collides with the
        row's own prose. It went red on `dropped` when a task's
        `next_action` came to read "unescaped pipes that silently dropped
        six call sites" — the row's free text, not the renderer, moving.
        And that is not a `status` accident: the census recorded in
        `test_a_row_whose_prose_carries_every_sentinel_still_passes` below
        finds the SAME trap already loaded on `owner`/`Nobody`, one board
        row away from firing, and shows all seven fields failing under the
        old rule. Scoped to the cell, a field can only ever collide with its
        OWN sentinel — and that residual case is what the round trip's
        `assertNotEqual(was, want)` guard is for.

        The column is resolved BY NAME through the schema glossary, the way
        `viewer/parsers.py § _parse_task_table` resolves it — not by a fixed
        index — because column ORDER is the thing that file spends its
        longest comment explaining is not constrained by the schema. Read
        through `split_row` and `header_index`, the repository's only row
        splitter and only header fold, so this locator cannot disagree with
        the reader it is grading.
        """
        lines = self.rendered(root).split("\n")
        at = [i for i, l in enumerate(lines) if l.startswith(f"| {tid} ")]
        self.assertEqual(len(at), 1, f"{tid}: {len(at)} rendered rows")
        i = at[0]
        j = i
        while j > 0 and not re.match(r"^\|\s*---", lines[j]):
            j -= 1
        self.assertGreater(j, 0, f"{tid}: no header separator above the row")
        header = T.header_index(T.split_row(lines[j - 1]))
        col = header.column(P._column_keys(column))
        self.assertNotEqual(col, -1, f"{tid}: no {column!r} column in {header}")
        cells = T.split_row(lines[i])
        return cells[col] if col < len(cells) else ""

    #: Store field -> the board column it renders into. Spelled once, and
    #: used by both round trips below, so a field cannot be graded against
    #: one column in one test and against another column in the next.
    FIELD_COLUMN = {"title": "Title", "owner": "Owner",
                    "next_action": "Next action", "evidence": "Evidence",
                    "verification": "Verification", "status": "Status",
                    "depends_on": "Depends on"}

    #: The value written into each field on disk, and looked for in its cell.
    MARKS = {"title": "A TITLE NOTHING WROTE", "owner": "Nobody",
             "next_action": "AN ACTION NOTHING WROTE",
             "evidence": "evidence/nothing.md", "verification": "V6",
             "status": "dropped", "depends_on": ["TASK-001", "TASK-002"]}

    @staticmethod
    def _want(mark) -> str:
        return ", ".join(mark) if isinstance(mark, list) else mark

    def test_every_rendered_field_moves_when_the_store_moves(self):
        """Set the field on disk, read its CELL; restore it, read it again.

        Both halves are equalities against the cell, and the restore half
        compares to the cell as it rendered BEFORE the mutation rather than
        asserting the sentinel is absent. That is what keeps the property
        from being re-broken by its own sentinel: `dropped` is a real
        `status` value, so a row legitimately in that state would fail an
        `assertNotIn` for reasons that have nothing to do with the renderer.
        Equality also grades strictly more than absence did — a renderer
        that dropped the cell to `—` on restore satisfied `assertNotIn` and
        fails this.

        `assertNotEqual(was, want)` is the guard that keeps the round trip
        from being vacuous: if a field's stored value already equalled its
        sentinel, both halves would pass without the renderer being asked
        anything, and the subtest would be decoration. It is not theoretical:
        `USER-916` renders `status: dropped` on the live board today, so the
        `status` sentinel IS a value this project's rows take.

        **What the restore half is worth, measured.** TASK-356 stripped the
        SET half out and ran the restore half alone against a renderer with
        `status` removed from `FIELD_BY_COLUMN`, and it came back GREEN — no
        independent power against that mutant, or against the other five
        planted with it. The reason is structural and worth writing down so
        the next round does not re-derive it: `BOARD.md` is a static
        template here — only `tasks.jsonl` is rewritten — so the only stale
        value a renderer can hold IS the board's original text, and the SET
        half already fails on it one line earlier. The restore half bites
        only a renderer that persists its own output back into the template,
        which `test_render_and_diff_write_no_file` separately forbids.

        It stays anyway, and not out of caution: it is the only assertion
        that says the cell tracks the store in BOTH directions, it costs one
        render, and dropping it would leave a test that has never once been
        shown to notice a value going the wrong way.
        """
        d = Project.perry(self)
        tid = a_live_row(d)
        for field, mark in self.MARKS.items():
            with self.subTest(field=field):
                column = self.FIELD_COLUMN[field]
                want = self._want(mark)
                was = self.cell_of(d, tid, column)
                self.assertNotEqual(
                    was, want,
                    f"{field}: the sentinel is already the rendered value, so "
                    f"this round trip would pass without rendering anything")

                recs = records(d)
                row = next(r for r in recs if r["id"] == tid)
                before = row[field]
                row[field] = mark
                rewrite(d, recs)
                self.assertEqual(self.cell_of(d, tid, column), want,
                                 f"{field} did not reach the board")

                row[field] = before
                rewrite(d, recs)
                self.assertEqual(
                    self.cell_of(d, tid, column), was,
                    f"{field} did not move back when the store did — the "
                    f"renderer is not reading this cell from the store")

    def test_a_row_whose_prose_carries_every_sentinel_still_passes(self):
        """**The regression this row exists to prevent.** TASK-356.

        The old rule asserted the sentinel appeared NOWHERE in the rendered
        row, and this project writes English into `title` and `next_action`
        by design, so a row's own free text could defeat it. It did: a task
        whose `next_action` read "unescaped pipes that silently dropped six
        call sites" made the `status` sentinel `dropped` unfindable-absent,
        and the only red on `main` was the board's prose, not the renderer.

        That was never a `status` accident. Here EVERY sentinel is planted in
        the row's own `title` and `next_action` at once — the worst board
        this project could legitimately write — and all seven round trips
        still have to pass. Under the whole-row rule all seven fail; the
        census below records that this is not hypothetical for two of them.

        **The live-board census, measured on 145 rendered rows:** seven
        fields, seven sentinels. Two are ordinary English words that the
        board's prose already contains — `dropped` (`status`) in 7 rows and
        `Nobody` (`owner`) in 1, every occurrence in `Title` or `Next
        action`, i.e. a column neither of them grades. A third, `V6`
        (`verification`), is a token this project writes into prose as a
        matter of routine ("closes at V4") and collides the day a V6 exists.
        The remaining four — `A TITLE NOTHING WROTE`, `AN ACTION NOTHING
        WROTE`, `evidence/nothing.md`, `TASK-001, TASK-002` — are shaped so
        prose would not produce them.

        The census is asserted here as a CONSTRUCTION and not as a scan of
        today's board, because a scan would make this test fail whenever the
        project's own text changed — which is the whole defect being fixed,
        re-introduced one level up. `USER-916` currently renders `status:
        dropped`, so even "no row holds this sentinel in this column" is a
        sentence project state can break; the per-field `assertNotEqual`
        guard in the round trip above is where that case is caught, on the
        one row actually under test.
        """
        d = Project.perry(self)
        tid = a_live_row(d)
        every = " ".join(self._want(m) for m in self.MARKS.values())

        recs = records(d)
        row = next(r for r in recs if r["id"] == tid)
        row["title"] = f"Prose citing {every} in a title"
        row["next_action"] = f"Free text quoting every sentinel: {every}"
        rewrite(d, recs)
        planted = self.row_of(d, tid)
        for field, mark in self.MARKS.items():
            self.assertIn(self._want(mark), planted,
                          f"{field}'s sentinel was not planted in the row")

        for field, mark in self.MARKS.items():
            with self.subTest(field=field):
                column = self.FIELD_COLUMN[field]
                want = self._want(mark)
                recs = records(d)
                row = next(r for r in recs if r["id"] == tid)
                was = self.cell_of(d, tid, column)
                self.assertNotEqual(was, want, f"{field}: vacuous round trip")
                before = row[field]
                row[field] = mark
                rewrite(d, recs)
                self.assertEqual(self.cell_of(d, tid, column), want,
                                 f"{field} did not reach the board")
                row[field] = before
                rewrite(d, recs)
                self.assertEqual(
                    self.cell_of(d, tid, column), was,
                    f"{field} did not move back when the store did")

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

    def test_a_declared_blank_marker_is_layout_not_verbatim_data(self):
        """`[]` projects through the schema's authored empty-cell marker.

        The marker is not an escape hatch: once the store carries a dependency,
        the rendered cell must move with it and the report must name the drift.
        """
        board = """# Board

## P1

| ID | Title | Owner | Status | Depends on |
|---|---|---|---|---|
| TASK-001 | First | User | blocked | — |
"""
        d = Project.fixture(self, board)
        out = json.loads(run("diff", root=d).stdout)
        self.assertTrue(out["identical"])
        self.assertEqual(out["cells_verbatim"], {})

        recs = records(d)
        recs[0]["depends_on"] = ["TASK-002"]
        rewrite(d, recs)
        self.assertIn("| TASK-002 |", self.rendered(d))
        out = json.loads(run("diff", root=d).stdout)
        self.assertEqual(
            [(c["id"], c["column"], c["board"], c["store"])
             for c in out["cells_the_store_and_board_disagree_on"]],
            [("TASK-001", "Depends on", "—", "TASK-002")])

    def test_a_store_row_no_line_holds_is_reported(self):
        d = Project.fixture(self, SECOND_PROJECT_BOARD)
        recs = records(d)
        ghost = dict(recs[0])
        ghost["id"] = "GHOST-001"
        rewrite(d, recs + [ghost])
        out = json.loads(run("diff", root=d).stdout)
        self.assertIn("GHOST-001", out["rows_not_on_board"])

    def test_missing_projection_excludes_terminal_and_deduplicates_tables(self):
        board = """# Board

## Open

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-001 | First | User | not_started | — | — |

## Open

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-002 | Second | User | in_progress | — | — |
"""
        d = Project.fixture(self, board)
        recs = records(d)
        active = dict(recs[0], id="GHOST-001", title="Missing",
                      status="in_progress", order=2)
        terminal = dict(recs[0], id="DONE-001", title="Closed",
                        status="done", order=3)
        rewrite(d, [*recs, active, terminal])

        out = json.loads(run("diff", root=d).stdout)
        self.assertTrue(out["identical"])
        self.assertEqual(out["rows_not_on_board"], ["GHOST-001"])


class TestItRendersAndNothingElse(unittest.TestCase):
    def test_rendering_without_a_store_is_not_a_pass(self):
        """Exit 2 and nothing on stdout — the same answer `verify` gives.

        Building the store from the board and rendering it back would compare
        `split_row` with `render_row` and call it a proof."""
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        live_stores.copy_state(d, skip=("tasks.jsonl",), events=False)
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
