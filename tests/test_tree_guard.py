"""`tests/tree_guard.py` — and the plant that shows it can actually fail.

A "the tree must not move" check is exactly the kind of guard that rots. It is
green on every honest run, which is every run, so nothing ever exercises the
branch that fails — and a guard whose failing branch is never taken is
indistinguishable from a guard that has been broken for a year. This project
has failed three rows in two days for shipping one.

So the load-bearing test here is not the unit coverage of `manifest` and
`compare` below it. It is `TestThePlantedWrite`, which unpacks this repository
at its last commit into a scratch directory, drops a test module into the copy
that writes into the copy's own root, runs the **real** `bash tests/run` there,
and requires that the suite comes back red naming the two paths that moved. Its
mutation half neuters `tree_guard.compare` in a second copy and requires the
same planted run to come back GREEN — because a red that would have been red
anyway proves nothing about the guard.

**Three things here exist because a V4 reviewer defeated the first version.**
`test_all_three_ignore_lists_are_the_documented_ones` — the first version
pinned two of the three lists, and blinding `IGNORE_NAMES` to `events.jsonl`
and `intake.jsonl` left all thirteen tests green.
`test_the_four_files_of_this_row_are_never_invisible` pins the same thing by
consequence rather than by name, so a fourth list invented tomorrow is caught
too. And `TestTheEnvironmentTheGuardCanSee` covers the vector the tree
comparison structurally cannot see: `$PERRY_PROJECT` aimed at a second
checkout, where all four files moved over there while step 0 truthfully
reported this tree unmoved.

The planting is into a COPY, never the live checkout: `work/reference/
review-constraints.md` says so, and the reason is that for the seconds the
plant exists, anything else running the suite sees a real, reproducible-looking
failure about nothing.

**And the copy is built from a commit, not from the live working tree.** That
direction matters too and it is the newer half: the first version read the tree
with `shutil.copytree` and reddened the moment anything else was writing to it.
See `copy_repo` (TASK-258).
"""

from __future__ import annotations

import io
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import threading
import unittest
from pathlib import Path

import tree_guard as TG

PERRY_HOME = Path(__file__).resolve().parent.parent

#: A module the runner will discover in the copy. It writes into the root it
#: finds — a `M` (an existing file changed) and a `+` (a file created), which
#: are two of the three verdicts `compare` can reach. `perry/BOARD.md` is the
#: file TASK-249's real defect moved.
PLANT = '''"""Planted by tests/test_tree_guard.py. Writes into its own root on
purpose — this module exists to be caught, and it only ever lives in a copy."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestAModuleThatWritesIntoTheLiveRoot(unittest.TestCase):
    def test_the_write_itself_passes(self):
        """It passes. That is the point: the module is GREEN and the suite
        must still come back red, because the tree moved."""
        with open(ROOT / "perry" / "BOARD.md", "a", encoding="utf-8") as fh:
            fh.write("\\n<!-- planted by TASK-249's guard test -->\\n")
        (ROOT / ".perry" / "task-249-planted.txt").write_text("planted\\n")
        self.assertTrue((ROOT / ".perry" / "task-249-planted.txt").exists())
'''

#: The control. Same shape, same runner path, writes only into a temp dir —
#: which is what every well-behaved module in this suite does. Without it, a
#: red planted run could mean "the guard works" or "`--only` is broken".
CONTROL = '''"""Planted by tests/test_tree_guard.py. Writes into a temp dir,
like every well-behaved module here. The suite must come back GREEN."""

import tempfile
import unittest
from pathlib import Path


class TestAModuleThatWritesWhereItShould(unittest.TestCase):
    def test_it_writes_into_a_temp_root(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "BOARD.md").write_text("a board in a temp root\\n")
            self.assertTrue((Path(d) / "BOARD.md").exists())
'''

PLANT_MODULE = "test_zz_task_249_planted_write.py"
CONTROL_MODULE = "test_zz_task_249_control.py"


#: Dropped from the fixture, exactly as the `shutil.copytree` version dropped
#: them. `git archive` omits all four today — `.git` is not tracked content,
#: `__pycache__/` and `*.pyc` are in `.gitignore`, and `git ls-files '*.pyo'`
#: is empty — but the exclusion is spelled out and applied here anyway,
#: because it is a property this fixture must have rather than a side effect
#: of whichever tool builds it and of what `.gitignore` says on the day.
#: `test_the_caches_are_excluded_and_not_merely_absent` is that distinction,
#: and the reason for wanting the property is unchanged: a stale `.pyc` beside
#: a source file whose mtime no longer matches is its own class of false
#: result, and the copy has no reason to carry one.
EXCLUDED_DIRS = (".git", "__pycache__")
EXCLUDED_SUFFIXES = (".pyc", ".pyo")

#: **The fenced exception, and the only read of the live tree left in here.**
#:
#: Everything in the fixture is the committed content — which is what makes it
#: stable — and for almost every file that is also what these tests want, since
#: they are testing the guard and not the rest of the repository. But three
#: files decide the ANSWER the copied suite gives: `tests/run` is the wiring
#: under test, `tests/tree_guard.py` is the guard it wires in, and
#: `tests/parallel` is what step 2 shells out to. Build those three from HEAD
#: and an uncommitted fix to any of them is never exercised: you edit
#: `tests/run`, this module runs the committed version, reports green, and you
#: have been told about a file you did not write. That is the same false green
#: this module exists to prevent, so the three are overlaid from the working
#: tree.
#:
#: They are safe to overlay for the same reason the rest is not: they are
#: hand-edited sources, not state a running process rewrites. The PMO writes
#: `perry/BOARD.md`, `.perry/events.jsonl` and the journal on every command;
#: nothing writes `tests/run` except a person or an agent editing it, and both
#: do it by rename. The residual is stated rather than closed: an uncommitted
#: edit to a file OUTSIDE this list is not exercised by the copied suite. For
#: `bin/perry-lint` — the only other file the copied run executes, at step 1 —
#: that is an improvement, since a locally broken linter reddening this module
#: was never information about the tree guard.
LIVE_FILES = ("tests/run", "tests/tree_guard.py", "tests/parallel")

