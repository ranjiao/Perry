"""TASK-159 — one answer to "what is a project root", proved by rendering.

Three readers each held a different answer, measured at `efa0d73`:

| where | what it meant by "project root" |
|---|---|
| `viewer/parsers.py § _resolve_project_root` | the directory holding `BOARD.md` — the STATE root |
| `bin/perry-viewer` | `$PERRY_PROJECT` — the PROJECT root |
| `bin/perry-state --root` | the PROJECT root |

On a project whose state lives in a subdirectory — **Perry's own,
`.perry/config.md § State root: perry`** — those are different directories, so
the viewer rendered an EMPTY snapshot when pointed exactly where its own
launcher points it. Measured before the fix, against this repository:
`tasks 0 · adrs 0 · phase None`.

**Every test here that makes a claim about the viewer goes through the render**
— `serve.py`'s shipped route functions and the shipped `viewer/templates/`,
via `tests/test_kr_chain_render.py`'s stand-ins, imported rather than retyped.
A resolution change proved only by a unit test on the resolver is not proved:
the resolver was self-consistent the whole time, and the page was still blank.

The two directions are one class each, and both must hold. A fix keyed on the
wrong side satisfies exactly one of them:

- `TestAProjectWhoseStateIsASubdirectoryRenders` — Perry's own shape;
- `TestAProjectWhoseStateIsItsRootIsUnchanged` — every other project's shape.

Measured, one revert at a time, against the 24 tests here:

| revert | failures |
|---|---|
| `load_snapshot`'s default root back to `PROJECT_ROOT` | 6 |
| `/architecture` and `/file/<rel>` read from `PROJECT_ROOT` again | 2 |
| the CWD walk stops reading `.perry/config.md` | 1 |
| `resolve_project_root` drops the round trip and takes the first anchor | 1 |
| `walk_design` handed the state root as its project root again | 1 |

`tests/test_kr_chain_render.py` stays green under every one of them — this row
does not touch what TASK-146 landed, and the chain card's degraded-mode
wording is exercised here rather than changed.

Run: python3 tests/parallel -j 4 test_project_root
"""

from __future__ import annotations

import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(os.environ.get("PERRY_HOME")
                  or Path(__file__).resolve().parent.parent)

sys.path.insert(0, str(PERRY_HOME / "tests"))
sys.path.insert(0, str(PERRY_HOME / "viewer"))

#: The Flask / `markdown` stand-ins and the real-templates Jinja environment
#: TASK-146 built so a route could be rendered in a suite that must not require
#: the viewer's opt-in dependencies. Imported, because a second copy of them is
#: a second thing to keep true — and because a page rendered through a
#: DIFFERENT harness than the one guarding the chain card would not prove the
#: chain card still works.
from test_kr_chain_render import (  # noqa: E402
    _env, _stub_flask, _stub_markdown, text_of)
from test_kr_progress_provenance import build_project  # noqa: E402

STATE_TOOL = PERRY_HOME / "bin" / "perry-state"

#: State files a fixture moves when its state root is a subdirectory.
#: `.perry/` is NOT among them, and that is the rule the inverse is read off:
#: it holds the pointer, so it cannot sit behind it.
MOVES = ("BOARD.md", "OKR.md", "ARCHITECTURE.md", "tasks.jsonl", "phase")

ARCHITECTURE = "# Architecture\n\n## Layers\n\nOne fixture, two layouts.\n"

#: The store rows that reach a board lane. TASK-146's fixture files its records
#: with no `group`, because the chain reads them by id and never asks which
#: section they sit in; a board reads nothing else. Added here rather than
#: there, so the fixture the chain card is guarded by stays exactly as it was.
#:
#: `TASK-001` and `TASK-002` are `done` and deliberately keep their group: a
#: closed row leaves the board while staying in the store, so their ABSENCE
#: from the rendered page is itself evidence the store is what was read.
ON_BOARD = "P1"


# ── the two layouts, from one body of state ───────────────────────────────


