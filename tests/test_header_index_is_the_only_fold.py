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

import importlib.machinery
import importlib.util
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

CONFORMANCE = ("# Conformance\n\n"
               "| **File** | Shape version | Declared | Route |\n"
               "| --- | --- | --- | --- |\n"
               "| `BOARD.md` | 2 | 2026-08-18 | migrate |\n")


def load(name: str):
    """A `bin/` script as a module, the way the rest of the suite does."""
    loader = importlib.machinery.SourceFileLoader(
        name.replace("-", "_"), str(PERRY_HOME / "bin" / name))
    spec = importlib.util.spec_from_loader(name.replace("-", "_"), loader)
    mod = importlib.util.module_from_spec(spec)
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
    """Named, not argued away.

    This watches the readers a parse REACHES. A function no parse calls is
    invisible to it — which is what `tests/test_header_rule_harness.py` plants
    for, and why both nets exist. Neither is complete; the FUNCTION is what
    makes the defect impossible, and these two measure that it stayed that way.
    """

    def test_the_static_net_is_the_one_that_sees_dead_code(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from header_rule import offenders_by_symbol
        self.assertEqual(offenders_by_symbol(PERRY_HOME), [])


if __name__ == "__main__":
    unittest.main()
