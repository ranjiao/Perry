"""TASK-475 — `perry-goals objective add`, the writer for phase objectives.

`phase new` writes a phase's prose and `phase/CURRENT` and no record;
`kr add --objective O` refuses an objective the phase does not declare; and the
procedure forbids appending one by hand. Before this verb a phase opened by the
writer could carry no KR at all — found live on 2026-09-21, a project whose
phase 003 had zero objectives and no way to get one.

This module holds the row's Verification: on a phase with no objectives,
`objective add` then `kr add` both succeed and `krs` lists the KR; every
refusal exits non-zero and moves not a byte of the store or the event log.

Every write goes to a project built under a temporary root (NN-5).

Run: python3 tests/parallel test_goals_objective_add
"""

from __future__ import annotations

COVERS = (
    "bin/perry-goals",
    "bin/lib/",
    "viewer/parsers.py",
    "schema/state-schema.json",
)

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test_goals_kr_revisions import Project  # noqa: E402
from test_goals_kr_writer import _phase_doc  # noqa: E402

FRESH = "005-fresh"


class ObjectiveProject(Project):
    def goals(self, *argv):
        argv = list(argv)
        if argv[:1] == ["objective"] and "--actor" not in argv \
                and "--no-actor" not in argv:
            argv += ["--actor", self.ACTOR]
        argv = [a for a in argv if a != "--no-actor"]
        return super().goals(*argv)

    def fresh_phase(self):
        """A current, active phase with no objective record — what `phase
        new` leaves behind."""
        (self.root / "phase" / f"{FRESH}.md").write_text(
            _phase_doc("005", "fresh", "active"))
        (self.root / "phase" / "CURRENT").write_text(f"{FRESH}\n")

    def add(self, oid="O1", text="the first objective", reason="why"):
        return self.ok("objective", "add", oid, "--text", text,
                       "--reason", reason)


class TestEndToEnd(ObjectiveProject):

    def test_objective_then_kr_on_a_phase_with_none(self):
        self.fresh_phase()
        self.assertRefused(
            ["kr", "add", "P005-O1-KR1", "--objective", "O1", "--text", "t",
             "--reason", "r"], "it has none")
        prior = self.linkage.read_bytes()
        got = self.add()
        self.assertTrue(got["written"])
        self.assertEqual(got["record"], {"kind": "objective", "phase": FRESH,
                                         "id": "O1",
                                         "title": "the first objective"})
        after = self.linkage.read_bytes()
        self.assertTrue(after.startswith(prior), "an append rewrote the store")
        self.assertEqual(json.loads(after[len(prior):]), got["record"])
        event = self.lines(self.events)[-1]
        self.assertEqual((event["event"], event["objective"], event["phase"],
                          event["actor"], event["reason"]),
                         ("objective_add", "O1", FRESH, self.ACTOR, "why"))

        self.ok("kr", "add", "P005-O1-KR1", "--objective", "O1",
                "--text", "a key result", "--reason", "r")
        objectives = self.ok("krs")["objectives"]
        self.assertEqual([(o["id"], [k["id"] for k in o["krs"]])
                          for o in objectives], [("O1", ["P005-O1-KR1"])])

    def test_file_order_is_objective_order(self):
        self.fresh_phase()
        self.add("O2", "second")
        self.add("O1", "first")
        for oid in ("O1", "O2"):
            self.ok("kr", "add", f"P005-{oid}-KR1", "--objective", oid,
                    "--text", "k", "--reason", "r")
        self.assertEqual([o["id"] for o in self.ok("krs")["objectives"]],
                         ["O2", "O1"])

    def test_dry_run_writes_nothing(self):
        self.fresh_phase()
        before = self.snapshot()
        got = self.ok("objective", "add", "O1", "--text", "t", "--reason",
                      "r", "--dry-run")
        self.assertFalse(got["written"])
        self.assertEqual(before, self.snapshot())

    def test_the_first_phase_creates_the_store(self):
        self.fresh_phase()
        self.linkage.unlink()
        self.add()
        self.assertEqual([r["id"] for r in self.lines(self.linkage)], ["O1"])


