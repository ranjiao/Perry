"""TASK-065's standing guard: one implementation of a `bin/` primitive.

**Written as the category, not as the instances.** That is the whole lesson of
the row this module lands with. Six primitives had fourteen-plus
implementations; the ones that got extracted stopped multiplying and the ones
that did not gained three more inside a single commit, because a second
implementation is the path of least resistance whenever the first is not
importable. TASK-067 then routed every reader through the one `split_row` and
found two offenders (`perry-state`, `perry-diagnose`) that no report had named
— because its test asked "does this file split a row at all", rather than
listing the files that had already been caught doing it.

So this asks what a file *does*, never what it is called:

- the wrapper functions are fine and expected. `perry-goals.write_atomic`
  takes an extra argument and refuses another lane's file first;
  `perry-conform.load_schema` arms the linter's glossary after; every
  `project_lock` passes its own `Refused`. Each one is three lines over
  `bin/lib`, and a name-based guard would flag all of them while missing a
  re-implementation called `_atomic_write`.
- what is NOT fine is a second **body**. `mkstemp` and a `.tmp` suffix are how
  you stage bytes; `flock` is how you take the lock; `raise …("schema not
  found at …")` is the refusing schema loader. A file in `bin/` that contains
  one of those has rebuilt a primitive, whatever it named the function.

`bin/lib/` is the only exemption, and it is exempt because it is the
implementation. The list is one entry long on purpose — a guard people can add
themselves to is a guard that stops meaning anything.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent

#: The implementation. Everything else in `bin/` imports from it.
LIB = PERRY_HOME / "bin" / "lib"


def _is_python(p: Path) -> bool:
    """A Python source file, by suffix or shebang — not by extension list.

    `bin/` holds bash scripts (`perry-detect-host`, `perry-dispatch-limit`) and
    Python scripts with no suffix at all (`perry-task`). Asking what the file
    is beats a suffix blacklist that the next asset type would extend — the
    same judgement `tests/test_one_header_rule.py` had to reach.
    """
    if p.suffix == ".py":
        return True
    if p.suffix:
        return False
    try:
        return "python" in p.read_text(errors="replace").split("\n", 1)[0]
    except OSError:
        return False


def _tools() -> list[Path]:
    """Every Python file under `bin/`, walked — not `iterdir`, not `glob`.

    `rglob`, because `bin/lib/` is itself a subdirectory and the two sibling
    guards in this suite were both measured blind to exactly that: a reviewer
    planted the byte-identical defect at `bin/lib/rows.py` and both stayed
    green. A guard for this row that could not see one directory down would be
    blind to the directory this row created.
    """
    return sorted(p for p in (PERRY_HOME / "bin").rglob("*")
                  if p.is_file()
                  and "__pycache__" not in p.parts
                  and _is_python(p))


#: Each primitive by the shape of its body. The value is what the offender has
#: rebuilt, phrased so the failure message says what to import instead.
KERNELS = {
    "staging bytes into a temp file (use `lib.write_atomic` / `lib.stage`)":
        re.compile(r"mkstemp\(|['\"]\.tmp['\"]"),
    "taking the project lock (use `lib.project_lock`)":
        re.compile(r"\bflock\("),
    "the refusing schema loader (use `lib.load_schema`)":
        re.compile(r"raise\s+\w+\(\s*f?['\"]schema not found at"),
}


def _code_lines(path: Path):
    """Non-comment lines. A comment naming the defect is not the defect — this
    module and `bin/lib` both quote every one of these spellings in prose."""
    for n, line in enumerate(path.read_text(errors="replace").split("\n"), 1):
        if not line.lstrip().startswith("#"):
            yield n, line


class TestOneImplementationPerPrimitive(unittest.TestCase):

    def test_no_tool_rebuilds_a_primitive_bin_lib_already_has(self):
        offenders = {}
        for p in _tools():
            if LIB in p.parents or p == LIB:
                continue
            for what, pat in KERNELS.items():
                hits = [f"{p.relative_to(PERRY_HOME).as_posix()}:{n}"
                        for n, line in _code_lines(p) if pat.search(line)]
                if hits:
                    offenders.setdefault(what, []).extend(hits)
        self.assertEqual(
            offenders, {},
            "these carry a second body for a primitive `bin/lib` already "
            "implements; import it instead of rebuilding it:\n  "
            + "\n  ".join(f"{w}\n    " + "\n    ".join(v)
                          for w, v in offenders.items()))

    def test_the_scan_actually_finds_each_kernel_in_bin_lib(self):
        """Anti-vacuity, half one. If a pattern matched nothing anywhere, the
        test above would pass by scanning for a spelling that no longer exists
        — which is how a guard quietly becomes ceremony."""
        src = "\n".join(line for _, line in _code_lines(LIB / "__init__.py"))
        for what, pat in KERNELS.items():
            with self.subTest(primitive=what):
                self.assertTrue(pat.search(src),
                                f"bin/lib no longer contains {what} — either "
                                f"it moved, or this pattern is now dead")

    def test_the_patterns_fire_on_a_rebuild_that_renames_the_function(self):
        """Anti-vacuity, half two: the guard must catch a body under a name it
        has never heard of. This is the planted file, held as a string rather
        than written into `bin/` — a reviewer who plants into the live tree
        makes a correct guard report a defect that does not exist."""
        planted = [
            'def _save(path, text):\n'
            '    fd, t = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")\n',
            'def _guard(root):\n'
            '    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)\n',
            'def _shape():\n'
            '    raise Nope(f"schema not found at {P}")\n',
        ]
        for src, (what, pat) in zip(planted, KERNELS.items()):
            with self.subTest(primitive=what):
                self.assertTrue(pat.search(src),
                                f"a renamed rebuild of {what} walks past this "
                                f"guard")

    def test_bin_lib_is_the_only_exemption(self):
        """The exemption list is one entry long, and it is the implementation.
        A second entry is how this guard would stop meaning anything, so the
        count is asserted rather than left to review."""
        exempt = [p for p in _tools() if LIB in p.parents or p == LIB]
        self.assertEqual(
            [p.relative_to(PERRY_HOME).as_posix() for p in exempt],
            ["bin/lib/__init__.py"],
            "bin/lib gained or lost a file — that is fine, but it is the only "
            "place exempt from the rule above, so it is worth noticing")


class TestEveryWriterReachesTheSharedLock(unittest.TestCase):
    """The complement. The guard above proves nobody rebuilt a primitive; it
    would also pass on a tool that took no lock at all, which is the failure it
    is supposed to make impossible."""

    #: Tools that write a project's state files and so must serialize.
    WRITERS = ("perry-task", "perry-tasks", "perry-migrate", "perry-goals",
               "perry-decide", "perry-knowledge")

    def test_every_writer_takes_the_project_lock(self):
        for name in self.WRITERS:
            with self.subTest(tool=name):
                src = (PERRY_HOME / "bin" / name).read_text()
                self.assertIn("lib.project_lock", src,
                              f"bin/{name} writes state and never reaches "
                              f"`lib.project_lock`")

    def test_every_writer_reaches_the_shared_atomic_write(self):
        for name in self.WRITERS:
            with self.subTest(tool=name):
                src = (PERRY_HOME / "bin" / name).read_text()
                self.assertTrue(
                    "lib.write_atomic" in src or "lib.stage" in src,
                    f"bin/{name} writes state and never reaches "
                    f"`lib.write_atomic`")


if __name__ == "__main__":
    unittest.main()
