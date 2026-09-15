"""A fixture's hand-written board, imported the documented way.

**Why this exists (TASK-262 Amendment (4), round 4b).** A `BOARD.md` a project
still holds is retired: no reader opens it. Many modules wrote a board by hand
because a board was the most legible way to state a fixture — rows under
headings, cells under columns — and then asked a reader what it saw. The
readers now read the stores, so a written board reaches them the way it
reaches a real project's readers: through the `--from-board` imports of
`reference/version-compatibility.md § Upgrading a project to G3`.

What the fixture states is unchanged; only the route to the reader moved.
"""

from __future__ import annotations

import pathlib

import inproc

#: `perry-tasks` verb → the words its refusal uses when the board has no such
#: section, which is "nothing to import" rather than a failure (the upgrade
#: procedure's step 4 says so).
IMPORTS = ("write", "risks-write", "asks-write", "cadence-write",
           "intake-write")
_NO_SECTION = "section on this board"
#: `risks-write`'s refusal for a bullet-list `## Top risks`.
_BULLETS = "is still a bullet list"


def import_board(root: pathlib.Path, *verbs: str, remove: bool = True) -> None:
    """Run each `perry-tasks <verb> --from-board --root <root>` in turn.

    `verbs` defaults to every import. A refusal because the board has no such
    section is skipped; any other non-zero exit raises. With `remove`, the
    board is then deleted from wherever `perry-tasks` found it (state root,
    else project root), which is the procedure's step 7.
    """
    root = pathlib.Path(root)
    for verb in verbs or IMPORTS:
        proc = inproc.run("perry-tasks", [verb, "--from-board", "--root",
                                          str(root)])
        said = proc.stdout + proc.stderr
        if proc.returncode != 0 and verb == "risks-write" \
                and _BULLETS in said:
            # Step 3 of the procedure: a bullet `## Top risks` is converted
            # and stored by `perry-task risk-migrate`, not imported.
            proc = inproc.run("perry-task", ["risk-migrate", "--root",
                                             str(root)])
            said = proc.stdout + proc.stderr
        if proc.returncode != 0 and _NO_SECTION not in said:
            raise AssertionError(f"perry-tasks {verb} --from-board refused on "
                                 f"{root}: exit {proc.returncode}: {said[-600:]}")
    if remove:
        for held in (root / "perry" / "BOARD.md", root / "BOARD.md"):
            if held.is_file():
                held.unlink()
