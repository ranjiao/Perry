"""The guard over the guard: `tests/live_state_expectations.py` still finds
checks that read the live project as their expected value.

`tests/live_state_expectations.py` carries the definition of the class and the
list of what it deliberately does not catch. This module is the evidence that
the definition still bites, and it is built the only way that proves anything:
**the instances come out of git, not out of my hands.** A guard tested against
examples written the same afternoon as the guard proves that the author can
restate a regex twice.

Three of the eight known instances are checked in verbatim under
`tests/fixtures/live-state/`, each a whole module as it stood in the commit
before its repair:

| fixture | commit | repaired by | the assertion |
|---|---|---|---|
| `md_store.before.py` | `d90612a` | `f3c4461` | `report["kinds"] == {"setting": len(records)}` |
| `track_attribution.before.py` | `d90612a` | `f3c4461` | `[t["track"] …] == ["main"]` |
| `v5_signoff.before.py` | `e116f8a` | `cbbc41a` | `set(events) == set(self.SIGNED)` |

`d90612a` is `f3c4461^` and `e116f8a` is `cbbc41a^`: each fixture is the module
as the repair found it.

Whole modules rather than excerpts, because trimming to the interesting class
is hand-writing an approximation by another name — the analysis reads
module-level bindings, class attributes and sibling methods, and an excerpt
would be a different program. `test_the_fixtures_are_what_git_holds` compares
them byte-for-byte against `git show` when the history is reachable, and
`test_the_fixtures_have_not_been_edited` pins their SHA-256 for the CI checkout
that is shallow and cannot.

**Verification 2 is the other half and is not decoration.** A guard that still
flags the repaired form is measuring the wrong thing, so the repaired versions
are checked too — for `test_track_attribution` and `test_v5_signoff` that is
the file in the tree today, byte-identical to its fix commit; for
`test_md_store` the repaired assertion is gone and three others in that module
are not, which the baseline records with a verdict apiece.

**The floor is a recorded number, not zero.** Six hits over 65 modules, three
of them real. Asserting zero would have meant either widening three verdicts
into silence or fixing three rows this one is explicitly not allowed to fix.

Run: python3 tests/parallel test_live_state_expectations
"""

from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import live_state_expectations as L  # noqa: E402

ROOT = L.ROOT
FIXTURES = ROOT / "tests" / "fixtures" / "live-state"


class Reconstruction(unittest.TestCase):
    """One instance, as it stood before its repair and after it."""

    fixture = ""
    #: `git show <commit>:<path>` — what the fixture is a copy of.
    commit = ""
    path = ""
    sha256 = ""
    #: The repair, and the file that carries it today (`""` when the module has
    #: moved on since, and only the assertion's absence can be checked).
    repaired_by = ""
    repaired_file = ""
    #: What the guard must say about the unrepaired module, and what must have
    #: stopped being said about the repaired one.
    flagged_test = ""
    flagged_expected = ""

    def before(self) -> list[L.Finding]:
        return L.scan_source((FIXTURES / self.fixture).read_text(), self.path)

    def hits(self, findings) -> list[L.Finding]:
        return [f for f in findings
                if f.test == self.flagged_test
                and f.expected == self.flagged_expected]


class Instance6(Reconstruction):
    """`.perry/config.md` declared one track and every config record stopped
    being a `setting`. The literal is a dict DISPLAY whose value is computed —
    `{"setting": len(records)}` — so a guard that only looked for wholly
    constant expectations would have walked past it: what the line pins is the
    KEY SET, one kind named `setting`, whatever the count beside it says."""

    fixture = "md_store.before.py"
    commit = "d90612a149e44b6e76523df04749308bc9b0d201"
    path = "tests/test_md_store.py"
    sha256 = ("7f87dbc64c6c3004f90a023bd6eee0669b344e6e0409ee44cb42548"
              "fe3b477d7")
    repaired_by = "f3c44617f2d32abf102de35eeda0ea7e33eee2a0"
    repaired_file = "tests/test_md_store.py"
    flagged_test = ("TestThisRepositoryIsReproducedByteForByte."
                    "test_config_including_its_prose_section")
    flagged_expected = "{'setting': len(records)}"

    def test_the_unrepaired_module_is_flagged(self):
        self.assertEqual(len(self.hits(self.before())), 1,
                         "\n".join(str(f) for f in self.before()))

    def test_the_repair_is_not_flagged(self):
        current = (ROOT / self.repaired_file)
        found = L.scan_source(current.read_text(), self.repaired_file)
        self.assertEqual(self.hits(found), [])

    def test_the_derived_form_the_repair_used_is_not_flagged(self):
        """The shape the repair replaced it with, on its own.

        `set(report["kinds"]) == {r["kind"] for r in records}` reads the same
        live file and restates nothing about it, which is exactly the
        difference the class turns on. If this ever flags, the guard has
        stopped measuring closedness and started measuring "touched a file"."""
        found = L.scan_source(REPAIRED_SHAPE, "tests/test_x.py")
        self.assertEqual([str(f) for f in found], [])


