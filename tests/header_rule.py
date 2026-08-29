"""The one-header-rule check. TASK-050 round 9 — **one net, over a symbol.**

Rounds 2 through 7 each shipped a better DETECTOR of a second header rule and
each was defeated within one review:

    round 2  three copies in files that never imported `squash`
    round 3  a SUBDIRECTORY was invisible; the pattern matched a SPELLING
    round 4  the `[` had to sit right after the `=`; and `_is_python` trusted
             the extension, so the same bytes were green without a shebang
    round 5  it knew `split_row(` and not the private splitter `.split("|")`
    round 5's REVIEW  nine planted spellings, FIVE escaped both nets
    round 6  the regex became an AST walk
    round 7's REVIEW  the walk's GATE is still an eleven-name allowlist of
             variable names: `[squash(c) for c in prev_cells]` at
             viewer/parsers.py could be reverted to the historical rule,
             silently drop a KR out of a user's OKR, and leave 2882 tests green
    round 8   kept the defeated shape net ALONGSIDE the symbol check, and the
             shape net promptly reported correct code — a value normalizer
             appended to `bin/perry-explain` turned `bash tests/run` red and one
             of the two failing tests was named
             `test_value_normalizers_are_not_flagged`

**Round 9 deleted the shape net.** Not because it was unfinished — because
finishing it is the thing seven rounds proved cannot be done, and keeping it
next to the check that replaces it is what put a false positive in front of
correct code. What is left is one net, and it is the one the amendment asks
for:

## The net. `offenders_by_symbol()`

*Nothing outside `viewer/tables.py § header_index` applies `squash` (or its
`norm` alias) to a header row or to a cell of one.*

It is the drift half — the same rule, copied — and it is the half the design
makes decidable, because after round 8's conversion the tree contains **zero**
such sites. The check is an equality against zero over one symbol.

It holds **no allowlist of variable names of any kind**. A row is what
`split_row` or `header_index` produced, followed through local dataflow:
assignment, aliasing, slicing, subscript, a walrus, an iterable wrapper, one
element-preserving comprehension unwrap, a parameter this file passes a row to,
and what a file-local function RETURNS. `ROW_NAMES` (eleven variable names) and
the `("header", "headers", "hdr")` subscript test are **deleted**; `BLESSED` and
`ROW_PRODUCERS` name FUNCTIONS this repository is allowed to have, which is the
design and not a spelling.

It cannot fire on a value normalizer, because a value normalizer folds a value
and not a row — that is not an exception carved out for it, it is what the two
words mean. Round 8's declared false positive came from treating any
`.split("|")` as a row source, which cannot tell `line.split("|")` from
`cell.split("|")`. **That inference is gone.** Criterion 3's own guard —
`tests/test_row_integrity.py § test_no_tool_splits_a_row_on_a_raw_pipe` —
already forbids a bare `.split("|")` anywhere in `bin/` or `viewer/`, so
nothing here needs to guess about one.

## What this net does NOT see, and what covers it instead

**A reader that invents its OWN rule** — `[c.strip("*` ").lower() for c in
cells]` — calls no blessed symbol, so this net is blind to it by construction.
That class is the whole of `tests/test_header_rule_harness.py § SECOND_RULE`,
which plants every shape the round 5 and round 7 reviews name (each entry
quoting the review line it comes from) and **asserts that it escapes**, so the
limit is a measured number rather than a claim.

What covers that class is not a net:

1. `viewer/tables.py § header_index` is the only function that folds a header
   cell, so there is nothing for a second rule to be a second copy OF; and
2. `tests/test_header_index_is_the_only_fold.py` watches the real readers parse
   a real decorated document and asks both *who folded a header cell* and *did
   every decorated header cell reach `header_index`*. A reader that grows its
   own rule stops reaching it, and that test goes red.

Its limit is stated there and measured there: it sees the readers a parse
reaches, and the module reports exactly which readers those are, with fold
counts, rather than listing readers it never observes.
"""

from __future__ import annotations

import ast
import warnings
from pathlib import Path

#: The one rule, its `perry-lint` alias, and the one function allowed to apply
#: it to a header row. **Names of FUNCTIONS**, which is what the design is
#: made of — not names of variables, which is what rounds 5 to 7 were failed
#: for.
BLESSED = frozenset({"squash", "norm", "header_index", "header_keys"})

#: The two names in `BLESSED` that are the RULE rather than the blessed
#: wrapper. A site that applies one of these to a row, outside `header_index`,
#: is a second copy of the one rule.
THE_RULE = frozenset({"squash", "norm"})

#: Builtins that wrap an iterable without changing what its elements ARE.
ITERABLE_WRAPPERS = frozenset({
    "enumerate", "reversed", "list", "tuple", "sorted", "set", "iter",
    "zip", "filter"})

