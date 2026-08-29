"""The one-header-rule check. TASK-050 round 8 — **over a symbol, not a shape.**

Rounds 2 through 7 each shipped a better DETECTOR of a second header rule and
each was defeated within one review:

    round 2  three copies in files that never imported `squash`
    round 3  a SUBDIRECTORY was invisible; the pattern matched a SPELLING
    round 4  the `[` had to sit right after the `=`
    round 5  it knew `split_row(` and not the private splitter `.split("|")`
    round 5's REVIEW  nine planted spellings, FIVE escaped both nets
    round 6  the regex became an AST walk
    round 7's REVIEW  the walk's GATE is still an eleven-name allowlist of
             variable names: `[squash(c) for c in prev_cells]` at
             viewer/parsers.py could be reverted to the historical rule,
             silently drop a KR out of a user's OKR, and leave 2882 tests green

**The seventh failure is why this file is no longer the deliverable.** The row
was answered by `viewer/tables.py § header_index` — one function that folds a
header cell, and nothing else in the repository that does. You do not stop two
implementations drifting apart by getting better at spotting the second one;
you stop it by having one. That is the move `ADR-007` already made for stores.

So the check this file performs is now **two nets, and they are not the same
kind of thing**:

## Net 1 — the symbol. `offenders_by_symbol()`

*Nothing outside `header_index` maps `squash` (or its `norm` alias) across a
row's cells.* This is the drift half, and it is the one the design makes
decidable: after round 8 the tree contains **zero** such sites, so the check is
an equality against zero over one symbol. It cannot fire on a value normalizer,
because a value normalizer folds a value and not a row — that is not an
exception carved out for it, it is what the two words mean.

## Net 2 — the shape. `offenders()`

*A collection built by mapping over a row's cells, whose element expression
case-folds, must fold through `squash`.* This is the second-rule half: code
that folds a header WITHOUT the blessed function. It is a shape check and
therefore defeasible — seven rounds of evidence say so — and it is kept
because a defeasible net over a surface this small still costs nothing to run.
**It is not what closes the row**; `tests/test_header_index_is_the_only_fold.py`
is, because it watches the real readers parse a real decorated document and
asks who called `squash`.

What changed inside net 2 for round 8: a row is now recognised by **local
dataflow from `split_row`**, not by its variable's name. `parts = split_row(l)`
on one line and the comprehension on the next — round 7's P21, "the most
ordinary spelling there is" — is caught, as are `cells[1:]`, `cs = cells`, a
parameter this file passes a row to, a `lambda` folder and two levels of local
indirection. `ROW_NAMES` survives ONLY as a fallback for a bare parameter with
no local provenance, and **it has not been extended** — extending it is what
rounds 5 through 7 did.

## What net 2 still cannot see, stated as assertions elsewhere

`tests/test_header_rule_harness.py` plants each of these and asserts it
escapes, so the list goes red rather than rotting:

- a folding helper defined in ANOTHER module (cross-module dataflow is a type
  checker's job);
- a fold over an iterable with no local provenance and a name this file has
  never heard of — `def read(stuff): return [c.lower() for c in stuff]`. There
  is no information in that function to distinguish it from a value normalizer,
  and **that is the proof that no static net closes this row**, which is why
  the round shipped a function instead of a net.
"""

from __future__ import annotations

import ast
import warnings
from pathlib import Path

#: The one rule, its `perry-lint` alias, and the one function allowed to apply
#: it to a header row.
BLESSED = frozenset({"squash", "norm", "header_index", "header_keys"})

#: Case-folding operations. `.title()`/`.upper()` are not here: neither
#: resolves a header in this repo, and a guard that reports code nobody wrote
#: is a guard nobody reads. `.translate()` is, because round 7's reviewer
#: planted it.
FOLDING_METHODS = frozenset({"lower", "casefold", "translate"})

#: **Not extended since round 6, deliberately.** After the conversion this is
#: a fallback for a bare parameter with no local provenance, not the gate the
#: check runs on — round 7 failed the row precisely because this was the gate.
ROW_NAMES = frozenset({
    "cells", "cols", "columns", "header", "headers", "hdr", "hdrs",
    "row", "cell", "header_cells", "raw_header"})

