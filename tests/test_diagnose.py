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
        """The family prefix is 2-4 letters — `NS`, `CTX`, `LOAD`, `MODE`. An
        earlier `[A-Z]{3}` here matched neither `NS-01` nor any `LOAD-*`, so
        five of the scanner's finding IDs were ungraded by both this test and
        `test_scanner_finding_ids_are_documented` and neither said so."""
        src = DIAGNOSE.read_text()
        import re as _re
        emitted = set(_re.findall(r'"([A-Z]{2,4}-\d{2})", "(?:error|warn|info)"', src))
        declared = set(_re.findall(r'^    "([A-Z]{2,4}-\d{2})":', src, _re.M))
        self.assertTrue(emitted, "no findings parsed out of the scanner")
        for family in ("NS-01", "LOAD-01", "MODE-01"):
            self.assertIn(family, emitted,
                          f"the ID pattern no longer matches {family}")
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
        """Six decisions RECORDED as waiting on a person, in the register that
        records them. This fixture used to be six documents each carrying the
        word `TBD`; it now uses six rows, because the count is over rows —
        `DecisionsAreCountedPerRecordNotPerMention` pins the difference."""
        rows = "\n".join(
            f"| {i} | Question {i} | a / b | TBD | — |" for i in range(1, 7))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "design/DESIGN-001-backlog.md",
                  "# DESIGN-001: Backlog\n\n## 4. User Decisions\n\n"
                  "| # | Decision | Options | Chosen | Date |\n"
                  "|---|---|---|---|---|\n" + rows + "\n")
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
        emitted = set(__import__("re").findall(r'"([A-Z]{2,4}-\d{2})", "', src))
        docs = (PERRY_HOME / "reference" / "diagnose.md").read_text() + \
               (PERRY_HOME / "state" / "diagnosis_TEMPLATE.md").read_text()
        self.assertGreaterEqual(len(emitted), 20,
                                "the ID pattern stopped matching — this test "
                                "would pass over an empty set")
        for fid in sorted(emitted):
            self.assertIn(fid, docs, f"{fid} is emitted but never documented")

    def test_every_finding_id_has_a_row_in_the_catalog_table(self):
        """Mentioned somewhere in the prose is not the same as looked-up-able.
        `reference/diagnose.md § Finding catalog` calls itself *the lookup*, and
        a stable ID with nowhere to look it up is worse than prose — so the row,
        with its severity, its trigger and its usual prescription, is what the
        contract actually is."""
        import re as _re
        src = DIAGNOSE.read_text()
        emitted = set(_re.findall(r'"([A-Z]{2,4}-\d{2})", "', src))
        doc = (PERRY_HOME / "reference" / "diagnose.md").read_text()
        body = doc.split("## Finding catalog", 1)
        self.assertEqual(len(body), 2, "the finding catalog heading is gone")
        table = body[1].split("\n## ", 1)[0]
        rows = dict(_re.findall(
            r"^\|\s*`([A-Z]{2,4}-\d{2})`\s*\|\s*(error|warn|info)\s*\|",
            table, _re.M))
        self.assertGreaterEqual(len(rows), 20, "the catalog table did not parse")
        for fid in sorted(emitted):
            self.assertIn(fid, rows,
                          f"{fid} has no row in the finding catalog table")

    def test_every_catalogued_id_satisfies_the_schema_pattern(self):
        """The catalog is the list of ids Perry emits; `findings[].id.pattern`
        is the shape `perry-lint` demands of a diagnosis that records one. When
        they disagree Perry writes a file and then reports its own output as
        malformed — which it did for a release: the pattern was
        `^[A-Z]{3}-\\d{2}$` and the catalog documents `LOAD-01`..`LOAD-04`,
        `NS-01` and `MODE-01`.

        Asserted over the WHOLE catalog, not over the prefixes that happened to
        bite. A pattern widened to admit `LOAD-` and nothing else leaves `NS-01`
        and `MODE-01` failing, and this fails on them."""
        import re as _re
        schema = json.loads(
            (PERRY_HOME / "schema" / "state-schema.json").read_text())
        entry = next(f for f in schema["files"] if f["id"] == "diagnosis")
        pattern = entry["frontmatter"]["fields"]["findings"]["items"]["id"]["pattern"]
        doc = (PERRY_HOME / "reference" / "diagnose.md").read_text()
        table = doc.split("## Finding catalog", 1)[1].split("\n## ", 1)[0]
        catalogued = _re.findall(
            r"^\|\s*`([A-Z][A-Z0-9-]*-\d+)`\s*\|\s*(?:error|warn|info)\s*\|",
            table, _re.M)
        self.assertGreaterEqual(len(catalogued), 20,
                                "the catalog table did not parse — this test "
                                "would pass over an empty set")
        self.assertGreaterEqual(
            len({fid.split("-")[0] for fid in catalogued}), 5,
            "one prefix in the whole catalog — this test could no longer tell "
            "a category-wide pattern from one widened to a single prefix")
        for fid in catalogued:
            self.assertRegex(fid, pattern,
                             f"{fid} is in the finding catalog but a diagnosis "
                             f"recording it fails schema/state-schema.json")


#: A diagnosis whose every enum-bound cell is a knob. Built field by field
#: rather than by string substitution, because `status` appears under both
#: `findings[]` and `prescription[]`, and a `str.replace(old, new, 1)` would
#: silently poison whichever came first — a mutation that reports green while
#: testing the wrong branch.
_DIAGNOSIS_DEFAULTS = {
    "depth": "standard",
    "stage": "done",
    "findings[].id": "CTX-01",
    "findings[].severity": "error",
    "findings[].source": "scan",
    "findings[].status": "open",
    "prescription[].status": "proposed",
}


def diagnosis_doc(**overrides: str) -> str:
    v = dict(_DIAGNOSIS_DEFAULTS, **overrides)
    return (
        "---\n"
        "diagnosis: 1\n"
        'project: "Sample"\n'
        'root: "/tmp/sample"\n'
        f"depth: {v['depth']}\n"
        f"stage: {v['stage']}\n"
        "findings:\n"
        f"  - id: {v['findings[].id']}\n"
        f"    severity: {v['findings[].severity']}\n"
        f"    source: {v['findings[].source']}\n"
        '    title: "Always-loaded files over budget"\n'
        f"    status: {v['findings[].status']}\n"
        "prescription:\n"
        "  - id: RX-1\n"
        '    change: "Split CLAUDE.md"\n'
        '    closes: ["CTX-01"]\n'
        f"    status: {v['prescription[].status']}\n"
        "---\n"
        "\n"
        "# Diagnosis — Sample\n"
    )


class TestLintValidatesTheDiagnosisPerryWrites(unittest.TestCase):
    """`.perry/diagnose/<date>-diagnosis.md` is a file Perry writes into
    somebody else's project, and nothing asserted that `perry-lint` — the tool
    that checks every other file Perry writes — reached it at all.

    *How* it is checked matters as much as *that* it is. Every rule below is
    read out of `schema/state-schema.json` at test time. A second, hand-written
    list of what a diagnosis contains is the thing that drifts, and the drift is
    silent: the file keeps linting clean against a list nobody updated."""

    def lint(self, root: Path) -> dict:
        out = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-lint"),
             "--root", str(root), "--json"],
            capture_output=True, text=True, timeout=180)
        return json.loads(out.stdout)

    def project(self, td: str, doc: str) -> Path:
        root = Path(td)
        (root / ".perry" / "diagnose").mkdir(parents=True)
        (root / ".perry" / "diagnose" / "2026-01-01-diagnosis.md").write_text(doc)
        return root

    def enum_fields(self) -> dict[str, str]:
        """Every enum-bound field the schema declares for a diagnosis, keyed by
        the same dotted path `diagnosis_doc` uses. Derived, never listed."""
        schema = json.loads(
            (PERRY_HOME / "schema" / "state-schema.json").read_text())
        entry = next(f for f in schema["files"] if f["id"] == "diagnosis")

        def walk(fields: dict, prefix: str) -> dict[str, str]:
            out: dict[str, str] = {}
            for name, rule in fields.items():
                if rule.get("enum"):
                    out[prefix + name] = rule["enum"]
                if rule.get("type") == "array":
                    items = rule.get("items") or {}
                    if items and not items.get("type"):
                        out.update(walk(items, f"{prefix}{name}[]."))
            return out

        return walk(entry["frontmatter"]["fields"], "")

    def test_a_well_formed_diagnosis_lints_clean(self):
        """The floor. Without it every assertion below would be satisfied by a
        linter that reports an error on any diagnosis whatsoever."""
        with tempfile.TemporaryDirectory() as td:
            root = self.project(td, diagnosis_doc())
            self.assertEqual(
                [f for f in self.lint(root)["findings"] if "diagnose" in f["file"]],
                [])

    def test_the_diagnosis_is_a_file_perry_lint_reaches(self):
        """The wiring, asserted separately from the rules — a file the schema
        describes perfectly and the linter never opens is checked by nothing."""
        with tempfile.TemporaryDirectory() as td:
            root = self.project(td, diagnosis_doc(stage="not_a_stage"))
            hits = [f for f in self.lint(root)["findings"]
                    if f["file"] == ".perry/diagnose/2026-01-01-diagnosis.md"]
        self.assertTrue(hits, "perry-lint never opened the diagnosis file")

    def test_every_enum_the_schema_declares_is_actually_enforced(self):
        """Schema-driven in both directions: the fields come from the schema,
        and the renderer is required to know all of them. A field added to the
        diagnosis spec that nothing here can reach fails loudly rather than
        being skipped in silence."""
        fields = self.enum_fields()
        self.assertEqual(
            set(fields) - set(_DIAGNOSIS_DEFAULTS), set(),
            "schema/state-schema.json declares an enum-bound diagnosis field "
            "that diagnosis_doc() cannot write — extend _DIAGNOSIS_DEFAULTS")
        self.assertGreaterEqual(len(fields), 5,
                                "the enum walk found almost nothing — it would "
                                "pass over a schema with the enums deleted")
        for path, enum_name in sorted(fields.items()):
            with self.subTest(field=path):
                with tempfile.TemporaryDirectory() as td:
                    root = self.project(
                        td, diagnosis_doc(**{path: "not_a_declared_value"}))
                    hits = [f for f in self.lint(root)["findings"]
                            if f["rule"] == "bad-enum"
                            and "not_a_declared_value" in f["message"]]
                self.assertTrue(
                    hits,
                    f"{path} is bound to enum {enum_name!r} in the schema and "
                    f"perry-lint accepted a value that is not in it")

    def test_a_finding_id_from_perrys_own_catalog_is_not_reported_as_malformed(self):
        """`LOAD-01` is in `reference/diagnose.md § Finding catalog` and Perry's
        own diagnose workflow emits it. Perry reporting its own output as
        malformed is the defect TASK-048 was opened on."""
        for fid in ("LOAD-01", "NS-01", "MODE-01", "CTX-01"):
            with self.subTest(id=fid):
                with tempfile.TemporaryDirectory() as td:
                    root = self.project(
                        td, diagnosis_doc(**{"findings[].id": fid}))
                    hits = [f for f in self.lint(root)["findings"]
                            if f["rule"] == "bad-id"]
                self.assertEqual(hits, [], f"{fid} was rejected by the pattern")

    def test_an_id_that_is_not_perrys_shape_is_still_reported(self):
        """The other half — widening the pattern to fit the catalog must not
        widen it to fit anything, or the check is decorative. `CON-03b` is the
        live case: it is on a real project's diagnosis and it is not a
        catalogued id."""
        for fid in ("ctx-1", "CON-03b", "CTX-1", "SOMEPREFIX-01"):
            with self.subTest(id=fid):
                with tempfile.TemporaryDirectory() as td:
                    root = self.project(
                        td, diagnosis_doc(**{"findings[].id": fid}))
                    hits = [f for f in self.lint(root)["findings"]
                            if f["rule"] == "bad-id"]
                self.assertTrue(hits, f"{fid!r} passed the finding id pattern")


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


