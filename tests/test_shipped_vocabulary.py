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


def read(rel: str) -> str:
    return (PERRY_HOME / rel).read_text(encoding="utf-8")


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


ALIASES = {"okr": "goals", "pmo": "work", "design": "decide"}

# `/perry` with no lane at all, plus the pipelines that belong to the router
# rather than to any lane. Harvested from `SKILL.md` rather than listed, so a
# router that gains or loses one does not need this file edited.
ROUTER_LANES = set(LANES) | set(ALIASES)


def lane_of(word: str) -> str | None:
    w = word.lower()
    return w if w in LANES else ALIASES.get(w)


class TestEveryCommandTheReadmeShowsExists(unittest.TestCase):
    """`TASK-027-round4-review.md § i-1`: both READMEs advertised
    `/perry pmo decide <topic>`. The lane alias resolves — `pmo` → `work` — and
    then the command dies on a subcommand that changed lanes, because the
    signed hand-off contract of 2026-08-16 deleted `decide` from `work` and
    `work/SKILL.md` tombstones the row.

    A reader who types a command that does not exist gets nothing and no error,
    which is the worst failure mode available. `tests/test_entrance.py` already
    guards the *lane* half of this (no bare `/okr`, `/pmo`, `/design`); this
    guards the *subcommand* half, which is the half that was wrong.

    The declared set is computed from the router and the three lane indexes.
    Nothing here is hand-listed, so the guard cannot drift away from what the
    lanes actually ship.
    """

    READMES = ("README.md", "README_cn.md")

    # A row of a lane's subcommand index: `| \`plan-week\` | … |`. A row whose
    # first cell carries `~~` is a tombstone — `work/SKILL.md` keeps the
    # withdrawn `decide` row visible so a reader learns where it went, and
    # counting it as declared would re-legalise the exact command i-1 found.
    ROW = re.compile(r"^\|\s*([^|]+?)\s*\|")
    TOKEN = re.compile(r"`([^`]+)`")
    WORD = re.compile(r"^[a-z][a-z0-9-]*$")
    # `/perry work triage`, `/perry goals plan-phase`, and the lane docs'
    # shorthand `/pmo viewer` — which is where `viewer` is declared, since it
    # lives in `work/SKILL.md`'s reference table and not in its index.
    INLINE = re.compile(
        r"/(?:perry\s+)?(goals|work|decide|okr|pmo|design)\s+([a-z][a-z0-9-]*)")

    @classmethod
    def declared(cls) -> tuple[set[tuple[str, str]], set[str]]:
        """(lane, subcommand) pairs, and the router's own bare commands."""
        pairs: set[tuple[str, str]] = set()
        for lane in LANES:
            text = (PERRY_HOME / lane / "SKILL.md").read_text()
            for line in text.splitlines():
                m = cls.ROW.match(line)
                if not m or "~~" in m.group(1):
                    continue
                for span in cls.TOKEN.findall(m.group(1)):
                    head = span.strip().split()[0] if span.strip() else ""
                    if cls.WORD.match(head):
                        pairs.add((lane, head))
            for found_lane, sub in cls.INLINE.findall(text):
                pairs.add((lane_of(found_lane), sub))

        router = (PERRY_HOME / "SKILL.md").read_text()
        for found_lane, sub in cls.INLINE.findall(router):
            pairs.add((lane_of(found_lane), sub))
        bare = {w for w in re.findall(r"/perry\s+([a-z][a-z0-9-]*)", router)
                if w not in ROUTER_LANES}
        return pairs, bare

    @classmethod
    def commands_in(cls, text: str) -> list[tuple[str, str | None, str]]:
        """Every command a README shows, as (raw, lane or None, subcommand).

        Two shapes, because the READMEs use both: a full `/perry <lane> <sub>`
        anywhere in the page, and a bare subcommand in the first cell of a row
        of one of the three per-lane tables under a `### \\`<lane>\\`` heading.
        The second shape is the one i-1 lived in.
        """
        out: list[tuple[str, str | None, str]] = []
        lane_here: str | None = None
        fenced = False
        for line in text.splitlines():
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            h = re.match(r"^###\s+`([a-z]+)`", line)
            if h:
                lane_here = lane_of(h.group(1))
            elif line.startswith("## "):
                lane_here = None
            # Only look where a command is actually being *shown*: inside
            # backticks, or on a fenced line that begins with the command.
            # The install snippet's "3. Confirm /perry is available." is prose
            # that happens to sit in a fence, and reading `is` out of it would
            # make this guard cry wolf on its own README.
            if fenced:
                scan = line if re.match(r"^\s*/perry\b", line) else ""
            else:
                scan = " ".join(re.findall(r"`([^`]+)`", line))
            for m in re.finditer(r"/perry\s+([a-z][a-z0-9-]*)"
                                 r"(?:\s+([a-z][a-z0-9-]*))?", scan):
                first, second = m.group(1), m.group(2)
                lane = lane_of(first)
                if lane and second:
                    out.append((m.group(0), lane, second))
                elif not lane:
                    out.append((m.group(0), None, first))
            if lane_here:
                m = cls.ROW.match(line)
                if m and "~~" not in m.group(1):
                    for span in cls.TOKEN.findall(m.group(1)):
                        head = span.strip().split()[0] if span.strip() else ""
                        if cls.WORD.match(head):
                            out.append((f"{lane_here} {head}", lane_here, head))
        return out

    def offenders(self, text: str) -> list[str]:
        pairs, bare = self.declared()
        subs = {s for _, s in pairs}
        bad = []
        for raw, lane, sub in self.commands_in(text):
            if lane is None:
                # No lane written. Legal when the subcommand is unambiguous
                # (`SKILL.md`: "/perry plan-phase and /perry goals plan-phase
                # are the same thing"), or when it is a router command.
                if sub in bare or sub in subs:
                    continue
                bad.append(f"`{raw}` — no lane declares `{sub}`")
            elif (lane, sub) not in pairs:
                bad.append(f"`{raw}` — the `{lane}` lane declares no `{sub}`")
        return bad

    def test_the_declared_set_is_not_empty_or_trivial(self):
        """Guard against the guard. If the harvest broke, every assertion
        below would pass over an empty set and say nothing."""
        pairs, bare = self.declared()
        self.assertGreater(len(pairs), 40,
                           f"only {len(pairs)} lane subcommands harvested — "
                           f"the lane index tables have moved")
        for expected in (("goals", "plan-phase"), ("goals", "score-phase"),
                         ("work", "triage"), ("work", "close-task"),
                         ("work", "viewer"), ("decide", "adr"),
                         ("decide", "resolve"), ("decide", "lock")):
            self.assertIn(expected, pairs)
        self.assertIn("diagnose", bare)
        self.assertIn("adopt", bare)

    def test_the_tombstoned_subcommand_is_not_harvested_as_declared(self):
        """`work/SKILL.md` keeps the withdrawn `decide` row visible, struck
        through, so a reader learns where it went. If the harvest counted it,
        this whole file would bless the command it exists to catch."""
        pairs, _ = self.declared()
        self.assertNotIn(("work", "decide"), pairs,
                         "the strikethrough row was read as a live command")

    def test_the_scan_finds_the_commands_the_readmes_actually_show(self):
        """The other half of the anti-vacuity guard: the extractor has to be
        seeing the page, not an empty list."""
        for doc in self.READMES:
            with self.subTest(doc=doc):
                found = self.commands_in(read(doc))
                self.assertGreater(len(found), 30,
                                   f"{doc}: only {len(found)} commands seen")
                self.assertIn(("work", "triage"),
                              [(l, s) for _, l, s in found])

    def test_the_scan_would_catch_the_command_that_was_wrong(self):
        """i-1, replayed. Both READMEs carried `/perry pmo decide <topic>` and
        a `decide <id>` row in the design lane's table; a guard that does not
        go red on either of those is not the guard this task owes."""
        replay = (
            "| Write down a decision | `/perry pmo decide <topic>` |\n"
            "\n### `design`\n\n"
            "| `decide <id>` | Answer the open questions one by one |\n"
        )
        bad = self.offenders(replay)
        self.assertEqual(len(bad), 2, f"expected both shapes caught, got {bad}")
        self.assertTrue(all("decide" in b for b in bad))

    def test_neither_readme_shows_a_command_that_does_not_exist(self):
        for doc in self.READMES:
            with self.subTest(doc=doc):
                bad = self.offenders(read(doc))
                self.assertEqual(
                    bad, [],
                    f"{doc} advertises commands the lanes do not declare:\n    "
                    + "\n    ".join(bad))