#: Builtins that wrap an iterable without changing what its elements ARE.
ITERABLE_WRAPPERS = frozenset({
    "enumerate", "reversed", "list", "tuple", "sorted", "set", "iter",
    "zip", "filter"})

#: Calls that PRODUCE a row's cells. **Two entries, and they are the two
#: functions this repository is allowed to have**: `split_row` is the only row
#: splitter (criterion 3) and `header_index` is the only header fold. Anything
#: else that yields a row — `bin/perry-state § cells_of`, `Board.section_table`
#: — is resolved by `_RowLocals` from what it RETURNS, not by being listed
#: here. Round 7's review named `cells_of` as an escape hatch for exactly that
#: reason: it was safe only because its result happened to be called `cells`.
ROW_PRODUCERS = frozenset({"split_row", "header_index"})


def is_python(p: Path) -> bool:
    """A Python source file, by suffix or shebang — not by extension list."""
    if p.suffix == ".py":
        return True
    if p.suffix:
        return False
    try:
        head = p.read_text(errors="replace").split("\n", 1)[0]
    except OSError:
        return False
    return "python" in head


def readers_under(root) -> list[Path]:
    """Every Python reader under `root`, minus the file that DEFINES the rule."""
    root = Path(root)
    return sorted(
        p for d in ("bin", "viewer")
        for p in (root / d).rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and p != root / "viewer" / "tables.py"
        and is_python(p))


def _string_constants(tree: ast.AST) -> dict[str, str]:
    """Module-level `NAME = "literal"`, so a constant splitter is resolvable."""
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = node.value.value
        if isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str) \
                and isinstance(node.target, ast.Name):
            out[node.target.id] = node.value.value
        # `PIPE = {"sep": "|"}["sep"]` and `class C: SEP = "|"` — a constant
        # reached through one attribute or one subscript is still a constant.
        if isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, ast.Assign) \
                        and isinstance(sub.value, ast.Constant) \
                        and isinstance(sub.value.value, str):
                    for t in sub.targets:
                        if isinstance(t, ast.Name):
                            out[t.id] = sub.value.value
    return out


def _pipe_literals(tree: ast.AST) -> bool:
    """Whether this module writes a `|` string literal anywhere at all."""
    return any(isinstance(n, ast.Constant) and isinstance(n.value, str)
               and "|" in n.value for n in ast.walk(tree))


