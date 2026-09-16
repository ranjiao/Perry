"""`linkage.jsonl` is a DECLARED store, not a comment in a JSON file — TASK-276.

DESIGN-015 implementation row A. The design's decision 1 puts the O→KR→task
edge register in a seventh store with `owner: perry`, because `phase/` is owned
by `goals` and `perry-task add` therefore cannot write an edge there — not as
an oversight but structurally (§ 1). Row A declares it; row B imports the
records; row C moves the six readers § 5.6 names; row D makes `add` write the
edge. `P003-O3-KR2` is measurable only at the end of that chain, which is why
this row is its head.

**What "declared" has to mean, and what this module is for.** Six stores
already declare themselves and `perry-lint --root .` prints a record count and
a drift verdict for each; phase KRs `P003-O1-KR1` and `KR2` are both scored 6
of 6 on exactly that output. So the honest test of this row is not whether a
key appeared in `schema/state-schema.json` — it is whether the seventh store
JOINS that population. Measured while writing this row: adding the `claims[]`
entry ALONE changed the census by nothing at all. Six store lines before, six
after. The census is driven by the checks that run, not by `claims[]`, so a
claim on its own is exactly the decorative declaration this module exists to
refuse. `TestTheCensusCountsIt` is the half that would have caught that.

**And `unchecked` is not a detail.** `P003-O1-KR3` — 6 of 6, measured by
TASK-229 — is the phase-003 operating rule that a store reports `unchecked`
rather than `clean` when its file is absent. This store's file does not exist
and will not until row B runs, so a seventh line reading `clean` would be a
green gate on a store nothing has ever written to: the census would report the
register in order at the exact moment it holds nothing. `TestNoRecordsIsNever
Clean` pins that, in both directions — absent, and present-but-uncompared.

Run: python3 tests/parallel test_linkage_store_declared
"""

from __future__ import annotations

COVERS = ("bin/perry-lint", "bin/lib/", "schema/state-schema.json", "setup")

import json
import pathlib
import sys
import unittest

import inproc
from store_fixture import StoreFixture

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINT = ROOT / "bin" / "perry-lint"
SCHEMA = json.loads((ROOT / "schema" / "state-schema.json").read_text())

STORE_KEY = "linkage.jsonl"

#: The three record kinds and their exact field sets, transcribed from
#: `DESIGN-015 § 5.1`'s JSONC block rather than from the schema — a test that
#: reads the schema to check the schema asserts only that JSON round-trips.
#: The design is locked, so this list is a fixed target: if it and the schema
#: disagree, one of them is wrong and the round has to say which.
#: The record shapes, and where each field came from.
#:
#: DESIGN-015 § 5.1 spelled three kinds; ADR-019 added three more and four
#: fields, because it deleted `phase/<NNN>-linkage.md` and every fact that
#: file's frontmatter carried had to be declared here or lost. The additions
#: are listed apart from § 5.1's set so the two authorities stay separable —
#: a later reader can see which line came from which decision.
DESIGN_015_5_1 = {
    "kr": {"kind", "phase", "objective", "id", "title", "target", "current",
           "stretch", "linked", "current_provenance"},
    "edge": {"kind", "task", "kr", "declared_at", "actor", "via"},
    "unlinked": {"kind", "task", "declared_at", "actor", "via"},
}

ADR_019 = {
    #: `metric` and `due` were the document's; `asserted_at` never existed
    #: anywhere and is TASK-155's fix.
    "kr": {"metric", "due", "asserted_at"},
    "edge": set(),
    #: WHICH PHASE'S BOARD the declaration was made against. § 5.1 gave the
    #: record no phase field on the ground that "this row serves no KR" is a
    #: statement about the row — true while the store covered one phase.
    "unlinked": {"phase"},
    "objective": {"kind", "phase", "id", "title"},
    "project": {"kind", "phase", "id", "kr", "name", "aliases", "status",
                "declared_at", "actor", "via"},
    "agent": {"kind", "phase", "id", "task", "declared_at", "actor", "via"},
}

