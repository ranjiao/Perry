"""Bind an explicit responsibility hierarchy to observed source facts.

The model declares names and ownership, never dependencies. Overlaps and
unassigned files stay visible. Imports imply reference, not business flow.
"""
import fnmatch
import hashlib
import json
import re


def bind(data, specification):
    if (not isinstance(specification, dict) or type(specification.get("version")) is not int
            or specification.get("version") != 1):
        raise ValueError("architecture model must have version: 1")
    nodes, leaves = [], []
    seen = set()

    def visit(items, parent=""):
        if not isinstance(items, list):
            raise ValueError("architecture components must be an array")
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("architecture component must be an object")
            slug = item.get("id", "")
            if not isinstance(slug, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*", slug):
                raise ValueError("component id must be a lowercase slug")
            key = parent + "/" + slug if parent else slug
            if key in seen or key == "unmapped":
                raise ValueError(f"duplicate or reserved component id: {key}")
            seen.add(key)
            label, description = item.get("label"), item.get("description", "")
            layer = item.get("layer", 0)
            if (not isinstance(label, str) or not label or not isinstance(description, str)
                    or type(layer) is not int or not 0 <= layer <= 10):
                raise ValueError(f"invalid label, description or layer: {key}")
            node = {"id": key, "parent": parent, "label": label,
                    "description": description, "layer": layer, "files": []}
            nodes.append(node)
            if "children" in item:
                if "paths" in item or not item["children"]:
                    raise ValueError(f"branch must have children and no paths: {key}")
                visit(item["children"], key)
            else:
                patterns = item.get("paths")
                if not isinstance(patterns, list) or not patterns or not all(
                        isinstance(p, str) and p and not p.startswith("/") and
                        ".." not in p.split("/") for p in patterns):
                    raise ValueError(f"leaf needs project-relative path patterns: {key}")
                leaves.append((node, patterns))

    visit(specification.get("components"))
    owners, issues = {}, []
    by_id = {n["id"]: n for n in nodes}
    unassigned = []
    for file in data["files"]:
        path = file["id"]
        matches = [node for node, patterns in leaves
                   if any(fnmatch.fnmatchcase(path, p) for p in patterns)]
        if len(matches) != 1:
            unassigned.append(path)
            issues.append({"path": path, "kind": "overlap" if matches else "unassigned",
                           "candidates": [n["id"] for n in matches]})
            owners[path] = "unmapped"
            continue
        key = matches[0]["id"]
        owners[path] = key
        while key:
            by_id[key]["files"].append(path)
            key = by_id[key]["parent"]
    if unassigned:
        nodes.append({"id": "unmapped", "parent": "", "label": "尚未归属的代码",
                      "description": "新增代码或分组冲突，需要审阅", "layer": 0,
                      "files": unassigned})
    for node in nodes:
        if not node["files"]:
            issues.append({"path": node["id"], "kind": "empty-component", "candidates": []})
    aliases = specification.get("scope_aliases", {})
    if not isinstance(aliases, dict) or any(not isinstance(k, str) or not isinstance(v, str) or v not in by_id
                                            for k, v in aliases.items()):
        raise ValueError("scope_aliases must map old paths to component ids")
    # Omit implicit package initialization from responsibility dependencies:
    # importing .values does not mean Store's responsibility depends on CLI.
    edge_map = {}
    for item in data["imports"]:
        if item["resolution"] == "internal":
            for target in item["targets"]:
                edge_map.setdefault((item["source"], target), []).append(item["id"])
    edges = [{"source": a, "target": b, "imports": ids}
             for (a, b), ids in sorted(edge_map.items())]
    data["architecture"] = {
        "version": 1, "title": specification.get("title", "代码架构"),
        "basis": specification.get("basis", "Explicit responsibility model; not inferred by AST"),
        "model_sha256": hashlib.sha256(json.dumps(specification, sort_keys=True,
                                                  ensure_ascii=True).encode()).hexdigest(),
        "nodes": nodes, "owners": owners, "issues": issues,
        "edges": edges, "scope_aliases": aliases,
    }
    return data