#: Calls that PRODUCE a row's cells. **Two entries, and they are the two
#: functions this repository is allowed to have**: `split_row` is the only row
#: splitter (criterion 3, guarded independently by
#: `tests/test_row_integrity.py`) and `header_index` is the only header fold.
#: Anything else that yields a row — `bin/perry-state § cells_of`,
#: `Board.section_table` — is resolved by `_RowLocals` from what it RETURNS.
ROW_PRODUCERS = frozenset({"split_row", "header_index"})

#: Directories whose contents are not readers of a user's document.
#: `tests/` is this check's own scaffolding and plants these shapes on purpose;
#: `viewer/tables.py` DEFINES the rule. Both are named with a reason, and
#: nothing else is skipped — round 4 failed this row for a scan that could not
#: see a file outside two named directories.
NOT_A_READER = ("tests", ".git", "__pycache__", ".perry")


def is_python(p: Path) -> bool:
    """A Python source file, by **what it is** — not by suffix and not by line 1.

    Round 4 measured the previous rule's two holes and five rounds carried them
    untouched: *"any non-`.py` suffix returns False without reading anything"*
    and *"a file whose first line is a docstring, a `# -*- coding:` line, or a
    licence header is invisible"*. The same bytes were green at
    `bin/perry-rowdump`, red with a shebang, red with a `.py` suffix.

    So this asks the parser. A file is Python when Python can parse it AND it
    declares something — an import, a definition, an assignment. Prose that
    happens to be comment-shaped parses to an empty module and does not
    qualify; a bash script does not parse at all.
    """
    if p.suffix == ".py":
        return True
    try:
        text = p.read_text(errors="replace")
    except OSError:
        return False
    if "\x00" in text[:4096]:
        return False
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError):
        return False
    return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef, ast.Import, ast.ImportFrom,
                              ast.Assign, ast.AnnAssign))
               for n in ast.walk(tree))


def readers_under(root) -> list[Path]:
    """Every Python reader under `root`, minus the file that DEFINES the rule.

    **The whole tree, not two directories.** Round 4's third hole — carried
    forward through rounds 5, 6, 7 and 8 — is that a Python reader outside
    `bin/` and `viewer/` was invisible: `packs/`, `modes/`, `decide/`,
    `goals/`, `templates/*/bin/`. Widening costs nothing, because this net
    fires only on the blessed symbol applied to a row and prose does not
    contain one.
    """
    root = Path(root)
    out = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).parts
        if any(part in NOT_A_READER for part in rel):
            continue
        if p == root / "viewer" / "tables.py":
            continue
        if is_python(p):
            out.append(p)
    return sorted(out)


def _preserves_elements(comp) -> bool:
    """Whether a comprehension yields its own loop variable, lightly touched.

    `[c.strip() for c in cells]` does; `[_as_dict(h, c) for c in cells]` does
    not — it yields a dict, and treating its result as a row's cells is how a
    taint analysis turns into a false-positive generator.
    """
    bound = {t.id for g in comp.generators for t in ast.walk(g.target)
             if isinstance(t, ast.Name)}
    node = comp.elt
    while True:
        if isinstance(node, ast.Name):
            return node.id in bound
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            node = node.func.value           # `c.strip("*` ").lower()`
            continue
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and len(node.args) == 1:
            node = node.args[0]              # `squash(c)`, `_norm(c)`
            continue
        return False


