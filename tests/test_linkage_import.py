"""The linkage register imports into `linkage.jsonl` losing nothing — TASK-277.

DESIGN-015 implementation row **B**. Row A (TASK-276) declared the store's
path in `§ claims` and its three record shapes in `§ stores.declared`; this
row is the one-time import that fills it, and row C then moves the six readers
§ 5.6 names onto it.

**The acceptance is a count, and a count is the weakest thing this module
asserts.** TASK-277's spec sets the bar at *"a count that differs is a
failure, not a rounding"* — but two integers agreeing is satisfied by a store
that dropped `TASK-203`'s edge and invented one for `TASK-999`. So every
count test here is set equality in BOTH directions across all three kinds:
nothing the register holds is missing from the store, nothing in the store
traces to nothing in the register. The count then falls out of the accounting
instead of standing in for it.

**Nothing in this module hardcodes 121, or 93.** The spec's own baseline —
`7 kr + 11 edge + 75 unlinked = 93`, measured 2026-09-02 on `d49964e` — was
already stale when this row ran: 6 + 15 + 100 = 121 on 2026-09-04, because
`P003-O2-KR2` was withdrawn (taking `TASK-099` and `TASK-050`'s edges with
it), `TASK-283` was linked, and DESIGN-015 wrote five rows of its own into the
register it is importing. A test pinning either number would have gone red on
a register that moved legitimately, and DESIGN-015 § 9 spends a whole
`## Changes` entry on precisely that trap — three sites still saying "five"
after the count became six, one of them an acceptance criterion. The register
is therefore re-measured at test time, through `parsers.parse_linkage`, which
is a different code path from the import's own raw-frontmatter reader.

**The three fields the register does not carry are where a migration lies.**
`declared_at`, `actor` and `via` are `required` on `edge` and `unlinked`, and
`phase/003-linkage.md` holds none of them — its `unlinked` is a flat array of
task ids. `TestTheStampIsNotFabricated` is the half of this module that
matters most: `via: "add"` is what `P003-O3-KR2` COUNTS, so an import that
stamped `add` would take a KR whose baseline is 0 to 100% without a line of
the behaviour it measures existing.

Run: python3 tests/parallel test_linkage_import
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS = ROOT / "bin" / "perry-tasks"
LINT = ROOT / "bin" / "perry-lint"
SCHEMA = json.loads((ROOT / "schema" / "state-schema.json").read_text())
STORE_KEY = "linkage.jsonl"

sys.path.insert(0, str(ROOT / "viewer"))
import parsers as P  # noqa: E402

import config_store  # noqa: E402


def declared() -> dict:
    return ((SCHEMA.get("stores") or {}).get("declared") or {}).get(STORE_KEY)


#: A register with one of everything the import has to carry, and the three
#: traps it has to survive: a `target: 0` that falsiness would drop, a KR with
#: no `target` and no `current` at all that a default would invent one for,
#: and two KRs under one objective so the edge count is not the KR count.
FIXTURE_REGISTER = """---
linkage: 1
phase: "009-fixture"
updated: "2026-09-01T04:05:06Z"
objectives:
  - id: O1
    title: "The first objective"
    krs:
      - id: P009-O1-KR1
        title: "A KR with a zero target"
        metric: "prose that must NOT reach the store"
        target: 0
        current: 3
        stretch: false
        linked: "O2-KR1"
        tasks: ["TASK-001", "TASK-002"]
      - id: P009-O1-KR2
        title: "A KR with no numbers at all"
        metric: "more prose"
        stretch: true
        tasks: []
  - id: O2
    title: "The second objective"
    krs:
      - id: P009-O2-KR1
        title: "A KR under the second objective"
        target: 12
        stretch: false
        tasks: ["TASK-003"]
unlinked: ["TASK-004", "TASK-005"]
agents: []
projects: []
---

# Phase #009 — fixture

