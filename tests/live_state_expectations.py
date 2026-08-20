"""The sweep TASK-113 ran by hand, as a mechanism: a check must not read the
live project as its expected value.

TASK-113 found five of these in one afternoon and fixed them one at a time; the
pass itself was thrown away, and three more arrived within the week — two the
moment `.perry/config.md` declared its first track (`d90612a`), two more when
PR #14 changed which paths `schema/state-schema.json` says Perry owns. There
was no mechanism, only a memory of having looked. This is the mechanism.

## What the class IS

**A check is in this class when a value it read out of the project it lives in
is asserted equal to a literal that enumerates or counts what that project
happens to hold today.** Both halves have to be true:

1. **It reaches live state.** The value under assertion came from a path
   `schema/state-schema.json` declares Perry writes — resolved through the
   `State root:` line in `.perry/config.md`, so `BOARD.md` anchored at `state`
   means `perry/BOARD.md` here — or from the **parsed payload** of one of
   Perry's own tools run with `cwd=` or `--root` pointing into this repository
   rather than at a fixture the test built. Nothing about the *names* of those
   paths is written down here; the list comes out of the schema, which is why
   the move behind instance 8 (a claim added, so `perry/tasks.jsonl` stopped
   being unclaimed) changes what this guard considers live rather than being
   a fact hard-coded past it.
2. **Its expectation is closed.** The other side of the assertion is a literal
   whose value is fixed by the source text: a non-trivial constant, or a
   non-empty list/set/tuple/dict *display* — including one reached through a
   module or class constant, or through `set(...)`/`sorted(...)` of one. A
   display pins cardinality and membership, so the project acquiring or losing
   one record falsifies it. `[]`, `{}`, `0`, `1`, `""`, `None` are not closed
   in this sense: "nothing is wrong" is a property, quantified over whatever
   the project holds, and it is the shape every one of the repairs took.

The two halves are what keep this from being either useless direction. A test
that reads a fixture it built fails (1) however literal its expectations are —
which is most of the suite, and is the whole point: `test_prioritize` asserts
exact rendered tables against boards it wrote itself, and must keep doing so. A
test that reads BOARD.md and asserts a property *of* what it read — `sum(...)
== len(records)`, `set(report["kinds"]) == {r["kind"] for r in records}`,
`problems == []` — fails (2), because it restates nothing.

## What it deliberately does NOT catch

Written down because a guard whose boundary is undocumented gets widened by the
next person until it flags everything.

- **Containment.** `assertIn("## Why the state root is not `.`", text)` over a
  live file is not flagged. Growth cannot falsify it, and `test_md_store` kept
  exactly that line through its repair. The cost is real and known: instance 8
  was `assertIn("perry/tasks.jsonl (unclaimed)", …)`, and this guard does not
  catch it. Catching it needs a different signal — a *path literal* the
  schema's claim list has made stale — and that signal cannot be told apart
  from the hundreds of path strings the fixtures legitimately write.
- **A live value used as INPUT.** Instance 2 borrowed `TASK-038` off the live
  board and passed it to `perry-task next`; the row closed, the tool answered
  "TASK-038 is not a row on the board", and the assertion about flag naming
  stopped running. That is the same disease and this guard is blind to it —
  the defect is in the fixture, not in an expected value, and every test that
  writes a plausible id would look identical.
- **`assertTrue` / `assertFalse` on a live value.** `assertFalse(w[
  "register_declared"])` is genuinely of the class and is not flagged on its
  own account: there is no expected side to judge, and the same shape covers
  `assertTrue(path.exists())`, which is fine. Instance 7 is still reported,
  from the `["main"]` on the line below it.
- **A tool's exit code and its human text.** `assertEqual(proc.returncode, 2)`
  and `assertGreater(len(proc.stdout), 40)` are contracts of the TOOL. Only
  the JSON payload is a projection of the project, so only it is followed.
- **Code, contracts and templates.** `schema/`, `SKILL.md`, `bin/`, `modes/`,
  `state/` and `tests/fixtures/` are not live state. A test that pins an exact
  literal against `schema/state-schema.json` SHOULD go red when someone edits
  the schema — that is a contract test doing its job, and `test_ownership` is
  full of them. The corollary is a known false positive: a payload subtree the
  tool builds from its own constants (`perry-task list --json § semantics`)
  cannot be told from one it built out of the project.
- **The repository root handed to a helper.** `self.drive("rows", str(ROOT))`
  runs a tool on this project and is not reported. Taking `ROOT` as a live
  target was tried and reverted: `relative_to(PERRY_HOME)` and the dozen other
  bookkeeping uses put 21 fixture-only assertions on the report.
- **Anything outside `tests/`.** `bin/perry-diagnose` reading its own output as
  input is the same disease in a different organ (TASK-126), and a different
  row.
- **Dynamic reach.** A live read routed through a base class in another module,
  or built by string formatting, is invisible here. The analysis is one module
  at a time, over the syntax.

## What it reports today

Not zero, and the number is the point: `tests/fixtures/live-state-expectations
.json` records every hit with a verdict, so a new one is a red rather than a
line in a report nobody reads. `tests/test_live_state_expectations.py` holds
that baseline to the sweep and reconstructs three of the eight instances out
of history to prove the sweep still finds what it was built for.

Run: python3 tests/live_state_expectations.py
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import pathlib
import re
import sys
from typing import NamedTuple

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: Every hit the sweep makes over this repository, with a verdict on each.
#: Recorded rather than asserted-to-be-empty because it is NOT empty, and a
#: floor nobody wrote down is a floor that drifts upward one silence at a time.
BASELINE = ROOT / "tests" / "fixtures" / "live-state-expectations.json"

#: Reading a path, as opposed to naming one. `exists`/`stat` are reads too: a
#: test can assert a count of what a live directory holds without opening it.
READ_METHODS = frozenset({
    "read_text", "read_bytes", "open", "read", "readlines", "glob", "rglob",
    "iterdir", "exists", "is_file", "is_dir", "stat",
})

#: Assertions with an expected side that has to match exactly. `assertIn` and
#: the truth asserts are out on purpose — see the module docstring.
EXACT_ASSERTS = frozenset({
    "assertEqual", "assertNotEqual", "assertListEqual", "assertDictEqual",
    "assertSetEqual", "assertTupleEqual", "assertCountEqual",
    "assertSequenceEqual", "assertMultiLineEqual",
})
#: A threshold on a live count is the same defect wearing an inequality —
#: `c9018ae` was `rows_from_store > 20`, made false by one ordinary close.
ORDER_ASSERTS = frozenset({
    "assertGreater", "assertGreaterEqual", "assertLess", "assertLessEqual",
})

#: Constructors that carry a literal through unchanged.
PURE_CTORS = frozenset({"set", "frozenset", "list", "tuple", "dict", "sorted"})

#: In-place growth, which taints the container the way an assignment would.
MUTATORS = frozenset({"append", "extend", "update", "add", "setdefault"})

#: Naming a path, not reading one.
PATH_OPS = frozenset({"str", "os.fspath", "Path", "pathlib.Path"})

#: `def` in either flavour.
FUNCTION = (ast.FunctionDef, ast.AsyncFunctionDef)

SUBPROCESS = frozenset({
    "subprocess.run", "subprocess.check_output", "subprocess.Popen",
    "subprocess.call", "subprocess.check_call",
})


# ── which paths are live state ────────────────────────────────────────────
# Read out of the schema, never listed here. The eight known instances span
# BOARD.md, the journal, the event log, `.perry/config.md` and the claim list
# itself; a guard that named any of them would have missed the others.

def state_root(root: pathlib.Path) -> str:
    """The `State root:` pointer, as a repo-relative prefix (`""` for `.`)."""
    config = root / ".perry" / "config.md"
    if not config.exists():
        return ""
    m = re.search(r"^-\s*State root:\s*(\S+)\s*$", config.read_text(), re.M)
    value = (m.group(1) if m else ".").strip("`").strip()
    return "" if value == "." else value.strip("/")


def live_patterns(root: pathlib.Path = ROOT) -> list[str]:
    """Every path the schema declares Perry writes, anchored for this project.

    `anchor: state` hangs the path under the state root; `anchor: project`
    hangs it at the repository root. The state root itself is included: a test
    that counts what `perry/` holds is reading live state whether or not it
    names a file inside it.
    """
    schema = json.loads((root / "schema" / "state-schema.json").read_text())
    prefix = state_root(root)
    out: set[str] = {".perry"}
    if prefix:
        out.add(prefix)
    declared = list(schema.get("claims", [])) + list(schema.get("files", []))
    for entry in declared:
        path = str(entry.get("path", "")).strip("/")
        if not path:
            continue
        if entry.get("anchor") == "state" and prefix:
            path = f"{prefix}/{path}"
        out.add(path)
    return sorted(out)


def is_live_path(rel: str, patterns: list[str]) -> bool:
    """Does this repo-relative path fall inside the project's own state?"""
    if rel is None:
        return False
    rel = rel.strip("/")
    if not rel:
        return False
    for pat in patterns:
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat + "/*"):
            return True
        # A directory named above a claimed glob — `perry/phase` for
        # `perry/phase/[0-9][0-9][0-9]-*.md` — is the same live directory.
        if pat.startswith(rel + "/"):
            return True
    return False


