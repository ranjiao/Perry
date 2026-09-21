"""TASK-469: one startup contract, three routes, gates before state.

The route an agent takes is judged by the agent reading `SKILL.md`, never by a
classifier (NN-4), so nothing here grades intent. What is structural, and
checked, is the shape the judgement runs on:

* the router's route table precedes step −2, names exactly three routes, and
  gives the Explain route no step that reads config, state or the update check;
* the Query and Change routes both run step 2, and step 2 still reads the
  recovery gate before the interrupted-run gate, before the state read;
* each lane defers its steps −3 to −1 to the router instead of carrying its own
  copy, and names the recovery and interrupted-run gates before its state read;
* `reference/startup.md` holds the eight acceptance cases.

Run: python3 -m unittest tests.test_startup_routing
"""

from __future__ import annotations

COVERS = ("SKILL.md", "goals/SKILL.md", "work/SKILL.md", "decide/SKILL.md",
          "reference/startup.md", "reference/snapshot.md")

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANES = ("goals", "work", "decide")
POINTER = "SKILL.md § Mandatory first move"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def first_move(router: str) -> str:
    m = re.search(r"^## Mandatory first move.*?(?=^## )", router, re.M | re.S)
    if m is None:
        raise AssertionError("the router lost `## Mandatory first move`")
    return m.group(0)


def routes(section: str) -> dict[str, str]:
    """Route name → its `Run` cell, from the table above step −2."""
    return {name: run for name, (run, _) in route_cells(section).items()}


def route_cells(section: str) -> dict[str, tuple[str, str]]:
    """Route name → (`Run` cell, `Then` cell).

    **The `Then` cell is half the contract and was unparsed.** Acceptance
    criterion 1 — no dashboard, no update check, no mode load, no project-state
    read — is written entirely in `Then`, and the V4 round rewrote Explain's
    `Then` to "the pages that answer, plus `perry-task list --json` and the
    dashboard" with the suite staying green (mutation P3).
    """
    table = section[:section.index("−2. **Set `$PERRY_HOME`**")]
    out = {}
    for line in table.splitlines():
        m = re.match(r"\|\s*\*\*(\w+)\*\*[^|]*\|([^|]*)\|([^|]*)\|", line)
        if m:
            out[m.group(1)] = (m.group(2).strip(), m.group(3).strip())
    return out


def steps(cell: str) -> set[str]:
    """The router step numbers a `Run` cell names, ranges expanded."""
    order = ["−2", "−1", "0", "1", "2", "3"]
    got = set()
    for a, b in re.findall(r"(−?\d)\s+to\s+(−?\d)", cell):
        got |= set(order[order.index(a):order.index(b) + 1])
    got |= set(re.findall(r"−?\d", re.sub(r"(−?\d)\s+to\s+(−?\d)", "", cell)))
    return got


class TestTheRouterRoutesBeforeItReads(unittest.TestCase):

    def setUp(self):
        self.section = first_move(read("SKILL.md"))
        self.routes = routes(self.section)

    def test_exactly_three_routes_precede_step_minus_two(self):
        self.assertEqual(sorted(self.routes), ["Change", "Explain", "Query"],
                         "the spec's bound is exactly three routes")

    def test_explain_runs_no_state_config_or_update_step(self):
        self.assertEqual(steps(self.routes["Explain"]), {"−2"},
                         "an explanation ran a step that reads the project "
                         "or fetches: " + self.routes["Explain"])

    def test_every_state_route_runs_the_recovery_gates(self):
        for name in ("Query", "Change"):
            with self.subTest(route=name):
                self.assertIn("2", steps(self.routes[name]),
                              f"{name} reads state without step 2's gates")

    def test_query_skips_the_update_check_and_the_dashboard_read(self):
        got = steps(self.routes["Query"])
        self.assertNotIn("0", got)
        self.assertNotIn("3", got)

    def test_recovery_precedes_interrupted_precedes_state(self):
        s = self.section
        order = [s.index("--section recovery"), s.index("--section interrupted"),
                 s.index("**Compute the state — one call**")]
        self.assertEqual(order, sorted(order))

    def test_the_cases_page_is_named_and_holds_eight_cases(self):
        self.assertIn("reference/startup.md", self.section)
        page = read("reference/startup.md")
        m = re.search(r"^## The eight cases\n(.*)", page, re.M | re.S)
        self.assertIsNotNone(m, "reference/startup.md lost its case table")
        rows = [l for l in m.group(1).splitlines()
                if l.startswith("| ") and not l.startswith("| Case")]
        self.assertEqual(len(rows), 8, "the spec's bound is eight cases")


