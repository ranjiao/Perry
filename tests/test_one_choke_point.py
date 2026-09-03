"""TASK-067 / `USER-915`: **nothing outside `viewer/tables.py` builds a row.**

The rule is on a *symbol*, not on a shape. `tests/test_row_integrity.py`
already carries the shape half — `HAND_ROW_RE` for `f"| {a} | {b} |"` and
`SPLIT_RE` for `.split("|")` — and its own docstring records why that half
cannot be finished:

    a row assembled with `" | ".join(cells)` is indistinguishable by grep from
    a regex alternation and from a separator row, both of which are correct
    and common here. A first version flagged all three and reported 14
    offenders of which 11 were fine.

So this module does not try to recognise a row-shaped string. It **enumerates
the surface**: every AST node in the tree that builds row text out of a `|`
literal without going through the choke point. That set is small, closed, and
listed below by name. `USER-904`, `USER-906` and `TASK-285` all chose this
move over a denylist; TASK-067 is the fourth time and the reason is the same
each time — a denylist over English (or over string shapes) loses review
rounds, and a rule over one enumerable surface does not.

The classifier is `TASK-323-bound.py`'s **W2**, reproduced here rather than
imported: the bound is an evidence file that documents a measurement taken on
one commit, and a guard that stops working when an evidence file is archived
is not a guard. It is kept in step by
`test_the_guard_agrees_with_the_census_rule` below.

## Declared limits — what this rule does NOT cover

Written here as well as in `viewer/tables.py`'s docstring, because these are
the two files a reader of the rule opens, and a backstop believed to work
where it is measured absent is worse than none.

1. **The read side is out of reach by construction.** This rule is about who
   *writes* a row. `.split("|", 6)` returns the right cell count with
   truncated content, so **no count-based check can ever cover the read
   side** — there is no count to disagree with.
2. **`ragged-row` is not this rule's backstop.** It is present for the write
   shapes w4-w7 and **absent** for the read shapes r2, r3, r4, r7, r8; and it
   **fires only inside a schema-recognised table.** TASK-323 round 1 confirmed
   with a control that the identical 8-cell row in an unrecognised section
   produces 0 errors, so a project filing work under its own headings via
   `perry-task add --group` has no net at all.
3. **`test_row_integrity.py`'s `SPLIT_RE` has four demonstrated blind spots**
   on the read half — `maxsplit`, `re.split`, a `SEP = "|"` constant, and
   `.rsplit`/`.partition`.
4. **`bin/perry-decide:332` is outside this rule** — it builds no row, so a
   rule about who builds rows does not reach it. It guards a line break with a
   third, weaker spelling (`len(_value.splitlines()) > 1`) that misses a
   trailing newline `viewer/tables.py § line_break_at` catches. Filed as its
   own row, not fixed here.
5. **`bin/perry-task:7431`** (`_v.strip() == exc.value`) is covered by neither
   this rule nor reading (A): message quality, not a corruption path.
"""
import ast
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent

#: The choke point itself. Exempt by name, and the ONLY name exempt.
CHOKE_POINT = "viewer/tables.py"

#: Row/cell writers that live in the choke point. A call to one of these is a
#: use of the choke point, wherever it appears.
WRITERS = {"render_row", "render_separator", "check_cell", "splice_cell",
           "append_cell", "append_separator_cell"}
SPLITTERS = {"split_row", "cell_spans"}

RE_FNS = {"compile", "match", "search", "sub", "subn", "fullmatch", "split",
          "findall", "finditer", "escape"}
DIAG = {"Finding", "Refused", "print"}

#: The two W2 nodes outside the choke point that are NOT rows, each opened and
#: named. A `(file, what)` pair rather than a line number, because line numbers
#: move — TASK-323 measured `perry-lint:887` and it is `:958` today, having
#: moved with no change to the code it names. **Anything not on this list is a
#: failure, including a new line in one of these two files.**
NOT_A_ROW = {
    ("bin/perry-lint", "` | `.join()"):
        "a finding MESSAGE — `\" | \".join(row)[:60]` truncated for the "
        "console. Never reaches a state file.",
    ("viewer/parsers.py", "`|`.join()"):
        "a regex ALTERNATION — `\"|\".join(...)` of alternatives, not cells.",
}


