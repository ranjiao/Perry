"""KR-O2.4's number: keys documented but not emitted, or emitted but not documented.

`tests/contract_key_parity.py` computes it; this holds it to a recorded
baseline so the count is comparable across runs by someone who was not here.

**What this is not.** `tests/test_contract_invariance.py` records the payload's
SHAPE and forbids a removal or a retype. It says nothing about the *document*:
a key emitted and never documented passes it cleanly, and a key documented and
never emitted was never in its baseline to begin with. This module reads the
markdown and the payload and diffs them against each other, which is the only
way the KR's metric can be a measurement rather than a hand count.

**Neither direction is asserted to be zero.** The repository's real numbers
today are 0 documented-not-emitted and 17 emitted-not-documented, and pinning
them to the baseline is what makes a change to either one visible. Closing the
gap is whatever rows the measurement produces; this row measures it.

Proved by mutation, in both directions, before it was committed:

- removing `startable` from both of its emit sites in `bin/perry-task` puts
  `tasks[].startable` in `documented_not_emitted` and names it here;
- adding an undeclared key to the payload puts `tasks[].<key>` in
  `emitted_not_documented` and names it here;
- moving one file out of `schema/` changes `contract_files_discovered` from 5
  to 4 and fails `test_the_glob_still_finds_every_contract_on_disk`.

Run: python3 tests/parallel test_contract_key_parity
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import contract_key_parity as parity  # noqa: E402


BASELINE = parity.BASELINE


def recorded() -> dict:
    return json.loads(BASELINE.read_text())


#: A whole contract page, in the shape the check reads: a `# ` heading naming
#: the invocation, and a ```jsonc``` sketch of the payload. `{extra}` is a key
#: no tool emits.
SIXTH = """# `perry-decide list --json` — `perry-sixth/list/1.0`

A contract page that did not exist when the check was written.

## The payload

