"""`enums.decision_status` — one binding for a decision's status, and a word
for a proposal.

**The defect.** Every other status in Perry — `task_status`, `design_status`,
`linkage_status`, `phase_status`, `candidate_status`, `finding_status`,
`prescription_status` — is declared in `schema/state-schema.json § enums` and
read from there. A decision's status was declared nowhere and spelled out in
three independent places: a `STATUSES` tuple in `bin/perry-decide`, a prose list
in `schema/decide-list-contract.md`, and another in
`decide/reference/decisions.md`. Three spellings of one list is how a value
lands in two of them, and that is a divergence rather than a typo — the writer
and the document describing the writer disagree, and only one of them refuses.

**The word.** `proposed` means *drafted, awaiting the user*: written down, not
adopted, governing nothing. Before it existed a draft ADR had to be filed as
`active`, so a proposal was indistinguishable from a decision in force.

`prescription_status` in the same schema already spends `proposed` on a
diagnose prescription awaiting the user's accept/decline, and reusing the word
is the point rather than a collision: it is the same sense — an agent-authored
artifact that a human has not yet adopted — and this schema already reuses a
value across enums whenever the sense is the same (`superseded` in
`design_status` and here, `dropped` in four enums, `active` in three). The
alternative, `draft`, would have been the real collision: `design_status.draft`
means *still being written*, which is not what this is. `test_the_word_is_pinned`
below is here so that reading stays a decision and not an accident.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from gate import GATE_OFF   # tests/gate.py — why this fixture opts out

PERRY_HOME = Path(os.environ.get("PERRY_HOME") or Path(__file__).resolve().parent.parent)
TOOL = PERRY_HOME / "bin" / "perry-decide"
SCHEMA = PERRY_HOME / "schema" / "state-schema.json"
CONTRACT = PERRY_HOME / "schema" / "decide-list-contract.md"
REFERENCE = PERRY_HOME / "decide" / "reference" / "decisions.md"
TEMPLATE = PERRY_HOME / "decide" / "state" / "DECISIONS_TEMPLATE.md"


def enum() -> list[str]:
    return json.loads(SCHEMA.read_text())["enums"]["decision_status"]


class Project:
    """A throwaway project, `perry-decide`'s own fixture shape."""

    def __init__(self, home: Path | None = None):
        self.home = home or PERRY_HOME
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n" + GATE_OFF)

    def run(self, *argv):
        env = dict(os.environ, PERRY_HOME=str(self.home))
        r = subprocess.run(
            ["python3", str(self.home / "bin" / "perry-decide"), *argv,
             "--root", str(self.root), "--json"],
            capture_output=True, text=True, env=env)
        try:
            return r.returncode, json.loads(r.stdout or "{}")
        except json.JSONDecodeError:
            return r.returncode, r.stdout + r.stderr

    def index(self) -> str:
        p = self.root / "DECISIONS.md"
        return p.read_text() if p.exists() else ""

    def file(self, adr: str, status: str) -> None:
        """Hand-write an ADR with an arbitrary status — the reader's input."""
        (self.root / "decisions").mkdir(exist_ok=True)
        (self.root / "decisions" / f"{adr}-hand.md").write_text(
            f"# {adr} — Hand written\n\n"
            f"> Status: {status}\n> Type: Process\n> Date: 2026-08-20\n")

    def ready(self):
        self.run("bootstrap")
        return self

    def __del__(self):
        self.dir.cleanup()


def perry_home_with(values: list[str]) -> tempfile.TemporaryDirectory:
    """A `$PERRY_HOME` identical to the real one but for `decision_status`.

    A symlink farm, not a copy: every top-level entry is linked back to the
    install, and only `schema/state-schema.json` is a real, patched file. That
    keeps the fixture honest — the tool under test is the shipped tool, loading
    the shipped `viewer/parsers.py` and `bin/`, reading one edited enum.
    """
    tmp = tempfile.TemporaryDirectory()
    farm = Path(tmp.name)
    for entry in PERRY_HOME.iterdir():
        if entry.name == "schema":
            continue
        (farm / entry.name).symlink_to(entry)
    (farm / "schema").mkdir()
    for entry in (PERRY_HOME / "schema").iterdir():
        if entry.name != "state-schema.json":
            (farm / "schema" / entry.name).symlink_to(entry)
    schema = json.loads(SCHEMA.read_text())
    schema["enums"]["decision_status"] = values
    (farm / "schema" / "state-schema.json").write_text(json.dumps(schema, indent=2))
    return tmp