#: DESIGN-022 § 5.1 (TASK-416, USER-937 decision 4): a KR's typed checks and
#: their measured values. Two kinds, no field on any existing kind.
DESIGN_022_5_1 = {
    "check": {"kind", "kr", "okr_version", "id", "label", "direction",
              "target", "baseline", "declared_at", "actor"},
    "measurement": {"kind", "kr", "okr_version", "check", "value",
                    "asserted_at", "evidence", "computed", "actor"},
}

EXPECTED = {
    kind: (DESIGN_015_5_1.get(kind, set()) | ADR_019.get(kind, set())
           | DESIGN_022_5_1.get(kind, set()))
    for kind in set(DESIGN_015_5_1) | set(ADR_019) | set(DESIGN_022_5_1)
}


def declared() -> dict:
    return ((SCHEMA.get("stores") or {}).get("declared") or {}).get(STORE_KEY)


class TestTheClaim(unittest.TestCase):
    """The `claims[]` entry itself — the mutation target the spec names.

    `claims[]` is what Perry OCCUPIES in a project it does not own, and a
    store Perry writes but does not claim collides in silence: `--claims` does
    not list it at setup and the default pass emits no `NS-01`. That is the
    exact defect TASK-100 closed for `tasks.jsonl` and `.perry/events.jsonl`,
    and declaring this store before anything writes it is the point of doing
    row A first.
    """

    def claim(self) -> dict | None:
        for c in SCHEMA["claims"]:
            if c["path"] == STORE_KEY:
                return c
        return None

    def test_linkage_jsonl_is_claimed(self):
        self.assertIsNotNone(
            self.claim(),
            f"{STORE_KEY} is written by DESIGN-015 rows B and D and claimed "
            f"by nobody — a store Perry occupies without declaring collides "
            f"in silence (TASK-100)")

    def test_the_claim_is_owned_by_perry_and_anchored_at_the_state_root(self):
        """Decision 1, and the half of it that does the work.

        `owner: perry` is the declaration `.perry/events.jsonl` carries: the
        file belongs to no lane. That is what lets `work` write an edge at
        `add` and `goals` write one at `link` with neither touching the
        other's directory — DESIGN-015 goal 3, satisfied without amending the
        hand-off contract. `owner: goals` is the rejected alternative and it
        is precisely the defect: it keeps `add` unable to write the edge.

        `anchor: state` is the other half. The store sits beside
        `tasks.jsonl`, so `/perry relocate` moves it with the board; a
        project-anchored claim outside `.perry/` would be unmovable.
        """
        claim = self.claim()
        self.assertIsNotNone(claim)
        self.assertEqual(claim["owner"], "perry",
                         "owner: goals is DESIGN-015 decision 1's REJECTED "
                         "option — it keeps `perry-task add` unable to write "
                         "the edge, which is the defect the design removes")
        self.assertEqual(claim["anchor"], "state",
                         "the store sits beside tasks.jsonl and must move "
                         "with it under /perry relocate")
        self.assertEqual(claim["kind"], "file")