# ── findings ──────────────────────────────────────────────────────────────

class Taint(NamedTuple):
    """What a function is holding: values read out of the project, and the
    results of tools run against it. The two are separate because a tool's
    exit code and its human text are the TOOL's contract — only the parsed
    payload is a projection of project state."""
    names: set[str]
    tools: set[str]


class Finding(NamedTuple):
    module: str
    lineno: int
    test: str
    assertion: str
    actual: str
    expected: str

    @property
    def key(self) -> tuple[str, str, str, str, str]:
        """Identity WITHOUT the line number, so an edit ten lines above does
        not look like a new finding."""
        return (self.module, self.test, self.assertion, self.actual,
                self.expected)

    def __str__(self) -> str:
        return (f"{self.module}:{self.lineno}  {self.test}\n"
                f"    {self.assertion}(<live>, {self.expected})\n"
                f"    live: {self.actual}")


# ── the syntax the analysis walks ─────────────────────────────────────────

def _dotted(node: ast.AST) -> str:
    """`subprocess.run`, `self.SIGNED`, `T` — or `""` for anything else."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else ""
    return ""


def _is_trivial_const(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and _trivial(node.value)


def _trivial(value: object) -> bool:
    """A literal that says "nothing", not "exactly this"."""
    if value is None or isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return value in (0, 1)
    if isinstance(value, (str, bytes)):
        return len(value) == 0
    return False


class Module:
    """One test module, read for the two halves of the class."""

    def __init__(self, source: str, name: str, patterns: list[str]):
        self.name = name
        self.tree = ast.parse(source, filename=name)
        self.patterns = patterns
        #: name → repo-relative path it denotes
        self.paths: dict[str, str] = {}
        #: name → the literal node it is bound to
        self.literals: dict[str, ast.AST] = {}
        #: names bound at module level to a live read
        self.module_live: set[str] = set()
        #: `Class.method` names whose return value is live
        self.live_methods: set[str] = set()
        #: path names bound inside the function currently being read
        self._scope: dict[str, str] = {}
        self._collect()

    # -- paths -------------------------------------------------------------

    def _const_str(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def path_of(self, node: ast.AST) -> str | None:
        """The repo-relative path this expression denotes, if it is knowable.

        `""` is the repository root, which is a real answer and not a miss —
        callers must test `is not None`.
        """
        if isinstance(node, ast.Name):
            if node.id in self._scope:
                return self._scope[node.id]
            return self.paths.get(node.id)
        if isinstance(node, ast.Attribute):
            if node.attr == "parent":
                base = self.path_of(node.value)
                if not base:    # unknown, or the repo root: no parent in here
                    return None
                return base.rsplit("/", 1)[0] if "/" in base else ""
            return self.paths.get(_dotted(node))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            base = self.path_of(node.left)
            seg = self._const_str(node.right)
            if base is None or seg is None:
                return None
            return f"{base}/{seg}".strip("/")
        if isinstance(node, ast.Call):
            fn = _dotted(node.func)
            if fn in ("str", "os.fspath") and len(node.args) == 1:
                return self.path_of(node.args[0])
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in ("resolve", "absolute", "expanduser"):
                    return self.path_of(node.func.value)
                if node.func.attr == "joinpath":
                    base = self.path_of(node.func.value)
                    segs = [self._const_str(a) for a in node.args]
                    if base is None or any(s is None for s in segs):
                        return None
                    return "/".join([base, *segs]).strip("/")
            if fn.endswith("Path") and len(node.args) == 1:
                if _dotted(node.args[0]) == "__file__":
                    return self.name
                return self.path_of(node.args[0])
        return None

    def local_paths(self, fn: ast.AST) -> dict[str, str]:
        """Path names bound inside one function.

        `log = PERRY_HOME / ".perry" / "events.jsonl"` is where instance 1's
        read starts, and it is a local. Two passes so a chain of them settles.
        """
        scope: dict[str, str] = {}
        saved, self._scope = self._scope, scope
        try:
            for _ in range(2):
                for node in ast.walk(fn):
                    if isinstance(node, ast.Assign) and len(node.targets) == 1:
                        name = _dotted(node.targets[0])
                        path = self.path_of(node.value)
                        if name and path is not None:
                            scope[name] = path
        finally:
            self._scope = saved
        return scope

    # -- collection --------------------------------------------------------

    def _collect(self) -> None:
        for node in self.tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                self._bind_module(node.targets[0], node.value)
        # Two passes: a method that returns live makes its callers live.
        for _ in range(2):
            for cls in [n for n in self.tree.body
                        if isinstance(n, ast.ClassDef)]:
                for item in cls.body:
                    if isinstance(item, ast.Assign) and len(item.targets) == 1:
                        target = _dotted(item.targets[0])
                        if target and self._is_literal_node(item.value):
                            self.literals.setdefault(target, item.value)
                            self.literals.setdefault(f"self.{target}",
                                                     item.value)
                    if isinstance(item, FUNCTION):
                        saved = self._scope
                        self._scope = self.local_paths(item)
                        try:
                            if self._returns_live(item, self.taint(item)):
                                self.live_methods.add(f"self.{item.name}")
                        finally:
                            self._scope = saved
        for node in self.tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                if self.is_live(node.value, Taint(set(), set())):
                    self.module_live |= _bound_names(node.targets[0])

    def _bind_module(self, target: ast.AST, value: ast.AST) -> None:
        name = _dotted(target)
        if not name:
            return
        path = self.path_of(value)
        if path is not None:
            self.paths[name] = path
        if self._is_literal_node(value):
            self.literals[name] = value

    def _is_literal_node(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Constant):
            return True
        if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
            return all(self._is_literal_node(e) for e in node.elts)
        if isinstance(node, ast.Dict):
            return all(k is not None and self._is_literal_node(k)
                       for k in node.keys)
        return False

    def _returns_live(self, fn: ast.AST, taint: Taint) -> bool:
        return any(isinstance(n, ast.Return) and n.value is not None
                   and self.is_live(n.value, taint)
                   for n in ast.walk(fn))

    # -- half one: does this expression reach live state? ------------------

    def live_source(self, node: ast.AST,
                    tools: frozenset[str] = frozenset()) -> bool:
        """This node, on its own, reads the project living around the test."""
        if not isinstance(node, ast.Call):
            return False
        fn = _dotted(node.func)
        if fn in ("open", "io.open") and node.args:
            return is_live_path(self.path_of(node.args[0]), self.patterns)
        if isinstance(node.func, ast.Attribute) \
                and node.func.attr in READ_METHODS:
            return is_live_path(self.path_of(node.func.value), self.patterns)
        if fn in ("json.loads", "json.load") and node.args:
            return self._reaches_tool(node.args[0], tools)
        if fn in SUBPROCESS:
            return False    # the run itself; only its PAYLOAD is the project
        if fn in PATH_OPS or self.path_of(node) is not None:
            return False   # naming a path is not reading one
        # Any other call handed a live path reads it — the callee is a helper
        # in this module or a sibling, and `assert_round_trips(M.CONFIG, path)`
        # is how instance 6 reached `.perry/config.md`. The repository ROOT
        # itself does not count — `relative_to(PERRY_HOME)` and `str(ROOT)`
        # handed to a helper are overwhelmingly bookkeeping, and taking them
        # as reads put 21 fixture-only assertions on the report.
        return any(is_live_path(self.path_of(a), self.patterns)
                   for a in _call_operands(node))

    def _reaches_tool(self, node: ast.AST, tools: frozenset[str]) -> bool:
        """Does this expression carry the output of a tool run on this repo?"""
        for n in ast.walk(node):
            if isinstance(n, ast.Call) and _dotted(n.func) in SUBPROCESS \
                    and self._tool_reads_this_project(n):
                return True
            if isinstance(n, (ast.Name, ast.Attribute)) \
                    and _dotted(n) in tools:
                return True
        return False

    def _tool_reads_this_project(self, call: ast.Call) -> bool:
        """A Perry tool pointed at this repository, not at a fixture.

        A test says which project it means in one of three places, read in
        this order: `--root <dir>`, `cwd=<dir>`, or a state path among the
        arguments. **With none of them the answer is no** — the tool would in
        fact inherit the runner's cwd and so read this repository, but
        `--help` and `--version` runs are the bulk of that population and none
        of them touches state. A stated blind spot, not a claim: say
        `cwd=ROOT` and the guard sees you.
        """
        operands = _call_operands(call)
        for i, node in enumerate(operands):
            if isinstance(node, ast.Constant) and node.value == "--root":
                nxt = operands[i + 1] if i + 1 < len(operands) else None
                return nxt is not None and self.path_of(nxt) is not None
        kwargs = {kw.arg: kw.value for kw in call.keywords if kw.arg}
        if "cwd" in kwargs:
            return self.path_of(kwargs["cwd"]) is not None
        return any(is_live_path(self.path_of(a), self.patterns)
                   for a in operands)

    def is_live(self, node: ast.AST, taint: Taint) -> bool:
        for n in ast.walk(node):
            if self.live_source(n, taint.tools):
                return True
            if isinstance(n, (ast.Name, ast.Attribute)):
                if _dotted(n) in taint.names:
                    return True
            if isinstance(n, ast.Call) \
                    and _dotted(n.func) in self.live_methods:
                return True
        return False

    def taint(self, fn: ast.AST) -> Taint:
        """Names inside one function that hold something read out of the
        project (`names`), and names holding a tool run against it (`tools`).

        Three passes rather than a real fixpoint: the deepest chain in this
        suite is four assignments and the analysis is advisory.
        """
        taint = Taint(set(self.module_live), set())
        for _ in range(3):
            before = len(taint.names) + len(taint.tools)
            for node in ast.walk(fn):
                bound: set[str] = set()
                value: ast.AST | None = None
                if isinstance(node, ast.Assign):
                    value = node.value
                    for t in node.targets:
                        bound |= _bound_names(t)
                elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
                    value, bound = node.value, _bound_names(node.target)
                elif isinstance(node, ast.For):
                    value, bound = node.iter, _bound_names(node.target)
                elif isinstance(node, ast.With):
                    for item in node.items:
                        if item.optional_vars is not None \
                                and self.is_live(item.context_expr, taint):
                            taint.names.update(
                                _bound_names(item.optional_vars))
                elif isinstance(node, ast.Call) \
                        and isinstance(node.func, ast.Attribute) \
                        and node.func.attr in MUTATORS:
                    if any(self.is_live(a, taint) for a in node.args):
                        taint.names.update(_bound_names(node.func.value))
                if value is None or not bound:
                    continue
                if self.is_live(value, taint):
                    taint.names.update(bound)
                if self._reaches_tool(value, frozenset(taint.tools)):
                    taint.tools.update(bound)
            if len(taint.names) + len(taint.tools) == before:
                break
        return taint

    # -- half two: is the expectation closed? ------------------------------

    def closed_literal(self, node: ast.AST, depth: int = 0) -> bool:
        if depth > 4:
            return False
        if isinstance(node, (ast.Name, ast.Attribute)):
            bound = self.literals.get(_dotted(node))
            return bound is not None and self.closed_literal(bound, depth + 1)
        if isinstance(node, ast.Constant):
            return not _trivial(node.value)
        if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
            # Every element fixed by the source, or it is not an enumeration:
            # `(expected["open"], expected["closed"])` restates nothing.
            return bool(node.elts) and all(
                self.closed_literal(e, depth + 1) or _is_trivial_const(e)
                for e in node.elts)
        if isinstance(node, ast.Dict):
            # The KEYS are what a dict display pins: `{"setting": n}`
            # says "one kind, named `setting`" whatever the count beside it is.
            return bool(node.keys) and all(
                k is not None and isinstance(k, ast.Constant)
                for k in node.keys)
        if isinstance(node, ast.Call) and len(node.args) == 1 \
                and _dotted(node.func) in PURE_CTORS:
            return self.closed_literal(node.args[0], depth + 1)
        return False

    # -- the sweep ---------------------------------------------------------

    def findings(self) -> list[Finding]:
        out: list[Finding] = []
        for cls in ast.walk(self.tree):
            if not isinstance(cls, ast.ClassDef):
                continue
            for fn in cls.body:
                if not isinstance(fn, FUNCTION):
                    continue
                out.extend(self._findings_in(fn, f"{cls.name}.{fn.name}"))
        return sorted(out, key=lambda f: (f.module, f.lineno))

    def _findings_in(self, fn: ast.AST, where: str) -> list[Finding]:
        saved, self._scope = self._scope, self.local_paths(fn)
        try:
            return self._scan(fn, where)
        finally:
            self._scope = saved

    def _scan(self, fn: ast.AST, where: str) -> list[Finding]:
        taint = self.taint(fn)
        out: list[Finding] = []
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call) \
                    or not isinstance(node.func, ast.Attribute):
                continue
            name = node.func.attr
            if name not in EXACT_ASSERTS and name not in ORDER_ASSERTS:
                continue
            if len(node.args) < 2:
                continue
            left, right = node.args[0], node.args[1]
            for live, lit in ((left, right), (right, left)):
                if self.closed_literal(lit) and self.is_live(live, taint):
                    out.append(Finding(
                        module=self.name, lineno=node.lineno, test=where,
                        assertion=name,
                        actual=_clip(ast.unparse(live)),
                        expected=_clip(ast.unparse(lit))))
                    break
        return out


def _call_operands(call: ast.Call) -> list[ast.AST]:
    """Positional arguments, flattened through the one list a command is
    usually spelled as, so `--root` and its value stay adjacent."""
    out: list[ast.AST] = []
    for arg in call.args:
        if isinstance(arg, (ast.List, ast.Tuple)):
            out.extend(arg.elts)
        elif isinstance(arg, ast.Starred):
            out.append(arg.value)
        else:
            out.append(arg)
    out.extend(kw.value for kw in call.keywords if kw.arg not in ("cwd",))
    return out


def _bound_names(target: ast.AST) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        return set().union(*(_bound_names(e) for e in target.elts)) \
            if target.elts else set()
    if isinstance(target, ast.Attribute):
        return {_dotted(target)} - {""}
    if isinstance(target, ast.Subscript):
        return _bound_names(target.value)
    if isinstance(target, ast.Starred):
        return _bound_names(target.value)
    return set()


def _clip(text: str, width: int = 96) -> str:
    text = " ".join(text.split())
    return text if len(text) <= width else text[:width - 1] + "…"


# ── entry points ──────────────────────────────────────────────────────────

def scan_source(source: str, name: str,
                root: pathlib.Path = ROOT) -> list[Finding]:
    """Every finding in one module's source text, named however you like.

    Takes source rather than a path so a historical revision — `git show
    <commit>:tests/<module>` — can be swept without being written back into
    the tree it was taken from.
    """
    return Module(source, name, live_patterns(root)).findings()


def sweep(root: pathlib.Path = ROOT) -> list[Finding]:
    """The whole suite as it stands."""
    patterns = live_patterns(root)
    out: list[Finding] = []
    for path in sorted((root / "tests").glob("test_*.py")):
        rel = path.relative_to(root).as_posix()
        out.extend(Module(path.read_text(), rel, patterns).findings())
    return out


def recorded() -> dict[tuple[str, str, str, str, str], dict]:
    """The baseline, keyed the way a finding is."""
    if not BASELINE.exists():
        return {}
    entries = json.loads(BASELINE.read_text())["findings"]
    return {(e["module"], e["test"], e["assertion"], e["actual"],
             e["expected"]): e for e in entries}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="machine-readable")
    ap.add_argument("--root", default="", help="the repo to sweep")
    ap.add_argument("--record", action="store_true",
                    help="rewrite the baseline, KEEPING every verdict already "
                         "written for a finding that is still there")
    args = ap.parse_args(argv)
    root = pathlib.Path(args.root).resolve() if args.root else ROOT
    found = sweep(root)
    if args.record:
        known = recorded()
        BASELINE.write_text(json.dumps({
            "note": "Every hit of tests/live_state_expectations.py over this "
                    "repository. A finding with no verdict has not been "
                    "looked at; `instance` means a row is owed for it.",
            "findings": [
                {**f._asdict(),
                 "verdict": known.get(f.key, {}).get("verdict", ""),
                 "why": known.get(f.key, {}).get("why", "")}
                for f in found],
        }, indent=2) + "\n")
        print(f"recorded {len(found)} finding(s) in "
              f"{BASELINE.relative_to(ROOT)}")
        return 0
    if args.json:
        print(json.dumps([f._asdict() for f in found], indent=2))
    else:
        print("\n".join(str(f) for f in found) if found
              else "no check reads live project state as its expected value")
        print(f"\n{len(found)} finding(s) · live paths: "
              f"{len(live_patterns(root))} declared in schema")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
