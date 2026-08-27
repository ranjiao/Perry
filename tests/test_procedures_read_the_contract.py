"""The neighbour rule to `test_procedures_call_the_tool`: a procedure must not
re-state a predicate the contract computes.

That module enforces the write side of ADR-007 — *call the tool for the fields,
then generate the prose*. This one is its mirror on the read side: **when the
payload already answers a question, the procedure asks the payload; it does not
work the answer out again from the cells the payload consumed.**

## The measurement

`work/reference/autopilot.md:131`, as it stood on 2026-08-27:

> **Eligible**: status ∈ {`not_started`, `blocked` with all blockers resolved},
> has `evidence/<YYYY-MM>/<TASK-ID>-spec.md` with `Dispatch mode: auto` +
> non-`manual` Executor, hook safety scan passes, all listed dependencies
> resolved.

That first clause is a second implementation of `tasks[].startable`, and it had
already outlived **three** contract versions that changed what it means:

- **1.12** stopped `startable` reading the stored `status`, so a row whose every
  dependency has closed is `startable: true` with `blocked_stale: true` — the
  case this prose calls *"`blocked` with all blockers resolved"*, computed a
  second time and by hand.
- **1.14** made a `USER-` ask a node, so a row waiting on a question is
  correctly unstartable. **This prose does not know asks exist**, so an agent
  following it would dispatch a row whose open question is the whole blocker.
- **1.15** added `depends_on_resolved`, so *why* an edge resolved is readable
  per edge rather than deduced from set arithmetic.

Not one of those three landed in this sentence. A rule stated twice is fixed
once; `tests/one_startable_rule.py` says so about `bin/` and fails on a second
statement of the same rule **in code**, counted by enclosing function. This copy
is in *prose*, where an AST scan cannot see it, and prose is what the agent
actually executes.

## The line: explaining a field vs. re-stating a predicate

A guard so broad it forbids a procedure from *explaining* a field is worse than
no guard, because it makes the pages that teach the payload unwritable. So the
line is drawn on **whose answer the sentence is about**, and there are two
tiers, because the two failure modes are not the same shape.

**Tier 1 — the procedure names its own verdict.** *"Eligible"*, *"ready to
dispatch"*, *"actionable"*, *"dispatchable"*: a word the contract does not
serve, standing for an answer the contract does serve. The moment such a word
is defined out of **raw board cells** — a `Status` enum value, a claim that
*all* the blockers are resolved — the procedure owns a copy of the rule, and it
will drift, because nothing that changes `resolve_startability` will ever come
back to edit this sentence. No connective saves it: a copy introduced by
*"because"* is still a copy. To go green the sentence cites the field instead —
*"**Eligible**: `startable` is `true`"* — which is delegation, and delegation is
the whole point.

**Tier 2 — the sentence is about the contract's own field.** `startable`,
`blocked_stale`: here the payload is plainly the authority and the page is
teaching a reader how to read it, which every reference page must be free to
do. So a raw cell may appear beside the field. What may not appear is a
**definitional link** between them — `:`, `∈`, *when*, *if*, *unless*,
*requires*, *means*, a defining parenthetical. That is the difference between

    `startable` is `false` because a dependency is open      ← a reason
    `startable` is `true` when every blocker has closed      ← a rule

Both mention the field and a cell. The first tells you why one row reads the way
it does and leaves the payload as the only thing that can decide; the second
hands you a procedure for computing the field yourself, which is precisely the
second implementation, wearing the field's own name as cover.

**Naming the field does not license a re-statement sitting beside it.** This is
`test_procedures_call_the_tool`'s R2 lesson, and the shape both of its live
instances had: the tool named, the hand path licensed one clause later. A
sentence that says *"read `startable`"* and then spells the predicate out is
reported, because the spelled-out half is what a reader in a hurry will follow.

## What is exempt, and why each exemption is a category

1. **A reason, not a rule** (tier 2). A raw cell joined to the field by
   *because* / *since* / *which means* explains a value the payload produced.
   Suppressed as `reason`.
2. **No definitional link** (tier 2). The field and a cell appear in one
   sentence with nothing defining one from the other — *"a row whose cell still
   reads `blocked` can be `startable` anyway"*. Suppressed as
   `no-definitional-link`. This is the exemption that makes the page able to
   explain `blocked_stale` at all, and `test_an_explanation_of_a_field_stays_
   green` is what keeps it honest.
3. **Fenced code is not prose.** Inherited: `blocks()` drops fences whole, and
   the commands in these pages are the tool invocations this guard is asking
   for. A JSON key list inside a fence is the payload, not a re-statement of it.

There is deliberately **no** exemption for tables or block quotes here. The
neighbour has one because a file inventory is not a procedure step; a predicate
written down in a table is still a predicate written down twice, and nothing in
the live corpus needs the escape.

## Why the corpus is imported and not re-derived

`procedure_pages()` comes from `test_procedures_call_the_tool`, which derives it
from the repository's shape — root `SKILL.md`, root `reference/**`, every lane's
`SKILL.md` plus `reference/**`, `packs/*/*.md` — precisely because four guards
here have been beaten by a file a hardcoded list did not name. Copying that walk
into this module would commit, about the corpus, the exact error this module
reports about predicates. One home, two readers.

## What is declared, and what closes the list

`PREDICATES` holds the rule, not the corpus. An entry may be added when a
predicate is **served as a field by a read contract** — that is the closure, and
it can only grow when someone writes a new field. `test_declared_fields_are_
served_by_the_contract` checks every declared field against
`schema/task-list-contract.md` at run time, so an entry naming a field that was
renamed is a red rather than a rule that silently stopped firing; and
`test_the_declared_home_exists` pins the function `bin/` states it in.

**One entry today, and that is a measurement rather than a shortcut.**
Startability is the only contract predicate a procedure page was found to have
copied — the sweep behind this module reported 2 sentences across 45 pages, both
in `autopilot.md`, both fixed by TASK-174. `TARGETS` in the neighbour started
smaller than it is and grew the day a writer existed to grow it (TASK-119); this
one grows the day a second predicate is found copied.

Run: python3 tests/parallel test_procedures_read_the_contract
"""

