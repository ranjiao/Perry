#!/usr/bin/env python3
"""Rule R -- the generator of TASK-067's Bound.

Domain D: every tracked file of this repository that is Python source
(a `.py` suffix, or an extensionless file whose shebang names python),
excluding `tests/` (a fixture is not a write path) and `__pycache__`.

A (file, line) is a MEMBER of the Bound iff its AST node is one of:

  W1  a call to a viewer/tables.py cell/row WRITER:
      render_row | check_cell | splice_cell | append_cell
  W2  a string expression that builds table-row text out of a literal
      containing `|` WITHOUT going through W1:
        - `<lit with |>.join(...)`
        - `<lit with |> % ...`     (BinOp Mod, either operand)
        - `<lit with |> + ...`     (BinOp Add, either operand)
        - `<lit with |>.format(...)`
        - f-string whose literal part holds `|` and which interpolates
  R1  a call to a viewer/tables.py row SPLITTER: split_row | cell_spans
  R2  a split of a string on `|` WITHOUT going through R1:
        - `.split/.rsplit/.partition/.rpartition(<lit or Name resolving
          to a str containing `|`>, ...)`
        - `re.split(<pattern literal that can match a literal `|`>, ...)`

Names are resolved through module-level and function-level `X = "..."`
bindings, so a `SEP = "|"` indirection is a member exactly as the
inline literal is.
"""
import ast, os, subprocess, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."

WRITERS = {"render_row", "check_cell", "splice_cell", "append_cell"}
SPLITTERS = {"split_row", "cell_spans"}
SPLIT_METHODS = {"split", "rsplit", "partition", "rpartition"}


def domain():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT,
                         capture_output=True, text=True).stdout.split()
    keep = []
    for f in out:
        if f.startswith("tests/") or "__pycache__" in f:
            continue
        p = os.path.join(ROOT, f)
        if not os.path.isfile(p):
            continue
        if f.endswith(".py"):
            keep.append(f)
            continue
        try:
            with open(p, "rb") as fh:
                first = fh.readline().decode("utf-8", "replace")
        except OSError:
            continue
        if first.startswith("#!") and "python" in first:
            keep.append(f)
    return sorted(keep)