class _RowLocals:
    """Names that hold a row's cells — or ONE cell of one — by **local
    dataflow**, per function.

    Round 7's finding was that the gate in front of an otherwise genuine AST
    walk was an eleven-name allowlist of variable names. Round 8 demoted it to
    a fallback and round 8's reviewer measured that the fallback was still
    load-bearing for eight of thirty catches. **Round 9 deleted it.** A name is
    a row because something in this function put a row in it, and for no other
    reason.

    **Scoped per function**, because a module-wide taint set makes one
    `cells = split_row(l)` colour every `cells` in a 3000-line file and a
    check that reports correct code is the failure mode criterion 4 names.
    File-local by construction: cross-module dataflow is a type checker's job.
    """

    def __init__(self, tree: ast.AST) -> None:
        self.tree = tree
        #: Named definitions — the ones a `Return` and a call can belong to.
        self.funcs = [n for n in ast.walk(tree)
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        #: Every callable BODY, lambdas included, because a `lambda` bound to a
        #: name is how round 7's reviewer escaped the walk and it takes an
        #: argument exactly like a `def` does.
        self.bodies = [n for n in ast.walk(tree)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                         ast.Lambda))]
        #: `name -> callable body`, for `def f(...)` and for `f = lambda ...`.
        self.by_name: dict[str, object] = {f.name: f for f in self.funcs}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name) \
                    and isinstance(node.value, ast.Lambda):
                self.by_name.setdefault(node.targets[0].id, node.value)
        #: `local name -> the BLESSED name it IS`. **Round 9's finding, and it
        #: is the corollary of deleting the shape net**: with the net gone the
        #: whole static claim rests here, and here recognised the rule by the
        #: FUNCTION'S NAME rather than by the symbol. A `def` wrapper and a
        #: name-bound `lambda` were both resolved — the two HARDER
        #: indirections — and the one-liner was not:
        #:
        #:     CAUGHT  fold = lambda s: squash(s)     ESCAPED  fold = squash
        #:     CAUGHT  def fold(s): return squash(s)  ESCAPED  from tables
        #:                                                     import squash as fold
        #:                                            ESCAPED  fold = tables.squash
        #:
        #: and the escaping form is **this repository's own idiom**:
        #: `bin/perry-lint:250` is literally `norm = squash`, seen today only
        #: because `norm` happens to be in `BLESSED`. The round 9 reviewer
        #: planted `_fold = squash` into `bin/perry-tasks` — the one converted
        #: reader the runtime watch does not drive — and `offenders_by_symbol`
        #: returned `[]` with the whole suite at its three pre-existing
        #: failures.
        #:
        #: This is not a list of names: a name is here because a binding in
        #: THIS FILE put the blessed function object in it, and for no other
        #: reason. File-wide rather than per-function, matching `by_name`:
        #: an import binds at module level and is called from every function
        #: in the file.
        self.aliases: dict[str, str] = {}
        self._resolve_aliases(tree)
        #: The two frozensets `offenders_by_symbol` actually asks, per file:
        #: the blessed names plus everything this file bound to one, and the
        #: RULE names plus everything this file bound to one of those. An
        #: alias of `header_index` is blessed but is not the rule, exactly as
        #: `header_index` itself is.
        self.blessed = frozenset(BLESSED | set(self.aliases))
        self.rule = frozenset(
            THE_RULE | {n for n, t in self.aliases.items() if t in THE_RULE})
        #: names holding a ROW (an iterable of cells)
        self.scope: dict[object, set[str]] = {None: set()}
        #: names holding ONE CELL of a row — `for c in split_row(l)`, `h[0]`
        self.cells: dict[object, set[str]] = {None: set()}
        for f in self.bodies:
            self.scope[f] = set()
            self.cells[f] = set()
        self.owner: dict[object, object] = {}
        # INNERMOST wins. `ast.walk` is breadth-first, so a nested function
        # comes after the one that contains it and overwrites its claim —
        # `bin/perry-state § parse_tracks` defines `cells_of` inside itself,
        # and attributing that helper's `return` to its enclosing function
        # said `parse_tracks` returns a row and `cells_of` returns nothing.
        for f in self.bodies:
            for sub in ast.walk(f):
                self.owner[sub] = f
        #: `{function name: {tuple positions that are a row, -1 for a bare
        #: return}}`. `_, ihdr = self.section_table("Intake")` is how
        #: `bin/perry-task` gets a header row, and round 7 measured BOTH of
        #: its `ihdr` sites as escaping — because the walk asked what the
        #: variable was called. This asks what the function returned.
        self.returns: dict[str, set[int]] = {}
        #: **Round 11, and it is the hole round 10's reviewer walked through
        #: with this repository's own idiom.** `bin/perry_store.py:854` is
        #: `header, keys = table["header"], table["keys"]`, and one line under
        #: it a bare `squash` folded that row with every guard silent —
        #: because a row carried on a DICT KEY was not a row here.
        #:
        #: A path says where a row sits INSIDE a value, read left to right
        #: from the value: `("key:header",)` — subscript by the string
        #: `header`; `("elem", "key:header")` — index or iterate, then
        #: subscript; `("pos:1", "elem", "key:header")` — a tuple position
        #: first; `("attr:header",)` — an object attribute. The EMPTY path is
        #: the row itself and lives in `self.scope`, so nothing here
        #: duplicates what was already there.
        #:
        #: This is the same bookkeeping `returns` already did for tuple
        #: positions, one step wider — provenance, not recognition. A path
        #: exists only because an expression in THIS FILE put a row there, so
        #: it cannot colour a value the way an allowlist of key names would.
        self.paths: dict[object, dict[str, set[tuple]]] = {}
        #: `function or class name -> paths in what it RETURNS`. The chain the
        #: reviewer's plant rode is four links long and entirely file-local:
        #: `markdown_tables` appends `{"header": split_row(...)}` to `out`,
        #: `risk_section_shape` returns `("table", tables)`, `risk_table`
        #: returns `tables[0]`, `risk_plan` unpacks `table["header"]`.
        self.rpaths: dict[str, set[tuple]] = {}
        #: `self.header = split_row(l)` in a method makes `T(line).header` a
        #: row, so a class is a producer exactly the way a function is.
        self.class_of: dict[object, str] = {}
        for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
            for sub_node in ast.walk(cls):
                if isinstance(sub_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.class_of.setdefault(sub_node, cls.name)
        # The fixpoint is over the paths too, and it needs more passes than
        # round 10's six: each link of a chain like the one above is closed by
        # a LATER pass, because a function's return is read before the local
        # that feeds it is bound. It still stops the moment nothing moves.
        for _ in range(12):
            before = ({k: set(v) for k, v in self.scope.items()},
                      {k: set(v) for k, v in self.cells.items()},
                      self._paths_snapshot())
            self._pass()
            if all(self.scope[k] == before[0][k] for k in self.scope) \
                    and all(self.cells[k] == before[1][k] for k in self.cells) \
                    and self._paths_snapshot() == before[2]:
                break

    def _alias_target(self, value) -> str | None:
        """The BLESSED name this expression IS, or `None`.

        `squash` -> `squash`; `tables.squash` / `ops.norm` -> the attribute,
        which is how the rule already travels between this repository's
        modules; a name already resolved as an alias -> what it resolves to,
        so `a = squash; fold = a` closes on the second pass.
        """
        if isinstance(value, ast.Name):
            name = value.id
        elif isinstance(value, ast.Attribute):
            name = value.attr
        else:
            return None                # a call, a lambda, a subscript: not an alias
        if name in BLESSED:
            return name
        return self.aliases.get(name)

    def _resolve_aliases(self, tree: ast.AST) -> None:
        """Every name this file binds directly to the one rule.

        Three shapes, which are the three the round 9 review planted and
        measured escaping — `fold = squash`, `from tables import squash as
        fold`, `fold = tables.squash`. Run to a fixpoint so a chain resolves;
        four passes is far past any chain a reader would write.

        Deliberately NOT resolved, and recorded as a limit rather than
        widened: a rebinding through a container (`FOLDS["k"] = squash`), a
        function that RETURNS the rule (`def picker(): return squash`), and a
        binding made in another module. The first two are a second-rule shape
        by another road; the third is a type checker's job and this walk is
        file-local by construction.
        """
        for _ in range(4):
            before = dict(self.aliases)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    for a in node.names:
                        if a.asname and a.name in BLESSED:
                            self.aliases.setdefault(a.asname, a.name)
                    continue
                if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                        and isinstance(node.targets[0], ast.Name):
                    target = self._alias_target(node.value)
                    if target and node.targets[0].id != target:
                        self.aliases.setdefault(node.targets[0].id, target)
            if self.aliases == before:
                break

    def of(self, node) -> object:
        """The function a node sits in, or None for module level."""
        return self.owner.get(node)

    def _pass(self) -> None:
        # Which file-local functions RETURN a row, and at which tuple position.
        for f in self.funcs:
            for node in ast.walk(f):
                if not isinstance(node, ast.Return) or node.value is None:
                    continue
                if self.of(node) is not f:
                    continue
                if isinstance(node.value, ast.Tuple):
                    for i, el in enumerate(node.value.elts):
                        if self.source(el, f):
                            self.returns.setdefault(f.name, set()).add(i)
                elif self.source(node.value, f):
                    self.returns.setdefault(f.name, set()).add(-1)
                # ...and where a row sits INSIDE what it returns.
                for pth in self._paths(node.value, f):
                    if pth:
                        self.rpaths.setdefault(f.name, set()).add(pth)
            # A GENERATOR is a producer too. `bin/perry-task §
            # _section_tables` is *the ONE walk over the board's task-bearing
            # sections* and it `yield`s its tables; `task_tables()` and
            # `find()` both read `table["header"]` off what it yields. Only
            # `Return` was read before, so a locally-built table handed over
            # by `yield` was a local case still open.
            for node in ast.walk(f):
                if not isinstance(node, (ast.Yield, ast.YieldFrom)) \
                        or node.value is None:
                    continue
                if self.of(node) is not f:
                    continue
                step = () if isinstance(node, ast.YieldFrom) else ("elem",)
                for pth in self._paths(node.value, f):
                    if step + pth:
                        self.rpaths.setdefault(f.name, set()).add(step + pth)
        # A name-bound `lambda` returns its body.
        for name, body in self.by_name.items():
            if isinstance(body, ast.Lambda) and self.source(body.body, body):
                self.returns.setdefault(name, set()).add(-1)
        for f in list(self.scope):
            body = f if f is not None else self.tree
            for node in ast.walk(body):
                if self.of(node) is not (f if f is not None else None):
                    continue
                # A loop or comprehension over a row binds ONE CELL.
                if isinstance(node, (ast.For, ast.AsyncFor)) \
                        and self.source(node.iter, f):
                    for t in ast.walk(node.target):
                        if isinstance(t, ast.Name):
                            self.cells[f].add(t.id)
                if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp,
                                     ast.GeneratorExp)):
                    for g in node.generators:
                        if self.source(g.iter, f):
                            for t in ast.walk(g.target):
                                if isinstance(t, ast.Name):
                                    self.cells[f].add(t.id)
                # A loop over a list of TABLES binds one table — `for table in
                # task_tables:` at `bin/perry_store.py:531`, whose next line is
                # `header = table["header"]`.
                if isinstance(node, (ast.For, ast.AsyncFor)):
                    self._bind_element(node.target, node.iter, f)
                if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp,
                                     ast.GeneratorExp)):
                    for g in node.generators:
                        self._bind_element(g.target, g.iter, f)
                # A container this function FILLS carries what was put in it.
                # `out.append({"header": header, ...})` is how
                # `bin/perry_store.py § markdown_tables` returns its tables,
                # and it is the first link of the four-link chain the round 10
                # reviewer's plant rode to `risk_plan`.
                if isinstance(node, ast.Call) \
                        and isinstance(node.func, ast.Attribute) \
                        and isinstance(node.func.value, ast.Name) and node.args:
                    holder, attr = node.func.value.id, node.func.attr
                    if attr in ("append", "add"):
                        new = {("elem",) + q for q in self._paths(node.args[0], f)}
                    elif attr in ("extend", "update"):
                        new = set(self._paths(node.args[0], f))
                    elif attr == "insert" and len(node.args) > 1:
                        new = {("elem",) + q for q in self._paths(node.args[1], f)}
                    elif attr == "setdefault" and len(node.args) > 1 \
                            and isinstance(node.args[0], ast.Constant) \
                            and isinstance(node.args[0].value, str):
                        new = {(f"key:{node.args[0].value}",) + q
                               for q in self._paths(node.args[1], f)}
                    else:
                        new = set()
                    self._add_path(f, holder, new)
                if isinstance(node, ast.Assign):
                    targets, value = node.targets, node.value
                elif isinstance(node, (ast.AnnAssign, ast.AugAssign,
                                       ast.NamedExpr)):
                    targets, value = [node.target], node.value
                else:
                    continue
                if value is None:
                    continue
                # A tuple unpack, ELEMENT BY ELEMENT. Two spellings reach
                # here and round 10 resolved only the first:
                #   `_, ihdr = board.section_table("Intake")`  (round 9's)
                #   `header, keys = table["header"], table["keys"]`
                # The second is `bin/perry_store.py:854` — the exact line the
                # round 10 reviewer planted one line under, three times over
                # in that file alone.
                positions = self._returns_of(value)
                if len(targets) == 1 and isinstance(targets[0], (ast.Tuple,
                                                                 ast.List)):
                    vpaths = self._paths(value, f)
                    elts = (value.elts
                            if isinstance(value, (ast.Tuple, ast.List))
                            else None)
                    bound = False
                    for i, t in enumerate(targets[0].elts):
                        if not isinstance(t, ast.Name):
                            continue
                        sub_p = {q[1:] for q in vpaths
                                 if q and q[0] == f"pos:{i}"}
                        if elts is not None and i < len(elts):
                            if self.cell(elts[i], f):
                                self.cells[f].add(t.id)
                                bound = True
                        if i in positions or () in sub_p:
                            self.scope[f].add(t.id)
                            bound = True
                        if {q for q in sub_p if q}:
                            self._add_path(f, t.id, sub_p)
                            bound = True
                    if bound:
                        continue
                # A row written INTO something — `spec["header"] = header`,
                # `self.header = split_row(line)`. The second makes
                # `T(line).header` a row wherever this file builds a `T`,
                # which is the attribute half of the same escape.
                for t in targets:
                    if isinstance(t, ast.Subscript) \
                            and isinstance(t.slice, ast.Constant) \
                            and isinstance(t.slice.value, str):
                        step, holder = f"key:{t.slice.value}", t.value
                    elif isinstance(t, ast.Attribute):
                        step, holder = f"attr:{t.attr}", t.value
                    else:
                        continue
                    if not isinstance(holder, ast.Name):
                        continue
                    carried = {(step,) + q for q in self._paths(value, f)}
                    self._add_path(f, holder.id, carried)
                    if holder.id == "self" and self.class_of.get(f):
                        for q in carried:
                            self.rpaths.setdefault(
                                self.class_of[f], set()).add(q)
                # ...and the paths a plain name carries along with it.
                if len(targets) == 1 and isinstance(targets[0], ast.Name):
                    self._add_path(f, targets[0].id, self._paths(value, f))
                if self.cell(value, f):
                    for t in targets:
                        for n in ast.walk(t):
                            if isinstance(n, ast.Name):
                                self.cells[f].add(n.id)
                if not self.source(value, f):
                    continue
                for t in targets:
                    for n in ast.walk(t):
                        if isinstance(n, ast.Name):
                            self.scope[f].add(n.id)
        # A parameter this FILE passes a row to IS a row, one level. That
        # closes `def read(cells)` by provenance rather than by the name.
        for call in [n for n in ast.walk(self.tree) if isinstance(n, ast.Call)]:
            if not isinstance(call.func, ast.Name):
                continue
            fn = self.by_name.get(call.func.id)
            if fn is None:
                continue
            params = [a.arg for a in fn.args.args]
            caller = self.of(call)
            for i, arg in enumerate(call.args):
                if i >= len(params):
                    continue
                if self.source(arg, caller):
                    self.scope[fn].add(params[i])
                elif self.cell(arg, caller):
                    self.cells[fn].add(params[i])
                # ...and a parameter this file passes a TABLE to carries the
                # table's paths, which is the same sentence one step wider.
                self._add_path(fn, params[i], self._paths(arg, caller))

    def _bind_element(self, target, iterable, scope) -> None:
        """`for X in <a list of tables>` — X is one table, with the paths the
        list said its elements have. A tuple target unpacks by position, which
        is `for title, pri, i, table in self._section_tables():` at
        `bin/perry-task:875`."""
        got = {q[1:] for q in self._paths(iterable, scope)
               if q and q[0] == "elem"}
        if isinstance(target, (ast.Tuple, ast.List)):
            for i, t in enumerate(target.elts):
                if not isinstance(t, ast.Name):
                    continue
                sub_p = {q[1:] for q in got if q and q[0] == f"pos:{i}"}
                if () in sub_p:
                    self.scope[scope].add(t.id)
                self._add_path(scope, t.id, sub_p)
            return
        if not isinstance(target, ast.Name):
            return
        if () in got:
            self.scope[scope].add(target.id)
        self._add_path(scope, target.id, got)

    def _paths_snapshot(self):
        """Everything the path fixpoint has to stop moving before it stops."""
        return ({k: {n: frozenset(v) for n, v in d.items()}
                 for k, d in self.paths.items()},
                {k: frozenset(v) for k, v in self.rpaths.items()})

    def _paths_of_name(self, scope, name: str) -> set[tuple]:
        return self.paths.get(scope, {}).get(name, set())

    def _add_path(self, scope, name: str, paths) -> None:
        """Bind non-empty paths to a local name. The EMPTY path is a row and
        belongs to `self.scope`; recording it here as well would give two
        answers to one question."""
        keep = {p for p in paths if p}
        if keep:
            self.paths.setdefault(scope, {}).setdefault(name, set()).update(keep)

    def _rpaths_of(self, node: ast.AST) -> set[tuple]:
        """Paths in what a call to a file-local function — or a file-local
        class — returns. Resolved by the callee's NAME, exactly as
        `_returns_of` already resolves tuple positions."""
        if not isinstance(node, ast.Call):
            return set()
        if isinstance(node.func, ast.Name):
            return self.rpaths.get(node.func.id, set())
        if isinstance(node.func, ast.Attribute):
            return self.rpaths.get(node.func.attr, set())
        return set()

    def _paths(self, node: ast.AST, scope) -> set[tuple]:
        """Where a row sits inside this expression's value.

        `()` in the answer means the expression IS a row, which is what
        `source()` asks. Every other member says "one more step and it is".
        """
        out: set[tuple] = set()
        if self._source_direct(node, scope):
            out.add(())
        if isinstance(node, ast.Name):
            out |= self._paths_of_name(scope, node.id)
            return out
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    for p in self._paths(v, scope):
                        out.add((f"key:{k.value}",) + p)
            return out
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for i, el in enumerate(node.elts):
                for p in self._paths(el, scope):
                    out.add(("elem",) + p)
                    out.add((f"pos:{i}",) + p)
            return out
        if isinstance(node, ast.Subscript):
            base = self._paths(node.value, scope)
            if isinstance(node.slice, ast.Slice):
                return out | base       # a slice of a list of tables is one
            key = node.slice.value if isinstance(node.slice, ast.Constant) else None
            for p in base:
                if not p:
                    continue
                if isinstance(key, str):
                    if p[0] == f"key:{key}":
                        out.add(p[1:])
                elif isinstance(key, int):
                    if p[0] in ("elem", f"pos:{key}"):
                        out.add(p[1:])
                elif p[0] == "elem":
                    out.add(p[1:])      # `tables[n]`, index not known here
            return out
        if isinstance(node, ast.Attribute):
            for p in self._paths(node.value, scope):
                if p and p[0] == f"attr:{node.attr}":
                    out.add(p[1:])
            return out
        if isinstance(node, ast.Call):
            out |= self._rpaths_of(node)
            if isinstance(node.func, ast.Name) \
                    and node.func.id in ITERABLE_WRAPPERS:
                for a in node.args:
                    out |= self._paths(a, scope)
            if isinstance(node.func, ast.Attribute) \
                    and node.func.attr in {"copy", "get", "pop"}:
                base = self._paths(node.func.value, scope)
                if node.func.attr == "copy":
                    out |= base
                elif node.args and isinstance(node.args[0], ast.Constant) \
                        and isinstance(node.args[0].value, str):
                    want = f"key:{node.args[0].value}"
                    out |= {p[1:] for p in base if p and p[0] == want}
            return out
        if isinstance(node, ast.IfExp):
            return (out | self._paths(node.body, scope)
                    | self._paths(node.orelse, scope))
        if isinstance(node, ast.BoolOp):
            for v in node.values:
                out |= self._paths(v, scope)
            return out
        return out

    def _returns_of(self, node: ast.AST) -> set[int]:
        """Tuple positions of a call to a file-local row-returning function."""
        if not isinstance(node, ast.Call):
            return set()
        if isinstance(node.func, ast.Name):
            return self.returns.get(node.func.id, set())
        if isinstance(node.func, ast.Attribute):
            return self.returns.get(node.func.attr, set())
        return set()

    def source(self, node: ast.AST, scope=...) -> bool:
        """Does this expression yield a ROW'S CELLS, in `scope`?

        Two answers, and the second is round 11's. `_source_direct` is round
        9's dataflow — assignment, aliasing, slicing, a walrus, a wrapper, one
        comprehension unwrap, a parameter, what a function returns. `_paths`
        adds the step it did not have: a row CARRIED inside something this
        file built — a dict key, a list element, a tuple position, an object
        attribute — which is how `bin/perry_store.py`, `bin/perry-task`,
        `bin/perry-tasks` and `bin/perry_md_store.py` hold a header row
        seventeen times over.
        """
        if scope is ...:
            scope = self.of(node)
        if self._source_direct(node, scope):
            return True
        return () in self._paths(node, scope)

    def _source_direct(self, node: ast.AST, scope) -> bool:
        """Round 9's local dataflow, unchanged. Recursive steps go back
        through `source`, so a carried row resolves at any depth."""
        names = self.scope.get(scope, set())
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ROW_PRODUCERS:
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ROW_PRODUCERS:
            return True                    # `ops.split_row(l)`, `L.header_index(h)`
        if -1 in self._returns_of(node):
            return True                    # a file-local function that returns one
        if isinstance(node, ast.Name):
            return node.id in names
        # `cells[1:]` — a SLICE of a row is a row. `cells[0]` is one CELL and
        # is answered by `cell()`, not here.
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Slice):
                return self.source(node.value, scope)
            return False
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ITERABLE_WRAPPERS:
            return any(self.source(a, scope) for a in node.args)
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            # ONE unwrap: a comprehension over an already-split row is still a
            # row's cells — but only while its element expression PRESERVES
            # the element. `rows += [_as_dict(header, c) for c in cells]` at
            # `bin/perry-diagnose` yields dicts, and colouring `rows` a row
            # made the check report a stage-vocabulary value normalizer three
            # hundred lines away.
            return (_preserves_elements(node)
                    and any(self.source(g.iter, scope) for g in node.generators))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in {"strip", "copy"}:
            return self.source(node.func.value, scope)
        if isinstance(node, ast.IfExp):
            return self.source(node.body, scope) or self.source(node.orelse, scope)
        return False

    def cell(self, node: ast.AST, scope=...) -> bool:
        """Does this expression yield ONE CELL of a row, in `scope`?

        **The scalar half, and it is here because round 8's reviewer showed
        the class was outside both nets by construction** — which is the shape
        of `viewer/parsers.py § read_conformance`, the "fifth copy", and of
        `bin/perry-state:157`'s `squash(cells[0]) != "term"`, which round 4
        reverted to a second rule with all 1363 tests green.
        """
        if scope is ...:
            scope = self.of(node)
        if isinstance(node, ast.Name):
            return node.id in self.cells.get(scope, set())
        if isinstance(node, ast.Subscript) and not isinstance(node.slice, ast.Slice):
            return self.source(node.value, scope)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in {"strip", "lstrip", "rstrip", "lower",
                                       "casefold", "upper", "replace", "title"}:
            return self.cell(node.func.value, scope)
        if isinstance(node, ast.IfExp):
            return self.cell(node.body, scope) or self.cell(node.orelse, scope)
        return False