class TestNothingElseInClaimsMoved(unittest.TestCase):
    """The NOT-authorised half of the 2026-09-04 authorisation, asserted.

    `evidence/2026-09/2026-09-04-high-stakes-authorisation.md` grants exactly
    one thing — adding this claim and its three record schemas — and refuses
    "changing any existing claim's path or owner". A permission that is only
    described in prose is checked by nobody, so the six stores that were
    already declared are pinned here by path AND owner. Named explicitly
    rather than scraped, on `test_claims.py`'s own reasoning: a silently
    narrowed check is worse than a loud failure.
    """

    #: (path, owner, anchor) as they stood before TASK-276, read off `main`
    #: at 5d19d83.
    PRE_EXISTING_STORES = [
        ("tasks.jsonl", "work", "state"),
        ("okr.jsonl", "goals", "state"),
        ("risks.jsonl", "work", "state"),
        ("intake.jsonl", "work", "state"),
        ("asks.jsonl", "work", "state"),
        (".perry/config.jsonl", "perry", "project"),
        (".perry/events.jsonl", "perry", "project"),
    ]

    def test_no_pre_existing_store_claim_changed_path_or_owner(self):
        by_path = {c["path"]: c for c in SCHEMA["claims"]}
        for path, owner, anchor in self.PRE_EXISTING_STORES:
            with self.subTest(path=path):
                self.assertIn(path, by_path,
                              f"{path} left claims[] — TASK-276 was "
                              f"authorised to ADD one claim, not to move one")
                self.assertEqual(by_path[path]["owner"], owner)
                self.assertEqual(by_path[path]["anchor"], anchor)

    def test_the_phase_directory_is_still_owned_by_goals(self):
        """The claim DESIGN-015 § 1 blames, left exactly as it was.

        `phase/` carrying `owner: goals` is what makes `perry-task` unable to
        write the edge, and the tempting "fix" is to widen that owner. The
        design rejects it: decision 1 puts the store beside the others under
        `owner: perry` instead, so the hand-off contract needs no second
        signature. Re-owning `phase/` is also the specific change the
        authorisation refuses.
        """
        phase = [c for c in SCHEMA["claims"] if c["path"] == "phase/"]
        self.assertEqual(len(phase), 1)
        self.assertEqual(phase[0]["owner"], "goals")


