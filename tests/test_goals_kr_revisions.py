"""TASK-264 deliverable 3 — KR add, restate and withdraw (DESIGN-022 § 5.7).

A KR's words change by APPENDING: `perry-goals kr add` appends a `kr` record,
`kr restate` / `kr withdraw` append a `kr_revision` record, each to the store
that holds the KR (`linkage.jsonl` for a phase KR, `okr.jsonl` for an overall
KR). What a KR is now is `bin/lib § kr_revisions`' fold, and every reader
reads it. This module holds the spec's Verification section:

- **the fold rule**, unit by unit (`TestTheFold`): `revised_at` order, file
  order on a tie, restate overwrites only what it names, withdraw is
  terminal, and every revision that breaks a rule is reported and not applied;
- **end to end, at both levels** (`TestPhaseEndToEnd`, `TestOverallEndToEnd`):
  add → check → measure → restate → withdraw → measure refused, with
  `krs --json`, `phase.kr_progress` and `OKR.md`'s bytes at each step;
- **every refusal** in § 5.7 (`TestRefusals`): the exit code, byte snapshots
  of both stores, `OKR.md` and the event log, and the recovery command;
- **every reader** (`TestReaders`): `perry-goals list`, `perry-state`,
  `perry-lint`, and `commit`'s write path carrying a revision through.

Every write goes to a project built under a temporary root (NN-5); nothing
here reads or writes this repository's own `perry/`.

Run: python3 tests/parallel test_goals_kr_revisions
"""

from __future__ import annotations

COVERS = (
    "bin/perry-goals",
    "bin/perry-state",
    "bin/perry-lint",
    "bin/lib/",
    "bin/perry_md_store.py",
    "viewer/parsers.py",
    "schema/state-schema.json",
)

import json
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "bin"))
import inproc  # noqa: E402
import lib  # noqa: E402
from test_goals_kr_writer import V3, V4, make_project  # noqa: E402

LINKAGE = "linkage.jsonl"
OKR = "okr.jsonl"
STATE = inproc.load("perry-state")


def revision(kr, op="restate", fields=None, reason="why",
             revised_at="2026-09-18T10:00:00+08:00", okr_version="",
             actor="t"):
    return {"kind": "kr_revision", "kr": kr, "okr_version": okr_version,
            "op": op, "fields": {} if fields is None else fields,
            "reason": reason, "revised_at": revised_at, "actor": actor}


def kr(kid="P004-O1-KR1", **extra):
    return {"kind": "kr", "phase": "004-now", "objective": "O1", "id": kid,
            "title": f"{kid} title", "target": 7, **extra}


