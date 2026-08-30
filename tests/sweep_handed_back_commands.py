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

    python3 tests/sweep_handed_back_commands.py [--all] <file> [...]

Exit 1 if any handed-back command lacks the root.  `--all` lists every phrase
with its ruling, so the ruling itself can be audited rather than trusted.

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


def string_expressions(tree) -> list[tuple[int, str]]:
    """Every maximal non-docstring string expression, once each, as
    `(line, text, assigned_to_a_command_name)`."""
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
        out.append((node.lineno, text, id(node) in assigned))
    return sorted(out)


def sites(path: str):
    """`(path, line, phrase, carries_root_or_None_if_a_mention)`."""
    with open(path) as fh:
        tree = ast.parse(fh.read())
    for lineno, text, is_command in string_expressions(tree):
        for m in CMD.finditer(text):
            phrase = (m.group(0) + TAIL.match(text, m.end()).group(0)).rstrip()
            if not (is_command or CUE.search(text[:m.start()])):
                yield path, lineno, phrase, None
            else:
                yield path, lineno, phrase, bool(ROOT.search(phrase))


def main(argv: list[str]) -> int:
    show_all = "--all" in argv
    handed = mentions = bad = 0
    for f in [a for a in argv if not a.startswith("-")]:
        for path, lineno, phrase, ok in sites(f):
            if ok is None:
                mentions += 1
                if show_all:
                    print(f"mention {path}:{lineno}: {phrase!r}")
                continue
            handed += 1
            bad += not ok
            if show_all or not ok:
                print(f"{'ok     ' if ok else 'MISSING'} "
                      f"{path}:{lineno}: {phrase!r}")
    print(f"\n{handed} handed-back command(s), {mentions} mention(s); "
          f"{bad} handed back without the caller's root")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
