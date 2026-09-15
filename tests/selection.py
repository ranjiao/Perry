#!/usr/bin/env python3
"""Which test modules a change selects. DESIGN-021 § 5.2, phase A (TASK-448).

Every `tests/test_*.py` declares what it is FOR:

    COVERS = ("bin/perry-task", "schema/task-list-contract.md")
    # or, for a module that genuinely guards everything:
    COVERS = ALL

and this module turns a set of changed paths into a set of modules, by rules
that compare paths and judge no meaning (`ARCHITECTURE.md § 6` NN-4).

## The rules, in the order they are applied

1. **Widening rules, checked first.** Each one selects the whole suite:
   a changed path under `bin/lib/`; `viewer/parsers.py`; a path under
   `schema/`; a path under `tests/` that is not a `tests/test_*.py`; and any
   changed path that no module's `COVERS` prefix matches.
2. A changed `tests/test_*.py` selects itself.
3. A changed path that starts with a prefix in a module's `COVERS` selects that
   module. The match is a plain string prefix, so `bin/perry-task` also
   matches `bin/perry-tasks` — a prefix errs toward running more.
4. A module declaring `COVERS = ALL` is selected on every change. It does NOT
   count as matching a path for rule 1's last clause: if it did, one `ALL`
   module anywhere would switch that clause off for the whole suite.
5. A module with no `COVERS` is always selected, so an undeclared module makes
   a run slower and never unsafe.

Two details the design leaves to the implementation, both chosen to select
more rather than less:

* `git diff` runs with `--no-renames`, so a rename reports both the path that
  left and the path that arrived, and a module covering either is selected.
* A changed `tests/test_*.py` that no longer exists selects nothing — there is
  no module left to run — and is not an unmatched path either.

`COVERS` is read from each module's source with `ast`, never by importing the
module: importing 143 test modules to read one constant would run their
module-level set-up, and a module that fails to import would silently have no
declaration. A `COVERS` that is not a non-empty tuple of relative path strings
or the name `ALL` is refused rather than guessed at.

## What prints

    python3 tests/selection.py --base <ref> [--head <ref>]
    python3 tests/selection.py --replay 50 --base <ref>

The first is what `bash tests/run --tier affected --base <ref> --dry-run`
calls: one line per selected module with the rule that selected it, the
selected share of module-seconds (`tests/durations.json`, read through
`tests/parallel § load_durations` — not a second reader of it), and
`this change is wide` when that share is over half. It runs no test.

The second replays the last N merges reachable by first parent from `--base`
through the same selector, each merge's changed paths being `M^1..M`, against
the declarations in the working tree. It reads git and writes nothing.
"""

from __future__ import annotations

import argparse
import ast
import collections
import importlib.machinery
import importlib.util
import pathlib
import re
import statistics
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable, Mapping, Union

ROOT = pathlib.Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"


class _All:
    """The one value `COVERS = ALL` may name. Compared by identity."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "ALL"


ALL = _All()

Declaration = Union[tuple, _All, None]

#: A test module, by path. Only depth one: `tests/fixtures/**/test_*.py` is a
#: fixture and a helper, never a module the runner discovers.
TEST_MODULE = re.compile(r"tests/test_[^/]*\.py")

#: The widening kinds, in the order they are checked, with the words printed.
BIN_LIB = "bin/lib/"
PARSERS = "viewer/parsers.py"
SCHEMA = "schema/"
TESTS_HELPER = "tests/ helper"
UNMATCHED = "unmatched"
WIDENING_KINDS = (BIN_LIB, PARSERS, SCHEMA, TESTS_HELPER, UNMATCHED)

#: The selected share above which a change is reported as wide (§ 5.2).
WIDE = 0.5


class DeclarationError(ValueError):
    """A `COVERS` this module refuses to interpret."""


class GitError(RuntimeError):
    """A git command the selector needed did not answer."""


# ── declarations ─────────────────────────────────────────────────────────

def is_test_module(path: str) -> bool:
    return TEST_MODULE.fullmatch(path) is not None


def read_covers(source: str, name: str = "<module>") -> Declaration:
    """The module's top-level `COVERS`, or None when it declares none."""
    value = None
    for node in ast.parse(source, name).body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
        else:
            continue
        if any(isinstance(t, ast.Name) and t.id == "COVERS" for t in targets):
            value = node.value
    if value is None:
        return None
    if isinstance(value, ast.Name) and value.id == "ALL":
        return ALL
    if isinstance(value, (ast.Tuple, ast.List)) and value.elts and all(
            isinstance(e, ast.Constant) and isinstance(e.value, str)
            for e in value.elts):
        prefixes = tuple(e.value for e in value.elts)
        bad = [p for p in prefixes
               if not p or p.startswith(("/", "./")) or ".." in p.split("/")]
        if bad:
            raise DeclarationError(
                f"{name}: COVERS prefixes must be repository-relative paths, "
                f"got {bad}")
        return prefixes
    raise DeclarationError(
        f"{name}: COVERS must be a non-empty tuple of path strings or ALL")