#: The opt-out for the conformance gate. Written as a literal here because
#: `tests/gate.py` — which will own this string — lands on `feat/work-modes`
#: after this branch was cut; the line is inert on a tree whose gate is still
#: advisory by default, so it is correct both before and after that merge.
GATE_OFF = "- Conformance gate: advisory\n"


def board_with_queue(rows: str) -> str:
    """A BOARD.md whose only populated section is the User Input Queue."""
    empty = ("| ID | Title | Owner | Status | Next action | Evidence |\n"
             "|---|---|---|---|---|---|\n")
    return ("# Board\n\n"
            f"## P0\n\n{empty}\n## P1\n\n{empty}\n## P2\n\n{empty}\n"
            "## Cadence\n\n"
            "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |\n"
            "|---|---|---|---|---|---|\n\n"
            "## User Input Queue\n\n"
            "| USER-id | Needed from user | Blocks | Idle | Status |\n"
            "|---|---|---|---|---|\n" + rows +
            "\n## Top risks\n\n- none\n")


class DecisionsAreCountedPerRecordNotPerMention(unittest.TestCase):
    """LOAD-03 counts DECISIONS. It used to count decision-words in prose.

    Measured on this repo: seven "open questions waiting on you" against a User
    Input Queue holding two. Three of the seven were `USER-004` — its own
    context file, the dispatch that quoted the context file, and the journal
    entry that recorded minting it. Writing an open question down was what made
    the number go up, so a project that documents its decisions well scored
    worse than one that leaves them in somebody's head.

    The rule now: a decision is countable when it has an identity, and the two
    registers that give it one are `BOARD.md § User Input Queue` and a design
    doc's `## User Decisions`. Prose has no identity — nothing in a sentence
    tells you whether it is the same question as the sentence two files away —
    so prose is reported next to the count and never inside it.
    """

    def project(self, root: Path, board: str | None = None) -> Path:
        (root / ".perry").mkdir(parents=True, exist_ok=True)
        (root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- State root: .\n" + GATE_OFF)
        if board is not None:
            (root / "BOARD.md").write_text(board)
        return root

    def load(self, build) -> dict:
        with tempfile.TemporaryDirectory() as td:
            root = self.project(Path(td))
            build(root)
            return scan(root)["user_load"]

    # ── the bug, as a fixture ────────────────────────────────────────────
    def test_one_row_discussed_in_three_files_is_one_decision(self):
        def build(root):
            (root / "BOARD.md").write_text(board_with_queue(
                "| USER-004 | Read-only files during migration | TASK-079 | 1d | pending |\n"))
            write(root, "evidence/TASK-079-context.md",
                  "# Context\n\n## What is still undecided — USER-004\n\n"
                  "The policy half of this row is undecided.\n")
            write(root, "evidence/TASK-079-dispatch.md",
                  "# Dispatch\n\nUSER-004 is still awaiting your decision.\n")
            write(root, "journal/2026-08-20.md",
                  "# Journal\n\nUSER-004 was minted because the question was "
                  "deliberately left undecided.\n")
        load = self.load(build)
        self.assertEqual(load["open_decisions"], 1,
                         "one queue row, discussed three times, counted more "
                         "than once")
        self.assertEqual(
            [s.split(" — ")[-1] for s in load["open_decision_samples"]],
            ["USER-004"])

    def test_two_rows_and_no_prose_count_two(self):
        load = self.load(lambda root: (root / "BOARD.md").write_text(
            board_with_queue(
                "| USER-001 | Threshold N | TASK-005 | 6d | pending |\n"
                "| USER-002 | Where the store lives | TASK-006 | 2d | pending |\n")))
        self.assertEqual(load["open_decisions"], 2)

    def test_an_answered_row_plus_prose_about_it_counts_zero(self):
        def build(root):
            (root / "BOARD.md").write_text(board_with_queue(
                "| USER-001 | Threshold N | — | — | **answered 2026-08-16: 30 days** |\n"))
            write(root, "journal/2026-08-16.md",
                  "# Journal\n\nUSER-001 was undecided for six days before it "
                  "was answered.\n")
        self.assertEqual(self.load(build)["open_decisions"], 0)

    # ── the boundary, decided deliberately ───────────────────────────────
    def test_a_question_raised_only_in_prose_is_reported_not_counted(self):
        """**The decision this row had to make, made explicitly.**

        A question raised in prose and never recorded IS a real open decision.
        It is still not counted, because counting it costs the property that
        makes the number worth reading: `open_decisions` equals the pending
        rows a person can go and look at, and reconciles against
        `perry-task list --json`'s `asks.open`. Prose cannot be deduplicated —
        that is the whole bug — so admitting it would put the number back to
        measuring how much the project writes.

        It is not discarded either: it lands in `decision_mentions`, which is
        where a reader looks for questions that ought to be recorded and are
        not. Recording one as a `USER-` row is what makes it countable, which
        is the same move Perry asks of a human.

        The other reading — count unrecorded prose questions too — would put
        this assertion at 1 and break `test_the_number_reconciles_with_the_queue`
        below. If a future row prefers it, this test is the one to change, and
        it should be changed knowingly.
        """
        def build(root):
            (root / "BOARD.md").write_text(board_with_queue(""))
            write(root, "notes/policy.md",
                  "# Policy\n\nWhether migration refuses read-only files is "
                  "still undecided.\n")
        load = self.load(build)
        self.assertEqual(load["open_decisions"], 0,
                         "an unrecorded question was counted, and the number "
                         "no longer reconciles against the queue")
        self.assertEqual(load["decision_mentions"], 1,
                         "an unrecorded question was dropped instead of "
                         "reported")
        self.assertEqual(load["decision_mention_samples"],
                         ["notes/policy.md:3"])

    def test_prose_about_a_recorded_row_is_not_reported_as_unrecorded(self):
        """The mention list is for questions nobody wrote down. A file that
        cites the row it is discussing is doing the right thing."""
        def build(root):
            (root / "BOARD.md").write_text(board_with_queue(
                "| USER-001 | Threshold N | TASK-005 | 6d | pending |\n"))
            write(root, "notes/a.md", "# A\n\nUSER-001 is still undecided.\n")
        load = self.load(build)
        self.assertEqual(load["open_decisions"], 1)

    # ── the exemptions this row must not regress ─────────────────────────
    def test_a_template_declared_tbd_field_is_not_a_decision(self):
        """`Implementation owner: TBD` is a field whose legal value is spelled
        that way — three designs written would otherwise queue three imaginary
        decisions on the user."""
        def build(root):
            write(root, "design/DESIGN-001-thing.md",
                  "# DESIGN-001: Thing\n\n"
                  "> Author: Ran   · Implementation owner: TBD\n"
                  "> Status: draft · Locked: TBD\n\n"
                  "## 4. User Decisions\n\n"
                  "| # | Decision | Options | Chosen | Date |\n"
                  "|---|---|---|---|---|\n"
                  "| 1 | Which store | a / b | **JSONL** | 2026-08-17 |\n")
        load = self.load(build)
        self.assertEqual(load["open_decisions"], 0)
        self.assertEqual(load["decision_mentions"], 0,
                         "a declared field value was reported as a question")

    def test_the_queue_register_reconciles_with_the_queue_on_this_repository(self):
        """Deliverable 3, asserted where it was measured: on Perry's own repo
        LOAD-03 reported 7 against a queue of 2 before this row.

        **This test used to compare the TOTAL, and that was the same defect
        TASK-113 was opened for.** `open_decisions` sums two registers — the
        User Input Queue and design docs with an unfilled `Chosen` row — while
        `perry-task`'s `asks.open` reads only the first. The equality held
        because no design document happened to have an open row, and
        `state/design_TEMPLATE.md` *requires* one before a doc can lock. So
        writing a design document — done twice this week — turned this red, and
        the test's name promised an invariant while it pinned a coincidence.

        What actually reconciles is the queue register against the queue, and
        that survives any number of design docs. The total is asserted as a
        lower bound, which is the relationship that is always true.
        """
        payload = scan(PERRY_HOME)
        tasks = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-task"),
             "list", "--all", "--json"],
            capture_output=True, text=True, timeout=120, cwd=str(PERRY_HOME))
        self.assertEqual(tasks.returncode, 0, tasks.stderr)
        asks_open = json.loads(tasks.stdout)["asks"]["open"]
        load = payload["user_load"]
        self.assertEqual(load["open_decisions_by_register"]["queue"], asks_open,
                         "diagnose and perry-task disagree about how many "
                         "queue rows are waiting on the user")
        self.assertGreaterEqual(load["open_decisions"], asks_open)
        self.assertEqual(load["open_decisions"],
                         sum(load["open_decisions_by_register"].values()),
                         "an open decision came from neither register")

    def test_a_design_doc_with_an_open_row_raises_the_total_and_not_the_queue(self):
        """The break the reconciliation test used to have, as a fixture.

        One pending queue row and one unfilled `Chosen` cell: the total is 2
        and the queue register is 1. That is the state an ordinary design
        document puts the project in, and nothing about it is wrong — which is
        why the check must be per register.
        """
        def build(root):
            (root / "BOARD.md").write_text(board_with_queue(
                "| USER-001 | Threshold N | TASK-005 | 6d | pending |\n"))
            write(root, "design/DESIGN-900-probe.md",
                  "# DESIGN-900: Probe\n\n## 4. User Decisions\n\n"
                  "| # | Decision | Options | Chosen | Date |\n"
                  "|---|---|---|---|---|\n"
                  "| 1 | Which store backs the probe | a / b | TBD | — |\n")
        load = self.load(build)
        self.assertEqual(load["open_decisions"], 2)
        self.assertEqual(load["open_decisions_by_register"],
                         {"queue": 1, "design": 1})


