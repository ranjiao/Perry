#!/usr/bin/env python3
"""Does every message that HANDS THE READER A COMMAND name it with the root
the reader used?  (TASK-234 round 4.)

The class this sweeps for, stated as the defect that produced it:

    `bin/perry-conform § message_for` propagates the invocation's `--root`
    into every branch through `_root_flag()`.  `migrate_record`'s two refusals
    did not.  A reader routed there by `perry-conform migrate --root $PROJ`,
    who copied the command they were handed, got `rc=0` and *"nothing to
    convert — `.perry/conformance.jsonl` is already this project's record (or
    it has none)"* — about whatever project they were standing in, while their
    own record sat unconverted and still gating every write.  Not an error: a
    success-shaped silence, which is the worst thing a refusal whose whole job
    is to hand back a working command can do.

`bin/perry-conform`'s members are pinned by
`tests/test_conformance.py § test_no_refusal_in_perry_conform_names_a_command
_without_the_root`, which runs this same rule as part of the suite.  This
script is the sweep over the WIDER tree, where the remaining members are and
where they are recorded rather than fixed (`TASK-234-result.md § 10.9`).

**Round 5 adds the second half of the class.**  Round 4 asked only *does the
phrase carry the root*.  The round-4 V4 FAIL carried it — and spelled it
`--root /Users/ada/My Project`, which the reader cannot run.  So a handed-back
command is now also read for HOW its arguments got there: every `{...}` inside
one has to be a spelling that is shell-safe by construction (`_q(...)`,
`_root_flag(...)`, `shlex.quote(...)`, or the `r` those produce), and a raw
`{v.path}` or `{root_arg}` is reported as `UNQUOTED`.

That rule cannot see the round-4 defect at its ORIGIN, because `_root_flag`'s
own body is `f" --root {root_arg}"` and contains no tool name for `CMD` to
match.  `FLAG_VALUE` is the rule for that: a long flag whose value is
interpolated raw, in any non-docstring template, command phrase or not.

    python3 tests/sweep_handed_back_commands.py [--all] <file> [...]

Exit 1 if any handed-back command lacks the root or interpolates a value raw.
`--all` lists every phrase with its ruling, so the ruling itself can be
audited rather than trusted.

**Read off the AST, not by grepping.**  A comment or docstring discussing this
very defect is not a finding, and a message assembled from implicit or `+`
concatenation is one string, not three.  Each `{expr}` is rendered as itself so
`{r}` and `{_root_flag(root_arg)}` are visible in the template.

**The blind spot, stated rather than left to be discovered.**  The ruling is
made from the text immediately before the phrase, so a command built somewhere
with no cue and interpolated into a message far away is read as a mention.  One
such site exists today — `bin/perry-migrate § rollback_message`, which assigns
to `cmd` — and `NAMED_AS_COMMAND` catches that shape by the variable's name.
A third shape (built into a name that says nothing, e.g. `s = "perry-x …"`)
would still be missed; there is none in this tree, checked by
`grep -rn 'cmd = f\?"perry-\|command = f\?"perry-' bin/ viewer/`, and a sweep
that claimed otherwise would be claiming more than it measures.
"""
from __future__ import annotations

import ast
import re
import sys

#: Perry's tools, by name. A command phrase starts at one of these.
TOOLS = ("conform", "lint", "migrate", "task", "tasks", "goals", "state",
         "decide", "diagnose", "explain", "okr", "config", "knowledge")
