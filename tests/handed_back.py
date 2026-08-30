#!/usr/bin/env python3
"""**One definition of "the command a refusal hands back", for the tests that
assert about one.**  (TASK-234 round 5.)

`tests/test_conformance.py` and `tests/test_migrate.py` both assert that a
message hands the reader a command they can run.  They held two copies of the
rule — an extractor and a substring assertion in one, a hand-written
`assertIn(f"… --root {root}")` in the other — and the second copy is the one
that went stale: the round-4 V4 FAIL was invisible to BOTH of them, because
both asked whether the text `--root <root>` was present and neither asked
whether the phrase was a command line.

The rule lives here so there is one of it.  `tests/sweep_handed_back_commands.py`
is the other half — this module reads what a message PRINTED, that one reads
what the source can print — and they are deliberately separate: a message can
be right at every site the sweep sees and still be unusable, which is exactly
what round 4 shipped.
"""
from __future__ import annotations

import re
import shlex

#: **The directory name every fixture project is built under.**
#:
#: The round-4 FAIL was `_root_flag` interpolating the root into a handed-back
#: command unquoted.  The row's own end-to-end proof already took the command
#: out of the message and ran `shlex.split` on it — the exact parser that
#: exposes the defect — and stayed green, because
#: `tempfile.TemporaryDirectory()` never yields a path with a space in it.
#: One character in a fixture was the difference between a proof and a ritual.
#:
#: So the name carries every character that changes how a shell reads a line:
#:
#:   ` `     word splitting — the measured defect
#:   `(` `)` `;` `&`   metacharacters: pasted bare, the line is a syntax error
#:           or a backgrounded fragment, not the command
#:   `'` `"` the quoting characters `shlex.quote` itself has to escape
#:   `$`     parameter expansion.  `$x`, not `$HOME`: an accidental expansion
#:           should produce nothing, not the developer's home directory
#:   `#`     comment — truncates the line from where it appears
#:   `*`     globbing, which `shlex.split` does NOT perform and a shell does,
#:           which is why the end-to-end proof also runs the command under
#:           `/bin/sh -c`
#:
#: **Two characters are deliberately absent, and they are limitations rather
#: than oversights.**  A newline cannot be handed back on a single line at all
#: and every extractor here is line-based.  A backtick is what this codebase
#: delimits an inline command with, so a root containing one truncates the
#: backticked shape below — quoted correctly and extracted wrongly.  Both are
#: measured in `tests/test_conformance.py §
#: TestTheCommandTheRefusalNamesIsTheOneTheReaderCanRun` and stated in
#: `TASK-234-result.md`, rather than left for the next reviewer to find.
HOSTILE_ROOT_NAME = "My Project (v2) & 'draft' \"q\" $x; echo hi #1 *"

#: An indented line of its own.  **Two spaces, not four** — which is what
#: `tests/sweep_handed_back_commands.py § CUE` has always required, while this
#: extractor required four.  The two rules are supposed to be the same rule
#: seen from the source side and the output side, and they disagreed:
#: `bin/perry-migrate § do_restore` prints its listing's command under THREE
#: spaces, so the sweep called it a handed-back command and this extractor did
#: not see it at all.  A test asserting over an empty extraction is a test
#: asserting nothing, which is how `test_every_way_back_this_tool_names_
#: carries_the_root` came to assert a substring instead.
_INDENTED = re.compile(r"^[ ]{2,}(perry-[a-z][a-z-]*(?:[ ][^\n]*)?)$",
                       re.MULTILINE)
#: A backticked span introduced by a cue word — `run`, `with`, `is`, `try`,
#: `use` — and the same span WITHOUT backticks, which is how the line under a
#: finished run reads: `undo with: perry-migrate restore <id> --root X`.  The
#: two branches are disjoint: one requires a backtick after the cue, the other
#: requires the command itself there, so prose like "is not what
#: `perry-conform declare` would have written" matches neither (the word after
#: `is` is "not").
_CUED = re.compile(
    r"\b(?:run|with|is|try|use)[ :]+(?:`(perry-[^`\n]+)`|(perry-[a-z][a-z-]*[^\n`]*))",
    re.IGNORECASE)


def commands_named(message: str) -> list[str]:
    """The commands a refusal hands back, extracted from the TEXT.

    Not from a list the test also wrote: the whole defect this closes was an
    assertion that constructed what it expected and so could not see what was
    printed. Only the two shapes this codebase uses to hand back a command are
    read — an indented line of its own, and a backticked span after `run` /
    `with` / `is` — so prose that merely NAMES a tool ("`perry-conform declare`
    would have written") is not mistaken for an instruction.
    """
    out = [m.group(1).strip() for m in _INDENTED.finditer(message)]
    for m in _CUED.finditer(message):
        out.append((m.group(1) or m.group(2)).strip())
    return out


def assert_every_command_carries(case, message: str, root, why: str) -> None:
    """**A refusal that names a command must name it with the root the caller
    used, in a spelling the reader can copy.** This is the class, not the
    instance.

    `perry-conform` propagates the invocation's `--root` into every branch of
    `message_for` through `_root_flag()`, and did not into either refusal in
    `migrate_record`. The consequence is worse than a command that errors: the
    dropped-root command exits 0 and reports "nothing to convert — already
    this project's record", about a project the reader never asked about,
    while their own record stays unconverted and keeps gating every write.

    **Round 4 fixed that and this assertion still could not see the next
    register down.** It read `assertIn(f"--root {root}", cmd)`, a substring
    test, which is satisfied by `--root /home/ada/My Project` — a line that
    parses as five arguments and exits 1 with a usage error about a file the
    reader never named. So the phrase is PARSED here, not searched.
    """
    named = commands_named(message)
    case.assertTrue(named,
                    f"{why}: no command was found in the refusal, so this "
                    f"assertion is vacuous — the extractor or the message "
                    f"changed shape:\n{message}")
    for cmd in named:
        # `shlex.split` is the parser `/bin/sh` agrees with on word splitting
        # and quoting, so a phrase that does not survive it is not a command,
        # whatever it looks like.
        try:
            argv = shlex.split(cmd)
        except ValueError as exc:
            case.fail(f"{why}: the refusal hands back {cmd!r}, which is not a "
                      f"command line at all — it does not parse ({exc}). The "
                      f"reader who copies it gets a shell error about a quote "
                      f"they did not type.")
        case.assertEqual(
            argv.count("--root"), 1,
            f"{why}: the refusal hands back {cmd!r}, which parses to "
            f"{argv!r} — that is not one `--root` and one value. Either the "
            f"root was dropped, or an argument carrying a space split into "
            f"several and the reader's command means something else.")
        i = argv.index("--root")
        case.assertGreater(
            len(argv), i + 1,
            f"{why}: {cmd!r} parses to {argv!r} — `--root` with nothing "
            f"after it")
        case.assertEqual(
            argv[i + 1], str(root),
            f"{why}: the refusal hands back {cmd!r}, which parses its root as "
            f"{argv[i + 1]!r} rather than the {str(root)!r} the reader's own "
            f"invocation carried. Run from where the reader is standing it "
            f"acts on a different project — silently, if that project happens "
            f"to be in a state where the command is a no-op.")