class TestTheFold(unittest.TestCase):
    """`lib.kr_revisions` / `lib.fold_kr_records` — § 5.7's four rules."""

    def fold(self, *revs, base=None, store=LINKAGE):
        records = [base or kr(), *revs]
        views, findings = lib.kr_revisions(records, store)
        key = lib.kr_revision_key(records[0], store)
        return views[key], findings

    def test_revisions_apply_in_revised_at_order_not_file_order(self):
        """Rule 1. The LATER line is the EARLIER revision: file order would
        leave the target at 5, `revised_at` order leaves it at 6. The two
        stamps are in different offsets, so text order would also be wrong:
        `…T09:00:00Z` is 17:00 at +08:00, after `…T12:00:00+08:00`."""
        view, findings = self.fold(
            revision("P004-O1-KR1", fields={"target": 6},
                     revised_at="2026-09-18T09:00:00Z"),
            revision("P004-O1-KR1", fields={"target": 5},
                     revised_at="2026-09-18T12:00:00+08:00"))
        self.assertEqual(findings, [])
        self.assertEqual(view["fields"], {"target": 6})
        self.assertEqual([r["changes"] for r in view["revisions"]], [
            [{"field": "target", "before": 7, "after": 5}],
            [{"field": "target", "before": 5, "after": 6}]])

    def test_equal_timestamps_apply_in_file_order(self):
        view, _ = self.fold(
            revision("P004-O1-KR1", fields={"target": 5}),
            revision("P004-O1-KR1", fields={"target": 6}))
        self.assertEqual(view["fields"], {"target": 6})

    def test_restate_overwrites_only_the_fields_it_names(self):
        records = [kr(metric="m"),
                   revision("P004-O1-KR1", fields={"title": "new words"})]
        folded = lib.fold_kr_records(records, LINKAGE)
        self.assertEqual(folded, [{**kr(metric="m"), "title": "new words"}])
        self.assertEqual(records[0]["title"], "P004-O1-KR1 title",
                         "the fold modified the record it was handed")

    def test_withdraw_is_terminal_and_a_revision_after_it_is_not_applied(self):
        view, findings = self.fold(
            revision("P004-O1-KR1", op="withdraw", reason="mistyped",
                     revised_at="2026-09-18T10:00:00+08:00"),
            revision("P004-O1-KR1", fields={"target": 1},
                     revised_at="2026-09-18T11:00:00+08:00"))
        self.assertEqual(view["status"], "withdrawn")
        self.assertEqual(view["withdrawn_reason"], "mistyped")
        self.assertEqual(view["withdrawn_at"], "2026-09-18T10:00:00+08:00")
        self.assertEqual(view["fields"], {})
        self.assertEqual(len(view["revisions"]), 1)
        self.assertEqual([f["line"] for f in findings], [3])
        self.assertIn("withdrawn", findings[0]["message"])

    def test_an_identity_field_is_not_applied_at_either_level(self):
        for store, base, field in (
                (LINKAGE, kr(), "objective"), (LINKAGE, kr(), "id"),
                (LINKAGE, kr(), "phase"),
                (OKR, {"kind": "kr", "version": V4, "id": "O4-KR1",
                       "objective_id": "O-14", "order": 2, "text": "t"},
                 "objective_id"),
                (OKR, {"kind": "kr", "version": V4, "id": "O4-KR1",
                       "text": "t", "order": 2}, "order")):
            with self.subTest(store=store, field=field):
                key = lib.kr_revision_key(base, store)
                view, findings = self.fold(
                    revision(key[0], okr_version=key[1],
                             fields={field: "X"}), base=base, store=store)
                self.assertEqual(view["fields"], {})
                self.assertEqual(len(findings), 1)
                self.assertIn("identity", findings[0]["message"])

    def test_each_malformed_revision_is_reported_and_skipped(self):
        cases = {
            "unknown KR": revision("P004-O9-KR9"),
            "bad op": revision("P004-O1-KR1", op="rename"),
            "empty reason": revision("P004-O1-KR1", reason="  "),
            "bad revised_at": revision("P004-O1-KR1", revised_at="yesterday"),
            "fields not an object": revision("P004-O1-KR1", fields=["x"]),
            "restate names nothing": revision("P004-O1-KR1", fields={}),
            "withdraw carries fields": revision("P004-O1-KR1", op="withdraw",
                                                fields={"target": 1}),
        }
        for name, rev in cases.items():
            with self.subTest(name):
                views, findings = lib.kr_revisions([kr(), rev], LINKAGE)
                self.assertEqual(len(findings), 1, findings)
                self.assertEqual(views[("P004-O1-KR1", "")]["revisions"], [])
                self.assertEqual(views[("P004-O1-KR1", "")]["status"], "active")

    def test_an_overall_kr_is_keyed_by_its_version(self):
        records = [{"kind": "kr", "version": V3, "id": "O1-KR1", "text": "a"},
                   {"kind": "kr", "version": V4, "id": "O1-KR1", "text": "b"},
                   revision("O1-KR1", op="withdraw", okr_version=V4)]
        views, _ = lib.kr_revisions(records, OKR)
        self.assertEqual(views[("O1-KR1", V3)]["status"], "active")
        self.assertEqual(views[("O1-KR1", V4)]["status"], "withdrawn")

    def test_the_identity_fields_are_the_schema_s(self):
        """Read from the declaration beside the record, per level."""
        schema = json.loads((HERE.parent / "schema" /
                             "state-schema.json").read_text())
        declared = schema["stores"]["declared"]
        self.assertEqual(lib.kr_identity_fields(LINKAGE),
                         {"kind", "id", "phase", "objective"})
        self.assertEqual(lib.kr_identity_fields(OKR),
                         {"kind", "id", "version", "objective", "objective_id",
                          "order"})
        for store in (LINKAGE, OKR):
            spec = declared[store]["records"]["kr_revision"]
            self.assertEqual(set(spec["fields"]), {
                "kind", "kr", "okr_version", "op", "fields", "reason",
                "revised_at", "actor"})
            self.assertEqual(spec["fields"]["op"]["pattern"],
                             "^(" + "|".join(lib.KR_REVISION_OPS) + ")$")

    def test_a_withdrawn_kr_leaves_every_count(self):
        krs = [{"id": "a", "stretch": False, "state": "measured", "met": True},
               {"id": "b", "stretch": False, "state": "measured", "met": True,
                "status": "withdrawn", "withdrawn_at": "t",
                "withdrawn_reason": "r"}]
        got = lib.objective_kr_summary(krs)
        self.assertEqual((got["total"], got["measured"], got["met"]), (1, 1, 1))
        self.assertEqual(lib.withdrawn_krs(krs),
                         [{"id": "b", "withdrawn_at": "t", "reason": "r"}])


