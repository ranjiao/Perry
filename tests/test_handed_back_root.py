#!/usr/bin/env python3
r"""**A command Perry hands a reader, that WRITES, names the project it is
about.**  (TASK-253.)

The harm, as the row states it: *Perry prints a command and a reader runs it
against a project Perry never named.*  The row was opened on `bin/perry-migrate
§ _plan_task_store`, which printed `perry-tasks render --write` in a refusal
while holding `plan.project_root` two lines above and not passing it.  A reader
who copies that runs it against whatever project their cwd happens to resolve
to, and it rewrites that project's `BOARD.md`.

`perry-migrate` was deleted by USER-910.  **The shape survived the deletion**,
and so did the apparatus built to catch it: `tests/sweep_handed_back_commands.py`
(round 4/5 of TASK-234) and `tests/handed_back.py` were both driven by
`tests/test_conformance.py` and `tests/test_migrate.py`, which went with the
tools.  Neither was run by anything when this row was picked up.  This module
is the rule wired back into the suite, and it imports the sweep's AST reader
rather than restating it.

Re-measured on `220f73d3`: **126 command phrases across `bin/`, 87 of which
name a writer, 65 of those paste-able — and 63 of the 65 carried no root.**

## The three questions, and why each is answered the way it is

**1. What is the population?**  Every file under `bin/` that Python can parse,
discovered by parsing it.  Not a list of file names: `bin/` holds nineteen
Python tools and four `bash` ones today, the bash four are skipped because
`ast.parse` refuses them rather than because anybody wrote them down, and a
twentieth tool is in the population the day it is added.  A guard that
hard-codes what it should discover is a shape this repository has paid for more
than once.

**2. Which subcommands WRITE?**  Two derivations, and the point of having both
is that they check each other.  `SURFACE["subcommands"][i]["writes"]` is the
tool's own statement (DESIGN-016 decision 5) and is authoritative where it
exists — four tools today.  For the tools DESIGN-016 has not reached, the
answer is taken from the `COMMANDS = {...}` dispatch table and a walk of the
module's own call graph to a filesystem write.  The second is an
approximation and `test_the_two_derivations_agree_where_both_exist` measures
exactly how bad it is rather than assuming it is good: on `perry-task`, where
both answers exist, five of thirty disagree and every one of the five is a
shape named there.

**3. Is the phrase something a reader can PASTE?**  This is the line the rule
is drawn on, and it is drawn there rather than at "is it an instruction"
because the second question is about English and this code makes no judgements
about English.

    `perry-tasks render --write`          paste-able.  Run from the wrong
                                          directory it rewrites the wrong
                                          project's BOARD.md, silently.
    `perry-task stage <ID> --stage <name>` not paste-able.  The reader has to
                                          fill in two metavariables, and what
                                          they are being handed is the SHAPE of
                                          the vector they already typed — which
                                          carried their own `--root`.

Rooting the second kind would teach a longer contract than the subcommand has
and would make the usage line harder to read, so the rule stops at the first.
**The limit that leaves is stated rather than discovered later**: a reader who
completes `perry-task cadence-done <id> --evidence <path>` and runs it from the
wrong directory suffers the same harm, and nothing here catches that.

## Judgement that is NOT made by code

Five phrases name a writer, are paste-able, and are still not hand-backs: the
message is talking ABOUT the command rather than handing it over.  They are
listed in `MENTIONS` with the sentence that makes each one a mention, in the
shape `tests/test_bin_surface.py § INDIRECT` uses — an entry that stops
matching anything is itself a failure, so the table cannot rot into a blanket.
"""
from __future__ import annotations

import ast
import importlib.machinery
import importlib.util
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import handed_back
import sweep_handed_back_commands as sweep

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
sys.path.insert(0, str(ROOT / "bin"))
sys.path.insert(0, str(ROOT / "viewer"))
import lib  # noqa: E402


# ── what a command phrase looks like ──────────────────────────────────────
#
# Deliberately looser than `sweep_handed_back_commands § CUE`, and that is the
# point.  The sweep rules a phrase an instruction from the words immediately
# before it — `run` / `with` / `is` / `try` / `use`, or an indented line — and
# EIGHT of `bin/perry-lint`'s hand-backs are introduced by neither: *"so a hand
# edit is drift: `perry-tasks render --write` puts the file back in line"*.
# The word before the backtick is "drift".  So this reads every phrase and
# decides on what the phrase IS, not on how it was introduced.

#: A metavariable — `<id>`, `<ID>`, `<row number>`, `<dropped|deferred>`. Text
#: the READER substitutes, which is what makes a phrase un-paste-able.
META = r"<[A-Za-z][A-Za-z0-9 _|-]*>"
#: One token of a command.  `{...}` interpolations may be GLUED to the word
#: around them — `{key}-write`, `prioritize{root_flag}` — and `[...]` is an
#: optional argument as a usage block spells it, read as part of the phrase so
#: that a usage line naming `--root` is seen to name it.
_TOK = (r"(?:\{[^{}]*\}|\[[^\][]*\]|[A-Za-z0-9][A-Za-z0-9./_-]*"
        r"|-[A-Za-z0-9][A-Za-z0-9._-]*|" + META + r")")