CMD = re.compile(r"perry-(?:" + "|".join(TOOLS) + r")\b")
#: the rest of the phrase, to the closing backtick or the end of the line.
TAIL = re.compile(r"[^`\n'\"]*")
ROOT = re.compile(r"\{r\}|\{_root_flag\([^)]*\)\}|--root")
#: Every `{...}` in a template, so each can be judged on its own.
INTERP = re.compile(r"\{([^{}]*)\}")
#: **The spellings that are shell-safe by construction.**  `_q` is
#: `shlex.quote`; `_root_flag` is built out of `_q`; `r` is what a message
#: assigns `_root_flag(root_arg)` to, by convention in both tools.  Anything
#: else interpolated into a command a reader is told to copy is a raw value,
#: and a raw value with a space in it is the round-4 FAIL.
SAFE_INTERP = re.compile(
    r"^(?:r|_q\(.*\)|_root_flag\(.*\)|(?:shlex\.)?quote\(.*\))$")
#: A long flag whose VALUE is interpolated raw — `--root {root_arg}`.  Read
#: over every template, not only over command phrases, because the choke point
#: itself names no tool: this is the rule that would have caught round 4 in
#: `_root_flag`'s own two lines.
FLAG_VALUE = re.compile(r"--[a-z][a-z-]+[= ]\{([^{}]*)\}")
#: **What makes a phrase an instruction rather than a mention**, checked
#: against the text IMMEDIATELY before it — through at most one backtick, so
#: "is not what `perry-conform declare` would have written" is a mention (the
#: word before the backtick is "what") while "the findings is `perry-lint{r}`"
#: is an instruction.
CUE = re.compile(r"(?:(?:^|\n)[ ]{2,}|\b(?:run|with|is|try|use)[ :]+`?)$",
                 re.IGNORECASE)
#: A command can also be BUILT first and interpolated into the message later —
#: `bin/perry-migrate § rollback_message` does exactly that. The name is the
#: cue there: a string assigned to `cmd` / `command` is the command, wherever
#: it is printed.
NAMED_AS_COMMAND = re.compile(r"(?i)(^|_)(cmd|command)s?($|_)")
#: **A literal that IS a command is a command, wherever it is used.**  Round
#: 4's recall was 10 of 15 planted spellings and every one of the five misses
#: was the same shape: the command reached the message through a NAME — a
#: module constant, a local, a dict value, a helper's return — so there was no
#: cue word in front of it to read.  There is no cue to read because there is
#: no sentence: the string is the whole command and nothing else.  That is
#: itself the signal.
#:
#: So: a literal that is a tool name followed by nothing but argument-shaped
#: tokens, and by at least one of them.  A BARE tool name is excluded — a
#: literal that is only `perry-task` is a value or an identifier far more often
#: than an instruction — and so is anything carrying prose punctuation, which
#: is what separates `"perry-conform migrate"` from
#: `"perry-conform: refused — {exc}"`.
_ARG = r"(?:--?[a-z][a-z0-9-]*|[a-z][a-z0-9./-]*|<[a-z][a-z-]*>|\{[^{}]*\})"
IS_WHOLLY_A_COMMAND = re.compile(
    r"^\s*perry-(?:" + "|".join(TOOLS) + r")(?:[ ]" + _ARG + r")+\s*$")


def _is_str(node) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def render(node) -> str | None:
    """The template text of a string expression, or `None` if it is not one."""
    if _is_str(node):
        return node.value
    if isinstance(node, ast.JoinedStr):
        out = []
        for v in node.values:
            if _is_str(v):
                out.append(v.value)
            else:
                # Quotes inside an interpolation are not phrase terminators:
                # `{applied['run']}` is one placeholder, not the end of the
                # command. Neutralised so `TAIL` reads the phrase whole.
                expr = ast.unparse(v.value).replace("'", "ʼ").replace('"', "ʼ")
                out.append("{" + expr + "}")
        return "".join(out)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = render(node.left), render(node.right)
        return None if left is None or right is None else left + right
    return None


