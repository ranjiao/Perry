#!/usr/bin/env python3
"""**Planted spellings for `tests/sweep_handed_back_commands.py`.**

Never imported and never run. Only ever PARSED, by the sweep and by
`tests/test_conformance.py § TestTheSweepIsMeasuredNotTrusted`, which is what
turns the sweep's recall from a sentence in a RESULT into a number the suite
recomputes.

The V4 round-4 reviewer measured the round-4 sweep at **10 found of 15**
plausible spellings, in a file of its own that no longer exists. A recall
number nobody can re-derive is a claim, so the fifteen are planted here with
the reviewer's own descriptions, plus the shapes round 5 added a rule for.

One function per spelling. The suffix is the measured verdict, and the test
asserts it both ways:

* `_found`   — the sweep reports at least one problem inside this function.
* `_missed`  — it reports none, and that is a **blind spot**: the command is
               genuinely handed back with the root dropped or a value
               interpolated raw, and the sweep cannot see it. Each says why.
* `_clean`   — it reports none, and that is **correct**: the phrase is a
               mention, a provenance value, or a properly built command. These
               guard the other direction, where a sweep that called everything
               a finding would also score 100 % recall.

Nothing here is a defect in Perry. `perry-conform` and `perry-migrate` are
both at zero; this file exists so the *sweep* can be measured.
"""
from __future__ import annotations

import shlex


# ── the six the round-4 sweep already caught ──────────────────────────────


def spelling_01_indented_continuation_line_found(root_arg):
    """The shipped shape: an f-string whose command sits on its own indented
    continuation line. This is the spelling the round-3 FAIL was written in."""
    raise ValueError(
        f"the record will not convert. Fix those lines, then run:\n"
        f"    perry-conform migrate\n"
        f"**Nothing was written.**")


def spelling_02_inline_backticked_after_a_cue_found(root_arg):
    """Introduced by a cue word inside prose, backticked."""
    return f"the way forward is `perry-conform migrate`, from the project"


def spelling_03_percent_format_call_found(n):
    """`str.format`, which is not an f-string and is still one template."""
    return "    perry-conform declare {n} files".format(n=n)


def spelling_04_percent_operator_found(n):
    """The `%` operator, same."""
    return "    perry-conform declare %s" % n


def spelling_05_plus_concatenation_of_two_literals_found():
    """Two literals joined with `+`: one string, not two."""
    return ("fix it, then run:\n"
            "    perry-conform " + "migrate\n")


def spelling_06_plus_concatenation_splitting_mid_word_found():
    """The same, split in the middle of the subcommand — the phrase is
    reassembled off the AST rather than grepped for."""
    return "    perry-conform mig" + "rate\n"


def spelling_09_augmented_assignment_found():
    """Built up with `+=` across statements."""
    msg = "the record will not convert.\n"
    msg += "    perry-conform migrate\n"
    return msg


def spelling_10_augmented_assignment_split_mid_word_found():
    msg = "the record will not convert.\n"
    msg += "    perry-conform mig"
    msg += "rate\n"
    return msg


def spelling_11_join_of_a_list_found():
    return "\n".join(["the record will not convert.",
                      "    perry-conform migrate"])


def spelling_15_two_bare_prints_found():
    print("the record will not convert. Then:")
    print("    perry-conform migrate")


# ── the four the round-4 sweep MISSED, and round 5's rule now catches ─────
#
# Every one of them is the same shape: the command reaches the message through
# a NAME, so there is no cue word in front of it to read. There is no cue
# because there is no sentence — the string is the whole command and nothing
# else, which `IS_WHOLLY_A_COMMAND` reads as the signal it is.


MIGRATE_HINT = "perry-conform migrate"


def spelling_07_module_constant_found():
    """Reviewer's #7. Interpolated from a module constant far away."""
    return f"the record will not convert. Run:\n    {MIGRATE_HINT}\n"


def spelling_08_local_variable_found():
    """Reviewer's #8."""
    fix = "perry-conform migrate"
    return f"the record will not convert. Run:\n    {fix}\n"


