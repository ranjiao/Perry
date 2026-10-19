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