_SNAPSHOT: tuple[str, bytes] | None = None


def _snapshot(root: Path) -> tuple[str, bytes]:
    """`(sha, tarball)` for `root` at HEAD. Built once per process.

    Once, and cached, so that a commit landing mid-run cannot move the fixture
    between one test and the next — eight copies of two different trees would
    be a slower version of the same disease.
    """
    global _SNAPSHOT
    if _SNAPSHOT is not None and root == PERRY_HOME:
        return _SNAPSHOT
    rev = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                         capture_output=True, text=True)
    if rev.returncode != 0:
        raise RuntimeError(
            f"tests/test_tree_guard.py builds its fixture from the last commit "
            f"of {root}, and `git rev-parse HEAD` failed there:\n{rev.stderr}")
    sha = rev.stdout.strip()
    tar = subprocess.run(["git", "-C", str(root), "archive", "--format=tar", sha],
                         capture_output=True)
    if tar.returncode != 0:
        raise RuntimeError(
            f"`git archive {sha}` failed in {root}:\n"
            f"{tar.stderr.decode('utf-8', 'replace')}")
    snap = (sha, tar.stdout)
    if root == PERRY_HOME:
        _SNAPSHOT = snap
    return snap


def _excluded(name: str) -> bool:
    return (any(part in EXCLUDED_DIRS for part in name.split("/"))
            or name.endswith(EXCLUDED_SUFFIXES))


def copy_repo(dest: Path, root: Path = PERRY_HOME) -> Path:
    """This repository **at its last commit**, in a scratch dir.

    The first version of this was `shutil.copytree(PERRY_HOME, ...)` over the
    LIVE working tree, and it reddened this module the first time it ran
    anywhere other than a private worktree. A copy of a directory another
    process is writing is a copy of no state at all: a file that exists at
    `scandir` and is gone by `copy2` raises `shutil.Error` — seven of the
    tests here died that way, in `copy_repo`, before reaching an assertion —
    and a file caught mid-write arrives in the fixture truncated, which is
    worse because it produces a plausible red instead of a traceback. Neither
    says anything about the guard.

    Four TASK-249 review rounds missed it because all four ran in private
    worktrees where nothing else was writing, which is exactly how a test that
    depends on the tree being still passes review. On the live checkout the
    PMO writes board, journal and event state on every command and dispatched
    agents edit `bin/` and `tests/` while the suite runs (TASK-258).

    So the fixture is unpacked from `git archive`: a tarball of a COMMIT, a
    state no concurrent write can move. That is this project's existing answer
    rather than a new one: *"Every destructive probe ran against `git archive`
    copies of `HEAD` and of `main`"* is how the TASK-235 V4 review states its
    method, and TASK-226, TASK-233 and TASK-243 say the same, for the same
    reason.

    On a still checkout the two agree exactly: extracting the archive and
    running the `copytree` this replaces produced the same set of paths with
    the same modes and the same sizes, measured on `d49964e` (846 entries,
    zero differences). So nothing downstream of the fixture changes; only the
    behaviour under a tree that is moving does.

    Three files are then overlaid from the working tree; `LIVE_FILES` above
    says which and why.
    """
    _, tarball = _snapshot(root)
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:") as tf:
        members = [m for m in tf.getmembers() if not _excluded(m.name)]
        # `tar` keeps the archive's own mode bits, and the mode is half of
        # what `manifest` records — a fixture that flattened the executable
        # bit off `bin/` would be a different tree from the one committed.
        # The keyword arrived in 3.12 and was backported to 3.11.4; asking
        # whether this interpreter has it beats both alternatives, since
        # passing it always breaks the older 3.11s this project still runs on
        # and omitting it always leaves the policy to whatever the running
        # Python defaults to.
        kwargs = {"filter": "tar"} if hasattr(tarfile, "tar_filter") else {}
        tf.extractall(dest, members=members, **kwargs)
    for rel in LIVE_FILES:
        src = root / rel
        if not src.is_file():
            continue
        target = dest / rel
        data = src.read_bytes()
        if not target.is_file() or target.read_bytes() != data:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        target.chmod(src.stat().st_mode & 0o7777)
    return dest


def run_suite(root: Path, module: str,
              perry_project: str | None = None) -> subprocess.CompletedProcess:
    """`bash tests/run --only <module>` in `root` — the real runner.

    Not `tree_guard.py` called directly: what is under test is whether the
    SUITE fails, which is a property of `tests/run`'s wiring as much as of the
    guard. TASK-249's defect was in wiring, not in an algorithm.

    `PERRY_PROJECT` is stripped unless a test asks for it, so that an ambient
    one in the outer runner's environment cannot decide the answer here.
    """
    env = dict(os.environ)
    env.pop("PERRY_PROJECT", None)
    if perry_project is not None:
        env["PERRY_PROJECT"] = perry_project
    return subprocess.run(
        ["bash", "tests/run", "--only", module.removesuffix(".py")],
        cwd=str(root), capture_output=True, text=True, env=env)


