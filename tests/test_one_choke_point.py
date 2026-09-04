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
6. **Nothing outside Python is in the domain.** A row built by a shell script
   or a template expansion is invisible to an AST walk, and no member of the
   census's 88 is one. Not measured, and stated so rather than left implied.
7. **Dot-directories are not walked** — `.git`, and `.claude/worktrees/`,
   which on the main checkout holds one full clone of this repository per live
   agent. `.github/` therefore has no net; it holds no Python today.
8. **A value computed at run time is out of reach.** `chr(124)` and
   `"@".replace("@", "|")` are silent. An AST literal walk cannot do better,
   and both are obfuscation rather than idiom — unlike the five `SEP`
   spellings round 5 found silent, which are now covered.

## What round 6 changed, and why the docstrings above are worth re-measuring

Round 5 FAILed this module on the gap between what it *claimed* and what it
*enforced*, in three independent directions — and the spec's own warning is
that prose written into a deliverable becomes what the next round relies on
instead of re-measuring. So, concretely: `_domain()` said DISCOVERED and read
`for d in ("bin", "viewer")`, leaving a tracked hand-built builder in
`packs/` completely silent; `TestTheChokePointsOwnInterior` closed two named
functions and left the category open; and
`test_the_guard_follows_a_separator_constant` asserted the `SEP` hole was
closed while five ordinary spellings walked through it. All three are fixed
here **and each fix has a control test beside it**, because the failure mode
was never a missing fix — it was a claim nobody re-measured.
"""
import ast
import contextlib
import os
import tempfile
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

#: **The choke point's own interior, enumerated.** The rule above exempts
#: `viewer/tables.py` by name — it must, or the choke point would flag itself
#: — so nothing above can see inside it. Round 5's F3: appending
#:
#:     def render_header(cells):
#:         return "| " + " | ".join(str(c) for c in cells) + " |"
#:
#: to the choke point left all thirteen tests green. Two mutations to this
#: module's interior had already come back GREEN in round 4, and the round-4
#: answer was two behavioural tests of two named functions — which closes two
#: instances and leaves the category open. Review rule 1 is *enumerate the
#: category, do not find the next instance*.
#:
#: So this is `NOT_A_ROW`'s construction turned inward: every `|`-literal
#: row-building node inside the choke point must be one of a named few. The
#: key is `(function, what)` and **not** a line number, for the reason
#: `NOT_A_ROW` states — line numbers move on their own. A new function is a
#: new key and fails; a new *shape* in an existing function is a new key and
#: fails.
#:
#: **Declared limit of this construction**: a second node of an
#: already-named shape inside an already-named function is covered by the
#: existing entry — `append_separator_cell` has two `+`-concat nodes under one
#: key today. Keying per line would catch that and would rot on the first
#: edit above it, which is the trade `NOT_A_ROW` already made deliberately.
CHOKE_POINT_INTERIOR = {
    ("render_row", "`+`-concat onto a `|` literal"):
        "the choke point itself — the one place a row is allowed to be built.",
    ("render_row", "` | `.join()"):
        "the same expression's join half.",
    ("render_separator", "`+`-concat onto a `|` literal"):
        "assembles the separator from `render_row`'s OWN output — the count "
        "comes from `split_row(render_row(...))`, never from `n` a second "
        "time. This is what routing the eight sites bought.",
    ("append_cell", "f-string with a `|` literal part"):
        "splices one cell into an existing line without re-rendering the "
        "rest of it; byte preservation is the module's whole argument.",
    ("append_separator_cell", "`+`-concat onto a `|` literal"):
        "widens a separator in the file's own dashes-and-colons style, and "
        "asserts the widened row gained exactly one cell.",
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
    indirection is found exactly as the inline literal is — **in every shape,
    not only in the two that happened to be tested.** Round 5's F2 found the
    resolution wired into `visit_BinOp`'s operands and `visit_Call`'s receiver
    and nowhere else, so `SEP + SEP.join(c) + SEP` fired while five ordinary
    spellings walked straight through:

        f"{SEP}{body}{SEP}"              f"{SEP} {a} {SEP} {b} {SEP}"
        f"{SEP}" + f"---{SEP}" * n       L = "| "; R = " |"; f"{L}{a}{R}"
        "%s %s %s" % (SEP, a, SEP)

    None of those is obfuscation; `f"{SEP} {a} {SEP}"` is how a person writes
    a row. The classifier handled f-strings and `%` correctly when the pipe
    was a literal and handled the constant correctly under `+` and `.join`;
    it was the *combination* that was uncovered. So resolution now happens in
    one place per shape: `_fstring_text` for interpolations and
    `_mod_operand_has_pipe` for `%` arguments, both going through `_strval`.

    `chr(124)` and `"@".replace("@", "|")` remain silent and are **not**
    counted as holes: an AST literal walk cannot be asked to catch a value
    computed at run time, and both are obfuscation rather than idiom.

    `self.scoped` carries the same hits keyed by enclosing function, which is
    what `interior_offenders` uses to hold the choke point's own interior to
    a named few.
    """

    def __init__(self, src):
        self.hits = []
        self.scoped = []
        self.stack = []
        self.funcs = []
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

    def visit_FunctionDef(self, node):
        self.funcs.append(node.name)
        self.generic_visit(node)
        self.funcs.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def _add(self, node, what):
        if _excluded(node, reversed(self.stack)):
            return
        row = (node.lineno, what)
        if row not in self.hits:
            self.hits.append(row)
            self.scoped.append(
                (self.funcs[-1] if self.funcs else "<module>",) + row)

    def _strval(self, node):
        v = _lit(node)
        if v is not None:
            return v
        if isinstance(node, ast.Name):
            return self.consts.get(node.id)
        return None

    def _fstring_text(self, node):
        """An f-string's constant parts **and its resolvable interpolations**.

        `f"{SEP}{body}{SEP}"` has no constant part at all: reading only the
        constants sees an empty string and calls it clean. Reading the
        interpolations through `_strval` sees `"||"`.
        """
        out = []
        for v in node.values:
            if isinstance(v, ast.Constant):
                out.append(_lit(v) or "")
            elif isinstance(v, ast.FormattedValue):
                out.append(self._strval(v.value) or "")
        return "".join(out)

    def visit_JoinedStr(self, node):
        if "|" in self._fstring_text(node) and any(
                isinstance(v, ast.FormattedValue) for v in node.values):
            self._add(node, "f-string with a `|` literal part")
        self.generic_visit(node)

    def _mod_operand_has_pipe(self, node):
        """A `%` right-hand side: the value itself, or any tuple element.

        `"%s %s %s" % (SEP, a, SEP)` puts the pipe in the *arguments*, not in
        the format string, so checking only the BinOp's two sides sees a
        format string with no `|` and stops.
        """
        s = self._strval(node)
        if s is not None and "|" in s:
            return True
        if isinstance(node, ast.Tuple):
            return any(self._strval(e) is not None and "|" in self._strval(e)
                       for e in node.elts)
        return False

    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Mod) and self._mod_operand_has_pipe(
                node.right):
            self._add(node, "`%` onto a `|` literal")
            self.generic_visit(node)
            return
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


