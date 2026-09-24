"""The kernel: a project's structured state behind one CLI (DESIGN-023).

`kernel/ARCHITECTURE.md` is the specification. Standard library only.
"""

from .cli import invoke, main

__all__ = ["invoke", "main"]
