"""Where the `startable` rule is stated in `bin/`. There must be exactly one place.

**TASK-148, and the measurement that produced it.** `bin/perry-task` stated the
rule twice, ~200 lines apart — once in `_cmd_list_from_board` and once in
`cmd_list` — and both are reachable. TASK-141 had to change the rule and
discovered it had to change it **twice**. That is the two-readers-of-one-rule
failure `schema/task-list-contract.md` warns about in its own prose, inside the
tool the contract describes.

**Why this is an AST scan and not a grep.** The two copies were not textually
alike. One read

    waiting = {"blocked", "review"}
    t["startable"] = bool(t["open"] and not t["blocked_by"] and …)

and the other

    task["startable"] = bool(task["open"] and not task["blocked_by"]
                             and (… or task["status"] not in {"blocked", "review"}))

— same rule, different variable names, the set inlined on one side and named on
the other. A regex for either spelling would have missed the other, which is
precisely how the second copy survived long enough to be found by a row that
tripped over it. `tests/test_one_primitive.py` reached the same judgement for
`bin/`'s primitives: ask what a file *does*, never what it named it.

## The two shapes

- **the assignment.** Storing a *computed* value into `["startable"]` or
  `["blocked_stale"]`. A constant — `"startable": False` in a row template — is
  not the rule; it is the blank that the rule later fills, and both list paths
  legitimately carry one.
- **the waiting set.** A collection whose members are exactly `blocked` and
  `review` — the statuses that mean somebody else has the ball. Written as a
  set, a tuple, a list or a `frozenset(...)`, all of which are the same claim.
  A *wider* set that merely contains them (`perry-state`'s four open states) is
  a different claim and is not matched.

## What is asserted

Not "at most one". **Exactly one**, counted by the enclosing function, so the
check fails in both directions: a second copy anywhere under `bin/` reddens it,
and so does the rule disappearing — a guard that would pass against a spelling
that no longer exists is ceremony, which is the failure this suite keeps
finding in its own checks.

The home is not hardcoded. `bin/lib/__init__.py § resolve_startability` is
where it lives today and the report prints that, but this module holds no list
of blessed files: moving the rule somewhere else stays green, and copying it
does not.

Run:

    python3 tests/one_startable_rule.py             # where the rule lives
    python3 tests/one_startable_rule.py --json      # the same, machine-readable
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import sys
from typing import NamedTuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"

#: The two derived fields the rule decides, and the only two it may write.
RULE_FIELDS = ("startable", "blocked_stale")

#: The statuses that mean somebody else has the ball. Exactly these two — see
#: the module docstring on why a superset is a different claim.
WAITING = frozenset(("blocked", "review"))


class Finding(NamedTuple):
    """One place a shape of the rule was found, and where it sits."""
    file: str
    line: int
    function: str
    shape: str
    source: str

    def where(self) -> str:
        return f"{self.file}:{self.line}"

    def home(self) -> str:
        """The (file, function) a copy would have to share to be the same copy."""
        return f"{self.file} § {self.function}"


def is_python(path: pathlib.Path) -> bool:
    """A Python source file, by suffix or by shebang.

    `bin/` holds bash (`perry-viewer`), Python with a `.py` suffix
    (`perry_store.py`) and Python with none at all (`perry-task`) — the file
    this whole check is about. The same judgement `tests/test_one_primitive.py`
    had to reach, and for the same directory.
    """
    if path.suffix == ".py":
        return True
    if path.suffix:
        return False
    try:
        return "python" in path.read_text(errors="replace").split("\n", 1)[0]
    except OSError:
        return False


def sources(root: pathlib.Path = BIN):
    """Every Python file under `root`, walked — `rglob`, so `bin/lib/` is seen.

    Two sibling guards in this suite were measured blind to exactly that: a
    reviewer planted the defect one directory down and both stayed green.
    """
    return sorted(p for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts
                  and is_python(p))


def _is_waiting_set(node: ast.AST) -> bool:
    """A collection of string constants whose members are exactly WAITING.

    `frozenset((...))`/`set([...])` unwrap to their one argument first, so the
    named form in `bin/lib` and the inlined form the old copies used are read
    as the same shape rather than as two.
    """
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id in ("set", "frozenset") and len(node.args) == 1:
        node = node.args[0]
    if not isinstance(node, (ast.Set, ast.Tuple, ast.List)):
        return False
    members = set()
    for element in node.elts:
        if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
            return False
        members.add(element.value)
    return members == set(WAITING)


def _writes_a_rule_field(target: ast.AST) -> str:
    """`…["startable"]` / `…["blocked_stale"]` as an assignment target, or ""."""
    if not isinstance(target, ast.Subscript):
        return ""
    key = target.slice
    if isinstance(key, ast.Constant) and key.value in RULE_FIELDS:
        return str(key.value)
    return ""


class _Walk(ast.NodeVisitor):
    """Collect findings, carrying the enclosing function's qualified name."""

    def __init__(self, name: str, lines: list[str]):
        self.name = name
        self.lines = lines
        self.stack: list[str] = []
        self.found: list[Finding] = []

    def _source(self, node: ast.AST) -> str:
        line = getattr(node, "lineno", 0)
        return self.lines[line - 1].strip() if 0 < line <= len(self.lines) else ""

    def _record(self, node: ast.AST, shape: str) -> None:
        self.found.append(Finding(
            file=self.name, line=getattr(node, "lineno", 0),
            function=".".join(self.stack) or "<module>",
            shape=shape, source=self._source(node)))

    def _scoped(self, node) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    visit_FunctionDef = _scoped
    visit_AsyncFunctionDef = _scoped
    visit_ClassDef = _scoped

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            field = _writes_a_rule_field(target)
            # A constant is the blank a row template carries, not the rule.
            if field and not isinstance(node.value, ast.Constant):
                self._record(node, f"computes ['{field}']")
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        field = _writes_a_rule_field(node.target)
        if field and node.value is not None \
                and not isinstance(node.value, ast.Constant):
            self._record(node, f"computes ['{field}']")
        self.generic_visit(node)

    def _collection(self, node) -> None:
        """`{...}`, `(...)`, `[...]` and `frozenset(...)` are all one shape.

        A `frozenset(("blocked", "review"))` matches here AND again when the
        walk descends into its tuple; `scan_source` drops the duplicate, so the
        named and inlined spellings weigh the same.
        """
        if _is_waiting_set(node):
            self._record(node, "the waiting-status set")
        self.generic_visit(node)

    visit_Set = _collection
    visit_Tuple = _collection
    visit_List = _collection
    visit_Call = _collection