from __future__ import annotations

import re
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from test_procedures_call_the_tool import (
    PERRY_HOME, blocks, procedure_pages, sentences, steps,
)


# ---------------------------------------------------------------- the rule

#: A word for the answer that the contract does **not** serve — the procedure's
#: own name for a verdict the payload already carries. Defining one of these out
#: of raw cells is tier 1 and is reported however it is phrased.
OWN_VERDICT = (
    r"\bin-?eligib\w*|\beligib\w*"
    r"|\bdispatchable\b|\bundispatchable\b|\bactionable\b"
    r"|\bready to (?:dispatch|start|go|be dispatched|be picked up)\b"
    r"|\bsafe to dispatch\b")

#: The contract's own field, named. A sentence about one of these is a sentence
#: about the payload's answer, so it is tier 2: allowed to mention a raw cell,
#: not allowed to define the field out of one.
FIELD_VERDICT = r"\bun-?startable\b|\bstartable\b|\bblocked_stale\b"

#: The stored `Status` enum. On its own each of these is just a word these pages
#: use constantly ("move the row to `review`"), which is why it only counts as a
#: raw input inside a *condition* — see `STATUS_CONDITION`.
#:
#: **Bounded on both sides, and that is not cosmetic.** Unbounded, `blocked`
#: matches inside `blocked_stale` and `blocked_by` — the two field names a page
#: uses when it is doing the right thing — so the sentence explaining
#: `blocked_stale` would carry its own raw-cell match and the guard would report
#: the explanation it exists to protect. An underscore is a word character, so
#: `\b` is exactly the boundary that tells the cell from the field.
STATUS = r"\b(?:not_started|in_progress|blocked|review|done|dropped)\b"

#: A claim about the row's stored status: the word `status` beside an enum
#: value, or a row/cell *being* one. This is the cell `startable` reads, said
#: again.
STATUS_CONDITION = (
    r"\bstatus\b[^.;!?]{0,45}?" + STATUS
    + r"|" + STATUS + r"[^.;!?]{0,25}?\bstatus\b"
    + r"|\b(?:row|task|it|one|cell)\b[^.;!?]{0,24}?"
      r"\b(?:is|are|says|reads|shows|stays|sits at)\b\s*[`'\"*]*" + STATUS)

