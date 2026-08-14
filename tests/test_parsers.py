"""Contract tests for Perry's state format.

These exist because the format lives in three places — SKILL.md prose,
`state/*_TEMPLATE.md`, and `viewer/parsers.py` — and nothing else stops them
drifting apart. Every test here pins one of those agreements.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
FIXTURE = PERRY_HOME / "tests" / "fixtures" / "sample-project"
sys.path.insert(0, str(PERRY_HOME / "viewer"))

import parsers as P  # noqa: E402


def read(rel: str) -> str:
    return (PERRY_HOME / rel).read_text()


def load_bin_module(name: str):
    """Import an extensionless script from bin/ as a module (no .py suffix, so
    the default loader can't infer one)."""
    import importlib.util
    from importlib.machinery import SourceFileLoader

    path = PERRY_HOME / "bin" / name
    loader = SourceFileLoader(name.replace("-", "_"), str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class TemplateContract(unittest.TestCase):
    """The shipped templates must parse. A template the parser can't read is
    the exact failure that made the viewer show empty panels."""

    def test_okr_template_yields_objectives_and_krs(self):
        okr = P.parse_okr(read("okr/state/OKR_TEMPLATE.md"))
        self.assertTrue(okr.objectives, "no objectives parsed from OKR_TEMPLATE")
        for obj in okr.objectives:
            self.assertTrue(obj.krs, f"objective {obj.title!r} parsed with zero KRs")
        ids = [kr.id for obj in okr.objectives for kr in obj.krs]
        self.assertIn("KR-O1.1", ids)
        self.assertTrue(any(kr.stretch for o in okr.objectives for kr in o.krs),
                        "Stretch? column not read")

    def test_okr_template_ignores_commented_example_version(self):
        """The template parks a `## v2:` example inside an HTML comment. It
        must not shadow v1 as the current version."""
        okr = P.parse_okr(read("okr/state/OKR_TEMPLATE.md"))
        self.assertTrue(okr.version.startswith("v1:"), okr.version)

    def test_okr_template_mission_principles_antigoals_versionlog(self):
        okr = P.parse_okr(read("okr/state/OKR_TEMPLATE.md"))
        self.assertTrue(okr.mission)
        self.assertEqual(len(okr.operating_principles), 5)
        self.assertEqual(len(okr.anti_goals), 4, "horizontal rules must not count as bullets")
        self.assertEqual(okr.version_log[0][0], "v1", "## Versioning log not read")

    def test_phase_template_yields_objectives_krs_and_scope_triggers(self):
        ph = P.parse_phase("001-demo", read("okr/state/phase_TEMPLATE.md"))
        self.assertEqual(len(ph.objectives), 2)
        self.assertEqual([kr.id for kr in ph.krs],
                         ["P-O1.1", "P-O1.2", "P-O1.3", "P-O2.1"])
        self.assertEqual(len(ph.scope_triggers), 2,
                         "## Phase Scope Reduction Rule not parsed")
        self.assertEqual({t.kind for t in ph.scope_triggers},
                         {"phase-day", "kr-progress"})

    def test_phase_template_placeholder_status_is_not_a_real_status(self):
        """The template ships `{{armed / disarmed / tripped}}`; reading that as
        a status would report every trigger as tripped."""
        ph = P.parse_phase("001-demo", read("okr/state/phase_TEMPLATE.md"))
        self.assertTrue(all(t.status == "armed" for t in ph.scope_triggers))

    def test_board_template_sections_parse(self):
        board = P.parse_board(read("pmo/state/BOARD_TEMPLATE.md"))
        # Empty template rows produce no tasks, but the sections must be found —
        # a renamed heading would silently zero the board.
        self.assertEqual(board.p0, [])
        self.assertEqual(board.user_input_queue, [])

    def test_linkage_template_placeholders_are_rejected(self):
        link = P.parse_linkage(read("okr/state/linkage_TEMPLATE.md"))
        self.assertFalse(link.ok, "unfilled template must not look populated")
        self.assertIn("placeholder", link.error)


class FixtureProject(unittest.TestCase):
    """A realistic filled-in project, parsed end to end."""

    @classmethod
    def setUpClass(cls):
        cls.snap = P.load_snapshot(FIXTURE)

    def test_board_counts(self):
        b = self.snap.board
        self.assertEqual(len(b.p0), 2)
        self.assertEqual(len(b.p1), 1)
        self.assertEqual([t.status for t in b.p0], ["in_progress", "blocked"])

    def test_phase_day_is_a_date_delta_not_a_trigger_count(self):
        ph = self.snap.phase
        self.assertIsNotNone(ph)
        self.assertEqual(ph.number, "002")
        self.assertEqual(ph.status, "active")
        self.assertIsNotNone(ph.day)
        self.assertNotEqual(ph.day, len(ph.scope_triggers),
                            "day must be computed from Started:, not from a list length")

    def test_phase_day_is_none_without_a_start_date(self):
        ph = P.parse_phase("003-x", "# Phase #003 — x\n\n> **Started**: TBD\n")
        self.assertIsNone(ph.day, "an unparseable start date must yield None, not 0")

    def test_scope_trigger_split(self):
        triggers = {t.kind: t for t in self.snap.phase.scope_triggers}
        kr = triggers["kr-progress"]
        self.assertIn("commit KRs are <50%", kr.condition)
        self.assertTrue(kr.response.startswith("scope cuts"))
        self.assertEqual(kr.when, "14")

    def test_linkage_graph(self):
        link = self.snap.linkage
        self.assertTrue(link.ok, link.error)
        self.assertEqual(link.phase, "002-release-pipeline")
        self.assertEqual([o.id for o in link.objectives], ["O1", "O2"])
        self.assertEqual(link.kr_for_task("REL-001"), "P-O1.1")
        self.assertEqual(link.unlinked, ["REL-009"])
        self.assertEqual({a.id for a in link.agents}, {"Coding Agent", "PMO Agent"})
        rows = {r.project_id: r for r in link.projects}
        self.assertEqual(set(rows), {"REL-001", "REL-002"})
        self.assertEqual(rows["REL-001"].serves_kr, "P-O1.1")
        self.assertIn("deploy-hardening", rows["REL-001"].aliases)

    def test_prose_target_yields_no_number(self):
        """A KR measured in prose ('flaky runs <= 1%') must carry no numeric
        target — a ceiling drawn as a progress bar misreports a risk limit."""
        krs = {k.id: k for o in self.snap.linkage.objectives for k in o.krs}
        self.assertEqual(krs["P-O1.1"].target, 3.0)
        self.assertIsNone(krs["P-O2.1"].target)
        self.assertEqual(krs["P-O2.1"].metric, "flaky runs <= 1%")

    def test_unlinked_survives_a_round_trip(self):
        """`unlinked` is declared, never inferred — so it has to come back out
        exactly as written, including when it is the only key present."""
        link = P.parse_linkage(
            "---\nlinkage: 1\nunlinked: [A-1, B-2]\n---\n")
        self.assertTrue(link.ok, link.error)
        self.assertEqual(link.unlinked, ["A-1", "B-2"])
        block = P.parse_linkage(
            "---\nlinkage: 1\nunlinked:\n  - A-1\n  - B-2\n---\n")
        self.assertEqual(block.unlinked, ["A-1", "B-2"])

    def test_a_prose_target_is_never_coerced(self):
        """The linter rejects it, but the reader must not invent one either."""
        link = P.parse_linkage(
            '---\nlinkage: 1\nobjectives:\n  - id: O1\n    title: t\n'
            '    krs:\n      - id: P-O1.1\n        title: t\n'
            '        metric: "max drawdown <= 15%"\n        target: "<= 15%"\n---\n')
        self.assertTrue(link.ok, link.error)
        kr = link.objectives[0].krs[0]
        self.assertIsNone(kr.target, "a prose target must stay absent, not become 15")
        self.assertEqual(kr.metric, "max drawdown <= 15%")

    def test_linkage_is_all_or_nothing(self):
        link = P.parse_linkage("---\nlinkage: 1\nobjectives:\n\t- id: O1\n---\n")
        self.assertFalse(link.ok)
        self.assertEqual(link.objectives, [], "a half-parsed graph must yield no data")

    def test_design_docs(self):
        by_id = {d.id: d for d in self.snap.design}
        self.assertEqual(by_id["DESIGN-001"].status, "locked")
        self.assertEqual(by_id["DESIGN-002"].status, "in_review")

    def test_top_risk_title_is_prose_not_a_label(self):
        self.assertTrue(self.snap.top_risks)
        title = self.snap.top_risks[0].title
        self.assertNotIn("TOP RISK", title)
        self.assertNotEqual(title.strip(), "4.2%")


class Attribution(unittest.TestCase):
    """reference/okr-linkage.md: resolve by stable ID / exact name / registered
    alias — never by fuzzy name. A near-match is not a match."""

    def setUp(self):
        self.snap = P.load_snapshot(FIXTURE)
        self.mod = load_bin_module("perry-state")

    def _task(self, tid, title=""):
        return P.Task(id=tid, title=title, owner="", status="not_started", next_action="")

    def test_declared_task_edge_resolves(self):
        """Resolution step 1: the graph names the edge outright."""
        self.assertEqual(
            self.mod.resolve_kr(self._task("REL-002"), self.snap.linkage), "P-O2.1")

    def test_exact_project_id_resolves(self):
        self.assertEqual(
            self.mod.resolve_kr(self._task("REL-001"), self.snap.linkage), "P-O1.1")

    def test_registered_alias_resolves(self):
        self.assertEqual(
            self.mod.resolve_kr(self._task("X-1", "deploy-hardening"), self.snap.linkage),
            "P-O1.1")

    def test_near_miss_name_does_not_resolve(self):
        """'Deploy script' is not 'Deploy script hardening'. Guessing here is
        the bug the linkage registry exists to prevent."""
        self.assertEqual(
            self.mod.resolve_kr(self._task("X-2", "Deploy script"), self.snap.linkage), "")

    def test_unknown_task_is_unlinked(self):
        self.assertEqual(
            self.mod.resolve_kr(self._task("REL-009", "Pipeline docs refresh"),
                                self.snap.linkage), "")


class StateExtractor(unittest.TestCase):
    """bin/perry-state is the standup's single read. Its payload is a contract."""

    @classmethod
    def setUpClass(cls):
        out = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(FIXTURE), "--json"],
            capture_output=True, text=True, check=True,
        )
        cls.payload = json.loads(out.stdout)

    def test_top_level_keys(self):
        for key in ("schema", "installed", "project", "okr", "phase", "board",
                    "attribution", "user_input_queue", "risks", "decisions",
                    "design", "architecture", "operations", "history", "warnings"):
            self.assertIn(key, self.payload)

    def test_counts_match_the_files(self):
        self.assertEqual(self.payload["board"]["p0"]["total"], 2)
        self.assertEqual(self.payload["board"]["blocked"], 1)
        self.assertEqual(self.payload["phase"]["kr_total"], 3)
        self.assertEqual(self.payload["user_input_queue"]["count"], 1)
        self.assertEqual(self.payload["design"]["locked"], 1)

    def test_unlinked_task_is_surfaced_not_guessed(self):
        att = self.payload["attribution"]
        self.assertEqual(att["linked"], 2)
        self.assertEqual([u["id"] for u in att["unlinked"]], ["REL-009"])

    def test_locked_design_without_impl_rows_is_flagged(self):
        self.assertEqual(
            [d["id"] for d in self.payload["design"]["pending_handoff"]], ["DESIGN-001"])

    def test_expired_sunset_is_reported(self):
        ids = [s["id"] for s in self.payload["decisions"]["expired_sunsets"]]
        self.assertIn("ADR-002", ids)

    def test_hook_high_stakes_gate_is_reported(self):
        """dispatch/autopilot's safety scan is armed only by this list, so its
        state must be visible in the payload rather than assumed."""
        hook = self.payload["project"]["hook"]
        self.assertTrue(hook["high_stakes_armed"])
        self.assertTrue(hook["high_stakes"])
        self.assertNotIn("high-stakes", " ".join(self.payload["warnings"]))

    def test_missing_hook_is_warned(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            shutil.copytree(FIXTURE, proj)
            (proj / ".perry" / "hook.md").unlink()
            out = subprocess.run(
                [sys.executable, str(PERRY_HOME / "bin" / "perry-state"),
                 "--root", str(proj), "--json"],
                capture_output=True, text=True, check=True,
            )
            payload = json.loads(out.stdout)
            self.assertFalse(payload["project"]["hook"]["high_stakes_armed"])
            self.assertIn("high-stakes", " ".join(payload["warnings"]))

    def test_no_state_project_reports_not_installed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            out = subprocess.run(
                [sys.executable, str(PERRY_HOME / "bin" / "perry-state"),
                 "--root", tmp, "--json"],
                capture_output=True, text=True, check=True,
            )
            self.assertFalse(json.loads(out.stdout)["installed"])


class ViewerTemplates(unittest.TestCase):
    """Templates read parser attributes by name, so a renamed field breaks them
    silently. Skipped when jinja2 isn't installed (the viewer is opt-in)."""

    def setUp(self):
        try:
            import jinja2  # noqa: F401
        except ImportError:
            self.skipTest("jinja2 not installed (viewer is opt-in)")

    def _env(self):
        import jinja2
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(PERRY_HOME / "viewer" / "templates")))
        # Filters that serve.py registers at runtime.
        for name in ("evidence_path", "strip_md", "md", "shortdate",
                     "first_line", "strip_leading_bold"):
            env.filters.setdefault(name, lambda v, *a, **k: v)
        return env

    def test_all_templates_compile(self):
        import jinja2
        env = self._env()
        for path in sorted((PERRY_HOME / "viewer" / "templates").glob("*.html")):
            with self.subTest(template=path.name):
                try:
                    env.get_template(path.name)
                except jinja2.TemplateSyntaxError as exc:
                    self.fail(f"{path.name}:{exc.lineno}: {exc}")

    def test_phase_track_renders_a_real_day_number(self):
        """Regression: the phase-track subtitle used to print the number of
        scope triggers as the phase day."""
        env = self._env()
        snap = P.load_snapshot(FIXTURE)
        out = env.from_string(
            "{% import '_macros.html' as m %}{{ m.phase_track(snap) }}"
        ).render(snap=snap)
        self.assertIn(f"day {snap.phase.day}", out)
        self.assertNotIn(f"day {len(snap.phase.scope_triggers)} ", out)


