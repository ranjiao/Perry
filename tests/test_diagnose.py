"""Contract tests for `/perry diagnose`.

Three things are pinned here, and each one has already been wrong once:

  1. `bin/perry-diagnose` reports the findings it should on a project that has
     the problem, and — more importantly — reports *nothing* on a project that
     does not. A diagnostic that cries wolf trains its user to skip it, which
     is the exact failure `reference/diagnose.md` exists to avoid.
  2. The two template linters are real gates: they exit non-zero on broken
     input. `reference/project-archetypes.md` claims non-code archetypes can
     have a runnable verification loop, and these scripts are that claim's
     only evidence.
  3. The `diagnosis: 1` schema entry and its template agree.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
FIXTURE = PERRY_HOME / "tests" / "fixtures" / "sample-project"
DIAGNOSE = PERRY_HOME / "bin" / "perry-diagnose"
KB_LINT = PERRY_HOME / "templates" / "knowledge-base" / "bin" / "kb-lint"
DELIV_LINT = PERRY_HOME / "templates" / "ops" / "bin" / "deliverable-lint"


def scan(root: Path) -> dict:
    out = subprocess.run(
        [sys.executable, str(DIAGNOSE), "--root", str(root), "--json"],
        capture_output=True, text=True, timeout=120,
    )
    assert out.returncode == 0, f"perry-diagnose exited {out.returncode}: {out.stderr}"
    return json.loads(out.stdout)


def ids(payload: dict) -> set[str]:
    return {f["id"] for f in payload["findings"]}


def write(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


class TestScanNeverCrashes(unittest.TestCase):
    def test_empty_directory_is_a_finding_not_an_error(self):
        with tempfile.TemporaryDirectory() as td:
            p = scan(Path(td))
        self.assertEqual(p["schema"], "diagnose/1")
        # An empty folder has no rules file, no spine, and no check.
        self.assertIn("CTX-04", ids(p))
        self.assertIn("TRK-01", ids(p))

    def test_missing_root_exits_zero(self):
        out = subprocess.run(
            [sys.executable, str(DIAGNOSE), "--root", "/nonexistent/xyzzy", "--json"],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(out.returncode, 0)
        self.assertIn("error", json.loads(out.stdout))

    def test_help_works(self):
        out = subprocess.run(
            [sys.executable, str(DIAGNOSE), "--help"],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(out.returncode, 0)
        self.assertIn("perry-diagnose", out.stdout)


class TestFindingsFire(unittest.TestCase):
    def test_oversized_tier0_file_trips_the_budget(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "CLAUDE.md", "\n".join(f"- rule {i}" for i in range(400)))
            p = scan(root)
        self.assertIn("CTX-01", ids(p))
        self.assertGreater(p["context_load"]["over_budget_by"], 0)

    def test_empty_tier0_file_is_not_treated_as_present(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "AGENTS.md", "")
            p = scan(root)
        self.assertIn("CTX-05", ids(p))

    def test_two_divergent_rule_files_are_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "CLAUDE.md", "# a\nrule one\n")
            write(root, "AGENTS.md", "# b\nrule two\n")
            p = scan(root)
        self.assertIn("CTX-02", ids(p))

    def test_symlinked_rule_files_are_not_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "AGENTS.md", "# a\nrule one\n")
            (root / "CLAUDE.md").symlink_to("AGENTS.md")
            p = scan(root)
        self.assertNotIn("CTX-02", ids(p))

    def test_doc_pile_without_an_index(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(20):
                write(root, f"docs/note-{i}.md", f"# Note {i}\nbody\n")
            p = scan(root)
        self.assertIn("DOC-02", ids(p))
        self.assertIn("DOC-01", ids(p))

    def test_linked_docs_are_not_orphans(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            links = "\n".join(f"- [n{i}](docs/note-{i}.md)" for i in range(20))
            write(root, "index.md", f"# Index\n{links}\n")
            for i in range(20):
                write(root, f"docs/note-{i}.md", f"# Note {i}\nbody\n")
            p = scan(root)
        self.assertNotIn("DOC-02", ids(p))
        self.assertEqual(p["documents"]["orphans"], [])

    def test_duplicate_titles_are_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "index.md", "# Index\n- [a](a.md)\n- [b](b.md)\n")
            write(root, "a.md", "# Caching strategy\nx\n")
            write(root, "b.md", "# Caching Strategy\ny\n")
            p = scan(root)
        self.assertIn("DOC-03", ids(p))

    def test_stale_path_in_a_rules_file_is_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "AGENTS.md", "# Rules\nAuth lives in [here](src/auth/session.ts).\n")
            p = scan(root)
        self.assertIn("CTX-03", ids(p))

    def test_illustrative_backticked_path_is_not_flagged(self):
        """A schema doc naming a path in *someone else's* project is not a
        broken reference. This is the false positive that made the first
        version of the scanner report Perry's own README as broken."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "AGENTS.md",
                  "# Rules\nProjects using this put goals in `phase/CURRENT`.\n")
            p = scan(root)
        self.assertNotIn("CTX-03", ids(p))


