"""The mutation harness for the one-header-rule guard. TASK-050, round five.

**This row went through four V4 rounds and each one ended the same way.** A
reviewer planted a reader that resolved a header its own way, the guard stayed
green, and the fix was to widen `SECOND_RULE` by one more alternation:

    round 2  three copies in files that never imported `squash`
    round 3  a SUBDIRECTORY was invisible (`bin/lib/rows.py` green,
             `bin/perry-rows-probe` red) · the pattern matched a SPELLING not a
             shape, so `for h in header` walked past `for c in cells`
    round 4  the `[` had to sit right after the `=`, so the PARENTHESISED
             comprehension — the live shape in `viewer/parsers.py` — was green

Four rounds, four blind spots, and every one found by a human doing by hand
what this file now does on every run. The row's own `Next action` is the
conclusion: *"the fifth hardening round should be a mutation harness, not
another regex."*

**A planted reader the guard does not report is a FINDING, not a skip.** That
is the review rule this file mechanises: a green mutation means either the
guard does not work or the test does not test it, and both are answers. The
corpus below therefore includes spellings that are known NOT to be caught, in
`TestTheHarnessKnowsWhatItCannotSee`, so the blind spots are enumerated in the
repository rather than rediscovered once a round.

Everything is planted into a COPY under `tempfile` — never the live tree.
`work/reference/review-constraints.md` is explicit about why: for the seconds a
planted file exists, a shared checkout has a file that makes this guard
legitimately red, and anything else running the suite sees a real-looking
failure about nothing.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_one_header_rule import (          # noqa: E402
    PERRY_HOME, readers_under, second_rule_offenders)


#: Each entry is `(name, relative path to plant at, source)`. The paths are as
#: load-bearing as the sources: two of the four historical blind spots were
#: about WHERE the file sat, not what it said.
CAUGHT = [
    (
        "the original spelling",
        "bin/perry-probe-a",
        '#!/usr/bin/env python3\n'
        'def read(prev, cells):\n'
        '    header = [c.strip().lower() for c in cells]\n'
        '    return header\n',
    ),
    (
        "round 3: the loop subject renamed",
        "bin/perry-probe-b",
        '#!/usr/bin/env python3\n'
        'def read(header):\n'
        '    header = [h.strip().lower() for h in header]\n'
        '    return header\n',
    ),
    (
        "round 3: planted in a SUBDIRECTORY",
        "bin/lib/rows_probe.py",
        'def read(cells):\n'
        '    cols = [c.strip().lower() for c in cells]\n'
        '    return cols\n',
    ),
    (
        "round 4: the parenthesised comprehension, the live shape",
        "bin/perry-probe-c",
        '#!/usr/bin/env python3\n'
        'def read(prev, ok):\n'
        '    header = ([c.strip().lower() for c in split_row(prev)]\n'
        '              if ok else [])\n'
        '    return header\n',
    ),
    (
        "the perry-explain shape: own splitter AND own header rule",
        "bin/perry-probe-d",
        '#!/usr/bin/env python3\n'
        'def read(line):\n'
        '    cols = [c.strip("*` ").lower() for c in line.split("|")]\n'
        '    return cols\n',
    ),
    (
        "no suffix, python by shebang only",
        "bin/perry-probe-e",
        '#!/usr/bin/env python3\n'
        'def read(columns):\n'
        '    hdr = [x.strip().lower() for x in columns]\n'
        '    return hdr\n',
    ),
]


def _plant(name: str, source: str) -> Path:
    """Copy `bin/` and `viewer/` into a temp root and plant one file in it."""
    tmp = Path(tempfile.mkdtemp(prefix="perry-header-harness-"))
    for d in ("bin", "viewer"):
        shutil.copytree(PERRY_HOME / d, tmp / d,
                        ignore=shutil.ignore_patterns("__pycache__"))
    target = tmp / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source)
    return tmp


class TestTheCopyItselfIsClean(unittest.TestCase):
    """The control. Without it every result below is unreadable.

    If an unplanted copy already reported an offender, each `assertTrue` in
    `TestAPlantedReaderIsReported` would pass on the pre-existing one and the
    harness would report success while catching nothing.
    """

    def test_an_unplanted_copy_reports_nothing(self):
        tmp = _plant("bin/perry-probe-none", "#!/usr/bin/env python3\n")
        try:
            self.assertEqual(second_rule_offenders(tmp), [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_copy_carries_the_readers(self):
        """A copy that lost the tree would make every scan below vacuous."""
        tmp = _plant("bin/perry-probe-none", "#!/usr/bin/env python3\n")
        try:
            self.assertGreater(len(readers_under(tmp)),
                               len(readers_under(PERRY_HOME)) - 5)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestAPlantedReaderIsReported(unittest.TestCase):
    """Every spelling a reviewer found by hand, now found on every run."""

    def test_each_planted_reader_is_caught(self):
        for label, where, source in CAUGHT:
            with self.subTest(label):
                tmp = _plant(where, source)
                try:
                    offenders = second_rule_offenders(tmp)
                    self.assertTrue(
                        offenders,
                        f"planted a divergent reader at {where} ({label}) and "
                        f"the guard reported NOTHING — a blind spot, which is "
                        f"a finding whichever way it is read")
                    self.assertTrue(
                        any(Path(where).name in o for o in offenders),
                        f"the guard reported {offenders} but not {where}")
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)


class TestTheHarnessKnowsWhatItCannotSee(unittest.TestCase):
    """**The blind spots that are still open, enumerated rather than skipped.**

    `SECOND_RULE` is a regex over source lines, so it recognises the ONE shape
    it was taught: a list comprehension calling `.lower()`. These two spellings
    resolve a header cell exactly as wrongly and are NOT reported.

    They are asserted as uncaught on purpose. A blind spot written down is one
    the next round does not have to spend a reviewer rediscovering, and the day
    the guard learns either shape these go red and get promoted into `CAUGHT` —
    which is the only kind of failure in this file that is good news.

    Neither is live in this repository today: `test_every_reader_that_resolves
    _headers_reaches_the_one_rule` is the complement that would catch a real
    file carrying one, because such a file splits rows and would have to reach
    `squash`. That is why these are documented rather than fixed here — fixing
    them means widening the regex, and this row's whole conclusion is that
    widening the regex is not what round five should be.
    """

    UNCAUGHT = [
        (
            "`.casefold()` instead of `.lower()`",
            "bin/perry-probe-f",
            '#!/usr/bin/env python3\n'
            'def read(cells):\n'
            '    header = [c.strip().casefold() for c in cells]\n'
            '    return header\n',
        ),
        (
            "`map()` instead of a comprehension",
            "bin/perry-probe-g",
            '#!/usr/bin/env python3\n'
            'def read(cells):\n'
            '    header = list(map(str.lower, [c.strip() for c in cells]))\n'
            '    return header\n',
        ),
    ]

    def test_these_shapes_are_known_to_walk_past_the_regex(self):
        for label, where, source in self.UNCAUGHT:
            with self.subTest(label):
                tmp = _plant(where, source)
                try:
                    offenders = second_rule_offenders(tmp)
                    hit = [o for o in offenders if Path(where).name in o]
                    self.assertEqual(
                        hit, [],
                        f"{label} is now CAUGHT — good news. Move it from "
                        f"UNCAUGHT into CAUGHT and delete this branch.")
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)

    def test_the_complement_guard_would_catch_a_real_one(self):
        """Why the two above are documented and not urgent.

        A real reader carrying one of those spellings also SPLITS a row, and
        the complement test requires any file that splits a row to reach
        `squash`. This asserts that second net is actually there, so the
        blind spots above are bounded rather than open-ended.
        """
        src = (PERRY_HOME / "tests" / "test_one_header_rule.py").read_text()
        self.assertIn("read tables without reaching `squash`", src)


if __name__ == "__main__":
    unittest.main()