def flat_project() -> Path:
    """A project whose state IS its root — every project but Perry's own.

    `.resolve()`d, because `tempfile` hands back `/var/…` and macOS resolves
    that to `/private/var/…`: `resolve_state_root`'s "a state root outside the
    project is a misconfiguration" guard compares a resolved child against an
    unresolved parent and rejects its own subdirectory. Both entrances resolve
    their roots before they ever reach these functions (`_resolve_project_root`
    and `bin/perry-state § resolve_root` both end in `.resolve()`), so a
    fixture that did not would be testing a path neither one produces."""
    root = build_project().resolve()
    (root / "ARCHITECTURE.md").write_text(ARCHITECTURE)
    store = root / "tasks.jsonl"
    store.write_text("".join(
        json.dumps({**json.loads(line), "group": ON_BOARD}) + "\n"
        for line in store.read_text().splitlines() if line.strip()))
    return root


def nested_project(sub: str = "state") -> Path:
    """The same project with `State root: <sub>` — Perry's own shape.

    Built by MOVING a flat fixture's files rather than by writing a second
    fixture, so the two layouts differ in nothing but where the state sits.
    That is what lets the render assertions below be identical strings: if the
    nested page said less than the flat one, it would be this resolution and
    not the content."""
    root = flat_project()
    dest = root / sub
    dest.mkdir(parents=True)
    for name in MOVES:
        shutil.move(str(root / name), str(dest / name))
    (root / ".perry" / "config.md").write_text(
        f"# Perry configuration\n\n- State root: {sub}\n")
    return root


# ── the shipped route, rendered ───────────────────────────────────────────


def render(root: Path, route: str = "board") -> str:
    """`GET /<route>`, through `serve.py`'s route function and the real templates.

    `root` is what `bin/perry-viewer` exports as `$PERRY_PROJECT`: the PROJECT
    root. Passing anything else here would be testing a configuration the
    launcher never produces."""
    filters: dict = {}
    sys.modules["flask"] = _stub_flask(filters)
    sys.modules["markdown"] = _stub_markdown()

    os.environ["PERRY_PROJECT"] = str(root)
    import parsers
    importlib.reload(parsers)      # both roots are module globals frozen at
    import serve                   # import, and each test renders another project
    importlib.reload(serve)

    env = _env(filters)
    serve.render_template = lambda name, **ctx: env.get_template(name).render(**ctx)
    return getattr(serve, route)()


TASK_ID = re.compile(r"TASK-\d{3}")


class Rendered(unittest.TestCase):
    def setUp(self):
        self.addCleanup(os.environ.pop, "PERRY_PROJECT", None)

    def board_of(self, root: Path) -> str:
        return text_of(render(root, "board"))


# ── item 1 — a project whose state is a subdirectory ──────────────────────


class TestAProjectWhoseStateIsASubdirectoryRenders(Rendered):
    """Pointed at the PROJECT root, which is the only thing the launcher exports."""

    def setUp(self):
        super().setUp()
        self.root = nested_project()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_the_board_carries_the_projects_rows_and_not_an_empty_snapshot(self):
        """The whole defect, in the one place a reader would have seen it.

        Before this row the same call rendered a board with no rows at all —
        not an error, not a warning, an empty project."""
        page = self.board_of(self.root)
        self.assertEqual(sorted(set(TASK_ID.findall(page))),
                         ["TASK-003", "TASK-004"])
        for title in ("Three", "Four"):
            self.assertIn(title, page)

    def test_the_phase_page_finds_the_phase_under_the_state_root(self):
        page = text_of(render(self.root, "phase"))
        self.assertIn("a-phase", page)
        self.assertNotIn("No active phase", page)

    def test_the_architecture_page_reads_a_file_under_the_state_root(self):
        """`/architecture` reads its file off a root of its own rather than
        through the snapshot, so it is the one page that could still be blank
        after the board was fixed."""
        page = text_of(render(self.root, "architecture"))
        self.assertIn("One fixture, two layouts.", page)

    def test_a_file_link_from_the_page_resolves(self):
        """Every `/file/<rel>` link in the templates is a STATE-root-relative
        path — `EvidenceFile.rel`, `DesignDoc.rel`, a literal `BOARD.md`. A
        route resolving them against the project root 404s all of them."""
        render(self.root, "board")          # loads `serve` for this project
        import serve
        page = text_of(serve.view_file("BOARD.md"))
        self.assertIn("TASK-001", page)

    def test_the_chain_card_still_refuses_to_invent(self):
        """TASK-146's degraded-mode behaviour must survive being un-degraded.

        The card's job is to state what it cannot evaluate; what changed here
        is only that on this shape it can now evaluate it. So the guarantee is
        asserted where it is load-bearing — no percentage, no verdict — rather
        than by the absence of the old apology."""
        card = text_of(render(self.root, "phase")).lower()
        for banned in ("%", "achieved", "on track", "complete"):
            self.assertNotIn(banned, card)
        self.assertIsNone(re.search(r"\bmet\b", card))
        self.assertIn("asserted by the author, not measured", card)