class Project(unittest.TestCase):
    ACTOR = "pmo"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="goals-kr-revisions-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = make_project(self.tmp / "p")
        self.linkage = self.root / LINKAGE
        self.okr = self.root / OKR
        self.okr_md = self.root / "OKR.md"
        self.events = self.root / ".perry" / "events.jsonl"

    def goals(self, *argv):
        argv = list(argv)
        if argv[:1] in (["kr"], ["check"], ["measure"]) and "--actor" not in argv:
            argv += ["--actor", self.ACTOR]
        return inproc.run("perry-goals", [*argv, "--root", str(self.root)],
                          env={"PERRY_PROJECT": None})

    def ok(self, *argv) -> dict:
        got = self.goals(*argv, "--json")
        self.assertEqual(got.returncode, 0, got.stdout + got.stderr)
        return json.loads(got.stdout)

    def snapshot(self):
        return tuple(p.read_bytes() if p.exists() else None
                     for p in (self.linkage, self.okr, self.okr_md,
                               self.events))

    def assertRefused(self, argv, *recovery, code=1):
        """Exit `code`; not a byte of either store, `OKR.md` or the log
        moved; and the message names each recovery fragment."""
        before = self.snapshot()
        got = self.goals(*argv)
        self.assertEqual(got.returncode, code, got.stdout + got.stderr)
        self.assertEqual(before, self.snapshot(), "a refusal wrote")
        said = got.stdout + got.stderr
        for fragment in recovery:
            self.assertIn(fragment, said)
        if code == 1:
            self.assertIn("Nothing was written", said)
        return said

    def phase_kr(self, kid) -> dict:
        krs = [k for o in self.ok("krs")["objectives"] for k in o["krs"]]
        return next(k for k in krs if k["id"] == kid)

    def overall_kr(self, kid, version=V4) -> dict:
        got = self.ok("krs", "--level", "overall", "--version", version)
        return next(k for v in got["versions"] for o in v["objectives"]
                    for k in o["krs"] if k["id"] == kid)

    def with_commitments(self):
        """An empty `## Commitments` table and a `pipeline` track, so
        `commit` has a register and a track to file against.

        The `### Objective` headings are left out ON PURPOSE: on the base
        tree, `commit` re-derives an objective record from its heading with
        `id: ""` and so blanks every minted objective id whose heading is in
        the file (probed at `5e5407ea`; not this row's defect, reported in
        its result). Without them no id is blanked and the KRs stay placed."""
        import config_store
        config_store.write_config(self.root, tracks=[
            config_store.track("main", "pipeline")])
        self.okr_md.write_text(
            f"# OKR — fixture\n\n## Mission\n\nA fixture.\n\n## {V3}\n\n"
            f"## {V4}\n" + (
            "\n## Commitments\n\n| Id | Track | Promise | To whom | Due | "
            "Status | By when note | Discharged by |\n"
            "|---|---|---|---|---|---|---|---|\n"))

    def with_phase_objective(self):
        """`## Objective 1` in the phase document, so `list` groups the
        phase's KRs (`parsers § phase_key_results_by_objective`)."""
        doc = self.root / "phase" / "004-now.md"
        doc.write_text(doc.read_text() + "\n## Objective 1 — now\n\nGoal.\n")

    def lines(self, path) -> list[dict]:
        return [json.loads(line) for line in path.read_text().splitlines()
                if line.strip()]

    def state(self) -> dict:
        got = inproc.run("perry-state", ["--json", "--root", str(self.root)],
                         env={"PERRY_PROJECT": None})
        self.assertEqual(got.returncode, 0, got.stderr[-400:])
        return json.loads(got.stdout)


