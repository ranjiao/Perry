"""A conservative static import graph, including extensionless Python scripts."""
from __future__ import annotations

import ast
import fnmatch
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tokenize

SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__", "build",
        "dist", "site-packages", ".tox", ".cache", ".mypy_cache", ".pytest_cache"}


def scan(root: Path, source_roots=(), excludes=(), max_bytes=2_000_000):
    """Return JSON-compatible facts; roots are explicit, not runtime sys.path.

    An unresolved import may be external, excluded, dynamic or missing. Never
    load it to find out. Multiple candidates remain ambiguous, not guessed.
    """
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("project root must be a directory")
    roots = [root]
    for name in source_roots:
        path = (root / name).resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_dir():
            raise ValueError(f"source root must be a directory inside project: {name}")
        if path not in roots:
            roots.append(path)
    files, trees, issues, skipped = [], {}, [], []

    def excluded(rel):
        return any(rel == p.rstrip("/") or rel.startswith(p.rstrip("/") + "/")
                   or fnmatch.fnmatchcase(rel, p) for p in excludes)

    def walk_error(error):
        issues.append({"path": str(error.filename), "line": 0,
                       "kind": "read-error", "message": str(error)})

    for directory, dirs, names in os.walk(root, onerror=walk_error, followlinks=False):
        parent = Path(directory)
        kept = []
        for name in sorted(dirs):
            p = parent / name
            rel = p.relative_to(root).as_posix()
            if (name in SKIP or p.is_symlink() or excluded(rel)
                    or (p / ".git").exists()):
                skipped.append(rel + "/")
            else:
                kept.append(name)
        dirs[:] = kept
        for name in sorted(names):
            path = parent / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink() or not path.is_file() or excluded(rel):
                skipped.append(rel)
                continue
            if path.suffix not in ("", ".py"):
                continue
            try:
                with path.open("rb") as stream:
                    first = stream.readline(256)
                    if path.suffix != ".py" and not (
                            first.startswith(b"#!") and b"python" in first.lower()):
                        continue
                    stream.seek(0)
                    raw = stream.read(max_bytes + 1)
                if len(raw) > max_bytes:
                    raise ValueError(f"exceeds {max_bytes} byte file limit")
                encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
                source = raw.decode(encoding)
            except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
                issues.append({"path": rel, "line": 0, "kind": "read-error",
                               "message": str(exc)})
                files.append({"id": rel, "status": "unreadable", "source": "",
                              "lines": 0, "sha256": None, "kind": "module"})
                continue
            entry = {"id": rel, "status": "parsed", "source": source,
                     "lines": len(source.splitlines()),
                     "sha256": hashlib.sha256(raw).hexdigest(),
                     "kind": "script" if path.suffix == "" else "module"}
            files.append(entry)
            try:
                trees[rel] = ast.parse(source, filename=rel)
            except (SyntaxError, ValueError, RecursionError) as exc:
                entry["status"] = "parse-error"
                issues.append({"path": rel, "line": getattr(exc, "lineno", 0),
                               "kind": "parse-error", "message": str(exc)})
    files.sort(key=lambda item: item["id"])
    aliases = {}
    for entry in files:
        path = root / entry["id"]
        if path.suffix != ".py":
            continue
        for base in roots:
            if not path.is_relative_to(base):
                continue
            parts = list(path.relative_to(base).with_suffix("").parts)
            is_package = parts[-1] == "__init__"
            if is_package:
                parts.pop()
            if parts and all(part.isidentifier() for part in parts):
                alias = ".".join(parts)
                aliases.setdefault(alias, set()).add(entry["id"])

    imports, edge_map = [], {}

    def resolve(name):
        matches = sorted(aliases.get(name, ()))
        if len(matches) > 1:
            return "ambiguous", matches
        if matches:
            return "internal", matches
        if name.split(".")[0] in sys.stdlib_module_names:
            return "stdlib", []
        # Namespace packages have no executable initializer; their children
        # can still be resolved independently by a from-import.
        if any(alias.startswith(name + ".") for alias in aliases):
            return "namespace", []
        return "unresolved", []

    def record(entry, node, module, symbol, contexts):
        kind, targets = resolve(module) if module else ("unresolved", [])
        if symbol and symbol != "*" and module:
            subkind, subtargets = resolve(module + "." + symbol)
            if subkind in ("internal", "ambiguous"):
                kind, targets = subkind, subtargets
        initializers = []
        if kind == "internal":
            # Importing a child also executes package initializers. Include
            # only unambiguous initializers, retaining their distinct reason.
            resolved_name = module + ("." + symbol if symbol and
                                     resolve(module + "." + symbol)[1] else "")
            for i in range(1, len(resolved_name.split("."))):
                candidates = aliases.get(".".join(resolved_name.split(".")[:i]), ())
                if len(candidates) == 1:
                    target = next(iter(candidates))
                    if target.endswith("/__init__.py") and target not in targets:
                        initializers.append(target)
        item = {"id": len(imports), "source": entry["id"],
                "line": node.lineno, "end_line": node.end_lineno,
                "column": node.col_offset, "module": module, "symbol": symbol,
                "statement": ast.get_source_segment(entry["source"], node),
                "resolution": kind, "targets": targets,
                "initializers": initializers, "contexts": contexts}
        imports.append(item)
        if kind == "internal":
            for target in sorted(set(targets + initializers)):
                edge_map.setdefault((entry["id"], target), []).append(item["id"])

    def inspect_node(entry, node, contexts):
        if isinstance(node, ast.Import):
            for alias in node.names:
                record(entry, node, alias.name, None, list(contexts))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                path = root / entry["id"]
                # The most specific configured root defines package context.
                base = max((r for r in roots if path.is_relative_to(r)),
                           key=lambda r: len(r.parts))
                parts = list(path.parent.relative_to(base).parts)
                if node.level > len(parts):
                    module = ""
                else:
                    module = ".".join(parts[:len(parts) - node.level + 1]
                                      + ([module] if module else []))
            for alias in node.names:
                record(entry, node, module, alias.name, list(contexts))
        elif isinstance(node, ast.Call):
            parts, func = [], node.func
            while isinstance(func, ast.Attribute):
                parts.append(func.attr)
                func = func.value
            name = ".".join([func.id] + parts[::-1]) if isinstance(func, ast.Name) else ""
            if name in ("__import__", "importlib.import_module") or name.endswith(
                    (".SourceFileLoader", ".spec_from_file_location", ".sys.path.insert")) or name in (
                        "sys.path.insert", "sys.path.append"):
                issues.append({"path": entry["id"], "line": node.lineno,
                               "kind": "dynamic-import-context",
                               "message": f"{name}: runtime resolution is not evaluated"})
        extra = ()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            extra = ("function-local",)
        elif isinstance(node, (ast.If, ast.Try, ast.For, ast.While, ast.Match)):
            extra = ("conditional",)
        return tuple(dict.fromkeys(contexts + extra))

    for entry in files:
        if entry["id"] in trees:
            pending = [(trees[entry["id"]], ())]
            while pending:
                node, contexts = pending.pop()
                next_contexts = inspect_node(entry, node, contexts)
                pending.extend((child, next_contexts) for child in
                               reversed(list(ast.iter_child_nodes(node))))
    edges = [{"source": a, "target": b, "imports": ids}
             for (a, b), ids in sorted(edge_map.items())]
    counts = {kind: sum(i["resolution"] == kind for i in imports)
              for kind in ("internal", "stdlib", "unresolved", "ambiguous", "namespace")}
    digest = hashlib.sha256(json.dumps({
        "files": [(f["id"], f["sha256"], f["status"]) for f in files],
        "source_roots": [p.relative_to(root).as_posix() for p in roots],
        "excludes": list(excludes), "max_bytes": max_bytes,
        "python": sys.version.split()[0], "schema": 1,
    }, sort_keys=True).encode()).hexdigest()
    return {"schema_version": 1, "project": root.name, "root": str(root),
            "snapshot": digest, "python": sys.version.split()[0],
            "scope": {"source_roots": [p.relative_to(root).as_posix() for p in roots],
                      "excludes": list(excludes), "default_excluded_dirs": sorted(SKIP),
                      "skipped_paths": sorted(skipped), "max_file_bytes": max_bytes,
                      "languages": ["Python"], "relations": "static imports"},
            "summary": {"files": len(files), "parsed": len(trees),
                        "lines": sum(f["lines"] for f in files),
                        "scripts": sum(f["kind"] == "script" for f in files),
                        "edges": len(edges), "imports": len(imports), **counts},
            "files": files, "imports": imports, "edges": edges, "issues": issues}
