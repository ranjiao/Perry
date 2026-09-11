"""Which flags each subcommand of a `SURFACE`-declaring tool actually READS.

One derivation for every tool whose dispatch is an `if cmd == …` chain —
`perry-tasks`, `perry-config`, and `perry_md_store` under the name of each
document it serves (`perry-okr`). `perry-task` is not one of these: it maps
flags onto an `args` namespace in `parse()`, and
`tests/test_bin_surface § TestPerryTaskDeclaresTheFlagsItsHandlersRead`
already derives its answer from that shape.

**Why a single reader rather than one per tool.** The three bodies differ in
where the chain lives and how deep the handlers sit, and in nothing else that
matters here: all three read a flag BY ITS LITERAL SPELLING out of the
`lib.parse_surface` result — `"--dry-run" in seen`, `given["--register"]`,
`"--from-board" not in argv`. So the question "does this subcommand read this
flag" is one question about one shape: *can this flag's spelling reach the
region of code that runs when `cmd` is this subcommand*.

Four things make the answer precise rather than "yes, everywhere":

1. **Branch narrowing.** A statement under `if cmd == "render":` belongs to
   `render`; under `if cmd in ("render", "diff")` to both. Nesting composes,
   which is what makes `perry_md_store`'s `if cmd == "render":` INSIDE
   `if cmd in ("render", "diff", "verify"):` come out as `render` alone.
2. **Fall-through.** When such a branch always returns, every statement after
   it is unreachable for the names it matched. That is the whole reason
   `perry-tasks`' tail — the `verify` body, which is guarded by nothing —
   belongs to `verify` and not to all seventeen.
3. **Lazy argument binding.** `cmd_render(…, write_board="--write" in flags,
   flags=flags)` is called for `render` AND for `diff`, so a reader that
   attributed the argument expression at the call site would say `diff` reads
   `--write`. It does not: `cmd_render` uses `write_board` only under
   `if not byte_compare:`. So an argument's flags travel INTO the parameter and
   are attributed where the parameter is USED. The same rule is what keeps
   `perry-config`'s prologue — `dry_run = "--dry-run" in read["seen"]`, above
   the chain and therefore "read by everything" — from making `--dry-run`
   unfalsifiable on `show`.
4. **Discriminator propagation.** `byte_compare=cmd == "diff"` is a per-
   subcommand constant, so inside the callee `if not byte_compare:` narrows
   the same way `if cmd == "render":` does.

**What "reads" means here, and why.** Not "the string appears" — *the flag can
change what this subcommand does*. A value computed and handed on but never
consulted changes nothing, which is exactly the accepted-and-silently-dropped
shape DESIGN-016 § 1.4 was opened on.

The derivation is deliberately allowed to UNDER-report: an under-report makes
direction B stricter and shows up at once as a red on an unmutated tree. It is
an OVER-report that is dangerous, because a reader that thinks every declared
flag is read makes direction B vacuous. So the over-report is a measurement
rather than a hope, and `tests/test_bin_surface` holds it to the number.
Measured 2026-09-11 on `488cf079`, over the three chain bodies:

    (subcommand, flag) pairs in the universe    149
    pairs the declarations carry                 48
    pairs this reader calls read                 63   (42.3%)
    a vacuous reader would call read            149   (100%)
    pairs it calls read and no declaration
      carries — direction B's blind spot         15   (all `perry-tasks`)

All fifteen are reads in code more than one subcommand runs, and each is a
place the tool DOES consult the flag — so declaring one gets it honoured or
refused out loud rather than accepted and dropped, which is why the blindness
is a limit rather than a hole. `test_the_pairs_direction_b_cannot_see_are_all
_shared_reads` carries the probe that establishes it.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

#: A flag as the tools spell them. Anchored on both ends on purpose: the
#: message text is full of "`--from-board`" and `f"render --write{r}"`, and
#: none of those is a read.
FLAG = re.compile(r"^--[a-z][a-z0-9-]*$")

#: How many calls deep a handler's flags are still attributed. `perry-tasks`
#: needs two — `main` → `cmd_risks_write` → `write_store_or_say_what_would_land`
#: — and the limit is what stops a walk through `json.dumps` and friends from
#: turning into a whole-module scan.
MAX_DEPTH = 3


class Val:
    """What an expression carries: flags, container-ness, and a discriminator.

    `container` marks the whole `seen`/`values`/`argv` bag — it names no single
    flag, so using it reads nothing; passing it to a handler is what matters.
    `disc` is a per-subcommand boolean (`cmd == "diff"`), which narrows inside
    the callee.
    """

    __slots__ = ("flags", "container", "disc")

    def __init__(self, flags=(), container=False, disc=None):
        self.flags = frozenset(flags)
        self.container = container
        self.disc = disc

    def __bool__(self):
        return bool(self.flags) or self.container or self.disc is not None

    def __repr__(self):                              # pragma: no cover - debug
        return (f"Val(flags={sorted(self.flags)}, container={self.container}, "
                f"disc={self.disc})")


EMPTY = Val()


def _terminates(body) -> bool:
    """Every path out of `body` leaves the enclosing function."""
    if not body:
        return False
    last = body[-1]
    if isinstance(last, (ast.Return, ast.Raise, ast.Continue, ast.Break)):
        return True
    if isinstance(last, ast.If):
        return _terminates(last.body) and _terminates(last.orelse)
    if isinstance(last, ast.With):
        return _terminates(last.body)
    if isinstance(last, ast.Try):
        return (_terminates(last.body) and
                all(_terminates(h.body) for h in last.handlers))
    return False


def _subexprs(node):
    """Every expression directly inside `node`, including the ones that are not
    its direct AST children.

    `ast.iter_child_nodes` on a comprehension yields `comprehension` objects
    rather than expressions, so a plain child walk never reaches
    `values.items()` in `merged.update({k: … for k, v in values.items()})` —
    which is the only place `bin/perry-config § cmd_track` consults the track
    flags, and the reader therefore reported `track` as reading none of them.
    Statement bodies are NOT descended into: a nested function or loop body is
    walked by the statement walker, which is what carries the active set.
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.expr):
            yield child
        elif not isinstance(child, ast.stmt):
            yield from _subexprs(child)