class TestTheInverseReachesWhatTheBoundedWalkCannot(Rendered):
    """`walk_design` looks for `.perry/events.jsonl` by walking up FOUR levels
    from the state root, because when it was written there was no inverse to
    ask. Four is a guess, and this fixture is the fifth level.

    Asserted through `/design`, where the count is the difference between "1
    task" and "no refs" — the design-handoff signal `walk_design`'s own
    docstring says shipped code was reported as never handed off for."""

    DOC = ("# DESIGN-009 — a thing\n\n"
           "> **Status**: locked 2026-08-01\n> **Date**: 2026-08-01\n\n"
           "## Plan\n\nOne doc, five levels down.\n")

    def setUp(self):
        super().setUp()
        self.root = nested_project(sub="a/b/c/d/e")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        state = self.root / "a/b/c/d/e"
        (state / "design").mkdir()
        (state / "design" / "DESIGN-009-a-thing.md").write_text(self.DOC)
        with open(self.root / ".perry" / "events.jsonl", "a") as fh:
            fh.write(json.dumps({"ts": "2026-08-12T09:00:00", "event": "done",
                                 "id": "TASK-004",
                                 "next": "implements DESIGN-009"}) + "\n")

    def test_the_design_is_not_reported_as_never_handed_off(self):
        html = render(self.root, "design")
        self.assertIn("DESIGN-009", text_of(html))
        self.assertIn(">1 task<", html)
        # The page's own footnote says the words "no refs", so the negative is
        # asserted on the cell that would carry them and not on the page.
        self.assertNotIn("locked but no BOARD task references this design ID",
                         html)


# ── item 2 — a project whose state IS its root, unchanged ─────────────────


class TestAProjectWhoseStateIsItsRootIsUnchanged(Rendered):
    """The configuration every non-Perry project has.

    This is the half a fix keyed on the wrong side breaks: teaching the
    launcher to export the state root, or the viewer to treat what it is given
    as one, satisfies the class above and silently re-points this one."""

    def setUp(self):
        super().setUp()
        self.flat = flat_project()
        self.nested = nested_project()
        self.addCleanup(shutil.rmtree, self.flat, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.nested, ignore_errors=True)

    def test_the_board_carries_the_projects_rows(self):
        page = self.board_of(self.flat)
        self.assertEqual(sorted(set(TASK_ID.findall(page))),
                         ["TASK-003", "TASK-004"])

    def test_both_layouts_render_the_same_rows(self):
        """One body of state, two layouts, one page. Asserted as a pair rather
        than one at a time, because each half passes on its own under a fix
        that has simply moved the disagreement."""
        rows = TASK_ID.findall(self.board_of(self.flat))
        self.assertTrue(rows, "neither layout rendered a row — this would "
                              "otherwise pass by both being empty")
        self.assertEqual(rows, TASK_ID.findall(self.board_of(self.nested)))

    def test_the_two_roots_are_the_same_directory_here(self):
        import parsers
        self.assertEqual(parsers.resolve_state_root(self.flat), self.flat)
        self.assertEqual(parsers.resolve_project_root(self.flat), self.flat)


# ── item 1, on the project the row was found on ───────────────────────────


class TestPerrysOwnConfiguration(Rendered):
    """`PERRY_HOME` itself: `State root: perry`, state in a subdirectory.

    Rendered against the live repository rather than a fixture, because a
    fixture is a shape somebody chose and this is the shape the defect was
    reported on. Nothing here asserts a particular row — the board moves — only
    that the page is a board of this project and not an empty one."""

    def setUp(self):
        super().setUp()
        self.assertTrue((PERRY_HOME / ".perry" / "config.md").exists(),
                        "PERRY_HOME is not a Perry project")

    def test_the_state_root_really_is_a_subdirectory_here(self):
        """Guards every assertion below from passing vacuously: if Perry's own
        state ever moves back to its root, this class stops testing the shape
        it was written for and says so."""
        import parsers
        self.assertNotEqual(parsers.resolve_state_root(PERRY_HOME), PERRY_HOME)

    def test_the_board_is_this_projects_board(self):
        page = self.board_of(PERRY_HOME)
        self.assertTrue(TASK_ID.findall(page),
                        "the viewer rendered an empty board for Perry itself")

    def test_the_decisions_this_project_has_recorded_are_on_the_page(self):
        """A second reader off the same root — `DECISIONS.md`, not `BOARD.md` —
        so the render is not proved by one file happening to be found."""
        page = text_of(render(PERRY_HOME, "today"))
        self.assertTrue(re.search(r"ADR-\d{3}", page),
                        "no ADR reached the page from Perry's own DECISIONS.md")