class TestPhaseEndToEnd(Project):
    """The spec's phase sequence, in order, through the CLI."""

    def test_add_check_measure_restate_withdraw_then_measure_refused(self):
        before = self.linkage.read_bytes()
        added = self.ok("kr", "add", "P004-O1-KR2", "--objective", "O1",
                        "--text", "p90 next-action length", "--set",
                        "target=400", "--reason", "phase 004 needs it")
        self.assertTrue(added["written"] and added["event_written"])
        self.assertTrue(self.linkage.read_bytes().startswith(before),
                        "an add rewrote a byte it did not append")
        self.assertEqual(self.lines(self.linkage)[-1], {
            "kind": "kr", "phase": "004-now", "objective": "O1",
            "id": "P004-O1-KR2", "title": "p90 next-action length",
            "target": 400})

        self.ok("check", "P004-O1-KR2", "--id", "p90", "--direction",
                "decrease", "--baseline", "1702", "--target", "400",
                "--label", "p90")
        self.ok("measure", "P004-O1-KR2", "--check", "p90", "--value", "1051",
                "--evidence", "evidence/2026-09/m.md")
        self.assertEqual(self.phase_kr("P004-O1-KR2")["state"], "measured")

        self.ok("kr", "restate", "P004-O1-KR2", "--set", "target=300",
                "--reason", "tightened")
        got = self.phase_kr("P004-O1-KR2")
        self.assertEqual(got["target"], 300)
        self.assertEqual(got["status"], "active")
        self.assertEqual(got["revisions"][0]["changes"],
                         [{"field": "target", "before": 400, "after": 300}])
        self.assertEqual(got["state"], "measured",
                         "a restate dropped the KR's measurements")

        self.ok("kr", "withdraw", "P004-O1-KR2", "--reason", "mistyped")
        got = self.phase_kr("P004-O1-KR2")
        self.assertEqual(got["status"], "withdrawn")
        self.assertEqual(got["withdrawn_reason"], "mistyped")
        self.assertEqual([r["op"] for r in got["revisions"]],
                         ["restate", "withdraw"])

        payload = self.state()
        counts, why = STATE.next_kr_progress(payload)
        self.assertEqual(why, "")
        # P004-O1-KR1 and O2-KR1 remain; the withdrawn KR is in no count.
        self.assertEqual(counts, {"commit_total": 2, "measured": 0, "met": 0,
                                  "unmeasured": 2})
        self.assertEqual(STATE.next_kr_withdrawn(payload), [
            {"id": "P004-O1-KR2", "withdrawn_at": got["withdrawn_at"],
             "reason": "mistyped"}])
        facts, _unknown = STATE.next_facts(payload, date.today())
        self.assertEqual(facts["phase.kr_progress.withdrawn"], 1)

        self.assertRefused(["measure", "P004-O1-KR2", "--check", "p90",
                            "--value", "400", "--evidence",
                            "evidence/2026-09/m.md"],
                           "withdrawn", "perry-goals kr add")
        events = [e["event"] for e in self.lines(self.events)]
        self.assertEqual(events, ["kr_add", "check", "measure", "kr_restate",
                                  "kr_withdraw"])
        self.assertEqual(self.lines(self.events)[3]["changes"],
                         {"target": {"before": 400, "after": 300}})