class TestOneBinding(unittest.TestCase):
    """V2-1. The values `bin/perry-decide` accepts come from the schema."""

    def test_the_enum_exists_and_is_the_shape_every_sibling_has(self):
        enums = json.loads(SCHEMA.read_text())["enums"]
        self.assertIn("decision_status", enums,
                      "a decision's status is the one status Perry never "
                      "declared — that absence is the bug")
        self.assertIsInstance(enums["decision_status"], list)
        self.assertTrue(all(isinstance(v, str) and v == v.lower()
                            for v in enums["decision_status"]))

    def test_no_hardcoded_status_tuple_is_left_in_the_tool(self):
        """The `STATUSES` tuple, and any successor spelled the same way."""
        src = TOOL.read_text()
        self.assertNotIn("STATUSES = (", src)
        values = set(enum())
        offenders = []
        for n, line in enumerate(src.split("\n"), 1):
            literals = set(re.findall(r"""["']([a-z_]+)["']""", line))
            if len(literals & values) >= 2:
                offenders.append(f"{n}: {line.strip()}")
        self.assertEqual(
            offenders, [],
            "two or more status values written out together is a second copy "
            "of the enum, which is the defect this task removed:\n    "
            + "\n    ".join(offenders))

    def test_a_value_added_to_the_schema_is_accepted_with_no_code_edit(self):
        """The load-bearing claim. `trialled` exists in no source file."""
        self.assertNotIn("trialled", TOOL.read_text())
        with perry_home_with(enum() + ["trialled"]) as home:
            p = Project(Path(home)).ready()
            p.run("new", "--title", "X", "--type", "Process")
            code, out = p.run("status", "ADR-001", "--status", "trialled")
            self.assertEqual(code, 0, out)
            code, listed = p.run("list", "--status", "trialled")
            self.assertEqual([a["id"] for a in listed["decisions"]], ["ADR-001"])
            self.assertEqual(listed["conformance"]["off_enum_status"], [],
                             "a value the schema declares is not off-enum")
            self.assertIn("Trialled: 1", p.index())

    def test_a_value_the_schema_does_not_declare_is_still_refused(self):
        p = Project().ready()
        p.run("new", "--title", "X", "--type", "Process")
        code, out = p.run("status", "ADR-001", "--status", "trialled")
        self.assertEqual(code, 1)
        self.assertIn("trialled", str(out))

    def test_the_tool_refuses_rather_than_falling_back_to_its_own_copy(self):
        """A schema with the enum removed must stop the writer, not be
        papered over with a default — the default is what this task deleted."""
        with perry_home_with([]) as home:
            p = Project(Path(home))
            code, out = p.run("bootstrap")
            self.assertEqual(code, 1)
            self.assertIn("decision_status", str(out))


class TestTheWordForAProposal(unittest.TestCase):
    """V2-2. `proposed` round-trips like any other value."""

    def test_the_word_is_pinned(self):
        """Deliberate, not incidental: see this module's docstring for why
        `proposed` and not `draft`. Changing it is a decision, and this
        assertion is where that decision gets made again."""
        self.assertIn("proposed", enum())
        self.assertNotIn("draft", enum(),
                         "`draft` is `design_status`'s word for *still being "
                         "written*, which is not *written and awaiting the user*")

    def test_it_is_written_listed_counted_and_filtered(self):
        p = Project().ready()
        p.run("new", "--title", "One", "--type", "Process")
        p.run("new", "--title", "Two", "--type", "Risk")
        code, _ = p.run("status", "ADR-001", "--status", "proposed")
        self.assertEqual(code, 0)

        _, all_of_them = p.run("list")
        by_id = {a["id"]: a for a in all_of_them["decisions"]}
        self.assertEqual(by_id["ADR-001"]["status"], "proposed")
        self.assertEqual(all_of_them["total"], 2)
        self.assertEqual(all_of_them["active"], 1,
                         "a proposal is not a decision in force")
        self.assertEqual(all_of_them["conformance"]["off_enum_status"], [])

        _, filtered = p.run("list", "--status", "proposed")
        self.assertEqual([a["id"] for a in filtered["decisions"]], ["ADR-001"])

    def test_the_index_counts_it_and_files_it_under_neither_active_nor_historical(self):
        p = Project().ready()
        p.run("new", "--title", "One", "--type", "Process")
        p.run("status", "ADR-001", "--status", "proposed")
        idx = p.index()
        self.assertIn("Proposed: 1", idx)
        head, _, rest = idx.partition("## Proposed")
        self.assertTrue(rest, "no Proposed section in the rendered index")
        self.assertNotIn("ADR-001", head, "a proposal was rendered as Active")
        self.assertNotIn("ADR-001", rest.split("## Superseded")[1],
                         "a proposal was filed under `(historical)`")

    def test_a_project_with_no_proposal_renders_no_proposed_section(self):
        """Available, not mandatory: an existing index does not grow a section
        because the value now exists."""
        p = Project().ready()
        p.run("new", "--title", "One", "--type", "Process")
        self.assertNotIn("## Proposed", p.index())

    def test_the_user_adopts_it_by_flipping_it_back(self):
        p = Project().ready()
        p.run("new", "--title", "One", "--type", "Process")
        p.run("status", "ADR-001", "--status", "proposed")
        code, _ = p.run("status", "ADR-001", "--status", "active")
        self.assertEqual(code, 0)
        _, out = p.run("list")
        self.assertEqual(out["active"], 1)
        self.assertNotIn("## Proposed", p.index())


