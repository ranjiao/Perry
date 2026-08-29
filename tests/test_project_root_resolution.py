"""TASK-159 — one answer to "what is a project root", asserted on the resolvers.

Three readers each held a different answer, measured at `efa0d73`:

| where | what it meant by "project root" |
|---|---|
| `viewer/parsers.py § _resolve_project_root` | the directory holding `BOARD.md` — the STATE root |
| `bin/perry-viewer` | `$PERRY_PROJECT` — the PROJECT root |
| `bin/perry-state --root` | the PROJECT root |

On a project whose state lives in a subdirectory — **Perry's own,
`.perry/config.md § State root: perry`** — those are different directories, so
a reader handed the project root read `BOARD.md` from a directory that has none
and got an EMPTY snapshot. Measured before the fix, against this repository:
`tasks 0 · adrs 0 · phase None`.

**This module is what survived TASK-178.** The original `tests/test_project_root.py`
proved the row through the web viewer's render — `serve.py`'s route functions
against the shipped `viewer/templates/` — because at the time a resolver that
was self-consistent while the page stayed blank was the exact failure mode. The
viewer is deleted and there is no page left to render, but the resolution
contract it was proving is not the viewer's: `resolve_state_root` and
`resolve_project_root` are `viewer/parsers.py`'s, and `bin/perry-state`,
`bin/perry-task`, `bin/perry-goals`, `bin/perry-lint` and `bin/perry-diagnose`
all reach the same two directories through them. Every assertion here is one
that was **never** about rendering; the render-only classes went with the
templates.

The three claims, each of which a fix keyed on the wrong side satisfies alone:

- `TestBothEntrancesLandOnTheSameTwoDirectories` — `viewer/parsers.py` and
  `bin/perry-state --root`, fed one value, land on the same PAIR;
- `TestTheInverseIsAnInverse` — `resolve_project_root` really is the inverse of
  `resolve_state_root`, round-tripped both ways;
- `TestTheCwdWalkMatchesPerryStates` — the two walks that answer "which project
  am I standing in" are the same predicate.

Run: python3 tests/parallel -j 4 test_project_root_resolution
"""

from __future__ import annotations

import importlib
import json
import os
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

from test_kr_progress_provenance import build_project  # noqa: E402

STATE_TOOL = PERRY_HOME / "bin" / "perry-state"

#: State files a fixture moves when its state root is a subdirectory.
#: `.perry/` is NOT among them, and that is the rule the inverse is read off:
#: it holds the pointer, so it cannot sit behind it.
MOVES = ("BOARD.md", "OKR.md", "ARCHITECTURE.md", "tasks.jsonl", "phase")

ARCHITECTURE = "# Architecture\n\n## Layers\n\nOne fixture, two layouts.\n"