# ── item 3 — the two entrances, asserted as a pair ────────────────────────


class TestBothEntrancesLandOnTheSameTwoDirectories(unittest.TestCase):
    """`viewer/parsers.py` and `bin/perry-state --root`, fed the same value.

    Asserted as a PAIR — (project root in, state root out) — and never one at a
    time. Each side is self-consistent on its own; what was wrong was only that
    they were self-consistent about different directories."""

    def setUp(self):
        self.root = nested_project()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.addCleanup(os.environ.pop, "PERRY_PROJECT", None)

    def viewer_pair(self, root: Path) -> tuple[Path, Path]:
        os.environ["PERRY_PROJECT"] = str(root)
        import parsers
        importlib.reload(parsers)
        return parsers.PROJECT_ROOT, parsers.STATE_ROOT

    def state_pair(self, root: Path) -> tuple[Path, Path]:
        """What `perry-state --root <project>` says it read.

        Its payload spells the state root `project.root` — a third name for the
        same confusion, and a published contract this row does not get to
        rename. Read here for what it IS, so a rename later cannot make these
        two agree only in words."""
        proc = subprocess.run(
            [sys.executable, str(STATE_TOOL), "--root", str(root), "--json"],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        payload = json.loads(proc.stdout)
        self.assertTrue(payload.get("installed"), payload.get("warnings"))
        return root.resolve(), Path(payload["project"]["root"]).resolve()

    def test_the_pair_agrees_where_the_two_roots_differ(self):
        proj, state = self.viewer_pair(self.root)
        self.assertNotEqual(proj, state,
                            "the fixture's state root is not a subdirectory — "
                            "this test would pass on the defect")
        self.assertEqual((proj, state), self.state_pair(self.root))

    def test_the_pair_agrees_where_the_two_roots_are_one(self):
        flat = flat_project()
        self.addCleanup(shutil.rmtree, flat, ignore_errors=True)
        proj, state = self.viewer_pair(flat)
        self.assertEqual(proj, state)
        self.assertEqual((proj, state), self.state_pair(flat))

    def test_the_pair_agrees_on_this_repository(self):
        self.assertEqual(self.viewer_pair(PERRY_HOME), self.state_pair(PERRY_HOME))


# ── the inverse itself, round-tripped ─────────────────────────────────────


class TestTheInverseIsAnInverse(unittest.TestCase):
    """`resolve_project_root` is the inverse `viewer/parsers.py` used to say
    nobody had written. It is read off `.perry/`, which was already the stored
    answer — the anchor cannot move, because it holds the pointer."""

    def setUp(self):
        import parsers
        self.P = parsers

    def test_it_round_trips_through_a_subdirectory_state_root(self):
        root = nested_project()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        state = self.P.resolve_state_root(root)
        self.assertEqual(state, root / "state")
        self.assertEqual(self.P.resolve_project_root(state), root)

    def test_it_round_trips_on_a_state_root_that_is_the_project_root(self):
        root = flat_project()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        self.assertEqual(
            self.P.resolve_project_root(self.P.resolve_state_root(root)), root)

    def test_it_round_trips_on_this_repository(self):
        self.assertEqual(
            self.P.resolve_project_root(self.P.resolve_state_root(PERRY_HOME)),
            PERRY_HOME)

    def test_a_project_nested_under_another_is_not_claimed_by_it(self):
        """A directory holding the anchor is a project root and answers for
        itself. `outer/vendor/inner` is its own project whose state IS its
        root, and it must not be read as part of `outer`."""
        outer = nested_project()
        self.addCleanup(shutil.rmtree, outer, ignore_errors=True)
        inner = outer / "vendor" / "inner"
        (inner / ".perry").mkdir(parents=True)
        (inner / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- State root: .\n")
        self.assertEqual(self.P.resolve_project_root(inner), inner)

    def test_a_directory_that_is_not_the_outer_projects_state_root_is_its_own(self):
        """**Why the round trip and not just `.perry/`'s presence.**

        `outer/elsewhere` sits inside a Perry project and is not that
        project's state root. Walking up for an anchor alone would hand back
        `outer`, and every `.perry/` read taken off that answer — the event
        log `walk_design` counts closures from — would be another project's.
        The pointer has to come back to where the question was asked."""
        outer = nested_project()
        self.addCleanup(shutil.rmtree, outer, ignore_errors=True)
        elsewhere = outer / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "BOARD.md").write_text("# Board — not this project\n")
        self.assertEqual(self.P.resolve_project_root(elsewhere), elsewhere)

    def test_a_directory_with_no_anchor_above_it_answers_for_itself(self):
        """Every fixture and every project written before the anchor existed."""
        with tempfile.TemporaryDirectory() as tmp:
            bare = Path(tmp).resolve()
            self.assertEqual(self.P.resolve_project_root(bare), bare)


# ── the walk, against the walk it has to agree with ───────────────────────


#: `bin/perry-state § resolve_root`, called in a child process standing in a
#: chosen directory. The tool is loaded rather than run: `main()` would build a
#: whole payload, and what is being compared is the walk alone. `__name__` is
#: deliberately not `__main__`, so the module's own entry point stays asleep.
PROBE = (
    "import pathlib\n"
    f"src = pathlib.Path({str(STATE_TOOL)!r}).read_text()\n"
    f"ns = {{'__file__': {str(STATE_TOOL)!r}, '__name__': 'perry_state_probe'}}\n"
    f"exec(compile(src, {str(STATE_TOOL)!r}, 'exec'), ns)\n"
    "print(ns['resolve_root'](None))\n"
)


class TestTheCwdWalkMatchesPerryStates(unittest.TestCase):
    """`_resolve_project_root`'s walk and `bin/perry-state § resolve_root`'s
    are the same predicate, asserted rather than commented.

    The launcher exports `$PERRY_PROJECT` from its own cwd, so if these two
    walks disagreed the pair above would still be wrong for anyone who started
    the viewer from a subdirectory — the same defect one level out."""

    def setUp(self):
        self.root = nested_project()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.addCleanup(os.chdir, os.getcwd())
        self.addCleanup(os.environ.pop, "PERRY_PROJECT", None)
        os.environ.pop("PERRY_PROJECT", None)

    def walked(self, cwd: Path) -> tuple[Path, Path]:
        os.chdir(cwd)
        import parsers
        importlib.reload(parsers)
        viewer = parsers.PROJECT_ROOT
        proc = subprocess.run([sys.executable, "-c", PROBE],
                              capture_output=True, text=True, cwd=str(cwd))
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        return viewer, Path(proc.stdout.strip())

    def test_standing_in_the_project_root_both_say_the_project_root(self):
        viewer, tool = self.walked(self.root)
        self.assertEqual(viewer, self.root)
        self.assertEqual(viewer, tool)

    def test_standing_in_a_subdirectory_both_walk_up_to_the_project_root(self):
        """The case that separates the two predicates.

        Standing anywhere in the project that is neither the state root nor a
        directory holding `BOARD.md`, a walk that looks only for state files
        finds none and falls back to the CWD — while `perry-state` standing in
        the same place walks up to `.perry/config.md` and reports the project
        root. The launcher exports its own CWD, so that gap is this same row
        one level out: two tools, one directory, two projects."""
        sub = self.root / "elsewhere"
        sub.mkdir()
        viewer, tool = self.walked(sub)
        self.assertEqual(viewer, self.root)
        self.assertEqual(viewer, tool)

    def test_standing_in_the_state_root_both_say_the_same_thing(self):
        """Whatever the answer is, it must be ONE answer. `perry-state` stops
        at the first directory holding `BOARD.md`, so this is the state root
        for both — a viewer that walked further would render a project the
        `bin/` tool beside it says it is not looking at."""
        viewer, tool = self.walked(self.root / "state")
        self.assertEqual(viewer, tool)


if __name__ == "__main__":
    unittest.main(verbosity=2)