def declarations(root: pathlib.Path = ROOT) -> dict[str, Declaration]:
    """Every `tests/test_*.py` under `root`, by file name, and its `COVERS`."""
    return {p.name: read_covers(p.read_text(), p.name)
            for p in sorted((root / "tests").glob("test_*.py"))}


# ── the selector: a pure function ────────────────────────────────────────

@dataclass(frozen=True)
class Selection:
    #: module file name → the rule that selected it, as printed
    modules: dict
    #: (kind, path) for every widening rule that fired, in check order
    widened: tuple

    @property
    def full(self) -> bool:
        return bool(self.widened)


def widening(path: str, prefixes: Iterable[str]) -> str | None:
    """The widening kind `path` fires, or None."""
    if path.startswith("bin/lib/"):
        return BIN_LIB
    if path == "viewer/parsers.py":
        return PARSERS
    if path.startswith("schema/"):
        return SCHEMA
    if path.startswith("tests/") and not is_test_module(path):
        return TESTS_HELPER
    if not is_test_module(path) and not any(path.startswith(p)
                                            for p in prefixes):
        return UNMATCHED
    return None


def select(changed: Iterable[str],
           decls: Mapping[str, Declaration]) -> Selection:
    """Apply § 5.2 to `changed` paths against `decls`. No I/O."""
    changed = sorted(set(changed))
    prefixes = sorted({p for d in decls.values()
                       if isinstance(d, tuple) for p in d})
    widened = tuple((kind, path) for path in changed
                    if (kind := widening(path, prefixes)) is not None)
    if widened:
        kind, path = widened[0]
        rule = f"full — {kind}: {path}"
        return Selection({m: rule for m in decls}, widened)

    picked: dict[str, str] = {}
    for m, d in decls.items():
        if f"tests/{m}" in changed:
            picked[m] = f"changed: tests/{m}"
        elif d is None:
            picked[m] = "no COVERS"
        elif d is ALL:
            picked[m] = "COVERS = ALL"
        else:
            hit = next(((p, c) for c in changed for p in d
                        if c.startswith(p)), None)
            if hit:
                picked[m] = f"covers {hit[0]}: {hit[1]}"
    return Selection(picked, ())


def share(sel: Selection, decls: Mapping[str, Declaration],
          durations: Mapping[str, float]) -> tuple[float, float]:
    """(selected module-seconds, suite module-seconds). Unmeasured count 0."""
    total = sum(durations.get(m, 0.0) for m in decls)
    chosen = sum(durations.get(m, 0.0) for m in sel.modules)
    return chosen, total


# ── the thin git and stopwatch layer ─────────────────────────────────────

def _git(root: pathlib.Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True,
                          text=True)
    if proc.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {proc.stderr.strip()}")
    return proc.stdout


def changed_paths(base: str, head: str = "HEAD",
                  root: pathlib.Path = ROOT) -> list[str]:
    out = _git(root, "diff", "--name-only", "--no-renames", f"{base}...{head}")
    return [line for line in out.splitlines() if line]


def merge_changed_paths(merge: str, root: pathlib.Path = ROOT) -> list[str]:
    out = _git(root, "diff", "--name-only", "--no-renames",
               f"{merge}^1", merge)
    return [line for line in out.splitlines() if line]


def recent_merges(base: str, count: int,
                  root: pathlib.Path = ROOT) -> list[tuple[str, str, str]]:
    """(sha, date, subject) of the last `count` first-parent merges."""
    out = _git(root, "log", "--merges", "--first-parent", f"-{count}",
               "--format=%H%x09%ad%x09%s", "--date=short", base)
    return [tuple(line.split("\t", 2)) for line in out.splitlines() if line]


def load_durations(root: pathlib.Path = ROOT) -> dict[str, float]:
    """`tests/parallel § load_durations`, imported rather than re-implemented."""
    sys.dont_write_bytecode = True
    runner = root / "tests" / "parallel"
    loader = importlib.machinery.SourceFileLoader("perry_tests_parallel_sel",
                                                  str(runner))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod.load_durations()


# ── output ───────────────────────────────────────────────────────────────

