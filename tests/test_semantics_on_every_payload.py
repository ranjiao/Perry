"""`semantics` is on **every** read payload, including the three with nothing
to say.

**The gap this closes, and it was named rather than found.** Four of Perry's
**six** read payloads shipped without the array: `perry-goals/list` at `2.2`,
`perry-decide/list` at `1.0`, `perry-knowledge/list` at `1.0`, and
`perry-roles/list` at `1.0` — which the measurement that opened this row did
not list at all, because it is a versioned SUBTREE of an unversioned snapshot
rather than its own `list` command. The consequence is not that a consumer
misses a warning: it is that `CONTRACT_TESTED` against any of those payloads
**can never go red**, because the array a consumer walks is absent by
construction. An honest comment, not a guard.

**Why the empty array is the deliverable and not a stub.** Three of the six
carry `[]`, and that is the shipped fact. **A consumer checks before it
looks**, so a key that appears only when there is something to say is one a
consumer cannot check — the same argument that puts `contract` at the top of an
empty knowledge store, applied to the array beside it. So the assertions below
are about **presence**, on every payload regardless of content, and the day a
fourth payload earns an entry nothing here has to be edited to notice.

**And no entry was invented to fill them.** None of the three has had a value
change meaning. Writing one in would send a consumer to re-check a field that
never moved, which is worse than the empty array by the amount of work it
costs. `TestNothingWasInventedToFillThem` holds that as a decision rather than
leaving it as a gap.

The one populated addition is `perry-goals/list` `2.2` — no key added, three
timestamps changed to UTC — which is exactly what `semantics` is for. `2.1`
added four keys and moved no value, and is deliberately absent: an entry for it
would tell a consumer sitting on `2.0` that a field it has never seen changed
meaning.

Run: python3 tests/parallel test_semantics_on_every_payload
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: `(name, argv, subtree)` for every read payload Perry publishes. `subtree` is
#: the key the versioned payload hangs under, or `""` for a whole response —
#: `perry-roles/list` is a subtree of `perry-state --json`, which is exactly
#: how it was missed when this row was measured.
#:
#: Six, and a hand-kept tuple of six is the shape of list this project keeps
#: finding rotted, so `TestTheListIsEveryContractOnDisk` counts it against the
#: glob that discovers a contract page rather than trusting it.
PAYLOADS = (
    ("perry-task/list", ("perry-task", "list", "--all"), ""),
    ("perry-events/list", ("perry-task", "events"), ""),
    ("perry-goals/list", ("perry-goals", "list"), ""),
    ("perry-decide/list", ("perry-decide", "list"), ""),
    ("perry-knowledge/list", ("perry-knowledge", "list"), ""),
    ("perry-roles/list", ("perry-state", "--section", "roles"), "roles"),
)

#: The three that carry `[]` today. Named so the assertions about them can be
#: about presence, and so a payload that later earns an entry is a deliberate
#: edit here rather than a test quietly passing on new content.
EMPTY_TODAY = ("perry-decide/list", "perry-knowledge/list", "perry-roles/list")


def payload(argv: tuple[str, ...], root: pathlib.Path, subtree: str) -> dict:
    tool, *rest = argv
    proc = subprocess.run(
        [sys.executable, str(ROOT / "bin" / tool), *rest,
         "--root", str(root), "--json"],
        capture_output=True, text=True, cwd=ROOT)
    if proc.returncode != 0:
        raise AssertionError(f"{argv} exited {proc.returncode}: "
                             f"{proc.stderr[-400:]}")
    got = json.loads(proc.stdout)
    return got[subtree] if subtree else got


class Base(unittest.TestCase):
    """Read against Perry's own project, which is the only one with enough
    state to populate every array these payloads carry."""

    @classmethod
    def setUpClass(cls):
        cls.live = {name: payload(argv, ROOT, sub)
                    for name, argv, sub in PAYLOADS}


class TestEveryPayloadCarriesTheKey(Base):

    def test_the_key_is_present_and_is_a_list(self):
        """**Presence, not content.** The assertion that makes the two empty
        arrays a shipped fact rather than a stub, and the one that fails on the
        next payload to be published without one."""
        for name, _, _sub in PAYLOADS:
            with self.subTest(contract=name):
                self.assertIn("semantics", self.live[name],
                              f"{name} publishes no `semantics` array, so a "
                              f"consumer cannot ask it what a minor changed")
                self.assertIsInstance(self.live[name]["semantics"], list)

    def test_the_key_is_there_on_a_project_with_no_state_at_all(self):
        """A key that appears once there is something to say is one a consumer
        cannot check, so the hardest case is the one that must carry it: a
        project declared and otherwise empty. No task, no OKR, no decision, no
        card, no role, no event log.

        (`.perry/config.md` and an empty `BOARD.md` are the declaration
        itself — `perry-state` emits no `roles` section for a directory that
        has not declared it is a project, and a payload nobody publishes is a
        different question from a key nobody carries.)"""
        with tempfile.TemporaryDirectory() as tmp:
            bare = pathlib.Path(tmp)
            (bare / ".perry").mkdir()
            (bare / ".perry" / "config.md").write_text("State root: .\n")
            (bare / "BOARD.md").write_text("# Board\n")
            for name, argv, sub in PAYLOADS:
                with self.subTest(contract=name):
                    got = payload(argv, bare, sub)
                    self.assertIn("semantics", got)
                    self.assertIsInstance(got["semantics"], list)

    def test_every_entry_names_fields_and_gives_a_reason(self):
        """An entry with no `note` is a version number, and a version number
        is what the consumer already had."""
        for name, _, _sub in PAYLOADS:
            for entry in self.live[name]["semantics"]:
                with self.subTest(contract=name, version=entry["version"]):
                    self.assertTrue(entry["fields"], "names no field")
                    self.assertTrue(entry["note"].strip(), "gives no reason")
                    self.assertEqual({"version", "fields", "note"}, set(entry))

    def test_every_list_is_ordered_oldest_minor_first(self):
        """It is read as "everything newer than the minor I tested against",
        which is a slice only while it is sorted. `perry-task/list` shipped
        1.5, 1.9, 1.7 once, and a 1.16 bump prepended an entry on 2026-08-27.
        **Append; never insert where it reads well.**"""
        for name, _, _sub in PAYLOADS:
            got = [e["version"] for e in self.live[name]["semantics"]]
            with self.subTest(contract=name):
                self.assertEqual(got, sorted(
                    got, key=lambda v: tuple(int(x) for x in v.split("."))))


class TestNothingWasInventedToFillThem(Base):
    """Recorded as a decision, not left as a gap.

    `perry-decide/list`, `perry-knowledge/list` and `perry-roles/list` have
    never had a value change meaning. The array is there so a consumer can ASK;
    it is empty because the honest answer is empty, and a fabricated entry
    would cost a consumer a re-check of a field that never moved.
    """

    def test_the_three_that_have_nothing_to_say_say_nothing(self):
        for name in EMPTY_TODAY:
            with self.subTest(contract=name):
                self.assertEqual([], self.live[name]["semantics"])

    def test_the_minor_that_added_the_key_is_not_itself_an_entry(self):
        """Adding `semantics` is a key addition, which rule 2 already covers.
        An entry announcing the array's own arrival would be the first false
        alarm in it — the call `perry-task` made for its `1.15` and `1.17`."""
        for name in EMPTY_TODAY + ("perry-goals/list",):
            minor = self.live[name]["contract"].rsplit("/", 1)[-1]
            with self.subTest(contract=name):
                self.assertNotIn(
                    minor, [e["version"]
                            for e in self.live[name]["semantics"]],
                    f"{name} reports its own key addition as a meaning change")


class TestTheGoalsEntryIsTheOneThatMatters(Base):
    """`2.2` added no key and changed what three timestamps say, which is the
    case `semantics` exists for and the reason the minor moved at all."""

    def entry(self, version: str):
        return next((e for e in self.live["perry-goals/list"]["semantics"]
                     if e["version"] == version), None)

    def test_2_2_names_all_three_timestamps_that_moved(self):
        got = self.entry("2.2")
        self.assertIsNotNone(got, "the minor that changed a meaning is silent")
        self.assertEqual(set(got["fields"]), {
            "krs[].current_provenance.asserted_at",
            "krs[].current_staleness.since",
            "krs[].current_staleness.moved_tasks[].at"})

    def test_the_note_says_what_a_consumer_gets_wrong(self):
        """A note reading "these are UTC now" leaves a consumer to work out
        whether that matters. The one thing it must say is what breaks."""
        note = self.entry("2.2")["note"]
        self.assertIn("UTC", note)
        self.assertIn("local", note.lower())

    def test_2_1_has_no_entry_and_that_is_deliberate(self):
        """Four keys added, no value moved. A consumer on `2.0` has never seen
        those keys, so telling it their meaning changed is a false alarm."""
        self.assertIsNone(
            self.entry("2.1"),
            "`2.1` was a pure key addition — an entry for it would send a "
            "consumer to re-check three blocks it does not have")


class TestTheListIsEveryContractOnDisk(unittest.TestCase):
    """`PAYLOADS` is a hand-kept tuple, which is the shape of list this project
    keeps finding rotted. It is checked against the glob that discovers a
    contract page, so a sixth payload cannot be published into a suite that
    silently never reads it."""

    def test_one_payload_per_contract_page(self):
        pages = sorted(ROOT.glob("schema/*-contract.md"))
        self.assertEqual(
            len(pages), len(PAYLOADS),
            "schema/ holds " + ", ".join(p.name for p in pages)
            + f" — {len(pages)} pages against {len(PAYLOADS)} payloads here")

    def test_each_page_names_the_version_its_tool_emits(self):
        for name, argv, sub in PAYLOADS:
            live = payload(argv, ROOT, sub)["contract"]
            page = ROOT / "schema" / (name.split("/")[0].split("-", 1)[1]
                                      + "-list-contract.md")
            with self.subTest(contract=name):
                self.assertTrue(page.exists(), f"no page at {page}")
                self.assertIn(live, page.read_text(),
                              f"{page.name} does not name {live}")


if __name__ == "__main__":
    unittest.main()
