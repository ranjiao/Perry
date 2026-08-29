"""Contract tests for Perry's localization layer.

The claim under test is narrow and load-bearing: **a project written in the
project's document language must lint clean and produce the same payload
shape as the English one.** If that ever stops being true, a Chinese user's
dashboard silently prints `—` where a number should be, and nothing fails
loudly enough to notice.

The two fixtures are deliberately the same project said twice —
`sample-project` in English, `sample-project-zh` in Chinese — so any assertion
below can be read as "these two must agree".

Adding a language? Copy this file, point it at your fixture, and add the
glossary entries per `reference/i18n.md § Adding a language`.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
EN = PERRY_HOME / "tests" / "fixtures" / "sample-project"
ZH = PERRY_HOME / "tests" / "fixtures" / "sample-project-zh"
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())

sys.path.insert(0, str(PERRY_HOME / "viewer"))

import parsers as P  # noqa: E402


def state(fixture: Path) -> dict:
    """`bin/perry-state --json` against a fixture project."""
    out = subprocess.run(
        [sys.executable, str(PERRY_HOME / "bin" / "perry-state"), "--json"],
        capture_output=True, text=True, cwd=str(fixture),
        env={"PERRY_PROJECT": str(fixture), "PATH": "/usr/bin:/bin"},
    )
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def lint(fixture: Path) -> list[dict]:
    out = subprocess.run(
        [sys.executable, str(PERRY_HOME / "bin" / "perry-lint"),
         "--root", str(fixture), "--json"],
        capture_output=True, text=True,
    )
    return json.loads(out.stdout)["findings"]


class GlossaryShape(unittest.TestCase):
    """The glossary is the single naming authority. Every reader loads it from
    the schema, so its shape is itself a contract."""

    def test_schema_declares_an_i18n_block(self):
        self.assertIn("i18n", SCHEMA)
        for key in ("languages", "invariant", "headings", "fields", "columns"):
            self.assertIn(key, SCHEMA["i18n"], f"i18n.{key} missing")

    def test_every_glossary_entry_lists_a_declared_language(self):
        langs = set(SCHEMA["i18n"]["languages"]) - {"en"}
        for kind in ("headings", "fields", "columns"):
            for name, per_lang in SCHEMA["i18n"][kind].items():
                self.assertTrue(per_lang, f"{kind}.{name} has no translations")
                unknown = set(per_lang) - langs
                self.assertFalse(
                    unknown,
                    f"{kind}.{name} translates into {unknown}, which is not in "
                    "i18n.languages — add the language there first",
                )

    def test_every_schema_column_is_in_the_glossary_or_is_invariant(self):
        """A column absent from the glossary can only ever be written in
        English. That is a legitimate choice (`KR`) but it has to be a choice,
        not an omission — so the exemptions are named here.

        `ADR` was the other one and TASK-235 removed it: the only schema table
        with an `ADR` column was `files[id=decisions]`, which declared the
        shape of `DECISIONS.md`, and that file is deleted (DESIGN-013 § 5.3).
        An exemption for a column no table declares is one nobody can be wrong
        about, so it goes rather than sitting here looking like coverage."""
        invariant_columns = {"KR"}
        known = set(SCHEMA["i18n"]["columns"])
        for spec in SCHEMA["files"]:
            for table in spec.get("tables", []):
                for col in table["columns"]:
                    self.assertTrue(
                        col in known or col in invariant_columns,
                        f"{spec['id']}: column {col!r} is neither in "
                        "i18n.columns nor declared invariant in this test",
                    )

    def test_localizable_headings_widened_their_match_regex(self):
        """A glossary entry nobody matches on is decoration. Every schema
        heading whose canonical name has translations must accept them."""
        gloss = SCHEMA["i18n"]["headings"]
        for spec in SCHEMA["files"]:
            for head in spec.get("headings", []):
                # `### Objective <N> — <title>` -> form `Objective <N>`,
                # canonical `Objective`. The form is what a real heading looks
                # like, so it is what the regex has to be probed with.
                form = head["label"].lstrip("# ").split(" —")[0].split("  (")[0].strip()
                canonical = re.sub(r"<[^>]*>", "", form).strip()
                entry = gloss.get(canonical)
                if not entry:
                    continue
                matcher = re.compile(head["match"])
                for spellings in entry.values():
                    for s in spellings:
                        probe = form.replace(canonical, s).replace("<N>", "1").strip()
                        self.assertTrue(
                            matcher.search(probe),
                            f"{spec['id']}: `{head['label']}` accepts "
                            f"{canonical!r} but not its declared form {probe!r} — "
                            "widen the `match` regex "
                            "(reference/i18n.md § Adding a language)",
                        )


class TranslatedDocsAreStillDocs(unittest.TestCase):
    """A translated README explains; it does not track.

    `bin/perry-explain` only counts an undefined ID as dangling when a
    *tracking* document relies on it — docs are full of illustrative IDs. That
    exemption used to match the exact filename, so adding `README_cn.md` made
    every example ID in it report as dangling against Perry's own repo."""

    def setUp(self):
        import importlib.util
        from importlib.machinery import SourceFileLoader
        loader = SourceFileLoader(
            "perry_explain", str(PERRY_HOME / "bin" / "perry-explain"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        self.explain = importlib.util.module_from_spec(spec)
        loader.exec_module(self.explain)

    def test_localized_variants_of_a_doc_are_illustrative(self):
        for rel in ("README_cn.md", "README.zh.md", "README-fr.md",
                    "INSTALL_cn.md", "docs/CONTRIBUTING.ja.md", "SKILL.md"):
            self.assertTrue(self.explain.is_illustrative(rel), rel)

    def test_real_tracking_files_are_not_swept_up(self):
        for rel in ("BOARD.md", "OKR.md", "decisions/ADR-001-x.md",
                    "phase/002-release-pipeline.md", "evidence/2026-08/REL-001.md"):
            self.assertFalse(self.explain.is_illustrative(rel), rel)


class ChineseProjectIsFirstClass(unittest.TestCase):
    """The zh fixture is the English fixture said in Chinese. Every number the
    standup prints has to survive the translation."""

    @classmethod
    def setUpClass(cls):
        cls.zh = state(ZH)
        cls.en = state(EN)

    def test_it_lints_without_errors(self):
        errors = [f for f in lint(ZH) if f["severity"] == "error"]
        self.assertEqual(errors, [], f"Chinese project does not lint clean: {errors}")

    def test_config_reports_the_document_language(self):
        cfg = self.zh["project"]["config"]
        self.assertTrue(cfg["present"])
        self.assertEqual(cfg["language"], "中文")

    def test_chat_language_is_carried_separately_from_document_language(self):
        """The whole point of two fields: files in one language, replies in
        another. A reader that collapses them makes that impossible."""
        self.assertEqual(self.zh["project"]["config"]["chat_language"], "follow user")

    def test_okr_mission_and_objectives_parse(self):
        okr = self.zh["okr"]
        self.assertTrue(okr["present"])
        self.assertEqual(okr["version"], self.en["okr"]["version"])
        self.assertTrue(okr["mission"], "## 使命 did not resolve to a mission")
        self.assertEqual(len(okr["objectives"]), len(self.en["okr"]["objectives"]))

    def test_kr_ids_stay_english_while_kr_text_is_chinese(self):
        """The layer split, asserted directly: ids are machine tokens, text is
        prose. Attribution resolves on the ids."""
        krs = [kr for o in self.zh["okr"]["objectives"] for kr in o["krs"]]
        self.assertEqual([k["id"] for k in krs],
                         ["KR-O1.1", "KR-O1.2", "KR-O1.3", "KR-O2.1"])
        for kr in krs:
            self.assertTrue(kr["text"], f"{kr['id']} has no text")
            self.assertRegex(kr["text"], r"[一-鿿]",
                             f"{kr['id']} text should be Chinese prose")

    def test_phase_sections_resolve_through_the_glossary(self):
        ph = self.zh["phase"]
        self.assertEqual(ph["number"], "001")
        self.assertEqual(ph["started"], "2026-08-01", "`启动：` header field")
        self.assertEqual(ph["status"], "active", "status VALUES stay English")
        self.assertTrue(ph["focus_present"], "## 阶段焦点 did not resolve")
        self.assertTrue(ph["cost_ceiling"], "## 成本上限 did not resolve")
        self.assertEqual(ph["kr_total"], self.en["phase"]["kr_total"])

    def test_scope_reduction_triggers_are_found(self):
        """`## 阶段缩圈规则` is the section that decides whether a phase cuts
        scope. Failing to find it doesn't error — it silently disarms."""
        self.assertEqual(len(P.parse_phase(
            "001-release-pipeline",
            (ZH / "phase" / "001-release-pipeline.md").read_text(),
        ).scope_triggers), 2)

    def test_board_counts_match_the_english_fixture(self):
        for key in ("p0", "p1", "p2"):
            self.assertEqual(self.zh["board"][key]["total"],
                             self.en["board"][key]["total"], key)
        self.assertEqual(self.zh["board"]["blocked"], self.en["board"]["blocked"])

    def test_board_statuses_stay_in_the_english_enum(self):
        """Status is an enum value, not prose — a Chinese board still reads
        `blocked`, with any qualifier localized: `blocked (等 USER-014)`.
        Cadence rows are excluded: their fourth column is Frequency."""
        allowed = set(SCHEMA["enums"]["task_status"])
        checked = 0
        for task in self.zh["board"]["tasks"]:
            if task["priority"] == "Cadence":
                continue
            self.assertIn(task["status"], allowed)
            checked += 1
        self.assertEqual(checked, 3)

    def test_localized_column_headers_are_not_read_as_a_task_row(self):
        """`| 编号 | 标题 | …` is a header, not a task called 编号."""
        ids = [t["id"] for t in self.zh["board"]["tasks"]]
        self.assertNotIn("编号", ids)
        self.assertIn("REL-001", ids)

    def test_user_input_queue_resolves(self):
        uiq = self.zh["user_input_queue"]
        self.assertEqual(uiq["count"], 1)
        self.assertEqual(uiq["oldest"]["id"], "USER-014")
        self.assertEqual(uiq["oldest"]["blocks"], "REL-002")

    def test_top_risk_resolves(self):
        self.assertEqual(self.zh["risks"]["count"], 1)
        self.assertTrue(self.zh["risks"]["top"]["title"])

    def test_decisions_resolve_from_adr_files_written_in_chinese(self):
        """**This asserted a localized heading and now asserts a localized
        FILE, and the difference is a real loss worth naming.**

        Until TASK-235 the zh fixture's decisions came from a `DECISIONS.md`
        whose heading was `## 进行中`, so this was the one place the heading
        glossary was exercised end-to-end on the decisions payload. That file
        is deleted (DESIGN-013 § 5.3) and the fixture now carries real
        `decisions/ADR-*.md` files — which it never had, so every field in that
        index was orphan data.

        What is asserted instead is the ADR reader's own i18n contract, stated
        in `decide/reference/decisions.md § Language`: the narrative and the
        title are in the project's language, and the `Status:` / `Type:` /
        `Date:` **field names and values stay English** because every
        downstream reader matches on them. A Chinese title must round-trip and
        an English field name must still be found in a file that is otherwise
        Chinese.
        """
        dec = self.zh["decisions"]
        self.assertEqual(dec["count"], 2)
        self.assertEqual(dec["last"]["id"], "ADR-002")
        self.assertEqual(dec["last"]["date"], "2026-07-10")
        self.assertEqual(dec["last"]["title"], "只做单区域",
                         "a Chinese ADR title did not survive the reader")
        self.assertEqual(self.en["decisions"]["count"], dec["count"],
                         "the zh fixture is the en fixture said in Chinese")

    def test_the_hook_safety_gate_arms_under_a_localized_heading(self):
        """`## 高风险操作` must arm the dispatch safety scan. The linter and
        `bin/perry-state` reach this section by different paths, and a gate one
        of them reports as unarmed while the other reads as armed is worse than
        either answer on its own."""
        self.assertTrue(self.zh["project"]["hook"]["high_stakes_armed"])
        self.assertEqual(
            [f for f in lint(ZH) if f["rule"] == "hook-high-stakes-armed"], [])

    def test_the_dashboard_renders_without_holes(self):
        """The user-visible end of the chain. A `—` here is the failure mode
        the whole glossary exists to prevent."""
        out = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-state"), "--dashboard"],
            capture_output=True, text=True, cwd=str(ZH),
            env={"PERRY_PROJECT": str(ZH), "PATH": "/usr/bin:/bin"},
        ).stdout
        for must in ("#001 release-pipeline", "P0=2", "USER-014",
                     "只做单区域", "2026-07-10"):
            self.assertIn(must, out, f"dashboard is missing {must!r}:\n{out}")


class InvariantsHoldInTheFixture(unittest.TestCase):
    """The fixture is also documentation: it must model the layer rules, not
    just pass the parsers."""

    def test_file_names_and_slugs_are_ascii(self):
        for path in ZH.rglob("*"):
            if path.is_dir() or ".perry" in path.parts:
                continue
            rel = path.relative_to(ZH).as_posix()
            self.assertTrue(rel.isascii(),
                            f"{rel}: file names and slugs stay ASCII "
                            "(reference/i18n.md § The invariant layer)")

    def test_config_field_names_stay_english(self):
        text = (ZH / ".perry" / "config.md").read_text()
        for name in ("Document language", "Chat language", "Repo layout"):
            self.assertIn(name + ":", text)

    def test_priority_sections_stay_english(self):
        board = (ZH / "BOARD.md").read_text()
        for p in ("## P0", "## P1", "## P2"):
            self.assertIn(p, board)


class TestChatProseRule(unittest.TestCase):
    """The rule added after Perry wrote a session's worth of Chinese that a
    fifteen-year industry veteran could not read.

    Every other i18n rule was being followed correctly at the time: files were
    in the document language, IDs and paths stayed English, nothing was
    half-translated. The gap was that no rule governed *prose in a reply*, so
    English sentences were written with dictionary substitutions.

    These are pointer checks, not style checks. Prose cannot be linted; a
    router rule naming a section that does not exist is exactly the defect this
    repo keeps finding, and that can be.
    """

    SECTION = "## Writing chat prose in a language that is not English"

    def test_the_section_exists(self):
        doc = (PERRY_HOME / "reference" / "i18n.md").read_text()
        self.assertIn(self.SECTION, doc)

    def test_the_router_points_at_it_and_the_pointer_resolves(self):
        router = (PERRY_HOME / "SKILL.md").read_text()
        named = "reference/i18n.md § Writing chat prose in a language that is not English"
        self.assertIn(named, router,
                      "the style rule does not name the section that owns it")
        doc = (PERRY_HOME / "reference" / "i18n.md").read_text()
        self.assertIn(named.split(" § ")[1], doc,
                      "the router names a section i18n.md does not have")

    def test_the_rule_survives_in_the_router_itself(self):
        """A rule that lives only in a tier-1 reference is a rule an agent
        reads after it has already answered. The one-line form has to be where
        the style rules are."""
        router = (PERRY_HOME / "SKILL.md").read_text()
        for fragment in ("stays English", "idiom", "one language end to end"):
            self.assertIn(fragment, router, f"the router lost {fragment!r}")


if __name__ == "__main__":
    unittest.main()