class TestNoFalsePositives(unittest.TestCase):
    def test_perry_project_state_files_are_not_orphans(self):
        """BOARD.md is reachable by convention, not by a link. Flagging it
        would report a correctly-adopted project as broken."""
        p = scan(FIXTURE)
        self.assertEqual(p["documents"]["orphans"], [])
        self.assertNotIn("DOC-01", ids(p))
        self.assertNotIn("DOC-02", ids(p))

    def test_perry_own_dirs_do_not_drive_the_archetype_guess(self):
        """`knowledge/` is Perry's digest store, not a note vault."""
        p = scan(FIXTURE)
        self.assertIn(p["archetype"]["confidence"], ("none", "low"))

    def test_a_healthy_small_project_reports_little(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "AGENTS.md", "# Rules\n- Test with `pytest`.\n")
            write(root, "STATE.md", "# State\nGoal: ship it.\n")
            write(root, "DECISIONS.md", "# Decisions\n- 2026-01-01 chose X\n")
            write(root, "Makefile", "test:\n\tpytest\n")
            write(root, "tests/test_x.py", "def test_x(): assert True\n")
            p = scan(root)
        for fid in ("CTX-01", "CTX-04", "CTX-05", "DOC-01", "DOC-02",
                    "TRK-01", "TRK-03", "TRK-04"):
            self.assertNotIn(fid, ids(p), f"{fid} fired on a healthy project")

    def test_scaffold_dirs_do_not_drive_the_archetype_guess(self):
        """A repo shipping `templates/knowledge-base/raw/` is a tool that
        scaffolds a vault, not a vault. Perry misread itself exactly this way
        the moment the scaffolds landed."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "package.json", '{"scripts":{"test":"jest"}}')
            for i in range(8):
                write(root, f"src/mod{i}.ts", "export const x = 1\n")
            for name in ("raw/a.md", "wiki/b.md", "notes/c.md"):
                write(root, f"templates/knowledge-base/{name}", "# n\n")
            p = scan(root)
        self.assertEqual(p["archetype"]["guess"], "software")

    def test_extensionless_scripts_count_as_code(self):
        """A CLI-tool repo whose source has no file extensions must not read
        as a pile of documentation."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(6):
                write(root, f"bin/tool-{i}", "#!/usr/bin/env python3\nprint(1)\n")
            p = scan(root)
        self.assertGreaterEqual(p["inventory"]["code_files"], 6)