def dry_run_lines(base: str, head: str, changed: list[str], sel: Selection,
                  decls: Mapping[str, Declaration],
                  durations: Mapping[str, float]) -> list[str]:
    chosen, total = share(sel, decls, durations)
    pct = 100.0 * chosen / total if total else 0.0
    out = [f"tier affected · {base}...{head} · {len(changed)} changed "
           f"path(s) · dry run, no test runs"]
    for kind, path in sel.widened:
        out.append(f"  widened to the full suite — {kind}: {path}")
    width = max((len(m) for m in sel.modules), default=0)
    for m in sorted(sel.modules):
        out.append(f"  {m:<{width}}  {sel.modules[m]}")
    out.append(f"selected {len(sel.modules)} of {len(decls)} modules · "
               f"{chosen:.1f} of {total:.1f} module-seconds ({pct:.1f}%)")
    if total and chosen / total > WIDE:
        out.append("this change is wide")
    return out


def replay(base: str, count: int, root: pathlib.Path = ROOT) -> list[str]:
    decls = declarations(root)
    durations = load_durations(root)
    rows, shares, kinds, sole, unmatched = [], [], collections.Counter(), \
        collections.Counter(), collections.Counter()
    merges = recent_merges(base, count, root)
    for i, (sha, date, subject) in enumerate(merges, 1):
        changed = merge_changed_paths(sha, root)
        sel = select(changed, decls)
        chosen, total = share(sel, decls, durations)
        s = chosen / total if total else 0.0
        shares.append(s)
        fired = sorted({k for k, _ in sel.widened},
                       key=WIDENING_KINDS.index)
        kinds.update(fired)
        if len(fired) == 1:
            sole[fired[0]] += 1
        unmatched.update(p for k, p in sel.widened if k == UNMATCHED)
        reason = "; ".join(
            f"{k} ({sum(1 for kk, _ in sel.widened if kk == k)})"
            for k in fired) or "—"
        title = subject.replace("|", "\\|")
        if len(title) > 70:
            title = title[:67] + "..."
        rows.append(f"| {i} | `{sha[:8]}` | {date} | {title} | {len(changed)} "
                    f"| {len(sel.modules)} | {100 * s:.1f}% | {reason} |")
    med = statistics.median(shares) if shares else 0.0
    out = ["| # | merge | date | subject | paths | modules | share | "
           "widening rule (paths) |",
           "|---|---|---|---|---|---|---|---|", *rows, ""]
    buckets = [("0–10%", 0, .10), ("10–25%", .10, .25), ("25–50%", .25, .50),
               ("50–99.9%", .50, .999), ("100% (full)", .999, 1.01)]
    out.append("| share of module-seconds | merges |")
    out.append("|---|---|")
    for label, lo, hi in buckets:
        n = sum(1 for s in shares if (lo < s <= hi) or (lo == 0 and s == 0))
        out.append(f"| {label} | {n} |")
    out.append("")
    out.append(f"merges: {len(shares)} · median share: {100 * med:.1f}% · "
               f"mean share: {100 * statistics.fmean(shares) if shares else 0:.1f}%")
    out.append("widening rule fired, merges: " + (", ".join(
        f"{k} {kinds[k]}" for k in WIDENING_KINDS if kinds[k]) or "none"))
    out.append("widening rule was the only one to fire, merges: " + (", ".join(
        f"{k} {sole[k]}" for k in WIDENING_KINDS if sole[k]) or "none"))
    if unmatched:
        top = collections.Counter()
        for p, n in unmatched.items():
            top["/".join(p.split("/")[:2]) if "/" in p else p] += n
        out.append("unmatched paths by first two segments: " + ", ".join(
            f"{k} {n}" for k, n in top.most_common(12)))
    if med <= WIDE:
        out.append(f"VERDICT: PASS — median share {100 * med:.1f}% ≤ 50%")
    else:
        reasons = ", ".join(f"{k} ({n} merges)"
                            for k, n in kinds.most_common(3))
        out.append(f"VERDICT: FAIL — median share {100 * med:.1f}% > 50%; "
                   f"most frequent reasons: {reasons}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", required=True, help="the ref to diff against")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--replay", type=int, metavar="N",
                    help="replay the last N first-parent merges from --base")
    args = ap.parse_args(argv)
    try:
        if args.replay:
            print("\n".join(replay(args.base, args.replay)))
            return 0
        decls = declarations()
        changed = changed_paths(args.base, args.head)
        sel = select(changed, decls)
        print("\n".join(dry_run_lines(args.base, args.head, changed, sel,
                                      decls, load_durations())))
    except (GitError, DeclarationError) as e:
        print(f"tests/selection.py: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