#: A **quantified** claim about the dependency graph — *all* blockers resolved,
#: *every* dependency closed, *no* open dependency. The quantifier is required:
#: "a dependency is open" is a remark about one edge, and the contract's answer
#: is about the whole set. It is the quantified form that re-implements
#: `blocked_by`, and it is the quantified form that went wrong at 1.14, when
#: "all blockers resolved" silently stopped covering an unanswered `USER-` ask.
DEPENDENCY_CLOSURE = (
    r"\b(?:all|every|each|no|none of|any)\b[^.;!?]{0,45}?"
    r"\b(?:blocker|blockers|dependency|dependencies|deps)\b"
    r"[^.;!?]{0,45}?"
    r"\b(?:resolved|closed|clear|cleared|done|satisfied|terminal|open|remain\w*)\b"
    r"|\b(?:blocker|blockers|dependency|dependencies)\b[^.;!?]{0,30}?"
    r"\b(?:all|every|none)\b[^.;!?]{0,30}?"
    r"\b(?:resolved|closed|satisfied|terminal)\b")

#: What a definition looks like in these pages. `:` after a bolded label, `∈`
#: over a set, a `when` / `if` clause, a defining parenthetical. This is what
#: turns a mention of a cell into an instruction for computing the field.
DEFINITIONAL = re.compile(
    r":|∈|\bwhen\b|\bif\b|\bunless\b|\bonly if\b|\brequires?\b|\bmust\b"
    r"|\bwith\b|\(|\bmeans?\b|→", re.I)

#: Exemption 1 — the cell is offered as the reason a row reads the way it does,
#: not as the rule for deciding every row.
REASON = re.compile(
    r"\bbecause\b|\bsince\b|\bwhich means\b|\bthat means\b|\bis why\b"
    r"|\bafter all\b|\bthe reason\b", re.I)

#: One rule: a predicate the read contract serves as a field, the place `bin/`
#: states it once, and how prose re-states it. See the docstring on what closes
#: this list.
PREDICATES = {
    "startability": dict(
        # The fields this predicate is served as. Checked against the contract.
        fields=("startable", "blocked_stale"),
        # Where `bin/` states it, exactly once, under `tests/one_startable_rule`.
        home=("bin/lib/__init__.py", "resolve_startability"),
        contract="schema/task-list-contract.md",
        own_verdict=OWN_VERDICT,
        field_verdict=FIELD_VERDICT,
        inputs="(?:" + STATUS_CONDITION + "|" + DEPENDENCY_CLOSURE + ")",
    ),
}


@dataclass(frozen=True)
class Finding:
    """One sentence that computes a contract predicate a second time."""

    page: Path
    line: int
    predicate: str
    tier: str
    sentence: str

    def render(self) -> str:
        where = self.page
        try:
            where = self.page.relative_to(PERRY_HOME)
        except ValueError:                                   # pragma: no cover
            pass
        return (f"  {where}:{self.line}  [{self.tier}] {self.predicate}\n"
                f"      {self.sentence[:200]}")


@dataclass(frozen=True)
class Suppression:
    """One sentence the guard deliberately stopped evaluating."""

    page: Path
    line: int
    predicate: str
    exemption: str
    sentence: str


def _spans(sentence: str, first: str, second: str):
    """Every (gap) between a match of `first` and a match of `second`.

    Order-free: the field may precede the cell or follow it, and the text
    between them is what carries the connective either way.
    """
    for a in re.finditer(first, sentence, re.I):
        for b in re.finditer(second, sentence, re.I):
            lo, hi = sorted(((a.start(), a.end()), (b.start(), b.end())))
            yield sentence[lo[1]:hi[0]]


