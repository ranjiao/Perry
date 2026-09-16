#!/usr/bin/env python3
"""Perry product release records; typed metadata and opaque, agent-authored notes.

This is product maintenance data, not a generic project's Perry state.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
RECORDS = "release/records.jsonl"
PROJECTIONS = ("VERSION", "CHANGELOG.md")
FIELDS = {"version", "date", "kind", "phase", "task", "delivery", "integrator",
          "notes", "upgrade", "breaking", "decision"}
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")
PHASE = re.compile(r"[0-9]{3,}-[a-z][a-z0-9-]*\Z")
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}\Z")
# Dogfood state is not shipped product code. The phase pointer is the one
# lifecycle exception: starting Perry's own new phase requires a minor entry.
PMO_PREFIXES = ("perry/",)
PMO_FILES = {".perry/config.jsonl", ".perry/events.jsonl", ".perry/hook.md"}
PMO_CONFIG_PREFIXES = (".perry/roles/",)
PHASE_POINTER = "perry/phase/CURRENT"


class Refused(ValueError):
    pass


def git(root: Path, *args: str, missing=False) -> bytes:
    out = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if out.returncode and not missing:
        raise Refused("git " + args[0] + ": " + out.stderr.decode(errors="replace").strip())
    return out.stdout if out.returncode == 0 else b""


def commit(root: Path, ref: str) -> str:
    return git(root, "rev-parse", "--verify", ref + "^{commit}").decode().strip()


def version(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not VERSION.fullmatch(value):
        raise Refused("version must be canonical numeric major.minor.patch")
    return tuple(map(int, value.split(".")))


def required_text(value, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise Refused(f"{field} requires nonempty text (write 'None.' when appropriate)")


def validate(rows: list[dict]) -> None:
    if not rows:
        raise Refused("no release records; restore the canonical record file")
    deliveries, phases, decisions = set(), set(), set()
    previous = None
    for row in rows:
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise Refused("release record has missing or unknown fields")
        for field in ("notes", "upgrade", "breaking", "integrator"):
            required_text(row[field], field)
        for field in ("delivery",):
            if not isinstance(row[field], str) or not TOKEN.fullmatch(row[field]):
                raise Refused(f"invalid {field}")
        if row["delivery"] in deliveries:
            raise Refused("duplicate delivery: " + row["delivery"])
        deliveries.add(row["delivery"])
        if not isinstance(row["phase"], str) or not PHASE.fullmatch(row["phase"]):
            raise Refused("phase must be a numbered slug, e.g. 004-guided")
        if row["task"] is not None and (not isinstance(row["task"], str)
                or not re.fullmatch(r"TASK-[0-9]+", row["task"])):
            raise Refused("task must be TASK-<number> or null")
        try:
            date = dt.date.fromisoformat(row["date"])
            if date.isoformat() != row["date"]:
                raise ValueError()
        except (ValueError, TypeError):
            raise Refused("date must be YYYY-MM-DD") from None
        current = version(row["version"])
        kind = row["kind"]
        if previous is None:
            if (kind, row["version"], row["phase"], row["task"], row["delivery"]) != (
                    "baseline", "0.1.0", "004-guided", "TASK-462", "TASK-462-baseline"):
                raise Refused("first record must be the TASK-462 phase-004 0.1.0 baseline")
            phases.add(row["phase"])
        else:
            a, b, c = version(previous["version"])
            if row["date"] < previous["date"]:
                raise Refused("release dates must not go backwards")
            if kind == "patch":
                expected = (a, b, c + 1)
                if row["phase"] != previous["phase"] or row["task"] is None:
                    raise Refused("patch requires a task delivery in the current phase")
            elif kind == "phase":
                expected = (a, b + 1, 0)
                if (row["phase"] in phases or int(row["phase"].split("-", 1)[0])
                        <= int(previous["phase"].split("-", 1)[0])):
                    raise Refused("phase must be new and move forwards")
                phases.add(row["phase"])
            elif kind == "major":
                expected = (a + 1, 0, 0)
                if row["phase"] != previous["phase"]:
                    raise Refused("major allocation keeps the current phase")
            else:
                raise Refused("only the first record can be a baseline")
            if current != expected:
                raise Refused("out-of-order version: expected " + ".".join(map(str, expected)))
        if kind == "major":
            if not isinstance(row["decision"], str) or not TOKEN.fullmatch(row["decision"]):
                raise Refused("major requires an explicit human-decision reference")
            if row["decision"] in decisions:
                raise Refused("major decision reference has already been used")
            decisions.add(row["decision"])
        elif row["decision"] is not None:
            raise Refused("decision is reserved for a major allocation")
        previous = row


def load(raw: bytes) -> list[dict]:
    try:
        # Reject duplicate JSON keys, which otherwise silently replace values.
        def pairs(items):
            out = {}
            for key, value in items:
                if key in out:
                    raise Refused("duplicate JSON field: " + key)
                out[key] = value
            return out
        rows = [json.loads(line, object_pairs_hook=pairs)
                for line in raw.decode("utf-8").splitlines() if line.strip()]
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Refused("corrupt release records: " + str(exc)) from exc
    validate(rows)
    return rows


def notes(row: dict) -> str:
    task = f" · {row['task']}" if row["task"] else ""
    return (f"## {row['version']} — {row['date']}\n\n"
            f"{row['kind']} · phase {row['phase']}{task} · delivery {row['delivery']}\n\n"
            f"### Changes\n\n{row['notes']}\n\n"
            f"### Upgrade notes\n\n{row['upgrade']}\n\n"
            f"### Breaking changes\n\n{row['breaking']}\n")


def projections(rows: list[dict]) -> dict[str, bytes]:
    return {"VERSION": (rows[-1]["version"] + "\n").encode("ascii"),
            "CHANGELOG.md": ("# Perry changelog\n\nGenerated from release/records.jsonl; "
                             "edit records through the release tool.\n\n"
                             + "\n".join(notes(row) for row in reversed(rows))).encode("utf-8")}


def read(root: Path, path: str, ref: str | None = None) -> bytes:
    if ref:
        sha = commit(root, ref)
        out = subprocess.run(["git", "-C", str(root), "show", f"{sha}:{path}"],
                             capture_output=True)
        if out.returncode:
            raise Refused(f"missing {path} at {sha}")
        return out.stdout
    try:
        return (root / path).read_bytes()
    except OSError as exc:
        raise Refused(f"cannot read {path}: {exc}") from exc


def checked(root: Path, ref: str | None = None) -> list[dict]:
    rows = load(read(root, RECORDS, ref))
    for path, expected in projections(rows).items():
        if read(root, path, ref) != expected:
            raise Refused(f"projection drift: {path}; inspect records then run render --repair")
    return rows


def atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".release-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@contextlib.contextmanager
def locked(root: Path):
    path = Path(git(root, "rev-parse", "--git-path", "perry-release.lock").decode().strip())
    if not path.is_absolute():
        path = root / path
    with path.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def render(root: Path) -> list[dict]:
    rows = load(read(root, RECORDS))
    for path, data in projections(rows).items():
        atomic(root / path, data)
    return checked(root)


def allocate(root: Path, kind: str, *, expected: str, date: str, phase: str,
             task: str | None, delivery: str, integrator: str, changes: str,
             upgrade: str, breaking: str, decision: str | None) -> dict:
    with locked(root):
        old = checked(root)
        if old[-1]["version"] != expected:
            raise Refused("stale expected version; rebase on the main integration history")
        a, b, c = version(expected)
        number = {"patch": (a, b, c + 1), "phase": (a, b + 1, 0),
                  "major": (a + 1, 0, 0)}[kind]
        row = dict(version=".".join(map(str, number)), date=date, kind=kind,
                   phase=phase, task=task, delivery=delivery, integrator=integrator,
                   notes=changes, upgrade=upgrade, breaking=breaking, decision=decision)
        validate(old + [row])
        raw = read(root, RECORDS)
        if not raw.endswith(b"\n"):
            raw += b"\n"
        # Canonical atomic replacement first. A crash before either projection
        # finishes makes checked() refuse; explicit render repairs from truth.
        atomic(root / RECORDS, raw + (json.dumps(row, ensure_ascii=False, sort_keys=True)
                                     + "\n").encode("utf-8"))
        render(root)
        return row


def product(path: str) -> bool:
    if path in (RECORDS, *PROJECTIONS):
        return False
    return not (path in PMO_FILES or path.startswith(PMO_PREFIXES + PMO_CONFIG_PREFIXES))


def check_base(root: Path, base: str, head: str) -> dict:
    base_sha, head_sha = commit(root, base), commit(root, head)
    if subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor",
                       base_sha, head_sha], capture_output=True).returncode:
        raise Refused("base is not an ancestor of the checked commit")
    current = checked(root, head_sha)
    paths = git(root, "diff", "--no-renames", "--name-only", "-z",
                base_sha, head_sha).decode().split("\0")
    paths = [p for p in paths if p]
    exists = git(root, "ls-tree", "--name-only", base_sha, "--", RECORDS).strip()
    if exists:
        before = checked(root, base_sha)
        if current[:len(before)] != before or len(current) < len(before):
            raise Refused("release history was rewritten or deleted")
        new = current[len(before):]
    else:
        # Only a genuinely pre-versioned ancestor gets the first-introduction
        # exception; deleting/reintroducing records later cannot reset history.
        if git(root, "log", "--format=%H", base_sha, "--", RECORDS).strip():
            raise Refused("base lost existing release history; baseline cannot be reintroduced")
        if len(current) != 1 or current[0]["kind"] != "baseline":
            raise Refused("first introduction must contain only the 0.1.0 baseline")
        new = current
    def pointer(sha):
        present = git(root, "ls-tree", "--name-only", sha, "--", PHASE_POINTER).strip()
        value = read(root, PHASE_POINTER, sha).decode("utf-8").strip() if present else ""
        if value in ("", "(none)", "none", "—"):
            return None
        if not PHASE.fullmatch(value):
            raise Refused("Perry phase pointer must be a single numbered slug or empty marker")
        return value
    start_phase = None
    if PHASE_POINTER in paths:
        prior, after = pointer(base_sha), pointer(head_sha)
        if after and after != prior:
            start_phase = after
    changed = [p for p in paths if product(p)]
    if start_phase:
        changed.append(PHASE_POINTER)
    if changed and not new:
        raise Refused("product changes require a new release record: " + ", ".join(changed))
    if not changed and any(r["kind"] in ("patch", "phase", "baseline") for r in new):
        raise Refused("PMO-only or synchronization changes do not allocate versions")
    if start_phase and exists and not any(r["kind"] == "phase" and r["phase"] == start_phase
                                         for r in new):
        raise Refused("Perry's new phase pointer requires its matching phase release record")
    return {"base": base_sha, "head": head_sha, "product_paths": changed,
            "new_versions": [r["version"] for r in new]}


def check_tag(rows: list[dict], tag: str) -> None:
    if tag != "v" + rows[-1]["version"]:
        raise Refused("tag must exactly match VERSION: v" + rows[-1]["version"])


def prepare(root: Path, ref: str, tag: str) -> str:
    sha = commit(root, ref)
    rows = checked(root, sha)
    check_tag(rows, tag)
    if commit(root, "HEAD") != sha or git(root, "status", "--porcelain").strip():
        raise Refused("prepare requires a clean checkout of the exact version commit")
    if git(root, "show-ref", "--verify", "refs/tags/" + tag, missing=True):
        raise Refused("tag already exists; it must not be reused or moved")
    return notes(rows[-1])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("show", "check", "notes"):
        p = sub.add_parser(name)
        p.add_argument("--ref", help="read an immutable Git commit/tag instead of working files")
        if name == "show":
            p.add_argument("--json", action="store_true")
        if name == "notes":
            p.add_argument("--version")
        if name == "check":
            p.add_argument("--base", help="compare explicit ancestor to --ref (default HEAD)")
            p.add_argument("--tag")
    p = sub.add_parser("render")
    p.add_argument("--repair", action="store_true", required=True)
    for kind in ("patch", "phase", "major"):
        p = sub.add_parser(kind)
        for flag in ("expected-version", "date", "phase", "delivery", "integrator",
                     "notes-file", "upgrade-file", "breaking-file"):
            p.add_argument("--" + flag, required=True)
        p.add_argument("--task", required=kind == "patch")
        if kind == "major":
            p.add_argument("--decision", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--ref", required=True)
    p.add_argument("--tag", required=True)
    args = ap.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command in ("patch", "phase", "major"):
            row = allocate(root, args.command, expected=args.expected_version,
                           date=args.date, phase=args.phase, task=args.task,
                           delivery=args.delivery, integrator=args.integrator,
                           changes=Path(args.notes_file).read_text(),
                           upgrade=Path(args.upgrade_file).read_text(),
                           breaking=Path(args.breaking_file).read_text(),
                           decision=getattr(args, "decision", None))
            print(row["version"])
        elif args.command == "render":
            with locked(root):
                print(render(root)[-1]["version"])
        elif args.command == "prepare":
            print(prepare(root, args.ref, args.tag), end="")
        else:
            ref = args.ref or ("HEAD" if args.command == "check" and args.base else None)
            rows = checked(root, ref)
            if args.command == "check":
                if args.tag:
                    check_tag(rows, args.tag)
                result = check_base(root, args.base, ref) if args.base else {"version": rows[-1]["version"]}
                print(json.dumps(result, sort_keys=True))
            elif args.command == "show":
                print(json.dumps(rows[-1], ensure_ascii=False, sort_keys=True) if args.json
                      else rows[-1]["version"])
            else:
                selected = [r for r in rows if args.version is None or r["version"] == args.version]
                if not selected:
                    raise Refused("unknown release version")
                print(notes(selected[-1]), end="")
        return 0
    except (Refused, OSError) as exc:
        print("release: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
