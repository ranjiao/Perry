"""TASK-264 — `perry-goals measure` and `perry-goals check` (DESIGN-022 § 5.3).

`TASK-416` declared the `check` and `measurement` record kinds on
`linkage.jsonl`, stated their two ordering rules in `bin/lib § kr_checks` and
derived a KR's position in `§ kr_position`. Nothing wrote either kind. This
module holds the writer to the spec's Verification section:

- § 3, **end to end on a copy of a project**: `check` declares `decrease
  1702 → 400` on a phase KR, and three `measure` calls move `perry-goals krs
  --json` through `fraction 0.0`, `0.5` and `met: true`
  (`TestEndToEnd`).
- § 4, **every refusal** in the spec's § 1 and § 2 asserts the exit code,
  that neither `linkage.jsonl` nor `.perry/events.jsonl` changed by a byte,
  and that the message names what to run next (`TestMeasureRefuses`,
  `TestCheckRefuses`).
- § 5, the five mutations are each red on a test named in
  `perry/evidence/2026-09/TASK-264-result.md`.

Every write goes to a project built under a temporary root (NN-5); nothing
here reads or writes this repository's own `perry/`.

Run: python3 tests/parallel test_goals_kr_writer
"""

from __future__ import annotations

COVERS = (
    "bin/perry-goals",
    "bin/lib/",
    "viewer/parsers.py",
    "bin/perry_md_store.py",
    "schema/state-schema.json",
)

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "bin"))
import inproc  # noqa: E402
import lib  # noqa: E402

V3 = "v3: 2026-09-01"
V4 = "v4: 2026-09-15"


def _phase_doc(number: str, slug: str, status: str) -> str:
    return (f"# Phase #{number} — {slug}\n\n"
            f"> **Owner**: `okr` skill (only writer).\n"
            f"> **Started**: 2026-09-01\n"
            f"> **Status**: {status}\n\n"
            f"## Phase Focus\n\nA fixture phase.\n")


def _kr(phase: str, objective: str, kid: str) -> dict:
    return {"kind": "kr", "phase": phase, "objective": objective, "id": kid,
            "title": f"{kid} title", "metric": "prose", "stretch": False}


def _okr_objective(version: str, oid: str, n: int) -> dict:
    return {"kind": "objective", "id": oid, "version": version,
            "title": f"Objective {n}",
            "heading": f"Objective {n} — Objective {n}", "order": n}


def _okr_kr(version: str, oid: str, n: int, kid: str, order: int) -> dict:
    return {"kind": "kr", "version": version,
            "objective": f"Objective {n} — Objective {n}", "objective_id": oid,
            "id": kid, "text": f"{kid} in {version}", "metric": "m",
            "stretch": "no", "deadline": "2026-10-15", "linked": "",
            "qualifier": "", "form": "table", "order": order}


