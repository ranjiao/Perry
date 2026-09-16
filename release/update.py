"""Bounded release consumer for bin/perry-update-check (stdlib only).

Product metadata, not project state. Never falls back from a failed release
check to main, and never resets a checkout. The shell owns host lookup/flags.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

API_URL = "https://api.github.com/repos/ranjiao/Perry/releases/latest"
VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\n", re.ASCII)
GIT_TIMEOUT = 30
MAX_RESPONSE = 1024 * 1024


class Refused(Exception):
    pass


def version(text: str) -> tuple[int, int, int]:
    match = VERSION.fullmatch(text)
    if not match:
        raise Refused("VERSION must be exactly ASCII X.Y.Z followed by a newline")
    return tuple(map(int, match.groups()))


def official_origin(origin: str) -> bool:
    return origin in {
        "git@github.com:ranjiao/Perry.git", "git@github.com:ranjiao/Perry",
        "https://github.com/ranjiao/Perry.git", "https://github.com/ranjiao/Perry",
        "ssh://git@github.com/ranjiao/Perry.git", "ssh://git@github.com/ranjiao/Perry",
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise Refused("release API redirected; checkout unchanged")


def latest_release() -> dict | None:
    request = urllib.request.Request(API_URL, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "Perry-update-check",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    deadline = time.monotonic() + 10
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=5) as response:
            chunks, size = [], 0
            while True:
                if time.monotonic() >= deadline:
                    raise Refused("release API exceeded its time limit")
                chunk = response.read1(min(8192, MAX_RESPONSE + 1 - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                if size > MAX_RESPONSE:
                    raise Refused("release API response exceeds 1 MiB")
        data = json.loads(b"".join(chunks))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise Refused(f"release API returned HTTP {exc.code}; checkout unchanged") from None
    except (OSError, ValueError, urllib.error.URLError):
        # Do not echo URLs, credentials, proxy details or response bodies.
        raise Refused("release API unavailable or invalid; checkout unchanged") from None
    return data


def release_metadata(data: dict) -> tuple[str, tuple[int, int, int], str]:
    if not isinstance(data, dict) or data.get("draft") is not False or data.get("prerelease") is not False:
        raise Refused("latest release is not a published stable release")
    tag = data.get("tag_name")
    if not isinstance(tag, str) or not tag.startswith("v"):
        raise Refused("release tag must be vX.Y.Z")
    value = version(tag[1:] + "\n")
    notes = data.get("body")
    if not isinstance(notes, str) or not notes.strip():
        raise Refused("release changes are missing; checkout unchanged")
    return tag, value, notes


def git(source: Path, *args: str, allowed=(0,)) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    env.setdefault("GIT_SSH_COMMAND", "ssh -oBatchMode=yes -oConnectTimeout=5")
    try:
        out = subprocess.run(["git", "-C", str(source), "-c", "credential.interactive=never",
                              *args], capture_output=True, text=True, errors="replace", env=env,
                             timeout=GIT_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise Refused("git operation exceeded 30 seconds; no forced update was attempted") from None
    except OSError:
        raise Refused("git could not run; checkout unchanged") from None
    if out.returncode not in allowed:
        raise Refused(f"git {args[0]} failed; no forced update was attempted")
    return out


def ref(source: Path, name: str) -> str | None:
    out = git(source, "rev-parse", "--verify", name, allowed=(0, 128))
    return out.stdout.strip() if out.returncode == 0 else None


def dirty(source: Path) -> bool:
    return bool(git(source, "status", "--porcelain").stdout)


def origin(source: Path) -> str:
    return git(source, "remote", "get-url", "origin").stdout.strip()


def verified_tag(source: Path, tag: str) -> str:
    # Fetch only this exact tag, not main or implicitly-followed tags. Git's
    # target_commitish API field can be a mutable branch and is never used.
    if not official_origin(origin(source)):
        raise Refused("release updates require the official ranjiao/Perry origin")
    git(source, "fetch", "--quiet", "--no-tags", "origin", "refs/tags/" + tag)
    commit = ref(source, "FETCH_HEAD^{commit}")
    if not commit:
        raise Refused("release tag does not resolve to a commit")
    expected = tag[1:] + "\n"
    text = git(source, "show", commit + ":VERSION").stdout
    version(text)
    if text != expected:
        raise Refused("release tag and target-tree VERSION disagree; checkout unchanged")
    for name in ("refs/tags/" + tag, "refs/perry/releases/" + tag):
        known = ref(source, name + "^{commit}")
        if known and known != commit:
            raise Refused("release tag moved or conflicts with a known tag; checkout unchanged")
    git(source, "update-ref", "refs/perry/releases/" + tag, commit)
    return commit


def developer(source: Path, reasons: list[str], log) -> None:
    git(source, "fetch", "--quiet", "--no-tags", "origin", "main:refs/remotes/origin/main")
    behind = git(source, "rev-list", "--count", "HEAD..refs/remotes/origin/main").stdout.strip()
    log(f"Perry dev mode ({', '.join(reasons)}): {behind} new commit(s) on origin/main; report only.")
    if "symlink" in reasons:
        log("To explicitly use verified releases: perry-update-check --force --channel release")


def check(source: Path, *, symlink=False, channel="auto", quiet=False, force=False) -> None:
    def log(text):
        if not quiet:
            print(text)

    head = ref(source, "HEAD")
    if not head:
        raise Refused("checkout has no HEAD")
    branch = git(source, "symbolic-ref", "--quiet", "--short", "HEAD", allowed=(0, 1)).stdout.strip()
    reasons = []
    if symlink and channel != "release":
        reasons.append("symlink")
    if dirty(source):
        reasons.append("dirty")
    if branch and branch != "main":
        reasons.append("on " + branch)
    if reasons:
        developer(source, reasons, log)
        (source / ".update-check").touch()
        return
    if not official_origin(origin(source)):
        raise Refused("release updates require the official ranjiao/Perry origin")
    current_text = git(source, "show", "HEAD:VERSION", allowed=(0, 128)).stdout
    current = version(current_text) if current_text else None
    if not branch:
        # A detached release is updateable, but an arbitrary detached commit
        # remains developer work. Verify its current tag against origin too.
        if not current or verified_tag(source, "v" + current_text.strip()) != head:
            developer(source, ["detached local work"], log)
            return
    data = latest_release()
    if data is None:
        log("Perry: no published stable GitHub Release; checkout unchanged (no main fallback).")
        (source / ".update-check").touch()
        return
    tag, available, notes = release_metadata(data)
    log(f"Perry current: {current_text.strip() or 'unversioned'}; available: {tag[1:]}")
    log("Release changes:\n" + notes)
    if current and available < current:
        raise Refused("available release is older; refusing a downgrade")
    target = verified_tag(source, tag)
    if current == available and head != target:
        developer(source, ["local commits or unreleased work"], log)
        return
    if git(source, "merge-base", "--is-ancestor", head, target, allowed=(0, 1)).returncode:
        common = git(source, "merge-base", head, target, allowed=(0, 1)).stdout.strip()
        if not common:
            raise Refused("release has unrelated history; checkout unchanged")
        developer(source, ["local commits"], log)
        return
    if target != head:
        # Recheck immediately before fast-forward. Never stash/reset/force;
        # Git also refuses an interfering concurrent edit when applying it.
        now_branch = git(source, "symbolic-ref", "--quiet", "--short", "HEAD", allowed=(0, 1)).stdout.strip()
        if dirty(source) or ref(source, "HEAD") != head or now_branch != branch or not official_origin(origin(source)):
            raise Refused("checkout changed during the check; retry after reviewing local work")
        git(source, "-c", "merge.autoStash=false", "merge", "--ff-only", "--no-edit", target)
        if ref(source, "HEAD") != target:
            raise Refused("update did not reach the verified release commit")
        log(f"Perry updated to {tag} ({target[:12]}); subsequent release checks remain enabled.")
    elif force:
        log(f"Perry is already at verified release {tag}.")
    (source / ".update-check").touch()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--symlink", action="store_true")
    parser.add_argument("--channel", choices=("auto", "release"), default="auto")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        gitdir = Path(git(args.source, "rev-parse", "--absolute-git-dir").stdout.strip())
        with (gitdir / "perry-update.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Refused("another update check is already running") from None
            check(args.source, symlink=args.symlink, channel=args.channel,
                  quiet=args.quiet, force=args.force)
        return 0
    except (Refused, OSError) as exc:
        message = str(exc) if isinstance(exc, Refused) else "local update operation failed"
        print("perry-update-check: " + message, file=sys.stderr)
        return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
