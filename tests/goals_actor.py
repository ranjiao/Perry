"""Explicit actor for legacy goals fixtures; actor-contract tests use raw inproc.

No production default: only commit/link calls in opted-in existing tests get
an owner. Reads, explicit actors and the new KR writer tests remain unchanged.
"""
from pathlib import Path
import inproc


def owned(argv, actor="test-goals"):
    argv = list(argv)
    if argv and argv[0] in ("commit", "link") and "--actor" not in argv:
        return [*argv, "--actor", actor]
    return argv


def command(argv, actor="test-goals"):
    argv = list(argv)
    for i, arg in enumerate(argv[:3]):
        if Path(str(arg)).name == "perry-goals":
            return argv[:i + 1] + owned(argv[i + 1:], actor)
    return argv


def run(tool, argv, *, bare=False, **kwargs):
    if tool == "perry-goals" and not bare:
        argv = owned(argv)
    return inproc.run(tool, argv, **kwargs)