Body prose. Never read by the import.
"""

SETTINGS = {"Document language": "English", "Repo layout": "single",
            "State root": "perry"}


class LinkageFixture(unittest.TestCase):
    """A minimal project carrying a linkage register and a `phase/CURRENT`."""

    def project(self, register: str = FIXTURE_REGISTER,
                current: str = "009-fixture",
                extra_registers: bool = False) -> pathlib.Path:
        root = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        (root / "perry" / "phase").mkdir(parents=True)
        config_store.write_config(root, SETTINGS)
        (root / ".perry" / "events.jsonl").write_text("", encoding="utf-8")
        (root / "perry" / "phase" / "CURRENT").write_text(current,
                                                          encoding="utf-8")
        (root / "perry" / "phase" / "009-linkage.md").write_text(
            register, encoding="utf-8")
        if extra_registers:
            # A previous phase's register, which a glob would have imported
            # and whose edges name KRs phase 009 does not have.
            (root / "perry" / "phase" / "008-linkage.md").write_text(
                register.replace("009", "008").replace("P008-", "P008-"),
                encoding="utf-8")
        return root

    def run_tasks(self, root: pathlib.Path, *args: str):
        return subprocess.run(
            [sys.executable, str(TASKS), *args, "--root", str(root)],
            capture_output=True, text=True, cwd=ROOT)

    def imported(self, root: pathlib.Path) -> list:
        proc = self.run_tasks(root, "linkage-write", "--from-register")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return self.store(root)

    def store(self, root: pathlib.Path) -> list:
        path = root / "perry" / STORE_KEY
        self.assertTrue(path.exists(), "the import wrote no store")
        return [json.loads(l) for l in
                path.read_text(encoding="utf-8").split("\n") if l.strip()]

    def register_facts(self, root: pathlib.Path) -> dict:
        """The register's facts, re-measured through the CANONICAL reader.

        `parsers.parse_linkage` is what `bin/perry-lint:1325` and every
        DESIGN-015 § 5.6 site is built on, and it is a different code path
        from the raw-frontmatter reader the import derives with. Comparing the
        import against itself would assert only that JSON round-trips.
        """
        text = (root / "perry" / "phase" / "009-linkage.md").read_text(
            encoding="utf-8")
        link = P.parse_linkage(text)
        self.assertFalse(link.error, link.error)
        krs = [k for o in link.objectives for k in o.krs]
        return {"kr": sorted(k.id for k in krs),
                "edge": sorted(f"{t}→{k.id}" for k in krs for t in k.tasks),
                "unlinked": sorted(link.unlinked)}

    def store_facts(self, records: list) -> dict:
        return {
            "kr": sorted(r["id"] for r in records if r["kind"] == "kr"),
            "edge": sorted(f"{r['task']}→{r['kr']}" for r in records
                           if r["kind"] == "edge"),
            "unlinked": sorted(r["task"] for r in records
                               if r["kind"] == "unlinked"),
        }


class TestNothingIsDroppedOrInvented(LinkageFixture):
    """The acceptance, as set equality rather than as two integers."""

    def test_every_register_fact_is_in_the_store_and_nothing_else_is(self):
        root = self.project()
        records = self.imported(root)
        self.assertEqual(self.store_facts(records), self.register_facts(root),
                         "the store is not a faithful account of the "
                         "register — see the diff for which kind moved")

    def test_the_count_falls_out_of_the_accounting(self):
        """And is never a hardcoded number. See this module's docstring."""
        root = self.project()
        records = self.imported(root)
        facts = self.register_facts(root)
        self.assertEqual(len(records), sum(len(v) for v in facts.values()))

    def test_one_edge_is_one_record_not_one_array(self):
        """`derived_not_stored.tasks` — a `tasks[]` on the `kr` record would
        be the same fact in two places one line after the store was built to
        stop that."""
        root = self.project()
        records = self.imported(root)
        for rec in records:
            self.assertNotIn("tasks", rec)
        # Three edges from two KRs that carry tasks, and one KR carrying none.
        self.assertEqual(sum(1 for r in records if r["kind"] == "edge"), 3)

    def test_the_metric_prose_does_not_reach_the_store(self):
        """Decision 2: an argument about how a number was reached is what a
        document is for. The fixture's `metric:` says so in words."""
        root = self.project()
        records = self.imported(root)
        blob = json.dumps(records)
        self.assertNotIn("metric", blob)
        self.assertNotIn("must NOT reach the store", blob)

    def test_a_zero_target_survives_and_a_missing_one_is_not_invented(self):
        """`absent is NOT zero`, row A's schema note, in both directions.

        A falsiness test in the derivation drops `P009-O1-KR1`'s real
        `target: 0`; a default invents one for `P009-O1-KR2`, which carries
        neither `target` nor `current`. Both are silent.
        """
        root = self.project()
        by_id = {r["id"]: r for r in self.imported(root) if r["kind"] == "kr"}
        self.assertEqual(by_id["P009-O1-KR1"]["target"], 0)
        self.assertEqual(by_id["P009-O1-KR1"]["current"], 3)
        self.assertNotIn("target", by_id["P009-O1-KR2"])
        self.assertNotIn("current", by_id["P009-O1-KR2"])
        self.assertEqual(by_id["P009-O2-KR1"]["target"], 12)
        self.assertNotIn("current", by_id["P009-O2-KR1"])

    def test_the_objective_is_carried_not_guessed(self):
        root = self.project()
        by_id = {r["id"]: r for r in self.imported(root) if r["kind"] == "kr"}
        self.assertEqual(by_id["P009-O1-KR1"]["objective"], "O1")
        self.assertEqual(by_id["P009-O2-KR1"]["objective"], "O2")

    def test_the_import_is_deterministic(self):
        """Two imports of one register produce the same bytes — the rule
        `perry_store.STORED`'s fixed field order carries for every store."""
        root = self.project()
        self.imported(root)
        first = (root / "perry" / STORE_KEY).read_bytes()
        self.imported(root)
        self.assertEqual((root / "perry" / STORE_KEY).read_bytes(), first)


