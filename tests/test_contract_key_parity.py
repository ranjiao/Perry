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

**A key inside a collection this project leaves empty was never in either
count.** `not_observable` said so honestly and that meant nothing had ever
checked it — 15 keys in four collections on 2026-08-27, with both numbers
reading 0. `tests/fixtures/witness-project` is read for those keys, and
`TestAWitnessProjectMakesAnEmptyCollectionObservable` plus
`TestTheWitnessedKeysRedden` hold the four collections open and prove one key
of each is compared: the same page mutation is named with the witness and
silent without it.

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
        task = self.live["contracts"]["perry-task/list/1.17"]
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

    def test_the_named_table_reads_the_same_however_full_the_arrays_are(self):
        """The oscillation, and the end of it.

        Inference reads the *state*: with both arrays full it ties and refuses,
        with one full it lands on that one, with both empty it refuses again
        and nothing is emitted to miss — so the same page and the same code
        measure 4, 0 and 0. A heading names collections, not rows, and an empty
        array is still a collection, so all three states now read 0.
        """
        named = "The entry — `items[]` and `cleared_items[]`"
        for label, payload in (
                ("both non-empty", TIED),
                ("one non-empty", dict(TIED, cleared_items=[])),
                ("both empty", dict(TIED, items=[], cleared_items=[]))):
            with self.subTest(label):
                bare = self.compare(
                    TIED_PAGE.format(heading="The entry, key by key"), payload)
                result = self.compare(TIED_PAGE.format(heading=named), payload)
                self.assertEqual([], result["emitted_not_documented"], label)
                self.assertEqual([], result["documented_not_emitted"], label)
                self.assertEqual([], result["unassigned"], label)
                if label == "one non-empty":
                    self.assertEqual(
                        ["items[]"],
                        parity.place(["id", "note"], parity.containers(
                            parity.paths(payload),
                            parity.empty_lists(payload))).boxes,
                        "the state-reading placement this test exists about "
                        "has changed shape")
                    self.assertEqual([], bare["emitted_not_documented"],
                                     "and it reads clean, which is the trap")

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


#: The collections Perry's own board leaves empty, the contract page that
#: documents each, and ONE key of each entry to delete in the mutation below.
#: Measured 2026-08-27: **15 keys across the first four**, every one of them in
#: `not_observable` and none of them ever compared against a payload.
#:
#: `review_idle` is the fifth and is here for the general case rather than for
#: tonight's reading: it is `in_progress_with_no_live_run`'s twin by design,
#: it happens to be non-empty on this board right now, and the day it empties
#: is the day its six keys would have gone dark. The witness holds it open
#: either way — which is what "the reading no longer depends on which rows are
#: idle this minute" has to mean if it means anything.
#:
#: `mutate` is the text to remove from the page — a real declaration on the
#: real page, not a marker put there for the test.
WITNESSED = (
    ("perry-decide/list/1.0", "decide-list-contract.md", "expired_sunsets",
     "expired_sunsets[].sunset", ', "sunset": "2026-06-30"'),
    ("perry-goals/list/2.1", "goals-list-contract.md",
     "krs[].current_staleness.moved_tasks",
     "krs[].current_staleness.moved_tasks[].at",
     ',\n                           "at": "2026-08-21T09:10:00"'),
    ("perry-task/list/1.17", "task-list-contract.md",
     "conformance.depends_on_unknown",
     "conformance.depends_on_unknown[].unknown",
     "| `unknown` | array | the dependency ids"),
    ("perry-task/list/1.17", "task-list-contract.md",
     "conformance.in_progress_with_no_live_run",
     "conformance.in_progress_with_no_live_run[].means",
     "| `means` | string | the sentence to show a reader."),
    ("perry-task/list/1.17", "task-list-contract.md",
     "conformance.review_idle", "conformance.review_idle[].means", ""),
    ("perry-task/list/1.17", "task-list-contract.md",
     "tasks[].evidence_relations", "tasks[].evidence_relations[].kind", ""),
)

#: The four that were unobservable when this row was opened, and the mutation
#: each was proved with. Two entries above carry no mutation and are excluded,
#: for opposite reasons:
#:
#: - `review_idle`'s keys are observable from the live board today, so deleting
#:   a row of the shared idle table is already caught without the witness.
#: - `tasks[].evidence_relations` (1.17) is observable from the live board
#:   **only when the first open row happens to carry an evidence cell** — a
#:   payload lists an entry shape from its FIRST element, and 4 of this board's
#:   36 open rows carry one. Asserting it unobservable-without-the-witness
#:   would pin a reading that flips with row order, which is the oscillation
#:   the witness exists to remove; the witness holds `WIT-001`'s cell open so
#:   the three keys are compared either way.
MUTATED = tuple(w for w in WITNESSED if w[4])