def _lit(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _excluded(node, stack):
    """E1 regex context · E2 fed to the splitter · E3 a diagnostic."""
    for anc in stack:
        if not isinstance(anc, ast.Call):
            continue
        f = anc.func
        if (isinstance(f, ast.Attribute) and f.attr in RE_FNS
                and isinstance(f.value, ast.Name) and f.value.id == "re"):
            return True
        if isinstance(f, ast.Name) and f.id in SPLITTERS:
            return True
        if isinstance(f, ast.Name) and f.id in DIAG:
            return True
    for sub in ast.walk(node):
        if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
                and sub.func.attr == "escape"
                and isinstance(sub.func.value, ast.Name)
                and sub.func.value.id == "re"):
            return True
    return False


class RowBuilders(ast.NodeVisitor):
    """W2: row text built from a literal containing `|` without a W1 call.

    Names resolve through `NAME = "..."` bindings, so a `SEP = "|"`
    indirection is found exactly as the inline literal is.
    """

    def __init__(self, src):
        self.hits = []
        self.stack = []
        self.consts = {}
        tree = ast.parse(src)
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign):
                v = _lit(n.value)
                if v is not None:
                    for t in n.targets:
                        if isinstance(t, ast.Name):
                            self.consts[t.id] = v
        self.visit(tree)

    def generic_visit(self, node):
        self.stack.append(node)
        super().generic_visit(node)
        self.stack.pop()

    def _add(self, node, what):
        if _excluded(node, reversed(self.stack)):
            return
        row = (node.lineno, what)
        if row not in self.hits:
            self.hits.append(row)

    def _strval(self, node):
        v = _lit(node)
        if v is not None:
            return v
        if isinstance(node, ast.Name):
            return self.consts.get(node.id)
        return None

    def visit_JoinedStr(self, node):
        parts = "".join(_lit(v) or "" for v in node.values
                        if isinstance(v, ast.Constant))
        if "|" in parts and any(isinstance(v, ast.FormattedValue)
                                for v in node.values):
            self._add(node, "f-string with a `|` literal part")
        self.generic_visit(node)

    def visit_BinOp(self, node):
        for side, other in ((node.left, node.right), (node.right, node.left)):
            s = self._strval(side)
            if s is None or "|" not in s:
                continue
            if isinstance(node.op, ast.Mod):
                self._add(node, "`%` onto a `|` literal")
                break
            if isinstance(node.op, ast.Add) and not isinstance(
                    other, ast.Constant):
                self._add(node, "`+`-concat onto a `|` literal")
                break
        self.generic_visit(node)

    def visit_Call(self, node):
        f = node.func
        if isinstance(f, ast.Name) and f.id in WRITERS:
            return          # a use of the choke point; do not descend
        if isinstance(f, ast.Attribute) and f.attr in WRITERS:
            return
        if isinstance(f, ast.Attribute):
            recv = self._strval(f.value)
            if f.attr in ("join", "format") and recv and "|" in recv:
                self._add(node, f"`{recv}`.{f.attr}()")
        self.generic_visit(node)


def _domain():
    """Every shipped Python source file, DISCOVERED, not listed.

    `tests/` is excluded — a fixture is not a write path — and so is the
    choke point itself. `rglob`, because `bin/lib/` exists and a guard that
    cannot see a subdirectory is a guard against the files that already had
    the bug.
    """
    out = []
    for d in ("bin", "viewer"):
        for p in sorted((PERRY_HOME / d).rglob("*")):
            if not p.is_file() or "__pycache__" in p.parts:
                continue
            rel = p.relative_to(PERRY_HOME).as_posix()
            if rel == CHOKE_POINT:
                continue
            if p.suffix == ".py":
                out.append(p)
                continue
            try:
                with p.open("rb") as fh:
                    first = fh.readline().decode("utf-8", "replace")
            except OSError:
                continue
            if first.startswith("#!") and "python" in first:
                out.append(p)
    return out