class TestTheReadmesNameTheFourModes(unittest.TestCase):
    """`DESIGN-003` is the largest thing built this phase and
    `grep -c mode README.md README_cn.md` returned 0 and 0. A reader deciding
    whether Perry fits their project could not find out that it is not only
    for software sprints."""

    READMES = ("README.md", "README_cn.md")
    MODES = ("project", "pipeline", "queue", "inquiry")

    def test_both_readmes_name_all_four_modes(self):
        for doc in self.READMES:
            with self.subTest(doc=doc):
                text = read(doc)
                for mode in self.MODES:
                    self.assertIn(f"`{mode}`", text,
                                  f"{doc} never names the `{mode}` mode")

    def test_both_readmes_say_how_a_project_declares_one(self):
        """Naming the modes without the register is a feature list. The
        register is the only thing that turns three of the four on."""
        for doc in self.READMES:
            with self.subTest(doc=doc):
                text = read(doc)
                self.assertIn("## Tracks", text,
                              f"{doc} names the modes but not the register "
                              f"that declares one")
                self.assertIn(".perry/config.md", text)

    def test_both_readmes_link_the_mode_file_that_carries_each_rule(self):
        for doc in self.READMES:
            with self.subTest(doc=doc):
                text = read(doc)
                for mode in self.MODES:
                    self.assertIn(f"modes/{mode}.md", text,
                                  f"{doc} does not point at modes/{mode}.md")

    def test_the_mode_files_the_readmes_point_at_exist(self):
        for mode in self.MODES:
            self.assertTrue((PERRY_HOME / "modes" / f"{mode}.md").is_file())

    def test_both_readmes_reflect_that_migration_is_mandatory(self):
        """`ADR-004`. A front door that promises drop-in compatibility is now
        false, and the README is the place a user forms that expectation."""
        for doc in self.READMES:
            with self.subTest(doc=doc):
                text = read(doc)
                self.assertIn("ADR-004-mandatory-migration.md", text,
                              f"{doc} never cites the decision")
                self.assertIn("/perry adopt", text)

    def test_the_readmes_show_where_state_actually_lands(self):
        """Found while fixing i-1, and the same class of defect. The default
        state root moved to `perry/` on 2026-08-17 so that a project's own
        `design/` and `evidence/` stop colliding — and both READMEs still drew
        the tree with `OKR.md` and `BOARD.md` at the top level. A reader who
        checked would have found neither file where the front door said.

        Pinned against the router's declaration rather than a literal, so
        moving the default again fails here instead of drifting.
        """
        m = re.search(r"write `State root:\s*([^\s`]+)`", read("SKILL.md"))
        self.assertIsNotNone(
            m, "SKILL.md no longer declares the default state root — this "
               "test would otherwise pass against nothing")
        default = m.group(1)
        for doc in self.READMES:
            with self.subTest(doc=doc):
                text = read(doc)
                tree = re.search(r"```\n(your-project/.*?)```", text, re.S)
                self.assertIsNotNone(tree, f"{doc} no longer draws the tree")
                body = tree.group(1)
                lines = body.splitlines()
                self.assertGreater(len(lines), 8, f"{doc}'s tree is a stub")
                # `.perry/` is a different directory and always at the top —
                # a bare `assertIn("perry/")` is satisfied by it, which is
                # exactly the shape of guard this repo keeps catching.
                root = [i for i, ln in enumerate(lines)
                        if re.search(rf"(?<![.\w]){re.escape(default)}/", ln)]
                self.assertTrue(
                    root,
                    f"{doc}'s tree never shows the `{default}/` container "
                    f"setup actually writes state into")
                okr = [i for i, ln in enumerate(lines) if "OKR.md" in ln]
                self.assertTrue(okr, f"{doc}'s tree does not show OKR.md")
                self.assertGreater(
                    okr[0], root[0],
                    f"{doc} draws OKR.md outside `{default}/`")

    def test_the_adr_the_readmes_cite_exists_and_is_active(self):
        adr = PERRY_HOME / "perry" / "decisions" / "ADR-004-mandatory-migration.md"
        self.assertTrue(adr.is_file())
        self.assertRegex(adr.read_text(),
                         re.compile(r"^>\s*Status:\s*active", re.M))


if __name__ == "__main__":
    unittest.main()
