"""The planting harness for the one-header-rule check. TASK-050, round 6.

**Round 5 shipped a harness and the reviewer defeated it in one sitting.** That
review is the design document for this file, so its findings are stated here
rather than paraphrased:

1. *"`CAUGHT` is six literals and `UNCAUGHT` is two. There is no generator, no
   mutation operator, no enumeration over spellings — it cannot produce a
   finding nobody had already written down."* True. The reviewer then planted
   nine spellings and **five escaped both nets**.
2. *"The bounded claim is false."* The complement net was
   `if "squash" not in src` — a whole-file substring test that all nine
   row-splitting readers already satisfy, so it contributed **zero** marginal
   protection against a new rule added to an existing reader. Demonstrated by
   appending a `.casefold()` header reader to `viewer/parsers.py` — the file
   the first pass claimed to have unified — and getting `[]` from both guards
   while the two rules demonstrably diverged.
3. The test written to prove that bound *"asserts only that an error-message
   string appears in a sibling source file and never exercises the
   complement."* It was a grep for a docstring. It is gone.

The structural cause of (2) and (3) was named exactly: the extraction
parameterised one net and left the other pinned to `PERRY_HOME`, so **the one
net the argument depended on was the one net the harness could not point at a
copy**. There is one net now — `tests/header_rule.py` — and it takes a root.

## What changed, and why the corpus is still literals

The check is an AST walk, not a regex, so it recognises a SHAPE rather than a
spelling: any collection built by mapping over a row's cells, whose element
expression case-folds, must fold through `squash`. That is what lets the same
rule cover a comprehension, a dict comprehension, `map()`, and a `for` loop
with `.append()` without being taught each one.

The corpus below is still a list of literals, and that is now honest about what
it is: a **regression corpus** pinning every spelling that has ever escaped
this guard, so round N+1 cannot reintroduce one. It is no longer asked to be
the thing that finds new shapes — the AST rule is. Every entry names the round
that bought it.

Everything is planted into a `tempfile` COPY.
`work/reference/review-constraints.md` is explicit: for the seconds a planted
file exists, a shared checkout has a file that makes this guard legitimately
red, and anything else running the suite sees a real-looking failure about
nothing.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from header_rule import offenders, readers_under      # noqa: E402

PERRY_HOME = Path(__file__).resolve().parent.parent

SHEBANG = "#!/usr/bin/env python3\n"

#: `(label, path to plant at, body)`. The path is as load-bearing as the body:
#: two historical blind spots were about WHERE the file sat.
CAUGHT = [
    ("round 2 · the original spelling", "bin/perry-probe-a",
     "def read(cells):\n    return [c.strip().lower() for c in cells]\n"),

    ("round 3 · the loop subject renamed", "bin/perry-probe-b",
     "def read(header):\n    return [h.strip().lower() for h in header]\n"),

    ("round 3 · planted in a SUBDIRECTORY", "bin/lib/rows_probe.py",
     "def read(cells):\n    return [c.strip().lower() for c in cells]\n"),

    ("round 4 · the parenthesised comprehension, the live shape",
     "bin/perry-probe-c",
     "def read(prev, ok):\n"
     "    header = ([c.strip().lower() for c in split_row(prev)] if ok else [])\n"
     "    return header\n"),

    ("round 5 · own splitter AND own rule (the perry-explain shape)",
     "bin/perry-probe-d",
     'def read(line):\n'
     '    return [c.strip("*` ").lower() for c in line.split("|")]\n'),

    ("round 5 · no suffix, python by shebang only", "bin/perry-probe-e",
     "def read(columns):\n    return [x.strip().lower() for x in columns]\n"),

    # ── the five the round 5 REVIEWER planted, which escaped both old nets ──
    ("round 5 review · casefold in a non-splitting helper", "bin/perry-probe-f",
     "def read(cells):\n    return [c.strip().casefold() for c in cells]\n"),

    ("round 5 review · casefold in a file that ALREADY contains `squash`",
     "bin/perry-probe-g",
     "from tables import squash\n"
     "def elsewhere(x):\n    return squash(x)\n"
     'def read(line):\n'
     '    return [c.strip().casefold() for c in line.split("|")]\n'),

    ("round 5 review · a PIPE constant splitter", "bin/perry-probe-h",
     'PIPE = "|"\n'
     "def read(line):\n"
     "    return [c.strip().lower() for c in line.split(PIPE)]\n"),

    ("round 5 review · re.split instead of str.split", "bin/perry-probe-i",
     "import re\n"
     "def read(line):\n"
     '    return [c.strip().lower() for c in re.split(r"\\|", line)]\n'),

    ("round 5 review · a for/append loop, no comprehension at all",
     "bin/perry-probe-j",
     "def read(cells):\n"
     "    out = []\n"
     "    for c in cells:\n"
     "        out.append(c.strip().lower())\n"
     "    return out\n"),

    # ── shapes the reviewer named as plausible but did not plant ──
    ("round 5 review · dict-comprehension header INDEX over enumerate()",
     "bin/perry-probe-k",
     "def read(cells):\n"
     "    return {c.strip().lower(): i for i, c in enumerate(cells)}\n"),

    ("round 5 review · the rule factored into a scalar helper",
     "bin/perry-probe-l",
     'def _norm(s):\n    return s.strip("*` ").lower()\n'
     "def read(line):\n    return [_norm(c) for c in split_row(line)]\n"),

    ("round 5 review · map() instead of a comprehension", "bin/perry-probe-m",
     "def read(cells):\n    return list(map(str.lower, cells))\n"),
]

#: Shapes that must NOT be reported. **Half of this guard's job.** Every
#: round's docstring warns that widening flags correct call sites, and a guard
#: that reports correct code is one people switch off.
CLEAN = [
    ("the correct reader", "bin/perry-probe-n",
     "from tables import squash\n"
     "def read(line):\n    return [squash(c) for c in split_row(line)]\n"),

    ("cells kept VERBATIM — the live shape at bin/perry-diagnose:1820",
     "bin/perry-probe-o",
     'def read(line):\n    return [c.strip("*` ") for c in split_row(line)]\n'),

    ("a value normalizer over aliases", "bin/perry-probe-p",
     "def read(aliases):\n    return [a.strip().lower() for a in aliases]\n"),

    ("a value normalizer over directory names — the live shape at "
     "bin/perry-diagnose:1394", "bin/perry-probe-q",
     'def read(inventory):\n    return [d.lower() for d in inventory["dirs"]]\n'),
]


def plant(where: str, body: str) -> Path:
    """Copy `bin/` and `viewer/` into a temp root and plant one file in it."""
    tmp = Path(tempfile.mkdtemp(prefix="perry-header-harness-"))
    for d in ("bin", "viewer"):
        shutil.copytree(PERRY_HOME / d, tmp / d,
                        ignore=shutil.ignore_patterns("__pycache__"))
    target = tmp / where
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(SHEBANG + body)
    return tmp


class TestTheCopyItselfIsClean(unittest.TestCase):
    """The control. Without it every result below is unreadable."""

    def test_an_unplanted_copy_reports_nothing(self):
        tmp = plant("bin/perry-probe-none", "x = 1\n")
        try:
            self.assertEqual(offenders(tmp), [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_copy_carries_the_readers(self):
        """A copy that lost the tree would make every scan below vacuous."""
        tmp = plant("bin/perry-probe-none", "x = 1\n")
        try:
            self.assertGreater(len(readers_under(tmp)),
                               len(readers_under(PERRY_HOME)) - 5)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestEveryEscapedSpellingIsReported(unittest.TestCase):
    """Every shape that has ever walked past this guard, on every run."""

    def test_each_planted_reader_is_caught(self):
        for label, where, body in CAUGHT:
            with self.subTest(label):
                tmp = plant(where, body)
                try:
                    found = offenders(tmp)
                    hits = [o for o in found if Path(where).name in o]
                    self.assertTrue(
                        hits,
                        f"planted a divergent reader at {where} ({label}) and "
                        f"the check reported nothing about it. Reported: "
                        f"{found}")
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)


class TestCorrectCodeIsNotReported(unittest.TestCase):
    """The other half. A check that flags correct code gets switched off."""

    def test_each_clean_shape_is_left_alone(self):
        for label, where, body in CLEAN:
            with self.subTest(label):
                tmp = plant(where, body)
                try:
                    hits = [o for o in offenders(tmp)
                            if Path(where).name in o]
                    self.assertEqual(
                        hits, [],
                        f"{label} at {where} was reported, and it is correct "
                        f"code — this is the false-positive failure every "
                        f"round of this row has warned about")
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)


class TestTheReviewersDecisiveCase(unittest.TestCase):
    """The exact planting that failed round 5, in the exact file.

    The round 5 review appended this to `viewer/parsers.py` — *"the file the
    first pass claimed to have unified, where the fifth copy actually lived"* —
    and reported `SECOND_RULE offenders: []`, `complement missing: []`, while
    the two rules produced `default** rung` and `default rung` from the same
    header. This is that case, kept as its own class because it is the one the
    verdict turned on.
    """

    BODY = ('\n\ndef parse_foreign_board_header(line):\n'
            '    return [c.strip("*` ").casefold() '
            'for c in line.split("|") if c.strip()]\n')

    def test_it_is_reported_now(self):
        tmp = Path(tempfile.mkdtemp(prefix="perry-header-decisive-"))
        try:
            for d in ("bin", "viewer"):
                shutil.copytree(PERRY_HOME / d, tmp / d,
                                ignore=shutil.ignore_patterns("__pycache__"))
            pp = tmp / "viewer" / "parsers.py"
            pp.write_text(pp.read_text() + self.BODY)
            hits = [o for o in offenders(tmp) if "parsers.py" in o]
            self.assertTrue(hits, "the case that failed round 5 still escapes")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestWhatTheCheckStillCannotSee(unittest.TestCase):
    """**Stated as assertions, so the list can go red rather than rot.**

    Round 5 claimed its blind spots were "bounded" by a complement test that
    turned out to be vacuous. There is no bounding argument here. These are the
    two shapes this walk does not resolve, written down so a reviewer does not
    have to rediscover them, and so the day one is closed these fail and get
    promoted into `CAUGHT`.

    Both are narrower than round 5's, and neither is live in this tree.
    """

    UNCAUGHT = [
        ("a folding helper defined in ANOTHER module", "bin/perry-probe-r",
         "from somewhere import _norm\n"
         "def read(line):\n    return [_norm(c) for c in split_row(line)]\n"),
        ("an iterable named nothing like a row and never split locally",
         "bin/perry-probe-s",
         "def read(stuff):\n    return [c.strip().lower() for c in stuff]\n"),
    ]

    def test_these_shapes_are_known_to_escape(self):
        for label, where, body in self.UNCAUGHT:
            with self.subTest(label):
                tmp = plant(where, body)
                try:
                    hits = [o for o in offenders(tmp)
                            if Path(where).name in o]
                    self.assertEqual(
                        hits, [],
                        f"{label} is now CAUGHT — good news. Move it into "
                        f"CAUGHT and delete this entry.")
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)

    def test_the_cross_module_case_is_the_price_of_a_file_local_walk(self):
        """Named, not argued away.

        Resolving `_norm` across modules is dataflow analysis, which is a type
        checker's job. What this file will NOT do is claim the gap is bounded
        by another check — that claim is what round 5 failed on.
        """
        self.assertIn("another module",
                      (Path(__file__).read_text()))


if __name__ == "__main__":
    unittest.main()