class Instance7(Reconstruction):
    """The same declaration reddened `test_track_attribution`, which asserted
    that Perry itself has no track register. The repair proves the no-op
    property on a project that HAS no register instead of on this one."""

    fixture = "track_attribution.before.py"
    commit = "d90612a149e44b6e76523df04749308bc9b0d201"
    path = "tests/test_track_attribution.py"
    sha256 = ("7bbc7cad5fe9ee9e5b081e896c7e0126eec71e4c72fc72b115259d4"
              "87e5320d4")
    repaired_by = "f3c44617f2d32abf102de35eeda0ea7e33eee2a0"
    repaired_file = "tests/test_track_attribution.py"
    flagged_test = ("TestPerrysOwnProjectIsUnmoved."
                    "test_it_still_reads_one_project_track")
    flagged_expected = "['main']"

    def test_the_unrepaired_module_is_flagged(self):
        self.assertEqual(len(self.hits(self.before())), 1,
                         "\n".join(str(f) for f in self.before()))

    def test_the_repaired_module_is_clean_end_to_end(self):
        """Not just the one line: the whole module, which is what item 2 of
        the verification asks for. The repaired class still asserts `["main"]`
        — against a project it built itself, where a literal is a fixture and
        not a snapshot."""
        text = (ROOT / self.repaired_file).read_text()
        self.assertIn('["main"]', text, "the literal did not survive the "
                                        "repair, so this proves nothing")
        self.assertEqual(L.scan_source(text, self.repaired_file), [])


class Instance1(Reconstruction):
    """TASK-113's: `test_v5_signoff` named exactly three V5 closes and three
    more were signed the day it shipped. The literal is a CLASS ATTRIBUTE
    behind a `set()` call — `set(self.SIGNED)` — which is why the analysis
    folds constants through both."""

    fixture = "v5_signoff.before.py"
    commit = "e116f8a288a2f0d159c1d3bc03b9ce9eb44c32af"
    path = "tests/test_v5_signoff.py"
    sha256 = ("89eb77fbc216d1363915f4f9cabe9405d6c15e6b51663da65a3cf0c"
              "19284700a")
    repaired_by = "cbbc41af5e81f9b552ba8797eb17727d7e1934f0"
    repaired_file = "tests/test_v5_signoff.py"
    flagged_test = ("TestHistoryIsNotRewritten."
                    "test_the_three_existing_v5_closes_still_read")
    flagged_expected = "set(self.SIGNED)"

    def test_the_unrepaired_module_is_flagged(self):
        self.assertEqual(len(self.hits(self.before())), 1,
                         "\n".join(str(f) for f in self.before()))

    def test_the_repaired_module_is_clean_end_to_end(self):
        text = (ROOT / self.repaired_file).read_text()
        self.assertEqual(L.scan_source(text, self.repaired_file), [])

    def test_the_reader_the_repair_replaced_it_with_is_not_flagged(self):
        """`assertEqual(problems, [])` over whatever the journal holds. The
        empty display is what separates a property from a snapshot, and it is
        the shape all five of TASK-113's repairs converged on."""
        found = L.scan_source(QUANTIFIED_SHAPE, "tests/test_x.py")
        self.assertEqual([str(f) for f in found], [])


#: The repaired `test_md_store` assertion, standing alone. Reads the same live
#: file; expects nothing the file does not say.
REPAIRED_SHAPE = '''
import pathlib, unittest
ROOT = pathlib.Path(__file__).resolve().parent.parent

class T(unittest.TestCase):
    def test_it(self):
        records, report = derive(ROOT / ".perry" / "config.md")
        self.assertEqual(sum(report["kinds"].values()), len(records))
        self.assertEqual(set(report["kinds"]), {r["kind"] for r in records})
        self.assertEqual("track" in report["kinds"], has_register)
'''

#: The repaired `test_v5_signoff` shape: quantified over the log, expecting
#: emptiness rather than a roster.
QUANTIFIED_SHAPE = '''
import pathlib, unittest
ROOT = pathlib.Path(__file__).resolve().parent.parent

class T(unittest.TestCase):
    def test_it(self):
        log = ROOT / ".perry" / "events.jsonl"
        problems = [p for line in log.read_text().split("\\n")
                    for p in unreadable(line)]
        self.assertEqual(problems, [])
        self.assertEqual(len(problems), 0)
'''

