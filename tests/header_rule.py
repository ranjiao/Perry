"""The one-header-rule check, as an AST walk. TASK-050 round 6.

**A regex over source lines cannot express this category, and five rounds of
trying is the evidence.** Each round widened `SECOND_RULE` by one alternation
and the next reviewer walked past it:

    round 2  three copies in files that never imported `squash`
    round 3  a SUBDIRECTORY was invisible; the pattern matched a SPELLING, so
             `for h in header` walked past `for c in cells`
    round 4  the `[` had to sit right after the `=`, so the parenthesised
             comprehension — the live shape in viewer/parsers.py — was green
    round 5  it knew `split_row(` and not the private splitter `.split("|")`
    round 5's REVIEW  nine planted spellings, FIVE escaped both nets:
             `.casefold()` in a non-splitting helper · `.casefold()` + a
             splitter in a file that already contains the token "squash" ·
             a `PIPE = "\\|"` constant splitter · `re.split(r"\\|", line)` ·
             a plain `for` loop with `.append()`

Regexes match spellings. The category is a SHAPE, so this asks the parser.

## The rule, in one sentence

**A collection built by mapping over a row's cells, whose element expression
case-folds, must fold through `viewer/tables.py § squash`.**

Every clause is load-bearing:

- *a collection built by mapping* — list/set/dict comprehensions, generator
  expressions, `map()`, and a `for` loop that `.append()`s. Round 5's review
  escaped through the last two.
- *over a row's cells* — this is the header/value line, and it is the whole
  judgement in this module. The tree has **30** case-folding comprehensions and
  not one is a header resolution: they lowercase directory names, aliases,
  spellings, modes and stages. Those normalize what a project WROTE, not which
  column it wrote it in, and a check that flags them is a check people switch
  off. `tests/test_one_header_rule.py § TestValueNormalizersAreNotFlagged`
  holds that line with the live count.
- *whose element expression case-folds* — `bin/perry-diagnose:1820` reads
  `[c.strip("*` ") for c in split_row(s)]`, which is a row-cell source and is
  CORRECT: it keeps the values verbatim. Folding is what needs the one rule.
- *must fold through `squash`* — including indirectly. A local helper that
  folds is resolved one level, because "factor the old rule into `_norm` and
  call that" is the natural refactor of the exact defect this row exists for
  (round 5's review, case G).

## What this deliberately still cannot see

Enumerated, not hidden — `tests/test_header_rule_harness.py` asserts each of
these is uncaught, so the list is a claim that can go red rather than a hope:

- a helper defined in ANOTHER module. Resolution is one level and file-local;
  cross-module dataflow is a type checker's job, not a guard's.
- a row-cell source this file cannot recognise — an iterable handed in as a
  parameter with a name outside `ROW_NAMES` and never split locally.

Both are narrower than what round 5 shipped, and both are stated rather than
argued away. The previous round claimed its blind spots were "bounded" by a
complement test that turned out to be a whole-file substring check every
reader already satisfied; there is no complement test any more, because this
walk subsumes it.

Imported by `tests/test_one_header_rule.py` (the guard) and
`tests/test_header_rule_harness.py` (the planting harness), so both nets are
ONE implementation pointed at different trees — round 5's review found the
harness could not point the complement at a copy, precisely because there were
two.
"""

from __future__ import annotations

import ast
import warnings
from pathlib import Path

#: The one rule, and its `perry-lint` alias.
BLESSED = frozenset({"squash", "norm"})

#: Case-folding method calls. `.title()` and `.upper()` are not here: neither
#: is used to resolve a header in this repo, and a guard that reports code
#: nobody wrote is a guard nobody reads.
FOLDING_METHODS = frozenset({"lower", "casefold"})

#: Names that ARE a row's cells. The header/value line, drawn where every
#: earlier round of this row drew it — what changed is that the shape around
#: them is now parsed rather than pattern-matched.
ROW_NAMES = frozenset({
    "cells", "cols", "columns", "header", "headers", "hdr", "hdrs",
    "row", "cell", "header_cells", "raw_header"})

#: Builtins that wrap an iterable without changing what its elements ARE.
#: `enumerate` is the load-bearing one: building a header INDEX is
#: `{... for i, c in enumerate(cells)}`, which is the single most likely shape
#: for the construct this whole rule exists to police.
ITERABLE_WRAPPERS = frozenset({
    "enumerate", "reversed", "list", "tuple", "sorted", "set", "iter"})


def is_python(p: Path) -> bool:
    """A Python source file, by suffix or shebang — not by extension list.

    Unchanged from the enumeration this replaces: asking what the file IS
    avoids a suffix blacklist the next asset type would extend. It exists
    because widening the walk once flagged a bash script and a JS asset.
    """
    if p.suffix == ".py":
        return True
    if p.suffix:
        return False
    try:
        return "python" in p.read_text(errors="replace").split("\n", 1)[0]
    except OSError:
        return False


def readers_under(root) -> list[Path]:
    """Every Python reader under `root`, minus the file that DEFINES the rule.

    Parameterised on `root` so the harness can point this at a planted COPY.
    Walks the tree rather than `iterdir()`ing it: a subdirectory was invisible
    for two rounds, and `bin/lib/` is a directory TASK-065 exists to create.
    """
    root = Path(root)
    return sorted(
        p for d in ("bin", "viewer")
        for p in (root / d).rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and p != root / "viewer" / "tables.py"
        and is_python(p))


