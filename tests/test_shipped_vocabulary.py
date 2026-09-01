"""What Perry hands a user must be written in the vocabulary a user can type.

`SKILL.md § Reading the lane docs` carves out the pages an agent **loads and
re-renders** before a user sees them — the three lane `SKILL.md` bodies,
`*/reference/`, `packs/`, and the shared root `reference/`. Inside a Perry
session that shorthand is routing vocabulary; the agent translates before
quoting. This file does not police those.

It polices the complement: everything with **no agent step left to translate
it**. The carve-out note in `SKILL.md` lists those classes in prose; this file
is the same list, mechanically, and `TestTheCarveOutSaysWhatThisFileEnforces`
asserts the two lists agree, so neither can drift without the other going red.

- `bin/` — `--help` is the quote, already rendered, printed to a terminal.
  `perry-state` also fills `warnings[]` and `perry-lint` fills
  `Finding.message`; `reference/i18n.md § chat output` sends both straight to
  chat. One of them named `/pmo decide --expire`, which exists in neither
  vocabulary: `decide <topic>` left the `work` lane on 2026-08-16 and the live
  form is `/perry decide adr --expire`.
- `*/state/*_TEMPLATE.md` and `state/*_TEMPLATE.md` — copied verbatim into the
  user's own repository and left there. `BOARD_TEMPLATE.md`'s two header lines
  sit at the top of the single most-read file Perry produces.
- `setup` — its completion banner is the first thing a user reads after
  install, at the exact moment they learn what to type.
- lane frontmatter `description:` — read by the host, not by an agent that has
  already loaded the router.
- `SKILL.md` itself — the router is the page a new user is shown, and the
  carve-out it declares does not name itself.
- `reference/host-capabilities.md` — the one page inside `reference/` that is
  *excluded* from the carve-out, because it owns per-host translation: it tells
  a user which entrance their host offers, and a reader types what it says.

**Round 5, on why this is shaped the way it is.** Round 4 quoted two strings in
`bin/`. The repair fixed those two strings and then wrote a guard shaped around
them: `TOOLS = ("perry-state", "perry-lint")` — 2 of 14 — over an AST walk that
*discarded docstrings*. Every one of the nine Python tools prints
`__doc__.strip()` for `--help`, so the guard was blind to its own subject
matter, and blind entirely to the five `bash` tools, which have no AST at all.
`perry-state --help`, `perry-dispatch-limit --help` and
`perry-codex-preflight --help` all still greeted the user in the dead
vocabulary while 27 tests passed.

So the check here is **"can this string reach a terminal"**, and it is answered
by running the program, not by reading it:
`TestEveryShippedToolsHelpIsTypeable` executes `--help` on every tool in `bin/`,
discovers the list from the filesystem so a new tool is covered on the day it
lands, and is language-agnostic by construction.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
LANES = ("goals", "work", "decide")


def shipped_tools() -> list[Path]:
    """Every executable in `bin/`, discovered rather than listed.

    The round-4 guard hard-coded two tool names and went quiet on the other
    twelve. Reading the directory means a tool added tomorrow is covered
    tomorrow, and a tool that is renamed cannot fall out of the set silently.
    """
    return sorted(p for p in (PERRY_HOME / "bin").iterdir()
                  if p.is_file() and not p.name.startswith(".")
                  and p.suffix != ".md" and os.access(p, os.X_OK))

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


class TestEveryShippedToolsHelpIsTypeable(unittest.TestCase):
    """The check is "can this string reach a terminal", so it runs the program.

    Round 4 quoted two `bin/` strings; the repair fixed those two and guarded
    them with an AST walk over two tools that *discarded docstrings*. All nine
    Python tools print `__doc__.strip()` for `--help`, and five more tools are
    `bash`, which an AST walk cannot see at all. Three tools were still
    greeting the user in the withdrawn vocabulary with the suite green:

        $ python3 bin/perry-state --help
          - the standup ritual (`/perry`, `/pmo`, `/okr`, `/design`) reads `--json`
        $ bash bin/perry-dispatch-limit --help
        perry-dispatch-limit — track concurrent /pmo dispatch slots.
        $ bash bin/perry-codex-preflight --help
        perry-codex-preflight — verify codex CLI before /pmo dispatch.

    Executing `--help` is language-agnostic, cannot be fooled by *where* the
    string lives in the source, and needs no per-tool registration. `--help` is
    read-only in every tool here: each one matches the flag and exits before it
    touches the filesystem.
    """

    def test_the_tool_list_is_the_directory_and_not_a_stale_literal(self):
        """Guard against the guard, and against the exact defect being fixed.
        A hard-coded pair of names is how the last version of this passed while
        three tools printed dead commands."""
        tools = shipped_tools()
        self.assertGreaterEqual(
            len(tools), 14,
            f"only {len(tools)} executables found in bin/ — the discovery has "
            f"come unstuck from the tree")
        names = {p.name for p in tools}
        # One of each language, and the three that were actually wrong.
        for expected in ("perry-state", "perry-lint", "perry-task",
                         "perry-dispatch-limit", "perry-codex-preflight",
                         "perry-detect-host"):
            self.assertIn(expected, names)
        # The two languages must both be represented, because the previous
        # guard could only ever have seen one of them.
        shebangs = {p.read_text(errors="replace").splitlines()[0] for p in tools}
        self.assertTrue(any("python" in s for s in shebangs))
        self.assertTrue(any("bash" in s for s in shebangs))

    @staticmethod
    def help_text(path: Path) -> str:
        proc = subprocess.run([str(path), "--help"], capture_output=True,
                              text=True, timeout=60, cwd=str(PERRY_HOME))
        return proc.stdout + proc.stderr

    def test_no_tools_help_output_names_a_withdrawn_command(self):
        offenders = []
        for path in shipped_tools():
            text = self.help_text(path)
            for n, line in enumerate(text.splitlines(), 1):
                for hit in withdrawn_hits(line):
                    offenders.append(
                        f"`{path.name} --help` line {n} → {hit.strip()!r}\n"
                        f"      {line.strip()[:100]}")
                    break
        self.assertEqual(
            offenders, [],
            "a shipped tool greets the user in a vocabulary that no longer "
            "exists:\n    " + "\n    ".join(offenders))

    def test_the_tools_actually_produced_help_to_scan(self):
        """The other half of the anti-vacuity guard. A tool that crashed, hung
        or printed nothing on `--help` would pass the scan above by saying
        nothing, which is the failure mode this whole file exists to catch."""
        thin = []
        for path in shipped_tools():
            text = self.help_text(path)
            if len(text.strip()) < 40:
                thin.append(f"{path.name}: {len(text.strip())} chars")
        self.assertEqual(
            thin, [],
            "a tool produced no usable --help, so scanning it proved "
            "nothing:\n    " + "\n    ".join(thin))

    def test_the_scan_would_catch_the_strings_that_were_wrong(self):
        """The three real round-5 lines, replayed verbatim. A guard that does
        not go red on all three is not the guard this task owes."""
        replay = [
            "  - the standup ritual (`/perry`, `/pmo`, `/okr`, `/design`) "
            "reads `--json`",
            "perry-dispatch-limit — track concurrent /pmo dispatch slots.",
            "perry-codex-preflight — verify codex CLI before /pmo dispatch.",
        ]
        for line in replay:
            with self.subTest(line=line[:50]):
                self.assertNotEqual(withdrawn_hits(line), [])

    def test_the_scan_does_not_cry_wolf_on_the_live_forms(self):
        """The replacements, and the two shapes that legitimately contain a
        lane word: a JSON section key (`--section ... okr / design`) and a
        directory (`design/`). If the pattern reddened on these, the honest
        fix would look like a false alarm and get exempted."""
        for line in (
            "perry-dispatch-limit — track concurrent /perry work dispatch slots.",
            "  --section     emit one top-level key only (board / phase / okr "
            "/ design / …)",
            "`decide/SKILL.md § init` creates `design/` and states outright",
            "evidence/<YYYY-MM>/okr-v2-retro.md",
        ):
            with self.subTest(line=line[:50]):
                self.assertEqual(withdrawn_hits(line), [], line)


class TestBinPrintsOnlyLiveCommands(unittest.TestCase):
    """`bin/` output is the quote, already rendered.

    Reproduced by the reviewer with no mutation at all:

        $ python3 bin/perry-state --json --root tests/fixtures/sample-project
        warnings: ['ADR-002 sunset criteria passed 16d ago —
                   run /pmo decide --expire ADR-002.']

    `--help` is covered above by execution. This class covers the strings that
    execution cannot reach without contriving the conditions that emit them —
    `warnings[]`, `Finding.message`, error branches — by walking the source.

    Two things changed after round 4. The tool list is now **every** Python
    tool, not two of them; and the **module** docstring is no longer discarded,
    because every one of these tools prints it as `--help`. Docstrings on
    functions and classes are still skipped: those are never printed, and
    keeping them exempt is what lets a docstring explain the old vocabulary —
    as several in this repo do — without the explanation becoming an offence.
    """

    @staticmethod
    def python_tools() -> list[Path]:
        return [p for p in shipped_tools()
                if "python" in p.read_text(errors="replace").splitlines()[0]]

    def test_the_python_tool_set_is_the_whole_of_it(self):
        """Guard against the guard: `TOOLS = ("perry-state", "perry-lint")` is
        precisely the shape that let round 5's defect through."""
        names = {p.name for p in self.python_tools()}
        self.assertGreaterEqual(len(names), 9,
                                f"only {len(names)} Python tools seen: {names}")
        for expected in ("perry-state", "perry-lint", "perry-task",
                         "perry-diagnose", "perry-goals", "perry-decide"):
            self.assertIn(expected, names)

    @staticmethod
    def message_literals(path: Path) -> list[tuple[int, str]]:
        """Every string literal that is not a function or class docstring.

        The module docstring is deliberately **included** — `--help` prints it.
        """
        tree = ast.parse(path.read_text())
        skip = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                body = node.body
                if (body and isinstance(body[0], ast.Expr)
                        and isinstance(body[0].value, ast.Constant)
                        and isinstance(body[0].value.value, str)):
                    skip.add(id(body[0].value))
        out = []
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and id(node) not in skip):
                out.append((node.lineno, node.value))
        return out

    def test_the_module_docstring_is_no_longer_discarded(self):
        """Guard against the guard, pinned on the mechanism that failed. The
        round-4 walk skipped `ast.Module` docstrings alongside function ones;
        that single word in a tuple is what hid `perry-state --help`."""
        path = PERRY_HOME / "bin" / "perry-state"
        first = ast.parse(path.read_text()).body[0]
        assert isinstance(first, ast.Expr)
        seen = [v for _, v in self.message_literals(path)]
        self.assertIn(first.value.value, seen,
                      "the module docstring is being skipped again — the text "
                      "`--help` prints would go unscanned")

    def test_a_function_docstring_is_still_allowed_to_explain_the_old_names(self):
        """The complement. Narrowing the exemption to *module* docstrings is
        only correct if the narrower exemption still holds."""
        src = ('"""mod"""\n'
               'def f():\n'
               '    """Historically this was `/pmo triage`."""\n'
               '    return 1\n')
        tree = ast.parse(src)
        skip = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                skip.add(id(node.body[0].value))
        vals = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and id(n) not in skip]
        self.assertNotIn("Historically this was `/pmo triage`.", vals)

    def test_no_tool_puts_a_withdrawn_command_in_a_string_it_can_print(self):
        offenders = []
        for path in self.python_tools():
            for lineno, value in self.message_literals(path):
                for hit in withdrawn_hits(value):
                    offenders.append(
                        f"bin/{path.name}:{lineno} → {hit.strip()!r} in "
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


# A line may keep a withdrawn spelling only when it is *reporting the
# withdrawal* — "earlier versions symlinked them so `/okr` worked; that was
# withdrawn". Round 4's m-4 rejected the previous exemption for being every
# blockquote and every line containing the word; this one is a closed set of
# past-tense markers that must appear on the same line as the hit, so a line
# that instructs the reader can never qualify.
WITHDRAWAL_MARKER = re.compile(
    r"\b(?:was withdrawn|were withdrawn|used to|earlier versions|"
    r"are written in shorthand|no longer)\b", re.I)


class TestTheRouterAndTheInstallerAreTypeable(unittest.TestCase):
    """`SKILL.md` and `setup` are the two pages a *new* user reads.

    The carve-out `SKILL.md:41` declares does not name `SKILL.md` itself
    (round 4, m-1) and never named `setup`. `setup`'s completion banner printed
    two consecutive lines, one in each vocabulary, at the exact moment a user
    learns what to type:

        skill        : /perry  (one entrance; goals / work / decide are lanes …)
        lanes        : /perry okr … · /perry pmo … · /perry design … · …
    """

    FILES = ("SKILL.md", "setup")

    def offenders(self, rel: str) -> list[str]:
        out = []
        for n, line in enumerate(read(rel).splitlines(), 1):
            if not withdrawn_hits(line) or WITHDRAWAL_MARKER.search(line):
                continue
            out.append(f"{rel}:{n} → {line.strip()[:110]}")
        return out

    def test_neither_names_a_command_that_no_longer_exists(self):
        for rel in self.FILES:
            with self.subTest(doc=rel):
                bad = self.offenders(rel)
                self.assertEqual(
                    bad, [],
                    f"{rel} shows a withdrawn command without saying it is "
                    f"withdrawn:\n    " + "\n    ".join(bad))

    def test_the_setup_banner_names_the_three_live_lanes_and_no_others(self):
        """Pinned on the banner specifically. The scan above would also be
        satisfied by deleting the line."""
        banner = [l for l in read("setup").splitlines()
                  if "lanes        :" in l]
        self.assertEqual(len(banner), 1,
                         "the completion banner's lane line is gone — this "
                         "test would pass against nothing")
        line = banner[0]
        for lane in LANES:
            self.assertIn(f"/perry {lane}", line,
                          f"the install banner never names the `{lane}` lane "
                          f"in the form a user types")
        for dead in ALIASES:
            self.assertNotIn(f"/perry {dead}", line,
                             f"the install banner still advertises `{dead}`")

    def test_the_exemption_is_a_narrow_seam_and_not_a_loophole(self):
        """Guard against the guard. If the marker set ever grows wide enough to
        excuse an instruction, this file stops meaning anything — which is the
        criticism round 4 levelled at the previous blockquote exemption."""
        excused = [(rel, n, line.strip())
                   for rel in self.FILES
                   for n, line in enumerate(read(rel).splitlines(), 1)
                   if withdrawn_hits(line) and WITHDRAWAL_MARKER.search(line)]
        self.assertLessEqual(
            len(excused), 4,
            f"{len(excused)} lines are being excused as historical notes; the "
            f"exemption has become a way to keep dead commands: {excused}")
        # And it must not excuse an instruction that merely mentions history.
        self.assertFalse(
            WITHDRAWAL_MARKER.search("Run `/pmo triage` to sort the board."),
            "the marker set matches a plain instruction")
        self.assertTrue(
            WITHDRAWAL_MARKER.search(
                "Earlier versions symlinked them so `/okr` worked."),
            "the marker set no longer recognises a genuine historical note")


class TestHostCapabilitiesNamesTheOneLiveEntrance(unittest.TestCase):
    """`reference/host-capabilities.md` is the one page inside the carve-out's
    directories that is *excluded* from it.

    It is the single owner of per-host translation: its job is to tell a user
    which entrance their host offers. It documented Perry as four skills on
    both hosts, so a Codex user following row `Skill invocation` ran `/skills`,
    looked for `pmo`, and found nothing — the three sibling skills were
    withdrawn *and* the lanes were renamed. A page whose whole purpose is to be
    accurate about the host cannot be read as shorthand, so this class allows
    it no exemption at all, not even the historical-note seam above.
    """

    REL = "reference/host-capabilities.md"

    def test_the_page_uses_no_withdrawn_command_anywhere(self):
        bad = [f"{self.REL}:{n} → {line.strip()[:110]}"
               for n, line in enumerate(read(self.REL).splitlines(), 1)
               if withdrawn_hits(line)]
        self.assertEqual(
            bad, [],
            "the page that owns per-host translation is itself written in the "
            "dead vocabulary:\n    " + "\n    ".join(bad))

    def test_the_invocation_row_offers_one_skill_on_each_host(self):
        """The specific cell a Codex user acts on.

        The Codex column read `` `/skills` then pick perry/okr/pmo/design ``,
        and that shape is invisible to `WITHDRAWN`: its lookbehind rejects a
        name character before the slash, so in `perry/okr` the `/` is preceded
        by `y` and nothing matches. A slash-joined alias list is therefore the
        one spelling of this defect that only a row-level check can see —
        which is why the match here is a plain word boundary and not the
        module pattern.
        """
        rows = [l for l in read(self.REL).splitlines()
                if l.startswith("| Skill invocation")]
        self.assertEqual(len(rows), 1, "the Skill invocation row is gone — "
                                       "this test would prove nothing")
        row = rows[0]
        self.assertIn("/perry", row)
        self.assertIn("/skills", row, "the Codex column no longer tells the "
                                      "user how to reach Perry at all")
        for dead in ALIASES:
            self.assertNotRegex(
                row, rf"\b{dead}\b",
                f"the invocation row still sends a user looking for a "
                f"`{dead}` entry that no host registers")

    def test_the_row_check_sees_the_slash_joined_list_the_module_pattern_misses(self):
        """Guard against the guard, on the exact seam above. If this ever
        stops holding, the Codex column can regress in silence."""
        codex_column = "`/skills` then pick perry/okr/pmo/design, or `$perry`"
        self.assertEqual(
            withdrawn_hits(codex_column), [],
            "the module pattern now catches the slash-joined list, so the "
            "reason this class carries its own matcher no longer holds")
        self.assertRegex(codex_column, r"\bpmo\b")

    def test_the_page_states_that_perry_registers_exactly_one_skill(self):
        """The prose half of the same claim. Row-level correctness without it
        leaves `All four Perry skills …` standing two lines above."""
        text = read(self.REL)
        self.assertNotRegex(
            text, r"[Aa]ll four Perry skills",
            "the page still asserts Perry registers four skills")
        self.assertRegex(
            text, r"registers \*\*one\*\* skill",
            "the page never states how many skills Perry actually registers")

    def test_it_names_the_lane_directories_that_exist(self):
        """`§ $PERRY_HOME` listed `okr/`, `pmo/`, `design/` as the directories
        on disk. Checked against the filesystem, not a literal."""
        text = read(self.REL)
        for lane in LANES:
            self.assertIn(f"`{lane}/`", text,
                          f"the $PERRY_HOME section does not name `{lane}/`")
            self.assertTrue((PERRY_HOME / lane).is_dir())
        for dead in ALIASES:
            self.assertFalse(
                (PERRY_HOME / dead).exists(),
                f"`{dead}/` exists again — this test is now checking nothing")


class TestTheCarveOutSaysWhatThisFileEnforces(unittest.TestCase):
    """The round-4 review's m-6: the carve-out silently omitted `bin/`,
    `*/state/`, the shared root `reference/`, `packs/`, `setup` and the router
    — which is where every finding lived — while this file's own docstring
    claimed four covered classes and covered two and a half.

    A guard that misdescribes its own coverage is worse than no guard, because
    the next reviewer trusts it. So the two documents are pinned to each other:
    `SKILL.md`'s carve-out note must name every class this file exempts *and*
    every class it enforces, and it must name them as the same lists.
    """

    @staticmethod
    def carve_out() -> str:
        text = read("SKILL.md")
        start = text.index("**Reading the lane docs**")
        return text[start:start + 2500]

    def test_the_carve_out_names_every_directory_it_exempts(self):
        note = self.carve_out()
        for exempt in ("`*/reference/`", "`packs/`"):
            self.assertIn(exempt, note,
                          f"the carve-out does not say it covers {exempt}, so "
                          f"~30 occurrences there are exempt by accident")
        self.assertIn("reference/", note)

    def test_the_carve_out_names_every_class_this_file_enforces(self):
        """Each of these has a test class above. If a class is added here
        without being declared there, the carve-out is over-claiming again."""
        note = self.carve_out()
        for enforced in ("`bin/`", "`setup`", "description:", "SKILL.md",
                         "reference/host-capabilities.md", "_TEMPLATE.md"):
            self.assertIn(
                enforced, note,
                f"the carve-out note never says {enforced} is outside it, "
                f"which is how it silently grew the last time")

    def test_the_carve_out_points_at_this_file(self):
        self.assertIn("tests/test_shipped_vocabulary.py", self.carve_out(),
                      "the prose list names no mechanical counterpart")

    def test_the_exempted_directories_really_do_still_contain_shorthand(self):
        """Guard against the guard, in the honest direction. The carve-out is
        only load-bearing while those trees actually use the shorthand; if they
        were cleaned up, keeping the exemption would hide a future regression
        and this test says so."""
        found = 0
        for base in ("packs", "reference"):
            for p in sorted((PERRY_HOME / base).rglob("*.md")):
                if p.name == "host-capabilities.md":
                    continue
                found += len([l for l in p.read_text().splitlines()
                              if withdrawn_hits(l)])
        self.assertGreater(
            found, 0,
            "`packs/` and the shared root `reference/` no longer contain any "
            "shorthand, so the carve-out that exempts them is dead weight — "
            "drop it from SKILL.md and enforce them here instead")


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
                         "hook_TEMPLATE.md",
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

    def test_no_decide_template_attributes_its_file_to_pmo(self):
        """The decision record moved to `decide` under the signed hand-off
        contract, and one of the relocated templates kept a header asserting
        that the lane forbidden to write it maintains it — a header that lands
        in the user's repo.

        **That template was `DECISIONS_TEMPLATE.md` and TASK-235 deleted it
        with the file it seeded.** The assertion is now over every template
        this lane still ships, which is what it should have been: the defect
        was a stale attribution in a `decide/state/` header, not a property of
        one filename. `ADR_TEMPLATE.md` and `design_TEMPLATE.md` are inside it
        today and a fourth is covered on the day it is added.
        """
        templates = sorted((PERRY_HOME / "decide" / "state").glob("*.md"))
        self.assertGreaterEqual(len(templates), 2,
                                "the decide lane's state templates moved; "
                                "this glob is now vacuous")
        for path in templates:
            with self.subTest(template=path.name):
                text = "\n".join(path.read_text().splitlines()[:6])
                self.assertNotRegex(
                    text, r"\bPMO\b",
                    f"{path.name} credits PMO with maintaining a file the "
                    f"contract gave to `decide`")


class TestLaneFrontmatterDescribesALaneNotACommand(unittest.TestCase):
    """Deliverable 4 covered `name:` and `description:`. Only `name:` landed.

    Beyond the letter of it: the old text asserted that `/okr`, `/pmo` and
    `/design` are commands a user invokes and that `pmo` and `okr` are skills.
    `SKILL.md § One skill, three lanes` states both are false — Perry registers
    exactly one skill and the lanes are read on demand, not invoked.
    """

    @staticmethod
    def frontmatter(lane: str) -> str:
        text = (PERRY_HOME / lane / "SKILL.md").read_text()
        m = re.search(r"^---\n(.*?)\n---", text, re.S)
        assert m, f"{lane}/SKILL.md has no frontmatter"
        return m.group(1)

    @classmethod
    def description(cls, lane: str) -> str:
        d = re.search(r"^description:\s*(.*)$", cls.frontmatter(lane), re.M)
        assert d, f"{lane}/SKILL.md declares no description"
        return d.group(1)

    def test_every_frontmatter_name_is_the_live_lane_name(self):
        for lane in LANES:
            with self.subTest(lane=lane):
                match = re.search(
                    r"^name:\s*(\S+)\s*$", self.frontmatter(lane), re.M)
                self.assertIsNotNone(
                    match, f"{lane}/SKILL.md declares no frontmatter name")
                self.assertEqual(
                    match.group(1), lane,
                    f"{lane}/SKILL.md still registers the retired "
                    f"`{match.group(1)}` lane name")

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


class TestStartupRootDescriptionsNameLiveLaneDirectories(unittest.TestCase):
    """Filesystem inventories are facts, not lane-document shorthand.

    The carve-out still permits commands such as `/pmo triage` inside lane
    instructions. This guard is deliberately narrower: it checks only the
    startup lines that tell an agent how to identify `$PERRY_HOME` on disk.
    """

    DESCRIPTIONS = {
        "SKILL.md": "**Set `$PERRY_HOME`**",
        "goals/SKILL.md": "**Set `$PERRY_HOME`**",
        "work/SKILL.md": "**Set `$PERRY_HOME`**",
        "decide/SKILL.md": "**Set `$PERRY_HOME`**",
        "reference/host-capabilities.md": "The Perry root contains",
    }

    def root_description(self, rel: str, marker: str) -> str:
        matches = [line for line in read(rel).splitlines() if marker in line]
        self.assertEqual(
            len(matches), 1,
            f"{rel} has {len(matches)} startup root descriptions; expected one")
        return matches[0]

    def test_startup_root_descriptions_name_no_retired_lane_directory(self):
        for rel, marker in self.DESCRIPTIONS.items():
            line = self.root_description(rel, marker)
            for retired in ALIASES:
                with self.subTest(rel=rel, retired=retired):
                    self.assertNotIn(
                        f"`{retired}/`", line,
                        f"{rel} describes the live Perry root with the retired "
                        f"`{retired}/` lane directory")

    def test_explicit_root_inventories_name_all_live_lane_directories(self):
        for rel, marker in self.DESCRIPTIONS.items():
            line = self.root_description(rel, marker)
            if "contains" not in line:
                continue
            for lane in LANES:
                with self.subTest(rel=rel, lane=lane):
                    self.assertIn(
                        f"`{lane}/`", line,
                        f"{rel} inventories `$PERRY_HOME` without `{lane}/`")


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
    # shorthand `/pmo <sub>` — a subcommand can be declared in a lane's
    # reference table rather than in its index, and both count as declared.
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
                         ("work", "handoff"), ("decide", "adr"),
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

    def test_both_readmes_reflect_that_migration_was_removed(self):
        """ADR-011 removed the migrator; the front door must not promise it."""
        for doc in self.READMES:
            with self.subTest(doc=doc):
                text = read(doc)
                self.assertIn(
                    "ADR-011-the-representation-layer-comes-out.md", text,
                    f"{doc} never cites the decision that removed migration")
                self.assertIn("/perry adopt", text)
                self.assertIn("TASK-261", text)
                self.assertNotIn("Adoption writes Perry's own state", text)
                self.assertNotIn("adopt 写出 Perry 自己的状态", text)

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
        cited = "ADR-011-the-representation-layer-comes-out.md"
        for doc in self.READMES:
            self.assertIn(cited, read(doc))
        adr = PERRY_HOME / "perry" / "decisions" / cited
        self.assertTrue(adr.is_file())
        self.assertRegex(adr.read_text(),
                         re.compile(r"^>\s*Status:\s*active", re.M))

    def test_a_superseded_migration_adr_points_to_an_active_replacement(self):
        adr = PERRY_HOME / "perry" / "decisions" / "ADR-004-mandatory-migration.md"
        self.assertTrue(adr.is_file())
        text = adr.read_text()
        replacement = re.search(r"Superseded by:\s*(ADR-\d+)\b", text)
        if replacement is None:
            return
        matches = list((PERRY_HOME / "perry" / "decisions").glob(
            f"{replacement.group(1)}-*.md"))
        self.assertEqual(len(matches), 1,
                         "a superseded ADR has no unique successor record")
        self.assertRegex(matches[0].read_text(),
                         re.compile(r"^>\s*Status:\s*active", re.M))




class TestTheTwoListsCoverTheTree(unittest.TestCase):
    """**Nothing checked that exempt ∪ enforced is the whole tree.**

    `TestTheCarveOutSaysWhatThisFileEnforces` pins the two lists to each other,
    so neither can grow without the other. It cannot see a path in **neither**
    — and that is how a whole directory falls out.

    A V4 round partitioned the seventeen top-level paths and found `viewer/` in
    neither list: `viewer/README.md:19-22` told non-technical users to run
    `/pmo viewer`, `/pmo browse` and `/pmo viewer stop` and called it "the
    recommended path", and `viewer/templates/architecture.html` printed
    `/pmo architecture init` into the page every project sees before
    `architecture init` is run. The spec's out-of-scope named only `README.md`,
    `README_cn.md` and `INSTALL.md`.

    **Those files are gone** — TASK-178 deleted the web viewer, and what is left
    under `viewer/` is `parsers.py` and `tables.py`, which ship no prose a user
    reads. The finding is history; the partition it produced is not, and this
    is that partition, asserted. A new top-level directory of shipped
    documentation lands in neither list by default, and by default that is
    now a failure.
    """

    #: Paths that ship no user-facing prose at all. Each needs a REASON, not a
    #: place on a list — a bare list is what let `viewer/` disappear.
    NOT_DOCUMENTATION = {
        "tests": "the suite; never shipped to a user",
        "schema": "machine-readable contracts; no prose an agent renders",
        ".git": "not shipped",
        ".claude": "not shipped",
        ".github": "CI configuration",
        "perry": "this project's own state, not the skill",
    }

    def test_every_shipped_top_level_path_is_in_one_list_or_the_other(self):
        """The carve-out is READ, not restated.

        My first version of this test hardcoded the exempt set and reported
        `bin`, `packs`, `reference`, `state` and `templates` — every one of
        them named in `SKILL.md`'s carve-out prose, which I had not read. That
        is the hardcoded-list defect this very file exists to prevent,
        committed inside the test written to prevent it.
        """
        note = TestTheCarveOutSaysWhatThisFileEnforces.carve_out()
        # Anything the carve-out names by path is exempt, whatever its shape:
        # `bin/`, `*/state/*_TEMPLATE.md`, `packs/`, `reference/`, `setup`.
        exempt = {m.strip("`/*").split("/")[0]
                  for m in re.findall(r"`([^`]+)`", note)}
        enforced = {"work", "goals", "decide", "modes", "SKILL.md", "AGENTS.md",
                    "README.md", "README_cn.md", "INSTALL.md"}
        uncovered = []
        for p in sorted(PERRY_HOME.iterdir()):
            name = p.name
            if name.startswith(".") or name in self.NOT_DOCUMENTATION:
                continue
            if p.is_file() and p.suffix not in (".md",):
                continue
            if name in exempt or name in enforced:
                continue
            if p.is_dir() and not any(p.rglob("*.md")) \
                    and not any(p.rglob("*.html")):
                continue
            uncovered.append(name)
        self.assertEqual(
            uncovered, [],
            f"in neither the carve-out nor the enforced set: {uncovered}. "
            f"A path that ships prose and is on no list is enforced by nothing "
            f"and exempted by nobody — say which it is.")


if __name__ == "__main__":
    unittest.main()