#: The store rows that reach a board lane. TASK-146's fixture files its records
#: with no `group`, because the chain reads them by id and never asks which
#: section they sit in; a board reads nothing else.
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
    fixture, so the two layouts differ in nothing but where the state sits."""
    root = flat_project()
    dest = root / sub
    dest.mkdir(parents=True)
    for name in MOVES:
        shutil.move(str(root / name), str(dest / name))
    (root / ".perry" / "config.md").write_text(
        f"# Perry configuration\n\n- State root: {sub}\n")
    return root


def roots_of(root: Path) -> tuple[Path, Path]:
    """`(PROJECT_ROOT, STATE_ROOT)` as `viewer/parsers.py` resolves them.

    `root` is the PROJECT root — what `bin/perry-state --root` takes and what
    `$PERRY_PROJECT` carried. Passing anything else here would be testing a
    configuration no entrance produces. Both roots are module globals frozen at
    import, so the module is reloaded per fixture."""
    os.environ["PERRY_PROJECT"] = str(root)
    import parsers
    importlib.reload(parsers)
    return parsers.PROJECT_ROOT, parsers.STATE_ROOT


# ── the bounded walk the inverse replaced ─────────────────────────────────


class TestTheInverseReachesWhatTheBoundedWalkCannot(unittest.TestCase):
    """`walk_design` looks for `.perry/events.jsonl` by walking up FOUR levels
    from the state root, because when it was written there was no inverse to
    ask. Four is a guess, and this fixture is the fifth level.

    Asserted on `DesignDoc.impl_refs`, where the count is the difference
    between "1 task" and "no refs" — the design-handoff signal `walk_design`'s
    own docstring says shipped code was reported as never handed off for.
    TASK-178 moved this off the `/design` page and onto the snapshot the page
    was reading; the number and its meaning are unchanged."""

    DOC = ("# DESIGN-009 — a thing\n\n"
           "> **Status**: locked 2026-08-01\n> **Date**: 2026-08-01\n\n"
           "## Plan\n\nOne doc, five levels down.\n")

    def setUp(self):
        self.addCleanup(os.environ.pop, "PERRY_PROJECT", None)
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
        proj, state = roots_of(self.root)
        self.assertNotEqual(proj, state,
                            "the fixture's state root is not a subdirectory — "
                            "this test would pass on the defect")
        import parsers
        snap = parsers.load_snapshot(state)
        docs = {d.id: d for d in snap.design}
        self.assertIn("DESIGN-009", docs)
        self.assertEqual(docs["DESIGN-009"].impl_refs, 1)


# ── item 2 — a project whose state IS its root, unchanged ─────────────────


class TestAProjectWhoseStateIsItsRootIsUnchanged(unittest.TestCase):
    """The configuration every non-Perry project has.

    This is the half a fix keyed on the wrong side breaks: teaching a caller to
    export the state root, or a reader to treat what it is given as one,
    satisfies the nested shape and silently re-points this one."""

    def setUp(self):
        self.addCleanup(os.environ.pop, "PERRY_PROJECT", None)
        self.flat = flat_project()
        self.addCleanup(shutil.rmtree, self.flat, ignore_errors=True)

    def test_the_two_roots_are_the_same_directory_here(self):
        import parsers
        self.assertEqual(parsers.resolve_state_root(self.flat), self.flat)
        self.assertEqual(parsers.resolve_project_root(self.flat), self.flat)


# ── item 1, on the project the row was found on ───────────────────────────


class TestPerrysOwnConfiguration(unittest.TestCase):
    """`PERRY_HOME` itself: `State root: perry`, state in a subdirectory.

    Asserted against the live repository rather than a fixture, because a
    fixture is a shape somebody chose and this is the shape the defect was
    reported on."""

    def setUp(self):
        self.assertTrue((PERRY_HOME / ".perry" / "config.md").exists(),
                        "PERRY_HOME is not a Perry project")

    def test_the_state_root_really_is_a_subdirectory_here(self):
        """Guards the repository-shaped assertions from passing vacuously: if
        Perry's own state ever moves back to its root, the classes written for
        that shape stop testing it and this says so."""
        import parsers
        self.assertNotEqual(parsers.resolve_state_root(PERRY_HOME), PERRY_HOME)

    def test_the_snapshot_off_perrys_own_project_root_is_not_empty(self):
        """The whole defect, on the project it was found on.

        Before this row the same call read `BOARD.md` from a directory that has
        none and produced a snapshot with no tasks and no ADRs — not an error,
        not a warning, an empty project."""
        proj, state = roots_of(PERRY_HOME)
        import parsers
        snap = parsers.load_snapshot(state)
        self.assertTrue(snap.board.all_tasks,
                        "an empty board was read for Perry itself")
        self.assertTrue(snap.adrs,
                        "no ADR reached the snapshot from Perry's own "
                        "`decisions/`")

    def tearDown(self):
        os.environ.pop("PERRY_PROJECT", None)


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
        proj, state = roots_of(self.root)
        self.assertNotEqual(proj, state,
                            "the fixture's state root is not a subdirectory — "
                            "this test would pass on the defect")
        self.assertEqual((proj, state), self.state_pair(self.root))

    def test_the_pair_agrees_where_the_two_roots_are_one(self):
        flat = flat_project()
        self.addCleanup(shutil.rmtree, flat, ignore_errors=True)
        proj, state = roots_of(flat)
        self.assertEqual(proj, state)
        self.assertEqual((proj, state), self.state_pair(flat))

    def test_the_pair_agrees_on_this_repository(self):
        self.assertEqual(roots_of(PERRY_HOME), self.state_pair(PERRY_HOME))


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

    A caller that takes its project root from its own cwd — which is what every
    `bin/` tool invoked with no `--root` does — would otherwise be reading a
    different project than the tool beside it, for anyone standing in a
    subdirectory: the same defect one level out."""

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
        walked = parsers.PROJECT_ROOT
        proc = subprocess.run([sys.executable, "-c", PROBE],
                              capture_output=True, text=True, cwd=str(cwd))
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        return walked, Path(proc.stdout.strip())

    def test_standing_in_the_project_root_both_say_the_project_root(self):
        parsed, tool = self.walked(self.root)
        self.assertEqual(parsed, self.root)
        self.assertEqual(parsed, tool)

    def test_standing_in_a_subdirectory_both_walk_up_to_the_project_root(self):
        """The case that separates the two predicates.

        Standing anywhere in the project that is neither the state root nor a
        directory holding `BOARD.md`, a walk that looks only for state files
        finds none and falls back to the CWD — while `perry-state` standing in
        the same place walks up to `.perry/config.md` and reports the project
        root. Two tools, one directory, two projects."""
        sub = self.root / "elsewhere"
        sub.mkdir()
        parsed, tool = self.walked(sub)
        self.assertEqual(parsed, self.root)
        self.assertEqual(parsed, tool)

    def test_standing_in_the_state_root_both_say_the_same_thing(self):
        """Whatever the answer is, it must be ONE answer. `perry-state` stops
        at the first directory holding `BOARD.md`, so this is the state root
        for both — a reader that walked further would load a project the `bin/`
        tool beside it says it is not looking at."""
        parsed, tool = self.walked(self.root / "state")
        self.assertEqual(parsed, tool)