_ARG = r"(?:--?[a-z][a-z0-9-]*|" + _TOK + r"+)"
#: What the reader has to finish before the line is a command: a metavariable,
#: or the `…` this codebase writes where a value goes (`--reason "…"`).
CONTINUES = re.compile(r"^\s*(?:<|[\"'`]?…|\.\.\.)")
#: The root, in every spelling `lib.root_flag` reaches the template through:
#: inline, through the `r` / `_r` local the longer messages assign, through a
#: `root_flag` parameter threaded into a helper that has no project of its own,
#: and literally, in a usage block.
ROOTED = re.compile(r"\{_?r\}|\{[A-Za-z_.]*root_flag[^{}]*\}|--root")

#: Calls that put bytes on disk.  Not a list of Perry's writers — a list of
#: what writing is, so the derivation below is about the code rather than about
#: a table somebody maintained.
WRITE_CALLS = frozenset({
    "write_atomic", "write_text", "write_bytes", "writelines", "mkdir",
    "replace", "rename", "unlink", "touch", "rmtree", "copy", "copy2",
    "copyfile", "makedirs", "remove"})

DISPATCH = re.compile(r"(?<![A-Z_])COMMANDS\s*=\s*\{(.*?)\}", re.S)
ENTRY = re.compile(r'"([a-z][a-z0-9-]*)"\s*:\s*([A-Za-z_][A-Za-z0-9_]*|None)')


# ── the five that are mentions ────────────────────────────────────────────
#
# Keyed on (file, phrase) rather than on a line number, so moving the code does
# not silently retire an exemption.  Each value is the sentence the phrase sits
# in, which is the evidence for the ruling: read it and the ruling is either
# obvious or wrong.  `test_every_mention_still_names_something` fails on an
# entry that matches nothing, so a stale one cannot quietly widen the rule.
MENTIONS = {
    ("bin/perry-lint", "perry-goals link"):
        "“`perry-goals link` appends an edge and never retracts one” — what "
        "the tool does, said to explain why the reader cannot simply undo the "
        "edge. Nothing is being handed over.",
    ("bin/perry-lint", "perry-goals link --unlinked"):
        "“several ids were passed to `perry-goals link --unlinked` as one "
        "argument — the shape that put 48 of them on one line here on "
        "2026-08-28.” Past tense: the command is the CAUSE being reported.",
    ("bin/perry-lint", "perry-task risk-add"):
        "“It is the fix whenever `perry-task risk-add` / `risk-clear` wrote "
        "the value — the ordinary case.” Provenance of the drift, not the "
        "remedy for it; the remedy is `risks-render --write` in the same "
        "sentence, and that one carries the root.",
    ("bin/perry-lint", "perry-task resolve-intake {n + 1}"):
        "“an inserted or deleted line renumbers every row beneath it, so "
        "`perry-task resolve-intake {n + 1}` no longer addresses what it "
        "did.” The sentence's whole content is that this command is WRONG "
        "now. Rooting it would dress a warning up as an instruction.",
    ("bin/perry-task", "perry-task next"):
        "“put the explanation in --reason or `perry-task next`, and name the "
        "handle here” — `next` names the FIELD the prose belongs in. There is "
        "no line to copy: the phrase has neither an id nor a value.",
}

#: How many paste-able writer phrases `bin/` holds. **This number is the
#: guard.** An eighteenth writer hand-back — a new refusal, a new register, a
#: tool converted to `SURFACE` so its subcommands start declaring `writes` —
#: changes it, and the failure names the site. Measured on `220f73d3`, where 63
#: of these 65 carried no root; the two that did are `bin/perry_md_store §
#: USAGE`, which has always spelled `[--root <p>]` in its own help block.
#:
#: **66 from TASK-236**: `bin/perry-goals § overall_kr_model` refuses `krs
#: --level overall` on a project with no `okr.jsonl` and hands back
#: `perry-okr write --from-file` as the way to mint one. It was written
#: without a root and this guard is what caught it, which is the eighteenth
#: case the note above predicted.
PASTEABLE_WRITER_PHRASES = 66