def spelling_12_helper_return_found():
    """Reviewer's #12: a nested helper that returns the command."""

    def way_out():
        return "perry-conform migrate"

    return f"the record will not convert. Run:\n    {way_out()}\n"


FIXES = {"legacy": "perry-conform migrate", "shape": "perry-migrate apply"}


def spelling_14_dict_value_found():
    """Reviewer's #14."""
    return f"the record will not convert. Run:\n    {FIXES['legacy']}\n"


# ── the one that is still missed, and why ────────────────────────────────


def spelling_13_cue_word_not_in_the_list_missed(root_arg):
    """Reviewer's #13, and **still a blind spot**.

    The ruling is made from the words immediately before the phrase, and the
    cue list is `run / with / is / try / use`. This sentence introduces the
    command with "is spelled", which starts with `is`, but the `is` is not
    adjacent to the phrase — five characters of "spelled " sit between them —
    so `CUE`'s `$`-anchored match fails and this reads as a mention.

    **Not fixed by adding cue words.** The list would have to contain every
    verb English can introduce an instruction with, and the first one nobody
    thought of is the one the next defect is written in. What closes this
    shape is `IS_WHOLLY_A_COMMAND` above, and it does not apply here because
    the command is a fragment of a larger sentence rather than a literal of
    its own. Recorded as the residual rather than papered over.
    """
    return f"the command is spelled perry-conform migrate, from anywhere"


# ── round 5's class: the root is there and the line is not a command ──────


def spelling_16_root_interpolated_raw_found(root_arg):
    """**The round-4 V4 FAIL, planted.** The root is present, spelled
    correctly, and interpolated raw — so on `/Users/ada/My Project` the reader
    copies a line that parses as two extra arguments and exits 1."""
    return (f"the record will not convert. Run:\n"
            f"    perry-conform migrate --root {root_arg}\n")


def spelling_17_path_argument_interpolated_raw_found(v, r):
    """Not the root: any other argument. `perry-conform check 'My Notes.md'`
    is a file a reader can really have, and four sites in `bin/perry-conform`
    interpolated exactly this raw until round 5."""
    return f"declare it with:\n    perry-conform declare {v.path}{r}\n"


def spelling_18_the_choke_point_itself_found(root_arg):
    """**Where round 4's defect actually lived**, and no command-phrase rule
    can reach it: `_root_flag`'s body names no tool, so `CMD` never matches.
    `FLAG_VALUE` is the rule that reads a long flag's value wherever it
    appears."""
    return f" --root {root_arg}" if root_arg else ""


def spelling_19_prose_glued_to_the_command_found(v, r, tail):
    """The DRIFTED branch of `bin/perry-conform § message_for`, as it stood
    before round 5: the unreadable-lines parenthetical appended to the command
    line itself, so the last line the reader copies is
    `syntax error near unexpected token '('`, rc=2. Caught here as an
    unquoted `{tail}` rather than as prose, which is the same finding by a
    different name — the rule is that everything interpolated into a line the
    reader copies has to be an argument."""
    return f"    perry-conform declare {v.path}{r}{tail}"


# ── correct rulings, which guard the other direction ──────────────────────


def spelling_20_prose_naming_a_tool_clean():
    """A mention: the reader is being told NOT to run this one."""
    return "is not what `perry-conform declare` would have written"


def spelling_21_provenance_value_clean(declare):
    """A VALUE that is spelled like a command because it is the name of one.
    Nothing prints it as an instruction."""
    return declare(writer="perry-conform declare", route="migrate")


def spelling_22_correctly_built_command_clean(root_arg):
    """Root carried, argument quoted at the choke point. The shape everything
    above is measured against."""
    r = f" --root {shlex.quote(root_arg)}" if root_arg else ""
    return f"fix it, then run:\n    perry-conform migrate{r}\n"


def spelling_23_bare_tool_name_as_a_value_clean():
    """A bare tool name with no arguments is a value or an identifier far more
    often than an instruction — a temp-directory prefix, a `writer` field, a
    dispatch key. Excluded deliberately; the cost is that a genuine bare
    `perry-lint` handed back with no cue in front of it is not seen."""
    return "perry-lint"