#: A fixture-built project asserting exact literals — most of this suite, and
#: the thing a too-broad guard would drown in.
FIXTURE_SHAPE = '''
import pathlib, tempfile, unittest
ROOT = pathlib.Path(__file__).resolve().parent.parent

class T(unittest.TestCase):
    def test_it(self):
        root = pathlib.Path(tempfile.mkdtemp())
        (root / "BOARD.md").write_text(BOARD)
        rows = read(root / "BOARD.md")
        self.assertEqual([r["id"] for r in rows], ["TASK-001", "TASK-002"])
        self.assertEqual(rows[0]["priority"], "P1")
'''

#: The class itself, in one method, reached three different ways.
LIVE_SHAPE = '''
import json, pathlib, subprocess, sys, unittest
ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin" / "perry-state"

class T(unittest.TestCase):
    def test_a_file(self):
        rows = read((ROOT / "perry" / "BOARD.md").read_text())
        self.assertEqual([r["id"] for r in rows], ["TASK-001"])

    def test_a_count(self):
        rows = read((ROOT / "perry" / "tasks.jsonl").read_text())
        self.assertGreater(len(rows), 40)

    def test_a_tool(self):
        proc = subprocess.run([sys.executable, str(TOOL), "--json"],
                              capture_output=True, text=True, cwd=ROOT)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["tracks"], ["main"])
'''


class TestTheFixturesAreHistoryAndNotMyHandwriting(unittest.TestCase):
    """Verification 1 says *reconstruct*, and a fixture nobody can audit is
    indistinguishable from an approximation typed to match the guard."""

    CASES = (Instance6, Instance7, Instance1)

    def test_the_fixtures_have_not_been_edited(self):
        """Runs everywhere, including the shallow CI checkout."""
        for case in self.CASES:
            with self.subTest(fixture=case.fixture):
                blob = (FIXTURES / case.fixture).read_bytes()
                self.assertEqual(hashlib.sha256(blob).hexdigest(),
                                 case.sha256)

    def test_the_fixtures_are_what_git_holds(self):
        """Runs where the history is reachable. `.github/workflows/ci.yml`
        uses `actions/checkout@v4` at its default depth of 1, so this SKIPS on
        CI — which is why the digest above exists and is not redundant."""
        for case in self.CASES:
            with self.subTest(fixture=case.fixture):
                proc = subprocess.run(
                    ["git", "show", f"{case.commit}:{case.path}"],
                    capture_output=True, cwd=ROOT)
                if proc.returncode != 0:
                    self.skipTest(f"{case.commit[:7]} is not in this checkout: "
                                  f"{proc.stderr.decode()[:120]}")
                self.assertEqual((FIXTURES / case.fixture).read_bytes(),
                                 proc.stdout,
                                 f"{case.fixture} is not byte-identical to "
                                 f"{case.commit[:7]}:{case.path}")

    def test_every_fixture_still_parses_as_python(self):
        for case in self.CASES:
            with self.subTest(fixture=case.fixture):
                ast.parse((FIXTURES / case.fixture).read_text())


class TestTheTwoHalvesAreBothLoadBearing(unittest.TestCase):
    """Anti-vacuity. Each half is removed in turn and the answer must move.

    A guard nobody has watched go red is not a guard, and a guard nobody has
    watched go GREEN on the honest form is worse — it teaches people to route
    around it.
    """

    def scan(self, source: str) -> list[L.Finding]:
        return L.scan_source(source, "tests/test_x.py")

    def test_a_fixture_built_project_is_never_flagged(self):
        self.assertEqual(self.scan(FIXTURE_SHAPE), [])

    def test_live_state_with_a_closed_expectation_is_flagged_three_ways(self):
        found = {f.test.split(".")[-1] for f in self.scan(LIVE_SHAPE)}
        self.assertEqual(found, {"test_a_file", "test_a_count", "test_a_tool"},
                         "\n".join(str(f) for f in self.scan(LIVE_SHAPE)))

    def test_an_empty_expectation_over_live_state_is_not_flagged(self):
        self.assertEqual(self.scan(QUANTIFIED_SHAPE), [])

    def test_a_derived_expectation_over_live_state_is_not_flagged(self):
        self.assertEqual(self.scan(REPAIRED_SHAPE), [])

    def test_moving_the_read_off_live_state_clears_every_finding(self):
        """Half one, removed: the same assertions against `schema/` — a
        contract, which a test SHOULD pin exactly."""
        contract = LIVE_SHAPE.replace('"perry" / "BOARD.md"',
                                      '"schema" / "state-schema.json"')
        contract = contract.replace('"perry" / "tasks.jsonl"',
                                    '"schema" / "contract-shapes.json"')
        contract = contract.replace("cwd=ROOT", "cwd=self.tmp")
        self.assertEqual(self.scan(contract), [])