def lit(node):
    """The str constant `node` denotes, or None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


#: Exclusion clauses. A node the pattern matches is NOT a member if it is:
#:  E1  regex context -- inside a `re.<fn>(...)` call, or its subtree calls
#:      `re.escape`. A `|` there is alternation, not a delimiter.
#:  E2  fed to the checked splitter -- the node is an argument of
#:      `split_row(...)` / `cell_spans(...)`; building a row TO HAND to the
#:      choke point is a use of the choke point.
#:  E3  a diagnostic -- the node is an argument of `Finding(...)`,
#:      `Refused(...)` or `print(...)`. The text becomes a console message,
#:      never a line of a state file.
RE_FNS = {"compile", "match", "search", "sub", "subn", "fullmatch", "split",
          "findall", "finditer", "escape"}
DIAG = {"Finding", "Refused", "print"}


def excluded(node, stack):
    for anc in stack:
        if not isinstance(anc, ast.Call):
            continue
        f = anc.func
        if (isinstance(f, ast.Attribute) and f.attr in RE_FNS
                and isinstance(f.value, ast.Name) and f.value.id == "re"):
            return "E1"
        if isinstance(f, ast.Name) and f.id in SPLITTERS:
            return "E2"
        if isinstance(f, ast.Name) and f.id in DIAG:
            return "E3"
    for sub in ast.walk(node):
        if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
                and sub.func.attr == "escape"
                and isinstance(sub.func.value, ast.Name)
                and sub.func.value.id == "re"):
            return "E1"
    return None


class Scan(ast.NodeVisitor):
    def __init__(self, path, src):
        self.path, self.hits = path, []
        self.consts = {}
        self.stack = []
        self.excl = []
        tree = ast.parse(src)
        # one pre-pass to bind `NAME = "literal"` anywhere in the file
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign):
                v = lit(n.value)
                if v is not None:
                    for t in n.targets:
                        if isinstance(t, ast.Name):
                            self.consts[t.id] = v
        self.visit(tree)

    def generic_visit(self, node):
        self.stack.append(node)
        super().generic_visit(node)
        self.stack.pop()

    def add(self, node, kind, what):
        e = excluded(node, reversed(self.stack))
        row = (self.path, node.lineno, kind, what)
        if e:
            if (row, e) not in self.excl:
                self.excl.append((row, e))
            return
        if row not in self.hits:
            self.hits.append(row)

    def strval(self, node):
        """str this node denotes, following one level of NAME binding."""
        v = lit(node)
        if v is not None:
            return v
        if isinstance(node, ast.Name):
            return self.consts.get(node.id)
        return None

    def visit_JoinedStr(self, node):
        parts = "".join(lit(v) or "" for v in node.values
                        if isinstance(v, ast.Constant))
        if "|" in parts and any(isinstance(v, ast.FormattedValue)
                                for v in node.values):
            self.add(node, "W2", "f-string with a `|` literal part")
        self.generic_visit(node)

    def visit_BinOp(self, node):
        for side, other in ((node.left, node.right), (node.right, node.left)):
            s = self.strval(side)
            if s is None or "|" not in s:
                continue
            if isinstance(node.op, ast.Mod):
                self.add(node, "W2", "`%` onto a `|` literal")
                break
            if isinstance(node.op, ast.Add) and not isinstance(
                    other, ast.Constant):
                self.add(node, "W2", "`+`-concat onto a `|` literal")
                break
        self.generic_visit(node)

    def visit_Call(self, node):
        f = node.func
        if isinstance(f, ast.Name) and f.id in WRITERS:
            self.add(node, "W1", f"{f.id}()")
        elif isinstance(f, ast.Attribute) and f.attr in WRITERS:
            self.add(node, "W1", f"{f.attr}()")
        elif isinstance(f, ast.Name) and f.id in SPLITTERS:
            self.add(node, "R1", f"{f.id}()")
        elif isinstance(f, ast.Attribute) and f.attr in SPLITTERS:
            self.add(node, "R1", f"{f.attr}()")
        elif isinstance(f, ast.Attribute):
            recv = self.strval(f.value)
            if f.attr in ("join", "format") and recv and "|" in recv:
                self.add(node, "W2", f"`{recv}`.{f.attr}()")
            elif (f.attr in SPLIT_METHODS and node.args and not
                  (isinstance(f.value, ast.Name) and f.value.id == 're')):
                a = self.strval(node.args[0])
                if a and "|" in a:
                    self.add(node, "R2", f".{f.attr}({a!r})")
            elif (f.attr == "split" and isinstance(f.value, ast.Name)
                  and f.value.id == "re"):
                pass
        # re.split(pattern, ...)
        if (isinstance(f, ast.Attribute) and f.attr == "split"
                and isinstance(f.value, ast.Name) and f.value.id == "re"
                and node.args):
            pat = self.strval(node.args[0])
            if pat and pipe_matchable(pat):
                self.add(node, "R2", f"re.split({pat!r})")
        self.generic_visit(node)


def pipe_matchable(pat):
    """True if regex `pat` can match a literal `|` character."""
    i, in_class = 0, False
    while i < len(pat):
        c = pat[i]
        if c == "\\":
            if i + 1 < len(pat) and pat[i + 1] == "|":
                return True
            i += 2
            continue
        if c == "[":
            in_class = True
        elif c == "]":
            in_class = False
        elif c == "|" and in_class:
            return True
        i += 1
    return False


rows = []
excl = []
for f in domain():
    src = open(os.path.join(ROOT, f), encoding="utf-8").read()
    try:
        sc = Scan(f, src); rows += sc.hits; excl += sc.excl
    except SyntaxError as e:
        print(f"!! {f}: {e}", file=sys.stderr)

rows.sort(key=lambda r: (r[0], r[1]))
for path, line, kind, what in rows:
    print(f"{kind}\t{path}:{line}\t{what}")
print(f"--- {len(rows)} member(s); {len(excl)} excluded ---", file=sys.stderr)
for (pp, ll, kk, ww), e in sorted(excl):
    print(f"  {e} excl {kk}\t{pp}:{ll}\t{ww}", file=sys.stderr)
for k in ("W1", "W2", "R1", "R2"):
    print(f"    {k}: {sum(1 for r in rows if r[2] == k)}", file=sys.stderr)