class TestTheThreeRecordSchemas(unittest.TestCase):
    """`stores.declared["linkage.jsonl"].records` against DESIGN-015 § 5.1."""

    def test_the_store_is_declared_at_all(self):
        self.assertIsNotNone(
            declared(),
            "the claim says Perry occupies the path; nothing says what one "
            "LINE of it must contain, so row B has nothing to validate an "
            "import against")

    def test_the_kinds_are_exactly_the_declared_ones(self):
        """Three from DESIGN-015 § 5.1, three from ADR-019 — and no seventh.

        A `kind` nothing writes is a shape a reader will one day be surprised
        not to find, and a kind written but not declared is a record
        `perry-lint` reports as malformed on every run.
        """
        self.assertEqual(set(declared()["records"]), set(EXPECTED))
        self.assertEqual(set(ADR_019) - set(DESIGN_015_5_1),
                         {"objective", "project", "agent"},
                         "ADR-019 added exactly the three kinds the deleted "
                         "document was the only home for")
        self.assertEqual(set(EXPECTED) - set(DESIGN_015_5_1) - set(ADR_019),
                         {"check", "measurement"},
                         "DESIGN-022 added exactly the two kinds USER-937 "
                         "decision 4 authorized")

    def test_there_is_no_fourth_kind(self):
        """§ 5.2 — never-asked is DERIVED, not stored.

        A task is never-asked when the store holds neither an `edge` nor an
        `unlinked` record for it. A `never_asked` record would have to be
        DELETED the moment an answer arrives, which is a second write and a
        chance to desync; absence cannot drift. Same rule `asks.jsonl` applies
        to `Idle`.
        """
        self.assertNotIn("never_asked", declared()["records"])
        self.assertNotIn("never-asked", declared()["records"])

    def test_each_kind_carries_exactly_the_fields_declared_for_it(self):
        for kind, want in EXPECTED.items():
            with self.subTest(kind=kind):
                got = set(declared()["records"][kind]["fields"])
                self.assertEqual(
                    got, want,
                    f"`{kind}` record: schema has {sorted(got)}, "
                    f"§ 5.1 + ADR-019 spell {sorted(want)}")

    def test_metric_is_on_the_kr_record_and_that_reverses_decision_2(self):
        """DESIGN-015 decision 2 said a `metric:` value is an argument about
        how a number was reached — 976 B of it in one case, 43% of the
        register by bytes — and that arguments are what a document is for. It
        named `phase/<NNN>-linkage.md` as the document.

        **ADR-019 deleted that document**, so the choice stopped being "store
        or document" and became "store or lose it". This asserts the reversal
        explicitly rather than letting the field appear in a set, because a
        locked design decision reversing is the kind of thing a reader must
        be able to find by grep.
        """
        fields = declared()["records"]["kr"]["fields"]
        self.assertIn("metric", fields)
        self.assertFalse(fields["metric"].get("required"),
                         "a KR measured in a bare number has no argument to "
                         "make, and requiring one would invent prose")
        self.assertIn("ADR-019", fields["metric"].get("note", ""),
                      "the field must carry the reason it reverses a locked "
                      "decision, or the next reader re-argues decision 2")

    def test_asserted_at_is_per_kr_and_optional(self):
        """TASK-155's fix, as a shape.

        The defect: `phase/<NNN>-linkage.md` carried ONE `updated:` stamp,
        `bin/lib § kr_progress_provenance` read it as every KR's assertion
        date, and appending one edge re-dated every asserted number in the
        phase. The field is per KR now.

        **OPTIONAL, and that is the load-bearing half.** Required would force
        every writer to supply a date, and the only date a writer that did not
        measure the number can supply is `now` — which is the same defect with
        a different spelling. `""` has to stay sayable, because "nobody
        recorded when" is a fact.
        """
        spec = declared()["records"]["kr"]["fields"]["asserted_at"]
        self.assertEqual(spec["type"], "string")
        self.assertFalse(spec.get("required"))
        self.assertEqual(spec.get("format"), "iso-datetime")
        self.assertIn("TASK-155", spec.get("note", ""))

    def test_an_unlinked_declaration_names_its_phase(self):
        """§ 5.1 gave it none, deliberately, and ADR-019 had to add one.

        The old argument was sound while the store held one phase: "this row
        serves no KR" is a statement about the row. The store holds every
        phase now — three on this project — and
        `parsers.linkage_records_for_phase` handed the WHOLE unlinked set to
        whichever phase was asked, so phase 001's 23 declarations would have
        counted against phase 003's board.
        """
        spec = declared()["records"]["unlinked"]["fields"]["phase"]
        self.assertTrue(spec.get("required"))
        self.assertIn("5.1", spec.get("note", ""),
                      "the note must name the decision it reverses")

    def test_tasks_is_absent_from_the_kr_record(self):
        """One edge, one record — the whole point of the store.

        `phase/<NNN>-linkage.md` carries `tasks: [...]` on each KR. A
        counterpart array here would put the same edge in two places, which is
        the DESIGN-013 § 5.1 violation this store exists to remove, and it
        would make `via` — the field `P003-O3-KR2` is counted from —
        unrecordable for an edge inside an array.
        """
        self.assertNotIn("tasks", declared()["records"]["kr"]["fields"])

    def test_via_distinguishes_add_from_link_and_is_required(self):
        """`P003-O3-KR2` is not computable without this field.

        The KR counts rows that took an edge *in the same action as `add`*.
        An edge with no `via` cannot be told from one the goals lane swept in
        later, which is the number-that-was-typed the whole design replaces.
        """
        for kind in ("edge", "unlinked"):
            with self.subTest(kind=kind):
                via = declared()["records"][kind]["fields"]["via"]
                self.assertTrue(via.get("required"),
                                "an optional `via` makes P003-O3-KR2 "
                                "uncountable for every record that omits it")
                self.assertIn("add", via.get("pattern", ""))
                self.assertIn("link", via.get("pattern", ""))

    def test_target_and_current_are_optional_numbers(self):
        """Absent is not zero, and a prose target is not a number.

        Both rules are already load-bearing on this project's own register:
        `P003-O2-KR3` carries no `target` and three phase KRs carry no
        `current`. `bin/lib § kr_progress_provenance` reports a missing
        `current` as `unasserted` rather than `0.0` because with six of eight
        phase KRs driving a count to zero, a defaulted `0` reads as met before
        the work starts.
        """
        for field in ("target", "current"):
            with self.subTest(field=field):
                spec = declared()["records"]["kr"]["fields"][field]
                self.assertEqual(spec["type"], "number")
                self.assertFalse(spec.get("required"))