#: Directory names never walked. An **exclusion** list, not an inclusion list,
#: and the difference is the whole of round 5's F1: a directory nobody has
#: created yet is in the domain the day it appears, instead of out of it until
#: somebody remembers to add it.
#:
#: - `__pycache__` — build output.
#: - dot-directories — `.git`, and `.claude/worktrees/`, which on the main
#:   checkout holds a full clone of this repository per live agent. Walking
#:   those would scan other agents' trees and report their probe files as this
#:   tree's offenders.
SKIP_DIRS = {"__pycache__"}

#: Excluded at the top level only, exactly as the census excludes `tests/`:
#: a fixture is not a write path. Scoped to the root so that a `tests`
#: directory *inside* a shipped package would still be walked.
SKIP_TOP = {"tests"}


def _domain(root=None):
    """Every shipped Python source file in the repository, DISCOVERED.

    **`root` defaults to `PERRY_HOME` and is a parameter for one reason
    (TASK-341): so that a probe can be planted into a scratch tree and walked
    by THIS code rather than written into the live checkout.** The walk is
    identical either way — it is the same function, not a re-implementation —
    which is what makes a scratch-tree plant a real measurement of the walk
    and not a mock of it. `work/reference/review-constraints.md`:

        Plant into a copy. Learned by planting into the live tree while five
        other rounds and a full-suite gate were running against it, and
        watching a correct guard report a defect that did not exist.

    Every caller that is asserting about the *repository* still passes no
    root and gets `PERRY_HOME`.

    **The whole tree**, which is the domain `TASK-323-bound.py` measures with
    `git ls-files`. Round 5 found this function scanning `for d in ("bin",
    "viewer")` under a docstring that claimed discovery, and measured what the
    two-directory version cost: a *tracked* `" | ".join` row builder placed in
    `packs/software-ops/` left **the rule itself green**. The only test that
    noticed was `test_the_guard_agrees_with_the_census_rule`, which reports a
    guard/census disagreement rather than a hand-built row — and which skips
    itself by design when the evidence file is archived, so archiving it made
    a hand-built builder in the tree completely silent.

    It also measured what the wider domain adds: **zero** findings. The
    property was available for free and was not taken.

    Discovery is a **walk, not `git ls-files`**, and that is deliberate rather
    than incidental. The census script shells out to git, so in a `git
    archive` copy — which is how this project's reviewers do all destructive
    work — it returns nothing. A domain that silently becomes empty is a guard
    that silently passes, which is the failure mode this function just had.
    A walk cannot be put into that state.

    `test_the_guard_domain_is_the_censuss_domain` asserts the two agree.
    """
    home = Path(root) if root is not None else PERRY_HOME
    out = []
    for root, dirs, files in os.walk(home):
        rel_root = Path(root).relative_to(home).as_posix()
        dirs[:] = sorted(d for d in dirs
                         if d not in SKIP_DIRS and not d.startswith(".")
                         and not (rel_root == "." and d in SKIP_TOP))
        for name in sorted(files):
            p = Path(root) / name
            rel = p.relative_to(home).as_posix()
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