class TestOverallEndToEnd(Project):
    """The same sequence on an overall KR, with `OKR.md`'s bytes at each step.

    `OKR.md` carries no KR row (TASK-236), so every step leaves it byte for
    byte as it was, and the byte gate — render(`OKR.md`, the store) ==
    `OKR.md` — holds after each."""

    def assertGateHolds(self):
        sys.path.insert(0, str(HERE.parent / "bin"))
        import perry_md_store as md
        text = self.okr_md.read_text(encoding="utf-8")
        rendered, _report = md.render(md.OKR, text,
                                      md.load_store(self.okr))
        self.assertEqual(rendered, text)

    def test_add_check_measure_restate_withdraw_then_measure_refused(self):
        okr_md = self.okr_md.read_bytes()
        store = self.okr.read_bytes()
        self.ok("kr", "add", "O4-KR2", "--okr-version", V4, "--objective",
                "O-14", "--text", "overall words", "--set", "metric=≤ 400",
                "--reason", "v4 gap")
        self.assertEqual(self.okr_md.read_bytes(), okr_md)
        self.assertTrue(self.okr.read_bytes().startswith(store))
        self.assertGateHolds()
        self.assertEqual(self.overall_kr("O4-KR2")["text"], "overall words")

        self.ok("check", "O4-KR2", "--id", "len", "--direction", "at_most",
                "--target", "400", "--label", "length")
        self.ok("measure", "O4-KR2", "--check", "len", "--value", "380",
                "--evidence", "evidence/2026-09/m.md")

        self.ok("kr", "restate", "O4-KR2", "--set", "text=restated words",
                "--reason", "clearer")
        got = self.overall_kr("O4-KR2")
        self.assertEqual(got["text"], "restated words")
        self.assertEqual(got["revisions"][0]["changes"], [
            {"field": "text", "before": "overall words",
             "after": "restated words"}])
        self.assertEqual(self.okr_md.read_bytes(), okr_md)
        self.assertGateHolds()
        rendered = self.goals("krs", "--level", "overall").stdout
        self.assertIn("| O4-KR2 | restated words |", rendered)

        self.ok("kr", "withdraw", "O4-KR2", "--reason", "dropped from v4")
        got = self.overall_kr("O4-KR2")
        self.assertEqual((got["status"], got["withdrawn_reason"]),
                         ("withdrawn", "dropped from v4"))
        rendered = self.goals("krs", "--level", "overall").stdout
        self.assertIn(f"| O4-KR2 | restated words — withdrawn "
                      f"{got['withdrawn_at'][:10]}: dropped from v4 |",
                      rendered)
        self.assertEqual(self.okr_md.read_bytes(), okr_md)
        self.assertGateHolds()
        self.assertTrue(self.okr.read_bytes().startswith(store),
                        "an overall write rewrote an existing line")

        self.assertRefused(["measure", "O4-KR2", "--check", "len", "--value",
                            "1", "--evidence", "evidence/2026-09/m.md"],
                           "withdrawn", "perry-goals kr add")
        self.assertRefused(["check", "O4-KR2", "--id", "x", "--direction",
                            "done", "--target", "1", "--label", "x"],
                           "withdrawn", "perry-goals kr add")