def _blessed_calls(node: ast.AST, blessed=BLESSED) -> list[str]:
    """Every BLESSED name applied in this expression, as a mapping function.

    `squash(c)` -> ['squash'];  `map(norm, cells)` -> ['norm'].
    A bare `ast.Name` counts only where it is being USED AS the mapping
    function, which is what `_mapping_sites` hands over as the element
    expression.

    `blessed` is the file's own set — `BLESSED` plus every name this file
    BOUND to one of them (`_RowLocals.blessed`). Round 9 asked `BLESSED`
    directly and `fold = squash` walked past.
    """
    found: list[str] = []
    if isinstance(node, ast.Name) and node.id in blessed:
        found.append(node.id)                    # `map(norm, cells)`
    if isinstance(node, ast.Attribute) and node.attr in blessed:
        found.append(node.attr)                  # `map(ops.norm, cells)`
    if isinstance(node, ast.Lambda):
        found.extend(_blessed_calls(node.body, blessed))
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            if isinstance(sub.func, ast.Attribute) and sub.func.attr in blessed:
                found.append(sub.func.attr)
            elif isinstance(sub.func, ast.Name) and sub.func.id in blessed:
                found.append(sub.func.id)
    return found


def _mapping_sites(node: ast.AST):
    """`(element expression, source expression)` for every mapping construct."""
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
        for g in node.generators:
            yield node.elt, g.iter
    elif isinstance(node, ast.DictComp):
        for g in node.generators:
            yield node.key, g.iter
            yield node.value, g.iter
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id in {"map", "filter"} and len(node.args) >= 2:
            yield node.args[0], node.args[1]
        elif node.func.id in {"sorted", "min", "max"} and node.args:
            for kw in node.keywords:
                if kw.arg == "key":
                    yield kw.value, node.args[0]