def _splits_on_pipe(node: ast.AST, consts: dict[str, str], tree=None) -> bool:
    """`x.split("|")`, `re.split(r"\\|", x)`, or either via a constant.

    A separator reached through an attribute or a subscript (`C.SEP`,
    `SEPS["row"]`) is resolved when the module contains a `|` literal at all —
    round 7's reviewer escaped with both, and resolving the exact container is
    dataflow analysis where a module-level existence test is enough.
    """
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Attribute) and node.func.attr in {"split", "findall"}:
        pass
    else:
        return False
    regex = isinstance(node.func, ast.Attribute) \
        and isinstance(node.func.value, ast.Name) and node.func.value.id == "re"

    def is_pipe(text: str) -> bool:
        # In a REGEX, a bare `|` is alternation and says nothing about rows —
        # `re.split(r"\n(?=## (?:Objective|目标))", text)` is a section
        # splitter, and flagging it is the false positive criterion 4 names.
        # A row splitter written as a regex has to ESCAPE the pipe.
        return ("\\|" in text or "[|]" in text) if regex else ("|" in text)

    for a in list(node.args) + [k.value for k in node.keywords]:
        if isinstance(a, ast.Constant) and isinstance(a.value, str) and is_pipe(a.value):
            return True
        if isinstance(a, ast.Name) and is_pipe(consts.get(a.id, "")):
            return True
        if isinstance(a, (ast.Attribute, ast.Subscript)) and tree is not None \
                and _pipe_literals(tree):
            return True
    return False


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
    """Names that hold a row's cells, by **local dataflow**, PER FUNCTION.

    Round 7's finding was that the gate in front of an otherwise genuine AST
    walk was an eleven-name allowlist: `prev_cells` and `ihdr` were not in it,
    so two live header resolutions and 21 of 25 planted readers walked past.
    This replaces the gate with provenance — a name is a row because something
    in this function put a row in it — and runs to a fixpoint so two levels of
    local indirection do not escape.

    **Scoped per function**, because a module-wide taint set makes one
    `cells = split_row(l)` colour every `cells` in a 3000-line file and a
    check that reports correct code is the failure mode criterion 4 names.
    File-local by construction: cross-module dataflow is a type checker's job.
    """

    def __init__(self, tree: ast.AST, consts: dict[str, str]) -> None:
        self.tree, self.consts = tree, consts
        self.funcs = [n for n in ast.walk(tree)
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        self.scope: dict[object, set[str]] = {None: set()}
        for f in self.funcs:
            self.scope[f] = set()
        self.owner: dict[object, object] = {}
        # INNERMOST wins. `ast.walk` is breadth-first, so a nested function
        # comes after the one that contains it and overwrites its claim —
        # `bin/perry-state § parse_tracks` defines `cells_of` inside itself,
        # and attributing that helper's `return` to its enclosing function
        # said `parse_tracks` returns a row and `cells_of` returns nothing.
        for f in self.funcs:
            for sub in ast.walk(f):
                self.owner[sub] = f
        #: `{function name: {tuple positions that are a row, -1 for a bare
        #: return}}`. `_, ihdr = self.section_table("Intake")` is how
        #: `bin/perry-task` gets a header row, and round 7 measured BOTH of
        #: its `ihdr` sites as escaping — because the walk asked what the
        #: variable was called. This asks what the function returned.
        self.returns: dict[str, set[int]] = {}
        self._here: object = None
        for _ in range(6):                      # fixpoint; 6 is far past need
            before = {k: set(v) for k, v in self.scope.items()}
            self._pass()
            if all(self.scope[k] == before[k] for k in self.scope):
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
        for f in list(self.scope):
            self._here = f
            body = f if f is not None else self.tree
            for node in ast.walk(body):
                if self.of(node) is not (f if f is not None else None):
                    continue
                if isinstance(node, ast.Assign):
                    targets, value = node.targets, node.value
                elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
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
            fn = next((f for f in self.funcs if f.name == call.func.id), None)
            if fn is None:
                continue
            params = [a.arg for a in fn.args.args]
            caller = self.of(call)
            for i, arg in enumerate(call.args):
                if i < len(params) and self.source(arg, caller):
                    self.scope[fn].add(params[i])

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
        if _splits_on_pipe(node, self.consts, self.tree):
            return True
        if -1 in self._returns_of(node):
            return True                    # a file-local function that returns one
        if isinstance(node, ast.Name):
            return node.id in names or node.id in ROW_NAMES
        # `cells[1:]`, `cells[0]`, `table["header"]` — a slice or an item of a
        # row is a row cell, and `["header"]` names one by hand.
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Constant) \
                    and node.slice.value in ("header", "headers", "hdr"):
                return True
            return self.source(node.value, scope)
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


def _folding_calls(node: ast.AST) -> list[str]:
    """Every fold-ish call in this expression, named.

    `c.strip().lower()` -> ['strip', 'lower'];  `squash(c)` -> ['squash'];
    `_norm(c)` -> ['_norm'] (resolved by the caller against `_local_folders`).
    A bare `ast.Name` counts only where it is being USED AS the mapping
    function — `map(str.lower, cells)`, `map(_norm, cells)` — which is what
    `_mapping_sites` hands over as the element expression.
    """
    found: list[str] = []
    if isinstance(node, ast.Name):
        found.append(node.id)                    # `map(_norm, cells)`
    if isinstance(node, ast.Attribute):
        found.append(node.attr)                  # `map(str.lower, cells)`
    if isinstance(node, ast.Lambda):
        found.extend(_folding_calls(node.body))
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            if isinstance(sub.func, ast.Attribute):
                found.append(sub.func.attr)
            elif isinstance(sub.func, ast.Name):
                found.append(sub.func.id)
            for kw in sub.keywords:              # `functools.partial(_norm, ...)`
                pass
        elif isinstance(sub, ast.Attribute) and sub.attr in FOLDING_METHODS:
            found.append(sub.attr)
    return found