class TestTheLanesShareTheRouterStartup(unittest.TestCase):

    def test_each_lane_defers_its_startup_to_the_router(self):
        for lane in LANES:
            text = read(f"{lane}/SKILL.md")
            with self.subTest(lane=lane):
                ritual = text[text.index("## Mandatory first move"):]
                state = ritual.index("**Compute the state")
                head = ritual[:state]
                self.assertIn(POINTER, head)
                self.assertIn("recovery", head)
                self.assertIn("interrupted-run gates", head)
                for own in ("perry-detect-host", "perry-update-check"):
                    self.assertNotIn(own, head,
                                     f"{lane} carries its own copy of {own}; "
                                     f"a second startup path drifts")


class TestTheThenCellCarriesCriterionOne(unittest.TestCase):
    """AC1's content lives in the `Then` column. Nothing read it (V4 D5/P3)."""

    #: What criterion 1 excludes by name. Each must appear in the cell's
    #: NEGATIVE clause and nowhere else.
    EXCLUDED = ("update check", "config", "state", "modes", "dashboard",
                "write")

    def explain_then(self) -> str:
        return route_cells(first_move(read("SKILL.md")))["Explain"][1].lower()

    def test_the_cell_carries_a_negation_and_it_names_every_exclusion(self):
        """Polarity, not presence.

        The first version of this test asserted the words were ABSENT, and it
        went red on the correct cell — which reads "No update check, config,
        state, modes, dashboard or write". A substring test cannot tell "no
        dashboard" from "the dashboard", which is the same shape as the P3
        defect it was written to catch.
        """
        then = self.explain_then()
        self.assertIn("no ", then, "Explain's Then cell carries no negation")
        negation = then[then.index("no "):]
        for token in self.EXCLUDED:
            with self.subTest(excluded=token):
                self.assertIn(token, negation,
                              f"criterion 1 excludes {token!r} and the cell's "
                              f"negative clause does not name it")
                self.assertNotIn(
                    token, then[:then.index("no ")],
                    f"{token!r} is named before the negation, so the cell "
                    f"both loads and excludes it")

    def test_nothing_is_added_after_the_negation(self):
        """Mutation P3 appended `plus perry-task list --json and the
        dashboard` — an addition the negation does not cover."""
        then = self.explain_then()
        for added in ("plus ", "perry-task list", "perry-state", "perry-explain"):
            self.assertNotIn(added, then, f"Explain's Then cell names {added!r}")

    def test_explain_still_says_what_it_does_load(self):
        self.assertIn("pages that answer", self.explain_then())


class TestTheLaneOrderingWordIsGuarded(unittest.TestCase):
    """Mutation P6: flipping the lanes' `before` to `after` stayed green.

    `test_each_lane_defers_its_startup_to_the_router` slices at
    `**Compute the state` and asserts two literals appear in the head — which
    cannot tell "run the gates BEFORE the state read" from "AFTER". That one
    word carries the whole of criteria 2 and 3 inside the lanes.
    """

    def test_each_lane_runs_the_gates_before_it_reads_state(self):
        for lane in LANES:
            with self.subTest(lane=lane):
                text = read(f"{lane}/SKILL.md")
                ritual = text[text.index("## Mandatory first move"):]
                head = ritual[:ritual.index("**Compute the state")]
                window = head[head.index("interrupted-run gates"):][:120]
                # **The word immediately after the gates, not anywhere near
                # them.** Mutation S3 kept `before` in the window and read
                # "gates, run before nothing and after this lane reads state";
                # a `\bbefore\b` search anywhere in 120 characters cannot
                # tell that from the rule.
                self.assertRegex(
                    window, r"^interrupted-run gates\s+before\b",
                    f"{lane} does not say the gates run immediately BEFORE "
                    f"it reads state; window was {window[:70]!r}")
                self.assertNotIn(" after", window,
                                 f"{lane}'s ordering clause says 'after'")