class TestTheLiveSetIsReadOutOfTheSchema(unittest.TestCase):
    """Instance 8's lesson: the literals that went stale were about *which
    paths the schema declares Perry owns*. A guard holding its own list of
    state files would have been wrong the day PR #14 merged."""

    def test_this_repository(self):
        patterns = L.live_patterns(ROOT)
        for live in ("perry/BOARD.md", "perry/tasks.jsonl", "perry/OKR.md",
                     "perry/journal/2026-08/2026-08-20.md",
                     ".perry/events.jsonl", ".perry/config.md"):
            with self.subTest(path=live):
                self.assertTrue(L.is_live_path(live, patterns))
        for code in ("schema/state-schema.json", "SKILL.md",
                     "bin/perry-task", "tests/fixtures/sample-project/BOARD.md",
                     "modes/queue.md", "state/BOARD_TEMPLATE.md"):
            with self.subTest(path=code):
                self.assertFalse(L.is_live_path(code, patterns))

    def project(self, state_root: str) -> list[str]:
        """A two-claim project with the `State root:` this asks for."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = pathlib.Path(tmp.name)
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            f"# Perry configuration\n\n- State root: {state_root}\n")
        (root / "schema").mkdir()
        (root / "schema" / "state-schema.json").write_text(json.dumps({
            "claims": [{"path": "BOARD.md", "anchor": "state"},
                       {"path": ".perry/", "anchor": "project"}],
            "files": [],
        }))
        return L.live_patterns(root)

    def test_the_same_claim_lands_where_the_state_root_points(self):
        """The proof that it is derived rather than listed. One schema, one
        claim, two projects: `BOARD.md` is at the top of the first and inside
        `docs/` in the second, and neither is written down here."""
        flat = self.project(".")
        self.assertTrue(L.is_live_path("BOARD.md", flat))
        self.assertFalse(L.is_live_path("docs/BOARD.md", flat))

        nested = self.project("docs")
        self.assertTrue(L.is_live_path("docs/BOARD.md", nested))
        self.assertFalse(L.is_live_path("BOARD.md", nested),
                         "the claim followed the state root, so a file at the "
                         "top is no longer the one the schema declares")
        for both in (flat, nested):
            self.assertTrue(L.is_live_path(".perry/events.jsonl", both),
                            "`anchor: project` never moves")


class TestTheFloorIsRecordedNotAssumed(unittest.TestCase):
    """Verification 3. Every hit is in the baseline with a verdict; a hit that
    is not is a red, and so is a baseline entry the sweep no longer makes."""

    def setUp(self):
        self.found = L.sweep(ROOT)
        self.known = L.recorded()

    def test_the_baseline_and_the_sweep_agree(self):
        new = [str(f) for f in self.found if f.key not in self.known]
        gone = [k for k in self.known if k not in {f.key for f in self.found}]
        self.assertEqual(new, [], "a check has started reading live project "
                                  "state as its expected value")
        self.assertEqual(gone, [], "a recorded finding is gone — re-record "
                                   "with `--record`, which keeps the verdicts")

    def test_every_recorded_finding_carries_a_verdict_and_a_reason(self):
        for entry in json.loads(L.BASELINE.read_text())["findings"]:
            with self.subTest(where=f"{entry['module']}:{entry['lineno']}"):
                self.assertIn(entry["verdict"], ("instance", "false positive"))
                self.assertGreater(len(entry["why"]), 60,
                                   "a verdict without a reason is a silence")

    def test_the_floor_is_not_claimed_to_be_zero(self):
        """The floor is real and every entry in it is judged.

        **This assertion used to be the very defect this module reports.** It
        read `count("instance") == 3` and `count("false positive") == 3` — a
        census of what the repository happened to hold the day it was written —
        and it went red on 2026-08-21 when TASK-122 landed one more test, for a
        reason that had nothing to do with whether the guard works. The guard
        found its own test.

        What is asserted now is the property: the recorded floor matches what
        the sweep finds, it is not empty, and **at least one entry is a real
        instance** — a floor of nothing but false positives would mean the
        guard had stopped discriminating. The exact counts belong in the
        fixture, which is versioned and re-recorded on purpose, not here.
        """
        verdicts = [e["verdict"]
                    for e in json.loads(L.BASELINE.read_text())["findings"]]
        self.assertEqual(len(self.found), len(verdicts),
                         "the recorded floor and the live sweep disagree — "
                         "re-record with --record and judge what is new")
        self.assertGreater(len(verdicts), 0,
                           "a floor of zero would be a claim this repository "
                           "has no instances, which was measured false")
        self.assertGreater(
            verdicts.count("instance"), 0,
            "every recorded finding is a false positive — either they were all "
            "fixed, in which case say so here, or the guard stopped finding "
            "the thing it exists to find")


if __name__ == "__main__":
    unittest.main()