def scan(page: Path,
         suppressions: list[Suppression] | None = None) -> list[Finding]:
    """Every re-statement on one page, optionally exposing each suppression."""
    text = page.read_text()
    found: list[Finding] = []

    def suppress(line: int, predicate: str, exemption: str, s: str) -> None:
        if suppressions is not None:
            suppressions.append(Suppression(page, line, predicate, exemption, s))

    for bstart, block in blocks(text):
        lines = block.split("\n")
        # A heading and the prose beneath it arrive as one block when no blank
        # line separates them, which is how most of these pages are written.
        while lines and lines[0].lstrip().startswith("#"):
            lines.pop(0)
            bstart += 1
        if not lines:
            continue
        for offset, step in steps("\n".join(lines)):
            line = bstart + offset
            for sentence in sentences(" ".join(step.split())):
                for name, rule in PREDICATES.items():
                    if not re.search(rule["inputs"], sentence, re.I):
                        continue
                    # Tier 1 — the procedure's own word for the answer, defined
                    # out of raw cells. Reported however it is phrased.
                    if re.search(rule["own_verdict"], sentence, re.I):
                        found.append(Finding(page, line, name, "own-verdict",
                                             sentence))
                        continue
                    # Tier 2 — the contract's field. A cell may sit beside it;
                    # a definitional link between them may not.
                    if not re.search(rule["field_verdict"], sentence, re.I):
                        continue
                    gaps = list(_spans(sentence, rule["field_verdict"],
                                       rule["inputs"]))
                    if any(REASON.search(gap) for gap in gaps):
                        suppress(line, name, "reason", sentence)
                        continue
                    if not any(DEFINITIONAL.search(gap) for gap in gaps):
                        suppress(line, name, "no-definitional-link", sentence)
                        continue
                    found.append(Finding(page, line, name, "field-defined",
                                         sentence))
    return found


# ---------------------------------------------------------------- the tests

#: `work/reference/autopilot.md:131` as it stood on 2026-08-27 — the sentence
#: this guard was built from, kept verbatim so the guard can never be rewritten
#: into one that would have missed it.
THE_MEASURED_DEFECT = (
    "- **Eligible**: status ∈ {`not_started`, `blocked` with all blockers "
    "resolved}, has `evidence/<YYYY-MM>/<TASK-ID>-spec.md` with "
    "`Dispatch mode: auto` + non-`manual` Executor, hook safety scan passes, "
    "all listed dependencies resolved.\n")