class TestCriterionTwosOwnSentencesAreGuarded(unittest.TestCase):
    """Mutations P1, P2, P4 and P5 each inverted one of criterion 2's
    sentences in place with the suite staying green.

    P2 and P5 were this change's own fix and shipped with no guard at all.
    P1 and P4 are older sentences; guarding them costs one assertion each and
    they are the stop and the never-resume rule, which is what criterion 2 is.
    """

    def sentences(self):
        router = read("SKILL.md")
        return (
            ("the blocking stop", router,
             "stop before any further project-state read or mutation"),
            ("the case-6 clause", router,
             "not even a listing"),
            ("the step-2 ordering", router,
             "Nothing reads state before step 2"),
            ("never resume", router, "Never resume without asking"),
            # D2's write half. Removing this gate left the suite green on the
            # first attempt at the round-2 fixes: the rule was written and
            # nothing read it, which is the same shape as P1-P6.
            ("first-time setup is Change-only", router,
             "**Change route only**"),
        )

    #: Words that turn a rule into a suggestion without removing it. A
    #: presence assertion cannot see any of them.
    WEASEL = ("unless", "except when", "in which case", "is fine", "may be",
              "if you need", "afterwards is", "run before nothing")

    def test_each_sentence_is_present_and_not_inverted(self):
        for name, text, phrase in self.sentences():
            with self.subTest(sentence=name):
                self.assertIn(phrase, text, f"{name} is gone")

    def test_no_rule_is_softened_by_what_follows_it(self):
        """Presence is not meaning.

        Four mutations kept every guarded literal and flipped the rule anyway
        — an escape clause after the blocking stop, an exception after
        "Never resume without asking", a qualifier naming the wrong step.
        All four were green before this test existed. It is the same lesson
        TASK-474's mislabelled F5 mutant taught one row over: a mutation that
        kills on the wrong property proves nothing about the right one.
        """
        for name, text, phrase in self.sentences():
            with self.subTest(sentence=name):
                tail = text[text.index(phrase) + len(phrase):][:140].lower()
                for weasel in self.WEASEL:
                    self.assertNotIn(
                        weasel, tail,
                        f"{name} is followed by {weasel!r}, which takes it "
                        f"back without removing it")

    def test_the_step_one_qualifier_names_step_one_and_the_config_read(self):
        """Mutation S1 pointed the qualifier at step 3 and stayed green."""
        router = read("SKILL.md")
        i = router.index("Nothing reads state before step 2")
        clause = router[i:i + 160]
        self.assertIn("step 1", clause,
                      "the qualifier does not name step 1, the step it is about")
        self.assertIn("config read", clause)
        for wrong in ("step 3", "step 0", "dashboard"):
            self.assertNotIn(wrong, clause, f"the qualifier names {wrong!r}")

    def test_first_time_setup_is_gated_where_step_one_prompts_for_it(self):
        """The gate must sit ON step 1, not merely somewhere in the file.

        First-time setup writes the config store. A Query that started it
        would turn a question into a mutation, ahead of the recovery gate.
        """
        router = read("SKILL.md")
        step1 = router[router.index("1. **Read `.perry/config.jsonl`**"):][:600]
        self.assertIn("first-time setup", step1)
        self.assertIn("**Change route only**", step1,
                      "step 1 prompts for a write with no route gate on it")

    def test_the_blocking_stop_is_not_turned_into_a_continue(self):
        router = read("SKILL.md")
        window = router[router.index("`blocking: true`"):][:600]
        for inverted in ("continue to the state read", "listing the state root",
                         "Resume the run"):
            self.assertNotIn(inverted, window)