class TestTheRegisterIsNeverWritten(LinkageFixture):
    """`phase/<NNN>-linkage.md` is byte-unchanged. The spec's hardest line."""

    def test_the_register_is_byte_identical_after_an_import(self):
        root = self.project()
        path = root / "perry" / "phase" / "009-linkage.md"
        before = path.read_bytes()
        self.imported(root)
        self.assertEqual(path.read_bytes(), before,
                         "the import moved the register it was told to read")

    def test_there_is_no_linkage_render_verb(self):
        """The omission is the design, not an unfinished family.

        The other four registers project a `BOARD.md` section and have a
        `-render` verb that writes it back. DESIGN-015 § 5.4 says this
        document is NOT a render of the store — a render would put `target`
        and `current` in a second place, which is the DESIGN-013 § 5.1
        violation the store exists to remove. A `linkage-render --write`
        would be the one command able to break the byte guarantee above.
        """
        root = self.project()
        proc = self.run_tasks(root, "linkage-render")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("linkage-build / linkage-write / linkage-diff",
                      proc.stderr)


class TestTheStampIsNotFabricated(LinkageFixture):
    """`declared_at`, `actor` and `via` — the three fields the register does
    not carry, and therefore the three this import could invent."""

    def test_via_is_link_and_never_add(self):
        """The one that would corrupt a KR.

        `via: "add"` is what `P003-O3-KR2` counts — *rows opened during phase
        003 that take a KR edge or an `unlinked` declaration in the same
        action as `add`*. DESIGN-015 § 1 measured that the historical
        declarations were NOT made at `add`: *"The 44 declarations were not
        made at `add`; they were swept in later."* Stamping `add` here would
        carry that KR from its 0 baseline to 100% without one line of the
        behaviour it measures existing.
        `evidence/2026-09/TASK-276-result.md § 10` flagged exactly this.

        **Row D has since landed, and this test is unaffected — deliberately.**
        When this was written `perry-task add` wrote nothing but journal
        prose, and the sentence saying so has been removed rather than left to
        rot (DESIGN-015 § 9's own `## Changes` trap: three sites still saying
        "five" after the count became six). `add --kr` now writes a real
        `via: "add"` edge, so `via: "add"` is no longer impossible in the
        store at large — but it remains impossible *here*, because this runs
        on a fixture project whose only writer is the import. That is exactly
        why the live-corpus assertion in `TestThisProjectsOwnImport` had to be
        scoped to the `goals` lane while this one did not have to move.
        """
        root = self.project()
        stamped = [r for r in self.imported(root) if "via" in r]
        self.assertTrue(stamped)
        for rec in stamped:
            self.assertEqual(rec["via"], "link",
                             f"{rec} was imported as if it had been declared "
                             f"at `add`, which is what P003-O3-KR2 counts")

    def test_declared_at_is_the_registers_own_stamp_not_todays_clock(self):
        root = self.project()
        for rec in self.imported(root):
            if "declared_at" in rec:
                self.assertEqual(rec["declared_at"], "2026-09-01T04:05:06Z")

    def test_a_day_only_updated_is_refused_rather_than_read_as_midnight(self):
        """Row A's schema note: *a day-only value is dropped, not guessed*.

        `lib.ts_moment` would happily read `2026-09-01` as UTC midnight, which
        is a fabricated wall clock on 115 records.
        """
        root = self.project(FIXTURE_REGISTER.replace(
            'updated: "2026-09-01T04:05:06Z"', 'updated: "2026-09-01"'))
        proc = self.run_tasks(root, "linkage-write", "--from-register")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("day-only value is dropped, not guessed", proc.stderr)
        self.assertFalse((root / "perry" / STORE_KEY).exists(),
                         "a refusal wrote a store (ADR-004)")

    def test_the_actor_is_the_lane_that_declared_them(self):
        """Found by a mutation: renaming `actor` left every test green.

        `actor` is not decoration. Row A's schema note says it is written from
        the start *"so DESIGN-015 § 5.5 is AUDITABLE before it is enforced"* —
        § 5.5 is the per-kind, per-lane table (`work` may never write a `kr`;
        `goals` may write all three), and `actor` plus `via` are the only two
        fields an audit of it can read. A value nothing pins is a value the
        audit reads whatever the last edit happened to leave.

        `goals` is the LANE, not a person. The register records no individual,
        so naming one would invent it; the lane is a fact the document
        asserts about itself — *"`goals` lane (only writer)"*.
        """
        stamped = [r for r in self.imported(self.project()) if "actor" in r]
        self.assertTrue(stamped)
        for rec in stamped:
            self.assertEqual(rec["actor"], "goals", rec)

    def test_the_kr_records_carry_no_stamp_at_all(self):
        """A `kr` is not a declaration by anybody; the schema gives it none of
        the three fields, so carrying them would be inventing a shape."""
        for rec in self.imported(self.project()):
            if rec["kind"] == "kr":
                for field in ("declared_at", "actor", "via"):
                    self.assertNotIn(field, rec)