class AFixtureIsNotTheProjectsState(unittest.TestCase):
    """TASK-153. `tests/fixtures/sample-project/BOARD.md` keeps a pending
    `USER-014` because a test needs a board with a pending row on it. LOAD-03
    counted it as one of *Perry's* open decisions, so `diagnose` reported a
    queue of 1 against `perry-task`'s 0 — and only once every one of Perry's
    real rows had been answered did the disagreement become visible.

    The fix is `perry-explain § is_illustrative`, called and not restated. The
    objection the row was opened with is what these tests exist for: this tool
    runs on **any** folder, so the rule may not be a guess about anybody's
    layout. `is_illustrative` decides by directory NAME, relative to the root
    being diagnosed — which is why a project that itself lives inside
    `tests/fixtures/` keeps its whole queue.
    """

    def project(self, root: Path) -> Path:
        (root / ".perry").mkdir(parents=True, exist_ok=True)
        (root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- State root: .\n" + GATE_OFF)
        return root

    # ── the half the objection is about ──────────────────────────────────
    def test_a_project_rooted_inside_a_fixtures_directory_keeps_its_queue(self):
        """The failure mode the fix could have introduced: a vendored or
        embedded project whose real state sits at
        `…/tests/fixtures/vendor-app/` reporting an empty queue because of
        where somebody else filed it. Paths are read relative to the root
        being diagnosed, so none of those directory names is ever seen."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "tests" / "fixtures" / "vendor-app"
            root.mkdir(parents=True)
            self.project(root)
            (root / "BOARD.md").write_text(board_with_queue(
                "| USER-001 | Which region is the default | TASK-005 | 3d | pending |\n"))
            write(root, "notes/rollout.md",
                  "# Rollout\n\nUSER-001 blocks the rollout.\n")
            load = scan(root)["user_load"]
        self.assertEqual(load["open_decisions_by_register"],
                         {"queue": 1, "design": 0},
                         "a project stored under tests/fixtures/ lost its own "
                         "queue")
        self.assertEqual(
            [s.split(" — ")[-1] for s in load["open_decision_samples"]],
            ["USER-001"])

    # ── the half the row was opened for ──────────────────────────────────
    def test_a_fixture_board_is_neither_the_queue_nor_a_row_in_it(self):
        """`examples/BOARD.md` is a fixture, `state/BOARD.md` is the project.

        Three ways this used to go wrong, all in one tree:

        * `examples/` sorts before `state/`, so the `*/BOARD.md` fallback read
          the fixture's queue as the project's;
        * `USER-900` exists only in the fixture, is discussed in the project's
          own notes — which is how a fixture id reaches `in_tracking_doc` —
          and was counted;
        * `USER-001` is defined in the fixture too, because the sorted walk
          reaches `examples/` first. Dropping on the definition point alone
          would lose a real pending row, which is the same miscount with the
          sign flipped.
        """
        with tempfile.TemporaryDirectory() as td:
            root = self.project(Path(td))
            write(root, "examples/BOARD.md", board_with_queue(
                "| USER-001 | Which region is the default | TASK-005 | 9d | pending |\n"
                "| USER-900 | A row a test needs to see pending | TASK-9 | 4d | pending |\n"))
            write(root, "state/BOARD.md", board_with_queue(
                "| USER-001 | Which region is the default | TASK-005 | 3d | pending |\n"))
            write(root, "notes/testing.md",
                  "# Testing\n\nThe board fixture keeps USER-900 pending on "
                  "purpose, and USER-001 is the row it mirrors.\n")
            load = scan(root)["user_load"]
        self.assertEqual(load["open_decisions_by_register"],
                         {"queue": 1, "design": 0})
        samples = load["open_decision_samples"]
        self.assertEqual(len(samples), 1, samples)
        # The evidence must point at the project's board, not the fixture's —
        # the id alone would pass while the reader was sent to `examples/`.
        self.assertTrue(samples[0].startswith("state/BOARD.md:"), samples[0])
        self.assertTrue(samples[0].endswith("— USER-001"), samples[0])

    # ── one rule, one implementation ─────────────────────────────────────
    def test_the_queue_register_asks_perry_explains_own_predicate(self):
        """Agreement over a corpus would pass with two copies of the rule in
        the tree, and a second copy is the defect `bin/perry-diagnose §
        load_sibling` was written to avoid. So this asserts identity: the
        function object the queue register calls is the one `perry-explain`
        defines, proved by replacing it and watching the answer change."""
        diagnose = load_bin_module("perry-diagnose")
        explain = diagnose.load_sibling("perry-explain")
        self.assertNotIn("is_illustrative", vars(diagnose),
                         "perry-diagnose grew its own copy of the rule")

        with tempfile.TemporaryDirectory() as td:
            root = self.project(Path(td))
            write(root, "examples/BOARD.md", board_with_queue(
                "| USER-900 | A row a test needs pending | TASK-9 | 4d | pending |\n"))
            write(root, "notes/testing.md",
                  "# Testing\n\nUSER-900 is the fixture's own row.\n")
            entries = explain.harvest(root)

            self.assertEqual(diagnose.open_user_asks(root, entries, explain), [])

            asked: list[str] = []
            real = explain.is_illustrative
            try:
                explain.is_illustrative = lambda rel: asked.append(rel) or False
                relaxed = diagnose.open_user_asks(root, entries, explain)
            finally:
                explain.is_illustrative = real

        self.assertTrue(asked, "the queue register never consulted the rule")
        self.assertEqual([i for i, _ in relaxed], ["USER-900"],
                         "the register answered from something other than "
                         "perry-explain.is_illustrative")


class AQuotedIdIsNotAQueueRow(unittest.TestCase):
    """TASK-165. The two halves of `user_load` disagreed about `USER-900`.

    The exemption for an id that is QUOTED rather than referenced was built for
    `dangling` and reached `open_decisions_by_register.queue` not at all. So
    `USER-900` — a `tests/fixtures/` board row whose only live mention outside
    the fixture is `TASK-153-result.md:50` quoting the test's own output while
    reporting what the check said — was in `dangling_in_reports` AND in
    `open_decision_samples` at the same time, and `diagnose` reported a queue of
    1 against `perry-task`'s 0.

    **Not a TASK-153 regression.** That fix filters on `is_illustrative`, which
    judges the FILE a row is DEFINED in, and `tests/test_diagnose.py` is
    illustrative. An id quoted out of a report has no definition point at all,
    so there was nothing for that rule to judge and the fallback counted it.

    The fix is `split_dangling`'s own verdict, passed in — `reported_only` is
    already the set of ids every live mention of which is a report. One rule,
    one implementation; these tests are what say so.
    """

    def project(self, root: Path) -> Path:
        (root / ".perry").mkdir(parents=True, exist_ok=True)
        (root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- State root: .\n" + GATE_OFF)
        return root

    # ── the one that stops a fix which just suppresses everything ────────
    def test_a_genuine_row_survives_a_note_quoting_another_id(self):
        """Verification 3, as a fixture. One real pending ask and one id the
        project only quoted back out of a check report, in the same tree.

        A fix that silenced the queue register would pass the reconciliation
        test on this repository — Perry's own queue is empty — and fail here.
        The count must be 1 and it must name `USER-001`.
        """
        with tempfile.TemporaryDirectory() as td:
            root = self.project(Path(td))
            (root / "BOARD.md").write_text(board_with_queue(
                "| USER-001 | Which region is the default | TASK-005 | 3d | pending |\n"))
            # A project note reporting what a check said. `LOAD-03` is one of
            # this checker's own finding codes, so the paragraph announces
            # itself as a report without anybody reading the English — and
            # `USER-902` is defined nowhere, which is what an id lifted out of
            # a report looks like.
            write(root, "notes/check-log.md",
                  "# Check log\n\n"
                  "LOAD-03 named USER-902 as the row it was counting, and the "
                  "id came out of the fixture rather than out of this queue.\n")
            load = scan(root)["user_load"]
        self.assertEqual(load["open_decisions_by_register"],
                         {"queue": 1, "design": 0},
                         "a quoted id was counted as an ask, or a real ask was "
                         "suppressed along with it")
        self.assertEqual(
            [s.split(" — ")[-1] for s in load["open_decision_samples"]],
            ["USER-001"])
        self.assertIn("USER-902", load["dangling_in_reports"],
                      "the fixture no longer exercises the quoted case")

    def test_the_two_halves_of_user_load_agree_about_every_id(self):
        """The shape of the defect, pinned directly: an id the report
        exemption covers must not also be a row of the queue register. Before
        this row `USER-900` was in both lists at once on this repository."""
        load = scan(PERRY_HOME)["user_load"]
        named = {s.split(" — ")[-1] for s in load["open_decision_samples"]}
        self.assertEqual(named & set(load["dangling_in_reports"]), set(),
                         "an id exempted as a quotation is also being counted "
                         "as a pending queue row")

    def test_the_quoted_verdict_has_one_implementation(self):
        """`split_dangling` decides quotation from reference. The queue
        register is handed that answer; it does not re-derive one.

        Asserted by identity rather than by agreement: the register is called
        with a verdict the test invents, and its answer moves. A private copy
        inside `open_user_asks` would keep the old answer, which is exactly how
        `test_the_queue_register_asks_perry_explains_own_predicate` pins the
        other half of the same rule.
        """
        diagnose = load_bin_module("perry-diagnose")
        explain = diagnose.load_sibling("perry-explain")
        with tempfile.TemporaryDirectory() as td:
            root = self.project(Path(td))
            (root / "BOARD.md").write_text(board_with_queue(""))
            write(root, "notes/check-log.md",
                  "# Check log\n\nLOAD-03 named USER-902.\n")
            entries = explain.harvest(root)
            counted = diagnose.open_user_asks(root, entries, explain, set())
            exempt = diagnose.open_user_asks(root, entries, explain,
                                             {"USER-902"})
        self.assertEqual([i for i, _ in counted], ["USER-902"],
                         "the fallback stopped counting an id for some reason "
                         "other than the verdict it was handed")
        self.assertEqual(exempt, [],
                         "the queue register ignored split_dangling's verdict")


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


class TestWritingThatACodeIsGoneDoesNotBringItBack(unittest.TestCase):
    """LOAD-02 must not read its own output as input.

    A signed V5 record in this repository's journal says:

        - the dangling-id check reports [] — TASK-107 resolves and REL-00 is
          gone *(Perry verified)*

    and recording that the report was empty is what put `REL-00` into it. The
    record is append-only — `tests/test_v5_signoff.TestHistoryIsNotRewritten`
    is there to say so — so the finding named a line nobody was permitted to
    fix, and the check could never report zero again once anybody wrote down
    that it had.

    The four exempt shapes are structural, never a reading of the English:
    inside a signed record, inside a blockquote, on a line naming one of this
    checker's own finding codes, or — in a document that reports on a check —
    a mention of an id the project has already reported on. **The anti-vacuity
    half is the point of this class**: an ordinary dangling id still fires
    LOAD-02, and every test that turns one off is paired with one proving the
    check still fires.
    """

    def load(self, files: dict) -> dict:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "BOARD.md").write_text(
                "# Board\n\n## P0\n\n"
                "| ID | Title | Owner | Status | Next action | Evidence |\n"
                "|---|---|---|---|---|---|\n")
            for rel, text in files.items():
                write(root, rel, text)
            return scan(root)["user_load"]

    # ── the check still fires: the anti-vacuity half ─────────────────────
    def test_a_genuinely_dangling_id_still_fails_load_02(self):
        load = self.load({"notes/plan.md":
                          "# Plan\n\nWe are blocked on ZZZ-404 until Friday.\n"})
        self.assertEqual(load["dangling"], ["ZZZ-404"])
        self.assertEqual(load["dangling_in_reports"], [])

    def test_one_live_reference_is_enough_to_keep_an_id_dangling(self):
        """An id quoted in ten reports and used once is still dangling. The
        exemption is per MENTION and the verdict is per id — otherwise burying
        a real reference under reports would silence a true finding."""
        load = self.load({
            "journal/2026-08-20.md":
                "# Journal\n\n## V5 sign-off\n\n"
                "**TASK-001 — V5 sign-off. R, 2026-08-20.**\n\n"
                "**checked**\n\n- ZZZ-404 is gone *(Perry verified)*\n",
            "notes/plan.md": "# Plan\n\nWe are still blocked on ZZZ-404.\n"})
        self.assertEqual(load["dangling"], ["ZZZ-404"])

    # ── the three shapes that are reports ────────────────────────────────
    def test_an_id_only_inside_a_signed_record_is_not_a_reference(self):
        load = self.load({"journal/2026-08-20.md":
                          "# Journal\n\n## Something else\n\nordinary prose.\n\n"
                          "## V5 sign-off\n\n"
                          "**TASK-001 — V5 sign-off. R, 2026-08-20.**\n\n"
                          "**accepted on report**\n\n"
                          "- the dangling-id check reports [] — ZZZ-404 is "
                          "gone *(Perry verified)*\n"})
        self.assertEqual(load["dangling"], [])
        # Containment, not equality: a fixture's own signature header
        # carries ids nobody defined either, and they are exempted for
        # exactly the same reason. Pinning the whole list would be one
        # more assertion about incidental state.
        self.assertIn("ZZZ-404", load["dangling_in_reports"])

    def test_a_signed_record_ends_at_the_next_heading(self):
        """The counterpart to the unclosed-fence test above: a sign-off
        section must not exempt the whole rest of the file."""
        load = self.load({"journal/2026-08-20.md":
                          "# Journal\n\n## V5 sign-off\n\n"
                          "**TASK-001 — V5 sign-off. R, 2026-08-20.**\n\n"
                          "**checked**\n\n- ZZZ-404 is gone *(Perry verified)*\n\n"
                          "## Today\n\nStill blocked on ZZZ-405.\n"})
        self.assertEqual(load["dangling"], ["ZZZ-405"],
                         "a sign-off heading swallowed the rest of the file")
        # Containment, not equality: a fixture's own signature header
        # carries ids nobody defined either, and they are exempted for
        # exactly the same reason. Pinning the whole list would be one
        # more assertion about incidental state.
        self.assertIn("ZZZ-404", load["dangling_in_reports"])

    def test_an_id_only_inside_a_quotation_is_not_a_reference(self):
        """The blockquote is the same statement as the fence `harvest` already
        exempts — these are someone else's words, quoted."""
        load = self.load({"notes/spec.md":
                          "# Spec\n\nThe line the check tripped on was:\n\n"
                          "> - the dangling-id check reports [] and ZZZ-404 "
                          "is gone\n"})
        self.assertEqual(load["dangling"], [])
        # Containment, not equality: a fixture's own signature header
        # carries ids nobody defined either, and they are exempted for
        # exactly the same reason. Pinning the whole list would be one
        # more assertion about incidental state.
        self.assertIn("ZZZ-404", load["dangling_in_reports"])

    def test_an_id_beside_one_of_this_tools_own_finding_codes_is_a_report(self):
        load = self.load({"notes/spec.md":
                          "# Spec\n\nLOAD-02 reports ZZZ-404 dangling, and "
                          "its only source is a signed record.\n"})
        self.assertEqual(load["dangling"], [])
        # Containment, not equality: a fixture's own signature header
        # carries ids nobody defined either, and they are exempted for
        # exactly the same reason. Pinning the whole list would be one
        # more assertion about incidental state.
        self.assertIn("ZZZ-404", load["dangling_in_reports"])

    def test_a_line_naming_a_test_is_a_report_too(self):
        """A review that demonstrates a check going red invents an id to
        demonstrate it with. `perry/evidence/…/TASK-108-dispatch…md` does
        exactly that — "adding one ordinary `DESIGN-900-probe.md` … turns the
        test red" — and charging the project for `DESIGN-900` is the same
        defect as `REL-00`, one document over."""
        load = self.load({"notes/review.md":
                          "# Review\n\nDemonstrated rather than argued: "
                          "adding one ordinary `ZZZ-404-probe.md` turns "
                          "test_the_number_reconciles_with_the_queue red.\n"})
        self.assertEqual(load["dangling"], [])
        self.assertIn("ZZZ-404", load["dangling_in_reports"])

    def test_the_check_name_mark_covers_the_paragraph_not_only_the_line(self):
        """A review names the check in one sentence and the id it demonstrated
        with in the next, and markdown wraps them across four lines. Scoping to
        the line exempts half a sentence and charges the project for the rest —
        which is what `DESIGN-900` did on the base branch.

        The paragraph ENDS at the blank line, and the id after it counts.
        """
        load = self.load({"notes/review.md":
                          "# Review\n\n1. **test_the_number_reconciles pins a\n"
                          "   coincidence.** Demonstrated rather than argued:\n"
                          "   adding one ordinary `ZZZ-404-probe.md` with an\n"
                          "   unfilled row turns it red.\n\n"
                          "We are still blocked on ZZZ-405.\n"})
        self.assertEqual(load["dangling"], ["ZZZ-405"],
                         "the paragraph mark leaked past its blank line")
        self.assertIn("ZZZ-404", load["dangling_in_reports"])

    # ── the fourth shape: a record narrating a check it reported ─────────
    #
    # Both halves of that mark are exercised below, one test each way. The
    # record fixture is `TASK-113-dispatch-…md` in miniature, because that is
    # the document the mark exists for: the account written to CLOSE the row
    # that fixed LOAD-02, whose prose has to say which ids the check reported
    # and therefore put them straight back into the count.
    RECORD = ("# TASK-001 — dispatch record\n\n"
              "## The suite is green\n\n"
              "`git diff` is empty, which was the row's hard bound: the signed\n"
              "record naming ZZZ-404 was never edited, and the fix is in the\n"
              "checker.\n\n"
              "## What LOAD-02 measured afterwards\n\n"
              "Zero, in the agent's own worktree.\n")
    REPORT = ("# Review\n\nLOAD-02 reported ZZZ-404 dangling, and its only "
              "source was a record nobody is permitted to edit.\n")

    def test_a_record_narrating_a_check_it_reported_is_not_a_reference(self):
        """The row that could not be closed, in miniature.

        Neither half of the mark reads English. The id is on the record —
        some other mention of it carries one of the first three marks — and
        the document doing the narrating names a check of its own. Note the
        report and the narration are in DIFFERENT documents, which is exactly
        `DESIGN-900`'s shape: reported in one dispatch record, narrated in the
        next one.
        """
        load = self.load({"notes/review.md": self.REPORT,
                          "evidence/TASK-001-dispatch.md": self.RECORD})
        self.assertEqual(load["dangling"], [])
        self.assertIn("ZZZ-404", load["dangling_in_reports"])

    def test_a_record_about_a_check_still_reports_an_id_it_never_reported_on(self):
        """The ID half — what keeps the fourth mark from becoming a path
        exemption. The same record, now blocked two sections down on an id
        nothing ever reported. Exempting the whole document because of what it
        discusses elsewhere would silence that, and exempting `evidence/`-
        shaped paths would silence every one of them.
        """
        load = self.load({
            "notes/review.md": self.REPORT,
            "evidence/TASK-001-dispatch.md":
                self.RECORD + "\n## Still open\n\n"
                              "We are blocked on ZZZ-405 until Friday.\n"})
        self.assertEqual(load["dangling"], ["ZZZ-405"],
                         "a document that reports on a check exempted an id "
                         "the project never reported on")
        self.assertIn("ZZZ-404", load["dangling_in_reports"])

    def test_a_document_that_reports_on_nothing_is_still_a_reference(self):
        """The DOCUMENT half. `ZZZ-404` is on the record here too, but the
        document relying on it is an ordinary plan that names no check — so
        the mention is an ordinary reference and still counts. Without this
        half, one report anywhere would silence an id everywhere.
        """
        load = self.load({"notes/review.md": self.REPORT,
                          "notes/plan.md": "# Plan\n\nWe are still blocked "
                                           "on ZZZ-404 until Friday.\n"})
        self.assertEqual(load["dangling"], ["ZZZ-404"])

    def test_naming_a_check_does_not_exempt_an_id_that_resolves_elsewhere(self):
        """Why the widening is safe. The rule is applied only to ids that are
        ALREADY undefined everywhere, so a real row cited beside a test name
        was never a candidate for it."""
        load = self.load({
            "BOARD.md": "# Board\n\n## P0\n\n"
                        "| ID | Title | Owner | Status | Next action | Evidence |\n"
                        "|---|---|---|---|---|---|\n"
                        "| ZZZ-404 | A real row | R | not_started | — | — |\n",
            "notes/review.md": "# Review\n\nZZZ-404 is covered by "
                               "test_the_row_still_closes_at_v5.\n"})
        self.assertEqual(load["dangling"], [])
        self.assertEqual(load["dangling_in_reports"], [],
                         "a defined row was routed through the exemption "
                         "instead of simply resolving")

    def test_the_finding_vocabulary_is_read_from_the_catalogue(self):
        """Not a hand-copied list: a finding added later is covered without
        anybody remembering to come back and widen a regex."""
        mod = load_bin_module("perry-diagnose")
        pattern = mod.finding_code_re()
        for fid in mod.WHY:
            self.assertTrue(pattern.search(f"{fid} reports ZZZ-404"), fid)
        self.assertIsNone(pattern.search("TASK-042 is a row, not a finding"))
        self.assertFalse(mod.names_a_check("a test_ is not a check name"))
        self.assertTrue(mod.names_a_check("test_two_flags_do_not_agree"))

    # ── the cost, named rather than hidden ───────────────────────────────
    def test_bare_prose_saying_a_code_is_gone_is_still_a_reference(self):
        """The boundary this fix deliberately does NOT cross.

        A paragraph reading `ZZZ-404 is gone`, carrying none of the three
        marks, still counts. Widening into a list of absence-words is the
        carve-out treadmill LOAD-03 rode for five rounds before `137ffb3`
        replaced the counting rule instead, and this does not start it.
        """
        load = self.load({"notes/plan.md": "# Plan\n\nZZZ-404 is gone now.\n"})
        self.assertEqual(load["dangling"], ["ZZZ-404"])

    def test_perrys_own_repository_reports_the_exemption_it_used(self):
        """An id dropped silently is an exemption nobody can audit."""
        load = scan(PERRY_HOME)["user_load"]
        # Not `dangling == []`: that would be this row's own defect, an
        # assertion over whatever the repository happens to hold today.
        # `test_perry_itself_passes_its_own_id_checks` owns the empty-list
        # gate; this one owns the id the fix was written for.
        self.assertNotIn("REL-00", load["dangling"])
        self.assertIn("REL-00", load["dangling_in_reports"],
                      "the exemption that cleared LOAD-02 is not reported "
                      "beside the count")


# ── work modes ────────────────────────────────────────────────────────────

CONFIG = "# Perry configuration\n\n- Document language: English\n- Repo layout: single\n"


def tracks_section(*rows: str) -> str:
    return ("\n## Tracks\n\n"
            "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
            "|---|---|---|---|---|---|---|---|\n" + "".join(rows))


def board(*sections: str) -> str:
    return "# BOARD\n\n" + "\n".join(sections)


def okr(*extra: str) -> str:
    return "# OKR\n\n## v1: 2026-08-01\n\n### Objective 1: ship it\n\n" + "\n".join(extra)


def modes_of(payload: dict) -> dict:
    return {t["track"]: t for t in payload["work_modes"]["tracks"]}


class TheDatedAndProseCountersPartitionTheCommitments(unittest.TestCase):
    """Every commitment is counted exactly once, in whichever language.

    TASK-091 split `By when` into a typed `Due` and a prose `By when note`, and
    renamed the schema i18n key with it. `diagnose`'s two counters did not move
    together: `dated` read `due` OR `by when`, `prose` read only `by when` — so
    a Chinese register's `截止`, which now resolves to `due`, carried prose,
    failed the date test, and **was counted by neither**. Measured across that
    commit by a V4: a board that scored `queue` with 1 standing commitment
    before scored no mode and no evidence after, while the English board was
    unchanged.

    The invariant is a partition, so it is tested as one: a commitment with a
    promise in it is either dated or prose, never both and never neither. That
    is why these assert on the SUM rather than on each counter — a future
    third counter that silently swallowed a case would pass a per-counter test.
    """

    def commitments(self, td: str, header: str, cell: str) -> dict:
        root = Path(td)
        write(root, ".perry/config.md", CONFIG)
        write(root, "OKR.md",
              "# OKR v1\n\n## Commitments\n\n"
              f"| ID | Promise | To whom | {header} | Status |\n"
              "|---|---|---|---|---|\n"
              f"| C-001 | ship the thing | ops | {cell} | open |\n")
        ev = modes_of(scan(root))["main"]["evidence"]
        flat = [e for v in ev.values() for e in v]
        return {
            "dated": sum(1 for e in flat if "promise a dated" in e),
            "prose": sum(1 for e in flat if "standing commitment" in e),
        }

    def test_english_and_chinese_score_the_same_promise_the_same_way(self):
        pairs = [("By when", "month by month", "截止", "逐月"),
                 ("Due", "2026-09-30", "截止", "2026-09-30"),
                 ("By when note", "quarterly-ish", "截止说明", "大约每季度")]
        for en_h, en_c, zh_h, zh_c in pairs:
            with self.subTest(promise=en_c):
                with tempfile.TemporaryDirectory() as td:
                    en = self.commitments(td, en_h, en_c)
                with tempfile.TemporaryDirectory() as td:
                    zh = self.commitments(td, zh_h, zh_c)
                self.assertEqual(en, zh,
                                 f"`{en_h}`/`{en_c}` and `{zh_h}`/`{zh_c}` are "
                                 f"the same promise written twice; scoring "
                                 f"them differently is the asymmetry the "
                                 f"`By when` → `Due` rename introduced")
                self.assertEqual(en["dated"] + en["prose"], 1,
                                 f"a commitment carrying a promise must be "
                                 f"counted exactly once; got {en}")

    def test_a_date_buried_in_prose_is_prose(self):
        """`2026-09-30 or so` is not a dated promise.

        `bin/perry-goals` refuses that value on `--due` and files it under
        `By when note`. `diagnose` used an unanchored `\\b...\\b` search and
        called it dated — the same cell, two answers, from the tool pair whose
        job is to agree. `lib.is_iso_date` is now the only spelling.
        """
        with tempfile.TemporaryDirectory() as td:
            got = self.commitments(td, "Due", "2026-09-30 or so")
        self.assertEqual(got, {"dated": 0, "prose": 1}, got)
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(self.commitments(td, "Due", "2026-09-30"),
                             {"dated": 1, "prose": 0})

    def test_impossible_and_interior_decorated_dates_are_not_dates(self):
        for value in ("2026-02-30", "2026-13-45", "2026-**09**-30"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as td:
                self.assertEqual(self.commitments(td, "Due", value),
                                 {"dated": 0, "prose": 1})
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(self.commitments(td, "Due", "**2026-09-30**"),
                             {"dated": 1, "prose": 0})

    def test_unfilled_markers_are_not_reclassified_as_prose(self):
        for value in ("n/a", "N/a", "N.A.", "TBD", "?", "？", "无", "无。", "待定",
                      "不适用", "不适用。", "**暂无！**"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as td:
                self.assertEqual(self.commitments(td, "Due", value),
                                 {"dated": 0, "prose": 0})

    def test_diagnose_calls_the_shared_blank_and_date_predicates(self):
        mod = load_bin_module("perry-diagnose")
        blank_calls = []
        date_calls = []
        original_blank = mod.lib.is_blank_cell
        original_date = mod.lib.is_iso_date
        mod.lib.is_blank_cell = lambda value: blank_calls.append(value) is None and value == "BLANK-SENTINEL"
        mod.lib.is_iso_date = lambda value: date_calls.append(value) is None and value == "DATE-SENTINEL"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG)
            write(root, "OKR.md",
                  "# OKR\n\n## Commitments\n\n"
                  "| ID | Track | Promise | To whom | Due | Status | By when note |\n"
                  "|---|---|---|---|---|---|---|\n"
                  "| C-1 | main | a | ops | DATE-SENTINEL | open | BLANK-SENTINEL |\n")
            try:
                mod.scan_work_modes(root, root)
            finally:
                mod.lib.is_blank_cell = original_blank
                mod.lib.is_iso_date = original_date
        self.assertIn("BLANK-SENTINEL", blank_calls)
        self.assertIn("DATE-SENTINEL", date_calls)

    def test_there_is_one_spelling_of_is_this_cell_a_date(self):
        """The uniqueness claim, checked by grep rather than asserted in prose.

        `bin/perry-goals` carried a comment reading "the one spelling of 'is
        this cell a date'" while `bin/perry-diagnose` carried a second,
        unanchored one — so `2026-09-30 or so` was refused by the writer and
        counted as a dated promise by the reader. A claim of uniqueness that a
        grep disproves is worse than no claim, because it stops the next reader
        from grepping.

        **Scoped to the PREDICATE form**, `fullmatch` against a bare date, and
        that scope is deliberate. Three tools asked exactly this about a
        knowledge card's `Last verified` and each spelled it out; they now
        import `lib.is_iso_date`, which also strips the decoration a cell may
        carry.

        What this does NOT cover, said plainly rather than left to be
        discovered: `re.search` for a date INSIDE text is a different question
        (four sites: `perry-task` x2, `perry-goals`, `perry-state` — extracting
        a date from a status line is not asking whether a cell is one), and
        `bin/perry-decide:459` prefix-matches a sunset timestamp and then
        slices ten characters, which is a third. Both are real duplication and
        neither is this defect; folding them in without measuring what changes
        would be a rename wearing a fix's clothes.
        """
        bad = []
        for tool in sorted((PERRY_HOME / "bin").iterdir()):
            if not tool.is_file() or tool.name.startswith("."):
                continue
            try:
                text = tool.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for n, line in enumerate(text.split("\n"), 1):
                if line.lstrip().startswith("#"):
                    continue
                if "fullmatch" in line and r"\d{4}-\d{2}-\d{2}" in line:
                    bad.append(f"{tool.name}:{n}: {line.strip()[:70]}")
        self.assertEqual(bad, [],
                         "a second predicate for `is this cell a date` — "
                         "import `lib.is_iso_date` instead, or this is how "
                         "`--due` and `diagnose` disagreed about the same "
                         "cell")


class TestWorkModeDetection(unittest.TestCase):
    """`diagnose` names which of DESIGN-003's four shapes a track's work fits.

    The load-bearing half is the refusal. Three of the four modes are read off
    columns a project may simply not have, and a scanner that fell back to
    `project` on an absent signal would print a verdict for every folder on
    earth having measured none of them — the same defect `reference/diagnose.md`
    names when it calls a signal that never clears worse than no check, facing
    the other way.
    """

    def test_a_folder_with_no_distinguishing_signal_gets_cannot_tell(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "AGENTS.md", "# rules\nrun make test\n")
            write(root, "Makefile", "test:\n\techo ok\n")
            t = modes_of(scan(root))["main"]
        self.assertIsNone(t["mode"], f"a bare folder was assigned {t['mode']}")
        self.assertEqual(t["confidence"], "none")
        self.assertEqual(t["scores"], {"project": 0, "pipeline": 0,
                                       "queue": 0, "inquiry": 0})

    def test_cannot_tell_is_printed_as_itself(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, "AGENTS.md", "# rules\n")
            out = subprocess.run(
                [sys.executable, str(DIAGNOSE), "--root", str(root), "--text"],
                capture_output=True, text=True, timeout=120).stdout
        self.assertIn("evidence says cannot tell", out)
        self.assertNotIn("evidence says project", out)

    def test_a_phase_and_objective_spine_reads_as_project(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG)
            write(root, "OKR.md", okr())
            write(root, "phase/CURRENT", "001-mvp\n")
            write(root, "phase/001-mvp.md", "# Phase 001\n")
            write(root, "BOARD.md", board(
                "## P0\n\n| ID | Title | Owner | Status |\n|---|---|---|---|\n"
                "| REL-1 | Ship it | Agent | in_progress |\n"))
            t = modes_of(scan(root))["main"]
        self.assertEqual(t["mode"], "project")
        self.assertEqual(t["confidence"], "high")
        # Each signal named separately, so dropping any one of them goes red
        # rather than being absorbed by the others' margin.
        self.assertTrue(any("phase/" in e for e in t["evidence"]["project"]))
        self.assertTrue(any("objective" in e for e in t["evidence"]["project"]))

    def test_intake_and_arrived_dates_read_as_queue(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG)
            write(root, "BOARD.md", board(
                "## Intake\n\n| Arrived | Request | Outcome |\n|---|---|---|\n"
                "| 2026-08-14 | Reconcile Q3 vendor spend | — |\n",
                "## P1\n\n| ID | Title | Owner | Status | Arrived | Stage |\n"
                "|---|---|---|---|---|---|\n"
                "| OPS-1 | Vendor invoice | Agent | in_progress | 2026-08-14 | triaged |\n"))
            t = modes_of(scan(root))["main"]
        self.assertEqual(t["mode"], "queue")
        self.assertEqual(t["confidence"], "high")
        self.assertTrue(any("Intake" in e for e in t["evidence"]["queue"]))
        self.assertTrue(any("Arrived" in e for e in t["evidence"]["queue"]))
        self.assertTrue(any("stage vocabulary" in e
                            for e in t["evidence"]["queue"]))

    def test_a_parent_column_and_answer_files_read_as_inquiry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG)
            write(root, "BOARD.md", board(
                "## P1\n\n| ID | Title | Owner | Status | Stage | Parent |\n"
                "|---|---|---|---|---|---|\n"
                "| Q-1 | Does batching cut cost? | Agent | in_progress | researching | — |\n"
                "| Q-2 | Per-call cost today? | Agent | done | answered | Q-1 |\n"))
            write(root, "evidence/2026-08/Q-2-answer.md", "# Answer\n$0.004 [SRC-1]\n")
            t = modes_of(scan(root))["main"]
        self.assertEqual(t["mode"], "inquiry")
        self.assertEqual(t["confidence"], "high")
        self.assertTrue(any("Parent" in e for e in t["evidence"]["inquiry"]))
        self.assertTrue(any("answer file" in e for e in t["evidence"]["inquiry"]))
        self.assertTrue(any("stage vocabulary" in e
                            for e in t["evidence"]["inquiry"]))

    def test_stage_since_and_dated_commitments_read_as_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG)
            write(root, "OKR.md",
                  "# OKR\n\n## Commitments\n\n"
                  "| Id | Track | Promise | To whom | Due | Status |\n"
                  "|---|---|---|---|---|---|\n"
                  "| blog/1 | blog | Launch post | Marketing | 2026-09-30 | active |\n")
            write(root, "BOARD.md", board(
                "## P1\n\n| ID | Title | Owner | Status | Stage | Stage since | Commitment |\n"
                "|---|---|---|---|---|---|---|\n"
                "| POST-1 | Launch post | Agent | in_progress | draft | 2026-08-12 | blog/1 |\n"))
            t = modes_of(scan(root))["main"]
        self.assertEqual(t["mode"], "pipeline")
        self.assertEqual(t["confidence"], "high")
        self.assertTrue(any("Stage since" in e
                            for e in t["evidence"]["pipeline"]))
        self.assertTrue(any("Commitment" in e for e in t["evidence"]["pipeline"]))
        self.assertTrue(any("dated `Due`" in e
                            for e in t["evidence"]["pipeline"]))
        self.assertTrue(any("stage vocabulary" in e
                            for e in t["evidence"]["pipeline"]))

    def test_a_by_when_note_reads_as_a_standing_commitment(self):
        """After TASK-091 the pipeline/queue signal is a COLUMN, not a regex
        over a cell: a dated promise carries `Due`, a standing one carries
        `By when note`."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG)
            write(root, "OKR.md",
                  "# OKR\n\n## Commitments\n\n"
                  "| Id | Track | Promise | To whom | Due | Status | By when note |\n"
                  "|---|---|---|---|---|---|---|\n"
                  "| ops/1 | ops | Invoices | Finance | 3d | active | within the track SLA |\n")
            write(root, "BOARD.md", board(
                "## P1\n\n| ID | Title | Owner | Status |\n"
                "|---|---|---|---|\n"
                "| OPS-1 | Reconcile | Agent | in_progress |\n"))
            t = modes_of(scan(root))["main"]
        self.assertTrue(any("By when note" in e for e in t["evidence"]["queue"]),
                        t["evidence"]["queue"])

    def test_a_pre_split_register_is_still_recognised(self):
        """This tool diagnoses FOREIGN projects — the one job ADR-007 keeps a
        parser for. A register written before the split still has to read as
        what it is, or adoption reports a project has no commitments."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG)
            write(root, "OKR.md",
                  "# OKR\n\n## Commitments\n\n"
                  "| Id | Track | Promise | To whom | By when | Status |\n"
                  "|---|---|---|---|---|---|\n"
                  "| blog/1 | blog | Launch post | Marketing | 2026-09-30 | active |\n"
                  "| ops/1 | ops | Invoices | Finance | within the track SLA | active |\n")
            write(root, "BOARD.md", board(
                "## P1\n\n| ID | Title | Owner | Status |\n"
                "|---|---|---|---|\n"
                "| POST-1 | Launch post | Agent | in_progress |\n"))
            t = modes_of(scan(root))["main"]
        self.assertTrue(any("dated `Due`" in e for e in t["evidence"]["pipeline"]),
                        t["evidence"]["pipeline"])
        self.assertTrue(any("By when note" in e for e in t["evidence"]["queue"]),
                        t["evidence"]["queue"])

    def test_conflicting_signals_are_reported_as_a_tie_not_a_winner(self):
        """`low` and `none` are both 'cannot tell', and the payload keeps them
        apart: nothing found is a different fact from two things found that
        disagree."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG)
            write(root, "BOARD.md", board(
                "## P1\n\n| ID | Title | Owner | Status | Arrived | Parent |\n"
                "|---|---|---|---|---|---|\n"
                "| X-1 | Something | Agent | in_progress | 2026-08-14 | X-0 |\n"))
            t = modes_of(scan(root))["main"]
        self.assertIsNone(t["mode"])
        self.assertEqual(t["confidence"], "low")
        self.assertEqual(t["scores"]["queue"], t["scores"]["inquiry"])

    def test_the_declaration_is_never_its_own_evidence(self):
        """A register row carries `Stages`, `SLA` and `Cycle`. Scoring those
        would let a declaration confirm itself, and MODE-01 could never fire."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG + tracks_section(
                "| blog | pipeline | commitments | brief→draft→review→approved→published "
                "| review:2 | 5d | 2026-W34 | V5 |\n"))
            write(root, "BOARD.md", board("## P1\n\n| ID | Title |\n|---|---|\n"))
            t = modes_of(scan(root))["blog"]
        self.assertIsNone(t["mode"], "the register scored itself as evidence")
        self.assertEqual(t["scores"]["pipeline"], 0)