class TestTheCensusCountsIt(StoreFixture):
    """The half that separates a declared store from a decorative one.

    Six stores print a record count and a drift verdict on every
    `perry-lint --root .`; `P003-O1-KR1` and `KR2` are scored 6 of 6 on that
    output. This asserts the seventh joins them — measured, because the claim
    alone did not.
    """

    def census(self, root: pathlib.Path) -> list[str]:
        # **In-process** (TASK-368). Measured in this tree before converting:
        # 85.3% of this module is children and the boundary is 65.6% of the
        # module. It shares `store_fixture.write_store`, converted by this
        # row, so its own three sites go with it rather than leaving the
        # module half-converted. `perry-lint`'s root-keyed `_TRACK_CONTEXTS`
        # was instrumented over a full in-process run here: 0 consultations.
        proc = inproc.run("perry-lint", ["--root", str(root)], cwd=str(ROOT))
        return [ln for ln in proc.stdout.splitlines()
                if ln.strip().startswith("·")]

    def payload(self, root: pathlib.Path) -> dict:
        proc = inproc.run("perry-lint", ["--root", str(root), "--json"],
                          cwd=str(ROOT))
        self.assertTrue(proc.stdout.strip().startswith("{"),
                        f"perry-lint printed no payload: {proc.stderr}")
        return json.loads(proc.stdout)

    def linkage_line(self, root: pathlib.Path) -> str:
        lines = [ln for ln in self.census(root) if STORE_KEY in ln
                 or "linkage store" in ln]
        self.assertEqual(
            len(lines), 1,
            f"expected exactly one linkage census line, got {lines}. A store "
            f"the census does not print is a store nobody checked")
        return lines[0]

    def test_the_census_prints_a_line_for_the_seventh_store(self):
        self.assertTrue(self.linkage_line(self.project()))

    def test_the_typed_payload_reports_records_and_shape_not_drift(self):
        """**This store's payload key is `linkage_store`, not
        `linkage_store_drift`, and the difference is ADR-019's whole claim.**

        The other six stores project from a markdown document and can disagree
        with it, so each carries a `drifted` count. This one projected from
        `phase/<NNN>-linkage.md` and did too — it reported `1 row(s) drifted`
        on this project, on `P003-O3-KR2`, the day the ADR was written. The
        document is deleted, so a `drifted` key here could only ever be zero,
        and a consumer reading zero would take it for a check that passed.
        Renaming rather than keeping it at `0` is what makes the absence
        visible to a reader instead of reassuring.
        """
        payload = self.payload(self.project())
        self.assertNotIn("linkage_store_drift", payload)
        self.assertEqual(set(payload["linkage_store"]),
                         {"store_present", "records", "malformed"})
        self.assertNotIn("drifted", payload["linkage_store"])

    def test_the_records_it_counts_are_the_ones_the_schema_declares(self):
        """The declaration is load-bearing: a bad record is a finding.

        This is what stops `stores.declared` being decoration. If the schema
        were never read, a record of any shape would count.
        """
        root = self.project()
        (root / "perry" / STORE_KEY).write_text(
            json.dumps({"kind": "edge", "task": "TASK-001",
                        "kr": "P003-O3-KR2",
                        "declared_at": "2026-09-04T10:00:00+08:00",
                        "actor": "Coding Agent", "via": "add"}) + "\n"
            + json.dumps({"kind": "edge", "task": "TASK-002",
                          "kr": "P003-O3-KR2",
                          "declared_at": "2026-09-04T10:00:00+08:00",
                          "actor": "Coding Agent", "via": "swept-in"}) + "\n",
            encoding="utf-8")
        payload = self.payload(root)
        self.assertEqual(payload["linkage_store"]["records"], 1,
                         "the record with an undeclared `via` was counted")
        self.assertEqual(payload["linkage_store"]["malformed"], 1)
        codes = [f["rule"] for f in payload["findings"]]
        self.assertIn("linkage-store-malformed", codes)


