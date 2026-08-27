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

    def test_no_heading_names_a_collection_the_payload_does_not_carry(self):
        """A heading that names its collections is a claim about the payload,
        and a claim that does not check out is a failure here rather than a
        quiet fall-back to guessing. Renaming an emitted array without
        touching the page that documents it fails on this line."""
        for name, entry in self.live["contracts"].items():
            self.assertEqual([], entry["named_no_such_collection"], name)

    def test_the_idle_entry_table_lands_on_both_arrays(self):
        """The row this syntax was added for. `in_progress_with_no_live_run`
        and `review_idle` carry one entry shape on purpose, so no matcher can
        tell them apart — one key table names both, and both must be
        documented by it, not one of them and not neither."""
        task = self.live["contracts"]["perry-task/list/1.15"]
        for array in ("in_progress_with_no_live_run", "review_idle"):
            for key in ("id", "status", "last_event", "idle_hours",
                        "threshold_hours", "means"):
                path = f"conformance.{array}[].{key}"
                self.assertNotIn(path, task["emitted_not_documented"])
            self.assertFalse(
                [u for u in task["unassigned"] if array in u],
                f"the table naming {array} is back in unassigned")


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


#: Two collections with the SAME entry shape, both non-empty, and **one** key
#: table naming both in its heading. This is TASK-040's case — `cleared_items[]`
#: beside `items[]` — and no tool on disk emits it, so the payload is handed to
#: `compare()` directly rather than run.
#:
#: It is the primary evidence for this row **because the repository's own board
#: cannot be trusted to hold the tie**: the two idle arrays are non-empty only
#: while rows happen to be idle, and KR-O2.4 reads 12 or 0 for the same source
#: tree depending on that. The fixture holds the tie open on purpose.
TIED = {
    "contract": "perry-sixth/list/1.0",
    "open": 1,
    "items": [{"id": "R-1", "note": "live"}],
    "cleared_items": [{"id": "R-2", "note": "retired"}],
}

TIED_PAGE = """# `perry-decide list --json` — `perry-sixth/list/1.0`

## The payload

```jsonc
{{
  "contract": "perry-sixth/list/1.0",
  "open": 1,
  "items": [],
  "cleared_items": []
}}
```

#### {heading}

| Key | Type | Meaning |
|---|---|---|
| `id` | string | the row. |
| `note` | string | what it says. |
"""

#: Same tie, but the two collections hang under different parents, so a bare
#: `rows[]` in a heading names two of them.
AMBIGUOUS = {"a": {"rows": [{"id": "x", "note": "y"}]},
             "b": {"rows": [{"id": "x", "note": "y"}]}}


class TestAHeadingMayNameTheCollectionsItServes(unittest.TestCase):
    """One key table, several containers — and the refusal that keeps it honest.

    `place` scores a table's key set against every emitted container. Two
    collections built to share an entry shape are therefore the SAME key set,
    and the outcome depends on which of them the project's state happens to
    have filled that minute:

    - both non-empty — a tie, refused, every key unassigned and its emitted
      twin filed as undocumented;
    - one non-empty — no tie, the table silently lands on whichever one has
      rows, and the other is documented only by being unobservable;
    - both empty — refused again, and invisible because nothing is emitted.

    The gap is constant; only its visibility moves. A heading that names its
    collections settles it in the document, where the author already said it.
    """

    def compare(self, text: str, payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            page = pathlib.Path(tmp) / "sixth-contract.md"
            page.write_text(text)
            return parity.compare(page, payload=payload)

    def test_one_table_naming_both_arrays_documents_both(self):
        """TASK-040's case, which is the acceptance test for this row: two
        identically-shaped arrays and ONE key table, 0 and 0."""
        result = self.compare(
            TIED_PAGE.format(
                heading="The entry — `items[]` and `cleared_items[]`"), TIED)
        self.assertEqual([], result["documented_not_emitted"])
        self.assertEqual([], result["emitted_not_documented"])
        self.assertEqual([], result["unassigned"])
        self.assertEqual([], result["named_no_such_collection"])

    def test_the_same_table_naming_nothing_is_still_unassigned(self):
        """The half that keeps the instrument honest. Identical payload,
        identical table — the heading is the only difference, and without it
        the tie is refused exactly as before."""
        result = self.compare(
            TIED_PAGE.format(heading="The entry, key by key"), TIED)
        self.assertEqual(
            ["The entry, key by key § id", "The entry, key by key § note"],
            result["unassigned"])
        self.assertEqual(
            ["cleared_items[].id", "cleared_items[].note",
             "items[].id", "items[].note"],
            result["emitted_not_documented"])

    def test_a_heading_naming_a_collection_the_payload_lacks_is_a_failure(self):
        """Not a silent pass and not a fall-back to guessing: the author said
        where the table hangs, so a name that resolves to nothing is reported
        and the table stays unassigned."""
        result = self.compare(
            TIED_PAGE.format(heading="The entry — `ghosts[]`"), TIED)
        self.assertEqual(1, len(result["named_no_such_collection"]))
        self.assertIn("`ghosts[]`", result["named_no_such_collection"][0])
        self.assertIn("no such collection",
                      result["named_no_such_collection"][0])
        self.assertEqual(2, len(result["unassigned"]))
        self.assertIn("items[].id", result["emitted_not_documented"])

    def test_one_bad_name_beside_a_good_one_refuses_the_whole_table(self):
        """Half a stated intent is not a licence to act on the other half."""
        result = self.compare(
            TIED_PAGE.format(heading="The entry — `items[]` and `ghosts[]`"),
            TIED)
        self.assertEqual(1, len(result["named_no_such_collection"]))
        self.assertEqual(2, len(result["unassigned"]))
        self.assertIn("items[].id", result["emitted_not_documented"])

    def test_a_name_matching_two_collections_is_a_failure_not_a_pick(self):
        result = self.compare(
            TIED_PAGE.format(heading="The entry — `rows[]`"), AMBIGUOUS)
        self.assertEqual(1, len(result["named_no_such_collection"]))
        for expected in ("a.rows[]", "b.rows[]"):
            self.assertIn(expected, result["named_no_such_collection"][0])
        self.assertEqual(2, len(result["unassigned"]))

    def test_a_name_is_matched_on_a_whole_segment(self):
        """`items[]` must not swallow `cleared_items[]`, or the ambiguity
        refusal above would fire on the very case this row exists to allow."""
        boxes = parity.containers(parity.paths(TIED), parity.empty_lists(TIED))
        self.assertEqual(
            parity.Placement(["items[]"], True, []),
            parity.named_boxes("The entry — `items[]`", boxes))

    def test_a_bare_name_without_brackets_is_not_a_collection_reference(self):
        """`` `asks` — `## User Input Queue` `` names the section an entry
        table belongs to; the entries hang under `asks.items[]`. Reading a
        bare backticked word as a container is how the check would start
        inventing findings against the wrong object."""
        boxes = parity.containers(parity.paths(TIED), parity.empty_lists(TIED))
        self.assertEqual(parity.Placement([], False, []),
                         parity.named_boxes("`items` — the open ones", boxes))

    def test_the_live_roles_page_names_no_collection_and_stays_unassigned(self):
        """On real data, not a fixture: `roles.cards` is empty in this project
        and its key table's heading names nothing, so it is still reported by
        name rather than guessed onto something."""
        entry = parity.compare(parity.ROOT / "schema"
                               / "roles-list-contract.md")
        self.assertEqual(6, len(entry["unassigned"]))
        self.assertTrue(all(u.startswith("A card — the six frozen fields")
                            for u in entry["unassigned"]))


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
