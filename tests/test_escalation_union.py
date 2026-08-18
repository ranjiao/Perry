"""The escalation union only ever grows.

DESIGN-006 § 5.2 and goal 6, phase D. A role's `## Must escalate` list is
**added to** the project's high-stakes list from `.perry/hook.md`; it is never
substituted for it.

Get that backwards and hiring a role quietly NARROWS what the project refuses
to do unsupervised — the opposite of what a role is for. It is also invisible:
a narrowed scan still passes everything it is asked, cheerfully, and the only
symptom is a dispatch that should have refused and did not.

So the guard here is deliberately written three ways, because a single one of
them is defeatable by a plausible "optimization":

1. **Structural** — `project` and `roles` are reported as separate halves, so a
   replacement is visible in the shape and not merely in a smaller number.
2. **Provenance** — `origins` says which side each fragment came from. Fold the
   two lists into one lookup and the `hook` origin disappears.
3. **Behavioural** — a project-only term must still TRIP THE SCAN while a role
   is declared, and a role-only term must trip it too. This is the one that
   survives a rewrite that keeps the dict keys and breaks the meaning.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
LINT = PERRY_HOME / "bin" / "perry-lint"
STATE = PERRY_HOME / "bin" / "perry-state"
sys.path.insert(0, str(PERRY_HOME / "viewer"))
import parsers as P  # noqa: E402

#: Two terms that share no substring with anything in the other list, so a
#: match can only have come from the side it was written on.
HOOK_TERM = "rm -rf"
ROLE_TERM = "wire-transfer"

HOOK = f"""# Hook

## High-stakes operations

- Destructive filesystem operations — `{HOOK_TERM}`, `rm -f`
"""

CARD = f"""# Role · finance

- Accepted by: user
- Default rung: V5
- Executors: any

## Context

Prepares the monthly close.

## Loads

- knowledge: reporting

## May touch

- write: reports/

## Must escalate