# ── TASK-164 — the two globals the tool leaves behind ─────────────────────


#: `bin/perry-state § main`, run in a child process against one project root,
#: reporting what it LEFT IN `viewer/parsers.py`'s two root globals. The tool is
#: loaded and `main()` called rather than the script being run, because the
#: globals are what is being measured and a finished subprocess has none left to
#: read. Its payload goes to a buffer; only the roots come back on stdout.
GLOBALS_PROBE = (
    "import contextlib, io, json, pathlib, sys\n"
    f"src = pathlib.Path({str(STATE_TOOL)!r}).read_text()\n"
    f"ns = {{'__file__': {str(STATE_TOOL)!r}, '__name__': 'perry_state_probe'}}\n"
    f"exec(compile(src, {str(STATE_TOOL)!r}, 'exec'), ns)\n"
    "with contextlib.redirect_stdout(io.StringIO()):\n"
    "    rc = ns['main'](['--root', sys.argv[1], '--json'])\n"
    "P = ns['P']\n"
    "print(json.dumps({\n"
    "    'rc': rc,\n"
    "    'project_root': str(P.PROJECT_ROOT),\n"
    "    'state_root': str(P.STATE_ROOT),\n"
    "    'hook_under_project_root': (P.PROJECT_ROOT / '.perry' / 'hook.md').exists(),\n"
    "    'hook_under_state_root': (P.STATE_ROOT / '.perry' / 'hook.md').exists(),\n"
    "}))\n"
)

#: A hook with one backticked fragment in it. The content is beside the point
#: here — what is asserted is that the FILE is reachable from the global whose
#: name says `.perry/` is anchored under it.
HOOK = ("# Perry hook — fixture\n\n## High-stakes operations\n\n"
        "- Publishing to a public repo — `git push`\n")

#: `nested_project()`'s default subdirectory, spelled out rather than resolved,
#: so this class asserts against a directory it chose and not against the
#: resolver it is checking the callers of.
SUB = "state"