class TestNoRecordsIsNeverClean(StoreFixture):
    """`P003-O1-KR3`'s rule, and what is left of it once drift cannot occur.

    The rule is that a store reports `unchecked` rather than `clean` when its
    file is absent — 6 of 6, measured by TASK-229 by removing each store in
    turn. A seventh that reported `clean` with nothing behind it would be the
    census asserting a register is in order at the moment it holds nothing.

    **The second state this class used to pin is gone with its cause.** It
    was "records present but nothing compared them yet" — the window between
    DESIGN-015 row B filling the store and row C moving the readers, where the
    line read `121 valid record(s), comparison incomplete`. There is no
    comparison to be incomplete: ADR-019 deleted the document, so the line
    reports what can still be true or false, which is how many records there
    are and how many of them match a declared shape.
    """

    def line(self, root: pathlib.Path) -> str:
        proc = inproc.run("perry-lint", ["--root", str(root)], cwd=str(ROOT))
        lines = [ln for ln in proc.stdout.splitlines()
                 if ln.strip().startswith("·")
                 and (STORE_KEY in ln or "linkage store" in ln)]
        self.assertEqual(len(lines), 1, proc.stdout)
        return lines[0]

    def test_with_the_file_absent_the_line_says_unchecked_not_clean(self):
        root = self.project()
        self.assertFalse((root / "perry" / STORE_KEY).exists())
        line = self.line(root)
        # The WHOLE sentence, not its last two words. A mutation that dropped
        # "the linkage store" left an earlier version of this test green: the
        # line still ended "is unchecked, not clean" while no longer saying
        # what was unchecked. Pinning only the suffix pins the reassurance and
        # not the content.
        self.assertIn("the linkage store is unchecked, not clean", line)

    def test_with_the_file_absent_the_line_never_says_drifted(self):
        """"Unchecked" and "0 drifted" are different answers.

        A count beside a declining is the defect TASK-117 closed for the task
        store: it read as drifted on 175 of 175 records while `perry-state`
        read the same tree as `drift: 0`.
        """
        self.assertNotIn("drifted", self.line(self.project()))

    def test_no_linkage_census_line_says_drifted_in_any_state(self):
        """**The drift class cannot occur, so the word must not appear.**

        Not "it happens to be zero" — there is one copy of this graph and
        nothing to compare it to, so a `drifted` count on this line would be a
        verdict about nothing. That is the strongest version of the mistake
        `P003-O1-KR3` exists to prevent: unchecked printed as clean.
        """
        for records in (None,
                        [],
                        [{"kind": "unlinked", "task": "TASK-001",
                          "phase": "003-storage-code",
                          "declared_at": "2026-09-04T10:00:00+08:00",
                          "actor": "Coding Agent", "via": "link"}]):
            with self.subTest(records=records):
                root = self.project()
                if records is not None:
                    (root / "perry" / STORE_KEY).write_text(
                        "".join(json.dumps(r) + "\n" for r in records),
                        encoding="utf-8")
                self.assertNotIn("drifted", self.line(root))

    def test_a_present_store_reports_its_records_and_its_malformed_count(self):
        """The control for the two tests above: a line that said nothing at
        all would satisfy both."""
        root = self.project()
        (root / "perry" / STORE_KEY).write_text(
            json.dumps({"kind": "unlinked", "task": "TASK-001",
                        "phase": "003-storage-code",
                        "declared_at": "2026-09-04T10:00:00+08:00",
                        "actor": "Coding Agent", "via": "link"}) + "\n",
            encoding="utf-8")
        line = self.line(root)
        self.assertIn("1 record(s)", line)
        self.assertIn("0 malformed", line)


if __name__ == "__main__":
    unittest.main()
