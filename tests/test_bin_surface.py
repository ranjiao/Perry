"""DESIGN-016 C1 — the declaration and the code agree, in both directions.

`SURFACE` inside each tool is what its parser reads, what `--describe --json`
prints, what `bin/perry list` indexes and what the generated usage block says.
That is only safe while the declaration and the code cannot drift, so this
module holds them together:

- every declared subcommand is REACHABLE — the tool dispatches it;
- every dispatchable subcommand is DECLARED — nothing is reachable and unlisted;
- for `perry-task`, every flag a handler reads is declared for that subcommand,
  re-derived from the source rather than trusted. That direction is the one
  that matters: `--kr` and `--design` were each accepted by a flat 46-flag
  table and dropped by the handler, twice, and nothing compared the two.

Run: python3 tests/parallel -j 4 test_bin_surface
"""

from __future__ import annotations

import ast
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(os.environ.get("PERRY_HOME")
                  or Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(PERRY_HOME / "tests"))
sys.path.insert(0, str(PERRY_HOME / "bin"))
sys.path.insert(0, str(PERRY_HOME / "viewer"))

import inproc  # noqa: E402
import surface_reads  # noqa: E402
from task_writer_support import Project  # noqa: E402
import lib  # noqa: E402

BIN = PERRY_HOME / "bin"
PERRY = BIN / "perry"

#: The tools that declare a surface today. `bin/perry list` reports the rest as
#: undeclared rather than hiding them, and this list is what C1 has converted.
DECLARED = ("perry-task", "perry-tasks", "perry-okr", "perry-config",
            "perry-state", "perry-diagnose")


