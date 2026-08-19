"""`bin/perry-knowledge` — the capture point writes a card, or refuses.

DESIGN-006 § 5.4, phase B. Phase A made a card's provenance *checkable*; this
is where it becomes *refusable*, because the write is the one moment the person
who knows the answer is still in the room.

Two rules carry the whole phase and both are pinned here:

- **Evidence proposes; the user declares.** `propose` is read-only and only
  says whether the capture point should fire; nothing reaches `knowledge/`
  except through `promote`, which runs after a user chose it.
- **A sourceless card is refused, not written blank.** `perry-lint --knowledge`
  reports one afterwards. This refuses it now.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
TOOL = PERRY_HOME / "bin" / "perry-knowledge"
LINT = PERRY_HOME / "bin" / "perry-lint"
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())
CARD_SPEC = next(f for f in SCHEMA["files"] if f["id"] == "knowledge-card")
INDEX_TEMPLATE = PERRY_HOME / "work" / "state" / "knowledge_INDEX_TEMPLATE.md"

EVIDENCE = """# TASK-001 — the monthly export double-counted every tenant row

The export joined `tenants` without excluding rows flagged `is_test`.
"""

SRC = "evidence/2026-08/TASK-001-export-fix.md"


class Base(unittest.TestCase):
    def project(self, extra: dict[str, str] | None = None,
                index: bool = True) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- State root: .\n", encoding="utf-8")
        (root / "evidence" / "2026-08").mkdir(parents=True)
        (root / "evidence" / "2026-08" / "TASK-001-export-fix.md").write_text(
            EVIDENCE, encoding="utf-8")
        (root / "knowledge").mkdir()
        if index:
            (root / "knowledge" / "INDEX.md").write_text(
                INDEX_TEMPLATE.read_text(encoding="utf-8")
                .replace("{{project name}}", "demo")
                .replace("{{YYYY-MM-DD}}", "2026-08-01"), encoding="utf-8")
        for rel, text in (extra or {}).items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        if (root / "BOARD.md").exists():
            seeded = subprocess.run(
                [sys.executable, str(PERRY_HOME / "bin" / "perry-tasks"),
                 "write", "--from-board", "--root", str(root)],
                capture_output=True, text=True)
            if seeded.returncode:
                raise AssertionError(seeded.stdout + seeded.stderr)
        return root

    def run_tool(self, root: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(TOOL), *args, "--root", str(root)],
            capture_output=True, text=True)

    def promote(self, root: Path, **kw) -> subprocess.CompletedProcess:
        """A complete, valid promotion, minus whatever the caller sets to None."""
        args = {"--topic": "reporting", "--slug": "test-tenants",
                "--claim": "the monthly export must exclude test tenants",
                "--source": SRC,
                "--invalidated-by": "the tenants table stops carrying is_test"}
        for k, v in kw.items():
            flag = "--" + k.replace("_", "-")
            if v is None:
                args.pop(flag, None)
            else:
                args[flag] = v
        flat: list[str] = []
        for k, v in args.items():
            flat += [k, v]
        return self.run_tool(root, "promote", *flat)

    def knowledge_lint(self, root: Path) -> dict:
        r = subprocess.run(
            [sys.executable, str(LINT), "--knowledge", "--root", str(root),
             "--json"], capture_output=True, text=True)
        return json.loads(r.stdout)


class TestASourcelessCardIsRefused(Base):
    """The rule phase A could only report. Four shapes of "no source", because
    the interesting one is not the missing flag — it is the dash, which looks
    like an answer and is the value a template hands you."""

    def test_a_missing_source_is_refused_and_nothing_is_written(self):
        root = self.project()
        r = self.promote(root, source=None)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("--source is required", r.stderr)
        self.assertFalse((root / "knowledge" / "reporting").exists(),
                         "a refused promotion created the topic directory")

    def test_a_dash_does_not_satisfy_the_source(self):
        for dash in ("—", "-", "TBD", "n/a"):
            with self.subTest(dash=dash):
                root = self.project()
                r = self.promote(root, source=dash)
                self.assertEqual(r.returncode, 1)
                self.assertIn("--source is required", r.stderr)

    def test_a_source_that_resolves_nowhere_is_refused(self):
        root = self.project()
        r = self.promote(root, source="evidence/2026-08/never-written.md")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("resolves to no file", r.stderr)
        self.assertFalse(list((root / "knowledge").rglob("test-tenants.md")))

    def test_the_refusal_is_the_same_rule_the_linter_reports(self):
        """One implementation. A card the linter calls dangling and the writer
        accepts is how a project ends up trusting neither."""
        root = self.project()
        card = root / "knowledge" / "reporting" / "hand-written.md"
        card.parent.mkdir(parents=True)
        card.write_text(
            "# reporting/hand-written — a claim\n\n"
            "- Kind: knowledge\n- Owner role: —\n"
            "- Source: evidence/2026-08/never-written.md\n"
            f"- Last verified: {date.today():%Y-%m-%d}\n"
            "- Invalidated by: something observable\n\nBody.\n",
            encoding="utf-8")
        self.assertIn("card-source-dangling",
                      {f["rule"] for f in self.knowledge_lint(root)["findings"]})
        r = self.promote(root, slug="tool-written",
                         source="evidence/2026-08/never-written.md")
        self.assertEqual(r.returncode, 1,
                         "the writer accepted a source the linter reports")


class TestTheOtherMandatoryFields(Base):
    def test_a_card_without_a_tripwire_is_refused(self):
        """`Invalidated by` is what makes a card revisable instead of
        accumulating. Without it the card goes stale in silence, which is the
        failure the whole schema exists for."""
        root = self.project()
        r = self.promote(root, invalidated_by=None)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("--invalidated-by is required", r.stderr)

    def test_a_card_without_a_claim_is_refused(self):
        root = self.project()
        r = self.promote(root, claim=None)
        self.assertEqual(r.returncode, 1)
        self.assertIn("--claim is required", r.stderr)

    def test_a_kind_off_the_declared_set_is_refused(self):
        root = self.project()
        r = self.promote(root, kind="runbook")
        self.assertEqual(r.returncode, 1)
        self.assertIn("not one of", r.stderr)

    def test_both_declared_kinds_are_accepted(self):
        """Anti-vacuity for the check above: the enum comes from the schema,
        so a test that only proves rejection would pass on an empty enum."""
        kinds = CARD_SPEC["discriminator"]["values"]
        self.assertIn("source-of-truth", kinds)
        for i, kind in enumerate(kinds):
            with self.subTest(kind=kind):
                root = self.project()
                r = self.promote(root, kind=kind, slug=f"card-{i}")
                self.assertEqual(r.returncode, 0, r.stderr)
                text = (root / "knowledge" / "reporting" /
                        f"card-{i}.md").read_text()
                self.assertIn(f"- Kind: {kind}", text)

    def test_a_card_is_never_silently_overwritten(self):
        root = self.project()
        self.assertEqual(self.promote(root).returncode, 0)
        before = (root / "knowledge" / "reporting" / "test-tenants.md").read_text()
        r = self.promote(root, claim="something else entirely")
        self.assertEqual(r.returncode, 1)
        self.assertIn("already exists", r.stderr)
        self.assertEqual(
            (root / "knowledge" / "reporting" / "test-tenants.md").read_text(),
            before, "a refused promotion still changed the record")


class TestARealCloseProducesACard(Base):
    """V3, end to end: `perry-task done` writes the evidence citation, the
    capture point pre-fills `Source:` from it, and `perry-lint --knowledge`
    reports the result clean."""

    BOARD = ("# Task board — demo\n\n## Active\n\n"
             "| ID | Title | Owner | Status | Priority | Evidence | Notes |\n"
             "|---|---|---|---|---|---|---|\n"
             "| TASK-001 | Fix the monthly export | Coding Agent | in_progress "
             "| P1 | — | — |\n")

    def test_close_then_promote_then_lint(self):
        root = self.project({"BOARD.md": self.BOARD})
        close = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-task"), "done",
             "TASK-001", "--evidence", SRC, "--rung", "V3",
             "--root", str(root)], capture_output=True, text=True)
        self.assertEqual(close.returncode, 0, close.stderr)

        prop = self.run_tool(root, "propose", "--source", SRC, "--rung", "V3",
                             "--json")
        self.assertEqual(prop.returncode, 0, prop.stderr)
        payload = json.loads(prop.stdout)
        self.assertTrue(payload["fires"], payload)
        self.assertEqual(payload["prefill"]["Source"], SRC,
                         "`Source:` was not pre-filled from the evidence")
        self.assertEqual(payload["prefill"]["Last verified"],
                         f"{date.today():%Y-%m-%d}")

        r = self.promote(root, source=payload["prefill"]["Source"])
        self.assertEqual(r.returncode, 0, r.stderr)
        card = root / "knowledge" / "reporting" / "test-tenants.md"
        self.assertTrue(card.exists())

        text = card.read_text()
        for field in (h["name"] for h in CARD_SPEC["header_fields"]):
            self.assertRegex(text, rf"(?m)^- {field}: \S",
                             f"`{field}` was written blank")

        out = self.knowledge_lint(root)
        self.assertEqual(out["findings"], [], out)
        self.assertEqual(out["cards"], 1)

    def test_a_closed_task_id_still_resolves_as_a_source(self):
        """`perry-task done` REMOVES the board row, so the id survives only in
        `.perry/events.jsonl` — which lives under the project root, not the
        state root. Deriving one from the other is the bug this pins."""
        root = self.project({"BOARD.md": self.BOARD})
        subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-task"), "done",
             "TASK-001", "--evidence", SRC, "--rung", "V3",
             "--root", str(root)], capture_output=True, text=True, check=True)
        self.assertNotIn("TASK-001", (root / "BOARD.md").read_text())
        r = self.promote(root, source="TASK-001")
        self.assertEqual(r.returncode, 0, r.stderr)


class TestWhenTheCapturePointDoesNotFire(Base):
    """Most closes produce nothing durable. A question that fires on every one
    is a question people learn to dismiss, and then it fires on the one that
    mattered."""

    def propose(self, root: Path, *args: str) -> dict:
        r = self.run_tool(root, "propose", *args, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_no_evidence_means_no_question(self):
        root = self.project()
        out = self.propose(root, "--source", "—")
        self.assertFalse(out["fires"])
        self.assertEqual(out["reason"], "no-source")

    def test_an_unresolvable_citation_means_no_question(self):
        root = self.project()
        out = self.propose(root, "--source", "evidence/2026-08/nope.md")
        self.assertFalse(out["fires"])
        self.assertEqual(out["reason"], "source-unresolvable")

    def test_a_self_attested_close_means_no_question(self):
        """V0/V1 is the agent attesting its own artifact. A claim whose
        provenance bottoms out there is the confident error the card schema
        exists to keep out."""
        root = self.project()
        for rung in ("V0", "V1"):
            with self.subTest(rung=rung):
                out = self.propose(root, "--source", SRC, "--rung", rung)
                self.assertFalse(out["fires"])
                self.assertEqual(out["reason"], "rung-unverified")

    def test_a_verified_close_does_fire(self):
        """The complement, and the anti-vacuity guard: a rung floor that
        rejected everything would pass every test above."""
        root = self.project()
        for rung in ("V2", "V3", "V5"):
            with self.subTest(rung=rung):
                out = self.propose(root, "--source", SRC, "--rung", rung)
                self.assertTrue(out["fires"], out)
                self.assertEqual(out["reason"], "ready")

    def test_asking_twice_about_one_source_is_the_nag_this_avoids(self):
        root = self.project()
        self.assertEqual(self.promote(root).returncode, 0)
        out = self.propose(root, "--source", SRC, "--rung", "V3")
        self.assertFalse(out["fires"])
        self.assertEqual(out["reason"], "already-promoted")
        self.assertEqual(out["existing"], ["knowledge/reporting/test-tenants.md"])

    def test_propose_writes_nothing_at_all(self):
        """Read-only is the half of `evidence proposes` a tool can enforce."""
        root = self.project()
        before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
        for rung in ("V1", "V3"):
            self.propose(root, "--source", SRC, "--rung", rung)
        after = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
        self.assertEqual(before, after, "`propose` touched the project")

    def test_dry_run_writes_nothing(self):
        root = self.project()
        before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
        # `--dry-run` takes no value; the helper passes flags in pairs, so the
        # invocation is spelled out here instead.
        r = self.run_tool(
            root, "promote", "--topic", "reporting", "--slug", "test-tenants",
            "--claim", "a claim", "--source", SRC,
            "--invalidated-by", "a tripwire", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        after = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)


class TestTheIndexIsPatchedAndNothingElseIs(Base):
    def test_only_the_cards_section_changes(self):
        root = self.project()
        idx = root / "knowledge" / "INDEX.md"
        before = idx.read_text()
        self.assertEqual(self.promote(root).returncode, 0)
        after = idx.read_text()

        def section(text: str, name: str) -> str:
            head = text.index(f"## {name}")
            rest = text.find("\n## ", head + 1)
            return text[head:rest if rest != -1 else len(text)]

        for untouched in ("Eternal (project constitution; never archived)",
                          "Active by topic", "Archived"):
            self.assertEqual(section(before, untouched),
                             section(after, untouched),
                             f"`## {untouched}` is the digest flow's section "
                             f"and the card writer rewrote it")
        cards = section(after, "Cards by topic")
        self.assertIn("### reporting (1)", cards)
        self.assertIn("test-tenants — the monthly export must exclude test "
                      "tenants (verified", cards)
        self.assertNotIn("(no cards yet)", cards)
        self.assertIn("<!-- A card is a CLAIM", cards,
                      "the template's format hint was dropped on rebuild")

    def test_an_absent_index_is_reported_and_not_invented(self):
        """A cards-only INDEX.md would assert "(no digests yet)" about a tree
        this tool never looked at."""
        root = self.project(index=False)
        r = self.run_tool(
            root, "promote", "--topic", "reporting", "--slug", "x",
            "--claim", "a claim", "--source", SRC,
            "--invalidated-by", "a tripwire", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            json.loads(r.stdout)["index"],
            {"updated": False, "reason": "absent",
             # `--root` is resolved by the tool, so the reported path is the
             # real one; on macOS `/var` is a symlink to `/private/var`.
             "path": str((root / "knowledge" / "INDEX.md").resolve())})
        self.assertFalse((root / "knowledge" / "INDEX.md").exists())
        self.assertTrue((root / "knowledge" / "reporting" / "x.md").exists())


class TestOwnerRole(Base):
    """`Owner role` is the field that is legitimately a dash — until roles
    exist. Then a blank means nobody re-verifies the claim (DESIGN-006 § 5.3)."""

    ROLE = ("# Role · finance\n\n- Accepted by: user\n\n## Context\nx\n\n"
            "## Loads\n- knowledge: reporting\n\n## May touch\n- write: x\n\n"
            "## Must escalate\n- any `payment`\n")

    def test_no_roles_declared_writes_the_dash(self):
        root = self.project()
        self.assertEqual(self.promote(root).returncode, 0)
        self.assertIn("- Owner role: —",
                      (root / "knowledge" / "reporting" / "test-tenants.md")
                      .read_text())

    def test_one_role_declared_is_derived_not_asked(self):
        root = self.project({".perry/roles/finance.md": self.ROLE})
        self.assertEqual(self.promote(root).returncode, 0, "one role, one right "
                         "answer — asking for it would be a second prompt")
        self.assertIn("- Owner role: finance",
                      (root / "knowledge" / "reporting" / "test-tenants.md")
                      .read_text())

    def test_several_roles_and_no_owner_is_refused(self):
        root = self.project({".perry/roles/finance.md": self.ROLE,
                             ".perry/roles/legal.md": self.ROLE})
        r = self.promote(root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("--owner-role is required", r.stderr)

    def test_an_owner_that_names_no_role_card_is_refused(self):
        root = self.project({".perry/roles/finance.md": self.ROLE})
        r = self.promote(root, owner_role="marketing")
        self.assertEqual(r.returncode, 1)
        self.assertIn("names no card in .perry/roles/", r.stderr)


class TestTheProjectRootIsPassedNotDerived(Base):
    """A phase-A defect the write path could not live with.

    `resolve_state_root` returns the PROJECT root by default, so on every
    project that has not moved its state — the common case, `State root: .` —
    `state_root.parent` names the directory *above* the project. Two checks
    read `.perry/` through that expression, and `.perry/` never moves.

    Neither was covered: phase A's fixture is flat, so `card-unowned` could not
    fire in it at all, and no test cited a task id whose row had been closed.
    """

    ROLE = ("# Role · finance\n\n- Accepted by: user\n\n## Context\nx\n\n"
            "## Loads\n- knowledge: reporting\n\n## May touch\n- write: x\n\n"
            "## Must escalate\n- any `payment`\n")

    def card(self, source: str, owner: str = "—") -> str:
        return (f"# reporting/c — a claim\n\n- Kind: knowledge\n"
                f"- Owner role: {owner}\n- Source: {source}\n"
                f"- Last verified: {date.today():%Y-%m-%d}\n"
                f"- Invalidated by: something observable\n\nBody.\n")

    def test_an_unowned_card_is_reported_once_roles_exist(self):
        root = self.project({".perry/roles/finance.md": self.ROLE,
                             "knowledge/reporting/c.md": self.card(SRC)})
        self.assertIn("card-unowned",
                      {f["rule"] for f in self.knowledge_lint(root)["findings"]},
                      "`.perry/roles/` was looked for above the project root, "
                      "so the finding could never fire on a flat layout")

    def test_an_owned_card_is_not_reported(self):
        """The complement — without it the check above passes on a rule that
        fires on every card."""
        root = self.project({".perry/roles/finance.md": self.ROLE,
                             "knowledge/reporting/c.md":
                                 self.card(SRC, owner="finance")})
        self.assertNotIn("card-unowned",
                         {f["rule"] for f
                          in self.knowledge_lint(root)["findings"]})

    def test_a_card_citing_a_closed_task_is_not_dangling(self):
        """The id survives only in `.perry/events.jsonl`, under the project
        root."""
        root = self.project({
            "BOARD.md": TestARealCloseProducesACard.BOARD,
            "knowledge/reporting/c.md": self.card("TASK-001")})
        subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-task"), "done",
             "TASK-001", "--evidence", SRC, "--rung", "V3",
             "--root", str(root)], capture_output=True, text=True, check=True)
        self.assertNotIn(
            "card-source-dangling",
            {f["rule"] for f in self.knowledge_lint(root)["findings"]},
            "the event log was looked for above the project root")


class TestTheCapturePointsCiteTheOneProcedure(Base):
    """Three capture points, one procedure. Three copies of a rule is how the
    third one drifts, and this repo has the scars."""

    PROCEDURE = PERRY_HOME / "work" / "reference" / "promotion.md"

    def test_the_procedure_exists_and_names_the_rule(self):
        text = self.PROCEDURE.read_text(encoding="utf-8")
        self.assertIn("Evidence proposes; the user declares", text)
        self.assertIn("refused, not written blank", text)

    def test_each_capture_point_routes_to_it(self):
        for rel, anchor in (
                ("work/reference/subcommands.md", "### `close-task <id>`"),
                ("work/reference/subcommands.md", "### `end-phase-retro`"),
                ("packs/software-ops/incidents.md",
                 "### `/pmo incident close <slug>`")):
            with self.subTest(anchor=anchor):
                text = (PERRY_HOME / rel).read_text(encoding="utf-8")
                start = text.index(anchor)
                nxt = text.find("\n### ", start + 1)
                block = text[start:nxt if nxt != -1 else len(text)]
                self.assertIn("promotion.md", block,
                              f"{anchor} does not route to the one procedure")
                self.assertIn("perry-knowledge", block,
                              f"{anchor} does not name the writer")

    def test_no_capture_point_tells_an_agent_to_write_the_card_by_hand(self):
        for rel in ("work/reference/subcommands.md",
                    "packs/software-ops/incidents.md",
                    "work/reference/promotion.md"):
            text = (PERRY_HOME / rel).read_text(encoding="utf-8")
            self.assertNotIn("write the card to `knowledge/", text)

    def test_the_incident_gate_stays_at_three_questions(self):
        """The promotion is an OPTION inside Q1, not a Q4. One question at an
        existing gate is the whole affordance budget (DESIGN-006 § 7)."""
        text = (PERRY_HOME / "packs" / "software-ops" / "incidents.md").read_text()
        self.assertIn("**Q3**", text)
        self.assertNotIn("**Q4**", text)


if __name__ == "__main__":
    unittest.main()