def offenders(paths=None, root=None):
    """`[(rel_path, line, what)]` for every row built outside the choke point,
    minus the two nodes named in `NOT_A_ROW`.

    `root` is the tree the reported paths are relative to, and the tree walked
    when `paths` is omitted. It defaults to `PERRY_HOME`; see `_domain`.
    """
    home = Path(root) if root is not None else PERRY_HOME
    found = []
    for p in (paths if paths is not None else _domain(home)):
        rel = p.relative_to(home).as_posix()
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


def shipped_dirs(home=None):
    """The shipped top-level directory names, DISCOVERED — never listed.

    The same exclusion the walk applies, asked of the same tree, so a
    directory created tomorrow is in this answer the day it appears. That
    discovery is round 5's F1 and it is preserved exactly; what TASK-341
    changed is only *where the probes go*, never how the set is found.
    """
    home = Path(home) if home is not None else PERRY_HOME
    return sorted(d.name for d in home.iterdir()
                  if d.is_dir() and not d.name.startswith(".")
                  and d.name not in SKIP_DIRS and d.name not in SKIP_TOP)


@contextlib.contextmanager
def scratch_tree(dirs=()):
    """A real on-disk tree, outside the repository, for probes to be planted
    into.

    **TASK-341.** Five tests in this module used to write their probes into
    the live checkout — `bin/perry-ninthrowprobe`, `bin/perry-sepprobe`,
    `bin/perry-callerprobe`, `bin/lib/rowprobe.py`, and a `perry_f1probe.py`
    in the repository root and in every shipped directory. Each write is
    visible to every other process reading this tree, and
    `tests/test_one_primitive.py:150` asserts that `bin/lib` holds exactly
    one file, so under `tests/parallel` the two collided and reddened the
    module that had nothing wrong with it. Measured: aligning the two
    schedules reddened `test_bin_lib_is_the_only_exemption` on the first run.

    The probes are still **real files in a real directory tree, walked by the
    real `_domain()`** — a scratch root is a tree, not a mock. What changes is
    that no other process can see it. `tests/test_tree_guard.py` reached the
    same construction for the same reason and says so in its docstring; so
    does `work/reference/review-constraints.md`; so, already, did
    `test_a_new_row_builder_in_the_choke_point_is_caught` in this very file
    and `test_the_patterns_fire_on_a_rebuild_that_renames_the_function` in
    `test_one_primitive.py`. This module was the last holdout.
    """
    with tempfile.TemporaryDirectory(prefix="perry-chokeprobe-") as d:
        root = Path(d)
        for name in dirs:
            (root / name).mkdir(parents=True, exist_ok=True)
        yield root