def _tools_with_a_surface() -> list[str]:
    """Every executable in `bin/` that declares a `SURFACE`, off the directory.

    `DECLARED` above is the list C1 converted and is asserted against THIS, so
    a seventh tool that grows a declaration joins the population by existing
    rather than by somebody remembering to type its name. TASK-411: this
    repository has been bitten repeatedly by a guard that hard-codes what it
    should discover.
    """
    out = []
    for path in sorted(BIN.iterdir()):
        if not path.is_file() or path.suffix in (".md", ".json", ".pyc"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # The textual pass first, so this does not import all eighteen tools
        # to ask six of them a question. A tool whose declaration is BUILT
        # rather than written out is still caught — `bin/perry-okr` is
        # `SURFACE = store.surface(store.OKR)` — because what is matched is the
        # binding and not its right-hand side.
        if not re.search(r"^SURFACE\s*=", text, re.M):
            continue
        try:
            mod = inproc.load(path.name)
        except Exception:                                # noqa: BLE001
            continue
        if isinstance(getattr(mod, "SURFACE", None), dict):
            out.append(path.name)
    return out


def run(tool: str, *argv: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("PERRY_PROJECT", None)
    return subprocess.run([sys.executable, str(BIN / tool), *argv],
                          capture_output=True, text=True, env=env)


def surface(tool: str) -> dict:
    return inproc.load(tool).SURFACE


class TestEveryDeclarationIsWellFormed(unittest.TestCase):

    def test_declared_is_every_tool_that_declares(self):
        """`DECLARED` is a list, so it can fall behind `bin/`.

        A seventh tool that grows a `SURFACE` and is not typed in above would
        be checked by nothing in this module — well-formedness, both dispatch
        directions, the usage block, `--describe`, all of it — and the suite
        would stay green because every case iterates the list. So the list is
        held against the directory (TASK-411).
        """
        self.assertEqual(sorted(DECLARED), _tools_with_a_surface())

    def test_check_surface_finds_nothing(self):
        for tool in DECLARED:
            with self.subTest(tool=tool):
                self.assertEqual(lib.check_surface(surface(tool)), [])

    def test_the_name_is_the_file_name(self):
        for tool in DECLARED:
            with self.subTest(tool=tool):
                self.assertEqual(surface(tool)["name"], tool)

    def test_every_subcommand_has_a_summary(self):
        for tool in DECLARED:
            for sub in surface(tool).get("subcommands", ()):
                with self.subTest(tool=tool, sub=sub["name"]):
                    self.assertTrue(sub.get("summary"),
                                    "a line in `perry list` with nothing on it")


class TestDeclaredAndDispatchableAreTheSameSet(unittest.TestCase):
    """Neither direction alone is enough: a declaration listing a subcommand
    nobody dispatches sends a caller at a refusal, and a subcommand nobody
    declares is now unreachable, because the parser refuses what the
    declaration does not list."""

    def test_every_declared_subcommand_is_reached(self):
        """Behavioural, not a regex over the dispatch: each subcommand is RUN
        against an empty project, and what is asserted is that the tool did not
        answer "that is not a subcommand". Whatever else it says — a refusal, a
        missing file, an empty store — means the name reached its handler."""
        with tempfile.TemporaryDirectory() as empty:
            for tool in ("perry-task", "perry-tasks", "perry-okr",
                         "perry-config"):
                for sub in surface(tool).get("subcommands", ()):
                    with self.subTest(tool=tool, sub=sub["name"]):
                        out = subprocess.run(
                            [sys.executable, str(BIN / tool), sub["name"],
                             "--root", empty],
                            capture_output=True, text=True)
                        blob = out.stdout + out.stderr
                        self.assertNotIn("is not a subcommand", blob)
                        self.assertNotIn("expected one of", blob)
                        self.assertNotIn("expected build", blob)

    def test_a_name_that_is_not_declared_is_refused(self):
        """The control for the case above: the refusal it looks for is
        reachable, so a tool that never refuses anything cannot pass."""
        for tool in ("perry-task", "perry-tasks", "perry-okr", "perry-config"):
            with self.subTest(tool=tool):
                out = subprocess.run(
                    [sys.executable, str(BIN / tool), "no-such-subcommand"],
                    capture_output=True, text=True)
                self.assertEqual(out.returncode, 2)

    def test_every_name_the_source_dispatches_is_declared(self):
        """The other direction, read off each tool's own command table.

        **`perry-tasks` has no table** — it dispatches through a chain of
        `if cmd == …` in `main` — so its seventeen subcommands were in neither
        direction of this class until a V4 review deleted `asks-diff` from the
        declaration, made it unreachable, and watched the suite stay green.
        Its names are read out of the source instead.
        """
        for tool, names in (
                ("perry-task", set(inproc.load("perry-task").COMMANDS)),
                ("perry-config", set(inproc.load("perry-config").COMMANDS)),
                ("perry-okr", set(inproc.load("perry-okr").store.COMMANDS)),
                ("perry-tasks", self._dispatched_by_perry_tasks())):
            declared = {s["name"] for s in surface(tool).get("subcommands", ())}
            for name in sorted(names):
                with self.subTest(tool=tool, sub=name):
                    self.assertIn(name, declared)

    def _dispatched_by_perry_tasks(self) -> set[str]:
        """Every literal `main` compares `cmd` against, from the source."""
        text = (BIN / "perry-tasks").read_text(encoding="utf-8")
        body = text[text.index("def main(argv"):]
        names = set(re.findall(r'cmd == "([a-z-]+)"', body))
        for group in re.findall(r"cmd in \(([^)]*)\)", body):
            names |= set(re.findall(r'"([a-z-]+)"', group))
        # `build` and `verify` are the fall-through at the end of `main`; they
        # are compared with `==` too, so nothing special is needed — but assert
        # the extraction found the shape it expects rather than nothing.
        self.assertGreaterEqual(len(names), 12,
                                f"the extraction found {sorted(names)}, which "
                                f"is not perry-tasks' dispatch")
        return names

    #: `(tool, argv, a string only THIS subcommand's own handler produces)`.
    #: Reaching *a* handler is not reaching the right one: a V4 review disabled
    #: `perry-config`'s `untrack` branch and watched it fall through to the
    #: `track` writer — `track 'alpha' — … now holds 1 record(s)`, exit 0, the
    #: track still there — then did the same to `unset` into `show`, and to
    #: three `perry-tasks` registers. The reachability check above passed every
    #: time, because none of those says "is not a subcommand".
    OWN_OUTPUT = (
        ("perry-config", ("show",), "Document language"),
        ("perry-config", ("set", "Chat language", "English"), "set 'Chat"),
        ("perry-config", ("unset", "Chat language"), "unset 'Chat"),
        ("perry-config", ("track", "alpha", "--mode", "project"), "track 'alpha'"),
        ("perry-config", ("untrack", "alpha"), "untrack 'alpha'"),
        # For the registers the fingerprint is the STORE PATH the verb would
        # write: `build` and `risks-build` print the same key set, so a key
        # cannot tell them apart, and the file each one owns can.
        ("perry-tasks", ("write", "--from-board", "--dry-run", "--json"),
         "tasks.jsonl"),
        ("perry-tasks", ("risks-write", "--from-board", "--dry-run", "--json"),
         "risks.jsonl"),
        ("perry-tasks", ("intake-write", "--from-board", "--dry-run", "--json"),
         "intake.jsonl"),
        ("perry-tasks", ("asks-write", "--from-board", "--dry-run", "--json"),
         "asks.jsonl"),
        ("perry-tasks", ("asks-build",), '"unanswered"'),
        # TASK-237 D1: `board` prints the TEMPLATE's title, placeholder and all,
        # which no board on disk carries — so `render` answering cannot pass.
        ("perry-tasks", ("board",), "# Board — {{project name}}"),
    )

    def test_every_declared_subcommand_runs_its_own_verb(self):
        """Not "a handler answered" — THIS subcommand's handler answered."""
        p = Project()
        for tool, argv, fingerprint in self.OWN_OUTPUT:
            with self.subTest(command=f"{tool} {' '.join(argv)}"):
                out = run(tool, *argv, "--root", str(p.root))
                self.assertIn(fingerprint, out.stdout + out.stderr,
                              f"{tool} {argv[0]} produced another verb's "
                              f"output:\n" + (out.stdout + out.stderr)[:300])

    def test_a_removal_that_removes_nothing_is_refused(self):
        """The other half of the same defect: the verb ran, and did nothing."""
        p = Project()
        out = run("perry-config", "unset", "No Such Setting",
                  "--root", str(p.root))
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("nothing was written", out.stderr)
        out = run("perry-config", "untrack", "no-such-track",
                  "--root", str(p.root))
        self.assertEqual(out.returncode, 1, out.stdout)


class TestPerryTaskDeclaresTheFlagsItsHandlersRead(unittest.TestCase):
    """The direction `--kr` and `--design` broke, re-derived rather than
    trusted: walk each handler's AST for `args.<attr>` reads, map them back to
    flags, and require the declaration to list them."""

    @classmethod
    def setUpClass(cls):
        cls.src = (BIN / "perry-task").read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.src)
        cls.funcs = {n.name: n for n in cls.tree.body
                     if isinstance(n, ast.FunctionDef)}
        seg = cls.src[cls.src.index("def parse(argv"):
                      cls.src.index("# The single source of truth")]
        cls.flag_of = {}
        for flag, attr in re.findall(r'"(--[a-z-]+)":\s*"([a-z_]+)"', seg):
            cls.flag_of.setdefault(attr, flag)
        for flag, attr in (("--dry-run", "dry_run"), ("--json", "as_json"),
                           ("--all", "all"), ("--clear", "clear"),
                           ("--unlinked", "unlinked")):
            cls.flag_of.setdefault(attr, flag)

    def _reads(self, node, depth=0, seen=None):
        seen = seen if seen is not None else set()
        out = set()
        for n in ast.walk(node):
            if (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                    and n.value.id == "args"):
                out.add(n.attr)
            if isinstance(n, ast.Call) and depth < 2:
                name = (n.func.id if isinstance(n.func, ast.Name)
                        else n.func.attr if isinstance(n.func, ast.Attribute)
                        else None)
                passes = any(isinstance(a, ast.Name) and a.id == "args"
                             for a in n.args) or any(
                    isinstance(k.value, ast.Name) and k.value.id == "args"
                    for k in n.keywords)
                if name in self.funcs and name not in seen and passes:
                    seen.add(name)
                    out |= self._reads(self.funcs[name], depth + 1, seen)
        return out

    #: `cell_writer(field, flag, …)` builds its handler as a closure over
    #: `getattr(args, flag)`, which no AST walk can see. The flag is the call's
    #: second argument, so it is read from the call site instead.
    CELL_WRITERS = dict(re.findall(
        r'^cmd_([a-z_]+) = cell_writer\(\s*"[a-z_ ]+",\s*"([a-z_]+)"',
        (BIN / "perry-task").read_text(encoding="utf-8"), re.M))

    def test_every_flag_a_handler_reads_is_declared_for_that_subcommand(self):
        face = surface("perry-task")
        universal = lib.always_accepted(face)
        table = re.findall(r'"([a-z-]+)": (cmd_[a-z_]+)',
                           self.src[self.src.index("COMMANDS = {"):
                                    self.src.index("def project_lock")])
        for name, fn in table:
            sub = lib.surface_subcommand(face, name)
            with self.subTest(sub=name):
                self.assertIsNotNone(sub, f"{name} is dispatched and undeclared")
                declared = set(sub.get("flags", ())) | universal
                if fn in self.funcs:
                    attrs = self._reads(self.funcs[fn])
                else:                       # a `cell_writer` closure
                    attrs = {self.CELL_WRITERS[fn.removeprefix("cmd_")],
                             "actor", "dry_run"}
                wanted = {self.flag_of[a] for a in attrs if a in self.flag_of}
                missing = sorted(wanted - declared - {"--root"})
                self.assertEqual(missing, [],
                                 f"{name} reads {missing} and does not declare "
                                 f"them, so the parser refuses what the handler "
                                 f"wants")

    def test_every_flag_it_declares_for_a_subcommand_is_read_by_that_handler(self):
        """The OTHER direction, and until a V4 round nothing checked it.

        A flag declared for a subcommand whose handler never reads it is
        accepted, silently dropped, and published by `--describe` as part of
        that subcommand's contract — the same harm as § 1.4's, arrived at from
        the opposite side. The reviewer declared `--rung` on `start`, whose
        `cmd_start` never reads it, and all 3,440 tests stayed green while
        `perry-task start TASK-001 --rung V4` exited 0 and stored `rung=None`.

        `--kr`'s and `--design`'s guard was a hand-written table of ten
        `(tool, sub, flag)` rows against a negative space of 1,277 pairs.
        This derives the answer for all 30 of this tool's subcommands.
        """
        face = surface("perry-task")
        universal = lib.always_accepted(face)
        table = re.findall(r'"([a-z-]+)": (cmd_[a-z_]+)',
                           self.src[self.src.index("COMMANDS = {"):
                                    self.src.index("def project_lock")])
        for name, fn in table:
            sub = lib.surface_subcommand(face, name)
            with self.subTest(sub=name):
                if fn in self.funcs:
                    attrs = self._reads(self.funcs[fn])
                else:
                    attrs = {self.CELL_WRITERS[fn.removeprefix("cmd_")],
                             "actor", "dry_run"}
                read = {self.flag_of[a] for a in attrs if a in self.flag_of}
                declared = set(sub.get("flags", ())) - universal - {"--root"}
                unread = sorted(declared - read - self.INDIRECT.get(name, set()))
                self.assertEqual(
                    unread, [],
                    f"{name} declares {unread}, no code under cmd_{name} "
                    f"reads them, and the parser accepts them anyway")

    #: Flags a handler genuinely honours through a path no AST walk can see —
    #: a closure, a `**kwargs` hand-off, or a helper reached more than two
    #: calls deep. **Each entry is a hole in the check above**, so each one
    #: names the line that does the reading; an entry with no such line is a
    #: defect being waved through.
    INDIRECT: dict = {}

    def test_the_derivation_finds_something(self):
        """The control: if `_reads` returned nothing the case above would pass
        for every subcommand and prove nothing."""
        self.assertIn("title", self._reads(self.funcs["cmd_add"]))


class TestTheChainToolsDeclareTheFlagsTheirBranchesRead(unittest.TestCase):
    """TASK-411 — the same two directions, for every tool that is NOT
    `perry-task`.

    `134afea6` closed both on `perry-task` and left the rest, because each
    dispatches differently: `perry-tasks` and `perry-config` are `if cmd == …`
    chains in `main`, and `perry-okr` runs `bin/perry_md_store.py`, whose
    declaration is built by a FUNCTION of the document rather than written as a
    literal. Measured then: direction B planted on all six declaring tools at
    once and **3,440 tests stayed green**, while `perry-task start TASK-001
    --rung V4` exited 0, printed `wrote TASK-001 (start)` and stored
    `rung=None`; and `--wip` dropped from `perry-config track`'s declared flags
    while `bin/perry-config` still read it left the suite at baseline.

    **One reader, not four.** `tests/surface_reads.py` derives the answer for
    all three chain bodies from the one thing they have in common: they read a
    flag by its literal spelling out of the `lib.parse_surface` result, so
    "does this subcommand read this flag" is "can that spelling reach code this
    subcommand runs". Four readers invented at once is how a guard ends up
    wrong in a way nobody checks, so the shape is held here by its own numbers:
    the population is derived, the over-report is measured and bounded, and the
    escape hatch is empty.

    `perry-state` and `perry-diagnose` are not here and are not excluded by
    name: they declare zero subcommands, so `is_chain_tool` does not select
    them, and `test_every_declaring_tool_is_read_by_one_of_the_two_readers`
    says what that leaves.
    """

    @classmethod
    def setUpClass(cls):
        cls.tools = []
        for tool in _tools_with_a_surface():
            mod = inproc.load(tool)
            if surface_reads.is_chain_tool(tool, BIN, mod):
                reads, only, path = surface_reads.flags_read(tool, BIN, mod)
                cls.tools.append((tool, mod, reads, only, path))

    def _pairs(self):
        """`(tool, subcommand, declared flags, reads, exclusive reads)`.

        Derived from each tool's own declaration — no list of subcommands is
        written down here, because a guard that hard-codes what it should
        discover is a guard against the rows that already had the bug.

        The flags every subcommand takes come off all three sets, not just off
        the declared one. `lib.always_accepted` is the answer to "this flag is
        honoured in `main`, for everything" — `--root`, `--json` on
        `perry-config` — and a direction that counted those as read by one
        subcommand and declared by none would report every subcommand of every
        tool.
        """
        for tool, mod, reads, only, _path in self.tools:
            face = mod.SURFACE
            universal = lib.always_accepted(face) | {"--root"}
            for sub in face["subcommands"]:
                name = sub["name"]
                yield (tool, name, set(sub.get("flags", ())) - universal,
                       set(reads[name]) - universal,
                       set(only[name]) - universal)

    def test_every_flag_it_declares_for_a_subcommand_is_read_under_that_subcommand(self):
        """Direction B: a declared flag no branch of this subcommand consults.

        It is accepted, silently dropped, and published by `--describe` as part
        of that subcommand's contract — DESIGN-016 § 1.4's shape, and the
        complaint the whole design was opened on. The permissive read set is
        the right one here: `perry-tasks build --register` is consulted once,
        in a prologue all seventeen subcommands run, and it is honoured there.
        """
        for tool, name, declared, reads, _only in self._pairs():
            with self.subTest(tool=tool, sub=name):
                unread = sorted(declared - reads
                                - self.INDIRECT.get((tool, name), set()))
                self.assertEqual(
                    unread, [],
                    f"{tool} {name} declares {unread}, no code this "
                    f"subcommand can reach reads them, and the parser accepts "
                    f"them anyway")

    def test_every_flag_only_this_subcommand_reads_is_declared_by_it(self):
        """Direction A: the parser refuses a flag the handler wants.

        **Exclusive reads, and that is the whole of the difference.** A flag
        consulted in code several subcommands share says nothing about which of
        them wants it — `cmd_risks_render`'s storeless branch tests
        `write_board` for `risks-render` and `risks-diff` alike, and only the
        first declares `--write`. Asserting the permissive set would demand
        fifteen exemptions on an unmutated tree, which is a table of fifteen
        holes. Asserting the exclusive set asks the question that has an
        answer: there is code ONLY this subcommand runs, it consults this flag,
        and the declaration does not carry it.
        """
        for tool, name, declared, _reads, only in self._pairs():
            with self.subTest(tool=tool, sub=name):
                missing = sorted(only - declared)
                self.assertEqual(
                    missing, [],
                    f"{tool} {name} reads {missing} in code no other "
                    f"subcommand runs and does not declare them, so the "
                    f"parser refuses what the handler wants")

    #: Flags a subcommand genuinely honours through a path `surface_reads`
    #: cannot follow — a `getattr`, a table built at runtime, a helper deeper
    #: than `MAX_DEPTH`. **Each entry is a hole in direction B**, keyed
    #: `(tool, subcommand)`, and each one must name the line that does the
    #: reading; an entry with no such line is a defect being waved through.
    #: `perry-task`'s equivalent is empty and so is this.
    INDIRECT: dict = {}

    def test_the_escape_hatch_is_empty(self):
        """A hatch nobody has to argue for fills up.

        A case that iterated `INDIRECT` and checked the shape of each entry
        would be a loop over nothing today and would keep passing as entries
        arrived. This asserts the emptiness instead, so adding the first entry
        means editing this case and writing down here why the walk cannot see
        that read — which is the argument the entry needs and the commit
        message is not the place for.
        """
        self.assertEqual(
            self.INDIRECT, {},
            "an exemption was added to direction B; say here which line does "
            "the reading and why `surface_reads` cannot follow it")

    def test_the_derivation_does_not_call_every_declared_flag_read(self):
        """The control that matters most, and it is a NUMBER.

        A reader that answers "read" for every pair makes direction B vacuous —
        it would pass with every declaration in the repository doubled. So the
        census is run here rather than quoted from a review: over the whole
        `(subcommand, flag)` universe of the chain tools, what fraction does
        the derivation call read? Measured on `488cf079`: **63 of 149 pairs,
        42.3%**, against a declaration carrying 48 and a vacuous reader's 149.

        The bound is deliberately loose — this is a wall, not a thermometer.
        A derivation that drifted to calling three quarters of the universe
        read has stopped discriminating, whatever else it still passes.
        """
        universe = claimed = declared = 0
        for tool, mod, reads, _only, _path in self.tools:
            face = mod.SURFACE
            universal = lib.always_accepted(face) | {"--root"}
            flags = sorted(set(lib.surface_flags(face)) - universal)
            self.assertTrue(flags, f"{tool} declares no flags of its own")
            for sub in face["subcommands"]:
                decl = set(sub.get("flags", ())) - universal
                for flag in flags:
                    universe += 1
                    claimed += flag in reads[sub["name"]]
                    declared += flag in decl
        self.assertGreater(universe, 100,
                           "the universe collapsed, so the ratio below is "
                           "about nothing")
        self.assertLess(claimed / universe, 0.75,
                        f"the derivation calls {claimed} of {universe} pairs "
                        f"read; at that rate direction B cannot fail")
        self.assertGreaterEqual(
            claimed, declared,
            f"the derivation finds {claimed} reads against {declared} declared "
            f"pairs — fewer reads than declarations means direction B is "
            f"failing above, not that this control is wrong")

    def test_the_pairs_direction_b_cannot_see_are_all_shared_reads(self):
        """Direction B's blind spot, measured and ratcheted.

        A pair the derivation calls read and the declaration does not carry is
        a pair direction B could not fail on: adding that flag to that
        subcommand would pass. **15 such pairs on `488cf079`**, all
        `perry-tasks` — `--register`, consulted in the prologue all seventeen
        subcommands run, and `--write` on the three `*-diff` verbs, whose
        `cmd_*_render` tests `write_board` in its storeless branch before it
        looks at `byte_compare`.

        **None of the fifteen is § 1.4's defect, and that is checkable rather
        than asserted.** The blind pairs are exactly the ones where the tool
        does consult the flag, so declaring one gets it honoured or refused out
        loud — not accepted and dropped. Probed 2026-09-11: `--register` added
        to `risks-build`'s declaration, then `perry-tasks risks-build
        --register intake` → exit 2, `the 'intake' register has no
        'risks-build' — it takes build, diff, render, write.`

        The count is a ceiling, not a record. A refactor that moved a flag's
        only reader into shared code would raise it, and the point of the
        number is that such a move has to be argued for.
        """
        blind = []
        for tool, name, declared, reads, only in self._pairs():
            for flag in sorted(reads - declared):
                blind.append((tool, name, flag))
                self.assertNotIn(
                    flag, only,
                    f"{tool} {name} reads {flag} where no other subcommand "
                    f"goes and does not declare it — direction A is failing "
                    f"above, not this")
        self.assertLessEqual(
            len(blind), 15,
            f"direction B is now blind on {len(blind)} pairs, up from the 15 "
            f"measured on 488cf079: {blind}")

    def test_the_derivation_finds_what_the_source_plainly_reads(self):
        """The other control: `_reads` returning nothing would pass direction B
        for every subcommand and prove nothing.

        Three reads, one per chain body, each a line anyone can check:
        `bin/perry-config § main` builds `track_values` from `TRACK_FLAGS`;
        `bin/perry_md_store § main` tests `"--from-file" not in seen` under
        `write`; `bin/perry-tasks § main` tests `"--from-board" not in argv`
        under `write`.
        """
        got = {(tool, name): reads
               for tool, name, _d, reads, _o in self._pairs()}
        self.assertIn("--mode", got[("perry-config", "track")])
        self.assertIn("--from-file", got[("perry-okr", "write")])
        self.assertIn("--from-board", got[("perry-tasks", "write")])
        self.assertNotIn("--from-board", got[("perry-tasks", "render")],
                         "every flag came back read for every subcommand, so "
                         "the narrowing is not narrowing")

    def test_every_declaring_tool_is_read_by_one_of_the_two_readers(self):
        """Nothing falls between the two shapes unnoticed.

        A tool that declares subcommands is dispatched either from a table of
        handler functions (`perry-task`, read by the class above) or from an
        `if cmd == …` chain (read here). A THIRD shape would be covered by
        neither and nothing would say so — which is how the other five tools
        came to be unguarded in both directions in the first place.
        """
        unread = []
        for tool in _tools_with_a_surface():
            mod = inproc.load(tool)
            if not mod.SURFACE.get("subcommands"):
                continue        # `perry-state`, `perry-diagnose`: tool-level
            if surface_reads.is_chain_tool(tool, BIN, mod):
                continue
            if surface_reads.is_table_tool(mod):
                continue
            unread.append(tool)
        self.assertEqual(unread, [],
                         f"{unread} declare subcommands and dispatch by "
                         f"neither shape, so no reader holds their "
                         f"declaration to their code")

    def test_both_populations_are_occupied(self):
        """The control for the case above: if every tool were a chain tool it
        would pass while saying nothing about the table shape, and vice
        versa."""
        chain, table = [], []
        for tool in _tools_with_a_surface():
            mod = inproc.load(tool)
            if not mod.SURFACE.get("subcommands"):
                continue
            (chain if surface_reads.is_chain_tool(tool, BIN, mod)
             else table if surface_reads.is_table_tool(mod) else []).append(tool)
        self.assertGreaterEqual(len(chain), 3, chain)
        self.assertGreaterEqual(len(table), 1, table)

    def test_the_chain_is_found_in_the_file_that_holds_it(self):
        """`perry-okr` declares and dispatches nothing itself — both are
        `bin/perry_md_store.py`'s, built per document — so a reader that looked
        only at the named file would find no chain and pass on an empty set."""
        where = {tool: path.name for tool, _m, _r, _o, path in self.tools}
        self.assertEqual(where.get("perry-okr"), "perry_md_store.py")
        self.assertEqual(where.get("perry-tasks"), "perry-tasks")


class TestRegisterIsAParameter(unittest.TestCase):
    """DESIGN-016 C5 — `<verb> --register <name>` is the shape; the twelve
    prefixed names are aliases for one release.

    The register list is DERIVED from `schema/state-schema.json § claims` —
    the `work`-owned state stores — so a register and a track are read the same
    way instead of one being data and the other twelve subcommand names
    (§ 1.7).
    """

    def setUp(self):
        self.p = Project()
        self.p.run("add", "--title", "a row so the store has something")
        for sub in ("write --from-board", "risks-write --from-board",
                    "intake-write --from-board", "asks-write --from-board"):
            run("perry-tasks", *sub.split(), "--root", str(self.p.root))

    def test_the_registers_come_from_the_schema(self):
        table = inproc.load("perry-tasks").registers()
        self.assertEqual(set(table), {"tasks", "risks", "intake", "asks"})
        self.assertEqual(table["tasks"], "", "the bare verbs are the task ones")

    def test_the_parameter_and_the_alias_are_the_same_call(self):
        """`render` and `write` are in the list on purpose: making
        `--register` a no-op for those two — `render --register risks --write`
        rewriting the TASK rows — left the suite green when a V4 review tried
        it. The read verbs cannot lose data; those two can.

        What is compared is the WHOLE answer, both streams and the code. Some
        pairs refuse on this fixture (`## Top risks` ships as a bullet list, so
        the import has nothing to read) and a refusal is as good a comparison
        as a success, as long as they are not ALL refusals — `succeeded` is
        that control.
        """
        extra = {"write": ("--from-board",),
                 "render": ("--write", "--dry-run", "--json")}
        succeeded = 0
        for register in ("risks", "intake", "asks"):
            for verb in ("build", "diff", "render", "write"):
                with self.subTest(register=register, verb=verb):
                    args = extra.get(verb, ())
                    a = run("perry-tasks", verb, "--register", register, *args,
                            "--root", str(self.p.root))
                    b = run("perry-tasks", f"{register}-{verb}", *args,
                            "--root", str(self.p.root))
                    self.assertEqual(a.returncode, b.returncode,
                                     a.stderr + b.stderr)
                    self.assertEqual(a.stdout, b.stdout)
                    self.assertEqual(a.stderr, b.stderr)
                    succeeded += a.returncode == 0
        self.assertGreaterEqual(succeeded, 4,
                                "every pair refused, so the comparison never "
                                "reached a call that does anything")

    def test_a_register_that_does_not_exist_names_the_ones_that_do(self):
        out = run("perry-tasks", "build", "--register", "nosuch",
                  "--root", str(self.p.root))
        self.assertEqual(out.returncode, 2)
        for name in ("tasks", "risks", "intake", "asks"):
            self.assertIn(name, out.stderr)

    def test_a_verb_the_register_lacks_says_which_it_has(self):
        """`verify` is the task store's alone: no register has one."""
        out = run("perry-tasks", "verify", "--register", "risks",
                  "--root", str(self.p.root))
        self.assertEqual(out.returncode, 2)
        self.assertIn("has no 'verify'", out.stderr)
        self.assertIn("build", out.stderr)


class TestHelpIsUsageFirstAndSmall(unittest.TestCase):
    """DESIGN-016 C2 and goal 8, and § 4 Decision 2's mitigation.

    `perry-task --help` was 10,690 bytes with `Usage:` at line 51. The essays
    moved into `bin/README.md § The argument, per tool` — moved, not cut — and
    what `--help` prints is generated from `SURFACE`, so it cannot describe a
    flag the parser does not take.
    """

    README = (PERRY_HOME / "bin" / "README.md").read_text(encoding="utf-8")
    MOVED = ("perry-task", "perry-tasks", "perry-config")

    def test_help_starts_with_usage(self):
        for tool in DECLARED:
            with self.subTest(tool=tool):
                out = run(tool, "--help")
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assertTrue(out.stdout.lstrip().startswith("Usage:"),
                                out.stdout[:120])

    def test_one_subcommand_costs_one_call_and_returns_only_that(self):
        for tool in DECLARED:
            subs = surface(tool).get("subcommands", ())
            if len(subs) < 2:
                continue
            with self.subTest(tool=tool):
                out = run(tool, subs[0]["name"], "--help")
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assertIn(subs[0]["name"], out.stdout)
                self.assertNotRegex(
                    out.stdout, rf"\b{re.escape(subs[1]['name'])}\b",
                    "one subcommand's help named another")
                self.assertLess(len(out.stdout), 1200, out.stdout[:200])

    def test_the_whole_tool_help_is_a_page_not_a_paper(self):
        for tool in DECLARED:
            with self.subTest(tool=tool):
                self.assertLess(len(run(tool, "--help").stdout), 3000)

    def test_the_essays_are_in_the_readme_rather_than_gone(self):
        """A sentence from each moved docstring, asserted present. The claim
        Decision 2 was answered on is that the argument MOVED."""
        for phrase in (
                "Every mutating call writes four things",
                "the event log is DERIVED AND DISPOSABLE".lower(),
                "ADR-007's first slice",
        ):
            with self.subTest(phrase=phrase[:40]):
                self.assertIn(phrase.lower(), self.README.lower())

    def test_every_tool_that_moved_its_essay_has_a_section(self):
        for tool in self.MOVED:
            with self.subTest(tool=tool):
                self.assertIn(f"### `{tool}`", self.README)


class TestTheReadmeSaysWhatTheToolsDo(unittest.TestCase):
    """DESIGN-016 D1 and § 4 Decision 2's mitigation — the check that ships
    WITH the move, so the README's drift is reported rather than read.

    § 1.6 counted eight statements in `bin/README.md` that were false on
    2026-09-09, including the file's most prominent write example, which `add`
    refuses.
    """

    README = (PERRY_HOME / "bin" / "README.md").read_text(encoding="utf-8")

    def test_every_tool_in_bin_has_a_row(self):
        for path in sorted(BIN.glob("perry-*")):
            if path.name.endswith(".py") or not path.is_file():
                continue
            with self.subTest(tool=path.name):
                self.assertIn(f"[`{path.name}`]({path.name})", self.README)

    def test_the_add_example_carries_the_flags_add_refuses_without(self):
        """R1's specific claim. The EXECUTION moved to
        `test_every_block_is_either_marked_a_synopsis_or_runs`, which runs this
        block whole rather than its first logical command.

        The first fix asserted these three flag strings appeared in the fence,
        and they did — on continuation lines ending in `\\`, which bash reads
        as a literal backslash, so the block was four commands and the first
        was the same refused call R1 was about. A V4 review caught it by
        running the block; a second V4 review found the runner stopped at the
        first line not ending in a continuation, so breaking the block's LAST
        line stayed green. What survives here is the doubled-backslash check,
        which is the shape a reader cannot see and a runner would only catch
        by accident.
        """
        at = self.README.index('perry-task" add --title')
        block = self.README[self.README.rindex("\n", 0, at) + 1:]
        block = block[:block.index("```")]
        self.assertNotIn("\\\\", block,
                         "a doubled backslash is a literal, not a continuation")
        for flag in ("--deliverable", "--verification", "--summary"):
            self.assertIn(flag, block)

    #: The only two reasons a fenced block may go unrun, and each is checked
    #: rather than believed: `placeholders` requires the block to contain one,
    #: and `runs the suite, not a project` is the single block that invokes
    #: `tests/run` itself. A third reason is a new row, not a new string.
    REASONS = ("placeholders", "runs the suite, not a project")
    MARKER = "<!-- not-executable: "

    def _blocks(self):
        """`(fence line number, body, reason or None)` for every ```bash block."""
        lines = self.README.split("\n")
        out, i = [], 0
        while i < len(lines):
            if lines[i].startswith("```bash"):
                prev = lines[i - 1].strip() if i else ""
                reason = (prev[len(self.MARKER):].removesuffix("-->").strip()
                          if prev.startswith(self.MARKER) else None)
                j = i + 1
                while j < len(lines) and lines[j].strip() != "```":
                    j += 1
                out.append((i + 1, "\n".join(lines[i + 1:j]), reason))
                i = j
            i += 1
        return out

    def test_every_block_is_either_marked_or_runs(self):
        """Criterion 11, over ALL ten fenced blocks rather than one line of one.

        A V4 round ran them: one was not valid bash at all — `perry-decide new
        <slug> --title "…"` makes `bash -n` refuse the whole fence — and two
        more acted on ids a fresh project does not have. The guard that existed
        read the first logical command of a single block, so breaking that
        block's LAST line left the suite green.

        Marked blocks are not skipped silently; the case below holds each
        marker to a reason it can check.
        """
        # **These blocks are real writes, and `PERRY_HOME` has to point at the
        # live checkout for them to run at all.** So the live state files are
        # fingerprinted around every block: an example that resolves the wrong
        # project fails HERE rather than silently opening rows on the board a
        # human is reading. Writing this guard was not optional — an earlier
        # draft of this case put four rows on Perry's own board, TASK-411 to
        # TASK-414, and nothing in the run said so.
        live = [PERRY_HOME / "perry" / "BOARD.md",
                PERRY_HOME / "perry" / "tasks.jsonl",
                PERRY_HOME / ".perry" / "events.jsonl"]
        before = {f: f.read_bytes() for f in live if f.exists()}
        for lineno, body, reason in self._blocks():
            if reason:
                continue
            with self.subTest(line=lineno):
                p = Project()
                p.run("add", "--title", "a row the examples can act on")
                out = subprocess.run(
                    ["bash", "-c", body], capture_output=True, text=True,
                    env={**os.environ, "PERRY_HOME": str(PERRY_HOME),
                         "PERRY_PROJECT": str(p.root)}, cwd=str(p.root))
                self.assertEqual(
                    out.returncode, 0,
                    f"bin/README.md:{lineno} does not run and is not marked:\n"
                    + out.stdout[-400:] + out.stderr[-400:])
                for f, was in before.items():
                    self.assertEqual(
                        f.read_bytes(), was,
                        f"bin/README.md:{lineno} wrote into the LIVE project "
                        f"at {f} — it resolved the checkout, not the scratch "
                        f"project $PERRY_PROJECT names")

    def test_a_marker_cannot_hide_a_broken_example(self):
        """The marker is a fact about the block, not a way to silence this.

        Without this, the fix for the case above is to mark every block. Each
        reason is checked against the block it excuses: `placeholders` must
        find one, and the suite block must actually be the suite.
        """
        marked = [(n, b, r) for n, b, r in self._blocks() if r]
        self.assertGreaterEqual(len(marked), 1, "the marker went unused")
        for lineno, body, reason in marked:
            with self.subTest(line=lineno):
                self.assertIn(reason, self.REASONS,
                              f"bin/README.md:{lineno} gives a reason this "
                              f"test does not know how to check")
                if reason == "placeholders":
                    self.assertTrue(
                        any(tok in body for tok in ("<", "\u2026")),
                        f"bin/README.md:{lineno} claims placeholders and has "
                        f"none — run it instead")
                else:
                    for line in body.splitlines():
                        self.assertTrue(
                            not line.strip() or line.startswith("bash tests/run"),
                            f"bin/README.md:{lineno} is excused as the suite "
                            f"and carries {line!r}")

    def test_the_blocks_are_counted_so_a_new_one_cannot_arrive_unnoticed(self):
        """The bound. Ten today: six run, four carry a stated reason."""
        blocks = self._blocks()
        self.assertEqual(len(blocks), 10, "a fenced block was added or removed")
        self.assertEqual(sum(1 for *_, r in blocks if r), 4)

    def test_the_dependency_claim_matches_the_one_tool_that_has_one(self):
        """R2: "No tool here calls an LLM … no dependencies at all" while
        `perry-codex-preflight` shells out to `codex exec`."""
        preflight = (BIN / "perry-codex-preflight").read_text(encoding="utf-8")
        self.assertIn("codex exec", preflight, "the premise changed")
        self.assertIn("codex exec", self.README)
        # The old sentence survives as a QUOTATION of what it used to say, so
        # the check is that it is no longer the claim: the paragraph that
        # quotes it also says which tool has a dependency and what it needs.
        head = self.README[:self.README.index("## The tools")]
        self.assertIn("which was", head, "the correction paragraph is gone")
        for needed in ("codex", "git", "timeout"):
            self.assertIn(needed, head)

    def test_the_store_census_count_is_the_one_the_linter_prints(self):
        """R6: `perry-lint --help` said SIX while the census printed seven.

        **Counted by running it**, not by grepping the sentence: the number in
        the help text is checked against the number of census lines a real run
        emits, so the two cannot drift again in either direction."""
        out = subprocess.run(
            [sys.executable, str(BIN / "perry-lint"), "--root",
             str(PERRY_HOME)], capture_output=True, text=True)
        printed = len([l for l in out.stdout.splitlines()
                       if "store:" in l or "store," in l])
        self.assertGreater(printed, 0, "the census printed nothing")
        words = {6: "SIX", 7: "SEVEN", 8: "EIGHT"}
        lint = (BIN / "perry-lint").read_text(encoding="utf-8")
        self.assertIn(f"ALL {words[printed]} declared stores", lint,
                      f"the census printed {printed} lines and the help text "
                      f"says otherwise")

    def test_the_exit_code_table_carries_three(self):
        """R5 of § 1.5: `perry_md_store` returns 3 and the table had 0/1/2.

        The code that produces it is checked too. Reading the README alone
        would keep passing if the tool stopped returning 3, which is the other
        half of the same drift."""
        table = self.README[self.README.index("**Exit codes**"):]
        table = table[:table.index("\n---\n")]   # the horizontal rule, not
        #                                          the table's own separator
        self.assertIn("| `3` |", table)
        store = (BIN / "perry_md_store.py").read_text(encoding="utf-8")
        self.assertIn("return 3", store,
                      "the table documents an exit code nothing returns")

    def test_the_detect_host_values_are_the_ones_it_prints(self):
        """Read off the TOOL. Typing the four values here as well as in the
        README meant a fifth one in the script — which is exactly the drift R5
        recorded — would have gone unreported; a V4 review added
        `cursor-cli` and the suite stayed green."""
        script = (BIN / "perry-detect-host").read_text(encoding="utf-8")
        # Quoted OR bare: `echo claude-code` prints the same thing as
        # `echo "claude-code"`, and a V4 review added an unquoted fifth value
        # that the quoted-only pattern did not see.
        # A line that is nothing but `echo <literal>`: quoted or bare, and
        # nothing else on the line. The quoted-only pattern missed an unquoted
        # fifth value a V4 review added; a looser one picks up `echo "Usage: …"`
        # and the `|| echo 0` in the parent walk.
        prints = set(re.findall(r'^\s*(?:\*[a-z]+\*\)\s*)?echo\s+"?([a-z][a-z-]+)"?\s*(?:;.*)?$',
                                script, re.M))
        self.assertGreaterEqual(len(prints), 4,
                                f"the extraction found {sorted(prints)}")
        row = next(l for l in self.README.splitlines()
                   if "perry-detect-host" in l and l.startswith("|"))
        for value in sorted(prints):
            with self.subTest(value=value):
                self.assertIn(value, row,
                              f"the tool prints {value!r} and the README's "
                              f"row does not name it")


class TestAFlagReachesOnlyItsOwnSubcommands(unittest.TestCase):
    """Goal 12 — the headline of C1, and until a V4 review it rested on ONE
    pre-existing assertion about ONE flag (`--unlinked`, TASK-394).

    `--kr` and `--design` were each accepted by a flat 46-flag table and
    dropped by the handler. What the declaration buys is that this cannot
    happen quietly: the parser refuses, and the refusal names what the
    subcommand does take.
    """

    #: `(tool, subcommand, a flag the tool declares elsewhere)`.
    ELSEWHERE = (
        # `perry-okr` runs `perry_md_store`, whose flags are declared in a
        # FUNCTION rather than a literal — a V4 review made `--write` and
        # `--from-file` universal there and no case here noticed.
        ("perry-okr", "build", "--write"),
        ("perry-okr", "build", "--from-file"),
        ("perry-okr", "verify", "--dry-run"),
        ("perry-task", "start", "--design"),
        ("perry-task", "start", "--kr"),
        ("perry-task", "next", "--unlinked"),
        ("perry-task", "list", "--evidence"),
        ("perry-tasks", "build", "--write"),
        ("perry-tasks", "diff", "--from-board"),
        ("perry-config", "show", "--mode"),
    )

    def setUp(self):
        self.p = Project()
        self.p.run("add", "--title", "a row for the refusals to act on")

    def test_a_declared_flag_on_another_subcommand_is_refused(self):
        for tool, sub, flag in self.ELSEWHERE:
            with self.subTest(tool=tool, sub=sub, flag=flag):
                out = run(tool, sub, flag, "X", "--root", str(self.p.root))
                self.assertEqual(out.returncode, 2,
                                 f"{tool} {sub} {flag} was accepted:\n"
                                 + out.stdout[:200] + out.stderr[:200])
                self.assertIn("not accepted by", out.stderr)
                self.assertIn(sub, out.stderr)

    def test_the_refusal_names_what_the_subcommand_does_take(self):
        out = run("perry-task", "start", "--design", "DESIGN-016",
                  "--root", str(self.p.root))
        self.assertIn("--next", out.stderr,
                      "the refusal did not name the accepted set, so the "
                      "caller learns what is wrong and not what is right")

    def test_the_whole_negative_space_is_refused(self):
        """`ELSEWHERE` is ten rows against a negative space of 1,279 pairs, so
        this walks all of them (TASK-411).

        Every declared tool, every subcommand, every flag that subcommand does
        NOT declare: the parser must refuse it and say so in the sentence the
        caller reads. Asked of `lib.parse_surface` rather than of eighteen
        hundred subprocesses — the cases above already prove each tool reaches
        this parser, and what is unmeasured is the SPACE, not the wiring.

        Measured 2026-09-11 on `488cf079`: 1,279 probes, 1,279 refused, 0
        accepted.
        """
        probes = 0
        accepted = []
        for tool in DECLARED:
            face = surface(tool)
            universal = lib.always_accepted(face)
            table = lib.surface_flags(face)
            for sub in face.get("subcommands", ()):
                takes = set(sub.get("flags", ())) | universal
                for flag, spec in sorted(table.items()):
                    if flag in takes:
                        continue
                    probes += 1
                    read = lib.parse_surface(
                        face, [sub["name"], flag,
                               *(["X"] if spec.get("arg") else [])])
                    if not (read["error"]
                            and "is not accepted by" in read["error"]):
                        accepted.append((tool, sub["name"], flag,
                                         read["error"]))
        self.assertEqual(accepted, [], "a declared flag reached a subcommand "
                                       "that does not declare it")
        self.assertGreater(probes, 1000,
                           f"only {probes} pairs were probed, so 'the negative "
                           f"space is clean' is a claim about a fraction of it")

    def test_the_control_is_that_the_flag_works_where_it_is_declared(self):
        """Without this, a tool that refused every flag everywhere would pass
        the case above."""
        (self.p.root / "design").mkdir(exist_ok=True)
        (self.p.root / "design" / "DESIGN-042-a-fixture.md").write_text(
            "# DESIGN-042: a fixture\n")
        code, _out = self.p.run("add", "--title", "a row that cites a design",
                                "--design", "DESIGN-042")
        self.assertEqual(code, 0)


class TestOneNoArgumentBehaviour(unittest.TestCase):
    """DESIGN-016 C3 — and the rule comes from the declaration, so it is a rule
    rather than a habit: a tool that takes subcommands cannot act without one,
    so a bare call prints its usage on stderr and exits 2; a flag-only tool
    does its documented default and exits 0.

    Bare calls used to answer four ways — usage and exit 2, the whole help and
    exit 0, 187KB of JSON, and a 3.7-second lint — so probing a tool by running
    it had no predictable cost (§ 1.3).
    """

    def test_a_subcommand_tool_refuses_and_shows_its_usage(self):
        for tool in DECLARED:
            if not surface(tool).get("subcommands"):
                continue
            with self.subTest(tool=tool):
                out = run(tool)
                self.assertEqual(out.returncode, 2, out.stdout[:200])
                self.assertIn("Usage:", out.stderr)
                self.assertEqual(out.stdout, "",
                                 "a bare call wrote to stdout, so a caller "
                                 "piping it gets half an answer")

    def test_a_flag_only_tool_does_its_default(self):
        for tool in DECLARED:
            if surface(tool).get("subcommands"):
                continue
            with self.subTest(tool=tool):
                out = run(tool, "--root", str(PERRY_HOME))
                self.assertEqual(out.returncode, 0, out.stderr[:200])
                self.assertTrue(out.stdout.strip())

    def test_the_two_groups_are_both_populated(self):
        """The control: if every declared tool fell in one group, one of the
        cases above would be vacuous."""
        with_subs = [t for t in DECLARED if surface(t).get("subcommands")]
        without = [t for t in DECLARED if not surface(t).get("subcommands")]
        self.assertTrue(with_subs)
        self.assertTrue(without)


class TestTheIndexIsDerivedFromTheDeclarations(unittest.TestCase):

    def _perry(self, *argv):
        return subprocess.run([sys.executable, str(PERRY), *argv],
                              capture_output=True, text=True)

    def test_list_names_every_declared_tool_and_subcommand(self):
        """**Parsed per tool, not grepped.** Substring-matching the whole
        listing let a V4 review print every subcommand of every tool under the
        FIRST tool — the index wrong about who owns what, which is the entire
        deliverable of C4 — and the test passed."""
        out = self._perry("list")
        self.assertEqual(out.returncode, 0, out.stderr)
        owned, current = {}, None
        for line in out.stdout.splitlines():
            if line.startswith("not yet declaring a surface"):
                break                      # the undeclared tail, not an entry
            if line.startswith("perry-"):
                current = line.split()[0]
                owned[current] = []
            elif line.startswith("  ") and current and line.strip():
                owned[current].append(line.split()[0])
        for tool in DECLARED:
            with self.subTest(tool=tool):
                self.assertIn(tool, owned)
                self.assertEqual(
                    owned[tool],
                    [s["name"] for s in surface(tool).get("subcommands", ())],
                    "the index attributes these subcommands to the wrong tool "
                    "or lists them in another order")

    def test_the_json_index_carries_the_same_counts(self):
        payload = json.loads(self._perry("list", "--json").stdout)
        self.assertEqual(set(payload), {"tools", "undeclared"},
                         "the machine-readable index changed shape")
        self.assertIn("perry-lint", payload["undeclared"],
                      "the undeclared list is what stops this index from "
                      "looking complete")
        by_name = {t["tool"]: t for t in payload["tools"]}
        for tool in DECLARED:
            with self.subTest(tool=tool):
                # NAMES, not the count. A count agrees with any renaming,
                # any reordering and any substitution — a V4 reviewer swapped
                # a subcommand and the assertion held. The count is implied by
                # the names and is not asserted separately.
                self.assertEqual(
                    [s["name"] for s in by_name[tool]["subcommands"]],
                    [s["name"] for s in surface(tool).get("subcommands", ())])

    def test_describe_reaches_one_subcommand(self):
        payload = json.loads(self._perry("describe", "tasks", "render").stdout)
        self.assertEqual(payload["subcommand"], "render")
        self.assertIn("BOARD.md", payload["writes"])

    def test_a_surface_that_will_not_load_is_reported_rather_than_demoted(self):
        """`surface_of` used to swallow every exception, so a tool whose
        declaration fails to import was silently reclassified as "not yet
        declaring one" — the index quietly smaller, and the undeclared list
        evidence of nothing. A V4 review reverted the warning and nothing
        noticed."""
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            broken = Path(td) / "bin"
            shutil.copytree(BIN, broken, symlinks=True)
            (broken / "perry-broken").write_text(
                "#!/usr/bin/env python3\nSURFACE = {\nimport nonsense\n")
            (broken / "perry-broken").chmod(0o755)
            out = subprocess.run([sys.executable, str(broken / "perry"), "list"],
                                 capture_output=True, text=True)
        self.assertIn("perry-broken", out.stderr,
                      "a tool whose surface will not load was demoted in "
                      "silence")
        self.assertIn("will not load", out.stderr)

    def test_an_unconverted_tool_is_reported_rather_than_hidden(self):
        """`perry list` says which tools have no declaration yet. A silent
        omission would make the index look complete while it is not."""
        out = self._perry("list")
        self.assertIn("not yet declaring a surface", out.stdout)
        self.assertIn("perry-lint", out.stdout)

    def test_forwarding_runs_the_tool(self):
        out = self._perry("state", "--root", str(PERRY_HOME), "--dashboard")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("Project", out.stdout)


class TestDescribeAnswersForEveryDeclaredTool(unittest.TestCase):

    def test_each_tool_prints_its_own_declaration(self):
        for tool in DECLARED:
            with self.subTest(tool=tool):
                out = subprocess.run(
                    [sys.executable, str(BIN / tool), "--describe", "--json"],
                    capture_output=True, text=True)
                self.assertEqual(out.returncode, 0, out.stderr)
                payload = json.loads(out.stdout)
                self.assertEqual(payload["tool"], tool)
                declared = surface(tool).get("subcommands", ())
                self.assertEqual([s["name"] for s in payload["subcommands"]],
                                 [s["name"] for s in declared])

    def test_the_published_payload_carries_each_subcommands_flags(self):
        """`--describe --json` is TASK-396's published write contract, and
        nothing compared the flags in it.

        A V4 reviewer made `lib.describe_surface` emit an empty flag list for
        every subcommand of every tool. All 3,440 tests stayed green while
        `perry describe task` and `perry-task --describe --json` both reported
        that `add` takes 4 flags instead of 27. The only test that read this
        payload compared `len(payload["subcommands"])` and the `tool` key.

        A consumer reading a surface that says a flag does not exist is the
        same harm as a tool that drops it (§ 1.4): the flag is there and the
        published answer says otherwise.
        """
        for tool in DECLARED:
            out = subprocess.run(
                [sys.executable, str(BIN / tool), "--describe", "--json"],
                capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            payload = json.loads(out.stdout)
            got = {s["name"]: sorted(s.get("flags", ()))
                   for s in payload["subcommands"]}
            decl = surface(tool)
            for sub in decl.get("subcommands", ()):
                with self.subTest(tool=tool, sub=sub["name"]):
                    self.assertEqual(got[sub["name"]],
                                     self.expected_flags(tool, sub))

    #: The universal flags, WRITTEN HERE rather than read from
    #: `lib.always_accepted`. A V4 round made that function return one extra
    #: name; every tool's payload advertised a flag the parser refuses with
    #: exit 2, and the whole suite stayed green — because the expectation was
    #: built by calling the function that produced the payload. That is round
    #: 4's own tautology, in the fix for round 4's tautology.
    #:
    #: `--root`, `--help` and `--describe` are `lib.COMMON_FLAGS`; `--json`
    #: chooses the OUTPUT format in `main` and no handler reads it, so the two
    #: tools that honour it everywhere declare it once as universal rather than
    #: thirty times. `test_the_universal_flags_are_the_ones_the_tools_accept`
    #: below is what keeps this list honest against the running tools.
    UNIVERSAL = {
        "perry-task": ("--describe", "--help", "--json", "--root"),
        "perry-tasks": ("--describe", "--help", "--root"),
        "perry-okr": ("--describe", "--help", "--root"),
        "perry-config": ("--describe", "--help", "--json", "--root"),
        "perry-state": ("--describe", "--help", "--root"),
        "perry-diagnose": ("--describe", "--help", "--root"),
    }

    @classmethod
    def expected_flags(cls, tool: str, sub: dict) -> list[str]:
        return sorted(set(sub.get("flags", ())) | set(cls.UNIVERSAL[tool]))

    def test_the_universal_flags_are_the_ones_the_tools_accept(self):
        """The list above, checked against the tools rather than the source.

        Each universal flag must be ACCEPTED on a subcommand that does not
        declare it — that is what universal means — and a name that is not on
        the list must be refused there. Without this the list is just a second
        copy of the declaration and could drift with it.
        """
        p = Project()
        p.run("add", "--title", "a row the probes can act on")
        reached = 0
        for tool, names in self.UNIVERSAL.items():
            decl = surface(tool)
            # EVERY subcommand that does not declare the flag, not the first
            # one. The first version took `subs[0]`, so it probed 4 of 57
            # subcommands and 8 of the 20 (tool, flag) entries in this dict,
            # and a V4 round counted that before this file did.
            for flag in names:
                if flag in ("--help", "--describe"):
                    # `parse_surface` answers these before a subcommand is
                    # dispatched at all, so they never enter `seen` and there
                    # is nothing here to probe. They are universal by
                    # construction, and this says so rather than looking
                    # tested.
                    continue
                subs = [x["name"] for x in decl.get("subcommands", ())
                        if flag not in set(x.get("flags", ()))]
                for sub in subs:
                    with self.subTest(tool=tool, sub=sub, flag=flag):
                        out = run(tool, sub, flag, "x", "--root", str(p.root))
                        self.assertNotIn(
                            "is not accepted by", out.stderr,
                            f"{flag} is on this file's universal list and "
                            f"{tool} {sub} refuses it")
                    reached += 1
            first = next((x["name"] for x in decl.get("subcommands", ())), None)
            if first:
                with self.subTest(tool=tool, sub=first, flag="--not-a-flag"):
                    out = run(tool, first, "--not-a-flag", "--root", str(p.root))
                    self.assertEqual(out.returncode, 2, out.stdout[:200])
        self.assertGreater(reached, 50,
                           "the probe reached almost nothing, so the list "
                           "above rests on itself")

    def test_the_universal_list_has_no_entry_no_test_can_read(self):
        """`perry-state` and `perry-diagnose` declare zero subcommands.

        Their entries in `UNIVERSAL` are unreachable by `expected_flags`, which
        iterates subcommands, and by the probe above, which needs one to run.
        A V4 round found them dead. They stay — the payload for a tool with no
        subcommands still carries these flags — and this is what says so, so
        the next reader does not take their presence as coverage.
        """
        dead = [t for t in self.UNIVERSAL
                if not surface(t).get("subcommands", ())]
        self.assertEqual(sorted(dead), ["perry-diagnose", "perry-state"])
        for tool in dead:
            with self.subTest(tool=tool):
                payload = json.loads(subprocess.run(
                    [sys.executable, str(BIN / tool), "--describe", "--json"],
                    capture_output=True, text=True).stdout)
                self.assertEqual(
                    sorted(f["name"] for f in payload["flags"]),
                    sorted({f["name"]
                            for f in surface(tool).get("flags", ())}
                           | set(self.UNIVERSAL[tool])))

    def test_the_single_subcommand_payload_carries_the_same_flags(self):
        """The branch the fix left behind.

        `describe_surface` has two branches and `134afea6` compared one. The
        other answers `<tool> <sub> --describe --json` and `perry describe
        <tool> <sub>` — which `bin/README.md` publishes as the way to ask about
        one subcommand, and which is the answer for all 57 declared
        subcommands. Emptying its flag list left 3,459 tests green while
        `perry describe task add` reported 0 flags instead of 27.
        """
        for tool in DECLARED:
            decl = surface(tool)
            for sub in decl.get("subcommands", ()):
                with self.subTest(tool=tool, sub=sub["name"]):
                    out = subprocess.run(
                        [sys.executable, str(BIN / tool), sub["name"],
                         "--describe", "--json"],
                        capture_output=True, text=True)
                    self.assertEqual(out.returncode, 0, out.stderr)
                    payload = json.loads(out.stdout)
                    self.assertEqual(payload["subcommand"], sub["name"])
                    self.assertEqual(
                        sorted(f["name"] for f in payload["flags"]),
                        self.expected_flags(tool, sub))

    def test_the_generated_usage_line_names_the_same_flags(self):
        """The third spelling of the same set, and it was uncompared too.

        `usage_lines` built the list a third time. Emptying it left the suite
        green while `perry-task add --help` printed a usage line with no flags
        at all — a rendered surface telling a reader a subcommand takes
        nothing. It also had the subtraction inside the union, so a subcommand
        that declared `--help` itself would have kept it in its own usage line.
        """
        for tool in DECLARED:
            decl = surface(tool)
            for sub in decl.get("subcommands", ()):
                with self.subTest(tool=tool, sub=sub["name"]):
                    want = {n for n in self.expected_flags(tool, sub)
                            if n not in ("--help", "--describe")}
                    self.assertEqual(
                        self._flags_in(lib.usage_lines(decl, sub["name"])),
                        want)

    @staticmethod
    def _flags_in(text: str) -> set[str]:
        """The flag names a usage line actually offers, parsed out of it.

        **An exact set, because `assertIn` could only see one direction.** The
        first version of the case above asked whether each declared flag
        appeared somewhere in the text, so a usage line naming EVERY flag of
        the whole tool passed for every subcommand. A V4 round made
        `usage_lines` do exactly that and the full suite stayed green while
        `perry-task add --help` offered 46 flags instead of the 25 `add`
        accepts — and the same declaration refuses 21 of those 46 with exit 2.
        Under-reporting was caught; over-reporting was not, and over-reporting
        is the one that sends a reader to a refusal.
        """
        return set(re.findall(r"\[(--[a-z][a-z-]*)", text))

    def test_a_subcommand_that_declares_help_keeps_it_out_of_its_usage_line(self):
        """The precedence fix, on a declaration that reaches it.

        `usage_lines` read `set(item["flags"]) | always_accepted(s) - {...}`,
        which binds as `set(...) | (always_accepted - {...})` and so keeps
        `--help` whenever a subcommand declares it itself. No shipped
        subcommand does, so the fix changes nothing today and reverting it
        reddens nothing — a V4 round said so and was right to. This is the
        fixture that reaches it, rather than a latent fix nothing holds.
        """
        made = {"name": "t", "kind": "read", "summary": "s",
                "flags": [{"name": "--help"}, {"name": "--describe"},
                          {"name": "--root", "arg": "path"},
                          {"name": "--only", "arg": "value"}],
                "subcommands": [{"name": "go", "summary": "",
                                 "flags": ["--only", "--help", "--describe"]}]}
        self.assertEqual(self._flags_in(lib.usage_lines(made, "go")),
                         {"--only", "--root"})


if __name__ == "__main__":
    unittest.main()
