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
import pathlib
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
FIXTURE = PERRY_HOME / "tests" / "fixtures" / "sample-project"
DIAGNOSE = PERRY_HOME / "bin" / "perry-diagnose"
KB_LINT = PERRY_HOME / "templates" / "knowledge-base" / "bin" / "kb-lint"
DELIV_LINT = PERRY_HOME / "templates" / "ops" / "bin" / "deliverable-lint"
EXPLAIN = PERRY_HOME / "bin" / "perry-explain"


def load_bin_module(name: str):
    """Import an extensionless script from bin/ as a module."""
    import importlib.util
    from importlib.machinery import SourceFileLoader

    path = PERRY_HOME / "bin" / name
    loader = SourceFileLoader(name.replace("-", "_"), str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


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


class TestIdsResolve(unittest.TestCase):
    """`bin/perry-explain` exists because Perry mints nine families of ID and
    hands them to a user who never agreed to learn them. If the resolver can't
    resolve them, the IDs are just as opaque as before."""

    def explain(self, root: Path, *args: str):
        return subprocess.run(
            [sys.executable, str(EXPLAIN), "--root", str(root), *args],
            capture_output=True, text=True, timeout=60,
        )

    def test_resolves_the_fixture_ids_a_user_would_hit(self):
        # USER-014 is the exact case: BOARD.md says "waiting on USER-014" and
        # nothing on that line says what it is.
        r = self.explain(FIXTURE, "USER-014", "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        e = json.loads(r.stdout)
        self.assertEqual(e["id"], "USER-014")
        self.assertTrue(e["title"], "USER-014 resolved with no title")
        self.assertTrue(e["defined"])

    def test_resolves_ids_from_every_shape_perry_writes(self):
        for wanted in ("REL-002",       # board table row
                       "ADR-001",       # decisions table + ID-named file
                       "P-O1.2",        # linkage YAML
                       "DESIGN-001"):   # design doc
            with self.subTest(id=wanted):
                r = self.explain(FIXTURE, wanted, "--json")
                self.assertEqual(r.returncode, 0, f"{wanted}: {r.stdout}")
                e = json.loads(r.stdout)
                self.assertTrue(e["title"], f"{wanted} has no readable title")

    def test_glossary_lists_every_id(self):
        r = self.explain(FIXTURE, "--all", "--json")
        rows = json.loads(r.stdout)
        ids = {x["id"] for x in rows}
        self.assertTrue({"REL-001", "ADR-002", "USER-014", "P-O1.1"} <= ids, ids)

    def test_dangling_ids_are_reported_and_gate(self):
        """The fixture's phase doc names REL-003, which is on no board."""
        r = self.explain(FIXTURE, "--dangling", "--json")
        self.assertEqual(r.returncode, 1)
        self.assertIn("REL-003", {x["id"] for x in json.loads(r.stdout)})

    def test_unknown_id_fails_helpfully(self):
        r = self.explain(FIXTURE, "REL-999")
        self.assertEqual(r.returncode, 1)
        self.assertIn("--all", r.stdout)

    def test_label_form_pairs_id_with_title(self):
        """The form the style rule requires: REL-002 ("Flake detector")."""
        mod = load_bin_module("perry-explain")
        entries = mod.harvest(FIXTURE)
        self.assertEqual(mod.label(entries["REL-002"]),
                         'REL-002 ("Flake detector")')
        self.assertEqual(mod.label({"id": "X-1"}), "X-1")

    def test_works_on_a_project_with_its_own_id_convention(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "plan.md",
                  "| ID | Title | Status |\n|---|---|---|\n"
                  "| EPIC-7 | Billing rewrite | active |\n")
            r = self.explain(root, "EPIC-7", "--json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)["title"], "Billing rewrite")


class TestUserLoadFindings(unittest.TestCase):
    def test_dangling_ids_surface_as_a_finding(self):
        p = scan(FIXTURE)
        self.assertIn("LOAD-02", ids(p))

    def test_id_sprawl_without_a_lookup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(1, 10):
                write(root, f"docs/m{i}.md",
                      f"# Notes {i}\nMILE-00{i} relates to ADR-00{i}.\n")
            p = scan(root)
        self.assertIn("LOAD-01", ids(p))

    def test_a_perry_project_has_a_lookup_so_no_sprawl_finding(self):
        """Perry ships bin/perry-explain, so its IDs are resolvable."""
        p = scan(FIXTURE)
        self.assertNotIn("LOAD-01", ids(p))

    def test_decision_backlog_surfaces(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(6):
                write(root, f"docs/d{i}.md", f"# Doc {i}\nBackend: TBD\n")
            p = scan(root)
        self.assertIn("LOAD-03", ids(p))

    def test_tokens_shaped_like_ids_but_arent(self):
        """Running against Perry's own repo first reported SHA-256 and a
        `#L12-40` line citation as undefined work items. 25 findings, 21 of
        them noise — which is how a checker teaches people to ignore it."""
        mod = load_bin_module("perry-explain")
        for token in ("SHA-256", "L12-40", "UTF-8", "NNN-1", "NN-7", "AES-256"):
            self.assertFalse(mod.is_real_id(token), f"{token} counted as an ID")
        for token in ("REL-001", "ADR-003", "USER-014", "EPIC-7", "CTX-01"):
            self.assertTrue(mod.is_real_id(token), f"{token} rejected as an ID")

    def test_illustrative_ids_are_not_dangling(self):
        """`tag your task like TASK-007` in a README refers to nothing and is
        not supposed to."""
        mod = load_bin_module("perry-explain")
        for rel in ("README.md", "SKILL.md", "work/reference/decisions.md",
                    "work/state/journal_TEMPLATE.md", "templates/software/STATE.md",
                    "tests/fixtures/p/BOARD.md"):
            self.assertTrue(mod.is_illustrative(rel), f"{rel} should be illustrative")
        # docs/ holds real documentation on most projects — excluding it would
        # blind the check on exactly the projects that need it.
        for rel in ("BOARD.md", "docs/plan.md", "phase/002-release.md"):
            self.assertFalse(mod.is_illustrative(rel), f"{rel} wrongly excluded")

    def test_perry_itself_passes_its_own_id_checks(self):
        """The skill that reports this must not commit it."""
        p = scan(PERRY_HOME)
        self.assertEqual(p["user_load"]["dangling"], [])
        self.assertEqual(p["user_load"]["untitled"], [])
        for fid in ("LOAD-01", "LOAD-02", "LOAD-03", "LOAD-04"):
            self.assertNotIn(fid, ids(p), f"Perry trips its own {fid}")

    def test_a_small_tidy_project_reports_no_load_findings(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "AGENTS.md", "# Rules\n- Test with `pytest`.\n")
            write(root, "STATE.md", "# State\nGoal: ship it.\n")
            write(root, "DECISIONS.md", "# Decisions\n- 2026-01-01 chose X\n")
            write(root, "Makefile", "test:\n\tpytest\n")
            p = scan(root)
        for fid in ("LOAD-01", "LOAD-02", "LOAD-03", "LOAD-04"):
            self.assertNotIn(fid, ids(p), f"{fid} fired on a tidy project")


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


class UserAskAnswerState(unittest.TestCase):
    """LOAD-03 must count asks that are *waiting*, not asks that ever existed.

    It counted every `USER-` id appearing in a tracking doc, ignoring its Status
    cell — so a project that answered its questions but had not yet swept the
    rows kept reporting an open decision backlog. Sweeping answered rows is
    `triage`'s job and is optional; being reported as blocked for not doing it
    is not. The finding's own text says "open questions are waiting on you",
    which was the claim that had drifted from what the number measured.
    """

    def _board(self, rows: str) -> str:
        return ("# Board\n\n## P0\n\n"
                "| ID | Title | Owner | Status | Next action | Evidence |\n"
                "|---|---|---|---|---|---|\n"
                "\n## P1\n\n| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
                "\n## P2\n\n| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
                "\n## Cadence\n\n| ID | Recurring task | Owner | Frequency | Next due | Last evidence |\n|---|---|---|---|---|---|\n"
                "\n## User Input Queue\n\n"
                "| USER-id | Needed from user | Blocks | Idle | Status |\n"
                "|---|---|---|---|---|\n" + rows +
                "\n## Top risks\n\n- none\n")

    def _count(self, rows: str) -> int:
        import subprocess, tempfile, json as _json
        from pathlib import Path as _P
        with tempfile.TemporaryDirectory() as td:
            root = _P(td)
            (root / ".perry").mkdir()
            (root / ".perry" / "config.md").write_text(
                "# c\n\n- Document language: English\n"
                "- Repo layout: single\n- State root: .\n")
            (root / "BOARD.md").write_text(self._board(rows))
            r = subprocess.run(
                ["python3", str(PERRY_HOME / "bin" / "perry-diagnose"),
                 "--root", str(root), "--json"],
                capture_output=True, text=True)
            return _json.loads(r.stdout)["user_load"]["open_decisions"]

    def test_an_answered_ask_is_not_waiting_on_anyone(self):
        self.assertEqual(
            self._count("| USER-001 | Threshold N | — | — | **answered 2026-08-16: 30 days** |\n"),
            0)

    def test_an_unanswered_ask_still_counts(self):
        self.assertEqual(
            self._count("| USER-001 | Threshold N | TASK-005 | 6d | pending |\n"),
            1)

    def test_answered_and_pending_are_counted_separately(self):
        self.assertEqual(
            self._count(
                "| USER-001 | A | — | — | **answered 2026-08-16** |\n"
                "| USER-002 | B | — | 3d | pending |\n"
                "| USER-003 | C | — | 9d | waiting on you |\n"),
            2)


class NestedRepositoriesAreNotScanned(unittest.TestCase):
    """A directory with its own `.git` is a different project.

    Found live: `perry-diagnose` reported a dangling `USER-` id that existed in
    no file of this repo. It was reading a subagent's half-written
    `bin/perry-task` out of a git worktree under `.claude/`, so Perry's own
    diagnostics were non-deterministic for as long as another agent was
    running — the number changed between two runs a minute apart.

    Skipping by directory name never finishes. A vendored checkout, a
    submodule, an agent worktree and a sibling repo dropped in by accident are
    the same shape, and only some of them have predictable names. `.git` is a
    directory in a clone and a FILE in a worktree; both mark a boundary.
    """

    def test_a_nested_clone_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".perry").mkdir()
            (root / ".perry" / "config.md").write_text(
                "# Perry configuration\n\n- State root: .\n")
            (root / "BOARD.md").write_text(
                "# BOARD\n\n## P0\n| ID | Title | Owner | Status | Next action | Evidence |\n"
                "|---|---|---|---|---|---|\n\n## P1\n| ID | Title | Owner | Status | Next action | Evidence |\n"
                "|---|---|---|---|---|---|\n\n## P2\n| ID | Title | Owner | Status | Next action | Evidence |\n"
                "|---|---|---|---|---|---|\n")

            other = root / "vendored"
            (other / ".git").mkdir(parents=True)      # a clone
            (other / "NOTES.md").write_text("blocked on TASK-777 and USER-777\n")

            wt = root / "wt"
            wt.mkdir()
            (wt / ".git").write_text("gitdir: /elsewhere\n")   # a worktree
            (wt / "NOTES.md").write_text("blocked on TASK-778\n")

            r = subprocess.run(
                ["python3", str(PERRY_HOME / "bin" / "perry-diagnose"),
                 "--root", str(root), "--json"], capture_output=True, text=True)
            payload = json.loads(r.stdout)
            blob = json.dumps(payload, ensure_ascii=False)
            for stray in ("TASK-777", "USER-777", "TASK-778"):
                self.assertNotIn(
                    stray, blob,
                    f"{stray} came from a nested repository and was counted as "
                    f"this project's")


class ImplementationPlanPlaceholdersAreNotUserDecisions(unittest.TestCase):
    """LOAD-03 measures decisions **queued on the user**.

    A `TBD` inside `## Implementation plan` waits on the handoff, not on a
    person — the common form is a task-id column reading `TBD at handoff`. The
    section that queues decisions on the user is `## User Decisions`, which has
    its own `Chosen` column and its own convention.

    Found when a 402-line design doc put six of them in one table and tripped
    LOAD-03 on Perry's own repo. A check that counts every planning placeholder
    trains the user to ignore it, which is the failure `reference/diagnose.md`
    names as worse than no check.
    """

    DOC = """# DESIGN-900: Example

## 4. User Decisions

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Which store | a / b | TBD | — |

## 6. Implementation plan

| Phase | Scope | Proposed task(s) | Owner |
|---|---|---|---|
| A | schema | TBD at handoff | Coding Agent |
| B | writer | TBD at handoff | Coding Agent |

## 7. Risks & mitigations

—
"""

    def payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".perry").mkdir()
            (root / ".perry" / "config.md").write_text(
                "# Perry configuration\n\n- State root: .\n")
            (root / "design").mkdir()
            (root / "design" / "DESIGN-900-example.md").write_text(self.DOC)
            r = subprocess.run(
                ["python3", str(PERRY_HOME / "bin" / "perry-diagnose"),
                 "--root", str(root), "--json"], capture_output=True, text=True)
            return json.loads(r.stdout)

    def test_the_user_decision_row_is_counted(self):
        """The real queue must still be measured — this is not a licence to
        stop counting."""
        d = self.payload()["user_load"]
        self.assertEqual(d["open_decisions"], 1)

    def test_the_plan_placeholders_are_not(self):
        d = self.payload()["user_load"]
        self.assertFalse(
            [s for s in d["open_decision_samples"] if "Implementation" in s],
            "a planning placeholder was counted as a decision queued on the user")
        self.assertLess(d["open_decisions"], 3,
                        "the two `TBD at handoff` cells were counted")


class TestAFencedBlockIsOutputNotAReference(unittest.TestCase):
    """Evidence files quote command transcripts, and those transcripts carry
    ids from throwaway fixtures and from copies of *other* projects. Committing
    four V4 reviews put `CAD-002`, `CAD-004`, `CADENCE-000` and `RX-010` into
    this repo's dangling report — ids Perry never minted, in output Perry was
    quoting.

    A dangling report full of ids the project does not own is one the user
    learns to ignore, which `reference/diagnose.md` names as worse than no
    check at all.

    Only fences are exempt, never inline code: ``see `TASK-042` `` is how Perry
    is supposed to cite a real row.
    """

    DOC = """# Notes

The row we are waiting on is `TASK-901`.

```
perry-task: wrote ZZZ-404 (risk-add) → board + journal + event
oldest: ZZZ-405 @ 224d
```
"""

    def harvest(self, text):
        import tempfile
        explain = load_bin_module("perry-explain")
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "BOARD.md").write_text("# BOARD\n")
            (root / "notes.md").write_text(text)
            return explain.harvest(root)

    def test_an_id_only_inside_a_fence_is_not_reported_as_dangling(self):
        e = self.harvest(self.DOC)
        for tracked in ("ZZZ-404", "ZZZ-405"):
            self.assertFalse(
                e.get(tracked, {}).get("in_tracking_doc"),
                f"{tracked} appears only in pasted output and was counted as "
                f"a reference this project owes a definition for")

    def test_an_id_in_prose_is_still_counted(self):
        """The exemption must not swallow the check it lives in."""
        e = self.harvest(self.DOC)
        self.assertTrue(e["TASK-901"]["in_tracking_doc"])
        self.assertFalse(e["TASK-901"]["defined"])

    def test_an_unclosed_fence_does_not_swallow_the_rest_of_the_file(self):
        """A single stray ``` would otherwise exempt every line after it."""
        e = self.harvest("# Notes\n\n```\nZZZ-404\n```\n\nWaiting on `TASK-902`.\n")
        self.assertTrue(e.get("TASK-902", {}).get("in_tracking_doc"),
                        "a stray fence swallowed every line after it")


if __name__ == "__main__":
    unittest.main()
