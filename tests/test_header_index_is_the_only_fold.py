"""**The check that closes TASK-050, and it is not a static one.**

Seven rounds built a detector of a second header rule and seven reviewers
defeated it, the last one by inverting the question: not *"does the check see a
file I invent?"* but *"of the header resolutions this tree already contains,
how many can it see?"* — and the answer was two of eight.

Round 8 answered that with a smaller surface rather than a better detector:
`viewer/tables.py § header_index` is the only function allowed to fold a header
cell. **This module watches the real readers parse a real decorated document
and asks who called `squash`.** It recognises no shapes and holds no list of
variable names, so there is no spelling of a reader that walks past it; what it
cannot see is a reader that no parse reaches, and that is stated below rather
than argued away.

The instrument is the one `tests/test_row_integrity.py § reader_calls` uses on
stores: wrap the primitive, record the caller's frame, run the workload.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
sys.path.insert(0, str(PERRY_HOME / "bin"))
import tables                                  # noqa: E402
import parsers as P                            # noqa: E402

#: The header cells this module watches — **decorated ones only, and that is
#: the whole trick.** A plain `ID` is folded twice for two different reasons:
#: once as a cell the project wrote, and once as the canonical English column
#: name `_column_keys("ID")` compares it against. The second is correct and is
#: not a header cell at all, so watching `ID` would report `_column_keys` and
#: `accepted` as offenders. Nobody writes a canonical name in bold, so a
#: DECORATED spelling can only have come off the document — which makes the
#: argument to the call the evidence, with no list of function names in it.
#:
#: `**Default** rung` is the divergence the whole row exists for: it
#: lowercases to `default** rung` and matches nothing.
HEADER_CELLS = ["**Risk**", "**Title**", "**Arrived**", "**Needed from user**",
                "**Default** rung", "**KR**", "**Due**", "**File**"]

#: What those cells resolve TO. Matched on the KEY rather than on the byte
#: string, because two readers strip part of the decoration on the way in —
#: `bin/perry-state § cells_of` hands `header_index` `Default** rung`, not
#: `**Default** rung` — and a watch keyed on the literal would have reported
#: that reader as never folding a cell it folds on every run.
HEADER_KEYS = {tables.squash(c) for c in HEADER_CELLS}

#: **The readers this module claims to watch, asserted one by one.** Round 8
#: listed twelve and one of them recorded nothing at all; a list that is only
#: prose cannot go red. `test_every_reader_this_module_claims_to_watch_actually
#: _folds_one` requires each of these to appear in the recorded call stacks.
WATCHED = [
    # viewer/parsers.py
    "_table_rows", "_parse_intake", "_parse_user_input", "_parse_cadence",
    "_parse_task_table", "read_conformance", "is_risk_register_header",
    # bin/
    "parse_tracks",            # bin/perry-state
    "_track_context",          # bin/perry-lint
    "md_table",                # bin/perry-diagnose
    "harvest",                 # bin/perry-explain
    "header_language",         # bin/perry-task AND bin/perry-goals
    "header_keys",             # bin/perry-task
    "markdown_tables",         # bin/perry_store.py
    "fix_tables",              # bin/perry-migrate
    "cmd_intake_write",        # bin/perry-tasks
]

CONFIG = (
    "# Perry configuration\n\n- State root: .\n\n## Tracks\n\n"
    "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | **Default** rung |\n"
    "|---|---|---|---|---|---|---|---|\n"
    "| ops | queue | OKR.md | new -> done | — | 3d | — | V2 |\n")

BOARD = (
    "# Board\n\n## Work\n\n"
    "| ID | **Title** | Owner | Status | Track | Stage |\n"
    "|---|---|---|---|---|---|\n"
    "| TASK-001 | ship it | me | open | ops | new |\n\n"
    "## Top risks\n\n"
    "| ID | **Risk** | Opened | Status |\n|---|---|---|---|\n"
    "| RX-001 | the vendor lapses | 2026-01-01 | open |\n\n"
    "## Intake\n\n"
    "| **Arrived** | Request | Outcome |\n|---|---|---|\n"
    "| 2026-01-01 | do a thing | |\n\n"
    "## User Input Queue\n\n"
    "| USER-id | **Needed from user** | Blocks | Asked | Idle | Status |\n"
    "|---|---|---|---|---|---|\n"
    "| USER-001 | which one | TASK-001 | 2026-01-01 | 1 | pending |\n")

OKR = (
    "# OKR\n\n## Objective 1 ship\n\n"
    "| **KR** | Target | Current |\n|---|---|---|\n"
    "| KR-1 | 3 | 1 |\n\n"
    "## Commitments\n\n| ID | Promise | **Due** |\n|---|---|---|\n"
    "| C-1 | do it | 2026-02-01 |\n")

#: Header ROWS, for the readers whose entry point takes a row rather than a
#: document. Each carries a decorated cell, which is what
#: `folds_of_a_header_cell` keys on.
BOARD_HEADER = ["ID", "**Title**", "Owner", "Status", "Track", "Stage"]
OKR_HEADER = ["**KR**", "Target", "Current"]
OKR_TABLE = ["| **KR** | Target | Current |", "|---|---|---|", "| KR-1 | 3 | 1 |"]

#: `bin/perry-migrate § fix_tables` takes a table spec, not a document.
MIGRATE_LINES = ["## Commitments", "", "| ID | Promise | **Due** |",
                 "|---|---|---|", "| C-1 | do it | 2026-02-01 |", ""]
MIGRATE_SPEC = {"tables": [{"under": "Commitments", "under_level": 2,
                            "columns": ["ID", "Promise", "Due"]}]}

#: **`bin/perry-tasks`, and it is here because round 9 declared it a limit and
#: round 9's reviewer walked through it.** § 6.2 of the round 9 result named
#: `bin/perry-tasks` as *"the one converted reader still not driven"*, and the
#: reviewer planted its escape there for exactly that reason: `_fold = squash`
#: plus `keys = [ops.norm(_fold(c)) for c in _hdr]` replacing the
#: `header_index(...)` call, with `offenders_by_symbol` returning `[]` and the
#: whole suite at its three pre-existing failures.
#:
#: The static half cannot see that site even with aliases resolved, and the
#: reason is not the alias: `_hdr` comes from
#: `perry_store.intake_table(board, ops)["header"]` — a row produced in ANOTHER
#: MODULE and carried through a dict key. `_RowLocals` is file-local by
#: construction and resolving that would be the interprocedural widening the
#: amendment rejects by name. So the reader is DRIVEN instead, which is the
#: half of the design that is blind to spelling altogether.
#:
#: `cmd_intake_write` writes a store, so it runs against a throwaway root; the
#: `**Arrived**` header is what makes the fold visible to
#: `folds_of_a_header_cell`.
INTAKE_BOARD = (
    "# Board — T\n\n"
    "## Intake\n\n"
    "| **Arrived** | Request | Outcome |\n|---|---|---|\n"
    "| 2026-01-01 | do a thing | — |\n\n"
    "## Work\n\n"
    "| ID | **Title** | Owner | Status | Track | Stage |\n"
    "|---|---|---|---|---|---|\n"
    "| TASK-001 | ship it | me | open | ops | new |\n")

INTAKE_CONFIG = ("# Perry configuration\n\n- Document language: English\n"
                 "- Repo layout: single\n- State root: .\n")

CONFORMANCE = ("# Conformance\n\n"
               "| **File** | Shape version | Declared | Route |\n"
               "| --- | --- | --- | --- |\n"
               "| `BOARD.md` | 2 | 2026-08-18 | migrate |\n")


def load(name: str):
    """A `bin/` script as a module, the way the rest of the suite does.

    Registered in `sys.modules` BEFORE `exec_module`, because `bin/perry-migrate`
    declares a `@dataclass` and `dataclasses` resolves the class's own module
    out of `sys.modules` while the decorator runs. Without this line
    `perry-migrate` cannot be loaded at all — which is one reason round 8's
    workload never executed it.
    """
    mod_name = name.replace("-", "_")
    loader = importlib.machinery.SourceFileLoader(
        mod_name, str(PERRY_HOME / "bin" / name))
    spec = importlib.util.spec_from_loader(mod_name, loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


class Watch:
    """Every `squash` call made while this is active, with its caller.

    Patched on `viewer/tables.py` itself, so every module that imported the
    name — under any alias, `squash`, `norm`, `L.norm`, `ops.norm` — is
    watched by the one patch. That is the property the round bought: there is
    one object to wrap because there is one rule.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []   # (caller function, argument)

    def __enter__(self):
        self.real = tables.squash
        watch = self

        def squash(s):
            # The whole STACK, not the immediate caller: `header_index` folds
            # inside a comprehension, so `f_back` is `<listcomp>` and a check
            # on one frame would report the blessed function as an offender.
            stack, f, n = [], sys._getframe(1), 0
            while f is not None and n < 12:
                stack.append(f.f_code.co_name)
                f, n = f.f_back, n + 1
            watch.calls.append((tuple(stack), str(s)))
            return watch.real(s)

        tables.squash = squash
        # The readers hold their own reference, bound at import. Rebind every
        # one of them, or the patch watches nothing and the test is vacuous —
        # which `test_the_watch_is_not_vacuous` is here to catch.
        self.patched = []
        for mod in list(sys.modules.values()):
            for attr in ("squash", "norm"):
                if getattr(mod, attr, None) is self.real:
                    setattr(mod, attr, squash)
                    self.patched.append((mod, attr))
        return self

    def __exit__(self, *exc):
        tables.squash = self.real
        for mod, attr in self.patched:
            setattr(mod, attr, self.real)
        return False

    def folds_of_a_header_cell(self) -> list[tuple[tuple, str]]:
        """Calls whose ARGUMENT is a DECORATED spelling of a fixture header cell.

        `arg.lower() != squash(arg)` is the whole discriminator and it needs
        no list of function names: it is true exactly when the argument carries
        `*`, a backtick or padding. A canonical English column name is written
        plainly — `_column_keys("Title")` folds `Title` — so anything that
        survives this test came off the DOCUMENT. Comparing against `squash`
        alone would not do: it lowercases, so `Title` would qualify.
        """
        return [(stack, arg) for stack, arg in self.calls
                if arg.lower() != self.real(arg) and self.real(arg) in HEADER_KEYS]