def _names_in(node) -> set[str]:
    """The string constants a subcommand test compares against."""
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.add(n.value)
    return out


class Reader:
    """One tool's dispatch body, read for the flags each subcommand can see."""

    def __init__(self, tree: ast.Module, module, subcommands):
        self.tree = tree
        self.module = module
        self.subs = frozenset(subcommands)
        self.funcs = {n.name: n for n in tree.body
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.out = {s: set() for s in self.subs}
        #: The same walk, kept twice. `out` is every flag whose spelling can
        #: reach code this subcommand runs; `only` is the subset read in code
        #: NO OTHER subcommand runs. The two answer the two directions, and
        #: they have to be different sets:
        #:
        #: * **direction B** — declared and never read — asks "can this flag
        #:   reach anything at all", so it must use the permissive `out`, or
        #:   `perry-tasks build --register` (read once in a prologue shared by
        #:   all seventeen) would be reported as dropped;
        #: * **direction A** — read and never declared — asks "is there code
        #:   only this subcommand runs that consults it", so it must use
        #:   `only`. A shared read says nothing about which of the sharers
        #:   wants the flag: `cmd_risks_render`'s storeless branch consults
        #:   `write_board` for `risks-render` AND `risks-diff`, and only the
        #:   first declares `--write`. Asserting the permissive set there
        #:   would demand fifteen exemptions on an unmutated tree — a table of
        #:   fifteen holes, which is the shape this row was opened to remove.
        self.only = {s: set() for s in self.subs}
        self.cmd_name: str | None = None
        self.flag_constants = self._flat_flag_constants()

    # ── the population, read off the module rather than listed ────────────
    def _flat_flag_constants(self) -> dict[str, frozenset]:
        """Module-level objects that are nothing but flag names.

        `bin/perry-config § TRACK_FLAGS` is the case this exists for: the track
        register's fields ARE flags, minted from the schema, and both the
        declaration and `cmd_track`'s reader are spelled `TRACK_FLAGS` rather
        than as seven literals.

        **The TOP level only, and that is what keeps `SURFACE` out.** `SURFACE`
        is a module-level object with every flag name somewhere inside it, and
        harvesting it would hand every flag to every subcommand — `perry-tasks
        § main` reads `SURFACE["subcommands"]` in its prologue. It is not
        harvested because its own members are `name`, `kind`, `summary`,
        `flags`, `subcommands`: none of them is flag-shaped, and this walk does
        not descend.

        `all` rather than `any` is the stricter reading of "this object IS a
        flag table", and nothing in `bin/` currently distinguishes the two —
        relaxing it to `any` was mutated on 2026-09-11 and no case moved. It is
        kept as the stricter of two equivalent rules, not because a measurement
        prefers it.
        """
        out: dict[str, frozenset] = {}
        for name in dir(self.module):
            if name.startswith("__"):
                continue
            try:
                obj = getattr(self.module, name)
            except Exception:                        # noqa: BLE001
                continue
            if isinstance(obj, dict):
                members = list(obj)
            elif isinstance(obj, (set, frozenset, list, tuple)):
                members = list(obj)
            else:
                continue
            if not members:
                continue
            if all(isinstance(m, str) and FLAG.match(m) for m in members):
                out[name] = frozenset(members)
        return out

    # ── the walk ──────────────────────────────────────────────────────────
    def read(self, fn: ast.FunctionDef, argv_param: str) -> tuple:
        env = {argv_param: Val(container=True)}
        self._stmts(fn.body, self.subs, env, 0, frozenset({fn.name}))
        return ({s: frozenset(v) for s, v in self.out.items()},
                {s: frozenset(v) for s, v in self.only.items()})

    def _emit(self, active, flags):
        if not flags:
            return
        for s in active:
            self.out[s].update(flags)
        if len(active) == 1:
            self.only[next(iter(active))].update(flags)

    def _narrow(self, test, env):
        """`(names this test selects, is the test PURELY that selection)`.

        `None` for a test that says nothing about `cmd`. The second half is
        what licenses fall-through: `if cmd in (…) and not store.exists():`
        selects those names but does not exhaust them, so the statements after
        it are still reachable for every one.
        """
        if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
            got, pure = None, False
            for part in test.values:
                sel, _ = self._narrow(part, env)
                if sel is not None:
                    got = sel if got is None else (got & sel)
            return got, pure
        if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            sel, pure = self._narrow(test.operand, env)
            return (None if sel is None else self.subs - sel), pure
        if isinstance(test, ast.Compare) and len(test.ops) == 1:
            left, op, right = test.left, test.ops[0], test.comparators[0]
            if isinstance(left, ast.Name) and left.id == self.cmd_name:
                names = self._compared_names(right)
                if not names:
                    # A comparison against something this reader cannot read
                    # narrows NOTHING, and saying so is the only safe answer:
                    # `perry-config § main` guards its chain with `if cmd not
                    # in COMMANDS`, and reading that as "against no names at
                    # all" made every statement after it unreachable — the
                    # whole tool came back reading no flags, and every
                    # direction-B case passed vacuously.
                    return None, False
                if isinstance(op, (ast.Eq, ast.In)):
                    return names, True
                if isinstance(op, (ast.NotEq, ast.NotIn)):
                    return (self.subs - names), True
            return None, False
        if isinstance(test, ast.Name):
            val = env.get(test.id)
            if val is not None and val.disc is not None:
                return frozenset(s for s in self.subs if val.disc.get(s)), True
        return None, False

    def _compared_names(self, node) -> frozenset:
        """The subcommand names a `cmd == …` / `cmd in …` compares against.

        The literals, and only the literals. A comparison against a NAME —
        `perry-config`'s `if cmd not in COMMANDS` — yields nothing here, and
        `_narrow`'s empty-set guard turns that into "this test narrows
        nothing", which is both safe and, for that particular test, exact:
        `COMMANDS` is every subcommand, so `not in COMMANDS` selects none of
        them. Resolving the name was tried and removed — mutating it away moved
        no case, because the guard already gives the right answer.
        """
        return frozenset(_names_in(node)) & self.subs

    def _stmts(self, body, active, env, depth, seen):
        for node in body:
            if not active:
                return
            active = self._stmt(node, active, env, depth, seen)

    def _stmt(self, node, active, env, depth, seen):
        if isinstance(node, ast.If):
            # The test itself runs for everything `active` still holds.
            self._expr(node.test, active, env, depth, seen)
            sel, pure = self._narrow(node.test, env)
            body_active = active if sel is None else (active & sel)
            else_active = active if sel is None else (active - sel)
            self._stmts(node.body, body_active, dict(env), depth, seen)
            if node.orelse:
                self._stmts(node.orelse, else_active, dict(env), depth, seen)
            if sel is not None and pure and _terminates(node.body):
                return else_active
            return active
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                self._expr(item.context_expr, active, env, depth, seen)
            self._stmts(node.body, active, env, depth, seen)
            return active
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            self._expr(getattr(node, "iter", None) or node.test,
                       active, env, depth, seen)
            self._stmts(node.body, active, dict(env), depth, seen)
            self._stmts(node.orelse, active, dict(env), depth, seen)
            return active
        if isinstance(node, ast.Try):
            self._stmts(node.body, active, env, depth, seen)
            for h in node.handlers:
                self._stmts(h.body, active, dict(env), depth, seen)
            self._stmts(node.orelse, active, env, depth, seen)
            self._stmts(node.finalbody, active, env, depth, seen)
            return active
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            self._assign(node.targets[0], node.value, active, env, depth, seen)
            return active
        if isinstance(node, ast.AnnAssign) and node.value is not None:
            self._assign(node.target, node.value, active, env, depth, seen)
            return active
        for child in _subexprs(node):
            self._expr(child, active, env, depth, seen)
        return active

    def _assign(self, target, value, active, env, depth, seen):
        """A binding defers: the flags land where the NAME is used.

        `perry-config § main` computes `dry_run` above the chain and hands it
        to four of the five branches; attributing it at the assignment would
        say `show` reads `--dry-run`, and a declaration that grew `--dry-run`
        on `show` would then be unfalsifiable.
        """
        if (isinstance(target, ast.Tuple) and isinstance(value, ast.Tuple)
                and len(target.elts) == len(value.elts)):
            for t, v in zip(target.elts, value.elts):
                self._assign(t, v, active, env, depth, seen)
            return
        val = self._expr(value, active, env, depth, seen, bind=True)
        if isinstance(target, ast.Name):
            if self.cmd_name is not None and target.id == self.cmd_name:
                # `perry-tasks` rewrites `cmd` when `--register` names one.
                # The name keeps its role; the rewrite is an alias, not a new
                # variable.
                return
            env[target.id] = val
            return
        self._emit(active, val.flags)

    def _expr(self, node, active, env, depth, seen, bind=False) -> Val:
        """Evaluate for two things at once: what runs NOW, and what is carried.

        `bind` says the result is about to be given a name, so the flags it
        carries are not yet read by anything.
        """
        if node is None:
            return EMPTY
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str) and FLAG.match(node.value):
                val = Val(flags={node.value})
                if not bind:
                    self._emit(active, val.flags)
                return val
            return EMPTY
        if isinstance(node, ast.Name):
            val = env.get(node.id)
            if val is not None:
                if not bind and val.flags:
                    self._emit(active, val.flags)
                return val
            table = self.flag_constants.get(node.id)
            if table is not None:
                if not bind:
                    self._emit(active, table)
                return Val(flags=table)
            return EMPTY
        if isinstance(node, ast.Subscript):
            base = self._expr(node.value, active, env, depth, seen, bind=True)
            key = None
            if isinstance(node.slice, ast.Constant):
                key = node.slice.value
            if base.container and key in ("seen", "values"):
                return Val(container=True)
            if base.container and key == "sub":
                return Val()                 # the subcommand, not a flag
            self._expr(node.slice, active, env, depth, seen, bind=bind)
            return Val(flags=base.flags, container=base.container)
        if isinstance(node, ast.Call):
            return self._call(node, active, env, depth, seen, bind)
        if isinstance(node, ast.Compare):
            # `"--dry-run" in seen` — the flag is read here and the RESULT is a
            # boolean that carries it onward.
            got = set()
            for part in [node.left, *node.comparators]:
                got |= self._expr(part, active, env, depth, seen,
                                  bind=bind).flags
            if (isinstance(node.left, ast.Name)
                    and node.left.id == self.cmd_name and len(node.ops) == 1):
                sel, _ = self._narrow(node, env)
                if sel is not None:
                    return Val(disc={s: s in sel for s in self.subs})
            return Val(flags=got)
        if isinstance(node, (ast.BoolOp, ast.UnaryOp, ast.BinOp, ast.IfExp)):
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                inner = self._expr(node.operand, active, env, depth, seen, bind)
                if inner.disc is not None:
                    return Val(flags=inner.flags,
                               disc={s: not v for s, v in inner.disc.items()})
                return inner
            got = set()
            for child in _subexprs(node):
                got |= self._expr(child, active, env, depth, seen, bind).flags
            return Val(flags=got)
        got = set()
        for child in _subexprs(node):
            got |= self._expr(child, active, env, depth, seen, bind).flags
        return Val(flags=got)

    def _call(self, node, active, env, depth, seen, bind) -> Val:
        """A call to a handler in this module is walked; anything else is not.

        The arguments are evaluated with `bind=True` — they travel into the
        parameters rather than being read at the call site (this module's
        docstring, point 3).
        """
        args = [self._expr(a, active, env, depth, seen, bind=True)
                for a in node.args]
        kwargs = {k.arg: self._expr(k.value, active, env, depth, seen,
                                    bind=True)
                  for k in node.keywords if k.arg}
        # **The RECEIVER of a method call carries flags too.**
        # `bin/perry-config § cmd_track` consults the track flags exactly once,
        # as `values.items()`, and a walk that reads only the arguments sees an
        # empty call and reports `track` as reading nothing — every one of the
        # eight track flags then passes direction B vacuously.
        recv = (self._expr(node.func.value, active, env, depth, seen, bind=True)
                if isinstance(node.func, ast.Attribute) else EMPTY)
        # **Only a BARE name is followed into this module's own handlers.**
        # `node.func.attr` would resolve `perry_store.render(b, r, m)` to
        # `bin/perry-tasks`' OWN module-level `render` — a different function
        # with the same last name — and attribute whatever it reads to the
        # caller. No case moves today if this is relaxed (mutated 2026-09-11:
        # the two collisions in `bin/`, `render` and `plan`, contain no flag);
        # it is the rule that is right rather than the rule that is currently
        # load-bearing, and the alternative is right only by accident.
        name = node.func.id if isinstance(node.func, ast.Name) else None
        target = self.funcs.get(name) if name else None
        given = [*args, *kwargs.values(), recv]
        carried = set().union(*(v.flags for v in given), set())
        if (target is None or depth + 1 >= MAX_DEPTH or name in seen
                or not any(v for v in given)):
            # Not a handler of ours, too deep, or passed nothing that came from
            # the vector. The flags its arguments carried are read HERE, since
            # nothing downstream will account for them.
            if carried and not bind:
                self._emit(active, carried)
            return Val(flags=carried)
        inner = self._bind_params(target, args, kwargs)
        self._stmts(target.body, active, inner, depth + 1, seen | {name})
        return EMPTY

    @staticmethod
    def _bind_params(fn, args, kwargs) -> dict:
        env: dict[str, Val] = {}
        names = ([a.arg for a in fn.args.posonlyargs]
                 + [a.arg for a in fn.args.args])
        for i, val in enumerate(args):
            if i < len(names):
                env[names[i]] = val
        for key, val in kwargs.items():             # keyword-only included
            env[key] = val
        return env


