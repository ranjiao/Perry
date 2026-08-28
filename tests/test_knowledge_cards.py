"""`perry-lint --knowledge` — a card cannot exist without provenance.

DESIGN-006 § 5.3, phase A. All four provenance fields are mandatory, because
without them the knowledge store becomes a farm of confident errors that agents
then execute against — strictly worse than no store. That is the axiom *no
`done` without evidence*, extended to the knowledge layer.

Advisory here, refused at the write path (phase B), where the person who knows
the answer is still in the room.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
LINT = PERRY_HOME / "bin" / "perry-lint"
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())
CARD_SPEC = next(f for f in SCHEMA["files"] if f["id"] == "knowledge-card")
STALE_DAYS = SCHEMA["thresholds"]["knowledge_stale_days"]["value"]

GOOD = """# toolchain/pycache — a same-second edit leaves a stale .pyc

- Kind: knowledge
- Owner role: —
- Source: evidence/2026-08/note.md
- Last verified: {today}
- Invalidated by: CPython switching to hash-based .pyc validation by default

The claim.
"""

DIGEST = """# Some paper

> Id: SRC-1
> Source: https://example.invalid/p
> Received: 2026-08-01
> Status: active

Body.
"""


class Base(unittest.TestCase):
    def project(self, files: dict[str, str]) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- State root: .\n", encoding="utf-8")
        (root / "perry").mkdir(exist_ok=True)
        for rel, text in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        return root

    def run_lint(self, root: Path, *flags: str) -> dict:
        r = subprocess.run(
            [sys.executable, str(LINT), *flags, "--root", str(root), "--json"],
            capture_output=True, text=True)
        return json.loads(r.stdout)

    def knowledge(self, root: Path) -> dict:
        return self.run_lint(root, "--knowledge")

    def rules(self, out: dict) -> set[str]:
        return {f["rule"] for f in out["findings"]}


class TestACardWithoutProvenanceIsReported(Base):
    def test_a_complete_card_is_clean_and_counted(self):
        root = self.project({"knowledge/toolchain/pycache.md":
                             GOOD.format(today=date.today().isoformat()),
                             "evidence/2026-08/note.md": "x"})
        out = self.knowledge(root)
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["cards"], 1)

    def test_each_missing_provenance_field_is_named(self):
        """One finding per field, naming the field. A card missing three is
        three problems, not one."""
        for field in ("Source", "Last verified", "Invalidated by"):
            card = "\n".join(l for l in GOOD.format(today="2026-08-01").split("\n")
                             if not l.startswith(f"- {field}:"))
            root = self.project({"knowledge/t/c.md": card})
            out = self.knowledge(root)
            self.assertIn("card-no-provenance", self.rules(out), field)
            self.assertTrue(any(field in f["message"] for f in out["findings"]),
                            f"no finding names {field}: {out['findings']}")

    def test_an_unowned_card_is_its_own_finding_not_a_missing_field(self):
        """`Owner role: —` is legal before roles exist (DESIGN-006 phase C).
        Reporting it as a missing field would tell a pre-phase-C project to fix
        something it cannot fix yet, so it gets its own rule and its own
        wording."""
        root = self.project({"knowledge/t/c.md":
                             GOOD.format(today=date.today().isoformat()),
                             "evidence/2026-08/note.md": "x"})
        out = self.knowledge(root)
        self.assertNotIn("card-unowned", self.rules(out),
                         "an em dash owner is legal today and must not warn "
                         "until phase C lands")

    def test_a_source_that_resolves_nowhere_is_reported(self):
        card = GOOD.format(today=date.today().isoformat()).replace(
            "evidence/2026-08/note.md", "evidence/2026-08/does-not-exist.md")
        root = self.project({"knowledge/t/c.md": card})
        self.assertIn("card-source-dangling", self.rules(self.knowledge(root)))

    def test_a_source_naming_a_real_file_resolves(self):
        root = self.project({"knowledge/t/c.md":
                             GOOD.format(today=date.today().isoformat()),
                             "evidence/2026-08/note.md": "x"})
        self.assertNotIn("card-source-dangling", self.rules(self.knowledge(root)))

    def test_a_source_naming_a_digest_id_resolves(self):
        card = GOOD.format(today=date.today().isoformat()).replace(
            "evidence/2026-08/note.md", "SRC-1")
        root = self.project({"knowledge/t/c.md": card,
                             "knowledge/src/paper.md": DIGEST})
        self.assertNotIn("card-source-dangling", self.rules(self.knowledge(root)))


class TestStaleness(Base):
    def test_a_card_older_than_the_threshold_is_stale(self):
        old = (date.today() - timedelta(days=STALE_DAYS + 1)).isoformat()
        root = self.project({"knowledge/t/c.md": GOOD.format(today=old),
                             "evidence/2026-08/note.md": "x"})
        out = self.knowledge(root)
        self.assertIn("card-stale", self.rules(out))
        self.assertTrue(any("hash-based" in f["message"]
                            for f in out["findings"]),
                        "the finding must quote the tripwire, so the reader "
                        "checks whether it fired instead of re-dating the card")

    def test_a_card_inside_the_threshold_is_not_stale(self):
        recent = (date.today() - timedelta(days=STALE_DAYS - 1)).isoformat()
        root = self.project({"knowledge/t/c.md": GOOD.format(today=recent),
                             "evidence/2026-08/note.md": "x"})
        self.assertNotIn("card-stale", self.rules(self.knowledge(root)))

    def test_the_threshold_comes_from_the_schema(self):
        """Not a literal in the linter — two numbers for one rule is how the
        entry card and the linter disagreed about a stale run once already."""
        src = LINT.read_text(encoding="utf-8")
        self.assertIn("knowledge_stale_days", src)
        self.assertNotIn("age > 90", src)

    def test_impossible_dates_are_rejected_before_calendar_arithmetic(self):
        for value in ("2026-02-30", "2026-13-45", "2026-**09**-30"):
            with self.subTest(value=value):
                root = self.project({
                    "knowledge/t/c.md": GOOD.format(today=value),
                    "evidence/2026-08/note.md": "x"})
                out = self.knowledge(root)
                self.assertEqual(out["cards"], 1)
                self.assertNotIn("card-stale", self.rules(out))


class TestCardsAndDigestsDoNotReportEachOther(Base):
    """They share `knowledge/*/*.md`. Neither is malformed for not being the
    other, and the discriminator is declared once in the schema."""

    def setUp(self):
        self.root = self.project({
            "knowledge/t/card.md": GOOD.format(today=date.today().isoformat()),
            "knowledge/src/paper.md": DIGEST,
            "evidence/2026-08/note.md": "x"})

    def test_provenance_does_not_report_the_card_as_a_digest_with_no_id(self):
        out = self.run_lint(self.root, "--provenance")
        self.assertNotIn("source-has-no-id", {f["rule"] for f in out["findings"]},
                         f"a card was judged as a digest: {out['findings']}")

    def test_knowledge_does_not_report_the_digest_as_a_card(self):
        out = self.knowledge(self.root)
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["cards"], 1, "the digest was counted as a card")

    def test_the_discriminator_is_read_from_the_schema(self):
        self.assertEqual(CARD_SPEC["discriminator"]["field"], "Kind")
        self.assertIn("knowledge", CARD_SPEC["discriminator"]["values"])


class TestTheKRCannotBeSatisfiedByAnEmptySet(Base):
    def test_the_card_count_is_reported_alongside_the_violation_count(self):
        """`KR-O5.1` reads "lint live · 0 violations". Zero violations over
        zero cards is trivially true and cannot distinguish "provenance is
        enforced" from "nobody has written a card"."""
        empty = self.project({})
        self.assertEqual(self.knowledge(empty)["cards"], 0)
        self.assertEqual(self.knowledge(empty)["findings"], [])

    def test_perry_itself_has_at_least_one_card(self):
        """Otherwise this project's own KR is met by an empty set."""
        out = json.loads(subprocess.run(
            [sys.executable, str(LINT), "--knowledge", "--json"],
            capture_output=True, text=True, cwd=PERRY_HOME).stdout)
        self.assertGreater(out["cards"], 0,
                           "Perry declares KR-O5.1 and has written no card")
        self.assertEqual(out["findings"], [],
                         f"Perry's own cards violate its own check: "
                         f"{out['findings']}")


if __name__ == "__main__":
    unittest.main()
