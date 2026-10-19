"""Small skill-side primitives; no project-state resolution or kernel imports."""
from datetime import datetime, timezone
from pathlib import Path
import re


def register_stamp() -> str:
    """UTC timestamp retained for architecture evidence: YYYY-MM-DDTHH:MM:SSZ."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def explicit_directory(value: str) -> Path:
    if not value.strip():
        raise ValueError("an explicit non-empty directory is required")
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(f"directory does not exist: {path}")
    return path


def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def field(text: str, label: str) -> str:
    match = re.search(rf"^\s*[-*]?\s*\**{re.escape(label)}\**\s*[:：]\s*([^\n]*)$", text, re.M)
    return match.group(1).strip().strip("*` ") if match else ""


def section(text: str, heading: str) -> str:
    match = re.search(rf"^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return match.group(1).strip() if match else ""


def bullets(text: str) -> list[str]:
    return re.findall(r"^\s*[-*]\s+(.+)$", text, re.M)


def owned_markdown(root, directory, recursive=False):
    """Do not let glob's suppressed directory errors hide a restore point."""
    root, directory = Path(root).resolve(), Path(directory)
    paths, errors = [], []
    try:
        if not directory.resolve().is_relative_to(root):
            raise ValueError('safety directory escapes project')
        for part in [directory, *directory.parents]:
            if part == root:
                break
            if part.is_symlink():
                raise ValueError('safety directory contains a symlink')
    except ValueError as exc:
        return [], [{'path':str(directory),'error':str(exc)}]
    def walk(folder):
        try:
            if folder.is_symlink():
                raise ValueError('safety directory is a symlink')
            if not folder.exists():
                return
            if not folder.is_dir():
                raise ValueError('safety directory is not a directory')
            for path in sorted(folder.iterdir()):
                if path.is_symlink():
                    raise ValueError('safety path is a symlink: ' + str(path))
                if recursive and path.is_dir():
                    walk(path)
                elif path.name.endswith('.md'):
                    paths.append(path)
        except (OSError, ValueError) as exc:
            errors.append({'path':str(folder),'error':str(exc)})
    walk(directory)
    return paths, errors