# ── the population, and where each tool's chain lives ──────────────────────

#: One parse per file per process, the way `tests/inproc § load` keeps one
#: import. `is_chain_tool` is asked about every declaring tool several times
#: over a run and `bin/perry-task` is 8,540 lines; without this each ask
#: re-parsed it — and re-printed the `DeprecationWarning` its line 1447 raises,
#: which turned one line of pre-existing noise into four.
_TREES: dict[Path, "ast.Module | None"] = {}


def _parse(path: Path):
    if path not in _TREES:
        try:
            _TREES[path] = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            _TREES[path] = None
    return _TREES[path]


def dispatch_site(tool_path: Path, bin_dir: Path):
    """`(source, tree, the function that reads the vector, its argv parameter)`.

    Derived rather than listed: the dispatch is the function that calls
    `lib.parse_surface`. `bin/perry-okr` has no such call — it is
    `bin/perry_md_store.py` under another name, reached by `store.main(…)` —
    so the hand-off is followed to the module that does. `None` when the file
    neither parses a surface nor hands off to something that does.
    """
    seen_files = set()
    path = tool_path
    while path not in seen_files:
        seen_files.add(path)
        tree = _parse(path)
        if tree is None:
            return None
        for fn in tree.body:
            if not isinstance(fn, ast.FunctionDef):
                continue
            for n in ast.walk(fn):
                if (isinstance(n, ast.Call)
                        and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "parse_surface"):
                    argv = (n.args[1].id if len(n.args) > 1
                            and isinstance(n.args[1], ast.Name) else "argv")
                    return path, tree, fn, argv
        nxt = _delegate(tree, bin_dir)
        if nxt is None:
            return None
        path = nxt
    return None