class TestOnlyHeaderIndexFoldsAHeaderCell(unittest.TestCase):
    """**The whole row, in one assertion, measured on a real parse.**"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        (self.tmp / ".perry").mkdir()
        (self.tmp / ".perry" / "config.md").write_text(CONFIG, encoding="utf-8")
        (self.tmp / ".perry" / "conformance.md").write_text(
            CONFORMANCE, encoding="utf-8")
        (self.tmp / "BOARD.md").write_text(BOARD, encoding="utf-8")
        (self.tmp / "OKR.md").write_text(OKR, encoding="utf-8")

    def parse_everything(self):
        """Every reader this row named, over the decorated fixtures."""
        state = load("perry-state")
        lint = load("perry-lint")
        diagnose = load("perry-diagnose")
        explain = load("perry-explain")
        state.parse_tracks(CONFIG)
        P.parse_board(BOARD)
        P.parse_okr(OKR)
        P.read_conformance(self.tmp)
        P._parse_intake(BOARD)
        P._parse_user_input(BOARD)
        P._parse_cadence(BOARD)
        P._table_rows(OKR)
        P.parse_top_risks(BOARD)
        aliases = {"id": {"id"}, "risk": {"risk"}, "status": {"status"},
                   "title": {"title"}, "arrived": {"arrived"},
                   "request": {"request"}, "outcome": {"outcome"}}
        for section in BOARD.split("\n## "):
            diagnose.md_table(section.split("\n"), aliases)
        lint._track_context(self.tmp / "BOARD.md", "ops")
        explain.harvest(self.tmp)
        # **Round 8's workload stopped here**, and its reviewer measured the
        # consequence: `bin/perry-task`, `bin/perry-goals`, `bin/perry-tasks`,
        # `bin/perry_store.py` and `bin/perry-migrate` were never executed at
        # all — *"roughly 38 of 58 converted sites are LIVE, converted, and
        # covered by the shape net alone."* The shape net is deleted, so the
        # four below are driven here instead of being listed and not watched.
        load("perry-task").header_language(BOARD_HEADER)
        load("perry-goals").header_language(OKR_HEADER, ["kr"])
        import perry_store                       # noqa: E402
        perry_store.markdown_tables(OKR_TABLE, 0, len(OKR_TABLE), lambda s: s)
        import perry_md_store                    # noqa: E402
        perry_md_store.scan_okr(OKR)
        load("perry-migrate").fix_tables(
            MIGRATE_LINES, MIGRATE_SPEC, {}, [], [])
        self.drive_intake_write()

    def drive_intake_write(self):
        """`bin/perry-tasks intake-write --from-board`, in process.

        The subprocess the rest of the suite uses would be invisible to the
        watch — a patch on `tables.squash` in THIS interpreter says nothing
        about another one — so the command function is called directly, on a
        throwaway root it is allowed to write into.
        """
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text(INTAKE_CONFIG,
                                                   encoding="utf-8")
        (root / "BOARD.md").write_text(INTAKE_BOARD, encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = load("perry-tasks").cmd_intake_write(root, ["--from-board"])
        self.assertEqual(rc, 0,
                         f"the intake import refused, so this reader was not "
                         f"driven and the watch measured nothing about it: "
                         f"{err.getvalue()[:400]}")
        self.assertTrue((root / "intake.jsonl").exists(),
                        "the import returned 0 and wrote no store")

    def test_every_fold_of_a_header_cell_came_from_header_index(self):
        with Watch() as w:
            self.parse_everything()
        stray = sorted({stack[0] for stack, _ in w.folds_of_a_header_cell()
                        if "header_index" not in stack})
        self.assertEqual(
            stray, [],
            "a header cell was folded outside `viewer/tables.py § "
            f"header_index`, by: {stray}. That is the second rule this row "
            "exists to make impossible.")

    def test_the_watch_is_not_vacuous(self):
        """A zero above must mean "nobody else folded one", not "nothing was
        folded" — the failure mode round 5's complement test died of."""
        with Watch() as w:
            self.parse_everything()
        folds = w.folds_of_a_header_cell()
        self.assertGreater(len(folds), 5,
                           "the readers folded almost no header cells, so the "
                           "assertion above measured nothing")
        self.assertGreater(len({arg for _s, arg in folds}), 3,
                           "one decorated cell reached the readers; the "
                           "fixtures are not exercising the readers")
        self.assertTrue(any("header_index" in s for s, _ in folds))

    def test_every_reader_this_module_claims_to_watch_actually_folds_one(self):
        """**Round 8's Finding 3, asserted instead of listed.**

        Round 8's evidence named twelve readers this module watches.
        `bin/perry-diagnose § md_table` was one of them and it contributed
        **zero** recorded folds, because it pre-stripped decoration with its own
        `c.strip("*` ")` before calling `header_index`, so the watch's
        discriminator never saw a decorated argument from it. *"A watcher that
        watches a reader it can never see is a vacuous entry."*

        The pre-strip is gone (`bin/perry-diagnose`, round 9) and the list is
        now an assertion: every function named below must appear in the
        recorded stacks, so a reader cannot be claimed as watched without being
        watched. The number beside each is not asserted — it moves with the
        fixtures — only that it is not zero.
        """
        with Watch() as w:
            self.parse_everything()
        seen = {fn for stack, _ in w.folds_of_a_header_cell() for fn in stack}
        for reader in WATCHED:
            with self.subTest(reader):
                self.assertIn(
                    reader, seen,
                    f"`{reader}` is named as a watched reader and folded no "
                    f"decorated header cell in this workload — either drive it "
                    f"or stop claiming it. Recorded: {sorted(seen)}")

    def test_the_rebinding_loop_watches_a_readers_own_reference(self):
        """**Round 9 review, smaller results: a guard that survives its own
        deletion.** `Watch.__enter__`'s rebinding loop carries the comment
        *"Rebind every one of them, or the patch watches nothing and the test
        is vacuous"*, and the reviewer replaced `for attr in ("squash",
        "norm"):` with `for attr in ():` and **all 7 tests in this module
        stayed green**, `test_the_watch_is_not_vacuous` included. A guard that
        can be deleted with the suite unchanged is not a guard.

        It is kept rather than deleted because what it protects is real and is
        exactly what this row forbids: a reader holding its own reference to
        the rule and calling it directly, without going through
        `header_index`. Nothing does that today — which is why the loop is
        silent today — so the protection has to be exercised deliberately.
        `bin/perry-lint:250` is `norm = squash`, the repository's own idiom
        for holding that reference, and it is the module used here.
        """
        lint = load("perry-lint")
        self.assertIs(lint.norm, tables.squash,
                      "`bin/perry-lint` no longer holds its own reference to "
                      "the rule; pick another reader that does, or delete the "
                      "rebinding loop this test exists for")
        real = tables.squash
        with Watch() as w:
            self.assertIsNot(
                lint.norm, real,
                "the rebinding loop left a reader's own reference pointing at "
                "the UNWATCHED function, so a fold made through it would be "
                "invisible to every assertion in this module")
            lint.norm("**Title**")
        self.assertIn(
            "**Title**", [arg for _stack, arg in w.calls],
            "a decorated header cell was folded through a reader's own "
            "reference and the watch did not see it")
        self.assertIs(lint.norm, real, "`__exit__` left the reader patched")

    def test_the_decorated_header_still_resolves(self):
        """Behaviour, not accounting. A guard satisfied by a rename is not one."""
        state = load("perry-state")
        tracks = state.parse_tracks(CONFIG)
        self.assertEqual(tracks[0].get("default_rung"), "V2",
                         "the bolded header lost its column")
        plain = state.parse_tracks(
            CONFIG.replace("**Default** rung", "Default rung"))
        self.assertEqual(tracks, plain)