class TestEmptyIsAsserted(LinkageFixture):
    """`agents: []` and `projects: []` — asserted empty, not silently absent.

    TASK-277's spec asks for this by name, and the distinction is the whole
    difference between a check and an accident: a loop over an empty list and
    a loop nobody wrote produce the same zero records.
    """

    def test_no_record_of_either_shape_is_produced(self):
        records = self.imported(self.project())
        kinds = {r["kind"] for r in records}
        self.assertEqual(kinds, {"kr", "edge", "unlinked"})
        self.assertEqual(len(declared()["records"]), 3,
                         "a fourth record kind was declared and this import "
                         "produces none of it")

    def test_a_non_empty_agents_list_is_refused_not_skipped(self):
        """The half that proves the zero above was measured.

        With `agents:` holding an entry the import must REFUSE, because it
        mints no record for one. An import that silently produced 121 records
        from a register holding 122 facts is the drop § 7's first risk row
        names.
        """
        root = self.project(FIXTURE_REGISTER.replace(
            "agents: []", 'agents:\n  - id: AGENT-1\n    tasks: ["TASK-004"]'))
        proc = self.run_tasks(root, "linkage-write", "--from-register")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("is not empty", proc.stderr)
        self.assertFalse((root / "perry" / STORE_KEY).exists())

    def test_a_non_empty_projects_list_is_refused_not_skipped(self):
        root = self.project(FIXTURE_REGISTER.replace(
            "projects: []",
            'projects:\n  - id: PROJ-1\n    serves: "P009-O1-KR1"'))
        proc = self.run_tasks(root, "linkage-write", "--from-register")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("is not empty", proc.stderr)

    def test_a_missing_key_is_refused_rather_than_read_as_empty(self):
        """An ABSENT `agents:` and an empty one produce the same zero records,
        and only one of them means the register has nothing to say."""
        root = self.project(FIXTURE_REGISTER.replace("agents: []\n", ""))
        proc = self.run_tasks(root, "linkage-write", "--from-register")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("carries no `agents:` key at all", proc.stderr)


class TestTheImportRefusesRatherThanGuesses(LinkageFixture):
    """Every check is a refusal that writes nothing — ADR-004."""

    def test_the_consent_flag_is_required(self):
        root = self.project()
        proc = self.run_tasks(root, "linkage-write")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--from-register", proc.stderr)
        self.assertFalse((root / "perry" / STORE_KEY).exists())

    def test_the_current_phases_register_is_the_one_imported(self):
        """Not a glob. This project holds three `phase/*-linkage.md` files and
        only one is the register `perry-goals link` appends to; importing all
        three would put phase 001's edges, naming KRs phase 003 does not have,
        into phase 003's store."""
        root = self.project(extra_registers=True)
        records = self.imported(root)
        for rec in records:
            if rec["kind"] == "kr":
                self.assertEqual(rec["phase"], "009-fixture")
        self.assertEqual(self.store_facts(records), self.register_facts(root))

    def test_an_objective_that_disagrees_with_its_kr_id_is_refused(self):
        """`perry-lint` reports this as `linkage-objective-agrees`. Writing
        either answer resolves in silence a disagreement the register is still
        having with itself."""
        root = self.project(FIXTURE_REGISTER.replace(
            "id: P009-O2-KR1", "id: P009-O7-KR1"))
        proc = self.run_tasks(root, "linkage-write", "--from-register")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("linkage-objective-agrees", proc.stderr)
        self.assertFalse((root / "perry" / STORE_KEY).exists())

    def test_an_unparseable_register_is_refused(self):
        root = self.project("no frontmatter here at all\n")
        proc = self.run_tasks(root, "linkage-write", "--from-register")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertFalse((root / "perry" / STORE_KEY).exists())

    def test_a_wrong_spec_version_is_refused(self):
        root = self.project(FIXTURE_REGISTER.replace("linkage: 1",
                                                     "linkage: 2"))
        proc = self.run_tasks(root, "linkage-write", "--from-register")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("expected 1", proc.stderr)