def _delegate(tree, bin_dir: Path):
    """The sibling module this file's `main` hands the whole call to."""
    aliases = {}
    for n in tree.body:
        if isinstance(n, ast.Import):
            for a in n.names:
                aliases[a.asname or a.name] = a.name
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef) or fn.name != "main":
            continue
        for n in ast.walk(fn):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "main"
                    and isinstance(n.func.value, ast.Name)):
                mod = aliases.get(n.func.value.id)
                cand = bin_dir / f"{mod}.py" if mod else None
                if cand is not None and cand.is_file():
                    return cand
    return None


def subcommand_variable(fn):
    """The LOCAL the parse result's `"sub"` was put in — `cmd`, in all three.

    `None` when there is none, and that is the population test rather than an
    error: `bin/perry-task` writes it to an ATTRIBUTE (`a.cmd = read["sub"]`)
    and dispatches through a table of handler functions, so it is read by
    `tests/test_bin_surface § TestPerryTaskDeclaresTheFlagsItsHandlersRead`
    and not here. A tool that lands in neither is the case the population
    control exists to fail on.
    """
    for node in ast.walk(fn):
        if not isinstance(node, ast.Assign):
            continue
        target, value = node.targets[0], node.value
        pairs = (list(zip(target.elts, value.elts))
                 if isinstance(target, ast.Tuple) and isinstance(value, ast.Tuple)
                 and len(target.elts) == len(value.elts) else [(target, value)])
        for t, v in pairs:
            if (isinstance(t, ast.Name) and isinstance(v, ast.Subscript)
                    and isinstance(v.slice, ast.Constant)
                    and v.slice.value == "sub"):
                return t.id
    return None