class TestARenamedPhaseIsTheSamePhase(ObjectiveProject):
    """TASK-475 V4 round 2, F2, and its two siblings in `kr add` (USER-979).
    Readers group a phase's records by NUMBER; the writers matched the exact
    slug. After the document is renamed and CURRENT repointed, the records
    filed under the old slug are still the phase's to every reader."""

    def renamed(self):
        self.fresh_phase()
        self.add("O1", "first")
        old = self.root / "phase" / f"{FRESH}.md"
        old.rename(self.root / "phase" / "005-renamed.md")
        (self.root / "phase" / "CURRENT").write_text("005-renamed\n")

    def test_objective_add_refuses_an_id_filed_under_the_old_slug(self):
        self.renamed()
        self.assertRefused(["objective", "add", "O1", "--text", "t",
                            "--reason", "r"], "already declares objective O1")

    def test_kr_add_finds_the_objective_filed_under_the_old_slug(self):
        self.renamed()
        self.ok("kr", "add", "P005-O1-KR1", "--objective", "O1",
                "--text", "k", "--reason", "r")

    def test_the_kr_cap_counts_krs_filed_under_the_old_slug(self):
        self.fresh_phase()
        self.add("O1", "first")
        for n in range(1, 5):
            self.ok("kr", "add", f"P005-O1-KR{n}", "--objective", "O1",
                    "--text", "k", "--reason", "r")
        old = self.root / "phase" / f"{FRESH}.md"
        old.rename(self.root / "phase" / "005-renamed.md")
        (self.root / "phase" / "CURRENT").write_text("005-renamed\n")
        self.assertRefused(["kr", "add", "P005-O1-KR5", "--objective", "O1",
                            "--text", "k", "--reason", "r"], "already")


class TestRefusals(ObjectiveProject):

    def test_an_id_the_phase_already_declares(self):
        # `004-now` is current and already declares O1.
        self.assertRefused(["objective", "add", "O1", "--text", "t",
                            "--reason", "r"], "already declares objective O1",
                           "never reused")

    def test_the_same_id_in_another_phase_is_not_a_reuse(self):
        self.fresh_phase()
        self.add("O1")  # 004-now also has an O1; ids are per phase

    def test_an_id_that_is_not_an_objective_id(self):
        self.assertRefused(["objective", "add", "P004-O2", "--text", "t",
                            "--reason", "r"], "is not an objective id")

    def test_no_text(self):
        self.assertRefused(["objective", "add", "O2", "--reason", "r"],
                           "--text is required")

    def test_no_reason_or_a_reason_on_two_lines(self):
        self.assertRefused(["objective", "add", "O2", "--text", "t"],
                           "needs --reason")
        self.assertRefused(["objective", "add", "O2", "--text", "t",
                            "--reason", "a\nb"], "line break")

    def test_an_unreadable_store(self):
        # Round 1's V4: read as empty, an unparseable store let a second O1
        # through, exit 0, record and event written.
        with self.linkage.open("a") as f:
            f.write("<<<<<<< HEAD\n")
        self.assertRefused(["objective", "add", "O1", "--text", "t",
                            "--reason", "r"], "cannot be read as JSONL")

    def test_a_scored_phase(self):
        (self.root / "phase" / "CURRENT").write_text("002-old\n")
        self.assertRefused(["objective", "add", "O2", "--text", "t",
                            "--reason", "r"], "is scored")

    def test_no_current_phase(self):
        (self.root / "phase" / "CURRENT").write_text("")
        self.assertRefused(["objective", "add", "O2", "--text", "t",
                            "--reason", "r"], "no current phase")

    def test_an_op_other_than_add(self):
        self.assertRefused(["objective", "restate", "O1", "--text", "t",
                            "--reason", "r"], "takes `add` and one <O-ID>")

    def test_no_actor_and_a_foreign_flag_exit_2(self):
        self.assertRefused(["objective", "add", "O2", "--text", "t",
                            "--reason", "r", "--no-actor"], "--actor",
                           code=2)
        self.assertRefused(["objective", "add", "O2", "--text", "t",
                            "--reason", "r", "--objective", "O1"],
                           "does not take --objective", code=2)


if __name__ == "__main__":
    unittest.main()