class TestAWitnessProjectMakesAnEmptyCollectionObservable(unittest.TestCase):
    """TASK-132. A key inside a collection this project leaves empty has no
    entry to be compared against, so it lands in `not_observable` and **nothing
    has ever checked it**. On 2026-08-27 that was 15 keys in four collections,
    and KR-O2.4 read 0 with all fifteen unverified — which is TASK-176's
    oscillation wearing an honest label.

    `tests/fixtures/witness-project` is a second project whose own state puts
    those collections in a non-empty state, read by the same commands. Nothing
    is written into a payload: the fixture holds a decision past its sunset, a
    dependency on an id no register carries, an `in_progress` row nothing has
    moved, a `review` row nobody has ruled on, and a linkage register older
    than its event log — and the real tools derive the entries from those files.
    """

    def setUp(self):
        self.live = parity.measure()
        self.blind = parity.measure(witness=None)

    def witness_payload(self, contract: str) -> dict:
        page = parity.ROOT / "schema" / dict(
            (c, f) for c, f, *_ in WITNESSED)[contract]
        argv, subtree = parity.invoke(page.read_text())
        return parity.run(argv, parity.WITNESS, subtree, "witness")

    def collection(self, payload: dict, path: str):
        """Walk a dotted path, stepping through `krs[]` as `krs[0]`."""
        node = payload
        for segment in path.split("."):
            if segment.endswith("[]"):
                node = node[segment[:-2]]
                self.assertTrue(node, f"{segment} is empty in the witness")
                node = node[0]
            else:
                node = node[segment]
        return node

    def test_the_witness_project_still_holds_every_condition_open(self):
        """The fixture is the instrument, and it is asserted against the
        WITNESS PROJECT rather than against the live board — an edit that
        resolves `WIT-404` or closes `WIT-001` must fail here whatever Perry's
        own board happens to be doing that minute."""
        for contract, _, collection, _, _ in WITNESSED:
            with self.subTest(collection):
                self.assertTrue(
                    self.collection(self.witness_payload(contract), collection),
                    f"{collection} is empty in {parity.WITNESS} — see that "
                    f"project's README for what produces it; do not fix the "
                    f"finding, it IS the deliverable")

    def test_every_key_in_those_collections_is_actually_compared(self):
        """Not merely reported as reachable: on the same footing as a key the
        live board emits, which means a disagreement with the page lands in one
        of the two gap lists. Proved by mutation below.

        Deliberately silent about WHICH project supplied the entry — the live
        board filling one of these collections is a fine reason for the witness
        not to be consulted, and a test that demanded the witness every time
        would be reading the board again."""
        for contract, _, _, key, _ in WITNESSED:
            with self.subTest(key):
                entry = self.live["contracts"][contract]
                self.assertNotIn(key, entry["not_observable"])
                self.assertNotIn(key, entry["documented_not_emitted"])
                self.assertNotIn(key, entry["emitted_not_documented"])

    def test_without_the_witness_the_four_are_unobservable(self):
        """Anti-vacuity, and the measurement this row was opened on. Reading
        `--root` alone puts all four back in `not_observable` with a reason —
        so they are checked *because of* the witness, not because they were
        fine anyway."""
        for contract, _, collection, key, _ in MUTATED:
            with self.subTest(key):
                entry = self.blind["contracts"][contract]
                self.assertIn(key, entry["not_observable"])
                self.assertIn(collection, entry["not_observable"][key])

    def test_the_witness_supplies_an_entry_shape_and_never_a_placement(self):
        """The narrowing that keeps this from being the same defect in a new
        costume. A fixture project's shape must not decide where a live page's
        key table hangs, or the ruler moves with something other than what it
        measures. `unassigned` is therefore identical with and without it —
        roles' six frozen fields and task's eight `asks` rows stay exactly
        where they were."""
        for name, entry in self.live["contracts"].items():
            with self.subTest(name):
                self.assertEqual(self.blind["contracts"][name]["unassigned"],
                                 entry["unassigned"])
                self.assertEqual(
                    self.blind["contracts"][name]["named_no_such_collection"],
                    entry["named_no_such_collection"])

    def test_not_observable_still_names_anything_left_uncovered(self):
        """The reporting is not deleted and not weakened — it is how this row
        was found. Whatever the witness cannot show is still named with the
        reason, and the reason now says which of the two projects left it
        empty."""
        for name, entry in self.blind["contracts"].items():
            for key, why in entry["not_observable"].items():
                self.assertTrue(why.strip(), f"{name}: {key} has no reason")
        for name, entry in self.live["contracts"].items():
            for key, why in entry["not_observable"].items():
                self.assertIn("empty in this run", why, f"{name}: {key}")
                self.assertIn(parity.WITNESS, why, f"{name}: {key}")


class TestTheWitnessedKeysRedden(unittest.TestCase):
    """Verification 2, one key per collection that was unobservable: delete a
    real declaration from a copy of the real page and the check must name the
    key. Without the witness each of these mutations is silent, which is
    exactly what `not_observable` cost."""

    def mutate(self, page: str, removed: str, witness) -> dict:
        source = parity.ROOT / "schema" / page
        text = source.read_text()
        self.assertIn(removed, text,
                      f"{page} no longer contains the declaration this "
                      f"mutation removes")
        with tempfile.TemporaryDirectory() as tmp:
            copy = pathlib.Path(tmp) / page
            copy.write_text(text.replace(removed, "", 1))
            return parity.compare(copy, witness=witness)

    def test_removing_a_witnessed_key_from_its_page_is_reported(self):
        for contract, page, _, key, removed in MUTATED:
            with self.subTest(key):
                result = self.mutate(page, removed, parity.WITNESS)
                self.assertIn(
                    key, result["emitted_not_documented"],
                    f"{page} no longer declares {key} and the check said "
                    f"nothing — the key is reported as observable and is not "
                    f"being compared")

    def test_the_same_mutation_is_silent_without_the_witness(self):
        """The cost of `not_observable`, stated as a test rather than as a
        paragraph: the identical page defect passes cleanly when the only
        project read is one that leaves the collection empty."""
        for contract, page, _, key, removed in MUTATED:
            with self.subTest(key):
                result = self.mutate(page, removed, None)
                self.assertNotIn(key, result["emitted_not_documented"])
                self.assertNotIn(key, result["documented_not_emitted"])


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