- any outbound `{ROLE_TERM}` or `invoice`
"""


class Base(unittest.TestCase):
    def project(self, hook: str | None = HOOK,
                cards: dict[str, str] | None = None) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n", encoding="utf-8")
        if hook is not None:
            (root / ".perry" / "hook.md").write_text(hook, encoding="utf-8")
        for name, text in (cards or {}).items():
            p = root / ".perry" / "roles" / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        return root


class TestTheUnionGrows(Base):
    """The safety property, stated three ways."""

    def test_a_role_adds_its_terms_to_the_scan(self):
        u = P.escalation_union(self.project(cards={"finance.md": CARD}))
        self.assertIn(ROLE_TERM, u["union"])
        self.assertIn("invoice", u["union"])

    def test_declaring_a_role_removes_nothing_from_the_project_list(self):
        """THE test. Every fragment the project declared for itself is still
        in the scan after a role is hired — including terms the role's own list
        says nothing about."""
        before = P.escalation_union(self.project())
        after = P.escalation_union(self.project(cards={"finance.md": CARD}))
        self.assertEqual(before["project"], after["project"],
                         "hiring a role changed the project's own list")
        self.assertTrue(set(before["union"]) <= set(after["union"]),
                        "the union shrank when a role was declared")
        self.assertIn(HOOK_TERM, after["union"])

    def test_the_two_halves_stay_separately_reported(self):
        """Structural guard. A caller that only ever sees one merged list
        cannot tell an addition from a substitution, so the halves are part of
        the contract."""
        u = P.escalation_union(self.project(cards={"finance.md": CARD}))
        self.assertEqual(u["project"], [HOOK_TERM, "rm -f"])
        self.assertEqual(u["roles"], {"finance": [ROLE_TERM, "invoice"]})
        self.assertNotIn(ROLE_TERM, u["project"])
        self.assertNotIn(HOOK_TERM, u["roles"]["finance"])

    def test_each_fragment_says_which_side_it_came_from(self):
        """Provenance guard. Fold the two lists into one lookup and the `hook`
        origin stops existing — which is the shape of the mistake."""
        u = P.escalation_union(self.project(cards={"finance.md": CARD}))
        self.assertEqual(u["origins"][HOOK_TERM], ["hook"])
        self.assertEqual(u["origins"][ROLE_TERM], ["role:finance"])
        self.assertEqual({o for os_ in u["origins"].values() for o in os_},
                         {"hook", "role:finance"})

    def test_a_term_in_both_lists_records_both_origins_and_appears_once(self):
        both = CARD.replace(f"`{ROLE_TERM}` or `invoice`", f"`{HOOK_TERM}`")
        u = P.escalation_union(self.project(cards={"finance.md": both}))
        self.assertEqual(u["union"].count(HOOK_TERM), 1)
        self.assertEqual(u["origins"][HOOK_TERM], ["hook", "role:finance"])

    def test_two_roles_both_contribute(self):
        second = CARD.replace(f"`{ROLE_TERM}` or `invoice`", "`payroll`")
        u = P.escalation_union(self.project(
            cards={"finance.md": CARD, "legal.md": second}))
        for frag in (HOOK_TERM, ROLE_TERM, "payroll"):
            self.assertIn(frag, u["union"], frag)


class TestTheScanActuallyTrips(Base):
    """Behavioural guard — the one that survives a rewrite which keeps the
    dict keys and breaks the meaning. A list is not a gate; matching is."""

    def scan(self, text: str, root: Path) -> list[str]:
        return P.matching_escalations(
            text, P.escalation_union(root)["union"])

    def test_a_role_added_term_trips_the_scan(self):
        root = self.project(cards={"finance.md": CARD})
        self.assertEqual(
            self.scan(f"Deliverable: send the {ROLE_TERM} to the vendor", root),
            [ROLE_TERM])

    def test_a_project_term_still_trips_the_scan_while_a_role_is_declared(self):
        """The replacement mutation dies here. If the union became the role's
        list INSTEAD OF the project's, this spec would sail through a
        pre-flight that used to refuse it, and nothing else would say so."""
        spec = f"Files in scope: a script that runs `{HOOK_TERM} build/`"
        with_role = self.project(cards={"finance.md": CARD})
        without = self.project()
        self.assertEqual(self.scan(spec, without), [HOOK_TERM])
        self.assertEqual(self.scan(spec, with_role), [HOOK_TERM],
                         "declaring a role stopped the project's own term "
                         "from tripping the pre-flight scan")

    def test_one_spec_touching_both_sides_matches_both(self):
        root = self.project(cards={"finance.md": CARD})
        got = self.scan(f"{HOOK_TERM} then {ROLE_TERM}", root)
        self.assertEqual(sorted(got), sorted([HOOK_TERM, ROLE_TERM]))


class TestTheUnionReachesTheTools(Base):
    """Two consumers read it, and neither carries its own copy."""

    def state(self, root: Path) -> dict:
        r = subprocess.run(
            [sys.executable, str(STATE), "--root", str(root),
             "--section", "project"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)["project"]

    def test_perry_state_publishes_the_union_beside_the_untouched_hook_list(self):
        proj = self.state(self.project(cards={"finance.md": CARD}))
        self.assertIn(ROLE_TERM, proj["escalation"]["union"])
        self.assertIn(HOOK_TERM, proj["escalation"]["union"])
        # `hook.high_stakes` is what the PROJECT declared and stays that.
        self.assertTrue(all(ROLE_TERM not in b
                            for b in proj["hook"]["high_stakes"]))

    def test_a_role_added_term_forces_v5_in_the_consequence_check(self):
        """The union feeding a real enforcement point, not just a payload.

        `perry-lint --verification` reads the same union: a task whose title
        matches a term ONLY the role declared now needs a human sign-off,
        exactly as if the project had written the term in its own hook."""
        root = self.project(cards={"finance.md": CARD})
        (root / "BOARD.md").write_text(
            "# Board — T\n\n## P0 (must finish this period)\n\n"
            "| ID | Title | Owner | Status | Next action | Evidence | Verification |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| T-1 | Send the {ROLE_TERM} | agent | done | — | `make x` ok | V3 |\n",
            encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(LINT), "--verification", "--root", str(root),
             "--json"], capture_output=True, text=True)
        found = json.loads(r.stdout)["findings"]
        self.assertIn("consequence-needs-signoff", [f["rule"] for f in found])
        self.assertTrue(any(ROLE_TERM in f["message"] for f in found), found)

    def test_the_linter_does_not_carry_its_own_extraction(self):
        """One rule, one implementation. `squash` is in this repo because the
        same idea spelled twice read a header two different ways; an escalation
        list is a worse place to rediscover that."""
        src = LINT.read_text(encoding="utf-8")
        self.assertNotIn(r'findall(r"`([^`]+)`"', src,
                         "perry-lint re-implements the backtick extraction")
        self.assertIn("P.escalation_union", src)


class TestAProseLineEnforcesNothing(Base):
    """An escalation line with zero backticks reads as a rule and contributes
    nothing to the scan — the `hook_TEMPLATE.md` backtick bug, in the file that
    inherited its extraction rule (DESIGN-006 § 7)."""

    PROSE = CARD.replace(f"- any outbound `{ROLE_TERM}` or `invoice`",
                         "- anything that moves money out of the company")

    def rules(self, root: Path) -> list[dict]:
        r = subprocess.run(
            [sys.executable, str(LINT), "--knowledge", "--root", str(root),
             "--json"], capture_output=True, text=True)
        return json.loads(r.stdout)["findings"]

    def test_an_unbackticked_escalation_line_is_warned_about(self):
        found = self.rules(self.project(cards={"finance.md": self.PROSE}))
        self.assertEqual([f["rule"] for f in found],
                         ["role-escalation-not-extractable"])
        self.assertIn("enforces nothing", found[0]["message"])

    def test_and_it_really_does_contribute_nothing(self):
        """The warning is only worth having because the claim behind it is
        true. Asserted rather than assumed."""
        u = P.escalation_union(self.project(cards={"finance.md": self.PROSE}))
        self.assertEqual(u["roles"], {"finance": []})
        self.assertEqual(u["union"], u["project"])

    def test_a_line_with_one_backtick_among_prose_is_accepted(self):
        """The rule is "extracts something", not "is entirely backticked".
        A check that demanded the latter would fire on every well-written
        card in the shipped pack."""
        found = self.rules(self.project(cards={"finance.md": CARD}))
        self.assertEqual(found, [])

    def test_the_shipped_role_cards_all_extract(self):
        rdir = PERRY_HOME / "packs" / "software-ops" / "roles"
        cards = {p.name: p.read_text(encoding="utf-8") for p in rdir.glob("*.md")}
        self.assertEqual(self.rules(self.project(cards=cards)), [])
        u = P.escalation_union(self.project(cards=cards))
        for name, frags in u["roles"].items():
            self.assertTrue(frags, f"{name} declares no extractable escalation")


if __name__ == "__main__":
    unittest.main()