def _local_folders(tree: ast.AST) -> set[str]:
    """File-local callables that case-fold — the `_norm` refactor, to fixpoint.

    Functions, `lambda`s bound to a name, and one bound to `functools.partial`
    of either. Round 7's reviewer escaped through the lambda and through two
    levels of indirection, so this iterates rather than resolving one level.
    """
    named: dict[str, ast.AST] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            named[node.name] = node
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            named[node.targets[0].id] = node.value
    out: set[str] = set()
    for _ in range(6):
        before = set(out)
        for name, body in named.items():
            if name in out:
                continue
            for sub in ast.walk(body):
                folds = isinstance(sub, ast.Attribute) and sub.attr in FOLDING_METHODS
                calls = (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
                         and sub.func.id in out and sub.func.id != name)
                # `functools.partial(_norm, x)` / `partial(_norm, x)`
                wraps = (isinstance(sub, ast.Call)
                         and any(isinstance(a, ast.Name) and a.id in out
                                 for a in sub.args)
                         and ((isinstance(sub.func, ast.Attribute)
                               and sub.func.attr == "partial")
                              or (isinstance(sub.func, ast.Name)
                                  and sub.func.id == "partial")))
                if folds or calls or wraps:
                    out.add(name)
                    break
        if out == before:
            break
    return out


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


def _scan(root, want_blessed: bool) -> list[str]:
    """The two nets, which differ only in which fold they are looking for."""
    out: list[str] = []
    for p in readers_under(root):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                warnings.simplefilter("ignore", SyntaxWarning)
                tree = ast.parse(p.read_text(errors="replace"))
        except SyntaxError:
            continue                            # not importable; not a reader
        consts = _string_constants(tree)
        rows = _RowLocals(tree, consts)
        local_folders = _local_folders(tree)

        def flag(node, elt, source):
            if not rows.source(source):
                return
            names = _folding_calls(elt)
            blessed = [n for n in names if n in BLESSED]
            folds = [n for n in names
                     if n in FOLDING_METHODS or n in local_folders]
            if want_blessed:
                # Net 1: the BLESSED rule, mapped across a row outside
                # `header_index`. One symbol, no shape.
                if not blessed:
                    return
            else:
                # Net 2: a fold that is not the blessed rule.
                if not folds or blessed:
                    return
            out.append(f"{p.name}:{node.lineno}: {ast.unparse(node)[:120]}")

        for node in ast.walk(tree):
            for elt, source in _mapping_sites(node):
                flag(node, elt, source)
            if isinstance(node, (ast.For, ast.AsyncFor)) and rows.source(node.iter):
                # A loop that accumulates a folded cell — `.append`, `.add`,
                # `out += [..]`, `d[..] = ..`. Round 7's reviewer escaped
                # through every one of those but `.append`.
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call) \
                            and isinstance(sub.func, ast.Attribute) \
                            and sub.func.attr in {"append", "add", "update",
                                                  "insert", "setdefault"} \
                            and sub.args:
                        for a in sub.args:
                            flag(node, a, node.iter)
                    elif isinstance(sub, ast.AugAssign):
                        flag(node, sub.value, node.iter)
                    elif isinstance(sub, ast.Assign) and any(
                            isinstance(t, ast.Subscript) for t in sub.targets):
                        for t in sub.targets:
                            if isinstance(t, ast.Subscript):
                                flag(node, t.slice, node.iter)
                        flag(node, sub.value, node.iter)
    return sorted(set(out))


def offenders(root) -> list[str]:
    """Net 2 — every site that folds a row's cells by a rule other than
    `squash`. `path:line: source`, sorted, one entry per site."""
    return _scan(root, want_blessed=False)


def offenders_by_symbol(root) -> list[str]:
    """Net 1 — every site outside `header_index` that maps `squash`/`norm`
    across a row's cells. **Zero after TASK-050 round 8.**"""
    return _scan(root, want_blessed=True)