class TestReadingStaysTolerant(unittest.TestCase):
    """V2-3. Writing is strict; reading is not."""

    def test_an_off_enum_status_is_read_and_reported_not_refused(self):
        p = Project().ready()
        p.file("ADR-001", "ratified")
        code, out = p.run("list")
        self.assertEqual(code, 0, out)
        self.assertEqual([a["id"] for a in out["decisions"]], ["ADR-001"])
        self.assertEqual(out["decisions"][0]["status"], "ratified",
                         "the value is reported as the file spells it")
        self.assertEqual(out["conformance"]["off_enum_status"],
                         [{"id": "ADR-001", "status": "ratified"}])
        self.assertEqual(out["total"], 1)

    def test_the_list_payload_keys_did_not_change(self):
        """V2-5. Adding a possible value to a documented field is not a break."""
        p = Project().ready()
        p.run("new", "--title", "One", "--type", "Process")
        p.run("status", "ADR-001", "--status", "proposed")
        _, out = p.run("list")
        self.assertEqual(
            set(out), {"contract", "semantics", "project_root", "state_root",
                       "conformance", "decisions", "active", "total",
                       "expired_sunsets"})
        self.assertEqual(out["contract"], "perry-decide/list/1.1")
        self.assertEqual(
            set(out["conformance"]),
            {"index_present", "indexed_without_file", "filed_without_index_row",
             "off_enum_status", "missing_type"})


class TestTheThreeSpellingsAgree(unittest.TestCase):
    """V2-4. Mechanically, so the next divergence fails instead of drifting.

    The prose is allowed to *describe* the enum; it is not allowed to disagree
    with it. Each check below reads the schema and then reads one place that
    lists the values, and asserts the two sets are equal.
    """

    def test_the_contract_status_filter_lists_exactly_the_enum(self):
        line = next(l for l in CONTRACT.read_text().split("\n")
                    if l.startswith("`--status "))
        spelled = line.split("`")[1].removeprefix("--status ").split("|")
        self.assertEqual(spelled, enum(), f"{CONTRACT.name}: {line}")

    def test_the_contract_status_field_lists_exactly_the_enum(self):
        row = next(l for l in CONTRACT.read_text().split("\n")
                   if l.startswith("| `status` |"))
        # Split on unescaped pipes — the cell spells the values `a` \| `b`,
        # and a naive split would stop at the first escaped one.
        cell = re.split(r"(?<!\\)\|", row)[3]
        spelled = re.findall(r"`([a-z_]+)`", cell)
        self.assertEqual(spelled, enum(), f"{CONTRACT.name}: {row}")

    def test_the_reference_status_model_lists_exactly_the_enum(self):
        body = REFERENCE.read_text().split("## Status model")[1].split("\n## ")[0]
        spelled = re.findall(r"(?m)^- \*\*([a-z_]+)\*\*", body)
        self.assertEqual(spelled, enum(),
                         f"{REFERENCE.name} § Status model")

    def test_the_reference_names_the_right_number_of_them(self):
        body = REFERENCE.read_text().split("## Status model")[1].split("\n## ")[0]
        words = {3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven",
                 8: "Eight", 9: "Nine"}
        self.assertIn(f"{words[len(enum())]} values:", body,
                      "the count in the prose is one more copy of the list, "
                      "and it drifted the same way the list did")

    def test_every_rendered_count_line_lists_exactly_the_enum(self):
        """The `> Active: 0 · Superseded: 0 · …` header — a fourth and fifth
        copy of the list, in the shipped template and in the reference's
        example index. `render_index` builds it from the enum; these two are
        pictures of what it builds."""
        for path in (TEMPLATE, REFERENCE):
            line = next(l for l in path.read_text().split("\n")
                        if re.match(r"^> [A-Z][a-z]+: [0-9<]", l))
            spelled = [f.split(":")[0].strip().lower()
                       for f in line[2:].split("·")]
            self.assertEqual(spelled, enum(), f"{path.name}: {line}")

    def test_the_tools_help_does_not_respell_the_list(self):
        """`--help` prints the module docstring, which used to carry a sixth
        copy on the `status` usage line."""
        r = subprocess.run(["python3", str(TOOL), "--help"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        for a, b in zip(enum(), enum()[1:]):
            self.assertNotIn(f"{a}|{b}", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
