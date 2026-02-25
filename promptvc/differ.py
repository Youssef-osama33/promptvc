"""
differ.py — Line-by-line diff engine for PromptVC.

Compares two prompt strings and returns a structured sequence of
:class:`DiffLine` objects, each annotated with its kind (added,
removed, or unchanged) and the original line numbers from both sides.

The algorithm delegates to :mod:`difflib.SequenceMatcher` — the same
engine used by Python's ``difflib.unified_diff`` — and wraps its output
in a richer, typed structure suited for programmatic use and colorized
terminal rendering.

Design decisions
----------------
- Full-snapshot diffs over stored deltas: simpler, always accurate.
- Dataclass over namedtuple: forward-compatible, IDE-friendly.
- Line numbers on both sides: enables side-by-side rendering later.
- Lines are normalized (stripped) before comparison so that trailing-
  newline differences ('line\\n' vs 'line') never cause false replaces.
- ``autojunk=False``: SequenceMatcher's heuristic is unreliable on the
  short, repetitive content typical of LLM prompts.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Sequence


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class DiffKind(str, Enum):
    """The role of a single line within a diff."""

    ADDED = "added"
    REMOVED = "removed"
    UNCHANGED = "unchanged"


@dataclass(frozen=True)
class DiffLine:
    """
    A single line from a unified diff.

    Attributes
    ----------
    kind : DiffKind
        Whether the line was added, removed, or unchanged.
    content : str
        The text of the line (without a trailing newline).
    line_num_a : int or None
        1-based line number in the *old* version, or ``None`` for added lines.
    line_num_b : int or None
        1-based line number in the *new* version, or ``None`` for removed lines.
    """

    kind: DiffKind
    content: str
    line_num_a: int | None = field(default=None)
    line_num_b: int | None = field(default=None)

    def is_added(self) -> bool:
        return self.kind is DiffKind.ADDED

    def is_removed(self) -> bool:
        return self.kind is DiffKind.REMOVED

    def is_unchanged(self) -> bool:
        return self.kind is DiffKind.UNCHANGED


@dataclass(frozen=True)
class DiffSummary:
    """
    Aggregate statistics for a completed diff.

    Attributes
    ----------
    added : int
        Number of added lines.
    removed : int
        Number of removed lines.
    unchanged : int
        Number of unchanged lines.
    """

    added: int
    removed: int
    unchanged: int

    @property
    def total(self) -> int:
        """Total number of lines across both sides."""
        return self.added + self.removed + self.unchanged

    @property
    def is_identical(self) -> bool:
        """True when the two versions are character-for-character identical."""
        return self.added == 0 and self.removed == 0

    def __str__(self) -> str:
        return f"+{self.added} lines  -{self.removed} lines  {self.unchanged} unchanged"


# ---------------------------------------------------------------------------
# Core diff function
# ---------------------------------------------------------------------------


def diff_prompts(content_a: str, content_b: str) -> List[DiffLine]:
    """
    Compare two prompt strings and return an annotated diff.

    Parameters
    ----------
    content_a : str
        The *old* prompt content (left side of the diff).
    content_b : str
        The *new* prompt content (right side of the diff).

    Returns
    -------
    list of DiffLine
        An ordered sequence of :class:`DiffLine` objects covering every
        line in both inputs. The sequence preserves the original reading
        order: removed lines from *a* appear before the inserted lines
        from *b* within each changed block.

    Notes
    -----
    Lines are stripped of trailing whitespace before being passed to
    SequenceMatcher. This prevents trailing-newline differences from
    being reported as replacements — e.g. comparing ``'x\\n'`` to ``'x'``
    would otherwise yield a spurious remove+add for the same content.

    Examples
    --------
    >>> lines = diff_prompts("Be helpful.", "Be concise and helpful.")
    >>> lines[0].kind
    <DiffKind.REMOVED: 'removed'>
    >>> lines[1].kind
    <DiffKind.ADDED: 'added'>
    """
    # Normalize: strip trailing whitespace/newlines so 'line\\n' == 'line'.
    lines_a: List[str] = [_strip(l) for l in content_a.splitlines(keepends=True)]
    lines_b: List[str] = [_strip(l) for l in content_b.splitlines(keepends=True)]

    # Handle completely empty inputs.
    if not content_a:
        lines_a = []
    if not content_b:
        lines_b = []

    matcher = difflib.SequenceMatcher(
        isjunk=None,
        a=lines_a,
        b=lines_b,
        autojunk=False,  # disable heuristic — prompts can be short
    )

    result: List[DiffLine] = []
    num_a = 1  # current 1-based line counter for side A
    num_b = 1  # current 1-based line counter for side B

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for line in lines_a[i1:i2]:
                result.append(
                    DiffLine(DiffKind.UNCHANGED, line, num_a, num_b)
                )
                num_a += 1
                num_b += 1

        elif tag == "replace":
            for line in lines_a[i1:i2]:
                result.append(DiffLine(DiffKind.REMOVED, line, num_a, None))
                num_a += 1
            for line in lines_b[j1:j2]:
                result.append(DiffLine(DiffKind.ADDED, line, None, num_b))
                num_b += 1

        elif tag == "delete":
            for line in lines_a[i1:i2]:
                result.append(DiffLine(DiffKind.REMOVED, line, num_a, None))
                num_a += 1

        elif tag == "insert":
            for line in lines_b[j1:j2]:
                result.append(DiffLine(DiffKind.ADDED, line, None, num_b))
                num_b += 1

    return result


def summarise(diff_lines: Sequence[DiffLine]) -> DiffSummary:
    """
    Compute aggregate statistics from a completed diff.

    Parameters
    ----------
    diff_lines : sequence of DiffLine
        The output of :func:`diff_prompts`.

    Returns
    -------
    DiffSummary
    """
    added = sum(1 for d in diff_lines if d.is_added())
    removed = sum(1 for d in diff_lines if d.is_removed())
    unchanged = sum(1 for d in diff_lines if d.is_unchanged())
    return DiffSummary(added=added, removed=removed, unchanged=unchanged)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _strip(line: str) -> str:
    """Remove trailing whitespace and newline characters from a line."""
    return line.rstrip("\r\n ")