def interior_offenders(src=None):
    """`[(function, line, what)]` inside the choke point that no
    `CHOKE_POINT_INTERIOR` entry names."""
    if src is None:
        src = (PERRY_HOME / CHOKE_POINT).read_text(encoding="utf-8")
    return [(fn, line, what) for fn, line, what in RowBuilders(src).scoped
            if (fn, what) not in CHOKE_POINT_INTERIOR]


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
        with scratch_tree(["bin"]) as root:
            probe = root / "bin" / "perry-ninthrowprobe"
            probe.write_text(
                '#!/usr/bin/env python3\n'
                'def render(cells):\n'
                '    return "| " + " | ".join(cells) + " |"\n',
                encoding="utf-8")
            found = offenders([probe], root=root)
        self.assertTrue(
            found, "a ninth hand-built row walked past the guard")
        self.assertEqual([f[0] for f in found],
                         ["bin/perry-ninthrowprobe"] * len(found))

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
                with scratch_tree(["bin"]) as root:
                    probe = root / "bin" / "perry-sepprobe"
                    probe.write_text(
                        f'#!/usr/bin/env python3\n'
                        f'def sep(n, cols):\n'
                        f'    return {spelling}\n', encoding="utf-8")
                    found = offenders([probe], root=root)
                self.assertTrue(
                    found, f"hand-built separator {spelling} walked past")

    def test_the_guard_is_silent_on_legitimate_render_row_callers(self):
        """**The other control.** A guard that fires on the choke point, or on
        its callers, is useless — people delete it or exempt their way around
        it until it means nothing.

        Every real caller shape in the tree: the bare call, the call whose
        argument is itself built, and the separator/widen helpers.
        """
        with scratch_tree(["bin"]) as root:
            probe = root / "bin" / "perry-callerprobe"
            probe.write_text(
                '#!/usr/bin/env python3\n'
                'from tables import (render_row, render_separator, '
                'append_cell,\n'
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
            found = offenders([probe], root=root)
        self.assertEqual(
            found, [],
            "the guard fires on a legitimate caller of the choke point")

    def test_the_guard_sees_a_file_in_a_subdirectory(self):
        """`bin/lib/` is real. A guard that only globs the top level is a
        guard against the files that already had the bug.

        **The probe goes into a scratch tree, and the walk is the real one**
        — `offenders()` with no `paths`, so `_domain()` does the descending,
        exactly as before. TASK-341: this test used to create a real
        `bin/lib/rowprobe.py` in the live checkout, and
        `tests/test_one_primitive.py:150` asserts `bin/lib` holds exactly one
        file. Two modules under `tests/parallel`, one of them red for a
        reason that had nothing to do with what it tests.

        The half that a scratch tree cannot carry — that the LIVE `bin/lib`
        is inside the real domain, so the descent has something to descend
        into — is asserted below it, as a read.
        """
        with scratch_tree(["bin/lib"]) as root:
            (root / "bin" / "lib" / "rowprobe.py").write_text(
                'def r(cells):\n'
                '    return "| " + " | ".join(cells) + " |"\n',
                encoding="utf-8")
            found = [f[0] for f in offenders(root=root)]
        self.assertIn("bin/lib/rowprobe.py", found,
                      "a row builder in a subdirectory is invisible")

    def test_the_live_bin_lib_is_inside_the_real_domain(self):
        """The read half of the test above: the subdirectory whose descent is
        being proved is a real, populated subdirectory of THIS tree, and the
        real `_domain()` reaches into it.

        Costs no write. Without it, the scratch-tree test above would prove
        the walk descends into a directory named `bin/lib` while `_domain()`
        quietly stopped reaching the one that exists.
        """
        live = {p.relative_to(PERRY_HOME).as_posix() for p in _domain()}
        self.assertIn("bin/lib/__init__.py", live,
                      "the real bin/lib is not in the guard's domain")

    def test_the_guard_follows_a_separator_constant(self):
        """`SEP = "|"` in **every shape**, not just the two that were tested.

        The bound resolves names and the read half's `SPLIT_RE` demonstrably
        does not — declared limit 3 — so the write half must not inherit that
        hole. Round 5's F2 found it half-inherited: resolution ran in
        `visit_BinOp`'s operands and `visit_Call`'s receiver only, so the two
        spellings below marked `[r5]` fired and the five below them, none of
        them obfuscated, were silent under a test asserting the opposite.

        These are parsed as source rather than written to disk because the
        point is the classifier, not the walk.
        """
        for name, src in (
                ("[r5] SEP + SEP.join(c) + SEP",
                 'SEP = "|"\ndef r(c):\n    return SEP + SEP.join(c) + SEP\n'),
                ("[r5] f-string around a resolved join",
                 'SEP = "|"\ndef r(c):\n'
                 '    return f"{SEP}{SEP.join(c)}{SEP}"\n'),
                ("f-string, constant has no pipe at all",
                 'SEP = "|"\ndef r(body):\n    return f"{SEP}{body}{SEP}"\n'),
                ("f-string, a whole row of resolved pipes",
                 'SEP = "|"\ndef r(a, b):\n'
                 '    return f"{SEP} {a} {SEP} {b} {SEP}"\n'),
                ("f-string separator built by repetition",
                 'SEP = "|"\ndef r(n):\n'
                 '    return f"{SEP}" + f"---{SEP}" * n\n'),
                ("two constants, one for each end",
                 'L = "| "\nR = " |"\ndef r(a):\n    return f"{L}{a}{R}"\n'),
                ("`%` with the pipe in the ARGUMENTS",
                 'SEP = "|"\ndef r(a):\n'
                 '    return "%s %s %s" % (SEP, a, SEP)\n')):
            with self.subTest(shape=name):
                self.assertTrue(
                    RowBuilders(src).hits,
                    f"a `SEP = \"|\"` indirection walked past: {name}")

    def test_a_resolved_constant_does_not_make_the_guard_cry_wolf(self):
        """**The control for the test above.** Resolving names into f-strings
        and `%` arguments widens what the classifier reaches, and a widened
        classifier that flags regex alternations or `render_row` callers gets
        exempted around until it means nothing — the exact failure
        `test_row_integrity.py`'s docstring records (14 offenders, 11 fine).

        Measured over the real tree as well as here: the whole-repo domain
        with this resolution in place yields the same two `NOT_A_ROW` nodes
        and nothing else.
        """
        for name, src in (
                ("regex alternation through a constant",
                 'import re\nSEP = "|"\ndef r(alts):\n'
                 '    return re.search(SEP.join(alts), "x")\n'),
                ("regex alternation inline",
                 'import re\ndef r(alts):\n'
                 '    return re.compile("|".join(alts))\n'),
                ("a legitimate render_row caller",
                 'from tables import render_row\ndef r(c):\n'
                 '    return render_row(c)\n'),
                ("same shapes, no pipe anywhere",
                 'S = ","\ndef r(c):\n    return f"{S}{S.join(c)}{S}"\n'),
                ("`%` with no pipe",
                 'def r(a, b):\n    return "%s / %s" % (a, b)\n'),
                ("a diagnostic, not a write path",
                 'SEP = "|"\ndef r(c):\n    return print(f"{SEP}{c}{SEP}")\n')):
            with self.subTest(shape=name):
                self.assertEqual(
                    RowBuilders(src).hits, [],
                    f"the guard cried wolf on {name}")

    def test_the_guard_sees_a_row_builder_in_any_shipped_directory(self):
        """**Round 5's F1, as a test.** The rule is over the repository.

        `_domain()` scanned `for d in ("bin", "viewer")` under a docstring
        that said DISCOVERED. A tracked builder in the author's own canonical
        shape, placed in `packs/software-ops/`, left THE RULE green — the only
        test that fired was the census-agreement one, whose message is about a
        guard/census disagreement and which skips itself when the evidence
        file is archived.

        So: plant that builder in every top-level shipped directory the tree
        actually has, discovered the same way the domain is, plus the
        repository root. Each one must be seen. A directory added tomorrow is
        covered by this test the day it appears, because nothing here is
        listed either.

        **TASK-341 moved the plant off the live tree and changed nothing
        else.** The earlier version wrote `perry_f1probe.py` into the
        repository root AND into every shipped directory at once — the widest
        write in the suite — with the note that "one short window is a smaller
        one". A smaller window is still a window: for its duration every other
        process reading this tree sees thirteen tracked-looking Python files
        that are not the repository's. `work/reference/review-constraints.md`
        does not say make the window short, it says **plant into a copy**.

        The discovery that F1 is about is untouched: `shipped_dirs()` asks the
        LIVE tree which directories exist, by the same exclusion the walk
        uses, so a directory added tomorrow is covered the day it appears. The
        scratch tree is then given those names and the real `_domain()` walks
        it. Re-narrow `_domain()` to `("bin", "viewer")` and every other
        directory goes red here, exactly as before.
        """
        body = ('def render(cells):\n'
                '    return "| " + " | ".join(cells) + " |"\n')
        names = shipped_dirs()
        self.assertGreater(len(names) + 1, 5,
                           "the domain walk found almost nothing to test")
        with scratch_tree(names) as root:
            probes = [root / "perry_f1probe.py"]
            probes += [root / n / "perry_f1probe.py" for n in names]
            for probe in probes:
                probe.write_text(body, encoding="utf-8")
            found = {f[0] for f in offenders(root=root)}
        for probe in probes:
            rel_dir = probe.parent.relative_to(root).as_posix()
            rel_dir = "" if rel_dir == "." else rel_dir
            with self.subTest(directory=rel_dir or "<repo root>"):
                self.assertIn(
                    probe.relative_to(root).as_posix(), found,
                    f"a hand-built row in {rel_dir or '<repo root>'} is "
                    f"invisible to the rule")

    def test_the_guard_domain_is_the_censuss_domain(self):
        """The walk and `git ls-files` must agree on which files are in scope.

        `_domain()` deliberately does not shell out to git — a `git archive`
        copy has none, and a domain that silently empties is a guard that
        silently passes. That independence is only safe if the two are checked
        against each other where git IS available, which is here.

        Skipped only when this is not a git checkout. Unlike the census
        *agreement* test, nothing depends on this one alone: the rule itself
        now walks the whole repository, so a narrowed domain fails
        `test_the_guard_sees_a_row_builder_in_any_shipped_directory` too.
        """
        import subprocess
        r = subprocess.run(["git", "ls-files"], cwd=str(PERRY_HOME),
                           capture_output=True, text=True)
        if r.returncode != 0 or not r.stdout.strip():
            self.skipTest("not a git checkout")
        census = set()
        for f in r.stdout.split():
            if f.startswith("tests/") or "__pycache__" in f:
                continue
            p = PERRY_HOME / f
            if not p.is_file() or f == CHOKE_POINT:
                continue
            if p.suffix == ".py":
                census.add(f)
                continue
            try:
                with p.open("rb") as fh:
                    first = fh.readline().decode("utf-8", "replace")
            except OSError:
                continue
            if first.startswith("#!") and "python" in first:
                census.add(f)
        mine = {p.relative_to(PERRY_HOME).as_posix() for p in _domain()}
        self.assertEqual(
            census - mine, set(),
            "these tracked Python files are in the census's domain and NOT "
            "in this guard's — the rule is narrower than it claims")

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

        Skipped **also when this is not a git checkout**, because the census
        script discovers its domain with `git ls-files` and therefore measures
        nothing in a `git archive` copy — which is how this project's
        reviewers do all destructive work. Round 5 hit exactly that and had to
        `git init` two scratch copies to get past it; a guard that reports a
        defect that does not exist is the hazard
        `work/reference/review-constraints.md` records. Nothing is lost by
        skipping: since round 6 the rule itself walks the whole repository and
        needs no census to see a hand-built row.
        """
        script = PERRY_HOME / "perry/evidence/2026-09/TASK-323-bound.py"
        if not script.exists():
            self.skipTest("census script not in the tree")
        import subprocess
        if subprocess.run(["git", "ls-files"], cwd=str(PERRY_HOME),
                          capture_output=True,
                          text=True).returncode != 0:
            self.skipTest("not a git checkout; the census measures nothing")
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


class TestTheChokePointsOwnInterior(unittest.TestCase):
    """**Both of these exist because a mutation came back GREEN.**

    The rule above exempts `viewer/tables.py` by name — it has to, or the
    choke point would flag itself — which means the guard cannot see inside
    the choke point at all. Two mutations to the module's own interior went
    green against the whole affected suite, and a green mutation is the
    finding. These are the tests that make them red.
    """

    def setUp(self):
        import sys
        sys.path.insert(0, str(PERRY_HOME / "viewer"))
        import tables
        self.T = tables

    def test_every_row_builder_inside_the_choke_point_is_named(self):
        """**The category, not the next instance.** Round 5's F3.

        The two tests below this one exist because two mutations to this
        module's interior came back green; they are behavioural tests of two
        named functions, and a *third* hand-built helper appended to
        `viewer/tables.py` was still silent — all thirteen tests green, no
        mutation needed:

            def render_header(cells):
                return "| " + " | ".join(str(c) for c in cells) + " |"

        `NOT_A_ROW` already had the shape of the answer: an allowlist keyed on
        something that does not move, with a rot-detector beside it. This is
        that construction pointed at the choke point's interior, which the
        rule above cannot see by construction.
        """
        self.assertEqual(
            interior_offenders(), [],
            "these build row text inside the choke point and no "
            "CHOKE_POINT_INTERIOR entry names them. Adding a row builder here "
            "is a real decision — the module docstring says every row of "
            "every state file goes through render_row — so name it and say "
            "why, or route it through render_row like everything else.")

    def test_a_new_row_builder_in_the_choke_point_is_caught(self):
        """The control that makes the test above a rule and not a listing.

        `render_header` verbatim from F3's proof, plus the `f"{SEP}"` shape
        F2 found silent, appended to the real module source in memory. The
        file on disk is never written — the round-5 review records this
        project paying once already for probes planted into a live tree.
        """
        src = (PERRY_HOME / CHOKE_POINT).read_text(encoding="utf-8")
        for name, extra in (
                ("render_header, F3's own probe",
                 '\n\ndef render_header(cells):\n'
                 '    return "| " + " | ".join(str(c) for c in cells) + " |"\n'),
                ("a resolved constant inside the choke point",
                 '\n\n_S = "|"\n\n\ndef render_head2(a, b):\n'
                 '    return f"{_S} {a} {_S} {b} {_S}"\n')):
            with self.subTest(shape=name):
                found = interior_offenders(src + extra)
                self.assertTrue(
                    found,
                    f"a hand-built row builder inside the choke point walked "
                    f"past: {name}")

    def test_the_named_interior_builders_still_exist(self):
        """`CHOKE_POINT_INTERIOR` is an allowlist and allowlists rot into a
        place people park things — the same argument
        `test_the_two_exempt_nodes_still_exist_and_are_still_not_rows` makes
        for `NOT_A_ROW`. A dead entry is cover for a future real builder in
        the same function, so it must be deleted rather than left."""
        live = {(fn, what)
                for fn, _, what in RowBuilders(
                    (PERRY_HOME / CHOKE_POINT).read_text(
                        encoding="utf-8")).scoped}
        for key in CHOKE_POINT_INTERIOR:
            with self.subTest(node=f"{key[0]} {key[1]}"):
                self.assertIn(
                    key, live,
                    f"{key[0]} no longer contains {key[1]}; the entry is dead "
                    f"and should be deleted, not left as cover")

    def test_render_separator_inherits_render_rows_refusal(self):
        """**Mutation M8 was green.** `render_separator` was replaced by the
        hand-built `"|" + "---|" * n` it exists to remove, and nothing went
        red — because the two produce identical bytes for every n a real
        caller passes, so no round-trip or byte test can tell them apart.

        Routing has exactly one observable consequence, and this is it: the
        refusals are inherited. `render_row([])` refuses an empty cell list,
        so `render_separator(0)` refuses too. The hand-built version returns
        `"|"` — a separator row for a table with no columns, written under a
        header `render_row` would have refused to write.
        """
        with self.assertRaises(self.T.UnrenderableCell):
            self.T.render_separator(0)

    def test_render_separator_agrees_with_render_row_on_the_cells(self):
        """The other half of routing: the separator's cell count is
        `render_row`'s, not a second count computed from `n` again. A header
        and its separator disagreeing is the ragged row this row is about.
        """
        for n in range(1, 16):
            with self.subTest(n=n):
                self.assertEqual(
                    self.T.split_row(self.T.render_separator(n)),
                    self.T.split_row(self.T.render_row(["---"] * n)))

    def test_render_separator_is_byte_identical_to_what_it_replaced(self):
        """Deliberate, and asserted so a later 'tidy-up' cannot quietly
        rewrite every table in every state file. All three spellings the
        eight routed sites used produced the same bytes; so does this."""
        for n in range(1, 16):
            with self.subTest(n=n):
                out = self.T.render_separator(n)
                self.assertEqual(out, "|" + "|".join(["---"] * n) + "|")
                self.assertEqual(out, "|" + "---|" * n)

    def test_a_separator_row_that_cannot_be_widened_is_refused(self):
        """**Mutation M9 was green.** The count assertion in
        `append_separator_cell` was replaced by `if False:` and nothing went
        red.

        The assertion is not dead code — a brute-force sweep of 50526
        separator-shaped lines fires it on 9399 of them. It was green because
        nothing exercised it. A hand-edited separator ending in a lone
        backslash is the realistic case: copying its last cell yields a row
        one cell short, which is the 7-header/6-separator ragged widen the
        function's own docstring is about.
        """
        for line in ("|", "|---|---\\"):
            with self.subTest(line=line):
                with self.assertRaises(self.T.UnrenderableCell):
                    self.T.append_separator_cell(line)

    def test_widening_a_separator_keeps_its_style_and_adds_one_cell(self):
        """The control for the test above: the shapes that are fine stay
        fine, in the file's own dashes-and-colons style."""
        for line, want in (("|---|---|", "|---|---|---|"),
                           ("|-----|:---:|", "|-----|:---:|:---:|"),
                           ("|---|---", "|---|---|---|")):
            with self.subTest(line=line):
                out = self.T.append_separator_cell(line)
                self.assertEqual(out, want)
                self.assertEqual(len(self.T.split_row(out)),
                                 len(self.T.cell_spans(line)) + 1)


if __name__ == "__main__":
    unittest.main()
