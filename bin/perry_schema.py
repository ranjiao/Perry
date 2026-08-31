#!/usr/bin/env python3
"""perry_schema — the state-file and schema helpers, and nothing else.

**This file used to be `bin/perry-conform`, the ADR-004 conformance gate, and
that gate is gone (TASK-261).** What it did: `perry-conform declare` recorded
that the user had declared a file to be Perry's at shape version N, and
`gate()` — called from `perry-task`, `perry-goals` and `perry_md_store` before
every write — refused when the file's LIVE shape no longer matched its stored
DECLARATION. Keeping the declaration and the check apart was the whole design,
because "a stored decision plus a live check can disagree, and that
disagreement is a finding".

It never disagreed. `.perry/conformance.jsonl` held 23 records at the end.
Every one was `route: declare`. Every one was a file in Perry's own
repository. Zero carried `route: migrate`. The disagreement the design exists
to surface needs a FOREIGN project that drifts, and Perry has never been
pointed at one — `TASK-097` ("migrate the two real projects, at V5") stayed
`not_started` from the day it was filed. A mechanism whose triggering
condition has never occurred is not a guard, and the three defects filed
against it (TASK-223, 246, 248) were work about itself.

`perry-decide` removed its own gate first and named the hole rather than
faking it. This is the same move with the measurement attached.

WHAT SURVIVED, and why the file survived with it: the gate was never the only
thing in here. `state_files()`, `load_schema()`, `spec_for()`, `shape_version()`
and the two CLI helpers are generic — they enumerate the state files a schema
declares and answer what shape it is at. `bin/perry-migrate` imports every one
of them and nothing about conformance. So the file is gutted and renamed
rather than deleted, and it now says what it is.
"""

from __future__ import annotations
import difflib
import importlib.machinery
import importlib.util
import json
import os
import re
import shlex
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent

PERRY_HOME = Path(os.environ.get("PERRY_HOME") or HERE.parent).resolve()
sys.path.insert(0, str(PERRY_HOME / "viewer"))
sys.path.insert(0, str(PERRY_HOME / "bin"))
import parsers as P  # noqa: E402
from tables import render_row  # noqa: E402
import lib  # noqa: E402

_LINT = None

def lint():
    """`bin/perry-lint` as a module, loaded once per process.

    This tool must NOT contain a second definition of Perry's shape. The one
    definition is `schema/state-schema.json`, and the one implementation of
    "does this file match it" is `perry-lint.check_file`. So the linter is
    imported rather than imitated, the same way `bin/perry-task` imports
    `bin/perry-state` rather than re-deriving its rules."""
    global _LINT
    if _LINT is None:
        sys.path.insert(0, str(PERRY_HOME / "bin"))
        spec = importlib.util.spec_from_loader(
            "perry_lint", importlib.machinery.SourceFileLoader(
                "perry_lint", str(PERRY_HOME / "bin" / "perry-lint")))
        mod = importlib.util.module_from_spec(spec)
        sys.modules.setdefault("perry_lint", mod)
        spec.loader.exec_module(mod)
        _LINT = mod
    return _LINT

class Refused(Exception):
    """A refusal is a first-class outcome, not a crash. Nothing was written."""

def load_schema() -> dict:
    """`lib.load_schema`, plus the one thing this tool needs done after it.

    The arming is not part of loading and is why this wrapper exists: without
    it, a project whose board says `负责人` is reported as missing `Owner`."""
    schema = lib.load_schema(Refused)
    lint().load_glossary(schema)
    return schema

def shape_version(schema: dict) -> int:
    """Perry's shape version — `schema_version`, not a number of its own.

    Deliberately NOT a second counter. `schema/state-schema.json` *is* the
    definition of Perry's shape; a `conformance_version` beside it would be one
    rule with two numbers, and the first schema change that forgot to bump both
    would make every marker a lie."""
    return int(schema.get("schema_version") or 0)

def state_files(project_root: Path, state_root: Path, schema: dict) -> list[tuple[str, Path, dict]]:
    """Every file the schema claims, as (key, absolute path, spec).

    The enumeration is `perry-lint.iter_targets` — the same globbing, the same
    `exclude` handling — so "a file perry-lint validates" and "a file that can
    be declared conformant" cannot come apart."""
    L = lint()
    out: list[tuple[str, Path, dict]] = []
    for spec in schema["files"]:
        base = project_root if spec.get("anchor") == "project" else state_root
        for path in L.iter_targets(base, spec):
            # **Two specs may share one glob.** `knowledge/*/*.md` is matched by
            # both the digest and the knowledge-card entry, and a card is not a
            # malformed digest. `spec_claims` is `perry-lint`'s one
            # implementation of the declared `discriminator`; putting the call
            # HERE rather than in each caller is what makes lint, conform and
            # migrate agree — the first version wired it into `perry-lint`
            # alone and `perry-migrate` immediately started writing the card's
            # five fields into every digest, `Kind: —` included, on every real
            # project. Caught by the suite.
            if not L.spec_claims(spec, L.strip_comments(
                    path.read_text(errors="replace")), schema):
                continue
            out.append((path.relative_to(base).as_posix(), path, spec))
    return out

def spec_for(project_root: Path, state_root: Path, schema: dict,
             key: str) -> tuple[Path, dict] | None:
    for k, path, spec in state_files(project_root, state_root, schema):
        if k == key:
            return path, spec
    return None

def _q(value) -> str:
    """**One argument of a command this tool hands back, spelled so the reader
    can copy it.** The single choke point for every such argument.

    `shlex.quote`, which is a no-op on a value with nothing shell-special in
    it — so a project at `/home/ada/perry` is still handed
    `--root /home/ada/perry`, and one at `/Users/ada/My Project` is handed
    `--root ʼ/Users/ada/My Projectʼ` instead of a line that parses as two
    arguments.

    **Why a named function and not `shlex.quote` inline.** Round 3 dropped the
    root from a handed-back command; round 4 added it back UNQUOTED, in the
    same sentence, because `_root_flag` was a convention and a convention is
    enforced by whoever remembers it. This is the same convention — but
    `tests/sweep_handed_back_commands.py` now reads every handed-back command
    off the AST and reports any `{...}` inside one that is not `_q(...)`,
    `_root_flag(...)`, `shlex.quote(...)` or the `r` those produce, and
    `tests/test_conformance.py § test_no_refusal_names_a_command_without_the
    _root` fails the suite on it. So the bypass spelling — `--root {root_arg}`,
    `declare {v.path}` — is not discouraged, it is RED. That is the difference
    between this shape and the one it replaces.
    """
    return shlex.quote(str(value))

def _root_flag(root_arg: str | None) -> str:
    return f" --root {_q(root_arg)}" if root_arg else ""

def _roots(root_arg: str | None) -> tuple[Path, Path]:
    project_root = (Path(root_arg).expanduser().resolve() if root_arg
                    else Path(os.environ.get("PERRY_PROJECT") or Path.cwd()).resolve())
    return project_root, P.resolve_state_root(project_root)