def scan_source(source: str, name: str) -> list[Finding]:
    """Every shape of the rule in one file's text. Raises on unparsable input."""
    walk = _Walk(name, source.split("\n"))
    walk.visit(ast.parse(source))
    seen: dict[tuple[int, str], Finding] = {}
    for finding in walk.found:
        seen.setdefault((finding.line, finding.shape), finding)
    return sorted(seen.values(), key=lambda f: (f.line, f.shape))


def _name(path: pathlib.Path) -> str:
    """Repo-relative where that is meaningful, bare otherwise.

    `measure()` is run against a COPY of `bin/` in a temp directory by the
    anti-vacuity tests, and a copy is not under `ROOT`.
    """
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def sweep(root: pathlib.Path = BIN) -> list[Finding]:
    out: list[Finding] = []
    for path in sources(root):
        try:
            text = path.read_text(errors="replace")
        except OSError:                                  # pragma: no cover
            continue
        try:
            out.extend(scan_source(text, _name(path)))
        except SyntaxError:                              # pragma: no cover
            continue
    return out


def homes(findings: list[Finding]) -> dict[str, list[Finding]]:
    """The rule's homes, keyed by the (file, function) a copy would have to share.

    Only the *assignment* shape defines a home. Counting by function rather
    than by file is what makes this see the defect it exists for: both copies
    lived in **one file**, `bin/perry-task`, 200 lines apart, so a per-file
    count would have called that one home and stayed green through the whole
    thing this row is about.

    The waiting set is a supporting shape, not a home of its own — the single
    implementation names it once at module scope, which is a different function
    from the one that reads it and always would be.
    """
    grouped: dict[str, list[Finding]] = {}
    for finding in findings:
        if finding.shape.startswith("computes"):
            grouped.setdefault(finding.home(), []).append(finding)
    return dict(sorted(grouped.items()))


def measure(root: pathlib.Path = BIN) -> dict:
    found = sweep(root)
    grouped = homes(found)
    files = {name.split(" § ")[0] for name in grouped}
    waiting = [f for f in found if not f.shape.startswith("computes")]
    return {
        "files_scanned": len(sources(root)),
        "homes": {name: [f._asdict() for f in items]
                  for name, items in grouped.items()},
        "home_count": len(grouped),
        "waiting_sets": [f._asdict() for f in waiting],
        # An inlined `{"blocked", "review"}` in a tool is half a copy of the
        # rule and the half that reads innocent: it is a status list, until it
        # is the status list, and then the rule is stated in two files again.
        "waiting_sets_outside_the_home": [
            f._asdict() for f in waiting if f.file not in files],
    }


def ok(result: dict) -> bool:
    return (result["home_count"] == 1
            and bool(result["waiting_sets"])
            and not result["waiting_sets_outside_the_home"])


def report(result: dict) -> str:
    lines = [f"python files scanned under bin/: {result['files_scanned']}",
             f"places the startable rule is stated: {result['home_count']}"]
    for name, items in result["homes"].items():
        lines.append(f"  {name}")
        for item in items:
            lines.append(f"    {item['file']}:{item['line']}  "
                         f"{item['shape']}  —  {item['source'][:80]}")
    lines.append(f"the waiting-status set, {len(result['waiting_sets'])} "
                 f"occurrence(s):")
    for item in result["waiting_sets"]:
        lines.append(f"    {item['file']}:{item['line']}  —  "
                     f"{item['source'][:80]}")
    if not ok(result):
        lines += ["", "EXPECTED EXACTLY ONE HOME, and the waiting set beside "
                  "it. More than one and a fix has to be applied more than "
                  "once (TASK-141 did); none at all and this check is scanning "
                  "for a shape that no longer exists."]
        for item in result["waiting_sets_outside_the_home"]:
            lines.append(f"  outside the home: {item['file']}:{item['line']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    result = measure()
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json
          else report(result))
    return 0 if ok(result) else 1


if __name__ == "__main__":
    sys.exit(main())
