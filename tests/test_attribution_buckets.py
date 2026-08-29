"""`attribution`'s three buckets are disjoint. TASK-228.

`perry-state --section attribution` reports `linked`, `unlinked` and
`declared_unlinked`. `unlinked` was built by asking "did this row resolve to a
KR?" — which is false for a **declared** row as much as an undeclared one, so
every id in the register's `unlinked[]` was reported in BOTH buckets.

Measured 2026-08-28 on Perry's own board, after declaring 48 rows:
`linked=8, unlinked=48, declared_unlinked=48`, and the two sets were
byte-identical.

**It is not a cosmetic double-count.** `unlinked` is the number a standup
renders as *"N tasks awaiting KR attribution"*. On 2026-08-29 it was read off
this payload and reported to the user as 52 rows owing an answer — when the
true never-asked count was **0**. Every one of those answers had been given the
day before, through `perry-goals link --unlinked`, with the user's consent. The
payload turned finished work into outstanding work, and the person it misled
was the person who had done it.

`reference/okr-linkage.md` had it right all along: *"`linked`, `unlinked`
(couldn't resolve), and `declared_unlinked` (the graph says outright that this
work serves no KR)"*. The document described three states and the code
implemented two. This module is the agreement between them.

**Why the never-asked reading is the load-bearing one.**
`phase/003-storage-code.md § P003-O3-KR1` drives to zero *"open `main`-track
rows in neither `objectives[].krs[].tasks[]` nor a declared `unlinked[]` — the
never-asked state"*, and says in as many words that work serving no KR is a
legitimate declarable state. A bucket folding the declared into the unresolved
makes that KR unmeasurable from the very payload it is defined against.

**The fixture is `tests/fixtures/sample-project`, copied**, not hand-built. It
already carries the exact shape under test — `REL-001`/`REL-002` linked,
`REL-009` declared `unlinked` — so the case is real rather than constructed,
and a fixture that drifts breaks this module loudly instead of quietly
asserting nothing. The first draft of this file DID hand-build a board; it
produced `linked: 0, unlinked: []` because no row parsed at all, and every
assertion in it passed vacuously on an empty set.

Run: python3 tests/parallel test_attribution_buckets
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / "bin" / "perry-state"
SAMPLE = ROOT / "tests" / "fixtures" / "sample-project"


class Fixture(unittest.TestCase):

    def project(self, *, declared: list[str] | None = None) -> pathlib.Path:
        """A copy of the sample project, optionally with a rewritten `unlinked`."""
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-attribution-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        dest = d / "sample-project"
        shutil.copytree(SAMPLE, dest)
        if declared is not None:
            link = dest / "phase" / "002-linkage.md"
            ids = ", ".join(declared)
            link.write_text(re.sub(r"^unlinked: \[.*?\]$",
                                   f"unlinked: [{ids}]",
                                   link.read_text(), count=1, flags=re.M))
        return dest

    def attribution(self, d: pathlib.Path) -> dict:
        proc = subprocess.run(
            [sys.executable, str(STATE), "--root", str(d),
             "--section", "attribution"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return json.loads(proc.stdout)["attribution"]

    def open_rows(self, d: pathlib.Path) -> list[dict]:
        proc = subprocess.run(
            [sys.executable, str(STATE), "--root", str(d), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return [t for t in json.loads(proc.stdout)["board"]["tasks"]
                if t["status"] not in {"done", "dropped"}
                and t.get("priority") != "Cadence"]


class TestTheFixtureIsTheShapeUnderTest(Fixture):
    """The control. Without it every assertion below could pass on nothing.

    The hand-built first draft of this module parsed zero rows and every
    disjointness assertion held trivially over two empty sets.
    """

    def test_the_sample_project_has_rows_in_all_three_states(self):
        att = self.attribution(self.project())
        self.assertGreater(att["linked"], 0, "no linked row — fixture drifted")
        self.assertEqual(list(att["declared_unlinked"]), ["REL-009"])
        self.assertGreater(len(self.open_rows(self.project())), 0)


class TestTheThreeBucketsAreDisjoint(Fixture):

    def test_a_declared_row_is_not_also_reported_as_unresolved(self):
        """The row. `REL-009` is declared; it belongs to one bucket."""
        att = self.attribution(self.project())
        unlinked = {r["id"] for r in att["unlinked"]}
        declared = set(att["declared_unlinked"])
        self.assertIn("REL-009", declared)
        self.assertNotIn("REL-009", unlinked)
        self.assertEqual(unlinked & declared, set(),
                         "the two buckets overlap — the double-count is back")

    def test_nothing_is_never_asked_in_the_shipped_fixture(self):
        """`P003-O3-KR1`'s target state, and the one the live defect faked.

        Perry's own board was in exactly this state on 2026-08-29 and the
        payload reported 52.
        """
        self.assertEqual(self.attribution(self.project())["unlinked"], [])

    def test_a_linked_row_is_in_neither_bucket(self):
        att = self.attribution(self.project())
        self.assertNotIn("REL-001", {r["id"] for r in att["unlinked"]})
        self.assertNotIn("REL-001", set(att["declared_unlinked"]))

    def test_every_open_row_lands_in_exactly_one_bucket(self):
        """The invariant behind the others, asserted as arithmetic.

        No row counted twice and none lost. A future fourth state has to come
        here and say what it is.
        """
        d = self.project()
        att = self.attribution(d)
        ids = {t["id"] for t in self.open_rows(d)}
        declared_open = ids & set(att["declared_unlinked"])
        self.assertEqual(
            att["linked"] + len(att["unlinked"]) + len(declared_open),
            len(ids),
            "the buckets do not partition the open rows")


class TestDeclaringARowMovesItBetweenBuckets(Fixture):
    """The mutation this row's own Verification asks for, run both ways."""

    def test_undeclaring_a_row_puts_it_in_unlinked_and_nowhere_else(self):
        att = self.attribution(self.project(declared=[]))
        self.assertEqual([r["id"] for r in att["unlinked"]], ["REL-009"])
        self.assertEqual(list(att["declared_unlinked"]), [])

    def test_declaring_it_again_takes_it_back_out(self):
        att = self.attribution(self.project(declared=["REL-009"]))
        self.assertEqual(att["unlinked"], [])
        self.assertEqual(list(att["declared_unlinked"]), ["REL-009"])


class TestTheDocumentAndThePayloadAgree(unittest.TestCase):
    """TASK-228's deliverable names both halves; the doc was already right.

    `reference/okr-linkage.md` distinguishes "couldn't resolve" from "the graph
    says outright that this work serves no KR". Nothing enforced it, which is
    how the payload drifted from the page describing it.
    """

    PAGE = ROOT / "reference" / "okr-linkage.md"

    def test_the_page_still_describes_three_distinct_states(self):
        text = self.PAGE.read_text()
        self.assertIn("`unlinked` (couldn't resolve)", text)
        self.assertIn("`declared_unlinked`", text)

    def test_the_page_says_the_buckets_are_disjoint(self):
        """Added by TASK-228 — the sentence a reader needs to trust a count."""
        self.assertIn("disjoint", self.PAGE.read_text().lower())


if __name__ == "__main__":
    unittest.main()