class ProceduresReadTheContract(unittest.TestCase):
    """A procedure asks the payload; it does not re-derive the payload."""

    def scan_text(self, text: str, name: str = "page.md"):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / name
            page.write_text(text)
            suppressed: list[Suppression] = []
            return scan(page, suppressed), suppressed

    # -- the corpus ------------------------------------------------------

    def test_the_corpus_is_the_neighbours_and_is_not_empty(self):
        """One derivation of the corpus, two readers of it.

        Re-deriving the walk here would be, about the corpus, exactly the
        defect this module reports about predicates — so it is imported. What
        is asserted is that the import is live: the walk still finds pages,
        still includes the page this row was written for, and still reaches
        the lane reference trees where procedure actually lives.
        """
        pages = procedure_pages()
        self.assertGreater(len(pages), 20, "the shared walk returned almost "
                                           "nothing — the corpus broke")
        self.assertIn(PERRY_HOME / "work" / "reference" / "autopilot.md", pages)
        self.assertIn(PERRY_HOME / "SKILL.md", pages)

    def test_a_planted_page_anywhere_in_the_tree_is_scanned(self):
        """The anti-defeat property, exercised rather than inherited.

        Four guards here were beaten by a file a hardcoded list did not name.
        The corpus walk is the neighbour's and it tests its own shape; what
        this checks is that *this* scanner is actually run over what the walk
        returns, including a lane that did not exist and a page nested under
        it.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lane = root / "reckon"
            (lane / "reference" / "deep").mkdir(parents=True)
            (lane / "SKILL.md").write_text("# reckon\n\n" + THE_MEASURED_DEFECT)
            (lane / "reference" / "deep" / "buried.md").write_text(
                "# buried\n\n1. A row is eligible once every listed "
                "dependency has closed.\n")
            (root / "reference").mkdir()
            (root / "SKILL.md").write_text("# root\n")
            (root / "reference" / "clean.md").write_text(
                "# clean\n\n1. Dispatch the rows `perry-task list --json` "
                "reports as `startable`.\n")

            pages = procedure_pages(root)
            reported = {p.relative_to(root).as_posix(): scan(p) for p in pages}
            self.assertEqual(
                set(reported),
                {"SKILL.md", "reference/clean.md", "reckon/SKILL.md",
                 "reckon/reference/deep/buried.md"},
                "the shared walk must reach a lane that did not exist")
            self.assertEqual(
                [f.tier for f in reported["reckon/SKILL.md"]], ["own-verdict"],
                "the planted lane entry point must report")
            self.assertEqual(
                [f.tier for f in reported["reckon/reference/deep/buried.md"]],
                ["own-verdict"], "a page nested under a new lane must report")
            self.assertEqual(reported["reference/clean.md"], [],
                             "delegating to the payload is the shape this "
                             "guard is asking for")
            self.assertEqual(reported["SKILL.md"], [])

    # -- the measured defect ---------------------------------------------

    def test_the_measured_defect_is_reported_verbatim(self):
        """`autopilot.md:131`, kept as a fixture so it can never come back.

        This is the one assertion that proves the guard is real rather than
        tuned to whatever the page says today: the sentence TASK-174 removed,
        byte for byte, must still be red.
        """
        findings, _ = self.scan_text(
            "# autopilot\n\n"
            "3. Read the BOARD top-to-bottom. For each open row, classify:\n"
            + THE_MEASURED_DEFECT)
        self.assertEqual([(f.predicate, f.tier) for f in findings],
                         [("startability", "own-verdict")],
                         f"the sentence this guard exists for; got {findings}")

    def test_the_page_the_row_fixed_no_longer_restates_it(self):
        """`work/reference/autopilot.md` itself, named.

        The corpus assertion below covers this page too, but only as one of
        forty-five. Naming it here means a future edit that puts the predicate
        back reports as *this* row's regression rather than as a corpus number
        that moved.
        """
        page = PERRY_HOME / "work" / "reference" / "autopilot.md"
        self.assertEqual([f.render() for f in scan(page)], [])
        self.assertIn("startable", page.read_text(),
                      "the eligibility step must read the field it stopped "
                      "re-deriving")

    # -- tier 1: the procedure's own verdict ------------------------------

    def test_an_invented_verdict_defined_from_cells_is_reported(self):
        """Tier 1, across the spellings the same rule can be written in.

        The two live copies of the `startable` rule in `bin/` were not
        textually alike, which is why `tests/one_startable_rule.py` is an AST
        scan. Prose has no AST, so the defence is that the guard is anchored on
        the *shape* — an invented verdict, plus a raw cell — and this battery
        is what keeps a later narrowing of either pattern from quietly
        deleting the rule.
        """
        cases = [
            "1. A row is eligible when its status is `not_started`.",
            "1. Treat the row as actionable if no dependency remains open.",
            "1. **Ready to dispatch**: every blocker has closed.",
            "1. The task is dispatchable once all its dependencies are "
            "resolved.",
            "1. Eligible rows are the ones whose status is `blocked` with all "
            "blockers resolved.",
            "1. It is eligible because all of its dependencies are closed.",
        ]
        for text in cases:
            with self.subTest(text=text):
                findings, _ = self.scan_text("# page\n\n" + text + "\n")
                self.assertEqual([f.tier for f in findings], ["own-verdict"],
                                 text)

    def test_no_connective_launders_an_invented_verdict(self):
        """*"because"* does not turn a second implementation into a reason.

        Tier 2 grants the reason exemption to sentences about the contract's
        own field, where the payload is plainly still the authority. Granting
        it to an invented verdict would make the whole tier evadable by one
        word, so it is not granted — and this is the test that says so, since
        the two tiers otherwise share every pattern.
        """
        reason, _ = self.scan_text(
            "# page\n\n1. The row is eligible because its status is "
            "`not_started` and all blockers are resolved.\n")
        self.assertEqual([f.tier for f in reason], ["own-verdict"])

    def test_delegating_to_the_payload_is_the_green_shape(self):
        """What the fix looks like, so the guard is known to accept it."""
        cases = [
            "1. **Eligible**: `startable` is `true` in `perry-task list "
            "--json`.",
            "1. Dispatch only the rows the payload reports as `startable`.",
            "1. Skipped — blocked: `blocked_by` still names an open id.",
            "1. Read `depends_on_resolved` for which edge is unsatisfied and "
            "what kind of thing it is.",
        ]
        for text in cases:
            with self.subTest(text=text):
                findings, _ = self.scan_text("# page\n\n" + text + "\n")
                self.assertEqual(findings, [], text)

    # -- tier 2: the contract's own field ---------------------------------

    def test_an_explanation_of_a_field_stays_green(self):
        """The line this guard would be worthless for crossing.

        A reference page that cannot explain `startable` cannot teach anybody
        to use it, and a guard that forbids the explanation is one people
        switch off. Each of these mentions the field and a board cell in one
        sentence, and each is suppressed for a stated reason rather than by
        accident — which is what the `suppressed` assertion is for.
        """
        cases = [
            ("1. `startable` is `false` because none of its dependencies has "
             "closed.", "reason"),
            ("1. A row whose Status cell still reads `blocked` can be "
             "`startable` anyway — `blocked_stale` says the cell is out of "
             "date.", "no-definitional-link"),
            ("1. `blocked_stale` is `true` on a row that says `blocked` while "
             "every one of its dependencies has closed, which means the cell "
             "and the graph disagree.", "no-definitional-link"),
        ]
        for text, exemption in cases:
            with self.subTest(text=text):
                findings, suppressed = self.scan_text("# page\n\n" + text + "\n")
                self.assertEqual(findings, [], text)
                self.assertIn(exemption, [s.exemption for s in suppressed],
                              f"the exemption must be observable; got "
                              f"{[s.exemption for s in suppressed]}")

    def test_defining_the_field_out_of_cells_is_still_reported(self):
        """Tier 2's own failure: the field's name used as cover for the rule.

        *"`startable` is `true` when every blocker has closed"* is the
        predicate, written a second time, wearing the field's name. If tier 2
        accepted every sentence that mentions a field, the whole guard would be
        one backtick away from silence.
        """
        cases = [
            "1. `startable` is `true` when every blocker has closed.",
            "1. `startable`: status ∈ {`not_started`, `in_progress`}.",
            "1. A row is `startable` if all its dependencies are resolved.",
            "1. `blocked_stale` means the row says `blocked` with every "
            "dependency closed.",
        ]
        for text in cases:
            with self.subTest(text=text):
                findings, _ = self.scan_text("# page\n\n" + text + "\n")
                self.assertEqual([f.tier for f in findings], ["field-defined"],
                                 text)

    def test_naming_the_field_does_not_license_a_restatement_beside_it(self):
        """The neighbour's R2 lesson, on the read side.

        Both live instances of R2 had the tool named and the hand path
        licensed one clause later. The same shape here — cite `startable`,
        then spell the predicate out — must report, because the spelled-out
        half is the half a reader in a hurry follows.
        """
        findings, _ = self.scan_text(
            "# page\n\n"
            "1. Read `startable` from the payload. Eligible means status "
            "`not_started`, or `blocked` with all blockers resolved.\n")
        self.assertEqual([f.tier for f in findings], ["own-verdict"])

    # -- what is not a predicate at all -----------------------------------

    def test_a_cell_condition_without_a_verdict_is_not_a_restatement(self):
        """A step branching on `Status` to pick a command decides nothing.

        `dispatch.md` reads *"if the row is `not_started`, run `perry-task
        start`; if it is `blocked` or `review`, run `status --status
        in_progress`"*. That is a status-driven branch over which write to
        perform, not a second opinion about whether the row can be worked on,
        and a guard that reports it forbids every conditional in the corpus.
        """
        cases = [
            "1. If the row is `not_started`, run `perry-task start`; if it is "
            "`blocked` or `review`, run `perry-task status <ID> --status "
            "in_progress`.",
            "1. All `P0` open tasks (not_started / in_progress / blocked / "
            "review).",
            "1. Move the row to `review`; never to `done`.",
            "1. A dependency is open, so leave the row alone.",
        ]
        for text in cases:
            with self.subTest(text=text):
                findings, _ = self.scan_text("# page\n\n" + text + "\n")
                self.assertEqual(findings, [], text)

    def test_an_unquantified_remark_about_one_edge_is_not_the_predicate(self):
        """The quantifier is load-bearing and this is why.

        The contract's answer is about the whole dependency set; *"a dependency
        is open"* is a remark about one edge and cannot be followed as a rule.
        Dropping the quantifier requirement would make `INPUTS` match half the
        prose in these pages, and the first thing it would report is the
        explanation in `test_an_explanation_of_a_field_stays_green`.
        """
        findings, suppressed = self.scan_text(
            "# page\n\n1. The row is not eligible; a dependency is open.\n")
        self.assertEqual(findings, [])
        self.assertEqual(suppressed, [])

    def test_a_field_name_is_not_the_cell_it_is_named_after(self):
        """`blocked_stale` and `blocked_by` are not the word `blocked`.

        Measured while this guard was being written: with the status enum
        unbounded, `blocked` matched inside both field names, so **the sentence
        that explains `blocked_stale` carried its own raw-cell match** and the
        tier-2 branch reported the explanation this guard exists to protect. An
        underscore is a word character, so `\b` is the whole fix — and this is
        the test that keeps someone from dropping it back out while widening
        the enum.
        """
        for text in ["1. `blocked_stale` is the field; `blocked_by` names the "
                     "open ids.",
                     "1. Read `blocked_by` and `depends_on_resolved` from the "
                     "payload."]:
            with self.subTest(text=text):
                findings, suppressed = self.scan_text("# page\n\n" + text + "\n")
                self.assertEqual(findings, [], text)
                self.assertEqual(suppressed, [], "a field name must not even "
                                                 "become a candidate")

    def test_a_fenced_block_is_not_prose(self):
        """Exemption 3, inherited from `blocks()` and worth pinning here.

        The fenced regions in these pages are commands and payload samples —
        the very thing this guard wants procedures to call and read. A guard
        that reported the sample would be asking pages to stop showing the
        payload.
        """
        findings, _ = self.scan_text(
            "# page\n\n"
            "```\n"
            "eligible = status in {not_started} and not blocked_by\n"
            "```\n")
        self.assertEqual(findings, [])

    # -- the declarations are live ----------------------------------------

    def test_declared_fields_are_served_by_the_contract(self):
        """Every declared field is a key the read contract actually serves.

        The rule table is the one thing here that is written down. An entry
        naming a field somebody renamed would go on suppressing nothing
        forever — silently, because a rule that never fires looks exactly like
        a clean repository. This is `test_owner_tools_exist`'s job, done
        against the contract instead of against `bin/`.
        """
        for name, rule in PREDICATES.items():
            contract = PERRY_HOME / rule["contract"]
            with self.subTest(predicate=name):
                self.assertTrue(contract.is_file(),
                                f"{rule['contract']} does not exist")
                text = contract.read_text()
                for field in rule["fields"]:
                    self.assertRegex(
                        text, rf"\|\s*`{re.escape(field)}`\s*\|",
                        f"`{field}` is not a key in {rule['contract']} — the "
                        f"rule is guarding a field the contract stopped "
                        f"serving")

    def test_the_declared_home_exists(self):
        """`bin/` states each predicate somewhere, and the entry names where.

        `tests/one_startable_rule.py` asserts there is exactly **one** home and
        does not care where. This asserts the place named here is still that
        place, so the docstring's claim about where the rule lives cannot rot
        into a file reference that resolves to nothing.
        """
        for name, rule in PREDICATES.items():
            path, function = rule["home"]
            with self.subTest(predicate=name):
                source = PERRY_HOME / path
                self.assertTrue(source.is_file(), f"{path} does not exist")
                self.assertRegex(source.read_text(),
                                 rf"(?m)^def {re.escape(function)}\(",
                                 f"{path} no longer defines {function}()")

    def test_every_declared_predicate_has_both_fixtures(self):
        """A rule with no red fixture and no green fixture is unreviewed.

        The neighbour asserts this over `TARGETS`; the same argument applies
        the moment a second predicate is declared here, and asserting it now
        is what makes the second entry arrive with its evidence rather than
        without it.
        """
        fixtures = {
            "startability": (
                "1. A row is eligible when all blockers are resolved.\n",
                "1. Dispatch the rows reported `startable`.\n"),
        }
        self.assertEqual(set(PREDICATES), set(fixtures),
                         "a declared predicate without both fixtures is "
                         "unreviewed")
        for name, (red, green) in fixtures.items():
            with self.subTest(predicate=name, branch="red"):
                findings, _ = self.scan_text("# page\n\n" + red)
                self.assertEqual([f.predicate for f in findings], [name])
            with self.subTest(predicate=name, branch="green"):
                findings, _ = self.scan_text("# page\n\n" + green)
                self.assertEqual(findings, [])

    # -- the corpus assertion ---------------------------------------------

    def test_no_procedure_restates_a_contract_predicate(self):
        findings = []
        for page in procedure_pages():
            findings.extend(f.render() for f in scan(page))
        self.assertEqual(
            findings, [],
            "A procedure must not compute a predicate the contract already "
            "serves — ask the payload for the field instead. These sentences "
            "derive the answer from the cells the payload reads:\n"
            + "\n".join(findings))


if __name__ == "__main__":
    unittest.main()
