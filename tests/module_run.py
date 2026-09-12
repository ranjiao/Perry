"""One question, asked in one place: **did this module actually run its tests?**

TASK-430. `python3 -m unittest tests.<name>` does NOT put `tests/` on
`sys.path`. A module that imports a sibling helper by bare name — 58 of the
148 files in this directory do, measured 2026-09-12 — therefore fails to
import, and `unittest` reports:

    ERROR: test_risks (unittest.loader._FailedTest.test_risks)
    ImportError: Failed to import test module: test_risks
    ...
    Ran 1 test in 0.000s
    FAILED (errors=1)

**`Ran 1 test` is the whole problem.** The module has 83 tests. Nothing ran,
and the run still produced a plausible-looking number.

**The dangerous case is not the error, it is the zero.** Read by a human the
block above is loud — it says FAILED. Read by a *script* that captures the
output and reduces it to one number, it is silent, and this repository has
been bitten twice:

  * `tests/parallel`'s own first version shelled out this way, reported 1,207
    tests against the serial suite's 1,287, and was nearly filed as a speedup.
    Eighty tests had stopped running and the number was still large enough to
    look right. See that file's line 13.
  * TASK-341's reviewer built a poller to measure how long a probe file existed
    in the live tree and got **0 foreign files out of 1,861 runs**. The module
    never imported; the loop spun at 30ms doing nothing. Its own conclusion:
    *a 0 from a poller is only worth the run count beside it.*

So this module exists to make that shape impossible to obtain by accident.
Two things live here and they are deliberately separable:

  * `load_failures(stderr)` — a pure classifier over captured output. Anything
    that already HAS a module's output can ask it the question, including
    `tests/parallel`, which calls it from `failure_block`.
  * `run_module(name)` — the only invocation in this repository that a probe,
    poller or measurement script should use. It runs the module the way the
    suite runs it (`discover`, which sets the path correctly) and **raises**
    rather than return a result carrying the placeholder shape.

**What this does NOT cover, stated plainly rather than implied away:** a human
who types `python3 -m unittest tests.<name>` at a shell executes nothing from
this file, and no guard placed in the repository can intercept that command.
That path is covered by a different mechanism — `tests/__init__.py`, which
Python itself imports when resolving `tests.<name>`, and which puts this
directory on `sys.path` so the bare-name sibling import resolves and the
command simply works. The two are complements, not alternatives: the
`__init__.py` removes the *sibling-import* cause on the one path a guard
cannot reach, and this file catches the *whole class* of load failure — a
typo'd import, a deleted helper, a circular import, a syntax error — on every
path that runs a module programmatically.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: The loader's own placeholder class. When a test module fails to import,
#: `unittest` cannot report the module's tests — it does not know what they
#: are — so it synthesises ONE test bearing this name whose only act is to
#: re-raise the import error. Every `Ran 1 test` discussed above is this.
PLACEHOLDER = "unittest.loader._FailedTest"

#: Two independent signals for the same event, on the principle `unaccounted()`
#: and `unittest_bad_count()` in `tests/parallel` already run on: one number is
#: a claim, two agreeing numbers are a measurement. The first matches the
#: loader's synthesised test id (both the 3.11+ `_FailedTest.<name>` spelling
#: and the older bare `_FailedTest` one); the second matches the sentence the
#: placeholder raises. A stream showing either is a module that did not load.
_PLACEHOLDER_ID = re.compile(
    r"^(?:ERROR|FAIL):\s+(?P<mod>\S+)\s+\("
    + re.escape(PLACEHOLDER) + r"(?:\.(?P=mod))?\)\s*$", re.MULTILINE)
_FAILED_IMPORT = re.compile(
    r"^ImportError: Failed to import test module: (?P<mod>\S+)\s*$",
    re.MULTILINE)

#: unittest's own `Ran N test(s)` line.
_RAN = re.compile(r"^Ran (?P<n>\d+) tests? in ", re.MULTILINE)


class ModuleDidNotRun(RuntimeError):
    """A module was asked for its tests and returned the loader's placeholder.

    Raised, not returned. A caller that wanted a number gets an exception
    instead of a number, which is the entire point: the failure mode this
    class exists for is a wrong number that looked right, and an exception is
    the one return value that cannot be quietly averaged into a result.
    """


def load_failures(stderr: str) -> list[str]:
    """Module names `unittest` reported as import failures, sorted, deduped.

    Empty list means the stream shows no load failure. The two regexes are
    OR-ed rather than AND-ed: either spelling on its own is sufficient
    evidence, because the failure being guarded against is one that HIDES, and
    requiring both signals would let a future unittest release that drops one
    of them turn the guard silently vacuous — green because it stopped
    looking, which is the defect wearing the guard's own clothes.
    """
    names = {m.group("mod") for m in _PLACEHOLDER_ID.finditer(stderr)}
    names |= {m.group("mod") for m in _FAILED_IMPORT.finditer(stderr)}
    return sorted(names)


def ran_count(stderr: str) -> int | None:
    """`Ran N` summed over the stream, or None if unittest never said.

    None is not zero — the same distinction `unittest_bad_count()` makes in
    `tests/parallel`. A module killed before it wrote a verdict line has an
    unknown count, and reporting unknown as 0 is how a silent failure is
    manufactured.
    """
    hits = _RAN.findall(stderr)
    return sum(int(n) for n in hits) if hits else None


def load_failure_verdict(mod: str, stderr: str) -> str | None:
    """The sentence to print about `mod`, or None if it loaded fine.

    Phrased around what the reader is about to get wrong — the count — rather
    than around the traceback, which is already in the output and is not the
    part that misleads.
    """
    failed = load_failures(stderr)
    if not failed:
        return None
    ran = ran_count(stderr)
    ran_txt = "no verdict line" if ran is None else f"`Ran {ran}`"
    return (f"{mod} did not load: {', '.join(failed)} raised at import, so "
            f"unittest ran {PLACEHOLDER} instead of this module's tests and "
            f"reported {ran_txt}. That count is not a result. The usual cause "
            f"is invoking `python3 -m unittest tests.{mod}`, which does not "
            f"put tests/ on sys.path; run `python3 -m unittest discover -s "
            f"tests -p {mod}.py`, or `python3 tests/parallel {mod}`.")


def run_module(name: str, root: pathlib.Path | None = None,
               timeout: float | None = None) -> dict:
    """Run one test module correctly, and refuse a result that did not run.

    **Use this from any probe, poller or measurement that needs a module's
    test count.** It invokes `discover`, which sets `sys.path` the way the
    serial suite does, so the sibling-import cause cannot arise here at all;
    and it then checks for the placeholder shape anyway, because `discover`
    closes one cause of a load failure and not the class.

    `name` is the module's bare stem, e.g. `test_risks`. `root` is the tree
    holding `tests/`, defaulting to this repository — it is a parameter so
    that `tests/test_module_run_guard.py` can drive this function against a
    scratch tree containing a deliberately broken module, rather than assert
    against a hand-written copy of what it would have said.

    **Do not call this with the name of the module you are calling it from.**
    It spawns a subprocess that runs that module, which calls this function,
    which spawns a subprocess … The recursion is unbounded and was hit while
    writing this file's own tests; it is cheap to avoid and expensive to
    notice, since the symptom is a hang rather than an error.

    Raises `ModuleDidNotRun` if the module failed to load. Returns a dict with
    `ran`, `rc`, `out` and `err` otherwise — and a zero in `ran` from this
    function is a real zero, which is the only kind worth reporting.
    """
    stem = name[:-3] if name.endswith(".py") else name
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests",
         "-p", f"{stem}.py", "-v"],
        capture_output=True, text=True, cwd=str(root or ROOT), timeout=timeout)
    verdict = load_failure_verdict(stem, proc.stderr)
    if verdict is not None:
        raise ModuleDidNotRun(verdict)
    return {"mod": stem, "rc": proc.returncode,
            "ran": ran_count(proc.stderr) or 0,
            "out": proc.stdout, "err": proc.stderr}
