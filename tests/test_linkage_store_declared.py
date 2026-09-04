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

import json
import pathlib
import subprocess
import sys
import unittest

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
DESIGN_015_5_1 = {
    "kr": {"kind", "phase", "objective", "id", "title", "target", "current",
           "stretch", "linked", "current_provenance"},
    "edge": {"kind", "task", "kr", "declared_at", "actor", "via"},
    "unlinked": {"kind", "task", "declared_at", "actor", "via"},
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

    def test_there_are_exactly_three_kinds(self):
        self.assertEqual(set(declared()["records"]), set(DESIGN_015_5_1))

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

    def test_each_kind_carries_exactly_the_fields_design_015_spells(self):
        for kind, want in DESIGN_015_5_1.items():
            with self.subTest(kind=kind):
                got = set(declared()["records"][kind]["fields"])
                self.assertEqual(
                    got, want,
                    f"`{kind}` record: schema has {sorted(got)}, "
                    f"DESIGN-015 § 5.1 spells {sorted(want)}")

    def test_metric_is_absent_from_the_kr_record(self):
        """Decision 2, and the reason the store is not just the file again.

        A `metric:` value is an argument about how a number was reached — 976 B
        of it in one case, 43% of the register by bytes. Arguments are what a
        document is for. Keeping it here would reproduce `DESIGN-013 § 5.1`'s
        second violation inside the store built to remove the first.
        """
        self.assertNotIn("metric", declared()["records"]["kr"]["fields"])

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
        proc = subprocess.run([sys.executable, str(LINT), "--root", str(root)],
                              capture_output=True, text=True, cwd=ROOT)
        return [ln for ln in proc.stdout.splitlines()
                if ln.strip().startswith("·")]

    def payload(self, root: pathlib.Path) -> dict:
        proc = subprocess.run([sys.executable, str(LINT), "--root", str(root),
                               "--json"], capture_output=True, text=True,
                              cwd=ROOT)
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

    def test_the_typed_payload_carries_the_same_four_keys_as_the_other_six(self):
        """One shape seven times, not seven shapes."""
        payload = self.payload(self.project())
        self.assertIn("linkage_store_drift", payload)
        self.assertEqual(
            set(payload["linkage_store_drift"]),
            set(payload["ask_store_drift"]),
            "a reader of --json must meet one store-drift shape, not two")

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
        self.assertEqual(payload["linkage_store_drift"]["records"], 1,
                         "the record with an undeclared `via` was counted")
        codes = [f["rule"] for f in payload["findings"]]
        self.assertIn("linkage-store-malformed", codes)


class TestNoRecordsIsNeverClean(StoreFixture):
    """`P003-O1-KR3`'s rule, reaching the seventh store on day one.

    The rule is that a store reports `unchecked` rather than `clean` when its
    file is absent — 6 of 6, measured by TASK-229 by removing each store in
    turn. A seventh that reported `clean` with nothing behind it would be the
    census asserting a register is in order at the moment it holds nothing,
    which is the same class of defect as a green gate on a false premise.

    Two states are pinned, because this row creates BOTH. The file is absent
    until DESIGN-015 row B imports it; and from row B until row C moves the
    readers, the file exists while nothing compares it to the document the
    edges still live in. Neither state is `clean`.
    """

    def line(self, root: pathlib.Path) -> str:
        proc = subprocess.run([sys.executable, str(LINT), "--root", str(root)],
                              capture_output=True, text=True, cwd=ROOT)
        lines = [ln for ln in proc.stdout.splitlines()
                 if ln.strip().startswith("·")
                 and (STORE_KEY in ln or "linkage store" in ln)]
        self.assertEqual(len(lines), 1, proc.stdout)
        return lines[0]

    def test_with_the_file_absent_the_line_says_unchecked_not_clean(self):
        root = self.project()
        self.assertFalse((root / "perry" / STORE_KEY).exists())
        line = self.line(root)
        # The WHOLE sentence, not its last two words. A mutation that
        # dropped "drift against the" left an earlier version of this test
        # green: the line still ended "is unchecked, not clean" while no
        # longer saying what was unchecked or against which store. Pinning
        # only the suffix pins the reassurance and not the content.
        self.assertIn(
            "drift against the linkage store is unchecked, not clean", line)

    def test_with_the_file_absent_the_line_never_says_drifted(self):
        """"Unchecked" and "0 drifted" are different answers.

        A count beside a declining is the defect TASK-117 closed for the task
        store: it read as drifted on 175 of 175 records while `perry-state`
        read the same tree as `drift: 0`. Both tools now decline, and neither
        emits a number beside the declining.
        """
        self.assertNotIn("drifted", self.line(self.project()))

    def test_records_present_but_uncompared_is_also_not_clean(self):
        """Row B lands before row C, and that window must not read clean.

        DESIGN-015's one hard ordering constraint is C before D, and its named
        failure mode is silent: the edge lands, every reader still answers
        from the document, and attribution reports never-asked for a row that
        was just linked. The census must not call that state clean either.
        """
        root = self.project()
        (root / "perry" / STORE_KEY).write_text(
            json.dumps({"kind": "unlinked", "task": "TASK-001",
                        "declared_at": "2026-09-04T10:00:00+08:00",
                        "actor": "Coding Agent", "via": "link"}) + "\n",
            encoding="utf-8")
        line = self.line(root)
        self.assertIn("1 valid record(s)", line)
        self.assertIn("unchecked, not clean", line)

    def test_the_word_clean_appears_on_no_linkage_census_line_yet(self):
        """The whole claim of this class, said once and directly.

        Nothing in row A computes a drift verdict for this store — comparing
        it against `phase/<NNN>-linkage.md` moves the six readers, which is
        row C. So there is no state reachable today in which this line is
        entitled to the word `clean` unqualified.
        """
        for records in (None, [{"kind": "unlinked", "task": "TASK-001",
                                "declared_at": "2026-09-04T10:00:00+08:00",
                                "actor": "Coding Agent", "via": "link"}]):
            with self.subTest(records=records):
                root = self.project()
                if records is not None:
                    (root / "perry" / STORE_KEY).write_text(
                        "".join(json.dumps(r) + "\n" for r in records),
                        encoding="utf-8")
                self.assertIn("unchecked, not clean", self.line(root))


if __name__ == "__main__":
    unittest.main()