class TestTrackingSignals(unittest.TestCase):
    def test_absent_check_and_decision_log(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "STATE.md", "# State\ngoal\n")
            p = scan(root)
        self.assertIn("TRK-03", ids(p))
        self.assertIn("TRK-04", ids(p))

    def test_a_project_local_check_script_counts(self):
        """The constructed verification loop the non-code archetypes rely on."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "STATE.md", "# State\ngoal\n")
            write(root, "bin/kb-lint", "#!/usr/bin/env python3\n")
            p = scan(root)
        self.assertTrue(p["tracking"]["has_check"])
        self.assertNotIn("TRK-03", ids(p))


class TestKbLint(unittest.TestCase):
    def build(self, root: Path):
        write(root, "index.md", "# Index\n- [[alpha]]\n- [[beta]]\n")
        write(root, "wiki/alpha.md", "# Alpha\nSource: raw/note.txt\nSee [[beta]].\n")
        write(root, "wiki/beta.md", "# Beta\nSource: raw/note.txt\n")
        write(root, "raw/note.txt", "source material\n")

    def run_lint(self, root: Path):
        return subprocess.run(
            [sys.executable, str(KB_LINT), "--root", str(root), "--json"],
            capture_output=True, text=True, timeout=60,
        )

    def test_clean_vault_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.build(root)
            r = self.run_lint(root)
        self.assertEqual(r.returncode, 0)
        self.assertTrue(json.loads(r.stdout)["ok"])

    def test_each_failure_class_is_caught_and_gates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.build(root)
            # unreachable + no provenance + duplicate title + broken link
            write(root, "wiki/gamma.md", "# Alpha\nsee [[nowhere]]\n")
            r = self.run_lint(root)
        self.assertEqual(r.returncode, 1, "kb-lint must gate, not just report")
        kinds = {f["kind"] for f in json.loads(r.stdout)["findings"]}
        self.assertEqual(
            kinds,
            {"broken-link", "unreachable", "no-provenance", "duplicate-title"},
        )

    def test_missing_index_is_fatal(self):
        with tempfile.TemporaryDirectory() as td:
            r = self.run_lint(Path(td))
        self.assertEqual(r.returncode, 1)
        self.assertEqual(
            json.loads(r.stdout)["findings"][0]["kind"], "no-index")


class TestDeliverableLint(unittest.TestCase):
    def run_lint(self, root: Path):
        return subprocess.run(
            [sys.executable, str(DELIV_LINT), "--json"],
            capture_output=True, text=True, timeout=60, cwd=str(root),
        )

    def test_complete_signed_deliverable_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "deliverables/brief.md",
                  "# Brief\n## Summary\ns\n## Detail\nd\n## Sources\n- x\n"
                  "Sign-off: A Person, 2026-08-16\n")
            r = self.run_lint(root)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_unsigned_incomplete_deliverable_gates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "deliverables/draft.md",
                  "# Draft\n## Summary\n{{fill me}}\nTODO: numbers\n")
            r = self.run_lint(root)
        self.assertEqual(r.returncode, 1)
        kinds = {f["kind"] for f in json.loads(r.stdout)["findings"]}
        self.assertTrue({"missing-section", "unfilled", "open-marker",
                         "no-signoff"} <= kinds, kinds)

    def test_undated_signoff_is_rejected(self):
        """A sign-off that can't be tied to a version isn't a sign-off."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "deliverables/brief.md",
                  "# Brief\n## Summary\ns\n## Detail\nd\n## Sources\n- x\n"
                  "Sign-off: A Person\n")
            r = self.run_lint(root)
        self.assertEqual(r.returncode, 1)
        kinds = {f["kind"] for f in json.loads(r.stdout)["findings"]}
        self.assertIn("signoff-undated", kinds)