class TestRefusals(Project):
    """Every refusal in § 5.7, each writing nothing and naming the way on."""

    def withdraw_p004(self):
        self.ok("kr", "withdraw", "P004-O1-KR1", "--reason", "gone")

    # ── add ──
    def test_add_an_id_that_exists(self):
        self.assertRefused(["kr", "add", "P004-O1-KR1", "--objective", "O1",
                            "--text", "x", "--reason", "r"],
                           "already exists", "never reused",
                           "perry-goals kr restate P004-O1-KR1")

    def test_add_reusing_a_withdrawn_id(self):
        self.withdraw_p004()
        said = self.assertRefused(["kr", "add", "P004-O1-KR1", "--objective",
                                   "O1", "--text", "x", "--reason", "r"],
                                  "is withdrawn", "never reused",
                                  "perry-goals krs")
        self.assertNotIn("kr restate", said)

    def test_add_reusing_a_withdrawn_overall_id(self):
        self.ok("kr", "withdraw", "O4-KR1", "--reason", "gone")
        self.assertRefused(["kr", "add", "O4-KR1", "--okr-version", V4,
                            "--objective", "O-14", "--text", "x",
                            "--reason", "r"], "is withdrawn", "never reused")

    def test_add_beyond_the_cap_counts_active_krs_only(self):
        for n in (2, 3):
            self.ok("kr", "add", f"P004-O1-KR{n}", "--objective", "O1",
                    "--text", "x", "--reason", "r")
        # P004-O1-KR1, O2-KR1, KR2, KR3: four active under O1.
        self.assertRefused(["kr", "add", "P004-O1-KR4", "--objective", "O1",
                            "--text", "x", "--reason", "r"],
                           "cap of 4", "perry-goals kr withdraw")
        self.withdraw_p004()
        self.ok("kr", "add", "P004-O1-KR4", "--objective", "O1", "--text", "x",
                "--reason", "a withdrawn KR frees its slot")

    def test_add_without_saying_its_level(self):
        self.assertRefused(["kr", "add", "O2-KR9", "--objective", "O1",
                            "--text", "x", "--reason", "r"],
                           '--okr-version ""')

    def test_add_to_a_scored_phase(self):
        (self.root / "phase" / "CURRENT").write_text("002-old\n")
        self.assertRefused(["kr", "add", "P002-O1-KR2", "--objective", "O1",
                            "--text", "x", "--reason", "r"],
                           "history is not revised", "perry-goals krs")

    def test_add_to_a_version_that_is_not_current(self):
        self.assertRefused(["kr", "add", "O9-KR1", "--okr-version", V3,
                            "--objective", "O-1", "--text", "x",
                            "--reason", "r"],
                           "not the current", f'--okr-version "{V4}"')

    def test_add_under_an_objective_the_phase_does_not_have(self):
        self.assertRefused(["kr", "add", "P004-O7-KR1", "--objective", "O7",
                            "--text", "x", "--reason", "r"],
                           "not an objective of phase", "perry-goals krs")

    def test_add_an_id_naming_another_phase(self):
        self.assertRefused(["kr", "add", "P003-O1-KR9", "--objective", "O1",
                            "--text", "x", "--reason", "r"],
                           "names phase 003", "P004-")

    def test_add_without_a_reason(self):
        self.assertRefused(["kr", "add", "P004-O1-KR2", "--objective", "O1",
                            "--text", "x"], "--reason", "perry-goals kr add")

    def test_add_setting_an_identity_field(self):
        self.assertRefused(["kr", "add", "P004-O1-KR2", "--objective", "O1",
                            "--text", "x", "--set", "phase=003-computed",
                            "--reason", "r"], "identity field")

    # ── restate ──
    def test_restate_an_identity_field_at_either_level(self):
        for argv in (["P004-O1-KR1", "--set", "id=P004-O1-KR9"],
                     ["P004-O1-KR1", "--set", "objective=O2"],
                     ["P004-O1-KR1", "--set", "phase=003-computed"],
                     ["O4-KR1", "--set", "version=v3: 2026-09-01"],
                     ["O4-KR1", "--set", "objective_id=O-11"],
                     ["O4-KR1", "--set", "order=9"]):
            with self.subTest(argv=argv):
                self.assertRefused(["kr", "restate", *argv, "--reason", "r"],
                                   "identity field", "perry-goals kr withdraw")

    def test_restate_that_names_no_field(self):
        self.assertRefused(["kr", "restate", "P004-O1-KR1", "--reason", "r"],
                           "names no field",
                           "perry-goals kr restate P004-O1-KR1 --set")

    def test_restate_that_changes_nothing(self):
        self.assertRefused(["kr", "restate", "P004-O1-KR1", "--set",
                            "title=P004-O1-KR1 title", "--reason", "r"],
                           "changes nothing", "perry-goals krs")

    def test_restate_an_unknown_or_mistyped_field(self):
        self.assertRefused(["kr", "restate", "P004-O1-KR1", "--set",
                            "colour=red", "--reason", "r"], "has no field")
        self.assertRefused(["kr", "restate", "P004-O1-KR1", "--set",
                            "target=many", "--reason", "r"],
                           "takes a number")

    def test_restate_a_withdrawn_kr(self):
        self.withdraw_p004()
        self.assertRefused(["kr", "restate", "P004-O1-KR1", "--set",
                            "title=x", "--reason", "r"],
                           "withdrawn", "terminal", "perry-goals kr add")

    def test_restate_without_a_reason(self):
        self.assertRefused(["kr", "restate", "P004-O1-KR1", "--set",
                            "title=x"], "--reason",
                           "perry-goals kr restate P004-O1-KR1")

    def test_restate_in_a_scored_phase(self):
        self.assertRefused(["kr", "restate", "P002-O1-KR1", "--set",
                            "title=x", "--reason", "r"],
                           "history is not revised", "perry-goals krs")

    def test_restate_in_a_version_that_is_not_current(self):
        self.assertRefused(["kr", "restate", "O3-KR1", "--set", "text=x",
                            "--reason", "r"],
                           "history is not revised",
                           "perry-goals krs --level overall")

    def test_restate_an_id_that_resolves_to_nothing(self):
        self.assertRefused(["kr", "restate", "P004-O9-KR9", "--set",
                            "title=x", "--reason", "r"],
                           "resolves to no KR", "perry-goals krs")

    def test_restate_a_bare_overall_id_two_versions_carry(self):
        self.assertRefused(["kr", "restate", "O1-KR1", "--set", "text=x",
                            "--reason", "r"],
                           "names 2 KRs", f'--okr-version "{V4}"')

    # ── withdraw ──
    def test_withdraw_twice(self):
        self.withdraw_p004()
        self.assertRefused(["kr", "withdraw", "P004-O1-KR1", "--reason", "r"],
                           "terminal", "perry-goals kr add")

    def test_withdraw_without_a_reason(self):
        self.assertRefused(["kr", "withdraw", "P004-O1-KR1"], "--reason",
                           "perry-goals kr withdraw P004-O1-KR1")

    def test_withdraw_in_a_scored_phase_or_past_version(self):
        self.assertRefused(["kr", "withdraw", "P002-O1-KR1", "--reason", "r"],
                           "history is not revised")
        self.assertRefused(["kr", "withdraw", "O1-KR1", "--okr-version", V3,
                            "--reason", "r"], "history is not revised")

    def test_withdraw_an_id_that_resolves_to_nothing(self):
        self.assertRefused(["kr", "withdraw", "P004-O9-KR9", "--reason", "r"],
                           "resolves to no KR")

    def test_check_on_a_withdrawn_kr(self):
        self.withdraw_p004()
        self.assertRefused(["check", "P004-O1-KR1", "--id", "x", "--direction",
                            "done", "--target", "1", "--label", "x"],
                           "withdrawn", "perry-goals kr add")

    # ── the surface ──
    def test_a_flag_the_op_does_not_take_is_exit_2(self):
        for argv in (["kr", "withdraw", "P004-O1-KR1", "--set", "title=x",
                      "--reason", "r"],
                     ["kr", "restate", "P004-O1-KR1", "--objective", "O1",
                      "--set", "title=x", "--reason", "r"],
                     ["kr", "add", "P004-O1-KR2", "--objective", "O1",
                      "--text", "x", "--reason", "r", "--check", "c"]):
            with self.subTest(argv=argv):
                self.assertRefused(argv, "does not take", code=2)

    def test_an_op_that_is_not_one_of_the_three(self):
        self.assertRefused(["kr", "rename", "P004-O1-KR1", "--reason", "r"],
                           "add | restate | withdraw")

    def test_dry_run_writes_nothing(self):
        for argv in (["kr", "add", "P004-O1-KR2", "--objective", "O1",
                      "--text", "x", "--reason", "r"],
                     ["kr", "restate", "P004-O1-KR1", "--set", "title=x",
                      "--reason", "r"],
                     ["kr", "withdraw", "O4-KR1", "--reason", "r"]):
            with self.subTest(argv=argv):
                before = self.snapshot()
                got = self.ok(*argv, "--dry-run")
                self.assertEqual((got["written"], got["dry_run"]),
                                 (False, True))
                self.assertEqual(before, self.snapshot())

    # ── the OKR.md gate ──
    def test_an_okr_md_that_still_carries_kr_rows_is_refused(self):
        """Those rows render from the UNFOLDED record: a restate would leave
        `OKR.md` saying the old words. Refused rather than written."""
        text = self.okr_md.read_text()
        self.okr_md.write_text(text + "\n| Id | KR | Metric / Target | "
                               "Stretch? | Deadline |\n|---|---|---|---|---|\n"
                               "| O1-KR1 | O1-KR1 in v4: 2026-09-15 | m | no | "
                               "2026-10-15 |\n")
        self.assertRefused(["kr", "restate", "O4-KR1", "--set", "text=x",
                            "--reason", "r"],
                           "still carries 1 KR row", "TASK-236",
                           "perry-okr diff")

    def test_a_store_the_file_already_disagrees_with_is_refused(self):
        self.with_commitments()
        got = self.goals("commit", "--track", "main", "--promise", "p",
                         "--to", "u", "--due", "2026-12-01", "--actor", "t")
        self.assertEqual(got.returncode, 0, got.stdout + got.stderr)
        rows = self.lines(self.okr)
        for r in rows:
            if r.get("kind") == "commitment":
                r["promise"] = "a different promise, in the store only"
        self.okr.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                    for r in rows))
        self.assertRefused(["kr", "withdraw", "O4-KR1", "--reason", "r"],
                           "byte for byte", "perry-okr diff")


