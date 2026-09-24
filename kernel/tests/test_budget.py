"""The concept budget (Goal 6; acceptance criterion 7) and `describe`.

The literals below are this test's own. It does not read
`kernel/ARCHITECTURE.md`: the suite passes with every `*.md` removed (Goal 2).
Raising a number means editing these literals and that document, and
DESIGN-023 § 7 makes that a revision of the design.
"""

from __future__ import annotations

import copy
import json
import unittest

from support import Sandbox, mkdtemp

from perry_kernel import surface
from perry_kernel.errors import ERRORS

MAX_CONCEPTS = 8
MAX_COMMAND_GROUPS = 12
CONCEPTS = ["template", "item", "field", "transition", "guard", "relation",
            "event", "attachment"]
GUARD_KINDS = ["required", "actor", "relations_closed", "limit"]
FIELD_KINDS = ["text", "int", "number", "date", "enum", "actor", "ref",
               "list", "metric"]


def budget_problems(described: dict) -> list[str]:
    problems = []
    if described["concepts"] != CONCEPTS:
        problems.append(f"concepts are {described['concepts']}")
    if len(described["concepts"]) > MAX_CONCEPTS:
        problems.append(f"{len(described['concepts'])} concepts, above "
                        f"{MAX_CONCEPTS}")
    groups = {c["name"].split()[0] for c in described["commands"]}
    if len(groups) > MAX_COMMAND_GROUPS:
        problems.append(f"{len(groups)} command groups, above "
                        f"{MAX_COMMAND_GROUPS}: {sorted(groups)}")
    if described["budget"] != {"concepts": MAX_CONCEPTS,
                               "command_groups": MAX_COMMAND_GROUPS}:
        problems.append(f"budget is {described['budget']}")
    fmt = described["template_format"]
    if fmt["guard_kinds"] != GUARD_KINDS:
        problems.append(f"guard kinds are {fmt['guard_kinds']}")
    if fmt["field_kinds"] != FIELD_KINDS:
        problems.append(f"field kinds are {fmt['field_kinds']}")
    return problems


def described_via_cli(sb: Sandbox, **kw) -> dict:
    r = sb.run("describe", store=False, root=False, **kw)
    assert r.ok, r
    return r.result


class TestTheBudget(unittest.TestCase):

    def test_the_kernel_is_within_its_budget(self):
        described = described_via_cli(Sandbox(self))
        self.assertEqual(budget_problems(described), [])
        groups = sorted({c["name"].split()[0] for c in described["commands"]})
        self.assertEqual(groups, ["attach", "describe", "events", "export",
                                  "import", "init", "item", "query", "rel",
                                  "template"])

    def test_a_ninth_concept_fails(self):
        described = described_via_cli(Sandbox(self))
        ninth = copy.deepcopy(described)
        ninth["concepts"].append("workflow")
        self.assertTrue(budget_problems(ninth))

    def test_a_thirteenth_command_group_fails_and_a_twelfth_does_not(self):
        described = described_via_cli(Sandbox(self))
        twelve = copy.deepcopy(described)
        for name in ("alpha go", "beta go"):
            twelve["commands"].append({"name": name})
        self.assertEqual(budget_problems(twelve), [])
        thirteen = copy.deepcopy(twelve)
        thirteen["commands"].append({"name": "gamma go"})
        self.assertTrue(budget_problems(thirteen))

    def test_a_fifth_guard_kind_or_a_tenth_field_kind_fails(self):
        described = described_via_cli(Sandbox(self))
        for key, extra in (("guard_kinds", "script"), ("field_kinds", "blob")):
            grown = copy.deepcopy(described)
            grown["template_format"][key].append(extra)
            self.assertTrue(budget_problems(grown))


class TestDescribe(unittest.TestCase):

    def test_byte_identical_in_every_project_and_through_the_executable(self):
        a, b = Sandbox(self), Sandbox(self)
        b.ready()
        outs = {
            a.run("describe", store=False, root=False).out,
            b.run("describe", flags=["--json"]).out,
            a.run("describe", store=False, root=False,
                  cwd=mkdtemp(self)).out,
            a.cli("describe", store=False, root=False).out,
        }
        self.assertEqual(len(outs), 1)

    def test_every_command_declares_its_shape(self):
        described = described_via_cli(Sandbox(self))
        self.assertEqual(list(described), [
            "surface", "concepts", "budget", "commands", "flags", "env",
            "exit_codes", "errors", "template_format"])
        self.assertEqual(described["surface"], "1.0")
        for command in described["commands"]:
            with self.subTest(command=command["name"]):
                self.assertEqual(sorted(command), [
                    "errors", "flags", "input", "kind", "name", "result",
                    "summary"])
                self.assertIn(command["kind"], ("read", "write"))
                self.assertTrue(set(command["errors"]) <= set(ERRORS))
                self.assertIn("usage", command["errors"])
                self.assertEqual("--dry-run" in command["flags"],
                                 command["kind"] == "write")
                self.assertEqual("--input" in command["flags"],
                                 command["input"] is not None)
                for key, spec in (command["input"] or {}).items():
                    self.assertIn("required", spec, key)
                    self.assertIn("type", spec, key)
        self.assertEqual(set(described["errors"]), set(ERRORS))
        self.assertEqual(described["exit_codes"],
                         {"0": "success", "1": "refused",
                          "2": "bad invocation",
                          "3": "internal fault (rolled back)"})
        self.assertEqual(sorted(described["env"]), [
            "PERRY_KERNEL_TESTING", "PERRY_PROJECT", "PERRY_STORE"])

    def test_the_declaration_drives_the_parser(self):
        """A key `describe` does not declare is refused; one it declares is
        accepted. The two come from one table."""
        sb = Sandbox(self).ready()
        for command in surface.COMMANDS:
            if command["input"] is None:
                continue
            with self.subTest(command=command["name"]):
                r = sb.run(*command["name"].split(),
                           data={"undeclared_key": 1})
                self.assertEqual(r.code_name, "unknown_key", r)
                self.assertEqual(r.details["keys"][0]["legal"],
                                 list(command["input"]))

    def test_describe_is_valid_json_with_no_store_seq(self):
        r = Sandbox(self).run("describe", store=False, root=False)
        self.assertIsNone(json.loads(r.out)["store_seq"])


if __name__ == "__main__":
    unittest.main()
