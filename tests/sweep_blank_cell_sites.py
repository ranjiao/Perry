"""Derive every site in `bin/` and `viewer/` that decides a cell means nothing.

**TASK-431, and this file is the row's actual deliverable.** `schema §
i18n.blank_cell` exists because there were three lists in `bin/` with three
different contents. The declaration landed; two of the three lists stayed, and
a fourth (`bin/perry-state § missing_defaults`) had appeared that nobody had
counted. The pattern is not "there is a list in `perry-lint`" — it is "a tool
that needs this answer writes its own", and it recurs. So the guard is a
DERIVATION, not a list of the sites that were wrong this time: a test that
enumerates the known sites has exactly the shape of the thing being removed
and goes stale the same way.

**How it works.** Read the declared spellings out of the schema, parse every
Python source under `bin/` and `viewer/` with `ast`, find every string
constant that is one of them, and keep the ones the code TESTS AGAINST rather
than PRINTS. Direction is the whole trick: at `70458893` there were 222 such
literals in the tree and 175 of them were output — f-strings, `x or "—"`
display defaults, `.split("-")` arguments. Grep cannot tell those apart and
this can.

**What it does NOT see, stated so the next reader does not trust it too far.**
It enumerates literals and the names they are bound to, WITHIN a module. A
reader in another module that imports the name sees no literal at all:
`bin/perry-knowledge` read `perry-lint`'s set through a `SourceFileLoader` at
five sites and this sweep was blind to every one (the test suite found them).
`cross_module_reads` below closes that hole for attribute access. It remains
blind to a set built at runtime, read from a file, or assembled by string
arithmetic — none of which exists in the tree today.

That residual is acceptable for one reason: a cross-module reader cannot exist
unless someone first DEFINES a container, and a container is caught here at
its definition site. The guard's job is to make a fourth list impossible to
add quietly, and a list is a literal.
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
SCHEMA = PERRY_HOME / "schema" / "state-schema.json"

_CONTAINERS = (ast.Set, ast.List, ast.Tuple, ast.Dict)
_EQ_OPS = (ast.In, ast.NotIn, ast.Eq, ast.NotEq)


def blank_key(value: str) -> str:
    """`lib._blank_key`, re-derived here ON PURPOSE.

    This is the one place in the row where restating the rule is right: the
    sweep must keep working against a tree in which somebody has broken
    `lib`, and a guard that imports the thing it is guarding cannot report
    that it is gone.
    """
    return (value or "").strip().strip("*`~ ").strip().lower() \
                        .rstrip(".。!！?？").strip()


def declared_spellings() -> set[str]:
    """The blank-key of every spelling in `schema § i18n.blank_cell`."""
    blank = (json.loads(SCHEMA.read_text(encoding="utf-8"))
             .get("i18n", {}) or {}).get("blank_cell") or {}
    out = {blank_key(str(v))
           for k, vals in blank.items()
           if k != "note" and isinstance(vals, list)
           for v in vals}
    out.discard("")
    return out


def sources() -> list[Path]:
    """Every Python source under `bin/` and `viewer/`.

    Extensionless scripts are found by SHEBANG, not by a filename list —
    `bin/perry-lint`, `bin/perry-state` and `bin/perry-task` all have no
    suffix, and a sweep that globbed `*.py` would have reported a clean tree
    while missing the three sites the row was filed about.
    """
    out = []
    for base in ("bin", "viewer"):
        for dirpath, _dirs, files in os.walk(PERRY_HOME / base):
            if "__pycache__" in dirpath:
                continue
            for name in sorted(files):
                path = Path(dirpath) / name
                if name.endswith(".py"):
                    out.append(path)
                elif "." not in name:
                    try:
                        with open(path, "rb") as handle:
                            if b"python" in handle.readline():
                                out.append(path)
                    except OSError:
                        pass
    return sorted(out)


def _parents_and_scopes(tree: ast.AST):
    parent, scope = {}, {}

    def walk(node, fn):
        for child in ast.iter_child_nodes(node):
            parent[child] = node
            name = (child.name
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    else fn)
            scope[child] = name
            walk(child, name)

    walk(tree, None)
    return parent, scope


def read_sites() -> dict[tuple[str, str, tuple[str, ...]], int]:
    """Every site that TESTS a value against a declared blank spelling.

    Keyed by `(relative path, enclosing function, the spellings involved)` and
    valued by how many occurrences that key has.

    **Keyed by function and not by line, deliberately.** TASK-431 broke
    `tests/test_handed_back_root.py § NO_ROOT_TO_GIVE` — an allowlist keyed by
    line number — merely by adding comments above the line it named. An
    allowlist that a comment can invalidate is not an allowlist. The spellings
    ride in the key so that a NEW list inside an already-exempt function still
    changes it.
    """
    declared = declared_spellings()
    found: dict[tuple[str, str, tuple[str, ...]], int] = {}

    for path in sources():
        rel = str(path.relative_to(PERRY_HOME))
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parent, scope = _parents_and_scopes(tree)

        # names bound to a container that holds a declared spelling
        bound: dict[str, set[str]] = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            spellings = {c.value for c in ast.walk(node.value)
                         if isinstance(c, ast.Constant)
                         and isinstance(c.value, str)
                         and blank_key(c.value) in declared}
            if spellings and isinstance(node.value, _CONTAINERS + (ast.BinOp,)):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        bound.setdefault(target.id, set()).update(spellings)

        def add(fn, spellings):
            key = (rel, fn or "<module>", tuple(sorted(spellings)))
            found[key] = found.get(key, 0) + 1

        # a Compare that tests against one of those names
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Compare)
                    and any(isinstance(o, _EQ_OPS) for o in node.ops)):
                continue
            for comparator in node.comparators:
                for inner in ast.walk(comparator):
                    if isinstance(inner, ast.Name) and inner.id in bound:
                        add(scope.get(node), bound[inner.id])

        # a literal on the tested side of a Compare, directly or in a container
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and blank_key(node.value) in declared):
                continue
            cursor, hops = node, 0
            while parent.get(cursor) is not None and hops < 6:
                above = parent[cursor]
                if isinstance(above, ast.Compare):
                    if (cursor in above.comparators
                            and any(isinstance(o, _EQ_OPS) for o in above.ops)):
                        spellings = {c.value for c in ast.walk(cursor)
                                     if isinstance(c, ast.Constant)
                                     and isinstance(c.value, str)
                                     and blank_key(c.value) in declared}
                        add(scope.get(node), spellings)
                    break
                if isinstance(above, _CONTAINERS):
                    cursor, hops = above, hops + 1
                    continue
                break
    return found


def cross_module_reads(names: set[str]) -> list[str]:
    """`<module>.<NAME>` reads of a blank-set constant from another module.

    The hole that `bin/perry-knowledge` fell through: it binds `bin/perry-lint`
    as `L` and asked `src in L.UNDECLARED_CELL` at five sites, with no
    blank-cell literal anywhere in the file.
    """
    out = []
    for path in sources():
        rel = str(path.relative_to(PERRY_HOME))
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in names:
                out.append(f"{rel}:{node.lineno} …{node.attr}")
    return out