class TestTheRecordsMatchTheDeclaredSchema(LinkageFixture):
    """Validated by the LINTER's own function, not by a second copy."""

    def test_every_imported_record_passes_the_census_validator(self):
        root = self.project()
        records = self.imported(root)
        proc = subprocess.run(
            [sys.executable, str(LINT), "--root", str(root)],
            capture_output=True, text=True, cwd=ROOT)
        self.assertNotIn("linkage-store-malformed", proc.stdout + proc.stderr,
                         "the import wrote records the census rejects")
        self.assertTrue(records)

    def test_no_record_carries_a_field_the_schema_does_not_declare(self):
        fields = {kind: set(spec.get("fields") or {})
                  for kind, spec in declared()["records"].items()}
        for rec in self.imported(self.project()):
            self.assertLessEqual(set(rec), fields[rec["kind"]])

    def test_every_required_field_is_present(self):
        required = {kind: {n for n, s in (spec.get("fields") or {}).items()
                           if s.get("required")}
                    for kind, spec in declared()["records"].items()}
        for rec in self.imported(self.project()):
            self.assertLessEqual(required[rec["kind"]], set(rec))

    def test_current_provenance_is_imported_into_by_nothing(self):
        """Row A declared it because § 5.1 spells it, and flagged that nothing
        stores it: `bin/lib § kr_progress_provenance` DERIVES it at read time
        from the event log, so an imported copy is stale by construction."""
        for rec in self.imported(self.project()):
            self.assertNotIn("current_provenance", rec)


class TestTheCensusStopsSayingUnchecked(LinkageFixture):
    """Row A left the seventh store reporting an ABSENT file. Row B fills it.

    **Updated by TASK-278, which is row C.** These two tests pinned the
    B-to-C window — *"until row C moves the readers there is nothing to
    compare the store against"* — and row C is what closes it. The readers
    now answer from the store, so the document beside it is the projection
    and the two can be held up against each other like the other six
    registers. The verdict is real.

    **What that argument was protecting is kept, not dropped**, because it
    was never about the words on the line: a `clean` verdict nobody computed
    is TASK-117's defect whichever row is current. So the third test below is
    new and asserts the same thing one state further on — with no register
    document to compare against, the line still says `unchecked, not clean`,
    and `comparison_performed` is driven by the count of registers actually
    compared rather than by "the store parsed".
    """

    def census(self, root: pathlib.Path) -> str:
        proc = subprocess.run(
            [sys.executable, str(LINT), "--root", str(root)],
            capture_output=True, text=True, cwd=ROOT)
        lines = [ln for ln in proc.stdout.split("\n")
                 if STORE_KEY in ln or "linkage store" in ln]
        self.assertEqual(len(lines), 1, f"expected one census line, got {lines}")
        return lines[0]

    def test_with_records_present_the_line_reports_the_count(self):
        """The count is DERIVED from the store, never typed in here. A
        literal would pin this module to one fixture and go red the day the
        fixture gained a KR — the staleness DESIGN-015 § 9 is about."""
        root = self.project()
        records = self.imported(root)
        self.assertIn(f"linkage store: {len(records)} record(s)",
                      self.census(root))

    def test_the_verdict_is_computed_now_that_the_readers_have_moved(self):
        """Row C's half of the line — TASK-278.

        The import produced a store that says exactly what the register says,
        so `0 row(s) drifted` here is a comparison that RAN and found nothing,
        not a comparison that was skipped. The two are told apart by the words
        on the line: `comparison incomplete` is gone, and a drift count is
        only ever printed on the branch that computed one.
        """
        root = self.project()
        self.imported(root)
        line = self.census(root)
        self.assertIn("row(s) drifted", line)
        self.assertIn("0 row(s) drifted", line,
                      "the import was byte-faithful, so nothing should drift")
        self.assertNotIn("comparison incomplete", line)

    def test_with_nothing_to_compare_it_is_unchecked_and_not_clean(self):
        """**Not `clean`.** The argument the B-to-C window's test carried,
        one state further on.

        A store whose phases have no register document beside them has
        nothing to compare against, and a `clean` verdict there would be the
        census asserting a drift comparison nobody ran — TASK-117's defect,
        and the reason `P003-O1-KR3` makes `unchecked` the answer for an
        unmeasurable store rather than `clean`.
        """
        root = self.project()
        self.imported(root)
        (root / "perry" / "phase" / "009-linkage.md").unlink()
        line = self.census(root)
        self.assertIn("comparison incomplete — drift is unchecked, not clean",
                      line)
        self.assertNotIn("row(s) drifted", line)