def offenders_by_symbol(root) -> list[str]:
    """Every site outside `header_index` that applies `squash`/`norm` to a
    header row or to a cell of one. **Zero after TASK-050.**

    `path:line: source`, sorted, one entry per site. The path is relative to
    `root` and not the bare filename: round 9's corpus plants the same shape at
    `bin/`, `bin/lib/`, `viewer/` and `packs/`, and a bare filename cannot tell
    a hit at one from a hit at another.
    """
    out: list[str] = []
    root = Path(root)
    for p in readers_under(root):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                warnings.simplefilter("ignore", SyntaxWarning)
                tree = ast.parse(p.read_text(errors="replace"))
        except (SyntaxError, ValueError, RecursionError):
            continue                            # not importable; not a reader
        rows = _RowLocals(tree)

        rel = p.relative_to(root).as_posix()

        def hit(node):
            out.append(f"{rel}:{node.lineno}: {ast.unparse(node)[:120]}")

        for node in ast.walk(tree):
            # (a) the rule MAPPED across a row.
            for elt, source in _mapping_sites(node):
                if rows.source(source) and _blessed_calls(elt, rows.blessed):
                    hit(node)
            # (b) a loop over a row that accumulates a blessed fold.
            if isinstance(node, (ast.For, ast.AsyncFor)) and rows.source(node.iter):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call) \
                            and isinstance(sub.func, ast.Attribute) \
                            and sub.func.attr in {"append", "add", "update",
                                                  "insert", "setdefault"} \
                            and sub.args:
                        if any(_blessed_calls(a, rows.blessed) for a in sub.args):
                            hit(node)
                    elif isinstance(sub, ast.AugAssign) \
                            and _blessed_calls(sub.value, rows.blessed):
                        hit(node)
                    elif isinstance(sub, ast.Assign) and any(
                            isinstance(t, ast.Subscript) for t in sub.targets):
                        if _blessed_calls(sub.value, rows.blessed) or any(
                                _blessed_calls(t.slice, rows.blessed)
                                for t in sub.targets
                                if isinstance(t, ast.Subscript)):
                            hit(node)
            # (c) the rule applied to ONE CELL of a row — the scalar half.
            if isinstance(node, ast.Call) and len(node.args) == 1:
                name = (node.func.id if isinstance(node.func, ast.Name)
                        else node.func.attr if isinstance(node.func, ast.Attribute)
                        else None)
                if name in rows.rule and rows.cell(node.args[0]):
                    hit(node)
    return sorted(set(out))
