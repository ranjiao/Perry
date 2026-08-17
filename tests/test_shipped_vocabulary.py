"""What Perry hands a user must be written in the vocabulary a user can type.

`SKILL.md § Reading the lane docs` carves out exactly two classes of file —
lane `SKILL.md` bodies and `*/reference/` prose — as places where the shorthand
`/pmo triage` is left standing, because inside a Perry session an agent reads
it as routing vocabulary and translates before quoting.

The round-4 review found that the carve-out was being applied to four classes
it never covered, and that each of the four ends up in front of the user with
**no agent step left to translate it**:

- `bin/` — `perry-state` fills the `warnings[]` array and `perry-lint` fills
  `Finding.message`; `reference/i18n.md § chat output` sends both straight to
  chat. One of them named `/pmo decide --expire`, which exists in neither
  vocabulary: `decide <topic>` left the `work` lane on 2026-08-16 and the live
  form is `/perry decide adr --expire`.
- `*/state/*_TEMPLATE.md` and `state/*_TEMPLATE.md` — these are copied verbatim
  into the user's own repository and stay there. `BOARD_TEMPLATE.md`'s two
  header lines sit at the top of the single most-read file Perry produces.
- `packs/` and the shared root `reference/` — outside every lane, so outside
  every lane-scoped guard.
- lane frontmatter `description:` — read by the host, not by an agent that has
  already loaded the router.

None of these had a guard of any kind. This file is that guard.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
LANES = ("goals", "work", "decide")

# A withdrawn command in any shape a document actually writes one:
#
#   `/pmo triage`   `/okr`   /okr init   `pmo triage`   `okr score`
#
# The lookbehind keeps `/perry work triage` out — the live form has a name
# character immediately before the lane word, not a slash. The trailing
# `(?![\w-])` keeps `evidence/<YYYY-MM>/okr-vN-retro.md` out: a `\b` there
# treats the hyphen as a boundary and reads a filename as a command.
WITHDRAWN = re.compile(
    r"(?<!\w)/(?:okr|pmo|design)(?![\w-])"
    r"|`(?:okr|pmo|design)\s+[a-z]"
)


def withdrawn_hits(text: str) -> list[str]:
    return WITHDRAWN.findall(text)


class TestBinPrintsOnlyLiveCommands(unittest.TestCase):
    """`bin/` output is the quote, already rendered.

    Reproduced by the reviewer with no mutation at all:

        $ python3 bin/perry-state --json --root tests/fixtures/sample-project
        warnings: ['ADR-002 sunset criteria passed 16d ago —
                   run /pmo decide --expire ADR-002.']

    The scan is over string *literals* rather than raw file text, and skips
    docstrings, so a comment explaining the old vocabulary is still allowed
    while anything that can reach a user is not. That distinction is the whole
    reason this is an AST walk instead of a grep.
    """

    TOOLS = ("perry-state", "perry-lint")

    @staticmethod
    def message_literals(path: Path) -> list[tuple[int, str]]:
        tree = ast.parse(path.read_text())
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
                body = node.body
                if (body and isinstance(body[0], ast.Expr)
                        and isinstance(body[0].value, ast.Constant)
                        and isinstance(body[0].value.value, str)):
                    docstrings.add(id(body[0].value))
        out = []
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and id(node) not in docstrings):
                out.append((node.lineno, node.value))
        return out

    def test_no_tool_puts_a_withdrawn_command_in_a_string_it_can_print(self):
        offenders = []
        for tool in self.TOOLS:
            path = PERRY_HOME / "bin" / tool
            for lineno, value in self.message_literals(path):
                for hit in withdrawn_hits(value):
                    offenders.append(
                        f"bin/{tool}:{lineno} → {hit.strip()!r} in "
                        f"{value.strip()[:80]!r}")
                    break
        self.assertEqual(
            offenders, [],
            "a bin/ tool can print a withdrawn command to the user:\n    "
            + "\n    ".join(offenders))

    def test_the_expired_adr_warning_names_the_lane_that_owns_adrs(self):
        """`/pmo decide --expire` was doubly dead — wrong lane *and* a deleted
        subcommand — so translating `pmo` → `work` would have produced another
        command that does not exist. Pinned as a literal because it is the one
        string in this file that alias translation could not have fixed.
        """
        text = (PERRY_HOME / "bin" / "perry-state").read_text()
        self.assertIn("/perry decide adr --expire", text,
                      "the expired-sunset warning no longer routes to "
                      "`/perry decide adr --expire`")
        self.assertNotIn("work decide --expire", text,
                         "the warning was alias-translated into "
                         "`/perry work decide`, which the contract deleted")

    def test_the_sample_project_warning_is_typeable(self):
        """End-to-end over the shipped fixture: whatever the tool actually
        emits, not what the source looks like."""
        import json
        import subprocess

        out = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"), "--json",
             "--root", str(PERRY_HOME / "tests" / "fixtures" / "sample-project")],
            capture_output=True, text=True, check=True).stdout
        payload = json.loads(out)
        emitted = list(payload.get("warnings") or [])
        self.assertTrue(emitted, "the fixture stopped producing any warning — "
                                 "this test would pass vacuously")
        for w in emitted:
            self.assertEqual(withdrawn_hits(w), [],
                             f"perry-state emitted a withdrawn command: {w}")


class TestShippedTemplatesAreTypeable(unittest.TestCase):
    """A template is not documentation — it is the user's file, pre-written.

    `work/reference/bootstrap.md` writes `BOARD.md` from
    `work/state/BOARD_TEMPLATE.md`; `decide/reference/decisions.md` writes every
    ADR from `decide/state/ADR_TEMPLATE.md`. Fourteen withdrawn commands across
    nine templates were being copied into every project Perry bootstrapped, and
    stayed there — including `` `/pmo decide --expire ADR-{{N}}` `` stamped into
    every ADR that has a sunset criterion.
    """

    def template_files(self):
        for lane in LANES:
            yield from sorted((PERRY_HOME / lane / "state").glob("*.md"))
        yield from sorted((PERRY_HOME / "state").glob("*.md"))

    def test_the_state_directories_are_where_this_thinks_they_are(self):
        """Guard against the guard: if `*/state/` moves, an empty glob makes
        every assertion below vacuously true."""
        found = list(self.template_files())
        self.assertGreater(len(found), 20,
                           f"only {len(found)} state templates found — the "
                           f"glob has come unstuck from the tree")
        names = {p.name for p in found}
        for expected in ("BOARD_TEMPLATE.md", "ADR_TEMPLATE.md",
                         "DECISIONS_TEMPLATE.md", "hook_TEMPLATE.md",
                         "phase_TEMPLATE.md", "diagnosis_TEMPLATE.md"):
            self.assertIn(expected, names)

    def test_no_shipped_template_writes_a_withdrawn_command_into_a_project(self):
        offenders = []
        for path in self.template_files():
            rel = path.relative_to(PERRY_HOME).as_posix()
            for n, line in enumerate(path.read_text().splitlines(), 1):
                for hit in withdrawn_hits(line):
                    offenders.append(f"{rel}:{n} → {hit.strip()!r}\n"
                                     f"      {line.strip()[:100]}")
                    break
        self.assertEqual(
            offenders, [],
            "a shipped template stamps a withdrawn command into the user's "
            "own repository:\n    " + "\n    ".join(offenders))

    def test_the_decisions_header_does_not_attribute_the_file_to_pmo(self):
        """`DECISIONS.md` moved to `decide` under the signed hand-off contract.
        Its own template — one of the two files this task relocated — kept a
        header asserting that the lane forbidden to write it maintains it, and
        that header is what lands in the user's repo."""
        header = (PERRY_HOME / "decide" / "state"
                  / "DECISIONS_TEMPLATE.md").read_text().splitlines()[:6]
        text = "\n".join(header)
        self.assertNotRegex(
            text, r"\bPMO\b",
            "DECISIONS_TEMPLATE.md still credits PMO with maintaining a file "
            "the contract gave to `decide`")
        self.assertIn("decide", text,
                      "the header names no maintainer at all")


class TestLaneFrontmatterDescribesALaneNotACommand(unittest.TestCase):
    """Deliverable 4 covered `name:` and `description:`. Only `name:` landed.

    Beyond the letter of it: the old text asserted that `/okr`, `/pmo` and
    `/design` are commands a user invokes and that `pmo` and `okr` are skills.
    `SKILL.md § One skill, three lanes` states both are false — Perry registers
    exactly one skill and the lanes are read on demand, not invoked.
    """

    @staticmethod
    def description(lane: str) -> str:
        text = (PERRY_HOME / lane / "SKILL.md").read_text()
        m = re.search(r"^---\n(.*?)\n---", text, re.S)
        assert m, f"{lane}/SKILL.md has no frontmatter"
        d = re.search(r"^description:\s*(.*)$", m.group(1), re.M)
        assert d, f"{lane}/SKILL.md declares no description"
        return d.group(1)

    def test_no_description_promises_a_withdrawn_command(self):
        for lane in LANES:
            with self.subTest(lane=lane):
                desc = self.description(lane)
                self.assertEqual(
                    withdrawn_hits(desc), [],
                    f"{lane}/SKILL.md description tells the host the user "
                    f"invokes a withdrawn command: {desc[:120]}")

    def test_every_description_names_its_own_live_entrance(self):
        for lane in LANES:
            with self.subTest(lane=lane):
                self.assertIn(f"/perry {lane}", self.description(lane),
                              f"{lane}/SKILL.md description never names the "
                              f"form the user actually types")

    def test_no_description_calls_a_lane_a_skill(self):
        """`pmo skill` / `okr skill` in a description is the same claim the
        router spends its first section refuting."""
        for lane in LANES:
            with self.subTest(lane=lane):
                desc = self.description(lane)
                self.assertNotRegex(
                    desc, r"\b(pmo|okr|design)\s+skill\b",
                    f"{lane}/SKILL.md description still calls a sibling lane "
                    f"a separate skill")

    def test_every_description_says_it_is_not_a_separate_command(self):
        for lane in LANES:
            with self.subTest(lane=lane):
                self.assertIn("not a separate command", self.description(lane),
                              f"{lane}/SKILL.md description reads as a "
                              f"standalone skill's description")


class TestPackPointersResolve(unittest.TestCase):
    """`packs/software-ops/` was extracted out of `work/reference/`, and its
    relative pointers were not re-based.

    Nine of them — `state/runbook_TEMPLATE.md`, `subcommands.md § close-task`,
    `dispatch.md § Pre-flight` and friends — resolved as siblings before the
    extraction and resolve to nothing after it. These are the pages the `work`
    lane loads to run `runbook-check`, `incident` and the `close-task` gate, so
    every "create it from the template at X" instruction pointed at nothing.
    """

    # Backticked spans that are file pointers rather than prose. A pointer may
    # carry a `§ Section` suffix; only the path half is resolved.
    POINTER = re.compile(r"`([^`]*?\.md)(?:\s*§[^`]*)?`")

    # A pack page names paths in two different namespaces, and only one of them
    # is checkable here:
    #
    #   the USER's project root — `runbook/INDEX.md`, `.perry/hook.md`,
    #       `ARCHITECTURE.md`. These do not exist inside $PERRY_HOME and are
    #       not supposed to.
    #   PERRY's own tree — `state/runbook_TEMPLATE.md`, `subcommands.md`.
    #       These are the ones the pack extraction broke.
    #
    # Perry's own documents are lowercase (`subcommands.md`, `dispatch.md`) or
    # end in `_TEMPLATE.md`; the user's state files are SHOUTED
    # (`ARCHITECTURE.md`, `BOARD.md`, `INDEX.md`). That convention is what
    # separates the two namespaces without a hand-maintained allowlist.
    PERRY_DOC = re.compile(r"^[a-z][a-z0-9_-]*\.md$")

    def pack_pages(self):
        return sorted((PERRY_HOME / "packs").rglob("*.md"))

    def test_the_pack_tree_is_where_this_thinks_it_is(self):
        pages = self.pack_pages()
        self.assertGreaterEqual(len(pages), 3,
                                "packs/ has moved or emptied — this test would "
                                "pass vacuously")

    def perry_pointers(self, line: str):
        """The pointers on this line that name a document inside `$PERRY_HOME`."""
        for target in self.POINTER.findall(line):
            if "{{" in target or "<" in target or "*" in target:
                continue  # a shape, not a path
            if target.startswith("/"):
                continue  # absolute on the user's machine
            name = target.rsplit("/", 1)[-1]
            if (target.startswith("$PERRY_HOME/")
                    or name.endswith("_TEMPLATE.md")
                    or ("/" not in target and self.PERRY_DOC.match(target))):
                yield target

    def test_every_perry_pointer_in_a_pack_resolves(self):
        offenders = []
        for page in self.pack_pages():
            rel = page.relative_to(PERRY_HOME).as_posix()
            for n, line in enumerate(page.read_text().splitlines(), 1):
                for target in self.perry_pointers(line):
                    if target.startswith("$PERRY_HOME/"):
                        cand = PERRY_HOME / target[len("$PERRY_HOME/"):]
                    else:
                        # A bare pointer is read relative to the page, which is
                        # exactly the assumption the extraction broke.
                        cand = page.parent / target
                    if not cand.exists():
                        offenders.append(f"{rel}:{n} → `{target}` "
                                         f"(resolves to {cand}) does not exist")
        self.assertEqual(
            offenders, [],
            "a pack page points at a Perry file that does not exist:\n    "
            + "\n    ".join(offenders))

    def test_the_pointer_scan_still_sees_the_shapes_it_was_written_for(self):
        """Guard against the guard. The namespace filter above is the part
        that could silently stop matching, and if it did, every dangling
        pointer would go quiet rather than red."""
        seen = set()
        for page in self.pack_pages():
            for line in page.read_text().splitlines():
                seen.update(self.perry_pointers(line))
        self.assertTrue(any(t.endswith("_TEMPLATE.md") for t in seen),
                        "the scan no longer recognises a template pointer")
        self.assertTrue(any(t.rsplit("/", 1)[-1] in
                            {"subcommands.md", "dispatch.md"} for t in seen),
                        "the scan no longer recognises a lane-reference pointer")


class TestLaneReferencePointersResolve(unittest.TestCase):
    """M-1: `work/reference/extending.md` cited `reference/decisions.md`, which
    inside the `work` lane resolves to `work/reference/decisions.md` — a file
    that moved to `decide/reference/` in this same task.

    Round 3 found and repaired the sibling instance in
    `work/reference/subcommands.md`; this one was left. Two bullets directly
    above it already used the `$PERRY_HOME/…` absolute form, which is the shape
    that survives a lane move.
    """

    def test_extending_md_points_at_the_lane_that_owns_adr_conventions(self):
        text = (PERRY_HOME / "work" / "reference" / "extending.md").read_text()
        self.assertIn("$PERRY_HOME/decide/reference/decisions.md", text,
                      "the ADR-conventions bullet no longer names the file "
                      "that owns ADR conventions")
        self.assertFalse(
            (PERRY_HOME / "work" / "reference" / "decisions.md").exists(),
            "work/reference/decisions.md exists again — either the file moved "
            "back or this test is now checking nothing")

    def test_no_work_reference_page_cites_a_bare_sibling_that_left_the_lane(self):
        """The general form of the same defect: a relative pointer to a page
        the `work` lane no longer contains."""
        offenders = []
        moved = ("decisions.md", "design.md")
        for page in sorted((PERRY_HOME / "work" / "reference").glob("*.md")):
            for n, line in enumerate(page.read_text().splitlines(), 1):
                for span in re.findall(r"`([^`]+)`", line):
                    path = span.split("§")[0].strip()
                    if path.startswith("reference/") and path[len("reference/"):] in moved:
                        offenders.append(
                            f"work/reference/{page.name}:{n} → `{span}` "
                            f"resolves inside `work`, where it does not exist")
        self.assertEqual(
            offenders, [],
            "a work/reference page cites a page that left the lane:\n    "
            + "\n    ".join(offenders))


if __name__ == "__main__":
    unittest.main()