class TestTheFixtureIsASnapshotAndNotTheLiveTree(unittest.TestCase):
    """**The fixture under a tree that is being written to.**

    Every other test in this file needs `copy_repo` to have worked before it
    can assert anything, so none of them can say what it produced or when it
    is allowed to fail. This one asks the question directly, and it asks it
    against a throwaway repository rather than this one, because a test that
    demonstrated the hazard by writing into the live checkout would be the
    hazard.

    The two halves are the two claims `copy_repo` makes. A tree being churned
    while it is copied yields the committed tree anyway — that is the fix. And
    an uncommitted edit to one of the three `LIVE_FILES` reaches the copy
    regardless — that is the fence, and without a test it is a comment.
    """

    def _repo(self, path: Path, files: dict[str, str]) -> Path:
        path.mkdir(parents=True)
        for rel, body in files.items():
            (path / rel).parent.mkdir(parents=True, exist_ok=True)
            (path / rel).write_text(body)
        git = ["git", "-C", str(path), "-c", "user.email=t@example.invalid",
               "-c", "user.name=t", "-c", "commit.gpgsign=false"]
        for argv in (["init", "-q"], ["add", "-A"],
                     ["commit", "-qm", "the committed state"]):
            r = subprocess.run(git + argv, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0,
                             f"{argv[0]} failed: {r.stdout}{r.stderr}")
        return path

    def test_a_tree_being_written_to_still_yields_the_committed_tree(self):
        """The reproduction of TASK-258, small enough to live in the suite.

        `shutil.copytree` here dies with `shutil.Error` on the first file that
        is unlinked between `scandir` and `copy2`; that is how this module
        reddened in the live checkout, seven tests at a time, with the message
        naming a file no test had ever heard of. Unpacking a commit cannot
        see the writes at all — not "usually does not", cannot: the tarball
        was built before the loop below started.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            committed = {f"d{d}/f{i}.txt": f"{d}/{i}\n"
                         for d in range(12) for i in range(40)}
            repo = self._repo(tmp / "repo", committed)

            stop = threading.Event()
            churned: list[str] = []

            def churn():
                # What the live checkout does to itself: state files written
                # by rename, so paths appear AND disappear under a walk.
                n = 0
                while not stop.is_set():
                    for d in range(12):
                        rel = f"d{d}/churn-{n}.txt"
                        (repo / (rel + ".tmp")).write_text("churn\n")
                        (repo / (rel + ".tmp")).rename(repo / rel)
                        churned.append(rel)
                        prev = repo / f"d{d}/churn-{n - 1}.txt"
                        if prev.exists():
                            prev.unlink()
                    n += 1

            writer = threading.Thread(target=churn, daemon=True)
            writer.start()
            self.addCleanup(stop.set)
            try:
                for attempt in range(4):
                    dest = tmp / f"copy{attempt}"
                    got = {str(p.relative_to(dest))
                           for p in copy_repo(dest, root=repo).rglob("*")
                           if p.is_file()}
                    self.assertEqual(
                        got, set(committed),
                        "the fixture is not the committed tree — it saw the "
                        "writes landing while it was built")
            finally:
                stop.set()
                writer.join(timeout=10)
            self.assertTrue(churned, "the writer never wrote; this test "
                                     "measured a still tree and proved nothing")

    def test_an_uncommitted_edit_to_a_live_file_reaches_the_copy(self):
        """The fence, asserted in both directions.

        `tests/run` uncommitted must be the one the copied suite runs, or an
        unfinished fix to the wiring is reported on by a module that ran the
        committed version instead. Everything else uncommitted must NOT be,
        or the stability the snapshot buys is given straight back.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo = self._repo(tmp / "repo", {"tests/run": "committed\n",
                                             "bin/perry-lint": "committed\n"})
            (repo / "tests" / "run").write_text("uncommitted\n")
            (repo / "bin" / "perry-lint").write_text("uncommitted\n")
            (repo / "scratch.txt").write_text("never committed\n")

            root = copy_repo(tmp / "copy", root=repo)
            self.assertIn("tests/run", LIVE_FILES)
            self.assertEqual((root / "tests" / "run").read_text(),
                             "uncommitted\n",
                             "tests/run is the wiring under test and the copy "
                             "got the committed version of it")
            self.assertEqual((root / "bin" / "perry-lint").read_text(),
                             "committed\n",
                             "the overlay is not fenced — it carried a file "
                             "that is not in LIVE_FILES")
            self.assertFalse((root / "scratch.txt").exists(),
                             "an untracked file reached the fixture, so the "
                             "fixture is reading the working tree after all")

    def test_the_caches_are_excluded_and_not_merely_absent(self):
        """`git archive` omits ignored paths, so this exclusion looks free —
        which is why it is asserted rather than assumed. A committed
        `__pycache__` (or a repository whose `.gitignore` stops ignoring one)
        would otherwise walk straight into the fixture, and a stale `.pyc`
        beside a source whose mtime no longer matches is its own class of
        false result.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo = self._repo(tmp / "repo", {
                "keep.py": "x = 1\n",
                "__pycache__/keep.cpython-313.pyc": "bytecode\n",
                "sub/stale.pyc": "bytecode\n",
                "sub/stale.pyo": "bytecode\n"})
            root = copy_repo(tmp / "copy", root=repo)
            self.assertTrue((root / "keep.py").is_file())
            for rel in ("__pycache__/keep.cpython-313.pyc", "sub/stale.pyc",
                        "sub/stale.pyo"):
                with self.subTest(excluded=rel):
                    self.assertFalse((root / rel).exists(),
                                     f"{rel} was committed and the fixture "
                                     f"carried it in anyway")


class TestTheEnvironmentTheGuardCanSee(unittest.TestCase):
    """**The fourth defeat vector, and it was live on this machine.**

    The guard hashes `$ROOT` and only `$ROOT`. `perry-task` resolves its
    project root from `$PERRY_PROJECT` *before* the cwd — so an agent running
    the suite in a worktree with `$PERRY_PROJECT` exported at the main checkout
    sends every un-rooted write into that other tree, and step 0 truthfully
    reports THIS one unmoved. A reviewer demonstrated it: all four files moved
    in a second checkout while step 0 printed `✓ nothing under … moved`.

    `tests/run` refuses to start in that environment. It does not silently
    re-point the variable — exporting `PERRY_PROJECT="$ROOT"` was tried first
    and reddens nine tests in `test_config_store_readers` that need it ABSENT.
    """

    def test_a_foreign_perry_project_refuses_the_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo(Path(tmp) / "repo")
            victim = Path(tmp) / "victim"
            victim.mkdir()
            (root / "tests" / CONTROL_MODULE).write_text(CONTROL)
            r = run_suite(root, CONTROL_MODULE, perry_project=str(victim))
            out = r.stdout + r.stderr

            self.assertEqual(r.returncode, 2,
                             "the suite ran with PERRY_PROJECT aimed at "
                             "another tree:\n" + out)
            self.assertIn("refusing to run", out)
            self.assertIn(str(victim), out,
                          "the refusal must name the directory it is "
                          "refusing:\n" + out)
            self.assertNotIn("schema drift guard", out,
                             "the refusal has to come BEFORE step 1 — after "
                             "it, tests have already run:\n" + out)

    def test_perry_project_equal_to_the_root_is_allowed(self):
        """The refusal must not be satisfied by refusing everything. Pointed
        at the tree the guard watches, the variable is harmless — that is the
        state `cd "$ROOT"` already produces — and the run proceeds.

        Note what this passes: `root.resolve()`, which is the ONE spelling
        that cannot trip a raw string comparison against `pwd -P`. It is kept
        as the plain case; the test below is the one that exercises the
        spellings a reviewer found refused.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo(Path(tmp) / "repo")
            (root / "tests" / CONTROL_MODULE).write_text(CONTROL)
            r = run_suite(root, CONTROL_MODULE,
                          perry_project=str(root.resolve()))
            out = r.stdout + r.stderr
            self.assertEqual(r.returncode, 0, out)
            self.assertIn("nothing under", out)

    def test_other_spellings_of_this_root_are_this_root(self):
        """**The test above was built so that it could not observe the bug.**

        `tests/run` computed `$ROOT` with `pwd -P` and compared
        `$PERRY_PROJECT` to it as a raw string, while `bin/perry-task` does
        `Path(...).resolve()`. Two environments that name this very tree were
        therefore refused, measured on `8dfd25e`: a symlink alias of the root,
        and the root with a trailing slash. Both would have written INSIDE the
        tree step 0 hashes — a false refusal in a guard whose argument for
        refusing is that it costs nothing — and the test above could not see
        either, because `root.resolve()` is exactly the spelling that survives
        a raw comparison.

        So: each accepted spelling asserted accepted, and — in the same test,
        because "accept everything" is the way a resolution fix goes wrong —
        a genuinely foreign root and a foreign root reached through a symlink
        asserted still refused.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo(Path(tmp) / "repo")
            (root / "tests" / CONTROL_MODULE).write_text(CONTROL)
            alias = Path(tmp) / "alias"
            alias.symlink_to(root, target_is_directory=True)
            foreign = Path(tmp) / "victim"
            foreign.mkdir()
            foreign_alias = Path(tmp) / "victim-alias"
            foreign_alias.symlink_to(foreign, target_is_directory=True)

            for label, value in (("a symlink alias of the root", str(alias)),
                                 ("the root with a trailing slash",
                                  str(root) + "/"),
                                 ("the unresolved root", str(root))):
                with self.subTest(spelling=label):
                    r = run_suite(root, CONTROL_MODULE, perry_project=value)
                    out = r.stdout + r.stderr
                    self.assertEqual(
                        r.returncode, 0,
                        f"{label} names the tree the guard watches and every "
                        f"un-rooted write would land inside it, and the suite "
                        f"refused to run:\n{out}")
                    self.assertIn("nothing under", out)

            for label, value in (("a foreign root", str(foreign)),
                                 ("a foreign root through a symlink",
                                  str(foreign_alias)),
                                 ("a root that does not exist",
                                  str(Path(tmp) / "nowhere"))):
                with self.subTest(spelling=label):
                    r = run_suite(root, CONTROL_MODULE, perry_project=value)
                    out = r.stdout + r.stderr
                    self.assertEqual(
                        r.returncode, 2,
                        f"resolving the comparison must not turn it into "
                        f"accept-everything: {label} was allowed to run:\n"
                        f"{out}")
                    self.assertIn("refusing to run", out)

    def test_a_differently_cased_spelling_of_this_root_is_this_root(self):
        """**The spelling the `cd … && pwd -P` fix did NOT close.**

        `pwd -P` collapses symlinks; it does not canonicalise case, and
        neither does `Path.resolve()`. So on a case-insensitive filesystem
        `$ROOT` typed in another case `cd`s into the same real directory,
        `perry-task` would compute the same differently-cased string and
        write into that same real directory — inside the tree step 0 hashes —
        and the resolved-string comparison refused it anyway. Round 3 of the
        V4 review measured it as a surviving false refusal, of exactly the
        class the resolution fix was raised to close.

        `test A -ef B` asks the question the guard actually cares about —
        same device, same inode — and answers it for every casing the
        filesystem folds together, without asserting anything about
        filesystems that do not fold them.

        Skipped where the filesystem is case-SENSITIVE: there the two
        spellings are two different directories and refusing is right.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo(Path(tmp) / "repo")
            (root / "tests" / CONTROL_MODULE).write_text(CONTROL)
            flipped = root.with_name(root.name.upper())
            if not (flipped.exists()
                    and os.path.samefile(str(flipped), str(root))):
                self.skipTest("this filesystem is case-sensitive, so "
                              f"{flipped} is not {root}")
            r = run_suite(root, CONTROL_MODULE, perry_project=str(flipped))
            out = r.stdout + r.stderr
            self.assertEqual(
                r.returncode, 0,
                f"{flipped} is the same directory as {root} on this "
                f"filesystem — every un-rooted write would land inside the "
                f"tree step 0 hashes — and the suite refused to run:\n{out}")
            self.assertIn("nothing under", out)

    def test_a_relative_perry_project_is_refused_and_says_why(self):
        """**The regression the resolution fix introduced, decided rather
        than inherited.**

        At `8dfd25e` a raw string comparison refused `.` and `tests/..`.
        `cd … && pwd -P` accepted them, and so would `-ef`, because this
        script has already `cd`ed to `$ROOT` — so the fix newly certified as
        "this tree" a value whose meaning is the reader's cwd. `perry-task`
        resolves it against each subprocess's cwd, and tests routinely pass
        `cwd=` a temp directory, so the two resolutions can disagree. Round 3
        could not construct a live escape in this suite and named it a
        residual; the answer taken here is that a value whose meaning depends
        on who reads it cannot be certified by a check whose whole job is to
        say where the writes will land.

        Both halves are asserted: refused, AND the refusal explains that it
        is the relativity and not a wrong directory — otherwise the reader of
        `PERRY_PROJECT=.` inside `$ROOT` is told their own tree is somewhere
        else.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo(Path(tmp) / "repo")
            (root / "tests" / CONTROL_MODULE).write_text(CONTROL)
            for value in (".", "tests/.."):
                with self.subTest(spelling=value):
                    r = run_suite(root, CONTROL_MODULE, perry_project=value)
                    out = r.stdout + r.stderr
                    self.assertEqual(
                        r.returncode, 2,
                        f"PERRY_PROJECT={value!r} resolves against whichever "
                        f"cwd reads it, and the run was allowed:\n{out}")
                    self.assertIn("refusing to run", out)
                    # The HEADLINE, not the paragraph under it. A first draft
                    # of this asserted "relative" anywhere in the output and
                    # stayed green when the banner was reworded to "points
                    # somewhere else", because the explanation below it still
                    # used the word. The banner is the line a reader acts on.
                    banner = next(l for l in out.splitlines()
                                  if "refusing to run" in l)
                    self.assertIn(
                        "relative", banner,
                        f"the refusal must say it is the relativity that is "
                        f"the problem — {value!r} inside $ROOT is not a "
                        f"different tree, and the banner it prints is "
                        f"{banner.strip()!r}:\n{out}")


class TestTheBulletUsesTheVocabularyOfTheMechanismSpelledInTestsRun(
        unittest.TestCase):
    """**What this reads is two STRINGS in `tests/run`. It is not a test of
    which mechanism shipped, and its old name said it was.**

    `tests/run` can close the ambient `$PERRY_PROJECT` case in one of two
    ways:

        RE-AIM   `export PERRY_PROJECT="$ROOT"`, so that every un-rooted write
                 lands in the tree the guard watches; or
        REFUSE   print and `exit 2` before step 1.

    Round 2 of the V4 review found `tests/run` REFUSING while `tree_guard.py`'s
    "What it does NOT catch, said plainly" list still described the RE-AIM —
    tried, and rejected for reddening nine tests — as the thing that shipped.
    A reader consulting the one list whose job is to say what is uncovered was
    told a mechanism was in place that was not. That is the rot this catches:
    the source is edited from one mechanism to the other and the bullet is
    left behind. It is cheap and it is worth having.

    **The claim is narrowed to that, because round 3 measured how much less
    than "which mechanism shipped" it can see, and the gap is total.** Three
    mutations of `tests/run` left both tests here GREEN while shipping the
    other mechanism, and two rewrites of the bullet left them green while
    describing the shipped one backwards:

    * `export "PERRY_PROJECT=$ROOT"` and `PERRY_PROJECT=…; export
      PERRY_PROJECT` ahead of the refusal — a live re-aim that made the
      refusal unreachable. `_implemented` now matches both spellings, so
      these two are caught today; they are recorded because the class of
      "a spelling the regex does not know" has no closed form.
    * `unset PERRY_PROJECT` with the whole refusal left in the file under
      `if false` — a dead refusal, still read as shipped, and **still not
      caught**: no substring search can tell a reachable line from an
      unreachable one.
    * the bullet rewritten to assert the exact OPPOSITE behaviour, and the
      bullet cut to the four words `**tests/run refuses.**` — both green,
      because what is required is the substring `refuses` present and the
      substring `export` absent, and nothing else.

    **The behaviour tests are what establish which mechanism ships.**
    `TestTheEnvironmentTheGuardCanSee` runs the real script and asserts on
    `rc`; all three source mutations above are red there. So this class is a
    vocabulary check on one bullet, the behaviour tests are the protection,
    and nothing depends on this one saying more than it does.
    """

    BULLET = "- **A write to a DIFFERENT checkout.**"

    #: Which of the two the source spells, read as text. Both are anchored at
    #: a line that is not a comment: `tests/run` DISCUSSES both mechanisms at
    #: length in comment blocks, and discussing is not shipping. The export
    #: pattern deliberately stops at the variable name rather than requiring
    #: `=`, so that `export "PERRY_PROJECT=$ROOT"` and a bare `export
    #: PERRY_PROJECT` after an assignment are both seen — two spellings a
    #: reviewer used to slip a live re-aim past the earlier pattern.
    RE_AIM = r"""^[^#\n]*\bexport[ \t]+["']?PERRY_PROJECT\b"""
    REFUSE = r"^[^#\n]*refusing to run: PERRY_PROJECT"

    def _implemented(self, run_src):
        found = []
        if re.search(self.RE_AIM, run_src, re.M):
            found.append("re-aim")
        if re.search(self.REFUSE, run_src, re.M):
            found.append("refuse")
        return found

    def setUp(self):
        self.run_src = (PERRY_HOME / "tests" / "run").read_text()
        doc = TG.__doc__ or ""
        self.assertEqual(
            doc.count(self.BULLET), 1,
            f"the bullet this test reads is not uniquely identifiable in "
            f"tree_guard.py's docstring ({doc.count(self.BULLET)} "
            f"occurrence(s) of {self.BULLET!r}) — fix that before trusting "
            f"any verdict here")
        start = doc.index(self.BULLET)
        # The bullet ends at the next top-level bullet OR at the next section
        # heading, whichever comes first — and there may be neither. The
        # first version terminated on `doc.index("\n- **", ...)` alone, so
        # moving this bullet to the end of its list would raise ValueError
        # and ERROR both tests here instead of reporting anything; and
        # running to the end of the docstring instead would swallow the "Why
        # a refusal and not a re-aim" section below, whose prose contains
        # both forbidden words. Bound it to its own bullet, always.
        ends = [i for i in (doc.find("\n- **", start + 1),
                            doc.find("\n## ", start + 1)) if i != -1]
        self.bullet = doc[start:min(ends)] if ends else doc[start:]

    def test_tests_run_spells_exactly_one_of_the_two_mechanisms(self):
        found = self._implemented(self.run_src)
        self.assertEqual(
            len(found), 1,
            f"tests/run spells {found or 'neither'} of the two ways to "
            f"close the ambient PERRY_PROJECT case; the docstring can only "
            f"describe one of them, so this test cannot say which is right "
            f"until the source does")

    def test_the_bullet_uses_the_word_of_the_mechanism_the_source_spells(self):
        found = self._implemented(self.run_src)
        # Not `found[0]`. When the source spells neither, the reader of this
        # test deserves the sentence above and not an IndexError from the
        # subscript — a test whose whole value is what it prints must not
        # crash on the way to printing it.
        self.assertEqual(
            len(found), 1,
            f"tests/run spells {found or 'neither'} of the two mechanisms, "
            f"so there is no single word the bullet could be required to "
            f"use; fix the source, or the sibling test above will tell you "
            f"the same thing")
        shipped = found[0]
        says, must_not = {"refuse": ("refuses", "export"),
                          "re-aim": ("export", "refuses")}[shipped]
        low = self.bullet.lower()
        self.assertIn(
            says, low,
            f"tests/run spells {shipped}, and tree_guard.py's '{self.BULLET}' "
            f"bullet never says so:\n\n{self.bullet}")
        self.assertNotIn(
            must_not, low,
            f"tests/run spells {shipped}, and the bullet still describes the "
            f"other mechanism — the one that was tried and withdrawn — as the "
            f"thing that ships:\n\n{self.bullet}")


class TestThePlantedWrite(unittest.TestCase):
    """The guard fails the suite on a write to the live root — and would not
    fail it if the guard were gone."""

    def test_a_module_that_writes_into_the_root_turns_the_suite_red(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo(Path(tmp) / "repo")
            (root / "tests" / PLANT_MODULE).write_text(PLANT)
            r = run_suite(root, PLANT_MODULE)
            out = r.stdout + r.stderr

            self.assertNotEqual(
                r.returncode, 0,
                "the planted module wrote into the root and the suite came "
                "back green — the guard is not wired into tests/run:\n" + out)
            self.assertIn("THE SUITE WROTE INTO THE TREE IT RAN IN", out)
            self.assertIn("M perry/BOARD.md", out,
                          "the guard failed the suite but did not name the "
                          "file that changed:\n" + out)
            self.assertIn("+ .perry/task-249-planted.txt", out,
                          "the guard failed the suite but did not name the "
                          "file that was created:\n" + out)
            # The module itself passed. If the suite were red because the
            # PLANT failed rather than because the tree moved, this test would
            # be measuring nothing.
            self.assertNotIn("✗ " + PLANT_MODULE, out,
                             "the planted module itself failed:\n" + out)

    def test_the_same_run_is_green_when_the_guard_is_neutered(self):
        """**The mutation.** One line of `tree_guard.py` — the comparison
        itself — is replaced with the empty answer, and the identical planted
        run must come back green. If it stays red, the red in the test above
        is coming from somewhere else and that test is vacuous.
        """
        anchor = "    lines = compare(before, manifest(root))"
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo(Path(tmp) / "repo")
            guard = root / "tests" / "tree_guard.py"
            src = guard.read_text()
            self.assertEqual(
                src.count(anchor), 1,
                f"the mutation anchor is not unique in tree_guard.py: "
                f"{src.count(anchor)} occurrence(s) of {anchor!r} — resolve "
                f"it before trusting this test")
            guard.write_text(src.replace(
                anchor, "    lines = []  # MUTATION by test_tree_guard.py"))

            (root / "tests" / PLANT_MODULE).write_text(PLANT)
            r = run_suite(root, PLANT_MODULE)
            out = r.stdout + r.stderr

            self.assertEqual(
                r.returncode, 0,
                "with the guard neutered the planted run should be green — "
                "if it is red, something OTHER than the guard is failing it "
                "and the test above proves nothing:\n" + out)
            # And the write really did happen, so the green above is the
            # guard's absence and not the plant failing to fire.
            self.assertIn("planted by TASK-249's guard test",
                          (root / "perry" / "BOARD.md").read_text())

    def test_a_module_that_stays_in_a_temp_root_is_green(self):
        """The control. Same runner, same `--only` path, no write to the root
        — so a red here would mean the mechanism, not the plant."""
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo(Path(tmp) / "repo")
            (root / "tests" / CONTROL_MODULE).write_text(CONTROL)
            r = run_suite(root, CONTROL_MODULE)
            out = r.stdout + r.stderr
            self.assertEqual(r.returncode, 0,
                             "a well-behaved module turned the suite red:\n"
                             + out)
            self.assertIn("nothing under", out)


class TestTheManifest(unittest.TestCase):
    """What `manifest` records, and what it deliberately does not."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        (self.root / "a.txt").write_text("one\n")
        (self.root / "sub").mkdir()
        (self.root / "sub" / "b.txt").write_text("two\n")

    def test_a_changed_file_is_M(self):
        before = TG.manifest(self.root)
        (self.root / "a.txt").write_text("ONE\n")
        self.assertEqual(TG.compare(before, TG.manifest(self.root)),
                         ["  M a.txt   (changed)"])

    def test_a_created_file_is_plus_and_a_removed_file_is_minus(self):
        before = TG.manifest(self.root)
        (self.root / "c.txt").write_text("three\n")
        (self.root / "sub" / "b.txt").unlink()
        self.assertEqual(TG.compare(before, TG.manifest(self.root)),
                         ["  + c.txt   (created)",
                          "  - sub/b.txt   (removed)"])

    def test_a_file_rewritten_with_the_same_bytes_is_not_a_change(self):
        """Content, not mtime. A test that reads and rewrites a file
        unchanged has not moved the tree, and reporting it would train
        everyone to ignore this guard."""
        before = TG.manifest(self.root)
        (self.root / "a.txt").write_text("one\n")
        self.assertEqual(TG.compare(before, TG.manifest(self.root)), [])

    def test_an_empty_directory_created_is_a_change(self):
        before = TG.manifest(self.root)
        (self.root / "fresh").mkdir()
        self.assertEqual(TG.compare(before, TG.manifest(self.root)),
                         ["  + fresh   (created)"])

    def test_a_relinked_symlink_is_a_change_without_following_it(self):
        (self.root / "link").symlink_to("a.txt")
        before = TG.manifest(self.root)
        (self.root / "link").unlink()
        (self.root / "link").symlink_to("sub/b.txt")
        self.assertEqual(TG.compare(before, TG.manifest(self.root)),
                         ["  M link   (changed)"])

    def test_bytecode_and_caches_are_not_recorded(self):
        """Running the suite compiles the suite. If `__pycache__` counted, the
        guard would be red on every first run and switched off by the end of
        the week."""
        before = TG.manifest(self.root)
        (self.root / "__pycache__").mkdir()
        (self.root / "__pycache__" / "x.cpython-313.pyc").write_bytes(b"\x00")
        (self.root / "sub" / "d.pyc").write_bytes(b"\x00")
        (self.root / ".git").mkdir()
        (self.root / ".git" / "index").write_bytes(b"\x00")
        self.assertEqual(TG.compare(before, TG.manifest(self.root)), [])

    def test_all_three_ignore_lists_are_the_documented_ones(self):
        """A guard is weakened by growing its ignore list, and that is the
        cheapest way to make a red run green.

        **There are THREE lists and the first version of this test pinned
        two.** A V4 reviewer set `IGNORE_NAMES = {".DS_Store",
        "events.jsonl", "intake.jsonl"}` — blinding the guard to two of the
        four files this whole row is about — and all thirteen tests stayed
        green. Naming two of three is how a pin becomes decoration.

        `.claude` and `.gstack` joined `IGNORE_DIRS` deliberately and this
        assertion is what made that deliberate: both are created by the agent
        harness this project is developed under, from outside the suite and in
        the middle of a run, and neither has a tracked file. The rule they
        satisfy — *this checkout actually produces it, and no test may
        legitimately write it* — is stated once in `tree_guard.py`'s docstring
        and is the same rule that keeps `.pytest_cache` and friends OUT.
        """
        self.assertEqual(set(TG.IGNORE_DIRS),
                         {".git", "__pycache__", ".claude", ".gstack"})
        self.assertEqual(TG.IGNORE_SUFFIXES, (".pyc", ".pyo"))
        self.assertEqual(set(TG.IGNORE_NAMES), {".DS_Store"})

    def test_every_ignored_name_is_a_bullet_in_the_list_of_what_is_missed(self):
        """**Every entry on those three lists is a permanent hole, and the
        list of holes has to contain all of them.**

        This is the round-3 V4 blocker turned into a test rather than a
        promise. `.claude` and `.gstack` were in `IGNORE_DIRS` and absent
        from *"What it does NOT catch, said plainly"* — while `.DS_Store` and
        `__pycache__`, strictly narrower holes, each had a bullet. A list
        whose entire job is to say what is uncovered, that omits the widest
        entry while naming two smaller ones, is worse than no list: it reads
        as complete. The section says so itself — *"They are listed so that
        the next reader inherits the list rather than rediscovering it"*.

        The pin above catches a list that GREW. This catches a list that grew
        **without the reader being told**, which is the same edit one step
        earlier and the one that actually happened.
        """
        doc = TG.__doc__ or ""
        head = "## What it does NOT catch, said plainly"
        self.assertEqual(doc.count(head), 1,
                         "the section this test reads is not uniquely "
                         "identifiable in tree_guard.py's docstring")
        start = doc.index(head)
        end = doc.find("\n## ", start + 1)
        section = doc[start:] if end == -1 else doc[start:end]
        names = sorted(set(TG.IGNORE_DIRS) | set(TG.IGNORE_NAMES)
                       | set(TG.IGNORE_SUFFIXES))
        # Otherwise three emptied lists would satisfy this by iterating over
        # nothing, which is how a derived assertion becomes decoration.
        self.assertTrue(names, "the guard ignores nothing at all — either "
                               "the three lists were emptied or this test is "
                               "reading the wrong module")
        for name in names:
            with self.subTest(ignored=name):
                self.assertIn(
                    name, section,
                    f"{name!r} is ignored by the guard — a permanent hole — "
                    f"and the one list whose job is to tell the next reader "
                    f"what is uncovered does not mention it")

    def test_the_four_files_of_this_row_are_never_invisible(self):
        """The pin above catches a list that GREW, by name. This catches the
        same attack by CONSEQUENCE, and it does not care which of the three
        lists was used — or whether a fourth is invented.

        `perry-task intake-sweep` writes exactly these four. If the manifest
        cannot see a change to one of them, the guard cannot fail on the thing
        it was built to fail on, whatever the mechanism.
        """
        four = ["\u002eperry/events.jsonl", "perry/BOARD.md",
                "perry/intake.jsonl", "perry/journal/2026-08/2026-08-30.md"]
        for rel in four:
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text("before\n")
        before = TG.manifest(self.root)
        for rel in four:
            (self.root / rel).write_text("after\n")
        moved = {l.split()[1] for l in TG.compare(before, TG.manifest(self.root))}
        self.assertEqual(moved, set(four),
                         "the manifest is blind to one of the four files "
                         "TASK-249's sweep writes")

    def test_a_permission_change_is_a_change(self):
        """`chmod +x` on a shipped script changes what the tree is without
        changing a byte of it, and what this repository ships is executable.
        How many is not stated here — see the test below."""
        import os as _os
        before = TG.manifest(self.root)
        _os.chmod(self.root / "a.txt", 0o755)
        self.assertEqual(TG.compare(before, TG.manifest(self.root)),
                         ["  M a.txt   (changed)"])

    def test_the_executables_this_repository_ships_carry_their_mode(self):
        """The set is DERIVED from the tree, and no count is written down.

        This docstring and `tree_guard.manifest`'s both said the repository
        ships **eleven** executables, and the tree held rather more. A number
        in a comment is a claim nothing checks, and writing today's count here
        instead would be the same defect one value later — so no count is
        written here either, in prose or in an assertion. This asserts the
        SHAPE of the set and lets the size be whatever it is on the day; if
        you want the number, `git ls-tree -r HEAD | awk '$1=="100755"' | wc -l`
        and `find . -type f -perm -u+x -not -path './.git/*' | wc -l` are the
        two instruments, and they agree.
        """
        m = TG.manifest(PERRY_HOME)
        execs = {rel for rel, tok in m.items()
                 if tok.startswith("f:") and int(tok.split(":")[1], 8) & 0o111}
        self.assertTrue(execs, "the manifest recorded no executable at all")
        # The bit the manifest reports is the bit on disk — otherwise this
        # test would be reading its own answer back.
        for rel in sorted(execs):
            self.assertTrue(os.access(PERRY_HOME / rel, os.X_OK),
                            f"manifest says {rel} is executable; the "
                            f"filesystem disagrees")
        # Every shipped `bin/perry-*` is one. A stripped bit there is a
        # broken install, which is exactly why the mode is in the token.
        shipped = {rel for rel, tok in m.items()
                   if rel.startswith("bin/perry-") and tok.startswith("f:")}
        self.assertTrue(shipped, "no bin/perry-* files found at all")
        self.assertEqual(
            shipped - execs, set(),
            "shipped bin/ scripts carrying no executable bit")
        # And the ones outside `bin/` that the manifest docstring describes.
        for rel in ("setup", "tests/run", "tests/parallel",
                    "tests/merge-check",
                    "templates/knowledge-base/bin/kb-lint",
                    "templates/ops/bin/deliverable-lint"):
            self.assertIn(rel, execs,
                          f"{rel} is described as a shipped executable and "
                          f"the manifest does not see its bit")


class TestTheCLI(unittest.TestCase):
    """`snapshot` / `verify`, the two verbs `tests/run` actually calls."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "tree"
        self.root.mkdir()
        (self.root / "a.txt").write_text("one\n")
        self.store = Path(self.tmp.name) / "manifest.json"

    def cli(self, *argv) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(PERRY_HOME / "tests" / "tree_guard.py"),
             *argv], capture_output=True, text=True)

    def test_verify_is_zero_on_an_unchanged_tree(self):
        self.assertEqual(
            self.cli("snapshot", str(self.root), str(self.store)).returncode, 0)
        r = self.cli("verify", str(self.root), str(self.store))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, "")

    def test_verify_is_one_and_names_the_path(self):
        self.cli("snapshot", str(self.root), str(self.store))
        (self.root / "a.txt").write_text("two\n")
        r = self.cli("verify", str(self.root), str(self.store))
        self.assertEqual(r.returncode, 1)
        self.assertIn("M a.txt", r.stderr)
        self.assertIn("perry-task", r.stderr,
                      "the failure should say where writes like this come "
                      "from, not just that one happened")

    def test_a_bad_invocation_is_two_not_a_traceback(self):
        r = self.cli("verify", str(self.root))
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