class TestFindingsExplainThemselves(unittest.TestCase):
    """The reader of a finding has usually read none of the research. A finding
    they cannot evaluate gets either obeyed blindly or ignored, so the scanner
    owes every one of them a plain-language mechanism."""

    def all_findings(self) -> list[dict]:
        """Provoke as many distinct findings as one project can carry."""
        collected: dict[str, dict] = {}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "CLAUDE.md",
                  "\n".join(f"- rule {i}" for i in range(300))
                  + "\nSee [gone](src/missing/file.ts).\n")
            write(root, "AGENTS.md", "# other\ndifferent rules\n")
            for i in range(20):
                write(root, f"docs/n{i}.md", f"# Note {i}\nbody\n")
            write(root, "docs/dup-a.md", "# Caching strategy\nx\n")
            write(root, "docs/dup-b.md", "# Caching Strategy\ny\n")
            write(root, "docs/huge.md", "\n".join(["line"] * 900))
            for f in scan(root)["findings"]:
                collected[f["id"]] = f
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "only.md", "# one\n")
            for f in scan(root)["findings"]:
                collected.setdefault(f["id"], f)
        return list(collected.values())

    def test_every_emitted_finding_carries_a_why(self):
        found = self.all_findings()
        self.assertGreaterEqual(len(found), 8, "provoke more findings")
        for f in found:
            self.assertTrue(f.get("why"), f"{f['id']} has no 'why'")
            self.assertGreater(len(f["why"]), 60, f"{f['id']} why is too thin")

    def test_the_why_table_covers_every_id_the_scanner_can_emit(self):
        src = DIAGNOSE.read_text()
        import re as _re
        emitted = set(_re.findall(r'"([A-Z]{3}-\d{2})", "(?:error|warn|info)"', src))
        declared = set(_re.findall(r'^    "([A-Z]{3}-\d{2})":', src, _re.M))
        self.assertTrue(emitted, "no findings parsed out of the scanner")
        self.assertEqual(emitted - declared, set(),
                         "emitted findings with no entry in WHY")

    def test_user_facing_text_avoids_perry_jargon(self):
        """`tier 0`, `rung`, `spine` are our words for these ideas, not the
        reader's. They belong in the reference docs, not in a report handed to
        someone who has never opened them."""
        jargon = ["tier 0", "tier-0", "rung", "spine", "archetype",
                  "progressive disclosure", "context rot", "orchestrat"]
        for f in self.all_findings():
            blob = f"{f['title']} {f['why']} {f['detail']}".lower()
            for word in jargon:
                self.assertNotIn(word, blob,
                                 f"{f['id']} uses Perry jargon: '{word}'")

    def test_text_mode_shows_the_why_above_the_remedy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "CLAUDE.md", "\n".join(f"- rule {i}" for i in range(300)))
            out = subprocess.run(
                [sys.executable, str(DIAGNOSE), "--root", str(root), "--text"],
                capture_output=True, text=True, timeout=120,
            ).stdout
        self.assertIn("why it bites", out)
        self.assertIn("what to do", out)
        self.assertLess(out.index("why it bites"), out.index("what to do"))
        self.assertIn("calibrated", out, "thresholds must be flagged as arguable")

    def test_a_clean_project_says_so_in_plain_language(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "AGENTS.md", "# Rules\n- Test with `pytest`.\n")
            write(root, "STATE.md", "# State\nGoal: ship it.\n")
            write(root, "DECISIONS.md", "# Decisions\n- 2026-01-01 chose X\n")
            write(root, "Makefile", "test:\n\tpytest\n")
            out = subprocess.run(
                [sys.executable, str(DIAGNOSE), "--root", str(root), "--text"],
                capture_output=True, text=True, timeout=120,
            ).stdout
        self.assertIn("Nothing to fix", out)


class TestSchemaAgreement(unittest.TestCase):
    def test_diagnosis_entry_and_template_agree(self):
        schema = json.loads(
            (PERRY_HOME / "schema" / "state-schema.json").read_text())
        entry = next(f for f in schema["files"] if f["id"] == "diagnosis")
        self.assertEqual(entry["owner"], "perry")
        self.assertEqual(entry["anchor"], "project")
        tpl = PERRY_HOME / entry["template"]
        self.assertTrue(tpl.is_file(), f"{entry['template']} missing")
        text = tpl.read_text()
        for field in entry["frontmatter"]["fields"]:
            self.assertIn(f"{field}:", text,
                          f"template does not carry declared field '{field}'")

    def test_declared_enums_exist(self):
        schema = json.loads(
            (PERRY_HOME / "schema" / "state-schema.json").read_text())
        for name in ("diagnosis_stage", "diagnosis_depth", "finding_severity",
                     "finding_source", "finding_status", "prescription_status"):
            self.assertIn(name, schema["enums"])

    def test_scanner_finding_ids_are_documented(self):
        """Every ID the scanner can emit must appear in the reference doc, or a
        user reading a finding has nowhere to go."""
        src = DIAGNOSE.read_text()
        emitted = set(__import__("re").findall(r'"([A-Z]{3}-\d{2})", "', src))
        docs = (PERRY_HOME / "reference" / "diagnose.md").read_text() + \
               (PERRY_HOME / "state" / "diagnosis_TEMPLATE.md").read_text()
        for fid in sorted(emitted):
            self.assertIn(fid, docs, f"{fid} is emitted but never documented")


if __name__ == "__main__":
    unittest.main()
