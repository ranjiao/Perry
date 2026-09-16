#!/usr/bin/env python3
"""Manual CI-only publisher: exact tested commit, create-only tags and releases.

No command in this module is invoked by ordinary tests or update checks.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

import manage


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def api(repo, token, path, payload=None, allow_missing=False):
    request = urllib.request.Request("https://api.github.com/repos/" + repo + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Accept": "application/vnd.github+json",
                 "Authorization": "Bearer " + token,
                 "X-GitHub-Api-Version": "2022-11-28",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=20) as response:
            raw = response.read(1024 * 1024 + 1)
    except urllib.error.HTTPError as exc:
        if allow_missing and exc.code == 404:
            return None
        raise manage.Refused(f"GitHub request refused (HTTP {exc.code}); nothing is overwritten") from exc
    if len(raw) > 1024 * 1024:
        raise manage.Refused("GitHub response exceeds 1 MiB")
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise manage.Refused("GitHub returned invalid JSON") from exc


def publish(root, repo, token, sha, tag, default_branch):
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise manage.Refused("publish requires a full immutable commit SHA")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise manage.Refused("invalid GitHub repository")
    if not token:
        raise manage.Refused("GH_TOKEN is required")
    body = manage.prepare(root, sha, tag)
    # The workflow fetches the default branch immediately before this check.
    manage.git(root, "check-ref-format", "refs/heads/" + default_branch)
    remote = "refs/remotes/origin/" + default_branch
    base = manage.commit(root, remote)
    if manage.git(root, "merge-base", sha, base).decode().strip() != sha:
        raise manage.Refused("release commit is not integrated into the default branch")
    if api(repo, token, "/releases/tags/" + tag, allow_missing=True) is not None:
        raise manage.Refused("release already exists; refusing to overwrite")
    if api(repo, token, "/git/ref/tags/" + tag, allow_missing=True) is not None:
        raise manage.Refused("remote tag already exists; refusing to reuse or move it")
    # POST refs is create-only. A race or an existing reference is refused by
    # GitHub; no PATCH, DELETE, force push or overwrite endpoint exists here.
    created = api(repo, token, "/git/refs", {"ref": "refs/tags/" + tag, "sha": sha})
    if not isinstance(created, dict) or not isinstance(created.get("object"), dict) or created["object"].get("sha") != sha:
        raise manage.Refused("unexpected created tag; stop and inspect remote state")
    release = api(repo, token, "/releases", {"tag_name": tag, "target_commitish": sha,
        "name": tag, "body": body, "draft": False, "prerelease": False, "make_latest": "legacy"})
    if not isinstance(release, dict) or release.get("tag_name") != tag:
        raise manage.Refused("unexpected release response; inspect remote state")
    return release


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--default-branch", required=True)
    a = ap.parse_args()
    try:
        result = publish(manage.ROOT, a.repo, os.environ.get("GH_TOKEN", ""),
                         a.commit, a.tag, a.default_branch)
        print(result.get("html_url", "release created"))
        return 0
    except (manage.Refused, OSError, urllib.error.URLError) as exc:
        print("release: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