def make_project(root: Path) -> Path:
    """A Perry project with every case the writer resolves or refuses.

    - phase `004-now` is current and active; `P004-O1-KR1` is the spec's
      end-to-end KR, and `O2-KR1` is ALSO an overall id in v4, so a bare
      `O2-KR1` names two KRs;
    - phase `003-computed` is active and holds `P003-O3-KR2`, the one KR in
      `lib.COMPUTED_KR_METRICS`;
    - phase `002-old` is scored;
    - `okr.jsonl` carries `O1-KR1` in v3 AND v4, `O3-KR1` in v3 only (a past
      version) and `O4-KR1` in v4 only; `OKR.md`'s latest heading is v4.
    """
    root.mkdir(parents=True, exist_ok=True)
    (root / ".perry").mkdir()
    (root / "phase").mkdir()
    (root / "phase" / "CURRENT").write_text("004-now\n")
    (root / "phase" / "004-now.md").write_text(_phase_doc("004", "now", "active"))
    (root / "phase" / "003-computed.md").write_text(
        _phase_doc("003", "computed", "active"))
    (root / "phase" / "002-old.md").write_text(_phase_doc("002", "old", "scored"))
    linkage = [
        {"kind": "objective", "phase": "002-old", "id": "O1", "title": "old"},
        _kr("002-old", "O1", "P002-O1-KR1"),
        {"kind": "objective", "phase": "003-computed", "id": "O3",
         "title": "computed"},
        _kr("003-computed", "O3", "P003-O3-KR2"),
        {"kind": "objective", "phase": "004-now", "id": "O1", "title": "now"},
        _kr("004-now", "O1", "P004-O1-KR1"),
        _kr("004-now", "O1", "O2-KR1"),
    ]
    (root / "linkage.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in linkage))
    okr = [
        _okr_objective(V3, "O-1", 1), _okr_objective(V3, "O-3", 3),
        _okr_kr(V3, "O-1", 1, "O1-KR1", 0), _okr_kr(V3, "O-3", 3, "O3-KR1", 1),
        _okr_objective(V4, "O-11", 1), _okr_objective(V4, "O-12", 2),
        _okr_objective(V4, "O-14", 4),
        _okr_kr(V4, "O-11", 1, "O1-KR1", 0), _okr_kr(V4, "O-12", 2, "O2-KR1", 1),
        _okr_kr(V4, "O-14", 4, "O4-KR1", 2),
    ]
    (root / "okr.jsonl").write_text("".join(json.dumps(r) + "\n" for r in okr))
    (root / "OKR.md").write_text(
        "# OKR — fixture\n\n## Mission\n\nA fixture.\n\n"
        f"## {V3}\n\n### Objective 1 — Objective 1\n\n"
        f"## {V4}\n\n### Objective 1 — Objective 1\n")
    (root / "evidence" / "2026-09").mkdir(parents=True)
    (root / "evidence" / "2026-09" / "m.md").write_text("measured\n")
    return root


class Project(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="goals-kr-writer-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = make_project(self.tmp / "p")
        self.store = self.root / "linkage.jsonl"
        self.events = self.root / ".perry" / "events.jsonl"

    #: The actor every `check` / `measure` call below passes unless it passes
    #: its own. `--actor` is REQUIRED on both (USER-950); `TestActorIsRequired`
    #: calls with `bare=True`, which adds nothing.
    ACTOR = "pmo"

    def goals(self, *argv, bare=False):
        # `--root` names the project, and `$PERRY_PROJECT` is unset for the
        # call so a caller's environment cannot point the write elsewhere.
        argv = list(argv)
        if (not bare and argv and argv[0] in ("check", "measure")
                and "--actor" not in argv):
            argv += ["--actor", self.ACTOR]
        return inproc.run("perry-goals", [*argv, "--root", str(self.root)],
                          env={"PERRY_PROJECT": None})

    def ok(self, *argv) -> dict:
        got = self.goals(*argv, "--json")
        self.assertEqual(got.returncode, 0, got.stdout + got.stderr)
        return json.loads(got.stdout)

    def records(self, kind: str) -> list[dict]:
        return [json.loads(line) for line in self.store.read_text().splitlines()
                if line.strip() and json.loads(line).get("kind") == kind]

    def logged(self) -> list[dict]:
        if not self.events.exists():
            return []
        return [json.loads(line) for line in self.events.read_text().splitlines()
                if line.strip()]

    def declare(self, kr="P004-O1-KR1", cid="p90", *extra,
                direction="decrease", target="400", baseline="1702"):
        argv = ["check", kr, "--id", cid, "--direction", direction,
                "--target", target, "--label", "p90 length", *extra]
        if baseline is not None:
            argv += ["--baseline", baseline]
        return self.ok(*argv)

    def measure(self, value, kr="P004-O1-KR1", cid="p90", *extra,
                evidence="evidence/2026-09/m.md"):
        return self.ok("measure", kr, "--check", cid, "--value", str(value),
                       "--evidence", evidence, *extra)

    def phase_kr(self, kid="P004-O1-KR1") -> dict:
        krs = [k for o in self.ok("krs")["objectives"] for k in o["krs"]]
        return next(k for k in krs if k["id"] == kid)

    def assertRefused(self, argv, *recovery, code=1, bare=False):
        """Exit `code`, not one byte of either file moved, and the message
        names each `recovery` fragment."""
        before = (self.store.read_bytes(),
                  self.events.read_bytes() if self.events.exists() else None)
        got = self.goals(*argv, bare=bare)
        after = (self.store.read_bytes(),
                 self.events.read_bytes() if self.events.exists() else None)
        self.assertEqual(got.returncode, code, got.stdout + got.stderr)
        self.assertEqual(before, after, "a refusal wrote")
        said = got.stdout + got.stderr
        for fragment in recovery:
            self.assertIn(fragment, said)
        if code == 1 or bare:
            self.assertIn("Nothing was written", said)
        return said


class TestEndToEnd(Project):
    """Verification § 3: `decrease 1702 → 400`, measured at 1702, 1051, 400."""

    def test_check_then_three_measurements(self):
        self.declare()
        self.assertEqual(self.phase_kr()["state"], "unmeasured")

        self.measure(1702)
        kr = self.phase_kr()
        self.assertEqual((kr["state"], kr["met"], kr["fraction"]),
                         ("measured", False, 0.0))

        self.measure(1051)
        kr = self.phase_kr()
        self.assertEqual((kr["state"], kr["met"], kr["fraction"]),
                         ("measured", False, 0.5))

        self.measure(400)
        kr = self.phase_kr()
        self.assertEqual((kr["state"], kr["met"], kr["fraction"]),
                         ("measured", True, 1.0))
        self.assertEqual(kr["checks"][0]["measurement"]["value"], 400)


class TestMeasureWrites(Project):
    def setUp(self):
        super().setUp()
        self.declare()

    def test_one_record_of_the_declared_shape(self):
        got = self.measure(1702, "P004-O1-KR1", "p90", "--actor", "goals")
        [rec] = self.records("measurement")
        self.assertEqual(set(rec), {"kind", "kr", "okr_version", "check",
                                    "value", "asserted_at", "evidence",
                                    "computed", "actor"})
        self.assertEqual(
            {k: rec[k] for k in rec if k != "asserted_at"},
            {"kind": "measurement", "kr": "P004-O1-KR1", "okr_version": "",
             "check": "p90", "value": 1702,
             "evidence": "evidence/2026-09/m.md", "computed": False,
             "actor": "goals"})
        self.assertIsNotNone(lib.ts_moment(rec["asserted_at"]))
        self.assertTrue(rec["asserted_at"].endswith("Z"))
        self.assertEqual(got["record"], rec)

    def test_the_measure_event_is_appended_with_the_record(self):
        """Mutation 2 — the record written without the event — is red here."""
        self.measure(1051)
        events = [e for e in self.logged() if e.get("event") == "measure"]
        self.assertEqual(len(events), 1, "the persisted measurement needs its event")
        [event] = events
        self.assertEqual(
            {k: event.get(k) for k in ("actor", "file", "kr", "okr_version",
                                       "check", "value", "evidence")},
            {"actor": "pmo", "file": "linkage.jsonl", "kr": "P004-O1-KR1",
             "okr_version": "", "check": "p90", "value": 1051,
             "evidence": "evidence/2026-09/m.md"})
        self.assertIsNotNone(lib.ts_moment(event["ts"]))

    def test_the_prior_bytes_are_kept_and_one_line_is_added(self):
        before = self.store.read_bytes()
        self.measure(1702)
        after = self.store.read_bytes()
        self.assertTrue(after.startswith(before))
        self.assertEqual(after[len(before):].count(b"\n"), 1)

    def test_dry_run_writes_nothing_and_says_what_it_would(self):
        before = (self.store.read_bytes(), self.events.read_bytes())
        got = self.measure(1702, "P004-O1-KR1", "p90", "--dry-run")
        self.assertEqual((self.store.read_bytes(), self.events.read_bytes()),
                         before)
        self.assertEqual((got["written"], got["dry_run"]), (False, True))
        self.assertEqual(got["record"]["value"], 1702)
        self.assertTrue(got["diff"][0].startswith("+linkage.jsonl"))

    def test_an_absolute_evidence_path_inside_the_project_is_stored_relative(self):
        self.measure(3, evidence=str(self.root / "evidence/2026-09/m.md"))
        self.assertEqual(self.records("measurement")[0]["evidence"],
                         "evidence/2026-09/m.md")

    def test_an_overall_kr_is_measured_under_its_full_version_label(self):
        self.ok("check", "O1-KR1", "--okr-version", V4, "--id", "done",
                "--direction", "done", "--target", "1", "--label", "shipped")
        self.ok("measure", "O1-KR1", "--okr-version", V4, "--check", "done",
                "--value", "1", "--evidence", "evidence/2026-09/m.md")
        [rec] = self.records("measurement")
        self.assertEqual((rec["kr"], rec["okr_version"]), ("O1-KR1", V4))
        entries = lib.kr_checks(self.records("check") + [rec])[("O1-KR1", V4)]
        self.assertTrue(lib.kr_position(entries)["met"])

    def test_the_store_current_version_is_writable_despite_projection_drift(self):
        self.declare("O4-KR1", "n", direction="at_most", target="0",
                     baseline=None)
        for projection in (f"# OKR\n\n## {V3}\n", "# OKR\n\n## v5: 2026-10-01\n", None):
            with self.subTest(projection=projection):
                doc = self.root / "OKR.md"
                if projection is None:
                    doc.unlink()
                else:
                    doc.write_text(projection)
                current = self.ok("krs", "--level", "overall")["versions"]
                self.assertEqual(current[0]["version"], V4)
                got = self.measure(0, "O4-KR1", "n")
                self.assertEqual(got["record"]["okr_version"], V4)

    def test_a_unique_overall_id_needs_no_version(self):
        self.ok("check", "O4-KR1", "--id", "n", "--direction", "at_most",
                "--target", "0", "--label", "issues")
        [rec] = [r for r in self.records("check") if r["kr"] == "O4-KR1"]
        self.assertEqual(rec["okr_version"], V4)


class TestDerivedEventFailure(Project):
    def test_an_event_failure_reports_the_persisted_record_without_a_journal(self):
        self.declare()
        self.events.unlink()
        self.events.mkdir()  # portable append failure, including privileged users
        for command in ("check", "measure"):
            for json_mode in (False, True):
                with self.subTest(command=command, json_mode=json_mode):
                    args = (["check", "P004-O1-KR1", "--id", "p90",
                             "--direction", "decrease", "--baseline", "1702",
                             "--target", "400", "--label", "p90 length"]
                            if command == "check" else
                            ["measure", "P004-O1-KR1", "--check", "p90",
                             "--value", "1051", "--evidence", "evidence/2026-09/m.md"])
                    if json_mode:
                        args.append("--json")
                    before = self.store.read_bytes()
                    got = self.goals(*args)
                    self.assertEqual(got.returncode, 0, got.stderr)
                    self.assertTrue(self.store.read_bytes().startswith(before))
                    self.assertEqual(self.store.read_bytes()[len(before):].count(b"\n"), 1)
                    self.assertIn("linkage.jsonl was written", got.stderr)
                    self.assertIn("event could not be appended", got.stderr)
                    self.assertNotIn("Nothing was written", got.stderr)
                    if json_mode:
                        result = json.loads(got.stdout)
                        self.assertTrue(result["written"])
                        self.assertFalse(result["event_written"])
                    else:
                        self.assertIn("record was written and the event was not", got.stderr)
                    self.assertFalse((self.root / "journal").exists())


class TestMeasureRefuses(Project):
    """Spec § 1's five refusals, and the typed values around them."""

    def setUp(self):
        super().setUp()
        self.declare()

    def test_an_undeclared_check(self):
        self.assertRefused(
            ["measure", "P004-O1-KR1", "--check", "median", "--value", "3",
             "--evidence", "evidence/2026-09/m.md"],
            "no check 'median'", "perry-goals check P004-O1-KR1 --id median")

    def test_a_computed_kr(self):
        """Mutation 1 — `measure` accepting a KR in `COMPUTED_KR_METRICS` — is
        red here: the check is declared, so only this refusal stands between
        the call and a write."""
        self.assertIn("P003-O3-KR2", lib.COMPUTED_KR_METRICS)
        self.declare("P003-O3-KR2", "share", direction="at_least",
                     target="80", baseline=None)
        self.assertRefused(
            ["measure", "P003-O3-KR2", "--check", "share", "--value", "31",
             "--evidence", "evidence/2026-09/m.md"],
            "COMPUTED_KR_METRICS", "never typed", "perry-goals krs")

    def test_a_missing_evidence_path(self):
        """Mutation 4 — accepting a missing evidence path — is red here."""
        self.assertRefused(
            ["measure", "P004-O1-KR1", "--check", "p90", "--value", "3",
             "--evidence", "evidence/2026-09/absent.md"],
            "does not exist under the project", "write the evidence first")

    def test_an_evidence_file_outside_the_project(self):
        outside = self.tmp / "outside.md"
        outside.write_text("x\n")
        self.assertRefused(
            ["measure", "P004-O1-KR1", "--check", "p90", "--value", "3",
             "--evidence", str(outside)],
            "does not exist under the project")

    def test_a_directory_is_not_evidence(self):
        self.assertRefused(
            ["measure", "P004-O1-KR1", "--check", "p90", "--value", "3",
             "--evidence", "evidence/2026-09"],
            "does not exist under the project")

    def test_a_scored_phase(self):
        self.declare("P002-O1-KR1", "n", direction="at_most", target="0",
                     baseline=None)
        self.assertRefused(
            ["measure", "P002-O1-KR1", "--check", "n", "--value", "0",
             "--evidence", "evidence/2026-09/m.md"],
            "which is scored", "perry-goals krs")

    def test_an_okr_version_that_is_not_current(self):
        self.ok("check", "O3-KR1", "--id", "n", "--direction", "at_most",
                "--target", "0", "--label", "old")
        self.assertRefused(
            ["measure", "O3-KR1", "--check", "n", "--value", "0",
             "--evidence", "evidence/2026-09/m.md"],
            f"'{V3}' is not the current one", V4,
            "perry-goals krs --level overall")

    def test_a_lagging_projection_cannot_reopen_a_past_store_version(self):
        self.ok("check", "O3-KR1", "--id", "n", "--direction", "at_most",
                "--target", "0", "--label", "old")
        (self.root / "OKR.md").write_text(f"# OKR\n\n## {V3}\n")
        self.assertRefused(
            ["measure", "O3-KR1", "--check", "n", "--value", "0",
             "--evidence", "evidence/2026-09/m.md"],
            f"'{V3}' is not the current one", V4, "okr.jsonl",
            "perry-goals krs --level overall")

    def test_a_bare_overall_id_two_versions_carry(self):
        """Mutation 5 — resolving without `okr_version` when two versions
        carry the id — is red here and on the `check` twin below."""
        self.assertRefused(
            ["measure", "O1-KR1", "--check", "done", "--value", "1",
             "--evidence", "evidence/2026-09/m.md"],
            "names 2 KRs", f'--okr-version "{V3}"', f'--okr-version "{V4}"')

    def test_a_bare_id_a_phase_and_a_version_both_carry(self):
        self.assertRefused(
            ["measure", "O2-KR1", "--check", "n", "--value", "1",
             "--evidence", "evidence/2026-09/m.md"],
            "names 2 KRs", '--okr-version ""', f'--okr-version "{V4}"')

    def test_an_id_that_resolves_to_no_kr(self):
        self.assertRefused(
            ["measure", "P004-O1-KR9", "--check", "p90", "--value", "1",
             "--evidence", "evidence/2026-09/m.md"],
            "resolves to no KR", "perry-goals krs")

    def test_a_version_label_that_is_not_exact(self):
        self.assertRefused(
            ["measure", "O1-KR1", "--okr-version", "v4", "--check", "done",
             "--value", "1", "--evidence", "evidence/2026-09/m.md"],
            "matched exactly", V4)

    def test_a_value_that_is_not_a_number(self):
        for bad in ("many", "nan", "inf", ""):
            with self.subTest(value=bad):
                self.assertRefused(
                    ["measure", "P004-O1-KR1", "--check", "p90", "--value",
                     bad, "--evidence", "evidence/2026-09/m.md"],
                    "--value takes a number")

    def test_a_missing_required_flag(self):
        self.assertRefused(
            ["measure", "P004-O1-KR1", "--value", "3", "--evidence",
             "evidence/2026-09/m.md"],
            "--check is required", "perry-goals measure <KR-ID>")


class TestCheckWrites(Project):
    def test_one_record_of_the_declared_shape(self):
        got = self.declare()
        [rec] = self.records("check")
        self.assertEqual(set(rec), {"kind", "kr", "okr_version", "id", "label",
                                    "direction", "target", "baseline",
                                    "declared_at", "actor"})
        self.assertEqual(
            {k: rec[k] for k in rec if k != "declared_at"},
            {"kind": "check", "kr": "P004-O1-KR1", "okr_version": "",
             "id": "p90", "label": "p90 length", "direction": "decrease",
             "target": 400, "baseline": 1702, "actor": "pmo"})
        self.assertIsNotNone(lib.ts_moment(rec["declared_at"]))
        self.assertIsNone(got["supersedes"])
        [event] = [e for e in self.logged() if e.get("event") == "check"]
        self.assertEqual((event["kr"], event["id"]), ("P004-O1-KR1", "p90"))

    def test_a_limit_is_stored_with_a_null_baseline(self):
        self.declare(direction="at_most", target="1054", baseline=None)
        self.assertIsNone(self.records("check")[0]["baseline"])

    def test_re_declaring_is_allowed_and_the_reader_takes_the_later(self):
        first = self.declare()
        second = self.declare(target="500")
        self.assertEqual(second["supersedes"], first["record"]["declared_at"])
        self.assertEqual(len(self.records("check")), 2)
        self.assertEqual(self.phase_kr()["checks"][0]["target"], 500)

    def test_dry_run_writes_nothing(self):
        before = self.store.read_bytes()
        got = self.declare("P004-O1-KR1", "p90", "--dry-run")
        self.assertEqual(self.store.read_bytes(), before)
        self.assertFalse(self.events.exists())
        self.assertEqual((got["written"], got["record"]["id"]), (False, "p90"))

    def test_a_phase_kr_is_named_explicitly_with_an_empty_version(self):
        self.ok("check", "O2-KR1", "--okr-version", "", "--id", "n",
                "--direction", "done", "--target", "1", "--label", "x")
        self.assertEqual(self.records("check")[0]["okr_version"], "")


class TestCheckRefuses(Project):
    """Spec § 2's refusals."""

    def check(self, *, direction, target, baseline=None, kr="P004-O1-KR1",
              cid="c"):
        argv = ["check", kr, "--id", cid, "--direction", direction,
                "--target", target, "--label", "a check"]
        return argv + (["--baseline", baseline] if baseline is not None else [])

    def test_increase_with_target_not_above_baseline(self):
        for target in ("5", "4"):
            with self.subTest(target=target):
                self.assertRefused(
                    self.check(direction="increase", target=target,
                               baseline="5"),
                    "`increase` needs --target above --baseline",
                    "--direction decrease")

    def test_decrease_with_target_not_below_baseline(self):
        """Mutation 3 — `decrease` accepting `target >= baseline` — is red."""
        for target in ("1702", "2000"):
            with self.subTest(target=target):
                self.assertRefused(
                    self.check(direction="decrease", target=target,
                               baseline="1702"),
                    "`decrease` needs --target below --baseline",
                    "--direction increase")

    def test_increase_or_decrease_without_a_baseline(self):
        for direction in ("increase", "decrease"):
            with self.subTest(direction=direction):
                self.assertRefused(
                    self.check(direction=direction, target="5"),
                    "no --baseline was given", "--baseline <N>")

    def test_done_with_a_target_other_than_one(self):
        for target in ("0", "2", "1.5"):
            with self.subTest(target=target):
                self.assertRefused(self.check(direction="done", target=target),
                                   "targets 1", "--target 1")

    def test_a_baseline_on_a_limit_or_a_milestone(self):
        for direction, target in (("at_least", "80"), ("at_most", "0"),
                                  ("done", "1")):
            with self.subTest(direction=direction):
                self.assertRefused(
                    self.check(direction=direction, target=target,
                               baseline="3"),
                    "takes no --baseline", "Re-run without `--baseline`")

    def test_a_direction_outside_the_five(self):
        self.assertRefused(self.check(direction="sideways", target="1"),
                           "is not one of", "increase · decrease")

    def test_an_id_that_resolves_to_no_kr(self):
        self.assertRefused(self.check(direction="done", target="1",
                                      kr="P009-O1-KR1"),
                           "resolves to no KR", "perry-goals krs")

    def test_a_bare_overall_id_two_versions_carry(self):
        self.assertRefused(self.check(direction="done", target="1",
                                      kr="O1-KR1"),
                           "names 2 KRs", f'--okr-version "{V4}"')

    def test_an_id_that_is_not_a_slug(self):
        self.assertRefused(self.check(direction="done", target="1",
                                      cid="P90 Length"),
                           "is not a check slug", "--id p90-length")

    def test_a_target_that_is_not_a_number(self):
        self.assertRefused(self.check(direction="at_most", target="lots"),
                           "--target takes a number")


class TestActorIsRequired(Project):
    """USER-950 (2026-09-16): every write names who made it. A missing or an
    empty `--actor` is a usage error — exit 2 — and nothing is written."""

    ARGV = {
        "measure": ["measure", "P004-O1-KR1", "--check", "p90", "--value",
                    "3", "--evidence", "evidence/2026-09/m.md"],
        "check": ["check", "P004-O1-KR1", "--id", "p90", "--direction",
                  "done", "--target", "1", "--label", "x"],
    }

    def setUp(self):
        super().setUp()
        self.declare()

    def test_a_missing_actor_is_refused(self):
        for verb, argv in self.ARGV.items():
            with self.subTest(verb=verb):
                self.assertRefused(argv, f"'{verb}' writes",
                                   "was not given", code=2, bare=True)

    def test_an_empty_actor_is_refused(self):
        for verb, argv in self.ARGV.items():
            for empty in ("", "   "):
                with self.subTest(verb=verb, actor=empty):
                    self.assertRefused([*argv, "--actor", empty],
                                       f"'{verb}' writes",
                                       "was given empty", code=2, bare=True)

    def test_the_given_actor_is_on_the_record_and_the_event(self):
        self.goals(*self.ARGV["measure"], "--actor", "user:ran")
        [rec] = self.records("measurement")
        [event] = [e for e in self.logged() if e["event"] == "measure"]
        self.assertEqual((rec["actor"], event["actor"]),
                         ("user:ran", "user:ran"))


class TestTheSurface(Project):
    """`bin/ARCHITECTURE.md § NN-B2` for the flags this row adds."""

    def test_a_flag_the_writer_does_not_take_is_exit_2(self):
        self.assertRefused(["measure", "P004-O1-KR1", "--id", "x"],
                           "does not take --id", code=2)
        self.assertRefused(["check", "P004-O1-KR1", "--evidence", "x"],
                           "does not take --evidence", code=2)

    def test_the_writers_flags_are_refused_elsewhere(self):
        self.assertRefused(["krs", "--value", "3"], "does not take --value",
                           code=2)

    def test_an_uninstalled_directory_is_refused(self):
        shutil.rmtree(self.root / ".perry")
        self.assertRefused(
            ["measure", "P004-O1-KR1", "--check", "p90", "--value", "3",
             "--evidence", "evidence/2026-09/m.md"],
            "not an installed Perry project")


if __name__ == "__main__":
    unittest.main()