class TestTheToolLeavesEachGlobalMeaningItsName(unittest.TestCase):
    """`bin/perry-state § main` overrides `viewer/parsers.py`'s root globals so
    that `--root` survives whatever cwd the script was invoked from. It used to
    override ONE of them with the OTHER one's value:

        root = P.resolve_state_root(project_root)   # the STATE root
        P.PROJECT_ROOT = root                       # the PROJECT root global

    On every project whose state IS its root the two are one directory and the
    inversion is invisible — which is every project but this one. On a project
    with `State root: <subdir>` it left `PROJECT_ROOT` naming a directory with
    no `.perry/` under it, and `.perry/` is the one thing that name promises:
    it holds the pointer, so it cannot sit behind it.

    **It has already cost once, and was fixed at one call site rather than at
    the global.** `--escalation-scan`, handed the state root, found zero
    fragments and reported a clean `unarmed` — a safety gate saying it has
    nothing to check, from a project whose hook lists thirty things.

    So `.perry/hook.md` is asserted DIRECTLY here, never through that gate's
    verdict: `unarmed` has two causes — nothing declared, and nothing found —
    and reading the verdict instead of the file is exactly how this hid the
    first time.

    TASK-164."""

    def setUp(self):
        self.root = nested_project(SUB)
        self.state = self.root / SUB
        (self.root / ".perry" / "hook.md").write_text(HOOK)
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.addCleanup(os.environ.pop, "PERRY_PROJECT", None)
        os.environ.pop("PERRY_PROJECT", None)

    def probe(self, root: Path, cwd: str | None = None) -> dict:
        proc = subprocess.run([sys.executable, "-c", GLOBALS_PROBE, str(root)],
                              capture_output=True, text=True, cwd=cwd)
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        return json.loads(proc.stdout)

    def test_the_fixture_really_separates_the_two_roots(self):
        """Without this the rest of the class would pass on the defect."""
        self.assertNotEqual(self.root, self.state)
        self.assertTrue((self.root / ".perry" / "hook.md").exists())
        self.assertFalse((self.state / ".perry" / "hook.md").exists())

    def test_the_project_root_global_holds_the_project_root(self):
        seen = self.probe(self.root)
        self.assertEqual(Path(seen["project_root"]), self.root)
        self.assertNotEqual(seen["project_root"], seen["state_root"])

    def test_the_state_root_global_holds_the_state_root(self):
        seen = self.probe(self.root)
        self.assertEqual(Path(seen["state_root"]), self.state)

    def test_a_project_root_anchored_file_is_found_after_the_tool_has_run(self):
        """The case that already failed once, asserted on the file itself."""
        seen = self.probe(self.root)
        self.assertTrue(
            seen["hook_under_project_root"],
            "`.perry/hook.md` is not under PROJECT_ROOT — the state root was "
            "assigned to the project root global")
        self.assertFalse(
            seen["hook_under_state_root"],
            "the fixture's state root holds a `.perry/`, so the assertion "
            "above could not have failed on the defect")

    def test_the_pair_survives_an_unrelated_cwd(self):
        """The requirement that motivated the assignment in the first place.

        Run from `/tmp`, which holds no project of its own and is not an
        ancestor of anything either global would otherwise walk to."""
        seen = self.probe(self.root, cwd=tempfile.gettempdir())
        self.assertEqual(seen["rc"], 0)
        self.assertEqual(Path(seen["project_root"]), self.root)
        self.assertEqual(Path(seen["state_root"]), self.state)
        self.assertTrue(seen["hook_under_project_root"])

    def test_a_project_whose_state_is_its_root_is_unchanged(self):
        flat = flat_project()
        self.addCleanup(shutil.rmtree, flat, ignore_errors=True)
        (flat / ".perry" / "hook.md").write_text(HOOK)
        seen = self.probe(flat)
        self.assertEqual(Path(seen["project_root"]), flat)
        self.assertEqual(Path(seen["state_root"]), flat)
        self.assertTrue(seen["hook_under_project_root"])

    def test_on_this_repository(self):
        """Perry's own layout — the one the row was found on."""
        seen = self.probe(PERRY_HOME)
        self.assertEqual(Path(seen["project_root"]), PERRY_HOME)
        self.assertNotEqual(seen["project_root"], seen["state_root"])
        self.assertTrue(seen["hook_under_project_root"])
        self.assertFalse(seen["hook_under_state_root"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