def is_chain_tool(tool: str, bin_dir: Path, module) -> bool:
    """Does this reader serve `tool`?

    Three conditions, all read off the tool: it declares subcommands, its
    vector is read by `lib.parse_surface`, and the result's `"sub"` lands in a
    local the body then branches on. Nothing here names a tool.
    """
    surface = getattr(module, "SURFACE", None)
    if not isinstance(surface, dict) or not surface.get("subcommands"):
        return False
    site = dispatch_site(bin_dir / tool, bin_dir)
    if site is None:
        return False
    return subcommand_variable(site[2]) is not None


def is_table_tool(module) -> bool:
    """The OTHER dispatch shape: a `COMMANDS` map from name to handler.

    `bin/perry-task`'s, and the one its own AST walk is written against. Read
    as a property of the module so the two populations together can be
    asserted to cover every declaring tool.
    """
    table = getattr(module, "COMMANDS", None)
    return (isinstance(table, dict) and bool(table)
            and all(callable(v) for v in table.values()))


def flags_read(tool: str, bin_dir: Path, module):
    """`(reads, exclusive_reads, the file the chain is in)` for one tool.

    `reads[sub]` is every flag that can reach code `sub` runs; `exclusive[sub]`
    is the subset read where no other subcommand goes. `Reader.only`'s note
    says why the two directions need different sets.
    """
    site = dispatch_site(bin_dir / tool, bin_dir)
    if site is None:
        raise AssertionError(
            f"{tool}: no `lib.parse_surface` call here or in the module this "
            f"file hands off to, so nothing holds its declaration to its code")
    path, tree, fn, argv = site
    cmd_name = subcommand_variable(fn)
    if cmd_name is None:
        raise AssertionError(
            f"{tool}: {fn.name} never puts the parse result's 'sub' in a "
            f"local, so this reader cannot tell which statements belong to "
            f"which subcommand")
    subs = [s["name"] for s in module.SURFACE.get("subcommands", ())]
    reader = Reader(tree, _module_at(path, module), subs)
    reader.cmd_name = cmd_name
    reads, only = reader.read(fn, argv)
    return reads, only, path


def _module_at(path: Path, fallback):
    """The imported module whose source `path` is — for its flag tables.

    `bin/perry-okr`'s chain lives in `bin/perry_md_store.py`, so the constants
    worth harvesting (`TRACK_FLAGS` and its kind) are that module's and not the
    thin wrapper's.
    """
    if not path.name.endswith(".py"):
        return fallback
    import importlib
    try:
        return importlib.import_module(path.stem)
    except Exception:                                # noqa: BLE001
        return fallback