class TestASharedSignalScoresForEveryModeThatOwnsIt(unittest.TestCase):
    """Two of the columns this scanner reads are named by **two** contracts.

    `Stage since` is pipeline's *Stage clock* and inquiry's *Question clock*
    (`modes/inquiry.md` § contract, whose triage step 2 computes
    `today − Stage since`). `Commitment` is pipeline's *Commitment link* and
    the cell `modes/queue.md` gives a routed intake row, carries on every row,
    and names an SLA breach by. Attributing either to `pipeline` alone let one
    column contradict a declaration the user wrote on purpose.
    """

    @staticmethod
    def inquiry_board(root: Path, declared_mode: str = "inquiry") -> None:
        """A canonical inquiry track: root questions, own stage vocabulary.

        `Parent` is empty because these are roots — `modes/inquiry.md` §
        contract defines the spine as exactly the rows with an empty `Parent`
        — and the stages are the track's own, which the register explicitly
        permits. So the inquiry-shaped signals a scanner might look for are
        legitimately absent, and the only column left is the question clock.
        """
        write(root, ".perry/config.md", CONFIG + tracks_section(
            f"| study | {declared_mode} | questions | scoping→reading→synthesis "
            f"| open:5 | — | — | V4 |\n"))
        write(root, "BOARD.md", board(
            "## P1\n\n| ID | Title | Owner | Status | Track | Stage | Stage since | Parent |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| Q-1 | Does batching cut cost? | Agent | in_progress | study | reading | 2026-08-10 | — |\n"
            "| Q-2 | What do vendors charge? | Agent | in_progress | study | scoping | 2026-08-12 | — |\n"))

    @staticmethod
    def queue_board(root: Path, declared_mode: str = "queue") -> None:
        """A queue track whose rows name the commitment they discharge.

        `modes/queue.md § Standing commitments` writes the link from the board
        side — the row's `Commitment` cell carries the promise's `Id` — so this
        board is doing exactly what that file asks for.
        """
        write(root, ".perry/config.md", CONFIG + tracks_section(
            f"| ops | {declared_mode} | commitments | waiting→working→closed "
            f"| — | 5d | monthly | V2 |\n"))
        write(root, "BOARD.md", board(
            "## P1\n\n| ID | Title | Owner | Status | Track | Stage | Commitment |\n"
            "|---|---|---|---|---|---|---|\n"
            "| OPS-1 | Vendor invoice | Agent | in_progress | ops | working | ops/1 |\n"
            "| OPS-2 | Access review | Agent | not_started | ops | waiting | ops/1 |\n"))

    def test_the_question_clock_is_inquiry_evidence_too(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.inquiry_board(root)
            t = modes_of(scan(root))["study"]
        self.assertEqual(t["scores"]["inquiry"], t["scores"]["pipeline"],
                         "`Stage since` was attributed to one of its two owners")
        self.assertTrue(any("Stage since" in e for e in t["evidence"]["inquiry"]),
                        "the question clock is missing from inquiry's evidence")
        self.assertTrue(any("Stage since" in e for e in t["evidence"]["pipeline"]),
                        "the stage clock is missing from pipeline's evidence")

    def test_the_commitment_cell_is_queue_evidence_too(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.queue_board(root)
            t = modes_of(scan(root))["ops"]
        self.assertEqual(t["scores"]["queue"], t["scores"]["pipeline"],
                         "`Commitment` was attributed to one of its two owners")
        self.assertTrue(any("Commitment" in e for e in t["evidence"]["queue"]))
        self.assertTrue(any("Commitment" in e for e in t["evidence"]["pipeline"]))

    def test_a_shared_column_cannot_separate_its_own_owners(self):
        """The reproduction. A board carrying only the question clock is a
        board that fits pipeline and inquiry equally, and the honest report is
        the tie — not the alphabetically luckier of the two."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.inquiry_board(root)
            payload = scan(root)
        t = modes_of(payload)["study"]
        self.assertIsNone(t["mode"], f"a shared column named `{t['mode']}`")
        self.assertEqual(t["confidence"], "low")
        self.assertNotIn("MODE-01", ids(payload),
                         "a correct declaration was contradicted by a column "
                         "its own mode contract names")

    def test_a_queue_row_naming_its_commitment_is_not_accused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.queue_board(root)
            payload = scan(root)
        self.assertNotIn("MODE-01", ids(payload))

    def test_shared_evidence_alone_never_reaches_high(self):
        """Both shared columns at once do point at pipeline — it is the only
        mode that owns both — but the whole case rests on evidence two other
        contracts also claim. That is a `medium`, and `MODE-01` does not fire
        on `medium`."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG + tracks_section(
                "| ops | queue | commitments | waiting→working→closed | — | 5d | monthly | V2 |\n"))
            write(root, "BOARD.md", board(
                "## P1\n\n| ID | Title | Owner | Status | Track | Stage | Stage since | Commitment |\n"
                "|---|---|---|---|---|---|---|---|\n"
                "| OPS-1 | Vendor invoice | Agent | in_progress | ops | working | 2026-08-10 | ops/1 |\n"))
            payload = scan(root)
        t = modes_of(payload)["ops"]
        self.assertEqual(t["mode"], "pipeline")
        self.assertEqual(t["confidence"], "medium")
        self.assertNotIn("MODE-01", ids(payload))

    def test_a_correctly_declared_inquiry_track_reads_as_inquiry(self):
        """The clearing case, and the one that matters most: the same board
        plus one signal only inquiry owns is named, with confidence, as what
        it says it is. A fix that made every inquiry track unreadable would
        pass every test above."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.inquiry_board(root)
            write(root, "evidence/2026-08/Q-3-answer.md", "# Answer\n$0.004 [SRC-1]\n")
            payload = scan(root)
        t = modes_of(payload)["study"]
        self.assertEqual(t["mode"], "inquiry")
        self.assertEqual(t["confidence"], "high")
        self.assertNotIn("MODE-01", ids(payload))

    def test_a_correctly_declared_queue_track_reads_as_queue(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.queue_board(root)
            write(root, "BOARD.md", (root / "BOARD.md").read_text() + (
                "\n## Intake\n\n| Arrived | Request | Outcome |\n|---|---|---|\n"
                "| 2026-08-14 | Reconcile Q3 vendor spend | — |\n"))
            payload = scan(root)
        t = modes_of(payload)["ops"]
        self.assertEqual(t["mode"], "queue")
        self.assertEqual(t["confidence"], "high")
        self.assertNotIn("MODE-01", ids(payload))


class TestHighIsMoreThanOneSignal(unittest.TestCase):
    """`MODE-01` is gated on `high`, and it is the only finding that
    contradicts something the user deliberately wrote down. So `high` costs
    more than one column."""

    def test_one_structural_signal_alone_is_medium(self):
        """`Arrived` is queue's alone and it is worth 3. Under the old rule
        `top >= 3` and a margin of 3 over an empty field made that `high`, so
        one column could accuse a declaration."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG + tracks_section(
                "| ops | pipeline | commitments | — | — | 5d | 2026-W34 | V5 |\n"))
            write(root, "BOARD.md", board(
                "## P1\n\n| ID | Title | Owner | Status | Track | Arrived |\n"
                "|---|---|---|---|---|---|\n"
                "| OPS-1 | Vendor invoice | Agent | in_progress | ops | 2026-08-14 |\n"))
            payload = scan(root)
        t = modes_of(payload)["ops"]
        self.assertEqual(t["mode"], "queue")
        self.assertEqual(t["confidence"], "medium",
                         "one column was enough to be sure")
        self.assertNotIn("MODE-01", ids(payload))

    def test_a_narrow_lead_is_medium_however_many_signals(self):
        """The other half of the gate. Two inquiry signals against one queue
        signal is a lead of 2 — real, and not a margin. `HIGH_MARGIN` is what
        keeps it out of a finding."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG + tracks_section(
                "| ops | queue | commitments | — | — | 5d | monthly | V2 |\n"))
            write(root, "BOARD.md", board(
                "## P1\n\n| ID | Title | Owner | Status | Track | Stage | Arrived | Parent |\n"
                "|---|---|---|---|---|---|---|---|\n"
                "| X-1 | Something | Agent | in_progress | ops | researching | 2026-08-14 | X-0 |\n"))
            payload = scan(root)
        t = modes_of(payload)["ops"]
        self.assertEqual(t["mode"], "inquiry")
        self.assertEqual(t["scores"]["inquiry"] - t["scores"]["queue"], 2)
        self.assertEqual(t["confidence"], "medium")
        self.assertNotIn("MODE-01", ids(payload))

    def test_no_single_signal_can_reach_the_high_floor(self):
        """The invariant the two numbers encode, asserted over the numbers
        themselves so that raising a weight later cannot quietly restore
        one-column certainty. Two shared signals sum below the floor too, so
        `high` always rests on evidence exactly one mode owns."""
        mod = load_bin_module("perry-diagnose")
        self.assertLess(mod.STRUCTURAL, mod.HIGH_SCORE)
        self.assertLess(mod.CORROBORATING, mod.HIGH_SCORE)
        self.assertLess(2 * mod.SHARED, mod.HIGH_SCORE)

    def test_every_column_signal_names_modes_that_exist(self):
        """The attribution table is data now. A typo in an owner tuple would
        otherwise score a mode nothing ever reads."""
        mod = load_bin_module("perry-diagnose")
        seen = set()
        for col, owners, phrase in mod.COLUMN_SIGNALS:
            seen.add(col)
            self.assertTrue(owners, f"`{col}` belongs to no mode")
            for m in owners:
                self.assertIn(m, mod.MODE_NAMES, f"`{col}` names `{m}`")
        self.assertEqual(seen, {"stage since", "commitment", "arrived", "parent"})


class TestModeDisagreementIsAFinding(unittest.TestCase):
    """MODE-01. A project whose register says `pipeline` and whose board shows
    a steady-state queue has one of the two wrong, and which one is the user's
    to say."""

    @staticmethod
    def queue_shaped(root: Path, declared_mode: str) -> None:
        write(root, ".perry/config.md", CONFIG + tracks_section(
            f"| ops | {declared_mode} | commitments | new→triaged→resolved | — | 5d | monthly | V2 |\n"))
        write(root, "BOARD.md", board(
            "## Intake\n\n| Arrived | Request | Outcome |\n|---|---|---|\n"
            "| 2026-08-14 | Reconcile Q3 vendor spend | — |\n",
            "## P1\n\n| ID | Title | Owner | Status | Track | Arrived | Stage |\n"
            "|---|---|---|---|---|---|---|\n"
            "| OPS-1 | Vendor invoice | Agent | in_progress | ops | 2026-08-14 | triaged |\n"))

    def test_a_pipeline_label_over_queue_work_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.queue_shaped(root, "pipeline")
            payload = scan(root)
        self.assertIn("MODE-01", ids(payload))
        f = next(x for x in payload["findings"] if x["id"] == "MODE-01")
        self.assertIn("pipeline", f["title"])
        self.assertIn("queue", f["title"])
        self.assertTrue(f["evidence"], "the finding cites no evidence")
        self.assertTrue(any("Intake" in e for e in f["evidence"]))

    def test_the_same_board_labelled_queue_is_not_a_finding(self):
        """The clearing case. A finding whose signal survives the fix is worse
        than no finding at all."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.queue_shaped(root, "queue")
            payload = scan(root)
        self.assertNotIn("MODE-01", ids(payload))
        self.assertEqual(modes_of(payload)["ops"]["mode"], "queue")

    def test_an_undeclared_project_is_never_told_its_mode_is_wrong(self):
        """The implicit `main` track is a default, not a claim. Reporting a
        disagreement with a value the user never wrote would fire on every
        project Perry has ever adopted."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG)
            write(root, "BOARD.md", board(
                "## Intake\n\n| Arrived | Request | Outcome |\n|---|---|---|\n"
                "| 2026-08-14 | Reconcile Q3 vendor spend | — |\n",
                "## P1\n\n| ID | Title | Owner | Status | Arrived | Stage |\n"
                "|---|---|---|---|---|---|\n"
                "| OPS-1 | Vendor invoice | Agent | in_progress | 2026-08-14 | triaged |\n"))
            payload = scan(root)
        self.assertNotIn("MODE-01", ids(payload))
        self.assertEqual(modes_of(payload)["main"]["mode"], "queue")

    def test_cannot_tell_never_produces_a_disagreement(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG + tracks_section(
                "| ops | queue | commitments | — | — | 5d | monthly | V2 |\n"))
            write(root, "BOARD.md", board("## P1\n\n| ID | Title |\n|---|---|\n"))
            payload = scan(root)
        self.assertIsNone(modes_of(payload)["ops"]["mode"])
        self.assertNotIn("MODE-01", ids(payload))


class TestPerTrackAttribution(unittest.TestCase):
    def test_two_tracks_are_judged_from_their_own_rows(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG + tracks_section(
                "| ops | queue | commitments | new→triaged→resolved | — | 5d | monthly | V2 |\n",
                "| study | inquiry | questions | open→researching→answered | open:5 | — | — | V4 |\n"))
            write(root, "BOARD.md", board(
                "## P1\n\n| ID | Title | Owner | Status | Track | Arrived | Parent | Stage |\n"
                "|---|---|---|---|---|---|---|---|\n"
                "| OPS-1 | Vendor invoice | Agent | in_progress | ops | 2026-08-14 | — | triaged |\n"
                "| Q-2 | Per-call cost? | Agent | in_progress | study | — | Q-1 | researching |\n"))
            m = modes_of(scan(root))
        self.assertEqual(m["ops"]["mode"], "queue")
        self.assertEqual(m["study"]["mode"], "inquiry")
        self.assertEqual(m["ops"]["scores"]["inquiry"], 0,
                         "the study track's rows leaked into ops")
        self.assertEqual(m["study"]["scores"]["queue"], 0,
                         "the ops track's rows leaked into study")

    def test_project_wide_signals_are_withheld_when_they_cannot_be_attributed(self):
        """`phase/` and `## Intake` carry no track column. On a two-track
        project they say nothing about either one, and a scanner that spread
        them across both would hand every track the same evidence."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG + tracks_section(
                "| ops | queue | commitments | — | — | 5d | monthly | V2 |\n",
                "| build | project | phase/ | — | — | — | — | V3 |\n"))
            write(root, "OKR.md", okr())
            write(root, "phase/CURRENT", "001-mvp\n")
            write(root, "phase/001-mvp.md", "# Phase 001\n")
            write(root, "BOARD.md", board("## P1\n\n| ID | Title |\n|---|---|\n"))
            m = modes_of(scan(root))
        for name in ("ops", "build"):
            self.assertEqual(m[name]["scores"]["project"], 0,
                             f"phase/ was attributed to `{name}` anyway")
            self.assertIsNone(m[name]["mode"])

    def test_a_single_declared_track_does_get_the_project_wide_signals(self):
        """The other half of the same rule — with one track there is exactly
        one thing to attribute them to, so withholding them would throw away
        the strongest evidence a Perry project has."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG + tracks_section(
                "| build | project | phase/ | — | — | — | — | V3 |\n"))
            write(root, "OKR.md", okr())
            write(root, "phase/CURRENT", "001-mvp\n")
            write(root, "phase/001-mvp.md", "# Phase 001\n")
            write(root, "BOARD.md", board("## P1\n\n| ID | Title |\n|---|---|\n"))
            t = modes_of(scan(root))["build"]
        self.assertEqual(t["mode"], "project")


class TestModeColumnsResolveByName(unittest.TestCase):
    def test_a_reordered_header_still_resolves(self):
        """Board columns are optional and reorderable. A positional read
        attributes one column's value to another the moment a project omits
        one — the bug a V4 review already found twice in this repo."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG)
            write(root, "BOARD.md", board(
                "## P1\n\n| Parent | Status | ID | Stage | Title |\n"
                "|---|---|---|---|---|\n"
                "| Q-1 | in_progress | Q-2 | researching | Per-call cost? |\n"))
            t = modes_of(scan(root))["main"]
        self.assertEqual(t["mode"], "inquiry")

    def test_the_chinese_column_names_resolve(self):
        """`schema/state-schema.json § i18n.columns` is the one list of these,
        and this scanner reads it rather than carrying a copy."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG)
            write(root, "BOARD.md", board(
                "## P1\n\n| 编号 | 标题 | 状态 | 到达 | 阶段 |\n"
                "|---|---|---|---|---|\n"
                "| OPS-1 | 对账 | in_progress | 2026-08-14 | triaged |\n"))
            t = modes_of(scan(root))["main"]
        self.assertEqual(t["mode"], "queue")
        self.assertTrue(any("Arrived" in e for e in t["evidence"]["queue"]),
                        "`到达` no longer resolves to the Arrived column")
        self.assertTrue(any("stage vocabulary" in e
                            for e in t["evidence"]["queue"]),
                        "`阶段` no longer resolves to the Stage column")

    def test_a_shared_stage_word_distinguishes_nothing(self):
        """`review` is pipeline's default stage AND a global Status value;
        `in_progress` is queue's AND a global Status value. Counting either
        would hand a mode to any board that uses the status enum."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root, ".perry/config.md", CONFIG)
            write(root, "BOARD.md", board(
                "## P1\n\n| ID | Title | Status | Stage |\n|---|---|---|---|\n"
                "| A-1 | Thing | review | review |\n"
                "| A-2 | Other | in_progress | in_progress |\n"))
            t = modes_of(scan(root))["main"]
        self.assertIsNone(t["mode"])
        self.assertEqual(t["confidence"], "none")


class TestModeScannerReportsItsOwnAbsence(unittest.TestCase):
    def test_the_scanner_is_available_on_every_shipped_fixture(self):
        """`available: false` is the honest answer when the track parser cannot
        be loaded — and it must not be the answer anywhere real, or every test
        above passes over a scanner that ran on nothing."""
        for name in ("sample-project", "sample-project-zh"):
            with self.subTest(fixture=name):
                p = scan(PERRY_HOME / "tests" / "fixtures" / name)
                self.assertTrue(p["work_modes"]["available"])
                self.assertTrue(p["work_modes"]["tracks"])


if __name__ == "__main__":
    unittest.main()