class TestTheHelpRouteIsNotSentToReadState(unittest.TestCase):
    """V4 D1. `work/SKILL.md`'s pack preamble sent the Explain route into a
    procedure whose step 1 runs `perry-config show` and `perry-state`.

    The remedy was first written into `reference/startup.md`, which the help
    route never opens — so this asserts it is in the lane file that drives the
    behaviour, which is the whole of D1.
    """

    #: The entry files that carry the route rule for the pack procedure. NOT
    #: every file that names the procedure: the fourth architecture re-review
    #: (D4) found about ten more pages naming it, `reference/router-
    #: subcommands.md § /perry help` among them, and `decide/SKILL.md` here
    #: carries the rule without naming the procedure.
    PACK_SITES = ("SKILL.md", "goals/SKILL.md", "work/SKILL.md",
                  "decide/SKILL.md", "reference/config.md")

    #: The exact instruction each site must carry, keyed by file. Pinning the
    #: SITE, not a window around the first heading: mutations A4 and A5 both
    #: survived a +/-1400-character window, because `reference/config.md`'s
    #: two instructions are 70 lines apart and only one fell inside it.
    ROUTE_RULES = {
        "work/SKILL.md": ("**Pack eligibility:**", "never on the explain route"),
        "goals/SKILL.md": ("Pack capabilities and controls`", "never on the explain route"),
        "reference/config.md": ("`/perry help` points here",
                                "not for step 1"),
    }

    def flat(self, text: str) -> str:
        return " ".join(text.split()).lower()

    def test_every_site_states_the_route_rule_at_the_instruction(self):
        """POSITIVE: each site must SAY the rule, where the rule is given.

        Round 2's guard was a blacklist of softening words and its reviewer
        walked around it with a hedge the list did not have. A blacklist of
        English cannot be completed; an assertion that a named instruction
        carries a named clause can be.
        """
        for rel, (anchor, clause) in self.ROUTE_RULES.items():
            with self.subTest(file=rel):
                text = read(rel)
                self.assertIn(anchor, text, f"{rel} lost its instruction")
                i = text.index(anchor)
                para = self.flat(text[i:text.index("\n\n", i)])
                self.assertIn(clause, para,
                              f"{rel}'s instruction does not scope itself by "
                              f"route; it reads {para[:110]!r}")

    def test_no_site_anywhere_tells_help_to_hide_a_pack_command(self):
        """Whole file, not a window. Hiding is a decision about which pack is
        active, and that decision needs a read help is not allowed to make."""
        for rel in self.PACK_SITES:
            with self.subTest(file=rel):
                flat = self.flat(read(rel))
                for verb in ("help hides", "hides inactive pack",
                             "help filters", "filtered from its executable"):
                    self.assertNotIn(
                        verb, flat,
                        f"{rel} tells an Explain request to {verb!r}")
                self.assertNotIn("also points here", flat,
                                 f"{rel} sends /perry help at the procedure "
                                 f"without saying which part it may run")

    def test_no_lane_sends_help_row_rendering_through_the_pack_procedure(self):
        """The defect itself: no lane may make help rows need that read.

        `goals` points at the same procedure for the DISCOVERY operation —
        "what else can Perry do?" — which is a Query and legitimately reads.
        Only the help-row clause is the defect, so only it is asserted away.
        """
        for lane in LANES:
            with self.subTest(lane=lane):
                text = read(f"{lane}/SKILL.md")
                self.assertNotIn(
                    "rendering its help rows", text,
                    f"{lane} applies the pack procedure to help rows; its "
                    f"step 1 reads perry-config and perry-state, and help is "
                    f"the one route with no recovery gate")

    def test_the_lane_that_has_pack_help_rows_says_to_mark_not_filter(self):
        text = read("work/SKILL.md")
        i = text.index("**Pack eligibility:**")
        # **The instruction paragraph alone, not a fixed-size window.** The
        # first version read 2,000 characters and went red on this file's own
        # account of what round 2 got wrong, which QUOTES the old wording. A
        # guard that cannot tell an instruction from a description of a
        # retired instruction reports the history as the defect.
        # **Whitespace-normalised.** Markdown wraps, so a phrase can fall
        # across a newline; a guard keyed to where the wrap lands is the
        # allowlist TASK-431 broke by adding a comment above the line it named.
        flat = lambda t: " ".join(t.split()).lower()  # noqa: E731
        rule = flat(text[i:text.index("\n\n", i)])
        body = flat(text[i:][:2000])
        self.assertNotIn(
            "before loading software-ops references", rule,
            "the half round 2 left: help <subcommand> reads the matching "
            "reference file, and for five subcommands that file is a "
            "packs/software-ops page")
        self.assertIn("never on the explain route", rule,
                      "the eligibility rule does not scope itself by route")
        self.assertIn("mark", body,
                      "the remedy is not in the file that drives the "
                      "behaviour; startup.md is not read by the help route")
        self.assertIn("never filter", body)


if __name__ == "__main__":
    unittest.main()