def string_expressions(tree) -> list[tuple[int, str, bool, bool]]:
    """Every maximal non-docstring string expression, once each, as
    `(line, text, assigned_to_a_command_name, is_a_named_value)`.

    **`is_a_named_value`** is what keeps `IS_WHOLLY_A_COMMAND` honest. A
    literal that is a keyword argument's value or a parameter's default is a
    VALUE — `writer="perry-conform declare"` records which tool wrote a
    declaration — and it is spelled exactly like a command because it is the
    name of one. Nothing prints it as an instruction, so it is not one.
    """
    named_value = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.value is not None:
            named_value.add(id(node.value))
        if isinstance(node, ast.arguments):
            for d in list(node.defaults) + list(node.kw_defaults):
                if d is not None:
                    named_value.add(id(d))
    assigned = set()
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            targets = [node.target]
        if any(isinstance(t, ast.Name) and NAMED_AS_COMMAND.search(t.id)
               for t in targets) and node.value is not None:
            assigned.add(id(node.value))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(getattr(node, "body", None), list):
            for stmt in node.body:
                if isinstance(stmt, ast.Expr) and _is_str(stmt.value):
                    docstrings.add(id(stmt.value))
    covered, out = set(), []
    for node in ast.walk(tree):
        if id(node) in covered or id(node) in docstrings:
            continue
        text = render(node)
        if text is None:
            continue
        for sub in ast.walk(node):
            covered.add(id(sub))
        out.append((node.lineno, text, id(node) in assigned,
                    id(node) in named_value))
    return sorted(out)


def raw_interpolations(phrase: str) -> list[str]:
    """The `{...}` inside `phrase` that are NOT shell-safe by construction."""
    return [e for e in INTERP.findall(phrase) if not SAFE_INTERP.match(e.strip())]


def sites(path: str):
    """`(path, line, phrase, problems)`.

    `problems` is `None` for a mention — a phrase naming a tool rather than
    handing one over — and otherwise a list of what is wrong with the command,
    empty when nothing is. Two rulings live in that list:

    * `no root` — the round-3 defect. The reader copies it and it acts on
      whatever project they are standing in.
    * `unquoted {expr}` — the round-4 defect. The root is there and the phrase
      is not a command line, because a value with a space in it was
      interpolated raw.
    """
    with open(path) as fh:
        tree = ast.parse(fh.read())
    for lineno, text, is_command, is_value in string_expressions(tree):
        # **The choke point itself.** `f" --root {root_arg}"` names no tool, so
        # no phrase rule below can reach it; it is where round 4's FAIL lived.
        for expr in FLAG_VALUE.findall(text):
            if not SAFE_INTERP.match(expr.strip()):
                yield path, lineno, text.strip(), [f"unquoted {{{expr}}}"]
        for m in CMD.finditer(text):
            phrase = (m.group(0) + TAIL.match(text, m.end()).group(0)).rstrip()
            handed = (is_command or CUE.search(text[:m.start()])
                      or (not is_value and IS_WHOLLY_A_COMMAND.match(text)))
            if not handed:
                yield path, lineno, phrase, None
                continue
            problems = [] if ROOT.search(phrase) else ["no root"]
            problems += [f"unquoted {{{e}}}" for e in raw_interpolations(phrase)]
            yield path, lineno, phrase, problems


def main(argv: list[str]) -> int:
    show_all = "--all" in argv
    handed = mentions = rootless = unquoted = 0
    for f in [a for a in argv if not a.startswith("-")]:
        for path, lineno, phrase, problems in sites(f):
            if problems is None:
                mentions += 1
                if show_all:
                    print(f"mention  {path}:{lineno}: {phrase!r}")
                continue
            handed += 1
            rootless += "no root" in problems
            unquoted += any(p.startswith("unquoted") for p in problems)
            if show_all or problems:
                tag = ("ok      " if not problems
                       else "MISSING " if "no root" in problems
                       else "UNQUOTED")
                note = f"   — {', '.join(problems)}" if problems else ""
                print(f"{tag} {path}:{lineno}: {phrase!r}{note}")
    print(f"\n{handed} handed-back command(s), {mentions} mention(s); "
          f"{rootless} handed back without the caller's root, "
          f"{unquoted} interpolating a value raw")
    return 1 if rootless or unquoted else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
