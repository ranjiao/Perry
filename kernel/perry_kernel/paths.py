"""Where the project is and where its store lives (§ 5.7, NN-K5).

The anchor order is the one every Perry tool resolves in: `--root`, then
`PERRY_PROJECT`, then the walk up from the working directory. The git common
dir is read from `.git` and `commondir`, never asked of `git`: the kernel runs
no command (NN-K2). Everything here takes the environment and the working
directory as arguments, so a caller can resolve for a directory it is not in.
"""

from __future__ import annotations

from pathlib import Path

from .errors import KernelError
from .values import SURROGATE

ANCHOR_DIR = ".perry"
OUTSIDE_GIT_STORE = "perry.db"   # under <anchor>/.perry/
STORE_DIR = "perry"                # under <git common dir>/
SLUG_SAFE = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
                      b"0123456789._-")


def working_directory(cwd) -> Path:
    if cwd is None:
        raise KernelError("io_error", "the working directory no longer exists")
    cwd = Path(cwd)
    if SURROGATE.search(str(cwd)):
        raise KernelError("io_error", "the working directory's path is not "
                                      "valid UTF-8")
    return cwd


def resolve_path(text: str, cwd, source: str = "a path") -> Path:
    """An absolute, resolved path, or a typed refusal. `~user` that names no
    one, a symlink loop and an unreadable component are `io_error`, never an
    exception (NN-K6)."""
    if text == "":
        # `Path("")` is the working directory: an empty value must never
        # quietly become one (the flags are refused at parse, § 5.1).
        raise KernelError("usage", f"{source} was given an empty value")
    try:
        path = Path(text).expanduser()
        if not path.is_absolute():
            path = working_directory(cwd) / path
        path = path.resolve()
    except (OSError, RuntimeError) as exc:
        raise KernelError("io_error", f"{source}: cannot resolve the path: "
                                      f"{getattr(exc, 'strerror', None) or exc}",
                          {"source": source})
    if SURROGATE.search(str(path)):
        raise KernelError("io_error", f"{source}: the path is not valid UTF-8",
                          {"source": source})
    return path


def _abs(text: str, cwd, source: str = "a path") -> Path:
    return resolve_path(text, cwd, source)


def env_value(environ, name: str):
    """An environment variable's value, or None when it is unset or empty.
    An empty variable counts as unset, as it does for `bin/`
    (`bin/lib § resolve_project_root` tests it for truth)."""
    value = environ.get(name)
    if value and SURROGATE.search(value):
        raise KernelError("usage", f"{name} is not valid UTF-8",
                          {"variable": name})
    return value if value else None


def _holds_anchor(directory: Path) -> bool:
    try:
        return (directory / ANCHOR_DIR).is_dir()
    except OSError:
        return False


def resolve_anchor(root_flag: str | None, environ, cwd) -> Path:
    """The project anchor: `--root`, else `PERRY_PROJECT`, else the first
    directory at or above `cwd` that holds `.perry/`."""
    project = env_value(environ, "PERRY_PROJECT")
    if root_flag is not None:
        chosen, source = _abs(root_flag, cwd, "--root"), "--root"
    elif project is not None:
        chosen, source = _abs(project, cwd, "PERRY_PROJECT"), "PERRY_PROJECT"
    else:
        start = resolve_path(".", cwd, "the working directory")
        for directory in (start, *start.parents):
            if _holds_anchor(directory):
                return directory
        raise KernelError("anchor_not_found",
                          f"no directory at or above {start} holds "
                          f"{ANCHOR_DIR}/", {"searched_from": str(start)})
    if not _holds_anchor(chosen):
        raise KernelError("anchor_not_found",
                          f"{chosen} (from {source}) holds no {ANCHOR_DIR}/",
                          {"path": str(chosen), "source": source})
    return chosen


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise KernelError("io_error", f"cannot read {path}: {exc.strerror}",
                          {"path": str(path)})
    except UnicodeDecodeError:
        raise KernelError("io_error", f"{path} is not valid UTF-8",
                          {"path": str(path)})


def _kind(path: Path):
    """`dir`, `file` or None; an unreadable component is `io_error`."""
    try:
        if path.is_dir():
            return "dir"
        if path.is_file():
            return "file"
    except OSError as exc:
        raise KernelError("io_error", f"cannot inspect {path}: "
                                      f"{exc.strerror}", {"path": str(path)})
    return None


def git_layout(anchor: Path):
    """`(top, git_dir, common_dir)` for the worktree holding `anchor`, or None
    outside git. `GIT_DIR` and `GIT_COMMON_DIR` are ignored on purpose."""
    for directory in (anchor, *anchor.parents):
        dotgit = directory / ".git"
        kind = _kind(dotgit)
        if kind == "dir":
            git_dir = _abs(str(dotgit), directory)
        elif kind == "file":
            pointer = None
            for line in _read_text(dotgit).splitlines():
                if line.startswith("gitdir:"):
                    pointer = line[len("gitdir:"):].strip()
                    break
            if not pointer:
                raise KernelError("io_error", f"{dotgit} has no gitdir: line",
                                  {"path": str(dotgit)})
            git_dir = _abs(pointer, directory)
        else:
            continue
        commondir = git_dir / "commondir"
        if _kind(commondir) == "file":
            common = _abs(_read_text(commondir).strip(), git_dir)
        else:
            common = git_dir
        return directory, git_dir, common
    return None


def slug(anchor: Path, top: Path) -> str:
    """`root` for a worktree's top level, else `root/<path>` with every byte
    outside [A-Za-z0-9._-] written as %XX. Injective."""
    rel = anchor.relative_to(top).as_posix()
    text = "root" if rel == "." else f"root/{rel}"
    return "".join(chr(b) if b in SLUG_SAFE else f"%{b:02X}"
                   for b in text.encode("utf-8"))


def derived_store(anchor: Path) -> Path:
    layout = git_layout(anchor)
    if layout is None:
        return anchor / ANCHOR_DIR / OUTSIDE_GIT_STORE
    top, _git_dir, common = layout
    return common / STORE_DIR / f"{slug(anchor, top)}.db"


def resolve_store(store_flag: str | None, environ, cwd, anchor_fn):
    """`(path, derived)`. `--store`, else `PERRY_STORE`, else derived from the
    anchor, which `anchor_fn()` resolves only when it is needed."""
    if store_flag is not None:
        return _abs(store_flag, cwd, "--store"), False
    named = env_value(environ, "PERRY_STORE")
    if named is not None:
        return _abs(named, cwd, "PERRY_STORE"), False
    path = derived_store(anchor_fn())
    if env_value(environ, "PERRY_KERNEL_TESTING") is not None:
        raise KernelError("store_live_under_test",
                          "PERRY_KERNEL_TESTING is set and no store was named; "
                          "pass --store or PERRY_STORE",
                          {"derived": str(path)})
    return path, True
