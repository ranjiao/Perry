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
        for _ in range(6):                      # fixpoint; 6 is far past need
            before = ({k: set(v) for k, v in self.scope.items()},
                      {k: set(v) for k, v in self.cells.items()})
            self._pass()
            if all(self.scope[k] == before[0][k] for k in self.scope) \
                    and all(self.cells[k] == before[1][k] for k in self.cells):
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
                if isinstance(node, ast.Assign):
                    targets, value = node.targets, node.value
                elif isinstance(node, (ast.AnnAssign, ast.AugAssign,
                                       ast.NamedExpr)):
                    targets, value = [node.target], node.value
                else:
                    continue
                if value is None:
                    continue
                # `_, ihdr = board.section_table("Intake")` — a tuple unpack of
                # a call whose Nth element is a row.
                positions = self._returns_of(value)
                if positions and len(targets) == 1 \
                        and isinstance(targets[0], (ast.Tuple, ast.List)):
                    for i, t in enumerate(targets[0].elts):
                        if i in positions and isinstance(t, ast.Name):
                            self.scope[f].add(t.id)
                    continue
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
        """Does this expression yield a ROW'S CELLS, in `scope`?"""
        if scope is ...:
            scope = self.of(node)
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
