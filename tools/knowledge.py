#!/usr/bin/env python3
"""Read and mechanically validate knowledge cards, with explicit document roots.

Usage: python3 tools/knowledge.py --root PROJECT --state-root DOCUMENTS
No promotion, state mutation, semantic judgement or implicit legacy resolver.
"""
import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys

from host_common import explicit_directory, field, strip_comments
from roles import report as role_report


def source_files(source: str, roots: tuple[Path, ...]) -> list[str]:
    """Resolve local file citations only; IDs and URLs need a separate review."""
    found = []
    for token in re.split(r"[\s,;·|]+", source):
        token = token.strip("*`()[]<>,;")
        if not token or "://" in token:
            continue
        token = re.sub(r":\d+$", "", token)
        for root in roots:
            candidate = (root / token).resolve()
            if candidate.is_relative_to(root) and candidate.is_file():
                found.append(str(candidate))
    return sorted(set(found))


def report(root: Path, state_root: Path, stale_days=90) -> dict:
    root, state_root = root.resolve(), state_root.resolve()
    cards, errors = [], []
    roles = {Path(c["path"]).stem for c in role_report(root)["cards"]}
    for path in sorted((state_root / "knowledge").rglob("*.md")):
        if path.name == "INDEX.md":
            continue
        text = strip_comments(path.read_text(encoding="utf-8"))
        kind = field(text, "Kind")
        if not kind:
            continue  # source digests are not cards
        heading = re.search(r"^#\s+(.+)$", text, re.M)
        claim = re.sub(r"^.*?\s+[—–-]\s+", "", heading.group(1)).strip() if heading else ""
        card = {"path": path.relative_to(state_root).as_posix(), "topic": path.parent.name,
                "slug": path.stem, "kind": kind, "claim": claim,
                **{key: field(text, label) for key, label in (
                    ("source", "Source"), ("owner_role", "Owner role"),
                    ("last_verified", "Last verified"), ("invalidated_by", "Invalidated by"))}}
        card_errors = []
        blank = {"", "—", "–", "-", "TBD", "(none)"}
        for key in ("claim", "source", "invalidated_by", "last_verified"):
            if card[key] in blank or "{{" in card[key]:
                card_errors.append("missing_" + key)
        if kind not in ("knowledge", "source-of-truth"):
            card_errors.append("invalid_kind")
        if roles and card["owner_role"] not in roles:
            card_errors.append("undeclared_owner_role")
        sources = source_files(card["source"], (root, state_root))
        if not sources:
            card_errors.append("source_not_local_file")
        age = None
        try:
            age = (date.today() - date.fromisoformat(card["last_verified"])).days
        except ValueError:
            card_errors.append("invalid_last_verified")
        if age is not None and age < 0:
            card_errors.append("future_last_verified")
        card.update(source_files=sources, stale=age is not None and age > stale_days,
                    errors=sorted(set(card_errors)))
        cards.append(card)
        errors += [{"path": card["path"], "code": code} for code in card["errors"]]
    return {"contract": "perry-knowledge/read/2.0", "semantics": [],
            "project_root": str(root), "state_root": str(state_root), "cards": cards,
            "total": len(cards), "stale": sum(c["stale"] for c in cards), "errors": errors,
            "source_policy": "local-files-only; IDs/URLs require explicit native/source review"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--state-root", required=True)
    parser.add_argument("--stale-days", type=int, default=90)
    args = parser.parse_args(argv)
    if args.stale_days < 0:
        parser.error("--stale-days must be non-negative")
    try:
        result = report(explicit_directory(args.root), explicit_directory(args.state_root), args.stale_days)
    except (ValueError, OSError) as exc:
        parser.exit(2, str(exc) + "\n")
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