def _string_constants(tree: ast.AST) -> dict[str, str]:
    """Module-level `NAME = "literal"`, so a constant splitter is resolvable.

    Round 5's review escaped with `PIPE = "\\|"` and `line.split(PIPE)`. One
    file-local lookup closes it; anything more is dataflow analysis.
    """
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = node.value.value
    return out


def _splits_on_pipe(node: ast.AST, consts: dict[str, str]) -> bool:
    """`x.split("|")`, `re.split(r"\\|", x)`, or either via a constant."""
    if not isinstance(node, ast.Call):
        return False
    args = list(node.args)
    if isinstance(node.func, ast.Attribute) and node.func.attr == "split":
        pass                                    # `x.split(<sep>)`
    elif isinstance(node.func, ast.Attribute) and node.func.attr in {"split", "findall"} \
            and isinstance(node.func.value, ast.Name) and node.func.value.id == "re":
        pass                                    # `re.split(<pat>, x)`
    else:
        return False
    for a in args:
        if isinstance(a, ast.Constant) and isinstance(a.value, str) and "|" in a.value:
            return True
        if isinstance(a, ast.Name) and "|" in consts.get(a.id, ""):
            return True
    return False


def is_row_cell_source(node: ast.AST, consts: dict[str, str]) -> bool:
    """Does this expression yield a ROW'S CELLS?

    Three ways, and the third is the one every earlier round relied on alone:
    a call to `split_row(...)`, any split on a pipe (literal or constant), or
    a name that IS a row's cells.
    """
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id == "split_row":
        return True
    if _splits_on_pipe(node, consts):
        return True
    if isinstance(node, ast.Name) and node.id in ROW_NAMES:
        return True
    # `enumerate(cells)`, `list(split_row(s))`, `sorted(cols)` — a wrapper
    # that preserves the elements does not stop them being a row's cells.
    # Round 5's review escaped here: its dict-comprehension case iterated
    # `enumerate(cells)`, and `enumerate` is exactly how a header INDEX gets
    # built, which is the construct this rule exists for.
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id in ITERABLE_WRAPPERS:
        return any(is_row_cell_source(a, consts) for a in node.args)
    # `[... for c in [x.strip() for x in split_row(line)]]` — one unwrap, so a
    # comprehension over an already-split row is still a row-cell source.
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
        return any(is_row_cell_source(g.iter, consts) for g in node.generators)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr in {"strip", "split"} :
        return is_row_cell_source(node.func.value, consts)
    return False


def _folding_calls(node: ast.AST) -> list[str]:
    """Every case-folding call in this expression, named.

    `c.strip().lower()` -> ['lower'];  `squash(c)` -> ['squash'];
    `_norm(c)` -> ['_norm'] (resolved by the caller, one level).
    """
    found: list[str] = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            if isinstance(sub.func, ast.Attribute) and sub.func.attr in FOLDING_METHODS:
                found.append(sub.func.attr)
            elif isinstance(sub.func, ast.Name):
                found.append(sub.func.id)
            elif isinstance(sub.func, ast.Attribute):
                found.append(sub.func.attr)
        elif isinstance(sub, ast.Attribute) and sub.attr in FOLDING_METHODS:
            found.append(sub.attr)              # `map(str.lower, cells)`
    return found


def _local_folders(tree: ast.AST) -> set[str]:
    """File-local functions that case-fold — the `_norm` refactor, one level."""
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Attribute) and sub.attr in FOLDING_METHODS:
                    out.add(node.name)
                    break
    return out


def _element_exprs(node: ast.AST):
    """The expression(s) a mapping construct applies per element, + its source."""
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
        for g in node.generators:
            yield node.elt, g.iter
    elif isinstance(node, ast.DictComp):
        for g in node.generators:
            yield node.key, g.iter
            yield node.value, g.iter
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id == "map" and len(node.args) >= 2:
        yield node.args[0], node.args[1]


def offenders(root) -> list[str]:
    """Every site that folds a row's cells by a rule other than `squash`.

    Returns `path:line: source`, sorted, one entry per site.
    """
    out: list[str] = []
    for p in readers_under(root):
        try:
            with warnings.catch_warnings():
                # Several shipped files carry regex strings that are not raw
                # literals; compiling them emits DeprecationWarning. That is a
                # property of the file being READ, not of this check, and
                # letting it through would make every run of the guard print
                # warnings about code it is not reporting on.
                warnings.simplefilter("ignore", DeprecationWarning)
                warnings.simplefilter("ignore", SyntaxWarning)
                tree = ast.parse(p.read_text(errors="replace"))
        except SyntaxError:
            continue                            # not importable; not a reader
        consts = _string_constants(tree)
        local_folders = _local_folders(tree)

        def flag(node, elt, source):
            if not is_row_cell_source(source, consts):
                return
            names = _folding_calls(elt)
            folds = [n for n in names
                     if n in FOLDING_METHODS or n in local_folders]
            if not folds:
                return                          # verbatim cells: not this rule
            if any(n in BLESSED for n in names):
                return                          # reaches the one rule
            out.append(f"{p.name}:{node.lineno}: "
                       f"{ast.unparse(node)[:120]}")

        for node in ast.walk(tree):
            for elt, source in _element_exprs(node):
                flag(node, elt, source)
            # A plain `for` loop that appends a folded cell — round 5's case H.
            if isinstance(node, ast.For) and is_row_cell_source(node.iter, consts):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call) \
                            and isinstance(sub.func, ast.Attribute) \
                            and sub.func.attr == "append" and sub.args:
                        flag(node, sub.args[0], node.iter)
    return sorted(set(out))
