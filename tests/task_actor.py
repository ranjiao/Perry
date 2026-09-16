"""Explicit actor arguments for existing writer fixtures (never production defaults).

The actor contract tests call the raw runner, so missing-owner refusals are
not repaired by this fixture. Other tests retain an explicitly supplied actor.
"""
from pathlib import Path

import inproc


def owned(argv, actor):
    """Name a fixture's writer while leaving reads and malformed argv intact."""
    argv = list(argv)
    tool = inproc.load("perry-task")
    surface = tool.SURFACE
    writes = {s["name"] for s in surface["subcommands"] if s.get("writes")}
    if "--actor" not in argv and argv and tool.parse(argv).cmd in writes:
        return [*argv, "--actor", actor]
    return argv


def command(argv, actor):
    """Add the fixture owner to a subprocess perry-task command only."""
    argv = list(argv)
    for i, arg in enumerate(argv[:3]):
        if Path(str(arg)).name == "perry-task":
            return argv[:i + 1] + owned(argv[i + 1:], actor)
    return argv