class TestTheDecoratedHeaderReachesTheOneFold(unittest.TestCase):
    """**Coverage, and it is the half that catches a SECOND rule.**

    `TestOnlyHeaderIndexFoldsAHeaderCell` asks who called `squash`; a reader
    that grows its OWN rule calls nobody, so that assertion alone stays green
    while the defect is live. This asks the complementary question — *did every
    decorated header cell in the fixtures reach `header_index`?* — so a reader
    that stops asking is a reader that goes red.

    `viewer/parsers.py § _table_rows` is the site the amendment names: today
    reverting it to `.strip("*` ").lower()` silently drops a KR out of a user's
    OKR with the whole suite green. It does not any more, and the two tests
    below are why — one by accounting, one by behaviour.
    """

    KR_SECTION = ("| **KR** id | Text | Target | Current |\n"
                  "|---|---|---|---|\n"
                  "| KR-1 | ship it | 3 | 1 |\n")

    def test_every_decorated_header_cell_reached_header_index(self):
        with Watch() as w:
            P._table_rows(self.KR_SECTION)
            P._table_rows(OKR)
            P.parse_okr(OKR)
            P.parse_board(BOARD)
            P.read_conformance(self._conformance_root())
            load("perry-state").parse_tracks(CONFIG)
        via = {w.real(arg) for stack, arg in w.folds_of_a_header_cell()
               if "header_index" in stack}
        missing = sorted(HEADER_KEYS - via)
        self.assertEqual(
            missing, [],
            f"these decorated header cells were never folded by "
            f"`header_index`, so some reader resolved them another way (or "
            f"stopped resolving them at all): {missing}")

    def test_a_bolded_kr_header_still_yields_the_KR(self):
        """The behaviour under the accounting. Round 7 measured this exact
        revert as losing the row with 2882 tests green."""
        rows = P._table_rows(self.KR_SECTION)
        self.assertEqual(
            [(r.get("kr id"), r.get("text")) for r in rows],
            [("KR-1", "ship it")],
            "the bolded `**KR** id` header lost its column and the KR with it")

    def _conformance_root(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        (tmp / ".perry").mkdir()
        (tmp / ".perry" / "conformance.md").write_text(CONFORMANCE,
                                                       encoding="utf-8")
        return tmp


class TestWhatThisCannotSee(unittest.TestCase):
    """Named, not argued away, and round 9 made the naming narrower.

    This watches the readers a parse REACHES, and
    `test_every_reader_this_module_claims_to_watch_actually_folds_one` above
    now asserts which those are, one by one, rather than listing them in prose.
    What it still cannot see is a fold in a code path this workload does not
    execute — a function nothing calls, a reader that grows its own rule for a
    column these fixtures do not carry, or a branch these documents do not take.

    The static net sees dead code and is blind to a second RULE; this sees a
    second rule and is blind to dead code. **Neither is complete and neither is
    what closes the row** — `viewer/tables.py § header_index` is, because there
    is one function to fold a header cell and therefore nothing for a second
    copy to be a copy of. These two measure that it stayed that way.
    """

    def test_the_static_net_is_the_one_that_sees_dead_code(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from header_rule import offenders_by_symbol
        self.assertEqual(offenders_by_symbol(PERRY_HOME), [])


if __name__ == "__main__":
    unittest.main()
