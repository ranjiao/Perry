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


class TestTheFloorIsMeasuredPerScript(Base):
    """`P.extracts` — the judgement call of TASK-201, pinned from both sides.

    The floor was a flat `len(frag) > 2`, which is a statement about ASCII
    wearing the clothes of a statement about length. It contradicted
    `_ESC_WORD`, which is written ASCII-only *on purpose* so that a CJK
    fragment reaches the matcher unguarded (ADR-007's fifth round) — a CJK
    fragment that never becomes a fragment never reaches anything. TASK-200
    measured 18 of 20 Chinese trading verbs discarded that way.

    Both halves are asserted because either alone is trivially satisfiable by
    breaking the other: drop the floor entirely and half two passes while
    `sh`, `go` and `*` start matching ordinary prose; keep it flat and half one
    fails on every two-character Chinese word there is.
    """

    def test_half_one_two_character_ascii_noise_still_does_not_extract(self):
        """`go` guarded at both edges still matches the English word "go".
        A gate that cries wolf on ordinary prose gets waved through — TASK-107
        is the whole reason this half of the floor is kept."""
        for noise in ("sh", "rm", "go", "db", "-f", "ci"):
            with self.subTest(fragment=noise):
                self.assertFalse(P.extracts(noise))
                self.assertEqual(P.escalation_fragments([f"- never `{noise}`"]),
                                 [])

    def test_half_two_a_two_character_cjk_word_extracts(self):
        """Two characters is the ordinary word in Chinese, not an abbreviation
        of one. A floor of three there is not a noise filter, it is a refusal
        to arm on an entire domain vocabulary."""
        for word in ("下单", "平仓", "建仓", "清仓"):
            with self.subTest(fragment=word):
                self.assertTrue(P.extracts(word))
                self.assertEqual(
                    P.escalation_fragments([f"- 任何 `{word}` 动作"]), [word])

    def test_one_character_is_never_enough_in_either_script(self):
        """ASCII: punctuation. CJK: a morpheme inside a large share of the
        compounds around it, with no boundary available to guard it — the same
        matches-everywhere shape reached from the other side."""
        for c in ("*", "/", "-", "买", "股"):
            with self.subTest(fragment=c):
                self.assertFalse(P.extracts(c))

    def test_the_ascii_half_is_unchanged(self):
        """Nothing that extracted before may stop extracting: that direction
        of the change would silently NARROW a live gate."""
        for frag in ("prod", "rm -rf", "origin", "design/", "~/.claude/skills",
                     "--force-with-lease", "$perry_home"):
            with self.subTest(fragment=frag):
                self.assertTrue(P.extracts(frag))

    def test_a_span_with_any_non_ascii_character_is_measured_as_non_ascii(self):
        self.assertTrue(P.extracts("a股"))
        self.assertTrue(P.extracts("下单"))

    def test_a_cjk_term_reaches_the_union_and_trips_the_scan(self):
        """End to end, because `extracts` returning True is not a gate. The
        fragment has to survive extraction, union and matching — the last of
        which is where `_ESC_WORD` deliberately leaves it unguarded."""
        root = self.project(hook="# Hook\n\n## High-stakes operations\n\n"
                                 "- 下单类操作 — `下单`、`平仓`\n")
        u = P.escalation_union(root)
        self.assertEqual(u["union"], ["下单", "平仓"])
        self.assertEqual(
            P.matching_escalations("本任务会在实盘 下单 一次", u["union"]),
            ["下单"])

    def test_every_extracted_fragment_can_still_match_itself(self):
        """A fragment that cannot match its own spelling is dead, and a dead
        fragment is invisible — the gate reports clean. Asserted across the
        floor's new admissions specifically."""
        for frag in ("下单", "平仓", "a股", "prod"):
            with self.subTest(fragment=frag):
                self.assertEqual(P.matching_escalations(frag, [frag]), [frag])


class TestALineThatYieldsNoFragmentIsReportedToo(Base):
    """Backticks are not the test; the extractor is. TASK-201.

    `escalate_unextractable` asked "does this line contain a backtick", which
    answers the right question only if every backticked span becomes a
    fragment. It does not — `P.extracts` has a floor — so a line whose only
    span is below it read as a rule, contributed nothing to the union and
    warned about nothing. That is DESIGN-006 § 7's failure class arriving
    through the hole its own fix left open, and it is the reason this is asked
    of the extractor now.

    `schema/roles-list-contract.md § must_escalate.unextractable` already said
    "bullets that yielded no fragment": the code, not the contract, was the
    deviation.
    """

    #: A line that HAS a backtick and yields nothing.
    SHORT = CARD.replace(f"- any outbound `{ROLE_TERM}` or `invoice`",
                         "- never shell out through `sh`")
    #: The same shape in Chinese — which now yields a fragment, so it must NOT
    #: be reported. Pins the fix against "warn about everything".
    CJK = CARD.replace(f"- any outbound `{ROLE_TERM}` or `invoice`",
                       "- 任何 `下单` 动作")

    def rules(self, root: Path) -> list[dict]:
        r = subprocess.run(
            [sys.executable, str(LINT), "--knowledge", "--root", str(root),
             "--json"], capture_output=True, text=True)
        return json.loads(r.stdout)["findings"]

    def test_the_warning_fires_on_a_backticked_span_below_the_floor(self):
        """**The warning, not the union.** The union being short is the
        symptom; the line being presented as a constraint it is not is the
        defect, and only the warning says so."""
        found = self.rules(self.project(cards={"finance.md": self.SHORT}))
        self.assertEqual([f["rule"] for f in found],
                         ["role-escalation-not-extractable"])
        self.assertIn("never shell out through `sh`", found[0]["message"])
        self.assertIn("enforces nothing", found[0]["message"])

    def test_the_payload_carries_it_too(self):
        """`must_escalate.unextractable` is frozen at `perry-roles/list/1.0`
        so a renderer can say the line is unenforced rather than presenting it
        as a constraint. A warning only the linter sees does not reach the
        delegation prompt."""
        card = P.parse_role_card("finance", self.SHORT)
        self.assertEqual(card.escalate_fragments, [])
        self.assertEqual(card.escalate_unextractable,
                         ["never shell out through `sh`"])

    def test_and_it_really_does_contribute_nothing(self):
        u = P.escalation_union(self.project(cards={"finance.md": self.SHORT}))
        self.assertEqual(u["roles"], {"finance": []})
        self.assertEqual(u["union"], u["project"])

    def test_a_line_that_does_yield_a_fragment_is_not_reported(self):
        """The other half. A fix that reported every line would satisfy the
        test above and destroy the signal — and `下单` is precisely the line
        that used to be dropped AND unreported."""
        root = self.project(cards={"finance.md": self.CJK})
        self.assertEqual(self.rules(root), [])
        self.assertEqual(P.escalation_union(root)["roles"], {"finance": ["下单"]})


if __name__ == "__main__":
    unittest.main()