class TestPerryRecognisesItsOwnStore(LinkageFixture):
    """The import's own finding, pinned so it cannot come back.

    The first `perry-lint --root .` run after the import raised **NS-01** on
    `perry/linkage.jsonl` — Perry reporting its own declared store as *"1
    file(s) Perry did not write"* and advising the user to `/perry relocate`
    away from it. `looks_like_perry_record` has had to be taught four store
    shapes before this one, and the comments on all four say exactly this
    happens when it is not: *"or it reports `asks.jsonl` as a file Perry did
    not write, against Perry's own claim, on every project that runs the
    import."* Row B is the import for the fifth.
    """

    def collisions(self, root: pathlib.Path) -> int:
        proc = subprocess.run(
            [sys.executable, str(LINT), "--root", str(root), "--claims",
             "--json"], capture_output=True, text=True, cwd=ROOT)
        return json.loads(proc.stdout)["collisions"]

    def test_an_imported_store_adds_no_collision(self):
        """A DELTA, measured on the same fixture before and after.

        An absolute zero would be asserting something about the fixture's
        other claims; what this row can be held to is that writing the store
        adds no collision that was not there a moment earlier.
        """
        root = self.project()
        before = self.collisions(root)
        self.imported(root)
        self.assertEqual(self.collisions(root), before,
                         "Perry reports its own store as a file it did not "
                         "write, against its own claim")

    def test_a_genuinely_foreign_jsonl_is_still_reported(self):
        """The fix must not be a blanket excuse for anything at the path — a
        project that happens to own a `linkage.jsonl` is exactly the collision
        the claim exists to report, which is why the rule is SHAPE, not name.
        """
        root = self.project()
        before = self.collisions(root)
        (root / "perry" / STORE_KEY).write_text(
            '{"customer": "acme", "amount": 12}\n', encoding="utf-8")
        self.assertEqual(self.collisions(root), before + 1,
                         "a user's own file at the claimed path is the "
                         "collision NS-01 exists to report")