def offenders(paths=None):
    """`[(rel_path, line, what)]` for every row built outside the choke point,
    minus the two nodes named in `NOT_A_ROW`."""
    found = []
    for p in (paths if paths is not None else _domain()):
        rel = p.relative_to(PERRY_HOME).as_posix()
        try:
            src = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            hits = RowBuilders(src).hits
        except SyntaxError:
            continue
        for line, what in hits:
            if (rel, what) in NOT_A_ROW:
                continue
            found.append((rel, line, what))
    return found


class TestNothingOutsideTheChokePointBuildsARow(unittest.TestCase):

    def test_no_tool_builds_a_table_row_outside_viewer_tables(self):
        """**The rule.** One enumerable surface, discovered not listed.

        Before TASK-067 this failed with eight offenders, every one of them a
        SEPARATOR row: `perry-task` 985/1034/1112/5174, `perry-goals`
        327/328/3093, `perry_md_store.py` 774. The last of those sat between
        `perry_md_store.py:773` and `:775`, which are both `render_row` calls
        — a hand-built row between two choke-point calls, the whole shape on
        one screen.

        They agreed with their headers only by accident: each derived its
        count from the same list it handed `render_row`, and `render_row` was
        evaluated first, so a value it refused took the separator down with
        it. Routing them makes that an invariant instead of a coincidence,
        which is the entire content of reading (B).
        """
        found = offenders()
        self.assertEqual(
            found, [],
            "these build a table row without the choke point; use "
            "viewer/tables.py render_row (or render_separator / append_cell "
            "/ append_separator_cell, which route through it). If one of "
            "these is genuinely not a row, open it and add it to NOT_A_ROW "
            "with the reason.")

    def test_the_guard_fires_on_a_ninth_hand_built_row(self):
        """**The control that makes this a rule and not a cleanup.**

        A guard that is green because the eight sites were fixed is a guard
        against those eight sites. This plants a ninth builder — the
        `" | ".join(cells)` shape `test_row_integrity.py` says grep cannot
        tell from an alternation — and requires it to be seen.
        """
        probe = PERRY_HOME / "bin" / "perry-ninthrowprobe"
        probe.write_text(
            '#!/usr/bin/env python3\n'
            'def render(cells):\n'
            '    return "| " + " | ".join(cells) + " |"\n',
            encoding="utf-8")
        try:
            found = offenders([probe])
            self.assertTrue(
                found, "a ninth hand-built row walked past the guard")
            self.assertEqual([f[0] for f in found],
                             ["bin/perry-ninthrowprobe"] * len(found))
        finally:
            probe.unlink(missing_ok=True)

    def test_the_guard_fires_on_a_hand_built_separator_row(self):
        """The shape TASK-067 actually removed, planted back.

        All three spellings the eight sites used, because they produce
        identical bytes and a guard that sees one and not the others would
        have been green on five of the eight.
        """
        for spelling in ('"|" + "|".join(["---"] * n) + "|"',
                         '"|" + "|".join("---" for _ in cols) + "|"',
                         '"|" + "---|" * n'):
            with self.subTest(spelling=spelling):
                probe = PERRY_HOME / "bin" / "perry-sepprobe"
                probe.write_text(
                    f'#!/usr/bin/env python3\n'
                    f'def sep(n, cols):\n'
                    f'    return {spelling}\n', encoding="utf-8")
                try:
                    self.assertTrue(
                        offenders([probe]),
                        f"hand-built separator {spelling} walked past")
                finally:
                    probe.unlink(missing_ok=True)

    def test_the_guard_is_silent_on_legitimate_render_row_callers(self):
        """**The other control.** A guard that fires on the choke point, or on
        its callers, is useless — people delete it or exempt their way around
        it until it means nothing.

        Every real caller shape in the tree: the bare call, the call whose
        argument is itself built, and the separator/widen helpers.
        """
        probe = PERRY_HOME / "bin" / "perry-callerprobe"
        probe.write_text(
            '#!/usr/bin/env python3\n'
            'from tables import (render_row, render_separator, append_cell,\n'
            '                    append_separator_cell, split_row)\n'
            'def a(cells):\n'
            '    return render_row(cells)\n'
            'def b(n):\n'
            '    return render_separator(n)\n'
            'def c(line, v):\n'
            '    return append_cell(line, v)\n'
            'def d(line):\n'
            '    return append_separator_cell(line)\n'
            'def e(line, extra):\n'
            '    return render_row(split_row(line) + [extra])\n',
            encoding="utf-8")
        try:
            self.assertEqual(
                offenders([probe]), [],
                "the guard fires on a legitimate caller of the choke point")
        finally:
            probe.unlink(missing_ok=True)

    def test_the_guard_sees_a_file_in_a_subdirectory(self):
        """`bin/lib/` is real. A guard that only globs the top level is a
        guard against the files that already had the bug."""
        d = PERRY_HOME / "bin" / "lib"
        made = not d.exists()
        d.mkdir(exist_ok=True)
        probe = d / "rowprobe.py"
        probe.write_text('def r(cells):\n'
                         '    return "| " + " | ".join(cells) + " |"\n',
                         encoding="utf-8")
        try:
            self.assertIn("bin/lib/rowprobe.py",
                          [f[0] for f in offenders()],
                          "a row builder in a subdirectory is invisible")
        finally:
            probe.unlink(missing_ok=True)
            if made:
                d.rmdir()

    def test_the_guard_follows_a_separator_constant(self):
        """`SEP = "|"` then `SEP.join(...)`. The bound resolves names, and the
        read half's `SPLIT_RE` demonstrably does not — declared limit 3. The
        write half must not inherit that hole."""
        probe = PERRY_HOME / "bin" / "perry-constprobe"
        probe.write_text('#!/usr/bin/env python3\n'
                         'SEP = "|"\n'
                         'def r(cells):\n'
                         '    return SEP + SEP.join(cells) + SEP\n',
                         encoding="utf-8")
        try:
            self.assertTrue(offenders([probe]),
                            "a `SEP = \"|\"` indirection walked past")
        finally:
            probe.unlink(missing_ok=True)

    def test_the_two_exempt_nodes_still_exist_and_are_still_not_rows(self):
        """`NOT_A_ROW` is an allowlist, and an allowlist rots into a place
        people park things. Both entries must still be found by the classifier
        — if one stops matching, the exemption is dead and must be deleted
        rather than left as cover for a future real row in the same file.
        """
        for (rel, what) in NOT_A_ROW:
            with self.subTest(node=f"{rel} {what}"):
                p = PERRY_HOME / rel
                self.assertTrue(p.exists(), f"{rel} is gone; drop its entry")
                hits = RowBuilders(p.read_text(encoding="utf-8")).hits
                self.assertIn(what, [w for _, w in hits],
                              f"{rel} no longer contains {what}; the "
                              f"exemption is dead and should be deleted")

    def test_the_guard_agrees_with_the_census_rule(self):
        """The classifier is TASK-323's W2, reproduced. If the census script
        is still in the tree, the two must return the same W2 set outside the
        choke point — otherwise this module has drifted from the rule whose
        measurement it inherits.

        Skipped, not failed, when the evidence file is not present: an
        archived measurement must not be able to break the guard.
        """
        script = PERRY_HOME / "perry/evidence/2026-09/TASK-323-bound.py"
        if not script.exists():
            self.skipTest("census script not in the tree")
        import subprocess
        out = subprocess.run(
            ["python3", str(script), str(PERRY_HOME)],
            capture_output=True, text=True, cwd=str(PERRY_HOME)).stdout
        census = {line.split("\t")[1] for line in out.splitlines()
                  if line.startswith("W2\t")
                  and not line.split("\t")[1].startswith(CHOKE_POINT)}
        mine = {f"{rel}:{line}" for rel, line, _ in offenders()}
        mine |= {f"{PERRY_HOME.joinpath(rel).relative_to(PERRY_HOME)}:{n}"
                 for rel, what in NOT_A_ROW
                 for n, w in RowBuilders(
                     (PERRY_HOME / rel).read_text(encoding="utf-8")).hits
                 if w == what}
        self.assertEqual(
            census, mine,
            "this guard and the census rule disagree about which nodes "
            "outside the choke point build row text")


if __name__ == "__main__":
    unittest.main()
