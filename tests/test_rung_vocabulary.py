"""`V4` must be answerable by a session that has never seen this repository.

A user asked whether a newly-opened agent session would know what `V3` and `V4`
mean. The ladder **is** defined — `schema/state-schema.json § verification` —
and no prose page a session loads carried it or pointed at it, so the vocabulary
Perry uses most was reachable only by reading a JSON file nobody thinks to open.

`perry-explain` exists precisely for this: "an ID is write-optimized for the
wrong reader". Asked for `V4` it said **not found**, and offered `V4-1, V4-2,
V4-3` — id-shaped fragments scraped out of prose. The one token a fresh session
is least able to infer from a board cell was the one it could not resolve.

The rungs are read from the schema and **not restated** anywhere. A second copy
would be this repository's most-found defect applied to its own vocabulary, and
these tests assert the single source rather than the text.

Run: python3 tests/parallel test_rung_vocabulary
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPLAIN = ROOT / "bin" / "perry-explain"
SCHEMA = json.loads((ROOT / "schema" / "state-schema.json").read_text())


def explain(token, *extra):
    return subprocess.run([sys.executable, str(EXPLAIN), token, *extra],
                          capture_output=True, text=True, cwd=ROOT)


class TestEveryRungResolves(unittest.TestCase):
    def test_all_seven_answer(self):
        """Enumerated from the schema's own enum, not a list written here —
        an eighth rung must not be able to ship unexplainable."""
        rungs = SCHEMA["enums"]["verification_rung"]
        self.assertGreaterEqual(len(rungs), 7)
        for r in rungs:
            with self.subTest(rung=r):
                proc = explain(r)
                self.assertEqual(proc.returncode, 0, proc.stdout)
                self.assertIn("verification rung", proc.stdout)
                self.assertNotIn("not found", proc.stdout)

    def test_the_text_comes_from_the_schema_not_a_copy(self):
        """If someone restates a rung in the script, this goes red — which is
        the point. One definition, read at runtime."""
        for rung, text in SCHEMA["verification"]["rungs"].items():
            with self.subTest(rung=rung):
                self.assertIn(text.split(" - ")[0][:30], explain(rung).stdout)

    def test_it_names_where_the_definition_lives(self):
        """A reader who wants more than one line needs the path, not a claim."""
        self.assertIn("schema/state-schema.json", explain("V4").stdout)

    def test_the_two_governing_rules_travel_with_it(self):
        """Both are things a fresh session gets wrong by default: the rung is a
        function of CONSEQUENCE, and a V4 whose reviewer saw the reasoning is
        V1 wearing a costume."""
        out = explain("V4").stdout
        self.assertIn("costume", out)
        self.assertIn("CONSEQUENCE", out)


class TestItStaysAnIdResolver(unittest.TestCase):
    def test_a_rung_shaped_token_outside_the_ladder_is_not_invented(self):
        self.assertIn("not found", explain("V9").stdout)

    def test_the_schema_lookup_is_the_guard_not_the_regex(self):
        """The regex in `rung_entry` is a fast path and nothing else.

        Deleting it left every test green — `V9` and `ADR-001` still resolve
        correctly, because the `rungs` dict lookup decides. That is worth
        pinning: two things that look like one rule is how someone later
        relaxes the lookup on the grounds that the regex already validates.

        This asserts the property directly — a token the regex would admit but
        the ladder does not contain must still miss.
        """
        rungs = set(SCHEMA["verification"]["rungs"])
        absent = next((f"V{n}" for n in range(7) if f"V{n}" not in rungs), None)
        if absent is None:
            self.skipTest("the ladder currently fills V0–V6; nothing to probe")
        self.assertIn("not found", explain(absent).stdout)

    def test_json_mode_carries_the_same_answer(self):
        proc = explain("V5", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["id"], "V5")
        self.assertEqual(payload["kind"], "verification rung")

    def test_an_ordinary_id_still_resolves_normally(self):
        """The rung branch runs before the glossary lookup; a real project ID
        must not be shadowed by it."""
        proc = explain("ADR-001")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertNotIn("verification rung", proc.stdout)


if __name__ == "__main__":
    unittest.main()