def tasks_module():
    """`bin/perry-tasks` in-process, for the guards that cannot be reached
    from the command line. Same `SourceFileLoader` mechanism the tool itself
    uses to reach its siblings — the scripts have no `.py` extension."""
    import importlib.machinery
    import importlib.util
    spec = importlib.util.spec_from_loader(
        "perry_tasks_under_test",
        importlib.machinery.SourceFileLoader("perry_tasks_under_test",
                                             str(TASKS)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestTheGuardsActUALLYFire(LinkageFixture):
    """**Every test above this class checks an OUTCOME on the happy path.**

    A mutation round said so, and it is the finding of this row: five separate
    guards — the canonical-reader cross-check, the undeclared-field check, the
    store→register direction of the account, the multiset arithmetic under it,
    and the register-digest check — could each be deleted outright and the
    whole module stayed green. Nothing ever made one of them fire, so each was
    a guard that had never been observed guarding anything: decoration in
    exactly the sense TASK-276's own round found in `stores.declared`'s
    unread `discriminator`.

    The shape is worth naming because it is not "a missing test". A suite that
    only ever presents correct input proves the code produces the right answer
    on correct input, and says nothing at all about the branches that exist
    solely for the wrong input — which is every safety check in the file.
    """

    def setUp(self):
        self.mod = tasks_module()
        self.root = self.project()
        self.records = self.imported(self.root)
        text = (self.root / "perry" / "phase" / "009-linkage.md").read_text(
            encoding="utf-8")
        self.canonical = P.parse_linkage(text)

    def test_a_surplus_record_makes_the_account_refuse(self):
        """The store→register direction. Without it the gate is one-way, and
        a one-way gate is satisfied by a store that holds everything the
        register does PLUS an edge for a task nobody linked."""
        surplus = dict(self.records[-1])
        surplus["task"] = "TASK-999"
        account = self.mod.linkage_account(self.records + [surplus],
                                           self.canonical)
        self.assertFalse(account["accounted"])
        self.assertIn("TASK-999",
                      account["kinds"]["unlinked"]["in_store_not_in_register"])

    def test_a_missing_record_makes_the_account_refuse(self):
        account = self.mod.linkage_account(self.records[:-1], self.canonical)
        self.assertFalse(account["accounted"])
        self.assertTrue(
            account["kinds"]["unlinked"]["in_register_not_in_store"])

    def test_a_duplicated_record_is_a_surplus_not_a_wash(self):
        """The multiset arithmetic. A set difference reports NOTHING here: the
        duplicate is `in` the register's list, so `store - register` is empty
        and the counts still differ. `cmd_asks_write` found this exact class
        for repeated `USER-` ids."""
        account = self.mod.linkage_account(
            self.records + [dict(self.records[-1])], self.canonical)
        self.assertFalse(account["accounted"],
                         "a duplicated record washed out of the account")
        self.assertEqual(account["store_total"],
                         account["register_total"] + 1)

    def test_an_undeclared_kind_in_the_store_is_reported(self):
        account = self.mod.linkage_account(
            self.records + [{"kind": "agent", "id": "AGENT-1"}],
            self.canonical)
        self.assertFalse(account["accounted"])
        self.assertEqual(account["unknown_kind"][0]["kind"], "agent")

    def test_linkage_diff_exits_non_zero_on_a_tampered_store(self):
        """And the gate is reachable from the command line, not only from a
        unit test that imports the module."""
        path = self.root / "perry" / STORE_KEY
        path.write_text(path.read_text(encoding="utf-8")
                        + json.dumps({"kind": "unlinked", "task": "TASK-999",
                                      "declared_at": "2026-09-01T04:05:06Z",
                                      "actor": "goals", "via": "link"}) + "\n",
                        encoding="utf-8")
        proc = self.run_tasks(self.root, "linkage-diff")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertFalse(json.loads(proc.stdout)["accounted"])

    def test_the_cross_check_against_the_canonical_reader_raises(self):
        """`_linkage_agrees_with_canonical` deleted outright left every test
        green, because the TESTS do the cross-check and the CODE's copy of it
        was never observed. Handed records that disagree, it must refuse."""
        wrong = [r for r in self.records if r["kind"] != "unlinked"]
        with self.assertRaises(self.mod.Refused):
            self.mod._linkage_agrees_with_canonical(wrong, self.canonical)

    def test_the_cross_check_sees_a_changed_kr_field_not_just_a_count(self):
        """A count agreeing is not the fields agreeing — § 7's first risk row
        is a dropped value, not a dropped record."""
        bent = [dict(r) for r in self.records]
        for r in bent:
            if r["kind"] == "kr" and r["id"] == "P009-O1-KR1":
                r["target"] = 99
        with self.assertRaises(self.mod.Refused):
            self.mod._linkage_agrees_with_canonical(bent, self.canonical)

    def test_an_undeclared_field_is_refused_not_silently_dropped(self):
        """`_linkage_ordered` rebuilds each record in the schema's declared
        order. A field the schema has never heard of would vanish in that
        rebuild, which is a derivation defect disappearing into a feature."""
        order = list(declared()["records"]["edge"]["fields"])
        with self.assertRaises(self.mod.Refused):
            self.mod._linkage_ordered({"kind": "edge", "task": "TASK-1",
                                       "invented": True}, order)
        # …and the control: a declared subset rebuilds fine.
        self.assertEqual(
            self.mod._linkage_ordered({"task": "TASK-1", "kind": "edge"},
                                      order),
            {"kind": "edge", "task": "TASK-1"})

    def test_a_register_that_moves_mid_import_is_reported_not_reported_clean(self):
        """The digest guard, made to fire.

        Nothing in `bin/perry-tasks` opens the register for writing, so this
        branch can only be reached by something else moving the file while the
        import runs — and reporting the import clean in that case would be a
        green gate over a register that changed under it. Deleting the branch
        left every test green, so here it is reached deliberately: the write
        step is wrapped to touch the register as a side effect.
        """
        root = self.project()
        register = root / "perry" / "phase" / "009-linkage.md"
        mod = tasks_module()
        real = mod.lib.write_atomic

        def meddle(path, text):
            out = real(path, text)
            register.write_text(register.read_text(encoding="utf-8") + "\n",
                                encoding="utf-8")
            return out

        mod.lib.write_atomic = meddle
        self.addCleanup(setattr, mod.lib, "write_atomic", real)
        code = mod.main(["linkage-write", "--from-register",
                         "--root", str(root)])
        self.assertEqual(code, 2, "the import reported success over a "
                                  "register that changed under it")


class TestThisProjectsOwnImport(unittest.TestCase):
    """The live register against the live store — the deliverable itself.

    Everything above runs on a fixture. This class asserts the same property
    of the file this row actually shipped, because a fixture proves the code
    works and only the real corpus proves the row landed.
    """

    def test_the_store_accounts_for_the_register_in_both_directions(self):
        proc = subprocess.run(
            [sys.executable, str(TASKS), "linkage-diff", "--root", str(ROOT)],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        account = json.loads(proc.stdout)
        self.assertTrue(account["accounted"])
        self.assertEqual(account["register_total"], account["store_total"])
        for kind, v in account["kinds"].items():
            self.assertEqual(v["in_register_not_in_store"], [], kind)
            self.assertEqual(v["in_store_not_in_register"], [], kind)

    def test_no_live_record_the_goals_lane_declared_was_stamped_via_add(self):
        """`via: "add"` on a record this lane wrote would inflate `P003-O3-KR2`.

        **Scoped to the `goals` lane, not to the whole store, and row D is
        why.** Until TASK-279 this asserted `via == "link"` over EVERY record
        in `perry/linkage.jsonl`. That was true only while the import was the
        store's sole writer. Row D gives `perry-task add --kr` the `work`
        lane's write, whose whole purpose is to stamp `via: "add"` — so the
        first legitimate use of the gate made the old assertion false, and
        two rows filed with `--kr` on 2026-09-07 did exactly that. The
        blanket form was reddening `main` for the feature working.

        **What is still asserted, and it is the part that matters.** The
        import stamps `actor: "goals"` unconditionally
        (`bin/perry-tasks § LINKAGE_IMPORT_ACTOR`), so every record it wrote
        is inside this filter — 115 of the live store's 123 today. DESIGN-015
        § 1 measured that the historical declarations were NOT made at `add`:
        *"The 44 declarations were not made at `add`; they were swept in
        later."* `bin/lib § computed_kr_current` counts `via == "add"` with
        NO `actor` filter, so an import that stamped `add` would carry
        `P003-O3-KR2` from its 0 baseline towards 100% on records describing
        behaviour that never ran. That guard is untouched.

        **The lane is the right scope, not "whatever a fresh import writes".**
        DESIGN-015 § 7 names `actor` and `via` as the two fields a check of
        the § 5.5 per-lane table would read, and § 5.5 gives `edge`-at-`add`
        to `work` (`perry-task`) and `edge`-at-`link` to `goals`
        (`perry-goals`). A record stamped `actor: "goals", via: "add"` is
        therefore not noise to be filtered away — it is precisely the § 7
        risk, a lane claiming an action § 5.5 does not give it, and this is
        the only site in the suite that would see it on the live corpus.

        The alternative scope — *the records a fresh import run produces* —
        was rejected. It re-runs the importer instead of reading the artefact
        that shipped, which is what this class exists for (*"only the real
        corpus proves the row landed"*); it cannot validate the shipped store
        at all, because the register has moved since the import and a re-run
        produces a different record set; and
        `TestTheStampIsNotFabricated.test_via_is_link_and_never_add` already
        covers the importer's own output, on a fixture, where the store has
        no other writer to confuse it.
        """
        records = [json.loads(line) for line
                   in (ROOT / "perry" / STORE_KEY).read_text(
                       encoding="utf-8").split("\n") if line.strip()]
        declared_by_goals = [r for r in records if r.get("actor") == "goals"]
        # Without this the loop below is vacuously true on an empty store, on
        # one whose `actor` was renamed, and on one the import never filled —
        # three ways to pass for the absence of the input rather than for the
        # guard. `kr` records carry no `actor` at all and are not in scope.
        self.assertTrue(declared_by_goals,
                        "no record in the live store is attributed to the "
                        "`goals` lane, so this test asserted nothing")
        for rec in declared_by_goals:
            self.assertEqual(
                rec.get("via"), "link",
                f"{rec} is attributed to the `goals` lane but claims it was "
                f"declared at `add` — which is what P003-O3-KR2 counts "
                f"(`bin/lib § computed_kr_current`), and what DESIGN-015 "
                f"§ 5.5 gives to `work`, not to this lane")


if __name__ == "__main__":
    unittest.main(verbosity=2)