class Linter(unittest.TestCase):
    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-lint"), *args],
            capture_output=True, text=True,
        )

    def test_shipped_templates_match_the_schema(self):
        """The drift guard. If this fails, a template and the schema disagree —
        which is how the parsers silently stopped reading real files."""
        res = self._run("--templates")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_fixture_project_has_no_errors(self):
        res = self._run("--root", str(FIXTURE), "--json")
        report = json.loads(res.stdout)
        self.assertEqual(report["errors"], 0,
                         json.dumps(report["findings"], indent=2, ensure_ascii=False))

    def test_catches_a_bad_status_enum(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            shutil.copytree(FIXTURE, proj)
            board = proj / "BOARD.md"
            board.write_text(board.read_text().replace("| in_progress |", "| wip |"))
            res = self._run("--root", str(proj), "--json")
            rules = {f["rule"] for f in json.loads(res.stdout)["findings"]}
            self.assertIn("bad-enum", rules)

    def test_catches_duplicate_linkage_names(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            shutil.copytree(FIXTURE, proj)
            f = proj / "phase" / "002-linkage.md"
            f.write_text(f.read_text().replace(
                'name: "Flake detector"', 'name: "Deploy script hardening"'))
            res = self._run("--root", str(proj), "--json")
            rules = {f["rule"] for f in json.loads(res.stdout)["findings"]}
            self.assertIn("linkage-names-unique", rules)

    def test_catches_objective_kr_mismatch(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            shutil.copytree(FIXTURE, proj)
            f = proj / "phase" / "002-linkage.md"
            f.write_text(f.read_text().replace(
                "    serves: P-O2.1\n    objective: O2",
                "    serves: P-O2.1\n    objective: O1"))
            res = self._run("--root", str(proj), "--json")
            rules = {f["rule"] for f in json.loads(res.stdout)["findings"]}
            self.assertIn("linkage-objective-agrees", rules)

    def test_catches_a_task_under_two_krs(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            shutil.copytree(FIXTURE, proj)
            f = proj / "phase" / "002-linkage.md"
            f.write_text(f.read_text().replace("tasks: [REL-002]", "tasks: [REL-002, REL-001]"))
            res = self._run("--root", str(proj), "--json")
            rules = {f["rule"] for f in json.loads(res.stdout)["findings"]}
            self.assertIn("linkage-task-single-kr", rules)

    def test_catches_a_prose_target_coerced_into_a_number_field(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            shutil.copytree(FIXTURE, proj)
            f = proj / "phase" / "002-linkage.md"
            f.write_text(f.read_text().replace("target: 3", 'target: "<= 15%"'))
            res = self._run("--root", str(proj), "--json")
            rules = {f["rule"] for f in json.loads(res.stdout)["findings"]}
            self.assertIn("bad-type", rules)

    def test_catches_locked_design_with_no_plan(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            shutil.copytree(FIXTURE, proj)
            f = proj / "design" / "DESIGN-001-pipeline-topology.md"
            f.write_text(f.read_text().replace("## Implementation plan\n", ""))
            res = self._run("--root", str(proj), "--json")
            rules = {f["rule"] for f in json.loads(res.stdout)["findings"]}
            self.assertTrue({"missing-section", "locked-design-has-plan"} & rules)


if __name__ == "__main__":
    unittest.main()