class TestReaders(Project):
    """Every reader reads the fold: list, state, lint, and `commit`."""

    def test_perry_goals_list_publishes_status_and_the_folded_values(self):
        self.with_phase_objective()
        self.ok("kr", "restate", "P004-O1-KR1", "--set", "title=new words",
                "--reason", "r")
        self.ok("kr", "withdraw", "O4-KR1", "--reason", "gone")
        got = self.ok("list")
        self.assertEqual(got["contract"], "perry-goals/list/3.6")
        rows = {(k["level"], k["id"]): k for k in got["krs"]}
        phase = rows[("phase", "P004-O1-KR1")]
        self.assertEqual((phase["title"], phase["status"]),
                         ("new words", "active"))
        self.assertEqual(phase["revisions"][0]["changes"][0]["before"],
                         "P004-O1-KR1 title")
        self.assertTrue(all(set(k) >= {"status", "revisions", "withdrawn_at",
                                       "withdrawn_reason"}
                            for k in got["krs"]))

    def test_the_overall_list_row_folds_its_own_store(self):
        # OKR.md's v4 block carries Objective 1 only, so O1-KR1 is the row.
        self.ok("kr", "restate", "O1-KR1", "--okr-version", V4, "--set",
                "text=v4 words, restated", "--reason", "r")
        rows = [k for k in self.ok("list")["krs"] if k["level"] == "overall"]
        self.assertEqual([(k["id"], k["title"], len(k["revisions"]))
                          for k in rows],
                         [("O1-KR1", "v4 words, restated", 1)])

    def test_perry_state_carries_status_on_every_linkage_kr(self):
        self.withdraw_p004 = lambda: self.ok(
            "kr", "withdraw", "P004-O1-KR1", "--reason", "gone")
        self.withdraw_p004()
        payload = self.state()
        krs = {k["id"]: k for o in payload["linkage"]["objectives"]
               for k in o["krs"]}
        self.assertEqual(krs["P004-O1-KR1"]["status"], "withdrawn")
        self.assertEqual(krs["O2-KR1"]["status"], "active")

    def test_perry_lint_names_a_hand_appended_revision_the_fold_skips(self):
        self.ok("kr", "withdraw", "P004-O1-KR1", "--reason", "gone")
        with open(self.linkage, "a") as fh:
            fh.write(json.dumps(revision(
                "P004-O1-KR1", fields={"title": "after"},
                revised_at="2099-01-01T00:00:00Z")) + "\n")
        with open(self.okr, "a") as fh:
            fh.write(json.dumps(revision(
                "O4-KR1", okr_version=V4, fields={"objective_id": "O-11"})) + "\n")
        got = inproc.run("perry-lint", ["--root", str(self.root)],
                         env={"PERRY_PROJECT": None})
        said = got.stdout + got.stderr
        self.assertIn("kr-revision-malformed", said)
        self.assertIn("after the KR was withdrawn", said)
        self.assertIn("identity field(s) objective_id", said)
        self.assertEqual(self.phase_kr("P004-O1-KR1")["text"],
                         "P004-O1-KR1 title")

    def test_commit_carries_a_revision_through_the_okr_md_gate(self):
        """`write_okr_and_store` rewrites the store from `OKR.md` plus what
        it keeps; a `kr_revision` is a store-only kind and is kept, line for
        line, and the KR still reads folded."""
        self.with_commitments()
        self.ok("kr", "restate", "O4-KR1", "--set", "text=restated",
                "--reason", "r")
        line = self.okr.read_text().splitlines()[-1]
        got = self.goals("commit", "--track", "main", "--promise", "p",
                         "--to", "u", "--due", "2026-12-01", "--actor", "t")
        self.assertEqual(got.returncode, 0, got.stdout + got.stderr)
        self.assertIn(line, self.okr.read_text().splitlines())
        self.assertEqual(self.overall_kr("O4-KR1")["text"], "restated")


if __name__ == "__main__":
    unittest.main()