```jsonc
{{
  "contract": "perry-sixth/list/1.0",
  "{extra}":  "never emitted by anything"
}}
```
"""


class TestTheBaselineIsAFile(unittest.TestCase):
    """Point 3 of the deliverable: the number lives on disk, not in a memory
    or a docstring, or it cannot be compared across runs."""

    def test_the_baseline_exists_and_parses(self):
        self.assertTrue(
            BASELINE.exists(),
            f"no baseline at {BASELINE} — run "
            f"`python3 tests/contract_key_parity.py --record`")
        self.assertIn("contracts", recorded())

    def test_the_baseline_records_a_count_per_contract(self):
        for name, entry in recorded()["contracts"].items():
            for field in ("documented_not_emitted", "emitted_not_documented"):
                self.assertIsInstance(entry[field], list, f"{name}: {field}")


class TestDiscoveryIsAGlob(unittest.TestCase):
    """A hand-written list of contracts is the defect this row exists about:
    KR-O2.4 says "all three contracts" and there are five."""

    def test_the_glob_still_finds_every_contract_on_disk(self):
        found = parity.discover()
        self.assertEqual(
            recorded()["contract_files_discovered"], len(found),
            "the number of contract files changed — "
            + ", ".join(p.name for p in found))

    def test_the_glob_finds_a_contract_that_did_not_exist_before(self):
        """Point 2, proved rather than asserted: a sixth page is picked up with
        no edit to the check."""
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp)
            for existing in parity.discover():
                (home / existing.name).write_text(existing.read_text())
            before = len(parity.discover(home))
            (home / "sixth-contract.md").write_text(SIXTH.format(extra="ghost"))
            self.assertEqual(before + 1, len(parity.discover(home)))


class TestThisREADMEAgreesWithTheGlob(unittest.TestCase):
    """`schema/README.md` said *three* read contracts for two contracts' worth
    of drift, while the directory beside it held five.

    A count in prose is exactly the hand-written list `discover()` refuses to
    carry, and it rots the same way — so it is checked against the glob rather
    than against a person who counted once. The failure this prevents is not
    cosmetic: a consumer is told to read `schema/`, and a contract the README
    does not list is one a careful reader concludes does not exist.
    `perry-knowledge/list/1.0` shipped, emitted its `contract:` string, and was
    asked to be built anyway.
    """

    #: Small on purpose. The README writes the number as a word, in house
    #: style, and a general number parser here would be more machinery than
    #: the fact deserves.
    WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
             "seven": 7, "eight": 8, "nine": 9, "ten": 10}

    def setUp(self):
        self.readme = (parity.ROOT / "schema" / "README.md").read_text()
        self.pages = parity.discover()

    def test_the_stated_count_is_the_number_of_contract_pages(self):
        stated = re.search(r"^## The (\w+) read contracts\s*$",
                           self.readme, flags=re.M)
        self.assertIsNotNone(
            stated, "schema/README.md no longer has a `## The <n> read "
                    "contracts` heading for the count to be checked against")
        word = stated.group(1).lower()
        self.assertIn(word, self.WORDS,
                      f"the heading says {word!r}, which is not a number word "
                      f"this check knows")
        self.assertEqual(
            len(self.pages), self.WORDS[word],
            "schema/README.md says there are "
            f"{self.WORDS[word]} read contracts and {parity.GLOB} matches "
            f"{len(self.pages)}: "
            + ", ".join(p.name for p in self.pages))

    def test_the_contract_table_pins_no_version(self):
        """The README's table carried THREE stale versions at once.

        On 2026-08-27 it pinned `perry-task/list` at `1.11` against a live
        `1.15`, `perry-goals/list` at `1.0` against `2.1`, and
        `perry-events/list` at `1.0` against `1.1`. All three had been correct
        when written. A version copied into a second place goes stale the first
        time the first place moves, and nothing was checking this one.

        So the table names the contract FAMILY and the numbers are gone. This
        asserts they stay gone — deleting the stale pins without this test just
        resets the clock on the same defect.

        Scoped to the table, not the file: the prose around it cites
        `perry-knowledge/list/1.0` while recounting the incident where that
        exact version shipped with no page, and that sentence is a historical
        fact rather than a pin. A file-wide ban would forbid the project from
        describing its own history.
        """
        rows = [l for l in self.readme.splitlines()
                if l.startswith("| `perry-") and "/list" in l]
        self.assertEqual(len(rows), len(self.pages),
                         f"expected one table row per contract page, got "
                         f"{len(rows)} rows for {len(self.pages)} pages")
        pinned = [l for l in rows if re.search(r"perry-[a-z]+/list/\d", l)]
        self.assertEqual(
            pinned, [],
            "the contract table names a version again. The live version is the "
            "`contract` string in the payload and the page's own first line; a "
            "number here has nothing checking it and goes stale silently:\n  "
            + "\n  ".join(pinned))

    def test_every_contract_page_on_disk_is_listed(self):
        """The count agreeing is necessary and not sufficient — six rows for
        five pages plus one invention would pass the check above."""
        for page in self.pages:
            self.assertIn(
                f"schema/{page.name}", self.readme,
                f"{page.name} is a contract page that schema/README.md never "
                f"names, so a reader of that page cannot find it")

    def test_the_readme_says_how_a_new_one_is_discovered(self):
        """Point 2 of TASK-169: the count going stale again is expected, and
        what saves the reader is being told the glob — not the table."""
        self.assertIn(parity.GLOB, self.readme,
                      "schema/README.md does not tell a reader the glob that "
                      "discovers a contract page")


class TestTheTwoWayDiffIsHeldToItsBaseline(unittest.TestCase):

    def setUp(self):
        self.recorded = recorded()
        self.live = parity.measure()

    def test_the_same_contracts_are_measured(self):
        self.assertEqual(set(self.recorded["contracts"]),
                         set(self.live["contracts"]),
                         "a contract appeared or vanished between runs")

    def test_no_documented_key_stopped_being_emitted(self):
        for name, entry in self.live["contracts"].items():
            if name not in self.recorded["contracts"]:
                continue        # a new contract: the test above names it
            was = self.recorded["contracts"][name]["documented_not_emitted"]
            now = entry["documented_not_emitted"]
            self.assertEqual(
                was, now,
                f"{name}: keys the document declares and the tool does not "
                f"emit changed\n    was: {was}\n    now: {now}\n    "
                f"appeared: {sorted(set(now) - set(was))}")

    def test_no_emitted_key_stopped_being_documented(self):
        for name, entry in self.live["contracts"].items():
            if name not in self.recorded["contracts"]:
                continue        # a new contract: the test above names it
            was = self.recorded["contracts"][name]["emitted_not_documented"]
            now = entry["emitted_not_documented"]
            self.assertEqual(
                was, now,
                f"{name}: keys the tool emits and the document does not "
                f"declare changed\n    was: {was}\n    now: {now}\n    "
                f"appeared: {sorted(set(now) - set(was))}")

    def test_every_payload_sketch_still_parses(self):
        """A sketch the check cannot read would silently shrink the documented
        side, which is the narrowed denominator this row is against."""
        for name, entry in self.live["contracts"].items():
            self.assertEqual([], entry["unparsed_sketches"], name)


class TestTheCheckDiscriminatesInBothDirections(unittest.TestCase):
    """Anti-vacuity. A check written and never proved to fire is the failure
    this project keeps finding, so both directions are exercised against a
    page built for the purpose — no repository file is touched."""

    def compare(self, text: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            page = pathlib.Path(tmp) / "sixth-contract.md"
            page.write_text(text)
            return parity.compare(page)

    def test_a_documented_key_nothing_emits_is_named(self):
        result = self.compare(SIXTH.format(extra="no_such_key"))
        self.assertIn("no_such_key", result["documented_not_emitted"])

    def test_an_emitted_key_the_page_never_declares_is_named(self):
        """The same page declares two keys and `perry-decide list` emits eight
        at the top level, so the other six are the other direction."""
        result = self.compare(SIXTH.format(extra="no_such_key"))
        for emitted in ("decisions", "active", "total"):
            self.assertIn(emitted, result["emitted_not_documented"])

    def test_a_page_naming_no_command_is_refused_rather_than_scored_zero(self):
        with self.assertRaises(ValueError):
            parity.invoke("# a contract page with no command\n")


class TestWhatCouldNotBeComparedIsNamed(unittest.TestCase):
    """Point 4 of the deliverable. A key the check could not place is reported
    by name with its reason; it is never dropped, because a silently narrowed
    denominator is worse than a smaller one that is stated."""

    def test_every_unobservable_key_carries_a_reason(self):
        for name, entry in recorded()["contracts"].items():
            for key, why in entry["not_observable"].items():
                self.assertTrue(why.strip(), f"{name}: {key} has no reason")

    def test_the_report_prints_the_file_count_and_a_total(self):
        text = parity.report(recorded())
        self.assertIn("contract files discovered: ", text)
        self.assertIn("KR-O2.4 metric: ", text)
        for name in recorded()["contracts"]:
            self.assertIn(name, text)


if __name__ == "__main__":
    unittest.main()