def _load(path: Path):
    spec = importlib.util.spec_from_loader(
        f"pt_{path.name.replace('-', '_')}",
        importlib.machinery.SourceFileLoader(
            f"pt_{path.name.replace('-', '_')}", str(path)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _called(node: ast.Call) -> str | None:
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    return f.attr if isinstance(f, ast.Attribute) else None


def _opens_for_writing(node: ast.Call) -> bool:
    if _called(node) != "open":
        return False
    modes = list(node.args[1:2]) + [k.value for k in node.keywords
                                    if k.arg == "mode"]
    return any(isinstance(a, ast.Constant) and isinstance(a.value, str)
               and set("wax+") & set(a.value) for a in modes)


def reaches_a_write(fn, funcs, seen=None, depth=0) -> bool:
    """Can this handler put bytes on disk? Its own body, then what it calls.

    Six levels, because `bin/perry-task`'s writers reach `commit` through two
    or three hops and stopping shorter reported half of them as readers. It
    over-approximates in one direction and under-approximates in the other —
    `cell_writer` builds a handler as a closure no walk can see — and
    `test_the_two_derivations_agree_where_both_exist` is where that is
    measured rather than hoped about.
    """
    if fn is None or depth > 6:
        return False
    seen = set() if seen is None else seen
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        name = _called(node)
        if name in WRITE_CALLS or _opens_for_writing(node):
            return True
        if name in funcs and name not in seen:
            seen.add(name)
            if reaches_a_write(funcs[name], funcs, seen, depth + 1):
                return True
    return False


def declared_writes(path: Path) -> dict | None:
    """`{subcommand: writes?}` from the tool's own `SURFACE`, or `None`."""
    src = path.read_text(encoding="utf-8")
    if "SURFACE" not in src:
        return None
    try:
        face = getattr(_load(path), "SURFACE", None)
    except Exception:                                   # pragma: no cover
        return None
    if not isinstance(face, dict):
        return None
    return {s["name"]: bool(s.get("writes"))
            for s in face.get("subcommands", ())}


def reached_writes(path: Path) -> dict:
    """`{subcommand: writes?}` from the dispatch table and the call graph."""
    src = path.read_text(encoding="utf-8")
    table = DISPATCH.search(src)
    if not table:
        return {}
    tree = _parse(path)
    funcs = {n.name: n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return {sub: reaches_a_write(funcs.get(handler), funcs)
            for sub, handler in ENTRY.findall(table.group(1))}


def write_table() -> tuple[dict, dict]:
    """`{(tool, subcommand): writes?}`, and `{(tool, flag): takes a value?}`.

    The declaration wins where there is one; the call graph fills in the rest.
    """
    writes, valued = {}, {}
    for path in sorted(BIN.glob("perry-*")):
        if path.suffix == ".py":
            continue
        face_writes = declared_writes(path)
        if face_writes is not None:
            writes.update({(path.name, k): v for k, v in face_writes.items()})
            try:
                face = getattr(_load(path), "SURFACE", {})
            except Exception:                           # pragma: no cover
                face = {}
            for flag in (face or {}).get("flags", ()):
                valued[(path.name, flag["name"])] = bool(flag.get("arg"))
        for sub, does in reached_writes(path).items():
            writes.setdefault((path.name, sub), does)
    return writes, valued


def _parse(path: Path):
    """`ast.parse`, without `bin/`'s own `DeprecationWarning`s on this
    module's output. Two files in the tree carry `"\\w"` in a non-raw string;
    re-parsing them here would print a warning per test that nothing in this
    module is about, on a line number that means nothing to the reader."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        warnings.simplefilter("ignore", SyntaxWarning)
        return ast.parse(path.read_text(encoding="utf-8"))


def python_files() -> list[Path]:
    """**The population, discovered.** Every file under `bin/` that parses as
    Python — which is what makes the four `bash` tools absent by measurement
    rather than by a list somebody has to remember to update."""
    out = []
    for path in sorted(BIN.rglob("*")):
        if (not path.is_file() or "__pycache__" in path.parts
                or path.suffix in (".md", ".json", ".pyc")):
            continue
        try:
            _parse(path)
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        out.append(path)
    return out


def tool_aliases(tree) -> set[str]:
    """Names this module binds to a literal starting `perry-`.

    `bin/perry_md_store.py` is one body serving several front ends and spells
    every command it hands back `{tool} render --write`. `tool` is admitted as
    a head not because of its name but because the module assigns it
    `f"perry-{doc.name}"`, which is read off the AST here.
    """
    out = set()
    for node in ast.walk(tree):
        targets = (node.targets if isinstance(node, ast.Assign) else
                   [node.target] if isinstance(node, ast.AnnAssign) else [])
        value = getattr(node, "value", None)
        text = sweep.render(value) if value is not None else None
        if not text or not text.startswith("perry-"):
            continue
        out.update(t.id for t in targets if isinstance(t, ast.Name))
    return out


def phrase_pattern(aliases: set[str]) -> re.Pattern:
    heads = "|".join(["perry-[a-z][a-z-]*"]
                     + [r"\{" + re.escape(a) + r"\}" for a in sorted(aliases)])
    return re.compile(r"(?<![\w-])((?:" + heads + r")(?:[ ]" + _ARG + r")+)")


def command_phrases() -> list[dict]:
    """Every `perry-<tool> <arg>…` in a message `bin/` can print."""
    writes, valued = write_table()
    rows = []
    for path in python_files():
        tree = _parse(path)
        pattern = phrase_pattern(tool_aliases(tree))
        rel = str(path.relative_to(ROOT))
        # `sweep.string_expressions` is the half worth importing rather than
        # rewriting: it skips docstrings, reassembles `+` and implicit
        # concatenation into ONE template, and renders each `{expr}` as
        # itself, so a command split across four source lines is one phrase.
        for lineno, text, _named, _value in sweep.string_expressions(tree):
            for m in pattern.finditer(text):
                phrase = m.group(1).rstrip(".,;")
                tail = text[m.end():]
                tokens = phrase.split()
                sub = tokens[1] if len(tokens) > 1 else ""
                # An interpolation inside a subcommand is judged over
                # everything it can expand to. Two shapes need this and they
                # pull opposite ways: `prioritize{root_flag}` is the fix
                # itself — without expansion, rooting a site would take it out
                # of the population and the held count would fall by one per
                # fix — and `{key}-write` is one message serving three
                # registers, all of which write. A writer iff something
                # matches and everything that matches writes.
                expands = re.compile("^" + "".join(
                    "[A-Za-z0-9._-]*" if part.startswith("{")
                    else re.escape(part)
                    for part in re.split(r"(\{[^{}]*\})", sub) if part) + "$")
                candidates = [v for (tool, name), v in writes.items()
                              if (tokens[0].startswith("{")
                                  or tool == tokens[0]) and expands.match(name)]
                rows.append({
                    "file": rel, "line": lineno, "phrase": phrase,
                    "writes": bool(candidates) and all(candidates),
                    "pasteable": not (re.search(META, phrase)
                                      or CONTINUES.match(tail)
                                      or valued.get((tokens[0], tokens[-1]),
                                                    False)),
                    # The ruling is made over the phrase and the rest of its
                    # line, stopping at the next backtick or newline — where a
                    # command ENDS in each of the two shapes this tree uses.
                    # Reading further would let a `--root` elsewhere in the
                    # same message vouch for a phrase that has none.
                    "rooted": bool(ROOTED.search(
                        phrase + re.split(r"[`\n]", tail, 1)[0])),
                })
    return rows


class TestThePopulationIsDiscovered(unittest.TestCase):
    """Nothing below means anything if the set it ranges over is a list."""

    def test_every_python_tool_in_bin_is_read(self):
        found = {p.name for p in python_files()}
        # Not an exhaustive list — an assertion that discovery actually
        # reaches the big four, which between them hold most of the hand-backs
        # and are the files a regression would land in.
        for name in ("perry-task", "perry-tasks", "perry-lint",
                     "perry_md_store.py"):
            self.assertIn(name, found, f"{name} is not in the population, so "
                                       f"nothing below asserts anything about "
                                       f"it")

    def test_the_bash_tools_are_absent_by_measurement(self):
        """They are skipped because `ast.parse` refuses them, not because
        anyone wrote them down — which is why a fifth one would be skipped too
        and a twentieth Python tool would be read."""
        found = {p.name for p in python_files()}
        bash = [p for p in BIN.glob("perry-*")
                if p.is_file() and p.name not in found]
        self.assertTrue(bash, "every tool parses as Python — this test is now "
                              "vacuous and the skip path is unmeasured")
        for path in bash:
            self.assertIn("bash", path.read_text(errors="replace")[:64],
                          f"{path.name} is not Python and not bash either; it "
                          f"is being skipped for a reason nobody has checked")

    def test_the_phrase_reader_sees_the_shapes_the_cue_rule_misses(self):
        """The recall this module exists for, stated as a case.

        `bin/perry-lint § check_store_drift` introduces its remedy with the
        word "drift", so `sweep § CUE` reads it as a mention and did not see
        any of `perry-lint`'s eight.
        """
        rows = [r for r in command_phrases()
                if r["file"] == "bin/perry-lint" and r["writes"]]
        self.assertGreaterEqual(
            len(rows), 8,
            "the reader has stopped seeing perry-lint's hand-backs, which is "
            "the exact blind spot this module was written to close")


class TestWhichSubcommandsWrite(unittest.TestCase):

    def test_the_two_derivations_agree_where_both_exist(self):
        """**Measured, not assumed.** `perry-task` declares a `SURFACE` and
        also has a dispatch table, so both answers exist for all thirty of its
        subcommands. Five disagree, and each of the five is one of two named
        shapes — so the approximation used for the UNDECLARED tools is a known
        quantity rather than a hope."""
        declared = declared_writes(BIN / "perry-task")
        reached = reached_writes(BIN / "perry-task")
        self.assertEqual(len(declared), 30)
        disagree = {k for k in declared if declared[k] != reached.get(k)}
        self.assertEqual(
            disagree,
            # `cell_writer(field, flag, …)` builds these three as closures, so
            # there is no function body for the walk to enter: under-reported.
            {"evidence", "retitle", "rung"}
            # These two reach a write through a helper they share with the
            # writers and do not perform one: over-reported.
            | {"list", "next"},
            "the call-graph derivation's error set has changed. It is the only "
            "answer available for perry-goals, perry-decide and "
            "perry-knowledge, so a change here is a change in what this "
            "module can claim about those three")

    def test_the_declaration_is_preferred_where_there_is_one(self):
        writes, _valued = write_table()
        self.assertFalse(writes[("perry-task", "list")],
                         "`list` reaches a write through a shared helper and "
                         "declares none; the declaration has to win")
        self.assertTrue(writes[("perry-task", "rung")],
                        "`rung` is a cell_writer closure the walk cannot "
                        "enter; the declaration has to win")


class TestEveryWriterHandBackCarriesTheRoot(unittest.TestCase):
    """The rule."""

    def test_no_pasteable_writer_is_handed_back_without_the_root(self):
        missing = [r for r in command_phrases()
                   if r["writes"] and r["pasteable"] and not r["rooted"]
                   and (r["file"], r["phrase"]) not in MENTIONS]
        self.assertEqual(
            [], [f"{r['file']}:{r['line']} {r['phrase']!r}" for r in missing],
            "each of these prints a command that WRITES and does not say "
            "which project it writes to. A reader who copies one runs it "
            "against whatever their cwd resolves to — reproduced on 220f73d3: "
            "`perry-tasks write --from-board`, copied out of a refusal about "
            "project A, wrote project B's tasks.jsonl and exited 0. Append "
            "`{lib.root_flag(<the project root the caller gave>)}` inside the "
            "backticks. If the phrase is a MENTION rather than a hand-back, "
            "say so in MENTIONS above with the sentence that makes it one.")

    def test_the_count_of_pasteable_writer_hand_backs_is_held(self):
        """**So an eighteenth cannot appear unnoticed.**

        The rule above is satisfied by a phrase this module stopped
        recognising, which is how a guard over a derived population dies
        quietly. The count is the other half: it moves when a hand-back is
        added, and it moves when the reader breaks.
        """
        rows = [r for r in command_phrases() if r["writes"] and r["pasteable"]]
        self.assertEqual(
            PASTEABLE_WRITER_PHRASES, len(rows),
            "the number of paste-able writer command phrases in bin/ has "
            "changed. If you added one, it must carry the root and this "
            "number goes up. If it went DOWN, check that the phrase reader "
            "above still sees the shape you wrote — a rule that ranges over "
            "nothing passes.\n  "
            + "\n  ".join(f"{r['file']}:{r['line']} {r['phrase']!r}"
                          for r in sorted(rows, key=lambda r: (r["file"],
                                                               r["line"]))))

    def test_every_mention_still_names_something(self):
        """An exemption that matches nothing is a hole with no edge."""
        seen = {(r["file"], r["phrase"]) for r in command_phrases()
                if r["writes"] and r["pasteable"]}
        stale = sorted(k for k in MENTIONS if k not in seen)
        self.assertEqual(
            [], stale,
            "these MENTIONS entries match no phrase in bin/ any more. Either "
            "the message was rewritten — delete the entry — or the phrase "
            "reader stopped seeing it, in which case the entry is now "
            "excusing nothing and hiding that fact")

    def test_the_five_mentions_are_the_only_exemptions(self):
        self.assertEqual(
            5, len(MENTIONS),
            "MENTIONS is the judgement this module does NOT make in code. It "
            "is meant to stay small enough to read; growing it is how a rule "
            "becomes a suggestion")


#: Call sites that pass a helper NO root flag, with the reason there is none.
#: `bin/perry-lint --templates` lints the templates Perry itself ships, out of
#: `PERRY_HOME`; there is no project in that branch to name and the findings
#: are about this repository rather than about anybody's board.
#: **The key is a LINE NUMBER, and both branches that landed today moved it.**
#: TASK-431 measured 5525 against its tree, TASK-419 measured 5604 against its
#: own, and on the merged tree neither is right, because each carries the
#: other's edits above the call as well. The number below was re-derived here,
#: on the merge. The call itself has not changed through any of this — it is
#: `check_file`'s `--templates` branch, which has no project root to name.
#:
#: **Three times in one day now.** Two independent agents hit it, and then a
#: five-line docstring correction in `bin/perry-lint` -- TASK-340, fixing a
#: citation of a tool deleted with USER-910 -- moved the call 5634 -> 5642 and
#: reddened this module, which has nothing to do with any of it. The call has
#: not changed once through all three.
#:
#: That is the argument for re-keying it by something stable: the enclosing
#: function plus the callee, the way `test_claims` does. Recorded here rather
#: than fixed, because re-keying is a change to how this module identifies a
#: call site and belongs in a round of its own.
#: **Keyed by LINE NUMBER, and that is a known cost** (noted by TASK-379,
#: 2026-09-12). The declaration is about one call site — `check_file` on a
#: TEMPLATE, where there is no project root to name — but the key is its
#: coordinate, so it stops matching whenever anything ABOVE it in
#: `bin/perry-lint` grows or shrinks. It moved 5642 -> 5714 when TASK-379
#: added three findings to `check_reviews`, ~70 lines higher up, and this
#: module went red for a change that touched neither the call nor the
#: template. Same class as `TASK-404` and as `TASK-431`'s "keyed by function
#: not line": a test that reddens when the file moves rather than when the
#: code breaks. Re-keying it on the enclosing function is a row of its own.
#:
#: **It bit a SECOND time the same day**, 5714 -> 5778, when TASK-370 scoped
#: two findings in `check_specs`. Two unrelated rows, both red on a coordinate
#: rather than on a behaviour, inside one session. The pin is re-dated again
#: and the recurrence is recorded here rather than filed, per this board's
#: standing rule; what it costs is one full suite run per occurrence.
NO_ROOT_TO_GIVE = {("bin/perry-lint", "check_file", 5778)}


class TestTheFlagReachesTheTemplateThatNamesIt(unittest.TestCase):
    """**A template can name the flag while its caller passes nothing**, and
    every rule above stays green while the printed line drops the root again.

    Found by mutation: `require_migrated(ctx["board"])` — the second argument
    removed, the default `""` taken — leaves `perry-task risk-migrate{root_flag}`
    in the source, so the AST rules see a rooted hand-back and the reader gets
    an un-rooted one. It is `tests/fixtures/handed_back_spellings.py §
    spelling_18_the_choke_point_itself` arrived at from the other end: there
    the choke point interpolated raw, here it is never called.

    So every helper that threads a `root_flag` through is checked at its call
    sites, not at its definition.

    **A SECOND mutation came back green after the first version of this class
    and is why `str.format` is here too.** `bin/perry-tasks §
    RISK_SECTION_UNIMPORTABLE` is a module constant with no project to name,
    so its three branches are `str.format` templates and the root goes in at
    the one call site: `.format(r=lib.root_flag(root))`. Mutated to
    `.format(r="")`, every rule above stayed green — the template still spells
    `{r}` and no function signature is involved at all. A rule that reads only
    function parameters cannot see a template field.
    """

    def _helpers(self):
        """`{path: {function name: index of its root_flag parameter}}`."""
        out = {}
        for path in python_files():
            tree = _parse(path)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef,
                                         ast.AsyncFunctionDef)):
                    continue
                names = [a.arg for a in node.args.posonlyargs + node.args.args]
                if "root_flag" in names:
                    out.setdefault(str(path.relative_to(ROOT)), {})[
                        node.name] = names.index("root_flag")
                elif any(a.arg == "root_flag" for a in node.args.kwonlyargs):
                    out.setdefault(str(path.relative_to(ROOT)), {})[
                        node.name] = None
        return out

    def test_there_are_helpers_threading_the_flag(self):
        self.assertTrue(self._helpers(), "no helper takes a root_flag any "
                                         "more, so the test below ranges over "
                                         "nothing and passes for free")

    @staticmethod
    def _from_the_choke_point(tree, expr, threading: bool) -> bool:
        """Does this argument come from `lib.root_flag`?

        Three spellings, and each is a real one in this tree rather than a
        concession:

        * the call itself, `lib.root_flag(project_root)`;
        * a local the same module binds to it — the longer messages assign
          `r = lib.root_flag(root)` once and interpolate it four times, and
          demanding the call at the call site would be a rule about house
          style rather than about where the value came from;
        * the enclosing function's OWN `root_flag`, passed onward.
          `bin/perry-task § register_change` is handed a state root and no
          project, so it threads what `commit` gave it down to
          `refuse_to_shrink`. That hop is safe because this same rule checks
          `register_change`'s call sites — the chain is verified link by link
          rather than trusted end to end.
        """
        source = ast.unparse(expr) if expr is not None else ""
        if "root_flag(" in source:
            return True
        if not isinstance(expr, ast.Name):
            return False
        if expr.id == "root_flag" and threading:
            return True
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == expr.id
                            for t in node.targets)
                    and "root_flag(" in ast.unparse(node.value)):
                return True
        return False

    def test_every_format_field_that_holds_the_root_is_given_one(self):
        """`"…{r}…".format(r=…)` — the same hole through `str.format`."""
        bare = []
        for path in python_files():
            tree = _parse(path)
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "format"):
                    continue
                for kw in node.keywords:
                    if kw.arg not in ("r", "root_flag"):
                        continue
                    if self._from_the_choke_point(tree, kw.value, False):
                        continue
                    bare.append(f"{path.relative_to(ROOT)}:{node.lineno} "
                                f".format({kw.arg}={ast.unparse(kw.value)})")
        self.assertEqual(
            [], bare,
            "a template field named for the root is being filled with "
            "something that did not come from `lib.root_flag`. The template "
            "still spells the field, so the phrase reads as rooted in the "
            "source and prints without a root")

    def test_every_call_to_one_of_them_passes_a_real_flag(self):
        helpers = self._helpers()
        wanted = {name: at for table in helpers.values()
                  for name, at in table.items()}
        bare = []
        for path in python_files():
            rel = str(path.relative_to(ROOT))
            tree = _parse(path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = _called(node)
                if name not in wanted:
                    continue
                at = wanted[name]
                given = next((k.value for k in node.keywords
                              if k.arg == "root_flag"), None)
                if given is None and at is not None and len(node.args) > at:
                    given = node.args[at]
                # `threading` is true only when the CALLER itself declares a
                # `root_flag` parameter, so `root_flag` passed onward is the
                # one its own call sites were checked for — and a local that
                # merely happens to be named `root_flag` is not.
                inside = next((f for f in ast.walk(tree)
                               if isinstance(f, (ast.FunctionDef,
                                                 ast.AsyncFunctionDef))
                               and f.lineno <= node.lineno <= f.end_lineno
                               and "root_flag" in [
                                   a.arg for a in f.args.posonlyargs
                                   + f.args.args + f.args.kwonlyargs]), None)
                if not self._from_the_choke_point(tree, given,
                                                  inside is not None):
                    if (rel, name, node.lineno) in NO_ROOT_TO_GIVE:
                        continue
                    source = ast.unparse(given) if given is not None else ""
                    bare.append(f"{rel}:{node.lineno} {name}(…) — "
                                f"root_flag={source or '(not passed)'}")
        self.assertEqual(
            [], bare,
            "these call a helper that interpolates a root into a command it "
            "hands the reader, and give it nothing. The template still names "
            "the flag, so every static rule in this module stays green while "
            "the printed line drops the root. Pass "
            "`lib.root_flag(<the caller's project root>)`, or declare the "
            "call in NO_ROOT_TO_GIVE with the reason there is no project "
            "there to name.")


class TestTheFlagIsShellSafe(unittest.TestCase):
    """`lib.root_flag` is the one place the root is spelled, so this is the one
    place the round-4 V4 FAIL `tests/handed_back.py` records can come back."""

    def test_a_hostile_root_survives_the_shell(self):
        flag = lib.root_flag(handed_back.HOSTILE_ROOT_NAME)
        argv = shlex.split(f"perry-tasks render --write{flag}")
        self.assertEqual(argv[:3], ["perry-tasks", "render", "--write"])
        self.assertEqual(argv[3], "--root")
        self.assertEqual(argv[4], handed_back.HOSTILE_ROOT_NAME)
        self.assertEqual(len(argv), 5, f"{argv!r} — the root split into "
                                       f"several arguments, which is the "
                                       f"round-4 FAIL exactly")

    def test_no_root_prints_what_it_printed_before(self):
        """The leading space belongs to the value, so a tool with nothing to
        name adds nothing rather than a dangling flag."""
        self.assertEqual("", lib.root_flag(None))
        self.assertEqual("", lib.root_flag(""))

    def test_the_flag_really_goes_through_shlex_quote(self):
        """A MUTATION check, and it is not decoration: an implementation that
        returned `f' --root {root}'` passes every assertion above on a root
        with no metacharacters in it, which is every root a
        `TemporaryDirectory` produces."""
        self.assertEqual(f" --root {shlex.quote('/a b')}",
                         lib.root_flag("/a b"))
        self.assertNotEqual(" --root /a b", lib.root_flag("/a b"))


class TestTheCommandTheRefusalNamesIsTheOneTheReaderCanRun(unittest.TestCase):
    """The other side of the AST rules: what a real run PRINTS.

    A template can be right at every site the static half sees and still
    produce a line nobody can run, which is what TASK-234 round 4 shipped. So
    one refusal is provoked for real, against a project whose directory name
    carries every character that changes how a shell reads a line, and the
    command is taken out of the OUTPUT — by `tests/handed_back.py`, the
    extractor that reads text rather than a list the test also wrote.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        # `.resolve()`, because `lib.resolve_project_root` does — and on
        # macOS `tempfile` hands out `/var/…`, which is a symlink to
        # `/private/var/…`. The two name one directory; the printed command
        # names the resolved one deliberately, so that a reader who re-runs it
        # from anywhere reaches the same project. A RELATIVE root echoed back
        # would not, which is the hazard `tests/run § step 0a` refuses to
        # start under.
        cls.project = (Path(cls.tmp.name) /
                       handed_back.HOSTILE_ROOT_NAME).resolve()
        src = ROOT / "tests" / "fixtures" / "sample-project"
        subprocess.run(["cp", "-R", str(src), str(cls.project)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _refusal(self) -> str:
        out = subprocess.run(
            [sys.executable, str(BIN / "perry-tasks"), "write",
             "--root", str(self.project)],
            capture_output=True, text=True, cwd=str(ROOT))
        return out.stdout + out.stderr

    def test_every_command_the_refusal_names_carries_this_root(self):
        handed_back.assert_every_command_carries(
            self, self._refusal(), self.project,
            "perry-tasks refusing a board-to-store import")

    def test_the_command_it_hands_back_runs_and_acts_on_THAT_project(self):
        """Copied out of the output, run through `/bin/sh -c` from a directory
        that is not the project, and then asked what it touched.

        On `220f73d3` the same command line was `perry-tasks write
        --from-board` with no root: run from here it writes the store of
        whatever project `tests/` sits in, reports success, and leaves the
        project the reader actually named untouched.
        """
        named = handed_back.commands_named(self._refusal())
        wanted = [c for c in named if "--from-board" in c]
        self.assertTrue(wanted, f"the refusal named {named!r} and none of them "
                                f"is the import it is telling the reader to "
                                f"run — the extractor or the message moved")
        argv = shlex.split(wanted[0])
        self.assertEqual(argv[0], "perry-tasks")
        store = self.project / "tasks.jsonl"
        self.assertFalse(store.exists())
        elsewhere = Path(self.tmp.name) / "not the project"
        elsewhere.mkdir()
        # Through `/bin/sh -c`, because `shlex.split` does not glob and a shell
        # does, and the root's name carries a `*`.
        line = wanted[0].replace("perry-tasks", shlex.quote(
            f"{sys.executable} {BIN / 'perry-tasks'}").strip("'"), 1)
        done = subprocess.run(["/bin/sh", "-c", line], capture_output=True,
                              text=True, cwd=str(elsewhere))
        self.assertEqual(0, done.returncode,
                         f"the command Perry handed back does not run:\n"
                         f"{line}\n{done.stdout}{done.stderr}")
        self.assertTrue(
            store.exists(),
            f"the handed-back command exited 0 and wrote nothing to the "
            f"project the refusal was about:\n{done.stdout}{done.stderr}")
        self.assertEqual([], sorted(p.name for p in elsewhere.iterdir()),
                         "it wrote into the directory it was RUN from")


class TestEveryToolAMessageNamesStillExists(unittest.TestCase):
    """A refusal that names a deleted tool is worse than one that names no root.

    `bin/perry-task § Board.find_section_row` ended *"Add the column, or run
    `perry-migrate` and then `perry-conform declare` for this file"*. USER-910
    deleted both tools with `perry_schema.py` and `test_migrate.py`. A rootless
    hand-back at least RUNS — it acts on the wrong project, which is TASK-253's
    harm. A hand-back naming a tool that does not exist cannot be followed at
    all, so the reader is left in exactly the state the message was written to
    get them out of.

    An AST sweep found that one line and no other, which is why this guard is
    cheap to add now and expensive to add later: it costs nothing today and
    catches the next tool deletion on the day it happens.

    **The population is derived at both ends.** The tools come from reading
    `bin/`, and the names come from `command_phrases()`, so deleting a tool
    reddens this without anyone remembering to update a list.
    """

    @classmethod
    def setUpClass(cls):
        cls.phrases = command_phrases()
        cls.present = {p.name for p in (ROOT / "bin").iterdir()
                       if p.is_file() and not p.name.startswith(".")
                       and p.suffix != ".md"}

    def test_the_sweep_found_something_to_check(self):
        """The control: an empty sweep would make every case below vacuous."""
        self.assertGreater(len(self.phrases), 50, "the phrase reader went quiet")
        self.assertIn("perry-task", self.present)

    def test_no_message_names_a_tool_that_is_not_in_bin(self):
        for row in self.phrases:
            tool = row["phrase"].split()[0]
            # An interpolated head — `{tool} render --write` — expands to
            # whichever register is being served, and those are checked by
            # their own aliases elsewhere. A literal name is checked here.
            if "{" in tool:
                continue
            with self.subTest(at=f"{row['file']}:{row['line']}", tool=tool):
                self.assertIn(
                    tool, self.present,
                    f"{row['file']}:{row['line']} tells the reader to run "
                    f"`{row['phrase']}` and bin/ has no {tool}")

    #: A tool named on its own, with no subcommand after it. `command_phrases`
    #: cannot see these — its pattern requires at least one argument — and the
    #: hole was found by mutating this very guard: putting back a bare
    #: `` `perry-migrate` `` left it green, and only the two-word form bit.
    #:
    #: Two shapes look like a bare tool and are not, so both are excluded by
    #: construction rather than by a list: a CONTRACT id (`perry-roles/list/1.1`
    #: — followed by `/`) and a FILENAME (`.perry-task-transaction.json` —
    #: preceded by a dot). Measured 2026-09-11: those four were the only
    #: matches in `bin/`, and with them excluded the sweep is clean.
    BARE = re.compile(r"(?<![\w.-])(perry-[a-z][a-z-]*)(?![\w-])(?!/)")

    def test_no_message_names_a_tool_on_its_own_that_is_not_in_bin(self):
        """The half `command_phrases` cannot reach.

        Naming a tool that does not exist is wrong in any grammar — as an
        instruction it cannot be followed, and as prose it sends a reader
        looking for something that is not there.
        """
        seen = 0
        for path in sorted((ROOT / "bin").glob("*")):
            if not path.is_file() or path.suffix == ".md":
                continue
            try:
                tree = ast.parse(path.read_text(errors="replace"))
            except SyntaxError:
                continue          # the bash tools, absent by measurement
            for lineno, text, _n, _v in sweep.string_expressions(tree):
                for m in self.BARE.finditer(text):
                    seen += 1
                    with self.subTest(at=f"{path.name}:{lineno}",
                                      tool=m.group(1)):
                        self.assertIn(
                            m.group(1), self.present,
                            f"{path.name}:{lineno} names {m.group(1)} and "
                            f"bin/ has no such tool")
        self.assertGreater(seen, 20, "the bare-name sweep went quiet")

    def test_the_two_tools_that_caused_this_are_really_gone(self):
        """If either comes back, the guard above stops being about anything and
        this says so rather than passing quietly."""
        for tool in ("perry-migrate", "perry-conform"):
            with self.subTest(tool=tool):
                self.assertNotIn(tool, self.present)


if __name__ == "__main__":
    unittest.main()
